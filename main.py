#!/usr/bin/env python3
"""The World in One Day -- 18 November 2026 (news-image-20261118, round 2).

Renders a 1024x1024 newspaper front page covering 50 verified stories from
Wednesday 18 November 2026 (UTC), plus a UTC timeline and a world-map strip.

Run:  python3 main.py
Output: entry.png next to this file, then copied to /output/entry.png.

Deterministic: same inputs always produce byte-identical output.
No network. Python 3.13 stdlib + Pillow only.
"""

import hashlib
import os
import shutil
import struct
import sys
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
OUT_LOCAL = HERE / "entry.png"
OUT_FINAL = Path("/output/entry.png")

W, H = 1024, 1024
MARGIN = 14
CW = W - 2 * MARGIN  # 996 content width

PAPER = (247, 243, 232)
INK = (20, 24, 31)
MUTED = (90, 95, 106)
RED = (179, 39, 30)
NAVY = (27, 42, 74)
TEAL = (15, 107, 107)
GOLD = (176, 128, 38)
RULE = (20, 24, 31)
PANEL = (255, 255, 255)
PANEL_LINE = (180, 180, 172)
MAP_LAND = (201, 209, 219)
MAP_SEA = (233, 238, 242)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def font(name, size):
    """Load a DejaVu font; fall back to Pillow's default bitmap font."""
    path = FONT_DIR / name
    try:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    except Exception:
        pass
    return ImageFont.load_default()


SERIF_B = lambda s: font("DejaVuSerif-Bold.ttf", s)  # noqa: E731
SANS = lambda s: font("DejaVuSans.ttf", s)  # noqa: E731
SANS_B = lambda s: font("DejaVuSans-Bold.ttf", s)  # noqa: E731


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap. Returns a list of lines that fit max_w."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, fill, max_w, lh):
    """Draw wrapped text; returns the y just below the last line."""
    for line in wrap(draw, text, fnt, max_w):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += lh
    return y


def center(draw, y, text, fnt, fill, x0=MARGIN, x1=W - MARGIN):
    """Draw one centred line; returns its pixel width."""
    w = draw.textlength(text, font=fnt)
    draw.text(((x0 + x1 - w) / 2, y), text, font=fnt, fill=fill)
    return w


def fit_image(name, w, h, centering=(0.5, 0.42)):
    """Centre-crop a generated illustration to exactly w x h."""
    im = Image.open(ASSETS / name).convert("RGB")
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=centering)


# ---------------------------------------------------------------- data
# Featured panels: 8 panels covering 10 numbered stories.
# F1=29, F2=30+31, F3=4+5, F4=11, F5=9, F6=47, F7=42, F8=41.
FEATURED_ROW1 = [
    {
        "tag": "F1 · SHENZHEN",
        "art": "f1.png",
        "head": "APEC OPENS IN SHENZHEN",
        "body": "Xi and Putin met ahead of a Trump–Xi–Putin summit "
                "scheduled for 19 Nov. Reported agenda: nuclear arms, "
                "Ukraine, Iran, trade and AI.",
    },
    {
        "tag": "F2 · MANILA · QUAD JOINT STATEMENT",
        "art": "f2.png",
        "head": "QUAD MEETS IN MANILA",
        "body": "First Quad leaders' meeting in over two years. Announced: "
                "maritime surveillance, an AI accelerator of over $85M, "
                "cable links, and a joint P-8/P-3C exercise planned "
                "for 2027.",
    },
    {
        "tag": "F3 · THE GULF",
        "art": "f3.png",
        "head": "GULF: STRIKES AND DRONES",
        "body": "US hits a Qeshm Island missile site; Iran drones hit US "
                "bases in Bahrain and Kuwait.",
    },
]

FEATURED_ROW2 = [
    {
        "tag": "F4 · UKRAINE",
        "art": "f4.png",
        "head": "CRIMEAN BRIDGE SPAN DESTROYED",
        "body": "Ukraine said it destroyed a road span for a 2nd day; the "
                "span collapsed. Officials separately reported Russian "
                "strikes on two Kyiv bridges.",
    },
    {
        "tag": "F5 · ALASKA",
        "art": "f5.png",
        "art_xy": (0.55, 0.62),
        "head": "PELTOLA WINS ALASKA U.S. SENATE RACE",
        "body": "Democrats take a 56–44 majority in the incoming Senate "
                "— their ninth midterm flip.",
    },
    {
        "tag": "F6 · MARKETS",
        "art": "f6.png",
        "head": "NVIDIA REVENUE DOUBLES",
        "body": "Revenue $115.8B in the quarter ended 25 Oct 2026, up 103% "
                "year on year. The board rules out Huang's return as CEO.",
    },
]

FEATURED_ROW3 = [
    {
        "tag": "F7 · ANDHRA PRADESH · IMD",
        "art": "f7.png",
        "head": "CYCLONE AKVAN NEARS ANDHRA",
        "body": "Forecasts on 18 Nov: landfall near 20 Nov, winds "
                "120–130 km/h, gusts 145 km/h.",
    },
    {
        "tag": "F8 · CRICKET",
        "art": "f8.png",
        "head": "DHONI RETIRES FROM THE IPL",
        "body": "272 games, 5 titles. The CSK great becomes team mentor "
                "for 2027.",
    },
]

TIMELINE = [
    ("10:16 UTC", "Voyager 1 reaches one light-day from Earth (NASA JPL)."),
    ("AFRICA", "South Africa: 17 killed in two shootings."),
    ("SHENZHEN", "Xi & Putin meet; trilateral set for 19 Nov."),
    ("THE GULF", "US strike on Qeshm; Iran drones hit Bahrain, Kuwait."),
    ("UKRAINE & ALASKA", "Ukraine hits Crimean Bridge; Peltola win confirmed."),
    ("BUSINESS & WEATHER", "Nvidia earnings; Cyclone Akvan nears Andhra."),
]

# World briefs: the other 40 stories, grouped by region.
BRIEFS = [
    ("NORTH AMERICA — 7 MORE", [
        "Trump arrives in Manila for the Quad, then Shenzhen.",
        "Trump–Xi–Putin trilateral set for 19 Nov.",
        "Putin arrives in Shenzhen a day early.",
        "US presses UN over Taiwan flight limits; Taiwan seeks $14B arms.",
        "Trump backs Jensen Huang for Nvidia CEO.",
        "Apple, Zoom, BBC, IKEA hit in cyberattack on 200 sites.",
        "ULA Vulcan rocket fails — 40 Amazon Leo satellites lost.",
    ]),
    ("EUROPE — 9 MORE", [
        "Russia pounds Kyiv bridges; water & power outages.",
        "Ukraine peace talks with US & Europe; Zelensky: “not easy”.",
        "EU–Rwanda return-hub talks in Vienna.",
        "Britain sanctions Israeli settlement firms.",
        "UK unemployment reported at 4.7%.",
        "France denies troops in Ukraine, rejecting Russian claim.",
        "Serbia MiG-29 crash — pilot killed.",
        "Russian An-12 crash in Siberia — 13 killed.",
        "Spain: minimum wage +5.3% to €1,286/month; election set for 29 Nov.",
    ]),
    ("AFRICA — 8", [
        "Nigeria: US intelligence helps target militants.",
        "Nigeria: Zamfara police free 20 abducted women, children.",
        "South Africa: 17 dead in two shootings; probe continues.",
        "Egypt–India trade cooperation: pharmaceuticals, agriculture "
        "and technology.",
        "African Union presses for peace in Sudan and Congo.",
        "China buys West African crude amid Gulf tensions.",
        "Rwanda delegation in Vienna for EU return hub talks.",
        "South Sudan election uncertainty continues.",
    ]),
    ("ASIA — 9 MORE", [
        "Modi at East Asia Summit — free e-visas for ASEAN tourists.",
        "Modi lays foundation for Gurudwara redevelopment in Manila.",
        "ASEAN chair to Singapore; Digital Economy Framework Agreement "
        "completed.",
        "China & SE Asia: South China Sea code 85–90% agreed.",
        "Canada & China extend trade deals; Carney meets Xi.",
        "Japan protests Russian airspace violation.",
        "Thailand fire — 11 dead in Phuket.",
        "Iran refuses UN nuclear inspection until war ends.",
        "Houthis advance at Khor Omairh, 100 km west of Aden.",
    ]),
    ("INDIA — 4 MORE", [
        "India re-elected to ITU Council 2027–2030.",
        "Amazon to invest $7B in India renewables by 2030.",
        "India wholesale inflation reported at 12.29%, a four-year high.",
        "India–Japan 2+2 dialogue in Tokyo (18–19 Nov).",
    ]),
    ("GLOBAL & SCIENCE — 3 MORE", [
        "Voyager 1 reaches one light-day from Earth (NASA JPL).",
        "US loses measles elimination status; 5,412 cases reported.",
        "Ebola in DR Congo tops 11,000 cases (2nd-largest on record).",
    ]),
]

DATE_CHECK = ("Compiled from wire reports filed Wednesday 18 November 2026 "
              "(UTC). 50 stories. No event dated after 18 Nov 2026 UTC is "
              "shown as having happened that day.")

# ------------------------------------------------------------- panels
def draw_featured(d, img, box, item, art_h, head_size=13, body_size=10):
    """One featured panel: art on top, kicker, headline, body."""
    x, y, w, h = box
    d.rectangle([x, y, x + w, y + h], fill=PANEL, outline=PANEL_LINE, width=1)
    ax, ay, aw, ah = x + 1, y + 1, w - 2, art_h
    img.paste(fit_image(item["art"], aw, ah,
                        item.get("art_xy", (0.5, 0.42))), (ax, ay))
    ty = ay + ah + 5
    d.text((x + 8, ty), item["tag"], font=SANS_B(9), fill=RED)
    ty += 13
    ty = draw_wrapped(d, x + 8, ty, item["head"], SANS_B(head_size), INK,
                      w - 16, head_size + 3)
    end = draw_wrapped(d, x + 8, ty + 2, item["body"], SANS(body_size),
                       (40, 44, 54), w - 16, body_size + 3)
    if end > y + h - 2:
        print(f"WARNING: panel {item['tag']} overflows by "
              f"{end - (y + h - 2)}px", file=sys.stderr)


def draw_timeline(d, y0):
    d.text((MARGIN, y0), "REPORTS FOR 18 NOVEMBER", font=SANS_B(11), fill=INK)
    right = "TIMING SHOWN ONLY WHERE SOURCED"
    rw = d.textlength(right, font=SANS_B(9))
    d.text((W - MARGIN - rw, y0 + 1), right, font=SANS_B(9), fill=MUTED)
    d.line([(MARGIN, y0 + 16), (W - MARGIN, y0 + 16)], fill=RULE, width=1)
    col_w = CW // 3
    for i, (label, text) in enumerate(TIMELINE):
        cx = MARGIN + (i % 3) * col_w
        cy = y0 + 22 + (i // 3) * 30
        d.rectangle([cx, cy, cx + col_w - 8, cy + 26], fill=(255, 255, 255),
                    outline=PANEL_LINE, width=1)
        d.text((cx + 6, cy + 2), label, font=SANS_B(9), fill=RED)
        tw = d.textlength(text, font=SANS(9))
        d.text((cx + 6, cy + 14), text, font=SANS(9), fill=INK)
        if tw > col_w - 14:  # safety: shrink only if a string ever overflows
            d.rectangle([cx, cy, cx + col_w - 8, cy + 26], outline=RED, width=1)


# Map: rough equirectangular continents + 8 numbered dots.
def _mx(lon):
    return MARGIN + (lon + 170) / 360.0 * CW


def _my(lat, y0, y1):
    return y1 - (lat + 55) / 130.0 * (y1 - y0)


def draw_map(d, y0, y1):
    d.text((MARGIN, y0), "PLACES CONNECTED TO THE FEATURED REPORTS",
           font=SANS_B(10), fill=INK)
    d.line([(MARGIN, y0 + 15), (W - MARGIN, y0 + 15)], fill=RULE, width=1)
    my0, my1 = y0 + 18, y1 - 2
    d.rectangle([MARGIN, my0, W - MARGIN, my1], fill=MAP_SEA)
    polys = [
        [(20, 576), (90, 570), (180, 572), (260, 576), (330, 584), (300, 592),
         (240, 596), (200, 606), (150, 604), (90, 600), (40, 592)],
        [(280, 600), (330, 598), (370, 604), (390, 612), (360, 622),
         (320, 622), (290, 612)],
        [(455, 578), (500, 572), (560, 574), (595, 580), (580, 590),
         (520, 592), (470, 588)],
        [(450, 594), (500, 592), (560, 592), (610, 598), (620, 610),
         (590, 620), (520, 620), (470, 612), (440, 602)],
        [(600, 576), (700, 570), (850, 572), (960, 578), (980, 590),
         (940, 600), (860, 606), (780, 606), (700, 600), (620, 594)],
        [(800, 610), (860, 608), (905, 612), (900, 620), (830, 622),
         (795, 616)],
    ]
    sy = (my1 - my0) / 52.0
    sx = CW / 996.0
    for poly in polys:
        scaled = [(MARGIN + (px - 14) * sx, my0 + (py - 570) * sy)
                  for px, py in poly]
        d.polygon(scaled, fill=MAP_LAND)
    spots = [  # (lon, lat, label, dx, dy)
        (-150, 64, "ALASKA", 6, -4),
        (-122, 37, "CALIFORNIA", 6, 3),
        (34, 45, "CRIMEA", 4, -9),
        (56, 26, "QESHM", 5, 4),
        (80, 16, "ANDHRA", -48, -10),
        (84, 11, "CHENNAI", 6, 4),
        (114, 22, "SHENZHEN", -60, -10),
        (121, 15, "MANILA", 6, 4),
    ]
    for lon, lat, label, dx, dy in spots:
        px, py = _mx(lon), _my(lat, my0, my1)
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=RED,
                  outline=(255, 255, 255), width=1)
        d.text((px + dx, py + dy), label, font=SANS_B(8), fill=INK)


def draw_briefs(d, y0, y1):
    d.text((MARGIN, y0), "WORLD BRIEFS — 40 MORE VERIFIED STORIES",
           font=SANS_B(12), fill=INK)
    d.line([(MARGIN, y0 + 17), (W - MARGIN, y0 + 17)], fill=RULE, width=2)
    col_w = (CW - 18) // 3
    cols = [
        [BRIEFS[0], BRIEFS[1]],
        [BRIEFS[2], BRIEFS[3]],
        [BRIEFS[4], BRIEFS[5]],
    ]
    top = y0 + 24
    for ci, groups in enumerate(cols):
        cx = MARGIN + ci * (col_w + 9)
        cy = top
        for title, items in groups:
            d.text((cx, cy), title, font=SANS_B(10), fill=NAVY)
            cy += 14
            d.line([(cx, cy), (cx + col_w, cy)], fill=(200, 200, 192), width=1)
            cy += 4
            for item in items:
                lines = wrap(d, "•  " + item, SANS(9.5), col_w)
                for line in lines:
                    d.text((cx, cy), line, font=SANS(9.5), fill=INK)
                    cy += 12
                cy += 1
            cy += 5
        if ci == 2:
            # Reading note fills the short third column honestly.
            note_y = cy + 2
            d.rectangle([cx, note_y, cx + col_w, y1 - 2], fill=(255, 255, 255),
                        outline=PANEL_LINE, width=1)
            ny = draw_wrapped(d, cx + 8, note_y + 6, "HOW TO READ THIS PAGE",
                              SANS_B(10), INK, col_w - 16, 13)
            ny = draw_wrapped(
                d, cx + 8, ny + 3,
                "Eight panels summarize 10 lead items: APEC's opening and "
                "Xi–Putin talks; the Quad meeting; the US strike and "
                "Iranian drone attacks; the Crimean Bridge collapse; "
                "Alaska's Senate result; Nvidia's earnings; the cyclone "
                "forecast; and Dhoni's retirement. Forty briefs complete "
                "the 50-item digest; some items overlap. The strip recaps "
                "selected reports. “Set for” means scheduled.",
                SANS(9), (40, 44, 54), col_w - 16, 12)
            draw_wrapped(
                d, cx + 8, ny + 4,
                "Only 10:16 UTC is a precise sourced time.",
                SANS(9), (40, 44, 54), col_w - 16, 12)
    return y1


# ------------------------------------------------------------- render
def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # Masthead
    center(d, 8, "THE WORLD IN ONE DAY", SERIF_B(44), INK)
    center(d, 60, "WEDNESDAY, 18 NOVEMBER 2026  ·  50 VERIFIED STORIES",
           SANS_B(16), RED)
    y = 84
    y = draw_wrapped(d, MARGIN, y, DATE_CHECK, SANS(10), MUTED, CW, 13)
    d.line([(MARGIN, 108), (W - MARGIN, 108)], fill=RULE, width=3)
    d.line([(MARGIN, 112), (W - MARGIN, 112)], fill=RULE, width=1)

    # UTC timeline strip
    draw_timeline(d, 118)

    # Featured row 1: F1, F2, F3
    y1 = 202
    widths = [368, 368, 240]
    x = MARGIN
    for item, w in zip(FEATURED_ROW1, widths):
        draw_featured(d, img, (x, y1, w, 140), item, 52)
        x += w + 8

    # Featured row 2: F4, F5, F6
    y2 = 348
    for i, item in enumerate(FEATURED_ROW2):
        x = MARGIN + i * (326 + 9)
        draw_featured(d, img, (x, y2, 326, 122), item, 44,
                      head_size=13, body_size=10)

    # Featured row 3: F7, F8
    y3 = 476
    for i, item in enumerate(FEATURED_ROW3):
        x = MARGIN + i * (492 + 12)
        draw_featured(d, img, (x, y3, 492, 92), item, 40,
                      head_size=13, body_size=10)

    # World map strip
    draw_map(d, 576, 644)

    # World briefs
    draw_briefs(d, 650, 994)

    # Footer
    d.line([(MARGIN, 1000), (W - MARGIN, 1000)], fill=RULE, width=1)
    center(d, 1006,
           "Editorial illustrations, not photographs · Sources: Reuters, AP, "
           "AFP, BBC, Al Jazeera, Xinhua, PIB/MEA India, Quad Joint "
           "Statement, IMD, NASA JPL — reports filed 18 Nov 2026 (UTC)",
           SANS(9), MUTED)
    return img


# --------------------------------------------------------- PNG checks
def verify_png(path):
    """Signature, per-chunk CRC, IHDR size, IEND present, no trailing bytes."""
    data = path.read_bytes()
    problems = []
    if len(data) > 1024 * 1024:
        problems.append(f"size {len(data)} bytes exceeds 1 MiB")
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        problems.append("bad PNG signature")
        return problems
    pos, seen_iend, width, height = 8, False, None, None
    while pos < len(data):
        if pos + 8 > len(data):
            problems.append("truncated chunk header")
            break
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        end = pos + 12 + length
        if end > len(data):
            problems.append(f"truncated chunk {ctype!r}")
            break
        chunk = data[pos + 4:end - 4]
        crc_stored = struct.unpack(">I", data[end - 4:end])[0]
        if zlib.crc32(chunk) & 0xFFFFFFFF != crc_stored:
            problems.append(f"CRC mismatch in {ctype!r}")
        if ctype == b"IHDR":
            width, height = struct.unpack(">II", chunk[4:12])
            if width > 1024 or height > 1024:
                problems.append(f"IHDR {width}x{height} exceeds 1024")
        if ctype == b"IEND":
            seen_iend = True
            pos = end
            break
        pos = end
    if not seen_iend:
        problems.append("missing IEND chunk")
    elif pos != len(data):
        problems.append(f"{len(data) - pos} trailing bytes after IEND")
    if width is None:
        problems.append("missing IHDR chunk")
    return problems


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    img = render()
    img.save(OUT_LOCAL, "PNG", compress_level=9, optimize=True)
    problems = verify_png(OUT_LOCAL)
    size = OUT_LOCAL.stat().st_size
    digest = sha256(OUT_LOCAL)
    print(f"entry.png: {img.size[0]}x{img.size[1]}, {size} bytes, "
          f"sha256 {digest}")
    if problems:
        print("PNG VERIFICATION FAILED:")
        for p in problems:
            print("  - " + p)
        return 1
    print("PNG verification: OK (signature, CRCs, IHDR, IEND, size)")
    try:
        OUT_FINAL.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(OUT_LOCAL, OUT_FINAL)
        print(f"copied to {OUT_FINAL}")
    except OSError as exc:
        print(f"WARNING: could not copy to /output: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
