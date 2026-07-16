"""Carimbo point-in-time: `ref_date` + regra de latência → `avail_date`.

Este é o utilitário canônico do invariante do projeto (docs/03_ARQUITETURA.md §0): toda
tabela carrega `ref_date` (a que dia o dado se refere) e `avail_date` (quando ficou público),
e **toda leitura a jusante filtra por `avail_date`** — nunca por `ref_date`. Centralizar o
carimbo e o filtro aqui evita que cada camada reimplemente (e erre) a regra.

A regra de latência é responsabilidade de quem conhece a fonte (docs/02_DADOS.md §6):
COTAHIST = fim do próprio pregão (lag 0 — e a regra de execução em D+1 do protocolo cobre a
sutileza intradiária); CHIRPS = 7 dias corridos (caso primário congelado em 01_TESE §5);
ComexStat = calendário oficial de divulgação. Fontes com calendário irregular passam um
mapeamento explícito em vez de lag fixo — **nunca interpolar** (R10).

O carimbo NÃO resolve o problema de *vintage* (fonte que reescreve o passado): isso é
propriedade da fonte e está tratado fonte a fonte em 02_DADOS. Aqui garantimos apenas que a
latência de publicação é respeitada.
"""

from __future__ import annotations

import pandas as pd

REF_COL = "ref_date"
AVAIL_COL = "avail_date"


def stamp_avail_date(
    df: pd.DataFrame,
    ref_col: str = REF_COL,
    lag_days: int | None = None,
    avail_map: pd.Series | None = None,
) -> pd.DataFrame:
    """Devolve cópia do DataFrame com a coluna `avail_date` carimbada.

    Exatamente um dos dois modos:
    - ``lag_days``: `avail_date = ref + lag` em **dias corridos** (latência típica de fonte
      contínua; dias corridos, não úteis, porque fonte publica em feriado também).
    - ``avail_map``: Series `ref_date → avail_date` explícita, para fontes com calendário
      irregular de divulgação (ex.: levantamentos da CONAB). Uma `ref_date` sem entrada no
      mapa é erro — silêncio aqui viraria lookahead ou perda de dado sem registro.
    """
    if (lag_days is None) == (avail_map is None):
        raise ValueError("passe exatamente um de lag_days ou avail_map")
    out = df.copy()
    ref = pd.to_datetime(out[ref_col])
    if lag_days is not None:
        if lag_days < 0:
            raise ValueError(f"lag_days não pode ser negativo, veio {lag_days}")
        out[AVAIL_COL] = ref + pd.Timedelta(days=lag_days)
    else:
        avail = ref.map(avail_map)
        if avail.isna().any():
            faltando = sorted(ref[avail.isna()].unique())
            raise ValueError(f"ref_date sem avail_date no mapa: {faltando[:5]}")
        out[AVAIL_COL] = pd.to_datetime(avail)
    return out


def available_asof(df: pd.DataFrame, t: pd.Timestamp | str) -> pd.DataFrame:
    """Só as linhas cujo `avail_date` ≤ `t` — o único filtro temporal permitido a jusante.

    Falha alto se o DataFrame não tem `avail_date`: um dado sem carimbo não pode ser
    consumido, e deixá-lo passar seria exatamente o lookahead que a camada existe para matar.
    """
    if AVAIL_COL not in df.columns:
        raise ValueError(
            f"DataFrame sem coluna {AVAIL_COL!r} — carimbe com stamp_avail_date antes de usar"
        )
    return df[df[AVAIL_COL] <= pd.Timestamp(t)]
