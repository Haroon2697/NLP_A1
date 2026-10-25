import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx

from backend.app.config import (
    NUM_CTX,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    TEMPERATURE,
    TOP_P,
)
from backend.app.conversation_manager import SYSTEM_PROMPT


BENCHMARK_PROMPTS = [
    {
        "category": "Greeting & Plan Inquiry",
        "prompt": "Hi! I am new here. What are the membership plans at FitZone Gym?",
    },
    {
        "category": "Policy & Freeze Query",
        "prompt": "How does the membership freeze policy work if I travel for 3 weeks?",
    },
    {
        "category": "Class Schedule & Trainers",
        "prompt": "Can you give me the weekly Yoga schedule and tell me who the trainer is?",
    },
]


async def run_single_benchmark(client: httpx.AsyncClient, prompt: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "num_predict": 256,
            "num_ctx": NUM_CTX,
        },
    }

    start = time.perf_counter()
    first_token_time = None
    token_count = 0
    full_text = []

    async with client.stream("POST", f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat", json=payload) as response:
        if response.status_code != 200:
            raise RuntimeError(f"Ollama returned {response.status_code}")

        async for raw_line in response.aiter_lines():
            if not raw_line or not raw_line.strip():
                continue
            try:
                data = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            msg = data.get("message") or {}
            chunk = msg.get("content") or data.get("response") or ""
            if chunk:
                if first_token_time is None:
                    first_token_time = time.perf_counter() - start
                token_count += 1
                full_text.append(chunk)

    total_time = time.perf_counter() - start
    ttft = first_token_time or total_time
    tokens_per_sec = token_count / total_time if total_time > 0 else 0.0

    return {
        "prompt": prompt,
        "ttft_seconds": round(ttft, 3),
        "total_seconds": round(total_time, 3),
        "token_count": token_count,
        "tokens_per_second": round(tokens_per_sec, 2),
        "response_preview": "".join(full_text)[:120].strip() + "...",
    }


async def main() -> None:
    print("=" * 70)
    print(f"FitZone Conversational AI - Local CPU Inference Benchmark")
    print(f"Model: {OLLAMA_MODEL} | Base URL: {OLLAMA_BASE_URL}")
    print("=" * 70)

    timeout = httpx.Timeout(180.0, connect=10.0)
    results = []

    async with httpx.AsyncClient(timeout=timeout) as client:
        # Check Ollama connection first
        try:
            health = await client.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            if health.status_code != 200:
                print(f"ERROR: Ollama server not ready at {OLLAMA_BASE_URL}")
                return
        except Exception as exc:
            print(f"ERROR: Could not connect to Ollama: {exc}")
            return

        for idx, item in enumerate(BENCHMARK_PROMPTS, 1):
            print(f"\n[Test {idx}/{len(BENCHMARK_PROMPTS)}] Running: {item['category']}...")
            try:
                data = await run_single_benchmark(client, item["prompt"])
                data["category"] = item["category"]
                results.append(data)
                print(f"  -> TTFT: {data['ttft_seconds']}s | Total: {data['total_seconds']}s | Tokens: {data['token_count']} | TPS: {data['tokens_per_second']} tok/s")
            except Exception as exc:
                print(f"  -> FAILED: {exc}")

    if not results:
        print("No benchmark results generated.")
        return

    avg_ttft = sum(r["ttft_seconds"] for r in results) / len(results)
    avg_total = sum(r["total_seconds"] for r in results) / len(results)
    avg_tps = sum(r["tokens_per_second"] for r in results) / len(results)
    total_tokens = sum(r["token_count"] for r in results)

    summary = {
        "model": OLLAMA_MODEL,
        "hardware": "Local CPU",
        "trials": len(results),
        "average_ttft_seconds": round(avg_ttft, 3),
        "average_total_seconds": round(avg_total, 3),
        "average_tokens_per_sec": round(avg_tps, 2),
        "total_tokens_generated": total_tokens,
        "runs": results,
    }

    output_path = Path(__file__).parent / "benchmark_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print(f"  Average Time to First Token (TTFT): {avg_ttft:.2f} s")
    print(f"  Average Total Turn Latency:        {avg_total:.2f} s")
    print(f"  Average Throughput:                {avg_tps:.2f} tokens/s")
    print(f"  Results saved to:                  {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
