"""Python mirror of the JS greeting pools. Used by the backend to speak
the opening greeting through the speaker as soon as the app launches.

The pools are intentionally shorter than the JS catalogues — the JS side
remains the authoritative visible catalogue; this is the spoken subset."""
from __future__ import annotations

import os
import random
from datetime import datetime

EN = {
    "dawn": [
        "Good morning, {name}.",
        "Up before the sun, {name}.",
        "Early start, {name}. The world is still asleep.",
    ],
    "morning": [
        "Good morning, {name}.",
        "Welcome back, {name}.",
        "Ready when you are, {name}.",
        "Top of the morning, {name}.",
    ],
    "midday": [
        "Welcome back, {name}.",
        "Afternoon, {name}. Ready to continue?",
        "Right on time, {name}.",
    ],
    "evening": [
        "Good evening, {name}.",
        "Evening, {name}. Long day?",
        "{name}, let us wrap the day cleanly.",
    ],
    "night": [
        "Burning the midnight oil, {name}?",
        "Late hours suit you, {name}.",
        "{name}. The city is asleep. We do not have to be.",
        "Standing watch, {name}.",
    ],
}

TA = {
    "dawn": [
        "காலை வணக்கம், {name}.",
        "சூரியனுக்கு முன்பே எழுந்துவிட்டீர்களா, {name}?",
    ],
    "morning": [
        "காலை வணக்கம், {name}.",
        "மீண்டும் வருக, {name}.",
        "தயாராக உள்ளேன், {name}.",
    ],
    "midday": [
        "மீண்டும் வருக, {name}.",
        "மதிய வணக்கம், {name}.",
    ],
    "evening": [
        "மாலை வணக்கம், {name}.",
        "{name}, இந்த நாளை நேர்த்தியாக முடிப்போம்.",
    ],
    "night": [
        "நள்ளிரவு எண்ணெய் எரிக்கிறீர்களா, {name}?",
        "{name}, நகரம் தூங்குகிறது. நாம் தூங்க வேண்டாம்.",
        "{name}, நான் இங்கேயே இருக்கிறேன். எப்போதும்.",
    ],
}


def _bucket(hour: int) -> str:
    if 4 <= hour < 7:  return "dawn"
    if 7 <= hour < 12: return "morning"
    if 12 <= hour < 17: return "midday"
    if 17 <= hour < 21: return "evening"
    return "night"


TA_NAME_BY_EN = {"Rudhran": "ருத்ரன்"}


def pick_greeting(language: str = "en", name: str | None = None) -> str:
    name = (name or os.getenv("HARRY_USER_NAME", "Rudhran")).strip() or "Rudhran"
    hour = datetime.now().hour
    bucket = _bucket(hour)
    use_ta = language == "ta" or (language == "auto" and hour % 2)
    pool = TA[bucket] if use_ta else EN[bucket]
    spoken = (os.getenv("HARRY_USER_NAME_TA") or TA_NAME_BY_EN.get(name, name)) \
        if use_ta else name
    return random.choice(pool).format(name=spoken)
