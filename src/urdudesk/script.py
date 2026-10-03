"""Urdu is written in characters that look alike and are not alike.

Urdu uses the Arabic script with its own letters, and a great deal of Urdu text
on the internet is typed with the Arabic ones instead. The pairs render nearly
identically in most fonts, so nothing looks wrong, and they are different
codepoints — so string equality, a vocabulary, a hash index and a BPE tokeniser
all treat them as different words.

    ی  U+06CC  FARSI YEH          vs  ي  U+064A  ARABIC LETTER YEH
    ک  U+06A9  KEHEH              vs  ك  U+0643  ARABIC LETTER KAF
    ہ  U+06C1  HEH GOAL           vs  ه  U+0647  ARABIC LETTER HEH
    ۂ  U+06C2  HEH GOAL + HAMZA   vs  ۀ  U+06C0  HEH WITH YEH ABOVE

Unicode's own NFC does not merge these: they are distinct letters, not
compatibility variants, and NFC is right not to touch them. Merging them is a
*language* decision, which is why it has to be written down rather than
imported.

This module holds that decision and nothing else. `normalise` maps each
variant to the Urdu form, strips the zero-width joiners that word processors
leave behind, and drops the diacritics that Urdu writes optionally — the same
word appears with and without them and means the same thing.

What it deliberately does NOT do is touch the Arabic-Indic digits. Urdu uses
۰۱۲۳ and Arabic uses ٠١٢٣; folding either into ASCII would be convenient and
would change what the text says about itself, so `digits` reports on them
instead.
"""

from __future__ import annotations

import re
import unicodedata

# The letter substitutions. Each maps an Arabic-script character to the Urdu
# one it is standing in for.
LETTERS = {
    "ي": "ی",  # ARABIC YEH        -> FARSI YEH
    "ى": "ی",  # ALEF MAKSURA      -> FARSI YEH
    "ك": "ک",  # ARABIC KAF        -> KEHEH
    "ه": "ہ",  # ARABIC HEH        -> HEH GOAL
    "ۀ": "ۂ",  # HEH + YEH ABOVE   -> HEH GOAL + HAMZA
    "ة": "ہ",  # TEH MARBUTA       -> HEH GOAL
    "أ": "ا",  # ALEF WITH HAMZA   -> ALEF
    "إ": "ا",  # ALEF WITH HAMZA BELOW -> ALEF
}

# Zero-width characters. They carry shaping information in some scripts; in
# Urdu web text they are overwhelmingly editor residue, and they split words.
INVISIBLE = "​‌‍‎‏﻿"

# Optional vowel marks. Urdu writes them in dictionaries, teaching material and
# poetry, and leaves them out everywhere else. The word is the same word.
DIACRITICS = "ًٌٍَُِّْٰٕٓٔ"

URDU_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"

_LETTER_TABLE = str.maketrans(LETTERS)
_STRIP_TABLE = str.maketrans("", "", INVISIBLE + DIACRITICS)

# Urdu word characters: the letters and combining marks of the Arabic-script
# blocks. Punctuation (، ؛ ؟ ۔), both digit sets and symbols live in the same
# blocks and are NOT word characters: "اس،" is the word "اس" and a comma.
_BLOCKS = ((0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF))
_WORD_CHARS = "".join(
    re.escape(chr(cp))
    for lo, hi in _BLOCKS
    for cp in range(lo, hi + 1)
    if unicodedata.category(chr(cp))[0] in "LM"
)
WORD = re.compile(f"[{_WORD_CHARS}]+")


def _need_str(text: object) -> None:
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")


def normalise(text: str) -> str:
    """One Urdu spelling for one Urdu word.

    NFC first, because some sources decompose the hamza carriers, and the
    letter table below expects composed forms.
    """
    _need_str(text)
    return unicodedata.normalize("NFC", text).translate(_LETTER_TABLE).translate(_STRIP_TABLE)


def normalise_letters(text: str) -> str:
    """Only the alphabet substitution. Kept separate because it and the
    diacritic stripping are different problems: this one merges words that
    were typed with the wrong alphabet, the other merges words that were typed
    correctly and fully."""
    _need_str(text)
    return unicodedata.normalize("NFC", text).translate(_LETTER_TABLE)


def normalise_marks(text: str) -> str:
    """Only the zero-width and diacritic stripping."""
    _need_str(text)
    return unicodedata.normalize("NFC", text).translate(_STRIP_TABLE)


def words(text: str) -> list[str]:
    _need_str(text)
    return WORD.findall(text)


def has_arabic_variants(text: str) -> bool:
    """Whether the text uses any Arabic letter that Urdu spells differently."""
    _need_str(text)
    return any(ch in text for ch in LETTERS)


def variant_counts(text: str) -> dict[str, int]:
    """How many of each substitutable character the text contains."""
    _need_str(text)
    return {ch: text.count(ch) for ch in LETTERS if ch in text}


def invisible_counts(text: str) -> dict[str, int]:
    _need_str(text)
    return {ch: text.count(ch) for ch in INVISIBLE if ch in text}


def digits(text: str) -> dict[str, int]:
    """Which of the three digit systems this text uses, and how much.

    Reported rather than normalised. A corpus that mixes ۱۲۳, ١٢٣ and 123 is
    telling you something about where it came from, and folding them together
    throws that away.
    """
    _need_str(text)
    return {
        "urdu": sum(text.count(d) for d in URDU_DIGITS),
        "arabic": sum(text.count(d) for d in ARABIC_DIGITS),
        "ascii": sum(ch.isdigit() and ch.isascii() for ch in text),
    }
