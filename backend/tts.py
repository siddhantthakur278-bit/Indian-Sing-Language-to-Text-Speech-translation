"""
Text-to-Speech (TTS) Integration Module
Handles voice synthesis requests for Indian Languages.
Supports high-fidelity streaming audio for Hindi, Marathi, Tamil, Bengali, English, etc.
"""

import logging
import urllib.parse
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

# Standard BCP 47 language tags
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

TTS_MODE = "hybrid_stream_with_browser_fallback"
CLOUD_TTS_AVAILABLE = True


def get_voice_locale(lang: str) -> str:
    """Return a configured Indian BCP 47 locale or raise for unknown codes."""
    normalized = lang.strip().lower()
    try:
        return LANGUAGE_VOICE_MAP[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported speech language code: {lang!r}") from exc


def get_tts_status() -> dict[str, object]:
    """Describe TTS capability."""
    return {
        "mode": TTS_MODE,
        "cloud_available": CLOUD_TTS_AVAILABLE,
        "supported_languages": sorted(LANGUAGE_VOICE_MAP),
    }


def synthesize_audio_bytes(text: str, lang: str) -> Optional[bytes]:
    """
    Synthesize speech audio bytes (MP3) for Indian languages using high-speed streaming engine.
    """
    if not text or not text.strip():
        return None

    clean_text = text.strip()
    target_lang = lang.lower().strip()
    if target_lang not in LANGUAGE_VOICE_MAP:
        target_lang = "hi"

    try:
        encoded_text = urllib.parse.quote(clean_text)
        url = (
            f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}"
            f"&tl={target_lang}&total=1&idx=0&textlen={len(clean_text)}&client=tw-ob&prev=input"
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                "Referer": "https://translate.google.com/",
            },
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            return resp.read()
    except Exception as exc:
        logger.warning(f"Native audio synthesis failed: {exc}")
        return None


def get_speech_audio(text: str, lang: str) -> Optional[str]:
    """
    Return the proxy URL for streaming speech audio.
    """
    if not text:
        return None

    encoded_text = urllib.parse.quote(text)
    return f"/api/tts?text={encoded_text}&lang={urllib.parse.quote(lang)}"
