"""Estado PIT de aluguel: completude, taxa recente e estoque marcado."""

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from quantagro.ingest.borrow_b3 import (
    parse_open_positions,
    parse_registered_loans,
    stamp_borrow_availability,
)
from quantagro.validate.borrow import BorrowFileCoverage, build_borrow_state

FIXTURES = Path(__file__).parent / "fixtures"
TICKERS = ("AGRO3", "SLCE3", "SMTO3")


def _inputs():
    sessions = pd.bdate_range("2026-07-13", "2026-07-20")
    registered_one = parse_registered_loans(FIXTURES / "b3_borrow_registered_20260717.csv")
    open_one = parse_open_positions(FIXTURES / "b3_borrow_open_20260717.csv")
    registered = pd.concat(
        [registered_one.assign(ref_date=date) for date in sessions[:-1]], ignore_index=True
    )
    opened = pd.concat(
        [open_one.assign(ref_date=date) for date in sessions[:-1]], ignore_index=True
    )
    registered = stamp_borrow_availability(registered, sessions)
    opened = stamp_borrow_availability(opened, sessions)
    close = pd.DataFrame(20.0, index=sessions, columns=TICKERS)
    coverage = BorrowFileCoverage(
        frozenset(sessions[:-1]), frozenset(sessions[:-1]), _attested=True
    )
    return sessions, registered, opened, close, coverage


def test_estado_usa_cinco_arquivos_anteriores_e_close_da_decisao():
    sessions, registered, opened, close, coverage = _inputs()
    state = build_borrow_state(registered, opened, close, sessions[-1:], TICKERS, coverage)
    decision = sessions[-1]
    assert state.complete.loc[decision].all()
    assert state.recent_trade.loc[decision].all()
    assert state.donor_rate.loc[decision, "SMTO3"] == pytest.approx(0.0465)
    assert state.stock_brl.loc[decision, "AGRO3"] == pytest.approx(3_970_314 * 20.0)


def test_taxa_repetida_sem_contrato_nao_cria_evidencia():
    sessions, registered, opened, close, coverage = _inputs()
    mask = registered["ticker"].eq("SLCE3")
    registered.loc[mask, ["contract_count", "asset_quantity"]] = 0
    state = build_borrow_state(registered, opened, close, sessions[-1:], TICKERS, coverage)
    assert not state.recent_trade.loc[sessions[-1], "SLCE3"]
    assert pd.isna(state.donor_rate.loc[sessions[-1], "SLCE3"])
    assert state.reason.loc[sessions[-1], "SLCE3"] == "no_recent_trade"


def test_arquivo_ausente_nao_vira_ticker_sem_negocio():
    sessions, registered, opened, close, coverage = _inputs()
    missing_date = sessions[-3]
    coverage = BorrowFileCoverage(
        coverage.registered_ref_dates - {missing_date},
        coverage.open_position_ref_dates,
        _attested=True,
    )
    state = build_borrow_state(registered, opened, close, sessions[-1:], TICKERS, coverage)
    assert not state.complete.loc[sessions[-1]].any()
    assert state.reason.loc[sessions[-1]].eq("missing_bdi_files").all()


def test_ticker_ausente_em_arquivo_completo_vira_zero():
    sessions, registered, opened, close, coverage = _inputs()
    opened = opened[opened["ticker"] != "AGRO3"]
    state = build_borrow_state(registered, opened, close, sessions[-1:], TICKERS, coverage)
    assert state.complete.loc[sessions[-1], "AGRO3"]
    assert state.stock_brl.loc[sessions[-1], "AGRO3"] == 0.0
    assert state.reason.loc[sessions[-1], "AGRO3"] == "zero_open_position"


def test_total_que_nao_fecha_com_modalidades_falha_alto():
    sessions, registered, opened, close, coverage = _inputs()
    mask = opened["ticker"].eq("AGRO3") & opened["is_total"]
    opened.loc[mask, "open_quantity"] += 1_000
    with pytest.raises(ValueError, match="não fecham"):
        build_borrow_state(registered, opened, close, sessions[-1:], TICKERS, coverage)


def test_taxa_agrega_modalidades_do_ultimo_dia_por_quantidade():
    sessions, registered, opened, close, coverage = _inputs()
    decision = sessions[-1]
    last_ref = sessions[-2]
    extra = (
        registered[registered["ticker"].eq("AGRO3") & registered["ref_date"].eq(last_ref)]
        .iloc[[0]]
        .copy()
    )
    extra["asset_quantity"] = 3 * extra["asset_quantity"]
    extra["donor_weighted_rate"] = 0.04
    registered = pd.concat([registered, extra], ignore_index=True)
    state = build_borrow_state(
        registered, opened, close, pd.DatetimeIndex([decision]), TICKERS, coverage
    )
    assert state.donor_rate.loc[decision, "AGRO3"] == pytest.approx((0.0008 + 3 * 0.04) / 4)


def _capture_pair(tmp_path: Path, fixture: str, table: str) -> tuple[Path, Path]:
    data = tmp_path / fixture
    data.write_bytes((FIXTURES / fixture).read_bytes())
    manifest = tmp_path / f"{table}.json"
    content = data.read_bytes()
    frame = (
        parse_registered_loans(data) if table == "BTBLoanBalance" else parse_open_positions(data)
    )
    manifest.write_text(
        json.dumps(
            {
                "source": "B3_BDI",
                "table": table,
                "ref_date": "2026-07-17",
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
                "rows": len(frame),
            }
        ),
        encoding="utf-8",
    )
    return data, manifest


def test_cobertura_nasce_de_capturas_atestadas(tmp_path: Path):
    registered = _capture_pair(tmp_path, "b3_borrow_registered_20260717.csv", "BTBLoanBalance")
    opened = _capture_pair(tmp_path, "b3_borrow_open_20260717.csv", "BTBLendingOpenPosition")
    coverage = BorrowFileCoverage.from_captures([registered], [opened])
    expected = frozenset({pd.Timestamp("2026-07-17")})
    assert coverage.registered_ref_dates == expected
    assert coverage.open_position_ref_dates == expected


def test_cobertura_rejeita_captura_adulterada(tmp_path: Path):
    registered = _capture_pair(tmp_path, "b3_borrow_registered_20260717.csv", "BTBLoanBalance")
    registered[0].write_bytes(registered[0].read_bytes()[:-10])
    with pytest.raises(ValueError, match="(tamanho|hash)"):
        BorrowFileCoverage.from_captures([registered], [])


def test_estado_rejeita_cobertura_declarada_sem_atestacao():
    sessions, registered, opened, close, _ = _inputs()
    unverified = BorrowFileCoverage(frozenset(sessions[:-1]), frozenset(sessions[:-1]))
    with pytest.raises(ValueError, match="não foi atestada"):
        build_borrow_state(registered, opened, close, sessions[-1:], TICKERS, unverified)
