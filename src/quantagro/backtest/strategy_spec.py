"""Contrato congelado da estratégia reformulada (D-053), pré-registrado ANTES do holdout.

Este módulo é a especificação executável e imutável da estratégia sob H′ (D-044). Ele é
**return-agnóstico**: não lê retorno de ação nem toca o holdout 2020–2025. Sua função é fixar,
num commit anterior ao primeiro contato com o holdout, todas as escolhas de desenho — universo,
direção operacional, canal por nome, sizing, execução e o teste estatístico primário — de modo
que a rodada única no holdout não tenha nenhum grau de liberdade ajustável.

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
    w = target * d_side / d_side.sum()
    for _ in range(100):
        over = w > cap_side + 1e-15
        if not over.any():
            break
        w[over] = cap_side[over]
        free = ~over
        rem = target - float(w[over].sum())
        denom = float(d_side[free].sum())
        if free.sum() == 0 or denom <= 0.0:
            break
        w[free] = rem * d_side[free] / denom
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
    s = np.array([float(scores[n]) for n in names])
    cap = np.array([float(caps[n]) for n in names])
    d = s - s.mean()
    long_m = d > 0
    short_m = d < 0
    if not long_m.any() or not short_m.any():
        return {n: 0.0 for n in names}  # sem os dois lados não há carteira dollar-neutral
    g = min(0.5, float(cap[long_m].sum()), float(cap[short_m].sum()))
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
    if PRIMARY_TEST_UNIVERSE != GRAIN_NAMES:
        raise ValueError("teste primário deve ser só grãos (A1 protege a força)")
    if not TEST_IS_ONE_SIDED or not (0.0 < ALPHA < 0.5):
        raise ValueError("teste primário deve ser unilateral com α em (0, 0.5)")
    if NATIONAL_SHOCK_WEIGHTING != "conab":
        raise ValueError("peso do choque nacional deve ser o contrato CONAB (D-028)")
    if len(HOLDOUT_CROP_YEARS) != 5:
        raise ValueError("holdout deve ter exatamente 5 anos-safra")


validate_strategy_spec()
