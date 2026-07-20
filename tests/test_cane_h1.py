"""Testes do portão físico da cana pré-registrado em D-050."""

import numpy as np
import pandas as pd

from quantagro.stats.cane_h1 import EXPECTED_CROP_YEARS, EXPECTED_UFS, cane_h1_verdict, run_cane_h1


def _panel(beta=0.12, seed=19):
    rng = np.random.default_rng(seed)
    rows = []
    for year in EXPECTED_CROP_YEARS:
        for uf in EXPECTED_UFS:
            for lev in (2, 3, 4):
                shock = rng.normal()
                rows.append(
                    {
                        "phase": "maturation",
                        "uf": uf,
                        "ano_agricola": year,
                        "id_levantamento": lev,
                        "shock": shock,
                        "logrev": beta * shock + rng.normal(scale=0.005),
                    }
                )
    return pd.DataFrame(rows)


def test_resultado_contem_5_ufs_8_safras_e_8_loo():
    result = run_cane_h1(_panel())
    assert len(result.query("scope == 'pooled'")) == 1
    assert set(result.query("scope == 'uf'")["key"]) == set(EXPECTED_UFS)
    assert len(result.query("scope == 'crop_year'")) == 8
    assert len(result.query("scope == 'leave_one_crop_year_out'")) == 8
    assert int(result.query("scope == 'pooled'").iloc[0]["n_clusters"]) == 8


def test_veredito_aprova_direcao_estavel_sem_consultar_pvalor():
    verdict = cane_h1_verdict(run_cane_h1(_panel()))
    assert verdict.passed
    assert verdict.pooled_beta > 0
    assert verdict.positive_leave_one_out == 8
    assert verdict.positive_ufs == 5


def test_veredito_reprova_sinal_negativo():
    verdict = cane_h1_verdict(run_cane_h1(_panel(beta=-0.12)))
    assert not verdict.passed
    assert verdict.pooled_beta < 0


def test_veredito_exige_estabilidade_loo_e_uf():
    rows = [{"scope": "pooled", "key": "all", "beta": 0.1}]
    rows += [
        {"scope": "leave_one_crop_year_out", "key": year, "beta": 0.1 if i < 5 else -0.1}
        for i, year in enumerate(EXPECTED_CROP_YEARS)
    ]
    rows += [
        {"scope": "uf", "key": uf, "beta": 0.1 if i < 2 else -0.1}
        for i, uf in enumerate(EXPECTED_UFS)
    ]
    verdict = cane_h1_verdict(pd.DataFrame(rows))
    assert not verdict.passed
    assert verdict.positive_leave_one_out == 5
    assert verdict.positive_ufs == 2
