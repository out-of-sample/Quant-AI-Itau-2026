"""Preflight return-agnóstico da rodada única do holdout (D-068/D-072).

O preflight compara código e inputs com manifestos SHA-256 sem abrir parquets nem calcular
resultados. D-072 fechou o executor, mas a execução continua separada por uma frase civil
posterior; consultar este módulo nunca consome a rodada.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

from .holdout_spec import (
    EXECUTOR_IMPLEMENTED,
    INPUT_SUMMARY,
    PACKAGE_ID,
    REQUIRED_INPUTS,
    RESULT_RECORD,
    RUN_RECORD,
    SOURCE_MANIFEST,
    SPEC_FILES,
    WORK_DIR,
    spec_sha256,
    validate_holdout_spec,
)
from .operational_spec import HoldoutLockedError


@dataclass(frozen=True)
class FileAttestation:
    """Hash e tamanho de um arquivo sem interpretar seu conteúdo."""

    path: str
    bytes: int
    sha256: str


@dataclass(frozen=True)
class HoldoutPreflight:
    """Estado completo do portão, seguro para imprimir antes do holdout."""

    logical_spec_sha256: str
    source_attestations: tuple[FileAttestation, ...]
    source_manifest_sha256: str | None
    source_manifest_errors: tuple[str, ...]
    input_attestations: tuple[FileAttestation, ...]
    input_manifest_sha256: str | None
    manifest_errors: tuple[str, ...]
    missing_spec_files: tuple[str, ...]
    present_inputs: tuple[str, ...]
    missing_inputs: tuple[str, ...]
    run_record_exists: bool
    result_record_exists: bool
    work_dir_exists: bool
    executor_implemented: bool
    ready: bool

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False, sort_keys=True)


def attest_file(path: Path, *, chunk_bytes: int = 1024 * 1024) -> FileAttestation:
    """Calcula SHA-256 em streaming; não parseia parquet/JSON nem expõe conteúdo."""
    if chunk_bytes <= 0:
        raise ValueError("chunk_bytes deve ser positivo")
    digest = sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_bytes):
            digest.update(chunk)
            size += len(chunk)
    return FileAttestation(str(path), size, digest.hexdigest())


def preflight_holdout(root: str | Path = ".") -> HoldoutPreflight:
    """Verifica contrato e presença dos inputs sem ler qualquer dado de holdout."""
    validate_holdout_spec()
    base = Path(root)
    missing_spec = tuple(path for path in SPEC_FILES if not (base / path).is_file())
    source_by_path = {
        path: attest_file(base / path) for path in SPEC_FILES if (base / path).is_file()
    }
    attestations = tuple(source_by_path.values())
    source_manifest_sha256: str | None = None
    source_manifest_errors: list[str] = []
    source_manifest_path = base / SOURCE_MANIFEST
    if not source_manifest_path.is_file():
        source_manifest_errors.append("manifesto de fontes ausente")
    else:
        source_manifest_sha256 = attest_file(source_manifest_path).sha256
        try:
            source_payload = json.loads(source_manifest_path.read_text(encoding="utf-8"))
            if source_payload.get("schema_version") != 1:
                source_manifest_errors.append("schema_version do manifesto de fontes deve ser 1")
            if source_payload.get("package_id") != PACKAGE_ID:
                source_manifest_errors.append(
                    "package_id do manifesto de fontes diverge do contrato"
                )
            if source_payload.get("logical_spec_sha256") != spec_sha256():
                source_manifest_errors.append(
                    "hash lógico do manifesto de fontes diverge do contrato"
                )
            records = source_payload.get("files")
            if not isinstance(records, dict) or set(records) != set(SPEC_FILES):
                source_manifest_errors.append("manifesto de fontes não cobre exatamente SPEC_FILES")
            else:
                for path in SPEC_FILES:
                    record = records[path]
                    attestation = source_by_path.get(path)
                    if not isinstance(record, dict) or record.get("path") != path:
                        source_manifest_errors.append(
                            f"caminho divergente no manifesto de fontes: {path}"
                        )
                    elif attestation is not None and (
                        record.get("sha256") != attestation.sha256
                        or record.get("bytes") != attestation.bytes
                    ):
                        source_manifest_errors.append(f"hash/tamanho divergente no fonte: {path}")
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            source_manifest_errors.append(
                f"manifesto de fontes inválido: {type(exc).__name__}: {exc}"
            )
    present_inputs = tuple(
        role for role, path in REQUIRED_INPUTS.items() if (base / path).is_file()
    )
    missing_inputs = tuple(role for role in REQUIRED_INPUTS if role not in present_inputs)
    input_attestations: tuple[FileAttestation, ...] = ()
    input_manifest_sha256: str | None = None
    manifest_errors: list[str] = []
    manifest_path = base / REQUIRED_INPUTS["input_manifest"]
    if manifest_path.is_file():
        input_manifest_sha256 = attest_file(manifest_path).sha256
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            if payload.get("schema_version") != 1:
                manifest_errors.append("schema_version do manifesto deve ser 1")
            if payload.get("package_id") != PACKAGE_ID:
                manifest_errors.append("package_id do manifesto diverge do contrato")
            if payload.get("logical_spec_sha256") != spec_sha256():
                manifest_errors.append("hash lógico do manifesto diverge do contrato")
            records = payload.get("inputs")
            expected_roles = set(REQUIRED_INPUTS) - {"input_manifest"}
            if not isinstance(records, dict) or set(records) != expected_roles:
                manifest_errors.append("papéis do manifesto não cobrem exatamente os parquets")
            else:
                verified = []
                for role in REQUIRED_INPUTS:
                    if role == "input_manifest":
                        continue
                    record = records[role]
                    expected_path = REQUIRED_INPUTS[role]
                    if not isinstance(record, dict) or record.get("path") != expected_path:
                        manifest_errors.append(f"caminho divergente no manifesto: {role}")
                        continue
                    path = base / expected_path
                    if not path.is_file():
                        continue
                    attestation = attest_file(path)
                    if (
                        record.get("sha256") != attestation.sha256
                        or record.get("bytes") != attestation.bytes
                    ):
                        manifest_errors.append(f"hash/tamanho divergente no input: {role}")
                    verified.append(attestation)
                input_attestations = tuple(verified)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            manifest_errors.append(f"manifesto inválido: {type(exc).__name__}: {exc}")
        summary_path = base / INPUT_SUMMARY
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            summary_manifest = summary.get("input_manifest")
            if summary.get("schema_version") != 1:
                manifest_errors.append("schema_version do resumo de inputs deve ser 1")
            if summary.get("package_id") != PACKAGE_ID:
                manifest_errors.append("package_id do resumo de inputs diverge do contrato")
            if summary.get("logical_spec_sha256") != spec_sha256():
                manifest_errors.append("hash lógico do resumo de inputs diverge do contrato")
            if (
                not isinstance(summary_manifest, dict)
                or summary_manifest.get("path") != REQUIRED_INPUTS["input_manifest"]
                or summary_manifest.get("sha256") != input_manifest_sha256
            ):
                manifest_errors.append("hash/caminho do manifesto diverge do resumo versionado")
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            manifest_errors.append(f"resumo de inputs inválido: {type(exc).__name__}: {exc}")
    run_record_exists = (base / RUN_RECORD).exists()
    result_record_exists = (base / RESULT_RECORD).exists()
    work_dir_exists = (base / WORK_DIR).exists()
    ready = (
        EXECUTOR_IMPLEMENTED
        and not missing_spec
        and not source_manifest_errors
        and not missing_inputs
        and not manifest_errors
        and len(input_attestations) == len(REQUIRED_INPUTS) - 1
        and not run_record_exists
        and not result_record_exists
        and not work_dir_exists
    )
    return HoldoutPreflight(
        logical_spec_sha256=spec_sha256(),
        source_attestations=attestations,
        source_manifest_sha256=source_manifest_sha256,
        source_manifest_errors=tuple(source_manifest_errors),
        input_attestations=input_attestations,
        input_manifest_sha256=input_manifest_sha256,
        manifest_errors=tuple(manifest_errors),
        missing_spec_files=missing_spec,
        present_inputs=present_inputs,
        missing_inputs=missing_inputs,
        run_record_exists=run_record_exists,
        result_record_exists=result_record_exists,
        work_dir_exists=work_dir_exists,
        executor_implemented=EXECUTOR_IMPLEMENTED,
        ready=ready,
    )


def require_holdout_ready(report: HoldoutPreflight) -> None:
    """Falha alto antes do I/O enquanto qualquer parte do pacote estiver incompleta."""
    if not report.executor_implemented:
        raise HoldoutLockedError(
            "executor da Fase 6 ainda não implementado; D-068–D-071 são só preflight"
        )
    if report.missing_spec_files:
        raise HoldoutLockedError(f"arquivos do contrato ausentes: {report.missing_spec_files}")
    if report.source_manifest_errors:
        raise HoldoutLockedError(f"manifesto de fontes inválido: {report.source_manifest_errors}")
    if report.missing_inputs:
        raise HoldoutLockedError(f"inputs do holdout ausentes: {report.missing_inputs}")
    if report.manifest_errors:
        raise HoldoutLockedError(f"manifesto do holdout inválido: {report.manifest_errors}")
    if report.run_record_exists:
        raise HoldoutLockedError("registro da rodada única já existe; segunda execução proibida")
    if report.result_record_exists or report.work_dir_exists:
        raise HoldoutLockedError("resultado/saída preexistente; segunda execução proibida")
    if not report.ready:
        raise HoldoutLockedError("preflight do holdout não está pronto")
