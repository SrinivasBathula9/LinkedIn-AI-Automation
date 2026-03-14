"""
Profile relevance classifier.
Uses sentence-transformer embeddings + scikit-learn LogisticRegression head.
Supports bootstrap training from labeled examples and incremental updates.
"""
from __future__ import annotations
import os
import pickle
import numpy as np
from typing import TypedDict
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import structlog

from backend.ai.embedder import embed_text, profile_to_text

log = structlog.get_logger()
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../models/classifier.pkl")


class ClassificationResult(TypedDict):
    is_relevant: bool
    confidence: float


class ProfileClassifier:
    def __init__(self):
        self._model: LogisticRegression | None = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                self._model = pickle.load(f)
            log.info("Classifier loaded", path=MODEL_PATH)

    def _save_model(self):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self._model, f)

    def predict(self, profile: dict) -> ClassificationResult:
        """Classify a profile. Falls back to rule-based scoring if untrained."""
        if self._model is None:
            return self._rule_based(profile)
        text = profile_to_text(profile)
        vec = np.array(embed_text(text)).reshape(1, -1)
        proba = self._model.predict_proba(vec)[0]
        is_relevant = bool(proba[1] >= 0.5)
        confidence = float(proba[1] if is_relevant else proba[0])
        return {"is_relevant": is_relevant, "confidence": round(confidence, 4)}

    def _rule_based(self, profile: dict) -> ClassificationResult:
        """Bootstrap classifier based on target role keywords."""
        TARGET_KEYWORDS = {
            "ceo", "cto", "coo", "cio", "chief", "vp", "vice president",
            "director", "hr", "recruiter", "talent", "ai", "ml", "machine learning",
            "platform engineer", "cloud", "architect", "consultant",
        }
        title = (profile.get("title") or "").lower()
        headline = (profile.get("headline") or "").lower()
        combined = f"{title} {headline}"
        hits = sum(1 for kw in TARGET_KEYWORDS if kw in combined)
        is_relevant = hits >= 1
        confidence = min(0.5 + hits * 0.1, 0.95) if is_relevant else 0.3
        return {"is_relevant": is_relevant, "confidence": round(confidence, 4)}

    def train(self, profiles: list[dict], labels: list[bool]) -> None:
        """Train or retrain the classifier on labeled profiles."""
        texts = [profile_to_text(p) for p in profiles]
        X = np.array([embed_text(t) for t in texts])
        y = np.array([int(l) for l in labels])
        self._model = LogisticRegression(max_iter=1000, class_weight="balanced", C=1.0)
        self._model.fit(X, y)
        self._save_model()
        log.info("Classifier trained", n_samples=len(labels))


# Module-level singleton
classifier = ProfileClassifier()
