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

**Regra de decomposição pré-registrada (D-064).** ``sector_orthogonal_decomposition`` congela, antes
do holdout, uma separação ADITIVA e EXATA do retorno bruto do livro em (i) a parte alinhada à aposta
de setor e (ii) o resíduo ortogonal a ela, projetando os pesos reais sobre os pesos setoriais
ingênuos em espaço de pesos — **sem usar retorno na separação** (return-agnóstica). É a Alternativa
1 do fork de 2026-07-26: não altera a estratégia negociada; ensina o resultado do holdout a se
explicar (quanto foi setor, quanto foi clima). Distinta do ``sector_climate_decomposition`` do D-060
(incremento sobre a ingênua + regressão ex-post), que continua como descritivo do dev.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .engine import TargetSchedule, build_target_schedule
from .operational_spec import PROCESSORS, PRODUCERS, TradeBlock
from .strategy_spec import GRAIN_NAMES, UNIVERSE

_HELD_TOL = 1e-12
_AGRO3_BRANCH_LABELS = ("never_eligible", "intermittent", "always_eligible")


@dataclass(frozen=True)
class Agro3LiquidityAudit:
    """Resumo return-agnóstico do ramo de liquidez pré-registrado em D-067."""

    branch: str
    decisions: int
    eligible_decisions: int
    active_decisions: int
    two_producer_decisions: int
    one_producer_decisions: int
    no_producer_decisions: int
    core_available_decisions: int


def audit_agro3_liquidity(decisions: pd.DataFrame) -> Agro3LiquidityAudit:
    """Classifica a trajetória PIT da AGRO3 sem consultar preço ou retorno.

    A classificação é feita sobre cada data de decisão, nunca sobre uma média do holdout:

    - ``never_eligible``: AGRO3 não passa o filtro em nenhuma decisão;
    - ``intermittent``: entra e sai mecanicamente conforme o ADTV21 conhecido em ``D``;
    - ``always_eligible``: passa em todas as decisões.

    ``active`` exige simultaneamente elegibilidade e score válido. A profundidade da perna
    produtora é contada sobre os grãos ativos, pois é essa seção transversal que chega ao
    teste/carteira. O resultado é puramente operacional e não cria subtestes por regime.
    """
    required = {
        "agro3_eligible",
        "agro3_active",
        "active_grain_producers",
        "active_grain_processors",
    }
    missing = required - set(decisions.columns)
    if missing:
        raise ValueError(f"auditoria AGRO3×ADTV sem colunas: {sorted(missing)}")
    if decisions.empty:
        raise ValueError("auditoria AGRO3×ADTV exige ao menos uma decisão")

    eligible = decisions["agro3_eligible"]
    active = decisions["agro3_active"]
    if not pd.api.types.is_bool_dtype(eligible.dtype) or not pd.api.types.is_bool_dtype(
        active.dtype
    ):
        raise ValueError("elegibilidade/atividade da AGRO3 devem ser booleanas")
    if eligible.isna().any() or active.isna().any() or (active & ~eligible).any():
        raise ValueError("AGRO3 ativa exige elegibilidade completa e verdadeira")

    producers = decisions["active_grain_producers"]
    processors = decisions["active_grain_processors"]
    if (
        producers.isna().any()
        or processors.isna().any()
        or not producers.isin((0, 1, 2)).all()
        or not processors.isin((0, 1, 2)).all()
    ):
        raise ValueError("contagens ativas de produtor/processador devem pertencer a {0,1,2}")
    if (active & producers.eq(0)).any() or (~active & producers.eq(2)).any():
        raise ValueError("profundidade produtora é incompatível com a atividade da AGRO3")

    total = len(decisions)
    eligible_count = int(eligible.sum())
    if eligible_count == 0:
        branch = "never_eligible"
    elif eligible_count == total:
        branch = "always_eligible"
    else:
        branch = "intermittent"
    if branch not in _AGRO3_BRANCH_LABELS:  # pragma: no cover - tripwire defensivo
        raise RuntimeError("classificação AGRO3×ADTV fora do contrato D-067")

    return Agro3LiquidityAudit(
        branch=branch,
        decisions=total,
        eligible_decisions=eligible_count,
        active_decisions=int(active.sum()),
        two_producer_decisions=int(producers.eq(2).sum()),
        one_producer_decisions=int(producers.eq(1).sum()),
        no_producer_decisions=int(producers.eq(0).sum()),
        core_available_decisions=int(((producers >= 1) & (processors >= 1)).sum()),
    )


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
    caps: dict[str, float] | None = None,
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
        frozen,
        grain_scores,
        cane_signal,
        membership,
        allow_holdout=allow_holdout,
        caps=caps,
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


def sector_orthogonal_decomposition(
    book_weights: pd.DataFrame,
    sector_weights: pd.DataFrame,
    returns: pd.DataFrame,
) -> dict[str, object]:
    """Decomposição aditiva pré-registrada (D-064): parte de setor × resíduo climático ortogonal.

    Para cada pregão ``t``, projeta os pesos reais ``w`` sobre a direção de setor ``s`` (os pesos da
    carteira setorial ingênua no mesmo dia — mesma máquina, mesmos caps/elegibilidade):

        c        = ⟨w, s⟩ / ⟨s, s⟩          (0 se ⟨s, s⟩ = 0)
        w_setor  = c · s                     (componente alinhada à aposta de setor)
        w_clima  = w − c · s                 (resíduo ortogonal: ⟨w_clima, s⟩ = 0)

    A separação usa **só ``w`` e ``s``, nunca retornos** ⇒ return-agnóstica, congelável antes do
    holdout. A contribuição bruta de cada perna no dia é peso·retorno e, por linearidade, ``setor``
    + ``clima`` reconstrói exatamente o bruto do livro. Os totais somam as contribuições diárias
    (atribuição **aritmética**, antes de custos — custos não são lineares na projeção e são
    reportados à parte). ``climate_share`` é a fatia do bruto que sobrevive à neutralização de
    setor. Descritiva no dev (circular); a inferência mora só no holdout (Fase 6).
    """
    cols = list(UNIVERSE)
    if list(book_weights.columns) != cols or list(sector_weights.columns) != cols:
        raise ValueError(f"pesos exigem exatamente as colunas {cols}")
    idx = book_weights.index
    sector = sector_weights.reindex(idx)
    if sector.isna().any().any():
        raise ValueError("pesos setoriais não alinham com o índice do livro (NaN após reindex)")
    ret = returns.reindex(index=idx, columns=cols).fillna(0.0)

    w = book_weights.to_numpy(dtype=float)
    s = sector.to_numpy(dtype=float)
    r = ret.to_numpy(dtype=float)

    dot_ws = (w * s).sum(axis=1)
    dot_ss = (s * s).sum(axis=1)
    coef = np.divide(dot_ws, dot_ss, out=np.zeros_like(dot_ws), where=dot_ss > _HELD_TOL)
    w_sector = coef[:, None] * s
    w_climate = w - w_sector

    g_sector = (w_sector * r).sum(axis=1)
    g_climate = (w_climate * r).sum(axis=1)
    g_book = (w * r).sum(axis=1)
    ortho_resid = (w_climate * s).sum(axis=1)

    sector_total = float(g_sector.sum())
    climate_total = float(g_climate.sum())
    book_total = float(g_book.sum())
    share = climate_total / book_total if abs(book_total) > _HELD_TOL else float("nan")

    daily = pd.DataFrame(
        {
            "coef": coef,
            "sector_gross": g_sector,
            "climate_gross": g_climate,
            "book_gross": g_book,
            "ortho_residual": ortho_resid,
        },
        index=idx,
    )
    return {
        "sector_arith_return": sector_total,
        "climate_arith_return": climate_total,
        "book_arith_return": book_total,
        "climate_share": share,
        "max_ortho_residual": float(np.abs(ortho_resid).max()) if len(ortho_resid) else 0.0,
        "daily": daily,
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
