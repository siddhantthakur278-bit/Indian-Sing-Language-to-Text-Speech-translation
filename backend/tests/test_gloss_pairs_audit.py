"""Tests for reproducible glossary conflict reporting."""

import csv
from pathlib import Path

import pytest

from backend.gloss_pairs_audit import (
    REQUIRED_FIELDS,
    audit_gloss_pairs,
)


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def make_row(
    gloss_sequence: str,
    english_sentence: str,
    hindi_translation: str = "अनुवाद",
    marathi_translation: str = "भाषांतर",
    is_emergency: str = "false",
) -> dict[str, str]:
    return {
        "gloss_sequence": gloss_sequence,
        "english_sentence": english_sentence,
        "hindi_translation": hindi_translation,
        "marathi_translation": marathi_translation,
        "is_emergency": is_emergency,
    }


def test_report_identifies_translation_and_emergency_label_conflicts(tmp_path):
    csv_path = tmp_path / "pairs.csv"
    write_rows(
        csv_path,
        [
            make_row("HELP CALL", "Please call for help.", is_emergency="true"),
            make_row(
                "HELP CALL",
                "Call for help.",
                hindi_translation="मदद के लिए बुलाएं",
                is_emergency="false",
            ),
        ],
    )

    report = audit_gloss_pairs(csv_path)

    assert "- CSV rows: 2" in report
    assert "- Repeated gloss sequences: 1" in report
    assert "- Conflicting translation fields: 2" in report
    assert "- Conflicting emergency labels: 1" in report
    assert "### `HELP CALL` — `english_sentence`" in report
    assert "### `HELP CALL` — `hindi_translation`" in report
    assert "### `HELP CALL`" in report
    assert "| 2 | true | Please call for help. |" in report
    assert "| 3 | false | Call for help. |" in report


def test_report_is_reproducible(tmp_path):
    csv_path = tmp_path / "pairs.csv"
    write_rows(csv_path, [make_row("HELLO", "Hello!")])

    assert audit_gloss_pairs(csv_path) == audit_gloss_pairs(csv_path)


def test_audit_rejects_malformed_csv_row(tmp_path):
    csv_path = tmp_path / "pairs.csv"
    csv_path.write_text(
        "gloss_sequence,english_sentence,hindi_translation,"
        "marathi_translation,is_emergency\n"
        "HELLO,Hello!,नमस्ते,नमस्कार\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Malformed CSV row at line 2"):
        audit_gloss_pairs(csv_path)


def test_audit_rejects_unexpected_header(tmp_path):
    csv_path = tmp_path / "pairs.csv"
    csv_path.write_text("gloss,translation\nHELLO,Hello!\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected CSV fields"):
        audit_gloss_pairs(csv_path)
