"""Testes da camada de inferência (stats/inference.py).

BH-FDR conferido contra statsmodels; OLS cluster/HAC contra beta conhecido; bootstraps sãos e
com guardas de amostra pequena. É o núcleo estatístico do portão — mentir aqui contamina tudo.
"""

import numpy as np
import pytest
from statsmodels.stats.multitest import multipletests

from quantagro.stats import (
    bh_fdr,
    cluster_bootstrap,
    moving_block_bootstrap,
    ols_cluster,
    ols_hac,
)


def _data(seed=1, n=200, slope=-0.8):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n)
    g = np.repeat(np.arange(10), n // 10)
    y = slope * x + rng.normal(scale=0.5, size=n) + g * 0.01
    return x, y, g


def test_bh_fdr_matches_statsmodels():
    p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
    out = bh_fdr(p, alpha=0.05)
    rej, q, *_ = multipletests(p, alpha=0.05, method="fdr_bh")
    assert np.allclose(out["qvalue"], q)
    assert (out["reject"].to_numpy() == rej).all()


def test_bh_fdr_preserva_ordem_de_entrada():
    p = [0.5, 0.001, 0.2]
    out = bh_fdr(p)
    assert out["pvalue"].tolist() == p
    # o menor p (índice 1) tem o menor q
    assert out["qvalue"].iloc[1] == out["qvalue"].min()


def test_bh_fdr_rejeita_entrada_invalida():
    with pytest.raises(ValueError):
        bh_fdr([])
    with pytest.raises(ValueError):
        bh_fdr([0.1, 1.5])


def test_ols_cluster_recupera_beta_e_conta_clusters():
    x, y, g = _data()
    r = ols_cluster(x, y, g, "t")
    assert r.beta == pytest.approx(-0.8, abs=0.05)
    assert r.n_clusters == 10
    assert r.nobs == 200
    assert r.pvalue < 1e-6
    assert r.ci_low < r.beta < r.ci_high


def test_ols_hac_beta_correto():
    x, y, _ = _data()
    r = ols_hac(x, y, maxlags=4, name="hac")
    assert r.beta == pytest.approx(-0.8, abs=0.05)
    assert r.cov_type == "HAC(4)"
    assert r.n_clusters is None


def test_ols_descarta_nan():
    x, y, g = _data(n=100)
    x = x.copy()
    x[0] = np.nan
    r = ols_cluster(x, y, g, "t")
    assert r.nobs == 99


def test_ols_amostra_pequena_falha_alto():
    with pytest.raises(ValueError):
        ols_cluster([1.0, 2.0], [1.0, 2.0], [0, 1])


def test_cluster_bootstrap_sinal_e_ic():
    x, y, g = _data()
    out = cluster_bootstrap(x, y, g, n_boot=1000)
    assert out["beta"] == pytest.approx(-0.8, abs=0.05)
    assert out["ci_high"] < 0  # efeito negativo forte
    assert out["pvalue"] < 0.05
    assert out["n_clusters"] == 10


def test_moving_block_bootstrap_roda_e_valida_bloco():
    x, y, _ = _data(n=60)
    out = moving_block_bootstrap(x, y, block=5, n_boot=1000)
    assert out["beta"] == pytest.approx(-0.8, abs=0.1)
    with pytest.raises(ValueError):
        moving_block_bootstrap(x, y, block=0)
    with pytest.raises(ValueError):
        moving_block_bootstrap(x, y, block=len(x) + 1)


def test_bootstrap_determinismo_por_seed():
    x, y, g = _data()
    a = cluster_bootstrap(x, y, g, n_boot=500, seed=42)
    b = cluster_bootstrap(x, y, g, n_boot=500, seed=42)
    assert a == b
