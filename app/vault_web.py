"""v2.3.0 Step 1 (v11 se): Emergency Web Command Vault - 127.0.0.1:8099 (SIRF VM ke andar, bahar se kabhi nahi).

Telegram + Cloudflare relay + ntfy - teeno band hon tab aakhri raasta: SSH tunnel se browser mein haal dekhna / chhota hukum.
Suraksha (v11 se zyada): DEFAULT BAND - owner 'vault chalu' + dohri pushti se hi; sirf loopback; lambi random chabi
(secrets/vault_key.txt, 600); har galat chabi par 2 sec ruk; hukum sirf jaankari wale (koi delete/install/deploy nahi).
Trading ports 8001-8003 se alag. Chowkidar ka firewall bhi 8099 ko bahar se nahi kholta.
"""
import hmac
import http.server
import json
import secrets
import threading
import time
import urllib.parse

from . import state
from .config import SECRETS, BASE
from .log import log

KEY_FILE = SECRETS / "vault_key.txt"
PORT = 8099
_STARTED = False
SAFE_CMDS = ("haal", "sab theek?", "🩺 sab theek?", "📊 aaj ka haal", "aaj ka haal", "pending", "⏳ pending", "raasta haal",
             "pause", "⏸ pause", "resume", "▶️ resume", "/panic", "/version", "spare reel", "quota haal", "blindfold")


def get_key():
    if KEY_FILE.exists():
        return KEY_FILE.read_text().strip()
    k = secrets.token_urlsafe(24)
    KEY_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    KEY_FILE.write_text(k)
    KEY_FILE.chmod(0o600)
    return k


def is_on():
    return bool(state.get("vault_on"))


def start_vault(on_cmd_fn):
    """127.0.0.1:8099 par chhota server (daemon thread). Sirf jab owner ne chalu kiya ho."""
    global _STARTED
    if _STARTED or not is_on():
        return False
    _STARTED = True

    class _Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(u.query)
            if not is_on() or not hmac.compare_digest(qs.get("key", [""])[0], get_key()):
                time.sleep(2)
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"403")
                return
            cmd = qs.get("cmd", [""])[0].strip()
            ran = None
            if cmd and cmd.lower() in SAFE_CMDS:
                threading.Thread(target=on_cmd_fn, args=(cmd,), daemon=True).start()
                ran = cmd
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            try:
                ver = (BASE / "VERSION").read_text().strip()
            except Exception:
                ver = "?"
            payload = {"ok": True, "version": ver, "paused": bool(state.get("paused")),
                       "working_on": state.get("working_on") or "idle", "triggered_cmd": ran,
                       "allowed": list(SAFE_CMDS) if cmd and not ran else None}
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _serve():
        try:
            srv = http.server.HTTPServer(("127.0.0.1", PORT), _Handler)
            srv.serve_forever()
        except Exception as e:
            log(f"vault_web port {PORT}: {e}")

    threading.Thread(target=_serve, daemon=True).start()
    return True


def vault_info():
    return ("🔐 EMERGENCY WEB VAULT (127.0.0.1:8099)\n"
            f"• Haal: {'CHALU' if is_on() else 'BAND (default)'} | sirf VM ke andar (bahar se kabhi nahi)\n"
            "• Kab kaam aata hai: Telegram + relay + ntfy teeno band hon. Laptop/Termux se SSH tunnel:\n"
            "  ssh -L 8099:127.0.0.1:8099 ubuntu@<VM>  → browser: http://127.0.0.1:8099/?key=<CHABI>&cmd=haal\n"
            "• Chabi: VM par secrets/vault_key.txt (chat mein kabhi nahi bheji jaati)\n"
            "• Hukum sirf jaankari/pause/resume/panic - koi delete/install/deploy nahi\n"
            "• Chalu/band: likhein 'vault chalu' / 'vault band' (dohri pushti). Chalu karne ke baad bot restart par shuru.")
