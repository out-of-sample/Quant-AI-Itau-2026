"""Snapshot reprodutível de eventos corporativos usados na série de preços.

Os endpoints B3/StatusInvest são mutáveis e a B3 trunca parte do histórico de eventos em
ações. O backtest, portanto, não consulta essas APIs durante a montagem: uma captura explícita
normaliza os eventos, limita-os à janela declarada e registra hashes da serialização JSON
canônica dos payloads interpretados.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from quantagro.prices.adjust import CorporateEvent

from .events_b3 import b3_cash_to_events, b3_stock_to_events
from .events_statusinvest import statusinvest_to_events

SCHEMA_VERSION = 1


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def _serialize(events: Sequence[CorporateEvent], cutoff: pd.Timestamp) -> list[dict[str, object]]:
    out = []
    for event in sorted(events, key=lambda item: item.cum_date):
        if event.cum_date.normalize() > cutoff:
            continue
        out.append(
            {
                "cum_date": event.cum_date.date().isoformat(),
                "cash_value": event.cash_value,
                "share_ratio": event.share_ratio,
            }
        )
    return out


def _deserialize(rows: Sequence[Mapping[str, object]]) -> list[CorporateEvent]:
    return [
        CorporateEvent(
            cum_date=pd.Timestamp(str(row["cum_date"])),
            cash_value=float(row["cash_value"]),
            share_ratio=float(row["share_ratio"]),
        )
        for row in rows
    ]


def ticker_snapshot(
    *,
    ticker: str,
    trading_name: str,
    issuing_company: str,
    b3_cash_rows: list[dict],
    b3_stock_rows: list[dict],
    statusinvest_rows: list[dict],
    cutoff: str | pd.Timestamp,
    source_retrieved_at: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Normaliza uma captura, preservando B3 e fallback sem somá-los indevidamente."""
    end = pd.Timestamp(cutoff).normalize()
    cash_b3 = b3_cash_to_events(b3_cash_rows, ticker)
    cash_si = statusinvest_to_events(statusinvest_rows)
    stock_b3 = b3_stock_to_events(b3_stock_rows, ticker)
    return {
        "ticker": ticker,
        "trading_name": trading_name,
        "issuing_company": issuing_company,
        "canonical_payload_sha256": {
            "b3_cash": _canonical_hash(b3_cash_rows),
            "b3_stock": _canonical_hash(b3_stock_rows),
            "statusinvest_cash": _canonical_hash(statusinvest_rows),
        },
        "raw_counts": {
            "b3_cash": len(b3_cash_rows),
            "b3_stock": len(b3_stock_rows),
            "statusinvest_cash": len(statusinvest_rows),
        },
        "source_retrieved_at": dict(sorted((source_retrieved_at or {}).items())),
        "cash_b3": _serialize(cash_b3, end),
        "cash_statusinvest": _serialize(cash_si, end),
        "stock_b3": _serialize(stock_b3, end),
    }


def make_snapshot(
    tickers: Mapping[str, Mapping[str, object]],
    *,
    cutoff: str | pd.Timestamp,
    retrieved_at: str,
) -> dict[str, object]:
    """Empacota capturas por ticker e valida a identidade declarada em cada uma."""
    end = pd.Timestamp(cutoff).normalize()
    if end.tz is not None:
        raise ValueError("cutoff deve ser uma data sem fuso")
    if not retrieved_at.endswith("Z"):
        raise ValueError("retrieved_at deve estar em UTC e terminar em Z")
    expected = set(tickers)
    observed = {str(payload.get("ticker")) for payload in tickers.values()}
    if expected != observed:
        raise ValueError("chaves e ticker interno do snapshot divergem")
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": {"end_date": end.date().isoformat(), "purpose": "development_prices"},
        "retrieved_at": retrieved_at,
        "sources": {
            "b3": "sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/",
            "statusinvest": "statusinvest.com.br/acao/companytickerprovents",
        },
        "tickers": dict(sorted(tickers.items())),
    }


def write_snapshot(snapshot: Mapping[str, object], path: str | Path) -> None:
    """Grava JSON canônico; a escrita só ocorre no comando explícito de captura."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_snapshot(path: str | Path) -> dict[str, Any]:
    """Carrega e valida a estrutura mínima do snapshot de produção."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("versão desconhecida do snapshot de eventos")
    if not isinstance(payload.get("tickers"), dict) or not payload["tickers"]:
        raise ValueError("snapshot sem tickers")
    return payload


def events_from_snapshot(
    snapshot: Mapping[str, object], ticker: str
) -> tuple[list[CorporateEvent], list[CorporateEvent], list[CorporateEvent]]:
    """Devolve B3 cash, fallback StatusInvest e eventos em ações, nesta ordem."""
    tickers = snapshot.get("tickers")
    if not isinstance(tickers, Mapping) or ticker not in tickers:
        raise KeyError(f"ticker ausente do snapshot: {ticker}")
    payload = tickers[ticker]
    if not isinstance(payload, Mapping):
        raise ValueError(f"payload inválido para {ticker}")
    return (
        _deserialize(payload.get("cash_b3", [])),
        _deserialize(payload.get("cash_statusinvest", [])),
        _deserialize(payload.get("stock_b3", [])),
    )
