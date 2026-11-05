"""Draws the final weather art in the panel's four inks and writes it for the firmware.

Run: .venv-esphome\\Scripts\\python.exe design\\art.py
Writes esphome/art/hero_*.png (210x196), esphome/art/icon_*.png (40x40) and docs/art-sheet.png.
"""
import math
from pathlib import Path

from PIL import Image

from panel import BLACK, INKS, RED, SS, WHITE, YELLOW, Canvas, cloud, crescent, disc, mask_of, shaded_cloud, sun_with_glow, tone

ROOT = Path(__file__).parent.parent
ART = ROOT / "esphome" / "art"
DOCS = ROOT / "docs"
HERO_BOX = (190, 0, 400, 196)  # The screen region a hero picture occupies.
ICON = 40


def sky(c, strength, pitch=4 * math.sqrt(2)):  # This pitch lands dots exactly on the pixel grid, avoiding moire.
    """Black halftone sky, fading out towards the text column and the hourly strip."""
    def at(x, y):
        return max(0.0, strength * min(1.0, (x - 192) / 78) * min(1.0, (194 - y) / 44))

    tone(c, BLACK, at, pitch=pitch)


def stars(c, points):
    for x, y, r in points:
        c.rect((x - r, y, x + r, y), YELLOW)
        c.rect((x, y - r, x, y + r), YELLOW)


def streaks(c, spots, color, length=15, width=2):
    for x, y in spots:
        c.shape(color, lambda d, x=x, y=y: d.line(
            [((x + 4) * SS, y * SS), ((x - 3) * SS, (y + length) * SS)], fill=255, width=width * SS))


def bolt(c, x, y, s=1.0):
    points = [(0, 0), (-16, 34), (-3, 34), (-13, 66), (17, 22), (3, 22), (13, 0)]
    scaled = [((x + px * s) * SS, (y + py * s) * SS) for px, py in points]
    outline = [((x + px * s * 1.0) * SS, (y + py * s) * SS) for px, py in points]
    c.shape(BLACK, lambda d: d.line(outline + outline[:1], fill=255, width=5 * SS))
    c.shape(YELLOW, lambda d: d.polygon(scaled, fill=255))


# Hero pictures. Each draws on a full canvas, then the art region is cropped out.
def sunny(c):
    sun_with_glow(c, 300, 96, 62, reach=104, strength=0.46)


def partly(c):
    sun_with_glow(c, 324, 58, 36, reach=84, strength=0.42)
    shaded_cloud(c, 302, 162, 76, shade_depth=36)


def clear_night(c):
    sky(c, 0.58)
    stars(c, [(226, 44, 3), (262, 120, 2), (378, 34, 3), (372, 140, 3), (240, 156, 2), (390, 86, 2)])
    crescent(c, 296, 94, 58, line=0)


def partly_night(c):
    sky(c, 0.58)
    stars(c, [(226, 44, 3), (254, 96, 2), (376, 30, 3), (390, 72, 2)])
    crescent(c, 298, 54, 38, line=0)
    shaded_cloud(c, 302, 162, 76, shade_depth=36)


def cloudy(c):
    far = lambda d: cloud(d, 352, 84, 46)
    c.image.paste(BLACK, (0, 0), mask_of(lambda d: cloud(d, 352, 84, 46, grow=2)))
    c.image.paste(WHITE, (0, 0), mask_of(far))
    tone(c, BLACK, lambda x, y: max(0.0, 0.5 * (y - 50) / 34), mask=mask_of(far), pitch=4.0)
    shaded_cloud(c, 290, 166, 84, shade_depth=40)


def rainy(c, spots=None, color=RED):
    sky(c, 0.3)
    shaded_cloud(c, 298, 108, 86, shade_depth=38, strength=0.62)
    streaks(c, spots or [(236, 126), (268, 134), (300, 126), (332, 134), (364, 126),
                         (252, 160), (284, 168), (316, 160), (348, 168)], color)


def pouring(c):
    spots = [(226 + 24 * i, 124 + 8 * (i % 2)) for i in range(7)] + [(238 + 24 * i, 154 + 8 * (i % 2)) for i in range(6)]
    sky(c, 0.42)
    shaded_cloud(c, 298, 108, 86, shade_depth=38, strength=0.72)
    streaks(c, spots, RED, length=22, width=3)


def flake(c, x, y, r=7, color=BLACK):
    def paint(d):
        for a in range(3):
            t = math.pi * a / 3
            dx, dy = math.cos(t) * r, math.sin(t) * r
            d.line([((x - dx) * SS, (y - dy) * SS), ((x + dx) * SS, (y + dy) * SS)], fill=255, width=2 * SS)
    c.shape(color, paint)


def snowy(c):
    shaded_cloud(c, 298, 108, 86, shade_depth=38)
    for x, y in [(236, 138), (278, 150), (320, 136), (362, 150), (256, 174), (300, 178), (344, 176)]:
        flake(c, x, y)


def sleet(c):
    shaded_cloud(c, 298, 108, 86, shade_depth=38)
    streaks(c, [(236, 130), (320, 130), (278, 162), (362, 162)], RED)
    for x, y in [(278, 138), (362, 138), (240, 174), (322, 174)]:
        flake(c, x, y)


def foggy(c):
    sun_with_glow(c, 300, 60, 36, reach=60, strength=0.2)
    for i, (x0, x1, y) in enumerate([(206, 378, 96), (230, 396, 116), (204, 366, 136), (236, 396, 156), (212, 372, 176)]):
        c.shape(WHITE, lambda d, x0=x0, x1=x1, y=y: d.rounded_rectangle(
            [(x0 - 2) * SS, (y - 8) * SS, (x1 + 2) * SS, (y + 8) * SS], radius=8 * SS, fill=255))
        c.shape(BLACK, lambda d, x0=x0, x1=x1, y=y: d.rounded_rectangle(
            [x0 * SS, (y - 4) * SS, x1 * SS, (y + 3) * SS], radius=3 * SS, fill=255))


def stormy(c, rain=False):
    sky(c, 0.42)
    shaded_cloud(c, 298, 106, 86, shade_depth=38, strength=0.72)
    if rain:
        streaks(c, [(232, 128), (260, 150), (350, 128), (374, 150)], RED)
    bolt(c, 298, 116)


def windy(c):
    # Three gusts, each a line ending in an upward curl, kept inside the art region.
    for x0, x1, y, r in [(208, 336, 74, 16), (226, 366, 112, 16), (208, 318, 150, 14)]:
        def paint(d, x0=x0, x1=x1, y=y, r=r):
            d.line([(x0 * SS, y * SS), (x1 * SS, y * SS)], fill=255, width=6 * SS)
            box = [(x1 - r) * SS, (y - 2 * r) * SS, (x1 + r) * SS, y * SS]
            d.arc(box, start=-180, end=90, fill=255, width=6 * SS)
        c.shape(BLACK, paint)


HEROES = {
    "sunny": sunny, "partly": partly, "clear_night": clear_night, "partly_night": partly_night,
    "cloudy": cloudy, "rainy": rainy, "pouring": pouring, "snowy": snowy, "sleet": sleet,
    "foggy": foggy, "stormy": stormy, "storm_rain": lambda c: stormy(c, rain=True), "windy": windy,
}


# Small icons, centred at (100, 100) on a scratch canvas and then cropped.
def icon_cloud(c, x, y, line=2):
    c.shape(BLACK, lambda d: cloud(d, x, y, 14, grow=line))
    c.shape(WHITE, lambda d: cloud(d, x, y, 14))


def small_sun(c, x, y, r):
    c.shape(BLACK, disc(x, y, r + 2))
    c.shape(YELLOW, disc(x, y, r))


def icon(kind):
    c = Canvas()
    x, y = 100, 100
    if kind == "sun":
        small_sun(c, x, y, 12)
    elif kind == "partly":
        small_sun(c, x + 7, y - 6, 8)
        icon_cloud(c, x, y + 9)
    elif kind == "moon":
        crescent(c, x - 1, y, 13)
    elif kind == "partly_moon":
        crescent(c, x + 7, y - 7, 9, bite=0.6)
        icon_cloud(c, x, y + 9)
    elif kind == "cloud":
        icon_cloud(c, x, y + 8)
    elif kind in ("rain", "pour"):
        icon_cloud(c, x, y + 2)
        xs = (-8, 0, 8) if kind == "rain" else (-11, -4, 3, 10)
        for dx in xs:
            c.shape(RED, lambda d, dx=dx: d.line([((x + dx + 2) * SS, (y + 6) * SS), ((x + dx - 2) * SS, (y + 15) * SS)], fill=255, width=2 * SS))
    elif kind == "snow":
        icon_cloud(c, x, y + 2)
        for dx in (-9, 0, 9):
            flake(c, x + dx, y + 11, r=4)
    elif kind == "sleet":
        icon_cloud(c, x, y + 2)
        c.shape(RED, lambda d: d.line([((x - 6) * SS, (y + 6) * SS), ((x - 10) * SS, (y + 15) * SS)], fill=255, width=2 * SS))
        flake(c, x + 6, y + 11, r=4)
    elif kind == "fog":
        for i, dy in enumerate((-9, -2, 5, 12)):
            inset = 3 if i % 2 else 0
            c.rect((x - 15 + inset, y + dy, x + 15 - inset, y + dy + 2), BLACK)
    elif kind == "storm":
        icon_cloud(c, x, y + 1)
        c.shape(BLACK, lambda d: d.polygon([((x + a) * SS, (y + b) * SS) for a, b in ((2, 2), (-6, 12), (-1, 12), (-4, 19), (6, 8), (1, 8), (5, 2))], fill=255))
        c.shape(YELLOW, lambda d: d.polygon([((x + a) * SS, (y + b) * SS) for a, b in ((2, 4), (-3, 11), (0, 11), (-2, 16), (4, 9), (0, 9), (3, 4))], fill=255))
    elif kind == "wind":
        for dy, w in ((-7, 13), (0, 15), (7, 10)):
            c.rect((x - 14, y + dy, x - 14 + 2 * w, y + dy + 2), BLACK)
    half = ICON // 2
    return c.image.crop((x - half, y - half, x + half, y + half))


ICONS = ["sun", "partly", "moon", "partly_moon", "cloud", "rain", "pour", "snow", "sleet", "fog", "storm", "wind"]


def main():
    ART.mkdir(exist_ok=True)
    heroes = {}
    for name, draw in HEROES.items():
        c = Canvas()
        draw(c)
        hero = c.image.crop(HERO_BOX)
        assert {col for _, col in hero.getcolors(maxcolors=64)} <= INKS, name
        hero.save(ART / f"hero_{name}.png")
        heroes[name] = hero
    icons = {}
    for name in ICONS:
        im = icon(name)
        assert {col for _, col in im.getcolors(maxcolors=64)} <= INKS, name
        im.save(ART / f"icon_{name}.png")
        icons[name] = im

    columns = 4
    rows = math.ceil(len(heroes) / columns)
    sheet = Image.new("RGB", (columns * 220, rows * 206 + 50), (120, 120, 120))
    for i, hero in enumerate(heroes.values()):
        sheet.paste(hero, (5 + (i % columns) * 220, 5 + (i // columns) * 206))
    for i, im in enumerate(icons.values()):
        sheet.paste(im, (5 + i * 45, rows * 206 + 5))
    DOCS.mkdir(exist_ok=True)
    sheet.save(DOCS / "art-sheet.png")
    print("heroes:", len(heroes), "icons:", len(icons))


if __name__ == "__main__":
    main()
