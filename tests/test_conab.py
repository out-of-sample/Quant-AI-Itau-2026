"""Testes da ingestão CONAB e do calendário curado R10.

Fixtures em `tests/fixtures/conab_*.txt` são recortes crus dos arquivos reais do Portal
de Informações (latin-1, ';', CRLF), baixados em 2026-07-16: soja/MT 2023/24 e trigo/RS
2018 (grãos), café/MG 2020-2021 (2020 sem o 2º levantamento — suspenso na pandemia),
cana/SP 2022/23 e 2017/18 (com o resíduo `id_levantamento == 99`).
"""

from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.conab import DATASETS, conab_url, download_conab, parse_levantamento
from quantagro.ingest.conab_calendar import attach_avail_date, conab_calendar
from quantagro.validate.pit import AVAIL_COL, REF_COL, available_asof

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def graos():
    return parse_levantamento(FIXTURES / "conab_graos.txt", "graos")


@pytest.fixture(scope="module")
def cafe():
    return parse_levantamento(FIXTURES / "conab_cafe.txt", "cafe")


@pytest.fixture(scope="module")
def cana():
    return parse_levantamento(FIXTURES / "conab_cana.txt", "cana")


class TestParse:
    def test_colunas_canonicas_e_tipos(self, graos):
        assert list(graos.columns[:6]) == [
            "ano_agricola",
            "safra",
            "uf",
            "produto",
            "id_produto",
            "id_levantamento",
        ]
        assert graos["id_levantamento"].dtype == "int64"
        assert graos["producao_mil_t"].dtype == "float64"
        # strip aplicado: sem padding da largura fixa do arquivo
        assert (graos["ano_agricola"] == graos["ano_agricola"].str.strip()).all()
        assert "SOJA" in set(graos["produto"])

    def test_numeros_reais_de_soja_mt(self, graos):
        """A seca de 2023/24 no arquivo real: 1º lev 44.348 → 6º 37.568 (−15%)."""
        soja = graos[(graos.produto == "SOJA") & (graos.uf == "MT")].set_index("id_levantamento")
        assert soja.loc[1, "producao_mil_t"] == pytest.approx(44347.7)
        assert soja.loc[6, "producao_mil_t"] == pytest.approx(37567.8)
        assert soja.loc[12, "producao_mil_t"] == pytest.approx(40420.3)

    def test_cana_renomeia_colunas_proprias(self, cana):
        assert "safra" in cana.columns  # dsc_safra_previsao → safra
        assert "producao_atr_kg_t" in cana.columns  # typo do arquivo corrigido
        assert "producao_etanol_total_mil_l" in cana.columns

    def test_preserva_lev_99(self, cana):
        assert 99 in set(cana["id_levantamento"])

    def test_cafe_2020_nao_tem_2o_levantamento(self, cafe):
        """Buraco real da fonte (pandemia), não do parse."""
        levs_2020 = set(cafe[cafe.ano_agricola == "2020"]["id_levantamento"])
        assert 2 not in levs_2020
        assert {1, 3, 4} <= levs_2020

    def test_dataset_desconhecido_falha(self):
        with pytest.raises(ValueError, match="dataset desconhecido"):
            parse_levantamento(FIXTURES / "conab_graos.txt", "trigo")


class TestCalendario:
    """Sanidade do mapa curado — cada violação aqui indicaria erro de transcrição."""

    @pytest.mark.parametrize("dataset", sorted(DATASETS))
    def test_datas_validas_e_em_dia_util(self, dataset):
        cal = conab_calendar(dataset)
        assert cal[AVAIL_COL].notna().all()
        # a CONAB divulga em dia útil; um sábado/domingo aqui é erro de curadoria
        assert (cal[AVAIL_COL].dt.dayofweek < 5).all()

    @pytest.mark.parametrize("dataset", sorted(DATASETS))
    def test_crescente_dentro_da_safra(self, dataset):
        cal = conab_calendar(dataset).sort_values(["ano_agricola", "id_levantamento"])
        for _, grupo in cal.groupby("ano_agricola"):
            assert grupo[AVAIL_COL].is_monotonic_increasing

    def test_graos_safras_fechadas_tem_12_levantamentos(self):
        cal = conab_calendar("graos")
        fechadas = cal[cal.ano_agricola < "2025/26"]
        assert (fechadas.groupby("ano_agricola").size() == 12).all()

    def test_datas_ancora_conhecidas(self):
        """Datas verificadas em ≥2 fontes independentes durante a curadoria."""
        g = conab_calendar("graos").set_index(["ano_agricola", "id_levantamento"])[AVAIL_COL]
        assert g[("2017/18", 1)] == pd.Timestamp("2017-10-10")  # upload CONAB 09h01
        assert g[("2022/23", 12)] == pd.Timestamp("2023-09-06")  # K2 + cal2023
        assert g[("2023/24", 6)] == pd.Timestamp("2024-03-12")  # gov.br (era pós-migração)
        cf = conab_calendar("cafe").set_index(["ano_agricola", "id_levantamento"])[AVAIL_COL]
        assert cf[("2024", 2)] == pd.Timestamp("2024-05-23")  # ConabCast + Cecafé
        cn = conab_calendar("cana").set_index(["ano_agricola", "id_levantamento"])[AVAIL_COL]
        assert cn[("2022/23", 1)] == pd.Timestamp("2022-04-27")  # K2 + novacana

    def test_cafe_2020_sem_2o_no_calendario(self):
        cal = conab_calendar("cafe")
        levs = set(cal[cal.ano_agricola == "2020"]["id_levantamento"])
        assert levs == {1, 3, 4}


class TestAttachAvailDate:
    def test_carimba_soja_mt(self, graos):
        soja = graos[graos.produto == "SOJA"]
        out = attach_avail_date(soja, "graos")
        assert AVAIL_COL in out.columns and REF_COL in out.columns
        lev6 = out[out.id_levantamento == 6].iloc[0]
        assert lev6[AVAIL_COL] == pd.Timestamp("2024-03-12")

    def test_integra_com_available_asof(self, graos):
        """O contrato PIT de ponta a ponta: em 2024-03-11 o 6º lev ainda não existe."""
        soja = attach_avail_date(graos[graos.produto == "SOJA"], "graos")
        vivel = available_asof(soja, "2024-03-11")
        assert set(vivel["id_levantamento"]) == {1, 2, 3, 4, 5}
        vivel = available_asof(soja, "2024-03-12")
        assert 6 in set(vivel["id_levantamento"])

    def test_falha_alto_em_cultura_de_inverno(self, graos):
        """Trigo usa ano civil ("2018") — fora do calendário até ser verificado."""
        with pytest.raises(ValueError, match="sem data no"):
            attach_avail_date(graos, "graos")  # inclui trigo RS 2018

    def test_falha_alto_em_lev_99(self, cana):
        with pytest.raises(ValueError, match="sem data no"):
            attach_avail_date(cana, "cana")

    def test_cana_sem_lev_99_carimba(self, cana):
        ok = attach_avail_date(cana[cana.id_levantamento != 99], "cana")
        assert ok[AVAIL_COL].notna().all()


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
        content = (FIXTURES / "conab_graos.txt").read_bytes()
        sess = _FakeSession(content)
        out = download_conab(
            "graos", dest_dir=tmp_path / "raw", manifest_dir=tmp_path / "manifests", session=sess
        )
        assert out.exists() and out.read_bytes() == content
        # a fonte reescreve o arquivo no lugar ⇒ o nome carrega a data de captura
        assert out.stem.startswith("LevantamentoGraos_20")
        manifests = list((tmp_path / "manifests").glob("conab_graos_*.json"))
        assert len(manifests) == 1
        texto = manifests[0].read_text(encoding="utf-8")
        assert '"sha256"' in texto and '"downloaded_at"' in texto

    def test_cache_do_dia_nao_rebaixa(self, tmp_path):
        sess = _FakeSession(b"x")
        for _ in range(2):
            download_conab(
                "graos", dest_dir=tmp_path / "raw", manifest_dir=tmp_path / "m", session=sess
            )
        assert sess.calls == 1

    def test_url(self):
        assert conab_url("cana").endswith("/LevantamentoCana.txt")
        with pytest.raises(ValueError, match="dataset desconhecido"):
            conab_url("algodao")
