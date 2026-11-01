"""Render the profile README banners as SVG, in the portfolio's "Latent Space" style.

Text is converted to paths, so GitHub shows the real fonts. The header's point field is the same real data as the
portfolio hero: 8,790 Netflix titles laid out with TF-IDF -> SVD -> t-SNE (netflix-tsne.bin from the portfolio repo).

Usage: python3 tools/make_svgs.py <fonts-dir> <netflix-tsne.bin> assets
fonts-dir needs Geist[wght].ttf, GeistMono[wght].ttf, Newsreader[opsz,wght].ttf and Newsreader-Italic[opsz,wght].ttf
(URL-encoded file names as downloaded from github.com/google/fonts). Requires fontTools and numpy.
"""
import os
import struct
import sys

import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONTS, FIELD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

# the portfolio's tokens; the light theme is transparent so it sits on GitHub's own page colour
THEMES = {
    "dark": dict(BG="#0d0e0d", TEXT="#e8e4da", MUTED="#b3aea3", LABEL="#8a867d", HAIR="#e8e4da1c", ACCENT="#9fbf98", DOT="#cfcabd", G=56, BOOST=1.35),
    "light": dict(BG=None, TEXT="#121311", MUTED="#46463f", LABEL="#67665e", HAIR="#1213111c", ACCENT="#3f6b45", DOT="#1b1c1a", G=8, BOOST=1.0),
}
MOTTO = ("DATA IS OMNIPOTENT.", "DATA IS OMNIPRESENT.")  # immutable

_cache = {}


def font(file, **axes):
    key = (file, tuple(sorted(axes.items())))
    if key not in _cache:
        _cache[key] = instantiateVariableFont(TTFont(os.path.join(FONTS, file)), axes)
    return _cache[key]


SANS = lambda: font("Geist%5Bwght%5D.ttf", wght=500)
MONO = lambda: font("GeistMono%5Bwght%5D.ttf", wght=400)
SERIF = lambda: font("Newsreader%5Bopsz,wght%5D.ttf", opsz=72, wght=400)
ITALIC = lambda: font("Newsreader-Italic%5Bopsz,wght%5D.ttf", opsz=72, wght=400)


def text(f, s, x, y, size, fill, tracking=0.0):
    """(svg <path>, advance in px); tracking in em."""
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
    k = size / f["head"].unitsPerEm
    pen = SVGPathPen(gs)
    cx = 0.0
    for ch in s:
        g = cmap.get(ord(ch))
        if g is None:
            cx += size * 0.3
            continue
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x + cx, y)))
        cx += hmtx[g][0] * k + tracking * size
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>', cx


def width(f, s, size, tracking=0.0):
    return text(f, s, 0, 0, size, "#000", tracking)[1]


def svg(w, h, body, title):
    frame = (
        f'<rect width="{w}" height="{h}" rx="14" fill="{BG}"/>'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="none" stroke="{HAIR}"/>'
        if BG else ""
    )
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{frame}{body}</svg>')


def load_field(path, keep=2600):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[:4])[0]
    f32 = len(b) >= 4 + n * 13
    pos = (np.frombuffer(b, "<f4", n * 3, 4) if f32 else np.frombuffer(b, "<i2", n * 3, 4) / 20000).reshape(n, 3)
    kind = np.frombuffer(b, "u1", n, 4 + n * 3 * (4 if f32 else 2))
    idx = np.linspace(0, n - 1, keep).astype(int)
    return pos[idx], kind[idx], n


POS, KIND, N = load_field(FIELD)

W = 1200


def field(cx, cy, scale):
    """The t-SNE layout, turned like the site's hero, drawn back to front with depth-of-field sizing."""
    a, b = 0.18, 0.5
    x, y, z = POS[:, 0], POS[:, 1], POS[:, 2]
    x1 = x * np.cos(b) + z * np.sin(b)
    z1 = -x * np.sin(b) + z * np.cos(b)
    y2 = y * np.cos(a) - z1 * np.sin(a)
    z2 = y * np.sin(a) + z1 * np.cos(a)
    order = np.argsort(z2)
    out = []
    for i in order:
        depth = (z2[i] + 1.2) / 2.4  # 0 far, 1 near
        blur = abs(depth - 0.5) * 2
        r = 1.1 + blur * 1.3
        op = min(1.0, (0.75 - blur * 0.45) * (0.55 + depth * 0.45) * BOOST)
        fill = ACCENT if KIND[i] else DOT
        out.append(f'<circle cx="{cx + x1[i] * scale:.1f}" cy="{cy - y2[i] * scale:.1f}" r="{r:.1f}" fill="{fill}" fill-opacity="{op:.2f}"/>')
    return "".join(out)


def header():
    h = 560
    parts = [field(W * 0.62, 230, 210)]
    p, _ = text(MONO(), "PRABHAT ACHARYA / PORTFOLIO", G, 62, 14, LABEL); parts.append(p)
    r = "KATHMANDU, NP"
    p, _ = text(MONO(), r, W - G - width(MONO(), r, 14), 62, 14, LABEL); parts.append(p)
    p, _ = text(SERIF(), "Prabhat Acharya", G, 140, 54, TEXT, -0.01); parts.append(p)
    for i, line in enumerate(("Full-stack Developer", "Databases & Data", "AI · ML · RAG")):
        p, _ = text(MONO(), line, G, 178 + i * 22, 14, MUTED); parts.append(p)
    # the motto, fitted to the gutter width
    size = min(104, 100 * (W - 2 * G) / width(SANS(), MOTTO[1], 100, -0.055))
    for i, line in enumerate(MOTTO):
        p, _ = text(SANS(), line, G - 3, 390 + i * size * 0.92, size, TEXT, -0.055); parts.append(p)
    parts.append(f'<line x1="{G}" y1="{h - 62}" x2="{W - G}" y2="{h - 62}" stroke="{HAIR}"/>')
    p, wf = text(MONO(), "FIG. 01", G, h - 30, 12, TEXT); parts.append(p)
    cap = f" — {N:,} NETFLIX TITLES, ONE POINT EACH · TF-IDF → SVD → t-SNE"
    p, _ = text(MONO(), cap, G + wf, h - 30, 12, LABEL); parts.append(p)
    r = "PRABHATACHARYA.VERCEL.APP"
    p, _ = text(MONO(), r, W - G - width(MONO(), r, 12), h - 30, 12, MUTED); parts.append(p)
    return svg(W, h, "".join(parts), "Prabhat Acharya. DATA IS OMNIPOTENT. DATA IS OMNIPRESENT.")


def section(num, label, plain, italic, name):
    h = 150
    parts = []
    p, wn = text(MONO(), f"({num})", G, 46, 14, LABEL); parts.append(p)
    p, _ = text(MONO(), label.upper(), G + wn + 12, 46, 14, TEXT); parts.append(p)
    size = 72
    p, w1 = text(SERIF(), plain, G - 2, 120, size, TEXT, -0.01); parts.append(p)
    p, _ = text(ITALIC(), italic, G - 2 + w1 + (size * 0.22 if plain else 0), 120, size, ACCENT, -0.01); parts.append(p)
    open(os.path.join(OUT, f"{name}-{THEME}.svg"), "w").write(svg(W, h, "".join(parts), f"{plain} {italic}".strip()))


for THEME, colours in THEMES.items():
    globals().update(colours)
    open(os.path.join(OUT, f"header-{THEME}.svg"), "w").write(header())
    section("01", "Selected work", "Selected", "work.", "work")
    section("02", "Toolkit", "The", "toolkit.", "toolkit")
    section("03", "Contact / say hello", "Let's", "talk.", "contact")
print("ok")
