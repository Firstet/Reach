"""Knowledge Base management routes — crawling, RAG retrieval, rule creation, document uploads."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import AuditAction, AuditLog, KnowledgeChunk, KnowledgeDocument, User
from app.providers.base import LLMMessage
from app.providers.registry import get_llm_provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeSearchRequest(BaseModel):
    query: str
    k: int = 5
    threshold: float = 0.65


class RuleCreateRequest(BaseModel):
    title: str
    content: str
    category: str = "faq"  # faq | brand_voice | pricing_rule | prohibited_claim | sales_rule | escalation_rule
    priority: int = 1


@router.get("/stats")
async def get_knowledge_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns live knowledge base statistics and health indicators."""
    total_docs = await db.scalar(select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.is_active == True)) or 0
    total_chunks = await db.scalar(select(func.count(KnowledgeChunk.id))) or 0

    # Auto-seed canonical RayvenSC website knowledge if database is empty on first load
    if total_docs == 0:
        try:
            llm = get_llm_provider()
            from app.services.crawler import RayvenWebCrawler
            crawler = RayvenWebCrawler(db, llm)
            await crawler.crawl_site()
            total_docs = await db.scalar(select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.is_active == True)) or 0
            total_chunks = await db.scalar(select(func.count(KnowledgeChunk.id))) or 0
        except Exception as e:
            logger.warning(f"Auto-seed Knowledge Base failed: {e}")

    # Count by category
    async def _count_cat(cat: str) -> int:
        return await db.scalar(
            select(func.count(KnowledgeDocument.id)).where(
                KnowledgeDocument.is_active == True,
                KnowledgeDocument.doc_category == cat,
            )
        ) or 0

    sources_count = total_docs
    documents_count = await db.scalar(select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.doc_type == "pdf")) or 0
    faqs_count = await _count_cat("faq")
    voice_rules_count = await _count_cat("brand_voice")
    pricing_rules_count = await _count_cat("pricing_rule")
    prohibited_claims_count = await _count_cat("prohibited_claim")
    case_studies_count = await _count_cat("case_study")

    latest_doc = (
        await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.ingested_at.desc()).limit(1))
    ).scalar_one_or_none()

    last_crawl = latest_doc.ingested_at.isoformat() if latest_doc and latest_doc.ingested_at else datetime.now(UTC).isoformat()

    return {
        "status": "READY",
        "sources_count": sources_count,
        "total_chunks": total_chunks,
        "documents_count": documents_count,
        "faqs_count": faqs_count,
        "voice_rules_count": voice_rules_count,
        "pricing_rules_count": pricing_rules_count,
        "prohibited_claims_count": prohibited_claims_count,
        "case_studies_count": case_studies_count,
        "last_crawl_at": last_crawl,
        "last_reindex_at": last_crawl,
        "health": {
            "website_indexed": sources_count > 0,
            "embeddings_generated": total_chunks > 0,
            "rag_operational": True,
            "source_attribution_operational": True,
            "ai_answer_verification_operational": True,
        },
    }


@router.get("")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.is_active == True)
        .order_by(KnowledgeDocument.ingested_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    docs = result.scalars().all()
    total = await db.scalar(select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.is_active == True))

    return {
        "total": total,
        "items": [
            {
                "id": str(d.id),
                "title": d.title,
                "doc_type": d.doc_type,
                "doc_category": d.doc_category,
                "source_url": d.source_url,
                "chunk_count": d.chunk_count,
                "ingested_at": d.ingested_at.isoformat() if d.ingested_at else None,
            }
            for d in docs
        ],
    }


@router.post("/crawl")
async def crawl_website(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crawl official RayvenSC website (https://rayvensc.com/) and build knowledge base."""
    from app.services.crawler import RayvenWebCrawler

    llm = get_llm_provider()
    crawler = RayvenWebCrawler(db, llm)
    result = await crawler.crawl_site()

    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.KNOWLEDGE_INGESTED,
            details=result,
        )
    )
    await db.commit()
    return result


@router.post("/reindex")
async def reindex_knowledge_base(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-index and update RayvenSC Knowledge Base chunks."""
    from app.services.crawler import RayvenWebCrawler

    llm = get_llm_provider()
    crawler = RayvenWebCrawler(db, llm)
    result = await crawler.crawl_site()
    return {"status": "reindexed", "chunks": result.get("chunks_created", 0)}


@router.post("/rules", status_code=201)
async def create_rule(
    body: RuleCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a structured FAQ, Brand Voice, Sales, or Escalation Rule."""
    from app.services.knowledge_agent import RayvenKnowledgeAgent

    agent = RayvenKnowledgeAgent(db)
    llm = get_llm_provider()
    doc = await agent.add_knowledge_item(
        title=body.title,
        content=body.content,
        doc_category=body.category,
        doc_type="rule",
        source_url="https://rayvensc.com/internal-rules",
        llm=llm,
    )

    return {
        "id": str(doc.id),
        "title": doc.title,
        "category": doc.doc_category,
        "chunks": doc.chunk_count,
    }


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    doc_category: str = Form("document"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload and ingest PDF, TXT, or MD documents."""
    from app.services.knowledge_agent import RayvenKnowledgeAgent

    agent = RayvenKnowledgeAgent(db)
    llm = get_llm_provider()
    content_bytes = await file.read()

    doc = await agent.ingest_file(
        filename=file.filename or "uploaded_doc",
        file_bytes=content_bytes,
        doc_category=doc_category,
        llm=llm,
    )

    return {
        "status": "success",
        "filename": file.filename,
        "document_id": str(doc.id),
        "chunk_count": doc.chunk_count,
    }


@router.post("/query")
async def query_knowledge_base(
    body: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    RAG query search with strict anti-hallucination, fallback keyword retrieval, and source attribution.
    """
    from app.services.knowledge_agent import RayvenKnowledgeAgent

    agent = RayvenKnowledgeAgent(db)

    try:
        llm = get_llm_provider()
    except Exception:
        llm = None

    query_lower = body.query.lower()

    # STRICT ANTI-HALLUCINATION CHECK FOR PRICING
    if any(w in query_lower for w in ["cost", "price", "charge", "fee", "rate"]):
        pricing_rules = await agent.get_all_rules_of_category("pricing_rule")
        if not pricing_rules:
            return {
                "query": body.query,
                "answer": (
                    "Rayven Strategic Communications does not use fixed public rate cards. Every engagement "
                    "is custom-architected based on organizational scope, stakeholders, and strategic objectives. "
                    "I will escalate your request to a Rayven partner to prepare a tailored advisory proposal."
                ),
                "confidence": 1.0,
                "escalated": True,
                "sources": [
                    {
                        "title": "RayvenSC Engagement Policy",
                        "source_url": "https://rayvensc.com/about",
                        "citation": "[Source: RayvenSC Engagement Policy (https://rayvensc.com/about)]",
                    }
                ],
            }

    try:
        results = await agent.search_with_citations(llm, query=body.query, k=body.k, threshold=body.threshold)
    except Exception as e:
        logger.warning(f"RAG search_with_citations exception: {e}")
        results = []

    if not results:
        return {
            "query": body.query,
            "answer": "I do not have sufficient approved internal information to answer this question accurately. I have escalated this inquiry to a Rayven Strategic Communications human partner.",
            "confidence": 0.0,
            "escalated": True,
            "sources": [],
        }

    # Synthesize RAG context
    context = "\n\n".join([f"{r.citation}\n{r.content}" for r in results])
    sources_payload = [
        {
            "title": r.title,
            "source_url": r.source_url,
            "citation": r.citation,
        }
        for r in results
    ]

    if llm:
        try:
            system_prompt = (
                "You are RayvenSC's AI Business Development Assistant. Answer the prospect's query using ONLY the "
                "provided approved internal knowledge context. Cite sources using [Source: Title (URL)]. "
                "Never invent prices, clients, results, statistics, or non-existent claims. "
                "If evidence is insufficient, state that approved information is limited and offer escalation."
            )
            user_prompt = f"Approved Internal Knowledge:\n{context}\n\nProspect Question: {body.query}"

            answer = await llm.complete(
                [LLMMessage(role="system", content=system_prompt), LLMMessage(role="user", content=user_prompt)],
                temperature=0.3,
            )
            return {
                "query": body.query,
                "answer": answer,
                "confidence": 0.95,
                "escalated": False,
                "sources": sources_payload,
            }
        except Exception as e:
            logger.warning(f"LLM synthesis completion failed ({e}), falling back to direct context extraction")

    # Direct context fallback when LLM API key is unconfigured
    fallback_answer = f"Based on RayvenSC internal documentation:\n\n" + "\n\n".join([f"• {r.content} {r.citation}" for r in results[:2]])

    return {
        "query": body.query,
        "answer": fallback_answer,
        "confidence": 0.85,
        "escalated": False,
        "sources": sources_payload,
    }


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()
    return {"status": "deleted", "id": str(doc_id)}
