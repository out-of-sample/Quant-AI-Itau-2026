"""Calendário point-in-time da Produção Agrícola Municipal (PAM/IBGE).

A tabela 1612 do SIDRA informa o ano civil de referência, mas não carrega a data em que cada
edição ficou pública. Este módulo mantém esse segundo relógio explicitamente. As datas abaixo
foram verificadas em calendários ou releases oficiais do IBGE; não há interpolação pela regra
"setembro do ano seguinte".

O calendário começa em 2014 porque a primeira janela operacional do sinal é a safra 2015/16.
Em 01/12/2015, quando essa janela começa, a PAM 2014 já estava pública desde 05/11/2015.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PamRelease:
    """Data efetiva de divulgação de uma edição anual e sua prova oficial."""

    ref_year: int
    avail_date: pd.Timestamp
    source_url: str


_IBGE_CALENDAR = "https://www.ibge.gov.br/calendario/mensal.html"
_IBGE_NEWS = "https://agenciadenoticias.ibge.gov.br"

PAM_RELEASES: dict[int, PamRelease] = {
    2014: PamRelease(
        2014,
        pd.Timestamp("2015-11-05"),
        f"{_IBGE_NEWS}/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/"
        "9688-pam-2014-recorde-de-producao-da-soja-impulsiona-agricultura",
    ),
    2015: PamRelease(
        2015,
        pd.Timestamp("2016-09-23"),
        f"{_IBGE_NEWS}/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/"
        "9812-pesquisa-agricola-municipal-recordes-de-producao-de-soja-e-milho-"
        "impulsionam-agricultura-em-2015",
    ),
    2016: PamRelease(
        2016,
        pd.Timestamp("2017-09-21"),
        f"{_IBGE_NEWS}/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/"
        "16814-pam-2016-valor-da-producao-agricola-nacional-foi-20-maior-do-que-em-2015",
    ),
    2017: PamRelease(
        2017,
        pd.Timestamp("2018-09-13"),
        f"{_IBGE_CALENDAR}?ano=2018&mes=9",
    ),
    2018: PamRelease(
        2018,
        pd.Timestamp("2019-09-05"),
        f"{_IBGE_CALENDAR}?ano=2019&mes=9",
    ),
    2019: PamRelease(
        2019,
        pd.Timestamp("2020-10-01"),
        f"{_IBGE_CALENDAR}?ano=2020&mes=10",
    ),
    2020: PamRelease(
        2020,
        pd.Timestamp("2021-09-22"),
        f"{_IBGE_CALENDAR}?ano=2021&mes=9",
    ),
    2021: PamRelease(
        2021,
        pd.Timestamp("2022-09-15"),
        f"{_IBGE_CALENDAR}?ano=2022&mes=9",
    ),
    2022: PamRelease(
        2022,
        pd.Timestamp("2023-09-14"),
        f"{_IBGE_CALENDAR}?ano=2023&mes=9",
    ),
    2023: PamRelease(
        2023,
        pd.Timestamp("2024-09-12"),
        f"{_IBGE_CALENDAR}?ano=2024&mes=9",
    ),
    2024: PamRelease(
        2024,
        pd.Timestamp("2025-09-11"),
        f"{_IBGE_CALENDAR}?ano=2025&mes=9",
    ),
}


def pam_release(ref_year: int) -> PamRelease:
    """Retorna a divulgação verificada; ano sem prova falha alto."""
    try:
        return PAM_RELEASES[int(ref_year)]
    except (KeyError, ValueError) as exc:
        raise KeyError(f"ano PAM sem data oficial curada: {ref_year!r}") from exc


def pam_avail_map() -> pd.Series:
    """Mapa ``31/12 do ano de referência → data efetiva de divulgação``."""
    return pd.Series(
        {pd.Timestamp(year, 12, 31): release.avail_date for year, release in PAM_RELEASES.items()},
        dtype="datetime64[us]",
        name="avail_date",
    )
