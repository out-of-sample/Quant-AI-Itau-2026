"""Análises indivisíveis da rodada única do holdout.

O módulo concentra a transformação dos sete inputs lacrados nos blocos D-068. Ele não contém
qualquer comando de execução civil, escrita de resultado ou impressão: a orquestração atômica
fica em :mod:`quantagro.backtest.holdout_executor`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from quantagro.validate.borrow import BorrowState, build_proxy_borrow_state

from .diagnostics import (
    attribution_by_name,
    audit_agro3_liquidity,
    build_naive_sector_schedule,
    concentration_metrics,
    cost_monotonicity,
    sector_orthogonal_decomposition,
)
from .engine import BacktestResult, TargetSchedule, build_target_schedule, run_backtest
from .holdout_spec import (
    ADTV_SENSITIVITY_BRL,
    CANE_CAP_SENSITIVITY,
    GRAIN_CAP_SENSITIVITY,
    H4_ALPHA,
    H4_CORE_CONTROLS,
    H4_EXTENDED_CONTROLS,
    H4_HAC_LAGS,
    H4_RISK_FREE_COLUMN,
    H5_ALPHA,
    H5_MAX_ABS_RATIO,
    HOLDING_SENSITIVITY_SESSIONS,
    LOO_CROP_YEARS,
    LOO_NAMES,
    PORTFOLIO_PRIMARY_COST_SCENARIO,
    REQUIRED_INPUTS,
    TERMINAL_EVENTS,
    TOTAL_SIGNAL_LAG_SENSITIVITY_DAYS,
)
from .operational_spec import (
    ADTV_FLOOR_BRL,
    COST_SCENARIOS,
    HOLDING_SESSIONS,
    PROCESSORS,
    PRODUCERS,
    REFERENCE_AUM_BRL,
    TradeBlock,
    build_trade_blocks,
    exact_primary_signflip,
)
from .strategy_spec import (
    CANE_NAME,
    CANE_SATELLITE_CAP,
    GRAIN_NAME_CAP,
    GRAIN_NAMES,
    HOLDOUT_CROP_YEARS,
    PER_NAME_CAP,
    UNIVERSE,
)
from .terminal_events import load_terminal_exits


@dataclass(frozen=True)
class HoldoutInputs:
    """Inputs já validados pelos manifestos civil e de fontes."""

    returns: pd.DataFrame
    market_state: pd.DataFrame
    grain_scores: pd.DataFrame
    cane_signal: pd.DataFrame
    h4_controls: pd.DataFrame
    h5_geographic_scores: pd.DataFrame
    terminal_exits: dict[str, pd.Timestamp]


@dataclass(frozen=True)
class PortfolioRun:
    """Agenda e livro de uma variação single-knob."""

    schedule: TargetSchedule
    result: BacktestResult
    membership: pd.DataFrame
    blocks: tuple[TradeBlock, ...]


def _normalize_index(frame: pd.DataFrame, what: str) -> pd.DataFrame:
    out = frame.copy()
    out.index = pd.DatetimeIndex(out.index).normalize()
    if out.index.empty or out.index.has_duplicates or not out.index.is_monotonic_increasing:
        raise ValueError(f"{what} deve ter datas únicas e crescentes")
    return out


def load_holdout_inputs(root: str | Path = ".") -> HoldoutInputs:
    """Abre os parquets somente depois do gate civil do executor."""
    base = Path(root)
    returns = _normalize_index(
        pd.read_parquet(base / REQUIRED_INPUTS["returns"]), "retornos lacrados"
    )
    if list(returns.columns) != list(UNIVERSE):
        raise ValueError("retornos exigem exatamente os cinco nomes congelados")

    state = pd.read_parquet(base / REQUIRED_INPUTS["market_state"])
    required_state = {
        "date",
        "ticker",
        "traded",
        "seasoned",
        "adtv_brl",
        "eligible",
        "reason",
    }
    if set(state.columns) != required_state:
        raise ValueError("estado de mercado não possui o schema civil exato")
    state = state.copy()
    state["date"] = pd.to_datetime(state["date"]).dt.normalize()
    if state.duplicated(["date", "ticker"]).any():
        raise ValueError("estado de mercado repete data×ticker")
    if set(state["ticker"].unique()) != set(UNIVERSE):
        raise ValueError("estado de mercado não cobre o universo congelado")

    grain = pd.read_parquet(base / REQUIRED_INPUTS["grain_scores"])
    required_grain = {"decision_date", "total_signal_lag_days", *GRAIN_NAMES}
    if set(grain.columns) != required_grain:
        raise ValueError("scores de grãos não possuem o schema civil exato")
    grain = grain.copy()
    grain["decision_date"] = pd.to_datetime(grain["decision_date"]).dt.normalize()
    if grain.duplicated(["decision_date", "total_signal_lag_days"]).any():
        raise ValueError("scores de grãos repetem decisão×lag")

    cane = pd.read_parquet(base / REQUIRED_INPUTS["cane_signal"])
    required_cane = {"decision_date", "total_signal_lag_days", "shock", "status"}
    if set(cane.columns) != required_cane:
        raise ValueError("sinal de cana não possui o schema civil exato")
    cane = cane.copy()
    cane["decision_date"] = pd.to_datetime(cane["decision_date"]).dt.normalize()
    if cane.duplicated(["decision_date", "total_signal_lag_days"]).any():
        raise ValueError("sinal de cana repete decisão×lag")

    h4 = pd.read_parquet(base / REQUIRED_INPUTS["h4_controls"]).copy()
    h4["ref_date"] = pd.to_datetime(h4["ref_date"]).dt.normalize()
    h4["avail_date"] = pd.to_datetime(h4["avail_date"]).dt.normalize()
    h4 = h4.set_index("ref_date").sort_index()
    expected_h4 = {
        "avail_date",
        *H4_EXTENDED_CONTROLS,
        H4_RISK_FREE_COLUMN,
    }
    if set(h4.columns) != expected_h4 or h4.index.has_duplicates:
        raise ValueError("controles H4 não possuem o schema civil exato")

    h5 = _normalize_index(
        pd.read_parquet(base / REQUIRED_INPUTS["h5_geographic_scores"]),
        "scores geográficos H5",
    )
    if list(h5.columns) != list(GRAIN_NAMES):
        raise ValueError("H5 exige exatamente os quatro grãos congelados")

    terminal_exits = load_terminal_exits(base / TERMINAL_EVENTS)
    state_indexed = state.set_index(["date", "ticker"])
    for ticker, last_trade in terminal_exits.items():
        if last_trade not in returns.index or pd.isna(returns.loc[last_trade, ticker]):
            raise ValueError(f"retorno terminal ausente para {ticker}")
        if returns.loc[returns.index > last_trade, ticker].notna().any():
            raise ValueError(f"retorno de {ticker} continua após o evento terminal")
        if not bool(state_indexed.loc[(last_trade, ticker), "traded"]):
            raise ValueError(f"{ticker} não negocia no close terminal registrado")
        later_state = state[state["ticker"].eq(ticker) & state["date"].gt(last_trade)]
        if later_state["traded"].any():
            raise ValueError(f"{ticker} volta a negociar após o evento terminal")
    return HoldoutInputs(returns, state, grain, cane, h4, h5, terminal_exits)


def _wide(state: pd.DataFrame, column: str, dtype) -> pd.DataFrame:
    wide = state.pivot(index="date", columns="ticker", values=column).sort_index()  # noqa: PD010
    wide.index = pd.DatetimeIndex(wide.index)
    return wide.loc[:, list(UNIVERSE)].astype(dtype)


def _all_blocks(
    sessions: pd.DatetimeIndex, holding_sessions: int = HOLDING_SESSIONS
) -> tuple[TradeBlock, ...]:
    return tuple(
        block
        for crop_year in HOLDOUT_CROP_YEARS
        for block in build_trade_blocks(sessions, crop_year, holding_sessions=holding_sessions)
    )


def _select_scores(
    frame: pd.DataFrame,
    blocks: tuple[TradeBlock, ...],
    total_signal_lag_days: int,
    columns: list[str],
) -> pd.DataFrame:
    selected = frame[frame["total_signal_lag_days"].eq(total_signal_lag_days)].copy()
    selected = selected.set_index("decision_date").sort_index()
    decisions = pd.DatetimeIndex([block.decision_date for block in blocks])
    missing = decisions.difference(selected.index)
    if len(missing):
        raise ValueError(
            f"input de sinal sem {len(missing)} decisões para lag {total_signal_lag_days}"
        )
    return selected.loc[decisions, columns]


def _membership(
    inputs: HoldoutInputs,
    *,
    adtv_floor_brl: float,
    excluded_name: str | None = None,
) -> pd.DataFrame:
    traded = _wide(inputs.market_state, "traded", bool)
    seasoned = _wide(inputs.market_state, "seasoned", bool)
    adtv = _wide(inputs.market_state, "adtv_brl", float)
    membership = traded & seasoned & adtv.ge(float(adtv_floor_brl))
    if np.isclose(adtv_floor_brl, ADTV_FLOOR_BRL):
        frozen = _wide(inputs.market_state, "eligible", bool)
        if not membership.equals(frozen):
            raise ValueError("elegibilidade primária diverge do estado materializado")
    if excluded_name is not None:
        if excluded_name not in UNIVERSE:
            raise ValueError(f"nome LOO fora do universo: {excluded_name}")
        membership.loc[:, excluded_name] = False
    return membership


def _run_schedule(
    inputs: HoldoutInputs,
    schedule: TargetSchedule,
    membership: pd.DataFrame,
    *,
    scenario: str,
    holding_sessions: int,
) -> BacktestResult:
    adtv = _wide(inputs.market_state, "adtv_brl", float)
    traded = _wide(inputs.market_state, "traded", bool)
    decisions = pd.DatetimeIndex([block.decision_date for block in schedule.blocks])
    borrow: BorrowState = build_proxy_borrow_state(decisions, UNIVERSE, membership.loc[decisions])
    return run_backtest(
        inputs.returns,
        schedule,
        adtv,
        traded,
        borrow,
        scenario=scenario,
        allow_holdout=True,
        holding_sessions=holding_sessions,
        terminal_exits=inputs.terminal_exits,
    )


def run_portfolio_variant(
    inputs: HoldoutInputs,
    *,
    blocks: tuple[TradeBlock, ...] | None = None,
    holding_sessions: int = HOLDING_SESSIONS,
    total_signal_lag_days: int = 7,
    adtv_floor_brl: float = ADTV_FLOOR_BRL,
    caps: dict[str, float] | None = None,
    scenario: str = PORTFOLIO_PRIMARY_COST_SCENARIO,
    excluded_name: str | None = None,
    grain_override: pd.DataFrame | None = None,
) -> PortfolioRun:
    """Executa uma variação explicitamente congelada, com um botão por chamada."""
    sessions = pd.DatetimeIndex(inputs.returns.index)
    selected_blocks = _all_blocks(sessions, holding_sessions) if blocks is None else tuple(blocks)
    membership = _membership(inputs, adtv_floor_brl=adtv_floor_brl, excluded_name=excluded_name)
    if grain_override is None:
        grain = _select_scores(
            inputs.grain_scores,
            selected_blocks,
            total_signal_lag_days,
            list(GRAIN_NAMES),
        )
    else:
        grain = _normalize_index(grain_override, "override de grãos")
    cane = _select_scores(
        inputs.cane_signal,
        selected_blocks,
        total_signal_lag_days,
        ["shock", "status"],
    )
    selected_caps = dict(PER_NAME_CAP if caps is None else caps)
    schedule = build_target_schedule(
        selected_blocks,
        grain,
        cane,
        membership,
        allow_holdout=True,
        caps=selected_caps,
    )
    result = _run_schedule(
        inputs,
        schedule,
        membership,
        scenario=scenario,
        holding_sessions=holding_sessions,
    )
    return PortfolioRun(schedule, result, membership, selected_blocks)


def portfolio_metrics(result: BacktestResult) -> dict[str, object]:
    """Métricas determinísticas e descritivas de um livro."""
    daily = result.daily
    net = daily["net_return"].astype(float)
    equity = daily["equity_brl"].astype(float)
    total_return = float(equity.iloc[-1] / REFERENCE_AUM_BRL - 1.0)
    elapsed_days = max((equity.index[-1] - equity.index[0]).days, 1)
    cagr = float((1.0 + total_return) ** (365.25 / elapsed_days) - 1.0)
    volatility = float(net.std(ddof=1) * np.sqrt(252.0))
    sharpe = (
        float(net.mean() / net.std(ddof=1) * np.sqrt(252.0))
        if net.std(ddof=1) > 0
        else float("nan")
    )
    drawdown = equity / equity.cummax() - 1.0
    return {
        "scope": result.scope,
        "scenario": result.scenario,
        "sessions": len(daily),
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": volatility,
        "sharpe_zero_rf": sharpe,
        "max_drawdown": float(drawdown.min()),
        "positive_day_rate": float((net > 0).mean()),
        "gross_pnl_brl": float(daily["gross_pnl_brl"].sum()),
        "spot_cost_brl": float(daily["spot_cost_brl"].sum()),
        "borrow_cost_brl": float(daily["borrow_cost_brl"].sum()),
        "net_pnl_brl": float(equity.iloc[-1] - REFERENCE_AUM_BRL),
        "turnover_one_way": float(daily["turnover_one_way"].sum()),
        "active_blocks": int(result.effective_targets.abs().sum(axis=1).gt(0).sum()),
        "blocks": len(result.block_status),
    }


def primary_hprime(
    returns: pd.DataFrame,
    schedule: TargetSchedule,
    terminal_exits: dict[str, pd.Timestamp] | None = None,
) -> dict[str, object]:
    """Inclinação transversal demeanada e sign-flip exato de D-053/D-055."""
    numerators = dict.fromkeys(HOLDOUT_CROP_YEARS, 0.0)
    denominators = dict.fromkeys(HOLDOUT_CROP_YEARS, 0.0)
    rows_by_year = dict.fromkeys(HOLDOUT_CROP_YEARS, 0)
    blocks_by_year = dict.fromkeys(HOLDOUT_CROP_YEARS, 0)

    for block in schedule.blocks:
        x_row = schedule.operational_scores.loc[block.execution_date, list(GRAIN_NAMES)]
        valid_names = x_row.index[x_row.notna()].tolist()
        if not (set(valid_names) & PRODUCERS) or not (set(valid_names) & PROCESSORS):
            raise ValueError(f"teste primário sem os dois lados em {block.decision_date.date()}")
        segment = returns.loc[block.execution_date : block.exit_date, valid_names].iloc[1:].copy()
        if len(segment) != HOLDING_SESSIONS:
            raise ValueError("teste primário não possui 21 retornos forward")
        for name in valid_names:
            missing = segment.index[segment[name].isna()]
            if not len(missing):
                continue
            terminal = (terminal_exits or {}).get(name)
            if terminal is None or (missing <= terminal).any():
                raise ValueError(
                    f"retorno forward ausente no bloco {block.crop_year}/{block.sequence}"
                )
            segment.loc[missing, name] = 0.0
        forward = (1.0 + segment).prod() - 1.0
        x = x_row.loc[valid_names].astype(float)
        x = x - x.mean()
        y = forward.astype(float) - float(forward.mean())
        denominator = float((x * x).sum())
        if denominator <= 0:
            raise ValueError(f"score sem dispersão no bloco {block.crop_year}/{block.sequence}")
        numerators[block.crop_year] += float((x * y).sum())
        denominators[block.crop_year] += denominator
        rows_by_year[block.crop_year] += len(valid_names)
        blocks_by_year[block.crop_year] += 1

    slopes = {
        year: float(numerators[year] / denominators[year])
        for year in HOLDOUT_CROP_YEARS
        if denominators[year] > 0
    }
    exact = exact_primary_signflip(slopes)
    return {
        "cluster_slopes": slopes,
        "rows_by_crop_year": rows_by_year,
        "blocks_by_crop_year": blocks_by_year,
        **asdict(exact),
    }


def _crop_year_effects(
    inputs: HoldoutInputs,
    *,
    grain_override: pd.DataFrame | None = None,
) -> dict[str, float]:
    sessions = pd.DatetimeIndex(inputs.returns.index)
    effects: dict[str, float] = {}
    for year in HOLDOUT_CROP_YEARS:
        blocks = tuple(build_trade_blocks(sessions, year))
        run = run_portfolio_variant(inputs, blocks=blocks, grain_override=grain_override)
        effects[year] = float(portfolio_metrics(run.result)["total_return"])
    return effects


def _h4_regression(
    strategy_daily: pd.DataFrame,
    controls: pd.DataFrame,
    columns: tuple[str, ...],
) -> dict[str, object]:
    aligned = controls.reindex(strategy_daily.index)
    needed = [*columns, H4_RISK_FREE_COLUMN]
    if aligned[needed].isna().any().any():
        raise ValueError("H4 não alinha integralmente com os retornos diários da estratégia")
    y = strategy_daily["net_return"].astype(float) - aligned[H4_RISK_FREE_COLUMN].astype(float)
    design = sm.add_constant(aligned.loc[:, list(columns)].astype(float), has_constant="add")
    if np.linalg.matrix_rank(design.to_numpy()) != design.shape[1]:
        raise ValueError("matriz H4 não possui posto completo")
    fit = sm.OLS(y, design).fit(cov_type="HAC", cov_kwds={"maxlags": H4_HAC_LAGS})
    alpha = float(fit.params["const"])
    tvalue = float(fit.tvalues["const"])
    p_two_sided = float(fit.pvalues["const"])
    p_one_sided = p_two_sided / 2.0 if tvalue >= 0 else 1.0 - p_two_sided / 2.0
    return {
        "controls": list(columns),
        "observations": int(fit.nobs),
        "alpha_daily": alpha,
        "alpha_annualized_arithmetic": alpha * 252.0,
        "alpha_standard_error_hac": float(fit.bse["const"]),
        "alpha_t": tvalue,
        "alpha_p_one_sided": p_one_sided,
        "r_squared": float(fit.rsquared),
        "passed": bool(alpha > 0 and p_one_sided <= H4_ALPHA),
    }


def _h5_placebos(inputs: HoldoutInputs, real_effects: dict[str, float]) -> dict[str, object]:
    real_exact = exact_primary_signflip(real_effects)
    geo_effects = _crop_year_effects(inputs, grain_override=inputs.h5_geographic_scores)
    geo_exact = exact_primary_signflip(geo_effects)
    ratio = (
        abs(geo_exact.statistic) / abs(real_exact.statistic)
        if abs(real_exact.statistic) > 0
        else float("inf")
    )
    geographic_died = bool(ratio < H5_MAX_ABS_RATIO and geo_exact.pvalue > H5_ALPHA)

    base_grain = _select_scores(
        inputs.grain_scores,
        _all_blocks(pd.DatetimeIndex(inputs.returns.index)),
        7,
        list(GRAIN_NAMES),
    )
    exposure_rows = []
    for swap_producers, swap_processors in product((False, True), repeat=2):
        permuted = base_grain.copy()
        if swap_producers:
            permuted.loc[:, ["AGRO3", "SLCE3"]] = permuted[["SLCE3", "AGRO3"]].to_numpy()
        if swap_processors:
            permuted.loc[:, ["BRFS3", "JBSS3"]] = permuted[["JBSS3", "BRFS3"]].to_numpy()
        effects = _crop_year_effects(inputs, grain_override=permuted)
        exposure_rows.append(
            {
                "swap_producers": swap_producers,
                "swap_processors": swap_processors,
                "mean_crop_year_return": float(np.mean(list(effects.values()))),
                "crop_year_returns": effects,
            }
        )
    return {
        "real": {"crop_year_returns": real_effects, **asdict(real_exact)},
        "geographic": {
            "crop_year_returns": geo_effects,
            **asdict(geo_exact),
            "absolute_ratio_to_real": ratio,
            "died": geographic_died,
        },
        "exposure_within_side": exposure_rows,
    }


def _caps(*, grain: float = GRAIN_NAME_CAP, cane: float = CANE_SATELLITE_CAP) -> dict[str, float]:
    return {name: grain for name in GRAIN_NAMES} | {CANE_NAME: cane}


def _descriptive_metrics(factory) -> dict[str, object]:
    """Registra inviabilidade econômica esperada sem mascarar erro de dado/código."""
    try:
        return {"materializable": True, **portfolio_metrics(factory().result)}
    except ValueError as exc:
        if "ordem excede 5% do ADTV21" not in str(exc):
            raise
        return {
            "materializable": False,
            "reason": "spot_participation_above_5pct",
        }


def run_all_analyses(
    inputs: HoldoutInputs,
    preflight_payload: dict[str, object],
) -> list[dict[str, object]]:
    """Calcula obrigatoriamente os blocos 0–10, sem ramificar pelo resultado primário."""
    primary_run = run_portfolio_variant(inputs)
    primary = primary_hprime(inputs.returns, primary_run.schedule, inputs.terminal_exits)

    scenario_runs = {
        scenario: run_portfolio_variant(inputs, scenario=scenario) for scenario in COST_SCENARIOS
    }
    scenario_metrics = {
        scenario: portfolio_metrics(run.result) for scenario, run in scenario_runs.items()
    }
    monotonic = cost_monotonicity(
        {
            scenario: float(run.result.daily["equity_brl"].iloc[-1])
            for scenario, run in scenario_runs.items()
        }
    )
    base = scenario_runs[PORTFOLIO_PRIMARY_COST_SCENARIO]

    liquidity = asdict(audit_agro3_liquidity(base.schedule.decisions))

    naive_schedule = build_naive_sector_schedule(base.blocks, base.membership, allow_holdout=True)
    naive_result = _run_schedule(
        inputs,
        naive_schedule,
        base.membership,
        scenario=PORTFOLIO_PRIMARY_COST_SCENARIO,
        holding_sessions=HOLDING_SESSIONS,
    )
    orthogonal = sector_orthogonal_decomposition(
        base.result.weights, naive_result.weights, inputs.returns
    )
    orthogonal_summary = {key: value for key, value in orthogonal.items() if key != "daily"}

    h4 = {
        "core": _h4_regression(base.result.daily, inputs.h4_controls, H4_CORE_CONTROLS),
        "extended": _h4_regression(base.result.daily, inputs.h4_controls, H4_EXTENDED_CONTROLS),
    }

    real_effects = _crop_year_effects(inputs)
    h5 = _h5_placebos(inputs, real_effects)

    loo_names = {
        name: portfolio_metrics(run_portfolio_variant(inputs, excluded_name=name).result)
        for name in LOO_NAMES
    }
    sessions = pd.DatetimeIndex(inputs.returns.index)
    all_blocks = _all_blocks(sessions)
    loo_years = {
        year: portfolio_metrics(
            run_portfolio_variant(
                inputs,
                blocks=tuple(block for block in all_blocks if block.crop_year != year),
            ).result
        )
        for year in LOO_CROP_YEARS
    }

    sensitivities: dict[str, object] = {
        "adtv_brl": {
            str(int(value)): _descriptive_metrics(
                lambda value=value: run_portfolio_variant(inputs, adtv_floor_brl=value)
            )
            for value in ADTV_SENSITIVITY_BRL
        },
        "holding_sessions": {
            str(value): _descriptive_metrics(
                lambda value=value: run_portfolio_variant(inputs, holding_sessions=value)
            )
            for value in HOLDING_SENSITIVITY_SESSIONS
        },
        "total_signal_lag_days": {
            str(value): _descriptive_metrics(
                lambda value=value: run_portfolio_variant(inputs, total_signal_lag_days=value)
            )
            for value in TOTAL_SIGNAL_LAG_SENSITIVITY_DAYS
        },
        "grain_cap": {
            str(value): _descriptive_metrics(
                lambda value=value: run_portfolio_variant(inputs, caps=_caps(grain=value))
            )
            for value in GRAIN_CAP_SENSITIVITY
        },
        "cane_cap": {
            str(value): _descriptive_metrics(
                lambda value=value: run_portfolio_variant(inputs, caps=_caps(cane=value))
            )
            for value in CANE_CAP_SENSITIVITY
        },
    }

    attribution = attribution_by_name(base.result.attribution_brl, base.result.weights)
    metrics_detail = {
        "base": portfolio_metrics(base.result),
        "terminal_exits": (
            base.result.daily.loc[
                base.result.daily["terminal_exit_tickers"].notna(),
                ["terminal_exit_tickers", "spot_cost_brl", "turnover_one_way"],
            ]
            .reset_index(names="date")
            .to_dict("records")
        ),
        "attribution_by_name": attribution.reset_index(names="ticker").to_dict("records"),
        "concentration": concentration_metrics(attribution),
        "daily": base.result.daily.reset_index(names="date").to_dict("records"),
        "weights": base.result.weights.reset_index(names="date").to_dict("records"),
        "planned_targets": base.result.planned_targets.reset_index(names="execution_date").to_dict(
            "records"
        ),
        "effective_targets": base.result.effective_targets.reset_index(
            names="execution_date"
        ).to_dict("records"),
        "block_status": base.result.block_status.reset_index().to_dict("records"),
        "sector_weights": naive_result.weights.reset_index(names="date").to_dict("records"),
        "orthogonal_daily": orthogonal["daily"].reset_index(names="date").to_dict("records"),
    }

    return [
        preflight_payload,
        primary,
        {"scenarios": scenario_metrics, "cost_monotonicity": monotonic},
        liquidity,
        orthogonal_summary,
        h4,
        h5,
        loo_names,
        loo_years,
        sensitivities,
        metrics_detail,
    ]
