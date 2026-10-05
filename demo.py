"""What the normaliser does, on four sentences. Needs no corpus.

python demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from urdudesk import script  # noqa: E402
from urdudesk.cli import _utf8_stdout  # noqa: E402

SAMPLES = [
    # Typed with Arabic YEH and KAF: renders as Urdu, compares as something else.
    "پاكستاني وزيراعظم نے آج اجلاس طلب كيا۔",
    # The same sentence typed with Urdu letters.
    "پاکستانی وزیراعظم نے آج اجلاس طلب کیا۔",
    # Diacritics and a zero-width non-joiner left behind by a word processor.
    "کِتاب‌خانہ میں ۱۲ نئی کتابیں آئیں۔",
    # Arabic HEH and TEH MARBUTA, Arabic-Indic digits.
    "يه خبر ١٢ بجے شائع هوئي، صفحة اول پر۔",
]


def main() -> None:
    _utf8_stdout()
    for n, text in enumerate(SAMPLES, 1):
        fixed = script.normalise(text)
        print(f"[{n}] input      {text}")
        print(f"    normalised {fixed}")
        variants = {f"U+{ord(c):04X}": k for c, k in script.variant_counts(text).items()}
        print(f"    arabic look-alikes {variants or 'none'}")
        zero_width = sum(script.invisible_counts(text).values())
        print(f"    zero-width {zero_width}, digits {script.digits(text)}")
        print(f"    words      {script.words(text)}")
        print()
    a, b = SAMPLES[0], SAMPLES[1]
    print(f"[1] == [2] as typed:      {a == b}")
    print(f"[1] == [2] after normalise: {script.normalise(a) == script.normalise(b)}")


if __name__ == "__main__":
    main()
