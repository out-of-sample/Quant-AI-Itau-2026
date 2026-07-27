"""Executor civil e atômico da rodada única do holdout.

O comando só atravessa o gate com a frase exata congelada. Antes de abrir qualquer parquet,
cria ``RUN_RECORD`` de modo exclusivo; sucesso ou falha consomem a tentativa. Os blocos 0–10
ficam numa pasta temporária no mesmo filesystem e só aparecem em ``WORK_DIR`` por um único
``os.replace`` depois que o selo 11 foi calculado.
"""

from __future__ import annotations

import hmac
import json
import os
import shutil
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .holdout import attest_file, preflight_holdout, require_holdout_ready
from .holdout_analysis import load_holdout_inputs, run_all_analyses
from .holdout_spec import (
    ANALYSIS_STEPS,
    AUTHORIZATION_PHRASE,
    CLAIM_REQUIREMENTS,
    NEXT_ATTEMPT,
    PACKAGE_ID,
    PRIOR_ATTEMPTS,
    RESULT_RECORD,
    RUN_RECORD,
    WORK_DIR,
)
from .operational_spec import HoldoutLockedError


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _json_safe(value: Any) -> Any:
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _encoded_json(payload: dict[str, object]) -> bytes:
    safe = _json_safe(payload)
    return (
        json.dumps(
            safe,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(_encoded_json(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        _fsync_directory(path.parent)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def _create_run_record_exclusive(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o644)
    except FileExistsError as exc:
        raise HoldoutLockedError(
            "registro da rodada única já existe; nova tentativa proibida"
        ) from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(_encoded_json(payload))
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_directory(path.parent)
    except BaseException:
        # A existência do registro é intencional mesmo se a gravação/execução falhar: a
        # tentativa foi consumida e exige auditoria humana, não repetição automática.
        raise


def _write_staged_json(path: Path, payload: dict[str, object]) -> None:
    with path.open("xb") as handle:
        handle.write(_encoded_json(payload))
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _claims(artifacts: list[dict[str, object]]) -> tuple[dict[str, bool], dict[str, bool]]:
    conditions = {
        "base_net_return_positive": bool(artifacts[2]["scenarios"]["base"]["total_return"] > 0),
        "primary_hprime_passed": bool(artifacts[1]["passed"]),
        "d064_climate_component_positive": bool(artifacts[4]["climate_arith_return"] > 0),
        "h4_extended_passed": bool(artifacts[5]["extended"]["passed"]),
        "h5_geographic_died": bool(artifacts[6]["geographic"]["died"]),
    }
    claims = {
        name: all(conditions[condition] for condition in required)
        for name, required in CLAIM_REQUIREMENTS.items()
    }
    return conditions, claims


def _preflight_payload(report) -> dict[str, object]:
    return {
        "logical_spec_sha256": report.logical_spec_sha256,
        "source_attestations": [asdict(item) for item in report.source_attestations],
        "source_manifest_sha256": report.source_manifest_sha256,
        "input_attestations": [asdict(item) for item in report.input_attestations],
        "input_manifest_sha256": report.input_manifest_sha256,
        "executor_implemented": report.executor_implemented,
        "ready_at_start": report.ready,
    }


def execute_holdout_once(
    root: str | Path,
    *,
    authorization: str,
) -> dict[str, object]:
    """Consome a única tentativa e emite o pacote selado sem resultado intermediário."""
    if not hmac.compare_digest(authorization.encode("utf-8"), AUTHORIZATION_PHRASE.encode("utf-8")):
        raise HoldoutLockedError("frase civil ausente ou divergente; nenhum input foi aberto")

    base = Path(root)
    report = preflight_holdout(base)
    require_holdout_ready(report)
    run_path = base / RUN_RECORD
    result_path = base / RESULT_RECORD
    final_dir = base / WORK_DIR
    if final_dir.exists() or result_path.exists():
        raise HoldoutLockedError("saída/result record preexistente; rodada não pode começar")
    for prior in PRIOR_ATTEMPTS:
        archived = base / str(prior["record"])
        if not archived.exists():
            raise HoldoutLockedError(
                f"registro da tentativa {prior['attempt']} sumiu de {prior['record']}; "
                "apagar trilha de tentativa é proibido"
            )

    started_at = _utc_now()
    run_record: dict[str, object] = {
        "schema_version": 1,
        "package_id": PACKAGE_ID,
        "status": "started",
        "attempt": NEXT_ATTEMPT,
        "prior_attempts": [dict(item) for item in PRIOR_ATTEMPTS],
        "started_at": started_at,
        "logical_spec_sha256": report.logical_spec_sha256,
        "input_manifest_sha256": report.input_manifest_sha256,
        "authorization_sha256": sha256(authorization.encode("utf-8")).hexdigest(),
        "source_attestations": [asdict(item) for item in report.source_attestations],
        "source_manifest_sha256": report.source_manifest_sha256,
        "input_attestations": [asdict(item) for item in report.input_attestations],
    }
    _create_run_record_exclusive(run_path, run_record)

    final_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".holdout_v1_staging_", dir=final_dir.parent))
    published = False
    try:
        inputs = load_holdout_inputs(base)
        artifacts = run_all_analyses(inputs, _preflight_payload(report))
        if len(artifacts) != len(ANALYSIS_STEPS) - 1:
            raise RuntimeError("executor não produziu exatamente os blocos 0–10")

        artifact_hashes: dict[str, str] = {}
        for step, payload in zip(ANALYSIS_STEPS[:-1], artifacts, strict=True):
            envelope = {
                "package_id": PACKAGE_ID,
                "order": step.order,
                "name": step.name,
                "role": step.role,
                "payload": payload,
            }
            output = staging / step.output
            _write_staged_json(output, envelope)
            artifact_hashes[step.output] = attest_file(output).sha256

        conditions, claims = _claims(artifacts)
        sealed_at = _utc_now()
        seal_payload = {
            "package_id": PACKAGE_ID,
            "logical_spec_sha256": report.logical_spec_sha256,
            "source_manifest_sha256": report.source_manifest_sha256,
            "input_manifest_sha256": report.input_manifest_sha256,
            "started_at": started_at,
            "sealed_at": sealed_at,
            "artifact_sha256": artifact_hashes,
            "conditions": conditions,
            "claims": claims,
        }
        seal_step = ANALYSIS_STEPS[-1]
        seal_envelope = {
            "package_id": PACKAGE_ID,
            "order": seal_step.order,
            "name": seal_step.name,
            "role": seal_step.role,
            "payload": seal_payload,
        }
        seal_path = staging / seal_step.output
        _write_staged_json(seal_path, seal_envelope)
        seal_sha = attest_file(seal_path).sha256

        observed = sorted(path.name for path in staging.iterdir() if path.is_file())
        expected = sorted(step.output for step in ANALYSIS_STEPS)
        if observed != expected:
            raise RuntimeError("staging não contém exatamente os 12 artefatos congelados")
        _fsync_directory(staging)
        os.replace(staging, final_dir)
        _fsync_directory(final_dir.parent)
        published = True

        result_record = {
            "schema_version": 1,
            "package_id": PACKAGE_ID,
            "status": "sealed",
            "sealed_at": sealed_at,
            "logical_spec_sha256": report.logical_spec_sha256,
            "source_manifest_sha256": report.source_manifest_sha256,
            "input_manifest_sha256": report.input_manifest_sha256,
            "work_dir": WORK_DIR,
            "seal_sha256": seal_sha,
            "artifact_sha256": artifact_hashes | {seal_step.output: seal_sha},
            "conditions": conditions,
            "claims": claims,
        }
        _atomic_write_json(result_path, result_record)
        result_attestation = attest_file(result_path)
        run_record |= {
            "status": "sealed",
            "sealed_at": sealed_at,
            "work_dir": WORK_DIR,
            "result_record": RESULT_RECORD,
            "result_record_sha256": result_attestation.sha256,
            "seal_sha256": seal_sha,
        }
        _atomic_write_json(run_path, run_record)
        return {
            "status": "sealed",
            "run_record": RUN_RECORD,
            "result_record": RESULT_RECORD,
            "work_dir": WORK_DIR,
            "seal_sha256": seal_sha,
        }
    except BaseException as exc:
        if not published:
            shutil.rmtree(staging, ignore_errors=True)
        failed = run_record | {
            "status": "failed",
            "failed_at": _utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "published_work_dir": published,
        }
        _atomic_write_json(run_path, failed)
        raise
