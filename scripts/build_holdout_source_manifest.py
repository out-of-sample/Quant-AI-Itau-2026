"""Congela hashes dos fontes executáveis do pacote D-072.

Rodar somente durante o checkpoint técnico, antes da autorização civil. O preflight exige
correspondência exata entre este manifesto versionado e ``holdout_spec.SPEC_FILES``.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")
from quantagro.backtest.holdout import attest_file  # noqa: E402
from quantagro.backtest.holdout_spec import (  # noqa: E402
    PACKAGE_ID,
    SOURCE_MANIFEST,
    SPEC_FILES,
    spec_sha256,
)


def main() -> None:
    missing = [path for path in SPEC_FILES if not Path(path).is_file()]
    if missing:
        raise FileNotFoundError(f"fontes do contrato ausentes: {missing}")
    files = {}
    for path in SPEC_FILES:
        attestation = attest_file(Path(path))
        files[path] = {
            "path": path,
            "bytes": attestation.bytes,
            "sha256": attestation.sha256,
        }
    payload = {
        "schema_version": 1,
        "package_id": PACKAGE_ID,
        "logical_spec_sha256": spec_sha256(),
        "files": files,
    }
    target = Path(SOURCE_MANIFEST)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
    print(f"manifesto de fontes congelado: {len(files)} arquivos em {target}")


if __name__ == "__main__":
    main()
