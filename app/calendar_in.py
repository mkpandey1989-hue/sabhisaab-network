"""Tyohaar / jayanti / khaas din: Google Search se PAKKI tarikh (panchang tithi + muhurat), 3 jaanch ke baad hi post.
Sab dharm, sab kshetra (Hindu, Muslim, Sikh, Isai, Jain, Bauddh, Bengali, Punjabi, Uttarakhandi, rashtriya, antarrashtriya),
naya mahina (Hindi maas aur English), naya saal. Sirf respectful shubhkamna/jaankari; vivaad, rajneeti, dharm-tulna kabhi nahi."""
import datetime
import json
import re
from . import state, tg, diary
from .brain import ask_grounded, ask_gemini, _json
from .config import BRANDS, IST, SITE
from .log import log

FIND = """Today is {today} (India, IST). Using Google Search, list ALL notable observances in India on {day}:
Hindu festivals/vrat/jayanti (with tithi per Drik Panchang) - include ALL vrat like Karwa Chauth, Ahoi Ashtami,
Ekadashi, Pradosh, Purnima, Amavasya, Sankranti, Chaturthi, Navratri days - Muslim, Sikh (gurpurab), Christian, Jain, Buddhist,
regional (Bengali, Punjabi, Uttarakhand, South Indian, Marathi, Gujarati etc.), national days, important international
days, and the start of a new Hindu month (maas) or English month/new year.
ONLY events actually observed on {day}. If observance differs by region/panchang (some today, some tomorrow), say so.
For Hindu festivals give tithi start/end time in IST and the main muhurat (puja/snan) time if well known.
Return ONLY JSON: {{"events": [{{"name_hi": "हिन्दी नाम", "name_en": "...", "community": "...", "major": true/false,
"tithi": "...", "muhurat": "...", "differs": "" or "short note on aaj/kal confusion", "note": "1 line what it is"}}]}}"""

VERIFY = """Verify with Google Search: Is "{name}" observed on {day} in India in {year}? Check Drik Panchang /
government holiday list / reputed news. Reply ONLY JSON: {{"ok": true/false, "date_found": "YYYY-MM-DD or range",
"muhurat": "...", "differs": "..."}}"""

SAFE = """You are the legal + social-harmony auditor of a Hindi media company that respects ALL communities.
Event: {ev}. Is a short respectful greeting/info story about it safe (no politics, no controversy, no religious
comparison, not a death/tragedy anniversary that needs care)? Then write the story text in Hindi (max 220 chars):
greeting + 1 useful fact (tithi/muhurat if given, else meaning). If aaj/kal differs, explain gently that panchang ke
anusaar kuch jagah aaj aur kuch jagah kal manaya ja raha hai. No brand promotion, no hashtags.
Also suggest one helpful, respectful video topic for our brands linked to this day (e.g. festival budget/shopping
savings for deals, money tips for money, tradition/info for pahadi, a clean family story for sunonatak) or "" if unsuitable.
Return ONLY JSON: {{"safe": true/false, "why": "...", "text": "...", "brand": "sunonatak|money|deals|pahadi|all",
"video_brand": "sunonatak|money|deals|pahadi|", "video_topic": "max 60 chars Hindi/Hinglish or empty"}}"""


def _find(day):
    txt, src = ask_grounded(FIND.format(today=datetime.date.today(), day=day))
    return _json(txt).get("events", []), src


def build(day):
    """3 jaanch: (1) Google search se list (2) har event ki alag search se tarikh pakki (3) samaj/kanoon audit."""
    try:
        evs, src = _find(day)
    except Exception as e:
        log(f"calendar find {day}: {e}")
        tg.alert("yellow", f"📅 {day} ke tyohaar Google search se nahi mil paaye ({str(e)[:80]}). Agli baar phir koshish.")
        state.update("cal_fail", lambda d: {**(d or {}), day: 1}, {})
        return None
    out = []
    for e in evs[:12]:
        name = e.get("name_en") or e.get("name_hi")
        try:
            vtxt, vsrc = ask_grounded(VERIFY.format(name=name, day=day, year=day[:4]))
            v = _json(vtxt)
        except Exception as ex:
            log(f"verify {name}: {ex}")
            continue
        if not v.get("ok") or day not in str(v.get("date_found", "")) and not e.get("differs"):
            log(f"calendar: {name} {day} pakka nahi ({v.get('date_found')}) - chhoda")
            continue
        try:
            a = ask_gemini(SAFE.format(ev=json.dumps({**e, **{k: v.get(k) for k in ("muhurat", "differs") if v.get(k)}},
                                                     ensure_ascii=False)), temperature=0.3)
        except Exception as ex:
            log(f"safe {name}: {ex}")
            continue
        if not a.get("safe") or not a.get("text"):
            diary.add("setting", f"event chhoda (audit): {name} - {a.get('why', '')[:80]}")
            continue
        out.append({**e, "muhurat": v.get("muhurat") or e.get("muhurat", ""), "differs": v.get("differs") or e.get("differs", ""),
                    "text": a["text"], "brand": a.get("brand", "all"), "sources": (src + vsrc)[:4]})
        vb, vt = a.get("video_brand"), (a.get("video_topic") or "").strip()
        if e.get("major") and vb in BRANDS and vt:        # bade din par us brand ki video usi vishay par (plan mein)
            plan = state.get("plan") or {}
            if not plan.get(day, {}).get(vb):
                plan.setdefault(day, {})[vb] = vt
                state.put("plan", plan)
                diary.add("setting", f"event video plan: {day} {vb}: {vt}")
    cal = state.get("calendar") or {}
    cal[day] = out
    keep = str(datetime.date.today() - datetime.timedelta(days=3))
    state.put("calendar", {d: v for d, v in cal.items() if d >= keep})
    return out


def refresh():
    """Raat 00:02 (tarikh badalte hi): aaj/kal/parso - jo din pehle se pakka ho chuka use dobara nahi (Gemini bachat)."""
    today = datetime.datetime.now(IST).date()
    cal = state.get("calendar") or {}
    res = {}
    for i in range(7):                       # 7 din pehle se taiyari
        d = str(today + datetime.timedelta(days=i))
        if d in cal and cal[d] is not None and i > 0:
            continue
        if d in cal and i == 0 and state.get("cal_rechecked") == d:
            continue
        r_ = build(d)
        if r_ is None:
            continue
        res[d] = r_
        if i == 0:
            state.put("cal_rechecked", d)
    return res


TITHI = """Using Google Search (Drik Panchang), for {day} in India (IST) give: Hindu tithi with paksha, Hindu month
(maas, purnimant), vikram samvat, and sunrise-based day name. Return ONLY JSON:
{{"tithi": "...", "paksha": "...", "maas": "...", "samvat": "...", "vaar": "..."}}"""


def tithi(day=None):
    day = day or str(datetime.datetime.now(IST).date())
    cache = state.get("tithi") or {}
    if day in cache:
        return cache[day]
    try:
        txt, _ = ask_grounded(TITHI.format(day=day))
        t = _json(txt)
        cache[day] = t
        state.put("tithi", dict(list(cache.items())[-30:]))
        return t
    except Exception as e:
        log(f"tithi: {e}")
        return {}


def today_text(day=None):
    day = day or str(datetime.datetime.now(IST).date())
    t = tithi(day)
    head = (f"🗓 {day} | {t.get('vaar', '')} | {t.get('maas', '')} {t.get('paksha', '')} {t.get('tithi', '')} "
            f"| Vikram Samvat {t.get('samvat', '')}\n") if t else ""
    evs = (state.get("calendar") or {}).get(day, []) or []
    if not evs:
        return head + f"📅 {day}: koi pakka (verify kiya) khaas din nahi mila."
    return head + _today_list(day, evs)


def _today_list(day, evs):
    return f"📅 {day} ke pakke khaas din:\n" + "\n".join(
        f"• {e.get('name_hi') or e.get('name_en')} ({e.get('community', '')})" + (f" | मुहूर्त: {e['muhurat']}" if e.get("muhurat") else "")
        + (f"\n   ⚠️ {e['differs']}" if e.get("differs") else "") for e in evs)


def post_today():
    """Event wale din apne aap story + Telegram post (aaj/kal ka bhed ho to dono din)."""
    from .growth import greet_post
    day = str(datetime.datetime.now(IST).date())
    yday = str(datetime.datetime.now(IST).date() - datetime.timedelta(days=1))
    cal = state.get("calendar") or {}
    done = state.get("greet_done") or {}
    items = [(day, e) for e in (cal.get(day) or [])]
    items += [(yday, e) for e in (cal.get(yday) or []) if e.get("differs")]      # kal wala bhed: aaj bhi
    for d, e in items:
        key = f"{day}:{(e.get('name_en') or e.get('name_hi'))[:40]}"
        if done.get(key):
            continue
        done[key] = 1
        state.put("greet_done", {k: v for k, v in done.items() if k[:10] >= yday})
        brands = list(BRANDS) if e.get("brand") == "all" or e.get("major") else [e.get("brand") if e.get("brand") in BRANDS else "sunonatak"]
        m = re.search(r"(\d{1,2})[:.](\d{2})", e.get("muhurat") or "")
        if m and d == day:              # muhurat ke samay ek aur story ("abhi shubh muhurat")
            at = datetime.datetime.now(IST).replace(hour=int(m.group(1)) % 24, minute=int(m.group(2)), second=0, microsecond=0)
            if at > datetime.datetime.now(IST):
                state.update("muhurat_q", lambda q, at=at, e=e, brands=brands: (q or []) + [
                    {"at": at.isoformat(), "event": {**e, "text": f"🪔 अभी शुभ मुहूर्त: {e.get('name_hi') or e.get('name_en')} "
                                                                  f"({e.get('muhurat')}). {e['text'][:120]}"}, "brands": brands}], [])
        try:
            r = greet_post(e, brands)
            tg.alert("green", f"🙏 Auto story/post: {e.get('name_hi') or e.get('name_en')} -> {r}")
        except Exception as ex:
            tg.alert("yellow", f"Tyohaar post nahi gayi ({e.get('name_en')}): {str(ex)[:150]}")



def muhurat_tick(run):
    q = state.get("muhurat_q") or []
    now = datetime.datetime.now(IST)
    due = [x for x in q if datetime.datetime.fromisoformat(x["at"]) <= now]
    if not due:
        return
    state.put("muhurat_q", [x for x in q if x not in due and datetime.datetime.fromisoformat(x["at"]) > now - datetime.timedelta(hours=6)])
    from .growth import greet_post
    for x in due:
        if now - datetime.datetime.fromisoformat(x["at"]) < datetime.timedelta(hours=2):
            run(lambda x=x: tg.alert("green", "🪔 Muhurat story: " + greet_post(x["event"], x["brands"])))
