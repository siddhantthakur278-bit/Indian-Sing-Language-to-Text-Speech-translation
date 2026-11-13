"""
Unit tests for Indic translation and caching module.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from translate import translate_text, _TRANSLATION_CACHE


class TestTranslationModule(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
