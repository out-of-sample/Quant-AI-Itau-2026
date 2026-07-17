"""Ingestão do Oceanic Niño Index (ONI) da NOAA/CPC.

O ONI é um controle, não o sinal da tese: impede atribuir ao choque climático regional um
efeito que seja apenas ENSO global. A fonte oficial publica uma média móvel de três meses da
anomalia ERSST.v5 na região Niño 3.4. A temporada é datada pelo mês central: ``DJF 2025`` tem
``ref_date = 2025-01-31``.

A NOAA informa duas propriedades que governam o contrato point-in-time:

- a página é atualizada até o dia 5 de cada mês; uma temporada só existe quando o terceiro
  mês terminou, logo ``DJF`` aparece inicialmente em 5 de março;
- os valores mais recentes podem mudar por até dois meses devido ao filtro do ERSST.v5.

Como a fonte sobrescreve o arquivo e não oferece consulta histórica *as-of*, o caso primário
usa o valor capturado somente depois da janela declarada de estabilização: ``avail_date`` é
o dia 5 do quarto mês após o mês central (publicação inicial + dois meses). Isso reduz, mas
não elimina, a contaminação de vintage: os períodos-base centrados também são atualizados a
cada cinco anos. Cada captura recebe data, hash e manifesto; a limitação permanece explícita.

Em 2026 a NOAA passou a usar RONI no monitoramento operacional. O pré-registro deste projeto
especifica ONI, portanto este módulo não troca o controle silenciosamente. RONI pode entrar
depois como teste de robustez, mediante decisão registrada.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import pandas as pd

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
ONI_SOURCE_PAGE = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php"

# Mês central de cada temporada sobreposta de três meses.
SEASON_CENTER_MONTH: dict[str, int] = {
    "DJF": 1,
    "JFM": 2,
    "FMA": 3,
    "MAM": 4,
    "AMJ": 5,
    "MJJ": 6,
    "JJA": 7,
    "JAS": 8,
    "ASO": 9,
    "SON": 10,
    "OND": 11,
    "NDJ": 12,
}

INITIAL_PUBLICATION_MONTHS = 2
REVISION_WINDOW_MONTHS = 2
PUBLICATION_DAY = 5


def _load_text(source: str | Path | bytes) -> str:
    if isinstance(source, bytes):
        return source.decode("ascii")
    path = Path(source)
    if path.exists():
        return path.read_text(encoding="ascii")
    return str(source)


def parse_oni(source: str | Path | bytes) -> pd.DataFrame:
    """Parseia ``oni.ascii.txt`` em uma linha por temporada.

    O schema canônico preserva a temperatura total fornecida pela NOAA e a anomalia ONI.
    Falha alto para temporada desconhecida, duplicata ou valor não numérico: uma mudança
    silenciosa no formato da fonte não pode chegar à regressão como dado aparentemente válido.
    """
    text = _load_text(source)
    raw = pd.read_csv(StringIO(text), sep=r"\s+")
    expected = {"SEAS", "YR", "TOTAL", "ANOM"}
    if set(raw.columns) != expected:
        raise ValueError(f"schema ONI inesperado: {list(raw.columns)!r}")
    unknown = sorted(set(raw["SEAS"]) - set(SEASON_CENTER_MONTH))
    if unknown:
        raise ValueError(f"temporadas ONI desconhecidas: {unknown}")

    out = raw.rename(columns={"SEAS": "season", "YR": "year", "TOTAL": "sst_c", "ANOM": "oni_c"})
    out["year"] = pd.to_numeric(out["year"], errors="raise").astype("int64")
    out["sst_c"] = pd.to_numeric(out["sst_c"], errors="raise").astype("float64")
    out["oni_c"] = pd.to_numeric(out["oni_c"], errors="raise").astype("float64")
    month = out["season"].map(SEASON_CENTER_MONTH)
    out["ref_date"] = pd.to_datetime(
        {"year": out["year"], "month": month, "day": 1}
    ) + pd.offsets.MonthEnd(0)
    if out.duplicated(["year", "season"]).any():
        raise ValueError("ONI contém duplicata de (year, season)")
    return out[["ref_date", "season", "year", "sst_c", "oni_c"]].reset_index(drop=True)


def stamp_oni_avail_date(
    df: pd.DataFrame, revision_window_months: int = REVISION_WINDOW_MONTHS
) -> pd.DataFrame:
    """Carimba publicação inicial e disponibilidade conservadora do ONI.

    Para uma temporada centrada em ``t``:

    - ``initial_avail_date`` = dia 5 de ``t + 2 meses`` (fim da janela + publicação);
    - ``avail_date`` = publicação inicial + janela de revisão declarada pela NOAA.

    O caso primário usa dois meses de estabilização. Zero é permitido apenas para análise
    de sensibilidade explícita; valor negativo é erro.
    """
    if revision_window_months < 0:
        raise ValueError("revision_window_months não pode ser negativo")
    out = df.copy()
    ref = pd.to_datetime(out["ref_date"])
    center_start = ref.dt.to_period("M").dt.to_timestamp()
    initial_month = center_start + pd.DateOffset(months=INITIAL_PUBLICATION_MONTHS)
    out["initial_avail_date"] = initial_month + pd.Timedelta(days=PUBLICATION_DAY - 1)
    out["avail_date"] = out["initial_avail_date"] + pd.DateOffset(months=revision_window_months)
    return out


def _write_manifest(content: bytes, stamp: str, manifest_dir: str | Path) -> Path:
    panel = parse_oni(content)
    latest = panel.iloc[-1]
    manifest = {
        "source": "NOAA-CPC-ONI",
        "dataset": "ERSST.v5",
        "url": ONI_URL,
        "methodology_url": ONI_SOURCE_PAGE,
        "latest_season": latest["season"],
        "latest_year": int(latest["year"]),
        "latest_ref_date": latest["ref_date"].date().isoformat(),
        "revision_window_months": REVISION_WINDOW_MONTHS,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "downloaded_at": datetime.now(UTC).isoformat(),
    }
    dest = Path(manifest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"oni_{stamp}.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def download_oni(
    dest_dir: str | Path = "data/raw/oni",
    manifest_dir: str | Path = "data/manifests",
    session=None,
    timeout: int = 60,
) -> Path:
    """Baixa a captura datada do ONI e grava manifesto de vintage.

    A URL é sobrescrita pela NOAA. O cache é por dia de captura: nunca rebaixa no mesmo dia,
    mas uma captura futura gera outro arquivo e outro hash para permitir medir revisões.
    """
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"oni_{stamp}.txt"
    if out.exists():
        return out
    if session is None:
        import requests

        session = requests
    response = session.get(ONI_URL, timeout=timeout)
    response.raise_for_status()
    content = response.content
    parse_oni(content)  # valida antes de persistir um arquivo aparentemente bem-sucedido
    out.write_bytes(content)
    _write_manifest(content, stamp, manifest_dir)
    return out
