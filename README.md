# urdu-desk

> **9.2% of BBC Urdu articles are typed with Arabic letters standing in for Urdu ones.** They render identically, Unicode's NFC will not merge them, and every exact-match comparison in a pipeline treats them as different words.

**Status:** complete as a measurement, over the whole corpus. No model, no training — the
claim is about what real Urdu text contains and it is settled by counting characters.

## What it does

Urdu is written in the Arabic script with its own letters. A great deal of Urdu text is
typed with the Arabic ones instead, because that is what the keyboard or the CMS produced.
The pairs look the same in almost any font:

| Urdu | | Arabic | | |
|---|---|---|---|---|
| ی | U+06CC FARSI YEH | ي | U+064A ARABIC YEH | |
| ک | U+06A9 KEHEH | ك | U+0643 ARABIC KAF | |
| ہ | U+06C1 HEH GOAL | ه | U+0647 ARABIC HEH | |

`unicodedata.normalize("NFC", …)` does **not** merge these, and is right not to: they are
distinct letters, not compatibility variants. Merging them is a decision about Urdu, which
is why it has to be written down rather than imported — it lives in
[`src/urdudesk/script.py`](src/urdudesk/script.py) and
[`test_unicode_nfc_does_not_do_this_for_you`](tests/test_script.py) pins the distinction.

## The corpus

[XL-Sum](https://huggingface.co/datasets/csebuetnlp/xlsum) Urdu — **84,581 BBC Urdu news
articles**, all three splits, 224.7M characters, about 48M word tokens. Nothing has been
cleaned, which is the point: a tidied corpus would answer a different question.

```
pip install -e .[dev]
python demo.py                 # four sentences, no corpus needed
python -m pytest               # 44 tests; 5 skip until the corpus is fetched
python scripts/fetch_data.py   # ~190 MB of parquet, not in git; resumes if interrupted
python scripts/measure.py      # every table below
```

The corpus lives in `data/`; set `URDUDESK_DATA` to keep it elsewhere.

## On your own text

```
urdu-desk check scraped.txt            # Arabic look-alikes, zero-width chars, digit systems
urdu-desk check --json a.txt b.txt     # same, as JSON; exit 1 if any look-alikes found
urdu-desk normalise in.txt -o out.txt  # rewrite with Urdu letters (--only letters|marks)
urdu-desk words "اس، وہ۔"              # tokenise the way the measurements do
```

`python -m urdudesk` is the same command. Files are read as UTF-8; `-` or no file is stdin.

From Python: `from urdudesk import script; script.normalise(text)`.

Measured over all three splits together. This is a description of what the text contains,
not a model fitted to one half and scored on the other, so there is no split to respect.

## How much is affected

Over all three splits (character counts, unaffected by tokenisation; validation + test
alone give 9.7%): **7,769 of 84,581 articles — 9.2%** contain at least one substitutable Arabic letter.

| Char | Codepoint | Name | Occurrences |
|---|---|---|---:|
| ي | U+064A | ARABIC LETTER YEH | **22,038** |
| ك | U+0643 | ARABIC LETTER KAF | 4,365 |
| ه | U+0647 | ARABIC LETTER HEH | 1,025 |
| ى | U+0649 | ALEF MAKSURA | 41 |
| أ | U+0623 | ALEF WITH HAMZA ABOVE | 25 |
| ة | U+0629 | TEH MARBUTA | 23 |

## What normalising does to the vocabulary

The tables in this section and the next are measured on the **validation and test splits
(16,916 articles, 8.7M word tokens)**, with the tokeniser that treats ، ۔ ؟ ؛ and digits as
separators. An earlier version of this README gave full-corpus figures from a tokeniser that
glued Urdu punctuation onto the preceding word (`اس،` counted as its own type); that inflated
the vocabulary by about 16% and those numbers are withdrawn. The full-corpus rerun needs the
156 MB train split; `scripts/measure.py` uses every split on disk and says which.

| | |
|---|---:|
| Distinct word types, as written | 86,033 |
| Distinct word types, normalised | 80,775 |
| **Reduction** | **6.1%** |
| Normalised types with more than one spelling | 4,237 (5.2%) |

Two different problems are folded together here, and they are worth separating — stripping
diacritics merges words that were typed *correctly*, while substituting letters merges words
typed with the wrong alphabet:

| | Types | Reduction |
|---|---:|---:|
| Letter substitution alone | 86,033 → 84,616 | 1.6% |
| Diacritics and zero-width alone | 86,033 → 82,253 | 4.4% |
| Both | 86,033 → 80,775 | **6.1%** |

One word, many spellings:

```
وزیراعلی    15 spellings
اعلی        13
ان          12
اس          11
سنی         10
```

## What it actually costs

This is the part worth being careful about, because the headline invites overstating it.

| | |
|---|---:|
| Tokens written in a **minority** spelling | 41,568 — **0.48%** of all tokens |

That is the honest figure: the share of tokens an exact match on the commonest form would
miss. Counting every token of every multi-spelling word instead gives a figure near half,
which is almost entirely the *dominant* spelling of two or three very common function
words — a denominator doing all the work.

For search, over the 200 commonest words:

| | Documents missed |
|---|---:|
| Worst word | **15.9%** |
| Median word | 0.0% |
| Mean | 0.2% |

**The effect is concentrated, not pervasive.** The median common word loses nothing. One
word in the top 200 loses a sixth of its documents. A retriever built on exact match is
mostly fine and occasionally badly wrong, which is harder to notice than being uniformly
wrong.

## Scope

**This is edited newswire, so treat every number as a floor.** BBC Urdu has sub-editors and
a house style. Forum posts, scraped web pages and user-generated Urdu will be worse, and the
same code will measure them — `script.py` takes any string.

## Layout

```
scripts/fetch_data.py       XL-Sum Urdu, byte-ranged, length-checked, atomic rename
src/urdudesk/script.py      the normalisation decisions, one mapping at a time
src/urdudesk/corpus.py      84,581 articles; available() rejects a half-downloaded split
src/urdudesk/cli.py         urdu-desk check / normalise / words
demo.py                     the normaliser on four sentences
scripts/measure.py          every table above
tests/                      44 tests; the 5 that need the corpus skip without it
```
