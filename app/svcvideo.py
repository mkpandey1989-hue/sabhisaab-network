"""v3.6.0: SERVICES AD VIDEO - roz 1 service, har brand ka ALAG version (owner 23 Nov 2026).

Kaise:
  - Raat 01:30 ke baad (VM khali ho tab - koi video 'making' na ho) aaj ka 1 kaam chunta hai (rate list se, sabse kam chala hua).
  - 4 brand x alag LOOK (8 rang) x alag HOOK (10) x alag LAYOUT (phone baayen/daayen) - zindagi bhar ka record
    (data/services/video_history.jsonl): ek hi kaam + look + hook + layout kabhi dobara nahi, kisi bhi channel par.
  - Bade brand jaisa ad: 0-3s jhatka (hook), 3-8s phone mein asli jaisa app/site chalta hua, 8-13s 3D price (bazaar rate kata),
    13-17s 3 fayde tick, 17-20s CTA + sabhisaab.com/services-list. Awaaz = wahi brand ki awaaz (tts.py). Owner ka naam/awaaz nahi.
  - Bani video PURANE raaste se jaati hai: pipeline job (manzoori ke button, 'Abhi daalo', jawab na mile to slot par apne aap)
    -> YouTube + FB + IG + Threads + Pinterest + Telegram + Dailymotion (har platform ki apni seema ke andar).
  - Ad video par 'AI se bana' nahi likhte (owner); asli insaan/chehra nahi banate (nakli chehra = policy khatra).
Chalu/band: 'services video chalu' / 'services video band'. Namoona: 'services video namoona'.
"""
import datetime
import json
import math
import pathlib
import random
import subprocess
import time

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import state
from .config import BRANDS, DATA, FPS, W, H
from .log import log

DIR = DATA / "services"
OUT = DATA / "services_video"
ASSETS = pathlib.Path(__file__).with_name("assets")
DUR = 20.0
SITE_TXT = "sabhisaab.com/services-list"

LOOKS = {   # v3.7.0 saaf, ujla (bade app-brand ad jaisa): bg upar, bg neeche, brand rang, gehra rang
    "mint":    ("#F2FBF8", "#D7F3EA", "#0F766E", "#0B3B36"),
    "sky":     ("#F3F7FF", "#DCE7FF", "#2F54EB", "#14245C"),
    "peach":   ("#FFF6EF", "#FFE1CC", "#E8590C", "#5A2307"),
    "lemon":   ("#FFFBEA", "#FFF0B3", "#B7791F", "#4A3208"),
    "rose":    ("#FFF3F6", "#FFD9E3", "#C2255C", "#5C0F2B"),
    "lilac":   ("#F7F3FF", "#E6DBFF", "#6741D9", "#2B1A66"),
    "teal":    ("#EFFBFC", "#CFF2F5", "#0C8599", "#073B44"),
    "pahad":   ("#F1F8FB", "#D6EAF2", "#1D5A6B", "#0B2A33"),
}
HOOKS = [  # (chhota kicker, bolne ke liye)
    ("सच बताइए…", "सच बताइए,"),
    ("बस {pv} रुपये", "सिर्फ़ {pv} रुपये में"),
    ("दुकानदार ध्यान दें", "दुकानदार भाई ध्यान दीजिए,"),
    ("90% लोग यहीं चूकते हैं", "नब्बे प्रतिशत लोग यहीं चूकते हैं,"),
    ("2-3 दिन में तैयार", "दो तीन दिन में तैयार,"),
    ("ग्राहक खुद आएंगे", "ग्राहक खुद आपको ढूंढेंगे,"),
    ("अब सब फ़ोन पर", "अब सब कुछ आपके फ़ोन पर,"),
    ("रात 2 बजे भी", "रात दो बजे भी,"),
    ("महंगी एजेंसी नहीं", "महंगी एजेंसी की ज़रूरत नहीं,"),
    ("पहले डेमो, फिर पैसा", "पहले डेमो देखिए, फिर पैसा दीजिए,"),
]
# kaam ke hisaab se: (sawal line 1, line 2, hal, phone screen, 3 fayde)
CATCOPY = {
    "web":    ("दुकान अभी भी", "सिर्फ़ ऑफ़लाइन?", "आपकी अपनी वेबसाइट", "site", ["आपके नाम पर", "WhatsApp ऑर्डर", "मोबाइल पर तेज़"]),
    "soft":   ("बिल अभी भी", "हाथ से बनाते हैं?", "अपना GST बिल ऐप", "bill", ["बिल तुरंत", "स्टॉक + उधार", "फ़ोन + कंप्यूटर"]),
    "bot":    ("रात 2 बजे", "ग्राहक का मैसेज?", "24x7 जवाब देने वाला बॉट", "bot", ["24x7 जवाब", "ऑर्डर अलर्ट", "रोज़ की रिपोर्ट"]),
    "trade":  ("अपनी स्ट्रैटेजी", "पैसा लगाने से पहले?", "बैकटेस्ट + अलर्ट", "trade", ["आपकी स्ट्रैटेजी", "आपका अकाउंट", "पहले टेस्ट"]),
    "calc":   ("वेबसाइट पर", "अपना कैलकुलेटर?", "आपके ब्रांड का टूल", "calc", ["आपका लोगो", "लीड फ़ॉर्म", "वेबसाइट पर"]),
    "design": ("पोस्ट और रील", "रोज़ कौन बनाए?", "ब्रांड जैसा डिज़ाइन", "list", ["बिना शूट", "हर प्लेटफ़ॉर्म", "आपके रंग"]),
    "ecom":   ("ऑनलाइन ऑर्डर", "लेना है?", "अपनी ऑनलाइन दुकान", "menu", ["UPI पेमेंट", "WhatsApp ऑर्डर", "कम COD"]),
    "docs":   ("Excel में", "घंटों का काम?", "मिनटों में हिसाब", "bill", ["बिना ग़लती", "Excel / PDF", "रोज़ की रिपोर्ट"]),
    "setup":  ("सर्वर, डोमेन,", "होस्टिंग उलझन?", "हम सेट कर देंगे", "list", ["आपके अकाउंट पर", "पासवर्ड आपका", "स्क्रीन पर समझाएं"]),
    "guide":  ("ख़ुद सीखना", "चाहते हैं?", "स्क्रीन-शेयर पर सीखें", "list", ["आपकी भाषा", "आपका समय", "हर सवाल का जवाब"]),
    "fix":    ("वेबसाइट या फ़ॉर्म", "काम नहीं कर रहा?", "हम ठीक कर देंगे", "list", ["उसी दिन", "पहले जाँच", "फिर पैसा"]),
    "care":   ("वेबसाइट की", "देखभाल कौन करे?", "महीने का केयर प्लान", "site", ["कभी भी बंद", "बैकअप", "छोटे बदलाव"]),
    "micro":  ("छोटा काम", "बड़ी दिक्कत?", "हम कर देंगे", "list", ["उसी दिन", "छोटी फ़ीस", "सीधे WhatsApp"]),
}
ITEMCOPY = {   # khaas kaam ke apne shabd
    "m-resume":  ("नौकरी के लिए", "रिज़्यूमे चाहिए?", "रिज़्यूमे सिर्फ़ ₹10", "resume", ["साफ़ फ़ॉर्मेट", "ग़लती ठीक", "PDF उसी दिन"]),
    "m-resume2": ("रिज़्यूमे से", "इंटरव्यू नहीं आता?", "प्रो रिज़्यूमे + LinkedIn", "resume", ["प्रो डिज़ाइन", "LinkedIn बायो", "उसी दिन"]),
    "m-form":    ("ऑनलाइन फ़ॉर्म", "भरने में दिक्कत?", "हम मदद करेंगे", "list", ["नौकरी / एडमिशन", "OTP आप डालें", "डॉक्यूमेंट नहीं रखते"]),
    "s-khata":   ("उधार अभी भी", "कॉपी में?", "उधार खाता ऐप", "khata", ["हर ग्राहक का बाकी", "रिमाइंडर", "फ़ोन पर"]),
    "s-stock":   ("माल कब ख़त्म", "पता नहीं चलता?", "स्टॉक अलर्ट ऐप", "stock", ["कम माल = अलर्ट", "रोज़ का हिसाब", "फ़ोन पर"]),
    "w-book":    ("बुकिंग के लिए", "दिन भर फ़ोन?", "ऑनलाइन बुकिंग पेज", "book", ["ख़ाली स्लॉट", "WhatsApp कन्फ़र्म", "24x7"]),
    "w-menu":    ("मेन्यू कार्ड", "पुराना हो गया?", "QR मेन्यू + ऑर्डर", "menu", ["QR स्कैन", "सीधा ऑर्डर", "रेट बदलना आसान"]),
    "m-any":     ("कोई भी", "कंप्यूटर का काम?", "लिखिए, हम करेंगे", "list", ["छोटा या बड़ा", "लिखित क़ीमत", "पहले डेमो"]),
}
SHOTS = pathlib.Path(__file__).with_name("assets") / "svc"


def copy_for(item):
    return ITEMCOPY.get(item["id"]) or CATCOPY.get(item["cat"]) or CATCOPY["micro"]


# ---------------------------------------------------------------- record (lifetime)
def _hist():
    f = DIR / "video_history.jsonl"
    out = []
    if f.exists():
        for ln in f.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def _hist_add(row):
    DIR.mkdir(parents=True, exist_ok=True)
    with open(DIR / "video_history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def pick_day(seed=None):
    """Aaj ka kaam (kam chala hua, 30 din mein nahi) + 4 brand ke liye 4 alag (look, hook, layout) - zindagi bhar naya."""
    from . import svc
    R = svc.rates()
    H_ = _hist()
    used = {(h["item"], h["look"], h["hook"], h["lay"]) for h in H_}
    cnt = {}
    recent = set()
    cut = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    for h in H_:
        cnt[h["item"]] = cnt.get(h["item"], 0) + 1
        if h.get("day", "") >= cut:
            recent.add(h["item"])
    rnd = random.Random(seed or time.time())
    pool = [i for i in R["items"] if i["id"] not in recent and i["cat"] not in ("care",)] or R["items"]
    pool.sort(key=lambda i: (cnt.get(i["id"], 0), rnd.random()))
    item = pool[0]
    combos = [(lk, hk, ly) for lk in LOOKS for hk in range(len(HOOKS)) for ly in ("L", "R")
              if (item["id"], lk, hk, ly) not in used]
    rnd.shuffle(combos)
    out, seen_l, seen_h = {}, set(), set()
    for b in BRANDS:
        pref = "pahad" if b == "pahadi" else None
        c = next((x for x in combos if x[0] not in seen_l and x[1] not in seen_h and (not pref or x[0] == pref)), None) \
            or next((x for x in combos if x[0] not in seen_l and x[1] not in seen_h), None) or (combos[0] if combos else None)
        if not c:
            continue
        combos.remove(c)
        seen_l.add(c[0])
        seen_h.add(c[1])
        out[b] = {"look": c[0], "hook": c[1], "lay": c[2]}
    return item, out


# ---------------------------------------------------------------- drawing helpers
def _font(size, weight="ExtraBold"):
    f = ImageFont.truetype(str(ASSETS / "Baloo2.ttf"), size, layout_engine=ImageFont.Layout.RAQM)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def _back(t):
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def _tick(d, cx, cy, r, color=(20, 20, 20)):
    d.line([(cx - r * .55, cy), (cx - r * .15, cy + r * .45), (cx + r * .6, cy - r * .45)], fill=color,
           width=max(4, int(r * .28)), joint="curve")


def _fit(text, size, maxw, weight="ExtraBold"):
    f = _font(size, weight)
    while size > 30 and f.getlength(text) > maxw:
        size -= 4
        f = _font(size, weight)
    return f


def _bg(look):
    top, bot = _hex(LOOKS[look][0]), _hex(LOOKS[look][1])
    g = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / H
        g.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3)))
    im = g.resize((W, H)).convert("RGBA")
    d = ImageDraw.Draw(im)
    dot = tuple(max(0, c - 22) for c in bot)
    for y in range(40, H, 56):                       # halki bindi-jaali (saaf premium look)
        for x in range(40, W, 56):
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(*dot, 90))
    return im


_SH = {}


def _card(im, box, r=40, fill=(255, 255, 255), shadow=26):
    """Safed card + naram parchhai (parchhai size ke hisaab se cache - tez)."""
    x0, y0, x1, y1 = (int(v) for v in box)
    w, h = x1 - x0, y1 - y0
    key = (w, h, r, shadow)
    sh = _SH.get(key)
    if sh is None:
        pad = 50
        sh = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 14, pad + w, pad + h + 14), r, fill=(0, 0, 0, shadow * 3))
        sh = sh.filter(ImageFilter.GaussianBlur(22))
        if len(_SH) > 200:
            _SH.clear()
        _SH[key] = sh
    px, py = x0 - 50, y0 - 50
    if px >= 0 and py >= 0 and px + sh.width <= im.width and py + sh.height <= im.height:
        im.alpha_composite(sh, (px, py))
    ImageDraw.Draw(im).rounded_rectangle((x0, y0, x1, y1), r, fill=fill)


def _phone_shot(key, t_scroll, ph_w=560):
    """Asli demo ka screenshot phone frame mein, dheere scroll hota hua."""
    sw = ph_w - 36
    shot = _SH.get(("shot", key, sw))
    if shot is None:
        f = SHOTS / f"{key}.jpg"
        shot = Image.open(f).convert("RGB") if f.exists() else Image.new("RGB", (520, 900), (245, 247, 248))
        shot = shot.resize((sw, int(shot.height * sw / shot.width)), Image.LANCZOS)
        _SH[("shot", key, sw)] = shot
    sh_h = int(ph_w * 1.9) - 36
    off = int(max(0, shot.height - sh_h) * _ease(t_scroll))
    view = Image.new("RGB", (sw, sh_h), (255, 255, 255))
    view.paste(shot.crop((0, off, sw, min(shot.height, off + sh_h))), (0, 0))
    ph = Image.new("RGBA", (ph_w + 80, int(ph_w * 1.9) + 80), (0, 0, 0, 0))
    sd = Image.new("RGBA", ph.size, (0, 0, 0, 0))
    ImageDraw.Draw(sd).rounded_rectangle((40, 58, ph_w + 40, int(ph_w * 1.9) + 58), 64, fill=(0, 0, 0, 110))
    ph.alpha_composite(sd.filter(ImageFilter.GaussianBlur(24)))
    d = ImageDraw.Draw(ph)
    d.rounded_rectangle((40, 40, ph_w + 40, int(ph_w * 1.9) + 40), 64, fill=(20, 22, 26))
    m = Image.new("L", view.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, *view.size), 46, fill=255)
    ph.paste(view, (58, 58), m)
    d.rounded_rectangle((40 + ph_w // 2 - 70, 70, 40 + ph_w // 2 + 70, 92), 11, fill=(20, 22, 26))
    return ph


def _marker(im, xy, text, font, brand, dark):
    """Highlight-marker wala shabd (bade ad jaisa)."""
    d = ImageDraw.Draw(im)
    bx = d.textbbox(xy, text, font=font, anchor="mm")
    pad = 18
    d.rounded_rectangle((bx[0] - pad, bx[1] - pad // 2, bx[2] + pad, bx[3] + pad // 2), 18, fill=brand)
    d.text(xy, text, font=font, fill=(255, 255, 255), anchor="mm")


# ---------------------------------------------------------------- one frame
def frame(item, v, t, brand, cache):
    look, lay = v["look"], v["lay"]
    c1, c2, br, dk = (_hex(c) for c in LOOKS[look])
    q1, q2, sol, shot, ben = copy_for(item)
    if "bg" not in cache:
        cache["bg"] = _bg(look)
    im = cache["bg"].copy()
    d = ImageDraw.Draw(im)
    side = 1 if lay == "R" else -1
    kick = HOOKS[v["hook"]][0].format(pv=f"{item['price']:,}")
    # upar: brand chip + progress patti (har frame)
    d.rounded_rectangle((60, 70, 60 + int((W - 120) * min(1, t / DUR)), 78), 4, fill=br)
    # S1 0-2.8: sawal
    if t < 2.8:
        k = _back(t / .55)
        f_k = _font(52, "SemiBold")
        d.text((W // 2, 620), kick, font=f_k, fill=br, anchor="mm")
        f = _fit(max(q1, q2, key=len), int(132 * max(.25, k)), W - 120)
        d.text((W // 2, 800), q1, font=f, fill=dk, anchor="mm")
        _marker(im, (W // 2, 970), q2, f, br, dk)
        if t > 1.2:
            d = ImageDraw.Draw(im)
            d.polygon([(W // 2 - 40, 1150), (W // 2 + 40, 1150), (W // 2, 1210)], fill=br)
    # S2 2.6-8.2: hal + asli phone
    if 2.6 <= t < 16.6:
        k = _ease((t - 2.6) / .6)
        f_s = _fit(sol, 92, W - 120)
        ytxt = 300 if t < 8.0 else 300
        d.text((W // 2, ytxt), sol, font=f_s, fill=dk, anchor="mm")
        chip = "असली डेमो · sabhisaab.com"
        fc = _font(34, "SemiBold")
        cw = fc.getlength(chip) + 60
        d.rounded_rectangle((W // 2 - cw // 2, 380, W // 2 + cw // 2, 440), 30, fill=(255, 255, 255))
        d.text((W // 2, 410), chip, font=fc, fill=br, anchor="mm")
        key = ("ph", int((t - 2.6) * 6))
        ph = cache.get(key)
        if ph is None:
            ph = _phone_shot(shot, min(1, max(0, (t - 3.4) / 4.6)))
            cache.clear() if len(cache) > 40 else None
            cache["bg"] = cache.get("bg") or _bg(look)
            cache[key] = ph
        sc = .98 if t < 8.0 else .98 - .24 * _ease((t - 8.0) / .6)
        phs = ph.resize((int(ph.width * sc), int(ph.height * sc)), Image.BILINEAR)
        cx = W // 2 if t < 8.0 else int(W // 2 + side * 240 * _ease((t - 8.0) / .6))
        y0 = 480 + int((1 - k) * 900)
        if t >= 8.0:
            y0 = int(480 + 380 * _ease((t - 8.0) / .6))  # 860 tak
        im.alpha_composite(phs, (cx - phs.width // 2, y0))
        d = ImageDraw.Draw(im)
    # S3 8-16.6: daam card (phone ke bagal mein)
    if 8.0 <= t < 16.6:
        k = _back((t - 8.0) / .6)
        cx = W // 2 - side * 250
        x0, x1 = cx - 230, cx + 230
        _card(im, (x0, 560, x1, 900), 44)
        d = ImageDraw.Draw(im)
        d.text((cx, 620), "सिर्फ़", font=_font(44, "SemiBold"), fill=dk, anchor="mm")
        fp = _fit(f"₹{item['price']:,}", int(150 * max(.2, k)), 420)
        d.text((cx, 720), f"₹{item['price']:,}", font=fp, fill=br, anchor="mm")
        d.text((cx, 820), "से शुरू", font=_font(44, "SemiBold"), fill=dk, anchor="mm")
        if t > 8.9:
            mk = f"बाज़ार में ₹{item['market'][0]:,}+"
            fm = _font(38, "SemiBold")
            d.text((cx, 950), mk, font=fm, fill=(120, 120, 120), anchor="mm")
            bx = d.textbbox((cx, 950), mk, font=fm, anchor="mm")
            d.line((bx[0], (bx[1] + bx[3]) // 2, bx[0] + (bx[2] - bx[0]) * _ease((t - 8.9) / .5), (bx[1] + bx[3]) // 2),
                   fill=(224, 49, 49), width=6)
        # S4 fayde (daam ke neeche)
        for i, b in enumerate(ben):
            kk = _ease((t - 11.0 - i * .45) / .45)
            if kk <= 0:
                continue
            yb = 1040 + i * 132
            xa = x0 + int((1 - kk) * -side * 500)
            _card(im, (xa, yb, xa + 460, yb + 104), 52, shadow=14)
            d = ImageDraw.Draw(im)
            d.ellipse((xa + 16, yb + 16, xa + 88, yb + 88), fill=br)
            _tick(d, xa + 52, yb + 52, 22, (255, 255, 255))
            d.text((xa + 108, yb + 52), b, font=_fit(b, 44, 330, "SemiBold"), fill=dk, anchor="lm")
        nm = item["name"] if len(item["name"]) < 44 else item["name"][:42] + "…"
        d.text((W // 2, 1790), nm, font=_fit(nm, 40, W - 140, "Medium"), fill=dk, anchor="mm")
    # S5 16.4-20: CTA (brand rang par safed)
    if t >= 16.4:
        k = _ease((t - 16.4) / .45)
        ov = Image.new("RGBA", (W, H), (*br, int(255 * k)))
        im.alpha_composite(ov)
        d = ImageDraw.Draw(im)
        kb = _back((t - 16.5) / .6)
        d.text((W // 2, 560), BRANDS[brand]["name"], font=_font(54, "SemiBold"), fill=(255, 255, 255), anchor="mm")
        d.text((W // 2, 720), "अपना काम लिखिए", font=_font(int(120 * max(.2, kb))), fill=(255, 255, 255), anchor="mm")
        d.text((W // 2, 850), "लिस्ट में नहीं? कोई भी काम — बताइए", font=_font(50, "SemiBold"), fill=(255, 255, 255), anchor="mm")
        pul = 1 + .035 * math.sin(t * 7)
        bw, bh = int(900 * pul), int(140 * pul)
        _card(im, (W // 2 - bw // 2, 980, W // 2 + bw // 2, 980 + bh), 70, shadow=30)
        d = ImageDraw.Draw(im)
        d.text((W // 2, 980 + bh // 2), SITE_TXT, font=_font(56), fill=br, anchor="mm")
        d.text((W // 2, 1230), "पहले डेमो  ·  2 बदलाव  ·  आपके नाम पर", font=_font(44, "SemiBold"),
               fill=(255, 255, 255), anchor="mm")
        d.text((W // 2, 1330), f"रिज़्यूमे ₹10 से  ·  फ़ॉर्म मदद ₹49", font=_font(44, "SemiBold"), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, H - 60), BRANDS[brand]["name"] + " · Services", font=_font(34, "SemiBold"),
           fill=(255, 255, 255) if t >= 16.6 else dk, anchor="mm")
    return im.convert("RGB")


# ---------------------------------------------------------------- audio + video
def voice_text(item, v):
    q1, q2, sol, _, ben = copy_for(item)
    hk = HOOKS[v["hook"]][1].format(pv=item["price"])
    return (f"{hk} {q1} {q2} {sol}. सिर्फ़ {item['price']} रुपये से शुरू। {ben[0]}, {ben[1]}, {ben[2]}। "
            f"लिस्ट में नहीं है तो कोई भी काम लिखिए। सब हिसाब डॉट कॉम स्लैश सर्विसेज़ लिस्ट।")


def render_variant(item, v, brand, out_dir):
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    wav = out_dir / "voice.wav"
    try:
        from . import tts
        vdur = tts.synth(voice_text(item, v), str(wav), 0, 1)
    except Exception as e:
        log(f"svcvideo tts: {e}")
        vdur = 0
        wav = None
    dur = max(DUR, vdur + 1.5)
    n = int(dur * FPS)
    mp4 = out_dir / "video.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-"]
    if wav:
        cmd += ["-i", str(wav), "-filter_complex", f"[1:a]apad,atrim=0:{dur:.2f},loudnorm=I=-14:TP=-1.5[a]", "-map", "0:v",
                "-map", "[a]", "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-threads", "2",
            "-movflags", "+faststart", "-t", f"{dur:.2f}", str(mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cache, thumbs = {}, []
    want = {int(1.5 * FPS): "t1.jpg", int(10.5 * FPS): "t2.jpg", int((dur - 1.5) * FPS): "t3.jpg"}
    for i in range(n):
        t = i / FPS
        tl = t if t < 16.8 else 16.8 + (t - 16.8) * (DUR - 16.8) / max(.01, dur - 16.8)   # lambi awaaz = CTA lamba
        fr = frame(item, v, min(tl, DUR - .01), brand, cache)
        if i in want:
            fr.save(out_dir / want[i], quality=92)
            thumbs.append(str(out_dir / want[i]))
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg fail")
    return str(mp4), sorted(thumbs), dur


def meta_for(item, v, brand, video, thumbs, dur):
    hook_s = HOOKS[v["hook"]][0].format(n=item["name"], p=f"{item['price']:,}")
    title = f"{hook_s} | {item['name'][:48]} ₹{item['price']:,} se"[:95]
    risk = ("\n⚠️ Sirf aapki apni strategy ka code - koi tip/signal/munafe ka vaada nahi. Bot aapke account par aap chalate hain."
            if item.get("risk") == "Y" else "")
    desc = (f"{item['name']} - ₹{item['price']:,} se shuru (bazaar mein ₹{item['market'][0]:,}+).\n"
            f"✓ Pehle demo, phir payment  ✓ 2 badlav shaamil  ✓ Code aur account aapke naam\n"
            f"List mein nahi? Apna CUSTOM kaam likhiye - website, billing app, bot, calculator, design, ₹10 ke chhote kaam bhi.\n"
            f"Rate list + live demo: {SITE_TXT}{risk}\n{BRANDS[brand]['tags']} #SabHisaabServices")
    return {"video": video, "thumbs": thumbs, "duration": dur, "title": title, "description": desc, "brand": brand,
            "page": "/services-list", "format": "short", "tags": ["sabhisaab services", item["name"], "website banwaye",
                                                                 "billing app", "dukaan online"],
            "design": "services_ad", "svc_item": item["id"], "svc_look": v["look"], "svc_hook": v["hook"],
            "svc_lay": v["lay"], "topic": item["name"]}


# ---------------------------------------------------------------- daily job (purane pipeline ke raaste)
def _slot(brand):
    from . import pipeline
    sl = [s.strip() for s in str(pipeline.schedule().get(brand, "")).split(",") if s.strip()]
    if len(sl) >= 2:
        a = [int(x) for x in sl[0].split(":")]
        b = [int(x) for x in sl[1].split(":")]
        m = ((a[0] * 60 + a[1]) + (b[0] * 60 + b[1])) // 2
    else:
        m = 15 * 60
    m = 15 * 60 if m < 10 * 60 else m
    return pipeline.now().replace(hour=m // 60, minute=(m % 60) // 5 * 5, second=0, microsecond=0)


def make_day(sample=False, only=None):
    """Aaj ka kaam -> 4 brand ka alag video -> pipeline job (manzoori / slot par apne aap). sample=True: sirf dikhana."""
    from . import pipeline, tg
    item, plan = pick_day()
    made = []
    for brand, v in plan.items():
        if only and brand != only:
            continue
        jid = f"svc{brand[:2]}{datetime.datetime.now().strftime('%m%d%H%M')}"
        out = OUT / jid
        try:
            video, thumbs, dur = render_variant(item, v, brand, out)
        except Exception as e:
            log(f"svcvideo {brand}: {e}")
            tg.alert("yellow", f"🎬 Services video ({BRANDS[brand]['name']}) nahi bani: {str(e)[:120]}")
            continue
        meta = meta_for(item, v, brand, video, thumbs, dur)
        (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        if not sample:
            _hist_add({"day": str(datetime.date.today()), "item": item["id"], "look": v["look"], "hook": v["hook"],
                       "lay": v["lay"], "brand": brand, "jid": jid})
        slot = _slot(brand)
        if slot < pipeline.now():
            slot += datetime.timedelta(days=1) if not sample else datetime.timedelta(0)
        pipeline.save_job(jid, {"brand": brand, "status": "waiting", "slot": slot.isoformat(),
                                "created": pipeline.now().isoformat(),
                                "reason": "test video" if sample else "roz ka schedule", "meta": str(out),
                                "title": meta["title"], "topic_key": f"svc:{item['id']}:{v['look']}:{v['hook']}",
                                "topic_kind": "services", "style": "services_ad"})
        pipeline._send_for_approval(jid, meta, [("✅", "services ad: rate list se, nakli daava nahi")])
        made.append(jid)
    return item, made


def tick(run):
    """bot.scheduler se: raat 01:30-05:00 ke beech, koi doosri video 'making' na ho tab, din mein ek baar."""
    if not state.get("svc_video_on"):
        return
    from . import pipeline
    n = pipeline.now()
    d = str(n.date())
    if state.get("svc_video_day") == d or not ("01:30" <= n.strftime("%H:%M") <= "05:00"):
        return
    if any(j.get("status") == "making" for j in pipeline.jobs().values()):
        return                                   # VM busy - agle chakkar mein
    state.put("svc_video_day", d)
    run(make_day)


def on_text(t, run):
    from . import tg, pipeline
    tl = t.lower().strip()
    if tl == "services video chalu":
        state.put("svc_video_on", True)
        mu = pipeline.max_uploads()
        if mu < 14:
            state.put("max_uploads", 14)          # roz 8 purani + 4 services (+2 jagah) - owner ka hukum, isi command se
        return tg.say("✅ Services video CHALU: roz raat 01:30 ke baad (VM khali ho tab) 4 brand ke 4 alag video, namoona "
                      "Telegram par, jawab na mila to apne slot par apne aap. Upload seema 14/din. Band: 'services video band'.")
    if tl == "services video band":
        state.put("svc_video_on", False)
        return tg.say("⏸ Services video band.")
    if tl in ("services video namoona", "services video sample"):
        tg.say("🎬 Services namoona ban raha hai (Pahadi brand, 2-4 min)... ye kahin post nahi hoga jab tak aap button na dabayein.")
        run(lambda: make_day(sample=True, only="pahadi"))
        return True
    if tl in ("services video report", "services video haal"):
        H_ = _hist()
        last = H_[-8:]
        return tg.say(f"🎬 Services video: kul {len(H_)} bani (zindagi bhar ka record, dohrav 0)\n" +
                      "\n".join(f"{h['day']} {h['brand']}: {h['item']} · {h['look']} · hook {h['hook']}" for h in last)
                      + "\nViews/lead: 'services report 7' (code/source ke saath)")
    return None
