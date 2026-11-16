"""v3.4.4 (16 Nov 2026 raat) - owner: "ek table ki tarah bot report de - pure brand pure platform, jab maangu tab, total ke
saath; advance lekin simple".

Ek table (Telegram <pre> - seedhi lines): har BRAND x har PLATFORM ke VIEWS (pichhle N din mein bani videos), aur aakhri
column 'Site' = us brand ke video-link se website par aaye LOG (GA4, utm_campaign=brand). Neeche KUL. Phir ek chhoti table
like/comment. Pinterest (poore account ka) + website ka kul alag line mein.
Data sirf asli API se (YouTube / Meta / Threads / Pinterest / GA4). Jo platform jawab na de -> '-' (andaaza kabhi nahi).
Hukum: 'report table' (7 din) | 'report table aaj' | 'report table 30'. Roz 21:50 apne aap (band: 'report table band').
"""
import datetime
import html as _h

import requests

from . import state, tg
from .config import BRANDS, IST
from .log import log

COLS = ["YT", "FB", "IG", "Thr"]
SHORT = {"sunonatak": "Suno", "money": "Money", "deals": "Labh", "pahadi": "Pahadi"}
HHMM = "21:50"


def _jobs(days):
    from . import pipeline
    since = (datetime.datetime.now(IST).date() - datetime.timedelta(days=max(0, days - 1)))
    out = []
    for jid, j in (pipeline.jobs() or {}).items():
        ids = j.get("ids") or {}
        if not ids or j.get("brand") not in BRANDS:
            continue
        try:
            d = datetime.date.fromisoformat(str(j.get("slot") or j.get("created") or "")[:10])
        except Exception:
            continue
        if d >= since:
            out.append((j["brand"], ids))
    return out


def _threads_stats(brand, mid):
    from . import threads as TH
    tok = (TH.info(brand) or {}).get("token")
    if not tok or not mid:
        return {}
    j = requests.get(f"https://graph.threads.net/v1.0/{mid}/insights",
                     params={"metric": "views,likes,replies", "access_token": tok}, timeout=30).json()
    out = {}
    for m in j.get("data") or []:
        v = (m.get("values") or [{}])[0].get("value") if m.get("values") else (m.get("total_value") or {}).get("value")
        out[{"replies": "comments"}.get(m.get("name"), m.get("name"))] = int(v or 0)
    return out


def collect(days=7):
    """-> {brand: {plat: {"views","likes","comments"} | None}}. None = API se nahi mila."""
    from . import youtube, meta as M
    rows = {b: {c: None for c in COLS} for b in BRANDS}

    def add(b, c, st):
        if not st:
            return
        cur = rows[b][c] or {"views": 0, "likes": 0, "comments": 0, "n": 0}
        for k in ("views", "likes", "comments"):
            cur[k] += int(st.get(k) or 0)
        cur["n"] += 1
        rows[b][c] = cur
    jb = _jobs(days)
    for b in BRANDS:
        yt = [ids.get("youtube") for bb, ids in jb if bb == b and ids.get("youtube")]
        if yt:
            try:
                for _, s in youtube.stats(b, yt).items():
                    add(b, "YT", s)
            except Exception as e:
                log(f"scoreboard yt {b}: {e}")
    for b, ids in jb:
        for c, key, fn in (("FB", "facebook", M.fb_video_stats), ("IG", "instagram", M.ig_media_stats),
                           ("Thr", "threads", _threads_stats)):
            if ids.get(key):
                try:
                    add(b, c, fn(b, ids[key]))
                except Exception as e:
                    log(f"scoreboard {c} {b}: {e}")
    return rows, len(jb)


def site_by_brand(days=7):
    """GA4: utm_campaign = brand -> log. -> ({brand: users}, kul_site_users) ya (None, None)."""
    from . import website as W
    if not W.SA.exists():
        return None, None
    try:
        tok = W._gcreds("https://www.googleapis.com/auth/analytics.readonly")
        url = f"https://analyticsdata.googleapis.com/v1beta/properties/{W.GA4_PROPERTY}:runReport"
        rng = [{"startDate": f"{max(0, days - 1)}daysAgo" if days > 1 else "today", "endDate": "today"}]
        j = requests.post(url, headers={"Authorization": f"Bearer {tok}"}, timeout=60, json={
            "dateRanges": rng, "dimensions": [{"name": "sessionCampaignName"}], "metrics": [{"name": "activeUsers"}],
            "limit": 50}).json()
        t = requests.post(url, headers={"Authorization": f"Bearer {tok}"}, timeout=60, json={
            "dateRanges": rng, "metrics": [{"name": "activeUsers"}]}).json()
    except Exception as e:
        log(f"scoreboard ga4: {e}")
        return None, None
    by = {b: 0 for b in BRANDS}
    for r in j.get("rows") or []:
        camp = r["dimensionValues"][0]["value"].lower()
        for b in BRANDS:
            if b in camp or (b == "deals" and "labh" in camp):
                by[b] += int(r["metricValues"][0]["value"])
    tot = int(((t.get("rows") or [{}])[0].get("metricValues") or [{"value": 0}])[0]["value"]) if t.get("rows") else 0
    return by, tot


def _n(x):
    if x is None:
        return "-"
    x = int(x)
    return f"{x / 1000:.1f}k" if x >= 10000 else str(x)


def table(days=7):
    rows, nvid = collect(days)
    site, site_tot = site_by_brand(days)
    head = "Brand  " + "".join(f"{c:>6}" for c in COLS + ["Site"])
    L = [head, "-" * len(head)]
    tot = {c: None for c in COLS}
    for b in BRANDS:
        cells = []
        for c in COLS:
            v = rows[b][c]["views"] if rows[b][c] else None
            cells.append(_n(v))
            if v is not None:
                tot[c] = (tot[c] or 0) + v
        cells.append(_n(site.get(b)) if site else "-")
        L.append(f"{SHORT.get(b, b)[:6]:<7}" + "".join(f"{x:>6}" for x in cells))
    L.append("-" * len(head))
    L.append("KUL    " + "".join(f"{_n(tot[c]):>6}" for c in COLS) + f"{_n(sum(site.values()) if site else None):>6}")
    lk = sum((rows[b][c] or {}).get("likes", 0) for b in BRANDS for c in COLS)
    cm = sum((rows[b][c] or {}).get("comments", 0) for b in BRANDS for c in COLS)
    allv = sum(v for v in tot.values() if v)
    title = "AAJ" if days == 1 else f"PICHHLE {days} DIN"
    out = [f"📊 SCOREBOARD - {title} ({nvid} video)", "<pre>" + _h.escape("\n".join(L)) + "</pre>",
           f"👁 Sab platform ke kul views: <b>{allv}</b> | 👍 {lk} like | 💬 {cm} comment"]
    if site_tot is not None:
        out.append(f"🌐 Website par kul log (har jagah se): <b>{site_tot}</b> | inme video-link se: {sum(site.values())}")
    try:
        from . import pinterest as PI
        if PI.connected():
            out.append(_h.escape(PI.analytics_summary(min(30, max(1, days))).split("\n")[0][:200]))
    except Exception:
        pass
    out.append("<i>Views = us din bani videos ke ab tak ke views. '-' = platform ne data nahi diya (andaaza nahi).\n"
               "Site = video ke link se website par aaye log (GA4). YT=YouTube, FB=Facebook, IG=Instagram, Thr=Threads.</i>")
    return "\n".join(out)


def send(days=7):
    try:
        txt = table(days)
    except Exception as e:
        return tg.say(f"📊 Scoreboard nahi bana: {str(e)[:200]}")
    try:
        return tg.call("sendMessage", {"chat_id": tg._chat(), "text": txt[:4000], "parse_mode": "HTML",
                                       "disable_web_page_preview": "true"})
    except Exception:
        import re
        return tg.say(re.sub(r"</?(pre|b|i)>", "", _h.unescape(txt)))


def due(now=None):
    now = now or datetime.datetime.now(IST)
    return now.strftime("%H:%M") >= HHMM and state.get("sb_day") != str(now.date()) and state.get("sb_on", True)


def on_text(tl, run):
    if tl.startswith("report table") or tl in ("scoreboard", "table report", "report tabel"):
        if tl.endswith("band") or tl.endswith("chalu"):
            state.put("sb_on", tl.endswith("chalu"))
            return tg.say("📊 Roz 21:50 ki table report: " + ("CHALU" if tl.endswith("chalu") else "BAND"))
        d = 1 if "aaj" in tl else (30 if "30" in tl or "mahin" in tl else 7)
        tg.say("📊 Saare platform se ginti la raha hoon (1-2 minute)...")
        return run(lambda: send(d))
    return None
