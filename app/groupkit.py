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
    if kind == "tool":
        state.put("grp_used", ((state.get("grp_used") or []) + [s])[-300:])
    tg.say("👥 AAJ KA GROUP POST (7:30) - neeche ke 2 sandesh copy karke paste karein:\n"
           "1️⃣ Facebook group / WhatsApp / Threads / Facebook page → pehla (link click hota hai)\n"
           "2️⃣ Instagram / Moj / ShareChat → doosra (wahan caption ka link click nahi hota)\n"
           "Niyam: din mein 2-3 group, ek group mein hafte mein max 2 baar, har jagah group ke niyam padh kar. "
           "Band: 'group post band'")
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
