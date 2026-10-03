"""Run the normaliser on your own text.

    urdu-desk check article.txt other.txt     # what is wrong with these files
    urdu-desk check --json < scraped.txt      # same, for a script
    urdu-desk normalise in.txt -o out.txt     # rewrite with Urdu letters
    urdu-desk words "اس، وہ۔"                 # how the text tokenises

Files are read as UTF-8 (a BOM is accepted). `-` or no file means stdin.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from urdudesk import script


def _utf8_stdout() -> None:
    # A Windows console defaults to cp1252, which cannot print a single Urdu
    # letter; without this every command dies on its first line of output.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def _read(source: str) -> str:
    if source == "-":
        data = sys.stdin.buffer.read()
        name = "<stdin>"
    else:
        path = Path(source)
        if not path.is_file():
            raise SystemExit(f"urdu-desk: no such file: {source}")
        data = path.read_bytes()
        name = source
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SystemExit(
            f"urdu-desk: {name} is not UTF-8 (byte {exc.start}); re-save it as UTF-8"
        ) from None


def report(text: str) -> dict:
    """Everything `check` says about one text, as plain data."""
    raw = script.words(text)
    normalised = script.words(script.normalise(text))
    return {
        "characters": len(text),
        "words": len(raw),
        "has_arabic_variants": script.has_arabic_variants(text),
        "arabic_variants": {
            f"U+{ord(ch):04X}": {"char": ch, "count": n, "urdu": f"U+{ord(script.LETTERS[ch]):04X}"}
            for ch, n in script.variant_counts(text).items()
        },
        "invisible": {f"U+{ord(ch):04X}": n for ch, n in script.invisible_counts(text).items()},
        "digits": script.digits(text),
        "distinct_words": len(set(raw)),
        "distinct_words_normalised": len(set(normalised)),
    }


def _print_report(name: str, r: dict) -> None:
    print(f"{name}: {r['words']:,} words, {r['characters']:,} characters")
    if r["arabic_variants"]:
        print("  Arabic letters standing in for Urdu ones:")
        for code, v in r["arabic_variants"].items():
            print(f"    {v['char']}  {code} x{v['count']:,}  -> {v['urdu']}")
    else:
        print("  no Arabic look-alike letters")
    if r["invisible"]:
        shown = ", ".join(f"{c} x{n:,}" for c, n in r["invisible"].items())
        print(f"  zero-width characters: {shown}")
    d = r["digits"]
    if any(d.values()):
        print(f"  digits: urdu {d['urdu']:,}, arabic {d['arabic']:,}, ascii {d['ascii']:,}")
    print(
        f"  distinct words {r['distinct_words']:,} -> {r['distinct_words_normalised']:,}"
        " after normalising"
    )


def main(argv: list[str] | None = None) -> int:
    _utf8_stdout()
    parser = argparse.ArgumentParser(
        prog="urdu-desk", description="Find and fix Arabic letters typed in Urdu text."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="report Arabic look-alikes, zero-width chars, digits")
    check.add_argument("files", nargs="*", default=["-"], help="UTF-8 files; '-' is stdin")
    check.add_argument("--json", action="store_true", help="machine-readable output")

    norm = sub.add_parser("normalise", aliases=["normalize"], help="rewrite text in Urdu letters")
    norm.add_argument("file", nargs="?", default="-")
    norm.add_argument("-o", "--output", help="write here instead of stdout")
    norm.add_argument(
        "--only",
        choices=("letters", "marks"),
        help="only substitute letters, or only strip diacritics/zero-width",
    )

    words = sub.add_parser("words", help="tokenise text the way the measurements do")
    words.add_argument("text", nargs="?", help="text to tokenise (default: stdin)")
    words.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "check":
        reports = {name: report(_read(name)) for name in args.files}
        if args.json:
            out = reports if len(reports) > 1 else next(iter(reports.values()))
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            for name, r in reports.items():
                _print_report("<stdin>" if name == "-" else name, r)
        return 1 if any(r["has_arabic_variants"] for r in reports.values()) else 0

    if args.command in ("normalise", "normalize"):
        fn = {
            None: script.normalise,
            "letters": script.normalise_letters,
            "marks": script.normalise_marks,
        }[args.only]
        result = fn(_read(args.file))
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8", newline="")
        else:
            sys.stdout.write(result)
        return 0

    text = args.text if args.text is not None else _read("-")
    tokens = script.words(text)
    print(json.dumps(tokens, ensure_ascii=False) if args.json else "\n".join(tokens))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
