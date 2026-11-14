"""v2.6.1 (owner: 'console ke search shabd page par daalo taaki ranking ho - bina insaan'): KEYWORD AUTO-SUDHAAR.

Sirf wahi shabd jinka jawab GANIT se pakka nikalta hai (koi AI andaza nahi):
  - personal loan EMI ('3 lakh personal loan emi 5 years')       -> /personal-loan-emi-calculator
  - data unit ('300 mb to gb', '1 tb is how many mb')            -> /data-storage-converter
  - mutthi/nali -> square feet ('10 mutthi in square feet')       -> /nali-mutthi-square-feet
  - roman number ('49 roman number')                              -> /roman-numerals-converter
Har shabd ka ek FAQ (dikhne wala + FAQPage schema dono) USI page par jahan Google use dikha raha hai. Naya page kabhi nahi
(scaled content niti). Roz max 2 page, har page par ek baar mein 1 FAQ, milta-julta sawal pehle se ho to nahi.
ZIP -> website.apply_zip (audit gate, force=False). Fail = kuch live nahi. Baaki shabd purane tareeke (owner digest) se.
"""
import datetime
import difflib
import html as H
import json
import re

from . import state
from .log import log

MAX_PAGES_DAY = 2
POS_MAX = 30


def _inr(x):
    s = str(int(round(x)))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


def emi(p, annual, years):
    r = annual / 1200
    n = int(years * 12)
    return p * r * (1 + r) ** n / ((1 + r) ** n - 1)


UNITS = {"kb": 1, "mb": 2, "gb": 3, "tb": 4, "pb": 5}
ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
         (5, "V"), (4, "IV"), (1, "I")]


def roman(n):
    out = ""
    for v, s in ROMAN:
        while n >= v:
            out += s
            n -= v
    return out


def _fmt(x):
    if x >= 100:
        return _inr(x) if abs(x - round(x)) < 1e-9 else f"{x:,.2f}"
    if x < 1:
        return f"{x:.4g}" if x >= 1e-4 else f"{x:.3e}"
    return f"{x:,.2f}".rstrip("0").rstrip(".")


def answer_for(q, page):
    """(sawal, jawab) ya None. Sirf pakka ganit."""
    t = q.lower().strip()
    if page == "/personal-loan-emi-calculator":
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\b", t)
        if not m or not re.search(r"emi|kist|loan", t):
            return None
        lakh = float(m.group(1))
        if not 0.5 <= lakh <= 50:
            return None
        y = re.search(r"(\d{1,2})\s*(?:saal|years?|yrs?|sal)\b", t)
        yrs = int(y.group(1)) if y else None
        if yrs is not None and not 1 <= yrs <= 7:
            return None
        P = lakh * 1e5
        L = f"{lakh:g}"
        if yrs:
            e14, e11 = emi(P, 14, yrs), emi(P, 11, yrs)
            return (f"{L} lakh personal loan ki EMI {yrs} saal ke liye kitni hogi?",
                    f"14% saalana byaj (reducing) par lagbhag Rs {_inr(e14)} mahina aur kul byaj lagbhag Rs {_inr(round(e14) * yrs * 12 - P)}. "
                    f"11% par EMI lagbhag Rs {_inr(e11)}. Dar bank aur credit score par nirbhar hai - apni dar upar calculator mein daalein.")
        return (f"{L} lakh personal loan ki EMI kitni banti hai?",
                f"14% byaj par 3 saal ke liye lagbhag Rs {_inr(emi(P, 14, 3))}, 5 saal ke liye lagbhag Rs {_inr(emi(P, 14, 5))} mahina. "
                f"11% par 5 saal ki EMI lagbhag Rs {_inr(emi(P, 11, 5))}. Processing fee alag hoti hai.")
    if page == "/data-storage-converter":
        m = re.search(r"(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb|pb)\b.*?\b(kb|mb|gb|tb|pb)\b", t)
        if not m or "bps" in t:
            return None
        n, a, b = float(m.group(1)), m.group(2), m.group(3)
        if a == b:
            return None
        bi = n * (1024 ** (UNITS[a] - UNITS[b]))
        de = n * (1000 ** (UNITS[a] - UNITS[b]))
        A, B = a.upper(), b.upper()
        return (f"{n:g} {A} kitne {B} hote hain?",
                f"Computer/phone ke hisaab (1024) se {n:g} {A} = {_fmt(bi)} {B}. Hard disk/pen drive ke dabbe wale hisaab (1000) se "
                f"{n:g} {A} = {_fmt(de)} {B}. Isi farak se likha size aur dikhne wala size alag lagta hai.")
    if page == "/nali-mutthi-square-feet":
        m = re.search(r"(\d+(?:\.\d+)?)\s*(mutthi|nali)\b", t)
        if not m:
            return None
        n, u = float(m.group(1)), m.group(2)
        if not 0 < n <= 500:
            return None
        sq = n * (135 if u == "mutthi" else 2160)
        if n == 1 and u == "nali":
            return None                                # page par pehle se
        return (f"{n:g} {u} kitne square feet hote hain?",
                f"Uttarakhand ke aam naap (1 nali = 16 mutthi = lagbhag 2,160 sq ft) se {n:g} {u} lagbhag {_inr(sq)} square feet, "
                f"yaani karib {_fmt(sq * 0.092903)} square meter. Kharid-bikri se pehle tehsil/patwari record se pushti karein.")
    if page == "/roman-numerals-converter":
        m = re.search(r"\b(\d{1,4})\b", t)
        if not m or not re.search(r"roman", t):
            return None
        n = int(m.group(1))
        if not 1 <= n <= 3999:
            return None
        return (f"{n} ko Roman number mein kaise likhte hain?",
                f"{n} = {roman(n)}. Bade se chhote kram mein likhte hain; 4, 9, 40, 90, 400, 900 ke liye chhota akshar pehle aata hai (IV, IX, XL, XC, CD, CM).")
    return None


# ---------------- page mein jodna (bina network, test ho sake) ----------------
def existing_questions(html):
    return [H.unescape(re.sub(r"<[^>]+>", "", q)).strip() for q in re.findall(r"<summary>(.*?)</summary>", html, re.S)]


def too_similar(q, qs):
    return any(difflib.SequenceMatcher(None, q.lower(), x.lower()).ratio() >= 0.75 for x in qs)


def add_faq(html, q, a, today):
    """<details> + FAQPage schema dono mein; dateModified aaj. -> naya html ya None."""
    m = re.search(r'(<script type="application/ld\+json">)(\{[^<]*"FAQPage"[^<]*\})(</script>)', html)
    if not m:
        return None
    blocks = list(re.finditer(r"<details[^>]*>.*?</details>", html, re.S))
    if not blocks:
        return None
    last = blocks[-1]
    cls = re.match(r"<details([^>]*)>", last.group(0)).group(1)
    blk = f"<details{cls}><summary>{H.escape(q)}</summary><p>{H.escape(a)}</p></details>"
    try:
        d = json.loads(m.group(2))
    except Exception:
        return None
    d.setdefault("mainEntity", []).append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
    html2 = html[:m.start(2)] + json.dumps(d, ensure_ascii=False) + html[m.end(2):]
    shift = len(html2) - len(html)
    pos = last.end() + (shift if last.end() > m.end(2) else 0)
    html2 = html2[:pos] + "\n" + blk + html2[pos:]
    return re.sub(r'"dateModified":\s*"[\d-]+"', f'"dateModified": "{today}"', html2)


def plan(kw, pages_html, today, done=None, max_pages=MAX_PAGES_DAY):
    """kw: {query: {page, imp, pos, status}}; pages_html: {'/slug': html}. -> ({repo_path: html}, [(q, sawal)])"""
    done = set(done or [])
    out, used, notes = {}, set(), []
    rows = sorted(kw.items(), key=lambda x: (-int(x[1].get("imp", 0)), float(x[1].get("pos", 99))))
    for q, info in rows:
        pg = info.get("page") or "/"
        if q in done or info.get("status") in ("nahi", "chhodo", "bot ne joda") or float(info.get("pos", 99)) > POS_MAX:
            continue
        if pg in used or (len(used) >= max_pages and pg not in out):
            continue
        html = out.get(f"site{pg}.html") or pages_html.get(pg)
        if not html:
            continue
        qa = answer_for(q, pg)
        if not qa:
            continue
        qs = existing_questions(html)
        if too_similar(qa[0], qs):
            done.add(q)
            continue
        nh = add_faq(html, qa[0], qa[1], today)
        if not nh:
            continue
        out[f"site{pg}.html"] = nh
        used.add(pg)
        notes.append((q, qa[0]))
    return out, notes


def run(force=False):
    from . import website, diary, tg
    from .config import DATA
    import zipfile
    today = str(datetime.date.today())
    if not force and state.get("kwfix_day") == today:
        return "kwfix: aaj ho chuka"
    state.put("kwfix_day", today)
    f = DATA / "keywords.json"
    if not f.exists():
        return "kwfix: keyword bank khaali"
    kw = json.loads(f.read_text())
    try:
        website.sync()
    except Exception as e:
        log(f"kwfix sync: {e}")
    d = website.DIR / "site"
    pages = {}
    for pg in {(v.get("page") or "/") for v in kw.values()}:
        p = d / ("index.html" if pg == "/" else pg.strip("/") + ".html")
        if p.exists():
            pages[pg] = p.read_text(encoding="utf-8")
    files, notes = plan(kw, pages, today, state.get("kwfix_done") or [])
    if not files:
        return "kwfix: aaj koi pakka-ganit wala shabd nahi"
    sm_f = d / "sitemap.xml"
    if sm_f.exists():
        sm = sm_f.read_text(encoding="utf-8")
        for p in files:
            slug = p[5:-5]
            sm = re.sub(r"(<loc>https://sabhisaab\.com/" + re.escape(slug) + r"</loc>\s*<lastmod>)[\d-]+", lambda x: x.group(1) + today, sm, count=1)
        files["site/sitemap.xml"] = sm
    z = DATA / "kwfix.zip"
    with zipfile.ZipFile(z, "w") as zz:
        for p, body in files.items():
            zz.writestr(p, body)
    r = website.apply_zip(z, force=False)
    z.unlink(missing_ok=True)
    if str(r).startswith("✅"):
        for q, _s in notes:
            kw[q]["status"] = "bot ne joda"
        f.write_text(json.dumps(kw, ensure_ascii=False))
        state.update("kwfix_done", lambda l: ((l or []) + [q for q, _ in notes])[-500:], [])
        diary.add("setting", "keyword FAQ joda: " + "; ".join(s for _, s in notes)[:300])
        tg.alert("green", "🔑 Google ke search shabd par page mein naya FAQ (ganit se pakka, audit pass):\n" +
                 "\n".join(f"• '{q}' → {s}" for q, s in notes))
        return f"kwfix: {len(notes)} FAQ ✅"
    return f"kwfix: audit mein ruka (kuch live nahi): {str(r)[:200]}"
