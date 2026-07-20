"""Roda o último teste de preço: transmissão do Shock ao preço LOCAL brasileiro (D-040).

Preço local recebido pelo agricultor (IPEADATA/DERAL-Seab-PR), em BRL. Reaproveita o Shock
nacional de H2a; muda só a fonte de preço. Desfechos contemporâneo e forward; β>0 esperado. A
especificação é D-040, pré-registrada antes deste resultado.
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
from quantagro.ingest.ipea_prices import (  # noqa: E402
    SERIES_LOCAL,
    download_ipea_prices,
    load_local_prices,
)
from quantagro.ingest.pam import parse_pam  # noqa: E402
from quantagro.stats.h2a_local import (  # noqa: E402
    build_h2a_local_panel,
    h2a_local_verdict,
    run_h2a_local,
)

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
        return load_local_prices()
    except FileNotFoundError:
        for crop in SERIES_LOCAL:
            download_ipea_prices(crop)
        return load_local_prices()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conab = parse_levantamento(CONAB_TXT, "graos")
    municipal = load_municipal()
    pam = load_pam()
    prices = load_prices()
    cfy = CLIMATOLOGY_FIRST_YEAR
    print(f"climatology_first_year={cfy} | preço local: {prices['crop'].value_counts().to_dict()}")

    print("\n=== construindo painel do teste local ===", flush=True)
    panel = build_h2a_local_panel(prices, municipal, pam, conab, cfy)
    print(f"local: {len(panel)} obs | clusters {panel['cluster'].nunique()}", flush=True)
    res = run_h2a_local(panel)
    v = h2a_local_verdict(res)

    pd.set_option("display.width", 220, "display.max_columns", 30)
    print("\n===== TESTE DE PREÇO LOCAL (desfecho ~ Shock; β>0 esperado) =====")
    print(res.to_string(index=False))
    print("\n===== VEREDITO (pooled span cheio) =====")
    print(f"transmite={v.transmits} | {v.detail}")

    panel.to_parquet(OUT_DIR / "h2a_local_panel.parquet", index=False)
    res.to_csv(OUT_DIR / "h2a_local_results.csv", index=False)
    print(f"\nartefatos salvos em {OUT_DIR}/")


if __name__ == "__main__":
    main()
