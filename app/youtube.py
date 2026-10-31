"""YouTube: TV/Device login (phone se manzoori), har brand ka alag token, upload + thumbnail."""
import json
import time
import requests
from .config import SECRETS, BRANDS, YT_CATEGORY
from .log import log

SCOPE = "https://www.googleapis.com/auth/youtube"
CLIENT = SECRETS / "yt_client.json"


def _client():
    j = json.loads(CLIENT.read_text())
    j = j.get("installed") or j.get("web") or j
    return j["client_id"], j["client_secret"]


def token_path(brand):
    return SECRETS / f"yt_{brand}.json"


def has_login(brand):
    return token_path(brand).exists()


def device_start():
    cid, _ = _client()
    r = requests.post("https://oauth2.googleapis.com/device/code", data={"client_id": cid, "scope": SCOPE}, timeout=30)
    j = r.json()
    if "device_code" not in j:
        raise RuntimeError(f"Google login shuru nahi hua: {j}")
    return j   # device_code, user_code, verification_url, interval, expires_in


def device_poll(dev, timeout_min=15):
    cid, sec = _client()
    end = time.time() + min(timeout_min * 60, dev.get("expires_in", 900))
    wait = int(dev.get("interval", 5))
    while time.time() < end:
        time.sleep(wait)
        r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
            "client_id": cid, "client_secret": sec, "device_code": dev["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"})
        j = r.json()
        if "refresh_token" in j:
            return j
        if j.get("error") == "slow_down":
            wait += 5
        elif j.get("error") not in ("authorization_pending",):
            raise RuntimeError(f"Login fail: {j.get('error')}")
    raise TimeoutError("Login ka samay khatam")


def _access(brand):
    tp = token_path(brand)
    t = json.loads(tp.read_text())
    if t.get("expires_at", 0) > time.time() + 120:
        return t["access_token"]
    cid, sec = _client()
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": cid, "client_secret": sec, "refresh_token": t["refresh_token"], "grant_type": "refresh_token"})
    j = r.json()
    if "access_token" not in j:
        raise RuntimeError(f"{brand}: YouTube login dobara chahiye ({j.get('error')})")
    t["access_token"], t["expires_at"] = j["access_token"], time.time() + int(j.get("expires_in", 3600))
    tp.write_text(json.dumps(t))
    tp.chmod(0o600)
    return t["access_token"]


def _api(brand, method, path, **kw):
    h = kw.pop("headers", {})
    h["Authorization"] = f"Bearer {_access(brand)}"
    r = requests.request(method, f"https://www.googleapis.com{path}", headers=h, timeout=kw.pop("timeout", 120), **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"YouTube {r.status_code}: {r.text[:300]}")
    return r.json() if r.content else {}


def save_login(brand, tok):
    t = {"refresh_token": tok["refresh_token"], "access_token": tok["access_token"],
         "expires_at": time.time() + int(tok.get("expires_in", 3600))}
    tp = token_path(brand)
    tp.write_text(json.dumps(t))
    tp.chmod(0o600)
    ch = my_channel(brand)
    t["channel_id"], t["channel_title"] = ch["id"], ch["snippet"]["title"]
    tp.write_text(json.dumps(t))
    return t


def my_channel(brand):
    items = _api(brand, "GET", "/youtube/v3/channels", params={"part": "snippet", "mine": "true"}).get("items", [])
    if not items:
        raise RuntimeError("Is login mein koi channel nahi mila")
    return items[0]


def channel_title(brand):
    return json.loads(token_path(brand).read_text()).get("channel_title", "?")


def channel_ok(brand):
    """Login wala channel sahi brand ka hai?"""
    t = json.loads(token_path(brand).read_text())
    want = BRANDS[brand]["name"].lower().replace(" ", "")
    got = t.get("channel_title", "").lower().replace(" ", "")
    return want in got or got in want, t.get("channel_title", "?")


def upload(brand, video_path, title, description, tags, thumb_path, privacy="public", publish_at=None):
    body = {"snippet": {"title": title[:100], "description": description[:4900], "tags": tags[:15],
                        "categoryId": YT_CATEGORY, "defaultLanguage": "hi", "defaultAudioLanguage": "hi"},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": True}}
    if publish_at:      # YouTube khud theek samay par public karega (minute ki bhi deri nahi)
        body["status"].update(privacyStatus="private", publishAt=publish_at)
    size = video_path.stat().st_size
    vid = None
    for n in range(5):
        try:
            url = _session(brand, body, size)
            with open(video_path, "rb") as f:
                r = requests.put(url, data=f, timeout=900, headers={"Content-Type": "video/mp4",
                                                                     "Content-Length": str(size)})
            if r.status_code in (200, 201):
                vid = r.json()["id"]
                break
            raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
        except Exception as e:
            log(f"upload koshish {n + 1} fail: {e}")
            if "quota" in str(e).lower():
                raise
            time.sleep(30 * (n + 1))
    if not vid:
        raise RuntimeError("Upload 5 baar fail")
    try:
        with open(thumb_path, "rb") as f:
            _api(brand, "POST", "/upload/youtube/v3/thumbnails/set", params={"videoId": vid},
                 headers={"Content-Type": "image/jpeg"}, data=f.read())
    except Exception as e:
        log(f"thumbnail set fail (video phir bhi live): {e}")
    return vid


def _session(brand, body, size):
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos",
                         params={"uploadType": "resumable", "part": "snippet,status"}, timeout=60,
                         headers={"Authorization": f"Bearer {_access(brand)}", "Content-Type": "application/json",
                                  "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
                         data=json.dumps(body))
    if init.status_code == 400 and "containsSyntheticMedia" in init.text and "containsSyntheticMedia" in body["status"]:
        body["status"].pop("containsSyntheticMedia")
        log("API ne AI flag field nahi maana; description mein AI label hai, bina field upload")
        return _session(brand, body, size)
    if init.status_code >= 400:
        raise RuntimeError(f"Upload shuru nahi hua {init.status_code}: {init.text[:300]}")
    return init.headers["Location"]


# ---------------- v0.5: views report + comments ----------------
def stats(brand, ids):
    out = {}
    for i in range(0, len(ids), 50):
        items = _api(brand, "GET", "/youtube/v3/videos", params={"part": "statistics,snippet",
                                                                  "id": ",".join(ids[i:i + 50])}).get("items", [])
        for it in items:
            s = it.get("statistics", {})
            out[it["id"]] = {"views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
                             "comments": int(s.get("commentCount", 0)), "title": it["snippet"]["title"]}
    return out


def new_comments(brand, seen):
    """Channel par naye comments (jinka jawab nahi diya)."""
    t = json.loads(token_path(brand).read_text())
    items = _api(brand, "GET", "/youtube/v3/commentThreads", params={
        "part": "snippet", "allThreadsRelatedToChannelId": t["channel_id"], "order": "time",
        "maxResults": 20, "textFormat": "plainText"}).get("items", [])
    out = []
    for it in items:
        top = it["snippet"]["topLevelComment"]
        if top["id"] in seen or it["snippet"].get("totalReplyCount", 0) > 0:
            continue
        sn = top["snippet"]
        if sn.get("authorChannelId", {}).get("value") == t["channel_id"]:
            continue          # apna comment
        out.append({"id": top["id"], "video": it["snippet"].get("videoId", ""), "author": sn.get("authorDisplayName", ""),
                    "text": sn.get("textDisplay", "")[:500]})
    return out


def reply_comment(brand, parent_id, text):
    return _api(brand, "POST", "/youtube/v3/comments", params={"part": "snippet"},
                json={"snippet": {"parentId": parent_id, "textOriginal": text[:900]}})


def add_to_playlist(brand, vid, kind="Shorts"):
    """Har brand ki 'Shorts' / 'Lambi videos' playlist (na ho to bana do) mein video jodo."""
    from . import state
    key = f"{brand}:{kind}"
    pl = (state.get("playlists") or {}).get(key)
    if not pl:
        name = f"{BRANDS[brand]['name']} - {'Shorts' if kind == 'Shorts' else 'Poori jaankari (lambi videos)'}"
        pl = _api(brand, "POST", "/youtube/v3/playlists", params={"part": "snippet,status"},
                  json={"snippet": {"title": name, "defaultLanguage": "hi",
                                    "description": f"{BRANDS[brand]['name']} ki saari videos. Free calculator: https://sabhisaab.com"},
                        "status": {"privacyStatus": "public"}})["id"]
        state.update("playlists", lambda d: {**(d or {}), key: pl}, {})
    _api(brand, "POST", "/youtube/v3/playlistItems", params={"part": "snippet"},
         json={"snippet": {"playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}})
    return pl


def top_comment(brand, vid, text):
    return _api(brand, "POST", "/youtube/v3/commentThreads", params={"part": "snippet"},
                json={"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": text[:900]}}}})



def delete_video(brand, vid):
    h = {"Authorization": f"Bearer {_access(brand)}"}
    r = requests.delete("https://www.googleapis.com/youtube/v3/videos", params={"id": vid}, headers=h, timeout=60)
    if r.status_code not in (200, 204):
        raise RuntimeError(f"YouTube delete {r.status_code}: {r.text[:200]}")
    return True


def recent_titles(brand, n=50):
    """Channel par asal mein kaunsi videos hain (doosri jaanch: dobara upload na ho)."""
    ch = _api(brand, "GET", "/youtube/v3/channels", params={"part": "contentDetails", "mine": "true"})["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = _api(brand, "GET", "/youtube/v3/playlistItems", params={"part": "snippet", "playlistId": up,
                                                                     "maxResults": n}).get("items", [])
    return [(i["snippet"]["title"], i["snippet"]["resourceId"]["videoId"]) for i in items]


def channel_stats(brand):
    it = _api(brand, "GET", "/youtube/v3/channels", params={"part": "statistics", "mine": "true"})["items"][0]["statistics"]
    return {"subs": int(it.get("subscriberCount", 0)), "views": int(it.get("viewCount", 0)), "videos": int(it.get("videoCount", 0))}



def recent_videos(brand, n=50):
    ch = _api(brand, "GET", "/youtube/v3/channels", params={"part": "contentDetails", "mine": "true"})["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = _api(brand, "GET", "/youtube/v3/playlistItems", params={"part": "snippet,status", "playlistId": up,
                                                                     "maxResults": n}).get("items", [])
    return [{"title": i["snippet"]["title"], "vid": i["snippet"]["resourceId"]["videoId"],
             "date": i["snippet"].get("publishedAt", "")[:16].replace("T", " "), "brand": brand} for i in items]
