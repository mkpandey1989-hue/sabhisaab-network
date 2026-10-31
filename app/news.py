"""Kaam ki khabar (Google News RSS, free): finance, tax, Uttarakhand, aur platform policy badlaav.
Sirf bharosemand khabar, source link ke saath, aapki manzoori se post."""
import re
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from .log import log

QUERIES = {"money": "RBI OR SEBI OR income tax OR EPFO OR SIP new rule", "deals": "GST rate OR electricity tariff OR sale offer India",
           "pahadi": "Uttarakhand yojana OR Uttarakhand government scheme", "sunonatak": "loan EMI fraud OR credit card rule"}
POLICY_Q = ("YouTube policy update OR YouTube monetization change OR Instagram reels policy OR Meta Graph API change "
            "OR Threads API OR Pinterest API change")


def fetch(q, n=8, days=2):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q + f" when:{days}d", "hl": "hi", "gl": "IN",
                                                                          "ceid": "IN:hi"})
    try:
        root = ET.fromstring(requests.get(url, timeout=20).content)
    except Exception as e:
        log(f"news fail {q}: {e}")
        return []
    out = []
    import email.utils
    import time as _t
    for it in root.iter("item"):
        try:          # sirf taaza khabar (7 din), purani nahi
            pd = email.utils.parsedate_to_datetime(it.findtext("pubDate") or "")
            if _t.time() - pd.timestamp() > 7 * 86400:
                continue
        except Exception:
            pass
        title = re.sub(r"\s+", " ", it.findtext("title") or "")
        out.append({"title": title[:200], "link": it.findtext("link") or "", "src": it.findtext("source") or ""})
        if len(out) >= n:
            break
    return out


def policy_news():
    return fetch(POLICY_Q, 10, days=7)
