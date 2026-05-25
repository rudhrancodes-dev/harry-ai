"""Catch-all conversational agent — defers to the Claude brain."""
from __future__ import annotations

from ..brain import Brain
from .base import Agent, AgentResult


class ConversationAgent(Agent):
    name = "conversation"
    description = "Free-form conversation, reasoning, and Q&A via Claude."
    triggers = ()

    def __init__(self, brain: Brain) -> None:
        self._brain = brain
        self._history: list[dict[str, str]] = []

    def matches(self, utterance: str) -> bool:
        return True

    def handle(self, utterance: str) -> AgentResult:
        response = self._brain.think(utterance, self._history)
        text = self._extract_text(response["content"])
        self._history.append({"role": "user", "content": utterance})
        self._history.append({"role": "assistant", "content": text})
        if len(self._history) > 12:
            self._history = self._history[-12:]
        return AgentResult(speech=text, handled=True)

    @staticmethod
    def _extract_text(content_blocks) -> str:
        parts = []
        for block in content_blocks:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return " ".join(parts).strip() or "I am not sure how to answer that, sir."
