"""Hindi + English mila text sahi font mein likhna (Devanagari font mein A-Z nahi hote)."""
import glob
import re
from functools import lru_cache
from PIL import ImageFont

_DEV = re.compile(r"[\u0900-\u097F\uA8E0-\uA8FF\u200C\u200D]+")


def _find(pattern: str) -> str:
    hits = sorted(glob.glob(f"/usr/share/fonts/**/{pattern}", recursive=True))
    if not hits:
        raise FileNotFoundError(f"Font nahi mila: {pattern} (sudo apt install fonts-noto-core)")
    return hits[0]


@lru_cache(maxsize=None)
def fonts(size: int, bold: bool = True):
    w = "Bold" if bold else "Regular"
    dev = ImageFont.truetype(_find(f"NotoSansDevanagari-{w}.ttf"), size, layout_engine=ImageFont.Layout.RAQM)
    lat = ImageFont.truetype(_find(f"NotoSans-{w}.ttf"), size, layout_engine=ImageFont.Layout.RAQM)
    return dev, lat


def runs(text: str):
    """text ko (tukda, latin?) mein todo: Devanagari akshar ek font, baaki (A-Z, 0-9, chinh) doosra."""
    out, i = [], 0
    for m in _DEV.finditer(text):
        if m.start() > i:
            out.append((text[i:m.start()], True))
        out.append((m.group(), False))
        i = m.end()
    if i < len(text):
        out.append((text[i:], True))
    return out


def width(text: str, size: int, bold=True) -> float:
    dev, lat = fonts(size, bold)
    return sum((lat if is_lat else dev).getlength(t) for t, is_lat in runs(text))


def draw(d, xy, text: str, size: int, fill, bold=True, stroke=0, stroke_fill=None):
    dev, lat = fonts(size, bold)
    x, y = xy
    base = y + size * 1.05   # dono font ek hi baseline par
    for t, is_lat in runs(text):
        f = lat if is_lat else dev
        d.text((x, base), t, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill, anchor="ls")
        x += f.getlength(t)


def wrap(text: str, size: int, max_w: int, bold=True):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if width(trial, size, bold) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(text: str, max_w: int, max_h: int, start=96, smallest=44, gap=1.35, bold=True):
    """Sabse bada font size jismein text dabbe mein aa jaye."""
    size = start
    while size >= smallest:
        lines = wrap(text, size, max_w, bold)
        if len(lines) * size * gap <= max_h:
            return size, lines
        size -= 4
    return smallest, wrap(text, smallest, max_w, bold)
