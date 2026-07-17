"""Testes da ingestão de precipitação CHIRPS (docs/02_DADOS.md §1.1).

Fixtures em `tests/fixtures/chirps_{prelim,final}_20240115.tif.gz` são **recortes reais** do
grid global p05 do CHIRPS de 15/01/2024 (janela lat −16..−8, lon −60..−44 — Brasil central,
cobrindo o médio-norte de MT e o oeste da Bahia), baixados ao vivo em 2026-07-16. Cada recorte
preserva as tags geo (`ModelPixelScale`, `ModelTiepoint`) do próprio recorte, então exercita o
mesmo caminho de leitura auto-descrita que o raster global. O par prelim/final é o mesmo dia:
a diferença entre eles é a **revisão de vintage** que a fonte primária existe para medir.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantagro.ingest.chirps import (
    DEFAULT_BOXES,
    NODATA,
    GeoTransform,
    assert_global_grid,
    build_chirps_panel,
    chirps_url,
    download_chirps,
    extract_boxes,
    read_chirps_grid,
)
from quantagro.validate.pit import AVAIL_COL, available_asof, stamp_avail_date

FIXTURES = Path(__file__).parent / "fixtures"
PRELIM = FIXTURES / "chirps_prelim_20240115.tif.gz"
FINAL = FIXTURES / "chirps_final_20240115.tif.gz"


class TestUrl:
    def test_final_e_prelim(self):
        u_final = chirps_url("2024-01-15", "final")
        u_prelim = chirps_url("2024-01-15", "prelim")
        assert u_final.endswith("/global_daily/tifs/p05/2024/chirps-v2.0.2024.01.15.tif.gz")
        assert u_prelim.endswith("/prelim/global_daily/tifs/p05/2024/chirps-v2.0.2024.01.15.tif.gz")
        # o prelim mora sob /prelim/, o final não
        assert "/prelim/" in u_prelim and "/prelim/" not in u_final

    def test_kind_invalido(self):
        with pytest.raises(ValueError, match="kind desconhecido"):
            chirps_url("2024-01-15", "provisorio")


class TestReadGrid:
    def test_le_recorte_e_geotransform(self):
        arr, gt = read_chirps_grid(FINAL)
        assert arr.shape == (160, 320)
        assert arr.dtype == np.float32
        assert gt == GeoTransform(origin_lon=-60.0, origin_lat=-8.0, pixel_deg=0.05)

    def test_le_gzip_e_bytes_iguais(self):
        # ler do caminho (.tif.gz) ou dos bytes já lidos deve dar o mesmo grid
        a1, _ = read_chirps_grid(PRELIM)
        a2, _ = read_chirps_grid(PRELIM.read_bytes())
        assert np.array_equal(a1, a2)

    def test_assert_global_grid_rejeita_recorte(self):
        # a tripwire de formato global não vale para um recorte — deve falhar alto
        arr, gt = read_chirps_grid(FINAL)
        with pytest.raises(ValueError, match="shape inesperado"):
            assert_global_grid(arr, gt)


class TestExtractBoxes:
    def test_valores_sanos_e_mesmas_chaves(self):
        arr, gt = read_chirps_grid(FINAL)
        out = extract_boxes(arr, gt, DEFAULT_BOXES)
        assert set(out) == set(DEFAULT_BOXES)
        for v in out.values():
            assert 0.0 <= v < 500.0  # mm/dia num intervalo fisicamente plausível

    def test_ignora_nodata(self):
        # grid sintético 2x2: metade nodata; a média deve usar só as células válidas
        gt = GeoTransform(origin_lon=0.0, origin_lat=0.0, pixel_deg=0.05)
        arr = np.array([[10.0, NODATA], [20.0, 30.0]], dtype="float32")
        box = {"tudo": (-1.0, 0.0, 0.0, 1.0)}
        out = extract_boxes(arr, gt, box)
        assert out["tudo"] == pytest.approx((10.0 + 20.0 + 30.0) / 3)

    def test_caixa_fora_do_grid_vira_nan(self):
        gt = GeoTransform(origin_lon=0.0, origin_lat=0.0, pixel_deg=0.05)
        arr = np.zeros((10, 10), dtype="float32")
        out = extract_boxes(arr, gt, {"longe": (40.0, 45.0, 40.0, 45.0)})
        assert np.isnan(out["longe"])

    def test_caixa_toda_nodata_vira_nan(self):
        gt = GeoTransform(origin_lon=0.0, origin_lat=0.0, pixel_deg=0.05)
        arr = np.full((4, 4), NODATA, dtype="float32")
        out = extract_boxes(arr, gt, {"oceano": (-0.2, 0.0, 0.0, 0.2)})
        assert np.isnan(out["oceano"])


class TestPanel:
    def test_painel_arrumado(self):
        panel = build_chirps_panel(
            [("2024-01-15", "prelim", PRELIM), ("2024-01-15", "final", FINAL)],
            DEFAULT_BOXES,
        )
        assert list(panel.columns) == ["ref_date", "region", "kind", "precip_mm"]
        assert len(panel) == 2 * len(DEFAULT_BOXES)
        assert set(panel["kind"]) == {"prelim", "final"}
        assert panel["ref_date"].dtype.kind == "M"

    def test_vintage_prelim_difere_do_final(self):
        # o valor de prelim (o que existia na época) não é igual ao final (revisado) —
        # é justamente isso que faz do CHIRPS a fonte primária com vintage
        panel = build_chirps_panel(
            [("2024-01-15", "prelim", PRELIM), ("2024-01-15", "final", FINAL)],
            {"MT_norte": DEFAULT_BOXES["MT_norte"]},
        )
        piv = panel.pivot_table(index="region", columns="kind", values="precip_mm")
        assert piv.loc["MT_norte", "prelim"] != piv.loc["MT_norte", "final"]

    def test_kind_invalido(self):
        with pytest.raises(ValueError, match="kind desconhecido"):
            build_chirps_panel([("2024-01-15", "xxx", FINAL)], DEFAULT_BOXES)

    def test_painel_vazio(self):
        panel = build_chirps_panel([], DEFAULT_BOXES)
        assert list(panel.columns) == ["ref_date", "region", "kind", "precip_mm"]
        assert panel.empty


class TestPointInTime:
    def test_carimbo_lag_7d_e_filtro_asof(self):
        panel = build_chirps_panel([("2024-01-15", "final", FINAL)], DEFAULT_BOXES)
        st = stamp_avail_date(panel, lag_days=7)
        assert (st[AVAIL_COL] == pd.Timestamp("2024-01-22")).all()
        # antes de avail_date nenhuma linha é visível; a partir dela, todas
        assert available_asof(st, "2024-01-21").empty
        assert len(available_asof(st, "2024-01-22")) == len(DEFAULT_BOXES)


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
    def test_baixa_grava_arquivo_e_manifesto(self, tmp_path):
        content = FINAL.read_bytes()
        sess = _FakeSession(content)
        out = download_chirps(
            "2024-01-15",
            "final",
            dest_dir=tmp_path / "raw",
            manifest_dir=tmp_path / "manifests",
            session=sess,
        )
        assert out.exists() and out.read_bytes() == content
        assert out.name == "chirps-v2.0.2024.01.15.final.tif.gz"
        manifests = list((tmp_path / "manifests").glob("chirps_final_20240115.json"))
        assert len(manifests) == 1
        texto = manifests[0].read_text(encoding="utf-8")
        assert '"sha256"' in texto and '"kind": "final"' in texto

    def test_prelim_e_final_nomes_distintos(self, tmp_path):
        sess = _FakeSession(b"x")
        for kind in ("prelim", "final"):
            download_chirps(
                "2024-01-15", kind, dest_dir=tmp_path, manifest_dir=tmp_path, session=sess
            )
        nomes = {p.name for p in tmp_path.glob("*.tif.gz")}
        assert nomes == {
            "chirps-v2.0.2024.01.15.prelim.tif.gz",
            "chirps-v2.0.2024.01.15.final.tif.gz",
        }

    def test_cache_nao_rebaixa(self, tmp_path):
        sess = _FakeSession(b"x")
        for _ in range(2):
            download_chirps(
                "2024-01-15", "final", dest_dir=tmp_path, manifest_dir=tmp_path, session=sess
            )
        assert sess.calls == 1

    def test_kind_invalido(self):
        with pytest.raises(ValueError, match="kind desconhecido"):
            download_chirps("2024-01-15", "xxx")
