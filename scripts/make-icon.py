"""Generate the Harry app icon — a 1024 px PNG, then iconutil converts it
to Harry.icns for the .app bundle. Re-run to regenerate.

Aesthetic: matches the Apple-iridescent / obsidian-Jarvis vibe of the UI."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

SIZE = 1024


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in ("/System/Library/Fonts/Supplemental/Futura.ttc",
                 "/Library/Fonts/Arial.ttf",
                 "/System/Library/Fonts/SFNS.ttf"):
        if Path(path).exists():
            try: return ImageFont.truetype(path, size)
            except OSError: continue
    return ImageFont.load_default()


def make() -> Path:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    margin = 80
    d.rounded_rectangle((margin, margin, SIZE - margin, SIZE - margin),
                        radius=220, fill=(14, 18, 30, 255))

    cx, cy = SIZE // 2, SIZE // 2
    for i, (r, color, width) in enumerate([
        (340, (124, 58, 237, 110), 4),
        (300, (34, 211, 238, 90),  3),
        (260, (244, 114, 182, 70), 2),
    ]):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=width)

    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((cx - 220, cy - 220, cx + 220, cy + 220),
               fill=(124, 58, 237, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img.alpha_composite(glow)

    for r, alpha in [(190, 220), (150, 255)]:
        d.ellipse((cx - r, cy - r, cx + r, cy + r),
                  fill=(226, 232, 240, alpha))

    f = _font(360)
    text = "H"
    bbox = d.textbbox((0, 0), text, font=f)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((cx - w / 2 - bbox[0], cy - h / 2 - bbox[1] - 10),
           text, fill=(14, 18, 30, 255), font=f)

    for i in range(72):
        a = (i / 72) * math.tau
        r1, r2 = 380, 396
        d.line((cx + math.cos(a) * r1, cy + math.sin(a) * r1,
                cx + math.cos(a) * r2, cy + math.sin(a) * r2),
               fill=(124, 58, 237, 180), width=2)

    out = OUT / "harry-icon-1024.png"
    img.save(out)
    return out


if __name__ == "__main__":
    p = make()
    print(f"wrote {p}")
