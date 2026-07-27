"""Execução do relatório descritivo do holdout, posterior ao selo.

Lê apenas artefatos **já publicados** pelo executor da rodada única e a série livre de risco,
que é input atestado. Não recalcula estratégia, não reabre parquets de retorno e não toca em
nada do contrato congelado — as fórmulas e as constantes vivem em `holdout_report_spec`, que
foi congelado antes da rodada.

Guarda dura: sem `11_seal.json` no diretório publicado, o relatório falha. Isso impede que
ele seja rodado sobre o desenvolvimento ou sobre uma rodada incompleta.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .holdout_report_spec import (
    BENCHMARK_PRIMARY,
    BENCHMARK_REJECTED,
    BENCHMARK_SECONDARY,
    HEADLINE_COST_SCENARIO,
    REPORT_IS_DESCRIPTIVE,
    TRIAL_LEDGER,
    crop_year_metrics,
    deflated_sharpe_ratio,
    n_trials,
    tail_risk_metrics,
    trial_sharpe_dispersion,
)
from .holdout_spec import ANALYSIS_STEPS, REQUIRED_INPUTS, WORK_DIR

SEAL_ARTIFACT = ANALYSIS_STEPS[-1].output
METRICS_ARTIFACT = ANALYSIS_STEPS[10].output
PORTFOLIO_ARTIFACT = ANALYSIS_STEPS[2].output
LOO_NAME_ARTIFACT = ANALYSIS_STEPS[7].output
LOO_YEAR_ARTIFACT = ANALYSIS_STEPS[8].output
SENSITIVITY_ARTIFACT = ANALYSIS_STEPS[9].output

REPORT_OUTPUT = "12_descriptive_report.json"


def _load(work_dir: Path, name: str) -> dict:
    path = work_dir / name
    if not path.exists():
        raise FileNotFoundError(f"artefato ausente: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _daily_frame(metrics: dict) -> pd.DataFrame:
    # D-075: os artefatos publicados são envelopes {name, order, package_id, payload, role};
    # a série diária mora sob `payload`. Correção estrutural de nível de dicionário, feita
    # depois do selo — não altera nenhuma regra pré-registrada em holdout_report_spec.py.
    series = metrics["payload"]["daily"] if "payload" in metrics else metrics["daily"]
    frame = pd.DataFrame(series)
    if "date" not in frame.columns:
        raise ValueError("bloco 10 sem coluna 'date' na série diária")
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.set_index("date").sort_index()


def _variant_daily_sharpes(work_dir: Path) -> list[float]:
    """Sharpes diários das variantes dos blocos 2, 7, 8 e 9, para a dispersão de tentativas."""
    values: list[float] = []

    def collect(node: object) -> None:
        if isinstance(node, dict):
            if "sharpe_zero_rf" in node:
                raw = node["sharpe_zero_rf"]
                if isinstance(raw, (int, float)):
                    values.append(float(raw) / (252.0**0.5))
            for child in node.values():
                collect(child)
        elif isinstance(node, list):
            for child in node:
                collect(child)

    for name in (
        PORTFOLIO_ARTIFACT,
        LOO_NAME_ARTIFACT,
        LOO_YEAR_ARTIFACT,
        SENSITIVITY_ARTIFACT,
    ):
        collect(_load(work_dir, name))
    return values


def build_report(root: str | Path = ".") -> dict[str, object]:
    """Monta o relatório descritivo a partir dos artefatos selados."""
    base = Path(root)
    work_dir = base / WORK_DIR
    if not (work_dir / SEAL_ARTIFACT).exists():
        raise RuntimeError(
            f"selo {SEAL_ARTIFACT} ausente em {work_dir}: o relatório descritivo só roda "
            "depois da rodada única concluída e selada"
        )

    metrics = _load(work_dir, METRICS_ARTIFACT)
    daily = _daily_frame(metrics)

    # D-075: o parquet vem com RangeIndex e a data é a coluna `ref_date`. O alinhamento aqui
    # espelha exatamente o do bloco 5 selado (holdout_analysis._load_inputs) para que o
    # benchmark do relatório e o da regressão H4 sejam a MESMA série. A versão anterior
    # convertia o RangeIndex em epoch (1970) e o reindex devolvia NaN em silêncio.
    controls = pd.read_parquet(base / REQUIRED_INPUTS["h4_controls"]).copy()
    controls["ref_date"] = pd.to_datetime(controls["ref_date"]).dt.normalize()
    controls = controls.set_index("ref_date").sort_index()
    risk_free = controls[BENCHMARK_PRIMARY].astype(float).reindex(daily.index)
    market_excess = (
        controls["rm_minus_rf"].astype(float).reindex(daily.index)
        if "rm_minus_rf" in controls.columns
        else None
    )
    if risk_free.isna().any() or (market_excess is not None and market_excess.isna().any()):
        raise ValueError(
            "controles não alinham integralmente com a série diária selada; "
            "métrica de excesso não pode ser publicada com buraco"
        )

    risk = tail_risk_metrics(daily, risk_free, market_excess)
    by_year = crop_year_metrics(daily, risk_free)

    observed_daily_sharpe = risk["excess_sharpe"] / (252.0**0.5)
    dispersion = trial_sharpe_dispersion(_variant_daily_sharpes(work_dir))
    deflated = deflated_sharpe_ratio(
        observed_sharpe=observed_daily_sharpe,
        n_obs=int(risk["sessions"]),
        skewness=float(risk["skewness"]),
        excess_kurtosis=float(risk["excess_kurtosis"]),
        trial_sharpe_std=dispersion,
        trials=n_trials(),
    )

    return {
        "descriptive_only": REPORT_IS_DESCRIPTIVE,
        "headline_cost_scenario": HEADLINE_COST_SCENARIO,
        "benchmark": {
            "primary": BENCHMARK_PRIMARY,
            "secondary": BENCHMARK_SECONDARY,
            "rejected": list(BENCHMARK_REJECTED),
        },
        "crop_year_performance": by_year,
        "risk": risk,
        "multiplicity": deflated
        | {
            "trial_sharpe_std_daily": dispersion,
            "trial_ledger": [{"decision": key, "what": what} for key, what in TRIAL_LEDGER],
        },
    }


def write_report(root: str | Path = ".") -> Path:
    """Publica o relatório ao lado dos artefatos da rodada."""
    base = Path(root)
    payload = build_report(base)
    target = base / WORK_DIR / REPORT_OUTPUT
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target
