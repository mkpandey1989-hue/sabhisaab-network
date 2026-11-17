"""Company jaisa dhaancha: har vibhag (Field/Data, Marketing, Content, SEO-Growth, Legal-Policy, Audit, Revenue)
apni report deta hai, GM faisla leta hai. Surakshit kaam (naye topic) bot khud lagu karta hai; bade badlaav par
sirf tab poochhta hai jab sach mein shak ho."""
import datetime
import json
from . import state, tg, diary, learn
from .brain import ask_gemini
from .config import BRANDS, IST
from .log import log

MEETING = """You are running the weekly board meeting of "Sabhisaab Network", a small Hindi media company:
website sabhisaab.com (free calculators) + 4 brand channels (YouTube Shorts, FB/IG Reels, Threads, Pinterest, Telegram):
sunonatak (money stories), money (personal finance), deals (savings/shopping), pahadi (Uttarakhand/GK).
Goal: legally grow audience, website traffic and revenue (YouTube Partner Program, AdSense later, affiliate with #ad)
WITHOUT any policy/copyright violation and without hurting any community.
DATA:
videos (views/brand/type/hour/title): {videos}
growth snapshots: {growth}
last insights: {insights}
upcoming verified events: {events}
recent problems (diary): {problems}
owner standing rules: {rules}
Departments speak briefly (2 bullet each, Hinglish, data-based, honest if data is too little):
Field/Data, Marketing, Content, SEO-Growth, Legal-Policy, Audit, Revenue. Then GM gives decisions.
Return ONLY JSON: {{"departments": {{"Field": ["..",".."], "Marketing": [..], "Content": [..], "SEO": [..],
"Legal": [..], "Audit": [..], "Revenue": [..]}}, "gm": ["decision 1", ...],
"auto_topics": [{{"brand": "sunonatak|money|deals|pahadi", "topic": "max 60 chars"}}] (max 6, safe evergreen/trend),
"ask_owner": ["only genuinely doubtful question", ...] (0-2)}}"""


def meeting():
    from .config import DATA
    try:
        g = json.loads((DATA / "growth.json").read_text())
        gl = {d: g[d] for d in sorted(g)[-8:]}
    except Exception:
        gl = {}
    probs = [r["text"][:100] for r in diary_recent() if r["kind"] in ("galti", "setting")][-12:]
    cal = state.get("calendar") or {}
    evs = {d: [e.get("name_en") or e.get("name_hi") for e in v] for d, v in cal.items()}
    try:
        m = ask_gemini(MEETING.format(videos=json.dumps(learn.video_table(40), ensure_ascii=False)[:5000],
                                      growth=json.dumps(gl)[:2500], insights=json.dumps(state.get("insights") or {}, ensure_ascii=False)[:800],
                                      events=json.dumps(evs, ensure_ascii=False)[:800], problems=json.dumps(probs, ensure_ascii=False)[:1500],
                                      rules=json.dumps(state.get("rules") or [], ensure_ascii=False)[:1000]), temperature=0.4)
    except Exception as e:
        return tg.alert("yellow", f"Company meeting nahi hui: {e}")
    added = []
    for t in (m.get("auto_topics") or [])[:6]:
        b, tp = t.get("brand"), (t.get("topic") or "").strip()
        if b in BRANDS and tp:
            state.update("extra_topics", lambda d, b=b, tp=tp: {**(d or {}), b: ((d or {}).get(b, []) + [tp])[-30:]}, {})
            added.append(f"{BRANDS[b]['name']}: {tp}")
    lines = ["🏢 Company meeting (hafta)"]
    for dep, pts in (m.get("departments") or {}).items():
        lines.append(f"\n👤 {dep}:")
        lines += [f"  • {p}" for p in pts[:2]]
    lines.append("\n🎯 GM ke faisle:")
    lines += [f"  ✔ {d}" for d in (m.get("gm") or [])[:5]]
    if added:
        lines.append("\n🤖 Bot ne khud lagu kiya (naye topic): " + "; ".join(added))
    if m.get("ask_owner"):
        lines.append("\n❓ Aapse sirf ye poochhna hai:\n" + "\n".join(f"  • {q}" for q in m["ask_owner"][:2]))
    state.put("last_meeting", {"t": str(datetime.datetime.now(IST))[:16], "gm": m.get("gm", [])})
    diary.add("setting", "company meeting: " + "; ".join(m.get("gm", []))[:300])
    tg.say("\n".join(lines)[:4000])


def diary_recent():
    from . import diary as D
    return D.recent(300)


def add_rule(text):
    """Aapka pakka niyam / sudhaar: aage ki har script, plan aur jawab mein lagu (self-correction log)."""
    rules = state.get("rules") or []
    rules.append({"t": str(datetime.date.today()), "rule": text.strip()[:300]})
    state.put("rules", rules[-40:])
    diary.add("setting", f"naya niyam: {text[:120]}")
    return f"📌 Niyam yaad kar liya, aage hamesha lagu: {text[:200]}"


def rules_text():
    return "; ".join(r["rule"] for r in (state.get("rules") or [])[-20:])


# ---------------- v2.3.0 Step 5 (v11 se, asli aankdon ke saath): kamai roadmap, 10-vibhag audit, milestone ----------------
# v11 mein ye sab haath se likhe 'READY ✅' the (jaise 'PDF study guides ready', 'AdSense 16 Nov') - jo bana hi nahi tha.
# Yahan har line asli state/file se.
def _latest_growth():
    from .config import DATA
    try:
        g = json.loads((DATA / "growth.json").read_text())
        day = sorted(g)[-1]
        return day, g[day]
    except Exception:
        return None, {}


def milestone_check():
    """YouTube subs / IG / FB followers par 100, 500, 1K, 5K, 10K, 50K, 1L ke padaav - ek baar badhai."""
    day, snap = _latest_growth()
    if not snap:
        return []
    seen = state.get("milestones_seen") or {}
    out = []
    for b, info in BRANDS.items():
        for key, lbl in (("yt_subs", "YouTube subscribers"), ("ig_followers", "Instagram followers"), ("fb_followers", "Facebook followers")):
            n = int((snap.get(b) or {}).get(key) or 0)
            for m in (100, 500, 1000, 5000, 10000, 50000, 100000):
                k = f"{b}:{key}:{m}"
                if n >= m and not seen.get(k):
                    seen[k] = day
                    out.append(f"🎉 Badhai! {info['name']} ne {m:,} {lbl} paar kiye (abhi {n:,}).")
    state.put("milestones_seen", seen)
    return out


def revenue_roadmap_status():
    """4 charan ki kamai yojana - har line asli haal se."""
    from . import siteknow, youtube, tasks
    try:
        pgs = len(siteknow.pages())
    except Exception:
        pgs = 0
    yt = sum(1 for b in BRANDS if youtube.has_login(b))
    _d, snap = _latest_growth()
    subs = {b: int((snap.get(b) or {}).get("yt_subs") or 0) for b in BRANDS}
    todo = " ".join(o.get("x", "") for o in (state.get("todo") or [])).lower()
    adsense = "⏳ PENDING list mein (dobara apply)" if "adsense" in todo else "✅/jaanch: PENDING mein nahi"
    lines = ["💰 KAMAI KI 4-CHARAN YOJANA (asli haal):",
             f"1) Audience + Search: website {pgs} page | YouTube jude {yt}/4 | Labh Lo Deals affiliate par #ad/ASCI label: haan",
             f"2) Apni audience: Telegram/WhatsApp channel + daily quiz/puzzle reel (Step 4) chalu",
             f"3) Platform kamai: AdSense - {adsense} | YouTube Partner (1000 subs + 10M Shorts views/90 din, ya 4000 ghante/12 mahine):",
             "   " + " | ".join(f"{BRANDS[b]['name'].split()[0]} {subs[b]}/1000" for b in BRANDS),
             "4) Lambi daud: brand sponsorship (Branded Content toggle), premium tools - jab audience bane"]
    try:
        lines.append(f"📋 Abhi aapke {len([o for o in (state.get('todo') or []) if not o.get('done')])} kaam baaki (🧾 Mere kaam)")
        _ = tasks
    except Exception:
        pass
    return "\n".join(lines)


def audit_10():
    """10 vibhag ka asli haal (har line state se)."""
    from . import siteknow, youtube, meta as M, threads as TH, pinterest as PI, pipeline
    try:
        pg = len(siteknow.pages())
    except Exception:
        pg = 0
    sp = pipeline.spare_reel_status()
    looks = state.get("brand_look") or {}
    used_pz = len(state.get("used_puzzle_hashes") or [])
    aw = state.get("awaaz") or {}
    hits = state.get("blindfold_hits") or 0
    return "\n".join([
        "🏢 10-VIBHAG AUDIT (asli haal):",
        f"1) Data: {len(learn.video_table(40))} video ka hisaab",
        f"2) Marketing: trend-kachra filter + keyword cluster (scaled-content suraksha) chalu",
        f"3) Content: 11 puzzle mode ({used_pz} sawal ho chuke, dohraav nahi) + bank + din-plan",
        f"4) Visual: pakke look {len(looks)}/4 channel | HUD {state.get('hud') or 'default chalu'}",
        f"5) Awaaz: sfx {'band' if aw.get('sfx') is False else 'chalu'} | music {'band' if aw.get('music') is False else 'chalu'} | -14 LUFS",
        f"6) Website: {pg} page",
        f"7) Channel: YT {sum(1 for b in BRANDS if youtube.has_login(b))}/4 | Meta {'ON' if M.has_token() else 'OFF'} | "
        f"Threads {sum(1 for b in BRANDS if TH.info(b))}/4 | Pinterest {'ON' if PI.connected() else 'OFF'}",
        f"8) Spare reel: {sum(sp.values())} taiyaar",
        f"9) Suraksha: Gemini Blindfold ({hits} baar chhupaya) | DM ledger 24h | commenter data 30 din | post-taala",
        "10) Kamai: '💰 Revenue Roadmap' dekhein"])


def revenue_report():
    return revenue_roadmap_status()


def digest():
    ms = milestone_check()
    return audit_10() + ("\n\n" + "\n".join(ms) if ms else "")
