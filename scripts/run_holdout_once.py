"""Entrada única da Fase 6 — atualmente limitada ao preflight D-068.

Sem argumentos, imprime apenas hashes de código e a lista de inputs ausentes. D-069 fechou
H4 e D-070/D-071 fecharam H5; ``--execute`` permanece bloqueado antes de qualquer leitura
de parquet até que o executor atômico seja fechado em decisão posterior.
"""

from __future__ import annotations

import argparse
import sys

sys.path.insert(0, "src")
from quantagro.backtest.holdout import preflight_holdout, require_holdout_ready  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="tenta atravessar o portão; D-068–D-071 ainda bloqueiam antes do I/O",
    )
    args = parser.parse_args()
    report = preflight_holdout()
    print(report.to_json())
    if args.execute:
        require_holdout_ready(report)


if __name__ == "__main__":
    main()
