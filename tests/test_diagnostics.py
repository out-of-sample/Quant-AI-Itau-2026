"""Testes dos diagnósticos descritivos da Fase 4.3 (D-060)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantagro.backtest.diagnostics import (
    attribution_by_name,
    build_naive_sector_schedule,
    concentration_metrics,
    cost_monotonicity,
    sector_climate_decomposition,
)
from quantagro.backtest.operational_spec import PRODUCERS, TradeBlock
from quantagro.backtest.strategy_spec import PER_NAME_CAP, UNIVERSE


def _frame(rows: dict[pd.Timestamp, dict[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows).T.reindex(columns=list(UNIVERSE)).astype(float)


def test_attribution_by_name_shares_and_side() -> None:
    dates = pd.to_datetime(["2019-01-08", "2019-01-09"])
    # SLCE3 short (perde valor ⇒ P&L short positivo), BRFS3/JBSS3 long e lucrativos.
    attribution = pd.DataFrame(
        {"AGRO3": 0.0, "SLCE3": 1_000.0, "BRFS3": 3_000.0, "JBSS3": 6_000.0, "SMTO3": 0.0},
        index=dates,
    ).reindex(columns=list(UNIVERSE))
    weights = pd.DataFrame(
        {"AGRO3": 0.0, "SLCE3": -0.4, "BRFS3": 0.2, "JBSS3": 0.2, "SMTO3": 0.0},
        index=dates,
    ).reindex(columns=list(UNIVERSE))

    attr = attribution_by_name(attribution, weights)
    # P&L é somado sobre os dias: JBSS3 domina.
    assert attr.loc["JBSS3", "gross_pnl_brl"] == pytest.approx(12_000.0)
    assert attr.loc["SLCE3", "side"] == "short"
    assert attr.loc["BRFS3", "side"] == "long"
    assert attr.loc["AGRO3", "side"] == "flat"
    total = attr["gross_pnl_brl"].sum()
    assert attr["pnl_share"].sum() == pytest.approx(1.0)
    assert attr.loc["JBSS3", "pnl_share"] == pytest.approx(12_000.0 / total)

    conc = concentration_metrics(attr)
    assert conc["top1_name"] == "JBSS3"
    assert 0.0 < conc["hhi"] <= 1.0


def test_attribution_zero_total_gives_nan_share() -> None:
    dates = pd.to_datetime(["2019-01-08"])
    attribution = _frame({dates[0]: dict.fromkeys(UNIVERSE, 0.0)})
    weights = _frame({dates[0]: dict.fromkeys(UNIVERSE, 0.0)})
    attr = attribution_by_name(attribution, weights)
    assert attr["pnl_share"].isna().all()


def test_attribution_rejects_wrong_columns() -> None:
    dates = pd.to_datetime(["2019-01-08"])
    bad = pd.DataFrame({"AGRO3": [0.0], "SLCE3": [0.0]}, index=dates)
    with pytest.raises(ValueError, match="colunas"):
        attribution_by_name(bad, bad)


def _dev_block() -> TradeBlock:
    return TradeBlock(
        crop_year="2018/19",
        sequence=0,
        decision_date=pd.Timestamp("2019-01-07"),
        execution_date=pd.Timestamp("2019-01-08"),
        exit_date=pd.Timestamp("2019-02-06"),
    )


def test_naive_sector_schedule_is_short_producer_long_processor() -> None:
    block = _dev_block()
    membership = pd.DataFrame(True, index=[block.decision_date], columns=list(UNIVERSE))
    schedule = build_naive_sector_schedule([block], membership)
    weights = schedule.target_weights.iloc[0]

    # Dollar-neutral, bruto 1,0, produtores short e processadores long.
    assert weights.sum() == pytest.approx(0.0, abs=1e-12)
    assert weights.abs().sum() == pytest.approx(1.0)
    for name in UNIVERSE:
        if name == "SMTO3":
            assert weights[name] == pytest.approx(0.0)  # cana inativa no benchmark
        elif name in PRODUCERS:
            assert weights[name] < 0
        else:
            assert weights[name] > 0
    # Pesos iguais por perna (sem informação cross-section) e dentro do cap.
    assert weights["AGRO3"] == pytest.approx(weights["SLCE3"])
    assert weights["BRFS3"] == pytest.approx(weights["JBSS3"])
    assert (weights.abs() <= pd.Series(PER_NAME_CAP) + 1e-12).all()


def test_sector_climate_decomposition_flags_spread_bet() -> None:
    dates = pd.date_range("2019-01-08", periods=6, freq="B")
    initial = 500_000.0
    # Livro cujo retorno diário é exatamente o spread processador−produtor ⇒ r2≈1, incremento 0.
    rng = np.random.default_rng(0)
    proc = rng.normal(0.01, 0.02, len(dates))
    prod = rng.normal(-0.005, 0.02, len(dates))
    returns = pd.DataFrame(
        {
            "AGRO3": prod,
            "SLCE3": prod,
            "BRFS3": proc,
            "JBSS3": proc,
            "SMTO3": np.zeros(len(dates)),
        },
        index=dates,
    )
    spread = proc - prod
    equity = initial * np.cumprod(1.0 + spread)
    book_daily = pd.DataFrame({"net_return": spread, "equity_brl": equity}, index=dates)
    # Benchmark ingênuo idêntico ao livro ⇒ incremento de clima nulo.
    naive_daily = book_daily.copy()

    out = sector_climate_decomposition(book_daily, naive_daily, returns, initial_aum_brl=initial)
    assert out["climate_increment"] == pytest.approx(0.0, abs=1e-12)
    assert out["spread_beta"] == pytest.approx(1.0, abs=1e-6)
    assert out["spread_r2"] == pytest.approx(1.0, abs=1e-6)


def test_cost_monotonicity() -> None:
    ok = cost_monotonicity({"zero": 540_000.0, "base": 536_000.0, "double": 532_000.0})
    assert ok["monotonic"]
    bad = cost_monotonicity({"zero": 500_000.0, "base": 536_000.0, "double": 532_000.0})
    assert not bad["monotonic"]
    with pytest.raises(ValueError, match="cenários"):
        cost_monotonicity({"zero": 1.0, "base": 1.0})
