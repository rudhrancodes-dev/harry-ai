"""Pluggable language-model backends. Pick one via HARRY_BRAIN env var:

  claude-code   →  shells out to the `claude` CLI (uses your Claude Pro / Max plan,
                   no API key required, authenticated via the browser)
  openrouter    →  HTTP to OpenRouter (DeepSeek, GPT, Claude, Gemini, etc.)
  openai-compat →  any OpenAI-compatible endpoint (opencode, Ollama, vLLM,
                   DeepSeek direct, Groq, Together, ...)
  off           →  no brain — only deterministic skills will work

Every backend implements `Brain.complete(system_prompt, user_text) -> str`.
"""
from __future__ import annotations

import os
from typing import Protocol

from .claude_code import ClaudeCodeBrain
from .openai_compat import OpenAICompatBrain
from .openrouter import OpenRouterBrain


class Brain(Protocol):
    name: str

    def complete(self, system_prompt: str, user_text: str) -> str: ...


class NullBrain:
    name = "off"

    def complete(self, system_prompt: str, user_text: str) -> str:
        return "I have no language model configured, sir. Please pick a brain backend."


def load_brain() -> Brain:
    backend = os.getenv("HARRY_BRAIN", "claude-code").strip().lower()
    if backend == "claude-code":
        return ClaudeCodeBrain()
    if backend == "openrouter":
        return OpenRouterBrain(
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324"),
        )
    if backend == "openai-compat":
        return OpenAICompatBrain(
            api_key=os.getenv("OPENCODE_API_KEY", ""),
            base_url=os.getenv("OPENCODE_BASE_URL", "http://localhost:11434/v1"),
            model=os.getenv("OPENCODE_MODEL", "deepseek-chat"),
        )
    if backend == "off":
        return NullBrain()
    raise RuntimeError(
        f"unknown HARRY_BRAIN={backend!r} — pick claude-code, openrouter, openai-compat, or off")


__all__ = ["Brain", "NullBrain", "load_brain",
           "ClaudeCodeBrain", "OpenRouterBrain", "OpenAICompatBrain"]
