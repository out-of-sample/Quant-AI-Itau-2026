"""Cross-check da série de retorno total montada contra o adjclose do Yahoo.

Validação obrigatória antes de congelar o dataset de preços de cada papel VIVO do universo
(papéis deslistados não existem no Yahoo — é a limitação declarada em D-013/D-016). O que
este script pega e o tripwire de |retorno| ≥ 30% não pega: bonificações pequenas ausentes
das fontes (caso real: bonificação de 10% da SLC em 05/2023, ausente da B3 e da StatusInvest,
divergência de 9,1% num único dia).

Uso:
    python scripts/crosscheck_yahoo.py TICKER "TRADING NAME" ISSUING ANO_INI ANO_FIM

    python scripts/crosscheck_yahoo.py SLCE3 "SLC AGRICOLA" SLCE 2023 2025

Interpretação: dias com diff acima do limiar são impressos para inspeção. Nem toda
divergência é buraco nosso — em dividendo grande o Yahoo usa fator multiplicativo
P_ex/(P_cum−div), que se afasta do retorno verdadeiro do acionista (P_ex+div)/P_cum
(nossa convenção, CRSP); ~1% de diff num dia de dividendo de ~10% é o Yahoo, não nós.
Divergência SEM provento conhecido no dia = investigar de verdade.

Este script é ferramenta de validação, roda manualmente e fala com a rede; o pipeline de
backtest nunca depende dele.
"""

from __future__ import annotations

import json
import sys
import urllib.request

import pandas as pd

from quantagro.ingest.cotahist import download_cotahist, filter_equities_spot, parse_cotahist
from quantagro.ingest.events_b3 import (
    b3_cash_to_events,
    b3_stock_to_events,
    fetch_b3_cash_dividends,
    fetch_b3_stock_events,
)
from quantagro.ingest.events_manual import manual_events
from quantagro.prices.assemble import assemble_total_return, close_series

THRESHOLD = 5e-3


def yahoo_adjclose(symbol: str, start: str, end: str) -> pd.Series:
    p1 = int(pd.Timestamp(start).timestamp())
    p2 = int(pd.Timestamp(end).timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?period1={p1}&period2={p2}&interval=1d&events=div%2Csplit"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    res = data["chart"]["result"][0]
    ts = (
        pd.to_datetime(res["timestamp"], unit="s", utc=True)
        .tz_convert("America/Sao_Paulo")
        .normalize()
        .tz_localize(None)
    )
    adj = res["indicators"]["adjclose"][0]["adjclose"]
    return pd.Series(adj, index=ts).dropna()


def main() -> int:
    ticker, trading_name, issuing, ano_ini, ano_fim = sys.argv[1:6]
    frames = []
    for ano in range(int(ano_ini), int(ano_fim) + 1):
        path = download_cotahist(f"A{ano}")
        frames.append(filter_equities_spot(parse_cotahist(path)))
    quotes = pd.concat(frames, ignore_index=True)

    close = close_series(quotes, ticker)
    cash = b3_cash_to_events(fetch_b3_cash_dividends(trading_name), ticker)
    stock = b3_stock_to_events(fetch_b3_stock_events(issuing)) + manual_events(ticker)
    nosso = assemble_total_return(close, cash_primary=cash, stock=stock).dropna()

    ya = yahoo_adjclose(f"{ticker}.SA", f"{ano_ini}-01-01", f"{int(ano_fim) + 1}-01-01")
    deles = ya.pct_change().dropna()
    comum = nosso.index.intersection(deles.index)
    d = (nosso.loc[comum] - deles.loc[comum]).abs()

    print(f"{ticker}: {len(comum)} pregões | {len(cash)} cash, {len(stock)} stock (c/ manuais)")
    print(f"diff médio {d.mean():.2e} | p99 {d.quantile(0.99):.2e} | max {d.max():.2e}")
    suspeitos = d[d > THRESHOLD]
    if suspeitos.empty:
        print(f"nenhum dia acima de {THRESHOLD:.0e} — série consistente com o Yahoo")
        return 0
    print(f"dias acima de {THRESHOLD:.0e} (inspecionar um a um):")
    for dt in suspeitos.index:
        print(f"  {dt.date()}: nosso {nosso.loc[dt]:+.4f} vs yahoo {deles.loc[dt]:+.4f}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
