"""Obsidian-vault-backed memory.

Creates a real Obsidian vault at ~/Documents/HarryVault (configurable via
HARRY_VAULT) on first use, complete with a `.obsidian/` folder so Obsidian
recognises it. Each Harry session becomes a markdown note under Sessions/
with YAML frontmatter — both human-readable and easy to grep.

Layout:
  HarryVault/
    .obsidian/app.json              ← minimal config so Obsidian opens it
    README.md                       ← what this vault is
    Sessions/
      2026-05-26.md                 ← one note per calendar day, appended
    People/
      Rudhran.md                    ← long-lived facts about the user
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def vault_path() -> Path:
    return Path(os.getenv("HARRY_VAULT", str(Path.home() / "Documents" / "HarryVault")))


@dataclass
class Turn:
    user: str
    harry: str
    agent: str
    language: str = "en"


class Memory:
    def __init__(self) -> None:
        self.root = vault_path()
        self._bootstrap()

    # ── public API ────────────────────────────────────────────────────────

    def record(self, turn: Turn) -> Path:
        path = self._daily_path()
        if not path.exists():
            path.write_text(self._daily_header(), encoding="utf-8")
        block = (
            f"### {datetime.now().strftime('%H:%M:%S')}  ·  agent: `{turn.agent}`"
            f"  ·  lang: `{turn.language}`\n"
            f"**Rudhran:** {turn.user}\n\n"
            f"**Harry:** {turn.harry}\n\n---\n\n"
        )
        with path.open("a", encoding="utf-8") as f:
            f.write(block)
        return path

    def last_session_summary(self, max_chars: int = 1200) -> str:
        sessions = sorted((self.root / "Sessions").glob("*.md"), reverse=True)
        if not sessions:
            return ""
        text = sessions[0].read_text(encoding="utf-8")
        return text[-max_chars:]

    def remember_user(self, fact: str) -> None:
        path = self.root / "People" / "Rudhran.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(
                "---\nname: Rudhran\nrole: CS student · Coimbatore\n---\n\n"
                "# Rudhran\n\n## Facts Harry has learned\n\n", encoding="utf-8")
        with path.open("a", encoding="utf-8") as f:
            f.write(f"- {fact}\n")

    # ── internals ─────────────────────────────────────────────────────────

    def _bootstrap(self) -> None:
        (self.root / "Sessions").mkdir(parents=True, exist_ok=True)
        (self.root / "People").mkdir(parents=True, exist_ok=True)
        obs = self.root / ".obsidian"
        obs.mkdir(exist_ok=True)
        app_cfg = obs / "app.json"
        if not app_cfg.exists():
            app_cfg.write_text(json.dumps({
                "alwaysUpdateLinks": True,
                "newFileLocation": "folder",
                "newFileFolderPath": "Sessions",
            }, indent=2), encoding="utf-8")
        readme = self.root / "README.md"
        if not readme.exists():
            readme.write_text(
                "# Harry Vault\n\n"
                "This is Harry's memory. Every conversation is appended to "
                "`Sessions/YYYY-MM-DD.md`. Long-lived facts about you live in "
                "`People/Rudhran.md`.\n\n"
                "You can open this folder as a vault in Obsidian — Harry has "
                "already created `.obsidian/app.json` so it shows up.\n",
                encoding="utf-8")

    def _daily_path(self) -> Path:
        return self.root / "Sessions" / f"{datetime.now().strftime('%Y-%m-%d')}.md"

    def _daily_header(self) -> str:
        today = datetime.now()
        return (
            f"---\n"
            f"date: {today.strftime('%Y-%m-%d')}\n"
            f"weekday: {today.strftime('%A')}\n"
            f"tags: [harry, session]\n"
            f"---\n\n"
            f"# {today.strftime('%A, %B %d, %Y')}\n\n"
        )
