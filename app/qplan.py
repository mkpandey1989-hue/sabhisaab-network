"""v2.7.3 (owner 10 Nov): SAWAL KA HAFTE-WAR SCHEDULE (default; owner jab chahe badle).

Owner ka hukum:
  - Pahadi Hisaab: Uttarakhand GK + pahadi shabd + purane naam.
  - Baaki 3 channel: SIRF sawal/paheli/ganit (ego wale zyada). SIP/FD/RD/loan-app jaise salah wale sawal ZERO (trend gaya).
    Ganit ke sawal (discount, pratishat, speed math) website ke liye kaafi; 'nayi jaankari' (trend GK) chalegi.
  - Din-war alag type, same samay (config.SCHEDULE), kisi channel ka sawal doosre par nahi, roz naya andaaz/rang.
  - Schedule kabhi na toote: plan ka type na mile to channel ka koi bhi jaancha type, phir purana tareeka.
"""
import datetime
import re

from . import state
from .config import BRANDS, SCHEDULE, IST
from .log import log

DAYS = ["Som", "Mangal", "Budh", "Guru", "Shukra", "Shani", "Ravi"]
# (pehla slot, doosra slot) - har din alag; ego/dimag wale zyada; har din ek 'website calculator' wala ganit
PLAN = {
    "sunonatak": [("ego_sawal", "box_rule"), ("dimag_trend", "coding"), ("utpate_shabd", "y_branch"), ("ego_sawal", "missing_digit"),
                  ("trend_gk", "direction"), ("dimag_trend", "magic_square"), ("elite24", "word_scramble")],
    "money": [("ego_sawal", "speed_math"), ("exam_quant", "magic_square"), ("dimag_trend", "age"), ("ego_sawal", "missing_digit"),
              ("trend_gk", "ratio_rule"), ("exam_quant", "pick_sum"), ("elite24", "cross_rule")],
    "deals": [("deals_quiz", "pie_rule"), ("ego_sawal", "color_match"), ("dimag_trend", "missing_digit"), ("deals_quiz", "simplify"),
              ("ego_sawal", "series"), ("pick_sum", "utpate_shabd"), ("elite24", "speed_math")],
    "pahadi": [("pahadi_gk", "pahadi_shabd"), ("pahadi_purana", "pahadi_gk"), ("pahadi_gk", "pahadi_shabd"),
               ("pahadi_shabd", "pahadi_purana"), ("pahadi_gk", "pahadi_shabd"), ("pahadi_purana", "pahadi_gk"),
               ("pahadi_gk", "pahadi_shabd")],
}
NAME = {"ego_sawal": "Ego Test (aasaan dikhe, log galat bolein)", "dimag_trend": "Dimag Hilao paheli", "trend_gk": "Nayi jaankari (GK)",
        "utpate_shabd": "Ulte-pulte shabd", "series": "Number series", "coding": "Coding (BOOK=ANNJ)", "clock_angle": "Ghadi ka kon",
        "calendar": "Calendar paheli", "direction": "Disha paheli", "age": "Umar paheli", "elite24": "24-Look elite paheli",
        "word_scramble": "Shabd jodo", "speed_math": "Speed math", "exam_quant": "Exam ganit (trick)", "sudoku4": "Mini sudoku",
        "number_connect": "Number connect", "purane_shabd": "Purane zamaane ke shabd", "deals_quiz": "Discount/offer ka ganit",
        "odd_one_out": "Alag kaun", "missing_digit": "Khaali ank (9?5 - 682)", "magic_square": "Jaadui vargh (jod 15)",
        "pick_sum": "4 ank jodkar N", "ratio_rule": "Anupaat (4:18::8:?)", "y_branch": "Y paheli", "box_rule": "Dibba paheli",
        "pie_rule": "Gola paheli", "cross_rule": "Cross paheli", "simplify": "Saral kijiye (BODMAS)", "color_match": "Rang milan", "pahadi_gk": "Uttarakhand GK", "pahadi_shabd": "Pahadi boli",
        "pahadi_purana": "Pahad ke purane naam"}
# owner: in vishayon ke sawal 3 aam channel par nahi (salah/trend gaya). Pahadi par lagu nahi.
BLOCK_RX = re.compile(r"\bsip\b|एसआईपी|एस आई पी|म्यूचुअल|mutual fund|\bfd\b|एफडी|फिक्स्ड डिपॉज़िट|fixed deposit|\brd\b|आरडी|"
                      r"रेकरिंग|recurring|लोन ऐप|loan app|लोन एप|कर्ज़ ऐप|instant loan|इंस्टेंट लोन|डिजिटल लोन|ppf|पीपीएफ|"
                      r"बीमा पॉलिसी|insurance policy|शेयर बाज़ार|stock market|निवेश करें|invest|"
                      r"निवेश सलाह|निवेश का|निवेश से|निवेश पर|\bnivesh\b|इन्वेस्ट|शेयर मार्केट|डीमैट|demat|म्यूच्युअल|एस\.आई\.पी", re.I)   # v3.1.0


def is_on():
    return state.get("qplan_on", True)


def slot_index(brand, slot_iso):
    """Din ka pehla (0) ya doosra (1) slot."""
    try:
        hm = datetime.datetime.fromisoformat(slot_iso).astimezone(IST).strftime("%H:%M")
    except Exception:
        return 0
    times = sorted(x.strip() for x in str(SCHEDULE.get(brand, "")).split(",") if x.strip())
    return times.index(hm) if hm in times else 0


def kind_for(brand, slot_iso=None, day=None):
    """Aaj is slot ka sawal-type (owner ka badla hua plan pehle; warna default + views se hua badlaav)."""
    custom = (state.get("qplan_custom") or {}).get(brand)
    plan = custom or PLAN.get(brand)
    if not plan:
        return "auto"
    d = day if day is not None else (datetime.datetime.fromisoformat(slot_iso).astimezone(IST).weekday() if slot_iso
                                      else datetime.datetime.now(IST).weekday())
    k = plan[d % 7][min(1, slot_index(brand, slot_iso) if slot_iso else 0)]
    if not custom:                                  # v2.8.1: views ke hisaab se adla-badli (owner ka plan kabhi nahi chhedte)
        k = (state.get("qplan_swaps") or {}).get(brand, {}).get(k, k)
    return k


# ---------------- v2.8.1 (owner: 'jo sabse zyada views/link laaye usko zyada') - hafte-war apne aap adla-badli ----------------
MIN_VIDS = 3
NEVER = {"money_quiz"}                              # owner: SIP/FD wale kabhi nahi


def kind_stats():
    """learn ke asli views: {kind: (ausat views, video ginti)} - kam se kam 3 video wale."""
    from . import learn
    d = learn.load().get("views_pkind", {})
    return {k: (v["views"] / len(v["videos"]), len(v["videos"])) for k, v in d.items() if len(v.get("videos", [])) >= MIN_VIDS}


def plan_swap(brand, stats=None, swaps=None):
    """Ek brand ka sabse kamzor type (median ka 60% se kam) -> sabse tagda bahar wala (median ka 120%+) ya ek naya (aazmane ko).
    Hafte mein max 1 badlaav; pahadi par bas pahadi type. -> (purana, naya) ya None. Bina network (test ho sake)."""
    from . import puzzles
    stats = kind_stats() if stats is None else stats
    swaps = dict(swaps if swaps is not None else ((state.get("qplan_swaps") or {}).get(brand) or {}))
    base = [k for d_ in PLAN[brand] for k in d_]
    current = [swaps.get(k, k) for k in base]
    have = [k for k in dict.fromkeys(current) if k in stats]
    if len(have) < 3:
        return None
    vals = sorted(stats[k][0] for k in have)
    med = vals[len(vals) // 2] or 1
    worst = min(have, key=lambda k: stats[k][0])
    if stats[worst][0] >= 0.6 * med:
        return None
    pool = [k for k in puzzles.BRAND_KINDS.get(brand, []) if k not in current and k not in NEVER and k != "elite24"
            and (brand != "pahadi" or k.startswith("pahadi"))]
    strong = sorted((k for k in pool if k in stats and stats[k][0] >= 1.2 * med), key=lambda k: -stats[k][0])
    fresh = [k for k in pool if k not in stats]
    new = strong[0] if strong else (fresh[0] if fresh else None)
    if not new:
        return None
    orig = next((o for o, n in swaps.items() if n == worst), worst)
    return orig, new


def weekly_adapt():
    """Har Ravivaar raat: har brand mein ek kamzor type ki jagah behtar (sirf default plan par). -> owner ke liye text"""
    stats = kind_stats()
    all_sw = dict(state.get("qplan_swaps") or {})
    lines = []
    for b in PLAN:
        if (state.get("qplan_custom") or {}).get(b):
            continue
        r = plan_swap(b, stats, all_sw.get(b) or {})
        if r:
            orig, new = r
            all_sw.setdefault(b, {})[orig] = new
            lines.append(f"• {BRANDS[b]['name']}: '{NAME.get(orig, orig)}' kam chala -> ab '{NAME.get(new, new)}'")
    state.put("qplan_swaps", all_sw)
    state.put("qplan_adapt_last", {"t": str(datetime.date.today()), "lines": lines})
    return ("🧠 Sawal-type ka hafte-war sudhaar (asli views se):\n" + "\n".join(lines)) if lines else ""


def blocked(brand, text):
    return brand != "pahadi" and bool(BLOCK_RX.search(str(text or "")))


def pattern(q):
    """Sawal ka saancha: ank hata kar (jaise '(5²-3²)' aur '(10²-8²)' ek hi saancha)."""
    t = re.sub(r"#\S+|\d+(?:[.,]\d+)?", "#", str(q or "").lower())
    t = re.sub(r"[^\w#\u0900-\u097f ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()[:120]


def pattern_recent(q, days=4):
    """Pichhle 4 din mein KISI bhi channel par yahi saancha aaya? (dohraav + 'templated' se bachav)"""
    p = pattern(q)
    if len(p) < 12:
        return False
    cut = str(datetime.date.today() - datetime.timedelta(days=days))
    return any(v >= cut for k, v in (state.get("q_patterns") or {}).items() if k == p)


def remember(q):
    p = pattern(q)
    if len(p) >= 12:
        cut = str(datetime.date.today() - datetime.timedelta(days=30))
        d = {k: v for k, v in (state.get("q_patterns") or {}).items() if v >= cut}
        d[p] = str(datetime.date.today())
        state.put("q_patterns", d)


def ok_script(brand, script):
    """Plan ke niyam: block vishay nahi, pichhle 4 din ka saancha nahi."""
    q = script.get("puzzle_q") or script.get("title", "")
    allt = " ".join([q, script.get("title", "")] + [s.get("show", "") for s in script.get("scenes") or []])
    if blocked(brand, allt):
        return False, "salah/trend-gaya vishay (SIP/FD/RD/loan app)"
    if pattern_recent(q):
        return False, "yahi saancha pichhle 4 din mein aa chuka"
    return True, ""


def cleanup():
    """Purane bank mein jo ab kaam ke nahi (block vishay, 3 aam channel par) - apne aap hatao. -> ginti"""
    n = 0
    try:
        from . import writer
        import json as _j
        for f in writer.BANK.glob("*.json"):
            b = f.name.split("_", 1)[0]
            if b == "pahadi":
                continue
            try:
                d = _j.loads(f.read_text())
            except Exception:
                continue
            txt = " ".join([d.get("title", ""), d.get("description", "")] + [s.get("show", "") for s in d.get("scenes") or []])
            if BLOCK_RX.search(txt):
                f.unlink(missing_ok=True)
                n += 1
    except Exception as e:
        log(f"qplan cleanup bank: {e}")
    try:
        from . import qbank
        bank = qbank._load() if hasattr(qbank, "_load") else None
        if isinstance(bank, dict):
            ch = False
            for cat, items in bank.items():
                if cat.startswith("pahadi") or not isinstance(items, list):
                    continue
                keep = [x for x in items if not (isinstance(x, dict) and BLOCK_RX.search(str(x.get("q", "")) + " " + " ".join(map(str, x.get("o") or x.get("options") or []))))]
                if len(keep) != len(items):
                    n += len(items) - len(keep)
                    bank[cat] = keep
                    ch = True
            if ch and hasattr(qbank, "_save"):
                qbank._save(bank)
    except Exception as e:
        log(f"qplan cleanup qbank: {e}")
    state.put("qplan_clean", {"t": str(datetime.date.today()), "n": n})
    return n


def week_text():
    L = ["🗓 SAWAL KA HAFTE-WAR SCHEDULE " + ("(chalu - default)" if is_on() else "(BAND)")]
    for b, v in BRANDS.items():
        times = ", ".join(sorted(x.strip() for x in str(SCHEDULE.get(b, "")).split(",") if x.strip()))
        L.append(f"\n{v['name']} ({times}):")
        plan = (state.get("qplan_custom") or {}).get(b) or PLAN[b]
        for i, (a, c) in enumerate(plan):
            L.append(f"  {DAYS[i]}: {NAME.get(a, a)} | {NAME.get(c, c)}")
    sw = state.get("qplan_swaps") or {}
    if any(sw.values()):
        L.append("\n🧠 Views ke hisaab se badle: " + "; ".join(f"{BRANDS[b]['name']}: {NAME.get(o, o)} -> {NAME.get(n, n)}"
                                                          for b, m in sw.items() if b in BRANDS for o, n in m.items()))
    L.append("\nNiyam: 3 aam channel par SIP/FD/RD/loan-app sawal nahi; ek channel ka sawal doosre par nahi; pichhle 4 din ka "
             "saancha nahi; har reel ka sawal puchhne ka andaaz + rang alag. Badalna: 'sawal plan band' / 'sawal plan chalu'.")
    return "\n".join(L)
