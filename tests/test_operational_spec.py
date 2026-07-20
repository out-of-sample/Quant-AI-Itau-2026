"""Invariantes do fechamento operacional return-agnóstico D-055."""

import math

import pandas as pd
import pytest

from quantagro.backtest.operational_spec import (
    ADTV_FLOOR_BRL,
    BORROW_LOOKBACK_SESSIONS,
    CANE_NAME,
    DEV_CROP_YEARS,
    EXPECTED_PERMUTATIONS,
    HOLDING_SESSIONS,
    HOLDOUT_CROP_YEARS,
    REFERENCE_AUM_BRL,
    TRANSITION_CROP_YEAR,
    HoldoutLockedError,
    TradeBlock,
    aggregate_cane_shock,
    borrow_all_in_rate,
    borrow_capacity_brl,
    borrow_is_available,
    build_trade_blocks,
    classify_block,
    compose_operational_scores,
    exact_primary_signflip,
    grain_mechanism_score,
    one_way_equity_cost_rate,
    require_backtest_scope,
    spot_capacity_brl,
    spot_participation,
    validate_operational_spec,
)


def _sessions(start="2014-01-01", end="2026-12-31"):
    return pd.bdate_range(start, end)


def test_grade_ancora_fim_de_semana_e_execucao_d1():
    # 07/01/2017 foi sábado: decisão no primeiro pregão sintético seguinte, execução no próximo.
    blocks = build_trade_blocks(_sessions(), "2016/17")
    assert blocks[0].decision_date == pd.Timestamp("2017-01-09")
    assert blocks[0].execution_date == pd.Timestamp("2017-01-10")


def test_blocos_tem_21_intervalos_e_transicao_sem_sobreposicao():
    sessions = _sessions()
    positions = {date: pos for pos, date in enumerate(sessions)}
    blocks = build_trade_blocks(sessions, "2018/19")
    for block in blocks:
        assert positions[block.exit_date] - positions[block.execution_date] == HOLDING_SESSIONS
    for previous, current in zip(blocks, blocks[1:], strict=False):
        assert previous.exit_date == current.execution_date
        assert current.decision_date < current.execution_date


def test_ultimo_bloco_e_primeiro_da_grade_com_decisao_apos_sete_de_setembro():
    blocks = build_trade_blocks(_sessions(), "2018/19")
    cutoff = pd.Timestamp("2019-09-07")
    assert blocks[-1].decision_date >= cutoff
    assert all(block.decision_date < cutoff for block in blocks[:-1])


def test_score_graos_manual_e_cultura_nao_iniciada_sem_renormalizacao():
    exposure = {"soy": 0.7, "corn_second": 0.3}
    assert grain_mechanism_score(exposure, {"soy": 2.0, "corn_second": -1.0}) == pytest.approx(1.1)
    assert grain_mechanism_score(exposure, {"soy": 2.0, "corn_second": None}) == pytest.approx(1.4)


def test_score_graos_falha_em_buraco_tecnico_e_chave_ausente():
    exposure = {"soy": 0.7, "corn_second": 0.3}
    with pytest.raises(ValueError, match="indefinido"):
        grain_mechanism_score(exposure, {"soy": 1.0, "corn_second": float("nan")})
    with pytest.raises(ValueError, match="exatamente"):
        grain_mechanism_score(exposure, {"soy": 1.0})


def test_cana_exige_cinco_ufs_e_mantem_escala_um_para_um():
    shocks = {"GO": 1.0, "MG": 2.0, "MS": 3.0, "PR": 4.0, "SP": 5.0}
    weights = {"GO": 1.0, "MG": 1.0, "MS": 1.0, "PR": 1.0, "SP": 6.0}
    assert aggregate_cane_shock(shocks, weights) == 4.0
    with pytest.raises(ValueError, match="cinco UFs"):
        aggregate_cane_shock(shocks | {"BA": 1.0}, weights)


def test_universo_sem_os_dois_lados_economicos_fica_inteiro_zerado():
    raw = {"AGRO3": 1.0, "SLCE3": 2.0, "BRFS3": -1.0}
    assert compose_operational_scores(raw, ["AGRO3", "SLCE3"]) == {}
    assert compose_operational_scores(raw, ["BRFS3"]) == {}


def test_core_valido_inverte_graos_e_cana_so_entra_quando_ativa():
    raw = {"AGRO3": 1.0, "BRFS3": -2.0}
    without_cane = compose_operational_scores(raw, ["AGRO3", "BRFS3", CANE_NAME])
    assert without_cane == {"AGRO3": -1.0, "BRFS3": 2.0}
    with_cane = compose_operational_scores(raw, ["AGRO3", "BRFS3", CANE_NAME], cane_shock=0.5)
    assert with_cane[CANE_NAME] == 0.5
    assert tuple(with_cane) == ("AGRO3", "BRFS3", CANE_NAME)


def test_particao_exclui_2019_20_e_lacra_holdout():
    dev = build_trade_blocks(_sessions(), DEV_CROP_YEARS[-1])
    transition = build_trade_blocks(_sessions(), TRANSITION_CROP_YEAR)
    holdout = build_trade_blocks(_sessions(), HOLDOUT_CROP_YEARS[0])
    assert {classify_block(block) for block in dev} == {"dev"}
    assert {classify_block(block) for block in transition} == {"excluded"}
    assert {classify_block(block) for block in holdout} == {"holdout"}
    assert require_backtest_scope(dev) == "dev"
    with pytest.raises(ValueError, match="fora do dev/holdout"):
        require_backtest_scope(transition)
    with pytest.raises(HoldoutLockedError, match="Fase 6"):
        require_backtest_scope(holdout)
    assert require_backtest_scope(holdout, allow_holdout=True) == "holdout"


def test_bloco_que_cruza_fronteira_nao_e_truncado():
    crossing = TradeBlock(
        "2018/19",
        99,
        pd.Timestamp("2019-12-20"),
        pd.Timestamp("2019-12-23"),
        pd.Timestamp("2020-01-23"),
    )
    assert classify_block(crossing) == "excluded"


def test_bloco_malformado_e_execucao_vazia_falham_alto():
    with pytest.raises(ValueError, match="decisão < execução < saída"):
        TradeBlock(
            "2018/19",
            0,
            pd.Timestamp("2019-01-10"),
            pd.Timestamp("2019-01-10"),
            pd.Timestamp("2019-02-10"),
        )
    with pytest.raises(ValueError, match="ao menos um bloco"):
        require_backtest_scope([])


def test_permutacao_exata_tem_32_estados_e_p_minimo_um_sobre_32():
    effects = dict.fromkeys(HOLDOUT_CROP_YEARS, 1.0)
    result = exact_primary_signflip(effects)
    assert result.permutations == EXPECTED_PERMUTATIONS == 32
    assert result.pvalue == 1 / 32
    assert result.passed


def test_permutacao_exige_todas_as_cinco_safras_sem_nan():
    with pytest.raises(ValueError, match="cinco anos"):
        exact_primary_signflip(dict.fromkeys(HOLDOUT_CROP_YEARS[:-1], 1.0))
    effects = dict.fromkeys(HOLDOUT_CROP_YEARS, 1.0)
    effects[HOLDOUT_CROP_YEARS[-1]] = float("nan")
    with pytest.raises(ValueError, match="finitas"):
        exact_primary_signflip(effects)


def test_patrimonio_piso_adtv_fecham_reversao_no_cap_em_cinco_porcento():
    assert REFERENCE_AUM_BRL == 500_000
    assert ADTV_FLOOR_BRL == 8_000_000
    assert spot_participation(0.80, ADTV_FLOOR_BRL) == pytest.approx(0.05)
    with pytest.raises(ValueError, match="excede"):
        one_way_equity_cost_rate(0.81, ADTV_FLOOR_BRL)


def test_custo_equity_base_zero_e_dobrado():
    base = one_way_equity_cost_rate(0.16, 8_000_000)  # ordem R$80 mil = 1% ADTV
    assert base == pytest.approx(20.5 / 10_000)
    assert one_way_equity_cost_rate(0.16, 8_000_000, scenario="zero") == 0
    assert one_way_equity_cost_rate(0.16, 8_000_000, scenario="double") == pytest.approx(2 * base)


def test_aluguel_tem_piso_tarifa_b3_intermediacao_e_stress():
    # Piso 5% + cap B3 0,70% + intermediação 1% = 6,70% a.a.
    base = borrow_all_in_rate(0.002)
    assert base == pytest.approx(0.067)
    assert borrow_all_in_rate(0.002, "double") == pytest.approx(0.134)
    assert borrow_all_in_rate(0.002, "zero") == 0
    assert BORROW_LOOKBACK_SESSIONS == 5


def test_disponibilidade_exige_negocio_recente_e_profundidade():
    assert borrow_is_available([0, 0, 100, 0, 0], stock_brl=20_000_000, short_notional_brl=200_000)
    assert not borrow_is_available(
        [0, 0, 0, 0, 0], stock_brl=20_000_000, short_notional_brl=100_000
    )
    assert not borrow_is_available([1], stock_brl=20_000_000, short_notional_brl=200_001)
    with pytest.raises(ValueError, match="até cinco"):
        borrow_is_available([1, 1, 1, 1, 1, 1], 20_000_000, 100_000)


def test_capacidade_combina_ordem_e_estoque_de_aluguel():
    assert spot_capacity_brl(8_000_000, 0.8) == 500_000
    assert borrow_capacity_brl(20_000_000, -0.4) == 500_000
    assert math.isinf(spot_capacity_brl(8_000_000, 0.0))
    assert math.isinf(borrow_capacity_brl(20_000_000, 0.4))


def test_validador_passa_no_contrato_atual():
    validate_operational_spec()
