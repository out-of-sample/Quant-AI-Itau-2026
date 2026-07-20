"""Roda o teste de reação das ações (Fase 3.2, D-042) uma vez, só no desenvolvimento.

Carrega os retornos totais dos 4 nomes (``build_equity_returns.py``), a matriz de exposição, o
painel municipal, PAM e CONAB; monta o painel score×retorno-forward e roda o teste primário
(painel demeanado na seção transversal) + o P&L da carteira dollar-neutral. A especificação é
D-042, pré-registrada antes deste resultado. O holdout 2020-2025 permanece lacrado.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from quantagro.features.exposure import load_exposure_registry  # noqa: E402
from quantagro.features.panel import CLIMATOLOGY_FIRST_YEAR  # noqa: E402
from quantagro.features.shock import stamp_municipal_panel  # noqa: E402
from quantagro.ingest.conab import parse_levantamento  # noqa: E402
from quantagro.ingest.pam import parse_pam  # noqa: E402
from quantagro.stats.equity_reaction import (  # noqa: E402
    build_equity_reaction_panel,
    reaction_verdict,
    run_equity_reaction,
)

CONAB_TXT = "data/raw/conab/LevantamentoGraos_20260716.txt"
PARTS_GLOB = "data/interim/municipal_precip/part_*.parquet"
RETURNS = "data/interim/equity_returns_dev.parquet"
REGISTRY = "data/reference/exposure_fundamental_v1.json"
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not Path(RETURNS).exists():
        raise SystemExit("retornos ausentes — rode scripts/build_equity_returns.py")
    returns = pd.read_parquet(RETURNS)
    registry = load_exposure_registry(REGISTRY)
    conab = parse_levantamento(CONAB_TXT, "graos")
    municipal = load_municipal()
    pam = load_pam()
    cfy = CLIMATOLOGY_FIRST_YEAR
    print(f"retornos: {returns.shape[0]}d × {list(returns.columns)} | cfy={cfy}", flush=True)

    print("\n=== construindo painel de reação ===", flush=True)
    panel = build_equity_reaction_panel(returns, registry, municipal, pam, conab, cfy)
    print(
        f"reação: {len(panel)} obs (data×nome) | datas {panel['date'].nunique()} | "
        f"safras {panel['ano_agricola'].nunique()} | nomes {sorted(panel['ticker'].unique())}"
    )
    res = run_equity_reaction(panel)
    v = reaction_verdict(res)

    pd.set_option("display.width", 200, "display.max_columns", 20)
    pr = res["primary"]
    print("\n===== TESTE PRIMÁRIO (retorno demeanado ~ score demeanado; β>0 esperado) =====")
    print(
        f"β={pr['beta']:+.5f} | t={pr['tstat']:.2f} | n={pr['n']} clusters={pr['n_clusters']} | "
        f"p1(boot)={pr['boot_p_one_sided']:.3f} | IC[{pr['ci_low']:+.4f},{pr['ci_high']:+.4f}]"
    )
    print("\n===== P&L carteira dollar-neutral (score-weighted) =====")
    print(
        f"média/período={res['pnl']['mean']:+.5f} | vol={res['pnl']['std']:.4f} | "
        f"períodos={res['pnl']['n_periods']} | hit-rate={res['pnl']['hit_rate']:.2f}"
    )
    print("\n===== por nome (corr score×retorno) =====")
    print(res["per_name"].to_string(index=False))
    print(f"\n===== VEREDITO ===== reage={v.reacts} | {v.detail}")

    panel.to_parquet(OUT_DIR / "equity_reaction_panel.parquet", index=False)
    print(f"\nartefato salvo em {OUT_DIR}/equity_reaction_panel.parquet")


if __name__ == "__main__":
    main()
