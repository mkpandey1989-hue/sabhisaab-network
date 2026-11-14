#!/usr/bin/env python3
"""Items -> poora HTML page (site ka template), linking, dedupe, queue manifest."""
import json, re, os, sys, difflib, collections, html as H, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen import build_pages, HUB_PAGES, SITE
from model import DISTRICTS
from themes import THEMES, ORDER, NIC, IMAGES
from clean import esc, is_deva
from ukjs import UK_JS, UK_CSS
from headings_hi import hinglish, _tpl as _tpl_h


def _tpl_only(body):
    if body.startswith("FAQ: "):
        return "Sawal-Jawab: " + body[5:]
    return _tpl_h(body, None)
from dhancha import neg_headings
from fix5 import apply as fix5_apply

TPL = "/home/claude/sabhisaab_site/site/uttarakhand-farmer-id-ukfr.html"
LIVE = os.environ.get("UK_LIVE_SITE", "/home/claude/sabhisaab_site/site")
OUT = os.environ.get("UK_OUT", "/home/claude/ukout")
DORDER = [d[1] for d in DISTRICTS]
DNAME = {d[1]: d[2] for d in DISTRICTS}
HUB_TOPIC_ORDER = ["uttarakhand-char-dham-panch-kedar", "uttarakhand-yatra-planner", "uttarakhand-gk-ukpsc",
                   "uttarakhand-zameen-kanoon-nali-mutthi", "uttarakhand-shahar-paryatan-sthal", "uttarakhand-pahadi-virasat-tyohar",
                   "uttarakhand-pahadi-shabdkosh", "uttarakhand-hindi-jankari", "uttarakhand-bhugol-nadiyan-glacier",
                   "uttarakhand-itihas-prasiddh-hastiyan", "uttarakhand-prashasan-arthvyavastha"]
HUB_MOD = {}
for slug, kind, _, parts, *_ in HUB_PAGES:
    for p in parts:
        if isinstance(p, int):
            HUB_MOD.setdefault(p, slug)

# ---------------------------------------------------------------- template ke hisse
_t = open(TPL, encoding="utf-8").read()
TOP = _t[:_t.find('<meta name="theme-color"')]
FONTS = _t[_t.find('<link rel="preconnect"'):_t.find("<style>")]
S1 = _t[_t.find("<style>"):_t.find("</style>") + 8]
_r = _t[_t.find("</style>") + 8:]
S2 = _r[_r.find("<style>"):_r.find("</style>") + 8]
FOOT = _t[_t.find("</main>"):]
FAVICON = re.search(r'<link rel="icon"[^>]*>', _t).group(0)
HEADER = re.search(r"<header>.*?</header>", _t, re.S).group(0)
EXTRA_CSS = """<style>
.ans{background:#E7F3F1;border-left:4px solid var(--brand);border-radius:10px;padding:11px 14px;margin:12px 0}
.ans p{margin:0}.tw{overflow-x:auto;margin:14px 0}
h3{font-family:'Bricolage Grotesque',sans-serif;font-size:1.05rem;margin:20px 0 8px}
h4{font-size:.98rem;margin:16px 0 6px}
.quiz{background:#fff;border:1px dashed var(--line);border-radius:10px;padding:10px 13px}
.dupref{font-size:.9rem;background:#FFF7ED;border-radius:8px;padding:8px 12px}
.ukrel{margin:22px 0;padding:14px 16px;background:#fff;border:1px solid var(--line);border-radius:12px}
.ukrel b{display:block;margin-bottom:8px}.ukrel ul{margin:0 0 0 18px}.ukrel li{margin:4px 0}
.ukrel a{color:var(--brand);font-weight:600;text-decoration:none}.ukrel a:hover{text-decoration:underline}
.ukdir{columns:2;column-gap:22px}@media(max-width:560px){.ukdir{columns:1}}
.crumb span{color:var(--muted)}
.faq .fa{padding:0 18px 15px;color:var(--dim)}.faq .fa p{padding:0}
.lead{font-size:1.02rem;color:var(--ink)}"""+UK_CSS+"""
</style>
"""

def norm_p(inner):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", inner)).strip().lower()

def text_of(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()

def slugify(t):
    t = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return t[:48] or "s"

# ---------------------------------------------------------------- kram (priority)
def priority(pages):
    by = {p["slug"]: p for p in pages}
    order = ["uttarakhand"] + [d + "-uttarakhand" for d in DORDER]
    topics = list(HUB_TOPIC_ORDER)
    for th in ORDER[1:]:
        for d in DORDER:
            s = d + "-" + THEMES[th][0]
            if s in by:
                order.append(s)
        if topics:
            order.append(topics.pop(0))
    order += topics
    order += [p["slug"] for p in pages if p["slug"] not in order]
    return order

# ---------------------------------------------------------------- page ke andar safai
def ratio(a, b):
    sm = difflib.SequenceMatcher(None, a, b)
    if sm.real_quick_ratio() < 0.8 or sm.quick_ratio() < 0.8:
        return 0
    return sm.ratio()

def sentences(t):
    return [x.strip() for x in re.split(r"(?<=[.!?।])\s+", t) if x.strip()]

DH = {"almora": "अल्मोड़ा", "bageshwar": "बागेश्वर", "chamoli": "चमोली", "champawat": "चंपावत", "dehradun": "देहरादून",
      "haridwar": "हरिद्वार", "nainital": "नैनीताल", "pauri-garhwal": "पौड़ी गढ़वाल", "pithoragarh": "पिथौरागढ़",
      "rudraprayag": "रुद्रप्रयाग", "tehri-garhwal": "टिहरी गढ़वाल", "udham-singh-nagar": "ऊधम सिंह नगर", "uttarkashi": "उत्तरकाशी"}


def district_headings(p):
    """v3.3 (14 Nov): 13 zilon mein ek jaisi template heading ('93. District Economy...') -> zile ka naam jodo
    (search relevance + har page ki heading alag). H1 mein Devanagari naam (Hindi search ke liye, ek baar)."""
    D, d = p.get("D"), p.get("district")
    if not d:                                   # rajya/hub page: sirf haath ke saanche (TPL) - baaki waisa hi
        for k, it in enumerate(p["items"]):
            if it[0] in ("h2", "h3", "h4"):
                m = re.match(r"^((?:[A-Z]\.)?\d{1,3}(?:\.\d{1,2})?\.?\s+)?(.*)$", it[1])
                v = _tpl_only(m.group(2))
                if v:
                    p["items"][k] = (it[0], (m.group(1) or "") + v) + tuple(it[2:])
        return
    names = {D.lower(), D.split()[0].lower()}
    out = []
    for it in p["items"]:
        if it[0] in ("h2", "h3", "h4"):
            t0 = re.sub(r"\b(of|in|for|from) the District\b", r"\1 " + D, it[1])
            t0 = re.sub(r"\bthe District\b", D, t0)
            it = (it[0], hinglish(t0, D)) + tuple(it[2:])
        if it[0] == "h2":
            t = it[1]
            t = re.sub(r"\b(of|in|for) the District\b", r"\1 " + D, t)
            t = re.sub(r"\bthe District\b", D, t)
            if not any(n in t.lower() for n in names):
                m = re.match(r"^(\d{1,3}\.)\s+(.*)$", t)
                t = ("%s %s: %s" % (m.group(1), D, m.group(2))) if m else "%s: %s" % (D, t)
            it = (it[0], t) + tuple(it[2:])
        elif it[0] in ("h3", "h4"):
            t = re.sub(r"\b(of|in|for|from) the District\b", r"\1 " + D, it[1])
            it = (it[0], re.sub(r"\bthe District\b", D, t)) + tuple(it[2:])
        out.append(it)
    p["items"] = out
    if DH.get(d) and DH[d] not in p["h1"]:
        p["h1"] = p["h1"].replace(D, "%s (%s)" % (D, DH[d]), 1)


def tidy_page(p, log):
    fix5_apply(p, log)          # v3.3.2 audit-5: Census 2011 sudhaar + bachi lekhak/SEO line
    district_headings(p)
    neg_headings(p)
    items = p["items"]
    # 1) FAQ: milte-julte sawal ek (jawab jod kar - kuch nahi khota)
    faqs = [i for i, it in enumerate(items) if it[0] == "faq"]
    drop = set()
    conv = set()
    for ai, i in enumerate(faqs):
        if i in drop or i in conv:
            continue
        qi = items[i][1].lower()
        for j in faqs[ai + 1:]:
            if j in drop or j in conv:
                continue
            qj = items[j][1].lower()
            r_ = difflib.SequenceMatcher(None, qi, qj).ratio()
            wd = set(re.findall(r"\w+", qi)) ^ set(re.findall(r"\w+", qj))
            if r_ >= 0.85 and not (r_ >= 0.93 or len(wd) <= 2):
                # sawal milta-julta dikhta hai par matlab alag ('purane pargana' / 'purane vyapar marg'): jawab jodna galat,
                # do FAQ rakhna audit ki 'milta-julta FAQ' galti - isliye doosra sawal-jawab saadhe para mein (kuch nahi khota)
                items[j] = ("p", items[j][1].rstrip() + " " + items[j][2])
                conv.add(j)
                continue
            if r_ >= 0.85:
                a1, a2 = items[i][2], items[j][2]
                _n = lambda x: re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", x.lower())).strip()   # 'par.' bhi 'par (' mein gina jaye
                if _n(a2) not in _n(a1):
                    add = [s for s in sentences(a2) if _n(s) not in _n(a1) and
                           max([difflib.SequenceMatcher(None, _n(s), _n(x)).ratio() for x in sentences(a1)] or [0]) < 0.7]
                    if add:
                        a1 = a1.rstrip() + " " + " ".join(add)
                items[i] = ("faq", items[i][1], a1)
                drop.add(j)
                log.append({"page": p["slug"], "action": "faq_merge", "kept": items[i][1], "merged": items[j][1]})
    # 2) lambe paragraph ka dohraav isi page par
    paras = [i for i, it in enumerate(items) if it[0] in ("p", "pb", "ans") and len(it[1]) > 110 and i not in drop]
    for ai, i in enumerate(paras):
        if i in drop:
            continue
        for j in paras[ai + 1:]:
            if j in drop:
                continue
            if ratio(items[i][1].lower(), items[j][1].lower()) >= 0.78:
                a1, a2 = items[i][1], items[j][1]
                add = [s for s in sentences(a2) if s.lower() not in a1.lower()]
                if add:
                    items[i] = (items[i][0], a1.rstrip() + " " + " ".join(add))
                drop.add(j)
                log.append({"page": p["slug"], "action": "para_merge", "kept": a1[:80], "merged": a2[:80]})
    items = [it for k, it in enumerate(items) if k not in drop]
    # 3) H2 ek jaise (audit ka niyam) -> baad wala H3
    seen = []
    out = []
    for it in items:
        if it[0] == "h2":
            a = it[1].lower()
            clash = any(a == b or (difflib.SequenceMatcher(None, a, b).ratio() >= 0.85 and min(len(a), len(b)) > 24 and
                                   (set(a.split()) <= set(b.split()) or set(b.split()) <= set(a.split()))) for b in seen)
            if clash:
                it = ("h3",) + tuple(it[1:])
                log.append({"page": p["slug"], "action": "h2_to_h3", "h": it[1]})
            else:
                seen.append(a)
        out.append(it)
    # 3b) khaali heading (editor/meta vaakya hatne ke baad neeche kuch nahi bacha) -> hatao, log mein
    while True:
        drop_h = None
        for i, it in enumerate(out):
            if it[0] in ("h2", "h3", "h4"):
                L = int(it[0][1])
                j = i + 1
                while j < len(out) and not (out[j][0] in ("h2", "h3", "h4") and int(out[j][0][1]) <= L):
                    if out[j][0] not in ("h2", "h3", "h4"):
                        break
                    j += 1
                else:
                    drop_h = i
                    break
                if j < len(out) and out[j][0] in ("h2", "h3", "h4") and int(out[j][0][1]) <= L:
                    drop_h = i
                    break
        if drop_h is None:
            break
        log.append({"page": p["slug"], "action": "empty_heading", "h": out[drop_h][1]})
        out.pop(drop_h)
    # 3c) ek page mein do baar wahi heading -> doosri ke saath uske h2 ka vishay (pathak aur Google dono ko farak dikhe)
    seen, par = set(), ""
    for k, it in enumerate(out):
        if it[0] not in ("h2", "h3", "h4"):
            continue
        mm = re.match(r"^((?:[A-Z]\.)?\d{1,3}(?:\.\d{1,2})?\.?\s+)?(.*)$", it[1])
        body = mm.group(2)
        if body in seen and par and par != body:
            out[k] = (it[0], it[1] + " (" + par + ")") + tuple(it[2:])
        seen.add(body)
        if it[0] == "h2":
            par = re.sub(r"^[^:]{2,25}:\s+", "", body) if p.get("D") and body.startswith(p["D"]) else body
            par = par if len(par) <= 45 else par[:45].rsplit(" ", 1)[0]
    # 4) 4 se kam FAQ -> saada sawal-jawab (audit niyam)
    if 0 < sum(1 for it in out if it[0] == "faq") < 4:
        out = [("qa", it[1], it[2]) if it[0] == "faq" else it for it in out]
    p["items"] = out

# ---------------------------------------------------------------- headings ke id + cross-ref map
def assign_ids(p):
    used = set()
    res = []
    for it in p["items"]:
        if it[0] in ("h2", "h3", "h4"):
            m = re.match(r"^(\d{1,3})(?:\.(\d{1,2}))?[.:)]?\s", it[1])
            base = ("h%s" % m.group(1) + ("-%s" % m.group(2) if m.group(2) else "")) if m else slugify(it[1])
            hid, n = base, 2
            while hid in used:
                hid = "%s-%d" % (base, n); n += 1
            used.add(hid)
            res.append((it[0], it[1], hid))
        else:
            res.append(it)
    p["items"] = res

def ref_maps(pages, modmap):
    hmap = collections.defaultdict(dict)       # district -> "31" / "31.2" -> (slug, id, text)
    for p in pages:
        key = p["district"] or "hub"
        for it in p["items"]:
            if it[0] in ("h2", "h3"):
                m = re.match(r"^(\d{1,3})(?:\.(\d{1,2}))?[.:)]?\s+(.*)$", it[1])
                if m:
                    k = m.group(1) + ("." + m.group(2) if m.group(2) else "")
                    hmap[key].setdefault(k, (p["slug"], it[2], m.group(3)))
    mmap = {}
    for d, mm in modmap.items():
        mmap[d] = {n: d + "-" + THEMES[th][0] for n, th in mm.items()}
    mmap["hub"] = dict(HUB_MOD)
    return hmap, mmap

REF = re.compile(r"\b(Headings?|Heading)\s+(\d{1,3})(?:\.(\d{1,2}))?\b|\bH(\d{2,3})\b|\b(Module|module)\s+(\d{1,2})\b")

def linkify(text_html, p, hmap, mmap, titles):
    key = p["district"] or "hub"
    def rep(m):
        if m.group(5):
            tgt = mmap.get(key, {}).get(int(m.group(6)))
            if not tgt or tgt == p["slug"]:
                return "\x00"            # isi page ka / bina page ka 'Module N' -> pathak ke liye bekaar shabd (neeche saaf)
            return '<a href="/%s" data-uk="%s">%s</a>' % (tgt, tgt, esc(titles.get(tgt, m.group(0))))
        num = m.group(2) or m.group(4)
        sub = m.group(3)
        k = num + ("." + sub if sub else "")
        hit = hmap.get(key, {}).get(k) or hmap.get(key, {}).get(num)
        if not hit:
            return "\x01" + m.group(0) + "\x02"     # jis heading ka page nahi mila: '(Heading 99)' jaisa ishara pathak ke kaam ka nahi
        slug, hid, ttl = hit
        ttl = re.sub(r"\s*\(.*?\)\s*", " ", ttl).strip()
        ttl = (ttl[:70].rsplit(" ", 1)[0] + "…") if len(ttl) > 72 else ttl
        if slug == p["slug"]:
            return '<a href="#%s">%s</a>' % (hid, esc(ttl))
        return '<a href="/%s#%s" data-uk="%s">%s</a>' % (slug, hid, slug, esc(ttl))
    t0 = text_html
    # v3.3.2 audit-3: Nainital/Pithoragarh file 'Section N' likhti thi (matlab Heading N); kanoon wala 'Section 143 ki/wali' nahi chhuta -
    # sirf bracket mein '(Section 23 aur 77)' ya table ka khaana jisme bas 'Section 31' ho
    t0 = re.sub(r"\(Sections?\s+(\d{1,3}(?:\.\d{1,2})?)((?:\s*(?:,|aur|and|&amp;|&)\s*\d{1,3}(?:\.\d{1,2})?)*)\)",
                lambda m: "(" + " aur ".join("Heading " + x for x in re.findall(r"\d{1,3}(?:\.\d{1,2})?", m.group(1) + m.group(2))) + ")", t0)
    t0 = re.sub(r"^\s*Sections?\s+(\d{1,3}(?:\.\d{1,2})?)\s*$", r"Heading \1", t0)
    if key == "nainital":                         # Nainital ki file mein 'Section N' = hamesha apni Heading N (kanoon ka '10(1)' nahi)
        t0 = re.sub(r"(?<!Bill ke )\bSections?\s+(?!143\b|154\b|118\b)(\d{1,3}(?:\.\d{1,2})?)(?!\s*\(\d)(?!\d)", r"Heading \1", t0)
    t0 = re.sub(r"\b(Headings?)\s+(\d{1,3}(?:\.\d{1,2})?)\s*(,|aur|and)\s*(\d{1,3}(?:\.\d{1,2})?)\b", r"\1 \2 \3 Heading \4", t0)
    out = REF.sub(rep, t0)
    out = re.sub(r"\(\s*\x01[^\x02]*\x02\s*(?:aur|,)\s*", "(", out)          # '(na-mila aur mila)' -> '(mila)'
    out = re.sub(r"\s*(?:aur|,)\s*\x01[^\x02]*\x02\s*\)", ")", out)
    if "\x01" in out:
        out = re.sub(r"\s*\(\x01[^\x02]*\x02(?:\.[A-Za-z0-9]+)?\)", "", out)
        out = out.replace("\x01", "").replace("\x02", "")
    if "\x00" in out:
        out = re.sub(r"\s*\(\x00\)", "", out)
        out = re.sub(r"\(\x00\s*[,:;]\s*", "(", out)
        out = re.sub(r"\s*\(\x00[^)]{0,40}\)", "", out)
        out = re.sub(r"\x00 ka maksad", "Is hisse ka maksad", out)
        out = re.sub(r"\b(ye|yeh|is)\s+\x00", lambda m: m.group(1) + " hissa", out, flags=re.I)
        out = out.replace("\x00", "yeh hissa")
    return out

SITEURL = re.compile(r"https?://(?:www\.)?sabhisaab\.com/uttarakhand(?:/([a-z-]+))?/?")
def siteurl(m):
    d = m.group(1)
    if d and d in DNAME:
        return '<a href="/%s-uttarakhand" data-uk="%s-uttarakhand">%s zila guide</a>' % (d, d, DNAME[d])
    return '<a href="/uttarakhand" data-uk="uttarakhand">Uttarakhand guide</a>'

def tx(t, p, hmap, mmap, titles):
    return SITEURL.sub(siteurl, linkify(esc(t), p, hmap, mmap, titles))

def lang_attr(t):
    return ' lang="hi"' if is_deva(t) else ""

def render_items(p, hmap, mmap, titles):
    out = []
    for it in p["items"]:
        k = it[0]
        if k in ("h2", "h3", "h4"):
            out.append(("h", '<%s id="%s"%s>%s</%s>' % (k, it[2], lang_attr(it[1]), esc(it[1]), k), it))
        elif k in ("p", "pb"):
            inner = tx(it[1], p, hmap, mmap, titles)
            if k == "pb":
                inner = "<b>%s</b>" % inner
            out.append(("p", "<p%s>%s</p>" % (lang_attr(it[1]), inner), inner))
        elif k == "ans":
            t = re.sub(r"^(Seedha Jawab|Seedha jawab|Quick Answer)\s*(\([^)]*\))?\s*:\s*", "", it[1])
            lab = "Seedha jawab:" if t != it[1] or not is_deva(it[1]) else ""
            if is_deva(it[1]):
                t = re.sub(r"^सीधा जवाब\s*:\s*", "", it[1]); lab = "सीधा जवाब:"
            inner = "<b>%s</b> %s" % (lab, tx(t, p, hmap, mmap, titles))
            out.append(("p", '<div class="ans"><p%s>%s</p></div>' % (lang_attr(it[1]), inner), inner))
        elif k == "ul":
            out.append(("x", "<ul>%s</ul>" % "".join("<li%s>%s</li>" % (lang_attr(x), tx(x, p, hmap, mmap, titles)) for x in it[1]), None))
        elif k == "table":
            rows = it[1]
            head = "".join("<th>%s</th>" % tx(c, p, hmap, mmap, titles) for c in rows[0])
            body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % tx(c, p, hmap, mmap, titles) for c in r) for r in rows[1:])
            out.append(("x", '<div class="tw"><table class="tb"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (head, body), None))
        elif k == "faq":
            q, a = esc(it[1]), tx(it[2], p, hmap, mmap, titles)
            out.append(("faq", '<details class="faq"%s><summary>%s</summary><p>%s</p></details>' % (lang_attr(it[1]), q, a), (it[1], a)))
        elif k == "qa":
            inner = "<b>%s</b> %s" % (esc(it[1]), tx(it[2], p, hmap, mmap, titles))
            out.append(("p", "<p%s>%s</p>" % (lang_attr(it[1]), inner), inner))
        elif k == "quiz":
            inner = tx(it[1], p, hmap, mmap, titles)
            inner = re.sub(r"(—\s*)?(Jawab|Uttar)\s*:", r"<b>\2:</b>", inner)
            out.append(("p", '<p class="quiz"%s>%s</p>' % (lang_attr(it[1]), inner), inner))
    return out

# ---------------------------------------------------------------- site par pehle se maujood text (dohraav jaanch)
def existing_text():
    paras, qa = {}, {}
    for f in sorted(os.listdir(LIVE)):
        if not f.endswith(".html"):
            continue
        s = open(os.path.join(LIVE, f), encoding="utf-8", errors="ignore").read()
        body = re.sub(r"<script\b.*?</script>", "", s, flags=re.S)
        body = re.sub(r"<style\b.*?</style>", "", body, flags=re.S)
        body = body[body.find("</head>"):]
        for x in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S):
            n = norm_p(x)
            if len(n) > 120:
                paras.setdefault(n, "/" + f[:-5])
        for q, a in re.findall(r"<details[^>]*><summary>(.*?)</summary>(.*?)</details>", body, re.S):
            qa.setdefault((text_of(q).lower(), text_of(a).lower()), "/" + f[:-5])
    return paras, qa

IMGSZ = {"uttarakhandghatibaadalgaon.webp": (1288, 952), "uttarakhandseedhidhaarkhet.webp": (1288, 952),
         "uttarakhand-pahadi-khet-mirchi.webp": (952, 1288), "uttarakhand-gaon-lambi-ghas.webp": (952, 1288),
         "uttarakhand-gaon-kele-ke-ped.webp": (1288, 952), "pahadi-chir-ke-ped.webp": (1288, 952),
         "pahadi-kheti-bel-mandap.webp": (1288, 952)}
WIDE = [i for i in IMAGES if IMGSZ[i[0]][0] > IMGSZ[i[0]][1]]

# v3.3.2 (owner 14 Nov): owner ki apni khichi photo/video-frame (photos/photos.py se saaf: chehra/awaaz/watermark/poster/number
# nahi, EXIF/GPS nahi, jagah ka naam nahi). Har zila-page par us ilake (Himalaya/madhya pahad/Terai) aur vishay se mel khati photo.
PHOTOS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos", "photos.json"), encoding="utf-8"))
for _ph in PHOTOS:
    IMGSZ[_ph["file"]] = (_ph["w"], _ph["h"])
HIGH = {"chamoli", "rudraprayag", "uttarkashi", "pithoragarh", "bageshwar"}
PLAIN = {"haridwar", "udham-singh-nagar"}
PH_USE = collections.Counter()
IMGSZ_OWN = {_ph["file"] for _ph in PHOTOS if _ph["w"] >= 1200 and _ph["w"] > _ph["h"]}
PH_DIST = collections.defaultdict(set)


def region_of(d):
    return "plain" if d in PLAIN else ("high" if d in HIGH else ("mid" if d else "hub"))


def photo_for(p, skip=(), second=False):
    """Page ke ilake + vishay se photo. Ek zile ke do page par ek hi photo nahi (jab tak vikalp ho); poori site par barabar bante."""
    reg = region_of(p["district"])
    ok = {"plain": ("plain", "any"), "high": ("high", "mid", "any"), "mid": ("mid", "any"), "hub": ("mid", "high", "any")}[reg]
    cand = [ph for ph in PHOTOS if ph["region"] in ok]
    key = p["district"] or "hub"
    th = p["theme"] if p["kind"] in ("theme", "main") else ("main" if p["kind"] == "hub" else "")
    def score(ph):
        wide = 0 if (second or p["kind"] not in ("main", "hub") or (ph["w"] > ph["h"] and ph["w"] >= 900)) else 1   # mukhya page ke upar badi chaudi photo
        big = 0 if (ph["w"] >= 1200 and ph["w"] > ph["h"]) else 1      # v3.3.2 audit-6: Google Discover/og ke liye 1200px+ chaudi
        return (wide, 1 if ph["file"] in skip else 0, 1 if ph["file"] in PH_DIST[key] else 0, 0 if th in ph["topics"] else 1,
                PH_USE[ph["file"]] // 5, big, 0 if ph["region"] == reg else 1, PH_USE[ph["file"]], ph["file"])
    best = min(cand, key=score)
    PH_USE[best["file"]] += 1
    PH_DIST[key].add(best["file"])
    return best


def photo_fig(ph, eager=False):
    tall = ph["h"] > ph["w"]
    return ('<figure class="shot%s"><img src="/%s" width="%d" height="%d" loading="%s"%s decoding="async" alt="%s">'
            '<figcaption>%s (photo: Sab Hisaab)</figcaption></figure>\n'
            % (" tall" if tall else "", ph["file"], ph["w"], ph["h"], "eager" if eager else "lazy",
               ' fetchpriority="high"' if eager else "", esc(ph["alt"]), esc(ph["alt"])))

NOTE = {
    "vaidya": "Is page ki gharelu nuskhe aur vaidya parampara wali baatein sirf lok-gyan aur itihaas ke roop mein likhi gayi hain, ilaaj ki salah nahi. Bimari ya chot mein doctor se hi salah lein; kisi jangli paudhe ko bina pehchaan ke na khayein.",
    "land": "Zameen ke naap aur kanoon ki ye jaankari aam samajh ke liye hai, kanooni salah nahi. Kharid-bikri se pehle tehsil, sub-registrar karyalay aur kisi vakil se taaza niyam zaroor milayein.",
    "sarkari": "Portal, fees aur niyam samay-samay par badalte hain. Aavedan se pehle official portal ya tehsil/zila karyalay se taaza jaankari lein. Apna OTP ya password kisi ko na batayein.",
    "tourism": "Sadak, mausam, permit aur kapat ki tithiyan har saal badalti hain. Yatra se pehle zila prashasan, Uttarakhand Tourism aur mausam vibhag ki taaza soochna dekh lein.",
    "transport": "Train, bus, udaan aur kiraye badalte rehte hain. Booking se pehle IRCTC, parivahan nigam ya airline ki site par taaza samay aur kiraya dekh lein.",
    "career": "Pariksha ki tithi, patrata aur syllabus ke liye hamesha UKPSC/UKSSSC ki official site par notification padhein. Yahan diye abhyas prashn asli pichhle prashn-patra nahi hain.",
}
DEFAULT_NOTE = ("Ye page aam jaankari ke liye hai. Doori, unchai, tithi aur aabadi jaise aankde alag-alag srot mein thode alag ho "
                "sakte hain; zaroori kaam se pehle zila prashasan ya official srot se ek baar milayein. Koi galti dikhe ya apne gaon ki "
                "jaankari jodni ho to contact page se batayein, hum jaanch kar sudhaar denge.")

def jld(o):
    return '<script type="application/ld+json">%s</script>' % json.dumps(o, ensure_ascii=False)

def li(slug, text, desc=None):
    d = (" &mdash; %s" % esc(desc)) if desc else ""
    return '<li data-ukli="%s"><a href="/%s" data-uk="%s">%s</a>%s</li>' % (slug, slug, slug, esc(text), d)

POLL_TI = {"food": 1, "buzurg": 2, "culture": 3, "shabd": 4}
DIDX = {d[1]: i + 1 for i, d in enumerate(DISTRICTS)}
GARHWAL = {"dehradun", "haridwar", "rudraprayag", "chamoli", "uttarkashi", "tehri-garhwal", "pauri-garhwal"}

def poll_block(p):
    """Rai-shumari (sahi-galat nahi). Code 98DDTT (6 ank) - /jawab ke 4-5 ank wale code se alag. Bina vote-URL ke chhupa rehta hai."""
    th = p.get("theme")
    if not p.get("district") or th not in POLL_TI:
        return ""
    D = p["D"]
    if th == "food":
        q, opts = "Aapke ghar mein Gahat ki daal ya Bhatt ki churkani kis bartan mein banti hai?", \
                  ["Lohe ki kadhai", "Pital ka bhaddu", "Pressure cooker", "Ab banti hi nahi"]
    elif th == "buzurg":
        q, opts = "Kya aapne kabhi Gharat (pan-chakki) ka pisa aata khaya hai?", ["Haan, bachpan mein", "Ab bhi khate hain", "Sirf suna hai"]
    elif th == "culture":
        q = "Aapka sabse pyaara pahadi tyohar kaun sa hai?"
        opts = ["Harela", "Phool Dei", "Igas (Budhi Diwali)", "Makar Sankranti"] if p["district"] in GARHWAL else \
               ["Harela", "Phool Dei", "Ghughutiya", "Kumaoni Holi"]
    else:
        q, opts = "Aap ghar mein kaun si boli bolte hain?", ["Garhwali", "Kumaoni", "Doosri pahadi boli", "Sirf Hindi"]
    code = "98%02d%02d" % (DIDX[p["district"]], POLL_TI[th])
    btns = "".join('<button type="button" data-o="%d">%s</button>' % (i, esc(o)) for i, o in enumerate(opts))
    return ('<div class="ukpoll" data-c="%s" hidden><b>🗳️ %s: aapki raay</b><p>%s</p>%s<p class="pr upd">'
            'Ek tap - koi naam ya login nahi. 30 vote ke baad sabka asli nateeja dikhega.</p></div>\n' % (code, esc(D), esc(q), btns))


def assemble(p, body_parts, faqs, by, img, extra_head=""):
    slug, title, desc = p["slug"], p["title"], p["desc"]
    url = SITE + "/" + slug
    full_title = title + " | Sab Hisaab"
    lang = p["lang"]
    top = TOP.replace('<html lang="hi-Latn">', '<html lang="%s">' % lang)
    iw, ih = IMGSZ[img[0]]
    crumbs = [("Home", SITE + "/"), ("Uttarakhand", SITE + "/uttarakhand")]
    if p["district"]:
        crumbs.append((p["D"], SITE + "/" + p["district"] + "-uttarakhand"))
    if slug not in ("uttarakhand",) and p["kind"] != "main":
        crumbs.append((p["label"] if p["kind"] == "theme" else p["title"][:60], url))
    elif p["kind"] == "main":
        pass
    bl = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)]}
    art = {"@context": "https://schema.org", "@type": "Article", "headline": p["h1"][:110], "description": desc,
           "inLanguage": lang, "datePublished": "@@PUB@@", "dateModified": "@@PUB@@",
           "image": [SITE + "/" + img[0]] + [SITE + "/" + f for f in p.get("_photos", []) if f != img[0]],
           "author": {"@type": "Person", "name": "Manoj Kumar Pandey", "url": SITE + "/author"},
           "publisher": {"@type": "Organization", "name": "Sab Hisaab", "url": SITE + "/",
                         "logo": {"@type": "ImageObject", "url": SITE + "/sab-hisaab-og.png"}},
           "mainEntityOfPage": {"@type": "WebPage", "@id": url},
           "about": {"@type": "Place", "name": (p["D"] + ", Uttarakhand") if p["district"] else "Uttarakhand, India"}}
    head = [top, '<meta name="theme-color" content="#0F766E">\n<meta name="color-scheme" content="light">\n'
            '<meta property="og:site_name" content="Sab Hisaab">\n<meta property="og:locale" content="hi_IN">\n'
            '<meta name="twitter:card" content="summary_large_image">\n',
            '<meta name="twitter:title" content="%s">\n' % esc(full_title),
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n', FAVICON, "\n",
            "<title>%s</title>\n" % esc(full_title),
            '<meta name="description" content="%s">\n' % esc(desc),
            '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">\n',
            '<link rel="canonical" href="%s">\n' % url,
            '<link rel="manifest" href="/manifest.json"><link rel="apple-touch-icon" href="/icon-192.png">\n',
            '<meta property="og:title" content="%s">\n' % esc(p["h1"]),
            '<meta property="og:description" content="%s">\n' % esc(desc),
            '<meta property="og:url" content="%s">\n<meta property="og:type" content="article">\n' % url,
            '<meta property="og:image" content="%s/%s">\n' % (SITE, img[0]),
            '<meta property="og:image:width" content="%d"><meta property="og:image:height" content="%d">\n' % (iw, ih),
            '<meta name="twitter:image" content="%s/%s">\n' % (SITE, img[0]),
            '<meta name="twitter:description" content="%s">\n' % esc(desc),
            FONTS, S1, "\n", S2, "\n", EXTRA_CSS, extra_head, jld(art), "\n"]
    if faqs:
        head.append(jld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}) + "\n")
    head.append(jld(bl) + "\n</head>\n<body>\n")
    vis = ['<a href="/">Home</a>', '<a href="/uttarakhand" data-uk="uttarakhand">Uttarakhand</a>'] if slug != "uttarakhand" else ['<a href="/">Home</a>', "<span>Uttarakhand</span>"]
    if p["district"] and p["kind"] != "main":
        vis.append('<a href="/%s-uttarakhand" data-uk="%s-uttarakhand">%s</a>' % (p["district"], p["district"], esc(p["D"])))
    words = sum(len(text_of(x).split()) for x in body_parts)
    body = ['<div class="pbar" id="pbar"></div>\n', HEADER, "\n<main>\n",
            '<div class="crumb">%s</div>\n' % " &rsaquo; ".join(vis),
            "<h1%s>%s</h1>\n" % (' lang="hi"' if is_deva(p["h1"]) else "", esc(p["h1"])),
            '<div class="meta">Lekhak: <a href="/author" style="color:inherit">Manoj Kumar Pandey</a> &middot; Aakhri update: '
            '<time datetime="@@PUB@@">@@PUBH@@</time> &middot; Padhne me ~%d minute</div>\n' % max(3, round(words / 200)),
            '<div class="gshare" id="gShare"><a class="wa" target="_blank" rel="noopener">🟢 WhatsApp par share</a>'
            '<button type="button" class="cp">🔗 Link copy karein</button></div>\n']
    body += body_parts
    body.append(UK_JS)
    body.append(FOOT)
    return "".join(head) + "".join(body)

def toc(rendered):
    hs = [(m.group(1), text_of(m.group(2))) for k, h, it in rendered if k == "h"
          for m in [re.match(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', h)] if m]
    if len(hs) < 3:
        return ""
    return '<div class="toc"><b>Is page me kya milega</b><ol>%s</ol></div>\n' % "".join(
        '<li><a href="#%s">%s</a></li>' % (i, esc(H.unescape(t))) for i, t in hs)

def related(p, by, theme_pages, main_pages):
    out = []
    d = p["district"]
    if d:
        sib = [s for s in theme_pages[d] if s != p["slug"]]
        rows = ([li(d + "-uttarakhand", "%s: poori zila guide" % p["D"])] if p["kind"] != "main" else []) + \
               [li(s, "%s: %s" % (p["D"], by[s]["label"])) for s in sib]
        out.append('<div class="ukrel" data-ukblk="1"><b>%s ke aur vishay</b><ul class="ukdir">%s</ul></div>\n'
                   % (esc(p["D"]), "".join(rows)))
        if p["kind"] == "theme":
            others = [o + "-" + THEMES[p["theme"]][0] for o in DORDER if o != d and (o + "-" + THEMES[p["theme"]][0]) in by]
            out.append('<div class="ukrel" data-ukblk="1"><b>Doosre zilon mein: %s</b><ul class="ukdir">%s</ul></div>\n'
                       % (esc(by[p["slug"]]["label"].lower()), "".join(li(s, by[s]["D"]) for s in others)))
        nb = [o for o in DORDER if o != d]
        out.append('<div class="ukrel" data-ukblk="1"><b>Uttarakhand ke 13 zile</b><ul class="ukdir">%s%s</ul></div>\n'
                   % (li("uttarakhand", "Uttarakhand: poori guide"), "".join(li(o + "-uttarakhand", DNAME[o]) for o in nb)))
    else:
        tops = [t for t in HUB_TOPIC_ORDER if t != p["slug"]]
        if p["slug"] != "uttarakhand":
            tops = ["uttarakhand"] + tops
        out.append('<div class="ukrel" data-ukblk="1"><b>Uttarakhand guide ke aur hisse</b><ul class="ukdir">%s</ul></div>\n'
                   % "".join(li(t, by[t]["label"] if t != "uttarakhand" else "Uttarakhand: poori guide") for t in tops))
        out.append('<div class="ukrel" data-ukblk="1"><b>Zile ke hisaab se poori jaankari</b><ul class="ukdir">%s</ul></div>\n'
                   % "".join(li(o + "-uttarakhand", DNAME[o]) for o in DORDER))
    if p["kind"] in ("hub", "hubtopic", "main", "tool"):
        from tools_content import TOOLS as _T
        tl = [k for k in _T if k != p["slug"]]
        out.append('<div class="ukrel" data-ukblk="1"><b>Uttarakhand ke free tool</b><ul class="ukdir">%s</ul></div>\n'
                   % "".join(li(k, _T[k]["title"]) for k in tl))
    tools = [t for t in (p.get("tools") or []) if os.path.exists(os.path.join(LIVE, t + ".html"))]
    if tools:
        names = {"nali-mutthi-converter": "Nali-Mutthi Converter", "nali-mutthi-square-feet": "Nali, Mutthi aur Bisi ka naap",
                 "zameen-kharidne-se-pehle-kagaz": "Zameen kharidne se pehle kaagaz", "fasal-munafa-calculator": "Fasal Munafa Calculator",
                 "uttarakhand-farmer-id-ukfr": "Uttarakhand Farmer ID (UKFR)", "agristack-guide": "AgriStack guide",
                 "stamp-duty-calculator": "Stamp Duty Calculator", "fuel-cost-calculator": "Fuel Cost Calculator (yatra ka kharcha)",
                 "temperature-converter": "Temperature Converter", "age-calculator": "Age Calculator (pariksha ki umar)",
                 "percentage-calculator": "Percentage Calculator", "emi-calculator": "EMI Calculator (ghar/gaadi)",
                 "mausam-weather": "Mausam (weather) dekhein", "din-bache-calculator": "Din Bache Calculator"}
        out.append('<div class="artread"><b>Kaam ke tool</b>%s</div>\n' % " &middot; ".join(
            '<a href="/%s">%s</a>' % (t, names.get(t, t)) for t in tools))
    return out

def build(out_dir=OUT):
    pages, internal, modmap = build_pages()
    log = []
    for p in pages:
        tidy_page(p, log)
        assign_ids(p)
    by = {p["slug"]: p for p in pages}
    order = priority(pages)
    hmap, mmap = ref_maps(pages, modmap)
    titles = {p["slug"]: (p["label"] if p["kind"] != "theme" else "%s: %s" % (p["D"], p["label"])) for p in pages}
    for p in pages:
        if p["kind"] == "main":
            titles[p["slug"]] = "%s: poori zila guide" % p["D"]
    theme_pages = collections.defaultdict(list)
    for th in ORDER[1:]:
        for d in DORDER:
            s = d + "-" + THEMES[th][0]
            if s in by:
                theme_pages[d].append(s)
    ex_p, ex_qa = existing_text()
    seen_p, seen_qa = dict(ex_p), dict(ex_qa)
    os.makedirs(os.path.join(out_dir, "pages"), exist_ok=True)
    manifest = []
    for rank, slug in enumerate(order):
        p = by[slug]
        rend = render_items(p, hmap, mmap, titles)
        parts, faqs, last_ptr = [], [], None
        for kind, h, extra in rend:
            if kind == "p":
                n = norm_p(extra)
                if len(n) > 120:
                    if n in seen_p and seen_p[n] != "/" + slug:
                        tgt = seen_p[n].strip("/")
                        log.append({"page": slug, "action": "dup_para_pointer", "to": tgt, "text": n[:90]})
                        if last_ptr == tgt:
                            continue
                        last_ptr = tgt
                        tt = titles.get(tgt) or by.get(tgt, {}).get("title") or tgt
                        if tgt in by:
                            parts.append('<p class="dupref">Is baare mein poori baat yahan di gayi hai: '
                                         '<a href="/%s" data-uk="%s">%s</a>.</p>\n' % (tgt, tgt, esc(tt)))
                        else:
                            parts.append('<p class="dupref">Is baare mein poori baat yahan di gayi hai: '
                                         '<a href="/%s">%s</a>.</p>\n' % (tgt, esc(tt)))
                        continue
                    seen_p.setdefault(n, "/" + slug)
                last_ptr = None
                parts.append(h + "\n")
            elif kind == "faq":
                q, a = extra
                key = (text_of(esc(q)).lower(), text_of("<p>%s</p>" % a).lower())
                an = norm_p(a)
                if (key in seen_qa and seen_qa[key] != "/" + slug):
                    tgt = seen_qa[key].strip("/")
                    log.append({"page": slug, "action": "dup_faq_pointer", "to": tgt, "q": q})
                    tt = titles.get(tgt) or tgt
                    parts.append(('<p class="dupref">Sawal &ldquo;%s&rdquo; ka jawab: <a href="/%s" data-uk="%s">%s</a>.</p>\n'
                                  % (esc(q), tgt, tgt, esc(tt))) if tgt in by else
                                 ('<p class="dupref">Sawal &ldquo;%s&rdquo; ka jawab: <a href="/%s">%s</a>.</p>\n' % (esc(q), tgt, esc(tt))))
                    continue
                seen_qa.setdefault(key, "/" + slug)
                if len(an) > 120:
                    seen_p.setdefault(an, "/" + slug)
                faqs.append((q, text_of(a)))
                parts.append(h.replace("<p>", '<div class="fa">', 1)[::-1].replace(">p/<", ">vid/<", 1)[::-1] + "\n")
                last_ptr = None
            else:
                last_ptr = None
                parts.append(h + "\n")
        # aakhri jaanch: isi page par 80%+ milte paragraph (audit niyam) -> doosra hatao, log mein darj
        pn = []
        for k_, x in enumerate(parts):
            m_ = re.match(r"<p[^>]*>(.*)</p>\n?$", x, re.S)
            if m_ and 'class="dupref"' not in x:
                n_ = norm_p(m_.group(1))
                if len(n_) > 120:
                    hit = next((o for o in pn if ratio(o, n_) >= 0.79), None)
                    if hit:
                        log.append({"page": slug, "action": "para_merge_post", "text": n_[:120]}); parts[k_] = ""; continue
                    pn.append(n_)
        parts = [x for x in parts if x]
        if 0 < len(faqs) < 4:     # pointer ke baad 4 se kam FAQ bache -> saada sawal-jawab
            new = []
            for x in parts:
                m = re.match(r'<details class="faq"([^>]*)><summary>(.*?)</summary><div class="fa">(.*?)</div></details>', x)
                new.append('<p%s><b>%s</b> %s</p>\n' % (m.group(1), m.group(2), m.group(3)) if m else x)
            parts, faqs = new, []
        # page ka dhancha: lead + hero + toc + content + jaal + note + srot
        img = (WIDE[rank % len(WIDE)] if p["kind"] in ("main", "hub") else IMAGES[rank % len(IMAGES)])
        ph = photo_for(p)
        if ph["w"] >= 1200 and ph["w"] > ph["h"]:          # social/Pinterest/og ke liye chaudi photo hi
            img = (ph["file"], ph["alt"])
        p["_photos"] = [ph["file"]]
        lead = '<p class="lead">%s</p>\n' % esc(p["desc"]) if not is_deva(p["desc"]) else '<p lang="hi">%s</p>\n' % esc(p["desc"])
        hero = ""
        if p["kind"] in ("main", "hub"):
            if ph["w"] > ph["h"] and ph["w"] >= 900:
                hero = photo_fig(ph, eager=True)
            else:
                hero = ('<figure class="shot"><img src="/%s" width="%d" height="%d" loading="eager" fetchpriority="high" '
                        'decoding="async" alt="%s"><figcaption>%s</figcaption></figure>\n'
                        % (img[0], IMGSZ[img[0]][0], IMGSZ[img[0]][1], esc(img[1]), esc(img[1])))
        if not (p["kind"] in ("main", "hub") and ph["w"] > ph["h"] and ph["w"] >= 900):
            # baaki page: apni photo pehle hisse ke baad (upar text rahe - padhne wala seedha jawab pehle dekhe)
            h2s = [i for i, x in enumerate(parts) if x.startswith("<h2")]
            at = h2s[1] if len(h2s) > 1 else len(parts)
            parts = parts[:at] + [photo_fig(ph)] + parts[at:]
        # v3.3.2 audit-6: lambe page (2,500+ shabd) par doosri, alag photo beech mein (81 photo - har page alag drishya)
        if len(re.sub(r"<[^>]+>", " ", "".join(parts)).split()) >= 2500:
            ph2 = photo_for(p, skip={ph["file"]}, second=True)
            if ph2["file"] != ph["file"]:
                h2s = [i for i, x in enumerate(parts) if x.startswith("<h2")]
                if len(h2s) >= 4:
                    at2 = h2s[len(h2s) // 2]
                    parts = parts[:at2] + [photo_fig(ph2)] + parts[at2:]
                    p["_photos"].append(ph2["file"])
                    if ph2["w"] >= 1200 and ph2["w"] > ph2["h"] and img[0] not in IMGSZ_OWN:
                        img = (ph2["file"], ph2["alt"])           # og/Discover ke liye apni chaudi photo
        tc = toc(rend)
        extra_top = []
        if p["kind"] == "main":
            rows = "".join(li(s, by[s]["label"][:1].upper() + by[s]["label"][1:], None) for s in theme_pages[p["district"]])
            extra_top.append('<div class="ukrel" data-ukblk="1"><b>%s ki poori guide: vishay chunein</b><ul class="ukdir">%s</ul></div>\n'
                             % (esc(p["D"]), rows))
        if p["slug"] == "uttarakhand":
            g = "".join(li(o + "-uttarakhand", DNAME[o], by[o + "-uttarakhand"]["mandal"] + " mandal") for o in DORDER)
            extra_top.append('<div class="ukrel" data-ukblk="1"><b>13 zilon ki alag guide</b><ul class="ukdir">%s</ul></div>\n' % g)
        rel = related(p, by, theme_pages, None)
        note = NOTE.get(p["theme"], DEFAULT_NOTE)
        srcs = ['<li><a href="https://uk.gov.in/" rel="nofollow noopener" target="_blank">Uttarakhand Sarkar (uk.gov.in)</a></li>',
                '<li><a href="https://uttarakhandtourism.gov.in/" rel="nofollow noopener" target="_blank">Uttarakhand Tourism</a></li>']
        if p["district"]:
            srcs.insert(0, '<li><a href="https://%s/" rel="nofollow noopener" target="_blank">%s zila prashasan (%s)</a></li>'
                        % (NIC[p["district"]], esc(p["D"]), NIC[p["district"]]))
        if p["theme"] in ("land", "sarkari") or "zameen" in slug:
            srcs.append('<li><a href="https://bhulekh.uk.gov.in/" rel="nofollow noopener" target="_blank">Uttarakhand Bhulekh</a></li>')
        if p["theme"] == "career" or "gk" in slug:
            srcs.append('<li><a href="https://psc.uk.gov.in/" rel="nofollow noopener" target="_blank">UKPSC</a></li>')
        tail = ['<div class="box" style="margin-top:22px"><b>Dhyan dein:</b> %s</div>\n' % esc(note),
                '<div class="srcbox"><b>Official source &mdash; yahin se confirm karein</b><ul>%s</ul></div>\n' % "".join(srcs)]
        # v3.3.2: 'Galti batayein' (attachment Layer 12) - pathak contact page se bataye; bot/owner jaanch kar sudhaarein
        tail.append('<p class="upd">Galti dikhi ya jaankari purani lage? <a href="/contact">Hamein batayein</a> &mdash; '
                    'srot se milaakar sudhaar kiya jaata hai.</p>\n')
        xh = ""
        pl = poll_block(p)
        if pl:                                  # v3.3.2: 'Gaon ki raay' 1-tap poll (asli ginti, 30 vote se pehle % nahi)
            cut = int(len(parts) * 0.45)
            at = next((i for i in range(cut, len(parts)) if parts[i].startswith("<h2")), len(parts))
            parts = parts[:at] + [pl] + parts[at:]
            xh = '<meta name="sh-vu" content="">\n'
        full = [lead, hero, tc] + extra_top + parts + rel + tail
        html = assemble(p, full, faqs, by, img, extra_head=xh)
        open(os.path.join(out_dir, "pages", slug + ".html"), "w", encoding="utf-8").write(html)
        links = sorted(set(re.findall(r'data-uk="([a-z0-9-]+)"', html)) - {slug})
        req = ["uttarakhand"] + ([p["district"] + "-uttarakhand"] if p["district"] and p["kind"] != "main" else [])
        manifest.append({"slug": slug, "rank": rank, "kind": p["kind"], "district": p["district"], "theme": p["theme"],
                         "title": p["title"], "links_to": links, "requires": [r for r in req if r != slug],
                         "images": sorted(set(re.findall(r'(?:src|content)="(?:https://sabhisaab\.com)?/([a-z0-9-]+\.webp)"', html))
                                          & {x["file"] for x in PHOTOS}),
                         "words": len(text_of(re.sub(r"<(script|style)\b.*?</\1>", "", html[html.find("<main>"):], flags=re.S)).split())})
    # v3.3.2: queue ke saath jaane wali apni photo (bot page ke saath hi website par daalta hai - pehle nahi, taaki 'faltu file' na bane)
    os.makedirs(os.path.join(out_dir, "img"), exist_ok=True)
    for f in sorted({x for m in manifest for x in m.get("images", [])}):
        shutil.copy2(os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos", f), os.path.join(out_dir, "img", f))
    # ---- 4 tool page
    from tools_content import TOOLS
    from tools import tool_parts, TOOL_CSS
    uk = set(by) | set(TOOLS)
    rank_of = {m["slug"]: m["rank"] for m in manifest}
    for i, (ts, t) in enumerate(TOOLS.items()):
        p = dict(slug=ts, kind="tool", district=None, D="Uttarakhand", mandal=None, boli=None, theme="tool", title=t["title"],
                 h1=t["h1"], desc=t["desc"], label=t["title"], tools=t["tools"], items=[], lang="hi-Latn")
        by[ts] = p
        parts, faqs, js = tool_parts(ts, uk)
        rel = related(p, by, theme_pages, None)
        tail = ['<div class="box" style="margin-top:22px"><b>Dhyan dein:</b> %s</div>\n' % esc(NOTE.get("tourism") if "dham" in ts else DEFAULT_NOTE),
                '<div class="srcbox"><b>Official source &mdash; yahin se confirm karein</b><ul>'
                '<li><a href="https://uk.gov.in/" rel="nofollow noopener" target="_blank">Uttarakhand Sarkar (uk.gov.in)</a></li>'
                '<li><a href="https://uttarakhandtourism.gov.in/" rel="nofollow noopener" target="_blank">Uttarakhand Tourism</a></li>'
                + ('<li><a href="https://sssc.uk.gov.in/" rel="nofollow noopener" target="_blank">UKSSSC</a></li>' if "quiz" in ts else "")
                + '</ul></div>\n']
        img = IMAGES[i % len(IMAGES)]
        html = assemble(p, parts + rel + tail + [js], faqs, by, img, extra_head=TOOL_CSS)
        open(os.path.join(out_dir, "pages", ts + ".html"), "w", encoding="utf-8").write(html)
        links = sorted(set(re.findall(r'data-uk="([a-z0-9-]+)"', html)) - {ts})
        manifest.append({"slug": ts, "rank": rank_of[t["after"]] + 0.5 + i / 100, "kind": "tool", "district": None,
                         "theme": "tool", "title": t["title"], "links_to": links, "requires": ["uttarakhand"],
                         "words": len(text_of(re.sub(r"<(script|style)\b.*?</\1>", "", html[html.find("<main>"):], flags=re.S)).split())})
    return pages, internal, manifest, log

if __name__ == "__main__":
    pages, internal, manifest, log = build()
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), ensure_ascii=False, indent=0)
    json.dump(log, open(os.path.join(OUT, "dedupe_log.json"), "w"), ensure_ascii=False, indent=0)
    c = collections.Counter(x["action"] for x in log)
    print(len(manifest), "pages", dict(c))
    ws = sorted(m["words"] for m in manifest)
    print("words min/med/max", ws[0], ws[len(ws)//2], ws[-1], "total", sum(ws))
