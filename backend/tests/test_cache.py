"""Tests for bounded caching of successful sentence API responses."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from backend import main as main_module
from backend.cache import ResponseCache


@pytest.fixture(autouse=True)
def clear_api_state():
    main_module.response_cache.clear()
    main_module.rate_limiter.clear()
    yield
    main_module.response_cache.clear()
    main_module.rate_limiter.clear()


def test_identical_valid_requests_use_cached_response(monkeypatch):
    sentence_mock = Mock(return_value=("Hello!", False))
    translate_mock = Mock(return_value="Hello!")
    tts_mock = Mock(return_value=None)
    monkeypatch.setattr(main_module, "glosses_to_sentence", sentence_mock)
    monkeypatch.setattr(main_module, "translate_text", translate_mock)
    monkeypatch.setattr(main_module, "get_speech_audio", tts_mock)
    client = TestClient(main_module.app)
    payload = {"glosses": [" hello "], "lang": "en"}

    first = client.post("/api/sentence", json=payload)
    second = client.post("/api/sentence", json=payload)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    sentence_mock.assert_called_once_with(["HELLO"])
    translate_mock.assert_called_once_with("Hello!", "en")
    tts_mock.assert_called_once_with("Hello!", "en")


def test_responses_are_cached_separately_by_language(monkeypatch):
    sentence_mock = Mock(return_value=("Hello!", False))
    translate_mock = Mock(side_effect=lambda sentence, language: f"{language}:{sentence}")
    tts_mock = Mock(return_value=None)
    monkeypatch.setattr(main_module, "glosses_to_sentence", sentence_mock)
    monkeypatch.setattr(main_module, "translate_text", translate_mock)
    monkeypatch.setattr(main_module, "get_speech_audio", tts_mock)
    client = TestClient(main_module.app)

    english = client.post(
        "/api/sentence",
        json={"glosses": ["HELLO"], "lang": "en"},
    )
    hindi = client.post(
        "/api/sentence",
        json={"glosses": ["HELLO"], "lang": "hi"},
    )

    assert english.status_code == hindi.status_code == 200
    assert english.json()["translated"] == "en:Hello!"
    assert hindi.json()["translated"] == "hi:Hello!"
    assert translate_mock.call_count == 2
    assert len(main_module.response_cache) == 2


def test_cache_evicts_least_recently_used_entry():
    cache = ResponseCache(max_entries=2)
    first_key = (("HELLO",), "en")
    second_key = (("THANK_YOU",), "en")
    third_key = (("HELP",), "hi")

    cache.put(first_key, {"sentence": "Hello!"})
    cache.put(second_key, {"sentence": "Thank you."})
    assert cache.get(first_key) == {"sentence": "Hello!"}
    cache.put(third_key, {"sentence": "Please help me."})

    assert len(cache) == 2
    assert cache.get(first_key) == {"sentence": "Hello!"}
    assert cache.get(second_key) is None
    assert cache.get(third_key) == {"sentence": "Please help me."}


def test_invalid_vocabulary_request_is_not_cached(monkeypatch):
    sentence_mock = Mock()
    translate_mock = Mock()
    tts_mock = Mock()
    monkeypatch.setattr(main_module, "glosses_to_sentence", sentence_mock)
    monkeypatch.setattr(main_module, "translate_text", translate_mock)
    monkeypatch.setattr(main_module, "get_speech_audio", tts_mock)
    client = TestClient(main_module.app)

    response = client.post(
        "/api/sentence",
        json={"glosses": ["NOT_A_VALID_GLOSS"], "lang": "en"},
    )

    assert response.status_code == 400
    assert len(main_module.response_cache) == 0
    sentence_mock.assert_not_called()
    translate_mock.assert_not_called()
    tts_mock.assert_not_called()


def test_failed_response_is_not_cached(monkeypatch):
    translate_mock = Mock(side_effect=[RuntimeError("test failure"), "Hello!"])
    monkeypatch.setattr(
        main_module, "glosses_to_sentence", Mock(return_value=("Hello!", False))
    )
    monkeypatch.setattr(main_module, "translate_text", translate_mock)
    monkeypatch.setattr(main_module, "get_speech_audio", Mock(return_value=None))
    client = TestClient(main_module.app, raise_server_exceptions=False)
    payload = {"glosses": ["HELLO"], "lang": "en"}

    failed = client.post("/api/sentence", json=payload)
    succeeded = client.post("/api/sentence", json=payload)

    assert failed.status_code == 500
    assert succeeded.status_code == 200
    assert translate_mock.call_count == 2
    assert len(main_module.response_cache) == 1
