"""Testes do parser/ingestão do COTAHIST.

O parse é validado contra um **fixture real** (algumas linhas do pregão de 27/12/2024, largura
fixa de 245 bytes), que é o único jeito honesto de amarrar os offsets do layout — se um offset
escorregar, o preço/ISIN de PETR4 sai errado e o teste quebra. O download é testado com uma
sessão HTTP fake, sem rede.
"""

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.cotahist import (
    cotahist_url,
    download_cotahist,
    filter_equities_spot,
    parse_cotahist,
)

FIXTURE = Path(__file__).parent / "fixtures" / "cotahist_sample.txt"


@pytest.fixture
def parsed() -> pd.DataFrame:
    return parse_cotahist(FIXTURE)


class TestParse:
    def test_descarta_header_e_trailer(self, parsed):
        # fixture = header + 4 detalhes (PETR4, SLCE3, JBSS3, NUTR3) + trailer
        assert len(parsed) == 4
        assert set(parsed["ticker"]) == {"PETR4", "SLCE3", "JBSS3", "NUTR3"}

    def test_campos_de_petr4_batem_com_o_real(self, parsed):
        row = parsed.set_index("ticker").loc["PETR4"]
        assert row["date"] == pd.Timestamp("2024-12-27")
        assert row["close"] == pytest.approx(35.66)
        assert row["financial_volume"] == pytest.approx(864782125.0)
        assert row["isin"] == "BRPETRACNPR6"
        assert row["quote_factor"] == 1
        assert row["codbdi"] == "02"
        assert row["tpmerc"] == "010"

    def test_papel_deslistado_esta_presente(self, parsed):
        # JBSS3 saiu da bolsa em 2025; em 27/12/2024 ainda negociava. O ponto do COTAHIST é
        # justamente capturar isso (delisting-proof).
        assert parsed.set_index("ticker").loc["JBSS3", "close"] == pytest.approx(36.21)

    def test_close_positivo_e_volume_nao_negativo(self, parsed):
        assert (parsed["close"] > 0).all()
        assert (parsed["financial_volume"] >= 0).all()

    def test_aceita_bytes_alem_de_caminho(self):
        df = parse_cotahist(FIXTURE.read_bytes())
        assert len(df) == 4


class TestFiltroAcoesVista:
    def test_remove_nao_lote_padrao(self, parsed):
        # NUTR3 no fixture tem codbdi=07 (não lote-padrão) e deve sair.
        eq = filter_equities_spot(parsed)
        assert set(eq["ticker"]) == {"PETR4", "SLCE3", "JBSS3"}
        assert (eq["codbdi"] == "02").all()


class TestUrl:
    @pytest.mark.parametrize(
        "period,esperado",
        [
            ("A2024", "COTAHIST_A2024.ZIP"),
            ("M122024", "COTAHIST_M122024.ZIP"),
            ("D27122024", "COTAHIST_D27122024.ZIP"),
        ],
    )
    def test_formato(self, period, esperado):
        assert cotahist_url(period).endswith(esperado)


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


def _fake_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("COTAHIST_D01012020.TXT", FIXTURE.read_text(encoding="latin-1"))
    return buf.getvalue()


class TestDownload:
    def test_baixa_grava_arquivo_e_manifesto(self, tmp_path):
        content = _fake_zip()
        sess = _FakeSession(content)
        raw = tmp_path / "raw"
        man = tmp_path / "manifests"
        out = download_cotahist("D01012020", dest_dir=raw, manifest_dir=man, session=sess)

        assert out.exists()
        assert out.read_bytes() == content
        manifest = json.loads((man / "cotahist_D01012020.json").read_text())
        assert manifest["sha256"] == hashlib.sha256(content).hexdigest()
        assert manifest["source"] == "COTAHIST"
        assert manifest["period"] == "D01012020"
        # e o arquivo baixado é parseável de ponta a ponta
        assert len(parse_cotahist(out)) == 4

    def test_cache_nao_rebaixa(self, tmp_path):
        sess = _FakeSession(_fake_zip())
        raw = tmp_path / "raw"
        download_cotahist("D01012020", dest_dir=raw, manifest_dir=tmp_path / "m", session=sess)
        download_cotahist("D01012020", dest_dir=raw, manifest_dir=tmp_path / "m", session=sess)
        assert sess.calls == 1  # segunda chamada usou o cache
