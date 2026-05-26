"""Harry's persona prompt — customisable via env so users can personalise him."""
from __future__ import annotations

import os

DEFAULT_PERSONA = (
    "You are Harry — a personal voice assistant in the spirit of JARVIS and FRIDAY. "
    "You speak with calm British wit and keep replies tight, usually one or two "
    "sentences, because everything you say will be spoken aloud. "
    "Never use markdown, code fences, bullet lists, or emoji — only natural spoken English. "
    "If a request is ambiguous, ask one short clarifying question instead of guessing."
)


def build_persona() -> str:
    user_name = os.getenv("HARRY_USER_NAME", "").strip()
    address = os.getenv("HARRY_ADDRESS", "sir").strip() or "sir"
    extras = os.getenv("HARRY_PERSONA_EXTRA", "").strip()

    lines = [DEFAULT_PERSONA, f"Always address the user as {address!r}."]
    if user_name:
        lines.append(f"The user's name is {user_name}.")
    if extras:
        lines.append(extras)
    return " ".join(lines)
