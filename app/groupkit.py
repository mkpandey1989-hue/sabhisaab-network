"""v3.4.20 (17 Nov 2026) - owner: "roz shaam 7:30 baje group ke liye post do - jaankari jaisi lage (admin approve kar de),
link clickable ho, FB group / Instagram / Threads / Moj / WhatsApp sab mein kaam aaye; mera personal naam kabhi nahi".

Bot FB group mein KHUD post nahi karta (Facebook auto-post band kar deta hai - niyam). Bot roz 19:30 owner ko 'copy karo,
paste karo' kit deta hai:
  1) Group/WhatsApp/Threads/Facebook ke liye: shirshak + kaam ki 4-5 baatein (page ke apne heading/sawal) + poora link (UTM).
  2) Instagram/Moj/ShareChat ke liye chhota roop (in par caption ka link click nahi hota - isliye 'link bio mein').
Page: aaj share hua Uttarakhand page; na ho to ek free calculator/guide (har din alag, list poori hone tak dohraav nahi).
Naam: sirf 'Sab Hisaab' - owner ka naam kabhi nahi. Hashtag kam (3-4), koi 'click karo jaldi' jaisi spam bhasha nahi.
"""
import datetime
import html as H
import re

from . import state, tg
from .config import IST
from .log import log

SITE = "https://sabhisaab.com"
HHMM = "19:30"
SKIP_H2 = ("srot", "sandarbh", "सवाल-जवाब", "faq", "aksar poochhe", "related", "judey", "share", "comment", "disclaimer")


def _site():
    from .website import DIR
    return DIR / "site"


def points(html_text, n=5):
    """Page ke apne H2 (srot/FAQ/share chhod kar) -> 'is page par kya milega' ki suchi."""
    body = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", html_text)
    out = []
    for h in re.findall(r"(?is)<h2[^>]*>(.*?)</h2>", body):
        t = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", h))).strip(" :-")
        if 6 <= len(t) <= 90 and not any(w in t.lower() for w in SKIP_H2) and t not in out:
            out.append(t)
        if len(out) >= n:
            break
    return out


def card(html_text):
    t = re.search(r"<title>(.*?)</title>", html_text, re.S)
    d = re.search(r'<meta name="description" content="([^"]*)"', html_text)
    title = H.unescape(t.group(1)).split(" | ")[0].strip() if t else ""
    return title, (H.unescape(d.group(1)).strip() if d else "")


def pick(today=None):
    """-> (slug, kind) - aaj ka UK page, warna agla free tool."""
    today = str(today or datetime.date.today())
    site = _site()
    for s, d in (state.get("uk_shared") or {}).items():
        if d == today and (site / f"{s}.html").exists():
            return s, "uk"
    try:
        from .answers import TOOL_NAMES
    except Exception:
        TOOL_NAMES = {}
    used = state.get("grp_used") or []
    left = [k for k in TOOL_NAMES if k not in used and (site / f"{k}.html").exists()]
    if not left:
        used, left = [], [k for k in TOOL_NAMES if (site / f"{k}.html").exists()]
    return (left[0], "tool") if left else (None, None)


def build(slug, kind, html_text):
    title, desc = card(html_text)
    pts = points(html_text)
    link = f"{SITE}/{slug}?utm_source=fbgroup&utm_medium=social&utm_campaign=group_{kind}"
    head = ("🏔️ " if kind == "uk" else "🧮 ") + title
    lines = [head, "", desc, ""]
    if pts:
        lines.append("Is page par:" if kind == "uk" else "Isme milega:")
        lines += [f"✔️ {p}" for p in pts]
        lines.append("")
    lines += [("Poori jaankari (free, bina login): " if kind == "uk" else "Free calculator (Hindi, bina login): ") + link, "",
              "Aapke kaam aaye to apne logon ke saath share karein 🙏",
              "#Uttarakhand #PahadiJankari #Hindi" if kind == "uk" else "#HindiCalculator #PaisaGyaan #SabHisaab"]
    group = "\n".join(lines).strip()
    short = "\n".join([head, "", desc, ""] + [f"✔️ {p}" for p in pts[:3]] +
                      ["", "🔗 Link bio mein - Sab Hisaab", "#Uttarakhand #Hindi" if kind == "uk" else "#Calculator #Hindi"]).strip()
    return group, short, link


def due(now=None):
    now = now or datetime.datetime.now(IST)
    return (now.strftime("%H:%M") >= HHMM and state.get("grp_day") != str(now.date()) and state.get("grp_on", True)
            and not state.get("paused"))


def run():
    state.put("grp_day", str(datetime.date.today()))
    s, kind = pick()
    if not s:
        return None
    try:
        h = (_site() / f"{s}.html").read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        log(f"groupkit read: {e}")
        return None
    group, short, link = build(s, kind, h)
    ban = None
    try:                                           # v3.4.21: banner photo (post ke saath lagao - zyada log rukte hain)
        from .config import TMP
        title, _d = card(h)
        lg = _site() / "icon-512.png"
        ban = banner(kind, title, points(h), s, TMP / f"grp_{s}.jpg", lg if lg.exists() else None)
    except Exception as e:
        log(f"groupkit banner: {e}")
    if kind == "tool":
        state.put("grp_used", ((state.get("grp_used") or []) + [s])[-300:])
    tg.say("👥 AAJ KA GROUP POST (7:30) - neeche ke 2 sandesh copy karke paste karein:\n"
           "1️⃣ Facebook group / WhatsApp / Threads / Facebook page → pehla (link click hota hai)\n"
           "2️⃣ Instagram / Moj / ShareChat → doosra (wahan caption ka link click nahi hota)\n"
           "Niyam: din mein 2-3 group, ek group mein hafte mein max 2 baar, har jagah group ke niyam padh kar. "
           "Band: 'group post band'")
    if ban:
        try:
            with open(ban, "rb") as f:
                tg.call("sendPhoto", {"chat_id": tg._chat(), "caption": "🖼 Banner - pehle ye photo lagao, phir neeche ka text"},
                        {"photo": ("banner.jpg", f.read(), "image/jpeg")})
        except Exception as e:
            log(f"groupkit photo: {e}")
    tg.say(group)
    tg.say(short)
    return None


def on_text(tl):
    if tl in ("group post", "group post do", "aaj ka group post"):
        state.put("grp_day", "")
        run()
        return True
    if tl in ("group post band", "group post chalu"):
        state.put("grp_on", tl.endswith("chalu"))
        return tg.say("👥 Roz 7:30 ka group post: " + ("CHALU" if tl.endswith("chalu") else "BAND"))
    return None


# ------------------------------------------------------------------ v3.4.21: banner (group admin ko bhi achha lage)
BW, BH = 1080, 1350


def _short(p, n=62):
    p = re.sub(r"\s*\([^)]*\)", "", p).strip()
    return p if len(p) <= n else p[:n - 1].rsplit(" ", 1)[0] + "…"


def banner(kind, title, pts, slug, out_path, logo=None):
    """1080x1350 jaankari-banner: bada shirshak patti par, hare tick wali 4 baatein, neeche poora pata. Owner ka naam/photo nahi."""
    from PIL import Image, ImageDraw, ImageFilter
    from . import text as T
    img = Image.new("RGB", (BW, BH), "#ffffff")
    d = ImageDraw.Draw(img)
    top, bot = ((120, 190, 245), (235, 248, 255)) if kind == "uk" else ((15, 118, 110), (30, 58, 138))
    for y in range(BH):
        t = y / BH
        d.line([(0, y), (BW, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    if kind == "uk":                                   # pahad: 3 parat + barf
        d.ellipse([820, 120, 980, 280], fill=(255, 214, 90))
        for base, col, pk in ((760, (96, 125, 160), [(0, 760), (180, 470), (330, 620), (520, 380), (700, 600), (880, 430), (1080, 640)]),
                              (900, (52, 120, 80), [(0, 900), (220, 640), (420, 820), (640, 600), (860, 800), (1080, 650)]),
                              (1040, (30, 90, 55), [(0, 1040), (260, 850), (540, 1000), (800, 860), (1080, 980)])):
            d.polygon(pk + [(BW, BH), (0, BH)], fill=col)
        for (x, y) in ((520, 380), (180, 470), (880, 430)):
            d.polygon([(x, y), (x - 45, y + 55), (x + 45, y + 55)], fill=(250, 250, 255))
    else:
        for i in range(0, BW, 90):                      # halka grid (calculator ehsaas)
            d.line([(i, 0), (i, BH)], fill=(255, 255, 255, 30) if False else tuple(min(255, c + 18) for c in top), width=1)
        for i in range(0, BH, 90):
            d.line([(0, i), (BW, i)], fill=tuple(min(255, c + 18) for c in top), width=1)
    # shirshak patti (laal, tirchhi)
    t1, _, t2 = title.partition(":")
    t1, t2 = t1.strip(), (t2.strip() or "")
    if not t2 and "—" in t1:
        t1, _, t2 = t1.partition("—")
        t1, t2 = t1.strip(), t2.strip()
    l1 = T.wrap(t1, 84, BW - 140)[:2]
    l2 = T.wrap(t2, 62, BW - 140)[:2] if t2 else []
    hh = 40 + len(l1) * 100 + len(l2) * 78 + 30
    d.polygon([(30, 70), (BW - 30, 50), (BW - 50, 70 + hh), (50, 90 + hh)], fill=(200, 30, 40))
    y = 95
    for ln in l1:
        T.draw(d, (BW / 2 - T.width(ln, 84) / 2, y), ln, 84, (255, 255, 255), stroke=4, stroke_fill=(90, 0, 10))
        y += 100
    for ln in l2:
        T.draw(d, (BW / 2 - T.width(ln, 62) / 2, y), ln, 62, (255, 228, 70), stroke=3, stroke_fill=(90, 0, 10))
        y += 78
    # tick wali baatein
    y = 140 + hh
    for p in [_short(x) for x in pts[:4]]:
        lines = T.wrap(p, 44, BW - 260)[:2]
        bh = 30 + 58 * len(lines)
        sh = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([86, y + 8, BW - 74, y + bh + 8], radius=26, fill=(0, 0, 0, 90))
        img.paste(sh.filter(ImageFilter.GaussianBlur(6)), (0, 0), sh.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([80, y, BW - 80, y + bh], radius=26, fill=(255, 250, 220), outline=(255, 200, 40), width=4)
        d.ellipse([104, y + bh / 2 - 30, 164, y + bh / 2 + 30], fill=(22, 163, 74))
        d.line([(119, y + bh / 2), (131, y + bh / 2 + 13), (151, y + bh / 2 - 13)], fill=(255, 255, 255), width=8)
        yy = y + 14
        for ln in lines:
            T.draw(d, (186, yy), ln, 44, (20, 30, 60))
            yy += 58
        y += bh + 26
    # khaali jagah: bada 'FREE' tamga (calculator) - aankh khinchne ke liye
    if kind != "uk" and BH - 190 - y > 240:
        cx, cy, r = BW // 2, (y + BH - 190) // 2, min(170, (BH - 190 - y) // 2 - 20)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 210, 40), outline=(255, 255, 255), width=8)
        for txt, sz, dy in (("100%", 70, -r * 0.62), ("FREE", 92, -r * 0.18), ("Hindi mein", 40, r * 0.42)):
            T.draw(d, (cx - T.width(txt, sz) / 2, cy + dy - sz * 0.55), txt, sz, (150, 20, 30))
    # neeche ka pata
    by = BH - 190
    d.polygon([(0, by + 20), (BW, by), (BW, BH), (0, BH)], fill=(18, 52, 140))
    msg = "Poori jaankari FREE - bina login"
    T.draw(d, (60, by + 34), msg, 40, (255, 228, 70))
    url = f"sabhisaab.com/{slug}"
    fz = 52 if T.width(url, 52) < BW - 260 else 40
    T.draw(d, (60, by + 92), url, fz, (255, 255, 255))
    if logo:
        try:
            lg = Image.open(logo).convert("RGBA").resize((130, 130))
            img.paste(lg, (BW - 170, by + 30), lg)
        except Exception:
            pass
    img.save(out_path, "JPEG", quality=92)
    return out_path
