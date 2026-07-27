"""Snapshot offline de eventos: reprodução e separação B3/fallback."""

import json
from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.events_snapshot import (
    events_from_snapshot,
    load_snapshot,
    make_snapshot,
    ticker_snapshot,
    write_snapshot,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _capture() -> dict[str, object]:
    b3_cash = json.loads((FIXTURES / "b3_cash_slc.json").read_text(encoding="utf-8"))["results"]
    b3_stock = json.loads((FIXTURES / "b3_stock_mglu.json").read_text(encoding="utf-8"))[
        "stockDividends"
    ]
    si = json.loads((FIXTURES / "statusinvest_slc.json").read_text(encoding="utf-8"))[
        "assetEarningsModels"
    ]
    return ticker_snapshot(
        ticker="SLCE3",
        trading_name="SLC AGRICOLA",
        issuing_company="SLC AGRICOLA",
        b3_cash_rows=b3_cash,
        b3_stock_rows=b3_stock,
        statusinvest_rows=si,
        cutoff="2024-12-31",
    )


def test_snapshot_preserva_fontes_separadas_e_hashes_estaveis():
    one = _capture()
    two = _capture()
    assert one["canonical_payload_sha256"] == two["canonical_payload_sha256"]
    assert one["cash_b3"]
    assert one["cash_statusinvest"]
    assert one["cash_b3"] is not one["cash_statusinvest"]


def test_cutoff_remove_evento_futuro_sem_mudar_hash_da_resposta():
    full = _capture()
    b3_cash = json.loads((FIXTURES / "b3_cash_slc.json").read_text(encoding="utf-8"))["results"]
    si = json.loads((FIXTURES / "statusinvest_slc.json").read_text(encoding="utf-8"))[
        "assetEarningsModels"
    ]
    short = ticker_snapshot(
        ticker="SLCE3",
        trading_name="SLC AGRICOLA",
        issuing_company="SLC AGRICOLA",
        b3_cash_rows=b3_cash,
        b3_stock_rows=[],
        statusinvest_rows=si,
        cutoff="2022-12-31",
    )
    assert (
        short["canonical_payload_sha256"]["b3_cash"] == full["canonical_payload_sha256"]["b3_cash"]
    )
    assert all(row["cum_date"] <= "2022-12-31" for row in short["cash_b3"])


def test_roundtrip_offline(tmp_path: Path):
    payload = make_snapshot(
        {"SLCE3": _capture()},
        cutoff="2024-12-31",
        retrieved_at="2026-07-20T20:00:00Z",
    )
    path = tmp_path / "events.json"
    write_snapshot(payload, path)
    loaded = load_snapshot(path)
    assert loaded["scope"]["purpose"] == "development_prices"
    b3, fallback, stock = events_from_snapshot(loaded, "SLCE3")
    assert b3 and fallback and stock
    assert all(isinstance(event.cum_date, pd.Timestamp) for event in b3 + fallback + stock)


def test_snapshot_aceita_escopo_explicito_do_holdout():
    payload = make_snapshot(
        {"SLCE3": _capture()},
        cutoff="2025-12-31",
        retrieved_at="2026-07-20T20:00:00Z",
        purpose="holdout_prices",
    )
    assert payload["scope"] == {
        "end_date": "2025-12-31",
        "purpose": "holdout_prices",
    }


def test_identidade_interna_divergente_falha():
    with pytest.raises(ValueError, match="divergem"):
        make_snapshot(
            {"SLCE3": _capture() | {"ticker": "AGRO3"}},
            cutoff="2024-12-31",
            retrieved_at="2026-07-20T20:00:00Z",
        )


def test_timestamp_precisa_ser_utc():
    with pytest.raises(ValueError, match="UTC"):
        make_snapshot(
            {"SLCE3": _capture()},
            cutoff="2024-12-31",
            retrieved_at="2026-07-20T20:00:00",
        )


def test_ticker_ausente_falha_alto():
    payload = make_snapshot(
        {"SLCE3": _capture()},
        cutoff="2024-12-31",
        retrieved_at="2026-07-20T20:00:00Z",
    )
    with pytest.raises(KeyError, match="ausente"):
        events_from_snapshot(payload, "SMTO3")
