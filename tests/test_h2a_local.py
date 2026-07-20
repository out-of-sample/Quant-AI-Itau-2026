"""Testes do último teste de preço (local BRL): parse IPEADATA e regra do veredito."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from quantagro.ingest.ipea_prices import PUBLICATION_LAG_DAYS, parse_ipea_prices
from quantagro.stats.h2a_local import LOCAL_OUTCOMES, h2a_local_verdict, run_h2a_local

# Formato real do OData do IPEADATA (ValoresSerie), com um valor nulo preservado.
IPEA_JSON = json.dumps(
    {
        "value": [
            {"VALDATA": "2015-01-01T00:00:00-02:00", "VALVALOR": 60.0},
            {"VALDATA": "2015-02-01T00:00:00-03:00", "VALVALOR": None},
            {"VALDATA": "2015-03-01T00:00:00-03:00", "VALVALOR": 63.5},
        ]
    }
)


def test_parse_ipea_month_end_and_lag():
    df = parse_ipea_prices(IPEA_JSON, "soy")
    assert len(df) == 2  # o valor nulo é descartado, nunca virado zero
    assert (df["price"] > 0).all()
    jan = df.iloc[0]
    assert jan["ref_date"] == pd.Timestamp("2015-01-31")
    assert jan["avail_date"] == pd.Timestamp("2015-01-31") + pd.Timedelta(days=PUBLICATION_LAG_DAYS)


def test_parse_ipea_rejects_unknown_crop():
    with pytest.raises(KeyError):
        parse_ipea_prices(IPEA_JSON, "wheat")


def _synthetic_local_panel(contemp_slope: float, fwd_slope: float, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for crop in ("soy", "corn_second"):
        for base in range(2018, 2024):
            ano = f"{base}/{(base + 1) % 100:02d}"
            for mo in range(3):
                shock = float(rng.normal())
                rows.append(
                    {
                        "crop": crop,
                        "ano_agricola": ano,
                        "base_year": base,
                        "obs_month": f"{base}-{12 - mo:02d}",
                        "shock": shock,
                        "contemp_local": contemp_slope * shock + 0.01 * rng.normal(),
                        "fwd_local": fwd_slope * shock + 0.05 * rng.normal(),
                        "cluster": f"{crop}:{ano}",
                    }
                )
    panel = pd.DataFrame(rows)
    panel["sample"] = np.where(panel["base_year"] <= 2019, "dev", "holdout")
    return panel


def test_local_verdict_transmits_when_positive():
    res = run_h2a_local(_synthetic_local_panel(contemp_slope=0.5, fwd_slope=0.3))
    assert set(res["outcome"]) == set(LOCAL_OUTCOMES)
    assert h2a_local_verdict(res).transmits is True


def test_local_verdict_null_when_flat():
    res = run_h2a_local(_synthetic_local_panel(contemp_slope=0.0, fwd_slope=0.0))
    assert h2a_local_verdict(res).transmits is False
