"""Testes das transformações da suíte de robustez de H1 (D-065). Puras, sem o build lento."""

from __future__ import annotations

import pandas as pd
import pytest

from quantagro.features.shock_spec import (
    CLIMATOLOGY_KIND,
    PRIMARY_SIGNAL_KIND,
    PRIMARY_WINDOWS,
    critical_period,
)
from quantagro.stats.robustness import (
    _prev_crop_year,
    placebo_spatial,
    placebo_temporal,
    pooled_full_row,
    shift_window,
    shifted_windows,
    use_final_as_signal,
    with_extra_signal_lag,
)


def test_shift_window_moves_critical_period_by_days() -> None:
    spec = PRIMARY_WINDOWS[0]
    base_start, base_end = critical_period(spec, "2020/21")
    shifted = shift_window(spec, 15)
    s_start, s_end = critical_period(shifted, "2020/21")
    assert (s_start - base_start).days == 15
    assert (s_end - base_end).days == 15


def test_shift_window_zero_is_identity() -> None:
    spec = PRIMARY_WINDOWS[0]
    assert shift_window(spec, 0) is spec


def test_shifted_windows_preserves_count_and_keys() -> None:
    out = shifted_windows(PRIMARY_WINDOWS, -15)
    assert len(out) == len(PRIMARY_WINDOWS)
    assert [w.key for w in out] == [w.key for w in PRIMARY_WINDOWS]


def _stamped() -> pd.DataFrame:
    dates = pd.to_datetime(["2020-01-31", "2020-02-29"])
    rows = []
    for kind in (PRIMARY_SIGNAL_KIND, CLIMATOLOGY_KIND):
        for d in dates:
            rows.append({"kind": kind, "ref_date": d, "avail_date": d, "precip_mm": 10.0})
    return pd.DataFrame(rows)


def test_with_extra_signal_lag_shifts_only_signal_avail() -> None:
    panel = _stamped()
    out = with_extra_signal_lag(panel, 14)
    sig = out[out["kind"] == PRIMARY_SIGNAL_KIND]
    clim = out[out["kind"] == CLIMATOLOGY_KIND]
    assert ((sig["avail_date"] - sig["ref_date"]).dt.days == 14).all()
    assert (clim["avail_date"] == clim["ref_date"]).all()  # climatologia intocada


def test_use_final_as_signal_relabels_and_keeps_climatology() -> None:
    panel = _stamped()
    out = use_final_as_signal(panel)
    # Sinal agora vem da série final (mesmas datas), e a climatologia final continua presente.
    assert set(out["kind"].unique()) == {PRIMARY_SIGNAL_KIND, CLIMATOLOGY_KIND}
    n_final = (panel["kind"] == CLIMATOLOGY_KIND).sum()
    assert (out["kind"] == PRIMARY_SIGNAL_KIND).sum() == n_final
    assert (out["kind"] == CLIMATOLOGY_KIND).sum() == n_final
    # Nenhuma linha prelim original sobreviveu (todas vieram do relabel do final).
    assert len(out) == 2 * n_final


def _panel(shocks: dict) -> pd.DataFrame:
    rows = []
    for (crop, uf, ano, lev), shock in shocks.items():
        rows.append(
            {
                "crop": crop,
                "uf": uf,
                "ano_agricola": ano,
                "id_levantamento": lev,
                "shock": shock,
                "logrev": -0.1 * shock,
            }
        )
    return pd.DataFrame(rows)


def test_placebo_spatial_permutes_within_group_preserving_multiset() -> None:
    panel = _panel(
        {
            ("soy", "MT", "2020/21", 3): 1.0,
            ("soy", "GO", "2020/21", 3): 2.0,
            ("soy", "PR", "2020/21", 3): 3.0,
        }
    )
    out = placebo_spatial(panel, seed=1)
    # O multiset de shocks no grupo é preservado; só o pareamento UF↔shock muda.
    assert sorted(out["shock"].tolist()) == [1.0, 2.0, 3.0]
    assert set(out["uf"]) == {"MT", "GO", "PR"}


def test_placebo_spatial_singleton_group_unchanged() -> None:
    panel = _panel({("corn_second", "MT", "2020/21", 5): 0.7})
    out = placebo_spatial(panel, seed=0)
    assert out["shock"].iloc[0] == 0.7


def test_prev_crop_year() -> None:
    assert _prev_crop_year("2020/21") == "2019/20"
    assert _prev_crop_year("2000/01") == "1999/00"


def test_placebo_temporal_uses_previous_year_shock() -> None:
    panel = _panel(
        {
            ("soy", "MT", "2019/20", 3): 5.0,
            ("soy", "MT", "2020/21", 3): 9.0,  # recebe o shock de 2019/20 (=5.0)
        }
    )
    out = placebo_temporal(panel)
    assert len(out) == 1  # só 2020/21 tem predecessor
    row = out.iloc[0]
    assert row["ano_agricola"] == "2020/21" and row["shock"] == 5.0


def test_pooled_full_row_selects_unique() -> None:
    res = pd.DataFrame(
        {
            "scope": ["full", "dev", "full"],
            "test": ["h1a:pooled", "h1a:pooled:dev", "h1a:crop=soy"],
            "beta": [-0.06, -0.05, -0.07],
            "boot_pvalue": [0.01, 0.2, 0.03],
        }
    )
    row = pooled_full_row(res)
    assert row["beta"] == -0.06


def test_pooled_full_row_requires_exactly_one() -> None:
    res = pd.DataFrame({"scope": ["dev"], "test": ["h1a:pooled:dev"], "beta": [0.0]})
    with pytest.raises(ValueError, match="1 linha pooled"):
        pooled_full_row(res)
