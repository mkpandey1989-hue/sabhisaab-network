"""v2.0.3: SEO DIARY - doosre log (usi vishay ke channel) ki video kyun chal rahi hai, hamari kyun nahi, log kya pasand
kar rahe hain, humein kya karna chahiye. Hafte mein ek baar apne aap (Shanivaar 21:00) + owner maange to ('seo diary abhi').

Sirf PADHNA (YouTube Data API search/videos - public jaankari). Koi scraping, copy, ya doosre ka content nahi uthate.
Seekh 3 jagah jaati hai: diary file (data/seo_diary.jsonl), state.insights (writer har nayi script mein maanta hai),
aur owner ko saaf Hinglish report.
Quota: har brand 1 search (100 unit) + 1 videos.list (1 unit) = ~404 unit/hafta (10,000/din ki seema mein aaram se)."""
import datetime
import json
import re
from . import state, tg
from .config import BRANDS, DATA
from .log import log

FILE = DATA / "seo_diary.jsonl"
QUERY = {"sunonatak": "paise ki kahani hindi shorts", "money": "sip fd ppf hindi shorts",
         "deals": "bachat tips hindi shorts", "pahadi": "uttarakhand pahadi shorts"}


def _iso_secs(d):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0


def _others(brand):
    """Pichhle 30 din ki sabse zyada dekhi gayi milti-julti Hindi Shorts (doosre channel)."""
    from . import youtube
    if not youtube.has_login(brand):
        return []
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = QUERY.get(brand) or BRANDS[brand]["name"]
    try:
        from . import seo
        tr = seo.trends(brand)[:1]
        if tr:
            q = tr[0]
    except Exception:
        pass
    s = youtube._api(brand, "GET", "/youtube/v3/search", params={
        "part": "snippet", "q": q, "type": "video", "videoDuration": "short", "order": "viewCount",
        "publishedAfter": since, "relevanceLanguage": "hi", "regionCode": "IN", "maxResults": 12})
    my_ch = None
    try:
        my_ch = youtube._api(brand, "GET", "/youtube/v3/channels", params={"part": "id", "mine": "true"})["items"][0]["id"]
    except Exception:
        pass
    ids = [i["id"]["videoId"] for i in s.get("items", []) if i.get("snippet", {}).get("channelId") != my_ch][:10]
    if not ids:
        return []
    v = youtube._api(brand, "GET", "/youtube/v3/videos", params={"part": "snippet,statistics,contentDetails",
                                                                 "id": ",".join(ids)})
    out = []
    for it in v.get("items", []):
        sn, st = it.get("snippet", {}), it.get("statistics", {})
        days = max(1, (datetime.datetime.utcnow() - datetime.datetime.strptime(sn.get("publishedAt", since)[:19],
                                                                                 "%Y-%m-%dT%H:%M:%S")).days)
        views = int(st.get("viewCount", 0))
        out.append({"title": sn.get("title", "")[:100], "views": views, "per_day": views // days,
                    "likes": int(st.get("likeCount", 0)), "comments": int(st.get("commentCount", 0)),
                    "secs": _iso_secs(it.get("contentDetails", {}).get("duration")),
                    "tags": (sn.get("tags") or [])[:6], "query": q})
    return sorted(out, key=lambda x: -x["per_day"])


def _ours(brand):
    """Hamari pichhli videos (learn.py ke views) - tulna ke liye."""
    try:
        from . import learn
        rows = [r for r in learn.video_table(40) if r.get("brand") == brand]
        return [{"title": r.get("title", "")[:80], "views": r.get("views", 0)} for r in rows[:10]]
    except Exception:
        return []


PROMPT = """You are the SEO + growth analyst of a small Hindi YouTube/Instagram brand "{name}" ({brand}).
Compare TOP videos by OTHER channels on the same subject (last 30 days, real public numbers) with OUR recent videos.
Others: {others}
Ours: {ours}
Return ONLY JSON: {{"why_they_win": [3-5 short Hinglish points: hook, title words, length, emotion, format, posting],
"why_we_lag": [2-4 short points], "do_more": [3-4 concrete actions for our next videos],
"avoid": [2-3 things], "title_tips": [3 title patterns in Hinglish with placeholders],
"topic_ideas": [5 fresh topic ideas (Hindi/Hinglish, no real person names, no politics/religion, no guaranteed returns)],
"website_ideas": [2 ideas for calculator/guide pages or improvements that match what people want]}}
Never suggest copying anyone's video, buying views/followers, clickbait that lies, 'comment LINK' bait, or DMs.
Keep everything inside YouTube/Meta/Google policies."""


def run(brands=None):
    from .brain import ask_gemini
    today = str(datetime.date.today())
    lines = [f"📓 SEO DIARY · {today}"]
    merged = {"do_more": [], "avoid": [], "title_tips": []}
    for b in (brands or list(BRANDS)):
        try:
            oth = _others(b)
            if not oth:
                lines.append(f"\n• {BRANDS[b]['name']}: YouTube login/quota nahi - is hafte skip")
                continue
            res = ask_gemini(PROMPT.format(name=BRANDS[b]["name"], brand=b,
                                           others=json.dumps(oth[:8], ensure_ascii=False)[:3500],
                                           ours=json.dumps(_ours(b), ensure_ascii=False)[:1500]),
                             json_mode=True, temperature=0.4)
            rec = {"t": today, "brand": b, "others": oth[:8], "notes": res}
            FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            for k in merged:
                merged[k] += (res.get(k) or [])[:2]
            best = oth[0]
            lines.append(f"\n🎯 {BRANDS[b]['name']} (khoj: {best['query']})")
            lines.append(f"Sabse tez doosri video: \"{best['title'][:60]}\" - {best['per_day']:,} views/din, {best['secs']}s")
            lines += ["✅ Unki jeet: " + "; ".join((res.get("why_they_win") or [])[:3]),
                      "⚠️ Hum peeche kyun: " + "; ".join((res.get("why_we_lag") or [])[:2]),
                      "👉 Ab karein: " + "; ".join((res.get("do_more") or [])[:3]),
                      "💡 Naye topic: " + "; ".join((res.get("topic_ideas") or [])[:3])]
            if res.get("website_ideas"):
                lines.append("🌐 Website: " + "; ".join(res["website_ideas"][:2]))
            ideas = [x for x in (res.get("topic_ideas") or []) if isinstance(x, str)][:3]
            if ideas:                      # sirf SUJHAAV: hafte ke plan mein jaate hain, jise owner manzoor karta hai
                state.update("seo_ideas", lambda d, b=b, i=ideas: {**(d or {}), b: i}, {})
        except Exception as e:
            log(f"seodiary {b}: {e}")
            lines.append(f"\n• {BRANDS[b]['name']}: abhi nahi ho paya ({str(e)[:80]})")
    if any(merged.values()):                # writer har nayi script mein ye seekh maanta hai
        ins = state.get("insights") or {}
        for k, v in merged.items():
            ins[k] = list(dict.fromkeys(v + (ins.get(k) or [])))[:6]
        ins["seo_diary_at"] = today
        state.put("insights", ins)
    state.put("seo_diary_day", today)
    return "\n".join(lines)[:3900]


def text_view(n=4):
    """Diary ki aakhri entries (owner maange to)."""
    try:
        rows = [json.loads(x) for x in FILE.read_text(encoding="utf-8").splitlines() if x.strip()][-n:]
    except Exception:
        rows = []
    if not rows:
        return "📓 SEO diary abhi khaali hai. Har Shanivaar 21:00 apne aap banti hai. Abhi chahiye to likhein: 'seo diary abhi'."
    out = ["📓 SEO diary (aakhri entries):"]
    for r in rows:
        nt = r.get("notes") or {}
        out.append(f"\n{r['t']} · {BRANDS.get(r['brand'], {}).get('name', r['brand'])}")
        out.append("✅ " + "; ".join((nt.get("why_they_win") or [])[:3]))
        out.append("👉 " + "; ".join((nt.get("do_more") or [])[:3]))
    return "\n".join(out)[:3900]
