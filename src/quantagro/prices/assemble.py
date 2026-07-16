"""Montador: COTAHIST + as três fontes de eventos → retorno total por papel.

Este módulo fecha o risco R5 juntando as peças já construídas — o close bruto do COTAHIST
(`ingest.cotahist`), os proventos em dinheiro da B3 (`ingest.events_b3`) e da StatusInvest
(`ingest.events_statusinvest`, cauda deslistada) e os eventos em ações da B3 — numa série de
**retorno total diário, point-in-time e delisting-aware** via `prices.adjust.total_return`.

As três armadilhas que ele existe para tratar (docs/02_DADOS.md §4.2.1, D-013/D-014):

1. **Dupla contagem na sobreposição de fontes.** Para papéis que a B3 cobre parcialmente
   (JBS até 2019), o merge usa a B3 como primária e só aceita da StatusInvest o que a B3 não
   tem: um evento da StatusInvest com a mesma data-com e valor igual dentro de 5e-4 relativo
   (a tolerância do cross-check documentado) é o mesmo evento e é descartado. Dois eventos
   legítimos na mesma data-com (dividendo + JCP, visto em SLC 12/12/2025) têm valores
   distintos e sobrevivem ambos.

2. **Proventos após a deslistagem.** BRFS3 tem provento com data-com posterior à incorporação
   pela Marfrig (visto ao vivo). Como a série do COTAHIST termina no último pregão do papel,
   o motor descarta eventos sem data-ex dentro da janela — comportamento herdado de
   `_align_events_to_ex_date` e travado em teste aqui.

3. **Split perdido (truncamento do supplement da B3).** O endpoint de eventos em ações parece
   truncar listas; um split ausente aparece na série como retorno de ~±50% num dia. O tripwire
   `flag_suspect_returns` lista esses dias para inspeção humana — é um detector barato, não
   prova de ausência, e nunca "corrige" sozinho.

O `close` por papel vem de `close_series`, que converte o preço de cotação para **por ação**
dividindo por `quote_factor` (fatcot=1000 = cotação por mil ações em papéis antigos; hoje
quase sempre 1 — conferido em arquivo real).
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from quantagro.prices.adjust import CorporateEvent, total_return

# Tolerância relativa para considerar "mesmo evento" no merge B3 × StatusInvest.
# Vem do cross-check documentado (pior desvio observado 3,9e-4, em 02_DADOS §4.2.1).
_SAME_EVENT_RTOL = 5e-4


def close_series(quotes: pd.DataFrame, ticker: str) -> pd.Series:
    """Close **por ação** de um papel, indexado por pregão, a partir das cotações do COTAHIST.

    Espera o DataFrame de `parse_cotahist` (idealmente já filtrado por `filter_equities_spot`;
    vários anos podem vir concatenados). Divide o close pelo `quote_factor` para normalizar
    cotações por lote de mil (fatcot=1000) para base por ação.
    """
    rows = quotes.loc[quotes["ticker"] == ticker, ["date", "close", "quote_factor"]]
    if rows.empty:
        raise ValueError(f"nenhuma cotação para {ticker!r} no DataFrame recebido")
    rows = rows.sort_values("date")
    if rows["date"].duplicated().any():
        dup = rows.loc[rows["date"].duplicated(), "date"].iloc[0]
        raise ValueError(
            f"{ticker!r} tem mais de uma cotação para {dup.date()} — o filtro de segmento "
            "(filter_equities_spot) foi aplicado?"
        )
    out = pd.Series(
        (rows["close"] / rows["quote_factor"]).to_numpy(),
        index=pd.DatetimeIndex(rows["date"]),
        name=ticker,
    )
    out.index.name = "date"
    return out


def merge_cash_events(
    primary: Iterable[CorporateEvent],
    fallback: Iterable[CorporateEvent],
    rtol: float = _SAME_EVENT_RTOL,
) -> list[CorporateEvent]:
    """Une proventos em dinheiro de duas fontes sem contar o mesmo evento duas vezes.

    `primary` (B3) entra inteira. De `fallback` (StatusInvest) entra só o que não casa com
    nenhum evento primário ainda não usado na mesma data-com com valor dentro de `rtol`
    relativo — o casamento é 1-para-1 (greedy pelo valor mais próximo), para que dividendo e
    JCP na mesma data não se anulem. Um evento de fallback na mesma data com valor fora da
    tolerância é tratado como **preenchimento de lacuna** da primária e mantido; divergência
    de valor real entre as fontes teria aparecido no cross-check (02_DADOS §4.2.1).
    """
    merged = list(primary)
    budget: dict[pd.Timestamp, list[float]] = {}
    for ev in merged:
        budget.setdefault(ev.cum_date, []).append(ev.cash_value)
    for ev in fallback:
        candidates = budget.get(ev.cum_date, [])
        if candidates:
            nearest = min(range(len(candidates)), key=lambda i: abs(candidates[i] - ev.cash_value))
            ref = candidates[nearest]
            if abs(ev.cash_value - ref) <= rtol * ref:
                candidates.pop(nearest)  # mesmo evento: consome o par e descarta o fallback
                continue
        merged.append(ev)
    merged.sort(key=lambda e: e.cum_date)
    return merged


def assemble_total_return(
    close: pd.Series,
    cash_primary: Iterable[CorporateEvent] = (),
    cash_fallback: Iterable[CorporateEvent] = (),
    stock: Iterable[CorporateEvent] = (),
) -> pd.Series:
    """Série de retorno total de um papel: close bruto + dinheiro (2 fontes) + ações.

    `cash_primary`/`cash_fallback` são os proventos em dinheiro da fonte primária (B3) e da
    preenchedora (StatusInvest) — deduplicados por `merge_cash_events`. `stock` são os eventos
    em ações (split/bonificação/grupamento) já normalizados. Eventos com data-com no último
    pregão ou depois dele (papel já deslistado) são descartados pelo motor — a série termina
    onde o pregão terminou.
    """
    events = merge_cash_events(cash_primary, cash_fallback) + list(stock)
    return total_return(close, events)


def flag_suspect_returns(ret: pd.Series, threshold: float = 0.30) -> pd.Series:
    """Dias com |retorno| ≥ `threshold` — tripwire barato para split perdido.

    Um split 2:1 ausente da fonte de eventos aparece como retorno de ~−50% num dia (e um
    grupamento 10:1 como ~+900%). O default de 30% é o piso que ainda pega um split 1,5:1
    (~−33%); **bonificações pequenas escapam** (uma de 12,5% aparece como −11%, dentro do
    ruído de mercado) — para essas, a defesa é o cross-check contra uma fonte ajustada
    independente, não este limiar. Movimentos legítimos ≥ 30% num pregão existem mas são
    raros; cada dia listado merece inspeção humana. É um detector, não prova de ausência —
    e nunca corrige nada sozinho (imputação silenciosa é proibida).
    """
    return ret[ret.abs() >= threshold]
