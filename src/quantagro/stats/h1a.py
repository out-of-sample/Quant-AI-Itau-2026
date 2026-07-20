"""H1a — o choque climático prevê a revisão da estimativa de safra da CONAB (D-030).

Painel ``(cultura, UF, safra, levantamento)``: a variável dependente é a **revisão log
acumulada** da estimativa de produção desde o primeiro levantamento presente; o regressor é o
``Shock`` da UF acumulado até a **data de publicação** daquele levantamento (``avail_date``,
fixo no corte — D-028). Inferência agrupada por ano-safra + BH-FDR sobre a família (stats).

O ``Shock`` de H1a é por UF (``uf_shock_asof``), então não depende do peso nacional CONAB (que
exigiria a safra anterior, ausente do painel de vintages para a primeira safra). Cada ``Shock``
filtra ``avail_date ≤ t`` por dentro; a revisão usa só levantamentos publicados até ``t``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..features.shock import PRELIM_LAG_DAYS, PRIMARY_SIGNAL_KIND, uf_shock_asof
from ..features.shock_spec import PRIMARY_WINDOWS, CropRegionWindow, critical_period
from ..ingest.conab_calendar import attach_avail_date
from ..ingest.pam import pam_weights_asof
from ..validate.pit import available_asof
from .inference import cluster_bootstrap, ols_cluster

_PROD_COL = "producao_mil_t"
DEV_LAST_BASE = 2019  # safras ≤ 2019/20 = desenvolvimento; ≥ 2020/21 = holdout (D-029)


def _window_contract(
    windows: tuple[CropRegionWindow, ...],
) -> tuple[dict[str, tuple[str, str]], dict[str, tuple[str, ...]]]:
    """Deriva produto/safra/UF do contrato congelado, sem mapa paralelo sujeito a drift."""
    if not windows:
        raise ValueError("windows não pode ser vazio")
    filters: dict[str, tuple[str, str]] = {}
    ufs: dict[str, set[str]] = {}
    for spec in windows:
        pair = (spec.conab_product, spec.conab_season)
        previous = filters.setdefault(spec.crop, pair)
        if previous != pair:
            raise ValueError(f"contrato CONAB inconsistente para {spec.crop}: {previous} vs {pair}")
        ufs.setdefault(spec.crop, set()).add(spec.uf)
    return filters, {crop: tuple(sorted(values)) for crop, values in ufs.items()}


def _prepare_conab(
    conab: pd.DataFrame,
    bases: range,
    windows: tuple[CropRegionWindow, ...] = PRIMARY_WINDOWS,
) -> pd.DataFrame:
    """Filtra o painel bruto ao contrato cultura/UF/safra e carimba ``avail_date``."""
    anos = {f"{b}/{(b + 1) % 100:02d}" for b in bases}
    crop_filter, crop_ufs = _window_contract(windows)
    keep = []
    for crop, (produto, safra) in crop_filter.items():
        sub = conab[
            (conab["produto"] == produto)
            & (conab["safra"] == safra)
            & (conab["uf"].isin(crop_ufs[crop]))
            & (conab["ano_agricola"].isin(anos))
            & (conab["id_levantamento"].between(1, 12))
        ].copy()
        sub["crop"] = crop
        keep.append(sub)
    out = pd.concat(keep, ignore_index=True)
    return attach_avail_date(out, "graos")


def _revisions(conab: pd.DataFrame) -> pd.DataFrame:
    """Revisão log acumulada por ``(crop, uf, safra, lev>base)``; base = 1º lev presente."""
    rows = []
    for (crop, uf, ano), grp in conab.groupby(["crop", "uf", "ano_agricola"], sort=False):
        grp = grp.sort_values("id_levantamento")
        prod = grp.set_index("id_levantamento")[_PROD_COL]
        prod = prod[prod > 0]
        if prod.size < 2:
            continue
        base_lev = int(prod.index.min())
        prod_base = float(prod.loc[base_lev])
        avail = grp.set_index("id_levantamento")["avail_date"]
        for lev, value in prod.items():
            if int(lev) == base_lev:
                continue
            rows.append(
                {
                    "crop": crop,
                    "uf": uf,
                    "ano_agricola": ano,
                    "id_levantamento": int(lev),
                    "base_lev": base_lev,
                    "avail_date": pd.Timestamp(avail.loc[lev]),
                    "logrev": float(np.log(float(value) / prod_base)),
                }
            )
    return pd.DataFrame(rows)


def _shocks(
    rev: pd.DataFrame,
    municipal_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    climatology_first_year: int,
    windows: tuple[CropRegionWindow, ...] = PRIMARY_WINDOWS,
) -> pd.DataFrame:
    """``Shock`` de UF em cada ``(safra, avail_date)``, memoizado por ``(spec, ano, corte, PAM)``.

    Levantamentos tardios de uma safra veem a janela plenamente decorrida ⇒ mesmo corte ⇒ mesmo
    ``Shock``. O corte é ``min(window_end, último ref prelim visível)``; a edição PAM as-of ``t``
    também entra na chave (pesos mudam quando uma nova PAM é divulgada no meio da safra, D-028). O
    ``available_asof`` grande do painel municipal só roda em cache-miss.
    """
    prelim_refs = np.sort(
        municipal_stamped.loc[municipal_stamped["kind"] == PRIMARY_SIGNAL_KIND, "ref_date"].unique()
    )
    # Pré-split por UF: cada spec só toca os municípios da sua UF, então `uf_shock_asof` varre
    # ~1/7 do painel em vez dos 16M — sem mudar nenhum resultado (os pesos já são por UF).
    by_uf = {uf: sub for uf, sub in municipal_stamped.groupby("uf", sort=False)}
    rows = []
    cache: dict[tuple, dict] = {}
    for (ano, t), _ in rev.groupby(["ano_agricola", "avail_date"], sort=False):
        ts = pd.Timestamp(t)
        weights = pam_weights_asof(pam_panel, ts)
        pam_year = int(weights["ref_year"].max())
        cutoff = (ts - pd.Timedelta(days=PRELIM_LAG_DAYS)).to_datetime64()
        pos = int(np.searchsorted(prelim_refs, cutoff, side="right"))
        vis_max = pd.Timestamp(prelim_refs[pos - 1]) if pos > 0 else None
        visible_by_uf: dict[str, pd.DataFrame] = {}
        for spec in windows:
            # Chave pelo CORTE efetivo (não pelo vis_max cru): depois do fim da janela o corte
            # fica preso em window_end e o Shock é idêntico entre levantamentos tardios.
            w_start, w_end = critical_period(spec, ano)
            cut_eff = min(w_end, vis_max) if vis_max is not None and vis_max >= w_start else None
            key = (spec.key, ano, cut_eff, pam_year)
            r = cache.get(key)
            if r is None:
                if spec.uf not in visible_by_uf:
                    visible_by_uf[spec.uf] = available_asof(by_uf[spec.uf], ts)
                r = uf_shock_asof(
                    ts, ano, spec, visible_by_uf[spec.uf], weights, climatology_first_year
                )
                cache[key] = r
            if r["status"] != "ok":
                continue
            rows.append(
                {
                    "crop": spec.crop,
                    "uf": spec.uf,
                    "ano_agricola": ano,
                    "avail_date": ts,
                    "shock": float(r["shock"]),
                    "cut_date": r["cut_date"],
                    "elapsed_days": r["elapsed_days"],
                    "n_clim_years": int(r["n_clim_years"]),
                }
            )
    return pd.DataFrame(rows)


def build_h1a_panel(
    conab: pd.DataFrame,
    municipal_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    climatology_first_year: int,
    bases: range = range(2017, 2025),
    windows: tuple[CropRegionWindow, ...] = PRIMARY_WINDOWS,
) -> pd.DataFrame:
    """Painel de regressão de H1a: ``(cultura, UF, safra, levantamento≥base+1)`` com revisão+Shock.

    ``municipal_stamped`` já carimbado (``stamp_municipal_panel``). ``bases`` = primeiros anos
    das safras com painel de vintages (2017/18+) **e** sinal ``prelim`` disponível.
    """
    conab = _prepare_conab(conab, bases, windows)
    rev = _revisions(conab)
    if rev.empty:
        raise ValueError("nenhuma revisão computável no painel CONAB filtrado")
    shocks = _shocks(rev, municipal_stamped, pam_panel, climatology_first_year, windows)
    panel = rev.merge(shocks, on=["crop", "uf", "ano_agricola", "avail_date"], how="inner")
    panel["base_year"] = panel["ano_agricola"].str.slice(0, 4).astype(int)
    panel["sample"] = np.where(panel["base_year"] <= DEV_LAST_BASE, "dev", "holdout")
    return panel.sort_values(["crop", "uf", "ano_agricola", "id_levantamento"]).reset_index(
        drop=True
    )


def _one_regression(sub: pd.DataFrame, name: str) -> dict:
    res = ols_cluster(sub["shock"], sub["logrev"], sub["ano_agricola"], name)
    boot = cluster_bootstrap(sub["shock"], sub["logrev"], sub["ano_agricola"])
    return {
        "test": name,
        "n": res.nobs,
        "n_clusters": res.n_clusters,
        "beta": res.beta,
        "se": res.se,
        "tstat": res.tstat,
        "pvalue": res.pvalue,
        "ci_low": res.ci_low,
        "ci_high": res.ci_high,
        "boot_pvalue": boot["pvalue"],
        "boot_ci_low": boot["ci_low"],
        "boot_ci_high": boot["ci_high"],
    }


def run_h1a(panel: pd.DataFrame) -> pd.DataFrame:
    """Regressões de H1a: agrupada e por cultura, no span cheio e nas sub-amostras dev/holdout.

    Sinal esperado ``β < 0`` (estresse ⇒ revisão para baixo). BH-FDR é aplicado depois, sobre a
    família completa H1a+H1b (ver ``gate``).
    """
    rows = []
    specs = [("pooled", panel)]
    for crop in sorted(panel["crop"].unique()):
        specs.append((f"crop={crop}", panel[panel["crop"] == crop]))
    for name, sub in specs:
        rows.append({"scope": "full", **_one_regression(sub, f"h1a:{name}")})
        for sample in ("dev", "holdout"):
            ss = sub[sub["sample"] == sample]
            if ss["ano_agricola"].nunique() >= 2 and len(ss) >= 3:
                rows.append({"scope": sample, **_one_regression(ss, f"h1a:{name}:{sample}")})
    return pd.DataFrame(rows)
