"""Pinterest: thumbnail ki image-pin + website link, har brand ke apne board par.
Trial access mein pins sandbox mein jaati hain (sirf aapko dikhti hain); Standard milte hi production."""
import base64
import json
import time
import requests
from .config import SECRETS, BRANDS, SITE
from .log import log

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


def _real_board(brand):
    """v2.1.3: LIVE ke baad purane sandbox board par pin nahi lagti (code 15). Production mein asli board banao."""
    c = _cfg()
    name = BRANDS[brand]["name"]
    for nm in (name, f"{name} | Sab Hisaab", f"{name} Tips"):
        try:
            hit = _req("POST", "/boards", c, data=json.dumps({"name": nm, "privacy": "PUBLIC",
                                                              "description": f"{name} - free hisaab, tips: sabhisaab.com"}))
            c.setdefault("boards", {})[brand] = hit["id"]
            c.setdefault("real_boards", {})[brand] = hit["id"]
            _save(c)
            return hit["id"]
        except Exception as e:
            if "exist" not in str(e).lower() and "duplicate" not in str(e).lower() and "409" not in str(e):
                raise
    raise RuntimeError("Pinterest: naya board nahi bana")


def can_pin_now(brand, link):
    """v2.3.0 (v11 se): Pinterest spam-suraksha - din mein max 15 pin, ek hi URL par din mein max 2."""
    import datetime
    from . import state
    today = str(datetime.date.today())
    st = state.get("pin_pace") or {}
    if st.get("date") != today:
        st = {"date": today, "total": 0, "urls": {}, "last_ts": {}}
    if st["total"] >= 15:
        return False, "Pinterest ki roz ki surakshit seema (15 pin) poori"
    clean_u = (link or "").split("?")[0].rstrip("/")
    if st["urls"].get(clean_u, 0) >= 2 and clean_u != SITE.rstrip("/"):
        return False, f"{clean_u} par aaj 2 pin ja chuke (spam-suraksha)"
    return True, "OK"


def record_pin_sent(brand, link):
    import datetime
    from . import state
    today = str(datetime.date.today())
    st = state.get("pin_pace") or {}
    if st.get("date") != today:
        st = {"date": today, "total": 0, "urls": {}, "last_ts": {}}
    st["total"] = st.get("total", 0) + 1
    clean_u = (link or "").split("?")[0].rstrip("/")
    st.setdefault("urls", {})[clean_u] = st["urls"].get(clean_u, 0) + 1
    st.setdefault("last_ts", {})[brand] = time.time()
    state.put("pin_pace", st)


def post_pin(brand, thumb_path, title, description, link, section=None):
    ok_pin, why_pin = can_pin_now(brand, link)
    if not ok_pin:
        raise RuntimeError(why_pin)
    c = _cfg()
    board = c.get("boards", {}).get(brand)
    if not board:
        raise RuntimeError("Pinterest board nahi mila")
    data = base64.b64encode(open(thumb_path, "rb").read()).decode()
    body = {"board_id": board, "title": title[:100], "description": description[:500], "link": link,
            "alt_text": title[:500], "media_source": {"source_type": "image_base64", "content_type": "image/jpeg",
                                                      "data": data}}
    if section:                                   # v2.4.0: board ke andar sahi section (apne aap sajna)
        try:
            sid = _section(board, section)
            if sid:
                body["board_section_id"] = sid
        except Exception as e:
            log(f"pin section: {e}")
    try:
        pin = _req("POST", "/pins", c, data=json.dumps(body))
    except RuntimeError as e:
        if '"code":15' not in str(e).replace(" ", "") or not c.get("live"):
            raise
        body["board_id"] = _real_board(brand)
        pin = _req("POST", "/pins", _cfg(), data=json.dumps(body))
    pid = pin.get("id", "")
    record_pin_sent(brand, link)
    from . import state as _st
    _st.put("pin_last_id", pid)
    return f"https://www.pinterest.com/pin/{pid}/" + (" (sandbox)" if c.get("env") == "sandbox" else "")


def env():
    return _cfg().get("env", "-")


def waiting():
    """v2.1.1: Standard LIVE nahi aur env production = post karne se 401 hi aayega (restore ke baad yahi hua).
    Tab pin chhodo, ❌ mat dikhao - '⏸ intezaar'."""
    c = _cfg()
    return not c.get("live") and c.get("env", "production") == "production"


# ---------------- v0.8: OAuth login (Standard access ke liye) ----------------
import urllib.parse
APP_ID = "1630338"        # v2.1.1: owner ke page URL se pakka (pehle 1630538 galat tha). Badalna: 'pinterest app id <id>'


def app_id():
    """v2.0.9: App ID owner ke page ke URL se (developers.pinterest.com/apps/<ID>/)."""
    return str(_cfg().get("app_id") or APP_ID)


def set_app_id(v):
    c = _cfg()
    c["app_id"] = v.strip()
    _save(c)
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
        {"client_id": app_id(), "redirect_uri": REDIRECT, "response_type": "code", "scope": SCOPES, "state": "sabhinet"})


def _token_call(data):
    c = _cfg()
    r = requests.post("https://api.pinterest.com/v5/oauth/token", timeout=30, auth=(app_id(), c["app_secret"]),
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
        cands = [x for x in boards if word in x.get("name", "").lower()]
        # v2.1.3: '<Brand> board' naam bot ne sandbox mein banaye the - asli board ho to wahi pehle
        cands.sort(key=lambda x: x.get("name", "").lower().endswith(" board"))
        if cands:
            mp[b] = cands[0]["id"]
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


# ---------------- v2.3.7 (owner: Pinterest se zyada traffic) - analytics + website page ka 'drip' pin ----------------
def analytics_summary(days=30):
    """Pinterest account: impressions, saves, pin click, website (outbound) click - pichhle N din."""
    import datetime
    if not connected():
        return "📌 Pinterest juda nahi."
    end = datetime.date.today()
    try:
        j = _req("GET", "/user_account/analytics", params={
            "start_date": str(end - datetime.timedelta(days=days)), "end_date": str(end),
            "metric_types": "IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK", "content_type": "ALL", "app_types": "ALL"})
        s = (j.get("all") or {}).get("summary_metrics") or {}
        return (f"📌 Pinterest ({days} din): {int(s.get('IMPRESSION', 0))} baar dikha | {int(s.get('SAVE', 0))} save | "
                f"{int(s.get('PIN_CLICK', 0))} pin-click | {int(s.get('OUTBOUND_CLICK', 0))} website-click")
    except Exception as e:
        return f"📌 Pinterest analytics: {str(e)[:150]} (naya account ho to 1-2 din der se data aata hai)"


DRIP_BRAND = (("pahad", "pahadi"), ("uttarakhand", "pahadi"), ("nali", "pahadi"), ("discount", "deals"), ("sale", "deals"),
              ("gst", "money"), ("emi", "money"), ("sip", "money"), ("loan", "money"), ("tax", "money"), ("fd", "money"),
              ("salary", "money"), ("percent", "deals"), ("bijli", "deals"))


def drip_pin():
    """Har ~90 min (08-22): ek website page/tool ka 1000x1500 pin (UTM link) - roz ki 15 ki seema ke andar, ek page 30 din
    mein ek baar. Pinterest ki spam-niti: alag image, alag title, seedha kaam ka page (koi bhatkaav nahi)."""
    import datetime
    import pathlib
    from . import state, siteknow, imagegen
    from .config import TMP
    if not connected() or not _cfg().get("live"):
        return "Pinterest live nahi"
    today = str(datetime.date.today())
    sent = state.get("pin_drip") or {}
    cut = str(datetime.date.today() - datetime.timedelta(days=30))
    sent = {k: v for k, v in sent.items() if v >= cut}
    pg = siteknow.pages() or {}
    cands = [(k, v) for k, v in pg.items() if v.get("in_sitemap") and v.get("title") and k not in sent and siteknow.is_content(k, v)
             and not k.startswith(("404", "privacy", "terms", "about", "contact", "thanks"))]
    if not cands:
        return "Saare page 30 din mein pin ho chuke"
    slug, info = sorted(cands)[sum(map(ord, today)) % len(cands)]
    low = (slug + " " + info.get("title", "")).lower()
    brand = next((b for w, b in DRIP_BRAND if w in low), "money")
    link = f"{SITE}/{slug.strip('/')}?utm_source=pinterest&utm_medium=social&utm_campaign={brand}_tool"
    ok, why = can_pin_now(brand, link)
    if not ok:
        return why
    title = info["title"][:90]
    desc = (info.get("desc") or title)[:350]
    lines = [x.strip() for x in desc.replace("|", ".").split(".") if 8 < len(x.strip()) < 70][:3] or ["Free calculator", "Hindi mein aasaan", "Turant jawab"]
    out = pathlib.Path(TMP) / f"drip_{slug.strip('/').replace('/', '_')}.jpg"
    imagegen.make_infographic_pin(brand, title, lines, out)
    style = ab_style()
    r = post_pin(brand, out, ab_title(style, title), desc + "\n\nFree tool: " + SITE + "/", link,
                 section="pahadi" if brand == "pahadi" else "tool")
    from . import state as _st2
    ab_record(_st2.get("pin_last_id"), style)
    sent[slug] = today
    state.put("pin_drip", sent)
    try:
        out.unlink(missing_ok=True)
    except Exception:
        pass
    return f"📌 drip pin: /{slug.strip('/')} -> {r}"



# ---------------- v2.4.0: board sections apne aap + A/B title test (asli pin analytics se seekhna) ----------------
SECTIONS = {"tool": "Free Calculators & Tools", "quiz": "Sawal-Paheli (Quiz)", "pahadi": "Pahadi GK & Boli"}


def _section(board_id, key):
    from . import state as _st
    name = SECTIONS.get(key, key)
    cache = _st.get("pin_sections") or {}
    ck = f"{board_id}:{name}"
    if cache.get(ck):
        return cache[ck]
    j = _req("GET", f"/boards/{board_id}/sections", params={"page_size": 50})
    sid = next((x["id"] for x in (j.get("items") or []) if x.get("name") == name), None)
    if not sid:
        sid = _req("POST", f"/boards/{board_id}/sections", data=json.dumps({"name": name})).get("id")
    if sid:
        cache[ck] = sid
        _st.put("pin_sections", cache)
    return sid


def ab_style():
    """A = page ka title, B = sawal/fayda wala hook. Jo jeeta (website-click/impression) usko 70%."""
    import random
    from . import state as _st
    sc = _st.get("pin_ab_score") or {}
    a, b = sc.get("A") or {}, sc.get("B") or {}
    ra = (a.get("click", 0) + 1) / (a.get("imp", 0) + 50)
    rb = (b.get("click", 0) + 1) / (b.get("imp", 0) + 50)
    best = "A" if ra >= rb else "B"
    return best if random.random() < 0.7 else ("B" if best == "A" else "A")


def ab_title(style, title):
    if style == "B":
        hook = random_hook()
        return f"{hook} {title}"[:100]
    return title[:100]


def random_hook():
    import random
    return random.choice(["10 second mein:", "Free mein jaano:", "Galti mat karna -", "Asli hisaab:", "Aasaan tareeka:"])


def ab_record(pid, style):
    import time as _t
    from . import state as _st
    if pid:
        _st.update("pin_ab", lambda L: ((L or []) + [{"id": pid, "s": style, "t": _t.time(), "done": False}])[-300:], [])


def ab_learn():
    """Hafte mein ek baar: 3+ din purane pin ka asli analytics -> A/B score."""
    import datetime
    import time as _t
    from . import state as _st
    lst = _st.get("pin_ab") or []
    sc = _st.get("pin_ab_score") or {}
    end = datetime.date.today()
    n = 0
    for it in lst:
        if it.get("done") or _t.time() - it["t"] < 3 * 86400:
            continue
        try:
            j = _req("GET", f"/pins/{it['id']}/analytics", params={"start_date": str(end - datetime.timedelta(days=30)),
                                                                    "end_date": str(end), "metric_types": "IMPRESSION,OUTBOUND_CLICK"})
            s_ = (j.get("all") or {}).get("summary_metrics") or {}
            d = sc.setdefault(it["s"], {"imp": 0, "click": 0})
            d["imp"] += int(s_.get("IMPRESSION", 0))
            d["click"] += int(s_.get("OUTBOUND_CLICK", 0))
            it["done"] = True
            n += 1
        except Exception as e:
            log(f"pin ab {it['id']}: {e}")
    _st.put("pin_ab", lst)
    _st.put("pin_ab_score", sc)
    return f"📌 A/B: {n} pin jaanche | A {sc.get('A', {})} | B {sc.get('B', {})}"
