"""Camada estatística: inferência que não mente para nós mesmos (docs/05_SUITE_ROBUSTEZ.md §6).

Newey-West e block bootstrap para autocorrelação, Benjamini-Hochberg para múltiplas
comparações, e agrupamento por ano-safra para reportar o N efetivo, não o N nominal.
"""

from __future__ import annotations

from .inference import (
    RegResult,
    bh_fdr,
    cluster_bootstrap,
    moving_block_bootstrap,
    ols_cluster,
    ols_hac,
)

__all__ = [
    "RegResult",
    "bh_fdr",
    "cluster_bootstrap",
    "moving_block_bootstrap",
    "ols_cluster",
    "ols_hac",
]
