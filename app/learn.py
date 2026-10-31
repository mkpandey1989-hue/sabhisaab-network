"""Seekhna: kaun sa rang / design / emoji zyada click (CTR) laata hai.
YouTube Analytics se har video ke impressions aur CTR aayenge (v0.3), yahan jud jayenge.
Chunaav: 2 thumbnail jo ab tak sabse achhe chale, 1 hamesha naya (taaki naye rang bhi aazmaye jayein)."""
import json
import random
from .config import DATA

STORE = DATA / "learn.json"
KINDS = ("palette", "layout", "emoji", "mood")


def load():
    try:
        return json.loads(STORE.read_text())
    except Exception:
        return {k: {} for k in KINDS} | {"videos": {}}


def save(d):
    STORE.write_text(json.dumps(d, ensure_ascii=False, indent=1))


def score(d, kind, name):
    s = d.get(kind, {}).get(name, {})
    return (s.get("clicks", 0) + 2) / (s.get("impr", 0) + 40)   # shuru mein sab barabar (~5%)


def pick(kind, options, k, rnd: random.Random, explore=1):
    d = load()
    opts = list(options)
    chosen = []
    for i in range(k):
        if i >= k - explore:
            c = rnd.choice(opts)                       # naya aazmao
        else:
            w = [score(d, kind, o) * rnd.uniform(0.7, 1.3) for o in opts]
            c = opts[w.index(max(w))]                 # ab tak ka sabse achha
        chosen.append(c)
        opts.remove(c)
    return chosen


def record_upload(video_id, variant: dict):
    d = load()
    d["videos"][video_id] = {"variant": variant, "impr": 0, "clicks": 0}
    save(d)


def update_stats(video_id, impressions: int, ctr_percent: float):
    """YouTube Analytics se aaye naye aankde jodo (sirf badhotri gini jaati hai)."""
    d = load()
    v = d["videos"].get(video_id)
    if not v:
        return
    clicks = int(impressions * ctr_percent / 100)
    di, dc = max(0, impressions - v["impr"]), max(0, clicks - v["clicks"])
    v["impr"], v["clicks"] = impressions, clicks
    for kind in KINDS:
        name = v["variant"].get(kind)
        if name:
            s = d.setdefault(kind, {}).setdefault(name, {"impr": 0, "clicks": 0})
            s["impr"] += di
            s["clicks"] += dc
    save(d)


def report(top=3):
    d = load()
    lines = []
    for kind in ("palette", "layout", "emoji"):
        items = sorted(d.get(kind, {}).items(), key=lambda kv: -score(d, kind, kv[0]))[:top]
        if items:
            lines.append(f"{kind}: " + ", ".join(f"{n} {100 * score(d, kind, n):.1f}%" for n, _ in items))
    return "\n".join(lines) or "Abhi data nahi (upload ke baad aayega)"



# ---------- v0.7: views se seekhna (kaunsa topic-type / samay / brand / mood zyada chalta hai) ----------
def update_views(vid, views):
    d = load()
    v = d["videos"].get(vid)
    if not v:
        return
    old = v.get("views", 0)
    v["views"] = views
    var = v.get("variant", {})
    for f in ("kind", "hour", "brand", "fmt", "mood", "palette", "layout"):
        name = var.get(f)
        if name:
            s = d.setdefault("views_" + f, {}).setdefault(str(name), {"views": 0, "videos": []})
            if vid not in s["videos"]:
                s["videos"].append(vid)
            s["views"] += max(0, views - old)
    save(d)


def avg_views(feature, name):
    s = load().get("views_" + feature, {}).get(str(name))
    if not s or not s["videos"]:
        return None
    return s["views"] / len(s["videos"])


def weight(feature, name, base=1.0):
    """Jo zyada dekha gaya uska wazan zyada (par naya bhi aazmaya jata rahe)."""
    d = load().get("views_" + feature, {})
    allv = [x["views"] / len(x["videos"]) for x in d.values() if x["videos"]]
    a = avg_views(feature, name)
    if a is None or not allv:
        return base
    mean = sum(allv) / len(allv) or 1
    return max(0.3, min(3.0, a / mean)) * base


def video_table(limit=40):
    vids = list(load()["videos"].items())[-limit:]
    return [{"vid": k, "views": v.get("views", 0), "retention": v.get("retention"), "ctr": v.get("ctr"),
             **{f: v.get("variant", {}).get(f) for f in ("brand", "kind", "hour", "title", "fmt", "palette", "layout")}}
            for k, v in vids]
