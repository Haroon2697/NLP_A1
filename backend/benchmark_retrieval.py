"""
Standalone Retrieval Latency Benchmark for FitZone Gym (Assignment 2)
Measures pure retrieval latency on CPU, completely isolated from LLM generation time.
Evaluates:
- Dense Vector Search (ChromaDB + ONNX all-MiniLM-L6-v2)
- Sparse BM25 Keyword Search
- Hybrid Search (RRF Fusion)
- Query LRU Caching
"""
from __future__ import annotations

import json
import logging
import statistics
import time
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.retrieval import get_retrieval_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fitzone.benchmark_retrieval")

BENCHMARK_QUERIES = [
    "What is the monthly price of the Basic Membership?",
    "Can I freeze or pause my gym membership while traveling?",
    "Who teaches Vinyasa Yoga and what days is it offered?",
    "What are Ahmed Khan's credentials and personal training rates?",
    "What is the cancellation notice period for monthly contracts?",
    "Do you offer student discounts and what are the eligible hours?",
    "What are the rules and attire for the sauna and steam room?",
    "How much does an InBody 570 body composition scan cost?",
    "What is included in the Black Card Executive VIP membership?",
    "Can I bring a guest with a Standard membership pass?",
]


def run_benchmark() -> dict:
    logger.info("Initializing Retrieval Engine for benchmarking...")
    engine = get_retrieval_engine()
    engine.cache.clear()

    total_chunks = engine.collection.count() if engine.collection else 0
    logger.info(f"Target Vector Store Chunks: {total_chunks}")

    logger.info("=" * 65)
    logger.info("RUNNING COLD RETRIEVAL BENCHMARKS (1st Pass - Cache Misses)")
    logger.info("=" * 65)

    cold_latencies: list[float] = []
    query_details: list[dict] = []

    for idx, query in enumerate(BENCHMARK_QUERIES, start=1):
        t0 = time.perf_counter()
        result = engine.search(query, top_k=4, use_hybrid=True)
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        cold_latencies.append(latency_ms)

        top_chunk_title = result["chunks"][0]["title"] if result["chunks"] else "None"
        query_details.append({
            "query": query,
            "cold_latency_ms": latency_ms,
            "chunks_retrieved": len(result["chunks"]),
            "top_match": top_chunk_title,
        })
        logger.info(f"[{idx:02d}/10] {query[:42]:<42} -> {latency_ms:>6.2f} ms | Top: {top_chunk_title[:28]}")

    logger.info("=" * 65)
    logger.info("RUNNING WARM RETRIEVAL BENCHMARKS (2nd Pass - Cache Hits)")
    logger.info("=" * 65)

    cached_latencies: list[float] = []
    for idx, query in enumerate(BENCHMARK_QUERIES, start=1):
        t0 = time.perf_counter()
        result = engine.search(query, top_k=4, use_hybrid=True)
        latency_ms = round((time.perf_counter() - t0) * 1000, 3)
        cached_latencies.append(latency_ms)
        query_details[idx - 1]["cached_latency_ms"] = latency_ms

    avg_cold = round(statistics.mean(cold_latencies), 2)
    median_cold = round(statistics.median(cold_latencies), 2)
    min_cold = min(cold_latencies)
    max_cold = max(cold_latencies)
    p95_cold = round(sorted(cold_latencies)[int(len(cold_latencies) * 0.95)], 2)

    avg_cached = round(statistics.mean(cached_latencies), 3)

    summary = {
        "benchmark_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hardware_target": "Local CPU",
        "embedding_model": "all-MiniLM-L6-v2 (ONNX runtime)",
        "vector_store": "ChromaDB Persistent (Cosine space)",
        "sparse_retriever": "BM25Okapi",
        "hybrid_algorithm": "Reciprocal Rank Fusion (w_dense=0.65, w_sparse=0.35)",
        "indexed_chunks": total_chunks,
        "sample_queries_count": len(BENCHMARK_QUERIES),
        "target_latency_ceiling_ms": 1000.0,
        "metrics_ms": {
            "cold_average_ms": avg_cold,
            "cold_median_ms": median_cold,
            "cold_min_ms": min_cold,
            "cold_max_ms": max_cold,
            "cold_p95_ms": p95_cold,
            "cached_average_ms": avg_cached,
        },
        "target_met": max_cold < 1000.0,
        "query_results": query_details,
    }

    out_file = BACKEND_DIR / "retrieval_benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("=" * 65)
    logger.info("RETRIEVAL BENCHMARK SUMMARY (Pure CPU Retrieval)")
    logger.info(f"Average Cold Retrieval Latency : {avg_cold} ms")
    logger.info(f"Median Cold Retrieval Latency  : {median_cold} ms")
    logger.info(f"P95 Retrieval Latency          : {p95_cold} ms")
    logger.info(f"Max Retrieval Latency          : {max_cold} ms (Target < 1000 ms: {'PASSED' if max_cold < 1000 else 'FAILED'})")
    logger.info(f"Average Cached Query Latency   : {avg_cached} ms (sub-millisecond!)")
    logger.info(f"Saved results to: {out_file}")
    logger.info("=" * 65)

    return summary


if __name__ == "__main__":
    run_benchmark()
