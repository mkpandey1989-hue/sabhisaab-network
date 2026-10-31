"""Facebook Page Reels + Instagram Reels (system user 'sabhisaab-bot' ka token, sirf VM par).
Token Telegram par /meta TOKEN SECRET bhejkar (bot message turant mita deta hai)."""
import hashlib
import hmac
import json
import time
import requests
from .config import SECRETS, GRAPH, RUPLOAD, GRAPH_VER, BRANDS
from .log import log

STORE = SECRETS / "meta.json"


def has_token():
    return STORE.exists()


def _cfg():
    return json.loads(STORE.read_text())


def _proof(token):
    c = _cfg()
    sec = None if c.get("secret_bad") else c.get("app_secret")
    return {"appsecret_proof": hmac.new(sec.encode(), token.encode(), hashlib.sha256).hexdigest()} if sec else {}


def _call(method, path, token, payload):
    """appsecret_proof galat ho (secret reset hua) to bina proof dobara; secret theek karne ka alert."""
    for with_proof in (True, False):
        extra = _proof(token) if with_proof else {}
        if with_proof and not extra:
            continue
        kw = {"params": {"access_token": token, **extra, **payload}} if method in ("GET", "DELETE") else \
             {"data": {"access_token": token, **extra, **payload}}
        j = requests.request(method, f"{GRAPH}{path}", timeout=120, **kw).json()
        err = j.get("error", {}).get("message", "") if "error" in j else ""
        if with_proof and "appsecret_proof" in err:
            _flag_secret()
            continue
        if err:
            if "appsecret_proof" in err:
                raise RuntimeError("Meta: App Secret galat/purana hai. App settings > Basic se abhi wala secret bot ko bhejein.")
            raise RuntimeError(f"Meta: {err}")
        return j
    raise RuntimeError("Meta: jawab nahi mila")


def _flag_secret():
    try:
        c = _cfg()
        c["secret_bad"] = True
        STORE.write_text(json.dumps(c))
    except Exception:
        pass


def _get(path, token, **params):
    return _call("GET", path, token, params)


def _post(path, token, **data):
    return _call("POST", path, token, data)


def _norm(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


def save_token(token, app_secret=""):
    old = _cfg() if has_token() else {}
    STORE.write_text(json.dumps({"token": token, "app_secret": app_secret or old.get("app_secret", "")}))
    STORE.chmod(0o600)
    return discover()


def discover():
    """System user ke pages + unke Instagram account dhoondh kar brand se jodo."""
    c = _cfg()
    pages = _get("/me/accounts", c["token"], fields="id,name,access_token,instagram_business_account{id,username}",
                 limit=50).get("data", [])
    mapping, lines = {}, []
    for b, info in BRANDS.items():
        want = _norm(info["name"])
        alt = {"sunonatak": "sunonatak", "money": "sabhisaabmoney", "deals": "labhlodeals", "pahadi": "pahadihisaab"}[b]
        hit = next((p for p in pages if want in _norm(p["name"]) or alt in _norm(p["name"])), None)
        if hit:
            ig = hit.get("instagram_business_account") or {}
            mapping[b] = {"page_id": hit["id"], "page_name": hit["name"], "page_token": hit["access_token"],
                          "ig_id": ig.get("id"), "ig_user": ig.get("username")}
            lines.append(f"✅ {info['name']}: FB '{hit['name']}'" + (f" + IG @{ig['username']}" if ig else " (IG nahi juda)"))
        else:
            lines.append(f"❌ {info['name']}: page nahi mila (system user ko page asset dein)")
    c["brands"] = mapping
    STORE.write_text(json.dumps(c))
    STORE.chmod(0o600)
    return "\n".join(lines)


def brand_info(brand):
    return _cfg().get("brands", {}).get(brand) if has_token() else None


def post_facebook(brand, video_path, caption):
    b = brand_info(brand)
    if not b:
        raise RuntimeError("FB page juda nahi")
    tok = b["page_token"]
    vid = _post(f"/{b['page_id']}/video_reels", tok, upload_phase="start")["video_id"]
    size = video_path.stat().st_size
    with open(video_path, "rb") as f:
        r = requests.post(f"{RUPLOAD}/video-upload/{GRAPH_VER}/{vid}", data=f, timeout=900,
                          headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size)})
    if not r.ok or not r.json().get("success"):
        raise RuntimeError(f"FB upload: {r.text[:200]}")
    try:      # AI label (Meta + India IT Rules 2026)
        _post(f"/{b['page_id']}/video_reels", tok, upload_phase="finish", video_id=vid, video_state="PUBLISHED",
              description=caption[:2000], is_ai_generated="true")
    except Exception as e:
        if "is_ai_generated" not in str(e):
            raise
        _post(f"/{b['page_id']}/video_reels", tok, upload_phase="finish", video_id=vid, video_state="PUBLISHED",
              description=caption[:2000])
    return vid


def _ig_container(b, tok, video_path, **fields):
    cid = _post(f"/{b['ig_id']}/media", tok, upload_type="resumable", **fields)["id"]
    size = video_path.stat().st_size
    with open(video_path, "rb") as f:
        r = requests.post(f"{RUPLOAD}/ig-api-upload/{GRAPH_VER}/{cid}", data=f, timeout=900,
                          headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size),
                                   "Content-Type": "application/octet-stream"})
    if not r.ok:
        raise RuntimeError(f"IG upload HTTP {r.status_code}: {r.text[:300]} (size {size // 1048576} MB)")
    for _ in range(40):          # Instagram video process karta hai (10 min tak)
        st = _get(f"/{cid}", tok, fields="status_code").get("status_code")
        if st == "FINISHED":
            return cid
        if st == "ERROR":
            try:
                why = _get(f"/{cid}", tok, fields="status").get("status", "")
            except Exception:
                why = ""
            raise RuntimeError(f"Instagram ne video process nahi ki {why}"[:300])
        time.sleep(15)
    raise RuntimeError("Instagram processing ka samay khatam")


def post_instagram(brand, video_path, caption):
    b = brand_info(brand)
    if not b or not b.get("ig_id"):
        raise RuntimeError("IG account juda nahi")
    tok = b["page_token"]
    caption = ig_safe_text(caption)               # v2.0.3: Instagram par koi link/UTM nahi (Meta scam-pattern)
    last = None
    vp = video_path
    for attempt in range(3):     # har baar naya container (IG kabhi-kabhi processing fail karta hai)
        try:
            cap = caption[:2100]
            if attempt == 2:                      # v2.0.6: teesri koshish chhote, saade caption ke saath
                first = [l for l in caption.splitlines() if l.strip() and "link bio" not in l.lower()][:2]
                cap = IG_LINK_LINE + "\n\n" + "\n".join(first)[:300] + "\nIs video ki awaaz AI se bani hai."
            cid = _ig_container(b, tok, vp, media_type="REELS", caption=cap, share_to_feed="true",
                                thumb_offset="200")      # cover = shuru ka (thumbnail wala) frame
            break
        except Exception as e:
            last = e
            log(f"IG {brand} koshish {attempt + 1}: {str(e)[:400]}")
            if attempt == 0:                      # v2.0.3: ProcessingFailedError -> IG ke pakke format mein dobara
                try:
                    vp = _ig_safe_video(video_path)
                    log(f"IG {brand}: file IG-safe format mein dobara bani")
                except Exception as e2:
                    log(f"IG safe video: {e2}")
            time.sleep(60 * (attempt + 1))
    else:
        raise RuntimeError(f"3 koshish fail: {str(last)[:150]}")
    mid = _post(f"/{b['ig_id']}/media_publish", tok, creation_id=cid)["id"]
    try:
        link = _get(f"/{mid}", tok, fields="permalink").get("permalink", "")
    except Exception:
        link = ""
    return mid, link


# ---------------- v0.6: story ----------------
def fb_photo_story(brand, image_path):
    """Facebook Page story (photo)."""
    b = brand_info(brand)
    if not b:
        raise RuntimeError("FB page juda nahi")
    tok = b["page_token"]
    with open(image_path, "rb") as f:
        r = requests.post(f"{GRAPH}/{b['page_id']}/photos", timeout=120,
                          data={"access_token": tok, "published": "false", **_proof(tok)}, files={"source": f}).json()
    if "id" not in r:
        raise RuntimeError(f"FB photo: {r.get('error', {}).get('message', r)}")
    _post(f"/{b['page_id']}/photo_stories", tok, photo_id=r["id"])
    return "FB story"


def ig_video_story(brand, video_path):
    b = brand_info(brand)
    if not b or not b.get("ig_id"):
        raise RuntimeError("IG juda nahi")
    tok = b["page_token"]
    cid = _ig_container(b, tok, video_path, media_type="STORIES")
    _post(f"/{b['ig_id']}/media_publish", tok, creation_id=cid)
    return "IG story"


def ig_comments(brand, seen):
    b = brand_info(brand)
    if not b or not b.get("ig_id"):
        return []
    tok = b["page_token"]
    media = _get(f"/{b['ig_id']}/media", tok, fields="id,comments.limit(20){id,text,username,replies.limit(1){id}}",
                 limit=8).get("data", [])
    out = []
    for md in media:
        for c in md.get("comments", {}).get("data", []):
            if c["id"] in seen or c.get("replies", {}).get("data") or c.get("username") == b.get("ig_user"):
                continue
            out.append({"id": c["id"], "author": c.get("username", ""), "text": c.get("text", "")[:500], "media": md.get("id", "")})
    return out


def ig_reply(brand, comment_id, text):
    b = brand_info(brand)
    text = ig_safe_text(text, add_line=False) or "🙏"          # v2.0.3: IG comment mein link nahi
    return _post(f"/{comment_id}/replies", b["page_token"], message=text[:900])



def delete_fb(brand, video_id):
    b = brand_info(brand)
    _call("DELETE", f"/{video_id}", b["page_token"], {})
    return True


def delete_ig(brand, media_id):
    b = brand_info(brand)
    _call("DELETE", f"/{media_id}", b["page_token"], {})     # Instagram kuch account par delete API nahi deta
    return True



def fb_video_stats(brand, video_id):
    """FB reel: views (plays), likes, comments - ek-ek metric (Meta ne kai purane naam hata diye)."""
    b = brand_info(brand)
    tok = b["page_token"]
    out = {}
    try:
        j = _get(f"/{video_id}", tok, fields="likes.summary(true).limit(0),comments.summary(true).limit(0)")
        out["likes"] = j.get("likes", {}).get("summary", {}).get("total_count", 0)
        out["comments"] = j.get("comments", {}).get("summary", {}).get("total_count", 0)
    except Exception:
        pass
    for m in ("fb_reels_total_plays", "blue_reels_play_count", "total_video_views"):
        try:
            d = _get(f"/{video_id}/video_insights", tok, metric=m).get("data", [])
            if d:
                out["views"] = d[0]["values"][0]["value"]
                break
        except Exception:
            continue
    return out


def ig_media_stats(brand, media_id):
    b = brand_info(brand)
    out = {}
    try:
        j = _get(f"/{media_id}", b["page_token"], fields="like_count,comments_count")
        out.update(likes=j.get("like_count", 0), comments=j.get("comments_count", 0))
    except Exception:
        pass
    try:
        d = _get(f"/{media_id}/insights", b["page_token"], metric="views").get("data", [])
        if d:
            out["views"] = d[0]["values"][0]["value"] if d[0].get("values") else d[0].get("total_value", {}).get("value")
    except Exception:
        pass
    return out


def private_reply_ig(brand, comment_id, text):
    """Comment keyword -> ek DM (Meta 'private reply'; 7 din ke andar, ek baar). App Review ke baad chalega."""
    if ig_dm_blocked(brand):                      # v2.0.3: Meta ki DM rok / owner ka niyam
        raise RuntimeError(f"{brand}: Instagram DM abhi band (rok)")
    b = brand_info(brand)
    return _post(f"/{b['ig_id']}/messages", b["page_token"], recipient=json.dumps({"comment_id": comment_id}),
                 message=json.dumps({"text": text[:900]}))


def private_reply_fb(brand, comment_id, text):
    b = brand_info(brand)
    return _post(f"/{b['page_id']}/messages", b["page_token"], recipient=json.dumps({"comment_id": comment_id}),
                 message=json.dumps({"text": text[:900]}))


# ---------------- v2.0.3: Instagram suraksha (29 Oct 2026, @sunonatak par Meta ki rok ke baad) ----------------
# Instagram caption/comment mein link click nahi hota, aur naye finance account par link + "comment LINK" + DM ka
# pattern Meta "scam / prohibited commercial practices" maanta hai. Isliye Instagram par: koi URL nahi, sirf "link bio mein".
IG_LINK_LINE = "🔗 Free calculator ka link bio mein 👆"
_URL_RX = __import__("re").compile(r"(?:https?://|www\.)\S+|\b[\w-]+\.(?:com|in|net|org|me|ly)(?:/\S*)?", __import__("re").I)


def ig_safe_text(text, add_line=True):
    """Instagram text se har link/UTM hatao; link wali line ki jagah ek baar 'link bio mein'."""
    if not isinstance(text, str):
        return text
    out, had = [], False
    for line in text.splitlines():
        if _URL_RX.search(line):
            had = True
            parts = __import__("re").split(r"(?<=[!?।.])\s+", _URL_RX.sub("", line))
            keep = [x.strip(" :-👉🌐🔗|") for x in parts
                    if not any(w in x.lower() for w in ("calculator", "hisaab yahan", "poora hisaab", "link", "कैलकुलेटर", "yahan:"))]
            line = " ".join(k for k in keep if k)
            if not line:
                continue
        if "link bio mein" in line.lower() or "comment mein link" in line.lower() or "link likh" in line.lower():
            had = True
            continue
        out.append(line)
    body = "\n".join(out).strip()
    tags = __import__("re").findall(r"#\w+", body)
    if len(tags) > 5:                             # v2.0.6: Instagram Help Center - ek post par max 5 hashtag
        keep = set(tags[:5])
        seen = set()
        def _tag(m):
            t = m.group(0)
            if t in keep and t not in seen:
                seen.add(t)
                return t
            return ""
        body = __import__("re").sub(r"#\w+", _tag, body)
        body = "\n".join(l.rstrip() for l in body.splitlines())
    while "\n\n\n" in body:
        body = body.replace("\n\n\n", "\n\n")
    return (IG_LINK_LINE + "\n\n" + body) if (add_line and (had or body)) else body


def ig_dm_blocked(brand):
    """Owner/Meta ki rok: is brand ke Instagram se DM band (tareekh tak). Default: @sunonatak 27 Nov 2026 tak."""
    import datetime
    from . import state
    d = dict({"sunonatak": "2026-11-27", "deals": "2026-11-28"}, **(state.get("ig_dm_block") or {}))
    till = d.get(brand)
    return bool(till) and str(datetime.date.today()) <= till


def _ig_safe_video(video_path):
    """IG ne file mana ki to ek baar IG ke pakke format mein dobara banao (H.264 + AAC, 30fps, yuv420p, faststart)."""
    import pathlib
    import subprocess
    src = pathlib.Path(video_path)
    out = src.with_name(src.stem + "_igsafe.mp4")
    if out.exists() and out.stat().st_size > 0:
        return out
    cmd = ["nice", "-n", "15", "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", "1", "-i", str(src),
           "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
           "-c:v", "libx264", "-profile:v", "high", "-level", "4.1", "-preset", "veryfast", "-b:v", "5M", "-maxrate", "8M",
           "-bufsize", "10M", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0 or not out.exists():
        raise RuntimeError("IG-safe video nahi bani: " + r.stderr[-200:])
    return out
