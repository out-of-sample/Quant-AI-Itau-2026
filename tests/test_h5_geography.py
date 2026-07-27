"""Construção do score geográfico H5 sem retornos."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantagro.backtest.operational_spec import HoldoutLockedError, TradeBlock
from quantagro.features.exposure import load_exposure_registry
from quantagro.robustness.h5_geography import (
    build_placebo_daily_precip,
    materialize_h5_grain_scores,
    placebo_window_shock_asof,
)

FIXTURES = Path(__file__).parent / "fixtures"
CHIRPS = FIXTURES / "h5_chirps_municipal_sample.csv"
EXPOSURE = Path("data/reference/exposure_hprime_v1.json")


def test_agregacao_fixture_real_e_carimbo_por_produto() -> None:
    municipal = pd.read_csv(CHIRPS, dtype={"municipality_code": str})
    daily = build_placebo_daily_precip(municipal)
    final = daily[daily["kind"] == "final"].iloc[0]
    assert final["n_cells"] == 91
    assert final["precip_mm"] == pytest.approx(9.74699534540591 * 46 / 91)
    assert final["avail_date"] == pd.Timestamp("2015-01-30")
    prelim = daily[daily["kind"] == "prelim"].iloc[0]
    assert prelim["avail_date"] == pd.Timestamp("2024-12-08")


def test_agregacao_rejeita_municipio_e_celula_ausentes() -> None:
    municipal = pd.read_csv(CHIRPS, dtype={"municipality_code": str})
    with pytest.raises(ValueError, match="cinco municípios"):
        build_placebo_daily_precip(municipal.iloc[1:])
    municipal.loc[0, "n_valid_cells"] -= 1
    with pytest.raises(ValueError, match="nodata"):
        build_placebo_daily_precip(municipal)


def _daily_stamped() -> pd.DataFrame:
    dates = pd.date_range("2000-12-01", "2021-05-31", freq="D")
    final = pd.DataFrame(
        {
            "ref_date": dates,
            "kind": "final",
            "precip_mm": 10.0 + (dates.year - 2000) / 20 + dates.dayofyear / 1000,
            "n_cells": 91,
            "avail_date": dates + pd.Timedelta(days=60),
        }
    )
    prelim_dates = pd.date_range("2020-12-01", "2021-05-31", freq="D")
    prelim = pd.DataFrame(
        {
            "ref_date": prelim_dates,
            "kind": "prelim",
            "precip_mm": 9.0 + prelim_dates.dayofyear / 1000,
            "n_cells": 91,
            "avail_date": prelim_dates + pd.Timedelta(days=7),
        }
    )
    return pd.concat([final, prelim], ignore_index=True).sort_values(["kind", "ref_date"])


def _conab() -> pd.DataFrame:
    rows = []
    ufs = {
        "soy": ("SOJA", "UNICA", ("MT", "GO", "PR", "MS", "MG", "RS", "BA")),
        "corn_second": ("MILHO", "2ª SAFRA", ("MT", "GO", "PR", "MS")),
    }
    for _, (product, season, states) in ufs.items():
        for i, uf in enumerate(states, start=1):
            rows.append(
                {
                    "produto": product,
                    "safra": season,
                    "ano_agricola": "2019/20",
                    "uf": uf,
                    "id_levantamento": 12,
                    "producao_mil_t": float(i),
                    "avail_date": pd.Timestamp("2020-09-10"),
                }
            )
    return pd.DataFrame(rows)


def _block() -> TradeBlock:
    return TradeBlock(
        crop_year="2020/21",
        sequence=0,
        decision_date=pd.Timestamp("2021-01-08"),
        execution_date=pd.Timestamp("2021-01-11"),
        exit_date=pd.Timestamp("2021-02-09"),
    )


def test_shock_asof_nao_muda_com_observacao_futura() -> None:
    daily = _daily_stamped()
    from quantagro.features.shock_spec import PRIMARY_WINDOWS

    spec = next(item for item in PRIMARY_WINDOWS if item.crop == "soy" and item.uf == "MT")
    original = placebo_window_shock_asof("2021-01-08", "2020/21", spec, daily, 2000)
    future = daily.copy()
    future.loc[
        (future["kind"] == "prelim") & (future["ref_date"] == pd.Timestamp("2021-01-08")),
        "precip_mm",
    ] = 1_000_000.0
    changed = placebo_window_shock_asof("2021-01-08", "2020/21", spec, future, 2000)
    assert original["status"] == "ok"
    assert changed["shock"] == pytest.approx(original["shock"])


def test_materializacao_holdout_exige_liberacao_explicita_e_tem_schema() -> None:
    registry = load_exposure_registry(EXPOSURE)
    with pytest.raises(HoldoutLockedError):
        materialize_h5_grain_scores(
            [_block()],
            registry,
            _daily_stamped(),
            _conab(),
            2000,
        )
    scores = materialize_h5_grain_scores(
        [_block()],
        registry,
        _daily_stamped(),
        _conab(),
        2000,
        allow_holdout=True,
    )
    assert list(scores.columns) == ["AGRO3", "SLCE3", "BRFS3", "JBSS3"]
    assert scores.index.tolist() == [pd.Timestamp("2021-01-08")]
    assert np.isfinite(scores.to_numpy()).all()
