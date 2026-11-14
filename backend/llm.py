"""Small REST adapter for Google's Gemini text-generation API."""

import logging
import os
import re
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
REQUEST_TIMEOUT_SECONDS = 10
MAX_OUTPUT_CHARACTERS = 500
_MODEL_PATTERN = re.compile(r"[A-Za-z0-9._-]+\Z")


def is_configured() -> bool:
    """Report whether a key and valid model are configured, without exposing them."""
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip() or DEFAULT_GEMINI_MODEL
    return bool(api_key and _MODEL_PATTERN.fullmatch(model))


def generate_text(prompt: str) -> str | None:
    """Generate one text candidate, returning None when unavailable or invalid."""
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key or not prompt.strip():
        return None

    model = os.getenv("LLM_MODEL", "").strip() or DEFAULT_GEMINI_MODEL
    if not _MODEL_PATTERN.fullmatch(model):
        logger.warning("Gemini model name is invalid; using deterministic fallback")
        return None

    url = f"{GEMINI_API_BASE_URL}/{quote(model, safe='')}:generateContent"
    try:
        response = requests.post(
            url,
            headers={"x-goog-api-key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "candidateCount": 1,
                    "temperature": 0.0,
                    "maxOutputTokens": 128,
                },
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.warning(
            "Gemini request failed (%s); using deterministic fallback",
            type(exc).__name__,
        )
        return None

    if not response.ok:
        logger.warning(
            "Gemini returned HTTP %s; using deterministic fallback",
            response.status_code,
        )
        return None

    try:
        data = response.json()
    except ValueError:
        logger.warning("Gemini returned invalid JSON; using deterministic fallback")
        return None

    candidates = data.get("candidates") if isinstance(data, dict) else None
    if not isinstance(candidates, list) or not candidates:
        logger.warning("Gemini returned no candidate; using deterministic fallback")
        return None

    candidate = candidates[0]
    if not isinstance(candidate, dict) or candidate.get("finishReason") not in (
        None,
        "STOP",
    ):
        logger.warning("Gemini candidate was blocked or incomplete; using fallback")
        return None

    content = candidate.get("content")
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list):
        logger.warning("Gemini candidate had no text parts; using fallback")
        return None

    text = " ".join(
        part["text"].strip()
        for part in parts
        if isinstance(part, dict) and isinstance(part.get("text"), str)
    ).strip()
    if not text or len(text) > MAX_OUTPUT_CHARACTERS or "\n" in text:
        logger.warning("Gemini candidate failed output validation; using fallback")
        return None
    return text
