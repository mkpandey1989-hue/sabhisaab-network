"""v3.4.7 (17 Nov 2026) - owner: "jo indexing karna ho wo link de dena; bot website live ke baad sitemap dabayega, uske baad hi
indexing karega aur link mere ko dega GSC wali".

GOOGLE 'REQUEST INDEXING' KI ROZ KI SUCHI - ek hi jagah, ek hi niyam:
1) Pehle Google ko LIVE sitemap bhejta hai (website.submit_sitemap - wahi jo Search Console mein 'Submit' hai).
2) Sirf wahi URL jo (a) LIVE sitemap.xml mein hain, (b) abhi HTTP 200 khulte hain, (c) roz ki Google jaanch (daily.json,
   URL Inspection API) ke hisaab se index NAHI hain.
2b) v3.4.8: link dene se theek pehle har URL Google URL Inspection API se TAAZA jaancha - index ho chuka = link nahi.
3) Har URL ka SEEDHA Search Console link (URL Inspection khulta hai) - dabao → 'REQUEST INDEXING'. Google ka apna link format
   (URL Inspection API ka 'inspectionResultLink' yahi hota hai).
4) Din mein max 10 (Google roz itne hi leta hai). Ek URL 7 din mein ek baar - roz wahi suchi dobara nahi.
5) Kram: index se NIKLE page > aaj/haal ke naye page > 'URL is unknown' > 'Discovered' > 'Crawled - not indexed'.
Bot khud Google ko 'Request indexing' NAHI bhej sakta (Google ka Indexing API sirf job/live-video page ke liye - niyam).

Hukum: 'indexing link' / 'gsc link' / 'index link' (abhi) | 'indexing ho gaya' (aaj ki suchi dabayi).
"""
import datetime
import json
import urllib.parse

from . import state, tg
from .config import IST, SITE
from .log import log

HHMM = "11:40"           # roz 11:30 ki Google index jaanch (pagequeue.gidx_run) ke baad
MAX_DAY = 10
REPEAT_DAYS = 7
PROP = "sc-domain:sabhisaab.com"

_RANK = {"URL is unknown to Google": 1, "Discovered - currently not indexed": 2, "Crawled - currently not indexed": 3}


def gsc_link(url):
    """Search Console URL Inspection ka seedha link (property + URL)."""
    return ("https://search.google.com/search-console/inspect?resource_id=" + urllib.parse.quote(PROP, safe="")
            + "&id=" + urllib.parse.quote(url, safe=""))


def _status():
    """daily.json -> ({url: {...}}, din)"""
    from .website import DIR, KEEP
    for p in (DIR / "state" / "daily.json", KEEP / "daily.json"):
        try:
            d = json.loads(p.read_text())
            if d.get("status"):
                return d["status"], d.get("day")
        except Exception:
            pass
    return {}, None


def _live_ok(u):
    import requests
    try:
        r = requests.get(u, timeout=20, headers={"User-Agent": "SabHisaab-bot-livecheck"})
        return r.status_code == 200 and "noindex" not in r.text[:6000].lower()
    except Exception:
        return False


def google_says_indexed(u):
    """v3.4.8 (owner: 'jo index ho gaye unka bhi link de raha hai'): daily.json kal ka ho sakta hai - link dene se THEEK PEHLE
    Google URL Inspection API se taaza jaanch (roz 2000 ki seema, hum max ~15). -> True (index hai) / False / None (pata nahi)."""
    import requests
    from . import website
    cache = state.get("idx_fresh") or {}
    today = str(datetime.date.today())
    if (cache.get(u) or [None])[0] == today:
        return cache[u][1]
    try:
        tk = website._gcreds("https://www.googleapis.com/auth/webmasters.readonly")
        j = requests.post("https://searchconsole.googleapis.com/v1/urlInspection/index:inspect", timeout=60,
                          headers={"Authorization": f"Bearer {tk}"},
                          json={"inspectionUrl": u, "siteUrl": PROP, "languageCode": "en"}).json()
        r = (j.get("inspectionResult") or {}).get("indexStatusResult") or {}
        if not r:
            return None
        ok = r.get("verdict") == "PASS"
    except Exception as e:
        log(f"idx inspect: {e}")
        return None
    cache = {k: v for k, v in cache.items() if (v or [""])[0] == today}
    cache[u] = [today, ok]
    state.put("idx_fresh", cache)
    return ok


def pick(extra_new=(), k=MAX_DAY, today=None, live_sm=None, status=None, live_ok=None, indexed=None):
    """-> [(url, wajah)] - sitemap-first + live + index-nahi + 7-din-ek-baar. (test ke liye sab inject ho sakta hai)"""
    today = today or datetime.date.today()
    st = status if status is not None else _status()[0]
    if live_sm is None:
        from . import website
        live_sm = website.live_sitemap_urls()
    if not live_sm:                     # sitemap hi nahi mila to KOI link nahi (niyam: pehle sitemap)
        return []
    live_ok = live_ok or _live_ok
    indexed = indexed or google_says_indexed
    new_set = set(extra_new)
    given = state.get("idx_given") or {}
    cut = str(today - datetime.timedelta(days=REPEAT_DAYS))
    drop = set(state.get("pq_idx_drop") or {})
    cand = []
    for u in extra_new:                 # aaj ke naye page (Google ne abhi jaancha bhi nahi)
        cand.append((0, u, "naya page"))
    for u, v in (st or {}).items():
        if v.get("ok"):
            continue
        why = v.get("why") or "index nahi"
        cand.append((0 if u in drop else _RANK.get(why, 4), u, ("index se nikla - " if u in drop else "") + why))
    seen, out = set(), []
    for _, u, why in sorted(cand, key=lambda x: x[0]):
        if u in seen or u not in live_sm or str(given.get(u, "")) > cut:
            continue
        seen.add(u)
        if not live_ok(u):
            continue
        if u not in new_set and indexed(u) is True:     # Google kehta hai index ho chuka -> link nahi (purani daily.json)
            continue
        out.append((u, why))
        if len(out) >= k:
            break
    return out


def message(rows, day=None, stale=False, sm_line=""):
    if not rows:
        return None
    L = [f"🔎 GOOGLE INDEXING - aaj ke {len(rows)} link (sitemap mein pakka ✅ | page live ✅ | Google index mein abhi nahi)"]
    if sm_line:
        L.append(f"🗺 {sm_line}")
    if stale:
        L.append(f"⚠️ Google ki index jaanch aakhri {day} ki hai - kuch page shayad ab tak index ho chuke hon (dabane se nuksaan nahi).")
    L.append("")
    for i, (u, why) in enumerate(rows, 1):
        L.append(f"{i}. {u.replace(SITE, '') or '/'} ({why})\n   👉 {gsc_link(u)}")
    L += ["", "Kaise (har link 1 minute):",
          "1) Link dabao → Search Console khulega (pehli baar Google account chunna pad sakta hai)",
          "2) 'URL is not on Google' / jaanch poori hone do (10-30 sec)",
          "3) 'REQUEST INDEXING' dabao → 1-2 min → 'Indexing requested' ✅",
          "Google din mein ~10 hi leta hai - 'Quota exceeded' aaye to baaki kal. Ek page ko dobara-dobara mat dabaiye.",
          "Ho jaye to likhein: 'indexing ho gaya' (ye link 7 din tak dobara nahi aayenge; bot roz Google se jaanchta rahega).",
          "Bing + IndexNow: bot khud bhejta hai, aapko kuch nahi karna."]
    return "\n".join(L)


def run(manual=False, extra_new=()):
    """Sitemap Google ko bhejo -> suchi chuno -> sandesh. -> text ya None."""
    from . import website
    today = datetime.date.today()
    if not manual:
        state.put("idx_day", str(today))
    sm_line = ""
    try:
        sm_line = website.submit_sitemap() or ""
    except Exception as e:
        log(f"idxlink sitemap: {e}")
    if sm_line and "✅" not in sm_line:
        return (f"🔎 Indexing link abhi nahi diye: Google ko sitemap nahi gaya ({sm_line}). Niyam: pehle sitemap, phir link. "
                "Bot agle ghante phir koshish karega." if not manual else f"🔎 Pehle sitemap jaana zaroori hai: {sm_line}")
    st, day = _status()
    rows = pick(extra_new, status=st)
    if not rows:
        if not manual:
            return None
        return ("✅ Aaj koi indexing link nahi: sitemap ke sab live page ya to Google index mein hain, ya pichhle 7 din mein aapko "
                "diye ja chuke hain (Google ko samay dein).")
    given = state.get("idx_given") or {}
    for u, _ in rows:
        given[u] = str(today)
    cut = str(today - datetime.timedelta(days=40))
    state.put("idx_given", {u: d for u, d in given.items() if d >= cut})
    state.put("idx_last", {"day": str(today), "urls": [u for u, _ in rows]})
    return message(rows, day, stale=bool(day and day < str(today - datetime.timedelta(days=1))), sm_line=sm_line)


def due(now=None):
    now = now or datetime.datetime.now(IST)
    return (now.strftime("%H:%M") >= HHMM and state.get("idx_day") != str(now.date()) and state.get("idx_on", True)
            and not state.get("paused"))


def note_given(urls):
    """pagequeue ke 'aaj naye page' sandesh mein jo link gaye - unhe 7 din dobara na do."""
    given = state.get("idx_given") or {}
    for u in urls:
        given[u] = str(datetime.date.today())
    state.put("idx_given", given)


def on_text(tl, run_bg):
    if tl in ("indexing link", "index link", "gsc link", "gsc links", "indexing links", "request indexing", "indexing kya karu",
              "indexing link do", "gsc link do"):
        tg.say("🔎 Pehle Google ko live sitemap bhej raha hoon, phir link chunta hoon (1-2 min)...")
        return run_bg(lambda: tg.say(run(manual=True) or "✅ Aaj koi indexing link nahi."))
    if tl in ("indexing ho gaya", "index ho gaya", "gsc ho gaya", "request indexing ho gaya"):
        last = state.get("idx_last") or {}
        state.put("idx_done", {"day": str(datetime.date.today()), "n": len(last.get("urls") or [])})
        return tg.say(f"👍 Note kiya ({len(last.get('urls') or [])} link). Ye 7 din dobara nahi aayenge. Google 2-14 din leta hai - "
                      "bot roz jaanch kar index hote hi suchi se hata dega.")
    if tl in ("indexing link band", "indexing link chalu"):
        state.put("idx_on", tl.endswith("chalu"))
        return tg.say("🔎 Roz 11:40 ki indexing suchi: " + ("CHALU" if tl.endswith("chalu") else "BAND"))
    return None
