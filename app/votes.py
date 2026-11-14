"""v2.8.0 (owner + 5 Nov plan A1/A2): ASLI % ENGINE - /jawab par 'tap karke socho' ke vote ki sirf GINTI.

Niti (pakki):
  - Koi naam/ID/IP/cookie SAVE nahi: Worker sirf 'is code par A/B/C/D kitni baar' ginta hai (KV mein 4 ank).
  - 30 vote se pehle koi % nahi dikhta ('nakli %' kabhi nahi). Ek browser ek sawal par ek hi vote (localStorage, sirf browser mein).
  - Sirf sabhisaab.com se aaya vote (Origin jaanch); code 3-6 ank, option 0-3 - baaki sab mana.
  - Cloudflare free: KV mein din ke 1000 write tak; uske upar vote chupchap nahi gine jaate (page tootta nahi).
Bot khud: Worker banata (owner ke maujooda Cloudflare token se, relay jaisa), site ke _headers (CSP connect-src) mein uska pata
jodta (audit gate), aur /jawab par 'socho phir tap karo' chalu karta. Privacy page mein likhna W10 mein.
"""
import json
import time

from . import state
from .config import SECRETS
from .log import log

CFG = SECRETS / "votes.json"
NAME = "sabhisaab-votes"
MIN_VOTES = 30

JS = r"""
// sabhisaab-votes (v2.8.0) - anonymous vote ginti. Koi IP/naam/cookie save nahi. Sirf sabhisaab.com se.
const OK_ORIGINS = ['https://sabhisaab.com', 'https://www.sabhisaab.com'];
function cors(origin) {
  const o = OK_ORIGINS.includes(origin) ? origin : OK_ORIGINS[0];
  return {'Access-Control-Allow-Origin': o, 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin'};
}
function j(body, origin, extra) {
  return new Response(JSON.stringify(body), {headers: Object.assign({'Content-Type': 'application/json'}, cors(origin), extra || {})});
}
export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const origin = req.headers.get('Origin') || '';
    if (req.method === 'OPTIONS') return new Response(null, {headers: cors(origin)});
    if (url.pathname === '/v' && req.method === 'POST') {
      if (!OK_ORIGINS.includes(origin)) return j({ok: false}, origin);
      const c = url.searchParams.get('c') || '', o = parseInt(url.searchParams.get('o') || '-1', 10);
      if (!/^\d{3,6}$/.test(c) || !(o >= 0 && o <= 3)) return j({ok: false}, origin);
      try {
        const raw = await env.KV.get('v:' + c);
        const a = raw ? JSON.parse(raw) : [0, 0, 0, 0];
        a[o] = (a[o] || 0) + 1;
        await env.KV.put('v:' + c, JSON.stringify(a));
        return j({ok: true}, origin);
      } catch (e) { return j({ok: false}, origin); }
    }
    if (url.pathname === '/p') {
      const codes = (url.searchParams.get('c') || '').split(',').filter(x => /^\d{3,6}$/.test(x)).slice(0, 60);
      const out = {};
      for (const c of codes) {
        const raw = await env.KV.get('v:' + c);
        if (raw) { const a = JSON.parse(raw); const n = a.reduce((s, x) => s + x, 0); if (n >= %MIN%) out[c] = a; }
      }
      return j(out, origin, {'Cache-Control': 'public, max-age=300'});
    }
    return new Response('ok', {headers: cors(origin)});
  }
};
""".replace("%MIN%", str(MIN_VOTES))


def cfg():
    try:
        return json.loads(CFG.read_text())
    except Exception:
        return {}


def url():
    return cfg().get("url") or ""


def deploy():
    """Worker + KV banao/naya karo (dobara chalana surakshit). -> url"""
    from . import relay
    tok, acc = relay._creds()
    c = cfg()
    if not c.get("kv"):
        for ns in relay._api("GET", f"/accounts/{acc}/storage/kv/namespaces", tok, params={"per_page": 100}) or []:
            if ns.get("title") == NAME:
                c["kv"] = ns["id"]
        if not c.get("kv"):
            c["kv"] = relay._api("POST", f"/accounts/{acc}/storage/kv/namespaces", tok, json={"title": NAME})["id"]
    sub = relay._subdomain(tok, acc)
    meta = {"main_module": "worker.js", "compatibility_date": "2024-09-23",
            "bindings": [{"type": "kv_namespace", "name": "KV", "namespace_id": c["kv"]}]}
    files = {"metadata": (None, json.dumps(meta), "application/json"),
             "worker.js": ("worker.js", JS.encode(), "application/javascript+module")}
    relay._api("PUT", f"/accounts/{acc}/workers/scripts/{NAME}", tok, files=files)
    try:
        relay._api("POST", f"/accounts/{acc}/workers/scripts/{NAME}/subdomain", tok, json={"enabled": True})
    except Exception as e:
        log(f"votes workers.dev on: {e}")
    c["url"] = f"https://{NAME}.{sub}.workers.dev"
    c["made"] = time.time()
    CFG.write_text(json.dumps(c))
    CFG.chmod(0o600)
    return c["url"]


def csp_with(headers_text, origin):
    """site/_headers ki Content-Security-Policy connect-src mein worker ka pata (pehle se ho to waisa hi). -> naya text ya None"""
    if not origin or origin in headers_text:
        return None
    lines = headers_text.splitlines()
    for i, ln in enumerate(lines):
        if "Content-Security-Policy:" in ln and "connect-src" in ln:
            lines[i] = ln.replace("connect-src 'self'", f"connect-src 'self' {origin}", 1)
            return "\n".join(lines) + ("\n" if headers_text.endswith("\n") else "")
    return None


def setup():
    """Ek baar: Worker banao -> site CSP mein jodo (audit gate) -> /jawab par tap-vote chalu. -> owner ke liye text"""
    from . import website
    import zipfile
    from .config import DATA
    try:
        u = deploy()
    except Exception as e:
        return f"❌ Vote counter nahi bana: {str(e)[:200]}\n(Cloudflare token mein 'Workers Scripts Edit' + 'Workers KV Storage Edit' chahiye)"
    try:
        website.sync()
    except Exception as e:
        log(f"votes sync: {e}")
    f = website.DIR / "site" / "_headers"
    new = csp_with(f.read_text(encoding="utf-8"), u) if f.exists() else None
    if new:
        z = DATA / "votes_csp.zip"
        with zipfile.ZipFile(z, "w") as zz:
            zz.writestr("site/_headers", new)
        r = website.apply_zip(z, force=False)
        z.unlink(missing_ok=True)
        if not str(r).startswith("✅"):
            return f"⚠️ Counter bana ({u}) par site ki CSP audit mein ruki: {str(r)[:200]}"
    state.put("votes_on", True)
    state.put("answer_dirty", True)             # /jawab dobara bane (tap-vote ke saath)
    return (f"✅ Asli % engine chalu: {u}\n• /jawab par har sawal: pehle socho, phir A/B/C/D tap - tabhi sahi jawab dikhega\n"
            f"• {MIN_VOTES} vote ke baad hi '% ne kya chuna' (nakli % kabhi nahi)\n• Koi naam/IP save nahi - sirf ginti")
