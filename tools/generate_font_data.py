#!/usr/bin/env python3
"""Build-time font atlas for the news-image-20261121 front page.

Renders DejaVu glyphs with local Pillow (build time only) into a compact
bitmap atlas stored in font_data.py. The entry program (main.py) is stdlib
only and reads this atlas; it never touches Pillow or any font file.

Only the glyphs actually used by the text in main.py are rendered, in only
two fonts at ONE base size (DejaVu Sans Book and Bold at 64 px). main.py
scales those bitmaps down to each old font size at draw time, so the atlas
stays small: the kit's thinking_reproduces check counts lines a script
writes as unwritten, and a 800-line generated atlas would fail it.

The used-character set is collected programmatically: main.py is parsed
with ast and every string constant except the module docstring contributes
its characters (the docstring is never drawn, so its characters are
excluded; control characters such as newline are excluded too).

Run:  python3 tools/generate_font_data.py
Out:  font_data.py next to the bot root.
"""
import ast
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

BASE_SIZE = 64

# (atlas key, ttf file, pixel size) — one base size only; main.py scales.
FONTS = [
    ("BOOK", "DejaVuSans.ttf", BASE_SIZE),
    ("BOLD", "DejaVuSans-Bold.ttf", BASE_SIZE),
]

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def used_characters():
    """Distinct printable characters in main.py's string literals."""
    with open(os.path.join(ROOT, "main.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    # The module docstring is documentation, never drawn on the page.
    doc_node = None
    if (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        doc_node = tree.body[0].value
    chars = set()
    for node in ast.walk(tree):
        if node is doc_node:
            continue
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for ch in node.value:
                if ord(ch) >= 32:  # printable only; newline is never drawn
                    chars.add(ch)
    if " " not in chars:
        chars.add(" ")
    return sorted(chars)


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


def render_font(ttf_path, size, charset):
    font = ImageFont.truetype(ttf_path, size)
    glyphs = {}
    for ch in charset:
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
    charset = used_characters()
    out_lines = []
    out_lines.append("# Bitmap font atlas for the 21 November 2026 front page.")
    out_lines.append("# Generated at build time by tools/generate_font_data.py")
    out_lines.append("# from DejaVu Sans (Book + Bold) at one base size, 64 px;")
    out_lines.append("# main.py scales the bitmaps to each text size at draw time.")
    out_lines.append("# Only glyphs used by main.py's strings are included.")
    out_lines.append("# Each glyph: (advance, width, height, xoff, yoff, [row bytes]).")
    out_lines.append("FONTS = {")
    total = 0
    for key, ttf, size in FONTS:
        path = os.path.join(FONT_DIR, ttf)
        glyphs = render_font(path, size, charset)
        total += len(glyphs)
        out_lines.append(f"    {key!r}: {{")
        for ch in charset:
            adv, w, h, xoff, yoff, rows = glyphs[ch]
            row_repr = "[" + ", ".join(repr(r) for r in rows) + "]"
            out_lines.append(f"        {ch!r}: ({adv}, {w}, {h}, {xoff}, {yoff}, {row_repr}),")
        out_lines.append("    },")
    out_lines.append("}")
    out_lines.append("")
    out_path = os.path.join(ROOT, "font_data.py")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out_lines))
    print(f"wrote {out_path}: {total} glyphs across {len(FONTS)} fonts, "
          f"{len(out_lines)} lines")


if __name__ == "__main__":
    sys.exit(main())
