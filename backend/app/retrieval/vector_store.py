"""
Core Retrieval Engine for FitZone Gym RAG Module
Manages ChromaDB vector store, ONNX embeddings, BM25 hybrid search, and LRU caching.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions

from .budgeter import ContextBudgeter
from .cache import QueryCache
from .config import (
    BM25_INDEX_PATH,
    CACHE_CAPACITY,
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    ENABLE_HYBRID_SEARCH,
    SIMILARITY_THRESHOLD,
    TOP_K,
)
from .hybrid_search import BM25Retriever, reciprocal_rank_fusion

logger = logging.getLogger("fitzone.retrieval")


class RetrievalEngine:
    """
    Production-grade CPU Retrieval Engine combining:
    - Persistent ChromaDB vector database with all-MiniLM-L6-v2 ONNX embeddings
    - BM25Okapi sparse keyword retrieval for exact term matching
    - Reciprocal Rank Fusion (RRF) for hybrid ranking
    - LRU Cache for sub-millisecond query retrieval
    - Score thresholding for graceful out-of-domain fallback
    """

    def __init__(self) -> None:
        self.client: Optional[chromadb.PersistentClient] = None
        self.collection: Optional[chromadb.Collection] = None
        self.embedding_fn: Optional[Any] = None
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.cache = QueryCache(capacity=CACHE_CAPACITY)
        self.budgeter = ContextBudgeter()
        self.is_initialized = False

    def initialize(self) -> bool:
        """Initializes ChromaDB client, collection, and BM25 index."""
        try:
            CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

            # Retrieve or create collection configured with cosine distance
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )

            # Load BM25 index if available
            if ENABLE_HYBRID_SEARCH and BM25_INDEX_PATH.exists():
                self.bm25_retriever = BM25Retriever.load(BM25_INDEX_PATH)
                logger.info("Loaded BM25 index for Hybrid Search.")

            self.is_initialized = True
            doc_count = self.collection.count()
            logger.info(f"RetrievalEngine initialized with {doc_count} chunks in collection '{COLLECTION_NAME}'.")
            return True
        except Exception as exc:
            logger.error(f"Failed to initialize RetrievalEngine: {exc}", exc_info=True)
            self.is_initialized = False
            return False

    def search(
        self,
        query: str,
        top_k: int = TOP_K,
        threshold: float = SIMILARITY_THRESHOLD,
        use_hybrid: bool = ENABLE_HYBRID_SEARCH,
    ) -> Dict[str, Any]:
        """
        Synchronous retrieval pipeline.
        Returns a dictionary containing:
            - chunks: List of retrieved chunk dictionaries
            - elapsed_ms: Retrieval latency in milliseconds
            - cached: Boolean indicating whether result was served from LRU cache
            - confident: Boolean indicating whether at least one chunk passed similarity threshold
        """
        start_time = time.perf_counter()

        cleaned_query = query.strip()
        if not cleaned_query:
            return {"chunks": [], "elapsed_ms": 0.0, "cached": False, "confident": False}

        # Check LRU Cache
        cached_result = self.cache.get(cleaned_query)
        if cached_result is not None:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            confident = any(c.get("similarity", 0.0) >= threshold or c.get("rrf_score", 0.0) > 0.015 for c in cached_result)
            return {
                "chunks": cached_result,
                "elapsed_ms": elapsed_ms,
                "cached": True,
                "confident": confident,
            }

        if not self.is_initialized or not self.collection:
            self.initialize()
            if not self.is_initialized or not self.collection:
                return {"chunks": [], "elapsed_ms": 0.0, "cached": False, "confident": False}

        try:
            # 1. Dense Vector Search
            fetch_k = max(top_k * 4, 16)
            chroma_results = self.collection.query(
                query_texts=[cleaned_query],
                n_results=fetch_k,
                include=["documents", "metadatas", "distances"],
            )

            vector_chunks: List[Dict[str, Any]] = []
            if chroma_results and chroma_results.get("documents") and chroma_results["documents"][0]:
                docs = chroma_results["documents"][0]
                metas = chroma_results["metadatas"][0]
                dists = chroma_results["distances"][0]
                ids = chroma_results["ids"][0]

                for doc_text, meta, dist, chunk_id in zip(docs, metas, dists, ids):
                    # For cosine distance, similarity = 1 - distance
                    # Chroma distances can slightly vary if not normalized; clamp to [0, 1]
                    sim = max(0.0, min(1.0, 1.0 - float(dist)))
                    vector_chunks.append({
                        "id": chunk_id,
                        "text": doc_text,
                        "doc_id": meta.get("doc_id", "DOC"),
                        "title": meta.get("title", "FitZone Guide"),
                        "category": meta.get("category", "General"),
                        "source_file": meta.get("source_file", ""),
                        "chunk_index": meta.get("chunk_index", 0),
                        "distance": round(float(dist), 4),
                        "similarity": round(sim, 4),
                    })

            # Filter vector results by similarity threshold
            filtered_vector_chunks = [c for c in vector_chunks if c["similarity"] >= threshold]

            # 2. Sparse BM25 Search & Hybrid Fusion
            if use_hybrid and self.bm25_retriever:
                bm25_chunks = self.bm25_retriever.search(cleaned_query, top_k=fetch_k)
                if bm25_chunks:
                    # Fuse using Reciprocal Rank Fusion
                    final_chunks = reciprocal_rank_fusion(
                        filtered_vector_chunks or vector_chunks[:fetch_k],
                        bm25_chunks,
                        top_k=top_k,
                    )
                else:
                    final_chunks = (filtered_vector_chunks or vector_chunks)[:top_k]
            else:
                final_chunks = (filtered_vector_chunks or vector_chunks)[:top_k]

            # Confidence check: must meet threshold or have good RRF rank
            has_confidence = bool(
                final_chunks
                and (
                    any(c.get("similarity", 0.0) >= threshold for c in final_chunks)
                    or any(c.get("rrf_score", 0.0) >= 0.015 for c in final_chunks)
                )
            )

            # Do not return low-confidence garbage chunks when similarity is weak
            if not has_confidence:
                final_chunks = []

            # Populate LRU Cache
            self.cache.put(cleaned_query, final_chunks)

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "chunks": final_chunks,
                "elapsed_ms": elapsed_ms,
                "cached": False,
                "confident": has_confidence,
            }

        except Exception as exc:
            logger.error(f"Error during retrieval search: {exc}", exc_info=True)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {"chunks": [], "elapsed_ms": elapsed_ms, "cached": False, "confident": False, "error": str(exc)}

    async def async_search(
        self,
        query: str,
        top_k: int = TOP_K,
        threshold: float = SIMILARITY_THRESHOLD,
        use_hybrid: bool = ENABLE_HYBRID_SEARCH,
    ) -> Dict[str, Any]:
        """
        Non-blocking async search. Runs vector & keyword search in a worker thread
        so FastAPI's asynchronous event loop remains responsive for all concurrent users.
        """
        return await asyncio.to_thread(self.search, query, top_k, threshold, use_hybrid)


# Singleton instance
_engine_instance: Optional[RetrievalEngine] = None


def get_retrieval_engine() -> RetrievalEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RetrievalEngine()
        _engine_instance.initialize()
    return _engine_instance
