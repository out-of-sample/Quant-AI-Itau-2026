"""Testes da ingestão de temperatura NASA POWER (docs/02_DADOS.md §1.2).

Fixtures em `tests/fixtures/power_{definitivo_2015,provisorio_2026}.json` são **respostas reais**
do endpoint diário por ponto (centroide de MT), baixadas ao vivo em 2026-07-16. A de 2015 vem com
`header.sources = ['MERRA2', 'POWER']` (definitivo); a recente com `['GEOSIT', 'POWER']`
(provisório) — o par existe para travar a classificação de vintage, que é a razão de o POWER ser
fonte secundária. Como a fonte não preserva vintage, essa proveniência por resposta é o que nos
deixa declarar e medir a contaminação por revisão.
"""

from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.power import (
    DEFAULT_POINTS,
    FILL_VALUE,
    TEMPERATURE_PARAMS,
    build_power_panel,
    classify_vintage,
    download_power,
    parse_power,
    power_request_params,
    power_url,
)
from quantagro.validate.pit import AVAIL_COL, available_asof, stamp_avail_date

FIXTURES = Path(__file__).parent / "fixtures"
DEFINITIVO = FIXTURES / "power_definitivo_2015.json"
PROVISORIO = FIXTURES / "power_provisorio_2026.json"


class TestClassifyVintage:
    def test_definitivo_so_merra2(self):
        assert classify_vintage(["MERRA2", "POWER"]) == "definitivo"

    def test_provisorio_com_geosit_ou_flashflux(self):
        assert classify_vintage(["GEOSIT", "POWER"]) == "provisorio"
        assert classify_vintage(["FLASHFLUX", "MERRA2"]) == "provisorio"  # provisório domina

    def test_desconhecido(self):
        assert classify_vintage([]) == "desconhecido"
        assert classify_vintage(None) == "desconhecido"


class TestUrl:
    def test_params_e_url(self):
        p = power_request_params(-12.5, -55.5, "2015-01-01", "2015-01-10")
        assert p["parameters"] == "T2M,T2M_MAX,T2M_MIN"
        assert p["community"] == "AG" and p["format"] == "JSON"
        assert p["start"] == "20150101" and p["end"] == "20150110"
        assert p["latitude"] == "-12.5" and p["longitude"] == "-55.5"
        assert power_url(-12.5, -55.5, "2015-01-01", "2015-01-10").startswith(
            "https://power.larc.nasa.gov/api/temporal/daily/point?"
        )

    def test_pontos_default_casam_com_regioes_do_chirps(self):
        from quantagro.ingest.chirps import DEFAULT_BOXES

        assert set(DEFAULT_POINTS) == set(DEFAULT_BOXES)  # join por `region` chuva×temperatura


class TestParse:
    def test_painel_arrumado_e_vintage(self):
        df = parse_power(DEFINITIVO, region="MT_norte")
        assert list(df.columns) == ["ref_date", "region", "param", "value", "source_vintage"]
        assert df["ref_date"].dtype.kind == "M"
        assert set(df["param"]) == set(TEMPERATURE_PARAMS)
        assert (df["source_vintage"] == "definitivo").all()
        assert (df["region"] == "MT_norte").all()
        # 10 dias × 3 parâmetros
        assert len(df) == 30

    def test_provisorio_classificado(self):
        df = parse_power(PROVISORIO, region="MATOPIBA_BA")
        assert (df["source_vintage"] == "provisorio").all()

    def test_fill_value_vira_na(self):
        synth = {
            "header": {"sources": ["MERRA2"]},
            "properties": {"parameter": {"T2M": {"20200101": FILL_VALUE, "20200102": 25.5}}},
        }
        df = parse_power(synth, region="X")
        v0 = df.loc[df["ref_date"] == pd.Timestamp("2020-01-01"), "value"]
        v1 = df.loc[df["ref_date"] == pd.Timestamp("2020-01-02"), "value"]
        assert v0.isna().all()  # fill nunca é tratado como temperatura real
        assert float(v1.iloc[0]) == pytest.approx(25.5)

    def test_aceita_dict_bytes_e_path(self):
        d = parse_power(DEFINITIVO)
        b = parse_power(DEFINITIVO.read_bytes())
        assert d.shape == b.shape and len(d) == 30

    def test_vazio(self):
        empty = {"header": {"sources": ["MERRA2"]}, "properties": {"parameter": {}}}
        df = parse_power(empty)
        assert list(df.columns) == ["ref_date", "region", "param", "value", "source_vintage"]
        assert df.empty


class TestPanel:
    def test_concatena_regioes_e_vintages(self):
        panel = build_power_panel([("MT_norte", DEFINITIVO), ("MATOPIBA_BA", PROVISORIO)])
        assert set(panel["region"]) == {"MT_norte", "MATOPIBA_BA"}
        assert set(panel["source_vintage"]) == {"definitivo", "provisorio"}
        assert len(panel) == 60

    def test_vazio(self):
        panel = build_power_panel([])
        assert list(panel.columns) == ["ref_date", "region", "param", "value", "source_vintage"]
        assert panel.empty


class TestPointInTime:
    def test_carimbo_lag_3d_e_filtro_asof(self):
        panel = build_power_panel([("MT_norte", DEFINITIVO)])
        st = stamp_avail_date(panel, lag_days=3)
        # 01/01/2015 fica visível só a partir de 04/01 (lag 3d corridos)
        linha = st[st["ref_date"] == pd.Timestamp("2015-01-01")]
        assert (linha[AVAIL_COL] == pd.Timestamp("2015-01-04")).all()
        # em 03/01 nada ainda está disponível; em 04/01 entra o 01/01, mas não o 02/01 (avail 05/01)
        assert available_asof(st, "2015-01-03").empty
        refs_0104 = set(available_asof(st, "2015-01-04")["ref_date"])
        assert pd.Timestamp("2015-01-01") in refs_0104
        assert pd.Timestamp("2015-01-02") not in refs_0104


class _FakeResp:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        pass


class _FakeSession:
    def __init__(self, content: bytes):
        self._content = content
        self.calls = 0

    def get(self, url, timeout=None):
        self.calls += 1
        return _FakeResp(self._content)


class TestDownload:
    def test_baixa_grava_arquivo_e_manifesto_de_vintage(self, tmp_path):
        content = DEFINITIVO.read_bytes()
        sess = _FakeSession(content)
        out = download_power(
            {"MT_norte": (-12.5, -55.5)},
            "2015-01-01",
            "2015-01-10",
            dest_dir=tmp_path / "raw",
            manifest_dir=tmp_path / "man",
            session=sess,
        )
        p = out["MT_norte"]
        assert p.exists() and p.read_bytes() == content
        assert p.name.startswith("power_MT_norte_20150101_20150110_")
        man = list((tmp_path / "man").glob("power_MT_norte_*.json"))
        assert len(man) == 1
        meta = pd.read_json(man[0], typ="series")
        assert meta["vintage"] == "definitivo"  # o manifesto registra a proveniência de vintage
        assert meta["source"] == "NASA-POWER"
        assert "sha256" in meta and meta["api_version"]

    def test_cache_nao_rebaixa(self, tmp_path):
        sess = _FakeSession(DEFINITIVO.read_bytes())
        for _ in range(2):
            download_power(
                {"MT_norte": (-12.5, -55.5)},
                "2015-01-01",
                "2015-01-10",
                dest_dir=tmp_path,
                manifest_dir=tmp_path,
                session=sess,
            )
        assert sess.calls == 1
