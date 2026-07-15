"""Fetchers de eventos corporativos da B3, normalizados para `CorporateEvent`.

Duas portas da B3 (ver docs/02_DADOS.md §4.2.1 e D-013):
- `GetListedCashDividends` — eventos em **dinheiro** (dividendo/JCP/rendimento). Autoritativa,
  com data de deliberação e data-com. **Não cobre deslistados** (a StatusInvest preenche essa
  cauda, em outro módulo).
- `GetListedSupplementCompany` — eventos em **ações** (split/bonificação/grupamento). Fica para
  o próximo passo.

Cuidados calibrados contra dados reais:
- `valueCash` vem em decimal brasileiro (vírgula) e é **por ação** quando `quotedPerShares == 1`
  (confirmado em SLC/PETROBRAS); ainda assim dividimos por `quotedPerShares` por segurança.
- `typeStock` distingue ON/PN — é preciso filtrar pela classe do próprio ticker, senão um
  dividendo de PN entraria num papel ON.
- a resposta traz **duplicatas** (visto em PETROBRAS) — normalizamos deduplicando.
- a data-com é `lastDatePriorEx`; registros sem ela (ex ainda não definido) são descartados.
"""

from __future__ import annotations

import base64
import json

import pandas as pd

from quantagro.prices.adjust import CorporateEvent

_CASH_URL = (
    "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/"
    "GetListedCashDividends/"
)
_HEADERS = {"User-Agent": "Mozilla/5.0"}

# sufixo do ticker → classe (typeStock) da B3
_CLASS_BY_SUFFIX = {"3": "ON", "4": "PN", "5": "PNA", "6": "PNB", "11": "UNT"}


def _br_float(s: str) -> float:
    """Converte decimal brasileiro ('1.234,56' → 1234.56)."""
    return float(s.strip().replace(".", "").replace(",", "."))


def _share_class(ticker: str) -> str:
    """Classe implícita no sufixo do ticker (SLCE3 → ON, ITSA4 → PN, BBSE11 → UNT).

    Tickers da B3 são sempre 4 letras + o número da classe, então o sufixo é `ticker[4:]`.
    """
    suffix = ticker[4:]
    if suffix not in _CLASS_BY_SUFFIX:
        raise ValueError(f"sufixo de classe não reconhecido no ticker {ticker!r}")
    return _CLASS_BY_SUFFIX[suffix]


def fetch_b3_cash_dividends(
    trading_name: str,
    session=None,
    page_size: int = 100,
    timeout: int = 30,
    max_pages: int = 50,
) -> list[dict]:
    """Busca os proventos em dinheiro de uma empresa (por `tradingName`) na B3, paginando.

    A API é paginada e **tem teto de `pageSize`** (~120; acima disso devolve vazio) — por isso
    o default é 100 e percorremos `totalPages` (ex.: PETROBRAS tem 337 eventos em 4 páginas).
    Retorna a lista crua de `results` acumulada. `session` permite injetar um cliente HTTP (ou
    fake em teste); por padrão usa `requests`.
    """
    if session is None:
        import requests

        session = requests
    results: list[dict] = []
    page = 1
    while page <= max_pages:
        payload = {
            "language": "pt-br",
            "pageNumber": page,
            "pageSize": page_size,
            "tradingName": trading_name,
        }
        enc = base64.b64encode(json.dumps(payload).encode()).decode()
        resp = session.get(_CASH_URL + enc, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        page_results = data.get("results") or []
        results.extend(page_results)
        total_pages = (data.get("page") or {}).get("totalPages") or 0
        if not page_results or page >= total_pages:
            break
        page += 1
    return results


def b3_cash_to_events(results: list[dict], ticker: str) -> list[CorporateEvent]:
    """Normaliza os `results` do B3 cash em `CorporateEvent` para um ticker específico.

    Filtra pela classe do ticker (ON/PN/…), descarta registros sem data-com, deduplica, e
    converte o valor para por-ação. Todos são eventos em dinheiro ⇒ `share_ratio = 1`.
    """
    want_class = _share_class(ticker)
    seen: set[tuple] = set()
    events: list[CorporateEvent] = []
    for r in results:
        if r.get("typeStock") != want_class:
            continue
        com = r.get("lastDatePriorEx")
        raw_value = r.get("valueCash")
        if not com or not raw_value:
            continue
        per_shares = int(r.get("quotedPerShares") or 1)
        value = _br_float(raw_value) / per_shares
        cum_date = pd.to_datetime(com, format="%d/%m/%Y")
        key = (cum_date, round(value, 10), r.get("corporateAction"))
        if key in seen:
            continue
        seen.add(key)
        events.append(CorporateEvent(cum_date=cum_date, cash_value=value))
    return events
