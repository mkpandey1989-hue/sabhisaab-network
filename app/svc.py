"""v3.5.0: Sab Hisaab SERVICES desk (23 Nov 2026, owner ne plan FINAL kiya).

Kya karta hai (purane kaam ko CHHUE bina - alag module, apna on/off 'services band/chalu'):
  1) Cloudflare Worker 'sabhisaab-leads' (free) - website form ka message JSON mein rakhta hai + turant Telegram.
     VM band ho tab bhi lead nahi khota.
  2) VM har 5 min worker se naye lead kheenchta hai -> data/services/leads.jsonl (append-only).
  3) Kaam pehchaan: SIRF rate list ke keyword (Gemini nahi - free tier khatam ho to bhi chalta hai).
  4) Quote: price SIRF svc_rates.json se. Guard: floor se neeche / max se upar = ruk + owner ko alert.
     Har quote ka version (SH..-v1, v2). Owner ✅ ke bina customer tak kuch nahi jaata.
  5) Audit log: har badlav hash-chain mein (pichhli line ka hash agli mein) - koi line mitaye/badle to raat ki jaanch pakad leti.
  6) Referral: REF-code; credit sirf payment ke 7 din baad; same phone = nahi; mahine mein max 5; cash nahi.
  7) Backup: har ghante data/services ki copy (72 ghante), raat ko audit + roz ki report.
  8) Demo ginti: website ke demo par kitne log aaye/ruke/click kiye (worker /ev) - roz report + 'services report'.
Niyam: owner ka naam/QR public kahin nahi; UPI QR sirf private quote mein; koi cold message nahi (sirf jisne form bhara).
"""
import datetime
import hashlib
import json
import re
import secrets
import shutil
import threading
import time

import requests

from . import state
from .config import DATA, SECRETS
from .log import log

NAME = "sabhisaab-leads"
DIR = DATA / "services"
BAK = DATA / "services_bak"
CFG = SECRETS / "svc.json"
RATES_F = __import__("pathlib").Path(__file__).with_name("svc_rates.json")
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
WA_OWNER = "919917436371"
LOCK = threading.Lock()
REF_DAYS = 7
REF_MONTH_CAP = 5
KEEP_LEAD_DAYS = 90


# ---------------------------------------------------------------- files
def _p(name):
    DIR.mkdir(parents=True, exist_ok=True)
    return DIR / name


def _cfg():
    try:
        return json.loads(CFG.read_text())
    except Exception:
        return {}


def _save_cfg(c):
    CFG.parent.mkdir(parents=True, exist_ok=True)
    CFG.write_text(json.dumps(c, indent=1))


def _read(name):
    f = _p(name)
    if not f.exists():
        return []
    out = []
    for ln in f.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out


def _append(name, obj):
    with LOCK:
        with open(_p(name), "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def now():
    return datetime.datetime.now(IST)


# ---------------------------------------------------------------- audit (hash chain)
def audit(action, **kw):
    """Har badlav ki line. h = sha256(pichhla h + ye line) - beech ki line badli to chain tootegi."""
    with LOCK:
        f = _p("audit.jsonl")
        prev = "0"
        if f.exists():
            last = f.read_text(encoding="utf-8").strip().splitlines()[-1:] or ["{}"]
            try:
                prev = json.loads(last[0]).get("h", "0")
            except Exception:
                prev = "broken"
        row = {"t": now().isoformat(timespec="seconds"), "a": action, **kw}
        row["h"] = hashlib.sha256((prev + json.dumps(row, ensure_ascii=False, sort_keys=True)).encode()).hexdigest()[:20]
        with open(f, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def audit_ok():
    prev, n = "0", 0
    for row in _read("audit.jsonl"):
        h = row.pop("h", "")
        if hashlib.sha256((prev + json.dumps(row, ensure_ascii=False, sort_keys=True)).encode()).hexdigest()[:20] != h:
            return False, n
        prev, n = h, n + 1
    return True, n


# ---------------------------------------------------------------- rates
_R = {}


def rates():
    if not _R:
        body = json.loads(RATES_F.read_text(encoding="utf-8"))
        sha = body.pop("sha", "")
        raw = json.dumps(body, ensure_ascii=False, sort_keys=True)
        if hashlib.sha256(raw.encode()).hexdigest()[:16] != sha:
            raise RuntimeError("svc_rates.json ka sha nahi milta - rate list kisi ne badli. Quote ROKE.")
        body["sha"] = sha
        _R.update(body)
        _R["by"] = {i["id"]: i for i in body["items"]}
    return _R


def _words(s):
    return set(re.findall(r"[a-z0-9ऀ-ॿ]+", (s or "").lower()))


def classify(text, picked=""):
    """-> (items[], red_name|None). Picked = form ka chuna hua kaam (sabse bharosemand)."""
    R = rates()
    w = _words(text) | _words(picked)
    low = " " + (text or "").lower() + " "
    for r in R["red"]:
        if any(k in low for k in r["kw"]):
            if not any(i["name"] == picked for i in R["items"]):
                return [], r["name"]
    if picked:
        for i in R["items"]:
            if i["name"] == picked or i["id"] == picked:
                return [i], None
    sc = []
    for i in R["items"]:
        s = len(w & set(i["kw"])) * 2 + len(w & _words(i["name"]))
        if s >= 2:
            sc.append((s, i))
    sc.sort(key=lambda x: -x[0])
    return [i for _, i in sc[:3]], None


def price(item, code="", urgent=False, care=False):
    """Discount niyam rate list se. Guard: floor <= final <= max. Galti par exception (quote nahi banta)."""
    R = rates()
    D = R["discount"]
    p = item["price"]
    off = 0
    code = (code or "").upper().strip()
    if code.startswith("REF-"):
        off += D["ref"]
    elif code in ("LABH10", "NATAK10", "MONEY10", "PAHADI10"):
        off += D["brand"]
    if care and item["cat"] != "care":
        off += D["care"]
    off = min(off, D["max"])
    d = round(p * off / 100)
    if p < D["small_cap_under"]:
        d = min(d, D["small_cap"])
    final = p - d
    if final < item["floor"]:                       # discount se floor ke neeche - floor par roko (nuksan nahi)
        final, d = item["floor"], p - item["floor"]
    if urgent:
        final = round(final * (100 + D["urgent"]) / 100)
    if not (item["floor"] <= final <= item["max"] * 1.5):
        raise ValueError(f"GUARD: {item['id']} final {final} seema ke bahar ({item['floor']}-{item['max']})")
    adv = final if item["cat"] == "micro" else max(item["floor"], round(final * .3))
    return {"base": p, "off_pct": off, "off": d, "final": final, "advance": adv, "floor": item["floor"]}


# ---------------------------------------------------------------- leads
def _clean_phone(s):
    d = re.sub(r"\D", "", s or "")
    if len(d) == 10:
        d = "91" + d
    return d


def leads():
    return {x["id"]: x for x in _read("leads.jsonl") if x.get("id")}


def lead_state(lid):
    st = {}
    for e in _read("events.jsonl"):
        if e.get("id") == lid:
            st.update(e)
    return st


def _event(lid, **kw):
    _append("events.jsonl", {"id": lid, "t": now().isoformat(timespec="seconds"), **kw})
    audit("event", id=lid, **kw)


def ingest(raw):
    """Ek naya lead (worker se). Dohra id = chhod. Quote draft + owner ko button."""
    lid = raw.get("id")
    if not lid or lid in leads():
        return None
    raw["phone"] = _clean_phone(raw.get("phone"))
    _append("leads.jsonl", raw)
    audit("lead", id=lid, src=raw.get("src", ""), code=raw.get("code", ""))
    return draft(lid)


def draft(lid, override=None, note=""):
    from . import tg
    L = leads().get(lid)
    if not L:
        return tg.say(f"❓ {lid} nahi mila")
    items, red = classify(L.get("message", ""), L.get("service", ""))
    ver = int(lead_state(lid).get("ver") or 0) + 1
    head = (f"🛎 KAAM {lid}-v{ver}{' ⚡URGENT' if L.get('urgent') else ''}\n👤 {L.get('name')}  📞 +{L.get('phone')}\n"
            f"💬 {L.get('message', '')[:600]}\n🏷 Code: {L.get('code') or '-'} | Budget: {L.get('budget') or '-'} | Src: {L.get('src') or '-'}")
    if red:
        _event(lid, ver=ver, status="red", red=red)
        return tg.say(head + f"\n\n🔴 Ye kaam NAHI lena: {red}\nCustomer ko vinamra mana + sahi vikalp:",
                      tg.inline([[("📝 Mana ka message", f"sv:no:{lid}")]]))
    if not items and override is None:
        _event(lid, ver=ver, status="manual")
        return tg.say(head + "\n\n🟡 Rate list mein seedha nahi mila (custom). Price likhein:\n"
                      f"'quote {lid} 4999 <kaam ka naam>'")
    it = items[0] if items else {"id": "custom", "cat": "custom", "name": note or "Custom kaam",
                                 "price": override, "floor": max(10, int(override * .6)), "max": override * 2}
    if override is not None:
        it = dict(it, price=int(override), name=note or it["name"])
        it["floor"] = min(it["floor"], it["price"]) if it["id"] != "custom" else it["floor"]
    try:
        q = price(it, L.get("code"), L.get("urgent"), L.get("care"))
    except Exception as e:
        _event(lid, ver=ver, status="guard", err=str(e))
        return tg.say(head + f"\n\n⛔ {e}\nQuote ROKA. Sahi price: 'quote {lid} <rupaye>'")
    q.update({"item": it["id"], "name": it["name"], "days": it.get("days", "baat karke"), "risk": it.get("risk", "G")})
    _event(lid, ver=ver, status="draft", quote=q)
    alt = "\n".join(f"   • {i['name']} ₹{i['price']}" for i in items[1:]) if len(items) > 1 else ""
    risk = "\n🟡 Sharton wala kaam: client ka apna account/server, tip-signal nahi." if q["risk"] == "Y" else ""
    txt = (head + f"\n\n🧾 {q['name']}\n₹{q['base']}" + (f" − ₹{q['off']} ({q['off_pct']}%)" if q["off"] else "") +
           f"{' +50% urgent' if L.get('urgent') else ''} = ₹{q['final']}\nAdvance: ₹{q['advance']} · {q['days']}" + risk +
           (f"\nDoosre mel:\n{alt}" if alt else ""))
    return tg.say(txt, tg.inline([[("✅ Customer ko bhejo", f"sv:ok:{lid}"), ("❌ Mana", f"sv:no:{lid}")]]))


def customer_msg(lid):
    L = leads()[lid]
    st = lead_state(lid)
    q = st.get("quote") or {}
    ref = L.get("ref") or ""
    return (f"Namaste {L.get('name', '')} ji 🙏\nSab Hisaab Services - aapka kaam: {q.get('name')}\n"
            f"Quote no: {lid}-v{st.get('ver')}\nKul: ₹{q.get('final')} (advance ₹{q.get('advance')}, baaki demo dekh kar)\n"
            f"Samay: {q.get('days')} · 2 badlav shaamil · final file poore payment ke baad\n"
            f"Ye quote 7 din tak valid. Sirf yahi likhit quote pakka hai.\n"
            f"Payment: UPI QR (isi chat mein bhejte hain).\n"
            f"Dost ko code {ref} dein - unhe 10% off, aapko agle kaam par credit.")


def wa_link(lid):
    from urllib.parse import quote
    return f"https://wa.me/{leads()[lid]['phone']}?text={quote(customer_msg(lid))}"


def mark_paid(lid, amt):
    L = leads().get(lid)
    if not L:
        return f"❓ {lid} nahi mila"
    amt = int(amt)
    _append("payments.jsonl", {"id": lid, "amt": amt, "t": now().isoformat(timespec="seconds")})
    _event(lid, status="paid", paid=amt)
    code = (L.get("code") or "").upper()
    msg = f"✅ {lid}: ₹{amt} mila (ledger mein)."
    if code.startswith("REF-"):
        msg += "\n" + _ref_pending(lid, code, amt)
    return msg


def mark_refund(lid, amt):
    """Refund: ledger mein minus + is order se bana referral credit (intezaar wala) RADD."""
    if lid not in leads():
        return f"❓ {lid} nahi mila"
    amt = int(amt)
    _append("payments.jsonl", {"id": lid, "amt": -amt, "t": now().isoformat(timespec="seconds"), "refund": True})
    _event(lid, status="refunded", refund=amt)
    rows = _read("referral.jsonl")
    n = 0
    for r in rows:
        if r.get("from") == lid and r.get("status") == "wait":
            r["status"] = "cancelled"
            n += 1
    if n:
        with LOCK:
            _p("referral.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        audit("ref_cancel", frm=lid, n=n)
    return f"↩️ {lid}: ₹{amt} refund ledger mein." + (f" Referral credit radd ({n})." if n else "")


def _ref_owner(code):
    for x in leads().values():
        if (x.get("ref") or "").upper() == code:
            return x
    return None


def _ref_pending(lid, code, amt):
    src = _ref_owner(code)
    L = leads()[lid]
    if not src:
        return "🎟 Referral code ka maalik nahi mila - credit nahi."
    if src["phone"] == L["phone"] or (src.get("ip") and src.get("ip") == L.get("ip")):
        audit("ref_block", id=lid, code=code, why="same phone/ip")
        return "🚫 Referral: same phone/IP - credit NAHI (fraud niyam)."
    mon = now().strftime("%Y-%m")
    given = [r for r in _read("referral.jsonl") if r.get("to") == src["id"] and r.get("t", "").startswith(mon)]
    if len(given) >= REF_MONTH_CAP:
        return f"🚫 Referral: {src['id']} is mahine {REF_MONTH_CAP} credit le chuka."
    credit = max(100, round(amt * .05))
    due = (now() + datetime.timedelta(days=REF_DAYS)).isoformat(timespec="seconds")
    _append("referral.jsonl", {"to": src["id"], "from": lid, "credit": credit, "due": due, "status": "wait",
                               "t": now().isoformat(timespec="seconds")})
    audit("ref_wait", to=src["id"], frm=lid, credit=credit)
    return f"🎟 Referral: {src['name']} ko ₹{credit} credit {REF_DAYS} din baad (refund na ho to)."


# ---------------------------------------------------------------- Cloudflare worker
JS = r"""
// sabhisaab-leads (v3.5.0) - website form -> KV (JSON) + Telegram. VM band ho to bhi lead surakshit.
const ORIG = ['https://sabhisaab.com', 'https://www.sabhisaab.com'];
function cors(req) { const o = req.headers.get('origin') || '';
  return {'access-control-allow-origin': ORIG.includes(o) ? o : ORIG[0], 'access-control-allow-methods': 'POST, OPTIONS',
          'access-control-allow-headers': 'content-type', 'content-type': 'application/json'}; }
const clean = (v, n) => String(v == null ? '' : v).replace(/[<>]/g, '').trim().slice(0, n);
function j(o, s, h) { return new Response(JSON.stringify(o), {status: s || 200, headers: h}); }
function day() { return new Date(Date.now() + 19800000).toISOString().slice(0, 10); }
export default {
  async fetch(req, env) {
    const u = new URL(req.url); const H = cors(req);
    if (req.method === 'OPTIONS') return new Response('', {headers: H});
    if (u.pathname === '/lead' && req.method === 'POST') {
      let d; try { d = await req.json(); } catch (e) { return j({error: 'data galat'}, 400, H); }
      if (d.website) return j({id: 'OK', ref: ''}, 200, H);
      const ip = req.headers.get('cf-connecting-ip') || 'x';
      const rk = 'rl:' + ip; const n = +(await env.KV.get(rk) || 0);
      if (n >= 6) return j({error: 'thodi der baad koshish karein'}, 429, H);
      await env.KV.put(rk, String(n + 1), {expirationTtl: 3600});
      const name = clean(d.name, 80), phone = clean(d.phone, 16).replace(/[^0-9+]/g, ''), msg = clean(d.message, 3000);
      if (!name || phone.replace(/\D/g, '').length < 10 || msg.length < 3) return j({error: 'naam, WhatsApp number aur kaam likhiye'}, 400, H);
      if (!d.consent) return j({error: 'sahmati ka dabba chunein'}, 400, H);
      const t = Date.now(); const id = 'SH' + new Date(t + 19800000).toISOString().slice(2, 10).replace(/-/g, '') +
        Math.random().toString(36).slice(2, 6).toUpperCase();
      const lead = {id, ref: 'REF-' + id.slice(-4), t: new Date(t).toISOString(), name, phone, message: msg,
        service: clean(d.service, 160), budget: clean(d.budget, 12), code: clean(d.code, 20).toUpperCase(),
        urgent: !!d.urgent, care: !!d.care, extras: clean(d.extras, 600), src: clean(d.src, 120), page: clean(d.page, 80),
        ip: ip.slice(0, 64)};
      await env.KV.put('lead:' + t + ':' + id, JSON.stringify(lead), {expirationTtl: 90 * 86400});
      try { await fetch('https://api.telegram.org/bot' + env.TG_TOKEN + '/sendMessage', {method: 'POST',
        headers: {'content-type': 'application/json'}, body: JSON.stringify({chat_id: env.TG_CHAT,
        text: '🛎 Naya kaam ' + id + (lead.urgent ? ' ⚡' : '') + '\n' + name + '\n' + (lead.service || '') + '\n' + msg.slice(0, 300) +
        '\n(quote 5 min mein bot bhejega)'})}); } catch (e) {}
      return j({id, ref: lead.ref}, 200, H);
    }
    if (u.pathname === '/ev' && req.method === 'POST') {
      let d; try { d = await req.json(); } catch (e) { return j({}, 200, H); }
      const demo = clean(d.d, 40).replace(/[^a-z0-9-]/gi, ''), ty = ['v', 's', 'c'].includes(d.t) ? d.t : '';
      if (!demo || !ty) return j({}, 200, H);
      const k = 'ev:' + day() + ':' + demo + ':' + ty; const n = +(await env.KV.get(k) || 0);
      await env.KV.put(k, String(n + (ty === 's' ? Math.min(+d.n || 0, 600) : 1)), {expirationTtl: 400 * 86400});
      return j({}, 200, H);
    }
    const p = u.pathname.split('/');
    if (!env.KEY || p[1] !== env.KEY) return new Response('not found', {status: 404});
    if (p[2] === 'pull') {
      const after = u.searchParams.get('after') || 'lead:0';
      const L = await env.KV.list({prefix: 'lead:', limit: 1000}); const out = [];
      for (const k of L.keys) if (k.name > after) out.push(JSON.parse(await env.KV.get(k.name)));
      return j({leads: out, last: L.keys.length ? L.keys[L.keys.length - 1].name : after});
    }
    if (p[2] === 'stats') {
      const L = await env.KV.list({prefix: 'ev:' + (u.searchParams.get('day') || day()), limit: 1000}); const o = {};
      for (const k of L.keys) o[k.name] = +(await env.KV.get(k.name) || 0);
      return j(o);
    }
    if (p[2] === 'ping') return new Response('ok');
    return new Response('not found', {status: 404});
  }
};
"""


def deploy():
    """Worker banao/naya karo (dobara chalana surakshit) + website ko pata do (svc-cfg.js) + deploy."""
    from . import tg, relay, website
    tok, acc = relay._creds()
    c = _cfg()
    c.setdefault("key", secrets.token_urlsafe(24))
    if not c.get("kv"):
        found = None
        for ns in relay._api("GET", f"/accounts/{acc}/storage/kv/namespaces", tok, params={"per_page": 100}) or []:
            if ns.get("title") == NAME:
                found = ns["id"]
        c["kv"] = found or relay._api("POST", f"/accounts/{acc}/storage/kv/namespaces", tok, json={"title": NAME})["id"]
    sub = relay._subdomain(tok, acc)
    meta = {"main_module": "worker.js", "compatibility_date": "2024-09-23", "bindings": [
        {"type": "secret_text", "name": "KEY", "text": c["key"]},
        {"type": "secret_text", "name": "TG_TOKEN", "text": tg._tok()},
        {"type": "plain_text", "name": "TG_CHAT", "text": str(tg._chat())},
        {"type": "kv_namespace", "name": "KV", "namespace_id": c["kv"]}]}
    files = {"metadata": (None, json.dumps(meta), "application/json"),
             "worker.js": ("worker.js", JS.encode(), "application/javascript+module")}
    relay._api("PUT", f"/accounts/{acc}/workers/scripts/{NAME}", tok, files=files)
    try:
        relay._api("POST", f"/accounts/{acc}/workers/scripts/{NAME}/subdomain", tok, json={"enabled": True})
    except Exception as e:
        log(f"svc workers.dev: {e}")
    c["url"] = f"https://{NAME}.{sub}.workers.dev"
    c["made"] = time.time()
    _save_cfg(c)
    audit("deploy", url=c["url"])
    f = website.DIR / "site" / "svc-cfg.js"
    if f.parent.exists():
        f.write_text(f"window.SVC_API='{c['url']}';window.SVC_WA='{WA_OWNER}';\n")
        state.put("site_undeployed", True)
        threading.Thread(target=lambda: tg.say("🌐 " + str(website.deploy())), daemon=True).start()
    return f"✅ Services desk chalu: {c['url']}\nForm ka message ab JSON mein + Telegram. Website deploy ho raha hai."


def ensure_site_cfg():
    """v3.5.1: website ZIP ne svc-cfg.js khaali kar diya ho to dobara bharo + deploy (warna form ka message Telegram tak nahi aata)."""
    from . import tg, website
    c = _cfg()
    f = website.DIR / "site" / "svc-cfg.js"
    want = f"window.SVC_API='{c['url']}';window.SVC_WA='{WA_OWNER}';\n"
    if not f.parent.exists() or (f.exists() and f.read_text() == want):
        return False
    f.write_text(want)
    state.put("site_undeployed", True)
    audit("site_cfg_fix")
    tg.say("🔧 Website ke form ka pata khaali mila - dobara bhara, deploy: " + str(website.deploy()))
    return True


def _api_get(path, **params):
    c = _cfg()
    if not c.get("url"):
        return None
    r = requests.get(f"{c['url']}/{c['key']}/{path}", params=params, timeout=(8, 30))
    r.raise_for_status()
    return r.json()


def sync():
    if not _cfg().get("url") or state.get("svc_off"):
        return 0
    j = _api_get("pull", after=state.get("svc_after") or "lead:0") or {}
    n = 0
    for raw in j.get("leads", []):
        try:
            if ingest(raw) is not None:
                n += 1
        except Exception as e:
            log(f"svc ingest {raw.get('id')}: {e}")
    if j.get("last"):
        state.put("svc_after", j["last"])
    return n


def demo_stats(day=None):
    j = _api_get("stats", day=day or now().strftime("%Y-%m-%d")) or {}
    out = {}
    for k, v in j.items():
        _, _, demo, ty = k.split(":", 3)
        out.setdefault(demo, {"v": 0, "s": 0, "c": 0})[ty] = v
    return out


# ---------------------------------------------------------------- backup / audit / report
def backup():
    if not DIR.exists():
        return
    BAK.mkdir(parents=True, exist_ok=True)
    dst = BAK / now().strftime("%Y%m%d-%H")
    if not dst.exists():
        shutil.copytree(DIR, dst)
    for old in sorted(BAK.iterdir())[:-72]:
        shutil.rmtree(old, ignore_errors=True)


def night_audit():
    bad = []
    ok, n = audit_ok()
    if not ok:
        bad.append(f"🔴 Audit chain TOOTI line {n + 1} par - kisi ne record badla!")
    try:
        _R.clear()
        rates()
    except Exception as e:
        bad.append(f"🔴 {e}")
    paid = {}
    for p_ in _read("payments.jsonl"):
        paid[p_["id"]] = paid.get(p_["id"], 0) + p_["amt"]
    for lid in leads():
        q = (lead_state(lid).get("quote") or {})
        if q and paid.get(lid, 0) > q.get("final", 0):
            bad.append(f"🟡 {lid}: payment ₹{paid[lid]} > quote ₹{q['final']}")
    rows = _read("referral.jsonl")
    changed = False
    for r in rows:
        if r.get("status") == "wait" and r.get("due", "") <= now().isoformat():
            r["status"] = "given"
            changed = True
            audit("ref_given", to=r["to"], credit=r["credit"])
    if changed:
        with LOCK:
            _p("referral.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    cut = (now() - datetime.timedelta(days=KEEP_LEAD_DAYS)).isoformat()
    L = _read("leads.jsonl")
    kept, wiped = [], 0
    for x in L:
        if x.get("t", "") < cut and x["id"] not in paid and x.get("phone"):
            x.update(phone="", name="(90 din - mitaya)", ip="", message="")
            wiped += 1
        kept.append(x)
    if wiped:
        with LOCK:
            _p("leads.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in kept), encoding="utf-8")
        audit("privacy_wipe", n=wiped)
    return bad


def report(days=1):
    cut = (now() - datetime.timedelta(days=days)).isoformat()
    L = [x for x in leads().values() if x.get("t", "") >= cut[:10]]
    P = [p_ for p_ in _read("payments.jsonl") if p_.get("t", "") >= cut]
    by_src = {}
    for x in L:
        k = (x.get("code") or x.get("src") or "seedha")[:20]
        by_src[k] = by_src.get(k, 0) + 1
    lines = [f"🧾 SERVICES - pichhle {days} din", f"Lead: {len(L)} | Paid: {len(P)} | ₹{sum(p_['amt'] for p_ in P)}"]
    if by_src:
        lines.append("Kahan se: " + ", ".join(f"{k} {v}" for k, v in sorted(by_src.items(), key=lambda z: -z[1])))
    try:
        ds = demo_stats()
        if ds:
            top = sorted(ds.items(), key=lambda z: -z[1]["v"])[:8]
            lines.append("Demo (aaj): " + "; ".join(f"{d} 👁{s['v']} ⏱{round(s['s'] / max(1, s['v']))}s 👆{s['c']}" for d, s in top))
    except Exception as e:
        lines.append(f"Demo ginti abhi nahi ({str(e)[:60]})")
    wait = [r for r in _read("referral.jsonl") if r.get("status") == "wait"]
    if wait:
        lines.append(f"Referral credit intezaar mein: {len(wait)}")
    return "\n".join(lines)


# ---------------------------------------------------------------- bot hooks
def tick(run):
    """bot.scheduler har chakkar mein bulata hai. Sasta: sirf samay dekh kar."""
    from . import tg
    if state.get("svc_off"):
        return
    t = time.time()
    if t - state.get("svc_sync_at", 0) > 300:
        state.put("svc_sync_at", t)
        run(sync)
    try:                                         # v3.7.0: Instagram account band/khula jaanch (din mein ek baar)
        from . import igguard
        igguard.tick(run)
    except Exception as e:
        log(f"igguard tick: {e}")
    if t - state.get("svc_bak_at", 0) > 3600:
        state.put("svc_bak_at", t)
        run(backup)
    n = now()
    d = str(n.date())
    if n.strftime("%H:%M") >= "23:20" and state.get("svc_audit_day") != d:
        state.put("svc_audit_day", d)
        def _na():
            bad = night_audit()
            if bad:
                tg.alert("red", "🛡 Services raat ki jaanch:\n" + "\n".join(bad))
        run(_na)
    if state.get("svc_cfg_day") != d and _cfg().get("url"):        # v3.5.1: website par form ka pata khaali na rahe
        state.put("svc_cfg_day", d)
        run(ensure_site_cfg)
    if n.strftime("%H:%M") >= "21:45" and state.get("svc_rep_day") != d and _cfg().get("url"):
        state.put("svc_rep_day", d)
        run(lambda: tg.say(report(1)))


def on_text(t, run):
    from . import tg
    tl = t.lower().strip()
    if tl in ("services chalu", "services shuru"):
        state.put("svc_off", False)
        run(lambda: tg.say(deploy()))
        return True
    if tl == "services band":
        state.put("svc_off", True)
        return tg.say("⏸ Services desk ruka (form ka message phir bhi worker mein surakshit rahega).")
    if tl in ("services report", "services haal", "service report"):
        run(lambda: tg.say(report(1)))
        return True
    m = re.match(r"services report (\d+)", tl)
    if m:
        run(lambda: tg.say(report(int(m.group(1)))))
        return True
    m = re.match(r"quote (sh\w+) (\d+)\s*(.*)", t, re.I)
    if m:
        audit("override", id=m.group(1).upper(), price=int(m.group(2)))
        run(lambda: draft(m.group(1).upper(), int(m.group(2)), m.group(3).strip()))
        return True
    m = re.match(r"paid (sh\w+) (\d+)", tl)
    if m:
        return tg.say(mark_paid(m.group(1).upper(), m.group(2)))
    m = re.match(r"refund (sh\w+) (\d+)", tl)
    if m:
        return tg.say(mark_refund(m.group(1).upper(), m.group(2)))
    m = re.match(r"lead (sh\w+)", tl)
    if m:
        lid = m.group(1).upper()
        L = leads().get(lid)
        return tg.say(json.dumps({**(L or {}), "state": lead_state(lid)}, ensure_ascii=False, indent=1)[:3500]
                      if L else f"❓ {lid} nahi mila")
    m = re.match(r"rate (.+)", tl)
    if m and not tl.startswith("rate card"):
        items, red = classify(m.group(1))
        if red:
            return tg.say(f"🔴 {red} - nahi lena")
        return tg.say("\n".join(f"{i['name']}: ₹{i['price']} (floor ₹{i['floor']}, market ₹{i['market'][0]}-{i['market'][1]})"
                                for i in items) or "Rate list mein nahi - custom quote")
    return None


def on_callback(rest):
    from . import tg
    act, _, lid = rest.partition(":")
    if lid not in leads():
        return tg.say(f"❓ {lid} nahi mila")
    if act == "ok":
        st = lead_state(lid)
        if st.get("status") != "draft":
            return tg.say(f"⛔ {lid}: quote '{st.get('status')}' haal mein hai - pehle sahi quote banayein.")
        _event(lid, status="sent", by="owner")
        return tg.say(f"📤 {lid} - customer ko WhatsApp par bhejne ke liye tap karein (message bhara hua):\n{wa_link(lid)}\n\n"
                      "Fir UPI QR isi chat mein bhejein. Paisa aaye to bank app mein dekh kar likhein: "
                      f"'paid {lid} <rupaye>'")
    if act == "no":
        _event(lid, status="declined", by="owner")
        from urllib.parse import quote
        L = leads()[lid]
        msg = (f"Namaste {L.get('name', '')} ji, aapke sandesh ke liye dhanyavaad. Ye kaam hum niyam/suraksha ki wajah se "
               "nahi lete. Iski jagah website, calculator, billing app ya bot jaisa kaam chahiye to zaroor batayein 🙏")
        return tg.say(f"Mana ka message (tap = WhatsApp):\nhttps://wa.me/{L['phone']}?text={quote(msg)}")
    return None
