"""Diagnósticos descritivos da Fase 4.3 (D-060), sobre o desenvolvimento.

**Nada aqui valida a estratégia.** A direção do dev foi queimada em D-043/D-044 e o P&L do dev é
circular; a validação é o holdout de 5 anos-safra, lacrado até a Fase 6. Este módulo apenas
descreve o que o motor produz no dev, para expor de forma sistemática dois riscos já conhecidos:

- concentração do P&L num único nome (atribuição por nome);
- quanto do retorno é uma aposta de SETOR (produtor × processador) e não o sinal cross-section
  de clima (decomposição setor-vs-clima).

A decomposição não muda o contrato congelado (D-053/D-055). Se ela motivar neutralizar setor na
própria estratégia, isso vira uma decisão pré-registrada ANTES do holdout, separada daqui.

O benchmark setorial ingênuo reusa a máquina de pesos congelada: alimenta ``build_target_schedule``
com um ``E·Shock`` constante (produtor +1, processador −1) e cana inativa. Depois da inversão H′
isso vira "short produtor / long processador" com pesos iguais por perna — a aposta de setor pura,
sem nenhuma informação cross-section de clima. A diferença entre a carteira real e essa carteira
isola exatamente o que o score de clima acrescenta além do tilt de setor.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .engine import TargetSchedule, build_target_schedule
from .operational_spec import PROCESSORS, PRODUCERS, TradeBlock
from .strategy_spec import GRAIN_NAMES, UNIVERSE

_HELD_TOL = 1e-12


def attribution_by_name(attribution_brl: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
    """P&L bruto por nome e sua fatia do total, a partir do livro diário do motor.

    ``attribution_brl`` é o P&L bruto diário por nome (retorno × posição, em reais) e ``weights``
    são os pesos diários pós-drift. O lado (long/short) é o sinal do peso médio nos dias em que o
    nome esteve na carteira. ``pnl_share`` divide pelo total bruto; se o total for ~0 fica ``NaN``.
    """
    if list(attribution_brl.columns) != list(UNIVERSE) or list(weights.columns) != list(UNIVERSE):
        raise ValueError(f"atribuição e pesos exigem exatamente as colunas {list(UNIVERSE)}")
    gross = attribution_brl.sum()
    total = float(gross.sum())
    held = weights.abs() > _HELD_TOL
    avg_weight = weights.where(held).mean()
    side = pd.Series(
        np.where(avg_weight > 0, "long", np.where(avg_weight < 0, "short", "flat")),
        index=avg_weight.index,
    )
    share = gross / total if abs(total) > _HELD_TOL else pd.Series(np.nan, index=gross.index)
    out = pd.DataFrame(
        {
            "side": side,
            "avg_weight": avg_weight,
            "gross_pnl_brl": gross,
            "pnl_share": share,
        }
    )
    return out.loc[list(UNIVERSE)]


def concentration_metrics(attribution: pd.DataFrame) -> dict[str, object]:
    """Concentração do P&L: nome dominante, sua fatia em módulo e o HHI das fatias."""
    shares = attribution["pnl_share"].abs().dropna()
    if shares.empty:
        return {"top1_name": None, "top1_abs_share": float("nan"), "hhi": float("nan")}
    return {
        "top1_name": str(shares.idxmax()),
        "top1_abs_share": float(shares.max()),
        "hhi": float((shares**2).sum()),
    }


def build_naive_sector_schedule(
    blocks: Sequence[TradeBlock],
    membership: pd.DataFrame,
    *,
    allow_holdout: bool = False,
) -> TargetSchedule:
    """Carteira setorial ingênua: short produtor / long processador, sem score de clima.

    Reusa integralmente a máquina de pesos congelada. Alimenta ``build_target_schedule`` com um
    ``E·Shock`` constante (produtor +1, processador −1) — que a inversão H′ transforma no tilt de
    setor com pesos iguais por perna — e cana inativa (``window_not_started``). O universo elegível
    é o mesmo da carteira real, então as duas só diferem pela informação cross-section de clima.
    """
    frozen = tuple(blocks)
    if not frozen:
        raise ValueError("benchmark setorial exige ao menos um bloco")
    decisions = pd.DatetimeIndex([block.decision_date for block in frozen])
    # E·Shock pré-H′: produtor +1 e processador −1 ⇒ operacional (negativo) = short produtor,
    # long processador. Constante em toda decisão: nenhuma variação cross-section de clima.
    sector_row = {name: (1.0 if name in PRODUCERS else -1.0) for name in GRAIN_NAMES}
    grain_scores = pd.DataFrame([sector_row] * len(frozen), index=decisions)
    cane_signal = pd.DataFrame({"shock": np.nan, "status": "window_not_started"}, index=decisions)
    return build_target_schedule(
        frozen, grain_scores, cane_signal, membership, allow_holdout=allow_holdout
    )


def _total_return(daily: pd.DataFrame, initial_aum_brl: float) -> float:
    return float(daily["equity_brl"].iloc[-1]) / float(initial_aum_brl) - 1.0


def sector_climate_decomposition(
    book_daily: pd.DataFrame,
    naive_daily: pd.DataFrame,
    returns: pd.DataFrame,
    *,
    initial_aum_brl: float,
) -> dict[str, float]:
    """Separa o retorno em aposta de setor e resíduo cross-section de clima.

    Duas leituras complementares, ambas DESCRITIVAS (dev com poucos nomes; sem p-valor — a
    inferência mora só no holdout):

    1. Incremento sobre a carteira setorial ingênua: retorno da carteira real menos o da carteira
       que só expressa short produtor / long processador. Se ~0, o livro é uma aposta de setor e o
       score de clima não acrescenta nada na seção transversal.
    2. Regressão do retorno diário líquido do livro no spread diário processador−produtor. ``beta``
       ≈ exposição ao spread; ``r2`` alto ⇒ o retorno é, em variância, o próprio spread setorial.
    """
    book_ret = _total_return(book_daily, initial_aum_brl)
    naive_ret = _total_return(naive_daily, initial_aum_brl)
    producers = [name for name in PRODUCERS if name in returns.columns]
    processors = [name for name in PROCESSORS if name in returns.columns]
    spread = (
        (returns[processors].mean(axis=1) - returns[producers].mean(axis=1))
        .reindex(book_daily.index)
        .fillna(0.0)
    )
    y = book_daily["net_return"].to_numpy(dtype=float)
    design = np.column_stack([np.ones_like(y), spread.to_numpy(dtype=float)])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    residual = y - design @ beta
    var_y = float(np.var(y))
    r2 = float(1.0 - np.var(residual) / var_y) if var_y > 0 else float("nan")
    return {
        "book_total_return": book_ret,
        "naive_sector_total_return": naive_ret,
        "climate_increment": book_ret - naive_ret,
        "spread_beta": float(beta[1]),
        "spread_r2": r2,
    }


def cost_monotonicity(equity_by_scenario: dict[str, float]) -> dict[str, object]:
    """Verifica que patrimônio final obedece zero ≥ base ≥ double (custo monótono)."""
    required = {"zero", "base", "double"}
    if set(equity_by_scenario) != required:
        raise ValueError(f"monotonicidade exige exatamente os cenários {sorted(required)}")
    zero = equity_by_scenario["zero"]
    base = equity_by_scenario["base"]
    double = equity_by_scenario["double"]
    ok = (zero >= base - 1e-6) and (base >= double - 1e-6)
    return {"monotonic": bool(ok), "zero": zero, "base": base, "double": double}
