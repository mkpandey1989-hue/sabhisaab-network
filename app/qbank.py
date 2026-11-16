"""v2.3.5 (owner 4 Nov): ANANT SAWAL-BANK - har category ke naye sawal roz apne aap (Gemini likhe -> Google se jaanch -> bank).
Koi sawal kisi bhi channel par dobara nahi (puzzles.used_puzzle_hashes + pipeline.q_registry dono se jaanch).
Trend: seo trends / khabar ke shabd se 'aaj log kya dhoondh rahe' -> us vishay ka PAKKA (na badalne wala) tathya ka sawal.
Gemini seema khatam -> kuch nahi tootta: static bank + ganit wale sawal + spare reel chalte rahte hain."""
import datetime
import json
import random

from . import state
from .config import DATA, BRANDS
from .log import log

FILE = DATA / "qbank.json"
LOW = 10            # isse kam bache to naye
PER_CALL = 8

CATS = {
    "utpate_shabd": ("Hindi ke aise shabd ya muhavre jinka arth aasaan lagta hai par zyadatar log galat batate hain "
                     "(ghumaavdaar, confusion wale). Arth bilkul pakka ho.", ["sunonatak", "deals"]),
    "purane_shabd": ("Purane zamaane ke anokhe shabd: purane sikke, naap-tol, samay ki ikaaiyan, gharelu cheezon ke purane naam "
                     "(pakke, kitaabon mein likhe arth).", ["money", "sunonatak"]),
    "shuddh_hindi": ("Roz ki angrezi cheezon ke prachalit, sahi Hindi naam (sarkari/shabdkosh wale; mazaak wale gadhe hue nahi).",
                     ["sunonatak"]),
    "pahadi_purana": ("Uttarakhand (Garhwal-Kumaon) ke purane zamaane ke ghar, saamaan, gehne, kapde, baaje, rasmon ke pahadi naam.",
                      ["pahadi"]),
    "pahadi_shabd": ("Garhwali/Kumaoni boli ke rozmarra shabd aur unka pakka Hindi arth.", ["pahadi"]),
    "pahadi_gk": ("Uttarakhand GK - sirf pakke, na badalne wale tathya (bhugol, itihaas, sanskriti, rajya pratik).", ["pahadi"]),
    "ego_sawal": ("Aise aasaan dikhne wale sawal jinhe log 'mujhe pata hai' soch kar jaldi mein galat karte hain - ganit, tark, "
                  "bhasha ya GK (jawab tark/tathya se ek hi).", ["sunonatak", "money", "deals"]),
    "dimag_trend": ("2026 mein chal rahi nayi dimag hilane wali pahelinyan (logic, ulta sochna, shabdon ka khel) - jawab tark se "
                    "pakka aur ek hi.", ["sunonatak", "deals", "money"]),
    "trend_gk": ("Aaj log jo dhoondh rahe (TREND shabd niche) usse juda koi PAKKA, purana, na badalne wala tathya - khabar ya "
                 "taaza ghatna ka sawal NAHI.", ["sunonatak", "money", "deals"]),
    "money_quiz": ("Paise/bachat/byaj/EMI/tax ke aasaan par ghumaavdaar ganit wale sawal (jawab ganit se pakka).", ["money"]),
    "deals_quiz": ("Discount, offer, cashback, bill, daam ke ghumaavdaar ganit wale sawal (jawab ganit se pakka).", ["deals"]),
}
DYN_ONLY = ("ego_sawal", "dimag_trend", "trend_gk", "money_quiz", "deals_quiz")
LABEL = {"ego_sawal": "Ego Test (Socho Phir Bolo)", "dimag_trend": "Dimag Hilao (Trending Paheli)", "trend_gk": "Trending GK",
         "money_quiz": "Paise ka Dimagi Sawal", "deals_quiz": "Deal ka Dimagi Ganit", "utpate_shabd": "Ulte-pulte shabd",
         "purane_shabd": "Purane zamaane ke shabd", "shuddh_hindi": "Shuddh Hindi naam", "pahadi_purana": "Pahad ke purane naam",
         "pahadi_shabd": "Pahadi boli", "pahadi_gk": "Pahadi GK"}

PROMPT = """Write {n} NEW multiple-choice quiz questions in Hindi (Devanagari) for an Indian family-friendly short-video channel.
Category: {hint}
{trend}
Rules: each question short (max 90 characters); exactly 4 short options (max 26 characters each, all different);
exactly ONE correct answer which must be copied exactly as one of the options; a 1-line explanation (max 90 characters);
facts must be well-established and checkable (no news, no opinions, no made-up statistics, no 'X% log' claims);
nothing political/religious-controversial/adult; never repeat or rephrase any of these existing questions:
{seen}
Return ONLY JSON: {{"items":[{{"q":"...","options":["...","...","...","..."],"answer":"...","exp":"..."}}]}}"""

VERIFY = """You are a strict fact-checker. For each numbered quiz item, use Google Search and decide if the given ANSWER is
correct AND the only correct option among the options (unambiguous). Return ONLY JSON: {{"results":[{{"i":1,"ok":true}}]}}
{items}"""


def _load():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(d):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(FILE)


def _used(q):
    from .puzzles import _hash, _strip_code
    from .pipeline import q_seen
    return _hash(_strip_code(q)) in set(state.get("used_puzzle_hashes") or []) or q_seen(q)


def available(cat):
    return [it for it in _load().get(cat, []) if not _used(it["q"])]


def take(cat, rnd=None):
    """Bank se ek naya (kabhi na gaya) sawal -> item ya None."""
    pool = available(cat)
    if not pool:
        return None
    it = (rnd or random).choice(pool)
    return {"q": it["q"], "ans": it["ans"], "opts": list(it["opts"]), "exp": it.get("exp", ""), "name": LABEL.get(cat, "")}


def _trend_words():
    words = []
    try:
        from . import seo
        for b in BRANDS:
            words += [t for t in seo.trends(b)][:4]
    except Exception:
        pass
    return words[:12]


def _items(res, key):
    """v2.6.0: Gemini ka JSON kabhi {key: [...]} aur kabhi seedha [...] hota hai - dono sambhalo."""
    if isinstance(res, list):
        return res
    if isinstance(res, dict):
        v = res.get(key)
        return v if isinstance(v, list) else []
    return []


def fill(cat, n=PER_CALL):
    """Ek category ke naye sawal: Gemini -> filter -> Google jaanch -> bank. -> kitne jude"""
    from .brain import ask_gemini, ask_grounded, _json
    hint = CATS[cat][0]
    d = _load()
    have = d.get(cat, [])
    seen = [it["q"] for it in have][-40:] + list(state.get("q_recent") or [])[-30:]
    trend = ""
    if cat == "trend_gk":
        tw = _trend_words()
        if not tw:
            return 0
        trend = "TREND (log abhi ye dhoondh rahe): " + ", ".join(tw)
    try:
        res = ask_gemini(PROMPT.format(n=n, hint=hint, trend=trend, seen="\n".join("- " + x for x in seen[-60:]) or "-"),
                         temperature=0.8)
    except Exception as e:
        log(f"qbank {cat}: {e}")
        return 0
    cand = []
    for x in (_items(res, "items"))[:n]:
        if not isinstance(x, dict):                  # v2.6.0: Gemini kabhi list/string deta tha -> 'list' has no .get
            continue
        q, ops, ans = str(x.get("q", "")).strip(), [str(o).strip() for o in (x.get("options") or [])], str(x.get("answer", "")).strip()
        if not q or len(ops) != 4 or len(set(ops)) != 4 or ans not in ops or len(q) > 140:
            continue
        if _used(q) or any(q == h["q"] for h in have) or any(q == c_["q"] for c_ in cand):
            continue
        import re
        if re.search(r"\d{2}\s*%\s*(लोग|log|लोगों)|सेक्सी|अश्लील", q + " ".join(ops)):
            continue
        cand.append({"q": q, "ans": ans, "opts": ops, "exp": str(x.get("exp", ""))[:120]})
    if not cand:
        return 0
    okset, how = None, "google"
    try:                                              # 1) Google se jaanch - galat/do-arthi sawal bank mein nahi
        txt, _src = ask_grounded(VERIFY.format(items="\n".join(
            f"{i + 1}. Q: {c_['q']} | options: {c_['opts']} | ANSWER: {c_['ans']}" for i, c_ in enumerate(cand))))
        okset = {int(r.get("i", 0)) for r in _items(_json(txt), "results") if isinstance(r, dict) and r.get("ok") is True}
    except Exception as e:
        log(f"qbank verify {cat} (google band): {str(e)[:120]}")
    if okset is None:                                 # 2) v2.3.6: Google seema khatam -> do-dimaag 'andha hal' (jawab bataye bina)
        okset, how = _blind_verify(cand, strict=cat in ("pahadi_gk", "trend_gk")), "do-dimaag"
        if not okset:
            state.put("qbank_last_err", {"t": str(datetime.datetime.now())[:16], "cat": cat, "err": "jaanch nahi ho payi"})
            return 0
    good = [dict(c_, t=str(datetime.date.today()), verified=how) for i, c_ in enumerate(cand) if (i + 1) in okset]
    if good:
        d.setdefault(cat, []).extend(good)
        d[cat] = d[cat][-400:]
        _save(d)
        state.update("qbank_added", lambda m: {**(m or {}), cat: (m or {}).get(cat, 0) + len(good)}, {})
    return len(good)


BLIND = """Solve each multiple-choice question yourself. Do not guess wildly: if a question is ambiguous or you are not sure,
answer "?". Return ONLY JSON: {{"answers":[{{"i":1,"a":"<exact option text or ?>"}}]}}
{items}"""


def _blind_solve(fn, cand):
    import random as _r
    items = []
    for i, c_ in enumerate(cand):
        ops = list(c_["opts"])
        _r.shuffle(ops)
        items.append(f"{i + 1}. {c_['q']} | options: {ops}")
    res = fn(BLIND.format(items="\n".join(items)), temperature=0.0)
    if isinstance(res, str):
        from .brain import _json
        res = _json(res)
    return {int(a.get("i", 0)): str(a.get("a", "")).strip() for a in _items(res, "answers") if isinstance(a, dict)}


def _blind_verify(cand, strict=False):
    """Do alag dimaag (Cloudflare Workers AI + Gemini, jo chale) bina jawab dekhe hal karein; dono/ek ka jawab wahi ho tabhi.
    strict (GK tathya) = do dimaag zaroori."""
    from . import brain
    votes = []
    for fn in (brain.ask_cf, brain.ask_gemini):
        try:
            votes.append(_blind_solve(fn, cand))
        except Exception as e:
            log(f"qbank blind: {str(e)[:100]}")
    need = 2 if strict else 1
    if len(votes) < need:
        return set()
    ok = set()
    for i, c_ in enumerate(cand):
        agree = sum(1 for v in votes if v.get(i + 1) == c_["ans"])
        wrong = sum(1 for v in votes if v.get(i + 1) not in (c_["ans"], "?", None, ""))
        if agree >= need and wrong == 0:
            ok.add(i + 1)
    return ok


def fill_all(max_cats=6):
    """Raat/dopahar: sabse khaali category pehle (har baar max 6, Gemini seema bachane ke liye)."""
    order = sorted(CATS, key=lambda c: len(available(c)))
    out = []
    for cat in order[:max_cats]:
        if len(available(cat)) >= LOW:
            continue
        k = fill(cat)
        out.append(f"{cat}+{k}")
    if out:
        log("qbank: " + ", ".join(out))
    return out


def status_text():
    lines = ["🏦 ANANT SAWAL-BANK (Gemini likhe → Google jaanch → bank; koi sawal kisi channel par dobara nahi)"]
    for cat in CATS:
        lines.append(f"• {LABEL.get(cat, cat)}: {len(available(cat))} taiyaar | ab tak jude {(state.get('qbank_added') or {}).get(cat, 0)}")
    le = state.get("qbank_last_err") or {}
    if le:
        lines.append(f"⚠ Aakhri dikkat: {le.get('t')} {le.get('cat')} - {le.get('err')} (Gemini/Google seema; bot khud dobara koshish karega)")
    lines.append("Apne aap: roz 01:20, 14:20 + har 3 ghante khaali category. Aapko kuch likhna nahi hai.")
    return "\n".join(lines)
