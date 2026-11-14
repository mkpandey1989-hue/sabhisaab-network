"""v3.3.0 (14 Nov 2026) - Page Queue: badi content ZIP (abhi: Uttarakhand ke 264 page) ko roz thoda-thoda, priority se, khud live karna.

Owner: "ZIP bot ko bhejunga, bot priority wise daily khud live kare, Google policy ke hisaab se, mujhe message aaye kaunse link
index karne hain, Bing par bhi jaaye; koi data delete nahi, duplicate nahi, website tute nahi."

Kaise:
- Queue ZIP pehchaan: andar 'ukqueue/manifest.json' + 'ukqueue/pages/<slug>.html'. Bot puchta hai (dohri pushti), phir
  data/pagequeue/ mein rakhta hai. Website par kuch nahi jaata jab tak roz ka samay na aaye.
- Roz 06:40 IST ke baad ek baar: manifest ke 'rank' kram se aaj ke page (default 8, kabhi 10 se zyada nahi - website ka
  NEW_PAGES_PER_DAY niyam, aur us din pehle se chadhe naye page bhi gine jaate hain). Shart: har naye page par kam se kam 3
  andar ke link (live pages se), aur uska 'requires' (hub/zila page) pehle live.
- Link-gating: jo page abhi live nahi, uska link nahi lagta (sirf text) - koi tuta link (404) kabhi nahi. Jaise-jaise page live
  hote hain, pehle wale pages ke link khud jud jaate hain (wahi file dobara, bina nayi tareekh - fake taazgi nahi).
- Sab kuch website._apply_zip ke audit gate se: audit ERROR = kuch nahi chadhta, owner ko laal alert, agle din dobara.
- Sitemap mein naye URL (asli publish tareekh), IndexNow/Google sitemap deploy ke baad purane raaste se (sirf naye page),
  Bing API apne aap 'naya/badla page' kram se.
- Deploy ke ~25 min baad page live jaanch kar owner ko: aaj ke URL + Google Search Console 'Request indexing' kram.
- Kabhi nahi: Indexing API (sirf job/live-video ke liye hai), ek din mein bulk IndexNow, nakli lastmod, page mitaana.
"""
import datetime
import json
import os
import re
import shutil
import threading
import time
import zipfile
import requests
from . import state, tg, diary
from .config import DATA, IST, NEW_PAGES_PER_DAY
from .log import log

QDIR = DATA / "pagequeue"
SITE = "https://sabhisaab.com"
DEFAULT_PER_DAY = 8
START_HHMM = "06:40"
_LOCK = threading.Lock()
SLUG_RX = re.compile(r"^[a-z0-9][a-z0-9-]{1,90}$")
IMG_RX = re.compile(r"^[a-z0-9][a-z0-9-]{1,90}\.webp$")
IMG_REF = re.compile(r'(?:src|content)="(?:https://sabhisaab\.com)?/([a-z0-9][a-z0-9-]{1,90}\.webp)"')
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

# Hub ka link in purane (pehle se live) pages par - ek baar, jis din hub live ho. Sirf maujood file par.
INJECT_PAGES = ["uttarakhand-farmer-id-ukfr", "nali-mutthi-square-feet", "nali-mutthi-converter", "bigha-kitna-hota-hai",
                "agristack-guide", "guides"]
INJECT_SNIP = ('<div class="artread"><b>Uttarakhand guide</b><a href="/uttarakhand">Uttarakhand ki poori jaankari: 13 zile, '
               'Char Dham, pahadi khana, nali-mutthi aur bhoo-kanoon</a></div>')
INJ_MARK = "<!--uk-hub-link-->"


# ------------------------------------------------------------------ shuddh (pure) hissa - tests/smoke.py isse jaanchta hai
GATE_MARK = "<!--ukg2-->"


def gate(html, live, pubdate, tools_count=None):
    """Jo page live nahi, uska link 'so' jaata hai (span/hidden - Google ko koi link nahi dikhta, text rehta hai); tareekh bharo.
    v3.3.1: ulta ho sakne wala markup - baad mein activate() sirf ye nishaan jagata hai, page ka baaki kuch nahi chhedta
    (taaki website ke doosre sudhaar - footer, privacy, owner mode - kabhi wapas na palte)."""
    def li(m):
        return m.group(0) if m.group(1) in live else m.group(0).replace("<li ", "<li hidden ", 1)
    html = re.sub(r'<li data-ukli="([a-z0-9-]+)">.*?</li>', li, html, flags=re.S)

    def a(m):
        if m.group(2) in live:
            return m.group(0)
        return '<span data-ukg="%s" data-h="/%s">%s</span>' % (m.group(2), m.group(1), m.group(3))
    html = re.sub(r'<a href="/([a-z0-9-]+(?:#[a-z0-9-]+)?)" data-uk="([a-z0-9-]+)">(.*?)</a>', a, html, flags=re.S)
    html = _hide_empty(html)
    if GATE_MARK not in html and "</main>" in html:
        html = html.replace("</main>", GATE_MARK + "</main>", 1)
    d = datetime.date.fromisoformat(pubdate)
    html = html.replace("@@PUB@@", pubdate).replace("@@PUBH@@", "%d %s %d" % (d.day, MONTHS[d.month - 1], d.year))
    if tools_count:
        html = re.sub(r"Saare \d{2,4} Tools", "Saare %d Tools" % tools_count, html)
    return vu_fill(html)


def vu_fill(html, vu=None):
    """v3.3.2: 'Gaon ki raay' poll ka vote-pata (sabhisaab-votes Worker, votes.py) - chalu ho tabhi; khaali = poll chhupa rehta hai."""
    if '<meta name="sh-vu" content="' not in html:
        return html
    if vu is None:
        try:
            from . import votes
            vu = votes.url() if state.get("votes_on") else ""
        except Exception:
            vu = ""
    vu = vu if re.match(r"^https://[A-Za-z0-9.-]+(?::\d+)?$", vu or "") else ""
    return re.sub(r'<meta name="sh-vu" content="[^"]*">', '<meta name="sh-vu" content="%s">' % vu, html, count=1)


def _hide_empty(html):
    """Jis link-dabbe ki saari li chhupi hon, wo dabba bhi chhupa; ek bhi khuli ho to dikhe."""
    def blk(m):
        body = m.group(0)
        shown = re.search(r'<li data-ukli="', body)
        body = body.replace('<div class="ukrel" hidden data-ukblk="1">', '<div class="ukrel" data-ukblk="1">')
        return body if shown else body.replace('<div class="ukrel" data-ukblk="1">', '<div class="ukrel" hidden data-ukblk="1">', 1)
    return re.sub(r'<div class="ukrel"(?: hidden)? data-ukblk="1">.*?</div>', blk, html, flags=re.S)


def activate(html, live):
    """Pehle se live page mein sirf soye hue link jagao (jo ab live hain). Baaki file waisi hi. -> naya html"""
    def li(m):
        return m.group(0).replace("<li hidden ", "<li ", 1) if m.group(1) in live else m.group(0)
    html = re.sub(r'<li hidden data-ukli="([a-z0-9-]+)">.*?</li>', li, html, flags=re.S)

    def sp(m):
        return ('<a href="%s" data-uk="%s">%s</a>' % (m.group(2), m.group(1), m.group(3))) if m.group(1) in live else m.group(0)
    html = re.sub(r'<span data-ukg="([a-z0-9-]+)" data-h="([^"]+)">(.*?)</span>', sp, html, flags=re.S)
    return vu_fill(_hide_empty(html))


def inbound(slug, live_after, links, inj):
    return sum(1 for q in live_after if q != slug and slug in links.get(q, ())) + inj.get(slug, 0)


def select(manifest, live, per_day, inj=None):
    """Rank kram mein aaj ke page; har chune page par 3+ andar ke link aur 'requires' pehle/saath live."""
    inj = inj or {}
    links = {m["slug"]: set(m.get("links_to", [])) for m in manifest}
    req = {m["slug"]: m.get("requires", []) for m in manifest}
    cand = [m["slug"] for m in sorted(manifest, key=lambda x: x["rank"]) if m["slug"] not in live]
    banned, chosen = set(), []
    for _ in range(40):
        for s in cand:
            if len(chosen) >= per_day:
                break
            if s in chosen or s in banned:
                continue
            if all(r in live or r in chosen for r in req[s]):
                chosen.append(s)
        after = set(live) | set(chosen)
        bad = [s for s in chosen if inbound(s, after, links, inj) < 3 or not all(r in after for r in req[s])]
        if not bad:
            return chosen
        for s in bad:
            chosen.remove(s)
            banned.add(s)
    return chosen


def page_images(htmls, on_site, in_queue):
    """Aaj ke page jin apni photo ko dikhate hain aur jo website par abhi nahi - wahi (queue mein ho to). Photo page se pehle nahi
    jaati (warna 'faltu file'), aur kabhi tuti photo (404) nahi."""
    need = set()
    for h in htmls:
        need |= set(IMG_REF.findall(h))
    return sorted(n for n in need if n not in on_site and n in in_queue)


def sitemap_add(sm, entries, base=SITE):
    """entries: [(slug, lastmod, image)] - alphabetical kram mein; pehle se ho to sirf lastmod."""
    for slug, lastmod, img in entries:
        loc = "%s/%s" % (base, slug)
        if "<loc>%s</loc>" % loc in sm:
            sm = re.sub(r"(<loc>%s</loc>\s*<lastmod>)[\d-]+" % re.escape(loc), lambda m: m.group(1) + lastmod, sm)
            continue
        block = ("<url>\n<loc>%s</loc>\n<lastmod>%s</lastmod>\n<changefreq>monthly</changefreq>\n<priority>0.7</priority>\n"
                 "<image:image><image:loc>%s/%s</image:loc></image:image>\n</url>\n") % (loc, lastmod, base, img)
        pos = None
        for m in re.finditer(r"<url>\s*<loc>%s/([^<]*)</loc>" % re.escape(base), sm):
            if m.group(1) and m.group(1) > slug:
                pos = m.start()
                break
        if pos is None:
            pos = sm.rfind("</urlset>")
        sm = sm[:pos] + block + sm[pos:]
    return sm


def inject(html, snippet=INJECT_SNIP):
    if INJ_MARK in html or "</main>" not in html:
        return html
    i = html.find('<div class="artread">')
    pos = i if i != -1 else html.find("</main>")
    return html[:pos] + INJ_MARK + snippet + "\n" + html[pos:]


def inject_home(html):
    """Homepage ke footer 'Categories' mein Uttarakhand (ek baar). Homepage ka baaki kuch nahi chhedta."""
    if 'href="/uttarakhand"' in html:
        return html
    i = html.find('<div class="hubbar">')
    if i == -1:
        return html
    j = html.find(' &middot; <a href="/">Saare', i)
    if j == -1:
        return html
    return html[:j] + ' &middot; <a href="/uttarakhand">Uttarakhand</a>' + html[j:]


def is_queue_zip(names):
    return any(n.replace("\\", "/").endswith("ukqueue/manifest.json") for n in names)


# ------------------------------------------------------------------ queue ki file (VM par)
def manifest():
    try:
        return json.loads((QDIR / "manifest.json").read_text(encoding="utf-8"))
    except Exception:
        return []


def _site_dir():
    from . import website
    return website.DIR / "site"


def live_slugs():
    d = _site_dir()
    return {f.stem for f in d.glob("*.html")} if d.exists() else set()


def load_zip(path):
    """ZIP jaancho aur data/pagequeue mein rakho. Website par kuch nahi jaata. -> sandesh"""
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        root = next(n for n in names if n.replace("\\", "/").endswith("ukqueue/manifest.json"))
        pre = root[: -len("manifest.json")]
        man = json.loads(z.read(root).decode("utf-8"))
        if not isinstance(man, list) or not man:
            return "❌ Queue ZIP ka manifest khaali/galat hai."
        pages = {}
        for m in man:
            s = str(m.get("slug", ""))
            if not SLUG_RX.match(s):
                return f"❌ Galat page naam: {s[:40]}"
            n = f"{pre}pages/{s}.html"
            if n not in names:
                return f"❌ Page file nahi mili: {s}"
            pages[s] = z.read(n)
        imgs = {}                                # v3.3.2: owner ki apni photo (ukqueue/img/*.webp) - page ke saath hi live
        for n in names:
            b = n.replace("\\", "/")
            if b.startswith(pre + "img/") and IMG_RX.match(b[len(pre) + 4:]):
                imgs[b[len(pre) + 4:]] = z.read(n)
    tmp = QDIR.with_name("pagequeue.new")
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "pages").mkdir(parents=True)
    old = manifest()
    keep = {m["slug"]: m for m in old}
    for m in man:
        keep[m["slug"]] = m                  # naya batch purani entry ki jagah (page mitaaya nahi jaata)
    for s, b in pages.items():
        (tmp / "pages" / f"{s}.html").write_bytes(b)
    (tmp / "img").mkdir()
    for nm, b in imgs.items():
        (tmp / "img" / nm).write_bytes(b)
    if (QDIR / "img").exists():
        for f in (QDIR / "img").glob("*.webp"):
            if not (tmp / "img" / f.name).exists():
                shutil.copy2(f, tmp / "img" / f.name)
    if (QDIR / "pages").exists():            # purani file jo naye batch mein nahi - rakho
        for f in (QDIR / "pages").glob("*.html"):
            if not (tmp / "pages" / f.name).exists():
                shutil.copy2(f, tmp / "pages" / f.name)
    (tmp / "manifest.json").write_text(json.dumps(sorted(keep.values(), key=lambda x: x["rank"]), ensure_ascii=False),
                                       encoding="utf-8")
    shutil.rmtree(QDIR, ignore_errors=True)
    tmp.rename(QDIR)
    live = live_slugs()
    left = [m for m in manifest() if m["slug"] not in live]
    per = int(state.get("pq_per_day") or DEFAULT_PER_DAY)
    state.put("pq_loaded", {"t": str(datetime.date.today()), "n": len(man), "file": os.path.basename(str(path))})
    diary.add("upload", f"page queue: {len(man)} page aaye ({len(left)} baaki)")
    return (f"✅ Queue mein {len(man)} page rakh diye (website par abhi kuch nahi gaya). Baaki {len(left)} page roz {per} ke "
            f"hisaab se ~{-(-len(left) // per)} din mein, har subah {START_HHMM} ke baad, audit ke saath live honge.")


# ------------------------------------------------------------------ roz ka kaam
def _tools_count():
    try:
        m = re.search(r"Saare (\d{2,4}) Tools", (_site_dir() / "index.html").read_text(encoding="utf-8"))
        return int(m.group(1)) if m else None
    except Exception:
        return None


def _today():
    return datetime.datetime.now(IST).date()


def due(now=None):
    now = now or datetime.datetime.now(IST)
    if not state.get("pq_on") or state.get("paused") or state.get("pq_day") == str(now.date()):
        return False
    return now.strftime("%H:%M") >= START_HHMM and bool(manifest())


def run_day(force=False):
    if not _LOCK.acquire(blocking=False):
        return "⏳ Queue pehle se chal rahi hai."
    try:
        return _run_day(force)
    except Exception as e:
        log(f"pagequeue: {e}")
        tg.alert("yellow", f"🏔️ Page queue aaj ruk gayi: {str(e)[:200]}. Kal phir koshish hogi (kuch live nahi hua).")
        return f"❌ {e}"
    finally:
        _LOCK.release()


def _run_day(force):
    from . import website
    today = str(_today())
    if not force and state.get("pq_day") == today:
        return "Aaj ki queue ho chuki."
    man = manifest()
    if not man:
        return "Queue khaali hai."
    website.sync()
    live = live_slugs()
    per = min(int(state.get("pq_per_day") or DEFAULT_PER_DAY), NEW_PAGES_PER_DAY)
    room = NEW_PAGES_PER_DAY - website._new_pages_today(0)
    per = max(0, min(per, room))
    if per == 0:
        state.put("pq_day", today)
        return "Aaj website par pehle hi 10 naye page chadh chuke - queue kal."
    inj = {"uttarakhand": sum(1 for p in INJECT_PAGES if (_site_dir() / f"{p}.html").exists()) + 1}   # +1 = homepage footer
    chosen = select(man, live, per, inj)
    if not chosen:
        left = [m for m in man if m["slug"] not in live]
        state.put("pq_day", today)
        if not left:
            state.put("pq_on", False)
            tg.alert("green", "🏔️ Page queue poori: saare page live. Queue band (nayi ZIP aaye to phir chalegi).")
            return "Queue poori."
        return "Aaj koi page sharton par poora nahi utra (link/kram) - kal dobara."
    after = live | set(chosen)
    pub = state.get("pq_pub") or {}
    tc = _tools_count()
    out = QDIR / "today"
    shutil.rmtree(out, ignore_errors=True)
    (out / "site").mkdir(parents=True)
    files = []
    imgs = {}
    for s in chosen:
        src = (QDIR / "pages" / f"{s}.html").read_text(encoding="utf-8")
        html = gate(src, after, today, tc)
        (out / "site" / f"{s}.html").write_text(html, encoding="utf-8")
        files.append(f"site/{s}.html")
        m = re.search(r'og:image" content="https://sabhisaab\.com/([^"]+)"', html)
        imgs[s] = m.group(1) if m else "sab-hisaab-og.png"
    regated = 0
    for m in man:                            # pehle ke live queue-page: naye live page ke link jodo (tareekh wahi)
        s = m["slug"]
        if s in chosen or s not in live or s not in pub:
            continue
        cur = (_site_dir() / f"{s}.html")
        if not cur.exists():
            continue
        old = cur.read_text(encoding="utf-8")
        if GATE_MARK in old:
            new = activate(old, after)              # v3.3.1: live file mein sirf link jagao (doosre sudhaar surakshit)
        else:                                        # v3.3.0 ka purana markup (sirf 14 Nov ke 8 page): ek baar source se
            new = gate((QDIR / "pages" / f"{s}.html").read_text(encoding="utf-8"), after, pub[s], tc)
        if new != old:
            (out / "site" / f"{s}.html").write_text(new, encoding="utf-8")
            files.append(f"site/{s}.html")
            regated += 1
    injected = []
    if "uttarakhand" in after and not state.get("pq_inj_done"):
        for p in INJECT_PAGES:
            f = _site_dir() / f"{p}.html"
            if f.exists():
                h = f.read_text(encoding="utf-8")
                h2 = inject(h)
                if h2 != h:
                    (out / "site" / f"{p}.html").write_text(h2, encoding="utf-8")
                    files.append(f"site/{p}.html")
                    injected.append(p)
        f = _site_dir() / "index.html"
        if f.exists():
            h = f.read_text(encoding="utf-8")
            h2 = inject_home(h)
            if h2 != h:
                (out / "site" / "index.html").write_text(h2, encoding="utf-8")
                files.append("site/index.html")
                injected.append("index")
    for nm in page_images([(out / f).read_text(encoding="utf-8") for f in files if f.endswith(".html")],
                          {f.name for f in _site_dir().glob("*.webp")}, {f.name for f in (QDIR / "img").glob("*.webp")}
                          if (QDIR / "img").exists() else set()):
        shutil.copy2(QDIR / "img" / nm, out / "site" / nm)
        files.append(f"site/{nm}")
    sm = (_site_dir() / "sitemap.xml").read_text(encoding="utf-8")
    (out / "site" / "sitemap.xml").write_text(sitemap_add(sm, [(s, today, imgs[s]) for s in chosen]), encoding="utf-8")
    files.append("site/sitemap.xml")
    zp = QDIR / f"today-{today}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(out / f, f)
    before_changed = list(state.get("site_changed") or [])
    res = website.apply_zip(str(zp), force=False)
    shutil.rmtree(out, ignore_errors=True)
    zp.unlink(missing_ok=True)
    if not res.startswith("✅"):
        tg.alert("red", "🏔️ Page queue: aaj ke page audit mein ruk gaye, website par kuch nahi gaya. Kal dobara koshish.\n" + res[:1500])
        state.put("pq_last_error", {"t": today, "err": res[:1500]})
        return res
    # IndexNow/sitemap sirf aaj ke NAYE page ke liye (re-gate/inject wale purane page ki baar-baar ping nahi)
    state.put("site_changed", sorted(set(before_changed + [f"site/{s}.html" for s in chosen])))
    for s in chosen:
        pub[s] = today
    state.put("pq_pub", pub)
    state.put("pq_day", today)
    if injected:
        state.put("pq_inj_done", True)
    state.put("pq_notify", {"t": time.time() + 25 * 60, "urls": chosen, "day": today})
    hist = state.get("pq_hist") or []
    hist.append({"d": today, "n": len(chosen), "slugs": chosen})
    state.put("pq_hist", hist[-60:])
    diary.add("upload", f"page queue: {len(chosen)} naye page ({regated} purane page mein link jude)")
    return f"✅ Queue: {len(chosen)} naye page chadhe, {regated} purane page mein naye link, inject {len(injected)}. {res}"


def _is_live(u):
    try:
        r = requests.get(u, timeout=20, headers={"User-Agent": "SabHisaab-bot-livecheck"})
        return r.status_code == 200 and "<h1" in r.text
    except Exception:
        return False


def tick():
    """Bot loop har minute: deploy ke baad (25 min) URL live jaancho, phir owner ko GSC/Bing ka sandesh."""
    n = state.get("pq_notify") or {}
    if not n or time.time() < float(n.get("t", 0)):
        return
    urls = [f"{SITE}/{s}" for s in n.get("urls", [])]
    ok = [u for u in urls if _is_live(u)]
    if len(ok) < len(urls) and float(n.get("tries", 0)) < 4:
        n["t"] = time.time() + 20 * 60
        n["tries"] = float(n.get("tries", 0)) + 1
        state.put("pq_notify", n)
        return
    state.put("pq_notify", {})
    tg.say(owner_message(ok, [u for u in urls if u not in ok]))


def owner_message(ok, bad=()):
    man = manifest()
    live = live_slugs()
    left = len([m for m in man if m["slug"] not in live])
    per = int(state.get("pq_per_day") or DEFAULT_PER_DAY)
    lines = [f"🏔️ Aaj {len(ok)} naya page LIVE (Uttarakhand):"]
    lines += [f"{i}. {u}" for i, u in enumerate(ok, 1)]
    old_ni = [s for s in request_list([u.replace(SITE + "/", "") for u in ok]) if f"{SITE}/{s}" not in ok]
    if old_ni:                                   # v3.3.2: bot ki Google-jaanch mein jo purane page abhi index nahi
        lines.append("Purane page jo Google ne index nahi kiye ya index se nikal gaye (roz ki Google jaanch) - inka bhi Request indexing:")
        lines += [f"{len(ok) + i}. {SITE}/{s}" for i, s in enumerate(old_ni, 1)]
    if bad:
        lines.append("⚠️ Ye abhi live nahi dikhe (bot kal phir jaanchega): " + ", ".join(bad))
    if ok:
        lines += ["", "👉 Aapka kaam (5 min, sirf Google):",
                  "Google Search Console → upar 'URL inspection' mein upar se ek-ek URL daalein → 'Request indexing'. "
                  "Google roz lagbhag 10 hi leta hai - jitne ho sakein upar se karein, baaki Google sitemap se khud dhoondhega.",
                  "https://search.google.com/search-console",
                  "Bing + IndexNow + Google sitemap: bot ne khud bhej diya (kuch nahi karna)."]
    lines.append(f"\nBaaki {left} page, roz {per} = ~{-(-left // per) if per else 0} din. 'queue haal' se poora haal.")
    return "\n".join(lines)


def status_text():
    man = manifest()
    if not man:
        return "🏔️ Page queue khaali hai. Queue ZIP (andar ukqueue/manifest.json) bot ko bhejein."
    live = live_slugs()
    done = [m for m in man if m["slug"] in live]
    left = sorted([m for m in man if m["slug"] not in live], key=lambda x: x["rank"])
    per = int(state.get("pq_per_day") or DEFAULT_PER_DAY)
    nxt = select(man, live, per, {"uttarakhand": len(INJECT_PAGES) + 1})
    err = state.get("pq_last_error") or {}
    s = [f"🏔️ Page queue: {'CHALU' if state.get('pq_on') else 'BAND'} | live {len(done)}/{len(man)} | roz {per} | "
         f"~{-(-len(left) // per) if per else 0} din baaki",
         f"Aakhri din: {state.get('pq_day') or '-'} | roz {START_HHMM} IST ke baad",
         "Agle page: " + (", ".join(nxt) if nxt else "-")]
    if err:
        s.append(f"Aakhri rukawat ({err.get('t')}): {err.get('err', '')[:300]}")
    gs = gidx_summary()
    if gs:
        s.append(gs)
    s.append("Command: 'queue roko' / 'queue chalu' / 'queue roz 6' (dohri pushti) / 'queue abhi' (aaj ka kaam abhi)")
    return "\n".join(s)


# ------------------------------------------------------------------ Telegram: command + dohri pushti
def on_text(tl):
    """bot.on_text se. Pehchana to sandesh bhejta hai aur True."""
    if tl in ("queue haal", "queue", "uk queue", "page queue", "uttarakhand queue", "queue status"):
        tg.say(status_text())
        return True
    if tl in ("queue roko", "queue band", "queue chalu", "queue shuru"):
        on = tl in ("queue chalu", "queue shuru")
        tg.say(f"Page queue {'CHALU' if on else 'BAND'} karein?", tg.inline([[("✅ Haan", f"pq:{'on' if on else 'off'}1"),
                                                                             ("❌ Nahi", "pq:x")]]))
        return True
    m = re.match(r"^queue roz (\d{1,2})$", tl)
    if m:
        n = int(m.group(1))
        if not 1 <= n <= NEW_PAGES_PER_DAY:
            tg.say(f"Roz 1 se {NEW_PAGES_PER_DAY} page tak hi (Google scaled-content niyam).")
            return True
        tg.say(f"Roz {n} page karein?", tg.inline([[("✅ Haan", f"pq:n{n}1"), ("❌ Nahi", "pq:x")]]))
        return True
    if tl in ("taazgi", "taazgi jaanch", "taza jaanch", "purana data", "fresh jaanch", "freshness"):
        threading.Thread(target=lambda: tg.say(fresh_run()), daemon=True).start()
        return True
    if tl in ("queue abhi", "queue aaj"):
        tg.say("Aaj ka queue kaam abhi chalayein? (audit ke baad hi kuch chadhega)",
               tg.inline([[("✅ Haan", "pq:now1"), ("❌ Nahi", "pq:x")]]))
        return True
    return False


def on_callback(rest, run):
    """bot.on_callback se ('pq:<rest>'). Pehli dabaan par dusri pushti; dusri par kaam."""
    if rest == "x":
        return tg.say("Theek hai, kuch nahi badla.")
    if rest.endswith("1"):
        act = rest[:-1]
        return tg.say("Pakka? (dohri pushti)", tg.inline([[("✅✅ Haan, pakka", f"pq:{act}2"), ("❌ Nahi", "pq:x")]]))
    if not rest.endswith("2"):
        return None
    act = rest[:-1]
    if act in ("on", "off"):
        state.put("pq_on", act == "on")
        return tg.say(f"✅ Page queue {'CHALU' if act == 'on' else 'BAND'}.")
    if act.startswith("n") and act[1:].isdigit():
        n = int(act[1:])
        if 1 <= n <= NEW_PAGES_PER_DAY:
            state.put("pq_per_day", n)
            return tg.say(f"✅ Ab roz {n} page.")
        return None
    if act == "now":
        return run(lambda: tg.say(run_day(force=False)))
    if act.startswith("load"):
        z = (state.get("pq_zip") or {})
        if not z or not os.path.exists(z.get("path", "")):
            return tg.say("Ye ZIP purani ho gayi - dobara bhejein.")
        state.put("pq_zip", {})

        def _go():
            msg = load_zip(z["path"])
            if msg.startswith("✅"):
                state.put("pq_on", True)
                if not state.get("pq_per_day"):
                    state.put("pq_per_day", DEFAULT_PER_DAY)
            tg.say(msg)
        return run(_go)
    return None


def offer_zip(ts, path, name, names):
    """updater.receive se: queue ZIP mili - owner se dohri pushti."""
    n = len([x for x in names if x.endswith(".html")])
    state.put("pq_zip", {"ts": ts, "path": str(path)})
    tg.say(f"🏔️ '{name}' page-queue ZIP hai ({n} page). Ise queue mein daalun? Website par roz {state.get('pq_per_day') or DEFAULT_PER_DAY} "
           f"page, har subah {START_HHMM} ke baad, audit pass hone par hi live honge. Abhi website par kuch nahi jayega.",
           tg.inline([[("✅ Haan, queue mein", "pq:load1"), ("❌ Nahi", "pq:x")]]))


# ------------------------------------------------------------------ v3.3.2: Google index ka haal + 'index doctor' (sirf PADHNA)
# VM par website repo ki scripts/daily.py roz subah Search Console URL Inspection se sitemap ke SAARE URL jaanchti hai
# (150/din: pehle kabhi-na-jaanche, phir jo index nahi, phir baaki) aur state/daily.json mein likhti hai.
# Bot Google se DOBARA nahi poochta (quota dohra nahi, do alag report nahi) - wahi nateeja padhta hai, aur jo page index mein
# nahi / index se nikal gaya, uski WEBSITE PAR wajah khud jaanchta hai (words, andar ke link, canonical, noindex, sitemap,
# milta-julta doosra page) aur owner ko saaf kaam batata hai. Content apne aap nahi likhta (Google spam policy).
GIDX_HHMM = "11:30"
SC_QUERY = "https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Asabhisaab.com/searchAnalytics/query"


def gidx_due(now=None):
    now = now or datetime.datetime.now(IST)
    return state.get("pq_gidx_day") != str(now.date()) and now.strftime("%H:%M") >= GIDX_HHMM


def _idx_status():
    """URL -> {'ok','why',...}: siteknow ke hi raaste (website repo state/daily.json, warna KEEP copy) - ek hi srot."""
    try:
        from . import siteknow
        return {(SITE + "/" + k) if k else SITE + "/": v for k, v in siteknow._index_status().items()}
    except Exception:
        return {}


def gidx_run():
    """Roz ek baar: daily.py ka nateeja padho (Google se dobara nahi poochna), index se NIKLE page yaad rakho (owner ki Request-indexing
    suchi mein upar), unki wajah siteknow.doctor se. daily.py sirf URL batati hai; ye sandesh wajah + kaam jodta hai."""
    today = str(_today())
    state.put("pq_gidx_day", today)
    st = _idx_status()
    if not st:
        return "Google index: daily.py ka nateeja abhi nahi mila (state/daily.json)"
    prev = state.get("pq_idx_prev") or {}
    drop = state.get("pq_idx_drop") or {}
    newly = []
    for u, v in st.items():
        ok = bool(v.get("ok"))
        if prev.get(u) is True and not ok:
            drop[u] = {"d": today, "why": v.get("why", "?")}
            newly.append(u)
        if ok and u in drop:
            drop.pop(u)
    state.put("pq_idx_prev", {u: bool(v.get("ok")) for u, v in st.items()})
    state.put("pq_idx_drop", drop)
    if newly:                                        # wajah: bot ka maujooda 'website doctor' (siteknow) - dohra jaanch-code nahi
        from . import siteknow
        lines = [f"🩺 Google index se NIKLE {len(newly)} page - website par wajah (website doctor):"]
        for u in newly[:8]:
            slug = u.replace(SITE + "/", "").strip("/")
            try:
                d = siteknow.doctor(slug_only=slug).split("\n", 1)[-1]
            except Exception:
                d = f"• /{slug} ({st[u].get('why', '?')})"
            lines.append(d[:500])
        lines.append("Kya karein: ye sandesh Claude ko bhejein - content/heading sudhaar wahi karega (bot apne aap content nahi likhta, "
                     "Google spam policy). Sudhaar live hone ke baad Search Console mein in URL par 'Request indexing' (bot roz ki "
                     "suchi mein bhi daalega). Bing ko bot khud bhejega.")
        tg.alert("yellow", "\n".join(lines))
    try:
        from . import website
        gsc_pages(website._gcreds("https://www.googleapis.com/auth/webmasters.readonly"))
    except Exception as e:
        log(f"gsc pages creds: {e}")
    return f"Google index: {sum(1 for v in st.values() if v.get('ok'))}/{len(st)} index, {len(newly)} naye nikle"


def gsc_pages(tk):
    """Pichhle 28 din: kaunse UK page Google search mein dikhe (impression/click). CTR kam wale = sirf sujhav."""
    try:
        man = {m["slug"] for m in manifest()}
        e = _today() - datetime.timedelta(days=2)
        j = requests.post(SC_QUERY, headers={"Authorization": f"Bearer {tk}"}, timeout=60,
                          json={"startDate": str(e - datetime.timedelta(days=27)), "endDate": str(e),
                                "dimensions": ["page"], "rowLimit": 5000}).json()
        rows = []
        for r in j.get("rows") or []:
            slug = r["keys"][0].replace(SITE + "/", "").replace("https://www.sabhisaab.com/", "").strip("/")
            if slug in man:
                rows.append((slug, int(r.get("impressions", 0)), int(r.get("clicks", 0))))
        rows.sort(key=lambda x: -x[1])
        low = [(s, i, c) for s, i, c in rows if i >= 1000 and c / i < 0.01]
        state.put("pq_gsc", {"t": str(_today()), "pages": len(rows), "imp": sum(i for _, i, _ in rows),
                             "clk": sum(c for _, _, c in rows), "top": rows[:5], "low_ctr": low[:5]})
    except Exception as ex:
        log(f"gsc pages: {ex}")


def gidx_summary(st=None):
    st = _idx_status() if st is None else st
    pub = state.get("pq_pub") or {}
    if not st:
        return ""
    chk = {s: st[f"{SITE}/{s}"] for s in pub if f"{SITE}/{s}" in st}
    ok = [s for s, x in chk.items() if x.get("ok")]
    notyet = [s for s, x in chk.items() if not x.get("ok")]
    lines = []
    if pub:
        lines.append(f"🔎 Google index (Uttarakhand): {len(ok)}/{len(pub)} live page index mein | Google ne jaanche {len(chk)}")
        if notyet:
            lines.append(f"   Abhi index nahi ({len(notyet)}): " + ", ".join(sorted(notyet)[:6]))
    allbad = [u for u, v in st.items() if not v.get("ok")]
    lines.append(f"🔎 Poori website: {len(st) - len(allbad)}/{len(st)} URL index mein")
    drop = state.get("pq_idx_drop") or {}
    if drop:
        lines.append(f"   Index se nikle (abhi tak wapas nahi) {len(drop)}: " + ", ".join(u.replace(SITE + '/', '') for u in list(drop)[:6]))
    if allbad:
        lines.append("   Har page ki wajah: '🩺 Website doctor'")
    g = state.get("pq_gsc") or {}
    if g:
        lines.append(f"📈 Google search (28 din): {g.get('pages', 0)} Uttarakhand page dikhe, {g.get('imp', 0)} baar dikhe, {g.get('clk', 0)} click")
        if g.get("top"):
            lines.append("   Sabse zyada: " + ", ".join(f"{s} ({i})" for s, i, _ in g["top"][:3]))
        if g.get("low_ctr"):
            lines.append("   Title sudhaar ke layak (1000+ baar dikhe, click 1% se kam - sirf sujhav, aapki haan ke bina kuch nahi badlega): "
                         + ", ".join(s for s, _, _ in g["low_ctr"][:3]))
    return "\n".join(lines)


def request_list(today_new, k=10, st=None):
    """Owner ka roz ka GSC 'Request indexing' kram: aaj ke naye page, phir jo Google index se NIKAL gaye, phir purane UK page
    jo Google ne jaanch kar abhi index nahi kiye (max 10 - Google ki roz ki seema ke andar)."""
    st = _idx_status() if st is None else st
    pub = state.get("pq_pub") or {}
    drop = [u.replace(SITE + "/", "") for u in (state.get("pq_idx_drop") or {})]
    old = [s for s in sorted(pub, key=lambda x: pub[x]) if s not in today_new
           and f"{SITE}/{s}" in st and not st[f"{SITE}/{s}"].get("ok")]
    out = list(today_new)[:k]
    for s in drop + old:
        if s not in out and len(out) < k:
            out.append(s)
    return out


# ---------------- v3.3.2 audit-6: taazgi ki chowkidari (owner 14 Nov: "bot sab page par nazar rakhe, purana data hone se Google
# index se na hataye") ----------------
# Bot content NAHI likhta (Google scaled-content/spam niyam) aur nakli lastmod NAHI badalta. Wo sirf har hafte live UK page padh kar
# pakadta hai ki kaunsi baat purani ho gayi: (1) beeti hui tareekh ke saath 'hoga/khulenge/shuru hoga' jaisa bhavishya-vaakya,
# (2) title/H1 mein pichhla saal, (3) samay-badalne wale page (yatra, sarkari, pariyojana, rasta) jinka 'Aakhri update' 150 din se
# purana. Suchi owner ko -> Claude sudhaar ZIP banata hai -> dateModified tabhi badalta hai jab content sach mein badla.
FRESH_DAY = 0          # Somvaar
FRESH_HHMM = "12:15"
_MON = {m.lower(): i + 1 for i, m in enumerate(MONTHS)}
_DATE_RX = re.compile(r"\b(\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December) (20\d\d)\b")
_FUT_RX = re.compile(r"\b(hoga|hogi|honge|khulenge|khulega|band honge|shuru hoga|shuru hogi|ghoshit hogi|aayojit hoga|lagega|"
                     r"ki ummeed|prastavit|aane wal[aie])\b", re.I)
_TS_RX = re.compile(r"-(ghumne-ki-jagah|kaise-pahunche|sarkari-seva|pariyojana-aapda-itihas|uttarakhand|basna-workation)$|"
                    r"^uttarakhand(-|$)|char-dham|kapat")


def fresh_scan(site_dir, today, slugs):
    """-> [(slug, wajah)]  (sirf padhta hai)"""
    out = []
    for s in slugs:
        f = os.path.join(site_dir, s + ".html")
        if not os.path.exists(f):
            continue
        h = open(f, encoding="utf-8", errors="ignore").read()
        body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))
        why = []
        for mm in _DATE_RX.finditer(txt):               # tareekh ke theek baad (60 akshar) bhavishya-kriya ho tabhi
            d, mo, y = mm.groups()
            after = txt[mm.end():mm.end() + 60]
            if not _FUT_RX.search(after) or re.search(r"[.|?!]", after[:after.find(_FUT_RX.search(after).group(0))]):
                continue
            try:
                dt = datetime.date(int(y), _MON[mo.lower()], int(d))
            except ValueError:
                continue
            if dt < today:
                why.append(f"beeti tareekh {d} {mo} {y} ke saath bhavishya ki baat: '{txt[max(0, mm.start() - 40):mm.end() + 50].strip()}'")
            if len(why) >= 3:
                break
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        for y in re.findall(r"\b(20\d\d)\b", (t.group(1) if t else "")):
            if int(y) < today.year and not re.search(r"kanoon|adhiniyam|act|niti|policy|sanshodhan", t.group(1), re.I):
                why.append(f"title mein purana saal {y}")
        m = re.search(r'"dateModified":\s*"(\d{4}-\d\d-\d\d)', h)
        if m and _TS_RX.search(s):
            age = (today - datetime.date.fromisoformat(m.group(1))).days
            if age > 150:
                why.append(f"samay ke saath badalne wala page, {age} din se update nahi (kiraya/tithi/niyam jaanchein)")
        if why:
            out.append((s, why))
    return out


def fresh_due(now=None):
    now = now or datetime.datetime.now(IST)
    wk = now.strftime("%G-W%V")
    return now.weekday() == FRESH_DAY and now.strftime("%H:%M") >= FRESH_HHMM and state.get("pq_fresh_wk") != wk


def fresh_run():
    now = datetime.datetime.now(IST)
    state.put("pq_fresh_wk", now.strftime("%G-W%V"))
    live = sorted(set(live_slugs()) | set((state.get("pq_pub") or {}).keys()))
    res = fresh_scan(str(_site_dir()), now.date(), live)
    state.put("pq_fresh", {s: w for s, w in res})
    if not res:
        return f"🧭 Taazgi jaanch: {len(live)} Uttarakhand page - sab taaza"
    lines = [f"🧭 Taazgi jaanch (hafta): {len(res)} page mein purani pad chuki baat - Google purane content ko neeche kar sakta hai:"]
    for s, w in res[:12]:
        lines.append(f"• /{s}: " + "; ".join(w[:2]))
    lines.append("Kya karein: ye sandesh Claude ko bhejein - wo taza sarkari srot se sahi karke website ZIP dega. Bot khud content "
                 "nahi badalta aur nakli 'update' tareekh nahi lagata (dono Google niyam ke khilaaf).")
    tg.alert("yellow", "\n".join(lines))
    return f"Taazgi: {len(res)} page"
