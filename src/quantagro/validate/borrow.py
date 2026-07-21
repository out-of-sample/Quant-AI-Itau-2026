"""Estado auditável de aluguel por decisão, derivado de boletins B3 point-in-time."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from quantagro.ingest.borrow_b3 import verify_bdi_capture


@dataclass(frozen=True)
class BorrowState:
    """Painéis decisão × ticker consumidos pelo motor de backtest."""

    donor_rate: pd.DataFrame
    recent_trade: pd.DataFrame
    stock_brl: pd.DataFrame
    complete: pd.DataFrame
    reason: pd.DataFrame


@dataclass(frozen=True)
class BorrowFileCoverage:
    """Datas cuja completude foi atestada fora do painel por arquivo+manifesto+hash."""

    registered_ref_dates: frozenset[pd.Timestamp]
    open_position_ref_dates: frozenset[pd.Timestamp]
    _attested: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "registered_ref_dates",
            frozenset(pd.Timestamp(date).normalize() for date in self.registered_ref_dates),
        )
        object.__setattr__(
            self,
            "open_position_ref_dates",
            frozenset(pd.Timestamp(date).normalize() for date in self.open_position_ref_dates),
        )

    @classmethod
    def from_captures(
        cls,
        registered: Sequence[tuple[str | Path, str | Path]],
        open_positions: Sequence[tuple[str | Path, str | Path]],
    ) -> BorrowFileCoverage:
        """Cria cobertura somente após atestar CSV+manifesto das duas tabelas BDI."""
        registered_dates = tuple(
            verify_bdi_capture(data, manifest, "BTBLoanBalance") for data, manifest in registered
        )
        open_dates = tuple(
            verify_bdi_capture(data, manifest, "BTBLendingOpenPosition")
            for data, manifest in open_positions
        )
        if len(set(registered_dates)) != len(registered_dates):
            raise ValueError("capturas BTBLoanBalance repetem data de referência")
        if len(set(open_dates)) != len(open_dates):
            raise ValueError("capturas BTBLendingOpenPosition repetem data de referência")
        return cls(frozenset(registered_dates), frozenset(open_dates), _attested=True)


def _sessions_before(
    date: pd.Timestamp, sessions: pd.DatetimeIndex, count: int
) -> pd.DatetimeIndex:
    pos = int(sessions.searchsorted(date, side="left"))
    if pos < count:
        raise ValueError(f"calendário não cobre {count} pregões anteriores a {date.date()}")
    return sessions[pos - count : pos]


def _total_open_quantity(rows: pd.DataFrame, ticker: str, ref_date: pd.Timestamp) -> float:
    selected = rows[(rows["ref_date"] == ref_date) & (rows["ticker"] == ticker)]
    if selected.empty:
        return 0.0
    totals = selected[selected["is_total"]]
    if len(totals) != 1:
        raise ValueError(f"posição aberta de {ticker} em {ref_date.date()} exige uma linha Total")
    parts = selected[~selected["is_total"]]
    total = float(totals.iloc[0]["open_quantity"])
    if not np.isclose(float(parts["open_quantity"].sum()), total, rtol=0, atol=1):
        raise ValueError(f"modalidades não fecham com Total para {ticker} em {ref_date.date()}")
    return total


def build_borrow_state(
    registered: pd.DataFrame,
    open_positions: pd.DataFrame,
    close: pd.DataFrame,
    decision_dates: pd.DatetimeIndex,
    tickers: tuple[str, ...],
    coverage: BorrowFileCoverage,
    *,
    lookback_sessions: int = 5,
) -> BorrowState:
    """Constrói taxa, negócio recente e estoque marcado sem backfill temporal.

    Para uma decisão no close de D, somente boletins com ``avail_date <= D`` entram. Exige-se
    cobertura completa dos cinco pregões anteriores na tabela de negócios e do pregão D-1 na
    posição aberta. Ausência de ticker num arquivo completo significa estoque/negócio zero;
    ausência do próprio arquivo deixa ``complete=False`` e não pode virar disponibilidade.
    """
    required_registered = {
        "ref_date",
        "avail_date",
        "ticker",
        "contract_count",
        "asset_quantity",
        "donor_weighted_rate",
    }
    required_open = {"ref_date", "avail_date", "ticker", "open_quantity", "is_total"}
    if not required_registered.issubset(registered):
        raise ValueError("negócios registrados sem colunas canônicas")
    if not required_open.issubset(open_positions):
        raise ValueError("posições abertas sem colunas canônicas")
    if not coverage._attested:
        raise ValueError("cobertura de aluguel não foi atestada por arquivo+manifesto")

    prices = close.copy()
    prices.index = pd.DatetimeIndex(prices.index).normalize()
    sessions = prices.index.sort_values().unique()
    if prices.index.has_duplicates or not prices.index.is_monotonic_increasing:
        raise ValueError("fechamentos devem ter datas crescentes e sem duplicatas")
    if not set(tickers).issubset(prices.columns):
        raise ValueError("fechamentos não contêm todos os tickers do aluguel")

    reg = registered.copy()
    opened = open_positions.copy()
    for frame in (reg, opened):
        frame["ref_date"] = pd.to_datetime(frame["ref_date"]).dt.normalize()
        frame["avail_date"] = pd.to_datetime(frame["avail_date"]).dt.normalize()
    if not coverage.registered_ref_dates.issubset(set(reg["ref_date"].unique())):
        raise ValueError("cobertura registrada atesta arquivo sem linhas correspondentes")
    if not coverage.open_position_ref_dates.issubset(set(opened["ref_date"].unique())):
        raise ValueError("cobertura de posição atesta arquivo sem linhas correspondentes")

    decisions = pd.DatetimeIndex(decision_dates).normalize()
    if decisions.has_duplicates or not decisions.is_monotonic_increasing:
        raise ValueError("decisões devem ser crescentes e sem duplicatas")
    columns = list(tickers)
    rates = pd.DataFrame(np.nan, index=decisions, columns=columns, dtype=float)
    recent = pd.DataFrame(False, index=decisions, columns=columns, dtype=bool)
    stock = pd.DataFrame(np.nan, index=decisions, columns=columns, dtype=float)
    complete = pd.DataFrame(False, index=decisions, columns=columns, dtype=bool)
    reasons = pd.DataFrame("", index=decisions, columns=columns, dtype=object)

    for decision in decisions:
        prior = _sessions_before(decision, sessions, lookback_sessions)
        previous = prior[-1]
        reg_asof = reg[reg["avail_date"] <= decision]
        open_asof = opened[opened["avail_date"] <= decision]
        have_reg_dates = coverage.registered_ref_dates.intersection(
            set(reg_asof["ref_date"].unique())
        )
        have_open_dates = coverage.open_position_ref_dates.intersection(
            set(open_asof["ref_date"].unique())
        )
        files_complete = set(prior).issubset(have_reg_dates) and previous in have_open_dates

        for ticker in columns:
            if not files_complete:
                reasons.loc[decision, ticker] = "missing_bdi_files"
                continue
            price = prices.loc[decision, ticker]
            if pd.isna(price) or not np.isfinite(float(price)) or float(price) <= 0:
                raise ValueError(f"close inválido para {ticker} em {decision.date()}")
            quantity = _total_open_quantity(open_asof, ticker, previous)
            stock.loc[decision, ticker] = quantity * float(price)
            complete.loc[decision, ticker] = True

            trades = reg_asof[
                reg_asof["ref_date"].isin(prior)
                & reg_asof["ticker"].eq(ticker)
                & reg_asof["contract_count"].gt(0)
                & reg_asof["asset_quantity"].gt(0)
            ]
            if trades.empty:
                reasons.loc[decision, ticker] = "no_recent_trade"
                continue
            latest = trades["ref_date"].max()
            latest_rows = trades[trades["ref_date"] == latest]
            values = latest_rows["donor_weighted_rate"].to_numpy(dtype=float)
            quantities = latest_rows["asset_quantity"].to_numpy(dtype=float)
            if not np.isfinite(values).all() or (values < 0).any():
                raise ValueError(f"taxa doadora inválida para {ticker} em {latest.date()}")
            rates.loc[decision, ticker] = float(np.average(values, weights=quantities))
            recent.loc[decision, ticker] = True
            reasons.loc[decision, ticker] = "ok" if quantity > 0 else "zero_open_position"

    return BorrowState(rates, recent, stock, complete, reasons)
