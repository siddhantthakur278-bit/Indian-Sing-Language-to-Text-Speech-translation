"""
ISL Translator - FastAPI Backend Application
Implements Integration Contract 7.2:
- GET /health
- POST /api/sentence
"""

import logging
import math
import time
from collections import deque
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from .cache import ResponseCache
from .config import settings
from .gloss_to_text import glosses_to_sentence, sentence_to_glosses
from .llm import is_configured as is_gemini_configured
from .schemas import (
    SentenceRequest,
    SentenceResponse,
    TextToGlossRequest,
    TextToGlossResponse,
)
from .translate import TRANSLATION_MODE, TranslationProviderError, translate_text
from .tts import get_speech_audio, get_tts_status, synthesize_audio_bytes
from .vocabulary import VocabularyValidationError, validate_glosses

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW_SECONDS = 60.0
MAX_TRACKED_CLIENTS = 10_000


class ClientRateLimiter:
    """Enforce a bounded, per-client sliding-window request limit."""

    def __init__(self, max_clients: int = MAX_TRACKED_CLIENTS) -> None:
        if max_clients < 1:
            raise ValueError("max_clients must be greater than zero")
        self._max_clients = max_clients
        self._requests: dict[str, deque[float]] = {}
        self._lock = Lock()

    def _remove_expired(self, now: float) -> None:
        cutoff = now - RATE_LIMIT_WINDOW_SECONDS
        expired_clients = []
        for client_id, timestamps in self._requests.items():
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if not timestamps:
                expired_clients.append(client_id)
        for client_id in expired_clients:
            del self._requests[client_id]

    def try_acquire(
        self, client_id: str, limit: int, *, now: float | None = None
    ) -> int | None:
        """Consume quota or return the seconds until this client can retry."""
        if limit < 1:
            raise ValueError("limit must be greater than zero")

        current_time = time.monotonic() if now is None else now
        cutoff = current_time - RATE_LIMIT_WINDOW_SECONDS
        with self._lock:
            timestamps = self._requests.get(client_id)
            if timestamps is not None:
                while timestamps and timestamps[0] <= cutoff:
                    timestamps.popleft()
                if not timestamps:
                    del self._requests[client_id]
                    timestamps = None

            if timestamps is None:
                if len(self._requests) >= self._max_clients:
                    self._remove_expired(current_time)
                if len(self._requests) >= self._max_clients:
                    oldest_expiry = min(
                        entries[0] + RATE_LIMIT_WINDOW_SECONDS
                        for entries in self._requests.values()
                    )
                    return max(1, math.ceil(oldest_expiry - current_time))
                timestamps = deque()
                self._requests[client_id] = timestamps

            if len(timestamps) >= limit:
                return max(
                    1,
                    math.ceil(
                        timestamps[0] + RATE_LIMIT_WINDOW_SECONDS - current_time
                    ),
                )

            timestamps.append(current_time)
            return None

    def allow_request(
        self, client_id: str, limit: int, *, now: float | None = None
    ) -> bool:
        """Record a request if this client has remaining quota in the window."""
        return self.try_acquire(client_id, limit, now=now) is None

    def clear(self) -> None:
        """Clear tracked request history."""
        with self._lock:
            self._requests.clear()


rate_limiter = ClientRateLimiter()
response_cache = ResponseCache()


def _rate_limit_response(request: Request) -> JSONResponse | None:
    """Return a 429 response when the direct client peer has exceeded its limit."""
    client_id = request.client.host if request.client else "unknown"
    limit = settings.rate_limit_per_min
    retry_after = rate_limiter.try_acquire(client_id, limit)
    if retry_after is not None:
        return JSONResponse(
            status_code=429,
            content={
                "message": (
                    "Rate limit exceeded. "
                    f"Maximum {limit} requests per minute."
                )
            },
            headers={"Retry-After": str(retry_after)},
        )
    return None


app = FastAPI(
    title="Indian Sign Language Translation API",
    description="Backend service translating ISL gloss sequences into natural sentences, multilingual translations, and speech.",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
async def health_check():
    """Report service liveness and configured backend feature modes."""
    return {
        "status": "ok",
        "features": {
            "gloss_to_sentence": (
                "rules_with_gemini"
                if is_gemini_configured()
                else "rules_only"
            ),
            "translation": TRANSLATION_MODE,
            "tts": get_tts_status(),
        },
    }


@app.post("/api/sentence", response_model=SentenceResponse, tags=["Translation"])
async def process_sentence(
    payload: SentenceRequest, request: Request
) -> SentenceResponse | JSONResponse:
    """
    Transforms an ISL gloss sequence into natural English, performs target language translation,
    and returns speech parameters per Contract 7.2.
    """
    rate_limit_error = _rate_limit_response(request)
    if rate_limit_error is not None:
        return rate_limit_error

    try:
        glosses = validate_glosses(payload.glosses)
    except VocabularyValidationError as exc:
        return JSONResponse(status_code=400, content={"message": str(exc)})

    target_lang = payload.lang
    cache_key = (tuple(glosses), target_lang)
    cached_response = response_cache.get(cache_key)
    if cached_response is not None:
        return SentenceResponse.model_validate(cached_response)

    # Log gloss count and target language safely (NEVER log sensitive biometric data or video)
    logger.info(f"Processing request: {len(glosses)} glosses -> '{target_lang}'")

    # 1. Convert Glosses to Natural English
    sentence, is_emergency = glosses_to_sentence(glosses)

    # 2. Translate sentence to target language
    try:
        translated = translate_text(sentence, target_lang)
    except TranslationProviderError as exc:
        logger.error(
            "Translation provider failed (%s)",
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=502,
            content={"message": "Translation service is unavailable."},
        )

    # 3. Resolve TTS audio URL
    audio_url = get_speech_audio(translated, target_lang)

    response = SentenceResponse(
        sentence=sentence,
        translated=translated,
        lang=target_lang,
        emergency=is_emergency,
        audio_url=audio_url
    )
    response_cache.put(cache_key, response.model_dump())
    return response


@app.get("/api/tts", tags=["TTS"])
async def stream_tts_audio(text: str, lang: str = "hi"):
    """Stream speech audio bytes for Indian languages."""
    audio_bytes = synthesize_audio_bytes(text, lang)
    if not audio_bytes:
        return JSONResponse(status_code=502, content={"message": "Failed to synthesize speech audio"})
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.post(
    "/api/text-to-gloss",
    response_model=TextToGlossResponse,
    tags=["Two-Way Mode"],
)
async def convert_text_to_gloss(
    payload: TextToGlossRequest, request: Request
) -> TextToGlossResponse | JSONResponse:
    """Convert hearing-user text into an ISL gloss sequence."""
    rate_limit_error = _rate_limit_response(request)
    if rate_limit_error is not None:
        return rate_limit_error

    text = payload.text
    glosses = sentence_to_glosses(text)
    return TextToGlossResponse(original_text=text, glosses=glosses)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
