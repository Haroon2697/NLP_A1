"""
NLP Assignment 3 — Voice & Tool Latency Benchmarking Suite
Measures:
1. ASR Latency: End of speech audio -> transcript ready
2. Retrieval Latency: Transcript -> grounded context ready
3. Tool Execution Latency: Tool call -> result returned
4. LLM First-Token Latency (TTFT): Context -> first token streamed
5. TTS First-Audio Latency: First sentence -> first audio chunk ready
6. End-to-End Voice Latency: End of speech -> first audio playback ready
7. Concurrency Test: 2 concurrent sessions measuring pipeline throughput
Outputs results to backend/voice_benchmark_results.json.
"""
from __future__ import annotations

import asyncio
import io
import json
import logging
import time
import wave
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from backend.app.conversation_manager import ConversationManager
from backend.app.llm_client import generate_response, stream_response
from backend.app.retrieval import get_retrieval_engine
from backend.app.tools import get_tool_orchestrator
from backend.app.voice import get_asr_engine, get_tts_engine

logger = logging.getLogger("fitzone.benchmark_voice")
RESULTS_PATH = Path(__file__).resolve().parent / "voice_benchmark_results.json"


def generate_synthetic_voice_audio(duration_s: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generates synthetic 16kHz mono 16-bit PCM WAV audio for benchmarking."""
    t = np.linspace(0, duration_s, int(sample_rate * duration_s), dtype=np.float32)
    tone = (np.sin(2 * np.pi * 300 * t) * 16384).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(tone.tobytes())
    return buf.getvalue()


async def benchmark_asr(asr_engine, wav_bytes: bytes, trials: int = 3) -> Dict[str, Any]:
    """Measures ASR transcription latency."""
    latencies = []
    for _ in range(trials):
        t0 = time.perf_counter()
        try:
            res = await asr_engine.async_transcribe(wav_bytes)
            elapsed = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed)
        except Exception:
            elapsed = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed)

    return {
        "engine": "faster-whisper (CTranslate2 int8 CPU)",
        "trials": trials,
        "mean_latency_ms": round(float(np.mean(latencies)), 2),
        "min_latency_ms": round(float(np.min(latencies)), 2),
        "max_latency_ms": round(float(np.max(latencies)), 2),
    }


async def benchmark_retrieval(retrieval_engine, queries: List[str]) -> Dict[str, Any]:
    """Measures Hybrid RAG (Dense + BM25) retrieval latency."""
    latencies = []
    for q in queries:
        t0 = time.perf_counter()
        res = await retrieval_engine.async_search(q)
        elapsed = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed)

    return {
        "engine": "ChromaDB (Dense) + BM25 (Sparse) + RRF",
        "queries_tested": len(queries),
        "mean_latency_ms": round(float(np.mean(latencies)), 2),
        "min_latency_ms": round(float(np.min(latencies)), 2),
        "max_latency_ms": round(float(np.max(latencies)), 2),
    }


async def benchmark_tools(orchestrator) -> Dict[str, Any]:
    """Measures tool execution latency for each registered tool."""
    tool_benchmarks = {}

    # 1. Weather
    t0 = time.perf_counter()
    w_res = await orchestrator.execute_tool("get_weather", {"city": "Islamabad"})
    tool_benchmarks["get_weather_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # 2. Calculator
    t0 = time.perf_counter()
    c_res = await orchestrator.execute_tool(
        "calculate_membership", {"plan": "premium", "months": 12, "student_discount": False}
    )
    tool_benchmarks["calculate_membership_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # 3. Schedule
    t0 = time.perf_counter()
    s_res = await orchestrator.execute_tool(
        "check_class_schedule", {"class_type": "yoga", "day_of_week": "monday"}
    )
    tool_benchmarks["check_class_schedule_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # 4. CRM
    t0 = time.perf_counter()
    crm_res = await orchestrator.execute_tool(
        "crm_lookup", {"action": "set", "user_id": "bench_user", "data": {"name": "Bench"}}
    )
    tool_benchmarks["crm_lookup_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    return tool_benchmarks


async def benchmark_tts(tts_engine, sample_sentences: List[str]) -> Dict[str, Any]:
    """Measures first-audio chunk latency and synthesis throughput."""
    latencies = []
    for s in sample_sentences:
        t0 = time.perf_counter()
        res = await tts_engine.async_synthesize(s)
        elapsed = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed)

    return {
        "engine": "piper-tts / local neural synthesis",
        "sample_count": len(sample_sentences),
        "mean_first_audio_ms": round(float(np.mean(latencies)), 2),
        "min_first_audio_ms": round(float(np.min(latencies)), 2),
        "max_first_audio_ms": round(float(np.max(latencies)), 2),
    }


async def benchmark_end_to_end_turn(
    conversation_manager: ConversationManager,
    query: str,
    wav_bytes: bytes,
    asr_engine,
    tts_engine,
) -> Dict[str, Any]:
    """
    Executes a complete voice pipeline turn:
    End of Speech -> ASR -> Retrieval/Tool -> LLM TTFT -> TTS First Audio.
    """
    turn_start = time.perf_counter()

    # 1. ASR
    asr_t0 = time.perf_counter()
    try:
        asr_res = await asr_engine.async_transcribe(wav_bytes)
        transcript = asr_res.get("text", "") or query
    except Exception:
        transcript = query
    asr_ms = round((time.perf_counter() - asr_t0) * 1000, 2)

    # 2. Retrieval & Prompt Compilation
    ret_t0 = time.perf_counter()
    session_id = f"bench_{int(time.time() * 1000)}"
    conversation_manager.add_turn(session_id, "user", transcript)
    messages, citations, ret_metrics = await conversation_manager.async_build_prompt_messages(
        session_id, transcript
    )
    retrieval_ms = round((time.perf_counter() - ret_t0) * 1000, 2)

    # 3. LLM TTFT (Time to First Token)
    llm_t0 = time.perf_counter()
    first_token_ms = None
    first_sentence = ""
    collected_tokens = []

    async for token in stream_response(messages):
        if first_token_ms is None:
            first_token_ms = round((time.perf_counter() - llm_t0) * 1000, 2)
        collected_tokens.append(token)
        first_sentence += token
        if any(punct in token for punct in [".", "!", "?", "\n"]) and len(first_sentence) > 20:
            break

    llm_ttft_ms = first_token_ms or round((time.perf_counter() - llm_t0) * 1000, 2)

    # 4. TTS First Audio Chunk
    tts_t0 = time.perf_counter()
    tts_res = await tts_engine.async_synthesize(first_sentence.strip() or "Welcome to FitZone Gym.")
    tts_ms = round((time.perf_counter() - tts_t0) * 1000, 2)

    total_e2e_ms = round((time.perf_counter() - turn_start) * 1000, 2)

    return {
        "query": query,
        "asr_latency_ms": asr_ms,
        "retrieval_latency_ms": retrieval_ms,
        "llm_ttft_ms": llm_ttft_ms,
        "tts_first_audio_ms": tts_ms,
        "end_to_end_ms": total_e2e_ms,
        "under_2s_target": total_e2e_ms < 2000.0,
    }


async def run_concurrent_benchmarks(cm, wav_bytes, asr, tts, num_concurrent: int = 2):
    """Measures pipeline performance with 2 concurrent voice turns."""
    queries = [
        "What is the schedule for Yoga on Monday?",
        "Can I freeze my membership if I travel?",
    ]
    tasks = [
        benchmark_end_to_end_turn(cm, queries[i % len(queries)], wav_bytes, asr, tts)
        for i in range(num_concurrent)
    ]
    t0 = time.perf_counter()
    results = await asyncio.gather(*tasks)
    total_elapsed = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "concurrent_users": num_concurrent,
        "total_batch_ms": total_elapsed,
        "per_user_results": results,
        "average_e2e_ms": round(float(np.mean([r["end_to_end_ms"] for r in results])), 2),
    }


async def main():
    print("=" * 70)
    print("FitAssist Real-Time Voice & Tool Orchestrator Benchmark")
    print("=" * 70)

    cm = ConversationManager()
    retrieval_engine = get_retrieval_engine()
    orchestrator = get_tool_orchestrator()
    asr = get_asr_engine()
    tts = get_tts_engine()

    wav_bytes = generate_synthetic_voice_audio(duration_s=2.0)

    print("\n[1/5] Benchmarking ASR Engine...")
    asr_stats = await benchmark_asr(asr, wav_bytes, trials=3)
    print(f"  ASR Mean Latency: {asr_stats['mean_latency_ms']}ms")

    print("\n[2/5] Benchmarking Retrieval Engine (ChromaDB + BM25)...")
    test_queries = [
        "How much is the senior citizen plan?",
        "What are the fees for swimming lane rental?",
        "Who is Dr. Zoya Merchant?",
        "Can I freeze my membership?",
    ]
    ret_stats = await benchmark_retrieval(retrieval_engine, test_queries)
    print(f"  Retrieval Mean Latency: {ret_stats['mean_latency_ms']}ms")

    print("\n[3/5] Benchmarking Tool Orchestration...")
    tool_stats = await benchmark_tools(orchestrator)
    for tool_name, lat in tool_stats.items():
        print(f"  {tool_name}: {lat}ms")

    print("\n[4/5] Benchmarking TTS First-Audio Synthesis...")
    sample_sentences = [
        "Welcome to FitZone Gym! Our basic membership is Rs. 4,000 per month.",
        "Here is our class schedule for Yoga on Monday at 6:00 PM.",
        "According to our membership freeze policy, members may pause for up to 30 days.",
    ]
    tts_stats = await benchmark_tts(tts, sample_sentences)
    print(f"  TTS First-Audio Mean Latency: {tts_stats['mean_first_audio_ms']}ms")

    print("\n[5/5] Benchmarking End-to-End Voice Turns & Concurrency...")
    single_turn = await benchmark_end_to_end_turn(
        cm, "What is the schedule for Yoga on Monday?", wav_bytes, asr, tts
    )
    print(f"  Single User End-to-End: {single_turn['end_to_end_ms']}ms (<2s: {single_turn['under_2s_target']})")

    concurrent_stats = await run_concurrent_benchmarks(cm, wav_bytes, asr, tts, num_concurrent=2)
    print(f"  2 Concurrent Users Mean End-to-End: {concurrent_stats['average_e2e_ms']}ms")

    final_results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hardware": "Local CPU (Intel / AMD)",
        "target_max_e2e_ms": 2000.0,
        "asr": asr_stats,
        "retrieval": ret_stats,
        "tools": tool_stats,
        "tts": tts_stats,
        "single_turn": single_turn,
        "concurrency": concurrent_stats,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2)

    print(f"\n[OK] Results saved to: {RESULTS_PATH}")
    print("\nLatency Summary Breakdown:")
    print(f"  1. ASR (Speech-to-Text):           {single_turn['asr_latency_ms']:>6.1f} ms")
    print(f"  2. Retrieval & Context Budgeting: {single_turn['retrieval_latency_ms']:>6.1f} ms")
    print(f"  3. LLM Time-to-First-Token:       {single_turn['llm_ttft_ms']:>6.1f} ms")
    print(f"  4. TTS First-Audio Generation:    {single_turn['tts_first_audio_ms']:>6.1f} ms")
    print("  " + "-" * 42)
    print(f"  TOTAL END-OF-SPEECH TO AUDIO:     {single_turn['end_to_end_ms']:>6.1f} ms")
    print(f"  Status: {'PASSED (<2.0s)' if single_turn['under_2s_target'] else 'EXCEEDED'}")


if __name__ == "__main__":
    asyncio.run(main())
