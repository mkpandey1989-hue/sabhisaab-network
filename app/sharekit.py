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
    try:                                            # v3.4.34: sirf wahi jiska jawab website par LIVE hai
        from .sawalpost import live_ids as _lv
        _L = _lv()
        if _L is not None:
            lst = [x for x in lst if str(x.get("aid") or x.get("code")) in _L]
    except Exception:
        pass
    try:                                            # v3.4.25: owner ko pehle diya ('sawal wali post') dobara nahi
        from .sawalpost import given as _gv
        _g = set(_gv("whatsapp"))
        lst = [x for x in lst if str(x.get("aid") or x.get("code")) not in _g] or lst
    except Exception:
        pass
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


def quiz_group_text():
    """Dusre ke group ke liye: aaj ka ek sawal (WhatsApp wale se alag) + 4 vikalp + 'aapka jawab?' + jawab link (fb_group UTM).
    Sawal poochne wali post group mein sabse zyada chalti hai (log comment karte hain) - seedha link-dump nahi."""
    from .answers import answer_url
    lst = [e for e in reversed(state.get("answer_key") or []) if e.get("q") and e.get("opts")]
    try:                                            # v3.4.34: sirf wahi jiska jawab website par LIVE hai
        from .sawalpost import live_ids as _lv
        _L = _lv()
        if _L is not None:
            lst = [x for x in lst if str(x.get("aid") or x.get("code")) in _L]
    except Exception:
        pass
    try:                                            # v3.4.25
        from .sawalpost import given as _gv
        _g = set(_gv("fbgroup"))
        lst = [x for x in lst if str(x.get("aid") or x.get("code")) not in _g] or lst
    except Exception:
        pass
    if len(lst) < 1:
        return None
    e = lst[1] if len(lst) > 1 else lst[0]          # WhatsApp status wale se alag sawal
    try:                                            # v3.4.27: 3 line (group mein 'See more' se pehle link dikhe)
        from .sawalpost import fmt as _fmt
        return _fmt(e, "fbgroup")[0][1]
    except Exception:
        pass
    q = re.sub(r"\s*#\S+", "", _txt(e.get("q")))
    ops = "  ".join(f"{'ABCD'[i]}) {_txt(o)}" for i, o in enumerate((e.get("opts") or [])[:4]))
    link = answer_url(e.get("aid") or e.get("code"), "facebook_group", e.get("brand"))
    return f"🧠 {q}\n{ops}\n👇 सही जवाब: {link}\n🤔 पहले खुद सोचिए, फिर जवाब देखिए"


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
            try:
                from .sawalpost import note_from_text as _nft
                _nft(w)                                 # v3.4.25: diya hua sawal dobara nahi
            except Exception:
                pass
            parts.append(("📱 WHATSAPP STATUS (lamba dabao → Copy → Status par paste; saath mein aaj ki video ka screenshot lagayein)", w))
    except Exception as e:
        log(f"sharekit wa: {e}")
    banner = None
    try:
        g, gs = group_text()
        if g:
            ig = None
            try:                                        # v3.4.21b: groupkit ka behtar text + banner (alag 19:30 sandesh band - dohra tha)
                from . import groupkit as _GK
                from .config import TMP
                h = (_site() / f"{gs}.html").read_text(encoding="utf-8", errors="ignore")
                g, ig, _l = _GK.build(gs, "uk", h)
                t_, _d = _GK.card(h)
                lg = _site() / "icon-512.png"
                banner = _GK.banner("uk", t_, _GK.points(h), gs, TMP / f"grp_{gs}.jpg", lg if lg.exists() else None)
            except Exception as e:
                log(f"sharekit banner: {e}")
            parts.append(("👥 FACEBOOK GROUP / WHATSAPP / THREADS - upar wali BANNER photo lagao, phir ye text (link click hota hai)", g))
            if ig:
                parts.append(("📸 INSTAGRAM / MOJ / SHARECHAT - wahi banner + ye chhota text (yahan caption ka link click nahi hota)", ig))
            state.update("sk_group_used", lambda d: {**(d or {}), gs: day}, {})
    except Exception as e:
        log(f"sharekit fb: {e}")
    try:                                                # v3.4.4: dusre ke group (aap admin nahi) - quiz wala text
        gq = quiz_group_text()
        if gq:
            try:
                from .sawalpost import note_from_text as _nft
                _nft(gq, "fbgroup")
            except Exception:
                pass
            parts.append(("👥 DUSRE KE FACEBOOK GROUP (GK / exam / pahadi groups - aap member ho, admin nahi). Facebook niyam: "
                          "din mein 2-3 group se zyada nahi, ek hi text ek saath sab group mein nahi, group ke 'Rules' padhein; "
                          "jahan link mana ho wahan link hata kar 'jawab comment mein' likhein. Admin manzoori maange to "
                          "intezaar karein - baar-baar post = spam.", gq))
    except Exception as e:
        log(f"sharekit fbq: {e}")
    qp = None
    try:                                                # v3.4.23: ASLI Quora sawal (link ke saath) + taiyaar jawab
        from . import quoradraft as _QDk
        qp = _QDk.daily_pack()
        if qp:
            parts.append(qp)
    except Exception as e:
        log(f"sharekit quora find: {e}")
    if not qp:
        try:
            q, qs = quora_text()
            if q:
                from . import quoradraft as _QDs
                q0 = q.split("\n", 1)[0].replace("🔎 Quora par ye sawal khojein (ya naya poochhein): ", "").strip()
                parts.append((f"❓ QUORA - is link par sawal dhoondho (na mile to yahi sawal khud poochho, phir jawab do):\n"
                              f"{_QDs.search_url(q0)}", q))
                state.update("sk_quora_used", lambda d: {**(d or {}), qs: day}, {})
        except Exception as e:
            log(f"sharekit quora: {e}")
    if not parts:
        return "Share kit: aaj kuch taiyaar nahi mila."
    tg.say("🧰 AAJ KI SHARE KIT - 5 minute. Har sandesh alag hai: lamba dabao → Copy → wahan paste.")
    for head, body in parts:
        tg.say(head)
        if banner and head.startswith("👥 FACEBOOK GROUP /"):
            try:
                with open(banner, "rb") as f:
                    tg.call("sendPhoto", {"chat_id": tg._chat(), "caption": "🖼 BANNER - photo par lamba dabao → Save, phir post mein lagao"},
                            {"photo": ("banner.jpg", f.read(), "image/jpeg")})
            except Exception as e:
                log(f"sharekit photo: {e}")
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
