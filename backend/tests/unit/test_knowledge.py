"""Unit tests for knowledge base ingestion helpers."""

import pytest
from app.knowledge.ingestion import _chunk_text


class TestChunking:
    def test_short_text_single_chunk(self):
        text = "Short text"
        chunks = _chunk_text(text, chunk_size=800)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_multiple_chunks(self):
        text = "a" * 2000
        chunks = _chunk_text(text, chunk_size=800, overlap=100)
        assert len(chunks) > 1
        # Each chunk should be at most 800 chars
        for chunk in chunks:
            assert len(chunk) <= 800

    def test_chunks_overlap(self):
        text = "a" * 1000
        chunks = _chunk_text(text, chunk_size=500, overlap=100)
        # Second chunk should start 400 chars into first chunk's end
        assert len(chunks) >= 2

    def test_exact_chunk_size(self):
        text = "x" * 800
        chunks = _chunk_text(text, chunk_size=800)
        assert len(chunks) == 1
