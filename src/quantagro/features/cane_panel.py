"""Datas mensais CHIRPS exigidas pelo contrato de cana D-050."""

from __future__ import annotations

import pandas as pd

from .panel import CLIMATOLOGY_FIRST_YEAR
from .shock_spec import CANE_GROWTH_WINDOWS, CANE_MATURATION_WINDOWS, critical_period

CANE_BASE_YEARS: tuple[int, ...] = tuple(range(2018, 2026))


def phase_months(spec, base_year: int) -> pd.DatetimeIndex:
    """Fins dos meses civis completos da fase em um ano-safra."""
    ano = f"{base_year}/{(base_year + 1) % 100:02d}"
    start, end = critical_period(spec, ano)
    return pd.date_range(start, end, freq="ME")


def required_cane_monthly_files(
    signal_bases: tuple[int, ...] = CANE_BASE_YEARS,
    climatology_first_year: int = CLIMATOLOGY_FIRST_YEAR,
) -> pd.DataFrame:
    """Pares mensais prelim/final necessários, sem baixar meses fora das duas fases."""
    if not signal_bases:
        raise ValueError("signal_bases não pode ser vazio")
    specs = (CANE_GROWTH_WINDOWS[0], CANE_MATURATION_WINDOWS[0])
    rows: list[tuple[pd.Timestamp, str]] = []
    for base in signal_bases:
        for spec in specs:
            rows.extend((d, "prelim") for d in phase_months(spec, base))
    for base in range(climatology_first_year, max(signal_bases)):
        for spec in specs:
            rows.extend((d, "final") for d in phase_months(spec, base))
    return (
        pd.DataFrame(rows, columns=["ref_date", "kind"])
        .drop_duplicates()
        .sort_values(["kind", "ref_date"])
        .reset_index(drop=True)
    )
