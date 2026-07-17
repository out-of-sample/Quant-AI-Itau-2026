"""Ingestão point-in-time da PAM/IBGE, tabela SIDRA 1612.

A PAM localiza a produção de soja e milho dentro de cada UF. Ela não gera sinal e não informa
milho 2ª safra separadamente no nível municipal: ``corn_total`` é um proxy espacial declarado
em D-023/R15. A fonte reescreve anos antigos; por isso cada download é uma captura datada com
hash. O ``avail_date`` reconstrói quando a edição anual apareceu, mas não desfaz correções
retroativas já incorporadas pelo SIDRA atual.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from quantagro.ingest.pam_calendar import pam_release
from quantagro.validate.pit import available_asof

TABLE = "1612"
VARIABLE_QUANTITY = "214"
UNIT_TONNES = "1017"
_BASE_URL = "https://apisidra.ibge.gov.br/values"

PAM_PRODUCTS: dict[str, str] = {
    "corn_total": "2711",
    "soy": "2713",
}

UF_CODES: dict[str, str] = {
    "BA": "29",
    "MG": "31",
    "PR": "41",
    "RS": "43",
    "MS": "50",
    "MT": "51",
    "GO": "52",
}
_CODE_TO_UF = {code: uf for uf, code in UF_CODES.items()}
_MISSING_SYMBOLS = {"..", "...", "X"}


def _validate_query(crop: str, years, ufs) -> tuple[list[int], list[str]]:
    if crop not in PAM_PRODUCTS:
        raise ValueError(f"produto PAM desconhecido: {crop!r}; use {sorted(PAM_PRODUCTS)}")
    if isinstance(years, (str, bytes)) or isinstance(ufs, str):
        raise TypeError("years e ufs devem ser sequências, não string única")
    ys = sorted({int(year) for year in years})
    us = sorted({str(uf).upper() for uf in ufs})
    if not ys or not us:
        raise ValueError("years e ufs não podem ser vazios")
    for year in ys:
        pam_release(year)  # prova PIT obrigatória antes de tocar na rede
    unknown = sorted(set(us) - UF_CODES.keys())
    if unknown:
        raise ValueError(f"UF fora do suporte primário: {unknown}")
    return ys, us


def pam_url(crop: str, years, ufs) -> str:
    """Consulta municipal da quantidade produzida, sem agregação silenciosa."""
    ys, us = _validate_query(crop, years, ufs)
    state_codes = ",".join(UF_CODES[uf] for uf in us)
    periods = ",".join(map(str, ys))
    product = PAM_PRODUCTS[crop]
    return (
        f"{_BASE_URL}/t/{TABLE}/n6/in%20n3%20{state_codes}/v/{VARIABLE_QUANTITY}/"
        f"p/{periods}/c81/{product}?formato=json"
    )


def _snapshot_name(crop: str, years: list[int], ufs: list[str], stamp: str) -> str:
    scope = "-".join(uf.lower() for uf in ufs)
    return f"pam_{TABLE}_{crop}_{years[0]}-{years[-1]}_{scope}_{stamp}.json"


def _write_manifest(
    crop: str,
    years: list[int],
    ufs: list[str],
    url: str,
    content: bytes,
    stamp: str,
    manifest_dir,
) -> Path:
    md = Path(manifest_dir)
    md.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": "IBGE-SIDRA-PAM",
        "table": TABLE,
        "variable": VARIABLE_QUANTITY,
        "crop": crop,
        "years": years,
        "ufs": ufs,
        "release_dates": {
            str(year): pam_release(year).avail_date.date().isoformat() for year in years
        },
        "url": url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "downloaded_at": datetime.now(UTC).isoformat(),
        "vintage_warning": (
            "SIDRA reescreve valores históricos; captura não reconstrói vintage original"
        ),
    }
    path = md / _snapshot_name(crop, years, ufs, stamp)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def download_pam(
    crop: str,
    years,
    ufs,
    dest_dir: str | Path = "data/raw/pam",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 180,
) -> Path:
    """Baixa uma captura datada da tabela 1612 e grava manifesto de vintage."""
    ys, us = _validate_query(crop, years, ufs)
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / _snapshot_name(crop, ys, us, stamp)
    if out.exists():
        return out
    if session is None:
        import requests

        session = requests
    url = pam_url(crop, ys, us)
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    content = resp.content
    payload = json.loads(content)
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("SIDRA devolveu resposta vazia ou fora do schema esperado")
    out.write_bytes(content)
    _write_manifest(crop, ys, us, url, content, stamp, manifest_dir)
    return out


def _load_payload(source: str | Path | bytes | list[dict]) -> list[dict]:
    if isinstance(source, list):
        return source
    if isinstance(source, bytes):
        return json.loads(source)
    return json.loads(Path(source).read_text(encoding="utf-8-sig"))


def _quantity(value: object) -> tuple[float, str]:
    text = str(value).strip()
    if text == "-":
        return 0.0, "zero"
    if text in _MISSING_SYMBOLS or not text:
        return np.nan, f"missing:{text or 'blank'}"
    try:
        return float(text.replace(" ", "")), "observed"
    except ValueError as exc:
        raise ValueError(f"valor SIDRA não reconhecido: {value!r}") from exc


def parse_pam(source: str | Path | bytes | list[dict]) -> pd.DataFrame:
    """Normaliza o JSON do SIDRA e aplica o calendário anual de disponibilidade."""
    payload = _load_payload(source)
    columns = [
        "ref_date",
        "avail_date",
        "ref_year",
        "crop",
        "uf",
        "municipality_code",
        "municipality_name",
        "quantity_tonnes",
        "value_status",
    ]
    if len(payload) <= 1:
        return pd.DataFrame(columns=columns)
    rows = []
    reverse_products = {code: crop for crop, code in PAM_PRODUCTS.items()}
    for raw in payload[1:]:  # primeira linha é o cabeçalho semântico da API
        if raw.get("D2C") != VARIABLE_QUANTITY or raw.get("MC") != UNIT_TONNES:
            raise ValueError(f"variável/unidade SIDRA inesperada: {raw.get('D2C')}/{raw.get('MC')}")
        product_code = str(raw.get("D4C", ""))
        if product_code not in reverse_products:
            raise ValueError(f"produto SIDRA inesperado: {product_code!r}")
        municipality_code = str(raw.get("D1C", ""))
        if len(municipality_code) != 7 or not municipality_code.isdigit():
            raise ValueError(f"geocódigo municipal inválido: {municipality_code!r}")
        uf = _CODE_TO_UF.get(municipality_code[:2])
        if uf is None:
            raise ValueError(f"geocódigo fora das UFs primárias: {municipality_code!r}")
        year = int(raw["D3C"])
        release = pam_release(year)
        quantity, status = _quantity(raw.get("V"))
        name = str(raw.get("D1N", "")).removesuffix(f" - {uf}").removesuffix(f" ({uf})").strip()
        rows.append(
            {
                "ref_date": pd.Timestamp(year, 12, 31),
                "avail_date": release.avail_date,
                "ref_year": year,
                "crop": reverse_products[product_code],
                "uf": uf,
                "municipality_code": municipality_code,
                "municipality_name": name,
                "quantity_tonnes": quantity,
                "value_status": status,
            }
        )
    out = pd.DataFrame(rows, columns=columns)
    key = ["ref_year", "crop", "municipality_code"]
    if out.duplicated(key).any():
        raise ValueError(f"duplicata SIDRA na chave {key}")
    return out.sort_values(key).reset_index(drop=True)


def pam_weights_asof(panel: pd.DataFrame, t) -> pd.DataFrame:
    """Pesos municipais da edição mais recente disponível em ``t``, dentro de cada UF.

    O símbolo ``-`` do SIDRA é zero verdadeiro. ``...`` é dado não disponível: permanece
    ``NaN`` (nunca vira zero), recebe peso ``NaN`` e é contado em ``missing_municipalities``.
    Os pesos reportados normalizam a tonelagem conhecida para um. Falha somente quando toda a
    UF/cultura é ausente ou soma zero.
    """
    visible = available_asof(panel, t).copy()
    if visible.empty:
        raise ValueError(f"nenhuma edição PAM disponível em {pd.Timestamp(t).date()}")
    group = ["crop", "uf"]
    latest = visible.groupby(group)["ref_year"].transform("max")
    selected = visible[visible["ref_year"] == latest].copy()
    totals = selected.groupby(group)["quantity_tonnes"].transform("sum")
    if (totals <= 0).any():
        bad = selected.loc[totals <= 0, group].drop_duplicates().to_dict("records")
        raise ValueError(f"produção PAM não positiva em UF/cultura: {bad}")
    selected["within_uf_weight"] = selected["quantity_tonnes"] / totals
    missing = selected["quantity_tonnes"].isna()
    selected["reported_municipalities"] = (
        (~missing).groupby([selected["crop"], selected["uf"]]).transform("sum")
    )
    selected["missing_municipalities"] = missing.groupby(
        [selected["crop"], selected["uf"]]
    ).transform("sum")
    columns = [
        "ref_date",
        "avail_date",
        "ref_year",
        "crop",
        "uf",
        "municipality_code",
        "municipality_name",
        "quantity_tonnes",
        "value_status",
        "within_uf_weight",
        "reported_municipalities",
        "missing_municipalities",
    ]
    return selected[columns].sort_values(["crop", "uf", "municipality_code"]).reset_index(drop=True)
