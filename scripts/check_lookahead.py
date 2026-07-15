#!/usr/bin/env python3
"""Tripwire determinístico contra lookahead óbvio.

NÃO é prova de ausência de lookahead — isso não existe estaticamente. É um arame de
tropeço barato contra os idiomas que mais causam vazamento de futuro neste tipo de código,
para forçar quem escreve a *parar e justificar*. A defesa real é a revisão de PR
(CONTRIBUTING.md §4) e os testes.

Regras (linha a linha, sobre .py passados como argumento):

  1. `.shift(-N)`  — deslocamento negativo traz barra futura para o presente.
  2. `.shift(n)` com n negativo por variável não é pego (limitação assumida).

Escape explícito: uma linha pode conter `# lookahead-ok: <motivo>` para ser ignorada —
espelha a regra do checklist de PR ("nenhum .shift(-1) sem justificativa explícita").
O motivo é obrigatório; `# lookahead-ok` pelado não basta.

Uso:
    python scripts/check_lookahead.py arquivo1.py arquivo2.py ...
Sai com código 1 se achar violação não justificada.
"""

from __future__ import annotations

import os
import re
import sys

# O próprio arquivo contém os idiomas que procura (na regex e nos exemplos do docstring),
# então se auto-denunciaria. Pular-se é mais simples que anotar cada linha com escape.
ESTE_ARQUIVO = os.path.abspath(__file__)

# .shift( seguido de sinal de menos e um dígito, com espaços opcionais: .shift(-1), .shift( -3 )
SHIFT_FUTURO = re.compile(r"\.shift\(\s*-\s*\d")
ESCAPE = re.compile(r"#\s*lookahead-ok:\s*\S")


def checar_arquivo(caminho: str) -> list[tuple[int, str]]:
    violacoes: list[tuple[int, str]] = []
    try:
        with open(caminho, encoding="utf-8") as f:
            linhas = f.readlines()
    except OSError, UnicodeDecodeError:
        return violacoes
    for n, linha in enumerate(linhas, start=1):
        if SHIFT_FUTURO.search(linha) and not ESCAPE.search(linha):
            violacoes.append((n, linha.rstrip()))
    return violacoes


def main(argv: list[str]) -> int:
    houve = False
    for caminho in argv:
        if not caminho.endswith(".py"):
            continue
        if os.path.abspath(caminho) == ESTE_ARQUIVO:
            continue
        for n, linha in checar_arquivo(caminho):
            houve = True
            print(f"{caminho}:{n}: possível lookahead (shift negativo) — {linha.strip()}")
    if houve:
        print(
            "\nSe for intencional, anote na linha:  # lookahead-ok: <por que não vaza futuro>",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
