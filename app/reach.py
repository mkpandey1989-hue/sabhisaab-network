"""v3.4.24 (18 Nov 2026, owner: "naya page nahi - baaki advance kaam sab bana do, fully automatic").

Koi naya website page NAHI banta. Sirf bahar se log laana + samajhna ki kaun kitna rukta hai.

1) FB PAGE LINK-CARD: sawal wali reel ke ~3 ghante baad usi brand ke FB page par ek link post (sawal + 4 vikalp + /jawab ka
   link, Facebook khud card banata hai - poora card clickable). Har brand din mein MAX 2, sirf 09:00-21:30. Engagement-bait
   ('tag karo / share karo / comment YES') kabhi nahi - Meta niti.
2) MAUKA CALENDAR: saal ke pakke mauke (salary ka hafta, advance tax kisht 15 Jun/Sep/Dec/Mar, ITR mausam, naya FY, festive sale,
   school admission, result, Char Dham yatra, garmi ka bijli bill...) par juda calculator - Telegram channel + FB page (cap ke
   andar). Roz max 1, ek hi tool 10 din mein dobara nahi. Text page ka APNA description (bot naya daawa nahi likhta).
3) FUNNEL (platform-wise rukna): GA4 se har platform: kitne log, kitne % ruke, ausat samay, ek aadmi kitne page. Ravivaar 20:40
   + 'funnel' likhne par. Sabse badi kami ek line mein (sirf ginti se, AI ka andaaza nahi).
4) SAAL JAANCH: 20 Dec ko un page ki suchi jinke title mein abhi ka saal hai (apne aap nahi badalta - tax/budget wale page
   naye budget se pehle badle to galat ho jayenge).
5) 'naye kaam haal': pehle se bane features (quiz poll, push, PageSpeed, YT comment login, quiz bot inline) ka ek jagah haal.

Hukum: 'fb link post band/chalu' | 'mauka band/chalu' | 'funnel' / 'funnel 30' | 'naye kaam haal' | 'saal jaanch'
"""
import datetime
import json
import re
import time

from . import state, tg
from .config import BRANDS, IST, SITE
from .log import log

FB_DELAY = 3 * 3600            # reel ke kitni der baad link post
FB_MAX = 2                     # har brand din mein
FB_FROM, FB_TO = "09:00", "21:30"
MK_HHMM = "10:30"
MK_GAP_DAYS = 10
FN_DAY, FN_HHMM = 6, "20:40"   # Ravivaar

# (shuru MM-DD, ant MM-DD, slug, brand, ek line - sirf pakki/aam baat, tareekh ka daawa wahi jo kanoon mein tay hai)
MAUKA = [
    ("03-10", "03-15", "advance-tax-calculator", "money", "15 मार्च एडवांस टैक्स की आख़िरी किस्त की तारीख़ है - अपना हिसाब पहले देख लें।"),
    ("06-10", "06-15", "advance-tax-calculator", "money", "15 जून एडवांस टैक्स की पहली किस्त की तारीख़ है - अपना हिसाब पहले देख लें।"),
    ("09-10", "09-15", "advance-tax-calculator", "money", "15 सितंबर एडवांस टैक्स की दूसरी किस्त की तारीख़ है - अपना हिसाब पहले देख लें।"),
    ("12-10", "12-15", "advance-tax-calculator", "money", "15 दिसंबर एडवांस टैक्स की तीसरी किस्त की तारीख़ है - अपना हिसाब पहले देख लें।"),
    ("04-01", "04-12", "old-vs-new-tax-regime-calculator", "money", "नया वित्त वर्ष शुरू - पुरानी या नई टैक्स व्यवस्था, किसमें कम टैक्स? हिसाब लगाकर देखें।"),
    ("07-01", "07-24", "income-tax-calculator", "money", "ITR भरने का मौसम है - अपना टैक्स पहले खुद जाँच लें।"),
    ("07-25", "08-10", "itr-late-fee-calculator", "money", "ITR देर से भरने पर लेट फ़ीस और ब्याज कितना? पहले हिसाब देख लें।"),
    ("01-05", "03-05", "section-80c-calculator", "money", "टैक्स बचाने का मौसम - 80C में कितना निवेश बाकी है, हिसाब देखें।"),
    ("02-01", "02-04", "income-tax-calculator", "money", "बजट के बाद अपना टैक्स दोबारा जाँचें।"),
    ("03-20", "04-15", "age-calculator", "sunonatak", "स्कूल एडमिशन का समय - बच्चे की सही उम्र (साल-महीने-दिन) एक टैप में।"),
    ("05-05", "05-31", "marks-percentage-calculator", "sunonatak", "रिज़ल्ट का मौसम - अंक से प्रतिशत तुरंत निकालें।"),
    ("05-05", "05-31", "cbse-best-of-five-calculator", "sunonatak", "CBSE रिज़ल्ट - बेस्ट ऑफ़ फ़ाइव प्रतिशत खुद निकालें।"),
    ("04-15", "05-31", "char-dham-yatra-kharcha-calculator", "pahadi", "चार धाम यात्रा की तैयारी - कुल खर्च का हिसाब पहले लगा लें।"),
    ("05-10", "06-30", "bijli-bill-calculator", "money", "गर्मी में AC-कूलर चल रहे हैं - इस महीने बिजली बिल कितना आएगा, देख लें।"),
    ("10-01", "11-12", "discount-calculator", "deals", "त्योहारी सेल चल रही है - असली छूट कितनी है, खरीदने से पहले हिसाब लगाएँ।"),
    ("10-15", "11-10", "gold-jewellery-price-calculator", "deals", "त्योहार पर गहने ले रहे हैं? मेकिंग चार्ज और GST जोड़कर असली कीमत देखें।"),
    ("12-20", "01-10", "sip-goal-calculator", "money", "नए साल का लक्ष्य - हर महीने कितनी SIP से लक्ष्य पूरा होगा, हिसाब देखें।"),
]
SALARY = ("50-30-20-budget-calculator", "money", "सैलरी आ गई? 50-30-20 नियम से ज़रूरत, शौक और बचत का बँटवारा देखें।")


def _now(now=None):
    return now or datetime.datetime.now(IST)


def _site_dir():
    from . import website
    return website.DIR / "site"


def _page_ok(slug):
    try:
        return (_site_dir() / f"{slug}.html").exists()
    except Exception:
        return False


def _clean_q(q):
    return re.sub(r"[ ]*#\S+", "", str(q or "")).strip()


# ------------------------------------------------------------------ 1) FB page link-card
def _fb_count(brand, day):
    c = state.get("rc_fb") or {}
    return int((c.get("n") or {}).get(brand, 0)) if c.get("day") == day else 0


def _fb_note(brand, day, aid=None):
    def f(c):
        c = c or {}
        if c.get("day") != day:
            c = {"day": day, "n": {}, "done": c.get("done", [])[-200:]}
        c["n"][brand] = int(c["n"].get(brand, 0)) + 1
        if aid:
            c["done"] = (c.get("done") or []) + [str(aid)]
        return c
    state.update("rc_fb", f, {})


def fb_text(e):
    from . import answers
    q = _clean_q(e.get("q"))
    opts = [str(o) for o in (e.get("opts") or [])][:4]
    aid = str(e.get("aid") or e.get("code"))
    link = f"{SITE}{answers.PAGE}?utm_source=facebook&utm_medium=linkpost&utm_campaign={e.get('brand')}&utm_content=c{aid}#c{aid}"
    body = (f"🧩 आज का सवाल ({e.get('bname') or BRANDS.get(e.get('brand'), {}).get('name', '')})\n{q}\n\n"
            + "\n".join(f"{'ABCD'[i]}) {o}" for i, o in enumerate(opts))
            + f"\n\nपहले खुद सोचिए, फिर सही जवाब और तरीका यहाँ देखिए 👇\n{link}")
    return body, link


def fb_post(brand, message, link):
    from . import meta as M
    bi = M.brand_info(brand)
    if not bi:
        raise RuntimeError("FB page juda nahi")
    r = M._post(f"/{bi['page_id']}/feed", bi["page_token"], message=message[:1900], link=link)
    return (r or {}).get("id", "")


def fb_candidates(day):
    from . import answers
    out = []
    done = set((state.get("rc_fb") or {}).get("done") or [])
    for e in reversed(state.get("answer_key") or []):
        if e.get("date") != day:
            continue
        aid = str(e.get("aid") or e.get("code"))
        if aid in done or e.get("brand") not in BRANDS or not answers.tap_ok(e):
            continue
        out.append(e)
    return out


def fb_due(now=None):
    """-> (entry) jo ab post hona chahiye, ya None. 'Pehli baar dekha' samay yahin yaad hota hai."""
    now = _now(now)
    if state.get("rc_fb_off") or state.get("paused"):
        return None
    hm, day = now.strftime("%H:%M"), str(now.date())
    seen = state.get("rc_seen") or {}
    t = time.time()
    changed = False
    pick = None
    for e in fb_candidates(day):
        aid = str(e.get("aid") or e.get("code"))
        if aid not in seen:
            seen[aid] = t
            changed = True
            continue
        if pick is None and t - seen[aid] >= FB_DELAY and FB_FROM <= hm <= FB_TO and _fb_count(e["brand"], day) < FB_MAX:
            tries = (state.get("rc_fb_tries") or {}).get(aid, 0)
            if tries < 2:
                pick = e
    if changed:
        state.put("rc_seen", dict(list(seen.items())[-300:]))
    return pick


def fb_run(e, now=None):
    from . import answers
    day = str(_now(now).date())
    aid = str(e.get("aid") or e.get("code"))
    if not answers.live():
        return None
    msg, link = fb_text(e)
    try:
        pid = fb_post(e["brand"], msg, link)
        _fb_note(e["brand"], day, aid)
        state.update("rc_fb_log", lambda l: ((l or []) + [{"d": day, "t": _now(now).strftime("%H:%M"), "b": e["brand"], "aid": aid,
                                                           "id": pid}])[-60:], [])
        return pid
    except Exception as ex:
        state.update("rc_fb_tries", lambda d: dict(list({**(d or {}), aid: (d or {}).get(aid, 0) + 1}.items())[-100:]), {})
        state.put("rc_fb_err", {"t": _now(now).strftime("%Y-%m-%d %H:%M"), "e": str(ex)[:200]})
        log(f"reach fb: {ex}")
        return None


# ------------------------------------------------------------------ 2) Mauka calendar
def _in(md, a, b):
    return a <= md <= b if a <= b else (md >= a or md <= b)


def mauka_pick(now=None):
    now = _now(now)
    md = now.strftime("%m-%d")
    last = state.get("rc_mk_last") or {}
    cands = [(s, b, ln) for a, z, s, b, ln in MAUKA if _in(md, a, z)]
    if now.day <= 3:
        cands.append(SALARY)
    for s, b, ln in cands:
        if not _page_ok(s):
            continue
        ld = last.get(s)
        if ld:
            try:
                if (now.date() - datetime.date.fromisoformat(ld)).days < MK_GAP_DAYS:
                    continue
            except Exception:
                pass
        return s, b, ln
    return None


def mauka_due(now=None):
    now = _now(now)
    return (not state.get("rc_mk_off") and not state.get("paused") and now.strftime("%H:%M") >= MK_HHMM
            and state.get("rc_mk_day") != str(now.date()))


def mauka_run(now=None, manual=False):
    from .config import TG_CHANNEL
    from . import sharekit
    now = _now(now)
    day = str(now.date())
    if not manual:
        state.put("rc_mk_day", day)
    p = mauka_pick(now)
    if not p:
        return "📅 Aaj koi khaas mauka (calendar) nahi - kuch post nahi kiya."
    slug, brand, line = p
    try:
        html = (_site_dir() / f"{slug}.html").read_text(encoding="utf-8", errors="ignore")
    except Exception:
        html = ""
    title, desc = sharekit.title_desc(html)
    title = title or slug.replace("-", " ")
    tg_link = f"{SITE}/{slug}?utm_source=telegram&utm_medium=mauka&utm_campaign={slug}"
    fb_link = f"{SITE}/{slug}?utm_source=facebook&utm_medium=mauka&utm_campaign={slug}"
    txt = f"📅 {line}\n\n🧮 {title}\n{desc}\n\n👉 {tg_link}"
    out = []
    r = tg.call("sendMessage", {"chat_id": TG_CHANNEL, "text": txt[:3900], "disable_web_page_preview": "false",
                                "reply_markup": json.dumps({"inline_keyboard": [[{"text": "🧮 Free calculator kholein", "url": tg_link}]]})})
    out.append("Telegram ✅" if r else "Telegram ❌")
    if not state.get("rc_fb_off") and _fb_count(brand, day) < FB_MAX:
        try:
            fb_post(brand, f"📅 {line}\n\n🧮 {title}\n{desc}\n\n👉 {fb_link}", fb_link)
            _fb_note(brand, day)
            out.append(f"FB ({BRANDS.get(brand, {}).get('name', brand)}) ✅")
        except Exception as ex:
            out.append(f"FB ❌ ({str(ex)[:60]})")
    state.update("rc_mk_last", lambda d: {**(d or {}), slug: day}, {})
    state.put("rc_mk_info", {"d": day, "slug": slug, "out": out})
    return f"📅 Mauka post: {SITE}/{slug} → " + ", ".join(out)


# ------------------------------------------------------------------ 3) Funnel
def funnel_rows(days=7):
    from . import website as W
    from .scoreboard import group_source
    import requests
    tok = W._gcreds("https://www.googleapis.com/auth/analytics.readonly")
    s, e = W.ga_range(days)
    j = requests.post(f"https://analyticsdata.googleapis.com/v1beta/properties/{W.GA4_PROPERTY}:runReport",
                      headers={"Authorization": f"Bearer {tok}"}, timeout=60, json={
                          "dateRanges": [{"startDate": s, "endDate": e}], "dimensions": [{"name": "sessionSource"}],
                          "metrics": [{"name": "activeUsers"}, {"name": "sessions"}, {"name": "engagedSessions"},
                                      {"name": "screenPageViews"}, {"name": "userEngagementDuration"}], "limit": 250}).json()
    if "error" in j:
        raise RuntimeError(j["error"].get("message", "")[:300])
    agg = {}
    for r in j.get("rows") or []:
        g = group_source(r["dimensionValues"][0]["value"])
        v = [float(x.get("value") or 0) for x in r["metricValues"]]
        a = agg.setdefault(g, [0.0] * 5)
        for i in range(5):
            a[i] += v[i]
    return agg


def funnel_text(days=7, agg=None):
    try:
        agg = agg if agg is not None else funnel_rows(days)
    except Exception as ex:
        return f"📉 Funnel report nahi bani: {str(ex)[:200]}"
    rows = [(g, *v) for g, v in agg.items() if v[0] >= 1]
    if not rows:
        return f"📉 Funnel ({days} din): abhi GA4 mein koi ginti nahi."
    rows.sort(key=lambda x: -x[1])
    U = sum(r[1] for r in rows)
    S = sum(r[2] for r in rows) or 1
    E = sum(r[3] for r in rows)
    L = [f"📉 FUNNEL - kahan se aaye, kitne ruke ({days} din, GA4 ki asli ginti)",
         f"Kul: {int(U)} log · ruke {100 * E / S:.0f}% · ausat {int(sum(r[5] for r in rows) / max(U, 1))} sec · "
         f"{sum(r[4] for r in rows) / max(U, 1):.1f} page/aadmi"]
    for g, u, s, en, pv, dur in rows[:12]:
        L.append(f"• {g}: {int(u)} log · ruke {100 * en / max(s, 1):.0f}% · {int(dur / max(u, 1))} sec · {pv / max(u, 1):.1f} page")
    big = [r for r in rows if r[1] >= max(10, 0.1 * U)]
    if big:
        worst = min(big, key=lambda r: r[3] / max(r[2], 1))
        best = max(big, key=lambda r: r[3] / max(r[2], 1))
        if worst[0] != best[0]:
            L.append(f"\n🔴 Sabse badi kami: {worst[0]} se aaye {int(worst[1])} log mein sirf {100 * worst[3] / max(worst[2], 1):.0f}% ruke.")
            L.append(f"🟢 Sabse achhe: {best[0]} ({100 * best[3] / max(best[2], 1):.0f}% ruke).")
    L.append("ℹ️ 'Ruke' = GA4 'engaged session' (10 sec+ ya 2 page ya koi kaam). 'Anjaan' = app ke andar khula link.")
    return "\n".join(L)


def funnel_due(now=None):
    now = _now(now)
    return now.weekday() == FN_DAY and now.strftime("%H:%M") >= FN_HHMM and state.get("rc_fn_day") != str(now.date())


# ------------------------------------------------------------------ 4) Saal jaanch
def year_pages(year=None):
    year = str(year or _now().year)
    out = []
    try:
        for f in sorted(_site_dir().glob("*.html")):
            m = re.search(r"<title>([^<]*)</title>", f.read_text(encoding="utf-8", errors="ignore"))
            if m and year in m.group(1):
                out.append(f.stem)
    except Exception as ex:
        log(f"year pages: {ex}")
    return out


def year_text(year=None):
    year = int(year or _now().year)
    pg = year_pages(year)
    if not pg:
        return f"📆 Saal jaanch: kisi page ke title mein {year} nahi - kuch karna nahi."
    return (f"📆 SAAL JAANCH: {len(pg)} page ke title mein {year} likha hai. 1 Jan ke baad ye purane lagenge:\n"
            + "\n".join(f"• {SITE}/{s}" for s in pg)
            + f"\n\n⚠️ Bot inhe apne aap NAHI badalta: tax/budget wale page mein naye niyam aane se pehle {year + 1} likhna galat hoga. "
              "Claude ko ye suchi dikhayein - wo har page jaanch kar badlega.")


def year_due(now=None):
    now = _now(now)
    return now.strftime("%m-%d") >= "12-20" and now.strftime("%H:%M") >= "11:00" and state.get("rc_yr") != str(now.year)


# ------------------------------------------------------------------ 5) Naye kaam haal
def status_text(now=None):
    now = _now(now)
    day = str(now.date())
    L = ["🚀 NAYE KAAM HAAL (traffic + rukna)"]
    lg = [x for x in (state.get("rc_fb_log") or []) if x.get("d") == day]
    L.append(f"{'⬜ BAND' if state.get('rc_fb_off') else '✅'} FB page link-card (reel ke 3 ghante baad, brand max {FB_MAX}/din): "
             f"aaj {len(lg)}" + "".join(f"\n   • {x['t']} {BRANDS.get(x['b'], {}).get('name', x['b'])} #{x['aid']}" for x in lg))
    er = state.get("rc_fb_err")
    if er:
        L.append(f"   Aakhri galti: {er.get('t')} - {er.get('e')}")
    mi = state.get("rc_mk_info") or {}
    L.append(f"{'⬜ BAND' if state.get('rc_mk_off') else '✅'} Mauka calendar (roz {MK_HHMM}): "
             + (f"aakhri {mi.get('d')} {SITE}/{mi.get('slug')} ({', '.join(mi.get('out') or [])})" if mi else "abhi koi nahi"))
    p = mauka_pick(now)
    L.append(f"   Aaj ka mauka: {SITE}/{p[0]}" if p else "   Aaj calendar mein koi mauka nahi")
    L.append(f"✅ Funnel report: har Ravivaar {FN_HHMM} (ya likho 'funnel')")
    L.append("\nPehle se bane (inka switch/login):")
    try:
        from . import push
        c = push.cfg()
        L.append(f"{'✅' if (c.get('app_id') and state.get('push_on')) else '⬜'} Website notification (OneSignal)"
                 + ("" if c.get("app_id") else " → bhejein: onesignal <app_id> <key>"))
    except Exception:
        pass
    L.append(f"{'✅' if state.get('answer_poll') else '⬜'} Telegram quiz poll (roz 2)" + ("" if state.get("answer_poll") else " → likho: jawab poll chalu"))
    try:
        from . import website
        L.append(f"{'✅' if website._env().get('PSI_KEY') else '⬜'} Website speed (PageSpeed, hafte mein)"
                 + ("" if website._env().get("PSI_KEY") else " → psi key <AIza...>"))
    except Exception:
        pass
    try:
        from . import ytcomment
        n = [BRANDS[b]["name"] for b in BRANDS if ytcomment.has(b)]
        L.append(f"{'✅' if len(n) == len(BRANDS) else '🟡'} YouTube comment par jawab-link: {len(n)}/{len(BRANDS)} channel"
                 + ("" if len(n) == len(BRANDS) else " → 'yt comment login'"))
    except Exception:
        pass
    try:
        from . import quizbot
        inl = state.get("quizbot_inline")
        L.append(f"{'✅' if quizbot.token() else '⬜'} Quiz bot" + (f" @{state.get('quizbot_user')}" if state.get("quizbot_user") else "")
                 + (" · inline share ✅" if inl else " · inline share ⬜ → BotFather: /setinline → quiz bot chunein → 'sawal ya code likhein'"))
    except Exception:
        pass
    L.append("✅ Jawab page: agla sawal, khoj, 3 milte-julte, challenge, streak, score card (pehle se)")
    return "\n".join(L)


# ------------------------------------------------------------------ loop + text
def tick(now, run):
    """bot loop se har baar; khud throttle. Bhaari kaam run() thread mein."""
    try:
        if time.time() - state.get("rc_at", 0) < 300:
            return
        state.put("rc_at", time.time())
        e = fb_due(now)
        if e:
            run(lambda e=e: fb_run(e))
        if mauka_due(now):
            state.put("rc_mk_day", str(now.date()))
            run(lambda: log(mauka_run(now)))
        if funnel_due(now):
            state.put("rc_fn_day", str(now.date()))
            run(lambda: tg.say(funnel_text(7)))
        if year_due(now):
            state.put("rc_yr", str(now.year))
            run(lambda: tg.say(year_text(now.year)))
    except Exception as ex:
        log(f"reach tick: {ex}")


def on_text(tl, run):
    """v3.4.26: hukum mila = True (tg.say dohra-rok par None deta tha -> AI ke paas chala jaata)."""
    r = _on_text(tl, run)
    return None if r is _NOPE else True


_NOPE = object()


def _on_text(tl, run):
    tl = re.sub(r"[.!?।]+$", "", (tl or "").strip().lower()).strip()
    m = re.fullmatch(r"funnel(?: (\d{1,3}))?(?: din)?|platform (?:wise|ke hisaab se) rukna|kaun kitna ruka|kahan se aaye kitne ruke", tl)
    if m:
        d = int(m.group(1)) if m.lastindex and m.group(1) else 7
        return run(lambda: tg.say(funnel_text(max(1, min(d, 90)))))
    if tl in ("fb link post band", "fb link band", "link card band"):
        state.put("rc_fb_off", True)
        return tg.say("⬜ FB page link-card band. Chalu: 'fb link post chalu'")
    if tl in ("fb link post chalu", "fb link chalu", "link card chalu"):
        state.put("rc_fb_off", False)
        return tg.say(f"✅ FB page link-card chalu (reel ke 3 ghante baad, har brand max {FB_MAX}/din).")
    if tl in ("mauka band", "mauka calendar band"):
        state.put("rc_mk_off", True)
        return tg.say("⬜ Mauka calendar band. Chalu: 'mauka chalu'")
    if tl in ("mauka chalu", "mauka calendar chalu"):
        state.put("rc_mk_off", False)
        return tg.say(f"✅ Mauka calendar chalu (roz {MK_HHMM}).")
    if tl in ("mauka abhi", "mauka post"):
        return run(lambda: tg.say(mauka_run(manual=True)))
    if tl in ("naye kaam haal", "naye kaam", "reach haal", "traffic kaam haal"):
        return tg.say(status_text())
    if tl in ("saal jaanch", "year check"):
        return tg.say(year_text())
    return _NOPE
