"""Testes do teste de reação das ações: retorno forward e regra do veredito."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantagro.stats.equity_reaction import (
    _forward_return,
    reaction_verdict,
    run_equity_reaction,
)


def test_forward_return_executes_d_plus_1():
    # índice diário; observação em 2019-01-10 (qui) → entra no 1º pregão após (D+1), sai h depois
    days = pd.bdate_range("2019-01-01", periods=30)
    index = pd.Series(np.linspace(100, 130, 30), index=days)
    t = pd.Timestamp("2019-01-10")
    r = _forward_return(index, t, h=5)
    pos = int(index.index.searchsorted(t, side="right"))
    assert r == np.log(index.iloc[pos + 5] / index.iloc[pos])
    # sem pregões suficientes à frente ⇒ NaN
    assert np.isnan(_forward_return(index, pd.Timestamp("2019-02-10"), h=5))


def _synthetic_reaction_panel(slope: float, seed: int = 0) -> pd.DataFrame:
    """Painel sintético: retorno = slope*score + ruído, 4 nomes × várias datas × safras."""
    rng = np.random.default_rng(seed)
    names = ["AGRO3", "SLCE3", "BRFS3", "JBSS3"]
    signs = {"AGRO3": 1, "SLCE3": 1, "BRFS3": -1, "JBSS3": -1}
    rows = []
    for base in range(2015, 2020):
        ano = f"{base}/{(base + 1) % 100:02d}"
        for m in range(4):
            date = pd.Timestamp(base, 12, 1) + pd.offsets.MonthEnd(m)
            shock = float(rng.normal())
            for tk in names:
                score = signs[tk] * shock
                rows.append(
                    {
                        "date": date,
                        "ticker": tk,
                        "ano_agricola": ano,
                        "score": score,
                        "fwd_ret": slope * score + 0.02 * rng.normal(),
                    }
                )
    return pd.DataFrame(rows)


def test_reaction_positive_signal_reacts():
    res = run_equity_reaction(_synthetic_reaction_panel(slope=0.05))
    v = reaction_verdict(res)
    assert v.beta > 0
    assert v.reacts is True
    assert res["pnl"]["mean"] > 0  # a carteira dollar-neutral ganha quando o score acerta


def test_reaction_null_signal_does_not_react():
    res = run_equity_reaction(_synthetic_reaction_panel(slope=0.0, seed=7))
    assert reaction_verdict(res).reacts is False
