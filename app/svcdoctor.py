"""v3.8.8 SERVICES DOCTOR - owner: "baar baar audit fail ho rhi hai, ek doctor baithao jo har 5 min par automatically theek kare".

Har 5 minute (sasta - sirf jaanch, bhaari kaam tabhi jab kuch bimaar ho):
 1. Awaaz engine: bimaar mila tha to alag process mein chhoti jaanch; theek hote hi bachi video bana deta hai.
 2. Aaj ki services video: jis brand ki aaj ki video nahi bani aur uska slot abhi aage hai - ek baar aur (din mein brand par max 2).
 3. Form/Worker (Cloudflare): har 30 min ping; 2 baar fail = worker dobara chadhao (2 ghante mein ek baar), phir bhi = owner ko.
 4. Atka hua 'video ban rahi' nishan (90 min+) hatao.
 5. Atke page-update (push queue) bhejo.
Owner ko SIRF badlaav par sandesh (bimaar hua / theek hua) - har 5 min shor nahi. 'services doctor' = abhi ka poora haal.
Niyam: naya content/rate kabhi nahi badalta, sirf pehle se jaanche raaste dobara chalata hai.
"""
import datetime
import time

import requests

from . import state
from .log import log

EVERY = 300


def _now():
    from . import pipeline
    return pipeline.now()


def _say(msg, red=False):
    from . import tg
    (tg.alert("red", msg) if red else tg.say(msg))


def _flag(name, bad, sick_msg, ok_msg, red=True):
    """Badlaav par hi bolo."""
    st = state.get("svcdoc_flags") or {}
    was = bool(st.get(name))
    if bad and not was:
        _say(sick_msg, red)
    if not bad and was and ok_msg:
        _say(ok_msg)
    st[name] = bool(bad)
    state.put("svcdoc_flags", st)


def check_tts(fix=True):
    from . import tts
    sick = state.get("svc_tts_bad")
    if not sick:
        return True, "awaaz ✅"
    if not fix:
        return False, f"awaaz bimaar: {sick.get('why', '')[:120]}"
    ok, msg = tts.selftest()
    if ok:
        state.put("svc_tts_bad", None)
        with tts._LOCK:                      # bot ke andar ka model bhi naya load ho
            tts._pipe = None
        _say(f"✅ Doctor: services video ki awaaz phir theek ({msg}). Bachi video ab ban rahi hai.")
        if sick.get("sample") and sick.get("brand"):
            state.put("svcdoc_namoona", sick["brand"])
        return True, "awaaz theek ki ✅"
    log(f"svcdoctor tts: {msg}")
    if time.time() - (sick.get("t") or 0) > 6 * 3600 and not sick.get("told6"):
        sick["told6"] = 1
        state.put("svc_tts_bad", sick)
        _say("🩺 Services awaaz 6 ghante se theek nahi ho rahi (" + msg[:120] + "). Ye bot ke bas se bahar lagta hai - is sandesh ka "
             "screenshot Claude ko bhejiye. Baaki video (quiz) par asar nahi.", red=True)
    return False, f"awaaz abhi bhi bimaar ({msg[:80]})"


def missing_today():
    """Aaj jin brand ki services video NAHI bani aur slot 25 min+ aage hai."""
    from . import pipeline, svcvideo
    n = _now()
    d = str(n.date())
    have = set()
    for j in pipeline.jobs().values():
        if j.get("style") == "services_ad" and str(j.get("created", ""))[:10] == d and j.get("reason") == "roz ka schedule":
            have.add(j.get("brand"))
    out = []
    try:
        plan = svcvideo.pick_day(day=d)
    except Exception as e:
        log(f"svcdoctor plan: {e}")
        return []
    for b, v in plan.items():
        if b in have:
            continue
        try:
            if svcvideo._slot_dt(v["slot"], n.date()) >= n + datetime.timedelta(minutes=35):
                out.append(b)
        except Exception:
            pass
    return out


def fill_missing():
    """Doctor ka ilaaj: bachi aaj ki services video (bot.run se - kaam ki line mein ek hi baar)."""
    from . import svcvideo
    bs = missing_today()
    if bs:
        svcvideo.make_day(brands=bs)


def check_video(run=None, fix=True):
    from . import pipeline
    from .svcvideo import video_on
    if not video_on():
        return True, "services video band hai (owner)"
    n = _now()
    d = str(n.date())
    hm = n.strftime("%H:%M")
    if (state.get("svc_holiday_until") or "") >= d:
        return True, "chhutti"
    mk = state.get("svc_making") or 0
    if mk and time.time() - mk > 90 * 60:           # atka nishan (bot beech mein ruka tha)
        state.put("svc_making", 0)
        mk = 0
    if mk:
        return True, "video abhi ban rahi hai"
    if state.get("svc_tts_bad"):
        return False, "awaaz theek hone ka intezaar"
    if not ("05:00" <= hm <= "19:30") or state.get("svc_video_day") != d:
        return True, "aaj ka samay/raat wala kaam baaki"
    miss = missing_today()
    if not miss:
        return True, "aaj ki services video ✅"
    tries = state.get("svcdoc_fill") or {}
    if tries.get("d") != d:
        tries = {"d": d}
    left = [b for b in miss if tries.get(b, 0) < 2]
    if not left:
        return False, f"aaj {', '.join(miss)} ki video 2 baar koshish ke baad bhi nahi bani"
    if fix and run is not None:
        for b in left:
            tries[b] = tries.get(b, 0) + 1
        state.put("svcdoc_fill", tries)
        run(fill_missing)
        return True, f"bachi video bana raha: {', '.join(left)}"
    return False, f"bachi video: {', '.join(left)}"


def check_worker(fix=True):
    from . import svc
    c = svc._cfg()
    if not c.get("url"):
        return True, "form worker abhi set nahi"
    try:
        r = requests.get(f"{c['url']}/{c['key']}/ping", timeout=20)
        good = r.ok and r.text.strip() == "ok"
    except Exception:
        good = False
    fails = 0 if good else int(state.get("svcdoc_wfail") or 0) + 1
    state.put("svcdoc_wfail", fails)
    if good:
        return True, "form/worker ✅"
    if fails >= 2 and fix and time.time() - (state.get("svcdoc_wfix") or 0) > 7200:
        state.put("svcdoc_wfix", time.time())
        try:
            svc.ensure_site_cfg()
            return False, "form/worker jawab nahi de raha - dobara chadhaya"
        except Exception as e:
            return False, f"form/worker band, dobara chadhana fail: {str(e)[:80]}"
    return False, f"form/worker jawab nahi ({fails} baar)"


def tick(run):
    t = time.time()
    if t - (state.get("svcdoc_at") or 0) < EVERY:
        return
    state.put("svcdoc_at", t)

    def _go():
        ok_t, m_t = check_tts()
        _flag("tts", not ok_t, "", "")
        ok_v, m_v = check_video(run)
        _flag("video", not ok_v, f"🩺 Doctor: {m_v}. Wajah 'services doctor' mein.", "✅ Doctor: aaj ki services video ab theek.")
        if t - (state.get("svcdoc_wat") or 0) > 1800:
            state.put("svcdoc_wat", t)
            ok_w, m_w = check_worker()
            _flag("worker", not ok_w, f"🩺 Doctor: website form ka worker: {m_w}. Customer ka form abhi bhi Telegram par aane ki "
                                      "koshish karta hai (offline line).", "✅ Doctor: website form/worker phir chal raha.")
        nb = state.get("svcdoc_namoona")
        if nb:
            state.put("svcdoc_namoona", None)
            from . import svcvideo
            svcvideo.make_day(sample=True, only=nb)
    run(_go)


def report():
    lines = ["🩺 Services doctor (har 5 min apne aap):"]
    for name, fn in (("Awaaz", lambda: check_tts(fix=False)), ("Video", lambda: check_video(None, fix=False)),
                     ("Form", lambda: check_worker(fix=False))):
        try:
            ok, m = fn()
        except Exception as e:
            ok, m = False, f"jaanch fail: {str(e)[:80]}"
        lines.append(f"{'✅' if ok else '❌'} {name}: {m}")
    try:
        from . import svcvideo
        rows = [l for l in (svcvideo.DIR / "video_audit.jsonl").read_text(encoding="utf-8").splitlines()[-6:]]
        import json
        for r in rows:
            j = json.loads(r)
            bad = [x for x in j.get("rep", []) if x.startswith("❌")]
            lines.append(f"  {j['t'][5:16]} {j['brand']}: {'✅' if j['ok'] else '❌ ' + (bad[0][:70] if bad else '')}")
    except Exception:
        pass
    q = 0
    try:
        from . import svc
        q = len(svc._read("push_queue.jsonl"))
    except Exception:
        pass
    lines.append(f"Atke page-update: {q}")
    return "\n".join(lines)
