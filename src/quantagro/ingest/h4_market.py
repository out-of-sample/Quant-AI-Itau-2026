"""Controles diários de mercado para a regressão de spanning H4.

H4 é atribuição ex post: estes dados nunca geram posição. Soja, milho e açúcar usam os ETFs
Teucrium SOYB, CORN e CANE, cujos benchmarks distribuem a exposição entre três vencimentos.
Isso evita construir, depois de ver retornos, uma regra própria de rolagem de futuros.

Os preços ajustados são capturados pelo endpoint Chart do Yahoo e presos por hash/manifesto.
O câmbio é a série diária DEXBZUS do FRED/Federal Reserve (BRL por USD). Ambas as fontes podem
reescrever o histórico; por isso o snapshot inteiro só fica disponível na data da captura.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

YAHOO_CHART_URL = "https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
FRED_DAILY_FX_SERIES = "DEXBZUS"

COMMODITY_ETFS = {
    "soy": "SOYB",
    "corn_second": "CORN",
    "sugar": "CANE",
}
FUND_PAGES = {
    "soy": "https://teucrium.com/soyb",
    "corn_second": "https://teucrium.com/corn",
    "sugar": "https://teucrium.com/cane",
}
YAHOO_HEADERS = {"User-Agent": "Mozilla/5.0"}


def _read_bytes(source: str | Path | bytes) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, Path):
        return source.read_bytes()
    text = str(source)
    if not text.lstrip().startswith(("{", "[")):
        path = Path(text)
        if path.exists():
            return path.read_bytes()
    return text.encode()


def parse_yahoo_adjusted(source: str | Path | bytes, control: str) -> pd.DataFrame:
    """Parseia um snapshot Chart em níveis ajustados diários, sem preencher lacunas."""
    if control not in COMMODITY_ETFS:
        raise KeyError(f"controle de commodity desconhecido: {control!r}")
    try:
        payload = json.loads(_read_bytes(source))
        chart = payload["chart"]
        if chart.get("error") is not None:
            raise ValueError(f"Yahoo Chart devolveu erro: {chart['error']!r}")
        result = chart["result"]
        if not isinstance(result, list) or len(result) != 1:
            raise ValueError("Yahoo Chart deve devolver exatamente um resultado")
        item = result[0]
        symbol = item["meta"]["symbol"]
        timestamps = item["timestamp"]
        adjusted = item["indicators"]["adjclose"][0]["adjclose"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("schema Yahoo Chart inesperado") from exc

    expected = COMMODITY_ETFS[control]
    if symbol != expected:
        raise ValueError(f"ticker Yahoo divergente: esperado {expected}, veio {symbol}")
    if len(timestamps) != len(adjusted) or not timestamps:
        raise ValueError("Yahoo Chart tem comprimentos incompatíveis ou série vazia")
    if any(value is None for value in adjusted):
        raise ValueError("Yahoo Chart contém adjusted close ausente")

    dates = (
        pd.to_datetime(timestamps, unit="s", utc=True)
        .tz_convert("America/New_York")
        .tz_localize(None)
        .normalize()
    )
    out = pd.DataFrame(
        {
            "ref_date": dates,
            "control": control,
            "symbol": symbol,
            "adjusted_close": pd.to_numeric(adjusted, errors="raise").astype("float64"),
        }
    )
    if out["ref_date"].duplicated().any():
        raise ValueError("Yahoo Chart contém ref_date duplicada")
    values = out["adjusted_close"].to_numpy()
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Yahoo Chart contém adjusted close inválido")
    return out.sort_values("ref_date").reset_index(drop=True)


def parse_fred_daily_fx(source: str | Path | bytes) -> pd.DataFrame:
    """Parseia DEXBZUS em nível diário BRL por USD, descartando feriados sem observação."""
    raw = pd.read_csv(StringIO(_read_bytes(source).decode()))
    expected = ("observation_date", FRED_DAILY_FX_SERIES)
    if tuple(raw.columns) != expected:
        raise ValueError(f"schema FRED DEXBZUS inesperado: {list(raw.columns)!r}")
    value = raw[FRED_DAILY_FX_SERIES]
    text = value.astype(str).str.strip()
    raw = raw[value.notna() & text.ne("") & text.ne(".")].copy()
    out = pd.DataFrame(
        {
            "ref_date": pd.to_datetime(raw["observation_date"], errors="raise"),
            "brl_per_usd": pd.to_numeric(raw[FRED_DAILY_FX_SERIES], errors="raise").astype(
                "float64"
            ),
        }
    )
    if out.empty or out["ref_date"].duplicated().any():
        raise ValueError("FRED DEXBZUS vazio ou com ref_date duplicada")
    values = out["brl_per_usd"].to_numpy()
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("FRED DEXBZUS contém câmbio inválido")
    return out.sort_values("ref_date").reset_index(drop=True)


def _write_manifest(
    content: bytes,
    *,
    role: str,
    raw_path: Path,
    source_url: str,
    rows: int,
    first_ref_date: pd.Timestamp,
    last_ref_date: pd.Timestamp,
    manifest_path: Path,
    extra: dict[str, object],
) -> None:
    manifest = {
        "source": "Yahoo-Chart" if role != "usdbrl" else "FRED-Federal-Reserve",
        "role": role,
        "raw_path": str(raw_path),
        "url": source_url,
        "rows": rows,
        "first_ref_date": first_ref_date.date().isoformat(),
        "last_ref_date": last_ref_date.date().isoformat(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "downloaded_at": datetime.now(UTC).isoformat(),
        **extra,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def download_h4_market(
    *,
    start: str = "2019-12-01",
    end: str = "2026-01-02",
    dest_dir: str | Path = "data/raw/h4_market",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 60,
) -> dict[str, Path]:
    """Baixa os quatro snapshots H4 e grava um manifesto por fonte.

    ``end`` é exclusivo. O início antecede 2020 para permitir calcular o primeiro retorno
    no calendário B3 sem preencher o nível anterior com informação futura.
    """
    if pd.Timestamp(start) >= pd.Timestamp(end):
        raise ValueError("intervalo H4 exige start < end")
    if session is None:
        import requests

        session = requests

    stamp = datetime.now(UTC).strftime("%Y%m%d")
    raw_dir = Path(dest_dir)
    manifests = Path(manifest_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    period1 = int(pd.Timestamp(start, tz="UTC").timestamp())
    period2 = int(pd.Timestamp(end, tz="UTC").timestamp())

    for control, symbol in COMMODITY_ETFS.items():
        out = raw_dir / f"yahoo_{symbol.lower()}_{stamp}.json"
        manifest_path = manifests / f"h4_yahoo_{control}_{stamp}.json"
        paths[control] = out
        if out.exists():
            parse_yahoo_adjusted(out, control)
            if not manifest_path.is_file():
                raise FileNotFoundError(f"cache H4 sem manifesto: {manifest_path}")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("sha256") != hashlib.sha256(out.read_bytes()).hexdigest():
                raise ValueError(f"cache H4 diverge do manifesto: {control}")
            continue
        url = YAHOO_CHART_URL.format(symbol=symbol)
        response = session.get(
            url,
            params={
                "period1": period1,
                "period2": period2,
                "interval": "1d",
                "events": "div,splits",
                "includeAdjustedClose": "true",
            },
            headers=YAHOO_HEADERS,
            timeout=timeout,
        )
        response.raise_for_status()
        content = response.content
        panel = parse_yahoo_adjusted(content, control)
        out.write_bytes(content)
        _write_manifest(
            content,
            role=control,
            raw_path=out,
            source_url=url,
            rows=len(panel),
            first_ref_date=panel["ref_date"].min(),
            last_ref_date=panel["ref_date"].max(),
            manifest_path=manifest_path,
            extra={
                "symbol": symbol,
                "fund_page": FUND_PAGES[control],
                "field": "adjusted_close",
                "currency": "USD",
                "period_start": start,
                "period_end_exclusive": end,
            },
        )

    fx_out = raw_dir / f"fred_{FRED_DAILY_FX_SERIES.lower()}_{stamp}.csv"
    fx_manifest = manifests / f"h4_fred_usdbrl_{stamp}.json"
    paths["usdbrl"] = fx_out
    if fx_out.exists():
        parse_fred_daily_fx(fx_out)
        if not fx_manifest.is_file():
            raise FileNotFoundError(f"cache H4 sem manifesto: {fx_manifest}")
        manifest = json.loads(fx_manifest.read_text(encoding="utf-8"))
        if manifest.get("sha256") != hashlib.sha256(fx_out.read_bytes()).hexdigest():
            raise ValueError("cache H4 diverge do manifesto: usdbrl")
        return paths
    fx_url = FRED_CSV_URL.format(series_id=FRED_DAILY_FX_SERIES)
    response = session.get(fx_url, timeout=timeout)
    response.raise_for_status()
    content = response.content
    panel = parse_fred_daily_fx(content)
    fx_out.write_bytes(content)
    _write_manifest(
        content,
        role="usdbrl",
        raw_path=fx_out,
        source_url=fx_url,
        rows=len(panel),
        first_ref_date=panel["ref_date"].min(),
        last_ref_date=panel["ref_date"].max(),
        manifest_path=fx_manifest,
        extra={
            "series_id": FRED_DAILY_FX_SERIES,
            "unit": "Brazilian reais per U.S. dollar",
            "field": "brl_per_usd",
        },
    )
    return paths


def load_h4_market(raw_dir: str | Path = "data/raw/h4_market") -> dict[str, pd.DataFrame]:
    """Carrega a captura mais recente de cada controle H4 já baixado."""
    root = Path(raw_dir)
    out: dict[str, pd.DataFrame] = {}
    for control, symbol in COMMODITY_ETFS.items():
        files = sorted(root.glob(f"yahoo_{symbol.lower()}_*.json"))
        if not files:
            raise FileNotFoundError(f"captura Yahoo H4 ausente para {control}")
        out[control] = parse_yahoo_adjusted(files[-1], control)
    fx_files = sorted(root.glob(f"fred_{FRED_DAILY_FX_SERIES.lower()}_*.csv"))
    if not fx_files:
        raise FileNotFoundError("captura FRED diária H4 ausente para usdbrl")
    out["usdbrl"] = parse_fred_daily_fx(fx_files[-1])
    return out
