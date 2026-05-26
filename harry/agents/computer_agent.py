"""Computer-use agent — Harry's hands on the desktop.

Performs cursor / keyboard / scroll actions via `cliclick` when available,
falling back to AppleScript's System Events. macOS only. Always asks for
explicit phrasing — Harry never moves the cursor speculatively.
"""
from __future__ import annotations

import platform
import re
import shutil
import subprocess

from .base import Agent, AgentResult


class ComputerAgent(Agent):
    name = "computer"
    description = "Drives mouse, keyboard, and scroll on macOS."
    triggers = (
        "click at", "move cursor to", "type out", "press key",
        "scroll up by", "scroll down by", "double click at", "right click at",
    )

    def __init__(self) -> None:
        self._cliclick = shutil.which("cliclick")

    def handle(self, utterance: str) -> AgentResult:
        if platform.system() != "Darwin":
            return AgentResult(
                speech="Computer control is macOS-only for now, sir.", handled=True)
        u = utterance.lower()
        if "click at" in u or "double click at" in u or "right click at" in u:
            return self._click(u)
        if "move cursor to" in u:
            return self._move(u)
        if "type out" in u:
            return self._type(utterance)
        if "press key" in u:
            return self._press(u)
        if "scroll up by" in u or "scroll down by" in u:
            return self._scroll(u)
        return AgentResult(speech="I am not sure how to perform that, sir.", handled=True)

    @staticmethod
    def _coords(text: str) -> tuple[int, int] | None:
        nums = re.findall(r"\d+", text)
        if len(nums) < 2:
            return None
        return int(nums[0]), int(nums[1])

    def _click(self, u: str) -> AgentResult:
        xy = self._coords(u)
        if not xy:
            return AgentResult(speech="I need an x and y coordinate, sir.", handled=True)
        kind = "kc:" if "right click" in u else ("dc:" if "double click" in u else "c:")
        if self._cliclick:
            subprocess.run([self._cliclick, f"{kind}{xy[0]},{xy[1]}"], check=False)
        else:
            return AgentResult(
                speech="Install cliclick for precise clicks, sir. brew install cliclick.",
                handled=True)
        return AgentResult(speech=f"Clicking at {xy[0]}, {xy[1]}, sir.", handled=True)

    def _move(self, u: str) -> AgentResult:
        xy = self._coords(u)
        if not xy:
            return AgentResult(speech="I need an x and y coordinate, sir.", handled=True)
        if self._cliclick:
            subprocess.run([self._cliclick, f"m:{xy[0]},{xy[1]}"], check=False)
        return AgentResult(speech=f"Cursor moved to {xy[0]}, {xy[1]}, sir.", handled=True)

    def _type(self, utterance: str) -> AgentResult:
        match = re.search(r"type out (.+)$", utterance, re.IGNORECASE)
        if not match:
            return AgentResult(speech="Tell me what to type, sir.", handled=True)
        text = match.group(1).strip().strip('"\'')
        if self._cliclick:
            subprocess.run([self._cliclick, f"t:{text}"], check=False)
        else:
            safe = text.replace('"', '\\"')
            subprocess.run(
                ["osascript", "-e",
                 f'tell application "System Events" to keystroke "{safe}"'],
                check=False)
        preview = text if len(text) < 40 else text[:37] + "..."
        return AgentResult(speech=f"Typed: {preview}, sir.", handled=True)

    @staticmethod
    def _press(u: str) -> AgentResult:
        match = re.search(r"press key (\w+)", u)
        if not match:
            return AgentResult(speech="Which key, sir?", handled=True)
        key = match.group(1).lower()
        codes = {"return": 36, "tab": 48, "space": 49, "delete": 51,
                 "escape": 53, "left": 123, "right": 124, "down": 125, "up": 126}
        if key not in codes:
            return AgentResult(speech=f"I cannot press {key}, sir.", handled=True)
        subprocess.run(
            ["osascript", "-e",
             f'tell application "System Events" to key code {codes[key]}'],
            check=False)
        return AgentResult(speech=f"Pressed {key}, sir.", handled=True)

    def _scroll(self, u: str) -> AgentResult:
        nums = re.findall(r"\d+", u)
        ticks = int(nums[0]) if nums else 3
        direction = -ticks if "down" in u else ticks
        if self._cliclick:
            subprocess.run(
                [self._cliclick, f"w:{direction * 100}"], check=False)
        return AgentResult(
            speech=f"Scrolled {'down' if direction < 0 else 'up'} by {abs(ticks)}, sir.",
            handled=True)
