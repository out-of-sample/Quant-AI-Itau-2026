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
    INPUT_SUMMARY,
    PACKAGE_ID,
    REQUIRED_INPUTS,
    SOURCE_MANIFEST,
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
    assert report.executor_implemented
    assert len(report.logical_spec_sha256) == 64


def _materialize_synthetic_gate(tmp_path) -> None:
    for relative in SPEC_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"source:{relative}".encode())
    input_records = {}
    for role, relative in REQUIRED_INPUTS.items():
        if role == "input_manifest":
            continue
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"input:{role}".encode())
        attestation = attest_file(path)
        input_records[role] = {
            "path": relative,
            "bytes": attestation.bytes,
            "sha256": attestation.sha256,
        }
    manifest = tmp_path / REQUIRED_INPUTS["input_manifest"]
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_id": PACKAGE_ID,
                "logical_spec_sha256": spec_sha256(),
                "inputs": input_records,
            }
        ),
        encoding="utf-8",
    )
    manifest_sha256 = attest_file(manifest).sha256
    (tmp_path / INPUT_SUMMARY).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_id": PACKAGE_ID,
                "logical_spec_sha256": spec_sha256(),
                "input_manifest": {
                    "path": REQUIRED_INPUTS["input_manifest"],
                    "sha256": manifest_sha256,
                },
            }
        ),
        encoding="utf-8",
    )
    source_records = {}
    for relative in SPEC_FILES:
        attestation = attest_file(tmp_path / relative)
        source_records[relative] = {
            "path": relative,
            "bytes": attestation.bytes,
            "sha256": attestation.sha256,
        }
    source_manifest = tmp_path / SOURCE_MANIFEST
    source_manifest.parent.mkdir(parents=True, exist_ok=True)
    source_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_id": PACKAGE_ID,
                "logical_spec_sha256": spec_sha256(),
                "files": source_records,
            }
        ),
        encoding="utf-8",
    )


def test_preflight_pronto_exige_hashes_de_fontes_e_inputs(tmp_path) -> None:
    _materialize_synthetic_gate(tmp_path)
    report = preflight_holdout(tmp_path)
    assert EXECUTOR_IMPLEMENTED
    assert report.ready
    assert not report.source_manifest_errors
    assert not report.manifest_errors
    require_holdout_ready(report)


def test_preflight_rejeita_adulteracao_de_fonte_e_input(tmp_path) -> None:
    _materialize_synthetic_gate(tmp_path)
    (tmp_path / SPEC_FILES[0]).write_bytes(b"fonte alterado")
    input_path = tmp_path / REQUIRED_INPUTS["returns"]
    input_path.write_bytes(b"input alterado")
    report = preflight_holdout(tmp_path)
    assert not report.ready
    assert any("hash/tamanho divergente no fonte" in item for item in report.source_manifest_errors)
    assert any("hash/tamanho divergente no input" in item for item in report.manifest_errors)
    with pytest.raises(HoldoutLockedError, match="manifesto de fontes"):
        require_holdout_ready(report)


def test_preflight_rejeita_manifesto_de_input_regravado(tmp_path) -> None:
    _materialize_synthetic_gate(tmp_path)
    manifest = tmp_path / REQUIRED_INPUTS["input_manifest"]
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["sources"] = [{"path": "fonte_nao_congelada"}]
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    report = preflight_holdout(tmp_path)
    assert not report.ready
    assert "hash/caminho do manifesto diverge do resumo versionado" in report.manifest_errors


def test_gate_rejeita_demais_estados_mesmo_em_fixture_sintetica() -> None:
    base = preflight_holdout()
    with pytest.raises(HoldoutLockedError, match="arquivos do contrato"):
        require_holdout_ready(
            replace(
                base,
                executor_implemented=True,
                missing_spec_files=("src/missing.py",),
                source_manifest_errors=(),
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
                source_manifest_errors=(),
                missing_inputs=("returns",),
                ready=False,
            )
        )
    with pytest.raises(HoldoutLockedError, match="segunda execução"):
        require_holdout_ready(
            replace(
                base,
                executor_implemented=True,
                missing_spec_files=(),
                source_manifest_errors=(),
                missing_inputs=(),
                manifest_errors=(),
                run_record_exists=True,
                ready=False,
            )
        )
