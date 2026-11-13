"""
ISL Translator - FastAPI Backend Application
Implements Integration Contract 7.2:
- GET /health
- POST /api/sentence
"""

import os
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

from config import settings
from gloss_to_text import glosses_to_sentence
from translate import translate_text
from tts import get_speech_audio

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

# Load classes.json for validation
CLASSES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "classes.json")
VALID_CLASSES = set()
if os.path.exists(CLASSES_PATH):
    try:
        with open(CLASSES_PATH, "r") as f:
            meta = json.load(f)
            VALID_CLASSES = set(meta.get("classes", []))
    except Exception as e:
        logger.warning(f"Could not load classes.json from {CLASSES_PATH}: {e}")

SUPPORTED_LANGUAGES = {"en", "hi", "mr", "ta", "bn", "te", "gu", "kn", "ml", "pa"}


class SentenceRequest(BaseModel):
    glosses: List[str] = Field(..., max_items=20, description="List of recognized ISL gloss tokens (up to 20)")
    lang: str = Field(default="en", description="Target language short code (en, hi, mr, etc.)")

    @validator("lang")
    def validate_language(cls, v):
        v = v.lower().strip()
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Language '{v}' is not supported. Choose from {sorted(list(SUPPORTED_LANGUAGES))}")
        return v

    @validator("glosses")
    def validate_gloss_tokens(cls, v):
        if not v:
            raise ValueError("Glosses list cannot be empty.")
        if len(v) > 20:
            raise ValueError("Cannot process more than 20 glosses in a single sequence.")
        return v


class SentenceResponse(BaseModel):
    sentence: str = Field(..., description="Grammatically natural English sentence")
    translated: str = Field(..., description="Sentence translated into target language")
    lang: str = Field(..., description="Target language code")
    emergency: bool = Field(..., description="Emergency safety flag (True if emergency detected)")
    audio_url: Optional[str] = Field(default=None, description="Cloud TTS audio URL or null for browser speech")


@app.get("/health", tags=["Health"])
async def health_check():
    """Service health probe endpoint."""
    return {"status": "ok"}


@app.post("/api/sentence", response_model=SentenceResponse, tags=["Translation"])
async def process_sentence(payload: SentenceRequest):
    """
    Transforms an ISL gloss sequence into natural English, performs target language translation,
    and returns speech parameters per Contract 7.2.
    """
    glosses = payload.glosses
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
