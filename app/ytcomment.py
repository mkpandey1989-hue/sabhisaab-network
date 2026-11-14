"""v2.5.7: YouTube COMMENT likhne ka alag login (scope youtube.force-ssl). Wajah: TV/device login (upload wala) Google se comment likhne
ki ijaazat nahi deta -> reply/top-comment 403 (state yt_reply_noscope / yt_comment_noscope). Upload wala token KABHI nahi badalta;
ye alag file (yc_<brand>.json) hai aur sirf comment likhne mein kaam aati hai. Wahi 'Desktop app' client jo /analytics mein hai.
Har brand ek baar: 'yt comment login' -> link -> us channel ka account chunein -> Allow -> browser ka address bot ko bhejein."""
import json
import time
import urllib.parse

import requests

from .config import SECRETS, BRANDS
from .log import log

SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
REDIRECT = "http://localhost"


def _client():
    from . import analytics
    return analytics._client()


def tpath(brand):
    return SECRETS / f"yc_{brand}.json"


def has(brand):
    return tpath(brand).exists()


def link(brand):
    cid, _ = _client()
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
        {"client_id": cid, "redirect_uri": REDIRECT, "response_type": "code", "scope": SCOPE,
         "access_type": "offline", "prompt": "consent select_account", "state": f"ytc:{brand}"})


def parse(url):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url.strip()).query)
    st = q.get("state", [""])[0]
    return q.get("code", [""])[0], (st.split(":", 1)[1] if st.startswith("ytc:") else "")


def is_comment_paste(text):
    t = urllib.parse.unquote(text or "")
    return "code=" in t and "state=ytc:" in t


def exchange(url):
    """-> (brand, channel_title). Channel brand se match na ho to kuch nahi likhta."""
    code, brand = parse(url)
    if brand not in BRANDS or not code:
        raise RuntimeError("Address mein brand/code nahi mila - 'yt comment login' se naya link lein (code 10 min chalta hai)")
    cid, sec = _client()
    j = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "code": code, "client_id": cid, "client_secret": sec, "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).json()
    if "refresh_token" not in j:
        raise RuntimeError(f"Google ne login nahi diya: {j.get('error_description') or j.get('error')}")
    if SCOPE not in (j.get("scope") or ""):
        raise RuntimeError("Google ne comment ki ijaazat nahi di (allow ke waqt saari ijaazat tick karein)")
    ch = requests.get("https://www.googleapis.com/youtube/v3/channels", timeout=30, params={"part": "snippet", "mine": "true"},
                      headers={"Authorization": f"Bearer {j['access_token']}"}).json().get("items") or []
    if not ch:
        raise RuntimeError("Is account par YouTube channel nahi mila - brand wale channel ka account chunein")
    title = ch[0]["snippet"]["title"]
    norm = lambda s: "".join(c for c in s.lower() if c.isalnum())
    if norm(BRANDS[brand]["name"]) not in norm(title):
        raise RuntimeError(f"Ye '{title}' channel {BRANDS[brand]['name']} se match nahi hua - kuch nahi badla")
    j["expires_at"] = time.time() + int(j.get("expires_in", 3600))
    j["channel_title"] = title
    tpath(brand).write_text(json.dumps(j))
    tpath(brand).chmod(0o600)
    return brand, title


def token(brand):
    t = json.loads(tpath(brand).read_text())
    if t.get("expires_at", 0) > time.time() + 120:
        return t["access_token"]
    cid, sec = _client()
    j = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": cid, "client_secret": sec, "refresh_token": t["refresh_token"], "grant_type": "refresh_token"}).json()
    if "access_token" not in j:
        raise RuntimeError(f"{brand}: comment login dobara chahiye ({j.get('error')}) - 'yt comment login'")
    t["access_token"], t["expires_at"] = j["access_token"], time.time() + int(j.get("expires_in", 3600))
    tpath(brand).write_text(json.dumps(t))
    return t["access_token"]


def missing():
    """Un brand ki list jinke paas YouTube login hai par comment-login nahi."""
    from . import youtube
    return [b for b in BRANDS if youtube.has_login(b) and not has(b)]
