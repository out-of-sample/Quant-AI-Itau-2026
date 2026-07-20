"""Contrato congelado da estratégia reformulada (D-053), pré-registrado ANTES do holdout.

Este módulo é a especificação executável e imutável da estratégia sob H′ (D-044). Ele é
**return-agnóstico**: não lê retorno de ação nem toca o holdout 2020–2025. Sua função é fixar,
num commit anterior ao primeiro contato com o holdout, as escolhas econômicas de D-053 —
universo, direção operacional, canal por nome, sizing, execução e teste estatístico primário.
A auditoria D-054 separa deste contrato a mecânica operacional ainda a fechar na Fase 4.0
(calendário, score multicanal, custos, permutação e fronteiras temporais).

Camadas de sinal (não confundir):

1. `signal/convention.py::raw_signal = E·Shock` — convenção de MECANISMO, travada em
   `tests/test_signal_sign.py`. Representa o canal de PREÇO (produtor sobe sob estresse), que foi
   **falsificado** em D-043. **Não é alterado aqui.**
2. Esta camada operacional H′ (D-044): para grãos, a estratégia toma o **negativo** de `E·Shock`
   (a seca prejudica o produtor — `Q>P`); para a cana (SMTO3), um canal próprio de maturação com
   direção +1 (seca → ATR↑ → long). A convenção de mecanismo permanece intacta; H′ é um sinal
   multiplicativo por cima.

Decisões de desenho congeladas (todas em docs/07 D-053; forks resolvidos com o time):

- **A1 — cana como satélite capado**: o TESTE estatístico primário usa só os 4 grãos (spread
  produtor–processador), para o mecanismo fraco da cana (p=0,12) não diluir o sinal forte. A
  CARTEIRA negociável inclui a SMTO3, mas com `|peso| ≤ 0,15` (D-052 põe a SMTO3 "no score").
- **B1 — sizing proporcional ao sinal, dollar-neutral, cap 0,40 por grão** (resolve R19).
- pesos do choque nacional = contrato CONAB da safra anterior (D-028), não equal-weight.
- execução D+1; horizonte forward de 21 pregões.
- teste primário = painel/spread `Shock×exposição` demeanado na seção transversal, cluster por
  ano-safra, **inferência por permutação**, **unilateral** α=0,10 (direção dada por H′).
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

# --- universo (D-052) -------------------------------------------------------------------
GRAIN_NAMES: tuple[str, ...] = ("AGRO3", "SLCE3", "BRFS3", "JBSS3")
CANE_NAME: str = "SMTO3"
UNIVERSE: tuple[str, ...] = GRAIN_NAMES + (CANE_NAME,)

# --- direção operacional H′ (D-044) -----------------------------------------------------
# A estratégia de grãos é o NEGATIVO de E·Shock: a seca prejudica o produtor (Q>P). O sinal de
# mecanismo (signal/convention.py) NÃO muda; esta é a camada operacional por cima.
H_PRIME_GRAIN_SIGN: float = -1.0
# Cana: canal de maturação, seca → ATR↑ → long o produtor de cana.
CANE_SUBMODEL_SIGN: float = +1.0

# --- sizing / R19 (B1) ------------------------------------------------------------------
GRAIN_NAME_CAP: float = 0.40  # |peso| máximo por nome de grão
CANE_SATELLITE_CAP: float = 0.15  # |peso| máximo da SMTO3 (satélite; A1)
GROSS: float = 1.0  # Σ|w| = 1
PER_NAME_CAP: dict[str, float] = {n: GRAIN_NAME_CAP for n in GRAIN_NAMES} | {
    CANE_NAME: CANE_SATELLITE_CAP
}

# --- execução ---------------------------------------------------------------------------
EXEC_LAG_DAYS: int = 1  # sinal com avail_date ≤ D executa no close de D+1
FWD_HORIZON_DAYS: int = 21

# --- choque nacional (D-028) ------------------------------------------------------------
NATIONAL_SHOCK_WEIGHTING: str = "conab"  # pesos da safra CONAB anterior, não "equal"

# --- holdout lacrado --------------------------------------------------------------------
HOLDOUT_CROP_YEARS: tuple[str, ...] = (
    "2020/21",
    "2021/22",
    "2022/23",
    "2023/24",
    "2024/25",
)

# --- teste estatístico primário (substitui H3/Fama-MacBeth; docs/14 §6) -----------------
PRIMARY_TEST_UNIVERSE: tuple[str, ...] = GRAIN_NAMES  # só grãos: protege a força (A1)
PRIMARY_TEST: str = "producer_processor_spread_panel"
INFERENCE: str = "permutation_cluster_by_crop_year"
TEST_IS_ONE_SIDED: bool = True
ALPHA: float = 0.10
CLUSTER_BY: str = "ano_agricola"


def operational_grain_score(raw_e_dot_shock: float | np.ndarray):
    """Score operacional de grão sob H′: negativo do sinal de mecanismo `E·Shock`.

    ``raw_e_dot_shock`` vem de ``signal.convention.raw_signal`` (já somado sobre culturas). H′
    inverte para a direção econômica derivada em D-044; a convenção de mecanismo fica intacta.
    """
    return H_PRIME_GRAIN_SIGN * np.asarray(raw_e_dot_shock, dtype=float)


def operational_cane_score(cane_shock: float | np.ndarray):
    """Score operacional da cana: seca de maturação (`shock>0`) → long (direção +1, D-051)."""
    return CANE_SUBMODEL_SIGN * np.asarray(cane_shock, dtype=float)


def _fill_side(d_side: np.ndarray, cap_side: np.ndarray, target: float) -> np.ndarray:
    """Water-filling: distribui ``target`` de bruto ∝ ``d_side``, respeitando o cap por nome.

    ``target ≤ Σ cap_side`` (garantido pelo chamador) ⇒ converge para soma exata ``target``.
    """
    d_side = np.asarray(d_side, dtype=float)
    cap_side = np.asarray(cap_side, dtype=float)
    if d_side.ndim != 1 or cap_side.shape != d_side.shape:
        raise ValueError("demandas e caps devem ser vetores unidimensionais do mesmo tamanho")
    if not np.isfinite(d_side).all() or not np.isfinite(cap_side).all():
        raise ValueError("demandas e caps devem ser finitos")
    if (d_side <= 0.0).any() or (cap_side < 0.0).any():
        raise ValueError("demandas devem ser positivas e caps não-negativos")
    if not np.isfinite(target) or target < 0.0 or target > float(cap_side.sum()) + 1e-12:
        raise ValueError("target inválido ou incompatível com a soma dos caps")

    # Um nome que bateu no cap fica travado. Recalcular `over` sobre todos os nomes a cada
    # iteração faria um nome já capado voltar ao conjunto livre e poderia violar o próprio cap.
    w = np.zeros_like(d_side)
    free = np.ones(d_side.size, dtype=bool)
    for _ in range(d_side.size + 1):
        remaining = target - float(w[~free].sum())
        if remaining <= 1e-15 or not free.any():
            break
        free_idx = np.flatnonzero(free)
        proposal = remaining * d_side[free] / float(d_side[free].sum())
        newly_capped = proposal > cap_side[free] + 1e-15
        if not newly_capped.any():
            w[free] = proposal
            break
        capped_idx = free_idx[newly_capped]
        w[capped_idx] = cap_side[capped_idx]
        free[capped_idx] = False

    if (w > cap_side + 1e-12).any() or not np.isclose(w.sum(), target, atol=1e-12):
        raise RuntimeError("water-filling não satisfez soma e caps do contrato")
    return w


def dollar_neutral_weights(
    scores: Mapping[str, float], caps: Mapping[str, float] | None = None
) -> dict[str, float]:
    """Pesos dollar-neutral proporcionais ao sinal, com cap por nome (B1). Return-agnóstico.

    Regra congelada: demean na seção transversal; os lados long e short recebem, cada um, o
    mesmo bruto ``g`` (⇒ Σw=0 e dollar-neutral por construção), com ``g = min(0,5, Σcap_long,
    Σcap_short)`` — alvo 0,5 por lado (Σ|w|=1), reduzido só se um cap tornar isso inviável (ex.:
    data só-cana, satélite capado em 0,15). Dentro de cada lado, peso ∝ ao sinal com water-filling
    do cap. Determinística; não usa retorno. Com os 5 nomes vivos no holdout, ``g=0,5`` e o cap
    raramente ativa.
    """
    if caps is None:
        caps = PER_NAME_CAP
    names = list(scores)
    if not names:
        return {}
    unknown = sorted(set(names) - set(UNIVERSE))
    if unknown:
        raise ValueError(f"tickers fora do universo congelado: {unknown}")
    missing_caps = sorted(set(names) - set(caps))
    if missing_caps:
        raise ValueError(f"caps ausentes para: {missing_caps}")
    s = np.array([float(scores[n]) for n in names])
    cap = np.array([float(caps[n]) for n in names])
    if not np.isfinite(s).all():
        raise ValueError("scores devem ser finitos")
    if not np.isfinite(cap).all() or (cap < 0.0).any():
        raise ValueError("caps devem ser finitos e não-negativos")
    d = s - s.mean()
    long_m = d > 0
    short_m = d < 0
    if not long_m.any() or not short_m.any():
        return {n: 0.0 for n in names}  # sem os dois lados não há carteira dollar-neutral
    g = min(GROSS / 2.0, float(cap[long_m].sum()), float(cap[short_m].sum()))
    w = np.zeros_like(d)
    w[long_m] = _fill_side(d[long_m], cap[long_m], g)
    w[short_m] = -_fill_side(-d[short_m], cap[short_m], g)
    return {n: float(wi) for n, wi in zip(names, w, strict=True)}


def validate_strategy_spec() -> None:
    """Tripwires contra mudança silenciosa do contrato congelado."""
    if UNIVERSE != GRAIN_NAMES + (CANE_NAME,) or len(set(UNIVERSE)) != 5:
        raise ValueError("universo da estratégia fora do contrato D-052/D-053")
    if H_PRIME_GRAIN_SIGN != -1.0 or CANE_SUBMODEL_SIGN != 1.0:
        raise ValueError("direção operacional H′ alterada sem decisão")
    if not (0.0 < CANE_SATELLITE_CAP <= GRAIN_NAME_CAP <= 1.0):
        raise ValueError("caps de sizing inconsistentes (cana ≤ grão ≤ 1)")
    if GROSS != 1.0:
        raise ValueError("bruto deve permanecer 1,0 no contrato D-053")
    if EXEC_LAG_DAYS != 1 or FWD_HORIZON_DAYS != 21:
        raise ValueError("execução deve permanecer D+1 e horizonte em 21 pregões")
    if PRIMARY_TEST_UNIVERSE != GRAIN_NAMES:
        raise ValueError("teste primário deve ser só grãos (A1 protege a força)")
    if PRIMARY_TEST != "producer_processor_spread_panel":
        raise ValueError("estatística primária alterada sem decisão")
    if INFERENCE != "permutation_cluster_by_crop_year" or CLUSTER_BY != "ano_agricola":
        raise ValueError("inferência primária alterada sem decisão")
    if not TEST_IS_ONE_SIDED or not (0.0 < ALPHA < 0.5):
        raise ValueError("teste primário deve ser unilateral com α em (0, 0.5)")
    if NATIONAL_SHOCK_WEIGHTING != "conab":
        raise ValueError("peso do choque nacional deve ser o contrato CONAB (D-028)")
    if len(HOLDOUT_CROP_YEARS) != 5:
        raise ValueError("holdout deve ter exatamente 5 anos-safra")


validate_strategy_spec()
