"""Reusable Pydantic schemas for the sentence translation API."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

SupportedLanguage = Literal[
    "en",
    "hi",
    "mr",
    "ta",
    "bn",
    "te",
    "gu",
    "kn",
    "ml",
    "pa",
]

SUPPORTED_LANGUAGES = frozenset(SupportedLanguage.__args__)


def _normalize_language(value: object) -> object:
    """Normalize supported language codes while leaving type errors to Pydantic."""
    if not isinstance(value, str):
        return value

    normalized = value.strip().lower()
    if normalized not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise ValueError(
            f"Unsupported language code '{normalized}'. Choose from: {supported}."
        )
    return normalized


class SentenceRequest(BaseModel):
    """Validated request body for converting ISL glosses to a sentence."""

    glosses: list[str] = Field(
        min_length=1,
        max_length=20,
        description="List of recognized ISL gloss tokens (1 to 20 items)",
    )
    lang: SupportedLanguage = Field(
        default="en",
        description="Target language short code",
    )

    @field_validator("lang", mode="before")
    @classmethod
    def normalize_language(cls, value: object) -> object:
        """Trim and lowercase a language code before Literal validation."""
        return _normalize_language(value)

    @field_validator("glosses")
    @classmethod
    def reject_blank_glosses(cls, value: list[str]) -> list[str]:
        """Reject gloss tokens that contain no non-whitespace characters."""
        if any(not gloss.strip() for gloss in value):
            raise ValueError("Gloss tokens cannot be empty or whitespace-only.")
        return value


class SentenceResponse(BaseModel):
    """Response body returned by the sentence translation API."""

    sentence: str = Field(description="Grammatically natural English sentence")
    translated: str = Field(description="Sentence translated into the target language")
    lang: SupportedLanguage = Field(description="Target language code")
    emergency: bool = Field(description="Whether an emergency phrase was detected")
    audio_url: str | None = Field(
        default=None,
        description="Cloud TTS audio URL or null for browser speech",
    )

    @field_validator("lang", mode="before")
    @classmethod
    def normalize_language(cls, value: object) -> object:
        """Trim and lowercase a language code before Literal validation."""
        return _normalize_language(value)


class TextToGlossRequest(BaseModel):
    """Validated request body for converting text into ISL glosses."""

    text: str = Field(
        ...,
        max_length=200,
        description="Spoken English or hearing user text",
    )


class TextToGlossResponse(BaseModel):
    """Response body returned by the text-to-gloss endpoint."""

    original_text: str = Field(description="Original spoken phrase")
    glosses: list[str] = Field(
        description="Ordered ISL Subject-Object-Verb gloss tokens"
    )
