"""API integration and endpoint contract tests."""

from dataclasses import replace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from backend import main as main_module
from backend.translate import TranslationProviderError

client = TestClient(main_module.app)


@pytest.fixture(autouse=True)
def clear_api_state():
    """Keep process-local rate-limit and cache state isolated per test."""
    main_module.response_cache.clear()
    main_module.rate_limiter.clear()
    yield
    main_module.response_cache.clear()
    main_module.rate_limiter.clear()


def test_health_check_endpoint(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "features": {
            "gloss_to_sentence": "rules_only",
            "translation": "offline_csv_with_english_fallback",
            "tts": {
                "mode": "browser_speech_synthesis",
                "cloud_available": False,
                "supported_languages": [
                    "bn",
                    "en",
                    "gu",
                    "hi",
                    "kn",
                    "ml",
                    "mr",
                    "pa",
                    "ta",
                    "te",
                ],
            },
        },
    }


def test_health_reports_gemini_configuration_without_exposing_credentials(
    monkeypatch,
):
    monkeypatch.setenv("LLM_API_KEY", "do-not-return-this-value")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["features"]["gloss_to_sentence"] == "rules_with_gemini"
    assert "do-not-return-this-value" not in response.text


def test_sentence_translation_endpoint_success():
    response = client.post(
        "/api/sentence",
        json={"glosses": ["ME", "HOSPITAL", "GO"], "lang": "hi"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "sentence" in data
    assert "translated" in data
    assert data["lang"] == "hi"
    assert data["emergency"] is True or "hospital" in data["sentence"].lower()
    assert data["audio_url"] is None


def test_sentence_translation_emergency_response():
    response = client.post(
        "/api/sentence",
        json={"glosses": ["HELP", "PAIN"], "lang": "mr"},
    )

    assert response.status_code == 200
    assert response.json()["emergency"] is True
    assert response.json()["lang"] == "mr"


def test_invalid_language_code():
    response = client.post(
        "/api/sentence",
        json={"glosses": ["HELLO"], "lang": "invalid_lang_code"},
    )

    assert response.status_code == 422


def test_empty_glosses():
    response = client.post(
        "/api/sentence",
        json={"glosses": [], "lang": "en"},
    )

    assert response.status_code == 422


def test_known_gloss_is_accepted():
    response = client.post(
        "/api/sentence",
        json={"glosses": ["HELLO"], "lang": "en"},
    )

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


def test_unknown_can_gloss_is_rejected_before_sentence_nlp(monkeypatch):
    sentence_mock = Mock()
    monkeypatch.setattr(main_module, "glosses_to_sentence", sentence_mock)

    response = client.post(
        "/api/sentence",
        json={"glosses": ["YOU", "HELP", "ME", "CAN"], "lang": "en"},
    )

    assert response.status_code == 400
    assert response.json() == {"message": "Unknown glosses: CAN."}
    sentence_mock.assert_not_called()


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


def test_translation_provider_error_returns_502_and_is_not_cached(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "translate_text",
        Mock(side_effect=TranslationProviderError("provider unavailable")),
    )

    response = client.post(
        "/api/sentence",
        json={"glosses": ["HELLO"], "lang": "hi"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "message": "Translation service is unavailable."
    }
    assert len(main_module.response_cache) == 0


@pytest.mark.parametrize("glosses", [["UNKNOWN"], ["IDLE"]])
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


def test_text_to_gloss_endpoint_returns_two_way_response():
    response = client.post(
        "/api/text-to-gloss",
        json={"text": "I am going to the hospital"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "original_text": "I am going to the hospital",
        "glosses": ["ME", "HOSPITAL", "GO"],
    }


def test_text_to_gloss_endpoint_rejects_text_over_200_characters():
    response = client.post(
        "/api/text-to-gloss",
        json={"text": "a" * 201},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("text", ["", "  \t "])
def test_text_to_gloss_endpoint_rejects_blank_text(text):
    response = client.post("/api/text-to-gloss", json={"text": text})

    assert response.status_code == 422


def test_text_to_gloss_and_sentence_share_rate_limit(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "settings",
        replace(main_module.settings, rate_limit_per_min=1),
    )

    first = client.post(
        "/api/sentence",
        json={"glosses": ["HELLO"], "lang": "en"},
    )
    second = client.post("/api/text-to-gloss", json={"text": "hello"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["message"] == (
        "Rate limit exceeded. Maximum 1 requests per minute."
    )
