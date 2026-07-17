"""Portão da Fase 2 — junta H1a e H1b, aplica BH-FDR sobre a família e emite o veredito (D-030).

A família primária pré-registrada tem 11 testes (span cheio): H1a {agrupado, soja, milho} e
H1b {soja, milho} × ``h∈{3,4,5,6}``. O portão **passa** se o ``β`` agrupado de H1a for negativo
e sobreviver ao BH-FDR; H1b corrobora fisicamente. Se H1a falhar, paramos e reformulamos — o
achado negativo vai para o relatório (``00_PLANO_MESTRE`` §4).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .inference import bh_fdr

FDR_ALPHA = 0.10


@dataclass(frozen=True)
class Verdict:
    passed: bool
    h1a_beta: float
    h1a_qvalue: float
    reason: str


def primary_family(h1a: pd.DataFrame, h1b: pd.DataFrame) -> pd.DataFrame:
    """Extrai a família primária de 11 testes (span cheio) na ordem pré-registrada (D-030)."""
    rows = []
    for name in ("h1a:pooled", "h1a:crop=soy", "h1a:crop=corn_second"):
        r = h1a[(h1a["test"] == name) & (h1a["scope"] == "full")]
        if not r.empty:
            rows.append(
                {
                    "test": name,
                    "beta": float(r["beta"].iloc[0]),
                    "pvalue": float(r["pvalue"].iloc[0]),
                }
            )
    for crop in ("soy", "corn_second"):
        for h in (3, 4, 5, 6):
            r = h1b[(h1b["crop"] == crop) & (h1b["h"] == h)]
            if not r.empty:
                rows.append(
                    {
                        "test": f"h1b:{crop}:h{h}",
                        "beta": float(r["beta"].iloc[0]),
                        "pvalue": float(r["pvalue"].iloc[0]),
                    }
                )
    return pd.DataFrame(rows)


def apply_fdr(family: pd.DataFrame, alpha: float = FDR_ALPHA) -> pd.DataFrame:
    """Anexa ``qvalue``/``reject`` (BH-FDR) à família de testes."""
    fdr = bh_fdr(family["pvalue"], alpha=alpha)
    out = family.copy()
    out["qvalue"] = fdr["qvalue"].to_numpy()
    out["reject"] = fdr["reject"].to_numpy()
    return out


def verdict(family_fdr: pd.DataFrame) -> Verdict:
    """Regra do portão pré-registrada: H1a agrupado com ``β < 0`` e significativo após BH-FDR."""
    row = family_fdr[family_fdr["test"] == "h1a:pooled"]
    if row.empty:
        return Verdict(False, float("nan"), float("nan"), "H1a agrupado ausente do resultado")
    beta = float(row["beta"].iloc[0])
    q = float(row["qvalue"].iloc[0])
    reject = bool(row["reject"].iloc[0])
    if beta < 0 and reject:
        return Verdict(
            True, beta, q, "H1a agrupado: β<0 e sobrevive ao BH-FDR — mecanismo confirmado"
        )
    if beta >= 0:
        return Verdict(False, beta, q, "H1a agrupado com sinal errado (β≥0) — reformular")
    return Verdict(False, beta, q, "H1a agrupado não sobrevive ao BH-FDR — sem poder/sem sinal")
