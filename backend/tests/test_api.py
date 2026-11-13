"""
API Integration and Endpoint Contract Tests
"""

import pytest

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


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
