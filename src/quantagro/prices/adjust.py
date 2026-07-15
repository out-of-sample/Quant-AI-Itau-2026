"""Motor de retorno total a partir de preço bruto (COTAHIST) + eventos corporativos.

Por que **retorno total diário** e não "preço ajustado"
------------------------------------------------------
O ajuste retroativo clássico ("adjusted close") reescala todo o passado a cada novo provento.
O nível ajustado numa data `t` passa então a embutir dividendos que só foram pagos **depois**
de `t` — isto é lookahead puro para qualquer sinal que olhe nível de preço. Por isso este
módulo nunca devolve um nível ajustado: devolve o **retorno total diário**, calculado só para
frente, usando cada evento apenas a partir da sua data-ex. Essa série é point-in-time por
construção (o retorno até `t` não muda se um evento posterior a `t` for adicionado — travado
em teste).

Convenção de datas
------------------
As fontes (B3 `lastDatePrior`; StatusInvest `ed`) informam a **data-com** (último pregão em que
a ação ainda carrega o provento). O preço cai no **primeiro pregão seguinte** — a data-ex. Como
o motor recebe o índice de pregões (do próprio COTAHIST), ele mesmo resolve a data-ex = primeiro
pregão estritamente após a data-com; não precisa de um calendário à parte.

Álgebra do retorno na data-ex `t` (pregão anterior `p`)
------------------------------------------------------
Quem detinha 1 ação até a data-com, na data-ex passa a ter `share_ratio` ações (split/
bonificação) valendo `close_t` cada, mais `cash_value` em dinheiro por ação original:

    retorno_bruto_t = (share_ratio · close_t + cash_value) / close_p

- `cash_value`: dividendo/JCP por ação, no valor **nominal da data-com** (0 se não houver).
- `share_ratio`: ações depois ÷ ações antes (1.0 se não houver evento em ações). Um split 2:1
  tem `share_ratio = 2`; como `close_t ≈ close_p/2`, o retorno fica ≈ 0 (split é neutro).

Em pregão sem evento, `share_ratio = 1` e `cash_value = 0`, então o retorno é `close_t/close_p`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CorporateEvent:
    """Um evento corporativo já normalizado (fonte-agnóstico).

    O trabalho específico de cada fonte — interpretar o `factor` da B3, tratar o campo `adj`
    da StatusInvest (que reescreve valor por ação para splits), converter proporção em
    `share_ratio` — é da camada de ingestão, não deste motor. Aqui os campos já chegam limpos.
    """

    cum_date: pd.Timestamp  # data-com; o preço ajusta no pregão seguinte
    cash_value: float = 0.0  # dividendo/JCP por ação, nominal na base da data-com
    share_ratio: float = 1.0  # ações depois ÷ ações antes (split/bonificação)

    def __post_init__(self) -> None:
        if self.share_ratio <= 0:
            raise ValueError(f"share_ratio deve ser > 0, veio {self.share_ratio}")
        if self.cash_value < 0:
            raise ValueError(f"cash_value não pode ser negativo, veio {self.cash_value}")


@dataclass
class _Aligned:
    cash: pd.Series
    ratio: pd.Series
    ignored: list[CorporateEvent] = field(default_factory=list)


def _align_events_to_ex_date(close: pd.Series, events: list[CorporateEvent]) -> _Aligned:
    """Mapeia cada evento para sua data-ex (1º pregão após a data-com) e acumula por data.

    Eventos cuja data-com cai em ou após o último pregão da série não têm data-ex dentro da
    janela e são ignorados (devolvidos em `ignored`, para o chamador registrar se quiser).
    """
    idx = close.index
    cash = pd.Series(0.0, index=idx)
    ratio = pd.Series(1.0, index=idx)
    ignored: list[CorporateEvent] = []

    # posição do 1º pregão estritamente após a data-com
    for ev in events:
        pos = idx.searchsorted(pd.Timestamp(ev.cum_date), side="right")
        if pos >= len(idx):
            ignored.append(ev)
            continue
        ex = idx[pos]
        # ordem numa mesma data-ex: aplica o split e só então soma o dinheiro (já na base nova)
        ratio.loc[ex] *= ev.share_ratio
        cash.loc[ex] += ev.cash_value
    return _Aligned(cash=cash, ratio=ratio, ignored=ignored)


def total_return(close: pd.Series, events: list[CorporateEvent] | None = None) -> pd.Series:
    """Retorno total diário, point-in-time, a partir do close bruto e dos eventos.

    Parameters
    ----------
    close : pd.Series
        Close bruto do COTAHIST (não ajustado) de UM papel, indexado por pregão (ordenado).
    events : list[CorporateEvent] | None
        Eventos corporativos do papel. `None`/vazio ⇒ retorno = variação simples do close.

    Returns
    -------
    pd.Series
        Retorno total por pregão, mesmo índice de `close`; a primeira posição é NaN.
    """
    if not close.index.is_monotonic_increasing:
        raise ValueError("close precisa estar ordenado por data crescente")
    if close.index.has_duplicates:
        raise ValueError("close tem datas duplicadas")

    aligned = _align_events_to_ex_date(close, events or [])
    prev = close.shift(1)
    gross = (aligned.ratio * close + aligned.cash) / prev
    ret = gross - 1.0
    ret.iloc[0] = np.nan
    ret.name = close.name
    return ret


def total_return_index(close: pd.Series, events: list[CorporateEvent] | None = None) -> pd.Series:
    """Índice de retorno total (base 1.0 no 1º pregão) — conveniência para plot/checagem.

    É o produto acumulado de (1 + retorno). Continua point-in-time: o valor em `t` só depende
    de eventos com data-ex ≤ `t`, nunca de proventos futuros (ao contrário do 'adjusted close').
    """
    ret = total_return(close, events).fillna(0.0)
    return (1.0 + ret).cumprod()
