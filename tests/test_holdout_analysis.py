"""Cálculos puros da rodada única, com dados sintéticos."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantagro.backtest.engine import TargetSchedule
from quantagro.backtest.holdout_analysis import (
    HoldoutInputs,
    primary_hprime,
    run_all_analyses,
)
from quantagro.backtest.operational_spec import TradeBlock, build_trade_blocks
from quantagro.backtest.strategy_spec import (
    GRAIN_NAMES,
    HOLDOUT_CROP_YEARS,
    UNIVERSE,
)


def test_primario_demean_e_signflip_exato_passam_com_relacao_positiva() -> None:
    blocks = []
    all_sessions = []
    score_rows = []
    target_rows = []
    decision_rows = []
    x = np.array([-1.0, -0.5, 0.5, 1.0])
    for year, crop_year in enumerate(HOLDOUT_CROP_YEARS, start=2021):
        sessions = pd.bdate_range(f"{year}-01-07", periods=23)
        block = TradeBlock(crop_year, 0, sessions[0], sessions[1], sessions[22])
        blocks.append(block)
        all_sessions.extend(sessions)
        score_rows.append(dict(zip(UNIVERSE[:4], x, strict=True)) | {"SMTO3": np.nan})
        target_rows.append(dict.fromkeys(UNIVERSE, 0.0))
        decision_rows.append(
            {
                "crop_year": crop_year,
                "sequence": 0,
                "decision_date": block.decision_date,
                "exit_date": block.exit_date,
                "status": "planned",
            }
        )

    executions = pd.DatetimeIndex([block.execution_date for block in blocks])
    scores = pd.DataFrame(score_rows, index=executions, columns=UNIVERSE)
    targets = pd.DataFrame(target_rows, index=executions, columns=UNIVERSE)
    decisions = pd.DataFrame(decision_rows, index=executions)
    schedule = TargetSchedule(tuple(blocks), scores, targets, decisions)

    returns = pd.DataFrame(
        0.0,
        index=pd.DatetimeIndex(sorted(set(all_sessions))),
        columns=UNIVERSE,
    )
    for block in blocks:
        first_held = returns.index[returns.index.get_loc(block.execution_date) + 1]
        returns.loc[first_held, UNIVERSE[:4]] = 0.01 * x

    terminal = blocks[-1].execution_date + pd.offsets.BDay(10)
    returns.loc[
        (returns.index > terminal) & (returns.index <= blocks[-1].exit_date),
        "JBSS3",
    ] = np.nan
    result = primary_hprime(returns, schedule, {"JBSS3": terminal})
    assert result["statistic"] == pytest.approx(0.01)
    assert result["pvalue"] == pytest.approx(1 / 32)
    assert result["passed"]
    assert result["permutations"] == 32
    assert set(result["cluster_slopes"]) == set(HOLDOUT_CROP_YEARS)


def _synthetic_inputs() -> HoldoutInputs:
    sessions = pd.bdate_range("2020-01-02", "2025-12-30", name="date")
    rng = np.random.default_rng(20260726)
    returns = pd.DataFrame(
        rng.normal(0.0002, 0.01, (len(sessions), len(UNIVERSE))),
        index=sessions,
        columns=UNIVERSE,
    )
    market_rows = [
        {
            "date": date,
            "ticker": ticker,
            "traded": True,
            "seasoned": True,
            "adtv_brl": 100_000_000.0,
            "eligible": True,
            "reason": "ok",
        }
        for date in sessions
        for ticker in UNIVERSE
    ]
    state = pd.DataFrame(market_rows)

    blocks_by_horizon = {
        horizon: tuple(
            block
            for year in HOLDOUT_CROP_YEARS
            for block in build_trade_blocks(sessions, year, holding_sessions=horizon)
        )
        for horizon in (10, 21, 42)
    }
    all_dates = sorted(
        {block.decision_date for blocks in blocks_by_horizon.values() for block in blocks}
    )
    primary_dates = [block.decision_date for block in blocks_by_horizon[21]]
    raw = dict(zip(GRAIN_NAMES, [1.0, 0.5, -0.5, -1.0], strict=True))
    grain_rows = []
    cane_rows = []
    for lag, dates in ((7, all_dates), (14, primary_dates), (21, primary_dates)):
        for date in dates:
            grain_rows.append({"decision_date": date, "total_signal_lag_days": lag} | raw)
            cane_rows.append(
                {
                    "decision_date": date,
                    "total_signal_lag_days": lag,
                    "shock": np.nan,
                    "status": "window_not_started",
                }
            )
    grain = pd.DataFrame(grain_rows)
    cane = pd.DataFrame(cane_rows)

    h4_values = rng.normal(0.0, 0.01, (len(sessions), 10))
    h4 = pd.DataFrame(
        h4_values,
        index=sessions,
        columns=[
            "rm_minus_rf",
            "smb",
            "hml",
            "wml",
            "iml",
            "usdbrl",
            "soy",
            "corn_second",
            "sugar",
            "oni",
        ],
    )
    h4["risk_free"] = 0.0001
    h4["avail_date"] = sessions
    h5 = pd.DataFrame(raw, index=pd.DatetimeIndex(primary_dates))
    return HoldoutInputs(returns, state, grain, cane, h4, h5, {})


def test_pacote_0_a_10_roda_integralmente_em_dados_sinteticos() -> None:
    artifacts = run_all_analyses(_synthetic_inputs(), {"safe": True})
    assert len(artifacts) == 11
    assert artifacts[0] == {"safe": True}
    assert artifacts[1]["permutations"] == 32
    assert set(artifacts[2]["scenarios"]) == {"zero", "base", "double"}
    assert artifacts[2]["cost_monotonicity"]["monotonic"]
    assert artifacts[5]["extended"]["observations"] > 1_000
    assert len(artifacts[6]["exposure_within_side"]) == 4
    assert set(artifacts[7]) == set(UNIVERSE)
    assert set(artifacts[8]) == set(HOLDOUT_CROP_YEARS)
