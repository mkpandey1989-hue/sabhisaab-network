"""v3.9.5 (owner 25 Nov 2026): "bonus wale ka system banao taki sab jagah same wahi update ho sake" + "refferal wale ke liye data
chahiye hoga taki usko benefit mil paaye - record rakhna padega".

EK SROT (single source) - referral bonus ke saare niyam yahin:
  - svc.py (bonus banana / dena / kaatna / expire), customer ka gupt page (q.html), website (terms#Referral, services-list FAQ +
    FAQ schema, svc-offer.js -> window.SVC_BONUS), services video ki awaaz, owner ki report - sab isi se padhte hain.
  - Dost ki chhoot (REF code) aur brand code ki chhoot svc_rates.json (sha-taala) ke 'discount' se aati hai - wo yahan sirf PADHI jaati
    hai (badalna = generator, docs/SERVICES_HANDOVER.md).
  - Niyam badalna: 'bonus set <naam> <ank>' -> dohri pushti -> state 'bonus_rules' -> website files agli sync (turant) + deploy.
RECORD (taaki bonus kabhi na khoye):
  - data/services/referral.jsonl = har bonus (kisko, kis order se, kitna, kab pakka, kab tak, istemaal/radd) - zindagi bhar (bahi).
  - Jis code-wale ka bonus baaki (intezaar/chalu) hai, uska naam + number 90-din safai mein NAHI mitta jab tak bonus khatam na ho
    (privacy page section 7 mein likha). Bonus khatam -> agli raat safai.
"""
import datetime
import re

from . import state

DEFAULT = {"ref_pct": 10, "ref_min_bill": 300, "ref_max": 500, "ref_use_pct": 10, "ref_expiry_days": 90, "ref_wait_days": 7,
           "ref_month_cap": 5}
LIMITS = {"ref_pct": (1, 30), "ref_min_bill": (0, 5000), "ref_max": (50, 2000), "ref_use_pct": (1, 50), "ref_expiry_days": (30, 365),
          "ref_wait_days": (1, 30), "ref_month_cap": (1, 20)}
LABEL = {"ref_pct": "dost ke chukaye bill ka bonus %", "ref_min_bill": "kam se kam bill (₹)", "ref_max": "ek bonus max (₹)",
         "ref_use_pct": "agle bill ka max kitna % kate", "ref_expiry_days": "bonus kitne din chale", "ref_wait_days": "payment ke kitne din baad pakka",
         "ref_month_cap": "ek mahine mein max bonus"}
HI_NUM = {5: "पाँच", 10: "दस", 15: "पंद्रह", 20: "बीस", 25: "पच्चीस", 30: "तीस"}


def R():
    """Abhi ke niyam (default + owner ke pakke badlav)."""
    r = dict(DEFAULT)
    for k, v in (state.get("bonus_rules") or {}).items():
        if k in DEFAULT:
            try:
                r[k] = int(v)
            except Exception:
                pass
    return r


def disc():
    """REF code (dost) aur brand code ki chhoot - svc_rates.json se (sirf padhna)."""
    try:
        from . import svc
        D = svc.rates()["discount"]
        return {"friend_pct": int(D.get("ref", 10)), "brand_pct": int(D.get("brand", 10)), "max_pct": int(D.get("max", 25))}
    except Exception:
        return {"friend_pct": 10, "brand_pct": 10, "max_pct": 25}


# ---------------------------------------------------------------- har jagah ka ek hi text
def terms_text():
    r, d = R(), disc()
    return (f"referral code se aaye naye customer ko pehle kaam par {d['friend_pct']}% tak chhoot milti hai. Code dene wale ko naye "
            f"customer ke chukaye bill ka {r['ref_pct']}% bonus milta hai - sirf ₹{r['ref_min_bill']} ya usse bade bill par, ek bonus mein "
            f"zyada se zyada ₹{r['ref_max']}. Bonus naye customer ka payment hone ke {r['ref_wait_days']} din baad pakka hota hai (refund ho "
            f"jaye to radd), agle paid kaam ke bill ka zyada se zyada {r['ref_use_pct']}% kaat sakta hai, {r['ref_expiry_days']} din tak "
            f"chalta hai, aur nakad nahi milta. Apne hi number/device se code nahi chalta; mahine mein zyada se zyada {r['ref_month_cap']} bonus.")


def faq_text():
    r, d = R(), disc()
    return (f"Form bhejne par aapko ek REF code milta hai. Dost us code se kaam karwaye to dost ko pehle kaam par {d['friend_pct']}% "
            f"chhoot milti hai, aur dost ke chukaye bill ka {r['ref_pct']}% aapko bonus milta hai (₹{r['ref_min_bill']} ya usse bade bill "
            f"par, ek baar mein max ₹{r['ref_max']}). Bonus dost ka payment hone ke {r['ref_wait_days']} din baad pakka hota hai, agle paid "
            f"kaam ke bill ka max {r['ref_use_pct']}% kaat sakta hai aur {r['ref_expiry_days']} din tak chalta hai. Ek hi phone/device se "
            "apna hi code nahi chalta, aur bonus nakad nahi milta. Aapka bonus aapke gupt kaam-page par dikhta hai.")


def page_text():
    """Customer ke gupt page (q.html) ka chhota roop."""
    r, d = R(), disc()
    return (f"se dost ko pehle kaam par {d['friend_pct']}% off — aapko uske chukaye bill ka {r['ref_pct']}% bonus "
            f"(₹{r['ref_min_bill']}+ bill par, max ₹{r['ref_max']}, agle kaam mein, {r['ref_expiry_days']} din tak).")


def say_hi(short=False):
    """Services video ki awaaz (Kokoro) - ank shabd mein."""
    p = R()["ref_pct"]
    w = HI_NUM.get(p, str(p))
    return f"दोस्त को भेजिए, {w} प्रतिशत आपका।" if short else f"दोस्त को भेजिए, उसके बिल का {w} प्रतिशत आपका।"


def js():
    import json
    r, d = R(), disc()
    return "window.SVC_BONUS=" + json.dumps({**r, **d}, ensure_ascii=False) + ";\n"


# ---------------------------------------------------------------- website par ek jaisa (terms + services-list + schema)
TERMS_RX = re.compile(r"(<li><b>Referral:</b>\s*)(.*?)(</li>)", re.S)
FAQ_Q = "Referral code kaise chalta hai?"
FAQ_RX = re.compile(r"(<summary>" + re.escape(FAQ_Q) + r"</summary><p>)(.*?)(</p>)", re.S)
LD_RX = re.compile(r'("name": "' + re.escape(FAQ_Q) + r'", "acceptedAnswer": \{"@type": "Answer", "text": ")((?:[^"\\]|\\.)*)(")')


def sync_html(name, html):
    """-> naya html (ya wahi). Sirf referral wali line/FAQ badalti hai - baaki page ka ek akshar nahi."""
    import html as _h
    import json
    if name == "terms.html":
        return TERMS_RX.sub(lambda m: m.group(1) + _h.escape(terms_text(), quote=False) + m.group(3), html, count=1)
    if name == "services-list.html":
        out = FAQ_RX.sub(lambda m: m.group(1) + _h.escape(faq_text(), quote=False) + m.group(3), html, count=1)
        return LD_RX.sub(lambda m: m.group(1) + json.dumps(faq_text(), ensure_ascii=False)[1:-1] + m.group(3), out, count=1)
    return html


def sync_site(site_dir):
    """website repo ke site/ mein terms + services-list ko niyam ke hisaab se. -> badli file ke naam."""
    import pathlib
    ch = []
    for nm in ("terms.html", "services-list.html"):
        f = pathlib.Path(site_dir) / nm
        if not f.exists():
            continue
        old = f.read_text(encoding="utf-8")
        new = sync_html(nm, old)
        if new != old:
            f.write_text(new, encoding="utf-8")
            ch.append(nm)
    return ch


# ---------------------------------------------------------------- record / report
def _rows():
    from . import svc
    return svc._read("referral.jsonl")


def active_referrers():
    """Jinka bonus abhi baaki hai (intezaar ya chalu, expire nahi) -> {lead_id: kab tak}. 90-din safai inhe nahi mitati."""
    r = R()
    now_ = datetime.datetime.now().isoformat()
    lim = (datetime.datetime.now() - datetime.timedelta(days=r["ref_expiry_days"])).isoformat()
    out = {}
    for x in _rows():
        st = x.get("status")
        if st == "wait" or (st == "given" and str(x.get("given_at", x.get("due", ""))) >= lim):
            till = str(x.get("given_at") or x.get("due") or now_)[:10]
            try:
                till = str(datetime.date.fromisoformat(till) + datetime.timedelta(days=r["ref_expiry_days"]))
            except Exception:
                pass
            out[x.get("to")] = max(out.get(x.get("to"), ""), till)
    return out


def balance(lid_or_phone):
    """-> {'amt': chalu bonus, 'wait': intezaar wala, 'till': kab tak, 'used': ab tak kata}"""
    from . import svc
    by = svc.leads()
    ph = (by.get(lid_or_phone) or {}).get("phone") or lid_or_phone
    r = R()
    lim = (datetime.datetime.now() - datetime.timedelta(days=r["ref_expiry_days"])).isoformat()
    amt = wait = used = 0
    till = ""
    for x in _rows():
        to = by.get(x.get("to")) or {}
        if not ph or to.get("phone") != ph:
            continue
        if x.get("status") == "wait":
            wait += int(x.get("credit") or 0)
        elif x.get("status") == "given" and str(x.get("given_at", x.get("due", ""))) >= lim:
            amt += int(x.get("credit") or 0)
            try:
                t_ = str(datetime.date.fromisoformat(str(x.get("given_at", x.get("due")))[:10]) + datetime.timedelta(days=r["ref_expiry_days"]))
                till = max(till, t_)
            except Exception:
                pass
        elif x.get("status") == "used":
            used += int(x.get("credit") or 0)
    return {"amt": amt, "wait": wait, "till": till, "used": used}


def status_text():
    r, d = R(), disc()
    rows = _rows()
    c = {k: [x for x in rows if x.get("status") == k] for k in ("wait", "given", "used", "expired", "cancelled")}
    L = ["🎟 BONUS / REFERRAL - ek hi niyam, har jagah (website terms + rate list + gupt page + video + bill)",
         f"• Dost ko pehle kaam par {d['friend_pct']}% chhoot (REF code) | brand code {d['brand_pct']}% | sab milakar max {d['max_pct']}%",
         f"• Code wale ko: dost ke chukaye bill ka {r['ref_pct']}% (₹{r['ref_min_bill']}+ bill, max ₹{r['ref_max']}), "
         f"{r['ref_wait_days']} din baad pakka, agle bill ka max {r['ref_use_pct']}%, {r['ref_expiry_days']} din, mahine mein max {r['ref_month_cap']}",
         "",
         f"📒 Record: intezaar {len(c['wait'])} (₹{sum(int(x.get('credit') or 0) for x in c['wait'])}) · chalu {len(c['given'])} "
         f"(₹{sum(int(x.get('credit') or 0) for x in c['given'])}) · istemaal {len(c['used'])} · khatam {len(c['expired'])} · radd {len(c['cancelled'])}"]
    try:
        from . import svc
        by = svc.leads()
        act = active_referrers()
        if act:
            L.append("Jinka bonus baaki (naam/number tab tak surakshit):")
            for lid, till in sorted(act.items(), key=lambda x: x[1])[:10]:
                x = by.get(lid) or {}
                b = balance(lid)
                L.append(f"  • {lid} {str(x.get('name') or '-').split(' ')[0]} (…{str(x.get('phone') or '')[-4:]}) ₹{b['amt']} chalu"
                         + (f" + ₹{b['wait']} intezaar" if b["wait"] else "") + f" · {till} tak")
    except Exception as e:
        L.append(f"(record padh nahi paya: {str(e)[:60]})")
    L += ["", "Badalna: 'bonus set ref_pct 15' (dohri pushti) - phir website + gupt page + video apne aap. Ek customer: 'bonus SH...' ya 'bonus 3651'"]
    return "\n".join(L)


def on_text(t):
    """Owner ke hukum. -> jawab text ya None."""
    from . import tg
    tl = (t or "").strip().lower()
    if tl in ("bonus", "bonus haal", "referral", "referral haal", "refferal", "refferal haal", "bonus system", "🎟 bonus"):
        return tg.say(status_text())
    m = re.fullmatch(r"bonus set (\w+) (\d+)", tl)
    if m:
        k, v = m.group(1), int(m.group(2))
        if k not in DEFAULT:
            return tg.say("❓ Ye niyam nahi. Naam: " + ", ".join(f"{a} ({LABEL[a]})" for a in DEFAULT))
        lo, hi = LIMITS[k]
        if not lo <= v <= hi:
            return tg.say(f"⛔ {k} ki surakshit seema {lo}-{hi} hai (nuksan / jhootha vaada na ho).")
        state.put("bonus_pending", {"k": k, "v": v, "n": 1})
        return tg.say(f"🎟 {LABEL[k]}: {R()[k]} → {v}. Ye website (terms, rate list), gupt page aur video sab jagah badlega.\n"
                      "Pakka? likhein: 'bonus pakka' (do baar)")
    if tl == "bonus pakka":
        p = state.get("bonus_pending") or {}
        if not p:
            return tg.say("Koi badlav line mein nahi. Pehle: 'bonus set <naam> <ank>'")
        if p.get("n", 1) < 2:
            state.put("bonus_pending", {**p, "n": 2})
            return tg.say("⚠️ Dobara pakka? Purane customer ke diye bonus nahi badlenge, sirf aage ke. Phir likhein: 'bonus pakka'")
        state.update("bonus_rules", lambda d: {**(d or {}), p["k"]: p["v"]}, {})
        state.put("bonus_pending", {})
        state.put("svc_cfg_day4", "")                  # website files (svc-offer.js, gupt page, terms, rate list) turant dobara
        from . import diary
        diary.add("pakka", f"bonus {p['k']} = {p['v']}")
        return tg.say(f"✅ {LABEL[p['k']]} = {p['v']}. Website/gupt page agle 1-3 min mein, video kal se.")
    m = re.fullmatch(r"bonus (sh\w{6,12}|\d{4})", tl)
    if m:
        from . import svc
        key = m.group(1).upper()
        by = svc.leads()
        hit = [k for k, x in by.items() if k == key or str(x.get("phone") or "").endswith(key)]
        if not hit:
            return tg.say(f"❓ {key} ka koi customer nahi mila")
        b = balance(hit[0])
        x = by[hit[0]]
        return tg.say(f"🎟 {hit[0]} {str(x.get('name') or '-').split(' ')[0]} (…{str(x.get('phone') or '')[-4:]}) · code {x.get('ref', '-')}\n"
                      f"Chalu bonus ₹{b['amt']}" + (f" ({b['till']} tak)" if b["till"] else "") + f" · intezaar ₹{b['wait']} · ab tak kata ₹{b['used']}")
    return None
