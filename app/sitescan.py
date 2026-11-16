"""v2.5.3: website ka SIRF-PADHNE wala scan (kuch badalta nahi). Plan ke W1/W5/W8/B1/B2: toote related-link (naam != page),
patle page (<300 shabd), 'Reviewed on' tareekh, title/h1, zaroori pages par ad code. Sitemap ke har URL par dheere (0.6 s gap) GET.
Report docs/SITESCAN.md + Telegram saar. Command: 'site scan'. Ravivaar bhi apne aap. Koi page/ZIP/deploy nahi chhuta."""
import re
import time

import requests

from . import state
from .config import SITE, BASE as ROOT
from .log import log

STOP = {"calculator", "converter", "tool", "online", "free", "ka", "ki", "ke", "vs", "and", "aur", "the", "a", "of", "in", "se", "to", "kaise", "kya",
        "hisab", "hisaab", "sab", "padhein", "dekhein", "ye", "yeh", "ek", "ya", "hai"}
NO_AD = ("/privacy", "/terms", "/contact", "/disclaimer", "/thanks")
MIN_WORDS = 300
SKIP_PREFIX = ("/jawab",)            # bot ka apna page alag jaancha jata hai


def _tokens(t):
    t = re.sub(r"[^0-9a-z\u0900-\u097f]+", " ", (t or "").lower())
    return {w for w in t.split() if w not in STOP and len(w) > 1}


def _strip(html):
    for tag in ("script", "style", "nav", "header", "footer", "aside"):
        html = re.sub(rf"<{tag}\b.*?</{tag}>", " ", html, flags=re.S | re.I)
    return html


def main_html(html):
    m = re.search(r"<main\b.*?</main>", html, re.S | re.I)
    return _strip(m.group(0) if m else html)


def words(html):
    t = re.sub(r"<[^>]+>", " ", main_html(html))
    return len(re.findall(r"[0-9A-Za-z\u0900-\u097f]+", t))


def title_of(html):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I) or re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    return re.sub(r"<[^>]+>|\s+", " ", m.group(1)).strip() if m else ""


def inner_links(html):
    """(href, anchor) - sirf andar ke, nav/header/footer ke bahar."""
    out = []
    for h, a in re.findall(r'<a\b[^>]*href="(/[^"#?]*)[^"]*"[^>]*>(.*?)</a>', main_html(html), re.S | re.I):
        a = re.sub(r"<[^>]+>|\s+", " ", a).strip()
        if a and h != "/" and len(a) <= 80:
            out.append((h.rstrip("/") or "/", a))
    return out


GENERIC = {"yahan", "is guide", "is lekh", "ye lekh", "is page", "lekh", "guide", "yahan dekhein", "tulna yahan hai",
           "yahan padhein", "link", "click", "page", "aaj ke jawab dekhein"}


def link_mismatch(anchor, target_title):
    """Purana (v2.5.3) seedha milan - sirf title. v2.6.0 se analyse() link_kind() use karta hai (galat alarm kam)."""
    a, t = _tokens(anchor), _tokens(target_title)
    return bool(a) and bool(t) and not (a & t)


def _ttag(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    return re.sub(r"<[^>]+>|\s+", " ", m.group(1)).strip() if m else ""


def _slug_tokens(path):
    return _tokens(path.strip("/").replace("-", " "))


def link_kind(page, anchor, href, titles):
    """v2.6.0: link ki asli jaanch.
    'self'    = page apne aap ko link kare (related list mein bekaar)
    'wrong'   = link ka naam kisi DOOSRE maujood page ke naam/slug se poora milta hai, par link kahin aur jaata hai
                (jaise 'Exit Load Calculator' -> /swp-calculator jabki /exit-load-calculator hai)
    'generic' = 'yahan', 'is guide' jaisa naam (galat nahi, bas SEO kamzor)
    None      = theek (naam target ke slug ya title se milta hai, ya koi behtar page nahi)"""
    if href == page:
        return "self", None
    low = re.sub(r"\s+", " ", anchor.lower()).strip(" .➤→")
    a = _tokens(anchor)
    if low in GENERIC or not a:
        return "generic", None
    if a <= _slug_tokens(href) or a <= _tokens(titles.get(href, "")):
        return None, None
    if len(a) < 2:
        return None, None
    better = sorted((q for q in titles if q not in (page, href) and a <= _slug_tokens(q)), key=lambda q: len(_slug_tokens(q)))
    return ("wrong", better[0]) if better else (None, None)


def analyse(pages):
    """pages: {path: html}. -> dict report (bina network, test ho sake)."""
    titles = {p: title_of(h) for p, h in pages.items()}
    names = {p: titles[p] + " " + _ttag(h) for p, h in pages.items()}     # v2.6.0: h1 + <title> dono
    rep = {"thin": [], "mismatch": [], "self": [], "generic": 0, "no_review": [], "no_h1": [], "ad_on_must": [], "n": len(pages)}
    for p, h in pages.items():
        if p.startswith(SKIP_PREFIX) or p in ("/", ""):
            continue
        w = words(h)
        if w < MIN_WORDS and p not in NO_AD:
            rep["thin"].append((p, w))
        if not re.search(r"<h1\b", h, re.I):
            rep["no_h1"].append(p)
        if not REVIEW_RX.search(h):                    # v2.6.2: 'Update: <time>' bhi tareekh hai (pehle galat gina jaata tha)
            rep["no_review"].append(p)
        if p in NO_AD and "adsbygoogle" in h:
            rep["ad_on_must"].append(p)
        for href, anc in inner_links(h):
            if href not in titles:
                continue
            kind, better = link_kind(p, anc, href, names)
            if kind == "wrong":
                rep["mismatch"].append((p, anc, href, f"{titles[href]} | sahi page: {better}"))
            elif kind == "self":
                rep["self"].append((p, anc))
            elif kind == "generic":
                rep["generic"] += 1
    rep["thin"].sort(key=lambda x: x[1])
    return rep


def report_text(rep, cap=12):
    L = [f"🔎 SITE SCAN ({rep['n']} page) - sirf padha, kuch badla nahi"]
    L.append(f"• Galat link (naam kisi aur page ka): {len(rep['mismatch'])} | khud ko link: {len(rep.get('self', []))} | "
             f"'yahan/is guide' jaise kamzor naam (galti nahi): {rep.get('generic', 0)}")
    for p, a, h, t in rep["mismatch"][:cap]:
        L.append(f"   {p}: '{a}' → {h} ({t[:40]})")
    L.append(f"• Patle page (<{MIN_WORDS} shabd): {len(rep['thin'])}")
    for p, w in rep["thin"][:cap]:
        L.append(f"   {p}: {w}")
    L.append(f"• 'Aakhri update/Reviewed on' nahi: {len(rep['no_review'])} | h1 nahi: {len(rep['no_h1'])}")
    L.append(f"• Zaroori page par ad code: {len(rep['ad_on_must'])}" + (" ❌ " + ", ".join(rep["ad_on_must"]) if rep["ad_on_must"] else " ✅"))
    return "\n".join(L)


def md_text(rep):
    L = ["# SITE SCAN (apne aap likha - kuch mat badlo, developer ko do)", "",
         f"Pages: {rep['n']}. Source: live sitemap. Niyam: MIN_WORDS={MIN_WORDS}.", "",
         "## Galat link - naam kisi DOOSRE page ka (W1/B1)", ""] + [f"- {p}: '{a}' → {h} (asli naam: {t})" for p, a, h, t in rep["mismatch"]]
    L += ["", "## Page khud ko link karta hai", ""] + [f"- {p}: '{a}'" for p, a in rep.get("self", [])]
    L += ["", f"Kamzor naam ('yahan', 'is guide'): {rep.get('generic', 0)} - galti nahi, dheere-dheere behtar naam (v2.6.0 se pehle ye bhi 'toote' gine jaate the)."]
    L += ["", "## Patle page (W5/B2) - content badhao ya noindex", ""] + [f"- {p}: {w} shabd" for p, w in rep["thin"]]
    L += ["", "## 'Aakhri update / Reviewed on' nahi (W8)", ""] + [f"- {p}" for p in rep["no_review"]]
    L += ["", "## h1 nahi", ""] + [f"- {p}" for p in rep["no_h1"]]
    L += ["", "## Zaroori page par ad code", ""] + [f"- {p}" for p in rep["ad_on_must"]]
    return "\n".join(L) + "\n"


def _urls():
    sm = requests.get(f"{SITE}/sitemap.xml", timeout=25, headers={"User-Agent": "SabhisaabBot-SiteScan/1.0"}).text
    out = []
    for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sm):
        if u.startswith(SITE):
            p = u[len(SITE):] or "/"
            out.append(p.rstrip("/") or "/")
    return list(dict.fromkeys(out))[:400]


def run(max_pages=400):
    pages = {}
    for p in _urls()[:max_pages]:
        try:
            r = requests.get(SITE + p, timeout=20, headers={"User-Agent": "SabhisaabBot-SiteScan/1.0"})
            if r.status_code == 200 and "text/html" in r.headers.get("content-type", ""):
                pages[p] = r.text
        except Exception as e:
            log(f"sitescan {p}: {e}")
        time.sleep(0.6)
    rep = analyse(pages)
    try:
        (ROOT / "docs").mkdir(exist_ok=True)
        (ROOT / "docs" / "SITESCAN.md").write_text(md_text(rep), encoding="utf-8")
    except Exception as e:
        log(f"sitescan md: {e}")
    state.put("sitescan_at", time.time())
    state.put("sitescan_last", {"mismatch": len(rep["mismatch"]) + len(rep.get("self", [])), "thin": len(rep["thin"]), "n": rep["n"], "v": 260})
    return report_text(rep)


# ---------------- v2.6.0: galat link khud theek (owner: 'bina insaan') ----------------
AUTOFIX_MAX_FILES = 15


def fix_links_in(html, page, titles):
    """Ek page ke 'wrong' link sahi page par (sirf href badalta hai; naam, baaki HTML waisa hi). -> (naya_html, ginti)."""
    n = [0]
    body_start = html.find("<main")
    if body_start < 0:
        return html, 0
    end = html.find("</main>", body_start)
    if end < 0:
        return html, 0

    def sub(m):
        href = (m.group(2).rstrip("/") or "/")
        anc = re.sub(r"<[^>]+>|\s+", " ", m.group(4)).strip()
        if href not in titles or not anc:
            return m.group(0)
        kind, better = link_kind(page, anc, href, titles)
        if kind != "wrong" or not better:
            return m.group(0)
        n[0] += 1
        return m.group(1) + better + m.group(3) + m.group(4) + "</a>"
    part = re.sub(r'(<a\b[^>]*?href=")(/[^"#?]*)("[^>]*>)(.*?)</a>', sub, html[body_start:end], flags=re.S | re.I)
    return html[:body_start] + part + html[end:], n[0]


def autofix(apply=True):
    """VM ke site repo mein galat related-link khud theek: audit gate ke saath ZIP -> website.apply_zip (force=False).
    Sirf 'wrong' (naam kisi doosre maujood page ka). 'yahan' jaise naam aur self-link nahi chhedta."""
    import zipfile
    from . import website
    from .config import DATA
    try:
        website.sync()
    except Exception as e:
        log(f"autofix sync: {e}")
    d = website.DIR / "site"
    pages = {}
    for f in d.glob("*.html"):
        pages["/" if f.stem == "index" else "/" + f.stem] = f.read_text(encoding="utf-8", errors="ignore")
    names = {p: title_of(h) + " " + _ttag(h) for p, h in pages.items()}
    changed = {}
    total = 0
    for p, h in sorted(pages.items()):
        if p.startswith(SKIP_PREFIX):
            continue
        nh, k = fix_links_in(h, p, names)
        if k:
            changed[p] = nh
            total += k
        if len(changed) >= AUTOFIX_MAX_FILES:
            break
    if not changed:
        return "🔗 Galat link: koi nahi ✅"
    if not apply:
        return f"🔗 {total} galat link {len(changed)} page par (sirf jaancha)"
    z = DATA / "linkfix.zip"
    with zipfile.ZipFile(z, "w") as zz:
        for p, h in changed.items():
            zz.writestr("site/" + ("index" if p == "/" else p.strip("/")) + ".html", h)
    r = website.apply_zip(z, force=False)
    z.unlink(missing_ok=True)
    ok = str(r).startswith("✅")
    state.put("linkfix_last", {"t": time.time(), "n": total, "pages": list(changed), "ok": ok})
    if ok:
        sl = dict(state.get("sitescan_last") or {})
        sl["mismatch"] = max(0, int(sl.get("mismatch", 0)) - total)
        state.put("sitescan_last", sl)
    return (f"🔗 {total} galat link {len(changed)} page par khud theek ✅ (audit pass, deploy line mein)" if ok
            else f"🔗 Link sudhaar audit mein ruka (kuch live nahi hua): {str(r)[:300]}")


# ---------------- v2.6.2: 'Aakhri update' tareekh (AdSense/E-E-A-T) - roz thode page, SIRF asli tareekh ----------------
REVIEW_PER_DAY = 12
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
REVIEW_RX = re.compile(r"aakhri (update|jaanch|badlaav)|reviewed on|last updated|update:\s*<time", re.I)


def add_review_line(html):
    """Page ki apni dateModified (JSON-LD) ko hi dikhata hai - tareekh aage/peeche nahi karta, dateModified nahi badalta.
    H1 ke neeche ki 'meta' line mein jodta hai; meta line na ho to H1 ke neeche nayi. -> naya html ya None."""
    if REVIEW_RX.search(html):
        return None
    m = re.search(r'"dateModified":\s*"(\d{4})-(\d{2})-(\d{2})"', html)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    stamp = f'Aakhri update: <time datetime="{y:04d}-{mo:02d}-{d:02d}">{d} {MONTHS[mo - 1]} {y}</time>'
    h1 = re.search(r"<h1\b[^>]*>.*?</h1>\s*", html, re.S)
    if not h1:
        return None
    meta = re.match(r'<div class="meta">(.*?)</div>', html[h1.end():], re.S)
    if meta:
        pos = h1.end() + meta.end() - len("</div>")
        return html[:pos] + " &middot; " + stamp + html[pos:]
    return html[:h1.end()] + f'<div class="meta">{stamp}</div>\n' + html[h1.end():]


def review_daily(apply=True, n=REVIEW_PER_DAY):
    """Roz n page (sabse zyada dekhe jaane wale pehle nahi - alphabetical, taaki har din alag) mein 'Aakhri update'. Audit gate."""
    import zipfile
    from . import website
    from .config import DATA
    try:
        website.sync()
    except Exception as e:
        log(f"review sync: {e}")
    d = website.DIR / "site"
    changed = {}
    for f in sorted(d.glob("*.html")):
        if f.stem in ("404", "links", "index") or f.stem.startswith("google"):
            continue
        h = f.read_text(encoding="utf-8", errors="ignore")
        if 'name="robots" content="noindex' in h:
            continue
        nh = add_review_line(h)
        if nh:
            changed[f.name] = nh
        if len(changed) >= n:
            break
    if not changed:
        state.put("review_done", True)
        return "📅 'Aakhri update' sab page par ✅"
    if not apply:
        return f"📅 {len(changed)} page mein jodna baaki (jaancha)"
    z = DATA / "review.zip"
    with zipfile.ZipFile(z, "w") as zz:
        for fn, body in changed.items():
            zz.writestr("site/" + fn, body)
    r = website.apply_zip(z, force=False)
    z.unlink(missing_ok=True)
    return (f"📅 {len(changed)} page par 'Aakhri update' (page ki asli tareekh) ✅" if str(r).startswith("✅")
            else f"📅 Aakhri-update audit mein ruka (kuch live nahi): {str(r)[:200]}")
