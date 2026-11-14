import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from config import get_settings, parse_origins


CONFIG_KEYS = [
    "LLM_API_KEY",
    "LLM_MODEL",
    "BHASHINI_USER_ID",
    "BHASHINI_API_KEY",
    "HF_TOKEN",
    "ALLOWED_ORIGINS",
    "RATE_LIMIT_PER_MIN",
]

def clear_config_environment(monkeypatch):
    """Remove configuration variables to test defaults."""
    for key in CONFIG_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_default_settings(monkeypatch):
    clear_config_environment(monkeypatch)

    settings = get_settings()
    assert settings.allowed_origins == ("http://localhost:3000",)
    assert settings.rate_limit_per_min == 60
    assert settings.llm_api_key == ""
    assert settings.bhashini_api_key == ""
    assert settings.hf_token == ""


def test_parse_multiple_origins():
    result = parse_origins("http://localhost:3000, https://example.com")

    assert result == (
        "http://localhost:3000",
        "https://example.com",
    )


def test_parse_empty_origins():
    assert parse_origins("") == ()


def test_custom_environment_settings(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("BHASHINI_USER_ID", "test-user")
    monkeypatch.setenv("BHASHINI_API_KEY", "test-bhashini")
    monkeypatch.setenv("HF_TOKEN", "test-token")
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,https://example.com",
    )
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "75")

    settings = get_settings()

    assert settings.llm_model == "test-model"
    assert settings.rate_limit_per_min == 75
    assert len(settings.allowed_origins) == 2


@pytest.mark.parametrize("invalid_value", ["abc", "0", "-5"])
def test_invalid_rate_limit(monkeypatch, invalid_value):
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", invalid_value)

    with pytest.raises(ValueError):
        get_settings()
