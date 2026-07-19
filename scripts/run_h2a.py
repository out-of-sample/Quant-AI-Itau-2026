"""Roda H2a (portão do lado long) uma vez e reporta o veredito (D-036).

Carrega o painel municipal CHIRPS, os vintages CONAB, os pesos PAM e os preços mundiais FRED;
monta o painel de H2a (``Shock`` nacional as-of fim de mês na janela → retorno forward do preço
mundial); roda as regressões por escopo/cultura/horizonte e imprime o veredito direcional. A
especificação é D-036, pré-registrada antes deste resultado — nada aqui olha o número para
escolher horizonte, fonte ou regra.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from quantagro.features.panel import CLIMATOLOGY_FIRST_YEAR  # noqa: E402
from quantagro.features.shock import stamp_municipal_panel  # noqa: E402
from quantagro.ingest.conab import parse_levantamento  # noqa: E402
from quantagro.ingest.fred_prices import (  # noqa: E402
    SERIES,
    download_fred_prices,
    load_commodity_prices,
)
from quantagro.ingest.pam import parse_pam  # noqa: E402
from quantagro.stats.h2a import PRIMARY_HORIZON, build_h2a_panel, h2a_verdict, run_h2a  # noqa: E402

CONAB_TXT = "data/raw/conab/LevantamentoGraos_20260716.txt"
PARTS_GLOB = "data/interim/municipal_precip/part_*.parquet"
OUT_DIR = Path("data/processed")


def load_pam() -> pd.DataFrame:
    files = sorted(glob.glob("data/raw/pam/pam_1612_*.json"))
    return pd.concat((parse_pam(f) for f in files), ignore_index=True)


def load_municipal() -> pd.DataFrame:
    parts = sorted(glob.glob(PARTS_GLOB))
    if not parts:
        raise SystemExit("painel municipal ausente — rode scripts/build_municipal_panel.py")
    panel = pd.concat((pd.read_parquet(p) for p in parts), ignore_index=True)
    panel = panel.drop_duplicates(["ref_date", "kind", "municipality_code"])
    producing = set(load_pam()["municipality_code"].unique())
    panel = panel[panel["municipality_code"].isin(producing)].copy()
    panel = panel.sort_values(["kind", "ref_date"]).reset_index(drop=True)
    return stamp_municipal_panel(panel)


def load_prices() -> pd.DataFrame:
    try:
        return load_commodity_prices()
    except FileNotFoundError:
        for crop in SERIES:
            download_fred_prices(crop)
        return load_commodity_prices()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conab = parse_levantamento(CONAB_TXT, "graos")
    municipal = load_municipal()
    pam = load_pam()
    prices = load_prices()
    cfy = CLIMATOLOGY_FIRST_YEAR
    print(f"climatology_first_year={cfy}", flush=True)
    print(f"preços FRED: {prices['crop'].value_counts().to_dict()}", flush=True)

    print("\n=== construindo painel H2a ===", flush=True)
    panel = build_h2a_panel(prices, municipal, pam, conab, cfy)
    smp = panel["sample"].value_counts().to_dict()
    print(
        f"H2a: {len(panel)} obs | safras {panel['ano_agricola'].nunique()} | "
        f"clusters {panel['cluster'].nunique()} | amostra {smp}"
    )
    res = run_h2a(panel)
    v = h2a_verdict(res)

    pd.set_option("display.width", 220, "display.max_columns", 30)
    print("\n===== H2a (retorno forward do preço ~ Shock) =====")
    print(res.to_string(index=False))
    print(f"\n===== VEREDITO DO PORTÃO (h={PRIMARY_HORIZON}, span cheio, pooled) =====")
    print(f"status={v.status} | β={v.beta:.4f} | p unilateral(bootstrap)={v.boot_p_one_sided:.4f}")
    print(f"n={v.n} | clusters={v.n_clusters} | motivo: {v.reason}")

    panel.to_parquet(OUT_DIR / "h2a_panel.parquet", index=False)
    res.to_csv(OUT_DIR / "h2a_results.csv", index=False)
    print(f"\nartefatos salvos em {OUT_DIR}/")


if __name__ == "__main__":
    main()
