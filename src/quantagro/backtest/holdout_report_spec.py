"""Pré-registro do relatório descritivo do holdout, anterior à rodada única.

Quatro coisas ficam congeladas aqui, **antes** de qualquer resultado ser observado:

1. `crop_year_metrics` — desempenho por ano-safra, com todos os cinco anos obrigatórios.
2. `tail_risk_metrics` — caracterização de risco do livro, que hoje não existe.
3. o benchmark de performance, declarado e justificado (e o que foi recusado como comparador).
4. `deflated_sharpe_ratio` — correção pelo número de especificações efetivamente testadas,
   com a contagem enumerada e fixada abaixo.

Por que congelar agora. Todas as quatro peças são calculáveis a partir dos artefatos
publicados pelo executor (o bloco 10 já publica a série diária, os pesos e a atribuição do
cenário base) e da série livre de risco, que já é input atestado de H4. Nada aqui altera o
que a rodada calcula. O que muda, e é justamente o ponto, é que escolher a fórmula, a janela
ou o comparador **depois** de ver o resultado seria seleção posterior disfarçada de método.

Estatuto: este relatório é **descritivo**. Ele não veta, não promove e não altera nenhum dos
claims congelados em D-068. Um resultado ruim aqui não invalida o teste primário, e um
resultado bom aqui não o corrobora.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from .operational_spec import HOLDOUT_CROP_YEARS

__all__ = [
    "ANNUALIZATION_SESSIONS",
    "BENCHMARK_PRIMARY",
    "BENCHMARK_REJECTED",
    "BENCHMARK_SECONDARY",
    "DDOF",
    "HEADLINE_COST_SCENARIO",
    "REPORT_IS_DESCRIPTIVE",
    "TAIL_QUANTILE",
    "TRIAL_LEDGER",
    "crop_year_metrics",
    "deflated_sharpe_ratio",
    "excess_sharpe",
    "n_trials",
    "report_spec_payload",
    "tail_risk_metrics",
]

# --------------------------------------------------------------------------------------
# Convenções numéricas — fixadas para que o número reportado não dependa de escolha tardia.
# --------------------------------------------------------------------------------------

ANNUALIZATION_SESSIONS: int = 252
DDOF: int = 1
#: Cauda esquerda de VaR/CVaR. Quantil histórico (não-paramétrico), interpolação linear.
TAIL_QUANTILE: float = 0.05

# --------------------------------------------------------------------------------------
# §3 — Benchmark de performance declarado
# --------------------------------------------------------------------------------------

#: Benchmark primário: a taxa livre de risco local (CDI), a MESMA série já usada por H4.
#: Justificativa: o livro é dollar-neutral, então não toma exposição direcional ao mercado —
#: ele consome capital como margem e garantia. O custo de oportunidade desse capital é a taxa
#: livre de risco, e não um índice de ações. O Sharpe reportado é líquido de CDI e substitui
#: o `sharpe_zero_rf` do bloco 10, que assume taxa livre de risco zero.
BENCHMARK_PRIMARY: str = "risk_free"

#: Comparador secundário: a carteira setorial ingênua já construída no bloco 4 (D-064). É o
#: contrafactual honesto da pergunta "isto é clima ou é setor?", e não um benchmark de
#: mercado.
BENCHMARK_SECONDARY: str = "naive_sector"

#: Comparadores explicitamente RECUSADOS, declarados antes do resultado para que não possam
#: ser escolhidos depois conforme convenham. Um livro dollar-neutral comparado a um índice de
#: ações pareceria brilhante num ano de queda e medíocre num ano de alta, pelos motivos
#: errados nos dois casos.
BENCHMARK_REJECTED: tuple[str, ...] = ("ibovespa", "cdi_plus_spread", "zero")

#: Cenário de custo do número de manchete. Fixado no cenário BASE — não no `zero`, que
#: ignora fricção, nem no melhor dos três depois de vistos.
HEADLINE_COST_SCENARIO: str = "base"

#: O relatório descreve; não veta nem promove. Ver docstring do módulo.
REPORT_IS_DESCRIPTIVE: bool = True

# --------------------------------------------------------------------------------------
# §4 — Contagem de especificações testadas (razão do Deflated Sharpe)
# --------------------------------------------------------------------------------------
#
# Regra de contagem, congelada: conta como tentativa (a) toda configuração distinta de
# estratégia — universo, direção, exposição, sizing, caps, horizonte — que foi adotada ou
# avaliada durante o desenvolvimento, e (b) toda variante calculada dentro da própria rodada.
#
# O grupo (b) é deliberadamente CONSERVADOR: essas variantes não foram usadas para selecionar
# nada, mas contá-las aumenta o número de tentativas e portanto eleva a barra que o Sharpe
# observado precisa vencer. Preferimos errar para o lado que nos penaliza.
#
# A lista é enumerada em vez de resumida num inteiro para que qualquer auditor possa conferir
# item a item contra `docs/07_RISCOS_E_DECISOES.md`.

TRIAL_LEDGER: tuple[tuple[str, str], ...] = (
    ("D-002", "tese reformulada de direcional para cross-seccional"),
    ("D-033", "matriz de exposição de preço: quatro nomes diretos"),
    ("D-035", "matriz D-033 mantida com a perna long condicionada a H2a"),
    ("D-043", "direção original produtor-comprado, AVALIADA COM RETORNOS no dev"),
    ("D-044", "direção H′ Q-dominante — o sinal foi escolhido após observar D-043"),
    ("D-047", "algodão como canal adicional do escore"),
    ("D-050", "cana como canal adicional do escore"),
    ("D-052", "universo com SMTO3 dentro e JALL3 fora"),
    ("D-053", "congelamento: 5 nomes, water-filling, caps 0,40/0,15, 21 pregões, D+1"),
    ("D-055", "contrato operacional: blocos contíguos, ADTV, AUM, custos"),
    ("D-059", "smoke do dev 2018/19, COM P&L OBSERVADO"),
    ("D-060", "diagnósticos do dev com retornos: atribuição e setor×clima"),
    ("D-061", "matriz de exposição rederivada sob H′ após o P&L do dev ter sido visto"),
    ("D-062", "veículos alternativos de monetização avaliados e recusados"),
    ("D-063", "espaço de veículos reenumerado após a correção do canal Rumo"),
    ("D-067", "ramo AGRO3×ADTV e elegibilidade da perna produtora"),
)

#: Variantes calculadas dentro da rodada única (blocos 2, 7, 8 e 9), contadas como tentativas
#: pelo critério conservador acima. 3 cenários de custo + 10 sensibilidades de parâmetro
#: + 5 leave-one-name-out + 5 leave-one-crop-year-out.
IN_RUN_VARIANTS: int = 23


def n_trials() -> int:
    """Número total de tentativas usado pelo Deflated Sharpe. Fixado antes da rodada."""
    return len(TRIAL_LEDGER) + IN_RUN_VARIANTS


# --------------------------------------------------------------------------------------
# §1 — Desempenho por ano-safra
# --------------------------------------------------------------------------------------


def crop_year_metrics(
    daily: pd.DataFrame,
    risk_free: pd.Series,
) -> dict[str, object]:
    """Desempenho por ano-safra do livro, com os cinco anos obrigatórios.

    Regra de honestidade congelada: **todos** os anos-safra do holdout aparecem no
    resultado, em ordem cronológica, inclusive os negativos e inclusive os sem bloco ativo.
    Nenhum ano pode ser omitido do artefato por qualquer motivo. O agregado sozinho pode
    esconder um único ano carregando o resultado — que é exatamente o defeito que D-060 já
    encontrou no dev, onde um nome respondia por 54,6% do P&L bruto.

    O retorno do dia é atribuído ao ano-safra do bloco que estava sendo carregado
    (`return_crop_year`), não à data-calendário.
    """
    if "return_crop_year" not in daily.columns:
        raise ValueError("série diária sem 'return_crop_year'; atribuição por ano impossível")

    net = daily["net_return"].astype(float)
    pnl = daily["net_pnl_brl"].astype(float)
    year_of = daily["return_crop_year"]
    total_pnl = float(pnl.sum())

    per_year: dict[str, dict[str, float | int]] = {}
    for crop_year in HOLDOUT_CROP_YEARS:
        mask = (year_of == crop_year).to_numpy(dtype=bool, na_value=False)
        year_net = net[mask]
        year_pnl = float(pnl[mask].sum())
        if len(year_net) == 0:
            per_year[crop_year] = {
                "sessions": 0,
                "compounded_return": float("nan"),
                "pnl_brl": 0.0,
                "pnl_share": float("nan"),
                "annualized_volatility": float("nan"),
                "max_drawdown": float("nan"),
                "positive_day_rate": float("nan"),
                "excess_sharpe": float("nan"),
            }
            continue
        curve = (1.0 + year_net).cumprod()
        drawdown = curve / curve.cummax() - 1.0
        std = float(year_net.std(ddof=DDOF)) if len(year_net) > DDOF else float("nan")
        per_year[crop_year] = {
            "sessions": int(len(year_net)),
            "compounded_return": float(curve.iloc[-1] - 1.0),
            "pnl_brl": year_pnl,
            "pnl_share": year_pnl / total_pnl if total_pnl != 0.0 else float("nan"),
            "annualized_volatility": (
                std * math.sqrt(ANNUALIZATION_SESSIONS) if std == std else float("nan")
            ),
            "max_drawdown": float(drawdown.min()),
            "positive_day_rate": float((year_net > 0).mean()),
            "excess_sharpe": excess_sharpe(year_net, risk_free.reindex(year_net.index)),
        }

    realised = {
        year: stats
        for year, stats in per_year.items()
        if isinstance(stats["sessions"], int) and stats["sessions"] > 0
    }
    returns_by_year = {
        year: float(stats["compounded_return"])
        for year, stats in realised.items()
        if stats["compounded_return"] == stats["compounded_return"]
    }
    shares = [
        abs(float(stats["pnl_share"]))
        for stats in realised.values()
        if stats["pnl_share"] == stats["pnl_share"]
    ]
    return {
        "crop_years": HOLDOUT_CROP_YEARS,
        "per_crop_year": per_year,
        "years_reported": len(per_year),
        "years_with_sessions": len(realised),
        "years_positive": sum(1 for value in returns_by_year.values() if value > 0),
        "worst_crop_year": min(returns_by_year, key=returns_by_year.get, default=None),
        "best_crop_year": max(returns_by_year, key=returns_by_year.get, default=None),
        "max_abs_pnl_share": max(shares) if shares else float("nan"),
    }


# --------------------------------------------------------------------------------------
# §2 — Caracterização de risco
# --------------------------------------------------------------------------------------


def excess_sharpe(net_return: pd.Series, risk_free: pd.Series) -> float:
    """Sharpe anualizado do excesso sobre o benchmark primário declarado (CDI).

    Substitui `sharpe_zero_rf` do bloco 10, que assume taxa livre de risco igual a zero.
    """
    excess = (net_return.astype(float) - risk_free.astype(float)).dropna()
    if len(excess) <= DDOF:
        return float("nan")
    std = float(excess.std(ddof=DDOF))
    if std <= 0.0:
        return float("nan")
    return float(excess.mean() / std * math.sqrt(ANNUALIZATION_SESSIONS))


def _time_under_water(equity: pd.Series) -> tuple[float, int]:
    """Duração média e máxima, em pregões, dos períodos abaixo do pico anterior."""
    below = (equity < equity.cummax()).to_numpy(dtype=bool)
    spells: list[int] = []
    current = 0
    for flag in below:
        if flag:
            current += 1
        elif current:
            spells.append(current)
            current = 0
    if current:
        spells.append(current)
    if not spells:
        return 0.0, 0
    return float(np.mean(spells)), int(max(spells))


def tail_risk_metrics(
    daily: pd.DataFrame,
    risk_free: pd.Series,
    market_excess: pd.Series | None = None,
) -> dict[str, object]:
    """Risco do livro: cauda, assimetria de perda, tempo submerso, beta e exposição.

    A carteira nunca foi caracterizada por risco — só por P&L, atribuição e turnover. Um
    livro dollar-neutral zera o notional, mas **não** zera beta, fatores nem commodity, como
    já registrado em D-034; por isso o beta contra o mercado é medido, não presumido.
    """
    net = daily["net_return"].astype(float)
    equity = daily["equity_brl"].astype(float)
    excess = (net - risk_free.reindex(net.index).astype(float)).dropna()

    var = float(np.quantile(net.to_numpy(), TAIL_QUANTILE, method="linear"))
    tail = net[net <= var]
    downside = excess[excess < 0.0]
    downside_dev = (
        float(math.sqrt(float((downside**2).mean())) * math.sqrt(ANNUALIZATION_SESSIONS))
        if len(downside)
        else 0.0
    )
    drawdown = equity / equity.cummax() - 1.0
    max_drawdown = float(drawdown.min())
    elapsed_days = max((equity.index[-1] - equity.index[0]).days, 1)
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    cagr = float((1.0 + total_return) ** (365.25 / elapsed_days) - 1.0)
    mean_tuw, max_tuw = _time_under_water(equity)

    beta = float("nan")
    if market_excess is not None:
        pair = pd.concat(
            {"y": excess, "x": market_excess.reindex(excess.index).astype(float)}, axis=1
        ).dropna()
        if len(pair) > DDOF and float(pair["x"].var(ddof=DDOF)) > 0.0:
            beta = float(pair["y"].cov(pair["x"]) / pair["x"].var(ddof=DDOF))

    return {
        "benchmark": BENCHMARK_PRIMARY,
        "sessions": int(len(net)),
        "excess_sharpe": excess_sharpe(net, risk_free.reindex(net.index)),
        "var_95": var,
        "cvar_95": float(tail.mean()) if len(tail) else float("nan"),
        "worst_session": float(net.min()),
        "downside_deviation": downside_dev,
        "sortino": (
            float(excess.mean() * ANNUALIZATION_SESSIONS / downside_dev)
            if downside_dev > 0.0
            else float("nan")
        ),
        "calmar": cagr / abs(max_drawdown) if max_drawdown < 0.0 else float("nan"),
        "max_drawdown": max_drawdown,
        "mean_time_under_water_sessions": mean_tuw,
        "max_time_under_water_sessions": max_tuw,
        "beta_vs_market": beta,
        "mean_gross_exposure": float(daily["gross_exposure"].astype(float).mean()),
        "max_gross_exposure": float(daily["gross_exposure"].astype(float).max()),
        "max_abs_net_exposure": float(daily["net_exposure"].astype(float).abs().max()),
        "skewness": float(net.skew()),
        "excess_kurtosis": float(net.kurt()),
    }


# --------------------------------------------------------------------------------------
# §4 — Deflated Sharpe Ratio
# --------------------------------------------------------------------------------------


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _normal_ppf(probability: float) -> float:
    """Inversa da normal padrão por bisseção — evita depender de scipy neste contrato."""
    if not 0.0 < probability < 1.0:
        raise ValueError("probabilidade fora de (0, 1)")
    low, high = -40.0, 40.0
    for _ in range(200):
        mid = 0.5 * (low + high)
        if _normal_cdf(mid) < probability:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


#: Constante de Euler–Mascheroni, usada no valor esperado do máximo de N tentativas.
EULER_MASCHERONI: float = 0.5772156649015329


def expected_max_sharpe(trial_sharpe_std: float, trials: int) -> float:
    """Sharpe máximo esperado sob a hipótese nula de que nenhuma tentativa tem habilidade.

    Bailey e López de Prado (2014). Em unidade DIÁRIA, como o resto do cálculo.
    """
    if trials < 2 or trial_sharpe_std <= 0.0:
        return 0.0
    gamma = EULER_MASCHERONI
    return float(
        trial_sharpe_std
        * (
            (1.0 - gamma) * _normal_ppf(1.0 - 1.0 / trials)
            + gamma * _normal_ppf(1.0 - 1.0 / (trials * math.e))
        )
    )


def deflated_sharpe_ratio(
    *,
    observed_sharpe: float,
    n_obs: int,
    skewness: float,
    excess_kurtosis: float,
    trial_sharpe_std: float,
    trials: int,
) -> dict[str, float]:
    """Probabilidade de que o Sharpe observado não seja artefato de múltiplas tentativas.

    Todos os Sharpes entram em unidade **diária** (não anualizada). O valor retornado é uma
    probabilidade, e é **descritivo**: não veta nem promove nenhum claim de D-068.

    Nenhum time do acervo de edições anteriores aplicou esta correção, e a razão é conhecida:
    ela exige declarar honestamente quantas especificações foram tentadas. Nosso log de
    decisões permite essa contagem, e ela está enumerada em `TRIAL_LEDGER`.
    """
    threshold = expected_max_sharpe(trial_sharpe_std, trials)
    kurt = excess_kurtosis + 3.0
    denominator = 1.0 - skewness * observed_sharpe + (kurt - 1.0) / 4.0 * observed_sharpe**2
    if n_obs <= 1 or denominator <= 0.0:
        return {
            "deflated_sharpe_ratio": float("nan"),
            "expected_max_sharpe_daily": threshold,
            "observed_sharpe_daily": observed_sharpe,
            "trials": float(trials),
        }
    statistic = (observed_sharpe - threshold) * math.sqrt(n_obs - 1) / math.sqrt(denominator)
    return {
        "deflated_sharpe_ratio": _normal_cdf(statistic),
        "expected_max_sharpe_daily": threshold,
        "observed_sharpe_daily": observed_sharpe,
        "trials": float(trials),
    }


def trial_sharpe_dispersion(variant_sharpes: Sequence[float]) -> float:
    """Desvio-padrão dos Sharpes das variantes, em unidade diária.

    Estimado sobre TODAS as variantes publicadas nos blocos 2, 7, 8 e 9 — cenários de custo,
    leave-one-name-out, leave-one-crop-year-out e as sensibilidades de parâmetro. A regra
    fica fixada aqui para que o conjunto não seja escolhido depois conforme o resultado.
    """
    values = np.asarray([value for value in variant_sharpes if value == value], dtype=float)
    if len(values) <= DDOF:
        return 0.0
    return float(values.std(ddof=DDOF))


def report_spec_payload() -> Mapping[str, object]:
    """Parâmetros do relatório que entram no hash lógico do contrato congelado."""
    return {
        "annualization_sessions": ANNUALIZATION_SESSIONS,
        "ddof": DDOF,
        "tail_quantile": TAIL_QUANTILE,
        "benchmark_primary": BENCHMARK_PRIMARY,
        "benchmark_secondary": BENCHMARK_SECONDARY,
        "benchmark_rejected": BENCHMARK_REJECTED,
        "headline_cost_scenario": HEADLINE_COST_SCENARIO,
        "descriptive_only": REPORT_IS_DESCRIPTIVE,
        "crop_years_mandatory": HOLDOUT_CROP_YEARS,
        "trial_ledger": TRIAL_LEDGER,
        "in_run_variants": IN_RUN_VARIANTS,
        "trials": n_trials(),
    }
