"""Monta o retorno total diário PIT dos nomes diretos (Fase 3.2 — teste de reação das ações).

Reaproveita o motor de retorno total (D-014) e os fetchers de eventos (B3 + StatusInvest +
curadoria). Baixa/parseia o COTAHIST anual, monta a série de cada nome e grava um parquet em
``data/interim`` (gitignored). Roda uma vez; imprime diagnóstico por nome para pegar o "vazio
silencioso" da B3 (pageSize/trading_name errado devolve vazio com sucesso — P5).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from quantagro.ingest.cotahist import (  # noqa: E402
    download_cotahist,
    filter_equities_spot,
    parse_cotahist,
)
from quantagro.ingest.events_b3 import (  # noqa: E402
    b3_cash_to_events,
    b3_stock_to_events,
    fetch_b3_cash_dividends,
    fetch_b3_stock_events,
)
from quantagro.ingest.events_manual import manual_events  # noqa: E402
from quantagro.ingest.events_statusinvest import (  # noqa: E402
    fetch_statusinvest_proventos,
    statusinvest_to_events,
)
from quantagro.prices.assemble import (  # noqa: E402
    assemble_total_return,
    close_series,
    flag_suspect_returns,
)

YEARS = range(2014, 2020)  # desenvolvimento (holdout 2020-2025 fica lacrado)
OUT = Path("data/interim/equity_returns_dev.parquet")

# ticker -> (trading_name B3, issuingCompany B3). StatusInvest entra como fallback quando a B3
# devolve dinheiro vazio (caso BRFS3, P5). Os quatro nomes diretos de D-033.
NAMES = {
    "AGRO3": ("BRASILAGRO", "BRASILAGRO"),
    "SLCE3": ("SLC AGRICOLA", "SLC AGRICOLA"),
    "BRFS3": ("BRF SA", "BRF SA"),
    "JBSS3": ("JBS", "JBS"),
}


def load_quotes() -> pd.DataFrame:
    frames = [filter_equities_spot(parse_cotahist(download_cotahist(f"A{y}"))) for y in YEARS]
    return pd.concat(frames, ignore_index=True)


def _retry(fn, what: str, tries: int = 5):
    """Retenta um fetch ao vivo com backoff — endpoints B3 devolvem vazio/erro transitório."""
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - endpoint flakiness; re-raise na última tentativa
            if i == tries - 1:
                raise
            print(f"    retry {what} ({i + 1}/{tries}): {type(e).__name__}", flush=True)
            time.sleep(3 * (i + 1))
    return None


def assemble_one(quotes: pd.DataFrame, ticker: str, trading_name: str, issuing: str) -> pd.Series:
    close = close_series(quotes, ticker)
    cash = b3_cash_to_events(_retry(lambda: fetch_b3_cash_dividends(trading_name), "cash"), ticker)
    cash_fallback = (
        statusinvest_to_events(_retry(lambda: fetch_statusinvest_proventos(ticker), "si"))
        if not cash
        else []
    )
    # Eventos-ação (split/bonificação) são raros; o endpoint B3 anda com rate-limit. Se falhar,
    # cai para a curadoria manual e um tripwire de retorno suspeito pega qualquer split não
    # ajustado (aparece como salto de ~2×), em vez de seguir em silêncio.
    try:
        b3_stock = b3_stock_to_events(
            _retry(lambda: fetch_b3_stock_events(issuing), "stock", tries=2), ticker
        )
    except Exception as e:  # noqa: BLE001
        print(
            f"    AVISO {ticker}: eventos-ação B3 indisponíveis ({type(e).__name__}); só curadoria"
        )
        b3_stock = []
    stock = b3_stock + manual_events(ticker)
    ret = assemble_total_return(
        close, cash_primary=cash, cash_fallback=cash_fallback, stock=stock
    ).dropna()
    src = "B3" if cash else ("StatusInvest" if cash_fallback else "NENHUMA")
    print(
        f"  {ticker}: {len(close)} pregões {close.index.min().date()}..{close.index.max().date()} "
        f"| {len(cash)} div B3, {len(cash_fallback)} fallback ({src}), {len(stock)} ações "
        f"| ret {len(ret)}d, média {ret.mean():.5f}, vol {ret.std():.4f}",
        flush=True,
    )
    flagged = flag_suspect_returns(ret)  # já devolve só as linhas suspeitas (data→retorno)
    if len(flagged):
        pares = [(d.date().isoformat(), round(float(v), 3)) for d, v in flagged.items()]
        print(
            f"    AVISO {ticker}: {len(flagged)} retorno(s) suspeito(s) (≥30%) em {pares} "
            f"— verificar split não capturado"
        )
    if len(ret) < 200:
        raise SystemExit(f"{ticker}: série curta demais ({len(ret)}d) — trading_name/issuing?")
    return ret.rename(ticker)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    quotes = load_quotes()
    print(f"COTAHIST {YEARS.start}-{YEARS.stop - 1}: {len(quotes)} linhas de pregão", flush=True)
    series = {tk: assemble_one(quotes, tk, tn, iss) for tk, (tn, iss) in NAMES.items()}
    panel = pd.DataFrame(series).sort_index()
    panel.index.name = "date"
    panel.to_parquet(OUT)
    print(f"\npainel de retornos: {panel.shape[0]} dias × {panel.shape[1]} nomes → {OUT}")
    print(f"cobertura por nome: { {c: int(panel[c].notna().sum()) for c in panel.columns} }")


if __name__ == "__main__":
    main()
