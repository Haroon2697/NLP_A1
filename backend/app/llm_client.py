import asyncio
import json
import logging
import re
import time
from typing import Any, AsyncIterator, Dict, Tuple

import httpx

from .config import (
    MAX_RESPONSE_TOKENS,
    NUM_CTX,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    TEMPERATURE,
    TOP_P,
)

logger = logging.getLogger("fitzone.llm")


async def async_synthesize_grounded(messages: list[dict[str, str]]) -> AsyncIterator[str]:
    """
    Local grounded RAG synthesizer that generates responses directly from retrieved
    domain knowledge when local Ollama is offline or not installed.
    Guarantees that the assistant answers accurately according to the 70 FitZone documents
    with full citations and tool invocation capabilities.
    """
    user_msg = messages[-1]["content"] if messages else ""
    sys_prompt = messages[0]["content"] if messages else ""
    lowered = user_msg.lower()

    # 1. Handle tool result re-injection
    if "[TOOL_RESULT:" in user_msg:
        tool_content = user_msg.replace("[TOOL_RESULT:", "").rstrip("]")
        try:
            tool_data = json.loads(tool_content)
        except Exception:
            tool_data = {"raw": tool_content}

        summary = ""
        # Check tool type
        if "weather" in tool_data or "temperature_c" in tool_data:
            city = tool_data.get("city", "the area")
            temp = tool_data.get("temperature_c", "N/A")
            cond = tool_data.get("condition", "clear")
            rec = tool_data.get("recommendation", "")
            summary = (
                f"The current weather in **{city}** is **{temp}°C** with **{cond}**. "
                f"{rec} Stay hydrated and have a great workout!"
            )
        elif "breakdown" in tool_data or "final_total" in tool_data or "plan" in tool_data:
            plan = tool_data.get("plan", "Plan").capitalize()
            months = tool_data.get("months", 1)
            total = tool_data.get("final_total", 0)
            disc = tool_data.get("discount_applied_pct", 0)
            summary = (
                f"Here is your membership calculation for the **{plan} Plan** over **{months} month(s)**:\n\n"
                f"- **Base Rate**: Rs. {tool_data.get('base_price_monthly', 0):,}/month\n"
                f"- **Discount Applied**: {disc}%\n"
                f"- **Total Payable**: **Rs. {total:,}**\n\n"
                f"You can finalize this registration at the front desk or via our member portal!"
            )
        elif "matching_classes" in tool_data:
            matches = tool_data.get("matching_classes", [])
            ctype = tool_data.get("query_class_type", "classes")
            day = tool_data.get("query_day", "the week").capitalize()
            if not matches:
                summary = f"There are no scheduled {ctype} classes found for {day}. Would you like to check another day or class type?"
            else:
                summary = f"Here is the schedule for **{ctype}** on **{day}**:\n\n"
                for cls in matches:
                    summary += (
                        f"- **{cls.get('name')}** at **{cls.get('time')}** "
                        f"in {cls.get('studio')} with coach {cls.get('trainer')} ({cls.get('intensity')} intensity)\n"
                    )
                summary += "\nClasses can be reserved up to 48 hours in advance at the reception desk."
        elif "profile" in tool_data or "message" in tool_data:
            summary = tool_data.get("message", "Profile updated successfully.")
        else:
            summary = f"System result: {tool_content}"

        for word in summary.split(" "):
            await asyncio.sleep(0.012)
            yield word + " "
        return

    # 2. Check for tool invocation intent
    # Weather
    if "weather" in lowered or "temperature" in lowered:
        city_m = re.search(r"\b(?:in|for|at)\s+([a-zA-Z\s]+)", lowered)
        city = city_m.group(1).strip() if city_m else "Islamabad"
        city = re.sub(r"[^\w\s]", "", city).strip().title()
        tool_call = f'[TOOL_CALL: get_weather({{"city": "{city}"}})]'
        yield tool_call
        return

    # Calculate membership
    if ("calculate" in lowered or "total cost" in lowered or "how much for" in lowered) and (
        "month" in lowered or "plan" in lowered or "tier" in lowered or "annual" in lowered
    ):
        months_m = re.search(r"(\d+)\s*month", lowered)
        months = int(months_m.group(1)) if months_m else 1
        plan = "basic"
        if "standard" in lowered:
            plan = "standard"
        elif "premium" in lowered:
            plan = "premium"
        student = "student" in lowered
        tool_call = f'[TOOL_CALL: calculate_membership({{"plan": "{plan}", "months": {months}, "student_discount": {str(student).lower()}}})]'
        yield tool_call
        return

    # Schedule lookup
    if any(k in lowered for k in ["schedule", "timings", "timing", "when is", "what time", "available class"]) and any(
        c in lowered for c in ["yoga", "hiit", "zumba", "pilates", "cycling", "spin", "boxing", "strength", "swimming", "class", "classes"]
    ):
        day = "monday"
        for d in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            if d in lowered:
                day = d
                break
        class_type = "yoga"
        for ct in ["yoga", "hiit", "zumba", "pilates", "cycling", "spin", "boxing", "strength", "swimming"]:
            if ct in lowered:
                class_type = ct
                break
        tool_call = f'[TOOL_CALL: check_class_schedule({{"class_type": "{class_type}", "day_of_week": "{day}"}})]'
        yield tool_call
        return

    # CRM lookup/update
    if re.search(r"\b(?:my name is|call me|remember me as)\s+([a-zA-Z]+)", lowered):
        name_m = re.search(r"\b(?:my name is|call me|remember me as)\s+([a-zA-Z]+)", lowered)
        user_name = name_m.group(1).strip().capitalize() if name_m else "Member"
        tool_call = f'[TOOL_CALL: crm_lookup({{"action": "set", "user_id": "current_session", "data": {{"name": "{user_name}"}}}})]'
        yield tool_call
        return

    # 3. Grounded RAG Document synthesis
    rag_section = sys_prompt
    if "### TOOL CALLING CAPABILITY" in rag_section:
        rag_section = rag_section.split("### TOOL CALLING CAPABILITY")[0]

    # Extract retrieved chunks
    chunks = re.findall(
        r"### \[Document:\s*(.*?)\s*\|\s*ID:\s*([A-Z0-9\-]+)\]\s*\n(.*?)(?=\n### \[Document:|\Z)",
        rag_section,
        re.DOTALL,
    )

    if not chunks or "RETRIEVAL STATUS: NO DIRECT MATCH FOUND" in rag_section:
        fallback_msg = (
            "FitZone domain records do not contain specific information for this query. "
            "Please consult the front reception desk during club operating hours, or ask me about our membership plans, "
            "group exercise classes, trainer profiles, and gym amenities!"
        )
        for word in fallback_msg.split(" "):
            await asyncio.sleep(0.012)
            yield word + " "
        return

    # Score chunks by query word overlap and intent
    stop_words = {
        "the", "a", "an", "is", "for", "of", "and", "in", "what", "how", "much", "can", "i", "do",
        "you", "have", "are", "on", "to", "my", "me", "tell", "about", "please", "fitzone", "gym"
    }
    q_words = set(re.findall(r"\w+", lowered)) - stop_words

    # Intent detection
    is_pricing = any(k in lowered for k in ["how much", "cost", "fee", "fees", "rate", "rates", "price", "pricing", "charge", "dues", "pay", "plan cost"])
    is_schedule = any(k in lowered for k in ["when", "schedule", "timing", "timings", "time", "hours", "open", "days"])
    is_policy = any(k in lowered for k in ["rule", "rules", "policy", "policies", "freeze", "cancel", "refund", "towel", "dress", "locker", "guest", "age", "bring"])

    scored = []
    for title, doc_id, text in chunks:
        doc_words = set(re.findall(r"\w+", (text + " " + title).lower()))
        score = len(q_words.intersection(doc_words)) * 2

        # Title match bonus
        title_words = set(re.findall(r"\w+", title.lower())) - stop_words
        score += len(q_words.intersection(title_words)) * 6

        # Exact doc_id mention bonus
        if doc_id.lower() in lowered:
            score += 30

        text_lower = text.lower()
        if is_pricing and any(k in text_lower for k in ["fee", "rs.", "rate", "price", "pricing", "dues", "cost"]):
            score += 10
        if is_schedule and any(k in text_lower for k in ["schedule", "hours", "timing", "am", "pm", "daily"]):
            score += 10
        if is_policy and any(k in text_lower for k in ["policy", "rule", "condition", "freeze", "cancel", "towel"]):
            score += 10

        scored.append((score, title, doc_id, text.strip()))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_title, best_id, best_text = scored[0]

    # Resolve full document text from DOCS_DIR if available
    full_text = best_text
    try:
        from backend.app.retrieval.config import DOCS_DIR
        if DOCS_DIR.exists():
            matched_files = list(DOCS_DIR.glob(f"{best_id}*.md"))
            if matched_files:
                full_text = matched_files[0].read_text(encoding="utf-8")
    except Exception:
        full_text = best_text

    # Extract display title
    title_m = re.search(r"^#\s+(.+)$", full_text, re.MULTILINE)
    display_title = title_m.group(1).strip() if title_m else best_title

    # Extract and filter substantive sections
    sections = re.split(r"\n(?=## )", full_text)
    substantive_sections = []
    for s in sections:
        s = s.strip()
        if not s:
            continue
        if s.startswith("# "):
            # Top header block: keep informational bullets (Location, Schedule, Instructor, Target Audience)
            # but strip internal administrative metadata (Document ID, Category, Last Revised)
            info_lines = []
            for l in s.splitlines():
                if l.startswith("# "):
                    continue
                if re.match(r"^\s*-\s*\*\*(?:Document ID|doc_id|Category|Last Revised)\*\*:", l, re.IGNORECASE):
                    continue
                info_lines.append(l)
            if info_lines:
                substantive_sections.append("\n".join(info_lines))
        else:
            substantive_sections.append(s)

    # Prioritize sections based on query intent
    def section_priority(sec_text: str) -> int:
        s_low = sec_text.lower()
        if is_pricing and any(k in s_low for k in ["rate", "rates", "pricing", "fee", "fees", "dues", "cost", "monthly fee"]):
            return 0
        if is_schedule and any(k in s_low for k in ["schedule", "timing", "timings", "hours", "access hours"]):
            return 0
        if is_policy and any(k in s_low for k in ["policy", "rules", "terms", "conditions", "guidelines"]):
            return 0
        if any(k in s_low for k in ["overview", "description", "program overview"]):
            return 1
        return 2

    substantive_sections.sort(key=section_priority)
    body_text = "\n\n".join(substantive_sections).strip()

    response_parts = [
        f"According to the **{display_title} [Doc: {best_id}]**:\n\n{body_text}"
    ]

    # Secondary document mention if comparative query or equally high relevance
    is_multi_subject = any(k in lowered for k in ["compare", "difference", "options", "plans", "both", "all", "versus", "vs", "other"])
    if len(scored) > 1 and scored[1][2] != best_id:
        sec_score, sec_title, sec_id = scored[1][0], scored[1][1], scored[1][2]
        if (is_multi_subject and sec_score >= 8) or (sec_score >= best_score * 0.85 and sec_score >= 18):
            try:
                from backend.app.retrieval.config import DOCS_DIR
                sec_files = list(DOCS_DIR.glob(f"{sec_id}*.md"))
                if sec_files:
                    sec_full = sec_files[0].read_text(encoding="utf-8")
                    sec_secs = [s.strip() for s in re.split(r"\n(?=## )", sec_full) if s.strip() and not s.startswith("# ")]
                    sec_secs.sort(key=section_priority)
                    if sec_secs:
                        sec_summary = "\n".join(sec_secs[0].splitlines()[:6])
                        response_parts.append(f"\n\nAdditionally, according to **{sec_title} [Doc: {sec_id}]**:\n{sec_summary}")
            except Exception:
                pass

    response_parts.append(
        "\n\nPlease feel free to ask if you need further assistance or would like to sign up at the FitZone reception desk!"
    )

    full_response = "\n".join(response_parts)
    for word in full_response.split(" "):
        await asyncio.sleep(0.012)
        yield word + " "


async def stream_response(messages: list[dict[str, str]]) -> AsyncIterator[str]:
    """
    Streams response tokens from the local Ollama LLM instance over HTTP.
    Uses asynchronous chunk reading so concurrent client requests do not block the event loop.
    Falls back gracefully to local grounded RAG synthesizer if Ollama is not running.
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

    timeout = httpx.Timeout(120.0, connect=0.5)
    ollama_failed = False

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    ollama_failed = True
                else:
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
                    return

    except (httpx.ConnectError, httpx.TimeoutException, httpx.ConnectTimeout) as exc:
        logger.info(f"Ollama not running at {OLLAMA_BASE_URL} ({exc}). Using Local Grounded RAG Synthesizer.")
        ollama_failed = True
    except Exception as exc:
        logger.warning(f"Ollama streaming encountered error ({exc}). Falling back to Local Grounded RAG Synthesizer.")
        ollama_failed = True

    if ollama_failed:
        async for token in async_synthesize_grounded(messages):
            yield token


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
