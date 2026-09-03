"""Unit tests for Rayven Knowledge Agent and source citations."""

import pytest
from app.services.knowledge_agent import KnowledgeSearchResult


class TestKnowledgeAgent:
    def test_knowledge_search_result_citation_format(self):
        res = KnowledgeSearchResult(
            content="RayvenSC provides narrative architecture and strategic communications.",
            title="RayvenSC Services Overview",
            source_url="https://rayvensc.com/services",
            doc_type="webpage",
            doc_category="document",
            similarity=0.92,
            citation="[Source: RayvenSC Services Overview (https://rayvensc.com/services)]",
        )
        assert "[Source: RayvenSC Services Overview" in res.citation
        assert "https://rayvensc.com/services" in res.citation
        assert res.similarity == 0.92
