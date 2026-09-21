"""Against the real XL-Sum Urdu parquet.

`test_available_skips_an_unreadable_split` is the one worth having: a 156 MB
download in flight leaves a real file at the real path that is not yet a
parquet, and a loader that trusts `exists()` reports it as a usable corpus.
"""

from __future__ import annotations

import pytest

from urdudesk import corpus, script

HAVE = corpus.available()
SIZES = {"train": 67_665, "validation": 8_458, "test": 8_458}


@pytest.mark.parametrize("split", [s for s in SIZES if s in HAVE])
def test_split_sizes(split):
    assert len(corpus.load(split)) == SIZES[split]


def test_at_least_one_split_is_present():
    assert HAVE, "run scripts/fetch_data.py"


def test_unknown_split_is_rejected():
    with pytest.raises(ValueError):
        corpus.load("dev")


def test_available_skips_an_unreadable_split(tmp_path, monkeypatch):
    """A half-written file must not count as a corpus."""
    monkeypatch.setattr(corpus, "DATA", tmp_path)
    (tmp_path / "test.parquet").write_bytes(b"not a parquet at all")
    assert "test" not in corpus.available()


@pytest.mark.parametrize("split", HAVE[:1])
def test_articles_have_text(split):
    articles = corpus.load(split)
    assert all(a.text.strip() for a in articles)
    assert all(a.summary.strip() for a in articles)


@pytest.mark.parametrize("split", HAVE[:1])
def test_the_corpus_really_is_urdu(split):
    """Guards against silently loading a different language config."""
    articles = corpus.load(split)[:200]
    urdu_chars = sum(
        1 for a in articles for ch in a.text[:500] if "؀" <= ch <= "ۿ"
    )
    total = sum(len(a.text[:500]) for a in articles)
    assert urdu_chars / total > 0.5


@pytest.mark.parametrize("split", HAVE[:1])
def test_some_articles_use_arabic_letters(split):
    """The premise of the repository. If this ever hits zero, either the
    corpus was cleaned upstream or the detector broke."""
    articles = corpus.load(split)
    affected = sum(1 for a in articles if script.has_arabic_variants(a.everything))
    assert 0 < affected / len(articles) < 0.5


@pytest.mark.parametrize("split", HAVE[:1])
def test_normalising_never_grows_the_vocabulary(split):
    """Merging can only ever reduce the number of distinct types."""
    articles = corpus.load(split)[:2000]
    raw = {w for a in articles for w in script.words(a.everything)}
    merged = {script.normalise(w) for w in raw}
    assert len(merged) <= len(raw)
