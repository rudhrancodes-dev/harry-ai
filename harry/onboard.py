"""`harry-onboard` — first-run setup, paperclipai-style.

What it does (idempotent):
  1. Writes ~/.config/harry/.env from your answers (or a sensible default).
  2. Creates the Obsidian vault at ~/Documents/HarryVault if missing.
  3. Optionally invokes the voice enrollment.
  4. Prints the next command (`harry`) to launch the desktop app.

Usage:
    harry-onboard               # interactive
    harry-onboard --yes         # accept defaults, write env, no prompts
    harry-onboard --print-env   # just dump the env it would write
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

DEFAULTS = {
    "HARRY_BRAIN": "claude-code",
    "HARRY_LANGUAGE": "auto",
    "HARRY_USER_NAME": "Rudhran",
    "HARRY_ADDRESS": "sir",
    "HARRY_WAKE_WORD": "harry",
    "HARRY_VAULT": str(Path.home() / "Documents" / "HarryVault"),
    "HARRY_HOST": "127.0.0.1",
    "HARRY_PORT": "7424",
}

ENV_PATH = Path.home() / ".config" / "harry" / ".env"


def _bool_in(prompt: str, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    ans = input(f"  {prompt} {suffix} ").strip().lower()
    if not ans: return default
    return ans in {"y", "yes"}


def _str_in(prompt: str, default: str) -> str:
    ans = input(f"  {prompt} [{default}] ").strip()
    return ans or default


def _write_env(values: dict[str, str]) -> Path:
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={v}" for k, v in values.items()]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ENV_PATH


def main() -> int:
    p = argparse.ArgumentParser(prog="harry-onboard")
    p.add_argument("--yes", action="store_true", help="accept defaults silently")
    p.add_argument("--print-env", action="store_true")
    args = p.parse_args()

    if args.print_env:
        for k, v in DEFAULTS.items(): print(f"{k}={v}")
        return 0

    values = dict(DEFAULTS)

    if not args.yes:
        print("\n✦ Harry onboarding\n")
        values["HARRY_USER_NAME"] = _str_in("What's your name?", values["HARRY_USER_NAME"])
        values["HARRY_LANGUAGE"]  = _str_in("Language (en / ta / auto)?", values["HARRY_LANGUAGE"])
        values["HARRY_BRAIN"]     = _str_in(
            "Brain backend (claude-code / openrouter / openai-compat / off)?",
            values["HARRY_BRAIN"])
        if values["HARRY_BRAIN"] == "openrouter":
            values["OPENROUTER_API_KEY"] = _str_in("OpenRouter API key", "")
            values["OPENROUTER_MODEL"]   = _str_in(
                "OpenRouter model", "deepseek/deepseek-chat-v3-0324")
        if values["HARRY_BRAIN"] == "openai-compat":
            values["OPENCODE_BASE_URL"] = _str_in("Base URL", "http://localhost:11434/v1")
            values["OPENCODE_MODEL"]    = _str_in("Model id", "deepseek-chat")
            values["OPENCODE_API_KEY"]  = _str_in("API key (blank for local)", "")
        if values["HARRY_BRAIN"] == "claude-code" and not shutil.which("claude"):
            print("\n⚠ The `claude` CLI is not on PATH. Install Claude Code and run `claude /login`,\n"
                  "  or switch HARRY_BRAIN to openrouter / openai-compat.")

    path = _write_env(values)
    print(f"\n✓ Wrote config → {path}")

    vault = Path(values["HARRY_VAULT"])
    vault.mkdir(parents=True, exist_ok=True)
    (vault / ".obsidian").mkdir(exist_ok=True)
    print(f"✓ Vault at  → {vault}")

    if not args.yes and _bool_in(
            "Run voice enrollment now? (you'll read 10 short prompts)", default=False):
        os.execvp(sys.executable, [sys.executable, "-m", "harry.enroll"])

    print("\nNext:\n   harry            # launches the desktop app\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
