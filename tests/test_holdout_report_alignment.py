"""Alinhamento do relatório descritivo com os artefatos selados (D-075).

O relatório do D-073 rodou pela primeira vez depois do selo da tentativa 2 e falhou em dois
pontos puramente estruturais, nenhum deles regra pré-registrada:

1. lia ``metrics["daily"]`` quando a série mora sob ``payload`` (envelope dos artefatos);
2. convertia o ``RangeIndex`` do parquet de controles em data, virando epoch 1970 — o
   ``reindex`` devolvia NaN e as métricas de excesso saíam NaN **em silêncio**.

O segundo é o perigoso: NaN publicado tem cara de resultado. Estes testes travam o
alinhamento contra o mesmo critério do bloco 5 selado e exigem falha alta, não NaN.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from quantagro.backtest.holdout_report import _daily_frame, build_report
from quantagro.backtest.holdout_spec import REQUIRED_INPUTS, WORK_DIR

WORK = Path(WORK_DIR)
SEALED = (WORK / "11_seal.json").exists()
sealed_only = pytest.mark.skipif(not SEALED, reason="exige a rodada única já selada")

# `data/interim/` e `data/processed/` não vão para o git (só os manifestos vão), então na CI
# nem os inputs nem os artefatos selados existem. Estes testes são de alinhamento contra dado
# real e só têm sentido onde o dado real está.
HAS_CONTROLS = Path(REQUIRED_INPUTS["h4_controls"]).is_file()
controls_only = pytest.mark.skipif(not HAS_CONTROLS, reason="exige o parquet de controles H4 local")


def test_serie_diaria_e_lida_de_dentro_do_envelope():
    envelope = {
        "name": "portfolio_metrics",
        "payload": {"daily": [{"date": "2021-01-08", "net_return": 0.001}]},
    }
    frame = _daily_frame(envelope)
    assert list(frame.columns) == ["net_return"]
    assert frame.index[0] == pd.Timestamp("2021-01-08")


def test_serie_diaria_sem_envelope_continua_funcionando():
    """Tolerância deliberada: o adaptador não pode depender do formato do envelope."""
    frame = _daily_frame({"daily": [{"date": "2021-01-08", "net_return": 0.001}]})
    assert frame.index[0] == pd.Timestamp("2021-01-08")


@controls_only
def test_controles_tem_a_data_em_ref_date_e_nao_no_indice():
    """A causa raiz: o parquet nunca teve índice de data."""
    controls = pd.read_parquet(REQUIRED_INPUTS["h4_controls"])
    assert not isinstance(controls.index, pd.DatetimeIndex)
    assert "ref_date" in controls.columns
    assert "risk_free" in controls.columns


@sealed_only
@controls_only
def test_relatorio_nao_publica_metrica_de_excesso_em_nan():
    """Se o benchmark não alinhar, o relatório precisa FALHAR — nunca devolver NaN."""
    report = build_report(".")
    risco = report["risk"]
    for chave in ("excess_sharpe", "sortino", "beta_vs_market", "downside_deviation"):
        valor = float(risco[chave])
        assert valor == valor, f"{chave} saiu NaN: benchmark desalinhado passou silencioso"
    por_ano = report["crop_year_performance"]["per_crop_year"]
    for ano, bloco in por_ano.items():
        valor = float(bloco["excess_sharpe"])
        assert valor == valor, f"excess_sharpe NaN em {ano}"


@sealed_only
@controls_only
def test_benchmark_do_relatorio_e_a_mesma_serie_do_h4_selado():
    """O risk-free do relatório tem de ser idêntico ao que a regressão H4 já usou."""
    controls = pd.read_parquet(REQUIRED_INPUTS["h4_controls"]).copy()
    controls["ref_date"] = pd.to_datetime(controls["ref_date"]).dt.normalize()
    controls = controls.set_index("ref_date").sort_index()

    metrics = json.loads((WORK / "10_metrics.json").read_text(encoding="utf-8"))
    daily = _daily_frame(metrics)
    alinhado = controls["risk_free"].reindex(daily.index)
    assert not alinhado.isna().any()
    assert len(alinhado) == len(daily)
