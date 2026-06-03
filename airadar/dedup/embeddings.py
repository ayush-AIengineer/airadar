"""Embedding backends for semantic dedup (Architecture §4.4).

Two interchangeable backends behind one interface, mirroring the enrichment pattern:

- :class:`HashingEmbedder` — deterministic, offline, zero-cost. A hashed bag-of-words
  vector. Good enough to catch near-identical names/one-liners in the skeleton and to
  run dedup with no API key. NOT semantically strong — the real backend replaces it.
- :class:`OpenAIEmbedder` — ``text-embedding-3-small`` (1536-dim), the spec's choice,
  used when an OpenAI key is configured.

Each embedder exposes ``dim`` so the Qdrant collection is created with the matching size.
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol


class Embedder(Protocol):
    dim: int
    name: str

    async def embed(self, text: str) -> list[float]: ...


class HashingEmbedder:
    """Deterministic hashed bag-of-words embedding (offline, no key)."""

    name = "hashing_v1"

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    async def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = [t for t in text.lower().split() if t]
        for tok in tokens:
            h = int.from_bytes(hashlib.md5(tok.encode("utf-8")).digest()[:8], "big")
            idx = h % self.dim
            sign = 1.0 if (h >> 1) & 1 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]


class OpenAIEmbedder:
    """Real semantic embeddings via OpenAI text-embedding-3-small."""

    name = "openai_text_embedding_3_small"
    dim = 1536

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def embed(self, text: str) -> list[float]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self._api_key)
        resp = await client.embeddings.create(
            model="text-embedding-3-small", input=text[:8000]
        )
        return list(resp.data[0].embedding)


def get_embedder(openai_api_key: str = "") -> Embedder:
    if openai_api_key:
        return OpenAIEmbedder(openai_api_key)
    return HashingEmbedder()
