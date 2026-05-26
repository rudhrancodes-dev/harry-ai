"""Generates the PNG assets used in the README.

Run from the repo root:
    python docs/generate_screenshots.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def make_banner() -> None:
    w, h = 1280, 360
    img = Image.new("RGB", (w, h), "#0a0e1a")
    d = ImageDraw.Draw(img)
    for y in range(h):
        c = int(10 + (y / h) * 18)
        d.line([(0, y), (w, y)], fill=(c, c + 4, c + 14))
    d.ellipse((-200, -200, 400, 400), outline="#1f3a8a", width=2)
    d.ellipse((w - 380, h - 220, w + 220, h + 380), outline="#7c3aed", width=2)
    d.text((60, 90), "HARRY", fill="#e2e8f0", font=_font(140, bold=True))
    d.text((68, 240), "voice-only agentic AI · hermes-style architecture",
           fill="#94a3b8", font=_font(28))
    d.text((68, 290), "by Rudhran B.   ·   github.com/rudhrancodes-dev",
           fill="#475569", font=_font(20))
    d.rectangle((w - 220, 80, w - 60, 130), outline="#22d3ee", width=2)
    d.text((w - 200, 92), "● ONLINE", fill="#22d3ee", font=_font(22, bold=True))
    img.save(OUT / "banner.png")


def make_architecture() -> None:
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), "#0f172a")
    d = ImageDraw.Draw(img)
    d.text((40, 30), "Harry — System Architecture",
           fill="#e2e8f0", font=_font(34, bold=True))
    d.text((40, 78), "Hermes-style orchestrator routes utterances to specialist agents.",
           fill="#94a3b8", font=_font(20))

    def box(x, y, bw, bh, title, subtitle, color):
        d.rounded_rectangle((x, y, x + bw, y + bh), radius=14,
                            outline=color, width=3, fill="#1e293b")
        d.text((x + 18, y + 16), title, fill=color, font=_font(22, bold=True))
        d.text((x + 18, y + 50), subtitle, fill="#cbd5e1", font=_font(16))

    def arrow(x1, y1, x2, y2, color="#475569"):
        d.line((x1, y1, x2, y2), fill=color, width=2)
        d.polygon([(x2, y2), (x2 - 8, y2 - 5), (x2 - 8, y2 + 5)], fill=color)

    box(60, 140, 240, 90, "Microphone", "speech_recognition / Whisper", "#22d3ee")
    box(60, 260, 240, 90, "Listener", "STT  →  text + confidence", "#22d3ee")
    box(60, 380, 240, 90, "Wake & Clarify", "wake word + re-ask loop", "#22d3ee")

    box(420, 260, 320, 110, "Orchestrator", "Hermes-style router", "#f59e0b")
    box(420, 410, 320, 90, "Brain  (pluggable)", "Claude Pro · OpenRouter · OpenAI-compat", "#a855f7")

    box(820, 90, 220, 70, "Time Agent", "clock / date / day", "#34d399")
    box(820, 170, 220, 70, "Weather Agent", "OpenWeather API", "#34d399")
    box(820, 250, 220, 70, "System Agent", "open mac apps", "#34d399")
    box(820, 330, 220, 70, "Computer Agent", "click / type / scroll (CUA)", "#34d399")
    box(820, 410, 220, 70, "Code Agent", "writes code to sandbox", "#34d399")
    box(820, 490, 220, 70, "Hermes Skills × 98", "unique-keyword catalogue", "#34d399")

    box(420, 560, 320, 100, "Speaker", "TTS  →  audible reply", "#f472b6")

    arrow(180, 230, 180, 260)
    arrow(180, 350, 180, 380)
    arrow(300, 425, 420, 315)
    arrow(740, 315, 820, 125)
    arrow(740, 315, 820, 205)
    arrow(740, 315, 820, 285)
    arrow(740, 315, 820, 365)
    arrow(740, 315, 820, 445)
    arrow(740, 315, 820, 525)
    arrow(580, 370, 580, 410)
    arrow(580, 500, 580, 560)
    arrow(820, 525, 740, 605, color="#64748b")

    d.text((40, 680), "user voice  →  listener  →  orchestrator  →  agent  →  speaker  →  user",
           fill="#64748b", font=_font(16))
    img.save(OUT / "architecture.png")


def make_terminal_demo() -> None:
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), "#0d1117")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w, 44), radius=8, fill="#161b22")
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        d.ellipse((20 + i * 24, 14, 36 + i * 24, 30), fill=color)
    d.text((w // 2 - 110, 12), "harry — python main.py",
           fill="#8b949e", font=_font(18))

    mono = _font(20)
    mono_b = _font(20, bold=True)

    lines = [
        ("$ python main.py", "#7ee787"),
        ("            HARRY — voice-only agentic assistant", "#e6edf3"),
        ("    brain: claude-code   ·   say 'harry, ...' to wake.", "#6e7681"),
        ("", "#e6edf3"),
        ("heard: harry what time is it    (0.94)", "#7ee787"),
        ("agent: time          harry: The time is 1:07 AM, sir.", "#79c0ff"),
        ("", "#e6edf3"),
        ("heard: harry tell a joke    (0.93)", "#7ee787"),
        ("agent: hermes-skills harry: I tried writing a pun, sir,", "#79c0ff"),
        ("                     but it had no punchline.", "#79c0ff"),
        ("", "#e6edf3"),
        ("heard: harry roll a dice    (0.96)", "#7ee787"),
        ("agent: hermes-skills harry: You rolled a 4, sir.", "#79c0ff"),
        ("", "#e6edf3"),
        ("heard: harry click at 480 320    (0.92)", "#7ee787"),
        ("agent: computer     harry: Clicking at 480, 320, sir.", "#79c0ff"),
        ("", "#e6edf3"),
        ("heard: harry code python that reverses a string", "#7ee787"),
        ("       into reverse.py    (0.89)", "#7ee787"),
        ("agent: code         harry: I have written 3 lines into", "#79c0ff"),
        ("                    .harry/workspace/reverse.py, sir.", "#79c0ff"),
        ("", "#e6edf3"),
        ("heard: harry mumble mumble    (0.18)", "#f0883e"),
        ("harry: I am not certain I understood. Please say that again.", "#79c0ff"),
    ]

    y = 70
    for text, color in lines:
        font = mono_b if text.startswith("harry:") else mono
        d.text((28, y), text, fill=color, font=font)
        y += 30

    img.save(OUT / "demo.png")


if __name__ == "__main__":
    make_banner()
    make_architecture()
    make_terminal_demo()
    print(f"wrote screenshots to {OUT}")
