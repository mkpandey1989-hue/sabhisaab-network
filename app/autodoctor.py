"""v3.4.4 (16 Nov 2026 raat) - owner: "roz kahin na kahin kuch fail - ek fully automatic audit banao jo daily khud problem
sort out kare".

AUTO-DOCTOR: roz 05:40 (aur 'auto doctor' likhne par) har hissa JAANCHTA hai aur jo SURAKSHIT tareeke se theek ho sakta hai wo
KHUD theek karta hai. Phir ek hi sandesh: 🔧 khud theek kiya | ❌ aapka kaam (step-wise) | ✅ baaki sab theek.
Niyam: (1) sirf pehle se bane, jaanche hue raaste dobara chalata hai (deploy, /jawab publish, Bing sitemap, Threads token, owner-mode,
Google-jaanch) - naya content kabhi nahi likhta; (2) har sudhaar audit gate se (website._apply_zip / deploy jaise pehle);
(3) koi bhi jaanch fail ho to baaki chalti rehti hain; (4) ek din mein ek hi baar khud chalta hai.
"""
import datetime
import json
import shutil
import time

import requests

from . import state, tg
from .config import IST, SITE, DATA
from .log import log

HHMM = "05:40"


def _get(url, timeout=25):
    return requests.get(url, timeout=timeout, headers={"User-Agent": "SabHisaab-autodoctor", "Cache-Control": "no-cache"})


def run(manual=False):
    from . import website
    fixed, need, ok = [], [], []

    def chk(name, fn):
        try:
            fn()
        except Exception as e:
            log(f"autodoctor {name}: {e}")
            need.append(f"{name}: jaanch khud fail ({str(e)[:80]}) - 'Sab theek?' dabayein, na sudhre to Claude ko screenshot")

    # 1) website zinda + sitemap live = VM wali (kam ho to dobara deploy)
    def site():
        r = _get(SITE + "/")
        if r.status_code != 200:
            website.deploy()
            r2 = _get(SITE + "/")
            (fixed if r2.status_code == 200 else need).append(
                f"Website khul nahi rahi thi (HTTP {r.status_code}) → dobara deploy " + ("✅ ab khul rahi" if r2.status_code == 200 else
                "❌ phir bhi nahi - Cloudflare Pages → Deployments dekhein"))
            return
        live = website.live_sitemap_urls() or set()
        loc = (website.DIR / "site" / "sitemap.xml").read_text(encoding="utf-8").count("<url>")
        if live and len(live) < loc:
            website.deploy()
            live2 = website.live_sitemap_urls() or set()
            (fixed if len(live2) >= loc else need).append(
                f"Live sitemap mein {len(live)} URL, VM par {loc} → dobara deploy: ab {len(live2)}")
        else:
            ok.append(f"Website + sitemap ({len(live)} URL)")
    chk("Website", site)

    # 2) /jawab: naya jawab atka ho to dobara chadhao
    def jawab():
        from . import answers
        if not state.get("jawab_site_on"):
            return
        if state.get("answer_dirty"):
            r = answers.publish_site(force=True)
            good = not any(w in str(r).lower() for w in ("fail", "ruk", "error", "nahi", "pushti baaki"))
            (fixed if good else need).append(f"/jawab par naya jawab atka tha → {str(r)[:160]}")
        else:
            ok.append("/jawab")
    chk("/jawab", jawab)

    # 3) Bing sitemap ginti barabar (warna khud dobara bhejo)
    def bing():
        r = website.bing_feed(why="auto-doctor")
        if not r:
            return
        (fixed if "dobara bheja" in r else ok).append(r.replace("🗺 ", ""))
    chk("Bing", bing)

    # 4) Google index ka data aaj/kal ka? Purana -> jaanch dobara chalao
    def gidx():
        try:
            d = json.loads((website.DIR / "state" / "daily.json").read_text()).get("day")
        except Exception:
            d = None
        old = str(datetime.date.today() - datetime.timedelta(days=1))
        if not d or d < old:
            import threading
            threading.Thread(target=website.daily, daemon=True).start()
            fixed.append(f"Google index jaanch purani thi ({d}) → dobara shuru (report 30-60 min mein)")
        else:
            ok.append(f"Google index jaanch ({d})")
    chk("Google index", gidx)

    # 5) Threads token taaza (60 din) - khud refresh
    def threads():
        from . import threads as TH
        r = TH.refresh_all() or []
        bad = [x for x in r if x.startswith("🔴")]
        if bad:
            need.extend(x + " → bot mein 'threads login' / Claude ko screenshot" for x in bad)
        elif r:
            fixed.extend(r)
        else:
            ok.append("Threads login")
    chk("Threads", threads)

    # 6) Owner-mode / tracking sudhaar website par laga hai?
    def track():
        from . import trackfix
        r = trackfix.apply()
        if r and r.startswith("✅"):
            fixed.append("Owner-mode/tracking sudhaar website par dobara lagaya")
            state.put("trackfix_owner", True)
        elif r:
            need.append(r)
        else:
            ok.append("Owner-mode")
    chk("Owner-mode", track)

    # 7) Disk - 85% se upar to purane namoone/render saaf
    def disk():
        u = shutil.disk_usage(str(DATA))
        pct = u.used * 100 // max(1, u.total)
        if pct >= 85:
            from . import studio
            n = studio.cleanup(days=1)
            u2 = shutil.disk_usage(str(DATA))
            p2 = u2.used * 100 // max(1, u2.total)
            (fixed if p2 < 85 else need).append(f"Disk {pct}% bhari → {n} purane namoone mitaye, ab {p2}%"
                                                 + ("" if p2 < 85 else " - 'vm audit' likhein"))
        else:
            ok.append(f"Disk {pct}%")
    chk("Disk", disk)

    # 8) Atki video: manzoor hui, samay 2 ghante pehle nikal gaya, par gayi nahi
    def stuck():
        from . import pipeline
        now = pipeline.now()
        bad = []
        for jid, j in (pipeline.jobs() or {}).items():
            if j.get("status") in ("approved", "queued") and j.get("slot"):
                try:
                    sl = datetime.datetime.fromisoformat(j["slot"])
                except Exception:
                    continue
                if now - sl > datetime.timedelta(hours=2) and not (j.get("done") or {}).get("youtube"):
                    bad.append(f"{jid} ({j.get('brand')}, {sl:%d %b %H:%M})")
        if bad:
            need.append("Ye manzoor video samay nikalne ke 2 ghante baad bhi nahi gayi: " + ", ".join(bad[:5])
                        + " → '⏳ Pending' dabayein; wahan '🚀 Abhi daalo' ya '❌ Mat daalo'")
        else:
            ok.append("Video line")
    chk("Video", stuck)

    # 9) v3.4.7: Claude ke jaanche website sudhaar (ek baar, audit gate) - /uttarakhand toote link, FIRE title, TDEE guide link
    def sitefix():
        from . import webfix347 as sitepatch
        r = sitepatch.apply()
        if r and r.startswith("⚠️"):
            need.append(r)
        elif r:
            fixed.append(r)
    chk("Website sudhaar", sitefix)

    # 10) v3.4.7: aaj ki Google indexing suchi gayi? (11:40 ke baad, din mein ek baar - na gayi ho to khud bhejo)
    def idx():
        from . import idxlink
        if idxlink.due():
            state.put("idx_day", str(datetime.date.today()))
            r = idxlink.run()
            if r:
                tg.say(r)
                fixed.append("Aaj ki Google indexing suchi (seedhe link) bheji")
    chk("Indexing link", idx)

    state.put("ad_last", {"at": time.time(), "fixed": len(fixed), "need": len(need)})
    if not manual and not fixed and not need:
        log("autodoctor: sab theek")
        return None
    L = [f"🩺 AUTO-DOCTOR ({datetime.datetime.now(IST):%d %b %H:%M}) - roz ki khud-jaanch + khud-sudhaar"]
    if fixed:
        L.append("\n🔧 KHUD THEEK KIYA:")
        L += [f"• {x}" for x in fixed]
    if need:
        L.append("\n❌ AAPKA KAAM:")
        L += [f"• {x}" for x in need]
    L.append(f"\n✅ Theek: {', '.join(ok)}" if ok else "")
    return "\n".join(x for x in L if x)


def due(now=None):
    now = now or datetime.datetime.now(IST)
    return now.strftime("%H:%M") >= HHMM and state.get("ad_day") != str(now.date()) and state.get("ad_on", True)


def on_text(tl, run_bg):
    if tl in ("auto doctor", "autodoctor", "khud jaanch", "self audit", "auto audit"):
        tg.say("🩺 Har hissa jaanch raha hoon, jo surakshit ho khud theek karunga (2-5 min)...")
        return run_bg(lambda: tg.say(run(manual=True) or "✅ Sab theek."))
    if tl in ("auto doctor band", "auto doctor chalu"):
        state.put("ad_on", tl.endswith("chalu"))
        return tg.say("🩺 Roz 05:40 ka auto-doctor: " + ("CHALU" if tl.endswith("chalu") else "BAND"))
    return None
