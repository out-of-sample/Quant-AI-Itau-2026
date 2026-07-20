"""Invariantes do contrato congelado da estratégia reformulada (D-053), antes do holdout."""

import numpy as np

from quantagro.backtest.strategy_spec import (
    ALPHA,
    CANE_NAME,
    CANE_SATELLITE_CAP,
    CLUSTER_BY,
    EXEC_LAG_DAYS,
    FWD_HORIZON_DAYS,
    GRAIN_NAME_CAP,
    GRAIN_NAMES,
    GROSS,
    HOLDOUT_CROP_YEARS,
    INFERENCE,
    NATIONAL_SHOCK_WEIGHTING,
    PRIMARY_TEST,
    PRIMARY_TEST_UNIVERSE,
    TEST_IS_ONE_SIDED,
    UNIVERSE,
    dollar_neutral_weights,
    operational_cane_score,
    operational_grain_score,
    validate_strategy_spec,
)


def test_universo_congelado_cinco_nomes():
    assert UNIVERSE == ("AGRO3", "SLCE3", "BRFS3", "JBSS3", "SMTO3")
    assert set(GRAIN_NAMES) == {"AGRO3", "SLCE3", "BRFS3", "JBSS3"}
    assert CANE_NAME == "SMTO3"


def test_hprime_inverte_o_sinal_de_graos_mas_nao_o_de_cana():
    # H′: a seca prejudica o produtor de grão -> score operacional = -(E·Shock).
    assert operational_grain_score(1.0) == -1.0
    assert operational_grain_score(-2.0) == 2.0
    # Cana: seca de maturação -> ATR sobe -> long (direção +1).
    assert operational_cane_score(1.0) == 1.0
    assert operational_cane_score(-1.0) == -1.0


def test_teste_primario_e_so_graos_para_proteger_a_forca():
    # A1: o mecanismo fraco da cana não entra no teste estatístico primário.
    assert PRIMARY_TEST_UNIVERSE == GRAIN_NAMES
    assert CANE_NAME not in PRIMARY_TEST_UNIVERSE
    assert TEST_IS_ONE_SIDED and 0.0 < ALPHA < 0.5


def test_pesos_do_choque_sao_o_contrato_conab():
    assert NATIONAL_SHOCK_WEIGHTING == "conab"


def test_holdout_tem_cinco_anos_safra_lacrados():
    assert HOLDOUT_CROP_YEARS == ("2020/21", "2021/22", "2022/23", "2023/24", "2024/25")


def test_execucao_e_inferencia_congeladas():
    assert EXEC_LAG_DAYS == 1
    assert FWD_HORIZON_DAYS == 21
    assert GROSS == 1.0
    assert PRIMARY_TEST == "producer_processor_spread_panel"
    assert INFERENCE == "permutation_cluster_by_crop_year"
    assert CLUSTER_BY == "ano_agricola"


def test_sizing_e_dollar_neutral_e_bruto_unitario():
    scores = {"AGRO3": -0.8, "SLCE3": -0.3, "BRFS3": 0.5, "JBSS3": 0.6, "SMTO3": 0.1}
    w = dollar_neutral_weights(scores)
    assert abs(sum(w.values())) < 1e-9  # Σw = 0 (dollar-neutral)
    assert abs(sum(abs(v) for v in w.values()) - 1.0) < 1e-9  # Σ|w| = 1


def test_sizing_respeita_os_caps_por_nome():
    # Score extremo num grão e na cana; os caps 0,40/0,15 têm de segurar.
    scores = {"AGRO3": -100.0, "SLCE3": 0.0, "BRFS3": 0.0, "JBSS3": 0.0, "SMTO3": 100.0}
    w = dollar_neutral_weights(scores)
    assert abs(w["AGRO3"]) <= GRAIN_NAME_CAP + 1e-9
    assert abs(w["SMTO3"]) <= CANE_SATELLITE_CAP + 1e-9
    assert abs(sum(w.values())) < 1e-9


def test_water_filling_nao_reabre_nome_que_ja_bateu_no_cap():
    # Regressão do defeito encontrado na auditoria pré-Fase 4: a implementação anterior
    # recolocava no conjunto livre um nome já capado e devolvia 29,7% apesar do teto de 25%.
    scores = {"AGRO3": 100.0, "SLCE3": 40.0, "BRFS3": 1.0, "JBSS3": -141.0}
    caps = {"AGRO3": 0.25, "SLCE3": 0.20, "BRFS3": 0.50, "JBSS3": 0.50}
    w = dollar_neutral_weights(scores, caps)
    assert abs(w["AGRO3"]) <= 0.25 + 1e-12
    assert abs(w["SLCE3"]) <= 0.20 + 1e-12
    assert abs(sum(w.values())) < 1e-12
    assert abs(sum(abs(v) for v in w.values()) - 1.0) < 1e-12


def test_satelite_da_cana_e_mais_apertado_que_grao():
    assert 0.0 < CANE_SATELLITE_CAP <= GRAIN_NAME_CAP <= 1.0


def test_sizing_sinal_zero_gera_carteira_vazia():
    scores = {n: 0.0 for n in UNIVERSE}
    w = dollar_neutral_weights(scores)
    assert all(v == 0.0 for v in w.values())


def test_sizing_rejeita_score_nao_finito_ticker_desconhecido_e_cap_ausente():
    import pytest

    with pytest.raises(ValueError, match="finitos"):
        dollar_neutral_weights({"AGRO3": np.nan, "BRFS3": 1.0})
    with pytest.raises(ValueError, match="fora do universo"):
        dollar_neutral_weights({"AGRO3": -1.0, "FAKE3": 1.0}, {"AGRO3": 0.5, "FAKE3": 0.5})
    with pytest.raises(ValueError, match="caps ausentes"):
        dollar_neutral_weights({"AGRO3": -1.0, "BRFS3": 1.0}, {"AGRO3": 0.5})


def test_sizing_proporcional_ao_sinal_preserva_ordem():
    # Sem cap ativo, |peso| deve crescer com |score demeanado| (B1: proporcional ao sinal).
    scores = {"AGRO3": -0.2, "SLCE3": -0.1, "BRFS3": 0.1, "JBSS3": 0.2, "SMTO3": 0.0}
    w = dollar_neutral_weights(scores)
    assert abs(w["AGRO3"]) > abs(w["SLCE3"])
    assert abs(w["JBSS3"]) > abs(w["BRFS3"])


def test_vetorizado_operational_grain_score():
    x = np.array([1.0, -2.0, 0.0])
    np.testing.assert_allclose(operational_grain_score(x), [-1.0, 2.0, 0.0])


def test_validador_passa_no_contrato_atual():
    validate_strategy_spec()  # não deve levantar


def test_soma_dos_sinais_operacionais_nao_quebra_convencao_de_mecanismo():
    # Garantia cruzada: a camada H′ NÃO altera signal/convention.raw_signal (canal falsificado).
    from quantagro.signal.convention import raw_signal

    # produtor sob estresse: mecanismo positivo (convenção antiga intacta)...
    assert raw_signal(1.0, 1.0) > 0
    # ...mas a estratégia operacional H′ o trata como negativo (short o produtor).
    assert operational_grain_score(raw_signal(1.0, 1.0)) < 0
