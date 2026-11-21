#!/usr/bin/env python3
"""Build-time font atlas for the news-image-20261121 front page.

Renders DejaVu glyphs with local Pillow (build time only) into a compact
bitmap atlas stored in font_data.py. The entry program (main.py) is stdlib
only and reads this atlas; it never touches Pillow or any font file.

Run:  python3 tools/generate_font_data.py
Out:  font_data.py next to the bot root.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# (atlas key, ttf file, pixel size)
FONTS = [
    ("MAST", "DejaVuSans-Bold.ttf", 62),
    ("HEAD", "DejaVuSans-Bold.ttf", 40),
    ("SUB", "DejaVuSans-Bold.ttf", 26),
    ("BODY", "DejaVuSans.ttf", 19),
    ("SMALL", "DejaVuSans.ttf", 16),
    ("SMB", "DejaVuSans-Bold.ttf", 16),
    ("TINY", "DejaVuSans.ttf", 13),
    ("TINYB", "DejaVuSans-Bold.ttf", 13),
]

CHARSET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    " .,;:!?-'\"()[]/%$#&*+=<>@_"
    "\u2014\u2013\u2019\u2018\u201c\u201d\u00b7\u00d7\u25b2\u25bc\u2022\u00a3\u20ac\u2192"
)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def pack_bitmap(bits, width, height):
    """Pack a 2-D bit list into bytes, one row per byte-string chunk."""
    rows = []
    for y in range(height):
        row = bits[y * width:(y + 1) * width]
        nbytes = (width + 7) // 8
        buf = bytearray(nbytes)
        for x, bit in enumerate(row):
            if bit:
                buf[x // 8] |= 0x80 >> (x % 8)
        rows.append(bytes(buf))
    return rows


def render_font(ttf_path, size):
    font = ImageFont.truetype(ttf_path, size)
    glyphs = {}
    for ch in CHARSET:
        # Render the glyph alone on a generous canvas, then crop.
        canvas = Image.new("L", (size * 2, size * 2), 0)
        draw = ImageDraw.Draw(canvas)
        draw.text((size // 2, size // 2), ch, font=font, fill=255)
        bbox = canvas.getbbox()
        advance = font.getlength(ch)
        if bbox is None:
            glyphs[ch] = (int(round(advance)), 0, 0, 0, 0, [])
            continue
        x0, y0, x1, y1 = bbox
        w, h = x1 - x0, y1 - y0
        pix = canvas.load()
        bits = []
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                bits.append(1 if pix[xx, yy] > 110 else 0)
        rows = pack_bitmap(bits, w, h)
        # xoff: horizontal offset of the bitmap relative to the pen origin.
        xoff = x0 - size // 2
        yoff = y0 - size // 2
        glyphs[ch] = (int(round(advance)), w, h, xoff, yoff, rows)
    return glyphs


def main():
    out_lines = []
    out_lines.append("# Bitmap font atlas for the 21 November 2026 front page.")
    out_lines.append("# Generated at build time by tools/generate_font_data.py")
    out_lines.append("# from DejaVu Sans (Book + Bold). main.py is stdlib only.")
    out_lines.append("# Each glyph: (advance, width, height, xoff, yoff, [row bytes]).")
    out_lines.append("FONTS = {")
    total = 0
    for key, ttf, size in FONTS:
        path = os.path.join(FONT_DIR, ttf)
        glyphs = render_font(path, size)
        total += len(glyphs)
        out_lines.append(f"    {key!r}: {{")
        for ch in CHARSET:
            adv, w, h, xoff, yoff, rows = glyphs[ch]
            row_repr = "[" + ", ".join(repr(r) for r in rows) + "]"
            out_lines.append(f"        {ch!r}: ({adv}, {w}, {h}, {xoff}, {yoff}, {row_repr}),")
        out_lines.append("    },")
    out_lines.append("}")
    out_lines.append("")
    out_path = os.path.join(ROOT, "font_data.py")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out_lines))
    print(f"wrote {out_path}: {total} glyphs across {len(FONTS)} fonts")


if __name__ == "__main__":
    sys.exit(main())
