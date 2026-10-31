"""v2.0.7: Telegram POORA band ho tab bhi khabar + chhote hukum - ntfy (free app, bina account, bina token).

- Telegram par bheja message na jaye to wahi text ntfy par (owner ke phone par notification).
- Har ntfy khabar par 3 button (Haal / Sab theek / Resume) - dabate hi hukum bot tak.
- Sirf SURAKSHIT hukum chalte hain (haal, status, pending, pause, resume, vm, raasta). Koi setting/secret nahi.
- Kabhi secret nahi bhejta: lambe token jaise text apne aap [chhupa] ho jaate hain.
Topic naam 24 akshar ke random (secrets/backup.json) - inhe kisi ko na dein.
"""
import json
import re
import secrets
import threading
import time
import requests
from . import state
from .config import SECRETS
from .log import log

NTFY = "https://ntfy.sh"
CFG = SECRETS / "backup.json"
SAFE = {"haal": "📊 Aaj ka haal", "report": "📊 Aaj ka haal", "status": "🩺 Sab theek?", "sab theek": "🩺 Sab theek?",
        "pending": "⏳ Pending", "pause": "⏸ Pause", "resume": "▶️ Resume", "vm": "🖥 VM", "raasta": "raasta haal",
        "menu": "backup menu"}
DAY_CAP = 80                      # ntfy.sh free seema se kaafi neeche
MIRROR = {"until": 0}             # ntfy se hukum aaya to 3 min tak har jawab ntfy par bhi
_LOCK = threading.Lock()


def topics():
    try:
        c = json.loads(CFG.read_text())
    except Exception:
        c = {}
    if not c.get("alert"):
        c = {"alert": "sn-" + secrets.token_hex(12), "cmd": "sn-" + secrets.token_hex(12), "since": str(int(time.time()))}
        CFG.write_text(json.dumps(c))
        CFG.chmod(0o600)
    return c


def _put(c):
    CFG.write_text(json.dumps(c))
    CFG.chmod(0o600)


def _clean(text):
    text = re.sub(r"\d{6,}:[A-Za-z0-9_-]{25,}", "[chhupa]", text)
    return re.sub(r"[A-Za-z0-9_\-]{36,}", "[chhupa]", text)


def _cap_ok():
    day = time.strftime("%Y-%m-%d")
    n = state.get("ntfy_count") or {}
    if n.get("d") != day:
        n = {"d": day, "n": 0}
    if n["n"] >= DAY_CAP:
        return False
    n["n"] += 1
    state.put("ntfy_count", n)
    return True


def send(text, level="yellow", title="Sabhisaab bot"):
    """ntfy par khabar. Kabhi exception nahi uthata (report kaam na roke)."""
    try:
        if not _cap_ok():
            return False
        c = topics()
        cmd = f"{NTFY}/{c['cmd']}"
        acts = "; ".join(f"http, {lbl}, {cmd}, method=POST, body={body}, clear=true"
                         for lbl, body in (("Haal", "haal"), ("Sab theek?", "status"), ("Resume", "resume")))
        pr = {"red": "5", "yellow": "4", "green": "2"}.get(level, "3")
        r = requests.post(f"{NTFY}/{c['alert']}", data=_clean(text)[:3800].encode("utf-8"), timeout=(8, 20),
                          headers={"Title": title, "Priority": pr, "Tags": "robot", "Actions": acts})
        return r.ok
    except Exception as e:
        log(f"ntfy send: {e}")
        return False


def mirror_on():
    return time.time() < MIRROR["until"]


def poll(handler):
    """Alag thread: har 30 sec ntfy ke hukum wale topic ko padho."""
    while True:
        try:
            c = topics()
            r = requests.get(f"{NTFY}/{c['cmd']}/json", params={"poll": "1", "since": c.get("since") or "10m"},
                             timeout=(8, 30))
            last = c.get("since")
            for line in r.text.splitlines():
                try:
                    m = json.loads(line)
                except Exception:
                    continue
                if m.get("event") != "message":
                    continue
                last = m.get("id") or last
                if time.time() - m.get("time", time.time()) > 900:
                    continue                                   # 15 min se purana hukum nahi chalate
                t = (m.get("message") or "").strip().lower()
                state.put("ntfy_ok", True)
                MIRROR["until"] = time.time() + 180
                if t in SAFE:
                    with _LOCK:
                        handler(SAFE[t])
                else:
                    send("Backup raaste par sirf ye hukum chalte hain: " + ", ".join(sorted(SAFE)) +
                         ". Baaki sab Telegram par.", "green")
            if last != c.get("since"):
                c["since"] = last
                _put(c)
        except Exception as e:
            log(f"ntfy poll: {e}")
        time.sleep(30)


def menu_text():
    return ("🆘 Backup raasta (ntfy) chal raha hai. Hukum: haal, status, pending, pause, resume, vm, raasta.\n"
            "Har khabar ke neeche ke button bhi dabaye ja sakte hain.")


def setup_text():
    c = topics()
    cmd = f"{NTFY}/{c['cmd']}/publish?message="
    return ("🆘 Backup khabar (Telegram poora band ho tab bhi) - ek baar ka kaam, 3 minute:\n\n"
            "1) Play Store se app 'ntfy' (by Philipp Heckel) install karein. Account nahi chahiye.\n"
            "2) App kholein → neeche ➕ → Topic name mein ye likhein (copy-paste):\n"
            f"{c['alert']}\n"
            "   'Use another server' KHAALI rehne dein → Subscribe.\n"
            "3) Ab ye link kholein (test hukum jayega, jawab app mein aayega):\n"
            f"{cmd}haal\n\n"
            "Jawab app mein aa gaya to sab tayyar - bot apne aap 'ho gaya' maan lega.\n"
            "Telegram band ho to app ki khabar ke neeche button (Haal / Sab theek? / Resume) dabayein, ya ye link:\n"
            f"• Haal: {cmd}haal\n• Sab theek: {cmd}status\n• Pending: {cmd}pending\n• Pause: {cmd}pause\n"
            f"• Resume: {cmd}resume\n• Telegram raasta: {cmd}raasta\n\n"
            "⚠️ Ye topic naam aur link kisi ko na dein. Inmein koi password/token nahi jaata.")
