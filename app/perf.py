"""v3.4.34 (owner 19 Nov: "faltu information/credit card wali video koi nahi dekhta - views ke hisaab se jo nahi chal raha wo
sawal hi band kar do; ye rights mere likhne aur confirmation ke baad bhi ho").

1) Har hafte (Ravivaar 19:00) pichhle 30 din ki har reel ke ASLI YouTube views (answer_key: brand, kind, yt link) ->
   har brand mein har sawal-type (kind) ka ausat. Jo type brand ke median ke 50% se kam (kam se kam 4 reel) = KAMZOR.
2) Kamzor type ka sandesh + button '🚫 Band karo'. 24 ghante jawab nahi -> bot khud band karta hai (owner ne kaha 'khud
   check karke band karo'), sandesh + '↩️ Wapas chalu' button. Sab ulta ho sakta hai.
3) Owner khud: '<shabd> wale sawal band karo' (jaise 'credit card wale sawal band karo') -> pushti button -> wo shabd
   kisi bhi naye sawal/video mein nahi (video audit + sawal-bank dono). 'band vishay' = suchi, '<shabd> chalu karo' = hatao.
Koi nakli aankda nahi: views YouTube API se; jahan data kam (4 se kam reel) wahan faisla nahi.
"""
import datetime
import re
import statistics
import time

from . import state, tg
from .config import BRANDS
from .log import log

MIN_N = 4
WEAK = 0.5
AUTO_HOURS = 24
YT_RX = re.compile(r"(?:youtu\.be/|shorts/|v=)([A-Za-z0-9_\-]{11})")


def kind_name(k):
    try:
        from .design import KIND_NAME
        return KIND_NAME.get(k, k or "aam sawal (AI vishay)")
    except Exception:
        return k or "aam sawal (AI vishay)"


def blocked_kinds(brand):
    return set((state.get("kind_block") or {}).get(brand, []))


def blocked_words():
    return [w for w in (state.get("topic_block") or []) if w]


def word_blocked(text):
    t = (text or "").lower()
    return next((w for w in blocked_words() if w.lower() in t), None)


def collect(days=30):
    """-> {brand: {kind: [views,...]}} (sirf 2+ din purani reel - views tik jaate hain)"""
    from . import youtube
    cut_new = str(datetime.date.today() - datetime.timedelta(days=2))
    cut_old = str(datetime.date.today() - datetime.timedelta(days=days))
    rows = {}
    for e in state.get("answer_key") or []:
        d = str(e.get("date", ""))
        m = YT_RX.search(str(e.get("yt") or ""))
        if not m or not (cut_old <= d <= cut_new) or e.get("brand") not in BRANDS:
            continue
        rows.setdefault(e["brand"], []).append((m.group(1), e.get("kind") or "", e.get("q", "")))
    out = {}
    for b, lst in rows.items():
        try:
            st = youtube.stats(b, [v for v, _, _ in lst])
        except Exception as ex:
            log(f"perf {b}: {ex}")
            continue
        for v, k, _q in lst:
            if v in st:
                out.setdefault(b, {}).setdefault(k, []).append(st[v]["views"])
    return out


def analyze(data):
    """-> (report_lines, weak=[(brand, kind, avg, median, n)])"""
    L, weak = [], []
    for b, kinds in data.items():
        allv = [x for v in kinds.values() for x in v]
        if len(allv) < 6:
            continue
        med = statistics.median(allv)
        L.append(f"━ {BRANDS[b]['name']} (median {int(med)} views, {len(allv)} reel)")
        for k, vs in sorted(kinds.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
            avg = sum(vs) / len(vs)
            flag = ""
            if len(vs) >= MIN_N and med > 0 and avg < WEAK * med and k not in blocked_kinds(b):
                flag = " ⚠️ KAMZOR"
                weak.append((b, k, int(avg), int(med), len(vs)))
            L.append(f"  • {kind_name(k)}: ausat {int(avg)} ({len(vs)} reel){flag}")
    return L, weak


def weekly():
    data = collect()
    L, weak = analyze(data)
    if not L:
        return tg.say("📉 Sawal-type jaanch: abhi kaafi data nahi (har brand ki 6+ reel 2 din purani chahiye).")
    tg.say("📉 KAUN SA SAWAL CHAL RAHA (YouTube asli views, 30 din):\n" + "\n".join(L)[:3800])
    pend = state.get("kind_pending") or {}
    for b, k, avg, med, n in weak[:6]:
        key = f"{b}|{k}"
        pend[key] = time.time()
        tg.say(f"🚫 {BRANDS[b]['name']}: '{kind_name(k)}' wale sawal kam chalte hain (ausat {avg} vs channel {med}, {n} reel).\n"
               f"Band karein? {AUTO_HOURS} ghante jawab nahi aaya to main khud band kar dunga (baad mein chalu ho sakta hai).",
               tg.inline([[("🚫 Haan, band karo", f"kb:{b}|{k}"), ("✅ Chalne do", f"kk:{b}|{k}")]]))
    state.put("kind_pending", pend)


def set_kind(brand, kind, block, by="owner"):
    kb = state.get("kind_block") or {}
    cur = set(kb.get(brand, []))
    (cur.add if block else cur.discard)(kind)
    kb[brand] = sorted(cur)
    state.put("kind_block", kb)
    pend = state.get("kind_pending") or {}
    pend.pop(f"{brand}|{kind}", None)
    state.put("kind_pending", pend)
    try:
        from . import diary
        diary.add("setting", f"sawal-type {'BAND' if block else 'chalu'} ({by}): {BRANDS[brand]['name']} - {kind_name(kind)}")
    except Exception:
        pass


def on_callback(kind_, rest):
    b, _, k = rest.partition("|")
    if b not in BRANDS:
        return tg.say("Purana button.")
    if kind_ == "kb":
        set_kind(b, k, True)
        return tg.say(f"🚫 Band: {BRANDS[b]['name']} - '{kind_name(k)}'. Aage ye type nahi banega.",
                      tg.inline([[("↩️ Wapas chalu", f"ku:{b}|{k}")]]))
    if kind_ == "ku":
        set_kind(b, k, False)
        return tg.say(f"✅ Chalu: {BRANDS[b]['name']} - '{kind_name(k)}'.")
    pend = state.get("kind_pending") or {}
    pend.pop(rest, None)
    state.put("kind_pending", pend)
    return tg.say(f"👍 '{kind_name(k)}' chalta rahega ({BRANDS[b]['name']}).")


def tick():
    """24 ghante jawab nahi -> khud band (owner ka hukum: 'khud check karke band karo')."""
    pend = state.get("kind_pending") or {}
    for key, at in list(pend.items()):
        if time.time() - float(at) >= AUTO_HOURS * 3600:
            b, _, k = key.partition("|")
            if b in BRANDS:
                set_kind(b, k, True, by="bot, 24 ghante jawab nahi")
                tg.say(f"🚫 24 ghante jawab nahi aaya - {BRANDS[b]['name']} ke '{kind_name(k)}' sawal band kar diye (kam views).",
                       tg.inline([[("↩️ Wapas chalu", f"ku:{b}|{k}")]]))
            pend.pop(key, None)
    state.put("kind_pending", pend)


def due(now):
    return now.weekday() == 6 and now.strftime("%H:%M") >= "19:00" and state.get("perf_day") != str(now.date())


def on_text(tl):
    """'credit card wale sawal band karo' / 'credit card band karo' -> pushti; 'band vishay'; '<x> chalu karo'."""
    tl = (tl or "").strip().lower()
    if tl in ("band vishay", "band sawal", "band topic", "kaun se sawal band", "sawal type haal", "sawal jaanch", "kaun sa sawal chal raha"):
        kb = state.get("kind_block") or {}
        L = ["🚫 BAND (aapke ya bot ke hukum se):"]
        L += [f"• Shabd: {w}" for w in blocked_words()] or ["• Koi shabd band nahi"]
        for b, ks in kb.items():
            for k in ks:
                L.append(f"• {BRANDS.get(b, {}).get('name', b)}: {kind_name(k)}")
        L.append("Chalu karna: '<shabd> chalu karo'. Views wali jaanch abhi: 'sawal jaanch abhi'.")
        return tg.say("\n".join(L)) or True
    if tl in ("sawal jaanch abhi", "views jaanch", "kaun sa sawal kam chal raha"):
        import threading
        threading.Thread(target=weekly, daemon=True).start()
        return tg.say("📉 YouTube se har sawal-type ke views la raha hoon (1-2 min)...") or True
    m = re.fullmatch(r"(.{3,40}?)\s+(?:wale|wali|wala|ke|ki)?\s*(?:sawal|swal|video|videos|vishay|topic|question)\s*band\s*(?:karo|kar do|kro|kardo)", tl)
    if m:
        w = m.group(1).strip()
        if w in ("sab", "saare", "sare", "video", "bot", "aaj ki", "aaj ke", "is", "ye", "yeh"):
            return None
        state.put("tb_ask", w)
        return tg.say(f"⚠️ Pakka? Aage koi bhi naya sawal/video jisme '{w}' ho - nahi banega (sab channel).",
                      tg.inline([[(f"🚫 Haan, '{w}' band", "tb:y"), ("❌ Nahi", "tb:n")]])) or True
    m = re.fullmatch(r"(.{3,40}?)\s+(?:wale|wali|wala)?\s*(?:sawal|swal|video|vishay|topic)?\s*(?:chalu|shuru)\s*(?:karo|kar do|kro)", tl)
    if m and m.group(1).strip() in blocked_words():
        w = m.group(1).strip()
        state.put("topic_block", [x for x in blocked_words() if x != w])
        return tg.say(f"✅ '{w}' wale sawal phir se chalu.") or True
    return None


def tb_answer(yes):
    w = state.get("tb_ask")
    state.put("tb_ask", None)
    if not w:
        return tg.say("Purana button.")
    if not yes:
        return tg.say("👍 Kuch band nahi kiya.")
    state.put("topic_block", sorted(set(blocked_words() + [w])))
    try:
        from . import diary
        diary.add("setting", f"vishay band (owner): {w}")
    except Exception:
        pass
    return tg.say(f"🚫 Band: '{w}' wale sawal/video ab kabhi nahi banenge (video audit + sawal-bank). Wapas: '{w} chalu karo'.")
