"""Governança de tentativas da rodada única (D-074).

A tentativa 1 falhou no bloco 9 por inviabilidade da grade de horizonte, sem publicar nada e
sem que ninguém observasse resultado. A tentativa 2 foi autorizada em decisão pública. Estes
testes travam as três propriedades que tornam essa exceção auditável em vez de arbitrária:

1. a trilha da tentativa 1 é **preservada**, nunca apagada;
2. o próprio contrato declara quantas tentativas houve, então liberar o caminho do registro
   com um `mv` silencioso quebra o hash e trava o preflight;
3. a trava do executor **continua valendo** — uma terceira tentativa exige novo D-NNN.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quantagro.backtest.holdout_executor import _create_run_record_exclusive
from quantagro.backtest.holdout_spec import (
    NEXT_ATTEMPT,
    PRIOR_ATTEMPTS,
    canonical_spec_payload,
)


def test_tentativa_1_esta_arquivada_e_nao_apagada():
    assert len(PRIOR_ATTEMPTS) == 1
    prior = PRIOR_ATTEMPTS[0]
    assert prior["attempt"] == 1
    assert prior["status"] == "failed"
    archived = Path(prior["record"])
    assert archived.exists(), "o registro da tentativa 1 não pode ser apagado"
    payload = json.loads(archived.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["error"] == "blocos sobrepostos"
    assert payload["published_work_dir"] is False


def test_nenhum_resultado_foi_observado_na_tentativa_1():
    """A propriedade que torna a segunda tentativa legítima, verificada e não afirmada."""
    prior = PRIOR_ATTEMPTS[0]
    assert prior["results_observed"] is False
    assert prior["published_work_dir"] is False
    payload = json.loads(Path(prior["record"]).read_text(encoding="utf-8"))
    proibidas = {"artifacts", "results", "claims", "conditions", "metrics"}
    assert not (proibidas & set(payload)), "o registro da falha não pode carregar resultado"
    assert not Path("data/reference/holdout_result_v1.json").exists()


def test_contrato_declara_a_contagem_de_tentativas():
    """Renomear o registro sem declarar aqui quebra o hash lógico — é essa a trava real."""
    payload = canonical_spec_payload()
    assert payload["prior_attempts"] == PRIOR_ATTEMPTS
    assert payload["next_attempt"] == NEXT_ATTEMPT == 2


def test_trava_de_exclusividade_continua_valendo(tmp_path):
    """A primitiva que consome a tentativa segue recusando a segunda criação.

    É isto que garante que a tentativa 3 exigirá novo D-NNN, e não um `mv`.
    """
    run_path = tmp_path / "run_record.json"
    _create_run_record_exclusive(run_path, {"status": "started", "attempt": NEXT_ATTEMPT})
    assert json.loads(run_path.read_text(encoding="utf-8"))["attempt"] == 2
    with pytest.raises(Exception, match="já existe"):
        _create_run_record_exclusive(run_path, {"status": "started"})


def test_registro_da_rodada_carrega_o_numero_da_tentativa(tmp_path):
    """Quem auditar o pacote precisa ver que esta é a tentativa 2, não a 1."""
    run_path = tmp_path / "run_record.json"
    _create_run_record_exclusive(
        run_path,
        {"status": "started", "attempt": NEXT_ATTEMPT, "prior_attempts": list(PRIOR_ATTEMPTS)},
    )
    payload = json.loads(run_path.read_text(encoding="utf-8"))
    assert payload["attempt"] == 2
    assert payload["prior_attempts"][0]["status"] == "failed"
