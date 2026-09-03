"""Knowledge Management API Router (Phase 3)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import KnowledgeDocument, User
from app.providers.registry import get_llm_provider
from app.services.knowledge_agent import RayvenKnowledgeAgent

router = APIRouter(prefix="/knowledge-mgmt", tags=["knowledge_management"])


class RuleCreateRequest(BaseModel):
    title: str
    content: str
    doc_category: str = "document"  # document | faq | messaging_rule | pricing_rule | prohibited_claim | case_study
    source_url: str | None = None


@router.post("/upload", status_code=201)
async def upload_document_file(
    file: UploadFile = File(...),
    doc_category: str = Form("document"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF, TXT, or MD document into the Knowledge Base."""
    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    agent = RayvenKnowledgeAgent(db)
    llm = get_llm_provider()

    try:
        doc = await agent.ingest_file(
            filename=file.filename or "uploaded_doc",
            file_bytes=content_bytes,
            doc_category=doc_category,
            llm=llm,
        )
        return {
            "id": str(doc.id),
            "title": doc.title,
            "doc_category": doc.doc_category,
            "chunk_count": doc.chunk_count,
            "ingested_at": doc.ingested_at.isoformat() if doc.ingested_at else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File ingestion failed: {e}")


@router.post("/rules", status_code=201)
async def add_faq_or_rule(
    body: RuleCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add FAQ, approved answer, messaging rule, or prohibited claim."""
    agent = RayvenKnowledgeAgent(db)
    llm = get_llm_provider()

    doc = await agent.add_knowledge_item(
        title=body.title,
        content=body.content,
        doc_category=body.doc_category,
        source_url=body.source_url,
        llm=llm,
    )
    return {
        "id": str(doc.id),
        "title": doc.title,
        "doc_category": doc.doc_category,
        "chunk_count": doc.chunk_count,
    }


@router.post("/crawl-site")
async def crawl_rayvensc_website(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-crawl rayvensc.com website content and update Knowledge Base."""
    from app.knowledge.ingestion import ingest_knowledge_base
    llm = get_llm_provider()
    stats = await ingest_knowledge_base(db, llm, force_reingest=True)
    return {"status": "completed", "stats": stats}


@router.post("/reindex")
async def reindex_knowledge_base(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-generate embeddings for all knowledge chunks."""
    from app.knowledge.ingestion import ingest_knowledge_base
    llm = get_llm_provider()
    stats = await ingest_knowledge_base(db, llm, force_reingest=True)
    return {"status": "reindexed", "stats": stats}


@router.delete("/documents/{doc_id}")
async def delete_knowledge_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.delete(doc)
    await db.commit()
    return {"deleted": True, "id": str(doc_id)}
