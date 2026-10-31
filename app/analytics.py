"""YouTube Analytics (asli retention + CTR) - alag 'Desktop app' login, kyunki TV login ye scope nahi deta.
Har brand ek baar: /analytics -> link -> brand account chunein -> Allow -> browser ka address bot ko bhejein.
Retention: YouTube Analytics API. CTR/impressions: YouTube Reporting API (roz ki report, 1-2 din der se)."""
import csv
import datetime
import io
import json
import time
import urllib.parse
import requests
from .config import SECRETS, BRANDS
from .log import log

CLIENT = SECRETS / "yt_analytics_client.json"
DESKTOP_ID = "462848870459-1oeps2obipkg9td4j6cjcgi60de8pkbm.apps.googleusercontent.com"   # yt-auto-desktop (ID secret nahi)
SCOPES = "https://www.googleapis.com/auth/yt-analytics.readonly https://www.googleapis.com/auth/youtube.readonly"
REDIRECT = "http://localhost"


def _client():
    j = json.loads(CLIENT.read_text())
    j = j.get("installed") or j.get("web") or j
    return j["client_id"], j["client_secret"]


def tpath(brand):
    return SECRETS / f"ya_{brand}.json"


def has(brand):
    return tpath(brand).exists()


def link(brand):
    cid, _ = _client()
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
        {"client_id": cid, "redirect_uri": REDIRECT, "response_type": "code", "scope": SCOPES,
         "access_type": "offline", "prompt": "consent select_account", "state": brand})


def exchange(url):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url.strip()).query)
    code, brand = q.get("code", [""])[0], q.get("state", [""])[0]
    if brand not in BRANDS:
        raise RuntimeError("Address mein brand nahi mila - /analytics se naya link lein")
    cid, sec = _client()
    j = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "code": code, "client_id": cid, "client_secret": sec, "redirect_uri": REDIRECT,
        "grant_type": "authorization_code"}).json()
    if "refresh_token" not in j:
        raise RuntimeError(f"Google ne login nahi diya: {j.get('error_description') or j.get('error')}")
    j["expires_at"] = time.time() + int(j.get("expires_in", 3600))
    tmp = SECRETS / "ya_new.json"
    tmp.write_text(json.dumps(j))
    tmp.chmod(0o600)
    ch = requests.get("https://www.googleapis.com/youtube/v3/channels", timeout=30,
                      params={"part": "snippet", "mine": "true"},
                      headers={"Authorization": f"Bearer {j['access_token']}"}).json()["items"][0]
    title = ch["snippet"]["title"]
    norm = lambda s: "".join(c for c in s.lower() if c.isalnum())
    target = next((k for k, v in BRANDS.items() if norm(v["name"]) in norm(title)), None)
    if not target:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Ye '{title}' channel kisi brand se match nahi hua")
    j["channel_id"], j["channel_title"] = ch["id"], title
    tpath(target).write_text(json.dumps(j))
    tpath(target).chmod(0o600)
    tmp.unlink(missing_ok=True)
    try:
        ensure_reach_job(target)
    except Exception as e:
        log(f"reach job {target}: {e}")
    return target, title


def _token(brand):
    t = json.loads(tpath(brand).read_text())
    if t.get("expires_at", 0) > time.time() + 120:
        return t["access_token"]
    cid, sec = _client()
    j = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": cid, "client_secret": sec, "refresh_token": t["refresh_token"], "grant_type": "refresh_token"}).json()
    if "access_token" not in j:
        raise RuntimeError(f"Analytics login dobara chahiye ({j.get('error')})")
    t["access_token"], t["expires_at"] = j["access_token"], time.time() + int(j.get("expires_in", 3600))
    tpath(brand).write_text(json.dumps(t))
    return t["access_token"]


def _get(brand, url, **params):
    r = requests.get(url, params=params, timeout=60, headers={"Authorization": f"Bearer {_token(brand)}"})
    if r.status_code >= 400:
        raise RuntimeError(f"Analytics {r.status_code}: {r.text[:200]}")
    return r.json() if "json" in r.headers.get("content-type", "") else r.text


def video_metrics(brand, days=28):
    """Har video: views, avg view %, avg duration (sec), likes, shares, subs gained."""
    end = datetime.date.today()
    j = _get(brand, "https://youtubeanalytics.googleapis.com/v2/reports", ids="channel==MINE",
             startDate=str(end - datetime.timedelta(days=days)), endDate=str(end), dimensions="video",
             metrics="views,averageViewPercentage,averageViewDuration,likes,shares,subscribersGained",
             sort="-views", maxResults=200)
    cols = [c["name"] for c in j.get("columnHeaders", [])]
    return {r[0]: dict(zip(cols[1:], r[1:])) for r in j.get("rows", [])}


# ---- CTR (impressions + click-through) : Reporting API 'channel_reach_basic_a1' ----
RAPI = "https://youtubereporting.googleapis.com/v1"


def ensure_reach_job(brand):
    t = json.loads(tpath(brand).read_text())
    if t.get("reach_job"):
        return t["reach_job"]
    h = {"Authorization": f"Bearer {_token(brand)}"}
    jobs = requests.get(f"{RAPI}/jobs", headers=h, timeout=30).json().get("jobs", [])
    job = next((x for x in jobs if x.get("reportTypeId") == "channel_reach_basic_a1"), None)
    if not job:
        job = requests.post(f"{RAPI}/jobs", headers=h, timeout=30,
                            json={"reportTypeId": "channel_reach_basic_a1", "name": "sabhisaab reach"}).json()
    t["reach_job"] = job.get("id")
    tpath(brand).write_text(json.dumps(t))
    return t["reach_job"]


def video_ctr(brand):
    """Pichhli reports se har video ka impressions aur CTR (%)."""
    jid = ensure_reach_job(brand)
    h = {"Authorization": f"Bearer {_token(brand)}"}
    reps = requests.get(f"{RAPI}/jobs/{jid}/reports", headers=h, timeout=30).json().get("reports", [])
    agg = {}
    for rep in sorted(reps, key=lambda x: x.get("startTime", ""))[-14:]:
        txt = requests.get(rep["downloadUrl"], headers=h, timeout=60).text
        for row in csv.DictReader(io.StringIO(txt)):
            v = row.get("video_id")
            imp = int(float(row.get("video_thumbnail_impressions", 0) or 0))
            ctr = float(row.get("video_thumbnail_impressions_ctr", 0) or 0)
            a = agg.setdefault(v, {"impressions": 0, "clicks": 0.0})
            a["impressions"] += imp
            a["clicks"] += imp * ctr
    return {v: {"impressions": a["impressions"], "ctr": round(100 * a["clicks"] / a["impressions"], 2) if a["impressions"] else 0}
            for v, a in agg.items()}


def report(brand_filter=None):
    lines = ["📊 YouTube Analytics (asli, pichhle 28 din):"]
    for b, info in BRANDS.items():
        if brand_filter and b != brand_filter:
            continue
        if not has(b):
            lines.append(f"🔑 {info['name']}: analytics login baaki (/analytics)")
            continue
        try:
            m = video_metrics(b)
            try:
                c = video_ctr(b)
            except Exception as e:
                c = {}
                log(f"ctr {b}: {e}")
            if not m:
                lines.append(f"• {info['name']}: abhi data nahi (YouTube 1-2 din der se deta hai)")
                continue
            avg_ret = sum(float(x.get("averageViewPercentage", 0)) for x in m.values()) / len(m)
            lines.append(f"• {info['name']}: {len(m)} video, avg dekhi gayi {avg_ret:.0f}%")
            for vid, x in list(m.items())[:3]:
                cc = c.get(vid, {})
                lines.append(f"   ▶️ {vid}: {x.get('views')} views, {float(x.get('averageViewPercentage', 0)):.0f}% dekhi, "
                             f"{x.get('likes')} likes" + (f", CTR {cc['ctr']}% ({cc['impressions']} impr.)" if cc else ""))
        except Exception as e:
            lines.append(f"⚠️ {info['name']}: {str(e)[:80]}")
    return "\n".join(lines)


def feed_learning():
    """Roz: retention + CTR seekh mein (thumbnail rang/layout aur topic chunav ke liye)."""
    from . import learn
    d = learn.load()
    for b in BRANDS:
        if not has(b):
            continue
        try:
            m = video_metrics(b)
        except Exception as e:
            log(f"feed {b}: {e}")
            continue
        try:
            c = video_ctr(b)
        except Exception:
            c = {}
        for vid, x in m.items():
            v = d["videos"].get(vid)
            if v:
                v["retention"] = float(x.get("averageViewPercentage", 0))
                if vid in c:
                    v["ctr"], v["impressions"] = c[vid]["ctr"], c[vid]["impressions"]
    learn.save(d)
