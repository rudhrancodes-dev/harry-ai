"""Base class for Harry's specialist sub-agents (Hermes-style executors)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AgentResult:
    speech: str
    handled: bool


class Agent(ABC):
    name: str = "agent"
    description: str = ""
    triggers: tuple[str, ...] = ()

    def matches(self, utterance: str) -> bool:
        text = utterance.lower()
        return any(trigger in text for trigger in self.triggers)

    @abstractmethod
    def handle(self, utterance: str) -> AgentResult: ...
