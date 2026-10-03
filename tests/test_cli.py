"""The command line, run in-process on temp files."""

from __future__ import annotations

import json

import pytest

from urdudesk import cli

ARABIC = "پاكستاني خبر"  # Arabic KAF and YEH
URDU = "پاکستانی خبر"


def test_check_json_reports_the_variants(tmp_path, capsys):
    f = tmp_path / "a.txt"
    f.write_text(ARABIC, encoding="utf-8")
    assert cli.main(["check", "--json", str(f)]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["has_arabic_variants"] is True
    assert out["arabic_variants"]["U+0643"]["count"] == 1
    assert out["arabic_variants"]["U+064A"]["urdu"] == "U+06CC"
    assert out["distinct_words_normalised"] == 2


def test_check_clean_file_exits_zero(tmp_path, capsys):
    f = tmp_path / "b.txt"
    f.write_text("\ufeff" + URDU, encoding="utf-8")  # BOM accepted
    assert cli.main(["check", str(f)]) == 0
    assert "no Arabic look-alike letters" in capsys.readouterr().out


def test_normalise_writes_output(tmp_path):
    src, dst = tmp_path / "in.txt", tmp_path / "out.txt"
    src.write_text(ARABIC + "\n", encoding="utf-8")
    assert cli.main(["normalise", str(src), "-o", str(dst)]) == 0
    assert dst.read_text(encoding="utf-8") == URDU + "\n"


def test_words_json(capsys):
    assert cli.main(["words", "--json", "اس، وہ۔"]) == 0
    assert json.loads(capsys.readouterr().out) == ["اس", "وہ"]


def test_missing_file_is_a_message_not_a_traceback(tmp_path):
    with pytest.raises(SystemExit, match="no such file"):
        cli.main(["check", str(tmp_path / "nope.txt")])


def test_non_utf8_file_is_explained(tmp_path):
    f = tmp_path / "c.txt"
    f.write_bytes("خبر".encode("cp1256"))
    with pytest.raises(SystemExit, match="not UTF-8"):
        cli.main(["check", str(f)])
