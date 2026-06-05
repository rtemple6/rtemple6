#!/usr/bin/env python3
"""Generate banner.svg for the rtemple6 profile README.

Workshop palette (cream paper + terracotta), Fraunces + DM Mono outlined to
vector paths so it renders identically on any GitHub viewer with no font
dependency. The GitHub contribution grid is the environment (per Ryan's
DESIGN_SYSTEM.md), not a widget. Motion via SMIL (works in <img>-rendered SVG).
"""
import re, os, random, urllib.request
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.environ.get("STATIC") == "1"  # render resting state (for preview)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")

# ---- Workshop palette (from DESIGN_SYSTEM.md) -----------------------------
PAPER      = "#F2EBDA"
PAPER_LIFT = "#FBF6E9"
PAPER_DEEP = "#E6DBC0"
INK        = "#1B1611"
INK_SOFT   = "#3B342A"
MUTED      = "#7A6F5F"
RULE       = "#D8CBAC"
TERRACOTTA = "#B8472A"
OXBLOOD    = "#6B1F1A"
BRASS      = "#B8893A"
OLIVE      = "#5C6B4A"
# graph heatmap stops
G_NONE = "#EDE3CB"; G_LOW = "#D9B47A"; G_MID = "#C97A3E"; G_HIGH = "#8E2F18"; G_PEAK = "#4A0F0A"


def fetch_latin_woff2(css_path):
    css = open(css_path).read()
    # blocks look like: /* latin */ @font-face { ... src: url(...woff2) ... }
    blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", css, re.S)
    chosen = None
    for label, body in blocks:
        if label == "latin":
            chosen = body
            break
    if chosen is None and blocks:
        chosen = blocks[0][1]
    url = re.search(r"url\((https://[^)]+\.woff2)\)", chosen).group(1)
    dst = os.path.join(HERE, "fonts", os.path.basename(url))
    if not os.path.exists(dst):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req) as r, open(dst, "wb") as f:
            f.write(r.read())
    return dst


def load_instance(css_path, axes):
    path = fetch_latin_woff2(css_path)
    font = TTFont(path)
    if "fvar" in font:
        have = {a.axisTag for a in font["fvar"].axes}
        pin = {k: v for k, v in axes.items() if k in have}
        if pin:
            instantiateVariableFont(font, pin, inplace=True)
    return font


def outline(font, text, size_px, tracking_px=0.0):
    """Return (path_d, width_px). Coordinates in font units, NOT flipped."""
    upm = font["head"].unitsPerEm
    scale = size_px / upm
    cmap = font.getBestCmap()
    glyphset = font.getGlyphSet()
    hmtx = font["hmtx"]
    pen = SVGPathPen(glyphset)
    penx = 0.0
    track_units = tracking_px / scale
    for ch in text:
        cp = ord(ch)
        if cp not in cmap:
            penx += upm * 0.3 + track_units
            continue
        gname = cmap[cp]
        tpen = TransformPen(pen, (1, 0, 0, 1, penx, 0))
        glyphset[gname].draw(tpen)
        adv = hmtx[gname][0]
        penx += adv + track_units
    return pen.getCommands(), penx, scale, upm


def text_group(font, text, size_px, x, baseline_y, fill, tracking_px=0.0,
               gid=None, anim=None):
    d, penx, scale, upm = outline(font, text, size_px, tracking_px)
    width = penx * scale
    # inner: position + flip y (font up -> svg up). outer <g> carries entrance anim.
    inner = (f'<g transform="translate({x:.2f},{baseline_y:.2f}) '
             f'scale({scale:.5f},{-scale:.5f})">'
             f'<path d="{d}" fill="{fill}"/></g>')
    if anim is None or STATIC:
        return inner, width
    # entrance: fade + rise, freeze
    begin = anim["begin"]
    rise = anim.get("rise", 14)
    dur = anim.get("dur", 0.7)
    return (
        f'<g opacity="0">'
        f'<animate attributeName="opacity" from="0" to="1" begin="{begin}s" '
        f'dur="{dur}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="0 {rise}" to="0 0" begin="{begin}s" dur="{dur}s" '
        f'calcMode="spline" keySplines="0.16 1 0.3 1" fill="freeze"/>'
        f'{inner}</g>'
    ), width


def build():
    fr_head = load_instance("fonts/fraunces.css", {"opsz": 144, "wght": 600})
    fr_ital = load_instance("fonts/fraunces-italic.css", {"opsz": 60, "wght": 500})
    dm_mono = load_instance("fonts/dmmono.css", {})

    W, H = 1200, 380
    M = 74  # left margin
    rnd = random.Random(7842341)  # seeded with Ryan's GitHub user id -> deterministic

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="Ryan Temple — Software Engineer, Product Designer, Builder. Hoboken, NJ. Building things that connect people.">'
    )

    # ---- defs: film grain + soft vignette ---------------------------------
    parts.append(
        '<defs>'
        '<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" '
        'numOctaves="2" stitchTiles="stitch" result="n"/>'
        '<feColorMatrix in="n" type="saturate" values="0"/>'
        '<feComponentTransfer><feFuncA type="linear" slope="0.5"/></feComponentTransfer>'
        '</filter>'
        f'<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{PAPER}" stop-opacity="0"/>'
        f'<stop offset="0.62" stop-color="{PAPER}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{PAPER}" stop-opacity="0.55"/>'
        f'</linearGradient>'
        '</defs>'
    )

    # ---- paper base -------------------------------------------------------
    parts.append(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')

    # ---- contribution grid as the environment -----------------------------
    # base cells very faint; "active" cells warmer; density rises toward the
    # right so the headline (left) stays clean and the grid reads as a field.
    pitch = 21; cell = 15; r = 3
    cols = W // pitch + 1
    rows = H // pitch + 1
    x0 = (W - cols * pitch) / 2 + (pitch - cell) / 2
    y0 = (H - rows * pitch) / 2 + (pitch - cell) / 2
    grid = ['<g>']
    embers = []  # (cx, cy) of peak cells to pulse
    for c in range(cols):
        # horizontal activity ramp: sparse at left, denser at right
        ramp = c / (cols - 1)
        for rr in range(rows):
            cx = x0 + c * pitch
            cy = y0 + rr * pitch
            rv = rnd.random()
            p = 0.10 + 0.55 * ramp  # probability a cell is "active"
            if rv < p:
                t = rnd.random()
                if t < 0.46:   col, op = G_LOW, 0.9
                elif t < 0.74: col, op = G_MID, 0.92
                elif t < 0.92: col, op = G_HIGH, 0.9
                else:          col, op = G_PEAK, 0.9
            else:
                col, op = PAPER_DEEP, 0.7
            grid.append(
                f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell}" height="{cell}" '
                f'rx="{r}" fill="{col}" opacity="{op:.2f}"/>'
            )
            if col == G_PEAK and rnd.random() < 0.5 and len(embers) < 9:
                embers.append((cx, cy))
    grid.append('</g>')
    # grid sits at low overall opacity so text reads cleanly over it
    parts.append(f'<g opacity="0.42">{"".join(grid)}</g>')

    # gentle ember pulse on a few peak cells (forge-like, very subtle)
    for i, (cx, cy) in enumerate(embers):
        b = round(0.4 * i, 2)
        parts.append(
            f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell}" height="{cell}" rx="{r}" '
            f'fill="{TERRACOTTA}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0.5;0" dur="3.6s" '
            f'begin="{b}s" repeatCount="indefinite" calcMode="spline" '
            f'keyTimes="0;0.5;1" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>'
            f'</rect>'
        )

    # right-edge fade so dense cells don't fight the eye
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#fade)"/>')

    # ---- type -------------------------------------------------------------
    # kicker (DM Mono, tracked, muted)
    kick, _ = text_group(dm_mono, "SOFTWARE ENGINEER  ·  PRODUCT DESIGNER  ·  BUILDER",
                         18, M, 92, MUTED, tracking_px=1.5,
                         anim={"begin": 0.05, "rise": 10, "dur": 0.6})
    parts.append(kick)

    # headline (Fraunces 600)
    head, head_w = text_group(fr_head, "Ryan Temple", 118, M, 218, INK,
                              anim={"begin": 0.18, "rise": 16})
    parts.append(head)

    # hairline rule drawing in under the name, terracotta
    rule_x1, rule_x2, rule_y = M + 3, M + 3 + min(head_w, 560), 250
    rule_len = rule_x2 - rule_x1
    if STATIC:
        parts.append(
            f'<line x1="{rule_x1:.1f}" y1="{rule_y}" x2="{rule_x2:.1f}" y2="{rule_y}" '
            f'stroke="{TERRACOTTA}" stroke-width="2.5" stroke-linecap="round"/>'
        )
    else:
        parts.append(
            f'<line x1="{rule_x1:.1f}" y1="{rule_y}" x2="{rule_x2:.1f}" y2="{rule_y}" '
            f'stroke="{TERRACOTTA}" stroke-width="2.5" stroke-linecap="round" '
            f'stroke-dasharray="{rule_len:.1f}" stroke-dashoffset="{rule_len:.1f}">'
            f'<animate attributeName="stroke-dashoffset" from="{rule_len:.1f}" to="0" '
            f'begin="0.5s" dur="0.9s" calcMode="spline" '
            f'keySplines="0.16 1 0.3 1" fill="freeze"/>'
            f'</line>'
        )

    # italic voice line (Fraunces italic 500, terracotta)
    ital, _ = text_group(fr_ital, "building things that connect people", 40, M, 312,
                         TERRACOTTA, anim={"begin": 0.62, "rise": 14})
    parts.append(ital)

    # bottom-right editorial corner mark (DM Mono, muted)
    mark, mark_w, scale, upm = outline(dm_mono, "HOBOKEN, NJ — EST. 2013", 14, tracking_px=1.2)
    mw = mark_w * scale
    mx = W - 74 - mw
    inner_mark = (f'<g transform="translate({mx:.2f},{H-40}) scale({scale:.5f},{-scale:.5f})">'
                  f'<path d="{mark}" fill="{MUTED}"/></g>')
    if STATIC:
        parts.append(f'<g opacity="0.85">{inner_mark}</g>')
    else:
        parts.append(
            f'<g opacity="0">'
            f'<animate attributeName="opacity" from="0" to="0.85" begin="1.0s" dur="0.7s" fill="freeze"/>'
            f'{inner_mark}</g>'
        )

    # ---- film grain overlay ----------------------------------------------
    parts.append(
        f'<rect width="{W}" height="{H}" filter="url(#grain)" '
        f'opacity="0.05"/>'
    )
    # top + bottom hairline frame (editorial)
    parts.append(f'<rect x="0.75" y="0.75" width="{W-1.5}" height="{H-1.5}" '
                 f'fill="none" stroke="{RULE}" stroke-width="1.5"/>')

    parts.append('</svg>')
    svg = "".join(parts)
    out = os.path.join(HERE, "banner.svg")
    open(out, "w").write(svg)
    print("wrote", out, "bytes:", len(svg))


if __name__ == "__main__":
    build()
