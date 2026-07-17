"""Testes de H1a (stats/h1a.py) — revisão log e montagem da regressão.

A integração com ``Shock`` já é coberta por test_shock.py; aqui trava-se o que H1a acrescenta:
a revisão log acumulada desde o primeiro levantamento e as regressões agrupadas por safra com
as sub-amostras dev/holdout (D-029/D-030).
"""

import numpy as np
import pandas as pd
import pytest

from quantagro.stats.h1a import DEV_LAST_BASE, _revisions, run_h1a


def _stamped_conab():
    # soja/MT, duas safras, produção decrescente (seca) — revisão log conferível na mão.
    rows = []
    for ano, prods in {"2018/19": [100, 95, 90], "2020/21": [200, 180, 170]}.items():
        for lev, p in enumerate(prods, start=1):
            rows.append(
                {
                    "crop": "soy",
                    "uf": "MT",
                    "ano_agricola": ano,
                    "id_levantamento": lev,
                    "producao_mil_t": float(p),
                    "avail_date": pd.Timestamp(2019, 1, 1) + pd.Timedelta(days=30 * lev),
                }
            )
    return pd.DataFrame(rows)


def test_revisoes_log_acumuladas_desde_o_primeiro_lev():
    rev = _revisions(_stamped_conab())
    # base = lev 1; lev 2 e lev 3 geram revisão. 2 safras × 2 = 4 linhas.
    assert len(rev) == 4
    r = rev[(rev.ano_agricola == "2018/19") & (rev.id_levantamento == 3)]
    assert float(r["logrev"].iloc[0]) == pytest.approx(np.log(90 / 100))
    assert (rev["id_levantamento"] != rev["base_lev"]).all()


def test_revisoes_ignora_producao_zero_e_serie_curta():
    conab = _stamped_conab()
    # zera todos menos o primeiro de uma safra ⇒ série < 2 ⇒ descartada
    conab.loc[(conab.ano_agricola == "2018/19") & (conab.id_levantamento > 1), "producao_mil_t"] = (
        0.0
    )
    rev = _revisions(conab)
    assert set(rev.ano_agricola.unique()) == {"2020/21"}


def _synthetic_panel(seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for base in range(2017, 2025):
        ano = f"{base}/{(base + 1) % 100:02d}"
        for crop in ("soy", "corn_second"):
            for uf in ("MT", "PR"):
                for lev in range(2, 8):
                    shock = rng.normal()
                    logrev = -0.1 * shock + rng.normal(scale=0.02)
                    rows.append(
                        {
                            "crop": crop,
                            "uf": uf,
                            "ano_agricola": ano,
                            "id_levantamento": lev,
                            "shock": shock,
                            "logrev": logrev,
                            "base_year": base,
                            "sample": "dev" if base <= DEV_LAST_BASE else "holdout",
                        }
                    )
    return pd.DataFrame(rows)


def test_run_h1a_recupera_sinal_negativo_e_produz_escopos():
    res = run_h1a(_synthetic_panel())
    pooled_full = res[(res.test == "h1a:pooled") & (res.scope == "full")]
    assert len(pooled_full) == 1
    assert float(pooled_full["beta"].iloc[0]) < 0  # estresse ⇒ revisão para baixo
    assert float(pooled_full["pvalue"].iloc[0]) < 0.05
    # escopos full/dev/holdout presentes para o agrupado
    scopes = set(res[res.test.str.startswith("h1a:pooled")]["scope"])
    assert {"full", "dev", "holdout"} <= scopes
    # por cultura também
    assert "h1a:crop=soy" in set(res["test"])
