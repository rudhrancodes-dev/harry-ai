"""Hermes-style skill agent — picks the skill whose longest trigger phrase
matches the utterance, then runs either a deterministic handler or routes
the utterance through the LLM brain with a skill-specific prompt."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..agents.base import Agent, AgentResult
from .handlers import HANDLERS
from .registry import SKILLS, Skill

if TYPE_CHECKING:
    from ..brain import Brain


class HermesSkillAgent(Agent):
    name = "hermes-skills"
    description = "Catalogue of 98 narrow skills routed by exact trigger phrase."
    triggers = ()

    def __init__(self, brain: "Brain | None") -> None:
        self._brain = brain
        self._index: list[tuple[str, Skill]] = sorted(
            ((t.lower(), s) for s in SKILLS for t in s.triggers),
            key=lambda pair: -len(pair[0]),
        )

    def matches(self, utterance: str) -> bool:
        return self._best_match(utterance) is not None

    def handle(self, utterance: str) -> AgentResult:
        skill = self._best_match(utterance)
        if skill is None:
            return AgentResult(speech="", handled=False)
        if skill.handler != "llm":
            fn = HANDLERS.get(skill.handler)
            if not fn:
                return AgentResult(
                    speech=f"Skill {skill.id} is misconfigured, sir.", handled=True)
            return AgentResult(speech=fn(utterance), handled=True)
        if self._brain is None:
            return AgentResult(
                speech="I have no language model configured for that, sir.", handled=True)
        text = self._brain.complete(skill.prompt, utterance)
        return AgentResult(speech=text, handled=True)

    def _best_match(self, utterance: str) -> Skill | None:
        u = utterance.lower()
        for trigger, skill in self._index:
            if trigger in u:
                return skill
        return None
