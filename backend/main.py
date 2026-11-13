"""
ISL Translator - FastAPI Backend Application
Implements Integration Contract 7.2:
- GET /health
- POST /api/sentence
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .gloss_to_text import glosses_to_sentence
from .schemas import SentenceRequest, SentenceResponse
from .translate import translate_text
from .tts import get_speech_audio
from .vocabulary import VocabularyValidationError, validate_glosses

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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
    """Service health probe endpoint."""
    return {"status": "ok"}


@app.post("/api/sentence", response_model=SentenceResponse, tags=["Translation"])
async def process_sentence(payload: SentenceRequest) -> SentenceResponse | JSONResponse:
    """
    Transforms an ISL gloss sequence into natural English, performs target language translation,
    and returns speech parameters per Contract 7.2.
    """
    try:
        glosses = validate_glosses(payload.glosses)
    except VocabularyValidationError as exc:
        return JSONResponse(status_code=400, content={"message": str(exc)})

    target_lang = payload.lang

    # Log gloss count and target language safely (NEVER log sensitive biometric data or video)
    logger.info(f"Processing request: {len(glosses)} glosses -> '{target_lang}'")

    # 1. Convert Glosses to Natural English
    sentence, is_emergency = glosses_to_sentence(glosses)

    # 2. Translate sentence to target language
    translated = translate_text(sentence, target_lang)

    # 3. Resolve TTS audio URL
    audio_url = get_speech_audio(translated, target_lang)

    return SentenceResponse(
        sentence=sentence,
        translated=translated,
        lang=target_lang,
        emergency=is_emergency,
        audio_url=audio_url
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
