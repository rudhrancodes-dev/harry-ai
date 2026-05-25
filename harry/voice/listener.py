"""Microphone listener — speech-to-text with confidence reporting."""
from __future__ import annotations

from dataclasses import dataclass

import speech_recognition as sr


@dataclass
class Transcription:
    text: str
    confidence: float
    heard_anything: bool


class Listener:
    def __init__(self, energy_threshold: int = 300, pause_threshold: float = 0.8) -> None:
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = energy_threshold
        self._recognizer.pause_threshold = pause_threshold
        self._recognizer.dynamic_energy_threshold = True
        self._mic = sr.Microphone()
        with self._mic as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=0.5)

    def listen(self, timeout: float = 6.0, phrase_limit: float = 12.0) -> Transcription:
        try:
            with self._mic as source:
                audio = self._recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )
        except sr.WaitTimeoutError:
            return Transcription(text="", confidence=0.0, heard_anything=False)

        try:
            result = self._recognizer.recognize_google(audio, show_all=True)
        except sr.UnknownValueError:
            return Transcription(text="", confidence=0.0, heard_anything=True)
        except sr.RequestError:
            return Transcription(text="", confidence=0.0, heard_anything=True)

        if not result or "alternative" not in result:
            return Transcription(text="", confidence=0.0, heard_anything=True)

        best = result["alternative"][0]
        return Transcription(
            text=best.get("transcript", "").strip(),
            confidence=float(best.get("confidence", 0.0)) or 0.5,
            heard_anything=True,
        )
