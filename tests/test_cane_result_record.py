"""Tripwires do registro imutável da primeira execução da cana (D-051)."""

import json
from pathlib import Path


def test_registro_preserva_pre_registro_veredito_e_limitacoes():
    record = json.loads(Path("data/reference/cane_h1_result_v1.json").read_text())
    assert record["decision"] == "D-051"
    assert record["preregistration_commit"].startswith("9b7e505")
    assert record["executable_contract_commit"].startswith("51d52c1")
    assert record["equity_returns_loaded"] is False
    primary = record["primary_maturation_atr"]
    assert primary["passed"] is True
    assert primary["pooled_beta"] > 0
    assert primary["positive_leave_one_out"] == 8
    assert primary["positive_ufs"] == 5
    assert primary["pvalue_two_sided"] > 0.10
    assert primary["cluster_bootstrap_pvalue_two_sided"] > 0.10
    assert len(record["limitations"]) >= 3
