"""
Unit tests for Indic translation and caching module.
"""

import unittest
import sys
import os
from unittest.mock import Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import translate
from translate import (
    OfflineCsvTranslationProvider,
    TranslationCache,
    translate_text,
)


class TestTranslationModule(unittest.TestCase):
    def setUp(self):
        translate._TRANSLATION_CACHE.clear()


    def test_english_pass_through(self):
        text = "I am going to the hospital."
        res = translate_text(text, "en")
        self.assertEqual(res, text)

    def test_cached_hindi_lookup(self):
        text = "Please help me."
        res = translate_text(text, "hi")
        self.assertTrue(len(res) > 0)
        self.assertTrue("मदद" in res or "सहायता" in res)

    def test_cached_marathi_lookup(self):
        text = "Please help me."
        res = translate_text(text, "mr")
        self.assertTrue(len(res) > 0)
        self.assertIn("मदत", res)

    def test_empty_string_handling(self):
        self.assertEqual(translate_text("", "hi"), "")
        self.assertEqual(translate_text("   ", "mr"), "   ")

    def test_translation_cache_is_bounded_and_evicts_lru(self):
        cache = TranslationCache(max_entries=2)
        first = ("one", "hi")
        second = ("two", "hi")
        third = ("three", "mr")
        cache.put(first, "१")
        cache.put(second, "२")

        self.assertEqual(cache.get(first), "१")
        cache.put(third, "३")

        self.assertEqual(len(cache), 2)
        self.assertIsNone(cache.get(second))
        self.assertEqual(cache.get(first), "१")
        self.assertEqual(cache.get(third), "३")

    def test_identical_translation_uses_provider_once(self):
        provider = Mock()
        provider.translate.return_value = "नमस्ते"
        self.enterContext(
            unittest.mock.patch.object(translate, "_TRANSLATION_PROVIDER", provider)
        )

        self.assertEqual(translate_text("Hello!", "hi"), "नमस्ते")
        self.assertEqual(translate_text("Hello!", "hi"), "नमस्ते")
        provider.translate.assert_called_once_with("Hello!", "hi")

    def test_cache_separates_target_languages(self):
        provider = Mock()
        provider.translate.side_effect = lambda text, language: f"{language}:{text}"
        self.enterContext(
            unittest.mock.patch.object(translate, "_TRANSLATION_PROVIDER", provider)
        )

        self.assertEqual(translate_text("Hello!", "hi"), "hi:Hello!")
        self.assertEqual(translate_text("Hello!", "mr"), "mr:Hello!")
        self.assertEqual(provider.translate.call_count, 2)

    def test_missing_offline_translation_falls_back_without_caching(self):
        provider = Mock()
        provider.translate.return_value = None
        self.enterContext(
            unittest.mock.patch.object(translate, "_TRANSLATION_PROVIDER", provider)
        )

        self.assertEqual(translate_text("No matching sentence.", "hi"), "No matching sentence.")
        self.assertEqual(translate_text("No matching sentence.", "hi"), "No matching sentence.")
        self.assertEqual(provider.translate.call_count, 2)

    def test_csv_provider_uses_existing_offline_pair(self):
        provider = OfflineCsvTranslationProvider()

        self.assertIn(
            provider.translate("Please help me.", "hi"),
            {"कृपया मेरी मदद करें।", "कृपया मेरी सहायता करें।"},
        )
        self.assertEqual(
            provider.translate("Please help me.", "mr"),
            "कृपया मला मदत करा.",
        )


if __name__ == "__main__":
    unittest.main()
