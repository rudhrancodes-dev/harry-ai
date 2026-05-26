"""Brain backed by the `claude` CLI in non-interactive mode.

Uses the user's existing Claude Pro / Max browser authentication — no
ANTHROPIC_API_KEY required. Falls back to a polite error string if the CLI
isn't installed or hasn't been signed in to.
"""
from __future__ import annotations

import shutil
import subprocess


class ClaudeCodeBrain:
    name = "claude-code"

    def __init__(self, model: str | None = None, timeout_seconds: int = 60) -> None:
        self._model = model
        self._timeout = timeout_seconds
        self._cli = shutil.which("claude")

    def complete(self, system_prompt: str, user_text: str) -> str:
        if not self._cli:
            return ("The Claude CLI is not installed, sir. "
                    "Install Claude Code or switch HARRY_BRAIN to openrouter.")
        prompt = f"{system_prompt}\n\nUser: {user_text}\nAssistant:"
        args = [self._cli, "-p", prompt]
        if self._model:
            args += ["--model", self._model]
        try:
            result = subprocess.run(
                args, capture_output=True, text=True,
                timeout=self._timeout, check=False,
            )
        except subprocess.TimeoutExpired:
            return "I took too long to think on that, sir."
        except FileNotFoundError:
            return "The Claude CLI vanished mid-flight, sir."
        reply = (result.stdout or result.stderr or "").strip()
        return reply or "I am not sure how to answer that, sir."
