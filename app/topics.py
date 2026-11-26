"""Topic chunna: sabhisaab.com ke sitemap se brand ke hisaab se page, jo pichhle 45 din mein na aaya ho."""
import datetime
import json
import random
import re
import requests
from . import state
from .config import DATA, SITE

CACHE = DATA / "sitemap.json"
BRAND_WORDS = {
    "pahadi": ["nali", "naali", "mutthi", "bigha", "zameen", "jameen", "land", "uttarakhand", "pahadi", "kheti",
               "acre", "hectare", "area"],
    "money": ["sip", "fd", "rd", "ppf", "nps", "tax", "interest", "byaj", "compound", "return", "invest", "salary",
              "gratuity", "pf", "epf", "retire", "inflation", "loan", "emi"],
    "deals": ["discount", "gst", "offer", "sale", "percent", "percentage", "profit", "loss", "price", "bachat",
              "saving", "unit", "electricity", "bijli"],
}
EXTRA_TOPICS = {
    "sunonatak": ["0% EMI ka asli kharcha", "credit card ka minimum due jaal", "dost ko udhaar aur likhit hisaab",
                  "shaadi ka kharcha aur loan", "naya phone EMI par ya cash", "bachat ki chhoti aadat ka bada asar",
                  "insurance na lene ka nuksaan", "online fraud OTP wala",
                  "10 second math trick: pratishat nikalna", "dimaag ghumane wala hisaab paheli", "roz ke shabd jinka asli naam kam log jaante"],
    "money": ["SIP vs FD kaun behtar", "PPF ke fayde", "emergency fund kitna", "compound interest ka jaadu",
              "home loan prepayment", "inflation se paisa kaise ghatta hai"],
    "deals": ["sale mein asli discount kaise jaanchein", "cashback vs discount", "bijli bill kaise kam karein",
              "GST bill kaise padhein", "online shopping mein chhupi fees"],
    "pahadi": ["nali aur mutthi ka hisaab", "bigha kitna bada hota hai", "pahadi kheti ke liye sarkari yojana",
               "zameen kharidne se pehle kya jaanchein", "uttarakhand mein zameen naap ki ikaiyan",
               "Uttarakhand GK: kam log jaante hain", "Uttarakhand ke 5 anokhe tathya", "pahadi shabd jinka asli matlab kam log jaante",
               "Uttarakhand ke lok parv aur unka mahatva", "pahad ke purane naap-tol aur unka hisaab",
               "pahad mein ghar banane ka kharcha (naksha, mitti, patthar)", "pahadi fasal ka hisaab: mandua, jhangora, rajma",
               "Uttarakhand ki sarkari naukri ki taiyari: GK ke 5 sawal", "pahad se palayan: gaon ki zameen ka kya karein"],
}


def _sitemap():
    today = str(datetime.date.today())
    try:
        c = json.loads(CACHE.read_text())
        if c.get("date") == today and c.get("urls"):
            return c["urls"]
    except Exception:
        pass
    urls = []
    try:
        x = requests.get(f"{SITE}/sitemap.xml", timeout=30).text
        urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", x)
        subs = [u for u in urls if u.endswith(".xml")]
        for s in subs[:10]:
            urls += re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", requests.get(s, timeout=30).text)
        urls = [u for u in urls if not u.endswith(".xml")]
        CACHE.write_text(json.dumps({"date": today, "urls": urls}))
    except Exception:
        try:
            urls = json.loads(CACHE.read_text()).get("urls", [])
        except Exception:
            urls = []
    return urls


def _brand_of(url):
    u = url.lower()
    for b, words in BRAND_WORDS.items():
        if any(w in u for w in words):
            return b
    return None


QUIZ_TOPICS = {   # v2.3.3: dimag + pyaar combo ke vishay (website page nahi); 60 din mein dohraav nahi
    "money": ["shaadi ka budget kaise banaye", "honeymoon ka kharcha aur bachat", "pehli salary ka 50-30-20 plan", "EMI ya cash: couple ki bahas",
              "gold ya FD: pati-patni ka faisla", "SIP kab shuru karein", "credit card ki minimum due ka jaal", "home loan ka asli byaj",
              "mehngai se paisa kaise ghatta hai", "rule of 72: paisa kab dugna", "emergency fund kitna ho", "PPF vs FD", "chhoti bachat badi daulat",
              "salary badhi par bachat kyun nahi", "loan app ka chhupa kharcha", "anniversary gift ka budget", "shaadi ka gold aur making charge"],
    "deals": ["sale mein 50% + 20% ka asli discount", "buy 1 get 1 vs 40% off", "gift par cashback ka asli fayda", "no-cost EMI ka sach",
              "date night ka bill split", "online vs dukaan ka daam", "festival sale ki chaal", "MRP aur discount ka ganit",
              "coupon + bank offer ka jod", "subscription ka saalana hisaab", "bijli bill kam karne ka ganit", "petrol vs EV ka kharcha",
              "wedding shopping ki bachat", "flash sale ka sach", "exchange offer ka asli daam"],
    "sunonatak": ["dil vs dimag paheli", "rishton ki paheli (khoon ka rishta)", "ghadi ki paheli", "umar ki paheli", "jasoosi paheli: kaun jhooth bol raha",
                  "pyaar ki paheli: kitne gulab", "shabd paheli: ulta shabd", "sach ya jhooth: 3 baatein", "tarazu ki paheli", "railway platform paheli",
                  "calendar ki paheli", "ganit ka jaadu: soch kar number", "aankhon ka dhokha (optical) paheli", "sikkon ki paheli", "seedhi-saanp ganit",
                  "ulte-pulte shabd: aasaan dikhe par ghumaavdaar arth", "purane zamaane ke anokhe shabd", "roz ki cheezon ke shuddh Hindi naam",
                  "muhavre ka asli matlab (couple ki bahas)", "sudoku jaisi chhoti tark paheli", "ankon ka ulta-pulta khel"],
    "pahadi": ["pahadi shaadi ki rasmein", "pahadi khana: bhatt, gahat, mandua", "pahadi lok geet aur nritya", "pahad ke mele aur thaul",
               "pahadi couple ki boli (Garhwali-Kumaoni shabd)", "pahad ke purane gaon ke ghar", "char dham ki yatra GK", "pahad ki nadiyan aur prayag",
               "pahad mein purane zamaane mein isko kya kehte the", "pahadi ulte-pulte shabd jo shehar wale galat samajhte",
               "pahadi gehne aur kapdon ke purane naam", "pahadi baaje aur lok parv ke naam"],
}


def next_topic(brand, rnd=None):
    rnd = rnd or random.Random()
    used = state.get("used_topics", {})
    today = str(datetime.date.today())
    plan = (state.get("plan") or {}).get(today, {}).get(brand)         # 1) aapka manzoor kiya hafte ka plan
    if plan and used.get(f"plan:{today}:{brand}", "0") < today:
        return {"key": f"plan:{today}:{brand}", "topic": plan, "page": "/", "kind": "plan"}
    mine_extra = (state.get("extra_topics") or {}).get(brand, [])   # 2) aapke bataye topic
    fresh_extra = [t for t in mine_extra if used.get(t, "0") < str(datetime.date.today() - datetime.timedelta(days=60))]
    if fresh_extra:
        pg = (state.get("topic_pages") or {}).get(fresh_extra[0], "/")      # v2.0.2: GSC query ka apna page
        return {"key": fresh_extra[0], "topic": fresh_extra[0], "page": pg, "kind": "owner" if pg == "/" else "page"}
    try:                            # v2.2.0: Pahadi GK / purane naam / pahadi shabd wale din (180 din dohraav nahi)
        from . import weekplan
        dt_ = weekplan.day_topic(brand, used)
        if dt_:
            return {"key": dt_, "topic": dt_, "page": "/", "kind": "idea"}
    except Exception:
        pass
    if state.get("quiz_topics_only", True):   # v2.3.3 (owner): purane website-page wale vishay band - sirf sawal wale vishay
        cut60 = str(datetime.date.today() - datetime.timedelta(days=60))
        pool = [t for t in QUIZ_TOPICS.get(brand, []) if used.get("q:" + t, "0") < cut60]
        if brand == "pahadi":
            from .weekplan import PAHADI_DAY_TOPICS
            pool += [t for v in PAHADI_DAY_TOPICS.values() for t in v if used.get("q:" + t, "0") < cut60]
        if pool:
            t = rnd.choice(pool)
            return {"key": "q:" + t, "topic": t, "page": "/", "kind": "idea"}
    cutoff = str(datetime.date.today() - datetime.timedelta(days=45))
    try:                            # v2.0: Google mein index nahi hue page pehle (bahar ka link = Google jaldi aata hai)
        from . import siteknow
        pend = [SITE + "/" + k for k in siteknow.not_indexed()]
        cut14 = str(datetime.date.today() - datetime.timedelta(days=14))
        pend = [u for u in pend if (brand == "sunonatak" or _brand_of(u) in (brand, None)) and used.get(u, "0") < cut14]
        if pend and rnd.random() < 0.35:
            u = rnd.choice(pend)
            t = (siteknow.pages().get(u.replace(SITE + "/", ""), {}) or {}).get("title", "")
            return {"key": u, "topic": (t.split("|")[0].strip() or u.replace(SITE + "/", "").replace("-", " ")),
                    "page": u.replace(SITE, ""), "kind": "page"}
    except Exception:
        pass
    pages = [u for u in _sitemap() if u.rstrip("/") != SITE]
    mine = [u for u in pages if _brand_of(u) == brand] if brand != "sunonatak" else pages
    fresh = [u for u in mine if used.get(u, "0") < cutoff]
    extra = [t for t in EXTRA_TOPICS.get(brand, []) if used.get(t, "0") < cutoff]
    try:
        from . import seo
        trend = [t for t in seo.trends(brand) if used.get(t, "0") < cutoff][:8]
    except Exception:
        trend = []
    from . import learn             # 3) jo type zyada dekha gaya, uska wazan zyada
    pool = ([("page", u) for u in fresh] + [("idea", t) for t in extra] + [("trend", t) for t in trend])
    if not pool:
        pool = [("page", u) for u in mine] + [("idea", t) for t in EXTRA_TOPICS.get(brand, [])]
    if not pool:
        pool = [("idea", "paise bachane ki aasaan aadat")]
    wts = [learn.weight("kind", k) * (2 if k == "trend" else 1) for k, _ in pool]
    kind, val = rnd.choices(pool, weights=wts, k=1)[0]
    page = val.replace(SITE, "") if kind == "page" else "/"
    slug = page.strip("/").replace("-", " ") if kind == "page" else val
    if kind == "page":              # v2.0: slug ki jagah page ka asli title (behtar script)
        try:
            from . import siteknow
            t = (siteknow.pages().get(page.strip("/"), {}) or {}).get("title", "")
            slug = t.split("|")[0].strip() or slug
        except Exception:
            pass
    return {"key": val, "topic": slug or "sab hisaab", "page": page or "/", "kind": kind}


def mark_used(key):
    state.update("used_topics", lambda d: {**(d or {}), key: str(datetime.date.today())}, {})
