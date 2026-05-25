"""Specialist agents. Imported lazily so optional dependencies (anthropic)
are only required for the agents that actually use them."""
from __future__ import annotations

from .base import Agent, AgentResult
from .orchestrator import Orchestrator
from .system_agent import SystemAgent
from .time_agent import TimeAgent
from .weather_agent import WeatherAgent

__all__ = [
    "Agent",
    "AgentResult",
    "Orchestrator",
    "SystemAgent",
    "TimeAgent",
    "WeatherAgent",
    "ConversationAgent",
]


def __getattr__(name: str):
    if name == "ConversationAgent":
        from .conversation_agent import ConversationAgent
        return ConversationAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
