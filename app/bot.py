"""Sabhisaab Network - 24x7 Telegram control bot (sirf owner). Chalana: systemd sabhinet.service"""
import datetime
import re
import os
import queue
import shutil
import subprocess
import threading
import time
import traceback
from . import tg, state, pipeline, youtube, updater, learn
from .config import BASE, BRANDS, SCHEDULE, AUTO_APPROVE, SECRETS, LOGS, VOICE, MAX_UPLOADS_DAY, IST, TG_MAX_MB
from .guard import cleanup, mem_avail_mb
from .log import log

VER = (BASE / "VERSION").read_text().strip()
STARTED = time.time()
WORK = queue.Queue()
UPWORK = queue.Queue()      # upload alag line: video banne ke kaam ke peeche nahi rukta (samay par post)
KB = tg.reply_keyboard([
    ["🎬 Abhi video", "⏳ Pending", "📊 Aaj ka haal"],
    ["🩺 Sab theek?", "⏸ Pause", "▶️ Resume"],
    ["📖 Poora menu"],
])
MENU_ROWS = [["📓 Aaj ka poora hisaab", "🗓 Kal ka plan", "📰 Khabar"],
             ["🔍 Duplicate jaanch", "📅 Aaj ke tyohaar", "🏢 Company meeting"],
             ["📊 Analytics", "🔗 Analytics jodo", "🧾 Mere kaam"],
             ["🌐 Website haal", "📑 Indexing", "🚀 Website deploy"],
             ["🔎 Bing", "🛠 Website audit", "⚙️ Badlaav ka record"],
             ["👥 Website par aaj kitne log", "📁 Website ki file"],
             ["📈 Growth graph", "🎬 Aakhri 5 video", "🗑 Post hatao"],
             ["🎨 Naye thumbnail", "✅ Thumb 1 se daalo", "❌ Mat daalo"],
             ["📺 Lamba video", "🎭 Mood video", "💬 Comments"],
             ["👀 Views", "📒 Hafte ka hisaab", "📅 7 din"],
             ["🖥 VM", "⚙️ Settings", "🛡 Suraksha"],
             ["📓 Diary", "📜 Logs", "©️ Copyright"],
             ["🔐 Privacy", "🩺 Website doctor", "🔄 Upgrade haal"],
             ["🧹 GitHub safai", "🧠 Website gyaan taaza", "🔎 SEO seekh"]]
LATER = {}
MOODS = ["😂 Mazedaar", "😲 Hairani wala", "💪 Motivation", "😢 Emotional kahani", "🧠 Gyaan/facts"]
COPYRIGHT = ("©️ Copyright jaanch (har video par apne aap):\n✅ Awaaz: Kokoro (Apache-2.0, commercial OK)\n"
             "✅ Font: Noto/Baloo (OFL, commercial OK)\n✅ Emoji: Noto Color Emoji (OFL)\n"
             "✅ Script: hamari apni (Gemini se nayi likhi), kisi ka text copy nahi\n✅ Music: koi gaana/music nahi daalte\n"
             "✅ Kisi asli insaan ki photo/awaaz nahi\n✅ AI label description mein + YouTube par 'altered content' flag\n"
             "⚠️ Aap khud koi photo/video bhejte hain to wo aapki apni ya free-license honi chahiye.")
TRADING = ["nifty-live", "delta-live", "nifty-chart", "sabhinet"]


QUEUED = set()


def run(fn, *a):
    """Ek hi kaam line mein do baar nahi (jaldibazi mein doubling nahi)."""
    key = (getattr(fn, "__name__", ""), repr(a)[:200])
    if key[0] != "<lambda>" and key in QUEUED:
        log(f"dobara kaam roka: {key[0]}")
        return
    QUEUED.add(key)
    WORK.put((fn, a))


def run_up(fn, *a):
    UPWORK.put((fn, a))


def up_worker():
    while True:
        fn, a = UPWORK.get()
        safe(fn, *a)


def safe(fn, *a):
    try:
        fn(*a)
    except Exception as e:
        log("THREAD ERROR " + traceback.format_exc())
        tg.alert("red", f"{fn.__name__} mein galti: {str(e)[:300]}")
    finally:
        if fn is updater.install:
            state.put("installing", 0)


def worker():
    while True:
        fn, a = WORK.get()
        QUEUED.discard((getattr(fn, "__name__", ""), repr(a)[:200]))
        state.put("working_on", f"{getattr(fn, '__name__', '?')} {a[:1]}")
        try:
            fn(*a)
        except Exception as e:
            log("WORK ERROR " + traceback.format_exc())
            k = f"{getattr(fn, '__name__', '?')}: {str(e)[:60]}"          # baar-baar wali galti -> khule kaam ki list
            cnt = state.get("err_count") or {}
            cnt[k] = cnt.get(k, 0) + 1
            state.put("err_count", dict(list(cnt.items())[-200:]))
            if cnt[k] == 3:
                state.update("todo", lambda l, k=k: (l or []) + [{"t": time.strftime("%Y-%m-%d"), "x": "Baar-baar galti: " + k}], [])
            tg.alert("red", f"Kaam mein galti ({fn.__name__}): {str(e)[:300]}\nBot chalu hai, agla kaam jaari.")
            try:
                from . import diary
                diary.add("galti", f"{fn.__name__}: {str(e)[:200]}")
            except Exception:
                pass
        finally:
            state.put("working_on", "")


def scheduler():
    last_clean = 0
    while True:
        try:
            pipeline.tick(run, run_up)
            if time.time() - last_clean > 6 * 3600:
                cleanup()
                last_clean = time.time()
                try:
                    from . import threads as TH
                    for line in TH.refresh_all():
                        tg.say(line)
                except Exception:
                    log("threads refresh error " + traceback.format_exc())
            nowt = datetime.datetime.now(IST)
            rt = report_times()                   # v2.0.3: har report apne tay samay par, theek minute (alag thread)
            if _due(nowt, rt["day"], 1) and state.get("report_day") != str(nowt.date()):
                state.put("report_day", str(nowt.date()))
                def _day():
                    from . import growth
                    return today_text() + "\n\n" + growth.views_report()
                ontime(rt["day"], _day)
            if _due(nowt, rt["events"], 1) and state.get("events_day") != str(nowt.date()):
                state.put("events_day", str(nowt.date()))
                from . import calendar_in
                ontime(rt["events"], calendar_in.today_text)
            if time.time() - state.get("comments_at", 0) > 2 * 3600 and not state.get("paused"):
                state.put("comments_at", time.time())
                from . import growth
                run(growth.check_comments)
                run(growth.check_ig_comments)
            day = str(nowt.date())
            try:                                          # v2.0.7: Telegram ka raasta + VM dhadkan (Cloudflare)
                ch = tg.route_change()
                if ch:
                    tg.say(ch)
                if time.time() - state.get("relay_tick_at", 0) > 600:
                    state.put("relay_tick_at", time.time())
                    from . import relay
                    threading.Thread(target=lambda: safe(relay.tick), daemon=True).start()
                    threading.Thread(target=lambda: safe(relay.auto), daemon=True).start()
            except Exception:
                log("relay tick " + traceback.format_exc())
            if nowt.strftime("%H:%M") >= "02:45" and state.get("privacy_day") != day:
                state.put("privacy_day", day)          # v1.7: 30 din se purana commenter data mitao (policy ka vaada)
                from . import privacy
                run(privacy.purge)
            if nowt.strftime("%H:%M") >= "03:00" and state.get("backup_day") != day:
                state.put("backup_day", day)
                from . import growth, pinterest as PI
                run(growth.backup_state)
                try:
                    r = PI.refresh_oauth()
                    if r:
                        tg.alert("green", r)
                except Exception as e:
                    tg.alert("yellow", f"Pinterest login refresh: {str(e)[:150]}")
            if state.get("old_crons_off"):          # website ka kaam ab yahin (purane GitHub cron band hone ke baad)
                from . import website
                if _due(nowt, rt["site"], 110) and state.get("site_daily_day") != day:
                    state.put("site_daily_day", day)          # v2.0.3: 110 min pehle taiyari, bhejna theek tay samay par
                    hold = _at(nowt, rt["site"]).timestamp()
                    threading.Thread(target=lambda h=hold: safe(website.daily, h), daemon=True).start()
                if nowt.strftime("%H:%M") >= "09:05" and state.get("site_pend_day") != day:
                    state.put("site_pend_day", day)
                    run(website.pending)
                if time.time() - state.get("site_watch_at", 0) > 1800:
                    state.put("site_watch_at", time.time())
                    run(website.watch)
            if nowt.strftime("%H:%M") >= "10:30" and state.get("tasks_day") != day:
                state.put("tasks_day", day)
                from . import tasks
                run(lambda: tasks.report(auto=True))
            if state.get("reply_queue"):
                from . import growth
                run_up(growth.reply_tick)
            if state.get("muhurat_q"):
                from . import calendar_in
                calendar_in.muhurat_tick(run)
            if nowt.strftime("%H:%M") >= "11:00" and state.get("pin_check_day") != day:
                state.put("pin_check_day", day)
                def _pc():
                    from . import pinterest as PI
                    r = PI.check_standard()
                    if r:
                        tg.alert("green" if "MIL GAYA" in r else "yellow", r)
                run(_pc)
            if nowt.strftime("%H:%M") >= "04:00" and state.get("gh_day") != day:
                state.put("gh_day", day)
                run(lambda: log(updater.mirror(daily=True)))
            if nowt.strftime("%H:%M") >= "08:30" and state.get("news_q") != day:
                state.put("news_q", day)
                from . import growth
                run(growth.news_digest)
            if nowt.weekday() == 0 and nowt.strftime("%H:%M") >= "09:00" and state.get("policy_day") != day:
                state.put("policy_day", day)
                from . import growth
                run(growth.policy_watch)
            if nowt.strftime("%H:%M") >= "06:00" and state.get("audit_day") != day:
                state.put("audit_day", day)
                from . import growth
                run(growth.self_audit)
            if nowt.strftime("%H:%M") >= "00:02" and state.get("cal_day") != day:
                state.put("cal_day", day)
                from . import calendar_in
                run(calendar_in.refresh)
            if (nowt.strftime("%H:%M") >= "00:10" and state.get("cal_day") == day and state.get("greet_day") != day
                    and state.get("auto_festival", True)):
                state.put("greet_day", day)
                from . import calendar_in
                run(calendar_in.post_today)
            if False:
                state.put("fest_day", day)
                from . import growth
                run(growth.auto_festival)
            if nowt.weekday() == 6 and nowt.strftime("%H:%M") >= "18:30" and state.get("rel_day") != day:
                state.put("rel_day", day)
                from . import growth
                run(growth.related_video_todo)
            if nowt.weekday() == 6 and nowt.strftime("%H:%M") >= "19:00" and state.get("meet_day") != day:
                state.put("meet_day", day)
                from . import company
                run(company.meeting)
            if nowt.strftime("%H:%M") >= "23:00" and state.get("snap_day") != day:
                state.put("snap_day", day)
                from . import growth
                run(growth.snapshot)
                if nowt.weekday() == 6:
                    run(growth.send_growth)
            if nowt.strftime("%H:%M") >= "22:00" and state.get("learn_day") != day:
                state.put("learn_day", day)
                from . import growth, analytics as AN
                run(growth.update_learning)
                run(AN.feed_learning)
            if nowt.weekday() == 6 and nowt.strftime("%H:%M") >= "20:00" and state.get("plan_day") != day:
                state.put("plan_day", day)
                from . import growth
                run(lambda: tg.alert("green", growth.weekly_insights()))
                run(growth.make_plan)
            if nowt.strftime("%H:%M") >= "10:00" and state.get("remind_day") != str(nowt.date()):
                from . import growth
                run(growth.login_reminder)
            if nowt.weekday() == 6 and nowt.strftime("%H:%M") >= "21:00" and state.get("week_day") != str(nowt.date()):
                state.put("week_day", str(nowt.date()))
                from . import growth
                run(lambda: tg.alert("green", growth.weekly_report()))
            if nowt.weekday() == 6 and "01:30" <= nowt.strftime("%H:%M") < "02:30" and state.get("long_day") != str(nowt.date()) \
                    and not state.get("paused"):
                state.put("long_day", str(nowt.date()))
                order = list(BRANDS)
                br = order[nowt.isocalendar()[1] % len(order)]      # har hafte agla brand
                run(pipeline.prepare, br, None, "hafte ki lambi video", None, "long")
            if nowt.strftime("%H:%M") >= "05:30" and state.get("heal_day") != day:      # v2.0: auto-heal
                state.put("heal_day", day)
                from . import upgrader
                run(upgrader.heal)
            if nowt.strftime("%H:%M") >= "06:20" and state.get("know_day") != day:      # v2.0: website gyaan + badlaav
                state.put("know_day", day)
                from . import siteknow
                run(lambda: siteknow.refresh(notify=True))
            try:                                                                           # v2.0.2: GitHub copy + auto deploy
                from . import website as _W
                for nm, fn in _W.tick_auto():
                    run(lambda fn=fn: (lambda r: r and tg.say(r if isinstance(r, str) else str(r)))(fn()))
            except Exception:
                log("tick_auto " + traceback.format_exc())
            if time.time() - (state.get("know_at") or 0) > 3 * 3600:                        # v2.0.2: website/page/policy nigrani har 3 ghante
                state.put("know_at", time.time())
                from . import siteknow
                run(lambda: siteknow.refresh(notify=True))
            if time.time() - (state.get("pol_at") or 0) > 6 * 3600:                         # v2.0.2: live privacy/terms har 6 ghante
                state.put("pol_at", time.time())
                def _pol():
                    from . import privacy
                    pr = privacy.check_site()
                    if pr and pr != state.get("pol_last"):
                        tg.alert("red", "🔐 Website policy page mein dikkat:\n• " + "\n• ".join(pr))
                    state.put("pol_last", pr)
                run(_pol)
            if nowt.strftime("%H:%M") >= "23:30" and state.get("recount_day") != day:      # v2.0.2: purani description ki ginti/link
                state.put("recount_day", day)
                from . import marketing
                run(lambda: log("recount: " + marketing.recount()))
            if nowt.weekday() == 6 and nowt.strftime("%H:%M") >= "19:30" and state.get("seo_day") != day:
                state.put("seo_day", day)                                                    # v2.0.2: GSC query -> topic (plan se pehle)
                from . import marketing
                run(lambda: tg.alert("green", marketing.gsc_ideas()))
            if (nowt.weekday() == 6 and "03:30" <= nowt.strftime("%H:%M") < "05:00" and state.get("sq_day") != day
                    and state.get("gh_squash_auto", True) and not state.get("gh_pending")):
                state.put("sq_day", day)                                                     # v2.0.2: GitHub par sirf taaza copy
                from . import website as _W2
                run(lambda: log("squash: " + _W2.squash_history()))
            if state.get("docs_dirty") and time.time() - (state.get("docs_push_at") or 0) > 600:
                state.put("docs_push_at", time.time())                                    # v2.0.4: kaam/query -> GitHub turant
                state.put("docs_dirty", False)
                run(lambda: log("docs push: " + updater.mirror(force=True)))
            if nowt.strftime("%H:%M") >= "23:40" and state.get("vidjson_day") != day:
                state.put("vidjson_day", day)                                             # v2.0.6: page par video link
                from . import website as _W3
                run(lambda: log(_W3.publish_videos()))
            if nowt.weekday() == 2 and nowt.strftime("%H:%M") >= "02:00" and state.get("redir_day") != day:
                state.put("redir_day", day)                                               # v2.0.6: redirect jaanch (Budh)
                def _rd():
                    from . import website as _W4
                    ok, bad = _W4.redirect_check()
                    updater.mark_dirty()
                    if bad:
                        tg.alert("yellow", f"↪️ Redirect jaanch: {ok} theek, {len(bad)} galat:\n" + "\n".join(bad[:10]))
                run(_rd)
            if nowt.strftime("%H:%M") >= "07:00" and state.get("kw_day") != day:
                state.put("kw_day", day)                                                  # v2.0.5: keyword bank roz
                from . import marketing
                run(lambda: (marketing.keyword_bank(), updater.mark_dirty()))
            if "01:00" <= nowt.strftime("%H:%M") < "05:00" and state.get("bank_day") != day and not state.get("paused"):
                state.put("bank_day", day)                                               # v2.0.3: script bank bhara rahe
                def _bank():
                    made = pipeline.bank_refill()
                    if made:
                        log("bank: " + "; ".join(made))
                run(_bank)
            if nowt.weekday() == 5 and nowt.strftime("%H:%M") >= "21:00" and state.get("seo_diary_day") != day:
                state.put("seo_diary_day", day)                                          # v2.0.3: SEO diary (Shanivaar)
                from . import seodiary
                run(lambda: tg.alert("green", seodiary.run()))
            if nowt.weekday() == 6 and "02:30" <= nowt.strftime("%H:%M") < "04:00" and state.get("upg_day") != day:
                state.put("upg_day", day)                                                # v2.0: hafte ka khud-upgrade
                from . import upgrader
                run(upgrader.weekly)
        except Exception:
            log("TICK ERROR " + traceback.format_exc())
        time.sleep(15)


# ---------------- v2.0.3: report theek samay par ----------------
REPORT_DEF = {"site": "08:00", "day": "21:30", "events": "07:30"}
REPORT_NAMES = {"site": "Website roz ki report (Google/Analytics/indexing)", "day": "Din ki report (videos + views)",
                "events": "Aaj ke tyohaar/events"}


def report_times():
    return {**REPORT_DEF, **(state.get("report_times") or {})}


def report_times_text():
    return "🕗 Report ka samay (IST):\n" + "\n".join(f"• {REPORT_NAMES[k]}: {v}" for k, v in report_times().items())


def _at(nowt, hhmm):
    h, m = map(int, hhmm.split(":"))
    return nowt.replace(hour=h, minute=m, second=0, microsecond=0)


def _due(nowt, hhmm, lead_min):
    """Tay samay se lead_min pehle taiyari shuru (aaj ke din, ek baar)."""
    return nowt >= _at(nowt, hhmm) - datetime.timedelta(minutes=lead_min)


def ontime(hhmm, build, level="green"):
    """Text pehle banao, phir theek hh:mm:00 par bhejo (worker queue ke peeche kabhi nahi atakta)."""
    def _go():
        try:
            txt = build()
            wait = _at(datetime.datetime.now(IST), hhmm).timestamp() - time.time()
            if 0 < wait < 3 * 3600:
                time.sleep(wait)
            if txt:
                tg.alert(level, txt)
        except Exception:
            log("ontime " + traceback.format_exc())
    threading.Thread(target=_go, daemon=True).start()


def parse_report_time(text):
    """'website report 8 baje' / 'subah ki report 8:00' / 'raat ki report 9:30 pm' -> (key, 'HH:MM') ya None."""
    tl = text.lower()
    if "report" not in tl and "riport" not in tl:
        return None
    m = re.search(r"(\d{1,2})\s*[:.]\s*(\d{2})", tl) or re.search(r"(\d{1,2})\s*(?:baje|bje|am|pm|o'?clock)", tl)
    if not m:
        return None
    h = int(m.group(1))
    mi = int(m.group(2)) if m.lastindex and m.lastindex >= 2 and m.group(2) and m.group(2).isdigit() else 0
    if any(w in tl for w in ("pm", "shaam", "sham", "raat", "dopahar")) and h < 12:
        h += 12
    if not (0 <= h <= 23 and 0 <= mi <= 59):
        return None
    if any(w in tl for w in ("tyohaar", "tyohar", "event", "festival")):
        key = "events"
    elif any(w in tl for w in ("din ki", "shaam", "sham", "raat", "video report", "views")):
        key = "day"
    elif any(w in tl for w in ("website", "site", "subah", "daily", "roz ki", "google", "morning", "index")):
        key = "site"
    else:
        return ("?", f"{h:02d}:{mi:02d}")
    return (key, f"{h:02d}:{mi:02d}")


def today_text():
    today = str(datetime.date.today())
    lines = [f"📊 Aaj ka haal (v{VER})", f"⬆️ Upload: {pipeline.uploads_today()}/{MAX_UPLOADS_DAY}"]
    for jid, j in pipeline.jobs().items():
        if j.get("created", "")[:10] == today or j["status"] in ("waiting", "approved", "need_login"):
            lines.append(f"• {BRANDS[j['brand']]['name']}: {j['status']} {j.get('title', '')[:40]}"
                         + (f" https://youtu.be/{j['vid']}" if j.get("vid") else ""))
    lines.append("⏰ Roz: " + ", ".join(f"{BRANDS[b]['name']} {t}" for b, t in pipeline.schedule().items()))
    lines.append("🎨 Seekh:\n" + learn.report())
    if state.get("paused"):
        lines.append("⏸ Bot ROKA hua hai (▶️ Resume dabayein)")
    return "\n".join(lines)


def week_text():
    h = state.get("history", [])
    since = str(datetime.date.today() - datetime.timedelta(days=7))
    rows = [x for x in h if x["date"] >= since]
    if not rows:
        return "📅 Pichhle 7 din mein koi upload nahi."
    out = [f"📅 7 din: {len(rows)} video"]
    out += [f"• {r['date'][5:]} {BRANDS[r['brand']]['name']}: {r['title'][:40]} https://youtu.be/{r['vid']}" for r in rows[-15:]]
    return "\n".join(out)


def vm_text():
    du = shutil.disk_usage("/")
    load = os.getloadavg()
    svc = []
    for s in TRADING:
        r = subprocess.run(["systemctl", "is-active", s], capture_output=True, text=True)
        svc.append(f"{'✅' if r.stdout.strip() == 'active' else '⚪'} {s}")
    return (f"🖥 VM\n🧠 RAM khaali: {mem_avail_mb()} MB\n💾 Disk: {du.used // 2**30}/{du.total // 2**30} GB\n"
            f"⚙️ Load: {load[0]:.2f} {load[1]:.2f}\n" + "\n".join(svc))


def health_text():
    up = int((time.time() - STARTED) / 60)
    from . import brain
    gm, ge = state.get("gemini_last_model", "-"), state.get("gemini_last_error", "")
    lines = [f"🩺 Sab theek? (v{VER}, chalu {up} min)",
             f"{'✅' if os.environ.get('GEMINI_API_KEY') and not ge else '🔴'} Gemini: {gm}" + (f" | galti: {ge[:120]}" if ge else ""),
             "🧠 Model kram: " + " > ".join(f"{m}{'✅' if (state.get('gemini_status') or {}).get(m) == 'ok' else ('⚠️' if (state.get('gemini_status') or {}).get(m) else '')}"
                                          for m in brain.discover()[:4]) or "🧠 (list nahi mili)",
             f"{'✅' if youtube.CLIENT.exists() else '❌'} YouTube client file (TV)"]
    for b in BRANDS:
        if youtube.has_login(b):
            ok, ch = youtube.channel_ok(b)
            lines.append(f"{'✅' if ok else '⛔'} {BRANDS[b]['name']} login ({ch})")
        else:
            lines.append(f"🔑 {BRANDS[b]['name']}: login baaki (/login)")
    from . import meta as M
    if M.has_token():
        for bk, bv in BRANDS.items():
            i = M.brand_info(bk)
            lines.append(f"{'✅' if i else '❌'} {bv['name']} FB" + (f" + IG @{i['ig_user']}" if i and i.get('ig_user') else " (IG nahi)"))
    else:
        lines.append("🔑 Facebook/Instagram: Meta token baaki")
    from . import threads as TH
    for bk, bv in BRANDS.items():
        i = TH.info(bk)
        lines.append(f"{'✅' if i else '🔑'} {bv['name']} Threads" + (f" @{i['username']}" if i else " token baaki"))
    from . import pinterest as PI
    from . import analytics as AN
    lines.append("📊 Analytics: " + ", ".join(f"{v['name'].split()[0]} {'✅' if AN.has(k) else '🔑'}" for k, v in BRANDS.items())
                 + ("" if AN.CLIENT.exists() else " (client file baaki: /analytics)"))
    ps = PI.status()
    lines.append(f"{'✅' if PI.connected() else '🔑'} Pinterest: {ps['env']}" + (" | login ✅" if ps["oauth"] else " | login (OAuth) baaki: /pinterest")
                 + (" | LIVE public" if ps["live"] else " | public ke liye Standard manzoori baaki"))
    if M.has_token() and M._cfg().get("secret_bad"):
        lines.append("🔴 Meta App Secret galat/purana - App settings > Basic se abhi wala secret bhejein")
    lines.append(f"{'⏸ ROKA hua' if state.get('paused') else '▶️ Chal raha'} | Auto-upload: {'ON' if pipeline.auto_on() else 'OFF'}")
    lines.append(f"📋 Kaam line mein: {WORK.qsize()} | abhi chal raha: {state.get('working_on') or 'kuch nahi'}")
    return "\n".join(lines)


def security_text():
    lines = ["🛡 Suraksha jaanch"]
    mode = oct(SECRETS.stat().st_mode)[-3:]
    lines.append(f"{'✅' if mode == '700' else '⚠️'} secrets folder ({mode})")
    for f in SECRETS.glob("*"):
        m = oct(f.stat().st_mode)[-3:]
        lines.append(f"{'✅' if m == '600' else '⚠️'} {f.name} ({m})")
    lines.append("✅ Sirf aapka chat ID bot chala sakta hai")
    lines.append("✅ Token/key sirf VM par, GitHub copy mein kabhi nahi")
    return "\n".join(lines)


HELP = (f"📖 Sabhisaab Network v{VER}\n"
        "🗣 Normal baat mein likhein, jaise: 'pahadi ki ek video Valmiki Jayanti par banao' ya "
        "'money ka time 1 baje kar do' - bot samjhega, confirmation lega, phir karega.\n"
        "🎬 Abhi video - brand chuno, video banegi aur manzoori ke liye aayegi\n"
        "⏳ Pending - jo video manzoori mein hain\n"
        "✅ Thumb 1 se daalo / 🎨 Naye thumbnail / ❌ Mat daalo - sabse nayi pending video par\n"
        "📊 Aaj ka haal | 📅 7 din | 🖥 VM | 🩺 Sab theek? | 🛡 Suraksha\n"
        "⏸ Pause / ▶️ Resume - roz ka kaam roko/chalao\n\n"
        "Commands: /login (YouTube), /pinterest (Pinterest login), /gemini, /logs, /safai, /panic, /version\n"
        "🔐 /privacy - policy ka haal | 'data hatao <naam>' - kisi ka comment data turant mitao\n"
        "Pucho: 'kal ka plan', 'aaj kya kiya', 'views batao', 'khabar', 'kya seekha'\n"
        "Update: naya .tgz/.zip yahin bhej do. Website ZIP mein file ki koi ginti-seema nahi (v2.0).\n"
        "🔎 'seo seekh' - Google search se naye topic | 'auto deploy chalu/band' | 'purani video theek karo'\n"
        "🩺 'website doctor' - page index kyun nahi | 🔄 'upgrade haal' - khud-sudhaar | 'cf token <t>' / 'cf account <id>' - seedha deploy\n"
        "📡 'raasta haal' - Telegram ke raaste (seedha + Cloudflare relay) | 🆘 'backup setup' - Telegram band ho tab bhi khabar (ntfy)\n"
        "YouTube client JSON: file yahin bhej do (bot surakshit rakh kar message mita dega).")


def latest_waiting():
    w = [(j["created"], jid) for jid, j in pipeline.jobs().items() if j["status"] == "waiting"]
    return max(w)[1] if w else None


def do_login(brand):
    if not youtube.CLIENT.exists():
        return tg.say("❌ Pehle YouTube TV client ki JSON file yahin bhejein (sabhisaab-bot-tv).")
    dev = youtube.device_start()
    tg.say(f"🔑 {BRANDS[brand]['name']} jodna:\n1) Phone par kholein: {dev['verification_url']}\n"
           f"2) Code daalein: {dev['user_code']}\n3) mkpandey1989@gmail.com chunein, phir channel "
           f"'{BRANDS[brand]['name']}' chunein, Allow.\n⏳ 15 minute tak intezaar karunga.")
    tok = youtube.device_poll(dev)
    youtube.save_login("_new", tok)            # pehle alag file mein: purana sahi login kabhi na mite
    ch = youtube.channel_title("_new")
    norm = "".join(c for c in ch.lower() if c.isalnum())
    target = next((k for k, v in BRANDS.items()
                   if "".join(c for c in v["name"].lower() if c.isalnum()) in norm), None)
    tmp = youtube.token_path("_new")
    if not target:
        tmp.unlink(missing_ok=True)
        return tg.say(f"⛔ Ye '{ch}' channel kisi brand se match nahi hua, isliye kuch nahi badla.")
    tmp.replace(youtube.token_path(target))
    reopen_jobs()
    if target == brand:
        tg.say(f"✅ {BRANDS[brand]['name']} juda: channel '{ch}'")
    else:
        tg.say(f"ℹ️ Ye login '{ch}' channel ka nikla, to use {BRANDS[target]['name']} mein joda ✅ "
               f"(baaki kisi brand ka login nahi badla).\n{BRANDS[brand]['name']} ke liye /login dobara karein aur "
               f"account list mein email nahi, '{BRANDS[brand]['name']}' wala naam chunein.")
    for jid, j in pipeline.jobs().items():
        if j["status"] == "need_login" and j["brand"] == brand:
            j["status"] = "approved"
            pipeline.save_job(jid, j)


BUTTONS = ["🎬 Abhi video", "📺 Lamba video", "⏳ Pending", "🎨 Naye thumbnail", "✅ Thumb 1 se daalo", "❌ Mat daalo",
           "📊 Aaj ka haal", "📅 7 din", "💬 Comments", "🖥 VM", "🩺 Sab theek?", "©️ Copyright", "⚙️ Settings",
           "⏸ Pause", "▶️ Resume", "🎭 Mood video", "🛡 Suraksha", "📖 Poora menu"]


def _norm(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


NORM = {_norm(b): b for b in BUTTONS}
NORM.update({"sabthik": "🩺 Sab theek?", "sabthikhai": "🩺 Sab theek?", "sabtheekhai": "🩺 Sab theek?",
             "status": "🩺 Sab theek?", "health": "🩺 Sab theek?", "menu": "📖 Poora menu", "help": "📖 Poora menu",
             "report": "📊 Aaj ka haal", "aajkahal": "📊 Aaj ka haal", "video": "🎬 Abhi video",
             "videobanao": "🎬 Abhi video", "pending": "⏳ Pending", "login": "/login"})


def on_text(text):
    t = text.strip()
    if t not in BUTTONS and not t.startswith("/"):
        t = NORM.get(_norm(t), t)        # bina emoji / chhote-bade akshar bhi chalega
    if t in ("/start", "/menu", "📖 Poora menu", "/help"):
        tg.say(HELP, KB)
        return tg.say("Baaki sab yahan:", tg.inline([[(x, f"mn:{i}:{j}") for j, x in enumerate(r)]
                                                    for i, r in enumerate(MENU_ROWS)]))
    if t.lower().startswith(("data hatao ", "data delete ")):
        from . import privacy
        nm = t.split(None, 2)[2] if len(t.split(None, 2)) > 2 else ""
        return tg.say(privacy.forget(nm))
    if t in ("🔐 Privacy", "/privacy", "privacy jaanch", "privacy ka haal"):
        from . import privacy
        return run(lambda: tg.say(privacy.report()))
    tl = t.lower()
    if t in ("🩺 Website doctor", "/doctor") or tl in ("website doctor", "doctor"):
        from . import siteknow
        return run(lambda: tg.say(siteknow.doctor()))
    if t in ("🔄 Upgrade haal", "/upgrade") or tl in ("upgrade haal", "khud sudhaar"):
        from . import upgrader
        return tg.say(upgrader.report())
    if t in ("🔎 SEO seekh", "/seo") or tl in ("seo seekh", "seo report"):
        from . import marketing
        return run(lambda: tg.say(marketing.gsc_ideas()))
    if tl in ("purani video theek karo", "ginti theek karo"):
        from . import marketing
        return run(lambda: tg.say("🔁 " + marketing.recount()))
    if tl in ("auto deploy chalu", "auto deploy band"):
        state.put("auto_deploy", tl.endswith("chalu"))
        return tg.say("✅ Website ZIP ke 15 min baad deploy " + ("ab bot khud karega." if tl.endswith("chalu") else "ab aap dabayenge."))
    if tl in ("github history auto band", "github history auto chalu"):
        state.put("gh_squash_auto", tl.endswith("chalu"))
        return tg.say("✅ Har Ravivaar GitHub par sirf taaza copy: " + ("ON" if tl.endswith("chalu") else "OFF"))
    if t in ("🧠 Website gyaan taaza", "/gyaan"):
        from . import siteknow
        def _g():
            ch = siteknow.refresh(notify=False)
            tg.say(f"🧠 Website ke {len(siteknow.pages())} page padh liye." + ("\n" + "\n".join(ch) if ch else " Koi naya badlaav nahi."))
        return run(_g)
    if t in ("🧹 GitHub safai", "/github"):
        return tg.say("🧹 GitHub safai (site par koi asar nahi):\n1) Purane Worker bot + band cron ki file hatao\n"
                      "2) Website repo ki puraani history hata kar sirf taaza copy rakho (bot repo pehle se aisa hi hai)",
                      tg.inline([[("1️⃣ Purani file hatao", "gs:1"), ("2️⃣ History saaf", "gs:2")], [("❌ Kuch nahi", "gs:0")]]))
    if tl.startswith(("cf token ", "cf account ")):
        from . import website
        k = "CLOUDFLARE_API_TOKEN" if tl.startswith("cf token") else "CLOUDFLARE_ACCOUNT_ID"
        website.set_env(k, t.split(None, 2)[2].strip())
        ok = all(website._cf())
        if ok:                                # v2.0.7: dono mile to Telegram ka doosra raasta bhi khud banao
            from . import relay
            state.put("relay_try_at", 0)
            run(relay.auto)
        return tg.say("🔐 Cloudflare " + ("token" if "TOKEN" in k else "account ID") + " surakshit. " +
                      ("Ab '🚀 Website deploy' seedha VM se hoga, aur Telegram ka doosra raasta (Cloudflare relay) "
                       "ban raha hai - 1-2 min mein khabar." if ok else
                       "Doosra hissa bhi bhejein (cf token / cf account)."))
    if tl in ("raasta haal", "rasta haal", "relay haal", "telegram raasta", "telegram rasta", "/raasta"):
        from . import relay
        return tg.say(relay.status_text())
    if tl in ("relay banao", "relay dobara", "raasta banao", "rasta banao"):
        from . import relay
        state.put("relay_try_at", 0)
        return run(lambda: tg.say("📡 " + relay.deploy()))
    if tl in ("backup setup", "ntfy", "ntfy setup", "dusra raasta", "doosra raasta", "dusra rasta", "/backup"):
        from . import backup
        return tg.say(backup.setup_text())
    if tl == "backup menu":
        from . import backup
        return tg.say(backup.menu_text())
    if tl in ("backup test", "ntfy test"):
        from . import backup
        return tg.say("🆘 ntfy par test bheja: " + ("✅ gaya" if backup.send("Test: backup raasta chal raha hai.", "green")
                                                   else "❌ nahi gaya (ntfy.sh tak raasta nahi?)"))
    if tl in ("website zip auto chalu", "website zip auto band"):
        state.put("site_zip_auto", tl.endswith("chalu"))
        return tg.say("✅ Website ZIP ab " + ("bina pooche audit ke baad chadhegi (deploy phir bhi aap dabayein)." if tl.endswith("chalu")
                                              else "chadhane se pehle poochegi."))
    if t in ("👥 Website par aaj kitne log", "/traffic"):
        from . import website
        return run(lambda: tg.say(website.traffic(1)))
    if t in ("📁 Website ki file", "/files"):
        return tg.say("Kaunsi file chahiye? Likhein: 'website file emi' ya 'website file site' (poori site ZIP).")
    if t.lower().startswith("website file "):
        from . import website
        nm = t[13:].strip()
        return run(lambda: (lambda r: r and tg.say(r))(website.send_files(nm)))
    if t in ("🌐 Website haal", "/site"):
        from . import website
        tg.say("🌐 Website ki poori jaanch (GSC + GA4 + indexing + speed + audit) - 10-40 min lag sakte hain, report khud aayegi.")
        return run(website.daily)
    if t in ("📑 Indexing", "/index"):
        from . import website
        return run(lambda: (lambda r: r and tg.say(r))(website.index_report()))
    if t in ("🚀 Website deploy", "/deploy"):
        from . import website
        return tg.alert("yellow", "🚀 Website deploy karein? (audit + calculator test ke baad hi live hoga)",
                        tg.inline([[("✅ Haan, deploy", "wd:1"), ("❌ Nahi", "wd:0")]]))
    if t in ("🔎 Bing", "/bing"):
        from . import website
        return run(lambda: tg.say(website.bing_status()))
    if t in ("🛠 Website audit", "/audit"):
        from . import website
        return run(lambda: tg.say(website.audit_text()))
    if t in ("🧾 Mere kaam", "/kaam"):
        from . import tasks
        return run(lambda: tg.say(tasks.report()))
    if t in ("⚙️ Badlaav ka record", "/badlaav"):
        from . import diary
        rows = [r for r in diary.recent(1000) if r["kind"] in ("setting", "pakka")][-25:]
        return tg.say("⚙️ Aakhri badlaav (bot inhe kabhi nahi bhoolta):\n" + "\n".join(f"• {r['t'][5:16]} {r['text'][:90]}" for r in rows)
                      + "\n\n⏰ Abhi ka schedule: " + ", ".join(f"{BRANDS[k]['name']} {v}" for k, v in pipeline.schedule().items()))
    if "threads link laga diya" in t.lower():
        state.put("threads_links_ok", True)
        return tg.say("✅ Note: charon Threads profile par website link laga hai.")
    if t.lower().startswith("hub video "):
        parts = t.split()
        br = next((k for k in BRANDS if len(parts) > 2 and parts[2].lower() in (k, BRANDS[k]["name"].split()[0].lower())), None)
        vid = _re.search(r"(?:youtu\.be/|v=|shorts/)([A-Za-z0-9_-]{11})", t)
        if not br or not vid:
            return tg.say("Aise likhein: hub video money https://youtu.be/XXXXXXXXXXX")
        state.update("hub_videos", lambda d: {**(d or {}), br: vid.group(1)}, {})
        return tg.say(f"✅ {BRANDS[br]['name']} ki hub video set. Har Ravivaar Shorts ki Related-video list mein ye dikhegi.")
    if t.lower().startswith(("auto jawab band", "comment jawab band")):
        state.put("auto_reply", False)
        return tg.say("✅ Comment ke jawab ab pehle aapko dikhaunga (draft).")
    if t.lower().startswith(("auto jawab chalu", "comment jawab chalu")):
        state.put("auto_reply", True)
        return tg.say("✅ Comment ke jawab bot khud dega (7-45 min baad, vinamra; gaali/spam hata dega).")
    if t.lower().startswith(("list mein daalo", "todo ")):
        item = t.split(" ", 3)[-1] if t.lower().startswith("list") else t[5:]
        state.update("todo", lambda l: (l or []) + [{"t": time.strftime("%Y-%m-%d"), "x": item.strip()}], [])
        return tg.say(f"📌 Kaam list mein: {item.strip()}  (ho jaye to likhein: 'ho gaya <shabd>')")
    if t.lower().startswith("ho gaya "):
        from . import tasks
        gone = tasks.mark_done(t[8:])
        if not gone:
            dn = tasks.already_done(t[8:])
            if dn:
                return tg.say(f"✅ Ye pehle hi ho chuka hai ({dn[0].get('done', '')}): {dn[0]['x'][:120]}")
            return tg.say("Is shabd se koi khula kaam nahi mila. '🧾 Mere kaam' mein dekh kar wahi shabd likhein.")
        return tg.say("✅ List se hataya:\n" + "\n".join("• " + g["x"][:100] for g in gone) +
                      "\n(Itihaas mein rakha - docs/PENDING.md mein 'ho chuke' mein dikhega.)")
    if t.lower().strip() in ("purana bot band", "purana bot band hai", "old bot band"):
        state.put("old_bot_off", True)
        return tg.say("✅ Note kar liya: purana website bot band. Ab website ka saara kaam isi bot se.")
    if t.lower().startswith("bing key "):
        v = t.split(None, 2)[2].strip()
        return run(lambda: tg.say(save_secret32("bing", v)))
    if t.lower().startswith("meta secret "):
        v = t.split(None, 2)[2].strip()
        return run(lambda: tg.say(save_secret32("meta", v)))
    if t.lower().startswith("psi key "):
        from . import website
        website.set_env("PSI_KEY", t.split(None, 2)[2].strip())
        return tg.say("🔐 PageSpeed key surakshit.")
    if t in ("🏢 Company meeting", "/meeting"):
        from . import company
        tg.say("🏢 Saare vibhag ki meeting bula raha hoon (data ke saath)...")
        return run(company.meeting)
    if t in ("🔍 Duplicate jaanch", "/dups"):
        from . import growth
        tg.say("🔍 Charon channel aur page jaanch raha hoon...")
        return run(growth.duplicate_scan)
    if t in ("📅 Aaj ke tyohaar", "/tyohaar"):
        from . import calendar_in
        return tg.say(calendar_in.today_text() + "\n\n" + calendar_in.today_text(
            str(datetime.datetime.now(IST).date() + datetime.timedelta(days=1))))
    if t in ("📈 Growth graph", "/growth"):
        from . import growth
        tg.say("📈 Graph bana raha hoon...")
        return run(growth.send_growth)
    if t in ("🎬 Aakhri 5 video", "/last"):
        from . import growth
        return run(lambda: tg.say(growth.video_detail(5)))
    if t in ("🗑 Post hatao", "/delete"):
        lst = state.get("posted_log", [])[-5:]
        if not lst:            # purani posts (record se pehle ki): seedha channels se
            def _yt_list():
                allv = []
                for br in BRANDS:
                    if youtube.has_login(br):
                        try:
                            allv += youtube.recent_videos(br, 5)
                        except Exception:
                            pass
                allv = sorted(allv, key=lambda x: x["date"], reverse=True)[:5]
                if not allv:
                    return tg.say("Koi video nahi mili.")
                tg.say("🗑 Aakhri 5 YouTube video (sab channel). Kaunsi hatani hai?", tg.inline(
                    [[(f"{x['date'][5:16]} {BRANDS[x['brand']]['name'][:8]}: {x['title'][:24]}", f"yd:{x['brand']}:Y:{x['vid']}")]
                     for x in allv]))
            return run(_yt_list)
        return tg.say("🗑 Kaunsi post hatani hai? (aakhri 5)", tg.inline(
            [[(f"{x['date'][5:]} {BRANDS[x['brand']]['name'][:10]}: {x['title'][:28]}", f"dx:{x['jid']}")] for x in reversed(lst)]))
    if t == "📓 Aaj ka poora hisaab":
        from . import growth
        return tg.say(growth.day_report())
    if t in ("🗓 Kal ka plan", "/kal"):
        return tg.say(plan_text())
    if t == "📰 Khabar":
        from . import growth
        state.put("news_day", "")
        return run(growth.news_digest)
    if t in ("👀 Views", "/views"):
        from . import growth
        return tg.say(growth.views_report())
    if t in ("📒 Hafte ka hisaab", "/report"):
        from . import growth
        return tg.say(growth.weekly_report())
    if t in ("📓 Diary", "/diary"):
        from . import diary
        return tg.say(diary.text_view())
    if t == "📜 Logs":
        t = "/logs"
    if t == "🎬 Abhi video":
        return tg.say("Kis brand ki video?", tg.inline(pipeline.BRAND_BTNS))
    if t == "📺 Lamba video":
        return tg.say("Kis brand ki LAMBI video (8-12 min)? Raat ko banana behtar (30-60 min lagte hain).",
                      tg.inline([[(v["name"], f"lv:{k}")] for k, v in BRANDS.items()]))
    if t == "🎭 Mood video":
        return tg.say("Kaisa mood?", tg.inline([[(m, f"md:{i}")] for i, m in enumerate(MOODS)]))
    if t == "💬 Comments":
        from . import growth
        tg.say("💬 YouTube + Instagram ke naye comment dekh raha hoon...")
        run(growth.check_comments)
        return run(growth.check_ig_comments)
    if t == "©️ Copyright":
        return tg.say(COPYRIGHT)
    if t == "⏳ Pending":
        w = [(jid, j) for jid, j in pipeline.jobs().items() if j["status"] in ("waiting", "approved", "need_login", "making")]
        if not w:
            return tg.say("⏳ Koi pending video nahi.")
        for jid, j in w:
            tg.say(f"🆔 {jid} | {BRANDS[j['brand']]['name']} | {j['status']}\n{j.get('title', '')}",
                   pipeline.job_buttons(jid) if j["status"] == "waiting" else None)
        return
    if t in ("🎨 Naye thumbnail", "✅ Thumb 1 se daalo", "❌ Mat daalo"):
        jid = latest_waiting()
        if not jid:
            return tg.say("Koi video manzoori mein nahi hai.")
        if t.startswith("🎨"):
            return run(pipeline.new_thumbs, jid)
        if t.startswith("✅"):
            return tg.say(pipeline.approve(jid, 1, now_flag=True))
        return tg.say(pipeline.reject(jid))
    if t == "📊 Aaj ka haal":
        return tg.say(today_text())
    if t == "📅 7 din":
        return tg.say(week_text())
    if t == "🖥 VM":
        return tg.say(vm_text())
    if t == "🩺 Sab theek?":
        return tg.say(health_text())
    if t == "🛡 Suraksha":
        return tg.say(security_text())
    if t == "⚙️ Settings":
        return tg.say(f"⚙️ Settings\n🎙 Awaaz: Kokoro {VOICE}\n⏰ Roz: " +
                      ", ".join(f"{BRANDS[b]['name']} {s}" for b, s in pipeline.schedule().items()) +
                      f"\n🤖 Auto-upload (jawab na mile to): {'ON' if pipeline.auto_on() else 'OFF'}\n"
                      f"⬆️ Roz ki YouTube seema: {pipeline.max_uploads()}\n🧠 Gemini model: {state.get('gemini_last_model', '-')}\n"
                      f"🙏 Tyohaar story apne aap (Google search se tarikh pakki, 3 jaanch, raat 00:10 + muhurat par): {'ON' if state.get('auto_festival', True) else 'OFF'}\n"
                      "🌙 Raat 11-7: sirf 🔴 alert awaaz ke saath\n"
                      "Badalna ho to normal likhein, jaise:\n• 'deals ka time 5 baje kar do'\n• 'money roz 2 baar: 9 baje aur 7 baje'\n"
                      "• 'roz 8 video tak daalo'\n• 'pahadi par Uttarakhand GK ki video bhi banao'")
    if t in ("⏸ Pause", "/pause"):
        state.put("paused", True)
        return tg.say("⏸ Roz ka kaam roka. Pending video bhi upload nahi hongi. ▶️ Resume se chalu.")
    if t in ("▶️ Resume", "/resume"):
        state.put("paused", False)
        return tg.say("▶️ Bot phir chalu.")
    if t == "/panic":
        state.put("paused", True)
        for jid, j in pipeline.jobs().items():
            if j["status"] in ("approved", "queued"):
                j["status"] = "waiting"
                pipeline.save_job(jid, j)
        return tg.say("🛑 PANIC: sab upload roke, bot ruka. ▶️ Resume se phir chalu.")
    if t.startswith("/meta") or "token" in t.lower():
        return tg.say("Token seedha yahan paste kar dein (kisi bhi format mein). Bot khud pehchanega, VM par rakhega "
                      "aur message mita dega.\n• Meta: EAA... se shuru + App Secret (32 akshar)\n• Threads: TH... se shuru")
    if t == "/login":
        return tg.say("Kis channel ka YouTube login?", tg.inline(
            [[(f"🔑 {v['name']}", f"lg:{k}")] for k, v in BRANDS.items()]))
    if t == "/logs":
        try:
            lines = (LOGS / "engine.log").read_text(encoding="utf-8").splitlines()[-25:]
        except Exception:
            lines = ["(log khaali)"]
        return tg.say("📜 Log:\n" + "\n".join(lines))
    if t == "/safai":
        return tg.say(cleanup())
    if t == "/version":
        return tg.say(f"v{VER}")
    if t.lower() in ("/analytics", "analytics login", "analytics jodo", "🔗 analytics jodo"):
        from . import analytics as AN
        if not AN.CLIENT.exists():
            state.put("awaiting", "ya_client")
            return tg.say("📊 Analytics: yt-auto-desktop ka naya client secret (GOCSPX- se shuru, 35 akshar) yahan chipkaayein "
                          "ya JSON file bhejein. Main turant chat se mita dunga.")
        rows = [[(f"{'✅' if AN.has(b) else '🔑'} {v['name']}", f"ya:{b}")] for b, v in BRANDS.items()]
        return tg.say("📊 Kis channel ka Analytics jodna hai?", tg.inline(rows))
    if t.lower() in ("📊 analytics", "/retention", "analytics report"):
        from . import analytics as AN
        return run(lambda: tg.say(AN.report()))
    if t.lower() in ("pinterest secret naya", "pinterest secret badlo", "pinterest naya secret"):
        state.put("awaiting", "pin_secret")         # v2.0.8: secret reset ke baad naya secret
        return tg.say("📌 Pinterest ka NAYA App secret bhejein (developers.pinterest.com/apps → Manage → App secret key → "
                      "Show → copy). Message main turant mita dunga, phir login link dunga.")
    if t.lower() in ("/pinterest", "pinterest login", "pinterest jodo"):
        from . import pinterest as PI
        if not PI.has_secret():
            state.put("awaiting", "pin_secret")
            return tg.say("📌 Pinterest login: pehle App secret key bhejein (developers.pinterest.com/apps → Manage → "
                          "App secret key → Show → copy). Message main turant mita dunga.")
        return tg.say("📌 Ye link kholein, 'Allow' dabayein, phir browser upar ka POORA address (sabhisaab.com/?code=...) "
                      f"copy karke yahan bhejein:\n{PI.oauth_link()}")
    if "pinterest" in t.lower() and "test" in t.lower():
        from . import pinterest as PI
        def _test():
            from .thumbs import make as mk
            from .config import DATA, SITE
            p = mk("deals", {"lines": ["Sab Hisaab", "*Test Pin*"], "emoji": "📌", "tag": "Demo"}, DATA, "demo")[0]
            tg.say("📌 Test pin bani: " + PI.post_pin("deals", p, "Sab Hisaab test pin", "Demo pin by Sabhisaab Publisher",
                                                     SITE + "/?utm_source=pinterest&utm_campaign=demo"))
        return run(_test)
    if "pinterest" in t.lower() and ("live" in t.lower() or "standard mil" in t.lower()):
        from . import pinterest as PI
        try:
            return tg.say(PI.go_live())
        except Exception as e:
            return tg.alert("yellow", str(e))
    if ("report" in tl and any(w in tl for w in ("time", "samay", "timing", "kab aati", "kab aayegi"))
            and not re.search(r"\d{1,2}\s*([:.]\s*\d{2}|baje|am|pm)", tl)):
        from . import pipeline as _pl
        return tg.say(report_times_text() + "\n\n🎬 Video ka roz ka samay: " +
                      ", ".join(f"{BRANDS[b]['name']} {s}" for b, s in _pl.schedule().items()) +
                      "\nReport ka samay badalna: 'website report 8 baje' (dohri pushti ke baad).")
    if "chowkidar" in tl and any(w in tl for w in ("file", "code", "bhejo", "do")):
        from . import updater
        return run(lambda: tg.say(updater.send_chowkidar_file()))
    if tl in ("report time", "report ka samay", "report samay", "/reports"):
        return tg.say(report_times_text() + "\nBadalna ho to likhein: 'website report 8 baje' / 'din ki report 9:30 pm'.")
    prt = parse_report_time(t)
    if prt and any(w in tl for w in ("kar do", "kardo", "bhejo", "aaye", "chahiye", "set", "samay", "time", "baje")):
        key, hhmm = prt
        if key == "?":
            return tg.say("Kaunsi report? " + ", ".join(f"'{k}' = {v}" for k, v in REPORT_NAMES.items())
                          + f"\nJaise: 'website report {hhmm} baje'.")
        k2 = save_intent({"action": "set_report", "topic": key, "time": hhmm})
        from . import brain
        return tg.say(f"🤔 Maine samjha: {brain.summary({'action': 'set_report', 'topic': key, 'time': hhmm})}\nPakka karoon?",
                      tg.inline([[("✅ Haan", f"ix:{k2}:1"), ("❌ Nahi", f"ix:{k2}:0")]]))
    if re.search(r"road\s*map|handover|hand over|pending (list|file)|docs?\b|status file|ai[_ ]start", tl) and \
            any(w in tl for w in ("do", "de", "bhej", "file", "chahiye", "dena", "dikhao", "download")):
        from . import updater
        return run(lambda: tg.say(updater.send_docs(tl)))
    if tl in ("seo diary", "seo dayari", "seo diary do", "dayari", "/seodiary") or (("diary" in tl or "dayari" in tl) and "seo" in tl):
        from . import seodiary
        if any(w in tl for w in ("abh", "naya", "nayi", "update", "bana", "chala", "taaza", "aaj")) or not seodiary.FILE.exists():
            tg.say("📓 SEO diary: doosre channel/page abhi dekh raha hoon (5-10 min)...")
            return run(lambda: tg.say(seodiary.run()))
        return tg.say(seodiary.text_view())
    if tl in ("redirect jaanch", "redirect check", "redirect"):
        from . import website
        def _rd():
            ok, bad = website.redirect_check()
            tg.say(f"↪️ Redirect: {ok} theek" + (f", {len(bad)} galat:\n" + "\n".join(bad[:15]) if bad else " - sab sahi (GSC mein 'Validate fix' daba sakte hain)."))
        tg.say("↪️ Saare purane .html link jaanch raha hoon (5-10 min)...")
        return run(_rd)
    if tl in ("keywords", "keyword", "keyword list", "/keywords", "search keywords"):
        from . import marketing
        return tg.say(marketing.keyword_text())
    if tl in ("keywords taaza", "keyword taaza", "keywords update"):
        from . import marketing
        def _kw():
            md = marketing.keyword_bank()
            updater.mark_dirty()
            tg.say(marketing.keyword_text() if md else "GSC se data nahi mila (service account?).")
        return run(_kw)
    mk = re.match(r"keywords?\s+(haan|ha|nahi|na)\s+(\d+)", tl)
    if mk:
        from . import marketing
        r_ = marketing.keyword_mark(int(mk.group(2)), mk.group(1).startswith("h"))
        updater.mark_dirty()
        return tg.say(r_)
    if t == "/gemini":
        from . import brain
        lst = brain.discover(force=True)
        state.put("gemini_cool", {})
        return tg.say("🧠 Chalu Gemini model (pehla sabse taakatwar):\n" + ("\n".join(lst) or "List nahi mili - key/network jaanchein")
                      + f"\nAakhri galti: {state.get('gemini_last_error') or '-'}")
    return run(think, text)


def facts():
    from . import meta as M, threads as TH, pinterest as PI
    today = str(datetime.date.today())
    js = [f"{jid}: {BRANDS[j['brand']]['name']} status={j['status']} title={j.get('title', '')[:40]} "
          f"done={list((j.get('done') or {}).keys())}" for jid, j in pipeline.jobs().items()
          if j["status"] not in ("rejected",)][-10:]
    up = [f"{h['date']} {BRANDS[h['brand']]['name']}: {h['title'][:40]} https://youtu.be/{h['vid']}"
          for h in state.get("history", [])[-8:]]
    conn = []
    for k, v in BRANDS.items():
        mi = M.brand_info(k) if M.has_token() else None
        conn.append(f"{v['name']}: youtube={'ok' if youtube.has_login(k) else 'LOGIN BAAKI'}, "
                    f"facebook={'ok' if mi else 'nahi'}, instagram={'ok' if mi and mi.get('ig_id') else 'nahi'}, "
                    f"threads={'ok' if TH.info(k) else 'nahi'}")
    errs = [r["text"][:100] for r in __import__("app.diary", fromlist=["x"]).recent(5, ["galti"])]
    du = shutil.disk_usage("/")
    return (f"date={today}; version={VER}; paused={bool(state.get('paused'))}; auto_upload={pipeline.auto_on()}; "
            f"schedule={pipeline.schedule()}; uploads_today={pipeline.uploads_today()}/{MAX_UPLOADS_DAY}\n"
            f"connections: {'; '.join(conn)}; pinterest={PI.env() if PI.connected() else 'nahi'}; "
            f"meta_secret_problem={bool(M.has_token() and M._cfg().get('secret_bad'))}\n"
            f"jobs: {js}\nrecent uploads: {up}\nrecent errors: {errs}\n"
            f"vm: ram_free_mb={mem_avail_mb()}, disk_used_gb={du.used // 2**30}/{du.total // 2**30}, "
            f"load={os.getloadavg()[0]:.2f}; gemini={state.get('gemini_last_model', '-')}\n"
            f"plan_today={(state.get('plan') or {}).get(today, {})}; "
            f"plan_tomorrow={(state.get('plan') or {}).get(str(datetime.date.today() + datetime.timedelta(days=1)), {})}; "
            f"plan_waiting_approval={bool(state.get('plan_pending'))}; insights={(state.get('insights') or {}).get('summary', '-')}\n"
            f"today_diary_counts={_today_counts()}; last_dup_scan={state.get('dup_scan')}\n"
            f"website_jobs_on_vm={bool(state.get('old_crons_off'))}; old_website_bot_off={bool(state.get('old_bot_off'))}; "
            f"owner_rules={(state.get('rules') or [])[-10:]}; calendar_today={[e.get('name_en') for e in (state.get('calendar') or {}).get(today, [])]}")


def plan_text(d=None):
    if not d or not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        d = str(datetime.date.today() + datetime.timedelta(days=1))
    p = (state.get("plan") or {}).get(d) or (state.get("plan_pending") or {}).get(d)
    if not p:
        return (f"🗓 {d} ka koi manzoor plan nahi hai. Us din bot khud topic chunega (trend + website + aapke topic). "
                "Naya plan chahiye to likhein 'agle hafte ka plan banao'.")
    tag = "" if (state.get("plan") or {}).get(d) else " (abhi manzoori baaki)"
    return f"🗓 {d} ka plan{tag}:\n" + "\n".join(f"• {BRANDS[k]['name']} ({pipeline.schedule().get(k)}): {v}"
                                                  for k, v in p.items() if k in BRANDS)


def _today_counts():
    from . import diary
    today = str(datetime.datetime.now(IST).date())
    c = {}
    for r in diary.recent(500):
        if r["t"][:10] == today:
            c[r["kind"]] = c.get(r["kind"], 0) + 1
    return c


def think(text):
    """Normal baat samjho -> jawab do, ya badlaav se pehle confirmation."""
    from . import brain, diary
    diary.add("hukum", text)
    fx = facts()
    it = brain.understand(text, fx)
    for _ in range(2):                    # v2.0: Gemini ko data chahiye to bot tool chala kar dobara poochta hai
        need = [n for n in (it.get("need") or []) if isinstance(n, dict) and n.get("tool")][:3]
        if not need or it.get("action") != "chat":
            break
        from . import kb
        res = "\n".join(f"[{n['tool']} {n.get('arg', '')}]\n{kb.run_tool(n['tool'], str(n.get('arg', '')))[:2500]}" for n in need)
        it = brain.understand(text, fx, res)
    a = it["action"]
    if a == "doctor":
        from . import siteknow
        return run(lambda: tg.say(siteknow.doctor((it.get("topic") or "").strip("/ ") or None)))
    if a == "upgrade":
        from . import upgrader
        return tg.say(upgrader.report())
    if a == "show_plan":
        return tg.say(plan_text(it.get("time")))
    if a == "website" and (it.get("topic") or "").lower().strip() in ("traffic", "users", "visitors", "log"):
        from . import website
        return run(lambda: tg.say(website.traffic(int(it.get("count") or 1))))
    if a == "website" and (it.get("topic") or "").lower().startswith("file"):
        from . import website
        nm = (it.get("topic") or "").split(":", 1)[-1].strip() or "site"
        return run(lambda: (lambda r: r and tg.say(r))(website.send_files(nm)))
    if a == "website":
        m = {"report": "🌐 Website haal", "index": "📑 Indexing", "audit": "🛠 Website audit", "deploy": "🚀 Website deploy",
             "bing": "🔎 Bing"}
        return on_text(m.get((it.get("topic") or "report").lower().strip(), "🌐 Website haal"))
    if a == "tasks":
        return on_text("🧾 Mere kaam")
    if a == "web":
        q = it.get("topic") or ""
        def _web():
            from .brain import ask_grounded
            try:
                ans, src = ask_grounded("Answer in short Hinglish for an Indian user, exact dates/times in IST, mention if "
                                        "regions/panchang differ. Question: " + q)
                tg.say("🔎 " + ans.strip()[:3000] + ("\n\nSource: " + "\n".join(src[:3]) if src else ""))
            except Exception as e:
                tg.say(f"Google search se jawab nahi mila: {str(e)[:150]}")
        tg.say("🔎 Google search se pakka kar raha hoon...")
        return run(_web)
    if a == "dup_scan":
        return on_text("🔍 Duplicate jaanch")
    if a == "festivals":
        return on_text("📅 Aaj ke tyohaar")
    if a == "meeting":
        return on_text("🏢 Company meeting")
    if a == "rule" and not (it.get("topic") or "").strip():
        return tg.say("Kaunsa niyam? Jaise: 'aage se pahadi ki video mein gaana mat daalna'.")
    if a == "growth_graph":
        return on_text("📈 Growth graph")
    if a == "video_detail":
        from . import growth
        br = it.get("brand") if it.get("brand") in BRANDS else None
        pf = next((p for p in ("facebook", "instagram", "youtube") if p in (it.get("topic") or "").lower()), None)
        return run(lambda: tg.say(growth.video_detail(10 if br else 5, br, pf)))
    if a == "delete":
        return on_text("🗑 Post hatao")
    if a == "day_report":
        from . import growth
        return tg.say(growth.day_report())
    if a == "news":
        from . import growth
        state.put("news_day", "")
        tg.say("📰 Aaj ki kaam ki khabar dhoondh raha hoon...")
        return run(growth.news_digest)
    if a == "add_topic" and (not it.get("brand") or not it.get("topic")):
        return tg.say("Kis brand ke liye kaun sa topic? Jaise: 'pahadi par Uttarakhand GK ki video bhi banao'.")
    if a in ("plan", "insights"):
        from . import growth
        if a == "plan":
            tg.say("🗓 Agle 7 din ka plan bana raha hoon...")
            return run(growth.make_plan)
        return run(lambda: tg.say(growth.weekly_insights()))
    if a in ("comments", "report"):
        from . import growth
        if it.get("reply"):
            tg.say(it["reply"])
        if a == "comments":
            return on_text("💬 Comments")
        return tg.say(growth.weekly_report())
    if a == "views":
        from . import growth
        if it.get("reply"):
            tg.say(it["reply"])
        return tg.say(growth.views_report())
    simple = {"status": "🩺 Sab theek?", "today": "📊 Aaj ka haal", "week": "📅 7 din", "vm": "🖥 VM",
              "pending": "⏳ Pending", "logs": "/logs", "safety": "🛡 Suraksha", "help": "/help", "diary": "/diary"}
    if a in simple:
        if it.get("reply"):
            tg.say(it["reply"])
        return on_text(simple[a])
    if a in brain.CHANGES:
        if (a in ("make_video", "make_long") and not it.get("brand")) or (a == "set_schedule" and it.get("brand") in ("", "all", None)):
            return tg.say((it.get("reply") or "") + "\nKis brand ke liye?", tg.inline(
                [[(v["name"], f"ib:{k}:{save_intent(it)}")] for k, v in BRANDS.items()]))
        if a == "set_schedule" and not re.match(r"^\d{1,2}:\d{2}(,\s*\d{1,2}:\d{2})*$", it.get("time") or ""):
            return tg.say("Samay samajh nahi aaya. Aise likhein: 'money ka time 13:30 kar do' ya 'money roz 9 baje aur 19 baje'.")
        key = save_intent(it)
        return tg.say(f"🤔 Maine samjha: {brain.summary(it)}\nPakka karoon?",
                      tg.inline([[("✅ Haan", f"ix:{key}:1"), ("❌ Nahi", f"ix:{key}:0")]]))
    rep = it.get("reply") or "Samajh nahi aaya, thoda alag tarah se likhein."
    tg.say(rep)
    try:                                           # v2.0.4: har baat ka record; jo bot kar nahi paya wo AI ke liye
        from . import updater
        updater.log_query(text, a, rep)
    except Exception:
        log("log_query " + traceback.format_exc())


def save_intent(it):
    key = str(int(time.time() * 1000))[-7:]
    state.update("intents", lambda d: {**dict(list((d or {}).items())[-199:]), key: it}, {})
    return key


def do_intent(key, stage):
    from . import brain, diary
    it = (state.get("intents") or {}).get(key)
    if not it:
        return tg.say("Ye purana sawaal hai, dobara likhein.")
    a = it["action"]
    if a in brain.DOUBLE and stage == 1:
        return tg.say(f"⚠️ Dobara pakka? {brain.summary(it)}\nYe roz ke liye yaad rahega jab tak aap na badlein.",
                      tg.inline([[("✅✅ Haan, pakka", f"ix:{key}:2"), ("❌ Nahi", f"ix:{key}:0")]]))
    diary.add("pakka", brain.summary(it))
    b = it.get("brand")
    if a == "make_long":
        for br in (list(BRANDS) if b == "all" else [b]):
            run(pipeline.prepare, br, None, "lambi video", it.get("topic") or None, "long")
        return tg.say("⏳ Lambi video line mein (30-60 min).")
    if a == "make_video":
        for br in (list(BRANDS) if b == "all" else [b]):
            run(pipeline.prepare, br, None, "aapne maanga", it.get("topic") or None)
        return tg.say("⏳ Kaam line mein laga diya" + (" (charon brand, ek ke baad ek)" if b == "all" else "") + ".")
    if a == "set_schedule":
        val = ",".join(f"{int(x.split(':')[0]):02d}:{int(x.split(':')[1]):02d}" for x in it["time"].split(","))
        state.update("schedule", lambda d: {**(d or {}), b: val}, {})
        diary.add("setting", f"{BRANDS[b]['name']} roz {val}")
        return tg.say(f"✅ {BRANDS[b]['name']} ab roz {val} par. Yaad rakh liya.")
    if a == "platform":
        pf = next((x for x in ("youtube", "facebook", "instagram", "threads", "pinterest", "telegram")
                   if x in (it.get("topic") or "").lower()), None)
        brs = list(BRANDS) if it.get("brand") in ("all", "", None) else [it.get("brand")]
        if not pf or any(x not in BRANDS for x in brs):
            return tg.say("Kaunsa brand aur kaunsa platform? Jaise: 'money ka facebook band karo'.")
        def upd(d):
            d = dict(d or {})
            for x in brs:
                cur = set(d.get(x, []))
                cur.discard(pf) if it.get("auto") else cur.add(pf)
                d[x] = sorted(cur)
            return d
        state.update("platform_off", upd, {})
        diary.add("setting", f"{pf} {'chalu' if it.get('auto') else 'band'}: {', '.join(brs)}")
        return tg.say(f"✅ {', '.join(BRANDS[x]['name'] for x in brs)}: {pf} {'chalu' if it.get('auto') else 'band'}. "
                      "Ye setting hamesha yaad rahegi.")
    if a == "add_topic":
        brs = list(BRANDS) if it["brand"] == "all" else [it["brand"]]
        for br in brs:
            state.update("extra_topics", lambda d, br=br: {**(d or {}), br: ((d or {}).get(br, []) + [it["topic"]])[-30:]}, {})
        diary.add("setting", f"naya topic yaad: {it['topic']} ({', '.join(brs)})")
        return tg.say(f"✅ Yaad rakh liya: '{it['topic']}' - agli videos mein aayega ({', '.join(BRANDS[x]['name'] for x in brs)}).")
    if a == "rule":
        from . import company
        return tg.say(company.add_rule(it.get("topic") or ""))
    if a == "set_report":
        state.update("report_times", lambda d: {**(d or {}), it["topic"]: it["time"]}, {})
        diary.add("setting", f"report {it['topic']} roz {it['time']}")
        return tg.say(f"✅ '{it['topic']}' report ab roz theek {it['time']} baje. Yaad rakh liya.\n" + report_times_text())
    if a == "set_count":
        n = max(1, min(int(it.get("count") or 6), 12))
        state.put("max_uploads", n)
        diary.add("setting", f"roz ki seema {n}")
        return tg.say(f"✅ Roz zyada se zyada {n} YouTube upload." + (" (6 se upar YouTube API ki roz ki seema mein dikkat ho sakti hai)" if n > 6 else ""))
    if a == "set_auto":
        state.put("auto_approve", bool(it.get("auto")))
        diary.add("setting", f"auto-upload {'ON' if it.get('auto') else 'OFF'}")
        return tg.say(f"✅ Auto-upload {'ON' if it.get('auto') else 'OFF'}.")
    if a in ("pause", "resume"):
        return on_text("⏸ Pause" if a == "pause" else "▶️ Resume")
    jid = latest_waiting()
    if not jid:
        return tg.say("Koi video manzoori mein nahi hai.")
    if a == "approve":
        return tg.say(pipeline.approve(jid, int(it.get("thumb") or 1), now_flag=True))
    if a == "reject":
        return tg.say(pipeline.reject(jid))
    if a == "new_thumbs":
        return run(pipeline.new_thumbs, jid)


def meta_setup(msg, text):
    from . import meta as M
    tg.delete(msg["chat"]["id"], msg["message_id"])      # token chat mein na rahe
    parts = text.split()
    if len(parts) < 2:
        return tg.say("Format: /meta TOKEN APP_SECRET  (message apne aap mitega)")
    try:
        rep = M.save_token(parts[1], parts[2] if len(parts) > 2 else "")
    except Exception as e:
        return tg.say(f"❌ Meta token se pages nahi mile: {str(e)[:300]}")
    tg.say("🔐 Meta token surakshit (VM par, chat se mitaya).\n" + rep)
    for jid, j in pipeline.jobs().items():
        if j["status"] in ("need_login", "partial"):
            j["status"], j["tries"] = "approved", 0
            pipeline.save_job(jid, j)


import re as _re
PENDING_SECRETS = {}
RX_META = _re.compile(r"EAA[A-Za-z0-9]{40,}")
RX_SECRET = _re.compile(r"\b[0-9a-f]{32}\b")
RX_THREADS = _re.compile(r"\bTH[A-Za-z0-9_\-]{40,}")
RX_TGTOKEN = _re.compile(r"\b\d{8,12}:[A-Za-z0-9_\-]{30,}\b")
RX_PIN = _re.compile(r"\bpina_[A-Za-z0-9_\-]{20,}")


def reopen_jobs():
    """Naya login/token juda -> jo video us wajah se ruki thi, unhe phir chalao (jo platform ho chuka, dobara nahi)."""
    for jid, j in pipeline.jobs().items():
        if j["status"] in ("need_login", "partial"):
            j["status"], j["tries"] = "approved", 0
            pipeline.save_job(jid, j)


def secret_intake(msg, text):
    """Message mein token ho to: turant chat se mitao, VM par surakshit rakho, jaanch kar batao. Format ki chinta nahi."""
    cft = _re.search(r"\bcf[a-z]{2,3}_[A-Za-z0-9._\-]{20,}", text)
    if cft:                                   # v2.0.8: Cloudflare token bina 'cf token' ke bhi pakdo (Gemini tak kabhi nahi)
        tg.delete(msg["chat"]["id"], msg["message_id"])
        from . import website, relay
        website.set_env("CLOUDFLARE_API_TOKEN", cft.group())
        if all(website._cf()):
            state.put("relay_try_at", 0)
            run(relay.auto)
        tg.say("🔐 Cloudflare token mila (chat se mitaya)." + ("" if all(website._cf()) else " Ab 'cf account <id>' bhejein."))
        return True
    if _re.fullmatch(r"\s*[0-9a-f]{40}\s*", text):
        tg.delete(msg["chat"]["id"], msg["message_id"])
        tg.say("🔐 40 akshar ki key mili aur chat se mita di (kahin rakhi nahi). Agar ye Pinterest ka naya App secret hai to "
               "pehle likhein 'pinterest secret naya', phir dobara bhejein.")
        return True
    gh = _re.search(r"\b(github_pat_[A-Za-z0-9_]{40,}|ghp_[A-Za-z0-9]{30,})\b", text)
    if gh:
        tg.delete(msg["chat"]["id"], msg["message_id"])
        envf = SECRETS / "bot.env"
        lines = [l for l in envf.read_text().splitlines() if not l.startswith("GITHUB_TOKEN=")] if envf.exists() else []
        envf.write_text("\n".join(lines + [f"GITHUB_TOKEN={gh.group(1)}"]) + "\n")
        os.chmod(envf, 0o600)
        os.environ["GITHUB_TOKEN"] = gh.group(1)
        tg.say("🔐 GitHub token mila (chat se mitaya). " + updater.mirror())
        return True
    pin_tok = RX_PIN.search(text)
    if pin_tok:
        tg.delete(msg["chat"]["id"], msg["message_id"])
        from . import pinterest as PI
        try:
            tg.say("🔐 Pinterest token mila (chat se mitaya).\n" + PI.save_token(pin_tok.group()))
            reopen_jobs()
        except Exception as e:
            tg.alert("red", f"Pinterest token nahi chala: {str(e)[:300]}")
        return True
    meta_tok, threads_tok = RX_META.search(text), RX_THREADS.search(text)
    lone_secret = RX_SECRET.search(text) if not (meta_tok or threads_tok) else None
    if not (meta_tok or threads_tok or lone_secret or RX_TGTOKEN.search(text)):
        return False
    tg.delete(msg["chat"]["id"], msg["message_id"])
    if lone_secret:
        # v2.0.5: 32 akshar wali key Meta App Secret bhi ho sakti hai aur Bing API key bhi. Bina pooche kabhi mat badlo
        # (29 Oct: Bing key ne Meta secret ko badal diya tha -> Instagram/story ruk gaye).
        (SECRETS / "secret32.pending").write_text(lone_secret.group())
        (SECRETS / "secret32.pending").chmod(0o600)
        tg.say("🔐 32 akshar ki key mili (chat se mitaya). Ye kiski hai?",
               tg.inline([[("🅱️ Bing API key", "sk:bing"), ("📘 Meta App Secret", "sk:meta")], [("❌ Kisi ki nahi", "sk:no")]]))
        return True
    if False:
        from . import meta as M
        pend = SECRETS / "meta_secret.pending"
        if M.has_token():
            c = M._cfg()
            c["app_secret"] = lone_secret.group()
            c["secret_bad"] = False
            M.STORE.write_text(__import__("json").dumps(c))
            M.STORE.chmod(0o600)
            try:
                rep = M.discover()
                reopen_jobs()
                tg.say("🔐 App Secret mila aur juda (chat se mitaya).\n" + rep)
            except Exception as e:
                tg.say(f"🔐 App Secret rakha, par jaanch fail: {str(e)[:200]}")
        else:
            pend.write_text(lone_secret.group())
            pend.chmod(0o600)
            tg.say("🔐 App Secret mila, surakshit rakha (chat se mitaya). Ab Meta token (EAA...) bhejein.")
        return True
    if RX_TGTOKEN.search(text) and not (meta_tok or threads_tok):
        tg.say("🔴 Ye Telegram bot ka token lagta hai. Isse kahin share na karein. Message mita diya.")
        return True
    if meta_tok:
        from . import meta as M
        sec = RX_SECRET.search(text.replace(meta_tok.group(), ""))
        pend = SECRETS / "meta_secret.pending"
        secret = sec.group() if sec else (pend.read_text().strip() if pend.exists() else "")
        pend.unlink(missing_ok=True)
        try:
            rep = M.save_token(meta_tok.group(), secret)
            tg.say("🔐 Meta token mila, VM par surakshit, chat se mitaya.\n" + rep +
                   ("" if secret else "\nℹ️ App Secret nahi mila. Agar 'Require App Secret' ON hai to token + secret dobara bhejein."))
            for jid, j in pipeline.jobs().items():
                if j["status"] in ("need_login", "partial"):
                    j["status"], j["tries"] = "approved", 0
                    pipeline.save_job(jid, j)
        except Exception as e:
            tg.say(f"❌ Meta token se pages nahi mile: {str(e)[:300]}\nToken/permission jaanch kar dobara bhejein.")
    if threads_tok:
        key = str(int(time.time()))[-6:]
        PENDING_SECRETS[key] = threads_tok.group()
        tg.say("🔐 Threads token mila (chat se mitaya). Ye kis brand ka hai?",
               tg.inline([[(f"🧵 {v['name']}", f"th:{k}:{key}")] for k, v in BRANDS.items()]))
    return True


def save_secret32(kind, val):
    """Bing key ya Meta App Secret - pehle JAANCH, sahi ho tabhi rakho; galat ho to purana wapas."""
    from . import website, meta as M
    if kind == "bing":
        website.set_env("BING_API_KEY", val)
        st = website.bing_status()
        if "nahi diya" in st or "jaanch nahi" in st:
            return "🅱️ Bing ne ye key nahi maani: " + st
        return "🅱️ Bing key surakshit aur chal rahi hai.\n" + st
    if not M.has_token():
        (SECRETS / "meta_secret.pending").write_text(val)
        return "📘 App Secret rakha. Ab Meta token (EAA...) bhejein."
    c = M._cfg()
    old = c.get("app_secret", "")
    c.update(app_secret=val, secret_bad=False, app_secret_prev=old)
    M.STORE.write_text(__import__("json").dumps(c))
    M.STORE.chmod(0o600)
    try:
        rep = M.discover()
        if M._cfg().get("secret_bad"):
            raise RuntimeError("Meta ne secret nahi maana")
        reopen_jobs()
        return "📘 Meta App Secret juda, Instagram/story phir chalu.\n" + rep
    except Exception as e:
        c = M._cfg()
        c.update(app_secret=old, secret_bad=bool(c.get("secret_bad")))
        M.STORE.write_text(__import__("json").dumps(c))
        return f"📘 Ye Meta App Secret nahi laga, purana wapas rakha. ({str(e)[:120]})"


def fix_secret_mixup():
    """v2.0.5 (ek baar): 29 Oct ko Bing key Meta secret ki jagah chali gayi thi. Agar Meta secret 'galat' hai aur Bing key
    nahi hai, to wahi value Bing par jaancho; chal jaaye to Bing key bana do aur owner se asli Meta secret maango."""
    from . import website, meta as M
    if state.get("mixup_fixed") or not M.has_token():
        return
    state.put("mixup_fixed", True)
    c = M._cfg()
    val = c.get("app_secret") or ""
    if not c.get("secret_bad") or not _re.fullmatch(r"[0-9a-f]{32}", val) or website._env().get("BING_API_KEY"):
        return
    website.set_env("BING_API_KEY", val)
    st = website.bing_status()
    if "nahi diya" in st or "jaanch nahi" in st:
        website.set_env("BING_API_KEY", "")
        return
    c = M._cfg()
    c.update(app_secret="", secret_bad=True)            # Bing key ab Meta ki jagah nahi
    M.STORE.write_text(__import__("json").dumps(c))
    tg.alert("red", "🔧 Galti mili aur theek ki: aapki Bing key galti se Meta App Secret ki jagah chali gayi thi "
                    "(isliye Instagram aur story fail ho rahe the). Bing key ab sahi jagah hai:\n" + st +
             "\n\n📘 Ab asli Meta App Secret chahiye: developers.facebook.com → My Apps → Sabhisaab Publisher → "
             "App settings → Basic → App secret → Show → copy → bot ko likhein: meta secret <secret>")


def on_callback(cb):
    data = cb.get("data", "")
    tg.answer(cb["id"])
    kind, _, rest = data.partition(":")
    if kind == "sk":                               # v2.0.5: 32-akshar key kiski hai
        f = SECRETS / "secret32.pending"
        if not f.exists():
            return tg.say("Ye purana sawaal hai, key dobara bhejein.")
        val = f.read_text().strip()
        f.unlink(missing_ok=True)
        if rest == "no":
            return tg.say("Theek hai, key kahin nahi rakhi (mita di).")
        return run(lambda: tg.say(save_secret32("bing" if rest == "bing" else "meta", val)))
    if kind == "gs":
        if rest == "0":
            return tg.say("Theek hai, kuch nahi badla.")
        if rest in ("1", "2"):
            return tg.alert("yellow", "⚠️ Pakka? " + ("Purani file repo se hategi (history mein rahegi)." if rest == "1" else
                            "GitHub par website ki puraani history hamesha ke liye hategi (site/deploy par asar nahi)."),
                            tg.inline([[("✅✅ Haan", f"gs:{rest}y"), ("❌ Nahi", "gs:0")]]))
        from . import website
        return run(lambda: tg.say(website.remove_obsolete() if rest == "1y" else website.squash_history()))
    if kind in ("ws", "wi"):
        from . import website, files
        zs = state.get("site_zips") or {}
        z = zs.pop(rest, None)
        if not z:
            return tg.say("Ye ZIP purani ho gayi, dobara bhejein.")
        state.put("site_zips", zs)
        if kind == "wi":
            import pathlib as _p
            src = _p.Path(z["path"]).parent / "x"
            dest = files.save(_p.Path(z["path"]).stem)
            shutil.move(str(src), dest)
            return tg.say("📁 Inbox mein rakh di.")
        tg.say("🔍 Website audit chal raha hai (pehle jaanch, phir hi chadhega)...")
        return run(lambda: tg.say(website.apply_zip(z["path"], z.get("force"))))
    if data == "ack_all":
        from . import website
        try:
            import json as _j
            p = website.DIR / "state" / "alerts.json"
            d = _j.loads(p.read_text()) if p.exists() else {}
            for v in (d.values() if isinstance(d, dict) else []):
                if isinstance(v, dict):
                    v["ack"] = True
            p.write_text(_j.dumps(d))
            (website.KEEP / "alerts.json").write_text(_j.dumps(d))
        except Exception as e:
            log(f"ack: {e}")
        return tg.say("✅ Website ke purane alert band.")
    if data == "do:audit":
        from . import website
        return run(lambda: tg.say(website.audit_text()))
    if data == "m:idx":
        from . import website
        return run(lambda: (lambda r: r and tg.say(r))(website.index_report()))
    if data == "rm_unused":
        return tg.say("Faltu file hatane ke liye un file ki list wali ZIP/ya naam likhein - main bina pooche kuch nahi mitata.")
    if kind == "lv":
        from . import diary
        diary.add("pakka", f"lambi video: {rest}")
        return run(pipeline.prepare, rest, None, "lambi video", None, "long")
    if kind == "md":
        return tg.say(f"{MOODS[int(rest)]} - kis brand ki?",
                      tg.inline([[(v["name"], f"mb:{rest}:{k}")] for k, v in BRANDS.items()]))
    if kind == "mb":
        i, _, br = rest.partition(":")
        return run(pipeline.prepare, br, None, "mood video", None, "short", MOODS[int(i)][2:])
    if kind == "cv":
        state.put("use_clips_next", rest)
        return run(pipeline.prepare, rest, None, "aapki video se reel")
    if kind == "pv":
        state.put("use_photos_next", rest)
        return run(pipeline.prepare, rest, None, "aapki photo se video")
    if kind == "pb":
        br, _, name = rest.partition(":")
        return tg.say("Kis brand ki gallery mein daalun?", tg.inline(
            [[(v["name"], f"pm:{br}:{k}:{name}")] for k, v in BRANDS.items() if k != br]))
    if kind == "pm":
        src, dst, name = rest.split(":", 2)
        from .config import DATA
        (DATA / "photos" / dst).mkdir(parents=True, exist_ok=True)
        try:
            (DATA / "photos" / src / name).replace(DATA / "photos" / dst / name)
            return tg.say(f"✅ Photo {BRANDS[dst]['name']} gallery mein.")
        except Exception as e:
            return tg.say(f"Photo nahi mili: {e}")
    if kind == "wd":
        if rest != "1":
            return tg.say("Theek hai, deploy nahi kiya.")
        from . import website
        return run(lambda: tg.say(website.deploy()))
    if kind == "ya":
        from . import analytics as AN
        return tg.say(f"📊 {BRANDS[rest]['name']} Analytics:\n1) Ye link kholein: {AN.link(rest)}\n"
                      f"2) Account list mein '{BRANDS[rest]['name']}' wala naam chunein (email nahi, Pahadi ke liye email)\n"
                      "3) 'Google hasn't verified' aaye to Advanced → Go to ... → dono box tick → Continue\n"
                      "4) Page 'site can't be reached' dikhayega - ye theek hai. Upar ka POORA address (localhost/?state=...&code=...) "
                      "copy karke yahan bhejein.")
    if kind == "yd":
        br, plat, vid = rest.split(":", 2)
        return tg.alert("yellow", "⚠️ Pakka hatayein? Wapas nahi aayegi.",
                        tg.inline([[("✅✅ Haan, hatao", f"yy:{br}:{plat}:{vid}"), ("❌ Nahi", "dw:x:x")]]))
    if kind == "yy":
        br, plat, vid = rest.split(":", 2)
        from . import growth
        return run(lambda: tg.say(growth.delete_by_id(br, plat, vid)))
    if kind == "dx":
        x = next((p for p in state.get("posted_log", []) if p["jid"] == rest), None)
        if not x:
            return tg.say("Post nahi mili.")
        live = ", ".join(k for k, v in x.get("ids", {}).items() if v)
        return tg.say(f"🗑 {x['title']}\nAbhi yahan hai: {live or '-'}\nKahan se hatayein?",
                      tg.inline([[("🗑 Sab jagah se", f"dw:{rest}:all"), ("▶️ Sirf YouTube", f"dw:{rest}:youtube")],
                                 [("❌ Kuch nahi", "dw:x:x")]]))
    if kind == "dw":
        jid, _, where = rest.partition(":")
        if jid == "x":
            return tg.say("Theek hai, kuch nahi hataya.")
        return tg.alert("yellow", f"⚠️ Pakka? Hatayi hui post wapas nahi aayegi ({'sab jagah' if where == 'all' else where}).",
                        tg.inline([[("✅✅ Haan, hatao", f"dy:{jid}:{where}"), ("❌ Nahi", "dw:x:x")]]))
    if kind == "dy":
        jid, _, where = rest.partition(":")
        from . import growth
        return run(lambda: tg.say(growth.delete_post(jid, where)))
    if kind == "np":
        from . import growth
        return tg.say(growth.news_post(rest))
    if kind == "nv":
        d = (state.get("news_posts") or {}).get(rest)
        if not d:
            return tg.say("Ye khabar purani ho gayi.")
        return run(pipeline.prepare, d["brand"], None, "kaam ki khabar", d["text"][:120])
    if kind == "pl":
        from . import growth
        return tg.say(growth.approve_plan(rest == "ok"))
    if kind == "es":
        state.update("fest_done", lambda d: {**(d or {}), rest: 1}, {})
        from . import growth
        return run(lambda: tg.say(growth.festival_post(rest)))
    if kind == "ev":
        from . import growth
        e = (state.get("event_ideas") or {}).get(rest)
        if not e:
            return tg.say("Ye idea purana ho gaya.")
        from . import diary
        diary.add("pakka", f"event video: {e['idea']}")
        return run(pipeline.prepare, e["brand"], None, "aaj ka khaas din", e["idea"])
    if kind == "cr":
        from . import growth
        try:
            return tg.say(growth.send_reply(rest))
        except Exception as e:
            return tg.alert("yellow", f"Jawab nahi gaya: {str(e)[:200]}")
    if kind == "cx":
        return tg.say("⏭ Chhod diya.")
    if kind == "mn":
        i, _, j = rest.partition(":")
        return on_text(MENU_ROWS[int(i)][int(j)])
    if kind == "ix":
        key, _, stage = rest.partition(":")
        if stage == "0":
            return tg.say("❌ Theek hai, kuch nahi badla.")
        return do_intent(key, int(stage))
    if kind == "ib":
        b, _, key = rest.partition(":")
        it = (state.get("intents") or {}).get(key, {})
        it["brand"] = b
        k2 = save_intent(it)
        from . import brain
        return tg.say(f"🤔 Maine samjha: {brain.summary(it)}\nPakka karoon?",
                      tg.inline([[("✅ Haan", f"ix:{k2}:1"), ("❌ Nahi", f"ix:{k2}:0")]]))
    if kind == "mk":
        return run(pipeline.prepare, rest, None, "aapne maanga")
    if kind in ("ok", "go"):
        jid, _, th = rest.partition(":")
        return tg.say(pipeline.approve(jid, int(th or 1), now_flag=(kind == "go")))
    if kind == "nt":
        return run(pipeline.new_thumbs, rest)
    if kind == "no":
        return tg.say(pipeline.reject(rest))
    if kind == "lg":
        return run(do_login, rest)
    if kind == "th":
        brand, _, key = rest.partition(":")
        tok = PENDING_SECRETS.pop(key, None)
        if not tok:
            return tg.say("Token ka samay nikal gaya (bot restart hua). Dobara bhejein.")
        from . import threads as TH
        try:
            user = TH.save_token(brand, tok)
            reopen_jobs()
            return tg.say(f"✅ Threads juda: {BRANDS[brand]['name']} = @{user}")
        except Exception as e:
            return tg.say(f"❌ {str(e)[:300]}")
    if kind == "up":
        return run(updater.install, rest)
    if kind == "upno":
        shutil.rmtree(updater.UPD / rest, ignore_errors=True)
        return tg.say("❌ Update cancel.")


def on_document(msg):
    doc = msg["document"]
    name = doc.get("file_name", "")
    if name.endswith(".json"):
        SECRETS.mkdir(mode=0o700, exist_ok=True)
        tmp = SECRETS / "incoming.json"
        tg.download(doc["file_id"], tmp)
        txt = tmp.read_text()
        if '"service_account"' in txt and "private_key" in txt:
            from . import website
            tmp.replace(website.SA)
            website.SA.chmod(0o600)
            tg.delete(msg["chat"]["id"], msg["message_id"])
            return tg.say("🔐 Website ki Google service account file surakshit (chat se mitayi). Ab GSC + GA4 + indexing report "
                          "isi bot se aayegi. '📑 Indexing' dabakar dekh sakte hain.")
        if state.get("awaiting") == "ya_client" and "client_id" in txt:
            from . import analytics as AN
            tmp.replace(AN.CLIENT)
            AN.CLIENT.chmod(0o600)
            state.put("awaiting", "")
            tg.delete(msg["chat"]["id"], msg["message_id"])
            return tg.say("🔐 Analytics client file surakshit (chat se mitayi). Ab /analytics dabayein, har brand ka link milega.")
        if "client_id" in txt and "client_secret" in txt:
            tmp.replace(youtube.CLIENT)
            youtube.CLIENT.chmod(0o600)
            tg.delete(msg["chat"]["id"], msg["message_id"])
            return tg.say("🔐 YouTube client file surakshit rakh di, chat se mita di. Ab /login se channel jodein.")
        tmp.unlink(missing_ok=True)
        return tg.say("Ye JSON YouTube client file nahi lagti.")
    if updater.receive(doc) is None:
        save_media(doc["file_id"], name, doc.get("file_size", 0))


def save_photo(file_id, caption=""):
    """Aapki photo -> gallery (brand ke hisaab se). Video/thumbnail/story mein kaam aayegi."""
    from .config import DATA
    from . import diary
    cap = caption.lower()
    br = next((k for k, v in BRANDS.items() if k in cap or v["name"].split()[0].lower() in cap), "pahadi")
    d = DATA / "photos" / br
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{time.strftime('%Y%m%d-%H%M%S')}.jpg"
    tg.download(file_id, p)
    n = len(list(d.glob("*.jpg")))
    diary.add("file", f"photo gallery {br}: {p.name}")
    tg.say(f"📸 Photo {BRANDS[br]['name']} gallery mein rakh di (kul {n}). {BRANDS[br]['name']} ki videos mein ab ye "
           "background ban kar aayengi.", tg.inline([[("🎬 Abhi in photo se video", f"pv:{br}"),
                                                       ("🔁 Doosre brand ki", f"pb:{br}:{p.name}")]]))
    if caption and not any(w in cap for w in BRANDS):
        run(think, caption)


def save_clip(file_id, size, caption=""):
    """Aapki mobile video -> clip gallery. Bot isse background bana kar upar text + awaaz ke saath video banata hai."""
    from .config import DATA
    from . import diary
    if size > TG_MAX_MB * 1024 * 1024:
        return tg.alert("yellow", f"Telegram bot {TG_MAX_MB} MB se badi video nahi le sakta. Chhoti (20-40 sec) video bhejein.")
    cap = caption.lower()
    br = next((k for k, v in BRANDS.items() if k in cap or v["name"].split()[0].lower() in cap), "pahadi")
    d = DATA / "clips" / br
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{time.strftime('%Y%m%d-%H%M%S')}.mp4"
    tg.download(file_id, p)
    diary.add("file", f"video clip {br}: {p.name}")
    tg.say(f"🎥 Video {BRANDS[br]['name']} gallery mein (kul {len(list(d.glob('*.mp4')))}). Agli videos mein background "
           "banegi, upar text + awaaz.", tg.inline([[("🎬 Abhi is video se reel", f"cv:{br}")]]))
    if caption and not any(w in cap for w in BRANDS):
        run(think, caption)


def save_media(file_id, name, size):
    from . import files, diary
    if size > TG_MAX_MB * 1024 * 1024:
        return tg.alert("yellow", f"Telegram bot {TG_MAX_MB} MB se badi file nahi utaar sakta. Chhota karke bhejein.")
    p = files.save(name)
    tg.download(file_id, p)
    diary.add("file", f"inbox: {p.name}")
    tg.say(f"📁 Mil gayi aur surakshit rakh di: {p.name}\nIska kya karna hai, normal baat mein bata dein "
           "(jaise 'is photo par pahadi ki story banao').")


def recover():
    """Restart ke baad adhoore kaam theek karo."""
    made = state.get("made_today", {})
    for jid, j in pipeline.jobs().items():
        if j["status"] == "making":
            j["status"] = "failed"
            pipeline.save_job(jid, j)
            s = j.get("slot", "")
            made.pop(f"{s[:10]}:{j['brand']}:{s[11:16]}", None)
        elif j["status"] in ("queued", "uploading"):
            j["status"] = "approved"
            pipeline.save_job(jid, j)
    state.put("made_today", made)


def main():
    owner = tg.owner_id()
    state.put("installing", 0)
    try:
        from . import guardtext
        guardtext.install()        # v2.0.2: har caption/comment/DM/description mein sahi ginti + poora link
        threading.Timer(90, lambda: safe(fix_secret_mixup)).start()        # v2.0.5: Bing/Meta key mix-up theek
    except Exception:
        log("guardtext " + traceback.format_exc())
    try:
        from . import privacy
        privacy.migrate()          # v2.0: audience platform-wise
    except Exception:
        log("privacy migrate " + traceback.format_exc())
    try:
        n_ = updater.scrub_logs()                     # v2.0.8: purane log se token mitao
        if n_:
            log(f"scrub_logs: {n_} line saaf")
    except Exception:
        log("scrub " + traceback.format_exc())
    recover()
    tg.set_commands([("menu", "Poora menu"), ("login", "YouTube channel jodna"), ("logs", "Log"),
                     ("safai", "Safai"), ("panic", "Sab roko"), ("version", "Version")])
    pend = state.get("pending_update")
    msg = f"🤖 Sabhisaab Network v{VER} chalu (24x7)."
    if pend:
        state.put("pending_update", None)
        msg = f"✅ Update safal: v{VER} chalu."
        run(lambda: tg.say(updater.mirror()))
    tg.say(msg, KB)
    threading.Thread(target=worker, daemon=True).start()
    threading.Thread(target=up_worker, daemon=True).start()
    threading.Thread(target=scheduler, daemon=True).start()
    try:                                                   # v2.0.7: Telegram band ho tab bhi chhote hukum (ntfy)
        from . import backup
        backup.topics()
        threading.Thread(target=lambda: backup.poll(lambda x: safe(on_text, x)), daemon=True).start()
    except Exception:
        log("ntfy start " + traceback.format_exc())
    offset = state.get("tg_offset", 0)
    while True:
        try:
            ups = tg.get_updates(offset)
            if state.get("conflict_told"):
                state.put("conflict_told", False)
            for u in ups:
                offset = u["update_id"] + 1
                state.put("tg_offset", offset)
                m = u.get("message") or {}
                cb = u.get("callback_query")
                if m and time.time() - m.get("date", time.time()) > 900:
                    log(f"purana message chhoda ({int(time.time() - m.get('date', 0))}s purana)")
                    continue          # restart/update ke baad purane message dobara na chalein
                who = (cb or m).get("from", {}).get("id")
                if who != owner:
                    continue   # sirf owner
                if cb:
                    on_callback(cb)
                elif m.get("document"):
                    on_document(m)
                elif m.get("photo"):
                    ph = m["photo"][-1]
                    save_photo(ph["file_id"], m.get("caption") or "")
                elif m.get("video"):
                    v = m["video"]
                    save_clip(v["file_id"], v.get("file_size", 0), m.get("caption") or "")
                elif m.get("text") and state.get("awaiting") == "pin_secret" and not m["text"].startswith("/"):
                    from . import pinterest as PI
                    tg.delete(m["chat"]["id"], m["message_id"])
                    PI.save_secret(m["text"].strip())
                    state.put("awaiting", "")
                    tg.say("🔐 Pinterest App secret surakshit (chat se mitaya). Ab ye link kholein, Allow dabayein, "
                           f"phir browser ka POORA address yahan bhejein:\n{PI.oauth_link()}")
                elif m.get("text") and "code=" in m["text"] and "localhost" in m["text"]:
                    from . import analytics as AN
                    tg.delete(m["chat"]["id"], m["message_id"])
                    try:
                        br_, title = AN.exchange(m["text"])
                        tg.say(f"✅ Analytics juda: {BRANDS[br_]['name']} (channel '{title}'). Asli retention ab, "
                               "CTR report YouTube 1-2 din mein dena shuru karega.")
                    except Exception as e:
                        tg.alert("yellow", f"Analytics login nahi hua: {str(e)[:200]}\n/analytics se naya link lein (code 10 min chalta hai).")
                elif m.get("text") and "code=" in m["text"] and "sabhisaab.com" in m["text"]:
                    from . import pinterest as PI
                    tg.delete(m["chat"]["id"], m["message_id"])
                    try:
                        user = PI.exchange(m["text"])
                        tg.say(f"✅ Pinterest juda (login): @{user}. Ab likhein 'pinterest test pin banao'.")
                    except Exception as e:
                        tg.alert("yellow", f"Pinterest login nahi hua: {str(e)[:200]}\n/pinterest se dobara karein (code 10 min mein expire hota hai).")
                elif m.get("text") and _re.search(r"GOCSPX-[A-Za-z0-9_\-]{20,}", m["text"]):
                    # Google ab JSON download nahi deta: sirf secret chipkao, client ID bot jaanta hai (yt-auto-desktop)
                    import json as _j
                    from . import analytics as AN
                    sec = _re.search(r"GOCSPX-[A-Za-z0-9_\-]{20,}", m["text"]).group()
                    cid = _re.search(r"\d{6,}-[a-z0-9]+\.apps\.googleusercontent\.com", m["text"])
                    tg.delete(m["chat"]["id"], m["message_id"])
                    AN.CLIENT.write_text(_j.dumps({"installed": {
                        "client_id": cid.group() if cid else AN.DESKTOP_ID, "client_secret": sec,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost"]}}))
                    AN.CLIENT.chmod(0o600)
                    state.put("awaiting", "")
                    tg.say(f"🔐 Analytics secret surakshit ({len(sec)} akshar, chat se mitaya). Ab /analytics dabayein - "
                           "har brand ka login button milega.")
                elif m.get("text") and m["text"].lower().strip().startswith(("bing key ", "psi key ", "cf token ", "cf account ", "meta secret ")):
                    tg.delete(m["chat"]["id"], m["message_id"])
                    on_text(m["text"])
                elif m.get("text") and secret_intake(m, m["text"]):
                    pass
                elif m.get("text") and m.get("reply_to_message") and _re.search(
                        r"\b(delete|del|hatao|hata do|mita do|mitao|remove)\b", m["text"].lower()):
                    r_ = m["reply_to_message"]                       # v2.0.4: jis message ka reply, wahi mitao (sach mein)
                    try:
                        tg.delete(m["chat"]["id"], r_["message_id"])
                        tg.delete(m["chat"]["id"], m["message_id"])
                        rest = _re.sub(r"\b(isko|ise|ye|yeh|is)?\s*(delete|del|hatao|hata do|mita do|mitao|remove)\s*(kar do|karo|kardo)?\b",
                                       "", m["text"], flags=_re.I)
                        rest = _re.sub(r"^[\s,.]*(aur|and|bhi)?[\s,.]*", "", _re.sub(r"\b(bot bhai|bhai)\b", "", rest, flags=_re.I)).strip()
                        tg.say("🗑 Wo message mita diya.")
                        if len(rest) > 6:
                            on_text(rest)
                    except Exception as e:
                        tg.say(f"Mita nahi paya (Telegram 48 ghante se purana bot message mitane nahi deta): {str(e)[:80]}")
                elif m.get("text"):
                    try:
                        updater.log_chat(m["text"])                    # v2.0.6: owner ki har baat (secret chhupa kar)
                    except Exception:
                        pass
                    on_text(m["text"])
        except Exception as e:
            log("LOOP ERROR " + traceback.format_exc())
            if "Doosra program" in str(e):
                if not state.get("conflict_told"):
                    state.put("conflict_told", True)
                    tg.say(f"⚠️ {e}")
                time.sleep(60)
            time.sleep(5)


if __name__ == "__main__":
    main()
