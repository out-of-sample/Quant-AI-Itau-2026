"""Registro PIT de saídas terminais do holdout."""

import json
from pathlib import Path

import pandas as pd
import pytest

from quantagro.backtest.terminal_events import load_terminal_exits


def test_registro_real_fecha_jbs_e_brf_nos_ultimos_pregoes():
    exits = load_terminal_exits("data/reference/holdout_terminal_events_v1.json")
    assert exits == {
        "JBSS3": pd.Timestamp("2025-06-06"),
        "BRFS3": pd.Timestamp("2025-09-22"),
    }


def test_politica_terminal_divergente_falha(tmp_path: Path):
    source = Path("data/reference/holdout_terminal_events_v1.json")
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["policy"] = "seguir_sucessor"
    path = tmp_path / "terminal.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="política"):
        load_terminal_exits(path)
