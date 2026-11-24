"""v3.9.3 (owner 24 Nov): services ki PAGE POST (photo + link) - jab log sabse zyada active, har brand roz 1, policy ke andar.

Niyam (Meta/Telegram spam se bachav):
- Har brand ke FB page par roz SIRF 1 services photo-post (link ke saath - FB par link theek; IG par link nahi isliye IG nahi).
- Har din alag 6 kaam, alag rang, alag likhawat (6 tarah) - ek jaisi post baar-baar nahi.
- Feed bhari na ho: services post wale din purani 'sawal photo-post' ek din chhod kar (pipeline.fb_photo_today).
- Samay = us brand ke asli views ka shaam ka sabse accha ghanta (studio.best_hours), brand ki reel se 40 min door.
  Ek baar tay hone ke baad PAKKA (master schedule) - badlav sirf owner ki dohri pushti se.
- 'Limited time / sirf aaj / jaldi' kabhi nahi. Neeche '* शर्तें लागू'. Owner ka naam/UPI kabhi nahi.
"""
import datetime
import json
import time
import zlib

from PIL import Image, ImageDraw

from . import state
from .config import BRANDS, DATA, W
from .log import log

OUT = DATA / "services_post"
PW, PH = 1080, 1350                    # 4:5 - FB feed mein poori dikhti hai
SITE_LIST = "https://sabhisaab.com/services-list"
CAPS = [
    "₹10 से शुरू — कोई भी डिजिटल काम हो जाएगा ✅\nफॉर्म, बायोडाटा, वेबसाइट, Excel, ऐप… आज के कुछ काम:",
    "छोटा हो या बड़ा, हर डिजिटल काम एक जगह — ₹10 से शुरू।\nकाम हिंदी में लिखिए, पहले बात, फिर लिखित रेट:",
    "1000+ डिजिटल काम की रेट लिस्ट — शुरुआती दाम, ₹10 से।\nइनमें से कुछ:",
    "घर बैठे डिजिटल काम — फोन से बताइए, हो जाएगा।\n₹10 से शुरू, बाज़ार से {p}% तक कम:",
    "फॉर्म भरना हो या दुकान की वेबसाइट — कोई भी डिजिटल काम।\nशुरुआती दाम (₹10 से):",
    "English ज़रूरी नहीं, शर्म की कोई बात नहीं — हर डिजिटल काम ₹10 से शुरू।\nआज की लिस्ट से:",
]
LOOK_ROT = ["mint", "sky", "peach", "lilac", "teal", "indigo", "coral", "forest", "rose", "pahad", "lemon", "plum"]


def on():
    v = state.get("svc_post_on")
    return True if v is None else bool(v)


def _now():
    from . import pipeline
    return pipeline.now()


# ---------------------------------------------------------------- pakka samay (master)
def _mins(hm):
    h, m = map(int, hm.split(":"))
    return h * 60 + m


def _calc_times():
    """Har brand: shaam ka best ghanta (asli views) -> 18:00-21:45 mein 15 min ke kadam, brand ki reel + doosre brand ki post se door."""
    from . import pipeline
    out, used = {}, []
    sch = pipeline.schedule()
    for i, b in enumerate(BRANDS):
        try:
            from .studio import best_hours
            eve = int(best_hours(b)[0][1][:2])
        except Exception:
            eve = 19 + (i % 3)
        reels = [_mins(x.strip()) for x in str(sch.get(b, "")).split(",") if x.strip()]
        cands = [h * 60 + m for h in range(18, 22) for m in (0, 15, 30, 45)]
        cands.sort(key=lambda c: abs(c - (eve * 60 + 15 * i)))
        pick = next((c for c in cands if all(abs(c - r) >= 40 for r in reels) and all(abs(c - u) >= 30 for u in used)
                     and all(abs(c - _mins(s)) >= 40 for s in ("18:00", "20:00"))), cands[0])
        used.append(pick)
        out[b] = f"{pick // 60:02d}:{pick % 60:02d}"
    return out


def times():
    """PAKKA samay (pehli baar tay hone ke baad wahi; owner hi dohri pushti se badal sakta hai)."""
    t = state.get("svc_post_times")
    if not t or set(t) != set(BRANDS):
        t = _calc_times()
        state.put("svc_post_times", t)
    return t


# ---------------------------------------------------------------- post ka chitra
def _pick(brand, day):
    """6 kaam: pehla hamesha ₹10 wala (sabse badi baat), 2 aur ₹99 tak, baaki sabse kam post hue - har din alag."""
    from . import svc, svcvideo as V
    R = svc.rates()
    by = R["by"]
    cnt = state.get("svc_post_cnt") or {}
    pool = [k for k in V.KAAM if k in by and not by[k].get("hide") and not by[k].get("novideo")]
    seed = datetime.date.fromisoformat(day).toordinal() * 7 + list(BRANDS).index(brand)
    sc = lambda k: (cnt.get(k, 0), zlib.crc32(f"{k}{seed}".encode()))
    ten = sorted([k for k in pool if by[k]["price"] <= 10], key=sc)[:1]
    cheap = [k for k in sorted([k for k in pool if 10 < by[k]["price"] <= 99], key=sc) if k not in ten][:2]
    cats, rest = set(), []
    for k in sorted([k for k in pool if k not in ten + cheap], key=sc):
        c = by[k]["cat"]
        if c in cats:
            continue
        cats.add(c)
        rest.append(k)
        if len(rest) >= 6 - len(ten) - len(cheap):
            break
    st = ten + cheap + rest
    for k in st:
        cnt[k] = cnt.get(k, 0) + 1
    state.put("svc_post_cnt", cnt)
    return st[:6]


def card(brand, day, path, items=None):
    from . import svc, svcvideo as V
    by = svc.rates()["by"]
    items = items or _pick(brand, day)
    look = LOOK_ROT[(datetime.date.fromisoformat(day).toordinal() + list(BRANDS).index(brand) * 5) % len(LOOK_ROT)]
    c1, c2, br, dk = (V._hex(c) for c in V.LOOKS[look])
    im = V._bg(look).crop((0, 0, PW, PH))
    cv = V.Canvas(im)
    V._logo_draw(im, brand, 60, 56, 64)
    cv.text((140, 88), BRANDS[brand]["name"], V._font(32, "SemiBold"), dk, anchor="lm", tag="bn")
    stk = "₹10 से शुरू"
    fs = V._font(60)
    sw = fs.getlength(stk) + 90
    ImageDraw.Draw(im).rounded_rectangle((PW // 2 - sw // 2, 170, PW // 2 + sw // 2, 262), 46, fill=(224, 49, 49))
    cv.text((PW // 2, 216), stk, fs, (255, 255, 255), tag="stk")
    f = V._fit(V.TAG1, 104, PW - 120)
    cv.text((PW // 2, 360), V.TAG1, f, dk, tag="t1")
    V._marker(cv, (PW // 2, 500), V.TAG2, f, br, tag="t2")
    gw, gh, gg = 300, 150, 24
    gx0 = (PW - (3 * gw + 2 * gg)) // 2
    for n, k in enumerate(items[:6]):
        it = by[k]
        nm = V.KAAM.get(k, (it["name"],))[0]
        gx, gy = gx0 + (n % 3) * (gw + gg), 620 + (n // 3) * (gh + gg)
        V._card(im, (gx, gy, gx + gw, gy + gh), 30, shadow=14)
        nm_s = V._short(nm, gw - 36, 32)
        cv.text((gx + gw // 2, gy + 55), nm_s, V._fit(nm_s, 32, gw - 36, "SemiBold"), dk, tag=f"n{n}")
        pr = V._rs(it["price"]) + " से"
        cv.text((gx + gw // 2, gy + 108), pr, V._font(40), br, tag=f"p{n}")
    up = V.usp_pct()
    ln = f"बाज़ार से {up}% तक कम · शुरुआती दाम" if up >= 50 else "शुरुआती दाम · पहले बात, फिर लिखित रेट"
    cv.text((PW // 2, 1000), ln, V._fit(ln, 44, PW - 140, "SemiBold"), dk, tag="ln")
    bw, bh = 820, 104
    ImageDraw.Draw(im).rounded_rectangle((PW // 2 - bw // 2, 1060, PW // 2 + bw // 2, 1060 + bh), 52, fill=br)
    cv.text((PW // 2, 1060 + bh // 2), V.SITE_TXT, V._fit(V.SITE_TXT, 50, bw - 80), (255, 255, 255), tag="site")
    cv.text((PW // 2, 1222), "कमेंट में अपना काम लिखिए · हिंदी चलेगी", V._fit("कमेंट में अपना काम लिखिए · हिंदी चलेगी", 40, PW - 120, "SemiBold"),
            dk, tag="cm")
    cv.text((PW // 2, 1298), V.TNC_TXT, V._fit(V.TNC_TXT, 30, PW - 120, "SemiBold"), dk, tag="tnc")
    # jaanch: koi likha bahar/chadha nahi, mana shabd nahi
    bad = []
    for b, s, tag in cv.boxes:
        if b[0] < 20 or b[2] > PW - 20 or b[1] < 20 or b[3] > PH - 10:
            bad.append(f"'{s[:16]}' bahar")
    bx = [(b, s) for b, s, _ in cv.boxes]
    for i in range(len(bx)):
        for j in range(i + 1, len(bx)):
            A, B = bx[i][0], bx[j][0]
            if min(A[2], B[2]) - max(A[0], B[0]) > 8 and min(A[3], B[3]) - max(A[1], B[1]) > 8:
                bad.append(f"'{bx[i][1][:12]}'+'{bx[j][1][:12]}' chadhe")
    im.convert("RGB").save(path, quality=90)
    return items, bad


def caption(brand, day, items):
    import re
    from . import svc, svcvideo as V
    by = svc.rates()["by"]
    up = V.usp_pct()
    i0 = (datetime.date.fromisoformat(day).toordinal() + list(BRANDS).index(brand)) % len(CAPS)
    head = CAPS[i0]
    if "{p}" in head and up < 50:
        head = CAPS[0]
    head = head.replace("{p}", str(up))
    lines = [f"• {V.KAAM.get(k, (by[k]['name'],))[0]} — ₹{by[k]['price']:,} से" for k in items]
    link = f"{SITE_LIST}?utm_source=facebook&utm_medium=post&utm_campaign={brand}_svc"
    code = V.CODES.get(brand, "")
    cap = (f"{head}\n" + "\n".join(lines) +
           f"\n\n👉 पूरी लिस्ट (1000+ काम): {link}\n💬 कमेंट में अपना काम लिखिए — हम बात करके लिखित रेट देंगे।"
           + (f"\n🏷 कोड {code} = 10% तक छूट" if code else "")
           + "\n* शर्तें लागू: sabhisaab.com/terms#rate\n#SabHisaabServices #DigitalSeva #OnlineMadad")
    hit = [p for p in V.BAN if re.search(p, cap, re.I)]
    return cap, hit


# ---------------------------------------------------------------- roz ka kaam
def post_one(brand, force=False):
    from . import meta as M, tg
    d = str(_now().date())
    done = state.get("svc_post_day") or {}
    if done.get(brand) == d and not force:
        return f"{BRANDS[brand]['name']}: aaj ki services post pehle hi ja chuki"
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{brand}_{d}.jpg"
    items, bad = card(brand, d, p)
    cap, hit = caption(brand, d, items)
    if bad or hit:
        tg.alert("yellow", f"🖼 {BRANDS[brand]['name']} ki services post jaanch mein ruki (post NAHI ki): {'; '.join(bad + hit)[:300]}")
        return "ruki"
    state.update("svc_post_day", lambda x: {**(x or {}), brand: d}, {})   # pehle nishan: dohri post kabhi nahi
    try:
        pid = M.post_fb_photo(brand, str(p), cap)
        url = f"https://www.facebook.com/{pid}"
        _log(brand, d, items, url)
        return f"✅ {BRANDS[brand]['name']}: services post FB par {url}"
    except Exception as e:
        _log(brand, d, items, f"fail: {str(e)[:120]}")
        tg.alert("yellow", f"🖼 {BRANDS[brand]['name']} ki services FB post nahi gayi: {str(e)[:200]}")
        return "fail"


def _log(brand, d, items, res):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "posts.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"), "day": d, "brand": brand, "items": items,
                            "res": res}, ensure_ascii=False) + "\n")


def tick(run):
    """Bot loop se har minute: jis brand ka pakka samay aa gaya (aur 90 min se zyada nahi beeta) - ek post."""
    if not on() or state.get("paused"):
        return
    n = _now()
    d, hm = str(n.date()), n.strftime("%H:%M")
    if (state.get("svc_holiday_until") or "") >= d:
        return
    done = state.get("svc_post_day") or {}
    for b, t in times().items():
        if done.get(b) == d or hm < t or _mins(hm) - _mins(t) > 90:
            continue
        if time.time() - float(state.get("svc_post_try") or 0) < 120:
            return
        state.put("svc_post_try", time.time())
        run(post_one, b)
        return


def fb_photo_today(brand):
    """Purani 'sawal photo-post': services post chalu ho to ek din chhod kar (FB feed mein ek din mein bahut post = spam jaisa)."""
    if not on():
        return True
    return (_now().date().toordinal() + list(BRANDS).index(brand)) % 2 == 0
