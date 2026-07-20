"""Validação física pré-registrada da cana (D-050), sem retornos acionários."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..features.cane_panel import CANE_BASE_YEARS
from ..features.cane_shock import uf_cane_shock_asof
from ..features.shock_spec import CANE_GROWTH_WINDOWS, CANE_MATURATION_WINDOWS
from ..ingest.conab_calendar import attach_avail_date
from .inference import cluster_bootstrap, ols_cluster

EXPECTED_CROP_YEARS = tuple(f"{year}/{(year + 1) % 100:02d}" for year in CANE_BASE_YEARS)
EXPECTED_UFS = ("GO", "MG", "MS", "PR", "SP")


@dataclass(frozen=True)
class CaneH1Verdict:
    """Regra de aprovação do portão maturação→ATR congelada em D-050."""

    passed: bool
    pooled_beta: float
    positive_leave_one_out: int
    total_leave_one_out: int
    positive_ufs: int
    total_ufs: int
    reason: str


def _prepare_conab(conab: pd.DataFrame) -> pd.DataFrame:
    out = conab[
        (conab["produto"] == "CANA DE ACUCAR")
        & (conab["safra"] == "UNICA")
        & (conab["uf"].isin(EXPECTED_UFS))
        & (conab["ano_agricola"].isin(EXPECTED_CROP_YEARS))
        & (conab["id_levantamento"].between(1, 4))
    ].copy()
    stamped = attach_avail_date(out, "cana")
    years = tuple(sorted(stamped["ano_agricola"].unique()))
    if years != EXPECTED_CROP_YEARS:
        raise ValueError(f"safras da cana fora do pré-registro: {years}")
    return stamped


def _revisions(conab: pd.DataFrame, value_col: str) -> pd.DataFrame:
    rows = []
    for (uf, year), group in conab.groupby(["uf", "ano_agricola"], sort=False):
        values = group.set_index("id_levantamento")[value_col].sort_index()
        if tuple(values.index) != (1, 2, 3, 4):
            raise ValueError(f"cana exige levantamentos 1–4 para {uf}/{year}")
        if (values <= 0).any():
            raise ValueError(f"medida não positiva em {uf}/{year}/{value_col}")
        base = float(values.loc[1])
        avail = group.set_index("id_levantamento")["avail_date"]
        for lev in (2, 3, 4):
            rows.append(
                {
                    "uf": uf,
                    "ano_agricola": year,
                    "id_levantamento": lev,
                    "avail_date": pd.Timestamp(avail.loc[lev]),
                    "logrev": float(np.log(float(values.loc[lev]) / base)),
                }
            )
    return pd.DataFrame(rows)


def build_cane_h1_panel(
    conab: pd.DataFrame,
    monthly_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    climatology_first_year: int,
    phase: str,
) -> pd.DataFrame:
    """Painel da fase: maturação usa ATR; crescimento usa produção."""
    prepared = _prepare_conab(conab)
    if phase == "maturation":
        windows = CANE_MATURATION_WINDOWS
        outcome = "atr"
        value_col = "producao_atr_kg_t"
    elif phase == "growth":
        windows = CANE_GROWTH_WINDOWS
        outcome = "production"
        value_col = "producao_mil_t"
    else:
        raise KeyError(f"fase da cana fora do D-050: {phase!r}")
    revisions = _revisions(prepared, value_col)
    by_uf = {spec.uf: spec for spec in windows}
    rows = []
    for rev in revisions.itertuples(index=False):
        shock = uf_cane_shock_asof(
            rev.avail_date,
            rev.ano_agricola,
            by_uf[rev.uf],
            monthly_stamped,
            pam_panel,
            climatology_first_year,
        )
        if shock["status"] != "ok":
            continue
        rows.append(
            {
                "phase": phase,
                "outcome": outcome,
                "uf": rev.uf,
                "ano_agricola": rev.ano_agricola,
                "id_levantamento": rev.id_levantamento,
                "avail_date": rev.avail_date,
                "shock": shock["shock"],
                "months_seen": shock["months_seen"],
                "logrev": rev.logrev,
            }
        )
    panel = pd.DataFrame(rows)
    years = tuple(sorted(panel["ano_agricola"].unique()))
    if years != EXPECTED_CROP_YEARS or set(panel["uf"]) != set(EXPECTED_UFS):
        raise ValueError(
            f"painel incompleto da cana: safras={years}, UFs={sorted(panel['uf'].unique())}"
        )
    return panel.sort_values(["uf", "ano_agricola", "id_levantamento"]).reset_index(drop=True)


def _slope(sub: pd.DataFrame) -> float:
    x = sub["shock"].to_numpy(dtype=float)
    y = sub["logrev"].to_numpy(dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if x.size < 3:
        return np.nan
    xc = x - x.mean()
    denom = float(xc @ xc)
    return float((xc @ (y - y.mean())) / denom) if denom > 0 else np.nan


def run_cane_h1(panel: pd.DataFrame) -> pd.DataFrame:
    """Pooled agrupado, UFs, safras e oito leave-one-safra-out."""
    years = tuple(sorted(panel["ano_agricola"].unique()))
    if years != EXPECTED_CROP_YEARS:
        raise ValueError(f"H1 cana exige {EXPECTED_CROP_YEARS}; recebeu {years}")
    primary = ols_cluster(panel["shock"], panel["logrev"], panel["ano_agricola"], "cane_h1")
    boot = cluster_bootstrap(panel["shock"], panel["logrev"], panel["ano_agricola"])
    rows = [
        {
            "scope": "pooled",
            "key": "all",
            "n": primary.nobs,
            "n_clusters": primary.n_clusters,
            "beta": primary.beta,
            "se": primary.se,
            "tstat": primary.tstat,
            "pvalue": primary.pvalue,
            "ci_low": primary.ci_low,
            "ci_high": primary.ci_high,
            "boot_pvalue": boot["pvalue"],
            "boot_ci_low": boot["ci_low"],
            "boot_ci_high": boot["ci_high"],
        }
    ]
    for uf in EXPECTED_UFS:
        sub = panel[panel["uf"] == uf]
        rows.append({"scope": "uf", "key": uf, "n": len(sub), "n_clusters": 8, "beta": _slope(sub)})
    for year in years:
        rows.append(
            {
                "scope": "crop_year",
                "key": year,
                "n": int((panel["ano_agricola"] == year).sum()),
                "n_clusters": 1,
                "beta": _slope(panel[panel["ano_agricola"] == year]),
            }
        )
        leave = panel[panel["ano_agricola"] != year]
        rows.append(
            {
                "scope": "leave_one_crop_year_out",
                "key": year,
                "n": len(leave),
                "n_clusters": 7,
                "beta": _slope(leave),
            }
        )
    return pd.DataFrame(rows)


def cane_h1_verdict(maturation_results: pd.DataFrame) -> CaneH1Verdict:
    """Aplica literalmente D-050; crescimento e significância não são consultados."""
    pooled = maturation_results.query("scope == 'pooled' and key == 'all'")
    loo = maturation_results.query("scope == 'leave_one_crop_year_out'")
    ufs = maturation_results.query("scope == 'uf'")
    if len(pooled) != 1 or len(loo) != 8 or len(ufs) != 5:
        raise ValueError("resultado incompleto para o veredito D-050")
    if loo["beta"].isna().any() or ufs["beta"].isna().any():
        raise ValueError("diagnóstico indefinido no veredito D-050")
    beta = float(pooled.iloc[0]["beta"])
    positive_loo = int((loo["beta"] > 0).sum())
    positive_ufs = int((ufs["beta"] > 0).sum())
    passed = beta > 0 and positive_loo >= 6 and positive_ufs >= 3
    status = "corroborado" if passed else "não corroborado"
    reason = (
        f"{status}: beta={beta:.4f}; {positive_loo}/8 LOO positivos; {positive_ufs}/5 UFs positivas"
    )
    return CaneH1Verdict(passed, beta, positive_loo, 8, positive_ufs, 5, reason)
