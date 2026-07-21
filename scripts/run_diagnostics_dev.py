"""Diagnósticos descritivos da Fase 4.3 no dev 2018/19 (D-060).

**NÃO valida a estratégia.** A direção do dev foi queimada (D-043/D-044) e o P&L do dev é
circular; só o holdout (Fase 6) valida. Este relatório expõe, de forma sistemática, dois riscos
já conhecidos: (1) concentração do P&L num único nome; (2) quanto do retorno é aposta de SETOR
(produtor × processador) e não sinal cross-section de clima. Reusa os carregadores do smoke.

Uso: ``python scripts/run_diagnostics_dev.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from run_smoke_dev import (  # noqa: E402
    CROP_YEAR,
    RETURNS,
    STATE,
    _wide,
    load_grain_inputs,
)

from quantagro.backtest.diagnostics import (  # noqa: E402
    attribution_by_name,
    build_naive_sector_schedule,
    concentration_metrics,
    cost_monotonicity,
    sector_climate_decomposition,
)
from quantagro.backtest.engine import build_target_schedule, run_backtest  # noqa: E402
from quantagro.backtest.inputs import materialize_grain_raw_scores  # noqa: E402
from quantagro.backtest.operational_spec import (  # noqa: E402
    COST_SCENARIOS,
    REFERENCE_AUM_BRL,
    build_trade_blocks,
)
from quantagro.backtest.strategy_spec import UNIVERSE  # noqa: E402
from quantagro.features.panel import CLIMATOLOGY_FIRST_YEAR  # noqa: E402
from quantagro.validate.borrow import build_proxy_borrow_state  # noqa: E402

OUT_DIR = Path("data/processed")


def main() -> None:
    print("=" * 92)
    print("DIAGNÓSTICOS DA FASE 4.3 — dev 2018/19 (D-060). DESCRITIVO, NÃO validação.")
    print("O P&L do dev é circular (direção H′ derivada do próprio dev). Só o holdout valida.")
    print("=" * 92)

    state = pd.read_parquet(STATE)
    returns = pd.read_parquet(RETURNS)
    adtv = _wide(state, "adtv_brl", float)
    traded = _wide(state, "traded", bool)
    eligible = _wide(state, "eligible", bool)

    sessions = pd.DatetimeIndex(sorted(state["date"].unique()))
    blocks = build_trade_blocks(sessions, CROP_YEAR)
    decisions = pd.DatetimeIndex([b.decision_date for b in blocks])

    registry, muni, pam_g, conab_g = load_grain_inputs()
    grain_scores = materialize_grain_raw_scores(
        blocks, registry, muni, pam_g, conab_g, CLIMATOLOGY_FIRST_YEAR
    )
    # SMTO3 é holdout-only no dev (D-059): sem peso CONAB de cana de 2017/18, fica fora do score.
    cane_signal = pd.DataFrame({"shock": np.nan, "status": "window_not_started"}, index=decisions)
    borrow = build_proxy_borrow_state(decisions, UNIVERSE, eligible.loc[decisions])

    book = build_target_schedule(blocks, grain_scores, cane_signal, eligible)
    naive = build_naive_sector_schedule(blocks, eligible)

    # --- Bloco A: invariantes de custo (o motor já garante Σw=0 e caps internamente) --------
    equity_by_scenario = {}
    book_results = {}
    for scenario in COST_SCENARIOS:
        result = run_backtest(returns, book, adtv, traded, borrow, scenario=scenario)
        book_results[scenario] = result
        equity_by_scenario[scenario] = float(result.daily["equity_brl"].iloc[-1])
    mono = cost_monotonicity(equity_by_scenario)
    base = book_results["base"]

    print("\n--- Bloco A · invariantes ---")
    tw = book.target_weights
    print(f"dollar-neutral alvo: máx|Σw| = {tw.sum(axis=1).abs().max():.2e} (esperado ~0)")
    print(f"bruto alvo máx: {tw.abs().sum(axis=1).max():.3f} (≤ 1,0)")
    print(
        f"custo monótono (zero≥base≥double): {mono['monotonic']} | "
        f"zero {mono['zero']:,.0f} ≥ base {mono['base']:,.0f} ≥ double {mono['double']:,.0f}"
    )

    # --- Bloco B: atribuição por nome -------------------------------------------------------
    attr = attribution_by_name(base.attribution_brl, base.weights)
    conc = concentration_metrics(attr)
    print("\n--- Bloco B · atribuição por nome (cenário base) ---")
    print(attr.round(4).to_string())
    print(
        f"\nconcentração: nome dominante {conc['top1_name']} "
        f"({conc['top1_abs_share']:.1%} do P&L bruto em módulo) | HHI {conc['hhi']:.3f}"
    )
    costs = base.daily[["gross_pnl_brl", "borrow_cost_brl", "spot_cost_brl", "net_pnl_brl"]].sum()
    print(
        f"bruto {costs['gross_pnl_brl']:,.0f} − aluguel {costs['borrow_cost_brl']:,.0f} "
        f"− spot {costs['spot_cost_brl']:,.0f} = líquido {costs['net_pnl_brl']:,.0f}"
    )

    # --- Bloco C: decomposição setor-vs-clima -----------------------------------------------
    naive_base = run_backtest(returns, naive, adtv, traded, borrow, scenario="base")
    decomp = sector_climate_decomposition(
        base.daily, naive_base.daily, returns, initial_aum_brl=REFERENCE_AUM_BRL
    )
    print("\n--- Bloco C · decomposição setor-vs-clima (cenário base) ---")
    book_r = decomp["book_total_return"]
    naive_r = decomp["naive_sector_total_return"]
    incr = decomp["climate_increment"]
    print(f"retorno da carteira real (com score de clima):    {book_r:+.2%}")
    print(f"retorno da carteira setorial ingênua (só setor):  {naive_r:+.2%}")
    print(f"incremento atribuível ao clima (real − ingênua):  {incr:+.2%}")
    print(
        f"regressão no spread processador−produtor: beta {decomp['spread_beta']:.3f}, "
        f"R² {decomp['spread_r2']:.3f}"
    )
    print(
        "\nLeitura: incremento ~0 e R² alto ⇒ no dev o livro É uma aposta de setor; o score de\n"
        "clima quase não diferencia com 3 nomes ativos. O retorno vem do spread proteína×\n"
        "produtor, não do sinal climático. Consequência para o relatório: reportar exposição\n"
        "setorial, não vender o P&L do dev como alpha de clima."
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    attr.to_parquet(OUT_DIR / "diag_dev_attribution.parquet")
    naive_base.daily.to_parquet(OUT_DIR / "diag_dev_naive_daily.parquet")
    pd.Series(decomp).to_json(OUT_DIR / "diag_dev_decomposition.json")

    print("\n" + "=" * 92)
    print("DIAGNÓSTICO OK se rodou sem erro. Interpretação de LUCRO fica para o holdout (Fase 6).")
    print("=" * 92)


if __name__ == "__main__":
    main()
