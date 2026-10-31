"""v2.0.2: Kamaai + traffic engine (sab policy ke andar, sab apne aap).

1) recount(): website ki tool ginti badli (188 -> 190) to purani YouTube video ki description (aur FB reel caption)
   mein purana number + adhoora link apne aap theek. Roz max 15 YouTube update (API quota ka 750/10,000 unit).
   Instagram/Threads caption API se edit nahi hote (platform ka niyam) - wahan nayi post sahi number ke saath.
2) gsc_ideas(): Google Search Console ki query - jahan log dhoondh rahe (impression zyada) par click kam -
   (a) wahi query video topic bankar apne aap line mein (website ke usi page ka link) = search + social dono se traffic
   (b) title/description sudharne ki salah owner ko (page badalna ZIP + audit ke raaste hi).
3) best_hours(): pichhle 30 din mein kis ghante ki video ko zyada views - har Ravivaar report (samay badalna owner ki
   pushti se hi - schedule strictly wahi rehta hai jo manzoor hai).
"""
import datetime
import re
import requests
from . import state, tg, diary
from .config import BRANDS, SITE
from .log import log


def recount(max_updates=15):
    from .guardtext import clean, stale_count, count
    from . import youtube
    n = count()
    if not n:
        return "ginti nahi mili"
    done = 0
    fixed = state.get("recount_done") or {}
    key = str(n)
    for b in BRANDS:
        if done >= max_updates or not youtube.has_login(b):
            continue
        try:
            vids = [v["vid"] for v in youtube.recent_videos(b, 50)]
        except Exception as e:
            log(f"recount list {b}: {e}")
            continue
        todo = [v for v in vids if fixed.get(v) != key][: max_updates - done]
        if not todo:
            continue
        try:
            items = youtube._api(b, "GET", "/youtube/v3/videos", params={"part": "snippet", "id": ",".join(todo)}).get("items", [])
        except Exception as e:
            log(f"recount get {b}: {e}")
            continue
        for it in items:
            sn, vid = it["snippet"], it["id"]
            d = sn.get("description", "")
            new = clean(d)
            if new != d and (stale_count(d) or "sabhisaab.com" in d):
                body = {"id": vid, "snippet": {"title": sn["title"], "description": new[:5000],
                                               "categoryId": sn.get("categoryId", "27"), "tags": sn.get("tags", []),
                                               "defaultLanguage": sn.get("defaultLanguage", "hi")}}
                try:
                    youtube._api(b, "PUT", "/youtube/v3/videos", params={"part": "snippet"}, json=body)
                    done += 1
                    diary.add("upload", f"purani video description theek ({BRANDS[b]['name']}): ginti {n} / poora link")
                except Exception as e:
                    log(f"recount put {vid}: {e}")
                    continue
            fixed[vid] = key
    state.put("recount_done", dict(list(fixed.items())[-1500:]))
    return f"{done} purani YouTube description theek (ginti {n})"


def _gsc(body):
    from .website import SA, _gcreds
    if not SA.exists():
        return []
    tk = _gcreds("https://www.googleapis.com/auth/webmasters.readonly")
    r = requests.post("https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Asabhisaab.com/searchAnalytics/query",
                      headers={"Authorization": f"Bearer {tk}"}, json=body, timeout=60).json()
    return r.get("rows", [])


def _brand_for(page):
    from .topics import _brand_of
    return _brand_of(SITE + page) or "money"


def gsc_ideas():
    """28 din: impression >= 20, CTR < 3% wali query -> video topic + sudhaar salah."""
    end = datetime.date.today() - datetime.timedelta(days=2)
    rows = _gsc({"startDate": str(end - datetime.timedelta(days=27)), "endDate": str(end),
                 "dimensions": ["query", "page"], "rowLimit": 250})
    if not rows:
        return "GSC data nahi mila (service account?)"
    seen = set(state.get("gsc_topics_seen") or [])
    added, advice = [], []
    for r in sorted(rows, key=lambda x: -x.get("impressions", 0)):
        q, page = r["keys"][0], r["keys"][1].replace(SITE, "") or "/"
        imp, ctr, pos = r.get("impressions", 0), r.get("ctr", 0), r.get("position", 99)
        if imp < 20 or ctr >= 0.03 or q in seen or len(q) < 4:
            continue
        b = _brand_for(page)
        state.update("extra_topics", lambda d, b=b, q=q: {**(d or {}), b: ((d or {}).get(b, []) + [q])[-30:]}, {})
        state.update("topic_pages", lambda d, q=q, p=page: {**dict(list((d or {}).items())[-300:]), q: p}, {})
        seen.add(q)
        added.append(f"{q} → {page} ({BRANDS[b]['name']})")
        if pos <= 15:
            advice.append(f"• {page}: '{q}' {imp} baar dikha, CTR {ctr * 100:.1f}%, position {pos:.0f} - title/description "
                          f"mein ye shabd saaf daalein")
        if len(added) >= 8:
            break
    state.put("gsc_topics_seen", list(seen)[-500:])
    if added:
        diary.add("setting", "GSC se naye video topic: " + "; ".join(added)[:300])
    msg = ("🔎 Google search se seekh (28 din)\n" + ("Naye video topic (apne aap line mein):\n" + "\n".join("• " + a for a in added)
                                                   if added else "Koi naya topic nahi") +
           ("\n\nPage sudhaar ki salah (click badhenge):\n" + "\n".join(advice[:6]) if advice else ""))
    return msg


def best_hours():
    from . import learn
    try:
        d = learn.report()
    except Exception:
        d = ""
    return "⏰ Samay ki seekh:\n" + (d[:800] or "abhi data kam")


# ---------------- v2.0.5: KEYWORD BANK (roz) - koi bhi AI page banane se pehle yahi padhe ----------------
KW_FILE = None


def _kw_action(q, page, imp, pos, ctr):
    ql = q.lower()
    if any(w in ql for w in ("login", "ukfr", "result", "admit card", "news")):
        return "chhodo", "humare vishay ka nahi (login/khabar) - is par page nahi"
    if page in ("/", "") and pos > 8:
        return "naya/milta page", "home par aa raha hai - sahi tool page par is shabd ka FAQ/section; zaroorat ho to ek hi achha page"
    if pos <= 10 and ctr < 0.03:
        return "title/description", f"{page}: title/description mein ye shabd saaf (click kam hain)"
    if pos <= 20:
        return "page mazboot", f"{page}: is sawaal ka seedha jawab + udaharan table/FAQ jodo (position {pos:.0f})"
    return "nazar", "abhi door hai - jab impression badhein tab"


def keyword_bank():
    """GSC (28 din, query+page) -> data/keywords.json + docs/KEYWORDS.md. Pehle se 'manzoor/ho gaya' wale yaad rahte hain.
    Google ki 'scaled content abuse' niti: ek-ek number ke liye alag page (5 lakh, 6 lakh, 7 lakh...) KABHI nahi -
    ek achha page + table/FAQ. Naya page sirf owner ki manzoori ('keyword haan <no.>') ke baad."""
    import json
    from .config import BASE, DATA
    end = datetime.date.today() - datetime.timedelta(days=2)
    rows = _gsc({"startDate": str(end - datetime.timedelta(days=27)), "endDate": str(end),
                 "dimensions": ["query", "page"], "rowLimit": 500})
    if not rows:
        return None
    f = DATA / "keywords.json"
    old = json.loads(f.read_text()) if f.exists() else {}
    agg = {}
    for r in rows:
        q, page = r["keys"][0].strip(), r["keys"][1].replace(SITE, "") or "/"
        a = agg.setdefault(q, {"q": q, "page": page, "imp": 0, "clicks": 0, "pos": 0.0})
        if r.get("impressions", 0) > a.get("_best", 0):
            a["page"], a["_best"] = page, r.get("impressions", 0)
        a["imp"] += r.get("impressions", 0)
        a["clicks"] += r.get("clicks", 0)
        a["pos"] = r.get("position", 99) if not a["pos"] else min(a["pos"], r.get("position", 99))
    out = {}
    for q, a in agg.items():
        a.pop("_best", None)
        ctr = a["clicks"] / a["imp"] if a["imp"] else 0
        act, why = _kw_action(q, a["page"], a["imp"], a["pos"], ctr)
        prev = old.get(q, {})
        out[q] = {**a, "ctr": round(ctr, 4), "action": act, "why": why, "first": prev.get("first", str(datetime.date.today())),
                  "status": prev.get("status", "naya" if act != "chhodo" else "chhodo")}
    for q, prev in old.items():                 # purane manzoor/ho-gaye kabhi na khoyein
        out.setdefault(q, {**prev, "imp": 0})
    f.write_text(json.dumps(out, ensure_ascii=False))
    rank = sorted(out.values(), key=lambda x: (-x["imp"], x["pos"]))
    lines = ["# KEYWORDS - Google Search Console se roz (bot likhta hai)",
             f"Updated: {datetime.datetime.now():%Y-%m-%d %H:%M} IST | 28 din | kul {len(out)} shabd", "",
             "AI/developer ke liye niyam: page/title badalne se PEHLE yahan dekho. 'naya' wale par kaam se pehle owner se",
             "pakka karo (bot: 'keyword haan <no.>' / 'keyword nahi <no.>'). Ek-ek number ke alag page (5 lakh, 6 lakh...)",
             "kabhi nahi - Google ki scaled-content niti; ek achha page + table/FAQ. Duplicate page kabhi nahi (pehle siteknow).", "",
             "| No | Shabd | Impr | Click | Position | Page | Kya karein | Haal |", "|---|---|---|---|---|---|---|---|"]
    for i, k in enumerate(rank[:120], 1):
        lines.append(f"| {i} | {k['q'][:60]} | {k['imp']} | {k['clicks']} | {k['pos']:.0f} | {k['page'][:40]} | "
                     f"{k['action']}: {k['why'][:90]} | {k['status']} |")
    md = "\n".join(lines) + "\n"
    (BASE / "docs").mkdir(exist_ok=True)
    (BASE / "docs" / "KEYWORDS.md").write_text(md)
    state.put("kw_rank", [k["q"] for k in rank[:120]])
    return md


def keyword_mark(no, ok):
    import json
    from .config import DATA
    f = DATA / "keywords.json"
    rank = state.get("kw_rank") or []
    if not f.exists() or not (1 <= no <= len(rank)):
        return "Ye number list mein nahi. 'keywords' likh kar list dekhein."
    d = json.loads(f.read_text())
    q = rank[no - 1]
    d[q]["status"] = "manzoor" if ok else "nahi"
    f.write_text(json.dumps(d, ensure_ascii=False))
    from . import diary
    diary.add("setting", f"keyword {'manzoor' if ok else 'nahi'}: {q}")
    return f"✅ '{q}' → {'manzoor (agle page/upgrade mein AI isi par kaam karega)' if ok else 'nahi karenge'}."


def keyword_text(n=15):
    rank = state.get("kw_rank") or []
    import json
    from .config import DATA
    f = DATA / "keywords.json"
    if not rank or not f.exists():
        return "Keyword list abhi nahi bani (roz 07:00 banti hai). Abhi: 'keywords taaza'."
    d = json.loads(f.read_text())
    out = ["🔑 Google par log ye khoj kar aa rahe hain (28 din):"]
    for i, q in enumerate(rank[:n], 1):
        k = d[q]
        out.append(f"{i}. {q} — {k['imp']} baar, pos {k['pos']:.0f} → {k['action']} [{k['status']}]")
    out.append("\nManzoor: 'keyword haan 2'  |  Na: 'keyword nahi 2'  |  Poori list: docs/KEYWORDS.md (GitHub)")
    return "\n".join(out)
