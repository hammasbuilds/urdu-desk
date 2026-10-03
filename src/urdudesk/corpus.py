"""BBC Urdu news, as XL-Sum published it.

84,581 articles with their summaries. Nothing here has been cleaned, which is
the reason to use it: every claim in this repository is about what real Urdu
text contains, and a tidied corpus would answer a different question.

    from urdudesk import corpus

    train = corpus.load("train")
    train[0].text          # the article body
    train[0].summary       # the one-line summary BBC wrote
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# The repository's data/ directory, unless URDUDESK_DATA points elsewhere
# (needed for a non-editable install, and for running the tests hermetically).
DATA = Path(os.environ.get("URDUDESK_DATA") or Path(__file__).resolve().parents[2] / "data")
SPLITS = ("train", "validation", "test")


class CorpusMissingError(FileNotFoundError):
    """The corpus is not on disk."""


@dataclass(frozen=True)
class Article:
    title: str
    text: str
    summary: str

    @property
    def everything(self) -> str:
        return f"{self.title}\n{self.summary}\n{self.text}"


@lru_cache(maxsize=4)
def load(split: str = "validation") -> tuple[Article, ...]:
    if split not in SPLITS:
        raise ValueError(f"unknown split {split!r}; have {SPLITS}")
    path = DATA / f"{split}.parquet"
    if not path.exists():
        raise CorpusMissingError(
            f"{path} is missing. Run scripts/fetch_data.py, which pulls the "
            "Urdu half of XL-Sum, or set URDUDESK_DATA to a directory holding it."
        )

    import pyarrow.parquet as pq

    rows = pq.read_table(path).to_pylist()
    return tuple(
        Article(
            title=row.get("title", "") or "",
            text=row.get("text", "") or "",
            summary=row.get("summary", "") or "",
        )
        for row in rows
    )


def available() -> list[str]:
    """Splits that are on disk AND readable.

    A file that exists is not the same as a corpus that is there: a download in
    flight leaves a real file at the real path that is not yet a parquet. The
    fetcher writes to a `.part` and renames, so that should not happen — this
    checks anyway, because a corrupt split reported as available turns into an
    error deep inside a measurement rather than here.
    """
    import pyarrow.parquet as pq

    out = []
    for split in SPLITS:
        path = DATA / f"{split}.parquet"
        if not path.exists():
            continue
        try:
            pq.read_metadata(path)
        except Exception:
            continue
        out.append(split)
    return out
