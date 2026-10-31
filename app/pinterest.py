"""Pinterest: thumbnail ki image-pin + website link, har brand ke apne board par.
Trial access mein pins sandbox mein jaati hain (sirf aapko dikhti hain); Standard milte hi production."""
import base64
import json
import time
import requests
from .config import SECRETS, BRANDS, SITE

STORE = SECRETS / "pinterest.json"
BASES = {"production": "https://api.pinterest.com/v5", "sandbox": "https://api-sandbox.pinterest.com/v5"}
BOARD_WORDS = {"sunonatak": "suno natak", "money": "sab hisaab money", "deals": "labh lo deals",
               "pahadi": "pahadi hisaab"}


def _cfg():
    try:
        return json.loads(STORE.read_text())
    except Exception:
        return {}


def _save(c):
    STORE.write_text(json.dumps(c))
    STORE.chmod(0o600)


def connected():
    return bool(_cfg().get("token"))


def _req(method, path, c=None, **kw):
    c = c or _cfg()
    if c.get("live") and c.get("oauth"):
        c = dict(c, token=c["oauth"]["access"])
    r = requests.request(method, BASES[c.get("env", "production")] + path, timeout=120,
                         headers={"Authorization": f"Bearer {c['token']}", "Content-Type": "application/json"}, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"Pinterest {r.status_code}: {r.text[:200]}")
    return r.json() if r.content else {}


def save_token(token):
    """Production aur sandbox dono aazmao; jo chale wahi. Boards dhoondho / sandbox mein bana do."""
    out = []
    for env in ("production", "sandbox"):
        c = {"token": token, "env": env, "saved": time.time()}
        try:
            me = _req("GET", "/user_account", c)
            c["user"] = me.get("username", "")
            boards = _req("GET", "/boards", c, params={"page_size": 100}).get("items", [])
            # production mein trial app pin nahi bana sakta: chhota test se pehchano
            c["boards"] = {}
            for b, word in BOARD_WORDS.items():
                hit = next((x for x in boards if word in x.get("name", "").lower()), None)
                if not hit and env == "sandbox":
                    hit = _req("POST", "/boards", c, data=json.dumps({"name": f"{BRANDS[b]['name']} board",
                                                                       "privacy": "PUBLIC"}))
                if hit:
                    c["boards"][b] = hit["id"]
            _save(c)
            out.append(f"✅ Pinterest juda ({env}) @{c['user']} | boards: " +
                       ", ".join(BRANDS[b]["name"] for b in c["boards"]))
            if env == "sandbox":
                out.append("ℹ️ Trial access: pins sirf aapko dikhengi (sandbox). Standard manzoori ke baad public.")
            return "\n".join(out)
        except Exception as e:
            out.append(f"{env}: {str(e)[:120]}")
    raise RuntimeError("Token kisi mein nahi chala: " + " | ".join(out))


def post_pin(brand, thumb_path, title, description, link):
    c = _cfg()
    board = c.get("boards", {}).get(brand)
    if not board:
        raise RuntimeError("Pinterest board nahi mila")
    data = base64.b64encode(open(thumb_path, "rb").read()).decode()
    pin = _req("POST", "/pins", c, data=json.dumps({
        "board_id": board, "title": title[:100], "description": description[:500], "link": link,
        "alt_text": title[:500], "media_source": {"source_type": "image_base64", "content_type": "image/jpeg",
                                                  "data": data}}))
    pid = pin.get("id", "")
    return f"https://www.pinterest.com/pin/{pid}/" + (" (sandbox)" if c.get("env") == "sandbox" else "")


def env():
    return _cfg().get("env", "-")


# ---------------- v0.8: OAuth login (Standard access ke liye) ----------------
import urllib.parse
APP_ID = "1630538"
REDIRECT = "https://sabhisaab.com/"
SCOPES = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"


def save_secret(secret):
    c = _cfg()
    c["app_secret"] = secret.strip()
    _save(c)


def has_secret():
    return bool(_cfg().get("app_secret"))


def oauth_link():
    return "https://www.pinterest.com/oauth/?" + urllib.parse.urlencode(
        {"client_id": APP_ID, "redirect_uri": REDIRECT, "response_type": "code", "scope": SCOPES, "state": "sabhinet"})


def _token_call(data):
    c = _cfg()
    r = requests.post("https://api.pinterest.com/v5/oauth/token", timeout=30, auth=(APP_ID, c["app_secret"]),
                      data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    j = r.json()
    if "access_token" not in j:
        raise RuntimeError(f"Pinterest login: {j.get('message', j)}")
    return j


def exchange(url_or_code):
    code = url_or_code
    if "code=" in url_or_code:
        code = urllib.parse.parse_qs(urllib.parse.urlparse(url_or_code.strip()).query).get("code", [""])[0]
    j = _token_call({"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT})
    c = _cfg()
    c["oauth"] = {"access": j["access_token"], "refresh": j.get("refresh_token", ""),
                  "exp": time.time() + int(j.get("expires_in", 2592000)),
                  "rexp": time.time() + int(j.get("refresh_token_expires_in", 31536000))}
    _save(c)
    me = requests.get(BASES["production"] + "/user_account", timeout=30,
                      headers={"Authorization": f"Bearer {j['access_token']}"}).json()
    return me.get("username", "?")


def refresh_oauth():
    c = _cfg()
    o = c.get("oauth")
    if not o or o["exp"] - time.time() > 5 * 86400:
        return None
    j = _token_call({"grant_type": "refresh_token", "refresh_token": o["refresh"], "scope": SCOPES})
    o.update(access=j["access_token"], exp=time.time() + int(j.get("expires_in", 2592000)))
    if j.get("refresh_token"):
        o["refresh"] = j["refresh_token"]
    _save(c)
    return "♻️ Pinterest login naya kiya"


def go_live():
    """Standard manzoori ke baad: OAuth token se production (public pins), boards dhoondh kar jodo."""
    c = _cfg()
    o = c.get("oauth")
    if not o:
        raise RuntimeError("Pehle /pinterest se login karein")
    c2 = {"token": o["access"], "env": "production"}
    boards = _req("GET", "/boards", c2, params={"page_size": 100}).get("items", [])
    mp = {}
    for b, word in BOARD_WORDS.items():
        hit = next((x for x in boards if word in x.get("name", "").lower()), None)
        if hit:
            mp[b] = hit["id"]
    c.update(token=o["access"], env="production", boards=mp, live=True)
    _save(c)
    return f"✅ Pinterest LIVE: public pins shuru. Boards: {', '.join(BRANDS[b]['name'] for b in mp)}"


def status():
    c = _cfg()
    return {"env": c.get("env", "-"), "oauth": bool(c.get("oauth")), "secret": bool(c.get("app_secret")),
            "live": bool(c.get("live"))}



def delete_pin(pid):
    _req("DELETE", f"/pins/{pid}")
    return True



def check_standard():
    """Roz: Standard manzoori mili? (production mein ek SECRET board par chhota test pin -> turant delete).
    Mili to apne aap LIVE. Returns message or None."""
    import base64
    c = _cfg()
    if c.get("live") or not c.get("oauth"):
        return None
    tok = {"token": c["oauth"]["access"], "env": "production"}
    try:
        boards = _req("GET", "/boards", tok, params={"page_size": 100}).get("items", [])
        bid = next((b["id"] for b in boards if b.get("name") == "sabhisaab-check"), None)
        if not bid:
            bid = _req("POST", "/boards", tok, json={"name": "sabhisaab-check", "privacy": "SECRET"})["id"]
        from PIL import Image
        import io
        buf = io.BytesIO()
        Image.new("RGB", (600, 900), (240, 240, 240)).save(buf, "PNG")
        pin = _req("POST", "/pins", tok, json={"board_id": bid, "title": "check", "media_source": {
            "source_type": "image_base64", "content_type": "image/png", "data": base64.b64encode(buf.getvalue()).decode()}})
        _req("DELETE", f"/pins/{pin['id']}", tok)
    except Exception as e:
        msg = str(e).lower()
        if "trial" in msg or "403" in msg or "not allowed" in msg or "access" in msg:
            return None                         # abhi manzoori nahi
        return f"Pinterest jaanch: {str(e)[:120]}"
    return "🎉 Pinterest Standard access MIL GAYA! " + go_live()
