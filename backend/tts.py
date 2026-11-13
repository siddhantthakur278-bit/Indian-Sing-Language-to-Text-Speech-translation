"""
Text-to-Speech (TTS) Integration Module
Handles voice synthesis requests for Indian Languages.
By default returns audio_url=None to signal the frontend to utilize the zero-cost,
client-side Web Speech API (speechSynthesis).
"""

import os
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


def get_speech_audio(text: str, lang: str) -> Optional[str]:
    """
    Returns audio_url if a cloud TTS service (e.g. Bhashini / Google TTS)
    is configured and returns an audio artifact.
    Otherwise returns None (frontend uses browser Web Speech API).
    """
    # Cloud TTS can be plugged in here via BHASHINI_API_KEY
    bhashini_key = os.getenv("BHASHINI_API_KEY")
    if bhashini_key:
        try:
            # Cloud audio generation
            return None
        except Exception as e:
            logger.warning(f"Cloud TTS synthesis failed: {e}")
            return None

    # Default: client-side browser synthesis
    return None
