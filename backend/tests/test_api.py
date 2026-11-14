"""
API Integration and Endpoint Contract Tests
"""

from unittest.mock import Mock

import pytest

from fastapi.testclient import TestClient
from backend import main as main_module

client = TestClient(main_module.app)


@pytest.fixture(autouse=True)
def clear_api_state():
    main_module.response_cache.clear()
    main_module.rate_limiter.clear()
    yield
    main_module.response_cache.clear()
    main_module.rate_limiter.clear()


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sentence_translation_endpoint_success():
    payload = {
        "glosses": ["ME", "HOSPITAL", "GO"],
        "lang": "hi"
    }
    response = client.post("/api/sentence", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "sentence" in data
    assert "translated" in data
    assert data["lang"] == "hi"
    assert data["emergency"] is True or "hospital" in data["sentence"].lower()
    assert data["audio_url"] is None


def test_sentence_translation_emergency_response():
    payload = {
        "glosses": ["HELP", "PAIN"],
        "lang": "mr"
    }
    response = client.post("/api/sentence", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["emergency"] is True
    assert data["lang"] == "mr"


def test_invalid_language_code():
    payload = {
        "glosses": ["HELLO"],
        "lang": "invalid_lang_code"
    }
    response = client.post("/api/sentence", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_empty_glosses():
    payload = {
        "glosses": [],
        "lang": "en"
    }
    response = client.post("/api/sentence", json=payload)
    assert response.status_code == 422


def test_known_gloss_is_accepted():
    response = client.post("/api/sentence", json={"glosses": ["HELLO"], "lang": "en"})

    assert response.status_code == 200
    assert response.json()["sentence"] == "Hello!"


def test_unknown_gloss_returns_bad_request_with_message():
    response = client.post(
        "/api/sentence",
        json={"glosses": ["NOT_A_SIGN"], "lang": "en"},
    )

    assert response.status_code == 400
    assert response.json() == {"message": "Unknown glosses: NOT_A_SIGN."}


def test_multiple_unknown_glosses_are_reported_together():
    response = client.post(
        "/api/sentence",
        json={"glosses": ["UNKNOWN_ONE", "HELLO", "UNKNOWN_TWO"], "lang": "en"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "message": "Unknown glosses: UNKNOWN_ONE, UNKNOWN_TWO."
    }


def test_idle_is_rejected_for_sentence_generation():
    response = client.post(
        "/api/sentence",
        json={"glosses": ["IDLE"], "lang": "en"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "message": "IDLE cannot be used to generate a sentence."
    }


def test_lowercase_glosses_are_normalized_before_processing(monkeypatch):
    sentence_mock = Mock(return_value=("Hello!", False))
    translate_mock = Mock(return_value="Hello!")
    tts_mock = Mock(return_value=None)
    monkeypatch.setattr(main_module, "glosses_to_sentence", sentence_mock)
    monkeypatch.setattr(main_module, "translate_text", translate_mock)
    monkeypatch.setattr(main_module, "get_speech_audio", tts_mock)

    response = client.post(
        "/api/sentence",
        json={"glosses": [" hello ", " thank_you "], "lang": "en"},
    )

    assert response.status_code == 200
    sentence_mock.assert_called_once_with(["HELLO", "THANK_YOU"])
    translate_mock.assert_called_once_with("Hello!", "en")
    tts_mock.assert_called_once_with("Hello!", "en")


def test_emergency_glosses_still_return_emergency_response():
    response = client.post(
        "/api/sentence",
        json={"glosses": ["HELP", "PAIN"], "lang": "mr"},
    )

    assert response.status_code == 200
    assert response.json()["emergency"] is True


@pytest.mark.parametrize(
    "language",
    ["en", "hi", "mr", "ta", "bn", "te", "gu", "kn", "ml", "pa"],
)
def test_supported_languages_remain_accepted(language):
    response = client.post(
        "/api/sentence",
        json={"glosses": ["HELLO"], "lang": language},
    )

    assert response.status_code == 200
    assert response.json()["lang"] == language


def test_sentence_response_structure_is_unchanged():
    response = client.post(
        "/api/sentence",
        json={"glosses": ["HELLO"], "lang": "en"},
    )

    assert response.status_code == 200
    assert set(response.json()) == {
        "sentence",
        "translated",
        "lang",
        "emergency",
        "audio_url",
    }


@pytest.mark.parametrize(
    "glosses",
    [["UNKNOWN"], ["IDLE"]],
)
def test_invalid_vocabulary_does_not_call_downstream_processing(
    monkeypatch, glosses
):
    sentence_mock = Mock()
    translate_mock = Mock()
    tts_mock = Mock()
    monkeypatch.setattr(main_module, "glosses_to_sentence", sentence_mock)
    monkeypatch.setattr(main_module, "translate_text", translate_mock)
    monkeypatch.setattr(main_module, "get_speech_audio", tts_mock)

    response = client.post(
        "/api/sentence",
        json={"glosses": glosses, "lang": "en"},
    )

    assert response.status_code == 400
    sentence_mock.assert_not_called()
    translate_mock.assert_not_called()
    tts_mock.assert_not_called()
