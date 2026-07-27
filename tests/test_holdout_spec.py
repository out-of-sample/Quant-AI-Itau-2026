"""Invariantes do pacote de rodada única D-068, sem tocar retornos."""

from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256

import pytest

from quantagro.backtest.holdout import (
    attest_file,
    preflight_holdout,
    require_holdout_ready,
)
from quantagro.backtest.holdout_spec import (
    ANALYSIS_STEPS,
    CLAIM_REQUIREMENTS,
    EXECUTOR_IMPLEMENTED,
    EXPECTED_LOGICAL_SPEC_SHA256,
    H4_EXTENDED_CONTROLS,
    H4_VETO_SPEC,
    H5_GEOGRAPHIC_PLACEBO,
    H5_INFERENCE,
    H5_STATISTIC,
    H5_VETO,
    PACKAGE_ID,
    REQUIRED_INPUTS,
    SPEC_FILES,
    canonical_spec_payload,
    spec_sha256,
    validate_holdout_spec,
)
from quantagro.backtest.operational_spec import HoldoutLockedError


def test_spec_tem_um_confirmatorio_e_continua_depois_de_falha() -> None:
    validate_holdout_spec()
    assert [step.name for step in ANALYSIS_STEPS if step.role == "confirmatory"] == [
        "primary_hprime"
    ]
    assert [step.order for step in ANALYSIS_STEPS] == list(range(len(ANALYSIS_STEPS)))
    assert [step.name for step in ANALYSIS_STEPS] == [
        "preflight",
        "primary_hprime",
        "portfolio_cost_scenarios",
        "liquidity_d067",
        "sector_climate_d064",
        "h4_spanning",
        "h5_placebos",
        "leave_one_name_out",
        "leave_one_crop_year_out",
        "parameter_sensitivities",
        "metrics_attribution",
        "seal_result",
    ]
    assert canonical_spec_payload()["continue_after_primary_failure"]
    assert not canonical_spec_payload()["allow_intermediate_result_display"]


def test_h4_h5_e_claim_climatico_sao_vetos_explicitos() -> None:
    assert H4_VETO_SPEC == "extended"
    assert "rm_minus_rf" in H4_EXTENDED_CONTROLS
    assert "ibov" not in H4_EXTENDED_CONTROLS
    assert H5_VETO == H5_GEOGRAPHIC_PLACEBO
    assert H5_STATISTIC == "mean_crop_year_base_net_return"
    assert H5_INFERENCE == "exact_crop_year_sign_flip"
    assert CLAIM_REQUIREMENTS["climate_alpha_evidence"] == (
        "base_net_return_positive",
        "primary_hprime_passed",
        "d064_climate_component_positive",
        "h4_extended_passed",
        "h5_geographic_died",
    )


def test_hash_logico_e_deterministico() -> None:
    first = spec_sha256()
    second = spec_sha256()
    expected = sha256(
        json.dumps(
            canonical_spec_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    assert first == second == expected
    assert first == EXPECTED_LOGICAL_SPEC_SHA256
    assert len(first) == 64
    assert canonical_spec_payload()["package_id"] == PACKAGE_ID


def test_atestacao_hash_sem_parsear_conteudo(tmp_path) -> None:
    payload = b"isto nao e parquet e nao deve ser interpretado"
    path = tmp_path / "sealed.parquet"
    path.write_bytes(payload)
    attestation = attest_file(path, chunk_bytes=7)
    assert attestation.bytes == len(payload)
    assert attestation.sha256 == sha256(payload).hexdigest()
    with pytest.raises(ValueError, match="positivo"):
        attest_file(path, chunk_bytes=0)


def test_preflight_lista_ausencias_e_nao_fica_pronto(tmp_path) -> None:
    report = preflight_holdout(tmp_path)
    assert report.missing_spec_files == SPEC_FILES
    assert report.missing_inputs == tuple(REQUIRED_INPUTS)
    assert not report.present_inputs
    assert not report.run_record_exists
    assert not report.ready
    assert not report.executor_implemented
    assert len(report.logical_spec_sha256) == 64


def test_execucao_falha_pelo_executor_antes_dos_inputs() -> None:
    report = preflight_holdout()
    assert not EXECUTOR_IMPLEMENTED
    with pytest.raises(HoldoutLockedError, match="ainda não implementado"):
        require_holdout_ready(report)


def test_gate_rejeita_demais_estados_mesmo_em_fixture_sintetica() -> None:
    base = preflight_holdout()
    with pytest.raises(HoldoutLockedError, match="arquivos do contrato"):
        require_holdout_ready(
            replace(
                base,
                executor_implemented=True,
                missing_spec_files=("src/missing.py",),
                missing_inputs=(),
                ready=False,
            )
        )
    with pytest.raises(HoldoutLockedError, match="inputs do holdout"):
        require_holdout_ready(
            replace(
                base,
                executor_implemented=True,
                missing_spec_files=(),
                ready=False,
            )
        )
    with pytest.raises(HoldoutLockedError, match="segunda execução"):
        require_holdout_ready(
            replace(
                base,
                executor_implemented=True,
                missing_spec_files=(),
                missing_inputs=(),
                run_record_exists=True,
                ready=False,
            )
        )
