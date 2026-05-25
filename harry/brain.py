"""Claude-powered reasoning brain. Wraps the Anthropic SDK with prompt caching."""
from __future__ import annotations

from typing import Any

from anthropic import Anthropic

HARRY_PERSONA = """You are Harry — a personal voice assistant in the spirit of JARVIS and FRIDAY.
You speak with calm British wit, address the user as "sir", and keep replies tight (one or two sentences) because everything you say will be spoken aloud.
Never use markdown, code fences, bullet lists, or emoji — only natural spoken English.
If a user request is ambiguous, ask a single short clarifying question instead of guessing."""


class Brain:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def think(
        self,
        user_text: str,
        history: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        messages = history + [{"role": "user", "content": user_text}]
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 400,
            "system": [
                {
                    "type": "text",
                    "text": HARRY_PERSONA,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = self._client.messages.create(**kwargs)
        return {
            "stop_reason": response.stop_reason,
            "content": response.content,
        }
