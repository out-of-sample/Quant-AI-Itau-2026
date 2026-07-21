"""Smoke test de engenharia do motor no desenvolvimento 2018/19 (D-058).

**NÃO é avaliação de estratégia.** A direção do dev foi queimada em D-043/D-044; o P&L abaixo é
descritivo, não valida a tese. O objetivo é verificar que o motor roda ponta a ponta com dados
reais e produz turnover/custos/atribuição sãos, consumindo a proxy de aluguel D-058. O holdout
2020–2025 permanece lacrado (``require_backtest_scope`` falha se um bloco não for dev).

Uso: ``python scripts/run_smoke_dev.py``.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from quantagro.backtest.engine import build_target_schedule, run_backtest  # noqa: E402
from quantagro.backtest.inputs import (  # noqa: E402
    materialize_cane_signal,
    materialize_grain_raw_scores,
)
from quantagro.backtest.operational_spec import COST_SCENARIOS, build_trade_blocks  # noqa: E402
from quantagro.backtest.strategy_spec import UNIVERSE  # noqa: E402
from quantagro.features.cane_shock import stamp_cane_monthly_panel  # noqa: E402
from quantagro.features.exposure import load_exposure_registry  # noqa: E402
from quantagro.features.panel import CLIMATOLOGY_FIRST_YEAR  # noqa: E402
from quantagro.features.shock import stamp_municipal_panel  # noqa: E402
from quantagro.ingest.conab import parse_levantamento  # noqa: E402
from quantagro.ingest.pam import parse_pam  # noqa: E402
from quantagro.stats.cane_h1 import _prepare_conab  # noqa: E402
from quantagro.stats.h2a import _stamp_grains  # noqa: E402
from quantagro.validate.borrow import build_proxy_borrow_state  # noqa: E402

CROP_YEAR = "2018/19"
STATE = "data/interim/market_state_dev.parquet"
RETURNS = "data/interim/equity_returns_dev.parquet"
OUT_DIR = Path("data/processed")


def _pam(pattern: str) -> pd.DataFrame:
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit(f"PAM ausente: {pattern}")
    return pd.concat((parse_pam(f) for f in files), ignore_index=True)


def load_grain_inputs():
    conab = _stamp_grains(
        parse_levantamento("data/raw/conab/LevantamentoGraos_20260716.txt", "graos")
    )
    pam = pd.concat(
        [_pam("data/raw/pam/pam_1612_soy_*.json"), _pam("data/raw/pam/pam_1612_corn_total_*.json")],
        ignore_index=True,
    )
    parts = sorted(glob.glob("data/interim/municipal_precip/part_*.parquet"))
    if not parts:
        raise SystemExit("painel municipal ausente — rode scripts/build_municipal_panel.py")
    muni = pd.concat((pd.read_parquet(p) for p in parts), ignore_index=True).drop_duplicates(
        ["ref_date", "kind", "municipality_code"]
    )
    producing = set(pam["municipality_code"].unique())
    muni = muni[muni["municipality_code"].isin(producing)].sort_values(["kind", "ref_date"])
    muni = stamp_municipal_panel(muni.reset_index(drop=True))
    registry = load_exposure_registry("data/reference/exposure_fundamental_v1.json")
    return registry, muni, pam, conab


def load_cane_inputs():
    conab = _prepare_conab(
        parse_levantamento("data/raw/conab/LevantamentoCana_20260716.txt", "cana")
    )
    pam = _pam("data/raw/pam/pam_1612_sugarcane_*.json")
    parts = sorted(glob.glob("data/interim/cane_monthly_precip/part_*.parquet"))
    if not parts:
        raise SystemExit("painel mensal da cana ausente — rode scripts/build_cane_monthly_panel.py")
    monthly = pd.concat((pd.read_parquet(p) for p in parts), ignore_index=True).drop_duplicates(
        ["ref_date", "kind", "municipality_code"]
    )
    return stamp_cane_monthly_panel(monthly), pam, conab


def _wide(state: pd.DataFrame, column: str, dtype) -> pd.DataFrame:
    wide = state.pivot(index="date", columns="ticker", values=column).sort_index()  # noqa: PD010
    wide.index = pd.DatetimeIndex(wide.index)
    return wide[list(UNIVERSE)].astype(dtype)


def main() -> None:
    print("=" * 90)
    print("SMOKE TEST DE ENGENHARIA — dev 2018/19 (D-058). NÃO é resultado de estratégia:")
    print("a direção do dev foi queimada em D-043/D-044; o P&L é descritivo. Holdout lacrado.")
    print("=" * 90)

    state = pd.read_parquet(STATE)
    returns = pd.read_parquet(RETURNS)
    adtv = _wide(state, "adtv_brl", float)
    traded = _wide(state, "traded", bool)
    eligible = _wide(state, "eligible", bool)

    sessions = pd.DatetimeIndex(sorted(state["date"].unique()))
    blocks = build_trade_blocks(sessions, CROP_YEAR)
    decisions = pd.DatetimeIndex([b.decision_date for b in blocks])
    span = f"{decisions.min().date()}→{decisions.max().date()}"
    print(f"\nblocos {CROP_YEAR}: {len(blocks)} | decisões {span}")

    registry, muni, pam_g, conab_g = load_grain_inputs()
    grain_scores = materialize_grain_raw_scores(
        blocks, registry, muni, pam_g, conab_g, CLIMATOLOGY_FIRST_YEAR
    )
    monthly, pam_c, conab_c = load_cane_inputs()
    try:
        cane_signal = materialize_cane_signal(
            blocks, monthly, pam_c, conab_c, CLIMATOLOGY_FIRST_YEAR
        )
        cane_note = "cana materializada"
    except ValueError as exc:
        if "CANA" not in str(exc).upper():
            raise
        # Limitação real (não bug): o bloco 2018/19 exige o peso CONAB de cana do ano ANTERIOR
        # (2017/18), mas a série de vintages datáveis da cana só começa em 2018/19 (D-050). Logo,
        # SMTO3 não é scoreável no dev — fica fora via window_not_started, com o motivo registrado.
        cane_signal = pd.DataFrame(
            {"shock": np.nan, "status": "window_not_started"}, index=decisions
        )
        cane_note = (
            "SMTO3 INATIVO no dev 2018/19 (satélite fora do score): sem peso CONAB de cana do "
            f"ano anterior. Motivo real capturado: {exc}"
        )

    print(f"\ncana: {cane_note}")
    schedule = build_target_schedule(blocks, grain_scores, cane_signal, eligible)
    borrow = build_proxy_borrow_state(decisions, UNIVERSE, eligible.loc[decisions])

    print("\n--- agenda de decisão (schedule) ---")
    cols = ["market_eligible", "scored_grains", "cane_status", "status"]
    print(schedule.decisions[cols].to_string())

    print("\n--- pesos-alvo por execução (dollar-neutral por construção) ---")
    tw = schedule.target_weights
    print(tw.round(3).to_string())
    print(f"máx |Σw| entre execuções = {tw.sum(axis=1).abs().max():.2e} (esperado ~0)")
    print(f"bruto Σ|w| por execução: {tw.abs().sum(axis=1).round(3).tolist()}")

    print("\n--- P&L por cenário (engenharia) ---")
    header = (
        f"{'cenário':>8} | {'gross':>10} | {'spot':>8} | {'aluguel':>8} | "
        f"{'net':>10} | {'ret%':>7} | {'turn 1w':>8}"
    )
    print(header)
    print("-" * len(header))
    initial = 500_000.0
    for scenario in COST_SCENARIOS:
        result = run_backtest(returns, schedule, adtv, traded, borrow, scenario=scenario)
        d = result.daily
        gross = d["gross_pnl_brl"].sum()
        spot = d["spot_cost_brl"].sum()
        bwr = d["borrow_cost_brl"].sum()
        net = d["equity_brl"].iloc[-1] - initial
        ret = net / initial * 100.0
        turn = d["turnover_one_way"].sum()
        print(
            f"{scenario:>8} | {gross:>10,.0f} | {spot:>8,.0f} | {bwr:>8,.0f} | "
            f"{net:>10,.0f} | {ret:>+6.2f}% | {turn:>7.2f}x"
        )
        if scenario == "base":
            print(
                f"\n  exposição: bruto máx {d['gross_exposure'].max():.3f}, "
                f"|net| máx {d['net_exposure'].abs().max():.2e} (dollar-neutral mantido)"
            )
            final_equity = float(d["equity_brl"].iloc[-1])
            healthy = np.isfinite(final_equity) and final_equity > 0
            print(f"  patrimônio final positivo e finito: {healthy}")
            print("\n  status por bloco:")
            print(
                "  "
                + result.block_status[["status", "limiting_ticker"]]
                .to_string()
                .replace("\n", "\n  ")
            )
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            d.to_parquet(OUT_DIR / "smoke_dev_daily_base.parquet")
            result.weights.to_parquet(OUT_DIR / "smoke_dev_weights_base.parquet")

    print("\n" + "=" * 90)
    print("SMOKE OK se: motor rodou os 3 cenários sem erro, Σw≈0, custos zero<base<2×,")
    print("patrimônio finito>0. Interpretação de LUCRO fica para o holdout (Fase 6).")
    print("=" * 90)


if __name__ == "__main__":
    main()
