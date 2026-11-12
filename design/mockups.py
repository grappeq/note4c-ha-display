"""Mockups for proposed screens: notifications and battery alerts. Not used by the firmware.

Run: python design/mockups.py  (needs Pillow and requests; run art.py first)
Writes docs/mockups/*.png at 2x, in the same approximation of the panel as preview.py.
"""
from PIL import Image

from panel import BLACK, H, INKS, RED, W, WHITE, YELLOW, Canvas, tone
from preview import ART, DAY, DOCS, MINUS, outfit

OUT = DOCS / "mockups"


def wrap(text, font, width, max_lines):
    """Greedy word wrap, ending with an ellipsis when the text doesn't fit. The firmware would do the same."""
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if font.getlength(candidate) <= width:
            line = candidate
            continue
        lines.append(line)
        line = word
        if len(lines) == max_lines:
            break
    else:
        lines.append(line)
        return lines[:max_lines]
    last = lines[-1]
    while font.getlength(last + "…") > width:
        last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
    return lines[:-1] + [last + "…"]


def weather_top(c, data=DAY):
    c.image.paste(Image.open(ART / f"hero_{data['hero']}.png").convert("RGB"), (190, 0))
    c.text((22, 36), "Ogródek", outfit(500, 20), BLACK)
    c.text((18, 106), data["temp"], outfit(700, 72), BLACK)
    c.text((22, 136), data["lines"][0], outfit(500, 18), BLACK)
    c.text((22, 157), data["lines"][1], outfit(500, 18), BLACK)
    c.text((22, 184), data["range"], outfit(700, 20), RED)


def hourly(c, data=DAY):
    columns = len(data["hours"])
    for i, (hour, icon, temp) in enumerate(data["hours"]):
        x = 400 * i // columns + 200 // columns
        c.text((x, 216), hour, outfit(700 if i == 0 else 500, 14), RED if i == 0 else BLACK, anchor="ms")
        c.image.paste(Image.open(ART / f"icon_{icon}.png").convert("RGB"), (x - 20, 218))
        c.text((x, 280), temp, outfit(700, 17), BLACK, anchor="ms")


def button_hint(c, x, y, text, color=BLACK):
    """A small round-button symbol, matching the BOOT button's shape, followed by a hint."""
    c.draw.ellipse((x, y - 10, x + 10, y), outline=color, width=2)
    c.draw.ellipse((x + 3, y - 7, x + 7, y - 3), fill=color)
    c.text((x + 15, y), text, outfit(500, 13), color)


def battery_icon(c, x, y, w=24, h=12, level=1, color=RED, line=2):
    """Battery outline with `level` filled bars out of four. (x, y) is the top left."""
    c.rect((x, y, x + w, y + h), BLACK)
    c.rect((x + line, y + line, x + w - line, y + h - line), WHITE)
    c.rect((x + w + 1, y + h // 3, x + w + line + 1, y + h - h // 3), BLACK)
    inner = w - 2 * line - 2
    bar = (inner - 3) // 4
    for i in range(level):
        bx = x + line + 1 + i * (bar + 1)
        c.rect((bx, y + line + 1, bx + bar - 1, y + h - line - 1), color)


def status_pill(c, text, icon=False):
    c.rect((196, 166, 393, 191), RED)
    c.rect((198, 168, 391, 189), WHITE)
    font = outfit(700, 15)
    if not icon:
        c.text((295, 184), text, font, RED, anchor="ms")
        return
    width = 30 + font.getlength(text)
    x = 295 - width / 2
    battery_icon(c, int(x), 173, w=20, h=11)
    c.text((x + 30, 184), text, font, RED)


def notice_card(c, title, message, index, count):
    """Replaces the hourly strip. The weather above stays, so the screen is still useful."""
    c.rect((0, 197, W - 1, H - 1), WHITE)
    c.rect((8, 200, 391, 296), BLACK)
    c.rect((10, 202, 389, 294), WHITE)
    c.rect((10, 202, 15, 294), RED)
    title_font, body_font = outfit(700, 17), outfit(500, 16)
    counter = f"{index}/{count}" if count > 1 else ""
    if counter:
        c.text((380, 221), counter, outfit(700, 14), RED, anchor="rs")
    c.text((25, 221), wrap(title, title_font, 330, 1)[0], title_font, BLACK)
    for n, line in enumerate(wrap(message, body_font, 352, 2)):
        c.text((25, 243 + n * 20), line, body_font, BLACK)
    button_hint(c, 25, 287, "przytrzymaj, aby odrzucić", RED)


def save(c, name):
    assert {col for _, col in c.image.getcolors(maxcolors=64)} <= INKS, name
    OUT.mkdir(parents=True, exist_ok=True)
    c.image.resize((W * 2, H * 2), Image.NEAREST).save(OUT / f"{name}.png")


def today():
    c = Canvas()
    weather_top(c)
    hourly(c)
    status_pill(c, "Niski stan baterii")
    save(c, "battery-today")


def battery_low():
    c = Canvas()
    weather_top(c)
    hourly(c)
    status_pill(c, "Naładuj baterię", icon=True)
    save(c, "battery-low")


def battery_critical():
    c = Canvas()
    # A yellow halftone wash says "not normal" from across the room without using the warning red.
    tone(c, YELLOW, lambda x, y: 0.32, pitch=6.0)
    c.rect((40, 40, 359, 259), WHITE)
    c.rect((40, 40, 359, 259), BLACK)
    c.rect((43, 43, 356, 256), WHITE)
    battery_icon(c, 140, 70, w=110, h=52, level=0, line=6)
    c.rect((152, 82, 164, 110), RED)  # One thin red sliver: nearly empty.
    c.text((200, 166), "Naładuj baterię", outfit(700, 30), BLACK, anchor="ms")
    c.text((200, 196), "Ekran się teraz nie odświeża.", outfit(500, 17), BLACK, anchor="ms")
    c.text((200, 218), "Wróci sam po podłączeniu ładowarki.", outfit(500, 17), BLACK, anchor="ms")
    c.text((200, 244), "Ostatnie dane: wt. 14:20", outfit(700, 15), RED, anchor="ms")
    save(c, "battery-critical")


def notice_band():
    c = Canvas()
    weather_top(c)
    notice_card(c, "Pralka skończyła pranie",
                "Pranie czeka w pralce od 18:40. Rozwieś je, zanim zacznie brzydko pachnieć.", 1, 3)
    save(c, "notice-band")


def notice_band_battery():
    c = Canvas()
    weather_top(c)
    status_pill(c, "Naładuj baterię", icon=True)
    notice_card(c, "Otwarte okno w sypialni", "Okno jest otwarte od 2 godzin, a na zewnątrz jest −1°.", 1, 1)
    save(c, "notice-band-battery")


def notice_full():
    c = Canvas()
    c.rect((0, 0, W - 1, 47), RED)
    c.text((18, 31), "Powiadomienie", outfit(700, 20), WHITE)
    c.text((382, 31), "2/3", outfit(700, 18), WHITE, anchor="rs")
    title_font, body_font = outfit(700, 26), outfit(500, 20)
    y = 88
    for line in wrap("Wyciek wody w łazience", title_font, 364, 2):
        c.text((18, y), line, title_font, BLACK)
        y += 32
    y += 6
    for line in wrap("Czujnik pod umywalką wykrył wodę o 07:12. Zawór główny został zamknięty automatycznie. "
                     "Sprawdź łazienkę i otwórz zawór w aplikacji.", body_font, 364, 5):
        c.text((18, y), line, body_font, BLACK)
        y += 25
    c.rect((0, 264, W - 1, 265), BLACK)
    button_hint(c, 18, 288, "przytrzymaj, aby odrzucić")
    c.text((382, 288), f"Ogródek {MINUS}1°", outfit(700, 15), BLACK, anchor="rs")
    save(c, "notice-full")


if __name__ == "__main__":
    today()
    battery_low()
    battery_critical()
    notice_band()
    notice_band_battery()
    notice_full()
