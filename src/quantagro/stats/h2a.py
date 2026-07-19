"""H2a — o ``Shock`` brasileiro prevê o preço mundial da commodity (portão do lado long, D-036).

Pré-registro (D-036), congelado antes de qualquer resultado:

- **Regressor**: ``Shock`` **nacional** as-of ``t`` (contrato D-028; pesos da safra CONAB
  anterior encerrada), calculado em cada **fim de mês dentro da janela** fenológica da cultura.
  Só computável de 2018/19 em diante (a safra anterior precisa existir no painel de vintages).
- **Desfecho**: retorno log **forward** do preço mundial (FRED/IMF, ``ingest.fred_prices``) do
  mês de observação ``m`` até ``m+h``: ``r = log(P[m+h]/P[m])``. Inteiramente posterior a ``t``
  (ressalva de execução: o IMF publica ``P[m]`` ~3 semanas depois; é lag de execução, não
  look-ahead). Horizonte primário ``h=3``; ``h∈{1,2,3}`` como robustez.
- **Sinal esperado**: ``β > 0`` (estresse ⇒ menos oferta ⇒ preço sobe). Oposto de H1a/H1b.
- **Perímetro (D-036, princípio D-029)**: teste de mecanismo, roda no **span cheio**
  2018/19–2024/25 com sub-amostras dev (≤2019/20) e holdout reportadas em separado. O veredito
  do portão olha o agregado; o desenho da carteira segue calibrado só no desenvolvimento.
- **Inferência**: cluster por ``ano-safra × cultura`` (OLS cluster-robusto) + *pairs cluster
  bootstrap*; pooled com efeito fixo de cultura (demeaning intra-cultura). N efetivo reportado.
- **Regra do portão (direcional + ressalva)**: no h primário, span cheio, pooled —
  ``β>0`` e p unilateral < 0,10 ⇒ **PASSA**; ``β>0`` sem significância ⇒ **INCONCLUSIVO**
  (long segue com ressalva, confirmar no holdout); ``β<0`` significativo ⇒ **REPROVA**
  (reformula o lado long).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..features.shock import shock_asof
from ..features.shock_spec import PRIMARY_WINDOWS, critical_period
from ..ingest.conab_calendar import attach_avail_date
from .inference import cluster_bootstrap, ols_cluster

HORIZONS = (1, 2, 3)
PRIMARY_HORIZON = 3
DEV_LAST_BASE = 2019  # safras ≤ 2019/20 = desenvolvimento; ≥ 2020/21 = holdout (D-029)
GATE_ALPHA = 0.10
_WEIGHT_BASES = range(2017, 2025)  # safras com painel de vintages CONAB p/ pesos nacionais
CROPS = ("soy", "corn_second")


def _stamp_grains(conab: pd.DataFrame) -> pd.DataFrame:
    """Carimba ``avail_date`` na fração soja/milho 2ª (idêntico a H1b — pesos de ``shock_asof``)."""
    anos = {f"{b}/{(b + 1) % 100:02d}" for b in _WEIGHT_BASES}
    sub = conab[
        (
            ((conab["produto"] == "SOJA") & (conab["safra"] == "UNICA"))
            | ((conab["produto"] == "MILHO") & (conab["safra"] == "2ª SAFRA"))
        )
        & conab["id_levantamento"].between(1, 12)
        & conab["ano_agricola"].isin(anos)
    ].copy()
    return attach_avail_date(sub, "graos")


def _national_window(crop: str, ano: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """União das janelas de UF da cultura na safra: (menor início, maior fim)."""
    specs = [s for s in PRIMARY_WINDOWS if s.crop == crop]
    starts, ends = [], []
    for s in specs:
        a, b = critical_period(s, ano)
        starts.append(a)
        ends.append(b)
    return min(starts), max(ends)


def _obs_month_ends(crop: str, ano: str) -> list[pd.Timestamp]:
    """Fins de mês dentro da janela nacional da cultura — datas de observação de H2a."""
    start, end = _national_window(crop, ano)
    first = (start + pd.offsets.MonthEnd(0)).normalize()
    out = []
    m = first
    while m <= end:
        out.append(m)
        m = (m + pd.offsets.MonthEnd(1)).normalize()
    return out


def _price_lookup(prices: pd.DataFrame, crop: str) -> pd.Series:
    """Série de preço mensal (índice = fim de mês) para a cultura."""
    s = prices[prices["crop"] == crop].set_index("ref_date")["price"]
    return s[~s.index.duplicated()].sort_index()


def _fwd_return(price: pd.Series, obs_month_end: pd.Timestamp, h: int) -> float:
    """``log(P[m+h]/P[m])`` — retorno forward do mês de observação a ``m+h``."""
    base = obs_month_end
    target = (obs_month_end + pd.offsets.MonthEnd(h)).normalize()
    p0 = price.get(base)
    p1 = price.get(target)
    if p0 is None or p1 is None or not (p0 > 0 and p1 > 0):
        return np.nan
    return float(np.log(p1 / p0))


def build_h2a_panel(
    prices: pd.DataFrame,
    municipal_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    conab: pd.DataFrame,
    climatology_first_year: int,
    bases: range = range(2018, 2025),
) -> pd.DataFrame:
    """Painel de H2a: ``(crop, safra, obs_month, h)`` com ``Shock`` nacional e retorno forward."""
    conab = _stamp_grains(conab)
    rows = []
    for crop in CROPS:
        price = _price_lookup(prices, crop)
        for base in bases:
            ano = f"{base}/{(base + 1) % 100:02d}"
            for t in _obs_month_ends(crop, ano):
                panel = shock_asof(
                    t, ano, municipal_stamped, pam_panel, conab, climatology_first_year
                )
                nat = panel[
                    (panel["level"] == "national")
                    & (panel["crop"] == crop)
                    & (panel["status"] == "ok")
                ]
                if nat.empty:
                    continue
                shock = float(nat["shock"].iloc[0])
                for h in HORIZONS:
                    r = _fwd_return(price, t, h)
                    rows.append(
                        {
                            "crop": crop,
                            "ano_agricola": ano,
                            "base_year": base,
                            "obs_month": t.strftime("%Y-%m"),
                            "h": h,
                            "target_month": (t + pd.offsets.MonthEnd(h)).strftime("%Y-%m"),
                            "shock": shock,
                            "fwd_ret": r,
                            "cluster": f"{crop}:{ano}",
                        }
                    )
    panel = pd.DataFrame(rows).dropna(subset=["fwd_ret"])
    if panel.empty:
        raise ValueError("nenhuma observação H2a computável (Shock nacional / preço ausente?)")
    panel["sample"] = np.where(panel["base_year"] <= DEV_LAST_BASE, "dev", "holdout")
    return panel.sort_values(["crop", "h", "ano_agricola", "obs_month"]).reset_index(drop=True)


def _demean_within_crop(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Remove a média por cultura de ``shock`` e ``fwd_ret`` — efeito fixo de cultura no pooled."""
    x = df["shock"] - df.groupby("crop")["shock"].transform("mean")
    y = df["fwd_ret"] - df.groupby("crop")["fwd_ret"].transform("mean")
    return x.to_numpy(), y.to_numpy()


def _one_sided_p(beta: float, two_sided_p: float, expected_positive: bool = True) -> float:
    """p unilateral na direção esperada a partir do bicaudal simétrico."""
    if expected_positive:
        return two_sided_p / 2 if beta > 0 else 1 - two_sided_p / 2
    return two_sided_p / 2 if beta < 0 else 1 - two_sided_p / 2


def run_h2a(panel: pd.DataFrame) -> pd.DataFrame:
    """Regressões de H2a por (escopo × cultura/pooled × horizonte). Sinal esperado ``β>0``."""
    rows = []
    scopes = {
        "full": panel,
        "dev": panel[panel["sample"] == "dev"],
        "holdout": panel[panel["sample"] == "holdout"],
    }
    for scope_name, scope in scopes.items():
        for h in HORIZONS:
            sub_h = scope[scope["h"] == h]
            # pooled (efeito fixo de cultura) + por cultura
            specs = [("pooled", None)] + [(c, c) for c in CROPS]
            for label, crop in specs:
                sub = sub_h if crop is None else sub_h[sub_h["crop"] == crop]
                if sub["cluster"].nunique() < 2 or len(sub) < 3:
                    continue
                if crop is None:
                    x, y = _demean_within_crop(sub)
                else:
                    x, y = sub["shock"].to_numpy(), sub["fwd_ret"].to_numpy()
                clusters = sub["cluster"].to_numpy()
                res = ols_cluster(x, y, clusters, f"h2a:{scope_name}:{label}:h{h}")
                boot = cluster_bootstrap(x, y, clusters)
                rows.append(
                    {
                        "scope": scope_name,
                        "unit": label,
                        "h": h,
                        "n": res.nobs,
                        "n_clusters": res.n_clusters,
                        "beta": res.beta,
                        "se": res.se,
                        "tstat": res.tstat,
                        "pvalue": res.pvalue,
                        "p_one_sided": _one_sided_p(res.beta, res.pvalue),
                        "boot_p": boot["pvalue"],
                        "boot_p_one_sided": _one_sided_p(res.beta, boot["pvalue"]),
                        "ci_low": res.ci_low,
                        "ci_high": res.ci_high,
                    }
                )
    return pd.DataFrame(rows)


@dataclass(frozen=True)
class H2aVerdict:
    """Veredito do portão do lado long (D-036)."""

    status: str  # PASSA | INCONCLUSIVO | REPROVA
    beta: float
    boot_p_one_sided: float
    n: int
    n_clusters: int
    reason: str


def h2a_verdict(results: pd.DataFrame) -> H2aVerdict:
    """Aplica a regra direcional pré-registrada ao h primário, span cheio, pooled."""
    row = results[
        (results["scope"] == "full")
        & (results["unit"] == "pooled")
        & (results["h"] == PRIMARY_HORIZON)
    ]
    if row.empty:
        return H2aVerdict("INCONCLUSIVO", np.nan, np.nan, 0, 0, "sem observações no h primário")
    r = row.iloc[0]
    beta, p1 = float(r["beta"]), float(r["boot_p_one_sided"])
    p_neg = 1 - p1  # p unilateral do lado negativo (β<0)
    if beta > 0 and p1 < GATE_ALPHA:
        status, reason = "PASSA", f"β>0 e p unilateral (bootstrap)={p1:.3f}<{GATE_ALPHA}"
    elif beta > 0:
        status, reason = "INCONCLUSIVO", f"β>0 mas p unilateral={p1:.3f}≥{GATE_ALPHA} (poder baixo)"
    elif beta < 0 and p_neg < GATE_ALPHA:
        status, reason = "REPROVA", f"β<0 significativo (p unilateral lado negativo={p_neg:.3f})"
    else:
        status, reason = "INCONCLUSIVO", f"β<0 não significativo (p lado negativo={p_neg:.3f})"
    return H2aVerdict(status, beta, p1, int(r["n"]), int(r["n_clusters"]), reason)
