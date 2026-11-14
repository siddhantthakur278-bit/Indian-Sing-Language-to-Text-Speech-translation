"""Unit tests for the verified multilingual dictionary."""

import pytest
from backend.multilingual_dict import MULTILINGUAL_DICTIONARY, lookup_multilingual_phrase

SUPPORTED_LANGS = ["en", "hi", "mr", "ta", "bn", "te", "gu", "kn", "ml", "pa"]

def test_all_phrases_have_all_ten_languages():
    """Verify every registered dictionary phrase has translations in all 10 scheduled languages."""
    for phrase, lang_map in MULTILINGUAL_DICTIONARY.items():
        assert len(phrase) > 0, "Dictionary key must not be empty"
        for lang in SUPPORTED_LANGS:
            assert lang in lang_map, f"Missing {lang} translation for '{phrase}'"
            assert len(lang_map[lang].strip()) > 0, f"Empty {lang} translation for '{phrase}'"

def test_lookup_emergency_phrases():
    """Verify emergency SOS phrase lookup across multiple languages."""
    phrase = "Please help me immediately!"
    
    hi_trans = lookup_multilingual_phrase(phrase, "hi")
    assert hi_trans == "कृपया तुरंत मेरी मदद करें!"

    mr_trans = lookup_multilingual_phrase(phrase, "mr")
    assert mr_trans == "कृपया मला लगेच मदत करा!"

    ta_trans = lookup_multilingual_phrase(phrase, "ta")
    assert ta_trans == "தயவுசெய்து எனக்கு உடனே உதவுங்கள்!"

def test_lookup_unknown_phrase_returns_none():
    """Verify searching for an uncatalogued phrase returns None without raising an error."""
    result = lookup_multilingual_phrase("Non-existent sign sentence", "hi")
    assert result is None

def test_lookup_strips_whitespace():
    """Verify whitespace handling during lookup."""
    padded = "  I need to go to the hospital.  "
    result = lookup_multilingual_phrase(padded, "hi")
    assert result == "मुझे अस्पताल जाना है।"
