"""v3.4.7/v3.4.8 (17 Nov 2026) - Claude ki chat-review se nikle website sudhaar, VM ki website par EK baar (audit gate se).

Bot content nahi likhta - ye sudhaar Claude ne jaanch kar likhe hain; bot sirf lagata hai (trackfix jaisa, _apply_zip ke audit
gate se; fail = kuch live nahi). Har sudhaar 'dohraane par kuch nahi badalta' (idempotent).

1) /uttarakhand: 'Kaam / Tool / Link' table - ukgen ne 'https://sabhisaab.com/uttarakhand-farmer-id-ukfr' ka shuru wala hissa
   'Uttarakhand guide' link bana diya tha, peechhe '-farmer-id-ukfr' text bacha (pathak ko toota dikhta tha; sitescan ne
   2 'khud ko link' gine). Ab har khaana asli link (jo page live hai) ya soya link (queue ka page - live hote hi jagega).
2) /fire-number-calculator: title/H1 '/retirement-calculator' se lagbhag same tha (Google ek hi rakhta hai - 'Discovered,
   not indexed'). Ab alag: '25x Niyam Se Jaldi Azaadi Ka Hisaab' (page ka description pehle se 25x niyam par hai).
   v3.4.8: v3.4.7 wala title 74 akshar tha -> VM audit ne roka ('title 60 se lamba'); ab 57.
4) Social: /links, /about aur homepage Organization 'sameAs' mein LinkedIn Page + Dailymotion channel (bahar ka link sirf
   naam ke saath - koi embed/cookie nahi, isliye privacy policy mein badlaav ki zarurat nahi).
3) /tdee-guide: andar se sirf 3 link (Crawled - not indexed). Calorie/BMR calculator aur Weight loss guide ki 'judey' suchi mein
   TDEE Guide ka link.
"""
import re
import tempfile
import zipfile
from pathlib import Path

from . import state
from .log import log

FIRE_OLD_T = "FIRE Number Calculator — Kitna Corpus Chahiye | Sab Hisaab"
FIRE_NEW_T = "FIRE Number Calculator — 25x Niyam Se Corpus | Sab Hisaab"   # 57 akshar (audit: max 60)
FIRE_OLD_H = "FIRE Number Calculator — Kitna Paisa Kaafi Hai"
FIRE_NEW_H = "FIRE Number Calculator — 25x Niyam Se Jaldi Azaadi Ka Hisaab"
TDEE_LINK = '<a href="/tdee-guide">TDEE Guide</a>'


def fix_uk_table(html, exists):
    """exists(slug) -> page live hai? -> naya html"""
    def broken(m):
        name, slug = m.group(1), "uttarakhand-" + m.group(2)
        return f"<td>{name}</td><td>{_cell(name, slug, exists)}</td>"
    html = re.sub(r'<td>([^<]{2,80})</td><td><a href="/uttarakhand" data-uk="uttarakhand">Uttarakhand guide</a>-([a-z0-9-]+)</td>',
                  broken, html)

    def raw(m):
        name = m.group(1)
        if name.strip().lower() in ("guide", "tool", "calculator", "page"):   # 'Guide' jaisa kamzor naam -> pehle khaane ka kaam
            prev = re.findall(r"<td>([^<]{2,80})</td>", html[max(0, m.start() - 200):m.start()])
            name = prev[-1] if prev else name
        return f"<td>{m.group(1)}</td><td>{_cell(name, m.group(2), exists)}</td>"
    return re.sub(r'<td>([^<]{2,80})</td><td>https://sabhisaab\.com/([a-z0-9-]+)</td>', raw, html)


def _cell(name, slug, exists):
    name = re.sub(r"\s*\((naya|new)\)\s*$", "", name).strip()
    if exists(slug):
        return f'<a href="/{slug}">{name}</a>'
    return f'<span data-ukg="{slug}" data-h="/{slug}">{name}</span>'      # pagequeue.activate() page live hote hi link banata hai


def fix_fire(html):
    return html.replace(FIRE_OLD_T, FIRE_NEW_T).replace(FIRE_OLD_H, FIRE_NEW_H)


def fix_tdee(html):
    if 'href="/tdee-guide"' in html:
        return html
    m = re.search(r'(<div class="(?:nextread|rel)">.*?<a href="/tdee-calculator">TDEE Calculator</a>)', html, re.S)
    if not m:
        return html
    return html[:m.end()] + ("\n" if "\n<a" in m.group(1) else "") + TDEE_LINK + html[m.end():]


LI_URL = "https://www.linkedin.com/company/144149065/"
DM_URL = "https://www.dailymotion.com/sabhisaab"
PIN_LI = ('<li><b>Pinterest:</b> <a href="https://www.pinterest.com/sabhisaabcom/" target="_blank" rel="noopener">'
          'pinterest.com/sabhisaabcom</a> — calculator aur bachat ke chhote card.</li>')
SOC_LI = (f'\n<li><b>LinkedIn:</b> <a href="{LI_URL}" target="_blank" rel="noopener">Sab Hisaab LinkedIn Page</a> — roz ek sawal '
          f'aur ek kaam ka calculator.</li>\n<li><b>Dailymotion:</b> <a href="{DM_URL}" target="_blank" rel="noopener">'
          'dailymotion.com/sabhisaab</a> — roz ki paheli aur hisaab wali video.</li>')
PIN_AB = '<b>Pinterest:</b> <a href="https://www.pinterest.com/sabhisaabcom/" target="_blank" rel="noopener">sabhisaabcom</a>'
SOC_AB = (f' &middot; <b>LinkedIn:</b> <a href="{LI_URL}" target="_blank" rel="noopener">Sab Hisaab Page</a> &middot; '
          f'<b>Dailymotion:</b> <a href="{DM_URL}" target="_blank" rel="noopener">sabhisaab</a>')
PIN_SA = '"https://www.pinterest.com/sabhisaabcom/"'


def fix_links(html):
    if DM_URL in html or PIN_LI not in html:
        return html
    return html.replace(PIN_LI, PIN_LI + SOC_LI, 1)


def fix_about(html):
    if DM_URL in html or PIN_AB not in html:
        return html
    return html.replace(PIN_AB, PIN_AB + SOC_AB, 1)


def fix_sameas(html):
    if DM_URL in html or PIN_SA not in html or '"sameAs"' not in html:
        return html
    return html.replace(PIN_SA, PIN_SA + f', "{LI_URL}", "{DM_URL}"', 1)


PRIV_PIN = ('<li><b>Pinterest:</b> hamare pin ek manzoor Pinterest app se jaate hain. Pinterest ki policy: <a href="https://policy.pinterest.com/'
            'privacy-policy" target="_blank" rel="noopener">Pinterest Privacy Policy</a>.</li>')
PRIV_ADD = ('\n<li><b>LinkedIn:</b> Sab Hisaab LinkedIn Page par roz ki post Make.com ke zariye jaati hai — sirf post bhejna; hum '
            'LinkedIn se kisi vyakti ka data nahi padhte ya rakhte. LinkedIn ki policy: <a href="https://www.linkedin.com/legal/'
            'privacy-policy" target="_blank" rel="noopener">LinkedIn Privacy Policy</a>.</li>'
            '\n<li><b>Dailymotion:</b> hamari kuch video Dailymotion ke official API se upload hoti hain — sirf upload; dekhne walon ka '
            'koi data hum nahi lete. Website par Dailymotion ka koi player/cookie nahi hai, sirf channel ka link hai. Dailymotion ki '
            'policy: <a href="https://legal.dailymotion.com/en/summary-of-privacy-policy" target="_blank" rel="noopener">Dailymotion '
            'Privacy Policy</a>.</li>')
PRIV_87_OLD = "— YouTube, Facebook, Instagram, Threads aur Pinterest par.</li>"
PRIV_87_NEW = "— YouTube, Facebook, Instagram, Threads, Pinterest, LinkedIn aur Dailymotion par.</li>"


def fix_privacy(html, today=None):
    """Asli badlaav (naye platform) -> 'Aakhri update' + dateModified aaj (sirf tab)."""
    import datetime as _d
    if "legal.dailymotion.com" in html or PRIV_PIN not in html:
        return html
    t = today or _d.date.today()
    mon = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
           "December"][t.month - 1]
    html = html.replace(PRIV_PIN, PRIV_PIN + PRIV_ADD, 1).replace(PRIV_87_OLD, PRIV_87_NEW, 1)
    html = re.sub(r'"dateModified": "\d{4}-\d\d-\d\d"', f'"dateModified": "{t.isoformat()}"', html, count=1)
    html = re.sub(r'(Aakhri update: <time datetime=")\d{4}-\d\d-\d\d(">)[^<]*(</time>)',
                  lambda m: f"{m.group(1)}{t.isoformat()}{m.group(2)}{t.day} {mon} {t.year}{m.group(3)}", html, count=1)
    return html


def patch_dir(site):
    """-> {zip-path: naya html} sirf badle file"""
    site = Path(site)
    out = {}

    def exists(s):
        return (site / f"{s}.html").exists()

    plan = [("uttarakhand", lambda h: fix_uk_table(h, exists)), ("fire-number-calculator", fix_fire)]
    plan += [(s, fix_tdee) for s in ("calorie-calculator", "bmr-calculator", "weight-loss-basics-guide")]
    plan += [("links", fix_links), ("about", fix_about), ("index", fix_sameas), ("privacy", fix_privacy)]
    if not exists("tdee-guide"):
        plan = [p for p in plan if p[1] is not fix_tdee]
    for slug, fn in plan:
        f = site / f"{slug}.html"
        if not f.exists():
            continue
        old = f.read_text(encoding="utf-8")
        new = fn(old)
        if new != old:
            out[f"site/{slug}.html"] = new
    if "site/privacy.html" in out:                       # sitemap lastmod = page ka dateModified (audit WARNING nahi)
        sm = site / "sitemap.xml"
        m = re.search(r'"dateModified": "(\d{4}-\d\d-\d\d)"', out["site/privacy.html"])
        if sm.exists() and m:
            x = sm.read_text(encoding="utf-8")
            y = re.sub(r"(<loc>https://sabhisaab\.com/privacy</loc>\s*<lastmod>)[^<]*(</lastmod>)",
                       lambda k: k.group(1) + m.group(1) + k.group(2), x, count=1)
            if y != x:
                out["site/sitemap.xml"] = y
    return out


def fix_story_title(html, wk):
    """v3.4.18: stories/*-quiz-YYYY-wNN - title/description/amp-story title mein '(सप्ताह NN)' (do hafte ke same title the)."""
    if f"(सप्ताह {wk})" in html:
        return html
    m = re.search(r"<title>(.*?) \| Sab Hisaab</title>", html)
    if not m:
        return html
    t = m.group(1)
    t2 = f"{t} (सप्ताह {wk})"
    html = html.replace(f"<title>{t} | Sab Hisaab</title>", f"<title>{t2} | Sab Hisaab</title>", 1)
    html = html.replace(f'<meta name="description" content="{t} - ', f'<meta name="description" content="{t2} - ', 1)
    html = html.replace(f'<amp-story standalone title="{t}"', f'<amp-story standalone title="{t2}"', 1)
    return html


GQ_PIN = "Hum aapka phone number ya naam save nahi karte.</p>"
GQ_ADD = ('\n<p><b>Telegram discussion group quiz:</b> hamare Telegram channel ke discussion group mein sawal-post ke neeche '
          'A/B/C/D likhne par bot batata hai ki jawab sahi hai ya nahi. Hafte ki leaderboard ke liye sirf aapka Telegram '
          'first name, Telegram ka number-id aur score rakha jaata hai — phone number kabhi nahi. Group mein "score hatao" '
          'likhte hi aapka naam aur score turant mit jaata hai.</p>')


def fix_privacy_gq(html, today=None):
    import datetime as _d
    if "discussion group quiz" in html or GQ_PIN not in html:
        return html
    t = today or _d.date.today()
    mon = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
           "December"][t.month - 1]
    html = html.replace(GQ_PIN, GQ_PIN + GQ_ADD, 1)
    html = re.sub(r'"dateModified": "\d{4}-\d\d-\d\d"', f'"dateModified": "{t.isoformat()}"', html, count=1)
    html = re.sub(r'(Aakhri update: <time datetime=")\d{4}-\d\d-\d\d(">)[^<]*(</time>)',
                  lambda m: f"{m.group(1)}{t.isoformat()}{m.group(2)}{t.day} {mon} {t.year}{m.group(3)}", html, count=1)
    return html


def apply_privacy_gq():
    """v3.4.21: privacy mein group-quiz line (ek baar, audit gate). Lagne ke baad hi groupquiz naam/score rakhta hai."""
    from . import website
    if state.get("sitepatch_3421") or not website.DIR.exists():
        return None
    with website.ZIP_LOCK:
        site = website.DIR / "site"
        f = site / "privacy.html"
        if not f.exists():
            return None
        old = f.read_text(encoding="utf-8")
        new = fix_privacy_gq(old)
        if new == old:
            if "discussion group quiz" in old:
                state.put("sitepatch_3421", True)
            return None
        changed = {"site/privacy.html": new}
        sm = site / "sitemap.xml"
        m = re.search(r'"dateModified": "(\d{4}-\d\d-\d\d)"', new)
        if sm.exists() and m:
            x = sm.read_text(encoding="utf-8")
            y = re.sub(r"(<loc>https://sabhisaab\.com/privacy</loc>\s*<lastmod>)[^<]*(</lastmod>)",
                       lambda k: k.group(1) + m.group(1) + k.group(2), x, count=1)
            if y != x:
                changed["site/sitemap.xml"] = y
        with tempfile.TemporaryDirectory() as td:
            zp = Path(td) / "sitepatch3421.zip"
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
                for rel, txt in changed.items():
                    z.writestr(rel, txt)
            r = website._apply_zip(str(zp))
    if str(r).startswith("✅") or "pehle se lagi" in str(r):
        state.put("sitepatch_3421", True)
        return "Privacy policy mein Telegram group-quiz ki line judi (audit paas) - ab group leaderboard chalu."
    log(f"sitepatch3421: {str(r)[:200]}")
    return "⚠️ Privacy (group quiz) sudhaar audit mein ruka: " + str(r)[:200]


def apply_stories():
    """VM website par EK baar (audit gate): purani quiz stories ke title alag."""
    from . import website
    if state.get("sitepatch_3418") or not website.DIR.exists():
        return None
    with website.ZIP_LOCK:
        site = website.DIR / "site"
        changed = {}
        for f in sorted((site / "stories").glob("*-quiz-*-w*.html")):
            wk = f.stem.rsplit("-w", 1)[-1].lstrip("0")
            old = f.read_text(encoding="utf-8")
            new = fix_story_title(old, wk)
            if new != old:
                changed[f"site/stories/{f.name}"] = new
        if not changed:
            state.put("sitepatch_3418", True)
            return None
        with tempfile.TemporaryDirectory() as td:
            zp = Path(td) / "sitepatch3418.zip"
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
                for rel, txt in changed.items():
                    z.writestr(rel, txt)
            r = website._apply_zip(str(zp))
    if str(r).startswith("✅") or "pehle se lagi" in str(r):
        state.put("sitepatch_3418", True)
        return f"Website sudhaar: {len(changed)} Web Story ke title ab alag-alag (do hafte ke same the) - audit paas, 15 min mein live."
    log(f"sitepatch3418: {str(r)[:200]}")
    return "⚠️ Web Story title sudhaar audit mein ruka, kuch live nahi hua: " + str(r)[:250]


def apply():
    """VM ki website par (audit gate). -> sandesh ya None (kuch badalna nahi tha)."""
    from . import website
    if state.get("sitepatch_348") or not website.DIR.exists():
        return None
    with website.ZIP_LOCK:
        changed = patch_dir(website.DIR / "site")
        if not changed:
            state.put("sitepatch_348", True)
            return None
        with tempfile.TemporaryDirectory() as td:
            zp = Path(td) / "sitepatch347.zip"
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
                for rel, txt in changed.items():
                    z.writestr(rel, txt)
            r = website._apply_zip(str(zp))
    if str(r).startswith("✅") or "pehle se lagi" in str(r):
        state.put("sitepatch_348", True)
        return (f"Website sudhaar {len(changed)} page par laga (audit paas, 15 min mein live): /uttarakhand table ke toote link, "
                "FIRE calculator ka alag title, TDEE guide ke andar ke link, LinkedIn + Dailymotion ke link (/links, /about, homepage) aur privacy policy mein dono platform")
    log(f"sitepatch: {str(r)[:200]}")
    return "⚠️ Website sudhaar (v3.4.8) audit mein ruka, kuch live nahi hua: " + str(r)[:250]
