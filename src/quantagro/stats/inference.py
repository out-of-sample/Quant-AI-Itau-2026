"""Inferência que não mente para nós mesmos (docs/05_SUITE_ROBUSTEZ.md §6, D-030).

Três instrumentos, todos pensados para o regime de **N efetivo pequeno** deste projeto (a
safra é anual):

- ``ols_cluster`` / ``ols_hac``: OLS com erros agrupados por ano-safra (H1a) ou Newey–West HAC
  (H1b), via statsmodels — a espinha dorsal, bem testada.
- ``cluster_bootstrap`` / ``moving_block_bootstrap``: p-valores de robustez que não dependem da
  aproximação assintótica (que é frágil com poucos clusters).
- ``bh_fdr``: Benjamini–Hochberg sobre a família de testes, para não celebrar o falso positivo
  que sempre aparece quando se testa cultura × região × horizonte.

Nada aqui escolhe hipótese olhando resultado; o pré-registro é D-030.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass(frozen=True)
class RegResult:
    """Resultado de uma regressão simples ``y ~ α + β·x`` — só o que se reporta."""

    name: str
    beta: float
    se: float
    tstat: float
    pvalue: float
    nobs: int
    n_clusters: int | None
    ci_low: float
    ci_high: float
    cov_type: str


def _clean_xy(x, y) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape or x.ndim != 1:
        raise ValueError("x e y devem ser vetores 1-D do mesmo tamanho")
    ok = np.isfinite(x) & np.isfinite(y)
    return x[ok], y[ok], ok


def _slope_from(res, cov_type: str, nobs: int, n_clusters: int | None, name: str) -> RegResult:
    beta = float(res.params[1])
    se = float(res.bse[1])
    ci = res.conf_int()
    ci_low, ci_high = float(ci[1][0]), float(ci[1][1])
    return RegResult(
        name=name,
        beta=beta,
        se=se,
        tstat=float(res.tvalues[1]),
        pvalue=float(res.pvalues[1]),
        nobs=nobs,
        n_clusters=n_clusters,
        ci_low=ci_low,
        ci_high=ci_high,
        cov_type=cov_type,
    )


def ols_cluster(x, y, clusters, name: str = "") -> RegResult:
    """OLS ``y ~ α + β·x`` com erros agrupados por ``clusters`` (ex.: ano-safra)."""
    x, y, ok = _clean_xy(x, y)
    groups = np.asarray(clusters)[ok]
    if x.size < 3:
        raise ValueError(f"amostra pequena demais para regressão: n={x.size}")
    X = sm.add_constant(x)
    res = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    return _slope_from(res, "cluster", x.size, int(np.unique(groups).size), name)


def ols_hac(x, y, maxlags: int, name: str = "") -> RegResult:
    """OLS ``y ~ α + β·x`` com erros Newey–West (HAC) até ``maxlags``."""
    x, y, _ = _clean_xy(x, y)
    if x.size < 3:
        raise ValueError(f"amostra pequena demais para regressão: n={x.size}")
    X = sm.add_constant(x)
    res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags, "use_correction": True})
    return _slope_from(res, f"HAC({maxlags})", x.size, None, name)


def _ols_beta(x: np.ndarray, y: np.ndarray) -> float:
    xc = x - x.mean()
    denom = float((xc * xc).sum())
    if denom <= 0:
        return np.nan
    return float((xc * (y - y.mean())).sum() / denom)


def cluster_bootstrap(x, y, clusters, n_boot: int = 5000, seed: int = 20260717) -> dict[str, float]:
    """*Pairs cluster bootstrap*: reamostra clusters (ano-safra) inteiros com reposição.

    Devolve ``beta`` (pontual), IC percentil 90% e um p-valor bicaudal
    ``2·min(P(β*≤0), P(β*≥0))`` — robustez que não depende do assintótico com poucos clusters.
    """
    x, y, ok = _clean_xy(x, y)
    groups = np.asarray(clusters)[ok]
    beta_hat = _ols_beta(x, y)
    uniq = np.unique(groups)
    idx_by_g = {g: np.nonzero(groups == g)[0] for g in uniq}
    rng = np.random.default_rng(seed)
    betas = np.empty(n_boot, dtype=float)
    n_ok = 0
    for _ in range(n_boot):
        pick = rng.choice(uniq, size=uniq.size, replace=True)
        sel = np.concatenate([idx_by_g[g] for g in pick])
        bb = _ols_beta(x[sel], y[sel])
        if np.isfinite(bb):
            betas[n_ok] = bb
            n_ok += 1
    betas = betas[:n_ok]
    p = 2.0 * min((betas <= 0).mean(), (betas >= 0).mean())
    return {
        "beta": beta_hat,
        "ci_low": float(np.quantile(betas, 0.05)),
        "ci_high": float(np.quantile(betas, 0.95)),
        "pvalue": float(min(p, 1.0)),
        "n_clusters": int(uniq.size),
        "n_boot": int(n_ok),
    }


def moving_block_bootstrap(
    x, y, block: int, n_boot: int = 5000, seed: int = 20260717
) -> dict[str, float]:
    """*Moving-block bootstrap* para série temporal curta (H1b), preserva autocorrelação.

    Reamostra blocos contíguos de tamanho ``block`` até cobrir a série; p-valor bicaudal por
    recentragem em torno de zero. Poder baixo com poucas observações — robustez, não juiz.
    """
    x, y, _ = _clean_xy(x, y)
    n = x.size
    if block < 1 or block > n:
        raise ValueError(f"block {block} fora de [1, {n}]")
    beta_hat = _ols_beta(x, y)
    n_blocks = int(np.ceil(n / block))
    starts_max = n - block
    rng = np.random.default_rng(seed)
    betas = np.empty(n_boot, dtype=float)
    n_ok = 0
    for _ in range(n_boot):
        starts = rng.integers(0, starts_max + 1, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        bb = _ols_beta(x[idx], y[idx])
        if np.isfinite(bb):
            betas[n_ok] = bb
            n_ok += 1
    betas = betas[:n_ok]
    centered = betas - betas.mean()
    p = 2.0 * min((centered <= -abs(beta_hat)).mean(), (centered >= abs(beta_hat)).mean())
    return {
        "beta": beta_hat,
        "ci_low": float(np.quantile(betas, 0.05)),
        "ci_high": float(np.quantile(betas, 0.95)),
        "pvalue": float(min(p, 1.0)),
        "n_boot": int(n_ok),
    }


def bh_fdr(pvalues, alpha: float = 0.10) -> pd.DataFrame:
    """Benjamini–Hochberg sobre uma família de p-valores.

    Devolve DataFrame com ``pvalue``, ``qvalue`` (BH ajustado, monótono) e ``reject`` ao nível
    ``alpha``. Preserva a ordem de entrada.
    """
    p = np.asarray(pvalues, dtype=float)
    if p.ndim != 1 or p.size == 0:
        raise ValueError("pvalues deve ser vetor 1-D não vazio")
    if np.any((p < 0) | (p > 1)):
        raise ValueError("p-valores fora de [0,1]")
    m = p.size
    order = np.argsort(p, kind="mergesort")
    ranked = p[order]
    q_sorted = ranked * m / (np.arange(1, m + 1))
    # monotonicidade BH: q é o mínimo cumulativo de trás para frente
    q_sorted = np.minimum.accumulate(q_sorted[::-1])[::-1]
    q_sorted = np.clip(q_sorted, 0, 1)
    qvalue = np.empty(m, dtype=float)
    qvalue[order] = q_sorted
    return pd.DataFrame({"pvalue": p, "qvalue": qvalue, "reject": qvalue <= alpha})
