"""Finaliza offline o snapshot de eventos corporativos do holdout até 2025.

Reusa exclusivamente as respostas brutas capturadas em 20/07/2026 e já usadas na auditoria
do desenvolvimento. Não consulta APIs e não lê preços ou retornos.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
from quantagro.ingest.events_snapshot import (  # noqa: E402
    make_snapshot,
    ticker_snapshot,
    write_snapshot,
)

OUT = Path("data/reference/corporate_events_holdout_v1.json")
STAGING = Path("data/raw/corporate_events_dev_capture")
CUTOFF = "2025-12-31"
NAMES = {
    "AGRO3": ("BRASILAGRO", "AGRO"),
    "SLCE3": ("SLC AGRICOLA", "SLCE"),
    "BRFS3": ("BRF SA", "BRFS"),
    "JBSS3": ("JBS", "JBSS"),
    "SMTO3": ("SAO MARTINHO", "SMTO"),
}
SOURCES = ("b3_cash", "b3_stock", "statusinvest_cash")


def _cached(ticker: str, source: str) -> dict:
    path = STAGING / f"{ticker}_{source}.json"
    if not path.is_file():
        raise FileNotFoundError(f"captura de evento ausente: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("rows"), list) or not str(
        payload.get("retrieved_at", "")
    ).endswith("Z"):
        raise ValueError(f"captura inválida: {path}")
    return payload


def build_snapshot() -> dict[str, object]:
    tickers = {}
    retrieved = []
    for ticker, (trading_name, issuing_company) in NAMES.items():
        cached = {source: _cached(ticker, source) for source in SOURCES}
        retrieved.extend(payload["retrieved_at"] for payload in cached.values())
        tickers[ticker] = ticker_snapshot(
            ticker=ticker,
            trading_name=trading_name,
            issuing_company=issuing_company,
            b3_cash_rows=cached["b3_cash"]["rows"],
            b3_stock_rows=cached["b3_stock"]["rows"],
            statusinvest_rows=cached["statusinvest_cash"]["rows"],
            cutoff=CUTOFF,
            source_retrieved_at={source: cached[source]["retrieved_at"] for source in SOURCES},
        )
    return make_snapshot(
        tickers,
        cutoff=CUTOFF,
        retrieved_at=max(retrieved),
        purpose="holdout_prices",
    )


def main() -> None:
    write_snapshot(build_snapshot(), OUT)
    print(f"snapshot holdout offline: {OUT}")


if __name__ == "__main__":
    main()
