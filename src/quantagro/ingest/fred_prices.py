"""Preços mensais globais de soja e milho (FRED / IMF Primary Commodity Prices) — H2a (D-036).

Fonte do desfecho de H2a: o **preço-referência mundial** de que o produtor brasileiro é
*price-taker* (o 20-F da BrasilAgro declara que o preço da soja segue a CBOT). Séries do FRED,
originadas do IMF Primary Commodity Prices, em USD por tonelada, frequência mensal:

- soja: ``PSOYBUSDM`` (Global price of Soybeans);
- milho 2ª: ``PMAIZMTUSDM`` (Global price of Corn).

Preço **não é reescrito** como estimativa de safra (CONAB) ou fator (NEFIN): é vintage-estável
por natureza. Ainda assim a captura é datada e recebe manifesto com hash, por disciplina de
reprodutibilidade. ``avail_date`` embute o atraso de publicação do IMF (~3 semanas no mês
seguinte): valor do mês ``m`` disponível a partir de ``fim de m + 21 dias`` — conservador.

Uso: **somente desfecho de H2a** (transmissão do ``Shock`` ao preço). Não gera posição, sizing
nem execução. A frequência mensal da linha não implica disponibilidade diária.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import pandas as pd

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
# cultura primária -> série FRED (IMF Primary Commodity Prices, USD/tonelada, mensal)
SERIES = {"soy": "PSOYBUSDM", "corn_second": "PMAIZMTUSDM"}
PUBLICATION_LAG_DAYS = 21  # atraso conservador de publicação do IMF no mês seguinte


def parse_fred_prices(source: str | Path | bytes, crop: str) -> pd.DataFrame:
    """Converte o CSV do FRED em painel tidy ``[crop, ref_date, price, avail_date]``.

    ``ref_date`` = fim do mês de referência; ``avail_date`` = ``ref_date + 21 dias`` (atraso de
    publicação do IMF). Linhas sem valor (``.``) são descartadas — nunca convertidas em zero.
    """
    if crop not in SERIES:
        raise KeyError(f"cultura fora do primário de H2a: {crop!r}")
    if isinstance(source, bytes):
        text = source.decode("utf-8")
    elif isinstance(source, (str, Path)) and Path(source).exists():
        text = Path(source).read_text(encoding="utf-8")
    else:
        text = str(source)
    raw = pd.read_csv(StringIO(text))
    value_col = [c for c in raw.columns if c != "observation_date"][0]
    raw = raw[raw[value_col].astype(str).str.strip() != "."].copy()
    ref_month = pd.to_datetime(raw["observation_date"])
    out = pd.DataFrame(
        {
            "crop": crop,
            "ref_date": (ref_month + pd.offsets.MonthEnd(0)).dt.normalize(),
            "price": raw[value_col].astype(float).to_numpy(),
        }
    )
    out["avail_date"] = out["ref_date"] + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    if (out["price"] <= 0).any():
        raise ValueError(f"preço não-positivo na série {SERIES[crop]}")
    return out.sort_values("ref_date").reset_index(drop=True)


def _write_manifest(content: bytes, crop: str, stamp: str, manifest_dir: str | Path) -> Path:
    panel = parse_fred_prices(content, crop)
    latest = panel.iloc[-1]
    manifest = {
        "source": "FRED/IMF-Primary-Commodity-Prices",
        "series_id": SERIES[crop],
        "crop": crop,
        "url": FRED_CSV_URL.format(series_id=SERIES[crop]),
        "unit": "USD per metric ton, monthly average",
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
    path = dest / f"fred_{SERIES[crop].lower()}_{stamp}.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def download_fred_prices(
    crop: str,
    dest_dir: str | Path = "data/raw/fred",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 60,
) -> Path:
    """Baixa a captura datada de uma série FRED e grava manifesto de vintage.

    Cache por dia de captura: não rebaixa no mesmo dia; uma captura futura gera outro arquivo e
    outro hash. Valida o parse antes de persistir para não gravar um arquivo vazio bem-sucedido.
    """
    if crop not in SERIES:
        raise KeyError(f"cultura fora do primário de H2a: {crop!r}")
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"fred_{SERIES[crop].lower()}_{stamp}.csv"
    if out.exists():
        return out
    if session is None:
        import requests

        session = requests
    response = session.get(FRED_CSV_URL.format(series_id=SERIES[crop]), timeout=timeout)
    response.raise_for_status()
    content = response.content
    parse_fred_prices(content, crop)  # valida antes de persistir
    out.write_bytes(content)
    _write_manifest(content, crop, stamp, manifest_dir)
    return out


def load_commodity_prices(raw_dir: str | Path = "data/raw/fred") -> pd.DataFrame:
    """Carrega e concatena as capturas mais recentes de soja e milho já baixadas."""
    raw = Path(raw_dir)
    frames = []
    for crop, series_id in SERIES.items():
        files = sorted(raw.glob(f"fred_{series_id.lower()}_*.csv"))
        if not files:
            raise FileNotFoundError(f"captura FRED ausente para {crop} — rode download_fred_prices")
        frames.append(parse_fred_prices(files[-1], crop))
    return pd.concat(frames, ignore_index=True)
