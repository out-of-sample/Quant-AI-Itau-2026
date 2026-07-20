"""Contrato mensal do CHIRPS para a cana (D-050)."""

import pandas as pd

from quantagro.features.cane_panel import phase_months, required_cane_monthly_files
from quantagro.features.shock_spec import CANE_GROWTH_WINDOWS, CANE_MATURATION_WINDOWS


def test_meses_das_duas_fases_nao_se_sobrepoem():
    growth = phase_months(CANE_GROWTH_WINDOWS[0], 2024)
    maturation = phase_months(CANE_MATURATION_WINDOWS[0], 2024)
    assert growth.tolist() == [
        pd.Timestamp("2023-12-31"),
        pd.Timestamp("2024-01-31"),
        pd.Timestamp("2024-02-29"),
    ]
    assert maturation.tolist() == [
        pd.Timestamp("2024-06-30"),
        pd.Timestamp("2024-07-31"),
        pd.Timestamp("2024-08-31"),
    ]
    assert growth.intersection(maturation).empty


def test_lista_mensal_eh_deduplicada_e_preserva_vintage():
    required = required_cane_monthly_files(signal_bases=(2018, 2019), climatology_first_year=2000)
    assert not required.duplicated(["ref_date", "kind"]).any()
    assert set(required["kind"]) == {"prelim", "final"}
    assert required.query("kind == 'prelim'")["ref_date"].min() == pd.Timestamp("2017-12-31")
