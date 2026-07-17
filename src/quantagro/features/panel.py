"""Construção do painel municipal diário de precipitação para os rodadores de H1.

Duas peças, separadas por custo (mesma lógica de ``regionalize.py``):

- **Índice de células** (``build_cell_index``): caro e independente do tempo — o mapa
  município→células da grade CHIRPS. Calculado uma vez e cacheado; reusado por todos os
  rasters.
- **Datas necessárias** (``required_files``): dado o conjunto primário de janelas
  (``shock_spec.PRIMARY_WINDOWS``), enumera exatamente os pares ``(ref_date, kind)`` que o
  ``Shock`` primário consome — o sinal ``prelim`` das safras operacionais e a climatologia
  ``final`` dos anos anteriores. Fora dessas janelas nenhum raster é baixado.

O laço de download em si (rede, retry, flush incremental) vive em
``scripts/build_municipal_panel.py``: baixa cada raster em memória, regionaliza com o índice
e descarta — o painel municipal (poucos MB) é o registro de resumo e de resiliência.
"""

from __future__ import annotations

import pandas as pd

from ..ingest.chirps import read_chirps_grid
from .regionalize import municipality_cell_index
from .shock_spec import PRIMARY_WINDOWS, critical_period

# climatology_first_year primário: a climatologia expanding começa em 2000. A densidade de
# estações do CHIRPS no Brasil melhora sensivelmente a partir de ~2000 (antes é mais
# satélite-only); ancorar aqui dá à safra 2015/16 uma base de 15 anos, folga confortável
# sobre o mínimo de 10 (D-023). Escolha justificada por qualidade de dado, não por resultado
# (D-030) — congelada antes de qualquer ajuste.
CLIMATOLOGY_FIRST_YEAR: int = 2000

# Safras operacionais do sinal: o CHIRPS prelim começa em 2015 e a primeira safra completa é
# 2015/16 (R16); a última com janela encerrada em 2026 é 2024/25. bases = primeiro ano.
SIGNAL_BASE_YEARS: tuple[int, ...] = tuple(range(2015, 2025))


def union_window(base_year: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Menor início e maior fim entre todas as janelas primárias do ano-safra ``base_year``.

    As janelas cultura×UF são contíguas o suficiente para que a união seja um intervalo só
    (soja dez→mar; milho 2ª mar→mai): [min start, max end] cobre todas sem buraco.
    """
    ano = f"{base_year}/{(base_year + 1) % 100:02d}"
    bounds = [critical_period(spec, ano) for spec in PRIMARY_WINDOWS]
    return min(s for s, _ in bounds), max(e for _, e in bounds)


def window_dates(base_year: int) -> pd.DatetimeIndex:
    """Datas diárias (inclusivas) da janela-união do ano-safra ``base_year``."""
    start, end = union_window(base_year)
    return pd.date_range(start, end, freq="D")


def required_files(
    signal_bases: tuple[int, ...] = SIGNAL_BASE_YEARS,
    climatology_first_year: int = CLIMATOLOGY_FIRST_YEAR,
) -> pd.DataFrame:
    """Pares ``(ref_date, kind)`` que o ``Shock`` primário consome, sem duplicatas.

    - ``prelim`` (sinal): janela-união de cada safra operacional em ``signal_bases``.
    - ``final`` (climatologia): janela-união de cada ano anterior usado como climatologia
      expanding — de ``climatology_first_year`` ao último ``base - 1``. Como a climatologia é
      expanding, a união dos anos necessários é ``[climatology_first_year, max(signal_bases) - 1]``.
    """
    rows: list[tuple[pd.Timestamp, str]] = []
    for base in signal_bases:
        for d in window_dates(base):
            rows.append((d, "prelim"))
    clim_years = range(climatology_first_year, max(signal_bases))
    for year in clim_years:
        for d in window_dates(year):
            rows.append((d, "final"))
    out = pd.DataFrame(rows, columns=["ref_date", "kind"])
    return out.drop_duplicates().sort_values(["kind", "ref_date"]).reset_index(drop=True)


def build_cell_index(geometry: pd.DataFrame, sample_source) -> pd.DataFrame:
    """Índice município→células a partir da malha e de um raster CHIRPS de referência.

    ``geometry`` é a concatenação das 7 UFs (``ibge_geometry.parse_geometry``);
    ``sample_source`` é um GeoTIFF CHIRPS (caminho ou bytes) que fixa a grade — o índice só
    vale para essa grade e ``municipal_daily_precip`` recusa qualquer raster incompatível.
    """
    arr, gt = read_chirps_grid(sample_source)
    n_rows, n_cols = arr.shape
    return municipality_cell_index(geometry, gt, n_rows, n_cols)
