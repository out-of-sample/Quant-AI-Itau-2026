"""Choque mensal da cana, separado por crescimento e maturação (D-050)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantagro.features.cane_panel import phase_months
from quantagro.features.shock import FINAL_LAG_DAYS, PRELIM_LAG_DAYS
from quantagro.features.shock_spec import (
    CLIMATOLOGY_KIND,
    EXPANDING_STD_DDOF,
    MIN_EXPANDING_YEARS,
    PRECIP_Z_TO_STRESS,
    PRIMARY_SIGNAL_KIND,
    CropRegionWindow,
    crop_year_start,
)
from quantagro.ingest.pam import pam_weights_asof
from quantagro.validate.pit import available_asof, stamp_avail_date


def stamp_cane_monthly_panel(panel: pd.DataFrame) -> pd.DataFrame:
    """Carimba cada acumulado mensal conforme o vintage prelim/final."""
    unknown = set(panel["kind"].unique()) - {PRIMARY_SIGNAL_KIND, CLIMATOLOGY_KIND}
    if unknown:
        raise ValueError(f"kind desconhecido no painel mensal: {sorted(unknown)}")
    parts = []
    for kind, lag in ((PRIMARY_SIGNAL_KIND, PRELIM_LAG_DAYS), (CLIMATOLOGY_KIND, FINAL_LAG_DAYS)):
        sub = panel[panel["kind"] == kind]
        if not sub.empty:
            parts.append(stamp_avail_date(sub, lag_days=lag))
    if not parts:
        return panel.assign(avail_date=pd.Series(dtype="datetime64[ns]"))
    return pd.concat(parts, ignore_index=True)


def _weights(pam_panel: pd.DataFrame, spec: CropRegionWindow, t) -> pd.Series:
    pam = pam_weights_asof(pam_panel, t)
    sub = pam[(pam["crop"] == "sugarcane") & (pam["uf"] == spec.uf)]
    out = sub.set_index("municipality_code")["within_uf_weight"].dropna()
    if out.empty:
        raise ValueError(f"sem peso PAM de cana para {spec.uf}")
    return out / out.sum()


def _monthly_sum(panel, kind: str, weights: pd.Series, dates: pd.DatetimeIndex) -> float:
    sub = panel[
        (panel["kind"] == kind)
        & (panel["ref_date"].isin(dates))
        & (panel["municipality_code"].isin(weights.index))
    ]
    got_dates = pd.DatetimeIndex(sorted(sub["ref_date"].unique()))
    if not got_dates.equals(dates):
        missing = dates.difference(got_dates)
        raise ValueError(f"painel mensal sem {len(missing)} mês(es): {list(missing[:3])}")
    grouped = sub.groupby("municipality_code")["precip_mm"].agg(["sum", "count", "size"])
    missing_codes = sorted(set(weights.index) - set(grouped.index))
    if missing_codes:
        raise ValueError(f"município PAM fora do painel mensal: {missing_codes[:5]}")
    bad = grouped[(grouped["size"] != len(dates)) | (grouped["count"] != grouped["size"])]
    if not bad.empty:
        raise ValueError(f"cobertura mensal incompleta: {sorted(bad.index)[:5]}")
    return float((grouped.loc[weights.index, "sum"] * weights).sum())


def uf_cane_shock_asof(
    t,
    ano_agricola: str,
    spec: CropRegionWindow,
    monthly_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    climatology_first_year: int,
) -> dict:
    """Déficit de chuva da fase observável em ``t``, comparado ao mesmo prefixo histórico."""
    ts = pd.Timestamp(t)
    visible = available_asof(monthly_stamped, ts)
    current_base = crop_year_start(ano_agricola)
    expected = phase_months(spec, current_base)
    prelim = visible[(visible["kind"] == PRIMARY_SIGNAL_KIND) & (visible["uf"] == spec.uf)]
    seen = expected.intersection(pd.DatetimeIndex(prelim["ref_date"].unique()))
    row = {
        "asof_date": ts,
        "ano_agricola": ano_agricola,
        "crop": "sugarcane",
        "phase": spec.phase,
        "uf": spec.uf,
        "window_start": expected[0].to_period("M").start_time,
        "window_end": expected[-1],
    }
    if seen.empty:
        first_avail = expected[0] + pd.Timedelta(days=PRELIM_LAG_DAYS)
        if ts >= first_avail:
            raise ValueError(
                f"painel mensal sem o primeiro mês já esperado para {spec.uf}/{spec.phase}: "
                f"{expected[0].date()} disponível desde {first_avail.date()}"
            )
        return row | {"months_seen": 0, "shock": np.nan, "status": "window_not_started"}
    prefix = expected[: len(seen)]
    if not seen.equals(prefix):
        raise ValueError(f"meses prelim não formam prefixo contíguo para {spec.uf}/{spec.phase}")
    weights = _weights(pam_panel, spec, ts)
    current = _monthly_sum(prelim, PRIMARY_SIGNAL_KIND, weights, prefix)
    years = range(climatology_first_year, current_base)
    if len(years) < MIN_EXPANDING_YEARS:
        raise ValueError(f"climatologia mensal com {len(years)} safras < {MIN_EXPANDING_YEARS}")
    final = visible[(visible["kind"] == CLIMATOLOGY_KIND) & (visible["uf"] == spec.uf)]
    history = []
    for base in years:
        dates = phase_months(spec, base)[: len(prefix)]
        history.append(_monthly_sum(final, CLIMATOLOGY_KIND, weights, dates))
    hist = np.asarray(history, dtype=float)
    mean = float(hist.mean())
    std = float(hist.std(ddof=EXPANDING_STD_DDOF))
    if not np.isfinite(std) or std <= 0:
        raise ValueError(f"climatologia mensal degenerada para {spec.key}/{spec.phase}")
    z = (current - mean) / std
    return row | {
        "cut_date": prefix[-1],
        "months_seen": len(prefix),
        "precip_mm": current,
        "clim_mean_mm": mean,
        "clim_std_mm": std,
        "n_clim_years": len(years),
        "z": z,
        "shock": PRECIP_Z_TO_STRESS * z,
        "status": "ok",
    }
