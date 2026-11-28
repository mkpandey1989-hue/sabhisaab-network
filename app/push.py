"""v2.9.2 (owner: OneSignal): WEBSITE NOTIFICATION - sirf jo khud 'haan' kare (opt-in), roz MAX 1 ('aaj ka sawal').
Niti: pehli visit par popup nahi (shaant button '/jawab' aur homepage par), privacy page mein OneSignal ka ullekh (W11), koi
niji data hamare paas nahi (subscription OneSignal rakhta hai), 'band' karna browser se. Key VM par secrets mein, chat se mitti hai.
"""
import json
import re
import time

import requests

from . import state
from .config import SECRETS, SITE
from .log import log

CFG = SECRETS / "onesignal.json"
WORKER = 'importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js");\n'
CSP_ADD = {"script-src": "https://cdn.onesignal.com", "connect-src": "https://onesignal.com https://api.onesignal.com https://cdn.onesignal.com",
           "style-src": "https://onesignal.com", "img-src": "https://onesignal.com"}


def cfg():
    try:
        return json.loads(CFG.read_text())
    except Exception:
        return {}


def parse(text):
    """'onesignal <app_id> <key>' -> (app_id, key) ya None"""
    m = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", text or "", re.I)
    k = re.search(r"\b(os_v2_app_[A-Za-z0-9_\-]{20,}|[A-Za-z0-9]{40,60})\b", (text or "").replace(m.group(1) if m else "", " "))
    return (m.group(1).lower(), k.group(1)) if m and k else None


def save(app_id, key):
    CFG.write_text(json.dumps({"app_id": app_id, "key": key, "t": time.time()}))
    CFG.chmod(0o600)


def csp_patch(headers_text):
    """'/*' wale CSP mein OneSignal ke domain (pehle se ho to waisa hi). -> naya text ya None"""
    if "cdn.onesignal.com" in headers_text:
        return None
    lines = headers_text.splitlines()
    done = False
    for i, ln in enumerate(lines):
        if "Content-Security-Policy:" in ln and not ln.strip().startswith("!") and "ampproject" not in ln:
            for d, add in CSP_ADD.items():
                if f"{d} " in ln:
                    ln = re.sub(rf"({d} [^;]*)", lambda m_: m_.group(1) + " " + add, ln, count=1)
            if "worker-src" not in ln:
                ln = ln.rstrip().rstrip(";") + "; worker-src 'self'"
            lines[i] = ln
            done = True
            break
    return ("\n".join(lines) + ("\n" if headers_text.endswith("\n") else "")) if done else None


def site_js(app_id):
    """install-app.js mein jodne wala chhota hissa: '🔔 Roz ka sawal' button - dabane par hi OneSignal load (opt-in)."""
    return ("\n  // v2.9.2: notification - sirf button dabane par (koi popup nahi). OneSignal subscription unke paas, hamare paas kuch nahi.\n"
            "  try { var bt0 = document.getElementById('shJawabList') || document.getElementById('jwStreak');\n"
            "    if (bt0 && !document.getElementById('shPush')) { var pb = document.createElement('button'); pb.id = 'shPush';\n"
            "      pb.type = 'button'; pb.textContent = '🔔 Roz ka naya sawal notification par'; pb.style.cssText = 'margin:8px 0;padding:8px 14px;"
            "border-radius:999px;border:1px solid #0F766E;background:#fff;color:#0F766E;cursor:pointer;font-size:.9rem';\n"
            "      bt0.parentNode.insertBefore(pb, bt0.nextSibling);\n"
            "      pb.addEventListener('click', function () { var s = document.createElement('script');\n"
            "        s.src = 'https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js'; s.defer = true;\n"
            "        window.OneSignalDeferred = window.OneSignalDeferred || [];\n"
            f"        OneSignalDeferred.push(function (OS) {{ OS.init({{ appId: '{app_id}' }}).then(function () {{\n"
            "          return OS.Notifications.requestPermission(); }).then(function () { pb.textContent = '✅ Notification chalu (band: browser setting)'; }); });\n"
            "        document.head.appendChild(s); }); } } catch (e) {}\n")


def setup():
    """Keys mile -> site par worker file + CSP + install-app.js button (audit gate). -> owner text"""
    import zipfile
    from . import website
    from .config import DATA
    c = cfg()
    if not c.get("app_id"):
        return "🔑 Pehle bhejein: onesignal <App ID> <API key>"
    try:
        website.sync()
    except Exception as e:
        log(f"push sync: {e}")
    site = website.DIR / "site"
    files = {"site/OneSignalSDKWorker.js": WORKER}
    hdr = site / "_headers"
    if hdr.exists():
        nh = csp_patch(hdr.read_text(encoding="utf-8"))
        if nh:
            files["site/_headers"] = nh
    js = site / "install-app.js"
    if js.exists():
        t = js.read_text(encoding="utf-8")
        if "shPush" not in t:
            anchor = "  // Pehle se app-mode me chal raha hai? To button ki zaroorat nahi."
            if anchor in t:
                files["site/install-app.js"] = t.replace(anchor, site_js(c["app_id"]) + "\n" + anchor, 1)
    z = DATA / "push.zip"
    with zipfile.ZipFile(z, "w") as zz:
        for p, b in files.items():
            zz.writestr(p, b)
    r = website.apply_zip(z, force=False, deploy_in=1)
    z.unlink(missing_ok=True)
    if str(r).startswith("✅"):
        state.put("push_on", True)
        return "✅ Website notification taiyaar: /jawab aur homepage par '🔔 Roz ka naya sawal' button (sirf dabane par). Roz max 1 notification (19:00)."
    return f"⚠️ Website par notification audit mein ruka (kuch live nahi): {str(r)[:200]}"


def send_daily():
    """Roz ek: aaj ka naya sawal (jawab nahi). OneSignal REST."""
    c = cfg()
    if not (c.get("app_id") and c.get("key") and state.get("push_on")):
        return ""
    last = (state.get("answer_key") or [])[-1:]
    if not last:
        return ""
    e = last[0]
    q = re.sub(r"\s+", " ", str(e.get("q", ""))).strip()[:120]
    key = c["key"]
    auth = f"Key {key}" if key.startswith("os_v2_") else f"Basic {key}"
    body = {"app_id": c["app_id"], "target_channel": "push", "included_segments": ["Total Subscriptions"],
            "headings": {"en": "🧩 Aaj ka sawal"}, "contents": {"en": q},
            "url": f"{SITE}/jawab?utm_source=push&utm_medium=notification#c{e.get('aid') or e.get('code')}"}
    try:
        r = requests.post("https://api.onesignal.com/notifications", headers={"Authorization": auth, "Content-Type": "application/json"},
                          json=body, timeout=30)
        return f"🔔 notification: HTTP {r.status_code}"
    except Exception as ex:
        return f"🔔 notification nahi gaya: {str(ex)[:80]}"
