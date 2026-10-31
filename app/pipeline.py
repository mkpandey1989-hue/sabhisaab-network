"""Video ka safar: topic -> script -> video -> audit -> Telegram manzoori -> YouTube upload -> seekh."""
import datetime
import json
import pathlib
import random
import shutil
import time
import uuid
from . import tg, audit, topics, writer, learn, state, youtube
from .config import IST, SCHEDULE, PREPARE_HOURS, AUTO_APPROVE, MAX_UPLOADS_DAY, BRANDS, POSTED, SITE
from .log import log
from .render import render

BRAND_BTNS = [[("🎭 Suno Natak", "mk:sunonatak"), ("💰 Money", "mk:money")],
              [("🛍 Labh Lo Deals", "mk:deals"), ("🏔 Pahadi", "mk:pahadi")]]


def schedule():
    return {**SCHEDULE, **(state.get("schedule") or {})}


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


def duplicate(brand, title, days=90, sig=None):
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


def prepare(brand, slot_iso=None, reason="schedule", topic_text=None, fmt="short", style=""):
    """Video banao aur manzoori ke liye bhejo. Fail ho to bank script se ek aur koshish."""
    jid = f"{brand[:3]}{uuid.uuid4().hex[:5]}"
    slot = slot_iso or (now() + datetime.timedelta(minutes=30)).isoformat()
    save_job(jid, {"brand": brand, "status": "making", "slot": slot, "created": now().isoformat(), "reason": reason})
    tg.say(f"🎬 {BRANDS[brand]['name']}: nayi {'LAMBI video (8-12 min, 30-60 min lagenge)' if fmt == 'long' else 'video'}"
           f" ban rahi hai ({reason}{', ' + style if style else ''})")
    for attempt in (1, 2, 3):
        topic = ({"key": f"custom:{topic_text}", "topic": topic_text, "page": "/", "kind": "custom"}
                 if topic_text and attempt == 1 else topics.next_topic(brand))
        script = writer.write(brand, topic, fmt, style) if (attempt < 3 or fmt == "long") else _bank(brand)
        from .guardtext import clean_script      # v2.0.2: ginti/link/naam scene ke text mein bhi sahi
        script = clean_script(script)
        if topic.get("page", "/") == "/" and topic.get("kind") != "page" and script.get("page", "/") in ("/", "", None):
            try:                                     # v2.0.2: website se bahar ka topic -> sabse milta tool/guide page
                from . import siteknow
                hit = siteknow.find(f"{topic.get('topic', '')} {script.get('title', '')}", 1)
                if hit:
                    script["page"] = "/" + hit[0][0]
            except Exception:
                pass
        dup = duplicate(brand, script.get("title", ""), sig=_sig(script))
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
        if gal and not script.get("clips") and (state.get("use_photos_next") == brand or (brand == "pahadi" and len(gal) >= 3)):
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
                                      TMP / f"ai_{jid}_{k}.png")
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
                save_job(jid, {**jobs()[jid], "status": "failed"})
                tg.alert("red", f"{BRANDS[brand]['name']}: aaj ki video nahi ban payi ({str(e)[:120]}). Galti ESCALATE.md mein.")
                return None
        else:
            tg.alert("red", f"{BRANDS[brand]['name']}: 3 koshish ke baad bhi video audit paas nahi hui.")
            return None
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


def check_link(meta):
    """Website ka page khulta hai? Na khule to homepage."""
    import requests
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


def _stories(brand, meta, vpath):
    """Nayi video ki khabar: FB story (card) + IG story (video, 60s tak). Fail ho to bas note."""
    from . import meta as M
    from .render import scene_frame
    res = []
    try:
        card = pathlib.Path(meta["video"]).parent / "story.png"
        scene_frame(brand, meta["title"], "Nayi video aa gayi! Profile par dekhein aur free calculator: https://sabhisaab.com/",
                    0, 1, card)
        res.append(M.fb_photo_story(brand, card))
    except Exception as e:
        res.append(f"FB story nahi ({str(e)[:60]})")
    try:
        if meta.get("duration", 99) <= 60:
            res.append(M.ig_video_story(brand, vpath))
    except Exception as e:
        res.append(f"IG story nahi ({str(e)[:60]})")
    return ", ".join(res)


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
        dup = duplicate(brand, meta["title"], sig=_sig(meta))
        if not dup and youtube.has_login(brand):          # jaanch 3: channel par asal mein kya pada hai
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
    ids = dict(job.get("ids", {}))
    for pf in (state.get("platform_off") or {}).get(brand, []):     # aapne is brand ke liye ye platform band kiya
        done.setdefault(pf, "band (aapki setting)")
    errs = {}
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
            vid = youtube.upload(brand, vpath, meta["title"], audit.description(meta), tags, pathlib.Path(thumb),
                                 publish_at=pub)
            done["youtube"] = f"https://youtu.be/{vid}"
            ids["youtube"] = vid
            if meta.get("format") == "long":       # lambi video = us brand ki 'hub' (Shorts ka Related video)
                state.update("hub_videos", lambda d, v=vid: {**(d or {}), brand: v}, {})
            variants = json.loads((pathlib.Path(job["meta"]) / "thumbs.json").read_text())
            learn.record_upload(vid, {**variants[int(job.get("thumb", 1)) - 1], "brand": brand,
                                      "kind": job.get("topic_kind", "idea"), "hour": now().strftime("%H"),
                                      "fmt": meta.get("format", "short"), "title": meta["title"][:80],
                                      "mood": job.get("style") or "normal"})
            try:      # channel ka apna pehla comment: website link (log yahin se site par aate hain)
                if not state.get("yt_comment_noscope"):   # v2.0.7: TV-login mein comment ki ijaazat nahi -> baar-baar 403 nahi
                    youtube.top_comment(brand, vid, f"👉 Poora hisaab / free tool: {SITE}{meta.get('page', '/')}"
                                                    f"?utm_source=youtube&utm_medium=comment&utm_campaign={brand}")
            except Exception as e:
                if "insufficient" in str(e).lower() or "403" in str(e):
                    state.put("yt_comment_noscope", True)
                log(f"top comment: {e}")
            state.update("uploads", lambda d: {**(d or {}), str(now().date()): (d or {}).get(str(now().date()), 0) + 1}, {})
        except Exception as e:
            errs["youtube"] = str(e)[:200]
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
            ids["facebook"] = M.post_facebook(brand, vpath, audit.description(meta, "facebook", "reels"))
            done["facebook"] = f"FB page: {M.brand_info(brand)['page_name']}"
        except Exception as e:
            errs["facebook"] = str(e)[:200]
    if "instagram" not in done:
        try:
            if not (M.brand_info(brand) or {}).get("ig_id"):
                raise RuntimeError("IG juda nahi (/meta)")
            cap = audit.description(meta, "instagram", "reels").replace("👉 Poora hisaab", "🔗 Link bio mein 👆\n👉 Poora hisaab")
            ids["instagram"], link = M.post_instagram(brand, vpath, cap)
            done["instagram"] = link or "IG reel live"
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
            tl = TH.post_text(brand, txt, link)
            done["threads"], ids["threads"] = tl.split("#")[0], tl.split("#")[-1]
        except Exception as e:
            errs["threads"] = str(e)[:200]
    if "pinterest" not in done:
        try:
            from . import pinterest as PI
            if not PI.connected():
                raise RuntimeError("Pinterest token nahi")
            link = f"{SITE}{meta.get('page', '/')}?utm_source=pinterest&utm_medium=pin&utm_campaign={brand}"
            done["pinterest"] = PI.post_pin(brand, thumb, meta["title"], meta.get("description", ""), link)
            ids["pinterest"] = done["pinterest"].split("/pin/")[-1].split("/")[0]
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
    lines = [f"📤 {BRANDS[brand]['name']}: {meta['title']}"]
    lines += [f"✅ {k}: {v}" for k, v in done.items()]
    lines += [f"❌ {k}: {v}" for k, v in errs.items()]
    lines.append(f"🔗 Website: {SITE}{meta.get('page', '/')}")
    if not errs:
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
    # purane job saaf (7 din)
    cutoff = (t - datetime.timedelta(days=7)).isoformat()
    old = [j for j, v in jobs().items() if v.get("created", "") < cutoff and v["status"] in
           ("posted", "rejected", "failed")]
    if old:
        state.update("jobs", lambda d: {k: v for k, v in (d or {}).items() if k not in old}, {})


# ---------------- v2.0.3: script BANK kabhi khaali nahi (schedule kabhi na chhoote) ----------------
BANK_MIN = 4


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


def bank_refill(max_new=2):
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
                tr = seo.trends(b) or [BRANDS[b]["name"]]
                t = random.choice(tr[:10])
                s = clean_script(writer.write(b, {"key": f"bank:{t}", "topic": t, "page": "/", "kind": "idea"}))
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
