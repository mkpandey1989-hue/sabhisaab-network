"""v2.6.1 (owner 9 Nov: 'policy badle ya API ka naya feature aaye to bot khud dekhe; khud na ho paye to mere kaam ki list mein'):
POLICY + API BADLAAV WATCHER.

- Asli policy/changelog page (YouTube, Meta/Instagram/Threads, Pinterest, AdSense, Google Search, Bing, Gemini, Telegram) har 3 din
  ek baar padhta hai (har page ek request, 2 sec gap - koi bojh/spam nahi).
- Page ka text vaakya-vaakya hash; sirf NAYE vaakya nikalte hain (cookie/tareekh jaise chhote shor ko chhod kar).
- Naye vaakya + hamare setup ki jaankari -> Gemini: asar (none/low/high), kya badla, kya karna, naya API feature.
- high/low asar = Telegram alert (ek page ka ek alert, dohraav nahi). Karne layak kaam / naya API feature = PENDING mein apne aap
  (tasks.add) - bot khud nahi kar sakta to wahan se Claude/owner tak.
- Pehli baar sirf 'aadhaar' banta hai (alert nahi). Page padh na paye (JS page) to chup - report mein 'padh nahi paya'.
Kabhi nahi: kisi page ko baar-baar maarna, policy ka matlab khud badal kar setting badalna (setting = owner ki dohri pushti).
"""
import datetime
import hashlib
import json
import re
import time

import requests

from . import state, tg
from .config import DATA
from .log import log

DIR = DATA / "policywatch"
EVERY = 3 * 86400
MIN_NEW = 3                      # isse kam naye vaakya = shor (tareekh/banner), alert nahi

WATCH = [
    # key, naam, url, kind
    ("yt_spam", "YouTube spam/deceptive policy", "https://support.google.com/youtube/answer/2801973?hl=en", "policy"),
    ("yt_ypp", "YouTube monetization (YPP) policies", "https://support.google.com/youtube/answer/1311392?hl=en", "policy"),
    ("yt_api_pol", "YouTube API Services Developer Policies", "https://developers.google.com/youtube/terms/developer-policies", "policy"),
    ("yt_api_rev", "YouTube Data API revision history", "https://developers.google.com/youtube/v3/revision_history", "api"),
    ("meta_terms", "Meta Platform Terms", "https://developers.facebook.com/terms/", "policy"),
    ("ig_guide", "Instagram Community Guidelines", "https://help.instagram.com/477434105621119", "policy"),
    ("graph_chg", "Facebook Graph API changelog", "https://developers.facebook.com/docs/graph-api/changelog", "api"),
    ("threads_chg", "Threads API changelog", "https://developers.facebook.com/docs/threads/changelog", "api"),
    ("pin_dev", "Pinterest developer guidelines", "https://policy.pinterest.com/en/developer-guidelines", "policy"),
    ("pin_comm", "Pinterest community guidelines", "https://policy.pinterest.com/en/community-guidelines", "policy"),
    ("pin_chg", "Pinterest API changelog", "https://developers.pinterest.com/docs/new/changelog/", "api"),
    ("adsense", "AdSense program policies", "https://support.google.com/adsense/answer/48182?hl=en", "policy"),
    ("g_spam", "Google Search spam policies", "https://developers.google.com/search/docs/essentials/spam-policies", "policy"),
    ("bing_wm", "Bing Webmaster Guidelines", "https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a", "policy"),
    ("gemini_terms", "Gemini API additional terms", "https://ai.google.dev/gemini-api/terms", "policy"),
    ("gemini_chg", "Gemini API changelog", "https://ai.google.dev/gemini-api/docs/changelog", "api"),
    ("tg_bot_chg", "Telegram Bot API changelog", "https://core.telegram.org/bots/api-changelog", "api"),
    ("tg_bot_tos", "Telegram bot developer terms", "https://telegram.org/tos/bot-developers", "policy"),
]

SETUP = ("Hamara setup: Hindi/Hinglish calculator website sabhisaab.com (AdSense apply baaki, Consent Mode v2), 4 brand (Suno Natak, "
         "Sab Hisaab Money, Labh Lo Deals, Pahadi Hisaab) - YouTube Shorts + lambi video (AI awaaz, AI label), Facebook/Instagram reel, "
         "Threads, Pinterest pin, Telegram channel. Bot API se upload, comment ka vinamra jawab (7-45 min baad), quiz reel (sawal "
         "video mein, jawab website/Telegram par), IndexNow/Bing API, GA4/GSC padhna, Gemini free tier. Instagram par link/DM nahi. "
         "Abhi koi channel/website monetised nahi.")

ASK = """{setup}

Page: {name} ({kind}). Ye vaakya is page par NAYE aaye hain (pichhli jaanch ke baad):
{lines}

Batao hamare setup par asar. Sirf asli niyam/feature ka badlaav gino; menu/banner/tareekh ka shor nahi.
Return ONLY JSON: {{"impact": "none|low|high", "what": "<Hinglish, 1-2 line: kya badla>", "action": "<Hinglish: hamein kya karna,
ya '' >", "new_feature": "<naya API feature jo bot ke kaam aa sake, ya ''>"}}"""


def _text(html):
    html = re.sub(r"<(script|style|noscript|svg|nav|header|footer)\b.*?</\1>", " ", html or "", flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", "\n", html)
    t = re.sub(r"&nbsp;|&#160;", " ", t)
    return re.sub(r"[ \t]+", " ", t)


def sentences(html):
    """Kaam ke vaakya (20-400 akshar, ank-tareekh ka shor hata kar normalize)."""
    out = []
    for raw in re.split(r"[\n.!?]+", _text(html)):
        s = raw.strip()
        if not (20 <= len(s) <= 400) or len(s.split()) < 4:
            continue
        out.append(s)
    return out


def _h(s):
    norm = re.sub(r"\d+", "#", s.lower())
    norm = re.sub(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b", "M", norm)   # tareekh ka shor
    norm = re.sub(r"\s+", " ", norm).strip()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:16]


def diff(old_hashes, sents):
    """-> (naye vaakya list, nayi hash list). Bina network (test)."""
    old = set(old_hashes or [])
    new_h, added, seen = [], [], set()
    for s in sents:
        h = _h(s)
        if h in seen:
            continue
        seen.add(h)
        new_h.append(h)
        if old and h not in old:
            added.append(s)
    return added, new_h


def _load(key):
    try:
        return json.loads((DIR / f"{key}.json").read_text())
    except Exception:
        return {}


def _save(key, d):
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / f"{key}.json").write_text(json.dumps(d))


def check_one(key, name, url, kind, ask=None):
    try:
        r = requests.get(url, timeout=40, headers={"User-Agent": "Mozilla/5.0 (SabhisaabBot-PolicyWatch/1.0; +https://sabhisaab.com)",
                                                   "Accept-Language": "en"})
        body = r.text if r.ok else ""
    except Exception as e:
        return {"key": key, "ok": False, "err": str(e)[:100]}
    sents = sentences(body)
    old = _load(key)
    if len(sents) < 15:                         # JS page / block - chup, report mein dikhega
        _save(key, {**old, "t": time.time(), "unread": True})
        return {"key": key, "ok": False, "err": "page padh nahi paya (JS/block)"}
    added, hashes = diff(old.get("h"), sents)
    _save(key, {"h": hashes[:5000], "t": time.time(), "unread": False, "first": old.get("first") or str(datetime.date.today())})
    if not old.get("h"):
        return {"key": key, "ok": True, "base": True}
    if len(added) < MIN_NEW:
        return {"key": key, "ok": True, "new": len(added)}
    ask = ask or _ask_ai
    try:
        res = ask(ASK.format(setup=SETUP, name=name, kind=kind, lines="\n".join("- " + s[:300] for s in added[:25])))
    except Exception as e:
        return {"key": key, "ok": True, "new": len(added), "err": f"AI: {str(e)[:80]}"}
    return {"key": key, "ok": True, "new": len(added), "res": res if isinstance(res, dict) else {}}


def _ask_ai(prompt):
    from .brain import ask_gemini
    return ask_gemini(prompt, temperature=0.1)


def run(force=False, ask=None):
    if not force and time.time() - float(state.get("pw_at", 0) or 0) < EVERY:
        return "policywatch: abhi nahi"
    state.put("pw_at", time.time())
    alerts, base, unread = [], 0, []
    for key, name, url, kind in WATCH:
        r = check_one(key, name, url, kind, ask)
        if r.get("base"):
            base += 1
        if not r.get("ok"):
            unread.append(name)
        res = r.get("res") or {}
        imp = str(res.get("impact", "none")).lower()
        if imp in ("low", "high"):
            alerts.append((imp, name, url, res))
        if res.get("new_feature"):
            try:
                from . import tasks
                tasks.add(f"[API naya] {name}: {str(res['new_feature'])[:220]}",
                          how="Bot khud nahi jod sakta - Claude ko bolein: 'naya API feature jodo' (link: " + url + ")")
            except Exception as e:
                log(f"policywatch task: {e}")
        if imp == "high" and res.get("action"):
            try:
                from . import tasks
                tasks.add(f"[Policy] {name}: {str(res['action'])[:220]}", how="Padh kar 'ho gaya policy' likhein. Srot: " + url)
            except Exception as e:
                log(f"policywatch task: {e}")
        time.sleep(2)
    state.put("pw_last", {"t": time.time(), "alerts": [(i, n, u, r_.get("what", "")) for i, n, u, r_ in alerts],
                          "unread": unread, "base": base})
    if alerts:
        hi = [a for a in alerts if a[0] == "high"]
        tg.alert("red" if hi else "yellow", "📜 Policy / API badlaav (asli page se, Gemini ka saar):\n" + "\n".join(
            f"{'🔴' if i == 'high' else '🟡'} {n}: {r_.get('what', '')}\n   👉 {r_.get('action') or 'kuch karna nahi'}\n   {u}"
            for i, n, u, r_ in alerts)[:3800])
    return f"policywatch: {len(WATCH)} page | badlaav {len(alerts)} | pehli baar {base} | padh nahi paya {len(unread)}"


def report():
    last = state.get("pw_last") or {}
    if not last:
        return "📜 Policy/API watcher abhi chala nahi (har 3 din apne aap; abhi chalana: 'policy jaancho')."
    L = [f"📜 POLICY / API WATCHER - aakhri jaanch {datetime.datetime.fromtimestamp(last['t']):%d %b %H:%M} ({len(WATCH)} page)"]
    for i, n, u, w in last.get("alerts") or []:
        L.append(f"{'🔴' if i == 'high' else '🟡'} {n}: {w}")
    if not last.get("alerts"):
        L.append("✅ Pichhli jaanch ke baad koi asar wala badlaav nahi")
    if last.get("unread"):
        L.append("ℹ️ Padh nahi paya (JS page): " + ", ".join(last["unread"][:8]) + " - inke liye news-watch (purana) chalta hai")
    return "\n".join(L)
