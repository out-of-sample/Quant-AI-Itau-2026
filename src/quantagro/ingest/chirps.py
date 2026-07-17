"""Ingestão de precipitação CHIRPS — clima primário da tese (docs/02_DADOS.md §1.1).

O CHIRPS (UCSB Climate Hazards Center) é a fonte climática **primária** porque é a única
testada que **preserva vintage**: publica dois produtos diários arquivados separadamente —
`prelim` (~2 dias de latência) e `final` (revisado, ~mês seguinte). O produto preliminar é o
que estava disponível na época; o final é a verdade revisada. Isso dá um proxy honesto de
point-in-time e permite **medir** o quanto a revisão contamina o sinal, em vez de torcer para
que não contamine (docs/05_SUITE_ROBUSTEZ.md §2.4).

Fatos da fonte, verificados ao vivo (2026-07-16):
- Grade global p05: 0.05° (~5 km), **2000 linhas × 7200 colunas**, canto superior-esquerdo em
  (lon −180, lat +50), cobrindo 50°S–50°N. `nodata = −9999` (oceano).
- GeoTIFF **sem compressão**, float32 (`sampleformat=IEEE float`), gravado dentro de um `.tif.gz`.
  Decodável sem GDAL — só `tifffile` (Python puro sobre numpy). O geotransform vem
  auto-descrito nas tags `ModelPixelScale` (33550) e `ModelTiepoint` (33922); lemos dele, não
  de constante fixa, para que a extração funcione igual num recorte (fixture) e no raster global.
- URLs por data (imutáveis, ao contrário do arquivo único da CONAB):
  final  → `.../global_daily/tifs/p05/{ANO}/chirps-v2.0.{ANO}.{MES}.{DIA}.tif.gz`
  prelim → `.../prelim/global_daily/tifs/p05/{ANO}/chirps-v2.0.{ANO}.{MES}.{DIA}.tif.gz`
  O timestamp do próprio diretório corrobora a latência (prelim de 15/01/2024 datado 17/01;
  final datado 15/02) — dentro do lag congelado de 7 dias corridos (docs/01_TESE §5).

Este módulo faz **só a ingestão**: baixa (com manifesto de vintage), decodifica o grid e agrega
a precipitação em **caixas lat/lon nomeadas** por região produtora. A *escolha* das caixas é
decisão de modelagem da camada de sinal — aqui elas entram como argumento explícito. O carimbo
`avail_date` (lag de 7 dias corridos) é aplicado a jusante por `quantagro.validate.pit`, com o
vintage prelim/final preservado na coluna `kind`.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

_BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0"

KINDS = ("prelim", "final")

# Constantes da grade global p05 — usadas só para validar que a fonte não mudou o formato
# por baixo dos nossos pés (o read em si lê o geotransform das tags do arquivo).
NODATA = -9999.0
_GRID_SHAPE = (2000, 7200)
_PIXEL_DEG = 0.05
_ORIGIN_LON = -180.0
_ORIGIN_LAT = 50.0


class GeoTransform(NamedTuple):
    """Geotransform mínimo de um grid CHIRPS, lido das tags do GeoTIFF.

    O canto superior-esquerdo do pixel (0, 0) fica em (`origin_lon`, `origin_lat`); a latitude
    **decresce** com a linha. `pixel_deg` é o lado do pixel em graus (0.05 no p05).
    """

    origin_lon: float
    origin_lat: float
    pixel_deg: float

    def cell_centers(self, n_rows: int, n_cols: int) -> tuple[np.ndarray, np.ndarray]:
        """Longitudes (colunas) e latitudes (linhas) dos **centros** dos pixels."""
        lons = self.origin_lon + (np.arange(n_cols) + 0.5) * self.pixel_deg
        lats = self.origin_lat - (np.arange(n_rows) + 0.5) * self.pixel_deg
        return lons, lats


# Caixas ilustrativas (a escolha real é da camada de sinal). Cada uma é
# (lat_min, lat_max, lon_min, lon_max) em graus decimais.
DEFAULT_BOXES: dict[str, tuple[float, float, float, float]] = {
    "MT_norte": (-14.0, -11.0, -57.0, -54.0),  # Sorriso / médio-norte de MT (soja e milho 2ª)
    "MATOPIBA_BA": (-14.0, -11.0, -46.0, -44.0),  # oeste da Bahia
}


def chirps_url(date, kind: str) -> str:
    """URL do GeoTIFF diário do CHIRPS para uma `date` e um `kind` ('prelim' ou 'final')."""
    if kind not in KINDS:
        raise ValueError(f"kind desconhecido: {kind!r} (use {list(KINDS)})")
    d = pd.Timestamp(date)
    stem = f"chirps-v2.0.{d.year:04d}.{d.month:02d}.{d.day:02d}.tif.gz"
    sub = "prelim/global_daily" if kind == "prelim" else "global_daily"
    return f"{_BASE_URL}/{sub}/tifs/p05/{d.year:04d}/{stem}"


def _write_manifest(date, kind: str, url: str, content: bytes, manifest_dir) -> Path:
    """Grava manifesto de vintage: prelim vs. final é a distinção de vintage do CHIRPS, e o
    sha256 + a data de captura são a prova de qual produto alimentou o backtest."""
    md = Path(manifest_dir)
    md.mkdir(parents=True, exist_ok=True)
    d = pd.Timestamp(date)
    manifest = {
        "source": "CHIRPS-2.0",
        "kind": kind,
        "ref_date": d.strftime("%Y-%m-%d"),
        "url": url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "downloaded_at": datetime.now(UTC).isoformat(),
    }
    path = md / f"chirps_{kind}_{d.strftime('%Y%m%d')}.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def download_chirps(
    date,
    kind: str,
    dest_dir: str | Path = "data/raw/chirps",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 300,
) -> Path:
    """Baixa o GeoTIFF diário do CHIRPS (prelim ou final) e grava manifesto de vintage.

    URLs por data são imutáveis, então o destino leva a data + o kind no nome; se o arquivo
    já existe, não rebaixa (o pipeline nunca depende de rede — R12). O par (kind, sha256) é a
    prova de qual vintage foi usado.
    """
    if kind not in KINDS:
        raise ValueError(f"kind desconhecido: {kind!r} (use {list(KINDS)})")
    d = pd.Timestamp(date)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"chirps-v2.0.{d.strftime('%Y.%m.%d')}.{kind}.tif.gz"
    if out.exists():
        return out
    if session is None:
        import requests

        session = requests
    url = chirps_url(date, kind)
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    out.write_bytes(resp.content)
    _write_manifest(date, kind, url, resp.content, manifest_dir)
    return out


def _read_geotransform(page) -> GeoTransform:
    """Extrai o GeoTransform das tags GeoTIFF (ModelPixelScale=33550, ModelTiepoint=33922).

    Lê direto das tags da página (não de `geotiff_metadata`, que o tifffile só popula quando há
    `GeoKeyDirectoryTag`) — assim funciona igual num recorte sem geokeys e no raster global.
    """
    scale = page.tags.valueof(33550)
    tie = page.tags.valueof(33922)
    if scale is None or tie is None:
        raise ValueError("GeoTIFF sem ModelPixelScale/ModelTiepoint — não é um CHIRPS válido")
    # ModelTiepoint = [i, j, k, x, y, z]: o pixel (j, i) mapeia para (x, y). CHIRPS usa (0,0).
    origin_lon, origin_lat = float(tie[3]), float(tie[4])
    px, py = float(scale[0]), float(scale[1])
    if abs(px - py) > 1e-9:
        raise ValueError(f"pixel não quadrado: {px} x {py}")
    return GeoTransform(origin_lon, origin_lat, px)


def read_chirps_grid(source: str | Path | bytes) -> tuple[np.ndarray, GeoTransform]:
    """Lê um GeoTIFF do CHIRPS (`.tif`, `.tif.gz` ou bytes) → (array float32, GeoTransform).

    O geotransform vem das tags do próprio arquivo (auto-descrito), então isto funciona igual
    para o raster global e para um recorte. `nodata` (−9999) é preservado no array — a máscara
    fica a cargo de `extract_boxes`, que sabe qual agregação ignora célula inválida.
    """
    import tifffile

    if isinstance(source, bytes):
        raw = source
    else:
        raw = Path(source).read_bytes()
    if raw[:2] == b"\x1f\x8b":  # magic gzip
        raw = gzip.decompress(raw)
    import io

    with tifffile.TiffFile(io.BytesIO(raw)) as tf:
        page = tf.pages[0]
        arr = page.asarray()
        gt = _read_geotransform(page)
    return arr.astype("float32", copy=False), gt


def assert_global_grid(arr: np.ndarray, gt: GeoTransform) -> None:
    """Confere que um grid é a grade global p05 esperada — tripwire contra a fonte mudar o
    formato silenciosamente. Não se aplica a recortes (fixtures)."""
    if arr.shape != _GRID_SHAPE:
        raise ValueError(f"shape inesperado {arr.shape} (esperado {_GRID_SHAPE})")
    if abs(gt.pixel_deg - _PIXEL_DEG) > 1e-9:
        raise ValueError(f"pixel {gt.pixel_deg} != {_PIXEL_DEG}")
    if abs(gt.origin_lon - _ORIGIN_LON) > 1e-6 or abs(gt.origin_lat - _ORIGIN_LAT) > 1e-6:
        raise ValueError(f"origem {(gt.origin_lon, gt.origin_lat)} != global")


def extract_boxes(
    arr: np.ndarray,
    gt: GeoTransform,
    boxes: dict[str, tuple[float, float, float, float]],
) -> dict[str, float]:
    """Média de precipitação por caixa nomeada, ignorando `nodata`.

    Cada caixa é `(lat_min, lat_max, lon_min, lon_max)`; a seleção usa o **centro** de cada
    pixel. Uma caixa sem nenhuma célula válida (fora do grid ou toda oceano) devolve `nan` —
    silêncio aqui viraria zero espúrio de chuva. `KeyError` de caixa não existe: o dict de
    saída tem exatamente as mesmas chaves da entrada.
    """
    n_rows, n_cols = arr.shape
    lons, lats = gt.cell_centers(n_rows, n_cols)
    out: dict[str, float] = {}
    for name, (lat_min, lat_max, lon_min, lon_max) in boxes.items():
        rmask = (lats >= lat_min) & (lats <= lat_max)
        cmask = (lons >= lon_min) & (lons <= lon_max)
        if not rmask.any() or not cmask.any():
            out[name] = float("nan")
            continue
        sub = arr[np.ix_(rmask, cmask)]
        valid = sub[sub != NODATA]
        out[name] = float(valid.mean()) if valid.size else float("nan")
    return out


def build_chirps_panel(
    files: list[tuple[object, str, str | Path]],
    boxes: dict[str, tuple[float, float, float, float]],
) -> pd.DataFrame:
    """Monta o painel arrumado a partir de `(ref_date, kind, caminho_do_tif)`.

    Devolve uma linha por `(ref_date, region, kind)` com `precip_mm`. Sem `avail_date`: o
    carimbo PIT (lag de 7 dias corridos) é aplicado a jusante por `validate.pit.stamp_avail_date`,
    preservando `kind` como o eixo de vintage (prelim = o que existia; final = revisado).
    """
    rows = []
    for date, kind, path in files:
        if kind not in KINDS:
            raise ValueError(f"kind desconhecido: {kind!r} (use {list(KINDS)})")
        arr, gt = read_chirps_grid(path)
        means = extract_boxes(arr, gt, boxes)
        ref = pd.Timestamp(date)
        for region, precip in means.items():
            rows.append({"ref_date": ref, "region": region, "kind": kind, "precip_mm": precip})
    cols = ["ref_date", "region", "kind", "precip_mm"]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows)[cols].reset_index(drop=True)
