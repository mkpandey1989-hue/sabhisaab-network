"""Telegram (seedha HTTP, purane bot jaisa). Token sirf env se."""
import json
import os
import time
import requests

# v2.0: SN_TG_API=http://127.0.0.1:8081 ho to local Bot API server (2 GB tak file). Na ho to Telegram cloud.
BASE = os.environ.get("SN_TG_API", "https://api.telegram.org").rstrip("/")
API = BASE + "/bot{}/{}"
DIRECT = "https://api.telegram.org"
# v2.0.7: kai raaste - local (agar ho) -> seedha Telegram -> Cloudflare relay. 8 sec mein na jude to agla raasta.
_R = {"pref": None, "until": 0, "last": None, "changed": None}
STICK = 600          # jo raasta chala, 10 min usi par; phir seedha raasta dobara aazmao


def _bases():
    out = []
    if BASE != DIRECT:
        out.append(BASE)
    out.append(DIRECT)
    try:
        from . import relay
        rb = relay.base()
        if rb:
            out.append(rb)
    except Exception:
        pass
    p = _R["pref"]
    if p in out and time.time() < _R["until"]:
        out.remove(p)
        out.insert(0, p)
    return out


def _name(b):
    if not b:
        return "-"
    if b == DIRECT:
        return "seedha Telegram"
    if b == BASE:
        return "local Bot API server"
    return "Cloudflare relay"


def route_name():
    return _name(_R["last"]) if _R["last"] else "seedha Telegram"


def route_change():
    """Raasta badla ho to EK baar batane wala sandesh (scheduler bhejta hai)."""
    ch = _R["changed"]
    _R["changed"] = None
    return ch


def _mark(b, first):
    if (_R["last"] and _R["last"] != b) or (not _R["last"] and b != first):
        _R["changed"] = (f"📡 Telegram ka raasta badla: ab '{_name(b)}' se baat ho rahi hai"
                         + (" (seedha raasta band mila)." if b != first else " (seedha raasta wapas)."))
    _R["last"] = b
    if b != first:
        _R["pref"], _R["until"] = b, time.time() + STICK
    elif _R["pref"] and time.time() >= _R["until"]:
        _R["pref"] = None


def _hide(t):
    """Galti ke text mein token / relay key kabhi nahi (log, alert, ntfy)."""
    try:
        t = t.replace(_tok(), "***")
        from . import relay
        k = relay.cfg().get("key")
        if k:
            t = t.replace(k, "***")
    except Exception:
        pass
    return t


def _http(kind, path, timeout, files=None, **kw):
    """Har raasta aazmao. Sirf network/relay ki galti par agla; Telegram ka apna jawab (ok/galti) wahi lauta do."""
    last = None
    bases = _bases()
    first = DIRECT if BASE == DIRECT else BASE
    for b in bases:
        try:
            if files:
                for f in files.values():
                    f.seek(0)
            r = requests.request(kind, b + path, timeout=(8, timeout), files=files, **kw)
            relayed = b not in (DIRECT, BASE)
            if relayed and r.status_code in (400, 404, 500, 502, 503, 504, 520, 522, 524, 530) and \
                    "json" not in r.headers.get("content-type", ""):
                raise requests.ConnectionError(f"relay {r.status_code}")
            _mark(b, first)
            return r, b
        except (requests.ConnectionError, requests.Timeout) as e:
            last = e
            if b == first:
                _R["pref"], _R["until"] = None, 0
    raise requests.ConnectionError(f"saare raaste band ({_hide(str(last))[:150]})")


def _tok():
    t = os.environ.get("LISTENER_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
    if not t:
        raise RuntimeError("Telegram token env mein nahi")
    return t


def _chat():
    return os.environ["OWNER_CHAT_ID"]


def call(method, data=None, files=None, timeout=120, tries=4):
    """Network toote to har baar saare raaste (seedha + Cloudflare relay), phir 10s, 30s, 60s ruk kar."""
    last = None
    for n in range(tries):
        try:
            if data and method in ("sendPhoto", "sendMessage", "sendVideo"):
                try:                               # v2.0.2: public channel post mein ginti/link hamesha sahi
                    from .guardtext import tg_clean
                    data = tg_clean(dict(data))
                except Exception:
                    pass
            r, b = _http("POST", f"/bot{_tok()}/{method}", timeout, files=files, data=data or {})
            j = r.json()
            if j.get("ok"):
                _R["file_base"] = b if method == "getFile" else _R.get("file_base")
                return j["result"]
            if r.status_code == 429:
                time.sleep(int(j.get("parameters", {}).get("retry_after", 30)) + 1)
                continue
            raise RuntimeError(f"Telegram {method}: {j.get('description')}")
        except (requests.ConnectionError, requests.Timeout) as e:
            last = e
            if n < tries - 1:
                time.sleep([10, 30, 60, 60][n])
    raise RuntimeError(f"Telegram {method}: network baar-baar toota ({_hide(str(last))[:200]})")


def _logbot(text):
    try:
        from . import updater
        updater.log_bot(text)
    except Exception:
        pass


def _backup(text, level="yellow"):
    try:
        from . import backup
        backup.send(text, level)
    except Exception:
        pass


def _chunks(text, n=3900):
    """v2.9.8 (owner: 'aadhi-adhuri report, link pura nahi'): 4000 se lamba sandesh line par todkar kai hisson mein - kaata nahi."""
    text = str(text)
    if len(text) <= n:
        return [text]
    out, cur = [], ""
    for line in text.split("\n"):
        while len(line) > n:
            if cur:
                out.append(cur)
                cur = ""
            out.append(line[:n])
            line = line[n:]
        if len(cur) + len(line) + 1 > n:
            out.append(cur)
            cur = line
        else:
            cur = (cur + "\n" + line) if cur else line
    if cur:
        out.append(cur)
    return out


def say(text, kb=None):
    parts = _chunks(text)
    if len(parts) > 1:                             # pehle hisse bina button, aakhri par button
        for k, part in enumerate(parts[:-1]):
            say(f"({k + 1}/{len(parts)})\n" + part)
        return say(f"({len(parts)}/{len(parts)})\n" + parts[-1], kb)
    data = {"chat_id": _chat(), "text": text[:4000], "disable_web_page_preview": "true"}
    if kb:
        data["reply_markup"] = json.dumps(kb)
    try:
        res = call("sendMessage", data, tries=2)
        try:
            from . import backup
            if backup.mirror_on():
                backup.send(text, "green")
        except Exception:
            pass
        _logbot(text)
        return res
    except Exception as e:  # report kabhi kaam na roke
        print("telegram say fail:", e)
        _backup(text)


TG_VIDEO_MAX_MB = 45      # v2.6.0: Telegram cloud Bot API 50 MB se badi file par 413 'Request Entity Too Large' deta hai


def _probe(path):
    """(width, height, seconds) ffprobe se; na mile to (1080, 1920, 0)."""
    import subprocess
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height:format=duration", "-of", "json", str(path)],
                           capture_output=True, text=True, timeout=60)
        j = json.loads(r.stdout or "{}")
        st = (j.get("streams") or [{}])[0]
        return int(st.get("width") or 1080), int(st.get("height") or 1920), float((j.get("format") or {}).get("duration") or 0)
    except Exception:
        return 1080, 1920, 0.0


def _preview(path, max_mb=TG_VIDEO_MAX_MB):
    """Badi video ka chhota preview (sirf Telegram dekhne ke liye). Asli file aur upload ki quality par koi asar nahi."""
    import subprocess
    import tempfile
    w, h, dur = _probe(path)
    if dur <= 0:
        return None
    total_kbps = int(max_mb * 0.92 * 8 * 1024 / dur)        # 8% jagah container/audio ke liye
    a_kbps = 64 if total_kbps > 300 else 32
    v_kbps = max(120, total_kbps - a_kbps)
    short = 480 if v_kbps < 900 else 720
    scale = f"scale=-2:{short}" if w >= h else f"scale={short}:-2"
    out = tempfile.NamedTemporaryFile(suffix="_preview.mp4", delete=False).name
    cmd = ["nice", "-n", "15", "ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-vf", scale,
           "-c:v", "libx264", "-preset", "veryfast", "-b:v", f"{v_kbps}k", "-maxrate", f"{v_kbps}k",
           "-bufsize", f"{v_kbps * 2}k", "-c:a", "aac", "-b:a", f"{a_kbps}k", "-movflags", "+faststart", out]
    try:
        subprocess.run(cmd, check=True, timeout=max(600, int(dur * 3)))
        if os.path.getsize(out) <= max_mb * 1024 * 1024 * 1.08:
            return out
    except Exception:
        pass
    try:
        os.remove(out)
    except Exception:
        pass
    return None


def video(path, caption="", thumb=None, markup=None):
    """v2.6.0: 45 MB se badi video ka apne aap chhota preview (lambi video bhi Telegram par dikh jaye).
    Aakaar asli video se (pehle har video 1080x1920 likha jaata tha - lambi 16:9 video tedhi dikhti thi)."""
    path = str(path)
    tmp = None
    try:
        if os.path.getsize(path) > TG_VIDEO_MAX_MB * 1024 * 1024:
            tmp = _preview(path)
            if not tmp:
                return call("sendMessage", {"chat_id": _chat(), "text": (
                    "🎬 Video bahut badi hai (" + str(os.path.getsize(path) // (1024 * 1024)) + " MB) - Telegram 50 MB se badi file "
                    "nahi leta aur chhota preview bhi nahi ban paya. Video VM par surakshit hai; upload asli quality mein hi hoga.\n\n"
                    + (caption or ""))[:4000]}, timeout=60)
            caption = "🔎 Chhota PREVIEW (Telegram 50 MB seema) - upload asli quality mein hoga.\n" + (caption or "")
            path = tmp
        w, h, _d = _probe(path)
        return _send_video(path, caption, thumb, markup, w, h)
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except Exception:
                pass


def _send_video(path, caption, thumb, markup, w, h):
    files = {"video": open(path, "rb")}
    if thumb:
        files["thumbnail"] = open(thumb, "rb")
    try:
        data = {"chat_id": _chat(), "caption": caption[:1000], "supports_streaming": "true", "width": w, "height": h}
        if markup:                       # v2.5.4: sirf namoona video par ek button (baaki jagah None - purana jaisa)
            data["reply_markup"] = json.dumps(markup)
        return call("sendVideo", data, files, timeout=600)
    finally:
        for f in files.values():
            f.close()


def photos(paths, caption=""):
    media, files = [], {}
    for i, p in enumerate(paths):
        files[f"p{i}"] = open(p, "rb")
        media.append({"type": "photo", "media": f"attach://p{i}", "caption": caption if i == 0 else ""})
    try:
        return call("sendMediaGroup", {"chat_id": _chat(), "media": json.dumps(media)}, files)
    finally:
        for f in files.values():
            f.close()


# ---------------- v0.2: sunna + buttons ----------------
def get_updates(offset, timeout=50):
    try:
        r, b = _http("GET", f"/bot{_tok()}/getUpdates", timeout + 15,
                     params={"offset": offset, "timeout": timeout,
                             "allowed_updates": json.dumps(["message", "callback_query"])})
        j = r.json()
        if j.get("ok"):
            return j["result"]
        if r.status_code == 409:
            raise RuntimeError("Doosra program isi bot ko chala raha hai (ytlistener band karein)")
    except (requests.ConnectionError, requests.Timeout, ValueError):
        time.sleep(5)
    return []


def owner_id():
    return int(_chat())


def answer(cb_id, text=""):
    try:
        call("answerCallbackQuery", {"callback_query_id": cb_id, "text": text[:180]}, tries=1)
    except Exception:
        pass


def delete(chat_id, msg_id):
    try:
        call("deleteMessage", {"chat_id": chat_id, "message_id": msg_id}, tries=1)
    except Exception:
        pass


def download(file_id, dest):
    info = call("getFile", {"file_id": file_id})
    fp = info["file_path"]
    if fp.startswith("/"):                 # local server (--local): file pehle se VM par hai
        import shutil
        shutil.copyfile(fp, dest)
        return dest
    fb = _R.get("file_base") or DIRECT
    if fb == BASE and BASE != DIRECT:
        fb = DIRECT
    url = f"{fb}/file/bot{_tok()}/{fp}"
    with requests.get(url, stream=True, timeout=(8, 120)) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
    return dest


def inline(rows):
    """rows = [[(text, data), ...], ...]"""
    return {"inline_keyboard": [[{"text": t, "callback_data": d[:64]} for t, d in row] for row in rows]}


def reply_keyboard(rows):
    return {"keyboard": [[{"text": t} for t in row] for row in rows], "resize_keyboard": True,
            "is_persistent": True, "input_field_placeholder": "Button dabao ya likho..."}


def set_commands(cmds):
    try:
        call("setMyCommands", {"commands": json.dumps([{"command": c, "description": d} for c, d in cmds])}, tries=1)
    except Exception:
        pass


# ---------------- v0.4: rang wale alert ----------------
def alert(level, text, kb=None):
    """level: red (zaroori, awaaz ke saath) | yellow (dhyan) | green (jaankari, bina awaaz)"""
    import datetime as _d
    icon = {"red": "🔴 ZAROORI", "yellow": "🟡 DHYAN", "green": "🟢"}.get(level, "")
    if not kb and level in ("yellow", "red"):     # v2.3.7: wahi galti baar-baar nahi (3 ghante mein ek baar, ginti yaad)
        try:
            import re as _r
            import time as _t
            from . import state as _st
            key = _r.sub(r"\d+", "#", text)[:120]
            seen = _st.get("alert_seen") or {}
            last = seen.get(key) or {}
            if _t.time() - last.get("t", 0) < 3 * 3600:
                seen[key] = {"t": last.get("t", 0), "n": last.get("n", 1) + 1}
                _st.put("alert_seen", dict(list(seen.items())[-300:]))
                return None
            if last.get("n", 1) > 1:
                text = text + f"\n(pichhle 3 ghante mein ye {last['n']} baar hua)"
            seen[key] = {"t": _t.time(), "n": 1}
            _st.put("alert_seen", dict(list(seen.items())[-300:]))
        except Exception:
            pass
    hr = _d.datetime.now(_d.timezone(_d.timedelta(hours=5, minutes=30))).hour
    quiet = level == "green" or (level == "yellow" and (hr >= 23 or hr < 7))   # raat ko sirf laal alert awaaz ke saath
    data = {"chat_id": _chat(), "text": f"{icon} {text}"[:4000], "disable_web_page_preview": "true",
            "disable_notification": "true" if quiet else "false"}
    if kb:
        data["reply_markup"] = json.dumps(kb)
    try:
        res = call("sendMessage", data, tries=2)
        try:
            from . import backup
            if backup.mirror_on():
                backup.send(f"{icon} {text}", level)
        except Exception:
            pass
        _logbot(f"{icon} {text}")
        return res
    except Exception as e:
        print("telegram alert fail:", e)
        _backup(f"{icon} {text}", level)
