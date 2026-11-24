"""v3.8.0: SERVICES AD VIDEO (owner 24 Nov 2026) - "Koi bhi digital kaam — ho jayega".

Kya badla (v3.7.0 se):
  - Ek video = 6 alag kaam (2 madad/form, 1 mobile-computer madad, 3 banana) -> dekhne wale ko lage "koi bhi kaam ho jata hai".
    Har kaam ka asli rate (rate list se), bazaar rate kata hua, ek fayda, aur chhoti asli/namoona screen.
  - Roz 4 ALAG video, IST 05:00 · 07:00 · 18:00 · 20:00 (har slot ek brand, brand roz badalta). Purana brand schedule nahi chheda.
  - Har video ka rang/hook/layout/kaam-set alag - zindagi bhar ka record (data/services/video_history.jsonl), dohrav nahi.
  - Season: kisi sarkari last date (svc.season_due, sirf .gov.in/.nic.in source) se 7 din pehle us din ki video usi kaam se shuru.
  - Sale: hafte ki sachchi sale (svc.offer) ho to asli rakam + asli khatam date.
  - Screen par: "Hindi mein likhiye, jaise ghar mein bolte hain" + referral "dost ke bill ka 10% aapka".
  - PUBLISH SE PEHLE 5 ROUND AUDIT (audit_video): 1 tathya (rate/date) 2 niyam/mana shabd 3 dikhawat (har text frame ke andar,
    aapas mein na chadhe, kaali frame nahi, toota akshar nahi) 4 awaaz (hai, lambai, chup nahi) 5 owner ✅ (purana manzoori raasta).
    1-4 mein ek bhi fail = video RUKI, owner ko wajah.
  - Ad par 'AI' / 'insaan' / owner ka naam kabhi nahi. Instagram par link/DM bulawa nahi (sirf "comment mein kaam likhiye").
Chalu/band: 'services video chalu' / 'services video band'. Namoona: 'services video namoona'.
"""
import datetime
import json
import math
import pathlib
import random
import re
import subprocess
import time

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import state
from .config import BRANDS, DATA, FPS, W, H
from .log import log

DIR = DATA / "services"
OUT = DATA / "services_video"
ASSETS = pathlib.Path(__file__).with_name("assets")
SHOTS = ASSETS / "svc"
SITE_TXT = "sabhisaab.com/services-list"
TAG1, TAG2 = "कोई भी डिजिटल काम", "हो जाएगा"
SLOTS = ["05:00", "07:00", "18:00", "20:00"]
CODES = {"deals": "LABH10", "sunonatak": "NATAK10", "money": "MONEY10", "pahadi": "PAHADI10"}   # svc.price ke brand code (kis brand se kaam aaya)          # owner 24 Nov: services video jaane ka samay (IST)
N_KAAM = 6
T_HOOK, T_TAG, T_K = 2.6, 2.0, 2.7                   # hook, tagline, har kaam
T_LIST0 = T_HOOK + T_TAG                             # 4.6
T_HINDI = T_LIST0 + N_KAAM * T_K                     # 20.8
T_CTA = T_HINDI + 3.4                                # 24.2
DUR = T_CTA + 4.6                                    # 28.8 (bina awaaz ka default)
GAP = 0.35                                           # v3.8.2: har vakya ke baad saans (pehle poora script ek saans mein, tez)


# v3.8.5 SHABDKOSH (owner: "Google aur jagah check karke jo asli likhte hain"): Hindi akhbaar/site (Prabhat Khabar, Canva,
# Visme, ResumeGyani...) "रिज्यूमे" likhte hain; English se aaye shabd bina nukta (फॉर्म, फोटो, साइज). Screen + awaaz dono par.
# Owner jod sakta hai: 'services shabd <galat> = <sahi>' (state svc_word_fix) - sabse upar.
WORDS = {"रिज़्यूमे": "रिज्यूमे", "रिज़्यूम": "रिज्यूमे", "रिज्यूम": "रिज्यूमे", "रेज़्यूमे": "रिज्यूमे", "फ़ॉर्म": "फॉर्म", "फ़ोटो": "फोटो",
         "फ़ोटो-साइन": "फोटो-साइन", "साइज़": "साइज", "फ़ोन": "फोन", "सर्विसेज़": "सर्विसेज", "ज़रूरी": "जरूरी", "बाज़ार": "बाजार",
         "सिर्फ़": "सिर्फ", "डिज़ाइन": "डिजाइन", "ज़्यादा": "ज्यादा", "हफ़्ते": "हफ्ते", "आख़िरी": "आखिरी", "तारीख़": "तारीख",
         "ग़लती": "गलती", "ख़त्म": "खत्म", "फ़ीस": "फीस", "प्रोफ़ेशनल": "प्रोफेशनल", "ऑफ़र": "ऑफर", "ज़": "ज"}
SAY_FIX = {"सर्विसेज़": "सर्विसेज"}
_DEV = "\u0900-\u097F"


def fix_words(t):
    """Poore shabd badlo (shabd ke beech nahi): owner ka shabdkosh pehle, phir WORDS."""
    t = str(t or "")
    table = {**WORDS, **(state.get("svc_word_fix") or {})}
    for a in sorted(table, key=len, reverse=True):
        if len(a) <= 1:
            continue
        t = re.sub(f"(?<![{_DEV}]){re.escape(a)}(?![{_DEV}])", table[a], t)
    return t


def say_clean(text):
    """v3.8.3: bolne ke liye saaf Hindi - nukta (़) hatao, angrezi shabd ki aam Hindi boli (resume -> रिज्यूम),
    owner ke sudhar (services awaaz sudhar X = Y) sabse upar."""
    t = fix_words(text)
    for a, b in (state.get("svc_say_fix") or {}).items():
        t = t.replace(a, b)
    for a, b in SAY_FIX.items():
        t = t.replace(a, b)
    return t.replace("\u093c", "")


def make_tl(d=None):
    """Scene ka samay. d = har hisse ki awaaz ki lambai {hook, tag, k0..k5, hindi, cta}. Scene kabhi awaaz se chhota nahi."""
    d = d or {}
    out, t = {}, 0.0
    for key, base in [("hook", T_HOOK), ("tag", T_TAG)] + [(f"k{i}", T_K) for i in range(N_KAAM)] + [("hindi", 3.4), ("cta", 4.6)]:
        ln = max(base, (d.get(key) or 0) + GAP + (0.6 if key == "cta" else 0))
        out[key] = (round(t, 3), round(t + ln, 3))
        t += ln
    out["dur"] = round(t, 3)
    return out

LOOKS = {   # saaf, ujla: bg upar, bg neeche, brand rang, gehra rang
    "mint":    ("#F2FBF8", "#D7F3EA", "#0F766E", "#0B3B36"),
    "sky":     ("#F3F7FF", "#DCE7FF", "#2F54EB", "#14245C"),
    "peach":   ("#FFF6EF", "#FFE1CC", "#B8400B", "#5A2307"),
    "lemon":   ("#FFFBEA", "#FFF0B3", "#8A5A12", "#4A3208"),
    "rose":    ("#FFF3F6", "#FFD9E3", "#B01F52", "#5C0F2B"),
    "lilac":   ("#F7F3FF", "#E6DBFF", "#6741D9", "#2B1A66"),
    "teal":    ("#EFFBFC", "#CFF2F5", "#0B6B7A", "#073B44"),
    "pahad":   ("#F1F8FB", "#D6EAF2", "#1D5A6B", "#0B2A33"),
    "coral":   ("#FFF5F3", "#FFDCD5", "#A8380A", "#4D1A06"),
    "forest":  ("#F2FAF3", "#D3EFD8", "#1F6E30", "#0E3317"),
    "indigo":  ("#F4F5FF", "#DADDFF", "#3049C9", "#1B2154"),
    "plum":    ("#FCF4FB", "#F3D9EE", "#A61E4D", "#45102A"),
}
HOOKS = [  # (screen kicker, bolne ke liye) - sach, bina nakli jaldi
    ("सच बताइए…", "सच बताइए,"),
    ("एक मिनट रुकिए", "एक मिनट रुकिए,"),
    ("ये आपके लिए है", "ये आपके लिए है,"),
    ("शर्म की बात नहीं", "इसमें शर्म की कोई बात नहीं,"),
    ("घर बैठे", "घर बैठे,"),
    ("छोटा हो या बड़ा", "काम छोटा हो या बड़ा,"),
    ("₹10 से शुरू", "सिर्फ़ दस रुपये से शुरू,"),
    ("आपकी भाषा में", "आपकी अपनी भाषा में,"),
    ("पहले बात, फिर काम", "पहले बात, फिर काम,"),
    ("मोबाइल हो या कंप्यूटर", "मोबाइल हो या कंप्यूटर,"),
]
# kaam: (screen naam, chhota group, dard-sawal line1, line2, ek fayda, screen key, bolne ka naam)
KAAM = {
    "m-resume":  ("रिज़्यूमे", "बनाना", "नौकरी के लिए", "रिज़्यूमे चाहिए?", "उसी दिन PDF", "resume", "रिज़्यूमे"),
    "m-form":    ("ऑनलाइन फ़ॉर्म मदद", "मदद", "ऑनलाइन फ़ॉर्म", "भरना मुश्किल लगता है?", "OTP आप ही डालें", "form", "ऑनलाइन फ़ॉर्म में मदद"),
    "m-scholar": ("स्कॉलरशिप फ़ॉर्म", "मदद", "स्कॉलरशिप का फ़ॉर्म", "समझ नहीं आता?", "डॉक्यूमेंट लिस्ट साथ", "form", "स्कॉलरशिप फ़ॉर्म"),
    "m-yojana":  ("किसान / पेंशन आवेदन", "मदद", "योजना का आवेदन", "कैसे करें?", "आप सामने, हम साथ", "form", "योजना के आवेदन में मदद"),
    "m-exam":    ("परीक्षा / नौकरी फ़ॉर्म", "मदद", "नौकरी का फ़ॉर्म", "फ़ोटो साइज़ में अटका?", "फ़ोटो-साइन सही साइज़", "form", "नौकरी फ़ॉर्म"),
    "m-docs":    ("फ़ोटो-साइन साइज़", "मदद", "फ़ोटो का साइज़", "रिजेक्ट हो जाता है?", "सही KB, सही साइज़", "docs", "फ़ोटो साइन साइज़"),
    "m-itr1":    ("ITR-1 मदद", "मदद", "ITR भरना है", "पर डर लगता है?", "आप लॉगिन, हम साथ", "itr", "आई टी आर वन में मदद"),
    "m-mobile":  ("मोबाइल / कंप्यूटर मदद", "मोबाइल-कंप्यूटर", "फ़ोन की सेटिंग", "उलझ गई है?", "कॉल या स्क्रीन-शेयर", "phone", "मोबाइल और कंप्यूटर मदद"),
    "m-study":   ("प्रोजेक्ट / PPT", "बनाना", "कॉलेज प्रोजेक्ट", "कल जमा करना है?", "साफ़ डिज़ाइन", "ppt", "प्रोजेक्ट और पी पी टी"),
    "m-letter":  ("आवेदन / पत्र", "बनाना", "आवेदन पत्र", "लिखना नहीं आता?", "सही भाषा", "letter", "आवेदन पत्र"),
    "m-biodata": ("शादी बायोडाटा", "बनाना", "शादी का बायोडाटा", "सुंदर चाहिए?", "सुंदर डिज़ाइन", "resume", "शादी बायोडाटा"),
    "m-typing":  ("हिंदी / इंग्लिश टाइपिंग", "बनाना", "हाथ का लिखा", "टाइप करवाना है?", "साफ़ टाइपिंग", "letter", "टाइपिंग"),
    "s-bill":    ("GST बिल ऐप", "बनाना", "बिल अभी भी", "हाथ से बनाते हैं?", "बिल तुरंत", "bill", "जी एस टी बिल ऐप"),
    "s-khata":   ("उधार खाता ऐप", "बनाना", "उधार अभी भी", "कॉपी में?", "हर ग्राहक का बाकी", "khata", "उधार खाता ऐप"),
    "s-stock":   ("स्टॉक ऐप", "बनाना", "माल कब ख़त्म", "पता नहीं चलता?", "कम माल = अलर्ट", "stock", "स्टॉक ऐप"),
    "w-1page":   ("दुकान की वेबसाइट", "बनाना", "दुकान अभी भी", "सिर्फ़ ऑफ़लाइन?", "आपके नाम पर", "site", "दुकान की वेबसाइट"),
    "w-book":    ("बुकिंग पेज", "बनाना", "बुकिंग के लिए", "दिन भर फ़ोन?", "24 घंटे बुकिंग", "book", "बुकिंग पेज"),
    "w-menu":    ("QR मेन्यू", "बनाना", "मेन्यू कार्ड", "पुराना हो गया?", "QR से ऑर्डर", "menu", "क्यू आर मेन्यू"),
    "d-logo":    ("लोगो", "बनाना", "दुकान का", "लोगो नहीं है?", "आपके रंग", "list", "लोगो"),
    "b-wa":      ("WhatsApp ऑटो-जवाब", "बनाना", "ग्राहक के मैसेज", "छूट जाते हैं?", "अपने आप जवाब", "bot", "व्हाट्सऐप ऑटो जवाब"),
    "c-calc":    ("अपना कैलकुलेटर", "बनाना", "वेबसाइट पर", "अपना टूल?", "आपका लोगो", "calc", "अपना कैलकुलेटर"),
}
GROUP_NEED = {"मदद": 2, "मोबाइल-कंप्यूटर": 1, "बनाना": 3}

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


def _key(row):
    return (tuple(sorted(row.get("set") or [row.get("item")])), row.get("look"), row.get("hook"), row.get("lay"))


def pick_day(seed=None, day=None):
    """Aaj ke 4 video: har brand ka apna 6-kaam set + look + hook + layout + slot. Zindagi bhar koi (set,look,hook,lay) dohra nahi.
    -> plan {brand: {"set": [ids], "look", "hook", "lay", "slot", "lead": id|None, "season": {...}|None}}"""
    from . import svc
    R = svc.rates()["by"]
    rnd = random.Random(seed if seed is not None else time.time())
    day = day or str(datetime.date.today())
    H_ = _hist()
    used = {_key(h) for h in H_}
    cnt = {}
    for h in H_:
        for i in h.get("set") or [h.get("item")]:
            cnt[i] = cnt.get(i, 0) + 1
    pool = {g: [k for k, v in KAAM.items() if v[1] == g and k in R] for g in GROUP_NEED}
    try:
        season = svc.season_due(7, day)
    except Exception:
        season = []
    try:
        sale = svc.offer(day)["sale"]["item"]
    except Exception:
        sale = None
    brands = list(BRANDS)
    k_ = (datetime.date.fromisoformat(day).toordinal()) % len(brands)
    order = brands[k_:] + brands[:k_]                    # har din brand ka slot badle
    try:                                                 # v3.8.5: brand ki apni roz wali video ke 75 min ke paas services video nahi (takra)
        from . import pipeline as _P
        sch = _P.schedule()
        def _m(x):
            h_, m_ = (int(y) for y in x.split(":"))
            return h_ * 60 + m_
        def clash(b, sl):
            return any(abs(_m(x.strip()) - _m(sl)) < 75 for x in str(sch.get(b, "")).split(",") if x.strip())
        import itertools
        best = None
        for perm in itertools.permutations(order):
            c_ = sum(clash(b, SLOTS[i]) for i, b in enumerate(perm))
            if best is None or c_ < best[0]:
                best = (c_, perm)
            if c_ == 0:
                break
        order = list(best[1])
    except Exception as e:
        log(f"svc slot clash: {e}")
    plan, looks_today, hooks_today = {}, set(), set()
    for bi, b in enumerate(order):
        for _try in range(400):
            s_ = []
            lead = None
            if season and bi == 0 and season[0]["item"] in KAAM:
                lead = season[0]["item"]
                s_.append(lead)
            if sale in KAAM and sale not in s_ and rnd.random() < .5:
                s_.append(sale)
            for g, n in GROUP_NEED.items():
                have = sum(1 for x in s_ if KAAM[x][1] == g)
                c_ = [x for x in pool[g] if x not in s_]
                c_.sort(key=lambda x: (cnt.get(x, 0) + rnd.random() * 3))
                s_ += c_[:max(0, n - have)]
            if "m-resume" not in s_ and rnd.random() < .6:      # ₹10 resume aksar dikhe
                s_[-1] = "m-resume"
            s_ = list(dict.fromkeys(s_))[:N_KAAM]
            while len(s_) < N_KAAM:
                extra = [x for x in KAAM if x in R and x not in s_]
                s_.append(rnd.choice(extra))
            if not lead:
                rnd.shuffle(s_)
            lk = rnd.choice([x for x in LOOKS if x not in looks_today] or list(LOOKS))
            if b == "pahadi" and "pahad" not in looks_today and rnd.random() < .5:
                lk = "pahad"
            hk = rnd.choice([x for x in range(len(HOOKS)) if x not in hooks_today] or list(range(len(HOOKS))))
            ly = rnd.choice("LR")
            row = {"set": s_, "look": lk, "hook": hk, "lay": ly}
            if _key(row) not in used:
                break
        looks_today.add(lk)
        hooks_today.add(hk)
        used.add(_key(row))
        row.update(slot=SLOTS[bi % len(SLOTS)], lead=lead, season=season[0] if lead else None)
        plan[b] = row
    return plan


# ---------------------------------------------------------------- drawing helpers
_FONT = {}


def _font(size, weight="ExtraBold"):
    k = (size, weight)
    if k not in _FONT:
        f = ImageFont.truetype(str(ASSETS / "Baloo2.ttf"), size, layout_engine=ImageFont.Layout.RAQM)
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
        if len(_FONT) > 300:
            _FONT.clear()
        _FONT[k] = f
    return _FONT[k]


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
    while size > 28 and f.getlength(text) > maxw:
        size -= 4
        f = _font(size, weight)
    return f


class Canvas:
    """Har text ka dabba yaad rakhta hai - audit round 3 (frame ke bahar / aapas mein chadha) isi se."""
    def __init__(self, im):
        self.im, self.boxes = im, []
        self.d = ImageDraw.Draw(im)

    def text(self, xy, s, font, fill, anchor="mm", tag=""):
        s = fix_words(s)                                      # v3.8.5: screen par bhi wahi shabdkosh
        self.d = ImageDraw.Draw(self.im)
        self.d.text(xy, s, font=font, fill=fill, anchor=anchor)
        self.boxes.append((self.d.textbbox(xy, s, font=font, anchor=anchor), s, tag))


def _bg(look):
    top, bot = _hex(LOOKS[look][0]), _hex(LOOKS[look][1])
    g = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / H
        g.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3)))
    im = g.resize((W, H)).convert("RGBA")
    d = ImageDraw.Draw(im)
    dot = tuple(max(0, c - 22) for c in bot)
    for y in range(40, H, 56):
        for x in range(40, W, 56):
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(*dot, 90))
    return im


_SH = {}


def _card(im, box, r=40, fill=(255, 255, 255), shadow=26):
    x0, y0, x1, y1 = (int(v) for v in box)
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    key = (w, h, r, shadow)
    sh = _SH.get(key)
    if sh is None:
        pad = 50
        sh = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 14, pad + w, pad + h + 14), r, fill=(0, 0, 0, shadow * 3))
        sh = sh.filter(ImageFilter.GaussianBlur(22))
        if len(_SH) > 300:
            _SH.clear()
        _SH[key] = sh
    px, py = x0 - 50, y0 - 50
    if px >= 0 and py >= 0 and px + sh.width <= im.width and py + sh.height <= im.height:
        im.alpha_composite(sh, (px, py))
    ImageDraw.Draw(im).rounded_rectangle((x0, y0, x1, y1), r, fill=fill)


def _mock(key, w=520):
    """Jin kaam ka asli screenshot nahi (form, ITR, phone, PPT, patra, docs) - saaf NAMOONA screen (koi sarkari logo/naam nahi)."""
    f_h, f_b, f_s = _font(34), _font(28, "SemiBold"), _font(24, "Medium")
    im = Image.new("RGB", (w, 1000), (248, 250, 251))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 96), fill=(15, 118, 110))
    title = {"form": "आवेदन फ़ॉर्म (नमूना)", "itr": "टैक्स सारांश (नमूना)", "phone": "फ़ोन सेटिंग", "ppt": "प्रोजेक्ट स्लाइड",
             "letter": "आवेदन पत्र", "docs": "फ़ोटो / साइन"}.get(key, "नमूना")
    d.text((24, 48), title, font=f_h, fill=(255, 255, 255), anchor="lm")
    y = 130
    if key == "form":
        for lab, val in [("नाम", "रमेश कुमार"), ("जन्म तिथि", "12-05-2004"), ("मोबाइल", "98•••••210"), ("पता", "गाँव / शहर"),
                         ("फ़ोटो", "ठीक · 45 KB"), ("हस्ताक्षर", "ठीक · 18 KB")]:
            d.text((24, y), lab, font=f_s, fill=(90, 100, 110), anchor="lm")
            d.rounded_rectangle((24, y + 18, w - 24, y + 82), 12, fill=(255, 255, 255), outline=(210, 220, 225), width=2)
            d.text((44, y + 50), val, font=f_b, fill=(30, 40, 50), anchor="lm")
            y += 120
        d.rounded_rectangle((24, y + 6, w - 24, y + 76), 14, fill=(15, 118, 110))
        d.text((w // 2, y + 41), "जमा करें (OTP आप डालें)", font=f_b, fill=(255, 255, 255), anchor="mm")
    elif key == "itr":
        for lab, val in [("कुल आय", "₹4,80,000"), ("कटौती (80C)", "₹50,000"), ("कर योग्य आय", "₹4,30,000"),
                         ("TDS कटा", "₹0"), ("देय कर", "₹0"), ("स्थिति", "जाँच के बाद जमा")]:
            d.rounded_rectangle((24, y, w - 24, y + 96), 14, fill=(255, 255, 255), outline=(220, 228, 232), width=2)
            d.text((44, y + 48), lab, font=f_s, fill=(90, 100, 110), anchor="lm")
            d.text((w - 44, y + 48), val, font=f_b, fill=(30, 40, 50), anchor="rm")
            y += 116
    elif key == "phone":
        for lab, on in [("Wi-Fi", 1), ("मोबाइल डेटा", 1), ("UPI ऐप", 1), ("ईमेल खाता", 1), ("बैकअप", 0), ("स्टोरेज साफ़", 1)]:
            d.rounded_rectangle((24, y, w - 24, y + 96), 14, fill=(255, 255, 255))
            d.text((44, y + 48), lab, font=f_b, fill=(30, 40, 50), anchor="lm")
            cx = w - 90
            d.rounded_rectangle((cx - 40, y + 30, cx + 40, y + 66), 18, fill=(15, 118, 110) if on else (200, 205, 210))
            d.ellipse((cx + (4 if on else -36), y + 32, cx + (36 if on else -4), y + 64), fill=(255, 255, 255))
            y += 112
    elif key == "ppt":
        for i in range(3):
            d.rounded_rectangle((24, y, w - 24, y + 250), 16, fill=(255, 255, 255), outline=(220, 228, 232), width=2)
            d.rectangle((24, y, w - 24, y + 56), fill=(47, 84, 235))
            d.text((44, y + 28), f"स्लाइड {i + 1}", font=f_b, fill=(255, 255, 255), anchor="lm")
            for j in range(3):
                d.rounded_rectangle((44, y + 82 + j * 50, w - 44 - j * 60, y + 104 + j * 50), 8, fill=(226, 232, 240))
            y += 280
    else:   # letter / docs
        d.text((24, y), "सेवा में,", font=f_b, fill=(30, 40, 50), anchor="lm")
        y += 60
        for j in range(12):
            d.rounded_rectangle((24, y, w - 24 - (j % 3) * 70, y + 20), 8, fill=(226, 232, 240))
            y += 50
    return im


def _phone_shot(key, t_scroll, ph_w=470):
    sw = ph_w - 36
    shot = _SH.get(("shot", key, sw))
    if shot is None:
        f = SHOTS / f"{key}.jpg"
        shot = Image.open(f).convert("RGB") if f.exists() else _mock(key)
        shot = shot.resize((sw, int(shot.height * sw / shot.width)), Image.LANCZOS)
        _SH[("shot", key, sw)] = shot
    sh_h = int(ph_w * 1.9) - 36
    off = int(max(0, shot.height - sh_h) * _ease(t_scroll))
    view = Image.new("RGB", (sw, sh_h), (255, 255, 255))
    view.paste(shot.crop((0, off, sw, min(shot.height, off + sh_h))), (0, 0))
    ph = Image.new("RGBA", (ph_w + 80, int(ph_w * 1.9) + 80), (0, 0, 0, 0))
    sd = Image.new("RGBA", ph.size, (0, 0, 0, 0))
    ImageDraw.Draw(sd).rounded_rectangle((40, 58, ph_w + 40, int(ph_w * 1.9) + 58), 60, fill=(0, 0, 0, 110))
    ph.alpha_composite(sd.filter(ImageFilter.GaussianBlur(24)))
    d = ImageDraw.Draw(ph)
    d.rounded_rectangle((40, 40, ph_w + 40, int(ph_w * 1.9) + 40), 60, fill=(20, 22, 26))
    m = Image.new("L", view.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, *view.size), 42, fill=255)
    ph.paste(view, (58, 58), m)
    d.rounded_rectangle((40 + ph_w // 2 - 60, 68, 40 + ph_w // 2 + 60, 88), 10, fill=(20, 22, 26))
    return ph


def _marker(cv, xy, text, font, brand, tag=""):
    d = ImageDraw.Draw(cv.im)
    bx = d.textbbox(xy, text, font=font, anchor="mm")
    pad = 18
    d.rounded_rectangle((bx[0] - pad, bx[1] - pad // 2, bx[2] + pad, bx[3] + pad // 2), 18, fill=brand)
    cv.text(xy, text, font, (255, 255, 255), tag=tag)


def _chips(im, cv, rows, y0, cur, br, dk, k=1.0):
    """Neeche 6 kaam ki patti (2x3) - dekhne wale ko ek saath dikhe 'kitne tarah ke kaam'. cur = abhi wala (rang mein)."""
    cw, ch, gap = 300, 96, 24
    x_start = (W - (3 * cw + 2 * gap)) // 2
    for n, r in enumerate(rows):
        col, row = n % 3, n // 2 if False else n // 3
        x0 = x_start + col * (cw + gap)
        yy = y0 + row * (ch + gap) + int((1 - k) * 300)
        on = n == cur
        _card(im, (x0, yy, x0 + cw, yy + ch), 30, fill=br if on else (255, 255, 255), shadow=10)
        nm = r["name"]
        cv.text((x0 + cw // 2, yy + 34), nm, _fit(nm, 30, cw - 30, "SemiBold"), (255, 255, 255) if on else dk,
                tag=("~" if k < .999 else "") + f"chip{n}")
        pr = _rs(r["price"]) + " से"
        cv.text((x0 + cw // 2, yy + 70), pr, _font(28, "ExtraBold"), (255, 255, 255) if on else br,
                tag=("~" if k < .999 else "") + f"chipp{n}")


LOGO_DIR = DATA / "brand_logo"


def _logo_img(brand, size):
    """Brand ka asli logo: Facebook page ki profile photo (ek baar le kar rakh li) - na mile to brand rang ka gol nishaan."""
    key = ("logo", brand, size)
    if key in _SH:
        return _SH[key]
    f = LOGO_DIR / f"{brand}.png"
    im = None
    if f.exists():
        try:
            im = Image.open(f).convert("RGBA")
        except Exception:
            im = None
    if im is None and state.get(f"logo_try2_{brand}") != str(datetime.date.today()):     # din mein ek koshish
        state.put(f"logo_try2_{brand}", str(datetime.date.today()))
        try:
            import requests
            from . import meta as M
            b = M.brand_info(brand)
            if b and b.get("page_id"):                      # v3.8.5: M._get = appsecret_proof ke saath (pehle bina proof - fail)
                j = M._get(f"/{b['page_id']}/picture", b["page_token"], redirect="false", type="large", height=400, width=400)
                url = (j.get("data") or {}).get("url")
                if url:
                    raw = requests.get(url, timeout=30).content
                    LOGO_DIR.mkdir(parents=True, exist_ok=True)
                    import io
                    Image.open(io.BytesIO(raw)).convert("RGBA").save(f)
                    im = Image.open(f).convert("RGBA")
        except Exception as e:
            log(f"logo {brand}: {e}")
    if im is None:
        bg_ = _hex(BRANDS[brand]["bg"][1])
        ac_ = _hex(BRANDS[brand]["accent"])
        im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        d_ = ImageDraw.Draw(im)
        d_.ellipse((0, 0, 255, 255), fill=bg_)
        ini = "".join(w[0] for w in BRANDS[brand]["name"].split()[:2]).upper()
        d_.text((128, 132), ini, font=_font(120), fill=ac_, anchor="mm")
    im = im.resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), m)
    _SH[key] = out
    return out


def _logo_draw(im, brand, x, y, size):
    try:
        lg = _logo_img(brand, size)
        ImageDraw.Draw(im).ellipse((x - 4, y - 4, x + size + 4, y + size + 4), fill=(255, 255, 255))
        im.alpha_composite(lg, (x, y))
    except Exception as e:
        log(f"logo draw: {e}")


def _rs(n):
    s = f"{int(n):,}"
    if int(n) >= 100000:                      # bharatiya ginti (1,00,000)
        x = str(int(n))
        s = re.sub(r"(\d)(?=(\d\d)+\d$)", r"\1,", x[:-3]) + "," + x[-3:]
    return "₹" + s


def _price_of(iid, R, sale):
    it = R[iid]
    if sale and sale.get("item") == iid:
        return sale["now"], it["price"]
    return it["price"], None


def ctx_for(v, brand, day=None):
    """Video ka saara likha/bola (audit isi ko jaanchta hai)."""
    from . import svc
    R = svc.rates()["by"]
    try:
        o = svc.offer(day)
        sale = o["sale"] if o["sale"]["start"] <= (day or str(datetime.date.today())) <= o["sale"]["end"] else None
    except Exception:
        sale = None
    lead = v["set"][0]
    k = KAAM[lead]
    hook = HOOKS[v["hook"]]
    q1, q2 = k[2], k[3]
    # v3.8.4: shuru mein "sasta" dikhe (owner) - SACH: bazaar ke kam rate se hamara rate, '% tak' (sabse bada asli farak, 10 ke kadam, max 90)
    pct = 0
    for iid in v["set"]:
        it = R[iid]
        pct = max(pct, int((1 - it["price"] / max(1, it["market"][0])) * 100))
    pct = min(90, pct // 10 * 10)
    mode = v["hook"] % 4
    lp, lm = R[lead]["price"], R[lead]["market"][0]
    say_hook = f"{hook[1]} {q1} {q2}"
    kick = hook[0]
    if mode == 0 and pct >= 30:
        kick, q1, q2 = "डिजिटल काम", "बाज़ार से", f"{pct}% तक सस्ता"
        say_hook = f"डिजिटल काम, बाज़ार से {pct} प्रतिशत तक सस्ता"
    elif mode == 1 and lm > lp:
        kick, q1, q2 = f"बाज़ार में {_rs(lm)}+", k[0], f"सिर्फ़ {_rs(lp)}"
        say_hook = f"बाज़ार में {lm} रुपये से ऊपर, यहाँ {k[6]}, सिर्फ़ {lp} रुपये"
    elif mode == 2:
        kick, q1, q2 = "₹10 से शुरू", "रिज़्यूमे ₹10", "फ़ॉर्म मदद ₹49"
        say_hook = "दस रुपये से शुरू। रिज़्यूम दस रुपये, फ़ॉर्म मदद उनचास रुपये"
    season = v.get("season")
    if season:
        d_ = datetime.date.fromisoformat(season["date"])
        q1, q2 = f"{k[0]} की आख़िरी तारीख़", f"{d_.day}/{d_.month}/{d_.year}"
        kick, say_hook = hook[0], f"{k[6]} की आख़िरी तारीख़ पास है"
    rows = []
    for iid in v["set"]:
        p_, old = _price_of(iid, R, sale)
        rows.append({"id": iid, "name": KAAM[iid][0], "group": KAAM[iid][1], "ben": KAAM[iid][4], "shot": KAAM[iid][5],
                     "say": KAAM[iid][6], "price": p_, "was": old, "market": R[iid]["market"][0], "sale_end": sale["end"] if old else ""})
    segs = [("hook", say_hook), ("tag", f"{TAG1}, {TAG2}।")] + \
           [(f"k{i}", f"{r['say']}, {r['price']} रुपये।") for i, r in enumerate(rows)] + \
           [("hindi", "हिंदी में लिखिए। दोस्त को भेजिए, दस प्रतिशत आपका।"),
            ("cta", "कमेंट में अपना काम लिखिए।")]
    say = (f"{hook[1]} {q1} {q2} {TAG1}, {TAG2}। " +
           "। ".join(f"{r['say']}, {r['price']} रुपये से" for r in rows) +
           "। हिंदी में लिखिए, जैसे घर में बोलते हैं, इंग्लिश ज़रूरी नहीं। दोस्त को भेजिए, उसके बिल का दस प्रतिशत आपका। "
           "कमेंट में अपना काम लिखिए, या सब हिसाब डॉट कॉम स्लैश सर्विसेज़ लिस्ट।")
    return {"segs": segs, "tl": make_tl(), "day": day or str(datetime.date.today()), "brand": brand, "look": v["look"], "lay": v["lay"], "kick": kick, "q1": q1, "q2": q2, "pct": pct, "rows": rows, "say": say,
            "season": season, "sale": sale}


# ---------------------------------------------------------------- one frame
def frame(cx_, t, cache, reg=None):
    """cx_ = ctx_for(...). reg = list -> is frame ke text dabbe (audit ke liye)."""
    look, lay = cx_["look"], cx_["lay"]
    c1, c2, br, dk = (_hex(c) for c in LOOKS[look])
    if "bg" not in cache:
        cache["bg"] = _bg(look)
    im = cache["bg"].copy()
    cv = Canvas(im)
    side = 1 if lay == "R" else -1
    d = ImageDraw.Draw(im)
    tl = cx_.get("tl") or make_tl()
    DUR_, T_HOOK_, T_LIST0_ = tl["dur"], tl["hook"][1], tl["tag"][1]
    T_HINDI_, T_CTA_ = tl["hindi"][0], tl["cta"][0]
    d.rounded_rectangle((60, 70, 60 + int((W - 120) * min(1, t / DUR_)), 78), 4, fill=br)
    if t < T_CTA_:                                   # brand ka logo (har frame, upar baayen)
        _logo_draw(im, cx_["brand"], 60, 100, 64)
        cv.text((140, 132), BRANDS[cx_["brand"]]["name"], _font(30, "SemiBold"), dk, anchor="lm", tag="lgname")
    # S0 hook
    if t < T_HOOK_:
        k = _back(t / .5)
        cv.text((W // 2, 600), cx_["kick"], _font(54, "SemiBold"), br, tag="kick")
        f = _fit(max(cx_["q1"], cx_["q2"], key=len), int(120 * max(.3, k)), W - 160)
        cv.text((W // 2, 790), cx_["q1"], f, dk, tag="q1")
        _marker(cv, (W // 2, 960), cx_["q2"], f, br, tag="q2")
        if t > 1.1:
            d = ImageDraw.Draw(im)
            d.polygon([(W // 2 - 36, 1150), (W // 2 + 36, 1150), (W // 2, 1205)], fill=br)
        if t > .7:                                         # neeche 6 kaam ki jhalak (khaali jagah nahi)
            _chips(im, cv, cx_["rows"], 1300, -1, br, dk, _ease((t - .7) / .5))
    # S1 tagline
    elif t < T_LIST0_:
        k = _back((t - T_HOOK_) / .5)
        f = _fit(TAG1, int(124 * max(.3, k)), W - 140)
        cv.text((W // 2, 760), TAG1, f, dk, tag="tag1")
        _marker(cv, (W // 2, 930), TAG2, f, br, tag="tag2")
        chip = "₹10 से शुरू  ·  मदद · बनाना · मोबाइल-कंप्यूटर"
        fc = _fit(chip, 40, W - 200, "SemiBold")
        cw = fc.getlength(chip) + 70
        _card(im, (W // 2 - cw // 2, 1100, W // 2 + cw // 2, 1180), 40, shadow=12)
        cv.text((W // 2, 1140), chip, fc, br, tag="chip")
        _chips(im, cv, cx_["rows"], 1300, -1, br, dk, _ease((t - T_HOOK_ - .3) / .5))
    # S2 kaam list
    elif t < T_HINDI_:
        i = next((j for j in range(N_KAAM) if t < tl[f"k{j}"][1]), N_KAAM - 1)
        r = cx_["rows"][i]
        lt = t - tl[f"k{i}"][0]
        sd = side if i % 2 == 0 else -side
        k = _ease(lt / .4)
        cv.text((W // 2, 210), f"काम {i + 1} / {N_KAAM}  ·  {r['group']}", _font(40, "SemiBold"), br, tag="num")
        cv.text((W // 2, 310), r["name"], _fit(r["name"], 92, W - 140), dk, tag="name")
        key = ("ph", r["shot"], int(lt * 5))
        ph = cache.get(key)
        if ph is None:
            ph = _phone_shot(r["shot"], min(1, max(0, (lt - .5) / 2.0)))
            if len(cache) > 60:
                bg = cache["bg"]
                cache.clear()
                cache["bg"] = bg
            cache[key] = ph
        px = W // 2 + sd * 230 - ph.width // 2 + int((1 - k) * sd * 700)
        im.alpha_composite(ph, (px, 420))
        ccx = W // 2 - sd * 255
        x0, x1 = ccx - 215, ccx + 215
        _card(im, (x0, 560, x1, 900), 44)
        cv.text((ccx, 620), "सिर्फ़", _font(42, "SemiBold"), dk, tag="p1")
        cv.text((ccx, 720), _rs(r["price"]), _fit(_rs(r["price"]), int(130 * max(.3, _back(lt / .5))), 390), br, tag="price")
        cv.text((ccx, 820), "से शुरू", _font(42, "SemiBold"), dk, tag="p2")
        old = f"बाज़ार {_rs(r['market'])}+" if not r["was"] else f"पहले {_rs(r['was'])}"
        fm = _fit(old, 38, 400, "SemiBold")
        cv.text((ccx, 950), old, fm, (120, 120, 120), tag="old")
        bx = ImageDraw.Draw(im).textbbox((ccx, 950), old, font=fm, anchor="mm")
        ImageDraw.Draw(im).line((bx[0], (bx[1] + bx[3]) // 2, bx[0] + (bx[2] - bx[0]) * _ease((lt - .5) / .4),
                                 (bx[1] + bx[3]) // 2), fill=(224, 49, 49), width=6)
        kk = _ease((lt - .7) / .4)
        if kk > 0:
            _card(im, (x0, 1030, x1, 1140), 52, shadow=14)
            d = ImageDraw.Draw(im)
            d.ellipse((x0 + 16, 1046, x0 + 94, 1124), fill=br)
            _tick(d, x0 + 55, 1085, 24, (255, 255, 255))
            cv.text((x0 + 112, 1085), r["ben"], _fit(r["ben"], 40, x1 - x0 - 130, "SemiBold"), dk, anchor="lm", tag="ben")
        _chips(im, cv, cx_["rows"], 1420, i, br, dk)
        if r["was"]:
            se = datetime.date.fromisoformat(r["sale_end"])
            cv.text((ccx, 1200), f"इस हफ़्ते · {se.day}/{se.month} तक", _font(36, "SemiBold"), (224, 49, 49), tag="sale")
    # S3 bhasha + referral
    elif t < T_CTA_:
        lt = t - T_HINDI_
        for j, (a, b) in enumerate([("हिंदी में लिखिए,", "जैसे घर में बोलते हैं"), ("English ज़रूरी नहीं", "शर्म की कोई बात नहीं"),
                                    ("दोस्त को भेजिए —", "उसके बिल का 10% आपका")]):
            kk = _ease((lt - j * .5) / .45)
            if kk <= 0:
                continue
            y0 = 520 + j * 330
            xo = int((1 - kk) * (900 if j % 2 else -900))
            _card(im, (110 + xo, y0, W - 110 + xo, y0 + 250), 50, fill=(255, 255, 255) if j < 2 else br)
            col = dk if j < 2 else (255, 255, 255)
            mv = "~" if kk < .999 else ""                # andar aate hue (animation) - audit bahar-jaanch nahi karta
            cv.text((W // 2 + xo, y0 + 85), a, _fit(a, 66, W - 300), col, tag=f"{mv}h{j}a")
            cv.text((W // 2 + xo, y0 + 170), b, _fit(b, 52, W - 300, "SemiBold"), br if j < 2 else (255, 255, 255), tag=f"{mv}h{j}b")
    # S4 CTA
    else:
        k = _ease((t - T_CTA_) / .45)
        im.alpha_composite(Image.new("RGBA", (W, H), (*br, int(255 * k))))
        kb = _back((t - T_CTA_ - .1) / .6)
        _logo_draw(im, cx_["brand"], W // 2 - 300, 300, 92)
        cv.text((W // 2 + 40, 346), BRANDS[cx_["brand"]]["name"], _fit(BRANDS[cx_["brand"]]["name"], 52, 480, "SemiBold"), (255, 255, 255), tag="bn")
        cv.text((W // 2, 490), TAG1, _fit(TAG1, int(108 * max(.3, kb)), W - 140), (255, 255, 255), tag="c1")
        cv.text((W // 2, 610), "— " + TAG2 + " —", _fit(TAG2, int(92 * max(.3, kb)), W - 200), (255, 255, 255), tag="c2")
        if cx_.get("pct", 0) >= 30:
            cv.text((W // 2, 712), f"बाज़ार से {cx_['pct']}% तक सस्ता", _font(50), (255, 236, 153), tag="pct")
        pul = 1 + .03 * math.sin(t * 7)
        bw, bh = int(860 * pul), int(124 * pul)
        _card(im, (W // 2 - bw // 2, 790, W // 2 + bw // 2, 790 + bh), 62, shadow=30)
        cv.text((W // 2, 790 + bh // 2), SITE_TXT, _fit(SITE_TXT, 54, bw - 80), br, tag="site")
        cv.text((W // 2, 990), "कमेंट में अपना काम लिखिए", _font(50, "SemiBold"), (255, 255, 255), tag="cm")
        grid = [("रिज़्यूमे", 10), ("फ़ॉर्म मदद", 49), ("मोबाइल मदद", 49), ("फ़ोटो-साइन", 29), ("ITR-1 मदद", 299),
                ("स्कॉलरशिप", 99), ("बायोडाटा", 49), ("प्रोजेक्ट/PPT", 99), ("वेबसाइट", 2999)]
        gw, gh, gg = 300, 104, 18
        gx0 = (W - (3 * gw + 2 * gg)) // 2
        for n_, (nm_, pr_) in enumerate(grid):
            gx, gy = gx0 + (n_ % 3) * (gw + gg), 1060 + (n_ // 3) * (gh + gg)
            ImageDraw.Draw(im).rounded_rectangle((gx, gy, gx + gw, gy + gh), 26, fill=(255, 255, 255))
            cv.text((gx + gw // 2, gy + 36), nm_, _fit(nm_, 32, gw - 30, "SemiBold"), dk, tag=f"g{n_}")
            cv.text((gx + gw // 2, gy + 74), _rs(pr_) + " से", _font(30), br, tag=f"gp{n_}")
        cv.text((W // 2, 1450), "पहले बात  ·  फिर रेट  ·  फिर काम", _font(40, "SemiBold"), (255, 255, 255), tag="steps")
        code = CODES.get(cx_["brand"])
        if code:
            cl = f"कोड {code} = 10% तक छूट"
            fc_ = _font(42)
            cw_ = fc_.getlength(cl) + 70
            ImageDraw.Draw(im).rounded_rectangle((W // 2 - cw_ // 2, 1510, W // 2 + cw_ // 2, 1596), 43, outline=(255, 255, 255), width=4)
            cv.text((W // 2, 1553), cl, fc_, (255, 255, 255), tag="code")
    cv.text((W // 2, H - 70), BRANDS[cx_["brand"]]["name"] + " · Services", _font(34, "SemiBold"),
            (255, 255, 255) if t >= T_CTA_ + .3 else dk, tag="foot")
    if reg is not None:
        reg.extend(cv.boxes)
    return im.convert("RGB")


# ---------------------------------------------------------------- 5 round audit
BAN = [r"\bAI\b", r"एआई", r"artificial", r"chat ?gpt", r"gemini", r"insaan", r"इंसान", r"guarantee", r"गारंटी", r"पक्का रिफ़ंड",
       r"pakka refund", r"refund pakka", r"सिर्फ़ आज", r"sirf aaj", r"आख़िरी मौका", r"last chance", r"slot bache", r"स्लॉट बचे",
       r"manoj", r"मनोज", r"pandey", r"पांडे", r"सरकारी विभाग", r"government official", r"\bDM\b", r"link (comment|maango)",
       r"comment link", r"100% (pakka|guaranteed)", r"approve (pakka|guaranteed)", r"selection pakka"]


def _glyph_ok(text):
    try:
        from fontTools.ttLib import TTFont
        if "cmap" not in _FONT:
            _FONT["cmap"] = TTFont(str(ASSETS / "Baloo2.ttf")).getBestCmap()
        cm = _FONT["cmap"]
        return [c for c in text if not c.isspace() and ord(c) not in cm and ord(c) not in (0x200C, 0x200D)]
    except Exception:
        return []


def audit_video(cx_, meta=None, mp4=None, voice_dur=None):
    """-> (ok, report_lines). Round 1-4 (5 = owner ✅ manzoori). Koi bhi ❌ = publish nahi."""
    from . import svc
    R = svc.rates()["by"]
    bad, good = [], []
    # 1 TATHYA
    try:
        o = svc.offer(cx_.get("day"))
    except Exception:
        o = {"sale": {}}
    for r in cx_["rows"]:
        it = R.get(r["id"])
        if not it:
            bad.append(f"1 tathya: {r['id']} rate list mein nahi")
            continue
        okp = r["price"] == it["price"] or (r["was"] and o["sale"].get("item") == r["id"] and r["price"] == o["sale"]["now"]
                                            and r["price"] >= it["floor"])
        if not okp:
            bad.append(f"1 tathya: {r['name']} ₹{r['price']} ≠ rate list ₹{it['price']}")
        if r["market"] != it["market"][0]:
            bad.append(f"1 tathya: {r['name']} bazaar rate galat")
        q = None if (r["was"] or cx_.get("day") != str(datetime.date.today())) else svc.price(it)
        if q and q["final"] > r["price"] and not o.get("fest"):
            bad.append(f"1 tathya: {r['name']} dikhaya ₹{r['price']} par quote ₹{q['final']} banega")
    if cx_.get("season"):
        s_ = cx_["season"]
        ok_s = any(x.get("date") == s_.get("date") and x.get("source") == s_.get("source") for x in svc.season_list())
        if not ok_s or not re.search(r"\.(gov|nic)\.in(/|$)", s_.get("source", "")):
            bad.append("1 tathya: season ki date sarkari source se pakki nahi")
    if not bad:
        good.append("1 tathya ✅ har rate rate-list se, bazaar rate sahi" + (", season date sarkari link se" if cx_.get("season") else ""))
    # 2 NIYAM
    texts = [cx_["kick"], cx_["q1"], cx_["q2"], cx_["say"]] + [r["name"] + " " + r["ben"] for r in cx_["rows"]]
    if meta:
        texts += [meta.get("title", ""), meta.get("description", "")]
    hit = sorted({p for p in BAN for s in texts if re.search(p, s, re.I)})
    if hit:
        bad.append("2 niyam: mana shabd: " + ", ".join(hit))
    if meta and len(meta.get("title", "")) > 100:
        bad.append("2 niyam: title 100 se lamba")
    if any(r["id"].startswith("m-itr") and r["price"] < 299 for r in cx_["rows"]):
        bad.append("2 niyam: ITR ka rate ₹299 se kam dikha")
    if not hit and not [b for b in bad if b.startswith("2")]:
        good.append("2 niyam ✅ mana shabd nahi (AI/guarantee/nakli jaldi/owner naam/DM)")
    # 3 DIKHAWAT
    vis = []
    cache = {}
    DUR_ = (cx_.get("tl") or make_tl())["dur"]
    for t10 in range(0, int(DUR_ * 10), 3):
        t = t10 / 10
        reg = []
        fr = frame(cx_, t, cache, reg)
        if t10 % 15 == 0:
            st = fr.convert("L").resize((54, 96))
            px = list(st.getdata())
            if sum(px) / len(px) < 15:
                vis.append(f"{t:.1f}s kaali frame")
        for (b, s, tag) in reg:
            if not tag.startswith("~") and (b[0] < 30 or b[2] > W - 30 or b[1] < 40 or b[3] > H - 30):
                vis.append(f"{t:.1f}s '{s[:18]}' frame ke bahar")
            miss = _glyph_ok(s)
            if miss:
                vis.append(f"'{s[:18]}' toota akshar {''.join(miss[:3])}")
        sb = [(b, s) for (b, s, tag) in reg if not tag.startswith("~")]
        for a_ in range(len(sb)):
            for b_ in range(a_ + 1, len(sb)):
                A, B = sb[a_][0], sb[b_][0]
                ix = min(A[2], B[2]) - max(A[0], B[0])
                iy = min(A[3], B[3]) - max(A[1], B[1])
                if ix > 8 and iy > 8:
                    vis.append(f"{t:.1f}s '{sb[a_][1][:14]}' aur '{sb[b_][1][:14]}' chadhe")
    vis = list(dict.fromkeys(vis))
    if vis:
        bad += ["3 dikhawat: " + x for x in vis[:8]]
    else:
        good.append(f"3 dikhawat ✅ {int(DUR_ * 10) // 3} frame: text frame ke andar, chadha nahi, kaali frame nahi, akshar poore")
    # 4 AWAAZ
    if mp4:
        try:
            pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type:format=duration", "-of", "json", str(mp4)],
                                capture_output=True, text=True, timeout=60)
            j = json.loads(pr.stdout or "{}")
            kinds = [s_.get("codec_type") for s_ in j.get("streams", [])]
            dur = float(j.get("format", {}).get("duration", 0))
            if "audio" not in kinds:
                bad.append("4 awaaz: video mein awaaz nahi")
            if dur < DUR_ - 1:
                bad.append(f"4 awaaz: video chhoti ({dur:.1f}s)")
            vd = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp4), "-af", "volumedetect", "-f", "null", "-"],
                                capture_output=True, text=True, timeout=120).stderr
            m = re.search(r"mean_volume: (-?[\d.]+) dB", vd)
            if m and float(m.group(1)) < -40:
                bad.append(f"4 awaaz: bahut dheemi ({m.group(1)} dB)")
            if voice_dur is not None and voice_dur < 8:
                bad.append("4 awaaz: bolne wali awaaz bani hi nahi")
            for k_, txt_ in cx_.get("segs") or []:                 # raftaar: har vakya 3.4 shabd/second se tez nahi
                ln_ = (cx_.get("lens") or {}).get(k_)
                if ln_ is None:
                    if cx_.get("lens"):
                        bad.append(f"4 awaaz: '{k_}' hisse ki awaaz nahi bani")
                    continue
                wps = len(txt_.split()) / max(.3, ln_)
                if wps > 3.4:
                    bad.append(f"4 awaaz: '{k_}' bahut tez ({wps:.1f} shabd/sec)")
            sd = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp4), "-af", "silencedetect=noise=-35dB:d=0.25", "-f", "null", "-"],
                                capture_output=True, text=True, timeout=120).stderr
            if cx_.get("lens") and sd.count("silence_start") < 5:
                bad.append(f"4 awaaz: vakyon ke beech ruk nahi ({sd.count('silence_start')} jagah) - ek saans mein bol raha")
            if not [b for b in bad if b.startswith("4")]:
                good.append(f"4 awaaz ✅ {dur:.1f}s, awaaz {m.group(1) if m else '?'} dB")
        except Exception as e:
            bad.append(f"4 awaaz: jaanch nahi ho paayi ({str(e)[:60]})")
    # 6 AAKARSHAN (padhne/dikhne layak): rang ka contrast + hook chhota + pehle 1 sec mein bada text
    def _lum(c):
        r_ = [(x / 255) / 12.92 if x / 255 <= .03928 else (((x / 255) + .055) / 1.055) ** 2.4 for x in c]
        return .2126 * r_[0] + .7152 * r_[1] + .0722 * r_[2]
    def _cr(a, b):
        a, b = _lum(a), _lum(b)
        return (max(a, b) + .05) / (min(a, b) + .05)
    t_, b_, br_, dk_ = (_hex(c) for c in LOOKS[cx_["look"]])
    six = []
    if _cr(dk_, b_) < 7:
        six.append(f"gehra text kam saaf ({_cr(dk_, b_):.1f})")
    if _cr(br_, b_) < 3.5:
        six.append(f"brand rang ka text kam saaf ({_cr(br_, b_):.1f})")
    if _cr((255, 255, 255), br_) < 4.5:
        six.append(f"CTA par safed text kam saaf ({_cr((255, 255, 255), br_):.1f})")
    if len((cx_["q1"] + " " + cx_["q2"]).split()) > 8:
        six.append("hook 8 shabd se lamba (scroll rokne ke liye chhota chahiye)")
    reg = []
    frame(cx_, 0.8, {}, reg)
    big = max([b[3] - b[1] for (b, s_, tg_) in reg if tg_ in ("q1", "q2")] or [0])
    if big < 90:
        six.append(f"pehle second ka text chhota ({big}px)")
    if six:
        bad += ["6 aakarshan: " + x for x in six]
    else:
        good.append(f"6 aakarshan ✅ contrast {_cr(dk_, b_):.0f}:1, hook {len((cx_['q1'] + ' ' + cx_['q2']).split())} shabd, pehla text {big}px")
    good.append("5 owner ✅ - neeche button (bina aapki haan ke slot tak ruki rahegi, phir purane niyam se)")
    return (not bad), (["❌ " + b for b in bad] + good)


# ---------------------------------------------------------------- audio + video
def render(cx_, out_dir):
    """v3.8.2: har scene ki awaaz ALAG banti hai (saans/ruk ke saath), scene ki lambai usi awaaz se - awaaz aur screen hamesha saath.
    Pehle poora script ek saans mein 1.06x par bolta tha (24.7s bina ruke) aur CTA bolte waqt screen kuch aur dikhati thi."""
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    segs = cx_["segs"]
    lens, wavs = {}, {}
    try:
        from . import tts
        for i, (key, txt) in enumerate(segs):
            w_ = out_dir / f"v_{key}.wav"
            lens[key] = tts.synth(say_clean(txt), str(w_), 1 if i else 0, len(segs))     # sirf hook thoda josh se, baaki saaf raftaar
            wavs[key] = w_
    except Exception as e:
        log(f"svcvideo tts: {e}")
        lens, wavs = {}, {}
    cx_["tl"] = tl = make_tl(lens)
    cx_["lens"] = lens
    dur = tl["dur"]
    vdur = sum(lens.values())
    n = int(dur * FPS)
    mp4 = out_dir / "video.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-"]
    if wavs:
        keys = [k for k, _ in segs if k in wavs]
        for k in keys:
            cmd += ["-i", str(wavs[k])]
        parts = []                                    # har awaaz apne scene ki lambai tak chup se bhari, phir jod (concat) - purane ffmpeg par bhi
        for j, k in enumerate(keys):
            sl = tl[k][1] - tl[k][0]
            parts.append(f"[{j + 1}:a]aresample=24000,aformat=channel_layouts=mono,apad=whole_dur={sl:.3f},atrim=0:{sl:.3f}[a{j}]")
        mix = "".join(f"[a{j}]" for j in range(len(keys)))
        cmd += ["-filter_complex", ";".join(parts) + f";{mix}concat=n={len(keys)}:v=0:a=1,apad,atrim=0:{dur:.2f},"
                f"loudnorm=I=-14:TP=-1.5[a]", "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-threads", "2",
            "-movflags", "+faststart", "-t", f"{dur:.2f}", str(mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cache, thumbs = {}, []
    want = {int(1.4 * FPS): "t1.jpg", int((tl["k0"][0] + 1.6) * FPS): "t2.jpg", int((dur - 1.5) * FPS): "t3.jpg"}
    for i in range(n):
        fr = frame(cx_, min(i / FPS, dur - .01), cache)
        if i in want:
            fr.save(out_dir / want[i], quality=92)
            thumbs.append(str(out_dir / want[i]))
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg fail")
    for w_ in wavs.values():
        try:
            w_.unlink()
        except Exception:
            pass
    return str(mp4), sorted(thumbs), dur, vdur


def meta_for(cx_, brand, video, thumbs, dur):
    names = ", ".join(r["name"] for r in cx_["rows"][:4])
    title = f"{TAG1} — {TAG2} | {cx_['rows'][0]['name']} {_rs(cx_['rows'][0]['price'])} se"[:95]
    rows = "\n".join(f"• {r['name']}: {_rs(r['price'])} se" + (f" (is hafte, {r['sale_end']} tak)" if r["was"] else "")
                     for r in cx_["rows"])
    madad = any(r["group"] == "मदद" for r in cx_["rows"])
    desc = (f"Koi bhi digital kaam — ho jayega. Hindi mein likhiye, jaise ghar mein bolte hain.\n{rows}\n"
            f"Pehle baat, phir likhit rate, phir kaam. Dost ko bhejiye - uske bill ka 10% aapka (₹300+ bill par).\n"
            + ("Form madad: OTP/password sirf aap daalte hain; sarkari fees portal par aap khud bharte hain. "
               "Hum sarkari vibhag nahi hain - sirf madad karte hain.\n" if madad else "")
            + (f"Code {CODES[brand]} = 10% tak chhoot (har kaam ki nichli seema ke andar).\n" if brand in CODES else "")
            + f"Comment mein apna kaam likhiye · Rate list: {SITE_TXT}\n{BRANDS[brand]['tags']} #SabHisaabServices")
    title, desc = fix_words(title), fix_words(desc)
    return {"video": video, "thumbs": thumbs, "duration": dur, "title": title, "description": desc, "brand": brand,
            "page": "/services-list", "format": "short", "tags": ["sabhisaab services", "online form madad", "resume", names[:60]],
            "design": "services_ad", "svc_set": [r["id"] for r in cx_["rows"]], "svc_item": cx_["rows"][0]["id"],
            "svc_look": cx_["look"], "topic": names}


# ---------------------------------------------------------------- daily job (purane pipeline ke raaste)
def _slot_dt(hhmm, day):
    from . import pipeline
    h_, m_ = (int(x) for x in hhmm.split(":"))
    n = pipeline.now()
    d = n.replace(year=day.year, month=day.month, day=day.day, hour=h_, minute=m_, second=0, microsecond=0)
    return d


def make_day(sample=False, only=None, day=None):
    """Aaj ke 4 video (4 slot) -> 5 round audit -> pass = pipeline job (manzoori/slot), fail = ruki + wajah owner ko."""
    from . import pipeline, tg
    dd = datetime.date.fromisoformat(day) if day else pipeline.now().date()
    plan = pick_day(day=str(dd))
    made = []
    for brand, v in plan.items():
        if only and brand != only:
            continue
        jid = f"svc{brand[:2]}{datetime.datetime.now().strftime('%m%d%H%M%S')}"
        out = OUT / jid
        try:
            cx_ = ctx_for(v, brand, str(dd))
            video, thumbs, dur, vdur = render(cx_, out)
            meta = meta_for(cx_, brand, video, thumbs, dur)
            ok, rep = audit_video(cx_, meta, video, vdur)
        except Exception as e:
            log(f"svcvideo {brand}: {e}")
            tg.alert("yellow", f"🎬 Services video ({BRANDS[brand]['name']}) nahi bani: {str(e)[:160]}")
            continue
        (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        (out / "audit.txt").write_text("\n".join(rep), encoding="utf-8")
        _append_audit(jid, brand, ok, rep)
        if not ok:
            tg.alert("red", f"⛔ Services video ({BRANDS[brand]['name']}) AUDIT FAIL - publish NAHI hogi:\n" + "\n".join(rep[:10]))
            continue
        if not sample:
            _hist_add({"day": str(dd), "set": v["set"], "item": v["set"][0], "look": v["look"], "hook": v["hook"],
                       "lay": v["lay"], "brand": brand, "slot": v["slot"], "jid": jid})
        slot = _slot_dt(v["slot"], dd)
        if slot < pipeline.now() and not sample:
            slot = pipeline.now() + datetime.timedelta(minutes=20)
        pipeline.save_job(jid, {"brand": brand, "status": "waiting", "slot": slot.isoformat(),
                                "created": pipeline.now().isoformat(),
                                "reason": "test video" if sample else "roz ka schedule", "meta": str(out),
                                "title": meta["title"], "topic_key": f"svc:{'-'.join(v['set'])}:{v['look']}:{v['hook']}",
                                "topic_kind": "services", "style": "services_ad"})
        pipeline._send_for_approval(jid, meta, [("✅", r[2:] if r.startswith("1") else r) for r in rep if "✅" in r][:5])
        made.append(jid)
    return plan, made


def _append_audit(jid, brand, ok, rep):
    DIR.mkdir(parents=True, exist_ok=True)
    with open(DIR / "video_audit.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"), "jid": jid, "brand": brand, "ok": ok,
                            "rep": rep}, ensure_ascii=False) + "\n")


def tick(run):
    """Raat 01:30-04:30 (05:00 wala slot pehle): koi video 'making' na ho tab, din mein ek baar - 4 video."""
    if not state.get("svc_video_on"):
        return
    from . import pipeline
    n = pipeline.now()
    d = str(n.date())
    if state.get("svc_video_day") == d or not ("01:30" <= n.strftime("%H:%M") <= "04:30"):
        return
    if any(j.get("status") == "making" for j in pipeline.jobs().values()):
        return
    state.put("svc_video_day", d)
    if (state.get("svc_holiday_until") or "") >= d:              # chhutti mode: naya kaam mat bulao
        return
    try:                                                        # kaam ki line lambi = aaj video nahi (jhootha vaada nahi)
        from . import svc as _S
        open_ = sum(1 for lid in _S.leads() if (_S.lead_state(lid).get("status") in ("accepted", "paid", "working")))
        if open_ >= int(state.get("svc_cap") or 8):
            from . import tg
            tg.say(f"⏸ Aaj services video nahi bani: {open_} kaam chal rahe hain (seema {state.get('svc_cap') or 8}). "
                   "Kaam kam hote hi kal se apne aap. Seema badlein: 'services seema 12'")
            return
    except Exception as e:
        log(f"svc cap: {e}")
    run(make_day)


def on_text(t, run):
    from . import tg, pipeline
    tl = t.lower().strip()
    if tl == "services video chalu":
        state.put("svc_video_on", True)
        if pipeline.max_uploads() < 14:
            state.put("max_uploads", 14)
        return tg.say("✅ Services video CHALU: roz raat 01:30 ke baad 4 alag video (6-6 kaam), 5 round audit, phir "
                      "IST 05:00 · 07:00 · 18:00 · 20:00 par (har slot alag brand). Fail = ruki + wajah. Band: 'services video band'.")
    m = re.match(r"services chhutti (\d+)$", tl)
    if m:
        till = (datetime.date.today() + datetime.timedelta(days=int(m.group(1)))).isoformat()
        state.put("svc_holiday_until", till)
        return tg.say(f"🏖 Chhutti {till} tak: services video ruki. Naye lead phir bhi aayenge (form chalu) - unhe sachcha jawab "
                      f"dein ki {till} ke baad kaam hoga. Wapas: 'services chhutti 0'")
    m = re.match(r"services seema (\d+)$", tl)
    if m:
        state.put("svc_cap", int(m.group(1)))
        return tg.say(f"✔ Ek saath max {m.group(1)} kaam - isse zyada chal rahe hon to us din services video nahi banegi.")
    m = re.match(r"services shabd (.+?)\s*=\s*(.+)$", t.strip(), re.I)
    if m:
        fx = dict(state.get("svc_word_fix") or {})
        fx[m.group(1).strip()] = m.group(2).strip()
        state.put("svc_word_fix", fx)
        return tg.say(f"✔ Shabdkosh: '{m.group(1).strip()}' → '{m.group(2).strip()}' (video ki screen + awaaz + title, aage hamesha). "
                      f"Poori list: services shabd list")
    if tl in ("services shabd list", "services shabdkosh"):
        fx = {**WORDS, **(state.get("svc_word_fix") or {})}
        return tg.say("📖 Services shabdkosh (screen + awaaz):\n" + "\n".join(f"{a} → {b}" for a, b in fx.items() if len(a) > 1)[:3500])
    m = re.match(r"services awaaz sudhar (.+?)\s*=\s*(.+)$", t.strip(), re.I)
    if m:
        fx = dict(state.get("svc_say_fix") or {})
        fx[m.group(1).strip()] = m.group(2).strip()
        state.put("svc_say_fix", fx)
        return tg.say(f"✔ Ab video mein '{m.group(1).strip()}' ki jagah '{m.group(2).strip()}' bola jayega. Sunne ke liye: services awaaz jaanch")
    if tl in ("services awaaz jaanch", "services voice test"):
        def _aj():
            import numpy as np
            import soundfile as sf
            from . import tts
            words = [v[6] for v in KAAM.values()] + [f"{TAG1}, {TAG2}", "हिंदी में लिखिए, जैसे घर में बोलते हैं",
                                                     "कमेंट में अपना काम लिखिए। सब हिसाब डॉट कॉम, स्लैश सर्विसेज़ लिस्ट"]
            out, parts = OUT / "awaaz_jaanch", []
            out.mkdir(parents=True, exist_ok=True)
            for n_, w_ in enumerate(words):
                f_ = out / f"{n_}.wav"
                tts.synth(say_clean(w_), str(f_), 1, 2)
                a_, sr_ = sf.read(str(f_), dtype="float32")
                parts += [a_ if a_.ndim == 1 else a_.mean(axis=1), np.zeros(int(sr_ * .9), dtype="float32")]
            sf.write(str(out / "sab.wav"), np.concatenate(parts), sr_)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "sab.wav"), "-c:a", "libmp3lame", "-q:a", "4",
                            str(out / "awaaz_jaanch.mp3")], check=True)
            with open(out / "awaaz_jaanch.mp3", "rb") as fh:
                tg.call("sendAudio", {"chat_id": tg._chat(), "caption": "🔊 Services video ke shabd (isi kram mein):\n" +
                                      "\n".join(f"{i + 1}. {w}" for i, w in enumerate(words))[:1000]}, files={"audio": fh})
            tg.say("Koi shabd galat bola gaya? Likhiye: services awaaz sudhar रिज्यूम = रेज़्यूमे  (baayen jo likha hai, daayen jaisa bolna hai)")
        tg.say("🔊 Shabd bol kar bhej raha hoon (1-2 min)...")
        run(_aj)
        return True
    if tl == "services video band":
        state.put("svc_video_on", False)
        return tg.say("⏸ Services video band.")
    if tl in ("services video namoona", "services video sample"):
        return tg.say("🎬 Kis brand ka services namoona banaun? (usi brand ka naam + logo lagega; button dabaye bina kahin post nahi)",
                      tg.inline([[(BRANDS[b]["name"], f"sv:vn:{b}") for b in list(BRANDS)[:2]],
                                 [(BRANDS[b]["name"], f"sv:vn:{b}") for b in list(BRANDS)[2:]]]))
    m = re.match(r"services video namoona (\w+)$", tl)
    if m and m.group(1) in BRANDS:
        return namoona(m.group(1), run)
    if tl in ("services video report", "services video haal"):
        H_ = _hist()
        A = []
        f = DIR / "video_audit.jsonl"
        if f.exists():
            A = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()[-20:] if x.strip()]
        fails = sum(1 for a in A if not a.get("ok"))
        return tg.say(f"🎬 Services video: kul {len(H_)} bani (zindagi bhar dohrav 0) · pichhle {len(A)} audit mein {fails} ruki\n" +
                      "\n".join(f"{h['day']} {h.get('slot', '')} {h['brand']}: {', '.join(h.get('set') or [h.get('item', '')])[:60]}"
                                for h in H_[-8:]) + "\nViews/lead: 'services report 7'")
    return None


def namoona(brand, run):
    from . import tg
    tg.say(f"🎬 {BRANDS[brand]['name']} ka services namoona ban raha hai (3-5 min, 6 round audit). Aane par '🚀 Abhi daalo' dabate hi "
           "turant post hoga; bina button kahin nahi jayega.")
    run(lambda: make_day(sample=True, only=brand))
    return True

