"""
Unit tests for Text-to-Speech (TTS) configuration and voice mappings.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tts import (
    CLOUD_TTS_AVAILABLE,
    LANGUAGE_VOICE_MAP,
    TTS_MODE,
    get_speech_audio,
    get_tts_status,
    get_voice_locale,
)


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

    def test_locale_lookup_normalizes_language_code(self):
        self.assertEqual(get_voice_locale(" HI "), "hi-IN")
        self.assertEqual(get_voice_locale("mr"), "mr-IN")

    def test_locale_lookup_rejects_unsupported_language(self):
        with self.assertRaises(ValueError):
            get_voice_locale("xx")

    def test_tts_status_reports_browser_fallback_not_cloud(self):
        status = get_tts_status()

        self.assertEqual(TTS_MODE, "browser_speech_synthesis")
        self.assertFalse(CLOUD_TTS_AVAILABLE)
        self.assertFalse(status["cloud_available"])
        self.assertEqual(set(status["supported_languages"]), set(LANGUAGE_VOICE_MAP))


if __name__ == "__main__":
    unittest.main()
