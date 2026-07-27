"""Contrato return-agnóstico da geografia placebo H5 (D-070).

O H5 troca somente o suporte espacial do ``Shock`` de grãos. Calendário, janelas
fenológicas, climatologia expanding, pesos CONAB, exposições, direção H′, sizing e custos
permanecem os mesmos. Os cinco municípios costeiros abaixo foram congelados antes de calcular
qualquer choque placebo e têm produção PAM observada igual a zero para soja e milho total em
todos os anos de 2014–2024.

A agregação é uma média por célula CHIRPS: a precipitação média de cada município recebe peso
igual ao número fixo de centros de célula dentro do polígono IBGE 2013. Isso reproduz a média
das 91 células sem usar produção como peso e sem escolher coordenadas depois do resultado.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

H5_PAM_AUDIT_YEARS: tuple[int, ...] = tuple(range(2014, 2025))
H5_PAM_CROPS: tuple[str, ...] = ("soy", "corn_total")
H5_SPATIAL_AGGREGATION = "equal_chirps_grid_cell"
H5_WINDOW_POLICY = "reuse_primary_crop_uf_windows"
H5_NATIONAL_WEIGHT_POLICY = "reuse_previous_completed_conab_uf_weights"


@dataclass(frozen=True)
class PlaceboMunicipality:
    """Município costeiro e número de células na malha CHIRPS/IBGE congelada."""

    municipality_code: str
    municipality_name: str
    uf: str
    n_cells: int


H5_PLACEBO_MUNICIPALITIES: tuple[PlaceboMunicipality, ...] = (
    PlaceboMunicipality("2906303", "Canavieiras", "BA", 46),
    PlaceboMunicipality("2920700", "Maraú", "BA", 27),
    PlaceboMunicipality("2927309", "Salinas da Margarida", "BA", 5),
    PlaceboMunicipality("4115705", "Matinhos", "PR", 4),
    PlaceboMunicipality("4119954", "Pontal do Paraná", "PR", 9),
)
H5_PLACEBO_CODES: tuple[str, ...] = tuple(
    municipality.municipality_code for municipality in H5_PLACEBO_MUNICIPALITIES
)
H5_TOTAL_CELLS = 91


def validate_h5_geography_spec() -> None:
    """Tripwires contra alteração silenciosa da geografia pré-materialização."""
    if len(H5_PLACEBO_MUNICIPALITIES) != 5 or len(set(H5_PLACEBO_CODES)) != 5:
        raise ValueError("H5 exige exatamente cinco municípios placebo distintos")
    if {municipality.uf for municipality in H5_PLACEBO_MUNICIPALITIES} != {"BA", "PR"}:
        raise ValueError("H5 deve preservar as duas faixas costeiras BA/PR")
    if any(
        len(municipality.municipality_code) != 7
        or not municipality.municipality_code.isdigit()
        or municipality.n_cells <= 0
        for municipality in H5_PLACEBO_MUNICIPALITIES
    ):
        raise ValueError("código municipal ou contagem de células H5 inválidos")
    if sum(municipality.n_cells for municipality in H5_PLACEBO_MUNICIPALITIES) != H5_TOTAL_CELLS:
        raise ValueError("contagem total de células H5 foi alterada")
    if H5_PAM_AUDIT_YEARS != tuple(range(2014, 2025)):
        raise ValueError("janela de auditoria PAM H5 foi alterada")
    if H5_PAM_CROPS != ("soy", "corn_total"):
        raise ValueError("culturas da auditoria H5 foram alteradas")
    if (
        H5_SPATIAL_AGGREGATION != "equal_chirps_grid_cell"
        or H5_WINDOW_POLICY != "reuse_primary_crop_uf_windows"
        or H5_NATIONAL_WEIGHT_POLICY != "reuse_previous_completed_conab_uf_weights"
    ):
        raise ValueError("transformação geográfica H5 foi alterada")


def audit_zero_grain_production(
    pam: pd.DataFrame,
    *,
    years: tuple[int, ...] = H5_PAM_AUDIT_YEARS,
) -> pd.DataFrame:
    """Prova cobertura completa e produção zero no suporte placebo.

    ``years`` é parametrizável apenas para fixtures; a materialização usa o default congelado.
    """
    required = {
        "ref_year",
        "crop",
        "uf",
        "municipality_code",
        "municipality_name",
        "quantity_tonnes",
    }
    missing = required - set(pam.columns)
    if missing:
        raise ValueError(f"PAM H5 sem colunas: {sorted(missing)}")
    selected = pam[
        pam["municipality_code"].isin(H5_PLACEBO_CODES)
        & pam["crop"].isin(H5_PAM_CROPS)
        & pam["ref_year"].isin(years)
    ].copy()
    key = ["ref_year", "crop", "municipality_code"]
    if selected.duplicated(key).any():
        raise ValueError("PAM H5 contém duplicata município×cultura×ano")
    expected = len(years) * len(H5_PAM_CROPS) * len(H5_PLACEBO_CODES)
    if len(selected) != expected:
        raise ValueError(f"PAM H5 incompleta: esperado {expected}, veio {len(selected)}")
    quantity = pd.to_numeric(selected["quantity_tonnes"], errors="raise").astype("float64")
    if not np.isfinite(quantity).all() or not quantity.eq(0.0).all():
        bad = selected.loc[~quantity.eq(0.0), ["ref_year", "crop", "municipality_code"]]
        raise ValueError(
            f"município H5 tem produção de grão positiva/ausente: {bad.to_dict('records')}"
        )

    identity = {
        municipality.municipality_code: (municipality.municipality_name, municipality.uf)
        for municipality in H5_PLACEBO_MUNICIPALITIES
    }
    for code, (name, uf) in identity.items():
        rows = selected[selected["municipality_code"] == code]
        if set(rows["municipality_name"]) != {name} or set(rows["uf"]) != {uf}:
            raise ValueError(f"identidade PAM diverge do contrato H5 para {code}")
    return (
        selected.groupby(["municipality_code", "municipality_name", "uf", "crop"], as_index=False)
        .agg(
            first_ref_year=("ref_year", "min"),
            last_ref_year=("ref_year", "max"),
            observations=("ref_year", "size"),
            total_tonnes=("quantity_tonnes", "sum"),
            max_tonnes=("quantity_tonnes", "max"),
        )
        .sort_values(["municipality_code", "crop"])
        .reset_index(drop=True)
    )


validate_h5_geography_spec()
