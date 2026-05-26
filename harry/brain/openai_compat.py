"""OpenAI-compatible backend — works with opencode, Ollama, vLLM, DeepSeek
direct, Groq, Together, LM Studio, or anything that exposes /v1/chat/completions."""
from __future__ import annotations

import requests


class OpenAICompatBrain:
    name = "openai-compat"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: int = 30,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds

    def complete(self, system_prompt: str, user_text: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            r = requests.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
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
            return f"I could not reach the model at {self._base_url}, sir."
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError):
            return "The model returned an unexpected reply, sir."
