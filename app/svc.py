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


SITE = "https://sabhisaab.com"
REF_PCT = 10            # v3.8.0: dost ke PAID bill ka 10% (fixed ₹50/₹100 nahi - ₹10 resume par nuksan nahi)
REF_MIN_BILL = 300      # isse chhote bill par bonus nahi banta
REF_MAX = 500           # ek bonus max
REF_USE_PCT = 10        # bonus agle PAID bill ka max 10% kaat sakta hai (kaam kabhi free nahi)
REF_EXPIRY_DAYS = 90    # = data mitane ke 90 din


def _kb(rows):
    """Telegram buttons: (text, 'sv:..') = callback, (text, 'https://..') = link."""
    return {"inline_keyboard": [[({"text": t, "url": d} if d.startswith("http") else {"text": t, "callback_data": d[:64]})
                                 for t, d in row] for row in rows]}


def page_link(lid):
    L = leads().get(lid) or {}
    return f"{SITE}/q?id={lid}&k={L.get('k', '')}" if L.get("k") else ""


def _wa(phone, msg):
    from urllib.parse import quote
    return f"https://wa.me/{phone}?text={quote(msg)}"


def _push(lid, **patch):
    """Worker (customer ka page) ko naya haal. Fail ho to queue - agle sync mein dobara."""
    c = _cfg()
    if not c.get("url"):
        _append("push_queue.jsonl", {"id": lid, "patch": patch, "t": now().isoformat(timespec="seconds")})
        return False
    try:
        r = requests.post(f"{c['url']}/{c['key']}/set", json={"id": lid, "patch": patch}, timeout=(8, 20))
        r.raise_for_status()
        return True
    except Exception as e:
        log(f"svc push {lid}: {e}")
        _append("push_queue.jsonl", {"id": lid, "patch": patch, "t": now().isoformat(timespec="seconds")})
        return False


def _flush_push():
    rows = _read("push_queue.jsonl")
    if not rows or not _cfg().get("url"):
        return 0
    with LOCK:
        _p("push_queue.jsonl").write_text("", encoding="utf-8")
    ok = 0
    for r in rows:
        ok += 1 if _push(r["id"], **r["patch"]) else 0
    return ok


def credits_for(phone):
    """Is phone ke paas kitna referral bonus (given, expire nahi, use nahi)."""
    tot, rows = 0, []
    lim = (now() - datetime.timedelta(days=REF_EXPIRY_DAYS)).isoformat()
    by_id = leads()
    for r in _read("referral.jsonl"):
        to = by_id.get(r.get("to")) or {}
        if to.get("phone") == phone and r.get("status") == "given" and r.get("given_at", r.get("due", "")) >= lim:
            tot += r["credit"]
            rows.append(r)
    return tot, rows


def draft(lid, override=None, note=""):
    from . import tg
    L = leads().get(lid)
    if not L:
        return tg.say(f"❓ {lid} nahi mila")
    items, red = classify(L.get("message", ""), L.get("service", ""))
    ver = int(lead_state(lid).get("ver") or 0) + 1
    link = page_link(lid)
    hello = _wa(L["phone"], f"Namaste {L.get('name', '')} ji 🙏 Sab Hisaab se. Aapka kaam mila ({lid}). "
                            f"Thoda samajhna tha - abhi baat kar sakte hain?" + (f"\nAapka page: {link}" if link else ""))
    head = (f"🛎 KAAM {lid}-v{ver}{' ⚡URGENT' if L.get('urgent') else ''}\n👤 {L.get('name')}  📞 +{L.get('phone')}\n"
            f"💬 {L.get('message', '')[:600]}\n🏷 Code: {L.get('code') or '-'} | Budget: {L.get('budget') or '-'} | Src: {L.get('src') or '-'}")
    talk = [("💬 WhatsApp", hello), ("📞 Uthaya", f"sv:cu:{lid}"), ("📵 Nahi", f"sv:cn:{lid}"), ("⏰ Baad", f"sv:cb:{lid}")]
    if red:
        _event(lid, ver=ver, status="red", red=red)
        return tg.say(head + f"\n\n🔴 Ye kaam NAHI lena: {red}\nCustomer ko vinamra mana + sahi vikalp:",
                      _kb([[("📝 Mana ka message", f"sv:no:{lid}")]]))
    if not items and override is None:
        _event(lid, ver=ver, status="manual")
        return tg.say(head + "\n\n🟡 Rate list mein seedha nahi mila (custom). Pehle baat karke kaam samjhein, phir likhein:\n"
                      f"quote {lid} 499 <kaam ka naam>", _kb([talk]))
    it = items[0] if items else {"id": "custom", "cat": "custom", "name": note or "Custom kaam",
                                 "price": override, "floor": max(10, int(override * .6)), "max": override * 2}
    if override is not None:
        it = dict(it, price=int(override), name=note or it["name"])
        it["floor"] = min(it["floor"], it["price"]) if it["id"] != "custom" else it["floor"]
    try:
        q = price(it, L.get("code"), L.get("urgent"), L.get("care"))
    except Exception as e:
        _event(lid, ver=ver, status="guard", err=str(e))
        return tg.say(head + f"\n\n⛔ {e}\nQuote ROKA. Sahi price: quote {lid} <rupaye>")
    cr, _ = credits_for(L["phone"])
    use = max(0, min(cr, round(q["final"] * REF_USE_PCT / 100), q["final"] - it["floor"])) if cr else 0
    if use:
        q["final"] -= use
        q["credit_use"] = use
        q["advance"] = min(q["advance"], q["final"])
    q.update({"item": it["id"], "name": it["name"], "days": it.get("days", "baat karke"), "risk": it.get("risk", "G"),
              "valid": (now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d"), "market": it.get("market")})
    _event(lid, ver=ver, status="draft", quote=q)
    alt = "\n".join(f"   • {i['name']} ₹{i['price']}" for i in items[1:]) if len(items) > 1 else ""
    risk = "\n🟡 Sharton wala kaam: client ka apna account/server, tip-signal nahi." if q["risk"] == "Y" else ""
    txt = (head + f"\n\n🧾 {q['name']}\n₹{q['base']}" + (f" − ₹{q['off']} ({q['off_pct']}%)" if q["off"] else "") +
           (f" − ₹{use} bonus" if use else "") +
           f"{' +50% urgent' if L.get('urgent') else ''} = ₹{q['final']}\nAdvance: ₹{q['advance']} · {q['days']}" + risk +
           (f"\nDoosre mel:\n{alt}" if alt else "") +
           "\n\n👉 Pehle baat karke kaam samjhein. Rate badalna ho: quote " + lid + " <rupaye> <naam>")
    return tg.say(txt, _kb([talk, [(f"✅ ₹{q['final']} customer ke page par bhejo", f"sv:ok:{lid}"), ("❌ Mana", f"sv:no:{lid}")]]))


def customer_msg(lid):
    L = leads()[lid]
    st = lead_state(lid)
    q = st.get("quote") or {}
    return (f"Namaste {L.get('name', '')} ji 🙏\nSab Hisaab - aapka kaam: {q.get('name')}\n"
            f"Kul: ₹{q.get('final')} (pehle ₹{q.get('advance')}) · Samay: {q.get('days')} · 2 badlav shaamil\n"
            f"Rate dekhein aur 'Haan' dabayein - wahin payment ka QR khulega:\n{page_link(lid)}\n"
            f"Quote {q.get('valid')} tak valid. Dost ko code {L.get('ref', '')} dein - unhe 10% off, "
            f"aapko unke bill ka 10% bonus.")


def wa_link(lid):
    return _wa(leads()[lid]["phone"], customer_msg(lid))


def send_rate(lid, by="owner"):
    """Ek click: quote -> customer ka page (Haan dabate hi QR). WhatsApp message bhara hua owner ko."""
    st = lead_state(lid)
    q = st.get("quote")
    if st.get("status") != "draft" or not q:
        return f"⛔ {lid}: abhi '{st.get('status')}' - pehle quote banayein (quote {lid} <rupaye>)."
    c = _cfg()
    patch = {"quote": {k: q.get(k) for k in ("name", "final", "advance", "days", "base", "off", "valid", "note")},
             "status": "rate", "pay_amt": q.get("advance") or q.get("final")}
    if c.get("upi"):
        patch["upi"] = c["upi"]
    pushed = _push(lid, **patch)
    _event(lid, status="rate", by=by)
    warn = "" if c.get("upi") else "\n⚠️ UPI ID set nahi - QR nahi dikhega. Likhein: services upi <aapki-upi@bank>"
    return (f"📤 {lid}: ₹{q['final']} customer ke page par {'chala gaya ✅' if pushed else 'queue mein (5 min mein)'}.{warn}\n"
            f"Customer ko batane ke liye tap (message bhara hua):\n{wa_link(lid)}")


def set_stage(lid, stage, **extra):
    """Owner override - koi bhi stage. Log + page par."""
    _event(lid, status=stage, by="owner", **extra)
    _push(lid, status=stage, **{k: v for k, v in extra.items() if k in ("paid", "due", "deliver_note", "pay_amt", "upi")})
    return f"✔ {lid} → {stage}" + (f" {extra}" if extra else "")


def mark_paid(lid, amt):
    L = leads().get(lid)
    if not L:
        return f"❓ {lid} nahi mila"
    amt = int(amt)
    _append("payments.jsonl", {"id": lid, "amt": amt, "t": now().isoformat(timespec="seconds")})
    tot = sum(p_["amt"] for p_ in _read("payments.jsonl") if p_["id"] == lid)
    q = lead_state(lid).get("quote") or {}
    stage = "working" if tot >= (q.get("advance") or 0) else "accepted"
    _event(lid, status="paid", paid=amt)
    _event(lid, status=stage)
    rest = max(0, (q.get("final") or 0) - tot)
    _push(lid, status=stage, paid=tot, pay_amt=rest or 0)
    if q.get("credit_use"):                              # bonus istemaal hua - band karo
        used, need = [], q["credit_use"]
        rows = _read("referral.jsonl")
        for r in rows:
            if need <= 0:
                break
            to = leads().get(r.get("to")) or {}
            if to.get("phone") == L["phone"] and r.get("status") == "given":
                r["status"] = "used"
                r["used_on"] = lid
                need -= r["credit"]
                used.append(r["credit"])
        with LOCK:
            _p("referral.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        audit("ref_used", id=lid, amt=q["credit_use"])
    code = (L.get("code") or "").upper()
    msg = f"✅ {lid}: ₹{amt} mila (kul ₹{tot}, baaki ₹{rest}). Stage: {stage}."
    if code.startswith("REF-"):
        msg += "\n" + _ref_pending(lid, code, amt)
    return msg


def mark_refund(lid, amt):
    """Refund: ledger mein minus + is order se bana referral bonus (intezaar wala) RADD."""
    if lid not in leads():
        return f"❓ {lid} nahi mila"
    amt = int(amt)
    _append("payments.jsonl", {"id": lid, "amt": -amt, "t": now().isoformat(timespec="seconds"), "refund": True})
    _event(lid, status="refunded", refund=amt)
    _push(lid, status="lost")
    rows = _read("referral.jsonl")
    n = 0
    for r in rows:
        if r.get("from") == lid and r.get("status") in ("wait", "given"):
            r["status"] = "cancelled"
            n += 1
    if n:
        with LOCK:
            _p("referral.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        audit("ref_cancel", frm=lid, n=n)
    return f"↩️ {lid}: ₹{amt} refund ledger mein." + (f" Referral bonus radd ({n})." if n else "")


def _ref_owner(code):
    for x in leads().values():
        if (x.get("ref") or "").upper() == code:
            return x
    return None


def ref_credit(amt):
    """10% of PAID amount; ₹300 se chhote bill par 0; max ₹500."""
    amt = int(amt)
    return 0 if amt < REF_MIN_BILL else min(REF_MAX, round(amt * REF_PCT / 100))


def _ref_pending(lid, code, amt):
    src = _ref_owner(code)
    L = leads()[lid]
    if not src:
        return "🎟 Referral code ka maalik nahi mila - bonus nahi."
    if src["phone"] == L["phone"] or (src.get("ip") and src.get("ip") == L.get("ip")):
        audit("ref_block", id=lid, code=code, why="same phone/ip")
        return "🚫 Referral: same phone/IP - bonus NAHI (fraud niyam)."
    if any(r.get("from") == lid for r in _read("referral.jsonl")):
        return "🎟 Is order ka bonus pehle hi bana hua hai."
    mon = now().strftime("%Y-%m")
    given = [r for r in _read("referral.jsonl") if r.get("to") == src["id"] and r.get("t", "").startswith(mon)]
    if len(given) >= REF_MONTH_CAP:
        return f"🚫 Referral: {src['id']} is mahine {REF_MONTH_CAP} bonus le chuka."
    paid = sum(p_["amt"] for p_ in _read("payments.jsonl") if p_["id"] == lid)
    credit = ref_credit(paid)
    if not credit:
        return f"🎟 Referral: bill ₹{paid} (₹{REF_MIN_BILL} se kam) - bonus nahi banta."
    due = (now() + datetime.timedelta(days=REF_DAYS)).isoformat(timespec="seconds")
    _append("referral.jsonl", {"to": src["id"], "from": lid, "credit": credit, "due": due, "status": "wait",
                               "t": now().isoformat(timespec="seconds")})
    audit("ref_wait", to=src["id"], frm=lid, credit=credit)
    return (f"🎟 Referral: {src['name']} ko ₹{credit} bonus {REF_DAYS} din baad (refund na ho to); "
            f"agle paid kaam ke bill ka max {REF_USE_PCT}% katega, {REF_EXPIRY_DAYS} din tak.")


# ---------------------------------------------------------------- Cloudflare worker
JS = __import__("pathlib").Path(__file__).with_name("svc_worker.js").read_text(encoding="utf-8")

# v3.8.0: sabhisaab.com/api/* -> worker (same-origin; kuch ISP/phone workers.dev rok dete hain, isliye form atakta tha)
FN_JS = """// v3.8.0 bot ne banaya - GitHub par nahi (.gitignore). sabhisaab.com/api/* -> services worker
const W = '%s', PK = '%s';
export async function onRequest(ctx) {
  const r = ctx.request, u = new URL(r.url);
  const h = new Headers({'content-type': r.headers.get('content-type') || 'application/json', 'origin': 'https://sabhisaab.com',
    'x-sh-pk': PK, 'x-sh-ip': r.headers.get('cf-connecting-ip') || ''});
  const init = {method: r.method, headers: h};
  if (!['GET', 'HEAD'].includes(r.method)) init.body = await r.text();
  try {
    const res = await fetch(W + u.pathname + u.search, init);
    return new Response(res.body, {status: res.status, headers: {'content-type': 'application/json', 'cache-control': 'no-store'}});
  } catch (e) {
    return new Response(JSON.stringify({error: 'server se jawab nahi - dobara koshish'}), {status: 502, headers: {'content-type': 'application/json'}});
  }
}
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
        {"type": "secret_text", "name": "PK", "text": c.setdefault("pk", secrets.token_urlsafe(24))},
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
    if _write_site_files(c):
        state.put("site_undeployed", True)
        threading.Thread(target=lambda: tg.say("🌐 " + str(website.deploy())), daemon=True).start()
    return f"✅ Services desk chalu: {c['url']}\nForm ka message ab JSON mein + Telegram. Website deploy ho raha hai."


def _site_files(c):
    """v3.8.0: website ko pata - (1) svc-cfg.js: pehle same-origin /api, atke to seedha worker;
    (2) functions/api/[[path]].js (Pages Function, gupt PK ke saath - GitHub par NAHI jaata)."""
    cfg = (f"window.SVC_API='/api';window.SVC_API2='{c['url']}';window.SVC_WA='{WA_OWNER}';"
           f"window.SVC_UPI_ON={1 if c.get('upi') else 0};\n")
    q = (__import__("pathlib").Path(__file__).parent / "assets" / "svc" / "q.html").read_text(encoding="utf-8")
    return {"site/svc-cfg.js": cfg, "functions/api/[[path]].js": FN_JS % (c["url"], c.get("pk", "")), "site/q.html": q}


def _write_site_files(c):
    """Badla ho to likho. True = kuch badla (deploy chahiye)."""
    from . import website
    if not (website.DIR / "site").exists() or not c.get("url"):
        return False
    gi = website.DIR / ".gitignore"
    try:
        g = gi.read_text() if gi.exists() else ""
        if "functions/" not in g:
            gi.write_text(g.rstrip("\n") + "\n# v3.8.0 services proxy (gupt key) - GitHub par nahi\nfunctions/\n")
    except Exception as e:
        log(f"svc gitignore: {e}")
    _patch_audit()
    changed = False
    for rel, body in _site_files(c).items():
        f = website.DIR / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        if not f.exists() or f.read_text() != body:
            f.write_text(body)
            changed = True
    return changed


def _patch_audit():
    """v3.8.0: /q customer ka gupt (noindex) page hai - SEO/inbound-link jaanch se bahar (warna deploy rukta)."""
    from . import website
    f = website.DIR / "scripts" / "audit.py"
    try:
        a = f.read_text(encoding="utf-8")
        b = a.replace('SKIP_SEO = {"404.html"}', 'SKIP_SEO = {"404.html", "q.html"}').replace(
            'if p in ("404", "googleb9a1fd91a1579ee6"): continue', 'if p in ("404", "googleb9a1fd91a1579ee6", "q"): continue')
        if b != a:
            f.write_text(b, encoding="utf-8")
            audit("audit_patch_q")
    except Exception as e:
        log(f"svc audit patch: {e}")


def ensure_site_cfg():
    """v3.5.1/v3.8.0: website ZIP ne svc-cfg.js ya proxy mita diya ho to dobara likho + deploy."""
    from . import tg, website
    c = _cfg()
    if not c.get("url"):
        return False
    if not c.get("pk") or not c.get("v380"):
        tg.say("🔧 Services worker v3.8.0 (gupt page + /api raasta) chadha raha hoon...")
        c["v380"] = 1
        _save_cfg(c)
        return deploy()
    if not _write_site_files(c):
        return False
    state.put("site_undeployed", True)
    audit("site_cfg_fix")
    tg.say("🔧 Website ke form ka raasta (svc-cfg/api) dobara likha, deploy: " + str(website.deploy()))
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
            r["given_at"] = now().isoformat(timespec="seconds")
            changed = True
        elif r.get("status") == "given" and r.get("given_at", r.get("due", "")) < (now() - datetime.timedelta(days=REF_EXPIRY_DAYS)).isoformat():
            r["status"] = "expired"
            changed = True
            audit("ref_expired", to=r["to"], credit=r["credit"])
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
    if t - state.get("svc_rem_at", 0) > 300:              # v3.8.0: yaad dilana + atka hua page-update dobara
        state.put("svc_rem_at", t)
        run(lambda: (_flush_push(), reminders()))
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
    if state.get("svc_cfg_day2") != d and _cfg().get("url"):        # v3.5.1: website par form ka pata khaali na rahe
        state.put("svc_cfg_day2", d)
        run(ensure_site_cfg)
    if n.strftime("%H:%M") >= "21:45" and state.get("svc_rep_day") != d and _cfg().get("url"):
        state.put("svc_rep_day", d)
        run(lambda: tg.say(report(1)))


def on_text(t, run):
    from . import tg
    tl = t.lower().strip()
    r = on_text_crm(t, run)
    if r is not None:
        return r
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
        return tg.say(send_rate(lid))
    if act in ("cu", "cn", "cb"):                       # call log: uthaya / nahi uthaya / baad mein
        what = {"cu": "uthaya", "cn": "nahi uthaya", "cb": "baad mein"}[act]
        _append("calls.jsonl", {"id": lid, "r": what, "t": now().isoformat(timespec="seconds")})
        if act == "cu" and lead_state(lid).get("status") in ("draft", "manual", None):
            _push(lid, status="talk")
        _event(lid, call=what)
        nxt = {"cu": "Kaam samajh aa gaya to rate wala ✅ button dabayein (ya quote " + lid + " <rupaye> <naam>).",
               "cn": "Bot 3 ghante baad yaad dilayega.", "cb": "Bot kal subah yaad dilayega."}[act]
        return tg.say(f"📞 {lid}: {what} - likh liya. {nxt}")
    if act == "no":
        _event(lid, status="declined", by="owner")
        _push(lid, status="lost")
        L = leads()[lid]
        msg = (f"Namaste {L.get('name', '')} ji, aapke sandesh ke liye dhanyavaad. Ye kaam hum niyam/suraksha ki wajah se "
               "nahi lete. Iski jagah website, resume, form madad, billing app jaisa kaam chahiye to zaroor batayein 🙏")
        return tg.say(f"Mana ka message (tap = WhatsApp):\n{_wa(L['phone'], msg)}")
    return None


def crm_list():
    """Khule kaam stage ke hisaab se (umr ke saath)."""
    out = {}
    for lid, L in leads().items():
        st = lead_state(lid).get("status") or "new"
        if st in ("closed", "lost", "declined", "red", "refunded", "feedback"):
            continue
        age = (now() - datetime.datetime.fromisoformat(L["t"].replace("Z", "+00:00")).astimezone(IST)).days
        out.setdefault(st, []).append(f"{lid} {L.get('name', '')[:14]} {age}d")
    if not out:
        return "📋 CRM: koi khula kaam nahi."
    return "📋 CRM (khule kaam)\n" + "\n".join(f"• {k}: " + ", ".join(v[:12]) for k, v in out.items())


def reminders():
    """5 min / 3 ghante / 24 ghante / 48 ghante wali yaad - har kaam par ek hi baar har tarah ki."""
    from . import tg
    sent = {(r["id"], r["k"]) for r in _read("reminded.jsonl")}
    calls = {}
    for c_ in _read("calls.jsonl"):
        calls[c_["id"]] = c_
    n_ = now()
    msgs = []
    for lid, L in leads().items():
        st = lead_state(lid)
        s_ = st.get("status") or "new"
        try:
            t0 = datetime.datetime.fromisoformat(L["t"].replace("Z", "+00:00")).astimezone(IST)
        except Exception:
            continue
        mins = (n_ - t0).total_seconds() / 60
        def want(k, cond, text):
            if cond and (lid, k) not in sent:
                msgs.append(text)
                _append("reminded.jsonl", {"id": lid, "k": k, "t": n_.isoformat(timespec="seconds")})
        talked = lid in calls or st.get("call")
        want("5m", s_ in ("draft", "manual") and not talked and 5 <= mins < 180,
             f"⏰ {lid} ({L.get('name', '')}) - 5 min ho gaye, abhi tak baat nahi. Jaldi jawab = kaam milne ka zyada mauka.")
        c_ = calls.get(lid) or {}
        if c_.get("r") == "nahi uthaya":
            ct = datetime.datetime.fromisoformat(c_["t"])
            want("3h:" + c_["t"], (n_ - ct).total_seconds() > 3 * 3600, f"📞 {lid} - 3 ghante pehle call nahi uthi thi, dobara try karein.")
        if c_.get("r") == "baad mein":
            ct = datetime.datetime.fromisoformat(c_["t"])
            want("bd:" + c_["t"], n_.date() > ct.date() and n_.hour >= 9, f"📞 {lid} - kal 'baad mein' bola tha, aaj baat karein.")
        want("24h", s_ in ("draft", "manual", "talk") and mins > 1440, f"🕐 {lid} - 24 ghante se rate nahi gaya.")
        if s_ == "rate":
            want("48h", mins > 2880, f"🕐 {lid} - rate bheje 2 din, customer ne haan nahi kaha. Ek baar WhatsApp karein: {wa_link(lid)}")
        due = st.get("due") or ""
        if s_ == "working" and due:
            want("due:" + due, n_.strftime("%Y-%m-%d") >= (datetime.date.fromisoformat(due) - datetime.timedelta(days=1)).isoformat(),
                 f"📦 {lid} - delivery {due} ko hai.")
    if msgs:
        tg.say("\n".join(msgs[:15]))
    return len(msgs)


def on_text_crm(t, run):
    """v3.8.0 naye command (owner)."""
    from . import tg
    tl = t.lower().strip()
    m = re.match(r"services upi (\S+@\S+)$", tl)
    if m:
        c = _cfg()
        c["upi"] = m.group(1)
        _save_cfg(c)
        audit("upi_set")
        run(lambda: (ensure_site_cfg(), tg.say("✅ UPI set. Ab customer ke 'Haan' dabate hi uske page par isi UPI ka QR (amount bhara) dikhega.")))
        return True
    if tl in ("services crm", "crm"):
        return tg.say(crm_list())
    m = re.match(r"(?:crm )?(sh\w+) (new|talk|rate|accepted|paid|working|delivered|feedback|closed|lost)$", tl)
    if m:
        return tg.say(set_stage(m.group(1).upper(), m.group(2)))
    m = re.match(r"crm (sh\w+) (?:amount|rakam) (\d+)$", tl)
    if m:
        lid = m.group(1).upper()
        q = dict(lead_state(lid).get("quote") or {})
        if not q:
            return tg.say(f"⛔ {lid}: pehle quote banayein")
        q["final"] = int(m.group(2))
        q["advance"] = min(q.get("advance") or q["final"], q["final"])
        _event(lid, quote=q, by="owner", override="amount")
        _push(lid, quote={k: q.get(k) for k in ("name", "final", "advance", "days", "base", "off", "valid", "note")},
              pay_amt=q["advance"])
        return tg.say(f"✔ {lid}: rakam ₹{q['final']} (page par bhi). Log mein darj.")
    m = re.match(r"crm (sh\w+) note (.+)$", t, re.I)
    if m:
        _event(m.group(1).upper(), note=m.group(2)[:300], by="owner")
        return tg.say("✔ note likha")
    m = re.match(r"crm (sh\w+) due (\d{4}-\d{2}-\d{2})$", tl)
    if m:
        return tg.say(set_stage(m.group(1).upper(), lead_state(m.group(1).upper()).get("status") or "working", due=m.group(2)))
    m = re.match(r"pay (sh\w+)$", tl)                                # one-click: customer ki haan ka intezaar kiye bina QR khol do
    if m:
        lid = m.group(1).upper()
        if lead_state(lid).get("status") == "draft":
            tg.say(send_rate(lid))
        return tg.say(set_stage(lid, "accepted", upi=_cfg().get("upi", "")) + " - QR customer ke page par khul gaya.")
    m = re.match(r"deliver (sh\w+)\s*(.*)$", t, re.I)
    if m:
        lid = m.group(1).upper()
        if lid not in leads():
            return tg.say(f"❓ {lid} nahi mila")
        set_stage(lid, "delivered", deliver_note=m.group(2)[:300])
        L = leads()[lid]
        msg = (f"Namaste {L.get('name', '')} ji 🙏 aapka kaam ({lid}) taiyaar hai. Ek baar dekh kar apne page par "
               f"star de dijiye - isse doosron ko bharosa milta hai:\n{page_link(lid)}")
        return tg.say(f"📦 {lid} delivered. Customer ko batane ke liye tap:\n{_wa(L['phone'], msg)}")
    m = re.match(r"(?:aur kaam|repeat) (sh\w+)$", tl)                  # 30 din baad - SIRF owner ke tap se
    if m:
        lid = m.group(1).upper()
        L = leads().get(lid)
        if not L:
            return tg.say(f"❓ {lid} nahi mila")
        msg = (f"Namaste {L.get('name', '')} ji 🙏 Sab Hisaab se. Pichhla kaam theek chal raha hai? Koi aur digital kaam ho "
               f"(form, resume, bill, website...) to bas Hindi mein likh dijiye.")
        return tg.say(f"Tap = WhatsApp (sirf aap bhejenge):\n{_wa(L['phone'], msg)}")
    return None
