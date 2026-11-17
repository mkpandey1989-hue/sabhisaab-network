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
        out.append(extra_table(days))
    except Exception as e:
        log(f"scoreboard extra: {e}")
    out.append("<i>Views = us din bani videos ke ab tak ke views. '-' = platform ne data nahi diya (andaaza nahi).\n"
               "Site = video ke link se website par aaye log (GA4). YT=YouTube, FB=Facebook, IG=Instagram, Thr=Threads.</i>")
    return "\n".join(out)


def send(days=7):
    try:
        txt = table(days)
    except Exception as e:
        return tg.say(f"📊 Scoreboard nahi bana: {str(e)[:200]}")
    parts = txt.split("\n🌐 WEBSITE", 1)
    if len(parts) == 2:
        parts[1] = "🌐 WEBSITE" + parts[1]
    r = None
    for part in parts:
        try:
            r = tg.call("sendMessage", {"chat_id": tg._chat(), "text": part[:4000], "parse_mode": "HTML",
                                        "disable_web_page_preview": "true"})
        except Exception:
            import re
            r = tg.say(re.sub(r"</?(pre|b|i)>", "", _h.unescape(part)))
    return r


def due(now=None):
    now = now or datetime.datetime.now(IST)
    return now.strftime("%H:%M") >= HHMM and state.get("sb_day") != str(now.date()) and state.get("sb_on", True)


def on_text(tl, run):
    if (tl.startswith("report table") or tl.startswith("table report") or tl.startswith("scoreboard") or tl.startswith("report tabel")
            or (("table" in tl or "tabel" in tl) and any(w in tl for w in ("report", "din ka", "din ki", "hisaab")))):
        if tl.endswith("band") or tl.endswith("chalu"):
            state.put("sb_on", tl.endswith("chalu"))
            return tg.say("📊 Roz 21:50 ki table report: " + ("CHALU" if tl.endswith("chalu") else "BAND"))
        d = parse_days(tl)
        tg.say("📊 Saare platform se ginti la raha hoon (1-2 minute)...")
        return run(lambda: send(d))
    return None


SRC_GROUPS = [("Google", ("google",)), ("Bing", ("bing",)), ("Pinterest", ("pinterest",)), ("LinkedIn", ("linkedin", "lnkd")), ("FB Group", ("fbgroup",)),
              ("Facebook", ("facebook", "fb", "m.facebook", "l.facebook")), ("Instagram", ("instagram", "ig")),
              ("YouTube", ("youtube",)), ("Telegram", ("telegram", "t.me")), ("Threads", ("threads",)),
              ("WhatsApp", ("whatsapp", "wa")), ("Quora", ("quora",)), ("Dailymotion", ("dailymotion", "dai")), ("Push", ("push",)), ("Seedha", ("(direct)",)),
              ("Anjaan", ("(not set)",))]


def group_source(src):
    """v3.4.7: GA4 source -> platform naam. 'whatsapp_status', 'facebook_group', 'lm.facebook.com', 'org.telegram.messenger',
    'quora' sab sahi khaane mein (pehle '_' wale 'Baaki' mein chale jaate the)."""
    import re as _r
    src = (src or "").lower().strip()
    toks = set(_r.split(r"[._\-/:]+", src))
    for g, keys in SRC_GROUPS:
        if any(src == k or src.startswith(k + ".") or k in toks for k in keys):
            return g
    return "Baaki"


def site_sources(days):
    """GA4: website par log - kahan se (source) -> [(naam, log)], kul."""
    from . import website as W
    tok = W._gcreds("https://www.googleapis.com/auth/analytics.readonly")
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{W.GA4_PROPERTY}:runReport"
    rng = [{"startDate": f"{max(0, days - 1)}daysAgo" if days > 1 else "today", "endDate": "today"}]
    j = requests.post(url, headers={"Authorization": f"Bearer {tok}"}, timeout=60, json={
        "dateRanges": rng, "dimensions": [{"name": "sessionSource"}], "metrics": [{"name": "activeUsers"}], "limit": 100}).json()
    agg = {}
    for r in j.get("rows") or []:
        n = int(r["metricValues"][0]["value"])
        name = group_source(r["dimensionValues"][0]["value"])
        agg[name] = agg.get(name, 0) + n
    order = [g for g, _ in SRC_GROUPS] + ["Baaki"]
    return [(g, agg[g]) for g in order if agg.get(g)]


def search_stats(days):
    """Google search (GSC) + Bing search: (dikha, click). GSC 2 din der se data deta hai."""
    from . import website as W
    import datetime as _d
    g = b = None
    try:
        gt = W._gcreds("https://www.googleapis.com/auth/webmasters.readonly")
        e = _d.date.today() - _d.timedelta(days=2)
        r = requests.post("https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Asabhisaab.com/searchAnalytics/query",
                          headers={"Authorization": f"Bearer {gt}"}, timeout=60,
                          json={"startDate": str(e - _d.timedelta(days=max(0, days - 1))), "endDate": str(e)}).json()
        row = (r.get("rows") or [{}])[0]
        g = (int(row.get("impressions", 0)), int(row.get("clicks", 0)))
    except Exception as ex:
        log(f"scoreboard gsc: {ex}")
    try:
        key = W._env().get("BING_API_KEY")
        if key:
            b = W._bing_traffic(key, days)
    except Exception as ex:
        log(f"scoreboard bing: {ex}")
    return g, b


def pin_stats(days):
    from . import pinterest as PI
    import datetime as _d
    if not PI.connected():
        return None
    end = _d.date.today()
    j = PI._req("GET", "/user_account/analytics", params={
        "start_date": str(end - _d.timedelta(days=max(1, days))), "end_date": str(end),
        "metric_types": "IMPRESSION,SAVE,OUTBOUND_CLICK", "content_type": "ALL", "app_types": "ALL"})
    m = (j.get("all") or {}).get("summary_metrics") or {}
    return int(m.get("IMPRESSION", 0)), int(m.get("SAVE", 0)), int(m.get("OUTBOUND_CLICK", 0))


def linkedin_posts(days):
    import datetime as _d
    cut = str(_d.date.today() - _d.timedelta(days=max(0, days - 1)))
    return len([x for x in (state.get("li_log") or []) if str(x.get("d", "")) >= cut and x.get("c") != "?"])


def extra_table(days):
    L = []
    try:
        src = site_sources(days)
        if src:
            w = max(len(g) for g, _ in src)
            rows = [f"{g:<{w}} {n:>6}" for g, n in src]
            rows.append("-" * (w + 7))
            raw = sum(n for _, n in src)
            try:                                 # v3.4.7: KUL = GA4 ka asli total (baaki reports jaisa), jodna nahi
                from . import website as W
                kul = (W._ga_total(*W.ga_range(days)) or (raw,))[0]
            except Exception:
                kul = raw
            rows.append(f"{'KUL':<{w}} {kul:>6}")
            note = ("\n<i>Ek aadmi do raaste se aaya to dono line mein gina jaata hai - isliye lines ka jod KUL se thoda zyada ho "
                    "sakta hai.</i>" if raw > kul else "")
            L.append("🌐 WEBSITE - log kahan se aaye (GA4):\n<pre>" + _h.escape("\n".join(rows)) + "</pre>" + note)
    except Exception as e:
        log(f"scoreboard src: {e}")
    g, b = search_stats(days)
    rows = ["Jagah       Dikha  Click"]
    rows.append(f"{'Google':<10}{_n(g[0]) if g else '-':>7}{_n(g[1]) if g else '-':>7}")
    rows.append(f"{'Bing':<10}{_n(b[0]) if b else '-':>7}{_n(b[1]) if b else '-':>7}")
    try:
        ps = pin_stats(days)
    except Exception as e:
        log(f"scoreboard pin: {e}")
        ps = None
    rows.append(f"{'Pinterest':<10}{_n(ps[0]) if ps else '-':>7}{_n(ps[2]) if ps else '-':>7}")
    rows.append(f"{'LinkedIn':<10}{'post ' + str(linkedin_posts(days)):>14}")
    try:                                          # v3.4.8: Dailymotion par gayi video ke views (juda ho tabhi)
        from . import dailymotion as _DMs
        if _DMs.ready():
            _v = _DMs.views(days)
            rows.append(f"{'Dailymotion':<10}{('views ' + _n(_v)) if _v is not None else '-':>14}")
    except Exception as e:
        log(f"scoreboard dm: {e}")
    L.append("🔎 SEARCH + PINTEREST + LINKEDIN + DAILYMOTION:\n<pre>" + _h.escape("\n".join(rows)) + "</pre>"
             + ("\n<i>Google ka data 2 din der se aata hai. Pinterest 'Click' = website par click. LinkedIn: kitni post gayi "
                "(views Make se nahi aate).</i>"))
    return "\n".join(L)


def parse_days(tl):
    """'report table 6 din' / '3 din ka' / 'aaj' / 'kal' / 'hafte' / 'mahina' / '15' -> din (1-90)."""
    import re as _r
    if "aaj" in tl:
        return 1
    m = _r.search(r"(\d{1,2})", tl)
    if m:
        return max(1, min(90, int(m.group(1))))
    if "kal" in tl:
        return 2
    if "mahin" in tl or "month" in tl:
        return 30
    return 7
