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
    from . import indiacal
    try:
        evs, src = _find(day)
    except Exception as e:
        log(f"calendar find {day}: {e}")
        # v2.1.7: Google-search Gemini fail = pehle din khaali. Ab apna pakka calendar (rashtriya din + Diwali-Chhath 2026)
        out = indiacal.events(day) or offline_events_for_day(day)     # v2.3.0: pakki tarikh wale din bhi
        out += [x for x in pahadi_small_events(day) if x["name_hi"] not in {y.get("name_hi") for y in out}]   # v2.3.6
        _plan_videos(day, out)
        cal = state.get("calendar") or {}
        cal[day] = out
        state.update("cal_offline_days", lambda L: sorted(set((L or []) + [day]))[-30:], [])    # Google mile to dobara
        keep = str(datetime.date.today() - datetime.timedelta(days=3))
        state.put("calendar", {d: v for d, v in cal.items() if d >= keep})
        return out
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
    have = {(x.get("name_en") or "").lower()[:12] for x in out}
    for x in indiacal.events(day) + pahadi_small_events(day):   # v2.1.7/2.3.6: apne calendar + pahad ke chhote parv
        if (x["name_en"] or "").lower()[:12] not in have:
            out.append(x)
    state.update("cal_offline_days", lambda L: [d for d in (L or []) if d != day], [])
    _plan_videos(day, [x for x in out if x.get("sources") == ["built-in calendar"]])
    cal = state.get("calendar") or {}
    cal[day] = out
    keep = str(datetime.date.today() - datetime.timedelta(days=3))
    state.put("calendar", {d: v for d, v in cal.items() if d >= keep})
    return out


def _plan_videos(day, evs):
    """Bade din par us brand ki video usi vishay par (roz ke plan mein) - pehle se plan ho to nahi chhedta."""
    plan = state.get("plan") or {}
    for e in evs:
        b, vt = e.get("brand"), (e.get("video_topic") or "").strip()
        if not (e.get("major") and vt):
            continue
        b = b if b in BRANDS else ("money" if b == "all" else "sunonatak")
        if not plan.get(day, {}).get(b):
            plan.setdefault(day, {})[b] = vt
            diary.add("setting", f"event video plan: {day} {b}: {vt}")
    state.put("plan", plan)


def refresh():
    """Raat 00:02 (tarikh badalte hi): aaj/kal/parso - jo din pehle se pakka ho chuka use dobara nahi (Gemini bachat)."""
    today = datetime.datetime.now(IST).date()
    cal = state.get("calendar") or {}
    res = {}
    offline = set(state.get("cal_offline_days") or [])
    for i in range(7):                       # 7 din pehle se taiyari
        d = str(today + datetime.timedelta(days=i))
        if d in cal and cal[d] is not None and i > 0 and d not in offline:   # v2.3.6: offline bana din Google se dobara
            continue
        if d in cal and i == 0 and state.get("cal_rechecked") == d and d not in offline:
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
        return fast_panchang(day)                 # v2.3.0: Google na mile to offline ganit (khaali nahi)


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


# ---------------- v2.3.0 Step 5 (v11 se, sahi ganit ke saath): offline panchang + kone ka badge ----------------
# v11 ka offline panchang ek 'ausat chandra-maas' aur angrezi mahine se maas maanta tha (aksar galat tithi/maas).
# Yahan Surya-Chandra ki asli sthiti (Meeus ka chhota ganit, ~0.01 degree) se tithi, aur amavasya par Surya ki rashi
# (Lahiri ayanamsha) se maas (purnimant, uttar Bharat). Google wala (ask_grounded) mile to wahi pehle.
import math as _m

_VAAR_HI = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
_TITHI_HI = ["प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी",
             "नवमी", "दशमी", "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी"]
_AMANTA = ["चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ़", "श्रावण", "भाद्रपद", "आश्विन", "कार्तिक", "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"]
# sirf pakki angrezi tarikh wale (chand par nirbhar tyohaar yahan NAHI - unki tarikh Google se pakki hoti hai)
_FIXED_OBSERVANCES = {
    "01-12": ("राष्ट्रीय युवा दिवस (स्वामी विवेकानंद जयंती)", "राष्ट्रीय"),
    "01-23": ("पराक्रम दिवस (नेताजी सुभाष चंद्र बोस जयंती)", "राष्ट्रीय"),
    "01-26": ("गणतंत्र दिवस", "राष्ट्रीय"),
    "02-28": ("राष्ट्रीय विज्ञान दिवस", "राष्ट्रीय"),
    "03-08": ("अंतर्राष्ट्रीय महिला दिवस", "अंतर्राष्ट्रीय"),
    "04-01": ("नया वित्तीय वर्ष", "आर्थिक"),
    "06-05": ("विश्व पर्यावरण दिवस", "अंतर्राष्ट्रीय"),
    "06-21": ("अंतर्राष्ट्रीय योग दिवस", "अंतर्राष्ट्रीय"),
    "08-15": ("स्वतंत्रता दिवस", "राष्ट्रीय"),
    "09-05": ("शिक्षक दिवस", "राष्ट्रीय"),
    "09-14": ("हिंदी दिवस", "राष्ट्रीय"),
    "10-02": ("गांधी व शास्त्री जयंती", "राष्ट्रीय"),
    "11-09": ("उत्तराखंड राज्य स्थापना दिवस", "उत्तराखंड"),
    "12-25": ("सुशासन दिवस", "राष्ट्रीय"),
}


def _jd(dt_utc):
    y, mo = dt_utc.year, dt_utc.month
    d = dt_utc.day + (dt_utc.hour + dt_utc.minute / 60) / 24
    if mo <= 2:
        y, mo = y - 1, mo + 12
    a = y // 100
    return int(365.25 * (y + 4716)) + int(30.6001 * (mo + 1)) + d + 2 - a + a // 4 - 1524.5


def _sun_moon(jd):
    t = (jd - 2451545.0) / 36525
    r = _m.radians
    l0 = 280.46646 + 36000.76983 * t
    ms = 357.52911 + 35999.05029 * t
    c = (1.914602 - 0.004817 * t) * _m.sin(r(ms)) + 0.019993 * _m.sin(r(2 * ms)) + 0.000289 * _m.sin(r(3 * ms))
    sun = (l0 + c - 0.00569 - 0.00478 * _m.sin(r(125.04 - 1934.136 * t))) % 360
    lp = 218.3164477 + 481267.88123421 * t
    dd = 297.8501921 + 445267.1114034 * t
    mp = 134.9633964 + 477198.8675055 * t
    f = 93.2720950 + 483202.0175233 * t
    terms = [(6288774, 0, 0, 1, 0), (1274027, 2, 0, -1, 0), (658314, 2, 0, 0, 0), (213618, 0, 0, 2, 0),
             (-185116, 0, 1, 0, 0), (-114332, 0, 0, 0, 2), (58793, 2, 0, -2, 0), (57066, 2, -1, -1, 0),
             (53322, 2, 0, 1, 0), (45758, 2, -1, 0, 0), (-40923, 0, 1, -1, 0), (-34720, 1, 0, 0, 0),
             (-30383, 0, 1, 1, 0), (15327, 2, 0, 0, -2), (-12528, 0, 0, 1, 2), (10980, 0, 0, 1, -2),
             (10675, 4, 0, -1, 0), (10034, 0, 0, 3, 0), (8548, 4, 0, -2, 0), (-7888, 2, 1, -1, 0),
             (-6766, 2, 1, 0, 0), (-5163, 1, 0, -1, 0), (4987, 1, 1, 0, 0), (4036, 2, -1, 1, 0)]
    sl = sum(k * _m.sin(r(a * dd + b * ms + cc * mp + e * f)) for k, a, b, cc, e in terms)
    moon = (lp + sl / 1e6) % 360
    return sun, moon


def _elong(jd):
    s, mo = _sun_moon(jd)
    return (mo - s) % 360, s


def fast_panchang(day_str=None):
    """Offline (bina internet) panchang: tithi + paksha (suryoday ~6:30 IST par), maas (purnimant), samvat, vaar."""
    d = datetime.date.fromisoformat(day_str) if day_str else datetime.datetime.now(IST).date()
    jd = _jd(datetime.datetime(d.year, d.month, d.day, 1, 0))          # 06:30 IST = 01:00 UTC
    el, _ = _elong(jd)
    idx = int(el // 12)                                                  # 0..29
    shukla = idx < 15
    tithi_name = "पूर्णिमा" if idx == 14 else ("अमावस्या" if idx == 29 else _TITHI_HI[idx % 15])
    # pichhli amavasya dhoondo (elongation 0) -> us samay Surya ki sidereal rashi -> amanta maas
    jn = jd - el / 12.19
    for _ in range(8):
        e2, _s = _elong(jn)
        if e2 > 180:
            e2 -= 360
        jn -= e2 / 12.19
    _e, s_trop = _elong(jn)
    ayan = 23.853 + (d.year - 2000) * 0.013969
    rashi = int(((s_trop - ayan) % 360) // 30)                            # 0 = Mesh
    amanta_i = (rashi + 1) % 12                                          # Meen(11)->Chaitra(0), Mesh(0)->Vaishakh(1)
    maas_i = amanta_i if shukla else (amanta_i + 1) % 12                 # purnimant: krishna paksha agla maas
    samvat = d.year + (56 if (d.month <= 4 and amanta_i in (9, 10, 11)) else 57)   # nav-varsh = amanta Chaitra shuru
    return {"tithi": tithi_name, "paksha": "शुक्ल पक्ष" if shukla else "कृष्ण पक्ष", "maas": _AMANTA[maas_i],
            "samvat": str(samvat), "vaar": _VAAR_HI[d.weekday()], "source": "offline ganit"}


def badge_line(day_str=None):
    """Video ke kone ka 1-line badge: Google se pakka tithi (cache) pehle, warna offline ganit."""
    day_str = day_str or str(datetime.datetime.now(IST).date())
    t = (state.get("tithi") or {}).get(day_str) or fast_panchang(day_str)
    evs = (state.get("calendar") or {}).get(day_str) or []
    ev = ""
    if evs:
        ev = (evs[0].get("name_hi") or evs[0].get("name_en") or "")[:16]
    elif day_str[5:] in _FIXED_OBSERVANCES:
        ev = _FIXED_OBSERVANCES[day_str[5:]][0][:16]
    return (f"{t.get('maas', '')} · {t.get('paksha', '')} {t.get('tithi', '')}" + (f" | {ev}" if ev else "")).strip(" ·|")


def offline_events_for_day(day):
    """Google (ask_grounded) seema par: sirf pakki angrezi tarikh wale din (chand wale tyohaar ka anumaan kabhi post nahi)."""
    mmdd = day[5:]
    if mmdd not in _FIXED_OBSERVANCES:
        return []
    nm, comm = _FIXED_OBSERVANCES[mmdd]
    p = fast_panchang(day)
    return [{"name_hi": nm, "name_en": nm, "community": comm, "major": True,
             "tithi": f"{p['maas']} {p['paksha']} {p['tithi']}", "muhurat": "", "differs": "",
             "text": f"{nm} की हार्दिक शुभकामनाएँ!", "brand": "pahadi" if "उत्तराखंड" in comm else ("money" if "आर्थिक" in comm else "all"),
             "sources": ["pakki tarikh (offline)"]}]



# ---------------- v2.3.6: pahad ke chhote-bade parv (bina Google, ganit se) - Pahadi Hisaab par roz kuch na kuch ----------------
_SANK = {9: ("मकर संक्रांति / उत्तरायणी", "Makar Sankranti / Uttarayani", True),
         11: ("फूलदेई (चैत्र संक्रांति)", "Phool Dei", True),
         0: ("बिखौती / बैसाखी (मेष संक्रांति)", "Bikhauti / Baisakhi", True),
         3: ("हरेला (श्रावण संक्रांति)", "Harela", True),
         4: ("घी संक्रांति (ओलगिया)", "Ghee Sankranti (Olgia)", True),
         5: ("खतड़ुआ (आश्विन संक्रांति)", "Khatarua", True)}
_RASHI = ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या", "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"]


def _sid_rashi(dt_utc):
    s_, _m_ = _sun_moon(_jd(dt_utc))
    ayan = 23.853 + (dt_utc.year - 2000) * 0.013969
    return int(((s_ - ayan) % 360) // 30)


def pahadi_small_events(day):
    """Sankranti (Surya ka rashi badalna - pahad ke Harela, Phooldei, Ghee Sankranti, Uttarayani, Khatarua, Bikhauti),
    Purnima, Amavasya, Ekadashi, Igas Bagwal (Kartik Shukla Ekadashi). Tithi suryoday wali (offline ganit)."""
    d = datetime.date.fromisoformat(day)
    out = []
    note = "पंचांग के अनुसार कुछ जगह यह एक दिन आगे-पीछे मनाया जाता है।"
    try:
        r0 = _sid_rashi(datetime.datetime(d.year, d.month, d.day, 0, 0) - datetime.timedelta(hours=5, minutes=30))
        r1 = _sid_rashi(datetime.datetime(d.year, d.month, d.day, 0, 0) + datetime.timedelta(hours=18, minutes=30))
        if r0 != r1:
            hi, en, major = _SANK.get(r1, (f"{_RASHI[r1]} संक्रांति", f"{_RASHI[r1]} Sankranti", False))
            out.append({"name_hi": hi, "name_en": en, "community": "uttarakhand", "major": major, "brand": "pahadi",
                        "text": f"{hi} की हार्दिक शुभकामनाएँ! {note}", "muhurat": "", "differs": note,
                        "video_topic": f"{en}: pahad ki parampara" if major else "", "sources": ["offline ganit"]})
        p = fast_panchang(day)
        t, pk, maas = p["tithi"], p["paksha"], p["maas"]
        if maas == "कार्तिक" and "शुक्ल" in pk and t == "एकादशी":
            out.append({"name_hi": "इगास बग्वाल / देवउठनी एकादशी", "name_en": "Igas Bagwal", "community": "uttarakhand", "major": True,
                        "brand": "pahadi", "text": "इगास बग्वाल (पहाड़ की दिवाली) की हार्दिक शुभकामनाएँ! भैलो खेलें, परंपरा निभाएँ। " + note,
                        "muhurat": "", "differs": note, "video_topic": "Igas Bagwal: pahad ki diwali", "sources": ["offline ganit"]})
        elif t in ("पूर्णिमा", "अमावस्या", "एकादशी"):
            nm = f"{maas} {t if t != 'एकादशी' else pk.split()[0] + ' एकादशी'}"
            out.append({"name_hi": nm, "name_en": nm, "community": "hindu", "major": False, "brand": "pahadi",
                        "text": f"आज {nm} है। {note}", "muhurat": "", "differs": note, "video_topic": "", "sources": ["offline ganit"]})
    except Exception as e:
        log(f"pahadi_small_events {day}: {e}")
    return out
