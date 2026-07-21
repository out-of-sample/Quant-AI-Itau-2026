"""Parser e carimbo PIT das tabelas reais de aluguel do BDI B3."""

from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.borrow_b3 import (
    download_bdi_table,
    parse_open_positions,
    parse_registered_loans,
    stamp_borrow_availability,
    verify_bdi_capture,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_registrados_preserva_taxa_repetida_sem_inventar_negocio():
    frame = parse_registered_loans(FIXTURES / "b3_borrow_registered_20260717.csv")
    stale = frame[(frame["ticker"] == "SLCE3") & (frame["market"] == "Neg. Eletrônica D+0")]
    assert len(frame) == 5
    assert stale.iloc[0]["contract_count"] == 0
    assert stale.iloc[0]["asset_quantity"] == 0
    assert stale.iloc[0]["donor_weighted_rate"] == pytest.approx(0.0019)


def test_registrados_parseia_decimal_percentual_e_bom():
    frame = parse_registered_loans(FIXTURES / "b3_borrow_registered_20260717.csv")
    smto = frame[(frame["ticker"] == "SMTO3") & (frame["market"] == "Registro")].iloc[0]
    assert smto["contract_count"] == 491
    assert smto["asset_quantity"] == 1_200_236
    assert smto["notional_brl"] == pytest.approx(18_819_700.48)
    assert smto["donor_weighted_rate"] == pytest.approx(0.0465)


def test_posicao_aberta_separa_total_das_modalidades():
    frame = parse_open_positions(FIXTURES / "b3_borrow_open_20260717.csv")
    agro = frame[frame["ticker"] == "AGRO3"]
    total = agro[agro["is_total"]].iloc[0]
    parts = agro[~agro["is_total"]]
    assert total["open_quantity"] == 3_970_314
    assert parts["open_quantity"].sum() == total["open_quantity"]
    assert pd.isna(total["average_price"])


def test_carimbo_usa_primeiro_pregao_estritamente_posterior():
    frame = parse_registered_loans(FIXTURES / "b3_borrow_registered_20260717.csv")
    sessions = pd.to_datetime(["2026-07-17", "2026-07-20", "2026-07-21"])
    stamped = stamp_borrow_availability(frame, sessions)
    assert stamped["ref_date"].eq(pd.Timestamp("2026-07-17")).all()
    assert stamped["avail_date"].eq(pd.Timestamp("2026-07-20")).all()


def test_carimbo_sem_pregao_posterior_falha_alto():
    frame = parse_open_positions(FIXTURES / "b3_borrow_open_20260717.csv")
    with pytest.raises(ValueError, match="sem pregão posterior"):
        stamp_borrow_availability(frame, pd.to_datetime(["2026-07-17"]))


def test_cabecalho_invalido_falha_alto(tmp_path: Path):
    path = tmp_path / "invalid.csv"
    path.write_text("nada;util\n", encoding="utf-8")
    with pytest.raises(ValueError, match="cabeçalho"):
        parse_registered_loans(path)


class _Response:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        return None


class _Session:
    def __init__(self, content: bytes):
        self.content = content
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _Response(self.content)


def test_download_bdi_grava_csv_manifesto_e_usa_cache(tmp_path: Path):
    content = (FIXTURES / "b3_borrow_registered_20260717.csv").read_bytes()
    session = _Session(content)
    raw = tmp_path / "raw"
    manifests = tmp_path / "manifests"
    first = download_bdi_table("BTBLoanBalance", "2026-07-17", raw, manifests, session=session)
    second = download_bdi_table("BTBLoanBalance", "2026-07-17", raw, manifests, session=session)
    assert first == second
    assert len(session.calls) == 1
    assert session.calls[0][1]["json"]["Date"] == "2026-07-17"
    assert session.calls[0][1]["json"]["FinalDate"] == "2026-07-17"
    manifest = manifests / "b3_bdi_BTBLoanBalance_20260717.json"
    assert manifest.exists()
    assert verify_bdi_capture(first, manifest, "BTBLoanBalance") == pd.Timestamp("2026-07-17")
    assert parse_registered_loans(first).shape[0] == 5


def test_download_bdi_rejeita_tabela_desconhecida(tmp_path: Path):
    with pytest.raises(ValueError, match="desconhecida"):
        download_bdi_table("qualquer", "2026-07-17", tmp_path)


def test_captura_truncada_ou_adulterada_falha_com_manifesto(tmp_path: Path):
    content = (FIXTURES / "b3_borrow_registered_20260717.csv").read_bytes()
    session = _Session(content)
    raw = tmp_path / "raw"
    manifests = tmp_path / "manifests"
    path = download_bdi_table("BTBLoanBalance", "2026-07-17", raw, manifests, session=session)
    path.write_bytes(content[:-100])
    with pytest.raises(ValueError, match="(tamanho|hash)"):
        verify_bdi_capture(
            path, manifests / "b3_bdi_BTBLoanBalance_20260717.json", "BTBLoanBalance"
        )
