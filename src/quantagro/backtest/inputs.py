"""Adaptadores point-in-time das features para a agenda do backtest.

Este módulo não lê retornos. Ele converte os contratos de clima, geografia, CONAB e exposição
em dois painéis exatamente no schema aceito por ``build_target_schedule``. Toda decisão é
calculada as-of ``TradeBlock.decision_date``; ausência técnica falha em vez de virar zero.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from quantagro.features.cane_shock import uf_cane_shock_asof
from quantagro.features.exposure import exposure_asof
from quantagro.features.shock import conab_uf_weights, shock_asof
from quantagro.features.shock_spec import CANE_MATURATION_WINDOWS

from .operational_spec import (
    CANE_UFS,
    GRAIN_CROPS,
    TradeBlock,
    aggregate_cane_shock,
    grain_mechanism_score,
    require_backtest_scope,
)
from .strategy_spec import GRAIN_NAMES


def materialize_grain_raw_scores(
    blocks: Sequence[TradeBlock],
    registry: pd.DataFrame,
    municipal_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    conab_stamped: pd.DataFrame,
    climatology_first_year: int,
    *,
    allow_holdout: bool = False,
) -> pd.DataFrame:
    """Materializa ``E·Shock`` por decisão e nome, antes da direção operacional H′."""
    frozen = tuple(blocks)
    require_backtest_scope(frozen, allow_holdout=allow_holdout)
    rows = []
    for block in frozen:
        panel = shock_asof(
            block.decision_date,
            block.crop_year,
            municipal_stamped,
            pam_panel,
            conab_stamped,
            climatology_first_year,
        )
        national = panel[panel["level"] == "national"].set_index("crop")
        if set(national.index) != set(GRAIN_CROPS):
            raise ValueError(f"Shock nacional incompleto em {block.decision_date.date()}")
        shocks: dict[str, float | None] = {}
        for crop in GRAIN_CROPS:
            status = str(national.loc[crop, "status"])
            value = national.loc[crop, "shock"]
            if status == "window_not_started":
                if pd.notna(value):
                    raise ValueError("janela não iniciada deve ter Shock ausente")
                shocks[crop] = None
            elif status == "ok" and pd.notna(value) and np.isfinite(float(value)):
                shocks[crop] = float(value)
            else:
                raise ValueError(
                    f"Shock técnico inválido para {crop} em {block.decision_date.date()}"
                )

        exposures = exposure_asof(registry, block.decision_date)
        values: dict[str, float] = {}
        for ticker in GRAIN_NAMES:
            selected = exposures[exposures["ticker"] == ticker]
            if selected.empty:
                values[ticker] = np.nan
                continue
            exposure = dict(zip(selected["crop"], selected["exposure"], strict=True))
            values[ticker] = grain_mechanism_score(exposure, shocks)
        rows.append({"decision_date": block.decision_date} | values)
    out = pd.DataFrame(rows).set_index("decision_date")
    out.index = pd.DatetimeIndex(out.index)
    return out.reindex(columns=GRAIN_NAMES)


def materialize_cane_signal(
    blocks: Sequence[TradeBlock],
    monthly_stamped: pd.DataFrame,
    pam_panel: pd.DataFrame,
    conab_stamped: pd.DataFrame,
    climatology_first_year: int,
    *,
    allow_holdout: bool = False,
) -> pd.DataFrame:
    """Materializa o Shock nacional de maturação da cana nas cinco UFs de D-055."""
    frozen = tuple(blocks)
    require_backtest_scope(frozen, allow_holdout=allow_holdout)
    by_uf = {spec.uf: spec for spec in CANE_MATURATION_WINDOWS}
    if set(by_uf) != set(CANE_UFS):
        raise RuntimeError("janelas de maturação não coincidem com as cinco UFs congeladas")

    rows = []
    for block in frozen:
        results = {
            uf: uf_cane_shock_asof(
                block.decision_date,
                block.crop_year,
                by_uf[uf],
                monthly_stamped,
                pam_panel,
                climatology_first_year,
            )
            for uf in CANE_UFS
        }
        statuses = {str(result["status"]) for result in results.values()}
        if statuses == {"window_not_started"}:
            rows.append(
                {
                    "decision_date": block.decision_date,
                    "shock": np.nan,
                    "status": "window_not_started",
                }
            )
            continue
        if statuses != {"ok"}:
            raise ValueError(
                f"cobertura parcial/técnica da cana em {block.decision_date.date()}: "
                f"{sorted(statuses)}"
            )
        shocks = {uf: float(results[uf]["shock"]) for uf in CANE_UFS}
        weights = conab_uf_weights(
            conab_stamped,
            by_uf[CANE_UFS[0]],
            CANE_UFS,
            block.crop_year,
            block.decision_date,
        )
        value = aggregate_cane_shock(shocks, weights.to_dict())
        rows.append({"decision_date": block.decision_date, "shock": value, "status": "ok"})
    out = pd.DataFrame(rows).set_index("decision_date")
    out.index = pd.DatetimeIndex(out.index)
    return out.loc[:, ["shock", "status"]]
