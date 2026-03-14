"""
Profile classifier training pipeline.

Usage:
    python references/classifier_training.py --data data/labeled_profiles.jsonl

The labeled_profiles.jsonl file should be newline-delimited JSON:
  {"title": "CTO", "company": "Acme", "headline": "...", "label": true}
  {"title": "Sales Rep", "company": "...", "headline": "...", "label": false}
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report
import pickle

from backend.ai.embedder import embed_text, profile_to_text


def load_data(path: str) -> tuple[list[dict], list[bool]]:
    profiles, labels = [], []
    with open(path) as f:
        for line in f:
            row = json.loads(line.strip())
            label = row.pop("label")
            profiles.append(row)
            labels.append(bool(label))
    return profiles, labels


def train(data_path: str, output_path: str = "models/classifier.pkl") -> None:
    print(f"Loading data from {data_path}...")
    profiles, labels = load_data(data_path)
    print(f"Loaded {len(profiles)} samples ({sum(labels)} positive, {len(labels)-sum(labels)} negative)")

    print("Generating embeddings...")
    texts = [profile_to_text(p) for p in profiles]
    X = np.array([embed_text(t) for t in texts])
    y = np.array([int(l) for l in labels])

    print("Training LogisticRegression classifier...")
    clf = LogisticRegression(max_iter=1000, class_weight="balanced", C=1.0, random_state=42)

    # 5-fold cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(clf, X, y, cv=cv, scoring="f1")
    print(f"Cross-val F1: {scores.mean():.3f} ± {scores.std():.3f}")

    # Final fit
    clf.fit(X, y)
    y_pred = clf.predict(X)
    print("\nClassification Report (train set):")
    print(classification_report(y, y_pred, target_names=["Not Relevant", "Relevant"]))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(clf, f)
    print(f"\nModel saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to labeled_profiles.jsonl")
    parser.add_argument("--output", default="models/classifier.pkl", help="Output model path")
    args = parser.parse_args()
    train(args.data, args.output)
