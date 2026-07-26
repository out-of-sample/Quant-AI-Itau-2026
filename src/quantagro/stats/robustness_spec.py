"""Suíte de robustez do sinal H1 — grid de perturbações e critérios, congelados (D-065).

**Return-agnóstico.** Testa o **mecanismo** clima→revisão CONAB (H1a), não retornos: o holdout de
retornos permanece lacrado; a leitura por sub-amostra segue a separação dev(≤2019/20)/holdout
(≥2020/21) de D-029, reportada mas não usada para escolher nada.

**Disciplina (pré-registro).** Cada perturbação desvia **um único botão** do baseline congelado de
H1a (D-030): não se procura o botão que maximiza β. O objetivo é mostrar que o β do desenho já
congelado **preserva sinal e ordem de grandeza** sob perturbações razoáveis, e que **placebos
matam** o sinal. Os critérios abaixo são fixados ANTES de rodar — este módulo é anterior à
materialização dos resultados (padrão do projeto: critério num commit anterior ao número).

Grid (todos single-knob a partir do baseline):
  - baseline: o spec de H1a de D-030 (prelim, climatologia congelada, janelas PRIMARY_WINDOWS).
  - real: climatologia ±2 anos; fonte final vs prelim (com ressalva de vintage R15/R16); lag de
    disponibilidade +14 dias; janela crítica deslocada ±15 dias.
  - placebo: espacial (embaralha o Shock entre UFs dentro do ano-safra) e temporal (usa o Shock do
    ano-safra anterior). Ambos devem colapsar para ~0.

Critérios (frozen):
  - perturbação **real** passa se o β agrupado no span cheio mantém o sinal esperado (β<0) E
    |β|/|β_base| ∈ [0,4; 2,5]. O dev é reportado como descritivo (N minúsculo), não decide.
  - **placebo** comporta-se corretamente se |β|/|β_base| < 0,5 E o bootstrap p > α (não
    significativo). Placebo significativo e de mesmo sinal = BANDEIRA VERMELHA (resultado mecânico).
  - veredito global "robusto" = todas as reais preservam o sinal, ≥5/6 ficam na banda, e os dois
    placebos morrem.
"""

from __future__ import annotations

from dataclasses import dataclass

EXPECTED_SIGN = -1  # estresse (Shock>0) ⇒ revisão de produção para baixo (logrev<0)
MAGNITUDE_BAND = (0.4, 2.5)  # |β|/|β_base| aceitável para uma perturbação real
PLACEBO_MAX_RATIO = 0.5  # placebo deve ter |β| abaixo desta fração do baseline
ALPHA = 0.10  # placebo significativo abaixo disto = bandeira vermelha
MIN_REAL_IN_BAND = 5  # das perturbações reais, quantas devem ficar na banda


@dataclass(frozen=True)
class Perturbation:
    """Um desvio single-knob do baseline de H1a. Todos os campos default = baseline congelado."""

    name: str
    family: str  # "baseline" | "real" | "placebo"
    climatology_first_year_delta: int = 0
    signal_kind: str = "prelim"  # "prelim" | "final"
    extra_lag_days: int = 0
    window_shift_days: int = 0
    placebo: str = "none"  # "none" | "spatial" | "temporal"
    note: str = ""

    def __post_init__(self) -> None:
        if self.family not in {"baseline", "real", "placebo"}:
            raise ValueError(f"family inválida: {self.family!r}")
        if self.signal_kind not in {"prelim", "final"}:
            raise ValueError(f"signal_kind inválido: {self.signal_kind!r}")
        if self.placebo not in {"none", "spatial", "temporal"}:
            raise ValueError(f"placebo inválido: {self.placebo!r}")
        knobs = [
            self.climatology_first_year_delta != 0,
            self.signal_kind != "prelim",
            self.extra_lag_days != 0,
            self.window_shift_days != 0,
            self.placebo != "none",
        ]
        active = sum(1 for k in knobs if k)
        if self.family == "baseline" and active != 0:
            raise ValueError("baseline não pode mexer em nenhum botão")
        if self.family != "baseline" and active != 1:
            raise ValueError(
                f"{self.name}: perturbação deve mexer em exatamente um botão, viu {active}"
            )
        if (self.placebo != "none") != (self.family == "placebo"):
            raise ValueError(f"{self.name}: campo placebo e family precisam concordar")


PERTURBATIONS: tuple[Perturbation, ...] = (
    Perturbation(
        "baseline", "baseline", note="spec H1a de D-030 (prelim, climatologia e janelas congeladas)"
    ),
    Perturbation(
        "clima_mais_longa",
        "real",
        climatology_first_year_delta=-2,
        note="climatologia começa 2 anos antes (baseline mais longo)",
    ),
    Perturbation(
        "clima_mais_curta",
        "real",
        climatology_first_year_delta=+2,
        note="climatologia começa 2 anos depois (ainda ≥10 safras)",
    ),
    Perturbation(
        "fonte_final",
        "real",
        signal_kind="final",
        note="sinal da série final vs prelim; ressalva de vintage R15/R16 na leitura",
    ),
    Perturbation(
        "lag_mais_14d", "real", extra_lag_days=14, note="disponibilidade 14 dias mais conservadora"
    ),
    Perturbation(
        "janela_menos_15d",
        "real",
        window_shift_days=-15,
        note="período crítico deslocado 15 dias para trás",
    ),
    Perturbation(
        "janela_mais_15d",
        "real",
        window_shift_days=+15,
        note="período crítico deslocado 15 dias para frente",
    ),
    Perturbation(
        "placebo_espacial",
        "placebo",
        placebo="spatial",
        note="Shock embaralhado entre UFs no mesmo ano-safra; deve morrer",
    ),
    Perturbation(
        "placebo_temporal",
        "placebo",
        placebo="temporal",
        note="Shock do ano-safra anterior; deve morrer",
    ),
)

REAL_PERTURBATIONS = tuple(p for p in PERTURBATIONS if p.family == "real")
PLACEBOS = tuple(p for p in PERTURBATIONS if p.family == "placebo")


@dataclass(frozen=True)
class PerturbationVerdict:
    name: str
    family: str
    beta: float
    ratio: float  # |β| / |β_base|
    boot_pvalue: float
    passed: bool  # real: na banda e sinal certo; placebo: morreu como devia
    flag: str  # "" ou motivo da falha/bandeira


def perturbation_verdict(
    pert: Perturbation, beta: float, boot_pvalue: float, baseline_abs_beta: float
) -> PerturbationVerdict:
    """Aplica o critério congelado a um β observado. Não decide desenho — só classifica."""
    if baseline_abs_beta <= 0:
        raise ValueError("baseline_abs_beta precisa ser > 0")
    ratio = abs(beta) / baseline_abs_beta
    lo, hi = MAGNITUDE_BAND
    if pert.family == "placebo":
        died = ratio < PLACEBO_MAX_RATIO and boot_pvalue > ALPHA
        flag = "" if died else "placebo não morreu (|β| alto ou significativo)"
        return PerturbationVerdict(pert.name, pert.family, beta, ratio, boot_pvalue, died, flag)
    sign_ok = (beta < 0) if EXPECTED_SIGN < 0 else (beta > 0)
    in_band = lo <= ratio <= hi
    passed = sign_ok and in_band
    if not sign_ok:
        flag = "sinal invertido"
    elif not in_band:
        flag = f"fora da banda [{lo}, {hi}] (ratio {ratio:.2f})"
    else:
        flag = ""
    return PerturbationVerdict(pert.name, pert.family, beta, ratio, boot_pvalue, passed, flag)


def overall_robust(verdicts: list[PerturbationVerdict]) -> bool:
    """Veredito global: reais preservam sinal, ≥MIN_REAL_IN_BAND na banda, placebos morrem."""
    reals = [v for v in verdicts if v.family == "real"]
    placebos = [v for v in verdicts if v.family == "placebo"]
    signs_ok = all((v.beta < 0) if EXPECTED_SIGN < 0 else (v.beta > 0) for v in reals)
    in_band = sum(1 for v in reals if v.passed)
    placebos_died = all(v.passed for v in placebos)
    return signs_ok and in_band >= MIN_REAL_IN_BAND and placebos_died
