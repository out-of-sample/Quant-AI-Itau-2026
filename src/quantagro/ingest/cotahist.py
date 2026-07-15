"""Ingestão do COTAHIST — série histórica oficial de pregão da B3.

O COTAHIST é a fonte de preço e de universo do projeto porque é **delisting-proof**: é um
registro do pregão e inclui todo papel negociado em cada dia, inclusive os que depois somem
(risco R4, decisão D-004). É um arquivo de **largura fixa**, registros de 245 bytes:

    tipo 00 = header | tipo 01 = detalhe (uma cotação) | tipo 99 = trailer

Os offsets abaixo (0-based, [início:fim]) seguem o layout oficial da B3 e foram **conferidos
contra um arquivo real** (dia 27/12/2024: PETR4=35,66, SLCE3=17,68, JBSS3=36,21, `fatcot=1`).

Preços vêm como inteiro com 2 casas implícitas (N(13)V99) ⇒ dividir por 100. `fatcot` (fator de
cotação) é 1 para ações normais; guardamos o valor para sinalizar as raras exceções (≠ 1) em vez
de assumir. Este módulo **só ingere/normaliza** — não ajusta por proventos (isso é
`quantagro.prices.adjust`).
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import IO

import pandas as pd

# Offsets 0-based [início:fim) do registro de detalhe (tipo 01), layout oficial da B3.
_OFF = {
    "data": (2, 10),
    "codbdi": (10, 12),
    "codneg": (12, 24),
    "tpmerc": (24, 27),
    "preult": (108, 121),
    "quatot": (152, 170),
    "voltot": (170, 188),
    "fatcot": (210, 217),
    "codisi": (230, 242),
}

_BASE_URL = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/"

# Mercado à vista, lote padrão — o segmento canônico para o fechamento diário de ações.
_CODBDI_LOTE_PADRAO = "02"
_TPMERC_VISTA = "010"


def _read_text(source: str | Path | bytes | IO) -> str:
    """Lê o conteúdo do COTAHIST de um caminho (.zip ou .txt), bytes ou file-like → texto.

    Aceita .ZIP (extrai o membro .TXT) ou o .TXT já cru. Encoding latin-1 (padrão da B3).
    """
    if isinstance(source, (str, Path)):
        raw: bytes = Path(source).read_bytes()
    elif isinstance(source, bytes):
        raw = source
    else:  # file-like
        chunk = source.read()
        if isinstance(chunk, str):
            return chunk
        raw = chunk
    if raw[:2] == b"PK":  # assinatura de ZIP
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            member = next(n for n in z.namelist() if n.upper().endswith(".TXT"))
            raw = z.read(member)
    return raw.decode("latin-1")


def parse_cotahist(source: str | Path | bytes | IO) -> pd.DataFrame:
    """Parseia o COTAHIST em um DataFrame arrumado de cotações (registros de detalhe).

    Retorna uma linha por cotação, colunas: date, ticker, close, quantity, financial_volume,
    codbdi, tpmerc, quote_factor, isin. Header e trailer são descartados. Vetorizado por
    fatiamento de string (sem loop por linha).
    """
    text = _read_text(source)
    s = pd.Series(text.splitlines(), dtype="string")
    s = s[s.str.slice(0, 2) == "01"]

    def col(name: str) -> pd.Series:
        a, b = _OFF[name]
        return s.str.slice(a, b)

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(col("data"), format="%Y%m%d"),
            "ticker": col("codneg").str.strip(),
            "close": col("preult").astype("int64") / 100,
            "quantity": col("quatot").astype("int64"),
            "financial_volume": col("voltot").astype("int64") / 100,
            "codbdi": col("codbdi"),
            "tpmerc": col("tpmerc"),
            "quote_factor": col("fatcot").astype("int64"),
            "isin": col("codisi").str.strip(),
        }
    )
    return df.reset_index(drop=True)


def filter_equities_spot(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém só o mercado à vista, lote padrão (o fechamento diário canônico das ações)."""
    keep = (df["codbdi"] == _CODBDI_LOTE_PADRAO) & (df["tpmerc"] == _TPMERC_VISTA)
    return df[keep].reset_index(drop=True)


def cotahist_url(period: str) -> str:
    """URL do arquivo COTAHIST para um período: 'A2024' (anual), 'M122024' (mensal),
    'D27122024' (diário)."""
    return f"{_BASE_URL}COTAHIST_{period}.ZIP"


def _write_manifest(period: str, url: str, content: bytes, manifest_dir: str | Path) -> Path:
    """Grava o manifesto de vintage: prova de qual arquivo (hash) foi baixado e quando."""
    md = Path(manifest_dir)
    md.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": "COTAHIST",
        "period": period,
        "url": url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "downloaded_at": datetime.now(UTC).isoformat(),
    }
    path = md / f"cotahist_{period}.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def download_cotahist(
    period: str,
    dest_dir: str | Path = "data/raw",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 120,
) -> Path:
    """Baixa (com cache) o COTAHIST de um período e grava o manifesto de vintage.

    Se o arquivo já existe em `dest_dir`, não rebaixa (o pipeline nunca depende de rede em
    tempo de execução — risco R12). `session` permite injetar um cliente HTTP (ou um fake em
    teste); por padrão usa `requests`.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"COTAHIST_{period}.ZIP"
    if out.exists():
        return out
    if session is None:
        import requests

        session = requests
    url = cotahist_url(period)
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    out.write_bytes(resp.content)
    _write_manifest(period, url, resp.content, manifest_dir)
    return out
