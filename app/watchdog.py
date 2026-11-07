"""v2.5.5: bot khud nigrani karta hai. Dikkat mile to Telegram par STEP-WISE 'kya karna hai'. Ek dikkat ka ek hi sandesh
(24 ghante baad hi dobara, jab tak dikkat rahe); theek hone par ek '✅ theek ho gaya'. Ye sirf PADHTA hai aur batata hai -
website/channel/settings kuch nahi badalta. Naye feature ka ek baar ka 'chalu karein?' prastav (ek tap, dohri pushti ke saath)."""
import re
import time

from . import state, tg
from .log import log

RESEND_H = 24


def _hrs(ts):
    return (time.time() - (ts or time.time())) / 3600


def evaluate():
    """-> list of dict(key, title, steps). Pure state padhta hai (network nahi) - test ho sake."""
    out = []
    now = time.time()
    on = bool(state.get("jawab_site_on"))
    if on:
        if state.get("jawab_live"):
            state.put("jawab_down_since", 0)
        else:
            ds = state.get("jawab_down_since") or 0
            if not ds:
                state.put("jawab_down_since", now)
            elif now - ds > 2 * 3600:
                out.append({"key": "jawab_down", "title": "/jawab page 2 ghante se nahi khul raha",
                            "steps": ["Bot mein 'canary' likhein - kaun sa page ❌ hai dekhein",
                                      "Cloudflare Pages → Deployments mein aakhri deploy ✅ hai ya ❌ dekhein",
                                      "Bot mein 'jawab website chalu' likhein (page dobara banega) - 30 min baad phir 'canary'",
                                      "Phir bhi nahi to 'canary' ka screenshot Claude ko bhejein"]})
        err = state.get("jawab_last_error") or ""
        if err and state.get("answer_dirty"):
            since = state.get("jawab_err_since") or 0
            if not since:
                state.put("jawab_err_since", now)
            elif now - since > 12 * 3600:
                out.append({"key": "jawab_publish", "title": "/jawab page 12 ghante se website par nahi chadh pa raha",
                            "steps": ["Neeche ka error padhein: " + err[:300],
                                      "Agar 'Audit fail' hai: error mein jis page ka naam hai uski galti developer se theek karwayein (docs/SITESCAN.md bhi dekhein)",
                                      "Theek hone par bot apne aap dobara koshish karta hai; jaldi chahiye to 'jawab website chalu'"]})
        else:
            state.put("jawab_err_since", 0)
    if state.get("up_alerted"):
        out.append({"key": "site_down", "title": "Website 5xx/slow/soft-404 de rahi hai",
                    "steps": ["Browser mein https://sabhisaab.com kholkar dekhein",
                              "Cloudflare dashboard → Pages → sabhisaab → Deployments dekhein; aakhri deploy ❌ ho to 'Retry deployment'",
                              "Bot mein 'canary' likhein; jawab Claude ko bhejein"]})
    try:
        from . import ytcomment
        miss = ytcomment.missing()
        if miss and (state.get("yt_reply_noscope") or state.get("yt_comment_noscope")):
            from .config import BRANDS
            out.append({"key": "yt_comment_login", "every": 7 * 24,
                        "title": "YouTube par bot comment nahi likh pa raha (upload wala login comment ki ijaazat nahi deta)",
                        "steps": ["Bot mein 'yt comment login' likhein - har channel ka ek link aayega",
                                  "Har link kholkar us channel ka account chunein (brand wala naam), 'Allow' dabayein (saari ijaazat tick)",
                                  "Browser ka poora address (localhost...code=...) bot ko bhej dein - bot turant mita dega",
                                  "Baaki channel: " + ", ".join(BRANDS[b]["name"] for b in miss),
                                  "Google Cloud → OAuth consent screen → Publishing status 'In production' rakhein, warna login 7 din mein expire hoga"]})
    except Exception as ex:
        log(f"watchdog ytc: {ex}")
    sl = state.get("sitescan_last") or {}
    if sl.get("mismatch"):
        out.append({"key": f"scan_mismatch_{sl['mismatch']}", "title": f"Website par {sl['mismatch']} toote related-link (naam ≠ page)",
                    "steps": ["Bot mein 'docs do' likhein ya GitHub docs/SITESCAN.md kholein (list wahin hai)",
                              "Developer ko do: link ka naam slug se banao (ek slug→title map), poori site par",
                              "Theek hone par agle Ravivaar ke scan mein ye alert apne aap hat jayega"]})
    return out


def _fmt(p):
    return f"⚠️ {p['title']}\nKya karein (step wise):\n" + "\n".join(f"{i}) {s}" for i, s in enumerate(p["steps"], 1))


def notify(problems):
    """Dedupe: ek key ek baar, 24 ghante baad dobara jab tak rahe; hatne par ek 'theek ho gaya'."""
    sent = state.get("wd_sent") or {}
    now = time.time()
    keys = {p["key"] for p in problems}
    for p in problems:
        if now - sent.get(p["key"], 0) >= p.get("every", RESEND_H) * 3600:
            sent[p["key"]] = now
            tg.alert("yellow", _fmt(p))
    for k in [k for k in sent if k not in keys and sent[k]]:
        tg.say(f"✅ Theek ho gaya: {k.replace('_', ' ')}")
        sent.pop(k, None)
    state.put("wd_sent", sent)


def net_checks():
    """Roz ek baar (network): ad code approval se pehle / privacy ke vaade. -> problems"""
    from . import adsense
    out = []
    pub = state.get("adsense_pub")
    try:
        home = adsense._get("/").text
        priv = adsense._get("/privacy").text
    except Exception as e:
        log(f"watchdog net: {e}")
        return out
    if "adsbygoogle" in home and not pub:
        out.append({"key": "ads_before_approval", "title": "Homepage par AdSense code hai par ads.txt/approval nahi",
                    "steps": ["Developer se ad code abhi hatwayein (approval se pehle nahi)", "Ya AdSense approve ho gaya ho to bot mein 'adsense id pub-...' likhein"]})
    if pub and re.search(r"koi vigyapan nahi", priv, re.I):
        out.append({"key": "privacy_no_ads_line", "title": "AdSense chalu hai par privacy page par 'koi vigyapan nahi' line hai",
                    "steps": ["docs/PRIVACY_PATCH.md ka 'Section 4' text developer ko dein", "Privacy page ki 'Aakhri update' tareekh badlwayein"]})
    if re.search(r"(?i:instagram)[^.\n]{0,200}\bLINK\b|\bLINK\b[^.\n]{0,200}(?i:instagram)", priv):
        out.append({"key": "privacy_ig_link", "title": "Privacy page par Instagram 'LINK' private-reply wali line hai (bot ye nahi karta)",
                    "steps": ["Bot mein 'privacy ig theek' likhein - bot purani aur nayi line dikhayega", "Sahi lage to ✅✅ dabayein (audit paas hone par hi chadhega)", "Phir 'Aakhri update' tareekh developer se badlwayein"]})
    return out


def propose_digest():
    """Ek baar (7 din baad dobara, max 2): Telegram digest ek tap se chalu karne ka prastav."""
    if state.get("answer_digest") or not state.get("jawab_site_on"):
        return
    asks = state.get("digest_asks", 0)
    if asks >= 2 or time.time() - state.get("digest_ask_at", 0) < 7 * 86400:
        return
    state.put("digest_asks", asks + 1)
    state.put("digest_ask_at", time.time())
    tg.say("💡 Prastav: roz shaam 20:30 par ek digest (sab jawab ek message mein + website button) Telegram channel par. "
           "Abhi har video ke saath alag post jaati hai. Chalu karein?", tg.inline([[("✅✅ Haan, chalu", "s44:on"), ("❌ Abhi nahi", "s44:x")]]))


def propose_poll():
    """Telegram native quiz poll (roz max 2) ka ek-tap prastav (max 2 baar, 7 din gap). Digest chalu ho to nahi."""
    if state.get("answer_poll") or state.get("answer_digest") or not state.get("jawab_site_on"):
        return
    asks = state.get("poll_asks", 0)
    if asks >= 2 or time.time() - state.get("poll_ask_at", 0) < 7 * 86400:
        return
    state.put("poll_asks", asks + 1)
    state.put("poll_ask_at", time.time())
    tg.say("💡 Prastav: Telegram channel par roz max 2 sawal NATIVE QUIZ POLL ki tarah (log vikalp chunte hain, jawab + website link explanation mein). "
           "Baaki jawab pehle jaisa text post. Chalu karein?", tg.inline([[("✅✅ Haan, chalu", "s46:on"), ("❌ Abhi nahi", "s46:x")]]))


def tick():
    """Bot loop se har baar bulao; khud throttle (har 30 min). Kabhi exception nahi uthata."""
    try:
        if time.time() - state.get("wd_at", 0) < 1800:
            return
        state.put("wd_at", time.time())
        probs = evaluate()
        if time.time() - state.get("wd_net_at", 0) > 86400:
            state.put("wd_net_at", time.time())
            probs += net_checks()
            state.put("wd_net_probs", [p["key"] for p in probs if p["key"] in ("ads_before_approval", "privacy_no_ads_line", "privacy_ig_link")])
            state.put("wd_net_cache", {p["key"]: p for p in probs if p["key"] in state.get("wd_net_probs")})
        else:                                      # network check roz ek baar; beech mein purani dikkat jab tak rahe
            probs += list((state.get("wd_net_cache") or {}).values())
        notify(probs)
        propose_digest()
        propose_poll()
    except Exception as e:
        log(f"watchdog: {e}")


def weekly(weekday, hhmm, today):
    """Ravivaar (6) 19:00 baad: ypp haal. Somvaar (0) 10:00 baad: adsense haal. Sirf padhna."""
    try:
        if weekday == 6 and hhmm >= "19:00" and state.get("wk_ypp") != today:
            state.put("wk_ypp", today)
            from . import ypp
            tg.say(ypp.report())
        if weekday == 0 and hhmm >= "10:00" and state.get("wk_ads") != today:
            state.put("wk_ads", today)
            from . import adsense
            tg.say(adsense.status())
    except Exception as e:
        log(f"watchdog weekly: {e}")


FEATURES = (
    ("Jawab website (/jawab)", "jawab_site_on", "jawab website chalu / band"),
    ("Telegram digest (roz 20:30)", "answer_digest", "jawab digest chalu / band"),
    ("Telegram quiz poll (roz max 2)", "answer_poll", "jawab poll chalu / band"),
    ("ads.txt (AdSense ke baad)", "adsense_pub", "adsense id pub-XXXXXXXXXXXXXXXX"),
)
AUTO = ("UTM + YouTube comment/description mein jawab-link (raat 23:30)", "Uptime (10 min) + canary (deploy ke baad)", "Site scan (Ravivaar 22:00)",
        "YPP haal (Ravivaar) + AdSense haal (Somvaar)", "Story link-sticker yaad (21:00)", "Watchdog: dikkat par step-wise sandesh")


def features_text():
    L = ["🧩 FEATURES (kya chalu hai)"]
    for name, key, how in FEATURES:
        L.append(f"{'✅' if state.get(key) else '⬜'} {name} → {how}")
    L.append("\nApne aap chalte rehte hain:")
    L += [f"✅ {a}" for a in AUTO]
    return "\n".join(L)
