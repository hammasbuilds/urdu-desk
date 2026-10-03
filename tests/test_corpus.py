"""Against the real XL-Sum Urdu parquet.

`test_available_skips_an_unreadable_split` is the one worth having: a 156 MB
download in flight leaves a real file at the real path that is not yet a
parquet, and a loader that trusts `exists()` reports it as a usable corpus.
"""

from __future__ import annotations

import pytest

from urdudesk import corpus, script

HAVE = corpus.available()
NEEDS_CORPUS = pytest.mark.skipif(
    not HAVE,
    reason="XL-Sum Urdu not on disk: run `python scripts/fetch_data.py` "
    "(or set URDUDESK_DATA)",
)
SIZES = {"train": 67_665, "validation": 8_458, "test": 8_458}


@NEEDS_CORPUS
def test_split_sizes():
    for split in HAVE:
        assert len(corpus.load(split)) == SIZES[split]


def test_missing_corpus_says_how_to_get_it(tmp_path, monkeypatch):
    monkeypatch.setattr(corpus, "DATA", tmp_path)
    corpus.load.cache_clear()
    with pytest.raises(corpus.CorpusMissingError, match="fetch_data.py"):
        corpus.load("test")
    assert corpus.available() == []


def test_unknown_split_is_rejected():
    with pytest.raises(ValueError):
        corpus.load("dev")


def test_available_skips_an_unreadable_split(tmp_path, monkeypatch):
    """A half-written file must not count as a corpus."""
    monkeypatch.setattr(corpus, "DATA", tmp_path)
    (tmp_path / "test.parquet").write_bytes(b"not a parquet at all")
    assert "test" not in corpus.available()


@NEEDS_CORPUS
def test_articles_have_text():
    split = HAVE[0]
    articles = corpus.load(split)
    assert all(a.text.strip() for a in articles)
    assert all(a.summary.strip() for a in articles)


@NEEDS_CORPUS
def test_the_corpus_really_is_urdu():
    split = HAVE[0]
    """Guards against silently loading a different language config."""
    articles = corpus.load(split)[:200]
    urdu_chars = sum(
        1 for a in articles for ch in a.text[:500] if "؀" <= ch <= "ۿ"
    )
    total = sum(len(a.text[:500]) for a in articles)
    assert urdu_chars / total > 0.5


@NEEDS_CORPUS
def test_some_articles_use_arabic_letters():
    split = HAVE[0]
    """The premise of the repository. If this ever hits zero, either the
    corpus was cleaned upstream or the detector broke."""
    articles = corpus.load(split)
    affected = sum(1 for a in articles if script.has_arabic_variants(a.everything))
    assert 0 < affected / len(articles) < 0.5


@NEEDS_CORPUS
def test_normalising_never_grows_the_vocabulary():
    split = HAVE[0]
    """Merging can only ever reduce the number of distinct types."""
    articles = corpus.load(split)[:2000]
    raw = {w for a in articles for w in script.words(a.everything)}
    merged = {script.normalise(w) for w in raw}
    assert len(merged) <= len(raw)
