"""Ingestão PIT das tabelas de empréstimo de ativos do Boletim Diário B3.

As exportações CSV possuem preâmbulo textual antes do cabeçalho, decimal brasileiro e, na
tabela de negócios registrados, duas linhas de cabeçalho. Taxas podem ser repetidas pela B3
em modalidades sem negócio no dia; por isso presença de taxa nunca equivale a evidência de
negociação — ``contract_count`` e ``asset_quantity`` precisam ser positivos.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

_REGISTERED_FIELDS = (
    "ref_date",
    "ticker",
    "isin",
    "issuer",
    "market",
    "contract_count",
    "asset_quantity",
    "notional_brl",
    "donor_min_rate",
    "donor_weighted_rate",
    "donor_max_rate",
    "taker_min_rate",
    "taker_weighted_rate",
    "taker_max_rate",
)
_OPEN_FIELDS = (
    "ref_date",
    "ticker",
    "isin",
    "issuer",
    "loan_type",
    "market",
    "open_quantity",
    "average_price",
    "published_balance_brl",
)
_EXPORT_URL = "https://arquivos.b3.com.br/bdi/table/export/csv?lang=pt-BR"
_TABLES = frozenset({"BTBLoanBalance", "BTBLendingOpenPosition"})


def _read_text(source: str | Path | bytes | io.TextIOBase) -> str:
    if isinstance(source, bytes):
        return source.decode("utf-8-sig")
    if hasattr(source, "read"):
        value = source.read()
        return value.decode("utf-8-sig") if isinstance(value, bytes) else value.lstrip("\ufeff")
    path = Path(source)
    return path.read_text(encoding="utf-8-sig")


def _rows_after_header(text: str, header_prefix: tuple[str, ...]) -> list[list[str]]:
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    start = next(
        (
            i
            for i, row in enumerate(rows)
            if tuple(cell.strip() for cell in row[:2]) == header_prefix
        ),
        None,
    )
    if start is None:
        raise ValueError("cabeçalho BDI não encontrado")
    return [row for row in rows[start + 1 :] if row and any(cell.strip() for cell in row)]


def _br_number(value: str) -> float:
    clean = value.strip()
    if not clean or clean == "-":
        return np.nan
    return float(clean.replace(".", "").replace(",", ".").replace("%", ""))


def _integer(value: str) -> int:
    number = _br_number(value)
    return 0 if np.isnan(number) else int(number)


def _rate(value: str) -> float:
    number = _br_number(value)
    return number / 100.0 if np.isfinite(number) else np.nan


def parse_registered_loans(
    source: str | Path | bytes | io.TextIOBase,
) -> pd.DataFrame:
    """Normaliza ``BTBLoanBalance`` sem inferir negócio a partir de taxa repetida."""
    raw = _rows_after_header(_read_text(source), ("Data", "Código IF"))
    if any(len(row) != len(_REGISTERED_FIELDS) for row in raw):
        raise ValueError("linha BTBLoanBalance com número inesperado de campos")
    frame = pd.DataFrame(raw, columns=_REGISTERED_FIELDS)
    frame["ref_date"] = pd.to_datetime(frame["ref_date"], format="%d/%m/%Y")
    for column in ("contract_count", "asset_quantity"):
        frame[column] = frame[column].map(_integer).astype("int64")
    frame["notional_brl"] = frame["notional_brl"].map(_br_number).astype(float)
    for column in _REGISTERED_FIELDS[8:]:
        frame[column] = frame[column].map(_rate).astype(float)
    frame["source"] = "B3_BDI_BTBLoanBalance"
    return frame


def parse_open_positions(
    source: str | Path | bytes | io.TextIOBase,
) -> pd.DataFrame:
    """Normaliza ``BTBLendingOpenPosition`` e identifica linhas agregadas ``Total``."""
    raw = _rows_after_header(_read_text(source), ("Data", "Código IF"))
    if any(len(row) != len(_OPEN_FIELDS) for row in raw):
        raise ValueError("linha BTBLendingOpenPosition com número inesperado de campos")
    frame = pd.DataFrame(raw, columns=_OPEN_FIELDS)
    frame["ref_date"] = pd.to_datetime(frame["ref_date"], format="%d/%m/%Y")
    frame["open_quantity"] = frame["open_quantity"].map(_integer).astype("int64")
    for column in ("average_price", "published_balance_brl"):
        frame[column] = frame[column].map(_br_number).astype(float)
    frame["is_total"] = frame["market"].str.strip().eq("Total")
    frame["source"] = "B3_BDI_BTBLendingOpenPosition"
    return frame


def stamp_borrow_availability(frame: pd.DataFrame, sessions: pd.DatetimeIndex) -> pd.DataFrame:
    """Carimba cada boletim como disponível no primeiro pregão após sua data de referência."""
    if "ref_date" not in frame:
        raise ValueError("tabela de aluguel sem ref_date")
    calendar = pd.DatetimeIndex(sessions).normalize().sort_values().unique()
    if len(calendar) == 0:
        raise ValueError("calendário de pregões vazio")
    ref = pd.DatetimeIndex(pd.to_datetime(frame["ref_date"])).normalize()
    positions = calendar.searchsorted(ref, side="right")
    if (positions >= len(calendar)).any():
        missing = sorted(set(ref[positions >= len(calendar)].strftime("%Y-%m-%d")))
        raise ValueError(f"sem pregão posterior para carimbar aluguel: {missing[:3]}")
    out = frame.copy()
    out["ref_date"] = ref
    out["avail_date"] = calendar[positions]
    return out


def verify_bdi_capture(
    data_path: str | Path, manifest_path: str | Path, expected_table: str
) -> pd.Timestamp:
    """Atesta que arquivo, hash, schema, contagem e data coincidem com o manifesto."""
    if expected_table not in _TABLES:
        raise ValueError(f"tabela BDI desconhecida: {expected_table!r}")
    raw_path = Path(data_path)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    content = raw_path.read_bytes()
    if manifest.get("source") != "B3_BDI" or manifest.get("table") != expected_table:
        raise ValueError("manifesto BDI não corresponde à tabela esperada")
    if manifest.get("bytes") != len(content):
        raise ValueError("tamanho do arquivo BDI diverge do manifesto")
    if manifest.get("sha256") != hashlib.sha256(content).hexdigest():
        raise ValueError("hash do arquivo BDI diverge do manifesto")
    parser = parse_registered_loans if expected_table == "BTBLoanBalance" else parse_open_positions
    frame = parser(content)
    if frame.empty or manifest.get("rows") != len(frame):
        raise ValueError("contagem de linhas BDI diverge do manifesto")
    ref_date = pd.Timestamp(str(manifest.get("ref_date"))).normalize()
    if not frame["ref_date"].eq(ref_date).all():
        raise ValueError("data interna do BDI diverge do manifesto")
    return ref_date


def download_bdi_table(
    table: str,
    ref_date: str | pd.Timestamp,
    dest_dir: str | Path = "data/raw/b3_bdi",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 120,
) -> Path:
    """Baixa uma exportação diária do BDI e grava hash/vintage; cache evita mutabilidade."""
    if table not in _TABLES:
        raise ValueError(f"tabela BDI desconhecida: {table!r}")
    date = pd.Timestamp(ref_date).normalize()
    if date.tz is not None:
        raise ValueError("ref_date BDI deve ser data sem fuso")
    destination = Path(dest_dir)
    destination.mkdir(parents=True, exist_ok=True)
    out = destination / f"{table}_{date:%Y%m%d}.csv"
    manifests = Path(manifest_dir)
    manifest_path = manifests / f"b3_bdi_{table}_{date:%Y%m%d}.json"
    if out.exists():
        if not manifest_path.exists():
            raise ValueError("cache BDI existe sem manifesto de completude")
        verify_bdi_capture(out, manifest_path, table)
        return out
    if session is None:
        import requests

        session = requests
    payload = {
        "Name": table,
        "Date": date.date().isoformat(),
        "FinalDate": date.date().isoformat(),
        "ClientId": "",
        "Filters": {},
    }
    response = session.post(
        _EXPORT_URL,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    content = response.content
    if not content.startswith(b"\xef\xbb\xbf") or b"C\xc3\xb3digo IF" not in content:
        raise ValueError("resposta BDI não parece um CSV oficial válido")
    out.write_bytes(content)

    manifests.mkdir(parents=True, exist_ok=True)
    parser = parse_registered_loans if table == "BTBLoanBalance" else parse_open_positions
    manifest = {
        "source": "B3_BDI",
        "table": table,
        "ref_date": date.date().isoformat(),
        "url": _EXPORT_URL,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "rows": len(parser(content)),
        "downloaded_at": datetime.now(UTC).isoformat(),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return out
