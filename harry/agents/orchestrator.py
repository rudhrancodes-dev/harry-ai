"""Hermes-style orchestrator. Routes utterances to the best specialist agent.

The conversation agent is registered last and matches anything, acting as the
fallback executor whenever no specialist's triggers fire.
"""
from __future__ import annotations

from typing import Sequence

from .base import Agent, AgentResult


class Orchestrator:
    def __init__(self, agents: Sequence[Agent]) -> None:
        if not agents:
            raise ValueError("Orchestrator needs at least one agent.")
        self._agents = list(agents)

    def route(self, utterance: str) -> tuple[Agent, AgentResult]:
        for agent in self._agents:
            if agent.matches(utterance):
                return agent, agent.handle(utterance)
        fallback = self._agents[-1]
        return fallback, fallback.handle(utterance)
