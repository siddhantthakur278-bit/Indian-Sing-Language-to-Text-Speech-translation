"""Quality checks for the committed gloss translation pairs."""

import csv
import unicodedata
from pathlib import Path

from backend.vocabulary import VOCABULARY

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GLOSS_PAIRS_PATH = PROJECT_ROOT / "data" / "gloss_pairs.csv"
EXPECTED_COLUMNS = (
    "gloss_sequence",
    "english_sentence",
    "hindi_translation",
    "marathi_translation",
    "is_emergency",
)


def load_rows() -> list[dict[str, str]]:
    """Load the committed CSV with its required UTF-8 encoding."""
    with GLOSS_PAIRS_PATH.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        assert tuple(reader.fieldnames or ()) == EXPECTED_COLUMNS
        return list(reader)


def test_gloss_pairs_are_nonempty_and_use_the_expected_schema():
    rows = load_rows()

    assert len(rows) == 149
    for row in rows:
        assert all(value.strip() for value in row.values())


def test_gloss_pairs_have_no_identical_duplicate_records():
    rows = load_rows()

    records = {
        tuple(row[column] for column in EXPECTED_COLUMNS)
        for row in rows
    }
    assert len(records) == len(rows)


def test_every_gloss_pair_uses_only_official_vocabulary():
    for row in load_rows():
        glosses = row["gloss_sequence"].split()

        assert glosses
        assert set(glosses) <= VOCABULARY
        assert "IDLE" not in glosses


def test_hindi_and_marathi_fields_are_populated_indic_text():
    rows = load_rows()

    for row in rows:
        assert row["hindi_translation"].strip() != row["english_sentence"].strip()
        assert row["marathi_translation"].strip() != row["english_sentence"].strip()
        assert any(
            "DEVANAGARI" in unicodedata.name(character, "")
            for character in row["hindi_translation"]
        )
        assert any(
            "DEVANAGARI" in unicodedata.name(character, "")
            for character in row["marathi_translation"]
        )


def test_emergency_labels_have_explicit_boolean_values():
    assert {
        row["is_emergency"].strip().lower() for row in load_rows()
    } == {"true", "false"}


def test_conflicting_emergency_sequence_label_is_reported_for_domain_review():
    labels_by_sequence: dict[tuple[str, ...], set[str]] = {}
    for row in load_rows():
        sequence = tuple(row["gloss_sequence"].split())
        labels_by_sequence.setdefault(sequence, set()).add(
            row["is_emergency"].strip().lower()
        )

    conflicts = {
        sequence
        for sequence, labels in labels_by_sequence.items()
        if len(labels) > 1
    }
    assert conflicts == {("DOCTOR", "CALL", "PLEASE")}


def test_dataset_coverage_gap_is_explicit():
    covered = {
        gloss
        for row in load_rows()
        for gloss in row["gloss_sequence"].split()
    }

    assert VOCABULARY - covered == {"HEAR", "IDLE", "SEE"}
