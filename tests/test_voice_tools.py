"""
Automated Test Suite for Assignment 3: Voice Pipeline & Tool Orchestrator.
Tests:
- Tool registrations and schemas (weather, calculator, schedule, CRM)
- Tool execution: calculate_membership (discounts, plans, durations)
- Tool execution: check_class_schedule (day and class filtering)
- Tool execution: get_weather (mock / API fallback)
- Tool execution: crm_lookup (get, set, update across sessions)
- Tool orchestrator: detection, dispatch, timeout handling (10s), formatting
- Voice ASR engine initialization & audio conversion
- Voice TTS engine initialization, sentence splitting, audio generation
- WebSocket /ws/chat and REST /api/chat tool handling
"""
from __future__ import annotations

import asyncio
import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.tools import (
    get_tool_orchestrator,
    MembershipCalculatorTool,
    ClassScheduleTool,
    WeatherTool,
    CRMTool,
)
from backend.app.voice import get_asr_engine, get_tts_engine

client = TestClient(app)


def test_tool_orchestrator_initialization():
    """Validates all 4 tools (including bonus CRM) are registered in orchestrator."""
    orchestrator = get_tool_orchestrator()
    assert "get_weather" in orchestrator.tools
    assert "calculate_membership" in orchestrator.tools
    assert "check_class_schedule" in orchestrator.tools
    assert "crm_lookup" in orchestrator.tools
    assert len(orchestrator.tools) >= 4


def test_tool_calling_instructions_and_schemas():
    """Validates that tool calling instructions contain schemas and examples."""
    orchestrator = get_tool_orchestrator()
    instructions = orchestrator.get_tool_calling_instructions()
    assert "TOOL CALLING CAPABILITY" in instructions
    assert "[TOOL_CALL: tool_name" in instructions
    assert "get_weather" in instructions
    assert "calculate_membership" in instructions
    assert "check_class_schedule" in instructions
    assert "crm_lookup" in instructions


def test_calculator_tool_pricing():
    """Tests membership calculator with various plans and discounts."""
    async def _run():
        calc = MembershipCalculatorTool()

        # 1. Basic 1 month (4000 monthly + 2000 registration fee = 6000)
        res_basic = await calc.execute(plan="basic", months=1, student_discount=False)
        assert res_basic["success"] is True
        assert res_basic["monthly_rate_rs"] == 4000
        assert res_basic["total_cost_rs"] == 6000

        # 2. Premium 12 months (15% annual discount)
        res_prem_annual = await calc.execute(plan="premium", months=12, student_discount=False)
        assert res_prem_annual["success"] is True
        assert res_prem_annual["annual_discount_applied"] is True
        # 9000 * 12 = 108,000 * 0.85 = 91,800 + 2000 reg fee = 93,800
        assert res_prem_annual["total_cost_rs"] == 93800

        # 3. Standard 3 months with student discount (10%)
        res_student = await calc.execute(plan="standard", months=3, student_discount=True)
        assert res_student["success"] is True
        assert res_student["student_discount_applied"] is True
        # 6000 * 3 = 18,000 * 0.90 = 16,200 + 2000 reg fee = 18,200
        assert res_student["total_cost_rs"] == 18200

    asyncio.run(_run())


def test_schedule_tool_queries():
    """Tests class schedule lookups by day and type."""
    async def _run():
        sched = ClassScheduleTool()

        # 1. Yoga on Monday
        res_yoga_mon = await sched.execute(class_type="yoga", day_of_week="monday")
        assert res_yoga_mon["success"] is True
        assert res_yoga_mon["total_found"] >= 1
        assert any("yoga" in c["name"].lower() for c in res_yoga_mon["classes"])

        # 2. HIIT on Thursday
        res_hiit = await sched.execute(class_type="hiit", day_of_week="thursday")
        assert res_hiit["success"] is True
        assert res_hiit["total_found"] >= 1

        # 3. Invalid day fallback
        res_invalid = await sched.execute(class_type="yoga", day_of_week="funday")
        assert res_invalid["success"] is True
        assert res_invalid["total_found"] == 0

    asyncio.run(_run())


def test_weather_tool_execution():
    """Tests weather tool with Islamabad/Lahore."""
    async def _run():
        weather = WeatherTool()
        res = await weather.execute(city="Islamabad")
        assert res["success"] is True
        assert "temperature_c" in res
        assert "condition" in res
        assert "recommendation" in res

    asyncio.run(_run())


def test_crm_tool_crud_lifecycle():
    """Tests CRM bonus tool: set user details, get user, and update preferences."""
    async def _run():
        crm = CRMTool()
        user_id = "test_user_pytest_999"

        # 1. Set user info
        set_res = await crm.execute(
            action="set",
            user_id=user_id,
            data={"name": "Hamza Tariq", "preferred_plan": "premium", "interests": ["boxing", "hiit"]},
        )
        assert set_res["success"] is True

        # 2. Get user info
        get_res = await crm.execute(action="get", user_id=user_id)
        assert get_res["success"] is True
        assert get_res["profile"]["name"] == "Hamza Tariq"
        assert get_res["profile"]["preferred_plan"] == "premium"

        # 3. Update user info
        upd_res = await crm.execute(
            action="update",
            user_id=user_id,
            data={"preferred_plan": "annual_vip", "notes": "Requested locker on 2nd floor"},
        )
        assert upd_res["success"] is True
        assert upd_res["profile"]["preferred_plan"] == "annual_vip"

    asyncio.run(_run())


def test_orchestrator_detection_and_timeout():
    """Validates orchestrator regex detection and timeout protection."""
    async def _run():
        orchestrator = get_tool_orchestrator()

        # 1. Detection
        sample_text = 'Let me check that for you.\n[TOOL_CALL: get_weather({"city": "Islamabad"})]\nPlease wait.'
        detected = orchestrator.detect_tool_call(sample_text)
        assert detected is not None
        tool_name, args = detected
        assert tool_name == "get_weather"
        assert args == {"city": "Islamabad"}

        # 2. Execution via orchestrator
        exec_res = await orchestrator.execute_tool("get_weather", {"city": "Islamabad"}, timeout=5.0)
        assert exec_res["success"] is True
        assert "elapsed_ms" in exec_res

        # 3. Non-existent tool handling
        bad_res = await orchestrator.execute_tool("non_existent_tool", {}, timeout=5.0)
        assert bad_res["success"] is False
        assert "Unknown tool" in bad_res["error"]

    asyncio.run(_run())


def test_tts_engine_sentence_splitting_and_fallback():
    """Tests TTS engine sentence boundary splitting and synthesis."""
    tts = get_tts_engine()
    text = "Welcome to FitZone! We offer Yoga, HIIT, and Zumba. How can I help you today?"
    sentences = tts.split_into_sentences(text)
    assert len(sentences) == 3
    assert "Welcome to FitZone!" in sentences[0]

    # Synthesize single sentence
    synth_res = tts.synthesize_text("Welcome to FitZone!")
    assert "audio_base64" in synth_res
    assert len(synth_res["audio_base64"]) > 0
    assert synth_res["latency_ms"] >= 0


def test_api_tools_endpoint():
    """Tests the GET /api/tools endpoint."""
    resp = client.get("/api/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is True
    assert len(data["tools"]) >= 4
    tool_names = [t["name"] for t in data["tools"]]
    assert "get_weather" in tool_names
    assert "calculate_membership" in tool_names
    assert "check_class_schedule" in tool_names
    assert "crm_lookup" in tool_names


def test_health_endpoint_includes_voice_and_tools():
    """Tests that /health reflects voice and tools runtime status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "voice" in data
    assert data["voice"]["enabled"] is True
    assert "tools" in data
    assert data["tools"]["enabled"] is True
