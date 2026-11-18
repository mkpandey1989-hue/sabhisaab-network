"""v3.4.25 (18 Nov 2026, owner: "jab bhi bot ko bolu 'sawal wali post do' to turant wahi sawal jo reel mein aa chuka aur jawab
website par hai - jo aaj de diya wo dobara na de, roz naya, reel wale kram se").

Hukum: 'sawal wali post' / 'sawal post do' / 'ek post do' / 'quiz post' / 'pahadi sawal post' (brand ka naam = usi brand ka).
Nateeja (owner ka diya hua saancha, hu-ba-hu):
    🧠 आज का सवाल / <sawal> / A) .. D) .. / 👇 सही जवाब + तरीका: / <poora /jawab link, UTM>
Niyam:
- Sirf wahi sawal jo reel mein ja chuka (answer_key - upload ke baad hi judta hai) + 4 vikalp + sahi jawab unme ek baar.
- Ek baar diya = kabhi dobara nahi (sp_given). 19:15 share kit ke WhatsApp/FB-group wale sawal bhi isi suchi mein.
- Kram: sabse nayi reel pehle (jo abhi tak nahi di). Sab de chuke = saaf bata do, purana dohraana nahi.
- Bot sawal/jawab apne se nahi likhta - reel wala hi.
"""
import json
import re
import urllib.parse as _u

from . import state, tg
from .config import BRANDS
from .log import log

KEEP = 800
BRAND_WORDS = {"pahadi": ("pahadi", "pahad", "पहाड़ी", "uttarakhand", "garhwali", "kumaoni"),
               "money": ("money", "paisa", "paise"),
               "deals": ("deals", "deal", "labh", "discount"),
               "sunonatak": ("sunonatak", "suno", "natak", "paheli", "dimag")}
RX = re.compile(r"(s[ae]?wa+l|sval|swal|quiz|paheli|पहेली|सवाल).{0,25}\bpost\b|\bpost\b.{0,12}(s[ae]?wa+l|swal|quiz)|"
                r"^(ek |1 |aur |ek aur |naya |nayi |new )?post (do|de|dedo|de do|dena|bhejo|chahiye|banao)\b|^(ek |1 )?aur post\b")


def given():
    return [str(x) for x in (state.get("sp_given") or [])]


def note(aid):
    if not aid:
        return
    aid = str(aid)
    state.update("sp_given", lambda l: ([x for x in (l or []) if str(x) != aid] + [aid])[-KEEP:], [])


def note_from_text(text):
    """share kit ke sandesh se '#c<aid>' nikaal kar 'diya hua' maano."""
    m = re.search(r"#c([0-9][0-9\-]*)\s*$", (text or "").strip())
    if m:
        note(m.group(1))


def _ok(e):
    o = [str(x) for x in (e.get("opts") or [])]
    return bool(e.get("q")) and len(o) == 4 and o.count(str(e.get("ans", ""))) == 1


def candidates(brand=None):
    g = set(given())
    out = []
    for e in reversed(state.get("answer_key") or []):          # sabse nayi reel pehle
        aid = str(e.get("aid") or e.get("code") or "")
        if not aid or aid in g or not _ok(e):
            continue
        if brand and e.get("brand") != brand:
            continue
        out.append(e)
    return out


def brand_in(tl):
    for b, ws in BRAND_WORDS.items():
        if any(w in tl for w in ws):
            return b
    for b, info in BRANDS.items():
        if info.get("name", "").lower() in tl:
            return b
    return None


def _clean(s):
    import html as _h
    return _h.unescape(re.sub(r"[ ]*#\S+", "", str(s or ""))).strip()


def post_text(e, source="whatsapp_status"):
    from .answers import answer_url
    ops = "\n".join(f"{'ABCD'[i]}) {_clean(o)}" for i, o in enumerate((e.get("opts") or [])[:4]))
    link = answer_url(e.get("aid") or e.get("code"), source, e.get("brand"))
    return f"🧠 आज का सवाल\n\n{_clean(e.get('q'))}\n\n{ops}\n\n👇 सही जवाब + तरीका:\n{link}"


def share_kb(text):
    link = (re.findall(r"https?://\S+", text) or [""])[-1]
    return {"inline_keyboard": [[{"text": "💬 WhatsApp par bhejo", "url": "https://wa.me/?text=" + _u.quote(text)}],
                                [{"text": "📘 Facebook par share", "url": "https://www.facebook.com/sharer/sharer.php?u=" + _u.quote(link, safe="")}]]}


def give(tl=""):
    """-> (head, post) ya (sandesh, None)."""
    b = brand_in(tl or "")
    c = candidates(b)
    if not c:
        left = len(candidates())
        bn = BRANDS.get(b, {}).get("name", b) if b else ""
        if b and left:
            return (f"📭 {bn} ke saare reel-sawal pehle de chuka hoon. Doosre brand ke {left} naye sawal baaki hain - "
                    "likho 'sawal wali post'.", None)
        return ("📭 Abhi koi naya sawal nahi bacha - jo reel gayi uske sawal pehle de chuka hoon (dohraana nahi). "
                "Agli sawal wali reel jaate hi naya milega.", None)
    e = c[0]
    txt = post_text(e)
    note(e.get("aid") or e.get("code"))
    rest = len(c) - 1
    head = (f"📋 Sawal wali post ({e.get('bname') or BRANDS.get(e.get('brand'), {}).get('name', '')}, reel #{e.get('code')}, "
            f"{e.get('date', '')}) - neeche wala sandesh lamba dabao → Copy, ya button se seedha bhejo. "
            f"Ye sawal ab dobara nahi aayega. Abhi {rest} naye aur baaki" + (" (is brand ke)" if b else "") + ".")
    return head, txt


def on_text(tl):
    tl = re.sub(r"[.!?।]+$", "", (tl or "").strip().lower())
    if "group post" in tl:                 # groupkit/share kit ka apna hukum
        return None
    if not RX.search(tl):
        return None
    try:
        head, txt = give(tl)
    except Exception as ex:
        log(f"sawalpost: {ex}")
        return tg.say(f"⚠️ Post nahi bani: {str(ex)[:150]}")
    tg.say(head)
    if txt:
        return tg.say(txt, share_kb(txt))
    return True


def seed_once():
    """v3.4.25: 17 Nov ko share kit se ja chuke (#5574 WhatsApp status, #8572 FB group) - dobara na aayein."""
    if state.get("sp_seed_3425"):
        return
    state.put("sp_seed_3425", True)
    for a in ("5574", "8572"):
        note(a)


if __name__ == "__main__":
    print(json.dumps(given()))
