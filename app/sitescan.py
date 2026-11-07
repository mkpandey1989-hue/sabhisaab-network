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


def link_mismatch(anchor, target_title):
    """True = anchor aur target ke naam mein ek bhi kaam ka shabd saajha nahi (jaise 'Exit Load' -> SWP Calculator)."""
    a, t = _tokens(anchor), _tokens(target_title)
    return bool(a) and bool(t) and not (a & t)


def analyse(pages):
    """pages: {path: html}. -> dict report (bina network, test ho sake)."""
    titles = {p: title_of(h) for p, h in pages.items()}
    rep = {"thin": [], "mismatch": [], "no_review": [], "no_h1": [], "ad_on_must": [], "n": len(pages)}
    for p, h in pages.items():
        if p.startswith(SKIP_PREFIX) or p in ("/", ""):
            continue
        w = words(h)
        if w < MIN_WORDS and p not in NO_AD:
            rep["thin"].append((p, w))
        if not re.search(r"<h1\b", h, re.I):
            rep["no_h1"].append(p)
        if not re.search(r"aakhri (update|jaanch)|reviewed on|last updated", h, re.I):
            rep["no_review"].append(p)
        if p in NO_AD and "adsbygoogle" in h:
            rep["ad_on_must"].append(p)
        for href, anc in inner_links(h):
            tt = titles.get(href)
            if tt and link_mismatch(anc, tt):
                rep["mismatch"].append((p, anc, href, tt))
    rep["thin"].sort(key=lambda x: x[1])
    return rep


def report_text(rep, cap=12):
    L = [f"🔎 SITE SCAN ({rep['n']} page) - sirf padha, kuch badla nahi"]
    L.append(f"• Toote related-link (naam≠page): {len(rep['mismatch'])}")
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
         "## Toote related-link (W1/B1)", ""] + [f"- {p}: '{a}' → {h} (asli naam: {t})" for p, a, h, t in rep["mismatch"]]
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
    state.put("sitescan_last", {"mismatch": len(rep["mismatch"]), "thin": len(rep["thin"]), "n": rep["n"]})
    return report_text(rep)
