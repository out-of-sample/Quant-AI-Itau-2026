"""Tripwire das exceções de retorno extremo do build offline."""

import pandas as pd
import pytest
from scripts.build_equity_returns import _validate_extremes


def test_excecao_exige_data_valor_e_tolerancia():
    date = pd.Timestamp("2017-05-22")
    allowed = {date: (-0.3134328358208951, 1e-9)}
    _validate_extremes(pd.Series([-0.3134328358208951], index=[date]), allowed, "JBSS3")

    with pytest.raises(RuntimeError, match="extremo auditado mudou"):
        _validate_extremes(pd.Series([9.0], index=[date]), allowed, "JBSS3")


def test_data_extrema_nao_declarada_falha():
    date = pd.Timestamp("2017-05-23")
    with pytest.raises(RuntimeError, match="exige auditoria"):
        _validate_extremes(pd.Series([-0.5], index=[date]), {}, "JBSS3")
