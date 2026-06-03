"""Qdrant wrapper for semantic dedup (Architecture §4.4 / §7.2).

Phase 2 runs Qdrant in **local on-disk mode** (``QdrantClient(path=...)``) so it needs no
Docker and no server — the same client API swaps to a hosted Qdrant URL in prod by
changing one setting. Stores one point per canonical tool, payload ``{tool_id, name,
first_seen_at}``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from qdrant_client import AsyncQdrantClient, models

COLLECTION = "tool_embeddings"


class DedupIndex:
    def __init__(self, path: str, dim: int) -> None:
        self._client = AsyncQdrantClient(path=path)
        self._dim = dim

    async def ensure_collection(self) -> None:
        exists = await self._client.collection_exists(COLLECTION)
        if not exists:
            await self._client.create_collection(
                collection_name=COLLECTION,
                vectors_config=models.VectorParams(
                    size=self._dim, distance=models.Distance.COSINE
                ),
            )

    async def nearest(
        self, vector: list[float], lookback_days: int
    ) -> tuple[uuid.UUID, float] | None:
        """Return (tool_id, score) of the most similar recent point, or None."""
        since = datetime.now(UTC) - timedelta(days=lookback_days)
        hits = await self._client.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=1,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="first_seen_ts",
                        range=models.Range(gte=since.timestamp()),
                    )
                ]
            ),
        )
        points = hits.points
        if not points:
            return None
        top = points[0]
        if not top.payload or "tool_id" not in top.payload:
            return None
        return uuid.UUID(str(top.payload["tool_id"])), float(top.score)

    async def upsert(
        self, tool_id: uuid.UUID, vector: list[float], name: str, first_seen: datetime
    ) -> None:
        await self._client.upsert(
            collection_name=COLLECTION,
            points=[
                models.PointStruct(
                    id=str(tool_id),
                    vector=vector,
                    payload={
                        "tool_id": str(tool_id),
                        "name": name,
                        "first_seen_ts": first_seen.timestamp(),
                    },
                )
            ],
        )

    async def close(self) -> None:
        await self._client.close()
