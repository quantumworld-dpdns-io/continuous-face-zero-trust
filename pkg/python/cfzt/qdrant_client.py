"""Qdrant vector database client wrapper."""
from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue


class QdrantClientWrapper:
    def __init__(self, url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=url)

    async def ensure_collection(self, name: str, dimension: int = 512, distance: str = "COSINE"):
        collections = self.client.get_collections().collections
        existing = [c.name for c in collections]
        if name not in existing:
            dist = Distance.COSINE if distance == "COSINE" else Distance.EUCLID
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dimension, distance=dist),
            )

    async def upsert(self, collection: str, point_id: int, vector: list[float], payload: dict | None = None):
        self.client.upsert(
            collection_name=collection,
            points=[PointStruct(id=point_id, vector=vector, payload=payload or {})],
        )

    async def search(self, collection: str, query_vector: list[float], top_k: int = 5, filters: dict | None = None):
        query_filter = None
        if filters:
            conditions = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()]
            query_filter = Filter(must=conditions)
        results = self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )
        return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]

    async def delete(self, collection: str, point_ids: list[int]):
        self.client.delete(collection_name=collection, points_selector=point_ids)
