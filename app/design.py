"""v2.3.0 (owner ke reference screenshot ke baad): PREMIUM NEON QUIZ DESIGN - reel + thumbnail.

Owner ne 3 Nov ko apne pasand ke quiz-reel ke namoone bheje (neon frame, glass card, A/B/C vikalp patti, timer ring,
neeche bada CTA). Ye module wahi andaaz CPU par (PIL) banata hai - koi bahari image/model zaroori nahi.
Sach ka niyam: koi nakli 'votes %' / '99% fail' nahi; jawab wale scene mein sahi vikalp hara + sahi ka nishaan.
Sirf apne khud ke banaye aakar (koi copyright wala chitra nahi).
"""
import math
import random
import re

from PIL import Image, ImageDraw, ImageFilter

from . import text as T
from .config import BRANDS, SITE

W, H = 1080, 1920
# v2.3.1: platform 'safe zone' - neeche ~420px (YouTube/IG ka naam-caption-button) aur daayein ~120px (like/comment) mein
# kuch zaroori nahi. Pehle site ka naam/CTA neeche dab jaata tha ("sabhisaab.com pura nahi dikhta").
SAFE_BOTTOM = 1470
CTA_Y = 1290
SITE_Y = 1400
OPT_X1 = 940
ACC = {  # brand: (mukhya neon, doosra neon)
    "money": ((0, 255, 150), (255, 204, 51)),
    "deals": ((255, 61, 139), (255, 204, 51)),
    "pahadi": ((0, 229, 255), (124, 255, 178)),
    "sunonatak": ((255, 196, 0), (190, 90, 255)),
}
KIND_NAME = {
    "shuddh_hindi": "शुद्ध हिंदी (Language GK)", "color_match": "रंग मिलान (Logic)", "number_connect": "संख्या ट्रिक (Math Trap)",
    "ball_memory": "गेंद-कटोरी (Memory)", "odd_one_out": "अलग पहचानो (Visual IQ)", "speed_math": "स्पीड गणित (Math Trap)",
    "matchstick": "माचिस तीली (Brain Riddle)", "memory_flash": "मेमोरी फ्लैश (Memory)", "optical_count": "त्रिभुज गिनो (Optical IQ)",
    "word_scramble": "शब्द पहेली (Word Logic)", "exam_quant": "सरकारी परीक्षा (Exam Trick)",
    "pahadi_gk": "पहाड़ी GK (Uttarakhand)", "pahadi_shabd": "पुराने पहाड़ी शब्द (Boli)",
}
BRAND_NAME = {"money": "Sab Hisaab Money", "deals": "Labh Lo Deals", "pahadi": "Pahadi Hisaab", "sunonatak": "Suno Natak"}
BRAND_CAT = {"money": "पैसे का हिसाब (Money Check)", "deals": "बचत का गणित (Smart Saving)",
             "pahadi": "पहाड़ी GK (Uttarakhand)", "sunonatak": "रोज़ की कहानी (Real Life)"}


# v2.3.6: rang-palette - bot khud naye rang aazmata hai (namoona -> aapki haan / 24 ghante baad apne aap default list mein)
PALETTES = {
    "neon_aqua": ((0, 229, 255), (255, 61, 139)), "royal_gold": ((255, 200, 60), (150, 90, 255)),
    "sunset": ((255, 120, 60), (255, 60, 140)), "mint_lime": ((60, 255, 180), (200, 255, 60)),
    "ice_blue": ((120, 200, 255), (255, 255, 255)), "ruby_gold": ((255, 70, 90), (255, 210, 80)),
    "violet_cyan": ((180, 90, 255), (0, 230, 255)), "emerald_pink": ((0, 220, 130), (255, 100, 200)),
}
_PAL = {"p": None}


def use_palette(name):
    """None = har channel ka apna rang (purana)."""
    _PAL["p"] = PALETTES.get(name) if name else None


def _acc(brand):
    if _PAL["p"]:
        return _PAL["p"]
    return ACC.get(brand, ACC["money"])


def _glow(base, shape_fn, color, radius=18, strength=2):
    """Neon chamak: shape ko alag layer par, blur karke niche, phir saaf shape upar."""
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shape_fn(ImageDraw.Draw(lay), color)
    blur = lay.filter(ImageFilter.GaussianBlur(radius))
    for _ in range(strength):
        base.alpha_composite(blur)
    base.alpha_composite(lay)


def _text_glow(base, xy, txt, size, fill, glow, radius=10):
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    T.draw(ImageDraw.Draw(lay), xy, txt, size, glow)
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(radius)))
    T.draw(ImageDraw.Draw(base), xy, txt, size, fill, stroke=2, stroke_fill=(0, 0, 0))


def _bg_light(seed, out_path, size):
    """v2.7.6: safed-halka parat + bindu grid + rangin confetti (3 SEC TEST jaisa)."""
    w, h = size
    rnd = random.Random(seed)
    img = Image.new("RGB", (w, h), (244, 246, 250))
    d = ImageDraw.Draw(img)
    for y in range(h):
        c = int(250 - 10 * y / h)
        d.line([(0, y), (w, y)], fill=(c, c + 1, min(255, c + 4)))
    for x in range(60, w, 46):
        for y in range(60, h, 46):
            if rnd.random() < 0.35:
                d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(205, 210, 222))
    for _ in range(60):
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        col = rnd.choice([(255, 90, 90), (60, 190, 120), (70, 140, 255), (255, 180, 40), (180, 90, 255)])
        if rnd.random() < 0.5:
            d.ellipse([x, y, x + 9, y + 9], fill=col)
        else:
            d.line([(x, y), (x + 16, y + 8)], fill=col, width=5)
    img.save(out_path, quality=95)
    return out_path


def _bg_versus(seed, out_path, size):
    """v2.7.6: comic split - baayein neela, daayein narangi, beech mein peeli bijli, halftone bindu."""
    w, h = size
    img = Image.new("RGB", (w, h), (30, 136, 229))
    d = ImageDraw.Draw(img)
    d.polygon([(int(w * 0.58), 0), (w, 0), (w, h), (int(w * 0.42), h)], fill=(255, 122, 26))
    for x in range(0, w, 28):                       # halftone bindu
        for y in range(0, h, 28):
            r_ = 4 if (x + y) % 56 == 0 else 3
            d.ellipse([x - r_, y - r_, x + r_, y + r_], fill=(255, 255, 255, 40) if x < w / 2 else (255, 230, 200))
    img = Image.blend(Image.new("RGB", (w, h), (30, 136, 229)), img, 0.92)
    d = ImageDraw.Draw(img)
    d.polygon([(int(w * 0.58), 0), (w, 0), (w, h), (int(w * 0.42), h)], fill=(255, 122, 26))
    cx = w // 2
    bolt = [(cx + 40, 0), (cx - 70, int(h * 0.42)), (cx + 20, int(h * 0.42)), (cx - 60, h), (cx + 90, int(h * 0.36)),
            (cx + 5, int(h * 0.36)), (cx + 110, 0)]
    d.polygon(bolt, fill=(255, 214, 0), outline=(40, 20, 0))
    img.save(out_path, quality=95)
    return out_path


def _bg_exam(seed, out_path, size):
    """v2.9.4: safed + halka rangin glow (peela/neela/gulabi baari-baari) - saaf exam card."""
    w, h = size
    rnd = random.Random(seed)
    tint = rnd.choice([(255, 236, 120), (190, 220, 255), (255, 205, 220), (200, 245, 210)])
    img = Image.new("RGB", (w, h), tint)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([-w * 0.25, h * 0.08, w * 1.25, h * 0.92], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(160))
    img = Image.composite(Image.new("RGB", (w, h), (255, 255, 255)), img, m)
    img.save(out_path, quality=95)
    return out_path


def background(brand, seed, out_path, size=(W, H)):
    """Gehra neeli-baingani parat + neon perspective grid + chamakti rekhaayein + bokeh. Har video alag (seed)."""
    if _LAY["l"] == "exam":
        return _bg_exam(seed, out_path, size)
    if _LAY["l"] == "light3":
        return _bg_light(seed, out_path, size)
    if _LAY["l"] == "versus":
        return _bg_versus(seed, out_path, size)
    w, h = size
    rnd = random.Random(seed)
    a1, a2 = _acc(brand)
    img = Image.new("RGBA", (w, h), (6, 8, 22, 255))
    # radial gradient (beech mein halka baingani)
    grad = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(grad)
    cx, cy = w // 2, int(h * 0.38)
    for r_ in range(int(max(w, h) * 0.9), 0, -12):
        gd.ellipse([cx - r_, cy - r_, cx + r_, cy + r_], fill=int(110 * (1 - r_ / (max(w, h) * 0.9))))
    tint = Image.new("RGBA", (w, h), (70, 20, 120, 255))
    img = Image.composite(tint, img, grad.filter(ImageFilter.GaussianBlur(40)))
    # perspective grid (neeche 40%)
    gl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gdr = ImageDraw.Draw(gl)
    hor = int(h * 0.62)
    for i in range(-14, 15):
        gdr.line([(w // 2 + i * 26, hor), (w // 2 + i * 260, h)], fill=a1 + (70,), width=2)
    y, step = hor, 10
    while y < h:
        gdr.line([(0, y), (w, y)], fill=a1 + (60,), width=2)
        step *= 1.28
        y += int(step)
    img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(1)))
    # chamakti light-trail rekhaayein
    for k in range(3):
        col = (a1 if k % 2 == 0 else a2) + (230,)
        ph, amp, yb = rnd.uniform(0, 6.28), rnd.randint(60, 160), rnd.randint(int(h * 0.12), int(h * 0.7))

        def trail(d, c, ph=ph, amp=amp, yb=yb):
            pts = [(x, yb + amp * math.sin(x / 170 + ph)) for x in range(-40, w + 41, 12)]
            d.line(pts, fill=c, width=6)
        _glow(img, trail, col, radius=16, strength=1)
    # bokeh kan
    bk = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bk)
    for _ in range(46):
        x_, y_, r_ = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(3, 14)
        c_ = rnd.choice([a1, a2, (255, 255, 255)])
        bd.ellipse([x_ - r_, y_ - r_, x_ + r_, y_ + r_], fill=c_ + (rnd.randint(40, 120),))
    img.alpha_composite(bk.filter(ImageFilter.GaussianBlur(3)))
    # vignette
    vg = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vg).rounded_rectangle([40, 40, w - 40, h - 40], radius=120, fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    img = Image.composite(img, dark, vg)
    img.convert("RGB").save(out_path, quality=95)
    return out_path


def _clean(t):
    t = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D]", "", t or "")
    t = re.sub(r"^\s*(✅|सही जवाब:?)\s*", "", t).replace("→", " = ").replace("⏱", "").replace("≈", " लगभग ").replace("×", " x ")
    return re.sub(r"\s{2,}", " ", t).strip()


REVEAL_RX = re.compile(r"^\s*✅|सही जवाब\s*[:：!।-]|सही जवाब है|सही उत्तर\s*[:：]|सही उत्तर है|^\s*जवाब\s*[:：]")


def _scene_kind(sc, idx, total, script):
    s = (sc.get("show") or "")
    if sc.get("answer_cta"):                      # v2.5.0: 'jawab website par' wala aakhri scene (jawab nahi dikhata)
        return "cta"
    if REVEAL_RX.search(s) and not script.get("answer_offsite"):
        return "reveal"       # v2.5.0: pehle 'सही जवाब बताइए' (sawal) ko bhi reveal maan kar PEHLE second mein jawab dikha deta tha
    if idx == total - 1:
        return "cta"
    if script.get("puzzle_options") and ("विकल्प" in s or idx == 1):
        return "options"
    if "ट्रिक" in s or "शॉर्टकट" in s or "💡" in s:
        return "trick"
    return "question" if idx == 0 else "info"


def _pill(img, cx, y, txt, size, acc, fill=(10, 12, 28, 220)):
    tw = T.width(txt, size)
    x0, x1 = int(cx - tw / 2 - 34), int(cx + tw / 2 + 34)
    _glow(img, lambda d, c: d.rounded_rectangle([x0, y, x1, y + size + 34], radius=(size + 34) // 2, outline=c, width=4),
          acc + (255,), radius=12, strength=1)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0 + 3, y + 3, x1 - 3, y + size + 31], radius=(size + 28) // 2, fill=fill)
    T.draw(d, (cx - tw / 2, y + 8), txt, size, (255, 255, 255))
    return y + size + 34


def _card(img, box, acc, lines, size):
    x0, y0, x1, y1 = box
    _glow(img, lambda d, c: d.rounded_rectangle(box, radius=44, outline=c, width=5), acc + (255,), radius=22, strength=2)
    glass = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glass).rounded_rectangle([x0 + 4, y0 + 4, x1 - 4, y1 - 4], radius=40, fill=(12, 16, 36, 215))
    img.alpha_composite(glass)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0 + 18, y0 + 14, x1 - 18, y0 + 20], radius=3, fill=(255, 255, 255, 40))     # kaanch ki chamak
    th = len(lines) * size * 1.32
    y = y0 + (y1 - y0 - th) / 2 - size * 0.12
    for ln in lines:
        col = (255, 230, 60) if re.search(r"[\d₹%?]", ln) and ln is lines[0] else (255, 255, 255)
        T.draw(d, ((x0 + x1 - T.width(ln, size)) / 2, y), ln, size, col, stroke=2, stroke_fill=(0, 0, 0))
        y += size * 1.32


def _check(d, cx, cy, s, col):
    d.line([(cx - s, cy), (cx - s * 0.3, cy + s * 0.7), (cx + s, cy - s * 0.8)], fill=col, width=max(6, s // 4), joint="curve")


# v2.4.0: LAYOUT bhi rotate - bot naya layout namoona deta hai (haan / 24 ghante baad apne aap)
LAYOUTS = {"list": "Vikalp line mein (purana)", "grid": "Vikalp 2x2 khane", "big3d": "Bada chitra, chhota card",
           # v2.7.5 (owner ki 24 card-model photo se): har vikalp ka apna neon rang 2x2 + seedhi timer-patti
           "neon4": "Char rang ke neon khane + timer patti", "bar": "Vikalp line + seedhi timer patti (rangin)",
           # v2.7.6: owner ki photo ke light/comic card - '3 SEC TEST' safed card, 'TEAM A vs TEAM B' comic split
           "light3": "Safed saaf card (3 SEC TEST jaisa)", "versus": "TEAM A vs TEAM B comic (neela-narangi)",
           "exam": "Exam card (safed, bold kaale ank, laal gol vikalp, diagram) - Ranker jaisa"}
LIGHT = ("light3", "versus", "exam")
_ELIM = {"s": set()}          # v2.7.6 V3 50-50: is scene mein kaun se 2 GALAT vikalp kaate gaye (sahi kabhi nahi)


def _strike(img, box):
    """Kata hua vikalp: upar halka dhakkan + laal tirchhi rekha (flash nahi)."""
    x0, y0, x1, y1 = box
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle(box, radius=26, fill=(20, 20, 30, 150))
    od.line([(x0 + 20, y1 - 14), (x1 - 20, y0 + 14)], fill=(255, 70, 70, 230), width=9)
    img.alpha_composite(ov)
OPT_COLS = [(0, 229, 255), (60, 255, 120), (230, 80, 255), (255, 160, 40)]      # A cyan, B hara, C bangni, D narangi
_LAY = {"l": "list"}


def use_layout(name):
    _LAY["l"] = name if name in LAYOUTS else "list"


def _options_grid(img, y, opts, ans, acc, reveal):
    """2x2 khane (game-show jaisa)."""
    letters = "ABCD"
    bw, bh, gap = (OPT_X1 - 90 - 24) // 2, 150, 24
    for i, o in enumerate(opts[:4]):
        x0 = 90 + (i % 2) * (bw + gap)
        y0 = y + (i // 2) * (bh + gap)
        ok = reveal and str(o).strip() == str(ans).strip()
        col = (0, 200, 110) if ok else ((70, 74, 96) if reveal else acc)
        box = [x0, y0, x0 + bw, y0 + bh]
        _glow(img, lambda d, c, b=box: d.rounded_rectangle(b, radius=34, outline=c, width=4), col + (255,), radius=12, strength=1)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([x0 + 3, y0 + 3, x0 + bw - 3, y0 + bh - 3], radius=31, fill=(0, 120, 70, 230) if ok else (14, 18, 38, 228))
        d.ellipse([x0 + 16, y0 + 16, x0 + 76, y0 + 76], fill=col + (255,))
        T.draw(d, (x0 + 46 - T.width(letters[i], 38) / 2, y0 + 18), letters[i], 38, (10, 10, 10))
        sz, lns = T.fit(_clean(str(o)), bw - 40, 70, start=44, smallest=26)
        yy = y0 + 84
        for ln in lns[:2]:
            T.draw(d, (x0 + (bw - T.width(ln, sz)) / 2, yy - 6), ln, sz, (255, 255, 255))
            yy += int(sz * 1.15)
        if ok:
            _check(d, x0 + bw - 46, y0 + 46, 20, (255, 255, 255))
        if str(o) in _ELIM["s"] and not reveal:
            _strike(img, box)
    return y + 2 * (bh + gap)


def _timer_bar(img, y, sec, acc, frac=0.7):
    """v2.7.5: seedhi neon timer-patti (gol ghadi ki jagah) - 'Ns' ke saath. Flash nahi."""
    x0, x1, h = 150, W - 210, 34
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y, x1, y + h], radius=17, outline=(255, 255, 255, 120), width=3, fill=(10, 12, 28, 200))
    fx = x0 + 6 + int((x1 - x0 - 12) * frac)
    _glow(img, lambda dd, c: dd.rounded_rectangle([x0 + 6, y + 6, fx, y + h - 6], radius=11, fill=c), acc + (255,), radius=10, strength=1)
    d = ImageDraw.Draw(img)
    T.draw(d, (x1 + 18, y - 6), f"{sec}s", 40, acc)
    return y + h + 26


def _options_neon4(img, y, opts, ans, acc, reveal):
    """v2.7.5: 2x2, har khana alag neon rang (A cyan, B hara, C bangni, D narangi)."""
    letters = "ABCD"
    bw, bh, gap = (OPT_X1 - 90 - 24) // 2, 140, 22
    for i, o in enumerate(opts[:4]):
        x0, y0 = 90 + (i % 2) * (bw + gap), y + (i // 2) * (bh + gap)
        ok = reveal and str(o).strip() == str(ans).strip()
        col = (0, 200, 110) if ok else ((70, 74, 96) if reveal else OPT_COLS[i])
        box = [x0, y0, x0 + bw, y0 + bh]
        _glow(img, lambda d, c, b=box: d.rounded_rectangle(b, radius=26, outline=c, width=5), col + (255,), radius=14, strength=2)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([x0 + 4, y0 + 4, x0 + bw - 4, y0 + bh - 4], radius=22, fill=(0, 110, 64, 230) if ok else (8, 10, 28, 225))
        T.draw(d, (x0 + 24, y0 + (bh - 60) / 2 - 8), letters[i], 60, col)
        sz, lns = T.fit(_clean(str(o)), bw - 120, 90, start=50, smallest=26)
        yy = y0 + (bh - len(lns[:2]) * sz * 1.15) / 2 - 6
        for ln in lns[:2]:
            T.draw(d, (x0 + 100 + (bw - 120 - T.width(ln, sz)) / 2, yy), ln, sz, (255, 255, 255))
            yy += int(sz * 1.15)
        if str(o) in _ELIM["s"] and not reveal:
            _strike(img, box)
    return y + 2 * (bh + gap)


def _options(img, y, opts, ans, acc, reveal):
    if _LAY["l"] in ("neon4", "bar") and not reveal:
        y = _timer_bar(img, y, 5, acc)
    if _LAY["l"] == "neon4" and len(opts) == 4:
        return _options_neon4(img, y, opts, ans, acc, reveal)
    if _LAY["l"] == "grid" and len(opts) == 4:
        return _options_grid(img, y, opts, ans, acc, reveal)
    d = ImageDraw.Draw(img)
    letters = "ABCD"
    for i, o in enumerate(opts[:4]):
        ok = reveal and str(o).strip() == str(ans).strip()
        bar_col = (0, 200, 110) if ok else ((70, 74, 96) if reveal else (OPT_COLS[i] if _LAY["l"] == "bar" else acc))
        box = [90, y, OPT_X1, y + 100]
        _glow(img, lambda dd, c, b=box: dd.rounded_rectangle(b, radius=58, outline=c, width=4),
              bar_col + (255,), radius=10 if not ok else 18, strength=1)
        fillc = (0, 120, 70, 230) if ok else (14, 18, 38, 225)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([box[0] + 3, y + 3, box[2] - 3, y + 97], radius=48, fill=fillc)
        d.ellipse([108, y + 14, 180, y + 86], fill=bar_col + (255,))
        T.draw(d, (144 - T.width(letters[i], 42) / 2, y + 18), letters[i], 42, (10, 10, 10))
        sz, lns = T.fit(_clean(str(o)), OPT_X1 - 330, 56, start=46, smallest=28)
        ln0 = lns[0] if len(lns) == 1 else (lns[0][:28] + "…")
        T.draw(d, (205, y + 50 - sz * 0.75), ln0, sz, (255, 255, 255))
        if ok:
            _check(d, OPT_X1 - 60, y + 50, 24, (255, 255, 255))
        if str(o) in _ELIM["s"] and not reveal:
            _strike(img, [box[0], y, box[2], y + 100])
        y += 114
    return y


def _timer(img, cx, cy, r, sec, acc):
    def ring(d, c):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 60), width=10)
        d.arc([cx - r, cy - r, cx + r, cy + r], start=-90, end=-90 + 300, fill=c, width=12)
    _glow(img, ring, acc + (255,), radius=14, strength=2)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r + 16, cy - r + 16, cx + r - 16, cy + r - 16], fill=(8, 10, 26, 230))
    fz = max(96, int(r * 0.9)) if r > 110 else 96
    lz = max(30, int(r * 0.22)) if r > 110 else 30
    T.draw(d, (cx - T.width(str(sec), fz) / 2, cy - fz * 0.82), str(sec), fz, (255, 255, 255))
    T.draw(d, (cx - T.width("सेकंड", lz) / 2, cy + fz * 0.3), "सेकंड", lz, acc)


def _cube(img, x, y, s, top_col, side_col, label, acc):
    """Isometric chamakta cube (upar akshar)."""
    pts_top = [(x, y), (x + s, y - s * 0.5), (x + 2 * s, y), (x + s, y + s * 0.5)]
    pts_l = [(x, y), (x + s, y + s * 0.5), (x + s, y + s * 1.5), (x, y + s)]
    pts_r = [(x + s, y + s * 0.5), (x + 2 * s, y), (x + 2 * s, y + s), (x + s, y + s * 1.5)]

    def sh(d, c):
        d.polygon(pts_top, outline=c, width=4)
        d.polygon(pts_l, outline=c, width=4)
        d.polygon(pts_r, outline=c, width=4)
    d = ImageDraw.Draw(img)
    d.polygon(pts_top, fill=top_col + (235,))
    d.polygon(pts_l, fill=side_col + (235,))
    d.polygon(pts_r, fill=tuple(max(0, v - 40) for v in side_col) + (235,))
    _glow(img, sh, acc + (255,), radius=8, strength=1)
    d = ImageDraw.Draw(img)
    fs = int(s * 0.62)
    T.draw(d, (x + s - T.width(label, fs) / 2, y - fs * 0.62), label, fs, (20, 20, 30))


def _panel3d(img, path, box, acc):
    """v2.3.3: apna 3D chitra (Blender) neon frame wali khidki mein - box ke hisaab se beech se kaata."""
    from PIL import ImageOps
    x0, y0, x1, y1 = [int(v) for v in box]
    ph = Image.open(path).convert("RGB")
    ph = ImageOps.fit(ph, (x1 - x0, y1 - y0), Image.LANCZOS, centering=(0.5, 0.45)).convert("RGBA")
    mask = Image.new("L", ph.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, ph.size[0] - 1, ph.size[1] - 1], radius=36, fill=255)
    img.paste(ph, (x0, y0), mask)
    _glow(img, lambda d, c: d.rounded_rectangle(box, radius=36, outline=c, width=5), acc + (255,), radius=14, strength=2)


_GRID = {"g": None}


def _sudoku(img, g, box, acc):
    a1, a2 = acc
    x0, y0, x1, y1 = [int(v) for v in box]
    side = min(x1 - x0, y1 - y0) - 10
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    n = len(g) or 4                                    # v2.8.0: 3x3 (jadui vargh / 1-9) bhi
    gx, gy, c = cx - side // 2, cy - side // 2, side // n
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([gx - 8, gy - 8, gx + side + 8, gy + side + 8], radius=18, fill=(10, 14, 32, 235))
    for i in range(n):
        for j in range(n):
            v = str(g[i][j])
            bx, by = gx + j * c, gy + i * c
            q_ = v == "?"
            d.rounded_rectangle([bx + 4, by + 4, bx + c - 4, by + c - 4], radius=10,
                                fill=(255, 230, 60, 255) if q_ else (24, 30, 60, 255), outline=a1 + (200,), width=2)
            fz = int(c * 0.55)
            T.draw(d, (bx + c / 2 - T.width(v, fz) / 2, by + c / 2 - fz * 0.75), v, fz, (20, 20, 20) if q_ else (255, 255, 255))
    for k in ((0, 2, 4) if n == 4 else (0, n)):
        d.line([(gx + k * c, gy), (gx + k * c, gy + side)], fill=a2 + (255,), width=5)
        d.line([(gx, gy + k * c), (gx + side, gy + k * c)], fill=a2 + (255,), width=5)


def _illustration(img, kind, brand, box, seed, path3d=None):
    """Har puzzle ka apna neon chitra (CPU par, apna banaya - koi copyright chitra nahi). v2.3.3: 3D ho to wahi."""
    if kind in ("sudoku4", "magic_square", "pick_sum") and _GRID.get("g"):   # v2.3.4/2.8.0: asli jaal (3D ki jagah)
        return _sudoku(img, _GRID["g"], box, _acc(brand))
    if path3d:
        try:
            return _panel3d(img, path3d, box, _acc(brand)[0])
        except Exception:
            pass
    if kind in ("pahadi_purana", "pahadi_shabd"):
        kind = "pahadi_gk"
    if kind in ("utpate_shabd", "purane_shabd", "shuddh_hindi", "word_scramble"):
        kind = "shuddh_hindi"
    a1, a2 = _acc(brand)
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    rnd = random.Random(seed)
    # peeche chamakta gola
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hr = min(x1 - x0, y1 - y0) // 2 - 10
    ImageDraw.Draw(halo).ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=a2 + (55,))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(60)))
    if kind in ("shuddh_hindi", "word_scramble"):
        letters = ["अ", "क", "श", "ह"] if kind == "shuddh_hindi" else ["ब", "च", "त", "?"]
        cols = [(255, 214, 90), (110, 235, 255), (255, 120, 190), (140, 255, 170)]
        s_ = 115
        for i, (lx, ly) in enumerate([(cx - 2.15 * s_, cy - 30), (cx - 0.2 * s_, cy - 140), (cx - 0.2 * s_, cy + 90), (cx + 1.7 * s_, cy - 20)]):
            _cube(img, lx, ly, s_, cols[i], tuple(int(v * 0.6) for v in cols[i]), letters[i], a1)
    elif kind == "optical_count":
        def tri(d, c):
            n = 3
            top, bl, br = (cx, y0 + 90), (x0 + 140, y1 - 60), (x1 - 140, y1 - 60)
            d.polygon([top, bl, br], outline=c, width=7)
            for k in range(1, n):
                px = bl[0] + (br[0] - bl[0]) * k / n
                d.line([top, (px, bl[1])], fill=c, width=6)
        _glow(img, tri, a1 + (255,), radius=14, strength=2)
    elif kind == "color_match":       # rang ki pipe beech ke '?' mein - kis box mein jaye, yahi sawal (chitra jawab nahi batata)
        cols = [(255, 70, 90), (70, 140, 255), (60, 230, 120), (255, 214, 60)]
        bx = [x0 + 90 + i * ((x1 - x0 - 180) // 3) for i in range(4)]
        for i in range(4):
            def pipe(d, c, i=i):
                d.line([(bx[i], y0 + 40), (bx[i], cy - 70), (cx, cy - 10)], fill=c, width=18, joint="curve")
            _glow(img, pipe, cols[i] + (230,), radius=10, strength=1)
        _glow(img, lambda dd, c: dd.ellipse([cx - 62, cy - 72, cx + 62, cy + 52], fill=(20, 24, 60, 255), outline=c, width=6),
              (255, 255, 255, 255), radius=12, strength=1)
        d = ImageDraw.Draw(img)
        T.draw(d, (cx - T.width("?", 80) / 2, cy - 76), "?", 80, (255, 230, 60))
        for i in range(4):
            d.rounded_rectangle([bx[i] - 60, y1 - 140, bx[i] + 60, y1 - 30], radius=18, fill=(20, 26, 60, 240), outline=a1 + (255,), width=4)
            T.draw(d, (bx[i] - T.width(str(i + 1), 64) / 2, y1 - 136), str(i + 1), 64, (255, 255, 255))
    elif kind == "ball_memory":
        d = ImageDraw.Draw(img)
        for i, lab in enumerate("ABC"):
            ccx = x0 + (x1 - x0) * (i + 1) // 4
            _glow(img, lambda dd, c, ccx=ccx: dd.polygon([(ccx - 90, cy + 110), (ccx + 90, cy + 110), (ccx + 60, cy - 90), (ccx - 60, cy - 90)],
                                                         outline=c, width=6), a1 + (255,), radius=10, strength=1)
            d = ImageDraw.Draw(img)
            d.polygon([(ccx - 86, cy + 106), (ccx + 86, cy + 106), (ccx + 57, cy - 86), (ccx - 57, cy - 86)], fill=(30, 36, 80, 235))
            T.draw(d, (ccx - T.width(lab, 56) / 2, cy - 30), lab, 56, a2)
        _glow(img, lambda dd, c: dd.ellipse([cx - 36, y1 - 120, cx + 36, y1 - 48], fill=c), (255, 90, 90, 255), radius=14, strength=2)
    elif kind == "matchstick":
        def stick(d, c, xa, ya, xb, yb):
            d.line([(xa, ya), (xb, yb)], fill=(240, 200, 120, 255), width=14)
            d.ellipse([xb - 14, yb - 14, xb + 14, yb + 14], fill=c)
        d = ImageDraw.Draw(img)
        xs = x0 + 70
        for k in range(6):
            xa = xs + k * 140
            _glow(img, lambda dd, c, xa=xa: stick(dd, c, xa, cy + 120, xa + 40, cy - 120), (255, 70, 40, 255), radius=8, strength=1)
    elif kind == "pahadi_gk" or (not kind and brand == "pahadi"):            # pahad: neon parvat + suraj
        def mnt(d, c):
            hh, ww = y1 - y0, x1 - x0
            base = y1 - int(hh * 0.10)
            d.polygon([(x0 + int(ww * 0.05), base), (x0 + int(ww * 0.32), y0 + int(hh * 0.30)), (x0 + int(ww * 0.62), base)], outline=c, width=7)
            d.polygon([(x0 + int(ww * 0.38), base), (x0 + int(ww * 0.68), y0 + int(hh * 0.14)), (x0 + int(ww * 0.95), base)], outline=c, width=7)
            for k in range(3):                    # barf ki lakeer
                d.line([(x0 + int(ww * (0.27 + 0.36 * (k % 2))), y0 + int(hh * (0.40 - 0.12 * (k % 2)))),
                        (x0 + int(ww * (0.37 + 0.36 * (k % 2))), y0 + int(hh * (0.40 - 0.12 * (k % 2))))], fill=(230, 245, 255, 255), width=5)
        sr = int(min(y1 - y0, x1 - x0) * 0.12)
        sx, sy = x0 + int((x1 - x0) * 0.04), y0 + int((y1 - y0) * 0.06)
        _glow(img, lambda dd, c: dd.ellipse([sx, sy, sx + 2 * sr, sy + 2 * sr], outline=c, width=7), (255, 204, 51, 255), radius=16, strength=2)
        _glow(img, mnt, a1 + (255,), radius=14, strength=2)
    elif kind == "pahadi_shabd" or (not kind and brand == "sunonatak"):     # boli/kahani: do baat ke bubble
        hh = y1 - y0
        b1 = [x0 + 80, y0 + int(hh * 0.12), cx + 40, y0 + int(hh * 0.48)]
        b2 = [cx - 20, y0 + int(hh * 0.40), x1 - 80, y0 + int(hh * 0.78)]
        _glow(img, lambda dd, c: dd.rounded_rectangle(b1, radius=40, outline=c, width=7), a1 + (255,), radius=14, strength=2)
        _glow(img, lambda dd, c: dd.rounded_rectangle(b2, radius=40, outline=c, width=7), a2 + (255,), radius=14, strength=2)
        d = ImageDraw.Draw(img)
        fz = int(hh * 0.22)
        T.draw(d, ((b1[0] + b1[2]) / 2 - T.width("अ आ", fz) / 2, b1[1] + (b1[3] - b1[1]) / 2 - fz * 0.75), "अ आ", fz, a1)
        T.draw(d, ((b2[0] + b2[2]) / 2 - T.width("?!", fz) / 2, b2[1] + (b2[3] - b2[1]) / 2 - fz * 0.75), "?!", fz, a2)
    elif not kind and brand == "deals":             # deal: chamakta price-tag + %
        def tag(d, c):
            d.polygon([(cx - 230, cy - 120), (cx + 130, cy - 120), (cx + 250, cy), (cx + 130, cy + 120), (cx - 230, cy + 120)], outline=c, width=8)
            d.ellipse([cx + 110, cy - 20, cx + 150, cy + 20], outline=c, width=6)
        _glow(img, tag, a1 + (255,), radius=16, strength=2)
        d = ImageDraw.Draw(img)
        T.draw(d, (cx - 190, cy - 95), "% OFF", 110, (255, 230, 60), stroke=3, stroke_fill=(0, 0, 0))
    else:   # paisa / ganit / exam / memory / odd: chamakta sikka + %
        for k in range(4):
            yy = cy + 120 - k * 46
            _glow(img, lambda dd, c, yy=yy: dd.ellipse([cx - 210, yy - 34, cx - 30, yy + 34], outline=c, width=6),
                  (255, 204, 51, 255), radius=8, strength=1)
            d = ImageDraw.Draw(img)
            d.ellipse([cx - 207, yy - 31, cx - 33, yy + 31], fill=(120, 90, 10, 235))
        d = ImageDraw.Draw(img)
        T.draw(d, (cx - 150, cy - 140), "₹", 120, (255, 230, 90), stroke=3, stroke_fill=(60, 40, 0))
        _glow(img, lambda dd, c: dd.ellipse([cx + 20, cy - 150, cx + 260, cy + 90], outline=c, width=10), a1 + (255,), radius=14, strength=2)
        sym = "%" if kind in ("speed_math", "exam_quant") else "?"
        d = ImageDraw.Draw(img)
        T.draw(d, (cx + 140 - T.width(sym, 150) / 2, cy - 140), sym, 150, a1, stroke=3, stroke_fill=(0, 0, 0))


def _frame(img, acc):
    """Bahar neon frame (owner ke namoone jaisa phone-frame ehsaas)."""
    _glow(img, lambda d, c: d.rounded_rectangle([22, 22, W - 22, H - 22], radius=70, outline=c, width=6), acc + (230,), radius=20, strength=2)


def body_frame(script, idx, total, out_path):
    """Ek scene ki paardarshi parat: neon frame + category + chitra + glass card + vikalp/timer + bada CTA."""
    use_layout(script.get("layout"))                 # v2.7.6 BUG FIX: pehle render scene-frame banane ke BAAD layout/rang
    use_palette(script.get("palette"))               # lagata tha -> har video pichhli video ka layout/rang le leti thi
    _sc0 = (script.get("scenes") or [{}])[idx] if idx < len(script.get("scenes") or []) else {}
    _ELIM["s"] = (set(map(str, _sc0.get("elim") if _sc0.get("elim") is not None else (script.get("fifty_out") or [])))
                  if _sc0.get("fifty") else set())      # v3.2.0: har scene apni kati-list (dheere-dheere kaatna)
    if str(script.get("puzzle_answer", "")).strip() in _ELIM["s"]:      # pakka: sahi kabhi nahi kat-ta
        _ELIM["s"] = set()
    if _LAY["l"] == "exam":
        return _body_exam(script, idx, total, out_path)
    if _LAY["l"] in LIGHT:
        return _body_light(script, idx, total, out_path)
    brand = script.get("brand", "money")
    a1, a2 = _acc(brand)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sc = (script.get("scenes") or [{}])[idx]
    kind = _scene_kind(sc, idx, total, script)
    pk = script.get("puzzle_kind", "")
    opts0 = script.get("puzzle_options") or []
    line = ""
    if (opts0 and script.get("answer_offsite") and not sc.get("answer_cta") and kind in ("question", "info", "trick")):
        line = _clean(sc.get("show"))           # v2.7.3: sawal + vikalp POORI reel mein dikhein (pehle 'sochiye' scene par gayab)
        line = re.sub(r"\s*\((?:Code|कोड)\s*#\d+\)", "", line).strip()
        line = re.sub(r"^(?:सवाल|प्रश्न)\s*[:：]\s*.*$", "", line).strip()    # sawal pehle se card mein - dohraav nahi
        kind = "options"
    _frame(img, a1)
    cat = script.get("cat_label") or KIND_NAME.get(pk) or ("सवाल-जवाब" if opts0 else BRAND_CAT.get(brand, "सब हिसाब"))
    _GRID["g"] = script.get("grid4")
    y = _pill(img, W / 2, 70, cat, 42, a2)
    opts = script.get("puzzle_options") or []
    ans = script.get("puzzle_answer") or ""
    q = _clean(script.get("puzzle_q") or (script.get("scenes") or [{}])[0].get("show", ""))
    think = int((script.get("hud") or {}).get("think", 5))
    cta = ""
    if kind in ("question", "options") and opts:
        big3d = _LAY["l"] == "big3d"
        ih = 430 if big3d else 330
        _illustration(img, pk, brand, [70, y + 10, W - 70, y + ih], script.get("title", ""), script.get("img3d"))
        sz, lines = T.fit(q, W - 300, 200 if big3d else 260, start=60 if big3d else 66, smallest=38)
        ct0 = y + ih - 30
        _card(img, [60, ct0, W - 60, ct0 + (240 if big3d else 300)], a1, lines[:4], sz)
        if kind == "options":
            _options(img, ct0 + (270 if big3d else 330), opts, ans, a1, reveal=False)
            if idx > 0 and _LAY["l"] not in ("neon4", "bar"):   # pehle scene par timer nahi; neon4/bar mein seedhi patti
                _timer(img, W - 150, y + 90, 80, think, a2)
            cta = line or "कमेंट में जवाब दीजिए!"
        else:                                     # v2.4.1: pehle scene par timer nahi (sawal abhi poora nahi hua)
            cta = "ध्यान से पढ़ो - विकल्प आ रहे हैं!"
    elif kind == "reveal" and opts:
        sz, lines = T.fit(q, W - 300, 200, start=54, smallest=38)
        _card(img, [60, y + 30, W - 60, y + 270], a1, lines[:3], sz)
        yy = _options(img, y + 300, opts, ans, a1, reveal=True)
        exp = _clean(sc.get("show"))
        sz2, l2 = T.fit(exp, W - 300, 220, start=44, smallest=30)
        _card(img, [60, yy + 10, W - 60, min(CTA_Y - 40, yy + 300)], (0, 200, 110), l2[:5], sz2)
        cta = "सही जवाब!"
    else:
        big = idx == 0
        _illustration(img, pk, brand, [70, y + 10, W - 70, y + (420 if big else 360)], script.get("title", "") + str(idx if big else 0), script.get("img3d"))
        top = y + (390 if big else 340)
        sz, lines = T.fit(_clean(sc.get("show")), W - 300, CTA_Y - top - 200, start=88, smallest=44)
        ch = min(CTA_Y - 40 - top, max(340, int(len(lines) * sz * 1.32 + 140)))
        top = max(top, top + ((CTA_Y - 40 - top) - ch) // 3)    # card ko khaali jagah ke beech ki taraf
        _card(img, [60, top, W - 60, top + ch], a2 if kind == "trick" else a1, lines, sz)
        dd = ImageDraw.Draw(img)                         # scene ginti (2/5) - kitna baaki, dekhne wala ruke
        badge = f"{idx + 1}/{total}"
        dd.rounded_rectangle([W - 190, top - 34, W - 80, top + 20], radius=26, fill=a1 + (255,))
        T.draw(dd, (W - 135 - T.width(badge, 34) / 2, top - 32), badge, 34, (10, 10, 10))
        cta = {"question": "पूरा देखिए, फिर बताइए!", "trick": "2 सेकंड की ट्रिक", "cta": "फ्री टूल: sabhisaab.com",
               "info": "ध्यान से देखो"}.get(kind, "")
        if sc.get("answer_cta"):
            cta = "लिंक: डिस्क्रिप्शन / बायो में"
    if cta:
        cz = 66
        while cz > 40 and T.width(cta, cz) > W - 140:      # v2.7.3: lambi line chhoti (bahar na jaaye)
            cz -= 2
        while T.width(cta, cz) > W - 140 and len(cta) > 8:
            cta = cta[:-2].rstrip() + "…" if not cta.endswith("…") else cta[:-3].rstrip() + "…"
        cw = T.width(cta, cz)
        _text_glow(img, ((W - cw) / 2, CTA_Y), cta, cz, (255, 230, 60), a2 + (255,), radius=16)
    d = ImageDraw.Draw(img)
    st = full_url(script)                                       # v2.3.2: PURA pata (owner niyam) - https://sabhisaab.com/<page>
    fz = 40 if T.width(st, 40) < W - 200 else 32
    sw = T.width(st, fz) + 60
    d.rounded_rectangle([(W - sw) / 2, SITE_Y - 6, (W + sw) / 2, SITE_Y + fz + 18], radius=30, fill=(0, 0, 0, 170))
    T.draw(d, ((W - T.width(st, fz)) / 2, SITE_Y), st, fz, (230, 240, 255))
    bn = BRAND_NAME.get(brand, "")                               # neeche (platform caption ke peeche) halki brand patti - khaali na lage
    if bn:
        tag = f"{bn} • रोज़ 2 नए सवाल"
        T.draw(d, ((W - T.width(tag, 34)) / 2, 1560), tag, 34, a2 + (150,))
    img.save(out_path)
    return out_path



def _body_light(script, idx, total, out_path):
    """v2.7.6: light/comic card - gehre akshar, safed card, rangin vikalp. Jawab kabhi nahi (offsite), flash nahi."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sc = (script.get("scenes") or [{}])[idx]
    opts = script.get("puzzle_options") or []
    vs = _LAY["l"] == "versus"
    ink, sub = (20, 24, 40), (90, 98, 120)
    cta_scene = bool(sc.get("answer_cta")) or idx == total - 1
    # upar ka shirshak
    if vs:
        head = "TEAM A vs TEAM B" if script.get("hook_style") in ("team", "bahas") else "आप किसके साथ?"
        sz = 92 if T.width(head, 92) < W - 120 else 70
        T.draw(d, ((W - T.width(head, sz)) / 2, 110), head, sz, (255, 214, 0), stroke=8, stroke_fill=(25, 15, 60))
    else:
        d.ellipse([90, 96, 190, 196], fill=(240, 70, 70))
        d.ellipse([108, 114, 172, 178], fill=(255, 255, 255))
        d.line([(140, 146), (140, 122)], fill=(240, 70, 70), width=6)
        d.line([(140, 146), (158, 158)], fill=(240, 70, 70), width=6)
        lab = "5 SEC TEST"
        T.draw(d, (215, 112), lab, 70, ink)
    q = _clean(script.get("puzzle_q") or (script.get("scenes") or [{}])[0].get("show", ""))
    if cta_scene:
        q = _clean(sc.get("show"))
    sz, lines = T.fit(q, W - 260, 300, start=66, smallest=40)
    top = 430 if not cta_scene else 520
    ch = int(len(lines[:4]) * sz * 1.32 + 90)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))     # halki parchhai
    ImageDraw.Draw(sh).rounded_rectangle([70, top + 14, W - 70, top + ch + 14], radius=40, fill=(0, 0, 0, 70))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([70, top, W - 70, top + ch], radius=40, fill=(255, 255, 255, 250), outline=(225, 230, 240), width=3)
    y = top + 45
    for ln in lines[:4]:
        T.draw(d, ((W - T.width(ln, sz)) / 2, y), ln, sz, ink)
        y += int(sz * 1.32)
    y = top + ch + 50
    if opts and not cta_scene:
        letters, cols = "ABCD", [(0, 170, 220), (40, 180, 100), (170, 80, 230), (240, 140, 20)]
        bw, bh, gap = (W - 200 - 30) // 2, 160, 34
        for i, o in enumerate(opts[:4]):
            x0, y0 = 100 + (i % 2) * (bw + gap), y + (i // 2) * (bh + gap)
            d.rounded_rectangle([x0, y0 + 8, x0 + bw, y0 + bh + 8], radius=30, fill=(0, 0, 0, 45))
            d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=30, fill=(255, 255, 255, 250), outline=cols[i], width=5)
            d.ellipse([x0 + 20, y0 + (bh - 74) / 2, x0 + 94, y0 + (bh + 74) / 2], fill=cols[i])
            T.draw(d, (x0 + 57 - T.width(letters[i], 42) / 2, y0 + (bh - 74) / 2 + 6), letters[i], 42, (255, 255, 255))
            osz, ol = T.fit(_clean(str(o)), bw - 140, 120, start=56, smallest=28)
            yy = y0 + (bh - len(ol[:2]) * osz * 1.15) / 2 - 4
            for ln in ol[:2]:
                T.draw(d, (x0 + 110 + (bw - 130 - T.width(ln, osz)) / 2, yy), ln, osz, ink)
                yy += int(osz * 1.15)
            if str(o) in _ELIM["s"]:
                _strike(img, [x0, y0, x0 + bw, y0 + bh])
                d = ImageDraw.Draw(img)
        y += 2 * (bh + gap)
    # neeche ki line (hook / sochiye / link)
    line = _clean(sc.get("show")) if not cta_scene and idx > 0 else ""
    line = re.sub(r"\s*\((?:Code|कोड)\s*#\d+\)", "", line)
    if idx == 0 and not cta_scene:
        line = re.sub(r"\s*\((?:Code|कोड)\s*#\d+\)", "", _clean(sc.get("show")))
    line = re.sub(r"^(?:सवाल|प्रश्न)\s*[:：].*$", "", line).strip()       # sawal card mein pehle se
    if line and line not in q:
        lz = 60
        while lz > 36 and T.width(line, lz) > W - 140:
            lz -= 2
        T.draw(d, ((W - T.width(line, lz)) / 2, min(y + 30, CTA_Y)), line[:60], lz, (255, 255, 255) if vs else (220, 50, 70),
               stroke=5 if vs else 0, stroke_fill=(25, 15, 60) if vs else None)
    st = full_url(script)
    fz = 40 if T.width(st, 40) < W - 200 else 32
    sw = T.width(st, fz) + 60
    d.rounded_rectangle([(W - sw) / 2, SITE_Y - 6, (W + sw) / 2, SITE_Y + fz + 18], radius=30, fill=(20, 24, 40, 220))
    T.draw(d, ((W - T.width(st, fz)) / 2, SITE_Y), st, fz, (255, 255, 255))
    img.save(out_path)
    return out_path


INK, RED, BLUE = (17, 17, 17), (220, 30, 40), (25, 60, 210)


def _num(d, cx, cy, txt, sz, col=INK):
    txt = str(txt)
    T.draw(d, (cx - T.width(txt, sz) / 2, cy - sz * 0.72), txt, sz, col)


def _diagram(img, dg, top, bottom):
    """Owner ki Ranker photo jaise diagram: ratio, Y, dibbe, gole, cross, expr."""
    d = ImageDraw.Draw(img)
    t, v = dg.get("type"), dg.get("vals") or []
    mid = (top + bottom) / 2
    if t == "ratio":
        line = f"{v[0]} : {v[1]} :: {v[2]} : ?"
        sz = 130
        while T.width(line, sz) > W - 120 and sz > 70:
            sz -= 6
        x = (W - T.width(line, sz)) / 2
        for part in line.split(" "):
            col = RED if part == "?" else INK
            T.draw(d, (x, mid - sz * 0.7), part, sz, col)
            x += T.width(part + " ", sz)
    elif t == "expr":
        line = str(v[0]) + " = ?"
        sz = 120
        while T.width(line, sz) > W - 100 and sz > 60:
            sz -= 6
        T.draw(d, ((W - T.width(line, sz)) / 2, mid - sz * 0.7), line, sz, INK)
    elif t == "y":
        for k, cx in enumerate((W * 0.27, W * 0.73)):
            a_, b_ = v[k * 3], v[k * 3 + 1]
            res = v[2] if k == 0 else "?"
            ty, jy, by = top + 60, top + 240, top + 410
            d.line([(cx - 150, ty + 60), (cx, jy)], fill=(230, 40, 160), width=12)
            d.line([(cx + 150, ty + 60), (cx, jy)], fill=(230, 40, 160), width=12)
            d.line([(cx, jy), (cx, by - 40)], fill=(230, 40, 160), width=12)
            _num(d, cx - 170, ty + 10, a_, 100, BLUE)
            _num(d, cx + 170, ty + 10, b_, 100, BLUE)
            _num(d, cx, by + 50, res, 120, RED if res == "?" else BLUE)
    elif t == "boxes":
        bw, bh = 330, 120
        pos = [(W * 0.27, top + 40), (W * 0.73, top + 40), (W * 0.5, top + 330)]
        for (cx, y0), (a_, b_, r_) in zip(pos, v):
            x0 = cx - bw / 2
            d.rectangle([x0, y0, x0 + bw, y0 + bh * 2], outline=INK, width=6)
            d.line([(x0, y0 + bh), (x0 + bw, y0 + bh)], fill=INK, width=6)
            d.line([(cx, y0), (cx, y0 + bh)], fill=INK, width=6)
            _num(d, cx - bw / 4, y0 + bh / 2 + 10, a_, 86)
            _num(d, cx + bw / 4, y0 + bh / 2 + 10, b_, 86)
            _num(d, cx, y0 + bh * 1.5 + 10, r_, 92, RED if r_ == "?" else INK)
    elif t == "pies":
        r = 98
        for k, vals in enumerate(v):
            cy = top + 85 + k * 180
            cx = W * 0.36
            d.ellipse([cx - r, cy - r * 0.85, cx + r, cy + r * 0.85], outline=INK, width=6)
            d.line([(cx, cy - r * 0.85), (cx, cy)], fill=INK, width=5)
            d.line([(cx, cy), (cx - r * 0.9, cy + r * 0.45)], fill=INK, width=5)
            d.line([(cx, cy), (cx + r * 0.9, cy + r * 0.45)], fill=INK, width=5)
            _num(d, cx - 44, cy - 14, vals[0], 56)
            _num(d, cx + 44, cy - 14, vals[1], 56)
            _num(d, cx, cy + 54, vals[2], 56)
            T.draw(d, (cx + r + 40, cy - 60), "=", 100, BLUE)
            _num(d, cx + r + 230, cy + 10, vals[3], 120, RED)
    elif t == "cross":
        cx, cy, r = W / 2, mid + 20, 82
        pts = [(cx, cy - 205), (cx - 280, cy), (cx + 280, cy), (cx, cy + 205)]
        for (px, py) in pts:
            d.line([(cx, cy), (px, py)], fill=BLUE, width=10)
        for (px, py), val in zip(pts, v):
            d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 255, 255), outline=BLUE, width=9)
            _num(d, px, py + 18, val, 92)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255), outline=BLUE, width=9)
        _num(d, cx, cy + 18, "?", 100, RED)


def _body_exam(script, idx, total, out_path):
    """v2.9.4: 'Ranker' jaisa saaf exam card - bold kaale ank, laal '?', laal gol A/B/C/D, diagram. Jawab kabhi nahi."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sc = (script.get("scenes") or [{}])[idx]
    opts = [str(o) for o in (script.get("puzzle_options") or [])]
    cta_scene = bool(sc.get("answer_cta")) or idx == total - 1
    cat = script.get("cat_label") or KIND_NAME.get(script.get("puzzle_kind", ""), "दिमागी चुनौती")
    hz = 60
    while T.width(cat, hz) > W - 260 and hz > 36:
        hz -= 2
    pw = T.width(cat, hz) + 90
    d.rounded_rectangle([(W - pw) / 2, 120, (W + pw) / 2, 120 + hz * 1.7], radius=60, fill=(16, 32, 120), outline=(255, 205, 40), width=6)
    T.draw(d, ((W - T.width(cat, hz)) / 2, 120 + hz * 0.25), cat, hz, (255, 255, 255))
    y = 120 + hz * 1.7 + 40
    if cta_scene:
        txt = _clean(sc.get("show"))
        sz, lines = T.fit(txt, W - 200, 600, start=72, smallest=44)
        y = 520
        for ln in lines[:6]:
            T.draw(d, ((W - T.width(ln, sz)) / 2, y), ln, sz, INK)
            y += int(sz * 1.3)
    else:
        q = _clean(script.get("q_show") or script.get("puzzle_q") or "")
        dg = script.get("diagram")
        qz, ql = T.fit(q, W - 160, 230 if dg else 520, start=64 if dg else 96, smallest=40)
        if not dg:                               # v3.1.1 (owner ki reel 12 Nov: sab kuch upar chipka, beech ka 45% parda khaali):
            blk = len(ql[:4]) * int(qz * 1.3) + 40 + (285 if opts else 0) + 80     # sawal + vikalp + neeche ki line ki kul oonchai
            y += max(0, min(340, int((SITE_Y - 40 - y - blk) * 0.42)))             # block ko parde ke beech ki taraf khiskao
        for ln in ql[:4]:
            T.draw(d, ((W - T.width(ln, qz)) / 2, y), ln, qz, RED if dg else INK)
            y += int(qz * 1.3)
        if dg:
            _diagram(img, dg, y + 10, y + 540)
            d = ImageDraw.Draw(img)
            y += 560
        else:
            y += 40
        if opts:
            letters = "ABCD"
            cw = (W - 160) / 2
            for i, o in enumerate(opts[:4]):
                cx0 = 80 + (i % 2) * cw
                cy0 = y + (i // 2) * 135
                d.ellipse([cx0 + 20, cy0, cx0 + 130, cy0 + 110], outline=RED, width=7)
                T.draw(d, (cx0 + 75 - T.width(letters[i], 64) / 2, cy0 + 8), letters[i], 64, RED)
                oz = 84
                while T.width(o, oz) > cw - 190 and oz > 36:
                    oz -= 4
                T.draw(d, (cx0 + 160, cy0 + 55 - oz * 0.75), o, oz, INK)   # v3.1.1: B/D laal the - 'galat' jaisa ishara lagta tha; sab ek rang
                if o in _ELIM["s"]:
                    _strike(img, [cx0 + 10, cy0 - 5, cx0 + cw - 20, cy0 + 115])
                    d = ImageDraw.Draw(img)
            y += 285
        line = re.sub(r"\s*\((?:Code|कोड)\s*#\d+\)", "", _clean(sc.get("show")))
        line = re.sub(r"^(?:सवाल|प्रश्न)\s*[:：].*$", "", line).strip()
        if line and line not in q:
            lz = 56
            while lz > 34 and T.width(line, lz) > W - 140:
                lz -= 2
            if y + lz * 1.4 < SITE_Y - 10:
                T.draw(d, ((W - T.width(line, lz)) / 2, y), line[:60], lz, (16, 32, 120))
    st = full_url(script)
    fz = 40 if T.width(st, 40) < W - 200 else 32
    sw = T.width(st, fz) + 60
    d.rounded_rectangle([(W - sw) / 2, SITE_Y - 6, (W + sw) / 2, SITE_Y + fz + 18], radius=30, fill=(220, 30, 40))
    T.draw(d, ((W - T.width(st, fz)) / 2, SITE_Y), st, fz, (255, 255, 255))
    img.save(out_path)
    return out_path

def full_url(script):
    """Owner (3 Nov shaam): video/thumbnail par hamesha HOME page ka pura pata - https://sabhisaab.com/ (page wala nahi).
    v2.5.0 (owner 5 Nov): jawab website par -> sawal-reel par https://sabhisaab.com/jawab (wahi pura link)."""
    if script.get("answer_offsite"):
        from .answers import live
        return SITE.rstrip("/") + ("/jawab" if live() else "/")
    return SITE.rstrip("/") + "/"


def _thumb_opts(script, n):
    allo = script.get("puzzle_options") or []
    ans_ = script.get("puzzle_answer") or ""
    if not allo or ans_ not in allo:
        return []
    wrong = [o for o in allo if o != ans_][:n - 1]
    pair = [ans_] + wrong
    random.Random(script.get("title", "") + str(n)).shuffle(pair)    # jawab chhupa - hamesha ek jagah nahi
    return pair


def _thumb_opt_box(img, x0, y, x1, h, letter, txt, acc):
    box = [x0, y, x1, y + h]
    _glow(img, lambda dd, c: dd.rounded_rectangle(box, radius=h // 2, outline=c, width=4), acc + (255,), radius=10, strength=1)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0 + 3, y + 3, x1 - 3, y + h - 3], radius=h // 2 - 3, fill=(14, 18, 38, 232))
    r = h // 2 - 10
    d.ellipse([x0 + 10, y + 10, x0 + 10 + 2 * r, y + 10 + 2 * r], fill=acc + (255,))
    T.draw(d, (x0 + 10 + r - T.width(letter, int(r * 1.1)) / 2, y + 10 + r - r * 0.92), letter, int(r * 1.1), (10, 10, 10))
    s2, l2 = T.fit(_clean(str(txt)), x1 - x0 - 2 * r - 50, h - 20, start=int(h * 0.5), smallest=24)
    T.draw(d, (x0 + 2 * r + 34, y + h / 2 - s2 * 0.72), l2[0][:24], s2, (255, 255, 255))


def thumbnail(script, out_path, variant=0):
    """v2.3.2 PRO thumbnail 1280x720 - 3 ALAG design (owner: 'jo look final kiya tha wo sab aaye'):
    0) chitra + bada sawal + A/B   1) sirf bada sawal (badi chamak '?')   2) bada 5s timer + sawal + A/B/C.
    Jawab kabhi thumbnail par nahi; neeche pura website pata."""
    tw, th = 1280, 720
    brand = script.get("brand", "money")
    a1, a2 = _acc(brand)
    lay = variant % 3
    if variant % 2:
        a1, a2 = a2, a1
    bgp = str(out_path) + ".bg.jpg"
    background(brand, f"{script.get('title', '')}{variant}", bgp, size=(tw, th))
    img = Image.open(bgp).convert("RGBA")
    if script.get("img3d") and lay == 1:             # v2.3.3: bade-sawal wale thumbnail ke peeche apna 3D (dhundhla)
        try:
            from PIL import ImageEnhance
            b3 = Image.open(script["img3d"]).convert("RGB").resize((tw, th), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3))
            img = ImageEnhance.Brightness(b3).enhance(0.55).convert("RGBA")
        except Exception:
            pass
    _glow(img, lambda d, c: d.rounded_rectangle([12, 12, tw - 12, th - 12], radius=40, outline=c, width=6), a1 + (240,), radius=16, strength=2)
    cat = script.get("cat_label") or KIND_NAME.get(script.get("puzzle_kind"), BRAND_CAT.get(brand, "सब हिसाब"))
    q = _clean(script.get("puzzle_q") or (script.get("thumb") or {}).get("lines", [script.get("title", "")])[0])
    q = re.sub(r"#\d{3,6}|#Shorts|\*", "", q).strip()
    pk = script.get("puzzle_kind", "")
    _GRID["g"] = script.get("grid4")

    def pill(cx_or_x, centered=False, cs=32):
        cw = T.width(cat, cs)
        px = cx_or_x - (cw + 40) / 2 if centered else cx_or_x
        _glow(img, lambda dd, c: dd.rounded_rectangle([px, 34, px + cw + 40, 34 + cs + 26], radius=30, outline=c, width=4),
              a2 + (255,), radius=10, strength=1)
        dd = ImageDraw.Draw(img)
        dd.rounded_rectangle([px + 3, 37, px + cw + 37, 31 + cs + 26], radius=27, fill=(10, 12, 28, 225))
        T.draw(dd, (px + 20, 40), cat, cs, (255, 255, 255))

    if lay == 0:                                     # chitra baayein + sawal daayein + A/B
        _illustration(img, pk, brand, [40, 90, 540, 630], script.get("title", "") + "0", script.get("img3d"))
        _timer(img, 470, 150, 62, 5, a2)
        pill(570)
        sz, lines = T.fit(q, tw - 610, 320, start=84, smallest=46)
        yy = 120
        for i, ln in enumerate(lines[:4]):
            _text_glow(img, (570, yy), ln, sz, (255, 230, 60) if i == 0 else (255, 255, 255), (a1 if i == 0 else a2) + (255,), radius=8)
            yy += int(sz * 1.25)
        ops = _thumb_opts(script, 2)
        oy = max(yy + 16, 460)
        for i, o in enumerate(ops):
            bx0 = 570 + i * 330
            _thumb_opt_box(img, bx0, oy, bx0 + 316, 84, "AB"[i], o, a1)
        _text_glow(img, (570, 585), "5 सेकंड में बताइए!" if ops else "पूरा हिसाब देखिए!", 46, (255, 230, 60), a2 + (255,), radius=12)
    elif lay == 1:                                   # sirf bada sawal - beech mein, peeche chamakta '?'
        qm = Image.new("RGBA", img.size, (0, 0, 0, 0))
        T.draw(ImageDraw.Draw(qm), (tw / 2 - T.width("?", 560) / 2, -60), "?", 560, a1 + (90,))
        img.alpha_composite(qm.filter(ImageFilter.GaussianBlur(6)))
        pill(tw / 2, centered=True)
        sz, lines = T.fit(q, tw - 160, 380, start=100, smallest=52)
        tot = len(lines[:4]) * sz * 1.22
        yy = 120 + (400 - tot) / 2
        for i, ln in enumerate(lines[:4]):
            _text_glow(img, ((tw - T.width(ln, sz)) / 2, yy), ln, sz, (255, 230, 60) if i == 0 else (255, 255, 255),
                       (a1 if i == 0 else a2) + (255,), radius=10)
            yy += int(sz * 1.22)
        cta = "सही जवाब कमेंट में!" if script.get("puzzle_options") else "पूरा सच जानिए!"
        _text_glow(img, ((tw - T.width(cta, 54)) / 2, 560), cta, 54, (255, 230, 60), a2 + (255,), radius=12)
    else:                                            # bada 5s timer baayein + sawal + A/B/C
        _timer(img, 260, 330, 190, 5, a2)
        dd = ImageDraw.Draw(img)
        T.draw(dd, (260 - T.width("चैलेंज", 44) / 2, 545), "चैलेंज", 44, (255, 230, 60))
        pill(520)
        sz, lines = T.fit(q, tw - 560, 240, start=72, smallest=42)
        yy = 115
        for i, ln in enumerate(lines[:3]):
            _text_glow(img, (520, yy), ln, sz, (255, 255, 255), a1 + (255,), radius=8)
            yy += int(sz * 1.22)
        ops = _thumb_opts(script, 3)
        oy = max(yy + 14, 330)
        for i, o in enumerate(ops):
            _thumb_opt_box(img, 520, oy, tw - 60, 74, "ABC"[i], o, a1)
            oy += 88
        if not ops:
            _text_glow(img, (520, 420), "5 सेकंड में बताइए!", 54, (255, 230, 60), a2 + (255,), radius=12)
    url = full_url(script)
    uw = T.width(url, 26) + 30
    d = ImageDraw.Draw(img)
    ux = tw - 30 - uw
    d.rounded_rectangle([ux, th - 62, ux + uw, th - 24], radius=19, fill=(0, 0, 0, 170))
    T.draw(d, (ux + 15, th - 60), url, 26, (230, 240, 255))
    img.convert("RGB").save(out_path, quality=92)
    try:
        import os
        os.remove(bgp)
    except Exception:
        pass
    return out_path


def blend_3d_bg(bg_path, path3d):
    """v2.3.3: neon parat ke upar apna 3D - dhundhla aur halka andhera (sawal/vikalp saaf padhe jaayein)."""
    from PIL import ImageOps, ImageEnhance
    bg = Image.open(bg_path).convert("RGB")
    p3 = ImageOps.fit(Image.open(path3d).convert("RGB"), bg.size, Image.LANCZOS, centering=(0.5, 0.5))
    p3 = ImageEnhance.Brightness(p3.filter(ImageFilter.GaussianBlur(24))).enhance(0.42)   # v2.4.1: AI chitra ke andar ka koi likha (jaise '15. Sha') padha na jaaye
    Image.blend(bg, p3, 0.55).save(bg_path, quality=95)
    return bg_path
