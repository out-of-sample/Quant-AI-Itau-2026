"""Invariantes da especificação climática congelada antes de observar retornos (D-023)."""

import pandas as pd
import pytest

from quantagro.features.shock_spec import (
    CLIMATOLOGY_KIND,
    COTTON_WINDOWS,
    EXPANDING_STD_DDOF,
    FIRST_COMPLETE_CROP_YEAR,
    MIN_EXPANDING_YEARS,
    PRECIP_Z_TO_STRESS,
    PRIMARY_CLIMATE_CHANNEL,
    PRIMARY_SIGNAL_KIND,
    PRIMARY_WINDOWS,
    REGIONALIZATION,
    critical_period,
    crop_year_start,
    windows_for_crop,
)


def test_escopo_primario_tem_apenas_soja_e_milho_segunda_safra():
    assert {spec.crop for spec in PRIMARY_WINDOWS} == {"soy", "corn_second"}
    assert {spec.uf for spec in windows_for_crop("soy")} == {
        "MT",
        "GO",
        "PR",
        "RS",
        "MS",
        "MG",
        "BA",
    }
    assert {spec.uf for spec in windows_for_crop("corn_second")} == {"MT", "PR", "GO", "MS"}


def test_canal_primario_e_convencao_de_estresse():
    assert PRIMARY_CLIMATE_CHANNEL == "chirps_precip_deficit"
    assert PRIMARY_SIGNAL_KIND == "prelim"
    assert CLIMATOLOGY_KIND == "final"
    assert FIRST_COMPLETE_CROP_YEAR == "2015/16"
    assert PRECIP_Z_TO_STRESS == -1.0  # chuva abaixo da média → Shock positivo
    assert MIN_EXPANDING_YEARS == 10
    assert EXPANDING_STD_DDOF == 1


def test_geografia_nao_depende_das_caixas_ilustrativas():
    assert REGIONALIZATION.spatial_unit == "municipio_ibge"
    assert REGIONALIZATION.climate_aggregation == "municipality_polygon_mean"
    assert REGIONALIZATION.within_uf_weight_source == "IBGE_PAM_1612"
    assert REGIONALIZATION.national_weight_source == "CONAB_previous_completed_crop"
    assert REGIONALIZATION.pam_availability_rule == "official_release_date"


def test_soja_mt_cruza_o_ano_safra_e_inclui_fevereiro_bissexto():
    mt = next(s for s in windows_for_crop("soy") if s.uf == "MT")
    assert critical_period(mt, "2023/24") == (
        pd.Timestamp("2023-12-01"),
        pd.Timestamp("2024-02-29"),
    )


def test_soja_rs_eh_um_mes_mais_tardia():
    rs = next(s for s in windows_for_crop("soy") if s.uf == "RS")
    assert critical_period(rs, "2023/24") == (
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-03-31"),
    )


def test_milho_segunda_safra_mt_tem_janela_estreita():
    mt = next(s for s in windows_for_crop("corn_second") if s.uf == "MT")
    assert critical_period(mt, "2023/24") == (
        pd.Timestamp("2024-03-15"),
        pd.Timestamp("2024-05-15"),
    )


@pytest.mark.parametrize("bad", ["2024", "23/24", "2023/25", "2023-24", ""])
def test_ano_agricola_ambiguo_falha_alto(bad):
    with pytest.raises(ValueError, match="ano_agricola"):
        crop_year_start(bad)


def test_cultura_fora_do_primario_falha_alto():
    with pytest.raises(KeyError, match="fora da especificação"):
        windows_for_crop("coffee")


def test_contrato_algodao_congelado():
    """Trava o contrato do algodão (D-047): MT+BA, janela floração/capulho, ano base+1."""
    specs = {s.uf: s for s in windows_for_crop("cotton")}
    assert set(specs) == {"MT", "BA"}
    assert len(COTTON_WINDOWS) == 2
    for s in COTTON_WINDOWS:
        assert s.conab_product == "ALGODAO EM PLUMA"
        assert s.conab_season == "UNICA"
        assert s.start_year_offset == 1 and s.end_year_offset == 1
    # MT: 15/03–31/05 do ano base+1; BA: 01/02–30/04
    mt_i, mt_f = critical_period(specs["MT"], "2023/24")
    ba_i, ba_f = critical_period(specs["BA"], "2023/24")
    assert (mt_i.month, mt_i.day, mt_i.year) == (3, 15, 2024)
    assert (mt_f.month, mt_f.day) == (5, 31)
    assert (ba_i.month, ba_i.day) == (2, 1)
    assert (ba_f.month, ba_f.day) == (4, 30)


def test_chaves_cultura_uf_sao_unicas():
    keys = [spec.key for spec in PRIMARY_WINDOWS]
    assert len(keys) == len(set(keys))
