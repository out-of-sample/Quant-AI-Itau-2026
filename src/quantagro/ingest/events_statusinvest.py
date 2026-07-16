"""Fetcher de proventos em dinheiro da StatusInvest, normalizados para `CorporateEvent`.

Papel desta fonte (D-013, docs/02_DADOS.md §4.2.1): **preencher a cauda deslistada** que a API
oficial da B3 não cobre — JBSS3 pós-2019, BRFS3 e STBP3. Onde a B3 cobre, ela é a primária e
esta fonte serve só de cross-check.

Calibrações contra dados reais (verificação ao vivo em 2026-07-16):

- Endpoint: ``GET statusinvest.com.br/acao/companytickerprovents?ticker=X&chartProventsType=2``,
  exige headers de browser (User-Agent + Referer). Resposta única, sem paginação; a lista de
  eventos vem em ``assetEarningsModels``.
- Campos por registro: ``ed`` (data-com — verificado idêntico ao `lastDatePriorEx` da B3),
  ``pd`` (pagamento), ``et``/``etd`` (tipo: Dividendo / JCP / Amortização — todos em dinheiro),
  ``v``/``sv`` (valor por ação, float/string), ``sov`` (string do valor **original**),
  ``adj`` (bool).
- **O gotcha do `adj`**: quando ``adj=True``, ``v``/``sv`` foram reescritos para a base
  pós-split (lookahead de reescrita!), e o valor **nominal da época** está em ``sov``.
  Quando ``adj=False``, ``sov`` vem como ``"-"`` e ``v`` já é o nominal.
  Regra: ``nominal = sov se adj senão v``. Misturar `v` ajustado com preço bruto do COTAHIST
  corromperia o fator de ajuste.
- **Cross-check contra a B3** (SLC, 8 registros sobrepostos): 7 batem exatos; 1 diverge
  3,9e-4 relativo (04/05/2023) porque a StatusInvest reconstrói o nominal multiplicando o
  valor ajustado pelo fator do split, com arredondamento. Tolerância de comparação: 5e-4.
- JCP vem **bruto** (sem IRRF), consistente com o `valueCash` da B3 — as duas fontes podem
  ser somadas sem ajuste de base.
"""

from __future__ import annotations

import pandas as pd

from quantagro.prices.adjust import CorporateEvent

_URL = "https://statusinvest.com.br/acao/companytickerprovents"


def _headers(ticker: str) -> dict[str, str]:
    """Headers de browser exigidos pelo endpoint (sem eles a resposta é 403/vazia)."""
    return {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Referer": f"https://statusinvest.com.br/acoes/{ticker.lower()}",
    }


def _br_float(s: str) -> float:
    """Converte decimal brasileiro ('1.234,56' → 1234.56)."""
    return float(s.strip().replace(".", "").replace(",", "."))


def fetch_statusinvest_proventos(ticker: str, session=None, timeout: int = 30) -> list[dict]:
    """Busca os proventos em dinheiro de um ticker na StatusInvest.

    Retorna a lista crua de ``assetEarningsModels``. Não há paginação — a resposta é única
    (verificado: STBP3 devolve os 50 eventos de uma vez). ``session`` permite injetar um
    cliente HTTP (ou fake em teste); por padrão usa ``requests``.
    """
    if session is None:
        import requests

        session = requests
    resp = session.get(
        _URL,
        params={"ticker": ticker, "chartProventsType": 2},
        headers=_headers(ticker),
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("assetEarningsModels") or []


def statusinvest_to_events(rows: list[dict]) -> list[CorporateEvent]:
    """Normaliza os registros da StatusInvest em `CorporateEvent` (dinheiro, `share_ratio=1`).

    O valor por ação usado é sempre o **nominal da época**: ``sov`` quando ``adj=True``,
    ``v`` caso contrário (ver docstring do módulo). Um registro com ``adj=True`` sem ``sov``
    utilizável é erro de dados e levanta ``ValueError`` — deixá-lo passar contaminaria a
    série com um valor reescrito, silenciosamente.

    Descarta registros sem data-com e deduplica por (data-com, valor, tipo).
    """
    seen: set[tuple] = set()
    events: list[CorporateEvent] = []
    for r in rows:
        com = r.get("ed")
        if not com:
            continue
        if r.get("adj"):
            sov = (r.get("sov") or "").strip()
            if not sov or sov == "-":
                raise ValueError(
                    f"registro StatusInvest com adj=True sem valor original (sov): {r!r}"
                )
            value = _br_float(sov)
        else:
            value = float(r.get("v") or 0.0)
        if value <= 0:
            continue
        cum_date = pd.to_datetime(com, format="%d/%m/%Y")
        key = (cum_date, round(value, 10), r.get("et"))
        if key in seen:
            continue
        seen.add(key)
        events.append(CorporateEvent(cum_date=cum_date, cash_value=value))
    return events
