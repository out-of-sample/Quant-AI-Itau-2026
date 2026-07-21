"""Materializa ADTV e universo PIT dos cinco nomes no desenvolvimento (2014–2019)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from quantagro.backtest.operational_spec import (  # noqa: E402
    ADTV_FLOOR_BRL,
    ADTV_WINDOW,
    build_trade_blocks,
)
from quantagro.backtest.strategy_spec import UNIVERSE  # noqa: E402
from quantagro.ingest.cotahist import (  # noqa: E402
    download_cotahist,
    filter_equities_spot,
    parse_cotahist,
)
from quantagro.validate.universe import universe_state  # noqa: E402

YEARS = range(2014, 2020)
OUT = Path("data/interim/market_state_dev.parquet")
SUMMARY_OUT = Path("data/reference/market_state_dev_summary_v1.json")
IPO_SEASONING = 60


def load_quotes() -> pd.DataFrame:
    frames = [filter_equities_spot(parse_cotahist(download_cotahist(f"A{y}"))) for y in YEARS]
    return pd.concat(frames, ignore_index=True)


def build_long_state(quotes: pd.DataFrame) -> pd.DataFrame:
    """Converte os painéis auditáveis para uma tabela longa sem perder reason codes."""
    state = universe_state(
        quotes,
        adtv_floor=ADTV_FLOOR_BRL,
        ipo_seasoning=IPO_SEASONING,
        adtv_window=ADTV_WINDOW,
        tickers=list(UNIVERSE),
    )
    frames = {
        "traded": state.traded,
        "seasoned": state.seasoned,
        "adtv_brl": state.adtv_brl,
        "eligible": state.eligible,
        "reason": state.reason,
    }
    columns = {}
    for name, frame in frames.items():
        melted = (
            frame.rename_axis(index="date", columns="ticker")
            .reset_index()
            .melt(id_vars="date", var_name="ticker", value_name=name)
        )
        columns[name] = melted.set_index(["date", "ticker"])[name]
    long = pd.concat(columns, axis=1).reset_index()
    return long.sort_values(["date", "ticker"], ignore_index=True)


def build_summary(state: pd.DataFrame) -> dict[str, object]:
    sessions = pd.DatetimeIndex(state["date"].unique()).sort_values()
    blocks = build_trade_blocks(sessions, "2018/19")
    decisions = []
    for block in blocks:
        selected = state[state["date"].eq(block.decision_date)].set_index("ticker")
        decisions.append(
            {
                "sequence": block.sequence,
                "decision_date": block.decision_date.date().isoformat(),
                "execution_date": block.execution_date.date().isoformat(),
                "exit_date": block.exit_date.date().isoformat(),
                "eligible": {ticker: bool(selected.loc[ticker, "eligible"]) for ticker in UNIVERSE},
                "adtv_brl": {
                    ticker: float(selected.loc[ticker, "adtv_brl"]) for ticker in UNIVERSE
                },
            }
        )
    coverage = {}
    for ticker in UNIVERSE:
        selected = state[state["ticker"].eq(ticker)]
        coverage[ticker] = {
            "rows": len(selected),
            "traded_sessions": int(selected["traded"].sum()),
            "eligible_sessions": int(selected["eligible"].sum()),
        }
    manifests = {}
    for year in YEARS:
        payload = json.loads(
            Path(f"data/manifests/cotahist_A{year}.json").read_text(encoding="utf-8")
        )
        manifests[f"A{year}"] = payload["sha256"]
    return {
        "schema_version": 1,
        "scope": {
            "start": "2014-01-01",
            "end": "2019-12-31",
            "crop_year": "2018/19",
            "calendar_sessions": len(sessions),
        },
        "parameters": {
            "adtv_floor_brl": ADTV_FLOOR_BRL,
            "adtv_window_sessions": ADTV_WINDOW,
            "ipo_seasoning_sessions": IPO_SEASONING,
        },
        "cotahist_sha256": manifests,
        "coverage": coverage,
        "trade_blocks": decisions,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    state = build_long_state(load_quotes())
    state.to_parquet(OUT, index=False)
    summary_payload = build_summary(state)
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = state.groupby("ticker")["eligible"].agg(["sum", "count"])
    print(f"estado de mercado: {len(state)} linhas → {OUT}")
    print(f"resumo auditável → {SUMMARY_OUT}")
    print(summary.to_string())


if __name__ == "__main__":
    main()
