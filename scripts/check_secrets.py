#!/usr/bin/env python3
"""Tripwire determinístico contra commitar segredos.

Bloqueia padrões óbvios de chave/credencial em arquivos de texto passados como argumento.
Como o guarda de lookahead, é um arame de tropeço, não uma varredura forense — mas pega os
acidentes mais comuns (colar um token num notebook, esquecer uma chave privada).

Escape explícito por linha: `# secret-ok: <motivo>` (ex.: exemplo em documentação).

Uso:
    python scripts/check_secrets.py arquivo1 arquivo2 ...
Sai com código 1 se achar algo.
"""

from __future__ import annotations

import re
import sys

PADROES: list[tuple[str, re.Pattern[str]]] = [
    ("chave privada", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("token tipo GitHub", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{20,}\b")),
    ("chave Google API", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")),
    # atribuição genérica a variável com cara de segredo e valor longo entre aspas
    (
        "segredo em atribuição",
        re.compile(
            r"(?i)(api[_-]?key|secret|passwd|password|token)\s*[:=]\s*['\"][0-9A-Za-z/\+_\-]{16,}['\"]"
        ),
    ),
]
ESCAPE = re.compile(r"#\s*secret-ok:\s*\S")


def checar_arquivo(caminho: str) -> list[tuple[int, str, str]]:
    achados: list[tuple[int, str, str]] = []
    try:
        with open(caminho, encoding="utf-8") as f:
            linhas = f.readlines()
    except OSError, UnicodeDecodeError:
        return achados
    for n, linha in enumerate(linhas, start=1):
        if ESCAPE.search(linha):
            continue
        for rotulo, padrao in PADROES:
            if padrao.search(linha):
                achados.append((n, rotulo, linha.rstrip()))
                break
    return achados


def main(argv: list[str]) -> int:
    houve = False
    for caminho in argv:
        for n, rotulo, _linha in checar_arquivo(caminho):
            houve = True
            print(f"{caminho}:{n}: possível segredo ({rotulo})")
    if houve:
        print(
            "\nRemova o segredo do código. Se for um exemplo falso, anote:  # secret-ok: <motivo>",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
