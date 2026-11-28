"""SEO + trend: YouTube search suggestions (free, bina key) se log abhi kya khoj rahe hain."""
import datetime
import json
import re
import requests
from . import state
from .log import log

SEEDS = {"sunonatak": ["emi", "loan", "credit card", "paise kaise bachaye", "kahani paise"],
         "money": ["sip", "fd vs", "ppf", "tax kaise bachaye", "mutual fund"],
         "deals": ["discount", "bijli bill", "online shopping", "cashback", "sale"],
         "pahadi": ["uttarakhand", "nali", "bigha", "pahadi", "uttarakhand yojana"]}


def suggest(q, lang="hi"):
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search", timeout=15,
                         params={"client": "firefox", "ds": "yt", "hl": lang, "q": q})
        return [s for s in json.loads(r.text)[1] if s.lower() != q.lower()][:8]
    except Exception as e:
        log(f"seo suggest fail {q}: {e}")
        return []


# v2.2.1 (3 Nov 2026): trend/keyword mein bahar ka kachra (gaana, SSC GD, khabar) title tak pahunch gaya tha
# ("Nalia Tale Balia Jhuri Sambalpuri Song: 3 galtiyan..." Pahadi par, "discount ssc gd 2026" Deals par). Ab do jaanch.
BAD = re.compile(r"news|live|khabar|ख़बर|खबर|taza|ताजा|samachar|समाचार|breaking|aaj ki|आज की|death|maut|hatya|murder|"
                 r"election|chunav|चुनाव|bjp|congress|modi|rahul|party|hindu|muslim|masjid|mandir|vivad|ipl|score|"
                 r"movie|film|actor|actress|song|gana|गाना|geet|dj|remix|status|shayari|sambalpuri|bhojpuri|haryanvi|"
                 r"punjabi|lyrics|video song|reel song|viral video|mms|leak|sexy|girl|bhabhi|lottery|satta|betting|"
                 r"ssc|gd|bharti|admit card|result|answer key|cutoff|recruitment|vacancy|syllabus", re.I)
COMMON = set("kaise kya hai ka ki ke ko me mein se par kitna kitni kab kahan best hindi in how to kare karen karein kar "
             "kare bachaye bachayen calculator formula niyam rules fayde fayda nuksan nuksaan matlab meaning kya hota "
             "online free 2025 2026 2027 aur ya vs better behtar tarika tips guide new naya rate list ke liye "
             "conversion convert kam kaun kaunsa konsa today sabse kitne ek karna jankari puri poori full form chart table "
             "banaye nikale nikalna calculate liye wala wali bataye upay tarike trick saal mahina din lakh crore rupees rs "
             "kamaye kamai hota hoti hote mai main kya hain hindi".split())
BRAND_EXTRA = {
    "sunonatak": ["emi", "loan", "credit", "card", "paise", "paisa", "bachat", "kahani", "byaj", "udhaar", "kharcha", "budget", "fraud", "otp"],
    "money": ["mutual", "fund", "fd", "sip", "ppf", "nps", "tax", "itr", "byaj", "interest", "return", "invest", "share", "gold", "bank"],
    "deals": ["discount", "offer", "sale", "cashback", "coupon", "price", "bill", "bijli", "shopping", "amazon", "flipkart",
              "emi", "gst", "bachat", "card", "festival", "diwali", "unit"],
    "pahadi": ["uttarakhand", "pahadi", "pahad", "garhwal", "garhwali", "kumaon", "kumaoni", "nali", "bigha", "zameen",
               "jameen", "kheti", "yojana", "gk", "dehradun", "almora", "nainital", "tehri", "pithoragarh", "chamoli", "naap"],
}


def relevant(x, brand, strict=True):
    """Suggestion brand ke kaam ka? Kachra-shabd nahi + (strict: seed ke alawa har shabd brand/aam shabd ho)."""
    if BAD.search(x) or len(x.split()) < 2:
        return False
    from .topics import BRAND_WORDS
    words = set(BRAND_WORDS.get(brand, [])) | set(BRAND_EXTRA.get(brand, []))
    for sd in SEEDS.get(brand, []):
        words |= set(sd.split())
    toks = re.findall(r"[a-z0-9]+", x.lower())
    if not strict:
        return any(t in words for t in toks)
    return all(t in words or t in COMMON for t in toks) and any(t in words for t in toks)


def trends(brand):
    """Roz ek baar: brand ke shabdon par log kya khoj rahe hain."""
    today = str(datetime.date.today())
    c = state.get("trends") or {}
    if c.get("date") == today and brand in c:
        return c[brand]
    out = []
    for s in SEEDS.get(brand, []):
        out += suggest(s)
    out = [x for x in dict.fromkeys(out) if relevant(x, brand)][:25]       # v2.2.1: sirf brand ke kaam ke
    c = c if c.get("date") == today else {"date": today}
    c[brand] = out
    state.put("trends", c)
    return out


def keywords_for(topic, brand=None):
    """v2.2.1: sirf wahi suggestion jo topic se mile (pehle 'nali' par gaane ka naam title mein aa gaya tha)."""
    tw = {w for w in re.findall(r"[a-z0-9\u0900-\u097f]+", (topic or "").lower()) if len(w) > 2}
    out = []
    for x in suggest(topic):
        xw = set(re.findall(r"[a-z0-9\u0900-\u097f]+", x.lower()))
        if BAD.search(x) or not (xw & tw):
            continue
        if brand and not relevant(x, brand, strict=False):
            continue
        out.append(x)
    return out[:6]
