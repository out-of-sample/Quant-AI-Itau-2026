"""Publica o relatório descritivo do holdout a partir dos artefatos já selados.

Sem parâmetros e sem graus de liberdade: tudo que o relatório calcula está congelado em
`backtest/holdout_report_spec.py`, anterior à rodada. Falha alto se o selo não existir.
"""

from __future__ import annotations

import sys

from quantagro.backtest.holdout_report import write_report


def main() -> int:
    try:
        target = write_report()
    except (RuntimeError, FileNotFoundError) as error:
        print(f"relatório não emitido: {error}", file=sys.stderr)
        return 1
    print(f"relatório descritivo publicado: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
