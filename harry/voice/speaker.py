"""Text-to-speech — offline via pyttsx3."""
from __future__ import annotations

import pyttsx3


class Speaker:
    def __init__(self, rate: int = 185, voice_hint: str = "male") -> None:
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)
        for voice in self._engine.getProperty("voices"):
            name = (voice.name or "").lower()
            if voice_hint == "male" and ("daniel" in name or "alex" in name or "male" in name):
                self._engine.setProperty("voice", voice.id)
                break

    def say(self, text: str) -> None:
        if not text:
            return
        self._engine.say(text)
        self._engine.runAndWait()
