"""Materialização return-agnóstica do score geográfico placebo H5 (D-070/D-071).

Somente a chuva muda de lugar. O painel municipal CHIRPS já congelado é agregado nas 91
células costeiras de D-070; depois, cada janela de ``PRIMARY_WINDOWS`` é recalculada com a
mesma climatologia expanding e os mesmos pesos nacionais CONAB do sinal real.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from quantagro.backtest.operational_spec import (
    GRAIN_CROPS,
    TradeBlock,
    grain_mechanism_score,
    require_backtest_scope,
)
from quantagro.backtest.strategy_spec import GRAIN_NAMES
from quantagro.features.exposure import exposure_asof
from quantagro.features.shock import (
    FINAL_LAG_DAYS,
    PRELIM_LAG_DAYS,
    conab_uf_weights,
)
from quantagro.features.shock_spec import (
    CLIMATOLOGY_KIND,
    EXPANDING_STD_DDOF,
    MIN_EXPANDING_YEARS,
    PRECIP_Z_TO_STRESS,
    PRIMARY_SIGNAL_KIND,
    PRIMARY_WINDOWS,
    CropRegionWindow,
    critical_period,
    crop_year_start,
)
from quantagro.validate.pit import available_asof, stamp_avail_date

from .h5_geography_spec import (
    H5_PLACEBO_CODES,
    H5_PLACEBO_MUNICIPALITIES,
    H5_TOTAL_CELLS,
)


def build_placebo_daily_precip(municipal: pd.DataFrame) -> pd.DataFrame:
    """Agrega as 91 células fixas em uma precipitação diária placebo."""
    required = {
        "ref_date",
        "kind",
        "municipality_code",
        "precip_mm",
        "n_cells",
        "n_valid_cells",
    }
    missing = required - set(municipal.columns)
    if missing:
        raise ValueError(f"painel municipal H5 sem colunas: {sorted(missing)}")
    selected = municipal[municipal["municipality_code"].isin(H5_PLACEBO_CODES)].copy()
    selected["ref_date"] = pd.to_datetime(selected["ref_date"]).dt.normalize()
    key = ["ref_date", "kind", "municipality_code"]
    if selected.empty or selected.duplicated(key).any():
        raise ValueError("painel municipal H5 vazio ou duplicado")
    unknown_kind = set(selected["kind"]) - {PRIMARY_SIGNAL_KIND, CLIMATOLOGY_KIND}
    if unknown_kind:
        raise ValueError(f"kind CHIRPS desconhecido no H5: {sorted(unknown_kind)}")

    expected_cells = {
        municipality.municipality_code: municipality.n_cells
        for municipality in H5_PLACEBO_MUNICIPALITIES
    }
    observed_cells = selected.groupby("municipality_code")["n_cells"].agg(["min", "max"])
    if set(observed_cells.index) != set(H5_PLACEBO_CODES):
        raise ValueError("painel H5 não cobre todos os municípios congelados")
    for code, cells in expected_cells.items():
        row = observed_cells.loc[code]
        if int(row["min"]) != cells or int(row["max"]) != cells:
            raise ValueError(f"contagem de células H5 diverge para {code}")
    if not selected["n_valid_cells"].eq(selected["n_cells"]).all():
        raise ValueError("painel H5 contém célula CHIRPS nodata")
    precip = pd.to_numeric(selected["precip_mm"], errors="raise").astype("float64")
    if not np.isfinite(precip).all() or (precip < 0).any():
        raise ValueError("precipitação H5 deve ser finita e não-negativa")
    counts = selected.groupby(["kind", "ref_date"])["municipality_code"].nunique()
    if not counts.eq(len(H5_PLACEBO_CODES)).all():
        raise ValueError("raster-dia H5 não cobre os cinco municípios")

    selected["_weighted_precip"] = precip * selected["n_cells"].astype("float64")
    grouped = (
        selected.groupby(["ref_date", "kind"], as_index=False)
        .agg(weighted_precip=("_weighted_precip", "sum"), n_cells=("n_cells", "sum"))
        .sort_values(["kind", "ref_date"])
    )
    if not grouped["n_cells"].eq(H5_TOTAL_CELLS).all():
        raise ValueError("raster-dia H5 não soma 91 células")
    grouped["precip_mm"] = grouped["weighted_precip"] / grouped["n_cells"]
    grouped = grouped[["ref_date", "kind", "precip_mm", "n_cells"]]

    parts = []
    for kind, lag in ((PRIMARY_SIGNAL_KIND, PRELIM_LAG_DAYS), (CLIMATOLOGY_KIND, FINAL_LAG_DAYS)):
        part = grouped[grouped["kind"] == kind]
        if not part.empty:
            parts.append(stamp_avail_date(part, lag_days=lag))
    if len(parts) != 2:
        raise ValueError("painel H5 exige os produtos prelim e final")
    return (
        pd.concat(parts, ignore_index=True).sort_values(["kind", "ref_date"]).reset_index(drop=True)
    )


def _window_sum(
    visible: pd.DataFrame,
    kind: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> float:
    selected = visible[
        (visible["kind"] == kind) & (visible["ref_date"] >= start) & (visible["ref_date"] <= end)
    ]
    expected = pd.date_range(start, end, freq="D")
    observed = pd.DatetimeIndex(selected["ref_date"])
    if len(selected) != len(expected) or not observed.equals(expected):
        missing = expected.difference(observed)
        raise ValueError(
            f"painel H5 sem cobertura diária em {start.date()}–{end.date()}: "
            f"{len(missing)} ausente(s)"
        )
    values = selected["precip_mm"].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("painel H5 contém precipitação ausente")
    return float(values.sum())


def placebo_window_shock_asof(
    t,
    ano_agricola: str,
    spec: CropRegionWindow,
    daily_stamped: pd.DataFrame,
    climatology_first_year: int,
) -> dict[str, object]:
    """Shock placebo para uma janela real de cultura/UF, observável em ``t``."""
    visible = available_asof(daily_stamped, pd.Timestamp(t))
    start, end = critical_period(spec, ano_agricola)
    prelim = visible[visible["kind"] == PRIMARY_SIGNAL_KIND]
    last_ref = prelim["ref_date"].max() if not prelim.empty else pd.NaT
    cut = min(end, last_ref) if pd.notna(last_ref) else pd.NaT
    base = {
        "asof_date": pd.Timestamp(t),
        "ano_agricola": ano_agricola,
        "crop": spec.crop,
        "uf_window": spec.uf,
        "window_start": start,
        "window_end": end,
    }
    if pd.isna(cut) or cut < start:
        return base | {
            "cut_date": pd.NaT,
            "elapsed_days": pd.NA,
            "n_clim_years": 0,
            "shock": np.nan,
            "status": "window_not_started",
        }
    elapsed = int((cut - start).days)
    current = _window_sum(prelim, PRIMARY_SIGNAL_KIND, start, cut)
    current_start_year = crop_year_start(ano_agricola)
    years = range(climatology_first_year, current_start_year)
    if len(years) < MIN_EXPANDING_YEARS:
        raise ValueError(f"climatologia H5 tem {len(years)} safras; mínimo é 10")
    final = visible[visible["kind"] == CLIMATOLOGY_KIND]
    history = []
    for year in years:
        hist_start, _ = critical_period(spec, f"{year}/{(year + 1) % 100:02d}")
        history.append(
            _window_sum(
                final,
                CLIMATOLOGY_KIND,
                hist_start,
                hist_start + pd.Timedelta(days=elapsed),
            )
        )
    values = np.asarray(history, dtype=float)
    std = float(values.std(ddof=EXPANDING_STD_DDOF))
    if not np.isfinite(std) or std <= 0:
        raise ValueError(f"climatologia H5 degenerada para {spec.key}: std={std}")
    z = (current - float(values.mean())) / std
    return base | {
        "cut_date": cut,
        "elapsed_days": elapsed,
        "n_clim_years": len(values),
        "shock": float(PRECIP_Z_TO_STRESS * z),
        "status": "ok",
    }


def placebo_national_shocks_asof(
    t,
    ano_agricola: str,
    daily_stamped: pd.DataFrame,
    conab_stamped: pd.DataFrame,
    climatology_first_year: int,
) -> dict[str, float | None]:
    """Agrega as janelas placebo com os mesmos pesos CONAB do Shock real."""
    by_crop: dict[str, float | None] = {}
    for crop in GRAIN_CROPS:
        specs = tuple(spec for spec in PRIMARY_WINDOWS if spec.crop == crop)
        weights = conab_uf_weights(
            conab_stamped,
            specs[0],
            [spec.uf for spec in specs],
            ano_agricola,
            t,
        )
        rows = [
            placebo_window_shock_asof(
                t,
                ano_agricola,
                spec,
                daily_stamped,
                climatology_first_year,
            )
            for spec in specs
        ]
        ok = [row for row in rows if row["status"] == "ok"]
        if not ok:
            by_crop[crop] = None
            continue
        invalid = {str(row["status"]) for row in rows} - {"ok", "window_not_started"}
        if invalid:
            raise ValueError(f"status técnico inválido no H5/{crop}: {sorted(invalid)}")
        active_weights = weights.loc[[str(row["uf_window"]) for row in ok]]
        coverage = float(active_weights.sum())
        by_crop[crop] = float(
            sum(
                weight * float(row["shock"]) for weight, row in zip(active_weights, ok, strict=True)
            )
            / coverage
        )
    return by_crop


def validate_h5_grain_scores(scores: pd.DataFrame) -> None:
    """Valida o input H5 no mesmo schema do score bruto real de grãos."""
    if tuple(scores.columns) != GRAIN_NAMES:
        raise ValueError(f"schema de scores H5 inesperado: {list(scores.columns)!r}")
    if not isinstance(scores.index, pd.DatetimeIndex):
        raise ValueError("scores H5 exigem DatetimeIndex de decisão")
    if scores.empty or scores.index.has_duplicates or not scores.index.is_monotonic_increasing:
        raise ValueError("scores H5 vazios, duplicados ou fora de ordem")
    if scores.isna().any().any() or not np.isfinite(scores.to_numpy()).all():
        raise ValueError("scores H5 contêm valor ausente ou infinito")


def materialize_h5_grain_scores(
    blocks: Sequence[TradeBlock],
    registry: pd.DataFrame,
    daily_stamped: pd.DataFrame,
    conab_stamped: pd.DataFrame,
    climatology_first_year: int,
    *,
    allow_holdout: bool = False,
) -> pd.DataFrame:
    """Materializa ``E·Shock_placebo`` sem ler retornos ou alterar H′."""
    frozen = tuple(blocks)
    require_backtest_scope(frozen, allow_holdout=allow_holdout)
    rows = []
    for block in frozen:
        shocks = placebo_national_shocks_asof(
            block.decision_date,
            block.crop_year,
            daily_stamped,
            conab_stamped,
            climatology_first_year,
        )
        exposures = exposure_asof(registry, block.decision_date)
        values: dict[str, float] = {}
        for ticker in GRAIN_NAMES:
            selected = exposures[exposures["ticker"] == ticker]
            if selected.empty:
                raise ValueError(
                    f"exposição H′ ausente para {ticker} em {block.decision_date.date()}"
                )
            exposure = dict(zip(selected["crop"], selected["exposure"], strict=True))
            values[ticker] = grain_mechanism_score(exposure, shocks)
        rows.append({"decision_date": block.decision_date} | values)
    out = pd.DataFrame(rows).set_index("decision_date").sort_index()
    out.index = pd.DatetimeIndex(out.index)
    out = out.reindex(columns=GRAIN_NAMES)
    validate_h5_grain_scores(out)
    return out
