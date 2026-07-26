"""Testes do spec congelado da suíte de robustez de H1 (D-065)."""

from __future__ import annotations

import pytest

from quantagro.stats.robustness_spec import (
    MAGNITUDE_BAND,
    PERTURBATIONS,
    PLACEBOS,
    REAL_PERTURBATIONS,
    Perturbation,
    overall_robust,
    perturbation_verdict,
)


def test_grid_is_single_knob_and_has_baseline_and_placebos() -> None:
    baselines = [p for p in PERTURBATIONS if p.family == "baseline"]
    assert len(baselines) == 1
    assert len(PLACEBOS) == 2  # espacial + temporal
    assert len(REAL_PERTURBATIONS) >= 5
    # __post_init__ já garante single-knob; aqui garantimos nomes únicos.
    names = [p.name for p in PERTURBATIONS]
    assert len(names) == len(set(names))


def test_perturbation_rejects_multi_knob() -> None:
    with pytest.raises(ValueError, match="exatamente um botão"):
        Perturbation("bad", "real", climatology_first_year_delta=-2, extra_lag_days=14)


def test_perturbation_rejects_baseline_with_knob() -> None:
    with pytest.raises(ValueError, match="nenhum botão"):
        Perturbation("bad", "baseline", extra_lag_days=1)


def test_placebo_field_must_match_family() -> None:
    with pytest.raises(ValueError, match="placebo e family"):
        Perturbation("bad", "real", placebo="spatial")


def test_real_verdict_in_band_passes() -> None:
    pert = REAL_PERTURBATIONS[0]
    v = perturbation_verdict(pert, beta=-0.06, boot_pvalue=0.01, baseline_abs_beta=0.067)
    assert v.passed and v.flag == ""


def test_real_verdict_sign_flip_fails() -> None:
    pert = REAL_PERTURBATIONS[0]
    v = perturbation_verdict(pert, beta=+0.05, boot_pvalue=0.2, baseline_abs_beta=0.067)
    assert not v.passed and v.flag == "sinal invertido"


def test_real_verdict_out_of_band_fails() -> None:
    pert = REAL_PERTURBATIONS[0]
    lo, hi = MAGNITUDE_BAND
    # |β| enorme: fora da banda superior mesmo com sinal certo.
    v = perturbation_verdict(
        pert, beta=-0.067 * (hi + 1), boot_pvalue=0.01, baseline_abs_beta=0.067
    )
    assert not v.passed and "fora da banda" in v.flag


def test_placebo_dies_correctly() -> None:
    pert = PLACEBOS[0]
    v = perturbation_verdict(pert, beta=-0.005, boot_pvalue=0.6, baseline_abs_beta=0.067)
    assert v.passed and v.flag == ""


def test_placebo_that_survives_is_flagged() -> None:
    pert = PLACEBOS[0]
    # β grande e significativo sob placebo = bandeira vermelha.
    v = perturbation_verdict(pert, beta=-0.05, boot_pvalue=0.01, baseline_abs_beta=0.067)
    assert not v.passed and "não morreu" in v.flag


def test_overall_robust_true_when_all_good() -> None:
    verdicts = []
    for pert in REAL_PERTURBATIONS:
        verdicts.append(perturbation_verdict(pert, -0.06, 0.02, 0.067))
    for pert in PLACEBOS:
        verdicts.append(perturbation_verdict(pert, -0.005, 0.7, 0.067))
    assert overall_robust(verdicts)


def test_overall_robust_false_when_placebo_survives() -> None:
    verdicts = [perturbation_verdict(p, -0.06, 0.02, 0.067) for p in REAL_PERTURBATIONS]
    verdicts.append(perturbation_verdict(PLACEBOS[0], -0.05, 0.01, 0.067))  # sobrevive
    verdicts.append(perturbation_verdict(PLACEBOS[1], -0.005, 0.7, 0.067))
    assert not overall_robust(verdicts)
