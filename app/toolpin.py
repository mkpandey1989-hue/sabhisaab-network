"""v2.9.1: WEBSITE TOOL PIN - Pinterest par roz EK pin website ke kisi tool/guide page ka (Pinterest ke link click hote hain -
website traffic ka seedha raasta). Niyam: din mein 1 (Pinterest ki roz ki seema + spam-suraksha can_pin_now ke andar), ek page
60 din mein ek baar, chitra apna banaya (1000x1500), title = page ka asli naam (bhramak nahi), SIP/FD/loan wale page 3 aam
brand par nahi (owner ka niyam). Brand din ke hisaab se baari-baari.
"""
import datetime
import re

from . import state
from .config import BRANDS, SITE, DATA
from .log import log

KEYS = {"deals": r"discount|offer|gst|sale|price|cashback|chhoot|shopping|bijli|electricity|mobile|recharge",
        "money": r"emi|tax|salary|percent|interest|byaj|ctc|hra|gratuity|epf|budget|inflation|tds",
        "pahadi": r"nali|mutthi|pahad|uttarakhand|bigha|mausam|weather",
        "sunonatak": r"age|umar|date|din|typing|unit|converter|stopwatch|random|number|bmi|time|calendar"}
ORDER = ["deals", "money", "sunonatak", "pahadi", "deals", "money", "sunonatak"]


def pick(brand, pages, used, today=None):
    """Brand ke vishay ka ek page jo 60 din mein pin nahi hua. -> (path, title) ya None. Bina network (test)."""
    from . import qplan
    today = today or datetime.date.today()
    cut = str(today - datetime.timedelta(days=60))
    rx = re.compile(KEYS[brand], re.I)
    rows = []
    for k, v in (pages or {}).items():
        p = "/" + str(k).strip("/")
        t = (v or {}).get("title") or ""
        if p in ("/", "/jawab", "/links", "/privacy", "/terms", "/about", "/contact", "/author") or not t:
            continue
        if not rx.search(p + " " + t) or qplan.blocked(brand, p + " " + t):
            continue
        if used.get(p, "") >= cut:
            continue
        rows.append((used.get(p, ""), p, t))
    rows.sort()
    return (rows[0][1], rows[0][2]) if rows else None


def image(title, brand):
    from PIL import Image, ImageDraw
    from . import text as T
    from .webstory import COLORS
    c1, c2 = COLORS.get(brand, ("#111827", "#6366F1"))
    w, h = 1000, 1500
    img = Image.new("RGB", (w, h), c1)
    d = ImageDraw.Draw(img)
    r1, g1, b1 = (int(c1[i:i + 2], 16) for i in (1, 3, 5))
    r2, g2, b2 = (int(c2[i:i + 2], 16) for i in (1, 3, 5))
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=(int(r1 + (r2 - r1) * t), int(g1 + (g2 - g1) * t), int(b1 + (b2 - b1) * t)))
    clean = re.sub(r"\s*\|\s*Sab Hisaab.*$", "", title)
    sz, lines = T.fit(clean, w - 120, 700, start=96, smallest=52)
    y = 360
    for ln in lines:
        T.draw(d, ((w - T.width(ln, sz)) / 2, y), ln, sz, (255, 255, 255))
        y += int(sz * 1.3)
    for i, s in enumerate(["• Free", "• Hindi mein", "• Bina login"]):
        T.draw(d, ((w - T.width(s, 54)) / 2, y + 80 + i * 80), s, 54, (255, 240, 180))
    T.draw(d, ((w - T.width("sabhisaab.com", 60)) / 2, h - 170), "sabhisaab.com", 60, (255, 255, 255))
    out = DATA / "toolpin.jpg"
    img.save(out, quality=90)
    return out


def run():
    from . import pinterest, siteknow
    today = datetime.date.today()
    brand = ORDER[today.weekday()]
    used = dict(state.get("toolpin_used") or {})
    got = pick(brand, siteknow.pages() or {}, used, today)
    if not got:
        return "toolpin: koi naya page nahi"
    path, title = got
    link = f"{SITE}{path}?utm_source=pinterest&utm_medium=pin&utm_campaign={brand}"
    ok_, why = pinterest.can_pin_now(brand, link)
    if not ok_:
        return f"toolpin: ruka ({why})"
    try:
        img = image(title, brand)
        clean = re.sub(r"\s*\|\s*Sab Hisaab.*$", "", title)
        u = pinterest.post_pin(brand, img, clean[:95], f"{clean} - free, Hindi mein, bina login. Seedha hisaab: {SITE}{path}", link,
                               section="tool")            # v3.0.0: 'Free Calculators & Tools' khane mein
    except Exception as e:
        log(f"toolpin: {e}")
        return f"toolpin: nahi gaya ({str(e)[:100]})"
    used[path] = str(today)
    state.put("toolpin_used", used)
    return f"📌 Website tool pin: {clean} -> {u}"
