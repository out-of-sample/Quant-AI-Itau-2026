"""Eventos terminais PIT que encerram um bloco sem trocar o universo congelado."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .strategy_spec import UNIVERSE

TERMINAL_EXIT_POLICY = "liquidate_entire_active_block_at_last_close"


def load_terminal_exits(path: str | Path) -> dict[str, pd.Timestamp]:
    """Valida o registro oficial e devolve ticker → último close negociável."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("schema de eventos terminais deve ser 1")
    if payload.get("purpose") != "point_in_time_terminal_exit_holdout":
        raise ValueError("registro terminal não pertence ao holdout")
    if payload.get("policy") != TERMINAL_EXIT_POLICY:
        raise ValueError("política de evento terminal diverge do contrato")
    rows = payload.get("events")
    if not isinstance(rows, list) or not rows:
        raise ValueError("registro terminal exige eventos")

    exits: dict[str, pd.Timestamp] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("evento terminal deve ser objeto")
        ticker = str(row.get("ticker", ""))
        if ticker not in UNIVERSE or ticker in exits:
            raise ValueError(f"ticker terminal inválido/duplicado: {ticker!r}")
        announced = pd.Timestamp(row["announcement_avail_date"]).normalize()
        last_trade = pd.Timestamp(row["last_trade_date"]).normalize()
        if announced.tz is not None or last_trade.tz is not None or announced > last_trade:
            raise ValueError(f"datas terminais inválidas para {ticker}")
        if not str(row.get("source", "")).strip() or not str(row.get("source_url", "")).startswith(
            "https://"
        ):
            raise ValueError(f"fonte terminal inválida para {ticker}")
        if not str(row.get("successor", "")).strip():
            raise ValueError(f"sucessor terminal ausente para {ticker}")
        exits[ticker] = last_trade
    return exits
