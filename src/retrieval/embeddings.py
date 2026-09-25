from __future__ import annotations

from functools import lru_cache
import hashlib
import math
import os
import re

from langchain_core.embeddings import Embeddings


@lru_cache(maxsize=4)
def _load_model(model_name: str):
    """Load MiniLM lazily so non-retrieval commands do not initialise torch."""
    from sentence_transformers import SentenceTransformer

    allow_download = os.getenv("ALLOW_EMBEDDING_DOWNLOAD", "").lower() in {"1", "true", "yes"}
    return SentenceTransformer(model_name, local_files_only=not allow_download)


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.backend = "sentence-transformers"
        self._load_failed = False

    def _model(self):
        if self.model is not None:
            return self.model
        if self._load_failed:
            return None
        try:
            self.model = _load_model(self.model_name)
        except Exception:
            # Offline mode is a first-class lab requirement. The manifest records
            # this fallback so results are never mistaken for MiniLM results.
            self.backend = "deterministic-hashing-fallback"
            self._load_failed = True
        return self.model

    @staticmethod
    def _fallback_vector(text: str, dimensions: int = 384) -> list[float]:
        values = [0.0] * dimensions
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            slot = int.from_bytes(digest[:4], "big") % dimensions
            values[slot] += 1.0 if digest[4] % 2 else -1.0
        magnitude = math.sqrt(sum(value * value for value in values))
        return [value / magnitude for value in values] if magnitude else values

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        model = self._model()
        if model is None:
            return [self._fallback_vector(text) for text in texts]
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        model = self._model()
        if model is None:
            return self._fallback_vector(text)
        embedding = model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()
