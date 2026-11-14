"""Script -> 1080x1920 video (awaaz + bade Hindi akshar) + 3 thumbnail."""
import json
import pathlib
import shutil
import subprocess
import time
import uuid
from PIL import Image, ImageDraw, ImageFilter
from . import text as T
from . import tts
from .config import W, H, FPS, CRF, PRESET, AUDIO_BITRATE, LOUDNESS, BRANDS, TMP, STOCK
from .guard import wait_until_ok
from .log import log


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _gradient(size, top, bottom):
    w, h = size
    t, b = _hex(top), _hex(bottom)
    img = Image.new("RGB", (1, h))
    for y in range(h):
        k = y / (h - 1)
        img.putpixel((0, y), tuple(int(t[i] + (b[i] - t[i]) * k) for i in range(3)))
    return img.resize((w, h))


def _decor(img, accent, seed):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = _hex(accent)
    w, h = img.size
    spots = [(0.12, 0.18, 0.22), (0.88, 0.32, 0.16), (0.2, 0.82, 0.18), (0.85, 0.9, 0.25)]
    for i, (x, y, r) in enumerate(spots):
        if (i + seed) % 2:
            continue
        R = int(r * w)
        d.ellipse([x * w - R, y * h - R, x * w + R, y * h + R], fill=a + (34,))
    layer = layer.filter(ImageFilter.GaussianBlur(60))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def _pill(d, xy, label, size, fg, bg):
    x, y = xy
    w = T.width(label, size) + size * 1.2
    d.rounded_rectangle([x, y, x + w, y + size * 1.7], radius=int(size * 0.85), fill=bg)
    T.draw(d, (x + size * 0.6, y + size * 0.2), label, size, fg)
    return w


def _photo_bg(path, W, H, b):
    from PIL import ImageEnhance
    ph = Image.open(path).convert("RGB")
    sc = max(W / ph.width, H / ph.height)
    ph = ph.resize((int(ph.width * sc) + 1, int(ph.height * sc) + 1), Image.LANCZOS)
    l, t = (ph.width - W) // 2, (ph.height - H) // 2
    ph = ph.crop((l, t, l + W, t + H))
    ph = ImageEnhance.Color(ImageEnhance.Contrast(ph).enhance(1.08)).enhance(1.12)   # asli, chamakdar
    ph = ImageEnhance.Brightness(ph).enhance(0.9)
    # sirf beech/neeche halki chhaya (text padhne ke liye), poori photo andheri nahi
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        a = int(110 * max(0, (y - H * 0.55) / (H * 0.45)))
        sd.line([(0, y), (W, y)], fill=a)
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(dark, ph, shade)


def bg_image(brand_key, W, H, out_png):
    b = BRANDS[brand_key]
    _decor(_gradient((W, H), *b["bg"]), b["accent"], 0).convert("RGB").save(out_png)


NEON = {"pahadi": (0, 229, 255, 190), "money": (0, 255, 135, 190), "deals": (255, 61, 139, 190), "sunonatak": (255, 204, 51, 190)}


def _hud_on(key, default=True):
    """v2.3.0 Step 2: HUD ke hisse Studio/setting se band-chalu (state 'hud')."""
    try:
        from . import state as _st
        return bool((_st.get("hud") or {}).get(key, default))
    except Exception:
        return default


def scene_frame(brand_key, title, body, idx, total, out_png, size=None, photo=None, layer=None, hud=None):
    """layer=None: poora frame | 'chrome': sirf brand + neeche site (poori video sthir) | 'body': sirf beech ka text.
    v2.3.0 Step 2 (v11 se): neon border, panchang badge, progress bar, power-word rang, (challenge par) timer + rewatch code."""
    hud = hud or {}
    W, H = size or (globals()["W"], globals()["H"])
    land = W > H
    b = BRANDS[brand_key]
    clear = photo == "CLEAR" or bool(layer)
    img = (Image.new("RGBA", (W, H), (0, 0, 0, 0)) if clear else _photo_bg(photo, W, H, b) if photo
           else _decor(_gradient((W, H), *b["bg"]), b["accent"], idx).convert("RGB"))
    d = ImageDraw.Draw(img, "RGBA")
    acc = _hex(b["accent"])
    # upar: brand + progress
    py = 50 if land else 110
    if layer != "body":
        _pill(d, (70, py), b["name"], 44, (20, 20, 20), acc)
    if land and layer != "body":      # lambi video: progress patti
        d.rounded_rectangle([W - 470, py + 26, W - 70, py + 46], radius=10, fill=(255, 255, 255, 60))
        d.rounded_rectangle([W - 470, py + 26, W - 470 + int(400 * (idx + 1) / max(total, 1)), py + 46], radius=10, fill=acc)
    if layer != "body" and _hud_on("neon"):          # v11: category neon border (har channel ka apna rang)
        d.rounded_rectangle([14, 14, W - 14, H - 14], radius=36, outline=NEON.get(brand_key, acc + (180,)), width=5)
    if layer != "body" and not land and _hud_on("panchang"):     # v11: desi panchang kone ka badge (Step 5 calendar)
        try:
            from . import calendar_in as _cal
            p_txt = _cal.badge_line() if hasattr(_cal, "badge_line") else ""
            if p_txt:
                psz = 28
                pw = T.width(p_txt, psz) + 34
                px = max(70, W - int(pw) - 65)
                py_b = py + 88
                d.rounded_rectangle([px, py_b, px + pw, py_b + 50], radius=24, fill=(10, 14, 24, 195), outline=acc + (180,), width=2)
                T.draw(d, (px + 17, py_b + 6), p_txt, psz, (255, 245, 200))
        except Exception:
            pass
    if layer != "chrome" and not land and total > 1 and _hud_on("progress"):   # v11: upar scene progress bar
        prog_w = int((W - 140) * ((idx + 1) / max(total, 1)))
        d.rounded_rectangle([70, 74, W - 70, 90], radius=8, fill=(255, 255, 255, 55))
        d.rounded_rectangle([70, 74, 70 + max(24, prog_w), 90], radius=8, fill=acc + (235,))
    if layer != "chrome" and not land and hud.get("timer") and total > 1:      # v11: timer badge (sirf challenge/puzzle par - sach)
        rem_s = max(0.8, (total - idx - 1) * float(hud.get("sec_per_scene", 4.2)))
        t_badge = f"00:0{rem_s:.1f}" if rem_s < 10 else f"00:{rem_s:.1f}"      # emoji font nahi -> sirf ank
        tb_w = T.width(t_badge, 32) + 36
        d.rounded_rectangle([W - tb_w - 65, 112, W - 65, 168], radius=26, fill=(15, 15, 22, 210), outline=(255, 230, 0, 220), width=3)
        T.draw(d, (W - tb_w - 47, 118), t_badge, 32, (255, 230, 0))
    if layer != "chrome" and not land and hud.get("rewatch") and idx == 1 and total >= 4:   # v11: beech mein chhupa code
        rw_txt = f"Code yaad rakhein: #{hud.get('rewatch')}"
        rw_w = T.width(rw_txt, 26) + 28
        d.rounded_rectangle([70, 205, 70 + rw_w, 248], radius=18, fill=(255, 230, 0, 215))
        T.draw(d, (84, 210), rw_txt, 26, (15, 15, 15))

    # title (sirf pehle scene par)
    top = 170 if land else 330
    if layer == "chrome":
        title, body = "", ""
    if idx == 0 and title:
        ts, tl = T.fit(title, W - 160, 300, start=78, smallest=50)
        for ln in tl:
            T.draw(d, ((W - T.width(ln, ts)) / 2, top), ln, ts, acc, stroke=3, stroke_fill=(0, 0, 0))
            top += int(ts * 1.35)
        top += 40
    # beech: mukhya baat
    # v1.8: Shorts/Reels ka "safe zone" - neeche ~28% (title, channel naam) aur daayin ~12% (like/comment button)
    # par platform ke button aate hain. Mukhya text ab usse upar aur button se door rehta hai.
    box_top, box_bottom = (max(top, 200), H - 210) if land else (max(top, 500), H - 790)
    if body:
        size, lines = T.fit(body, W - (360 if land else 300), box_bottom - box_top, start=96 if land else 96, smallest=48)
        block = len(lines) * size * 1.35
        y = box_top + (box_bottom - box_top - block) / 2
        pad = 46
        pw_on = _hud_on("power_words")
        d.rounded_rectangle([50, y - pad, W - 50, y + block + pad * 0.6], radius=48,
                            fill=(8, 12, 20, 155) if pw_on else (0, 0, 0, 120), outline=(acc + (110,)) if pw_on else None, width=3)
        import re as _re_pw                   # v11: power-word rang (peela number/fayda, hara sahi jawab, laal chetavni)
        pw_rx = _re_pw.compile(r"(\d+[.,%₹²³]*|₹\s*\d+|सही जवाब|सावधान|सबक|ट्रिक|चैलेंज|बोनस|फ्री|100%|99%|95%)")
        for li_idx, ln in enumerate(lines):
            ln_col = (255, 255, 255)
            if pw_on:
                if "✅" in ln or "सही जवाब" in ln or "सबक:" in ln:
                    ln_col = (0, 255, 135)
                elif any(w in ln for w in ("सावधान", "गलती", "धोखा", "जाल", "ख़तरा", "नुकसान", "⚠️")):
                    ln_col = (255, 95, 115)
                elif pw_rx.search(ln) and li_idx == 0:
                    ln_col = (255, 230, 0)
            T.draw(d, ((W - T.width(ln, size)) / 2, y), ln, size, ln_col, stroke=4, stroke_fill=(0, 0, 0))
            y += size * 1.35
    if layer == "body":
        return img.save(out_png, "PNG")
    # neeche: disclaimer + site
    # v1.8: poora pata "https://sabhisaab.com/" - Shorts/Reels mein safe zone ke andar (UI ke neeche nahi chhupta)
    from .config import SITE_URL
    site = SITE_URL
    if land:
        fs = 34
        for ln in T.wrap(b["footer"], fs, W - 160):
            T.draw(d, ((W - T.width(ln, fs)) / 2, H - 150), ln, fs, (235, 235, 235))
        T.draw(d, ((W - T.width(site, 52)) / 2, H - 100), site, 52, acc, stroke=2, stroke_fill=(0, 0, 0))
    else:
        ss = 52
        while T.width(site, ss) > W - 380 and ss > 36:      # daayin button se door
            ss -= 2
        sy = H - 710
        sw = T.width(site, ss)
        d.rounded_rectangle([(W - sw) / 2 - 26, sy - 14, (W + sw) / 2 + 26, sy + ss * 1.25 + 8], radius=30, fill=(0, 0, 0, 150))
        T.draw(d, ((W - sw) / 2, sy), site, ss, acc, stroke=2, stroke_fill=(0, 0, 0))
        fs = 32
        fy = sy + int(ss * 1.25) + 26
        for ln in T.wrap(b["footer"], fs, W - 380):
            T.draw(d, ((W - T.width(ln, fs)) / 2, fy), ln, fs, (240, 240, 240), stroke=2, stroke_fill=(0, 0, 0))
            fy += int(fs * 1.3)
    (img if clear else img.convert("RGB")).save(out_png, "PNG")


def thumbnails(brand_key, title, out_dir):
    """3 alag design ke thumbnail (1280x720)."""
    b = BRANDS[brand_key]
    acc = _hex(b["accent"])
    paths = []
    styles = [
        (b["bg"][0], b["bg"][1], (255, 255, 255), acc),
        ("#0d0d0d", "#262626", acc, (255, 255, 255)),
        (b["accent"], "#ffffff", (15, 15, 15), _hex(b["bg"][1])),
    ]
    for i, (c1, c2, txt, bar) in enumerate(styles, 1):
        img = _decor(_gradient((1280, 720), c1, c2), b["accent"] if i != 3 else b["bg"][1], i).convert("RGB")
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, 22, 720], fill=bar)
        size, lines = T.fit(title, 1120, 470, start=112, smallest=60)
        y = (720 - len(lines) * size * 1.3) / 2 - 30
        for ln in lines:
            T.draw(d, (70, y), ln, size, txt, stroke=5, stroke_fill=(0, 0, 0) if i != 3 else (255, 255, 255))
            y += size * 1.3
        _pill(d, (70, 610), b["name"], 40, (15, 15, 15) if i != 2 else (15, 15, 15), bar if i != 3 else acc)
        p = out_dir / f"thumb_{i}.jpg"
        img.convert("RGB").save(p, "JPEG", quality=92)
        paths.append(p)
    return paths


def _ff(args, threads, timeout=3600):
    cmd = ["nice", "-n", "15", "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", str(threads)] + args
    try:                                             # v2.1.9: atka ffmpeg kabhi ghanto nahi (v2.3.0: nice 15, v11 jaisa)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError("ffmpeg 60 min mein khatam nahi hua - roka (atka tha)")
    if r.returncode != 0:
        tail = (r.stderr or "").strip()[-800:] or f"exit {r.returncode} (shayad RAM khatam / -9 = OOM)"   # v2.7.4: khaali galti nahi
        raise RuntimeError("ffmpeg: " + tail)


def render(script: dict, notify=None) -> dict:
    """script = {brand, title, scenes:[{show, say}], page, description}"""
    t0 = time.time()
    brand = script["brand"]
    job = TMP / f"{brand}-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
    job.mkdir(parents=True)
    scenes = script["scenes"]
    W, H = (1920, 1080) if script.get("format") == "long" else (globals()["W"], globals()["H"])
    parts = []
    try:
        XF = 0.15 if script.get("design") == "neon_quiz" else 0.4    # v2.7.3: neon mein do text ek saath dhundhle na dikhein
        SS = 2 if W > H else 3        # super-sample zoom: kaanpna nahi
        durs, wavs, bodies = [], [], []
        phs, clips = script.get("photos") or [], script.get("clips") or []
        if script.get("design") == "neon_quiz" and script.get("layout") in ("light3", "versus", "exam"):
            phs, clips = [], []                   # v2.9.4: safed/comic/exam card par AI photo nahi - apna saaf parat (pehle kaala dikhta tha)
        for i, sc in enumerate(scenes):
            wait_until_ok(notify)
            wav = job / f"s{i}.wav"
            try:                                   # v2.3.0 Step 3: scene ke hisaab se awaaz (tts naya ho to)
                durs.append(tts.synth(sc.get("say") or sc["show"], str(wav), scene_idx=i, total_scenes=len(scenes),
                                      hold=float(sc.get("hold") or 0)))
            except TypeError:
                durs.append(tts.synth(sc.get("say") or sc["show"], str(wav)))
            wavs.append(wav)
            png = job / f"b{i}.png"
            if script.get("design") == "neon_quiz" and (W, H) == (1080, 1920):     # v2.3.0: premium neon quiz
                from . import design as _DS
                _DS.body_frame(script, i, len(scenes), png)
            else:
                scene_frame(brand, script["title"], sc["show"], i, len(scenes), png, (W, H), layer="body", hud=script.get("hud"))
            bodies.append(png)
            log(f"scene {i + 1}/{len(scenes)} awaaz ok ({durs[-1]:.1f}s)")
        total = sum(durs) + 0.6
        chrome = job / "chrome.png"
        if script.get("design") == "neon_quiz" and (W, H) == (1080, 1920):
            Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(chrome)          # design ka apna footer/pill
        else:
            scene_frame(brand, "", "", 0, len(scenes), chrome, (W, H), layer="chrome")
        threads = wait_until_ok(notify)
        # 1) background: ek lagataar video (bina jhatke)
        bgv = job / "bg.mp4"
        enc = ["-c:v", "libx264", "-preset", PRESET, "-crf", str(CRF), "-profile:v", "high", "-pix_fmt", "yuv420p"]
        if clips or phs:          # aapki video/photo: har scene ka apna bg, aapas mein naram crossfade
            seg = []
            for i, d_ in enumerate(durs):
                ln = d_ + (XF if i < len(durs) - 1 else 0.6)
                fr = max(2, int(round(ln * FPS)))
                o = job / f"g{i}.mp4"
                if clips:
                    _ff(["-stream_loop", "-1", "-i", clips[i % len(clips)], "-vf",
                         f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},"
                         f"eq=saturation=1.1:brightness=-0.06", "-frames:v", str(fr), "-an"] + enc + [str(o)], threads)
                else:
                    gp = job / f"gp{i}.png"
                    _pb = _photo_bg(phs[i % len(phs)], W, H, BRANDS[brand])
                    if script.get("design") == "neon_quiz":   # v2.4.2: AI chitra ke andar ka likha (jaise '5000') na padha jaaye
                        from PIL import ImageEnhance as _IE
                        _pb = _IE.Brightness(_pb.convert("RGB").filter(ImageFilter.GaussianBlur(22))).enhance(0.55)
                    _pb.save(gp)
                    _ff(["-i", str(gp), "-vf", f"scale={W * SS}:-2:flags=lanczos,zoompan=z='1+0.04*on/{fr}':"
                         f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={W}x{H}:fps={FPS}",
                         "-frames:v", str(fr)] + enc + [str(o)], threads)
                seg.append(o)
            ins, fc, last, off = [], [], "0:v", 0.0
            for o in seg:
                ins += ["-i", str(o)]
            for i in range(1, len(seg)):
                off += durs[i - 1]
                fc.append(f"[{last}][{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}]")
                last = f"x{i}"
            _ff(ins + (["-filter_complex", ";".join(fc), "-map", f"[{last}]"] if fc else []) + enc + [str(bgv)], threads)
        else:                     # rang wala background: poori video mein ek hi dheema zoom
            gp = job / "bg.png"
            vs = script.get("visual_style") or ("puzzle_grid" if script.get("puzzle_kind") else "")
            if script.get("design") == "neon_quiz" and (W, H) == (1080, 1920):
                from . import design as _DS
                _DS.use_palette(script.get("palette"))   # v2.3.6: namoona/rotation ka rang
                _DS.use_layout(script.get("layout"))     # v2.4.0: layout bhi
                _DS.background(brand, script.get("title", ""), gp)
                if script.get("img3d") and script.get("layout") not in ("light3", "versus"):               # v2.3.3: peeche apna 3D (dhundhla, andhera) - upar wahi 3D saaf khidki mein
                    try:
                        _DS.blend_3d_bg(gp, script["img3d"])
                    except Exception as e:
                        log(f"3d bg: {e}")
            elif vs and vs != "classic":            # v2.3.0 Step 2 (v11 se): 9 viral style - Studio mein pakka look se
                try:
                    from . import imagegen as _IG
                    _IG.procedural_scene(brand, vs, 0, f"{script.get('title', '')} {scenes[0].get('show', '')}", gp)
                    if W != 1080 or H != 1920:
                        Image.open(gp).resize((W, H), Image.LANCZOS).save(gp)
                except Exception as e:
                    log(f"visual style {vs}: {e}")
                    bg_image(brand, W, H, gp)
            else:                                   # purana (classic) - default, jab tak Studio mein naya pakka na ho
                bg_image(brand, W, H, gp)
            fr = int(round(total * FPS))
            _ff(["-i", str(gp), "-vf", f"scale={W * SS}:-2:flags=lanczos,zoompan=z='1+0.06*on/{fr}':"
                 f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={W}x{H}:fps={FPS}",
                 "-frames:v", str(fr)] + enc + [str(bgv)], threads)
        # 2) awaaz
        audio = job / "voice.wav"
        (job / "alist.txt").write_text("".join(f"file '{w.name}'\n" for w in wavs))
        _ff(["-f", "concat", "-safe", "0", "-i", str(job / "alist.txt"), "-af", "apad=pad_dur=0.6", "-ar", "48000",
             "-ac", "2", str(audio)], 1)
        # 3) upar: brand/site sthir + har scene ka text naram fade-in/fade-out
        # v2.3.0 Step 2 (v11 se): 8 se zyada scene (lambi video) -> 6-6 ke batch (RAM 5.6 GB wala atkaav khatam).
        # Shorts (4-8 scene) pehle jaisa ek hi pass (quality waisi hi).
        BATCH = 6 if len(bodies) > 8 else len(bodies)
        cur_vid = bgv
        st = 0.0
        joined = job / "joined.mp4"
        for b_start in range(0, len(bodies), BATCH):
            b_bodies = bodies[b_start:b_start + BATCH]
            b_durs = durs[b_start:b_start + BATCH]
            first, lastb = b_start == 0, b_start + BATCH >= len(bodies)
            ins = ["-i", str(cur_vid)]
            fc, last, in_idx = [], "0:v", 1
            if first:
                ins += ["-loop", "1", "-i", str(chrome)]
                fc.append("[0:v][1:v]overlay=0:0:shortest=1[c0]")
                last, in_idx = "c0", 2
            for j_i, (pth, d_) in enumerate(zip(b_bodies, b_durs)):
                i = b_start + j_i
                ln = d_ + (XF if i < len(durs) - 1 else 0.6)
                ins += ["-loop", "1", "-t", f"{ln:.3f}", "-i", str(pth)]
                fin = 0.01 if i == 0 else XF
                fc.append(f"[{in_idx}:v]format=rgba,fade=t=in:st=0:d={fin}:alpha=1,"
                          f"fade=t=out:st={max(0.0, ln - XF):.3f}:d={XF}:alpha=1,setpts=PTS+{st:.3f}/TB[t{i}]")
                fc.append(f"[{last}][t{i}]overlay=0:0:eof_action=pass[c{i + 1}]")
                last = f"c{i + 1}"
                in_idx += 1
                st += d_
            if lastb:
                _ff(ins + ["-i", str(audio), "-filter_complex", ";".join(fc), "-map", f"[{last}]",
                           "-map", f"{in_idx}:a", "-t", f"{total:.3f}", "-r", str(FPS)] + enc +
                    ["-c:a", "aac", "-b:a", AUDIO_BITRATE, str(joined)], wait_until_ok(notify))
            else:
                step_out = job / f"step_{b_start}.mp4"
                _ff(ins + ["-filter_complex", ";".join(fc), "-map", f"[{last}]", "-t", f"{total:.3f}",
                           "-r", str(FPS), "-an"] + enc + [str(step_out)], wait_until_ok(notify), timeout=1800)
                cur_vid = step_out
        if (script.get("design") == "neon_quiz" and (W, H) == (1080, 1920) and script.get("karaoke", True)
                and _karaoke_on()):
            try:                                   # v2.9.0: karaoke subtitle (fail = bina subtitle, video nahi rukti)
                from . import karaoke as _KR
                kdir = job / "kara"
                kdir.mkdir()
                pat, _n = _KR.make_sequence(scenes, durs, str(kdir), total, W)
                kara = job / "joined_k.mp4"
                _ff(["-i", str(joined), "-framerate", str(_KR.FPS), "-i", pat, "-filter_complex",
                     f"[1:v]format=rgba[k];[0:v][k]overlay=0:{_KR.Y}:eof_action=pass:shortest=0[v]", "-map", "[v]", "-map", "0:a",
                     "-t", f"{total:.3f}", "-r", str(FPS)] + enc + ["-c:a", "copy", str(kara)], wait_until_ok(notify))
                joined = kara
            except Exception as e:
                log(f"karaoke chhoda: {str(e)[:200]}")
        out_dir = STOCK / job.name
        out_dir.mkdir(parents=True)
        final = out_dir / "video.mp4"
        _ff(["-i", str(joined), "-c:v", "copy", "-af", LOUDNESS, "-c:a", "aac", "-b:a", AUDIO_BITRATE,
             "-ar", "48000", "-movflags", "+faststart", str(final)], wait_until_ok(notify))
        from .thumbs import make as make_thumbs
        thumb = script.get("thumb") or {"lines": [script.get("thumb_title") or script["title"]], "emoji": "🤔"}
        try:
            if script.get("design") == "neon_quiz":          # v2.3.0: neon quiz thumbnail (3 rang)
                from . import design as _DS
                thumbs = [pathlib.Path(_DS.thumbnail(script, out_dir / f"thumb_{k}.jpg", k)) for k in range(3)]
            else:
                thumbs = make_thumbs(brand, thumb, out_dir, script["title"])
        except Exception as e:                     # v2.3.0 (v11 se): naya thumbnail fail -> purana tareeka
            log(f"thumbs: {e}")
            thumbs = thumbnails(brand, script["title"], out_dir)
        meta = dict(script, video=str(final), thumbs=[str(p) for p in thumbs],
                    scene_starts=[round(sum(durs[:k]), 2) for k in range(len(durs))],      # v2.7.0: asli chapters ke liye
                    render_sec=round(time.time() - t0, 1), duration=probe_duration(final))
        (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
        log(f"VIDEO OK {final} {meta['duration']:.1f}s, {meta['render_sec']}s mein bani")
        return meta
    finally:
        shutil.rmtree(job, ignore_errors=True)


def _karaoke_on():
    try:
        from . import state as _st
        return _st.get("karaoke_on", True)
    except Exception:
        return True


def probe(path, entries):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", entries, "-of", "json", str(path)],
                       capture_output=True, text=True, timeout=120)
    return json.loads(r.stdout or "{}")


def probe_duration(path) -> float:
    return float(probe(path, "format=duration").get("format", {}).get("duration", 0))


def add_cover(video_path, thumb_path, out_path, dur=0.8, cover_png=None):
    """Shorts mein YouTube/IG/FB apna banaya thumbnail nahi dikhate, pehla frame dikhate hain.
    Isliye chuna hua thumbnail 0.8 second ka 'cover' bana kar video ke shuru mein jod do (sab platform par wahi dikhega)."""
    from PIL import Image, ImageFilter, ImageEnhance
    tmp = pathlib.Path(out_path).parent / "cover_tmp"
    tmp.mkdir(exist_ok=True)
    try:
        if cover_png:
            png = pathlib.Path(cover_png)
            return _cover_concat(png, video_path, out_path, dur, tmp)
        th = Image.open(thumb_path).convert("RGB")
        bg = th.resize((int(1920 * th.width / th.height), 1920)).crop((0, 0, 1080, 1920)) \
            if th.width / th.height < 1080 / 1920 else th.resize((int(th.width * 1920 / th.height), 1920))
        left = (bg.width - 1080) // 2
        bg = bg.crop((left, 0, left + 1080, 1920)).filter(ImageFilter.GaussianBlur(28))
        bg = ImageEnhance.Brightness(bg).enhance(0.55)
        fg = th.resize((1080, int(th.height * 1080 / th.width)))
        bg.paste(fg, (0, (1920 - fg.height) // 2))
        png = tmp / "cover.png"
        bg.save(png)
        return _cover_concat(png, video_path, out_path, dur, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _cover_concat(png, video_path, out_path, dur, tmp):
    if True:
        cover = tmp / "cover.mp4"
        _ff(["-loop", "1", "-framerate", str(FPS), "-i", str(png), "-f", "lavfi", "-i",
             "anullsrc=channel_layout=stereo:sample_rate=48000", "-t", f"{dur}", "-r", str(FPS),
             "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", PRESET, "-crf", str(CRF), "-profile:v", "high",
             "-c:a", "aac", "-b:a", AUDIO_BITRATE, "-ar", "48000", "-ac", "2", "-shortest", str(cover)], 2)
        # ek hi baar poora re-encode (stream-copy jodne se Instagram 'Processing' error deta tha)
        _ff(["-i", str(cover), "-i", str(pathlib.Path(video_path).resolve()), "-filter_complex",
             "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-preset", PRESET, "-crf", str(CRF), "-profile:v", "high", "-pix_fmt", "yuv420p",
             "-r", str(FPS), "-c:a", "aac", "-b:a", AUDIO_BITRATE, "-ar", "48000", "-ac", "2",
             "-movflags", "+faststart", str(out_path)], 2)
        return pathlib.Path(out_path)
