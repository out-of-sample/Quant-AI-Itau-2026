"""Testes de H2a: parse do preço FRED, janela de observação, retorno forward e regra do portão."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantagro.ingest.fred_prices import PUBLICATION_LAG_DAYS, parse_fred_prices
from quantagro.stats.h2a import (
    PRIMARY_HORIZON,
    _fwd_return,
    _obs_month_ends,
    build_h2a_panel,
    h2a_verdict,
    run_h2a,
)

# Trecho real do formato FRED (PSOYBUSDM), com uma linha ausente "." preservada de propósito.
FRED_CSV = (
    "observation_date,PSOYBUSDM\n"
    "2015-01-01,401.5\n"
    "2015-02-01,.\n"
    "2015-03-01,380.2\n"
    "2015-04-01,384.1\n"
)


def test_parse_fred_month_end_and_avail_lag():
    df = parse_fred_prices(FRED_CSV, "soy")
    # a linha "." é descartada, nunca virada zero
    assert len(df) == 3
    assert (df["price"] > 0).all()
    # ref_date é fim de mês; avail_date embute o atraso de publicação do IMF
    jan = df.iloc[0]
    assert jan["ref_date"] == pd.Timestamp("2015-01-31")
    assert jan["avail_date"] == pd.Timestamp("2015-01-31") + pd.Timedelta(days=PUBLICATION_LAG_DAYS)


def test_parse_fred_rejects_unknown_crop():
    with pytest.raises(KeyError):
        parse_fred_prices(FRED_CSV, "wheat")


def test_obs_month_ends_within_window():
    # soja 2018/19: janela nacional ~dez/2018–mar/2019 ⇒ fins de mês dez,jan,fev,mar
    ends = _obs_month_ends("soy", "2018/19")
    assert pd.Timestamp("2018-12-31") in ends
    assert pd.Timestamp("2019-03-31") in ends
    assert all(e == (e + pd.offsets.MonthEnd(0)) for e in ends)


def test_fwd_return_log_ratio():
    price = pd.Series(
        [100.0, 110.0, 121.0],
        index=[pd.Timestamp("2019-01-31"), pd.Timestamp("2019-02-28"), pd.Timestamp("2019-03-31")],
    )
    r = _fwd_return(price, pd.Timestamp("2019-01-31"), 2)
    assert r == pytest.approx(np.log(121.0 / 100.0))
    # alvo ausente ⇒ NaN, nunca zero
    assert np.isnan(_fwd_return(price, pd.Timestamp("2019-03-31"), 2))


def _synthetic_panel(slope: float, seed: int = 0) -> pd.DataFrame:
    """Painel H2a sintético: fwd_ret = slope*shock + ruído, 2 culturas × 6 safras × 3 meses."""
    rng = np.random.default_rng(seed)
    rows = []
    for crop in ("soy", "corn_second"):
        for base in range(2018, 2024):  # 6 safras -> 12 clusters no pooled
            ano = f"{base}/{(base + 1) % 100:02d}"
            for mo in range(3):
                shock = float(rng.normal())
                for h in (1, 2, 3):
                    rows.append(
                        {
                            "crop": crop,
                            "ano_agricola": ano,
                            "base_year": base,
                            "obs_month": f"{base}-{12 - mo:02d}",
                            "h": h,
                            "shock": shock,
                            "fwd_ret": slope * shock + 0.01 * rng.normal(),
                            "cluster": f"{crop}:{ano}",
                        }
                    )
    panel = pd.DataFrame(rows)
    panel["sample"] = np.where(panel["base_year"] <= 2019, "dev", "holdout")
    return panel


def test_run_h2a_positive_relation_passes():
    res = run_h2a(_synthetic_panel(slope=0.5))
    v = h2a_verdict(res)
    assert v.status == "PASSA"
    assert v.beta > 0
    # existe linha pooled no h primário, span cheio
    row = res[(res["scope"] == "full") & (res["unit"] == "pooled") & (res["h"] == PRIMARY_HORIZON)]
    assert len(row) == 1


def test_run_h2a_negative_relation_fails():
    v = h2a_verdict(run_h2a(_synthetic_panel(slope=-0.5)))
    assert v.status == "REPROVA"
    assert v.beta < 0


def test_run_h2a_reports_dev_and_holdout():
    res = run_h2a(_synthetic_panel(slope=0.5))
    assert set(res["scope"]) == {"full", "dev", "holdout"}


def test_build_h2a_panel_requires_observations():
    empty_prices = pd.DataFrame({"crop": [], "ref_date": [], "price": [], "avail_date": []})
    with pytest.raises((ValueError, KeyError, FileNotFoundError)):
        build_h2a_panel(empty_prices, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), 2000)
