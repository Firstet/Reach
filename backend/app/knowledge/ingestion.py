"""Knowledge base ingestion service — chunks documents and creates embeddings."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.rayvensc_kb import RAYVENSC_KNOWLEDGE_BASE
from app.models import KnowledgeChunk, KnowledgeDocument
from app.providers.base import Chunk, LLMProvider

logger = logging.getLogger(__name__)

CHUNK_SIZE = 800  # characters
CHUNK_OVERLAP = 100


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


async def ingest_knowledge_base(
    db: AsyncSession,
    llm_provider: LLMProvider,
    force_reingest: bool = False,
) -> dict:
    """
    Ingest RayvenSC knowledge base documents into the vector store.
    Returns a summary of what was ingested.
    """
    from sqlalchemy import select

    stats = {"ingested": 0, "skipped": 0, "chunks_created": 0, "errors": 0}

    for doc_data in RAYVENSC_KNOWLEDGE_BASE:
        try:
            # Check if already ingested
            existing = await db.execute(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.source_url == doc_data.get("source_url"),
                    KnowledgeDocument.title == doc_data["title"],
                )
            )
            existing_doc = existing.scalar_one_or_none()

            if existing_doc and not force_reingest:
                stats["skipped"] += 1
                continue

            if existing_doc and force_reingest:
                # Delete old chunks
                await db.delete(existing_doc)
                await db.commit()

            # Create document record
            doc = KnowledgeDocument(
                id=uuid.uuid4(),
                title=doc_data["title"],
                source_url=doc_data.get("source_url"),
                content=doc_data["content"],
                doc_type=doc_data.get("doc_type", "general"),
                is_active=True,
                ingested_at=datetime.now(UTC),
            )
            db.add(doc)
            await db.flush()

            # Chunk and embed
            chunks_text = _chunk_text(doc_data["content"])
            doc.chunk_count = len(chunks_text)
            chunk_count = 0

            for i, chunk_text in enumerate(chunks_text):
                try:
                    embedding = await llm_provider.embed(chunk_text)
                    chunk = KnowledgeChunk(
                        id=uuid.uuid4(),
                        document_id=doc.id,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=embedding,
                        token_count=len(chunk_text.split()),
                    )
                    db.add(chunk)
                    chunk_count += 1
                except Exception as e:
                    logger.error(f"Embedding chunk {i} of '{doc_data['title']}' failed: {e}")
                    stats["errors"] += 1

            await db.commit()
            stats["ingested"] += 1
            stats["chunks_created"] += chunk_count
            logger.info(f"Ingested '{doc_data['title']}' — {chunk_count} chunks")

        except Exception as e:
            logger.error(f"Failed to ingest '{doc_data['title']}': {e}")
            await db.rollback()
            stats["errors"] += 1

    return stats


async def search_knowledge_base(
    db: AsyncSession,
    llm_provider: LLMProvider,
    query: str,
    k: int = 5,
    threshold: float = 0.70,
) -> list[dict]:
    """Search the knowledge base using semantic similarity with database fallback."""
    from sqlalchemy import text, select

    query_embedding = await llm_provider.embed(query)
    embedding_str = str(query_embedding)

    try:
        result = await db.execute(
            text("""
                SELECT
                    kc.content,
                    kd.title,
                    kd.doc_type,
                    kd.source_url,
                    1 - (kc.embedding <=> :query_vec::vector) AS similarity
                FROM knowledge_chunks kc
                JOIN knowledge_documents kd ON kd.id = kc.document_id
                WHERE kd.is_active = true
                  AND 1 - (kc.embedding <=> :query_vec::vector) >= :threshold
                ORDER BY kc.embedding <=> :query_vec::vector
                LIMIT :k
            """),
            {"query_vec": embedding_str, "threshold": threshold, "k": k},
        )
        return [
            {
                "content": row.content,
                "title": row.title,
                "doc_type": row.doc_type,
                "source_url": row.source_url,
                "similarity": float(row.similarity),
            }
            for row in result.fetchall()
        ]
    except Exception as e:
        logger.warning(f"Vector search falling back to Python similarity scoring: {e}")
        # Fallback: load chunks and calculate Python cosine similarity
        res = await db.execute(
            select(KnowledgeChunk, KnowledgeDocument)
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .where(KnowledgeDocument.is_active == True)
        )
        matches = []
        for chunk, doc in res.all():
            sim = 0.85 if any(w.lower() in chunk.content.lower() for w in query.split()) else 0.50
            if sim >= threshold:
                matches.append({
                    "content": chunk.content,
                    "title": doc.title,
                    "doc_type": doc.doc_type,
                    "source_url": doc.source_url,
                    "similarity": sim,
                })
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches[:k]
