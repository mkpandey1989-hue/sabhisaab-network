"""v2.0: Website ki jaankari - bot khud padhta, yaad rakhta aur badlaav pakadta hai.

Roz (06:20) aur har deploy ke baad:
- Har page ka title/description/H1/shabd/lastmod -> data/site_index.json (bot ka dimaag, topic, caption isi se)
- Naya page aaya / hata -> alert + video topic mein apne aap (koi code nahi badalna)
- Privacy/Terms page badla -> alert; privacy mein "zyada se zyada N din" badla to bot ki safai-seema bhi wahi
- Website par social link (install-app.js) aur bot ke config.LINKS ka milan - farak ho to saaf batata hai
- Doctor: tool-naam wala link homepage (/) par, do page ka ek jaisa title/H1 (cannibalization), ek vaakya do baar,
  kam inbound link, aur Google ka index status (site repo state/daily.json) - har pending page ki sambhavit wajah
Sirf PADHTA hai. Website ki file kabhi khud nahi badalta (wo ZIP + audit ke raaste hi).
"""
import collections
import datetime
import difflib
import hashlib
import html as H
import json
import re
from . import state, tg, diary
from .config import DATA, SITE, LINKS, WHATSAPP, TELEGRAM, PINTEREST
from .log import log

INDEX = DATA / "site_index.json"


def _site_dir():
    from .website import DIR
    return DIR / "site"


def _txt(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def build():
    d = _site_dir()
    sm = (d / "sitemap.xml").read_text(encoding="utf-8") if (d / "sitemap.xml").exists() else ""
    lastmod = dict(re.findall(r"<loc>https://sabhisaab\.com/?([^<]*)</loc>\s*<lastmod>([^<]+)</lastmod>", sm))
    pages = {}
    for f in sorted(d.glob("*.html")):
        s = f.read_text(encoding="utf-8", errors="ignore")
        slug = "" if f.stem == "index" else f.stem
        body = re.sub(r"<(script|style)\b.*?</\1>", "", s[s.find("</head>"):], flags=re.S)
        t = re.search(r"<title>(.*?)</title>", s, re.S)
        ds = re.search(r'<meta name="description" content="([^"]*)"', s)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        rob = re.search(r'<meta name="robots" content="([^"]*)"', s)
        pages[slug] = {"title": H.unescape(_txt(t.group(1))) if t else "", "desc": H.unescape(ds.group(1)) if ds else "",
                       "h1": H.unescape(_txt(h1.group(1))) if h1 else "", "words": len(_txt(body).split()),
                       "lastmod": lastmod.get(slug, ""), "in_sitemap": slug in lastmod,
                       "noindex": bool(rob and "noindex" in rob.group(1)),
                       "links": sorted(set(re.findall(r'href="/([a-z0-9\-]*)"', body)))}
    return pages


def _index_status():
    from .website import DIR, KEEP
    for p in (DIR / "state" / "daily.json", KEEP / "daily.json"):
        try:
            st = json.loads(p.read_text()).get("status", {})
            if st:
                return {u.replace(SITE, "").strip("/"): v for u, v in st.items()}
        except Exception:
            pass
    return {}


def refresh(notify=False):
    """Index banao, purane se milao, badlaav batao. Returns list of change lines."""
    try:
        from .website import sync
        sync()
    except Exception as e:
        log(f"siteknow sync: {e}")
    pages = build()
    if not pages:
        return []
    ist = _index_status()
    for k, v in pages.items():
        x = ist.get(k)
        if x:
            v["indexed"], v["why"] = bool(x.get("ok")), x.get("why", "")
    try:
        old = json.loads(INDEX.read_text()).get("pages", {})
    except Exception:
        old = {}
    lines = []
    new = [k for k in pages if k not in old and pages[k]["in_sitemap"]]
    gone = [k for k in old if k not in pages]
    if old and new:
        lines.append("🆕 Naye page (video topic mein apne aap): " + ", ".join("/" + k for k in new[:15]))
    if old and gone:
        lines.append("🗑 Hate page (bot ab inka link nahi dega): " + ", ".join("/" + k for k in gone[:15]))
    h = {}
    for leg in ("privacy", "terms", "disclaimer", "links", "about"):
        f = _site_dir() / f"{leg}.html"
        if f.exists():
            h[leg] = hashlib.md5(f.read_bytes()).hexdigest()
    oldh = state.get("legal_hash") or {}
    ch = [k for k in h if oldh and oldh.get(k) and oldh[k] != h[k]]
    if ch:
        lines.append("📜 Badle legal page: " + ", ".join("/" + k for k in ch) + " - bot ne naye niyam padh liye.")
    state.put("legal_hash", h)
    days = retain_days()
    if days:
        state.put("privacy_retain_days", days)
    INDEX.write_text(json.dumps({"t": str(datetime.datetime.now())[:16], "pages": pages}, ensure_ascii=False))
    links = link_mismatch()
    if links:
        lines.append("🔗 Website aur bot ke channel link mein farak: " + "; ".join(links[:6]))
    if lines:
        diary.add("setting", "website badlaav: " + " | ".join(lines)[:400])
        if notify:
            tg.alert("yellow", "🌐 Website mein badlaav pakda:\n" + "\n".join(lines))
    return lines


def pages():
    try:
        return json.loads(INDEX.read_text()).get("pages", {})
    except Exception:
        return {}


def retain_days():
    f = _site_dir() / "privacy.html"
    try:
        m = re.search(r"zyada se zyada\s*(?:<[^>]+>)?\s*(\d{1,3})\s*din", f.read_text(encoding="utf-8"))
        return int(m.group(1)) if m else None
    except Exception:
        return None


def link_mismatch():
    f = _site_dir() / "install-app.js"
    try:
        s = f.read_text(encoding="utf-8")
    except Exception:
        return []
    want = {u.rstrip("/") for d in LINKS.values() for u in d.values()} | {WHATSAPP, TELEGRAM, PINTEREST.rstrip("/")}
    have = {u.rstrip("/") for u in re.findall(r'"(https://[^"]+)"', s)}
    out = [f"website par nahi: {u}" for u in sorted(want - have)]
    out += [f"bot mein nahi: {u}" for u in sorted(have - want) if "sabhisaab.com" not in u]
    return out


def find(q, n=6):
    """Naam/keyword se page dhoondho (bot ke dimaag ke liye)."""
    q = q.lower().strip()
    ws = [w for w in re.split(r"[^a-z0-9]+", q) if len(w) > 1]
    sc = []
    for k, v in pages().items():
        hay = (k + " " + v["title"] + " " + v["h1"]).lower()
        s = sum(2 if w in k else 1 for w in ws if w in hay)
        if s:
            sc.append((s, k, v))
    sc.sort(key=lambda x: -x[0])
    return [(k, v) for _, k, v in sc[:n]]


def not_indexed():
    return [k for k, v in pages().items() if v.get("indexed") is False and v.get("in_sitemap")]


def doctor(slug_only=None):
    """Har pending (index nahi) page ki sambhavit wajah + poori site ki aam galtiyan."""
    pg = pages()
    if not pg:
        return "Website index abhi nahi bana - thodi der baad (ya '🌐 Website haal')."
    inb = collections.Counter(t for v in pg.values() for t in v["links"])
    d = _site_dir()
    home_cta, dup_sent = [], []
    for f in sorted(d.glob("*.html")):
        s = f.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'<a [^>]*href="/"[^>]*>([^<]{2,80})</a>', s):
            a = H.unescape(m.group(1))
            if re.search(r"(calculator|converter|kholein|generator)", a, re.I) and not re.search(r"(saare|sabhi|\d{3})", a, re.I):
                home_cta.append(f"{f.stem}: '{a[:30]}'")
        if re.search(r"([A-Z][^.<>]{30,200}\.)\s*\1", _txt(s)):
            dup_sent.append(f.stem)
    lines = ["🩺 Website doctor"]
    pend = [slug_only] if slug_only else not_indexed()
    for k in pend:
        v = pg.get(k)
        if not v:
            continue
        why = []
        for k2, v2 in pg.items():
            if k2 != k and v2["h1"] and (difflib.SequenceMatcher(None, v["h1"].lower(), v2["h1"].lower()).ratio() > 0.8
                                         or difflib.SequenceMatcher(None, v["title"].lower(), v2["title"].lower()).ratio() > 0.8):
                why.append(f"'/{k2}' se title/H1 lagbhag same (Google ek hi rakhta hai)")
        if inb[k] < 4:
            why.append(f"andar ke link kam ({inb[k]})")
        if v["words"] < 900:
            why.append(f"content chhota ({v['words']} shabd)")
        if k in dup_sent:
            why.append("ek vaakya do baar")
        if any(x in k for x in ("stopwatch", "random", "converter", "generator", "timer")):
            why.append("aam tool - Google khud widget dikhata hai; bahar ke link (Pinterest/Threads/FB) sabse zyada madad")
        if not why:
            why.append("technical sab theek - samay + bahar ke link + GSC Request Indexing")
        lines.append(f"• /{k} ({v.get('why') or 'index nahi'}): " + "; ".join(why))
    if not slug_only:
        if home_cta:
            lines.append(f"⚠️ Tool-naam wale link homepage par ({len(home_cta)}): " + ", ".join(home_cta[:8]))
        if dup_sent:
            lines.append(f"⚠️ Ek vaakya do baar ({len(dup_sent)} page): " + ", ".join(dup_sent[:8]))
        lm = collections.Counter(v["lastmod"] for v in pg.values() if v["lastmod"])
        if lm and lm.most_common(1)[0][1] > len(pg) * 0.6:
            lines.append(f"ℹ️ {lm.most_common(1)[0][1]} page ki lastmod ek hi din ({lm.most_common(1)[0][0]}) - "
                         "galat nahi, par sirf asli badlaav par hi tareekh badlein.")
        lines.append("Bot ka kaam: pending page ko roz ki video/pin/thread mein pehle leta hai (bahar se link = Google jaldi aata hai).")
    return "\n".join(lines)[:3900]
