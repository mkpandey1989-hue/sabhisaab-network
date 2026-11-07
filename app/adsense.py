"""v2.5.2: AdSense taiyari - jaanch (sirf padhna) + ads.txt (owner ki dohri pushti ke baad). KABHI: khud ad click, 'click karo' kehna,
auto-refresh, ads ko button/navigation jaisa dikhana, zaroori pages par ad. Ye module ad code website par NAHI lagata - sirf
taiyari jaanchta hai aur approval ke baad ads.txt likhta hai."""
import re

import requests

from . import state
from .config import SITE
from .log import log

PUB_RX = re.compile(r"^pub-\d{16}$")
GOOGLE_TAG = "f08c47fec0942fa0"           # Google ka standard certification-authority ID (ads.txt ki line ka aakhri hissa)
MUST_PAGES = ("/about", "/contact", "/privacy", "/terms", "/disclaimer", "/author")


def ads_txt(pub):
    if not PUB_RX.match(pub or ""):
        raise ValueError("publisher ID 'pub-' + 16 ank hona chahiye (AdSense → Account → Settings → Account information)")
    return f"google.com, {pub}, DIRECT, {GOOGLE_TAG}\n"


def _get(path):
    return requests.get(SITE + path, timeout=25, allow_redirects=True, headers={"User-Agent": "SabhisaabBot-AdsenseCheck/1.0"})


def status():
    """Taiyari ki jaanch. -> text. Sirf GET."""
    rows = []
    for p in MUST_PAGES:
        try:
            r = _get(p)
            rows.append(f"{'✅' if r.status_code == 200 and 'Page nahi mila' not in r.text else '❌'} {p} ({r.status_code})")
        except Exception as e:
            rows.append(f"❌ {p}: {str(e)[:60]}")
    try:
        r = _get("/ads.txt")
        pub = state.get("adsense_pub") or ""
        has = r.status_code == 200 and "google.com" in r.text and (not pub or pub in r.text)
        rows.append(("✅" if has else "⏳") + " ads.txt " + ("maujood" if has else "abhi nahi (approval ke BAAD 'adsense id pub-...' likhein)"))
    except Exception:
        rows.append("⏳ ads.txt jaanch nahi ho payi")
    try:
        r = _get("/robots.txt")
        blocked = bool(re.search(r"user-agent:\s*mediapartners-google[^\n]*\n\s*disallow:\s*/\s*$", r.text, re.I | re.M))
        rows.append(("❌ robots.txt Mediapartners-Google ko rok raha" if blocked else "✅ robots.txt AdSense bot ko nahi rokta"))
    except Exception:
        rows.append("⏳ robots.txt jaanch nahi ho payi")
    try:
        r = _get("/privacy")
        t = r.text
        rows.append(("⚠️ privacy mein ab bhi 'koi vigyapan nahi' type line - ads shuru hote hi badlein" if re.search(r"koi vigyapan nahi", t, re.I)
                     else "✅ privacy mein 'ads nahi' wali line nahi mili") + (" | AdSense/DoubleClick section: " +
                     ("✅" if re.search(r"adsense|doubleclick|dart", t, re.I) else "❌")))
    except Exception:
        pass
    try:
        r = _get("/")
        rows.append(("⚠️ homepage par adsbygoogle pehle se hai (approval se pehle nahi hona chahiye)" if "adsbygoogle" in r.text
                     else "✅ ad code abhi kisi page par nahi (sahi - approval se pehle)"))
    except Exception:
        pass
    todo = ["1) Apply se pehle 20-30 sabse accha page chunkar content-review (kamzor tool pages par misaal/FAQ badhao ya noindex)",
            "2) AdSense → Privacy & messaging → Certified CMP chalu (EU/UK visitors; India ke liye zaroori nahi)",
            "3) Approval ke baad: 'adsense id pub-XXXXXXXXXXXXXXXX' (ads.txt) → privacy text update → ad slot sirf tool/guide/lekh/jawab par",
            "4) Ad slot: min-height reserve (layout shift nahi), tool ke button ke paas nahi, privacy/terms/contact/disclaimer par bilkul nahi",
            "5) Kabhi nahi: khud click, 'ad par click karo', auto-refresh, ad ko navigation jaisa dikhana"]
    return "💰 ADSENSE TAIYARI (live jaanch)\n" + "\n".join(rows) + "\n\nBaaki kaam:\n" + "\n".join(todo)


def write_ads_txt(pub):
    """Dohri pushti ke baad: site/ads.txt -> website.apply_zip (audit gate, force=False). -> result text"""
    import zipfile
    from . import website
    from .config import DATA
    body = ads_txt(pub)
    z = DATA / "adsense.zip"
    with zipfile.ZipFile(z, "w") as zz:
        zz.writestr("site/ads.txt", body)
    try:
        r = website.apply_zip(z, force=False)
    finally:
        z.unlink(missing_ok=True)
    if str(r).startswith("✅"):
        state.put("adsense_pub", pub)
    else:
        log(f"ads.txt: {str(r)[:200]}")
    return str(r)
