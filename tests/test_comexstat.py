"""Testes da ingestão ComexStat/Secex-MDIC (docs/02_DADOS.md §3).

Fixtures em `tests/fixtures/comexstat_*.json` são **respostas reais** do `POST /general`
(2026-07-16): soja em grão (`12019000`) export 2023 jan-mar; café (`09011110`) export 2023
jan-fev; e a resposta-armadilha do NCM passado como **inteiro** (`9011110`) — lista vazia com
`success: true`, o erro silencioso que o guardrail `_validate_ncms` existe para impedir.
"""

from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.comexstat import (
    THESIS_NCMS,
    _validate_ncms,
    build_query,
    download_comex,
    parse_comex,
)
from quantagro.validate.pit import AVAIL_COL, available_asof, stamp_avail_date

FIXTURES = Path(__file__).parent / "fixtures"
SOJA = FIXTURES / "comexstat_soja_2023.json"
CAFE = FIXTURES / "comexstat_cafe_2023.json"
VAZIO = FIXTURES / "comexstat_vazio.json"


class TestValidateNcms:
    def test_int_barrado(self):
        # o gotcha: int perde o zero à esquerda -> vazio com success:true. Barrar antes da rede.
        with pytest.raises(TypeError, match="int perde o zero"):
            _validate_ncms([9011110])

    def test_comprimento_errado_barrado(self):
        with pytest.raises(ValueError, match="8 dígitos"):
            _validate_ncms(["9011110"])  # 7 dígitos (zero à esquerda perdido)
        with pytest.raises(ValueError, match="8 dígitos"):
            _validate_ncms(["123456789"])  # 9 dígitos

    def test_string_unica_barrada(self):
        with pytest.raises(TypeError, match="sequência"):
            _validate_ncms("12019000")

    def test_vazio_barrado(self):
        with pytest.raises(ValueError, match="nenhum NCM"):
            _validate_ncms([])

    def test_validos_passam(self):
        assert _validate_ncms(["12019000", "09011110"]) == ["12019000", "09011110"]

    def test_todos_os_ncms_da_tese_sao_validos(self):
        # meta-teste: a própria constante THESIS_NCMS não pode cair no gotcha
        for produto, ncms in THESIS_NCMS.items():
            assert _validate_ncms(list(ncms)), produto


class TestBuildQuery:
    def test_estrutura(self):
        q = build_query(["12019000"], "2023-01", "2023-03")
        assert q["flow"] == "export" and q["monthDetail"] is True
        assert q["period"] == {"from": "2023-01", "to": "2023-03"}
        assert q["filters"] == [{"filter": "ncm", "values": ["12019000"]}]
        assert q["metrics"] == ["metricFOB", "metricKG"]

    def test_valida_ncm_no_build(self):
        with pytest.raises(TypeError):
            build_query([9011110], "2023-01", "2023-03")

    def test_flow_invalido(self):
        with pytest.raises(ValueError, match="export.*import"):
            build_query(["12019000"], "2023-01", "2023-03", flow="both")


class TestParse:
    def test_painel_arrumado_e_numerico(self):
        df = parse_comex(SOJA)
        assert list(df.columns) == ["ref_date", "co_ncm", "metric_fob_usd", "metric_kg"]
        assert df["metric_fob_usd"].dtype == "int64" and df["metric_kg"].dtype == "int64"
        assert df["ref_date"].dtype.kind == "M"
        assert (df["co_ncm"] == "12019000").all()
        assert len(df) == 3

    def test_ref_date_e_fim_do_mes(self):
        df = parse_comex(SOJA)
        assert set(df["ref_date"]) == {
            pd.Timestamp("2023-01-31"),
            pd.Timestamp("2023-02-28"),
            pd.Timestamp("2023-03-31"),
        }

    def test_ordenado(self):
        df = parse_comex(SOJA)
        assert df["ref_date"].is_monotonic_increasing

    def test_resposta_vazia_do_gotcha(self):
        # a resposta do NCM-int é vazia com success:true; o parse devolve painel vazio tipado
        df = parse_comex(VAZIO)
        assert df.empty
        assert list(df.columns) == ["ref_date", "co_ncm", "metric_fob_usd", "metric_kg"]

    def test_aceita_dict_bytes_e_path(self):
        p = parse_comex(CAFE)
        b = parse_comex(CAFE.read_bytes())
        assert p.shape == b.shape and len(p) == 2
        assert (p["co_ncm"] == "09011110").all()  # zero à esquerda preservado


class TestPointInTime:
    def test_carimbo_mensal_lag_7d(self):
        df = parse_comex(SOJA)
        st = stamp_avail_date(df, lag_days=7)
        # jan/2023 (ref 31/01) fica visível a partir de 07/02 — início do mês seguinte
        jan = st[st["ref_date"] == pd.Timestamp("2023-01-31")]
        assert (jan[AVAIL_COL] == pd.Timestamp("2023-02-07")).all()
        assert available_asof(st, "2023-02-06").empty
        assert len(available_asof(st, "2023-02-07")) == 1


class _FakeResp:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        pass


class _FakeSession:
    """Sessão fake: `post` devolve a resposta de dados; `get` devolve o dates/updated."""

    def __init__(self, post_content: bytes):
        self._post = post_content
        self._get = (
            b'{"data":{"updated":"2023-04-05","year":"2023","monthNumber":"03"},"success":true}'
        )
        self.posts = 0
        self.gets = 0

    def post(self, url, json=None, timeout=None):
        self.posts += 1
        return _FakeResp(self._post)

    def get(self, url, timeout=None):
        self.gets += 1
        return _FakeResp(self._get)


class TestDownload:
    def test_baixa_grava_arquivo_e_manifesto_de_vintage(self, tmp_path):
        content = SOJA.read_bytes()
        sess = _FakeSession(content)
        out = download_comex(
            ["12019000"],
            "2023-01",
            "2023-03",
            dest_dir=tmp_path / "raw",
            manifest_dir=tmp_path / "man",
            session=sess,
        )
        assert out.exists() and out.read_bytes() == content
        assert out.name.startswith("comexstat_export_2023-01_2023-03_")
        man = list((tmp_path / "man").glob("comexstat_export_*.json"))
        assert len(man) == 1
        meta = pd.read_json(man[0], typ="series")
        assert meta["source"] == "ComexStat-MDIC"
        assert meta["vintage_updated"] == "2023-04-05"  # prova de vintage do dates/updated
        assert meta["vintage_latest_month"] == "2023-03"

    def test_valida_ncm_antes_da_rede(self, tmp_path):
        sess = _FakeSession(b"{}")
        with pytest.raises(TypeError):
            download_comex(
                [9011110],
                "2023-01",
                "2023-03",
                dest_dir=tmp_path,
                manifest_dir=tmp_path,
                session=sess,
            )
        assert sess.posts == 0  # barrou antes de tocar a rede

    def test_success_false_levanta(self, tmp_path):
        sess = _FakeSession(b'{"data":{"list":[]},"success":false,"message":"erro X"}')
        with pytest.raises(ValueError, match="success=False"):
            download_comex(
                ["12019000"],
                "2023-01",
                "2023-03",
                dest_dir=tmp_path,
                manifest_dir=tmp_path,
                session=sess,
            )

    def test_cache_nao_rebaixa(self, tmp_path):
        sess = _FakeSession(SOJA.read_bytes())
        for _ in range(2):
            download_comex(
                ["12019000"],
                "2023-01",
                "2023-03",
                dest_dir=tmp_path,
                manifest_dir=tmp_path,
                session=sess,
            )
        assert sess.posts == 1
