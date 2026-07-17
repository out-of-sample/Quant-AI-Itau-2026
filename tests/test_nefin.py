"""Testes da ingestão NEFIN com fixtures dos commits oficiais de 01/06 e 19/06/2026."""

import json
from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.nefin import (
    FACTOR_COLUMNS,
    NEFIN_COMMITS_URL,
    NEFIN_FILE_PATH,
    compare_nefin_vintages,
    download_nefin,
    latest_nefin_commit,
    nefin_raw_url,
    parse_nefin,
    stamp_nefin_avail_date,
)
from quantagro.validate.pit import available_asof

FIXTURES = Path(__file__).parent / "fixtures"
CURRENT = FIXTURES / "nefin_factors_current.csv"
PREVIOUS = FIXTURES / "nefin_factors_previous.csv"
COMMIT = {
    "sha": "e12ab2b324cbd0d26e300477949349711598bccc",
    "commit": {
        "committer": {"date": "2026-06-19T20:31:52Z"},
        "message": "Weekly partial update",
    },
}


class TestParse:
    def test_fixture_real_schema_e_valores(self):
        df = parse_nefin(CURRENT)
        assert list(df.columns) == ["ref_date", *FACTOR_COLUMNS]
        assert len(df) == 6
        assert df["ref_date"].dtype.kind == "M"
        row = df[df["ref_date"] == pd.Timestamp("2001-11-05")].iloc[0]
        assert row["rm_minus_rf"] == pytest.approx(0.041041762715293)
        assert row["hml"] == pytest.approx(-0.0129404098113986)
        assert row["risk_free"] == pytest.approx(0.000704187361509456)

    def test_retorno_esta_em_decimal_nao_percentual(self):
        df = parse_nefin(CURRENT)
        assert df[list(FACTOR_COLUMNS)].abs().to_numpy().max() < 1
        assert df.iloc[0]["rm_minus_rf"] == pytest.approx(0.0066006, rel=1e-4)

    def test_aceita_path_bytes_e_texto(self):
        a = parse_nefin(CURRENT)
        b = parse_nefin(CURRENT.read_bytes())
        c = parse_nefin(CURRENT.read_text(encoding="utf-8"))
        pd.testing.assert_frame_equal(a, b)
        pd.testing.assert_frame_equal(a, c)

    @pytest.mark.parametrize(
        ("content", "message"),
        [
            ("Date,SMB\n2020-01-01,0.1\n", "schema NEFIN inesperado"),
            (
                "Date,Rm_minus_Rf,SMB,HML,WML,IML,Risk_Free\n"
                "2020-01-01,0.1,0.1,0.1,0.1,0.1,0.1\n"
                "2020-01-01,0.2,0.2,0.2,0.2,0.2,0.2\n",
                "ref_date duplicada",
            ),
            (
                "Date,Rm_minus_Rf,SMB,HML,WML,IML,Risk_Free\n2020-01-01,0.1,,0.1,0.1,0.1,0.1\n",
                "fator ausente",
            ),
        ],
    )
    def test_falha_alto_em_dado_invalido(self, content, message):
        with pytest.raises(ValueError, match=message):
            parse_nefin(content)


class TestVintage:
    def test_revisao_material_hml_e_replicavel_na_fixture(self):
        report = compare_nefin_vintages(parse_nefin(PREVIOUS), parse_nefin(CURRENT))
        hml = report.set_index("factor").loc["hml"]
        assert hml["overlap_rows"] == 5
        assert hml["changed_rows"] == 4
        assert hml["changed_gt_1bp"] == 4
        assert hml["max_abs_revision"] == pytest.approx(0.0275936904909542)
        rf = report.set_index("factor").loc["risk_free"]
        assert rf["changed_rows"] == 0

    def test_tolerancia_negativa_e_erro(self):
        with pytest.raises(ValueError, match="atol não pode ser negativo"):
            compare_nefin_vintages(parse_nefin(PREVIOUS), parse_nefin(CURRENT), atol=-1)


class TestPointInTime:
    def test_snapshot_inteiro_disponivel_na_data_do_commit(self):
        stamped = stamp_nefin_avail_date(parse_nefin(CURRENT), "2026-06-19T20:31:52Z")
        assert (stamped["avail_date"] == pd.Timestamp("2026-06-19")).all()
        assert available_asof(stamped, "2026-06-18").empty
        assert len(available_asof(stamped, "2026-06-19")) == len(stamped)

    def test_publicacao_anterior_ao_dado_falha_alto(self):
        with pytest.raises(ValueError, match="anterior à última ref_date"):
            stamp_nefin_avail_date(parse_nefin(CURRENT), "2026-05-01")


class _FakeResponse:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        pass


class _FakeSession:
    def __init__(self, csv_content: bytes, commits=None):
        self.csv_content = csv_content
        self.commits = commits if commits is not None else [COMMIT]
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        if url == NEFIN_COMMITS_URL:
            return _FakeResponse(json.dumps(self.commits).encode())
        return _FakeResponse(self.csv_content)


class TestSourceAndDownload:
    def test_commit_query_e_url_presa_ao_sha(self):
        session = _FakeSession(CURRENT.read_bytes())
        commit = latest_nefin_commit(session=session)
        assert commit["sha"] == COMMIT["sha"]
        assert commit["committed_at"] == "2026-06-19T20:31:52Z"
        assert session.calls[0]["params"] == {"path": NEFIN_FILE_PATH, "per_page": 1}
        assert COMMIT["sha"] in nefin_raw_url(commit["sha"])

    @pytest.mark.parametrize("sha", ["", "xyz1234", "abc"])
    def test_sha_invalido_falha_alto(self, sha):
        with pytest.raises(ValueError, match="SHA de commit inválido"):
            nefin_raw_url(sha)

    def test_commit_vazio_ou_malformado_falha_alto(self):
        with pytest.raises(ValueError, match="não devolveu commit"):
            latest_nefin_commit(session=_FakeSession(CURRENT.read_bytes(), commits=[]))
        with pytest.raises(ValueError, match="schema inesperado"):
            latest_nefin_commit(session=_FakeSession(CURRENT.read_bytes(), commits=[{}]))

    def test_download_pinado_manifesto_e_cache(self, tmp_path):
        session = _FakeSession(CURRENT.read_bytes())
        first = download_nefin(
            dest_dir=tmp_path / "raw",
            manifest_dir=tmp_path / "man",
            session=session,
        )
        second = download_nefin(
            dest_dir=tmp_path / "raw",
            manifest_dir=tmp_path / "man",
            session=session,
        )
        assert first == second and first.read_bytes() == CURRENT.read_bytes()
        # Consulta o commit nas duas chamadas, mas baixa o CSV só na primeira.
        assert len(session.calls) == 3
        assert COMMIT["sha"] in session.calls[1]["url"]
        manifests = list((tmp_path / "man").glob("nefin_factors_*.json"))
        assert len(manifests) == 1
        meta = json.loads(manifests[0].read_text(encoding="utf-8"))
        assert meta["commit_sha"] == COMMIT["sha"]
        assert meta["commit_date"] == "2026-06-19T20:31:52Z"
        assert meta["rows"] == 6
        assert meta["last_ref_date"] == "2026-06-02"
        assert len(meta["sha256"]) == 64

    def test_resposta_csv_invalida_nao_e_persistida(self, tmp_path):
        session = _FakeSession(b"not,a,nefin,file\n")
        with pytest.raises(ValueError, match="schema NEFIN inesperado"):
            download_nefin(tmp_path / "raw", tmp_path / "man", session=session)
        assert not list((tmp_path / "raw").glob("*.csv"))
