"""Especificação congelada do choque climático primário (D-023).

Este módulo define *antes de observar retornos* quais culturas, UFs, janelas fenológicas e
canal climático pertencem ao teste primário. Ele não calcula o ``Shock``: é o contrato que a
implementação posterior deve obedecer.

Escolhas primárias:

- culturas: soja e milho 2ª safra;
- canal: déficit de precipitação CHIRPS (``stress = -z(precipitação acumulada)``);
- suporte regional fixo: UFs que, no 12º levantamento CONAB 2024/25, formavam o menor
  conjunto acima de 80% da produção nacional de cada cultura;
- janelas críticas: calendário CONAB, ZARC/MAPA e fisiologia Embrapa, documentados em
  ``docs/09_FENOLOGIA_E_LIMIARES.md``;
- geografia operacional: média climática municipal ponderada pela PAM/IBGE mais recente já
  publicada; agregação nacional com pesos da safra CONAB anterior já encerrada.

Temperatura POWER, caixas retangulares, outras culturas e deslocamentos de janela são testes
secundários. Promovê-los ao caso primário exige nova decisão versionada — nunca uma escolha
depois de olhar Sharpe ou retorno.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass

import pandas as pd

PRIMARY_CLIMATE_CHANNEL = "chirps_precip_deficit"
PRIMARY_SIGNAL_KIND = "prelim"
CLIMATOLOGY_KIND = "final"
FIRST_COMPLETE_CROP_YEAR = "2015/16"
PRECIP_Z_TO_STRESS = -1.0
MIN_EXPANDING_YEARS = 10
EXPANDING_STD_DDOF = 1


@dataclass(frozen=True)
class RegionalizationSpec:
    """Contrato da ponderação espacial, sem coordenadas escolhidas manualmente."""

    spatial_unit: str = "municipio_ibge"
    climate_aggregation: str = "municipality_polygon_mean"
    within_uf_weight_source: str = "IBGE_PAM_1612"
    national_weight_source: str = "CONAB_previous_completed_crop"
    pam_availability_rule: str = "official_release_date"


REGIONALIZATION = RegionalizationSpec()


@dataclass(frozen=True)
class CropRegionWindow:
    """Janela crítica de uma cultura/UF em relação ao início do ano-safra.

    ``start_year_offset`` e ``end_year_offset`` são somados ao primeiro ano de uma safra
    ``AAAA/AA``. ``end_day=None`` significa o último dia do mês, inclusive em ano bissexto.
    """

    crop: str
    conab_product: str
    conab_season: str
    uf: str
    phase: str
    start_month: int
    start_day: int
    start_year_offset: int
    end_month: int
    end_day: int | None
    end_year_offset: int

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Z]{2}", self.uf):
            raise ValueError(f"UF inválida: {self.uf!r}")
        if self.start_year_offset not in (-1, 0, 1) or self.end_year_offset not in (-1, 0, 1):
            raise ValueError("offset do ano-safra deve ser -1, 0 ou 1")
        # Datas não-bissextas bastam para validar mês/dia; fim de fevereiro usa None.
        pd.Timestamp(2001, self.start_month, self.start_day)
        if self.end_day is not None:
            pd.Timestamp(2001, self.end_month, self.end_day)

    @property
    def key(self) -> tuple[str, str]:
        """Identificador único ``(crop, UF)``."""
        return self.crop, self.uf


PRIMARY_WINDOWS: tuple[CropRegionWindow, ...] = (
    # Soja: MT/GO/PR/MS/MG compartilham dez–fev; RS e BA são mais tardios.
    CropRegionWindow("soy", "SOJA", "UNICA", "MT", "R1-R6", 12, 1, 0, 2, None, 1),
    CropRegionWindow("soy", "SOJA", "UNICA", "GO", "R1-R6", 12, 1, 0, 2, None, 1),
    CropRegionWindow("soy", "SOJA", "UNICA", "PR", "R1-R6", 12, 1, 0, 2, None, 1),
    CropRegionWindow("soy", "SOJA", "UNICA", "MS", "R1-R6", 12, 1, 0, 2, None, 1),
    CropRegionWindow("soy", "SOJA", "UNICA", "MG", "R1-R6", 12, 1, 0, 2, None, 1),
    CropRegionWindow("soy", "SOJA", "UNICA", "RS", "R1-R6", 1, 1, 1, 3, 31, 1),
    CropRegionWindow("soy", "SOJA", "UNICA", "BA", "R1-R6", 1, 1, 1, 3, 31, 1),
    # Milho 2ª: janela estreita de pré-floração a início do enchimento de grãos.
    CropRegionWindow(
        "corn_second", "MILHO", "2ª SAFRA", "MT", "flowering_grain_fill", 3, 15, 1, 5, 15, 1
    ),
    CropRegionWindow(
        "corn_second", "MILHO", "2ª SAFRA", "GO", "flowering_grain_fill", 3, 15, 1, 4, 30, 1
    ),
    CropRegionWindow(
        "corn_second", "MILHO", "2ª SAFRA", "PR", "flowering_grain_fill", 4, 1, 1, 5, 31, 1
    ),
    CropRegionWindow(
        "corn_second", "MILHO", "2ª SAFRA", "MS", "flowering_grain_fill", 4, 1, 1, 5, 31, 1
    ),
)

# Canal de expansão — algodão (D-046/D-047). Contrato à parte do primário de grãos, mesmo
# mecanismo (preço global, seca prejudica o produtor sob H′). Suporte mínimo >80%: MT+BA
# (MT ~68%, BA ~17% da produção 2023/24). Fase crítica hídrica = floração + formação do capulho
# (~60-100 dias após a emergência; 50-60% da necessidade hídrica), fonte MAPA/ZARC + Embrapa.
# Plantio MT ~jan-fev (após a soja) ⇒ janela mar-mai; BA ~dez-jan ⇒ janela fev-abr. Ambos no
# ano base+1. CONAB: "ALGODAO EM PLUMA", safra "UNICA".
COTTON_WINDOWS: tuple[CropRegionWindow, ...] = (
    CropRegionWindow(
        "cotton", "ALGODAO EM PLUMA", "UNICA", "MT", "flowering_boll", 3, 15, 1, 5, 31, 1
    ),
    CropRegionWindow(
        "cotton", "ALGODAO EM PLUMA", "UNICA", "BA", "flowering_boll", 2, 1, 1, 4, 30, 1
    ),
)

# Canal de expansão — cana (D-046/D-050). Os dois contratos nunca são combinados: seca no
# crescimento é adversa à tonelagem, enquanto seca na maturação pode favorecer ATR. O suporte
# SP+MG+GO+MS+PR cobre 87,8% da produção CONAB 2024/25.
_CANE_UFS = ("SP", "MG", "GO", "MS", "PR")
CANE_GROWTH_WINDOWS: tuple[CropRegionWindow, ...] = tuple(
    CropRegionWindow(
        "sugarcane", "CANA DE ACUCAR", "UNICA", uf, "vegetative_growth", 12, 1, -1, 2, None, 0
    )
    for uf in _CANE_UFS
)
CANE_MATURATION_WINDOWS: tuple[CropRegionWindow, ...] = tuple(
    CropRegionWindow("sugarcane", "CANA DE ACUCAR", "UNICA", uf, "maturation", 6, 1, 0, 8, None, 0)
    for uf in _CANE_UFS
)

ALL_WINDOWS: tuple[CropRegionWindow, ...] = PRIMARY_WINDOWS + COTTON_WINDOWS


def crop_year_start(ano_agricola: str) -> int:
    """Extrai o primeiro ano de ``AAAA/AA`` e falha alto em formatos ambíguos."""
    match = re.fullmatch(r"(\d{4})/(\d{2})", str(ano_agricola))
    if match is None:
        raise ValueError(f"ano_agricola fora do formato AAAA/AA: {ano_agricola!r}")
    start = int(match.group(1))
    if int(match.group(2)) != (start + 1) % 100:
        raise ValueError(f"ano_agricola inconsistente: {ano_agricola!r}")
    return start


def critical_period(spec: CropRegionWindow, ano_agricola: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Materializa a janela inclusiva da especificação para um ano-safra."""
    base = crop_year_start(ano_agricola)
    start_year = base + spec.start_year_offset
    end_year = base + spec.end_year_offset
    end_day = spec.end_day or calendar.monthrange(end_year, spec.end_month)[1]
    start = pd.Timestamp(start_year, spec.start_month, spec.start_day)
    end = pd.Timestamp(end_year, spec.end_month, end_day)
    if end < start:
        raise ValueError(f"janela invertida para {spec.key}: {start.date()} > {end.date()}")
    return start, end


def windows_for_crop(crop: str) -> tuple[CropRegionWindow, ...]:
    """Retorna as janelas da cultura (grão primário ou algodão), falhando fora do pré-registro."""
    out = tuple(spec for spec in ALL_WINDOWS if spec.crop == crop)
    if not out:
        raise KeyError(f"cultura fora da especificação: {crop!r}")
    return out


def cane_windows(phase: str) -> tuple[CropRegionWindow, ...]:
    """Contrato da cana por fase; misturar fases de sinais opostos é proibido (D-050)."""
    if phase == "growth":
        return CANE_GROWTH_WINDOWS
    if phase == "maturation":
        return CANE_MATURATION_WINDOWS
    raise KeyError(f"fase da cana fora do pré-registro: {phase!r}")


def validate_primary_spec() -> None:
    """Tripwires contra duplicata ou mudança silenciosa dos contratos congelados."""
    keys = [spec.key for spec in ALL_WINDOWS]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicata (cultura, UF) na especificação")
    for spec in ALL_WINDOWS:
        critical_period(spec, "2023/24")
    for windows in (CANE_GROWTH_WINDOWS, CANE_MATURATION_WINDOWS):
        keys = [spec.key for spec in windows]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicata (cultura, UF) no contrato da cana")
        for spec in windows:
            critical_period(spec, "2023/24")


validate_primary_spec()
