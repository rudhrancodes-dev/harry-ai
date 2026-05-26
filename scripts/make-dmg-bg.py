"""Generate the DMG background image — branded obsidian / iridescent panel
with a soft arrow leading the eye from where Harry.app will sit to where
the Applications symlink will sit.

Output:  assets/dmg-background.png  (660 × 400, 144 dpi for retina)

Window layout the AppleScript will set up:
    window bounds:   {x: 400, y: 100, w: 660, h: 400}
    icon size:       128
    Harry.app pos:   (165, 200)
    Applications:    (495, 200)
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 660, 400
# Finder positions icons relative to the content area (below the title bar).
# These ICON_Y / X values must match the create-dmg --icon positions so the
# painted slots line up with where Finder actually drops the icons.
ICON_Y = 240
LEFT_X = 165
RIGHT_X = 495


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Futura.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        if Path(path).exists():
            try: return ImageFont.truetype(path, size)
            except OSError: continue
    return ImageFont.load_default()


def make() -> Path:
    img = Image.new("RGB", (W, H), "#0e121e")
    d = ImageDraw.Draw(img)

    # subtle vertical gradient
    for y in range(H):
        c = int(14 + (y / H) * 10)
        d.line([(0, y), (W, y)], fill=(c, c + 2, c + 12))

    # two soft glows centred on the icon slots
    for cx, hue in [(LEFT_X, (124, 58, 237)), (RIGHT_X, (34, 211, 238))]:
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse((cx - 140, ICON_Y - 130, cx + 140, ICON_Y + 130),
                   fill=(*hue, 60))
        glow = glow.filter(ImageFilter.GaussianBlur(48))
        img.paste(glow, (0, 0), glow)

    # ── title bar (top-left) ─────────────────────────────────────────
    d.text((36, 28), "HARRY", fill="#e2e8f0", font=_font(34))
    d.text((38, 72), "Intelligence · v0.2.0", fill="#94a3b8", font=_font(15))

    # bottom-right caption (subtle, like Claude's installer)
    d.text((W - 36, H - 24), "Drag Harry to Applications",
           fill="#94a3b8", font=_font(13), anchor="rb")

    # ── arrow from .app slot → Applications slot ──────────────────────
    arrow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arrow)
    y = ICON_Y
    x1, x2 = LEFT_X + 78, RIGHT_X - 80
    steps = 60
    for i in range(steps):
        t = i / steps
        x = x1 + (x2 - x1) * t
        r, g, b = (
            int(124 + (34 - 124) * t),
            int(58 + (211 - 58) * t),
            int(237 + (238 - 237) * t),
        )
        ad.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(r, g, b, 200))
    head = [(x2 + 18, y), (x2 - 6, y - 12), (x2 - 6, y + 12)]
    ad.polygon(head, fill=(34, 211, 238, 230))
    arrow = arrow.filter(ImageFilter.GaussianBlur(0.6))
    img.paste(arrow, (0, 0), arrow)

    # ── icon placeholder rings (Finder draws the real icons on top) ───
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for cx, color in [(LEFT_X, (124, 58, 237, 80)),
                      (RIGHT_X, (34, 211, 238, 80))]:
        for r in (84, 72):
            od.ellipse((cx - r, y - r, cx + r, y + r),
                       outline=color, width=1)
    img.paste(overlay, (0, 0), overlay)

    # tick marks framing the install line
    for i in range(36):
        a = (i / 36) * math.tau
        for cx in (LEFT_X, RIGHT_X):
            r1, r2 = 92, 98
            d.line((cx + math.cos(a) * r1, y + math.sin(a) * r1,
                    cx + math.cos(a) * r2, y + math.sin(a) * r2),
                   fill="#1f2937", width=1)

    # macOS Finder treats the DMG background as logical points, not pixels.
    # On a retina display, a 660×400 file at 72 DPI would only cover the
    # upper-left quarter of the window. So we save the @2x version (1320×800)
    # with 144 DPI metadata, which Finder interprets as 660×400 logical
    # points rendered at HiDPI — fills the whole window crisply.
    img2x = img.resize((W * 2, H * 2), Image.LANCZOS)
    out = OUT / "dmg-background.png"
    img2x.save(out, dpi=(144, 144))
    # keep the @1x around too in case anyone wants to inspect the design
    img.save(OUT / "dmg-background@1x.png", dpi=(72, 72))
    return out


if __name__ == "__main__":
    p = make()
    print(f"wrote {p}")
