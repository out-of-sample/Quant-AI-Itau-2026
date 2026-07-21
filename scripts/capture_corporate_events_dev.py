"""Congela eventos corporativos até 2019 para a montagem offline dos retornos dev."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, "src")
from quantagro.ingest.events_b3 import (  # noqa: E402
    fetch_b3_cash_dividends,
    fetch_b3_stock_events,
)
from quantagro.ingest.events_snapshot import (  # noqa: E402
    make_snapshot,
    ticker_snapshot,
    write_snapshot,
)
from quantagro.ingest.events_statusinvest import fetch_statusinvest_proventos  # noqa: E402

OUT = Path("data/reference/corporate_events_dev_v1.json")
STAGING = Path("data/raw/corporate_events_dev_capture")
CUTOFF = "2019-12-31"
NAMES = {
    "AGRO3": ("BRASILAGRO", "AGRO"),
    "SLCE3": ("SLC AGRICOLA", "SLCE"),
    "BRFS3": ("BRF SA", "BRFS"),
    "JBSS3": ("JBS", "JBSS"),
    "SMTO3": ("SAO MARTINHO", "SMTO"),
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _retry(fn, what: str, tries: int = 6):
    for attempt in range(tries):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - fonte pública tem rate-limit transitório
            if attempt == tries - 1:
                raise
            print(f"retry {what} ({attempt + 1}/{tries}): {type(exc).__name__}", flush=True)
            time.sleep(4 * (attempt + 1))
    raise RuntimeError("retry terminou sem retorno")  # pragma: no cover


def _cache_path(ticker: str, source: str) -> Path:
    return STAGING / f"{ticker}_{source}.json"


def _capture_source(ticker: str, source: str, query: str, fn) -> tuple[list[dict], str]:
    """Persiste cada resposta separadamente para uma captura retomável e auditável."""
    path = _cache_path(ticker, source)
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("query") == query:
            print(f"cache {ticker}/{source}: {len(payload['rows'])} linhas", flush=True)
            return payload["rows"], payload["retrieved_at"]
        print(f"cache inválido {ticker}/{source}: consulta mudou", flush=True)

    rows = _retry(fn, f"{ticker}/{source}")
    retrieved_at = _utc_now()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"query": query, "retrieved_at": retrieved_at, "rows": rows},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"capturado {ticker}/{source}: {len(rows)} linhas", flush=True)
    return rows, retrieved_at


def _capture_ticker(ticker: str) -> None:
    trading_name, issuing_company = NAMES[ticker]
    sources = {
        "b3_cash": (trading_name, lambda: fetch_b3_cash_dividends(trading_name)),
        "b3_stock": (issuing_company, lambda: fetch_b3_stock_events(issuing_company)),
        "statusinvest_cash": (ticker, lambda: fetch_statusinvest_proventos(ticker)),
    }
    for source, (query, fn) in sources.items():
        _capture_source(ticker, source, query, fn)
        time.sleep(2)


def _load_ticker(ticker: str) -> dict[str, object] | None:
    cached: dict[str, tuple[list[dict], str]] = {}
    for source in ("b3_cash", "b3_stock", "statusinvest_cash"):
        path = _cache_path(ticker, source)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        expected_query = {
            "b3_cash": NAMES[ticker][0],
            "b3_stock": NAMES[ticker][1],
            "statusinvest_cash": ticker,
        }[source]
        if payload.get("query") != expected_query:
            return None
        cached[source] = payload["rows"], payload["retrieved_at"]

    trading_name, issuing_company = NAMES[ticker]
    return ticker_snapshot(
        ticker=ticker,
        trading_name=trading_name,
        issuing_company=issuing_company,
        b3_cash_rows=cached["b3_cash"][0],
        b3_stock_rows=cached["b3_stock"][0],
        statusinvest_rows=cached["statusinvest_cash"][0],
        cutoff=CUTOFF,
        source_retrieved_at={source: item[1] for source, item in cached.items()},
    )


def _finalize() -> bool:
    captured = {ticker: _load_ticker(ticker) for ticker in NAMES}
    missing = [ticker for ticker, payload in captured.items() if payload is None]
    if missing:
        print(f"snapshot ainda incompleto; faltam fontes de: {missing}", flush=True)
        return False
    complete = {ticker: payload for ticker, payload in captured.items() if payload is not None}
    write_snapshot(
        make_snapshot(complete, cutoff=CUTOFF, retrieved_at=_utc_now()),
        OUT,
    )
    print(f"snapshot congelado em {OUT}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", choices=sorted(NAMES), help="captura um ticker por vez")
    parser.add_argument(
        "--finalize",
        action="store_true",
        help="monta o snapshot apenas se todas as fontes existirem",
    )
    args = parser.parse_args()
    if not args.ticker and not args.finalize:
        parser.error("informe --ticker ou --finalize")
    if args.ticker:
        _capture_ticker(args.ticker)
    _finalize()


if __name__ == "__main__":
    main()
