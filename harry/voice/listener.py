"""Microphone listener — bilingual EN+TA with confidence reporting.

When the configured language is "auto", Harry tries Tamil first (the
recogniser's en-IN model picks up Tanglish well enough that EN often falls
through), then English, and returns whichever scored higher.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import speech_recognition as sr


@dataclass
class Transcription:
    text: str
    confidence: float
    heard_anything: bool
    language: str = ""  # "en" | "ta" | ""


class Listener:
    def __init__(
        self,
        energy_threshold: int = 300,
        pause_threshold: float = 0.8,
        language: str | None = None,
    ) -> None:
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = energy_threshold
        self._recognizer.pause_threshold = pause_threshold
        self._recognizer.dynamic_energy_threshold = True
        self._mic = sr.Microphone()
        self._language = (language or os.getenv("HARRY_LANGUAGE", "en")).lower()
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

        if self._language == "ta":
            return self._recognise(audio, "ta-IN", "ta")
        if self._language == "en":
            return self._recognise(audio, "en-IN", "en")

        # auto: try both, return whichever scored higher
        ta = self._recognise(audio, "ta-IN", "ta")
        en = self._recognise(audio, "en-IN", "en")
        return ta if ta.confidence >= en.confidence else en

    def _recognise(self, audio, locale: str, tag: str) -> Transcription:
        try:
            result = self._recognizer.recognize_google(audio, language=locale, show_all=True)
        except sr.UnknownValueError:
            return Transcription(text="", confidence=0.0, heard_anything=True, language=tag)
        except sr.RequestError:
            return Transcription(text="", confidence=0.0, heard_anything=True, language=tag)
        if not result or "alternative" not in result:
            return Transcription(text="", confidence=0.0, heard_anything=True, language=tag)
        best = result["alternative"][0]
        return Transcription(
            text=best.get("transcript", "").strip(),
            confidence=float(best.get("confidence", 0.0)) or 0.5,
            heard_anything=True,
            language=tag,
        )
