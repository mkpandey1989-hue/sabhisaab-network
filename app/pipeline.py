"""Video ka safar: topic -> script -> video -> audit -> Telegram manzoori -> YouTube upload -> seekh."""
import datetime
import json
import os
import pathlib
import random
import shutil
import time
import uuid
from . import tg, audit, topics, writer, learn, state, youtube
from .config import IST, SCHEDULE, PREPARE_HOURS, AUTO_APPROVE, MAX_UPLOADS_DAY, BRANDS, POSTED, SITE, STOCK
from .log import log


class _Wait(Exception):
    """Platform jaanboojh kar ruka (galti nahi)."""
from .render import render

BRAND_BTNS = [[("🎭 Suno Natak", "mk:sunonatak"), ("💰 Money", "mk:money")],
              [("🛍 Labh Lo Deals", "mk:deals"), ("🏔 Pahadi", "mk:pahadi")]]


def schedule():
    sch = {**SCHEDULE, **(state.get("schedule") or {})}
    if state.get("quiz_slot_on", True):           # v2.3.1: owner ne pehle ek hi samay rakha ho to bhi doosra sawal-slot
        from .config import QUIZ_SLOT
        for b, q in QUIZ_SLOT.items():
            if b in sch and len([x for x in str(sch[b]).split(",") if x.strip()]) < 2 and q not in str(sch[b]):
                sch[b] = f"{sch[b]},{q}"
    return sch


def max_uploads():
    return int(state.get("max_uploads") or MAX_UPLOADS_DAY)


def auto_on():
    v = state.get("auto_approve")
    return AUTO_APPROVE if v is None else v


def _similar(a, b):
    import difflib
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _sig(meta_or_script):
    import hashlib
    txt = "|".join(s.get("show", "") for s in meta_or_script.get("scenes", []))
    return hashlib.md5(txt.encode()).hexdigest()[:16]


def duplicate(brand, title, days=365, sig=None):          # v2.4.1: 365 din (owner)
    """Pichhle 90 din mein isi brand par milta-julta title YA bilkul wahi content (scenes) gaya hai?"""
    since = str((now() - datetime.timedelta(days=days)).date())
    for h in state.get("history", []):
        if h["date"] < since:
            continue
        if sig and h.get("sig") == sig:
            return h
        if h["brand"] == brand and _similar(h["title"], title) > 0.8:
            return h
    return None


def _qnorm(q):
    import re as _r
    return _r.sub(r"[\s\W_]+", "", str(q or "").lower())[:120]


def q_seen(q, thr=0.86):
    """v2.3.4: ye sawal (ya lagbhag yahi) kisi bhi channel par pehle bana? (sab channel ka ek register, 2000 sawal)"""
    n = _qnorm(q)
    if not n:
        return False
    import difflib
    for old in (state.get("q_registry") or [])[-2000:]:
        if old == n or (abs(len(old) - len(n)) < 25 and difflib.SequenceMatcher(None, old, n).ratio() >= thr):
            return True
    return False


def q_add(q):
    n = _qnorm(q)
    if n:
        state.update("q_registry", lambda L: ((L or []) + [n])[-6000:], [])
        state.update("q_recent", lambda L: ((L or []) + [str(q)[:90]])[-40:], [])


def _dup_of(brand, m):
    """v2.3.0: puzzle -> sawal-hash/sig se; baaki -> title + sig se."""
    if m.get("puzzle_hash"):
        return duplicate(brand, "\x00" + m["puzzle_hash"], sig=_sig(m))
    return duplicate(brand, m.get("title", ""), sig=_sig(m))


def now():
    return datetime.datetime.now(IST)


def jobs():
    return state.get("jobs", {})


def save_job(jid, job):
    state.update("jobs", lambda d: {**(d or {}), jid: job}, {})


def job_buttons(jid):
    return tg.inline([[("✅ Thumb 1", f"ok:{jid}:1"), ("✅ Thumb 2", f"ok:{jid}:2"), ("✅ Thumb 3", f"ok:{jid}:3")],
                      [("🎨 Naye thumbnail", f"nt:{jid}"), ("❌ Mat daalo", f"no:{jid}")],
                      [("🚀 Abhi daalo (Thumb 1)", f"go:{jid}:1")]])


def prepare(brand, slot_iso=None, reason="schedule", topic_text=None, fmt="short", style="", sample=None, script_in=None):
    """Video banao aur manzoori ke liye bhejo. Fail ho to bank script se ek aur koshish.
    v2.2.0: sample={..} = NAMOONA (Sample Studio) - kabhi post nahi; owner ka pakka look roz ki video par apne aap."""
    from .guardtext import clean_script          # v2.3.0: shuru mein (pehle loop ke andar tha -> bank-fallback UnboundLocalError)
    visual = ""
    if sample:
        visual = sample.get("visual", "")
    if not style and not sample and fmt == "short" and not topic_text:
        try:                                     # v2.2.0: din ka andaaz (weekplan) + owner ka pakka look (studio)
            from . import studio, weekplan
            lk = studio.approved(brand) or {}
            style = "; ".join(x for x in (weekplan.style_for(brand), lk.get("style", "")) if x)
            visual = lk.get("visual", "")
            if state.get("quiz_all", True):          # v2.3.1 (owner): har reel sawal wali - neon vikalp ke saath
                from .writer import QUIZ_STYLE
                style = QUIZ_STYLE + ("; " + style if style else "")
        except Exception as e:
            log(f"brand look: {e}")
    jid = f"{brand[:3]}{uuid.uuid4().hex[:5]}"
    slot = slot_iso or (now() + datetime.timedelta(minutes=30)).isoformat()
    save_job(jid, {"brand": brand, "status": "making", "slot": slot, "created": now().isoformat(), "reason": reason})
    tg.say(f"🎬 {BRANDS[brand]['name']}: nayi {'LAMBI video (8-12 min, 30-60 min lagenge)' if fmt == 'long' else 'video'}"
           f" ban rahi hai ({reason}{', ' + ('sawal-slot: jaancha hua puzzle/GK' if style == '__puzzle__' else style[:60]) if style else ''})")
    if style == "__puzzle__":                     # v2.3.1: sawal-slot - jaancha hua puzzle / pahadi GK / purane shabd
        style = ""
        try:
            from . import puzzles
            script_in = puzzles.generate_puzzle("auto", brand)
            if brand == "pahadi" and script_in.get("puzzle_kind") not in ("pahadi_gk", "pahadi_shabd", "pahadi_purana"):
                script_in = None                 # pahadi bank khatam -> Gemini se naya pahadi GK sawal (Google se tathya-jaanch)
                from .writer import QUIZ_STYLE
                style = QUIZ_STYLE + "; vishay: Uttarakhand GK ya purane Garhwali/Kumaoni shabd (pakka tathya)"
        except Exception as e:
            log(f"quiz slot puzzle: {e}")
    if script_in is None and not sample and not topic_text and fmt == "short" and state.get("puzzles_on", True) \
            and not state.get("quiz_slot_on", True):
        try:                                      # v2.3.0 Step 4: (sirf jab sawal-slot band ho) challenge din -> puzzle
            from . import weekplan, puzzles
            if "challenge" in (weekplan.style_for(brand) or "").lower():
                script_in = puzzles.generate_puzzle("auto", brand)
        except Exception as e:
            log(f"challenge puzzle: {e}")
    for attempt in (1, 2, 3):
        topic = ({"key": f"custom:{topic_text}", "topic": topic_text, "page": "/", "kind": "custom"}
                 if topic_text and attempt == 1 else topics.next_topic(brand))
        if script_in is not None and attempt == 1:        # v2.3.0: pehle se bani script (puzzle) - writer nahi
            script = dict(script_in, brand=brand)
            topic = {"key": f"puzzle:{script.get('puzzle_hash', '')}", "topic": script.get("title", ""), "page": "/", "kind": "idea"}
        else:
            script = writer.write(brand, topic, fmt, style) if (attempt < 3 or fmt == "long") else _bank(brand)
        from .guardtext import clean_script      # v2.0.2: ginti/link/naam scene ke text mein bhi sahi
        script = clean_script(script)
        if script.get("puzzle_q") and not script.get("puzzle_hash") and q_seen(script["puzzle_q"]):
            log(f"prepare {brand}: ye sawal kisi channel par pehle aa chuka - naya chahiye")       # v2.3.4: sab channel mila kar
            script.pop("puzzle_options", None)
        if (fmt == "short" and not topic_text and state.get("quiz_all", True) and not script.get("puzzle_options")
                and "QUIZ FORMAT" in (style or "")):      # v2.3.3 (owner): purani kahani-wali reel kabhi nahi - sirf sawal wali
            log(f"prepare {brand}: script mein 4 vikalp nahi (koshish {attempt}) - sawal wali chahiye")
            if attempt < 3:
                continue
            from . import puzzles as _PZ             # aakhri raasta: jaancha hua puzzle/GK (slot nahi tootega)
            script = clean_script(_PZ.generate_puzzle("auto", brand))
        if visual and visual != "neon":           # v2.3.0 Step 2: pakka/namoona visual style
            script["visual_style"] = visual
        if sample and sample.get("layout"):       # v2.4.0: naye layout ka namoona
            script["layout"] = sample["layout"]
        elif not script.get("layout"):
            ok_l = ["list"] + [x for x in (state.get("layouts_ok") or []) if x != "list"]
            script["layout"] = ok_l[(now().toordinal() * 3 + list(BRANDS).index(brand)) % len(ok_l)]
        if sample and sample.get("palette"):      # v2.3.6: naye rang ka namoona
            script["palette"] = sample["palette"]
        elif not script.get("palette"):           # pakke rangon mein roz baari-baari (channel + din se)
            ok_p = [p for p in (state.get("palettes_ok") or []) if p]
            if ok_p:
                opts = [None] + ok_p
                script["palette"] = opts[(now().toordinal() + list(BRANDS).index(brand)) % len(opts)]
        if fmt == "short" and not script.get("design") and state.get("neon_default", True) and visual in ("", "neon"):
            script["design"] = "neon_quiz"            # v2.3.0: owner ke reference jaisa premium neon (naya default)
        if fmt == "short" and script.get("puzzle_options"):   # v2.5.0: jawab video mein nahi - website/Telegram par
            from . import answers as _ANS
            script = _ANS.strip_reveal(script)
        if script.get("design") == "neon_quiz" and not script.get("img3d"):
            try:                                      # v2.3.3: APNA 3D (Blender) - Gemini ke bina, har reel ka 3D chitra
                from . import blender3d, design as _DS
                script["fmt_style"] = style
                acc = "%02x%02x%02x" % _DS._acc(brand)[0]
                p3 = blender3d.ai_art(script, accent=acc)         # v2.4.0: pehle AI-art (sample jaisa), phir Blender
                if p3:
                    script["img_src"] = "Cloudflare Workers AI (Flux) - AI chitra"
                elif blender3d.available():
                    p3 = blender3d.render(script, accent=acc)
                    if p3:
                        script["img_src"] = "Blender 3D (apna)"
                if p3:
                    script["img3d"] = str(p3)
            except Exception as e:
                log(f"3d: {e}")
        if "challenge" in (style or "").lower() or script.get("puzzle_kind"):     # v11 HUD: timer + chhupa code (sirf challenge)
            script["hud"] = {"timer": True, "rewatch": random.randint(11, 99)}
        if script.get("puzzle_kind"):              # v2.4.1: paheli -> hamesha home (galat page jaise googleXXXX nahi)
            script["page"] = "/"
        elif topic.get("page", "/") == "/" and topic.get("kind") != "page" and script.get("page", "/") in ("/", "", None):
            try:                                     # v2.0.2: website se bahar ka topic -> sabse milta tool/guide page
                from . import siteknow
                hit = siteknow.find(f"{topic.get('topic', '')} {script.get('title', '')}", 1)
                if hit:
                    script["page"] = "/" + hit[0][0]
            except Exception:
                pass
        dup = (duplicate(brand, "\x00" + script.get("puzzle_hash", ""), sig=_sig(script)) if script.get("puzzle_hash")
               else duplicate(brand, script.get("title", ""), sig=_sig(script)))   # v2.3.0: puzzle ka asli sawal-hash
        if dup:                                   # jaanch 1: pehle ja chuka?
            tg.alert("green", f"Milta-julta title {dup['date']} ko ja chuka, naya topic le raha hoon.")
            topics.mark_used(topic["key"])
            continue
        from . import audit_ai                    # jaanch 2+3: kanoon/samaj + tathya (Google search)
        ok_ai, notes = audit_ai.check(brand, script)
        if not ok_ai:
            tg.alert("green", f"🛡 {BRANDS[brand]['name']}: script roki ({'; '.join(notes)[:250]}). Naya topic le raha hoon.")
            topics.mark_used(topic["key"])
            continue
        from .config import DATA
        cl = sorted((DATA / "clips" / brand).glob("*.mp4")) if (DATA / "clips" / brand).exists() else []
        if cl and (state.get("use_clips_next") == brand or (fmt != "long" and len(cl) >= 2 and random.random() < 0.5)):
            state.put("use_clips_next", "")
            script["clips"] = [str(c) for c in random.sample(cl, min(len(cl), len(script["scenes"])))]
        gal = sorted((DATA / "photos" / brand).glob("*.jpg")) if (DATA / "photos" / brand).exists() else []
        if gal and not script.get("clips") and not state.get("no_gallery_reels") and (     # v2.3.0: owner 'in photos se reels mat banana'
                state.get("use_photos_next") == brand or (brand == "pahadi" and len(gal) >= 3)):
            state.put("use_photos_next", "")
            used = state.get("photo_used") or {}
            gal = sorted(gal, key=lambda g: used.get(g.name, 0))[:len(script["scenes"])]
            script["photos"] = [str(g) for g in gal]        # aapki asli photo = original content (policy mein madad)
            for g in gal:
                used[g.name] = used.get(g.name, 0) + 1
            state.put("photo_used", used)
        if not script.get("photos") and not script.get("clips") and state.get("ai_images", True):
            try:                 # premium 3D AI background (Gemini image) - free na mile to purana design
                from . import imagegen
                from .config import TMP
                imgs = []
                for k in range(min(3, len(script["scenes"]))):
                    o = imagegen.make(f"{script['title']} - {script['scenes'][k]['show'][:120]}",
                                      TMP / f"ai_{jid}_{k}.png", brand_key=brand,
                                      style_name=(visual if visual not in ("", "classic", "neon") else "auto"), scene_idx=k,
                                      procedural_fallback=bool(visual and visual not in ("classic", "neon")))
                    if not o:
                        break
                    imgs.append(str(o))
                if imgs:
                    script["photos"] = imgs
                    script["ai_images"] = True
            except Exception as e:
                log(f"ai images: {e}")
        from . import guard as _G               # v2.0.2: slot ke paas VM busy ho to bhi 1 core par bana do (post na chhoote)
        try:
            _G.set_deadline(datetime.datetime.fromisoformat(slot).timestamp() - 40 * 60)
        except Exception:
            _G.set_deadline(None)
        meta = render(script, notify=tg.say)
        _G.set_deadline(None)
        meta["ai_audit"] = notes
        checks = audit.run(meta)
        if meta.get("page_broken"):          # v1.8: toota page link -> homepage, meta mein bhi pakka
            try:
                (pathlib.Path(meta["video"]).parent / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
            except Exception as e:
                log(f"meta save: {e}")
        if audit.passed(checks):
            break
        tg.say("❌ Audit fail, doosri script se koshish:\n" + "\n".join(f"{c} {m}" for c, m in checks if c == "❌"))
    else:
        save_job(jid, {**jobs()[jid], "status": "failed"})
        if reason == "roz ka schedule" and not str(reason).endswith("(dobara)"):
            tg.alert("yellow", f"{BRANDS[brand]['name']}: 3 koshish fail - taiyaar script bank se aakhri koshish (slot na chhoote).")
            try:                                 # v2.0.2: koi bhi karan ho, schedule ki video jaaye
                sc = clean_script(_bank(brand))
                meta = render(sc, notify=tg.say)
                checks = audit.run(meta)
                if audit.passed(checks):
                    topic = {"key": f"bank:{now().date()}:{brand}", "kind": "idea"}
                    save_job(jid, {**jobs()[jid], "status": "making"})
                    script = sc
                else:
                    raise RuntimeError("bank script bhi audit fail")
            except Exception as e:
                sp = _take_spare(brand)                 # v2.3.0: pehle se bani spare reel (slot kabhi na chhoote)
                if sp:
                    meta, checks = sp
                    script = meta
                    topic = {"key": f"spare:{now().date()}:{brand}", "kind": "idea"}
                    save_job(jid, {**jobs()[jid], "status": "making"})
                    tg.alert("green", f"🎞 {BRANDS[brand]['name']}: pehle se bani spare reel le li (slot nahi chhoota).")
                else:
                    save_job(jid, {**jobs()[jid], "status": "failed"})
                    tg.alert("red", f"{BRANDS[brand]['name']}: aaj ki video nahi ban payi ({str(e)[:120]}). Galti ESCALATE.md mein.")
                    return None
        else:
            tg.alert("red", f"{BRANDS[brand]['name']}: 3 koshish ke baad bhi video audit paas nahi hui.")
            return None
    if sample:                                   # v2.2.0: namoona - manzoori/upload line mein kabhi nahi
        job = {**jobs()[jid], "status": "sample", "sample": sample, "meta": meta["video"].rsplit("/", 1)[0],
               "title": meta["title"], "style": style}
        save_job(jid, job)
        from . import studio
        studio.send(jid, meta, checks, sample)
        return jid
    if meta.get("puzzle_q"):
        q_add(meta["puzzle_q"])                   # v2.3.4/2.3.5: har sawal (Gemini + bank + puzzle) register mein
    try:                                          # v2.4.0: provenance ledger (copyright saboot)
        from . import ops as _OPS
        _OPS.provenance({**meta, "audit_notes": " | ".join(str(x) for x in (locals().get("notes") or []))[:200]},
                        script.get("img_src", ""))
    except Exception as e:
        log(f"provenance: {e}")
    job = {**jobs()[jid], "status": "waiting", "meta": meta["video"].rsplit("/", 1)[0], "topic_key": topic["key"],
           "ai_audit": meta.get("ai_audit", []),
           "topic_kind": topic.get("kind", "idea"), "style": style,
           "title": meta["title"], "source": script.get("source")}
    save_job(jid, job)
    _send_for_approval(jid, meta, checks)
    return jid


def _bank(brand):
    import glob
    files = sorted(glob.glob(str(writer.BANK / f"{brand}_*.json")))
    used = [h.get("sig") for h in state.get("history", [])]
    fresh = [f for f in files if _sig(json.loads(pathlib.Path(f).read_text(encoding="utf-8"))) not in used]
    if not fresh:
        raise RuntimeError("Bank ki saari script pehle ja chuki hain (dobara nahi daalenge); Gemini se nayi chahiye")
    s = json.loads(pathlib.Path(random.choice(fresh)).read_text(encoding="utf-8"))
    s["source"] = "bank"
    writer.quiz_fields(s)                        # v2.3.3: bank ki sawal-wali script ke vikalp bhi
    return s


def _meta(job):
    return json.loads((pathlib.Path(job["meta"]) / "meta.json").read_text())


def _send_for_approval(jid, meta, checks):
    slot = datetime.datetime.fromisoformat(jobs()[jid]["slot"])
    try:
        tg.video(meta["video"], f"{meta['title']}\n⏱ {meta['duration']:.0f}s | {BRANDS[meta['brand']]['name']}",
                 meta["thumbs"][0])
    except Exception as e:
        tg.say(f"⚠️ Video preview nahi gaya (network): {e}")
    tg.photos(meta["thumbs"], "🖼 Thumb 1 / 2 / 3")
    auto = (f"\n⏰ Jawab na mila to {slot:%H:%M} par Thumb 1 se apne aap upload."
            if auto_on() and jobs()[jid].get("reason") in ("roz ka schedule", "hafte ki lambi video", "schedule")
            else "\n🔒 Ye aapki/test video hai: aapke button dabaye bina kahin nahi jayegi.")
    tg.alert("yellow", f"Manzoori chahiye\n🆔 {jid} | {BRANDS[meta['brand']]['name']}\n📝 {meta['title']}\n"
             f"✅ Audit pass ({len(checks)} jaanch){auto}\n\nKaun sa thumbnail daalein?", job_buttons(jid))


def new_thumbs(jid):
    from .thumbs import make
    job = jobs()[jid]
    meta = _meta(job)
    t = meta.get("thumb") or {"lines": [meta["title"]]}
    t = dict(t, emoji="")   # naye emoji bhi
    if meta.get("design") == "neon_quiz":           # v2.3.2: 'Naye thumbnail' bhi wahi pakka neon design (pehle purana aa jaata tha)
        from . import design as _DS
        _DS.use_palette(meta.get("palette"))
        k0 = int(time.time()) % 97
        meta["thumbs"] = [str(_DS.thumbnail(meta, pathlib.Path(job["meta"]) / f"thumb_n{k0}_{k}.jpg", k0 + k)) for k in range(3)]
    else:
        meta["thumbs"] = [str(p) for p in make(meta["brand"], t, job["meta"], meta["title"] + str(time.time()))]
    (pathlib.Path(job["meta"]) / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    tg.photos(meta["thumbs"], f"🎨 Naye thumbnail ({jid})")
    tg.say("Kaun sa daalein?", job_buttons(jid))


def approve(jid, thumb, now_flag=False):
    job = jobs().get(jid)
    if not job or job["status"] not in ("waiting", "approved"):
        return "Ye video ab manzoori mein nahi hai."
    job.update(status="approved", thumb=int(thumb), now=now_flag)
    save_job(jid, job)
    when = "abhi" if now_flag else datetime.datetime.fromisoformat(job["slot"]).strftime("%H:%M par")
    return f"👍 Thumb {thumb} chuna. Upload {when}."


def reject(jid):
    job = jobs().get(jid)
    if job:
        job["status"] = "rejected"
        save_job(jid, job)
        shutil.rmtree(job.get("meta", ""), ignore_errors=True)
    return "🗑 Video hata di. Is slot ke liye nayi video chahiye to 🎬 Abhi video dabayein."


def uploads_today():
    d = str(now().date())
    return state.get("uploads", {}).get(d, 0)


BRAND_PAGE_WORDS = {      # v2.1.6: brand ki video ka link usi mizaaj ka page ho (Pahadi shabd → bike loan EMI nahi)
    "pahadi": ("bigha", "nali", "zameen", "land", "uttarakhand", "pahadi", "acre", "area", "khasra", "farmer", "kheti",
               "yojana", "muthi", "jamin", "hectare", "biswa", "plot"),
    "money": ("sip", "fd", "emi", "loan", "tax", "salary", "pf", "ppf", "mutual", "interest", "rd", "gold", "gratuity",
              "retire", "invest", "nps", "hra", "income", "inflation", "fund", "bachat", "savings", "compound", "da-"),
    "deals": ("discount", "gst", "price", "emi", "offer", "cashback", "road", "mileage", "percent", "sale", "loan", "fuel",
              "electricity", "bill", "tip", "split", "unit"),
}


def check_link(meta):
    """Website ka page khulta hai? Na khule to homepage. Brand se mel na khaye to bhi homepage."""
    import requests
    pg_ = meta.get("page", "/") or "/"
    words = BRAND_PAGE_WORDS.get(meta.get("brand", ""))
    if words and pg_ != "/" and not any(w in pg_.lower() for w in words):
        log(f"page mel nahi khata ({meta.get('brand')}: {pg_}) - homepage")
        meta["page"] = "/"
    url = f"{SITE}{meta.get('page', '/')}"
    try:
        ok = requests.get(url, timeout=20, allow_redirects=True).status_code == 200
    except Exception:
        ok = False
    if not ok and meta.get("page", "/") != "/":
        tg.say(f"⚠️ Website page nahi khula ({url}), homepage link lagaya.")
        meta["page"] = "/"
    return meta


def _channel_post(meta, links):
    import json as _j
    from .config import TG_CHANNEL
    b = BRANDS[meta["brand"]]
    rows = [[{"text": "🌐 Free calculator", "url": f"{SITE}{meta.get('page', '/')}?utm_source=telegram&utm_medium=channel&utm_campaign={meta['brand']}"}]]
    if links.get("youtube"):
        rows.append([{"text": "▶️ YouTube par dekhein", "url": links["youtube"]}])
    from .config import WHATSAPP
    rows.append([{"text": "💬 WhatsApp channel", "url": WHATSAPP}])
    cap = f"{meta['title']}\n\n{b['name']} | {b['footer']}\n🌐 {SITE}{meta.get('page', '/')}"
    with open(links.get("_thumb") or meta["thumbs"][0], "rb") as f:     # wahi chuna hua thumbnail
        r = tg.call("sendPhoto", {"chat_id": TG_CHANNEL, "caption": cap[:1000], "reply_markup": _j.dumps({"inline_keyboard": rows})},
                    {"photo": f})
    links["_tgid"] = (r or {}).get("message_id")
    return f"https://t.me/{TG_CHANNEL.lstrip('@')}/{links['_tgid']}" if links.get("_tgid") else f"https://t.me/{TG_CHANNEL.lstrip('@')}"


def _story_card(brand, meta):
    """v2.3.6: story bhi naye neon design mein - sawal + vikalp (jawab nahi; reel dekhne ka kaaran)."""
    from PIL import Image
    d = pathlib.Path(meta["video"]).parent
    card = d / "story.png"
    if meta.get("design") == "neon_quiz":
        from . import design as _DS
        _DS.use_palette(meta.get("palette"))
        _DS.use_layout(meta.get("layout"))
        bg, fr = d / "story_bg.jpg", d / "story_fr.png"
        _DS.background(brand, meta.get("title", "") + "s", bg)
        if meta.get("img3d"):
            _DS.blend_3d_bg(bg, meta["img3d"])
        n = len(meta.get("scenes") or [1])
        _DS.body_frame(meta, 1 if meta.get("puzzle_options") else 0, max(n, 2), fr)
        im = Image.open(bg).convert("RGBA")
        im.alpha_composite(Image.open(fr))
        im.convert("RGB").save(card)
    else:
        from .render import scene_frame
        scene_frame(brand, meta["title"], "Nayi video aa gayi! Profile par dekhein aur free calculator: https://sabhisaab.com/", 0, 1, card)
    return card


def _fb_photo_daily(brand, meta):
    """v2.3.6: har page par roz 1 photo-post (sawal wala thumbnail + jawab reel mein + link) - FB 'photo posts' kaam."""
    from . import meta as M
    day = str(now().date())
    if not state.get("fb_photo_daily", True) or (state.get("fb_photo_day") or {}).get(brand) == day:
        return ""
    th = (meta.get("thumbs") or [None])[0]
    if not th:
        return ""
    q = meta.get("puzzle_q") or meta.get("title", "")
    cap = (f"🧠 {q}\n\nAapka jawab kya hai? Comment karein 👇\nSahi jawab hamari nayi reel mein (page par).\n\n"
           f"Aise hi free calculator aur paheliyan: https://sabhisaab.com/")
    try:
        pid = M.post_fb_photo(brand, th, cap)
        state.update("fb_photo_day", lambda d_: {**(d_ or {}), brand: day}, {})
        return f"FB photo-post {str(pid)[:20]}"
    except Exception as e:
        return f"FB photo-post nahi ({str(e)[:60]})"


def _stories(brand, meta, vpath):
    """Nayi video ki khabar: FB story (card) + IG story (video, 60s tak) + roz 1 FB photo-post. Fail ho to bas note."""
    from . import meta as M
    res = []
    try:
        card = _story_card(brand, meta)
        res.append(M.fb_photo_story(brand, card))
    except Exception as e:
        res.append(f"FB story nahi ({str(e)[:60]})")
    try:
        r_ = _fb_photo_daily(brand, meta)
        if r_:
            res.append(r_)
    except Exception as e:
        res.append(f"FB photo-post nahi ({str(e)[:60]})")
    try:                                          # v2.3.6: WhatsApp channel ka API nahi - roz 1 taiyaar post aapko (bas forward)
        day = str(now().date())
        if state.get("wa_ready", True) and state.get("wa_ready_day") != day and meta.get("thumbs"):
            state.put("wa_ready_day", day)
            q = meta.get("puzzle_q") or meta.get("title", "")
            tg.photos([str(meta["thumbs"][0])], f"📲 WhatsApp channel ke liye taiyaar (bas forward/copy karein):\n\n🧠 {q}\n"
                                                 "Jawab socho aur reply karo! Sahi jawab + free calculator 👉 https://sabhisaab.com/")
    except Exception as e:
        log(f"wa ready: {e}")
    try:
        if meta.get("duration", 99) <= 60:
            res.append(M.ig_video_story(brand, vpath))
    except Exception as e:
        res.append(f"IG story nahi ({str(e)[:60]})")
    return ", ".join(res)


# ---------------- v2.3.0 Step 1 (v11 se, aur pakka): har platform ka post-taala (do baar kabhi nahi) ----------------
def _lock_key(brand, platform, sig):
    return f"{now().date()}:{brand}:{platform}:{sig}"


def acquire_post_lock(brand, platform, sig):
    """v11 jaisa naam/kaam: True = daal sakte ho. Do-charan: 'trying' -> 'done' (safal) / hata (fail).
    Bot beech post mein ruk gaya tha (purana 'trying') -> dobara NAHI (shayad pehle gaya) - owner ko khabar."""
    st = post_lock_state(brand, platform, sig)
    if st in ("done", "unsure", "busy"):
        return False
    k = _lock_key(brand, platform, sig)
    keep = str((now() - datetime.timedelta(days=7)).date())
    state.update("post_locks", lambda d: {**{a: b for a, b in (d or {}).items() if a[:10] >= keep},
                                          k: {"st": "trying", "pid": os.getpid(), "t": now().isoformat(timespec="seconds")}}, {})
    return True


def post_lock_state(brand, platform, sig):
    v = (state.get("post_locks") or {}).get(_lock_key(brand, platform, sig))
    if not v:
        return "free"
    if isinstance(v, str) or v.get("st") == "done":
        return "done"
    return "busy" if v.get("pid") == os.getpid() else "unsure"


def post_lock_done(brand, platform, sig, ok=True):
    k = _lock_key(brand, platform, sig)
    if ok:
        state.update("post_locks", lambda d: {**(d or {}), k: {"st": "done", "t": now().isoformat(timespec="seconds")}}, {})
    else:
        state.update("post_locks", lambda d: {a: b for a, b in (d or {}).items() if a != k}, {})


def _locked_post(brand, platform, sig, done, errs, fn):
    """fn() -> done text. Taala ke saath: pehle gaya / shayad gaya -> dobara nahi."""
    st = post_lock_state(brand, platform, sig)
    if st == "done":
        done[platform] = "✓ pehle hi ja chuka (post-taala)"
        return
    if st == "unsure":
        done[platform] = "⚠ pichhli baar beech mein ruka - dobara NAHI daala (shayad pehle gaya; aap ek baar dekh lein)"
        tg.alert("yellow", f"{BRANDS[brand]['name']} {platform}: bot post ke beech ruka tha. Do baar na jaye isliye dobara nahi daala - "
                           "ek baar app mein dekh lein.")
        post_lock_done(brand, platform, sig, ok=True)
        return
    if not acquire_post_lock(brand, platform, sig):
        errs[platform] = "abhi isi post par kaam chal raha (taala)"
        return
    try:
        done[platform] = fn()
        post_lock_done(brand, platform, sig, ok=True)
    except Exception:
        post_lock_done(brand, platform, sig, ok=False)
        raise


def upload(jid, pre=False):
    """Har platform alag: jo ho chuka wo dobara nahi. Ek fail ho to baaki chalte rahein.
    pre=True: sirf YouTube par slot ke samay ke liye schedule (baaki platform theek slot par)."""
    from . import meta as M
    job = jobs()[jid]
    brand = job["brand"]
    if uploads_today() >= max_uploads() and "youtube" not in job.get("done", {}):
        tg.say(f"⏳ Aaj ki upload seema ({max_uploads()}) poori. {jid} kal subah jayegi.")
        job["slot"] = (now() + datetime.timedelta(hours=12)).replace(hour=9, minute=0).isoformat()
        job["status"] = "approved"
        save_job(jid, job)
        return
    meta = check_link(_meta(job))
    if "youtube" not in job.get("done", {}):
        dup = (duplicate(brand, "\x00" + meta.get("puzzle_hash", ""), sig=_sig(meta)) if meta.get("puzzle_hash")
               else duplicate(brand, meta["title"], sig=_sig(meta)))
        if not dup and youtube.has_login(brand) and not meta.get("puzzle_hash"):   # jaanch 3 (puzzle: sawal-hash hi kaafi)
            try:
                for t_, v_ in youtube.recent_titles(brand):
                    if _similar(t_, meta["title"]) > 0.8:
                        dup = {"date": "channel par", "title": t_}
                        break
            except Exception as e:
                log(f"recent titles: {e}")
        if dup:
            job["status"] = "rejected"
            save_job(jid, job)
            return tg.alert("yellow", f"{jid}: milti-julti video pehle ja chuki hai ({dup.get('date')}: {dup.get('title', '')[:50]}). "
                                      "Dobara nahi daali.")
    thumb = meta["thumbs"][int(job.get("thumb", 1)) - 1]
    vpath = pathlib.Path(meta["video"])
    if meta.get("format") != "long":           # Shorts: chuna hua thumbnail cover frame ban kar sab platform par
        final = pathlib.Path(job["meta"]) / "final.mp4"
        if not final.exists():
            try:
                from .thumbs import vertical_cover
                from .render import add_cover
                variants = json.loads((pathlib.Path(job["meta"]) / "thumbs.json").read_text())
                cv = vertical_cover(brand, meta.get("thumb") or {"lines": [meta["title"]]},
                                    variants[int(job.get("thumb", 1)) - 1], pathlib.Path(job["meta"]) / "cover.png")
                add_cover(vpath, None, final, cover_png=cv)
            except Exception as e:
                log(f"cover: {e}")
        if final.exists():
            vpath = final
    done = dict(job.get("done", {}))
    prev_keys = set(done)                         # v2.1.4: dobara koshish mein sirf naya batao (pehle poora report baar-baar)
    prev_errs = dict(job.get("last_errs") or {})
    ids = dict(job.get("ids", {}))
    for pf in (state.get("platform_off") or {}).get(brand, []):     # aapne is brand ke liye ye platform band kiya
        done.setdefault(pf, "band (aapki setting)")
    errs = {}
    waits = {}                                    # v2.1.1: jaanboojh kar ruka (❌ nahi), jaise Pinterest manzoori
    job["status"] = "uploading"
    save_job(jid, job)

    if "youtube" not in done:
        try:
            if not youtube.has_login(brand):
                raise RuntimeError("login nahi (/login)")
            ok, ch = youtube.channel_ok(brand)
            if not ok:
                raise RuntimeError(f"galat channel juda hai ({ch})")
            tags = meta.get("tags") or [BRANDS[brand]["name"], "sabhisaab", "hindi"]
            pub = None
            if pre:
                sl = datetime.datetime.fromisoformat(job["slot"])
                pub = sl.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            yst = post_lock_state(brand, "youtube", _sig(meta))     # v2.3.0: do baar kabhi nahi
            if yst in ("done", "unsure"):
                tg.alert("yellow", f"{jid}: YouTube par ye video shayad pehle ja chuki (bot beech mein ruka tha). Dobara NAHI daali - "
                                   "channel par ek baar dekh lein.")
                post_lock_done(brand, "youtube", _sig(meta), ok=True)
                raise RuntimeError("post-taala: shayad pehle gaya (dobara nahi)")
            if not acquire_post_lock(brand, "youtube", _sig(meta)):
                raise RuntimeError("isi video par abhi kaam chal raha (taala)")
            try:
                vid = youtube.upload(brand, vpath, meta["title"], audit.description(meta), tags, pathlib.Path(thumb),
                                     publish_at=pub)
                post_lock_done(brand, "youtube", _sig(meta), ok=True)
            except Exception:
                post_lock_done(brand, "youtube", _sig(meta), ok=False)
                raise
            done["youtube"] = f"https://youtu.be/{vid}"
            ids["youtube"] = vid
            if meta.get("format") == "long":       # lambi video = us brand ki 'hub' (Shorts ka Related video)
                state.update("hub_videos", lambda d, v=vid: {**(d or {}), brand: v}, {})
            variants = json.loads((pathlib.Path(job["meta"]) / "thumbs.json").read_text())
            learn.record_upload(vid, {**variants[int(job.get("thumb", 1)) - 1], "brand": brand,
                                      "kind": job.get("topic_kind", "idea"), "hour": now().strftime("%H"),
                                      "fmt": meta.get("format", "short"), "title": meta["title"][:80],
                                      "mood": job.get("style") or "normal", "hook": meta.get("hook_used", ""),
                                      "visual": meta.get("visual_style", "") or "classic",
                                      "pkind": meta.get("puzzle_kind") or ("gemini_quiz" if meta.get("puzzle_options") else "card"),
                                      "theme3d": pathlib.Path(meta.get("img3d") or "x_").name.split("_")[0]})
            try:      # channel ka apna pehla comment: website link (log yahin se site par aate hain)
                if not youtube.comment_blocked(brand, "yt_comment_noscope"):   # v2.0.7: TV-login mein comment ki ijaazat nahi -> baar-baar 403 nahi
                    _cm = (f"👉 Poora hisaab / free tool: {SITE}{meta.get('page', '/')}"
                           f"?utm_source=youtube&utm_medium=comment&utm_campaign={brand}"
                           + (f"&utm_content=c{meta.get('reel_code')}" if meta.get("reel_code") else ""))
                    try:                              # v2.5.2: jawab ka link bhi (sirf website live hone par; warna Telegram)
                        from . import answers as _ANC
                        _al = _ANC.desc_line(meta, "youtube")
                        if _al:
                            _cm = _al + "\n" + _cm
                    except Exception:
                        pass
                    youtube.top_comment(brand, vid, _cm)
            except Exception as e:
                from . import ytcomment as _YCP
                if ("insufficient" in str(e).lower() or "403" in str(e)) and not _YCP.has(brand):
                    state.put("yt_comment_noscope", True)
                log(f"top comment: {e}")
            state.update("uploads", lambda d: {**(d or {}), str(now().date()): (d or {}).get(str(now().date()), 0) + 1}, {})
        except Exception as e:
            errs["youtube"] = str(e)[:200]
        if errs.get("youtube", "").startswith("post-taala: shayad"):      # v2.3.0: dobara nahi, aage badho
            done["youtube"] = "⚠ shayad pehle ja chuki (post-taala) - dobara nahi daali"
            errs.pop("youtube", None)
    if pre:          # baaki platform slot par; abhi bas YouTube schedule sambhal ke rakho
        job = jobs()[jid]
        job["done"], job["ids"] = {**job.get("done", {}), **done}, {**job.get("ids", {}), **ids}
        job["status"] = "approved"
        if errs.get("youtube"):
            job["yt_err"] = errs["youtube"]
        save_job(jid, job)
        if "youtube" in done:
            topics.mark_used(job.get("topic_key", ""))
            state.update("history", lambda h: ((h or []) + [{"date": str(now().date()), "brand": brand,
                         "vid": done["youtube"].rsplit("/", 1)[-1], "title": meta["title"], "sig": _sig(meta), "page": meta.get("page", "/")}])[-500:], [])
            tg.alert("green", f"⏰ {jid}: YouTube par {job['slot'][11:16]} ke liye schedule ho gayi (theek samay par public). "
                              "Baaki platform bhi isi samay.")
        return
    if meta.get("format") == "long":
        done.setdefault("facebook", "lambi video: reel nahi (sirf Shorts reel bante hain)")
        done.setdefault("instagram", "lambi video: reel nahi")
    if "facebook" not in done:
        try:
            if not M.brand_info(brand):
                raise RuntimeError("Meta token nahi (/meta)")
            def _fb():
                ids["facebook"] = M.post_facebook(brand, vpath, audit.description(meta, "facebook", "reels"))
                return f"FB page: {M.brand_info(brand)['page_name']}"
            _locked_post(brand, "facebook", _sig(meta), done, errs, _fb)
        except Exception as e:
            errs["facebook"] = str(e)[:200]
    if "instagram" not in done:
        try:
            if not (M.brand_info(brand) or {}).get("ig_id"):
                raise RuntimeError("IG juda nahi (/meta)")
            cap = audit.description(meta, "instagram", "reels").replace("👉 Poora hisaab", "🔗 Link bio mein 👆\n👉 Poora hisaab")
            def _ig():
                ids["instagram"], lk_ = M.post_instagram(brand, vpath, cap)
                return lk_ or "IG reel live"
            _locked_post(brand, "instagram", _sig(meta), done, errs, _ig)
        except Exception as e:
            errs["instagram"] = str(e)[:200]
    if "threads" not in done:
        try:
            from . import threads as TH
            if not TH.info(brand):
                raise RuntimeError("Threads token nahi (bot ko token bhejein)")
            link = f"{SITE}{meta.get('page', '/')}?utm_source=threads&utm_medium=social&utm_campaign={brand}"
            yt = done.get("youtube", "")
            txt = f"{meta['title']}\n\n{meta.get('description', '').strip()}\n\n👉 {link}" + (f"\n▶️ {yt}" if yt else "")
            def _th():
                if meta.get("puzzle_options"):          # v2.3.0 (v11 se): puzzle -> Threads par options wali paheli
                    tl = TH.post_riddle_thread(brand, meta["title"], meta["puzzle_options"], link)
                else:
                    tl = TH.post_text(brand, txt, link)
                ids["threads"] = tl.split("#")[-1]
                return tl.split("#")[0]
            _locked_post(brand, "threads", _sig(meta), done, errs, _th)
        except Exception as e:
            errs["threads"] = str(e)[:200]
    if "pinterest" not in done:
        try:
            from . import pinterest as PI
            if not PI.connected():
                raise RuntimeError("Pinterest token nahi")
            if PI.waiting():
                raise _Wait("⏸ Standard login/manzoori ke baad (bot roz 11 baje khud jaanchta hai)")
            link = f"{SITE}{meta.get('page', '/')}?utm_source=pinterest&utm_medium=pin&utm_campaign={brand}"
            from . import answers as _ANSL
            if meta.get("answer_offsite") and _ANSL.live():   # v2.5.0: pin dabate hi seedha us sawal ka jawab (website)
                link = f"{SITE}/jawab?utm_source=pinterest&utm_medium=pin&utm_campaign={brand}&utm_content=c{meta.get('reel_code', '')}#c{meta.get('reel_code', '')}"
            pin_img = pathlib.Path(job["meta"]) / "pinterest_infographic.jpg"     # v2.3.0 (v11 se): 1000x1500 checklist pin
            try:
                from . import imagegen as _IG
                if not pin_img.exists():
                    _IG.make_infographic_pin(brand, meta["title"], [x.get("show", "") for x in meta.get("scenes", []) if x.get("show")], pin_img)
            except Exception as e:
                log(f"infographic pin: {e}")

            def _pi():
                u_ = PI.post_pin(brand, pin_img if pin_img.exists() else thumb, meta["title"], meta.get("description", ""), link,
                                 section="pahadi" if brand == "pahadi" else "quiz")   # v2.4.0: board section
                ids["pinterest"] = u_.split("/pin/")[-1].split("/")[0]
                return u_
            _locked_post(brand, "pinterest", _sig(meta), done, errs, _pi)
        except _Wait as w:
            waits["pinterest"] = str(w)
        except Exception as e:
            errs["pinterest"] = str(e)[:200]
    if "telegram" not in done:
        try:
            lk = dict(done, _thumb=thumb)
            done["telegram"] = _channel_post(meta, lk)
            ids["telegram"] = lk.get("_tgid")
        except Exception as e:
            errs["telegram"] = str(e)[:200]

    if "youtube" in done and "playlist" not in done:
        try:
            youtube.add_to_playlist(brand, done["youtube"].rsplit("/", 1)[-1],
                                    "Long" if meta.get("format") == "long" else "Shorts")
            done["playlist"] = "✓ playlist mein juda"
        except Exception as e:
            log(f"playlist: {e}")
            done["playlist"] = "playlist nahi juda (baad mein)"
    if "story" not in done and meta.get("format") != "long":
        done["story"] = _stories(brand, meta, vpath)
    if "answer" not in done and meta.get("answer_offsite") and any(k in done for k in ("youtube", "facebook", "instagram")):
        try:                                      # v2.5.0: video bahar aate hi jawab Telegram + website (register)
            from . import answers as _ANS
            _ANS.record(meta, {"youtube": done.get("youtube", "")})
            done["answer"] = f"jawab Telegram + website (kod #{meta.get('reel_code')})"
        except Exception as e:
            log(f"answer record: {e}")
    newly_yt = "youtube" in done and "youtube" not in job.get("done", {}) and not job.get("yt_pre")
    job["done"], job["ids"] = done, ids
    state.update("posted_log", lambda l: ([x for x in (l or []) if x["jid"] != jid] +
                 [{"jid": jid, "brand": brand, "title": meta["title"][:80], "date": str(now().date()), "ids": ids, "page": meta.get("page", "/")}])[-60:], [])
    if newly_yt:      # history turant (taaki dobara na jaye), baaki platform chahe baad mein
        topics.mark_used(job.get("topic_key", ""))
        state.update("history", lambda h: ((h or []) + [{"date": str(now().date()), "brand": brand,
                     "vid": done.get("youtube", "").rsplit("/", 1)[-1], "title": meta["title"], "sig": _sig(meta), "page": meta.get("page", "/")}])[-500:], [])
    if not errs:
        dest = POSTED / pathlib.Path(job["meta"]).name
        shutil.move(job["meta"], dest)
        job.update(status="posted", meta=str(dest), vid=done.get("youtube", "").rsplit("/", 1)[-1])
    else:
        job["status"] = "need_login" if any("login" in e or "token" in e or "juda" in e for e in errs.values()) else "approved"
        if job["status"] == "approved":
            job["tries"] = job.get("tries", 0) + 1
            if job["tries"] >= 3:
                job["status"] = "partial"      # 3 koshish ke baad ruko, report mein dikhega
            else:
                job["slot"] = (now() + datetime.timedelta(minutes=30)).isoformat()   # 30 min baad phir koshish
                job["now"] = False
    save_job(jid, job)
    retry = bool(prev_keys)
    job["last_errs"] = {k: v[:80] for k, v in errs.items()}
    save_job(jid, job)
    if retry:
        new_ok = {k: v for k, v in done.items() if k not in prev_keys}
        same = {k: v[:80] for k, v in errs.items()} == {k: v[:80] for k, v in prev_errs.items()}
        if not new_ok and same:
            log(f"retry {jid}: kuch naya nahi, report nahi bheji")
            lines = None
        else:
            lines = [f"♻️ {BRANDS[brand]['name']} (dobara koshish): {meta['title'][:70]}"]
            lines += [f"✅ {k}: {v}" for k, v in new_ok.items()]
            lines += [f"❌ {k}: {v}" for k, v in errs.items()]
    else:
        lines = [f"📤 {BRANDS[brand]['name']}: {meta['title']}"]
        lines += [f"✅ {k}: {v}" for k, v in done.items()]
        lines += [f"❌ {k}: {v}" for k, v in errs.items()]
        lines.append(f"🔗 Website: {SITE}{meta.get('page', '/')}")
    if not errs and not retry:
        yt = done.get("youtube", "")
        tg.say("📲 WhatsApp channel ke liye (copy karke forward karein):\n\n"
               f"{meta['title']}\n\n▶️ {yt}\n🌐 {SITE}{meta.get('page', '/')}?utm_source=whatsapp&utm_campaign={brand}")
    from . import diary
    diary.add("upload", f"{BRANDS[brand]['name']}: {meta['title'][:60]} | ok={list(done)} fail={list(errs)}")
    try:                                          # v2.0.5: har brand x platform ka aakhri haal (HEALTH.md + alert)
        now_s = now().strftime("%Y-%m-%d %H:%M")
        def _h(d):
            d = dict(d or {})
            for pf in done:
                d[f"{brand}:{pf}"] = {"ok": True, "t": now_s, "err": ""}
            for pf, wmsg in waits.items():
                d[f"{brand}:{pf}"] = {"ok": True, "t": now_s, "err": "", "wait": wmsg}
            for pf, e in errs.items():
                prev = d.get(f"{brand}:{pf}", {})
                d[f"{brand}:{pf}"] = {"ok": False, "t": now_s, "err": e[:160], "fails": (prev.get("fails", 0) + 1) if not prev.get("ok", True) else 1,
                                      "last_ok": prev.get("t") if prev.get("ok") else prev.get("last_ok", "")}
            return d
        state.update("platform_health", _h, {})
        from . import updater
        if errs:
            updater.mark_dirty()
    except Exception as e:
        log(f"health: {e}")
    if lines:
        tg.alert("yellow" if errs else "green", "\n".join(lines))


def tick(run, run_up=None):
    """Har minute: schedule ke hisaab se video banao / upload karo. run(fn,*a) = worker queue."""
    if state.get("paused"):
        return
    t = now()
    today = str(t.date())
    made = state.get("made_today", {})
    for brand, slots in schedule().items():
        for hhmm in [s.strip() for s in str(slots).split(",") if s.strip()]:
            h, m = map(int, hhmm.split(":"))
            slot = t.replace(hour=h, minute=m, second=0, microsecond=0)
            key = f"{today}:{brand}:{hhmm}"
            if made.get(key):
                continue
            if slot - datetime.timedelta(hours=PREPARE_HOURS) <= t < slot + datetime.timedelta(hours=2):
                state.update("made_today", lambda d, k=key: {**{a: b for a, b in (d or {}).items() if a[:10] >= today}, k: 1}, {})
                made[key] = 1
                from .config import QUIZ_SLOT
                _sl = [x.strip() for x in str(slots).split(",") if x.strip()]
                if state.get("quiz_slot_on", True) and (QUIZ_SLOT.get(brand) == hhmm or (len(_sl) > 1 and hhmm == _sl[-1])):
                    # v2.3.1/2.3.3: doosra (aakhri) slot = jaancha hua puzzle/GK / 24-look elite paheli
                    run(prepare, brand, slot.isoformat(), "roz ka schedule", None, "short", "__puzzle__")
                else:
                    run(prepare, brand, slot.isoformat(), "roz ka schedule")
    for jid, job in jobs().items():
        slot = datetime.datetime.fromisoformat(job["slot"])
        auto_ok = job.get("reason") in ("roz ka schedule", "hafte ki lambi video", "schedule")   # aapki/test video kabhi khud nahi
        if job["status"] == "waiting" and auto_on() and auto_ok and t >= slot - datetime.timedelta(minutes=20):
            approve(jid, 1)       # autopilot: 3 audit paas -> slot se 20 min pehle khud manzoor (theek samay par post)
            tg.alert("green", f"🤖 {jid}: aapka jawab nahi aaya, 3 audit paas hain - Thumb 1 se {job['slot'][11:16]} par jayegi.")
            job = jobs()[jid]
        run_up = run_up or run
        if (job["status"] == "approved" and not job.get("now") and "youtube" not in job.get("done", {})
                and datetime.timedelta(minutes=12) < slot - t <= datetime.timedelta(hours=3) and not job.get("yt_pre")):
            job["yt_pre"] = 1                      # YouTube par pehle se 'schedule' (theek samay par khud public)
            save_job(jid, job)
            run_up(upload, jid, True)
        if job["status"] == "approved" and (job.get("now") or t >= slot):
            job["status"] = "queued"
            save_job(jid, job)
            run_up(upload, jid)
    try:                                          # v2.2.0: bhoole hue namoone 1 din baad saaf
        from . import studio
        studio.cleanup()
    except Exception as e:
        log(f"studio cleanup: {e}")
    # purane job saaf (7 din)
    cutoff = (t - datetime.timedelta(days=7)).isoformat()
    old = [j for j, v in jobs().items() if v.get("created", "") < cutoff and v["status"] in
           ("posted", "rejected", "failed")]
    if old:
        state.update("jobs", lambda d: {k: v for k, v in (d or {}).items() if k not in old}, {})


# ---------------- v2.3.0 Step 1 (v11 se): SPARE REEL BANK + offline lambi video ----------------
SPARE_PER_BRAND = 2
SPARE_MAX_DAYS = 30


def spare_reel_status():
    """Har brand ki kitni pehle-se-bani reel taiyaar hai (data/spare_reels/<brand>/)."""
    from .config import SPARE_REELS_DIR
    out = {}
    for b in BRANDS:
        bdir = SPARE_REELS_DIR / b
        out[b] = len(list(bdir.glob("*/video.mp4"))) if bdir.exists() else 0
    return out


def spare_reel_refill(brand=None):
    """VM khaali ho tab (raat): har brand ki 2 tak spare reel - bank script se, audit-paas, kabhi post nahi jab tak zaroorat na ho."""
    from .config import SPARE_REELS_DIR
    from .guardtext import clean_script
    targets = [brand] if brand in BRANDS else list(BRANDS)
    made = []
    cut = time.time() - SPARE_MAX_DAYS * 86400
    for b in targets:
        bdir = SPARE_REELS_DIR / b
        bdir.mkdir(parents=True, exist_ok=True)
        for v in bdir.glob("*/video.mp4"):          # purani (30 din) spare hatao - taaza rahe
            if v.stat().st_mtime < cut:
                shutil.rmtree(v.parent, ignore_errors=True)
        if len(list(bdir.glob("*/video.mp4"))) >= SPARE_PER_BRAND:
            continue
        try:
            sc = None
            try:
                from . import puzzles                # Step 4 ke baad: puzzle reel bhi
                sc = puzzles.generate_puzzle("auto", b)
            except Exception:
                sc = _bank(b)
            sc = clean_script(sc)
            meta = render(sc)
            checks = audit.run(meta)
            if audit.passed(checks) and not _dup_of(b, meta):
                src_d = pathlib.Path(meta["video"]).parent
                dest_d = bdir / src_d.name
                shutil.move(str(src_d), str(dest_d))
                m2 = json.loads((dest_d / "meta.json").read_text(encoding="utf-8"))
                m2["video"] = str(dest_d / "video.mp4")
                m2["thumbs"] = [str(dest_d / pathlib.Path(p).name) for p in m2.get("thumbs", [])]
                (dest_d / "meta.json").write_text(json.dumps(m2, ensure_ascii=False, indent=2))
                made.append(f"{BRANDS[b]['name']}: {m2.get('title', '')[:40]}")
            else:
                shutil.rmtree(pathlib.Path(meta["video"]).parent, ignore_errors=True)
        except Exception as e:
            log(f"spare_reel_refill {b}: {e}")
    st = spare_reel_status()
    return ("🎞 Spare reel bank: " + ", ".join(f"{BRANDS[k]['name']}: {v}" for k, v in st.items()) +
            (("\nNayi: " + "; ".join(made)) if made else ""))


def _take_spare(brand):
    """Slot bachaane ke liye ek spare reel STOCK mein laao -> (meta, checks) ya None. Jo pehle ja chuki ho (sig) wo nahi."""
    from .config import SPARE_REELS_DIR
    bdir = SPARE_REELS_DIR / brand
    for v in sorted(bdir.glob("*/video.mp4")) if bdir.exists() else []:
        try:
            m = json.loads((v.parent / "meta.json").read_text(encoding="utf-8"))
            if _dup_of(brand, m):
                shutil.rmtree(v.parent, ignore_errors=True)
                continue
            dest = STOCK / v.parent.name
            shutil.move(str(v.parent), str(dest))
            m["video"] = str(dest / "video.mp4")
            m["thumbs"] = [str(dest / pathlib.Path(p).name) for p in m.get("thumbs", [])]
            (dest / "meta.json").write_text(json.dumps(m, ensure_ascii=False, indent=2))
            checks = audit.run(m)
            if audit.passed(checks):
                return m, checks
        except Exception as e:
            log(f"take spare: {e}")
    return None


def build_offline_long_script(brand):
    """Ravivaar ki lambi video Gemini band ho tab bhi: bank ki (abhi tak na gayi) script + puzzle se 25+ scene ki
    'Master Guide' (chapters ke saath). Kabhi pehle gayi script nahi."""
    import glob
    files = sorted(glob.glob(str(writer.BANK / f"{brand}_*.json")))
    used = {h.get("sig") for h in (state.get("history") or [])}
    scenes = [{"show": f"{BRANDS[brand]['name']} — hafte ki Master Guide: zaroori hisaab",
               "say": f"Swagat hai {BRANDS[brand]['name']} ki is hafte ki master guide mein. Aaj zaroori vishayon ka poora hisaab samjhenge."}]
    chapters = ["00:00 Parichay"]
    sec_est, parts = 6, 0
    for fp in files:
        if parts >= 6:
            break
        try:
            b_sc = json.loads(pathlib.Path(fp).read_text(encoding="utf-8"))
            if _sig(b_sc) in used:
                continue
            parts += 1
            mm, ss = divmod(sec_est, 60)
            chapters.append(f"{mm:02d}:{ss:02d} Bhaag {parts}: {b_sc.get('title', '')[:45]}")
            for sc in b_sc.get("scenes", [])[:-1]:
                scenes.append(sc)
                sec_est += 6
        except Exception:
            pass
    try:
        from . import puzzles
        for _ in range(2):
            for sc in puzzles.generate_puzzle("auto", brand).get("scenes", [])[:-1]:
                scenes.append(sc)
    except Exception:
        pass
    scenes.append({"show": f"Poora hisaab aur saare free calculator: {SITE}/",
                   "say": "In sab ke free calculator ke liye sab hisaab dot com dekhein aur channel subscribe karein."})
    if len(scenes) < 25:
        raise RuntimeError("Offline lambi video ke liye bank mein kaafi nayi script nahi")
    return {"brand": brand, "format": "long", "page": "/", "source": "bank",
            "title": f"{BRANDS[brand]['name']}: hafte ke zaroori hisaab - poori Master Guide",
            "description": "Is hafte ki master guide. Chapters:\n" + "\n".join(chapters),
            "thumb": {"lines": [BRANDS[brand]["name"], "*Master Guide*"], "emoji": "📺"}, "scenes": scenes[:60]}


# ---------------- v2.0.3: script BANK kabhi khaali nahi (schedule kabhi na chhoote) ----------------
BANK_MIN = 6                 # v2.3.2: roz 2 slot -> 3 din ka bank (pehle 4)


def bank_fresh(brand):
    import glob
    used = {h.get("sig") for h in state.get("history", [])}
    n = 0
    for f in glob.glob(str(writer.BANK / f"{brand}_*.json")):
        try:
            if _sig(json.loads(pathlib.Path(f).read_text(encoding="utf-8"))) not in used:
                n += 1
        except Exception:
            pass
    return n


def bank_refill(max_new=3):
    """Raat ko (01:00, VM khaali): har brand ke liye kam se kam 4 taaza, 3-jaanch-paas script bank mein.
    Gemini band ho ya video fail ho to slot par yahi chalti hai. Topic: trend/evergreen (aaj ke plan se alag)."""
    from . import audit_ai, seo
    from .guardtext import clean_script
    writer.BANK.mkdir(parents=True, exist_ok=True)
    made = []
    for b in BRANDS:
        need = max(0, BANK_MIN - bank_fresh(b))
        for _ in range(min(need, max_new)):
            try:
                if b == "pahadi":                   # v2.3.2: pahadi bank = Uttarakhand GK / purane shabd (trend nahi)
                    from .weekplan import PAHADI_DAY_TOPICS
                    t = random.choice([x for v in PAHADI_DAY_TOPICS.values() for x in v])
                else:
                    tr = seo.trends(b) or [BRANDS[b]["name"]]
                    t = random.choice(tr[:10])
                s = clean_script(writer.write(b, {"key": f"bank:{t}", "topic": t, "page": "/", "kind": "idea"},
                                              "short", writer.QUIZ_STYLE))      # v2.3.2: bank ki script bhi SAWAL wali (4 vikalp)
                if s.get("source") != "gemini" or duplicate(b, s.get("title", ""), sig=_sig(s)):
                    continue
                ok, notes = audit_ai.check(b, s)
                if not ok:
                    continue
                s["bank_made"] = str(now().date())
                (writer.BANK / f"{b}_auto_{now():%Y%m%d%H%M%S}.json").write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
                made.append(f"{BRANDS[b]['name']}: {s.get('title', '')[:40]}")
            except Exception as e:
                log(f"bank_refill {b}: {e}")
    return made
