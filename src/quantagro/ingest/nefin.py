"""Ingestão dos fatores de risco brasileiros do NEFIN/FEA-USP.

Os fatores ``Rm-Rf``, ``SMB``, ``HML``, ``WML`` e ``IML`` entram somente na regressão de
*spanning* H4, junto da taxa livre de risco. São controles de atribuição **ex post**: nunca
geram posição nem calibram o sinal.

O site é servido pelo repositório oficial ``nefin/nefin.github.io``. O CSV tem observações
diárias, mas é publicado em lote e sobrescrito. A frequência da linha não é a frequência de
disponibilização. Verificação dos dois commits disponíveis após a migração do site mostrou
revisão material: entre 01/06 e 19/06/2026, 4.484 de 6.218 valores HML sobrepostos mudaram
acima de 1e-10 e 3.889 mudaram mais de 1 bp; a maior revisão foi 2,76 p.p.

Consequência point-in-time: o downloader consulta o commit que publicou o arquivo e baixa a
URL *raw* presa ao SHA, nunca a branch mutável. Todas as linhas do snapshot recebem o mesmo
``avail_date`` — a data do commit. Isso é deliberadamente conservador: não inventa um
calendário histórico linha a linha que a fonte não fornece. Como H4 é diagnóstico ex post,
essa escolha não restringe o conjunto de informação usado para negociar.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

NEFIN_REPOSITORY = "nefin/nefin.github.io"
NEFIN_FILE_PATH = "static/resources/risk_factors/nefin_factors.csv"
NEFIN_PUBLIC_URL = "https://nefin.com.br/resources/risk_factors/nefin_factors.csv"
NEFIN_PAGE_URL = "https://nefin.com.br/data/risk-factors/"
NEFIN_COMMITS_URL = f"https://api.github.com/repos/{NEFIN_REPOSITORY}/commits"

_EXPECTED_SOURCE_COLUMNS = (
    "Date",
    "Rm_minus_Rf",
    "SMB",
    "HML",
    "WML",
    "IML",
    "Risk_Free",
)
FACTOR_COLUMNS = ("rm_minus_rf", "smb", "hml", "wml", "iml", "risk_free")
_RENAME = {
    "Date": "ref_date",
    "Rm_minus_Rf": "rm_minus_rf",
    "SMB": "smb",
    "HML": "hml",
    "WML": "wml",
    "IML": "iml",
    "Risk_Free": "risk_free",
}
_HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "quantagro/0.0.0"}


def _load_text(source: str | Path | bytes) -> str:
    if isinstance(source, bytes):
        return source.decode("utf-8")
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    if "\n" not in source and Path(source).exists():
        return Path(source).read_text(encoding="utf-8")
    return source


def parse_nefin(source: str | Path | bytes) -> pd.DataFrame:
    """Parseia o CSV oficial em painel diário canônico de retornos decimais.

    O índice serializado pelo R é descartado. Schema, datas, nulos, infinitos e duplicatas
    falham alto: uma mudança silenciosa da fonte não pode alterar a regressão H4.
    """
    raw = pd.read_csv(StringIO(_load_text(source)))
    if raw.columns[0].startswith("Unnamed:"):
        raw = raw.iloc[:, 1:]
    if tuple(raw.columns) != _EXPECTED_SOURCE_COLUMNS:
        raise ValueError(f"schema NEFIN inesperado: {list(raw.columns)!r}")
    out = raw.rename(columns=_RENAME)
    out["ref_date"] = pd.to_datetime(out["ref_date"], format="%Y-%m-%d", errors="raise")
    for col in FACTOR_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="raise").astype("float64")
    if out["ref_date"].duplicated().any():
        raise ValueError("NEFIN contém ref_date duplicada")
    if out[list(FACTOR_COLUMNS)].isna().any().any():
        raise ValueError("NEFIN contém fator ausente")
    if not np.isfinite(out[list(FACTOR_COLUMNS)].to_numpy()).all():
        raise ValueError("NEFIN contém fator infinito")
    return out[["ref_date", *FACTOR_COLUMNS]].sort_values("ref_date").reset_index(drop=True)


def latest_nefin_commit(session=None, timeout: int = 60) -> dict[str, str]:
    """Devolve SHA, data e mensagem do commit oficial que publicou o CSV atual."""
    if session is None:
        import requests

        session = requests
    response = session.get(
        NEFIN_COMMITS_URL,
        params={"path": NEFIN_FILE_PATH, "per_page": 1},
        headers=_HEADERS,
        timeout=timeout,
    )
    response.raise_for_status()
    payload = json.loads(response.content)
    if not isinstance(payload, list) or not payload:
        raise ValueError("GitHub não devolveu commit para o CSV NEFIN")
    item = payload[0]
    try:
        return {
            "sha": item["sha"],
            "committed_at": item["commit"]["committer"]["date"],
            "message": item["commit"]["message"],
        }
    except (KeyError, TypeError) as exc:
        raise ValueError("resposta de commit NEFIN com schema inesperado") from exc


def nefin_raw_url(commit_sha: str) -> str:
    """URL imutável do CSV presa ao commit oficial."""
    if len(commit_sha) < 7 or not all(c in "0123456789abcdef" for c in commit_sha.lower()):
        raise ValueError(f"SHA de commit inválido: {commit_sha!r}")
    return f"https://raw.githubusercontent.com/{NEFIN_REPOSITORY}/{commit_sha}/{NEFIN_FILE_PATH}"


def stamp_nefin_avail_date(df: pd.DataFrame, published_at) -> pd.DataFrame:
    """Carimba todas as linhas com a data de publicação do snapshot.

    Não existe calendário histórico linha a linha. Usar ``ref_date + 1`` inventaria
    disponibilidade e introduziria lookahead. O timestamp do commit é observável e auditável.
    """
    ts = pd.Timestamp(published_at)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    out = df.copy()
    if not out.empty and ts.normalize() < pd.to_datetime(out["ref_date"]).max().normalize():
        raise ValueError("published_at anterior à última ref_date do snapshot NEFIN")
    out["snapshot_published_at"] = ts
    out["avail_date"] = ts.normalize()
    return out


def compare_nefin_vintages(
    old: pd.DataFrame, new: pd.DataFrame, atol: float = 1e-10
) -> pd.DataFrame:
    """Resume revisões na sobreposição de dois snapshots para a suíte de robustez."""
    if atol < 0:
        raise ValueError("atol não pode ser negativo")
    overlap = old.merge(new, on="ref_date", suffixes=("_old", "_new"), validate="one_to_one")
    rows = []
    for factor in FACTOR_COLUMNS:
        delta = (overlap[f"{factor}_new"] - overlap[f"{factor}_old"]).abs()
        rows.append(
            {
                "factor": factor,
                "overlap_rows": len(overlap),
                "changed_rows": int((delta > atol).sum()),
                "changed_gt_1bp": int((delta > 1e-4).sum()),
                "max_abs_revision": float(delta.max()) if len(delta) else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _write_manifest(
    content: bytes, commit: dict[str, str], raw_url: str, stamp: str, manifest_dir: str | Path
) -> Path:
    panel = parse_nefin(content)
    manifest = {
        "source": "NEFIN-FEA-USP",
        "page_url": NEFIN_PAGE_URL,
        "public_url": NEFIN_PUBLIC_URL,
        "repository": NEFIN_REPOSITORY,
        "file_path": NEFIN_FILE_PATH,
        "commit_sha": commit["sha"],
        "commit_date": commit["committed_at"],
        "commit_message": commit["message"],
        "pinned_url": raw_url,
        "first_ref_date": panel["ref_date"].min().date().isoformat(),
        "last_ref_date": panel["ref_date"].max().date().isoformat(),
        "rows": len(panel),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "downloaded_at": datetime.now(UTC).isoformat(),
    }
    dest = Path(manifest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"nefin_factors_{stamp}_{commit['sha'][:12]}.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def download_nefin(
    dest_dir: str | Path = "data/raw/nefin",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 60,
) -> Path:
    """Baixa o CSV oficial preso ao commit e grava manifesto do snapshot.

    A consulta leve ao commit ocorre em toda chamada; o CSV só é baixado se aquele SHA ainda
    não estiver no cache local. Assim uma atualização no mesmo dia não é perdida.
    """
    if session is None:
        import requests

        session = requests
    commit = latest_nefin_commit(session=session, timeout=timeout)
    raw_url = nefin_raw_url(commit["sha"])
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"nefin_factors_{stamp}_{commit['sha'][:12]}.csv"
    if out.exists():
        return out
    response = session.get(raw_url, headers=_HEADERS, timeout=timeout)
    response.raise_for_status()
    content = response.content
    parse_nefin(content)  # valida antes de persistir resposta aparentemente bem-sucedida
    out.write_bytes(content)
    _write_manifest(content, commit, raw_url, stamp, manifest_dir)
    return out
