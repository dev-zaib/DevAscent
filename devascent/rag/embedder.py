"""Embedding generation service using OpenAI text-embedding-3-small."""
import hashlib
from typing import Optional
from devascent.config import assessment_config


# In-memory cache to avoid re-embedding identical text
_embedding_cache: dict[str, list[float]] = {}


def _cache_key(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def generate_embedding(text: str) -> Optional[list[float]]:
    """Generate a vector embedding for text using OpenAI.

    Returns 1536-dimensional vector. Falls back to None if no API key.
    Results are cached in-memory by content hash.
    """
    key = _cache_key(text)
    if key in _embedding_cache:
        return _embedding_cache[key]

    api_key = assessment_config.openai_api_key
    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model=assessment_config.embedding_model,
            input=text,
        )
        embedding = response.data[0].embedding
        _embedding_cache[key] = embedding
        return embedding
    except Exception:
        return None


def generate_challenge_embedding(challenge: dict) -> Optional[list[float]]:
    """Generate embedding for a challenge by concatenating key fields."""
    text_parts = [
        challenge.get("title", ""),
        challenge.get("description", ""),
        ", ".join(challenge.get("target_skills", [])),
        challenge.get("target_level", ""),
        challenge.get("difficulty", ""),
    ]
    combined = " | ".join(filter(None, text_parts))
    return generate_embedding(combined)


def generate_weak_spot_embedding(weak_skills: list[str]) -> Optional[list[float]]:
    """Generate embedding for user's weak skill areas.

    Combines skill names with domain context to create a query vector
    that matches challenges targeting those skills.
    """
    if not weak_skills:
        return None

    text = "Engineering challenge for: " + ", ".join(weak_skills)
    return generate_embedding(text)
