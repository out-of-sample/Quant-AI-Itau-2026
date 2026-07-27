"""Testes do pré-registro do relatório descritivo do holdout.

As fórmulas são exercitadas em séries sintéticas — nenhum retorno do holdout é lido.
"""

from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
import pytest

from quantagro.backtest.holdout_report import build_report
from quantagro.backtest.holdout_report_spec import (
    ANNUALIZATION_SESSIONS,
    BENCHMARK_PRIMARY,
    BENCHMARK_REJECTED,
    HEADLINE_COST_SCENARIO,
    IN_RUN_VARIANTS,
    REPORT_IS_DESCRIPTIVE,
    TRIAL_LEDGER,
    crop_year_metrics,
    deflated_sharpe_ratio,
    excess_sharpe,
    expected_max_sharpe,
    n_trials,
    report_spec_payload,
    tail_risk_metrics,
    trial_sharpe_dispersion,
)
from quantagro.backtest.holdout_spec import SPEC_FILES, canonical_spec_payload
from quantagro.backtest.operational_spec import HOLDOUT_CROP_YEARS


def _synthetic_daily(seed: int = 7, sessions_per_year: int = 21) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    equity = 500_000.0
    for crop_year in HOLDOUT_CROP_YEARS:
        for _ in range(sessions_per_year):
            net = float(rng.normal(0.0006, 0.01))
            equity *= 1.0 + net
            rows.append(
                {
                    "net_return": net,
                    "net_pnl_brl": equity * net,
                    "equity_brl": equity,
                    "return_crop_year": crop_year,
                    "gross_exposure": 1.0,
                    "net_exposure": 0.0,
                }
            )
    index = pd.bdate_range("2020-01-02", periods=len(rows))
    return pd.DataFrame(rows, index=index)


def _flat_rf(index: pd.Index, value: float = 0.0002) -> pd.Series:
    return pd.Series(value, index=index)


# ---------------------------------------------------------------- pré-registro no contrato


def test_report_spec_entra_no_contrato_congelado():
    """O pré-registro só vale se for verificável por máquina: precisa estar no hash."""
    assert "src/quantagro/backtest/holdout_report_spec.py" in SPEC_FILES
    assert canonical_spec_payload()["report"] == dict(report_spec_payload())


def test_relatorio_e_descritivo_e_nao_veta():
    assert REPORT_IS_DESCRIPTIVE is True
    payload = report_spec_payload()
    assert "veto" not in json.dumps(payload).lower()


def test_manchete_fica_no_cenario_base_e_ibov_e_recusado():
    """O cenário e o comparador ficam escolhidos antes do resultado, não depois."""
    assert HEADLINE_COST_SCENARIO == "base"
    assert "ibovespa" in BENCHMARK_REJECTED
    assert BENCHMARK_PRIMARY not in BENCHMARK_REJECTED


def test_contagem_de_tentativas_e_enumerada_e_fixa():
    assert n_trials() == len(TRIAL_LEDGER) + IN_RUN_VARIANTS
    assert n_trials() == 39
    decisions = [key for key, _ in TRIAL_LEDGER]
    assert len(decisions) == len(set(decisions)), "tentativa duplicada no ledger"
    assert all(key.startswith("D-") for key in decisions)
    # As duas tentativas que usaram retorno do dev precisam estar declaradas.
    assert {"D-043", "D-059"}.issubset(set(decisions))


# ---------------------------------------------------------------- métricas por ano-safra


def test_todos_os_anos_safra_aparecem_mesmo_sem_bloco():
    """Regra de honestidade: nenhum ano pode sumir do artefato."""
    daily = _synthetic_daily()
    daily = daily[daily["return_crop_year"] != HOLDOUT_CROP_YEARS[-1]]
    out = crop_year_metrics(daily, _flat_rf(daily.index))
    assert set(out["per_crop_year"]) == set(HOLDOUT_CROP_YEARS)
    assert out["years_reported"] == len(HOLDOUT_CROP_YEARS)
    assert out["years_with_sessions"] == len(HOLDOUT_CROP_YEARS) - 1
    ausente = out["per_crop_year"][HOLDOUT_CROP_YEARS[-1]]
    assert ausente["sessions"] == 0


def test_participacao_de_pnl_por_ano_soma_um():
    daily = _synthetic_daily()
    out = crop_year_metrics(daily, _flat_rf(daily.index))
    shares = [stats["pnl_share"] for stats in out["per_crop_year"].values()]
    assert math.isclose(sum(shares), 1.0, rel_tol=1e-9)
    assert out["worst_crop_year"] in HOLDOUT_CROP_YEARS
    assert out["best_crop_year"] in HOLDOUT_CROP_YEARS


def test_ano_negativo_nao_e_omitido():
    daily = _synthetic_daily()
    alvo = HOLDOUT_CROP_YEARS[1]
    mask = daily["return_crop_year"] == alvo
    daily.loc[mask, "net_return"] = -0.02
    out = crop_year_metrics(daily, _flat_rf(daily.index))
    assert out["per_crop_year"][alvo]["compounded_return"] < 0
    assert out["worst_crop_year"] == alvo
    assert out["years_positive"] < len(HOLDOUT_CROP_YEARS)


def test_serie_sem_ano_safra_falha_alto():
    daily = _synthetic_daily().drop(columns=["return_crop_year"])
    with pytest.raises(ValueError, match="return_crop_year"):
        crop_year_metrics(daily, _flat_rf(daily.index))


# ---------------------------------------------------------------- risco


def test_cvar_nunca_e_melhor_que_var():
    daily = _synthetic_daily()
    risk = tail_risk_metrics(daily, _flat_rf(daily.index))
    assert risk["cvar_95"] <= risk["var_95"]
    assert risk["worst_session"] <= risk["cvar_95"]


def test_beta_recupera_inclinacao_conhecida():
    daily = _synthetic_daily()
    rf = _flat_rf(daily.index)
    mercado = (daily["net_return"] - rf) / 0.5
    risk = tail_risk_metrics(daily, rf, mercado)
    assert math.isclose(risk["beta_vs_market"], 0.5, rel_tol=1e-6)


def test_beta_ausente_quando_nao_ha_controle_de_mercado():
    daily = _synthetic_daily()
    risk = tail_risk_metrics(daily, _flat_rf(daily.index))
    assert math.isnan(risk["beta_vs_market"])


def test_tempo_submerso_em_serie_monotona_e_zero():
    index = pd.bdate_range("2020-01-02", periods=30)
    daily = pd.DataFrame(
        {
            "net_return": 0.001,
            "net_pnl_brl": 1.0,
            "equity_brl": np.cumprod(np.full(30, 1.001)) * 500_000.0,
            "return_crop_year": HOLDOUT_CROP_YEARS[0],
            "gross_exposure": 1.0,
            "net_exposure": 0.0,
        },
        index=index,
    )
    risk = tail_risk_metrics(daily, _flat_rf(index))
    assert risk["max_time_under_water_sessions"] == 0
    assert risk["max_drawdown"] == 0.0


def test_sharpe_de_excesso_difere_do_sharpe_com_rf_zero():
    """O bloco 10 reporta Sharpe com taxa livre de risco zero; o benchmark declarado corrige."""
    daily = _synthetic_daily()
    net = daily["net_return"]
    sem_rf = float(net.mean() / net.std(ddof=1) * math.sqrt(ANNUALIZATION_SESSIONS))
    com_rf = excess_sharpe(net, _flat_rf(daily.index, 0.0004))
    assert com_rf < sem_rf


# ---------------------------------------------------------------- deflated sharpe


def test_mais_tentativas_elevam_a_barra():
    baixo = expected_max_sharpe(0.05, 5)
    alto = expected_max_sharpe(0.05, 500)
    assert alto > baixo > 0


def test_deflated_sharpe_cai_quando_ha_mais_tentativas():
    comum = dict(observed_sharpe=0.08, n_obs=500, skewness=-0.2, excess_kurtosis=2.0)
    poucas = deflated_sharpe_ratio(**comum, trial_sharpe_std=0.03, trials=2)
    muitas = deflated_sharpe_ratio(**comum, trial_sharpe_std=0.03, trials=1000)
    assert poucas["deflated_sharpe_ratio"] > muitas["deflated_sharpe_ratio"]
    assert 0.0 <= muitas["deflated_sharpe_ratio"] <= 1.0


def test_sharpe_nulo_com_muitas_tentativas_nao_convence():
    out = deflated_sharpe_ratio(
        observed_sharpe=0.0,
        n_obs=500,
        skewness=0.0,
        excess_kurtosis=0.0,
        trial_sharpe_std=0.05,
        trials=n_trials(),
    )
    assert out["deflated_sharpe_ratio"] < 0.5


def test_dispersao_ignora_nan_e_exige_duas_variantes():
    assert trial_sharpe_dispersion([1.0]) == 0.0
    assert trial_sharpe_dispersion([]) == 0.0
    limpo = trial_sharpe_dispersion([0.1, 0.2, float("nan")])
    assert math.isclose(limpo, float(np.std([0.1, 0.2], ddof=1)))


# ---------------------------------------------------------------- guarda do executor


def test_relatorio_recusa_rodar_sem_selo(tmp_path):
    (tmp_path / "data" / "processed" / "holdout_v1").mkdir(parents=True)
    with pytest.raises(RuntimeError, match="selo"):
        build_report(tmp_path)
