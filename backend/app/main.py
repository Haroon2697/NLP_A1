from __future__ import annotations

import asyncio
import base64
import json
import time
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import (
    BACKEND_DIR,
    ENABLE_TOOLS,
    ENABLE_VOICE,
    FRONTEND_DIR,
    MAX_HISTORY_PAIRS,
    MAX_RESPONSE_TOKENS,
    NUM_CTX,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    TEMPERATURE,
    TOOL_TIMEOUT_SECONDS,
)
from .conversation_manager import ConversationManager
from .llm_client import generate_response, stream_response
from .retrieval import get_retrieval_engine

app = FastAPI(
    title="FitZone Gym Assistant API",
    description="Conversational AI Backend for FitZone Gym with Local RAG, Voice Pipeline, and Tool Orchestrator.",
    version="3.0.0",
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
    """Health check endpoint providing runtime, model, and RAG configuration."""
    engine = get_retrieval_engine()
    doc_count = engine.collection.count() if engine.collection else 0

    # Tool status
    tool_status = {}
    if ENABLE_TOOLS:
        try:
            from .tools import get_tool_orchestrator
            orch = get_tool_orchestrator()
            tool_status = {
                "enabled": True,
                "tools": list(orch.tools.keys()),
                "timeout_seconds": TOOL_TIMEOUT_SECONDS,
            }
        except Exception:
            tool_status = {"enabled": False, "error": "Tool orchestrator failed to load"}

    return {
        "status": "ok",
        "service": "FitAssist RAG + Voice + Tools Backend",
        "version": "3.0.0",
        "model": OLLAMA_MODEL,
        "ollama_url": OLLAMA_BASE_URL,
        "context_window": NUM_CTX,
        "max_history_pairs": MAX_HISTORY_PAIRS,
        "temperature": TEMPERATURE,
        "rag": {
            "status": "initialized" if engine.is_initialized else "uninitialized",
            "chunks_indexed": doc_count,
            "cache": engine.cache.stats(),
        },
        "voice": {"enabled": ENABLE_VOICE},
        "tools": tool_status,
    }


@app.get("/api/rag/stats")
async def rag_stats() -> dict[str, Any]:
    """Provides vector database collection and query cache statistics."""
    engine = get_retrieval_engine()
    doc_count = engine.collection.count() if engine.collection else 0
    return {
        "vector_store": "ChromaDB (Persistent CPU)",
        "embedding_model": "all-MiniLM-L6-v2 (ONNX)",
        "indexed_chunks": doc_count,
        "cache": engine.cache.stats(),
        "hybrid_search": "BM25Okapi + Reciprocal Rank Fusion",
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
            "typical_retrieval_ms": 45.0,
        },
        "limits": {
            "max_response_tokens": MAX_RESPONSE_TOKENS,
            "context_tokens": NUM_CTX,
            "max_history_pairs": MAX_HISTORY_PAIRS,
        },
    }


@app.get("/api/tools")
async def get_tools_info() -> dict[str, Any]:
    """Returns information about available tools and their schemas."""
    if not ENABLE_TOOLS:
        return {"enabled": False, "tools": []}
    try:
        from .tools import get_tool_orchestrator
        orch = get_tool_orchestrator()
        tools_info = []
        for name, tool in orch.tools.items():
            tools_info.append({
                "name": name,
                "description": tool.description,
                "parameters_schema": tool.parameters_schema,
            })
        return {"enabled": True, "tools": tools_info}
    except Exception as exc:
        return {"enabled": False, "error": str(exc)}


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
    """REST endpoint for single-turn complete responses with RAG grounding."""
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
            "citations": [],
            "retrieval_metrics": {"retrieval_ms": 0.0, "status": "redirected"},
            "metrics": {"ttft_seconds": 0.0, "total_seconds": 0.0, "tokens_per_second": 0.0},
        })

    conversation_manager.add_turn(session_id, "user", message)
    messages, citations, ret_metrics = await conversation_manager.async_build_prompt_messages(
        session_id, message
    )

    try:
        reply, metrics = await generate_response(messages)
        final_reply = reply.strip() or "I'm sorry, I could not produce a response."

        # Check if the LLM wants to call a tool
        if ENABLE_TOOLS:
            final_reply, tool_metrics = await _handle_tool_calls(
                final_reply, messages, session_id
            )
            if tool_metrics:
                metrics["tool_calls"] = tool_metrics

        conversation_manager.add_turn(session_id, "assistant", final_reply)
        return JSONResponse(content={
            "session_id": session_id,
            "reply": final_reply,
            "redirected": False,
            "citations": citations,
            "retrieval_metrics": ret_metrics,
            "metrics": metrics,
        })
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": f"LLM error: {exc}"})


async def _handle_tool_calls(
    llm_output: str, messages: list[dict], session_id: str,
    max_rounds: int = 3,
) -> tuple[str, list[dict]]:
    """
    Detects and executes tool calls in LLM output.
    Re-feeds tool results back to the LLM for a final natural response.
    Supports up to max_rounds of tool calls to prevent infinite loops.
    """
    from .tools import get_tool_orchestrator
    orchestrator = get_tool_orchestrator()
    tool_metrics = []

    current_output = llm_output
    current_messages = list(messages)

    for round_num in range(max_rounds):
        parsed = orchestrator.detect_tool_call(current_output)
        if not parsed:
            break

        tool_name, arguments = parsed

        # Execute the tool
        result = await orchestrator.execute_tool(
            tool_name, arguments, timeout=TOOL_TIMEOUT_SECONDS
        )
        tool_metrics.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "success": result.get("success", False),
            "elapsed_ms": result.get("elapsed_ms", 0),
            "round": round_num + 1,
        })

        # Format result and re-feed to LLM
        formatted_result = orchestrator.format_tool_result(result)

        # Add the LLM's tool call as assistant message
        current_messages.append({"role": "assistant", "content": current_output})
        # Add the tool result as a system/user message
        current_messages.append({"role": "user", "content": formatted_result})

        # Get a new LLM response incorporating the tool result
        try:
            new_reply, _ = await generate_response(current_messages)
            current_output = new_reply.strip() or "I'm sorry, I could not process the tool result."
        except Exception as exc:
            current_output = f"I encountered an error processing the result: {exc}"
            break

    return current_output, tool_metrics


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time streaming responses with RAG grounding.
    Preserves exact backward-compatible protocol from Assignment 1 while providing
    source citation chips and retrieval latency telemetry.

    A3 additions: Tool call detection in streaming, TTS audio streaming.
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

            # Check for voice audio message
            if payload.get("type") == "voice_audio":
                await _handle_voice_message(websocket, payload)
                continue

            # Validate message payload
            try:
                session_id, message = validate_message_payload(payload)
            except ValueError as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
                continue

            # Process as text message
            await _process_text_message(websocket, session_id, message)

    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": f"Connection error: {exc}"})
        except RuntimeError:
            pass


async def _handle_voice_message(websocket: WebSocket, payload: dict) -> None:
    """
    Handles incoming voice audio from the browser.
    Transcribes using local ASR, then processes as a text message.
    """
    session_id = payload.get("session_id", "")
    audio_b64 = payload.get("audio_data", "")
    audio_format = payload.get("format", "wav")
    voice_mode = payload.get("voice_mode", True)

    if not session_id or not audio_b64:
        await websocket.send_json({"type": "error", "message": "session_id and audio_data required."})
        return

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception:
        await websocket.send_json({"type": "error", "message": "Invalid base64 audio data."})
        return

    # Transcribe using ASR
    asr_start = time.perf_counter()
    try:
        from .voice import get_asr_engine
        asr = get_asr_engine()

        if audio_format == "wav":
            result = await asyncio.to_thread(asr.transcribe_wav, audio_bytes)
        else:
            result = await asr.async_transcribe(audio_bytes)

        transcript = result.get("text", "").strip()
        asr_latency_ms = round((time.perf_counter() - asr_start) * 1000, 2)

        # Send transcript back to client
        await websocket.send_json({
            "type": "transcript",
            "text": transcript,
            "is_final": True,
            "asr_latency_ms": asr_latency_ms,
            "asr_details": {
                "engine_latency_ms": result.get("latency_ms", 0),
                "audio_duration_ms": result.get("audio_duration_ms", 0),
                "language": result.get("language", "en"),
            },
        })

        if not transcript:
            err_msg = result.get("error") or "No clear speech detected. Please speak directly into your microphone and try again."
            await websocket.send_json({
                "type": "error",
                "message": err_msg
            })
            return

        # Process the transcript as a text message (with TTS if voice_mode)
        await _process_text_message(
            websocket, session_id, transcript, voice_mode=voice_mode
        )

    except Exception as exc:
        await websocket.send_json({
            "type": "error",
            "message": f"ASR error: {str(exc)}"
        })


async def _process_text_message(
    websocket: WebSocket, session_id: str, message: str,
    voice_mode: bool = False,
) -> None:
    """
    Core message processing pipeline used by both text and voice modes.
    Handles guardrails, RAG retrieval, LLM streaming, tool calls, and TTS.
    """
    # Guardrail interception
    if conversation_manager.should_redirect(message):
        reply = conversation_manager.off_topic_reply()
        conversation_manager.add_turn(session_id, "user", message)
        conversation_manager.add_turn(session_id, "assistant", reply)
        await websocket.send_json({"type": "start", "session_id": session_id})
        await websocket.send_json({"type": "token", "content": reply})

        # TTS for voice mode
        if voice_mode:
            await _stream_tts(websocket, reply)

        await websocket.send_json({
            "type": "done",
            "session_id": session_id,
            "redirected": True,
            "ttft": 0.0,
            "tokens": 1,
            "elapsed": 0.0,
            "retrieval_ms": 0.0,
            "citations": [],
        })
        return

    # Record user turn and retrieve grounded context
    conversation_manager.add_turn(session_id, "user", message)
    messages, citations, ret_metrics = await conversation_manager.async_build_prompt_messages(
        session_id, message
    )

    await websocket.send_json({"type": "start", "session_id": session_id})

    # Send source citations event if chunks were retrieved
    if citations:
        await websocket.send_json({
            "type": "citations",
            "session_id": session_id,
            "sources": citations,
            "retrieval_ms": ret_metrics.get("retrieval_ms", 0.0),
            "cached": ret_metrics.get("cached", False),
        })

    start_time = time.perf_counter()
    first_token_time: float | None = None
    token_count = 0
    collected_chunks: list[str] = []
    tool_metrics: list[dict] = []

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

        # Check for tool calls in the complete response
        if ENABLE_TOOLS:
            final_reply, tool_metrics = await _handle_tool_calls_streaming(
                final_reply, messages, session_id, websocket, voice_mode
            )

        conversation_manager.add_turn(session_id, "assistant", final_reply)

        # Stream TTS for voice mode (if no tool call already handled it)
        if voice_mode and not tool_metrics:
            await _stream_tts(websocket, final_reply)

        done_payload = {
            "type": "done",
            "session_id": session_id,
            "redirected": False,
            "ttft": ttft,
            "tokens": token_count,
            "elapsed": round(elapsed, 3),
            "tps": round(token_count / elapsed, 2) if elapsed > 0 else 0.0,
            "retrieval_ms": ret_metrics.get("retrieval_ms", 0.0),
            "cached": ret_metrics.get("cached", False),
            "citations": citations,
        }
        if tool_metrics:
            done_payload["tool_calls"] = tool_metrics

        await websocket.send_json(done_payload)
    except Exception as exc:
        await websocket.send_json({"type": "error", "message": f"LLM error: {exc}"})


async def _handle_tool_calls_streaming(
    llm_output: str, messages: list[dict], session_id: str,
    websocket: WebSocket, voice_mode: bool = False,
    max_rounds: int = 3,
) -> tuple[str, list[dict]]:
    """
    Streaming version of tool call handling.
    Sends the tool result response tokens to the websocket as they stream.
    """
    from .tools import get_tool_orchestrator
    orchestrator = get_tool_orchestrator()
    tool_metrics = []

    current_output = llm_output
    current_messages = list(messages)

    for round_num in range(max_rounds):
        parsed = orchestrator.detect_tool_call(current_output)
        if not parsed:
            break

        tool_name, arguments = parsed

        # Notify client that a tool is being called
        await websocket.send_json({
            "type": "tool_call",
            "tool_name": tool_name,
            "arguments": arguments,
            "round": round_num + 1,
        })

        # Execute the tool
        result = await orchestrator.execute_tool(
            tool_name, arguments, timeout=TOOL_TIMEOUT_SECONDS
        )

        # Notify client of tool result
        await websocket.send_json({
            "type": "tool_result",
            "tool_name": tool_name,
            "success": result.get("success", False),
            "elapsed_ms": result.get("elapsed_ms", 0),
        })

        tool_metrics.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "success": result.get("success", False),
            "elapsed_ms": result.get("elapsed_ms", 0),
            "round": round_num + 1,
        })

        # Format result and re-feed to LLM
        formatted_result = orchestrator.format_tool_result(result)
        current_messages.append({"role": "assistant", "content": current_output})
        current_messages.append({"role": "user", "content": formatted_result})

        # Stream the new LLM response incorporating the tool result
        try:
            new_chunks = []
            async for chunk in stream_response(current_messages):
                new_chunks.append(chunk)
                await websocket.send_json({"type": "token", "content": chunk})

            current_output = "".join(new_chunks).strip() or "I'm sorry, I could not process the tool result."
        except Exception as exc:
            current_output = f"I encountered an error processing the result: {exc}"
            break

    # TTS for the final tool-processed response
    if voice_mode and tool_metrics:
        await _stream_tts(websocket, current_output)

    return current_output, tool_metrics


async def _stream_tts(websocket: WebSocket, text: str) -> None:
    """
    Synthesizes text to speech sentence-by-sentence and streams
    audio chunks back to the client for sequential playback.
    """
    if not ENABLE_VOICE:
        return

    try:
        from .voice import get_tts_engine
        tts = get_tts_engine()

        sentences = tts.split_into_sentences(text)
        tts_start = time.perf_counter()

        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            result = await tts.async_synthesize(sentence)
            audio_b64 = result.get("audio_base64", "")

            if audio_b64:
                await websocket.send_json({
                    "type": "tts_audio",
                    "audio_data": audio_b64,
                    "sentence_index": i,
                    "total_sentences": len(sentences),
                    "duration_ms": result.get("duration_ms", 0),
                    "latency_ms": result.get("latency_ms", 0),
                    "engine": result.get("engine", "unknown"),
                })

        tts_total_ms = round((time.perf_counter() - tts_start) * 1000, 2)
        await websocket.send_json({
            "type": "tts_done",
            "total_latency_ms": tts_total_ms,
            "sentences_synthesized": len(sentences),
        })

    except Exception as exc:
        await websocket.send_json({
            "type": "tts_error",
            "message": f"TTS error: {str(exc)}",
        })


# Mount frontend static directory if present
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_ui():
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return JSONResponse(content={"message": "Frontend index.html not found"})
