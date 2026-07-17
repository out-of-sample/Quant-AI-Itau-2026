"""Testes da camada C1: carimbo point-in-time e universo dinâmico.

O invariante testado com mais força é o negativo: `available_asof` nunca devolve linha com
`avail_date > t`, dado sem carimbo não passa, e `ref_date` fora do mapa explode em vez de
interpolar (R10). No universo, os quatro critérios do protocolo (§1) e as duas propriedades
estruturais: deslistagem não apaga o passado e seasoning é conservador no início da janela.
"""

import pandas as pd
import pytest

from quantagro.validate.pit import available_asof, stamp_avail_date
from quantagro.validate.universe import eligible_count, universe_membership


class TestStampAvailDate:
    def _df(self, dates):
        return pd.DataFrame({"ref_date": pd.to_datetime(dates), "valor": range(len(dates))})

    def test_lag_fixo_em_dias_corridos(self):
        out = stamp_avail_date(self._df(["2024-01-10"]), lag_days=7)
        assert out["avail_date"].iloc[0] == pd.Timestamp("2024-01-17")

    def test_lag_zero_e_valido(self):
        # COTAHIST: disponível no fim do próprio pregão (execução D+1 cobre o intradiário)
        out = stamp_avail_date(self._df(["2024-01-10"]), lag_days=0)
        assert out["avail_date"].iloc[0] == pd.Timestamp("2024-01-10")

    def test_lag_negativo_e_erro(self):
        with pytest.raises(ValueError, match="negativo"):
            stamp_avail_date(self._df(["2024-01-10"]), lag_days=-1)

    def test_mapa_explicito(self):
        mapa = pd.Series(
            {pd.Timestamp("2024-01-10"): pd.Timestamp("2024-02-15")}  # divulgação irregular
        )
        out = stamp_avail_date(self._df(["2024-01-10"]), avail_map=mapa)
        assert out["avail_date"].iloc[0] == pd.Timestamp("2024-02-15")

    def test_ref_fora_do_mapa_explode_em_vez_de_interpolar(self):
        # R10: calendário irregular sem entrada é erro, nunca interpolação silenciosa
        mapa = pd.Series({pd.Timestamp("2024-01-10"): pd.Timestamp("2024-02-15")})
        with pytest.raises(ValueError, match="sem avail_date no mapa"):
            stamp_avail_date(self._df(["2024-01-10", "2024-02-10"]), avail_map=mapa)

    def test_exige_exatamente_um_modo(self):
        df = self._df(["2024-01-10"])
        with pytest.raises(ValueError, match="exatamente um"):
            stamp_avail_date(df)
        with pytest.raises(ValueError, match="exatamente um"):
            stamp_avail_date(df, lag_days=1, avail_map=pd.Series(dtype="datetime64[ns]"))

    def test_nao_mutila_o_original(self):
        df = self._df(["2024-01-10"])
        stamp_avail_date(df, lag_days=3)
        assert "avail_date" not in df.columns


class TestAvailableAsof:
    def test_nunca_devolve_linha_futura(self):
        df = stamp_avail_date(
            pd.DataFrame({"ref_date": pd.to_datetime(["2024-01-01", "2024-01-10"])}),
            lag_days=7,
        )
        vis = available_asof(df, "2024-01-09")
        assert len(vis) == 1  # só a de ref 01/01 (avail 08/01); a de 10/01 só em 17/01
        assert (vis["avail_date"] <= pd.Timestamp("2024-01-09")).all()

    def test_dado_sem_carimbo_nao_passa(self):
        df = pd.DataFrame({"ref_date": pd.to_datetime(["2024-01-01"])})
        with pytest.raises(ValueError, match="sem coluna 'avail_date'"):
            available_asof(df, "2024-01-09")


def _quotes(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    """(date, ticker, financial_volume) → DataFrame no schema do parse_cotahist."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime([r[0] for r in rows]),
            "ticker": [r[1] for r in rows],
            "financial_volume": [r[2] for r in rows],
        }
    )


def _daily(ticker: str, start: str, n: int, vol: float) -> list[tuple[str, str, float]]:
    dates = pd.bdate_range(start, periods=n)
    return [(d.strftime("%Y-%m-%d"), ticker, vol) for d in dates]


class TestUniverseMembership:
    def test_seasoning_60_pregoes(self):
        quotes = _quotes(_daily("NOVA3", "2024-01-02", 80, 1e6))
        m = universe_membership(quotes, adtv_floor=0.0, ipo_seasoning=60, adtv_window=5)
        assert not m["NOVA3"].iloc[:60].any()  # 60 primeiros pregões: fora
        assert m["NOVA3"].iloc[60:].all()  # do 61º em diante: dentro

    def test_piso_de_adtv_exclui_iliquido(self):
        liq = _daily("LIQD3", "2024-01-02", 80, 5e6)
        ili = _daily("ILIQ3", "2024-01-02", 80, 1e4)  # bem abaixo do piso
        m = universe_membership(_quotes(liq + ili), adtv_floor=1e6, ipo_seasoning=10, adtv_window=5)
        assert m["LIQD3"].iloc[-1]
        assert not m["ILIQ3"].any()

    def test_dia_sem_negociacao_derruba_o_adtv(self):
        # papel líquido que para de negociar por vários dias: volume zero conta contra
        rows = _daily("FALH3", "2024-01-02", 30, 1e6)
        rows += _daily("FALH3", "2024-03-01", 30, 1e6)  # buraco de fevereiro
        rows += _daily("CHEIO3", "2024-01-02", 72, 1e6)  # calendário completo
        m = universe_membership(_quotes(rows), adtv_floor=9e5, ipo_seasoning=5, adtv_window=21)
        primeiro_pos_buraco = pd.Timestamp("2024-03-01")
        assert not m.loc[primeiro_pos_buraco, "FALH3"]  # ADTV ainda contaminado pelos zeros

    def test_deslistagem_sai_mas_nao_apaga_o_passado(self):
        morta = _daily("MORT3", "2024-01-02", 70, 1e6)  # negocia até ~10/04 e some
        viva = _daily("VIVA3", "2024-01-02", 100, 1e6)
        m = universe_membership(
            _quotes(morta + viva), adtv_floor=0.0, ipo_seasoning=10, adtv_window=5
        )
        ultima = pd.Timestamp(morta[-1][0])
        assert m.loc[ultima, "MORT3"]  # no último pregão dela: dentro
        assert not m.loc[m.index > ultima, "MORT3"].any()  # depois: fora, para sempre
        assert m.loc[m.index <= ultima, "MORT3"].iloc[11:].all()  # o passado fica

    def test_whitelist_de_exposicao(self):
        rows = _daily("AAAA3", "2024-01-02", 30, 1e6) + _daily("BBBB3", "2024-01-02", 30, 1e6)
        m = universe_membership(
            _quotes(rows), adtv_floor=0.0, ipo_seasoning=5, adtv_window=5, tickers=["AAAA3"]
        )
        assert list(m.columns) == ["AAAA3"]

    def test_whitelist_sem_match_e_erro(self):
        with pytest.raises(ValueError, match="whitelist"):
            universe_membership(
                _quotes(_daily("AAAA3", "2024-01-02", 5, 1.0)),
                adtv_floor=0.0,
                tickers=["ZZZZ3"],
            )

    def test_piso_negativo_e_erro(self):
        with pytest.raises(ValueError, match="adtv_floor"):
            universe_membership(_quotes(_daily("AAAA3", "2024-01-02", 5, 1.0)), adtv_floor=-1)

    def test_cotacao_duplicada_explode(self):
        rows = [("2024-01-02", "DUPL3", 1.0), ("2024-01-02", "DUPL3", 2.0)]
        with pytest.raises(ValueError):
            universe_membership(_quotes(rows), adtv_floor=0.0)


class TestEligibleCount:
    def test_conta_deslistagem_e_ipo(self):
        antiga = _daily("ANTI3", "2024-01-02", 100, 1e6)
        morta = _daily("MORT3", "2024-01-02", 70, 1e6)
        m = universe_membership(
            _quotes(antiga + morta), adtv_floor=0.0, ipo_seasoning=10, adtv_window=5
        )
        n = eligible_count(m)
        assert n.iloc[5] == 0  # ninguém temperado ainda
        assert n.iloc[20] == 2  # as duas dentro
        assert n.iloc[-1] == 1  # MORT3 já deslistou


class TestManualEvents:
    def test_slc_tem_a_bonificacao_de_2023(self):
        from quantagro.ingest.events_manual import manual_events

        evs = manual_events("SLCE3")
        bonif = [e for e in evs if e.cum_date == pd.Timestamp("2023-05-08")]
        assert len(bonif) == 1
        assert bonif[0].share_ratio == pytest.approx(1.1)  # 1 nova para cada 10

    def test_ticker_sem_curadoria_e_lista_vazia(self):
        from quantagro.ingest.events_manual import manual_events

        assert manual_events("XXXX3") == []

    @pytest.mark.parametrize(
        "ticker,cum_date",
        [("VITT3", "2024-04-12"), ("KLBN11", "2024-05-06")],
    )
    def test_bonificacoes_encontradas_na_auditoria_final(self, ticker, cum_date):
        from quantagro.ingest.events_manual import manual_events

        events = manual_events(ticker)
        assert len(events) == 1
        assert events[0].cum_date == pd.Timestamp(cum_date)
        assert events[0].share_ratio == pytest.approx(1.1)

    def test_devolve_copia_nao_o_registro(self):
        from quantagro.ingest.events_manual import manual_events

        manual_events("SLCE3").clear()
        assert manual_events("SLCE3")  # o registro interno não foi esvaziado
