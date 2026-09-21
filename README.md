# urdu-desk

> **9.2% of BBC Urdu articles are typed with Arabic letters standing in for Urdu ones.** They render identically, Unicode's NFC will not merge them, and every exact-match comparison in a pipeline treats them as different words.

**Status:** complete as a measurement, over the whole corpus. No model, no training — the
claim is about what real Urdu text contains and it is settled by counting characters.

## The problem

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
articles**, all three splits, 224.7M characters, 48.2M word tokens. Nothing has been
cleaned, which is the point: a tidied corpus would answer a different question.

```
python scripts/fetch_data.py   # ~190 MB of parquet, not in git
python scripts/measure.py      # every table below
python -m pytest               # 30 tests
```

Measured over all three splits together. This is a description of what the text contains,
not a model fitted to one half and scored on the other, so there is no split to respect.

## How much is affected

**7,769 of 84,581 articles — 9.2%** contain at least one substitutable Arabic letter.

| Char | Codepoint | Name | Occurrences |
|---|---|---|---:|
| ي | U+064A | ARABIC LETTER YEH | **22,038** |
| ك | U+0643 | ARABIC LETTER KAF | 4,365 |
| ه | U+0647 | ARABIC LETTER HEH | 1,025 |
| ى | U+0649 | ALEF MAKSURA | 41 |
| أ | U+0623 | ALEF WITH HAMZA ABOVE | 25 |
| ة | U+0629 | TEH MARBUTA | 23 |

## What normalising does to the vocabulary

| | |
|---|---:|
| Distinct word types, as written | 277,594 |
| Distinct word types, normalised | 259,399 |
| **Reduction** | **6.6%** |
| Normalised types with more than one spelling | 13,647 (5.3%) |

Two different problems are folded together here, and they are worth separating — stripping
diacritics merges words that were typed *correctly*, while substituting letters merges words
typed with the wrong alphabet:

| | Types | Reduction |
|---|---:|---:|
| Letter substitution alone | 277,594 → 272,616 | 1.8% |
| Diacritics and zero-width alone | 277,594 → 264,479 | 4.7% |
| Both | 277,594 → 259,399 | **6.6%** |

One word, many spellings:

```
وزیراعلی    26 spellings
اعلی        18
ان          15
تقریبا      15
دلی         15
```

## What it actually costs

This is the part worth being careful about, because the headline invites overstating it.

| | |
|---|---:|
| Tokens written in a **minority** spelling | 231,214 — **0.48%** of all tokens |

That is the honest figure: the share of tokens an exact match on the commonest form would
miss. Counting every token of every multi-spelling word instead gives **50.8%**, which is
almost entirely the *dominant* spelling of two or three very common function words — a
denominator doing all the work.

For search, over the 200 commonest words:

| | Documents missed |
|---|---:|
| Worst word | **15.1%** |
| Median word | 0.0% |
| Mean | 0.2% |

**The effect is concentrated, not pervasive.** The median common word loses nothing. One
word in the top 200 loses a sixth of its documents. A retriever built on exact match is
mostly fine and occasionally badly wrong, which is harder to notice than being uniformly
wrong.

## Two things that are not problems here

**Zero-width characters are rare.** 1.9% of articles contain one — mostly directional marks
(U+200F, U+200E) rather than joiners. They still split words, and `normalise` removes them.

**The digits are ASCII.** Urdu has ۰۱۲۳ and Arabic has ٠١٢٣, and this corpus uses neither:
**753,286 ASCII digits against 8 Urdu and 37 Arabic.** BBC Urdu writes numbers in ASCII.
`script.digits` reports the mix rather than normalising it, because folding them together is
easy and throws away what the text says about where it came from — but on this corpus there
is nothing to fold.

## Scope

**This is edited newswire, so treat every number as a floor.** BBC Urdu has sub-editors and
a house style. Forum posts, scraped web pages and user-generated Urdu will be worse, and the
same code will measure them — `script.py` takes any string.

## Layout

```
scripts/fetch_data.py       XL-Sum Urdu, byte-ranged, length-checked, atomic rename
src/urdudesk/script.py      the normalisation decisions, one mapping at a time
src/urdudesk/corpus.py      84,581 articles; available() rejects a half-downloaded split
scripts/measure.py          every table above
tests/                      30 tests, one per orthographic decision
```
