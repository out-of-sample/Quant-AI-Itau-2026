#!/usr/bin/env python3
"""Executa a mesma porta de qualidade localmente e na CI.

O script usa apenas a biblioteca padrão para orquestrar ferramentas já instaladas pelo
``requirements.lock``. O Makefile é um atalho opcional; este arquivo é a interface canônica e
funciona também em ambientes mínimos sem ``make``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence


def run(command: Sequence[str]) -> None:
    rendered = " ".join(command)
    if len(command) > 12:
        rendered = f"{' '.join(command[:5])} … ({len(command) - 5} argumentos)"
    print(f"+ {rendered}", flush=True)
    subprocess.run(command, check=True)


def project_files(pattern: str | None = None) -> list[str]:
    command = ["git", "ls-files", "--cached", "--others", "--exclude-standard"]
    if pattern is not None:
        command.append(pattern)
    output = subprocess.run(command, check=True, capture_output=True, text=True).stdout
    return [line for line in output.splitlines() if line]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true", help="aplica correções seguras do Ruff")
    parser.add_argument("--skip-tests", action="store_true", help="pula pytest")
    args = parser.parse_args(argv)
    python = sys.executable

    if args.fix:
        run([python, "-m", "ruff", "check", "--fix", "."])
        run([python, "-m", "ruff", "format", "."])
    else:
        run([python, "-m", "ruff", "check", "."])
        run([python, "-m", "ruff", "format", "--check", "."])

    run([python, "scripts/check_lookahead.py", *project_files("*.py")])
    run([python, "scripts/check_secrets.py", *project_files()])
    run([python, "scripts/check_docs.py", *project_files("*.md")])
    if not args.skip_tests:
        run([python, "-m", "pytest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
