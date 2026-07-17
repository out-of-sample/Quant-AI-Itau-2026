"""Malha municipal fixa do IBGE para a regionalização climática.

O suporte espacial primário é a edição municipal **2013**, escolhida antes de calcular o
Shock. Os arquivos internos da edição foram gerados em 16/03/2015, antes da primeira janela
operacional (dezembro/2015). Fixar uma única malha evita mudanças mecânicas no sinal quando o
IBGE refina limites ou cria município; um geocódigo PAM positivo sem polígono não é descartado
— a cobertura falha alto e exige crosswalk versionado.

O parser usa PyShp puro, sem GDAL/GeoPandas. A geometria é serializada como GeoJSON compacto,
adequado a Parquet, e acompanha ``ref_date``/``avail_date`` como qualquer tabela do projeto.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import shapefile

GEOMETRY_EDITION = 2013
GEOMETRY_REF_DATE = pd.Timestamp("2013-12-31")
GEOMETRY_AVAIL_DATE = pd.Timestamp("2015-03-16")
_EXPECTED_MEMBER_DATE = (2015, 3, 16)
_BASE_URL = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais"
)
_UF_CODES = {"BA": "29", "MG": "31", "PR": "41", "RS": "43", "MS": "50", "MT": "51", "GO": "52"}


def geometry_url(uf: str, edition: int = GEOMETRY_EDITION) -> str:
    """URL arquivada da malha municipal fixa; outra edição exige nova decisão."""
    uf = str(uf).upper()
    if uf not in _UF_CODES:
        raise ValueError(f"UF fora do suporte primário: {uf!r}")
    if edition != GEOMETRY_EDITION:
        raise ValueError(f"edição congelada é {GEOMETRY_EDITION}, veio {edition}")
    return f"{_BASE_URL}/municipio_{edition}/{uf}/{uf.lower()}_municipios.zip"


def _write_manifest(uf: str, url: str, content: bytes, manifest_dir) -> Path:
    md = Path(manifest_dir)
    md.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": "IBGE-Malha-Municipal",
        "edition": GEOMETRY_EDITION,
        "uf": uf,
        "ref_date": GEOMETRY_REF_DATE.date().isoformat(),
        "artifact_member_timestamp": GEOMETRY_AVAIL_DATE.date().isoformat(),
        "url": url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "downloaded_at": datetime.now(UTC).isoformat(),
        "spatial_policy": "suporte fixo pre-amostra; geocódigo novo exige crosswalk explícito",
    }
    path = md / f"ibge_municipios_{GEOMETRY_EDITION}_{uf.lower()}.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def download_geometry(
    uf: str,
    dest_dir: str | Path = "data/raw/ibge_geometry",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 180,
) -> Path:
    """Baixa o ZIP histórico por UF, com cache e manifesto de conteúdo."""
    uf = str(uf).upper()
    url = geometry_url(uf)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"ibge_municipios_{GEOMETRY_EDITION}_{uf.lower()}.zip"
    if out.exists():
        return out
    if session is None:
        import requests

        session = requests
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    content = resp.content
    if not zipfile.is_zipfile(io.BytesIO(content)):
        raise ValueError("IBGE não devolveu um ZIP válido")
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        _validate_member_dates(zf)
    out.write_bytes(content)
    _write_manifest(uf, url, content, manifest_dir)
    return out


def _zip_bytes(source: str | Path | bytes) -> bytes:
    return source if isinstance(source, bytes) else Path(source).read_bytes()


def _members(zf: zipfile.ZipFile) -> tuple[str, str, str, str | None, str | None]:
    by_suffix: dict[str, list[str]] = {}
    for name in zf.namelist():
        by_suffix.setdefault(Path(name).suffix.lower(), []).append(name)
    for required in (".shp", ".shx", ".dbf"):
        if len(by_suffix.get(required, [])) != 1:
            raise ValueError(f"ZIP da malha precisa de exatamente um {required}")
    prj = by_suffix.get(".prj", [None])
    cpg = by_suffix.get(".cpg", [None])
    return by_suffix[".shp"][0], by_suffix[".shx"][0], by_suffix[".dbf"][0], prj[0], cpg[0]


def _validate_member_dates(zf: zipfile.ZipFile) -> None:
    """Tripwire do artefato pré-amostra: todos os membros oficiais datam de 16/03/2015."""
    dates = {item.date_time[:3] for item in zf.infolist() if not item.is_dir()}
    if dates != {_EXPECTED_MEMBER_DATE}:
        raise ValueError(f"timestamp interno da malha mudou: {sorted(dates)}")


def parse_geometry(source: str | Path | bytes, uf: str) -> pd.DataFrame:
    """Lê o ZIP oficial e devolve uma linha Parquet-safe por município."""
    uf = str(uf).upper()
    if uf not in _UF_CODES:
        raise ValueError(f"UF fora do suporte primário: {uf!r}")
    raw = _zip_bytes(source)
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        raise ValueError("fonte de geometria não é ZIP")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        _validate_member_dates(zf)
        shp_name, shx_name, dbf_name, prj_name, cpg_name = _members(zf)
        encoding = zf.read(cpg_name).decode("ascii").strip() if cpg_name else "utf-8"
        projection = zf.read(prj_name).decode("ascii", errors="replace") if prj_name else ""
        if "SIRGAS" not in projection.upper() or "GEOGCS" not in projection.upper():
            raise ValueError("malha sem projeção geográfica SIRGAS declarada")
        reader = shapefile.Reader(
            shp=io.BytesIO(zf.read(shp_name)),
            shx=io.BytesIO(zf.read(shx_name)),
            dbf=io.BytesIO(zf.read(dbf_name)),
            encoding=encoding,
        )
        fields = {field.name for field in reader.fields[1:]}
        required = {"CD_GEOCMU", "NM_MUNICIP"}
        if not required <= fields:
            raise ValueError(f"campos ausentes na malha: {sorted(required - fields)}")
        rows = []
        for item in reader.iterShapeRecords():
            record = item.record.as_dict()
            code = str(record["CD_GEOCMU"]).strip()
            if len(code) != 7 or code[:2] != _UF_CODES[uf]:
                raise ValueError(f"geocódigo incompatível com {uf}: {code!r}")
            if item.shape.shapeType not in {
                shapefile.POLYGON,
                shapefile.POLYGONM,
                shapefile.POLYGONZ,
            }:
                raise ValueError(f"geometria municipal não poligonal: {item.shape.shapeTypeName}")
            min_lon, min_lat, max_lon, max_lat = map(float, item.shape.bbox)
            if not (-75 <= min_lon < max_lon <= -30 and -35 <= min_lat < max_lat <= 6):
                raise ValueError(f"bbox fora do Brasil para {code}: {item.shape.bbox}")
            geometry = item.shape.__geo_interface__
            rows.append(
                {
                    "ref_date": GEOMETRY_REF_DATE,
                    "avail_date": GEOMETRY_AVAIL_DATE,
                    "geometry_edition": GEOMETRY_EDITION,
                    "uf": uf,
                    "municipality_code": code,
                    "municipality_name_geometry": str(record["NM_MUNICIP"]).strip(),
                    "geometry_json": json.dumps(geometry, separators=(",", ":")),
                    "min_lon": min_lon,
                    "min_lat": min_lat,
                    "max_lon": max_lon,
                    "max_lat": max_lat,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty or out["municipality_code"].duplicated().any():
        raise ValueError("malha vazia ou com geocódigo duplicado")
    return out.sort_values("municipality_code").reset_index(drop=True)


def attach_geometry(weights: pd.DataFrame, geometry: pd.DataFrame) -> pd.DataFrame:
    """Anexa a malha fixa e falha se produção positiva não tiver polígono."""
    required = {"municipality_code", "quantity_tonnes", "within_uf_weight"}
    if not required <= set(weights.columns):
        raise ValueError(f"pesos PAM sem colunas: {sorted(required - set(weights.columns))}")
    if geometry["municipality_code"].duplicated().any():
        raise ValueError("malha com geocódigo duplicado")
    positive = weights[weights["quantity_tonnes"] > 0]
    missing = sorted(set(positive["municipality_code"]) - set(geometry["municipality_code"]))
    if missing:
        raise ValueError(f"município PAM positivo sem geometria fixa/crosswalk: {missing[:10]}")
    geo_cols = [
        "municipality_code",
        "geometry_edition",
        "geometry_json",
        "min_lon",
        "min_lat",
        "max_lon",
        "max_lat",
    ]
    return weights.merge(
        geometry[geo_cols], on="municipality_code", how="left", validate="many_to_one"
    )
