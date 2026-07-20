"""Executa uma vez o portão H1 da cana D-050, sem carregar retornos acionários."""

from __future__ import annotations

import glob
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from quantagro.features.cane_shock import stamp_cane_monthly_panel  # noqa: E402
from quantagro.features.panel import CLIMATOLOGY_FIRST_YEAR  # noqa: E402
from quantagro.ingest.conab import parse_levantamento  # noqa: E402
from quantagro.ingest.pam import parse_pam  # noqa: E402
from quantagro.stats.cane_h1 import (  # noqa: E402
    build_cane_h1_panel,
    cane_h1_verdict,
    run_cane_h1,
)

CONAB_TXT = "data/raw/conab/LevantamentoCana_20260716.txt"
PAM_GLOB = "data/raw/pam/pam_1612_sugarcane_*.json"
PARTS_GLOB = "data/interim/cane_monthly_precip/part_*.parquet"
OUT_DIR = Path("data/processed")


def main() -> None:
    pam_files = sorted(glob.glob(PAM_GLOB))
    parts = sorted(glob.glob(PARTS_GLOB))
    if not pam_files or not parts:
        raise SystemExit("dados da cana ausentes — rode scripts/build_cane_monthly_panel.py")
    pam = pd.concat((parse_pam(path) for path in pam_files), ignore_index=True)
    monthly = pd.concat((pd.read_parquet(path) for path in parts), ignore_index=True)
    monthly = monthly.drop_duplicates(["ref_date", "kind", "municipality_code"])
    monthly = stamp_cane_monthly_panel(monthly)
    conab = parse_levantamento(CONAB_TXT, "cana")

    maturation = build_cane_h1_panel(conab, monthly, pam, CLIMATOLOGY_FIRST_YEAR, "maturation")
    maturation_results = run_cane_h1(maturation)
    verdict = cane_h1_verdict(maturation_results)
    growth = build_cane_h1_panel(conab, monthly, pam, CLIMATOLOGY_FIRST_YEAR, "growth")
    growth_results = run_cane_h1(growth)

    print(
        f"maturação: {len(maturation)} obs, {maturation['ano_agricola'].nunique()} safras; "
        f"crescimento: {len(growth)} obs"
    )
    print("\nPORTÃO MATURAÇÃO/ATR")
    print(maturation_results.to_string(index=False))
    print(f"\npassou={verdict.passed} | {verdict.reason}")
    print("\nDIAGNÓSTICO CRESCIMENTO/PRODUÇÃO (não altera veredito)")
    print(growth_results.to_string(index=False))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    maturation.to_parquet(OUT_DIR / "cane_h1_maturation_panel.parquet", index=False)
    maturation_results.to_csv(OUT_DIR / "cane_h1_maturation_results.csv", index=False)
    growth.to_parquet(OUT_DIR / "cane_h1_growth_panel.parquet", index=False)
    growth_results.to_csv(OUT_DIR / "cane_h1_growth_results.csv", index=False)
    (OUT_DIR / "cane_h1_verdict.json").write_text(
        json.dumps(asdict(verdict), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
