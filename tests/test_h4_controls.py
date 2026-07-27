"""Invariantes do painel diário H4, sem retorno da estratégia."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantagro.ingest.nefin import FACTOR_COLUMNS
from quantagro.ingest.oni import parse_oni
from quantagro.robustness.h4_controls import (
    H4_COLUMNS,
    build_h4_controls,
    validate_h4_controls,
)


def _nefin() -> pd.DataFrame:
    dates = pd.bdate_range("2019-12-20", "2020-01-10")
    data: dict[str, object] = {"ref_date": dates}
    for i, column in enumerate(FACTOR_COLUMNS, start=1):
        data[column] = np.full(len(dates), i / 10_000)
    return pd.DataFrame(data)


def _level(dates, values, value_column) -> pd.DataFrame:
    return pd.DataFrame({"ref_date": pd.to_datetime(dates), value_column: values})


def _market() -> dict[str, pd.DataFrame]:
    dates = pd.bdate_range("2019-12-20", "2020-01-10")
    values = np.arange(len(dates), dtype=float) + 100
    return {
        "usdbrl": _level(dates, values, "brl_per_usd"),
        "soy": _level(dates, values * 2, "adjusted_close"),
        "corn_second": _level(dates, values * 3, "adjusted_close"),
        "sugar": _level(dates, values * 4, "adjusted_close"),
    }


def _oni() -> pd.DataFrame:
    return parse_oni(
        "SEAS YR TOTAL ANOM\nJJA 2019 27.0 0.4\nJAS 2019 26.8 0.5\nASO 2019 26.7 0.6\n"
    )


def test_builder_schema_retorno_e_snapshot() -> None:
    panel = build_h4_controls(
        _nefin(),
        _market(),
        _oni(),
        snapshot_avail_date="2026-07-27",
    )
    assert tuple(panel.columns) == H4_COLUMNS
    assert panel["ref_date"].min() == pd.Timestamp("2020-01-01")
    assert (panel["avail_date"] == pd.Timestamp("2026-07-27")).all()
    expected = 108 / 107 - 1
    row = panel.loc[panel["ref_date"].eq("2020-01-01")].iloc[0]
    assert row["soy"] == pytest.approx(expected)
    assert row["usdbrl"] == pytest.approx(expected)
    assert row["oni"] == pytest.approx(0.5)


def test_feriado_externo_carrega_nivel_sem_olhar_futuro() -> None:
    market = _market()
    for role in market:
        value = "brl_per_usd" if role == "usdbrl" else "adjusted_close"
        market[role] = market[role][market[role]["ref_date"].ne(pd.Timestamp("2020-01-02"))]
        assert value in market[role]
    panel = build_h4_controls(
        _nefin(),
        market,
        _oni(),
        snapshot_avail_date="2026-07-27",
    )
    row = panel.loc[panel["ref_date"].eq("2020-01-02")].iloc[0]
    assert row[["usdbrl", "soy", "corn_second", "sugar"]].eq(0).all()


def test_staleness_e_input_ausente_falham_alto() -> None:
    market = _market()
    market["soy"] = market["soy"].iloc[:1]
    with pytest.raises(ValueError, match="carregado"):
        build_h4_controls(
            _nefin(),
            market,
            _oni(),
            snapshot_avail_date="2026-07-27",
        )
    market = _market()
    del market["sugar"]
    with pytest.raises(ValueError, match="ausentes"):
        build_h4_controls(
            _nefin(),
            market,
            _oni(),
            snapshot_avail_date="2026-07-27",
        )


def test_oni_nao_usa_temporada_ainda_indisponivel() -> None:
    oni = parse_oni("SEAS YR TOTAL ANOM\nJAS 2019 26.8 0.5\nASO 2019 26.7 0.6\nSON 2019 26.6 9.0\n")
    panel = build_h4_controls(
        _nefin(),
        _market(),
        oni,
        snapshot_avail_date="2026-07-27",
    )
    assert panel.loc[panel["ref_date"].lt("2020-01-05"), "oni"].eq(0.5).all()
    assert panel.loc[panel["ref_date"].ge("2020-01-05"), "oni"].eq(0.6).all()
    assert not panel["oni"].eq(9.0).any()


def test_validador_rejeita_nulo_e_avail_date_antes_da_referencia() -> None:
    panel = build_h4_controls(
        _nefin(),
        _market(),
        _oni(),
        snapshot_avail_date="2026-07-27",
    )
    bad = panel.copy()
    bad.loc[0, "soy"] = np.nan
    with pytest.raises(ValueError, match="ausente"):
        validate_h4_controls(bad)
    bad = panel.copy()
    bad["avail_date"] = pd.Timestamp("2019-01-01")
    with pytest.raises(ValueError, match="snapshot"):
        validate_h4_controls(bad)
