"""v3.4.7 (17 Nov 2026) - owner: "jo indexing karna ho wo link de dena; bot website live ke baad sitemap dabayega, uske baad hi
indexing karega aur link mere ko dega GSC wali".

GOOGLE 'REQUEST INDEXING' KI ROZ KI SUCHI - ek hi jagah, ek hi niyam:
1) Pehle Google ko LIVE sitemap bhejta hai (website.submit_sitemap - wahi jo Search Console mein 'Submit' hai).
2) Sirf wahi URL jo (a) LIVE sitemap.xml mein hain, (b) abhi HTTP 200 khulte hain, (c) roz ki Google jaanch (daily.json,
   URL Inspection API) ke hisaab se index NAHI hain.
2b) v3.4.8: link dene se theek pehle har URL Google URL Inspection API se TAAZA jaancha - index ho chuka = link nahi.
3b) v3.4.13: queue ke naye page bhi isi suchi mein (pagequeue alag link nahi deta); 7-din niyam sirf "indexing ho gaya" ke baad;
   kuch na ho to bhi 11:40 par chhota "aaj kaam nahi" sandesh (chup nahi).
3) v3.4.8b: sirf page ka POORA URL (tap = copy) - Search Console ka deep-link owner ke phone par error deta tha.
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
        if indexed(u) is True:          # Google kehta hai index ho chuka -> link nahi (v3.4.13: naye page par bhi)
            continue
        out.append((u, why))
        if len(out) >= k:
            break
    return out


WHY_HI = {"URL is unknown to Google": "Google ko pata hi nahi", "Discovered - currently not indexed": "Google ne dekha, index nahi kiya",
          "Crawled - currently not indexed": "Google aaya, index nahi kiya", "naya page": "naya page"}


def message(rows, day=None, stale=False, sm_line=""):
    """v3.4.8b (owner: 'console ka link error deta hai - sirf POORA link do jo karna hai, priority se'): sirf page ka poora URL,
    upar se zaroori pehle. HTML <code> = Telegram mein ek tap se copy. -> HTML text"""
    import html as _h
    if not rows:
        return None
    L = [f"🔎 <b>GOOGLE INDEXING - aaj ke {len(rows)} page</b> (upar wala sabse zaroori)",
         "Har page: sitemap mein ✅ | live ✅ | Google ne abhi index nahi kiya (aaj Google se taaza jaancha)", ""]
    if stale:
        L.insert(1, f"⚠️ Google ki roz ki jaanch aakhri {day} ki hai.")
    for i, (u, why) in enumerate(rows, 1):
        w = WHY_HI.get(why.replace("index se nikla - ", ""), why)
        L.append(f"{i}. <code>{_h.escape(u)}</code>\n    <i>{_h.escape(('index se nikla - ' if why.startswith('index se nikla') else '') + w)}</i>")
    L += ["", "<b>Kaise (har page 1 minute):</b>",
          "1) Upar ka link <b>dabao</b> → copy ho jayega",
          "2) Search Console kholo: https://search.google.com/search-console → upar <b>'Inspect any URL'</b> dabbe mein paste → Enter",
          "3) <b>REQUEST INDEXING</b> dabao → 'Indexing requested' ✅",
          "'Quota exceeded' aaye to baaki kal. Ho jaye to likhein: <b>indexing ho gaya</b> (ye page 7 din dobara nahi aayenge).",
          "Bing + IndexNow bot khud karta hai."]
    return "\n".join(L)


def send_html(text):
    try:
        from . import updater
        updater.log_bot(text)
    except Exception:
        pass
    try:
        r = tg.call("sendMessage", {"chat_id": tg._chat(), "text": text[:4000], "parse_mode": "HTML", "disable_web_page_preview": "true"})
        if r and (not isinstance(r, dict) or r.get("ok", True)):
            return r
    except Exception as e:
        log(f"idx html: {e}")
    import re as _r, html as _h
    return tg.say(_h.unescape(_r.sub(r"</?(b|i|code)>", "", text)))


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
    cut3 = str(today - datetime.timedelta(days=3))       # v3.4.13: queue ke naye page (subah live) bhi ISI ek suchi mein
    pqn = [u for u, d in sorted((state.get("pq_new_pages") or {}).items(), key=lambda x: x[1], reverse=True) if d >= cut3]
    rows = pick(list(extra_new) + [u for u in pqn if u not in extra_new], status=st)
    if not rows:
        gv = state.get("idx_given") or {}
        wk = len([u for u, d in gv.items() if d > str(today - datetime.timedelta(days=REPEAT_DAYS))])
        return ("✅ GOOGLE INDEXING: aaj aapka koi kaam nahi - sitemap ke sab live page Google index mein hain"
                + (f" ya {wk} page par aap pichhle 7 din mein Request indexing kar chuke (Google 2-14 din leta hai)." if wk else "."))
    # v3.4.13: 7-din wala niyam sirf tab jab owner 'indexing ho gaya' likhe - bina kiye suchi gayab nahi hoti
    state.put("idx_last", {"day": str(today), "urls": [u for u, _ in rows]})
    send_html(message(rows, day, stale=bool(day and day < str(today - datetime.timedelta(days=1))), sm_line=sm_line))
    return None


def migrate_3413():
    """v3.4.13 ek baar: aaj subah ke adhoore sandesh (console link / /path) ke URL 'diye' maan liye gaye the - owner ne kiye nahi.
    Unhe wapas suchi mein lao; queue ke pichhle 3 din ke naye page jodo; aaj ki suchi update ke baad turant dobara aaye."""
    if state.get("mig_idx3413"):
        return
    state.put("mig_idx3413", True)
    done = state.get("idx_done") or {}
    cut = str(datetime.date.today() - datetime.timedelta(days=7))
    if not (done.get("day") and done["day"] >= cut):
        state.put("idx_given", {})
    pub = state.get("pq_pub") or {}
    c3 = str(datetime.date.today() - datetime.timedelta(days=3))
    note_new_pages([f"{SITE}/{k}" for k, d in pub.items() if str(d) >= c3])
    state.put("idx_day", "")


def due(now=None):
    now = now or datetime.datetime.now(IST)
    try:
        migrate_3413()
    except Exception as e:
        log(f"idx mig: {e}")
    return (now.strftime("%H:%M") >= HHMM and state.get("idx_day") != str(now.date()) and state.get("idx_on", True)
            and not state.get("paused"))


def note_given(urls):
    """owner ne 'indexing ho gaya' likha - in URL ko 7 din dobara na do (v3.4.13: sirf pakka hone par)."""
    given = state.get("idx_given") or {}
    for u in urls:
        given[u] = str(datetime.date.today())
    cut = str(datetime.date.today() - datetime.timedelta(days=40))
    state.put("idx_given", {u: d for u, d in given.items() if d >= cut})


def note_new_pages(urls):
    """pagequeue: aaj live hue naye page - 11:40 ki ek hi indexing suchi mein sabse upar aayenge."""
    d = state.get("pq_new_pages") or {}
    for u in urls:
        d.setdefault(u, str(datetime.date.today()))
    cut = str(datetime.date.today() - datetime.timedelta(days=10))
    state.put("pq_new_pages", {u: x for u, x in d.items() if x >= cut})


def on_text(tl, run_bg):
    if tl in ("indexing link", "index link", "gsc link", "gsc links", "indexing links", "request indexing", "indexing kya karu",
              "indexing link do", "gsc link do", "indexing", "aaj ke indexing link", "indexing link nahi aaye"):
        tg.say("🔎 Pehle Google ko live sitemap bhej raha hoon, phir har page Google se taaza jaanch kar suchi deta hoon (1-3 min)...")
        return run_bg(lambda: (lambda r: r and tg.say(r))(run(manual=True)))
    if tl in ("indexing ho gaya", "index ho gaya", "gsc ho gaya", "request indexing ho gaya", "ho gaya indexing"):
        last = state.get("idx_last") or {}
        note_given(last.get("urls") or [])
        state.put("idx_done", {"day": str(datetime.date.today()), "n": len(last.get("urls") or [])})
        return tg.say(f"👍 Note kiya ({len(last.get('urls') or [])} link). Ye 7 din dobara nahi aayenge. Google 2-14 din leta hai - "
                      "bot roz jaanch kar index hote hi suchi se hata dega.")
    if tl in ("indexing link band", "indexing link chalu"):
        state.put("idx_on", tl.endswith("chalu"))
        return tg.say("🔎 Roz 11:40 ki indexing suchi: " + ("CHALU" if tl.endswith("chalu") else "BAND"))
    return None
