"""Semântica civil, irreversível e atômica do executor D-072."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

import quantagro.backtest.holdout_executor as executor
from quantagro.backtest.holdout import preflight_holdout
from quantagro.backtest.holdout_spec import (
    ANALYSIS_STEPS,
    AUTHORIZATION_PHRASE,
    RESULT_RECORD,
    RUN_RECORD,
    WORK_DIR,
)
from quantagro.backtest.operational_spec import HoldoutLockedError


def _ready_report():
    base = preflight_holdout()
    return replace(
        base,
        missing_spec_files=(),
        source_manifest_errors=(),
        missing_inputs=(),
        manifest_errors=(),
        run_record_exists=False,
        result_record_exists=False,
        work_dir_exists=False,
        ready=True,
    )


def _artifacts(primary_passed: bool = False) -> list[dict[str, object]]:
    out: list[dict[str, object]] = [{} for _ in range(11)]
    out[1] = {"passed": primary_passed}
    out[2] = {"scenarios": {"base": {"total_return": 0.1}}}
    out[4] = {"climate_arith_return": 0.02}
    out[5] = {"extended": {"passed": True}}
    out[6] = {"geographic": {"died": True}}
    return out


def test_frase_errada_falha_antes_do_preflight(monkeypatch, tmp_path) -> None:
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("preflight não deveria rodar")

    monkeypatch.setattr(executor, "preflight_holdout", forbidden)
    with pytest.raises(HoldoutLockedError, match="frase civil"):
        executor.execute_holdout_once(tmp_path, authorization="não autorizado")
    assert not called
    assert not (tmp_path / RUN_RECORD).exists()


def test_falha_do_primario_nao_interrompe_e_so_publica_depois_do_selo(
    monkeypatch, tmp_path, capsys
) -> None:
    monkeypatch.setattr(executor, "preflight_holdout", lambda root: _ready_report())
    monkeypatch.setattr(executor, "load_holdout_inputs", lambda root: object())
    monkeypatch.setattr(
        executor,
        "run_all_analyses",
        lambda inputs, preflight: _artifacts(primary_passed=False),
    )

    sealed = executor.execute_holdout_once(tmp_path, authorization=AUTHORIZATION_PHRASE)
    assert sealed["status"] == "sealed"
    assert capsys.readouterr().out == ""
    outputs = sorted(path.name for path in (tmp_path / WORK_DIR).iterdir())
    assert outputs == sorted(step.output for step in ANALYSIS_STEPS)
    result = json.loads((tmp_path / RESULT_RECORD).read_text(encoding="utf-8"))
    assert result["conditions"]["primary_hprime_passed"] is False
    assert result["claims"]["oos_strategy_evidence"] is False
    run = json.loads((tmp_path / RUN_RECORD).read_text(encoding="utf-8"))
    assert run["status"] == "sealed"


def test_excecao_consumiu_tentativa_sem_publicar_resultado(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(executor, "preflight_holdout", lambda root: _ready_report())
    monkeypatch.setattr(executor, "load_holdout_inputs", lambda root: object())

    def broken(*args, **kwargs):
        raise RuntimeError("falha sintética")

    monkeypatch.setattr(executor, "run_all_analyses", broken)
    with pytest.raises(RuntimeError, match="falha sintética"):
        executor.execute_holdout_once(tmp_path, authorization=AUTHORIZATION_PHRASE)

    run = json.loads((tmp_path / RUN_RECORD).read_text(encoding="utf-8"))
    assert run["status"] == "failed"
    assert not (tmp_path / RESULT_RECORD).exists()
    assert not (tmp_path / WORK_DIR).exists()

    with pytest.raises(HoldoutLockedError, match="registro da rodada única"):
        executor.execute_holdout_once(tmp_path, authorization=AUTHORIZATION_PHRASE)
