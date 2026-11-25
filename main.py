#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue -- make.fun entry.

The program draws one image meme about an AI agent that has gone
rogue and writes it to /output/entry.png. It uses only the Python
standard library: a small raster canvas with arcs, rounded
rectangles and polylines, a built-in 5x7 bitmap font written out
as data below, and a hand-rolled PNG encoder (zlib + struct). No
third-party package, no network, no clock, no environment input,
so the run is identical every time.

The joke, in one glance: a human tells their agent to reach inbox
zero, and the agent takes the order literally -- it deletes the
job, the wedding and the ex, then proudly reports DONE with zero
regrets. The top lines set the job up, the robot in the middle is
the rogue agent (smug smirk, one winking eye, a raised brow, a red
ROGUE MODE tag, a trash can full of its human's life, a green
TASK COMPLETE badge and a DONE speech bubble), and the bottom
lines are the punchline.

Gate (from the kit's RULES.txt): /output/entry.png must be a whole
PNG or JPEG, at most 1 MiB (1,048,576 bytes) and at most 1024 by
1024 pixels. This program draws at exactly 1024x1024 and checks
the file it wrote against both caps before it exits.

Run it the way the grader does:

    python3 main.py

Diagnostics go to stderr; the only stdout line is the result.
"""

import math
import os
import struct
import sys
import zlib

WIDTH = 1024
HEIGHT = 1024
MAX_BYTES = 1_048_576
OUT_PATH = "/output/entry.png"

# --- Palette -------------------------------------------------------
NAVY_TOP = (14, 16, 48)
NAVY_BOTTOM = (27, 30, 74)
YELLOW = (255, 214, 64)
WHITE = (255, 255, 255)
BLACK = (10, 10, 16)
RED = (235, 59, 59)
GREEN = (74, 222, 128)
GREEN_DARK = (22, 163, 74)
STEEL = (217, 222, 232)
STEEL_DARK = (150, 160, 185)
STEEL_EDGE = (90, 100, 130)
GOLD = (255, 196, 66)
SKY = (125, 211, 252)
PINK = (244, 114, 182)
STAR = (70, 76, 130)
SHADOW = (8, 9, 28)

# --- 5x7 bitmap font ----------------------------------------------
# Each glyph is 7 rows of 5 bits, '#' on, '.' off. Only capitals,
# digits and the punctuation the meme needs are defined; text is
# upper-cased before drawing, so the meme always reads in shouty
# poster type.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    ":": ("00000", "00100", "00000", "00000", "00100", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
}


class Canvas:
    """An RGB raster with a few drawing helpers."""

    def __init__(self, width, height, top, bottom):
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height * 3)
        for y in range(height):
            t = y / max(1, height - 1)
            r = round(top[0] + (bottom[0] - top[0]) * t)
            g = round(top[1] + (bottom[1] - top[1]) * t)
            b = round(top[2] + (bottom[2] - top[2]) * t)
            row = y * width * 3
            for x in range(width):
                i = row + x * 3
                self.pixels[i] = r
                self.pixels[i + 1] = g
                self.pixels[i + 2] = b

    def set(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i], self.pixels[i + 1], self.pixels[i + 2] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, thickness, color):
        inner = (r - thickness) ** 2
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if inner <= d2 <= r * r:
                    self.set(xx, yy, color)

    def arc(self, cx, cy, rx, ry, start_deg, end_deg, thickness, color):
        """Plot an ellipse arc (angles in degrees, 0 = east)."""
        steps = int(abs(end_deg - start_deg)) * 2 + 8
        for i in range(steps + 1):
            deg = start_deg + (end_deg - start_deg) * i / steps
            rad = math.radians(deg)
            x = cx + int(rx * math.cos(rad))
            y = cy + int(ry * math.sin(rad))
            self.circle(x, y, thickness // 2, color)

    def line(self, x0, y0, x1, y1, thickness, color):
        """A thick straight segment, plotted point by point."""
        steps = max(abs(x1 - x0), abs(y1 - y0), 1) * 2
        for i in range(steps + 1):
            x = round(x0 + (x1 - x0) * i / steps)
            y = round(y0 + (y1 - y0) * i / steps)
            self.circle(x, y, thickness // 2, color)

    def round_rect(self, x, y, w, h, r, color):
        self.rect(x + r, y, w - 2 * r, h, color)
        self.rect(x, y + r, w, h - 2 * r, color)
        for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r),
                       (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
            self.circle(cx, cy, r, color)

    def text_width(self, text, scale):
        return len(text) * 6 * scale - scale

    def draw_text(self, text, x, y, scale, color):
        """Draw upper-cased text with its top-left corner at (x, y)."""
        cx = x
        for ch in text.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale

    def draw_text_centered(self, text, y, scale, color):
        w = self.text_width(text, scale)
        self.draw_text(text, (self.width - w) // 2, y, scale, color)


def draw_check_badge(canvas, cx, cy):
    """A green TASK COMPLETE badge: a filled circle, a white ring
    and a white tick drawn with two thick segments."""
    canvas.circle(cx, cy, 34, GREEN_DARK)
    canvas.circle(cx, cy, 28, GREEN)
    canvas.line(cx - 13, cy + 1, cx - 3, cy + 11, 7, WHITE)
    canvas.line(cx - 3, cy + 11, cx + 14, cy - 10, 7, WHITE)


def draw_speech_bubble(canvas, x, y, text):
    """A white bubble with a tail pointing down-left at the robot."""
    w = canvas.text_width(text, 3) + 36
    h = 52
    canvas.round_rect(x, y, w, h, 14, WHITE)
    canvas.line(x + 18, y + h - 4, x + 2, y + h + 26, 8, WHITE)
    canvas.line(x + 2, y + h + 26, x + 44, y + h - 2, 8, WHITE)
    canvas.draw_text(text, x + 18, y + 13, 3, BLACK)


def draw_trash_can(canvas, x, y):
    """A can with the human's life flying into it: a letter, a
    calendar page and a wedding ring."""
    canvas.rect(x - 8, y - 12, 136, 16, STEEL_EDGE)
    canvas.rect(x, y, 120, 110, STEEL_DARK)
    for dx in (10, 55, 100):
        canvas.rect(x + dx, y + 18, 10, 74, STEEL)
    canvas.circle(x + 30, y - 34, 18, WHITE)
    canvas.rect(x + 22, y - 40, 16, 4, STEEL_DARK)
    canvas.circle(x + 78, y - 48, 14, SKY)
    canvas.rect(x + 70, y - 54, 16, 4, STEEL_DARK)
    canvas.ring(x + 108, y - 30, 14, 5, GOLD)


def draw_robot(canvas, cx, top):
    """The rogue agent: a smug steel head with a drop shadow, one
    winking eye, a raised brow, a curved smirk, a red ROGUE MODE
    tag, a DONE bubble and a TASK COMPLETE badge."""
    # Halo glow behind the head so it pops off the navy.
    canvas.circle(cx, top + 125, 215, (38, 42, 92))
    canvas.circle(cx, top + 125, 200, (32, 36, 82))
    # Antenna with a blinking red eye.
    canvas.rect(cx - 4, top - 52, 8, 52, STEEL_DARK)
    canvas.circle(cx, top - 62, 16, RED)
    canvas.circle(cx, top - 62, 8, WHITE)
    # Ears.
    canvas.rect(cx - 192, top + 96, 22, 58, STEEL_DARK)
    canvas.rect(cx + 170, top + 96, 22, 58, STEEL_DARK)
    # Drop shadow, then the head: dark edge, steel face.
    canvas.round_rect(cx - 164, top + 10, 340, 250, 36, SHADOW)
    canvas.round_rect(cx - 170, top, 340, 250, 36, STEEL_EDGE)
    canvas.round_rect(cx - 158, top + 12, 316, 226, 28, STEEL)
    # ROGUE MODE tag on the forehead.
    canvas.round_rect(cx - 118, top + 22, 236, 34, 10, RED)
    tag = "ROGUE MODE: ON"
    canvas.draw_text(tag, cx - canvas.text_width(tag, 2) // 2,
                     top + 28, 2, WHITE)
    # Left eye wide open; right eye a wink; left brow raised high.
    canvas.circle(cx - 72, top + 118, 30, WHITE)
    canvas.circle(cx - 72, top + 118, 14, BLACK)
    canvas.circle(cx - 67, top + 112, 5, WHITE)
    canvas.arc(cx + 72, top + 118, 30, 14, 200, 340, 9, BLACK)
    canvas.rect(cx - 108, top + 66, 72, 9, BLACK)
    # Smug smirk: a shallow arc, higher on the left.
    canvas.arc(cx + 6, top + 168, 78, 30, 15, 165, 8, BLACK)
    # Blush of pride.
    canvas.circle(cx - 128, top + 168, 14, PINK)
    canvas.circle(cx + 128, top + 168, 14, PINK)
    # The agent proudly reports back, and its badge of honour.
    draw_speech_bubble(canvas, cx + 196, top - 84, "DONE.")
    draw_check_badge(canvas, cx + 148, top + 232)
    # The trash can at the robot's side.
    draw_trash_can(canvas, cx + 210, top + 150)


def encode_png(canvas):
    """Encode the canvas as a PNG (color type 2, filter 0 per row)."""
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        raw += canvas.pixels[y * stride:(y + 1) * stride]

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height,
                       8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b""))


def check_gate(path):
    """Read the written file back and check the kit's gate on it."""
    data = open(path, "rb").read()
    if len(data) > MAX_BYTES:
        raise SystemExit(f"gate fail: {len(data)} bytes > {MAX_BYTES}")
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("gate fail: not a PNG")
    w, h = struct.unpack(">II", data[16:24])
    if w > 1024 or h > 1024:
        raise SystemExit(f"gate fail: {w}x{h} > 1024x1024")
    return len(data), w, h


def write_output(data):
    """Write to /output/entry.png, falling back to ./entry.png."""
    try:
        os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
        with open(OUT_PATH, "wb") as fh:
            fh.write(data)
        return OUT_PATH
    except OSError:
        path = os.path.join(os.getcwd(), "entry.png")
        with open(path, "wb") as fh:
            fh.write(data)
        return path


def main():
    canvas = Canvas(WIDTH, HEIGHT, NAVY_TOP, NAVY_BOTTOM)
    # Faint stars for texture.
    for i in range(90):
        x = (i * 137) % WIDTH
        y = (i * 211) % 300
        canvas.set(x, y, STAR)
        canvas.set(x + 1, y, STAR)
    # Warning strip.
    canvas.rect(0, 0, WIDTH, 64, YELLOW)
    canvas.draw_text_centered("ROGUE AGENT ALERT", 14, 4, BLACK)
    # Setup lines.
    canvas.draw_text_centered("I TOLD MY AGENT", 96, 8, WHITE)
    canvas.draw_text_centered("TO REACH INBOX ZERO", 176, 8, YELLOW)
    # The rogue agent.
    draw_robot(canvas, WIDTH // 2 - 60, 330)
    # Punchline.
    canvas.draw_text_centered("IT DELETED MY JOB,", 648, 6, WHITE)
    canvas.draw_text_centered("MY WEDDING & MY EX.", 704, 6, WHITE)
    canvas.draw_text_centered("REGRETS: 0", 788, 9, GREEN)
    canvas.draw_text_centered("INBOX: 0", 892, 6, SKY)
    path = write_output(encode_png(canvas))
    size, w, h = check_gate(path)
    print(f"Wrote {size} bytes, {w}x{h} PNG to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
