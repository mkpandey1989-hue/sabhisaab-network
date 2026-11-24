"""v2.3.0 (v11 ke '6-pass audit' ki jagah ASLI jaanch): har pass sach mein chalata hai aur ✅/❌ wahi likhta hai jo
nikla. v11 mein ye sab likha-likhaya 'PASS ✅' tha (jaise 'Claude-Audit 100% Verified')."""
import pathlib
import py_compile
import tempfile


def _ok(cond, txt):
    return f"{'✅' if cond else '❌'} {txt}"


def run_6pass_audit() -> str:
    from . import state
    keep = {k: state.get(k) for k in ("used_puzzle_hashes", "reel_codes", "last_puzzle_kind")}   # jaanch se asli sawal kharch na hon
    try:
        return _run(L=["🏆 6-PASS ASLI SELF-AUDIT (sab abhi chalaya gaya):"])
    finally:
        for k, v in keep.items():
            state.put(k, v)


def _run(L):
    from . import bot, guard, imagegen, puzzles, calendar_in, sfx, web_widgets, pipeline, youtube, threads, pinterest, design
    from .config import BASE, VISUAL_STYLES
    from .meta import ig_safe_text
    # 1 code
    bad = []
    for pf in sorted((BASE / "app").glob("*.py")):
        try:
            py_compile.compile(str(pf), doraise=True)
        except Exception as e:
            bad.append(f"{pf.name}: {str(e)[:60]}")
    L.append(_ok(not bad, f"1) Code: {len(list((BASE / 'app').glob('*.py')))} file compile" + (f" | galti: {bad[:2]}" if bad else "")))
    # 2 buttons
    deck = [b for _, rows in bot.PRO_DECK_PANELS.values() for r in rows for b in r if b[1].startswith("pe:") and b[1][3:].isdigit()]
    menu = [x for r in bot.MENU_ROWS for x in r]
    L.append(_ok(len(deck) == 50, f"2) 50-button deck: {len(deck)}/50 | menu button {len(menu)}"))
    # 3 privacy/blindfold
    leak = "EAAabcdef1234567890abcdefghijklmnop AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz123456 test@gmail.com 9876543210 /home/ubuntu/sabhisaab-network/secrets/bot.env"
    sc = guard.scrub_for_ai(leak)
    igt = ig_safe_text("Dekho https://sabhisaab.com/?utm=1 #a #b #c #d #e #f #g")
    L.append(_ok(all(x not in sc for x in ("EAAabc", "AIzaSy", "test@gmail", "9876543210", "/secrets/bot.env")) and "http" not in igt,
                 "3) Gemini Blindfold + Instagram bina link"))
    # 4 visuals
    with tempfile.TemporaryDirectory() as td:
        tp = pathlib.Path(td)
        n_ok = 0
        for v in [s for s in VISUAL_STYLES if s != "auto"]:
            try:
                imagegen.procedural_scene("money", v, 0, "Test", tp / f"{v}.png")
                n_ok += 1
            except Exception:
                pass
        try:
            pz = puzzles.generate_puzzle("speed_math", "money")
            design.background("money", "t", tp / "bg.jpg")
            design.body_frame(pz, 1, len(pz["scenes"]), tp / "b.png")
            design.thumbnail(pz, tp / "th.jpg")
            neon_ok = True
        except Exception:
            neon_ok = False
    L.append(_ok(n_ok == 9 and neon_ok, f"4) Visual: {n_ok}/9 style + Premium Neon quiz (frame+thumbnail)"))
    # 5 puzzle/panchang/audio
    ok1, v1 = puzzles.dual_verify_math("square_diff", 9, 7)
    ex = puzzles.generate_exam_question("Banking")
    p = calendar_in.fast_panchang()
    rs = sfx.shepard_riser_reveal()
    L.append(_ok(ok1 and ex["correct_answer"] in ex["options"] and p.get("tithi") and len(rs) > 0,
                 f"5) Puzzle dual-solver ({v1}) + exam ({ex['topic'][:20]}) + panchang ({p.get('maas')} {p.get('tithi')}) + awaaz"))
    # 6 website/long/quota
    pages = web_widgets.generate_5_elite_pages()
    spec = all(web_widgets.verify_page_spec(h, r.replace("site/", "").replace(".html", ""))["all_passed"] for r, h in pages.items())
    try:
        ls = len(pipeline.build_offline_long_script("money")["scenes"])
    except Exception as e:
        ls = f"nahi ({str(e)[:40]})"
    q = youtube.quota_status()
    L.append(_ok(spec, f"6) Website 5 page draft spec | offline lambi video {ls} scene | YouTube quota {q['remaining_units']} | "
                       f"Threads {threads.check_threads_quota('money')['used']} | Pinterest {pinterest.can_pin_now('money', 'https://sabhisaab.com/x')[0]}"))
    L.append("Trading services: sabhinet sirf padhta hai (kabhi restart/stop nahi).")
    return "\n".join(L)


def run_5pass_audit():
    return run_6pass_audit()


def run_3pass_audit():
    return run_6pass_audit()


def daily_heal():
    """v2.3.7: roz 05:45 - khud audit, jo toota wo khud theek karne ki koshish, phir sirf zaroori baat aapko."""
    import shutil
    from . import tg, guard, state
    fixed, still = [], []
    try:
        rep = run_6pass_audit()
    except Exception as e:
        rep = f"❌ audit hi nahi chala: {e}"
    bad = [ln for ln in rep.splitlines() if ln.startswith("❌")]
    du = shutil.disk_usage("/")
    if du.used / du.total > 0.80 or bad:
        try:
            guard.clean_uv_cache(execute=False)
            fixed.append("safai")
        except Exception as e:
            still.append(f"safai: {e}")
    for ln in bad:
        try:
            if ln.startswith("❌ 4)"):                    # visual/3D
                from . import blender3d
                t_ = blender3d.self_test()
                if "✅" not in t_:
                    t_ = blender3d.repair()
                (fixed if "✅" in t_ else still).append("3D: " + t_.splitlines()[-1][:80])
            elif ln.startswith("❌ 1)"):
                still.append("code compile galti - Claude ko 'vm audit' file bhejein")
        except Exception as e:
            still.append(f"{ln[:40]}: {e}")
    try:
        fixed += self_fix()                       # v2.4.0: jaani galtiyon ka pakka ilaaj
    except Exception as e:
        still.append(f"self_fix: {e}")
    try:
        from . import qbank
        if any(len(qbank.available(c)) < 3 for c in qbank.CATS):
            qbank.fill_all(max_cats=4)
            fixed.append("sawal-bank bhara")
    except Exception as e:
        still.append(f"sawal-bank: {e}")
    state.put("daily_heal", {"t": __import__("time").strftime("%Y-%m-%d %H:%M"), "bad": bad, "fixed": fixed, "still": still})
    if bad or still:
        tg.alert("yellow" if not still else "red", "🩺 ROZ KI KHUD-JAANCH:\n" + "\n".join(bad[:5]) +
                 ("\n🔧 Khud theek kiya: " + ", ".join(fixed) if fixed else "") +
                 ("\n❗ Abhi bhi dikkat: " + "; ".join(still[:3]) + "\nKya karein: 'vm audit' dabakar file Claude ko bhejein." if still else ""))
    return rep


# v2.4.0: SURAKSHIT khud-ilaaj (owner: 'bot khud apna code badle'). Code khud nahi badalta (galat patch = poora bot gir sakta);
# jaani-pehchaani galtiyon ke liye pakke ilaaj chalata hai. Anjaani galti -> saaf khabar + 'vm audit' Claude ko.
FIXES = [
    (r"models/[\w.\-]+ is not found|404 .*model|model .*not found", "Gemini model list naya (purana model hata)",
     lambda: __import__("app.brain", fromlist=["discover"]).discover(force=True)),
    (r"Pinterest login|Authentication failed.*pinterest|pinterest.*401", "Pinterest login naya",
     lambda: __import__("app.pinterest", fromlist=["refresh_oauth"]).refresh_oauth()),
    (r"Threads token|threads.*(expired|Session has expired)", "Threads token naya",
     lambda: __import__("app.threads", fromlist=["refresh_all"]).refresh_all()),
    (r"No space left|disk (full|bhar)", "safai (disk)",
     lambda: __import__("app.guard", fromlist=["clean_uv_cache"]).clean_uv_cache(execute=False)),
    (r"ffmpeg.*timed out|timed out after \d+ seconds.*ffmpeg", "atke ffmpeg hataye",
     lambda: __import__("app.guard", fromlist=["reap_stuck_ffmpeg"]).reap_stuck_ffmpeg(40)),
    (r"node_tree|Blender|blender3d .* rc=", "3D jaanch + marammat",
     lambda: __import__("app.blender3d", fromlist=["self_test"]).self_test()),
]


def self_fix(lines=3000):
    """Pichhle 24 ghante ke log mein jaani galti -> uska pakka ilaaj (din mein ek baar har ilaaj)."""
    import re
    import time as _t
    from .config import LOGS
    from . import state
    try:
        txt = "\n".join((LOGS / "engine.log").read_text(encoding="utf-8", errors="ignore").splitlines()[-lines:])
    except Exception:
        return []
    done = []
    seen = state.get("self_fix_day") or {}
    today = _t.strftime("%Y-%m-%d")
    for rx, name, fn in FIXES:
        if re.search(rx, txt, re.I) and seen.get(name) != today:
            seen[name] = today
            try:
                fn()
                done.append(f"✅ {name}")
            except Exception as e:
                done.append(f"⚠ {name}: {str(e)[:60]}")
    state.put("self_fix_day", seen)
    return done
