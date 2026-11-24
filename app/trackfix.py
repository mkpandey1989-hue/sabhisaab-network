"""v3.4.1 (16 Nov 2026 raat) - owner: "(not set) kahan se aaye, itni baar bola theek nahi hua" + "meri khud ki ginti kabhi na aaye".

ASLI WAJAH (jaancha, 296 page):
1) Har page par Consent Mode v2 'analytics_storage: denied' SAB deshon ke liye default tha. Visitor ne cookie banner par
   'Sab cookies theek hain' der se dabaya (ya agle page par) to Google ko session ki shuruaat (session_start, jisme source hota hai)
   nahi milti -> GA4 mein source '(not set)'. Aur jo banner dabate hi nahi (zyada log, khaaskar Telegram/Instagram ke andar wale
   browser mein) wo report mein gine hi nahi jaate -> asli se kam log dikhte the.
   ILAAJ (Google ka apna 'region' tareeka): Europe/UK/Switzerland (EEA - jahan kanoon/Google ki EU consent policy lagti hai) mein
   pehle jaisa 'denied' jab tak sahmati na mile. Baaki desh (India) mein analytics cookie shuru se chalu, ads wali cookie phir bhi
   band (personalised ads sirf sahmati par). Banner waise hi; 'Sirf zaroori cookies' dabane par analytics bhi band - aur agle har
   page par bhi band rehti hai (pehle ye yaad nahi rakha jaata tha). Privacy page ka Analytics hissa usi hisaab se + tareekh aaj.
   Ye badlaav owner ki DOHRI PUSHTI ke baad hi ('tracking fix').
2) Owner mode sirf '#owner-on' + localStorage tha. Telegram/Instagram/Facebook ke andar khulne wale browser ka apna alag dabba
   hota hai - wahan se aaye to visit gin li jaati thi. Ab '?owner=on' bhi chalta hai aur cookie mein bhi yaad (kuch app browser
   localStorage mita dete hain). Kisi bhi app ke andar wale browser mein: page ke bade shirshak (H1) par 4 second mein 7 baar tap
   -> 'Owner mode?' -> OK. 'owner link' bot ka hukum poora tareeka batata hai.
   Ye hissa privacy par asar nahi (sirf owner ka apna browser) - isliye apne aap lagta hai.
Sab badlaav website._apply_zip (audit gate) se; idempotent; naye roz ke page (pagequeue) bhi publish se pehle isi se guzarte hain.
"""
import re
import tempfile
import zipfile
from pathlib import Path

from . import state
from .log import log

GA_ID = "G-QX5MWV42TR"
EEA = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
       "PL", "PT", "RO", "SK", "SI", "ES", "SE", "IS", "LI", "NO", "GB", "CH"]

# ---- 1) consent (owner ki pushti ke baad)
C_OLD = ("gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',"
         "analytics_storage:'denied',wait_for_update:500});")
C_NEW = ("gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',"
         "analytics_storage:'denied',wait_for_update:500,region:[" + ",".join(f"'{c}'" for c in EEA) + "]});"
         "gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',"
         "analytics_storage:'granted'});")
U_OLD = ("try{var _c=localStorage.getItem('sh_consent');if(_c==='all'){gtag('consent','update',{ad_storage:'granted',"
         "ad_user_data:'granted',ad_personalization:'granted',analytics_storage:'granted'});}}catch(e){}")
U_NEW = ("try{var _c=localStorage.getItem('sh_consent');if(_c==='all'){gtag('consent','update',{ad_storage:'granted',"
         "ad_user_data:'granted',ad_personalization:'granted',analytics_storage:'granted'});}else if(_c==='essential')"
         "{gtag('consent','update',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',"
         "analytics_storage:'denied'});}}catch(e){}")
C_MARK = "region:['AT'"                 # C_NEW laga hai ya nahi

# ---- 2) owner mode (apne aap)
O_OLD = ("try{var _h=location.hash;if(_h==='#owner-on'){localStorage.setItem('sh_owner','1');}else if(_h==='#owner-off')"
         "{localStorage.removeItem('sh_owner');}if(localStorage.getItem('sh_owner')==='1'){window['ga-disable-" + GA_ID + "']=true;")
O_NEW = ("try{var _h=location.hash,_s=location.search,_ok=false;if(_h==='#owner-on'||/[?&]owner=on(&|$)/.test(_s))"
         "{try{localStorage.setItem('sh_owner','1');}catch(e){}document.cookie='sh_owner=1;path=/;max-age=63072000;SameSite=Lax;Secure';}"
         "else if(_h==='#owner-off'||/[?&]owner=off(&|$)/.test(_s)){try{localStorage.removeItem('sh_owner');}catch(e){}"
         "document.cookie='sh_owner=;path=/;max-age=0';}"
         "document.addEventListener('click',function(ev){var t=ev.target;if(!t||!t.closest||!t.closest('h1'))return;"
         "var n=Date.now();window._shT=(window._shT||[]).filter(function(x){return n-x<4000;});window._shT.push(n);"
         "if(window._shT.length>=7){window._shT=[];if(confirm('Owner mode: is browser ki visit Analytics mein na gine?'))"
         "{location.href=location.pathname+'?owner=on';}}});"
         "try{_ok=localStorage.getItem('sh_owner')==='1';}catch(e){}"
         "if(_ok||/(^|; )sh_owner=1/.test(document.cookie)){window['ga-disable-" + GA_ID + "']=true;")
O_MARK = "/(^|; )sh_owner=1/"

# ---- privacy page (sirf consent ke saath)
P_OLD1 = ("<li><b>Sahmati se pehle:</b> Google Consent Mode v2 ki wajah se analytics cookie band rehti hai. Is dauran Google ko "
          "bina cookie aur bina pehchaan wale saadharan signal (jaise page khula) ja sakte hain, jinse Google sirf andaaze wale "
          "kul aankde banata hai.</li>")
P_NEW1 = ("<li><b>Europe, UK aur Switzerland:</b> Google Consent Mode v2 ki wajah se analytics cookie tab tak band rehti hai jab tak "
          "aap banner par sahmati na dein. Is dauran Google ko bina cookie aur bina pehchaan wale saadharan signal (jaise page khula) "
          "ja sakte hain.</li>\n<li><b>India aur baaki desh:</b> sirf ginti wali analytics cookie shuru se chalti hai (vigyapan wali "
          "cookie nahi). Banner par <b>\"Sirf zaroori cookies\"</b> dabate hi ye bhi band ho jaati hai aur aage har page par band "
          "rehti hai.</li>")
P_OLD2 = "<li><b>Sahmati ke baad:</b> analytics cookie chalu hoti hai aur visit ka hisaab theek se judta hai.</li>"
P_NEW2 = ("<li><b>\"Sab cookies theek hain\" ke baad:</b> analytics ke saath vigyapan wali cookie bhi chalu ho sakti hai "
          "(jab site par ads lagenge).</li>")


PO_OLD = ("<li><b>sh_owner</b> — ye sirf tab banta hai jab site chalane wala apne hi browser me \"owner mode\" chalu kare, taaki "
          "uski apni visit Google Analytics me na gini jaaye. Aam visitor ke browser me ye kabhi nahi banta.</li>")
PO_NEW = ("<li><b>sh_owner</b> (localStorage + isi naam ki ek chhoti cookie) — ye sirf tab banta hai jab site chalane wala apne hi "
          "browser me \"owner mode\" chalu kare, taaki uski apni visit Google Analytics me na gini jaaye. Aam visitor ke browser me "
          "ye apne aap kabhi nahi banta; isme koi pehchaan nahi hoti.</li>")


def patch_owner(html):
    if not isinstance(html, str):
        return html, False
    ch = False
    if O_MARK not in html and O_OLD in html:
        html, ch = html.replace(O_OLD, O_NEW, 1), True
    if PO_OLD in html:
        html, ch = html.replace(PO_OLD, PO_NEW, 1), True
    return html, ch


def patch_consent(html):
    if not isinstance(html, str) or C_MARK in html or C_OLD not in html:
        return html, False
    h = html.replace(C_OLD, C_NEW, 1)
    if U_OLD in h:
        h = h.replace(U_OLD, U_NEW, 1)
    return h, True


def patch_privacy(html):
    if not isinstance(html, str) or P_OLD1 not in html:
        return html, False
    return html.replace(P_OLD1, P_NEW1, 1).replace(P_OLD2, P_NEW2, 1), True


def bump_date(html, today):
    """Privacy page ki 'Aakhri update' + JSON-LD dateModified = aaj (policy ka text badla to)."""
    import datetime
    d = datetime.date.fromisoformat(today)
    mon = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
           "December"][d.month - 1]
    html = re.sub(r'(Aakhri update: <time datetime=")[0-9-]+(">)[^<]+(</time>)', rf"\g<1>{today}\g<2>{d.day} {mon} {d.year}\g<3>",
                  html, 1)
    return re.sub(r'("dateModified":\s*")[0-9-]+(")', rf"\g<1>{today}\g<2>", html, 1)


def consent_on():
    return bool(state.get("trackfix_consent"))


def patch_html(html, consent=None, name="", today=None):
    """Ek page -> (naya, badla?). consent=None -> state ke hisaab se (owner ne 'tracking fix' pakka kiya ho tabhi)."""
    ch = False
    before = html
    html, c1 = patch_owner(html)
    ch |= c1
    if consent if consent is not None else consent_on():
        html, c2 = patch_consent(html)
        ch |= c2
        if name.endswith("privacy.html"):
            html, c3 = patch_privacy(html)
            ch |= c3
    if ch and name.endswith("privacy.html") and today:
        import re as _r
        txt = lambda h: _r.sub(r"<script.*?</script>", "", h, flags=_r.S)
        if txt(before) != txt(html):                 # policy ka padhne wala text badla -> tareekh aaj
            html = bump_date(html, today)
    return html, ch


def patch_dir(site_dir, consent=None):
    import datetime
    today = str(datetime.date.today())
    out = {}
    for f in sorted(Path(site_dir).glob("*.html")):
        try:
            new, ch = patch_html(f.read_text(encoding="utf-8"), consent, f.name, today)
        except Exception as e:
            log(f"trackfix {f.name}: {e}")
            continue
        if ch:
            out["site/" + f.name] = new
    return out


def apply(consent=None):
    """VM ki website par (audit gate). -> sandesh/None. Dohraane par kuch nahi badalta."""
    from . import website
    if not website.DIR.exists():
        return None
    with website.ZIP_LOCK:
        changed = patch_dir(website.DIR / "site", consent)
        if not changed:
            return None
        with tempfile.TemporaryDirectory() as td:
            zp = Path(td) / "trackfix.zip"
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
                for rel, txt in changed.items():
                    z.writestr(rel, txt)
            r = website._apply_zip(str(zp))
    ok = str(r).startswith("✅") or "pehle se lagi" in str(r)
    if not ok:
        log(f"trackfix apply: {str(r)[:200]}")
        return "⚠️ Tracking sudhaar website par nahi lag paya (audit/commit): " + str(r)[:300]
    return f"✅ Tracking sudhaar {len(changed)} page par laga (audit paas) - 15 min mein live."


def ask():
    import time as _t
    from . import tg
    return tg.say(
        "📊 '(not set)' AUR KAM GINTI KA ASLI ILAAJ - pakka karein?\n\n"
        "Wajah: abhi har desh mein analytics cookie tab tak band rehti hai jab tak visitor banner par 'Sab cookies theek hain' na "
        "dabaye. Der se dabaya = source '(not set)'. Na dabaya (zyada log, khaaskar Telegram/Instagram ke andar) = gine hi nahi.\n\n"
        "Badlaav (Google ka apna 'region' tareeka):\n"
        "• Europe/UK/Switzerland: pehle jaisa - sahmati ke baad hi.\n"
        "• India + baaki desh: sirf GINTI wali analytics cookie shuru se chalu. Ads wali cookie band hi rahegi.\n"
        "• Banner waisa hi - 'Sirf zaroori cookies' dabate hi analytics band, aur ab har agle page par bhi band rahega.\n"
        "• Privacy page ka 'Analytics' hissa isi hisaab se likha jayega + tareekh aaj.\n\n"
        "Nateeja: (not set) lagbhag khatam, aur asli log gine jayenge. India ke kanoon aur Google/AdSense niyam ke andar hai.",
        tg.inline([[("✅✅ Haan, laga do", "tf:on"), ("❌ Nahi", "tf:x")]]))


def on_callback(rest, run):
    from . import tg
    if rest == "on":
        state.put("trackfix_consent", True)
        return run(lambda: tg.say(apply(True) or "✅ Pehle se laga hua hai."))
    return tg.say("👍 Kuch nahi badla. (Jab chahein: 'tracking fix')")
