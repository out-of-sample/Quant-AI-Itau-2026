"""Validação H1 do canal de algodão pré-registrada em D-048.

O teste usa somente o mecanismo físico: ``Shock`` de algodão por UF contra a revisão log da
produção CONAB de pluma. Não importa preços nem retornos acionários. Como apenas 2022/23,
2023/24 e 2024/25 têm vintages completos e datáveis, a aprovação é direcional: beta agrupado
negativo e pelo menos duas de três estimativas leave-one-safra-out negativas. P-valores com
três clusters são diagnósticos, nunca a regra de decisão.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..features.shock_spec import COTTON_WINDOWS
from .h1a import build_h1a_panel
from .inference import cluster_bootstrap, ols_cluster

COTTON_BASES = range(2022, 2025)
EXPECTED_CROP_YEARS = ("2022/23", "2023/24", "2024/25")


@dataclass(frozen=True)
class CottonH1Verdict:
    """Veredito direcional congelado antes do resultado (D-048)."""

    passed: bool
    pooled_beta: float
    negative_leave_one_out: int
    total_leave_one_out: int
    reason: str


def build_cotton_h1_panel(
    conab: pd.DataFrame,
    municipal_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    climatology_first_year: int,
) -> pd.DataFrame:
    """Monta o painel MT+BA das três safras datáveis completas do algodão."""
    panel = build_h1a_panel(
        conab,
        municipal_stamped,
        pam_panel,
        climatology_first_year,
        bases=COTTON_BASES,
        windows=COTTON_WINDOWS,
    )
    years = tuple(sorted(panel["ano_agricola"].unique()))
    if years != EXPECTED_CROP_YEARS:
        raise ValueError(f"safras do algodão fora do pré-registro: {years}")
    if set(panel["crop"]) != {"cotton"} or set(panel["uf"]) != {"BA", "MT"}:
        raise ValueError("painel do algodão fora do contrato cotton/BA+MT")
    return panel


def _slope(sub: pd.DataFrame) -> float:
    """Inclinação OLS descritiva; usada nos diagnósticos sem erro assintótico."""
    x = sub["shock"].to_numpy(dtype=float)
    y = sub["logrev"].to_numpy(dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if x.size < 3:
        return np.nan
    xc = x - x.mean()
    denom = float(xc @ xc)
    if denom <= 0:
        return np.nan
    return float((xc @ (y - y.mean())) / denom)


def run_cotton_h1(panel: pd.DataFrame) -> pd.DataFrame:
    """Executa estimativa primária e diagnósticos pré-registrados, sem produzir o veredito."""
    years = tuple(sorted(panel["ano_agricola"].unique()))
    if years != EXPECTED_CROP_YEARS:
        raise ValueError(f"H1 algodão exige exatamente {EXPECTED_CROP_YEARS}; recebeu {years}")

    primary = ols_cluster(
        panel["shock"], panel["logrev"], panel["ano_agricola"], "cotton_h1:pooled"
    )
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

    for uf in ("BA", "MT"):
        sub = panel[panel["uf"] == uf]
        res = ols_cluster(sub["shock"], sub["logrev"], sub["ano_agricola"], f"cotton_h1:{uf}")
        rows.append(
            {
                "scope": "uf",
                "key": uf,
                "n": res.nobs,
                "n_clusters": res.n_clusters,
                "beta": res.beta,
                "se": res.se,
                "tstat": res.tstat,
                "pvalue": res.pvalue,
                "ci_low": res.ci_low,
                "ci_high": res.ci_high,
            }
        )

    for year in years:
        sub = panel[panel["ano_agricola"] == year]
        rows.append(
            {
                "scope": "crop_year",
                "key": year,
                "n": len(sub),
                "n_clusters": 1,
                "beta": _slope(sub),
            }
        )
        leave = panel[panel["ano_agricola"] != year]
        rows.append(
            {
                "scope": "leave_one_crop_year_out",
                "key": year,
                "n": len(leave),
                "n_clusters": leave["ano_agricola"].nunique(),
                "beta": _slope(leave),
            }
        )

    return pd.DataFrame(rows)


def cotton_h1_verdict(results: pd.DataFrame) -> CottonH1Verdict:
    """Aplica literalmente a regra D-048; não consulta significância."""
    pooled = results[(results["scope"] == "pooled") & (results["key"] == "all")]
    loo = results[results["scope"] == "leave_one_crop_year_out"]
    if len(pooled) != 1 or len(loo) != 3 or loo["beta"].isna().any():
        raise ValueError("resultado incompleto para o veredito D-048")
    beta = float(pooled.iloc[0]["beta"])
    negative = int((loo["beta"] < 0).sum())
    passed = beta < 0 and negative >= 2
    if passed:
        reason = f"corroborado: beta={beta:.4f}<0 e {negative}/3 LOO negativos"
    else:
        reason = f"não corroborado: beta={beta:.4f}; {negative}/3 LOO negativos"
    return CottonH1Verdict(passed, beta, negative, 3, reason)
