"""Universo dinâmico point-in-time a partir do COTAHIST (docs/04_PROTOCOLO_BACKTEST.md §1).

O universo **não é uma lista de tickers — é uma função de `t`**. Uma ação pertence ao universo
no pregão `t` se, e somente se:

(i)   estava sendo negociada na B3 em `t` segundo o COTAHIST;
(ii)  já se passaram `ipo_seasoning` pregões desde a primeira negociação (poeira de IPO:
      estabilização, lock-up, bookbuilding);
(iii) o ADTV dos últimos `adtv_window` pregões supera o piso de liquidez;
(iv)  tem exposição fundamentalista definida — critério aplicado via `tickers` (whitelist),
      porque a matriz `E` é da camada de features, não desta.

O piso de ADTV **não tem default de propósito**: a camada continua reutilizável, mas o backtest
primário passa explicitamente R$ 8 milhões, congelados sem P&L em D-055 (04_PROTOCOLO §4).

Duas propriedades importam mais que tudo:
- **Deslistagem não apaga o passado**: o papel sai do universo quando para de negociar, mas
  permanece em todos os `t` anteriores (JBSS3/BRFS3/MRFG3/STBP3 — risco R4).
- **Conservador por construção no início da janela**: a contagem de pregões pós-IPO usa só
  os dados fornecidos. Um papel listado muito antes do início da janela passa os primeiros
  `ipo_seasoning` pregões fora do universo — perda pequena e sem lookahead. Para o backtest
  real, alimentar o histórico desde antes do início do período avaliado.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class UniverseState:
    """Painéis auditáveis que explicam cada inclusão e exclusão do universo."""

    traded: pd.DataFrame
    seasoned: pd.DataFrame
    adtv_brl: pd.DataFrame
    eligible: pd.DataFrame
    reason: pd.DataFrame


def universe_state(
    quotes: pd.DataFrame,
    adtv_floor: float,
    ipo_seasoning: int = 60,
    adtv_window: int = 21,
    tickers: list[str] | None = None,
) -> UniverseState:
    """Devolve universo, ADTV e reason codes no calendário B3 completo.

    O calendário é extraído **antes** da whitelist. Assim, um pregão em que nenhum papel do
    universo econômico negociou continua contando na janela de ADTV e no seasoning. A função
    mantém ``pivot`` (não ``pivot_table``) para duplicatas explodirem em vez de serem somadas.
    """
    if adtv_floor < 0:
        raise ValueError(f"adtv_floor não pode ser negativo, veio {adtv_floor}")
    if ipo_seasoning < 0 or adtv_window <= 0:
        raise ValueError("seasoning deve ser não-negativo e janela de ADTV positiva")
    required = {"date", "ticker", "financial_volume"}
    missing = required - set(quotes.columns)
    if missing:
        raise ValueError(f"cotações sem colunas obrigatórias: {sorted(missing)}")
    calendar = pd.DatetimeIndex(pd.to_datetime(quotes["date"]).unique()).sort_values()
    if calendar.empty:
        raise ValueError("cotações vazias")

    selected = quotes
    if tickers is not None:
        selected = selected[selected["ticker"].isin(tickers)]
        if selected.empty:
            raise ValueError("nenhum dos tickers da whitelist aparece nas cotações")
    volume = selected.pivot(index="date", columns="ticker", values="financial_volume")  # noqa: PD010
    volume.index = pd.DatetimeIndex(volume.index)
    volume = volume.reindex(calendar)
    traded = volume.notna()
    adtv = volume.fillna(0.0).rolling(adtv_window).mean()

    # Pregões decorridos desde a primeira negociação observada, não número de negócios do
    # papel. Uma suspensão temporária continua envelhecendo a companhia no calendário B3.
    started = traded.cummax()
    sessions_since_first = started.cumsum() - 1
    seasoned = sessions_since_first >= ipo_seasoning
    eligible = traded & seasoned & (adtv >= adtv_floor)

    reason = pd.DataFrame("eligible", index=calendar, columns=volume.columns, dtype="string")
    reason = reason.mask(~traded, "not_traded")
    reason = reason.mask(traded & ~seasoned, "seasoning")
    reason = reason.mask(traded & seasoned & adtv.isna(), "adtv_warmup")
    reason = reason.mask(traded & seasoned & adtv.notna() & (adtv < adtv_floor), "adtv_below_floor")
    if not np.array_equal(eligible.to_numpy(), reason.eq("eligible").to_numpy()):
        raise RuntimeError("reason codes não fecham com a matriz de elegibilidade")

    for frame in (traded, seasoned, adtv, eligible, reason):
        frame.index.name = "date"
    return UniverseState(traded, seasoned, adtv, eligible, reason)


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
    return universe_state(
        quotes,
        adtv_floor=adtv_floor,
        ipo_seasoning=ipo_seasoning,
        adtv_window=adtv_window,
        tickers=tickers,
    ).eligible


def eligible_count(membership: pd.DataFrame) -> pd.Series:
    """Nº de papéis elegíveis por pregão — o gráfico-prova de que o universo é dinâmico.

    Entregável obrigatório do relatório (04_PROTOCOLO §1): a contagem caindo nas
    deslistagens e subindo nos IPOs é a evidência visual de que não há survivorship.
    """
    out = membership.sum(axis=1)
    out.name = "eligible_count"
    return out
