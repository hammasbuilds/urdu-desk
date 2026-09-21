"""Pull the Urdu half of XL-Sum: real BBC Urdu news, as published.

    python scripts/fetch_data.py

~190 MB across three splits. The corpus matters here for what it is rather than
what it is labelled with: naturally occurring Urdu prose, written by
professional journalists, not normalised or cleaned by anyone in between.

That is the point. Every claim in this repository is about what real Urdu text
actually contains, so a corpus that had been tidied up would answer a different
question.

Byte-ranged and checked against Content-Length: the train shard is 156 MB and a
single GET over this link truncates silently often enough to matter.
"""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
BASE = (
    "https://huggingface.co/datasets/csebuetnlp/xlsum/"
    "resolve/refs%2Fconvert%2Fparquet/urdu"
)
SPLITS = ("validation", "test", "train")
CHUNK = 4_000_000

EXPECT = {"train": 67_665, "validation": 8_458, "test": 8_458}


def expected_size(url: str) -> int:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "urdu-desk"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return int(response.headers["Content-Length"])


def fetch(split: str) -> None:
    out = DATA / f"{split}.parquet"
    url = f"{BASE}/{split}/0000.parquet"
    total = expected_size(url)

    if out.exists() and out.stat().st_size == total:
        print(f"  {out.name} already complete ({total / 1e6:.0f} MB)")
        return

    # Downloaded to a .part and renamed only once the length checks out, so a
    # half-written file is never visible under its real name. Without this a
    # long download makes the split look present-but-corrupt to everything
    # else, and the error surfaces as "parquet magic bytes not found" in a
    # measurement script rather than as "still downloading" here.
    partial = out.with_suffix(out.suffix + ".part")
    print(f"  {out.name}  {total / 1e6:.0f} MB ", end="", flush=True)
    written = 0
    with partial.open("wb") as handle:
        while written < total:
            end = min(written + CHUNK, total) - 1
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "urdu-desk", "Range": f"bytes={written}-{end}"},
            )
            try:
                with urllib.request.urlopen(request, timeout=300) as response:
                    block = response.read()
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                print(f"\n    failed at byte {written:,}: {exc}")
                raise
            if not block:
                raise OSError(f"{out.name}: empty response at byte {written:,}")
            handle.write(block)
            written += len(block)
            print(".", end="", flush=True)

    got = partial.stat().st_size
    if got != total:
        partial.unlink()
        raise OSError(f"{out.name}: got {got:,} bytes, expected {total:,}. Removed.")
    partial.replace(out)
    print(" ok")


def main() -> None:
    DATA.mkdir(exist_ok=True)
    print("fetching XL-Sum (urdu)")
    for split in SPLITS:
        fetch(split)

    import pyarrow.parquet as pq

    print("\nchecking")
    ok = True
    for split in SPLITS:
        rows = pq.read_table(DATA / f"{split}.parquet").num_rows
        want = EXPECT[split]
        good = rows == want
        ok &= good
        print(f"  {split:<11}{rows:>8,}  {'ok' if good else f'EXPECTED {want:,}'}")

    if not ok:
        print("\nThe splits are not the published ones; stop rather than measure "
              "something else.", file=sys.stderr)
        raise SystemExit(1)
    print("\ncorpus ready")


if __name__ == "__main__":
    main()
