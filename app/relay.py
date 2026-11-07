"""v2.0.7: Telegram ka DOOSRA raasta + VM ke bina chowkidaar (Cloudflare Worker, free).

Kyun: 29 Oct 2026 ko VM (Oracle) se api.telegram.org ka raasta beech ke network par toot gaya (Google/GitHub chal rahe the).
Dono bot chup ho gaye. Ab:
  1) tg.py pehle seedha Telegram aazmata hai; 8 second mein na jude to Cloudflare Worker ke raaste (yahi relay).
  2) Worker har 10 min VM ki dhadkan (beat) dekhta hai. 30 min se dhadkan nahi = VM band/atka -> Cloudflare se hi
     owner ko Telegram + ntfy par khabar (VM ke bina).
  3) Chowkidar/trading service sirf PADHE jaate hain (systemctl is-active) - kabhi chhede nahi jaate.
Secret: relay ka key + bot token sirf owner ke apne Cloudflare account ke 'secret' mein (chat/GitHub par kabhi nahi).
"""
import json
import secrets
import subprocess
import time
import requests
from . import state
from .config import SECRETS
from .log import log

CFG = SECRETS / "relay.json"
NAME = "sabhinet-relay"
CF = "https://api.cloudflare.com/client/v4"
WATCH = ["chowkidar", "nifty-live", "delta-live", "nifty-chart"]     # sirf padhna (is-active), kabhi restart nahi
DEAD_MIN = 30

JS = r"""
// sabhinet-relay (v2.0.7) - Telegram ka doosra raasta + VM chowkidaar. Sirf api.telegram.org tak, sirf sahi key se.
const TG = 'https://api.telegram.org/';
async function tell(env, text) {
  try {
    await fetch(TG + 'bot' + env.TG_TOKEN + '/sendMessage', {method: 'POST',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify({chat_id: env.TG_CHAT, text: text, disable_web_page_preview: true})});
  } catch (e) {}
  if (env.NTFY_TOPIC) {
    try {
      await fetch('https://ntfy.sh/' + env.NTFY_TOPIC, {method: 'POST', body: text,
        headers: {'Title': 'Sabhisaab VM', 'Priority': '5', 'Tags': 'rotating_light'}});
    } catch (e) {}
  }
}
export default {
  async fetch(req, env) {
    const u = new URL(req.url);
    const p = u.pathname.split('/');
    if (!env.RELAY_KEY || p[1] !== env.RELAY_KEY) return new Response('not found', {status: 404});
    const rest = p.slice(2).join('/');
    if (rest === 'ping') return new Response('ok');
    if (rest === 'beat' && req.method === 'POST') {
      const info = (await req.text()).slice(0, 1500);
      await env.KV.put('beat', JSON.stringify({t: Date.now(), info: info}));
      return new Response('ok');
    }
    if (!/^(bot|file\/bot)\d+:[A-Za-z0-9_-]+\/[A-Za-z0-9_.\/-]+$/.test(rest)) return new Response('bad path', {status: 400});
    const h = new Headers();
    const ct = req.headers.get('content-type');
    if (ct) h.set('content-type', ct);
    const init = {method: req.method, headers: h};
    if (req.method !== 'GET' && req.method !== 'HEAD') init.body = req.body;
    const r = await fetch(TG + rest + u.search, init);
    return new Response(r.body, {status: r.status,
      headers: {'content-type': r.headers.get('content-type') || 'application/json', 'x-sn-relay': '1'}});
  },
  async scheduled(ev, env, ctx) {
    const raw = await env.KV.get('beat');
    if (!raw) return;
    const b = JSON.parse(raw);
    const gap = Math.round((Date.now() - b.t) / 60000);
    const told = await env.KV.get('told');
    if (gap > __DEAD__ && told !== String(b.t)) {
      await env.KV.put('told', String(b.t));
      await tell(env, '\u{1F534} ZAROORI (Cloudflare chowkidaar, VM ke bina): VM / Sabhisaab bot se ' + gap +
        ' min se koi khabar nahi.\nKya karein: cloud.oracle.com \u2192 Compute \u2192 Instances \u2192 nifty-a1 \u2192 State dekhein. ' +
        'Stopped ho to Start. Running ho to 10 min ruk kar bhi chup rahe to Reboot (Force nahi). Terminate KABHI nahi.');
    } else if (gap <= __DEAD__ && told && told !== 'ok' && told !== String(b.t)) {
      await env.KV.put('told', 'ok');
      await tell(env, '\u2705 VM / Sabhisaab bot wapas khabar de raha hai (Cloudflare chowkidaar).');
    }
  }
};
""".replace("__DEAD__", str(DEAD_MIN))


def cfg():
    try:
        return json.loads(CFG.read_text())
    except Exception:
        return {}


def _save(c):
    CFG.write_text(json.dumps(c))
    CFG.chmod(0o600)


def base():
    """Telegram ke liye relay ka pata (url/key) - tabhi jab Worker ban chuka ho."""
    c = cfg()
    if c.get("url") and c.get("key"):
        return f"{c['url'].rstrip('/')}/{c['key']}"
    return None


def ok():
    return bool(cfg().get("live"))


def _creds():
    from .website import _cf
    tok, acc = _cf()
    if not (tok and acc):
        raise RuntimeError("Cloudflare token/account VM par nahi ('cf token <token>' aur 'cf account <id>' bot ko bhejein)")
    return tok, acc


def _api(method, path, tok, **kw):
    r = requests.request(method, CF + path, headers={"Authorization": f"Bearer {tok}"}, timeout=60, **kw)
    try:
        j = r.json()
    except Exception:
        raise RuntimeError(f"Cloudflare {r.status_code}: {r.text[:150]}")
    if not j.get("success"):
        errs = "; ".join(f"{e.get('code')}: {e.get('message')}" for e in j.get("errors", []))
        raise RuntimeError(f"Cloudflare {path.split('/')[-1]}: {errs or r.status_code}")
    return j.get("result")


def _kv(tok, acc, c):
    if c.get("kv"):
        return c["kv"]
    for ns in _api("GET", f"/accounts/{acc}/storage/kv/namespaces", tok, params={"per_page": 100}) or []:
        if ns.get("title") == NAME:
            return ns["id"]
    return _api("POST", f"/accounts/{acc}/storage/kv/namespaces", tok, json={"title": NAME})["id"]


def _subdomain(tok, acc):
    try:
        sub = (_api("GET", f"/accounts/{acc}/workers/subdomain", tok) or {}).get("subdomain")
        if sub:
            return sub
    except Exception as e:
        log(f"relay subdomain get: {e}")
    want = "sabhisaab-" + secrets.token_hex(3)
    return _api("PUT", f"/accounts/{acc}/workers/subdomain", tok, json={"subdomain": want})["subdomain"]


def deploy():
    """Cloudflare par Worker banao/naya karo. Dobara chalana surakshit (wahi key, wahi KV)."""
    from . import tg, backup
    tok, acc = _creds()
    c = cfg()
    c.setdefault("key", secrets.token_urlsafe(24))
    c["kv"] = _kv(tok, acc, c)
    sub = _subdomain(tok, acc)
    meta = {"main_module": "worker.js", "compatibility_date": "2024-09-23", "bindings": [
        {"type": "secret_text", "name": "RELAY_KEY", "text": c["key"]},
        {"type": "secret_text", "name": "TG_TOKEN", "text": tg._tok()},
        {"type": "plain_text", "name": "TG_CHAT", "text": str(tg._chat())},
        {"type": "plain_text", "name": "NTFY_TOPIC", "text": backup.topics().get("alert", "")},
        {"type": "kv_namespace", "name": "KV", "namespace_id": c["kv"]}]}
    files = {"metadata": (None, json.dumps(meta), "application/json"),
             "worker.js": ("worker.js", JS.encode(), "application/javascript+module")}
    _api("PUT", f"/accounts/{acc}/workers/scripts/{NAME}", tok, files=files)
    try:
        _api("POST", f"/accounts/{acc}/workers/scripts/{NAME}/subdomain", tok, json={"enabled": True})
    except Exception as e:
        log(f"relay workers.dev on: {e}")
    _api("PUT", f"/accounts/{acc}/workers/scripts/{NAME}/schedules", tok, json=[{"cron": "*/10 * * * *"}])
    c["url"] = f"https://{NAME}.{sub}.workers.dev"
    c["live"] = False
    c["made"] = time.time()
    _save(c)
    return verify(wait=True)


def verify(wait=False):
    """Relay sach mein Telegram tak pahunchata hai? (getMe). Naya workers.dev kuch minute le sakta hai."""
    from . import tg
    c = cfg()
    if not c.get("url"):
        return "📡 Relay abhi bana nahi."
    tries = 8 if wait else 1
    last = ""
    for n in range(tries):
        try:
            r = requests.get(f"{base()}/bot{tg._tok()}/getMe", timeout=(8, 20))
            if r.ok and r.json().get("ok"):
                c["live"] = True
                c["checked"] = time.time()
                _save(c)
                return "✅ Telegram ka doosra raasta (Cloudflare relay) CHALU. Seedha raasta toote to bot khud isse baat karega."
            last = f"{r.status_code} {r.text[:80]}"
        except Exception as e:
            last = str(e)[:100]
        if n < tries - 1:
            time.sleep(20)
    return (f"🟡 Relay bana, par abhi jawab nahi ({last}). Naya Cloudflare pata 5-10 min mein chalu hota hai - "
            "bot khud dobara jaanchega.")


def _active(svc):
    try:
        return subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return "?"


def _ver():
    try:
        from .config import BASE
        return (BASE / "VERSION").read_text().strip()
    except Exception:
        return "?"


def tick():
    """Har 10 min (scheduler se, alag thread): Cloudflare ko dhadkan + doosri service ki sirf jaanch."""
    from . import tg
    st = {s: _active(s) for s in WATCH}
    info = json.dumps({"v": _ver(), "route": tg.route_name(), "svc": st})
    if base():
        try:
            requests.post(f"{base()}/beat", data=info, timeout=(8, 20))
            if not ok():
                tg.say(verify())
        except Exception as e:
            log(f"relay beat: {e}")
    # service watch: 2 baar lagataar band = ek hi khabar; wapas chalu = ek khabar
    seen = state.get("svc_watch") or {}
    for s, v in st.items():
        prev = seen.get(s, {"bad": 0, "told": False})
        if v != "active":
            prev["bad"] += 1
            if prev["bad"] >= 2 and not prev["told"]:
                prev["told"] = True
                tg.alert("red", f"Service '{s}' {v} hai (20 min se). Bot ise chhedta nahi - VM bot/Chowkidar ya laptop se "
                                f"dekhein: systemctl status {s}")
        else:
            if prev.get("told"):
                tg.alert("green", f"Service '{s}' wapas active.")
            prev = {"bad": 0, "told": False}
        seen[s] = prev
    state.put("svc_watch", seen)


def auto():
    """CF token + account aate hi (ya har 6 ghante, jab tak na bane) relay khud banao."""
    from . import tg
    try:
        _creds()
    except Exception:
        return
    if cfg().get("live"):
        return
    if time.time() - (state.get("relay_try_at") or 0) < 6 * 3600:
        return
    state.put("relay_try_at", time.time())
    try:
        tg.say("📡 " + deploy())
    except Exception as e:
        tg.alert("yellow", f"Telegram ka doosra raasta (Cloudflare relay) nahi bana: {str(e)[:250]}\n"
                           "Token mein ye ijaazat chahiye: Workers Scripts Edit, Workers KV Storage Edit, Account Settings Read.")


def status_text():
    from . import tg, backup
    c = cfg()
    lines = ["📡 Telegram ke raaste"]
    lines.append(f"• Abhi chal raha: {tg.route_name()}")
    lines.append("• Cloudflare relay: " + ("✅ chalu" if c.get("live") else ("🟡 bana, jaanch baaki" if c.get("url") else
                                                                           "❌ nahi bana (cf token + cf account chahiye)")))
    lines.append("• VM chowkidaar (Cloudflare, VM ke bina): " + ("✅ har 10 min" if c.get("live") else "❌ relay ke saath banega"))
    lines.append("• Backup app ntfy: " + ("✅ judi" if state.get("ntfy_ok") else "🔑 'backup setup' likhein"))
    lines.append("• Service jaanch: " + ", ".join(f"{s} {'✅' if _active(s) == 'active' else '🔴'}" for s in WATCH))
    lines.append("Trading/Chowkidar ko bot sirf padhta hai, kabhi chhedta nahi.")
    return "\n".join(lines)
