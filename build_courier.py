"""The Globe Courier — compositor for news-image-20261123.

Builds entry.png (1024x1024), a one-page broadsheet for Monday,
23 November 2026, from three photo panels generated in-session plus
typeset headlines. Run:  python3 build_courier.py [output-path]
Deterministic: same inputs always produce the same bytes.

Design: charcoal + amber, centred masthead, three equal columns,
lead story in the centre column topped by its photo panel.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"

W = H = 1024
MARGIN = 28
CONTENT = W - 2 * MARGIN
COL = 304
GUT = 28

PAPER = (247, 243, 234)
INK = (32, 32, 34)
CHARCOAL = (44, 44, 48)
AMBER = (178, 114, 18)
AMBER_DARK = (138, 86, 10)
MUTED = (98, 94, 84)
BODY = (58, 56, 50)
FAINT = (205, 199, 186)

FONTS = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    try:
        return ImageFont.truetype(str(Path(FONTS) / name), size)
    except OSError:
        return ImageFont.load_default(size)


SERIF_B = lambda s: font("DejaVuSerif-Bold.ttf", s)
SERIF = lambda s: font("DejaVuSerif.ttf", s)
SERIF_I = lambda s: font("DejaVuSerif-Italic.ttf", s)
SANS = lambda s: font("DejaVuSans.ttf", s)
SANS_B = lambda s: font("DejaVuSans-Bold.ttf", s)


def wrap(draw, text, fnt, width):
    """Greedy word wrap; returns a list of lines that fit `width`."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(draw, x, y, text, fnt, width, fill=INK, leading=None):
    """Draw wrapped text; returns the y just below the last line."""
    leading = leading or int(fnt.size * 1.22)
    for line in wrap(draw, text, fnt, width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def rule(draw, x, y, width, fill=CHARCOAL, px=2):
    draw.rectangle([x, y, x + width, y + px - 1], fill=fill)


def kicker(draw, x, y, text, size=14):
    fnt = SANS_B(size)
    draw.text((x, y), text.upper(), font=fnt, fill=AMBER_DARK)
    return y + int(size * 1.55)


def cover_crop(img, tw, th):
    """Centre-crop to the target aspect, then resize."""
    sw, sh = img.size
    target = tw / th
    if sw / sh > target:
        nw = int(sh * target)
        box = ((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh)
    else:
        nh = int(sw / target)
        box = (0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh)
    return img.crop(box).resize((tw, th), Image.LANCZOS)


def photo(draw, canvas, path, x, y, w, h, caption=None):
    img = Image.open(path).convert("RGB")
    canvas.paste(cover_crop(img, w, h), (x, y))
    draw.rectangle([x, y, x + w - 1, y + h - 1], outline=CHARCOAL, width=2)
    if caption:
        draw.text((x, y + h + 5), caption, font=SERIF_I(12), fill=MUTED)
        return y + h + 22
    return y + h


def story(draw, canvas, x, y, kicker_text, img_path, caption,
          headline, deck, head_size=24, photo_h=178):
    """One photo story in a column; returns the y below it."""
    y = kicker(draw, x, y, kicker_text)
    y = photo(draw, canvas, img_path, x, y + 2, COL, photo_h, caption)
    y = para(draw, x, y + 6, headline, SERIF_B(head_size), COL,
             leading=head_size + 6)
    y = para(draw, x, y + 6, deck, SANS(14), COL, fill=BODY, leading=19)
    return y


def text_story(draw, x, y, kicker_text, headline, deck):
    """One text-only story in a column; returns the y below it."""
    y = kicker(draw, x, y, kicker_text)
    y = para(draw, x, y + 2, headline, SERIF_B(21), COL, leading=26)
    y = para(draw, x, y + 5, deck, SANS(14), COL, fill=BODY, leading=19)
    return y


def build():
    canvas = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(canvas)
    xs = [MARGIN, MARGIN + COL + GUT, MARGIN + 2 * (COL + GUT)]

    # ---- Masthead: centred, charcoal + amber ----------------------
    rule(d, MARGIN, 20, CONTENT, fill=CHARCOAL, px=4)
    rule(d, MARGIN, 27, CONTENT, fill=AMBER, px=2)
    mast = SERIF_B(52)
    title = "THE GLOBE COURIER"
    d.text(((W - d.textlength(title, font=mast)) / 2, 38), title,
           font=mast, fill=INK)
    date_f = SANS_B(18)
    date_t = "MONDAY, 23 NOVEMBER 2026"
    sub_f = SANS(18)
    sub_t = "  \u2022  WORLD NEWS IN ONE PAGE"
    total = d.textlength(date_t, font=date_f) + d.textlength(sub_t, font=sub_f)
    x = (W - total) / 2
    d.text((x, 102), date_t, font=date_f, fill=AMBER_DARK)
    d.text((x + d.textlength(date_t, font=date_f), 102), sub_t,
           font=sub_f, fill=MUTED)
    rule(d, MARGIN, 132, CONTENT, fill=AMBER, px=2)
    rule(d, MARGIN, 137, CONTENT, fill=CHARCOAL, px=1)

    # ---- Row A: three photo stories; lead in the centre -----------
    y0 = 152
    antalya = ASSETS / "media-generation-panel-antalya-0-99704f85-53f1-4232-8983-529e92c3f1d0.webp"
    hormuz = ASSETS / "media-generation-panel-hormuz-0-7f93a5ea-b615-43e0-a324-34b8ca01c55c.webp"
    benghazi = ASSETS / "media-generation-panel-benghazi-0-3e4ad8ef-b714-417f-b2e8-f3f865e50440.webp"
    end_l = story(
        d, canvas, xs[0], y0, "Strait of Hormuz", hormuz,
        "A tanker in the Strait of Hormuz at dawn.",
        "Two more tankers hit mines as the strait burns",
        "Two supertankers catch fire after striking naval mines east of "
        "Hormuz on Sunday, and UK maritime authorities report projectile "
        "strikes near Khasab. Attacks on shipping are at their highest "
        "level since the war began.",
        head_size=24)
    end_c = story(
        d, canvas, xs[1], y0, "Antalya \u2014 Lead story", antalya,
        "The COP31 plenary hall in Antalya, emptying.",
        "COP31 collapses: no deal on fossil fuels",
        "After two weeks and record overtime, the climate summit ends "
        "without an overarching pact \u2014 the first such failure since "
        "Copenhagen in 2009. The EU, the UK and island states reject a "
        "text that never mentions fossil fuels.",
        head_size=27)
    end_r = story(
        d, canvas, xs[2], y0, "Benghazi", benghazi,
        "A warship listing in Benghazi harbour at dawn.",
        "Russian warship sunk by sea drones off Libya",
        "The corvette Merkury capsizes and sinks after suspected Ukrainian "
        "sea drones strike it in port; a second vessel is hit hours later. "
        "Libya asks the UN to investigate.",
        head_size=24)
    row_a_end = max(end_l, end_c, end_r)

    # ---- Vertical separators between the columns ------------------
    for gx in (MARGIN + COL + GUT // 2, MARGIN + 2 * COL + 3 * GUT // 2):
        d.line([(gx, y0), (gx, row_a_end)], fill=FAINT, width=1)

    # ---- Row B: three text stories --------------------------------
    y = row_a_end + 14
    rule(d, MARGIN, y, CONTENT, fill=FAINT, px=1)
    y += 14
    end_l = text_story(
        d, xs[0], y, "Brussels",
        "NATO meets today after Russian missiles land in Poland",
        "Prosecutors confirm all three objects that fell on Friday were "
        "Russian Kh-101 cruise missiles. The North Atlantic Council holds "
        "an emergency session in Brussels.")
    end_c = text_story(
        d, xs[1], y, "Sinaloa",
        "Mexico captures \u2018El Chapo Isidro\u2019 in deadly raid",
        "FBI most-wanted fugitive Fausto Isidro Meza Flores is seized in "
        "Guasave; 11 people are killed, four of them soldiers. US "
        "intelligence helped plan the raid.")
    end_r = text_story(
        d, xs[2], y, "Kyiv region",
        "Drone hits apartment block; 11 missing in the rubble",
        "A Russian drone strikes a five-storey block in Dymer, north of "
        "Kyiv, early on Sunday, killing two. Rescuers search for "
        "survivors, including two children.")
    row_b_end = max(end_l, end_c, end_r)

    # ---- In brief --------------------------------------------------
    y = row_b_end + 14
    rule(d, MARGIN, y, CONTENT, fill=FAINT, px=1)
    y += 12
    chip = "IN BRIEF"
    chip_f = SANS_B(14)
    chip_w = d.textlength(chip, font=chip_f) + 20
    d.rectangle([MARGIN, y, MARGIN + chip_w, y + 23], fill=CHARCOAL)
    d.text((MARGIN + 10, y + 4), chip, font=chip_f, fill=(232, 178, 74))
    y += 31
    briefs = [
        ("GENEVA", "128 states agree to pursue rules on killer robots by 2028."),
        ("JUBA", "24 civilians killed in fresh violence in South Sudan."),
        ("CIKANDE", "Seven bodies recovered, dozens missing after a factory fire in Indonesia."),
        ("OKINAWA", "Shuri Castle\u2019s restored main hall opens, seven years after fire."),
    ]
    for row in range(2):
        pair = briefs[row * 2:(row + 1) * 2]
        wrapped = []
        for city, text in pair:
            off = d.textlength(city + " \u2014 ", font=SANS_B(13))
            lines = wrap(d, text, SANS(13), COL + GUT - 14 - off)
            wrapped.append((city, lines, off))
        row_h = max(len(lines) for _, lines, _ in wrapped) * 16
        for i, (city, lines, off) in enumerate(wrapped):
            bx = MARGIN + i * (COL + GUT)
            d.text((bx, y), "\u25aa ", font=SANS_B(13), fill=AMBER_DARK)
            cx = bx + 14
            d.text((cx, y), city + " \u2014 ", font=SANS_B(13), fill=INK)
            yy = y
            for j, line in enumerate(lines):
                d.text((cx + (off if j == 0 else 0), yy), line,
                       font=SANS(13), fill=BODY)
                yy += 16
        y += row_h + 8

    # ---- Footer ----------------------------------------------------
    rule(d, MARGIN, 978, CONTENT, fill=FAINT, px=1)
    foot = ("Sources: CNN \u2022 Reuters \u2022 Le Monde \u2022 AP \u2022 AFP \u2022 "
            "UKMTO \u2022 The Times")
    ff = SANS(11)
    d.text(((W - d.textlength(foot, font=ff)) / 2, 986), foot,
           font=ff, fill=MUTED)
    tag = "THE GLOBE COURIER \u2014 ONE DAY. ONE PAGE."
    tf = SANS_B(11)
    d.text(((W - d.textlength(tag, font=tf)) / 2, 1002), tag,
           font=tf, fill=AMBER_DARK)

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "entry.png"
    canvas.save(out, "PNG", optimize=True)
    size = out.stat().st_size
    print(f"wrote {out} {size} bytes")
    if size > 1_048_576:
        canvas.save(out, "JPEG", quality=88, optimize=True)
        print(f"PNG over 1 MiB; re-saved as JPEG bytes: {out.stat().st_size}")


if __name__ == "__main__":
    build()
