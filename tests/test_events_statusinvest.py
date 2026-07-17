"""Testes do fetcher de proventos da StatusInvest (cauda deslistada — D-013).

Duas fixtures de respostas reais (2026-07-16): SLC (mistura adj=True/False, usada também no
cross-check contra a fixture da B3) e JBS (a cauda deslistada de verdade: 22 eventos, 11 deles
pós-2019, que a API da B3 não tem). A regra crítica testada é a do campo `adj`: o valor usado
tem que ser o nominal da época (`sov`), nunca o reescrito pós-split (`v`).
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.events_statusinvest import (
    _br_float,
    fetch_statusinvest_proventos,
    statusinvest_to_events,
)

FIXTURE_SLC = Path(__file__).parent / "fixtures" / "statusinvest_slc.json"
FIXTURE_JBS = Path(__file__).parent / "fixtures" / "statusinvest_jbs.json"
FIXTURE_KLBN = Path(__file__).parent / "fixtures" / "statusinvest_klbn_installments.json"
FIXTURE_B3_SLC = Path(__file__).parent / "fixtures" / "b3_cash_slc.json"


@pytest.fixture
def slc_rows() -> list[dict]:
    return json.loads(FIXTURE_SLC.read_text(encoding="utf-8"))["assetEarningsModels"]


@pytest.fixture
def jbs_rows() -> list[dict]:
    return json.loads(FIXTURE_JBS.read_text(encoding="utf-8"))["assetEarningsModels"]


class TestNormalizacaoReal:
    def test_slc_gera_eventos_de_dinheiro(self, slc_rows):
        ev = statusinvest_to_events(slc_rows)
        assert len(ev) == len(slc_rows)  # nenhum registro real é descartado
        assert all(e.share_ratio == 1.0 for e in ev)
        assert all(e.cash_value > 0 for e in ev)

    def test_adj_true_usa_o_valor_original_sov(self, slc_rows):
        # dividendo de 29/04/2022: v=1,2131 (reescrito pós-split), sov=2,42614793 (nominal).
        ev = statusinvest_to_events(slc_rows)
        e = next(x for x in ev if x.cum_date == pd.Timestamp("2022-04-29"))
        assert e.cash_value == pytest.approx(2.42614793, rel=1e-8)

    def test_adj_false_usa_v(self, slc_rows):
        # JCP de 27/12/2023: adj=False, sov="-", v nominal.
        ev = statusinvest_to_events(slc_rows)
        e = next(x for x in ev if x.cum_date == pd.Timestamp("2023-12-27"))
        assert e.cash_value == pytest.approx(0.05452740721, rel=1e-8)

    def test_jbs_cobre_a_cauda_pos_2019(self, jbs_rows):
        # a razão de existir desta fonte: a B3 congela JBS em 2019.
        ev = statusinvest_to_events(jbs_rows)
        pos_2019 = [e for e in ev if e.cum_date >= pd.Timestamp("2020-01-01")]
        assert len(pos_2019) == 11
        ultimo = max(ev, key=lambda e: e.cum_date)
        assert ultimo.cum_date == pd.Timestamp("2025-05-23")
        assert ultimo.cash_value == pytest.approx(1.0)

    def test_klabin_preserva_quatro_parcelas_iguais(self):
        rows = json.loads(FIXTURE_KLBN.read_text(encoding="utf-8"))["assetEarningsModels"]
        events = statusinvest_to_events(rows)
        assert len(events) == 4
        assert sum(e.cash_value for e in events) == pytest.approx(0.91194344496)


class TestCrossCheckContraB3:
    """Onde as duas fontes se sobrepõem (SLC), os nominais têm que bater.

    Tolerância 5e-4: a StatusInvest reconstrói o nominal multiplicando o valor ajustado pelo
    fator do split, com arredondamento — pior caso observado 3,9e-4 (dividendo de 04/05/2023).
    """

    def test_valores_batem_na_sobreposicao(self, slc_rows):
        b3_raw = json.loads(FIXTURE_B3_SLC.read_text(encoding="utf-8"))["results"]
        si_ev = statusinvest_to_events(slc_rows)
        si_por_data: dict[pd.Timestamp, list[float]] = {}
        for e in si_ev:
            si_por_data.setdefault(e.cum_date, []).append(e.cash_value)

        conferidos = 0
        for r in b3_raw:
            com = pd.to_datetime(r["lastDatePriorEx"], format="%d/%m/%Y")
            if com not in si_por_data:
                continue
            v_b3 = _br_float(r["valueCash"])
            v_si = min(si_por_data[com], key=lambda v: abs(v - v_b3))
            assert v_si == pytest.approx(v_b3, rel=5e-4), f"divergência em {com.date()}"
            conferidos += 1
        assert conferidos >= 8  # a sobreposição inteira da fixture foi de fato conferida


class TestNormalizacaoForjada:
    def _reg(self, ed="12/12/2025", v=1.0, sov="-", adj=False, et="Dividendo"):
        return {
            "ed": ed,
            "pd": "23/12/2025",
            "et": et,
            "etd": et,
            "v": v,
            "sv": "x",
            "sov": sov,
            "adj": adj,
        }

    def test_descarta_sem_data_com(self):
        assert statusinvest_to_events([self._reg(ed=None)]) == []
        assert statusinvest_to_events([self._reg(ed="")]) == []

    def test_adj_sem_sov_e_erro_alto_e_claro(self):
        # deixar passar usaria o valor reescrito pós-split — corrupção silenciosa do fator.
        with pytest.raises(ValueError, match="adj=True sem valor original"):
            statusinvest_to_events([self._reg(adj=True, sov="-")])

    def test_preserva_registros_identicos_sem_id_do_direito(self):
        ev = statusinvest_to_events([self._reg(), self._reg()])
        assert len(ev) == 2

    def test_valor_zero_ou_ausente_descartado(self):
        assert statusinvest_to_events([self._reg(v=0.0)]) == []
        assert statusinvest_to_events([self._reg(v=None)]) == []

    def test_sov_decimal_brasileiro(self):
        ev = statusinvest_to_events([self._reg(adj=True, sov="2,59718105")])
        assert ev[0].cash_value == pytest.approx(2.59718105)


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload):
        self._payload = payload
        self.last_kwargs = None

    def get(self, url, params=None, headers=None, timeout=None):
        self.last_kwargs = {"url": url, "params": params, "headers": headers}
        return _FakeResp(self._payload)


class TestFetch:
    def test_fetch_devolve_a_lista_de_eventos(self, jbs_rows):
        sess = _FakeSession({"assetEarningsModels": jbs_rows})
        out = fetch_statusinvest_proventos("JBSS3", session=sess)
        assert out == jbs_rows
        assert sess.last_kwargs["params"] == {"ticker": "JBSS3", "chartProventsType": 2}
        # o endpoint recusa requisição sem cara de browser
        assert "User-Agent" in sess.last_kwargs["headers"]
        assert sess.last_kwargs["headers"]["Referer"].endswith("/acoes/jbss3")

    def test_resposta_sem_eventos_vira_lista_vazia(self):
        sess = _FakeSession({"assetEarningsModels": None})
        assert fetch_statusinvest_proventos("XXXX3", session=sess) == []
