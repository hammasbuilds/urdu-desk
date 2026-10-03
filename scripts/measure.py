"""Every number in the README.

    python scripts/measure.py

No model, no training. The claim is about what real Urdu text contains, and it
is settled by counting characters.
"""

from __future__ import annotations

import collections
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from urdudesk import corpus, script  # noqa: E402
from urdudesk.cli import _utf8_stdout  # noqa: E402


def rule(title: str) -> None:
    print("\n" + "=" * 76)
    print(title)
    print("=" * 76)


def name(ch: str) -> str:
    try:
        return unicodedata.name(ch)
    except ValueError:
        return "?"


def the_corpus(articles) -> None:
    rule("the corpus")
    chars = sum(len(a.everything) for a in articles)
    print(f"articles        {len(articles):>9,}")
    print(f"characters      {chars:>9,}")
    print(f"word tokens     {sum(len(script.words(a.everything)) for a in articles):>9,}")


def the_prevalence(articles) -> None:
    rule("how much real Urdu is typed with Arabic letters")
    affected = 0
    per_char: collections.Counter = collections.Counter()
    for article in articles:
        counts = script.variant_counts(article.everything)
        if counts:
            affected += 1
            per_char.update(counts)

    print("articles containing at least one substitutable Arabic letter:")
    print(f"  {affected:,} of {len(articles):,}   {affected / len(articles):.1%}\n")
    print(f"{'char':<6}{'codepoint':<12}{'name':<34}{'occurrences':>13}")
    for ch, count in per_char.most_common():
        print(f"{ch:<6}U+{ord(ch):04X}      {name(ch)[:32]:<34}{count:>13,}")

    print("\n  ^ these are not typos. They render identically in most fonts, so")
    print("    nothing looks wrong, and they are different codepoints — so every")
    print("    exact-match comparison in a pipeline treats them as different words.")


def the_vocabulary(articles) -> None:
    rule("what normalising does to the vocabulary")
    raw: collections.Counter = collections.Counter()
    normalised: collections.Counter = collections.Counter()
    merged: dict[str, set[str]] = collections.defaultdict(set)

    for article in articles:
        text = article.everything
        for word in script.words(text):
            raw[word] += 1
        for word in script.words(script.normalise(text)):
            normalised[word] += 1
        for word in script.words(text):
            merged[script.normalise(word)].add(word)

    collapsed = sum(1 for forms in merged.values() if len(forms) > 1)
    print(f"distinct word types, as written      {len(raw):>9,}")
    print(f"distinct word types, normalised      {len(normalised):>9,}")
    print(f"  reduction                          {1 - len(normalised) / len(raw):>9.1%}")
    print(f"\nnormalised types with >1 spelling    {collapsed:>9,}"
          f"   ({collapsed / len(normalised):.1%} of the vocabulary)")

    # Tokens written in a spelling that is NOT the commonest one for that word.
    # Counting every token of every multi-spelling word instead gives 50.8%,
    # which is almost entirely the dominant spelling of two or three very
    # common function words — a denominator doing all the work.
    minority_tokens = 0
    for forms in merged.values():
        if len(forms) < 2:
            continue
        counts = sorted((raw[f] for f in forms), reverse=True)
        minority_tokens += sum(counts[1:])
    total_tokens = sum(raw.values())
    print(f"\ntokens written in a minority spelling {minority_tokens:>9,}"
          f"   ({minority_tokens / total_tokens:.2%} of all tokens)")
    print("  (i.e. would be missed by an exact match on the commonest form)")

    print("\n  worst offenders — one word, several spellings:")
    worst = sorted(merged.items(), key=lambda kv: -len(kv[1]))[:5]
    for base, forms in worst:
        shown = ", ".join(sorted(forms)[:4])
        print(f"    {base:<18} {len(forms)} spellings: {shown}")

    # The two effects are different problems and deserve separating. Stripping
    # diacritics merges words that were typed correctly; substituting letters
    # merges words that were typed with the wrong alphabet.
    letters_only = {script.normalise_letters(w) for w in raw}
    marks_only = {script.normalise_marks(w) for w in raw}
    print("\n  where the reduction comes from:")
    print(f"    letter substitution alone   {len(raw):,} -> {len(letters_only):,}"
          f"   ({1 - len(letters_only) / len(raw):.1%})")
    print(f"    diacritics alone            {len(raw):,} -> {len(marks_only):,}"
          f"   ({1 - len(marks_only) / len(raw):.1%})")
    print(f"    both                        {len(raw):,} -> {len(normalised):,}"
          f"   ({1 - len(normalised) / len(raw):.1%})")


def the_retrieval_cost(articles) -> None:
    rule("what it costs to search")
    index_raw: dict[str, set[int]] = collections.defaultdict(set)
    index_norm: dict[str, set[int]] = collections.defaultdict(set)
    for n, article in enumerate(articles):
        text = article.everything
        for word in set(script.words(text)):
            index_raw[word].add(n)
        for word in set(script.words(script.normalise(text))):
            index_norm[word].add(n)

    common = [w for w, _ in collections.Counter(
        {w: len(d) for w, d in index_norm.items()}
    ).most_common(200)]

    missed = []
    for word in common:
        found = len(index_raw.get(word, ()))
        whole = len(index_norm[word])
        if whole:
            missed.append((whole - found) / whole)
    missed.sort(reverse=True)

    print("for the 200 commonest words, searching the raw text instead of the")
    print("normalised text misses, per word:")
    print(f"  worst   {missed[0]:.1%}")
    print(f"  median  {missed[len(missed) // 2]:.1%}")
    print(f"  mean    {sum(missed) / len(missed):.1%}")
    print("\n  ^ a reader who types the Urdu spelling into a search box does not")
    print("    find the articles typed with the Arabic one, and neither does a")
    print("    retriever built on exact match or on a vocabulary that never saw")
    print("    them merged.")


def the_invisibles(articles) -> None:
    rule("characters that are not there")
    per_char: collections.Counter = collections.Counter()
    affected = 0
    for article in articles:
        counts = script.invisible_counts(article.everything)
        if counts:
            affected += 1
            per_char.update(counts)

    print(f"articles containing a zero-width character: {affected:,}"
          f"   ({affected / len(articles):.1%})")
    for ch, count in per_char.most_common():
        print(f"  U+{ord(ch):04X}  {name(ch)[:40]:<42}{count:>10,}")
    if not per_char:
        print("  none — this corpus is cleaner than most Urdu on the web")


def the_digits(articles) -> None:
    rule("three numbering systems")
    total = collections.Counter()
    for article in articles:
        for system, count in script.digits(article.everything).items():
            total[system] += count
    everything = sum(total.values()) or 1
    for system in ("urdu", "arabic", "ascii"):
        print(f"  {system:<8}{total[system]:>10,}   {total[system] / everything:>6.1%}")
    print("\n  ^ reported, not normalised. Folding ۱۲۳ and ١٢٣ into 123 is easy and")
    print("    throws away what the text says about where it came from.")


def main() -> None:
    _utf8_stdout()
    have = corpus.available()
    if not have:
        print("no corpus — run scripts/fetch_data.py")
        raise SystemExit(1)

    # Every split together. This is a description of what Urdu text contains,
    # not a model being fitted to one half and scored on the other, so there is
    # no split to respect — and using all of it means the counts are over the
    # whole corpus rather than a quarter of it.
    articles = tuple(a for split in have for a in corpus.load(split))
    print(f"measuring on {', '.join(have)} — {len(articles):,} articles")
    if "train" not in have:
        print("  (train is not downloaded; run scripts/fetch_data.py for the full corpus)")

    the_corpus(articles)
    the_prevalence(articles)
    the_vocabulary(articles)
    the_retrieval_cost(articles)
    the_invisibles(articles)
    the_digits(articles)
    print()


if __name__ == "__main__":
    main()
