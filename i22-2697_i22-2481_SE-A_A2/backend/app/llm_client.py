import json
import time
from typing import AsyncIterator, Dict, Any

import httpx

from .config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    MAX_RESPONSE_TOKENS,
    TEMPERATURE,
    TOP_P,
    NUM_CTX,
)


async def stream_response(messages: list[dict[str, str]]) -> AsyncIterator[str]:
    """
    Streams response tokens from the local Ollama LLM instance over HTTP.
    Uses asynchronous chunk reading so concurrent client requests do not block the event loop.
    """
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "num_predict": MAX_RESPONSE_TOKENS,
            "num_ctx": NUM_CTX,
        },
    }

    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {error_text.decode('utf-8', errors='ignore')}")

                async for raw_line in response.aiter_lines():
                    if not raw_line or not raw_line.strip():
                        continue
                    try:
                        data = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue

                    message_obj = data.get("message") or {}
                    token = message_obj.get("content") or data.get("response") or data.get("content")
                    if token:
                        yield token
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Could not connect to Ollama at {OLLAMA_BASE_URL}. Ensure Ollama is running (`ollama serve`)."
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Local LLM streaming error: {exc}") from exc


async def generate_response(messages: list[dict[str, str]]) -> tuple[str, Dict[str, Any]]:
    """
    Collects a full non-streaming response with performance metrics (TTFT, total time, token count).
    """
    start_time = time.perf_counter()
    first_token_time = None
    chunks: list[str] = []

    async for chunk in stream_response(messages):
        if first_token_time is None:
            first_token_time = time.perf_counter() - start_time
        chunks.append(chunk)

    total_time = time.perf_counter() - start_time
    full_text = "".join(chunks).strip()
    metrics = {
        "ttft_seconds": round(first_token_time or 0.0, 3),
        "total_seconds": round(total_time, 3),
        "token_chunks": len(chunks),
        "tokens_per_second": round(len(chunks) / total_time, 2) if total_time > 0 else 0.0,
    }
    return full_text, metrics
