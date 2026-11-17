"""v3.3.5 (owner 15 Nov: 'audience tezi se badhe, future mein link badle ya janganana/aankde badle to bot khud update kare,
website fully updated rahe'): Uttarakhand pages ke liye teen chowkidar.

1) share_run  - roz 18:45 IST: pichhle 7 din mein live hua EK UK page (jo abhi share nahi hua) Pahadi Hisaab ke FB page (link
   post), Threads (link card) aur Telegram channel (page ki apni photo) par. Text = page ka apna title + meta description (koi
   naya likha nahi, AI nahi). Din mein ek hi - spam nahi. 'uk share band' / 'uk share chalu'.
2) link_run   - Ravivaar 11:45: live UK pages ke BAHARI link (sarkari portal, srot) jaanche. Pakka redirect (301/308) = naya
   pata apne aap (wahi cheez, naya address). 404/410 do hafte lagaatar = link hata kar sirf text (shabd nahi badalte) + owner ko
   suchi. Bahari site ka timeout/403 = kuch nahi (bahut sarkari site bot ko rokti hain). Sab website.apply_zip (audit) se.
3) src_run    - Ravivaar 12:05: sarkari srot (Census, BKTC kapat, zila portal) ke page ka 'nishaan' (hash). Badla = owner ko
   alert: kaun sa srot badla aur kin pages par asar. Tathya bot KHUD NAHI likhta (Google ki scaled/auto content niti + owner
   ka niyam: bot content auto-write nahi karta) - Claude/owner pushti karke naya queue ZIP banate hain; bot wo ZIP aane par
   live page apne aap naye roop mein badal deta hai (v3.3.4 ukc). Saal ke tay mauke (Basant Panchami = Badrinath kapat
   tithi, Mahashivratri = Kedarnath, Vijayadashami = band hone ki tithi) par yaad dilana bhi.
"""
import datetime
import hashlib
import html as H
import json
import re
import zipfile

from . import state, tg
from .config import IST, SITE
from .log import log

SHARE_HHMM = "18:45"
LINK_DAY, LINK_HHMM = 6, "11:45"           # Ravivaar
SRC_DAY, SRC_HHMM = 6, "12:05"
UA = {"User-Agent": "Mozilla/5.0 (compatible; SabhisaabLinkCheck/1.0; +https://sabhisaab.com/)"}

# Sarkari/pakke srot jinke badalne par UK pages ke tathya badal sakte hain (srot -> kis tarah ke pages)
SOURCES = {
    "census": ("https://censusindia.gov.in/", "Census (aabadi, sex ratio, saksharta) - sab 13 zila page + hub"),
    "bktc": ("https://badrinath-kedarnath.gov.in/", "Badrinath-Kedarnath kapat tithi - Chamoli, Rudraprayag, Char Dham page"),
    "uk_gov": ("https://uk.gov.in/", "Rajya portal (zile, yojana) - hub + sarkari seva pages"),
    "eci_uk": ("https://ceo.uk.gov.in/", "Vidhan Sabha / chunav - zila prashasan pages"),
    "transport": ("https://transport.uk.gov.in/", "RTO code / transport - zila prashasan pages"),
}
# Saal ke tay mauke (mahina, din-shuru, din-ant, sandesh) - tithi panchang se badalti hai, isliye poora hafta-khidki
SEASON = [
    (1, 20, 31, "Basant Panchami ke aas-paas Badrinath ke kapat khulne ki tithi ghoshit hoti hai - Chamoli / Char Dham page ki "
                "tithi naye saal ki karni hogi (Claude ko bolein: 'kapat tithi update')."),
    (2, 10, 28, "Mahashivratri par Kedarnath kapat khulne ki tithi Ukhimath mein ghoshit hoti hai - Rudraprayag / Char Dham page."),
    (10, 1, 25, "Vijayadashami par kapat band hone ki tithiyan ghoshit hoti hain - Char Dham pages ki 'band' tithi naye saal ki."),
]


def _site():
    from . import website
    return website.DIR / "site"


def _uk_live(site=None):
    from . import pagequeue as PQ
    site = site or _site()
    man = {m["slug"] for m in PQ.manifest()}
    return [s for s in sorted(man) if (site / f"{s}.html").exists()]


# ------------------------------------------------------------------ 1) roz ek UK page social par
def page_card(html_text):
    """-> (title, desc, photo) page ke APNE shabd (title tag ka pehla hissa + meta description), photo = og:image (apni)."""
    t = re.search(r"<title>(.*?)</title>", html_text, re.S)
    d = re.search(r'<meta name="description" content="([^"]*)"', html_text)
    o = re.search(r'<meta property="og:image" content="([^"]+)"', html_text)
    title = H.unescape(t.group(1)).split(" | ")[0].strip() if t else ""
    return title, H.unescape(d.group(1)).strip() if d else "", (o.group(1) if o else "")


def share_pick(today, pub, shared, site_has):
    """Pichhle 7 din mein live, abhi share nahi hua, sabse purana pehle. -> slug ya None"""
    cand = []
    for s, d in (pub or {}).items():
        try:
            age = (today - datetime.date.fromisoformat(d)).days
        except Exception:
            continue
        if 0 <= age <= 7 and s not in shared and site_has(s):
            cand.append((d, s))
    return sorted(cand)[0][1] if cand else None


def share_due(now=None):
    now = now or datetime.datetime.now(IST)
    return (now.strftime("%H:%M") >= SHARE_HHMM and state.get("uk_share_day") != str(now.date())
            and state.get("uk_share_on", True))


def share_run():
    from . import meta as M
    now = datetime.datetime.now(IST)
    today = now.date()
    state.put("uk_share_day", str(today))
    site = _site()
    shared = state.get("uk_shared", {}) or {}
    s = share_pick(today, state.get("pq_pub") or {}, shared, lambda x: (site / f"{x}.html").exists())
    if not s:
        return None
    title, desc, photo = page_card((site / f"{s}.html").read_text(encoding="utf-8", errors="ignore"))
    if not title:
        return None
    url = f"{SITE}/{s}"
    txt = f"{title}\n\n{desc}".strip()
    out = []
    try:
        bi = M.brand_info("pahadi")
        if bi:
            link = f"{url}?utm_source=facebook&utm_medium=social&utm_campaign=uk_page"
            M._post(f"/{bi['page_id']}/feed", bi["page_token"], message=f"{txt}\n\n👉 {link}", link=link)
            out.append("FB")
    except Exception as e:
        out.append(f"FB nahi ({str(e)[:40]})")
    try:
        from . import threads as TH
        if TH.info("pahadi"):
            TH.post_text("pahadi", txt[:450], f"{url}?utm_source=threads&utm_medium=social&utm_campaign=uk_page")
            out.append("Threads")
    except Exception as e:
        out.append(f"Threads nahi ({str(e)[:40]})")
    try:
        from .config import TG_CHANNEL
        cap = f"{txt}\n\n🌐 {url}?utm_source=telegram&utm_medium=channel&utm_campaign=uk_page"[:1000]
        img = site / photo.rsplit("/", 1)[-1] if photo.startswith(SITE) else None
        if img and img.exists() and img.suffix in (".webp", ".jpg", ".png"):
            from PIL import Image
            import io
            buf = io.BytesIO()
            Image.open(img).convert("RGB").save(buf, "JPEG", quality=88)
            tg.call("sendPhoto", {"chat_id": TG_CHANNEL, "caption": cap}, {"photo": ("p.jpg", buf.getvalue(), "image/jpeg")})
        else:
            tg.call("sendMessage", {"chat_id": TG_CHANNEL, "text": cap})
        out.append("Telegram")
    except Exception as e:
        out.append(f"Telegram nahi ({str(e)[:40]})")
    shared[s] = str(today)
    state.put("uk_shared", shared)
    log(f"uk share {s}: {out}")
    return f"📣 Aaj ka Uttarakhand page share: {url} → " + ", ".join(out)


# ------------------------------------------------------------------ 2) bahari link chowkidar
EXT_RX = re.compile(r'<a href="(https?://[^"#]+)"([^>]*)>(.*?)</a>', re.S)


def ext_links(html_text):
    return sorted({u for u, _, _ in EXT_RX.findall(html_text) if "sabhisaab.com" not in u})


def check_url(url, get=None):
    """-> ('ok'|'moved'|'gone'|'unknown', naya_url)"""
    import requests
    get = get or (lambda u: requests.get(u, headers=UA, timeout=20, allow_redirects=False))
    try:
        r = get(url)
    except Exception:
        return "unknown", None
    if r.status_code in (301, 308):
        loc = r.headers.get("Location", "")
        if loc.startswith("/"):
            m = re.match(r"(https?://[^/]+)", url)
            loc = (m.group(1) if m else "") + loc
        if loc.startswith("https://") and loc != url:
            try:                                          # naya pata khud khulta ho tabhi badlo
                r2 = get(loc)
                if r2.status_code == 200:
                    return "moved", loc
            except Exception:
                pass
        return "unknown", None
    if r.status_code in (404, 410):
        return "gone", None
    if r.status_code == 200:
        return "ok", None
    return "unknown", None


def relink(html_text, moved, gone):
    """moved {old: new} -> href badlo; gone set -> <a> hata kar sirf andar ka text. -> (html, n)"""
    n = 0

    def f(m):
        nonlocal n
        u, attrs, inner = m.group(1), m.group(2), m.group(3)
        if u in moved:
            n += 1
            return f'<a href="{moved[u]}"{attrs}>{inner}</a>'
        if u in gone:
            n += 1
            return inner
        return m.group(0)
    return EXT_RX.sub(f, html_text), n


def link_due(now=None):
    now = now or datetime.datetime.now(IST)
    return now.weekday() == LINK_DAY and now.strftime("%H:%M") >= LINK_HHMM and \
        state.get("uk_link_wk") != now.strftime("%G-W%V")


def link_run(get=None, apply=None):
    from . import website
    now = datetime.datetime.now(IST)
    state.put("uk_link_wk", now.strftime("%G-W%V"))
    try:
        website.sync()
    except Exception as e:
        log(f"uk link sync: {e}")
    site = _site()
    pages = {s: (site / f"{s}.html").read_text(encoding="utf-8", errors="ignore") for s in _uk_live(site)}
    urls = sorted({u for h in pages.values() for u in ext_links(h)})[:400]
    strikes = state.get("uk_link_gone", {}) or {}
    moved, gone, new_strikes = {}, set(), {}
    for u in urls:
        st, nu = check_url(u, get)
        if st == "moved":
            moved[u] = nu
        elif st == "gone":
            new_strikes[u] = strikes.get(u, 0) + 1
            if new_strikes[u] >= 2:                       # do hafte lagaatar - ek baar ki gadbad par nahi
                gone.add(u)
    state.put("uk_link_gone", {u: k for u, k in new_strikes.items() if u not in gone})
    files = {}
    for s, h in pages.items():
        nh, k = relink(h, moved, gone)
        if k:
            files[f"site/{s}.html"] = nh
    if not files:
        return f"🔗 UK bahari link: {len(urls)} jaanche, sab theek (ya bahari site ne jawab nahi diya - kuch nahi badla)." \
            + (f" {len(new_strikes)} link pehli baar 404 - agle hafte phir jaanch." if new_strikes else "")
    from .config import DATA
    z = DATA / "uklinks.zip"
    with zipfile.ZipFile(z, "w") as zz:
        for p, body in files.items():
            zz.writestr(p, body.encode("utf-8"))
    r = (apply or website.apply_zip)(z, force=False)
    z.unlink(missing_ok=True)
    lines = [f"🔗 UK bahari link: {len(urls)} jaanche, {len(moved)} naye pate par, {len(gone)} band link hataye (shabd wahi) "
             f"- {len(files)} page. {str(r)[:120]}"]
    lines += [f"• {u} → {v}" for u, v in list(moved.items())[:8]] + [f"• hata: {u}" for u in list(gone)[:8]]
    return "\n".join(lines)


# ------------------------------------------------------------------ 3) sarkari srot chowkidar (badla = owner ko)
def _textsig(html_text):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_text or "", flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?\b|\b\d{1,2}[-/ ]\w{3,9}[-/ ]\d{4}\b", " ", t)   # ghadi/aaj ki tareekh nahi gino
    return hashlib.sha1(re.sub(r"\s+", " ", t).strip().encode("utf-8")).hexdigest()[:16]


def src_due(now=None):
    now = now or datetime.datetime.now(IST)
    return now.weekday() == SRC_DAY and now.strftime("%H:%M") >= SRC_HHMM and \
        state.get("uk_src_wk") != now.strftime("%G-W%V")


def season_note(day):
    for mo, d1, d2, msg in SEASON:
        if day.month == mo and d1 <= day.day <= d2:
            return msg
    return None


def src_run(get=None):
    import requests
    get = get or (lambda u: requests.get(u, headers=UA, timeout=30))
    now = datetime.datetime.now(IST)
    state.put("uk_src_wk", now.strftime("%G-W%V"))
    old = state.get("uk_src_sig", {}) or {}
    new, changed = dict(old), []
    for k, (u, what) in SOURCES.items():
        try:
            r = get(u)
            if r.status_code != 200:
                continue
            sig = _textsig(r.text)
        except Exception:
            continue
        if k in old and old[k] != sig:
            changed.append((k, u, what))
        new[k] = sig
    state.put("uk_src_sig", new)
    lines = []
    if changed:
        lines.append("🏛 Sarkari srot badla (UK pages ke tathya jaanchne layak):")
        lines += [f"• {u} - {what}" for _, u, what in changed]
        lines.append("Bot tathya khud nahi likhta (Google niti). Claude ko bolein: 'UK srot badla, pages update karo' - "
                     "naya queue ZIP aate hi live page apne aap badal jayenge.")
    sn = season_note(now.date())
    if sn:
        lines.append("📅 " + sn)
    if lines:
        from . import tasks
        try:
            tasks.add(f"[Developer] {lines[1] if changed else lines[-1]}"[:300], "app/ukwatch.py src_run")
        except Exception:
            pass
        return "\n".join(lines)
    return None


def status_text():
    sh = state.get("uk_shared", {}) or {}
    return (f"📣 UK share: {'CHALU' if state.get('uk_share_on', True) else 'BAND'} | ab tak {len(sh)} page share\n"
            f"🔗 Bahari link: Ravivaar 11:45 | 🏛 Sarkari srot: Ravivaar 12:05 ({len(state.get('uk_src_sig', {}) or {})} srot par nazar)")
