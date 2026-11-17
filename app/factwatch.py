"""v2.6.1 (owner 9 Nov: 'sarkar dar badle to website par khud badle, bina insaan'): SARKARI-DAR WATCHER.

Kya karta hai:
- Har darj dar (PPF, NSC, SSY, SCSS, KVP, POMIS, EPF) ka website par ABHI ka number padhta hai (tools.js + calculator page).
- Google-search wala Gemini se aaj ki dar + srot; sirf sarkari srot (gov.in / nic.in / rbi.org.in) maane jaate hain.
- Doosri jaanch: wahi sarkari page khud khol kar dekhta hai ki naya number scheme ke naam ke paas likha hai.
- Do alag din-samay (kam se kam 6 ghante ke farak) par wahi naya number mile tabhi badlaav (ek baar ki galti se kuch nahi badalta).
- Badlaav SIRF darj jagah par: tools.js mein us tool ka 'Byaj %' default + label, us calculator page ka input, aur
  usi scheme ke page par scheme-naam ke 50 akshar ke andar likha purana % (saal likha ho to nahi - wo itihaas hai).
- Website ZIP -> audit (website.apply_zip, force=False). Fail = kuch live nahi. Phir calculator test.
- Shak ho (srot sarkari nahi, do jaanch alag, number ajeeb) to kuch nahi badalta - owner ko ek alert + PENDING.
Kabhi nahi: bina srot ka number, ek hi jaanch par badlaav, poori site par andha find-replace, publish date peeche karna.
"""
import datetime
import json
import re
import time

import requests

from . import state, tg
from .log import log

OFFICIAL = (".gov.in", ".nic.in", "rbi.org.in", "nsiindia.gov.in", "indiapost.gov.in", "epfindia.gov.in", "pib.gov.in")
MIN_GAP = 6 * 3600          # do jaanch ke beech kam se kam
MAX_JUMP = 1.5              # ek baar mein isse zyada % badlaav = shak (owner se poochho)

# key: (naam, tools.js id, calculator page, scheme-shabd regex, kis kis page par text, Gemini ke liye naam)
FACTS = {
    "ppf": ("PPF", "ppf", "ppf-calculator", r"PPF|Public Provident", ("ppf-calculator", "ppf-extension-calculator", "post-office-guide"),
            "Public Provident Fund (PPF)"),
    "nsc": ("NSC", "nsc", "nsc-calculator", r"NSC|National Savings Certificate", ("nsc-calculator", "post-office-guide"),
            "National Savings Certificate (NSC)"),
    "ssy": ("Sukanya Samriddhi", "ssy", "sukanya-samriddhi-calculator", r"Sukanya|SSY", ("sukanya-samriddhi-calculator", "post-office-guide"),
            "Sukanya Samriddhi Yojana (SSY)"),
    "scss": ("SCSS", "scss", "scss-calculator", r"SCSS|Senior Citizen", ("scss-calculator", "post-office-guide"),
             "Senior Citizens Savings Scheme (SCSS)"),
    "kvp": ("KVP", "kvp", "kvp-calculator", r"KVP|Kisan Vikas", ("kvp-calculator", "post-office-guide"), "Kisan Vikas Patra (KVP)"),
    "pomis": ("Post Office MIS", "pomis", "post-office-mis-calculator", r"POMIS|Post Office MIS|\bMIS\b",
              ("post-office-mis-calculator", "post-office-mis-ka-hisaab", "post-office-guide"), "Post Office Monthly Income Scheme (POMIS)"),
    "epf": ("EPF", "epf", "epf-calculator", r"EPF|Provident Fund", ("epf-calculator",), "EPF interest rate (EPFO, latest declared)"),
}

ASK = """Today is {today}. Give the CURRENT official interest rate (percent per year) in India for: {items}.
Use only official Government of India sources (finance ministry / India Post / NSI / PIB / EPFO). For small savings schemes give the
rate for the current quarter. Return ONLY JSON: {{"rates": [{{"key": "<key>", "rate": <number>, "period": "<quarter or FY>",
"source": "<official url>"}}]}} with keys exactly: {keys}. If unsure about one, omit it."""


# ---------------- website par abhi kya likha hai ----------------
def _site():
    from .website import DIR
    return DIR / "site"


def tool_block(js, tid):
    m = re.search(r"\{id:'" + re.escape(tid) + r"'\s*,.*?fields:`(.*?)`", js, re.S)
    return m


def current_value(js, tid):
    m = tool_block(js, tid)
    if not m:
        return None
    r = re.search(r'<input id="r"[^>]*value="([\d.]+)"', m.group(1))
    return r.group(1) if r else None


def site_values():
    try:
        js = (_site() / "tools.js").read_text(encoding="utf-8")
    except Exception:
        return {}
    return {k: current_value(js, v[1]) for k, v in FACTS.items()}


# ---------------- do jaanch ----------------
def _num(x):
    try:
        v = float(str(x).strip().rstrip("%"))
        return v if 0.5 <= v <= 20 else None
    except Exception:
        return None


def official(src):
    s = str(src or "").lower()
    return any(o in s for o in OFFICIAL)


def ask_rates(keys=None):
    """Google-search Gemini se -> {key: (rate, period, [srot])}. Sirf sarkari srot wale."""
    from .brain import ask_grounded, _json
    keys = list(keys or FACTS)
    items = "; ".join(f"{k} = {FACTS[k][5]}" for k in keys)
    txt, srcs = ask_grounded(ASK.format(today=datetime.date.today(), items=items, keys=", ".join(keys)))
    out = {}
    try:
        data = _json(txt)
    except Exception:
        return out
    rows = data.get("rates") if isinstance(data, dict) else data
    for r in rows or []:
        if not isinstance(r, dict) or r.get("key") not in FACTS:
            continue
        v = _num(r.get("rate"))
        gov = [s for s in ([r.get("source")] + list(srcs)) if official(s)]
        if v is not None and gov:
            out[r["key"]] = (v, str(r.get("period", ""))[:40], gov[:3])
    return out


def page_confirms(text, key, value):
    """Sarkari page ke text mein scheme ke naam ke 160 akshar ke andar ye % likha hai?"""
    rx = re.compile(FACTS[key][3], re.I)
    t = re.sub(r"<[^>]+>", " ", text or "")
    t = re.sub(r"\s+", " ", t)
    want = {f"{value:g}", f"{value:.1f}", f"{value:.2f}"}
    for m in rx.finditer(t):
        win = t[m.start(): m.start() + 160]
        if any(re.search(r"(?<![\d.])" + re.escape(w) + r"(?![\d])", win) for w in want):
            return True
    return False


def _fetch(url):
    u = url.split(" ")[-1] if " " in url else url
    r = requests.get(u, timeout=30, headers={"User-Agent": "Mozilla/5.0 SabhisaabBot-FactWatch/1.0"})
    return r.url, r.text if r.ok else ""


def second_check(key, value, sources):
    for s in sources:
        try:
            final, body = _fetch(s)
            if official(final) and page_confirms(body, key, value):
                return final
        except Exception as e:
            log(f"factwatch fetch: {str(e)[:80]}")
    return ""


# ---------------- website mein sirf darj jagah badlaav (bina network, test ho sake) ----------------
def patch_tools_js(js, tid, old, new):
    m = tool_block(js, tid)
    if not m:
        return js, 0
    blk = m.group(1)
    nb, n1 = re.subn(r'(<input id="r"[^>]*value=")' + re.escape(old) + r'(")', lambda x: x.group(1) + new + x.group(2), blk)
    nb, n2 = re.subn(r"(\(abhi\s*~?\s*)" + re.escape(old) + r"(\))", lambda x: x.group(1) + new + x.group(2), nb)
    return js[:m.start(1)] + nb + js[m.end(1):], n1 + n2


def fact_box(key, new, period, src, today):
    dom = re.sub(r"^https?://(www\.)?", "", (src or "").split(" ")[-1]).split("/")[0] or "sarkari srot"
    url = (src or "").split(" ")[-1]
    link = f'<a href="{url}" rel="noopener nofollow">{dom}</a>' if url.startswith("http") else dom
    return (f'<p class="upd" id="taaza-dar">Taaza sarkari dar{(" (" + period + ")") if period else ""}: <b>{new}%</b> saalana · '
            f'srot: {link} · bot ne jaancha: {today}. Neeche ke udaharan purani/maani gayi dar par ho sakte hain - apni rakam '
            f'aur dar upar calculator mein daalein.</p>')


def patch_page(html, key, old, new, today, period="", src="", own=False):
    """Calculator ka default input (sirf jahan wahi purana number ho) + (sirf scheme ke apne page par) bot ka 'Taaza dar'
    dabba H1 ke neeche. Lekh ke udaharan/table NAHI badalte - unke number purani dar par ganit kiye gaye hain (andha
    badalne se ganit galat ho jaata). Badla to dateModified aaj."""
    n = 0
    html, k = re.subn(r'(<input id="r"[^>]*value=")' + re.escape(old) + r'(")', lambda x: x.group(1) + new + x.group(2), html)
    n += k
    if own:
        box = fact_box(key, new, period, src, today)
        if 'id="taaza-dar"' in html:
            html = re.sub(r'<p class="upd" id="taaza-dar">.*?</p>', lambda x: box, html, count=1, flags=re.S)
            n += 1
        else:
            m = re.search(r"<h1\b[^>]*>.*?</h1>", html, re.S)
            if m:
                html = html[:m.end()] + box + html[m.end():]
                n += 1
    if n:
        html = re.sub(r'"dateModified":\s*"[\d-]+"', f'"dateModified": "{today}"', html)
    return html, n


def old_mentions(html, key, old):
    """Lekh mein purani dar kahan likhi hai (sirf batane ke liye - badalta nahi)."""
    t = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S))
    return sum(1 for m in re.finditer(FACTS[key][3], t) if re.search(r"(?<![\d.])" + re.escape(old) + r"\s?%", t[m.start():m.start() + 60]))


def build_patch(changes, today=None, meta=None, notes=None):
    """changes: {key: (old, new)} -> {repo_path: naya_text} (sirf jo sach mein badle). meta: {key: (period, src)}.
    notes (list) mein: kis page ke lekh mein purani dar ke udaharan bache (owner/Claude ke liye)."""
    meta = meta or {}
    today = today or str(datetime.date.today())
    d = _site()
    files = {}
    js = (d / "tools.js").read_text(encoding="utf-8")
    js0 = js
    for key, (old, new) in changes.items():
        js, _n = patch_tools_js(js, FACTS[key][1], old, new)
        for pg in FACTS[key][4]:
            f = d / f"{pg}.html"
            if not f.exists():
                continue
            cur = files.get(f"site/{pg}.html") or f.read_text(encoding="utf-8")
            per, src = meta.get(key, ("", ""))
            nh, k = patch_page(cur, key, old, new, today, per, src, own=(pg == FACTS[key][2]))
            if k:
                files[f"site/{pg}.html"] = nh
            if notes is not None:
                left = old_mentions(nh, key, old)
                if left:
                    notes.append(f"/{pg}: {FACTS[key][0]} ke {left} udaharan abhi {old}% par")
    if js != js0:
        files["site/tools.js"] = js
    if files:
        sm_f = d / "sitemap.xml"
        if sm_f.exists():
            sm = sm_f.read_text(encoding="utf-8")
            for p in files:
                if p.endswith(".html"):
                    slug = p[5:-5]
                    sm = re.sub(r"(<loc>https://sabhisaab\.com/" + re.escape(slug) + r"</loc>\s*<lastmod>)[\d-]+",
                                lambda x: x.group(1) + today, sm, count=1)
            files["site/sitemap.xml"] = sm
    return files


def mark_reviewed(key, day=None):
    """v2.6.3: website repo ke state/review_ok.json mein is dar ke page 'aaj jaanche gaye' - watch.py ka 90-din wala
    'data purana' alarm tabhi hatta hai jab dar sach mein sarkari srot se mili ho (tareekh ka dikhawa nahi)."""
    try:
        from .website import DIR
        f = DIR / "state" / "review_ok.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        d = json.loads(f.read_text()) if f.exists() else {}
        day = day or str(datetime.date.today())
        for pg in set(FACTS[key][4]) | {FACTS[key][2]}:
            d[pg] = day
        f.write_text(json.dumps(d, indent=1))
        return True
    except Exception as e:
        log(f"factwatch review_ok: {e}")
        return False


# ---------------- roz ka kaam ----------------
def due(now=None):
    """Teen mahine ki dar badalne ke dino (25 Mar-7 Apr, 25 Jun-7 Jul, 25 Sep-7 Oct, 25 Dec-7 Jan) mein roz, baaki Somvaar."""
    now = now or datetime.datetime.now()
    m, d = now.month, now.day
    window = (m in (3, 6, 9, 12) and d >= 25) or (m in (1, 4, 7, 10) and d <= 7)
    return (window or now.weekday() == 0 or bool(state.get("fact_seen"))   # naya number mila ho to agle din dobara jaanch
            or not state.get("fact_ran_once"))                              # v2.6.3: install ke baad pehli jaanch turant


def run(force=False):
    if not force and state.get("fact_day") == str(datetime.date.today()):
        return "factwatch: aaj ho chuka"
    if not force and not due():
        return "factwatch: aaj ka din nahi"
    state.put("fact_day", str(datetime.date.today()))
    state.put("fact_ran_once", True)
    have = site_values()
    try:
        got = ask_rates([k for k in FACTS if have.get(k)])
    except Exception as e:
        state.put("fact_last", {"t": time.time(), "err": str(e)[:200]})
        return f"factwatch: Google jaanch nahi hui ({str(e)[:100]}) - kal phir"
    seen = dict(state.get("fact_seen") or {})
    ready, doubt = {}, []
    for k, (v, period, srcs) in got.items():
        old = have.get(k)
        if not old:
            continue
        if abs(float(old) - v) < 0.001:
            seen.pop(k, None)
            if second_check(k, v, srcs):          # v2.6.3: sarkari page par wahi dar = page ki dar sach mein jaanchi gayi
                mark_reviewed(k)
            continue
        if abs(float(old) - v) > MAX_JUMP:
            doubt.append(f"{FACTS[k][0]}: site {old}% vs mila {v:g}% (bahut bada farak)")
            continue
        conf = second_check(k, v, srcs)
        if not conf:
            doubt.append(f"{FACTS[k][0]}: {v:g}% ({period}) - sarkari page par khud pakka nahi ho paya")
            continue
        prev = seen.get(k) or {}
        if prev.get("v") == v and time.time() - float(prev.get("t", 0)) >= MIN_GAP:
            ready[k] = (old, f"{v:g}", period, conf)
        elif prev.get("v") != v:
            seen[k] = {"v": v, "t": time.time(), "src": conf}
    state.put("fact_seen", seen)
    state.put("fact_last", {"t": time.time(), "got": {k: v[0] for k, v in got.items()}, "site": have})
    msg = []
    if ready:
        msg.append(apply(ready))
    if doubt:
        key = "|".join(sorted(doubt))
        if state.get("fact_doubt_key") != key:
            state.put("fact_doubt_key", key)
            tg.alert("yellow", "🧮 Sarkari dar - shak, website NAHI badli (aap ek baar dekh lein):\n• " + "\n• ".join(doubt))
        msg.append(f"shak {len(doubt)}")
    if seen and not ready:
        msg.append("naya number pehli baar mila - " + ", ".join(FACTS[k][0] for k in seen) + " (6+ ghante baad dobara jaanch ke baad hi badlega)")
    return "factwatch: " + (" | ".join(msg) if msg else "sab dar sahi ✅")


def apply(ready):
    import zipfile
    from . import website, diary
    from .config import DATA
    try:
        website.sync()
    except Exception as e:
        log(f"factwatch sync: {e}")
    notes = []
    files = build_patch({k: (o, n) for k, (o, n, _p, _s) in ready.items()}, meta={k: (p, s_) for k, (_o, _n, p, s_) in ready.items()},
                        notes=notes)
    if not files:
        return "factwatch: badalne ki jagah nahi mili"
    z = DATA / "factwatch.zip"
    with zipfile.ZipFile(z, "w") as zz:
        for p, body in files.items():
            zz.writestr(p, body)
    r = website.apply_zip(z, force=False)
    z.unlink(missing_ok=True)
    lines = [f"• {FACTS[k][0]}: {o}% → {n}% ({p}) srot: {s[:90]}" for k, (o, n, p, s) in ready.items()]
    if str(r).startswith("✅"):
        seen = dict(state.get("fact_seen") or {})
        for k in ready:
            seen.pop(k, None)
        state.put("fact_seen", seen)
        state.update("fact_history", lambda h: ((h or []) + [{"t": str(datetime.datetime.now())[:16], "ch": lines}])[-50:], [])
        diary.add("setting", "sarkari dar badli: " + "; ".join(lines)[:300])
        try:
            ct = website.verify_calculators_smoke()
        except Exception as e:
            ct = f"calculator test nahi chala: {e}"
        tg.alert("green", "🧮 Sarkari dar badli - website apne aap update (audit pass):\n" + "\n".join(lines) +
                 f"\nBadle: {', '.join(p for p in files if p != 'site/sitemap.xml')}\n{ct[:300]}"
                 + ("\n\nℹ️ Lekh ke udaharan purani dar par ganit kiye gaye hain (andha nahi badle):\n• " + "\n• ".join(notes[:8])
                    + "\nInhe naye ganit ke saath badalwana ho to Claude ko: 'dar udaharan theek karo'" if notes else ""))
        if notes:
            from . import tasks as _T
            try:
                _T.add("[Claude] Sarkari dar badli - lekh ke udaharan naye ganit se: " + "; ".join(notes[:6]))
            except Exception:
                pass
        return f"{len(ready)} dar badli ✅"
    tg.alert("yellow", "🧮 Sarkari dar badli par website audit mein ruki (kuch live nahi hua):\n" + "\n".join(lines) + f"\n{str(r)[:400]}")
    return "audit mein ruka"


def report():
    have = site_values()
    last = state.get("fact_last") or {}
    got = last.get("got") or {}
    L = ["🧮 SARKARI DAR (website par abhi | aakhri jaanch mein mila)"]
    for k, v in FACTS.items():
        L.append(f"• {v[0]}: {have.get(k) or '-'}% | {got.get(k, '-')}")
    if last.get("t"):
        L.append(f"Aakhri jaanch: {datetime.datetime.fromtimestamp(last['t']):%d %b %H:%M}" + (f" (galti: {last['err']})" if last.get("err") else ""))
    for h in (state.get("fact_history") or [])[-3:]:
        L.append(f"Badla {h['t']}: " + "; ".join(h["ch"])[:200])
    L.append("Apne aap: teen-mahine ke badlaav ke dino (25 Mar-7 Apr waghairah) mein roz, baaki har Somvaar. Abhi: 'dar jaancho'.")
    return "\n".join(L)
