"""The normalisation decisions, each one asserted on its own.

Every entry in the table is a judgement about Urdu orthography rather than a
Unicode rule, so each gets a test that says which two characters it is merging
and why they are the same word.
"""

from __future__ import annotations

import unicodedata

import pytest

from urdudesk import script

# The pairs, written out so a reader can see what is being merged.
YEH_AR, YEH_UR = "ي", "ی"
KAF_AR, KEHEH_UR = "ك", "ک"
HEH_AR, HEH_GOAL_UR = "ه", "ہ"


def test_arabic_yeh_becomes_urdu_yeh():
    """Urdu writes ی; a great deal of Urdu text is typed with Arabic ي."""
    assert script.normalise(f"پاک{YEH_AR}") == f"پاک{YEH_UR}"


def test_arabic_kaf_becomes_keheh():
    assert script.normalise(f"{KAF_AR}تاب") == f"{KEHEH_UR}تاب"


def test_arabic_heh_becomes_heh_goal():
    assert script.normalise(f"{HEH_AR}ے") == f"{HEH_GOAL_UR}ے"


def test_the_two_spellings_become_equal():
    """The whole point: two strings that render alike now compare alike."""
    typed_arabic = f"پاکستان{KAF_AR}{YEH_AR}"
    typed_urdu = f"پاکستان{KEHEH_UR}{YEH_UR}"
    assert typed_arabic != typed_urdu
    assert script.normalise(typed_arabic) == script.normalise(typed_urdu)


def test_unicode_nfc_does_not_do_this_for_you():
    """NFC is right to leave them alone; merging them is a language decision.

    Worth pinning, because 'just run NFC' is the obvious thing to reach for and
    it does not solve this at all.
    """
    typed_arabic = f"{KAF_AR}{YEH_AR}"
    typed_urdu = f"{KEHEH_UR}{YEH_UR}"
    assert unicodedata.normalize("NFC", typed_arabic) != unicodedata.normalize(
        "NFC", typed_urdu
    )
    assert script.normalise(typed_arabic) == script.normalise(typed_urdu)


def test_normalise_is_idempotent():
    text = f"پاکستان{KAF_AR}{YEH_AR} ا{HEH_AR}م خبر"
    once = script.normalise(text)
    assert script.normalise(once) == once


def test_zero_width_characters_are_removed():
    """They are editor residue in Urdu web text and they split words."""
    assert script.normalise("پاک‌ستان") == "پاکستان"
    assert script.normalise("خبر‍") == "خبر"
    assert script.normalise("﻿خبر") == "خبر"


def test_optional_diacritics_are_removed():
    """Urdu writes vowel marks in dictionaries and poetry, not in news."""
    assert script.normalise("کِتاب") == script.normalise("کتاب")


def test_digits_are_reported_and_not_changed():
    """Folding ۱۲۳ into 123 is easy and discards where the text came from."""
    text = "۱۲۳ ١٢٣ 123"
    assert script.normalise(text) == text
    counted = script.digits(text)
    assert counted == {"urdu": 3, "arabic": 3, "ascii": 3}


def test_words_splits_on_non_urdu():
    assert script.words("خبر نامہ 2024") == ["خبر", "نامہ"]


def test_variant_counts_reports_only_substitutable_characters():
    counted = script.variant_counts(f"{YEH_AR}{YEH_AR}{KAF_AR}")
    assert counted == {YEH_AR: 2, KAF_AR: 1}
    assert script.variant_counts(f"{YEH_UR}{KEHEH_UR}") == {}


def test_has_arabic_variants():
    assert script.has_arabic_variants(f"پاک{YEH_AR}")
    assert not script.has_arabic_variants(f"پاک{YEH_UR}")


@pytest.mark.parametrize("ch", sorted(script.LETTERS))
def test_every_mapping_target_is_itself_stable(ch):
    """Normalising a mapping's output must not move it again."""
    target = script.LETTERS[ch]
    assert script.normalise(target) == target


def test_words_do_not_carry_urdu_punctuation():
    """، ۔ ؟ ؛ sit in the Arabic block; "اس،" is the word "اس" and a comma.

    Before this, the vocabulary counted every word once per punctuation mark
    that followed it."""
    assert script.words("اس، وہ۔ کیا؟ ہاں؛") == ["اس", "وہ", "کیا", "ہاں"]


def test_digits_are_not_words():
    assert script.words("۱۲۳ ١٢٣ خبر") == ["خبر"]


def test_words_keep_diacritics_inside_the_word():
    assert script.words("کِتاب") == ["کِتاب"]


@pytest.mark.parametrize(
    "fn",
    [script.normalise, script.normalise_letters, script.words, script.variant_counts,
     script.has_arabic_variants, script.digits],
)
def test_non_string_input_is_a_clear_error(fn):
    with pytest.raises(TypeError, match="expected str, got NoneType"):
        fn(None)


def test_empty_text():
    assert script.normalise("") == ""
    assert script.words("") == []
    assert not script.has_arabic_variants("")
