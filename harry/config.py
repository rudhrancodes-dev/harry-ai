"""Runtime configuration loaded from environment variables."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str
    model: str
    wake_word: str
    openweather_api_key: str | None
    stt_energy_threshold: int
    stt_pause_threshold: float
    max_clarification_rounds: int


def load_config() -> Config:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return Config(
        anthropic_api_key=key,
        model=os.getenv("HARRY_MODEL", "claude-sonnet-4-6"),
        wake_word=os.getenv("HARRY_WAKE_WORD", "harry").lower(),
        openweather_api_key=os.getenv("OPENWEATHER_API_KEY") or None,
        stt_energy_threshold=int(os.getenv("HARRY_STT_ENERGY", "300")),
        stt_pause_threshold=float(os.getenv("HARRY_STT_PAUSE", "0.8")),
        max_clarification_rounds=int(os.getenv("HARRY_MAX_CLARIFY", "2")),
    )
