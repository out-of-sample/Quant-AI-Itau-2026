"""Preço LOCAL brasileiro de soja e milho (IPEADATA/DERAL-Seab-PR) — teste de preço final (D-040).

D-039 mostrou que o choque não transmite ao preço **mundial** (USD e proxy mundial×câmbio). Falta
o preço **local** brasileiro, que embute a base doméstica e é o preço que o produtor de fato
recebe e que o processador de fato paga. O CEPEA/ESALQ (a referência de preço local) está atrás
de Cloudflare, sem acesso programático reproduzível (D-025). O IPEADATA (IPEA, governo federal)
espelha, com API OData aberta e sem chave, a série da **Seab-PR/DERAL**:

- soja: ``DERAL12_PRSO12`` (preço médio recebido pelo agricultor, R$/60kg, mensal);
- milho: ``DERAL12_PRMI12`` (idem).

É o "preço recebido pelo agricultor" no Paraná — um dos maiores produtores e UF do experimento
primário. Não é o CEPEA, mas serve ao mesmo fim econômico (preço local em BRL) e é, para o lado
**produtor**, ainda mais direto: é a receita realizada, não o FOB porto. Limitações declaradas:
é preço do Paraná (não nacional) e pode sofrer revisão modesta; captura datada + manifesto por
disciplina; ``avail_date`` embute atraso de ~30 dias (preço do mês ``m`` compilado no mês
seguinte). Uso: **somente desfecho do teste de preço local (D-040)**; nunca gera posição.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

IPEA_URL = "http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{code}')"
# cultura primária -> série IPEADATA (preço local recebido pelo agricultor, R$/60kg, mensal)
SERIES_LOCAL = {"soy": "DERAL12_PRSO12", "corn_second": "DERAL12_PRMI12"}
PUBLICATION_LAG_DAYS = 30  # atraso conservador (preço do mês m compilado no mês seguinte)


def parse_ipea_prices(source: str | Path | bytes, crop: str) -> pd.DataFrame:
    """Converte o JSON OData do IPEADATA em ``[crop, ref_date, price, avail_date]`` (fim de mês)."""
    if crop not in SERIES_LOCAL:
        raise KeyError(f"cultura fora do primário: {crop!r}")
    if isinstance(source, bytes):
        payload = json.loads(source.decode("utf-8"))
    elif isinstance(source, (str, Path)) and Path(source).exists():
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
    else:
        payload = json.loads(str(source))
    recs = [r for r in payload.get("value", []) if r.get("VALVALOR") is not None]
    if not recs:
        raise ValueError(f"série IPEADATA vazia para {crop} ({SERIES_LOCAL[crop]})")
    ref_month = pd.to_datetime([r["VALDATA"] for r in recs], utc=True).tz_localize(None)
    out = pd.DataFrame(
        {
            "crop": crop,
            "ref_date": (ref_month + pd.offsets.MonthEnd(0)).normalize(),
            "price": [float(r["VALVALOR"]) for r in recs],
        }
    )
    out["avail_date"] = out["ref_date"] + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    if (out["price"] <= 0).any():
        raise ValueError(f"preço não-positivo na série {SERIES_LOCAL[crop]}")
    return out.sort_values("ref_date").reset_index(drop=True)


def _write_manifest(content: bytes, crop: str, stamp: str, manifest_dir: str | Path) -> Path:
    panel = parse_ipea_prices(content, crop)
    latest = panel.iloc[-1]
    manifest = {
        "source": "IPEADATA (mirror of Seab-PR/DERAL)",
        "series_id": SERIES_LOCAL[crop],
        "crop": crop,
        "url": IPEA_URL.format(code=SERIES_LOCAL[crop]),
        "unit": "BRL per 60kg, farmer-received price, Parana, monthly",
        "license_note": "IPEADATA public data; non-commercial academic use",
        "publication_lag_days": PUBLICATION_LAG_DAYS,
        "latest_ref_date": latest["ref_date"].date().isoformat(),
        "latest_price": float(latest["price"]),
        "n_obs": int(len(panel)),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "downloaded_at": datetime.now(UTC).isoformat(),
    }
    dest = Path(manifest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"ipea_{SERIES_LOCAL[crop].lower()}_{stamp}.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def download_ipea_prices(
    crop: str,
    dest_dir: str | Path = "data/raw/ipea",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 60,
) -> Path:
    """Baixa a captura datada de uma série de preço local do IPEADATA e grava manifesto."""
    if crop not in SERIES_LOCAL:
        raise KeyError(f"cultura fora do primário: {crop!r}")
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"ipea_{SERIES_LOCAL[crop].lower()}_{stamp}.json"
    if out.exists():
        return out
    if session is None:
        import requests

        session = requests
    response = session.get(IPEA_URL.format(code=SERIES_LOCAL[crop]), timeout=timeout)
    response.raise_for_status()
    content = response.content
    parse_ipea_prices(content, crop)  # valida antes de persistir
    out.write_bytes(content)
    _write_manifest(content, crop, stamp, manifest_dir)
    return out


def load_local_prices(raw_dir: str | Path = "data/raw/ipea") -> pd.DataFrame:
    """Carrega e concatena as capturas mais recentes de soja e milho local já baixadas."""
    raw = Path(raw_dir)
    frames = []
    for crop, code in SERIES_LOCAL.items():
        files = sorted(raw.glob(f"ipea_{code.lower()}_*.json"))
        if not files:
            raise FileNotFoundError(
                f"captura IPEADATA ausente para {crop} — rode download_ipea_prices"
            )
        frames.append(parse_ipea_prices(files[-1], crop))
    return pd.concat(frames, ignore_index=True)
