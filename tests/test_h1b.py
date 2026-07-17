"""Testes de H1b (stats/h1b.py) — âncora de colheita, Δlog ano-contra-ano e regressão.

A integração com ``Shock`` nacional já é coberta por test_shock.py; aqui trava-se o desfecho de
exportação: âncora modal por cultura, Δlog YoY do kg exportado e a regressão por cultura×horizonte.
"""

import numpy as np
import pandas as pd
import pytest

from quantagro.stats.h1b import HORIZONS, _anchor_month, _yoy_dlog, run_h1b


def test_anchor_month_modal_por_cultura():
    assert _anchor_month("soy") == 2  # maioria das UFs de soja encerra em fevereiro
    assert _anchor_month("corn_second") == 5  # milho 2ª encerra em maio


def _export():
    # duas NCMs, jan/2018–dez/2020, com salto conhecido para conferir o Δlog
    rows = []
    for year in (2018, 2019, 2020):
        for month in range(1, 13):
            for ncm, base in (("12019000", 1000), ("10059010", 500)):
                kg = base * (2 if year == 2020 and month == 5 else 1)
                rows.append(
                    {
                        "ref_date": (pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)),
                        "co_ncm": ncm,
                        "metric_kg": kg,
                    }
                )
    return pd.DataFrame(rows)


def test_yoy_dlog_conferivel():
    exp = _export()
    # maio/2020 dobrou vs maio/2019 ⇒ Δlog = log(2)
    assert _yoy_dlog(exp, "12019000", 2020, 5) == pytest.approx(np.log(2))
    # mês sem salto ⇒ Δlog = 0
    assert _yoy_dlog(exp, "12019000", 2020, 6) == pytest.approx(0.0)
    # ano sem base anterior ⇒ NaN
    assert np.isnan(_yoy_dlog(exp, "12019000", 2018, 5))


def _panel(seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for base in range(2018, 2025):
        ano = f"{base}/{(base + 1) % 100:02d}"
        for crop in ("soy", "corn_second"):
            shock = rng.normal()
            for h in HORIZONS:
                rows.append(
                    {
                        "crop": crop,
                        "ano_agricola": ano,
                        "base_year": base,
                        "h": h,
                        "shock": shock,
                        "dlog_export": -0.2 * shock + rng.normal(scale=0.05),
                    }
                )
    return pd.DataFrame(rows)


def test_run_h1b_por_cultura_e_horizonte():
    res = run_h1b(_panel())
    # 2 culturas × 4 horizontes = 8 regressões
    assert len(res) == 8
    assert set(res["h"]) == set(HORIZONS)
    # sinal esperado negativo domina (estresse ⇒ menos exportação)
    assert (res["beta"] < 0).mean() >= 0.75
