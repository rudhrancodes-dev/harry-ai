"""Catch-all conversational agent — defers to whichever Brain backend is loaded."""
from __future__ import annotations

from ..brain import Brain
from ..persona import build_persona
from .base import Agent, AgentResult


class ConversationAgent(Agent):
    name = "conversation"
    description = "Free-form conversation routed through the configured Brain backend."
    triggers = ()

    def __init__(self, brain: Brain) -> None:
        self._brain = brain
        self._persona = build_persona()

    def matches(self, utterance: str) -> bool:
        return True

    def handle(self, utterance: str) -> AgentResult:
        text = self._brain.complete(self._persona, utterance) \
            or "I am not sure how to answer that, sir."
        return AgentResult(speech=text, handled=True)
