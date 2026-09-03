"""pgvector-based vector store provider."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.base import Chunk, VectorStoreProvider

logger = logging.getLogger(__name__)


class PgVectorProvider:
    """Vector store backed by pgvector extension in PostgreSQL."""

    provider_name = "pgvector"

    def __init__(self, session: AsyncSession, threshold: float = 0.75):
        self._session = session
        self._threshold = threshold

    async def upsert(self, chunks: list[Chunk]) -> None:
        from app.models import KnowledgeChunk

        for chunk in chunks:
            # Use INSERT ... ON CONFLICT DO UPDATE
            stmt = text("""
                INSERT INTO knowledge_chunks (id, document_id, chunk_index, content, embedding, token_count, created_at)
                VALUES (:id, :document_id, :chunk_index, :content, :embedding, :token_count, NOW())
                ON CONFLICT (id) DO UPDATE
                SET content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    token_count = EXCLUDED.token_count
            """)
            meta = chunk.metadata
            await self._session.execute(stmt, {
                "id": chunk.id,
                "document_id": meta.get("document_id"),
                "chunk_index": meta.get("chunk_index", 0),
                "content": chunk.content,
                "embedding": chunk.embedding,
                "token_count": meta.get("token_count"),
            })
        await self._session.commit()

    async def search(
        self,
        query_embedding: list[float],
        k: int = 5,
        threshold: float | None = None,
    ) -> list[Chunk]:
        th = threshold if threshold is not None else self._threshold
        stmt = text("""
            SELECT
                id::text,
                document_id::text,
                chunk_index,
                content,
                embedding,
                1 - (embedding <=> :query_vec::vector) AS similarity
            FROM knowledge_chunks
            WHERE 1 - (embedding <=> :query_vec::vector) >= :threshold
            ORDER BY embedding <=> :query_vec::vector
            LIMIT :k
        """)
        result = await self._session.execute(stmt, {
            "query_vec": str(query_embedding),
            "threshold": th,
            "k": k,
        })
        rows = result.fetchall()
        return [
            Chunk(
                id=str(row.id),
                content=row.content,
                embedding=list(row.embedding) if row.embedding else [],
                metadata={
                    "document_id": str(row.document_id),
                    "chunk_index": row.chunk_index,
                    "similarity": row.similarity,
                },
            )
            for row in rows
        ]

    async def delete(self, chunk_ids: list[str]) -> None:
        from app.models import KnowledgeChunk

        for cid in chunk_ids:
            await self._session.execute(
                delete(KnowledgeChunk).where(KnowledgeChunk.id == uuid.UUID(cid))
            )
        await self._session.commit()

    async def health_check(self) -> bool:
        try:
            await self._session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"pgvector health check failed: {e}")
            return False
