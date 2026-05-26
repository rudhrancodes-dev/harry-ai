"""FastAPI backend for the Harry desktop app.

Responsibilities:
  - serve the React/Babel UI from webapp/
  - expose /api/config (GET/POST) so the Settings drawer can switch the
    HARRY_BRAIN backend, language, and persona at runtime
  - expose /api/greeting so the app can speak the opening greeting
  - stream state/transcript/tool events to the UI over /ws
  - take spoken or typed input from the UI, route it through the
    orchestrator, persist the turn to the Obsidian vault, and speak the
    reply through the macOS `say` voices

The voice loop runs in a background thread; the UI is the front-end of
the same Harry orchestrator that the headless main.py uses.
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import threading
from pathlib import Path
from typing import Any

from dotenv import load_dotenv, set_key
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from harry.agents import (
    CodeAgent, ComputerAgent, ConversationAgent, Orchestrator,
    SystemAgent, TimeAgent, WeatherAgent,
)
from harry.brain import load_brain
from harry.greetings import pick_greeting
from harry.memory import Memory, Turn, vault_path
from harry.skills import HermesSkillAgent
from harry.voice import Speaker
from harry.voice.speaker_id import SpeakerID

ROOT = Path(__file__).resolve().parent.parent
WEBAPP = ROOT / "webapp"
ENV_PATH = ROOT / ".env"

load_dotenv(ENV_PATH)


# ── Hub for fan-out to all connected UI clients ───────────────────────────

class Hub:
    def __init__(self) -> None:
        self.clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def join(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self.clients.add(ws)

    async def leave(self, ws: WebSocket) -> None:
        async with self._lock:
            self.clients.discard(ws)

    async def broadcast(self, msg: dict[str, Any]) -> None:
        data = json.dumps(msg)
        dead: list[WebSocket] = []
        for c in list(self.clients):
            try: await c.send_text(data)
            except Exception: dead.append(c)
        if dead:
            async with self._lock:
                for c in dead: self.clients.discard(c)


# ── Lazy global wiring (orchestrator + memory) ────────────────────────────

class HarryRuntime:
    def __init__(self) -> None:
        self.memory = Memory()
        self.brain = load_brain()
        self.speaker = Speaker()
        self.speaker_id = SpeakerID()
        self.orchestrator = Orchestrator([
            TimeAgent(),
            WeatherAgent(api_key=os.getenv("OPENWEATHER_API_KEY") or None),
            SystemAgent(),
            ComputerAgent(),
            CodeAgent(brain=self.brain),
            HermesSkillAgent(brain=self.brain),
            ConversationAgent(brain=self.brain),
        ])

    def reload_brain(self) -> None:
        self.brain = load_brain()
        self.orchestrator = Orchestrator([
            TimeAgent(),
            WeatherAgent(api_key=os.getenv("OPENWEATHER_API_KEY") or None),
            SystemAgent(),
            ComputerAgent(),
            CodeAgent(brain=self.brain),
            HermesSkillAgent(brain=self.brain),
            ConversationAgent(brain=self.brain),
        ])

    def handle_text(self, text: str) -> tuple[str, str, str]:
        agent, result = self.orchestrator.route(text)
        return agent.name, result.speech, _detect_lang(result.speech)


def _detect_lang(text: str) -> str:
    return "ta" if any("஀" <= ch <= "௿" for ch in text) else "en"


hub = Hub()
runtime: HarryRuntime | None = None
app = FastAPI(title="Harry · Intelligence")


@app.on_event("startup")
async def _on_startup() -> None:
    global runtime
    runtime = HarryRuntime()
    asyncio.create_task(_speak_opening())


async def _speak_opening() -> None:
    await asyncio.sleep(0.6)
    language = os.getenv("HARRY_LANGUAGE", "en")
    name = os.getenv("HARRY_USER_NAME", "Rudhran")
    text = pick_greeting(language=language, name=name)
    await hub.broadcast({"type": "greeting", "text": text})
    await hub.broadcast({"type": "state", "state": "speaking"})
    await hub.broadcast({"type": "transcript", "who": "harry", "text": text})
    threading.Thread(target=runtime.speaker.say, args=(text,), daemon=True).start()
    await asyncio.sleep(max(2.0, len(text) * 0.045))
    await hub.broadcast({"type": "state", "state": "idle"})


# ── API ──────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "brain": runtime.brain.name if runtime else None}


@app.get("/api/config")
async def get_config() -> dict:
    return _current_config()


@app.post("/api/config")
async def post_config(patch: dict) -> dict:
    mapping = {
        "brain":     "HARRY_BRAIN",
        "language":  "HARRY_LANGUAGE",
        "user_name": "HARRY_USER_NAME",
        "address":   "HARRY_ADDRESS",
        "wake_word": "HARRY_WAKE_WORD",
        "openrouter_key":   "OPENROUTER_API_KEY",
        "openrouter_model": "OPENROUTER_MODEL",
        "opencode_key":     "OPENCODE_API_KEY",
        "opencode_base":    "OPENCODE_BASE_URL",
        "opencode_model":   "OPENCODE_MODEL",
    }
    ENV_PATH.touch(exist_ok=True)
    for ui_key, env_key in mapping.items():
        if ui_key in patch:
            value = str(patch[ui_key])
            os.environ[env_key] = value
            try:
                set_key(str(ENV_PATH), env_key, value, quote_mode="never")
            except Exception:
                pass
    if "brain" in patch and runtime:
        runtime.reload_brain()
    return _current_config()


@app.get("/api/greeting")
async def get_greeting() -> dict:
    return {"text": pick_greeting(
        language=os.getenv("HARRY_LANGUAGE", "en"),
        name=os.getenv("HARRY_USER_NAME", "Rudhran"),
    )}


@app.get("/api/sessions")
async def list_sessions() -> dict:
    sessions = sorted((vault_path() / "Sessions").glob("*.md"), reverse=True)
    return {"sessions": [s.stem for s in sessions]}


def _current_config() -> dict:
    return {
        "brain": os.getenv("HARRY_BRAIN", "claude-code"),
        "language": os.getenv("HARRY_LANGUAGE", "en"),
        "user_name": os.getenv("HARRY_USER_NAME", "Rudhran"),
        "address": os.getenv("HARRY_ADDRESS", "sir"),
        "wake_word": os.getenv("HARRY_WAKE_WORD", "harry"),
        "openrouter_model": os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324"),
        "opencode_base": os.getenv("OPENCODE_BASE_URL", "http://localhost:11434/v1"),
        "opencode_model": os.getenv("OPENCODE_MODEL", "deepseek-chat"),
        "vault_path": str(vault_path()),
        "speaker_enrolled": runtime.speaker_id.enrolled if runtime else False,
        "speaker_threshold": runtime.speaker_id.threshold if runtime else 0.78,
    }


# ── WebSocket ────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await hub.join(ws)
    try:
        await ws.send_text(json.dumps({"type": "state", "state": "idle"}))
        async for raw in _ws_iter(ws):
            try: msg = json.loads(raw)
            except json.JSONDecodeError: continue
            await _handle_ws_message(msg)
    except WebSocketDisconnect:
        pass
    finally:
        await hub.leave(ws)


async def _ws_iter(ws: WebSocket):
    while True:
        yield await ws.receive_text()


async def _handle_ws_message(msg: dict) -> None:
    t = msg.get("type")
    if t == "text":
        await _process_user_text(msg.get("text", ""))
    elif t == "wake":
        await hub.broadcast({"type": "state", "state": "wake"})
    elif t == "mute":
        await hub.broadcast({"type": "state", "state": "muted" if msg.get("on") else "idle"})
    elif t == "config":
        await post_config(msg.get("patch", {}))


async def _process_user_text(text: str) -> None:
    text = (text or "").strip()
    if not text:
        return
    await hub.broadcast({"type": "transcript", "who": "user", "text": text})
    await hub.broadcast({"type": "state", "state": "thinking"})
    loop = asyncio.get_running_loop()
    agent_name, reply, lang = await loop.run_in_executor(
        None, runtime.handle_text, text)
    runtime.memory.record(Turn(user=text, harry=reply, agent=agent_name, language=lang))
    await hub.broadcast({"type": "tool", "name": agent_name, "arg": "routed", "done": True})
    await hub.broadcast({"type": "state", "state": "speaking"})
    await hub.broadcast({"type": "transcript", "who": "harry", "text": reply})
    threading.Thread(target=runtime.speaker.say, args=(reply,), daemon=True).start()
    await asyncio.sleep(max(1.6, len(reply) * 0.040))
    await hub.broadcast({"type": "state", "state": "idle"})


# ── Static UI ─────────────────────────────────────────────────────────────

app.mount("/assets", StaticFiles(directory=str(WEBAPP)), name="assets")


@app.get("/{path:path}")
async def serve(path: str):
    if not path or path == "/":
        return FileResponse(str(WEBAPP / "index.html"))
    target = WEBAPP / path
    if target.is_file():
        return FileResponse(str(target))
    return JSONResponse({"error": "not found"}, status_code=404)


# ── Entrypoint ────────────────────────────────────────────────────────────

def main() -> int:
    import uvicorn
    host = os.getenv("HARRY_HOST", "127.0.0.1")
    port = int(os.getenv("HARRY_PORT", "7424"))

    def _bye(*_a):
        print("\nbye, sir.")
        os._exit(0)
    signal.signal(signal.SIGINT, _bye)

    uvicorn.run("harry.server:app", host=host, port=port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
