"""Ensaio geral do pipeline da rodada única sobre inputs SINTÉTICOS.

Motivação (D-074): a primeira tentativa de rodada morreu no bloco 9 porque a grade de
horizonte congelada em D-068 era inviável no calendário real da B3 — dois blocos de anos-safra
vizinhos se sobrepunham em uma única fronteira. Nenhum teste pegou isso porque o smoke do dev
roda um ano-safra e só o horizonte base, e os testes unitários usavam calendários sintéticos
sem feriados, onde a colisão não aparece.

Estes testes fecham essa lacuna de duas formas:

1. `test_grade_de_horizonte_e_viavel_no_calendario_real` verifica, contra o calendário real de
   pregões, que **toda** combinação congelada de horizonte × ano-safra produz blocos que não se
   sobrepõem. É o teste que teria evitado a tentativa perdida.
2. `test_pipeline_completo_roda_com_inputs_sinteticos` executa `run_all_analyses` de ponta a
   ponta com dados fabricados, exercitando os blocos 0–10 inclusive os que a tentativa
   real nunca alcançou (atribuição e serialização).

Os dados são inventados; nenhum retorno, sinal ou artefato do holdout é lido. O calendário é
metadado público da bolsa (quais dias houve pregão), não resultado.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantagro.backtest.holdout_analysis import HoldoutInputs, run_all_analyses
from quantagro.backtest.holdout_spec import (
    ANALYSIS_STEPS,
    H4_EXTENDED_CONTROLS,
    H4_RISK_FREE_COLUMN,
    HOLDING_SENSITIVITY_SESSIONS,
)
from quantagro.backtest.operational_spec import HOLDING_SESSIONS, build_trade_blocks
from quantagro.backtest.strategy_spec import (
    GRAIN_NAMES,
    HOLDOUT_CROP_YEARS,
    UNIVERSE,
)

FIXTURE = Path(__file__).parent / "fixtures" / "b3_sessions_2020_2025.csv"


def real_sessions() -> pd.DatetimeIndex:
    """Pregões reais da B3 entre 02/01/2020 e 30/12/2025, extraídos do COTAHIST."""
    return pd.DatetimeIndex(pd.read_csv(FIXTURE)["date"]).normalize()


def _all_blocks(sessions: pd.DatetimeIndex, holding: int):
    return [
        block
        for crop_year in HOLDOUT_CROP_YEARS
        for block in build_trade_blocks(sessions, crop_year, holding_sessions=holding)
    ]


def _overlaps(blocks) -> list[tuple[str, int, str, int]]:
    ordered = sorted(blocks, key=lambda b: b.execution_date)
    bad = []
    for first, second in zip(ordered, ordered[1:], strict=False):
        if second.execution_date < first.exit_date:
            bad.append((first.crop_year, first.sequence, second.crop_year, second.sequence))
    return bad


# --------------------------------------------------------------------- viabilidade da grade


def test_calendario_fixture_bate_com_o_contrato():
    sessions = real_sessions()
    assert len(sessions) == 1495
    assert sessions.is_monotonic_increasing and not sessions.has_duplicates
    assert str(sessions[0].date()) == "2020-01-02"
    assert str(sessions[-1].date()) == "2025-12-30"


@pytest.mark.parametrize("holding", (HOLDING_SESSIONS, *HOLDING_SENSITIVITY_SESSIONS))
def test_grade_de_horizonte_e_viavel_no_calendario_real(holding):
    """Nenhum horizonte congelado pode gerar blocos sobrepostos no calendário real.

    Regressão direta da falha de D-074: com 42 pregões, o bloco #5 de 2023/24 terminava em
    10/01/2025 enquanto o bloco #0 de 2024/25 executava em 08/01/2025.
    """
    blocks = _all_blocks(real_sessions(), holding)
    assert blocks, f"horizonte {holding} não produziu blocos"
    assert _overlaps(blocks) == [], f"horizonte {holding} gera blocos sobrepostos"


def test_horizonte_de_42_permanece_inviavel_e_por_isso_saiu_da_grade():
    """Registro executável do motivo da remoção — não é opinião, é aritmética de calendário."""
    bad = _overlaps(_all_blocks(real_sessions(), 42))
    assert bad, "se 42 passou a caber, a remoção precisa ser reavaliada em decisão pública"
    assert 42 not in HOLDING_SENSITIVITY_SESSIONS


# --------------------------------------------------------------------- ensaio ponta a ponta


def _synthetic_inputs(seed: int = 11) -> HoldoutInputs:
    """Inputs fabricados com os schemas civis exatos, sobre o calendário real."""
    rng = np.random.default_rng(seed)
    sessions = real_sessions()

    returns = pd.DataFrame(
        rng.normal(0.0003, 0.018, (len(sessions), len(UNIVERSE))),
        index=sessions,
        columns=list(UNIVERSE),
    )

    state = pd.DataFrame(
        [
            {
                "date": date,
                "ticker": ticker,
                "traded": True,
                "seasoned": True,
                "adtv_brl": 5.0e7,
                "eligible": True,
                "reason": "ok",
            }
            for date in sessions
            for ticker in UNIVERSE
        ]
    )

    horizons = (HOLDING_SESSIONS, *HOLDING_SENSITIVITY_SESSIONS)
    decisions = sorted(
        {block.decision_date for h in horizons for block in _all_blocks(sessions, h)}
    )
    lags = (7, 14, 21)
    grain_rows, cane_rows = [], []
    for date in decisions:
        for lag in lags:
            grain_rows.append(
                {"decision_date": date, "total_signal_lag_days": lag}
                | {name: float(rng.normal()) for name in GRAIN_NAMES}
            )
            cane_rows.append(
                {
                    "decision_date": date,
                    "total_signal_lag_days": lag,
                    "shock": float(rng.normal()),
                    "status": "ok",
                }
            )

    h4 = pd.DataFrame(
        {name: rng.normal(0.0002, 0.01, len(sessions)) for name in H4_EXTENDED_CONTROLS}
        | {H4_RISK_FREE_COLUMN: np.full(len(sessions), 0.0004)},
        index=sessions,
    )
    h4.index.name = "ref_date"
    h4["avail_date"] = sessions

    h5 = pd.DataFrame(
        rng.normal(0.0, 1.0, (len(decisions), len(GRAIN_NAMES))),
        index=pd.DatetimeIndex(decisions),
        columns=list(GRAIN_NAMES),
    )

    return HoldoutInputs(
        returns=returns,
        market_state=state,
        grain_scores=pd.DataFrame(grain_rows),
        cane_signal=pd.DataFrame(cane_rows),
        h4_controls=h4,
        h5_geographic_scores=h5,
        terminal_exits={},
    )


def test_pipeline_completo_roda_com_inputs_sinteticos():
    """Blocos 0–10 executam de ponta a ponta, incluindo os que a tentativa real não alcançou."""
    artifacts = run_all_analyses(_synthetic_inputs(), {"ready": True, "synthetic": True})
    assert len(artifacts) == len(ANALYSIS_STEPS) - 1
    assert all(isinstance(item, dict) for item in artifacts)


def test_pipeline_sintetico_e_serializavel_em_json():
    """O bloco 10 publica série diária e pesos; se não serializa, o selo nunca acontece."""
    artifacts = run_all_analyses(_synthetic_inputs(), {"ready": True, "synthetic": True})
    for step, payload in zip(ANALYSIS_STEPS[:-1], artifacts, strict=True):
        texto = json.dumps(payload, ensure_ascii=False, default=str)
        assert texto, f"bloco {step.order} ({step.output}) serializou vazio"


def test_ensaio_sintetico_nao_le_nenhum_input_real(monkeypatch):
    """Garante que o ensaio é realmente cego: qualquer leitura de parquet falharia."""

    def proibido(*args, **kwargs):  # pragma: no cover - só dispara em regressão
        raise AssertionError("o ensaio sintético tentou ler parquet real")

    monkeypatch.setattr(pd, "read_parquet", proibido)
    artifacts = run_all_analyses(_synthetic_inputs(), {"ready": True, "synthetic": True})
    assert len(artifacts) == len(ANALYSIS_STEPS) - 1
