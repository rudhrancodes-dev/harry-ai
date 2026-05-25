"""Weather lookup via OpenWeather (optional)."""
from __future__ import annotations

import re

import requests

from .base import Agent, AgentResult


class WeatherAgent(Agent):
    name = "weather"
    description = "Looks up current weather conditions for a named city."
    triggers = ("weather", "temperature", "forecast", "rain", "hot", "cold")

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key

    def handle(self, utterance: str) -> AgentResult:
        if not self._api_key:
            return AgentResult(
                speech="I do not have a weather key configured, sir.",
                handled=True,
            )
        city = self._extract_city(utterance) or "Coimbatore"
        try:
            r = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": self._api_key, "units": "metric"},
                timeout=5,
            )
            r.raise_for_status()
            data = r.json()
        except Exception:
            return AgentResult(
                speech=f"I could not reach the weather service for {city}, sir.",
                handled=True,
            )

        temp = round(data["main"]["temp"])
        condition = data["weather"][0]["description"]
        return AgentResult(
            speech=f"It is {temp} degrees and {condition} in {city}, sir.",
            handled=True,
        )

    @staticmethod
    def _extract_city(utterance: str) -> str | None:
        match = re.search(r"\b(?:in|at|for)\s+([A-Za-z][A-Za-z\s]+?)$", utterance.strip())
        if not match:
            return None
        return match.group(1).strip().title()
