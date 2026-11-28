"""v3.7.0: Instagram account RUKA ho (Meta ne band/appeal - jaise Suno Natak 23 Nov 2026) to bot baar-baar koshish na kare.

Kyun: band account par roz 2 upload + comment ke jawab = har baar ❌ error, aur Meta ko lagta hai band account se zabardasti
ho rahi hai (appeal par bura asar). Isliye:
  - IG upload mein 'account band/suspend/disable/checkpoint/permission' wali galti -> us brand ka Instagram apne aap BAND
    (platform_off, wahi setting jo owner 'X ka instagram band karo' se lagata hai) + owner ko ek hi alert.
  - Band rahne tak us brand par IG comment padhna/jawab bhi band.
  - Roz ek baar chupchaap jaanch (/{ig_id}?fields=username): account wapas khul gaya to apne aap CHALU + owner ko khabar.
  - Owner ne khud band kiya ho (auto nahi) to bot kabhi khud chalu nahi karta.
"""
import re
import time

from . import state
from .config import BRANDS
from .log import log

BAD_RX = re.compile(r"disabl|suspend|checkpoint|restrict|not authorized|permission|does not exist|cannot be loaded|"
                    r"unsupported get request|session has been invalidated|error validating access token|"
                    r"code\"?: ?(10|190|200|803)\b|subcode\"?: ?(2207050|2207051|2207085)\b|account.*(band|blocked)", re.I)


def off(brand):
    return "instagram" in ((state.get("platform_off") or {}).get(brand) or [])


def _set(brand, turn_off):
    def upd(d):
        d = dict(d or {})
        cur = set(d.get(brand, []))
        cur.add("instagram") if turn_off else cur.discard("instagram")
        d[brand] = sorted(cur)
        return d
    state.update("platform_off", upd, {})
    auto = set(state.get("ig_auto_off") or [])
    auto.add(brand) if turn_off else auto.discard(brand)
    state.put("ig_auto_off", sorted(auto))


# v3.9.5 (audit 25 Nov): Meta ki taraf ki kuch der ki galti (file processing / network) - account band NAHI. Pehle ye bhi 3 baar
# hone par brand ka poora Instagram band kar deti thi (services reel par ProcessingFailedError roz aata hai, 30 min baad chal jaata hai).
TRANSIENT_RX = re.compile(r"ProcessingFailed|Request processing failed|processing ka samay|process nahi ki|HTTP 5\d\d|"
                          r"timed? ?out|Connection|temporar|try again|is_transient\"?: ?true|code\"?: ?(1|2|4|17|32|341)\b|"
                          r"seema poori|publish seema", re.I)


def transient(err):
    return bool(TRANSIENT_RX.search(str(err))) and not BAD_RX.search(str(err))


def note_fail(brand, err):
    """pipeline IG upload ki galti -> account-band jaisi ho to brand ka IG apne aap band."""
    if transient(err):
        return False                                  # v3.9.5: Meta ki kuch der ki galti - ginti nahi, band nahi; pipeline khud dobara bhejti hai
    if off(brand) or not BAD_RX.search(str(err)):
        cnt = dict(state.get("ig_fail_cnt") or {})
        cnt[brand] = cnt.get(brand, 0) + 1
        state.put("ig_fail_cnt", cnt)
        if cnt[brand] < 3 or off(brand):
            return False
    _set(brand, True)
    state.put("ig_fail_cnt", {**(state.get("ig_fail_cnt") or {}), brand: 0})
    from . import tg
    tg.alert("red", f"📸 {BRANDS[brand]['name']} ka Instagram ab bot ne ROKA (Meta ne account band/appeal mein rakha lagta hai).\n"
                    f"Galti: {str(err)[:150]}\nBaaki sab platform chalu. Bot roz chupchaap jaanchega - account khulte hi "
                    "apne aap chalu karke batayega. Appeal Instagram app mein hi hoti hai (bot nahi kar sakta).")
    return True


def note_ok(brand):
    cnt = dict(state.get("ig_fail_cnt") or {})
    if cnt.get(brand):
        cnt[brand] = 0
        state.put("ig_fail_cnt", cnt)


def daily_check():
    """Auto-band brand ka IG khul gaya? -> chalu."""
    from . import meta as M, tg
    for b in list(state.get("ig_auto_off") or []):
        try:
            bi = M.brand_info(b) or {}
            if not bi.get("ig_id"):
                continue
            j = M._get(f"/{bi['ig_id']}", bi["page_token"], fields="username")
            if j.get("username"):
                _set(b, False)
                tg.alert("green", f"📸 {BRANDS[b]['name']} ka Instagram wapas khul gaya - bot ne upload/comment phir CHALU kiye.")
        except Exception as e:
            log(f"igguard {b}: {str(e)[:80]}")


def tick(run):
    d = time.strftime("%Y-%m-%d")
    if state.get("ig_guard_day") != d and state.get("ig_auto_off"):
        state.put("ig_guard_day", d)
        run(daily_check)
