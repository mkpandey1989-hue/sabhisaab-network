"""v3.4.1 (16 Nov 2026 raat) - owner: "Quora, WhatsApp status, Facebook group - jo karne ko bola tha wo bhi complete karo".

Ye teeno jagah koi bot apne aap post NAHI kar sakta: Facebook ne Groups API 2024 mein band kiya, Quora ka koi API nahi, WhatsApp
Status ka API nahi - aur bot se zabardasti post = spam/account band. Isliye bot roz 19:15 par owner ko 3 TAIYAAR sandesh bhejta hai,
har ek alag (lamba dabao -> Copy -> wahan paste). Sab text website ke APNE page/sawal se (bot naya content nahi likhta - niyam).
Har link par alag UTM (whatsapp_status / fb_group / quora) - GA4 mein dikhega kahan se kitne aaye.

1) WhatsApp Status: aaj ka quiz sawal + 4 vikalp + jawab ka seedha link (jawab likha nahi - log site par jayein)
2) Facebook group (apna 'Pahadi Hisaab Parivar' ya jinmein aap ho): ek Uttarakhand page - naam, 2 line, link
3) Quora: ek asli sawal (page ke FAQ se) + uska jawab (page ka hi) + 'poora hisaab' link. Quora par wahi sawal khoj kar
   jawab dein; apne shabdon mein 1 line jodna achha (copy-paste jawab Quora kam dikhata hai).
Hukum: 'share kit' (abhi) | 'share kit band' / 'share kit chalu'.
"""
import datetime
import html as _h
import json
import re

from . import state, tg
from .config import IST, SITE
from .log import log

HHMM = "19:15"


def _site():
    from . import website
    return website.DIR / "site"


def _txt(s):
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", str(s or "")))).strip()


def _u(path, src, camp):
    return f"{SITE}{path}?utm_source={src}&utm_medium=share&utm_campaign={camp}"


def faqs(html):
    """Page ke FAQPage JSON-LD se [(sawal, jawab)]."""
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html or "", re.S):
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        for x in (d if isinstance(d, list) else [d]):
            for g in ([x] + list(x.get("@graph") or [])) if isinstance(x, dict) else []:
                if isinstance(g, dict) and g.get("@type") == "FAQPage":
                    for q in g.get("mainEntity") or []:
                        a = (q.get("acceptedAnswer") or {}).get("text")
                        if q.get("name") and a:
                            out.append((_txt(q["name"]), _txt(a)))
    return out


def title_desc(html):
    t = re.search(r"<title>([^<]+)</title>", html or "")
    d = re.search(r'<meta name="description" content="([^"]+)"', html or "")
    title = re.sub(r"\s*[|–-]\s*Sab Hisaab.*$", "", _txt(t.group(1))) if t else ""
    return title, _txt(d.group(1)) if d else ""


# ---------------------------------------------------------------- 1) WhatsApp status
def status_text(today=None):
    from .answers import answer_url
    today = today or datetime.date.today()
    lst = [e for e in reversed(state.get("answer_key") or []) if e.get("q") and e.get("opts")]
    e = next((x for x in lst if str(x.get("date", ""))[:10] == str(today)), lst[0] if lst else None)
    if not e:
        return None
    q = re.sub(r"\s*#\S+", "", _txt(e.get("q")))
    ops = "\n".join(f"{'ABCD'[i]}) {_txt(o)}" for i, o in enumerate((e.get("opts") or [])[:4]))
    link = answer_url(e.get("aid") or e.get("code"), "whatsapp_status", e.get("brand"))
    return f"🧠 आज का सवाल\n\n{q}\n\n{ops}\n\n👇 सही जवाब + तरीका:\n{link}"


# ---------------------------------------------------------------- 2) Facebook group
def group_text(today=None):
    today = today or datetime.date.today()
    site = _site()
    pub = state.get("pq_pub") or {}
    used = state.get("sk_group_used") or {}
    cand = sorted((used.get(s, ""), s) for s in pub if (site / f"{s}.html").exists())
    if not cand:
        return None, None
    s = cand[0][1]
    title, desc = title_desc((site / f"{s}.html").read_text(encoding="utf-8", errors="ignore"))
    if not title:
        return None, None
    return f"🏔️ {title}\n\n{desc}\n\n👉 पूरी जानकारी (फ्री, हिंदी में):\n{_u('/' + s, 'facebook', 'fb_group')}", s


# ---------------------------------------------------------------- 3) Quora
def quora_text():
    site = _site()
    used = state.get("sk_quora_used") or {}
    best = None
    for f in sorted(site.glob("*.html")):
        s = f.stem
        if s in ("index", "jawab", "links", "privacy", "terms", "about", "contact", "author", "404") or s.startswith("google"):
            continue
        last = used.get(s, "")
        if best and last >= best[0]:
            continue
        try:
            fq = faqs(f.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        fq = [x for x in fq if 25 <= len(x[1]) <= 700 and x[0].endswith("?")]
        if fq:
            best = (last, s, fq[0])
            if not last:
                break
    if not best:
        return None, None
    _, s, (q, a) = best
    title, _ = title_desc((site / f"{s}.html").read_text(encoding="utf-8", errors="ignore"))
    return (f"🔎 Quora par ye sawal khojein (ya naya poochhein): {q}\n\n— JAWAB (copy) —\n{a}\n\n"
            f"पूरा हिसाब / कैलकुलेटर ({title}): {_u('/' + s, 'quora', 'answer')}\n\n"
            "💡 Upar apne shabdon mein 1 line jod dein (jaise apna anubhav) - Quora aise jawab zyada dikhata hai."), s


# ---------------------------------------------------------------- roz
def due(now=None):
    now = now or datetime.datetime.now(IST)
    return (now.strftime("%H:%M") >= HHMM and state.get("sk_day") != str(now.date()) and state.get("sk_on", True)
            and not state.get("paused"))


def run(manual=False):
    day = str(datetime.date.today())
    if not manual:
        state.put("sk_day", day)
    parts = []
    try:
        w = status_text()
        if w:
            parts.append(("📱 WHATSAPP STATUS (lamba dabao → Copy → Status par paste; saath mein aaj ki video ka screenshot lagayein)", w))
    except Exception as e:
        log(f"sharekit wa: {e}")
    try:
        g, gs = group_text()
        if g:
            parts.append(("👥 FACEBOOK GROUP (apne 'Pahadi Hisaab Parivar' group ya jis group mein aap ho - niyam padh kar)", g))
            state.update("sk_group_used", lambda d: {**(d or {}), gs: day}, {})
    except Exception as e:
        log(f"sharekit fb: {e}")
    try:
        q, qs = quora_text()
        if q:
            parts.append(("❓ QUORA (roz 1 jawab = mahino tak Google se log)", q))
            state.update("sk_quora_used", lambda d: {**(d or {}), qs: day}, {})
    except Exception as e:
        log(f"sharekit quora: {e}")
    if not parts:
        return "Share kit: aaj kuch taiyaar nahi mila."
    tg.say("🧰 AAJ KI SHARE KIT - 3 jagah, 5 minute. Har sandesh alag hai: lamba dabao → Copy → wahan paste.")
    for head, body in parts:
        tg.say(head)
        tg.say(body)
    return None


def on_text(tl):
    if tl in ("share kit", "sharekit", "aaj ki share kit", "share kit do"):
        r = run(manual=True)
        return tg.say(r) if r else True
    if tl in ("share kit band", "share kit chalu"):
        state.put("sk_on", tl.endswith("chalu"))
        return tg.say("🧰 Roz 19:15 ki share kit: " + ("CHALU" if tl.endswith("chalu") else "BAND"))
    return None
