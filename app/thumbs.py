"""Attractive thumbnails (1280x720). Har video alag: title ke mood se rang + emoji, 6 layout, roz badalte.
Script mein (sab optional):
  "thumb": {"lines": ["0% EMI का", "*छुपा ख़र्च!*"], "emoji": "😱", "tag": "सावधान!", "badge": "₹4,200", "mood": "warning"}
*shabd* = rangeen patti wala highlight."""
import datetime
import glob
import json
import hashlib
import math
import pathlib
import random
import re
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from .config import BRANDS

TW, TH = 1280, 720
ASSETS = pathlib.Path(__file__).parent / "assets"
WHITE, BLACK = (255, 255, 255), (0, 0, 0)

# rang: (bg1, bg2, highlight patti, highlight akshar, mukhya akshar, outline, accent)
PALETTES = {
    "red":     ("#7a0000", "#d90f1f", "#ffd600", "#000000", "#ffffff", "#000000", "#ffd600"),
    "fire":    ("#1a0000", "#5c0000", "#ff2a2a", "#ffffff", "#ffe600", "#000000", "#ff2a2a"),
    "gold":    ("#003d1f", "#00813d", "#ffd600", "#000000", "#ffffff", "#000000", "#ffd600"),
    "money":   ("#ffc400", "#ffe45c", "#0a7a35", "#ffffff", "#111111", "#ffffff", "#0a7a35"),
    "blue":    ("#00205c", "#0059d6", "#00e5ff", "#001a33", "#ffffff", "#000000", "#00e5ff"),
    "purple":  ("#24004d", "#6a00c2", "#ffd600", "#000000", "#ffffff", "#000000", "#ff3d8b"),
    "pink":    ("#5c0033", "#e6007a", "#ffffff", "#c2005f", "#ffee00", "#000000", "#ffee00"),
    "orange":  ("#7a2900", "#ff6a00", "#ffffff", "#c43d00", "#ffffff", "#000000", "#fff200"),
    "teal":    ("#00332e", "#00897b", "#ffd600", "#000000", "#ffffff", "#000000", "#a6ffcb"),
    "night":   ("#0b0b12", "#26263a", "#ff2a2a", "#ffffff", "#ffffff", "#000000", "#ffd600"),
    "sky":     ("#0a4f8f", "#3fa9f5", "#ff3b30", "#ffffff", "#ffffff", "#002244", "#ffe600"),
}
MOODS = {
    "warning": (["red", "fire", "night", "orange"], ["😱", "🚨", "⚠️", "😨", "🤯"]),
    "money":   (["gold", "money", "teal", "purple"], ["🤑", "💰", "💸", "🪙", "😎"]),
    "tips":    (["blue", "sky", "purple", "teal"], ["💡", "🧠", "✅", "😃", "🔥"]),
    "story":   (["purple", "orange", "night", "pink"], ["😲", "😢", "😳", "🙄", "😮"]),
    "question": (["pink", "purple", "blue", "orange"], ["🤔", "❓", "🧐", "😯", "🙋"]),
    "pahadi":  (["teal", "sky", "gold", "blue"], ["🏔️", "🌾", "🏡", "😊", "📏"]),
    "happy":   (["orange", "pink", "money", "sky"], ["🥳", "😍", "🎉", "😄", "🤩"]),
}
KEYS = [("warning", "सावधान छुपा धोखा जाल गलती ग़लती नुकसान फँस फंस खतरा ख़तरा सच scam"),
        ("money", "बचत कमाई कमाएं लाभ फायदा फ़ायदा पैसा पैसे ₹ sip fd ppf ब्याज rich"),
        ("pahadi", "पहाड़ पहाड़ी नाली मुट्ठी बीघा जमीन ज़मीन खेती उत्तराखंड"),
        ("tips", "कैसे तरीका तरीके ट्रिक trick tips आसान सीखें"),
        ("question", "? क्या कौन क्यों कितना"),
        ("story", "कहानी किस्सा story"),
        ("happy", "ऑफर offer deal सेल sale मुफ्त फ्री free")]


@lru_cache(maxsize=None)
def baloo(size, weight="ExtraBold"):
    f = ImageFont.truetype(str(ASSETS / "Baloo2.ttf"), size, layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_name(weight)
    return f


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def detect_mood(text):
    t = text.lower()
    for mood, words in KEYS:
        if any(w.lower() in t for w in words.split()):
            return mood
    return "story"


def emoji_img(ch, size):
    hits = glob.glob("/usr/share/fonts/**/NotoColorEmoji.ttf", recursive=True)
    if not hits or not ch:
        return None
    f = ImageFont.truetype(hits[0], 109)
    im = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((90, 90), ch, font=f, embedded_color=True, anchor="mm")
    bbox = im.getbbox()
    if not bbox:
        return None
    im = im.crop(bbox)
    k = size / max(im.size)
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=2))


# ---------- background ----------
def bg_burst(c1, c2, cx, cy, rays=18):
    img = Image.new("RGB", (TW, TH), _hex(c1))
    d = ImageDraw.Draw(img)
    R = 1700
    for i in range(rays):
        a1 = 2 * math.pi * i / rays
        a2 = a1 + math.pi / rays
        d.polygon([(cx, cy), (cx + R * math.cos(a1), cy + R * math.sin(a1)),
                   (cx + R * math.cos(a2), cy + R * math.sin(a2))], fill=_hex(c2))
    return _vignette(img)


def bg_gradient(c1, c2, diag=True):
    a, b = _hex(c1), _hex(c2)
    g = Image.linear_gradient("L").resize((TW, TH))
    if diag:
        g = g.rotate(-35, expand=False, fillcolor=128).resize((TW, TH))
    img = Image.composite(Image.new("RGB", (TW, TH), b), Image.new("RGB", (TW, TH), a), g)
    return _vignette(img, 0.35)


def _vignette(img, strength=0.55):
    m = Image.new("L", (TW, TH), 0)
    ImageDraw.Draw(m).ellipse([-320, -260, TW + 320, TH + 260], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(130))
    dark = Image.blend(img, Image.new("RGB", (TW, TH), BLACK), strength)
    return Image.composite(img, dark, m)


# ---------- elements ----------
def _glow(base, im, xy, color=WHITE, radius=18):
    a = im.split()[-1]
    g = Image.new("RGBA", im.size, color + (0,))
    g.putalpha(a)
    pad = radius * 3
    big = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    big.paste(g, (pad, pad), g)
    big = big.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(radius))
    base.alpha_composite(big, (xy[0] - pad, xy[1] - pad))
    base.alpha_composite(im, xy)


def _shadow_text(base, xy, text, font, fill, stroke, stroke_fill, anchor="ls"):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0] + 8, xy[1] + 10), text, font=font, fill=(0, 0, 0, 170), anchor=anchor,
                             stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(base).text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=stroke,
                              stroke_fill=stroke_fill)


def _arrow(d, start, end, color, width=28):
    (x1, y1), (x2, y2) = start, end
    ang = math.atan2(y2 - y1, x2 - x1)
    L = width * 2.5
    bx, by = x2 - L * 0.8 * math.cos(ang), y2 - L * 0.8 * math.sin(ang)
    d.line([start, (bx, by)], fill=color, width=width)
    p2 = (x2 - L * math.cos(ang - 0.6), y2 - L * math.sin(ang - 0.6))
    p3 = (x2 - L * math.cos(ang + 0.6), y2 - L * math.sin(ang + 0.6))
    d.polygon([(x2, y2), p2, p3], fill=color)


def _starburst(base, center, r, color, text, rot=-12):
    r = int(r * 1.3)
    s = int(r * 2.6)
    st = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    pts = []
    for i in range(32):
        rr = r if i % 2 == 0 else r * 0.8
        a = math.pi * i / 16
        pts.append((s / 2 + rr * math.cos(a), s / 2 + rr * math.sin(a)))
    d.polygon(pts, fill=color, outline=WHITE, width=6)
    size = int(r * 0.62)
    f = baloo(size)
    while f.getlength(text) > r * 1.45 and size > 30:
        size -= 4
        f = baloo(size)
    d.text((s / 2, s / 2), text, font=f, fill=WHITE, anchor="mm", stroke_width=4, stroke_fill=BLACK)
    st = st.rotate(rot, resample=Image.BICUBIC)
    base.alpha_composite(st, (int(center[0] - s / 2), int(center[1] - s / 2)))


def _parse(line):
    return [(p.strip("*").strip(), p.startswith("*")) for p in re.split(r"(\*[^*]+\*)", line) if p.strip()]


def _text_block(base, lines, x, y, max_w, size, P, align="left", line_colors=None):
    """Bade bold akshar; *highlight* rangeen patti par; har line alag rang ho sakti hai."""
    d = ImageDraw.Draw(base)
    for li, line in enumerate(lines):
        parts = _parse(line)
        s = size
        while s > 64:
            f = baloo(s)
            if sum(f.getlength(t + " ") for t, _ in parts) <= max_w:
                break
            s -= 6
        f = baloo(s)
        total = sum(f.getlength(t) for t, _ in parts) + f.getlength(" ") * (len(parts) - 1)
        cx = x + (max_w - total) / 2 if align == "center" else x
        for t, hl in parts:
            tw = f.getlength(t)
            base_y = y + s * 0.95
            if hl:
                pad = s * 0.18
                d.rounded_rectangle([cx - pad, y + s * 0.1, cx + tw + pad, y + s * 1.12], radius=int(s * 0.2),
                                    fill=_hex(P[2]), outline=BLACK, width=5)
                d.text((cx, base_y), t, font=f, fill=_hex(P[3]), anchor="ls")
            else:
                col = _hex(line_colors[li % len(line_colors)]) if line_colors else _hex(P[4])
                _shadow_text(base, (cx, base_y), t, f, col, max(7, s // 13), _hex(P[5]))
            cx += tw + f.getlength(" ") + (s * 0.3 if hl else 0)
            d = ImageDraw.Draw(base)
        y += s * 1.16
    return y


def _tag(d, text, xy, bg, fg):
    f = baloo(46)
    x, y = xy
    w = f.getlength(text)
    d.rounded_rectangle([x, y, x + w + 46, y + 74], radius=37, fill=bg, outline=BLACK, width=4)
    d.text((x + 23, y + 59), text, font=f, fill=fg, anchor="ls")


def _badge(d, name, bg, fg=(15, 15, 15)):
    f = baloo(38, "Bold")
    w = f.getlength(name)
    d.rounded_rectangle([40, TH - 92, 40 + w + 44, TH - 30], radius=31, fill=bg, outline=BLACK, width=3)
    d.text((62, TH - 45), name, font=f, fill=fg, anchor="ls")


# ---------- 6 layout ----------
def L_burst_right(P, t, brand, rnd):
    img = bg_burst(P[0], P[1], 1000, 360).convert("RGBA")
    e = emoji_img(t["emoji"], 410)
    if e:
        _glow(img, e, (TW - e.width - 40, (TH - e.height) // 2 + 20))
    d = ImageDraw.Draw(img)
    if t.get("tag"):
        _tag(d, t["tag"], (50, 38), _hex(P[6]), BLACK)
    yb = _text_block(img, t["lines"], 60, 135, 760, 150, P)
    d = ImageDraw.Draw(img)
    _arrow(d, (640, min(yb + 30, 640)), (860, 520), _hex(P[6]))
    if t.get("badge"):
        _starburst(img, (380, 590), 95, (230, 20, 30), t["badge"])
    _badge(ImageDraw.Draw(img), brand["name"], _hex(P[6]))
    return img


def L_band_ring(P, t, brand, rnd):
    img = bg_gradient(P[0], P[1]).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.polygon([(0, 480), (TW, 300), (TW, 440), (0, 615)], fill=_hex(P[2]))
    cx, cy, r = 990, 330, 255
    d.ellipse([cx - r - 16, cy - r - 16, cx + r + 16, cy + r + 16], fill=_hex(P[6]))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(25, 25, 32))
    e = emoji_img(t["emoji"], 370)
    if e:
        img.alpha_composite(e, (cx - e.width // 2, cy - e.height // 2))
    d = ImageDraw.Draw(img)
    if t.get("tag"):
        _tag(d, t["tag"], (50, 38), (230, 20, 30), WHITE)
    _text_block(img, t["lines"], 60, 130, 700, 150, P)
    if t.get("badge"):
        _starburst(img, (1130, 600), 90, (230, 20, 30), t["badge"])
    _badge(ImageDraw.Draw(img), brand["name"], _hex(P[6]))
    return img


def L_split(P, t, brand, rnd):
    img = Image.new("RGBA", (TW, TH), _hex(P[1]) + (255,))
    d = ImageDraw.Draw(img)
    d.polygon([(0, 0), (820, 0), (660, TH), (0, TH)], fill=_hex(P[0]))
    d.line([(820, 0), (660, TH)], fill=_hex(P[6]), width=18)
    for i in range(6):
        rr = 120 + i * 70
        d.ellipse([1010 - rr, 380 - rr, 1010 + rr, 380 + rr], outline=WHITE + (40,), width=6)
    e = emoji_img(t["emoji"], 400)
    if e:
        _glow(img, e, (1010 - e.width // 2, 380 - e.height // 2), _hex(P[6]), 20)
    if t.get("tag"):
        _tag(ImageDraw.Draw(img), t["tag"], (40, 36), _hex(P[6]), BLACK)
    _text_block(img, t["lines"], 45, 130, 640, 140, P)
    if t.get("badge"):
        _starburst(img, (760, 150), 92, (230, 20, 30), t["badge"], 10)
    _badge(ImageDraw.Draw(img), brand["name"], _hex(P[6]))
    return img


def L_center_top(P, t, brand, rnd):
    img = bg_burst(P[1], P[0], TW // 2, 900, 22).convert("RGBA")
    e = emoji_img(t["emoji"], 330)
    if e:
        _glow(img, e, (TW - e.width - 70, TH - e.height - 40), WHITE, 16)
    _text_block(img, t["lines"], 40, 40, TW - 80, 160, P, align="center",
                line_colors=[P[4], P[6]])
    if t.get("badge"):
        _starburst(img, (TW // 2 - 80, 575), 100, (230, 20, 30), t["badge"])
    _badge(ImageDraw.Draw(img), brand["name"], _hex(P[6]))
    return img


def L_frame_stack(P, t, brand, rnd):
    img = bg_gradient(P[1], P[0], diag=False).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TW - 1, TH - 1], outline=_hex(P[6]), width=26)
    d.rectangle([26, 26, TW - 27, TH - 27], outline=BLACK, width=6)
    e = emoji_img(t["emoji"], 380)
    if e:
        _glow(img, e.rotate(-10, expand=True), (40, 150), WHITE, 18)
    d = ImageDraw.Draw(img)
    if t.get("tag"):
        _tag(d, t["tag"], (TW - 60 - baloo(46).getlength(t["tag"]) - 46, 50), (230, 20, 30), WHITE)
    _text_block(img, t["lines"], 470, 150, 760, 150, P, line_colors=[P[6], P[4], P[2]])
    if t.get("badge"):
        _starburst(img, (1080, 600), 90, (230, 20, 30), t["badge"])
    _badge(ImageDraw.Draw(img), brand["name"], _hex(P[6]))
    return img


def L_spotlight(P, t, brand, rnd):
    img = Image.new("RGB", (TW, TH), _hex(P[0]))
    spot = Image.new("L", (TW, TH), 0)
    ImageDraw.Draw(spot).ellipse([620, -120, 1400, 820], fill=255)
    spot = spot.filter(ImageFilter.GaussianBlur(90))
    img = Image.composite(Image.new("RGB", (TW, TH), _hex(P[1])), img, spot).convert("RGBA")
    d = ImageDraw.Draw(img)
    for i in range(0, TW + TH, 46):
        d.line([(i, 0), (i - TH, TH)], fill=WHITE + (14,), width=3)
    e = emoji_img(t["emoji"], 440)
    if e:
        _glow(img, e, (TW - e.width - 60, (TH - e.height) // 2), _hex(P[6]), 24)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 24, TH], fill=_hex(P[6]))
    if t.get("tag"):
        _tag(d, t["tag"], (60, 38), WHITE, BLACK)
    yb = _text_block(img, t["lines"], 70, 140, 700, 155, P)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([70, min(yb + 10, 600), 470, min(yb + 26, 616)], radius=8, fill=_hex(P[6]))
    if t.get("badge"):
        _starburst(img, (600, 600), 88, (230, 20, 30), t["badge"])
    _badge(ImageDraw.Draw(img), brand["name"], _hex(P[6]))
    return img


LAYOUTS = [L_burst_right, L_band_ring, L_split, L_center_top, L_frame_stack, L_spotlight]


def make(brand_key, thumb, out_dir, title=""):
    """3 alag thumbnail: alag layout + alag rang + alag emoji. Har din/har title par badalte hain."""
    brand = BRANDS[brand_key]
    t = dict(thumb)
    t["lines"] = t.get("lines") or [t.get("text") or title]
    text_all = " ".join(t["lines"]) + " " + title
    mood = t.get("mood") or ("pahadi" if brand_key == "pahadi" and detect_mood(text_all) == "story"
                             else detect_mood(text_all))
    pals, emojis = MOODS.get(mood, MOODS["story"])
    seed = hashlib.md5((text_all + str(datetime.date.today())).encode()).hexdigest()
    rnd = random.Random(seed)
    from . import learn
    by_name = {f.__name__: f for f in LAYOUTS}
    layouts = [by_name[n] for n in learn.pick("layout", by_name, 3, rnd)]
    pal_names = learn.pick("palette", pals, 3, rnd)
    emo_list = [t["emoji"]] if t.get("emoji") else []
    emo_list += [e for e in rnd.sample(emojis, len(emojis)) if e not in emo_list]
    paths, variants = [], []
    for i, (lay, pn) in enumerate(zip(layouts, pal_names), 1):
        ti = dict(t, emoji=emo_list[(i - 1) % len(emo_list)])
        img = lay(PALETTES[pn], ti, brand, rnd)
        p = pathlib.Path(out_dir) / f"thumb_{i}.jpg"
        img.convert("RGB").save(p, "JPEG", quality=93)
        paths.append(p)
        variants.append({"palette": pn, "layout": lay.__name__, "emoji": ti["emoji"], "mood": mood})
    (pathlib.Path(out_dir) / "thumbs.json").write_text(json.dumps(variants, ensure_ascii=False))
    return paths


def vertical_cover(brand_key, thumb, variant, out_png):
    """Chune hue thumbnail ka hi rang/emoji/text, 1080x1920 (Shorts cover) mein."""
    global TW, TH
    old = (TW, TH)
    TW, TH = 1080, 1920
    try:
        t = dict(thumb)
        t["lines"] = t.get("lines") or [t.get("text", "")]
        t["emoji"] = variant.get("emoji") or t.get("emoji") or "😮"
        P = PALETTES.get(variant.get("palette"), PALETTES["red"])
        img = bg_burst(P[1], P[0], TW // 2, 1300, 22).convert("RGBA")
        e = emoji_img(t["emoji"], 560)
        if e:
            _glow(img, e, ((TW - e.width) // 2, 1080), WHITE, 22)
        d = ImageDraw.Draw(img)
        if t.get("tag"):
            _tag(d, t["tag"], (60, 140), (230, 20, 30), WHITE)
        _text_block(img, t["lines"], 50, 300, TW - 100, 170, P, align="center", line_colors=[P[4], P[6]])
        if t.get("badge"):
            _starburst(img, (TW - 200, 960), 110, (230, 20, 30), t["badge"])
        _badge(ImageDraw.Draw(img), BRANDS[brand_key]["name"], _hex(P[6]))
        img.convert("RGB").save(out_png, "PNG")
        return out_png
    finally:
        TW, TH = old
