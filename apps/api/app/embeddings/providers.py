import hashlib
import math
from typing import Protocol


class EmbeddingProvider(Protocol):
    provider_name: str
    model_name: str
    dimension: int

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector for each input text."""


class FakeHashEmbeddingProvider:
    """Deterministic local embedding provider for exercising indexing flows."""

    provider_name = "local-hash"
    model_name = "fake-hash-v1"

    def __init__(self, dimension: int = 64) -> None:
        if dimension < 1:
            raise ValueError("Embedding dimension must be at least 1.")
        self.dimension = dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        seed = f"{self.provider_name}:{self.model_name}:{self.dimension}:{text}".encode("utf-8")
        needed_bytes = self.dimension * 4
        digest_bytes = bytearray()
        counter = 0

        while len(digest_bytes) < needed_bytes:
            digest_bytes.extend(hashlib.sha256(seed + counter.to_bytes(4, "big")).digest())
            counter += 1

        values: list[float] = []
        for index in range(self.dimension):
            start = index * 4
            raw = int.from_bytes(digest_bytes[start : start + 4], "big")
            values.append((raw / 0xFFFFFFFF) * 2.0 - 1.0)

        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0:
            return [0.0 for _ in values]
        return [round(value / norm, 8) for value in values]
