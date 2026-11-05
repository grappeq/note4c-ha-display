"""Drawing helpers for the panel: its four inks, hard edges, and halftone dots for extra tones."""
import math

from PIL import Image, ImageDraw

W, H, SS = 400, 300, 4  # Panel size, and the supersampling used for smooth curves.
BLACK, WHITE, RED, YELLOW = (0, 0, 0), (255, 255, 255), (255, 0, 0), (255, 255, 0)
INKS = {BLACK, WHITE, RED, YELLOW}

_COS, _SIN = math.cos(math.radians(45)), math.sin(math.radians(45))


class Canvas:
    def __init__(self, background=WHITE):
        self.image = Image.new("RGB", (W, H), background)
        self.draw = ImageDraw.Draw(self.image)
        self.draw.fontmode = "1"  # Same as ESPHome's 1-bit fonts: no grey edge pixels.

    def shape(self, color, painter):
        """Draws a shape at 4x in panel coordinates, then thresholds it to hard edges."""
        self.image.paste(color, (0, 0), mask_of(painter))

    def rect(self, box, color):
        self.draw.rectangle(box, fill=color)

    def text(self, xy, text, font, color, anchor="ls"):
        self.draw.text(xy, text, font=font, fill=color, anchor=anchor)


def mask_of(painter):
    mask = Image.new("L", (W * SS, H * SS), 0)
    painter(ImageDraw.Draw(mask))
    return mask.resize((W, H), Image.BOX).point(lambda v: 255 if v >= 128 else 0)


def disc(x, y, r):
    return lambda d: d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=255)


def halftone(x, y, pitch=5.0):
    """Screen value in 0..1 on a 45-degree dot grid. Lower values fill first, so dots grow with tone."""
    u = (x * _COS + y * _SIN) * 2 * math.pi / pitch
    v = (-x * _SIN + y * _COS) * 2 * math.pi / pitch
    return (2 - math.cos(u) - math.cos(v)) / 4


def tone(c, color, tone_at, mask=None, pitch=5.0):
    """Prints `color` as dots wherever the screen is below tone_at(x, y), optionally inside a mask."""
    px = c.image.load()
    m = mask.load() if mask else None
    for y in range(H):
        for x in range(W):
            if m and not m[x, y]:
                continue
            t = tone_at(x, y)
            if t > 0 and halftone(x, y, pitch) < t:
                px[x, y] = color


def cloud(d, x, y, s, grow=0.0):
    """A cloud with its base centred on (x, y) and a width of about 2*s, in panel coordinates."""
    g = grow
    blobs = [(-0.58, -0.30, 0.42), (-0.05, -0.56, 0.58), (0.56, -0.34, 0.44)]
    for bx, by, r in blobs:
        cx, cy, rr = x + bx * s, y + by * s, r * s + g
        d.ellipse([(cx - rr) * SS, (cy - rr) * SS, (cx + rr) * SS, (cy + rr) * SS], fill=255)
    d.rounded_rectangle([(x - s - g) * SS, (y - 0.42 * s - g) * SS, (x + s + g) * SS, (y + g) * SS],
                        radius=(0.28 * s + g) * SS, fill=255)


def sun_with_glow(c, sx, sy, sr, reach=118, strength=0.44):
    def glow(x, y):
        dist = math.hypot(x - sx, y - sy)
        # Keeps a clear white ring around the sun, and fades out before reaching the text.
        return 0.0 if dist < sr + 7 else max(0.0, strength * (1 - (dist - sr) / reach))

    tone(c, YELLOW, glow, pitch=6.0)
    sun = mask_of(disc(sx, sy, sr))
    c.image.paste(YELLOW, (0, 0), sun)
    # Warm core: red dots build towards the sun's lower edge, reading as orange.
    tone(c, RED, lambda x, y: max(0.0, 0.42 * ((y - sy + sr * 0.2) / (sr * 1.2))), mask=sun, pitch=4.0)


def shaded_cloud(c, cx, cy, cs, shade_top=None, shade_depth=42, offset=(7, 7), strength=0.5):
    """A white cloud with halftone shading, a thin outline and an offset red "misprint" shadow."""
    c.image.paste(RED, (0, 0), mask_of(lambda d: cloud(d, cx + offset[0], cy + offset[1], cs)))
    c.image.paste(BLACK, (0, 0), mask_of(lambda d: cloud(d, cx, cy, cs, grow=2)))
    main = mask_of(lambda d: cloud(d, cx, cy, cs))
    c.image.paste(WHITE, (0, 0), main)
    top = cy - shade_depth if shade_top is None else shade_top
    tone(c, BLACK, lambda x, y: max(0.0, strength * (y - top) / shade_depth), mask=main, pitch=4.5)


def crescent(c, x, y, r, line=2, color=YELLOW, bite=0.62):
    """A crescent moon. Its inner curve is cut away, so whatever is behind it shows through."""
    bx, by, br = x + r * bite, y - r * 0.28, r * 0.86

    def moon_mask(grow):
        whole = mask_of(disc(x, y, r + grow))
        cut = mask_of(disc(bx, by, br - grow))
        return Image.composite(Image.new("L", (W, H), 0), whole, cut)

    if line:
        c.image.paste(BLACK, (0, 0), moon_mask(line))
    c.image.paste(color, (0, 0), moon_mask(0))
