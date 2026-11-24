"""v3.9.3 (owner 24 Nov): MASTER SCHEDULE - kaun si reel / post / story / report kab, ek button par.

Pakka: 25 Nov 2026 se. Reel ka samay pehle se dohri pushti se hi badalta tha ('schedule money 12:30,20:30').
Services post ka samay bhi ab pakka - badlna: 'post samay pahadi 19:30' -> ✅✅ dohri pushti. Bina pushti kuch nahi badalta.
"""
import datetime

from . import state
from .config import BRANDS

SINCE = "2026-11-25"


def _svc_slot(brand, day):
    try:
        from . import svcvideo
        return svcvideo.pick_day(day=day)[brand]["slot"]
    except Exception:
        return "?"


def text():
    from . import pipeline, svcpost, svcvideo
    n = pipeline.now()
    d, d2 = str(n.date()), str(n.date() + datetime.timedelta(days=1))
    sch = pipeline.schedule()
    pt = svcpost.times()
    taken = (state.get("svc_taken") or {}).get(d) or {}
    lk = state.get("sched_lock") or {}
    L = [f"🗓 MASTER SCHEDULE (IST) · 🔒 pakka" + (f" ({str(lk.get('t', ''))[:10]} se)" if lk.get("t") else "")
         + " - badlav sirf aapki dohri pushti se; update/restart se kabhi nahi",
         ("Har brand roz 2 reel: 1 sawal + 1 services. " if pipeline.one_sawal() else "") + "Post/story neeche.", ""]
    for b in BRANDS:
        reels = [x.strip() for x in str(sch.get(b, "")).split(",") if x.strip()]
        s1, s2 = _svc_slot(b, d), _svc_slot(b, d2)
        sv = "aapka namoona gaya (slot bhara)" if b in taken else s1
        fbp = "sawal photo-post aaj ✅" if svcpost.fb_photo_today(b) else "sawal photo-post kal"
        L.append(f"▪️ {BRANDS[b]['name']}")
        L.append(f"   🎬 Reel (sawal): {', '.join(reels)}  ·  🧾 Services reel: aaj {sv}, kal {s2}")
        L.append(f"   🖼 Services page-post (FB, link ke saath): {pt.get(b, '-')}  ·  {fbp}")
        L.append("   📲 Har reel ke saath: FB + IG story, Telegram channel, Threads; Pinterest/Dailymotion roz ki seema tak (services pehle)")
    L += ["",
          "⏱ Roz ke aur kaam (apne aap):",
          "   00:20-04:30 raat mein aaj ki saari reel ban kar line mein (slot khaali na rahe) · 01:30 services video ·",
          "   09:15 + 18:30 LinkedIn post · 19:15 share-kit · 20:30 jawab digest (agar chalu) · 21:00 story-sticker yaad ·",
          "   11:20 Google index jaanch · 23:58 services din ka hisaab · har 5 min services doctor · roz safai (purani badi file)",
          "",
          f"📌 Services reel ka slot har din brand badalta hai ({', '.join(svcvideo.SLOTS)}) - har channel ko sab samay milein.",
          "🛡 Spam se bachav: FB par brand ki roz max 1 services post; sawal photo-post ek din chhod kar; IG caption mein link nahi;",
          "   Pinterest roz ki seema (ek link par max 2) + Dailymotion seema - pehle services, normal video ki jagah kam.",
          "",
          "🧪 Aap koi reel bina schedule bhejo (namoona/abhi video): Thumb dabate hi bot poochhega 'aaj ki reel ki jagah gine ya extra?'",
          "   - jawab ke baad hi turant jaati hai; jawab na diya = nahi jaati, schedule waise hi chalta.",
          "Badalna: 'schedule pahadi 18:00' (reel) · 'post samay pahadi 19:30' (services post) - dono dohri pushti se.",
          "Band/chalu: 'services post band' / 'services post chalu'."]
    return "\n".join(L)


def on_text(t, run):
    """'master schedule' + services post ke hukum. -> True agar sambhala."""
    import re
    from . import tg, svcpost
    tl = t.lower().strip()
    if t in ("🗓 Master schedule",) or tl in ("master schedule", "master", "pura schedule", "poora schedule", "schedule button"):
        tg.say(text())
        return True
    if tl == "services post band":
        state.put("svc_post_on", False)
        tg.say("⏸ Services page-post band. Wapas: 'services post chalu'")
        return True
    if tl == "services post chalu":
        state.put("svc_post_on", True)
        tg.say("✅ Services page-post chalu (har brand roz 1, pakke samay par):\n" + "\n".join(
            f"• {BRANDS[b]['name']}: {x}" for b, x in svcpost.times().items()))
        return True
    m = re.match(r"(?:services )?post (?:samay|time) (\w+) ([0-2]?\d:[0-5]\d)$", tl)
    if m:
        b = next((k for k in BRANDS if k == m.group(1) or BRANDS[k]["name"].lower().startswith(m.group(1))), None)
        if not b:
            tg.say("Brand nahi pehchana (pahadi / money / deals / sunonatak)")
            return True
        hm = m.group(2).zfill(5)
        state.put("svc_post_pending", {"b": b, "t": hm})
        tg.say(f"⚠️ PAKKI SETTING: {BRANDS[b]['name']} ki services post {svcpost.times().get(b)} se {hm} karein?",
               tg.inline([[("✅ Haan", "mst:y1"), ("❌ Nahi", "mst:n")]]))
        return True
    if t == "🖼 Services post namoona" or tl in ("services post abhi", "services post namoona"):
        b = next(iter(BRANDS))
        p = svcpost.OUT / "namoona.jpg"
        svcpost.OUT.mkdir(parents=True, exist_ok=True)
        items, bad = svcpost.card(b, str(datetime.date.today()), p)
        cap, hit = svcpost.caption(b, str(datetime.date.today()), items)
        tg.photos([str(p)], ("❌ " + "; ".join(bad + hit) + "\n\n" if bad or hit else "") + cap[:900])
        return True
    return False


def on_cb(data):
    """Inline 'mst:*' (dohri pushti)."""
    from . import tg, svcpost
    p = state.get("svc_post_pending") or {}
    if data == "mst:n" or not p:
        state.put("svc_post_pending", None)
        return tg.say("❌ Kuch nahi badla.")
    if data == "mst:y1":
        return tg.say(f"⚠️ PAKKA? {BRANDS[p['b']]['name']} services post roz {p['t']} par.",
                      tg.inline([[("✅✅ Pakka", "mst:y2"), ("❌ Nahi", "mst:n")]]))
    if data == "mst:y2":
        t = dict(svcpost.times())
        t[p["b"]] = p["t"]
        state.put("svc_post_times", t)
        state.put("svc_post_pending", None)
        return tg.say(f"✅ {BRANDS[p['b']]['name']} services post ab roz {p['t']} par (pakka).")
    return None
