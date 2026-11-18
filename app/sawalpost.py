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

v3.4.26 (owner: "jis platform/brand ki likhu uski de, sab platform ki jab mangu - kuch miss na ho"):
- '<platform> post' / '<brand> <platform> post' / '<brand> post' / '<brand> sawal' / 'sab platform post' (ek sawal, har platform
  ka apna saancha + sahi UTM). Platform: whatsapp, fb group, facebook (page), instagram (caption + 1080x1920 story photo +
  sticker link), threads, linkedin, reddit (title + body alag), telegram.
- 'group post' (UK page banner kit), 'linkedin post' (Make se asli post) - purane hukum waise hi.
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
               "sunonatak": ("sunonatak", "suno natak", "suno", "natak")}

# platform -> (pehchaan shabd, utm_source, naam)
PLAT = {
    "facebook": (("fb page", "facebook page", "page ke liye", "page par"), "facebook", "Facebook PAGE"),
    "fbgroup": (("fb group", "facebook group", "fbgroup", "group ke liye", "group mein", "group me ", "groups", "facebook", "fb ", " fb"),
                "facebook_group", "Facebook GROUP"),     # v3.4.27: sirf 'facebook' = GROUP (owner groups mein daalta hai)
    "whatsapp": (("whatsapp", "whats app", "wa status", "status"), "whatsapp_status", "WhatsApp status / channel"),
    "instagram": (("instagram", "insta", " ig", "ig ", "story"), "instagram", "Instagram"),
    "threads": (("threads", "thread"), "threads", "Threads"),
    "linkedin": (("linkedin", "linkdin", "linked in"), "linkedin", "LinkedIn"),
    "reddit": (("reddit",), "reddit", "Reddit"),
    "telegram": (("telegram", "tg "), "telegram", "Telegram"),
}
ALL_WORDS = ("sab platform", "sabhi platform", "har platform", "all platform", "sab jagah", "sabki post", "sab ki post", "sabke liye")
SKIP_WORDS = ("kitn", "gayi", "gyi", "gaya", "hatao", "delete", "band", "chalu", "haal", "status kya", "report", "seekh", "namoona")
EXACT_OTHER = ("group post", "group post do", "aaj ka group post", "group post band", "group post chalu", "linkedin post",
               "linkedin post karo", "welcome post", "mauka post", "fb link post band", "fb link post chalu")
OPENERS = ["🧠 दिमाग लगाइए - पहली बार में सही बता पाएँगे?", "🤔 ज़रा सोचिए, जवाब क्या होगा?", "🎯 आज का सवाल - 10 सेकंड में जवाब दीजिए!",
           "🔥 99% लोग पहली बार में गलत बताते हैं - आप?", "📝 आज की पहेली - कमेंट में अपना जवाब लिखिए", "💡 सोचो, समझो, फिर बताओ!"]
RX = re.compile(r"(s[ae]?wa+l|sval|swal|quiz|paheli|पहेली|सवाल).{0,25}\bpost\b|\bpost\b.{0,12}(s[ae]?wa+l|swal|quiz)|"
                r"^(ek |1 |aur |ek aur |naya |nayi |new )?post (do|de|dedo|de do|dena|bhejo|chahiye|banao)\b|^(ek |1 )?aur post\b")


def _gv():
    """v3.4.27: platform-wise 'diya hua' (owner: WhatsApp par diya sawal FB group ke liye bhi chahiye - Pahadi jaldi khatam ho
    jaata tha). Purana sp_given (sab ek suchi) -> whatsapp + facebook mein maana."""
    d = state.get("sp_gv")
    if d is None:
        old = [str(x) for x in (state.get("sp_given") or [])]
        d = {"whatsapp": old[-KEEP:], "facebook": old[-KEEP:]}
        state.put("sp_gv", d)
    return d


def given(plat=None):
    d = _gv()
    if plat:
        return [str(x) for x in d.get(plat, [])]
    out = []
    for v in d.values():
        out += [str(x) for x in v]
    return out


def note(aid, plat="whatsapp"):
    if not aid:
        return
    aid = str(aid)

    def f(d):
        d = d or {}
        lst = [x for x in d.get(plat, []) if str(x) != aid] + [aid]
        d[plat] = lst[-KEEP:]
        return d
    _gv()
    state.update("sp_gv", f, {})


def note_from_text(text, plat="whatsapp"):
    """share kit ke sandesh se '#c<aid>' nikaal kar 'diya hua' maano."""
    m = re.findall(r"#c([0-9][0-9\-]*)", (text or ""))      # v3.4.27: link ab aakhri line nahi (3 line saancha)
    if m:
        note(m[-1], plat)


def _ok(e):
    o = [str(x) for x in (e.get("opts") or [])]
    return bool(e.get("q")) and len(o) == 4 and o.count(str(e.get("ans", ""))) == 1


def candidates(brand=None, plats=None):
    g = set()
    for p_ in (plats or ["whatsapp"]):
        g |= set(given(p_))
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


SAWAL_RX = re.compile(r"s[ae]?wa+l|swal|sval|quiz|paheli|पहेली|सवाल")
SITE = "https://sabhisaab.com"


def plats_in(tl):
    """-> platform list (kram se). 'sab platform' = sab."""
    t = f" {tl} "
    if any(w in t for w in ALL_WORDS):
        return list(PLAT.keys())
    for k, (ws, _s, _n) in PLAT.items():
        if any(w in t for w in ws):
            return [k]
    return []


def is_ours(tl):
    if tl in EXACT_OTHER or any(w in tl for w in SKIP_WORDS):
        return False
    if RX.search(tl):
        return True
    has_post = bool(re.search(r"\bpost\b|पोस्ट", tl))
    has_sawal = bool(SAWAL_RX.search(tl))
    return bool((brand_in(tl) or plats_in(tl)) and (has_post or has_sawal) and len(tl.split()) <= 7)


def link(e, src, medium="answer"):
    from . import answers
    aid = str(e.get("aid") or e.get("code"))
    if not answers.live():
        return answers.answer_url(aid, src, e.get("brand"))
    return (f"{SITE}{answers.PAGE}?utm_source={src}&utm_medium={medium}&utm_campaign={e.get('brand')}"
            f"&utm_content=c{aid}#c{aid}")


def _ops(e, sep="\n"):
    return sep.join(f"{'ABCD'[i]}) {_clean(o)}" for i, o in enumerate((e.get("opts") or [])[:4]))


def fmt(e, plat):
    """-> [(sirlekh, text)] - har platform ka apna saancha (niyam ke andar)."""
    q = _clean(e.get("q"))
    if plat == "whatsapp":
        return [("📱 WHATSAPP status / channel", post_text(e))]
    if plat == "telegram":
        return [("✈️ TELEGRAM", post_text(e, "telegram"))]
    if plat == "fbgroup":
        # v3.4.27 (owner: group mein 'See more' aata, link chhup jaata): 3 line - sawal / vikalp ek line / link. Chhota link.
        aid = str(e.get("aid") or e.get("code"))
        os_ = [_clean(o) for o in (e.get("opts") or [])[:4]]
        one = "  ".join(f"{'ABCD'[i]}) {o}" for i, o in enumerate(os_))
        opl = one if len(one) <= 60 else "  ".join(f"{'ABCD'[i]}) {o}" for i, o in enumerate(os_[:2])) + "\n" + \
            "  ".join(f"{'ABCD'[i + 2]}) {o}" for i, o in enumerate(os_[2:]))
        lk = link(e, "facebook_group")
        try:
            from . import answers as _A
            if _A.live():
                lk = f"{SITE}{_A.PAGE}?utm_source=facebook_group&utm_campaign={e.get('brand')}&utm_content=c{aid}#c{aid}"
        except Exception:
            pass
        return [("👥 FACEBOOK GROUP - 3 line (See more se pehle sab dikhega). Post karte waqt neeche bana LINK CARD ka ❌ MAT "
                 "dabana - wo poora card clickable hai. Har group mein alag sawal maango.",
                 f"🧠 {q}\n{opl}\n👇 सही जवाब: {lk}\n✍️ अपना जवाब कमेंट में लिखिए"),
                ("💬 Jis group mein LINK MANA ho: post mein upar ki sirf pehli 2 line (sawal + vikalp) daalo, aur ye apne PEHLE "
                 "COMMENT mein (comment ka link bhi click hota hai):",
                 f"✅ सही जवाब और आसान तरीका यहाँ: {lk}")]
    if plat == "facebook":
        return [("📘 FACEBOOK PAGE post (link ka card apne aap banega)",
                 f"🧩 आज का सवाल\n{q}\n\n{_ops(e)}\n\nपहले खुद सोचिए, फिर सही जवाब और तरीका यहाँ देखिए 👇\n{link(e, 'facebook')}")]
    if plat == "threads":
        t = f"🧠 {q}\n\n{_ops(e)}\n\nसही जवाब + तरीका 👇\n{link(e, 'threads')}"
        return [("🧵 THREADS (500 akshar ke andar)", t[:495])]
    if plat == "linkedin":
        return [("💼 LINKEDIN (apni profile/page par haath se)",
                 f"Quick brain teaser 🧠\n\n{q}\n\n{_ops(e)}\n\nComment your answer 👇\nAnswer + method: {link(e, 'linkedin')}"
                 "\n\n#SabHisaab #Puzzle #Maths #GK")]
    if plat == "reddit":
        return [("🟠 REDDIT - 1) TITLE dabbe mein (link nahi)", f"🧠 {q}"),
                 ("🟠 REDDIT - 2) BODY / text dabbe mein. Naye account se link wali post hat sakti hai - karma 100+ hone tak "
                  "link wali 2 line hata do aur link sirf comment mein, jab koi poochhe.",
                  f"{_ops(e)}\n\nपहले कमेंट में अपना जवाब लिखिए 👇\nसही जवाब + तरीका: {link(e, 'reddit', 'post')}")]
    if plat == "instagram":
        st = link(e, "instagram", "story")
        return [("📸 INSTAGRAM reel/post CAPTION (caption ka link click nahi hota - isliye bio/highlight)",
                 f"🧠 {q}\n\n{_ops(e)}\n\n💬 कमेंट में अपना जवाब लिखिए!\n✅ सही जवाब: प्रोफ़ाइल पर '✅ जवाब' हाइलाइट या bio का लिंक 👆\n\n"
                 "#PahadiHisaab #SabHisaab #Quiz #GK #Uttarakhand" if e.get("brand") == "pahadi" else
                 f"🧠 {q}\n\n{_ops(e)}\n\n💬 कमेंट में अपना जवाब लिखिए!\n✅ सही जवाब: प्रोफ़ाइल पर '✅ जवाब' हाइलाइट या bio का लिंक 👆\n\n"
                 "#SabHisaab #Quiz #Puzzle #GK"),
                ("📸 INSTAGRAM STORY - upar wali photo lagao → sticker 🙂 → LINK → ye link paste → text: सही जवाब देखें 👆", st)]
    return [("📱", post_text(e))]


def story_card(e, out):
    """1080x1920 Instagram story photo: brand rang, 'आज का सवाल', sawal, 4 vikalp. Neeche khaali jagah = link sticker."""
    from PIL import Image, ImageDraw
    from . import text as T
    W_, H_ = 1080, 1920
    cols = {"pahadi": ((22, 101, 52), (12, 74, 110)), "money": ((15, 118, 110), (30, 58, 138)),
            "deals": ((194, 65, 12), (127, 29, 29)), "sunonatak": ((88, 28, 135), (30, 27, 75))}
    top, bot = cols.get(e.get("brand"), cols["money"])
    img = Image.new("RGB", (W_, H_), top)
    d = ImageDraw.Draw(img)
    for y in range(H_):
        k = y / H_
        d.line([(0, y), (W_, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3)))
    bn = e.get("bname") or BRANDS.get(e.get("brand"), {}).get("name", "Sab Hisaab")
    T.draw(d, (W_ / 2 - T.width(bn, 44) / 2, 150), bn, 44, (255, 255, 255))
    hd = "आज का सवाल"
    d.rounded_rectangle([200, 230, 880, 350], 40, fill=(250, 204, 21))
    T.draw(d, (W_ / 2 - T.width(hd, 72) / 2, 248), hd, 72, (30, 30, 30))
    lines = T.wrap(_clean(e.get("q")), 74, W_ - 160)[:5]
    y = 430
    for ln in lines:
        T.draw(d, (W_ / 2 - T.width(ln, 74) / 2, y), ln, 74, (255, 255, 255), stroke=3, stroke_fill=(0, 0, 0))
        y += 102
    y += 50
    for i, o in enumerate((e.get("opts") or [])[:4]):
        d.rounded_rectangle([110, y, W_ - 110, y + 120], 30, fill=(255, 255, 255))
        d.ellipse([135, y + 20, 215, y + 100], fill=top)
        T.draw(d, (175 - T.width("ABCD"[i], 50) / 2, y + 28), "ABCD"[i], 50, (255, 255, 255))
        ot = T.wrap(_clean(o), 52, W_ - 380)[:1]
        T.draw(d, (250, y + 30), ot[0] if ot else "", 52, (20, 20, 20))
        y += 150
    ft = "सही जवाब और तरीका - नीचे लिंक दबाइए"
    T.draw(d, (W_ / 2 - T.width(ft, 46) / 2, max(y + 40, 1560)), ft, 46, (253, 230, 138))
    img.save(out, quality=92)
    return out


def give(tl=""):
    """-> (head, [(sirlekh, text)], photo ya None) ya (sandesh, [], None)."""
    b = brand_in(tl or "")
    ps = plats_in(tl or "") or ["whatsapp"]
    c = candidates(b, ps)
    if not c:
        left = len(candidates(None, ps))
        bn = BRANDS.get(b, {}).get("name", b) if b else ""
        pn0 = "sab platform" if len(ps) > 1 else PLAT[ps[0]][2]
        if b and left:
            return (f"📭 {bn} ke saare reel-sawal {pn0} ke liye pehle de chuka hoon. Doosre brand ke {left} naye sawal baaki "
                    f"hain - likho '{PLAT[ps[0]][2].split()[0].lower()} post' (bina brand). Doosre platform ke liye {bn} ke "
                    "sawal abhi baaki ho sakte hain.", [], None)
        return (f"📭 {pn0} ke liye koi naya sawal nahi bacha - jo reel gayi uske sawal is platform par pehle de chuka hoon "
                "(dohraana nahi). Agli sawal wali reel jaate hi naya milega.", [], None)
    e = c[0]
    parts = []
    for p_ in ps:
        parts += fmt(e, p_)
    photo = None
    if "instagram" in ps:
        try:
            from .config import TMP
            photo = story_card(e, TMP / f"story_{e.get('aid') or e.get('code')}.jpg")
        except Exception as ex:
            log(f"story card: {ex}")
    for p_ in ps:
        note(e.get("aid") or e.get("code"), p_)
    rest = len(c) - 1
    pn = "sab platform" if len(ps) > 1 else PLAT[ps[0]][2]
    head = (f"📋 {pn} ki post ({e.get('bname') or BRANDS.get(e.get('brand'), {}).get('name', '')}, reel #{e.get('code')}, "
            f"{e.get('date', '')}) - har sandesh lamba dabao → Copy. Ye sawal {pn} ke liye dobara nahi aayega. "
            f"Abhi {rest} naye aur baaki" + (" (is brand ke)" if b else "") + ".\n"
            "Maang sakte ho: '<brand> <platform> post' - jaise 'pahadi fb group post', 'money insta post', 'sab platform post'.")
    return head, parts, photo


def on_text(tl):
    tl = re.sub(r"[.!?।]+$", "", (tl or "").strip().lower()).strip()
    if not is_ours(tl):
        return None
    try:
        head, parts, photo = give(tl)
    except Exception as ex:
        log(f"sawalpost: {ex}")
        tg.say(f"⚠️ Post nahi bani: {str(ex)[:150]}")
        return True
    tg.say(head)
    if photo:
        try:
            with open(photo, "rb") as fh:
                tg.call("sendPhoto", {"chat_id": tg._chat(), "caption": "📸 Instagram STORY ki photo - kholo → ⋮ → Save, "
                                      "phir Instagram Story mein lagao (neeche khaali jagah par LINK sticker)"}, {"photo": fh})
        except Exception as ex:
            log(f"story photo: {ex}")
    for h, txt in parts:
        tg.say(h)
        tg.say(txt, share_kb(txt) if "http" in txt and not txt.startswith("http") else None)
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
