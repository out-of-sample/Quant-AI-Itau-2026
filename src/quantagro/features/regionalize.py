"""Regionalização do raster CHIRPS na malha municipal fixa do IBGE (D-023/D-024).

Este módulo materializa a geografia congelada do sinal primário: a média de precipitação
por **polígono municipal** (edição IBGE 2013, `ingest/ibge_geometry.py`), que a camada de
sinal pondera pela PAM *as-of* para chegar à UF. Ele não conhece cultura, janela fenológica
nem peso de produção — só transforma (raster, malha) em painel municipal diário.

Duas peças, separadas porque têm custos muito diferentes:

1. ``municipality_cell_index`` — para cada município, quais células da grade p05 têm o
   **centro** dentro do polígono (regra even-odd, que trata buracos e multipolígonos).
   É a parte cara (ponto-em-polígono sobre ~2.600 municípios), mas é função só da malha e
   do geotransform — ambos congelados — então calcula uma vez e o resultado é cacheável
   em Parquet. O índice carrega as constantes da grade em colunas próprias: um índice
   construído para uma grade não pode ser aplicado silenciosamente a outra.
2. ``municipal_daily_precip`` — dado o índice, agrega cada raster diário em média municipal
   ignorando ``nodata``. É a parte barata e roda por dia de CHIRPS.

Município menor que a célula (~5,5 km; ex.: Santa Cruz de Minas/MG) pode não conter nenhum
centro de célula. Descartá-lo silenciosamente distorceria o peso PAM; falhar alto bloquearia
o pipeline por um caso geométrico conhecido. A saída declarada: o município recebe a célula
cujo centro é o mais próximo do centroide do polígono, com ``cell_source="nearest_centroid"``
— auditável no índice, testado, e com efeito espacial máximo de meia célula.

Sem ``avail_date`` aqui: o carimbo PIT (lag de 7 dias corridos do CHIRPS) é aplicado a
jusante por ``validate.pit.stamp_avail_date``, preservando ``kind`` como eixo de vintage.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from quantagro.ingest.chirps import NODATA, GeoTransform, read_chirps_grid

_POINT_CHUNK = 4096

_GRID_COLS = ("grid_rows", "grid_cols", "grid_origin_lon", "grid_origin_lat", "grid_pixel_deg")


def _polygons(geometry: dict) -> list[list[list[list[float]]]]:
    """Lista de polígonos ``[anel_externo, buracos...]`` de um GeoJSON Polygon/MultiPolygon."""
    kind = geometry.get("type")
    if kind == "Polygon":
        return [geometry["coordinates"]]
    if kind == "MultiPolygon":
        return list(geometry["coordinates"])
    raise ValueError(f"geometria municipal não poligonal: {kind!r}")


def _closed_ring(ring) -> np.ndarray:
    v = np.asarray(ring, dtype=np.float64)
    if v.ndim != 2 or v.shape[1] < 2 or v.shape[0] < 3:
        raise ValueError("anel de polígono degenerado")
    v = v[:, :2]
    if not np.array_equal(v[0], v[-1]):
        v = np.vstack([v, v[:1]])
    return v


def _ring_crossings(px: np.ndarray, py: np.ndarray, ring: np.ndarray) -> np.ndarray:
    """Cruzamentos do raio horizontal (+x) de cada ponto com as arestas de um anel fechado."""
    x0, y0 = ring[:-1, 0], ring[:-1, 1]
    x1, y1 = ring[1:, 0], ring[1:, 1]
    keep = y0 != y1  # aresta horizontal nunca cruza o raio
    x0, y0, x1, y1 = x0[keep], y0[keep], x1[keep], y1[keep]
    if x0.size == 0:
        return np.zeros(px.shape[0], dtype=np.int64)
    py2, px2 = py[:, None], px[:, None]
    straddle = (y0 > py2) != (y1 > py2)
    xint = x0 + (py2 - y0) * (x1 - x0) / (y1 - y0)
    return (straddle & (px2 < xint)).sum(axis=1)


def points_in_geometry(lons: np.ndarray, lats: np.ndarray, geometry: dict) -> np.ndarray:
    """Regra even-odd sobre todos os anéis: buracos e multipolígonos saem de graça.

    ``lons``/``lats`` são pares ponto a ponto (mesmo comprimento). O cálculo é vetorizado
    ponto × aresta em blocos, para limitar memória em municípios grandes.
    """
    lons = np.asarray(lons, dtype=np.float64)
    lats = np.asarray(lats, dtype=np.float64)
    if lons.shape != lats.shape or lons.ndim != 1:
        raise ValueError("lons e lats devem ser vetores 1-D do mesmo tamanho")
    rings = [_closed_ring(ring) for polygon in _polygons(geometry) for ring in polygon]
    inside = np.zeros(lons.shape[0], dtype=bool)
    for start in range(0, lons.shape[0], _POINT_CHUNK):
        sl = slice(start, start + _POINT_CHUNK)
        crossings = np.zeros(lons[sl].shape[0], dtype=np.int64)
        for ring in rings:
            crossings += _ring_crossings(lons[sl], lats[sl], ring)
        inside[sl] = (crossings % 2).astype(bool)
    return inside


def _centroid(geometry: dict) -> tuple[float, float]:
    """Centroide (shoelace) do maior anel externo; degenerado cai na média dos vértices."""
    best_area = -1.0
    best: tuple[float, float] | None = None
    for polygon in _polygons(geometry):
        v = _closed_ring(polygon[0])
        x0, y0 = v[:-1, 0], v[:-1, 1]
        x1, y1 = v[1:, 0], v[1:, 1]
        cross = x0 * y1 - x1 * y0
        area = float(cross.sum()) / 2.0
        if abs(area) > best_area:
            best_area = abs(area)
            if abs(area) > 1e-12:
                cx = float(((x0 + x1) * cross).sum() / (6.0 * area))
                cy = float(((y0 + y1) * cross).sum() / (6.0 * area))
            else:
                cx, cy = float(v[:-1, 0].mean()), float(v[:-1, 1].mean())
            best = (cx, cy)
    assert best is not None  # _polygons garante ≥ 1 polígono
    return best


def _nearest_cell(geometry: dict, gt: GeoTransform, n_rows: int, n_cols: int) -> tuple[int, int]:
    """Célula cujo centro é o mais próximo do centroide — fallback de município sub-célula."""
    lon, lat = _centroid(geometry)
    col = int(np.floor((lon - gt.origin_lon) / gt.pixel_deg))
    row = int(np.floor((gt.origin_lat - lat) / gt.pixel_deg))
    if not (0 <= row < n_rows and 0 <= col < n_cols):
        raise ValueError(f"centroide municipal fora da grade: lon={lon:.4f}, lat={lat:.4f}")
    return row, col


def municipality_cell_index(
    geometry: pd.DataFrame, gt: GeoTransform, n_rows: int, n_cols: int
) -> pd.DataFrame:
    """Uma linha por (município, célula da grade cujo centro cai no polígono).

    ``geometry`` é a saída de ``ibge_geometry.parse_geometry`` (uma ou mais UFs
    concatenadas). O resultado carrega as constantes da grade (shape, origem, pixel) para
    que ``municipal_daily_precip`` recuse um raster incompatível — o índice é válido para
    exatamente uma grade.
    """
    required = {
        "municipality_code",
        "uf",
        "geometry_json",
        "min_lon",
        "min_lat",
        "max_lon",
        "max_lat",
    }
    missing = required - set(geometry.columns)
    if missing:
        raise ValueError(f"malha sem colunas: {sorted(missing)}")
    # A malha traz polígonos de água não-municipais (RS: 4300001 Lagoa Mirim, 4300002 Lagoa
    # dos Patos — código de município "0000"). Nunca têm produção PAM, mas no índice seriam
    # uma armadilha para qualquer média não-ponderada; ficam fora, explicitamente.
    non_municipal = geometry["municipality_code"].str.slice(2, 6) == "0000"
    geometry = geometry[~non_municipal]
    if geometry.empty:
        raise ValueError("malha sem nenhum polígono municipal")
    if geometry["municipality_code"].duplicated().any():
        raise ValueError("malha com geocódigo duplicado")
    lons, lats = gt.cell_centers(n_rows, n_cols)
    out_code: list[str] = []
    out_uf: list[str] = []
    out_row: list[np.ndarray] = []
    out_col: list[np.ndarray] = []
    out_src: list[np.ndarray] = []
    for muni in geometry.itertuples(index=False):
        geom = json.loads(muni.geometry_json)
        margin = gt.pixel_deg
        ridx = np.nonzero((lats >= muni.min_lat - margin) & (lats <= muni.max_lat + margin))[0]
        cidx = np.nonzero((lons >= muni.min_lon - margin) & (lons <= muni.max_lon + margin))[0]
        if ridx.size and cidx.size:
            rr, cc = np.meshgrid(ridx, cidx, indexing="ij")
            rr, cc = rr.ravel(), cc.ravel()
            inside = points_in_geometry(lons[cc], lats[rr], geom)
            rr, cc = rr[inside], cc[inside]
        else:
            rr = cc = np.empty(0, dtype=np.int64)
        if rr.size:
            src = np.full(rr.size, "polygon")
        else:
            row, col = _nearest_cell(geom, gt, n_rows, n_cols)
            rr = np.array([row], dtype=np.int64)
            cc = np.array([col], dtype=np.int64)
            src = np.array(["nearest_centroid"])
        out_code.append(muni.municipality_code)
        out_uf.append(muni.uf)
        out_row.append(rr)
        out_col.append(cc)
        out_src.append(src)
    counts = [r.size for r in out_row]
    out = pd.DataFrame(
        {
            "municipality_code": np.repeat(np.asarray(out_code, dtype=object), counts),
            "uf": np.repeat(np.asarray(out_uf, dtype=object), counts),
            "row": np.concatenate(out_row),
            "col": np.concatenate(out_col),
            "cell_source": np.concatenate(out_src),
            "grid_rows": n_rows,
            "grid_cols": n_cols,
            "grid_origin_lon": gt.origin_lon,
            "grid_origin_lat": gt.origin_lat,
            "grid_pixel_deg": gt.pixel_deg,
        }
    )
    return out.sort_values(["municipality_code", "row", "col"]).reset_index(drop=True)


def _validate_grid(index: pd.DataFrame, arr: np.ndarray, gt: GeoTransform, label: str) -> None:
    n_rows = int(index["grid_rows"].iloc[0])
    n_cols = int(index["grid_cols"].iloc[0])
    if arr.shape != (n_rows, n_cols):
        raise ValueError(f"{label}: shape {arr.shape} difere da grade do índice {(n_rows, n_cols)}")
    expected = (
        float(index["grid_origin_lon"].iloc[0]),
        float(index["grid_origin_lat"].iloc[0]),
        float(index["grid_pixel_deg"].iloc[0]),
    )
    actual = (gt.origin_lon, gt.origin_lat, gt.pixel_deg)
    if not np.allclose(actual, expected, atol=1e-9):
        raise ValueError(f"{label}: geotransform {actual} difere do índice {expected}")


def municipal_daily_precip(
    files: list[tuple[object, str, str | Path | bytes]], index: pd.DataFrame
) -> pd.DataFrame:
    """Painel municipal diário a partir de ``(ref_date, kind, raster)`` + índice de células.

    Uma linha por ``(ref_date, kind, municipality_code)`` com a média das células válidas
    (``nodata`` fora da conta; município só-``nodata`` devolve ``NaN`` e fica visível em
    ``n_valid_cells`` — silêncio viraria zero espúrio de chuva). Todo raster precisa casar
    com a grade para a qual o índice foi construído.
    """
    required = {"municipality_code", "uf", "row", "col", *_GRID_COLS}
    missing = required - set(index.columns)
    if missing:
        raise ValueError(f"índice sem colunas: {sorted(missing)}")
    if index.empty:
        raise ValueError("índice de células vazio")
    for col in _GRID_COLS:
        values = index[col].to_numpy()
        if (values != values[0]).any():
            raise ValueError(f"índice mistura grades diferentes ({col})")
    groups, codes = pd.factorize(index["municipality_code"])
    uf_by_code = index.groupby("municipality_code", sort=False)["uf"].first()
    rows_flat = index["row"].to_numpy(dtype=np.int64)
    cols_flat = index["col"].to_numpy(dtype=np.int64)
    n_codes = len(codes)
    n_cells = np.bincount(groups, minlength=n_codes)
    out_frames: list[pd.DataFrame] = []
    for date, kind, source in files:
        if kind not in ("prelim", "final"):
            raise ValueError(f"kind desconhecido: {kind!r}")
        arr, gt = read_chirps_grid(source)
        _validate_grid(index, arr, gt, f"raster {pd.Timestamp(date).date()}/{kind}")
        vals = arr[rows_flat, cols_flat].astype(np.float64)
        valid = vals != NODATA
        sums = np.bincount(groups, weights=np.where(valid, vals, 0.0), minlength=n_codes)
        cnts = np.bincount(groups, weights=valid.astype(np.float64), minlength=n_codes)
        precip = np.divide(sums, cnts, out=np.full(n_codes, np.nan), where=cnts > 0)
        out_frames.append(
            pd.DataFrame(
                {
                    "ref_date": pd.Timestamp(date),
                    "kind": kind,
                    "uf": uf_by_code.loc[codes].to_numpy(),
                    "municipality_code": codes,
                    "precip_mm": precip,
                    "n_cells": n_cells,
                    "n_valid_cells": cnts.astype(np.int64),
                }
            )
        )
    cols_out = [
        "ref_date",
        "kind",
        "uf",
        "municipality_code",
        "precip_mm",
        "n_cells",
        "n_valid_cells",
    ]
    if not out_frames:
        return pd.DataFrame(columns=cols_out)
    out = pd.concat(out_frames, ignore_index=True)
    return (
        out[cols_out].sort_values(["ref_date", "kind", "municipality_code"]).reset_index(drop=True)
    )
