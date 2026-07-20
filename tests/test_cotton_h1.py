"""Testes do portão direcional H1 do algodão (D-048)."""

import numpy as np
import pandas as pd
import pytest

from quantagro.features.shock_spec import COTTON_WINDOWS
from quantagro.stats.cotton_h1 import (
    _revisions_for_measure,
    cotton_h1_verdict,
    run_cotton_h1,
)
from quantagro.stats.h1a import _window_contract


def _panel(beta=-0.12, seed=7):
    rng = np.random.default_rng(seed)
    rows = []
    for year in ("2022/23", "2023/24", "2024/25"):
        for uf in ("BA", "MT"):
            for lev in range(5, 11):
                shock = rng.normal()
                rows.append(
                    {
                        "crop": "cotton",
                        "uf": uf,
                        "ano_agricola": year,
                        "id_levantamento": lev,
                        "shock": shock,
                        "logrev": beta * shock + rng.normal(scale=0.01),
                    }
                )
    return pd.DataFrame(rows)


def test_contrato_h1_deriva_produto_pluma_e_ufs_do_shock_spec():
    filters, ufs = _window_contract(COTTON_WINDOWS)
    assert filters == {"cotton": ("ALGODAO EM PLUMA", "UNICA")}
    assert ufs == {"cotton": ("BA", "MT")}


def test_resultados_contem_primario_ufs_safras_e_leave_one_out():
    results = run_cotton_h1(_panel())
    assert len(results.query("scope == 'pooled'")) == 1
    assert set(results.query("scope == 'uf'")["key"]) == {"BA", "MT"}
    assert len(results.query("scope == 'crop_year'")) == 3
    assert len(results.query("scope == 'leave_one_crop_year_out'")) == 3
    assert int(results.query("scope == 'pooled'").iloc[0]["n_clusters"]) == 3


def test_veredito_aprova_beta_e_estabilidade_negativos():
    results = run_cotton_h1(_panel())
    verdict = cotton_h1_verdict(results)
    assert verdict.passed
    assert verdict.pooled_beta < 0
    assert verdict.negative_leave_one_out == 3


def test_veredito_reprova_sinal_positivo_sem_consultar_pvalor():
    results = run_cotton_h1(_panel(beta=0.12))
    verdict = cotton_h1_verdict(results)
    assert not verdict.passed
    assert verdict.pooled_beta > 0


def test_veredito_reprova_beta_negativo_sem_estabilidade_leave_one_out():
    results = pd.DataFrame(
        [
            {"scope": "pooled", "key": "all", "beta": -0.1},
            {"scope": "leave_one_crop_year_out", "key": "2022/23", "beta": -0.01},
            {"scope": "leave_one_crop_year_out", "key": "2023/24", "beta": 0.02},
            {"scope": "leave_one_crop_year_out", "key": "2024/25", "beta": 0.03},
        ]
    )
    verdict = cotton_h1_verdict(results)
    assert not verdict.passed
    assert verdict.pooled_beta < 0
    assert verdict.negative_leave_one_out == 1


def test_revisao_de_medida_usa_primeiro_levantamento_positivo_como_base():
    conab = pd.DataFrame(
        {
            "crop": ["cotton"] * 3,
            "uf": ["BA"] * 3,
            "ano_agricola": ["2022/23"] * 3,
            "id_levantamento": [1, 2, 3],
            "area": [100.0, 110.0, 90.0],
        }
    )
    revisions = _revisions_for_measure(conab, "area")
    assert revisions["id_levantamento"].tolist() == [2, 3]
    assert revisions["logrev_measure"].tolist() == pytest.approx([np.log(1.1), np.log(0.9)])
