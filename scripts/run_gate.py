"""Roda o portão da Fase 2 (H1a + H1b) uma vez e reporta o veredito (D-030).

Carrega o painel municipal CHIRPS (partes de ``build_municipal_panel.py``), o painel de
vintages CONAB, os pesos PAM e a exportação ComexStat; monta os painéis de regressão; aplica
BH-FDR sobre a família primária; imprime as tabelas e o veredito e salva os artefatos em
``data/processed/``. Não escolhe nada olhando resultado — a especificação é D-030.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from quantagro.features.panel import CLIMATOLOGY_FIRST_YEAR  # noqa: E402
from quantagro.features.shock import stamp_municipal_panel  # noqa: E402
from quantagro.ingest.comexstat import parse_comex  # noqa: E402
from quantagro.ingest.conab import parse_levantamento  # noqa: E402
from quantagro.ingest.pam import parse_pam  # noqa: E402
from quantagro.stats.gate import apply_fdr, primary_family, verdict  # noqa: E402
from quantagro.stats.h1a import build_h1a_panel, run_h1a  # noqa: E402
from quantagro.stats.h1b import build_h1b_panel, run_h1b  # noqa: E402

CONAB_TXT = "data/raw/conab/LevantamentoGraos_20260716.txt"
PARTS_GLOB = "data/interim/municipal_precip/part_*.parquet"
OUT_DIR = Path("data/processed")


def load_municipal() -> pd.DataFrame:
    parts = sorted(glob.glob(PARTS_GLOB))
    if not parts:
        raise SystemExit("painel municipal ausente — rode scripts/build_municipal_panel.py")
    panel = pd.concat((pd.read_parquet(p) for p in parts), ignore_index=True)
    panel = panel.drop_duplicates(["ref_date", "kind", "municipality_code"])
    return stamp_municipal_panel(panel)


def load_pam() -> pd.DataFrame:
    files = sorted(glob.glob("data/raw/pam/pam_1612_*.json"))
    return pd.concat((parse_pam(f) for f in files), ignore_index=True)


def load_export() -> pd.DataFrame:
    f = sorted(glob.glob("data/raw/comexstat/comexstat_export_*.json"))[-1]
    return parse_comex(f)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conab = parse_levantamento(CONAB_TXT, "graos")
    municipal = load_municipal()
    pam = load_pam()
    export = load_export()
    cfy = CLIMATOLOGY_FIRST_YEAR
    print(f"climatology_first_year={cfy}")
    print(
        f"painel municipal: {municipal['ref_date'].nunique()} datas × "
        f"{municipal['municipality_code'].nunique()} municípios"
    )

    print("\n=== construindo painel H1a ===", flush=True)
    h1a_panel = build_h1a_panel(conab, municipal, pam, cfy)
    print(
        f"H1a: {len(h1a_panel)} obs | safras {h1a_panel['ano_agricola'].nunique()} | "
        f"por cultura {h1a_panel['crop'].value_counts().to_dict()}"
    )
    h1a_res = run_h1a(h1a_panel)

    print("\n=== construindo painel H1b ===", flush=True)
    h1b_panel = build_h1b_panel(export, municipal, pam, conab, cfy)
    print(f"H1b: {len(h1b_panel)} obs | safras {h1b_panel['ano_agricola'].nunique()}")
    h1b_res = run_h1b(h1b_panel)

    family = apply_fdr(primary_family(h1a_res, h1b_res))
    v = verdict(family)

    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("\n===== H1a (revisão CONAB ~ Shock) =====")
    print(h1a_res.to_string(index=False))
    print("\n===== H1b (Δlog exportação ~ Shock) =====")
    print(h1b_res.to_string(index=False))
    print("\n===== Família primária + BH-FDR (α=0.10) =====")
    print(family.to_string(index=False))
    print("\n===== VEREDITO DO PORTÃO =====")
    print(f"passou={v.passed} | H1a β={v.h1a_beta:.4f} q={v.h1a_qvalue:.4f}")
    print(f"motivo: {v.reason}")

    h1a_panel.to_parquet(OUT_DIR / "h1a_panel.parquet", index=False)
    h1b_panel.to_parquet(OUT_DIR / "h1b_panel.parquet", index=False)
    h1a_res.to_csv(OUT_DIR / "h1a_results.csv", index=False)
    h1b_res.to_csv(OUT_DIR / "h1b_results.csv", index=False)
    family.to_csv(OUT_DIR / "gate_family_fdr.csv", index=False)
    print(f"\nartefatos salvos em {OUT_DIR}/")


if __name__ == "__main__":
    main()
