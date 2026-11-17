"""v3.4.7 (17 Nov 2026) - Claude ki chat-review se nikle website sudhaar, VM ki website par EK baar (audit gate se).

Bot content nahi likhta - ye sudhaar Claude ne jaanch kar likhe hain; bot sirf lagata hai (trackfix jaisa, _apply_zip ke audit
gate se; fail = kuch live nahi). Har sudhaar 'dohraane par kuch nahi badalta' (idempotent).

1) /uttarakhand: 'Kaam / Tool / Link' table - ukgen ne 'https://sabhisaab.com/uttarakhand-farmer-id-ukfr' ka shuru wala hissa
   'Uttarakhand guide' link bana diya tha, peechhe '-farmer-id-ukfr' text bacha (pathak ko toota dikhta tha; sitescan ne
   2 'khud ko link' gine). Ab har khaana asli link (jo page live hai) ya soya link (queue ka page - live hote hi jagega).
2) /fire-number-calculator: title/H1 '/retirement-calculator' se lagbhag same tha (Google ek hi rakhta hai - 'Discovered,
   not indexed'). Ab alag: '25x Niyam Se Jaldi Azaadi Ka Hisaab' (page ka description pehle se 25x niyam par hai).
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
FIRE_NEW_T = "FIRE Number Calculator — 25x Niyam Se Jaldi Retirement Corpus | Sab Hisaab"
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


def patch_dir(site):
    """-> {zip-path: naya html} sirf badle file"""
    site = Path(site)
    out = {}

    def exists(s):
        return (site / f"{s}.html").exists()

    plan = [("uttarakhand", lambda h: fix_uk_table(h, exists)), ("fire-number-calculator", fix_fire)]
    plan += [(s, fix_tdee) for s in ("calorie-calculator", "bmr-calculator", "weight-loss-basics-guide")]
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
    return out


def apply():
    """VM ki website par (audit gate). -> sandesh ya None (kuch badalna nahi tha)."""
    from . import website
    if state.get("sitepatch_347") or not website.DIR.exists():
        return None
    with website.ZIP_LOCK:
        changed = patch_dir(website.DIR / "site")
        if not changed:
            state.put("sitepatch_347", True)
            return None
        with tempfile.TemporaryDirectory() as td:
            zp = Path(td) / "sitepatch347.zip"
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
                for rel, txt in changed.items():
                    z.writestr(rel, txt)
            r = website._apply_zip(str(zp))
    if str(r).startswith("✅") or "pehle se lagi" in str(r):
        state.put("sitepatch_347", True)
        return (f"Website sudhaar {len(changed)} page par laga (audit paas, 15 min mein live): /uttarakhand table ke toote link, "
                "FIRE calculator ka alag title, TDEE guide ke andar ke link")
    log(f"sitepatch: {str(r)[:200]}")
    return "⚠️ Website sudhaar (v3.4.7) audit mein ruka, kuch live nahi hua: " + str(r)[:250]
