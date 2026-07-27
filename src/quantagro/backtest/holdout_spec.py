"""Contrato do pacote de rodada única do holdout (D-068), anterior aos retornos.

Este módulo não executa o holdout. Ele congela, em forma validável, o que a futura rodada
única precisa calcular e emitir sem pausas para decisão humana. A ordem não é uma hierarquia
de divulgação seletiva: todos os passos rodam mesmo que o teste primário falhe.

O teste H3′/H′ por sign-flip de cinco anos-safra é a única hipótese confirmatória, com
``alpha=0,10`` já congelado em D-053/D-055. H4 e H5 são vetos adversariais para a expressão
"alpha climático"; sensibilidades e subgrupos são descritivos e não criam novos p-valores.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256

from .operational_spec import (
    ADTV_FLOOR_BRL,
    COST_SCENARIOS,
    EXPECTED_PERMUTATIONS,
    HOLDING_SESSIONS,
    PERMUTATION_KIND,
)
from .strategy_spec import (
    ALPHA,
    CLUSTER_BY,
    HOLDOUT_CROP_YEARS,
    INFERENCE,
    PRIMARY_TEST,
    PRIMARY_TEST_UNIVERSE,
    TEST_IS_ONE_SIDED,
    UNIVERSE,
)

PACKAGE_ID = "holdout_v1_d068"
RUN_RECORD = "data/reference/holdout_run_record_v1.json"
RESULT_RECORD = "data/reference/holdout_result_v1.json"
WORK_DIR = "data/processed/holdout_v1"

# D-069 fechou H4 e D-070/D-071 fecharam H5. O executor continua desabilitado até a
# orquestração final ser implementada e auditada em commit próprio.
EXECUTOR_IMPLEMENTED = False
CONTINUE_AFTER_PRIMARY_FAILURE = True
ALLOW_INTERMEDIATE_RESULT_DISPLAY = False

PRIMARY_ALPHA = ALPHA
PRIMARY_EXPECTED_SIGN = 1
PORTFOLIO_PRIMARY_COST_SCENARIO = "base"

# H4: a especificação core é decomposição; somente a estendida funciona como veto. Rm-Rf
# substitui IBOV para evitar duplicar o fator de mercado. O desfecho é retorno líquido menos
# Risk_Free: comparação conservadora com o capital que poderia render a taxa livre de risco.
H4_ALPHA = 0.10
H4_HAC_LAGS = HOLDING_SESSIONS
H4_CORE_CONTROLS = ("rm_minus_rf", "smb", "hml", "wml", "iml")
H4_EXTENDED_CONTROLS = H4_CORE_CONTROLS + (
    "usdbrl",
    "soy",
    "corn_second",
    "sugar",
    "oni",
)
H4_RISK_FREE_COLUMN = "risk_free"
H4_VETO_SPEC = "extended"

# H5 geográfico permanece o veto existencial prometido desde o pré-registro. O placebo de
# exposição é obrigatório, mas descritivo: permutações que preservem lado econômico têm
# suporte pequeno demais para um segundo teste a 10%.
H5_ALPHA = 0.10
H5_MAX_ABS_RATIO = 0.50
H5_GEOGRAPHIC_PLACEBO = "nonproducing_geography"
H5_EXPOSURE_PLACEBO = "within_economic_side_permutation"
H5_STATISTIC = "mean_crop_year_base_net_return"
H5_INFERENCE = "exact_crop_year_sign_flip"
H5_VETO = H5_GEOGRAPHIC_PLACEBO

ADTV_SENSITIVITY_BRL = (4_000_000.0, 12_000_000.0)
HOLDING_SENSITIVITY_SESSIONS = (10, 42)
TOTAL_SIGNAL_LAG_SENSITIVITY_DAYS = (14, 21)
GRAIN_CAP_SENSITIVITY = (0.30, 0.50)
CANE_CAP_SENSITIVITY = (0.10, 0.20)
LOO_NAMES = UNIVERSE
LOO_CROP_YEARS = HOLDOUT_CROP_YEARS


@dataclass(frozen=True)
class AnalysisStep:
    """Um passo obrigatório da rodada, com papel inferencial e artefato próprio."""

    order: int
    name: str
    role: str
    required: bool
    output: str


ANALYSIS_STEPS = (
    AnalysisStep(0, "preflight", "gate", True, "00_preflight.json"),
    AnalysisStep(1, "primary_hprime", "confirmatory", True, "01_primary_hprime.json"),
    AnalysisStep(2, "portfolio_cost_scenarios", "decision", True, "02_portfolio.json"),
    AnalysisStep(3, "liquidity_d067", "diagnostic", True, "03_liquidity.json"),
    AnalysisStep(4, "sector_climate_d064", "diagnostic", True, "04_sector_climate.json"),
    AnalysisStep(5, "h4_spanning", "veto", True, "05_h4_spanning.json"),
    AnalysisStep(6, "h5_placebos", "veto", True, "06_h5_placebos.json"),
    AnalysisStep(7, "leave_one_name_out", "sensitivity", True, "07_loo_name.json"),
    AnalysisStep(8, "leave_one_crop_year_out", "sensitivity", True, "08_loo_year.json"),
    AnalysisStep(9, "parameter_sensitivities", "sensitivity", True, "09_sensitivities.json"),
    AnalysisStep(10, "metrics_attribution", "diagnostic", True, "10_metrics.json"),
    AnalysisStep(11, "seal_result", "gate", True, "11_seal.json"),
)

# Inputs derivados serão materializados e atestados antes da autorização civil. O preflight
# não tenta substituí-los por arquivos de dev, fontes atuais ou downloads ad hoc.
REQUIRED_INPUTS = {
    "returns": "data/interim/holdout/equity_returns.parquet",
    "market_state": "data/interim/holdout/market_state.parquet",
    "grain_scores": "data/interim/holdout/grain_scores.parquet",
    "cane_signal": "data/interim/holdout/cane_signal.parquet",
    "h4_controls": "data/interim/holdout/h4_controls.parquet",
    "h5_geographic_scores": "data/interim/holdout/h5_geographic_grain_scores.parquet",
    "input_manifest": "data/interim/holdout/input_manifest.json",
}

# Qualquer mudança nestes arquivos altera o hash do contrato e exige nova decisão anterior
# ao holdout. O próprio módulo entra na lista; o runner final será acrescentado antes do unlock.
SPEC_FILES = (
    "src/quantagro/backtest/strategy_spec.py",
    "src/quantagro/backtest/operational_spec.py",
    "src/quantagro/backtest/inputs.py",
    "src/quantagro/backtest/engine.py",
    "src/quantagro/backtest/diagnostics.py",
    "src/quantagro/backtest/holdout_spec.py",
    "src/quantagro/backtest/holdout.py",
    "src/quantagro/features/shock_spec.py",
    "src/quantagro/features/shock.py",
    "src/quantagro/features/exposure.py",
    "src/quantagro/ingest/h4_market.py",
    "src/quantagro/robustness/h4_controls.py",
    "src/quantagro/robustness/h5_geography.py",
    "src/quantagro/robustness/h5_geography_spec.py",
    "src/quantagro/validate/universe.py",
    "src/quantagro/validate/borrow.py",
    "data/reference/exposure_hprime_v1.json",
    "data/reference/borrow_rate_calibration_v1.json",
    "data/reference/h4_controls_summary_v1.json",
    "data/reference/h5_geography_spec_v1.json",
    "data/reference/h5_geographic_scores_summary_v1.json",
    "data/manifests/pam_1612_corn_total_2014-2024_ba_20260727.json",
    "scripts/build_h4_controls.py",
    "scripts/build_h5_geographic_scores.py",
    "scripts/run_holdout_once.py",
)

CLAIM_REQUIREMENTS = {
    "positive_oos_pnl": ("base_net_return_positive",),
    "oos_strategy_evidence": ("base_net_return_positive", "primary_hprime_passed"),
    "climate_alpha_evidence": (
        "base_net_return_positive",
        "primary_hprime_passed",
        "d064_climate_component_positive",
        "h4_extended_passed",
        "h5_geographic_died",
    ),
}

# Tripwire civil: qualquer alteração do payload lógico exige atualizar este valor numa decisão
# posterior e explicitamente anterior ao unlock. O hash não depende do whitespace dos fontes.
EXPECTED_LOGICAL_SPEC_SHA256 = "cb125fea931b616e2c62ec22a2821d3899c5a84643fa28d6f02ab9060a04912b"


def canonical_spec_payload() -> dict[str, object]:
    """Representação serializável e ordenada de todos os graus de liberdade de D-068."""
    return {
        "package_id": PACKAGE_ID,
        "executor_implemented": EXECUTOR_IMPLEMENTED,
        "continue_after_primary_failure": CONTINUE_AFTER_PRIMARY_FAILURE,
        "allow_intermediate_result_display": ALLOW_INTERMEDIATE_RESULT_DISPLAY,
        "primary": {
            "alpha": PRIMARY_ALPHA,
            "expected_sign": PRIMARY_EXPECTED_SIGN,
            "test": PRIMARY_TEST,
            "universe": PRIMARY_TEST_UNIVERSE,
            "inference": INFERENCE,
            "one_sided": TEST_IS_ONE_SIDED,
            "cluster_by": CLUSTER_BY,
            "permutation_kind": PERMUTATION_KIND,
            "permutations": EXPECTED_PERMUTATIONS,
        },
        "portfolio": {
            "primary_cost_scenario": PORTFOLIO_PRIMARY_COST_SCENARIO,
            "cost_scenarios": COST_SCENARIOS,
        },
        "h4": {
            "alpha": H4_ALPHA,
            "hac_lags": H4_HAC_LAGS,
            "core_controls": H4_CORE_CONTROLS,
            "extended_controls": H4_EXTENDED_CONTROLS,
            "risk_free_column": H4_RISK_FREE_COLUMN,
            "veto_spec": H4_VETO_SPEC,
        },
        "h5": {
            "alpha": H5_ALPHA,
            "max_abs_ratio": H5_MAX_ABS_RATIO,
            "geographic": H5_GEOGRAPHIC_PLACEBO,
            "exposure": H5_EXPOSURE_PLACEBO,
            "statistic": H5_STATISTIC,
            "inference": H5_INFERENCE,
            "veto": H5_VETO,
        },
        "sensitivities": {
            "cost": COST_SCENARIOS,
            "adtv_brl": ADTV_SENSITIVITY_BRL,
            "holding_sessions": HOLDING_SENSITIVITY_SESSIONS,
            "total_signal_lag_days": TOTAL_SIGNAL_LAG_SENSITIVITY_DAYS,
            "grain_cap": GRAIN_CAP_SENSITIVITY,
            "cane_cap": CANE_CAP_SENSITIVITY,
            "loo_names": LOO_NAMES,
            "loo_crop_years": LOO_CROP_YEARS,
        },
        "steps": tuple(asdict(step) for step in ANALYSIS_STEPS),
        "required_inputs": REQUIRED_INPUTS,
        "spec_files": SPEC_FILES,
        "claims": CLAIM_REQUIREMENTS,
        "run_record": RUN_RECORD,
        "result_record": RESULT_RECORD,
        "work_dir": WORK_DIR,
    }


def spec_sha256() -> str:
    """Hash determinístico do payload lógico, independente de whitespace dos fontes."""
    payload = json.dumps(
        canonical_spec_payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return sha256(payload).hexdigest()


def validate_holdout_spec() -> None:
    """Tripwires contra relaxamento silencioso do pacote antes da rodada única."""
    orders = tuple(step.order for step in ANALYSIS_STEPS)
    if orders != tuple(range(len(ANALYSIS_STEPS))):
        raise ValueError("passos do holdout devem ter ordem contígua a partir de zero")
    if len({step.name for step in ANALYSIS_STEPS}) != len(ANALYSIS_STEPS):
        raise ValueError("nomes dos passos do holdout devem ser únicos")
    if len({step.output for step in ANALYSIS_STEPS}) != len(ANALYSIS_STEPS):
        raise ValueError("artefatos dos passos do holdout devem ser únicos")
    signatures = tuple((step.name, step.role, step.output) for step in ANALYSIS_STEPS)
    if signatures != (
        ("preflight", "gate", "00_preflight.json"),
        ("primary_hprime", "confirmatory", "01_primary_hprime.json"),
        ("portfolio_cost_scenarios", "decision", "02_portfolio.json"),
        ("liquidity_d067", "diagnostic", "03_liquidity.json"),
        ("sector_climate_d064", "diagnostic", "04_sector_climate.json"),
        ("h4_spanning", "veto", "05_h4_spanning.json"),
        ("h5_placebos", "veto", "06_h5_placebos.json"),
        ("leave_one_name_out", "sensitivity", "07_loo_name.json"),
        ("leave_one_crop_year_out", "sensitivity", "08_loo_year.json"),
        ("parameter_sensitivities", "sensitivity", "09_sensitivities.json"),
        ("metrics_attribution", "diagnostic", "10_metrics.json"),
        ("seal_result", "gate", "11_seal.json"),
    ):
        raise ValueError("ordem, papel ou artefato da rodada única foi alterado")
    confirmatory = [step for step in ANALYSIS_STEPS if step.role == "confirmatory"]
    if len(confirmatory) != 1 or confirmatory[0].name != "primary_hprime":
        raise ValueError("H′ deve ser a única hipótese confirmatória")
    if not all(step.required for step in ANALYSIS_STEPS):
        raise ValueError("nenhum passo pré-registrado pode ser omitido")
    if not CONTINUE_AFTER_PRIMARY_FAILURE or ALLOW_INTERMEDIATE_RESULT_DISPLAY:
        raise ValueError("rodada não pode parar nem exibir resultado intermediário")
    if PRIMARY_ALPHA != 0.10 or PRIMARY_EXPECTED_SIGN != 1:
        raise ValueError("teste primário D-053/D-055 foi alterado")
    if (
        PRIMARY_TEST != "producer_processor_spread_panel"
        or PRIMARY_TEST_UNIVERSE != ("AGRO3", "SLCE3", "BRFS3", "JBSS3")
        or INFERENCE != "permutation_cluster_by_crop_year"
        or not TEST_IS_ONE_SIDED
        or CLUSTER_BY != "ano_agricola"
        or PERMUTATION_KIND != "exact_crop_year_sign_flip"
        or EXPECTED_PERMUTATIONS != 32
    ):
        raise ValueError("estrutura do teste confirmatório foi alterada")
    if PORTFOLIO_PRIMARY_COST_SCENARIO != "base" or tuple(COST_SCENARIOS) != (
        "zero",
        "base",
        "double",
    ):
        raise ValueError("cenários de custo da carteira foram alterados")
    if H4_VETO_SPEC != "extended" or H4_HAC_LAGS != 21 or H4_ALPHA != 0.10:
        raise ValueError("veto H4 foi alterado")
    if H4_CORE_CONTROLS != ("rm_minus_rf", "smb", "hml", "wml", "iml") or H4_EXTENDED_CONTROLS != (
        "rm_minus_rf",
        "smb",
        "hml",
        "wml",
        "iml",
        "usdbrl",
        "soy",
        "corn_second",
        "sugar",
        "oni",
    ):
        raise ValueError("controles H4 foram alterados ou duplicam mercado")
    if (
        H5_VETO != H5_GEOGRAPHIC_PLACEBO
        or H5_MAX_ABS_RATIO != 0.50
        or H5_STATISTIC != "mean_crop_year_base_net_return"
        or H5_INFERENCE != "exact_crop_year_sign_flip"
    ):
        raise ValueError("veto H5 foi alterado")
    if ADTV_FLOOR_BRL != 8_000_000 or ADTV_SENSITIVITY_BRL != (4_000_000.0, 12_000_000.0):
        raise ValueError("grid de liquidez foi alterado")
    if HOLDING_SESSIONS != 21 or HOLDING_SENSITIVITY_SESSIONS != (10, 42):
        raise ValueError("grid de horizonte foi alterado")
    if TOTAL_SIGNAL_LAG_SENSITIVITY_DAYS != (14, 21):
        raise ValueError("grid de lag total foi alterado")
    if GRAIN_CAP_SENSITIVITY != (0.30, 0.50) or CANE_CAP_SENSITIVITY != (0.10, 0.20):
        raise ValueError("grid de caps foi alterado")
    if LOO_NAMES != UNIVERSE or LOO_CROP_YEARS != HOLDOUT_CROP_YEARS:
        raise ValueError("leave-one-out deve enumerar universo e cinco safras congelados")
    if CLAIM_REQUIREMENTS != {
        "positive_oos_pnl": ("base_net_return_positive",),
        "oos_strategy_evidence": ("base_net_return_positive", "primary_hprime_passed"),
        "climate_alpha_evidence": (
            "base_net_return_positive",
            "primary_hprime_passed",
            "d064_climate_component_positive",
            "h4_extended_passed",
            "h5_geographic_died",
        ),
    }:
        raise ValueError("níveis de afirmação do holdout foram alterados")
    if REQUIRED_INPUTS != {
        "returns": "data/interim/holdout/equity_returns.parquet",
        "market_state": "data/interim/holdout/market_state.parquet",
        "grain_scores": "data/interim/holdout/grain_scores.parquet",
        "cane_signal": "data/interim/holdout/cane_signal.parquet",
        "h4_controls": "data/interim/holdout/h4_controls.parquet",
        "h5_geographic_scores": "data/interim/holdout/h5_geographic_grain_scores.parquet",
        "input_manifest": "data/interim/holdout/input_manifest.json",
    }:
        raise ValueError("caminhos ou papéis dos inputs foram alterados")
    if spec_sha256() != EXPECTED_LOGICAL_SPEC_SHA256:
        raise RuntimeError("payload lógico diverge do hash civil congelado em D-068–D-071")


validate_holdout_spec()
