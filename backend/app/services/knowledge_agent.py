"""
Rayven Knowledge Agent Service
Provides RAG retrieval with explicit source citations, Knowledge Document CRUD,
PDF/Text/MD file parsing, rule categorization, and RayvenSC positioning enforcement.
"""

from __future__ import annotations

import io
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import KnowledgeChunk, KnowledgeDocument
from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeSearchResult:
    content: str
    title: str
    source_url: str | None
    doc_type: str
    doc_category: str
    similarity: float
    citation: str


class RayvenKnowledgeAgent:
    """RAG search with source citations, document ingestion, and rules management."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def search_with_citations(
        self,
        llm: LLMProvider,
        query: str,
        k: int = 5,
        threshold: float = 0.65,
        category_filter: str | None = None,
    ) -> list[KnowledgeSearchResult]:
        """Perform RAG vector search and return chunks with explicit source citations."""
        from app.knowledge.ingestion import search_knowledge_base

        raw_chunks = await search_knowledge_base(
            self._db, llm, query=query, k=k, threshold=threshold
        )

        results: list[KnowledgeSearchResult] = []
        for c in raw_chunks:
            # Fetch document category if needed
            doc_id = c.get("document_id")
            doc = await self._db.get(KnowledgeDocument, uuid.UUID(doc_id)) if doc_id else None

            cat = doc.doc_category if doc else "document"
            if category_filter and cat != category_filter:
                continue

            title = c.get("title") or (doc.title if doc else "Rayven Knowledge Base")
            url = doc.source_url if doc else None
            similarity = c.get("similarity", 0.8)

            citation = f"[Source: {title}"
            if url:
                citation += f" ({url})"
            citation += "]"

            results.append(KnowledgeSearchResult(
                content=c.get("content", ""),
                title=title,
                source_url=url,
                doc_type=doc.doc_type if doc else "document",
                doc_category=cat,
                similarity=similarity,
                citation=citation,
            ))

        return results

    async def add_knowledge_item(
        self,
        title: str,
        content: str,
        doc_category: str = "document",  # document | faq | messaging_rule | pricing_rule | prohibited_claim | case_study
        doc_type: str = "manual",
        source_url: str | None = None,
        llm: LLMProvider | None = None,
    ) -> KnowledgeDocument:
        """Add a new knowledge document or rule to the KB and index it immediately."""
        from app.knowledge.ingestion import chunk_text

        doc = KnowledgeDocument(
            id=uuid.uuid4(),
            title=title.strip(),
            content=content.strip(),
            doc_type=doc_type,
            doc_category=doc_category,
            source_url=source_url,
            is_active=True,
            ingested_at=datetime.now(UTC),
        )
        self._db.add(doc)
        await self._db.flush()

        # Chunk and embed
        chunks = chunk_text(content, chunk_size=500, overlap=50)
        chunk_objects = []

        for idx, chunk_text_val in enumerate(chunks):
            embedding = await llm.embed(chunk_text_val) if llm else None
            k_chunk = KnowledgeChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_text_val,
                embedding=embedding,
                token_count=len(chunk_text_val.split()),
            )
            chunk_objects.append(k_chunk)
            self._db.add(k_chunk)

        doc.chunk_count = len(chunk_objects)
        await self._db.commit()
        await self._db.refresh(doc)
        logger.info(f"Added Knowledge item: '{title}' ({doc_category}) with {doc.chunk_count} chunks")
        return doc

    async def ingest_file(
        self,
        filename: str,
        file_bytes: bytes,
        doc_category: str = "document",
        llm: LLMProvider | None = None,
    ) -> KnowledgeDocument:
        """Parse and ingest a PDF, TXT, or MD file."""
        text_content = ""

        if filename.lower().endswith(".pdf"):
            # Simple PDF text extraction fallback
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                pages_text = [p.extract_text() for p in reader.pages if p.extract_text()]
                text_content = "\n\n".join(pages_text)
            except Exception as e:
                logger.warning(f"pypdf extraction failed for {filename}: {e}, using string decoder")
                text_content = file_bytes.decode("utf-8", errors="ignore")
        else:
            text_content = file_bytes.decode("utf-8", errors="ignore")

        # Clean text
        text_content = re.sub(r"\n{3,}", "\n\n", text_content).strip()
        if not text_content:
            raise ValueError(f"No extractable text found in file {filename}")

        return await self.add_knowledge_item(
            title=f"Uploaded File: {filename}",
            content=text_content,
            doc_category=doc_category,
            doc_type="pdf" if filename.lower().endswith(".pdf") else "document",
            llm=llm,
        )

    async def get_all_rules_of_category(self, doc_category: str) -> list[str]:
        """Fetch content of all active rules in a specific category (e.g. prohibited_claim)."""
        stmt = select(KnowledgeDocument.content).where(
            KnowledgeDocument.doc_category == doc_category,
            KnowledgeDocument.is_active == True,
        )
        res = await self._db.execute(stmt)
        return [r for r in res.scalars().all()]
