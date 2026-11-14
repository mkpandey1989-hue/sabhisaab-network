"""v2.3.3: APNA 3D (Gemini ke bina) - Blender (free, open-source) se har reel ka 3D chitra. VM par raat ko apne aap install.
Sirf apne banaye aakar (koi bahari model/copyright nahi). Hindi text 3D mein nahi - neon design upar se lagta hai."""
import hashlib
import pathlib
import shutil
import subprocess
import time

from . import state
from .config import DATA
from .log import log

CACHE = DATA / "img3d"
SCENE = pathlib.Path(__file__).with_name("blender3d_scene.py")
THEMES = ("couple", "heart_brain", "coins", "mountains", "question", "clock", "balance", "vault", "chess", "bowls", "camels",
          "matrix", "gates", "laser", "family", "elevator", "cube", "train", "compass", "well", "bridges", "river", "flasks",
          "blackhole", "candles", "triangle", "crime", "grid")


def available():
    return bool(shutil.which("blender")) and state.get("use_3d", True)


def install():
    """Ek baar: sudo apt se Blender (~400 MB). Trading ko na chhede: nice + raat. -> text"""
    if shutil.which("blender"):
        return "✅ Blender pehle se hai"
    r = subprocess.run("sudo -n nice -n 15 apt-get -o DPkg::Lock::Timeout=600 install -y -q --no-install-recommends blender",
                       shell=True, capture_output=True, text=True, timeout=3600)
    ok = bool(shutil.which("blender"))
    state.put("blender_install", {"t": time.strftime("%Y-%m-%d %H:%M"), "ok": ok, "err": (r.stderr or "")[-300:]})
    return "✅ Blender install ho gaya - ab har reel mein apna 3D" if ok else "❌ Blender install nahi hua: " + (r.stderr or "")[-200:]


def _h2(script):
    return int(hashlib.md5(str(script.get("title", "")).encode()).hexdigest()[:4], 16) % 2


def theme_for(script):
    """Format/puzzle/brand se 3D scene."""
    st = (script.get("fmt_style") or "") + " " + " ".join(sc.get("show", "") for sc in (script.get("scenes") or [])[:2])
    pk = script.get("puzzle_kind", "")
    b = script.get("brand", "")
    if script.get("look24"):                          # v2.3.3: owner ke 24-look ka apna scene
        lk = script["look24"]
        return {"dice": "cube", "origami": "cube", "chronicle": "clock", "circuit": "laser", "lever": "balance",
                "prison": "train", "cyber": "matrix", "ramayan": "camels", "aladdin": "candles", "pahadi_rasta": "mountains",
                "titanic": "river", "mirror_clock": "clock", "blackbox": "vault", "spinner": "blackhole", "lava": "candles",
                "swamp": "grid", "kitchen": "flasks", "balloon": "question", "anime": "family"}.get(lk, lk if lk in THEMES else "question")
    ttl = str(script.get("title", ""))
    if "Dil vs Dimag" in ttl:
        return "heart_brain" if _h2(script) else "couple"
    if "Pyaar ka Hisaab" in ttl or "Pahadi Dil" in ttl:
        return "couple"
    if "Sach ya Jhooth" in ttl:
        return "question"
    if pk in ("pahadi_gk",) or (b == "pahadi" and "Dil vs" not in st and "couple" not in st.lower()):
        return "mountains"
    if pk in ("speed_math", "exam_quant", "number_connect"):
        return "coins"
    kmap = {"sudoku4": "grid", "series": "matrix", "coding": "vault", "calendar": "clock", "clock_angle": "clock",
            "direction": "compass", "age": "family", "utpate_shabd": "question", "purane_shabd": "coins",
            "pahadi_purana": "mountains", "pahadi_shabd": "mountains", "shuddh_hindi": "question", "word_scramble": "matrix",
            "memory_flash": "grid", "odd_one_out": "laser", "color_match": "flasks", "ball_memory": "bowls",
            "matchstick": "triangle", "optical_count": "triangle"}       # v2.3.4: har sawal ke hisaab se apna scene
    if pk in kmap:
        return kmap[pk]
    if pk:
        return "question"
    if "Dil vs Dimag" in st:
        return "heart_brain" if _h2(script) else "couple"
    if "Pyaar ka Hisaab" in st or "COUPLE" in st:
        return "couple" if b in ("sunonatak", "pahadi") or _h2(script) else "coins"
    if "Sach ya Jhooth" in st:
        return "question"
    return "coins" if b in ("money", "deals") else "question"


ALT = {   # v2.3.4: aaj doosre channel par same scene gaya ho to milta-julta doosra
    "question": ["vault", "laser", "blackhole", "crime", "matrix"], "coins": ["vault", "balance", "chess", "bowls"],
    "couple": ["heart_brain", "family", "candles"], "heart_brain": ["couple", "balance", "candles"],
    "mountains": ["river", "bridges", "well", "compass"], "clock": ["candles", "compass", "blackhole"],
    "grid": ["matrix", "cube", "chess"], "matrix": ["grid", "cube", "laser"],
}


def _unique_today(brand, th):
    """Ek din mein do channel par kabhi ek jaisa 3D scene nahi."""
    import datetime as _dt
    today = str(_dt.date.today())
    d = (state.get("theme_day") or {}).get(today) or {}
    used = {v for k, v in d.items() if k != brand}
    if th in used:
        th = next((a for a in ALT.get(th, []) + list(THEMES) if a not in used), th)
    state.update("theme_day", lambda x: {today: {**((x or {}).get(today) or {}), brand: th}}, {})
    return th


def render(script, w=800, h=450, samples=24, accent="00e5ff"):
    """-> PNG path (1280x720, naram) ya None. Cache: same title+theme dobara nahi banta."""
    if not available():
        return None
    th = script.get("theme3d") or theme_for(script)
    if not script.get("sample_mode") and not script.get("look24"):
        th = _unique_today(script.get("brand", ""), th)
    key = hashlib.md5(f"{script.get('title', '')}|{th}|{w}x{h}".encode()).hexdigest()[:12]
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{th}_{key}.png"
    if out.exists():
        return out
    raw = CACHE / f"raw_{key}.png"
    seed = int(key[:6], 16) % 100000
    try:
        r = None
        for mode in ("simple", "full"):              # v2.3.5: saada (Blender 4/5 dono) pehle; chamak PIL se
            r = subprocess.run(["nice", "-n", "15", shutil.which("blender") or "blender", "-b", "--factory-startup", "-P", str(SCENE),
                                "--", th, str(seed), str(raw), str(w), str(h), str(samples), accent, mode],
                               capture_output=True, text=True, timeout=900, env=_env())
            if raw.exists():
                break
            _fail(th, mode, r)
        if not raw.exists():
            return None
        from PIL import Image, ImageFilter, ImageEnhance, ImageChops
        im = Image.open(raw).convert("RGB").filter(ImageFilter.MedianFilter(3))
        im = ImageEnhance.Contrast(im).enhance(1.06).resize((1280, 720), Image.LANCZOS)
        hi = im.point(lambda v: 0 if v < 170 else int((v - 170) * 2.4))          # v2.3.5: chamak (bloom) - har Blender par
        im = ImageChops.add(im, hi.filter(ImageFilter.GaussianBlur(14)), scale=1.25)
        im.save(out)
        raw.unlink(missing_ok=True)
        state.update("img3d_count", lambda n: (n or 0) + 1, 0)
        return out
    except Exception as e:
        log(f"blender3d: {e}")
        return None


def _env():
    import os
    e = dict(os.environ)
    e.setdefault("HOME", "/home/ubuntu")
    e["PYTHONPATH"] = ""                              # bot ka venv Blender ke apne Python se na takraaye
    e.pop("PYTHONHOME", None)
    return e


def _fail(th, mode, r):
    tail = ((r.stdout or "") + "\n" + (r.stderr or ""))[-700:] if r else "koi output nahi"
    state.put("b3d_last_err", {"t": time.strftime("%Y-%m-%d %H:%M"), "theme": th, "mode": mode, "rc": getattr(r, "returncode", None),
                               "tail": tail})
    state.update("b3d_fail_count", lambda n: (n or 0) + 1, 0)
    log(f"blender3d {th} {mode} rc={getattr(r, 'returncode', None)}: {tail[-300:]}")


def self_test():
    """'3d jaanch': chhota sa render (~20-60 sec) - safal/asafal + asli galti ki aakhri lines (Claude ke liye)."""
    if not shutil.which("blender"):
        return "❌ Blender VM par nahi mila. Likhein: '3d install karo'"
    t0 = time.time()
    out = CACHE / "selftest.png"
    CACHE.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    v = subprocess.run([shutil.which("blender"), "-b", "--factory-startup", "--version"], capture_output=True, text=True, timeout=120, env=_env())
    lines = [f"🧊 3D JAANCH: {(v.stdout or '').splitlines()[0] if v.stdout else 'version nahi mila'}"]
    for mode in ("simple", "full"):
        r = subprocess.run(["nice", "-n", "15", shutil.which("blender"), "-b", "--factory-startup", "-P", str(SCENE), "--",
                            "coins", "7", str(out), "160", "90", "4", "00e5ff", mode], capture_output=True, text=True, timeout=600, env=_env())
        if out.exists():
            lines.append(f"✅ 3D theek hai ({time.time() - t0:.0f} sec, {'Blender 4/5 dono wala tareeka' if mode == 'simple' else mode}; "
                         "chamak bahar se lagti hai).")
            state.put("b3d_last_err", None)
            return "\n".join(lines)
        _fail("coins", mode, r)
        lines.append(f"❌ {mode} tareeka nahi chala (rc {r.returncode})")
    err = (state.get("b3d_last_err") or {}).get("tail", "")
    lines.append("Aakhri galti (ye screenshot Claude ko bhejein):\n" + "\n".join(err.strip().splitlines()[-12:])[-900:])
    lines.append("Turant koshish: '3d repair karo' (zaroori library ke saath dobara install)")
    return "\n".join(lines)


def repair():
    """Blender zaroori library (Mesa/EGL, recommends) ke saath dobara - ARM VM par kuch library chhoot jaati hain."""
    r = subprocess.run("sudo -n nice -n 15 apt-get -o DPkg::Lock::Timeout=600 install -y -q --reinstall blender libgl1 libegl1 "
                       "libglx-mesa0 libgl1-mesa-dri libxi6 libxxf86vm1 libxfixes3 libxrender1 libxkbcommon0 libsm6",
                       shell=True, capture_output=True, text=True, timeout=3600)
    state.put("blender_install", {"t": time.strftime("%Y-%m-%d %H:%M"), "ok": bool(shutil.which("blender")),
                                  "err": (r.stderr or "")[-300:]})
    return self_test()


def cleanup(days=7):
    cut = time.time() - days * 86400
    for f in CACHE.glob("*.png") if CACHE.exists() else []:
        if f.stat().st_mtime < cut:
            f.unlink(missing_ok=True)


def status_text():
    bi = state.get("blender_install") or {}
    le = state.get("b3d_last_err") or {}
    return (f"🧊 APNA 3D (Blender): {'✅ chalu' if available() else ('❌ band (use_3d)' if shutil.which('blender') else '⏳ install baaki')}\n"
            f"• Ab tak bane 3D chitra: {state.get('img3d_count') or 0} | atke: {state.get('b3d_fail_count') or 0}\n"
            + (f"• Aakhri galti ({le.get('t')}, {le.get('theme')}/{le.get('mode')}): {le.get('tail', '')[-160:]}\n" if le else "")
            + "• Jaanch: '3d jaanch' | theek: '3d repair karo'\n"
            f"• Scene: couple (pyaar), dil-vs-dimag tarazu, sikke/%, pahad, chamakta '?'\n"
            f"• Install: {bi.get('t', '-')} {'✅' if bi.get('ok') else ('❌ ' + bi.get('err', '')[:80] if bi else '')}\n"
            "• Hukum: '3d install karo' | '3d band' / '3d chalu' (dohri pushti)")


# ---------------- v2.4.0: pehle AI-ART (Cloudflare Flux, aapke sample jaisa), na mile to apna Blender 3D ----------------
ART_PROMPT = {
    "couple": "a cute stylized 3D animated cartoon couple (young man and woman, Indian, family friendly) facing each other, glowing heart between them, neon city bokeh",
    "heart_brain": "a golden balance scale with a glowing red heart on one side and a glowing pink brain on the other",
    "coins": "stacks of shiny gold coins on a dark reflective table, luxury finance scene",
    "mountains": "majestic Himalayan snow peaks at sunrise with deodar trees and a small stone temple, Uttarakhand",
    "question": "a glowing crystal sphere with swirling neon light rings above a reflective floor",
    "clock": "an antique golden pocket watch on dark velvet with glowing gears",
    "balance": "an ornate golden balance scale holding sparkling diamonds",
    "vault": "a futuristic steel bank vault door with a glowing combination dial and red laser beams",
    "chess": "a royal golden chess set mid-game on a marble board, dramatic spotlight",
    "bowls": "three ornate golden bowls upside down on a table with a sparkling diamond peeking out",
    "camels": "a desert palace at dusk with a caravan of camels, golden light",
    "matrix": "abstract glowing neon cubes floating in dark cyberspace",
    "gates": "two glowing futuristic gates guarded by two robot sentinels, one blue one red",
    "laser": "a dark vault room crossed with red laser beams and a glowing diamond on a pedestal",
    "family": "glowing connected orbs network like a tree of light in a dark room",
    "elevator": "a sleek glass elevator in a modern tower at night with glowing floor buttons",
    "cube": "a colorful Rubik's style cube sliced into small glowing cubes",
    "train": "a vintage train entering a stone mountain tunnel with headlights glowing",
    "compass": "a brass compass on an old map with a long shadow from the morning sun",
    "well": "a cute green cartoon frog climbing out of an old stone well, sunny village",
    "bridges": "three different rope and wooden bridges over a deep glowing canyon",
    "river": "a small wooden boat on a calm river with a goat and a cabbage, misty morning",
    "flasks": "glowing colorful laboratory flasks and test tubes on a dark bench",
    "blackhole": "a swirling black hole with a bright orange accretion disk in deep space",
    "candles": "two burning candles in the dark with soft warm glow and smoke",
    "triangle": "an impossible Penrose triangle sculpture glowing in neon colors",
    "crime": "a detective desk with a magnifying glass, old papers and yellow crime-scene tape, noir light",
    "grid": "a glowing neon tiled floor pattern in perspective, dark futuristic room",
}


LOOK_ART = {
    "ramayan": "an ancient golden palace of Lanka on an island at sunset, epic Indian architecture, no people",
    "aladdin": "a magical golden oil lamp glowing with blue smoke in a cave full of treasure",
    "pahadi_rasta": "a winding Himalayan trekking trail leading to a stone temple between snow peaks",
    "titanic": "a sunken ocean liner on the sea floor with a glowing treasure chest and old keys",
    "mirror_clock": "an ornate magic mirror reflecting a vintage wall clock in a candle-lit room",
    "blackbox": "a bright orange aircraft flight recorder box on a hangar floor",
    "spinner": "a hypnotic black and white optical illusion spiral",
    "lava": "a scorching desert valley with heat haze and cracked earth at noon",
    "swamp": "a misty swamp path of glowing stepping stones",
    "kitchen": "pink Himalayan rock salt crystals in a rustic Indian kitchen",
    "balloon": "colorful balloons floating in a park with an archery target",
    "anime": "a row of identical cute stylized robots with one slightly different",
    "dice": "two ivory dice tumbling on green felt with dramatic light",
    "origami": "a paper cube being folded from a cross-shaped net, origami style",
    "chronicle": "a steampunk time machine with clocks and calendars",
    "circuit": "a glowing electronic circuit board with sparks",
    "lever": "a wooden lever balance with weights on a workshop table",
    "prison": "a dark stone prison tunnel with three glowing exits",
    "cyber": "a hooded figure silhouette in a dark room lit by green screen glow, no face",
}


def ai_art(script, accent="00e5ff"):
    """-> path ya None. Owner ke CF account ki free seema; fail par caller Blender chalata hai."""
    if not state.get("use_ai_art", True):
        return None
    th = script.get("theme3d") or theme_for(script)
    if not script.get("sample_mode") and not script.get("look24"):
        th = _unique_today(script.get("brand", ""), th)
    base = LOOK_ART.get(script.get("look24", "")) or ART_PROMPT.get(th, ART_PROMPT["question"])
    key = hashlib.md5(f"{script.get('title', '')}|{th}|art".encode()).hexdigest()[:12]
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"art_{th}_{key}.jpg"
    if out.exists():
        return out
    from . import imagegen
    p = imagegen.cf_image(base, out)
    if not p:
        return None
    try:
        from PIL import Image, ImageOps
        im = Image.open(p).convert("RGB")
        ImageOps.fit(im, (1280, 720), Image.LANCZOS, centering=(0.5, 0.5)).save(out, quality=92)
    except Exception as e:
        log(f"ai_art resize: {e}")
    state.update("ai_art_count", lambda n: (n or 0) + 1, 0)
    return out
