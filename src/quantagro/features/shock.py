"""Cálculo do ``Shock`` primário — implementação do contrato congelado (D-023, `01_TESE` §3.1).

Tudo aqui é função de uma data de decisão ``t``: o que entra é somente o que tinha
``avail_date ≤ t``. O caminho é o pré-registrado:

    painel municipal CHIRPS (``features/regionalize.py``)
      → acumulado da janela fenológica até a data de corte (produto ``prelim``)
      → climatologia expanding do MESMO trecho em safras anteriores (produto ``final``)
      → ``z`` → ``Shock = −z``  (estresse: seco ⇒ positivo)
      → UF (peso municipal PAM *as-of* ``t``, D-024)
      → nacional (peso de produção da safra CONAB anterior já encerrada, nunca a corrente).

Decisões de implementação dentro desse contrato (D-028):

- **Mesmo trecho por deslocamento**: o acumulado parcial até ``d`` dias após o início da
  janela é comparado com o acumulado dos mesmos ``d`` dias das safras anteriores (trechos de
  comprimento igual; um dia de borda em ano bissexto é irrelevante e mantém a comparação
  limpa).
- **Pesos espaciais únicos em ``t``**: a PAM *as-of* ``t`` pondera tanto o trecho corrente
  quanto a climatologia — apples-to-apples espacial, e é informação disponível em ``t``.
- **Climatologia com anos explícitos e cobertura obrigatória**: o chamador declara o primeiro
  ano-safra; toda safra do intervalo precisa de cobertura diária completa, senão o cálculo
  falha alto (pular ano silenciosamente mudaria a climatologia sem registro).
- **Carimbo por produto**: ``prelim`` fica público em ~2 dias (lag congelado de 7); ``final``
  sai ~1 mês depois (lag conservador de 60). Um único lag para os dois superestimaria a
  disponibilidade do ``final``.
- **Nacional renormalizado sobre janelas já iniciadas**: antes de todas as UFs entrarem na
  janela, o índice usa as que já entraram e reporta ``uf_coverage_weight`` — composição
  visível, nunca imputada.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantagro.features.shock_spec import (
    CLIMATOLOGY_KIND,
    EXPANDING_STD_DDOF,
    MIN_EXPANDING_YEARS,
    PRECIP_Z_TO_STRESS,
    PRIMARY_SIGNAL_KIND,
    PRIMARY_WINDOWS,
    CropRegionWindow,
    critical_period,
    crop_year_start,
)
from quantagro.ingest.pam import pam_weights_asof
from quantagro.validate.pit import AVAIL_COL, available_asof, stamp_avail_date

# O milho 2ª safra usa o milho total da PAM como proxy espacial declarado (D-023/R15).
PAM_CROP_FOR: dict[str, str] = {"soy": "soy", "corn_second": "corn_total"}

# Lags de publicação por produto CHIRPS (dias corridos): prelim é o caso primário congelado
# (01_TESE §5); final sai ~1 mês depois da referência — 60 dias é conservador de propósito.
PRELIM_LAG_DAYS = 7
FINAL_LAG_DAYS = 60

_PRODUCTION_COL = "producao_mil_t"


def _ano_agricola(start_year: int) -> str:
    return f"{start_year}/{(start_year + 1) % 100:02d}"


def stamp_municipal_panel(municipal: pd.DataFrame) -> pd.DataFrame:
    """Carimba ``avail_date`` no painel municipal, com o lag correto de cada produto."""
    unknown = set(municipal["kind"].unique()) - {PRIMARY_SIGNAL_KIND, CLIMATOLOGY_KIND}
    if unknown:
        raise ValueError(f"kind desconhecido no painel municipal: {sorted(unknown)}")
    parts = []
    for kind, lag in ((PRIMARY_SIGNAL_KIND, PRELIM_LAG_DAYS), (CLIMATOLOGY_KIND, FINAL_LAG_DAYS)):
        sub = municipal[municipal["kind"] == kind]
        if not sub.empty:
            parts.append(stamp_avail_date(sub, lag_days=lag))
    return pd.concat(parts, ignore_index=True)


def conab_uf_weights(
    conab: pd.DataFrame, spec: CropRegionWindow, ufs, ano_agricola: str, t
) -> pd.Series:
    """Peso de produção por UF da safra CONAB **anterior** já divulgada em ``t``.

    Usa o levantamento mais recente disponível da safra anterior (para uma safra encerrada,
    é o 12º). A corrente nunca entra: é a revisão dela que o sinal quer prever (§3.1). UF do
    suporte sem produção divulgada é erro, não zero silencioso.
    """
    prev = _ano_agricola(crop_year_start(ano_agricola) - 1)
    visible = available_asof(conab, t)
    rows = visible[
        (visible["produto"] == spec.conab_product)
        & (visible["safra"] == spec.conab_season)
        & (visible["ano_agricola"] == prev)
        & (visible["uf"].isin(list(ufs)))
    ]
    if rows.empty:
        raise ValueError(
            f"nenhum levantamento CONAB de {spec.conab_product}/{spec.conab_season} "
            f"da safra {prev} disponível em {pd.Timestamp(t).date()}"
        )
    latest = rows[rows["id_levantamento"] == rows["id_levantamento"].max()]
    prod = latest.set_index("uf")[_PRODUCTION_COL]
    missing = sorted(set(ufs) - set(prod.index))
    if missing:
        raise ValueError(f"UF do suporte sem produção CONAB na safra {prev}: {missing}")
    prod = prod.loc[list(ufs)].astype(float)
    if (prod < 0).any() or prod.sum() <= 0:
        raise ValueError(f"produção CONAB inválida na safra {prev}: {prod.to_dict()}")
    return prod / prod.sum()


def _stretch_sum(
    municipal: pd.DataFrame, kind: str, codes: pd.Index, start: pd.Timestamp, end: pd.Timestamp
) -> pd.Series:
    """Acumulado por município no trecho [start, end], exigindo cobertura diária completa."""
    sub = municipal[
        (municipal["kind"] == kind)
        & (municipal["ref_date"] >= start)
        & (municipal["ref_date"] <= end)
        & (municipal["municipality_code"].isin(codes))
    ]
    expected = pd.date_range(start, end, freq="D")
    missing_days = expected.difference(pd.DatetimeIndex(sub["ref_date"].unique()))
    if len(missing_days):
        raise ValueError(
            f"painel {kind} sem cobertura diária no trecho {start.date()}–{end.date()}: "
            f"faltam {len(missing_days)} dia(s), ex. {list(missing_days[:3])}"
        )
    grouped = sub.groupby("municipality_code")["precip_mm"].agg(["sum", "count", "size"])
    short = grouped[grouped["size"] != len(expected)]
    if not short.empty:
        raise ValueError(f"município sem todos os dias do trecho: {sorted(short.index)[:5]}")
    missing_codes = sorted(set(codes) - set(grouped.index))
    if missing_codes:
        raise ValueError(f"município com peso PAM fora do painel municipal: {missing_codes[:5]}")
    with_nan = grouped[grouped["count"] != grouped["size"]]
    if not with_nan.empty:
        raise ValueError(
            f"precipitação municipal NaN dentro do trecho: {sorted(with_nan.index)[:5]}"
        )
    return grouped["sum"]


def _uf_weights(pam_weights: pd.DataFrame, spec: CropRegionWindow) -> pd.Series:
    sel = pam_weights[
        (pam_weights["crop"] == PAM_CROP_FOR[spec.crop]) & (pam_weights["uf"] == spec.uf)
    ]
    weights = sel.set_index("municipality_code")["within_uf_weight"].dropna()
    if weights.empty:
        raise ValueError(f"sem peso PAM para {PAM_CROP_FOR[spec.crop]}/{spec.uf}")
    return weights / weights.sum()


def _weighted_stretch(
    municipal: pd.DataFrame, kind: str, weights: pd.Series, start: pd.Timestamp, end: pd.Timestamp
) -> float:
    sums = _stretch_sum(municipal, kind, weights.index, start, end)
    return float((sums.loc[weights.index] * weights).sum())


def uf_shock_asof(
    t,
    ano_agricola: str,
    spec: CropRegionWindow,
    municipal_visible: pd.DataFrame,
    pam_weights: pd.DataFrame,
    climatology_first_year: int,
) -> dict:
    """``Shock`` de uma (cultura, UF) em ``t`` — ver o contrato no docstring do módulo.

    ``municipal_visible`` já deve estar filtrado por ``avail_date ≤ t``; ``pam_weights`` é a
    saída de ``pam_weights_asof(panel, t)``.
    """
    start, end = critical_period(spec, ano_agricola)
    prelim = municipal_visible[municipal_visible["kind"] == PRIMARY_SIGNAL_KIND]
    row = {
        "asof_date": pd.Timestamp(t),
        "ano_agricola": ano_agricola,
        "crop": spec.crop,
        "level": "uf",
        "uf": spec.uf,
        "window_start": start,
        "window_end": end,
    }
    last_ref = prelim["ref_date"].max() if not prelim.empty else pd.NaT
    cut = min(end, last_ref) if pd.notna(last_ref) else pd.NaT
    if pd.isna(cut) or cut < start:
        return row | {
            "cut_date": pd.NaT,
            "elapsed_days": pd.NA,
            "precip_mm": np.nan,
            "clim_mean_mm": np.nan,
            "clim_std_mm": np.nan,
            "n_clim_years": 0,
            "z": np.nan,
            "shock": np.nan,
            "status": "window_not_started",
        }
    elapsed = int((cut - start).days)
    weights = _uf_weights(pam_weights, spec)
    current = _weighted_stretch(prelim, PRIMARY_SIGNAL_KIND, weights, start, cut)

    current_start_year = crop_year_start(ano_agricola)
    years = range(climatology_first_year, current_start_year)
    if len(years) < MIN_EXPANDING_YEARS:
        raise ValueError(
            f"climatologia com {len(years)} safra(s) < mínimo {MIN_EXPANDING_YEARS} "
            f"({climatology_first_year}..{current_start_year - 1})"
        )
    final = municipal_visible[municipal_visible["kind"] == CLIMATOLOGY_KIND]
    history = []
    for year in years:
        y_start, _ = critical_period(spec, _ano_agricola(year))
        y_end = y_start + pd.Timedelta(days=elapsed)
        history.append(_weighted_stretch(final, CLIMATOLOGY_KIND, weights, y_start, y_end))
    hist = np.asarray(history, dtype=float)
    mean = float(hist.mean())
    std = float(hist.std(ddof=EXPANDING_STD_DDOF))
    if not np.isfinite(std) or std <= 0:
        raise ValueError(f"climatologia degenerada para {spec.key}: std={std}")
    z = (current - mean) / std
    return row | {
        "cut_date": cut,
        "elapsed_days": elapsed,
        "precip_mm": current,
        "clim_mean_mm": mean,
        "clim_std_mm": std,
        "n_clim_years": len(years),
        "z": z,
        "shock": PRECIP_Z_TO_STRESS * z,
        "status": "ok",
    }


def shock_asof(
    t,
    ano_agricola: str,
    municipal: pd.DataFrame,
    pam_panel: pd.DataFrame,
    conab: pd.DataFrame,
    climatology_first_year: int,
    windows: tuple[CropRegionWindow, ...] = PRIMARY_WINDOWS,
) -> pd.DataFrame:
    """Painel de ``Shock`` (UF + nacional por cultura) observável na data de decisão ``t``.

    Entradas: painel municipal CHIRPS **carimbado** (``stamp_municipal_panel``), painel PAM
    (``ingest.pam.parse_pam``) e painel CONAB de grãos **carimbado**
    (``ingest.conab_calendar.attach_avail_date``). Cada uma é filtrada por ``avail_date ≤ t``
    aqui dentro — nenhum dado do futuro entra por construção, não por disciplina do chamador.
    """
    if AVAIL_COL not in municipal.columns:
        raise ValueError("painel municipal sem avail_date — use stamp_municipal_panel")
    ts = pd.Timestamp(t)
    municipal_visible = available_asof(municipal, ts)
    pam_weights = pam_weights_asof(pam_panel, ts)
    rows = [
        uf_shock_asof(
            ts, ano_agricola, spec, municipal_visible, pam_weights, climatology_first_year
        )
        for spec in windows
    ]
    crops = sorted({spec.crop for spec in windows})
    national_rows = []
    for crop in crops:
        specs = [spec for spec in windows if spec.crop == crop]
        ufs = [spec.uf for spec in specs]
        weights = conab_uf_weights(conab, specs[0], ufs, ano_agricola, ts)
        for r in rows:
            if r["crop"] == crop:
                r["national_weight"] = float(weights[r["uf"]])
        ok = [r for r in rows if r["crop"] == crop and r["status"] == "ok"]
        base = {
            "asof_date": ts,
            "ano_agricola": ano_agricola,
            "crop": crop,
            "level": "national",
            "uf": pd.NA,
            "window_start": min(r["window_start"] for r in rows if r["crop"] == crop),
            "window_end": max(r["window_end"] for r in rows if r["crop"] == crop),
            "clim_mean_mm": np.nan,
            "clim_std_mm": np.nan,
            "precip_mm": np.nan,
            "z": np.nan,
        }
        if not ok:
            national_rows.append(
                base
                | {
                    "cut_date": pd.NaT,
                    "elapsed_days": pd.NA,
                    "n_clim_years": 0,
                    "shock": np.nan,
                    "status": "window_not_started",
                    "uf_coverage_weight": 0.0,
                }
            )
            continue
        w = weights.loc[[r["uf"] for r in ok]]
        coverage = float(w.sum())
        shock = float(sum(wi * ri["shock"] for wi, ri in zip(w, ok, strict=True)) / coverage)
        national_rows.append(
            base
            | {
                "cut_date": max(r["cut_date"] for r in ok),
                "elapsed_days": max(r["elapsed_days"] for r in ok),
                "n_clim_years": min(r["n_clim_years"] for r in ok),
                "shock": shock,
                "status": "ok",
                "uf_coverage_weight": coverage,
            }
        )
    out = pd.DataFrame(rows + national_rows)
    cols = [
        "asof_date",
        "ano_agricola",
        "crop",
        "level",
        "uf",
        "window_start",
        "window_end",
        "cut_date",
        "elapsed_days",
        "precip_mm",
        "clim_mean_mm",
        "clim_std_mm",
        "n_clim_years",
        "z",
        "shock",
        "national_weight",
        "uf_coverage_weight",
        "status",
    ]
    return out.reindex(columns=cols).sort_values(["crop", "level", "uf"]).reset_index(drop=True)
