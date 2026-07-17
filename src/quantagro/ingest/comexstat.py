"""Ingestão do ComexStat/Secex-MDIC — camada de confirmação por comércio exterior (§3 de 02_DADOS).

O ComexStat confirma a tese em **baixa frequência**: o volume/valor exportado das commodities
agrícolas é a contraparte comercial do choque de oferta que o clima e a CONAB sinalizam. Entra
como **camada de confirmação mensal** (H1b), não como gatilho de alta frequência.

Duas propriedades da fonte governam o desenho — ambas reconfirmadas ao vivo (2026-07-16):

- 🔴 **Gotcha do NCM (falha silenciosa)**: a API exige o código NCM como **string de 8 dígitos**.
  Passar como inteiro (perdendo o zero à esquerda) retorna **lista vazia com `success: true`** —
  erro sem erro. Verificado: café `"09011110"` devolve 2 linhas; `9011110` (int) devolve 0. Isso
  afeta café (0901) e carnes (02xx), metade das NCMs da tese. Por isso `_validate_ncms` **falha
  alto** para qualquer valor que não seja string de 8 dígitos — o guardrail obrigatório da §3.1.

- 🔴 **Não preserva vintage**: "nas divulgações consolidadas, todos os meses do ano corrente
  podem sofrer alterações" — congelamento só em fevereiro do ano seguinte. Não há consulta
  *as-of*. Um download em massa hoje devolve a versão **atual** (revisada). Mitigação: o endpoint
  `general/dates/updated` informa o mês mais recente e a data de atualização — gravados no
  manifesto como prova de vintage —, e a fonte é usada como confirmação mensal, não como gatilho.

Schema da API (verificado): `POST /general` com corpo JSON (`flow`, `period.from/to` em "AAAA-MM",
`filters` por `ncm`, `details`, `metrics`), resposta `{"data":{"list":[...]},"success":true}` com
cada linha trazendo `coNcm`, `year`, `monthNumber`, `metricFOB` (US$) e `metricKG` (kg líquido) —
**as métricas vêm como string** e são convertidas aqui. Calendário: divulgação nos primeiros
dias úteis do mês seguinte (latência ~3-5 dias úteis); o carimbo `avail_date` é aplicado a
jusante por `quantagro.validate.pit`.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

_BASE_URL = "https://api-comexstat.mdic.gov.br"
_GENERAL_URL = f"{_BASE_URL}/general"
_DATES_UPDATED_URL = f"{_BASE_URL}/general/dates/updated"

# NCMs da tese (docs/02_DADOS.md §3.5), verificados contra a tabela oficial. Sempre string de 8
# dígitos — nunca int (ver gotcha na docstring). produto → lista de NCMs.
THESIS_NCMS: dict[str, tuple[str, ...]] = {
    "soja_grao": ("12019000",),
    "farelo_soja": ("23040010", "23040090"),
    "oleo_soja": ("15071000", "15079011"),
    "milho": ("10059010",),
    "acucar": ("17011400", "17019900"),
    "cafe": ("09011110", "09011190"),
    "carne_bovina": ("02013000", "02023000"),
    "frango": ("02071200", "02071400"),
    "celulose": ("47032900",),
    "algodao": ("52010010", "52010020"),
}


def _validate_ncms(ncms) -> list[str]:
    """Guardrail da §3.1: cada NCM tem que ser **string de exatamente 8 dígitos**.

    Int (que perde o zero à esquerda) ou string de comprimento errado dispararia o retorno vazio
    com `success: true` — falha silenciosa. Aqui vira erro alto, antes de bater na rede.
    """
    if isinstance(ncms, str):
        raise TypeError("passe uma sequência de NCMs (lista/tupla), não uma string única")
    out = []
    for v in ncms:
        if not isinstance(v, str):
            raise TypeError(f"NCM {v!r} tem que ser string (int perde o zero à esquerda)")
        if len(v) != 8 or not v.isdigit():
            raise ValueError(f"NCM tem que ter 8 dígitos, veio {v!r}")
        out.append(v)
    if not out:
        raise ValueError("nenhum NCM informado")
    return out


def build_query(
    ncms,
    period_from: str,
    period_to: str,
    flow: str = "export",
    details: tuple[str, ...] = ("ncm",),
    metrics: tuple[str, ...] = ("metricFOB", "metricKG"),
    month_detail: bool = True,
) -> dict:
    """Monta o corpo do `POST /general`, validando os NCMs (string de 8 dígitos)."""
    if flow not in ("export", "import"):
        raise ValueError(f"flow tem que ser 'export' ou 'import', veio {flow!r}")
    valid = _validate_ncms(ncms)
    return {
        "flow": flow,
        "monthDetail": month_detail,
        "period": {"from": period_from, "to": period_to},
        "filters": [{"filter": "ncm", "values": valid}],
        "details": list(details),
        "metrics": list(metrics),
    }


def dates_updated(session=None, timeout: int = 60) -> dict:
    """Consulta o endpoint de vintage: último mês disponível + data de atualização.

    Devolve `{'updated': 'AAAA-MM-DD', 'year': 'AAAA', 'monthNumber': 'MM'}`. É a prova de qual
    vintage a fonte servia no momento da captura (a fonte revisa o passado — ver docstring).
    """
    if session is None:
        import requests

        session = requests
    resp = session.get(_DATES_UPDATED_URL, timeout=timeout)
    resp.raise_for_status()
    return json.loads(resp.content).get("data", {})


def _stamped_name(flow: str, period_from: str, period_to: str, stamp: str) -> str:
    """Nome do arquivo/manifesto: um vintage por captura (a fonte sobrescreve o passado)."""
    return f"comexstat_{flow}_{period_from}_{period_to}_{stamp}.json"


def _write_manifest(query: dict, content: bytes, vintage: dict, stamp: str, manifest_dir) -> Path:
    """Manifesto de vintage: a fonte revisa até fev do ano seguinte, então a data de atualização
    (`dates/updated`) + a data de captura + o hash são a prova de qual versão foi usada."""
    md = Path(manifest_dir)
    md.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": "ComexStat-MDIC",
        "query": query,
        "vintage_updated": vintage.get("updated"),
        "vintage_latest_month": f"{vintage.get('year')}-{vintage.get('monthNumber')}"
        if vintage
        else None,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "downloaded_at": datetime.now(UTC).isoformat(),
    }
    path = md / _stamped_name(query["flow"], query["period"]["from"], query["period"]["to"], stamp)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def download_comex(
    ncms,
    period_from: str,
    period_to: str,
    flow: str = "export",
    dest_dir: str | Path = "data/raw/comexstat",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 120,
) -> Path:
    """Baixa uma consulta ao ComexStat e grava manifesto de vintage por captura.

    A fonte revisa o passado (não há consulta por vintage), então o destino leva a data de captura
    no nome — um vintage por captura — e não rebaixa se o arquivo do dia já existe (R12). O
    manifesto registra a data de atualização da fonte (`dates/updated`) como prova de vintage.
    """
    query = build_query(ncms, period_from, period_to, flow=flow)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    out = dest / _stamped_name(flow, period_from, period_to, stamp)
    if out.exists():
        return out
    if session is None:
        import requests

        session = requests
    resp = session.post(_GENERAL_URL, json=query, timeout=timeout)
    resp.raise_for_status()
    content = resp.content
    payload = json.loads(content)
    if not payload.get("success", False):
        raise ValueError(f"ComexStat retornou success=False: {payload.get('message')}")
    out.write_bytes(content)
    _write_manifest(
        query, content, dates_updated(session=session, timeout=timeout), stamp, manifest_dir
    )
    return out


def parse_comex(source: str | Path | bytes | dict) -> pd.DataFrame:
    """Parseia uma resposta do ComexStat em painel arrumado (formato longo).

    Uma linha por `(ref_date, co_ncm)`, com `metric_fob_usd` (US$) e `metric_kg` (kg líquido)
    convertidos de string para numérico. `ref_date` é o **último dia do mês de referência** (o
    dado é mensal); o carimbo `avail_date` (latência ~3-5 dias úteis, divulgação no início do mês
    seguinte) é aplicado a jusante por `validate.pit`.
    """
    if isinstance(source, dict):
        payload = source
    elif isinstance(source, bytes):
        payload = json.loads(source)
    else:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
    rows = payload.get("data", {}).get("list", [])
    cols = ["ref_date", "co_ncm", "metric_fob_usd", "metric_kg"]
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows)
    period = df["year"].astype(str) + "-" + df["monthNumber"].astype(str).str.zfill(2)
    df["ref_date"] = pd.PeriodIndex(period, freq="M").to_timestamp(how="end").normalize()
    df["co_ncm"] = df["coNcm"].astype(str)
    df["metric_fob_usd"] = pd.to_numeric(df["metricFOB"]).astype("int64")
    df["metric_kg"] = pd.to_numeric(df["metricKG"]).astype("int64")
    return df[cols].sort_values(["ref_date", "co_ncm"]).reset_index(drop=True)
