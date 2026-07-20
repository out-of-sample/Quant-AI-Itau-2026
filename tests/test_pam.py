"""Testes da PAM/SIDRA 1612 e de seu relógio point-in-time.

``pam_mt_sample.json`` é resposta real da API oficial, capturada em 16/07/2026: Acorizal,
Cuiabá e Sorriso, milho/soja, 2022/2023. Ela contém tanto ``-`` (zero SIDRA) quanto valores
observados e prova os códigos 2711/2713 e a unidade 1017 (toneladas).
"""

from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.pam import (
    download_pam,
    pam_url,
    pam_weights_asof,
    parse_pam,
)
from quantagro.ingest.pam_calendar import PAM_RELEASES, pam_avail_map, pam_release

FIXTURE = Path(__file__).parent / "fixtures" / "pam_mt_sample.json"
FIXTURE_COTTON = Path(__file__).parent / "fixtures" / "pam_cotton_sample.json"


class TestCalendar:
    def test_datas_criticas(self):
        assert pam_release(2014).avail_date == pd.Timestamp("2015-11-05")
        assert pam_release(2019).avail_date == pd.Timestamp("2020-10-01")
        assert pam_release(2024).avail_date == pd.Timestamp("2025-09-11")

    def test_todas_as_datas_tem_fonte_oficial(self):
        assert set(PAM_RELEASES) == set(range(2014, 2025))
        assert all(r.source_url.startswith("https://") for r in PAM_RELEASES.values())

    def test_ano_sem_prova_falha(self):
        with pytest.raises(KeyError, match="sem data oficial"):
            pam_release(2025)

    def test_avail_map_indexa_fim_do_ano(self):
        avail = pam_avail_map()
        assert avail[pd.Timestamp("2022-12-31")] == pd.Timestamp("2023-09-14")


class TestUrl:
    def test_query_preserva_nivel_municipal_e_codigos(self):
        url = pam_url("soy", [2022, 2023], ["MT", "GO"])
        assert "/t/1612/n6/in%20n3%2052,51/v/214/p/2022,2023/c81/2713" in url

    def test_milho_total_explicito(self):
        assert pam_url("corn_total", [2023], ["MT"]).endswith("/c81/2711?formato=json")

    def test_algodao_herbaceo_em_caroco_explicito(self):
        assert pam_url("cotton", [2023], ["MT", "BA"]).endswith("/c81/2689?formato=json")

    def test_ano_sem_calendario_barra_antes_da_rede(self):
        with pytest.raises(KeyError):
            pam_url("soy", [2025], ["MT"])

    def test_produto_uf_e_tipos_invalidos(self):
        with pytest.raises(ValueError, match="produto PAM"):
            pam_url("corn_second", [2023], ["MT"])
        with pytest.raises(ValueError, match="UF fora"):
            pam_url("soy", [2023], ["SP"])
        with pytest.raises(TypeError, match="sequências"):
            pam_url("soy", "2023", ["MT"])


class TestParse:
    def test_schema_e_valores_reais(self):
        df = parse_pam(FIXTURE)
        assert len(df) == 12
        assert set(df["crop"]) == {"soy", "corn_total"}
        assert set(df["uf"]) == {"MT"}
        assert set(df["value_status"]) == {"zero", "observed"}
        row = df.query("municipality_code == '5107925' and ref_year == 2023 and crop == 'soy'")
        assert row.iloc[0]["municipality_name"] == "Sorriso"
        assert row.iloc[0]["quantity_tonnes"] == 2_244_375

    def test_ref_e_avail_sao_relogios_distintos(self):
        df = parse_pam(FIXTURE)
        y2022 = df[df["ref_year"] == 2022]
        assert (y2022["ref_date"] == pd.Timestamp("2022-12-31")).all()
        assert (y2022["avail_date"] == pd.Timestamp("2023-09-14")).all()

    def test_algodao_real_mt_ba(self):
        df = parse_pam(FIXTURE_COTTON)
        assert len(df) == 8
        assert set(df["crop"]) == {"cotton"}
        assert set(df["uf"]) == {"MT", "BA"}
        sao_desiderio = df.query("municipality_code == '2928901' and ref_year == 2023")
        assert sao_desiderio.iloc[0]["quantity_tonnes"] == 543_506

    def test_zero_sidra_nao_vira_missing(self):
        df = parse_pam(FIXTURE)
        acorizal = df[df["municipality_code"] == "5100102"]
        assert (acorizal["quantity_tonnes"] == 0).all()
        assert (acorizal["value_status"] == "zero").all()

    def test_variavel_errada_falha(self):
        payload = [{}, {"D2C": "999", "MC": "1017"}]
        with pytest.raises(ValueError, match="variável/unidade"):
            parse_pam(payload)


class TestWeights:
    def test_asof_nao_enxerga_edicao_futura(self):
        df = parse_pam(FIXTURE)
        before = pam_weights_asof(df, "2024-09-11")
        after = pam_weights_asof(df, "2024-09-12")
        assert set(before["ref_year"]) == {2022}
        assert set(after["ref_year"]) == {2023}

    def test_pesos_somam_um_por_cultura_uf(self):
        weights = pam_weights_asof(parse_pam(FIXTURE), "2024-09-12")
        sums = weights.groupby(["crop", "uf"])["within_uf_weight"].sum()
        assert (sums.round(12) == 1.0).all()

    def test_pesos_algodao_somam_um_em_mt_e_ba(self):
        weights = pam_weights_asof(parse_pam(FIXTURE_COTTON), "2024-09-12")
        sums = weights.groupby(["crop", "uf"])["within_uf_weight"].sum()
        assert set(sums.index.get_level_values("uf")) == {"MT", "BA"}
        assert (sums.round(12) == 1.0).all()

    def test_sem_edicao_disponivel_falha(self):
        with pytest.raises(ValueError, match="nenhuma edição"):
            pam_weights_asof(parse_pam(FIXTURE), "2023-09-13")

    def test_missing_nao_vira_zero_e_fica_contado(self):
        df = parse_pam(FIXTURE)
        df.loc[df.index[0], ["quantity_tonnes", "value_status"]] = [float("nan"), "missing:X"]
        weights = pam_weights_asof(df, "2023-09-14")
        row = weights.loc[weights.index[0]]
        assert pd.isna(row["quantity_tonnes"])
        assert pd.isna(row["within_uf_weight"])
        group = weights[(weights["crop"] == row["crop"]) & (weights["uf"] == row["uf"])]
        assert (group["missing_municipalities"] == 1).all()


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
    def test_captura_datada_e_manifesto(self, tmp_path):
        session = _Session(FIXTURE.read_bytes())
        out = download_pam(
            "soy",
            [2022, 2023],
            ["MT"],
            dest_dir=tmp_path / "raw",
            manifest_dir=tmp_path / "man",
            session=session,
        )
        assert out.exists() and out.name.startswith("pam_1612_soy_2022-2023_mt_")
        manifest = next((tmp_path / "man").glob("pam_1612_soy_*.json")).read_text()
        assert '"release_dates"' in manifest and '"vintage_warning"' in manifest

    def test_cache_nao_rebaixa(self, tmp_path):
        session = _Session(FIXTURE.read_bytes())
        for _ in range(2):
            download_pam(
                "soy", [2023], ["MT"], dest_dir=tmp_path, manifest_dir=tmp_path, session=session
            )
        assert session.calls == 1
