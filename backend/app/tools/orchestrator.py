"""
Tool Orchestrator — Detects tool calls in LLM output, dispatches tools,
handles timeouts, and feeds results back into the conversation.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .weather_tool import WeatherTool
from .calculator_tool import MembershipCalculatorTool
from .schedule_tool import ClassScheduleTool
from .crm_tool import CRMTool

logger = logging.getLogger("fitzone.tools.orchestrator")

# Default timeout for all tool calls (seconds)
TOOL_TIMEOUT_SECONDS = 10


class ToolOrchestrator:
    """
    Central dispatcher for all FitZone tools. Registers tools, detects tool calls
    in LLM output, executes them with timeouts, and formats results for the LLM.
    """

    def __init__(self) -> None:
        self.tools: Dict[str, Any] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Registers all available FitZone tools."""
        weather = WeatherTool()
        calculator = MembershipCalculatorTool()
        schedule = ClassScheduleTool()
        crm = CRMTool()

        self.tools[weather.name] = weather
        self.tools[calculator.name] = calculator
        self.tools[schedule.name] = schedule
        self.tools[crm.name] = crm

        logger.info(f"Tool Orchestrator initialized with {len(self.tools)} tools: {list(self.tools.keys())}")

    def get_tools_description(self) -> str:
        """
        Returns a formatted description of all available tools and their schemas
        for inclusion in the LLM system prompt.
        """
        descriptions = []
        for name, tool in self.tools.items():
            desc = (
                f"### Tool: {name}\n"
                f"Description: {tool.description}\n"
                f"Parameters: {json.dumps(tool.parameters_schema, indent=2)}\n"
            )
            descriptions.append(desc)

        return "\n".join(descriptions)

    def get_tool_calling_instructions(self) -> str:
        """
        Returns instructions for the LLM on how to call tools.
        This is appended to the system prompt.
        """
        tools_desc = self.get_tools_description()
        return f"""
### TOOL CALLING CAPABILITY
You have access to the following tools. When a user's request requires real-time data, calculations, schedule lookups, or user profile management, you MUST use the appropriate tool.

To call a tool, output EXACTLY this format on its own line:
[TOOL_CALL: tool_name({{"param1": "value1", "param2": "value2"}})]

IMPORTANT RULES:
1. The tool call MUST be on its own line, exactly matching the format above.
2. Arguments MUST be valid JSON inside the parentheses.
3. Only call ONE tool at a time.
4. After a tool call, STOP generating. Wait for the tool result before continuing.
5. When you receive a tool result, incorporate it naturally into your response.
6. If a tool call fails, explain the issue politely and suggest alternatives.

AVAILABLE TOOLS:
{tools_desc}

TOOL USAGE EXAMPLES:
- User asks "What's the weather in Islamabad?":
  [TOOL_CALL: get_weather({{"city": "Islamabad"}})]

- User asks "How much would 6 months of Premium membership cost with student discount?":
  [TOOL_CALL: calculate_membership({{"plan": "premium", "months": 6, "student_discount": true}})]

- User asks "What yoga classes are available on Monday?":
  [TOOL_CALL: check_class_schedule({{"class_type": "yoga", "day_of_week": "monday"}})]

- To store a user's name for CRM:
  [TOOL_CALL: crm_lookup({{"action": "set", "user_id": "session-123", "data": {{"name": "Ali", "preferred_plan": "premium"}}}})]
"""

    def detect_tool_call(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Parses LLM output to detect a tool call.
        Returns (tool_name, arguments) if found, else None.
        """
        # Pattern: [TOOL_CALL: tool_name({"key": "value"})]
        pattern = r'\[TOOL_CALL:\s*(\w+)\((\{.*?\})\)\]'
        match = re.search(pattern, text, re.DOTALL)

        if not match:
            return None

        tool_name = match.group(1).strip()
        try:
            arguments = json.loads(match.group(2))
        except json.JSONDecodeError as exc:
            logger.warning(f"Failed to parse tool arguments: {exc}")
            return None

        return tool_name, arguments

    async def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any],
        timeout: float = TOOL_TIMEOUT_SECONDS
    ) -> Dict[str, Any]:
        """
        Executes a tool by name with the given arguments.
        Applies a timeout and handles errors gracefully.
        """
        start_time = time.perf_counter()

        if tool_name not in self.tools:
            available = ", ".join(self.tools.keys())
            return {
                "success": False,
                "error": f"Unknown tool '{tool_name}'. Available tools: {available}",
                "elapsed_ms": 0.0,
            }

        tool = self.tools[tool_name]

        try:
            result = await asyncio.wait_for(
                tool.execute(arguments),
                timeout=timeout,
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            result["elapsed_ms"] = elapsed_ms
            result["tool_name"] = tool_name
            logger.info(f"Tool '{tool_name}' executed in {elapsed_ms}ms")
            return result

        except asyncio.TimeoutError:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning(f"Tool '{tool_name}' timed out after {timeout}s")
            return {
                "success": False,
                "error": f"Tool '{tool_name}' timed out after {timeout} seconds.",
                "tool_name": tool_name,
                "elapsed_ms": elapsed_ms,
            }
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"Tool '{tool_name}' error: {exc}", exc_info=True)
            return {
                "success": False,
                "error": f"Tool error: {str(exc)}",
                "tool_name": tool_name,
                "elapsed_ms": elapsed_ms,
            }

    def format_tool_result(self, result: Dict[str, Any]) -> str:
        """Formats tool result for injection back into the LLM conversation."""
        tool_name = result.get("tool_name", "unknown")
        elapsed = result.get("elapsed_ms", 0)

        if result.get("success"):
            # Remove metadata fields from the display
            display = {k: v for k, v in result.items()
                       if k not in ("success", "elapsed_ms", "tool_name")}
            return (
                f"[TOOL_RESULT from {tool_name} ({elapsed}ms)]:\n"
                f"{json.dumps(display, indent=2, ensure_ascii=False)}\n"
                f"[END_TOOL_RESULT]\n\n"
                f"Now incorporate this tool result into a natural, helpful response for the user."
            )
        else:
            error_msg = result.get("error", "Unknown error")
            return (
                f"[TOOL_RESULT from {tool_name} — FAILED ({elapsed}ms)]:\n"
                f"Error: {error_msg}\n"
                f"[END_TOOL_RESULT]\n\n"
                f"The tool call failed. Explain the issue politely and suggest alternatives."
            )


# Singleton instance
_orchestrator_instance: Optional[ToolOrchestrator] = None


def get_tool_orchestrator() -> ToolOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = ToolOrchestrator()
    return _orchestrator_instance
