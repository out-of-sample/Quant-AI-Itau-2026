"""Testes da ingestão ONI com amostra real NOAA/CPC capturada em 2026-07-16."""

import json
from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.oni import (
    ONI_URL,
    SEASON_CENTER_MONTH,
    download_oni,
    parse_oni,
    stamp_oni_avail_date,
)
from quantagro.validate.pit import available_asof

FIXTURE = Path(__file__).parent / "fixtures" / "oni_sample.txt"


class TestParse:
    def test_fixture_real_e_schema(self):
        df = parse_oni(FIXTURE)
        assert list(df.columns) == ["ref_date", "season", "year", "sst_c", "oni_c"]
        assert len(df) == 11
        assert df["ref_date"].dtype.kind == "M"
        row = df[(df["year"] == 2023) & (df["season"] == "MJJ")].iloc[0]
        assert row["ref_date"] == pd.Timestamp("2023-06-30")
        assert row["sst_c"] == pytest.approx(28.42)
        assert row["oni_c"] == pytest.approx(0.84)

    def test_todas_as_temporadas_tem_mes_central_unico(self):
        assert list(SEASON_CENTER_MONTH) == [
            "DJF",
            "JFM",
            "FMA",
            "MAM",
            "AMJ",
            "MJJ",
            "JJA",
            "JAS",
            "ASO",
            "SON",
            "OND",
            "NDJ",
        ]
        assert set(SEASON_CENTER_MONTH.values()) == set(range(1, 13))

    def test_aceita_bytes_e_texto(self):
        path = parse_oni(FIXTURE)
        raw = parse_oni(FIXTURE.read_bytes())
        text = parse_oni(FIXTURE.read_text(encoding="ascii"))
        pd.testing.assert_frame_equal(path, raw)
        pd.testing.assert_frame_equal(path, text)

    def test_schema_mudou_falha_alto(self):
        with pytest.raises(ValueError, match="schema ONI inesperado"):
            parse_oni("SEASON YEAR VALUE\nDJF 2020 0.1\n")

    def test_temporada_desconhecida_falha_alto(self):
        with pytest.raises(ValueError, match="temporadas ONI desconhecidas"):
            parse_oni("SEAS YR TOTAL ANOM\nXYZ 2020 25.0 0.1\n")

    def test_duplicata_falha_alto(self):
        text = "SEAS YR TOTAL ANOM\nDJF 2020 25.0 0.1\nDJF 2020 25.1 0.2\n"
        with pytest.raises(ValueError, match="duplicata"):
            parse_oni(text)


class TestPointInTime:
    def test_djf_publica_em_marco_e_estabiliza_em_maio(self):
        df = parse_oni(FIXTURE)
        stamped = stamp_oni_avail_date(df)
        row = stamped[(stamped["year"] == 2015) & (stamped["season"] == "DJF")].iloc[0]
        assert row["ref_date"] == pd.Timestamp("2015-01-31")
        assert row["initial_avail_date"] == pd.Timestamp("2015-03-05")
        assert row["avail_date"] == pd.Timestamp("2015-05-05")

    def test_ndj_atravessa_ano_corretamente(self):
        df = parse_oni("SEAS YR TOTAL ANOM\nNDJ 2024 26.1 -0.4\n")
        row = stamp_oni_avail_date(df).iloc[0]
        assert row["ref_date"] == pd.Timestamp("2024-12-31")
        assert row["initial_avail_date"] == pd.Timestamp("2025-02-05")
        assert row["avail_date"] == pd.Timestamp("2025-04-05")

    def test_available_asof_respeita_estabilizacao(self):
        stamped = stamp_oni_avail_date(parse_oni(FIXTURE))
        before = available_asof(stamped, "2015-05-04")
        on_date = available_asof(stamped, "2015-05-05")
        assert not ((before["year"] == 2015) & (before["season"] == "DJF")).any()
        assert ((on_date["year"] == 2015) & (on_date["season"] == "DJF")).any()

    def test_lag_inicial_disponivel_so_em_robustez(self):
        row = stamp_oni_avail_date(parse_oni(FIXTURE), revision_window_months=0).iloc[0]
        assert row["avail_date"] == row["initial_avail_date"]

    def test_janela_negativa_e_erro(self):
        with pytest.raises(ValueError, match="não pode ser negativo"):
            stamp_oni_avail_date(parse_oni(FIXTURE), revision_window_months=-1)


class _FakeResponse:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        pass


class _FakeSession:
    def __init__(self, content: bytes):
        self.content = content
        self.calls = []

    def get(self, url, timeout=None):
        self.calls.append((url, timeout))
        return _FakeResponse(self.content)


class TestDownload:
    def test_baixa_valida_e_grava_manifesto(self, tmp_path):
        session = _FakeSession(FIXTURE.read_bytes())
        path = download_oni(
            dest_dir=tmp_path / "raw",
            manifest_dir=tmp_path / "manifests",
            session=session,
        )
        assert path.exists() and path.read_bytes() == FIXTURE.read_bytes()
        assert session.calls[0][0] == ONI_URL
        manifests = list((tmp_path / "manifests").glob("oni_*.json"))
        assert len(manifests) == 1
        manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
        assert manifest["source"] == "NOAA-CPC-ONI"
        assert manifest["dataset"] == "ERSST.v5"
        assert manifest["latest_season"] == "AMJ"
        assert manifest["latest_year"] == 2026
        assert manifest["revision_window_months"] == 2
        assert len(manifest["sha256"]) == 64

    def test_cache_nao_rebaixa(self, tmp_path):
        session = _FakeSession(FIXTURE.read_bytes())
        for _ in range(2):
            download_oni(
                dest_dir=tmp_path / "raw",
                manifest_dir=tmp_path / "manifests",
                session=session,
            )
        assert len(session.calls) == 1

    def test_resposta_invalida_nao_e_persistida(self, tmp_path):
        session = _FakeSession(b"not an ONI file")
        with pytest.raises(ValueError, match="schema ONI inesperado"):
            download_oni(
                dest_dir=tmp_path / "raw",
                manifest_dir=tmp_path / "manifests",
                session=session,
            )
        assert not list((tmp_path / "raw").glob("oni_*.txt"))
