"""Construção e validação do painel diário de controles H4 (D-069).

O calendário-mestre é o NEFIN/B3. Níveis de ETFs e câmbio são carregados até cada sessão
brasileira e transformados em retorno simples entre sessões B3 consecutivas. Um feriado
americano gera retorno zero naquele dia e o movimento acumulado chega na próxima observação;
nenhum valor futuro é puxado para trás.

ONI entra em nível, como variável de regime, usando somente a temporada cuja ``avail_date``
conservadora já ocorreu. O painel final é um snapshot ex post: ``avail_date`` é a data mais
tardia das capturas que o compõem, não uma disponibilidade histórica inventada.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from quantagro.backtest.holdout_spec import H4_EXTENDED_CONTROLS, H4_RISK_FREE_COLUMN
from quantagro.ingest.nefin import FACTOR_COLUMNS
from quantagro.ingest.oni import stamp_oni_avail_date

H4_START = pd.Timestamp("2020-01-01")
H4_END = pd.Timestamp("2025-12-31")
MAX_MARKET_STALENESS_DAYS = 4
H4_COLUMNS = (
    "ref_date",
    "avail_date",
    *H4_EXTENDED_CONTROLS,
    H4_RISK_FREE_COLUMN,
)


def _aligned_return(
    calendar: pd.DatetimeIndex,
    panel: pd.DataFrame,
    *,
    value_column: str,
    role: str,
) -> pd.Series:
    required = {"ref_date", value_column}
    missing = required - set(panel.columns)
    if missing:
        raise ValueError(f"{role}: colunas ausentes {sorted(missing)}")
    clean = panel[list(required)].copy()
    clean["ref_date"] = pd.to_datetime(clean["ref_date"]).dt.normalize()
    if clean["ref_date"].duplicated().any():
        raise ValueError(f"{role}: ref_date duplicada")
    clean = clean.sort_values("ref_date").set_index("ref_date")
    values = pd.to_numeric(clean[value_column], errors="raise").astype("float64")
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError(f"{role}: nível deve ser positivo e finito")

    union = values.index.union(calendar).sort_values()
    aligned = values.reindex(union).ffill().reindex(calendar)
    observed_dates = pd.Series(values.index, index=values.index)
    source_date = observed_dates.reindex(union).ffill().reindex(calendar)
    if aligned.isna().any() or source_date.isna().any():
        raise ValueError(f"{role}: cobertura não alcança o início do calendário")
    staleness = (calendar.to_series(index=calendar) - source_date).dt.days
    if (staleness > MAX_MARKET_STALENESS_DAYS).any():
        worst = int(staleness.max())
        raise ValueError(f"{role}: nível carregado por {worst} dias; máximo é 4")
    result = aligned.pct_change(fill_method=None)
    result.name = role
    return result


def _oni_asof(calendar: pd.DatetimeIndex, oni: pd.DataFrame) -> pd.Series:
    stamped = stamp_oni_avail_date(oni)
    if stamped["avail_date"].duplicated().any():
        raise ValueError("ONI tem avail_date duplicada")
    right = stamped[["avail_date", "oni_c"]].sort_values("avail_date")
    left = pd.DataFrame({"ref_date": calendar})
    merged = pd.merge_asof(
        left,
        right,
        left_on="ref_date",
        right_on="avail_date",
        direction="backward",
        allow_exact_matches=True,
    )
    values = pd.to_numeric(merged["oni_c"], errors="raise").astype("float64")
    if values.isna().any() or not np.isfinite(values).all():
        raise ValueError("ONI não cobre o calendário H4 sem usar valor futuro")
    values.index = calendar
    values.name = "oni"
    return values


def validate_h4_controls(panel: pd.DataFrame) -> None:
    """Falha alto se o painel puder contaminar ou quebrar a futura regressão H4."""
    if tuple(panel.columns) != H4_COLUMNS:
        raise ValueError(f"schema H4 inesperado: {list(panel.columns)!r}")
    ref = pd.to_datetime(panel["ref_date"])
    avail = pd.to_datetime(panel["avail_date"])
    if panel.empty or ref.duplicated().any() or not ref.is_monotonic_increasing:
        raise ValueError("painel H4 vazio, duplicado ou fora de ordem")
    if ref.min() < H4_START or ref.max() > H4_END:
        raise ValueError("painel H4 fora da janela congelada")
    if (avail < ref).any() or not avail.eq(avail.iloc[0]).all():
        raise ValueError("painel H4 deve ser um único snapshot disponível após cada ref_date")
    numeric = panel[[*H4_EXTENDED_CONTROLS, H4_RISK_FREE_COLUMN]]
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("painel H4 contém controle ausente ou infinito")
    return_columns = [*H4_EXTENDED_CONTROLS[:-1], H4_RISK_FREE_COLUMN]
    if (numeric[return_columns].abs() >= 1).any().any():
        raise ValueError("painel H4 contém retorno diário fora de (-100%, 100%)")
    if (numeric["oni"].abs() > 5).any():
        raise ValueError("painel H4 contém ONI fora da faixa física esperada")


def build_h4_controls(
    nefin: pd.DataFrame,
    market: Mapping[str, pd.DataFrame],
    oni: pd.DataFrame,
    *,
    snapshot_avail_date,
) -> pd.DataFrame:
    """Materializa controles no calendário NEFIN/B3, sem ler retornos da estratégia."""
    missing_market = {"usdbrl", "soy", "corn_second", "sugar"} - set(market)
    if missing_market:
        raise ValueError(f"controles de mercado ausentes: {sorted(missing_market)}")
    required_nefin = {"ref_date", *FACTOR_COLUMNS}
    missing_nefin = required_nefin - set(nefin.columns)
    if missing_nefin:
        raise ValueError(f"NEFIN sem colunas H4: {sorted(missing_nefin)}")

    factors = nefin[list(required_nefin)].copy()
    factors["ref_date"] = pd.to_datetime(factors["ref_date"]).dt.normalize()
    factors = factors.sort_values("ref_date")
    warm = factors[factors["ref_date"].between(H4_START - pd.Timedelta(days=10), H4_END)].copy()
    if warm.empty or not (warm["ref_date"] < H4_START).any():
        raise ValueError("NEFIN não contém sessão anterior para aquecer retornos H4")
    calendar = pd.DatetimeIndex(warm["ref_date"])

    controls = {
        "usdbrl": _aligned_return(
            calendar, market["usdbrl"], value_column="brl_per_usd", role="usdbrl"
        ),
        "soy": _aligned_return(calendar, market["soy"], value_column="adjusted_close", role="soy"),
        "corn_second": _aligned_return(
            calendar,
            market["corn_second"],
            value_column="adjusted_close",
            role="corn_second",
        ),
        "sugar": _aligned_return(
            calendar, market["sugar"], value_column="adjusted_close", role="sugar"
        ),
        "oni": _oni_asof(calendar, oni),
    }
    factor_frame = warm.set_index("ref_date")[list(FACTOR_COLUMNS)]
    out = factor_frame.join(pd.DataFrame(controls), how="left")
    out = out.loc[out.index >= H4_START].copy()
    out.insert(0, "avail_date", pd.Timestamp(snapshot_avail_date).normalize())
    out = out.reset_index()
    out = out[
        [
            "ref_date",
            "avail_date",
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
            "risk_free",
        ]
    ]
    validate_h4_controls(out)
    return out
