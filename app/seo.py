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


def trends(brand):
    """Roz ek baar: brand ke shabdon par log kya khoj rahe hain."""
    today = str(datetime.date.today())
    c = state.get("trends") or {}
    if c.get("date") == today and brand in c:
        return c[brand]
    out = []
    for s in SEEDS.get(brand, []):
        out += suggest(s)
    bad = re.compile(r"news|live|khabar|ख़बर|खबर|taza|ताजा|samachar|समाचार|breaking|aaj ki|आज की|death|maut|hatya|murder|"
                     r"election|chunav|चुनाव|bjp|congress|modi|rahul|party|hindu|muslim|masjid|mandir|vivad|ipl|score|"
                     r"movie|film|actor|actress|song|gana|गाना|viral video|mms|leak|sexy|girl|bhabhi|lottery|satta|betting", re.I)
    out = [x for x in dict.fromkeys(out) if not bad.search(x) and len(x.split()) >= 2][:25]
    c = c if c.get("date") == today else {"date": today}
    c[brand] = out
    state.put("trends", c)
    return out


def keywords_for(topic):
    return suggest(topic)[:6]
