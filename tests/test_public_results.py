"""Regression checks for the repository's public results layer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "results/data/holdout_v1"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_public_headline_metrics_match_sealed_claims() -> None:
    portfolio = read_json(PUBLIC / "02_portfolio.json")["payload"]["scenarios"]["base"]
    hprime = read_json(PUBLIC / "01_primary_hprime.json")["payload"]
    h4 = read_json(PUBLIC / "05_h4_spanning.json")["payload"]["extended"]
    report = read_json(PUBLIC / "12_descriptive_report.json")
    claims = read_json(ROOT / "data/reference/holdout_result_v1.json")["claims"]

    assert portfolio["total_return"] == pytest.approx(0.1697408393116817)
    assert portfolio["max_drawdown"] == pytest.approx(-0.20916793291376568)
    assert hprime["passed"] is True
    assert hprime["pvalue"] == pytest.approx(0.0625)
    assert h4["passed"] is False
    assert h4["alpha_t"] == pytest.approx(-1.0297059176066865)
    assert report["risk"]["excess_sharpe"] == pytest.approx(-0.5031279991425698)
    assert claims == {
        "climate_alpha_evidence": False,
        "oos_strategy_evidence": True,
        "positive_oos_pnl": True,
    }


def test_compact_public_series_reconciles_endpoints() -> None:
    payload = read_json(PUBLIC / "public_series.json")
    series = payload["series"]

    assert len(series) == 1186
    assert series[0]["date"] == "2021-01-08"
    assert series[-1]["date"] == "2025-10-08"
    assert series[-1]["strategy_index"] == pytest.approx(116.97408393)
    assert series[-1]["risk_free_index"] == pytest.approx(163.30629146)
    assert min(row["drawdown"] for row in series) == pytest.approx(-0.20916793)
    assert all(
        later["risk_free_index"] >= earlier["risk_free_index"]
        for earlier, later in zip(series, series[1:], strict=False)
    )


def test_public_figures_are_accessible_and_data_sourced() -> None:
    figures = sorted((ROOT / "results/figures").glob("*.svg"))
    assert len(figures) == 12
    for figure in figures:
        svg = figure.read_text(encoding="utf-8")
        assert 'role="img"' in svg
        assert "<title" in svg
        assert "<desc" in svg
        assert "FONTE ·" in svg


def test_readme_uses_repository_figures_not_report_screenshots() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "results/figures/pipeline.svg" in readme
    assert "results/figures/performance.svg" in readme
    assert "resultado-holdout.png" not in readme
    assert readme.index("## A pergunta") < readme.index("## Reproduzir e verificar")
