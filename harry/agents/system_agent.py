"""System control — open apps, control volume, etc. Only safe, read-mostly actions."""
from __future__ import annotations

import platform
import subprocess

from .base import Agent, AgentResult


SAFE_APPS = {
    "safari": "Safari",
    "chrome": "Google Chrome",
    "finder": "Finder",
    "terminal": "Terminal",
    "notes": "Notes",
    "calendar": "Calendar",
    "spotify": "Spotify",
}


class SystemAgent(Agent):
    name = "system"
    description = "Opens approved desktop applications on macOS."
    triggers = ("open ", "launch ", "start ")

    def handle(self, utterance: str) -> AgentResult:
        text = utterance.lower()
        for keyword, app in SAFE_APPS.items():
            if keyword in text:
                return self._open(app)
        return AgentResult(
            speech="I am not permitted to open that application, sir.",
            handled=True,
        )

    @staticmethod
    def _open(app_name: str) -> AgentResult:
        if platform.system() != "Darwin":
            return AgentResult(
                speech="App launching is only supported on macOS at the moment, sir.",
                handled=True,
            )
        try:
            subprocess.run(["open", "-a", app_name], check=True, timeout=5)
        except (subprocess.SubprocessError, FileNotFoundError):
            return AgentResult(
                speech=f"I could not open {app_name}, sir.",
                handled=True,
            )
        return AgentResult(speech=f"Opening {app_name}, sir.", handled=True)
