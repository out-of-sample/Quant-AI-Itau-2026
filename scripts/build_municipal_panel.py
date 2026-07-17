"""Constrói o painel municipal diário de precipitação CHIRPS para os rodadores de H1.

Estratégia de streaming (ver ``features/panel.py``): cada raster é baixado em memória,
regionalizado com o índice de células cacheado e descartado — o painel municipal (em partes
parquet) é o registro de resumo e de resiliência, e o manifesto consolidado
(``data/manifests/chirps_h1_bulk.parquet``, uma linha por raster com url+sha256) é a prova de
vintage. Idempotente: relê o manifesto e pula o que já foi baixado.

Uso:
    python scripts/build_municipal_panel.py            # run completo (~6197 rasters)
    python scripts/build_municipal_panel.py --limit 40 # amostra p/ medir throughput
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
from quantagro.features.panel import required_files  # noqa: E402
from quantagro.features.regionalize import municipal_daily_precip  # noqa: E402
from quantagro.ingest.chirps import chirps_url  # noqa: E402

INDEX_PATH = Path("data/interim/municipal_cell_index.parquet")
PARTS_DIR = Path("data/interim/municipal_precip")
MANIFEST_PATH = Path("data/manifests/chirps_h1_bulk.parquet")

_local = threading.local()


def _session() -> requests.Session:
    s = getattr(_local, "session", None)
    if s is None:
        s = requests.Session()
        _local.session = s
    return s


def fetch_and_regionalize(date, kind: str, index: pd.DataFrame):
    """Baixa um raster (com retry) e devolve (linhas municipais, linha de manifesto)."""
    url = chirps_url(date, kind)
    last = None
    for attempt in range(4):
        try:
            resp = _session().get(url, timeout=300)
            resp.raise_for_status()
            content = resp.content
            break
        except Exception as exc:  # noqa: BLE001 - rede: registrar e tentar de novo
            last = exc
            time.sleep(2 * (attempt + 1))
    else:
        raise RuntimeError(f"falha ao baixar {url}: {last}")
    rows = municipal_daily_precip([(pd.Timestamp(date), kind, content)], index)
    man = {
        "ref_date": pd.Timestamp(date),
        "kind": kind,
        "url": url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "nbytes": len(content),
    }
    return rows, man


def _load_done() -> set[tuple[pd.Timestamp, str]]:
    if not MANIFEST_PATH.exists():
        return set()
    man = pd.read_parquet(MANIFEST_PATH, columns=["ref_date", "kind"])
    return set(zip(pd.to_datetime(man["ref_date"]), man["kind"], strict=True))


def _next_part_no() -> int:
    if not PARTS_DIR.exists():
        return 0
    parts = sorted(PARTS_DIR.glob("part_*.parquet"))
    return len(parts)


def _append_manifest(mans: list[dict]) -> None:
    new = pd.DataFrame(mans)
    if MANIFEST_PATH.exists():
        old = pd.read_parquet(MANIFEST_PATH)
        new = pd.concat([old, new], ignore_index=True)
    new = new.drop_duplicates(["ref_date", "kind"]).sort_values(["kind", "ref_date"])
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    new.to_parquet(MANIFEST_PATH, index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="máximo de rasters (amostra)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--batch", type=int, default=240)
    args = ap.parse_args()

    index = pd.read_parquet(INDEX_PATH)
    req = required_files()
    done = _load_done()
    todo = [
        (r.ref_date, r.kind)
        for r in req.itertuples(index=False)
        if (r.ref_date, r.kind) not in done
    ]
    if args.limit is not None:
        todo = todo[: args.limit]
    print(f"necessários={len(req)} já_feitos={len(done)} a_fazer={len(todo)}", flush=True)
    if not todo:
        print("nada a fazer — painel completo.", flush=True)
        return

    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    part_no = _next_part_no()
    t0 = time.time()
    processed = 0
    for i in range(0, len(todo), args.batch):
        chunk = todo[i : i + args.batch]
        frames: list[pd.DataFrame] = []
        mans: list[dict] = []
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(fetch_and_regionalize, d, k, index): (d, k) for d, k in chunk}
            for fut in as_completed(futs):
                rows, man = fut.result()
                frames.append(rows)
                mans.append(man)
        part = pd.concat(frames, ignore_index=True)
        part.to_parquet(PARTS_DIR / f"part_{part_no:05d}.parquet", index=False)
        part_no += 1
        _append_manifest(mans)
        processed += len(chunk)
        rate = processed / (time.time() - t0)
        eta = (len(todo) - processed) / rate / 60 if rate else float("nan")
        print(
            f"  {processed}/{len(todo)} rasters | {rate:.1f}/s | ETA {eta:.0f} min",
            flush=True,
        )
    print(f"concluído: {processed} rasters em {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
