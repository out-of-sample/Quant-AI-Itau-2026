"""Matriz fundamentalista point-in-time de empresa por cultura (D-032).

O registro versionado contém vintages integrais de cada companhia. Esta camada valida a
proveniência, materializa ``E = direção × materialidade × peso`` e seleciona somente o último
vintage cuja ``avail_date`` já era conhecida na data da decisão. Retornos não entram aqui.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pandas as pd

PRIMARY_CROPS = ("soy", "corn_second")
MATERIALITY_LEVELS = frozenset({0.0, 0.25, 0.5, 1.0})
AVAILABILITY_BASES = frozenset({"exact_filing", "conservative_bound"})
_TICKER_RE = re.compile(r"^[A-Z]{4}\d{1,2}$")
_REQUIRED = frozenset(
    {
        "exposure_id",
        "ticker",
        "ref_date",
        "avail_date",
        "availability_basis",
        "direction",
        "materiality",
        "crop_weights",
        "crop_weight_basis",
        "source",
        "evidence",
        "calculation",
    }
)


def _validate_source(source: object, exposure_id: str) -> dict[str, str]:
    if not isinstance(source, dict):
        raise ValueError(f"{exposure_id}: source deve ser objeto")
    required = {"title", "url", "locator"}
    if not required.issubset(source) or any(not str(source[k]).strip() for k in required):
        raise ValueError(f"{exposure_id}: source incompleta")
    parsed = urlparse(str(source["url"]))
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{exposure_id}: source.url deve ser HTTPS")
    return {key: str(source[key]).strip() for key in required}


def _validate_vintage(raw: object, crops: tuple[str, ...]) -> list[dict[str, object]]:
    if not isinstance(raw, dict):
        raise ValueError("cada vintage deve ser objeto")
    missing = _REQUIRED - raw.keys()
    if missing:
        raise ValueError(f"vintage sem campos obrigatórios: {sorted(missing)}")

    exposure_id = str(raw["exposure_id"]).strip()
    ticker = str(raw["ticker"]).strip().upper()
    if not exposure_id:
        raise ValueError("exposure_id vazio")
    if _TICKER_RE.fullmatch(ticker) is None:
        raise ValueError(f"{exposure_id}: ticker inválido: {ticker!r}")

    ref_date = pd.Timestamp(raw["ref_date"])
    avail_date = pd.Timestamp(raw["avail_date"])
    if ref_date > avail_date:
        raise ValueError(f"{exposure_id}: ref_date posterior a avail_date")

    availability_basis = str(raw["availability_basis"])
    if availability_basis not in AVAILABILITY_BASES:
        raise ValueError(f"{exposure_id}: availability_basis inválida")

    direction = int(raw["direction"])
    if direction not in {-1, 1} or float(raw["direction"]) != direction:
        raise ValueError(f"{exposure_id}: direction deve ser -1 ou +1")
    materiality = float(raw["materiality"])
    if materiality not in MATERIALITY_LEVELS or materiality == 0:
        raise ValueError(f"{exposure_id}: materiality deve ser 0,25, 0,50 ou 1")

    weights = raw["crop_weights"]
    if not isinstance(weights, dict) or set(weights) != set(crops):
        raise ValueError(f"{exposure_id}: crop_weights deve conter exatamente {list(crops)}")
    numeric_weights = {crop: float(weights[crop]) for crop in crops}
    if any(not np.isfinite(value) or value < 0 for value in numeric_weights.values()):
        raise ValueError(f"{exposure_id}: crop_weight negativo ou não finito")
    if not np.isclose(sum(numeric_weights.values()), 1.0, atol=1e-12):
        raise ValueError(f"{exposure_id}: crop_weights não somam 1")

    source = _validate_source(raw["source"], exposure_id)
    crop_weight_basis = str(raw["crop_weight_basis"]).strip()
    evidence = str(raw["evidence"]).strip()
    calculation = str(raw["calculation"]).strip()
    if not crop_weight_basis or not evidence or not calculation:
        raise ValueError(f"{exposure_id}: base, evidência e cálculo devem ser preenchidos")

    rows: list[dict[str, object]] = []
    for crop, weight in numeric_weights.items():
        exposure = direction * materiality * weight
        if not -1 <= exposure <= 1:
            raise ValueError(f"{exposure_id}: exposição fora de [-1,+1]")
        rows.append(
            {
                "exposure_id": exposure_id,
                "ticker": ticker,
                "crop": crop,
                "ref_date": ref_date,
                "avail_date": avail_date,
                "availability_basis": availability_basis,
                "direction": direction,
                "materiality": materiality,
                "crop_weight": weight,
                "exposure": exposure,
                "crop_weight_basis": crop_weight_basis,
                "source_title": source["title"],
                "source_url": source["url"],
                "source_locator": source["locator"],
                "evidence": evidence,
                "calculation": calculation,
            }
        )
    return rows


def load_exposure_registry(path: str | Path) -> pd.DataFrame:
    """Lê e valida o registro JSON, devolvendo uma linha por vintage × cultura."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("schema_version de exposição não suportada")
    crops = tuple(payload.get("crops", ()))
    if crops != PRIMARY_CROPS:
        raise ValueError(f"crops deve ser exatamente {list(PRIMARY_CROPS)}")
    vintages = payload.get("vintages")
    if not isinstance(vintages, list) or not vintages:
        raise ValueError("registro sem vintages")

    rows = [row for vintage in vintages for row in _validate_vintage(vintage, crops)]
    out = pd.DataFrame(rows)
    counts = out.groupby("exposure_id", sort=False).size()
    if not counts.eq(len(crops)).all():
        raise ValueError("exposure_id duplicado")
    vintage_keys = out.drop_duplicates("exposure_id")
    if vintage_keys.duplicated(["ticker", "avail_date"]).any():
        raise ValueError("dois vintages da empresa com a mesma avail_date")
    return out.sort_values(["avail_date", "ticker", "crop"], kind="stable").reset_index(drop=True)


def exposure_asof(registry: pd.DataFrame, t: pd.Timestamp | str) -> pd.DataFrame:
    """Seleciona o último vintage integral disponível por empresa em ``t``.

    A seleção ocorre pelo identificador do vintage, não linha a linha, preservando a unidade
    soja+milho. Antes da primeira evidência, a empresa simplesmente não aparece.
    """
    required = {"exposure_id", "ticker", "crop", "avail_date", "exposure"}
    missing = required - set(registry.columns)
    if missing:
        raise ValueError(f"registro sem colunas obrigatórias: {sorted(missing)}")
    available = registry.loc[registry["avail_date"] <= pd.Timestamp(t)].copy()
    if available.empty:
        return available.reset_index(drop=True)
    latest = (
        available[["ticker", "exposure_id", "avail_date"]]
        .drop_duplicates()
        .sort_values(["ticker", "avail_date", "exposure_id"], kind="stable")
        .groupby("ticker", sort=False, as_index=False)
        .tail(1)["exposure_id"]
    )
    return (
        available[available["exposure_id"].isin(latest)]
        .sort_values(["ticker", "crop"], kind="stable")
        .reset_index(drop=True)
    )


def exposure_matrix_asof(registry: pd.DataFrame, t: pd.Timestamp | str) -> pd.DataFrame:
    """Matriz ``ticker × cultura`` observável em ``t``, em ordem determinística."""
    selected = exposure_asof(registry, t)
    if selected.empty:
        return pd.DataFrame(columns=PRIMARY_CROPS, dtype=float).rename_axis("ticker")
    matrix = selected.pivot(index="ticker", columns="crop", values="exposure")  # noqa: PD010
    return matrix.reindex(columns=PRIMARY_CROPS).sort_index().rename_axis(columns=None)
