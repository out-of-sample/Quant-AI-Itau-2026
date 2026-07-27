"""Entrada única da Fase 6 — preflight ou rodada civil atômica D-072.

Sem argumentos, imprime apenas hashes e o estado do portão sem abrir parquets. ``--execute``
exige também a frase civil exata congelada; sem ela, falha antes do I/O. Durante a rodada não
há impressão intermediária: o comando só devolve a localização do pacote depois do selo final.
"""

from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, "src")
from quantagro.backtest.holdout import preflight_holdout  # noqa: E402
from quantagro.backtest.holdout_executor import execute_holdout_once  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="consome a rodada única somente com a frase civil exata",
    )
    parser.add_argument(
        "--authorization",
        help="frase civil D-072; não é necessária para consultar o preflight",
    )
    args = parser.parse_args()
    if args.execute:
        sealed = execute_holdout_once(".", authorization=args.authorization or "")
        print(json.dumps(sealed, ensure_ascii=False, indent=2, sort_keys=True))
        return
    if args.authorization:
        parser.error("--authorization só pode acompanhar --execute")
    print(preflight_holdout().to_json())


if __name__ == "__main__":
    main()
