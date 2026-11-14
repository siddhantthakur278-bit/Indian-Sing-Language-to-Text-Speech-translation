"""
Unit tests for Indic translation and caching module.
"""

import unittest
import sys
import os
import csv
import tempfile
from unittest.mock import Mock
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import translate
from translate import (
    OfflineCsvTranslationProvider,
    TranslationCache,
    TranslationDatasetError,
    load_translation_dataset,
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

    def test_loader_rejects_missing_required_field(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pairs.csv"
            path.write_text(
                "gloss_sequence,english_sentence,hindi_translation,"
                "marathi_translation,is_emergency\n"
                "HELLO,Hello!,नमस्ते,,false\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                TranslationDatasetError, "Missing required values"
            ):
                load_translation_dataset(path)

    def test_loader_rejects_malformed_row_and_extra_columns(self):
        rows = [
            "gloss_sequence,english_sentence,hindi_translation,"
            "marathi_translation,is_emergency",
            "HELLO,Hello!,नमस्ते,नमस्कार,false,unexpected",
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pairs.csv"
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(
                TranslationDatasetError, "Malformed CSV row"
            ):
                load_translation_dataset(path)

    def test_loader_rejects_invalid_vocabulary_and_emergency_label(self):
        cases = [
            ("UNKNOWN", "false", "non-canonical gloss"),
            ("HELLO", "maybe", "Invalid is_emergency"),
        ]
        for glosses, label, expected_error in cases:
            with self.subTest(glosses=glosses, label=label):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "pairs.csv"
                    write_translation_rows(
                        path,
                        [
                            {
                                "gloss_sequence": glosses,
                                "english_sentence": "Example.",
                                "hindi_translation": "उदाहरण।",
                                "marathi_translation": "उदाहरण।",
                                "is_emergency": label,
                            }
                        ],
                    )
                    with self.assertRaisesRegex(
                        TranslationDatasetError, expected_error
                    ):
                        load_translation_dataset(path)

    def test_loader_rejects_exact_duplicate_records(self):
        row = {
            "gloss_sequence": "HELLO",
            "english_sentence": "Hello!",
            "hindi_translation": "नमस्ते!",
            "marathi_translation": "नमस्कार!",
            "is_emergency": "false",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pairs.csv"
            write_translation_rows(path, [row, row])

            with self.assertRaisesRegex(TranslationDatasetError, "Duplicate"):
                load_translation_dataset(path)

    def test_loader_accepts_utf8_bom_and_reports_lookup_conflicts(self):
        rows = [
            {
                "gloss_sequence": "HELLO",
                "english_sentence": "Hello!",
                "hindi_translation": "नमस्ते!",
                "marathi_translation": "नमस्कार!",
                "is_emergency": "false",
            },
            {
                "gloss_sequence": "YOU",
                "english_sentence": " hello! ",
                "hindi_translation": "प्रणाम!",
                "marathi_translation": "नमस्कार!",
                "is_emergency": "false",
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pairs.csv"
            write_translation_rows(path, rows, encoding="utf-8-sig")

            translations, conflicts = load_translation_dataset(path)

        self.assertEqual(conflicts, ("hi:hello!",))
        self.assertEqual(translations[("hello!", "hi")], "प्रणाम!")

    def test_loader_rejects_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pairs.csv"
            path.write_bytes(b"\xff\xfe\xff")

            with self.assertRaisesRegex(TranslationDatasetError, "valid UTF-8"):
                load_translation_dataset(path)


if __name__ == "__main__":
    unittest.main()


def write_translation_rows(path, rows, *, encoding="utf-8"):
    fields = (
        "gloss_sequence",
        "english_sentence",
        "hindi_translation",
        "marathi_translation",
        "is_emergency",
    )
    with path.open("w", encoding=encoding, newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
