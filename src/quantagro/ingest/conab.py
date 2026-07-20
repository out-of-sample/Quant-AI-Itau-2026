"""Ingestão dos levantamentos de safra da CONAB (docs/02_DADOS.md §2).

Os arquivos do Portal de Informações da CONAB são CSV delimitados por `;`, encoding
latin-1, e o `Levantamento{Graos,Cafe,Cana}.txt` é um **painel de vintages verdadeiro**:
cada linha é a estimativa de um `(ano_agricola, uf, produto)` em um `id_levantamento`
específico (1º ao 12º para grãos; 1º ao 4º para café e cana). É o elo intermediário
datável da tese (D-005): o choque climático deve prever a *revisão* entre levantamentos.

Duas propriedades da fonte governam o desenho deste módulo:

- **A fonte reescreve o arquivo todo a cada divulgação** (não há URL por vintage).
  Por isso o download é carimbado com a data (um arquivo por dia de captura) e todo
  download grava manifesto com hash — a prova de qual vintage alimentou o backtest.
- **O arquivo NÃO traz a data de divulgação** de cada levantamento (risco R10) — só o
  número. O mapa `(ano_agricola, id_levantamento) → data` é curadoria à parte, em
  `quantagro.ingest.conab_calendar`, e o carimbo `avail_date` acontece lá.

Fatos do arquivo real (verificados em 2026-07-16):
- `id_levantamento == 99` ("LEVANT") é resíduo legado sem número de levantamento
  (algodão 2018/19–2021/22; 2017/18 tem só o 12º levantamento; café 2017; cana até
  2020/21). Não é datável — o parser
  preserva a linha, mas o calendário nunca a cobre (carimbo falha alto, de propósito).
- Grãos tem `ano_agricola` em dois formatos: "2017/18" (safra de verão) e "2018" (ano
  civil — culturas de inverno: trigo, aveia, cevada...). O alinhamento dos levantamentos
  de inverno com o calendário de boletins é ambíguo (testado empiricamente: as revisões
  de trigo não casam com um único ano-boletim) ⇒ culturas de inverno ficam fora do
  calendário até serem verificadas. A tese não as usa.
- Café usa ano civil (int no arquivo; normalizado para str). Em 2020 **não houve o 2º
  levantamento** (suspenso na pandemia) — buraco real da fonte, não do nosso mapa.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import IO

import pandas as pd

_BASE_URL = "https://portaldeinformacoes.conab.gov.br/downloads/arquivos/"

# dataset → (nome do arquivo na CONAB, colunas de medida específicas)
DATASETS = {
    "graos": "LevantamentoGraos.txt",
    "cafe": "LevantamentoCafe.txt",
    "cana": "LevantamentoCana.txt",
}

# Colunas canônicas comuns aos três arquivos, na ordem de saída.
_ID_COLS = ["ano_agricola", "safra", "uf", "produto", "id_produto", "id_levantamento"]


def conab_url(dataset: str) -> str:
    """URL do arquivo de levantamento para um dataset ('graos', 'cafe' ou 'cana')."""
    if dataset not in DATASETS:
        raise ValueError(f"dataset desconhecido: {dataset!r} (use {sorted(DATASETS)})")
    return f"{_BASE_URL}{DATASETS[dataset]}"


def _write_manifest(dataset: str, url: str, content: bytes, stamp: str, manifest_dir) -> Path:
    """Grava o manifesto de vintage: a CONAB reescreve o arquivo a cada divulgação,
    então o hash + data de captura são a única prova de qual vintage foi usado."""
    md = Path(manifest_dir)
    md.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": "CONAB",
        "dataset": dataset,
        "url": url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "downloaded_at": datetime.now(UTC).isoformat(),
    }
    path = md / f"conab_{dataset}_{stamp}.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def download_conab(
    dataset: str,
    dest_dir: str | Path = "data/raw/conab",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 300,
) -> Path:
    """Baixa o levantamento de um dataset e grava manifesto, carimbando a data de captura.

    Diferente do COTAHIST (imutável por período), o arquivo da CONAB **muda no lugar** a
    cada divulgação. O destino leva a data de captura no nome (um vintage por dia); se o
    arquivo de hoje já existe, não rebaixa (pipeline nunca depende de rede — R12).
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    out = dest / f"{DATASETS[dataset].removesuffix('.txt')}_{stamp}.txt"
    if out.exists():
        return out
    if session is None:
        import requests

        session = requests
    url = conab_url(dataset)
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    out.write_bytes(resp.content)
    _write_manifest(dataset, url, resp.content, stamp, manifest_dir)
    return out


def parse_levantamento(source: str | Path | bytes | IO, dataset: str) -> pd.DataFrame:
    """Parseia um Levantamento{Graos,Cafe,Cana}.txt em painel arrumado de vintages.

    Uma linha por `(ano_agricola, safra, uf, produto, id_levantamento)`, com as medidas
    do arquivo (produção, área, produtividade — cana traz também açúcar, etanol e ATR).
    Normalizações: strip de espaços (o arquivo padeja com brancos), `ano_agricola` como
    string ("2023/24" ou "2023"), `id_levantamento` como int. Nenhuma linha é descartada
    — inclusive `id_levantamento == 99` (ver docstring do módulo).
    """
    if dataset not in DATASETS:
        raise ValueError(f"dataset desconhecido: {dataset!r} (use {sorted(DATASETS)})")
    df = pd.read_csv(source, sep=";", encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    # cana usa nomes próprios para as mesmas colunas de identificação
    df = df.rename(
        columns={"dsc_safra_previsao": "safra", "produtcao_atr_kg_t": "producao_atr_kg_t"}
    )
    for c in df.columns:
        if df[c].dtype == object or str(df[c].dtype) == "str":
            df[c] = df[c].str.strip()
    df["ano_agricola"] = df["ano_agricola"].astype("str").str.strip()
    df["id_levantamento"] = df["id_levantamento"].astype("int64")
    if df.empty:
        raise ValueError(f"arquivo de levantamento ({dataset}) vazio após o parse")
    measures = [c for c in df.columns if c not in _ID_COLS and c != "dsc_levantamento"]
    for c in measures:
        df[c] = df[c].astype("float64")
    return df[_ID_COLS + measures].reset_index(drop=True)
