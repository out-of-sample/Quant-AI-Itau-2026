"""Roda os diagnósticos de H2a (D-038) uma vez: contemporâneo e BRL.

Distinguem as duas leituras do resultado forward-negativo de H2a (D-037): transmissão fraca ao
preço mundial USD vs. reação contemporânea + reversão invisível a um teste forward, e transmissão
via câmbio/base capturada só em BRL. Diagnóstico, não portão — sem poder de veto próprio. A
especificação é D-038, pré-registrada antes deste resultado.
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
    download_fred_fx,
    download_fred_prices,
    load_commodity_prices,
    load_fx,
)
from quantagro.ingest.pam import parse_pam  # noqa: E402
from quantagro.stats.h2a import build_h2a_diag_panel, run_h2a_diag  # noqa: E402

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


def load_fx_series() -> pd.DataFrame:
    try:
        return load_fx()
    except FileNotFoundError:
        download_fred_fx()
        return load_fx()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conab = parse_levantamento(CONAB_TXT, "graos")
    municipal = load_municipal()
    pam = load_pam()
    prices = load_prices()
    fx = load_fx_series()
    cfy = CLIMATOLOGY_FIRST_YEAR
    print(f"climatology_first_year={cfy} | câmbio EXBZUS: {len(fx)} meses", flush=True)

    print("\n=== construindo painel de diagnóstico H2a ===", flush=True)
    panel = build_h2a_diag_panel(prices, fx, municipal, pam, conab, cfy)
    print(f"diag: {len(panel)} obs | clusters {panel['cluster'].nunique()}", flush=True)
    res = run_h2a_diag(panel)

    pd.set_option("display.width", 220, "display.max_columns", 30)
    print("\n===== DIAGNÓSTICOS H2a (desfecho ~ Shock; β>0 esperado) =====")
    print(res.to_string(index=False))
    print("\n=== resumo pooled full-span (a leitura) ===")
    key = res[(res["scope"] == "full") & (res["unit"] == "pooled")]
    for r in key.itertuples(index=False):
        print(f"  {r.outcome:12s} β={r.beta:+.4f}  p1(boot)={r.boot_p_one_sided:.3f}  n={r.n}")

    panel.to_parquet(OUT_DIR / "h2a_diag_panel.parquet", index=False)
    res.to_csv(OUT_DIR / "h2a_diag_results.csv", index=False)
    print(f"\nartefatos salvos em {OUT_DIR}/")


if __name__ == "__main__":
    main()
