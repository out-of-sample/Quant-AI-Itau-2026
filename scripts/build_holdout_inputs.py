"""Materializa e atesta os inputs lacrados da rodada única sem calcular P&L.

O comando é offline: todos os seis COTAHIST anuais, o snapshot de eventos e os painéis
climáticos precisam existir. Somente cobertura, schema e hashes são impressos/registrados;
nenhuma média, retorno individual, curva ou resultado da estratégia é exibido.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import tempfile
from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from quantagro.backtest.holdout import attest_file  # noqa: E402
from quantagro.backtest.holdout_spec import (  # noqa: E402
    HOLDING_SENSITIVITY_SESSIONS,
    PACKAGE_ID,
    REQUIRED_INPUTS,
    TOTAL_SIGNAL_LAG_SENSITIVITY_DAYS,
    spec_sha256,
)
from quantagro.backtest.inputs import (  # noqa: E402
    materialize_cane_signal,
    materialize_grain_raw_scores,
)
from quantagro.backtest.operational_spec import (  # noqa: E402
    ADTV_FLOOR_BRL,
    HOLDING_SESSIONS,
    build_trade_blocks,
)
from quantagro.backtest.strategy_spec import HOLDOUT_CROP_YEARS, UNIVERSE  # noqa: E402
from quantagro.features.cane_shock import stamp_cane_monthly_panel  # noqa: E402
from quantagro.features.exposure import load_exposure_registry  # noqa: E402
from quantagro.features.panel import CLIMATOLOGY_FIRST_YEAR  # noqa: E402
from quantagro.features.shock import (  # noqa: E402
    municipal_cumulative_index,
    stamp_municipal_panel,
)
from quantagro.ingest.conab import parse_levantamento  # noqa: E402
from quantagro.ingest.cotahist import filter_equities_spot, parse_cotahist  # noqa: E402
from quantagro.ingest.events_manual import manual_events  # noqa: E402
from quantagro.ingest.events_snapshot import events_from_snapshot, load_snapshot  # noqa: E402
from quantagro.ingest.pam import parse_pam  # noqa: E402
from quantagro.prices.assemble import (  # noqa: E402
    assemble_total_return,
    close_series,
    flag_suspect_returns,
)
from quantagro.stats.cane_h1 import _prepare_conab  # noqa: E402
from quantagro.stats.h2a import _stamp_grains  # noqa: E402
from quantagro.validate.universe import universe_state  # noqa: E402

YEARS = tuple(range(2020, 2026))
SNAPSHOT = Path("data/reference/corporate_events_holdout_v1.json")
EXCEPTIONS = Path("data/reference/price_return_exceptions_holdout_v1.json")
SUMMARY = Path("data/reference/holdout_inputs_summary_v1.json")
PRIMARY_LAG_DAYS = 7
IPO_SEASONING = 60


def _pam(pattern: str) -> pd.DataFrame:
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"PAM ausente: {pattern}")
    return pd.concat((parse_pam(path) for path in files), ignore_index=True)


def _quotes() -> pd.DataFrame:
    frames = []
    for year in YEARS:
        path = Path(f"data/raw/COTAHIST_A{year}.ZIP")
        if not path.is_file():
            raise FileNotFoundError(f"COTAHIST ausente: {path}")
        frames.append(filter_equities_spot(parse_cotahist(path)))
    return pd.concat(frames, ignore_index=True)


def _exceptions() -> dict[str, dict[pd.Timestamp, tuple[float, float]]]:
    payload = json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    if payload.get("purpose") != "audited_extreme_raw_returns_in_holdout":
        raise ValueError("registro de extremos não pertence ao holdout")
    return {
        ticker: {
            pd.Timestamp(row["date"]): (
                float(row["expected_return"]),
                float(row["absolute_tolerance"]),
            )
            for row in payload["exceptions"]
            if row["ticker"] == ticker
        }
        for ticker in UNIVERSE
    }


def _validate_extremes(
    flagged: pd.Series,
    allowed: dict[pd.Timestamp, tuple[float, float]],
    ticker: str,
) -> None:
    unused = set(allowed) - set(flagged.index)
    if unused:
        raise RuntimeError(f"{ticker}: exceções declaradas não aparecem: {sorted(unused)}")
    unexpected = flagged[~flagged.index.isin(allowed)]
    if len(unexpected):
        dates = [date.date().isoformat() for date in unexpected.index]
        raise RuntimeError(
            f"{ticker}: retorno(s) extremo(s) não auditado(s) em {dates}; "
            "interrompido sem gravar o pacote"
        )
    for date, observed in flagged.items():
        expected, tolerance = allowed[date]
        if not np.isclose(float(observed), expected, rtol=0, atol=tolerance):
            raise RuntimeError(f"{ticker}: extremo auditado mudou em {date.date()}")


def build_returns(quotes: pd.DataFrame) -> pd.DataFrame:
    snapshot = load_snapshot(SNAPSHOT)
    allowed = _exceptions()
    series = {}
    for ticker in UNIVERSE:
        close = close_series(quotes, ticker)
        cash, fallback, stock = events_from_snapshot(snapshot, ticker)
        returns = assemble_total_return(
            close,
            cash_primary=cash,
            cash_fallback=fallback,
            stock=stock + manual_events(ticker),
        )
        _validate_extremes(flag_suspect_returns(returns.dropna()), allowed[ticker], ticker)
        series[ticker] = returns
    sessions = pd.DatetimeIndex(sorted(quotes["date"].unique()), name="date")
    panel = pd.DataFrame(series).reindex(sessions).loc[:, list(UNIVERSE)]
    observed = panel.to_numpy(dtype=float, na_value=np.nan)
    if np.isinf(observed).any() or np.nanmin(observed) < -1:
        raise ValueError("painel de retornos contém infinito ou retorno abaixo de -100%")
    return panel


def build_market_state(quotes: pd.DataFrame) -> pd.DataFrame:
    state = universe_state(
        quotes,
        adtv_floor=ADTV_FLOOR_BRL,
        tickers=list(UNIVERSE),
        ipo_seasoning=IPO_SEASONING,
    )
    frames = {
        "traded": state.traded,
        "seasoned": state.seasoned,
        "adtv_brl": state.adtv_brl,
        "eligible": state.eligible,
        "reason": state.reason,
    }
    columns = {}
    for name, frame in frames.items():
        melted = (
            frame.rename_axis(index="date", columns="ticker")
            .reset_index()
            .melt(id_vars="date", var_name="ticker", value_name=name)
        )
        columns[name] = melted.set_index(["date", "ticker"])[name]
    return (
        pd.concat(columns, axis=1).reset_index().sort_values(["date", "ticker"], ignore_index=True)
    )


def _feature_blocks(sessions: pd.DatetimeIndex) -> tuple:
    by_date = {}
    horizons = (HOLDING_SESSIONS, *HOLDING_SENSITIVITY_SESSIONS)
    for horizon in horizons:
        for crop_year in HOLDOUT_CROP_YEARS:
            for block in build_trade_blocks(sessions, crop_year, holding_sessions=horizon):
                previous = by_date.get(block.decision_date)
                if previous is not None and previous.crop_year != block.crop_year:
                    raise RuntimeError("mesma decisão foi atribuída a duas safras")
                by_date.setdefault(block.decision_date, block)
    return tuple(by_date[date] for date in sorted(by_date))


def _grain_sources():
    conab = _stamp_grains(
        parse_levantamento("data/raw/conab/LevantamentoGraos_20260716.txt", "graos")
    )
    pam = pd.concat(
        [
            _pam("data/raw/pam/pam_1612_soy_*.json"),
            _pam("data/raw/pam/pam_1612_corn_total_*.json"),
        ],
        ignore_index=True,
    )
    parts = sorted(glob.glob("data/interim/municipal_precip/part_*.parquet"))
    if not parts:
        raise FileNotFoundError("painel municipal de grãos ausente")
    municipal = pd.concat((pd.read_parquet(path) for path in parts), ignore_index=True)
    municipal = municipal.drop_duplicates(["ref_date", "kind", "municipality_code"])
    municipal = municipal[municipal["municipality_code"].isin(set(pam["municipality_code"]))]
    municipal = stamp_municipal_panel(
        municipal.sort_values(["kind", "ref_date"]).reset_index(drop=True)
    )
    registry = load_exposure_registry("data/reference/exposure_hprime_v1.json")
    return registry, municipal, municipal_cumulative_index(municipal), pam, conab


def _cane_sources():
    conab = _prepare_conab(
        parse_levantamento("data/raw/conab/LevantamentoCana_20260716.txt", "cana")
    )
    pam = _pam("data/raw/pam/pam_1612_sugarcane_*.json")
    parts = sorted(glob.glob("data/interim/cane_monthly_precip/part_*.parquet"))
    if not parts:
        raise FileNotFoundError("painel mensal de cana ausente")
    monthly = pd.concat((pd.read_parquet(path) for path in parts), ignore_index=True)
    monthly = monthly.drop_duplicates(["ref_date", "kind", "municipality_code"])
    return stamp_cane_monthly_panel(monthly), pam, conab


def build_signals(sessions: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_variant_blocks = _feature_blocks(sessions)
    primary_blocks = tuple(
        block
        for crop_year in HOLDOUT_CROP_YEARS
        for block in build_trade_blocks(sessions, crop_year)
    )
    registry, municipal, municipal_index, grain_pam, grain_conab = _grain_sources()
    monthly, cane_pam, cane_conab = _cane_sources()
    grain_rows = []
    cane_rows = []
    for lag in (PRIMARY_LAG_DAYS, *TOTAL_SIGNAL_LAG_SENSITIVITY_DAYS):
        print(f"features: iniciando lag total {lag} dias", flush=True)
        # Horizonte alternativo muda as datas de decisão, mas os lags 14/21 são
        # single-knob sobre a agenda primária. Não materializar combinações não registradas.
        blocks = all_variant_blocks if lag == PRIMARY_LAG_DAYS else primary_blocks
        grain = materialize_grain_raw_scores(
            blocks,
            registry,
            municipal,
            grain_pam,
            grain_conab,
            CLIMATOLOGY_FIRST_YEAR,
            allow_holdout=True,
            total_signal_lag_days=lag,
            municipal_cumulative_index=municipal_index,
        )
        grain.insert(0, "total_signal_lag_days", lag)
        grain_rows.append(grain.reset_index(names="decision_date"))

        cane = materialize_cane_signal(
            blocks,
            monthly,
            cane_pam,
            cane_conab,
            CLIMATOLOGY_FIRST_YEAR,
            allow_holdout=True,
            total_signal_lag_days=lag,
        )
        cane.insert(0, "total_signal_lag_days", lag)
        cane_rows.append(cane.reset_index(names="decision_date"))
        print(f"features: lag total {lag} dias concluído", flush=True)
    return (
        pd.concat(grain_rows, ignore_index=True),
        pd.concat(cane_rows, ignore_index=True),
    )


def _atomic_parquet(frame: pd.DataFrame, path: Path, *, index: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    temp_path = Path(temporary)
    try:
        frame.to_parquet(temp_path, index=index)
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def _source_paths() -> list[Path]:
    fixed = [
        SNAPSHOT,
        EXCEPTIONS,
        Path("data/reference/exposure_hprime_v1.json"),
        Path("data/raw/conab/LevantamentoGraos_20260716.txt"),
        Path("data/raw/conab/LevantamentoCana_20260716.txt"),
        Path("data/reference/h4_controls_summary_v1.json"),
        Path("data/reference/h5_geographic_scores_summary_v1.json"),
    ]
    patterns = [
        "data/raw/COTAHIST_A202*.ZIP",
        "data/manifests/cotahist_A202*.json",
        "data/raw/pam/pam_1612_soy_*.json",
        "data/raw/pam/pam_1612_corn_total_*.json",
        "data/raw/pam/pam_1612_sugarcane_*.json",
        "data/interim/municipal_precip/part_*.parquet",
        "data/interim/cane_monthly_precip/part_*.parquet",
    ]
    paths = fixed + [Path(path) for pattern in patterns for path in sorted(glob.glob(pattern))]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"fontes do pacote ausentes: {missing}")
    return sorted(set(paths))


def _record(path: Path) -> dict[str, object]:
    attestation = attest_file(path)
    return {
        "path": str(path),
        "bytes": attestation.bytes,
        "sha256": attestation.sha256,
    }


def _verify_reusable_signals() -> tuple[pd.DataFrame, pd.DataFrame]:
    manifest_path = Path(REQUIRED_INPUTS["input_manifest"])
    if not manifest_path.is_file():
        raise FileNotFoundError("--reuse-signals exige o manifesto anterior")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = payload.get("inputs")
    if not isinstance(records, dict):
        raise ValueError("manifesto anterior não contém registros de input")
    frames = []
    for role in ("grain_scores", "cane_signal"):
        path = Path(REQUIRED_INPUTS[role])
        record = records.get(role)
        if not path.is_file() or not isinstance(record, dict):
            raise FileNotFoundError(f"--reuse-signals exige registro e parquet de {role}")
        observed = _record(path)
        if (
            record.get("path") != observed["path"]
            or record.get("bytes") != observed["bytes"]
            or record.get("sha256") != observed["sha256"]
        ):
            raise ValueError(f"feature {role} mudou desde o manifesto anterior")
        frames.append(pd.read_parquet(path))
    return frames[0], frames[1]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reuse-signals",
        action="store_true",
        help="regrava só preços/estado/manifesto e reutiliza features já materializadas",
    )
    args = parser.parse_args()
    print("inputs: carregando COTAHIST e eventos", flush=True)
    quotes = _quotes()
    returns = build_returns(quotes)
    print("inputs: retornos lacrados validados; construindo estado de mercado", flush=True)
    state = build_market_state(quotes)
    sessions = pd.DatetimeIndex(returns.index)
    if args.reuse_signals:
        grain, cane = _verify_reusable_signals()
        expected_lags = {PRIMARY_LAG_DAYS, *TOTAL_SIGNAL_LAG_SENSITIVITY_DAYS}
        if (
            set(grain["total_signal_lag_days"].unique()) != expected_lags
            or set(cane["total_signal_lag_days"].unique()) != expected_lags
        ):
            raise ValueError("features reutilizadas não cobrem os três lags congelados")
        print("inputs: features PIT existentes atestadas para reutilização", flush=True)
    else:
        print("inputs: estado de mercado concluído; construindo features PIT", flush=True)
        grain, cane = build_signals(sessions)
        print("inputs: features concluídas; gravando parquets e manifesto", flush=True)

    _atomic_parquet(returns, Path(REQUIRED_INPUTS["returns"]), index=True)
    _atomic_parquet(state, Path(REQUIRED_INPUTS["market_state"]), index=False)
    _atomic_parquet(grain, Path(REQUIRED_INPUTS["grain_scores"]), index=False)
    _atomic_parquet(cane, Path(REQUIRED_INPUTS["cane_signal"]), index=False)

    inputs = {
        role: _record(Path(path))
        for role, path in REQUIRED_INPUTS.items()
        if role != "input_manifest"
    }
    manifest = {
        "schema_version": 1,
        "package_id": PACKAGE_ID,
        "logical_spec_sha256": spec_sha256(),
        "inputs": inputs,
        "sources": [_record(path) for path in _source_paths()],
    }
    manifest_path = Path(REQUIRED_INPUTS["input_manifest"])
    _write_json(manifest_path, manifest)
    manifest_sha = sha256(manifest_path.read_bytes()).hexdigest()

    summary = {
        "schema_version": 1,
        "package_id": PACKAGE_ID,
        "logical_spec_sha256": spec_sha256(),
        "input_manifest": {
            "path": str(manifest_path),
            "sha256": manifest_sha,
        },
        "coverage": {
            "calendar_sessions": len(returns),
            "start": returns.index.min().date().isoformat(),
            "end": returns.index.max().date().isoformat(),
            "market_state_rows": len(state),
            "grain_signal_rows": len(grain),
            "cane_signal_rows": len(cane),
            "signal_lags_days": sorted(grain["total_signal_lag_days"].unique().tolist()),
        },
        "inputs": inputs,
    }
    _write_json(SUMMARY, summary)
    print(
        f"pacote lacrado materializado: {len(returns)} sessões, "
        f"{len(grain)} linhas de grãos, {len(cane)} linhas de cana"
    )
    print(f"manifesto SHA-256 {manifest_sha}")


if __name__ == "__main__":
    main()
