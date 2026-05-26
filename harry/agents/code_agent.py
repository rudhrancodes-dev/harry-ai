"""Code-writing agent — asks the Brain for code, saves it to a sandbox.

Voice flow:
    "harry, code python that reverses a string into reverse.py"

The agent extracts: language, the requirement, the target filename. It calls
the configured Brain with a code-focused system prompt, strips fences, and
writes the result under ~/.harry/workspace/. Never overwrites a file
outside that sandbox.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..brain import Brain
from .base import Agent, AgentResult

WORKSPACE = Path.home() / ".harry" / "workspace"
WORKSPACE.mkdir(parents=True, exist_ok=True)

CODE_SYSTEM = (
    "You are a senior software engineer pair-programming with Harry. "
    "Reply with ONLY the code body — no prose, no markdown fences, no comments "
    "explaining what you are doing. Aim for clean, idiomatic, runnable code."
)


class CodeAgent(Agent):
    name = "code"
    description = "Writes code files to ~/.harry/workspace/ via the Brain backend."
    triggers = ("code python that", "code javascript that", "code bash that",
                "code typescript that", "write code that", "code rust that")

    def __init__(self, brain: Brain) -> None:
        self._brain = brain

    def handle(self, utterance: str) -> AgentResult:
        lang, spec, filename = self._parse(utterance)
        if not spec:
            return AgentResult(
                speech="Tell me what the code should do, sir.", handled=True)
        prompt = f"Write {lang} code that {spec}."
        body = self._strip_fences(self._brain.complete(CODE_SYSTEM, prompt))
        if not body or body.startswith("I "):
            return AgentResult(
                speech="The brain returned no code, sir.", handled=True)
        path = self._safe_path(filename, lang)
        path.write_text(body + ("\n" if not body.endswith("\n") else ""), encoding="utf-8")
        return AgentResult(
            speech=f"I have written {len(body.splitlines())} lines into "
                   f"{path.relative_to(Path.home())}, sir.",
            handled=True,
        )

    @staticmethod
    def _parse(u: str) -> tuple[str, str, str | None]:
        lang_match = re.search(
            r"code (python|javascript|typescript|bash|rust)", u, re.IGNORECASE)
        lang = (lang_match.group(1).lower() if lang_match else "python")
        spec_match = re.search(r"that (.+?)(?: into ([\w.\-/]+))?$", u, re.IGNORECASE)
        spec = spec_match.group(1).strip() if spec_match else u
        filename = spec_match.group(2) if spec_match else None
        return lang, spec, filename

    @staticmethod
    def _strip_fences(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2 and lines[-1].startswith("```"):
                return "\n".join(lines[1:-1]).strip()
        return text

    @staticmethod
    def _safe_path(filename: str | None, lang: str) -> Path:
        ext = {"python": ".py", "javascript": ".js", "typescript": ".ts",
               "bash": ".sh", "rust": ".rs"}.get(lang, ".txt")
        if not filename:
            filename = f"snippet_{int.from_bytes(__import__('os').urandom(3), 'big'):x}{ext}"
        candidate = (WORKSPACE / filename).resolve()
        if not str(candidate).startswith(str(WORKSPACE.resolve())):
            candidate = WORKSPACE / "blocked_path.txt"
        return candidate
