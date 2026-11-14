"""Offline Indic translation adapter with a bounded, thread-safe LRU cache."""

import csv
import logging
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GLOSS_PAIRS_PATH = PROJECT_ROOT / "data" / "gloss_pairs.csv"
MAX_TRANSLATION_CACHE_ENTRIES = 256

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


class OfflineCsvTranslationProvider:
    """Look up existing Hindi and Marathi translations from the committed CSV."""

    _translation_fields = {
        "hi": "hindi_translation",
        "mr": "marathi_translation",
    }

    def __init__(self, csv_path: Path = GLOSS_PAIRS_PATH) -> None:
        self._translations: dict[tuple[str, str], str] = {}
        try:
            with csv_path.open(encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    english = (row.get("english_sentence") or "").strip().casefold()
                    if not english:
                        continue
                    for language, field in self._translation_fields.items():
                        translated = (row.get(field) or "").strip()
                        if translated:
                            self._translations[(english, language)] = translated
        except FileNotFoundError:
            logger.warning(
                "Offline translation CSV is missing; English fallback is active"
            )
        except (OSError, UnicodeError, csv.Error):
            logger.exception(
                "Could not load offline translations; English fallback is active"
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

    logger.info(
        "Offline translation unavailable for target '%s'; returning English text",
        norm_target,
    )
    return text
