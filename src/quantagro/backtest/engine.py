"""Motor diário da Fase 4.1, fiel aos contratos D-053/D-055/D-056.

O motor separa três objetos que não podem ser confundidos:

1. ``TargetSchedule`` materializa, em cada decisão, os scores operacionais e pesos-alvo;
2. os gates de investibilidade podem zerar um bloco inteiro antes de qualquer retorno;
3. ``run_backtest`` mantém quantidades de um índice de retorno total fixas dentro de cada
   bloco, marca o drift e só negocia nos closes previstos.

Uma posição aberta no close de ``X`` recebe os retornos em ``(X, saída]``. Na transição, o
último retorno pertence ao bloco antigo; depois dele ocorre uma única ordem líquida contra a
posição marcada. Não há ``ffill`` de pesos-alvo nem rebalanceamento diário implícito.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .operational_spec import (
    COST_SCENARIOS,
    HOLDING_SESSIONS,
    REFERENCE_AUM_BRL,
    TradeBlock,
    borrow_all_in_rate,
    compose_operational_scores,
    one_way_equity_cost_rate,
    require_backtest_scope,
)
from .strategy_spec import GRAIN_NAMES, PER_NAME_CAP, UNIVERSE, dollar_neutral_weights

_TRADING_DAYS_PER_YEAR = 252
_CANE_STATUSES = frozenset({"ok", "window_not_started"})


@dataclass(frozen=True)
class TargetSchedule:
    """Scores e pesos planejados em cada execução, sem consultar retornos."""

    blocks: tuple[TradeBlock, ...]
    operational_scores: pd.DataFrame
    target_weights: pd.DataFrame
    decisions: pd.DataFrame


@dataclass(frozen=True)
class BacktestResult:
    """Livro auditável do motor; valores monetários estão em reais."""

    scope: str
    scenario: str
    daily: pd.DataFrame
    attribution_brl: pd.DataFrame
    holdings_brl: pd.DataFrame
    weights: pd.DataFrame
    orders_brl: pd.DataFrame
    planned_targets: pd.DataFrame
    effective_targets: pd.DataFrame
    block_status: pd.DataFrame


def _datetime_frame(frame: pd.DataFrame, what: str) -> pd.DataFrame:
    out = frame.copy()
    out.index = pd.DatetimeIndex(out.index).normalize()
    if out.index.has_duplicates or not out.index.is_monotonic_increasing:
        raise ValueError(f"{what} deve ter datas crescentes e sem duplicatas")
    return out


def _require_dates(frame: pd.DataFrame, dates: pd.DatetimeIndex, what: str) -> None:
    missing = dates.difference(frame.index)
    if len(missing):
        raise ValueError(f"{what} sem {len(missing)} data(s) obrigatórias: {list(missing[:3])}")


def build_target_schedule(
    blocks: Sequence[TradeBlock],
    grain_raw_scores: pd.DataFrame,
    cane_signal: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    allow_holdout: bool = False,
) -> TargetSchedule:
    """Materializa scores e pesos-alvo por bloco sem ler preço ou retorno.

    ``grain_raw_scores`` contém ``E·Shock`` antes da inversão H′. ``NaN`` significa que o
    nome não possuía score/exposição válida naquela decisão e, portanto, não é elegível; valor
    infinito falha. ``cane_signal`` exige as colunas ``shock`` e ``status``. Somente
    ``window_not_started`` admite ``shock`` ausente — qualquer outro buraco falha alto.
    """
    frozen = tuple(blocks)
    require_backtest_scope(frozen, allow_holdout=allow_holdout)
    if not frozen:
        raise ValueError("agenda exige ao menos um bloco")

    grain = _datetime_frame(grain_raw_scores, "scores de grãos")
    cane = _datetime_frame(cane_signal, "sinal de cana")
    eligible = _datetime_frame(membership, "universo")
    if set(grain.columns) != set(GRAIN_NAMES):
        raise ValueError(f"scores de grãos exigem exatamente {list(GRAIN_NAMES)}")
    if set(cane.columns) != {"shock", "status"}:
        raise ValueError("sinal de cana exige exatamente as colunas shock e status")
    if not set(UNIVERSE).issubset(eligible.columns):
        raise ValueError("universo não contém todos os cinco nomes congelados")
    eligible = eligible.loc[:, list(UNIVERSE)]
    if eligible.isna().any().any() or not all(
        pd.api.types.is_bool_dtype(dtype) for dtype in eligible.dtypes
    ):
        raise ValueError("universo deve ser booleano e não pode conter ausências")

    decisions = pd.DatetimeIndex([block.decision_date for block in frozen])
    executions = pd.DatetimeIndex([block.execution_date for block in frozen], name="execution_date")
    if decisions.has_duplicates or executions.has_duplicates:
        raise ValueError("blocos não podem repetir decisão ou execução")
    _require_dates(grain, decisions, "scores de grãos")
    _require_dates(cane, decisions, "sinal de cana")
    _require_dates(eligible, decisions, "universo")

    op_rows: list[dict[str, float]] = []
    weight_rows: list[dict[str, float]] = []
    decision_rows: list[dict[str, object]] = []
    for block in frozen:
        date = block.decision_date
        raw_row = grain.loc[date]
        if np.isinf(raw_row.to_numpy(dtype=float, na_value=np.nan)).any():
            raise ValueError(f"score infinito em {date.date()}")
        market_eligible = eligible.columns[eligible.loc[date]].tolist()
        raw = {
            name: float(raw_row[name])
            for name in GRAIN_NAMES
            if name in market_eligible and pd.notna(raw_row[name])
        }

        status = str(cane.loc[date, "status"])
        if status not in _CANE_STATUSES:
            raise ValueError(f"status de cana inválido em {date.date()}: {status!r}")
        cane_value = cane.loc[date, "shock"]
        if status == "window_not_started":
            if pd.notna(cane_value):
                raise ValueError("cana window_not_started deve ter shock ausente")
            cane_shock = None
        else:
            if pd.isna(cane_value) or not np.isfinite(float(cane_value)):
                raise ValueError(f"Shock de cana ausente/não finito em {date.date()}")
            cane_shock = float(cane_value)

        scores = compose_operational_scores(raw, market_eligible, cane_shock)
        weights = dollar_neutral_weights(scores) if scores else {}
        op_rows.append({name: scores.get(name, np.nan) for name in UNIVERSE})
        weight_rows.append({name: weights.get(name, 0.0) for name in UNIVERSE})
        active = bool(weights) and not np.isclose(sum(abs(v) for v in weights.values()), 0.0)
        decision_rows.append(
            {
                "crop_year": block.crop_year,
                "sequence": block.sequence,
                "decision_date": date,
                "execution_date": block.execution_date,
                "exit_date": block.exit_date,
                "market_eligible": len(market_eligible),
                "scored_grains": len(raw),
                "cane_status": status,
                "status": "planned" if active else "flat_missing_economic_side",
            }
        )

    operational = pd.DataFrame(op_rows, index=executions, columns=UNIVERSE, dtype=float)
    targets = pd.DataFrame(weight_rows, index=executions, columns=UNIVERSE, dtype=float)
    _validate_targets(targets)
    metadata = pd.DataFrame(decision_rows).set_index("execution_date")
    metadata.index = pd.DatetimeIndex(metadata.index)
    return TargetSchedule(frozen, operational, targets, metadata)


def _validate_targets(targets: pd.DataFrame) -> None:
    values = targets.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("pesos-alvo devem ser finitos")
    if not np.allclose(values.sum(axis=1), 0.0, atol=1e-12):
        raise ValueError("pesos-alvo devem ser dollar-neutral")
    if (np.abs(values).sum(axis=1) > 1.0 + 1e-12).any():
        raise ValueError("pesos-alvo excedem bruto 1,0")
    caps = pd.Series(PER_NAME_CAP).loc[list(targets.columns)].to_numpy()
    if (np.abs(values) > caps + 1e-12).any():
        raise ValueError("peso-alvo excede cap por nome")


def _validated_panel(frame: pd.DataFrame, what: str, *, boolean: bool = False) -> pd.DataFrame:
    out = _datetime_frame(frame, what)
    if not set(UNIVERSE).issubset(out.columns):
        raise ValueError(f"{what} não contém todos os cinco nomes")
    out = out.loc[:, list(UNIVERSE)]
    if boolean:
        if out.isna().any().any() or not all(
            pd.api.types.is_bool_dtype(dtype) for dtype in out.dtypes
        ):
            raise ValueError(f"{what} deve ser booleano e completo")
    return out


def _effective_targets(
    schedule: TargetSchedule,
    borrow_rates: pd.DataFrame,
    borrow_available: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[pd.Timestamp, pd.Series]]:
    rates = _validated_panel(borrow_rates, "taxas de aluguel")
    available = _validated_panel(borrow_available, "disponibilidade de aluguel", boolean=True)
    decision_dates = pd.DatetimeIndex([b.decision_date for b in schedule.blocks])
    _require_dates(rates, decision_dates, "taxas de aluguel")
    _require_dates(available, decision_dates, "disponibilidade de aluguel")

    effective = schedule.target_weights.copy()
    status_rows = []
    block_rates: dict[pd.Timestamp, pd.Series] = {}
    for block in schedule.blocks:
        target = effective.loc[block.execution_date]
        shorts = target[target < -1e-15].index
        reason = str(schedule.decisions.loc[block.execution_date, "status"])
        if len(shorts):
            if not available.loc[block.decision_date, shorts].all():
                effective.loc[block.execution_date] = 0.0
                reason = "flat_borrow_unavailable"
                shorts = pd.Index([])
            else:
                observed = rates.loc[block.decision_date, shorts]
                if observed.isna().any() or not np.isfinite(observed.to_numpy(dtype=float)).all():
                    raise ValueError(f"taxa de aluguel inválida em {block.decision_date.date()}")
                if (observed < 0).any():
                    raise ValueError("taxa de aluguel observada não pode ser negativa")
        annual = pd.Series(0.0, index=UNIVERSE, dtype=float)
        for name in shorts:
            annual[name] = float(rates.loc[block.decision_date, name])
        block_rates[block.execution_date] = annual
        status_rows.append(
            {
                "crop_year": block.crop_year,
                "sequence": block.sequence,
                "decision_date": block.decision_date,
                "execution_date": block.execution_date,
                "exit_date": block.exit_date,
                "status": reason,
            }
        )
    return effective, pd.DataFrame(status_rows).set_index("execution_date"), block_rates


def _spot_trade(
    equity_before: float,
    holdings_before: np.ndarray,
    target: np.ndarray,
    adtv: np.ndarray,
    scenario: str,
) -> tuple[float, np.ndarray, np.ndarray, float]:
    """Resolve o patrimônio pós-custo para que os pesos pós-negociação sejam exatos."""
    if equity_before <= 0 or not np.isfinite(equity_before):
        raise ValueError("patrimônio pré-negociação deve ser positivo e finito")
    if not np.isfinite(holdings_before).all() or not np.isfinite(target).all():
        raise ValueError("posição e alvo devem ser finitos")

    def cost_for(equity_after: float) -> tuple[float, np.ndarray]:
        orders = target * equity_after - holdings_before
        cost = 0.0
        for order, liquidity in zip(orders, adtv, strict=True):
            if abs(order) <= 1e-12:
                continue
            if not np.isfinite(liquidity) or liquidity <= 0:
                raise ValueError("ordem exige ADTV positivo e finito")
            delta = float(order / equity_before)
            rate = one_way_equity_cost_rate(
                delta, float(liquidity), aum_brl=equity_before, scenario=scenario
            )
            cost += abs(float(order)) * rate
        return cost, orders

    if scenario == "zero":
        cost, orders = cost_for(equity_before)
        equity_after = equity_before
    else:
        lo, hi = 0.0, equity_before
        for _ in range(80):
            mid = (lo + hi) / 2.0
            cost, _ = cost_for(mid)
            residual = equity_before - cost - mid
            if residual > 0:
                lo = mid
            else:
                hi = mid
        equity_after = (lo + hi) / 2.0
        cost, orders = cost_for(equity_after)
        if not np.isclose(equity_after + cost, equity_before, rtol=0, atol=1e-7):
            raise RuntimeError("solver de custos não fechou a identidade contábil")
    holdings_after = target * equity_after
    return equity_after, holdings_after, orders, float(cost)


def _trade_asof(
    trade_date: pd.Timestamp,
    block_by_execution: Mapping[pd.Timestamp, TradeBlock],
    sessions: pd.DatetimeIndex,
) -> pd.Timestamp:
    block = block_by_execution.get(trade_date)
    if block is not None:
        return block.decision_date
    pos = int(sessions.get_loc(trade_date))
    if pos == 0:
        raise ValueError("saída final não possui pregão anterior para medir ADTV")
    return sessions[pos - 1]


def run_backtest(
    returns: pd.DataFrame,
    schedule: TargetSchedule,
    adtv_brl: pd.DataFrame,
    borrow_rates: pd.DataFrame,
    borrow_available: pd.DataFrame,
    *,
    scenario: str = "zero",
    initial_aum_brl: float = REFERENCE_AUM_BRL,
    allow_holdout: bool = False,
) -> BacktestResult:
    """Executa os blocos com quantidades fixas e ledger diário autoconsistente.

    O gate de escopo é a primeira operação. Para demonstrar que ele ocorre antes do I/O, o
    entrypoint ``run_backtest_from_parquet`` recebe um caminho e só o abre depois dessa trava.
    Taxas de aluguel são observadas em D, convertidas para ``a.a./252`` e mantidas fixas pelos
    21 intervalos. O cenário zero remove dinheiro, mas preserva disponibilidade e participação.
    """
    scope = require_backtest_scope(schedule.blocks, allow_holdout=allow_holdout)
    if scenario not in COST_SCENARIOS:
        raise ValueError(f"cenário de custo inválido: {scenario!r}")
    if not np.isfinite(initial_aum_brl) or initial_aum_brl <= 0:
        raise ValueError("patrimônio inicial deve ser positivo e finito")

    ret = _validated_panel(returns, "retornos")
    if not np.isfinite(ret.to_numpy(dtype=float, na_value=np.nan)[~ret.isna().to_numpy()]).all():
        raise ValueError("retorno infinito no painel")
    adtv = _validated_panel(adtv_brl, "ADTV")
    effective, block_status, block_rates = _effective_targets(
        schedule, borrow_rates, borrow_available
    )
    _validate_targets(effective)

    blocks = schedule.blocks
    for previous, current in zip(blocks, blocks[1:], strict=False):
        if current.execution_date < previous.exit_date:
            raise ValueError("blocos sobrepostos")
    required_boundaries = pd.DatetimeIndex(
        sorted({d for b in blocks for d in (b.execution_date, b.exit_date)})
    )
    _require_dates(ret, required_boundaries, "retornos")
    for block in blocks:
        left = int(ret.index.get_loc(block.execution_date))
        right = int(ret.index.get_loc(block.exit_date))
        if right - left != HOLDING_SESSIONS:
            raise ValueError(f"{block.crop_year}/{block.sequence} não contém 21 intervalos")

    block_by_execution = {b.execution_date: b for b in blocks}
    events: dict[pd.Timestamp, np.ndarray] = {
        b.execution_date: effective.loc[b.execution_date].to_numpy(dtype=float) for b in blocks
    }
    for block in blocks:
        if block.exit_date not in block_by_execution:
            events[block.exit_date] = np.zeros(len(UNIVERSE), dtype=float)

    first = min(events)
    last = max(events)
    sessions = ret.loc[first:last].index
    trade_asofs = pd.DatetimeIndex(
        [_trade_asof(date, block_by_execution, ret.index) for date in events]
    )
    _require_dates(adtv, trade_asofs, "ADTV")

    names = list(UNIVERSE)
    holdings = np.zeros(len(names), dtype=float)
    equity = float(initial_aum_brl)
    current_annual = np.zeros(len(names), dtype=float)
    current_block: TradeBlock | None = None
    daily_rows = []
    attribution_rows = []
    holding_rows = []
    weight_rows = []
    order_rows = []

    for date in sessions:
        equity_previous = equity
        return_block = current_block
        if date == first:
            gross_by_name = np.zeros(len(names), dtype=float)
            borrow = 0.0
        else:
            day_return = ret.loc[date].to_numpy(dtype=float)
            held = np.abs(holdings) > 1e-12
            if np.isnan(day_return[held]).any():
                missing = [names[i] for i in np.flatnonzero(held & np.isnan(day_return))]
                raise ValueError(
                    f"retorno ausente para posição mantida em {date.date()}: {missing}"
                )
            safe_return = np.where(held, day_return, 0.0)
            gross_by_name = holdings * safe_return
            daily_rates = (
                np.array(
                    [borrow_all_in_rate(rate, scenario) for rate in current_annual], dtype=float
                )
                / _TRADING_DAYS_PER_YEAR
            )
            borrow = float((np.maximum(-holdings, 0.0) * daily_rates).sum())
            holdings = holdings * (1.0 + safe_return)
            equity = equity + float(gross_by_name.sum()) - borrow
            if equity <= 0 or not np.isfinite(equity):
                raise ValueError("patrimônio ficou não positivo/não finito")

        spot_cost = 0.0
        orders = np.zeros(len(names), dtype=float)
        gross_turnover = 0.0
        if date in events:
            target = events[date]
            asof = _trade_asof(date, block_by_execution, ret.index)
            liquidity = adtv.loc[asof].to_numpy(dtype=float)
            pretrade_equity = equity
            equity, holdings, orders, spot_cost = _spot_trade(
                pretrade_equity, holdings, target, liquidity, scenario
            )
            gross_turnover = float(np.abs(orders).sum() / pretrade_equity)
            if date in block_by_execution:
                current_block = block_by_execution[date]
                observed = block_rates[date].to_numpy(dtype=float)
                current_annual = observed
            else:
                current_block = None
                current_annual = np.zeros(len(names), dtype=float)
            order_rows.append({"date": date} | dict(zip(names, orders, strict=True)))

        gross_pnl = float(gross_by_name.sum())
        net_pnl = equity - equity_previous
        if not np.isclose(net_pnl, gross_pnl - borrow - spot_cost, rtol=0, atol=1e-7):
            raise RuntimeError("identidade diária de P&L não fecha")
        weights = holdings / equity
        daily_rows.append(
            {
                "date": date,
                "return_crop_year": return_block.crop_year if return_block else pd.NA,
                "return_sequence": return_block.sequence if return_block else pd.NA,
                "post_trade_crop_year": current_block.crop_year if current_block else pd.NA,
                "post_trade_sequence": current_block.sequence if current_block else pd.NA,
                "gross_pnl_brl": gross_pnl,
                "borrow_cost_brl": borrow,
                "spot_cost_brl": spot_cost,
                "net_pnl_brl": net_pnl,
                "gross_return": gross_pnl / equity_previous,
                "net_return": net_pnl / equity_previous,
                "equity_brl": equity,
                "gross_exposure": float(np.abs(weights).sum()),
                "net_exposure": float(weights.sum()),
                "gross_traded": gross_turnover,
                "turnover_one_way": gross_turnover / 2.0,
            }
        )
        attribution_rows.append({"date": date} | dict(zip(names, gross_by_name, strict=True)))
        holding_rows.append({"date": date} | dict(zip(names, holdings, strict=True)))
        weight_rows.append({"date": date} | dict(zip(names, weights, strict=True)))

    def frame(rows: list[dict], *, columns: Sequence[str] | None = None) -> pd.DataFrame:
        out = pd.DataFrame(rows).set_index("date")
        out.index = pd.DatetimeIndex(out.index)
        return out.reindex(columns=columns) if columns is not None else out

    return BacktestResult(
        scope=scope,
        scenario=scenario,
        daily=frame(daily_rows),
        attribution_brl=frame(attribution_rows, columns=names),
        holdings_brl=frame(holding_rows, columns=names),
        weights=frame(weight_rows, columns=names),
        orders_brl=frame(order_rows, columns=names),
        planned_targets=schedule.target_weights.copy(),
        effective_targets=effective,
        block_status=block_status,
    )


def run_backtest_from_parquet(
    returns_path: str | Path,
    schedule: TargetSchedule,
    adtv_brl: pd.DataFrame,
    borrow_rates: pd.DataFrame,
    borrow_available: pd.DataFrame,
    **kwargs,
) -> BacktestResult:
    """Abre retornos somente depois de o gate dev/holdout autorizar a execução."""
    allow_holdout = bool(kwargs.get("allow_holdout", False))
    require_backtest_scope(schedule.blocks, allow_holdout=allow_holdout)
    returns = pd.read_parquet(returns_path)
    return run_backtest(
        returns,
        schedule,
        adtv_brl,
        borrow_rates,
        borrow_available,
        **kwargs,
    )
