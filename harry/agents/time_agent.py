"""Time and date specialist."""
from __future__ import annotations

from datetime import datetime

from .base import Agent, AgentResult


class TimeAgent(Agent):
    name = "time"
    description = "Tells the current time, date, or day of the week."
    triggers = ("time", "date", "day", "today", "what day")

    def handle(self, utterance: str) -> AgentResult:
        now = datetime.now()
        text = utterance.lower()
        if "date" in text or "today" in text or "day" in text:
            spoken = now.strftime("It is %A the %d of %B, %Y, sir.")
        else:
            spoken = now.strftime("The time is %I:%M %p, sir.").lstrip("0")
        return AgentResult(speech=spoken, handled=True)
