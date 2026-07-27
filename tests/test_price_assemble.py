"""Testes do montador (prices/assemble): merge de fontes, delisting e tripwire de split.

O merge B3 × StatusInvest é testado com as fixtures **reais** das duas fontes (SLC), incluindo
o caso divergente de 3,9e-4 do cross-check e o par dividendo+JCP na mesma data-com. O corte na
deslistagem reproduz o resíduo real da BRFS3 (provento com data-com após a incorporação).
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.cotahist import filter_equities_spot, parse_cotahist
from quantagro.ingest.events_b3 import b3_cash_to_events
from quantagro.ingest.events_manual import manual_events
from quantagro.ingest.events_statusinvest import statusinvest_to_events
from quantagro.prices.adjust import CorporateEvent
from quantagro.prices.assemble import (
    assemble_total_return,
    close_series,
    flag_suspect_returns,
    merge_cash_events,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def b3_slc_events() -> list[CorporateEvent]:
    raw = json.loads((FIXTURES / "b3_cash_slc.json").read_text(encoding="utf-8"))["results"]
    return b3_cash_to_events(raw, "SLCE3")


@pytest.fixture
def si_slc_events() -> list[CorporateEvent]:
    raw = json.loads((FIXTURES / "statusinvest_slc.json").read_text(encoding="utf-8"))
    return statusinvest_to_events(raw["assetEarningsModels"])


def _close(dates: list[str], values: list[float], name: str = "XXXX3") -> pd.Series:
    return pd.Series(values, index=pd.DatetimeIndex(dates), name=name)


class TestCloseSeries:
    def test_extrai_do_cotahist_real(self):
        # a fixture real de 27/12/2024: SLCE3 fechou 17,68 com fatcot=1
        df = filter_equities_spot(parse_cotahist(FIXTURES / "cotahist_sample.txt"))
        s = close_series(df, "SLCE3")
        assert s.loc[pd.Timestamp("2024-12-27")] == pytest.approx(17.68)
        assert s.name == "SLCE3"

    def test_normaliza_fatcot_1000_para_por_acao(self):
        df = pd.DataFrame(
            {
                "date": [pd.Timestamp("2005-01-03")],
                "ticker": ["VELH3"],
                "close": [850.0],  # cotação por lote de mil
                "quote_factor": [1000],
            }
        )
        s = close_series(df, "VELH3")
        assert s.iloc[0] == pytest.approx(0.85)

    def test_data_duplicada_e_erro(self):
        df = pd.DataFrame(
            {
                "date": [pd.Timestamp("2024-01-02")] * 2,
                "ticker": ["SLCE3"] * 2,
                "close": [17.0, 18.0],
                "quote_factor": [1, 1],
            }
        )
        with pytest.raises(ValueError, match="mais de uma cotação"):
            close_series(df, "SLCE3")

    def test_ticker_ausente_e_erro(self):
        df = filter_equities_spot(parse_cotahist(FIXTURES / "cotahist_sample.txt"))
        with pytest.raises(ValueError, match="nenhuma cotação"):
            close_series(df, "NAOEXISTE")


class TestMergeCashEvents:
    def test_sobreposicao_real_nao_conta_duas_vezes(self, b3_slc_events, si_slc_events):
        # B3 (8 eventos) cobre todas as datas da StatusInvest exceto 03/04/2008:
        # o merge tem que dar 8 + 1, mesmo com o caso divergente de 3,9e-4 (04/05/2023).
        merged = merge_cash_events(b3_slc_events, si_slc_events)
        assert len(merged) == len(b3_slc_events) + 1
        so_fallback = [e for e in merged if e.cum_date == pd.Timestamp("2008-04-03")]
        assert len(so_fallback) == 1

    def test_na_sobreposicao_vale_o_valor_da_primaria(self, b3_slc_events, si_slc_events):
        # no caso divergente, o valor mantido é o da B3 (2,59617683), não o da StatusInvest
        merged = merge_cash_events(b3_slc_events, si_slc_events)
        ev = [e for e in merged if e.cum_date == pd.Timestamp("2023-05-04")]
        assert len(ev) == 1
        assert ev[0].cash_value == pytest.approx(2.59617683, rel=1e-8)

    def test_dividendo_e_jcp_na_mesma_data_sobrevivem(self, b3_slc_events, si_slc_events):
        # 12/12/2025 tem dividendo E JCP (real); o casamento 1-para-1 não pode fundi-los
        merged = merge_cash_events(b3_slc_events, si_slc_events)
        no_dia = [e for e in merged if e.cum_date == pd.Timestamp("2025-12-12")]
        assert sorted(round(e.cash_value, 6) for e in no_dia) == [0.045291, 0.860520]

    def test_fallback_preenche_lacuna_na_mesma_data(self):
        primaria = [CorporateEvent(cum_date=pd.Timestamp("2020-05-10"), cash_value=1.0)]
        fallback = [
            CorporateEvent(cum_date=pd.Timestamp("2020-05-10"), cash_value=1.0),  # duplicado
            CorporateEvent(cum_date=pd.Timestamp("2020-05-10"), cash_value=0.3),  # lacuna real
        ]
        merged = merge_cash_events(primaria, fallback)
        assert sorted(e.cash_value for e in merged) == [0.3, 1.0]

    def test_fallback_sozinho_passa_inteiro(self, si_slc_events):
        merged = merge_cash_events([], si_slc_events)
        assert len(merged) == len(si_slc_events)

    def test_saida_ordenada_por_data_com(self, b3_slc_events, si_slc_events):
        merged = merge_cash_events(b3_slc_events, si_slc_events)
        datas = [e.cum_date for e in merged]
        assert datas == sorted(datas)


class TestAssembleTotalReturn:
    def test_bonificacao_slc_2021_esta_no_registro_manual(self):
        events = manual_events("SLCE3")
        event = [item for item in events if item.cum_date == pd.Timestamp("2021-12-30")]
        assert len(event) == 1
        assert event[0].share_ratio == pytest.approx(1.1)

    def test_split_real_smto_2016_fica_neutro_com_ratio_tres(self):
        quotes = filter_equities_spot(parse_cotahist(FIXTURES / "cotahist_smto_split_2016.txt"))
        close = close_series(quotes, "SMTO3")
        event = CorporateEvent(cum_date=pd.Timestamp("2016-12-09"), share_ratio=3.0)
        ret = assemble_total_return(close, stock=[event]).dropna()
        assert ret.iloc[0] == pytest.approx(3 * 17.45 / 52.45 - 1)
        assert abs(ret.iloc[0]) < 0.01

    def test_dividendo_de_cada_fonte_entra_uma_vez(self):
        close = _close(["2024-01-02", "2024-01-03", "2024-01-04"], [10.0, 9.0, 9.0])
        ev = CorporateEvent(cum_date=pd.Timestamp("2024-01-02"), cash_value=1.0)
        ret = assemble_total_return(close, cash_primary=[ev], cash_fallback=[ev])
        # (9 + 1)/10 - 1 = 0: o dividendo absorve a queda UMA vez (não duas)
        assert ret.loc[pd.Timestamp("2024-01-03")] == pytest.approx(0.0)

    def test_split_e_dinheiro_juntos(self):
        close = _close(["2024-01-02", "2024-01-03"], [20.0, 10.5])
        div = CorporateEvent(cum_date=pd.Timestamp("2024-01-02"), cash_value=0.5)
        split = CorporateEvent(cum_date=pd.Timestamp("2024-01-02"), share_ratio=2.0)
        ret = assemble_total_return(close, cash_primary=[div], stock=[split])
        # (2·10,5 + 0,5)/20 − 1 = 7,5%
        assert ret.loc[pd.Timestamp("2024-01-03")] == pytest.approx(0.075)

    def test_provento_apos_deslistagem_e_ignorado(self):
        # o resíduo real da BRFS3: data-com depois do último pregão do papel.
        close = _close(["2025-06-04", "2025-06-05", "2025-06-06"], [10.0, 10.2, 10.1])
        residuo = CorporateEvent(cum_date=pd.Timestamp("2025-09-18"), cash_value=1.83)
        com_residuo = assemble_total_return(close, cash_primary=[residuo])
        sem_nada = assemble_total_return(close)
        pd.testing.assert_series_equal(com_residuo, sem_nada)

    def test_data_com_no_ultimo_pregao_tambem_e_ignorada(self):
        # a data-ex seria o pregão seguinte — que não existe para um papel deslistado.
        close = _close(["2025-06-04", "2025-06-05", "2025-06-06"], [10.0, 10.2, 10.1])
        ev = CorporateEvent(cum_date=pd.Timestamp("2025-06-06"), cash_value=5.0)
        com_ev = assemble_total_return(close, cash_primary=[ev])
        sem_ev = assemble_total_return(close)
        pd.testing.assert_series_equal(com_ev, sem_ev)


class TestFlagSuspectReturns:
    def test_pega_split_perdido(self):
        # split 2:1 sem o evento na fonte: o close cai ~50% e o "retorno" vira −49,5%
        close = _close(["2024-01-02", "2024-01-03", "2024-01-04"], [40.0, 20.2, 20.4])
        ret = assemble_total_return(close)  # sem eventos = split perdido
        suspeitos = flag_suspect_returns(ret)
        assert list(suspeitos.index) == [pd.Timestamp("2024-01-03")]

    def test_serie_com_evento_correto_fica_limpa(self):
        close = _close(["2024-01-02", "2024-01-03", "2024-01-04"], [40.0, 20.2, 20.4])
        split = CorporateEvent(cum_date=pd.Timestamp("2024-01-02"), share_ratio=2.0)
        ret = assemble_total_return(close, stock=[split])
        assert flag_suspect_returns(ret).empty

    def test_grupamento_perdido_tambem_dispara(self):
        close = _close(["2024-01-02", "2024-01-03"], [1.0, 9.9])
        ret = assemble_total_return(close)
        assert not flag_suspect_returns(ret).empty
