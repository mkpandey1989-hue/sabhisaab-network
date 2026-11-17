"""v3.4.8 (17 Nov 2026) - owner: "Dailymotion par bhi roz ki video; bot khud key maange, chat se hata de; link jitne ho sakein
(privacy niyam ke andar)".

DAILYMOTION (Partner account, Private API key - Studio → Settings → Account → API keys):
- Jodna: bot khud poochta hai ('dailymotion jodo' ya install ke baad ek baar) → owner key paste → bot turant chat se mitata →
  secret maangta → mitata → token jaanch → channel dhoondhta → ✅. Secret sirf VM par (secrets/dailymotion.json, 600).
- Roz: jo video YouTube par ja chuki (manzoor), unme se din mein max DM_MAX (default 2) Dailymotion par bhi - wahi file,
  title, description (sawal ka jawab-link + free calculator, utm_source=dailymotion), tags, category 'school',
  is_created_for_kids=false (Dailymotion ka zaroori khaana). Ek video ek baar (post-taala pipeline ka).
- Dailymotion ki galti main pipeline ko nahi rokti (YouTube/FB/IG waise hi) - '⏸/⚠️' line, din mein ek alert.
- 'Mat daalo' (reject) par Dailymotion copy bhi mitti hai.
Hukum: 'dailymotion jodo' | 'dailymotion haal' | 'dailymotion roz 3' | 'dailymotion band' / 'dailymotion chalu'.
Docs: developers.dailymotion.com (private API key: client_credentials; REST: partner.api.dailymotion.com/rest).
"""
import datetime
import json
import re
import time

import requests

from . import state, tg
from .config import SECRETS, SITE
from .log import log

STORE = SECRETS / "dailymotion.json"
TOKEN_URLS = ("https://oauth2.dailymotion.com/v2/token", "https://partner.api.dailymotion.com/oauth/v1/token")
SCOPES = ("manage_videos", "video.manage")
# v3.4.14 (17 Nov 12:32): Dailymotion ne naya API v2 (api.dailymotion.com/v2) laya - v2 token purane /rest/file/upload par
# 401 'invalid' deta tha (aaj ek bhi video nahi gayi). Ab pehle v2: token scope 'video.manage account.read' -> /files/upload_sessions
# -> file POST -> /profiles/{profile_id}/videos. v2 na chale tabhi purana tareeka (partner token + /rest).
V2 = "https://api.dailymotion.com/v2"
V2_TOKEN = "https://oauth2.dailymotion.com/v2/token"
V2_SCOPES = ("video.manage account.read", "video.manage")
LEGACY_TOKEN = "https://partner.api.dailymotion.com/oauth/v1/token"
API = "https://partner.api.dailymotion.com/rest"
PUBLIC = "https://api.dailymotion.com"
DM_MAX = 2
CATEGORY = "school"


# ---------------------------------------------------------------- store
def _cfg():
    try:
        return json.loads(STORE.read_text())
    except Exception:
        return {}


def _save(c):
    STORE.parent.mkdir(mode=0o700, exist_ok=True)
    STORE.write_text(json.dumps(c))
    STORE.chmod(0o600)


def ready():
    c = _cfg()
    return bool(c.get("key") and c.get("secret") and c.get("channel"))


def on():
    return ready() and state.get("dm_on") is not False


def per_day():
    try:
        return max(0, min(10, int(state.get("dm_max") or DM_MAX)))
    except Exception:
        return DM_MAX


# ---------------------------------------------------------------- auth
def token(force=False):
    c = _cfg()
    tk = state.get("dm_tok") or {}
    if not force and tk.get("t") and time.time() < float(tk.get("exp", 0)) - 120:
        return tk["t"]
    last = ""
    combos = [(c.get("token_url"), c.get("scope"))] if c.get("token_url") else []
    combos += [(u, s) for u in TOKEN_URLS for s in SCOPES]
    for url, scope in combos:
        try:
            r = requests.post(url, timeout=30, data={"grant_type": "client_credentials", "client_id": c.get("key", ""),
                                                     "client_secret": c.get("secret", ""), "scope": scope},
                              headers={"Content-Type": "application/x-www-form-urlencoded"})
            j = r.json() if r.content else {}
            if r.status_code == 200 and j.get("access_token"):
                if c.get("token_url") != url or c.get("scope") != scope:
                    c.update(token_url=url, scope=scope)
                    _save(c)
                state.put("dm_tok", {"t": j["access_token"], "exp": time.time() + int(j.get("expires_in", 1800))})
                return j["access_token"]
            last = f"{r.status_code} {str(j.get('error_description') or j.get('error') or r.text)[:120]}"
        except Exception as e:
            last = str(e)[:120]
    raise RuntimeError(f"Dailymotion login nahi hua ({last})")


def _h():
    return {"Authorization": f"Bearer {token()}"}


def _tok_req(url, scope):
    c = _cfg()
    r = requests.post(url, timeout=30, data={"grant_type": "client_credentials", "client_id": c.get("key", ""),
                                             "client_secret": c.get("secret", ""), "scope": scope},
                      headers={"Content-Type": "application/x-www-form-urlencoded"})
    j = r.json() if r.content else {}
    if r.status_code == 200 and j.get("access_token"):
        return j
    raise RuntimeError(f"{r.status_code} {str(j.get('error_description') or j.get('error') or r.text)[:120]}")


def token_v2(force=False):
    """API v2 ka token (video.manage + account.read). -> (token, scope)"""
    tk = state.get("dm_tok2") or {}
    if not force and tk.get("t") and time.time() < float(tk.get("exp", 0)) - 120:
        return tk["t"], tk.get("scope", "")
    last = ""
    for sc in V2_SCOPES:
        try:
            j = _tok_req(V2_TOKEN, sc)
            state.put("dm_tok2", {"t": j["access_token"], "exp": time.time() + int(j.get("expires_in", 1800)), "scope": sc})
            return j["access_token"], sc
        except Exception as e:
            last = str(e)
    raise RuntimeError(f"Dailymotion v2 login nahi hua ({last})")


def token_legacy():
    """Purane /rest ke liye partner token (manage_videos)."""
    tk = state.get("dm_tok1") or {}
    if tk.get("t") and time.time() < float(tk.get("exp", 0)) - 120:
        return tk["t"]
    j = _tok_req(LEGACY_TOKEN, "manage_videos")
    state.put("dm_tok1", {"t": j["access_token"], "exp": time.time() + int(j.get("expires_in", 1800))})
    return j["access_token"]


def profile_id():
    """v2 /me -> profiles[].profile_id (hamara 'sabhisaab'). Ek baar mil gaya to yaad."""
    c = _cfg()
    if c.get("profile_id"):
        return c["profile_id"]
    t, _ = token_v2()
    r = requests.get(f"{V2}/me", headers={"Authorization": f"Bearer {t}"}, timeout=30)
    j = r.json() if r.content else {}
    pr = j.get("profiles") or []
    want = (c.get("user") or "sabhisaab").lower()
    pick = next((p for p in pr if str(p.get("name", "")).lower() == want), pr[0] if pr else None)
    if (not pick or not pick.get("profile_id")) and c.get("channel"):
        # v3.4.15: key mein 'account read' nahi (owner ki key: sirf Manage videos) -> jude channel ka id (x...) hi profile id
        log(f"dm v2 /me: {r.status_code} - channel id {c['channel']} se koshish")
        return c["channel"]
    if not pick or not pick.get("profile_id"):
        raise RuntimeError(f"profile id nahi mila ({r.status_code} {str(j)[:120]}) - Dailymotion API key mein 'account read' "
                           "permission chahiye")
    c["profile_id"] = pick["profile_id"]
    _save(c)
    return c["profile_id"]


def _upload_v2(vpath, meta):
    t, _ = token_v2()
    H = {"Authorization": f"Bearer {t}"}
    r = requests.post(f"{V2}/files/upload_sessions", headers=H, timeout=60)
    j = r.json() if r.content else {}
    up = j.get("upload_url")
    if not up:
        raise RuntimeError(f"v2 upload session nahi bana: {r.status_code} {str(j)[:150]}")
    with open(vpath, "rb") as f:
        fr = requests.post(up, files={"file": (str(vpath).rsplit("/", 1)[-1], f, "video/mp4")}, timeout=1800)
    fj = fr.json() if fr.content else {}
    furl = fj.get("url") or fj.get("file_url") or (fj.get("source") or {}).get("file_url")
    if not furl:
        raise RuntimeError(f"v2 file upload fail: {fr.status_code} {str(fj)[:150]}")
    title = re.sub(r"\s*#\S+", "", meta.get("title", "")).strip()[:250] or "Sab Hisaab"
    body = {"title": title, "visibility": "public", "is_for_kids": False, "source": {"file_url": furl},
            "description": build_desc(meta)[:2900], "tags": [x for x in tags_of(meta).split(",") if x][:10],
            "language": "hi", "country": "IN"}
    pid = profile_id()
    cr = requests.post(f"{V2}/profiles/{pid}/videos", headers=H, json=body, timeout=120)
    cj = cr.json() if cr.content else {}
    if cr.status_code not in (200, 201) and cr.status_code == 422:      # koi vaikalpik khaana na chale to bina uske
        log(f"dm v2 create full: {str(cj)[:200]}")
        cr = requests.post(f"{V2}/profiles/{pid}/videos", headers=H, timeout=120,
                           json={k: body[k] for k in ("title", "visibility", "is_for_kids", "source")})
        cj = cr.json() if cr.content else {}
    vid = cj.get("id") or cj.get("video_id") or cj.get("xid")
    if cr.status_code not in (200, 201) or not vid:
        raise RuntimeError(f"v2 video nahi bani: {cr.status_code} {str(cj)[:180]}")
    c = _cfg()
    c["api"] = "v2"
    _save(c)
    return f"https://www.dailymotion.com/video/{vid}", vid


def find_channel(name_hint=None, tries=3):
    """v3.4.11: Dailymotion kabhi 'Connection reset' deta hai (17 Nov 09:51) - 3 baar koshish."""
    for i in range(max(1, tries)):
        cid, user = _find_channel_once(name_hint)
        if cid:
            return cid, user
        time.sleep(3 * (i + 1))
    return None, None


def _find_channel_once(name_hint=None):
    """Private key se jude channel ka id (xid) + username."""
    for url in (f"{API}/me?fields=id,username,screenname", ):
        try:
            j = requests.get(url, headers=_h(), timeout=30).json()
            if j.get("id"):
                return j["id"], j.get("username") or j.get("screenname") or ""
        except Exception as e:
            log(f"dm me: {e}")
    for nm in [name_hint, "sabhisaab"]:
        if not nm:
            continue
        try:
            j = requests.get(f"{PUBLIC}/user/{nm}?fields=id,username", timeout=30).json()
            if j.get("id"):
                return j["id"], j.get("username") or nm
        except Exception as e:
            log(f"dm user: {e}")
    return None, None


# ---------------------------------------------------------------- jodna (bot khud poochta hai)
def ask(rotate=False):
    state.put("awaiting", "dm_key")
    note = ("⚠️ Pehle: subah wala secret bot ne pehchana nahi tha aur wo chat-record (GitHub) mein khul gaya - isliye Dailymotion "
            "Studio → Settings → Account → API keys mein purani key DELETE karke nayi Private key banaiye (Manage videos ON).\n\n"
            "Phir Notepad se sirf nayi API key copy karke yahan paste kar dijiye (aur kuch nahi).\n" if rotate else
            "Laptop ke Notepad se sirf API key copy karke yahan paste kar dijiye (aur kuch nahi).\n")
    return tg.say("🎬 DAILYMOTION JODNA (1 minute, kuch type nahi karna)\n\n" + note +
                  "Bot use turant chat se mita dega, phir secret maangega.\n\n"
                  "(Key: Dailymotion Studio → Settings → Account → API keys. Abhi nahi karna ho to: 'dailymotion baad mein')")


def clean_secret(t):
    """v3.4.8b: Dailymotion secret mein < & \\ ' | ? , jaise nishaan hote hain (pehle sirf A-Z 0-9 maanta tha -> secret
    pehchana hi nahi, Gemini tak gaya). Ab: aage-peeche ki khaali jagah + beech ki line-break (Notepad copy) hatao; koi bhi
    akshar chalega, bas beech mein space na ho aur 8-300 lamba ho. -> saaf text ya '' """
    t = re.sub(r"[\r\n]+", "", (t or "").strip())
    if not (8 <= len(t) <= 300) or re.search(r"\s", t):
        return ""
    if re.search(r"[\u2190-\u2BFF\U0001F000-\U0001FFFF]", t):      # emoji/teer = button/baat, secret nahi
        return ""
    return t


def looks_secret(t):
    """bot.py: awaiting dm_* ke dauran ye message key/secret maana jaaye?"""
    return bool(clean_secret(t))


def intake(msg_text):
    """awaiting dm_key / dm_secret mein aaya text -> jawab (message bot.py mitata hai)."""
    aw = state.get("awaiting") or ""
    val = clean_secret(msg_text)
    if aw == "dm_key":
        if not val:
            return "❌ Ye API key jaisi nahi lagi. Notepad se sirf key (ek shabd) copy karke bhejiye."
        c = _cfg()
        c["key"] = val
        c.pop("secret", None)
        _save(c)
        state.put("awaiting", "dm_secret")
        return "🔐 API key mili (chat se mitayi). Ab API secret paste kariye - wo bhi turant mitega."
    if aw == "dm_secret":
        if not val:
            return "❌ Ye secret jaisa nahi laga. Notepad se sirf secret (ek shabd) copy karke bhejiye."
        c = _cfg()
        c["secret"] = val
        _save(c)
        state.put("awaiting", "")
        state.put("dm_tok", {})
        return connect_text()
    return None


def connect_text():
    try:
        token(force=True)
    except Exception as e:
        state.put("awaiting", "dm_key")
        return (f"❌ {e}\nKey/secret shayad galat copy hue. Dobara: pehle API key paste kariye (bot phir secret maangega).\n"
                "Dhyan: Studio mein key 'Private API Key' ho aur 'Manage videos' ke chaaron tick ON hon.")
    cid, user = find_channel()
    if not cid:
        return ("⚠️ Login ho gaya par channel nahi mila. Bot mein likhiye: 'dailymotion channel sabhisaab' "
                "(apne channel ka username).")
    c = _cfg()
    c.update(channel=cid, user=user)
    _save(c)
    state.put("dm_on", True)
    return (f"✅ Dailymotion juda: @{user} (channel {cid}). Key/secret VM par surakshit, chat se mitaye.\n"
            f"Ab roz YouTube par gayi video mein se {per_day()} Dailymotion par bhi jayengi (jawab + free calculator link ke saath, "
            "utm_source=dailymotion - report mein alag line).\n"
            "Hukum: 'dailymotion haal' | 'dailymotion roz 3' | 'dailymotion band'")


# ---------------------------------------------------------------- upload
def can_post_today():
    d = str(datetime.date.today())
    log_ = state.get("dm_log") or {}
    return int(log_.get(d, 0)) < per_day()


def _mark_posted():
    d = str(datetime.date.today())
    state.update("dm_log", lambda x: {k: v for k, v in {**(x or {}), d: int((x or {}).get(d, 0)) + 1}.items()
                                      if k >= str(datetime.date.today() - datetime.timedelta(days=40))}, {})


def build_desc(meta):
    """Description: jawab-link + calculator link (utm dailymotion) + tags. Wahi niyam jo baaki platform (audit.description)."""
    from . import audit
    try:
        d = audit.description(meta, "dailymotion", "video")
    except Exception as e:
        log(f"dm desc: {e}")
        page = meta.get("page") or "/"
        d = (f"{meta.get('title', '')}\n\n{meta.get('description', '')}\n\n"
             f"👉 Free calculator: {SITE}{page}?utm_source=dailymotion&utm_medium=video&utm_campaign={meta.get('brand', '')}")
    return d[:2900]


def tags_of(meta):
    from .config import BRANDS
    raw = " ".join([BRANDS.get(meta.get("brand"), {}).get("tags", ""), meta.get("tags", "") if isinstance(meta.get("tags"), str) else
                    " ".join(meta.get("tags") or [])])
    out = []
    for t in re.findall(r"#?([\wऀ-ॿ]{2,40})", raw):
        if t.lower() not in [x.lower() for x in out] and t.lower() not in ("shorts", "short"):
            out.append(t)
    return ",".join((out + ["SabHisaab", "Hindi"])[:10])


def upload(vpath, meta):
    """-> (video_url, xid). v3.4.14: pehle naya API v2; na chale to purana /rest (partner token)."""
    try:
        u, x = _upload_v2(vpath, meta)
        _mark_posted()
        return u, x
    except Exception as e2:
        log(f"dm v2: {e2}")
        err2 = str(e2)
    try:
        return _upload_legacy(vpath, meta)
    except Exception as e1:
        raise RuntimeError(f"naya API: {err2[:160]} | purana: {str(e1)[:120]}")


def _hl():
    return {"Authorization": f"Bearer {token_legacy()}"}


def _upload_legacy(vpath, meta):
    c = _cfg()
    j = requests.get(f"{API}/file/upload", headers=_hl(), timeout=60).json()
    up = j.get("upload_url")
    if not up:
        raise RuntimeError(f"upload URL nahi mila: {str(j)[:150]}")
    with open(vpath, "rb") as f:
        r = requests.post(up, files={"file": (str(vpath).rsplit("/", 1)[-1], f, "video/mp4")}, timeout=1800).json()
    furl = r.get("url")
    if not furl:
        raise RuntimeError(f"file upload fail: {str(r)[:150]}")
    title = re.sub(r"\s*#\S+", "", meta.get("title", "")).strip()[:150] or "Sab Hisaab"
    base = {"url": furl, "title": title, "channel": CATEGORY, "published": "true", "private": "false",
            "is_created_for_kids": "false"}
    extra = {"description": build_desc(meta), "tags": tags_of(meta)}
    r = requests.post(f"{API}/user/{c['channel']}/videos", headers=_hl(), data={**base, **extra}, timeout=120).json()
    if not r.get("id"):                       # koi vaikalpik khaana na chale to bina uske (video phir bhi jaye)
        log(f"dm create full: {str(r)[:200]}")
        r = requests.post(f"{API}/user/{c['channel']}/videos", headers=_hl(), data=base, timeout=120).json()
        if r.get("id"):
            try:
                requests.post(f"{API}/video/{r['id']}", headers=_hl(), data={"description": extra["description"]}, timeout=60)
            except Exception:
                pass
    if not r.get("id"):
        raise RuntimeError(f"video nahi bani: {str(r)[:180]}")
    _mark_posted()
    return f"https://www.dailymotion.com/video/{r['id']}", r["id"]


def delete(xid):
    try:
        t, _ = token_v2()
        r = requests.delete(f"{V2}/videos/{xid}", headers={"Authorization": f"Bearer {t}"}, timeout=60)
        if r.status_code in (200, 202, 204):
            return True
    except Exception as e:
        log(f"dm v2 delete: {e}")
    try:
        r = requests.delete(f"{API}/video/{xid}", headers=_hl(), timeout=60)
        return r.status_code in (200, 204)
    except Exception:
        return False


def warn_once(err):
    d = str(datetime.date.today()) + "|" + str(err)[:25]      # v3.4.14: nayi tarah ki galti ho to usi din bhi batao
    if state.get("dm_warn_day") == d:
        return
    state.put("dm_warn_day", d)
    tg.alert("yellow", f"🎬 Dailymotion par aaj video nahi gayi: {str(err)[:200]}\nBaaki platform par sab theek. 'dailymotion haal' se dekhein.")


# ---------------------------------------------------------------- report / hukum
def views(days=7):
    """Aakhri N din mein Dailymotion par gayi video ke views (Dailymotion API) -> int ya None."""
    c = _cfg()
    if not c.get("channel"):
        return None
    try:
        cut = int(time.time()) - days * 86400
        j = requests.get(f"{PUBLIC}/user/{c['channel']}/videos", params={"fields": "id,views_total,created_time", "limit": 100,
                                                                         "created_after": cut}, timeout=30).json()
        if "list" not in j:
            return None
        return sum(int(x.get("views_total") or 0) for x in j.get("list") or [])
    except Exception as e:
        log(f"dm views: {e}")
        return None


def status_text():
    c = _cfg()
    if not ready():
        return "🎬 Dailymotion: abhi juda nahi. Likhiye 'dailymotion jodo' - bot key/secret khud maangega."
    d = str(datetime.date.today())
    v = views(7)
    return (f"🎬 Dailymotion: @{c.get('user', '?')} | roz {per_day()} video | aaj gayi: {(state.get('dm_log') or {}).get(d, 0)} | "
            f"{'CHALU' if on() else 'BAND'}" + (f" | 7 din views: {v}" if v is not None else "") +
            "\nHukum: 'dailymotion roz 3' | 'dailymotion band' / 'dailymotion chalu' | 'dailymotion jodo' (nayi key)")


def on_text(tl):
    if tl in ("dailymotion jodo", "dailymotion key", "dailymotion login", "dailymotion connect", "dailymotion juda"):
        return ask()
    if tl in ("dailymotion baad mein", "dailymotion baad me"):
        state.put("awaiting", "")
        state.put("dm_ask_done", True)
        return tg.say("👍 Theek hai. Jab chahein: 'dailymotion jodo'.")
    if tl in ("dailymotion haal", "dailymotion", "dailymotion status"):
        return tg.say(status_text())
    m = re.match(r"^dailymotion roz (\d{1,2})$", tl)
    if m:
        state.put("dm_max", max(0, min(10, int(m.group(1)))))
        return tg.say(f"🎬 Dailymotion: ab roz max {per_day()} video.")
    m = re.match(r"^dailymotion channel ([a-z0-9._\-]{3,60})$", tl)
    if m:
        cid, user = find_channel(m.group(1))
        if not cid:
            return tg.say("❌ Ye channel nahi mila. Studio → Edit profile mein jo Username hai wahi likhiye.")
        c = _cfg()
        c.update(channel=cid, user=user)
        _save(c)
        state.put("dm_on", True)
        return tg.say(f"✅ Dailymotion channel juda: @{user}")
    if tl in ("dailymotion band", "dailymotion chalu"):
        state.put("dm_on", tl.endswith("chalu"))
        return tg.say("🎬 Dailymotion roz ki video: " + ("CHALU" if tl.endswith("chalu") else "BAND"))
    return None
