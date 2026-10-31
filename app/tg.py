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


def _backup(text, level="yellow"):
    try:
        from . import backup
        backup.send(text, level)
    except Exception:
        pass


def say(text, kb=None):
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
        return res
    except Exception as e:  # report kabhi kaam na roke
        print("telegram say fail:", e)
        _backup(text)


def video(path, caption="", thumb=None):
    files = {"video": open(path, "rb")}
    if thumb:
        files["thumbnail"] = open(thumb, "rb")
    try:
        return call("sendVideo", {"chat_id": _chat(), "caption": caption[:1000], "supports_streaming": "true",
                                  "width": 1080, "height": 1920}, files, timeout=600)
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
        return res
    except Exception as e:
        print("telegram alert fail:", e)
        _backup(f"{icon} {text}", level)
