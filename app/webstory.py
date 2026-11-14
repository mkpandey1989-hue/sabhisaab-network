"""v2.9.1 (plan P1-4): GOOGLE WEB STORIES - har brand ki har hafte ek story (Google Search/Discover ke 'Web Stories' mein dikhti hai).

Kya: is hafte usi brand ke 5 JAANCHE HUE sawal (answers.answer_key) -> AMP story: cover, (sawal + vikalp, phir jawab + wajah) x5,
aakhri page 'saare jawab + free calculator' (sabhisaab.com/jawab). Poster (640x853) PIL se apna bana (koi copyright chitra nahi).
Niti: nakli aankda nahi, jawab kabhi galat nahi (pehle se jaancha), hafte mein brand ki ek hi (scaled content nahi), naya-page
seema (10/din) ke andar. /stories/* ka apna CSP (AMP script cdn.ampproject.org) - bot khud _headers mein jodta hai.
Sab website.apply_zip (audit gate) se. Fail = kuch live nahi, video schedule par koi asar nahi.
"""
import datetime
import html as H
import io
import re

from . import state
from .config import BRANDS, SITE
from .log import log

N_Q = 5
CSP_BLOCK = ("/stories/*\n  ! Content-Security-Policy\n  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' "
             "https://cdn.ampproject.org https://www.googletagmanager.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
             "font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: https:; connect-src 'self' https://cdn.ampproject.org "
             "https://www.google-analytics.com; frame-ancestors 'self'; base-uri 'self'; object-src 'none'\n")
COLORS = {"sunonatak": ("#3B0764", "#9333EA"), "money": ("#064E3B", "#10B981"), "deals": ("#7C2D12", "#F97316"),
          "pahadi": ("#0C4A6E", "#0EA5E9")}


def _e(x):
    return H.escape(str(x or ""), quote=True)


def items(brand, key=None, today=None):
    from .hubvideo import week_items
    out = [e for e in week_items(brand, today, key) if len(e.get("opts") or []) == 4 or e.get("ans")]
    return out[:N_Q]


def slug(brand, today=None):
    y, w, _ = (today or datetime.date.today()).isocalendar()
    return f"{brand}-quiz-{y}-w{w:02d}"


def title(brand, n):
    b = BRANDS[brand]["name"]
    return {"pahadi": f"उत्तराखंड GK: {n} सवाल - कितने सही?", "money": f"{n} गणित ट्रिक सवाल - कितने सही?",
            "deals": f"डिस्काउंट का असली हिसाब: {n} सवाल", "sunonatak": f"{n} दिमागी पहेलियाँ (जवाब के साथ)"}.get(brand, f"{b}: {n} सवाल")


def poster(brand, text_title):
    """640x853 JPEG poster (apna banaya)."""
    from PIL import Image, ImageDraw
    from . import text as T
    c1, c2 = COLORS.get(brand, ("#111827", "#6366F1"))
    w, h = 640, 853
    img = Image.new("RGB", (w, h), c1)
    d = ImageDraw.Draw(img)
    r1, g1, b1 = (int(c1[i:i + 2], 16) for i in (1, 3, 5))
    r2, g2, b2 = (int(c2[i:i + 2], 16) for i in (1, 3, 5))
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=(int(r1 + (r2 - r1) * t), int(g1 + (g2 - g1) * t), int(b1 + (b2 - b1) * t)))
    sz, lines = T.fit(text_title, w - 80, 420, start=58, smallest=34)
    y = (h - len(lines) * sz * 1.35) / 2 - 40
    for ln in lines:
        T.draw(d, ((w - T.width(ln, sz)) / 2, y), ln, sz, (255, 255, 255))
        y += int(sz * 1.35)
    T.draw(d, ((w - T.width("sabhisaab.com", 30)) / 2, h - 90), "sabhisaab.com", 30, (255, 255, 230))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return buf.getvalue()


def build(brand, key=None, today=None):
    """-> (html, poster_bytes, slug) ya None (sawal kam)."""
    its = items(brand, key, today)
    if len(its) < 4:
        return None
    sl = slug(brand, today)
    t = title(brand, len(its))
    c1, c2 = COLORS.get(brand, ("#111827", "#6366F1"))
    url = f"{SITE}/stories/{sl}"
    pages = [f'<amp-story-page id="cover"><amp-story-grid-layer template="fill"><div class="bg"></div></amp-story-grid-layer>'
             f'<amp-story-grid-layer template="vertical" class="c"><h1>{_e(t)}</h1><p class="sub">{_e(BRANDS[brand]["name"])} · '
             f'सोचिए, फिर अगले पेज पर जवाब</p></amp-story-grid-layer></amp-story-page>']
    for i, e in enumerate(its, 1):
        q = re.sub(r"#\S+", "", str(e.get("q", ""))).strip()
        opts = [str(o) for o in (e.get("opts") or [])][:4]
        ol = "".join(f"<li>{'ABCD'[k]}) {_e(o)}</li>" for k, o in enumerate(opts))
        pages.append(f'<amp-story-page id="q{i}"><amp-story-grid-layer template="fill"><div class="bg"></div></amp-story-grid-layer>'
                     f'<amp-story-grid-layer template="vertical" class="c"><p class="n">सवाल {i}</p><h2>{_e(q)}</h2>'
                     + (f"<ul>{ol}</ul>" if ol else "") + '<p class="sub">5 सेकंड सोचिए... अगले पेज पर जवाब</p>'
                     '</amp-story-grid-layer></amp-story-page>')
        aid = e.get("aid") or e.get("code")
        pages.append(f'<amp-story-page id="a{i}"><amp-story-grid-layer template="fill"><div class="bg2"></div></amp-story-grid-layer>'
                     f'<amp-story-grid-layer template="vertical" class="c"><p class="n">सवाल {i} का जवाब</p>'
                     f'<h2>✅ {_e(e.get("ans"))}</h2>' + (f'<p>{_e(str(e.get("exp", ""))[:180])}</p>' if e.get("exp") else "")
                     + f'</amp-story-grid-layer><amp-story-page-outlink layout="nodisplay"><a href="{SITE}/jawab#c{_e(aid)}">'
                     f'पूरी वजह देखें</a></amp-story-page-outlink></amp-story-page>')
    pages.append(f'<amp-story-page id="end"><amp-story-grid-layer template="fill"><div class="bg"></div></amp-story-grid-layer>'
                 f'<amp-story-grid-layer template="vertical" class="c"><h2>आपके कितने सही हुए?</h2><p>रोज़ नए सवाल, सारे जवाब और '
                 f'free calculator - sabhisaab.com पर</p></amp-story-grid-layer><amp-story-page-outlink layout="nodisplay">'
                 f'<a href="{SITE}/jawab">सारे जवाब देखें</a></amp-story-page-outlink></amp-story-page>')
    css = (f"amp-story{{font-family:'Noto Sans Devanagari','Mukta',sans-serif;color:#fff}}.bg{{background:linear-gradient(160deg,{c1},{c2});"
           f"width:100%;height:100%}}.bg2{{background:linear-gradient(160deg,#052e16,#16a34a);width:100%;height:100%}}"
           ".c{padding:28px;align-content:center;text-align:center}h1{font-size:34px;line-height:1.3}h2{font-size:28px;line-height:1.35}"
           "p{font-size:18px;line-height:1.5}.n{font-size:16px;opacity:.85;letter-spacing:.5px}.sub{font-size:15px;opacity:.9}"
           "ul{list-style:none;padding:0;margin:14px 0;text-align:left}li{background:rgba(0,0,0,.28);border-radius:12px;padding:10px 14px;"
           "margin:8px 0;font-size:19px}")
    html = ("<!doctype html>\n<html ⚡ lang=\"hi\">\n<head>\n<meta charset=\"utf-8\">\n<title>" + _e(t) + " | Sab Hisaab</title>\n"
            f'<link rel="canonical" href="{url}">\n<meta name="viewport" content="width=device-width">\n'
            f'<meta name="description" content="{_e(t)} - har sawal ka sahi jawab aur wajah, sabhisaab.com">\n'
            '<script async src="https://cdn.ampproject.org/v0.js"></script>\n'
            '<script async custom-element="amp-story" src="https://cdn.ampproject.org/v0/amp-story-1.0.js"></script>\n'
            '<style amp-boilerplate>body{-webkit-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-moz-animation:-amp-start 8s '
            'steps(1,end) 0s 1 normal both;-ms-animation:-amp-start 8s steps(1,end) 0s 1 normal both;animation:-amp-start 8s steps(1,end) '
            '0s 1 normal both}@-webkit-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@-moz-keyframes -amp-start{from'
            '{visibility:hidden}to{visibility:visible}}@-ms-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@-o-keyframes '
            '-amp-start{from{visibility:hidden}to{visibility:visible}}@keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}'
            '</style><noscript><style amp-boilerplate>body{-webkit-animation:none;-moz-animation:none;-ms-animation:none;animation:none}'
            '</style></noscript>\n'
            f"<style amp-custom>{css}</style>\n</head>\n<body>\n"
            f'<amp-story standalone title="{_e(t)}" publisher="Sab Hisaab" publisher-logo-src="{SITE}/icon-192.png" '
            f'poster-portrait-src="{SITE}/stories/{sl}.jpg">\n' + "\n".join(pages) + "\n</amp-story>\n</body>\n</html>\n")
    return html, poster(brand, t), sl


def headers_with_block(text):
    """site/_headers mein /stories/* ka apna CSP (pehle se ho to waisa hi). -> naya text ya None"""
    if "/stories/*" in text:
        return None
    return text.rstrip("\n") + "\n\n" + CSP_BLOCK


def sitemap_add(sm, url, day):
    if f"<loc>{url}</loc>" in sm or "</urlset>" not in sm:
        return None
    ent = f"  <url><loc>{url}</loc><lastmod>{day}</lastmod></url>\n"
    return sitemap_insert(sm, ent, url.split("sabhisaab.com/", 1)[-1])


def publish(brand):
    """Hafte mein ek baar per brand. -> owner ke liye ek line"""
    import zipfile
    from . import website
    from .config import DATA
    b = build(brand)
    if not b:
        return f"📖 {BRANDS[brand]['name']}: is hafte 4 se kam jaanche sawal - story nahi bani"
    html, jpg, sl = b
    try:
        website.sync()
    except Exception as e:
        log(f"webstory sync: {e}")
    site = website.DIR / "site"
    files = {f"site/stories/{sl}.html": html.encode("utf-8"), f"site/stories/{sl}.jpg": jpg}
    hdr = site / "_headers"
    if hdr.exists():
        nh = headers_with_block(hdr.read_text(encoding="utf-8"))
        if nh:
            files["site/_headers"] = nh.encode("utf-8")
    smf = site / "sitemap.xml"
    if smf.exists():
        sm = sitemap_add(smf.read_text(encoding="utf-8"), f"{SITE}/stories/{sl}", str(datetime.date.today()))
        if sm:
            files["site/sitemap.xml"] = sm.encode("utf-8")
    z = DATA / "story.zip"
    with zipfile.ZipFile(z, "w") as zz:
        for p, body in files.items():
            zz.writestr(p, body)
    r = website.apply_zip(z, force=False)
    z.unlink(missing_ok=True)
    if str(r).startswith("✅"):
        state.update("stories", lambda d: {**(d or {}), sl: str(datetime.date.today())}, {})
        try:                                           # v3.0.0: Bing/Yandex ko turant (IndexNow) - Google sitemap se
            website.indexnow([f"{SITE}/stories/{sl}"], "web story")
        except Exception as e:
            log(f"story indexnow: {e}")
        ok_, msg_ = live_check(f"{SITE}/stories/{sl}")
        return (f"📖 Web Story live: {SITE}/stories/{sl}\n(Bing ko turant bheja; Google sitemap se.)\n" + (msg_ if ok_ is not None else ""))
    return f"📖 Web Story audit mein ruki (kuch live nahi): {str(r)[:200]}"


def sitemap_insert(sm, ent, path):
    """v2.9.1: naya <url> sahi A-Z jagah par - sitemap ek-line ya kai-line dono format mein (pehle sirf ek-line pakadta tha)."""
    for m in re.finditer(r"<loc>" + re.escape(SITE) + r"/([^<]+)</loc>", sm):
        if m.group(1) > path:
            u = sm.rfind("<url>", 0, m.start())
            ls = sm.rfind("\n", 0, u) + 1
            return sm[:ls] + ent + sm[ls:]
    return sm.replace("</urlset>", ent + "</urlset>", 1)



def live_check(url):
    """v3.0.1 (GSC: 'Web Story is invalid - mandatory attribute missing'): Cloudflare ZARAZ har page ke <head> mein apni <script>
    daal deta hai - AMP mein aisi script mana hai. Live story padh kar AMP ke bahar ki script dhoondo. -> (ok, sandesh)"""
    import requests
    try:
        h = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 SabhisaabBot-AMPcheck"}).text
    except Exception as e:
        return None, f"jaanch nahi ho payi: {str(e)[:80]}"
    bad = []
    for m in re.finditer(r"<script\b([^>]*)>", h, re.I):
        attrs = m.group(1)
        if "cdn.ampproject.org" in attrs or "application/ld+json" in attrs:
            continue
        bad.append("zaraz (Cloudflare)" if "cfasync" in attrs or "zaraz" in h[m.end():m.end() + 300] else attrs.strip()[:60])
    if not bad:
        return True, "✅ Story mein koi bahari script nahi (AMP saaf)"
    return False, ("❌ Web Story mein Cloudflare ki bahari script ghus rahi hai: " + ", ".join(dict.fromkeys(bad)) + "\n"
                   "Theek karne ka tareeka (ek baar): dash.cloudflare.com → sabhisaab.com → baayein 'Zaraz' → Zaraz band (Disable) "
                   "- ye khaali hai, koi tool nahi chala raha. Phir bot mein 'amp jaanch'; ✅ aaye to GSC mein story URL → 'Request indexing'.")
