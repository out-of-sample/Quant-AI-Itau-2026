"""Análise de poder do teste de reação das ações (D-045).

Pergunta: qual a probabilidade de o teste no holdout dar um **veredito claro** (rejeitar na
direção certa, α=0,10 unilateral) em função do tamanho do efeito real, do nº de nomes e do nº de
anos-safra? O gargalo é o nº de **eventos independentes** (anos-safra) — o holdout tem 5 fixos
(2020/21–2024/25); o único ajuste operável é o nº de nomes (expansão de universo).

Monte Carlo do teste efetivo: por ano-safra, um choque; por nome, score = sinal×choque; retorno
= β·score + comum + ruído idiossincrático. Demeaning na seção transversal (remove o comum/
mercado) e SE agrupado por ano-safra — exatamente o `run_equity_reaction`. Calibração: |β|≈0,09 é
o efeito observado no desenvolvimento (D-043); ruído σ do retorno de ~21 pregões varrido em
[0,10; 0,16]. Resultado e leitura em `docs/07` D-045.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

ALPHA = 0.10
N_SIM = 4000


def power(
    beta: float, n_names: int, n_years: int, sigma: float, seed: int = 1
) -> tuple[float, float]:
    """Poder e meia-largura do IC 90% do teste demeanado-cluster, via Monte Carlo.

    ``beta`` efeito real (retorno por unidade de score); ``n_names`` nomes (metade produtor,
    metade processador); ``n_years`` anos-safra (clusters); ``sigma`` desvio idiossincrático do
    retorno forward. Um choque por ano-safra (datas extras no ano são ~correlacionadas: conta
    como poder efetivo, não inflado).
    """
    rng = np.random.default_rng(seed)
    nplus = n_names // 2
    signs = np.array([1.0] * nplus + [-1.0] * (n_names - nplus))
    rej = 0
    ses = []
    for _ in range(N_SIM):
        xs, ys, groups = [], [], []
        for c in range(n_years):
            shock = rng.normal()
            score = signs * shock
            common = rng.normal() * 0.05  # componente de mercado, removido pelo demeaning
            ret = beta * score + common + rng.normal(size=n_names) * sigma
            xs.append(score - score.mean())
            ys.append(ret - ret.mean())
            groups.append(np.full(n_names, c))
        x = np.concatenate(xs)
        y = np.concatenate(ys)
        g = np.concatenate(groups)
        sxx = float(x @ x)
        if sxx <= 0:
            continue
        b = float(x @ y) / sxx
        resid = y - b * x
        meat = sum(float((x[g == c] * resid[g == c]).sum()) ** 2 for c in range(n_years))
        se = np.sqrt(meat / sxx**2) * np.sqrt(
            n_years / (n_years - 1)
        )  # correção de poucos clusters
        t = b / se
        if np.sign(b) == np.sign(beta) and stats.t.sf(abs(t), n_years - 1) < ALPHA:
            rej += 1
        ses.append(se)
    return rej / N_SIM, float(np.median(ses)) * 1.645


def main() -> None:
    print(
        "Poder = P(veredito claro na direção certa, α=0,10 unilateral). Holdout = 5 anos-safra.\n"
    )
    print(f"{'β':>5} {'nomes':>6} {'anos':>5} {'σ.10':>6} {'σ.13':>6} {'σ.16':>6} {'IC±':>7}")
    for beta in (0.09, 0.05, 0.03):
        for years in (5, 10):
            for names in (4, 6, 8, 12):
                p10, ci = power(beta, names, years, 0.10)
                p13, _ = power(beta, names, years, 0.13)
                p16, _ = power(beta, names, years, 0.16)
                row = f"{beta:>5.2f} {names:>6} {years:>5}"
                print(f"{row} {p10:>5.0%} {p13:>6.0%} {p16:>6.0%} {ci:>7.3f}")
        print()
    print("Leitura: β grande (0,09, o do dev) => conclusivo já com 4 nomes; β moderado (0,05) =>")
    print(
        "~8 nomes chegam a ~80-90%; β pequeno (0,03) => inconclusivo mesmo expandido (faltam anos)."
    )


if __name__ == "__main__":
    main()
