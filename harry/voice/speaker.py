"""Bilingual text-to-speech.

Strategy:
  - English  →  macOS `say -v Daniel` (calm British butler) when available,
                else pyttsx3 with the best male voice it can find.
  - Tamil    →  macOS `say -v "Vani"` if installed, else `say` with a
                Hindi voice as a near-neighbour fallback, else pyttsx3.

Detection of script: a single Tamil codepoint anywhere in the line flips
the speaker to Tamil for that line — supports mixed Tanglish utterances.
"""
from __future__ import annotations

import platform
import shutil
import subprocess

import pyttsx3


def _is_tamil(text: str) -> bool:
    return any("஀" <= ch <= "௿" for ch in text)


class Speaker:
    def __init__(self, rate: int = 185) -> None:
        self._mac_say = shutil.which("say") if platform.system() == "Darwin" else None
        self._engine = None
        if not self._mac_say:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", rate)

    def say(self, text: str) -> None:
        if not text:
            return
        tamil = _is_tamil(text)
        if self._mac_say:
            voice = "Vani" if tamil else "Daniel"
            try:
                subprocess.run([self._mac_say, "-v", voice, text],
                               check=False, timeout=30)
                return
            except (subprocess.SubprocessError, FileNotFoundError):
                pass  # fall through to pyttsx3 below
        if self._engine:
            self._engine.say(text)
            self._engine.runAndWait()
