"""Orchestrator routing tests — no microphone or network required."""
from harry.agents.base import Agent, AgentResult
from harry.agents.orchestrator import Orchestrator
from harry.agents.system_agent import SystemAgent
from harry.agents.time_agent import TimeAgent
from harry.agents.weather_agent import WeatherAgent


class _Fallback(Agent):
    name = "fallback"
    triggers = ()

    def matches(self, utterance: str) -> bool:
        return True

    def handle(self, utterance: str) -> AgentResult:
        return AgentResult(speech="fallback", handled=True)


def _orch() -> Orchestrator:
    return Orchestrator([
        TimeAgent(),
        WeatherAgent(api_key=None),
        SystemAgent(),
        _Fallback(),
    ])


def test_time_routes_to_time_agent():
    agent, _ = _orch().route("what time is it")
    assert agent.name == "time"


def test_weather_routes_to_weather_agent():
    agent, _ = _orch().route("how is the weather in london")
    assert agent.name == "weather"


def test_open_routes_to_system_agent():
    agent, _ = _orch().route("open safari please")
    assert agent.name == "system"


def test_unmatched_falls_through_to_fallback():
    agent, result = _orch().route("tell me about quantum entanglement")
    assert agent.name == "fallback"
    assert result.speech == "fallback"
