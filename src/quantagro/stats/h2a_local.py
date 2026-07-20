"""H2a-local — transmissão do Shock ao preço LOCAL brasileiro (último teste de preço, D-040).

D-037/D-039: o choque não transmite ao preço mundial (USD nem proxy mundial×câmbio), forward
nem contemporâneo. Falta o preço **local** (BRL, recebido pelo agricultor; ``ingest.ipea_prices``),
que embute a base doméstica e é o preço certo tanto do produtor (receita realizada) quanto do
processador (custo do milho brasileiro). Reaproveita o Shock nacional e a geometria de H2a; muda
só a fonte de preço. Desfechos: contemporâneo (``log(P[m]/P[base])``, base = mês antes da janela)
e forward (``log(P[m+h]/P[m])``, ``h`` primário). Sinal esperado ``β>0``.

É o **último** teste de preço pré-registrado (D-040): se também for nulo, o mecanismo de preço da
tese está morto; se transmitir, o canal de preço vive no mercado local (favorece o lado
processador e a receita realizada do produtor).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..stats.h2a import (
    CROPS,
    DEV_LAST_BASE,
    GATE_ALPHA,
    PRIMARY_HORIZON,
    _base_month,
    _fwd_return,
    _national_shocks,
    _obs_month_ends,
    _one_sided_p,
    _price_lookup,
    _stamp_grains,
)
from .inference import cluster_bootstrap, ols_cluster

LOCAL_OUTCOMES = ("contemp_local", "fwd_local")


def build_h2a_local_panel(
    local_prices: pd.DataFrame,
    municipal_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    conab: pd.DataFrame,
    climatology_first_year: int,
    bases: range = range(2018, 2025),
) -> pd.DataFrame:
    """Painel do teste local: ``(crop, safra, obs_month)`` com Shock nacional e retornos locais."""
    conab_stamped = _stamp_grains(conab)
    obs_points = [
        (crop, f"{base}/{(base + 1) % 100:02d}", t)
        for crop in CROPS
        for base in bases
        for t in _obs_month_ends(crop, f"{base}/{(base + 1) % 100:02d}")
    ]
    shocks = _national_shocks(
        obs_points, municipal_stamped, pam_panel, conab_stamped, climatology_first_year
    )
    price_by_crop = {crop: _price_lookup(local_prices, crop) for crop in CROPS}
    h = PRIMARY_HORIZON
    rows = []
    for crop, ano, t in obs_points:
        shock = shocks.get((crop, ano, t))
        if shock is None:
            continue
        price = price_by_crop[crop]
        base_m = _base_month(crop, ano)
        p0, p1 = price.get(base_m), price.get(t)
        contemp = (
            float(np.log(p1 / p0))
            if p0 is not None and p1 is not None and p0 > 0 and p1 > 0
            else np.nan
        )
        rows.append(
            {
                "crop": crop,
                "ano_agricola": ano,
                "base_year": int(ano[:4]),
                "obs_month": t.strftime("%Y-%m"),
                "shock": shock,
                "contemp_local": contemp,
                "fwd_local": _fwd_return(price, t, h),
                "cluster": f"{crop}:{ano}",
            }
        )
    panel = pd.DataFrame(rows)
    if panel.empty:
        raise ValueError("nenhuma observação do teste local computável")
    panel["sample"] = np.where(panel["base_year"] <= DEV_LAST_BASE, "dev", "holdout")
    return panel.sort_values(["crop", "ano_agricola", "obs_month"]).reset_index(drop=True)


def run_h2a_local(panel: pd.DataFrame) -> pd.DataFrame:
    """Regressões do teste local: desfecho ~ Shock, por escopo × pooled/cultura (β>0 esperado)."""
    rows = []
    scopes = {
        "full": panel,
        "dev": panel[panel["sample"] == "dev"],
        "holdout": panel[panel["sample"] == "holdout"],
    }
    for outcome in LOCAL_OUTCOMES:
        for scope_name, scope in scopes.items():
            for label, crop in [("pooled", None)] + [(c, c) for c in CROPS]:
                sub = scope if crop is None else scope[scope["crop"] == crop]
                sub = sub.dropna(subset=[outcome, "shock"])
                if sub["cluster"].nunique() < 2 or len(sub) < 3:
                    continue
                if crop is None:
                    x = (sub["shock"] - sub.groupby("crop")["shock"].transform("mean")).to_numpy()
                    y = (sub[outcome] - sub.groupby("crop")[outcome].transform("mean")).to_numpy()
                else:
                    x, y = sub["shock"].to_numpy(), sub[outcome].to_numpy()
                clusters = sub["cluster"].to_numpy()
                res = ols_cluster(x, y, clusters, f"local:{outcome}:{scope_name}:{label}")
                boot = cluster_bootstrap(x, y, clusters)
                rows.append(
                    {
                        "outcome": outcome,
                        "scope": scope_name,
                        "unit": label,
                        "n": res.nobs,
                        "n_clusters": res.n_clusters,
                        "beta": res.beta,
                        "tstat": res.tstat,
                        "boot_p_one_sided": _one_sided_p(res.beta, boot["pvalue"]),
                        "ci_low": res.ci_low,
                        "ci_high": res.ci_high,
                    }
                )
    return pd.DataFrame(rows)


@dataclass(frozen=True)
class LocalVerdict:
    """Veredito do último teste de preço (D-040)."""

    transmits: bool
    detail: str


def h2a_local_verdict(results: pd.DataFrame) -> LocalVerdict:
    """Transmite se algum desfecho pooled span-cheio tem β>0 com p unilateral < 0,10."""
    key = results[(results["scope"] == "full") & (results["unit"] == "pooled")]
    parts = []
    transmits = False
    for outcome in LOCAL_OUTCOMES:
        row = key[key["outcome"] == outcome]
        if row.empty:
            continue
        r = row.iloc[0]
        beta, p1 = float(r["beta"]), float(r["boot_p_one_sided"])
        ok = beta > 0 and p1 < GATE_ALPHA
        transmits = transmits or ok
        parts.append(f"{outcome}: β={beta:+.4f} p1={p1:.3f}{' *' if ok else ''}")
    detail = " | ".join(parts) if parts else "sem observações pooled span-cheio"
    return LocalVerdict(transmits, detail)
