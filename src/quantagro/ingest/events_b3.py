"""Fetchers de eventos corporativos da B3, normalizados para `CorporateEvent`.

Duas portas da B3 (ver docs/02_DADOS.md §4.2.1 e D-013):
- `GetListedCashDividends` — eventos em **dinheiro** (dividendo/JCP/rendimento). Autoritativa,
  com data de deliberação e data-com. **Não cobre deslistados** (a StatusInvest preenche essa
  cauda, em outro módulo).
- `GetListedSupplementCompany` — eventos em **ações** (split/bonificação/grupamento), com o
  campo `factor`. ⚠️ trunca as listas (confirmado em SLC/VITT/KLABIN) e pode repetir o mesmo
  evento para ON, PN e UNIT. A normalização filtra a classe pelo marcador do ISIN e deduplica
  data/ratio; a completude continua sendo conferida externamente (02_DADOS §4.2.1).

Cuidados calibrados contra dados reais:
- `valueCash` vem em decimal brasileiro (vírgula) e é **por ação** quando `quotedPerShares == 1`
  (confirmado em SLC/PETROBRAS); ainda assim dividimos por `quotedPerShares` por segurança.
- `typeStock` distingue ON/PN — é preciso filtrar pela classe do próprio ticker, senão um
  dividendo de PN entraria num papel ON.
- a resposta traz **duplicatas** (visto em PETROBRAS) — normalizamos deduplicando.
- a data-com é `lastDatePriorEx`; registros sem ela (ex ainda não definido) são descartados.

Interpretação do `factor` dos eventos em ações — **validada contra o preço do COTAHIST**:
- `DESDOBRAMENTO`/`BONIFICACAO`: `factor` é % de ações novas ⇒ `ratio = 1 + factor/100`
  (SLC split 100 → 2,0×, confirmado: preço caiu 2,08×; WEG 100 → 2×; TOTVS 200 → 3×).
- `GRUPAMENTO`: `factor` é o próprio `ratio` (MGLU 0,10 → reverso 10:1, confirmado: preço
  saltou 9,96×). **Semântica diferente** dos anteriores — calibrada em um caso, marcada como a
  mais arriscada.
- `INCORPORACAO`/`RESGATE`/`CISAO`: eventos **terminais** (o papel deixa de existir ou vira
  outro) — **não** são `share_ratio` simples e são deixados para o montador tratar como fim de
  série; aqui são descartados.
"""

from __future__ import annotations

import base64
import json

import pandas as pd

from quantagro.prices.adjust import CorporateEvent

_PROXY = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/"
_CASH_URL = _PROXY + "GetListedCashDividends/"
_SUPPLEMENT_URL = _PROXY + "GetListedSupplementCompany/"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

# sufixo do ticker → classe (typeStock) da B3
_CLASS_BY_SUFFIX = {"3": "ON", "4": "PN", "5": "PNA", "6": "PNB", "11": "UNT"}
_ISIN_MARKER_BY_SUFFIX = {"3": "NOR", "4": "NPR", "5": "NPA", "6": "NPB", "11": "DAM"}

# labels de evento em ações → como o `factor` vira `share_ratio` (validado contra preço real)
_RATIO_ADD = {"DESDOBRAMENTO", "BONIFICACAO"}  # ratio = 1 + factor/100
_RATIO_DIRECT = {"GRUPAMENTO"}  # ratio = factor


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


def fetch_b3_stock_events(issuing_company: str, session=None, timeout: int = 30) -> list[dict]:
    """Busca os eventos em ações de uma empresa (por código, ex.: 'MGLU') no supplement da B3.

    Retorna a lista crua de `stockDividends` (split/bonificação/grupamento/incorporação/…).
    """
    payload = {"issuingCompany": issuing_company, "language": "pt-br"}
    enc = base64.b64encode(json.dumps(payload).encode()).decode()
    if session is None:
        import requests

        session = requests
    resp = session.get(_SUPPLEMENT_URL + enc, headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return []
    company = data[0] if isinstance(data, list) else data
    return company.get("stockDividends") or []


def _stock_ratio(label: str, factor: float) -> float | None:
    """`share_ratio` a partir do label + `factor`; None se não for um ratio simples.

    Interpretação validada contra o preço real do COTAHIST (ver docstring do módulo).
    """
    if label in _RATIO_ADD:
        return 1.0 + factor / 100.0
    if label in _RATIO_DIRECT:
        return factor
    return None  # INCORPORACAO/RESGATE/CISAO — terminal, tratado no montador


def b3_stock_to_events(
    stock_dividends: list[dict], ticker: str | None = None
) -> list[CorporateEvent]:
    """Normaliza os eventos em ações em `CorporateEvent` (só `share_ratio`, sem dinheiro).

    Quando ``ticker`` é informado, filtra o ISIN pela classe do papel (ON/PN/UNIT). Isso é
    obrigatório para companhias com várias classes: a B3 devolve uma linha por classe e,
    sem o filtro, o mesmo bônus seria multiplicado várias vezes. Registros idênticos também
    são deduplicados como segunda defesa.

    Descarta o que não é ratio simples (incorporação/resgate/cisão) e registros sem data-com.
    """
    marker = None
    if ticker is not None:
        suffix = ticker[4:]
        if suffix not in _ISIN_MARKER_BY_SUFFIX:
            raise ValueError(f"sufixo de classe não reconhecido no ticker {ticker!r}")
        marker = _ISIN_MARKER_BY_SUFFIX[suffix]
    seen: set[tuple[pd.Timestamp, float, str]] = set()
    events: list[CorporateEvent] = []
    for e in stock_dividends:
        isin = (e.get("assetIssued") or e.get("isinCode") or "").strip()
        if marker is not None and isin and marker not in isin:
            continue
        com = e.get("lastDatePrior")
        raw = e.get("factor")
        label = (e.get("label") or "").strip()
        if not com or not raw:
            continue
        ratio = _stock_ratio(label, _br_float(raw))
        if ratio is None:
            continue
        cum_date = pd.to_datetime(com, format="%d/%m/%Y")
        key = (cum_date, round(ratio, 12), label)
        if key in seen:
            continue
        seen.add(key)
        events.append(CorporateEvent(cum_date=cum_date, share_ratio=ratio))
    return events
