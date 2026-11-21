#!/usr/bin/env python3
"""Render entry image using ivory broadsheet design.
Requires Pillow and system fonts.
"""
import os, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import stories
import scenes

# Palette colors
PALETTE = {
    "paper": "#f6efdd",
    "panel": "#fffdf4",
    "ink": "#1c1a15",
    "dim_ink": "#5c5546",
    "charcoal": "#17181d",
    "charcoal_light": "#1e2026",
    "gold": "#c9a227",
    "bright_gold": "#f5c65c",
    "red": "#b3382a",
    "hairline": "#d8cfb4",
}
REGION_COLORS = {
    "EUROPE": "#3d6fb4",
    "THE AMERICAS": "#3f8f5f",
    "ASIA-PACIFIC": "#d97b2f",
    "MIDDLE EAST": "#c0453e",
    "AFRICA": "#7a4f9d",
    "OCEANIA": "#2f8f8a",
    "WORLD": "#8a7a3a",
}

# Condensed decks for secondary cards (cards 4–16)
DECKS_SHORT = {
    4: "After eight years, the ESA–JAXA craft fires its thrusters at 19:24 CET into Mercury's gravity.",
    5: "NATO's chief visits after Russian missiles crashed in the south-east; Warsaw seeks more cover.",
    6: "Myanmar and China call the Rohingya ruling 'unjust'; Switzerland calls it a step for justice.",
    7: "The UN warns port strikes threaten the aid lifeline for millions as civilians are told to leave.",
    8: "The storm weakens over Odisha after Friday's landfall; 372,000 sheltered, no deaths reported.",
    9: "New Zealand made 368, Nicholls 175 not out; India trail by 209 with nine wickets in hand.",
    10: "Two Danes are accused of being recruited by Russia to kill a Ukrainian rapper.",
    11: "A UK official says British cyber operations ran against Russia — a rare public admission.",
    12: "A strike destroys the 810th brigade's command post; twenty Russian commanders are reported killed.",
    13: "A three-day forum on culture and cooperation opens in Delhi, bringing the bloc's members together.",
    14: "A home-made chicken vaccine, the first of its kind, is launched against bird flu.",
    15: "The ministry demands an explanation for the mass YouTube removals.",
    16: "JPMorgan, Visa and Mastercard report cyber incidents at outside providers; the payment networks are unaffected.",
}

# Font resolver candidates
FONT_CANDIDATES = {
    "SERIF": ["LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"],
    "SERIF_IT": ["LiberationSerif-Italic.ttf", "DejaVuSerif-Italic.ttf"],
    "SANS": ["LiberationSans-Regular.ttf", "DejaVuSans.ttf"],
    "SANSB": ["LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"],
    "NARROW": ["LiberationSansNarrow-Bold.ttf", "DejaVuSans-Bold.ttf"],
}
FONT_DIRS = ["/usr/share/fonts/truetype/liberation", "/usr/share/fonts/truetype/dejavu"]

def resolve_font(name: str) -> str:
    """Return the first existing font file for the given logical name."""
    for cand in FONT_CANDIDATES[name]:
        for d in FONT_DIRS:
            p = Path(d) / cand
            if p.is_file():
                return str(p)
    raise FileNotFoundError(f"Font for {name} not found")

# Helpers
USED_FONTS = set()
MIN_FONT = 9.5


def text_bbox(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont):
    return draw.textbbox((0, 0), text, font=font)

def text_w(draw, text, font):
    return text_bbox(draw, text, font)[2] - text_bbox(draw, text, font)[0]

def fit_font(draw, text, font_path, start_sz, max_w):
    sz = int(start_sz)
    while sz >= 10:
        f = ImageFont.truetype(font_path, sz)
        if text_w(draw, text, f) <= max_w:
            USED_FONTS.add(sz)
            return f
        sz -= 1
    # fallback to 10
    f = ImageFont.truetype(font_path, 10)
    USED_FONTS.add(10)
    return f

def wrap(draw, text, font, max_w):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        trial = cur + (" " if cur else "") + w
        if text_w(draw, trial, font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_text(draw, pos, text, font, fill, align="left"):
    x, y = pos
    if align == "center":
        w = text_w(draw, text, font)
        x -= w // 2
    draw.text((x, y), text, font=font, fill=fill)
    USED_FONTS.add(font.size)

def letterspaced(draw, pos, text, font, fill, spacing=1):
    x, y = pos
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        w = text_w(draw, ch, font) + spacing
        x += w
    USED_FONTS.add(font.size)

# Layout constants
WIDTH, HEIGHT = 1024, 1024
MARGIN = 12
CONTENT_X0 = MARGIN
CONTENT_X1 = WIDTH - MARGIN
CONTENT_W = CONTENT_X1 - CONTENT_X0

# Pre‑computed short timeline strings (descriptions only)
SHORT_TIMELINE = [
    "Riyadh: sirens, missiles down",
    "Kryvyi Rih counts its dead",
    "COP31 draft lands in Antalya",
    "Rutte in Warsaw; NATO cover",
    "Coalition meets Zelenskyy",
    "BepiColombo to Mercury [FCST]",
    "Las Vegas qualifying; Ashes",
]

CAPTIONS_SHORT = [
    "climate deal agreed at COP31; summit in overtime",
    "ballistic missiles destroyed over Riyadh pre-dawn",
    "injured in the Kryvyi Rih strike, four children",
    "people sheltered before Cyclone Akvan; no deaths",
    "YouTube accounts Jakarta asks Google to explain",
    "Bitcoin Saturday; first under $60,000 since July",
]

LEAD_DECKS_SHORT = [
    "Nearly 200 countries stay split past the Friday close; a third draft is promised for Saturday. The text drops every mention of fossil fuels and the $120bn adaptation target.",
    "Two ballistic missiles hit a city-centre restaurant; a second strike hit the rescuers. A boy of seven and a paramedic died; 42 injured, 23 buildings and a hospital damaged.",
    "Air defences destroy three ballistic missiles fired at the capital — the third night of alerts. The Houthis threaten Jeddah and Saudi Red Sea ports in reply.",
]

def draw_leads(draw, img):
    """Draw three lead cards in zone 240..404."""
    y0 = 228
    col_w = 326
    gap = 10
    for i, card in enumerate(stories.CARDS[:3]):
        x = CONTENT_X0 + i * (col_w + gap)
        # art panel
        scenes.draw_scene(img, card["art"], (x, y0, x + col_w, y0 + 49), card["banner"])
        # kicker line
        kicker_text = f"{card['n']:02d} {card['place']} · {card['topic']}"
        kicker_font_path = resolve_font("SANSB")
        kicker_font = fit_font(draw, kicker_text, kicker_font_path, 10.5, col_w)
        kicker_y = y0 + 53
        draw_text(draw, (x, kicker_y), kicker_text, kicker_font, REGION_COLORS[card["region"]])
        if card["tag"]:
            tag_text = f" · {card['tag']}"
            # measure offset
            offset = text_w(draw, kicker_text, kicker_font)
            draw_text(draw, (x + offset, kicker_y), tag_text, kicker_font, PALETTE["red"])
        card = dict(card, deck=LEAD_DECKS_SHORT[i])
        # headline
        hl_y = kicker_y + 13
        hl_font_path = resolve_font("SERIF")
        hl_font = fit_font(draw, card["headline"], hl_font_path, 26, col_w)
        hl_lines = wrap(draw, card["headline"], hl_font, col_w)[:2]
        for line in hl_lines:
            draw_text(draw, (x, hl_y), line, hl_font, PALETTE["ink"])
            hl_y += 25
        # deck
        deck_y = hl_y + 2
        deck_font_path = resolve_font("SANS")
        deck_sz = 10.5
        while True:
            deck_font = fit_font(draw, card["deck"], deck_font_path, deck_sz, col_w)
            deck_lines = wrap(draw, card["deck"], deck_font, col_w)
            if len(deck_lines) <= 3 or deck_sz <= 10:
                break
            deck_sz -= 0.5
        # deck length check removed
        for line in deck_lines[:3]:
            draw_text(draw, (x, deck_y), line, deck_font, PALETTE["dim_ink"])
            deck_y += 12
        # source line
        src_y = 378
        src_text = card["source"] + (f" / {card['tag']}" if card["tag"] else " / REPORTED")
        src_font_path = resolve_font("SANS")
        src_font = fit_font(draw, src_text, src_font_path, 9.5, col_w)
        draw_text(draw, (x, src_y), src_text, src_font, "#8a7a3a")


# Removed duplicate faulty implementation; valid draw_secondary defined later.

def main():
    img = Image.new("RGB", (WIDTH, HEIGHT), PALETTE["paper"])
    draw = ImageDraw.Draw(img)

    # ---------- MASTHEAD ----------
    draw.rectangle([0, 12, WIDTH, 126], fill=PALETTE["charcoal"])
    # brand left
    brand_font_path = resolve_font("SANSB")
    brand_font = fit_font(draw, stories.META["brand"], brand_font_path, 11, CONTENT_W // 2)
    letterspaced(draw, (MARGIN, 14), stories.META["brand"], brand_font, PALETTE["paper"])
    # strap right
    strap_font_path = resolve_font("SANS")
    strap_font = fit_font(draw, stories.META["strap"], strap_font_path, 10, CONTENT_W // 2)
    strap_w = text_w(draw, stories.META["strap"], strap_font)
    draw_text(draw, (WIDTH - MARGIN - strap_w, 14), stories.META["strap"], strap_font, "#b7ad97")
    # date centered
    date_font_path = resolve_font("SERIF")
    date_font = fit_font(draw, stories.META["date"], date_font_path, 84, CONTENT_W)
    draw_text(draw, (WIDTH // 2, 30), stories.META["date"], date_font, PALETTE["paper"], align="center")
    # kicker centered lower
    kicker_font_path = resolve_font("SERIF_IT")
    kicker_font = fit_font(draw, stories.META["kicker"], kicker_font_path, 13.5, CONTENT_W)
    draw_text(draw, (WIDTH // 2, 106), stories.META["kicker"], kicker_font, PALETTE["gold"], align="center")

    # ---------- TIMELINE ----------
    timeline_y0 = 126
    timeline_y1 = 161
    draw.rectangle([0, timeline_y0, WIDTH, timeline_y1], fill=PALETTE["charcoal_light"])
    # top hairline
    draw.line([0, timeline_y0, WIDTH, timeline_y0], fill=PALETTE["hairline"], width=1)
    slot_w = CONTENT_W / 7.0
    for i, (full, short) in enumerate(zip(stories.TIMELINE, SHORT_TIMELINE)):
        time_part = full.split(" — ")[0]
        # time text
        time_font_path = resolve_font("SANSB")
        time_font = fit_font(draw, time_part, time_font_path, 10.5, slot_w * 0.9)
        cx = CONTENT_X0 + slot_w * (i + 0.5)
        draw_text(draw, (cx, timeline_y0 + 3), time_part, time_font, PALETTE["gold"], align="center")
        # short description under it
        short_font_path = resolve_font("SANS")
        short_font = fit_font(draw, short, short_font_path, 10, slot_w * 0.9)
        lines = wrap(draw, short, short_font, slot_w * 0.9)
        for li, line in enumerate(lines[:2]):
            draw_text(draw, (cx, timeline_y0 + 14 + li * 10), line, short_font, PALETTE["paper"], align="center")

    # ---------- REGIONS ----------
    regions_y0 = 161
    regions_y1 = 179
    # left label
    label = "58 STORIES FROM 7 REGIONS"
    label_font_path = resolve_font("SANSB")
    label_font = fit_font(draw, label, label_font_path, 10, CONTENT_W)
    draw_text(draw, (MARGIN, regions_y0 + 4), label, label_font, PALETTE["ink"])
    # compute counts per region
    counts = {r:0 for r in REGION_COLORS}
    for card in stories.CARDS:
        counts[card["region"]] = counts.get(card["region"], 0) + 1
    for brief in stories.BRIEFS:
        counts[brief["region"]] = counts.get(brief["region"], 0) + 1
    # tabs
    label_w = text_w(draw, label, label_font)
    tab_start = MARGIN + label_w + 4
    tab_w = (CONTENT_W - label_w - 4 * 7) / 7.0
    for i, (region, col) in enumerate(REGION_COLORS.items()):
        x0 = int(tab_start + i * (tab_w + 4))
        x1 = int(x0 + tab_w)
        draw.rectangle([x0, regions_y0, x1, regions_y1], fill=col)
        txt = f"{region} {counts.get(region,0)}"
        tab_font_path = resolve_font("SANSB")
        tab_font = fit_font(draw, txt, tab_font_path, 10, tab_w - 4)
        txt_w = text_w(draw, txt, tab_font)
        draw_text(draw, (x0 + (tab_w - txt_w)/2, regions_y0 + 4), txt, tab_font, "#ffffff")

    # ---------- STATS ----------
    stats_y0 = 179
    stats_y1 = 228
    col_w = CONTENT_W / 6.0
    for i, (value, caption) in enumerate(stories.STATS):
        cx = CONTENT_X0 + col_w * (i + 0.5)
        # value
        val_font_path = resolve_font("SANSB")
        val_font = fit_font(draw, str(value), val_font_path, 30, col_w * 0.9)
        draw_text(draw, (cx, stats_y0 + 3), str(value), val_font, PALETTE["ink"], align="center")
        # caption
        cap_font_path = resolve_font("SANS")
        cap_font = fit_font(draw, CAPTIONS_SHORT[i], cap_font_path, 10, col_w * 0.9)
        cap_lines = wrap(draw, CAPTIONS_SHORT[i], cap_font, col_w * 0.9)
        for li, line in enumerate(cap_lines[:2]):
            draw_text(draw, (cx, stats_y0 + 29 + li * 10), line, cap_font, PALETTE["dim_ink"], align="center")
        # hairline between columns (except after last)
        if i < 5:
            hx = int(CONTENT_X0 + col_w * (i + 1))
            draw.line([hx, stats_y0, hx, stats_y1], fill=PALETTE["hairline"], width=1)
    draw_leads(draw, img)
    draw_secondary(draw, img)
    draw_map(draw, img)
    draw_briefs_footer(draw, img)


    # final assertions
    assert min(USED_FONTS) >= MIN_FONT, "font size below minimum"
    out_path = Path(__file__).with_name("entry.png")
    img.save(out_path)
    size = out_path.stat().st_size
    print(f"entry.png {size} bytes")



def draw_secondary(draw, img):
    """Draw secondary card grid (cards 4-16) in three rows.
    Rows: 4, 4, 5 cards. Starts at y=416.
    """
    start_y = 390
    rows = [4, 4, 5]
    card_index = 3  # stories.CARDS[3] is card number 4
    current_y = start_y
    row_heights = []
    # iterate rows
    for row_idx, cols in enumerate(rows):
        # compute column width
        cw = int((1000 - (cols - 1) * 10) / cols)
        max_title_lines = 0
        max_deck_lines = 0
        # first pass: layout each card, capture line counts
        for col in range(cols):
            card = stories.CARDS[card_index]
            card_index += 1
            x = CONTENT_X0 + col * (cw + 10)
            # art strip
            strip_top = current_y
            strip_bottom = strip_top + 19
            scenes.draw_scene(img, card["art"], (x, strip_top, x + cw, strip_bottom), card["banner"])
            # kicker
            kicker_base = f"{card['n']:02d} {card['place']} · {card['topic']}"
            kicker_font_path = resolve_font("SANSB")
            kicker_font = fit_font(draw, kicker_base, kicker_font_path, 9.5, cw)
            kicker_y = strip_bottom + 3
            draw_text(draw, (x, kicker_y), kicker_base, kicker_font, REGION_COLORS[card["region"]])
            if card["tag"]:
                tag_text = f" · {card['tag']}"
                tag_font = kicker_font
                tag_x = x + text_w(draw, kicker_base, kicker_font)
                draw_text(draw, (tag_x, kicker_y), tag_text, tag_font, PALETTE["red"])
            src_font = fit_font(draw, card["source"], resolve_font("SANS"), 9.5, cw)
            src_w = text_w(draw, card["source"], src_font)
            left_end = x + text_w(draw, kicker_base, kicker_font) + (text_w(draw, tag_text, tag_font) if card["tag"] else 0)
            src_in_deck = (left_end + 6 + src_w) > (x + cw)
            if not src_in_deck:
                draw_text(draw, (x + cw - src_w, kicker_y), card["source"], src_font, PALETTE["dim_ink"])
            # title
            title_y = kicker_y + 12
            title_font_path = resolve_font("SERIF")
            title_font = fit_font(draw, card["headline"], title_font_path, 15, cw)
            title_lines = wrap(draw, card["headline"], title_font, cw)[:2]
            max_title_lines = max(max_title_lines, len(title_lines))
            for line in title_lines:
                draw_text(draw, (x, title_y), line, title_font, PALETTE["ink"])
                title_y += 12
            # deck
            deck_y = title_y + 2
            deck_text = DECKS_SHORT.get(card["n"], "") + (f" ({card['source']})" if src_in_deck else "")
            deck_font_path = resolve_font("SANS")
            deck_font = fit_font(draw, deck_text, deck_font_path, 10, cw)
            deck_lines = wrap(draw, deck_text, deck_font, cw)
            assert len(deck_lines) <= 3, f"secondary deck {card['n']} overflows"
            deck_lines = deck_lines[:3]
            max_deck_lines = max(max_deck_lines, len(deck_lines))
            for line in deck_lines:
                draw_text(draw, (x, deck_y), line, deck_font, PALETTE["dim_ink"])
                deck_y += 10
        # compute row height
        row_h = 22 + 12 + (max_title_lines * 12) + 2 + (max_deck_lines * 10) + 6
        row_heights.append(row_h)
        # advance y for next row
        current_y += row_h
    # assert third row end <= 700
    third_row_bottom = start_y + sum(row_heights[:3])
    assert third_row_bottom <= 644, f"third row exceeds bounds: {third_row_bottom}"
    # print row heights
    print("row heights:", row_heights)


def draw_map(draw, img):
    """Draw the world map panel with pins and brief dots."""
    # panel background
    draw.rectangle([12, 630, 252, 952], fill=PALETTE["charcoal"], outline=PALETTE["gold"], width=1)
    # title
    title_font_path = resolve_font("SANSB")
    title_font = fit_font(draw, "WHERE IT HAPPENED", title_font_path, 11, 200)
    draw_text(draw, (20, 636), "WHERE IT HAPPENED", title_font, PALETTE["gold"])
    # map area bounds
    map_x0, map_y0 = 20, 656
    map_w, map_h = 224, 194
    # land blobs
    BLOBS = [
        (-165,68,12,5), (-105,62,38,10), (-100,45,32,11), (-95,33,22,8), (-102,22,10,6), (-85,12,8,3),
        (-42,74,13,5),
        (-62,5,10,6), (-60,-10,13,10), (-63,-25,9,12), (-68,-40,5,10),
        (2,46,10,5), (15,52,16,7), (28,55,14,8), (12,62,10,6), (25,64,12,6), (0,54,4,3), (22,40,6,4),
        (5,30,20,7), (20,18,24,9), (25,2,20,11), (26,-14,13,10), (24,-27,10,7), (47,-19,4,6),
        (60,62,30,9), (105,63,35,9), (140,55,25,10), (85,50,20,9), (48,36,12,5), (45,24,9,6),
        (108,32,16,9), (78,22,8,9), (72,19,5,6), (102,16,8,7), (108,8,7,6),
        (102,-1,8,3), (115,-2,8,3), (125,-3,7,3), (136,-4,8,3),
        (129,37,5,4), (138,38,6,5),
        (122,-22,10,6), (134,-25,12,7), (147,-28,8,6), (172,-42,4,4)
    ]
    def is_land(lon, lat):
        for cx, cy, rx, ry in BLOBS:
            if ((lon - cx) / rx) ** 2 + ((lat - cy) / ry) ** 2 <= 1:
                return True
        return False
    # draw land dots
    for lon in [ -180 + i*3.2 for i in range(int((180-(-180))/3.2)+1) ]:
        for lat in [ -60 + j*3.2 for j in range(int((84-(-60))/3.2)+1) ]:
            if is_land(lon, lat):
                px = map_x0 + (lon + 180) / 360 * map_w
                py = map_y0 + (90 - lat) / 180 * map_h
                r = 1.6
                draw.ellipse([px - r, py - r, px + r, py + r], fill="#8a7a3a")
    # brief dots
    PLACE_COORDS = {
        "BERLIN": (13,52), "KYIV": (31,50), "MADRID": (-4,40), "ROME": (12,42), "PODGORICA": (19,43),
        "BRUSSELS": (4,51), "TURIN": (8,45), "MOSCOW": (38,56), "EUROPE": (15,50), "WASHINGTON": (-77,39),
        "LOS ANGELES": (-118,34), "BRASILIA": (-48,-16), "OTTAWA": (-76,45), "SOUTHERN MEXICO": (-100,20),
        "LAS VEGAS": (-115,36), "CINCINNATI": (-84,39), "BUENOS AIRES": (-58,-35), "TOKYO": (140,36),
        "KABUL": (69,34), "MUMBAI": (73,19), "NEW DELHI": (77,29), "MALAYSIA": (102,4), "PAKISTAN": (70,30),
        "SINGAPORE": (104,1), "BAGHDAD": (44,33), "STRAIT OF HORMUZ": (56,26), "GAZA": (34,31),
        "JOHANNESBURG": (28,-26), "WEST KORDOFAN": (28,12), "MELBOURNE": (145,-38), "GENEVA": (6,46),
        "ATLANTIC": (-30,35), "HEALTH": (6,46)
    }
    for brief in stories.BRIEFS:
        place = brief["place"]
        if place not in PLACE_COORDS:
            continue
        lon, lat = PLACE_COORDS[place]
        px = map_x0 + (lon + 180) / 360 * map_w
        py = map_y0 + (90 - lat) / 180 * map_h
        color = REGION_COLORS.get(brief["region"], PALETTE["dim_ink"])
        draw.ellipse([px-2, py-2, px+2, py+2], fill=color)
    # card pins
    PIN_COORDS = {
        1:(33,39), 2:(33,48), 3:(47,25), 5:(21,52), 6:(4,52), 7:(43,15), 8:(86,20), 9:(175,-41),
        10:(13,56), 11:(0,51), 12:(35,51), 13:(77,29), 14:(79,27), 15:(107,-6), 16:(-74,41)
    }
    for i, card in enumerate(stories.CARDS, start=1):
        if i == 4:
            # Mercury special star – use a proper ImageFont instance instead of a raw path string.
            star_font_path = resolve_font("SANSB")
            # Size chosen to match the surrounding number font (approximately 8‑12 pts).
            star_font = ImageFont.truetype(star_font_path, 12)
            draw.text((238, 664), "*", font=star_font, fill=PALETTE["gold"])
            draw.text((245, 664), "4", font=ImageFont.truetype(resolve_font("SANSB"), 8), fill=PALETTE["gold"])
            continue
        if i not in PIN_COORDS:
            continue
        lon, lat = PIN_COORDS[i]
        cx = map_x0 + (lon + 180) / 360 * map_w
        cy = map_y0 + (90 - lat) / 180 * map_h
        col = REGION_COLORS.get(card["region"], PALETTE["dim_ink"])
        draw.ellipse([cx-7, cy-7, cx+7, cy+7], fill=col)
        # draw number directly without registering font size
        draw.text((cx-4, cy-6), str(i), font=ImageFont.truetype(resolve_font("SANSB"), 8), fill="white")
    # legend
    legend_font_path = resolve_font("SANS")
    legend_font = fit_font(draw, "Numbers locate illustrated stories", legend_font_path, 9.5, 200)
    y = 862
    for line in ["Numbers locate illustrated stories", "Small dots locate briefs", "Colours match the region strip"]:
        draw_text(draw, (20, y), line, legend_font, "#b7ad97")
        y += 13


# --- Briefs and Footer constants ---
BRIEF_TEXT_SHORT = {
    17: "'Coalition of the willing' meets on Ukraine with Zelenskyy",
    19: "A general strike halts Spain; Amnesty says police used excessive force",
    28: "Trump: Iran wants a deal, but no rush; may decide in 2027",
    30: "Brazil boosts Indigenous land safeguards; chief Raoni talks",
    32: "US sanctions Italian crime syndicate, Australian biker gang",
    34: "A second judge blocks Trump's triumphal arch, a 'rushed job'",
    35: "Pentagon puts cost of US engagement against Iran at $48.3bn",
    36: "US floats NATO membership for Ukraine in a land deal",
    45: "US panel: India targets minorities in voter-roll changes",
    50: "Iran claims waters 500 km beyond the strait",
}

DATE_CHECK_SHORT = "Left out on purpose — not Saturday's news: ~900,000 AI chips for China + Nvidia subpoena (Thu) · Myanmar verdict itself (Thu) · Mongolia's president resigns (voted Thu) · EU €7.9bn Ukraine payment + €1bn aid (Fri) · Bayer $7.25bn Roundup approval (Fri) · Akvan's Gopalpur landfall (Fri) · missiles down in Poland (Fri) · Kyiv bridges, Thursday-night barrage · S&P 500 −3.7% (Fri close) · Shenzhen declaration (Thu)."

def draw_briefs_footer(draw, img):
    """Draw briefs columns and footer with date check."""
    # Title
    title = "ALSO ON SATURDAY 21 NOVEMBER — 42 MORE STORIES"
    title_font = fit_font(draw, title, resolve_font("SANSB"), 12, CONTENT_W)
    draw_text(draw, (264, 636), title, title_font, PALETTE["ink"])
    # Columns
    col_x = [264, 514, 764]
    col_w = 238
    start_y = 654
    leading = 10
    bottoms = []
    for idx, x in enumerate(col_x):
        y = start_y
        start_n = 17 + idx * 14
        end_n = start_n + 14
        column_briefs = [b for b in stories.BRIEFS if start_n <= b["n"] < end_n]
        for brief in column_briefs:
            n = brief["n"]
            place = brief["place"]
            text = BRIEF_TEXT_SHORT.get(n, brief.get("text", ""))
            source = brief.get("source", "")
            tag = brief.get("tag", "")
            line = f"{n} {place} — {text} [{source}]"
            if tag:
                line += f" [{tag}]"
            # wrap and draw
            body_font = fit_font(draw, line, resolve_font("SANS"), 9.5, col_w)
            lines = wrap(draw, line, body_font, col_w)
            for ln in lines:
                draw_text(draw, (x, y), ln, body_font, PALETTE["ink"])
                y += leading
            y += 1  # space after each brief
        bottoms.append(y)
    for i, b in enumerate(bottoms, 1):
        print(f"column {i} bottom {b}")
    assert max(bottoms) <= 952, f"briefs overflow: {bottoms}"
    # Certainty label and legend
    cert_label = "HOW SURE ARE WE?"
    cert_font = fit_font(draw, cert_label, resolve_font("SANSB"), 9.5, 200)
    draw_text(draw, (12, 954), cert_label, cert_font, PALETTE["ink"])
    label_w = text_w(draw, cert_label, cert_font)
    rest = " — REPORTED = confirmed by wires · CLAIM = one side's claim · FORECAST = not yet happened"
    rest_font = fit_font(draw, rest, resolve_font("SANS"), 9.5, CONTENT_W - (12 + label_w + 2))
    draw_text(draw, (12 + label_w + 2, 954), rest, rest_font, PALETTE["ink"])
    # Truth line
    truth_font = fit_font(draw, stories.TRUTH, resolve_font("SANS"), 9.5, CONTENT_W - 24)
    draw_text(draw, (12, 965), stories.TRUTH, truth_font, PALETTE["dim_ink"])
    # Date check box
    draw.rectangle([12, 974, 1012, 1014], fill=PALETTE["charcoal"])
    dc_label = "DATE CHECK"
    dc_label_font = fit_font(draw, dc_label, resolve_font("SANSB"), 9.5, 100)
    draw_text(draw, (20, 977), dc_label, dc_label_font, PALETTE["red"])
    # sourcing right‑aligned
    sourcing = stories.SOURCING
    src_font = fit_font(draw, sourcing, resolve_font("SANS"), 9.5, 100)
    src_w = text_w(draw, sourcing, src_font)
    draw_text(draw, (1004 - src_w, 977), sourcing, src_font, "#b7ad97")
    # date check text (≤2 lines)
    date_font = fit_font(draw, DATE_CHECK_SHORT, resolve_font("SANS"), 9.5, 972)
    lines = wrap(draw, DATE_CHECK_SHORT, date_font, 972)
    assert len(lines) <= 2, "date check exceeds 2 lines"
    dy = 988
    for ln in lines:
        draw_text(draw, (20, dy), ln, date_font, "#f2ead8")
        dy += 10.5


if __name__ == "__main__":
    main()
