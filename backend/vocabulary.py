"""Load and validate glosses against the repository's official vocabulary."""

import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VOCABULARY_PATH = PROJECT_ROOT / "data" / "classes.json"
_CLASS_NAME_PATTERN = re.compile(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*\Z")


class VocabularyLoadError(ValueError):
    """Raised when the official vocabulary file is missing or invalid."""


class VocabularyValidationError(ValueError):
    """Raised when glosses contain unknown entries or the non-sentence IDLE class."""

    def __init__(
        self,
        message: str,
        *,
        unknown_glosses: tuple[str, ...] = (),
        idle_glosses: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.unknown_glosses = unknown_glosses
        self.idle_glosses = idle_glosses


def load_vocabulary(path: str | Path = DEFAULT_VOCABULARY_PATH) -> frozenset[str]:
    """Load, validate, and return the official gloss names as an immutable set."""
    vocabulary_path = Path(path)
    if not vocabulary_path.is_file():
        raise VocabularyLoadError(
            f"Vocabulary file does not exist: {vocabulary_path}"
        )

    try:
        with vocabulary_path.open("r", encoding="utf-8") as vocabulary_file:
            data: Any = json.load(vocabulary_file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VocabularyLoadError(
            f"Could not read valid UTF-8 JSON from vocabulary file "
            f"{vocabulary_path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise VocabularyLoadError(
            f"Vocabulary file {vocabulary_path} must contain a JSON object."
        )

    classes = data.get("classes")
    if not isinstance(classes, list):
        raise VocabularyLoadError(
            f"Vocabulary file {vocabulary_path} must contain a 'classes' array."
        )
    if not classes:
        raise VocabularyLoadError(
            f"Vocabulary file {vocabulary_path} contains no classes."
        )

    for index, name in enumerate(classes):
        if not isinstance(name, str) or not _CLASS_NAME_PATTERN.fullmatch(name):
            raise VocabularyLoadError(
                f"Invalid class entry at index {index} in {vocabulary_path}: "
                f"{name!r}. Expected an uppercase gloss name with optional "
                "underscore-separated parts."
            )

    if len(set(classes)) != len(classes):
        seen: set[str] = set()
        duplicates: list[str] = []
        for name in classes:
            if name in seen and name not in duplicates:
                duplicates.append(name)
            seen.add(name)
        raise VocabularyLoadError(
            f"Duplicate class names in {vocabulary_path}: "
            f"{', '.join(duplicates)}."
        )

    if "total_classes" in data:
        total_classes = data["total_classes"]
        if type(total_classes) is not int or total_classes != len(classes):
            raise VocabularyLoadError(
                f"'total_classes' in {vocabulary_path} must equal the number "
                f"of class entries ({len(classes)}); got {total_classes!r}."
            )

    return frozenset(classes)


VOCABULARY = load_vocabulary()


def normalize_gloss(gloss: str) -> str:
    """Trim surrounding whitespace and uppercase a gloss without altering it."""
    if not isinstance(gloss, str):
        raise TypeError("Glosses must be strings.")
    return gloss.strip().upper()


def validate_glosses(
    glosses: list[str],
    vocabulary: frozenset[str] = VOCABULARY,
) -> list[str]:
    """Return normalized glosses or raise with all unknown entries and any IDLE."""
    if not isinstance(glosses, list) or not glosses:
        raise VocabularyValidationError("Glosses list cannot be empty.")

    normalized_glosses = [normalize_gloss(gloss) for gloss in glosses]
    if any(not gloss for gloss in normalized_glosses):
        raise VocabularyValidationError(
            "Glosses cannot contain empty or whitespace-only tokens."
        )

    unknown_glosses = tuple(
        gloss for gloss in normalized_glosses if gloss not in vocabulary
    )
    idle_glosses = tuple(gloss for gloss in normalized_glosses if gloss == "IDLE")
    if unknown_glosses or idle_glosses:
        errors: list[str] = []
        if unknown_glosses:
            errors.append(f"Unknown glosses: {', '.join(unknown_glosses)}.")
        if idle_glosses:
            errors.append("IDLE cannot be used to generate a sentence.")
        raise VocabularyValidationError(
            " ".join(errors),
            unknown_glosses=unknown_glosses,
            idle_glosses=idle_glosses,
        )

    return normalized_glosses
