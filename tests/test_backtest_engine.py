"""Canários da contabilidade diária do motor D-056."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantagro.backtest.engine import (
    TargetSchedule,
    build_target_schedule,
    run_backtest,
    run_backtest_from_parquet,
)
from quantagro.backtest.operational_spec import HoldoutLockedError, TradeBlock
from quantagro.backtest.strategy_spec import UNIVERSE
from quantagro.validate.borrow import BorrowState


def _calendar(start="2019-01-02", periods=50):
    return pd.bdate_range(start, periods=periods)


def _blocks(sessions=None, count=1):
    s = _calendar() if sessions is None else sessions
    first = TradeBlock("2018/19", 0, s[0], s[1], s[22])
    if count == 1:
        return (first,)
    second = TradeBlock("2018/19", 1, s[21], s[22], s[43])
    return (first, second)


def _target_row(*, reverse=False):
    row = {name: 0.0 for name in UNIVERSE}
    sign = -1.0 if reverse else 1.0
    row.update(
        {
            "AGRO3": 0.25 * sign,
            "SLCE3": 0.25 * sign,
            "BRFS3": -0.25 * sign,
            "JBSS3": -0.25 * sign,
        }
    )
    return row


def _schedule(blocks, *, reverse_second=False):
    index = pd.DatetimeIndex([b.execution_date for b in blocks], name="execution_date")
    rows = [_target_row()]
    if len(blocks) == 2:
        rows.append(_target_row(reverse=reverse_second))
    targets = pd.DataFrame(rows, index=index, columns=UNIVERSE, dtype=float)
    scores = pd.DataFrame(np.nan, index=index, columns=UNIVERSE)
    decisions = pd.DataFrame(
        {
            "crop_year": [b.crop_year for b in blocks],
            "sequence": [b.sequence for b in blocks],
            "decision_date": [b.decision_date for b in blocks],
            "exit_date": [b.exit_date for b in blocks],
            "status": "planned",
        },
        index=index,
    )
    return TargetSchedule(tuple(blocks), scores, targets, decisions)


def _inputs(sessions=None):
    s = _calendar() if sessions is None else sessions
    returns = pd.DataFrame(0.0, index=s, columns=UNIVERSE)
    adtv = pd.DataFrame(100_000_000.0, index=s, columns=UNIVERSE)
    traded = pd.DataFrame(True, index=s, columns=UNIVERSE, dtype=bool)
    rates = pd.DataFrame(0.10, index=s, columns=UNIVERSE)
    recent = pd.DataFrame(True, index=s, columns=UNIVERSE, dtype=bool)
    stock = pd.DataFrame(100_000_000.0, index=s, columns=UNIVERSE)
    complete = pd.DataFrame(True, index=s, columns=UNIVERSE, dtype=bool)
    reason = pd.DataFrame("ok", index=s, columns=UNIVERSE)
    return returns, adtv, traded, BorrowState(rates, recent, stock, complete, reason)


def test_materializa_h_prime_e_zerada_sem_dois_lados_economicos():
    blocks = _blocks()
    decision = blocks[0].decision_date
    grain = pd.DataFrame([[1.0, np.nan, -1.0, np.nan]], index=[decision], columns=UNIVERSE[:4])
    cane = pd.DataFrame({"shock": [np.nan], "status": ["window_not_started"]}, index=[decision])
    membership = pd.DataFrame(False, index=[decision], columns=UNIVERSE, dtype=bool)
    membership.loc[decision, ["AGRO3", "BRFS3"]] = True

    schedule = build_target_schedule(blocks, grain, cane, membership)
    assert schedule.operational_scores.loc[blocks[0].execution_date, "AGRO3"] == -1.0
    assert schedule.operational_scores.loc[blocks[0].execution_date, "BRFS3"] == 1.0
    assert schedule.target_weights.loc[blocks[0].execution_date, "AGRO3"] < 0
    assert schedule.target_weights.loc[blocks[0].execution_date, "BRFS3"] > 0

    membership.loc[decision, "BRFS3"] = False
    flat = build_target_schedule(blocks, grain, cane, membership)
    assert (flat.target_weights == 0).all().all()
    assert flat.decisions.iloc[0]["status"] == "flat_missing_economic_side"


def test_cana_so_aceita_ausencia_antes_da_janela():
    blocks = _blocks()
    decision = blocks[0].decision_date
    grain = pd.DataFrame(0.0, index=[decision], columns=UNIVERSE[:4])
    membership = pd.DataFrame(True, index=[decision], columns=UNIVERSE, dtype=bool)
    bad = pd.DataFrame({"shock": [np.nan], "status": ["ok"]}, index=[decision])
    with pytest.raises(ValueError, match="ausente/não finito"):
        build_target_schedule(blocks, grain, bad, membership)

    bad = pd.DataFrame({"shock": [0.0], "status": ["window_not_started"]}, index=[decision])
    with pytest.raises(ValueError, match="deve ter shock ausente"):
        build_target_schedule(blocks, grain, bad, membership)


def test_close_de_execucao_nao_recebe_retorno_e_bloco_tem_21_intervalos():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    returns.loc[blocks[0].execution_date, "AGRO3"] = 0.50
    returns.loc[sessions[2], "AGRO3"] = 0.10

    result = run_backtest(returns, _schedule(blocks), adtv, traded, borrow)
    assert result.daily.loc[blocks[0].execution_date, "gross_pnl_brl"] == 0.0
    assert result.daily.loc[sessions[2], "gross_pnl_brl"] == pytest.approx(12_500.0)
    held_returns = result.daily.loc[blocks[0].execution_date : blocks[0].exit_date].iloc[1:]
    assert len(held_returns) == 21


def test_quantidades_fixas_permitem_drift_sem_ordem_diaria():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    returns.loc[sessions[2], "AGRO3"] = 0.10

    result = run_backtest(returns, _schedule(blocks), adtv, traded, borrow)
    assert result.weights.loc[sessions[2], "AGRO3"] > 0.25
    assert list(result.orders_brl.index) == [blocks[0].execution_date, blocks[0].exit_date]
    assert result.daily.loc[sessions[2], "gross_traded"] == 0.0


def test_retorno_bruto_do_bloco_fecha_com_formula_direta():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    returns.loc[sessions[2], "AGRO3"] = 0.10
    returns.loc[sessions[3], "AGRO3"] = -0.05
    returns.loc[sessions[4], "BRFS3"] = 0.04

    result = run_backtest(returns, _schedule(blocks), adtv, traded, borrow)
    growth = (1.0 + returns.loc[sessions[2] : blocks[0].exit_date]).prod()
    expected = 1.0 + sum(_target_row()[name] * (growth[name] - 1.0) for name in UNIVERSE)
    assert result.daily.iloc[-1]["equity_brl"] / 500_000 == pytest.approx(expected)
    assert result.attribution_brl.sum(axis=1).equals(result.daily["gross_pnl_brl"])


def test_transicao_conta_close_uma_vez_e_negocia_contra_drift():
    sessions = _calendar()
    blocks = _blocks(sessions, count=2)
    returns, adtv, traded, borrow = _inputs(sessions)
    transition = blocks[0].exit_date
    returns.loc[transition, "AGRO3"] = 0.10

    result = run_backtest(returns, _schedule(blocks, reverse_second=True), adtv, traded, borrow)
    assert result.daily.index.is_unique
    assert result.daily.loc[transition, "return_sequence"] == 0
    assert result.daily.loc[transition, "post_trade_sequence"] == 1
    pretrade_agro = 125_000 * 1.10
    target_after = -0.25 * (500_000 + 12_500)
    assert result.orders_brl.loc[transition, "AGRO3"] == pytest.approx(target_after - pretrade_agro)


def test_indisponibilidade_de_um_short_zera_bloco_inteiro_inclusive_custo_zero():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    borrow.recent_trade.loc[blocks[0].decision_date, "BRFS3"] = False

    result = run_backtest(returns, _schedule(blocks), adtv, traded, borrow, scenario="zero")
    assert (result.effective_targets == 0).all().all()
    assert result.block_status.iloc[0]["status"] == "flat_borrow_no_recent_trade"
    assert result.daily["equity_brl"].eq(500_000).all()


def test_limite_de_um_porcento_do_estoque_e_inclusivo():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    decision = blocks[0].decision_date
    borrow.stock_brl.loc[decision, ["BRFS3", "JBSS3"]] = 12_500_000.0
    allowed = run_backtest(returns, _schedule(blocks), adtv, traded, borrow, scenario="zero")
    assert allowed.block_status.iloc[0]["status"] == "planned"

    borrow.stock_brl.loc[decision, "BRFS3"] -= 1.0
    blocked = run_backtest(returns, _schedule(blocks), adtv, traded, borrow, scenario="zero")
    assert blocked.block_status.iloc[0]["status"] == "flat_borrow_capacity"
    assert (blocked.effective_targets == 0).all().all()


def test_capacidade_short_usa_patrimonio_real_na_transicao():
    sessions = _calendar()
    blocks = _blocks(sessions, count=2)
    returns, adtv, traded, borrow = _inputs(sessions)
    returns.loc[sessions[2], "AGRO3"] = 0.10
    second_decision = blocks[1].decision_date
    borrow.stock_brl.loc[second_decision, ["BRFS3", "JBSS3"]] = 12_500_000.0

    result = run_backtest(returns, _schedule(blocks), adtv, traded, borrow, scenario="zero")
    assert result.block_status.iloc[0]["status"] == "planned"
    assert result.block_status.iloc[1]["status"] == "flat_borrow_capacity"
    assert (result.effective_targets.iloc[1] == 0).all()


def test_arquivo_de_aluguel_incompleto_falha_alto_em_vez_de_assumir_zero():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    borrow.complete.loc[blocks[0].decision_date, "BRFS3"] = False
    with pytest.raises(ValueError, match="estado de aluguel incompleto"):
        run_backtest(returns, _schedule(blocks), adtv, traded, borrow, scenario="zero")


def test_papel_sem_negocio_no_close_de_execucao_nao_recebe_ordem():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    traded.loc[blocks[0].execution_date, "AGRO3"] = False
    result = run_backtest(returns, _schedule(blocks), adtv, traded, borrow, scenario="zero")
    assert result.block_status.iloc[0]["status"] == "flat_execution_not_traded"
    assert result.block_status.iloc[0]["limiting_ticker"] == "AGRO3"
    assert (result.effective_targets == 0).all().all()
    assert (result.orders_brl == 0).all().all()


def test_posicao_aberta_sem_negocio_na_saida_falha_alto():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    traded.loc[blocks[0].exit_date, "AGRO3"] = False
    with pytest.raises(ValueError, match="posição mantida sem negociação"):
        run_backtest(returns, _schedule(blocks), adtv, traded, borrow, scenario="zero")


def test_retorno_total_menor_que_menos_cem_porcento_falha_alto():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    returns.loc[sessions[2], "AGRO3"] = -1.01
    with pytest.raises(ValueError, match="menor que -100%"):
        run_backtest(returns, _schedule(blocks), adtv, traded, borrow)


def test_aluguel_incide_21_vezes_sobre_short_antigo_e_nao_no_close_de_entrada():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    result = run_backtest(returns, _schedule(blocks), adtv, traded, borrow, scenario="base")

    charged = result.daily["borrow_cost_brl"] > 0
    assert int(charged.sum()) == 21
    assert not charged.loc[blocks[0].execution_date]
    initial_short = -result.holdings_brl.loc[blocks[0].execution_date].clip(upper=0).sum()
    assert result.daily["borrow_cost_brl"].sum() == pytest.approx(
        initial_short * (0.10 + 0.007 + 0.01) / 252 * 21
    )


def test_entrada_e_saida_pagavam_turnover_e_custo_sem_rebalancear_no_meio():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    zero = run_backtest(returns, _schedule(blocks), adtv, traded, borrow, scenario="zero")
    assert zero.daily.loc[blocks[0].execution_date, "gross_traded"] == pytest.approx(1.0)
    assert zero.daily.loc[blocks[0].execution_date, "turnover_one_way"] == pytest.approx(0.5)
    assert zero.daily.loc[blocks[0].exit_date, "gross_traded"] == pytest.approx(1.0)
    assert zero.daily["spot_cost_brl"].sum() == 0.0

    base = run_backtest(returns, _schedule(blocks), adtv, traded, borrow, scenario="base")
    assert base.daily.loc[blocks[0].execution_date, "spot_cost_brl"] > 0
    assert base.daily.loc[blocks[0].exit_date, "spot_cost_brl"] > 0


def test_solver_de_custo_instala_pesos_exatos_e_fecha_contabilidade():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    result = run_backtest(returns, _schedule(blocks), adtv, traded, borrow, scenario="base")
    entry = blocks[0].execution_date
    assert result.weights.loc[entry].to_dict() == pytest.approx(_target_row(), abs=1e-12)
    identity = (
        result.daily["gross_pnl_brl"]
        - result.daily["borrow_cost_brl"]
        - result.daily["spot_cost_brl"]
    )
    assert np.allclose(identity, result.daily["net_pnl_brl"], atol=1e-7)


def test_retorno_ausente_em_posicao_mantida_falha_alto():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    returns.loc[sessions[2], "AGRO3"] = np.nan
    with pytest.raises(ValueError, match="retorno ausente"):
        run_backtest(returns, _schedule(blocks), adtv, traded, borrow)


def test_ordem_acima_de_cinco_porcento_do_adtv_falha_alto():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    adtv.loc[blocks[0].decision_date] = 1_000_000.0
    with pytest.raises(ValueError, match="excede 5%"):
        run_backtest(returns, _schedule(blocks), adtv, traded, borrow)


def test_holdout_e_bloqueado_antes_de_ler_parquet(monkeypatch, tmp_path: Path):
    sessions = _calendar("2021-01-04", 30)
    block = TradeBlock("2020/21", 0, sessions[0], sessions[1], sessions[22])
    schedule = _schedule((block,))
    _, adtv, traded, borrow = _inputs(sessions)
    called = False

    def forbidden_read(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("parquet não deveria ser aberto")

    monkeypatch.setattr(pd, "read_parquet", forbidden_read)
    with pytest.raises(HoldoutLockedError, match="Fase 6"):
        run_backtest_from_parquet(tmp_path / "holdout.parquet", schedule, adtv, traded, borrow)
    assert not called


def test_painel_de_retorno_precisa_conter_calendario_b3_completo():
    sessions = _calendar()
    blocks = _blocks(sessions)
    returns, adtv, traded, borrow = _inputs(sessions)
    returns = returns.drop(index=sessions[10])
    with pytest.raises(ValueError, match="21 intervalos"):
        run_backtest(returns, _schedule(blocks), adtv, traded, borrow)
