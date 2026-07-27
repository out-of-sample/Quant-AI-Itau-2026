"""Contrato congelado da geografia placebo H5 (D-070)."""

from pathlib import Path

import pandas as pd
import pytest

from quantagro.robustness.h5_geography_spec import (
    H5_PLACEBO_CODES,
    H5_PLACEBO_MUNICIPALITIES,
    H5_TOTAL_CELLS,
    audit_placebo_cell_index,
    audit_zero_grain_production,
    validate_h5_geography_spec,
)

FIXTURE = Path(__file__).parent / "fixtures" / "h5_pam_zero_2024.csv"


def test_geografia_h5_fixa_cinco_municipios_e_91_celulas() -> None:
    validate_h5_geography_spec()
    assert H5_PLACEBO_CODES == ("2906303", "2920700", "2927309", "4115705", "4119954")
    assert sum(item.n_cells for item in H5_PLACEBO_MUNICIPALITIES) == H5_TOTAL_CELLS == 91


def test_fixture_pam_oficial_prova_zero_nas_duas_culturas() -> None:
    pam = pd.read_csv(FIXTURE, dtype={"municipality_code": str})
    audit = audit_zero_grain_production(pam, years=(2024,))
    assert len(audit) == 10
    assert audit["observations"].eq(1).all()
    assert audit["total_tonnes"].eq(0).all()
    assert audit["max_tonnes"].eq(0).all()


def test_auditoria_rejeita_cobertura_incompleta_e_producao_positiva() -> None:
    pam = pd.read_csv(FIXTURE, dtype={"municipality_code": str})
    with pytest.raises(ValueError, match="incompleta"):
        audit_zero_grain_production(pam.iloc[:-1], years=(2024,))
    pam.loc[0, "quantity_tonnes"] = 1.0
    with pytest.raises(ValueError, match="produção"):
        audit_zero_grain_production(pam, years=(2024,))


def test_auditoria_rejeita_identidade_municipal_divergente() -> None:
    pam = pd.read_csv(FIXTURE, dtype={"municipality_code": str})
    pam.loc[pam["municipality_code"].eq("2906303"), "municipality_name"] = "Outro"
    with pytest.raises(ValueError, match="identidade PAM"):
        audit_zero_grain_production(pam, years=(2024,))


def test_indice_de_celulas_exige_contagens_congeladas() -> None:
    rows = []
    for municipality in H5_PLACEBO_MUNICIPALITIES:
        rows.extend(
            {
                "municipality_code": municipality.municipality_code,
                "uf": municipality.uf,
                "row": i,
                "col": i + 100,
            }
            for i in range(municipality.n_cells)
        )
    index = pd.DataFrame(rows)
    audit = audit_placebo_cell_index(index)
    assert audit["n_cells"].sum() == 91
    with pytest.raises(ValueError, match="diverge"):
        audit_placebo_cell_index(index.iloc[:-1])
