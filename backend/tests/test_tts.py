"""
Unit tests for Text-to-Speech (TTS) configuration and voice mappings.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tts import LANGUAGE_VOICE_MAP, get_speech_audio


class TestTTSModule(unittest.TestCase):

    def test_voice_mapping_coverage(self):
        core_languages = ["en", "hi", "mr", "ta", "bn", "te", "gu", "kn", "ml", "pa"]
        for lang in core_languages:
            self.assertIn(lang, LANGUAGE_VOICE_MAP)
            self.assertTrue(LANGUAGE_VOICE_MAP[lang].endswith("-IN"))

    def test_default_browser_fallback_returns_none(self):
        # When cloud API keys are absent, returns None so frontend uses Web Speech API
        audio_url = get_speech_audio("नमस्ते", "hi")
        self.assertIsNone(audio_url)


if __name__ == "__main__":
    unittest.main()
