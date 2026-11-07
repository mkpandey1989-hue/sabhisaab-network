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


def background(brand, seed, out_path, size=(W, H)):
    """Gehra neeli-baingani parat + neon perspective grid + chamakti rekhaayein + bokeh. Har video alag (seed)."""
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
LAYOUTS = {"list": "Vikalp line mein (purana)", "grid": "Vikalp 2x2 khane", "big3d": "Bada chitra, chhota card"}
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
    return y + 2 * (bh + gap)


def _options(img, y, opts, ans, acc, reveal):
    if _LAY["l"] == "grid" and len(opts) == 4:
        return _options_grid(img, y, opts, ans, acc, reveal)
    d = ImageDraw.Draw(img)
    letters = "ABCD"
    for i, o in enumerate(opts[:4]):
        ok = reveal and str(o).strip() == str(ans).strip()
        bar_col = (0, 200, 110) if ok else ((70, 74, 96) if reveal else acc)
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
    gx, gy, c = cx - side // 2, cy - side // 2, side // 4
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([gx - 8, gy - 8, gx + side + 8, gy + side + 8], radius=18, fill=(10, 14, 32, 235))
    for i in range(4):
        for j in range(4):
            v = str(g[i][j])
            bx, by = gx + j * c, gy + i * c
            q_ = v == "?"
            d.rounded_rectangle([bx + 4, by + 4, bx + c - 4, by + c - 4], radius=10,
                                fill=(255, 230, 60, 255) if q_ else (24, 30, 60, 255), outline=a1 + (200,), width=2)
            fz = int(c * 0.55)
            T.draw(d, (bx + c / 2 - T.width(v, fz) / 2, by + c / 2 - fz * 0.75), v, fz, (20, 20, 20) if q_ else (255, 255, 255))
    for k in (0, 2, 4):
        d.line([(gx + k * c, gy), (gx + k * c, gy + side)], fill=a2 + (255,), width=5)
        d.line([(gx, gy + k * c), (gx + side, gy + k * c)], fill=a2 + (255,), width=5)


def _illustration(img, kind, brand, box, seed, path3d=None):
    """Har puzzle ka apna neon chitra (CPU par, apna banaya - koi copyright chitra nahi). v2.3.3: 3D ho to wahi."""
    if kind == "sudoku4" and _GRID.get("g"):          # v2.3.4: sudoku ka asli 4x4 jaal (3D ki jagah)
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
    brand = script.get("brand", "money")
    a1, a2 = _acc(brand)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sc = (script.get("scenes") or [{}])[idx]
    kind = _scene_kind(sc, idx, total, script)
    pk = script.get("puzzle_kind", "")
    _frame(img, a1)
    cat = script.get("cat_label") or KIND_NAME.get(pk, BRAND_CAT.get(brand, "सब हिसाब"))
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
            _timer(img, W - 150, y + 90, 80, think, a2)
            cta = "कमेंट में जवाब दो!"
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
        cta = {"question": "पूरा देखो, फिर बताओ!", "trick": "2 सेकंड की ट्रिक", "cta": "फ्री टूल: sabhisaab.com",
               "info": "ध्यान से देखो"}.get(kind, "")
        if sc.get("answer_cta"):
            cta = "लिंक: डिस्क्रिप्शन / बायो में"
    if cta:
        cz = 66
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
        _text_glow(img, (570, 585), "5 सेकंड में बताओ!" if ops else "पूरा हिसाब देखो!", 46, (255, 230, 60), a2 + (255,), radius=12)
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
            _text_glow(img, (520, 420), "5 सेकंड में बताओ!", 54, (255, 230, 60), a2 + (255,), radius=12)
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
