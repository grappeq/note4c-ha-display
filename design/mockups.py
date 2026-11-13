"""Renders the notice and battery screens, mirroring the layout in esphome/note4c.yaml.

Run: python design/mockups.py  (needs Pillow and requests; run art.py first)
Writes docs/mockups/*.png at 2x. Like preview.py, these use sample data and approximate the panel.
"""
from PIL import Image

from panel import BLACK, H, INKS, RED, W, WHITE, YELLOW, Canvas
from preview import ART, DAY, DOCS, MINUS, outfit

OUT = DOCS / "mockups"
LABEL = "Ogródek"
HINT = "przytrzymaj, aby odrzucić"


def ellipsize(text, font, width):
    """Shortens text to fit, ending with an ellipsis. Drops whole words where it can."""
    while text and font.getlength(text + "…") > width:
        text = text.rsplit(" ", 1)[0] if " " in text else text[:-1]
    return text + "…"


def wrap(text, font, width, max_lines):
    """Greedy word wrap, the same as the firmware's. The last line ends with an ellipsis when the text doesn't fit."""
    lines, line, overflow = [], "", False
    for word in text.split():
        candidate = f"{line} {word}" if line else word
        if not line or font.getlength(candidate) <= width:
            line = candidate
            continue
        lines.append(line)
        line = word
        if len(lines) == max_lines:
            overflow = True
            break
    if not overflow and line:
        lines.append(line)
    return [ellipsize(l, font, width) if (overflow and i == len(lines) - 1) or font.getlength(l) > width else l
            for i, l in enumerate(lines)]


def weather_top(c, data=DAY):
    c.image.paste(Image.open(ART / f"hero_{data['hero']}.png").convert("RGB"), (190, 0))
    c.text((22, 36), LABEL, outfit(500, 20), BLACK)
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


def circle(c, cx, cy, r, color):
    c.draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)


def button_hint(c, x, y, text, color):
    """The round BOOT button, followed by a hint. (x, y) is the left end of the baseline."""
    circle(c, x + 5, y - 5, 5, color)
    circle(c, x + 5, y - 5, 3, WHITE)
    circle(c, x + 5, y - 5, 2, color)
    c.text((x + 15, y), text, outfit(500, 13), color)


def battery_icon(c, x, y, w, h, level, line):
    """Battery outline with `level` of four bars filled. (x, y) is the top left."""
    c.rect((x, y, x + w, y + h), BLACK)
    c.rect((x + line, y + line, x + w - line, y + h - line), WHITE)
    c.rect((x + w + 1, y + h // 3, x + w + line + 1, y + h - h // 3), BLACK)
    bar = (w - 2 * line - 2 - 3) // 4
    for i in range(level):
        bx = x + line + 1 + i * (bar + 1)
        c.rect((bx, y + line + 1, bx + bar - 1, y + h - line - 1), RED)


def status_box(c, text, battery=False):
    c.rect((196, 166, 393, 191), RED)
    c.rect((198, 168, 391, 189), WHITE)
    font = outfit(700, 15)
    if not battery:
        c.text((295, 184), text, font, RED, anchor="ms")
        return
    x = 295 - (30 + round(font.getlength(text))) // 2
    battery_icon(c, x, 173, 20, 11, 1, 2)
    c.text((x + 30, 184), text, font, RED)


def notice_card(c, title, message, count):
    """Takes the place of the hourly forecast."""
    c.rect((8, 200, 391, 296), BLACK)
    c.rect((10, 202, 389, 294), WHITE)
    c.rect((10, 202, 15, 294), RED)
    if count > 1:
        c.text((380, 221), f"1/{count}", outfit(700, 15), RED, anchor="rs")
    title_font, body_font = outfit(700, 17), outfit(500, 16)
    c.text((25, 221), wrap(title, title_font, 330, 1)[0], title_font, BLACK)
    for n, line in enumerate(wrap(message, body_font, 352, 2)):
        c.text((25, 243 + n * 20), line, body_font, BLACK)
    button_hint(c, 25, 287, HINT, RED)


def notice_full(c, title, message, count, footer):
    """A priority notice takes the whole screen. The temperature moves to the footer."""
    c.rect((0, 0, W - 1, 47), RED)
    c.text((18, 31), "Powiadomienie", outfit(700, 20), WHITE)
    if count > 1:
        c.text((382, 31), f"1/{count}", outfit(700, 20), WHITE, anchor="rs")
    title_font, body_font = outfit(700, 26), outfit(500, 20)
    y = 88
    for line in wrap(title, title_font, 364, 2):
        c.text((18, y), line, title_font, BLACK)
        y += 32
    y += 6
    for line in wrap(message, body_font, 364, (258 - y) // 25 + 1):
        c.text((18, y), line, body_font, BLACK)
        y += 25
    c.rect((0, 264, W - 1, 265), BLACK)
    button_hint(c, 18, 288, HINT, BLACK)
    c.text((382, 288), footer, outfit(700, 15), BLACK, anchor="rs")


def critical(c, last_data):
    # A yellow dot screen says "not normal" from across the room, without the warning red.
    for y in range(0, H, 6):
        for x in range(3 if (y // 6) % 2 else 0, W, 6):
            c.rect((x, y, x + 1, y + 1), YELLOW)
    c.rect((40, 40, 359, 259), BLACK)
    c.rect((43, 43, 356, 256), WHITE)
    battery_icon(c, 140, 70, 110, 52, 0, 6)
    c.rect((152, 82, 164, 110), RED)
    c.text((200, 166), "Naładuj baterię", outfit(700, 26), BLACK, anchor="ms")
    c.text((200, 196), "Ekran się teraz nie odświeża.", outfit(500, 18), BLACK, anchor="ms")
    c.text((200, 218), "Wróci sam po podłączeniu ładowarki.", outfit(500, 18), BLACK, anchor="ms")
    c.text((200, 244), f"Ostatnie dane: {last_data}", outfit(700, 15), RED, anchor="ms")


def save(c, name):
    assert {col for _, col in c.image.getcolors(maxcolors=64)} <= INKS, name
    OUT.mkdir(parents=True, exist_ok=True)
    c.image.resize((W * 2, H * 2), Image.NEAREST).save(OUT / f"{name}.png")


def screen(name, notice=None, status=None, battery=False):
    c = Canvas()
    weather_top(c)
    if notice:
        notice_card(c, *notice)
    else:
        hourly(c)
    if status:
        status_box(c, status, battery)
    save(c, name)


if __name__ == "__main__":
    screen("battery-low", status="Naładuj baterię", battery=True)
    screen("battery-low-stale", status="Dane z 14:20", battery=True)
    screen("notice-card", notice=("Pralka skończyła pranie",
                                  "Pranie czeka w pralce od 18:40. Rozwieś je, zanim zacznie brzydko pachnieć.", 3))
    screen("notice-card-battery", notice=("Otwarte okno w sypialni",
                                          f"Okno jest otwarte od 2 godzin, a na zewnątrz jest {MINUS}1°.", 1),
           status="Naładuj baterię", battery=True)
    c = Canvas()
    notice_full(c, "Wyciek wody w łazience", "Czujnik pod umywalką wykrył wodę o 07:12. Zawór główny został zamknięty "
                "automatycznie. Sprawdź łazienkę i otwórz zawór w aplikacji.", 2, f"{LABEL} {MINUS}1°")
    save(c, "notice-full")
    c = Canvas()
    critical(c, "12.11, 14:20")
    save(c, "battery-critical")
