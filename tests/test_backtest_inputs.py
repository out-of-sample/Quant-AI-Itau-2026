"""Testes dos adaptadores PIT de features para a agenda da Fase 4."""

import pandas as pd
import pytest

import quantagro.backtest.inputs as inputs
from quantagro.backtest.operational_spec import HoldoutLockedError, TradeBlock


def _block(crop_year="2018/19", start="2019-01-07"):
    sessions = pd.bdate_range(start, periods=23)
    return TradeBlock(crop_year, 0, sessions[0], sessions[1], sessions[22])


def _registry(date):
    rows = []
    exposures = {
        "AGRO3": {"soy": 0.7, "corn_second": 0.3},
        "BRFS3": {"soy": -0.5, "corn_second": -0.5},
    }
    for ticker, crops in exposures.items():
        for crop, exposure in crops.items():
            rows.append(
                {
                    "exposure_id": ticker,
                    "ticker": ticker,
                    "crop": crop,
                    "avail_date": date - pd.Timedelta(days=1),
                    "exposure": exposure,
                }
            )
    return pd.DataFrame(rows)


def test_materializa_score_grao_sem_renormalizar_janela_nao_iniciada(monkeypatch):
    block = _block()

    def fake_shock(*args, **kwargs):
        return pd.DataFrame(
            [
                {"level": "national", "crop": "soy", "status": "ok", "shock": 2.0},
                {
                    "level": "national",
                    "crop": "corn_second",
                    "status": "window_not_started",
                    "shock": None,
                },
            ]
        )

    monkeypatch.setattr(inputs, "shock_asof", fake_shock)
    out = inputs.materialize_grain_raw_scores(
        [block],
        _registry(block.decision_date),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        2000,
    )
    assert out.loc[block.decision_date, "AGRO3"] == pytest.approx(1.4)
    assert out.loc[block.decision_date, "BRFS3"] == pytest.approx(-1.0)
    assert pd.isna(out.loc[block.decision_date, "SLCE3"])


def test_buraco_tecnico_de_shock_nao_vira_zero(monkeypatch):
    block = _block()
    monkeypatch.setattr(
        inputs,
        "shock_asof",
        lambda *args, **kwargs: pd.DataFrame(
            [
                {"level": "national", "crop": "soy", "status": "ok", "shock": 1.0},
                {"level": "national", "crop": "corn_second", "status": "ok", "shock": None},
            ]
        ),
    )
    with pytest.raises(ValueError, match="técnico inválido"):
        inputs.materialize_grain_raw_scores(
            [block],
            _registry(block.decision_date),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            2000,
        )


def test_cana_agrega_cinco_ufs_com_peso_conab(monkeypatch):
    block = _block()
    values = {"GO": 1.0, "MG": 2.0, "MS": 3.0, "PR": 4.0, "SP": 5.0}
    monkeypatch.setattr(
        inputs,
        "uf_cane_shock_asof",
        lambda t, year, spec, *args: {"status": "ok", "shock": values[spec.uf]},
    )
    monkeypatch.setattr(
        inputs,
        "conab_uf_weights",
        lambda *args: pd.Series({"GO": 0.1, "MG": 0.1, "MS": 0.1, "PR": 0.1, "SP": 0.6}),
    )
    out = inputs.materialize_cane_signal(
        [block], pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), 2000
    )
    assert out.loc[block.decision_date, "status"] == "ok"
    assert out.loc[block.decision_date, "shock"] == pytest.approx(4.0)


def test_cana_parcial_falha_e_todas_nao_iniciadas_ficam_fora(monkeypatch):
    block = _block()

    def partial(t, year, spec, *args):
        status = "ok" if spec.uf == "SP" else "window_not_started"
        return {"status": status, "shock": 1.0 if status == "ok" else None}

    monkeypatch.setattr(inputs, "uf_cane_shock_asof", partial)
    with pytest.raises(ValueError, match="cobertura parcial"):
        inputs.materialize_cane_signal(
            [block], pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), 2000
        )

    monkeypatch.setattr(
        inputs,
        "uf_cane_shock_asof",
        lambda *args: {"status": "window_not_started", "shock": None},
    )
    out = inputs.materialize_cane_signal(
        [block], pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), 2000
    )
    assert out.loc[block.decision_date, "status"] == "window_not_started"
    assert pd.isna(out.loc[block.decision_date, "shock"])


def test_holdout_falha_antes_de_calcular_feature(monkeypatch):
    block = _block("2020/21", "2021-01-07")
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("feature não deveria ser calculada")

    monkeypatch.setattr(inputs, "shock_asof", forbidden)
    with pytest.raises(HoldoutLockedError, match="Fase 6"):
        inputs.materialize_grain_raw_scores(
            [block], pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), 2000
        )
    assert not called
