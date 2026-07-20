"""Teste de reação das ações (Fase 3.2, D-042) — o score `E·Shock` ordena os retornos?

Primeiro teste que toca retorno de ação, **só no desenvolvimento** (o holdout protege retorno).
Reaproveita o Shock nacional de H2a e a matriz de exposição PIT. Score por nome e data:
``S_i(t) = Σ_c E_i,c(t) · Shock_c(t)`` (cultura com janela não iniciada contribui 0). Desfecho:
retorno total forward de ``H`` pregões, execução D+1. Teste primário: painel com retorno e score
**demeanados na seção transversal por data** (remove o comum/mercado), OLS agrupado por ano-safra
+ bootstrap; ``β>0`` esperado. Neutro a mercado por construção. Direcional (amostra pequena).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..features.exposure import exposure_asof
from .h2a import CROPS, _national_shocks, _obs_month_ends, _stamp_grains
from .inference import cluster_bootstrap, ols_cluster

FWD_DAYS = 21  # pregões do retorno forward (~1 mês)
DEV_LAST_BASE = 2019


def _union_obs_dates(ano: str) -> list[pd.Timestamp]:
    """Fins de mês nas janelas de soja OU milho na safra — datas de observação do score."""
    dates = set(_obs_month_ends("soy", ano)) | set(_obs_month_ends("corn_second", ano))
    return sorted(dates)


def _forward_return(index: pd.Series, t: pd.Timestamp, h: int) -> float:
    """Retorno log forward: entra em D+1 (1º pregão após ``t``), sai ``h`` pregões depois."""
    pos = int(index.index.searchsorted(t, side="right"))  # 1º pregão estritamente após t = D+1
    if pos >= len(index) or pos + h >= len(index):
        return np.nan
    p0, p1 = float(index.iloc[pos]), float(index.iloc[pos + h])
    if not (p0 > 0 and p1 > 0):
        return np.nan
    return float(np.log(p1 / p0))


def build_equity_reaction_panel(
    returns: pd.DataFrame,
    registry: pd.DataFrame,
    municipal_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    conab: pd.DataFrame,
    climatology_first_year: int,
    bases: range = range(2015, 2020),
    fwd_days: int = FWD_DAYS,
) -> pd.DataFrame:
    """Painel ``(data, ticker)``: score ``E·Shock`` as-of ``t`` e retorno forward do nome."""
    conab_stamped = _stamp_grains(conab)
    # índice de retorno total por nome (para o retorno forward)
    idx = {c: (1.0 + returns[c].dropna()).cumprod() for c in returns.columns}
    # todas as (crop, ano, t) para o Shock nacional
    obs_by_ano = {
        f"{b}/{(b + 1) % 100:02d}": _union_obs_dates(f"{b}/{(b + 1) % 100:02d}") for b in bases
    }
    obs_points = [
        (crop, ano, t) for ano, dates in obs_by_ano.items() for t in dates for crop in CROPS
    ]
    # Shock nacional equal-weighted (sem CONAB da safra anterior) → cobre o dev inteiro
    # (2015/16+), 5 safras em vez de 2; simplificação declarada para o diagnóstico (D-042).
    shocks = _national_shocks(
        obs_points,
        municipal_stamped,
        pam_panel,
        conab_stamped,
        climatology_first_year,
        weighting="equal",
    )
    rows = []
    for ano, dates in obs_by_ano.items():
        for t in dates:
            sh = {c: shocks.get((c, ano, t), 0.0) for c in CROPS}
            if all(v == 0.0 for v in sh.values()):
                continue  # nenhuma cultura com Shock observável em t
            expo = exposure_asof(registry, t)  # ticker × crop × exposure PIT
            if expo.empty:
                continue
            for ticker, g in expo.groupby("ticker"):
                e = dict(zip(g["crop"], g["exposure"], strict=False))
                score = sum(e.get(c, 0.0) * sh[c] for c in CROPS)
                if ticker not in idx:
                    continue
                fwd = _forward_return(idx[ticker], t, fwd_days)
                rows.append(
                    {
                        "date": t,
                        "ticker": ticker,
                        "ano_agricola": ano,
                        "score": float(score),
                        "fwd_ret": fwd,
                    }
                )
    panel = pd.DataFrame(rows).dropna(subset=["fwd_ret"])
    if panel.empty:
        raise ValueError("nenhuma observação de reação computável")
    return panel.sort_values(["date", "ticker"]).reset_index(drop=True)


def _demean_by_date(panel: pd.DataFrame, col: str) -> pd.Series:
    """Remove a média da seção transversal (por data) — neutraliza o componente comum/mercado."""
    return panel[col] - panel.groupby("date")[col].transform("mean")


@dataclass(frozen=True)
class ReactionVerdict:
    reacts: bool
    beta: float
    boot_p_one_sided: float
    n: int
    n_clusters: int
    detail: str


def run_equity_reaction(panel: pd.DataFrame) -> dict:
    """Teste primário (painel demeanado) + P&L da carteira dollar-neutral. β>0 esperado."""
    # só datas com ≥2 nomes (demeaning transversal precisa de variação na data)
    counts = panel.groupby("date")["ticker"].transform("count")
    p = panel[counts >= 2].copy()
    x = _demean_by_date(p, "score").to_numpy()
    y = _demean_by_date(p, "fwd_ret").to_numpy()
    clusters = p["ano_agricola"].to_numpy()
    res = ols_cluster(x, y, clusters, "equity:xsection")
    boot = cluster_bootstrap(x, y, clusters)
    p1 = boot["pvalue"] / 2 if res.beta > 0 else 1 - boot["pvalue"] / 2

    # P&L: carteira dollar-neutral ponderada pelo score, retorno médio forward por data
    def _pnl(grp: pd.DataFrame) -> float:
        s = grp["score"] - grp["score"].mean()
        if s.abs().sum() == 0:
            return np.nan
        w = s / s.abs().sum()  # dollar-neutral (Σw=0), bruto=1
        return float((w * grp["fwd_ret"]).sum())

    pnl = p.groupby("date", group_keys=False).apply(_pnl, include_groups=False).dropna()

    per_name = (
        panel.groupby("ticker")
        .apply(
            lambda g: pd.Series({"n": len(g), "corr_score_ret": g["score"].corr(g["fwd_ret"])}),
            include_groups=False,
        )
        .reset_index()
    )
    return {
        "primary": {
            "beta": res.beta,
            "tstat": res.tstat,
            "n": res.nobs,
            "n_clusters": res.n_clusters,
            "boot_p_one_sided": p1,
            "ci_low": res.ci_low,
            "ci_high": res.ci_high,
        },
        "pnl": {
            "mean": float(pnl.mean()),
            "std": float(pnl.std()),
            "n_periods": int(len(pnl)),
            "hit_rate": float((pnl > 0).mean()),
        },
        "per_name": per_name,
    }


def reaction_verdict(result: dict, alpha: float = 0.10) -> ReactionVerdict:
    """Reage se o painel primário tem β>0 com p unilateral < alpha."""
    pr = result["primary"]
    beta, p1 = float(pr["beta"]), float(pr["boot_p_one_sided"])
    reacts = beta > 0 and p1 < alpha
    detail = (
        f"β={beta:+.4f} p1(boot)={p1:.3f} n={pr['n']} clusters={pr['n_clusters']} | "
        f"P&L médio={result['pnl']['mean']:+.4f} hit={result['pnl']['hit_rate']:.2f}"
    )
    return ReactionVerdict(reacts, beta, p1, int(pr["n"]), int(pr["n_clusters"]), detail)
