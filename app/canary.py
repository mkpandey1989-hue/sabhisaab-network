"""v2.5.2: deploy ke baad 'sach mein live hai?' jaanch (audit ka Section 8). Sirf padhta hai (GET) - koi badlaav/post nahi.
Soft-404 pakadta hai (galat URL par 404 aana chahiye), /jawab ka asli text, sitemap, ek h1, aur AdSense ke baad:
privacy/terms/contact/disclaimer par ad code nahi. Bot deploy ke baad apne aap chalata hai; 'canary' likhne par haath se bhi."""
import time

import requests

from .config import SITE
from .log import log

KEY_PAGES = (("/", ""), ("/jawab", "आज के सवालों के सही जवाब"), ("/privacy", ""), ("/terms", ""), ("/contact", ""))
NO_AD_PAGES = ("/privacy", "/terms", "/contact", "/disclaimer", "/thanks")
NOT_FOUND_MARK = "Page nahi mila"


def _get(path, bust=True):
    u = f"{SITE}{path}" + (f"?_={int(time.time())}" if bust else "")
    return requests.get(u, timeout=25, allow_redirects=True, headers={"Cache-Control": "no-cache", "User-Agent": "SabhisaabBot-Canary/1.0"})


def evaluate(path, status, body, marker=""):
    """Alag function taaki bina network test ho. -> (ok, kaaran)"""
    if status != 200:
        return False, f"HTTP {status}"
    if NOT_FOUND_MARK in (body or ""):
        return False, "200 par 'Page nahi mila' (soft-404)"
    if marker and marker not in (body or ""):
        return False, f"asli text nahi mila ({marker[:20]})"
    if path == "/jawab" and (body or "").count("<h1") != 1:
        return False, f"h1 ginti {(body or '').count('<h1')} (1 chahiye)"
    return True, ""


def ads_on_forbidden(path, body):
    """AdSense policy: publisher content ke bina / zaroori pages par ad code nahi."""
    return path in NO_AD_PAGES and "adsbygoogle" in (body or "")


def run():
    """-> (sab_theek, report_text)"""
    rows, bad = [], 0
    for path, mark in KEY_PAGES:
        try:
            r = _get(path)
            ok, why = evaluate(path, r.status_code, r.text, mark)
            if ads_on_forbidden(path, r.text):
                ok, why = False, "is page par AdSense code nahi hona chahiye"
        except Exception as e:
            ok, why = False, str(e)[:80]
        bad += (not ok)
        rows.append(f"{'✅' if ok else '❌'} {path}" + (f" - {why}" if why else ""))
    try:                                                    # galat URL par sachchi 404
        r = _get("/ye-page-nahi-hai-9z")
        ok = r.status_code == 404
    except Exception:
        ok = False
    bad += (not ok)
    rows.append(f"{'✅' if ok else '❌'} soft-404 jaanch (galat URL par 404)")
    try:
        sm = _get("/sitemap.xml", bust=False).text
        ok = f"{SITE}/jawab" in sm
    except Exception:
        ok = False
    bad += (not ok)
    rows.append(f"{'✅' if ok else '❌'} sitemap mein /jawab")
    return bad == 0, "🐤 CANARY (deploy ke baad jaanch)\n" + "\n".join(rows)


def after_deploy():
    """deploy_direct ke baad: sirf ❌ ho to Telegram alert. Kabhi exception nahi uthata (deploy ko nahi rokta)."""
    try:
        time.sleep(20)                                      # edge cache ko thoda samay
        ok, rep = run()
        if not ok:
            from . import tg
            tg.alert("yellow", rep)
        return "canary ✅" if ok else "canary ❌ (Telegram par)"
    except Exception as e:
        log(f"canary: {e}")
        return ""


def ping():
    """Halka uptime: / aur /jawab. -> list of problems (khaali = theek). 5xx / timeout / soft-404."""
    bad = []
    for path, mark in (("/", ""), ("/jawab", "आज के सवालों के सही जवाब")):
        try:
            r = _get(path)
            ok, why = evaluate(path, r.status_code, r.text, mark)
            if not ok:
                bad.append(f"{path}: {why}")
        except Exception as e:
            bad.append(f"{path}: {str(e)[:60]}")
    return bad


def uptime_tick():
    """Har ~10 min. Lagaataar 2 baar kharab par EK alert; theek hone par EK 'wapas theek' (spam nahi)."""
    from . import state, tg
    now = time.time()
    if now - state.get("up_at", 0) < 600:
        return
    state.put("up_at", now)
    bad = ping()
    fails = state.get("up_fails", 0)
    if bad:
        fails += 1
        state.put("up_fails", fails)
        if fails == 2 and not state.get("up_alerted"):
            state.put("up_alerted", True)
            tg.alert("yellow", "🌐 Website dikkat (2 baar lagaataar):\n" + "\n".join(bad))
    else:
        if state.get("up_alerted"):
            tg.say("✅ Website wapas theek (uptime jaanch).")
        state.put("up_fails", 0)
        state.put("up_alerted", False)
