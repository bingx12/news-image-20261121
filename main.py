#!/usr/bin/env python3
"""THE WORLD TODAY — Saturday 21 November 2026, in one image.

A pure-stdlib Python 3.13 program. It draws a newspaper front page summing
up the real news of 21 November 2026 and writes it to /output/entry.png
(1024x1024 PNG, deterministic: two runs produce identical bytes).

No network, no file reads outside its own directory, no clock, no random.
Text comes from a bitmap font atlas (font_data.py) generated at build time
from DejaVu Sans at one base size and scaled to each text size at draw
time; this program only ever reads that atlas.

Stories (all happened or first reported 21 Nov 2026; sources in README):
  LEAD    Russia's biggest strikes of the year on Ukraine; missiles land
          in Poland — Tusk calls it a deliberate provocation.
  MARKETS AI sell-off: Nasdaq -5.28%, S&P 500 -3.70% into correction,
          Nasdaq erases all 2026 gains; Nikkei -5.06%.
  UK-EU   Britain and the EU sign their biggest post-Brexit deal: food
          trade, carbon markets, youth mobility, Erasmus+.
  CLIMATE COP31 in Antalya runs into overtime, deadlocked on fossil fuels.
  SCIENCE Daraxonrasib + chemo: tumours shrank or vanished in 60.7% of
          61 pancreatic-cancer patients; undetectable in 1 in 12.
  EARTH   Magnitude 6.8 quake in Peru's Junin region, felt in Lima.
  ALSO    FBI crime database hacked; Bayer's $7.25bn Roundup deal;
          Houthi missiles at Riyadh intercepted; Basra fire kills 4.
"""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from font_data import FONTS

W, H = 1024, 1024
OUT = "/output/entry.png"

# ---- palette -------------------------------------------------------------
PAPER = (250, 246, 236)
INK = (26, 26, 26)
RED = (178, 34, 34)
DARKRED = (140, 22, 22)
NAVY = (16, 36, 64)
NAVY2 = (24, 52, 88)
BLUE = (30, 84, 145)
GOLD = (176, 141, 45)
GREY = (110, 106, 98)
LGREY = (214, 208, 196)
GREEN = (34, 110, 60)
WHITE = (255, 255, 255)
CREAM = (238, 231, 214)
SKY = (140, 180, 210)


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def rect(self, x, y, w, h, c, t=1):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, c)
                else:
                    if r * r - 2 * r <= d2 <= r * r:
                        self.set(xx, yy, c)

    def poly(self, pts, c):
        """Even-odd scanline polygon fill."""
        if not pts:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self.set(x, y, c)


# ---- text ----------------------------------------------------------------
# The atlas holds DejaVu Book + Bold at ONE base size (64 px). Each old
# font key maps to (atlas weight, target pixel size); bitmaps and metrics
# are scaled down at draw time with nearest-neighbour sampling, so the
# atlas stays small enough for the kit's authored-lines check.
BASE_SIZE = 64
FONT_MAP = {
    "MAST": ("BOLD", 62),
    "HEAD": ("BOLD", 40),
    "SUB": ("BOLD", 26),
    "BODY": ("BOOK", 19),
    "SMALL": ("BOOK", 16),
    "SMB": ("BOLD", 16),
    "TINY": ("BOOK", 13),
    "TINYB": ("BOLD", 13),
}


def _scaled(v, size):
    """Scale a base-size-64 metric to `size` px, truncated toward zero.

    Truncation (not rounding) is deliberate: it reproduces the native-size
    rendering's line breaks exactly, so wrapped paragraphs keep the same
    breaks the layout was designed around.
    """
    n = v * size
    if n >= 0:
        return n // BASE_SIZE
    return -((-n) // BASE_SIZE)


def _scaled_up(v, size):
    """Scale a base-size-64 bitmap extent to `size` px, rounded up.

    Extents round UP, unlike metrics: truncating a glyph's height would
    drop its bottom rows (the foot of E, the bowl of B) from the sampled
    bitmap. Rounding up keeps every source row reachable.
    """
    return -((-v * size) // BASE_SIZE)


def text_width(font_key, text):
    base, size = FONT_MAP[font_key]
    font = FONTS[base]
    total = 0
    for ch in text:
        g = font.get(ch)
        if g is None:
            g = font[" "]
        total += _scaled(g[0], size)
    return total


def draw_text(cv, font_key, x, y, text, color):
    """Draw text with its top at y. Returns the width drawn."""
    base, size = FONT_MAP[font_key]
    font = FONTS[base]
    pen = x
    for ch in text:
        g = font.get(ch)
        if g is None:
            g = font[" "]
        adv, w, h, xoff, yoff, rows = g
        sw = _scaled_up(w, size)
        sh = _scaled_up(h, size)
        gx = pen + _scaled(xoff, size)
        gy = y + _scaled(yoff, size)
        if w and h:
            for oy in range(sh):
                row = rows[oy * BASE_SIZE // size]
                for ox in range(sw):
                    rx = ox * BASE_SIZE // size
                    if row[rx // 8] & (0x80 >> (rx % 8)):
                        cv.set(gx + ox, gy + oy, color)
        pen += _scaled(adv, size)
    return pen - x


def draw_text_centered(cv, font_key, cx, y, text, color):
    w = text_width(font_key, text)
    draw_text(cv, font_key, cx - w // 2, y, text, color)
    return w


def wrap(font_key, text, max_w):
    """Greedy word wrap. Returns a list of lines."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(font_key, trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            # A single word wider than the column: hard-split it.
            while text_width(font_key, word) > max_w and len(word) > 1:
                cut = len(word)
                while cut > 1 and text_width(font_key, word[:cut]) > max_w:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, font_key, x, y, text, max_w, color, leading=None):
    """Draw a wrapped paragraph. Returns the y just below the last line."""
    if leading is None:
        leading = {"MAST": 66, "HEAD": 46, "SUB": 32, "BODY": 24,
                   "SMALL": 20, "SMB": 20, "TINY": 16, "TINYB": 16}[font_key]
    for line in wrap(font_key, text, max_w):
        draw_text(cv, font_key, x, y, line, color)
        y += leading
    return y


def rule(cv, x, y, w, color=INK, t=2):
    cv.hline(x, y, w, color, t)


# ---- PNG encoder (stdlib only, deterministic) ----------------------------
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: None
        raw += cv.px[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


# ---- page ----------------------------------------------------------------
def draw_masthead(cv):
    cv.hline(0, 0, W, RED, 7)
    draw_text_centered(cv, "MAST", W // 2, 16, "THE WORLD TODAY", INK)
    rule(cv, 28, 96, W - 56, INK, 2)
    draw_text_centered(cv, "SMB", W // 2, 104,
                       "SATURDAY 21 NOVEMBER 2026", INK)
    draw_text(cv, "TINY", 28, 106, "ONE IMAGE · THE WHOLE DAY", GREY)
    draw_text(cv, "TINY", W - 28 - text_width("TINY", "PRICE: ONE DAY"),
              106, "PRICE: ONE DAY", GREY)


def draw_lead_map(cv, x, y, w, h):
    """War map: night-blue panel, Poland/Ukraine land, strikes, arcs."""
    cv.fill_rect(x, y, w, h, NAVY)
    cv.rect(x, y, w, h, INK, 2)
    # Simplified landmass: western Europe (left), Ukraine/Poland (centre).
    cv.poly([(x + 8, y + 150), (x + 60, y + 120), (x + 130, y + 128),
             (x + 170, y + 100), (x + 240, y + 96), (x + 300, y + 120),
             (x + 318, y + 180), (x + 300, y + 250), (x + 220, y + 300),
             (x + 120, y + 296), (x + 40, y + 260), (x + 10, y + 210)],
            NAVY2)
    # Poland (highlighted) and Ukraine (highlighted) as rough shapes.
    cv.poly([(x + 96, y + 96), (x + 150, y + 88), (x + 176, y + 104),
             (x + 168, y + 138), (x + 120, y + 146), (x + 96, y + 122)],
            (58, 96, 140))
    cv.poly([(x + 176, y + 104), (x + 250, y + 96), (x + 296, y + 128),
             (x + 288, y + 196), (x + 220, y + 208), (x + 168, y + 138)],
            (88, 120, 158))
    # Missile arcs from the east.
    for (ax, ay, bx, by) in [(x + 320, y + 60, x + 210, y + 150),
                             (x + 326, y + 120, x + 240, y + 170),
                             (x + 318, y + 200, x + 250, y + 190)]:
        mx, my = (ax + bx) // 2, min(ay, by) - 26
        for t in range(0, 21):
            tt = t / 20.0
            px = int((1 - tt) ** 2 * ax + 2 * (1 - tt) * tt * mx + tt * tt * bx)
            py = int((1 - tt) ** 2 * ay + 2 * (1 - tt) * tt * my + tt * tt * by)
            if t % 2 == 0:
                cv.set(px, py, (255, 120, 90))
                cv.set(px + 1, py, (255, 120, 90))
    # Strike markers: Kyiv and the Polish impact site.
    cv.circle(x + 238, y + 168, 7, RED, fill=True)
    cv.circle(x + 238, y + 168, 11, RED, fill=False)
    cv.circle(x + 138, y + 118, 6, (255, 200, 60), fill=True)
    cv.circle(x + 138, y + 118, 10, (255, 200, 60), fill=False)
    draw_text(cv, "TINYB", x + 252, y + 160, "KYIV", WHITE)
    draw_text(cv, "TINYB", x + 92, y + 78, "POLAND", (255, 200, 60))
    draw_text(cv, "TINYB", x + 218, y + 214, "UKRAINE", WHITE)
    draw_text(cv, "TINY", x + 14, y + h - 44,
              "400+ drones and 110 missiles fired overnight,", (200, 214, 228))
    draw_text(cv, "TINY", x + 14, y + h - 28,
              "bridges and rail stations hit in Kyiv.", (200, 214, 228))


def draw_lead(cv):
    y = 126
    draw_text(cv, "SMB", 28, y, "WAR IN EUROPE", RED)
    draw_text(cv, "TINYB", 640 - text_width("TINYB", "LIVE · 21 NOV"),
              y, "LIVE · 21 NOV", RED)
    y += 26
    draw_text(cv, "HEAD", 28, y, "MISSILES FALL", INK)
    y += 46
    draw_text(cv, "HEAD", 28, y, "ON POLAND", INK)
    y += 52
    draw_text(cv, "SUB", 28, y,
              "Russia's biggest strikes of the year hit", INK)
    y += 32
    draw_text(cv, "SUB", 28, y, "Ukraine — and cross a NATO border.", INK)
    y += 44
    y = draw_block(
        cv, "BODY", 28, y,
        "Russia fired more than 400 drones and 110 missiles at Ukraine "
        "overnight, killing at least eight in Kyiv. Two Russian missiles "
        "and a suspected drone came down in Poland. PM Donald Tusk "
        "called it a deliberate provocation; NATO called it a grave "
        "violation and scrambled jets.",
        612, INK)
    y += 8
    draw_text(cv, "TINY", 28, y,
              "Sources: BBC · France 24 · CBS News · El Pais", GREY)
    draw_lead_map(cv, 664, 126, 332, 300)


def draw_markets(cv):
    y = 484
    rule(cv, 28, y - 12, W - 56, INK, 2)
    draw_text(cv, "SMB", 28, y, "MARKETS IN FREEFALL", RED)
    draw_text(cv, "TINY", W - 28 - text_width(
        "TINY", "FRIDAY CLOSE · 21 NOV 2026"), y + 2,
        "FRIDAY CLOSE · 21 NOV 2026", GREY)
    # Falling chart, left half.
    cx, cy, cw, ch = 28, y + 30, 520, 88
    cv.fill_rect(cx, cy, cw, ch, CREAM)
    cv.rect(cx, cy, cw, ch, LGREY, 1)
    pts = [(cx + 8, cy + 26), (cx + 110, cy + 38), (cx + 210, cy + 36),
           (cx + 310, cy + 56), (cx + 410, cy + 68), (cx + 512, cy + 82)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED)
        cv.line(pts[i][0], pts[i][1] + 1, pts[i + 1][0], pts[i + 1][1] + 1, RED)
    for (px, py) in pts:
        cv.circle(px, py, 3, DARKRED, fill=True)
    draw_text(cv, "TINYB", cx + 10, cy + 4, "NASDAQ · THE WEEK'S ROUT", INK)
    draw_text(cv, "TINY", cx + 10, cy + ch - 18,
              "AI doubts wipe about $4 trillion in a week", GREY)
    # Index table, right half.
    rows = [("NASDAQ", "-5.28%", "erases all 2026 gains"),
            ("S&P 500", "-3.70%", "into correction"),
            ("NIKKEI", "-5.06%", "worst week since Covid"),
            ("FTSE 100", "-1.02%", "  "),
            ("GOLD", "-4.62%", "  ")]
    tx = 576
    ty = y + 30
    for name, chg, note in rows:
        draw_text(cv, "SMB", tx, ty, name, INK)
        draw_text(cv, "SMB", tx + 150, ty, chg, RED)
        if note.strip():
            draw_text(cv, "TINY", tx + 240, ty + 2, note, GREY)
        ty += 20
    draw_text(cv, "TINY", 28, y + 126,
              "Nvidia faces an SEC accounting probe, Reuters reports; "
              "Anthropic slides again on day two of trading.", GREY)


def draw_uk_eu(cv, x, y, w):
    # Union Jack (simplified) + EU ring of stars.
    fx, fy = x, y
    cv.fill_rect(fx, fy, 92, 52, (0, 36, 125))
    cv.fill_rect(fx, fy + 21, 92, 10, WHITE)
    cv.fill_rect(fx + 41, fy, 10, 52, WHITE)
    cv.fill_rect(fx, fy + 23, 92, 6, RED)
    cv.fill_rect(fx + 43, fy, 6, 52, RED)
    cv.line(fx, fy, fx + 92, fy + 52, WHITE)
    cv.line(fx + 92, fy, fx, fy + 52, WHITE)
    ex = x + 108
    cv.fill_rect(ex, fy, 92, 52, (0, 51, 153))
    import math
    for k in range(12):
        a = 2 * math.pi * k / 12 - math.pi / 2
        sx = ex + 46 + int(17 * math.cos(a))
        sy = fy + 26 + int(17 * math.sin(a))
        cv.circle(sx, sy, 2, (255, 204, 0), fill=True)
    draw_text(cv, "SMB", x, y + 62, "BRITAIN AND EU SEAL", INK)
    draw_text(cv, "SMB", x, y + 82, "BIGGEST POST-BREXIT DEAL", INK)
    draw_block(
        cv, "SMALL", x, y + 106,
        "Three deals in Brussels: food trade, carbon markets, youth "
        "mobility — 100,000 visas each way, food checks scrapped, "
        "Britain back in Erasmus+.",
        w, INK)


def draw_cop31(cv, x, y, w):
    # Sun over a clock: talks running past deadline.
    cx, cy = x + 46, y + 26
    cv.circle(cx, cy, 24, (255, 176, 32), fill=True)
    for k in range(8):
        import math
        a = 2 * math.pi * k / 8
        cv.line(cx + int(28 * math.cos(a)), cy + int(28 * math.sin(a)),
                cx + int(36 * math.cos(a)), cy + int(36 * math.sin(a)),
                (255, 176, 32))
    cv.circle(x + 150, y + 26, 24, PAPER, fill=True)
    cv.circle(x + 150, y + 26, 24, INK, fill=False)
    cv.line(x + 150, y + 26, x + 150, y + 8, INK)
    cv.line(x + 150, y + 26, x + 164, y + 32, INK)
    draw_text(cv, "SMB", x, y + 62, "CLIMATE TALKS RUN", INK)
    draw_text(cv, "SMB", x, y + 82, "INTO OVERTIME", INK)
    draw_block(
        cv, "SMALL", x, y + 106,
        "COP31 in Antalya passes its deadline with nearly 200 nations "
        "deadlocked over fossil fuels; a draft drops the phase-out "
        "language.",
        w, INK)


def draw_cancer(cv, x, y, w):
    # Capsule + big response figure.
    cv.circle(x + 26, y + 26, 24, (30, 84, 145), fill=True)
    cv.fill_rect(x + 26, y + 2, 60, 48, (30, 84, 145))
    cv.circle(x + 86, y + 26, 24, (240, 90, 60), fill=True)
    cv.fill_rect(x + 26, y + 2, 60, 48, (30, 84, 145))
    cv.circle(x + 26, y + 26, 24, (30, 84, 145), fill=True)
    cv.fill_rect(x + 50, y + 2, 36, 48, (240, 90, 60))
    cv.circle(x + 86, y + 26, 24, (240, 90, 60), fill=True)
    draw_text(cv, "HEAD", x + 128, y + 4, "60.7%", RED)
    draw_text(cv, "SMB", x, y + 62, "CANCER PILL SHRINKS", INK)
    draw_text(cv, "SMB", x, y + 82, "TUMOURS IN 6 IN 10", INK)
    draw_block(
        cv, "SMALL", x, y + 106,
        "Daraxonrasib plus chemotherapy shrank or erased tumours in "
        "60.7% of 61 patients; in 1 in 12 the cancer became "
        "undetectable.",
        w, INK)


def draw_peru(cv):
    y = 844
    rule(cv, 28, y - 12, W - 56, INK, 2)
    draw_text(cv, "HEAD", 28, y, "M6.8", RED)
    draw_text(cv, "SMB", 140, y + 12, "QUAKE SHAKES PERU'S ANDES", INK)
    draw_block(
        cv, "BODY", 28, y + 44,
        "A magnitude 6.8 earthquake struck Peru's Junin region, 129 km "
        "deep, sending Lima residents into the streets. No casualties "
        "or major damage reported.",
        780, INK)
    # Small South-America outline with epicentre dot.
    mx, my = 850, y - 6
    cv.poly([(mx + 10, my + 4), (mx + 46, my), (mx + 78, my + 12),
             (mx + 84, my + 40), (mx + 60, my + 78), (mx + 34, my + 84),
             (mx + 12, my + 52), (mx + 4, my + 22)], (58, 96, 140))
    cv.circle(mx + 34, my + 34, 5, RED, fill=True)
    cv.circle(mx + 34, my + 34, 9, RED, fill=False)
    draw_text(cv, "TINYB", mx + 48, my + 48, "JUNIN", INK)


def draw_footer(cv):
    y = 956
    rule(cv, 28, y - 12, W - 56, INK, 2)
    draw_text(cv, "SMB", 28, y, "ALSO TODAY", RED)
    src = "Sources: Reuters · BBC · AP · NBC News"
    draw_text(cv, "TINY", W - 28 - text_width("TINY", src), y + 2,
              src, GREY)
    draw_block(
        cv, "SMALL", 28, y + 22,
        "FBI probes a suspected hack of its national crime database · "
        "Bayer's $7.25bn Roundup deal approved · Houthi missiles at "
        "Riyadh intercepted · Basra plant fire kills four · Gen Z "
        "protests in 25 nations · Bitcoin nears $62,000.",
        W - 56, INK)


def build():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_lead(cv)
    draw_markets(cv)
    rule(cv, 28, 628, W - 56, INK, 2)
    draw_uk_eu(cv, 28, 640, 296)
    draw_cop31(cv, 364, 640, 296)
    draw_cancer(cv, 700, 640, 296)
    draw_peru(cv)
    draw_footer(cv)
    return cv


def main():
    cv = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    n = write_png(cv, OUT)
    print(f"wrote {OUT} {n} bytes {W}x{H}")


if __name__ == "__main__":
    main()
