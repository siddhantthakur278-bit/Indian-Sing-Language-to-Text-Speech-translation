"""Small REST adapter for Google's Gemini text-generation API."""

import logging
import os
import re
from collections.abc import Sequence
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_GEMINI_MODEL = "gemini-flash-lite-latest"
REQUEST_TIMEOUT_SECONDS = 10
MAX_OUTPUT_CHARACTERS = 500
_MODEL_PATTERN = re.compile(r"[A-Za-z0-9._-]+\Z")
_OUTPUT_WORD_PATTERN = re.compile(r"[a-z]+(?:'[a-z]+)?")

# The LLM may add grammar, but content words must be licensed by an input gloss.
_FUNCTION_WORDS = frozenset(
    {
        "a", "an", "and", "am", "are", "as", "at", "be", "been", "being",
        "but", "by", "can", "could", "did", "do", "does", "for", "from",
        "had", "has", "have", "he", "her", "here", "him", "his", "how",
        "i", "if", "in", "into", "is", "it", "its", "may", "me", "might",
        "must", "my", "no", "not", "of", "on", "or", "our", "please",
        "shall", "she", "should", "so", "than", "that", "the", "their",
        "them", "then", "there", "these", "they", "this", "those", "through",
        "to", "under", "us", "was", "we", "were", "what", "when", "where",
        "which", "who", "whom", "why", "will", "with", "would", "you", "your",
    }
)
_CONTENT_WORDS_BY_GLOSS: dict[str, frozenset[str]] = {
    "HELLO": frozenset({"hello", "hi"}),
    "THANK_YOU": frozenset({"thank", "thanks"}),
    "SORRY": frozenset({"sorry"}),
    "PLEASE": frozenset({"please"}),
    "WELCOME": frozenset({"welcome"}),
    "GOODBYE": frozenset({"goodbye", "bye"}),
    "ME": frozenset({"i", "me", "my", "mine"}),
    "YOU": frozenset({"you", "your", "yours"}),
    "HE_SHE": frozenset({"he", "she", "him", "her", "his"}),
    "WE": frozenset({"we", "us", "our", "ours"}),
    "MOTHER": frozenset({"mother", "mom"}),
    "FATHER": frozenset({"father", "dad"}),
    "FRIEND": frozenset({"friend"}),
    "DOCTOR": frozenset({"doctor"}),
    "TEACHER": frozenset({"teacher"}),
    "POLICE": frozenset({"police"}),
    "HELP": frozenset({"help"}),
    "PAIN": frozenset({"pain"}),
    "HOSPITAL": frozenset({"hospital"}),
    "FIRE": frozenset({"fire"}),
    "MEDICINE": frozenset({"medicine", "medication"}),
    "WATER": frozenset({"water"}),
    "ACCIDENT": frozenset({"accident"}),
    "AMBULANCE": frozenset({"ambulance"}),
    "EMERGENCY": frozenset({"emergency"}),
    "DANGER": frozenset({"danger"}),
    "FOOD": frozenset({"food"}),
    "EAT": frozenset({"eat", "eats", "ate", "eating"}),
    "DRINK": frozenset({"drink", "drinks", "drank", "drinking"}),
    "TOILET": frozenset({"toilet", "washroom"}),
    "MONEY": frozenset({"money"}),
    "HOME": frozenset({"home", "house"}),
    "SCHOOL": frozenset({"school"}),
    "MARKET": frozenset({"market"}),
    "WORK": frozenset({"work", "working"}),
    "SLEEP": frozenset({"sleep", "sleeping"}),
    "CLOTHES": frozenset({"clothes"}),
    "TIME": frozenset({"time"}),
    "GO": frozenset({"go", "goes", "went", "going"}),
    "COME": frozenset({"come", "comes", "came", "coming"}),
    "WANT": frozenset({"want", "wants", "wanted"}),
    "NEED": frozenset({"need", "needs", "needed"}),
    "KNOW": frozenset({"know", "knows", "knew", "known"}),
    "UNDERSTAND": frozenset({"understand", "understands", "understood"}),
    "STOP": frozenset({"stop", "stops", "stopped", "stopping"}),
    "WAIT": frozenset({"wait", "waits", "waited", "waiting"}),
    "CALL": frozenset({"call", "calls", "called", "calling"}),
    "SEE": frozenset({"see", "sees", "saw", "seen"}),
    "HEAR": frozenset({"hear", "hears", "heard"}),
    "SPEAK": frozenset({"speak", "speaks", "spoke", "spoken"}),
    "WRITE": frozenset({"write", "writes", "wrote", "written"}),
    "MEET": frozenset({"meet", "meets", "met", "meeting"}),
    "BUY": frozenset({"buy", "buys", "bought", "buying"}),
    "WHAT": frozenset({"what"}),
    "WHERE": frozenset({"where"}),
    "WHEN": frozenset({"when"}),
    "WHO": frozenset({"who"}),
    "WHY": frozenset({"why"}),
    "HOW": frozenset({"how"}),
    "ONE": frozenset({"one"}),
    "TWO": frozenset({"two"}),
    "THREE": frozenset({"three"}),
    "FOUR": frozenset({"four"}),
    "FIVE": frozenset({"five"}),
    "SIX": frozenset({"six"}),
    "SEVEN": frozenset({"seven"}),
    "EIGHT": frozenset({"eight"}),
    "NINE": frozenset({"nine"}),
    "TEN": frozenset({"ten"}),
}


def _supported_output_words(source_glosses: Sequence[str]) -> set[str] | None:
    """Return allowed words, or None if any source gloss lacks grounding data."""
    gloss_words = [gloss.strip().upper() for gloss in source_glosses]
    if not gloss_words or any(gloss not in _CONTENT_WORDS_BY_GLOSS for gloss in gloss_words):
        return None

    supported_words = set(_FUNCTION_WORDS)
    for gloss in gloss_words:
        supported_words.update(_CONTENT_WORDS_BY_GLOSS[gloss])
    return supported_words


def is_grounded_output(text: str, source_glosses: Sequence[str]) -> bool:
    """Reject candidate content words not supported by any source gloss."""
    supported_words = _supported_output_words(source_glosses)
    if supported_words is None:
        return False
    output_words = _OUTPUT_WORD_PATTERN.findall(text.casefold())
    return bool(output_words) and all(word in supported_words for word in output_words)


def is_configured() -> bool:
    """Report whether a key and valid model are configured, without exposing them."""
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip() or DEFAULT_GEMINI_MODEL
    return bool(api_key and _MODEL_PATTERN.fullmatch(model))


def generate_text(
    prompt: str, *, source_glosses: Sequence[str]
) -> str | None:
    """Generate one text candidate, returning None when unavailable or invalid."""
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if (
        not api_key
        or not prompt.strip()
        or _supported_output_words(source_glosses) is None
    ):
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
    if (
        not text
        or len(text) > MAX_OUTPUT_CHARACTERS
        or "\n" in text
        or not is_grounded_output(text, source_glosses)
    ):
        logger.warning("Gemini candidate failed output validation; using fallback")
        return None
    return text
