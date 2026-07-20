"""Contrato mensal do CHIRPS para a cana (D-050)."""

import pandas as pd
import pytest

from quantagro.features.cane_panel import phase_months, required_cane_monthly_files
from quantagro.features.cane_shock import stamp_cane_monthly_panel, uf_cane_shock_asof
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


def _synthetic_monthly():
    spec = CANE_MATURATION_WINDOWS[0]  # SP
    rows = []
    for base in range(2000, 2018):
        for date in phase_months(spec, base):
            rows.append(
                {
                    "ref_date": date,
                    "kind": "final",
                    "uf": "SP",
                    "municipality_code": "3500105",
                    "precip_mm": 80.0 + base - 2000,
                }
            )
    for date in phase_months(spec, 2018):
        rows.append(
            {
                "ref_date": date,
                "kind": "prelim",
                "uf": "SP",
                "municipality_code": "3500105",
                "precip_mm": 50.0,
            }
        )
    return stamp_cane_monthly_panel(pd.DataFrame(rows))


def _synthetic_pam():
    return pd.DataFrame(
        {
            "ref_date": [pd.Timestamp("2016-12-31")],
            "avail_date": [pd.Timestamp("2017-09-21")],
            "ref_year": [2016],
            "crop": ["sugarcane"],
            "uf": ["SP"],
            "municipality_code": ["3500105"],
            "municipality_name": ["Adamantina"],
            "quantity_tonnes": [100.0],
            "value_status": ["observed"],
        }
    )


def test_shock_mensal_respeita_prefixo_visivel_e_climatologia_expanding():
    spec = CANE_MATURATION_WINDOWS[0]
    partial = uf_cane_shock_asof(
        "2018-08-05", "2018/19", spec, _synthetic_monthly(), _synthetic_pam(), 2000
    )
    full = uf_cane_shock_asof(
        "2018-10-31", "2018/19", spec, _synthetic_monthly(), _synthetic_pam(), 2000
    )
    assert partial["months_seen"] == 1  # julho só fica visível em 07/08
    assert full["months_seen"] == 3
    assert full["n_clim_years"] == 18
    assert full["shock"] > 0  # mês corrente mais seco que toda a climatologia


def test_ausencia_de_mes_ja_publicavel_falha_em_vez_de_parecer_janela_nao_iniciada():
    spec = CANE_MATURATION_WINDOWS[0]
    empty = _synthetic_monthly().query("not (kind == 'prelim' and uf == 'SP')")
    with pytest.raises(ValueError, match="primeiro mês já esperado"):
        uf_cane_shock_asof("2018-07-10", "2018/19", spec, empty, _synthetic_pam(), 2000)
