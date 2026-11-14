"""Offline Indic translation adapter with a bounded, thread-safe LRU cache."""

import csv
import logging
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Protocol

from backend.vocabulary import VOCABULARY

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GLOSS_PAIRS_PATH = PROJECT_ROOT / "data" / "gloss_pairs.csv"
MAX_TRANSLATION_CACHE_ENTRIES = 256
REQUIRED_CSV_FIELDS = (
    "gloss_sequence",
    "english_sentence",
    "hindi_translation",
    "marathi_translation",
    "is_emergency",
)

INDICTRANS2_LANG_MAP = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "mr": "mar_Deva",
    "ta": "tam_Taml",
    "bn": "ben_Beng",
    "te": "tel_Telu",
    "gu": "guj_Gujr",
    "kn": "kan_Knda",
    "ml": "mal_Mlym",
    "pa": "pan_Guru",
}


class TranslationProvider(Protocol):
    """Interface implemented by available translation adapters."""

    def translate(self, text: str, target_lang: str) -> str | None:
        """Return a translation or None when this provider has no result."""


class TranslationProviderError(RuntimeError):
    """Raised when an external translation provider fails."""


class TranslationDatasetError(ValueError):
    """Raised when the offline CSV has malformed or invalid data."""


def load_translation_dataset(
    csv_path: Path = GLOSS_PAIRS_PATH,
) -> tuple[dict[tuple[str, str], str], tuple[str, ...]]:
    """Validate the CSV and return lookup pairs plus detected conflicts."""
    translations: dict[tuple[str, str], str] = {}
    seen_records: set[tuple[str, ...]] = set()
    conflicts: set[str] = set()
    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file, strict=True)
            if tuple(reader.fieldnames or ()) != REQUIRED_CSV_FIELDS:
                raise TranslationDatasetError(
                    f"Expected CSV fields in order: {', '.join(REQUIRED_CSV_FIELDS)}"
                )

            for line_number, row in enumerate(reader, start=2):
                if None in row or any(
                    row.get(field) is None for field in REQUIRED_CSV_FIELDS
                ):
                    raise TranslationDatasetError(
                        f"Malformed CSV row at line {line_number}: "
                        "column count does not match the header."
                    )

                normalized = {
                    field: row[field].strip() for field in REQUIRED_CSV_FIELDS
                }
                missing = [
                    field for field, value in normalized.items() if not value
                ]
                if missing:
                    raise TranslationDatasetError(
                        f"Missing required values at line {line_number}: "
                        f"{', '.join(missing)}."
                    )

                glosses = normalized["gloss_sequence"].split()
                if not glosses or any(
                    gloss not in VOCABULARY or gloss == "IDLE" for gloss in glosses
                ):
                    raise TranslationDatasetError(
                        f"Invalid or non-canonical gloss sequence at line "
                        f"{line_number}: {normalized['gloss_sequence']!r}."
                    )

                label = normalized["is_emergency"].lower()
                if label not in {"true", "false"}:
                    raise TranslationDatasetError(
                        f"Invalid is_emergency value at line {line_number}: "
                        f"{normalized['is_emergency']!r}."
                    )
                normalized["is_emergency"] = label

                record = tuple(normalized[field] for field in REQUIRED_CSV_FIELDS)
                if record in seen_records:
                    raise TranslationDatasetError(
                        f"Duplicate CSV record at line {line_number}."
                    )
                seen_records.add(record)

                english = normalized["english_sentence"].casefold()
                for language, field in (
                    ("hi", "hindi_translation"),
                    ("mr", "marathi_translation"),
                ):
                    key = (english, language)
                    translated = normalized[field]
                    existing = translations.get(key)
                    if existing is not None and existing != translated:
                        conflicts.add(
                            f"{language}:{normalized['english_sentence']}"
                        )
                    translations[key] = translated
    except TranslationDatasetError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise TranslationDatasetError(
            f"Could not load valid UTF-8 CSV from {csv_path}: {exc}"
        ) from exc

    return translations, tuple(sorted(conflicts))


class OfflineCsvTranslationProvider:
    """Look up existing Hindi and Marathi translations from the committed CSV."""

    _translation_fields = {
        "hi": "hindi_translation",
        "mr": "marathi_translation",
    }

    def __init__(self, csv_path: Path = GLOSS_PAIRS_PATH) -> None:
        try:
            self._translations, self.translation_conflicts = load_translation_dataset(
                csv_path
            )
        except TranslationDatasetError as exc:
            logger.warning(
                "Offline translation dataset unavailable (%s); English fallback is active",
                exc,
            )
            self._translations = {}
            self.translation_conflicts = ()
        if self.translation_conflicts:
            logger.warning(
                "Offline translations contain %d conflicting language/sentence "
                "lookup keys; deterministic last-row values are used",
                len(self.translation_conflicts),
            )

    def translate(self, text: str, target_lang: str) -> str | None:
        """Return a CSV translation for a matching sentence and language."""
        field = self._translation_fields.get(target_lang)
        if field is None:
            return None
        return self._translations.get((text.strip().casefold(), target_lang))


class TranslationCache:
    """Thread-safe least-recently-used cache with a fixed maximum size."""

    def __init__(self, max_entries: int = MAX_TRANSLATION_CACHE_ENTRIES) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be greater than zero")
        self._max_entries = max_entries
        self._entries: OrderedDict[tuple[str, str], str] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: tuple[str, str]) -> str | None:
        """Get and promote a cached translation."""
        with self._lock:
            value = self._entries.get(key)
            if value is not None:
                self._entries.move_to_end(key)
            return value

    def put(self, key: tuple[str, str], value: str) -> None:
        """Store a translated value, evicting least-recently-used entries."""
        with self._lock:
            self._entries[key] = value
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        """Remove cached translations."""
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


_TRANSLATION_PROVIDER: TranslationProvider = OfflineCsvTranslationProvider()
_TRANSLATION_CACHE = TranslationCache()
TRANSLATION_MODE = "offline_csv_with_english_fallback"


def translate_text(text: str, target_lang: str) -> str:
    """Translate using available offline data, otherwise return the English source."""
    if not text:
        return ""

    norm_target = target_lang.lower().strip()
    if norm_target == "en":
        return text

    cache_key = (text.strip().casefold(), norm_target)
    cached = _TRANSLATION_CACHE.get(cache_key)
    if cached is not None:
        return cached

    translated = _TRANSLATION_PROVIDER.translate(text, norm_target)
    if translated:
        _TRANSLATION_CACHE.put(cache_key, translated)
        return translated

    # Check for Gemini / LLM Translation if configured
    llm_key = os.getenv("LLM_API_KEY")
    if llm_key:
        try:
            import urllib.request
            import json
            lang_names = {
                "hi": "Hindi", "mr": "Marathi", "ta": "Tamil", "bn": "Bengali",
                "te": "Telugu", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi"
            }
            target_name = lang_names.get(norm_target, norm_target)
            model = os.getenv("LLM_MODEL", "gemini-flash-lite-latest")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={llm_key}"
            prompt = f"Translate this English sentence into {target_name}: {text}. Output only the {target_name} translated text, with no explanations or notes."
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}]
            }).encode("utf-8")

            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        translated = parts[0].get("text", "").strip()
                        translated = translated.replace('"', '').replace('`', '').strip()
                        if translated:
                            _TRANSLATION_CACHE.put(cache_key, translated)
                            return translated
        except Exception as e:
            logger.warning(f"Gemini translation failed: {e}")

    # Check offline verified multilingual dictionary (10 languages)
    try:
        from backend.multilingual_dict import lookup_multilingual_phrase
        dict_trans = lookup_multilingual_phrase(text, norm_target)
        if dict_trans:
            _TRANSLATION_CACHE.put(cache_key, dict_trans)
            return dict_trans
    except Exception as e:
        logger.warning(f"Dictionary lookup error: {e}")

    logger.info(
        "Offline translation unavailable for target '%s'; returning English text",
        norm_target,
    )
    return text
