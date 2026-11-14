"""Threads: har brand ka apna token. Post = hook text + YouTube link + website link (Threads par link click hota hai).
Token 60 din chalta hai; bot har 20 din mein apne aap naya karta hai."""
import json
import time
import requests
from .config import SECRETS, BRANDS

API = "https://graph.threads.net/v1.0"
STORE = SECRETS / "threads.json"


def _load():
    try:
        return json.loads(STORE.read_text())
    except Exception:
        return {}


def _save(d):
    STORE.write_text(json.dumps(d))
    STORE.chmod(0o600)


def save_token(brand, token):
    me = requests.get(f"{API}/me", params={"fields": "id,username", "access_token": token}, timeout=30).json()
    if "id" not in me:
        raise RuntimeError(f"Threads token nahi chala: {me.get('error', {}).get('message', me)}")
    d = _load()
    d[brand] = {"token": token, "user_id": me["id"], "username": me.get("username", ""), "saved": time.time()}
    _save(d)
    return me.get("username", "")


def info(brand):
    return _load().get(brand)


def alive(brand, max_age=6 * 3600):
    """v2.1.1: token SACH mein chal raha hai? (/me). Pehle sirf file dekhi jaati thi - restore ke baad STATUS 'OK' kehta
    raha jabki 3 brand ka token 30 Oct ko khatam ho chuka tha. 6 ghante ka cache."""
    from . import state
    v = info(brand)
    if not v:
        return False, "token nahi"
    cache = state.get("threads_alive") or {}
    c = cache.get(brand)
    if c and time.time() - c["t"] < max_age and c.get("tok") == v["token"][-6:]:
        return c["ok"], c["msg"]
    try:
        me = requests.get(f"{API}/me", params={"fields": "id,username", "access_token": v["token"]}, timeout=20).json()
        ok, msg = ("id" in me), ("" if "id" in me else me.get("error", {}).get("message", str(me))[:120])
    except Exception as e:
        return True, f"jaanch nahi ho payi ({str(e)[:60]})"          # network galti par 'band' mat bolo
    cache[brand] = {"t": time.time(), "ok": ok, "msg": msg, "tok": v["token"][-6:]}
    state.put("threads_alive", cache)
    return ok, msg


def refresh_all():
    d, out = _load(), []
    for b, v in d.items():
        if time.time() - v.get("saved", 0) > 20 * 86400:
            r = requests.get("https://graph.threads.net/refresh_access_token",
                             params={"grant_type": "th_refresh_token", "access_token": v["token"]}, timeout=30).json()
            if "access_token" in r:
                v.update(token=r["access_token"], saved=time.time())
                out.append(f"♻️ Threads {BRANDS[b]['name']} token naya")
            else:
                out.append(f"🔴 Threads {BRANDS[b]['name']} token refresh fail: {r.get('error', {}).get('message', '')}")
    _save(d)
    return out


def check_threads_quota(brand):
    """v2.3.0 (v11 se): Threads API 250 post / 24 ghante (har profile) - 240 par ruk jaate hain."""
    import datetime
    from . import state
    today = str(datetime.date.today())
    cnt = ((state.get("threads_daily") or {}).get(today) or {}).get(brand, 0)
    return {"date": today, "brand": brand, "used": cnt, "limit": 250, "ok": cnt < 240}


def _threads_count(brand):
    import datetime
    from . import state
    today = str(datetime.date.today())
    state.update("threads_daily", lambda d: {today: {**((d or {}).get(today) or {}),
                                                    brand: (((d or {}).get(today) or {}).get(brand, 0) + 1)}}, {})


def post_riddle_thread(brand, question, options, link):
    """v2.3.0 (v11 se): Threads par '10 second' paheli (options + website link card). Step 4 ke puzzle isse jaate hain."""
    opts_txt = "\n".join(f"{chr(65 + i)}) {o}" for i, o in enumerate((options or [])[:4]))
    body = f"🧠 10 second challenge:\n\n{question}\n\n{opts_txt}\n\n👇 Jawab comment karein, sahi jawab + poora hisaab yahan:\n👉 {link}"
    return post_text(brand, body[:495], link=link)


def _publish(v, cid):
    """v2.4.1: container taiyaar hone tak ruko (status FINISHED), phir 3 koshish - pehle 5 sec baad seedha 'Fatal' aata tha."""
    p = {}
    for i in range(6):
        time.sleep(4 + i * 3)
        try:
            st = requests.get(f"{API}/{cid}", timeout=30, params={"fields": "status,error_message", "access_token": v["token"]}).json()
            if st.get("status") == "ERROR":
                return {"error": {"message": st.get("error_message", "container ERROR")}}
            if st.get("status") not in (None, "FINISHED", "PUBLISHED"):
                continue
        except Exception:
            pass
        p = requests.post(f"{API}/{v['user_id']}/threads_publish", timeout=60,
                          data={"creation_id": cid, "access_token": v["token"]}).json()
        if "id" in p:
            return p
    return p


def post_text(brand, text, link=None):
    """TEXT post + link_attachment (Threads par clickable link card -> website traffic)."""
    q_st = check_threads_quota(brand)
    if not q_st.get("ok", True):
        raise RuntimeError(f"Threads 24 ghante ki seema ({q_st.get('used')}/{q_st.get('limit')})")
    v = info(brand)
    if not v:
        raise RuntimeError("Threads token nahi")
    data = {"media_type": "TEXT", "text": text[:500], "access_token": v["token"]}
    if link:
        data["link_attachment"] = link
    c = requests.post(f"{API}/{v['user_id']}/threads", timeout=60, data=data).json()
    if "id" not in c and link:          # link card na chale to bina card (text mein link to hai hi)
        data.pop("link_attachment")
        c = requests.post(f"{API}/{v['user_id']}/threads", timeout=60, data=data).json()
    if "id" not in c:
        raise RuntimeError(f"Threads: {c.get('error', {}).get('message', c)}")
    p = _publish(v, c["id"])
    if "id" not in p and data.get("link_attachment"):     # v2.4.1: 'Fatal' aksar link-card ki wajah se -> bina card dobara
        data.pop("link_attachment", None)
        c2 = requests.post(f"{API}/{v['user_id']}/threads", timeout=60, data=data).json()
        if "id" in c2:
            p = _publish(v, c2["id"])
    if "id" not in p:
        raise RuntimeError(f"Threads publish: {p.get('error', {}).get('message', p)}")
    state_id = p["id"]
    _threads_count(brand)
    return f"https://www.threads.net/@{v['username']}#{state_id}"



def delete_post(brand, media_id):
    v = info(brand)
    r = requests.delete(f"{API}/{media_id}", params={"access_token": v["token"]}, timeout=30).json()
    if not r.get("success"):
        raise RuntimeError(f"Threads delete: {r.get('error', {}).get('message', r)}")
    return True
