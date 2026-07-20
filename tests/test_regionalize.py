"""Testes da regionalização raster CHIRPS → município IBGE (features/regionalize.py).

Duas famílias: sintética (grade 10×10 de 1°, polígonos desenhados à mão — valida a regra
even-odd, buraco, multipolígono e o fallback de município sub-célula com aritmética que dá
para conferir no papel) e real (malha IBGE 2013 de Acorizal/Cuiabá × recortes reais do
CHIRPS de 15/01/2024 — valida o caminho inteiro e pina os valores como regressão; a área
implícita pelas células casa com a área municipal oficial, e a revisão prelim→final aparece
no nível municipal).
"""

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import tifffile

from quantagro.features.regionalize import (
    municipal_daily_precip,
    municipal_monthly_precip,
    municipality_cell_index,
    points_in_geometry,
)
from quantagro.ingest.chirps import NODATA, GeoTransform
from quantagro.ingest.ibge_geometry import parse_geometry
from quantagro.validate.pit import available_asof, stamp_avail_date

FIXTURES = Path(__file__).parent / "fixtures"
PRELIM = FIXTURES / "chirps_prelim_20240115.tif.gz"
FINAL = FIXTURES / "chirps_final_20240115.tif.gz"
MT_SAMPLE = FIXTURES / "ibge_mt_2013_sample.zip"

# Grade sintética: 10×10 células de 1°, canto superior-esquerdo em (lon 0, lat 10).
# Centros de célula: lon 0.5..9.5 (col 0..9), lat 9.5..0.5 (row 0..9).
GT = GeoTransform(origin_lon=0.0, origin_lat=10.0, pixel_deg=1.0)
SHAPE = (10, 10)


def _ring(lon0, lon1, lat0, lat1):
    """Anel retangular fechado (CCW) de um bbox."""
    return [[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]]


def _geometry_row(code, geometry, uf="MT"):
    coords = np.concatenate([np.asarray(r, dtype=float) for p in _as_polygons(geometry) for r in p])
    return {
        "municipality_code": code,
        "uf": uf,
        "geometry_json": json.dumps(geometry),
        "min_lon": coords[:, 0].min(),
        "max_lon": coords[:, 0].max(),
        "min_lat": coords[:, 1].min(),
        "max_lat": coords[:, 1].max(),
    }


def _as_polygons(geometry):
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    return list(geometry["coordinates"])


def _tif_bytes(arr, gt):
    """GeoTIFF em memória com as mesmas tags geo que o CHIRPS real carrega."""
    buf = io.BytesIO()
    tifffile.imwrite(
        buf,
        np.asarray(arr, dtype=np.float32),
        extratags=[
            (33550, 12, 3, (gt.pixel_deg, gt.pixel_deg, 0.0)),
            (33922, 12, 6, (0.0, 0.0, 0.0, gt.origin_lon, gt.origin_lat, 0.0)),
        ],
    )
    return buf.getvalue()


class TestPointsInGeometry:
    def test_quadrado_e_buraco(self):
        geom = {"type": "Polygon", "coordinates": [_ring(1, 8, 1, 8), _ring(3, 6, 3, 6)]}
        lons = np.array([0.5, 2.5, 4.5, 7.5, 9.5])
        lats = np.array([4.5, 4.5, 4.5, 4.5, 4.5])
        inside = points_in_geometry(lons, lats, geom)
        # fora | dentro | no buraco | dentro | fora
        assert inside.tolist() == [False, True, False, True, False]

    def test_multipoligono_e_uniao(self):
        geom = {
            "type": "MultiPolygon",
            "coordinates": [[_ring(1, 3, 1, 3)], [_ring(6, 8, 6, 8)]],
        }
        lons = np.array([2.5, 7.5, 4.5])
        lats = np.array([2.5, 7.5, 4.5])
        assert points_in_geometry(lons, lats, geom).tolist() == [True, True, False]

    def test_tipo_nao_poligonal_falha(self):
        with pytest.raises(ValueError, match="não poligonal"):
            points_in_geometry(np.array([0.0]), np.array([0.0]), {"type": "Point"})


class TestMunicipalityCellIndex:
    def test_quadrado_seleciona_celulas_com_centro_dentro(self):
        geom = {"type": "Polygon", "coordinates": [_ring(2, 5, 3, 6)]}
        idx = municipality_cell_index(pd.DataFrame([_geometry_row("5100102", geom)]), GT, *SHAPE)
        # centros dentro: lon {2.5, 3.5, 4.5} × lat {3.5, 4.5, 5.5} → 9 células
        assert len(idx) == 9
        assert set(idx["col"]) == {2, 3, 4}
        assert set(idx["row"]) == {4, 5, 6}  # lat 5.5→row 4, 4.5→5, 3.5→6
        assert (idx["cell_source"] == "polygon").all()

    def test_buraco_exclui_celulas(self):
        geom = {"type": "Polygon", "coordinates": [_ring(1, 8, 1, 8), _ring(3, 6, 3, 6)]}
        idx = municipality_cell_index(pd.DataFrame([_geometry_row("5100102", geom)]), GT, *SHAPE)
        # 7×7 centros no anel externo − 3×3 no buraco = 40
        assert len(idx) == 40
        hole = idx[(idx["col"].between(3, 5)) & (idx["row"].between(4, 6))]
        assert hole.empty

    def test_municipio_subcelula_usa_fallback_do_centroide(self):
        # bbox inteiro entre dois centros de célula: nenhum centro dentro
        geom = {"type": "Polygon", "coordinates": [_ring(2.1, 2.3, 3.1, 3.3)]}
        idx = municipality_cell_index(pd.DataFrame([_geometry_row("3157906", geom)]), GT, *SHAPE)
        assert len(idx) == 1
        assert idx["cell_source"].iloc[0] == "nearest_centroid"
        # centroide (2.2, 3.2) → col floor(2.2)=2, row floor(10−3.2)=6
        assert (idx["row"].iloc[0], idx["col"].iloc[0]) == (6, 2)

    def test_poligono_de_agua_nao_municipal_fica_fora(self):
        # RS traz Lagoa Mirim (4300001) e Lagoa dos Patos (4300002) na malha — não são
        # municípios (código de município "0000") e não podem virar linha do painel
        geom = {"type": "Polygon", "coordinates": [_ring(1, 3, 1, 3)]}
        rows = pd.DataFrame(
            [_geometry_row("4300001", geom, uf="RS"), _geometry_row("4311239", geom, uf="RS")]
        )
        idx = municipality_cell_index(rows, GT, *SHAPE)
        assert set(idx["municipality_code"]) == {"4311239"}

    def test_geocodigo_duplicado_falha(self):
        geom = {"type": "Polygon", "coordinates": [_ring(1, 3, 1, 3)]}
        two = pd.DataFrame([_geometry_row("5100102", geom), _geometry_row("5100102", geom)])
        with pytest.raises(ValueError, match="duplicado"):
            municipality_cell_index(two, GT, *SHAPE)

    def test_indice_carrega_constantes_da_grade(self):
        geom = {"type": "Polygon", "coordinates": [_ring(1, 3, 1, 3)]}
        idx = municipality_cell_index(pd.DataFrame([_geometry_row("5100102", geom)]), GT, *SHAPE)
        assert (idx["grid_rows"] == 10).all() and (idx["grid_cols"] == 10).all()
        assert (idx["grid_pixel_deg"] == 1.0).all()


class TestMunicipalDailyPrecip:
    def _index(self):
        geom = {"type": "Polygon", "coordinates": [_ring(2, 5, 3, 6)]}
        return municipality_cell_index(pd.DataFrame([_geometry_row("5100102", geom)]), GT, *SHAPE)

    def test_media_ignora_nodata(self):
        arr = np.full(SHAPE, 4.0, dtype=np.float32)
        arr[4, 2] = NODATA  # uma das 9 células do município vira nodata
        arr[5, 3] = 13.0
        panel = municipal_daily_precip(
            [("2024-01-15", "prelim", _tif_bytes(arr, GT))], self._index()
        )
        assert len(panel) == 1
        row = panel.iloc[0]
        assert row["n_cells"] == 9 and row["n_valid_cells"] == 8
        assert row["precip_mm"] == pytest.approx((7 * 4.0 + 13.0) / 8)

    def test_municipio_todo_nodata_vira_nan_visivel(self):
        arr = np.full(SHAPE, NODATA, dtype=np.float32)
        panel = municipal_daily_precip(
            [("2024-01-15", "final", _tif_bytes(arr, GT))], self._index()
        )
        assert np.isnan(panel["precip_mm"].iloc[0])
        assert panel["n_valid_cells"].iloc[0] == 0

    def test_raster_de_outra_grade_falha(self):
        outra = GeoTransform(origin_lon=-60.0, origin_lat=-8.0, pixel_deg=0.05)
        arr = np.zeros(SHAPE, dtype=np.float32)
        with pytest.raises(ValueError, match="geotransform"):
            municipal_daily_precip([("2024-01-15", "final", _tif_bytes(arr, outra))], self._index())
        with pytest.raises(ValueError, match="shape"):
            municipal_daily_precip(
                [("2024-01-15", "final", _tif_bytes(np.zeros((5, 5)), GT))], self._index()
            )

    def test_kind_invalido_falha(self):
        arr = np.zeros(SHAPE, dtype=np.float32)
        with pytest.raises(ValueError, match="kind desconhecido"):
            municipal_daily_precip([("2024-01-15", "raw", _tif_bytes(arr, GT))], self._index())

    def test_indices_de_grades_diferentes_nao_se_misturam(self):
        idx = self._index()
        other = idx.copy()
        other["grid_pixel_deg"] = 0.05
        with pytest.raises(ValueError, match="mistura grades"):
            municipal_daily_precip([], pd.concat([idx, other], ignore_index=True))

    def test_mensal_normaliza_referencia_para_fim_do_mes(self):
        arr = np.full(SHAPE, 90.0, dtype=np.float32)
        panel = municipal_monthly_precip(
            [("2024-02-01", "prelim", _tif_bytes(arr, GT))], self._index()
        )
        assert panel.iloc[0]["ref_date"] == pd.Timestamp("2024-02-29")
        assert panel.iloc[0]["precip_mm"] == pytest.approx(90.0)


class TestFixturaRealMT:
    def _real(self):
        from quantagro.ingest.chirps import read_chirps_grid

        geo = parse_geometry(MT_SAMPLE, "MT")
        arr, gt = read_chirps_grid(PRELIM)
        return geo, gt, arr.shape

    def test_celulas_casam_com_a_area_municipal(self):
        geo, gt, shape = self._real()
        idx = municipality_cell_index(geo, gt, *shape)
        n = idx.groupby("municipality_code").size()
        # célula p05 ≈ 30,25 km². Acorizal ≈ 840 km² (IBGE) → ~28 células;
        # Cuiabá ≈ 3.500 km² → ~116. Pinado como regressão do PIP real.
        assert n.loc["5100102"] == 27
        assert n.loc["5103403"] == 118
        assert (idx["cell_source"] == "polygon").all()

    def test_painel_real_e_revisao_de_vintage(self):
        geo, gt, shape = self._real()
        idx = municipality_cell_index(geo, gt, *shape)
        panel = municipal_daily_precip(
            [("2024-01-15", "prelim", PRELIM), ("2024-01-15", "final", FINAL)], idx
        )
        assert len(panel) == 4
        assert (panel["n_valid_cells"] == panel["n_cells"]).all()  # MT não tem oceano
        wide = panel.pivot_table(
            index="municipality_code", columns="kind", values="precip_mm", aggfunc="first"
        )
        # regressão dos valores reais (15/01/2024) e prova de que prelim ≠ final
        assert wide.loc["5103403", "prelim"] == pytest.approx(2.668, abs=0.01)
        assert wide.loc["5103403", "final"] == pytest.approx(3.045, abs=0.01)
        assert (wide["prelim"] != wide["final"]).all()

    def test_carimbo_pit_a_jusante(self):
        geo, gt, shape = self._real()
        idx = municipality_cell_index(geo, gt, *shape)
        panel = municipal_daily_precip([("2024-01-15", "prelim", PRELIM)], idx)
        stamped = stamp_avail_date(panel, lag_days=7)
        assert available_asof(stamped, "2024-01-21").empty  # ref+6 → ainda invisível
        vis = available_asof(stamped, "2024-01-22")  # ref+7 → visível
        assert set(vis["municipality_code"]) == {"5100102", "5103403"}
