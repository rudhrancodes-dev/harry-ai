"""Specialist agents. ConversationAgent / CodeAgent are lazily imported so
the optional Brain backend deps don't need to be present for `pytest`."""
from __future__ import annotations

from .base import Agent, AgentResult
from .computer_agent import ComputerAgent
from .orchestrator import Orchestrator
from .system_agent import SystemAgent
from .time_agent import TimeAgent
from .weather_agent import WeatherAgent

__all__ = [
    "Agent", "AgentResult", "Orchestrator",
    "SystemAgent", "TimeAgent", "WeatherAgent",
    "ComputerAgent", "ConversationAgent", "CodeAgent",
]


def __getattr__(name: str):
    if name == "ConversationAgent":
        from .conversation_agent import ConversationAgent
        return ConversationAgent
    if name == "CodeAgent":
        from .code_agent import CodeAgent
        return CodeAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
