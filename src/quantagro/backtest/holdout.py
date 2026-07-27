"""Preflight return-agnóstico da rodada única do holdout (D-068).

O preflight atesta código e presença dos inputs sem abrir parquets nem calcular resultados.
Enquanto ``holdout_spec.EXECUTOR_IMPLEMENTED`` for falso, qualquer tentativa de execução
falha antes do I/O. D-069 fechou o input H4; o executor e o registro civil serão
implementados somente depois que H5 e seu schema também estiverem fechados.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

from .holdout_spec import (
    EXECUTOR_IMPLEMENTED,
    REQUIRED_INPUTS,
    RUN_RECORD,
    SPEC_FILES,
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
    missing_spec_files: tuple[str, ...]
    present_inputs: tuple[str, ...]
    missing_inputs: tuple[str, ...]
    run_record_exists: bool
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
    attestations = tuple(attest_file(base / path) for path in SPEC_FILES if (base / path).is_file())
    present_inputs = tuple(
        role for role, path in REQUIRED_INPUTS.items() if (base / path).is_file()
    )
    missing_inputs = tuple(role for role in REQUIRED_INPUTS if role not in present_inputs)
    run_record_exists = (base / RUN_RECORD).exists()
    ready = (
        EXECUTOR_IMPLEMENTED and not missing_spec and not missing_inputs and not run_record_exists
    )
    return HoldoutPreflight(
        logical_spec_sha256=spec_sha256(),
        source_attestations=attestations,
        missing_spec_files=missing_spec,
        present_inputs=present_inputs,
        missing_inputs=missing_inputs,
        run_record_exists=run_record_exists,
        executor_implemented=EXECUTOR_IMPLEMENTED,
        ready=ready,
    )


def require_holdout_ready(report: HoldoutPreflight) -> None:
    """Falha alto antes do I/O enquanto qualquer parte do pacote estiver incompleta."""
    if not report.executor_implemented:
        raise HoldoutLockedError(
            "executor da Fase 6 ainda não implementado; D-068/D-069 são só preflight"
        )
    if report.missing_spec_files:
        raise HoldoutLockedError(f"arquivos do contrato ausentes: {report.missing_spec_files}")
    if report.missing_inputs:
        raise HoldoutLockedError(f"inputs do holdout ausentes: {report.missing_inputs}")
    if report.run_record_exists:
        raise HoldoutLockedError("registro da rodada única já existe; segunda execução proibida")
    if not report.ready:
        raise HoldoutLockedError("preflight do holdout não está pronto")
