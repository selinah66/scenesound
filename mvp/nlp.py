"""Local retrieval adapted from Class 2 / Class 3 text-feature demos.

See docs/class_code_reference.md for exact notebook sections and adaptations.
The ranking and application integration are SceneSound additions.
"""

import csv
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def preprocess_text(text: str) -> str:
    """Normalize a retrieval copy, while leaving the original prompt untouched.

    Adapted from Class 2 section 2.2 and Class 3 section 3.1.2.
    Keep digits, apostrophes, and stop words for scene descriptions.
    """
    text = text.lower().replace("’", "'")
    # Replace punctuation with spaces so adjacent words are not joined together.
    text = re.sub(r"[^\w\s']", " ", text)
    return " ".join(text.split())


def load_sound_descriptions(path: str | Path) -> list[dict]:
    """Read the team's small collection of text descriptions."""
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required = {"id", "audio_type", "description"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("CSV needs id, audio_type, and description columns.")
        records = list(reader)
    if not records or any(not row["description"].strip() for row in records):
        raise ValueError("Provide at least one record and no empty descriptions.")
    if len({row["id"] for row in records}) != len(records):
        raise ValueError("Each sound description needs a unique id.")
    return records


def retrieve_examples(
    scene: str, records: list[dict], audio_type: str, top_k: int = 3
) -> list[dict]:
    """Rank text examples by lexical similarity, not by audio quality."""
    if not scene.strip():
        raise ValueError("Please enter a scene description.")
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    candidates = [row for row in records if row["audio_type"] == audio_type]
    if not candidates:
        return []

    # Class 2 section 2.4 / Class 3 section 3.1: fit_transform text with TF-IDF.
    # SceneSound additions: consistent preprocessor, word pairs, audio-type filtering, query transformation, and cosine-similarity ranking.
    vectorizer = TfidfVectorizer(
        preprocessor=preprocess_text,
        lowercase=False,  # preprocess_text already handles lowercasing.
        ngram_range=(1, 2),
        stop_words=None,
    )
    document_vectors = vectorizer.fit_transform(
        row["description"] for row in candidates
    )
    # Fit on the reference collection; transform the new query with that same fit.
    query_vector = vectorizer.transform([scene])
    scores = cosine_similarity(query_vector, document_vectors).ravel()
    ranked = sorted(range(len(candidates)), key=lambda i: scores[i], reverse=True)

    # Do not return arbitrary suggestions when nothing overlaps the vocabulary.
    return [
        {**candidates[i], "score": float(scores[i])}
        for i in ranked
        if scores[i] > 0
    ][:top_k]
