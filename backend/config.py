"""Centralized environment configuration for the ISL backend."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load environment variables from the repository root.
load_dotenv(PROJECT_ROOT / ".env")


def parse_origins(value: str) -> tuple[str, ...]:
    """Parse comma-separated frontend origins."""
    return tuple(origin.strip() for origin in value.split(",") if origin.strip())


@dataclass(frozen=True)
class Settings:
    """Central configuration for backend services."""

    llm_api_key: str
    llm_model: str
    bhashini_user_id: str
    bhashini_api_key: str
    hf_token: str
    allowed_origins: tuple[str, ...]
    rate_limit_per_min: int


def get_settings() -> Settings:
    """Read configuration from environment variables."""
    raw_limit = os.getenv("RATE_LIMIT_PER_MIN", "60")
    try:
        rate_limit = int(raw_limit)
    except ValueError as exc:
        raise ValueError("RATE_LIMIT_PER_MIN must be an integer") from exc

    if rate_limit < 1:
        raise ValueError("RATE_LIMIT_PER_MIN must be greater than zero")

    return Settings(
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
        bhashini_user_id=os.getenv("BHASHINI_USER_ID", ""),
        bhashini_api_key=os.getenv("BHASHINI_API_KEY", ""),
        hf_token=os.getenv("HF_TOKEN", ""),
        allowed_origins=parse_origins(
            os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        ),
        rate_limit_per_min=rate_limit,
    )


settings = get_settings()
