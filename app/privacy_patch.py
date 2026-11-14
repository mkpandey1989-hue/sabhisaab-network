"""v2.5.7: privacy page ko policy = practice banana (ek tap ki pushti ke baad). Bot VM ke site repo ki privacy.html padhta hai, EXACT purani
line aur naya text Telegram par dikhata hai; aap ✅✅ dabayein tabhi website.apply_zip (audit gate, force=False) se badlega.
Sirf do kaam: (1) Instagram 'LINK' private-reply wali line -> sach (hum comment/DM se link nahi bhejte), (2) UTM/WhatsApp-share ka ek chhota vaada
(sirf agar pehle se na likha ho). Baaki page ek akshar nahi chhua jata. Page mein ye line na mile to bot kuch nahi karta, sirf batata hai."""
import re
import zipfile

from . import state
from .log import log

IG_NEW = ("Hum Instagram par comment ya DM se link nahi bhejte. Jawab aur tool ka link bio mein ya website par milta hai. "
          "Agar aap khud hamein message bhejte hain to hum sirf aapke sawal ka jawab dete hain.")
UTM_NEW = ("Hamare link ke saath ek chhota tag (utm) ho sakta hai jisse hum jaante hain ki aap kis platform ya video se aaye; isme aapki pehchaan "
           "nahi hoti. Share button dabane par aapka WhatsApp khulta hai; hum koi data collect nahi karte.")
EL_RX = re.compile(r"<(p|li)\b[^>]*>((?:(?!</\1>).)*?)</\1>", re.S | re.I)


def _path():
    from .website import DIR
    return DIR / "site" / "privacy.html"


def find_ig(html):
    """Wo <p>/<li> jisme Instagram aur akshar-wala 'LINK' dono hon -> (poora element, tag) ya None."""
    for m in EL_RX.finditer(html):
        body = m.group(2)
        if re.search(r"\bLINK\b", body) and re.search(r"instagram", body, re.I):
            return m.group(0), m.group(1).lower()
    return None


def build(html):
    """-> (naya_html, [badlav ka saar]) ya (None, []) agar kuch badalna nahi."""
    out, notes = html, []
    ig = find_ig(out)
    if ig:
        old, tag = ig
        out = out.replace(old, f"<{tag}>{IG_NEW}</{tag}>", 1)
        notes.append(("Instagram line badlegi", re.sub(r"<[^>]+>", " ", old).strip()[:300], IG_NEW))
    if not re.search(r"\butm\b", out, re.I):
        mm = re.search(r"<(\w+)\b[^>]*\bid=\"data-deletion\"[^>]*>", out)
        if mm:
            out = out[:mm.start()] + f"<p>{UTM_NEW}</p>\n" + out[mm.start():]
            notes.append(("Naya chhota vaada (UTM/share)", "", UTM_NEW))
    return (out, notes) if out != html else (None, [])


def proposal():
    """-> (text, ok). Sirf padhta hai."""
    f = _path()
    if not f.exists():
        return "privacy.html VM ke site repo mein nahi mila (bot 'website file privacy' se pehle mangwa lein).", False
    new, notes = build(f.read_text(encoding="utf-8"))
    if not new:
        return "✅ Privacy page mein Instagram 'LINK' wali line nahi mili aur UTM vaada pehle se hai - kuch badalna nahi.", False
    L = ["📝 PRIVACY PAGE - ye badlav hoga (aur kuch nahi):"]
    for t, old, nw in notes:
        L.append(f"\n▪️ {t}" + (f"\n   PURANA: {old}" if old else "") + f"\n   NAYA: {nw}")
    L.append("\nPakka? (audit paas hone par hi jayega; 'Aakhri update' tareekh aap/developer badlein)")
    return "\n".join(L)[:3800], True


def apply():
    from . import website
    from .config import DATA
    f = _path()
    new, notes = build(f.read_text(encoding="utf-8")) if f.exists() else (None, [])
    if not new:
        return "Kuch badalne layak nahi mila (page badal chuka ho sakta hai)."
    z = DATA / "privacy_patch.zip"
    with zipfile.ZipFile(z, "w") as zz:
        zz.writestr("site/privacy.html", new)
    try:
        r = website.apply_zip(z, force=False)
    finally:
        z.unlink(missing_ok=True)
    if str(r).startswith("✅"):
        state.put("privacy_patched_at", __import__("time").time())
    return str(r)[:600]
