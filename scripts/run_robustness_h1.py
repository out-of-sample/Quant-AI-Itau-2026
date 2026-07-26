"""Roda a suíte de robustez do sinal H1 (D-065) sobre o grid congelado, uma vez.

**Return-agnóstico.** Testa o mecanismo H1a (revisão CONAB ~ Shock), não retornos; o holdout de
retornos segue lacrado. Reusa os carregadores de ``run_gate.py`` (painel municipal CHIRPS, CONAB,
PAM). Cada perturbação constrói inputs modificados para o ``build_h1a_panel`` inalterado; o baseline
é bit-idêntico ao portão D-030. Perturbações que não puderem rodar (ex.: climatologia que sai da
cobertura da série final) são reportadas como falha declarada, nunca omitidas em silêncio.

Uso: ``python scripts/run_robustness_h1.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from run_gate import CONAB_TXT, load_municipal, load_pam  # noqa: E402

from quantagro.features.panel import CLIMATOLOGY_FIRST_YEAR  # noqa: E402
from quantagro.ingest.conab import parse_levantamento  # noqa: E402
from quantagro.stats.robustness import run_perturbation  # noqa: E402
from quantagro.stats.robustness_spec import (  # noqa: E402
    PERTURBATIONS,
    PerturbationVerdict,
    overall_robust,
    perturbation_verdict,
)

OUT_DIR = Path("data/processed")


def main() -> None:
    print("=" * 92)
    print("SUÍTE DE ROBUSTEZ DO SINAL H1 (D-065). Return-agnóstico: mecanismo H1a, não retornos.")
    print("Baseline = portão D-030. Perturbações single-knob; placebos devem MATAR o sinal.")
    print("=" * 92, flush=True)

    conab = parse_levantamento(CONAB_TXT, "graos")
    municipal = load_municipal()
    pam = load_pam()
    cfy = CLIMATOLOGY_FIRST_YEAR

    results: dict[str, dict] = {}
    errors: dict[str, str] = {}
    baseline_panel = None
    baseline_abs = None

    for pert in PERTURBATIONS:  # baseline vem primeiro por construção do grid
        try:
            r = run_perturbation(pert, conab, municipal, pam, cfy, baseline_panel)
        except Exception as exc:  # noqa: BLE001 — falha declarada, não silenciosa
            errors[pert.name] = f"{type(exc).__name__}: {exc}"
            print(f"[{pert.name}] FALHOU: {errors[pert.name]}", flush=True)
            continue
        results[pert.name] = r
        if pert.name == "baseline":
            baseline_panel = r["panel"]
            baseline_abs = abs(r["beta"])
        print(
            f"[{pert.name}] β={r['beta']:+.4f} boot_p={r['boot_pvalue']:.3f} "
            f"N={r['n']} safras={r['n_clusters']}",
            flush=True,
        )

    if baseline_abs is None or baseline_abs <= 0:
        raise SystemExit("baseline não produziu β utilizável — abortando")

    verdicts: list[PerturbationVerdict] = []
    for pert in PERTURBATIONS:
        if pert.family == "baseline" or pert.name not in results:
            continue
        r = results[pert.name]
        verdicts.append(perturbation_verdict(pert, r["beta"], r["boot_pvalue"], baseline_abs))

    print("\n" + "-" * 92)
    print(f"baseline β = {results['baseline']['beta']:+.4f} (|β_base| = {baseline_abs:.4f})")
    print("-" * 92)
    table = pd.DataFrame(
        [
            {
                "perturbação": v.name,
                "família": v.family,
                "β": round(v.beta, 4),
                "|β|/|β_base|": round(v.ratio, 2),
                "boot_p": round(v.boot_pvalue, 3),
                "passou": v.passed,
                "flag": v.flag,
            }
            for v in verdicts
        ]
    )
    print(table.to_string(index=False))
    if errors:
        print("\nperturbações não executáveis (declaradas, não omitidas):")
        for name, msg in errors.items():
            print(f"  - {name}: {msg}")

    robust = overall_robust(verdicts)
    print("\n" + "=" * 92)
    print(f"VEREDITO GLOBAL: {'ROBUSTO' if robust else 'NÃO ROBUSTO (ver flags acima)'}")
    print("Descritivo do mecanismo; não valida retorno. Holdout de retornos lacrado (Fase 6).")
    print("=" * 92)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT_DIR / "robustness_h1_verdicts.csv", index=False)
    summary = pd.Series(
        {
            "baseline_beta": results["baseline"]["beta"],
            "baseline_abs_beta": baseline_abs,
            "overall_robust": robust,
            "n_errors": len(errors),
        }
    )
    summary.to_json(OUT_DIR / "robustness_h1_summary.json")
    print(f"\nartefatos salvos em {OUT_DIR}/")


if __name__ == "__main__":
    main()
