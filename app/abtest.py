"""v2.9.1 (plan: A/B thumbnail): LAMBI video ka thumbnail CTR kam ho to doosra (pehle se bana) thumbnail apne aap.

Kyun sirf lambi: YouTube Shorts mein custom thumbnail feed mein dikhta hi nahi. Kab: upload ke 3-10 din (YouTube Reporting
ka data 1-2 din der se aata hai - '3 ghante' sambhav nahi). Shart: owner ka '/analytics' login (bina login kuch nahi karta,
sirf PENDING mein yaad). Niyam: kam se kam 300 impression, CTR brand ki baaki lambi video ke median ka 70% se kam; har video par
EK hi badlaav (baar-baar nahi). Thumbnail.set YouTube API ka jayaz tareeka hai.
"""
import json
import shutil
import statistics
import time

from . import state, tg
from .config import BRANDS, DATA
from .log import log

DIR = DATA / "ab"
MIN_IMP = 300


def remember(brand, vid, thumbs, used=0):
    """Upload ke waqt: baaki thumbnail sambhaal kar rakho (STOCK saaf ho jaata hai)."""
    DIR.mkdir(parents=True, exist_ok=True)
    keep = []
    for k, p in enumerate(thumbs or []):
        if k == used:
            continue
        try:
            dst = DIR / f"{vid}_{k}.jpg"
            shutil.copy(p, dst)
            keep.append(str(dst))
        except Exception as e:
            log(f"ab copy: {e}")
    if keep:
        state.update("ab_long", lambda d: {**(d or {}), vid: {"brand": brand, "t": time.time(), "alts": keep, "done": False}}, {})


def decide(vid, ctrs, min_imp=MIN_IMP):
    """ctrs: {video_id: {'impressions','ctr'}} -> True agar is video ka thumbnail badalna chahiye. Bina network (test)."""
    me = ctrs.get(vid) or {}
    if me.get("impressions", 0) < min_imp:
        return False
    others = [v["ctr"] for k, v in ctrs.items() if k != vid and v.get("impressions", 0) >= min_imp]
    if len(others) < 2:
        return False
    return me.get("ctr", 0) < 0.7 * statistics.median(others)


def tick():
    from . import analytics, youtube
    cands = dict(state.get("ab_long") or {})
    if not cands:
        return ""
    msgs = []
    by_brand = {}
    for vid, c in cands.items():
        age = (time.time() - float(c.get("t", 0))) / 86400
        if c.get("done") or not 3 <= age <= 10:
            continue
        by_brand.setdefault(c["brand"], []).append(vid)
    for b, vids in by_brand.items():
        if not analytics.has(b):
            continue
        try:
            ctrs = analytics.video_ctr(b)
        except Exception as e:
            log(f"ab ctr {b}: {e}")
            continue
        for vid in vids:
            c = cands[vid]
            if not decide(vid, ctrs):
                continue
            alt = next((a for a in c.get("alts") or []), None)
            if not alt:
                continue
            try:
                with open(alt, "rb") as f:
                    youtube._api(b, "POST", "/upload/youtube/v3/thumbnails/set", params={"videoId": vid},
                                 headers={"Content-Type": "image/jpeg"}, data=f.read())
                c["done"] = True
                msgs.append(f"• {BRANDS[b]['name']}: https://youtu.be/{vid} (CTR {ctrs[vid]['ctr']}%) -> doosra thumbnail")
            except Exception as e:
                log(f"ab set {vid}: {e}")
    old = time.time() - 30 * 86400
    state.put("ab_long", {k: v for k, v in cands.items() if float(v.get("t", 0)) > old})
    return ("🖼 A/B thumbnail (lambi video, CTR kam tha):\n" + "\n".join(msgs)) if msgs else ""
