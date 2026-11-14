"""Unit tests for reusable sentence API schemas."""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from schemas import SentenceRequest, SentenceResponse


@pytest.mark.parametrize("language", ["en", "hi", "mr"])
def test_valid_request_for_supported_initial_languages(language):
    request = SentenceRequest(glosses=["HELLO"], lang=language)

    assert request.glosses == ["HELLO"]
    assert request.lang == language


def test_request_defaults_to_english():
    request = SentenceRequest(glosses=["HELLO"])

    assert request.lang == "en"


def test_request_normalizes_language_code():
    request = SentenceRequest(glosses=["HELLO"], lang=" HI ")

    assert request.lang == "hi"


def test_request_rejects_empty_gloss_list():
    with pytest.raises(ValidationError):
        SentenceRequest(glosses=[])


def test_request_rejects_more_than_twenty_glosses():
    with pytest.raises(ValidationError):
        SentenceRequest(glosses=["HELLO"] * 21)


def test_request_rejects_unsupported_language():
    with pytest.raises(ValidationError):
        SentenceRequest(glosses=["HELLO"], lang="xx")


def test_request_rejects_empty_gloss_token():
    with pytest.raises(ValidationError):
        SentenceRequest(glosses=[""])


def test_request_rejects_whitespace_only_gloss_token():
    with pytest.raises(ValidationError):
        SentenceRequest(glosses=[" \t "])


@pytest.mark.parametrize(
    "payload",
    [
        {"glosses": "HELLO"},
        {"glosses": [1]},
        {"glosses": ["HELLO"], "lang": 1},
    ],
)
def test_request_rejects_invalid_field_types(payload):
    with pytest.raises(ValidationError):
        SentenceRequest.model_validate(payload)


def test_valid_response_model():
    response = SentenceResponse(
        sentence="Hello!",
        translated="नमस्ते!",
        lang="hi",
        emergency=False,
        audio_url="https://example.com/audio.mp3",
    )

    assert response.model_dump() == {
        "sentence": "Hello!",
        "translated": "नमस्ते!",
        "lang": "hi",
        "emergency": False,
        "audio_url": "https://example.com/audio.mp3",
    }


def test_response_defaults_audio_url_to_none():
    response = SentenceResponse(
        sentence="Hello!",
        translated="Hello!",
        lang="en",
        emergency=False,
    )

    assert response.audio_url is None


def test_emergency_response_model():
    response = SentenceResponse(
        sentence="Please help me.",
        translated="कृपया मेरी मदद करें।",
        lang="hi",
        emergency=True,
    )

    assert response.emergency is True
    assert response.audio_url is None
