"""Entry point — runs Harry's voice loop.

Routing priority (first match wins):
  TimeAgent          – clock / date
  WeatherAgent       – local weather lookups
  SystemAgent        – open mac apps from a safe list
  ComputerAgent      – cursor / keyboard / scroll via cliclick
  CodeAgent          – "code python that ... into foo.py"  →  saves a file
  HermesSkillAgent   – 98 narrow skills with unique trigger phrases
  ConversationAgent  – free-form fallback through the configured Brain
"""
from __future__ import annotations

import signal
import sys

from rich.console import Console

from harry.agents import (
    CodeAgent,
    ComputerAgent,
    ConversationAgent,
    Orchestrator,
    SystemAgent,
    TimeAgent,
    WeatherAgent,
)
from harry.brain import load_brain
from harry.config import load_config
from harry.skills import HermesSkillAgent
from harry.voice import Listener, Speaker

console = Console()


def banner(brain_name: str) -> None:
    console.print(
        "[bold cyan]HARRY[/bold cyan] — voice-only agentic assistant",
        justify="center",
    )
    console.print(f"[dim]brain: {brain_name}   ·   say 'harry, ...' to wake.  Ctrl+C to exit.[/dim]\n")


def main() -> int:
    config = load_config()
    brain = load_brain()

    listener = Listener(
        energy_threshold=config.stt_energy_threshold,
        pause_threshold=config.stt_pause_threshold,
    )
    speaker = Speaker()
    orchestrator = Orchestrator(
        [
            TimeAgent(),
            WeatherAgent(api_key=config.openweather_api_key),
            SystemAgent(),
            ComputerAgent(),
            CodeAgent(brain=brain),
            HermesSkillAgent(brain=brain),
            ConversationAgent(brain=brain),
        ]
    )

    banner(brain.name)
    speaker.say("Harry online. Standing by.")

    def shutdown(_signum, _frame):
        speaker.say("Powering down. Goodbye.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    while True:
        console.print("[dim]listening...[/dim]")
        transcription = listener.listen()

        if not transcription.heard_anything:
            continue
        if not transcription.text:
            speaker.say("I did not catch that. Could you repeat?")
            continue

        utterance = transcription.text.lower()
        console.print(f"[green]heard[/green]: {transcription.text} "
                      f"[dim](confidence {transcription.confidence:.2f})[/dim]")

        if config.wake_word and config.wake_word not in utterance:
            continue

        payload = utterance.split(config.wake_word, 1)[-1].strip(" ,.;:!?")
        if not payload:
            speaker.say("Yes?")
            continue

        rounds = 0
        while transcription.confidence < 0.35 and rounds < config.max_clarification_rounds:
            speaker.say("I am not certain I understood. Please say that again.")
            transcription = listener.listen()
            if not transcription.text:
                rounds += 1
                continue
            payload = transcription.text.lower().split(config.wake_word, 1)[-1].strip(" ,.;:!?")
            rounds += 1

        agent, result = orchestrator.route(payload)
        console.print(f"[magenta]agent[/magenta]: {agent.name}")
        console.print(f"[cyan]harry[/cyan]: {result.speech}\n")
        speaker.say(result.speech)


if __name__ == "__main__":
    raise SystemExit(main())
