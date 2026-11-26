"""v3.9.4 (owner 25 Nov): 📥 LEADS - ek button, sab ek jagah. Bahut sandesh dekhne ki zaroorat nahi:
  - kul / aaj / 7 din, kahan se (website, video code, comment, DM, phone), brand-wise
  - ABHI KARNA: har khula kaam agle kadam ke saath (purana pehle) + button (khol kar wahi kaam)
  - comment / DM wale jinka number abhi nahi (24 ghante se zyada = ⏰)
DM (Messenger + Instagram): sirf jisne KHUD message kiya, 24 ghante ke andar, ek thread par 24 ghante mein ek hi apne-aap jawab
(Meta ka niyam - ye cold DM nahi). Number likha ho to apne aap lead card + follow-up. Ijaazat (pages_messaging /
instagram_manage_messages) na ho to chupchaap ruk kar Leads mein batata hai.
"""
import datetime
import re
import time

from . import state
from .config import BRANDS
from .log import log

CODE2B = {"LABH10": "deals", "NATAK10": "sunonatak", "MONEY10": "money", "PAHADI10": "pahadi"}
OPEN = ("new", "draft", "manual", "talk", "rate", "accepted", "paid", "working", "delivered")
NEXT = {"new": "📞 baat karo", "draft": "📞 baat karo", "manual": "📞 baat karo", "talk": "🧾 rate bhejo",
        "rate": "⏳ Haan ka intezaar - yaad dilao", "accepted": "💰 advance aaya? 'paid SH.. X'", "paid": "🔧 kaam karo -> 'deliver SH..'",
        "working": "🔧 kaam karo -> 'deliver SH..'", "delivered": "⭐ feedback / band"}
PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?([6-9](?:[\s-]?\d){9})(?!\d)")


def _now():
    from . import svc
    return svc.now()


def _bn(b):
    return BRANDS.get(b, {}).get("name", b or "-").split()[0]


def brand_of(L):
    c = (L.get("code") or "").upper()
    if c in CODE2B:
        return CODE2B[c]
    s = (str(L.get("src") or "") + " " + str(L.get("page") or "")).lower()
    for b in BRANDS:
        if b in s:
            return b
    return ""


def src_of(L):
    c = (L.get("code") or "").upper()
    s = str(L.get("src") or "")
    if s.startswith("manual-dm"):
        return "DM"
    if s.startswith("manual-"):
        return {"manual-call": "phone", "manual-phone": "phone", "manual-wa": "WhatsApp", "manual-whatsapp": "WhatsApp"}.get(s, "dukaan/aur")
    if c in CODE2B:
        return "video code"
    if c.startswith("REF-"):
        return "dost ka code"
    return "website"


# ---------------------------------------------------------------- comment / DM wale (number nahi)
def soft_leads(days=7):
    """Comment + DM jinme kaam/daam poocha, aur number nahi mila -> list (purana pehle)."""
    from . import svc
    cut = (_now() - datetime.timedelta(days=days)).isoformat()
    done = set(state.get("lb_done") or [])
    out = []
    for c in svc._read("comments.jsonl"):
        u = c.get("u") or {}
        if c.get("t", "") < cut or c.get("id") in done or u.get("intent") not in ("kaam", "price", "kaam_any"):
            continue
        out.append({"id": c["id"], "t": c["t"], "pf": c.get("pf"), "b": c.get("b"), "who": c.get("who", ""), "text": c.get("text", ""),
                    "item": u.get("item"), "auto": c.get("auto"), "kind": "comment"})
    for d in svc._read("dm.jsonl"):
        if d.get("t", "") < cut or d.get("id") in done or d.get("lead"):
            continue
        out.append({"id": d["id"], "t": d["t"], "pf": d.get("pf"), "b": d.get("b"), "who": d.get("who", ""), "text": d.get("text", ""),
                    "item": d.get("item"), "auto": d.get("replied"), "kind": "DM"})
    # form bhar diya (naam milta) = ab asli lead
    names = {str(L.get("name", "")).lower().split()[0] for L in svc.leads().values() if L.get("name")}
    out = [x for x in out if not (x["who"] and str(x["who"]).lower().split()[0] in names)]
    return sorted(out, key=lambda x: x["t"])


# ---------------------------------------------------------------- ek message mein sab
def text_and_kb():
    from . import svc
    n = _now()
    d = str(n.date())
    w7 = str((n - datetime.timedelta(days=7)).date())
    LL = {k: v for k, v in svc.leads().items() if not str(v.get("phone", "")).endswith("9999999999") and v.get("name") != "Bot jaanch"}
    st = {k: (svc.lead_state(k).get("status") or "new") for k in LL}
    today = [k for k, v in LL.items() if str(v.get("t", ""))[:10] == d]
    wk = [k for k, v in LL.items() if str(v.get("t", ""))[:10] >= w7]
    pay = svc._read("payments.jsonl")
    p_d = sum(int(p.get("amt") or 0) for p in pay if str(p.get("t", ""))[:10] == d)
    p_m = sum(int(p.get("amt") or 0) for p in pay if str(p.get("t", ""))[:7] == d[:7])
    soft = soft_leads()
    L_ = [f"📥 LEADS — {n.strftime('%d-%m-%Y %H:%M')}",
          f"Aaj: {len(today)} naye · 7 din: {len(wk)} · Kul: {len(LL)}   💰 Aaj ₹{p_d:,} · Mahina ₹{p_m:,}"]
    srcs = {}
    for k in wk:
        s_ = src_of(LL[k])
        srcs[s_] = srcs.get(s_, 0) + 1
    cm7 = sum(1 for x in soft if x["kind"] == "comment")
    dm7 = sum(1 for x in soft if x["kind"] == "DM")
    L_.append("Kahan se (7 din): " + (", ".join(f"{a} {b}" for a, b in sorted(srcs.items(), key=lambda z: -z[1])) or "-")
              + f" · comment (bina number) {cm7} · DM (bina number) {dm7}")
    rows = []
    for b in BRANDS:
        f_ = sum(1 for k in wk if brand_of(LL[k]) == b)
        c_ = sum(1 for x in soft if x["b"] == b and x["kind"] == "comment")
        m_ = sum(1 for x in soft if x["b"] == b and x["kind"] == "DM")
        rows.append(f"{_bn(b)}: form {f_} · comment {c_} · DM {m_}")
    nb = sum(1 for k in wk if not brand_of(LL[k]))
    L_.append("Brand (7 din): " + " | ".join(rows) + f" | bina brand (website/Google) {nb}")
    cnt = {}
    for k, s_ in st.items():
        cnt[s_] = cnt.get(s_, 0) + 1
    L_.append("Haal: " + " · ".join(f"{NEXT.get(s_, s_).split()[0]} {s_} {cnt[s_]}" for s_ in OPEN if cnt.get(s_)))
    act = sorted([k for k in LL if st[k] in OPEN and st[k] != "delivered"], key=lambda k: str(LL[k].get("t", "")))
    kb, btn = [], []
    L_.append("")
    L_.append(f"👉 ABHI KARNA ({len(act)}) - purana pehle:" if act else "👉 Koi khula kaam nahi 🎉")
    for i, k in enumerate(act[:10], 1):
        v = LL[k]
        try:
            age_h = (n - datetime.datetime.fromisoformat(str(v["t"]).replace("Z", "+00:00"))).total_seconds() / 3600
        except Exception:
            age_h = 0
        age = f"{int(age_h)} ghante" if age_h < 48 else f"{int(age_h / 24)} din"
        kaam = (v.get("service") or v.get("message") or "")[:40].replace("\n", " ")
        L_.append(f"{i}. {k} · {str(v.get('name', ''))[:14]} · {kaam} · {age} · {_bn(brand_of(v)) if brand_of(v) else src_of(v)}"
                  f"\n    ➡ {NEXT.get(st[k], st[k])}")
        btn.append((f"{i}. {str(v.get('name', ''))[:10] or k[-4:]}", f"lb:o:{k}"))
    for j in range(0, len(btn), 3):
        kb.append(btn[j:j + 3])
    if len(act) > 10:
        L_.append(f"…aur {len(act) - 10} ('📂 Khule kaam')")
    if soft:
        L_.append("")
        L_.append(f"💬 Comment/DM - kaam poocha, number abhi nahi ({len(soft)}):")
        sb = []
        for i, x in enumerate(soft[-6:], 1):
            age_h = (n - datetime.datetime.fromisoformat(str(x["t"])[:19]).replace(tzinfo=n.tzinfo)).total_seconds() / 3600
            L_.append(f"{'⏰' if age_h > 24 else '•'} {x['kind']} {_bn(x['b'])} {str(x['pf'] or '').upper()} · {str(x['who'])[:14]}: "
                      f"\"{x['text'][:60]}\" · {'bot ne jawab diya' if x['auto'] else 'jawab baaki'} · {int(age_h)} ghante")
            sb.append((f"✅ {i} ho gaya", f"lb:cd:{x['id'][-40:]}"))
        for j in range(0, len(sb), 3):
            kb.append(sb[j:j + 3])
        L_.append("(⏰ = 24 ghante se form nahi bhara; number mile to 'manual naam 98xxxxxxxx kaam')")
    pm = state.get("dm_perm") or {}
    if pm:
        L_.append("")
        L_.append("📨 DM padhne ki Meta ijaazat abhi nahi: " + ", ".join(sorted(pm)) + " - 'dm ijaazat' likhiye (1 baar ka tareeka)")
    kb.append([("🔄 Taaza", "lb:r"), ("📊 Aaj ka hisaab", "lb:t")])
    return "\n".join(L_), {"inline_keyboard": [[{"text": t, "callback_data": c[:64]} for t, c in r] for r in kb]}


def show():
    from . import tg
    t, kb = text_and_kb()
    return tg.say(t[:4000], kb)


def on_cb(rest, run):
    from . import tg, svc
    op, _, arg = rest.partition(":")
    if op == "r":
        return show()
    if op == "t":
        return tg.say(svc.today_report())
    if op == "o":
        L = svc.leads().get(arg)
        if not L:
            return tg.say(f"❓ {arg} nahi mila")
        hello = svc._wa(L["phone"], f"Namaste {L.get('name', '')} ji 🙏 Sab Hisaab se. Aapka kaam mila ({arg}). Abhi baat kar sakte hain?")
        return tg.say(svc.lead_brief(arg) + f"\n➡ {NEXT.get(svc.lead_state(arg).get('status') or 'new', '')}",
                      svc._kb([[("💬 WhatsApp", hello), ("📞 Baat hui", f"sv:cu:{arg}"), ("📵 Nahi uthaya", f"sv:cn:{arg}")],
                               [("🧾 Rate wala card", f"lb:d:{arg}"), ("🔇 Band (test/bekaar)", f"lb:x:{arg}")]]))
    if op == "d":
        return svc.draft(arg)
    if op == "x":
        svc._event(arg, status="lost", by="owner", why="leads se band")
        svc._push(arg, status="lost")
        return tg.say(f"🔇 {arg} band (customer ko koi sandesh nahi gaya).")
    if op == "cd":
        state.update("lb_done", lambda L: ((L or []) + [x["id"] for x in soft_leads(30) if x["id"].endswith(arg)])[-500:], [])
        return tg.say("✅ Ho gaya - Leads se hata.")
    return None


def on_text(t, run):
    from . import tg
    tl = t.lower().strip()
    if t == "📥 Leads" or tl in ("leads", "lead", "lead box", "aaj ki leads", "kitni lead", "kitni lead aayi", "kitne lead aaye", "sab lead"):
        show()
        return True
    if tl in ("dm ijaazat", "dm permission", "dm ijazat"):
        tg.say("📨 DM ka 1 baar ka tareeka (Meta):\n1) developers.facebook.com → aapka app → Permissions: 'pages_messaging' aur "
               "'instagram_manage_messages' jodiye (Standard access apne page ke liye kaafi).\n2) Phir page token dobara banaiye "
               "('⚙️ Channel setup' wala tareeka) - nayi permission token mein aati hai.\n3) Bot 5 min mein khud jaanch lega; "
               "Leads mein 'DM ijaazat nahi' hat jayega.\nNiyam: bot sirf usi ko jawab deta hai jisne khud message kiya, 24 ghante ke "
               "andar, ek baar - koi bulk/cold DM nahi.")
        return True
    if tl in ("dm band", "dm jawab band"):
        state.put("dm_on", False)
        tg.say("⏸ DM ka apne-aap jawab band (padhna + Leads mein dikhna chalu). Wapas: 'dm chalu'")
        return True
    if tl in ("dm chalu", "dm jawab chalu"):
        state.put("dm_on", True)
        tg.say("✅ DM ka apne-aap jawab chalu (sirf jisne khud likha, 24 ghante mein ek baar).")
        return True
    return False


# ---------------------------------------------------------------- DM (Messenger + Instagram)
def _dm_reply(u, has_phone, text, pf):
    from . import svc
    dev = bool(re.search(r"[ऀ-ॿ]", text or ""))
    site = "sabhisaab.com/services-list"
    if has_phone:
        return ("धन्यवाद 🙏 आपका काम मिल गया, हम जल्दी फ़ोन/WhatsApp करेंगे। — सब हिसाब सर्विसेज़" if dev else
                "Dhanyavaad 🙏 Aapka kaam mil gaya, hum jaldi call/WhatsApp karenge. — Sab Hisaab Services")
    if u.get("intent") == "kaam" and u.get("item"):
        it = svc.rates()["by"][u["item"]]
        nm = re.split(r"[(+]|\s-\s", it["name"])[0].strip()
        return (f"नमस्ते 🙏 जी, {nm} हो जाएगा, ₹{it['price']:,} से। अपना मोबाइल नंबर यहीं लिख दीजिए - बात करके लिखित रेट देंगे। "
                f"या फ़ॉर्म: {site}" if dev else
                f"Namaste 🙏 Ji, {nm} ho jayega - ₹{it['price']:,} se. Apna mobile number yahin likh dijiye, baat karke likhit rate denge. "
                f"Ya form: {site}")
    return ("नमस्ते 🙏 सब हिसाब सर्विसेज़ - कोई भी डिजिटल काम ₹10 से शुरू। काम और मोबाइल नंबर लिख दीजिए, हम बात करेंगे। "
            f"पूरी लिस्ट: {site}" if dev else
            "Namaste 🙏 Sab Hisaab Services - koi bhi digital kaam ₹10 se shuru. Kaam aur mobile number likh dijiye, hum baat karenge. "
            f"Poori list: {site}")


def dm_check():
    """Har 5 min: dono platform ke naye DM (jo page ko aaye). Ijaazat na ho to us platform par 24 ghante ruk."""
    from . import meta as M, svc, svccomment as SC
    try:
        from . import igguard
    except Exception:
        igguard = None
    seen = set(state.get("dm_seen") or [])
    perm = dict(state.get("dm_perm") or {})
    replied = dict(state.get("dm_replied") or {})
    now_t = time.time()
    new_seen = []
    for b in BRANDS:
        bi = M.brand_info(b)
        if not bi or not bi.get("page_id"):
            continue
        for pf in ("fb", "ig"):
            key = f"{_bn(b)} {pf.upper()}"
            if now_t - float((state.get("dm_perm_at") or {}).get(key, 0)) < 86400:
                continue
            if pf == "ig" and (not bi.get("ig_id") or (igguard and igguard.off(b))):
                continue
            try:
                kw = {"fields": "id,updated_time,messages.limit(3){id,message,from,created_time}", "limit": 10}
                if pf == "ig":
                    kw["platform"] = "instagram"
                convs = M._get(f"/{bi['page_id']}/conversations", bi["page_token"], **kw).get("data", [])
                perm.pop(key, None)
            except Exception as e:
                s = str(e)
                if re.search(r"\(#(10|200|230|3|190)\)|permission|pages_messaging|instagram_manage_messages", s, re.I):
                    perm[key] = s[:80]
                    state.update("dm_perm_at", lambda d, k=key: {**(d or {}), k: now_t}, {})
                else:
                    log(f"dm {key}: {s[:150]}")
                continue
            for cv in convs:
                for m in (cv.get("messages") or {}).get("data", []):
                    mid = m.get("id")
                    fr = m.get("from") or {}
                    if not mid or mid in seen or fr.get("id") in (bi.get("page_id"), bi.get("ig_id")):
                        continue
                    seen.add(mid)
                    new_seen.append(mid)
                    try:
                        ct = datetime.datetime.strptime(m.get("created_time", "")[:19], "%Y-%m-%dT%H:%M:%S").replace(
                            tzinfo=datetime.timezone.utc).timestamp()
                    except Exception:
                        ct = now_t
                    if now_t - ct > 86400:                    # 24 ghante se purana: Meta jawab ki ijaazat nahi deta
                        continue
                    txt = str(m.get("message") or "")[:1000]
                    who = (fr.get("name") or fr.get("username") or "")[:40]
                    u = SC.understand(txt) if txt else {"intent": "unclear"}
                    ph = PHONE.search(txt)
                    row = {"id": f"dm{mid[-30:]}", "t": svc.now().isoformat(timespec="seconds"), "pf": pf, "b": b, "who": who,
                           "text": txt[:300], "item": u.get("item"), "thread": cv.get("id")}
                    if ph:
                        try:
                            row["lead"] = svc.manual_add(who or "DM customer", ph.group(1), f"[{pf.upper()} DM {_bn(b)}] {txt}",
                                                         how=f"dm-{pf}-{b}")
                        except Exception as e:
                            log(f"dm lead: {e}")
                    if (state.get("dm_on", True) and u.get("intent") not in ("abuse", "spam") and txt
                            and now_t - float(replied.get(cv.get("id"), 0)) > 86400):
                        try:
                            M._post(f"/{bi['page_id']}/messages", bi["page_token"], recipient=__import__("json").dumps({"id": fr.get("id")}),
                                    messaging_type="RESPONSE",
                                    message=__import__("json").dumps({"text": _dm_reply(u, bool(ph), txt, pf)[:900]}))
                            replied[cv.get("id")] = now_t
                            row["replied"] = True
                        except Exception as e:
                            log(f"dm reply {key}: {str(e)[:150]}")
                    svc._append("dm.jsonl", row)
    state.put("dm_seen", (list(state.get("dm_seen") or []) + new_seen)[-3000:])
    state.put("dm_perm", perm)
    state.put("dm_replied", {k: v for k, v in replied.items() if now_t - v < 3 * 86400})


def tick(run):
    if state.get("paused"):
        return
    t = time.time()
    if t - float(state.get("lb_dm_at") or 0) > 300:
        state.put("lb_dm_at", t)
        run(dm_check)
