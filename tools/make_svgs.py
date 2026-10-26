"""Render profile README banners as SVG with text converted to paths (portfolio fonts + colours).

Usage: python3 tools/make_svgs.py <fonts-dir> assets
fonts-dir needs Archivo%5Bwdth,wght%5D.ttf, Archivo-Italic%5Bwdth,wght%5D.ttf and GeistMono%5Bwght%5D.ttf
from github.com/google/fonts (ofl/archivo, ofl/geistmono). Requires fontTools."""
import sys, os
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

FONTS, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

# dark = the portfolio's .dk palette; light = its footer palette, transparent so it sits on GitHub's white page
THEMES = {
    "dark": dict(BG="#111010", TEXT="#edeae4", MUTED="#b9b4ac", LABEL="#8f8a82", HAIR="#edeae41f", ACCENT="#7fa8ff", G=56),
    "light": dict(BG=None, TEXT="#0c0c0c", MUTED="#6f6f6c", LABEL="#9c9c98", HAIR="#0c0c0c1f", ACCENT="#2f63d8", G=2),
}

_cache = {}
def font(file, **axes):
    key = (file, tuple(sorted(axes.items())))
    if key not in _cache:
        f = TTFont(os.path.join(FONTS, file))
        _cache[key] = instantiateVariableFont(f, axes)
    return _cache[key]

DISPLAY = lambda: font("Archivo%5Bwdth,wght%5D.ttf", wdth=70, wght=800)
ROW = lambda: font("Archivo%5Bwdth,wght%5D.ttf", wdth=88, wght=600)
ITALIC = lambda: font("Archivo-Italic%5Bwdth,wght%5D.ttf", wdth=115, wght=250)
MONO = lambda: font("GeistMono%5Bwght%5D.ttf", wght=400)

def text(f, s, x, y, size, fill, tracking=0.0):
    """Return (svg <path>, advance width in px). tracking is in em."""
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
    upm = f["head"].unitsPerEm
    k = size / upm
    pen = SVGPathPen(gs)
    cx = 0.0
    for ch in s:
        g = cmap.get(ord(ch))
        if g is None:
            cx += size * (0.09 if ch == "\u2009" else 0.3); continue
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x + cx, y)))
        cx += hmtx[g][0] * k + tracking * size
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>', cx

def width(f, s, size, tracking=0.0):
    return text(f, s, 0, 0, size, "#000", tracking)[1]

def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{title}">'
            f'<title>{title}</title>'
            + (f'<rect width="{w}" height="{h}" rx="14" fill="{BG}"/>'
               f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="none" stroke="{HAIR}"/>' if BG else "")
            + f'{body}</svg>')

W = 1200

def header():
    h = 440
    parts = []
    p, _ = text(MONO(), "PRABHAT ACHARYA / PORTFOLIO", G, 66, 15, LABEL); parts.append(p)
    r = "KATHMANDU, NP / UTC+5:45"
    p, _ = text(MONO(), r, W - G - width(MONO(), r, 15), 66, 15, LABEL); parts.append(p)
    parts.append(f'<line x1="{G}" y1="92" x2="{W-G}" y2="92" stroke="{HAIR}"/>')
    # fit "PRABHAT — Acharya" to the gutter width
    gap = 0.04
    unit = width(DISPLAY(), "PRABHAT\u2009\u2009—\u2009\u2009", 100, -0.02) + width(ITALIC(), "Acharya", 100, -0.03) + gap * 100
    size = min(200, 100 * (W - 2 * G) / unit)
    base = 225 + size * 0.36
    p, w1 = text(DISPLAY(), "PRABHAT\u2009\u2009—\u2009\u2009", G - 4, base, size, TEXT, -0.02); parts.append(p)
    p, _ = text(ITALIC(), "Acharya", G - 4 + w1 + gap * size, base, size, ACCENT, -0.03); parts.append(p)
    parts.append(f'<line x1="{G}" y1="356" x2="{W-G}" y2="356" stroke="{HAIR}"/>')
    p, _ = text(MONO(), "FULL STACK · DATABASES · AI/ML", G, 394, 15, MUTED); parts.append(p)
    r = "PRABHATACHARYA.VERCEL.APP"
    p, _ = text(MONO(), r, W - G - width(MONO(), r, 15), 394, 15, MUTED); parts.append(p)
    return svg(W, h, "".join(parts), "Prabhat Acharya — Full stack, databases, AI/ML. Kathmandu, Nepal.")

def section(num, label, plain, italic, name):
    h = 170
    parts = []
    p, wn = text(MONO(), f"({num})", G, 52, 15, LABEL); parts.append(p)
    p, _ = text(MONO(), label.upper(), G + wn + 14, 52, 15, TEXT); parts.append(p)
    size = 84
    p, w1 = text(DISPLAY(), plain.upper(), G - 3, 140, size, TEXT, -0.02); parts.append(p)
    p, _ = text(ITALIC(), italic, G - 3 + w1 + (16 if plain else 0), 140, size, ACCENT, -0.03); parts.append(p)
    open(os.path.join(OUT, f"{name}-{THEME}.svg"), "w").write(svg(W, h, "".join(parts), f"{plain} {italic}".strip()))

for THEME, colours in THEMES.items():
    globals().update(colours)
    open(os.path.join(OUT, f"header-{THEME}.svg"), "w").write(header())
    section("01", "Selected work", "Selected", "work", "work")
    section("02", "Toolkit", "The", "toolkit", "toolkit")
    section("03", "Contact / say hello", "Let's", "talk!", "contact")
print("ok")
