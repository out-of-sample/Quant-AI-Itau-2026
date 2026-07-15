"""Testes dos fetchers de eventos da B3 (dinheiro).

O parse de JSON real é amarrado por um fixture (resposta real do B3 cash para SLC AGRICOLA);
a lógica de normalização (filtro de classe ON/PN, dedupe, descarte sem data-com) é testada com
casos forjados, e o fetch com sessão fake, sem rede.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.events_b3 import (
    _br_float,
    _share_class,
    b3_cash_to_events,
    fetch_b3_cash_dividends,
)

FIXTURE = Path(__file__).parent / "fixtures" / "b3_cash_slc.json"


@pytest.fixture
def slc_results() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["results"]


class TestBrFloat:
    @pytest.mark.parametrize(
        "s,val",
        [("0,86051967", 0.86051967), ("1.234,56", 1234.56), ("2,00000000", 2.0)],
    )
    def test_decimal_brasileiro(self, s, val):
        assert _br_float(s) == pytest.approx(val)


class TestShareClass:
    @pytest.mark.parametrize("ticker,cls", [("SLCE3", "ON"), ("ITSA4", "PN"), ("BBSE11", "UNT")])
    def test_mapeia_sufixo(self, ticker, cls):
        assert _share_class(ticker) == cls

    def test_sufixo_desconhecido_falha(self):
        with pytest.raises(ValueError, match="classe"):
            _share_class("SLCE9")


class TestNormalizacaoReal:
    def test_slc_gera_eventos_de_dinheiro(self, slc_results):
        ev = b3_cash_to_events(slc_results, "SLCE3")
        assert len(ev) >= 1
        assert all(e.share_ratio == 1.0 for e in ev)  # dinheiro não mexe em quantidade
        assert all(e.cash_value > 0 for e in ev)

    def test_primeiro_evento_bate_com_o_real(self, slc_results):
        ev = b3_cash_to_events(slc_results, "SLCE3")
        primeiro = next(e for e in ev if e.cum_date == pd.Timestamp("2025-12-12"))
        assert primeiro.cash_value == pytest.approx(0.86051967)


class TestNormalizacaoForjada:
    def _reg(self, typeStock="ON", com="12/12/2025", value="1,00", ca="DIVIDENDO"):
        return {
            "typeStock": typeStock,
            "lastDatePriorEx": com,
            "valueCash": value,
            "quotedPerShares": "1",
            "corporateAction": ca,
        }

    def test_filtra_pela_classe_do_ticker(self):
        regs = [self._reg("ON", value="1,00"), self._reg("PN", value="2,00")]
        on = b3_cash_to_events(regs, "XXXX3")
        pn = b3_cash_to_events(regs, "XXXX4")
        assert [e.cash_value for e in on] == [pytest.approx(1.0)]
        assert [e.cash_value for e in pn] == [pytest.approx(2.0)]

    def test_deduplica_registros_identicos(self):
        regs = [self._reg(), self._reg()]  # a B3 às vezes repete
        assert len(b3_cash_to_events(regs, "XXXX3")) == 1

    def test_descarta_sem_data_com(self):
        regs = [self._reg(com=None), self._reg(com="")]
        assert b3_cash_to_events(regs, "XXXX3") == []

    def test_quoted_per_shares_divide(self):
        regs = [self._reg(value="10,00")]
        regs[0]["quotedPerShares"] = "1000"
        ev = b3_cash_to_events(regs, "XXXX3")
        assert ev[0].cash_value == pytest.approx(0.01)


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeSession:
    """Sessão fake de uma página só (totalPages=1)."""

    def __init__(self, results):
        self._results = results
        self.last_url = None

    def get(self, url, headers=None, timeout=None):
        self.last_url = url
        return _FakeResp({"page": {"totalPages": 1}, "results": self._results})


class _PagedSession:
    """Sessão fake que devolve `pages` (lista de listas de results), uma por pageNumber."""

    def __init__(self, pages):
        self._pages = pages
        self.calls = 0

    def get(self, url, headers=None, timeout=None):
        results = self._pages[self.calls] if self.calls < len(self._pages) else []
        self.calls += 1
        return _FakeResp({"page": {"totalPages": len(self._pages)}, "results": results})


class TestFetch:
    def test_fetch_retorna_results(self, slc_results):
        sess = _FakeSession(slc_results)
        out = fetch_b3_cash_dividends("SLC AGRICOLA", session=sess)
        assert out == slc_results
        assert sess.last_url.startswith("https://sistemaswebb3-listados.b3.com.br/")

    def test_fetch_sem_results(self):
        sess = _FakeSession([])
        assert fetch_b3_cash_dividends("INEXISTENTE", session=sess) == []

    def test_fetch_pagina_ate_o_fim(self):
        # 3 páginas de 2 registros cada → 6 acumulados, 3 chamadas.
        pages = [[{"a": 1}, {"a": 2}], [{"a": 3}, {"a": 4}], [{"a": 5}, {"a": 6}]]
        sess = _PagedSession(pages)
        out = fetch_b3_cash_dividends("MUITOS", session=sess, page_size=2)
        assert len(out) == 6
        assert sess.calls == 3

    def test_fetch_respeita_max_pages(self):
        pages = [[{"a": i}] for i in range(10)]  # totalPages=10, mas limitamos a 3
        sess = _PagedSession(pages)
        out = fetch_b3_cash_dividends("MUITOS", session=sess, page_size=1, max_pages=3)
        assert len(out) == 3
        assert sess.calls == 3
