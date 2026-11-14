"""Sabhisaab Network - 24x7 Telegram control bot (sirf owner). Chalana: systemd sabhinet.service"""
import datetime
import re
import os
import queue
import shutil
import subprocess
import threading
import time
import json
import pathlib
import traceback
from . import tg, state, pipeline, youtube, updater, learn
from . import ytcomment as _ytc_mod
from .config import BASE, BRANDS, SCHEDULE, AUTO_APPROVE, SECRETS, LOGS, VOICE, MAX_UPLOADS_DAY, IST, TG_MAX_MB
from .guard import cleanup, mem_avail_mb
from .log import log

VER = (BASE / "VERSION").read_text().strip()
STARTED = time.time()
WORK = queue.Queue()
UPWORK = queue.Queue()      # upload alag line: video banne ke kaam ke peeche nahi rukta (samay par post)
KB = tg.reply_keyboard([
    ["🎬 Abhi video", "⏳ Pending", "📊 Aaj ka haal"],
    ["🧪 Namoona", "🎨 24 Look", "💬 Comment haal"],      # v2.3.3: owner - sample/look/comment saamne
    ["⚙️ Channel setup"],                                  # v2.7.2: channel-wise line-wise setting + FINAL
    ["🩺 Sab theek?", "⏸ Pause", "▶️ Resume"],
    ["⏰ Best time", "👑 Pro 50 Deck", "📖 Poora menu"],
])
PRO = {"📈 Poora haal": "poora haal", "🌐 Link se traffic": "aaj website par kitne log aaye", "🔎 Google jaanch": "google jaanch",
       "💬 Comment haal": "comment haal", "📮 Bing + index": "bing haal", "📡 Raasta haal": "raasta haal",
       "🔎 VM audit": "vm audit", "🛡 Chowkidar fix": "chowkidar fix", "🆘 Backup setup": "backup setup",
       "📅 Hafte ka traffic": "is hafte website par kitne log aaye", "📮 Aaj index bhejo": "index bhejo",
       "🧾 Kaam (number)": "🧾 Mere kaam"}          # v2.1.8: pro buttons -> seedhe hukum
MENU_ROWS = [["📈 Poora haal", "🌐 Link se traffic", "📅 Hafte ka traffic"],
             ["🔎 Google jaanch", "📮 Bing + index", "📮 Aaj index bhejo"],
             ["💬 Comment haal", "📡 Raasta haal", "🔎 VM audit"],
             ["🛡 Chowkidar fix", "🆘 Backup setup", "🧾 Kaam (number)"],
             ["📓 Aaj ka poora hisaab", "🗓 Kal ka plan", "📰 Khabar"],
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
             ["🧹 GitHub safai", "🧠 Website gyaan taaza", "🔎 SEO seekh"],
             ["🧪 Sample studio", "📅 Din-plan", "📘 Studio manual"],
             ["📏 Quota haal", "🙈 Gemini Blindfold", "🧹 Deep Safai"],
             ["🔐 Web Vault (8099)", "🎨 9 Visual Style", "🎛 HUD"],
             ["🔊 Awaaz", "🎚 QC", "🖼 Carousel"],
             ["🧩 11-Mode Puzzle/GK", "📲 WhatsApp Card", "🎯 Exam sawal"],
             ["💰 Revenue Roadmap", "🎯 Scroll jaanch", "📸 Photo Gallery"],
             ["🌐 Website draft", "👑 Pro 50 Deck", "🏆 6x Audit (asli)"],
             ["🚨 Exam Alerts", "🔢 Reel Code Khoj", "🚩 Doubt/Error Shield"],
             ["🧊 Apna 3D", "🏦 Sawal bank", "📈 Kul hisaab"],
             ["📌 Pinterest haal", "🧹 Kachra saaf", "🗓 Schedule"],
             ["🔑 Token haal", "💾 Backup", "📜 Provenance"]]
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
    last_reap = 0
    while True:
        try:
            pipeline.tick(run, run_up)
            if time.time() - last_reap > 900:                # v2.3.0: sirf apna atka ffmpeg (40 min+) band
                last_reap = time.time()
                try:
                    from .guard import reap_stuck_ffmpeg
                    k_ = reap_stuck_ffmpeg(40)
                    if k_:
                        tg.alert("yellow", "🧹 Atka ffmpeg band kiya (sirf sabhinet ka): " + "; ".join(k_)[:300])
                except Exception as e:
                    log(f"reap: {e}")
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
            if time.time() - state.get("comments_at", 0) > 45 * 60 and not state.get("paused"):     # v2.3.3: 2 ghante -> 45 min
                state.put("comments_at", time.time())
                from . import growth

                def _cm():                                 # v2.9.9: alag thread - lambi video (30-60 min) ke peeche nahi atakta
                    for f_ in (growth.check_comments, growth.check_ig_comments, growth.check_fb_comments):
                        safe(f_)
                threading.Thread(target=_cm, daemon=True, name="comments").start()
            day = str(nowt.date())
            if nowt.weekday() == 6 and nowt.strftime("%H:%M") >= "10:30" and state.get("selfaudit_day") != str(nowt.date()):
                state.put("selfaudit_day", str(nowt.date()))     # v2.1.6: har Ravivaar khud ka audit (sirf padhta hai)
                def _sa():
                    from . import vmaudit, guard as _g
                    _g.cleanup()
                    txt_, F_ = vmaudit.run_all()
                    red_ = [f for f in F_ if f[0] == "🔴"]
                    if red_:
                        tg.say(vmaudit.run_and_send())
                    else:
                        tg.say(f"🟢 Hafte ka self-audit: koi zaroori kami nahi (🟡 {len(F_)} chhoti baatein). Safai bhi ho gayi.")
                run(_sa)
            if nowt.strftime("%H:%M") >= "11:20" and state.get("index_day") != str(nowt.date()) and not state.get("paused"):
                state.put("index_day", str(nowt.date()))        # v2.1.6: roz sitemap (Google) + naye page (Bing/IndexNow)
                from . import website as _w
                def _di():
                    r_ = _w.daily_index()
                    log("daily index: " + r_)
                    if "❌" in r_ or "HTTP 4" in r_:
                        tg.alert("yellow", "📮 Roz ki indexing mein dikkat: " + r_ + "\nIlaaj: bot mein 'google jaanch'")
                run(_di)
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
            if nowt.strftime("%H:%M") >= "21:15" and state.get("milestone_day") != day:      # v2.3.0: padaav ki badhai
                state.put("milestone_day", day)

                def _ms():
                    from . import company as _CP
                    for m_ in _CP.milestone_check():
                        tg.alert("green", m_)
                run(_ms)
            try:                                       # v3.3.0: page queue - roz 06:40 ke baad ek baar + deploy ke baad sandesh
                from . import pagequeue as _PQ
                if _PQ.due(nowt):
                    if state.get("pq_try_day") != day:
                        state.put("pq_try_day", day)
                        run(_PQ.run_day)
                if state.get("pq_notify"):
                    run(_PQ.tick)
                if _PQ.gidx_due(nowt):                 # v3.3.2: roz 11:30 ke baad Google index ka haal (sirf padhna)
                    state.put("pq_gidx_day", day)
                    run(_PQ.gidx_run)
                if _PQ.fresh_due(nowt):                # v3.3.2 audit-6: Somvaar - purani pad chuki baat ki suchi (content nahi badalta)
                    state.put("pq_fresh_wk", nowt.strftime("%G-W%V"))
                    run(_PQ.fresh_run)
            except Exception as _e:
                log(f"pagequeue loop: {_e}")
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
            for i_r, r_ in enumerate(state.get("routines") or []):              # v2.3.7: owner ke roz ke hukum
                k_r = f"rt_{i_r}_{r_.get('t')}"
                if nowt.strftime("%H:%M") >= r_.get("t", "99:99") and (state.get("routine_done") or {}).get(k_r) != day:
                    state.update("routine_done", lambda d, k=k_r: {**(d or {}), k: day}, {})
                    log(f"routine {r_}")
                    threading.Thread(target=lambda c=r_["cmd"]: safe(on_text, c), daemon=True).start()
            if time.time() - state.get("wd_at", 0) > 1800:        # v2.5.5: watchdog - dikkat par step-wise sandesh
                def _wd():
                    from . import watchdog as _W2
                    _W2.tick()
                    _W2.weekly(nowt.weekday(), nowt.strftime("%H:%M"), day)
                run(_wd)
            if time.time() - state.get("up_at", 0) > 600:         # v2.5.3: halka uptime (10 min), spam nahi
                def _up():
                    from . import canary as _C
                    _C.uptime_tick()
                run(_up)
            if "10:20" <= nowt.strftime("%H:%M") < "12:00" and state.get("fact_day") != day and not state.get("paused"):
                def _fw():                                  # v2.6.1: sarkari-dar watcher (khud din chunta hai)
                    from . import factwatch as _F
                    r_ = _F.run()
                    if "badli" in r_ or "ruka" in r_:
                        log(r_)
                run(_fw)
            if "03:30" <= nowt.strftime("%H:%M") < "05:00" and time.time() - float(state.get("pw_at", 0) or 0) > 3 * 86400:
                def _pw():                                  # v2.6.1: policy/API badlaav watcher (har 3 din)
                    from . import policywatch as _P
                    log(_P.run())
                run(_pw)
            if "07:40" <= nowt.strftime("%H:%M") < "09:00" and state.get("kwfix_day") != day and state.get("kwfix_auto", True):
                def _kf():                                  # v2.6.1: GSC shabd par pakka-ganit FAQ (roz max 2 page)
                    from . import kwfix as _K
                    log(_K.run())
                run(_kf)
            if nowt.weekday() == 6 and nowt.strftime("%H:%M") >= "22:00" and state.get("scan_day") != day:   # Ravivaar raat: site scan (sirf padhna)
                state.put("scan_day", day)
                def _scan():
                    from . import sitescan as _S
                    tg.say(_S.run())
                    if state.get("linkfix_auto", True):       # v2.6.0: galat related-link khud theek (audit gate ke saath)
                        tg.say(_S.autofix())
                run(_scan)
            if state.get("jawab_site_on"):        # v2.5.2: live-check (marker, 1 ghanta / 20 min), reconcile, alert - answers.tick
                def _jl():
                    from . import answers as _A
                    _A.tick()
                run(_jl)
            jv = state.get("jawab_verify") or {}
            if jv.get("at") and time.time() >= float(jv["at"]):     # v2.9.2: 15 min baad pakka - naya jawab live par hai?
                state.put("jawab_verify", {})
                def _jv(aid=jv.get("aid")):
                    from . import answers as _A
                    miss = _A.coverage_check(5)
                    if miss:
                        log(_A.publish_site(force=True))
                        tg.alert("yellow", f"🌐 /jawab par naya jawab 15 min mein nahi dikha ({', '.join(map(str, miss[:3]))}) - dobara bheja.")
                run(_jv)
            if state.get("answer_dirty") and time.time() - state.get("jawab_pub_at", 0) > 30 * 60:   # v2.5.0: /jawab page
                state.put("jawab_pub_at", time.time())

                def _jw():
                    from . import answers as _A
                    log(_A.publish_site())
                run(_jw)
            if not state.get("jawab_asked") and state.get("answer_offsite", True):       # v2.5.0: ek baar owner se pushti
                state.put("jawab_asked", True)
                tg.say("✅ NAYA: reel mein ab sirf sawal + 'jawab comment karo'; SAHI JAWAB Telegram channel par (abhi se chalu) aur "
                       "website ke https://sabhisaab.com/jawab page par (code ke saath).\nWebsite par ye page bot roz apne aap update "
                       "kare? (site audit pass hone par hi live; koi aur page nahi chhedta)",
                       tg.inline([[("✅ Haan, website par bhi", "s41:on"), ("❌ Sirf Telegram", "s41:off")]]))
            if nowt.strftime("%H:%M") >= "02:15" and state.get("bk_day") != day:      # v2.4.0: roz encrypted offsite backup
                state.put("bk_day", day)

                def _bk():
                    from . import ops as _O
                    _O.make_backup()
                    if nowt.weekday() == 6:
                        r_ = _O.restore_drill()
                        if not r_.startswith("✅"):
                            tg.alert("yellow", "💾 " + r_)
                run(_bk)
            if nowt.strftime("%H:%M") >= "06:20" and state.get("ops_day") != day:     # v2.4.0: token + API jaanch
                state.put("ops_day", day)

                def _ops():
                    from . import ops as _O
                    _O.token_watch()
                    _O.contract_tests()
                    from . import pinterest as _P
                    if nowt.weekday() == 0:
                        log(_P.ab_learn())
                run(_ops)
            if nowt.weekday() == 2 and nowt.strftime("%H:%M") >= "11:00" and state.get("lay_week") != day:   # v2.4.0
                state.put("lay_week", day)
                from . import studio as _ST
                run(_ST.propose_layout)
            if time.time() - state.get("lay_check_at", 0) > 3600:
                state.put("lay_check_at", time.time())
                from . import studio as _ST
                run(_ST.layout_auto_check)
            if nowt.strftime("%H:%M") >= "05:45" and state.get("heal_day") != day:     # v2.3.7: roz khud-jaanch + khud-ilaaj
                state.put("heal_day", day)

                def _heal():
                    from . import elite_audit as _EA
                    _EA.daily_heal()
                run(_heal)
            if "08:00" <= nowt.strftime("%H:%M") <= "22:00" and time.time() - state.get("pin_drip_at", 0) > 90 * 60 \
                    and state.get("pin_drip_on", True) and not state.get("paused"):      # v2.3.7: Pinterest drip (website page)
                state.put("pin_drip_at", time.time())

                def _drip():
                    from . import pinterest as _PI
                    log(_PI.drip_pin())
                run(_drip)
            if nowt.weekday() == 6 and nowt.strftime("%H:%M") >= "11:00" and state.get("pal_week") != day:   # v2.3.6
                state.put("pal_week", day)
                from . import studio as _ST
                run(_ST.propose_palette)
            if time.time() - state.get("pal_check_at", 0) > 3600:
                state.put("pal_check_at", time.time())
                from . import studio as _ST
                run(_ST.palette_auto_check)
            if (state.get("cal_offline_days") and time.time() - state.get("cal_retry_at", 0) > 6 * 3600
                    and nowt.strftime("%H:%M") >= "00:30"):            # v2.3.6: Google seema laut aaye to offline din pakke karo
                state.put("cal_retry_at", time.time())
                from . import calendar_in
                run(calendar_in.refresh)
            if nowt.strftime("%H:%M") >= "00:02" and state.get("cal_day") != day:
                state.put("cal_day", day)
                from . import calendar_in
                run(calendar_in.refresh)
            if (nowt.strftime("%H:%M") >= "07:00" and state.get("cal_day") == day and state.get("greet_day") != day
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
            if state.get("bk_pass_saved") is False and nowt.strftime("%H:%M") >= "10:05" and state.get("bkpass_remind_day") != day:
                state.put("bkpass_remind_day", day)       # v2.7.1: naya backup password save hone tak roz ek yaad
                tg.say("🔐 Yaad: naya backup password abhi 'save' mark nahi hua. 'backup password' likh kar dekhein, kahin likh lein, "
                       "phir 'backup password save' likhein.")
            if (not state.get("votes_on") and state.get("votes_auto", True) and "11:30" <= nowt.strftime("%H:%M") < "12:00"
                    and state.get("votes_try_day") != day):
                state.put("votes_try_day", day)            # v2.8.0: asli % engine apne aap (Cloudflare token ho to); fail = kal phir
                def _vt():
                    from . import votes as _VT
                    r_ = _VT.setup()
                    tg.say(r_ if r_.startswith("✅") else "ℹ️ " + r_ + "\n(kal phir apne aap koshish)")
                run(_vt)
            if (state.get("sitescan_last") or {}).get("v", 0) < 260 and state.get("scan_fix_day") != day \
                    and "04:30" <= nowt.strftime("%H:%M") < "05:30":
                state.put("scan_fix_day", day)             # v2.8.1: purani ginti (105) ki jagah naye scanner se taaza
                def _rs():
                    from . import sitescan as _S
                    _S.run()
                    if state.get("linkfix_auto", True):
                        log(_S.autofix())
                run(_rs)
            if "03:10" <= nowt.strftime("%H:%M") < "04:00" and state.get("qclean_day") != day:
                state.put("qclean_day", day)               # v2.7.3: kaam ke nahi purane sawal/script roz apne aap saaf
                def _qc():
                    from . import qplan as _QP
                    n_ = _QP.cleanup()
                    if n_:
                        log(f"qplan cleanup: {n_} hataye")
                run(_qc)
            if nowt.weekday() == 6 and "23:10" <= nowt.strftime("%H:%M") < "23:50" and state.get("qadapt_day") != day:
                state.put("qadapt_day", day)               # v2.8.1: sawal-type views ke hisaab se (owner ka plan nahi chhedta)
                def _qa():
                    from . import qplan as _QP
                    r_ = _QP.weekly_adapt()
                    if r_:
                        tg.say(r_ + "\n(Wapas purana: 'sawal plan reset')")
                run(_qa)
            if "14:00" <= nowt.strftime("%H:%M") < "15:00" and state.get("ab_day") != day:
                state.put("ab_day", day)                   # v2.9.1: lambi video ka A/B thumbnail (analytics login ho to)
                def _ab():
                    from . import abtest as _AB
                    r_ = _AB.tick()
                    if r_:
                        tg.say(r_)
                run(_ab)
            if "17:10" <= nowt.strftime("%H:%M") < "18:00" and state.get("toolpin_day") != day and state.get("toolpin_on", True):
                state.put("toolpin_day", day)              # v2.9.1: roz 1 website-tool pin (Pinterest link click hote hain)
                def _tp():
                    from . import toolpin as _TP
                    log(_TP.run())
                run(_tp)
            if nowt.weekday() == 5 and "20:00" <= nowt.strftime("%H:%M") < "21:00" and state.get("ideas_day") != day:
                state.put("ideas_day", day)                # v2.9.1: comment se hafte ka idea (sirf owner ko)
                def _id():
                    from . import ideas as _ID
                    r_ = _ID.weekly()
                    if r_:
                        tg.say(r_)
                run(_id)
            if int(time.time()) % 600 < 25:               # v2.9.5: quiz bot ka thread zinda rahe
                try:
                    from . import quizbot as _QBw
                    if _QBw.ensure():
                        log("quizbot: dobara chalu kiya")
                except Exception:
                    pass
            if "21:05" <= nowt.strftime("%H:%M") < "22:00" and state.get("trend_day") != day:
                state.put("trend_day", day)                # v2.9.9: roz raat website traffic - 15 din ausat se tulna
                def _tt():
                    from . import website as _WT
                    tg.say(_WT.traffic_trend())
                run(_tt)
            if nowt.weekday() == 6 and "09:30" <= nowt.strftime("%H:%M") < "10:30" and state.get("psi_day") != day:
                state.put("psi_day", day)                  # v2.9.5: hafte mein website speed (PageSpeed) - key ho to
                run(lambda: tg.say(psi_weekly()))
            if not state.get("sitepatch_v292") and time.time() - STARTED > 120 and state.get("sitepatch_try") != day:
                state.put("sitepatch_try", day)            # v2.9.2: ZIP ke saath aaya website-sudhaar ek baar
                def _sp():
                    from . import website as _WSP
                    r_ = _WSP.sitepatch_apply()
                    if r_:
                        tg.say(r_)
                run(_sp)
            if not state.get("ownermode_v312") and time.time() - STARTED > 300 and state.get("ownermode_try") != day:
                state.put("ownermode_try", day)            # v3.1.2: owner ki apni visit Analytics mein na gini jaaye - code ek baar har page par
                def _om():
                    from . import ownermode as _OM
                    r_ = _OM.apply()
                    if r_:
                        tg.say(r_)
                run(_om)
            if "19:05" <= nowt.strftime("%H:%M") < "20:00" and state.get("push_day") != day and state.get("push_on"):
                state.put("push_day", day)                 # v2.9.2: roz max 1 website notification (opt-in walon ko)
                def _ps():
                    from . import push as _PS
                    log(_PS.send_daily())
                run(_ps)
            if "08:00" <= nowt.strftime("%H:%M") < "09:00" and state.get("quizd_day") != day and state.get("quiz_subs"):
                state.put("quizd_day", day)                # v2.9.2: quiz bot - sirf /roz chunne walon ko
                def _qd():
                    from . import quizbot as _QB
                    log(f"quizbot roz: {_QB.daily()}")
                run(_qd)
            if nowt.weekday() == 0 and "10:30" <= nowt.strftime("%H:%M") < "11:30" and state.get("learn_day") != day:
                state.put("learn_day", day)                # v2.9.4: hafte mein ek baar - jo nahi samjha usse seekhna (pushti se)
                def _lp():
                    r_ = learn_propose()
                    if r_:
                        tg.say(*r_)
                run(_lp)
            STORY_DAYS = {1: "pahadi", 3: "money", 5: "deals", 6: "sunonatak"}   # v2.9.1: Web Story har brand hafte mein ek
            if nowt.weekday() in STORY_DAYS and "12:15" <= nowt.strftime("%H:%M") < "13:30" and state.get("story_day") != day \
                    and state.get("stories_on", True):
                state.put("story_day", day)
                def _ws(br=STORY_DAYS[nowt.weekday()]):
                    from . import webstory as _WS
                    log(_WS.publish(br))
                run(_ws)
            HUB_DAYS = {0: "pahadi", 2: "money", 4: "deals", 6: "sunonatak"}   # v2.7.0: har brand ki har hafte apni hub video
            if nowt.weekday() in HUB_DAYS and "01:30" <= nowt.strftime("%H:%M") < "02:30" and state.get("long_day") != str(nowt.date()) \
                    and not state.get("paused"):
                state.put("long_day", str(nowt.date()))
                br = HUB_DAYS[nowt.weekday()]                       # Som Pahadi, Budh Money, Shukra Deals, Ravi Suno Natak
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
                run(lambda: (log("recount: " + marketing.recount()), log("jawab links: " + marketing.jawab_links())))   # ek ke baad ek (description takraav nahi)
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
            if "14:05" <= nowt.strftime("%H:%M") < "16:00" and state.get("bank_day2") != day and not state.get("paused"):
                state.put("bank_day2", day)                          # v2.3.2: Gemini ki free seema ~13:30 IST par taazi hoti hai
                run(lambda: log("bank (taazi seema): " + "; ".join(pipeline.bank_refill())))
            if "01:00" <= nowt.strftime("%H:%M") < "05:00" and state.get("bank_day") != day and not state.get("paused"):
                state.put("bank_day", day)                                               # v2.0.3: script bank bhara rahe
                def _bank():
                    made = pipeline.bank_refill()
                    if made:
                        log("bank: " + "; ".join(made))
                run(_bank)
            if nowt.strftime("%H:%M") >= "06:40" and state.get("bing_try_day") != day:     # v2.3.1: Bing URL submission quota
                state.put("bing_try_day", day)

                def _bing():
                    from . import website as _WB
                    log(_WB.bing_submit_daily())
                run(_bing)
            if time.time() - state.get("qbank_retry_at", 0) > 3 * 3600 and not state.get("paused"):   # v2.3.6: har 3 ghante
                state.put("qbank_retry_at", time.time())

                def _qb3():
                    from . import qbank as _QB
                    _QB.fill_all(max_cats=3)
                run(_qb3)
            for _qt in ("01:20", "14:20"):                                    # v2.3.5: anant sawal-bank (Gemini taazi seema ke baad)
                if nowt.strftime("%H:%M") >= _qt and state.get("qbank_" + _qt) != day and not state.get("paused"):
                    state.put("qbank_" + _qt, day)

                    def _qb():
                        from . import qbank as _QB
                        _QB.fill_all()
                    run(_qb)
            if "03:10" <= nowt.strftime("%H:%M") < "05:00" and state.get("b3d_try") != day and state.get("use_3d", True):
                state.put("b3d_try", day)                                   # v2.3.3: apna 3D - Blender raat ko ek baar install

                def _b3d():
                    import shutil as _sh
                    from . import blender3d as _B3
                    if not _sh.which("blender"):
                        r_ = _B3.install()
                        tg.alert("green" if r_.startswith("✅") else "yellow", "🧊 " + r_)
                    if _sh.which("blender") and not (state.get("img3d_count") or 0):      # v2.3.4: bana nahi to khud jaanch + repair
                        t_ = _B3.self_test()
                        if "✅" not in t_:
                            t_ = _B3.repair()
                        tg.alert("green" if "3D theek hai" in t_ else "yellow", t_[:1500])
                    _B3.cleanup()
                run(_b3d)
            if "02:30" <= nowt.strftime("%H:%M") < "05:30" and state.get("spare_day") != day and not state.get("paused"):
                state.put("spare_day", day)                                              # v2.3.0: spare reel bank bhara rahe
                run(lambda: log(pipeline.spare_reel_refill()))
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
        if j["status"] != "sample" and (j.get("created", "")[:10] == today or j["status"] in ("waiting", "approved", "need_login")):
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
    return (f"🖥 VM\n🧠 RAM khaali: {mem_avail_mb()} MB\n💾 Disk: {du.used / 1e9:.0f}/{du.total / 1e9:.0f} GB\n"
            f"⚙️ Load: {load[0]:.2f} {load[1]:.2f}\n" + "\n".join(svc))


def health_text():
    up = int((time.time() - STARTED) / 60)
    from . import brain
    gm, ge = state.get("gemini_last_model", "-"), state.get("gemini_last_error", "")
    lines = [f"🩺 Sab theek? (v{VER}, chalu {up} min)",
             f"{'✅' if os.environ.get('GEMINI_API_KEY') and not ge else '🔴'} Gemini: {gm}" + (f" | galti: {ge[:120]}" if ge else ""),
             "🧠 Model kram: " + " > ".join(f"{m}{'✅' if (state.get('gemini_status') or {}).get(m) == 'ok' else ('⚠️' if (state.get('gemini_status') or {}).get(m) else '')}"
                                          for m in brain._models()[:4]) or "🧠 (list nahi mili)",
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
        ok_, why_ = TH.alive(bk) if i else (False, "")
        lines.append(f"{'✅' if i and ok_ else ('🔴' if i else '🔑')} {bv['name']} Threads" +
                     ((f" @{i['username']}" + ("" if ok_ else f" - token KHATAM: Meta developer se naya Threads token (TH... wala) chat mein paste karein, bot brand poochega"))
                      if i else " token baaki"))
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
        "🆕 v2.3.0: /pro50 (50-button deck) | /sample /manual /styles /hud /awaaz /qc /carousel | /puzzles /card /exam "
        "'code 123' | /revenue /scroll /gallery /dpdp /examalerts | /quota /blindfold /deepsafai /vault | /webpage | /audit6x\n"
        "🆕 v2.3.3: 🧪 Namoona | 🎨 24 Look (/looks) | ⏰ Best time (/besttime) | 🧊 Apna 3D (/3d) | 💬 Comment haal\n"
        "Pucho: 'kal ka plan', 'aaj kya kiya', 'views batao', 'khabar', 'kya seekha'\n"
        "Update: naya .tgz/.zip yahin bhej do. Website ZIP mein file ki koi ginti-seema nahi (v2.0).\n"
        "🔎 'seo seekh' - Google search se naye topic | 'auto deploy chalu/band' | 'purani video theek karo'\n"
        "🩺 'website doctor' - page index kyun nahi | 🔄 'upgrade haal' - khud-sudhaar | 'cf token <t>' / 'cf account <id>' - seedha deploy\n"
        "🔎 'vm audit' - poore VM ki jaanch (sirf padhta hai) | 🛡 'chowkidar fix'\n"
        "📡 'raasta haal' - Telegram ke raaste (seedha + Cloudflare relay) | 🆘 'backup setup' - Telegram band ho tab bhi khabar (ntfy)\n"
        "YouTube client JSON: file yahin bhej do (bot surakshit rakh kar message mita dega).")

# ---------------- v2.3.0 Step 7 (v11 se): 👑 50-BUTTON PRO DECK - har button hamare asli kaam par ----------------
PRO_DECK_PANELS = {
    "A": ("🎬 Panel A (1-10): Visual style + reel", [
        [("1. 3D Mascot", "pe:1"), ("2. Worker Chart", "pe:2")],
        [("3. Stick-Figure Mic", "pe:3"), ("4. Liquid Match", "pe:4")],
        [("5. Mystery Box", "pe:5"), ("6. Tyohaar/Dhol", "pe:6")],
        [("7. Jeevit Fasal", "pe:7"), ("8. Puzzle Board", "pe:8")],
        [("9. Shuddh Hindi", "pe:9"), ("10. Carousel (5 slide)", "pe:10")],
        [("⬅️ 50-Button Deck", "pe:home")]]),
    "B": ("📅 Panel B (11-18): Roz ka kaam + 4 channel", [
        [("11. Panchang badge", "pe:11"), ("12. Money video", "pe:12")],
        [("13. Deals video", "pe:13"), ("14. Pahadi video", "pe:14")],
        [("15. Suno Natak video", "pe:15"), ("16. Sarkari exam khabar", "pe:16")],
        [("17. Rewatch code (challenge)", "pe:17"), ("18. Lambi video", "pe:18")],
        [("⬅️ 50-Button Deck", "pe:home")]]),
    "C": ("🛡️ Panel C (19-26): Audit, niyam, DPDP, solver", [
        [("19. 6-pass asli audit", "pe:19"), ("20. 6-stage deep audit", "pe:20")],
        [("21. AI label jaanch", "pe:21"), ("22. DPDP ledger", "pe:22")],
        [("23. Dual-solver ganit", "pe:23"), ("24. Duplicate jaanch", "pe:24")],
        [("25. Awaaz LUFS + contrast QC", "pe:25"), ("26. Niti badlaav / upgrade", "pe:26")],
        [("⬅️ 50-Button Deck", "pe:home")]]),
    "D": ("🚀 Panel D (27-34): Post, wapsi, DM, funnel", [
        [("27. Autopilot CHALU", "pe:27"), ("28. Manzoori par roko", "pe:28")],
        [("29. Post hatao", "pe:29"), ("30. Atka kaam dobara", "pe:30")],
        [("31. Comment-DM haal", "pe:31"), ("32. Story jaanch", "pe:32")],
        [("33. Vinamra jawab ON/OFF", "pe:33"), ("34. WhatsApp card", "pe:34")],
        [("⬅️ 50-Button Deck", "pe:home")]]),
    "E": ("🌐 Panel E (35-42): Website + kamai", [
        [("35. Website doctor", "pe:35"), ("36. Website gyaan taaza", "pe:36")],
        [("37. Sawal-galti shield", "pe:37"), ("38. Website page draft", "pe:38")],
        [("39. GSC/Bing haal", "pe:39"), ("40. Traffic + kitni der ruke", "pe:40")],
        [("41. Kamai roadmap", "pe:41"), ("42. Retention/thakaan", "pe:42")],
        [("⬅️ 50-Button Deck", "pe:home")]]),
    "F": ("🖥️ Panel F (43-50): VM, suraksha, gallery, vault", [
        [("43. VM haal (sirf padhna)", "pe:43"), ("44. Deep safai", "pe:44")],
        [("45. Gemini Blindfold", "pe:45"), ("46. Ek file mangao", "pe:46")],
        [("47. Mere kaam (pending)", "pe:47"), ("48. Diary", "pe:48")],
        [("49. Raasta haal (relay/ntfy)", "pe:49"), ("50. PANIC - sab roko", "pe:50")],
        [("⬅️ 50-Button Deck", "pe:home")]]),
}
PE_STYLE = {1: "mascot_3d", 2: "organ_workers", 3: "stick_mic", 4: "liquid_match", 5: "mystery_box", 6: "festive_dhol",
            7: "living_object", 8: "puzzle_grid"}
PE_TEXT = {10: "/carousel", 16: "🚨 Exam Alerts", 18: "📺 Lamba video", 19: "🏆 6x Audit (asli)", 20: "🛡 6-Stage Audit",
           22: "/dpdp", 23: "/exam", 24: "🔍 Duplicate jaanch", 25: "/qc", 26: "🔄 Upgrade haal", 29: "🗑 Post hatao",
           32: "story jaanch", 34: "/card", 35: "🩺 Website doctor", 36: "🧠 Website gyaan taaza", 37: "🚩 Doubt/Error Shield",
           38: "/webpage", 39: "🔎 Bing", 40: "👥 Website par aaj kitne log", 41: "/revenue", 42: "/scroll", 43: "🖥 VM",
           44: "🧹 Deep Safai", 45: "/blindfold", 47: "🧾 Mere kaam", 48: "📓 Diary", 49: "📡 Raasta haal", 50: "/panic"}


def send_pro_deck_home():
    rows = [[("🎬 A (1-10) Visual + reel", "pe:panel:A"), ("📅 B (11-18) Roz + channel", "pe:panel:B")],
            [("🛡️ C (19-26) Audit + niyam", "pe:panel:C"), ("🚀 D (27-34) Post + DM", "pe:panel:D")],
            [("🌐 E (35-42) Website + kamai", "pe:panel:E"), ("🖥️ F (43-50) VM + suraksha", "pe:panel:F")]]
    return tg.say("👑 50-BUTTON PRO DECK — 6 panel, har button asli kaam (setting badle to dohri pushti):", tg.inline(rows))


def _latest_meta():
    """v2.3.0: sabse nayi bani video ka meta (QC / carousel ke liye)."""
    import json as _j
    best = None
    for jid, j in pipeline.jobs().items():
        try:
            if j.get("meta") and (pathlib.Path(j["meta"]) / "meta.json").exists():
                if not best or j.get("created", "") > best[0]:
                    best = (j.get("created", ""), j["meta"])
        except Exception:
            pass
    if not best:
        return None
    return _j.loads((pathlib.Path(best[1]) / "meta.json").read_text(encoding="utf-8"))


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
    if text.startswith("__fz__"):                  # v2.7.2: fuzzy se sudhra hua command (ek hi baar)
        text = text[6:]
    _la = (state.get("learned_alias") or {}).get(text.strip().lower())
    if _la and not text.startswith("__la__"):      # v2.9.4: owner ki pushti se seekha hua matlab
        text = _la
    t = text.strip()
    if t not in BUTTONS and not t.startswith("/"):
        t = NORM.get(_norm(t), t)        # bina emoji / chhote-bade akshar bhi chalega
    t = PRO.get(t, t)
    if t in ("/start", "/menu", "📖 Poora menu", "/help"):
        tg.say(HELP, KB)
        return tg.say("Baaki sab yahan:", tg.inline([[(x, f"mn:{i}:{j}") for j, x in enumerate(r)]
                                                    for i, r in enumerate(MENU_ROWS)]))
    if t.lower().startswith(("data hatao ", "data delete ")):            # v2.3.0: sahmati bhi wapas + data mitao
        from . import privacy
        nm = t.split(None, 2)[2] if len(t.split(None, 2)) > 2 else ""
        return tg.say(privacy.withdraw_consent(nm))
    if t.lower().startswith("consent jodo "):
        from . import privacy
        nm = t.split(None, 2)[2] if len(t.split(None, 2)) > 2 else "guest"
        r_ = privacy.record_consent(nm)
        return tg.say("✅ Sahmati darj: " + json.dumps(r_.get("record", r_), ensure_ascii=False)[:300] if r_.get("ok") else "⛔ " + r_["reason"])
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
        val = t.split(None, 2)[2].strip()
        if k == "CLOUDFLARE_ACCOUNT_ID" and not re.fullmatch(r"[0-9a-f]{32}", val):   # v2.1.1: 30 Oct ko 31 akshar gaya tha
            return tg.say(f"❌ Account ID {len(val)} akshar ka hai, 32 hona chahiye (sirf 0-9, a-f). Cloudflare → Workers & Pages → "
                          "daayin taraf Account ID ke copy nishaan se dobara copy karein. Kuch nahi badla.")
        website.set_env(k, val)
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
    if tl in ("backup reset", "ntfy reset", "backup naya"):
        from . import backup, relay
        backup.rotate()
        if relay.cfg().get("url"):
            run(relay.deploy)
        return tg.say("🔒 Naya ntfy topic bana. App mein purana hata kar naya jodein:\n\n" + backup.setup_text())
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
        return run(lambda: tg.say(website.traffic_smart()))
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
        return run(lambda: tg.say(website.bing_report()))           # v3.2.0: poori Bing report
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
    _hn = re.fullmatch(r"(?i)\s*ho\s*gaya\s+(\d{1,2})\s*", t)
    if _hn:                                        # v2.1.6: 'ho gaya 3' - list ka number, pakka karne ka button
        from . import tasks
        it = tasks.by_number(int(_hn.group(1)))
        if not it:
            return tg.say("Ye number list mein nahi. Pehle '🧾 Mere kaam' dabayein, phir wahi number likhein.")
        k, txt = it
        if not str(k).startswith("todo_"):              # v2.9.3: bot-jaanch wala kaam - owner ki pushti se band (dobara nahi aata)
            if str(k).startswith(tasks.STRICT):
                return tg.say(f"🔑 Is kaam ke bina bot kaam hi nahi kar sakta, isliye bot khud API se pakka karta hai:\n{txt[:160]}\n"
                              "Kar diya hai to bot mein jo token/link maanga gaya tha wahi bhejein - turant hat jayega.")
            return tg.say(f"Pakka kar diya?\n{txt[:200]}", tg.inline([[("✅ Haan, maine kar diya", f"ho:{k[:40]}")], [("❌ Nahi", "hg:0")]]))
        return tg.say(f"Pakka ho gaya?\n{txt[:200]}", tg.inline([[("✅ Haan, ho gaya", f"hg:{k[5:25]}")], [("❌ Nahi", "hg:0")]]))
    if t.lower().startswith("ho gaya "):
        from . import tasks
        gone = tasks.mark_done(t[8:])
        if not gone:
            dn = tasks.already_done(t[8:])
            if dn:
                return tg.say(f"✅ Ye pehle hi ho chuka hai ({dn[0].get('done', '')}): {dn[0]['x'][:120]}")
            sg = tasks.suggest(t[8:])                 # v2.8.2: spelling galat ho to milte-julte kaam ke button (pushti ke saath)
            cp = tasks.find_computed(t[8:])           # v2.9.3: bot-jaanch wale kaam bhi (pehle 'nahi mila' / phir dikhte the)
            if cp and not sg:
                return tg.say("🤔 Ye kaam? (aapke shabd se)", tg.inline([[("✅ " + tt_[:46], f"ho:{kk_[:40]}")] for kk_, tt_ in cp]
                                                                      + [[("❌ Inme se koi nahi", "hg:0")]]))
            if sg:
                return tg.say("🤔 Kaunsa kaam ho gaya? (aapke shabd se milte-julte)",
                              tg.inline([[("✅ " + o["x"][:48], f"hg:{o['x'][:20]}")] for _, o in sg] + [[("❌ Inme se koi nahi", "hg:0")]]))
            return tg.say("Is shabd se koi khula kaam nahi mila. '🧾 Mere kaam' mein dekh kar number likhein, jaise 'ho gaya 3'.")
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
        return run(lambda: tg.say("🔐 PageSpeed key surakshit. " + _psi_test()))
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
    if t in ("🙈 Gemini Blindfold", "/blindfold") or tl in ("blindfold", "gemini blindfold", "dlp"):
        from .guard import blindfold_status
        return tg.say(blindfold_status())
    if t in ("🧹 Deep Safai", "/deepsafai") or tl in ("deep safai", "vm kachra safai"):
        from .guard import clean_uv_cache
        return run(lambda: tg.say(clean_uv_cache(execute=False)))
    if tl in ("deep safai karo", "kachra saaf karo"):
        return tg.say("⚠️ Pakka? ~/.cache/uv mitega (zaroorat par apne aap dobara banta hai). huggingface/venv KABHI nahi.",
                      tg.inline([[("✅✅ Haan, safai", "s1:ds"), ("❌ Nahi", "s1:no")]]))
    if t in ("🔐 Web Vault (8099)", "/vault") or tl in ("web vault", "vault info", "vault"):
        from . import vault_web
        return tg.say(vault_web.vault_info())
    if tl in ("vault chalu", "vault band"):
        on_ = tl.endswith("chalu")
        return tg.say(f"⚠️ Pakka? Web Vault (127.0.0.1:8099, sirf VM ke andar) {'CHALU' if on_ else 'BAND'}.",
                      tg.inline([[("✅✅ Haan, pakka", "s1:v1" if on_ else "s1:v0"), ("❌ Nahi", "s1:no")]]))
    if tl in ("spare reel", "spare reels", "spare bank", "spare reel status", "spare reel haal"):
        st = pipeline.spare_reel_status()
        return tg.say("🎞 Pehle se bani spare reel (slot bachaane ke liye): " +
                      ", ".join(f"{BRANDS[k]['name']}: {v}" for k, v in st.items()) +
                      "\nRoz raat 02:30 ke baad khud bharti hai (har channel 2). Abhi: 'spare reel banao'")
    if tl in ("spare reel banao", "spare reel refill", "spare bank bharo"):
        tg.say("🎞 Spare reel bana raha hoon (VM khaali ho to; kuch minute)...")
        return run(lambda: tg.say(pipeline.spare_reel_refill()))
    if t in ("📏 Quota haal", "/quota") or tl in ("quota", "quota haal", "seema haal"):
        from . import youtube as _Y, threads as _T, meta as _M, pinterest as _P
        q = _Y.quota_status()
        lines = [f"📏 ROZ KI SEEMA (aaj)\n▶️ YouTube: {q['uploads_today']} upload, ~{q['used_units']}/10000 unit "
                 f"({'✅' if q['can_upload'] else '⛔ kal'})"]
        for b_ in BRANDS:
            try:
                ig = _M.check_ig_publishing_limit(b_)
            except Exception:
                ig = {"quota_usage": "?", "quota_total": 50}
            th = _T.check_threads_quota(b_)
            lines.append(f"• {BRANDS[b_]['name']}: IG {ig['quota_usage']}/{ig['quota_total']} | Threads {th['used']}/{th['limit']}")
        pp = state.get("pin_pace") or {}
        lines.append(f"📌 Pinterest aaj: {pp.get('total', 0)}/15 (ek URL par max 2)")
        lines.append("🔒 Har post par taala: ek hi video kisi platform par do baar nahi (bot beech mein ruka to bhi).")
        return tg.say("\n".join(lines))
    if t in ("🎨 9 Visual Style", "/styles") or tl in ("styles", "visual style", "9 style", "visual styles"):
        from . import studio
        tg.say(studio.styles_text())
        return tg.say("Kis channel ka?", tg.inline([[(v["name"], f"s2:st:{k}")] for k, v in BRANDS.items()]))
    if t in ("🎛 HUD", "/hud") or tl in ("hud", "hud haal"):
        from . import studio
        return tg.say(studio.hud_text())
    if tl.startswith("hud "):
        from . import studio
        hp = studio.hud_parse(tl)
        if hp:
            state.put("hud_pending", [hp[0], hp[1]])
            return tg.say(f"⚠️ Pakka? {studio.HUD_PARTS[hp[0]]} {'CHALU' if hp[1] else 'BAND'} (aage ki har video).",
                          tg.inline([[("✅✅ Haan, pakka", "s2:hy"), ("❌ Nahi", "s2:no")]]))
    if t in ("🔊 Awaaz", "/awaaz") or tl in ("awaaz", "awaaz haal", "sound haal"):
        from . import sfx
        return tg.say(sfx.settings_text())
    if tl.startswith("awaaz ") and tl.split()[-1] in ("band", "chalu") and len(tl.split()) == 3 \
            and tl.split()[1] in ("sfx", "music", "phonetic", "pace", "trim"):
        k_, on_ = tl.split()[1], tl.endswith("chalu")
        state.put("awaaz_pending", [k_, on_])
        return tg.say(f"⚠️ Pakka? Awaaz ka '{k_}' {'CHALU' if on_ else 'BAND'} (aage ki har video).",
                      tg.inline([[("✅✅ Haan, pakka", "s3:ay"), ("❌ Nahi", "s3:no")]]))
    if t in ("🎚 QC", "/qc") or tl in ("qc", "video qc", "audio qc", "lufs"):
        m_ = _latest_meta()
        if not m_:
            return tg.say("Abhi koi bani hui video nahi mili (QC ke liye).")
        from . import audit as _A
        return run(lambda: tg.say(_A.qc_report(m_)))
    if t in ("🖼 Carousel", "/carousel") or tl in ("carousel", "carousel banao", "5 slide"):
        m_ = _latest_meta()
        if not m_:
            return tg.say("Abhi koi script/video nahi mili (carousel ke liye).")
        def _car():
            from . import thumbs as _th
            from .config import TMP
            sl = _th.make_carousel(m_["brand"], m_, TMP / f"car_{int(time.time())}")
            tg.photos([str(x) for x in sl], f"🖼 5-slide carousel (1080x1350): {m_.get('title', '')[:60]}\n"
                                             "Instagram/Facebook par haath se daal sakte hain (bot khud post nahi karta).")
        return run(_car)
    if t in ("🧩 11-Mode Puzzle/GK", "/puzzles") or tl in ("puzzle", "puzzles", "paheli", "puzzle banao"):
        from . import puzzles as _pz
        names = {"shuddh_hindi": "Shuddh Hindi", "color_match": "Rang milaan", "number_connect": "Sankhya trick",
                 "ball_memory": "Gend-katori", "odd_one_out": "Alag akshar", "speed_math": "Speed math",
                 "matchstick": "Machis teeli", "memory_flash": "Memory flash", "optical_count": "Tribhuj ginti",
                 "word_scramble": "Shabd paheli", "exam_quant": "Sarkari exam trick", "pahadi_gk": "Pahadi GK",
                 "pahadi_shabd": "Purane pahadi shabd"}
        names.update({"elite24": "24-Look paheli", "utpate_shabd": "Ulte-pulte shabd", "purane_shabd": "Purane shabd",
                      "pahadi_purana": "Pahad ke purane naam", "sudoku4": "Sudoku", "series": "Sankhya series", "coding": "Coding",
                      "calendar": "Calendar", "clock_angle": "Ghadi ka kon", "direction": "Disha", "age": "Umar paheli",
                      "ego_sawal": "Ego test", "dimag_trend": "Dimag hilao", "trend_gk": "Trending GK", "money_quiz": "Paise ka sawal",
                      "deals_quiz": "Deal ka ganit"})     # v2.3.7: naye mode (pehle KeyError - button tootta tha)
        rows = [[(f"{i}. {names.get(k, k)}", f"s4:pz:{k}") for i, k in list(enumerate(_pz.PUZZLE_TYPES, 1))[j:j + 2]]
                for j in range(0, len(_pz.PUZZLE_TYPES), 2)]
        rows.append([("🖼 Carousel (aakhri video)", "s4:car"), ("📲 Challenge card", "s4:card")])
        return tg.say(f"🧩 {len(_pz.PUZZLE_TYPES)} PUZZLE / GK MODE — har jawab do tareeke se jaancha, koi sawal dohraaya nahi.\n"
                      "Button dabao → channel chuno → video manzoori line mein aayegi (aapke button ke bina post nahi).\n"
                      f"Din-plan ke 'challenge' din bot khud puzzle daalta hai: {'CHALU' if state.get('puzzles_on', True) else 'BAND'} "
                      "('puzzle din band' / 'puzzle din chalu').", tg.inline(rows))
    if tl in ("puzzle din band", "puzzle din chalu"):
        state.put("s4_pending", tl.endswith("chalu"))
        return tg.say(f"⚠️ Pakka? Challenge din par apne aap puzzle reel: {'CHALU' if tl.endswith('chalu') else 'BAND'}.",
                      tg.inline([[("✅✅ Haan, pakka", "s4:on"), ("❌ Nahi", "s4:no")]]))
    if tl.startswith(("code ", "reel code ")) and tl.split()[-1].lstrip("#").isdigit():
        from . import puzzles as _pz
        return tg.say(_pz.lookup_code(tl.split()[-1]))
    if tl.startswith(("sawal galti ", "report sawal ")):
        from . import puzzles as _pz
        return tg.say(_pz.report_question_error(t.split(None, 2)[-1]))
    if t in ("📲 WhatsApp Card", "/card") or tl.startswith("challenge card"):
        return on_callback({"id": "0", "data": "s4:card"})
    if t in ("🎯 Exam sawal", "/exam") or tl in ("exam sawal", "dual solver", "exam check"):
        from . import puzzles as _pz
        ex = _pz.generate_exam_question("Banking")
        return tg.say(f"🎯 {ex['topic']} (do tareeke se jaancha ✅)\n{ex['question_stem']}\nVikalp: " + " | ".join(ex["options"]) +
                      f"\n✅ {ex['correct_answer']}\n💡 {ex['shortcut_trick']}\n📘 {ex['step_by_step_explanation']}\n⚠ {ex['most_picked_wrong_option']}")
    if t in ("💰 Revenue Roadmap", "/revenue") or tl in ("revenue", "kamai", "kamai yojana", "revenue roadmap"):
        from . import company as _CP
        return run(lambda: tg.say(_CP.revenue_report() + "\n\n" + _CP.digest()))
    if tl in ("10 vibhag", "10 vibhag audit", "audit 10", "/audit10"):
        from . import company as _CP
        return run(lambda: tg.say(_CP.audit_10()))
    if tl in ("comment mining", "sawaal mining", "audience topics"):
        from . import growth as _GR
        return run(lambda: tg.say(_GR.mine_comment_topics()))
    if tl in ("vip fans", "superfans", "super fan", "top audience"):
        from . import growth as _GR
        return tg.say(_GR.vip_superfans())
    if tl in ("dpdp ledger", "consent ledger", "dpdp check", "/dpdp"):
        from . import privacy as _PV
        return tg.say(_PV.consent_ledger_summary())
    if tl in ("fatigue check", "reach drop", "retention drop"):
        from . import learn as _LN
        f_, r_ = _LN.check_fatigue_and_reach_drop(), _LN.analyze_retention_drop()
        return tg.say(f"📉 RETENTION + THAKAAN:\n• {f_['note']}\n• Ausat retention: {r_['avg_retention'] if r_['avg_retention'] is not None else '-'}%\n"
                      f"• Agli script ki salaah: {r_['auto_edit_advice']}")
    if t in ("🎯 Scroll jaanch", "/scroll") or tl in ("scroll jaanch", "scroll away", "kitne log scroll"):
        from . import analytics as _AN
        return run(lambda: tg.say(_AN.scroll_and_retention_forensics()))
    if tl in ("story jaanch", "story api", "story kyu nahi"):
        from . import growth as _GR
        return run(lambda: tg.say(_GR.story_api_diagnostic()))
    if tl in ("keyword cluster", "scaled content", "scaled content check"):
        from . import marketing as _MK
        return tg.say(_MK.cluster_scaled_queries())
    if tl in ("scheme rates", "sarkari number", "section 123", "dhara 123"):
        from . import siteknow as _SK
        return tg.say(_SK.check_scheme_constants())
    if tl in ("scheme rates jaancho", "sarkari number jaancho"):
        from . import siteknow as _SK
        return run(lambda: (_SK.verify_scheme_rates(), tg.say(_SK.check_scheme_constants())))
    if tl in ("calculator test", "calc test", "calculator smoke"):
        from . import website as _WB
        return run(lambda: tg.say(_WB.verify_calculators_smoke()))
    if tl in ("panchang", "aaj ki tithi", "tithi"):
        from . import calendar_in as _CI
        p_ = _CI.tithi()
        return tg.say(f"🗓 {p_.get('vaar', '')} | {p_.get('maas', '')} {p_.get('paksha', '')} {p_.get('tithi', '')} | Vikram Samvat {p_.get('samvat', '')}"
                      f" ({'Google se' if p_.get('source') != 'offline ganit' else 'offline ganit'})\nVideo badge: {_CI.badge_line()}")
    if tl.startswith("single file "):
        from . import files as _FL
        q_ = t.split(None, 2)[2] if len(t.split(None, 2)) > 2 else ""
        return run(lambda: tg.say(_FL.send_single_file(q_)))
    if t in ("📸 Photo Gallery", "/gallery") or ("photo" in tl and any(w in tl for w in ("wapas", "dena", "delete", "hatao", "mat banana",
                                                                                      "gallery", "galary", "phir banao"))):
        from . import files as _FL
        if any(w in tl for w in ("mat banana", "reel mat", "reels mat", "use mat")):
            state.put("s5_pending", "gal_off")
            return tg.say("⚠️ Pakka? Gallery ki photo se reel banana BAND (photo VM par rahegi).",
                          tg.inline([[("✅✅ Haan, pakka", "s5:y"), ("❌ Nahi", "s5:no")]]))
        if "phir banao" in tl:
            state.put("s5_pending", "gal_on")
            return tg.say("⚠️ Pakka? Gallery ki photo se reel phir CHALU.", tg.inline([[("✅✅ Haan, pakka", "s5:y"), ("❌ Nahi", "s5:no")]]))
        if any(w in tl for w in ("delete", "hatao", "mita")):
            state.put("s5_pending", "gal_del")
            return tg.say("⚠️ Pakka? Gallery ki aakhri 3 photo VM se HAMESHA ke liye mitengi.",
                          tg.inline([[("✅✅ Haan, mitao", "s5:y"), ("❌ Nahi", "s5:no")]]))
        if any(w in tl for w in ("wapas", "dena", "do ")):
            return run(lambda: tg.say(_FL.send_recent_photos(3)))
        n_ = len(_FL.gallery_photos(None, 500))
        return tg.say(f"📸 PHOTO GALLERY: {n_} photo | reel mein: {'BAND' if state.get('no_gallery_reels') else 'CHALU'}\n"
                      "Likhein: 'last 3 photos wapas do' / 'photos delete kar do gallery se' / 'in photos se reels mat banana' / "
                      "'photos se reel phir banao'")
    if t in ("🌐 Website draft", "/webpage") or tl in ("website draft", "website widget zip", "website page", "naya page draft"):
        from . import web_widgets as _WW
        names = {"brain-challenge-daily-quiz": "Daily quiz + reel code", "sarkari-exam-eligibility-calculator": "Exam yogyata/umar",
                 "exam-normalization-percentile-calculator": "Normalization anumaan", "desi-calendar-tithi-converter": "Desi calendar/tithi",
                 "shuddh-hindi-dictionary-quiz": "Shuddh Hindi shabdkosh"}
        return tg.say("🌐 WEBSITE: ek baar mein sirf EK page (aapka niyam).\nBot sirf DRAFT banata hai → aap Claude ko bhejein → Claude sudhaar "
                      "kar website ZIP dega → wahi ZIP yahan (audit → GitHub → live). Bot khud website par kuch nahi daalta.\nKaun sa page?",
                      tg.inline([[(names.get(sl, sl), f"s6:{sl}")] for sl in _WW.page_slugs()]))
    if tl in ("calcspecs", "/calcspecs", "calculator specs"):
        from . import web_widgets as _WW
        return tg.say(_WW.calculator_specs())
    if t in ("👑 Pro 50 Deck", "/pro50", "/deck") or tl in ("pro deck", "50 button", "50 deck", "pro 50"):
        return send_pro_deck_home()
    if t in ("🏆 6x Audit (asli)", "/audit6x") or tl in ("6x audit", "6 pass audit", "1000 audit", "elite audit"):
        from . import elite_audit as _EA
        tg.say("🏆 6-pass asli audit chal raha hai (1-3 min)...")
        return run(lambda: tg.say(_EA.run_6pass_audit()))
    if t in ("🛡 6-Stage Audit",) or tl in ("6 stage audit", "deep 6 stage"):
        from . import audit as _AU
        return run(lambda: tg.say(_AU.deep_6stage_audit()))
    if t in ("🚨 Exam Alerts", "/examalerts") or tl in ("exam alerts", "sarkari exam", "exam khabar"):
        from . import news as _NW
        return run(lambda: tg.say("🚨 TAAZA SARKARI EXAM KHABAR (sirf headline + srot):\n" +
                                  ("\n".join(f"• {a['title']} ({a['src']})" for a in _NW.exam_alerts()[:6]) or "Abhi koi nayi headline nahi.")))
    if t == "🔢 Reel Code Khoj":
        return tg.say("🔢 Kisi bhi reel ka jawab: likhein 'code 786' (4 ank ka code reel par likha hota hai; purani reels ka 3 ank).")
    if t == "🚩 Doubt/Error Shield":
        reps = state.get("question_reports") or {}
        retired = sum(1 for v in reps.values() if v.get("status") == "quarantined_retired")
        return tg.say(f"🚩 SAWAL-GALTI SHIELD:\n• Kul shikayat: {len(reps)} | hamesha ke liye hataye: {retired}\n"
                      "• Niyam: 3 shikayat par sawal apne aap hat jaata hai (dobara kabhi nahi)\n"
                      "• Shikayat darj: 'sawal galti <code ya sawal>' | Website par 'सुधार बताएँ' button email kholta hai")
    if t in ("🗓 Panchang Badge", "/panchang"):
        from . import calendar_in as _CI
        return tg.say(f"🗓 Video ke kone ka badge: {_CI.badge_line()}\nHaal: {'CHALU' if (state.get('hud') or {}).get('panchang', True) else 'BAND'}"
                      " | Badlo: 'hud panchang band' / 'hud panchang chalu' (dohri pushti)")
    if tl in ("bing bhejo", "bing submit", "bing url bhejo"):
        from . import website as _WB
        return run(lambda: tg.say(_WB.bing_submit_daily(force=True)))
    from . import media_tools as _MT
    if _MT.YT_RX.search(t) and re.search(r"(version|apna|banao|bana do|clone|jaisa|isi tarah)", tl):
        ca = _MT.competitor_angle(t)                # v2.4.0: competitor ka VISHAY -> apni original sawal-reel (copy nahi)
        if not ca:
            return tg.say("Is link ki jaankari nahi mili (private/hata hua?).")
        bk, topic, ttl = ca
        tg.say(f"🕵️ Vishay mila: '{ttl[:90]}' → {BRANDS[bk]['name']} par APNA original sawal-reel (unka video/shabd copy nahi). "
               "Manzoori line mein aayegi.")
        from .writer import QUIZ_STYLE
        return run(pipeline.prepare, bk, None, "aapne maanga (competitor vishay)", topic, "short", QUIZ_STYLE)
    if tl in ("square video", "wide video", "1:1 video", "16:9 video", "reframe", "sab size", "har size"):
        tg.say("🎞 Aakhri video ke 1:1 aur 16:9 ban rahe hain (1-3 min)...")
        return run(_MT.reframe_latest)
    from . import ops as _OPS
    if t in ("🔑 Token haal", "/tokens") or tl in ("token haal", "token", "login haal", "expiry"):
        return run(lambda: tg.say(_OPS.token_text()))
    if tl in ("api jaanch", "api check", "contract test"):
        return run(lambda: tg.say("🧪 API JAANCH:\n" + "\n".join(f"{'✅' if ok else '❌'} {n} {e}" for n, ok, e in _OPS.contract_tests())))
    if t in ("💾 Backup", "/backup") or tl in ("backup", "backup haal", "offsite backup"):
        return tg.say(_OPS.backup_text())
    if tl in ("backup abhi", "backup banao"):
        return run(lambda: tg.say("💾 " + ("ban gaya + aapke Telegram par" if _OPS.make_backup() else "nahi bana")))
    if tl in ("restore drill", "backup jaanch"):
        return run(lambda: tg.say(_OPS.restore_drill()))
    if tl == "backup password":
        pw = _OPS.show_password() or (_OPS._password() and _OPS.show_password())
        r_ = tg.say(f"🔐 Backup password: {pw}\n(Ise kahin likh lein - iske bina backup nahi khulega. Ye message 1 min mein khud mitega.)")
        try:
            mid = (r_ or {}).get("message_id") or ((r_ or {}).get("result") or {}).get("message_id")
            if mid:
                threading.Timer(60, lambda: tg.call("deleteMessage", {"chat_id": tg._chat(), "message_id": mid})).start()
        except Exception:
            pass
        return r_
    if tl in ("backup password reset", "backup password naya", "naya backup password"):       # v2.7.1
        return tg.say("⚠️ Naya backup password banega (padhne-layak, 4 shabd + 4 ank) aur usi se turant naya backup.\n"
                      "Purane backup purane password se hi khulenge. Pakka?",
                      tg.inline([[("✅✅ Haan, naya banao", "s41b:y"), ("❌ Nahi", "s41b:n")]]))
    if tl in ("maine save kar liya", "save kar liya", "maine save kiya", "save ho gaya", "password save ho gaya") \
            and state.get("bk_pass_saved") is False:          # v2.9.6: 10 Nov 16:08/16:13 owner ne likha, bot nahi samjha
        state.put("bk_pass_saved", True)
        return tg.say("✅ Backup password save maana - ab roz yaad nahi dilaunga. (Bhool jaayein to 'backup password')")
    if any(w in tl for w in ("like kon", "like kaun", "kon like", "kaun like", "likes kaun", "like kar rha", "like kar raha")):
        return tg.say("👍 Like karne walon ke NAAM YouTube/Instagram/Facebook API se kisi ko nahi milte (unki privacy niti), aur hum "
                      "naam rakhte bhi nahi (hamari privacy policy). Har video ke like/comment ki GINTI aur kaunsa video zyada chala - "
                      "'📊 Aaj ka haal' aur 'kya chal raha' mein. Comment karne walon ko bot jawab deta hai ('💬 Comment haal').")
    if tl in ("backup password save", "password save kar liya", "ho gaya backup password"):
        state.put("bk_pass_saved", True)
        return tg.say("✅ Theek. Ab roz yaad nahi dilaunga. Kabhi bhool jaayein to 'backup password' likhein (VM par surakshit hai).")
    if tl.startswith("backup password badlo "):
        newp = t.split(None, 3)[3] if len(t.split(None, 3)) > 3 else ""
        state.put("bkpass_pending", newp)
        return tg.say("⚠️ Pakka? Backup password badlega (purane backup purane password se hi khulenge).",
                      tg.inline([[("✅✅ Haan, badlo", "s40:y"), ("❌ Nahi", "s40:n")]]))
    if t in ("📜 Provenance", "/provenance") or tl in ("provenance", "srot", "copyright saboot"):
        try:
            from .config import DATA as _D
            last = (_D / "provenance.jsonl").read_text(encoding="utf-8").splitlines()[-3:]
        except Exception:
            last = []
        return tg.say("📜 SROT-REGISTER (aakhri 3 video - font/awaaz/chitra/sawal ka srot + license):\n" +
                      ("\n".join(x[:400] for x in last) or "abhi khaali"))
    if tl in ("jawab haal", "answer key", "jawab website", "jawab page"):
        lst = state.get("answer_key") or []
        return tg.say(f"✅ JAWAB SYSTEM: video mein jawab {'NAHI (website/Telegram par)' if state.get('answer_offsite', True) else 'HAAN'} | "
                      f"website /jawab: {'CHALU' if state.get('jawab_site_on') else 'BAND'} | ab tak {len(lst)} jawab\n"
                      + "\n".join(f"#{e['code']} {e['bname']}: {e['ans']}" for e in lst[-5:])
                      + "\nBadalna: 'jawab website chalu/band' | 'jawab video mein' / 'jawab website par' (dohri pushti)")
    if tl in ("owner mode", "ownermode", "owner mod", "meri visit", "meri visit mat gino", "apni visit"):   # v3.1.2
        from . import ownermode as _OM
        return tg.say(_OM.status())
    if tl in ("final jaanch", "final authority", "final check", "final janch", "aakhri jaanch"):   # v3.1.0: pakka darwaza - aakhri video ka haal
        from . import finalgate as _FG
        return tg.say(_FG.report())
    if re.match(r"^(awaaz|awaz|voice)\s+(raftaar|raftar|speed)\b", tl):         # v3.1.0: awaaz ki raftaar (dohri pushti)
        from . import finalgate as _FG
        v_ = _FG.parse_speed(tl)
        if v_ is None:
            return tg.say(f"🔊 Awaaz ki raftaar abhi: {_FG.voice_speed():.2f} (1.00 = saadharan).\n"
                          f"Badalna: 'awaaz raftaar 1.1' ({_FG.SPEED_MIN} se {_FG.SPEED_MAX} ke beech; 1.1 = 10% tez). "
                          "Agli video se laagu; purani video nahi badlengi. 'final jaanch' mein asli shabd/second dikhta hai.")
        return tg.say(f"⚠️ Pakka? Awaaz ki raftaar {_FG.voice_speed():.2f} ➜ {v_:.2f} (sab channel, agli video se).",
                      tg.inline([[("✅✅ Haan", f"s47:{v_:.2f}"), ("❌ Nahi", "s47:x")]]))
    if tl in ("jawab digest chalu", "jawab digest band"):                    # v2.5.2: roz ek digest (dohri pushti)
        v_ = "on" if tl.endswith("chalu") else "off"
        return tg.say("⚠️ Pakka? " + ("Telegram par har video ke saath alag jawab-post band; roz shaam 20:30 par ek digest (sab jawab ek message mein)."
                                      if v_ == "on" else "Wapas har video ke saath alag jawab-post."),
                      tg.inline([[("✅✅ Haan", f"s44:{v_}"), ("❌ Nahi", "s44:x")]]))
    if tl in ("yt comment login", "youtube comment login", "comment login", "yt comment"):   # v2.5.7: YouTube par comment likhne ka alag login
        from . import ytcomment as _YC, analytics as _AN
        if not _AN.CLIENT.exists():
            return tg.say("❌ Pehle '/analytics' wala Desktop client (yt_analytics_client.json) jodna padega - /analytics likhkar steps dekhein. Wahi client yahan bhi chalta hai.")
        miss = _YC.missing()
        if not miss:
            return tg.say("✅ Sab channel ka comment-login ho chuka hai.")
        tg.say("🔑 YouTube COMMENT login (upload wala login nahi badlega). Har channel ke liye:\n1) Neeche link phone/Chrome mein kholein\n"
               "2) Us channel ka account chunein (brand wala naam, email nahi)\n3) 'Allow' (saari ijaazat tick)\n"
               "4) Browser ka address (localhost... code=...) POORA yahan bhej dein - bot turant mita dega.\n(Code 10 min chalta hai.)")
        for b_ in miss:
            tg.say(f"▶️ {BRANDS[b_]['name']}:\n{_YC.link(b_)}")
        return
    if tl in ("privacy ig theek", "privacy theek karo", "privacy patch"):               # v2.5.7: policy = practice (ek tap pushti)
        from . import privacy_patch as _PP
        txt_, ok_ = _PP.proposal()
        return tg.say(txt_, tg.inline([[("✅✅ Haan, badlo", "s45:ok"), ("❌ Nahi", "s45:x")]]) if ok_ else None)
    if tl in ("jawab poll chalu", "jawab poll band"):
        v_ = "on" if tl.endswith("chalu") else "off"
        return tg.say("⚠️ Pakka? " + ("Roz max 2 jawab Telegram par native quiz poll ki tarah (baaki text post)." if v_ == "on" else "Poll band, sab jawab text post."),
                      tg.inline([[("✅✅ Haan", f"s46:{v_}"), ("❌ Nahi", "s46:x")]]))
    if tl in ("features", "feature haal", "kya chalu hai"):
        from . import watchdog as _WD
        return tg.say(_WD.features_text())
    if "comment" in tl and any(w in tl for w in ("jud", "login haal", "login ho", "login per", "login par")) \
            and not tl.startswith("yt comment login"):  # v2.9.8: 'comment login per saare page jud gaye kya' ka seedha jawab
        from . import ytcomment as _YC
        st_ = state.get("cstats") or {}
        rows_ = []
        for b_, v_ in BRANDS.items():
            rows_.append(f"• {v_['name']}: YouTube comment-login {'✅ juda' if _YC.has(b_) else '❌ nahi - likhein: yt comment login ' + b_}")
        err_ = str((st_.get("last_err") or st_.get("err") or ""))[:160]
        return tg.say("💬 COMMENT-LOGIN HAAL\n" + "\n".join(rows_) + "\n• Facebook/Instagram: Meta token se (alag login nahi)"
                      + (f"\n• Aakhri galti: {err_}" if err_ else "") + "\nPoori ginti: '💬 Comment haal'")
    if tl in ("traffic trend", "aaj traffic", "traffic badh raha", "traffic ghat raha", "website trend"):    # v2.9.9
        from . import website as _WT
        return run(lambda: tg.say(_WT.traffic_trend()))
    if tl in ("quiz bot haal", "quizbot haal", "quiz bot", "quiz haal"):                               # v2.9.5
        from . import quizbot as _QB
        _QB.ensure()
        return tg.say(_QB.status_text())
    if tl.startswith("yt comment login ") and tl.split()[-1] in BRANDS:                                  # v2.9.5: ek channel zabardasti
        from . import ytcomment as _YC
        br_ = tl.split()[-1]
        try:
            _YC.tpath(br_).unlink(missing_ok=True)
        except Exception:
            pass
        return tg.say(f"🔑 {BRANDS[br_]['name']} ka comment-login (naya):\n{_YC.link(br_)}\nUs channel ka Google/Brand account chunein → "
                      "Allow → 'localhost' wala poora address yahan bhejein.")
    if tl in ("welcome pin", "welcome post", "welcome pin karo", "channel welcome"):                   # v2.9.2
        return tg.say("📌 Telegram channel @sabhisaab mein welcome post (saare official channel ke link) daal kar PIN kar doon?\n"
                      "(Galti se pin hua 'ho gaya welcome pin' wala message aap channel mein khud delete kar dein.)",
                      tg.inline([[("✅✅ Haan, daalo + pin", "wp:y"), ("❌ Nahi", "wp:n")]]))
    if tl in ("web story jaanch", "amp jaanch", "webstory jaanch", "amp check"):                          # v3.0.2: 'story jaanch' purana (FB/IG story)
        from . import webstory as _WS
        sl_ = sorted((state.get("stories") or {}).items(), key=lambda x: x[1])
        if not sl_:
            return tg.say("Abhi koi Web Story nahi bani.")
        return run(lambda: tg.say(_WS.live_check(f"https://sabhisaab.com/stories/{sl_[-1][0]}")[1]))
    if tl.startswith(("story banao", "web story")):                                                   # v2.9.1
        from . import webstory as _WS
        br_ = next((b for b in BRANDS if b in tl or BRANDS[b]["name"].lower() in tl), "money")
        tg.say(f"📖 {BRANDS[br_]['name']} ki Web Story bana raha hoon (is hafte ke jaanche sawal se)...")
        return run(lambda: tg.say(_WS.publish(br_)))
    if tl in ("vote chalu", "% engine chalu", "percent chalu", "vote counter chalu"):                 # v2.8.0
        from . import votes as _VT
        tg.say("🗳 Asli % engine (vote counter) bana raha hoon - Cloudflare par (1-2 min)...")
        return run(lambda: tg.say(_VT.setup()))
    if tl in ("vote band", "% engine band"):
        state.put("votes_on", False)
        state.put("answer_dirty", True)
        return tg.say("✅ /jawab par vote/% band (tap karke sochna chalta rahega, bas ginti nahi).")
    if tl in ("kya chal raha", "look haal", "jeet", "winners", "kaunsa look chal raha"):            # v2.7.5
        from . import learn as _LN
        return tg.say(_LN.winners_text())
    if tl in ("sawal schedule", "sawal plan", "hafte ka schedule", "week schedule", "schedule dikhao", "sawal ka schedule"):   # v2.7.3
        from . import qplan as _QP
        return tg.say(_QP.week_text())
    if tl in ("sawal plan reset", "sawal plan wapas"):                                       # v2.8.1
        state.put("qplan_swaps", {})
        return tg.say("✅ Views wale badlaav hataye - default hafte-war plan wapas.")
    if tl in ("sawal plan band", "sawal plan chalu"):
        state.put("qplan_on", tl.endswith("chalu"))
        return tg.say("✅ Hafte-war sawal schedule " + ("chalu (default)" if tl.endswith("chalu") else "band - purana tareeka (channel ke mizaaj se)"))
    if tl in ("bank safai", "sawal safai", "purane sawal hatao"):
        from . import qplan as _QP
        return run(lambda: tg.say(f"🧹 Kaam ke nahi wale purane sawal/script hataye: {_QP.cleanup()}"))
    if tl in ("hook haal", "hook", "puchhne ka tareeka", "sawal ka tareeka"):                   # v2.7.1
        from . import hooks as _HK
        return tg.say(_HK.status_text())
    if tl.startswith("hook "):
        from . import hooks as _HK
        raw_ = tl.split(None, 1)[1].strip()
        m_ = _HK.match(raw_)                       # v2.7.2: spelling galat ho to bhi ('bahes' -> 'bahas')
        if m_:
            state.put("hook_mode", m_)
            state.put("hook_mode_brand", {})       # sab channel par ek jaisa (channel-wise: '⚙️ Channel setup')
            note = "" if m_ == raw_ else f" (aapne '{raw_}' likha - maine '{m_}' samjha)"
            return tg.say(f"✅ Sawal puchhne ka tareeka: {'har reel par baari-baari' if m_ == 'rotate' else m_}{note}. Agli reel se.")
        return tg.say("❌ Ye andaaz samajh nahi aaya. 'hook haal' likh kar list dekhein.")
    if t in ("⚙️ Channel setup", "/setup") or tl in ("channel setup", "setup", "setting", "settings", "channel setting"):
        from . import setupwiz as _SW
        return tg.say("⚙️ Kis channel ki setting dekhni/pakki karni hai? (✅ = FINAL ho chuka)", _SW.brand_menu())
    if tl in ("dar jaancho", "sarkari dar", "sarkari dar jaancho", "rates", "dar haal"):          # v2.6.1
        from . import factwatch as _F
        if tl in ("sarkari dar", "dar haal", "rates"):
            return tg.say(_F.report())
        tg.say("🧮 Sarkari dar Google + sarkari page se jaanch raha hoon (2-3 min)...")
        return run(lambda: tg.say(_F.run(force=True) + "\n\n" + _F.report()))
    if tl in ("policy jaancho", "policy haal", "api haal", "policy"):                         # v2.6.1
        from . import policywatch as _P
        if tl == "policy jaancho":
            tg.say("📜 18 policy/API page padh raha hoon (3-5 min)...")
            return run(lambda: tg.say(_P.run(force=True) + "\n\n" + _P.report()))
        return tg.say(_P.report())
    if tl in ("keyword sudhaar", "kw sudhaar", "keyword faq"):                                 # v2.6.1
        from . import kwfix as _K
        return run(lambda: tg.say(_K.run(force=True)))
    if tl in ("link theek", "link sudhaar", "galat link theek karo"):         # v2.6.0: galat related-link khud theek
        from . import sitescan as _SS
        tg.say("🔗 Galat link dhoondh kar theek kar raha hoon (audit pass hone par hi live)...")
        return run(lambda: tg.say(_SS.autofix()))
    if tl.startswith(("queue", "uk queue", "page queue", "uttarakhand queue")):     # v3.3.0: page queue
        from . import pagequeue as _PQ
        if _PQ.on_text(tl):
            return
    if tl in ("site scan", "site jaanch scan", "patle page"):                 # v2.5.3: sirf padhta hai
        from . import sitescan as _SS
        tg.say("🔎 Scan shuru (bada site hai - kuch minute lagenge, kuch badla nahi jayega)...")
        return run(lambda: tg.say(_SS.run()))
    if tl in ("ypp haal", "ypp", "monetization haal"):
        from . import ypp as _YP
        return run(lambda: tg.say(_YP.report()))
    if tl in ("adsense haal", "adsense jaanch", "adsense taiyari"):          # v2.5.2: sirf padhta hai
        from . import adsense as _AD
        return run(lambda: tg.say(_AD.status()))
    if tl.startswith("adsense id "):                                          # v2.5.2: approval ke baad ads.txt (dohri pushti)
        from . import adsense as _AD
        pub = t.split(None, 2)[2].strip().lower()
        try:
            _AD.ads_txt(pub)
        except ValueError as e_:
            return tg.say(f"❌ {e_}")
        state.put("adsense_pending", pub)
        return tg.say(f"⚠️ Website par lagega (AdSense se site jodne ke liye - koi ad nahi dikhega):\n1) ads.txt: google.com, {pub}, DIRECT, f08c47fec0942fa0\n"
                      f"2) homepage <head>: <meta name=\"google-adsense-account\" content=\"ca-{pub}\">\nPhir AdSense mein 'Meta tag' chunkar Verify.",
                      tg.inline([[("✅✅ Haan, pakka", "s43:ok"), ("❌ Nahi", "s43:x")]]))
    if tl in ("canary", "site jaanch", "live jaanch"):                        # v2.5.2: deploy ke baad wali jaanch haath se
        from . import canary as _CN
        return run(lambda: tg.say(_CN.run()[1]))
    if tl in ("jawab website chalu", "jawab website band"):
        return on_callback({"id": "0", "data": "s41:on" if tl.endswith("chalu") else "s41:off"})
    if tl in ("jawab video mein", "jawab website par"):
        v_ = "voff" if tl.endswith("mein") else "von"
        return tg.say("⚠️ Pakka? " + ("Jawab wapas VIDEO mein dikhega." if v_ == "voff" else "Jawab video se hatega (website/Telegram)."),
                      tg.inline([[("✅✅ Haan", f"s41:{v_}"), ("❌ Nahi", "s41:x")]]))
    if tl in ("layout list", "naya layout"):
        from . import studio, design as _DS
        if tl == "naya layout":
            tg.say("🧩 Naya layout namoona ban raha hai (3-8 min)...")
            return run(studio.propose_layout)
        return tg.say("🧩 LAYOUT: " + ", ".join(f"{k} ({v})" for k, v in _DS.LAYOUTS.items()) +
                      f"\nChalu: list + {', '.join(state.get('layouts_ok') or []) or '-'}\nHatana: 'layout hatao <naam>'")
    if tl.startswith("layout hatao "):
        nm = tl.split(None, 2)[2].strip()
        state.update("layouts_ok", lambda L: [x for x in (L or []) if x != nm], [])
        return tg.say(f"✅ Layout '{nm}' hata (roz ki list se).")
    m_rt = re.match(r"^(?:roz|har din|daily)\s+((?:[01]?\d|2[0-3]):[0-5]\d)\s+(?:baje\s+)?(.{3,80})$", tl)
    if m_rt:                                      # v2.3.7: koi bhi hukum roz apne aap (dohri pushti)
        hm = m_rt.group(1).zfill(5)
        cmd = t.split(None, 2)[2] if len(t.split(None, 2)) > 2 else m_rt.group(2)
        cmd = re.sub(r"^(baje\s+)", "", cmd, flags=re.I).strip()
        state.put("routine_pending", [hm, cmd])
        return tg.say(f"⚠️ Pakka? Roz {hm} par bot khud ye hukum chalayega: '{cmd}'\n(Fayda: aapko likhna nahi padega. Dhyan: hukum galat ho "
                      "to roz galat chalega - 'routine list' se dekh/hata sakte hain.)",
                      tg.inline([[("✅✅ Haan, roz karo", "s38:y"), ("❌ Nahi", "s38:n")]]))
    if tl in ("routine list", "routine", "roz ke kaam"):
        rl = state.get("routines") or []
        return tg.say("🔁 ROZ APNE AAP CHALNE WALE HUKUM:\n" + ("\n".join(f"{i + 1}. {r['t']} → {r['cmd']}" for i, r in enumerate(rl))
                      or "abhi koi nahi") + "\nJodna: 'roz 08:00 kachra saaf' | Hatana: 'routine hatao 1'")
    m_rh = re.match(r"^routine hatao (\d+)$", tl)
    if m_rh:
        rl = state.get("routines") or []
        i = int(m_rh.group(1)) - 1
        if 0 <= i < len(rl):
            gone = rl.pop(i)
            state.put("routines", rl)
            return tg.say(f"✅ Hataya: {gone['t']} → {gone['cmd']}")
        return tg.say("Ye number list mein nahi.")
    if re.search(r"(kachra|kachara|safai|saaf karo|saaf kar|clean ?up|junk)", tl) and not tl.startswith(("ho gaya", "/kachra")):
        def _safai():                             # v2.3.7: asli safai (pehle AI 'saaf kar diya' bol deta tha bina kuch kiye)
            from . import guard, blender3d
            r_ = guard.clean_uv_cache(execute=False)
            try:
                blender3d.cleanup(7)
            except Exception:
                pass
            tg.say("🧹 SAFAI ASLI MEIN HUI:\n" + str(r_)[:1500])
        tg.say("🧹 Safai chal rahi hai (purani video/thumbnail/tmp, atke ffmpeg, purane 3D)...")
        return run(_safai)
    if re.search(r"\b(total|kul|jod|jodkar|sab mila)\b", tl) and re.search(r"(impression|click|view|reach)", tl):
        from . import analytics as _AN
        tg.say("📈 Sab platform se gin raha hoon (1-2 min)...")
        return run(lambda: tg.say(_AN.totals_text()))
    if "pinterest" in tl and re.search(r"(kitne|dekha|view|impression|analytics|haal|click)", tl):
        from . import pinterest as _PI
        return run(lambda: tg.say(_PI.analytics_summary(30)))
    m_all = re.match(r"^sab channel ek samay\s+((?:[01]\d|2[0-3]):[0-5]\d(?:\s*,\s*(?:[01]\d|2[0-3]):[0-5]\d)?)$", tl)
    if m_all:                                     # v2.5.0: saare channel ek hi samay (alag sawal) - dohri pushti
        tm = re.sub(r"\s+", "", m_all.group(1))
        state.put("sched_all_pending", tm)
        return tg.say(f"⚠️ Pakka? Charon channel roz {tm} par (har channel ka sawal alag).\nFayda: ek samay par 4 naye sawal - log "
                      "doosre channel bhi dekhne aate hain. Nuksaan: din ke baaki peak samay khaali; ek saath 4 video ka load "
                      "(bot 3 ghante pehle bana leta hai, isliye chalega).", tg.inline([[("✅✅ Haan, lagao", "s42:y"), ("❌ Nahi", "s42:n")]]))
    m_sc = re.match(r"^schedule\s+(money|deals|pahadi|sunonatak|suno)\s+((?:[01]\d|2[0-3]):[0-5]\d(?:\s*,\s*(?:[01]\d|2[0-3]):[0-5]\d)?)$", tl)
    if m_sc:                                      # v2.3.6: samay badalna (dohri pushti)
        bk = "sunonatak" if m_sc.group(1) == "suno" else m_sc.group(1)
        tm = re.sub(r"\s+", "", m_sc.group(2))
        state.put("sched_pending", [bk, tm])
        return tg.say(f"⚠️ Pakka? {BRANDS[bk]['name']} ka roz ka samay: {tm} (aakhri samay = paheli/3D reel).",
                      tg.inline([[("✅✅ Haan, lagao", "s37:y"), ("❌ Nahi", "s37:n")]]))
    if (re.search(r"\b(kab|schedule|shedule|timing|samay)\b", tl) and re.search(r"(reel|video|sawal|swal|question|post|math|gk|paheli)", tl)) \
            or t in ("🗓 Schedule", "/schedule"):
        return tg.say(schedule_text())                # v2.3.6: AI andaaza nahi - asli schedule
    if t in ("🧊 Apna 3D", "/3d") or tl in ("3d haal", "3d", "apna 3d", "3d status"):
        from . import blender3d as _B3
        return tg.say(_B3.status_text())
    if tl in ("rang list", "design list", "rang haal", "/rang"):
        from . import studio
        return tg.say(studio.palettes_text())
    if tl in ("naya rang", "naya design", "naya rang dikhao"):
        from . import studio
        tg.say("🎨 Naya rang namoona ban raha hai (3-8 min)...")
        return run(studio.propose_palette)
    if tl.startswith("rang hatao "):
        nm = tl.split(None, 2)[2].strip()
        return tg.say(f"⚠️ Pakka? Rang '{nm}' default list se hatega.", tg.inline([[("✅✅ Haan", f"s36:rh:{nm}"), ("❌ Nahi", "s36:x")]]))
    if t == "📈 Kul hisaab":
        return on_text("total impression aur click")
    if t == "📌 Pinterest haal":
        return on_text("pinterest haal")
    if t == "🧹 Kachra saaf":
        return on_text("kachra saaf")
    if t in ("🏦 Sawal bank", "/qbank") or tl in ("sawal bank", "question bank", "sawal bank haal"):
        from . import qbank as _QB
        return tg.say(_QB.status_text())
    if tl in ("sawal bank bharo", "naye sawal banao"):
        from . import qbank as _QB
        tg.say("🏦 Naye sawal ban rahe hain (Gemini → Google jaanch, 2-6 min)...")
        return run(lambda: (_QB.fill_all(max_cats=11), tg.say(_QB.status_text())))
    if tl in ("3d jaanch", "3d test", "3d check"):
        from . import blender3d as _B3
        tg.say("🧊 3D jaanch chal rahi hai (1-3 min)...")
        return run(lambda: tg.say(_B3.self_test()))
    if tl in ("3d repair karo", "3d repair", "3d theek karo"):
        from . import blender3d as _B3
        tg.say("🧊 Blender zaroori library ke saath dobara lag raha hai (5-15 min)...")
        return run(lambda: tg.say(_B3.repair()))
    if tl in ("3d install karo", "blender install karo"):
        from . import blender3d as _B3
        tg.say("🧊 Blender install ho raha hai (~5-15 min, VM dheere se) ...")
        return run(lambda: tg.say(_B3.install()))
    if tl in ("3d band", "3d chalu"):
        state.put("s33_pending", tl.endswith("chalu"))
        return tg.say(f"⚠️ Pakka? Reel mein apna 3D chitra {'CHALU' if tl.endswith('chalu') else 'BAND'}.",
                      tg.inline([[("✅✅ Haan, pakka", "s33:y"), ("❌ Nahi", "s33:n")]]))
    if t in ("📘 Studio manual", "/manual") or tl in ("manual", "studio manual", "sample manual", "guide"):
        from . import studio
        return tg.say(studio.MANUAL)
    if t in ("📅 Din-plan", "/plan7") or tl in ("din plan", "din-plan", "hafte ka din plan", "kis din kya"):
        from . import weekplan
        return tg.say(weekplan.text())
    if tl in ("din plan band", "din plan chalu"):
        state.put("dp_pending", {"op": "onoff", "val": tl.endswith("chalu")})
        return tg.say(f"⚠️ Pakka? Din-plan {'CHALU' if tl.endswith('chalu') else 'BAND'} (roz ki video ka andaaz).",
                      tg.inline([[("✅✅ Haan, pakka", "dp:y"), ("❌ Nahi", "dp:n")]]))
    try:
        from . import weekplan
        _ch = weekplan.parse_change(t)
    except Exception:
        _ch = None
    if _ch:
        bk, wd, val = _ch
        state.put("dp_pending", {"op": "set", "bk": bk, "wd": wd, "val": list(val)})
        return tg.say(f"⚠️ Pakka? {BRANDS[bk]['name']} — {weekplan.DAYS[wd]} ka andaaz '{val[0]}' "
                      f"(aage har {weekplan.DAYS[wd]} isi tarah).", tg.inline([[("✅✅ Haan, pakka", "dp:y"), ("❌ Nahi", "dp:n")]]))
    if t in ("🎨 24 Look", "/looks", "/24look") or tl in ("24 look", "look chuno", "24 look chuno"):
        return tg.say("🎨 Kis channel ke 24 look set karne hain? (har look = pakka sawal + apna 3D chitra)",
                      tg.inline([[(v["name"], f"s24:b:{k}")] for k, v in BRANDS.items()]))
    if t in ("⏰ Best time", "/besttime") or tl in ("best time", "best samay", "kab daalein"):
        from . import studio
        return tg.say(studio.best_time_text(), tg.inline([[("✅ Ye samay lagao", "s24:bt"), ("❌ Nahi", "s24:no")]]))
    if t == "🧪 Namoona":
        from . import studio
        return tg.say(studio.status_text() + "\n\nYa kisi 24-look ka namoona: '🎨 24 Look' → channel → '🎬 Kisi look ka namoona'.",
                      studio.brand_buttons())
    if t in ("🧪 Sample studio", "/sample", "/namoona") or tl in ("sample", "namoona", "sample studio", "sample video",
                                                                      "namoona video", "sample dikhao", "namoona dikhao"):
        from . import studio                    # v2.2.0: har channel ka namoona (kabhi post nahi)
        bk = next((k for k, v in BRANDS.items() if k in tl or v["name"].lower() in tl), None)
        if bk:
            return run(studio.make, bk, 0)
        return tg.say(studio.status_text(), studio.brand_buttons())
    if tl.startswith(("sample ", "namoona ")):
        from . import studio
        bk = next((k for k, v in BRANDS.items() if k in tl or v["name"].lower().split()[0] in tl.split()), None)
        if bk:
            return run(studio.make, bk, 0)
        return tg.say(studio.status_text(), studio.brand_buttons())
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
    _m = _re.match(r"(?i)\s*pinterest\s+app\s*id\s+(\d{5,9})\s*$", t)
    if _m:                                      # v2.0.9: OAuth mein sahi App ID (redirect mismatch ka asli kaaran)
        from . import pinterest as PI
        PI.set_app_id(_m.group(1))
        return tg.say(f"✅ Pinterest App ID ab {PI.app_id()}. Ab '/pinterest' likhein - naya login link milega.")
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
    if tl in ("comment haal", "comments haal", "comment", "comments", "/comments", "comment ka haal", "jawab haal"):
        from . import growth
        return tg.say(growth.comment_text())
    if (tl in ("poora haal", "pura haal", "followers", "/followers", "engagement") or
            sum(w in tl for w in ("follower", "like", "view", "comment", "subscriber")) >= 2):
        from . import growth                        # v2.1.5: followers + views + likes + comment ek saath
        tg.say("📈 Saare platform se ginti la raha hoon (1 min)...")
        return run(lambda: tg.say(growth.engagement_report()))
    if tl in ("google jaanch", "google check", "google haal", "/google", "analytics jaanch", "ga jaanch"):
        from . import website
        return run(lambda: tg.say(website.google_check()))
    if tl in ("index bhejo", "indexing bhejo", "sitemap bhejo", "daily index"):
        from . import website
        return run(lambda: tg.say("📮 " + website.daily_index()))
    if (re.search(r"\b(ind[ei]?[kx]s?\w*|indix\w*|indeks\w*)\b", tl) and not tl.startswith(("index bhejo", "indexing bhejo"))
            and re.search(r"\b(report|riport|haal|hal|status|batao|bata|bataiye|latest|kitne|kitna|dikhao|do|kya hua|"
                          r"kon|kaun|konse|kaunse|kon ?kon|bheje|bheja|huye|hue|hua)\b", tl)):
        from . import website, pagequeue as _pq   # v3.3.2: 14 Nov 'indixing report do latest' ka jawab hi nahi aaya tha
        def _ir():
            r = website.bing_report()
            g = _pq.gidx_summary()
            if g and g not in r:
                r += "\n\n" + g
            r += "\n\n" + website.indexnow_text()
            if re.search(r"\b(kon|kaun|konse|kaunse|bheje|bheja)\b", tl):   # v3.3.2 audit-5: 2-3 Nov 'kaun se bheje' - naam bhi do
                r += "\n\n" + website.sent_today_text()
            tg.say("📑 Indexing ka taaza haal (Google + Bing):\n" + r)
        return run(_ir)
    if tl in ("bing haal", "bing", "indexing haal", "index haal", "/bing", "indexnow haal"):
        from . import website
        return run(lambda: tg.say(website.bing_report() + "\n\n" + website.indexnow_text()))
    if (any(w in tl for w in ("website", "site", "link", "traffic")) and
            any(w in tl for w in ("aaye", "aaya", "aya ", "aye", "kitne log", "click", "visitor", "traffic", "aate", "aaenge",
                                  "aayenge", "users"))):
        from . import website                       # v2.1.4: seedha GA4 (Gemini se 'access nahi' jawab nahi)
        d = 30 if any(w in tl for w in ("mahin", "month", "30 din")) else (
            7 if any(w in tl for w in ("hafte", "hafta", "week", "7 din", "saptah")) else (2 if "kal" in tl else 1))
        tg.say("🔎 Google Analytics se asli ginti la raha hoon...")
        return run(lambda: tg.say(website.traffic(d)))
    if "pinterest" in tl and any(w in tl for w in ("kya hua", "kya huwa", "haal", "status", "manzoori", "approve")):
        from . import pinterest as PI
        ps = PI.status()
        return tg.say("📌 Pinterest: " + ("✅ Standard LIVE - pins public ja rahi hain." if ps["live"] else
                      (f"Standard form {state.get('pin_form')} ko bhara, Pinterest review kar raha hai (aksar 1-4 hafte). "
                       "Bot roz 11 baje khud jaanchta hai; milte hi pins public + aapko khabar." if state.get("pin_form") else
                       "Standard form abhi nahi bhara.")) + f"\nLogin: {'✅' if ps['oauth'] else '❌'} | abhi: {ps['env']}")
    if tl in ("vm audit", "/audit", "audit", "pura audit", "poora audit", "vm ka audit", "postmortem", "vm postmortem"):
        from . import vmaudit                        # v2.1.1: sirf padhta hai; file sirf owner ko (GitHub nahi)
        tg.say("🔎 Poore VM ka audit shuru (1-3 min). Kuch badlega/mitega nahi.")
        return run(lambda: tg.say(vmaudit.run_and_send()))
    if tl in ("chowkidar fix", "chowkidar fix karo", "chowkidar theek karo", "chowkidar update", "chowkidar update karo"):
        files, txt = updater.chowkidar_preview()
        if not files:
            return tg.say(txt)
        return tg.say(txt + "\n\nPakka badlein?", tg.inline([[("✅ Haan, badlo", "cw:1")], [("❌ Nahi", "cw:0")]]))
    if "chowkidar" in tl and any(w in tl for w in ("file", "code", "bhejo", "do")):
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
    try:                                            # v2.9.4: bina pakke command wali baat ka record (seekhne ke liye; 50 tak)
        state.update("free_text_log", lambda L: ((L or []) + [{"t": time.strftime("%Y-%m-%d %H:%M"), "x": text[:200]}])[-50:], [])
    except Exception:
        pass
    fz = fuzzy_command(tl)                          # v2.7.2: spelling galat ho to bhi pakka command chale
    if fz and fz != tl and not text.startswith("__fz__"):
        tg.say(f"🔤 Aapne '{t[:40]}' likha - maine '{fz}' samjha.")
        return on_text("__fz__" + fz)
    return run(think, text)


def learn_propose():
    """v2.9.4 (owner: 'bot chatting dekh kar khud seekhe, pushti le'): pichhli baaton mein jo pakka command nahi bani, Gemini se
    'shayad iska matlab ye command' -> owner ko button. Haan = hamesha ke liye (learned_alias)."""
    from .brain import ask_gemini
    log_ = [r["x"] for r in (state.get("free_text_log") or []) if len(r.get("x", "")) < 80][-25:]
    if len(log_) < 3:
        return None
    prompt = ("Telegram bot ke owner ne ye chhote sandesh likhe jo kisi pakke command se nahi mile. Har ek ke liye batao ki inme se "
              "kaunsa command uska matlab hai (sirf tab jab pakka ho, warna null):\nCOMMANDS: " + ", ".join(KNOWN_CMDS) +
              "\nSANDESH:\n" + "\n".join(f"- {x}" for x in log_) + '\nReturn ONLY JSON list: [{"msg": "...", "cmd": "... ya null"}]')
    try:
        r = ask_gemini(prompt, temperature=0.1)
    except Exception:
        return None
    rows = [x for x in (r if isinstance(r, list) else []) if isinstance(x, dict) and x.get("cmd") in KNOWN_CMDS and x.get("msg")]
    if not rows:
        return None
    pend = {str(i): [x["msg"].strip().lower()[:80], x["cmd"]] for i, x in enumerate(rows[:6])}
    state.put("learn_pending", pend)
    return ("🧠 Bot seekhna chahta hai - aapki ye baatein kisi pakke command se nahi mili thi. Sahi ho to ✅ dabaiye (hamesha yaad):\n"
            + "\n".join(f"{k}. '{v[0]}' → {v[1]}" for k, v in pend.items()),
            tg.inline([[(f"✅ {k}", f"la:{k}") for k in list(pend)[:3]], [(f"✅ {k}", f"la:{k}") for k in list(pend)[3:6]]
                       if len(pend) > 3 else [("❌ Koi nahi", "la:x")], [("❌ Koi nahi", "la:x")]]))


KNOWN_CMDS = ("amp jaanch", "traffic trend", "quiz bot haal", "vote chalu", "look haal", "kya chal raha", "sawal schedule", "bank safai", "hook haal", "hook rotate", "channel setup", "comment haal", "aaj ka haal", "poora haal", "sab theek", "pending",
              "website traffic", "bing haal", "sarkari dar", "dar jaancho", "policy haal", "policy jaancho", "keyword sudhaar",
              "link theek", "site scan", "backup password", "backup password reset", "backup password save", "backup abhi",
              "jawab haal", "ypp haal", "adsense haal", "best time", "24 look", "namoona", "token haal", "google jaanch",
              "seo diary", "keywords", "canary", "features", "pause", "resume", "abhi video", "raasta haal", "vm audit",
              "queue haal", "queue roko", "queue chalu", "queue abhi")


def fuzzy_command(tl):
    """Chhote command ki spelling galti (2-3 akshar) pakdo. Lambi baat nahi - wo Gemini samjhega."""
    import difflib
    if not tl or len(tl) > 30 or tl in KNOWN_CMDS:
        return None
    m = difflib.get_close_matches(tl, KNOWN_CMDS, n=1, cutoff=0.84)
    return m[0] if m else None


def schedule_text():
    """v2.3.6: 'reel kab aayegi' ka PAKKA jawab (asli schedule + aaj kya bana/gaya) - AI ke andaaze ki jagah."""
    from .config import QUIZ_SLOT
    from .weekplan import ANDAAZ, style_for
    t = pipeline.now()
    today = str(t.date())
    made = state.get("made_today") or {}
    hist = [h for h in (state.get("history") or []) if h.get("date") == today]
    L = [f"🗓 AAJ ({today}) KA PAKKA SCHEDULE - har channel 2 SAWAL wali reel (3 ghante pehle banti, aapko Thumb ke saath aati):"]
    for b, slots in pipeline.schedule().items():
        sl = [x.strip() for x in str(slots).split(",") if x.strip()]
        parts = []
        for hm in sl:
            kind = "jaancha puzzle/GK/24-look" if (QUIZ_SLOT.get(b) == hm or (len(sl) > 1 and hm == sl[-1])) else "naya Gemini sawal (din-format)"
            st = "✅ ban chuki/line mein" if made.get(f"{today}:{b}:{hm}") else ("⏳ " + ("abhi banegi" if hm > t.strftime("%H:%M") else "samay nikal gaya"))
            parts.append(f"{hm} {kind} ({st})")
        L.append(f"• {BRANDS[b]['name']}: " + " | ".join(parts))
    L.append(f"Aaj upload ho chuke: {len(hist)} | Aaj ka format: " + ", ".join(
        f"{BRANDS[b]['name'].split()[0]}={(style_for(b).split('(')[1].split(')')[0] if '(' in style_for(b) else style_for(b)[:20]) or '-'}"
        for b in BRANDS))
    L.append("Samay badalna: '⏰ Best time' ya 'schedule money 12:30,20:30' (dohri pushti).")
    _ = ANDAAZ
    return "\n".join(L)


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
            f"SCHEDULE_TRUTH (reel kab - inhi se jawab do): {schedule_text()}\n"
            f"connections: {'; '.join(conn)}; pinterest={PI.env() if PI.connected() else 'nahi'}; "
            f"meta_secret_problem={bool(M.has_token() and M._cfg().get('secret_bad'))}\n"
            f"jobs: {js}\nrecent uploads: {up}\nrecent errors: {errs}\n"
            f"vm: ram_free_mb={mem_avail_mb()}, disk_used_gb={du.used / 1e9:.0f}/{du.total / 1e9:.0f}, "
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
        return run(lambda: tg.say(website.traffic_smart() if int(it.get("count") or 1) == 1 else website.traffic(int(it.get("count")))))
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
    if a == "chat" and re.search(r"(kar diya|kar di |kar diye|ho gaya hai|saaf kar|bhej diya|laga diya|set kar diya|band kar diya|"
                                 r"chalu kar diya|delete kar|mita diya|thik kar diya|theek kar diya|fix kar)", rep.lower()):
        rep += ("\n\n⚠️ Sach: ye sirf baat-cheet ka jawab hai - maine abhi koi kaam CHALAYA nahi. Asli kaam ke liye button dabayein "
                "ya saaf hukum likhein (jaise 'kachra saaf', '3d jaanch', 'schedule money 12:30,20:30').")   # v2.3.7
    tg.say(rep)
    try:                                           # v2.0.4: har baat ka record; jo bot kar nahi paya wo AI ke liye
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
    tg.say(reopen_jobs())


import re as _re
PENDING_SECRETS = {}
RX_META = _re.compile(r"EAA[A-Za-z0-9]{40,}")
RX_SECRET = _re.compile(r"\b[0-9a-f]{32}\b")
RX_THREADS = _re.compile(r"\bTH[A-Za-z0-9_\-]{40,}")
RX_TGTOKEN = _re.compile(r"\b\d{8,12}:[A-Za-z0-9_\-]{30,}\b")
RX_PIN = _re.compile(r"\bpina_[A-Za-z0-9_\-]{20,}")


REOPEN_GAP_MIN = 20          # v2.6.3: ek ke baad ek, 20 min ke farak se (pehle 30 post 2 min mein - Instagram/FB spam jaisa)
REOPEN_MAX_AGE_DAYS = 3      # isse purani ruki video dobara social par nahi (purana maal ek saath = spam jaisa)


def _qb_tok(text):
    from . import quizbot as _QB
    return _QB.parse(text)


def welcome_text():
    from .config import OFFICIAL, OFFICIAL_COMMON
    L = ["🙏 Sab Hisaab mein aapka swagat hai!", "",
         "Roz naye dimagi sawal, paheli, ganit trick aur Uttarakhand GK - har reel ka sahi jawab + wajah yahan aur website par.", "",
         f"🧮 Free calculator + saare jawab: {OFFICIAL_COMMON['site']}/jawab", f"💬 WhatsApp channel: {OFFICIAL_COMMON['whatsapp']}", ""]
    for b, v in BRANDS.items():
        o = OFFICIAL.get(b) or {}
        L.append(f"▶️ {v['name']}: {o.get('yt', '')}")
    L += ["", f"📌 Pinterest: {OFFICIAL_COMMON['pinterest']}", "",
          "Sirf yahi hamare asli channel hain. Koi aur paise maange ya 'inaam' ka link de to wo nakli hai."]
    return "\n".join(L)


def welcome_pin():
    from .config import TG_CHANNEL
    r = tg.call("sendMessage", {"chat_id": TG_CHANNEL, "text": welcome_text(), "disable_web_page_preview": "true"}, timeout=60)
    mid = ((r or {}).get("result") or {}).get("message_id") or (r or {}).get("message_id")
    if not mid:
        return "❌ Channel mein post nahi gaya - bot channel ka admin hai? ('Post messages' ijaazat)"
    try:
        tg.call("pinChatMessage", {"chat_id": TG_CHANNEL, "message_id": mid, "disable_notification": "true"}, timeout=60)
    except Exception as e:
        return f"✅ Welcome post gaya, par PIN nahi hua ({str(e)[:80]}) - bot ko channel mein 'Pin messages' ijaazat dein, ya khud pin karein."
    try:                                           # v2.9.3: dono purane 'welcome pin' kaam band
        from . import tasks
        for _ in range(3):
            if not tasks.mark_done("welcome", prefix=False):
                break
    except Exception:
        pass
    return "✅ Telegram channel mein welcome post daal kar PIN kar diya. WhatsApp channel mein yahi text aap forward kar dein:\n\n" + welcome_text()


def reopen_jobs():
    """Naya login/token juda -> ruki video phir chalao (jo platform ho chuka, dobara nahi), par DHEERE: har ek 20 min ke farak
    par, aur 3 din se purani nahi (wo 'partial' hi rehti hai, flag old_skip). -> owner ke liye ek line."""
    import datetime as _dt
    now_ = _dt.datetime.now(IST)
    rows = []
    for jid, j in pipeline.jobs().items():
        if j.get("status") in ("need_login", "partial") and not j.get("old_skip"):
            rows.append((j.get("created", ""), jid, j))
    rows.sort()
    k, old = 0, 0
    for created, jid, j in rows:
        try:
            age = (now_ - _dt.datetime.fromisoformat(created).astimezone(IST)).days if created else 0
        except Exception:
            age = 0
        if age > REOPEN_MAX_AGE_DAYS:
            j["status"], j["old_skip"] = "partial", True
            old += 1
        else:
            j["status"], j["tries"], j["now"] = "approved", 0, False
            j["slot"] = (now_ + _dt.timedelta(minutes=5 + k * REOPEN_GAP_MIN)).isoformat()
            k += 1
        pipeline.save_job(jid, j)
    if not rows:
        return "ℹ️ Koi ruki video nahi thi."
    return (f"♻️ {k} ruki video dobara line mein - har ek {REOPEN_GAP_MIN} min ke farak par (spam se bachav)"
            + (f"; {old} video {REOPEN_MAX_AGE_DAYS} din se purani thi - unhe dobara nahi bheja" if old else ""))


def psi_weekly():
    """v2.9.5 (pending 'PageSpeed watcher'): 5 zaroori page ki mobile speed + LCP/CLS; 50 se kam par saaf chetavni."""
    import requests as _rq
    from . import website
    k = website._env().get("PSI_KEY")
    if not k:
        return "📊 PageSpeed: key bot mein nahi. Bhejein: psi key <AIza...> (Google Cloud 'sabhinet-pagespeed' wali)"
    rows = []
    for pth in ("/", "/jawab", "/emi-calculator", "/discount-calculator", "/nali-mutthi-square-feet"):
        try:
            r = _rq.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                        params={"url": f"https://sabhisaab.com{pth}", "key": k, "strategy": "mobile", "category": "performance"},
                        timeout=150).json()
            if "error" in r:
                rows.append(f"• {pth}: ❌ {r['error'].get('message', '')[:80]}")
                continue
            lh = r["lighthouseResult"]
            sc = int(lh["categories"]["performance"]["score"] * 100)
            au = lh.get("audits", {})
            lcp = au.get("largest-contentful-paint", {}).get("displayValue", "?")
            cls = au.get("cumulative-layout-shift", {}).get("displayValue", "?")
            rows.append(f"• {pth}: {'🟢' if sc >= 90 else '🟡' if sc >= 50 else '🔴'} {sc}/100 | LCP {lcp} | CLS {cls}")
        except Exception as e:
            rows.append(f"• {pth}: jaanch nahi ({str(e)[:60]})")
    state.put("psi_last", rows)
    return "📊 Website speed (mobile, PageSpeed):\n" + "\n".join(rows) + "\n(🔴 ho to Claude ko dikhayein - kaunsa hissa bhaari hai wo report mein)"


def _psi_test():
    try:
        import requests as _rq
        from . import website
        k = website._env().get("PSI_KEY")
        r = _rq.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                    params={"url": "https://sabhisaab.com/", "key": k, "strategy": "mobile", "category": "performance"},
                    timeout=120).json()
        if "error" in r:
            return f"❌ Key jaanch fail: {r['error'].get('message', '')[:150]}"
        sc = int(r["lighthouseResult"]["categories"]["performance"]["score"] * 100)
        return f"✅ Key chal rahi hai - sabhisaab.com mobile speed: {sc}/100"
    except Exception as e:
        return f"Key rakh li; jaanch nahi ho payi ({str(e)[:80]})"


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
    gk = _re.search(r"\bAIza[0-9A-Za-z_\-]{30,}", text)
    if gk and not text.lower().startswith("psi key"):   # v2.1.8: Google API key bina 'psi key' ke (pehle Gemini tak gayi)
        tg.delete(msg["chat"]["id"], msg["message_id"])
        f = SECRETS / "aiza.pending"
        SECRETS.mkdir(mode=0o700, exist_ok=True)
        f.write_text(gk.group())
        f.chmod(0o600)
        tg.say("🔐 Google API key mili (chat se mitayi, abhi kahin nahi rakhi). Ye kis kaam ki hai?",
               tg.inline([[("📊 PageSpeed (website speed)", "ak:psi")], [("❌ Galti se bheji - mita do", "ak:0")]]))
        return True
    pin_sec = _re.search(r"(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])", text)
    if pin_sec:          # v2.0.10: 40-hex = Pinterest App secret (akela ho ya 'pinterest secret naya <secret>' ke saath)
        tg.delete(msg["chat"]["id"], msg["message_id"])
        from . import pinterest as PI
        PI.save_secret(pin_sec.group())
        state.put("awaiting", "")
        tg.say("🔐 Pinterest App secret surakshit (chat se mitaya). Ab ye link kholein, 'Allow' dabayein, phir browser ka "
               f"POORA address (sabhisaab.com/?code=...) yahan bhejein:\n{PI.oauth_link()}")
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
            tg.say(reopen_jobs())
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
    if kind == "pq":                               # v3.3.0: page queue (dohri pushti)
        from . import pagequeue as _PQ
        return _PQ.on_callback(rest, run)
    if kind == "sk":                               # v2.0.5: 32-akshar key kiski hai
        f = SECRETS / "secret32.pending"
        if not f.exists():
            return tg.say("Ye purana sawaal hai, key dobara bhejein.")
        val = f.read_text().strip()
        f.unlink(missing_ok=True)
        if rest == "no":
            return tg.say("Theek hai, key kahin nahi rakhi (mita di).")
        return run(lambda: tg.say(save_secret32("bing" if rest == "bing" else "meta", val)))
    if kind == "ak":                               # v2.1.8: Google API key kis kaam ki
        f = SECRETS / "aiza.pending"
        if not f.exists():
            return tg.say("Ye key purani ho gayi - dobara bhejein.")
        k_ = f.read_text().strip()
        f.unlink(missing_ok=True)
        if rest == "psi":
            from . import website
            website.set_env("PSI_KEY", k_)
            return run(lambda: tg.say("🔐 PageSpeed key surakshit. " + _psi_test()))
        return tg.say("🗑 Key mita di, kahin nahi rakhi.")
    if kind == "hg":                               # v2.1.6: pending kaam pakka ho gaya
        if rest == "0":
            return tg.say("Theek hai, list mein rehne diya.")
        from . import tasks
        gone = tasks.mark_done(rest, prefix=True)
        return tg.say(("✅ List se hataya:\n" + "\n".join("• " + g["x"][:100] for g in gone)) if gone else
                      "Ye kaam pehle hi hat chuka hai.")
    if kind == "cw":                               # v2.1.0: Chowkidar ytlistener -> sabhinet (dohri pushti)
        if rest == "0":
            return tg.say("Theek hai, Chowkidar ko nahi chheda.")
        if rest == "1":
            return tg.alert("yellow", "⚠️ Dobara pakka? Chowkidar ki file badlegi aur Chowkidar 10 sec ke liye restart hoga "
                                      "(trading service par asar nahi).",
                            tg.inline([[("✅✅ Haan, pakka", "cw:2")], [("❌ Nahi", "cw:0")]]))
        if rest == "2":
            return run(lambda: tg.say(updater.chowkidar_apply()))
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
    if kind == "s45":                              # v2.5.7: privacy patch (dohri pushti)
        if rest == "ok":
            from . import privacy_patch as _PP
            return run(lambda: tg.say("📝 " + _PP.apply()))
        return tg.say("👍 Privacy page nahi badla.")
    if kind == "s46":                              # v2.5.7: Telegram quiz poll
        if rest in ("on", "off"):
            state.put("answer_poll", rest == "on")
            return tg.say("✅ Telegram quiz poll " + ("CHALU (roz max 2)." if rest == "on" else "BAND."))
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s47":                              # v3.1.0: awaaz ki raftaar (dohri pushti)
        from . import finalgate as _FG
        v_ = _FG.parse_speed(rest)
        if v_ is None:
            return tg.say("👍 Kuch nahi badla.")
        state.put("voice_speed", v_)
        return tg.say(f"✅ Awaaz ki raftaar ab {v_:.2f}. Agli video se laagu. Wapas: 'awaaz raftaar 1.0'.")
    if kind == "s44":                              # v2.5.2: jawab digest (dohri pushti)
        if rest in ("on", "off"):
            state.put("answer_digest", rest == "on")
            return tg.say("✅ Jawab digest " + ("CHALU: roz 20:30 par ek message." if rest == "on" else "BAND: har video ke saath alag post."))
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s43":                              # v2.5.2: ads.txt (dohri pushti)
        pub = state.get("adsense_pending")
        state.put("adsense_pending", None)
        if rest == "ok" and pub:
            from . import adsense as _AD
            return run(lambda: tg.say("🌐 " + _AD.write_ads_txt(pub)))
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s42":                              # v2.5.0: sab channel ek samay
        tm = state.get("sched_all_pending")
        state.put("sched_all_pending", None)
        if rest == "y" and tm:
            state.update("schedule", lambda d: {**(d or {}), **{b: tm for b in BRANDS}}, {})
            return tg.say(f"✅ Charon channel ab roz {tm} (alag-alag sawal).")
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s41":                              # v2.5.0: jawab website page (dohri pushti)
        if rest == "on":
            return tg.say("⚠️ Dobara pakka? Bot roz website par sirf /jawab page update karega (audit pass hone par).",
                          tg.inline([[("✅✅ Haan, pakka", "s41:ON"), ("❌ Nahi", "s41:off")]]))
        if rest == "ON":
            state.put("jawab_site_on", True)
            state.put("answer_dirty", True)
            state.put("jawab_pub_at", 0)
            from . import answers as _A
            run(lambda: tg.say("🌐 " + _A.publish_site(force=True)))
            return tg.say("✅ Website /jawab chalu - pehla page ban raha hai.")
        if rest == "voff":
            state.put("answer_offsite", False)
            return tg.say("✅ Ab jawab pehle ki tarah VIDEO mein hi aayega.")
        if rest == "von":
            state.put("answer_offsite", True)
            return tg.say("✅ Ab jawab video mein nahi - Telegram/website par.")
        if rest == "x":
            return tg.say("👍 Kuch nahi badla.")
        state.put("jawab_site_on", False)
        return tg.say("👍 Jawab sirf Telegram channel par jayenge (website band).")
    if kind == "la":                               # v2.9.4: seekha hua matlab pakka
        pend = state.get("learn_pending") or {}
        if rest in pend:
            msg_, cmd_ = pend[rest]
            state.update("learned_alias", lambda d: {**(d or {}), msg_: cmd_}, {})
            return tg.say(f"✅ Yaad kar liya: '{msg_}' = {cmd_}")
        return tg.say("👍 Theek, kuch nahi seekha.")
    if kind == "ho":                               # v2.9.3: owner ki pushti - bot-jaanch wala kaam band (dobara nahi dikhta)
        from . import tasks
        if tasks.owner_confirm(rest):
            return tg.say("✅ Pakka - list se hata diya, ab dobara nahi aayega. (Itihaas: docs/PENDING.md)")
        return tg.say("🔑 Ye kaam bot API se hi pakka karta hai - jo token/link maanga gaya tha wahi bhejein.")
    if kind == "wp":                               # v2.9.2: Telegram channel welcome post + pin
        if rest != "y":
            return tg.say("👍 Kuch nahi kiya.")
        return run(lambda: tg.say(welcome_pin()))
    if kind == "cs":                               # v2.7.2: channel setup wizard
        from . import setupwiz as _SW, studio as _ST
        op, _, arg = rest.partition(":")
        if op == "b" and arg in BRANDS:
            txt_, kb_ = _SW.card(arg)
            return tg.say(txt_, kb_)
        if op == "hk" and arg in BRANDS:
            txt_, kb_ = _SW.hook_samples(arg)
            return tg.say(txt_, kb_)
        if op == "hs":
            br_, _, md_ = arg.partition(":")
            if br_ in BRANDS:
                tg.say(_SW.set_hook(br_, md_))
                txt_, kb_ = _SW.card(br_)
                return tg.say(txt_, kb_)
        if op == "look" and arg in BRANDS:
            tg.say(f"🎬 {BRANDS[arg]['name']}: namoona ban raha hai (2-6 min) - video + 3 thumbnail aayenge. Wahan '➡️ Agla' "
                   "se agla look, '✅ Pakka' se pakka. Namoona kabhi post nahi hota.")
            return run(_ST.make, arg, int(((state.get("studio") or {}).get(arg) or {}).get("n", 0)))
        if op == "pal":
            return tg.say(_ST.palettes_text())
        if op == "bt":
            return tg.say(_ST.best_time_text(), tg.inline([[("✅ Ye samay lagao", "s24:bt"), ("❌ Nahi", "s24:no")]]))
        if op == "fin" and arg in BRANDS:
            return tg.say(_SW.finalize(arg), _SW.brand_menu())
        return tg.say("Ye button purana hai - '⚙️ Channel setup' dobara likhein.")
    if kind == "s41b":                             # v2.7.1: backup password reset
        if rest == "saved":
            state.put("bk_pass_saved", True)
            return tg.say("✅ Shabaash. Roz ki yaad band.")
        if rest != "y":
            return tg.say("👍 Kuch nahi badla.")
        from . import ops as _OPS

        def _do():
            pw, msg = _OPS.reset_password()
            r_ = tg.say(f"🔐 NAYA backup password:\n\n{pw}\n\nIse abhi Google Keep / phone ke Notes / kaagaz par likh lein "
                   "(backup ke saath Telegram par mat rakhiye). Ye message 15 min mein khud mitega.\n" + msg,
                   tg.inline([[("✅ Maine save kar liya", "s41b:saved")]]))
            try:
                mid = (r_ or {}).get("message_id") or ((r_ or {}).get("result") or {}).get("message_id")
                if mid:
                    threading.Timer(900, lambda: tg.call("deleteMessage", {"chat_id": tg._chat(), "message_id": mid})).start()
            except Exception:
                pass
        return run(_do)
    if kind == "s40":                              # v2.4.0: backup password badlo
        np_ = state.get("bkpass_pending")
        state.put("bkpass_pending", None)
        if rest == "y" and np_:
            from . import ops as _OPS
            return tg.say(_OPS.set_password(np_))
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s39":                              # v2.4.0: naya layout haan/naa
        from . import studio
        op, _, nm = rest.partition(":")
        if op in ("la", "lr"):
            return studio.layout_decide(nm, op == "la")
        return tg.say("👍")
    if kind == "s38":                              # v2.3.7: roz ka routine (dohri pushti)
        rp = state.get("routine_pending")
        state.put("routine_pending", None)
        if rest == "y" and rp:
            state.update("routines", lambda L: ((L or []) + [{"t": rp[0], "cmd": rp[1]}])[-20:], [])
            return tg.say(f"✅ Ab roz {rp[0]} par: '{rp[1]}' (apne aap)")
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s37":                              # v2.3.6: schedule badlaav (dohri pushti)
        sp = state.get("sched_pending")
        state.put("sched_pending", None)
        if rest == "y" and sp:
            state.update("schedule", lambda d: {**(d or {}), sp[0]: sp[1]}, {})
            return tg.say(f"✅ {BRANDS[sp[0]]['name']}: ab roz {sp[1]}")
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s36":                              # v2.3.6: naya rang haan/naa
        from . import studio
        op, _, nm = rest.partition(":")
        if op in ("pa", "pr"):
            return studio.palette_decide(nm, op == "pa")
        if op == "rh":
            state.update("palettes_ok", lambda L: [x for x in (L or []) if x != nm], [])
            return tg.say(f"✅ Rang '{nm}' list se hata.")
        return tg.say("👍")
    if kind == "s24":                              # v2.3.3: 24-look chunna + namoona + best time (dohri pushti)
        from . import studio
        op, _, rr = rest.partition(":")
        bk, _, lk = rr.partition(":")
        if op == "b" and bk in BRANDS:
            return tg.say(studio.looks_text(bk), studio.looks_menu(bk))
        if op in ("t", "all", "none") and bk in BRANDS:
            from .puzzles import LOOK24, looks_for
            dr = state.get("looks24_draft") or {}
            cur = list(dr.get(bk) if dr.get(bk) is not None else looks_for(bk))
            if op == "t" and lk in LOOK24:
                cur = [x for x in cur if x != lk] if lk in cur else cur + [lk]
            elif op == "all":
                cur = list(LOOK24)
            elif op == "none":
                cur = []
            dr[bk] = cur
            state.put("looks24_draft", dr)
            return tg.say(f"{BRANDS[bk]['name']}: {len(cur)}/24 chune (abhi pakka nahi)", studio.looks_menu(bk))
        if op == "f" and bk in BRANDS:
            n_ = len(((state.get("looks24_draft") or {}).get(bk)) or [])
            return tg.say(f"⚠️ Dobara pakka? {BRANDS[bk]['name']} ki roz ki paheli-reel sirf in {n_} look se (0 = sab 24).",
                          tg.inline([[("✅✅ Haan, pakka", f"s24:F:{bk}"), ("❌ Nahi", "s24:no")]]))
        if op == "F" and bk in BRANDS:
            dr = state.get("looks24_draft") or {}
            sel = dr.pop(bk, None)
            state.put("looks24_draft", dr)
            if sel is not None:
                state.update("looks24", lambda d: {**(d or {}), bk: sel}, {})
            return tg.say(f"✅ Pakka: {BRANDS[bk]['name']} - {len(sel or []) or 24} look roz baari-baari (3D ke saath).")
        if op == "sm" and bk in BRANDS:
            return tg.say("Kaun sa look dekhna hai? (namoona, post nahi hoga)", studio.sample_look_buttons(bk))
        if op == "s" and bk in BRANDS:
            tg.say("🎬 Namoona ban raha hai (3D ke saath 3-8 min)...")
            return run(studio.make_look, bk, lk)
        if op == "bt":
            return tg.say("⚠️ Dobara pakka? Charon channel ka samay sujhav ke hisaab se badlega (har channel 2 reel).",
                          tg.inline([[("✅✅ Haan, lagao", "s24:BT"), ("❌ Nahi", "s24:no")]]))
        if op == "BT":
            prop = state.get("best_time_pending") or {}
            if prop:
                state.update("schedule", lambda d: {**(d or {}), **prop}, {})
                state.put("best_time_pending", None)
                return tg.say("✅ Naya samay laga: " + " | ".join(f"{BRANDS[k]['name'].split()[0]} {v}" for k, v in prop.items()))
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s33":                              # v2.3.3: 3D band/chalu (dohri pushti)
        v_ = state.get("s33_pending")
        state.put("s33_pending", None)
        if rest == "y" and v_ is not None:
            state.put("use_3d", bool(v_))
            return tg.say(f"✅ Apna 3D: {'CHALU' if v_ else 'BAND'}")
        return tg.say("👍 Kuch nahi badla.")
    if kind == "pe":                               # v2.3.0 Step 7: 50-button deck
        if rest == "home":
            return send_pro_deck_home()
        if rest.startswith("panel:"):
            ttl, rows = PRO_DECK_PANELS.get(rest.split(":", 1)[1], PRO_DECK_PANELS["A"])
            return tg.say(f"🎛 {ttl}", tg.inline(rows))
        if rest in ("27y", "28y", "33y"):
            if rest == "33y":
                v = not state.get("auto_reply", True)
                state.put("auto_reply", v)
                return tg.say(f"✅ Vinamra jawab (comment ka insaani-andaaz jawab): {'CHALU' if v else 'BAND'}")
            state.put("auto_approve", rest == "27y")
            return tg.say("✅ Autopilot CHALU (slot par Thumb 1 se khud; sirf audit-paas)." if rest == "27y"
                          else "✅ Manzoori par roko: aapke button ke bina koi post nahi.")
        b_no = int(rest) if rest.isdigit() else 0
        if b_no in PE_STYLE:
            from . import studio
            vi = next((i for i, lk in enumerate(studio.LOOKS) if lk.get("visual") == PE_STYLE[b_no]), 0)
            return tg.say(f"Style '{PE_STYLE[b_no]}' ka namoona kis channel par? (post nahi hoga)",
                          tg.inline([[(v["name"], f"sm:b:{k}:{vi}")] for k, v in BRANDS.items()]))
        if b_no == 9:
            return on_callback({"id": "0", "data": "s4:pz:shuddh_hindi"})
        if b_no == 11:
            return on_text("🗓 Panchang Badge")
        if b_no in (12, 13, 14, 15):
            bk = {12: "money", 13: "deals", 14: "pahadi", 15: "sunonatak"}[b_no]
            return run(pipeline.prepare, bk, None, "aapne maanga")
        if b_no == 17:
            return tg.say("⚡ Rewatch code: sirf challenge/puzzle video ke 2nd scene par 'Code yaad rakhein: #NN' (sach rehne ke liye "
                          "aam video par nahi). Band karna ho to 'puzzle din band'.")
        if b_no == 21:
            from .config import AI_LABEL
            import inspect
            from . import youtube as _Y, meta as _M
            y_ok = "containsSyntheticMedia" in inspect.getsource(_Y.upload)
            f_ok = "is_ai_generated" in inspect.getsource(_M.post_facebook)
            return tg.say(f"🤖 AI LABEL JAANCH (code se):\n• Har description: '{AI_LABEL}' ✅\n• YouTube containsSyntheticMedia: "
                          f"{'✅' if y_ok else '❌'}\n• Facebook is_ai_generated: {'✅' if f_ok else '❌'}\n• Instagram/Threads: description label ✅")
        if b_no in (27, 28):
            return tg.say("⚠️ Pakka? " + ("Autopilot CHALU: jawab na mile to slot par Thumb 1 se khud post." if b_no == 27
                                         else "Manzoori par roko: aapke button ke bina koi post nahi."),
                          tg.inline([[("✅✅ Haan, pakka", f"pe:{b_no}y"), ("❌ Nahi", "pe:home")]]))
        if b_no == 30:
            reopen_jobs()
            return tg.say("▶️ Atke / login-wale kaam dobara line mein.")
        if b_no == 31:
            from . import meta as _M
            led = state.get("ig_dm_ledger") or {}
            return tg.say("📲 COMMENT-DM: 24 ghante mein ek user ko ek DM (Meta niyam) | aaj ke DM: "
                          f"{sum(1 for k in led if ':c:' in k)}\n" + "\n".join(
                              f"• {BRANDS[b]['name']}: {'🔒 band' if _M.ig_dm_blocked(b) else '🟢 khula'}" for b in BRANDS))
        if b_no == 33:
            return tg.say(f"⚠️ Pakka? Vinamra jawab {'BAND' if state.get('auto_reply', True) else 'CHALU'} karein?",
                          tg.inline([[("✅✅ Haan, pakka", "pe:33y"), ("❌ Nahi", "pe:home")]]))
        if b_no == 46:
            return tg.say("📂 Sirf 1 surakshit file: likhein 'single file AI_START.md' (secret/token wali file kabhi nahi).")
        if b_no in PE_TEXT:
            return on_text(PE_TEXT[b_no])
        return tg.say("👍")
    if kind == "s6":                               # v2.3.0 Step 6: website DRAFT (sirf owner ko, live nahi)
        def _wd():
            from . import web_widgets as _WW
            zp = _WW.build_widget_bundle_zip(rest)
            with open(zp, "rb") as fh:
                tg.call("sendDocument", {"chat_id": tg._chat(), "caption":
                        f"📝 DRAFT (live nahi): {rest}\n1 page + widget (reel-code jawab, streak, sudhaar email) + reel-codes.json.\n"
                        "Ye Claude ko bhejein; sudhri hui website ZIP yahan bhejne par hi audit ke baad live."}, {"document": fh})
        return run(_wd)
    if kind == "s5":                               # v2.3.0 Step 5: gallery (dohri pushti)
        p_ = state.get("s5_pending")
        state.put("s5_pending", None)
        if rest == "y" and p_:
            from . import files as _FL, diary
            if p_ == "gal_off":
                state.put("no_gallery_reels", True)
                diary.add("niyam", "owner: gallery photos se reels mat banana")
                return tg.say("✅ Gallery photo se reel BAND.")
            if p_ == "gal_on":
                state.put("no_gallery_reels", False)
                return tg.say("✅ Gallery photo se reel CHALU.")
            if p_ == "gal_del":
                return run(lambda: tg.say(_FL.delete_recent_photos(3)))
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s4":                               # v2.3.0 Step 4: puzzle
        from . import puzzles as _pz
        op, _, arg = rest.partition(":")
        if op == "pz" and arg in _pz.PUZZLE_TYPES:
            return tg.say("Kis channel par?", tg.inline([[(v["name"], f"s4:pb:{arg}:{k}")] for k, v in BRANDS.items()]))
        if op == "pb":
            kd, _, bk = arg.partition(":")
            if bk in BRANDS:
                def _mk():
                    sc = _pz.generate_puzzle(kd, bk)
                    pipeline.prepare(bk, None, "aapne maanga (puzzle)", None, "short", "", None, sc)
                return run(_mk)
        if op == "card":
            def _card():
                codes = state.get("reel_codes") or {}
                code = list(codes)[-1] if codes else _pz.generate_puzzle("auto", "sunonatak")["reel_code"]
                cp = _pz.make_challenge_card(10, 0, code)
                tg.photos([str(cp)], f"📲 WhatsApp challenge card (1080x1080) - puzzle #{code}. Forward karein.")
            return run(_card)
        if op == "car":
            return on_text("/carousel")
        if op == "on":
            v = state.get("s4_pending")
            state.put("s4_pending", None)
            if v is not None:
                state.put("puzzles_on", bool(v))
                return tg.say(f"✅ Challenge din par puzzle: {'CHALU' if v else 'BAND'}.")
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s3":                               # v2.3.0 Step 3: awaaz setting (dohri pushti)
        ap = state.get("awaaz_pending")
        state.put("awaaz_pending", None)
        if rest == "ay" and ap:
            state.update("awaaz", lambda d: {**(d or {}), ap[0]: bool(ap[1])}, {})
            return tg.say(f"✅ Awaaz '{ap[0]}': {'CHALU' if ap[1] else 'BAND'} (agli video se).")
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s2":                               # v2.3.0 Step 2: visual style / HUD
        from . import studio
        op, _, arg = rest.partition(":")
        if op == "st" and arg in BRANDS:
            return tg.say(f"{BRANDS[arg]['name']}: kaun sa style? (namoona aayega, post nahi hoga)", studio.style_buttons(arg))
        if op == "hy":
            hp = state.get("hud_pending")
            state.put("hud_pending", None)
            if hp:
                return tg.say(studio.hud_apply(hp[0], hp[1]))
        return tg.say("👍 Kuch nahi badla.")
    if kind == "s1":                               # v2.3.0 Step 1: dohri pushti wale
        if rest == "ds":
            from .guard import clean_uv_cache
            return run(lambda: tg.say(clean_uv_cache(execute=True)))
        if rest in ("v1", "v0"):
            state.put("vault_on", rest == "v1")
            if rest == "v1":
                from . import vault_web
                vault_web.get_key()
                vault_web.start_vault(lambda x: safe(on_text, x))
            return tg.say("✅ Web Vault " + ("CHALU (127.0.0.1:8099; chabi VM par secrets/vault_key.txt)." if rest == "v1" else "BAND."))
        return tg.say("👍 Kuch nahi badla.")
    if kind == "dp":                               # v2.2.0: din-plan badlaav (dohri pushti)
        p = state.get("dp_pending") or {}
        state.put("dp_pending", {})
        if rest != "y" or not p:
            return tg.say("👍 Kuch nahi badla.")
        from . import weekplan
        if p.get("op") == "onoff":
            state.put("day_plan_on", bool(p.get("val")))
            return tg.say(f"✅ Din-plan {'CHALU' if p.get('val') else 'BAND'}.")
        return tg.say(weekplan.apply_change(p["bk"], int(p["wd"]), p["val"]))
    if kind == "dl":                               # v2.5.4: namoona video ka Download button (original file)
        from . import studio as _ST
        return run(_ST.download, rest)
    if kind == "sm":                               # v2.2.0: Sample Studio
        from . import studio
        op, _, rr = rest.partition(":")
        jid, _, arg = rr.partition(":")
        if op == "b" and jid in BRANDS:
            return run(studio.make, jid, int(arg or 0))
        if op == "t":
            return tg.say(studio.like(jid, arg or 1))
        if op == "n":
            return run(studio.new_thumbs, jid)
        if op == "x":
            return run(studio.nxt, jid)
        if op == "d":
            return tg.say(studio.wipe(jid))
        if op == "f":
            return studio.finalize_ask(jid)
        if op == "F":
            return tg.say(studio.finalize(jid))
        if op == "p":
            return studio.promote(jid)
        return tg.say("👍 Theek hai, kuch pakka nahi kiya.")
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
            tg.say("🔐 Website ki Google service account file surakshit (chat se mitayi). Ab jaanch kar raha hoon...")
            return run(lambda: tg.say(website.google_check()))
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
    try:                                              # v2.9.2: quiz bot (token ho to) alag thread
        from . import quizbot as _QB0
        if _QB0.token():
            _QB0._started = True
            _QB0.start()
    except Exception:
        log("quizbot " + traceback.format_exc())
    try:
        from . import privacy
        privacy.migrate()          # v2.0: audience platform-wise
    except Exception:
        log("privacy migrate " + traceback.format_exc())
    try:                                              # v2.1.5: website config (bot token) sirf owner padhe
        from .config import DATA as _D
        if (_D / "site_repo" / "config.json").exists():
            (_D / "site_repo" / "config.json").chmod(0o600)
    except Exception:
        pass
    try:
        n_ = updater.scrub_logs()                     # v2.0.8: purane log se token mitao
        if n_:
            log(f"scrub_logs: {n_} line saaf")
    except Exception:
        log("scrub " + traceback.format_exc())
    recover()
    tg.set_commands([("menu", "Poora menu"), ("login", "YouTube channel jodna"), ("logs", "Log"),
                     ("safai", "Safai"), ("panic", "Sab roko"), ("version", "Version"),
                     ("sample", "Sample studio (namoona)"), ("manual", "Studio manual"), ("quota", "Roz ki seema"),
                     ("blindfold", "Gemini Blindfold (DLP)"), ("styles", "9 visual style"), ("hud", "Video HUD"), ("awaaz", "Awaaz/SFX"),
                     ("qc", "Video QC (LUFS)"), ("carousel", "5-slide carousel"),
                     ("puzzles", "11 puzzle/GK mode"), ("card", "WhatsApp challenge card"), ("exam", "Exam sawal (dual-solver)"), ("revenue", "Kamai yojana + 10 vibhag"),
                     ("scroll", "Scroll-away jaanch"), ("gallery", "Photo gallery"), ("dpdp", "DPDP ledger"), ("webpage", "Website page draft (Claude ke liye)"), ("pro50", "50-button Pro Deck"),
                     ("audit6x", "6-pass asli audit"), ("examalerts", "Sarkari exam khabar"), ("deepsafai", "Deep safai + atka ffmpeg"), ("vault", "Web Vault 8099")])
    try:                                                   # v2.3.0: Web Vault sirf owner ne chalu kiya ho tab
        from . import vault_web
        vault_web.start_vault(lambda x: safe(on_text, x))
    except Exception:
        log("vault_web start " + traceback.format_exc())
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
    if not state.get("ntfy_rotated_214"):                  # v2.1.4: purana topic GitHub par khula tha -> naya
        try:
            from . import backup, relay
            if state.get("ntfy_ok"):
                backup.rotate()
                if relay.cfg().get("url"):
                    threading.Thread(target=lambda: safe(relay.deploy), daemon=True).start()
                tg.say("🔒 Suraksha: ntfy ka purana topic galti se GitHub par dikh gaya tha, isliye bot ne NAYA topic bana diya.\n"
                       "ntfy app mein purana topic hata kar ye naya jodein (2 minute):\n\n" + backup.setup_text())
            state.put("ntfy_rotated_214", True)
        except Exception:
            log("ntfy rotate " + traceback.format_exc())
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
                elif m.get("voice") or m.get("audio"):           # v2.4.0: awaaz se hukum
                    from . import media_tools as _MT
                    run(_MT.on_voice, m, on_text)
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
                elif m.get("text") and m["text"].lower().lstrip().startswith(("onesignal", "one signal")):
                    from . import push as _PS                   # v2.9.2: OneSignal App ID + key (chat se mitao)
                    tg.delete(m["chat"]["id"], m["message_id"])
                    pk = _PS.parse(m["text"])
                    if not pk:
                        tg.say("❌ App ID (abcd1234-....) aur API key dono nahi mile. Aise bhejein:\nonesignal <App ID> <API key>")
                    else:
                        _PS.save(*pk)
                        tg.say("🔐 OneSignal key VM par surakshit (chat se mitaya). Website par button laga raha hoon...")
                        run(lambda: tg.say(_PS.setup()))
                elif m.get("text") and ("quiz bot" in m["text"].lower() or "quizbot" in m["text"].lower()) and _qb_tok(m["text"]):
                    from . import quizbot as _QB                # v2.9.2: BotFather token (chat se mitao)
                    tg.delete(m["chat"]["id"], m["message_id"])
                    tok_ = _qb_tok(m["text"])
                    try:
                        me = _QB.api("getMe", tok=tok_).get("result") or {}
                    except Exception:
                        me = {}
                    if not me.get("username"):
                        tg.say("❌ Ye token Telegram ne nahi maana. BotFather se dobara copy karke bhejein: quiz bot token <token>")
                    else:
                        _QB.save(tok_)
                        if not getattr(_QB, "_started", False):
                            _QB._started = True
                            _QB.start()
                        tg.say(f"✅ Quiz bot chalu: https://t.me/{me['username']} (token surakshit, chat se mitaya). Log /aaj se sawal, "
                               "code bhej kar purana jawab, /roz se roz ka sawal le sakte hain.")
                elif m.get("text") and "localhost" in m["text"] and _ytc_mod.is_comment_paste(m["text"]):
                    from . import ytcomment as YC          # v2.5.7: comment-login (state=ytc:<brand>)
                    tg.delete(m["chat"]["id"], m["message_id"])
                    try:
                        br_, title = YC.exchange(m["text"])
                        state.put("yt_reply_noscope", bool(YC.missing()) and state.get("yt_reply_noscope"))
                        state.put("yt_comment_noscope", bool(YC.missing()) and state.get("yt_comment_noscope"))
                        left = YC.missing()
                        tg.say(f"✅ Comment-login juda: {BRANDS[br_]['name']} (channel '{title}'). Ab is channel par jawab/pehla comment jayega."
                               + (f"\nBaaki: {', '.join(BRANDS[x]['name'] for x in left)} → 'yt comment login'" if left else "\n🎉 Sab channel ho gaye."))
                    except Exception as e:
                        tg.alert("yellow", f"Comment-login nahi hua: {str(e)[:250]}\n'yt comment login' se naya link lein (code 10 min chalta hai).")
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
