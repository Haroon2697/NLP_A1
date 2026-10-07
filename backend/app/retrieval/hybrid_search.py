"""
Hybrid Search Module: Combining BM25 Keyword Search with Dense Vector Search
Uses Reciprocal Rank Fusion (RRF) for robust multi-modal chunk retrieval.
"""
from __future__ import annotations

import pickle
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> List[str]:
    """Lightweight regex tokenizer for BM25 keyword matching."""
    return [w for w in re.findall(r"\w+", text.lower()) if len(w) > 1]


class BM25Retriever:
    """Manages the BM25 sparse keyword index over document chunks."""

    def __init__(self) -> None:
        self.chunk_ids: List[str] = []
        self.corpus_chunks: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None

    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """Builds the BM25 index from indexed chunks."""
        self.corpus_chunks = chunks
        self.chunk_ids = [c["id"] for c in chunks]
        tokenized_corpus = [tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Scores chunks against query tokens using BM25Okapi."""
        if not self.bm25 or not self.corpus_chunks:
            return []

        tokens = tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        scored_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for rank, idx in enumerate(scored_indices[:top_k], start=1):
            if scores[idx] <= 0.0:
                continue
            chunk = self.corpus_chunks[idx].copy()
            chunk["bm25_score"] = float(scores[idx])
            chunk["bm25_rank"] = rank
            results.append(chunk)

        return results

    def save(self, filepath: Path) -> None:
        """Serializes the BM25 index to disk."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "chunk_ids": self.chunk_ids,
            "corpus_chunks": self.corpus_chunks,
            "bm25": self.bm25,
        }
        with open(filepath, "wb") as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, filepath: Path) -> Optional[BM25Retriever]:
        """Loads a pre-indexed BM25 instance from disk."""
        if not filepath.exists():
            return None
        try:
            with open(filepath, "rb") as f:
                data = pickle.load(f)
            instance = cls()
            instance.chunk_ids = data["chunk_ids"]
            instance.corpus_chunks = data["corpus_chunks"]
            instance.bm25 = data["bm25"]
            return instance
        except Exception:
            return None


def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    k_constant: int = 60,
    dense_weight: float = 0.65,
    sparse_weight: float = 0.35,
    top_k: int = 4,
) -> List[Dict[str, Any]]:
    """
    Merges dense vector search results and sparse BM25 results using Reciprocal Rank Fusion (RRF).
    RRF score = sum(weight / (k_constant + rank)) for each rank list.
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    # Accumulate dense ranks
    for rank, item in enumerate(vector_results, start=1):
        doc_id = item["id"]
        doc_map[doc_id] = item
        scores[doc_id] = scores.get(doc_id, 0.0) + (dense_weight / (k_constant + rank))

    # Accumulate BM25 ranks
    for rank, item in enumerate(bm25_results, start=1):
        doc_id = item["id"]
        if doc_id not in doc_map:
            doc_map[doc_id] = item
        scores[doc_id] = scores.get(doc_id, 0.0) + (sparse_weight / (k_constant + rank))

    # Sort merged results by composite RRF score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    fused_results: List[Dict[str, Any]] = []
    for rank, doc_id in enumerate(sorted_ids[:top_k], start=1):
        item = doc_map[doc_id].copy()
        item["rrf_score"] = round(scores[doc_id], 5)
        item["final_rank"] = rank
        fused_results.append(item)

    return fused_results
