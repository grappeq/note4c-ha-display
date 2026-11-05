"""Renders sample screens from the finished art, mirroring the layout in esphome/note4c.yaml.

Run: python design/preview.py  (needs Pillow and requests; run art.py first)
Writes docs/preview-day.png and docs/preview-night.png at 2x. These use sample data and approximate
the panel: the firmware draws its own text, and real inks are more muted than these colours.
"""
import re
from pathlib import Path

import requests
from PIL import Image, ImageFont

from panel import BLACK, H, INKS, RED, W, Canvas

ROOT = Path(__file__).parent.parent
ART = ROOT / "esphome" / "art"
DOCS = ROOT / "docs"
FONT_DIR = Path(__file__).parent / "fonts"  # Downloaded on first use, not kept in the repo.
MINUS = "−"

DAY = {
    "hero": "partly", "temp": f"{MINUS}1°", "lines": ("Częściowe", "zachmurzenie"), "range": f"3° / {MINUS}2°",
    "hours": [("teraz", "partly", f"{MINUS}1°"), ("10", "partly", "0°"), ("11", "sun", "1°"), ("12", "sun", "2°"),
              ("13", "partly", "3°"), ("14", "cloud", "3°"), ("15", "rain", "2°"), ("16", "rain", "1°")],
}
NIGHT = {
    "hero": "clear_night", "temp": f"{MINUS}1°", "lines": ("Bezchmurnie", ""), "range": f"6° / 1°",
    "hours": [("teraz", "moon", f"{MINUS}1°"), ("0", "partly_moon", "2°"), ("1", "partly_moon", "2°"), ("2", "fog", "3°"),
              ("3", "fog", "3°"), ("4", "partly_moon", "3°"), ("5", "partly_moon", "2°"), ("6", "cloud", "2°")],
}


def outfit(weight, size):
    path = FONT_DIR / f"outfit-{weight}.ttf"
    if not path.exists():
        FONT_DIR.mkdir(exist_ok=True)
        css = requests.get("https://fonts.googleapis.com/css2", params={"family": f"Outfit:wght@{weight}"}, timeout=30).text
        url = re.search(r"url\((https://[^)]+\.ttf)\)", css).group(1)
        path.write_bytes(requests.get(url, timeout=60).content)
    return ImageFont.truetype(str(path), size)


def render(data, name):
    c = Canvas()
    c.image.paste(Image.open(ART / f"hero_{data['hero']}.png").convert("RGB"), (190, 0))
    c.text((22, 36), "Ogródek", outfit(500, 20), BLACK)
    c.text((18, 106), data["temp"], outfit(700, 72), BLACK)
    c.text((22, 136), data["lines"][0], outfit(500, 18), BLACK)
    c.text((22, 157), data["lines"][1], outfit(500, 18), BLACK)
    c.text((22, 184), data["range"], outfit(700, 20), RED)
    columns = len(data["hours"])
    for i, (hour, icon, temp) in enumerate(data["hours"]):
        x = 400 * i // columns + 200 // columns
        c.text((x, 216), hour, outfit(700 if i == 0 else 500, 14), RED if i == 0 else BLACK, anchor="ms")
        c.image.paste(Image.open(ART / f"icon_{icon}.png").convert("RGB"), (x - 20, 218))
        c.text((x, 280), temp, outfit(700, 17), BLACK, anchor="ms")
    assert {col for _, col in c.image.getcolors(maxcolors=64)} <= INKS, name
    DOCS.mkdir(exist_ok=True)
    c.image.resize((W * 2, H * 2), Image.NEAREST).save(DOCS / f"preview-{name}.png")


if __name__ == "__main__":
    render(DAY, "day")
    render(NIGHT, "night")
