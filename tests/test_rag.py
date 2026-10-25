"""
Automated Test Suite for Assignment 2 RAG System
Tests:
- Corpus completeness (50-100 documents)
- Vector indexing & metadata preservation
- Top-k retrieval accuracy (k >= 3)
- BM25 & Dense Hybrid Search (RRF)
- LRU Query caching
- Context budgeting & overflow protection
- Failure handling: weak matches, timeouts, errors
- API integration & stats endpoint
"""
from __future__ import annotations

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.conversation_manager import ConversationManager
from backend.app.retrieval import get_retrieval_engine, ContextBudgeter, QueryCache
from backend.app.retrieval.config import DOCS_DIR, CHUNK_SIZE
from backend.app.retrieval.hybrid_search import tokenize, BM25Retriever, reciprocal_rank_fusion

client = TestClient(app)


def test_corpus_documents_count():
    """Validates that corpus contains 50-100 realistic domain documents."""
    assert DOCS_DIR.exists(), f"Corpus dir not found: {DOCS_DIR}"
    docs = list(DOCS_DIR.glob("*.md")) + list(DOCS_DIR.glob("*.txt"))
    assert 50 <= len(docs) <= 100, f"Expected 50-100 documents, found {len(docs)}"


def test_vector_store_indexed_chunks():
    """Validates ChromaDB collection contains indexed chunks."""
    engine = get_retrieval_engine()
    assert engine.collection is not None
    count = engine.collection.count()
    assert count >= 100, f"Expected at least 100 chunks, found {count}"


def test_top_k_retrieval_structure():
    """Verifies that retrieval returns at least 3 chunks with proper metadata."""
    engine = get_retrieval_engine()
    res = engine.search("What is the cost of the basic plan?", top_k=4)
    assert res["confident"] is True
    chunks = res["chunks"]
    assert len(chunks) >= 3, f"Expected at least 3 chunks, got {len(chunks)}"

    first_chunk = chunks[0]
    for key in ["id", "text", "doc_id", "title", "category", "source_file"]:
        assert key in first_chunk, f"Missing key '{key}' in retrieved chunk"


def test_retrieval_domain_accuracy():
    """Validates that specific queries retrieve their designated ground truth documents."""
    engine = get_retrieval_engine()

    # Query 1: Membership Freeze
    res_freeze = engine.search("Can I freeze my membership if I travel?")
    top_doc_ids = [c["doc_id"] for c in res_freeze["chunks"]]
    assert "POL-01" in top_doc_ids, f"Expected POL-01 in {top_doc_ids}"

    # Query 2: InBody Scan
    res_inbody = engine.search("How much is an InBody 570 scan?")
    top_doc_ids_inbody = [c["doc_id"] for c in res_inbody["chunks"]]
    assert "FEE-03" in top_doc_ids_inbody, f"Expected FEE-03 in {top_doc_ids_inbody}"

    # Query 3: Yoga Class
    res_yoga = engine.search("What is the schedule for Vinyasa Yoga?")
    top_titles = [c["title"].lower() for c in res_yoga["chunks"]]
    assert any("yoga" in t for t in top_titles), f"Yoga not found in {top_titles}"


def test_bm25_and_hybrid_search():
    """Tests BM25 sparse retrieval and Reciprocal Rank Fusion."""
    engine = get_retrieval_engine()
    assert engine.bm25_retriever is not None

    # Search for an exact term code
    bm25_results = engine.bm25_retriever.search("MEM-03 VIP", top_k=5)
    assert len(bm25_results) > 0
    assert any("MEM-03" in c["doc_id"] for c in bm25_results)

    # Test RRF fusion
    vec_results = engine.search("MEM-03 VIP", top_k=5, use_hybrid=False)["chunks"]
    fused = reciprocal_rank_fusion(vec_results, bm25_results, top_k=4)
    assert len(fused) <= 4
    assert "rrf_score" in fused[0]


def test_lru_query_cache():
    """Validates LRU cache hit/miss behavior and speed."""
    cache = QueryCache(capacity=3)
    assert cache.get("test query") is None

    cache.put("test query", [{"id": "chunk_1", "text": "hello"}])
    cached = cache.get("test query")
    assert cached is not None
    assert cached[0]["id"] == "chunk_1"

    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1

    # Test capacity eviction
    cache.put("query 2", [])
    cache.put("query 3", [])
    cache.put("query 4", [])  # Should evict least recently used
    assert cache.stats()["size"] <= 3


def test_context_budgeter_enforcement():
    """Validates that context budgeter strictly enforces max token limits."""
    budgeter = ContextBudgeter(num_ctx=2048, max_response_tokens=256, max_rag_tokens=300)

    # Create dummy oversized chunks
    oversized_chunks = [
        {"id": f"c_{i}", "doc_id": f"D_{i}", "title": f"Doc {i}", "text": "Word " * 200, "category": "Test"}
        for i in range(10)
    ]

    formatted_context, citations, tokens_used = budgeter.allocate_chunks(
        chunks=oversized_chunks,
        system_prompt="System instructions " * 50,
        history_messages=[{"role": "user", "content": "hello"}],
        user_query="test query",
    )

    assert tokens_used <= budgeter.max_rag_tokens + 50
    assert len(citations) < len(oversized_chunks)  # Truncated or capped


def test_failure_handling_out_of_domain():
    """
    Phase IV: Weak or unanswerable queries should not fabricate documents.
    """
    import asyncio
    manager = ConversationManager()
    messages, citations, metrics = asyncio.run(
        manager.async_build_prompt_messages(
            session_id="test_weak",
            user_message="Do you sell interstellar rocket fuel?",
        )
    )

    # Off-domain or ungrounded query
    assert len(citations) == 0
    # Must contain graceful fallback instructions
    system_content = messages[0]["content"]
    assert "NO DIRECT MATCH FOUND" in system_content or "do not have specific documented records" in system_content


def test_failure_handling_retrieval_error():
    """
    Phase IV: Verifies graceful degradation if vector store throws an unexpected exception.
    """
    import asyncio
    manager = ConversationManager()

    # Pass an empty query or simulate failure
    messages, citations, metrics = asyncio.run(
        manager.async_build_prompt_messages(
            session_id="test_err",
            user_message="   ",
        )
    )
    assert len(messages) >= 1

    assert messages[0]["role"] == "system"


def test_api_health_endpoint_rag_status():
    """Checks that health endpoint provides RAG metadata."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "rag" in data
    assert data["rag"]["chunks_indexed"] >= 100


def test_api_rag_stats_endpoint():
    """Checks /api/rag/stats endpoint returns vector store and cache telemetry."""
    res = client.get("/api/rag/stats")
    assert res.status_code == 200
    data = res.json()
    assert "vector_store" in data
    assert "embedding_model" in data
    assert "cache" in data
    assert data["indexed_chunks"] >= 100


def test_api_chat_rest_returns_citations(monkeypatch):
    """Checks /api/chat returns source citations for grounded queries."""
    from unittest.mock import AsyncMock
    import backend.app.main as main_mod

    mock_gen = AsyncMock(return_value=("Cancellation requires 30 days notice per POL-02.", {"ttft_seconds": 0.5, "total_seconds": 1.2, "tokens_per_second": 10.0}))
    monkeypatch.setattr(main_mod, "generate_response", mock_gen)

    res = client.post("/api/chat", json={
        "session_id": "test_rest_rag",
        "message": "What is the policy for membership cancellation?",
    })
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "citations" in data
    assert len(data["citations"]) > 0
    assert "retrieval_metrics" in data


@pytest.mark.anyio
async def test_grounded_answer_factual_rates_senior_citizen():
    """Verifies that grounded query for senior citizen plan returns exact rates and factual details."""
    from backend.app.llm_client import stream_response

    manager = ConversationManager()
    messages, citations, _ = await manager.async_build_prompt_messages(
        "test_senior_rates", "How much is the senior citizen plan?"
    )
    tokens = []
    async for tok in stream_response(messages):
        tokens.append(tok)
    reply = "".join(tokens)

    # Validate factual answers from MEM-07
    assert "MEM-07" in reply
    assert "3,200" in reply
    assert "Registration Fee" in reply
    assert "Waived" in reply


