"""
Text-to-Speech (TTS) Integration Module
Handles voice synthesis requests for Indian Languages.
By default returns audio_url=None to signal the frontend to utilize the zero-cost,
client-side Web Speech API (speechSynthesis).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Standard BCP 47 language tags for browser speechSynthesis
LANGUAGE_VOICE_MAP = {
    "en": "en-IN",
    "hi": "hi-IN",
    "mr": "mr-IN",
    "ta": "ta-IN",
    "bn": "bn-IN",
    "te": "te-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "pa": "pa-IN",
}

TTS_MODE = "browser_speech_synthesis"
CLOUD_TTS_AVAILABLE = False


def get_voice_locale(lang: str) -> str:
    """Return a configured Indian English BCP 47 locale or raise for unknown codes."""
    normalized = lang.strip().lower()
    try:
        return LANGUAGE_VOICE_MAP[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported speech language code: {lang!r}") from exc


def get_tts_status() -> dict[str, object]:
    """Describe the real TTS availability without implying cloud service support."""
    return {
        "mode": TTS_MODE,
        "cloud_available": CLOUD_TTS_AVAILABLE,
        "supported_languages": sorted(LANGUAGE_VOICE_MAP),
    }


def get_speech_audio(text: str, lang: str) -> Optional[str]:
    """
    Validate the language and return None for browser speech synthesis fallback.

    Cloud TTS is not implemented by this backend.
    """
    get_voice_locale(lang)
    if not text:
        return None

    logger.debug("Cloud TTS is not implemented; frontend browser speech is required")
    return None
