"""OpenRouter backend — one key, hundreds of models including DeepSeek v3."""
from __future__ import annotations

import requests

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterBrain:
    name = "openrouter"

    def __init__(self, api_key: str, model: str, timeout_seconds: int = 30) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds

    def complete(self, system_prompt: str, user_text: str) -> str:
        if not self._api_key:
            return ("OpenRouter has no API key set, sir. "
                    "Add OPENROUTER_API_KEY to your environment.")
        try:
            r = requests.post(
                ENDPOINT,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "HTTP-Referer": "https://github.com/rudhrancodes-dev/harry-ai",
                    "X-Title": "Harry",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text},
                    ],
                    "max_tokens": 400,
                },
                timeout=self._timeout,
            )
            r.raise_for_status()
            data = r.json()
        except requests.RequestException:
            return "I could not reach OpenRouter, sir."
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError):
            return "OpenRouter returned an unexpected reply, sir."
