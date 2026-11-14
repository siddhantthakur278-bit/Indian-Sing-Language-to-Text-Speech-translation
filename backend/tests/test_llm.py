"""Tests for the Gemini REST adapter without external network access."""

from unittest.mock import Mock

import requests

from backend import llm


def _response(payload, *, status_code=200):
    response = Mock()
    response.ok = 200 <= status_code < 300
    response.status_code = status_code
    response.json.return_value = payload
    return response


def test_generate_text_uses_configured_gemini_rest_request(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "unit-test-secret")
    monkeypatch.setenv("LLM_MODEL", "gemini-test-model")
    post = Mock(
        return_value=_response(
            {
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {"parts": [{"text": "  I am going home.  "}]},
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(llm.requests, "post", post)

    result = llm.generate_text(
        "Translate these glosses: ME HOME GO",
        source_glosses=["ME", "HOME", "GO"],
    )

    assert result == "I am going home."
    post.assert_called_once()
    args, kwargs = post.call_args
    assert args == (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-test-model:generateContent",
    )
    assert kwargs["headers"] == {"x-goog-api-key": "unit-test-secret"}
    assert kwargs["json"]["contents"] == [
        {"parts": [{"text": "Translate these glosses: ME HOME GO"}]}
    ]
    assert kwargs["json"]["generationConfig"] == {
        "candidateCount": 1,
        "temperature": 0.0,
        "maxOutputTokens": 128,
    }
    assert kwargs["timeout"] == llm.REQUEST_TIMEOUT_SECONDS


def test_generate_text_uses_default_model(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "unit-test-secret")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    post = Mock(return_value=_response({"candidates": []}))
    monkeypatch.setattr(llm.requests, "post", post)

    assert llm.generate_text("prompt", source_glosses=["HELLO"]) is None
    assert llm.DEFAULT_GEMINI_MODEL in post.call_args.args[0]


def test_generate_text_skips_request_without_api_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    post = Mock()
    monkeypatch.setattr(llm.requests, "post", post)

    assert llm.generate_text("prompt", source_glosses=["HELLO"]) is None
    post.assert_not_called()


def test_generate_text_falls_back_on_transport_error(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "unit-test-secret")
    post = Mock(side_effect=requests.Timeout())
    monkeypatch.setattr(llm.requests, "post", post)

    assert llm.generate_text("prompt", source_glosses=["HELLO"]) is None


def test_generate_text_falls_back_on_http_failure(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "unit-test-secret")
    monkeypatch.setattr(llm.requests, "post", Mock(return_value=_response({}, status_code=503)))

    assert llm.generate_text("prompt", source_glosses=["HELP"]) is None


def test_generate_text_rejects_blocked_or_incomplete_candidate(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "unit-test-secret")
    blocked = _response(
        {
            "candidates": [
                {
                    "finishReason": "SAFETY",
                    "content": {"parts": [{"text": "unsafe"}]},
                }
            ]
        }
    )
    monkeypatch.setattr(llm.requests, "post", Mock(return_value=blocked))

    assert llm.generate_text("prompt", source_glosses=["HELP"]) is None


def test_generate_text_rejects_empty_or_multiline_output(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "unit-test-secret")
    post = Mock(
        side_effect=[
            _response({"candidates": [{"content": {"parts": [{"text": "  "}]}}]}),
            _response(
                {"candidates": [{"content": {"parts": [{"text": "One.\nTwo."}]}}]}
            ),
        ]
    )
    monkeypatch.setattr(llm.requests, "post", post)

    assert llm.generate_text("prompt", source_glosses=["HELLO"]) is None
    assert llm.generate_text("prompt", source_glosses=["HELLO"]) is None


def test_generate_text_rejects_unsupported_content_words(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "unit-test-secret")
    monkeypatch.setattr(
        llm.requests,
        "post",
        Mock(
            return_value=_response(
                {
                    "candidates": [
                        {
                            "finishReason": "STOP",
                            "content": {
                                "parts": [{"text": "I am going to the hospital."}]
                            },
                        }
                    ]
                }
            )
        ),
    )

    assert (
        llm.generate_text(
            "prompt",
            source_glosses=["ME", "HOME", "GO"],
        )
        is None
    )


def test_generate_text_accepts_gloss_grounded_content(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "unit-test-secret")
    monkeypatch.setattr(
        llm.requests,
        "post",
        Mock(
            return_value=_response(
                {
                    "candidates": [
                        {
                            "finishReason": "STOP",
                            "content": {
                                "parts": [{"text": "I am going home."}]
                            },
                        }
                    ]
                }
            )
        ),
    )

    assert (
        llm.generate_text("prompt", source_glosses=["ME", "HOME", "GO"])
        == "I am going home."
    )


def test_generate_text_rejects_unknown_source_gloss(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "unit-test-secret")
    post = Mock()
    monkeypatch.setattr(llm.requests, "post", post)

    assert llm.generate_text("prompt", source_glosses=["UNKNOWN"]) is None
    post.assert_not_called()
