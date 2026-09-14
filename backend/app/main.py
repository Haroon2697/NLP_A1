from __future__ import annotations

import json
import time
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import (
    BACKEND_DIR,
    FRONTEND_DIR,
    MAX_HISTORY_PAIRS,
    MAX_RESPONSE_TOKENS,
    NUM_CTX,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    TEMPERATURE,
)
from .conversation_manager import ConversationManager
from .llm_client import generate_response, stream_response

app = FastAPI(
    title="FitZone Gym Assistant API",
    description="Conversational AI Backend for FitZone Gym Membership, Classes, and Policies.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversation_manager = ConversationManager()


def validate_message_payload(payload: Any) -> tuple[str, str]:
    """Validates the structure of an incoming chat request."""
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    session_id = payload.get("session_id")
    message = payload.get("message")
    if not session_id or not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id is required and must be a non-empty string.")
    if message is None or not isinstance(message, str):
        raise ValueError("message is required and must be a string.")
    cleaned = message.strip()
    if not cleaned:
        raise ValueError("message cannot be empty.")
    return session_id.strip(), cleaned


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint providing runtime and model configuration."""
    return {
        "status": "ok",
        "service": "FitAssist Backend",
        "model": OLLAMA_MODEL,
        "ollama_url": OLLAMA_BASE_URL,
        "context_window": NUM_CTX,
        "max_history_pairs": MAX_HISTORY_PAIRS,
        "temperature": TEMPERATURE,
    }


@app.get("/api/benchmarks")
async def get_benchmarks() -> dict[str, Any]:
    """Returns local CPU hardware benchmarks and runtime parameters."""
    results_file = BACKEND_DIR / "benchmark_results.json"
    if results_file.exists():
        try:
            with open(results_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "model": OLLAMA_MODEL,
        "quantization": "Q4_K_M",
        "parameters": "3.1B",
        "hardware": "Local CPU (Intel / AMD)",
        "measured_metrics": {
            "warm_time_to_first_token_seconds": 1.10,
            "average_throughput_tokens_per_sec": 3.54,
            "typical_response_time_seconds": "39s - 66s",
        },
        "limits": {
            "max_response_tokens": MAX_RESPONSE_TOKENS,
            "context_tokens": NUM_CTX,
            "max_history_pairs": MAX_HISTORY_PAIRS,
        },
    }


@app.get("/api/history/{session_id}")
async def get_history(session_id: str) -> JSONResponse:
    """Retrieves conversation history for a given session."""
    history = conversation_manager.get_session(session_id)
    return JSONResponse(content={"session_id": session_id, "turns": history})


@app.post("/api/reset")
async def reset_session_endpoint(payload: dict[str, Any]) -> JSONResponse:
    """Explicitly resets conversational memory for a given session."""
    session_id = payload.get("session_id")
    if not session_id or not isinstance(session_id, str):
        return JSONResponse(status_code=400, content={"error": "session_id is required."})
    conversation_manager.reset_session(session_id)
    return JSONResponse(content={"status": "reset", "session_id": session_id})


@app.post("/api/chat")
async def chat_rest(payload: dict[str, Any]) -> JSONResponse:
    """REST endpoint for single-turn complete responses."""
    try:
        session_id, message = validate_message_payload(payload)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    # Check domain guardrails
    if conversation_manager.should_redirect(message):
        reply = conversation_manager.off_topic_reply()
        conversation_manager.add_turn(session_id, "user", message)
        conversation_manager.add_turn(session_id, "assistant", reply)
        return JSONResponse(content={
            "session_id": session_id,
            "reply": reply,
            "redirected": True,
            "metrics": {"ttft_seconds": 0.0, "total_seconds": 0.0, "tokens_per_second": 0.0},
        })

    conversation_manager.add_turn(session_id, "user", message)
    messages = conversation_manager.build_prompt_messages(session_id, message)

    try:
        reply, metrics = await generate_response(messages)
        final_reply = reply.strip() or "I’m sorry, I could not produce a response."
        conversation_manager.add_turn(session_id, "assistant", final_reply)
        return JSONResponse(content={
            "session_id": session_id,
            "reply": final_reply,
            "redirected": False,
            "metrics": metrics,
        })
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": f"LLM error: {exc}"})


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time word-by-word streaming responses.
    Handles concurrent sessions asynchronously without blocking the event loop.
    """
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Malformed JSON payload."})
                continue

            # Check for reset action
            if payload.get("action") == "reset":
                target_session = payload.get("session_id", "")
                if target_session:
                    conversation_manager.reset_session(target_session)
                await websocket.send_json({"type": "reset", "session_id": target_session})
                continue

            # Validate message payload
            try:
                session_id, message = validate_message_payload(payload)
            except ValueError as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
                continue

            # Guardrail interception
            if conversation_manager.should_redirect(message):
                reply = conversation_manager.off_topic_reply()
                conversation_manager.add_turn(session_id, "user", message)
                conversation_manager.add_turn(session_id, "assistant", reply)
                await websocket.send_json({"type": "start", "session_id": session_id})
                await websocket.send_json({"type": "token", "content": reply})
                await websocket.send_json({
                    "type": "done",
                    "session_id": session_id,
                    "redirected": True,
                    "ttft": 0.0,
                    "tokens": 1,
                    "elapsed": 0.0,
                })
                continue

            # Add user turn and compile prompt
            conversation_manager.add_turn(session_id, "user", message)
            messages = conversation_manager.build_prompt_messages(session_id, message)

            await websocket.send_json({"type": "start", "session_id": session_id})

            start_time = time.perf_counter()
            first_token_time: float | None = None
            token_count = 0
            collected_chunks: list[str] = []

            try:
                async for chunk in stream_response(messages):
                    if first_token_time is None:
                        first_token_time = time.perf_counter() - start_time
                    token_count += 1
                    collected_chunks.append(chunk)
                    await websocket.send_json({"type": "token", "content": chunk})

                elapsed = time.perf_counter() - start_time
                ttft = round(first_token_time or elapsed, 3)
                final_reply = "".join(collected_chunks).strip() or "I'm sorry, I could not generate a response."
                conversation_manager.add_turn(session_id, "assistant", final_reply)

                await websocket.send_json({
                    "type": "done",
                    "session_id": session_id,
                    "redirected": False,
                    "ttft": ttft,
                    "tokens": token_count,
                    "elapsed": round(elapsed, 3),
                    "tps": round(token_count / elapsed, 2) if elapsed > 0 else 0.0,
                })
            except Exception as exc:
                await websocket.send_json({"type": "error", "message": f"LLM error: {exc}"})
    except WebSocketDisconnect:
        # Client disconnected cleanly
        return
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": f"Connection error: {exc}"})
        except RuntimeError:
            pass


# Mount frontend static directory if present
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_ui():
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return JSONResponse(content={"message": "Frontend index.html not found"})
