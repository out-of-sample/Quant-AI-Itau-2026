"""H1b — o choque prevê a exportação física da cultura (ex post, D-026/D-030; corroboração).

Regressor: ``Shock`` **nacional** da safra (janela plenamente decorrida), ponderando UFs pelo
último levantamento CONAB da safra anterior (contrato congelado D-028) — por isso só é
computável de 2018/19 em diante (a safra anterior precisa existir no painel de vintages).

Desfecho: variação log ano-contra-ano do volume exportado (kg líquido) no ``h``-ésimo mês após
o fim da janela fenológica, ``h ∈ {3,4,5,6}``. Base **final** do ComexStat, ex post — sem
*vintage*; corrobora, não dimensiona (R18/D-026). Poder baixo (~7 safras); H1a é o motor do veto.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from ..features.shock import shock_asof
from ..features.shock_spec import PRIMARY_WINDOWS
from ..ingest.conab_calendar import attach_avail_date, conab_calendar
from .inference import moving_block_bootstrap, ols_hac

HORIZONS = (3, 4, 5, 6)
DEV_LAST_BASE = 2019  # safras ≤ 2019/20 = desenvolvimento; ≥ 2020/21 = holdout (D-029)

# NCM primário por cultura (D-030): grão. Farelo/óleo ficam para robustez.
CROP_NCM = {"soy": "12019000", "corn_second": "10059010"}
# Safras com painel de vintages CONAB (para os pesos nacionais da safra anterior).
_WEIGHT_BASES = range(2017, 2025)


def _anchor_month(crop: str) -> int:
    """Mês modal de fim de janela da cultura (soja=fev; milho 2ª=mai) — âncora da colheita."""
    ends = [s.end_month for s in PRIMARY_WINDOWS if s.crop == crop]
    return Counter(ends).most_common(1)[0][0]


def _stamp_grains(conab: pd.DataFrame) -> pd.DataFrame:
    """Carimba ``avail_date`` na fração soja/milho 2ª do painel — pesos nacionais de shock_asof.

    ``shock_asof`` filtra o CONAB por ``avail_date ≤ t`` por dentro (``conab_uf_weights``), então
    o painel precisa estar carimbado. Filtra a levs 1–12 e às safras cobertas pelo calendário.
    """
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


def _last_survey_avail(dataset: str = "graos") -> pd.DataFrame:
    """``avail_date`` do último levantamento de cada safra (janela plenamente decorrida)."""
    cal = conab_calendar(dataset)
    idx = cal.groupby("ano_agricola")["id_levantamento"].idxmax()
    return cal.loc[idx, ["ano_agricola", "avail_date"]].reset_index(drop=True)


def national_shocks(
    municipal_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    conab: pd.DataFrame,
    climatology_first_year: int,
    bases: range,
) -> pd.DataFrame:
    """``Shock`` nacional por ``(crop, safra)`` em ``t`` = ``avail_date`` do último levantamento."""
    conab = _stamp_grains(conab)
    last = _last_survey_avail().set_index("ano_agricola")["avail_date"]
    rows = []
    for base in bases:
        ano = f"{base}/{(base + 1) % 100:02d}"
        if ano not in last.index:
            continue
        t = pd.Timestamp(last.loc[ano])
        panel = shock_asof(t, ano, municipal_stamped, pam_panel, conab, climatology_first_year)
        nat = panel[(panel["level"] == "national") & (panel["status"] == "ok")]
        for r in nat.itertuples(index=False):
            rows.append(
                {"crop": r.crop, "ano_agricola": ano, "base_year": base, "shock": float(r.shock)}
            )
    return pd.DataFrame(rows)


def _yoy_dlog(export: pd.DataFrame, ncm: str, year: int, month: int) -> float:
    """Δlog ano-contra-ano do kg exportado no ``(year, month)`` vs ``(year-1, month)``."""
    s = export[export["co_ncm"] == ncm].set_index("ref_date")["metric_kg"]

    def kg(y: int, m: int) -> float:
        stamp = pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0)
        v = s.get(stamp.normalize())
        return float(v) if v is not None and v > 0 else np.nan

    cur, prev = kg(year, month), kg(year - 1, month)
    if not np.isfinite(cur) or not np.isfinite(prev):
        return np.nan
    return float(np.log(cur / prev))


def build_h1b_panel(
    export: pd.DataFrame,
    municipal_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    conab: pd.DataFrame,
    climatology_first_year: int,
    bases: range = range(2018, 2025),
) -> pd.DataFrame:
    """Painel de H1b: ``(crop, safra, h)`` com ``Shock`` nacional e Δlog da exportação em t+h."""
    shocks = national_shocks(municipal_stamped, pam_panel, conab, climatology_first_year, bases)
    if shocks.empty:
        raise ValueError("nenhum Shock nacional computável (safra anterior ausente?)")
    rows = []
    for r in shocks.itertuples(index=False):
        anchor = _anchor_month(r.crop)
        ncm = CROP_NCM[r.crop]
        for h in HORIZONS:
            target = pd.Timestamp(r.base_year + 1, anchor, 1) + pd.offsets.MonthBegin(h)
            dlog = _yoy_dlog(export, ncm, target.year, target.month)
            rows.append(
                {
                    "crop": r.crop,
                    "ano_agricola": r.ano_agricola,
                    "base_year": r.base_year,
                    "h": h,
                    "target_month": target.strftime("%Y-%m"),
                    "shock": r.shock,
                    "dlog_export": dlog,
                }
            )
    panel = pd.DataFrame(rows).dropna(subset=["dlog_export"])
    panel["sample"] = np.where(panel["base_year"] <= DEV_LAST_BASE, "dev", "holdout")
    return panel.sort_values(["crop", "h", "ano_agricola"]).reset_index(drop=True)


def run_h1b(panel: pd.DataFrame) -> pd.DataFrame:
    """Regressões de H1b: por cultura × horizonte, Newey–West + moving-block bootstrap.

    Sinal esperado ``β < 0`` (estresse ⇒ menos produção ⇒ menos exportação). N pequeno por
    construção — corroboração, não veto.
    """
    rows = []
    for crop in sorted(panel["crop"].unique()):
        for h in HORIZONS:
            sub = panel[(panel["crop"] == crop) & (panel["h"] == h)]
            if len(sub) < 3:
                continue
            maxlags = max(1, min(2, len(sub) - 2))
            res = ols_hac(sub["shock"], sub["dlog_export"], maxlags, f"h1b:{crop}:h{h}")
            boot = moving_block_bootstrap(
                sub["shock"].to_numpy(), sub["dlog_export"].to_numpy(), block=2
            )
            rows.append(
                {
                    "test": res.name,
                    "crop": crop,
                    "h": h,
                    "n": res.nobs,
                    "beta": res.beta,
                    "se": res.se,
                    "tstat": res.tstat,
                    "pvalue": res.pvalue,
                    "ci_low": res.ci_low,
                    "ci_high": res.ci_high,
                    "boot_pvalue": boot["pvalue"],
                }
            )
    return pd.DataFrame(rows)
