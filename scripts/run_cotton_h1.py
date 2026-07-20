"""Executa uma vez a validação H1 do algodão pré-registrada em D-048.

O script usa PAM do algodão, CHIRPS municipal já existente e vintages CONAB de pluma. Não
carrega preço nem retorno de ação. Artefatos ficam em ``data/processed/``; a decisão pública
de promoção ou rejeição do canal deve reproduzir literalmente ``cotton_h1_verdict``.
"""

from __future__ import annotations

import glob
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from quantagro.features.panel import CLIMATOLOGY_FIRST_YEAR  # noqa: E402
from quantagro.features.shock import stamp_municipal_panel  # noqa: E402
from quantagro.ingest.conab import parse_levantamento  # noqa: E402
from quantagro.ingest.pam import parse_pam  # noqa: E402
from quantagro.stats.cotton_h1 import (  # noqa: E402
    build_cotton_h1_panel,
    cotton_h1_verdict,
    run_cotton_h1,
)

CONAB_TXT = "data/raw/conab/LevantamentoGraos_20260716.txt"
PARTS_GLOB = "data/interim/municipal_precip/part_*.parquet"
PAM_GLOB = "data/raw/pam/pam_1612_*.json"
OUT_DIR = Path("data/processed")


def load_pam() -> pd.DataFrame:
    files = sorted(glob.glob(PAM_GLOB))
    if not files:
        raise SystemExit("PAM ausente")
    panel = pd.concat((parse_pam(path) for path in files), ignore_index=True)
    if "cotton" not in set(panel["crop"]):
        raise SystemExit("PAM do algodão ausente — baixe cotton/2014-2024/BA+MT")
    return panel


def load_municipal(cotton_codes: set[str]) -> pd.DataFrame:
    parts = sorted(glob.glob(PARTS_GLOB))
    if not parts:
        raise SystemExit("painel municipal ausente — rode scripts/build_municipal_panel.py")
    panel = pd.concat((pd.read_parquet(path) for path in parts), ignore_index=True)
    panel = panel.drop_duplicates(["ref_date", "kind", "municipality_code"])
    panel = panel[panel["municipality_code"].isin(cotton_codes)].copy()
    panel = panel.sort_values(["kind", "ref_date"]).reset_index(drop=True)
    return stamp_municipal_panel(panel)


def main() -> None:
    pam = load_pam()
    # Preservar também municípios de peso zero: `_stretch_sum` exige cobertura do universo
    # PAM selecionado e falha alto se o carregador omitir linhas existentes (lição ao vivo
    # registrada na validação D-049). Apenas `NaN` é removido depois por `_uf_weights`.
    cotton = pam[pam["crop"] == "cotton"]
    municipal = load_municipal(set(cotton["municipality_code"]))
    conab = parse_levantamento(CONAB_TXT, "graos")

    panel = build_cotton_h1_panel(conab, municipal, pam, CLIMATOLOGY_FIRST_YEAR)
    results = run_cotton_h1(panel)
    verdict = cotton_h1_verdict(results)

    pd.set_option("display.width", 180, "display.max_columns", 30)
    print(
        f"painel: {len(panel)} obs | {panel['ano_agricola'].nunique()} safras | "
        f"{panel['uf'].value_counts().to_dict()}"
    )
    print(results.to_string(index=False))
    print(f"\npassou={verdict.passed} | {verdict.reason}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(OUT_DIR / "cotton_h1_panel.parquet", index=False)
    results.to_csv(OUT_DIR / "cotton_h1_results.csv", index=False)
    (OUT_DIR / "cotton_h1_verdict.json").write_text(
        json.dumps(asdict(verdict), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"artefatos salvos em {OUT_DIR}/cotton_h1_*")


if __name__ == "__main__":
    main()
