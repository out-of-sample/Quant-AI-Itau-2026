"""Universo dinâmico point-in-time a partir do COTAHIST (docs/04_PROTOCOLO_BACKTEST.md §1).

O universo **não é uma lista de tickers — é uma função de `t`**. Uma ação pertence ao universo
no pregão `t` se, e somente se:

(i)   estava sendo negociada na B3 em `t` segundo o COTAHIST;
(ii)  já se passaram `ipo_seasoning` pregões desde a primeira negociação (poeira de IPO:
      estabilização, lock-up, bookbuilding);
(iii) o ADTV dos últimos `adtv_window` pregões supera o piso de liquidez;
(iv)  tem exposição fundamentalista definida — critério aplicado via `tickers` (whitelist),
      porque a matriz `E` é da camada de features, não desta.

O piso de ADTV **não tem default de propósito**: seu valor é decisão de calibração in-sample
(04_PROTOCOLO §3), não desta camada.

Duas propriedades importam mais que tudo:
- **Deslistagem não apaga o passado**: o papel sai do universo quando para de negociar, mas
  permanece em todos os `t` anteriores (JBSS3/BRFS3/MRFG3/STBP3 — risco R4).
- **Conservador por construção no início da janela**: a contagem de pregões pós-IPO usa só
  os dados fornecidos. Um papel listado muito antes do início da janela passa os primeiros
  `ipo_seasoning` pregões fora do universo — perda pequena e sem lookahead. Para o backtest
  real, alimentar o histórico desde antes do início do período avaliado.
"""

from __future__ import annotations

import pandas as pd


def universe_membership(
    quotes: pd.DataFrame,
    adtv_floor: float,
    ipo_seasoning: int = 60,
    adtv_window: int = 21,
    tickers: list[str] | None = None,
) -> pd.DataFrame:
    """Matriz booleana (pregão × ticker) de pertencimento ao universo.

    `quotes` é o DataFrame de `parse_cotahist` já filtrado por `filter_equities_spot`
    (vários períodos concatenados). O calendário de pregão é o do próprio arquivo — dias em
    que a B3 operou. ADTV = média móvel de `adtv_window` pregões do volume financeiro, com
    dia sem negociação contando **zero** (iliquidez conta contra o papel, não é ignorada).
    """
    if adtv_floor < 0:
        raise ValueError(f"adtv_floor não pode ser negativo, veio {adtv_floor}")
    df = quotes
    if tickers is not None:
        df = df[df["ticker"].isin(tickers)]
        if df.empty:
            raise ValueError("nenhum dos tickers da whitelist aparece nas cotações")
    # pivot (não pivot_table) de propósito: duplicata (date, ticker) tem que EXPLODIR,
    # não ser agregada silenciosamente — indicaria filtro de segmento não aplicado.
    vol = df.pivot(index="date", columns="ticker", values="financial_volume")  # noqa: PD010
    traded = vol.notna()
    adtv = vol.fillna(0.0).rolling(adtv_window).mean()
    seasoned = traded.cumsum() > ipo_seasoning
    membership = traded & seasoned & (adtv >= adtv_floor)
    membership.index.name = "date"
    return membership


def eligible_count(membership: pd.DataFrame) -> pd.Series:
    """Nº de papéis elegíveis por pregão — o gráfico-prova de que o universo é dinâmico.

    Entregável obrigatório do relatório (04_PROTOCOLO §1): a contagem caindo nas
    deslistagens e subindo nos IPOs é a evidência visual de que não há survivorship.
    """
    out = membership.sum(axis=1)
    out.name = "eligible_count"
    return out
