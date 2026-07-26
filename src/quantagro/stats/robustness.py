"""Execução da suíte de robustez de H1 (D-065) sobre o grid congelado de ``robustness_spec``.

**O motor de Shock congelado nunca é tocado.** Cada perturbação constrói *inputs modificados* para
o ``build_h1a_panel`` inalterado: climatologia por parâmetro, janela por specs deslocadas, lag por
shift de ``avail_date`` + ``signal_lag_days``, fonte ``final`` por relabel do painel, e placebos por
transformação do painel já montado. O baseline (todos os defaults) é bit-idêntico ao portão D-030.
Return-agnóstico: mede o mecanismo H1a, não retornos.
"""

from __future__ import annotations

import calendar
from dataclasses import replace

import numpy as np
import pandas as pd

from ..features.shock import FINAL_LAG_DAYS, PRELIM_LAG_DAYS
from ..features.shock_spec import (
    CLIMATOLOGY_KIND,
    PRIMARY_SIGNAL_KIND,
    PRIMARY_WINDOWS,
    CropRegionWindow,
    crop_year_start,
)
from .h1a import build_h1a_panel, run_h1a
from .robustness_spec import Perturbation

_REF_BASE = 2021  # ano de referência arbitrário para deslocar janelas (offsets são relativos)


def shift_window(spec: CropRegionWindow, days: int) -> CropRegionWindow:
    """Desloca a janela de ``days`` dias, re-derivando mês/dia/offset (``end_day`` fixado)."""
    if days == 0:
        return spec
    start = pd.Timestamp(_REF_BASE + spec.start_year_offset, spec.start_month, spec.start_day)
    start += pd.Timedelta(days=days)
    end_day = (
        spec.end_day or calendar.monthrange(_REF_BASE + spec.end_year_offset, spec.end_month)[1]
    )
    end = pd.Timestamp(_REF_BASE + spec.end_year_offset, spec.end_month, end_day)
    end += pd.Timedelta(days=days)
    return replace(
        spec,
        start_month=start.month,
        start_day=start.day,
        start_year_offset=start.year - _REF_BASE,
        end_month=end.month,
        end_day=end.day,
        end_year_offset=end.year - _REF_BASE,
    )


def shifted_windows(
    windows: tuple[CropRegionWindow, ...], days: int
) -> tuple[CropRegionWindow, ...]:
    return tuple(shift_window(spec, days) for spec in windows)


def with_extra_signal_lag(stamped: pd.DataFrame, extra_days: int) -> pd.DataFrame:
    """Atrasa o sinal: soma ``extra_days`` ao ``avail_date`` das linhas de sinal."""
    if extra_days == 0:
        return stamped
    out = stamped.copy()
    mask = out["kind"] == PRIMARY_SIGNAL_KIND
    out.loc[mask, "avail_date"] = out.loc[mask, "avail_date"] + pd.Timedelta(days=extra_days)
    return out


def use_final_as_signal(stamped: pd.DataFrame) -> pd.DataFrame:
    """Usa a série ``final`` como sinal: relabela ``final``→sinal (mantendo o carimbo de +60d) e
    preserva as linhas ``final`` para a climatologia. As linhas ``prelim`` originais saem."""
    final = stamped[stamped["kind"] == CLIMATOLOGY_KIND].copy()
    if final.empty:
        raise ValueError("painel sem série final para usar como sinal")
    signal = final.copy()
    signal["kind"] = PRIMARY_SIGNAL_KIND
    return pd.concat([final, signal], ignore_index=True)


def _prev_crop_year(ano_agricola: str) -> str:
    start = crop_year_start(ano_agricola) - 1
    return f"{start}/{(start + 1) % 100:02d}"


def _next_crop_year(ano_agricola: str) -> str:
    start = crop_year_start(ano_agricola) + 1
    return f"{start}/{(start + 1) % 100:02d}"


def placebo_spatial(panel: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Placebo espacial: embaralha o ``shock`` entre UFs no mesmo ``(crop, ano, levantamento)``.

    Preserva a distribuição marginal e o calendário; rompe só o pareamento UF↔revisão. Grupos com
    uma única UF ficam inalterados (nada a embaralhar).
    """
    rng = np.random.default_rng(seed)
    out = panel.copy()
    for _, idx in out.groupby(
        ["crop", "ano_agricola", "id_levantamento"], sort=False
    ).groups.items():
        rows = list(idx)
        if len(rows) < 2:
            continue
        vals = out.loc[rows, "shock"].to_numpy()
        out.loc[rows, "shock"] = vals[rng.permutation(len(vals))]
    return out


def placebo_temporal(panel: pd.DataFrame) -> pd.DataFrame:
    """Placebo temporal: cada obs recebe o ``shock`` do ano-safra ANTERIOR (mesma UF/levantamento).

    Rompe o pareamento temporal (revisão de hoje × clima do ano passado). Reduz N (só anos com
    predecessor na amostra) — aceitável para um placebo, cujo β esperado é ~0.
    """
    # Relabela cada fonte (ano X, shock s) para o ano seguinte X+1, para que panel[ano=Y] case com
    # a fonte de Y−1 e receba o shock do ano anterior.
    source = panel[["crop", "uf", "ano_agricola", "id_levantamento", "shock"]].copy()
    source["ano_agricola"] = source["ano_agricola"].map(_next_crop_year)
    source = source.rename(columns={"shock": "_placebo_shock"})
    merged = panel.drop(columns=["shock"]).merge(
        source, on=["crop", "uf", "ano_agricola", "id_levantamento"], how="inner"
    )
    merged = merged.rename(columns={"_placebo_shock": "shock"})
    return merged.reset_index(drop=True)


def build_perturbed_panel(
    pert: Perturbation,
    conab: pd.DataFrame,
    municipal_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    climatology_first_year: int,
    baseline_panel: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Constrói o painel de H1a sob a perturbação. Placebos reusam ``baseline_panel`` (barato)."""
    if pert.placebo == "spatial":
        if baseline_panel is None:
            raise ValueError("placebo espacial exige baseline_panel")
        return placebo_spatial(baseline_panel)
    if pert.placebo == "temporal":
        if baseline_panel is None:
            raise ValueError("placebo temporal exige baseline_panel")
        return placebo_temporal(baseline_panel)

    windows = PRIMARY_WINDOWS
    municipal = municipal_stamped
    cfy = climatology_first_year + pert.climatology_first_year_delta
    signal_lag = PRELIM_LAG_DAYS
    if pert.window_shift_days != 0:
        windows = shifted_windows(PRIMARY_WINDOWS, pert.window_shift_days)
    if pert.extra_lag_days != 0:
        municipal = with_extra_signal_lag(municipal_stamped, pert.extra_lag_days)
        signal_lag = PRELIM_LAG_DAYS + pert.extra_lag_days
    if pert.signal_kind == "final":
        municipal = use_final_as_signal(municipal_stamped)
        signal_lag = FINAL_LAG_DAYS
    return build_h1a_panel(
        conab, municipal, pam_panel, cfy, windows=windows, signal_lag_days=signal_lag
    )


def pooled_full_row(results: pd.DataFrame) -> pd.Series:
    """Extrai a linha agrupada do span cheio (``h1a:pooled``, scope ``full``) de ``run_h1a``."""
    hit = results[(results["scope"] == "full") & (results["test"] == "h1a:pooled")]
    if len(hit) != 1:
        raise ValueError(f"esperava 1 linha pooled/full, achei {len(hit)}")
    return hit.iloc[0]


def run_perturbation(
    pert: Perturbation,
    conab: pd.DataFrame,
    municipal_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    climatology_first_year: int,
    baseline_panel: pd.DataFrame | None = None,
) -> dict:
    """Roda uma perturbação ponta a ponta e devolve β/boot-p agrupados + N/safras (span cheio)."""
    panel = build_perturbed_panel(
        pert, conab, municipal_stamped, pam_panel, climatology_first_year, baseline_panel
    )
    res = run_h1a(panel)
    row = pooled_full_row(res)
    return {
        "name": pert.name,
        "family": pert.family,
        "beta": float(row["beta"]),
        "boot_pvalue": float(row["boot_pvalue"]),
        "n": int(row["n"]),
        "n_clusters": int(row["n_clusters"]),
        "panel": panel,
    }
