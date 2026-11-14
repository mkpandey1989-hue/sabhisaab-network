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
    for f in ("kind", "hour", "brand", "fmt", "mood", "palette", "layout", "hook", "visual", "pkind", "theme3d",
              "vpal", "vlay", "hstyle", "look24", "vmech"):   # v3.2.0 jawab-tareeka    # v2.3.5 sawal-category + 3D; v2.7.5 video ka rang/layout/hook-andaaz/24-look
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


# ---------------- v2.3.0 Step 5 (v11 se): Hook bandit + script score + retention/fatigue jaanch ----------------
# v11 ke hook mein banaye hue aankde the ("99% log", "sirf 3%", "95%", "90% yuva") - YouTube ki 'misleading' niti ke
# khilaaf aur jhooth. Yahan wahi andaaz, bina jhoothe aankde. Jeet ka hisaab asli views se (pehle kabhi update nahi hota tha).
HOOK_BANK = [
    "रोज़ दिखने वाली इस चीज़ का असली हिसाब बहुत कम लोग जानते हैं!",
    "5 सेकंड का दिमागी टेस्ट: बिना कैलकुलेटर बताइए सही जवाब क्या होगा?",
    "रुकिए! यह छोटी सी गलती हर महीने आपके पैसे घटा सकती है!",
    "ज़्यादातर लोग यहाँ जल्दबाज़ी में गलत विकल्प चुन लेते हैं - आप?",
    "क्या आपकी नज़र और दिमाग़ सच में तेज़ हैं? अभी 5 सेकंड में परखिए!",
    "दुकान या बैंक में यह गणित कोई खुलकर नहीं समझाता - आज समझिए!",
    "क्या आपको इसका शुद्ध हिंदी नाम पता है?",
    "सिर्फ़ 1 नियम समझ लीजिए, पैसे का हिसाब कभी गलत नहीं होगा!",
    "चुनौती: वीडियो खत्म होने से पहले सही जवाब बताइए!",
    "खरीदारी से पहले यह 3 सेकंड का फॉर्मूला ज़रूर लगाइए!",
    "पहाड़ का यह रोचक तथ्य शायद आपने पहले नहीं सुना!",
    "अगर बचत बढ़ानी है, तो यह 20 सेकंड का हिसाब ध्यान से देखिए!",
]


def pick_bandit_hook(brand, rnd=None):
    """Epsilon-greedy: 80% ab tak sabse zyada views wala hook, 20% naya aazmao."""
    rnd = rnd or random.Random()
    d = load().get("views_hook", {})
    if rnd.random() < 0.20 or not d:
        return rnd.choice(HOOK_BANK)
    return max(HOOK_BANK, key=lambda h: weight("hook", h) * rnd.uniform(0.9, 1.1))


def score_script(script):
    """1-10 score: hook (pehla scene), jigyasa (jawab end mein), saaf text, lambai. 7 se kam = kamzor."""
    scenes = script.get("scenes") or []
    title = script.get("title") or ""
    first = scenes[0].get("show", "") if scenes else ""
    s_hook = 7.0 + (2.0 if any(c in first or c in title for c in ("?", "!", "%", "₹", "सेकंड", "सच", "कैसे", "क्या")) else 0) \
        + (0.8 if len(first) <= 95 else 0)
    s_cur = 7.2 + (2.0 if len(scenes) >= 4 and any("सही" in sc.get("show", "") or "सबक" in sc.get("show", "") for sc in scenes[-3:]) else 0)
    s_clar = 8.5 if all(len(sc.get("show", "")) <= 125 for sc in scenes) else 6.0
    s_len = 9.0 if 4 <= len(scenes) <= 8 or script.get("format") == "long" else 5.5
    total = round((s_hook + s_cur + s_clar + s_len) / 4.0, 2)
    return {"score_hook": round(min(10.0, s_hook), 1), "score_curiosity": round(min(10.0, s_cur), 1),
            "score_clarity": round(min(10.0, s_clar), 1), "score_length": round(min(10.0, s_len), 1),
            "score_total": min(10.0, total), "passed": total >= 7.0}


def analyze_retention_drop():
    """Pichhli videos ki average retention -> agli script ki raftaar ki salaah (writer ko jaati hai)."""
    rets = [float(v["retention"]) for v in video_table(40) if v.get("retention") is not None]
    avg = round(sum(rets) / len(rets), 1) if rets else None
    if avg is None:
        return {"avg_retention": None, "auto_edit_advice": "Retention data abhi nahi (YouTube Analytics jodne ke baad)."}
    if avg < 45.0:
        act = "Pehle 3 second mein number/sawal rakho; har scene 4 second se chhota."
    elif avg < 65.0:
        act = "Beech (8-14 sec) mein bonus sawal / twist jodo."
    else:
        act = "Retention achhi (65%+) - yahi andaaz jaari."
    return {"avg_retention": avg, "auto_edit_advice": act}


def check_fatigue_and_reach_drop():
    """Aakhri 3 video ke views pichhli ausat se 30%/50% kam? (sirf jaankari + salaah; khud kuch nahi badalta)"""
    views = [int(v.get("views", 0)) for v in video_table(30) if v.get("views") is not None]
    if len(views) < 6:
        return {"fatigue": False, "reach_drop": False, "drop_pct": 0.0, "note": "Data abhi ban raha hai (6+ video chahiye)."}
    prev = sum(views[:-3]) / max(1, len(views[:-3]))
    rec = sum(views[-3:]) / 3.0
    drop = round(100.0 * (prev - rec) / prev, 1) if prev > 0 else 0.0
    return {"prev_avg_views": round(prev, 1), "recent_avg_views": round(rec, 1), "drop_pct": drop,
            "fatigue": drop >= 30.0, "reach_drop": drop >= 50.0,
            "note": ("🚨 Reach 50%+ giri - salaah: Studio mein naya visual/puzzle look aazmayein" if drop >= 50.0
                     else ("⚠ 30%+ giravat - salaah: hook/andaaz badlein (din-plan / Studio)" if drop >= 30.0
                           else "✅ Reach theek hai."))}


# ---------------- v2.7.5 (owner: 'jo look/andaaz fayde ka hai wo apne aap zyada chale') ----------------
MIN_TRIES = 3          # har naya vikalp kam se kam itni video mein aazmaya jaaye (naya look kabhi daba na rahe)
EXPLORE = 0.25         # 25% baar bina wazan ke (bazaar/trend badle to naya bhi jeet sake)


def choose(feature, options, seed, avoid=None):
    """Views ke hisaab se chunav: kam aazmaye pehle (MIN_TRIES tak), phir jeetne wale ka zyada wazan, 25% khoj.
    'avoid' (pichhla) dobara nahi agar aur vikalp hon. Bina network, pakka-dohraane layak (seed)."""
    opts = [o for o in options if o not in (avoid,)] or list(options)
    if not opts:
        return None
    rnd = random.Random(str(seed))
    d = load().get("views_" + feature, {})
    fresh = [o for o in opts if len((d.get(str(o)) or {}).get("videos", [])) < MIN_TRIES]
    if fresh:
        return rnd.choice(fresh)
    if rnd.random() < EXPLORE:
        return rnd.choice(opts)
    ws = [weight(feature, o) for o in opts]
    return rnd.choices(opts, weights=ws, k=1)[0]


def winners_text(top=3):
    """Owner ke liye: kaunsa rang/layout/andaaz/24-look/sawal-type sabse zyada dekha gaya."""
    d = load()
    names = {"vpal": "🎨 Rang", "vlay": "🧩 Layout", "hstyle": "🎣 Sawal ka andaaz", "look24": "✨ 24-Look", "pkind": "❓ Sawal-type",
             "hour": "⏰ Ghanta", "vmech": "🎯 Jawab-tareeka"}
    L = ["🏆 KYA CHAL RAHA HAI (asli views ka ausat, kam se kam 3 video)"]
    for f, nm in names.items():
        rows = [(k, v["views"] / len(v["videos"]), len(v["videos"])) for k, v in d.get("views_" + f, {}).items() if len(v["videos"]) >= 3]
        rows.sort(key=lambda x: -x[1])
        if rows:
            L.append(f"{nm}: " + ", ".join(f"{k} ~{a:.0f} ({n})" for k, a, n in rows[:top]))
    if len(L) == 1:
        L.append("Abhi kaafi data nahi - har naya vikalp pehle 3 video mein aazmaya ja raha hai.")
    L.append("Bot inhi se apne aap chunta hai: jeetne wala zyada, par 25% naya bhi (trend badle to).")
    return "\n".join(L)
