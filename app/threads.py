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


def post_text(brand, text, link=None):
    """TEXT post + link_attachment (Threads par clickable link card -> website traffic)."""
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
    time.sleep(5)
    p = requests.post(f"{API}/{v['user_id']}/threads_publish", timeout=60,
                      data={"creation_id": c["id"], "access_token": v["token"]}).json()
    if "id" not in p:
        raise RuntimeError(f"Threads publish: {p.get('error', {}).get('message', p)}")
    state_id = p["id"]
    return f"https://www.threads.net/@{v['username']}#{state_id}"



def delete_post(brand, media_id):
    v = info(brand)
    r = requests.delete(f"{API}/{media_id}", params={"access_token": v["token"]}, timeout=30).json()
    if not r.get("success"):
        raise RuntimeError(f"Threads delete: {r.get('error', {}).get('message', r)}")
    return True
