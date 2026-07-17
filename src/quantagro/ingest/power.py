"""Ingestão de temperatura NASA POWER — clima SECUNDÁRIO da tese (docs/02_DADOS.md §1.2).

O POWER entra restrito à **temperatura** (estresse térmico, geada), onde não há alternativa
gratuita com vintage. É secundário justamente porque **não preserva vintage**: a série é a
reanálise MERRA-2 com uma cauda de baixa latência (GEOS-IT/FLASHFLUX) anexada, e os últimos
~2 meses são **provisórios e serão sobrescritos**; mesmo o MERRA-2 "definitivo" é reprocessado
a cada alguns meses. Respeitar `avail_date` (latência ~3 dias) **não** conserta isso — o valor
em si é uma versão revisada. Essa contaminação é **irremovível na fonte**; o papel deste módulo
é (a) medir a latência no carimbo e (b) **registrar a proveniência de vintage** de cada captura,
para que a limitação seja declarada e mensurável, nunca ignorada (docs/05_SUITE_ROBUSTEZ.md).

Mecanismo de vintage, verificado ao vivo (2026-07-16) lendo `header.sources` da resposta:
- fetch antigo (2015) → `['MERRA2', 'POWER']` → classificado **definitivo**;
- fetch recente (jun/2026) → `['GEOSIT', 'POWER']` → classificado **provisório**.
A classificação é por resposta (a API não expõe a fonte por data), então uma captura em massa de
histórico hoje devolve a versão **atual** (revisada) — o que exige a limitação declarada acima.

Fatos da API (verificados ao vivo): endpoint `.../temporal/daily/point`, JSON, HTTP 200, **sem
chave**; `fill_value = -999.0`; unidades em °C; `header.api.version` versiona a API; a resposta
snapa para a célula da grade (~0.5°) e devolve as coordenadas reais em `geometry.coordinates`
(`[lon, lat, elev]`). Rate limit não é garantido (a doc menciona HTTP 429) ⇒ **cache local
agressivo**: o destino leva a data de captura no nome (um vintage por captura, como a CONAB) e
não rebaixa se o arquivo do dia já existe.

Este módulo faz **só a ingestão**: baixa por ponto nomeado (com manifesto de vintage), parseia o
JSON em painel arrumado e classifica a proveniência. Os pontos default são os centroides das
mesmas regiões produtoras do CHIRPS (`ingest/chirps.DEFAULT_BOXES`), para que precipitação e
temperatura casem pela coluna `region`. O carimbo `avail_date` (lag de 3 dias corridos) é
aplicado a jusante por `quantagro.validate.pit`.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd

_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
_COMMUNITY = "AG"

# Restrição de escopo (D-019): só temperatura. Precipitação vem do CHIRPS (com vintage).
TEMPERATURE_PARAMS = ("T2M", "T2M_MAX", "T2M_MIN")

FILL_VALUE = -999.0

# Classificação de vintage a partir de header.sources: a presença de qualquer produto de baixa
# latência marca a resposta como provisória (será sobrescrita).
_PROVISIONAL_SOURCES = frozenset({"GEOSIT", "FLASHFLUX"})
_DEFINITIVE_SOURCE = "MERRA2"

# Pontos default = centroides das caixas do CHIRPS, para casar `region` entre chuva e temperatura.
# region → (lat, lon) em graus decimais.
DEFAULT_POINTS: dict[str, tuple[float, float]] = {
    "MT_norte": (-12.5, -55.5),  # centroide de (-14..-11, -57..-54)
    "MATOPIBA_BA": (-12.5, -45.0),  # centroide de (-14..-11, -46..-44)
}


def _ymd(date) -> str:
    return pd.Timestamp(date).strftime("%Y%m%d")


def power_request_params(
    lat: float,
    lon: float,
    start,
    end,
    parameters: tuple[str, ...] = TEMPERATURE_PARAMS,
    community: str = _COMMUNITY,
) -> dict[str, str]:
    """Dicionário de query params para o endpoint diário por ponto."""
    return {
        "parameters": ",".join(parameters),
        "community": community,
        "latitude": f"{lat}",
        "longitude": f"{lon}",
        "start": _ymd(start),
        "end": _ymd(end),
        "format": "JSON",
    }


def power_url(
    lat: float,
    lon: float,
    start,
    end,
    parameters: tuple[str, ...] = TEMPERATURE_PARAMS,
    community: str = _COMMUNITY,
) -> str:
    """URL completa da consulta (para manifesto e depuração)."""
    params = power_request_params(lat, lon, start, end, parameters, community)
    return f"{_BASE_URL}?{urlencode(params)}"


def classify_vintage(sources) -> str:
    """Classifica a proveniência de uma resposta a partir de `header.sources`.

    'provisorio' se contém qualquer produto de baixa latência (GEOS-IT/FLASHFLUX) — a resposta
    será sobrescrita; 'definitivo' se é só MERRA-2 (que ainda assim é reprocessado — a limitação
    de vintage permanece, ver docstring do módulo). Sem MERRA-2 nem provisório → 'desconhecido'.
    """
    s = set(sources or ())
    if s & _PROVISIONAL_SOURCES:
        return "provisorio"
    if _DEFINITIVE_SOURCE in s:
        return "definitivo"
    return "desconhecido"


def _load_json(source: str | Path | bytes | dict) -> dict:
    if isinstance(source, dict):
        return source
    if isinstance(source, bytes):
        return json.loads(source)
    return json.loads(Path(source).read_text(encoding="utf-8"))


def _write_manifest(region, lat, lon, url, content, resp, stamp, manifest_dir) -> Path:
    """Manifesto de vintage: o POWER sobrescreve o passado, então sources + data de captura são
    a única prova de qual versão (provisória/definitiva) alimentou o backtest."""
    md = Path(manifest_dir)
    md.mkdir(parents=True, exist_ok=True)
    header = resp.get("header", {})
    sources = header.get("sources")
    coords = resp.get("geometry", {}).get("coordinates")
    manifest = {
        "source": "NASA-POWER",
        "region": region,
        "requested_lat": lat,
        "requested_lon": lon,
        "grid_coordinates": coords,  # [lon, lat, elev] da célula efetiva
        "start": header.get("start"),
        "end": header.get("end"),
        "sources": sources,
        "vintage": classify_vintage(sources),
        "api_version": header.get("api", {}).get("version"),
        "url": url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "downloaded_at": datetime.now(UTC).isoformat(),
    }
    path = md / f"power_{region}_{header.get('start')}_{header.get('end')}_{stamp}.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def download_power(
    points: dict[str, tuple[float, float]],
    start,
    end,
    parameters: tuple[str, ...] = TEMPERATURE_PARAMS,
    dest_dir: str | Path = "data/raw/power",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 120,
) -> dict[str, Path]:
    """Baixa a série diária de cada ponto nomeado e grava manifesto de vintage por captura.

    O POWER **sobrescreve o passado** (não há URL/consulta por vintage), então o destino leva a
    data de captura no nome — um vintage por captura, como a CONAB — e não rebaixa se o arquivo do
    dia já existe (cache agressivo: rate limit não é garantido, e o pipeline nunca depende de
    rede — R12). Devolve `region → caminho do JSON`.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    if session is None:
        import requests

        session = requests
    out: dict[str, Path] = {}
    for region, (lat, lon) in points.items():
        path = dest / f"power_{region}_{_ymd(start)}_{_ymd(end)}_{stamp}.json"
        if path.exists():
            out[region] = path
            continue
        url = power_url(lat, lon, start, end, parameters)
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        content = resp.content
        path.write_bytes(content)
        _write_manifest(region, lat, lon, url, content, _load_json(content), stamp, manifest_dir)
        out[region] = path
    return out


def parse_power(source: str | Path | bytes | dict, region: str | None = None) -> pd.DataFrame:
    """Parseia uma resposta do POWER em painel arrumado (formato longo).

    Uma linha por `(ref_date, param)`, com `value` (fill −999 → `NaN` — nunca tratar o fill como
    temperatura real) e `source_vintage` (classificação da resposta: provisório/definitivo).
    Se `region` for dado, entra como coluna. `param` preserva o nome do POWER (T2M, T2M_MAX...).
    """
    d = _load_json(source)
    header = d.get("header", {})
    vintage = classify_vintage(header.get("sources"))
    par = d.get("properties", {}).get("parameter", {})
    rows = []
    for param, series in par.items():
        for ymd, value in series.items():
            rows.append({"ref_date": ymd, "param": param, "value": value})
    cols = ["ref_date", "region", "param", "value", "source_vintage"]
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows)
    df["ref_date"] = pd.to_datetime(df["ref_date"], format="%Y%m%d")
    df["value"] = df["value"].astype("float64").replace(FILL_VALUE, pd.NA).astype("Float64")
    df["region"] = region
    df["source_vintage"] = vintage
    return df[cols].reset_index(drop=True)


def build_power_panel(items: list[tuple[str, str | Path | bytes | dict]]) -> pd.DataFrame:
    """Monta o painel a partir de `(region, fonte_json)`.

    Concatena o parse de cada ponto. Sem `avail_date`: o carimbo PIT (lag de 3 dias corridos,
    latência meteorológica medida) é aplicado a jusante por `validate.pit.stamp_avail_date`.
    A coluna `source_vintage` preserva a proveniência para a análise de robustez de revisão.
    """
    cols = ["ref_date", "region", "param", "value", "source_vintage"]
    frames = [parse_power(src, region=region) for region, src in items]
    if not frames:
        return pd.DataFrame(columns=cols)
    return pd.concat(frames, ignore_index=True)[cols].reset_index(drop=True)
