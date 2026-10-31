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
