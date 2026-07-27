"""Contrato operacional return-agnóstico da Fase 4.0 (D-055).

Este módulo fecha os graus de liberdade encontrados em D-054 antes da máquina de backtest.
Ele não lê preços, retornos ou o holdout: materializa calendário, composição do score, política
de universo incompleto, partição temporal, inferência exata e hipóteses de investibilidade.

O painel estatístico e a carteira usam os mesmos blocos não sobrepostos. Cada posição entra no
close de ``X_k`` e é encerrada/rebalanceada no close de ``X_{k+1}``, exatamente 21 intervalos
de pregão depois. O retorno do close de transição pertence uma única vez ao bloco que termina.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from math import inf, sqrt

import numpy as np
import pandas as pd

from quantagro.features.shock_spec import crop_year_start

from .strategy_spec import (
    ALPHA,
    CANE_NAME,
    FWD_HORIZON_DAYS,
    GRAIN_NAMES,
    HOLDOUT_CROP_YEARS,
    operational_cane_score,
    operational_grain_score,
)

# --- calendário ------------------------------------------------------------------------
ANCHOR_MONTH_DAY: tuple[int, int] = (1, 7)
FINAL_SIGNAL_MONTH_DAY: tuple[int, int] = (9, 7)
HOLDING_SESSIONS: int = FWD_HORIZON_DAYS

# --- score e lados econômicos -----------------------------------------------------------
GRAIN_CROPS: tuple[str, ...] = ("soy", "corn_second")
PRODUCERS: frozenset[str] = frozenset({"AGRO3", "SLCE3"})
PROCESSORS: frozenset[str] = frozenset({"BRFS3", "JBSS3"})
CANE_UFS: tuple[str, ...] = ("GO", "MG", "MS", "PR", "SP")
CANE_SCALE: float = 1.0  # z-score na mesma escala natural; o cap de 0,15 é o único haircut

# --- partição temporal -----------------------------------------------------------------
DEV_CROP_YEARS: tuple[str, ...] = ("2015/16", "2016/17", "2017/18", "2018/19")
TRANSITION_CROP_YEAR: str = "2019/20"
DEV_END = pd.Timestamp("2019-12-31")
HOLDOUT_START = pd.Timestamp("2020-01-01")
HOLDOUT_END = pd.Timestamp("2025-12-31")

# --- liquidez e custos -----------------------------------------------------------------
REFERENCE_AUM_BRL: float = 500_000.0
ADTV_WINDOW: int = 21
ADTV_FLOOR_BRL: float = 8_000_000.0
MAX_SPOT_PARTICIPATION: float = 0.05
B3_SPOT_FEE_BPS: float = 3.5  # 3,0 bps vigente; 3,2 no leilão; arredondado para cima
BROKERAGE_BPS: float = 2.0  # hipótese uniforme; corretagem histórica é contrato privado
SLIPPAGE_FIXED_BPS: float = 5.0
IMPACT_BPS_AT_ONE_PERCENT: float = 10.0
BORROW_LOOKBACK_SESSIONS: int = 5
BORROW_RATE_FLOOR: float = 0.05
BORROW_INTERMEDIARY_RATE: float = 0.01
B3_BORROW_FEE_ALPHA: float = 0.20
B3_BORROW_FEE_FLOOR: float = 0.00025  # 2,5 bps a.a.
B3_BORROW_FEE_CAP: float = 0.007  # 70 bps a.a.
MAX_BORROW_STOCK_SHARE: float = 0.01
COST_SCENARIOS: tuple[str, ...] = ("zero", "base", "double")

# --- inferência -------------------------------------------------------------------------
PERMUTATION_KIND: str = "exact_crop_year_sign_flip"
EXPECTED_PERMUTATIONS: int = 2 ** len(HOLDOUT_CROP_YEARS)


@dataclass(frozen=True)
class TradeBlock:
    """Bloco de 21 retornos close-to-close, identificado por ano-safra."""

    crop_year: str
    sequence: int
    decision_date: pd.Timestamp
    execution_date: pd.Timestamp
    exit_date: pd.Timestamp

    def __post_init__(self) -> None:
        crop_year_start(self.crop_year)
        if self.sequence < 0:
            raise ValueError("sequência do bloco deve ser não-negativa")
        if not self.decision_date < self.execution_date < self.exit_date:
            raise ValueError("bloco exige decisão < execução < saída")


@dataclass(frozen=True)
class ExactPermutationResult:
    """Resultado do teste unilateral exato sobre cinco clusters ano-safra."""

    statistic: float
    pvalue: float
    permutations: int
    passed: bool


class HoldoutLockedError(PermissionError):
    """Acesso solicitado ao holdout antes da liberação deliberada da Fase 6."""


def _sessions_index(sessions: Sequence[pd.Timestamp] | pd.DatetimeIndex) -> pd.DatetimeIndex:
    idx = pd.DatetimeIndex(sessions).normalize()
    if idx.empty or not idx.is_monotonic_increasing or idx.has_duplicates:
        raise ValueError("pregões devem formar índice não vazio, crescente e sem duplicatas")
    return idx


def build_trade_blocks(
    sessions: Sequence[pd.Timestamp] | pd.DatetimeIndex,
    crop_year: str,
    *,
    holding_sessions: int = HOLDING_SESSIONS,
) -> tuple[TradeBlock, ...]:
    """Gera a grade D→X de D-055 sem consultar preços ou retornos.

    A primeira decisão é o primeiro pregão em ou após 7/jan do segundo ano da safra, quando
    dezembro completo já está disponível pelo lag de sete dias. Rebalanceamentos seguintes
    ocorrem a cada 21 pregões. O primeiro ``D_k`` da grade em ou após 7/set é o último; seu
    bloco ainda é mantido por 21 pregões e então a carteira fica zerada.
    """
    idx = _sessions_index(sessions)
    if (
        isinstance(holding_sessions, bool)
        or not isinstance(holding_sessions, int)
        or holding_sessions <= 0
    ):
        raise ValueError("horizonte deve ser um inteiro positivo de pregões")
    year = crop_year_start(crop_year) + 1
    anchor = pd.Timestamp(year, *ANCHOR_MONTH_DAY)
    cutoff = pd.Timestamp(year, *FINAL_SIGNAL_MONTH_DAY)
    decision_pos = int(idx.searchsorted(anchor, side="left"))
    if decision_pos >= len(idx) or decision_pos + 1 >= len(idx):
        raise ValueError(f"calendário não cobre a âncora de {crop_year}")

    blocks: list[TradeBlock] = []
    execution_pos = decision_pos + 1
    for sequence in range(len(idx)):
        exit_pos = execution_pos + holding_sessions
        if exit_pos >= len(idx):
            raise ValueError(f"calendário não cobre a saída final de {crop_year}")
        block = TradeBlock(
            crop_year=crop_year,
            sequence=sequence,
            decision_date=idx[decision_pos],
            execution_date=idx[execution_pos],
            exit_date=idx[exit_pos],
        )
        blocks.append(block)
        if block.decision_date >= cutoff:
            break
        # O close de saída do bloco atual é o close de execução do próximo. A nova decisão
        # usa somente o pregão imediatamente anterior; nenhum retorno é duplicado.
        execution_pos = exit_pos
        decision_pos = execution_pos - 1
    else:  # pragma: no cover - proteção lógica; o calendário finito sempre encerra antes
        raise RuntimeError("grade não alcançou a data final")
    return tuple(blocks)


def grain_mechanism_score(
    exposure: Mapping[str, float], shocks: Mapping[str, float | None]
) -> float:
    """Calcula ``E·Shock`` sem renormalizar cultura cuja janela ainda não começou.

    ``None`` significa exclusivamente ``window_not_started`` e contribui zero. Chave ausente,
    cultura extra ou valor não finito representa erro de dado e falha alto.
    """
    if set(exposure) != set(GRAIN_CROPS) or set(shocks) != set(GRAIN_CROPS):
        raise ValueError("score de grãos exige exatamente soja e milho 2ª safra")
    total = 0.0
    for crop in GRAIN_CROPS:
        e = float(exposure[crop])
        shock = shocks[crop]
        if not np.isfinite(e):
            raise ValueError("exposição de grão deve ser finita")
        if shock is None:
            continue
        value = float(shock)
        if not np.isfinite(value):
            raise ValueError("Shock indefinido não pode virar zero")
        total += e * value
    return total


def aggregate_cane_shock(
    shocks_by_uf: Mapping[str, float], weights_by_uf: Mapping[str, float]
) -> float:
    """Choque nacional de maturação da cana, CONAB-weighted nas cinco UFs de D-050.

    As cinco UFs são obrigatórias. Os pesos positivos são normalizados apenas dentro do suporte
    pré-registrado; buraco técnico não é renormalizado silenciosamente.
    """
    expected = set(CANE_UFS)
    if set(shocks_by_uf) != expected or set(weights_by_uf) != expected:
        raise ValueError("cana exige exatamente as cinco UFs do contrato D-050")
    shocks = np.array([float(shocks_by_uf[uf]) for uf in CANE_UFS])
    weights = np.array([float(weights_by_uf[uf]) for uf in CANE_UFS])
    if not np.isfinite(shocks).all() or not np.isfinite(weights).all():
        raise ValueError("Shock e pesos da cana devem ser finitos")
    if (weights < 0).any() or weights.sum() <= 0:
        raise ValueError("pesos da cana devem ser não-negativos e somar valor positivo")
    return float(CANE_SCALE * (shocks @ (weights / weights.sum())))


def compose_operational_scores(
    grain_raw_scores: Mapping[str, float],
    eligible: Sequence[str],
    cane_shock: float | None = None,
) -> dict[str, float]:
    """Compõe o conjunto que será demeanado, com trava dos dois lados econômicos.

    A carteira só existe se ao menos um produtor e um processador de grãos tiverem score válido
    e forem elegíveis. SMTO3 não substitui o núcleo; antes do primeiro prefixo válido de
    maturação, ``cane_shock=None`` a mantém fora do score e do demean.
    """
    eligible_set = set(eligible)
    unknown = eligible_set - (set(GRAIN_NAMES) | {CANE_NAME})
    if unknown:
        raise ValueError(f"ticker elegível fora do universo: {sorted(unknown)}")
    score_unknown = set(grain_raw_scores) - set(GRAIN_NAMES)
    if score_unknown:
        raise ValueError(f"score de grão fora do núcleo: {sorted(score_unknown)}")
    active_grains = tuple(
        name for name in GRAIN_NAMES if name in grain_raw_scores and name in eligible_set
    )
    active_set = set(active_grains)
    values = {name: float(grain_raw_scores[name]) for name in active_grains}
    if not np.isfinite(list(values.values())).all():
        raise ValueError("scores de grãos devem ser finitos")
    if not (active_set & PRODUCERS) or not (active_set & PROCESSORS):
        return {}
    scores = {name: float(operational_grain_score(value)) for name, value in values.items()}
    if CANE_NAME in eligible_set and cane_shock is not None:
        cane = float(cane_shock)
        if not np.isfinite(cane):
            raise ValueError("Shock de cana indefinido não pode entrar no demean")
        scores[CANE_NAME] = float(operational_cane_score(cane))
    return scores


def classify_block(block: TradeBlock) -> str:
    """Classifica um bloco como ``dev``, ``holdout`` ou ``excluded`` sem truncá-lo."""
    if block.crop_year in DEV_CROP_YEARS and block.exit_date <= DEV_END:
        return "dev"
    if (
        block.crop_year in HOLDOUT_CROP_YEARS
        and block.decision_date >= HOLDOUT_START
        and block.exit_date <= HOLDOUT_END
    ):
        return "holdout"
    return "excluded"


def require_backtest_scope(blocks: Sequence[TradeBlock], allow_holdout: bool = False) -> str:
    """Falha antes da leitura de retornos em blocos excluídos ou holdout não liberado."""
    if not blocks:
        raise ValueError("execução exige ao menos um bloco")
    scopes = {classify_block(block) for block in blocks}
    if "excluded" in scopes:
        raise ValueError("bloco fora do dev/holdout congelado; fronteiras nunca são truncadas")
    if len(scopes) != 1:
        raise ValueError("uma execução não pode misturar desenvolvimento e holdout")
    scope = scopes.pop()
    if scope == "holdout" and not allow_holdout:
        raise HoldoutLockedError("holdout lacrado; somente a Fase 6 pode liberar a rodada única")
    return scope


def exact_primary_signflip(cluster_slopes: Mapping[str, float]) -> ExactPermutationResult:
    """Teste exato unilateral de H′ por sign-flip dos cinco anos-safra.

    Cada entrada é a inclinação transversal do respectivo ano-safra, calculada sobre todos os
    blocos e quatro grãos. A estatística é a média das cinco inclinações (peso igual por safra).
    Enumeram-se os ``2**5=32`` sinais; portanto não há semente nem aproximação assintótica.
    """
    if set(cluster_slopes) != set(HOLDOUT_CROP_YEARS):
        raise ValueError("teste primário exige exatamente os cinco anos-safra do holdout")
    effects = np.array([float(cluster_slopes[year]) for year in HOLDOUT_CROP_YEARS])
    if not np.isfinite(effects).all():
        raise ValueError("inclinações por safra devem ser finitas")
    observed = float(effects.mean())
    permuted = np.array(
        [float((effects * np.asarray(signs)).mean()) for signs in product((-1.0, 1.0), repeat=5)]
    )
    pvalue = float(np.count_nonzero(permuted >= observed - 1e-15) / len(permuted))
    return ExactPermutationResult(
        statistic=observed,
        pvalue=pvalue,
        permutations=len(permuted),
        passed=observed > 0 and pvalue <= ALPHA,
    )


def spot_participation(
    delta_weight: float, adtv_brl: float, aum_brl: float = REFERENCE_AUM_BRL
) -> float:
    """Participação de uma ordem no ADTV21, usando ``|Δw|`` e patrimônio declarado."""
    if not all(np.isfinite(x) for x in (delta_weight, adtv_brl, aum_brl)):
        raise ValueError("ordem, ADTV e patrimônio devem ser finitos")
    if adtv_brl <= 0 or aum_brl <= 0:
        raise ValueError("ADTV e patrimônio devem ser positivos")
    return abs(float(delta_weight)) * float(aum_brl) / float(adtv_brl)


def one_way_equity_cost_rate(
    delta_weight: float,
    adtv_brl: float,
    aum_brl: float = REFERENCE_AUM_BRL,
    scenario: str = "base",
) -> float:
    """Custo monetário de uma ordem como fração do notional negociado.

    O cenário zero remove custo monetário, mas não a trava de participação. ``double`` dobra o
    custo base inteiro. Ordem acima de 5% do ADTV é inexequível e falha alto.
    """
    if scenario not in COST_SCENARIOS:
        raise ValueError(f"cenário de custo inválido: {scenario!r}")
    participation = spot_participation(delta_weight, adtv_brl, aum_brl)
    if participation > MAX_SPOT_PARTICIPATION + 1e-15:
        raise ValueError("ordem excede 5% do ADTV21")
    if abs(delta_weight) == 0 or scenario == "zero":
        return 0.0
    bps = (
        B3_SPOT_FEE_BPS
        + BROKERAGE_BPS
        + SLIPPAGE_FIXED_BPS
        + IMPACT_BPS_AT_ONE_PERCENT * sqrt(participation / 0.01)
    )
    if scenario == "double":
        bps *= 2.0
    return bps / 10_000.0


def borrow_all_in_rate(observed_rate: float, scenario: str = "base") -> float:
    """Taxa anual do short: contrato PIT com piso + tarifa B3 + intermediação."""
    if scenario not in COST_SCENARIOS:
        raise ValueError(f"cenário de custo inválido: {scenario!r}")
    rate = float(observed_rate)
    if not np.isfinite(rate) or rate < 0:
        raise ValueError("taxa observada de aluguel deve ser finita e não-negativa")
    contract = max(rate, BORROW_RATE_FLOOR)
    b3_fee = float(np.clip(B3_BORROW_FEE_ALPHA * contract, B3_BORROW_FEE_FLOOR, B3_BORROW_FEE_CAP))
    all_in = contract + b3_fee + BORROW_INTERMEDIARY_RATE
    if scenario == "zero":
        return 0.0
    return 2.0 * all_in if scenario == "double" else all_in


def borrow_is_available(
    recent_contract_quantities: Sequence[float],
    stock_brl: float,
    short_notional_brl: float,
) -> bool:
    """Proxy PIT de disponibilidade congelada em D-055.

    Exige ao menos um negócio positivo nos últimos cinco pregões e posição pretendida de no
    máximo 1% do estoque alugado. A função não prova oferta na corretora; apenas implementa a
    condição conservadora e reproduzível escolhida antes do P&L.
    """
    quantities = np.asarray(recent_contract_quantities, dtype=float)
    if quantities.ndim != 1 or quantities.size > BORROW_LOOKBACK_SESSIONS:
        raise ValueError("histórico de aluguel deve conter até cinco pregões")
    if not np.isfinite(quantities).all() or (quantities < 0).any():
        raise ValueError("quantidades de contratos devem ser finitas e não-negativas")
    if not np.isfinite(stock_brl) or stock_brl < 0:
        raise ValueError("estoque alugado deve ser finito e não-negativo")
    if not np.isfinite(short_notional_brl) or short_notional_brl < 0:
        raise ValueError("notional short deve ser finito e não-negativo")
    has_trade = quantities.size > 0 and bool((quantities > 0).any())
    has_depth = short_notional_brl <= MAX_BORROW_STOCK_SHARE * stock_brl + 1e-12
    return has_trade and has_depth


def spot_capacity_brl(adtv_brl: float, delta_weight: float) -> float:
    """Patrimônio máximo imposto pela participação de 5% na ordem à vista."""
    if not np.isfinite(adtv_brl) or adtv_brl < 0 or not np.isfinite(delta_weight):
        raise ValueError("ADTV e peso devem ser finitos e não-negativos onde aplicável")
    return inf if delta_weight == 0 else MAX_SPOT_PARTICIPATION * adtv_brl / abs(delta_weight)


def borrow_capacity_brl(stock_brl: float, short_weight: float) -> float:
    """Patrimônio máximo com posição limitada a 1% do estoque alugado observado."""
    if not np.isfinite(stock_brl) or stock_brl < 0 or not np.isfinite(short_weight):
        raise ValueError("estoque e peso short devem ser finitos")
    if short_weight >= 0:
        return inf
    return MAX_BORROW_STOCK_SHARE * stock_brl / abs(short_weight)


def validate_operational_spec() -> None:
    """Tripwires contra alteração silenciosa de D-055."""
    if HOLDING_SESSIONS != 21 or ANCHOR_MONTH_DAY != (1, 7) or FINAL_SIGNAL_MONTH_DAY != (9, 7):
        raise ValueError("calendário operacional D-055 foi alterado")
    if DEV_CROP_YEARS[-1] != "2018/19" or TRANSITION_CROP_YEAR != "2019/20":
        raise ValueError("partição temporal D-055 foi alterada")
    if CANE_SCALE != 1.0 or CANE_NAME in GRAIN_NAMES:
        raise ValueError("escala ou separação do satélite de cana foi alterada")
    if REFERENCE_AUM_BRL != 500_000 or ADTV_FLOOR_BRL != 8_000_000:
        raise ValueError("patrimônio/piso de ADTV D-055 foi alterado")
    if ADTV_WINDOW != 21 or MAX_SPOT_PARTICIPATION != 0.05:
        raise ValueError("janela/participação de liquidez D-055 foi alterada")
    if PERMUTATION_KIND != "exact_crop_year_sign_flip" or EXPECTED_PERMUTATIONS != 32:
        raise ValueError("inferência exata D-055 foi alterada")


validate_operational_spec()
