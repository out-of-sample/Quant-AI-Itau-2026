"""Testes do motor de retorno total (quantagro.prices.adjust).

Cobrem a álgebra (dividendo, split, combinação), a convenção de data-ex = pregão seguinte à
data-com, e — o mais importante para a disciplina do projeto — a propriedade **point-in-time**:
o retorno até `t` não pode mudar quando se acrescenta um evento posterior a `t`. Um "adjusted
close" retroativo falharia esse teste; é essa a razão de o motor devolver retorno, não nível.
"""

import numpy as np
import pandas as pd
import pytest

from quantagro.prices.adjust import CorporateEvent, total_return, total_return_index


def _close(values):
    idx = pd.bdate_range("2020-01-06", periods=len(values))  # começa numa segunda-feira
    return pd.Series(values, index=idx, dtype=float, name="TICK3")


class TestSemEventos:
    def test_retorno_e_variacao_simples(self):
        close = _close([100, 110, 99])
        ret = total_return(close)
        assert np.isnan(ret.iloc[0])
        np.testing.assert_allclose(ret.iloc[1:], [0.10, -0.10])

    def test_events_none_e_lista_vazia_sao_equivalentes(self):
        close = _close([100, 110, 99])
        pd.testing.assert_series_equal(total_return(close, None), total_return(close, []))


class TestDividendo:
    def test_dividendo_absorve_a_queda_de_preco_na_data_ex(self):
        # close cai de 100 para 99 exatamente pelo dividendo de 1.00; retorno total = 0.
        close = _close([100, 100, 99, 99])
        ev = CorporateEvent(cum_date=close.index[1], cash_value=1.0)
        ret = total_return(close, [ev])
        assert ret.iloc[2] == pytest.approx(0.0)
        # sem o dividendo, o mesmo pregão teria retorno -1%
        assert total_return(close).iloc[2] == pytest.approx(-0.01)

    def test_dividendo_aplica_no_pregao_seguinte_a_data_com_nao_no_proprio(self):
        close = _close([100, 100, 99, 99])
        ev = CorporateEvent(cum_date=close.index[1], cash_value=1.0)
        ret = total_return(close, [ev])
        # a data-com (índice 1) não é afetada; a data-ex é o índice 2
        assert ret.iloc[1] == pytest.approx(0.0)  # 100/100 - 1
        assert ret.iloc[2] == pytest.approx(0.0)  # (99+1)/100 - 1


class TestSplit:
    def test_split_2x1_e_neutro(self):
        close = _close([100, 100, 50, 50])
        ev = CorporateEvent(cum_date=close.index[1], share_ratio=2.0)
        ret = total_return(close, [ev])
        assert ret.iloc[2] == pytest.approx(0.0)  # (2*50)/100 - 1
        assert total_return(close).iloc[2] == pytest.approx(-0.5)  # sem o split, cairia 50%


class TestCombinado:
    def test_split_e_dividendo_na_mesma_data_ex(self):
        # 1 ação vira 2 (a 49.5 cada) + 1.00 em dinheiro por ação original = 100 → retorno 0
        close = _close([100, 100, 49.5, 49.5])
        ev = CorporateEvent(cum_date=close.index[1], cash_value=1.0, share_ratio=2.0)
        assert total_return(close, [ev]).iloc[2] == pytest.approx(0.0)


class TestForaDaJanela:
    def test_evento_com_data_com_no_ultimo_pregao_e_ignorado(self):
        close = _close([100, 101, 102])
        ev = CorporateEvent(cum_date=close.index[-1], cash_value=5.0)  # sem pregão seguinte
        pd.testing.assert_series_equal(total_return(close, [ev]), total_return(close))

    def test_evento_apos_a_serie_e_ignorado(self):
        close = _close([100, 101, 102])
        ev = CorporateEvent(cum_date=close.index[-1] + pd.Timedelta(days=30), cash_value=5.0)
        pd.testing.assert_series_equal(total_return(close, [ev]), total_return(close))


class TestPointInTime:
    def test_retorno_passado_nao_muda_com_evento_futuro(self):
        # A prova de que a série é forward-only: acrescentar um evento em t=4 não pode alterar
        # nenhum retorno até t=3. Um adjusted-close retroativo reprovaria aqui.
        close = _close([100, 100, 99, 99, 80, 80])
        ev_passado = CorporateEvent(cum_date=close.index[1], cash_value=1.0)
        ev_futuro = CorporateEvent(cum_date=close.index[4], cash_value=1.0)
        so_passado = total_return(close, [ev_passado])
        com_futuro = total_return(close, [ev_passado, ev_futuro])
        pd.testing.assert_series_equal(so_passado.iloc[:4], com_futuro.iloc[:4])
        # e o evento futuro de fato muda o retorno na sua própria data-ex (índice 5)
        assert so_passado.iloc[5] != pytest.approx(com_futuro.iloc[5])


class TestIndiceDeRetornoTotal:
    def test_base_1_e_cumprod(self):
        close = _close([100, 110, 99])
        tri = total_return_index(close)
        assert tri.iloc[0] == pytest.approx(1.0)
        assert tri.iloc[1] == pytest.approx(1.10)
        assert tri.iloc[2] == pytest.approx(1.10 * 0.90)


class TestValidacao:
    def test_indice_desordenado_falha(self):
        close = _close([100, 110, 99]).iloc[::-1]
        with pytest.raises(ValueError, match="ordenado"):
            total_return(close)

    def test_datas_duplicadas_falham(self):
        idx = pd.to_datetime(["2020-01-06", "2020-01-06", "2020-01-08"])
        close = pd.Series([100.0, 101.0, 102.0], index=idx)
        with pytest.raises(ValueError, match="duplicadas"):
            total_return(close)

    def test_share_ratio_invalido_falha(self):
        with pytest.raises(ValueError, match="share_ratio"):
            CorporateEvent(cum_date=pd.Timestamp("2020-01-07"), share_ratio=0.0)

    def test_cash_negativo_falha(self):
        with pytest.raises(ValueError, match="cash_value"):
            CorporateEvent(cum_date=pd.Timestamp("2020-01-07"), cash_value=-1.0)
