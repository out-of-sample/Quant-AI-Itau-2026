"""Captura e regionaliza o CHIRPS mensal exigido pela cana (D-050).

O processo é incremental: rasters globais ficam apenas em memória, cada lote vira Parquet local
e um manifesto consolidado preserva URL, hash e tamanho. PAM e malha fixa são capturadas antes.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, "src")
from quantagro.features.cane_panel import required_cane_monthly_files  # noqa: E402
from quantagro.features.panel import build_cell_index  # noqa: E402
from quantagro.features.regionalize import municipal_monthly_precip  # noqa: E402
from quantagro.ingest.chirps import (  # noqa: E402
    chirps_monthly_url,
    download_chirps_monthly,
)
from quantagro.ingest.ibge_geometry import (  # noqa: E402
    download_geometry,
    parse_geometry,
)
from quantagro.ingest.pam import download_pam  # noqa: E402

UFS = ("SP", "MG", "GO", "MS", "PR")
INDEX_PATH = Path("data/interim/cane_municipal_cell_index.parquet")
PARTS_DIR = Path("data/interim/cane_monthly_precip")
MANIFEST_PATH = Path("data/manifests/chirps_cane_monthly_bulk.parquet")
_local = threading.local()


def _session() -> requests.Session:
    session = getattr(_local, "session", None)
    if session is None:
        session = requests.Session()
        _local.session = session
    return session


def _prepare_static_inputs() -> None:
    download_pam("sugarcane", range(2014, 2025), UFS)
    geometry = []
    for uf in UFS:
        path = download_geometry(uf)
        geometry.append(parse_geometry(path, uf))
    if not INDEX_PATH.exists():
        sample = download_chirps_monthly("2000-01-01", "final")
        index = build_cell_index(pd.concat(geometry, ignore_index=True), sample)
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        index.to_parquet(INDEX_PATH, index=False)


def _fetch(date, kind: str, index: pd.DataFrame):
    url = chirps_monthly_url(date, kind)
    last = None
    for attempt in range(4):
        try:
            response = _session().get(url, timeout=300)
            response.raise_for_status()
            content = response.content
            break
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 * (attempt + 1))
    else:
        raise RuntimeError(f"falha ao baixar {url}: {last}")
    rows = municipal_monthly_precip([(date, kind, content)], index)
    manifest = {
        "ref_date": pd.Timestamp(date),
        "kind": kind,
        "url": url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "nbytes": len(content),
    }
    return rows, manifest


def _done() -> set[tuple[pd.Timestamp, str]]:
    if not MANIFEST_PATH.exists():
        return set()
    frame = pd.read_parquet(MANIFEST_PATH, columns=["ref_date", "kind"])
    return set(zip(pd.to_datetime(frame["ref_date"]), frame["kind"], strict=True))


def _append_manifest(rows: list[dict]) -> None:
    new = pd.DataFrame(rows)
    if MANIFEST_PATH.exists():
        new = pd.concat([pd.read_parquet(MANIFEST_PATH), new], ignore_index=True)
    new = new.drop_duplicates(["ref_date", "kind"]).sort_values(["kind", "ref_date"])
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    new.to_parquet(MANIFEST_PATH, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--batch", type=int, default=12)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    _prepare_static_inputs()
    index = pd.read_parquet(INDEX_PATH)
    required = required_cane_monthly_files()
    done = _done()
    todo = [
        (row.ref_date, row.kind)
        for row in required.itertuples(index=False)
        if (row.ref_date, row.kind) not in done
    ]
    if args.limit is not None:
        todo = todo[: args.limit]
    print(f"necessários={len(required)} já_feitos={len(done)} a_fazer={len(todo)}", flush=True)
    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    part_no = len(list(PARTS_DIR.glob("part_*.parquet")))
    for start in range(0, len(todo), args.batch):
        chunk = todo[start : start + args.batch]
        frames, manifests = [], []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(_fetch, d, k, index): (d, k) for d, k in chunk}
            for future in as_completed(futures):
                frame, manifest = future.result()
                frames.append(frame)
                manifests.append(manifest)
        pd.concat(frames, ignore_index=True).to_parquet(
            PARTS_DIR / f"part_{part_no:05d}.parquet", index=False
        )
        part_no += 1
        _append_manifest(manifests)
        print(f"  {min(start + len(chunk), len(todo))}/{len(todo)}", flush=True)


if __name__ == "__main__":
    main()
