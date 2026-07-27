"""Materializa o snapshot diário de controles H4 sem ler retornos da estratégia.

Uso:
    python scripts/build_h4_controls.py --download
    python scripts/build_h4_controls.py

Na primeira execução, seleciona as capturas mais recentes e grava seus caminhos/hashes em
``data/reference/h4_controls_summary_v1.json``. Execuções seguintes ficam presas àquele
registro: uma captura nova não substitui silenciosamente o vintage congelado.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from quantagro.backtest.holdout_spec import spec_sha256  # noqa: E402
from quantagro.ingest.h4_market import (  # noqa: E402
    COMMODITY_ETFS,
    download_h4_market,
    parse_fred_daily_fx,
    parse_yahoo_adjusted,
)
from quantagro.ingest.nefin import parse_nefin  # noqa: E402
from quantagro.ingest.oni import parse_oni  # noqa: E402
from quantagro.robustness.h4_controls import (  # noqa: E402
    H4_END,
    H4_START,
    MAX_MARKET_STALENESS_DAYS,
    build_h4_controls,
)

OUT = Path("data/interim/holdout/h4_controls.parquet")
SUMMARY = Path("data/reference/h4_controls_summary_v1.json")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _latest(pattern: str) -> Path:
    paths = sorted(Path().glob(pattern))
    if not paths:
        raise FileNotFoundError(f"captura ausente: {pattern}")
    return paths[-1]


def _first_source_registry() -> dict[str, dict[str, str]]:
    raw = {
        "nefin": _latest("data/raw/nefin/nefin_factors_*.csv"),
        "oni": _latest("data/raw/oni/oni_*.txt"),
        "usdbrl": _latest("data/raw/h4_market/fred_dexbzus_*.csv"),
        **{
            role: _latest(f"data/raw/h4_market/yahoo_{symbol.lower()}_*.json")
            for role, symbol in COMMODITY_ETFS.items()
        },
    }
    manifests = {
        "nefin": _latest("data/manifests/nefin_factors_*.json"),
        "oni": _latest("data/manifests/oni_*.json"),
        "usdbrl": _latest("data/manifests/h4_fred_usdbrl_*.json"),
        **{role: _latest(f"data/manifests/h4_yahoo_{role}_*.json") for role in COMMODITY_ETFS},
    }
    registry: dict[str, dict[str, str]] = {}
    for role in raw:
        manifest = json.loads(manifests[role].read_text(encoding="utf-8"))
        actual = _sha256(raw[role])
        if actual != manifest["sha256"]:
            raise ValueError(f"{role}: hash bruto diverge do manifesto")
        registry[role] = {
            "raw_path": str(raw[role]),
            "manifest_path": str(manifests[role]),
            "sha256": actual,
            "downloaded_at": manifest["downloaded_at"],
        }
    return registry


def source_registry() -> dict[str, dict[str, str]]:
    """Usa o registro já congelado; só seleciona o mais recente na primeira execução."""
    if not SUMMARY.exists():
        return _first_source_registry()
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    registry = payload["sources"]
    for role, source in registry.items():
        raw = Path(source["raw_path"])
        manifest = Path(source["manifest_path"])
        if not raw.is_file() or not manifest.is_file():
            raise FileNotFoundError(f"{role}: captura/manifesto congelado ausente")
        if _sha256(raw) != source["sha256"]:
            raise ValueError(f"{role}: captura diverge do hash congelado")
        payload_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        if payload_manifest["sha256"] != source["sha256"]:
            raise ValueError(f"{role}: manifesto diverge do registro H4")
    return registry


def _load_inputs(registry: dict[str, dict[str, str]]):
    nefin = parse_nefin(Path(registry["nefin"]["raw_path"]))
    oni = parse_oni(Path(registry["oni"]["raw_path"]))
    market = {
        role: parse_yahoo_adjusted(Path(registry[role]["raw_path"]), role)
        for role in COMMODITY_ETFS
    }
    market["usdbrl"] = parse_fred_daily_fx(Path(registry["usdbrl"]["raw_path"]))
    snapshot = max(pd.Timestamp(source["downloaded_at"]) for source in registry.values())
    if snapshot.tzinfo is not None:
        snapshot = snapshot.tz_convert("UTC").tz_localize(None)
    return nefin, market, oni, snapshot.normalize()


def _summary_payload(
    panel: pd.DataFrame,
    registry: dict[str, dict[str, str]],
    output_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "decision": "D-069",
        "holdout_logical_spec_sha256": spec_sha256(),
        "scope": {
            "start": H4_START.date().isoformat(),
            "end": H4_END.date().isoformat(),
            "rows": len(panel),
            "first_ref_date": panel["ref_date"].min().date().isoformat(),
            "last_ref_date": panel["ref_date"].max().date().isoformat(),
            "snapshot_avail_date": panel["avail_date"].iloc[0].date().isoformat(),
        },
        "transform": {
            "calendar": "NEFIN/B3",
            "market_return": "simple_return_between_consecutive_b3_sessions",
            "market_alignment": "last_observation_carried_forward_without_backfill",
            "max_market_staleness_calendar_days": MAX_MARKET_STALENESS_DAYS,
            "commodity_proxies": COMMODITY_ETFS,
            "commodity_currency": "USD",
            "usdbrl_quote": "BRL_per_USD",
            "oni": "latest_stabilized_level_available_asof_ref_date",
            "never_used_for_positions": True,
        },
        "quality": {
            "missing_cells": int(panel.isna().sum().sum()),
            "duplicate_ref_dates": int(panel["ref_date"].duplicated().sum()),
            "zero_market_returns": {
                role: int(panel[role].eq(0).sum())
                for role in ("usdbrl", "soy", "corn_second", "sugar")
            },
        },
        "sources": registry,
        "output": {
            "path": str(OUT),
            "sha256": output_sha256,
            "columns": list(panel.columns),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--download",
        action="store_true",
        help="baixa snapshots se ainda não existirem; nunca substitui o registro congelado",
    )
    args = parser.parse_args()
    if args.download and SUMMARY.exists():
        raise SystemExit("H4 já congelado; captura nova exige decisão explícita")
    if args.download:
        download_h4_market()

    registry = source_registry()
    nefin, market, oni, snapshot = _load_inputs(registry)
    panel = build_h4_controls(
        nefin,
        market,
        oni,
        snapshot_avail_date=snapshot,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUT.with_name(f".{OUT.name}.tmp")
    panel.to_parquet(temporary, index=False)
    output_sha = _sha256(temporary)
    summary = _summary_payload(panel, registry, output_sha)

    if SUMMARY.exists():
        frozen = json.loads(SUMMARY.read_text(encoding="utf-8"))
        if frozen != summary:
            temporary.unlink(missing_ok=True)
            raise RuntimeError("rebuild H4 diverge do registro congelado")
    else:
        SUMMARY.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    temporary.replace(OUT)

    print(
        f"H4: {len(panel)} sessões, {panel['ref_date'].min().date()}→"
        f"{panel['ref_date'].max().date()}, snapshot {snapshot.date()}"
    )
    print(f"painel → {OUT} ({output_sha})")
    print(f"registro auditável → {SUMMARY}")
    print("nenhum retorno da estratégia foi lido")


if __name__ == "__main__":
    main()
