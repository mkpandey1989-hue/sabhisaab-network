"""Growth kaam: roz ke tyohaar/event idea, comment ka jawab (aapki manzoori se), views report."""
import datetime
import json
import time
from . import tg, state, diary, youtube
from .brain import ask_gemini
from .config import BRANDS, IST, SITE
from .log import log

EVENT_PROMPT = """Today is {date} (India). List well-known Indian or Uttarakhand festivals, jayantis, national/international
days, or major finance dates (tax deadlines, budget) that fall TODAY or TOMORROW. Only include items you are sure about;
if unsure, return an empty list. For each, give one short Hindi video idea for the most suitable brand.
Brands: sunonatak (money stories), money (personal finance), deals (saving/shopping), pahadi (Uttarakhand/pahadi).
Return ONLY JSON: {{"events": [{{"name": "...", "day": "aaj|kal", "brand": "brand key", "idea": "Hindi topic"}}]}}"""

REPLY_PROMPT = """You reply to YouTube comments for the Hindi channel "{brand}" (topic: personal money, calculators,
sabhisaab.com). Comment: "{text}"
Write ONE short polite reply in simple Hindi (Devanagari) or Hinglish matching the commenter's language.
Use gender-neutral respectful words (aap), never guess gender, never promise returns, no spam.
If they ask for details or a calculator, mention sabhisaab.com. If the comment is abusive or spam, return "SKIP".
Return ONLY the reply text."""


def daily_events():
    today = str(datetime.datetime.now(IST).date())
    if state.get("events_day") == today:
        return
    state.put("events_day", today)
    try:
        ev = ask_gemini(EVENT_PROMPT.format(date=today), temperature=0.2).get("events", [])[:4]
    except Exception as e:
        return log(f"events: {e}")
    if not ev:
        return
    rows, lines = [], []
    for i, e in enumerate(ev):
        b = e.get("brand") if e.get("brand") in BRANDS else "sunonatak"
        key = f"{today}:{i}"
        state.update("event_ideas", lambda d, k=key, v={"brand": b, "idea": e.get("idea", "")}: {**(d or {}), k: v}, {})
        lines.append(f"• {e.get('name')} ({e.get('day')}): {BRANDS[b]['name']} - {e.get('idea')}")
        rows.append([(f"🎬 Video: {e.get('name', '')[:18]}", f"ev:{key}"),
                     (f"🖼 Story/Post", f"es:{key}")])
        state.update("event_ideas", lambda d, k=key, nm=e.get("name", ""): {**(d or {}), k: {**(d or {}).get(k, {}), "name": nm}}, {})
    diary.add("hukum", "aaj ke event idea bheje")
    tg.alert("green", "📅 Aaj/kal ke khaas din (video idea):\n" + "\n".join(lines) + "\nBanana ho to button dabayein.",
             tg.inline(rows))


CLASSIFY = """You manage comments for the Hindi channel "{brand}" (money, calculators, sabhisaab.com).
Comment by {author}: "{text}"
The comment is on our video: "{video}".
Classify and reply like a polite, warm human team member (not instant-bot style): simple Hindi/Hinglish matching the
commenter, respectful 'aap', gender-neutral, 1-2 short sentences, at most one emoji, never promise returns.
Sound natural: refer to what THEY said (not generic "thanks for comment"), vary wording, no copy-paste feel. If it is a
question, actually answer it first. If they share their own number/situation, respond to it. Never argue; for
criticism thank them and say we'll improve. Do not repeat any of these recent replies: {recent}
If they ask how/where/calculator/link/details: add "👉 {link}" (exactly this full link) and, if useful, "WhatsApp: {wa}".
If they ask a factual money/tax question, answer briefly and safely, then point to the link for the full calculation.
type: abuse (gaali/hate/harassment) | spam (promo links, scams, bots) | question | praise | other.
Return ONLY JSON: {{"type": "...", "mood": "happy|curious|angry|neutral", "reply": "..."}}"""


def _handle_comment(platform, b, c):
    """Har comment: samjho, gaali/spam hatao, baaki ka 7-45 min baad insaan jaisa vinamra jawab (queue), diary mein yaad."""
    import random
    try:
        from .config import WHATSAPP
        vt = ""
        vid_ = c.get("video") or c.get("media") or ""
        for h_ in reversed(state.get("history") or []):
            if h_.get("vid") == vid_:
                vt = h_.get("title", "")
                break
        recent = " | ".join(x.get("text", "")[:60] for x in (state.get("reply_queue") or [])[-8:])
        r = ask_gemini(CLASSIFY.format(brand=BRANDS[b]["name"], author=c.get("author", ""), text=c["text"][:500],
                                       link=page_link(platform, b, c), wa=WHATSAPP, video=vt or "brand ki video",
                                       recent=recent or "-"),
                       temperature=0.6)
    except Exception as e:
        return log(f"classify: {e}")
    aud = state.get("audience") or {}
    # v2.0: key = platform:naam (privacy section 8 - alag platform ke log jode nahi jaate)
    a = aud.setdefault(f"{platform}:{c.get('author', '?')}", {"n": 0, "brands": [], "mood": "", "first": str(datetime.date.today())})
    a["n"] += 1
    a["mood"] = r.get("mood", "")
    a["last"] = str(datetime.date.today())
    if b not in a["brands"]:
        a["brands"].append(b)
    state.put("audience", dict(list(aud.items())[-3000:]))
    typ = r.get("type", "other")
    if typ in ("abuse", "spam"):
        try:
            if platform == "yt":
                youtube._api(b, "POST", "/youtube/v3/comments/setModerationStatus",
                             params={"id": c["id"], "moderationStatus": "rejected"})
            else:
                from . import meta as M
                bi = M.brand_info(b)
                M._post(f"/{c['id']}", bi["page_token"], hide="true")
            diary.add("setting", f"{typ} comment hataya ({platform} {BRANDS[b]['name']}): {c['text'][:60]}")
        except Exception as e:
            log(f"moderate: {e}")
        return
    if not r.get("reply") or not state.get("auto_reply", True):
        return
    at = time.time() + random.randint(7 * 60, 45 * 60)          # turant nahi - insaan jaisa
    state.update("reply_queue", lambda q: (q or []) + [{"at": at, "pf": platform, "b": b, "id": c["id"],
                                                        "text": r["reply"][:900], "who": c.get("author", "")}], [])
    diary.add("comment", f"{platform} {BRANDS[b]['name']} {c.get('author', '')} ({r.get('mood')}): {c['text'][:80]}")


def page_link(platform, b, c):
    """v1.8: comment jis video/reel par aaya, usi video ka website page (poora https link + UTM). Na mile to homepage."""
    vid = c.get("video") or c.get("media") or ""
    page = "/"
    if vid:
        for h in reversed(state.get("history") or []):
            if h.get("vid") == vid and h.get("page"):
                page = h["page"]
                break
        else:
            for p in reversed(state.get("posted_log") or []):
                if vid in json.dumps(p.get("ids", {})) and p.get("page"):
                    page = p["page"]
                    break
    src = {"yt": "youtube", "ig": "instagram"}.get(platform, platform)
    return f"{SITE}{page}{'&' if '?' in page else '?'}utm_source={src}&utm_medium=comment&utm_campaign={b}"


def reply_tick():
    q = state.get("reply_queue") or []
    due = [x for x in q if x["at"] <= time.time()]
    if not due:
        return
    state.put("reply_queue", [x for x in q if x["at"] > time.time()])
    from . import meta as M
    for x in due:
        try:
            if x["pf"] == "yt":
                youtube.reply_comment(x["b"], x["id"], x["text"])
            else:
                M.ig_reply(x["b"], x["id"], x["text"])
            diary.add("upload", f"jawab diya {x['pf']} {BRANDS[x['b']]['name']} -> {x['who']}: {x['text'][:60]}")
        except Exception as e:
            log(f"reply send: {e}")


def check_comments():
    seen = set(state.get("seen_comments", []))
    for b in BRANDS:
        if not youtube.has_login(b):
            continue
        try:
            for c in youtube.new_comments(b, seen):
                seen.add(c["id"])
                if state.get("auto_reply", True):
                    _handle_comment("yt", b, c)
                    continue
                try:
                    draft = ask_gemini(REPLY_PROMPT.format(brand=BRANDS[b]["name"], text=c["text"]),
                                       json_mode=False, temperature=0.5).strip()
                except Exception:
                    draft = ""
                if not draft or draft.upper().startswith("SKIP"):
                    continue
                key = c["id"][-20:]
                state.update("reply_drafts", lambda d, k=key, v={"brand": b, "parent": c["id"], "text": draft, "at": time.time()}:
                             {**(d or {}), k: v}, {})
                tg.alert("yellow", f"💬 {BRANDS[b]['name']} par comment ({c['author']}):\n\"{c['text'][:300]}\"\n\n"
                                   f"Mera jawab:\n{draft}",
                         tg.inline([[("✅ Ye jawab bhejo", f"cr:{key}"), ("⏭ Chhodo", f"cx:{key}")]]))
        except Exception as e:
            log(f"comments {b}: {e}")
    state.put("seen_comments", list(seen)[-2000:])


import re as _re
KEYWORD = _re.compile(r"\b(link|info|calculator|website)\b|लिंक|कैलकुलेटर|वेबसाइट|लिंक भेजो", _re.I)


def check_ig_comments():
    from . import meta as M
    seen = set(state.get("seen_comments", []))
    for b in BRANDS:
        try:
            for c in M.ig_comments(b, seen):
                seen.add(c["id"])
                if KEYWORD.search(c["text"]) and time.time() > state.get("dm_block_until", 0):
                    try:      # "LINK" comment -> ek private DM with calculator link (Meta ka manzoor tareeka)
                        M.private_reply_ig(b, c["id"], f"Namaste! 🙏 Aapka free calculator yahan hai 👉 "
                                                       + page_link("ig", b, c).replace("utm_medium=comment", "utm_medium=dm")
                                                       + "\nAur aise hisaab ke liye follow karein.")
                        diary.add("upload", f"IG DM link: {BRANDS[b]['name']} @{c['author']}")
                        state.update("dm_count", lambda n: (n or 0) + 1, 0)
                    except Exception as e:
                        if "permission" in str(e).lower() or "(#3)" in str(e) or "(#10)" in str(e) or "(#200)" in str(e):
                            state.put("dm_block_until", time.time() + 86400)
                            state.put("dm_perm_missing", True)
                        log(f"ig dm: {e}")
                if state.get("auto_reply", True):
                    _handle_comment("ig", b, c)
                    continue
                try:
                    draft = ask_gemini(REPLY_PROMPT.format(brand=BRANDS[b]["name"], text=c["text"]),
                                       json_mode=False, temperature=0.5).strip()
                except Exception:
                    draft = ""
                if not draft or draft.upper().startswith("SKIP"):
                    continue
                key = "ig" + c["id"][-18:]
                state.update("reply_drafts", lambda d, k=key, v={"brand": b, "parent": c["id"], "text": draft, "ig": True, "at": time.time()}:
                             {**(d or {}), k: v}, {})
                tg.alert("yellow", f"💬 Instagram {BRANDS[b]['name']} par comment (@{c['author']}):\n\"{c['text'][:300]}\"\n\n"
                                   f"Mera jawab:\n{draft}",
                         tg.inline([[("✅ Ye jawab bhejo", f"cr:{key}"), ("⏭ Chhodo", f"cx:{key}")]]))
        except Exception as e:
            log(f"ig comments {b}: {e}")
    state.put("seen_comments", list(seen)[-2000:])


def send_reply(key):
    d = (state.get("reply_drafts") or {}).get(key)
    if not d:
        return "Ye draft purana hai."
    if d.get("ig"):
        from . import meta as M
        M.ig_reply(d["brand"], d["parent"], d["text"])
    else:
        youtube.reply_comment(d["brand"], d["parent"], d["text"])
    diary.add("upload", f"comment jawab: {d['text'][:60]}")
    return "✅ Jawab chala gaya."


def views_report():
    hist = state.get("history", [])[-40:]
    lines, total = [], 0
    for b in BRANDS:
        ids = [h["vid"] for h in hist if h["brand"] == b and h.get("vid")]
        if not ids or not youtube.has_login(b):
            continue
        try:
            st = youtube.stats(b, ids)
        except Exception as e:
            lines.append(f"{BRANDS[b]['name']}: stats nahi mile ({str(e)[:60]})")
            continue
        top = sorted(st.items(), key=lambda kv: -kv[1]["views"])[:3]
        v = sum(x["views"] for x in st.values())
        total += v
        lines.append(f"📺 {BRANDS[b]['name']}: {v} views, {sum(x['likes'] for x in st.values())} likes")
        for vid, x in top:
            lines.append(f"   ⭐ {x['views']} | {x['title'][:40]} https://youtu.be/{vid}")
    return ("👀 Views (YouTube, aakhri videos)\n" + "\n".join(lines) + f"\nKul: {total}") if lines else \
        "👀 Abhi views ka data nahi (upload ke baad aayega)."


GREET_PROMPT = """Write a short, warm Hindi greeting (max 70 characters, Devanagari) for "{name}" from the brand
"{brand}". Respectful, no religion-based comparison, no politics. Return only the text."""


def festival_post(key):
    """Tyohaar/khaas din: sundar card banakar FB story + Telegram channel post (aapki manzoori ke baad)."""
    from . import meta as M
    from .render import scene_frame
    from .thumbs import make as make_thumbs
    from .config import DATA, TG_CHANNEL
    e = (state.get("event_ideas") or {}).get(key)
    if not e:
        return "Ye idea purana hai."
    b, name = e["brand"], e.get("name") or e.get("idea", "")
    try:
        msg = ask_gemini(GREET_PROMPT.format(name=name, brand=BRANDS[b]["name"]), json_mode=False, temperature=0.6).strip()
    except Exception:
        msg = f"{name} की हार्दिक शुभकामनाएँ!"
    d = DATA / "greet"
    d.mkdir(exist_ok=True)
    card = d / f"{key.replace(':', '_')}.png"
    scene_frame(b, name, msg, 0, 1, card)
    thumbs = make_thumbs(b, {"lines": [name[:22], f"*शुभकामनाएँ*"], "emoji": "🙏", "tag": "आज"}, d, name)
    out = []
    try:
        out.append(M.fb_photo_story(b, card))
    except Exception as ex:
        out.append(f"FB story nahi ({str(ex)[:60]})")
    try:
        with open(thumbs[0], "rb") as f:
            tg.call("sendPhoto", {"chat_id": TG_CHANNEL, "caption": f"{msg}\n\n{BRANDS[b]['name']} | {SITE}"}, {"photo": f})
        out.append("Telegram post")
    except Exception as ex:
        out.append(f"Telegram nahi ({str(ex)[:60]})")
    diary.add("upload", f"tyohaar post: {name} -> {out}")
    return "🖼 " + name + ": " + ", ".join(out)


def login_reminder():
    """Roz ek baar: kaun sa login/token baaki hai (taaki koi platform chhoote nahi)."""
    from . import meta as M, threads as TH, pinterest as PI
    today = str(datetime.date.today())
    if state.get("remind_day") == today:
        return
    state.put("remind_day", today)
    miss = [f"YouTube {v['name']}" for k, v in BRANDS.items() if not youtube.has_login(k)]
    miss += [f"Threads {v['name']}" for k, v in BRANDS.items() if not TH.info(k)]
    if not M.has_token():
        miss.append("Facebook/Instagram (Meta token)")
    if not PI.connected():
        miss.append("Pinterest")
    if miss:
        tg.alert("yellow", "🔑 Ye abhi jude nahi hain (inke bina us platform par post nahi jayegi):\n• " + "\n• ".join(miss)
                 + "\nYouTube ke liye /login dabayein.")


def weekly_report():
    """Har Ravivaar: poore hafte ka A-Z hisaab."""
    from collections import Counter
    since = str(datetime.date.today() - datetime.timedelta(days=7))
    hist = [h for h in state.get("history", []) if h["date"] >= since]
    from . import diary as D
    rows = D.recent(500)
    ups = [r for r in rows if r["kind"] == "upload" and r["t"][:10] >= since]
    errs = [r for r in rows if r["kind"] == "galti" and r["t"][:10] >= since]
    by_brand = Counter(h["brand"] for h in hist)
    from . import learn
    lines = [f"📒 Hafte ka hisaab ({since} se)",
             f"🎬 YouTube video: {len(hist)} | " + ", ".join(f"{BRANDS[b]['name']} {n}" for b, n in by_brand.items()),
             f"📤 Kul post ghatnaayein: {len(ups)} | 🔴 galtiyan: {len(errs)}",
             views_report(), "🎨 Thumbnail seekh:\n" + learn.report()]
    if errs:
        lines.append("Aakhri galtiyan:\n" + "\n".join("• " + r["text"][:90] for r in errs[-5:]))
    return "\n\n".join(lines)



# ---------------- v0.7: seekhna, plan, self-audit ----------------
def update_learning():
    """Roz: har video ke views laao -> topic-type / samay / brand / mood ki seekh update."""
    from . import learn
    vids = learn.video_table(80)
    for b in BRANDS:
        ids = [x["vid"] for x in vids if x.get("brand") == b]
        if not ids or not youtube.has_login(b):
            continue
        try:
            for vid, st in youtube.stats(b, ids).items():
                learn.update_views(vid, st["views"])
        except Exception as e:
            log(f"learn views {b}: {e}")


INSIGHT_PROMPT = """You are a YouTube growth analyst for Hindi finance/info Shorts. Our last videos with views:
{table}
Find patterns (topic type, title style, hour, brand, mood). Be specific and honest; if data is too little, say so.
Return ONLY JSON: {{"summary": "2-3 lines Hinglish for the owner", "do_more": ["..."], "avoid": ["..."],
"title_tips": ["..."], "best_hours": ["HH:MM"]}}"""


def weekly_insights():
    from . import learn
    rows = [x for x in learn.video_table(60) if x.get("title")]
    if len(rows) < 6:
        return "🧠 Seekh: abhi videos kam hain (6+ chahiye), agle hafte se pattern niklenge."
    table = "\n".join(f"{r['views']} views | ret {r.get('retention') or '-'}% | ctr {r.get('ctr') or '-'}% | {r.get('brand')} | "
                      f"{r.get('kind')} | {r.get('hour')}h | thumb {r.get('palette')}/{r.get('layout')} | {r['title']}" for r in rows)
    try:
        ins = ask_gemini(INSIGHT_PROMPT.format(table=table[:6000]), temperature=0.3)
    except Exception as e:
        return f"🧠 Seekh nahi bani: {e}"
    state.put("insights", ins)
    diary.add("setting", "hafte ki seekh update (script mein apne aap lagu)")
    return ("🧠 Hafte ki seekh (aage ki scripts mein apne aap lagu):\n" + ins.get("summary", "") +
            "\n✅ Zyada: " + "; ".join(ins.get("do_more", [])[:4]) + "\n⛔ Kam: " + "; ".join(ins.get("avoid", [])[:3]) +
            ("\n⏰ Achha samay: " + ", ".join(ins.get("best_hours", [])[:4]) if ins.get("best_hours") else ""))


PLAN_PROMPT = """Make a 7-day content plan (Hindi Shorts) starting {start} for 4 brands.
Brands: sunonatak (money stories), money (personal finance), deals (saving/shopping), pahadi (Uttarakhand/pahadi, GK).
Use: trending searches {trends}; known upcoming festivals/days in India/Uttarakhand (only if sure); lessons: {lessons}.
Mix evergreen + trending + little-known facts. No duplicates. Each topic max 60 chars, Hindi/Hinglish.
STRICT: never use any real person's or celebrity's name, brand names, or misleading/clickbait claims; no politics/religion.
Stories must use fictional common first names only.
Return ONLY JSON: {{"YYYY-MM-DD": {{"sunonatak": "...", "money": "...", "deals": "...", "pahadi": "..."}}, ...}} (7 days)."""


def make_plan():
    from . import seo
    start = datetime.date.today() + datetime.timedelta(days=1)
    tr = {b: seo.trends(b)[:6] for b in BRANDS}
    for b, ideas in (state.get("seo_ideas") or {}).items():      # v2.0.3: SEO diary ke sujhaav bhi (plan manzoori se hi)
        if b in tr:
            tr[b] = list(dict.fromkeys(ideas[:3] + tr[b]))[:8]
    ins = state.get("insights") or {}
    try:
        plan = ask_gemini(PLAN_PROMPT.format(start=start, trends=json.dumps(tr, ensure_ascii=False),
                                             lessons="; ".join(ins.get("do_more", [])[:4]) or "-"), temperature=0.7)
    except Exception as e:
        return tg.alert("yellow", f"Hafte ka plan nahi bana: {e}")
    plan = {d: v for d, v in plan.items() if isinstance(v, dict)}
    try:      # doosri jaanch: koi asli/mashhoor naam to nahi aaya?
        chk = ask_gemini("Rewrite this JSON plan so that NO topic contains a real person's/celebrity's name or brand name "
                         "(replace with a generic topic of same meaning). Keep the same keys. Return ONLY JSON.\n"
                         + json.dumps(plan, ensure_ascii=False), temperature=0.1)
        if isinstance(chk, dict) and set(chk) == set(plan):
            plan = chk
    except Exception:
        pass
    state.put("plan_pending", plan)
    lines = [f"{d[5:]}: " + " | ".join(f"{BRANDS[b]['name'].split()[0]}: {t}" for b, t in v.items() if b in BRANDS)
             for d, v in sorted(plan.items())]
    tg.alert("yellow", "🗓 Agle 7 din ka content plan (marketing):\n" + "\n".join(lines) +
             "\n\nManzoor? Badlaav chahiye to normal likhein (jaise 'monday ka money topic SIP kar do').",
             tg.inline([[("✅ Plan manzoor", "pl:ok"), ("❌ Nahi, bot khud chune", "pl:no")]]))


def approve_plan(ok):
    pend = state.get("plan_pending") or {}
    if not ok or not pend:
        state.put("plan_pending", {})
        return "Theek hai, bot roz khud topic chunega."
    cur = state.get("plan") or {}
    cur.update(pend)
    keep = str(datetime.date.today() - datetime.timedelta(days=2))
    state.put("plan", {d: v for d, v in cur.items() if d >= keep})
    state.put("plan_pending", {})
    diary.add("pakka", f"hafte ka plan manzoor ({len(pend)} din)")
    return "✅ Plan manzoor. Roz ki video isi plan se banegi."


def self_audit():
    """Roz subah apni jaanch: website, logins, tokens, Gemini, disk. Sirf dikkat par laal alert."""
    import shutil
    import requests
    from . import meta as M, threads as TH, pinterest as PI, brain
    probs, ok = [], []
    try:
        ok.append("website") if requests.get(SITE, timeout=20).status_code == 200 else probs.append("Website nahi khul rahi")
    except Exception:
        probs.append("Website nahi khul rahi")
    for b, v in BRANDS.items():
        try:
            youtube._access(b)
        except Exception as e:
            probs.append(f"YouTube {v['name']}: {str(e)[:60]}")
    try:
        if M.has_token():
            M._get("/me", M._cfg()["token"], fields="id")
    except Exception as e:
        probs.append(f"Meta: {str(e)[:80]}")
    for b, v in BRANDS.items():
        i = TH.info(b)
        if i and time.time() - i.get("saved", 0) > 55 * 86400:
            probs.append(f"Threads {v['name']} token purana (refresh fail?)")
    if not brain.discover(force=True):
        probs.append("Gemini model list nahi mili")
    try:
        from .updater import github_token_days
        gd = github_token_days()
        if gd is not None and gd < 15:
            probs.append("GitHub token " + ("band ho gaya" if gd < 0 else f"{gd} din mein khatam") + " - naya token bot ko bhejein")
    except Exception:
        pass
    try:
        from . import pinterest as PI
        r = PI.refresh_oauth()
    except Exception as e:
        probs.append(f"Pinterest login refresh: {str(e)[:60]}")
    try:                       # v1.7: website ki privacy/terms (Meta/Google/Pinterest app inhi par tike hain)
        from . import privacy
        probs += ["Policy: " + x for x in privacy.check_site()]
    except Exception as e:
        log(f"privacy check: {e}")
    if datetime.date.today().weekday() == 0:      # v1.8: har Somvaar - saare channel link khulte hain? (404 = laal)
        try:
            from .config import LINKS, WHATSAPP, TELEGRAM, PINTEREST
            from .audit import link_ok
            urls = [u for d in LINKS.values() for u in d.values()] + [WHATSAPP, TELEGRAM, PINTEREST, SITE + "/links"]
            bad = [u for u in urls if link_ok(u) is False]
            probs += [f"Link nahi khul raha: {u}" for u in bad]
        except Exception as e:
            log(f"link health: {e}")
    du = shutil.disk_usage("/")
    if du.used / du.total > 0.8:
        probs.append(f"Disk {du.used * 100 // du.total}% bhari - jagah badhani padegi ya safai")
    state.put("audit", {"t": time.time(), "probs": probs})
    if probs:
        tg.alert("red", "Subah ki jaanch mein dikkat:\n• " + "\n• ".join(probs))
    else:
        tg.alert("green", "Subah ki jaanch: sab theek (website, privacy policy, logins, Gemini, disk).")


def auto_festival():
    """12 baje tak aapne event par kuch nahi kiya to bot khud shubhkamna story/post laga de."""
    today = str(datetime.date.today())
    done = state.get("fest_done") or {}
    for key, e in (state.get("event_ideas") or {}).items():
        if key.startswith(today) and not done.get(key):
            done[key] = 1
            state.put("fest_done", done)
            try:
                tg.alert("green", "Auto: " + festival_post(key))
            except Exception as ex:
                log(f"auto festival: {ex}")



# ---------------- v0.8: khabar, policy, din ki diary, backup ----------------
NEWS_PROMPT = """From these Indian news headlines, pick at most 3 that are USEFUL, factual and safe for a Hindi
personal-finance / Uttarakhand info audience (rule changes, deadlines, new schemes). Skip politics, crime, rumours,
celebrity gossip, and anything unverified. For each give brand and a short Hindi post/story text (max 200 chars)
that states the fact neutrally and says "source: <publisher>". Headlines:
{items}
Return ONLY JSON: {{"picks": [{{"i": index, "brand": "sunonatak|money|deals|pahadi", "text": "..."}}]}}"""


def news_digest():
    from . import news
    today = str(datetime.date.today())
    if state.get("news_day") == today:
        return
    state.put("news_day", today)
    items = []
    seen = set(state.get("news_seen") or [])
    for b, q in news.QUERIES.items():
        items += [x for x in news.fetch(q, 5) if x["title"][:80] not in seen]
    state.put("news_seen", (list(seen) + [x["title"][:80] for x in items])[-500:])
    if not items:
        return
    lst = "\n".join(f"{i}. {x['title']} ({x['src']})" for i, x in enumerate(items))
    try:
        picks = ask_gemini(NEWS_PROMPT.format(items=lst[:5000]), temperature=0.2).get("picks", [])[:3]
    except Exception as e:
        return log(f"news pick: {e}")
    if not picks:
        return
    rows, lines = [], []
    for p in picks:
        i = int(p.get("i", -1))
        if not 0 <= i < len(items) or p.get("brand") not in BRANDS:
            continue
        key = f"n{today}:{i}"
        state.update("news_posts", lambda d, k=key, v={"brand": p["brand"], "text": p.get("text", ""), "link": items[i]["link"]}:
                     {**(d or {}), k: v}, {})
        lines.append(f"• {BRANDS[p['brand']]['name']}: {p.get('text', '')}\n  {items[i]['link'][:80]}")
        rows.append([(f"📢 Post: {BRANDS[p['brand']]['name']}", f"np:{key}"), ("🎬 Video", f"nv:{key}")])
    if rows:
        tg.alert("green", "📰 Aaj ki kaam ki khabar (source ke saath, aapki manzoori se):\n" + "\n".join(lines), tg.inline(rows))


def news_post(key):
    from .config import TG_CHANNEL
    d = (state.get("news_posts") or {}).get(key)
    if not d:
        return "Ye khabar purani ho gayi."
    tg.call("sendMessage", {"chat_id": TG_CHANNEL, "text": f"📢 {d['text']}\n\n{BRANDS[d['brand']]['name']} | {SITE}",
                            "disable_web_page_preview": "true"})
    diary.add("upload", f"khabar post: {d['text'][:60]}")
    return "✅ Khabar Telegram channel par lagi."


POLICY_PROMPT = """These are recent news headlines about YouTube / Meta (Facebook, Instagram, Threads) / Pinterest policies or APIs:
{items}
For a small Indian creator who auto-posts AI-voiced Hindi Shorts with website links, list only changes that could affect
monetization, reach, AI-content labels, link rules, or API access. If nothing relevant, return empty list.
Return ONLY JSON: {{"alerts": [{{"what": "short Hinglish", "action": "what we should do"}}]}}"""


def policy_watch():
    from . import news
    seen = set(state.get("policy_seen") or [])
    items = [x for x in news.policy_news() if x["title"][:80] not in seen]     # pehle bheji khabar dobara nahi
    state.put("policy_seen", (list(seen) + [x["title"][:80] for x in items])[-300:])
    if not items:
        return
    try:
        al = ask_gemini(POLICY_PROMPT.format(items="\n".join(f"- {x['title']} ({x['src']})" for x in items)),
                        temperature=0.2).get("alerts", [])
    except Exception as e:
        return log(f"policy: {e}")
    if al:
        diary.add("setting", "policy khabar: " + "; ".join(a.get("what", "") for a in al)[:300])
        tg.alert("yellow", "📜 Platform policy mein badlaav ki khabar (jaanch lein):\n" +
                 "\n".join(f"• {a.get('what')}\n  👉 {a.get('action')}" for a in al))


def day_report(day=None):
    """Din bhar ka poora hisaab (diary + uploads + jobs + galti + settings + kal ka plan)."""
    from . import diary as D
    day = day or str(datetime.datetime.now(IST).date())
    rows = [r for r in D.recent(800) if r["t"][:10] == day]
    by = {}
    for r in rows:
        by.setdefault(r["kind"], []).append(r)
    hist = [h for h in state.get("history", []) if h["date"] == day]
    tmr = str(datetime.date.fromisoformat(day) + datetime.timedelta(days=1))
    plan = (state.get("plan") or {}).get(tmr, {})
    from .pipeline import schedule
    lines = [f"📓 {day} ka poora hisaab",
             f"🎬 YouTube par gayi: {len(hist)}"] + [f"   • {BRANDS[h['brand']]['name']}: {h['title'][:45]} https://youtu.be/{h['vid']}" for h in hist]
    for k, label in (("upload", "📤 Post/upload ghatnaayein"), ("hukum", "🗣 Aapke hukum"), ("pakka", "✅ Pakke kiye"),
                     ("setting", "⚙️ Setting badli"), ("file", "📁 Files"), ("galti", "🔴 Galtiyan")):
        if by.get(k):
            lines.append(f"{label}: {len(by[k])}")
            lines += [f"   • {r['t'][11:16]} {r['text'][:80]}" for r in by[k][-6:]]
    lines.append("⏰ Kal ka schedule: " + ", ".join(f"{BRANDS[b]['name']} {s}" for b, s in schedule().items()))
    if plan:
        lines.append("🗓 Kal ke topic (plan): " + " | ".join(f"{BRANDS[b]['name']}: {t}" for b, t in plan.items() if b in BRANDS))
    return "\n".join(lines)


def backup_state():
    import shutil
    from .config import DATA, STATE
    d = DATA / "backup"
    d.mkdir(exist_ok=True)
    day = datetime.date.today().strftime("%Y%m%d")
    for src in (STATE, DATA / "learn.json", DATA / "diary.jsonl"):
        if src.exists():
            shutil.copy2(src, d / f"{src.stem}-{day}{src.suffix}")
    from .config import BACKUP_KEEP          # v2.0: 7 din (pehle sirf 1)
    k = BACKUP_KEEP
    for old in sorted(d.glob("state-*.json"))[:-k] + sorted(d.glob("learn-*.json"))[:-k] + sorted(d.glob("diary-*.jsonl"))[:-k]:
        old.unlink(missing_ok=True)



# ---------------- v0.9: graph wali growth report + video detail ----------------
def snapshot():
    """Roz raat: har brand ke followers/views ka hisaab (graph ke liye)."""
    from . import meta as M
    from .config import DATA
    f = DATA / "growth.json"
    try:
        g = json.loads(f.read_text())
    except Exception:
        g = {}
    day = str(datetime.date.today())
    row = {}
    for b in BRANDS:
        r = {}
        try:
            if youtube.has_login(b):
                s = youtube.channel_stats(b)
                r.update(yt_subs=s["subs"], yt_views=s["views"], yt_videos=s["videos"])
        except Exception as e:
            log(f"snap yt {b}: {e}")
        try:
            i = M.brand_info(b) if M.has_token() else None
            if i:
                if i.get("ig_id"):
                    j = M._get(f"/{i['ig_id']}", i["page_token"], fields="followers_count,media_count")
                    r.update(ig_followers=j.get("followers_count", 0), ig_media=j.get("media_count", 0))
                j = M._get(f"/{i['page_id']}", i["page_token"], fields="followers_count,fan_count")
                r.update(fb_followers=j.get("followers_count") or j.get("fan_count") or 0)
        except Exception as e:
            log(f"snap meta {b}: {e}")
        row[b] = r
    g[day] = row
    f.write_text(json.dumps(g))
    return g


def growth_chart():
    """4 graph: YouTube subscribers, YouTube views, Instagram followers, Facebook followers (har brand ki line)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from .config import DATA
    try:
        g = json.loads((DATA / "growth.json").read_text())
    except Exception:
        g = snapshot()
    if str(datetime.date.today()) not in g:
        g = snapshot()
    days = sorted(g)[-30:]
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    for ax, (key, label) in zip(axs.flat, [("yt_subs", "YouTube subscribers"), ("yt_views", "YouTube kul views"),
                                           ("ig_followers", "Instagram followers"), ("fb_followers", "Facebook followers")]):
        for b, info in BRANDS.items():
            ys = [g[d].get(b, {}).get(key) for d in days]
            if any(y is not None for y in ys):
                ax.plot([d[5:] for d in days], [y or 0 for y in ys], marker="o", label=info["name"])
        ax.set_title(label)
        ax.tick_params(axis="x", rotation=45, labelsize=7)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
    fig.suptitle(f"Sabhisaab Network growth ({days[0]} se {days[-1]})")
    fig.tight_layout()
    out = DATA / "growth.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    first, last = g[days[0]], g[days[-1]]
    lines = ["📈 Growth (graph ke saath):"]
    for b, info in BRANDS.items():
        a, z = first.get(b, {}), last.get(b, {})
        lines.append(f"• {info['name']}: YT subs {z.get('yt_subs', '-')} ({z.get('yt_subs', 0) - a.get('yt_subs', 0):+}), "
                     f"YT views {z.get('yt_views', '-')}, IG {z.get('ig_followers', '-')}, FB {z.get('fb_followers', '-')}")
    return out, "\n".join(lines)


def send_growth():
    p, cap = growth_chart()
    with open(p, "rb") as f:
        tg.call("sendPhoto", {"chat_id": tg._chat(), "caption": cap[:1000]}, {"photo": f})


def video_detail(n=5, brand=None, platform=None):
    """Aakhri n videos: har platform par views / likes / comments (YouTube, Facebook, Instagram)."""
    from . import meta as M
    log_ = [x for x in state.get("posted_log", []) if not brand or x["brand"] == brand][-n:]
    if not log_ and brand and M.has_token():          # purani posts: seedha Facebook page se
        try:
            bi = M.brand_info(brand)
            vids = M._get(f"/{bi['page_id']}/videos", bi["page_token"], fields="id,description,created_time", limit=n).get("data", [])
            log_ = [{"brand": brand, "title": (x.get("description") or "")[:50], "date": x.get("created_time", "")[:10],
                     "ids": {"facebook": x["id"]}} for x in reversed(vids)]
        except Exception as e:
            log(f"fb fallback: {e}")
    if not log_:
        return "Abhi koi post record mein nahi" + (f" ({BRANDS[brand]['name']})" if brand else "") + "."
    out, tot = [], {}
    for x in reversed(log_):
        ids = x.get("ids", {})
        line = [f"🎬 {x['date']} | {BRANDS[x['brand']]['name']}: {x['title'][:50]}"]
        rows = []
        if ids.get("youtube") and platform in (None, "youtube"):
            try:
                st = youtube.stats(x["brand"], [ids["youtube"]]).get(ids["youtube"], {})
                rows.append(("▶️ YouTube", st.get("views", 0), st.get("likes", 0), st.get("comments", 0)))
            except Exception:
                pass
        if ids.get("facebook") and platform in (None, "facebook"):
            try:
                st = M.fb_video_stats(x["brand"], ids["facebook"])
                rows.append(("📘 Facebook", st.get("views", "-"), st.get("likes", 0), st.get("comments", 0)))
            except Exception:
                pass
        if ids.get("instagram") and platform in (None, "instagram"):
            try:
                st = M.ig_media_stats(x["brand"], ids["instagram"])
                rows.append(("📸 Instagram", st.get("views", "-"), st.get("likes", 0), st.get("comments", 0)))
            except Exception:
                pass
        for name, vw, lk, cm in rows:
            line.append(f"   {name}: {vw} views, {lk} likes, {cm} comments")
            t = tot.setdefault(name, [0, 0, 0])
            for i, val in enumerate((vw, lk, cm)):
                t[i] += val if isinstance(val, int) else 0
        out.append("\n".join(line))
    summary = "📊 Kul: " + " | ".join(f"{k}: {a} views, {b} likes, {c} comments" for k, (a, b, c) in tot.items())
    return summary + "\n\n" + "\n\n".join(out)


def delete_post(jid, where="all"):
    """Galti se gayi post hatao (aapki double manzoori ke baad)."""
    from . import meta as M, threads as TH, pinterest as PI
    from .config import TG_CHANNEL
    item = next((x for x in state.get("posted_log", []) if x["jid"] == jid), None)
    if not item:
        return "Ye post record mein nahi mili."
    b, ids, res = item["brand"], item.get("ids", {}), []
    plan = {"youtube": lambda: youtube.delete_video(b, ids["youtube"]),
            "facebook": lambda: M.delete_fb(b, ids["facebook"]),
            "instagram": lambda: M.delete_ig(b, ids["instagram"]),
            "threads": lambda: TH.delete_post(b, ids["threads"]),
            "pinterest": lambda: PI.delete_pin(ids["pinterest"]),
            "telegram": lambda: tg.call("deleteMessage", {"chat_id": TG_CHANNEL, "message_id": ids["telegram"]})}
    for k, fn in plan.items():
        if not ids.get(k) or (where != "all" and k != where):
            continue
        try:
            fn()
            res.append(f"✅ {k} se hata di")
            ids[k] = None
        except Exception as e:
            res.append(f"❌ {k}: {str(e)[:80]}" + (" (Instagram app se khud hatayein)" if k == "instagram" else ""))
    item["ids"] = ids
    state.update("posted_log", lambda l: [item if x["jid"] == jid else x for x in (l or [])], [])
    diary.add("setting", f"post hatayi: {item['title'][:50]} -> {res}")
    return f"🗑 {item['title'][:60]}\n" + "\n".join(res)



def greet_post(e, brands):
    """Pakka kiya hua event: card -> FB story + IG story (5s video) + Telegram channel (ek baar)."""
    from . import meta as M
    from .render import scene_frame, _ff
    from .config import DATA, TG_CHANNEL
    name = e.get("name_hi") or e.get("name_en")
    d = DATA / "greet"
    d.mkdir(exist_ok=True)
    out = []
    for b in brands:
        card = d / f"{b}-{abs(hash(name)) % 10**8}.png"
        scene_frame(b, name, e["text"], 0, 1, card)
        try:
            out.append(f"{BRANDS[b]['name']} FB " + str(M.fb_photo_story(b, card))[:20])
        except Exception as ex:
            out.append(f"{BRANDS[b]['name']} FB story nahi ({str(ex)[:40]})")
        try:
            mp4 = card.with_suffix(".mp4")
            _ff(["-loop", "1", "-i", str(card), "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                 "-t", "6", "-r", "30", "-vf", "format=yuv420p", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(mp4)], 2)
            out.append(f"IG " + str(M.ig_video_story(b, mp4))[:20])
        except Exception as ex:
            out.append(f"IG story nahi ({str(ex)[:40]})")
    try:
        with open(card, "rb") as f:
            tg.call("sendPhoto", {"chat_id": TG_CHANNEL, "caption": f"{e['text']}\n\n{SITE}"[:1000]}, {"photo": f})
        out.append("Telegram")
    except Exception as ex:
        out.append(f"Telegram nahi ({str(ex)[:40]})")
    diary.add("upload", f"tyohaar story: {name} -> {', '.join(out)[:200]}")
    return ", ".join(out)



# ---------------- v1.0: duplicate scan (asli channel/page par) ----------------
def duplicate_scan():
    """YouTube (4 channel) + Facebook + Instagram par milti-julti posts dhoondo. Purani rakho, nayi hatane ka button."""
    from difflib import SequenceMatcher
    from . import meta as M
    sim = lambda a, b: SequenceMatcher(None, a.lower()[:80], b.lower()[:80]).ratio()
    report, rows, total = [], [], 0
    for b, info in BRANDS.items():
        groups = {}
        if youtube.has_login(b):
            try:
                vids = sorted(youtube.recent_videos(b, 50), key=lambda x: x["date"])
                for i, x in enumerate(vids):
                    for y in vids[:i]:
                        if sim(x["title"], y["title"]) > 0.8:
                            groups.setdefault(("YouTube", y["vid"]), []).append(x)
                            break
            except Exception as e:
                report.append(f"{info['name']} YouTube jaanch nahi: {str(e)[:60]}")
        try:
            bi = M.brand_info(b) if M.has_token() else None
            if bi and bi.get("ig_id"):
                media = M._get(f"/{bi['ig_id']}/media", bi["page_token"], fields="id,caption,timestamp,permalink",
                               limit=50).get("data", [])
                media = sorted(media, key=lambda x: x.get("timestamp", ""))
                for i, x in enumerate(media):
                    for y in media[:i]:
                        if sim((x.get("caption") or "")[:80], (y.get("caption") or "")[:80]) > 0.85:
                            groups.setdefault(("Instagram", y["id"]), []).append(
                                {"title": (x.get("caption") or "")[:50], "vid": x["id"], "date": x.get("timestamp", "")[:16],
                                 "link": x.get("permalink")})
                            break
            if bi:
                fbv = M._get(f"/{bi['page_id']}/videos", bi["page_token"], fields="id,description,created_time",
                             limit=50).get("data", [])
                fbv = sorted(fbv, key=lambda x: x.get("created_time", ""))
                for i, x in enumerate(fbv):
                    for y in fbv[:i]:
                        if sim((x.get("description") or "")[:80], (y.get("description") or "")[:80]) > 0.85:
                            groups.setdefault(("Facebook", y["id"]), []).append(
                                {"title": (x.get("description") or "")[:50], "vid": x["id"], "date": x.get("created_time", "")[:16]})
                            break
        except Exception as e:
            report.append(f"{info['name']} FB/IG jaanch nahi: {str(e)[:60]}")
        for (plat, keep), dups in groups.items():
            for dpx in dups:
                total += 1
                report.append(f"• {info['name']} {plat}: '{dpx['title'][:45]}' ({dpx['date']}) - duplicate")
                if plat != "Instagram":
                    rows.append([(f"🗑 {plat[:2]} {info['name'][:8]} {dpx['date'][5:10]}", f"yd:{b}:{plat[0]}:{dpx['vid']}")])
                else:
                    report.append(f"   Instagram app se hatayein: {dpx.get('link', '')}")
    head = f"🔍 Duplicate jaanch (har channel/page ki aakhri 50 post): {total} mili"
    state.put("dup_scan", {"t": str(datetime.datetime.now(IST))[:16], "total": total})
    if not total:
        return tg.say(head + "\n✅ Koi duplicate nahi." + ("\n" + "\n".join(report) if report else ""))
    tg.say(head + "\n" + "\n".join(report[:30]) + "\nPurani wali rakhi hai; nayi duplicate hatane ke button:",
           tg.inline(rows[:10]) if rows else None)


def delete_by_id(brand, plat, vid):
    from . import meta as M
    if plat == "Y":
        youtube.delete_video(brand, vid)
    elif plat == "F":
        M.delete_fb(brand, vid)
    diary.add("setting", f"duplicate hatayi: {brand} {plat} {vid}")
    return f"✅ Hata di ({BRANDS[brand]['name']}, {'YouTube' if plat == 'Y' else 'Facebook'})"



def related_video_todo():
    """Har Ravivaar: is hafte ke Shorts ki list + Studio link (Related video sirf Studio se lagta hai, API se nahi)."""
    since = str(datetime.date.today() - datetime.timedelta(days=7))
    rows = [x for x in state.get("posted_log", []) if x["date"] >= since and x.get("ids", {}).get("youtube")]
    if not rows:
        return
    hub = state.get("hub_videos") or {}
    lines = ["🔗 Is hafte ke Shorts mein 'Related video' lagayein (har ek ~20 sec, sirf laptop Studio se):"]
    for x in rows[-20:]:
        h = hub.get(x["brand"])
        lines.append(f"• {BRANDS[x['brand']]['name']}: https://studio.youtube.com/video/{x['ids']['youtube']}/edit"
                     + (f"  → related: youtu.be/{h}" if h else ""))
    lines.append("Studio → Details → 'Related video' → us brand ki hub/lambi video chunein → Save. "
                 "Hub video set karne ke liye bot ko likhein: 'hub video money <video link>'.")
    tg.say("\n".join(lines)[:4000])
