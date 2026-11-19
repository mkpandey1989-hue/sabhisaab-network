"""v3.4.26 (18 Nov 2026): bot ki chatting (CHAT.md 17-18 Nov) mein jo baatein AI galat samjha - unke seedhe jawab.

- 'Aaj linkdin per kitni post gyi' -> AI ne kaha 'bot LinkedIn par post nahi karta' (galat: Make se roz jaati hai) -> asli ginti.
- 'Graff' / 'growth graff' -> AI ne poocha 'saaf likhein' -> seedha growth graph.
- 'pin kit' -> har platform par EK BAAR lagane wala text (bio / pin / highlight / button) - brand ke hisaab se, sahi UTM ke saath.
"""
import datetime
import re

from . import state, tg
from .config import BRANDS

SITE = "https://sabhisaab.com"
HANDLE = {"sunonatak": "sunonatak", "money": "sabhisaabmoney", "deals": "labhlodeals", "pahadi": "pahadihisaab"}


def li_count_text():
    today = str(datetime.date.today())
    lg = state.get("li_log") or []
    td = [x for x in lg if str(x.get("d")) == today]
    wk = [x for x in lg if str(x.get("d", "")) >= str(datetime.date.today() - datetime.timedelta(days=6))]
    L = [f"💼 LinkedIn (Sab Hisaab Page) - bot Make.com ke raaste roz khud post karta hai (subah 09:15 + shaam 18:30).",
         f"• Aaj: {len(td)} post" + "".join(f"\n   - {x.get('t', '')} {('(' + str(x.get('c')) + ')') if x.get('c') not in (None, '?') else ''}"
                                             for x in td),
         f"• Pichhle 7 din: {len(wk)} post"]
    if state.get("li_fail"):
        L.append(f"⚠️ Aakhri dikkat: {state.get('li_last_err')} - Make mein scenario ON hai ya nahi dekhein.")
    L.append("Poora haal: 'linkedin haal'")
    return "\n".join(L)


def _u(src, brand, medium="profile", path="/jawab"):
    return f"{SITE}{path}?utm_source={src}&utm_medium={medium}&utm_campaign={brand}"


def pin_kit(brand=None):
    bs = [brand] if brand in BRANDS else list(BRANDS)
    out = ["📌 PIN KIT - har platform par EK BAAR lagao, phir hamesha upar rahega (bot ki nayi post neeche jaati hai).",
           "Har brand ka apna link (UTM) - report mein pata chalega kahan se kitne aaye. Brand akela chahiye: 'pin kit pahadi'.", ""]
    for b in bs:
        nm = BRANDS[b]["name"]
        txt = (f"🧠 रोज़ नया सवाल — सही जवाब और आसान तरीका यहाँ 👇\n{_u('{S}', b)}\n"
               f"✅ 300+ फ्री हिंदी कैलकुलेटर: {SITE}/?utm_source={{S}}&utm_medium=profile&utm_campaign={b}")
        out.append(f"━━━━ {nm} ━━━━")
        out.append("📸 INSTAGRAM\n"
                   f" 1) Edit profile → Links → {_u('instagram', b, 'bio')}\n"
                   f" 2) '✅ जवाब' HIGHLIGHT: story (koi photo) → LINK sticker → {_u('instagram', b, 'highlight')} → "
                   "sticker text 'सही जवाब यहाँ 👆' → story daalo → story kholo → ❤️ Highlight → New → naam '✅ जवाब'\n"
                   " 3) Ek achhi reel → ⋮ → Pin to your profile")
        out.append("📘 FACEBOOK PAGE\n"
                   f" 1) Page → Edit → Add button → 'Learn more' → {_u('facebook', b, 'button')}\n"
                   f" 2) Intro → Website: {SITE}\n"
                   " 3) Ye post daalo → ⋯ → 'Pin post' / 'Feature':\n" + txt.replace("{S}", "facebook"))
        out.append("▶️ YOUTUBE\n"
                   f" 1) Studio → Customisation → Basic info → Links → title 'सही जवाब + कैलकुलेटर' → {_u('youtube', b, 'channel')}\n"
                   " 2) Channel → Create → Post (yahan link click hota hai):\n" + txt.replace("{S}", "youtube"))
        out.append("🧵 THREADS\n"
                   f" 1) Edit profile → Link → {_u('threads', b, 'bio')}\n"
                   " 2) Ye post daalo → ⋯ → Pin to profile:\n" + txt.replace("{S}", "threads"))
        out.append("")
    out.append("━━━━ SAB EK BAAR (brand nahi) ━━━━")
    out.append("✈️ TELEGRAM channel: bot ko likho 'welcome pin' → ✅ dabao → bot khud post + PIN karega.")
    out.append(f"💬 WHATSAPP channel: Channel info → Edit description → {_u('whatsapp', 'channel', 'description')}")
    out.append(f"💼 LINKEDIN page: Edit page → Buttons → 'Visit website' → {_u('linkedin', 'page', 'button', '/')}")
    out.append(f"🎬 DAILYMOTION: Channel → Edit → About/Website → {SITE}")
    out.append(f"❓ QUORA: Profile → Edit credentials/bio → {SITE}")
    out.append("📌 Pinterest + Reddit: pehle se juda.")
    out.append("\nKaam ho jaye to: 'ho gaya pin kit'")
    return "\n".join(out)


def on_text(tl, run=None):
    tl = re.sub(r"[.!?।]+$", "", (tl or "").strip().lower()).strip()
    try:                                                    # v3.4.29: 'sab features' - har feature ka asli haal
        from . import featureaudit
        if featureaudit.on_text(tl):
            return True
    except Exception as ex:
        from .log import log
        log(f"featureaudit: {ex}")
    if re.search(r"\blinked?\s?in\b|\blinkdin\b|\blinkden\b", tl) and re.search(r"kitn|gayi|gyi|gai\b|hui|huyi|post gayi", tl):
        tg.say(li_count_text())
        return True
    if re.fullmatch(r"(growth )?(graff|graf|grph|graph|grafh)( do| dikhao| bhejo)?", tl):
        from . import growth
        tg.say("📈 Graph bana raha hoon...")
        (run or (lambda f: f()))(growth.send_growth)
        return True
    m = re.fullmatch(r"pin ?kit(?: (\w+))?|pin wala text|bio link kit", tl)
    if m:
        from .sawalpost import brand_in
        b = brand_in(tl)
        tg.say(pin_kit(b))
        return True
    if (tl in ("comment wapas", "comment unhide", "unhide", "unhide comment", "chhupe comment", "hidden comment", "comment wapas lao")
            or (re.search(r"comment", tl) and re.search(r"hide|chhup|chup|hat (gaya|gya|ja)|hat ja", tl))):
        from . import growth
        tg.say("🔍 Pichhli 8 reel/post ke chhupe comment dekh raha hoon...")
        (run or (lambda f: f()))(lambda: tg.say(growth.unhide_text()))
        return True
    if tl in ("ho gaya pin kit", "pin kit ho gaya"):
        state.put("pin_kit_done", str(datetime.date.today()))
        try:
            from . import tasks
            tasks.mark_done("pin kit")
        except Exception:
            pass
        tg.say("✅ Shabaash - ab har platform par jawab ka raasta hamesha upar hai. Report mein 'profile/highlight/bio' "
                      "wale log alag dikhenge.")
        return True
    return None
