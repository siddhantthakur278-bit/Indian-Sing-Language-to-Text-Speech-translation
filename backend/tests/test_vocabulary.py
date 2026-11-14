"""Tests for official vocabulary loading, normalization, and validation."""

import json
from pathlib import Path

import pytest

from backend.vocabulary import (
    DEFAULT_VOCABULARY_PATH,
    VOCABULARY,
    VocabularyLoadError,
    VocabularyValidationError,
    load_vocabulary,
    normalize_gloss,
    validate_glosses,
)


def write_vocabulary_file(tmp_path: Path, data: object) -> Path:
    """Write JSON data to a temporary vocabulary file."""
    path = tmp_path / "classes.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_loads_official_vocabulary_file():
    assert load_vocabulary() == VOCABULARY


def test_official_vocabulary_contains_seventy_classes():
    assert len(load_vocabulary()) == 70


def test_official_vocabulary_includes_idle():
    assert "IDLE" in load_vocabulary()


def test_normalizes_lowercase_gloss():
    assert normalize_gloss("hello") == "HELLO"


def test_normalizes_surrounding_whitespace():
    assert normalize_gloss("  HOSPITAL  ") == "HOSPITAL"


def test_normalization_preserves_underscores():
    assert normalize_gloss("  thank_you ") == "THANK_YOU"


def test_validates_single_known_gloss():
    assert validate_glosses(["hello"]) == ["HELLO"]


def test_validates_multiple_known_glosses():
    assert validate_glosses(["me", "hospital", "go"]) == [
        "ME",
        "HOSPITAL",
        "GO",
    ]


def test_rejects_unknown_gloss():
    with pytest.raises(VocabularyValidationError) as error:
        validate_glosses(["NOT_A_SIGN"])

    assert error.value.unknown_glosses == ("NOT_A_SIGN",)


def test_reports_multiple_unknown_glosses_together():
    with pytest.raises(VocabularyValidationError) as error:
        validate_glosses(["UNKNOWN_ONE", "HELLO", "UNKNOWN_TWO"])

    assert error.value.unknown_glosses == ("UNKNOWN_ONE", "UNKNOWN_TWO")
    assert "UNKNOWN_ONE, UNKNOWN_TWO" in str(error.value)


def test_rejects_idle_for_sentence_generation():
    with pytest.raises(VocabularyValidationError, match="IDLE cannot"):
        validate_glosses(["IDLE"])


def test_missing_vocabulary_file_raises_clear_error(tmp_path):
    with pytest.raises(VocabularyLoadError, match="does not exist"):
        load_vocabulary(tmp_path / "missing.json")


def test_malformed_json_raises_clear_error(tmp_path):
    path = tmp_path / "classes.json"
    path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(VocabularyLoadError, match="valid UTF-8 JSON"):
        load_vocabulary(path)


@pytest.mark.parametrize(
    "data",
    [
        [],
        {},
        {"classes": "HELLO"},
        {"classes": []},
    ],
)
def test_invalid_vocabulary_structure_raises_error(tmp_path, data):
    with pytest.raises(VocabularyLoadError):
        load_vocabulary(write_vocabulary_file(tmp_path, data))


def test_duplicate_class_names_raise_error(tmp_path):
    path = write_vocabulary_file(
        tmp_path,
        {"classes": ["HELLO", "HELLO"]},
    )

    with pytest.raises(VocabularyLoadError, match="Duplicate class names"):
        load_vocabulary(path)


@pytest.mark.parametrize("invalid_entry", ["", " ", "hello", "HELLO-WORLD", 1, None])
def test_invalid_class_entries_raise_error(tmp_path, invalid_entry):
    path = write_vocabulary_file(
        tmp_path,
        {"classes": ["HELLO", invalid_entry]},
    )

    with pytest.raises(VocabularyLoadError, match="Invalid class entry"):
        load_vocabulary(path)


@pytest.mark.parametrize(
    "total_classes",
    [None, "2", 3],
)
def test_incorrect_total_classes_metadata_raises_error(tmp_path, total_classes):
    path = write_vocabulary_file(
        tmp_path,
        {"classes": ["HELLO", "GOODBYE"], "total_classes": total_classes},
    )

    with pytest.raises(VocabularyLoadError, match="total_classes"):
        load_vocabulary(path)


def test_default_vocabulary_path_points_to_official_classes_file():
    assert DEFAULT_VOCABULARY_PATH.is_file()
