"""Materialize the compact public time series used by repository figures.

The strategy curve comes from the sealed D-075 metrics. The risk-free curve
comes from the frozen H4 controls. Both inputs are local research artifacts;
the compact, derived JSON is versioned so a clean clone can rebuild every
public figure without redistributing the full intermediate panels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "data/processed/holdout_v1/10_metrics.json"
CONTROLS = ROOT / "data/interim/holdout/h4_controls.parquet"
OUTPUT = ROOT / "results/data/holdout_v1/public_series.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=METRICS)
    parser.add_argument("--controls", type=Path, default=CONTROLS)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def build(metrics_path: Path, controls_path: Path) -> dict[str, object]:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))["payload"]
    daily = pd.DataFrame(metrics["daily"])
    daily["date"] = pd.to_datetime(daily["date"])

    controls = pd.read_parquet(controls_path, columns=["ref_date", "risk_free"])
    controls["ref_date"] = pd.to_datetime(controls["ref_date"])
    merged = daily.merge(
        controls,
        left_on="date",
        right_on="ref_date",
        validate="one_to_one",
        how="left",
    )
    if merged["risk_free"].isna().any():
        missing = merged.loc[merged["risk_free"].isna(), "date"].dt.date.tolist()
        raise ValueError(f"risk-free missing for {missing[:5]}")

    initial_equity = 500_000.0
    merged["strategy_index"] = merged["equity_brl"] / initial_equity * 100.0
    merged["risk_free_index"] = (1.0 + merged["risk_free"]).cumprod() * 100.0
    running_max = merged["equity_brl"].cummax().clip(lower=initial_equity)
    merged["drawdown"] = merged["equity_brl"] / running_max - 1.0

    series = [
        {
            "date": row.date.date().isoformat(),
            "strategy_index": round(float(row.strategy_index), 8),
            "risk_free_index": round(float(row.risk_free_index), 8),
            "drawdown": round(float(row.drawdown), 8),
        }
        for row in merged.itertuples(index=False)
    ]
    return {
        "schema_version": 1,
        "scope": "sealed holdout 2020/21–2024/25",
        "initial_equity_brl": initial_equity,
        "method": "strategy equity / initial equity; compounded daily local risk-free",
        "source_artifacts": [
            "data/processed/holdout_v1/10_metrics.json",
            "data/interim/holdout/h4_controls.parquet",
        ],
        "series": series,
    }


def main() -> None:
    args = parse_args()
    payload = build(args.metrics, args.controls)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.output} ({len(payload['series'])} sessions)")


if __name__ == "__main__":
    main()
