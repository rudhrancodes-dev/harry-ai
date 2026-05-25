"""Entry point — runs Harry's voice loop.

Flow per turn:
  1. Listen for a phrase from the microphone.
  2. If nothing was heard, loop quietly.
  3. If speech was heard but not understood, ask the user to repeat (up to N rounds).
  4. Optionally require the wake word ("harry ...") before responding.
  5. Hand the utterance to the orchestrator and speak its reply.
"""
from __future__ import annotations

import signal
import sys

from rich.console import Console

from harry.agents import (
    ConversationAgent,
    Orchestrator,
    SystemAgent,
    TimeAgent,
    WeatherAgent,
)
from harry.brain import Brain
from harry.config import load_config
from harry.voice import Listener, Speaker

console = Console()


def banner() -> None:
    console.print(
        "[bold cyan]HARRY[/bold cyan] — voice-only agentic assistant",
        justify="center",
    )
    console.print("[dim]say 'harry, ...' to wake.  Ctrl+C to exit.[/dim]\n")


def main() -> int:
    config = load_config()
    listener = Listener(
        energy_threshold=config.stt_energy_threshold,
        pause_threshold=config.stt_pause_threshold,
    )
    speaker = Speaker()
    brain = Brain(api_key=config.anthropic_api_key, model=config.model)
    orchestrator = Orchestrator(
        [
            TimeAgent(),
            WeatherAgent(api_key=config.openweather_api_key),
            SystemAgent(),
            ConversationAgent(brain=brain),
        ]
    )

    banner()
    speaker.say("Harry online. Standing by, sir.")

    def shutdown(_signum, _frame):
        speaker.say("Powering down. Goodbye, sir.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    while True:
        console.print("[dim]listening...[/dim]")
        transcription = listener.listen()

        if not transcription.heard_anything:
            continue

        if not transcription.text:
            speaker.say("I did not catch that, sir. Could you repeat?")
            continue

        utterance = transcription.text.lower()
        console.print(f"[green]heard[/green]: {transcription.text} "
                      f"[dim](confidence {transcription.confidence:.2f})[/dim]")

        if config.wake_word and config.wake_word not in utterance:
            continue

        payload = utterance.split(config.wake_word, 1)[-1].strip(" ,.;:!?")
        if not payload:
            speaker.say("Yes, sir?")
            continue

        rounds = 0
        while transcription.confidence < 0.35 and rounds < config.max_clarification_rounds:
            speaker.say("I am not certain I understood. Please say that again, sir.")
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
