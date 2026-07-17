"""Testes do orquestrador do portão (stats/gate.py) — família, BH-FDR e regra do veredito.

A regra do portão é pré-registrada (D-030): passa só se H1a agrupado tiver β<0 e sobreviver ao
BH-FDR. Estes testes travam as três saídas possíveis (passa, sinal errado, sem significância).
"""

import pandas as pd

from quantagro.stats.gate import apply_fdr, primary_family, verdict


def _h1a_res(pooled_beta, pooled_p):
    rows = [
        {"test": "h1a:pooled", "scope": "full", "beta": pooled_beta, "pvalue": pooled_p},
        {"test": "h1a:crop=soy", "scope": "full", "beta": -0.1, "pvalue": 0.02},
        {"test": "h1a:crop=corn_second", "scope": "full", "beta": -0.05, "pvalue": 0.2},
        {"test": "h1a:pooled", "scope": "dev", "beta": -0.2, "pvalue": 0.3},
    ]
    return pd.DataFrame(rows)


def _h1b_res():
    rows = []
    for crop in ("soy", "corn_second"):
        for h in (3, 4, 5, 6):
            rows.append({"crop": crop, "h": h, "beta": -0.1, "pvalue": 0.5})
    return pd.DataFrame(rows)


def test_primary_family_tem_11_testes_na_ordem():
    fam = primary_family(_h1a_res(-0.15, 0.001), _h1b_res())
    assert len(fam) == 11
    assert fam["test"].iloc[0] == "h1a:pooled"
    assert fam["test"].tolist()[:3] == ["h1a:pooled", "h1a:crop=soy", "h1a:crop=corn_second"]
    # só o escopo full entra na família (dev/holdout ficam fora)
    assert not fam["test"].duplicated().any()


def test_apply_fdr_anexa_qvalue_e_reject():
    fam = apply_fdr(primary_family(_h1a_res(-0.15, 0.001), _h1b_res()))
    assert {"qvalue", "reject"}.issubset(fam.columns)
    assert (fam["qvalue"] >= fam["pvalue"] - 1e-9).all()


def test_veredito_passa_quando_h1a_negativo_e_significativo():
    fam = apply_fdr(primary_family(_h1a_res(-0.15, 0.0005), _h1b_res()))
    v = verdict(fam)
    assert v.passed is True
    assert v.h1a_beta < 0
    assert "confirmado" in v.reason


def test_veredito_falha_com_sinal_errado():
    fam = apply_fdr(primary_family(_h1a_res(0.15, 0.0005), _h1b_res()))
    v = verdict(fam)
    assert v.passed is False
    assert "sinal errado" in v.reason


def test_veredito_falha_sem_significancia():
    # β<0 mas p alto ⇒ não sobrevive ao BH-FDR
    fam = apply_fdr(primary_family(_h1a_res(-0.15, 0.6), _h1b_res()))
    v = verdict(fam)
    assert v.passed is False
    assert not v.reason.startswith("H1a agrupado: β<0")
