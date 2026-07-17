"""Testes da malha municipal fixa do IBGE.

``ibge_mt_2013_sample.zip`` contém dois registros reais extraídos sem simplificação do arquivo
oficial ``municipio_2013/MT/mt_municipios.zip``: Acorizal e Cuiabá, com SHP/SHX/DBF/PRJ/CPG.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.ibge_geometry import (
    GEOMETRY_AVAIL_DATE,
    GEOMETRY_EDITION,
    attach_geometry,
    download_geometry,
    geometry_url,
    parse_geometry,
)

FIXTURE = Path(__file__).parent / "fixtures" / "ibge_mt_2013_sample.zip"


class TestUrl:
    def test_url_historica_fixa(self):
        assert geometry_url("MT").endswith("/municipio_2013/MT/mt_municipios.zip")

    def test_outra_edicao_e_uf_falham(self):
        with pytest.raises(ValueError, match="edição congelada"):
            geometry_url("MT", edition=2022)
        with pytest.raises(ValueError, match="UF fora"):
            geometry_url("SP")


class TestParse:
    def test_fixture_real_e_schema_parquet_safe(self):
        df = parse_geometry(FIXTURE, "MT")
        assert len(df) == 2
        assert set(df["municipality_code"]) == {"5100102", "5103403"}
        assert (df["geometry_edition"] == GEOMETRY_EDITION).all()
        assert (df["avail_date"] == GEOMETRY_AVAIL_DATE).all()
        assert all(isinstance(value, str) for value in df["geometry_json"])
        assert {json.loads(value)["type"] for value in df["geometry_json"]} <= {
            "Polygon",
            "MultiPolygon",
        }

    def test_bbox_fisicamente_no_brasil(self):
        df = parse_geometry(FIXTURE, "MT")
        assert (df["min_lon"] < df["max_lon"]).all()
        assert (df["min_lat"] < df["max_lat"]).all()
        assert df["max_lon"].max() < -30

    def test_uf_incompatível_falha(self):
        with pytest.raises(ValueError, match="incompatível"):
            parse_geometry(FIXTURE, "GO")

    def test_timestamp_do_artefato_e_tripwire(self):
        import io
        import zipfile

        source = zipfile.ZipFile(FIXTURE)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as changed:
            for member in source.infolist():
                info = zipfile.ZipInfo(member.filename, date_time=(2026, 1, 1, 0, 0, 0))
                changed.writestr(info, source.read(member.filename))
        with pytest.raises(ValueError, match="timestamp interno"):
            parse_geometry(buffer.getvalue(), "MT")

    def test_bytes_e_path_equivalentes(self):
        a = parse_geometry(FIXTURE, "MT")
        b = parse_geometry(FIXTURE.read_bytes(), "MT")
        pd.testing.assert_frame_equal(a, b)


class TestAttach:
    def test_anexa_geometria_sem_perder_peso(self):
        geometry = parse_geometry(FIXTURE, "MT")
        weights = pd.DataFrame(
            {
                "municipality_code": ["5100102", "5103403"],
                "quantity_tonnes": [1.0, 3.0],
                "within_uf_weight": [0.25, 0.75],
            }
        )
        out = attach_geometry(weights, geometry)
        assert out["within_uf_weight"].sum() == 1.0
        assert out["geometry_json"].notna().all()

    def test_municipio_positivo_sem_poligono_falha(self):
        geometry = parse_geometry(FIXTURE, "MT")
        weights = pd.DataFrame(
            {
                "municipality_code": ["5199999"],
                "quantity_tonnes": [1.0],
                "within_uf_weight": [1.0],
            }
        )
        with pytest.raises(ValueError, match="sem geometria fixa"):
            attach_geometry(weights, geometry)


class _Resp:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class _Session:
    def __init__(self, content):
        self.content = content
        self.calls = 0

    def get(self, url, timeout=None):
        self.calls += 1
        return _Resp(self.content)


class TestDownload:
    def test_zip_e_manifesto(self, tmp_path):
        session = _Session(FIXTURE.read_bytes())
        out = download_geometry(
            "MT", dest_dir=tmp_path / "raw", manifest_dir=tmp_path / "man", session=session
        )
        assert out.name == "ibge_municipios_2013_mt.zip"
        manifest = next((tmp_path / "man").glob("ibge_municipios_2013_mt.json")).read_text()
        assert '"spatial_policy"' in manifest and '"sha256"' in manifest

    def test_resposta_nao_zip_falha(self, tmp_path):
        with pytest.raises(ValueError, match="ZIP válido"):
            download_geometry(
                "MT",
                dest_dir=tmp_path,
                manifest_dir=tmp_path,
                session=_Session(b"<html>erro</html>"),
            )
