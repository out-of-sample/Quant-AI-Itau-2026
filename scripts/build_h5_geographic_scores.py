"""Materializa o input H5 geográfico sem ler retornos da estratégia.

O script usa somente fontes já congeladas: painel municipal CHIRPS, PAM, CONAB, exposições H′
e calendário NEFIN/B3. A primeira execução prende os hashes das partes municipais e do output;
rebuild divergente falha antes de substituir o parquet.
"""

from __future__ import annotations

import glob
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from quantagro.backtest.holdout_spec import spec_sha256  # noqa: E402
from quantagro.backtest.operational_spec import build_trade_blocks  # noqa: E402
from quantagro.backtest.strategy_spec import HOLDOUT_CROP_YEARS  # noqa: E402
from quantagro.features.exposure import load_exposure_registry  # noqa: E402
from quantagro.features.panel import CLIMATOLOGY_FIRST_YEAR  # noqa: E402
from quantagro.ingest.conab import parse_levantamento  # noqa: E402
from quantagro.ingest.nefin import parse_nefin  # noqa: E402
from quantagro.ingest.pam import parse_pam  # noqa: E402
from quantagro.robustness.h5_geography import (  # noqa: E402
    build_placebo_daily_precip,
    materialize_h5_grain_scores,
)
from quantagro.robustness.h5_geography_spec import (  # noqa: E402
    H5_PLACEBO_CODES,
    audit_placebo_cell_index,
    audit_zero_grain_production,
)
from quantagro.stats.h2a import _stamp_grains  # noqa: E402

OUT = Path("data/interim/holdout/h5_geographic_grain_scores.parquet")
SUMMARY = Path("data/reference/h5_geographic_scores_summary_v1.json")
GEOGRAPHY_SPEC = Path("data/reference/h5_geography_spec_v1.json")
CELL_INDEX = Path("data/interim/municipal_cell_index.parquet")
CHIRPS_MANIFEST = Path("data/manifests/chirps_h1_bulk.parquet")
CONAB_RAW = Path("data/raw/conab/LevantamentoGraos_20260716.txt")
CONAB_MANIFEST = Path("data/manifests/conab_graos_20260716.json")
EXPOSURE = Path("data/reference/exposure_hprime_v1.json")
H4_SUMMARY = Path("data/reference/h4_controls_summary_v1.json")
PAM_RAW = (
    Path("data/raw/pam/pam_1612_soy_2014-2024_ba-go-mg-ms-mt-pr-rs_20260717.json"),
    Path("data/raw/pam/pam_1612_corn_total_2014-2024_go-ms-mt-pr_20260717.json"),
    Path("data/raw/pam/pam_1612_corn_total_2014-2024_ba_20260727.json"),
)
PAM_MANIFESTS = (
    Path("data/manifests/pam_1612_soy_2014-2024_ba-go-mg-ms-mt-pr-rs_20260717.json"),
    Path("data/manifests/pam_1612_corn_total_2014-2024_go-ms-mt-pr_20260717.json"),
    Path("data/manifests/pam_1612_corn_total_2014-2024_ba_20260727.json"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _initial_registry() -> dict[str, object]:
    h4 = json.loads(H4_SUMMARY.read_text(encoding="utf-8"))
    nefin = h4["sources"]["nefin"]
    municipal_parts = tuple(
        Path(path) for path in sorted(glob.glob("data/interim/municipal_precip/part_*.parquet"))
    )
    if not municipal_parts:
        raise FileNotFoundError("partes municipais CHIRPS ausentes")
    fixed = {
        "geography_spec": GEOGRAPHY_SPEC,
        "cell_index": CELL_INDEX,
        "chirps_manifest": CHIRPS_MANIFEST,
        "conab_raw": CONAB_RAW,
        "conab_manifest": CONAB_MANIFEST,
        "exposure": EXPOSURE,
        "nefin_raw": Path(nefin["raw_path"]),
        "nefin_manifest": Path(nefin["manifest_path"]),
    }
    fixed.update({f"pam_raw_{i}": path for i, path in enumerate(PAM_RAW)})
    fixed.update({f"pam_manifest_{i}": path for i, path in enumerate(PAM_MANIFESTS)})
    for role, path in fixed.items():
        if not path.is_file():
            raise FileNotFoundError(f"{role}: arquivo ausente {path}")
    return {
        "fixed": {
            role: {"path": str(path), "sha256": _sha256(path)} for role, path in fixed.items()
        },
        "municipal_parts": [
            {"path": str(path), "sha256": _sha256(path)} for path in municipal_parts
        ],
    }


def source_registry() -> dict[str, object]:
    """Usa os hashes já congelados após a primeira execução."""
    if not SUMMARY.exists():
        return _initial_registry()
    registry = json.loads(SUMMARY.read_text(encoding="utf-8"))["sources"]
    records = list(registry["fixed"].values()) + list(registry["municipal_parts"])
    for record in records:
        path = Path(record["path"])
        if not path.is_file():
            raise FileNotFoundError(f"fonte H5 congelada ausente: {path}")
        if _sha256(path) != record["sha256"]:
            raise ValueError(f"fonte H5 diverge do hash congelado: {path}")
    return registry


def _load_municipal(parts: list[dict[str, str]]) -> pd.DataFrame:
    frames = [
        pd.read_parquet(
            record["path"],
            filters=[("municipality_code", "in", list(H5_PLACEBO_CODES))],
        )
        for record in parts
    ]
    panel = pd.concat(frames, ignore_index=True)
    manifest = pd.read_parquet(CHIRPS_MANIFEST, columns=["ref_date", "kind"])
    expected = pd.MultiIndex.from_frame(
        manifest.assign(ref_date=pd.to_datetime(manifest["ref_date"]))[["ref_date", "kind"]]
    )
    observed = pd.MultiIndex.from_frame(
        panel.assign(ref_date=pd.to_datetime(panel["ref_date"]))[["ref_date", "kind"]]
        .drop_duplicates()
        .sort_values(["ref_date", "kind"])
    )
    if len(expected) != 6197 or set(expected) != set(observed):
        raise ValueError("painel municipal H5 diverge dos 6.197 raster-dias manifestados")
    return panel


def _summary_payload(
    scores: pd.DataFrame,
    daily: pd.DataFrame,
    registry: dict[str, object],
    output_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "decision": "D-071",
        "holdout_logical_spec_sha256": spec_sha256(),
        "scope": {
            "crop_years": list(HOLDOUT_CROP_YEARS),
            "rows": len(scores),
            "first_decision_date": scores.index.min().date().isoformat(),
            "last_decision_date": scores.index.max().date().isoformat(),
            "tickers": list(scores.columns),
        },
        "geography": {
            "municipality_codes": list(H5_PLACEBO_CODES),
            "chirps_cells": 91,
            "raster_days": len(daily),
            "first_final_ref_date": daily.loc[daily["kind"].eq("final"), "ref_date"]
            .min()
            .date()
            .isoformat(),
            "last_prelim_ref_date": daily.loc[daily["kind"].eq("prelim"), "ref_date"]
            .max()
            .date()
            .isoformat(),
        },
        "quality": {
            "missing_scores": int(scores.isna().sum().sum()),
            "duplicate_decision_dates": int(scores.index.duplicated().sum()),
            "finite_scores": bool(pd.notna(scores).all().all()),
        },
        "sources": registry,
        "output": {
            "path": str(OUT),
            "sha256": output_sha256,
            "columns": list(scores.columns),
            "index": "decision_date",
        },
        "never_read_returns": True,
    }


def main() -> None:
    registry = source_registry()
    fixed = registry["fixed"]

    cell_index = pd.read_parquet(fixed["cell_index"]["path"])
    audit_placebo_cell_index(cell_index)
    pam = pd.concat(
        (parse_pam(fixed[f"pam_raw_{i}"]["path"]) for i in range(len(PAM_RAW))),
        ignore_index=True,
    )
    audit_zero_grain_production(pam)

    municipal = _load_municipal(registry["municipal_parts"])
    daily = build_placebo_daily_precip(municipal)
    conab = _stamp_grains(parse_levantamento(fixed["conab_raw"]["path"], "graos"))
    exposure = load_exposure_registry(fixed["exposure"]["path"])
    sessions = pd.DatetimeIndex(parse_nefin(fixed["nefin_raw"]["path"])["ref_date"])
    blocks = tuple(
        block
        for crop_year in HOLDOUT_CROP_YEARS
        for block in build_trade_blocks(sessions, crop_year)
    )
    scores = materialize_h5_grain_scores(
        blocks,
        exposure,
        daily,
        conab,
        CLIMATOLOGY_FIRST_YEAR,
        allow_holdout=True,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUT.with_name(f".{OUT.name}.tmp")
    scores.to_parquet(temporary)
    output_sha = _sha256(temporary)
    summary = _summary_payload(scores, daily, registry, output_sha)
    if SUMMARY.exists():
        frozen = json.loads(SUMMARY.read_text(encoding="utf-8"))
        if frozen != summary:
            temporary.unlink(missing_ok=True)
            raise RuntimeError("rebuild H5 diverge do registro congelado")
    else:
        SUMMARY.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    temporary.replace(OUT)
    print(
        f"H5: {len(scores)} decisões, {scores.index.min().date()}→"
        f"{scores.index.max().date()}, 91 células / {len(daily)} raster-dias"
    )
    print(f"scores → {OUT} ({output_sha})")
    print(f"registro auditável → {SUMMARY}")
    print("nenhum retorno da estratégia foi lido; o veto H5 não foi estimado")


if __name__ == "__main__":
    main()
