"""Parsers e downloader dos controles H4 com fixtures reais Yahoo/FRED."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.h4_market import (
    COMMODITY_ETFS,
    FRED_DAILY_FX_SERIES,
    YAHOO_CHART_URL,
    download_h4_market,
    parse_fred_daily_fx,
    parse_yahoo_adjusted,
)

FIXTURES = Path(__file__).parent / "fixtures"
YAHOO = FIXTURES / "yahoo_soyb_sample.json"
FRED = FIXTURES / "fred_dexbzus_sample.csv"


def test_parse_yahoo_fixture_real() -> None:
    panel = parse_yahoo_adjusted(YAHOO, "soy")
    assert list(panel.columns) == ["ref_date", "control", "symbol", "adjusted_close"]
    assert len(panel) == 7
    assert panel.iloc[0]["ref_date"] == pd.Timestamp("2024-01-02")
    assert panel.iloc[0]["adjusted_close"] == pytest.approx(26.549999237060547)
    assert panel["symbol"].unique().tolist() == ["SOYB"]


def test_parse_yahoo_falha_em_ticker_nulo_e_schema() -> None:
    payload = json.loads(YAHOO.read_text())
    payload["chart"]["result"][0]["meta"]["symbol"] = "CORN"
    with pytest.raises(ValueError, match="ticker Yahoo divergente"):
        parse_yahoo_adjusted(json.dumps(payload), "soy")
    payload["chart"]["result"][0]["meta"]["symbol"] = "SOYB"
    payload["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"][0] = None
    with pytest.raises(ValueError, match="ausente"):
        parse_yahoo_adjusted(json.dumps(payload), "soy")
    with pytest.raises(ValueError, match="schema"):
        parse_yahoo_adjusted("{}", "soy")


def test_parse_fred_diario_descarta_feriado_sem_inventar_zero() -> None:
    panel = parse_fred_daily_fx(FRED)
    assert len(panel) == 7
    assert pd.Timestamp("2024-01-01") not in panel["ref_date"].tolist()
    assert panel.iloc[0]["brl_per_usd"] == pytest.approx(4.8943)
    assert panel.iloc[-1]["brl_per_usd"] == pytest.approx(4.8929)


class _FakeResponse:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self) -> None:
        pass


class _FakeSession:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        if "fredgraph.csv" in url:
            return _FakeResponse(FRED.read_bytes())
        symbol = url.rsplit("/", 1)[-1]
        payload = json.loads(YAHOO.read_text())
        payload["chart"]["result"][0]["meta"]["symbol"] = symbol
        return _FakeResponse(json.dumps(payload).encode())


def test_downloader_valida_cache_e_grava_quatro_manifestos(tmp_path) -> None:
    session = _FakeSession()
    paths = download_h4_market(
        start="2024-01-01",
        end="2024-01-11",
        dest_dir=tmp_path / "raw",
        manifest_dir=tmp_path / "manifests",
        session=session,
    )
    assert set(paths) == {*COMMODITY_ETFS, "usdbrl"}
    assert len(session.calls) == 4
    assert session.calls[0]["url"] == YAHOO_CHART_URL.format(symbol="SOYB")
    assert session.calls[-1]["url"].endswith(f"id={FRED_DAILY_FX_SERIES}")
    manifests = sorted((tmp_path / "manifests").glob("h4_*.json"))
    assert len(manifests) == 4
    payloads = [json.loads(path.read_text()) for path in manifests]
    assert {payload["role"] for payload in payloads} == {
        "soy",
        "corn_second",
        "sugar",
        "usdbrl",
    }
    assert all(len(payload["sha256"]) == 64 for payload in payloads)

    download_h4_market(
        start="2024-01-01",
        end="2024-01-11",
        dest_dir=tmp_path / "raw",
        manifest_dir=tmp_path / "manifests",
        session=session,
    )
    assert len(session.calls) == 4


def test_cache_sem_manifesto_falha_alto(tmp_path) -> None:
    session = _FakeSession()
    paths = download_h4_market(
        start="2024-01-01",
        end="2024-01-11",
        dest_dir=tmp_path / "raw",
        manifest_dir=tmp_path / "manifests",
        session=session,
    )
    manifest = next((tmp_path / "manifests").glob("h4_yahoo_soy_*.json"))
    manifest.unlink()
    assert paths["soy"].is_file()
    with pytest.raises(FileNotFoundError, match="sem manifesto"):
        download_h4_market(
            start="2024-01-01",
            end="2024-01-11",
            dest_dir=tmp_path / "raw",
            manifest_dir=tmp_path / "manifests",
            session=session,
        )
