#!/usr/bin/env python3
"""The Globe Courier — a one-page broadsheet front page for 23 November 2026.

Renders the make.fun news-image-20261123 entry: a 1024x1024 PNG broadsheet
with a centred masthead, three photo stories across the top row (the lead
story in the centre column), three text stories below, an IN BRIEF band and
a sources footer.

Inputs: the three photo panels in assets/ (WebP) and the story copy in this
file (researched from the morning wires of 23 November 2026; see BUILD.md).

The output is deterministic: fixed fonts, fixed geometry, no timestamps,
no randomness — running the script twice yields byte-identical PNGs.

Usage: python3 build_courier.py [output.png]   (default: entry.png)
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"

PAGE_W, PAGE_H = 1024, 1024
MARGIN = 28
COL_W = 306
GUTTER = 25
CONTENT_W = PAGE_W - 2 * MARGIN  # 968
PHOTO_H = 180

# Palette — warm newsprint paper, charcoal ink, amber accent.
PAPER = (247, 243, 234)
INK = (26, 24, 20)
CHARCOAL = (35, 32, 28)
AMBER = (139, 92, 5)
AMBER_RULE = (160, 110, 10)
BODY_INK = (41, 38, 33)
GREY = (110, 104, 92)
HAIRLINE = (198, 191, 176)

MASTHEAD = "THE GLOBE COURIER"
DATE_LINE = "MONDAY, 23 NOVEMBER 2026"
DATE_TAIL = "  •  WORLD NEWS IN ONE PAGE"

# ---------------------------------------------------------------- stories

TOP_STORIES = [
    {
        "kicker": "STRAIT OF HORMUZ",
        "photo": "media-generation-panel-hormuz-0-7f93a5ea-b615-43e0-a324-34b8ca01c55c.webp",
        "caption": "A tanker in the Strait of Hormuz at dawn.",
        "headline": "Two more tankers hit mines as the strait burns",
        "body": (
            "Two supertankers catch fire after striking naval mines east of "
            "Hormuz on Sunday, and UK maritime authorities report projectile "
            "strikes near Khasab. Attacks on shipping are at their highest "
            "level since the war began."
        ),
    },
    {
        "kicker": "ANTALYA — LEAD STORY",
        "photo": "media-generation-panel-antalya-0-99704f85-53f1-4232-8983-529e92c3f1d0.webp",
        "caption": "The COP31 plenary hall in Antalya, emptying.",
        "headline": "COP31 collapses: no deal on fossil fuels",
        "body": (
            "After two weeks and record overtime, the climate summit ends "
            "without an overarching pact — the first such failure since "
            "Copenhagen in 2009. The EU, the UK and island states reject a "
            "text that never mentions fossil fuels."
        ),
    },
    {
        "kicker": "BENGHAZI",
        "photo": "media-generation-panel-benghazi-0-3e4ad8ef-b714-417f-b2e8-f3f865e50440.webp",
        "caption": "A warship listing in Benghazi harbour at dawn.",
        "headline": "Russian warship sunk by sea drones off Libya",
        "body": (
            "The corvette Merkury capsizes and sinks after suspected "
            "Ukrainian sea drones strike it in port; a second vessel is hit "
            "hours later. Libya asks the UN to investigate."
        ),
    },
]

LOWER_STORIES = [
    {
        "kicker": "BRUSSELS",
        "headline": "NATO meets today after Russian missiles land in Poland",
        "body": (
            "Prosecutors confirm all three objects that fell on Friday were "
            "Russian Kh-101 cruise missiles. The North Atlantic Council holds "
            "an emergency session in Brussels."
        ),
    },
    {
        "kicker": "SINALOA",
        "headline": "Mexico captures ‘El Chapo Isidro’ in deadly raid",
        "body": (
            "FBI most-wanted fugitive Fausto Isidro Meza Flores is seized in "
            "Guasave; 11 people are killed, four of them soldiers. US "
            "intelligence helped plan the raid."
        ),
    },
    {
        "kicker": "KYIV REGION",
        "headline": "Drone hits an apartment block; 11 missing in the rubble",
        "body": (
            "A Russian drone strikes a five-storey block in Dymer, north of "
            "Kyiv, early on Sunday, killing two. Rescuers search for "
            "survivors, including two children."
        ),
    },
]

BRIEF_ITEMS = [
    ("GENEVA", "128 states agree to pursue rules on killer robots by 2028."),
    ("JUBA", "24 civilians killed in fresh violence in South Sudan."),
    ("CIKANDE", "Seven bodies recovered, dozens missing after a factory fire in Indonesia."),
    ("OKINAWA", "Shuri Castle’s restored main hall opens, seven years after fire."),
]

SOURCES = "Sources: CNN • Reuters • Le Monde • AP • AFP • UKMTO • The Times"
TAGLINE = "THE GLOBE COURIER — ONE DAY. ONE PAGE."


# ---------------------------------------------------------------- fonts

def _find_font_file(stem: str) -> Path | None:
    """Locate a DejaVu font file by stem, searching the usual font dirs."""
    for base in ("/usr/share/fonts", "/usr/local/share/fonts"):
        for hit in Path(base).rglob(f"{stem}.ttf"):
            return hit
    return None


def load_font(stem: str, size: int) -> ImageFont.FreeTypeFont:
    path = _find_font_file(stem)
    if path is None:
        return ImageFont.load_default()
    return ImageFont.truetype(str(path), size)


# ---------------------------------------------------------------- text helpers

def wrap_text(draw: ImageDraw.ImageDraw, text: str,
              font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    """Greedy word wrap: pack as many whole words per line as fit."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if not current or draw.textlength(trial, font=font) <= width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_tracked(draw: ImageDraw.ImageDraw, x: float, y: float, text: str,
                 font: ImageFont.FreeTypeFont, fill: tuple, tracking: int = 2) -> None:
    """Draw text with extra space between letters (kicker style)."""
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += draw.textlength(char, font=font) + tracking


def tracked_width(draw: ImageDraw.ImageDraw, text: str,
                  font: ImageFont.FreeTypeFont, tracking: int = 2) -> float:
    total = sum(draw.textlength(ch, font=font) for ch in text)
    return total + tracking * max(len(text) - 1, 0)


def centre_x(draw: ImageDraw.ImageDraw, text: str,
             font: ImageFont.FreeTypeFont, tracking: int = 0) -> float:
    if tracking:
        width = tracked_width(draw, text, font, tracking)
    else:
        width = draw.textlength(text, font=font)
    return (PAGE_W - width) / 2


# ---------------------------------------------------------------- photos

def photo_panel(path: Path, width: int, height: int) -> Image.Image:
    """Centre-crop a photo to the target aspect, then scale it down."""
    img = Image.open(path).convert("RGB")
    want = width / height
    w, h = img.size
    if w / h > want:  # too wide: trim the sides
        new_w = int(h * want)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:  # too tall: trim top and bottom
        new_h = int(w / want)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    return img.resize((width, height), Image.LANCZOS)


# ---------------------------------------------------------------- column drawing

def draw_photo_story(draw, page, x, story, y_top, fonts):
    """One top-row story: kicker, photo, caption, headline, body."""
    kicker_font, caption_font, headline_font, body_font = fonts
    draw_tracked(draw, x, y_top, story["kicker"], kicker_font, AMBER)
    y = y_top + 24
    panel = photo_panel(ASSETS / story["photo"], COL_W, PHOTO_H)
    page.paste(panel, (x, y))
    draw.rectangle([x, y, x + COL_W - 1, y + PHOTO_H - 1], outline=INK, width=1)
    y += PHOTO_H + 8
    for line in wrap_text(draw, story["caption"], caption_font, COL_W):
        draw.text((x, y), line, font=caption_font, fill=GREY)
        y += 18
    y += 6
    for line in wrap_text(draw, story["headline"], headline_font, COL_W):
        draw.text((x, y), line, font=headline_font, fill=INK)
        y += 33
    y += 6
    for line in wrap_text(draw, story["body"], body_font, COL_W):
        draw.text((x, y), line, font=body_font, fill=BODY_INK)
        y += 19
    return y


def draw_text_story(draw, x, story, y_top, fonts):
    """One lower-row story: kicker, headline, body (no photo)."""
    kicker_font, headline_font, body_font = fonts
    draw_tracked(draw, x, y_top, story["kicker"], kicker_font, AMBER)
    y = y_top + 24
    for line in wrap_text(draw, story["headline"], headline_font, COL_W):
        draw.text((x, y), line, font=headline_font, fill=INK)
        y += 29
    y += 6
    for line in wrap_text(draw, story["body"], body_font, COL_W):
        draw.text((x, y), line, font=body_font, fill=BODY_INK)
        y += 19
    return y


def draw_brief_item(draw, x, y, width, place, text, fonts):
    """One IN BRIEF item: amber square bullet, bold place name, body text."""
    bold_font, body_font = fonts
    bullet = 8
    draw.rectangle([x, y + 5, x + bullet - 1, y + 5 + bullet - 1], fill=AMBER)
    tx = x + bullet + 8
    tw = width - (bullet + 8)
    lead = f"{place} — "
    lines = wrap_text(draw, lead + text, body_font, tw)
    for i, line in enumerate(lines):
        if i == 0:
            draw.text((tx, y), lead, font=bold_font, fill=INK)
            rest = line[len(lead):]
            rx = tx + draw.textlength(lead, font=bold_font)
            draw.text((rx, y), rest, font=body_font, fill=BODY_INK)
        else:
            draw.text((tx, y), line, font=body_font, fill=BODY_INK)
        y += 19
    return y


# ---------------------------------------------------------------- page

def render() -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    draw = ImageDraw.Draw(page)

    masthead_font = load_font("DejaVuSerif-Bold", 62)
    date_font = load_font("DejaVuSans-Bold", 19)
    kicker_font = load_font("DejaVuSans-Bold", 15)
    caption_font = load_font("DejaVuSerif-Italic", 13)
    headline_font = load_font("DejaVuSerif-Bold", 28)
    headline2_font = load_font("DejaVuSerif-Bold", 24)
    body_font = load_font("DejaVuSerif", 14)
    brief_bold_font = load_font("DejaVuSerif-Bold", 14)
    chip_font = load_font("DejaVuSans-Bold", 15)
    footer_font = load_font("DejaVuSans", 13)
    tagline_font = load_font("DejaVuSans-Bold", 14)

    # --- top rules + masthead + dateline + double rule
    draw.rectangle([MARGIN, 20, MARGIN + CONTENT_W - 1, 22], fill=CHARCOAL)
    draw.line([MARGIN, 27, MARGIN + CONTENT_W - 1, 27], fill=AMBER_RULE, width=1)
    draw.text((centre_x(draw, MASTHEAD, masthead_font), 36),
              MASTHEAD, font=masthead_font, fill=INK)
    date_w = draw.textlength(DATE_LINE, font=date_font)
    tail_w = draw.textlength(DATE_TAIL, font=date_font)
    total = date_w + tail_w
    x0 = (PAGE_W - total) / 2
    draw.text((x0, 106), DATE_LINE, font=date_font, fill=AMBER)
    draw.text((x0 + date_w, 106), DATE_TAIL, font=date_font, fill=GREY)
    draw.rectangle([MARGIN, 128, MARGIN + CONTENT_W - 1, 129], fill=CHARCOAL)
    draw.line([MARGIN, 134, MARGIN + CONTENT_W - 1, 134], fill=AMBER_RULE, width=1)

    # --- row A: three photo stories, lead in the centre column
    col_x = [MARGIN, MARGIN + COL_W + GUTTER, MARGIN + 2 * (COL_W + GUTTER)]
    row_a_top = 148
    bottoms = []
    for x, story in zip(col_x, TOP_STORIES):
        bottoms.append(draw_photo_story(
            draw, page, x, story, row_a_top,
            (kicker_font, caption_font, headline_font, body_font)))
    row_a_bottom = max(bottoms)
    # faint vertical separators between the columns
    for sep_x in (col_x[1] - GUTTER // 2 - 1, col_x[2] - GUTTER // 2 - 1):
        draw.line([sep_x, row_a_top, sep_x, row_a_bottom], fill=HAIRLINE, width=1)

    # --- row B: three text stories
    y = row_a_bottom + 12
    draw.line([MARGIN, y, MARGIN + CONTENT_W - 1, y], fill=HAIRLINE, width=1)
    row_b_top = y + 12
    bottoms_b = []
    for x, story in zip(col_x, LOWER_STORIES):
        bottoms_b.append(draw_text_story(
            draw, x, story, row_b_top,
            (kicker_font, headline2_font, body_font)))
    row_b_bottom = max(bottoms_b)
    for sep_x in (col_x[1] - GUTTER // 2 - 1, col_x[2] - GUTTER // 2 - 1):
        draw.line([sep_x, row_b_top, sep_x, row_b_bottom], fill=HAIRLINE, width=1)

    # --- IN BRIEF band
    y = row_b_bottom + 12
    draw.line([MARGIN, y, MARGIN + CONTENT_W - 1, y], fill=HAIRLINE, width=1)
    y += 12
    chip = "IN BRIEF"
    chip_w = draw.textlength(chip, font=chip_font) + 28
    draw.rectangle([MARGIN, y, MARGIN + chip_w - 1, y + 25], fill=CHARCOAL)
    draw.text((MARGIN + 14, y + 5), chip, font=chip_font, fill=AMBER)
    y += 25 + 10
    brief_w = (CONTENT_W - GUTTER) // 2
    row_ends = []
    for row in range(2):
        left = BRIEF_ITEMS[row * 2]
        right = BRIEF_ITEMS[row * 2 + 1]
        end_l = draw_brief_item(draw, MARGIN, y, brief_w, left[0], left[1],
                                (brief_bold_font, body_font))
        end_r = draw_brief_item(draw, MARGIN + brief_w + GUTTER, y, brief_w,
                                right[0], right[1],
                                (brief_bold_font, body_font))
        row_ends.append(max(end_l, end_r))
        y = max(end_l, end_r) + 8

    # --- footer
    y = row_ends[-1] + 6
    draw.line([MARGIN, y, MARGIN + CONTENT_W - 1, y], fill=HAIRLINE, width=1)
    draw.text((centre_x(draw, SOURCES, footer_font), y + 10),
              SOURCES, font=footer_font, fill=GREY)
    draw.text((centre_x(draw, TAGLINE, tagline_font), y + 32),
              TAGLINE, font=tagline_font, fill=AMBER)
    return page


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else HERE / "entry.png"
    img = render()
    img.save(out, format="PNG")
    print(f"wrote {out} ({img.size[0]}x{img.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
