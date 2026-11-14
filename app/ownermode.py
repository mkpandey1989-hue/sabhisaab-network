"""v3.1.2 (owner, 12 Nov 2026): "jab main khud website kholta hoon to meri visit Analytics mein na gini jaaye - mobile aur laptop
dono, hotspot hai, IP badalta rehta hai."

IP se rokna mumkin nahi (IP badalta hai). Isliye BROWSER se: owner apne har browser mein EK BAAR ye link kholta hai:
    https://sabhisaab.com/#owner-on          (band karna ho: https://sabhisaab.com/#owner-off)
Us browser ke localStorage mein 'sh_owner' = 1 ban jaata hai aur har page ka chhota code Google Analytics ko us browser se
poori tarah band rakhta hai (Google ka apna official tareeka: window['ga-disable-<ID>'] = true). Neeche kone mein chhoti patti
"Owner mode" dikhti hai taaki pata rahe ki chalu hai. '#' wala hissa server/Google tak jaata hi nahi - koi naya URL nahi banta.
Incognito tab ya browser ka data saaf karne par dobara link kholna hoga.

Ye module wahi ek line website ke HAR page (aur about.html saanche, jisse /jawab banta hai) mein jodta hai - VM ki ABHI ki
file par (GitHub ki purani copy par nahi), audit gate se, ek baar. Dobara chalane par kuch nahi badalta (idempotent).
Google Search Console par iska asar nahi: GSC visit nahi ginta, sirf Google search mein dikhna/click ginta hai.
"""
import re
import tempfile
import zipfile
from pathlib import Path

from . import state
from .log import log

GA_ID = "G-QX5MWV42TR"
ANCHOR = "window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}\n"
LINE = ("try{var _h=location.hash;if(_h==='#owner-on'){localStorage.setItem('sh_owner','1');}else if(_h==='#owner-off')"
        "{localStorage.removeItem('sh_owner');}if(localStorage.getItem('sh_owner')==='1'){window['ga-disable-" + GA_ID + "']=true;"
        "document.addEventListener('DOMContentLoaded',function(){var d=document.createElement('div');"
        "d.textContent='Owner mode: ye visit Analytics me nahi gini jaati';"
        "d.style.cssText='position:fixed;left:8px;bottom:8px;z-index:99999;background:#111;color:#fff;font:12px sans-serif;"
        "padding:6px 10px;border-radius:8px;opacity:.85';document.body.appendChild(d);});}}catch(e){}\n")
MARK = "localStorage.getItem('sh_owner')"
ON_URL = "https://sabhisaab.com/#owner-on"
OFF_URL = "https://sabhisaab.com/#owner-off"


def patch_html(html):
    """-> (naya_html, badla?) Sirf wahi page jisme Analytics ka consent-code hai aur 'sh_owner' pehle se nahi."""
    if not isinstance(html, str) or MARK in html or ANCHOR not in html:      # MARK code ka tukda hai - privacy page ke text mein 'sh_owner' shabd hai
        return html, False
    return html.replace(ANCHOR, ANCHOR + LINE, 1), True


def patch_dir(site_dir):
    """site/*.html (sirf upar ke star ke page; AMP stories nahi) -> {relative_path: naya_html} jo badle."""
    out = {}
    for f in sorted(Path(site_dir).glob("*.html")):
        try:
            new, ch = patch_html(f.read_text(encoding="utf-8"))
        except Exception as e:
            log(f"ownermode {f.name}: {e}")
            continue
        if ch:
            out["site/" + f.name] = new
    return out


def apply():
    """VM ki website-repo par ek baar. website._apply_zip (audit gate + commit + deploy) se hi - fail to kuch live nahi. -> sandesh/None"""
    from . import website
    if not website.DIR.exists():
        return None
    with website.ZIP_LOCK:                     # owner ki ZIP ke saath takraav nahi; file bhi taale ke andar hi padhi jaati hain
        changed = patch_dir(website.DIR / "site")
        if not changed:
            state.put("ownermode_v312", 1)
            return None
        with tempfile.TemporaryDirectory() as td:
            zp = Path(td) / "ownermode.zip"
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
                for rel, txt in changed.items():
                    z.writestr(rel, txt)
            r = website._apply_zip(str(zp))
    if str(r).startswith("✅") or "pehle se lagi" in str(r):
        state.put("ownermode_v312", 1)
        return ("👤 OWNER MODE taiyaar (website ke " + str(len(changed)) + " page par chhota code laga, audit paas).\n"
                "Ab apne HAR browser mein EK BAAR ye link kholein (phone ka Chrome + laptop ka Chrome):\n" + ON_URL + "\n"
                "Neeche kone mein 'Owner mode' ki kaali patti dikhe = us browser ki visit Analytics mein nahi ginegi (IP badle to bhi).\n"
                "Band: " + OFF_URL + "  |  Incognito ya data saaf karne par dobara kholna hoga.  |  Haal: 'owner mode'")
    log(f"ownermode apply: {str(r)[:200]}")
    return "⚠️ Owner mode ka code website par nahi lag paya (audit/commit): " + str(r)[:300] + "\nKal bot dobara koshish karega."


def status():
    done = bool(state.get("ownermode_v312"))
    return ("👤 OWNER MODE (aapki apni visit Analytics mein na gini jaaye)\n"
            + ("✅ Website par code laga hua hai.\n" if done else "⏳ Code abhi website par lag raha hai (install ke kuch minute baad).\n")
            + "Chalu karna: har browser mein EK BAAR kholein → " + ON_URL + "\n"
            "Pehchaan: neeche-baayein kaali patti 'Owner mode: ye visit Analytics me nahi gini jaati'.\n"
            "Band karna: " + OFF_URL + "\n"
            "Dhyan: (1) phone aur laptop dono par alag-alag kholna hai, har browser mein. (2) Incognito tab mein ya browser ka data saaf "
            "karne ke baad dobara. (3) Search Console par asar nahi - wo visit nahi ginta, sirf Google search mein dikhna aur click; "
            "isliye Google par khud apni site khoj kar baar-baar click na karein.")
