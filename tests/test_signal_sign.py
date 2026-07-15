"""Teste-canário da convenção de sinal.

Existe antes do sinal existir, de propósito: trava a regra de *quem sobe e quem cai* sob
estresse climático, que é o ponto onde nasce o bug mais caro e mais silencioso desta
estratégia — tratar um frigorífico como se fosse produtor (risco R11).

Se algum dia este teste ficar vermelho, a suposição não é "atualiza o teste": é "alguém
inverteu o sinal". A convenção está fixada na tese pré-registrada (01_TESE §3) e não muda
sem uma decisão registrada em 07_RISCOS_E_DECISOES.md.
"""

import numpy as np

from quantagro.signal.convention import FLAT, LONG, SHORT, position_side, raw_signal


class TestRawSignal:
    def test_produtor_sob_estresse_recebe_score_positivo(self):
        # Produtor puro (E=+1) sob seca na fase crítica (Shock=+1): preço sobe, ele ganha.
        assert raw_signal(exposure=1.0, shock=1.0) > 0

    def test_frigorifico_sob_estresse_recebe_score_negativo(self):
        # Consumidor do insumo (E=-1) sob o MESMO estresse: custo sobe, margem cai.
        assert raw_signal(exposure=-1.0, shock=1.0) < 0

    def test_supersafra_inverte_ambos_os_lados(self):
        # Shock negativo (clima bom demais, super oferta): produtor perde, frigorífico ganha.
        assert raw_signal(exposure=1.0, shock=-1.0) < 0
        assert raw_signal(exposure=-1.0, shock=-1.0) > 0

    def test_sem_choque_nao_gera_sinal(self):
        assert raw_signal(exposure=1.0, shock=0.0) == 0
        assert raw_signal(exposure=-1.0, shock=0.0) == 0

    def test_sem_exposicao_nao_gera_sinal(self):
        assert raw_signal(exposure=0.0, shock=1.0) == 0

    def test_vetorizado_preserva_a_convencao_elemento_a_elemento(self):
        exposure = np.array([1.0, -1.0, 0.0, 0.5])
        shock = np.array([1.0, 1.0, 1.0, -2.0])
        out = raw_signal(exposure, shock)
        np.testing.assert_allclose(out, [1.0, -1.0, 0.0, -1.0])


class TestPositionSide:
    def test_score_positivo_e_long(self):
        assert position_side(0.7) == LONG

    def test_score_negativo_e_short(self):
        assert position_side(-0.7) == SHORT

    def test_score_zero_e_flat(self):
        assert position_side(0.0) == FLAT

    def test_direcoes_sao_1_menos1_0(self):
        # Amarra os valores concretos: se alguém trocar LONG por -1, o resto do código quebra.
        assert (LONG, SHORT, FLAT) == (1, -1, 0)

    def test_vetorizado(self):
        scores = np.array([2.0, -3.0, 0.0])
        np.testing.assert_array_equal(position_side(scores), [LONG, SHORT, FLAT])
