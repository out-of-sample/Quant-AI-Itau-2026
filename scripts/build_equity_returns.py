"""Monta offline o retorno total diário PIT dos cinco nomes congelados até 2019.

O build nunca consulta APIs mutáveis: usa o snapshot versionado B3 + StatusInvest e a curadoria
primária. Um retorno absoluto de 30% sem explicação interrompe a execução, em vez de produzir
um painel potencialmente contaminado por split ausente.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from quantagro.ingest.cotahist import (  # noqa: E402
    download_cotahist,
    filter_equities_spot,
    parse_cotahist,
)
from quantagro.ingest.events_manual import manual_events  # noqa: E402
from quantagro.ingest.events_snapshot import (  # noqa: E402
    events_from_snapshot,
    load_snapshot,
)
from quantagro.prices.assemble import (  # noqa: E402
    assemble_total_return,
    close_series,
    flag_suspect_returns,
)

YEARS = range(2014, 2020)  # desenvolvimento (holdout 2020-2025 fica lacrado)
OUT = Path("data/interim/equity_returns_dev.parquet")
SNAPSHOT = Path("data/reference/corporate_events_dev_v1.json")
EXCEPTIONS = Path("data/reference/price_return_exceptions_v1.json")

NAMES = ("AGRO3", "SLCE3", "BRFS3", "JBSS3", "SMTO3")


def load_quotes() -> pd.DataFrame:
    frames = [filter_equities_spot(parse_cotahist(download_cotahist(f"A{y}"))) for y in YEARS]
    return pd.concat(frames, ignore_index=True)


def assemble_one(
    quotes: pd.DataFrame,
    snapshot: dict,
    ticker: str,
    allowed_extremes: dict[pd.Timestamp, tuple[float, float]],
) -> pd.Series:
    close = close_series(quotes, ticker)
    cash, cash_fallback, b3_stock = events_from_snapshot(snapshot, ticker)
    stock = b3_stock + manual_events(ticker)
    ret = assemble_total_return(
        close, cash_primary=cash, cash_fallback=cash_fallback, stock=stock
    ).dropna()
    print(
        f"  {ticker}: {len(close)} pregões {close.index.min().date()}..{close.index.max().date()} "
        f"| {len(cash)} div B3, {len(cash_fallback)} fallback, {len(stock)} ações "
        f"| ret {len(ret)}d, média {ret.mean():.5f}, vol {ret.std():.4f}",
        flush=True,
    )
    flagged = flag_suspect_returns(ret)  # já devolve só as linhas suspeitas (data→retorno)
    _validate_extremes(flagged, allowed_extremes, ticker)
    if len(flagged):
        print(f"    {ticker}: {len(flagged)} extremo(s) auditado(s) no registro de exceções")
    if len(ret) < 200:
        raise SystemExit(f"{ticker}: série curta demais ({len(ret)}d) — trading_name/issuing?")
    return ret.rename(ticker)


def _validate_extremes(
    flagged: pd.Series,
    allowed: dict[pd.Timestamp, tuple[float, float]],
    ticker: str,
) -> None:
    unused = set(allowed) - set(flagged.index)
    if unused:
        raise RuntimeError(
            f"{ticker}: exceções declaradas não aparecem no tripwire: {sorted(unused)}"
        )
    unexpected = flagged[~flagged.index.isin(allowed)]
    if len(unexpected):
        pares = [(d.date().isoformat(), round(float(v), 3)) for d, v in unexpected.items()]
        raise RuntimeError(
            f"{ticker}: {len(unexpected)} retorno(s) suspeito(s) (≥30%) em {pares}; "
            "evento corporativo ausente ou movimento extremo exige auditoria"
        )
    for date, observed in flagged.items():
        expected, tolerance = allowed[date]
        if not np.isclose(float(observed), expected, rtol=0, atol=tolerance):
            raise RuntimeError(
                f"{ticker}: extremo auditado mudou em {date.date()}: "
                f"observado={observed:.12f}, esperado={expected:.12f}±{tolerance}"
            )


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    snapshot = load_snapshot(SNAPSHOT)
    missing = sorted(set(NAMES) - set(snapshot["tickers"]))
    if missing:
        raise RuntimeError(f"snapshot de eventos incompleto: {missing}")
    exception_payload = json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    exceptions: dict[str, dict[pd.Timestamp, tuple[float, float]]] = {
        ticker: {
            pd.Timestamp(row["date"]): (
                float(row["expected_return"]),
                float(row["absolute_tolerance"]),
            )
            for row in exception_payload["exceptions"]
            if row["ticker"] == ticker
        }
        for ticker in NAMES
    }
    quotes = load_quotes()
    print(f"COTAHIST {YEARS.start}-{YEARS.stop - 1}: {len(quotes)} linhas de pregão", flush=True)
    series = {
        ticker: assemble_one(quotes, snapshot, ticker, exceptions[ticker]) for ticker in NAMES
    }
    panel = pd.DataFrame(series).sort_index()
    panel.index.name = "date"
    panel.to_parquet(OUT)
    print(f"\npainel de retornos: {panel.shape[0]} dias × {panel.shape[1]} nomes → {OUT}")
    print(f"cobertura por nome: { {c: int(panel[c].notna().sum()) for c in panel.columns} }")


if __name__ == "__main__":
    main()
