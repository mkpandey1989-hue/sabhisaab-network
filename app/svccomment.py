"""v3.8.0: SIRF services video ke comment (owner 24 Nov 2026). Purani video ke comment ka system jaisa tha waisa.

  - Comment kisi bhi bhasha/spelling mein (Hinglish, Hindi, pahadi andaaz, galat spelling) -> samajh: kaam / rate sawal / tareef /
    bharosa-sawal / mana-kaam / gaali-spam / samajh nahi.
  - Pakka samajh = chhota, izzat wala PUBLIC jawab usi andaaz mein (Devanagari mein likha to Devanagari, Roman mein Roman),
    7-45 min baad (insaan jaisa). Instagram par link/DM nahi - "bio ke link par". FB/YouTube par saada pata.
  - Pakka na ho / bharosa-sawal / gaali / mana-kaam = KOI jawab nahi -> owner ko Telegram (sujhaya jawab + button).
  - Koi jhootha vaada nahi (guarantee, pakka selection, refund), rate sirf rate list se.
"""
import random
import re
import time

from . import state
from .config import BRANDS
from .log import log

DEV = re.compile(r"[ऀ-ॿ]")
SPAM = re.compile(r"(https?://|www\.|t\.me/|bit\.ly|whatsapp\.com/|earn \d+|paisa kamao|crypto signal|dm me|follow back|f4f|"
                  r"sexy|hot girls|loan approved|लोन पास)", re.I)
ABUSE = re.compile(r"\b(chutiya|chutiye|madarchod|mc\b|bc\b|bhosdi|bhenchod|gandu|harami|kutta|kutte|saala|saale|fraud log|chor log)\b|"
                   r"चूतिया|मादरचोद|भोसड़ी|हरामी|कुत्ते", re.I)
TRUST = re.compile(r"(fraud|fake|scam|dhokha|dhoka|asli hai|real hai|bharosa|bharose|bharosa kaise|thag|thagi|paisa doob|"
                   r"फ्रॉड|धोखा|असली है|भरोसा|ठग)", re.I)
PRAISE = re.compile(r"^(\W|nice|good|great|wah|waah|badhiya|bahut badhiya|super|awesome|mast|osm|👍|❤|🔥|🙏|very nice|"
                    r"अच्छा|बढ़िया|बहुत बढ़िया|वाह|शानदार|सुंदर|thanks|thank you|dhanyavaad|धन्यवाद|"
                    r"video|vdo|bhai|bro|ji|sir|hai|h|bahut|bohot|very|so|ekdam|👌|😍|💯|वीडियो|भाई|जी|है|बहुत)+$", re.I)   # v3.8.7: 'nice video bhai' = tareef
WANT = re.compile(r"(chahiye|chaiye|chahie|chaahiye|banwana|banvana|banwa|banana hai|bana do|bnana|bnwana|karwana|karvana|krwana|"
                  r"karna hai|krna hai|bharna|bharwana|help|madad|madat|kaise|kese|kaam|kam hai|need|want|chahta|chahti|"
                  r"nahi chal|nhi chal|nahi ho raha|nhi ho rha|kharab|problem|dikkat|samasya|atak|band ho|नहीं चल|खराब|दिक्कत|समस्या|"
                  r"kar doge|kar dogi|kar sakte|kr skte|hoga kya|ho jayega|ho jaega|चाहिए|चाहिये|बनवाना|बनाना|करवाना|भरना|मदद|काम)", re.I)
PRICE = re.compile(r"(kitne|kitna|kitni|rate|price|charge|fees|fee|paisa|paise|rupay|rupaye|₹|rs\.?|कितने|कितना|रेट|फीस|पैसे)", re.I)
NORM = [(r"\bresum\w*|\bcv\b|\bbiodata\b", " resume "), (r"\bfrom\b|\bfarm\b|\bform\w*\b|फॉर्म|फ़ॉर्म|फार्म", " form "),
        (r"\bitr\w*|income ?tax|इनकम टैक्स|आईटीआर", " itr "), (r"\bwebsit\w*|\bwebsite\b|\bsite\b|वेबसाइट", " website "),
        (r"\bscholar\w*|छात्रवृत्ति|स्कॉलरशिप", " scholarship "), (r"\bmobail\b|\bmobile\b|\bfone\b|\bphone\b|मोबाइल|फोन|फ़ोन", " mobile "),
        (r"\blaptop\b|\bcomputer\b|\bpc\b|कंप्यूटर|लैपटॉप", " computer "), (r"\bbil\b|\bbill\b|बिल", " bill "),
        (r"किसान", " kisan "), (r"पेंशन", " pension "), (r"नौकरी", " naukri "), (r"रिज़्यूमे|रिज्यूमे|बायोडाटा", " resume "),
        (r"प्रोजेक्ट", " project "), (r"लोगो", " logo "), (r"टाइपिंग", " typing ")]


def norm(text):
    t = " " + (text or "").lower() + " "
    for a, b in NORM:
        t = re.sub(a, b, t)
    return re.sub(r"\s+", " ", t)


def svc_media_ids():
    """Services video ke sab platform id (YT/IG/FB) - pipeline jobs se."""
    from . import pipeline
    ids = set()
    try:
        for j in pipeline.jobs().values():
            if j.get("style") == "services_ad" or str(j.get("topic_kind")) == "services":
                for v in (j.get("ids") or {}).values():
                    if v:
                        ids.add(str(v).rsplit("/", 1)[-1])
    except Exception as e:
        log(f"svccomment ids: {e}")
    for h in state.get("history") or []:
        if h.get("page") == "/services-list" and h.get("vid"):
            ids.add(str(h["vid"]))
    ids |= set(state.get("svc_media_ids") or [])
    return {i for i in ids if len(i) >= 6}


def is_svc(c):
    m = str(c.get("video") or c.get("media") or "")
    if not m:
        return False
    for i in svc_media_ids():
        if i == m or i in m or m.endswith("_" + i):
            return True
    return False


def understand(text):
    """-> dict(intent, item, conf). Rules pehle (bina AI, hamesha chalta). Pakka na ho to Gemini (ho to), warna owner."""
    from . import svc
    raw = (text or "").strip()
    n = norm(raw)
    if not raw:
        return {"intent": "unclear", "item": None, "conf": 0}
    if SPAM.search(raw):
        return {"intent": "spam", "item": None, "conf": .95}
    if ABUSE.search(raw):
        return {"intent": "abuse", "item": None, "conf": .95}
    if TRUST.search(raw):
        return {"intent": "trust", "item": None, "conf": .9}
    items, red = svc.classify(n)
    if red:
        return {"intent": "red", "item": None, "red": red, "conf": .85}
    if PRAISE.match(raw.lower().strip(" .!")):
        return {"intent": "praise", "item": None, "conf": .9}
    want, price_q = bool(WANT.search(raw) or WANT.search(n)), bool(PRICE.search(raw))
    if items and (want or price_q or len(raw.split()) <= 4):
        return {"intent": "kaam", "item": items[0]["id"], "conf": .9 if want or price_q else .8}
    if price_q:
        return {"intent": "price", "item": None, "conf": .8}
    if want:
        return {"intent": "kaam_any", "item": None, "conf": .65}
    try:                                                     # Gemini sirf jab rule pakka na ho
        from .brain import ask_gemini
        r = ask_gemini("Comment ek Indian service-ad video par hai (kaam: resume, form madad, ITR madad, mobile madad, website, bill app). "
                       "JSON do: {\"intent\": kaam|price|praise|trust|abuse|spam|other, \"kaam_words\": \"2-4 shabd\", \"conf\": 0-1}. "
                       f"Comment: {raw[:400]}", temperature=0.1)
        it = (svc.classify(norm(str(r.get("kaam_words", ""))))[0] or [None])[0]
        return {"intent": r.get("intent", "other"), "item": it["id"] if it else None, "conf": float(r.get("conf", 0)) * .9}
    except Exception as e:
        log(f"svccomment ai: {e}")
    return {"intent": "unclear", "item": None, "conf": 0}


def _fw(x):
    try:
        from .svcvideo import fix_words
        return fix_words(x)
    except Exception:
        return x


def reply_for(platform, u, text):
    """Usi andaaz mein chhota jawab. None = jawab mat do (owner ko)."""
    from . import svc
    dev = bool(DEV.search(text or ""))
    cta_r = "Bio ke link par apna kaam likhiye" if platform == "ig" else "sabhisaab.com/services-list par apna kaam likhiye"
    cta_d = "बायो के लिंक पर अपना काम लिखिए" if platform == "ig" else "sabhisaab.com/services-list पर अपना काम लिखिए"
    hin_r, hin_d = " - Hindi mein likhna chalega 🙏", " - हिंदी में लिखना चलेगा 🙏"
    if u["intent"] == "kaam" and u.get("item"):
        it = svc.rates()["by"][u["item"]]
        from .svcvideo import KAAM
        nm_d = KAAM.get(u["item"], (it["name"],))[0]
        p_ = f"₹{it['price']:,}"
        nm_r = re.split(r'[(+]|\s-\s', it['name'])[0].strip()
        madad = KAAM.get(u["item"], ("", ""))[1] in ("मदद", "मोबाइल-कंप्यूटर")
        nm_d = re.sub(r"\s*(में )?मदद$", "", nm_d).strip()
        nm_r = re.sub(r"(?i)\s*(mein|me)$", "", re.sub(r"(?i)\s*(madad|help)$", "", nm_r).strip())
        if madad:                                   # v3.8.7: madad wale kaam mein nateeja ka vaada nahi (jaise "paisa aa jayega") - sirf madad
            out = (f"जी, {nm_d} में मदद कर देंगे, {p_} से। पहले बात करके देखेंगे क्या हो सकता है। {cta_d}{hin_d}" if dev else
                   f"Ji, {nm_r} mein madad kar denge - {p_} se. Pehle baat karke dekhenge kya ho sakta hai. {cta_r}{hin_r}")
        else:
            out = (f"जी, {nm_d} हो जाएगा, {p_} से। {cta_d}{hin_d}" if dev else
                   f"Ji, ye kaam ho jayega - {nm_r} {p_} se. {cta_r}{hin_r}")
        return _fw(out)
    if u["intent"] in ("price", "kaam_any"):
        return _fw(f"जी, काम के हिसाब से रेट - ₹10 (Resume) से शुरू। पहले बात, फिर लिखित रेट। {cta_d}{hin_d}" if dev else
                f"Ji, rate kaam ke hisaab se - ₹10 (resume) se shuru. Pehle baat, phir likhit rate. {cta_r}{hin_r}")
    if u["intent"] == "praise":
        return ("धन्यवाद 🙏 कोई भी डिजिटल काम हो तो बताइए।" if dev else "Dhanyavaad 🙏 Koi bhi digital kaam ho to batayiye.")
    return None


STRONG = re.compile(r"(chahiye|chaiye|chahie|banwana|banvana|karwana|karvana|krwana|bharwana|bana do|bana doge|kar doge|kar sakte|"
                    r"kr skte|madad chahiye|help chahiye|चाहिए|बनवाना|करवाना|भरवाना|बना दो|कर दोगे)", re.I)


def sawal_kaam(c):
    """v3.9.4: SAWAL reel par bhi koi saaf kaam maange ('resume chahiye', 'form bharwana hai') -> services jaisa samjho.
    Quiz ka jawab ('C', 'सी', 'D🔥') kabhi nahi."""
    t = (c.get("text") or "").strip()
    if len(t) < 8 or not STRONG.search(t):
        return False
    u = understand(t)
    return u.get("intent") == "kaam" and bool(u.get("item")) and u.get("conf", 0) >= .85


def handle(platform, b, c, force=False):
    """growth._handle_comment se pehle: services video/post ka comment (ya force = sawal reel par saaf kaam) ho to yahan."""
    from . import tg
    if not force and not is_svc(c):
        return False
    txt = c.get("text") or ""
    u = understand(txt)
    rep = reply_for(platform, u, txt) if u.get("conf", 0) >= .75 else None
    _log({"pf": platform, "b": b, "id": c["id"], "text": txt[:300], "u": u, "auto": bool(rep), "who": c.get("author", "")[:40],
          "on": "sawal" if force else "services"})
    if rep and state.get("auto_reply", True):
        at = time.time() + random.randint(7 * 60, 45 * 60)
        state.update("reply_queue", lambda q: (q or []) + [{"at": at, "pf": platform, "b": b, "id": c.get("parent") or c["id"],
                                                            "text": rep[:600], "who": c.get("author", "")}], [])
        if u["intent"] == "kaam" and state.get("svc_comment_ping"):     # v3.9.4: default chup - '📥 Leads' mein dikhta hai
            tg.say(f"🛎 Services comment ({platform.upper()} {BRANDS[b]['name']}): \"{txt[:200]}\"\n→ samjha: {u.get('item')} · "
                   f"jawab {int((at - time.time()) / 60)} min mein: {rep[:200]}")
        return True
    why = {"trust": "bharose ka sawal (aap khud jawab dein)", "abuse": "gaali", "spam": "spam/link", "red": f"mana kaam: {u.get('red')}",
           "unclear": "samajh nahi aaya"}.get(u["intent"], f"pakka nahi ({u['intent']}, {u.get('conf', 0):.0%})")
    key = ("ig" if platform == "ig" else "fb" if platform == "fb" else "yt") + c["id"][-18:]
    sug = reply_for(platform, {**u, "intent": u["intent"] if u["intent"] in ("kaam", "price", "praise") else "kaam_any"}, txt)
    if u["intent"] in ("abuse", "spam"):
        sug = None
    if u["intent"] == "red":
        sug = ("माफ़ कीजिए, ये काम हम नहीं करते 🙏 फ़ॉर्म, रिज़्यूमे, वेबसाइट जैसा काम हो तो बताइए।" if DEV.search(txt) else
               "Maaf kijiye, ye kaam hum nahi karte 🙏 Form, resume, website jaisa koi kaam ho to batayiye.")
        if str(u.get("red", "")).startswith("Trading"):        # v3.9.1: signal maangne wale ko saaf jawab (aap bhejein)
            sug = ("जी, हम टिप/सिग्नल नहीं देते, न कमाई का वादा 🙏 आपके अपने नियम का टूल (अलर्ट, चार्ट, बैकटेस्ट) बना सकते हैं।" if DEV.search(txt)
                   else "Ji, hum tip/signal nahi dete, na kamai ka vaada 🙏 Aapke apne niyam ka tool (alert, chart, backtest) bana sakte hain.")
    if u["intent"] == "trust":
        sug = ("जी, पहले बात, फिर लिखित रेट, पहले डेमो फिर पूरा पैसा। पासवर्ड/OTP हम कभी नहीं माँगते 🙏" if DEV.search(txt) else
               "Ji, pehle baat, phir likhit rate; demo dekh kar baaki payment. Password/OTP hum kabhi nahi maangte 🙏")
    if sug:
        state.update("reply_drafts", lambda d, k=key, v={"brand": b, "parent": c.get("parent") or c["id"], "text": sug,
                                                         "ig": platform == "ig", "fb": platform == "fb", "at": time.time()}:
                     {**(d or {}), k: v}, {})
    kb = tg.inline([[("✅ Ye jawab bhejo", f"cr:{key}"), ("⏭ Chhodo", f"cx:{key}")]]) if sug else None
    tg.say(f"💬 Services comment - bot ne jawab NAHI diya ({why})\n{platform.upper()} {BRANDS[b]['name']} · {c.get('author', '')}:\n"
           f"\"{txt[:300]}\"" + (f"\n\nSujhaya jawab:\n{sug}" if sug else "\n(Jawab ki zaroorat nahi lagti)"), kb)
    return True


def _log(row):
    from . import svc
    try:
        svc._append("comments.jsonl", {"t": svc.now().isoformat(timespec="seconds"), **row})
    except Exception as e:
        log(f"svccomment log: {e}")
