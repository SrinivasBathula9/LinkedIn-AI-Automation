"""
Sentence-transformer embeddings (all-MiniLM-L6-v2, 384 dims).
Singleton pattern — model loaded once at startup.
"""
from __future__ import annotations
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.config import settings

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_text(text: str) -> list[float]:
    """Return a 384-dim embedding for a single text string."""
    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Batch embed multiple texts."""
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    return vectors.tolist()


def profile_to_text(profile: dict) -> str:
    """Concatenate profile fields into a single text for embedding."""
    parts = [
        profile.get("title", ""),
        profile.get("company", ""),
        profile.get("headline", ""),
        profile.get("summary", ""),
        profile.get("location", ""),
    ]
    return " | ".join(p for p in parts if p)
