"""v2.4.0 (owner ki pehli lambi list):
1) Voice-note se hukum: Telegram awaaz -> Cloudflare Whisper (aapke CF account, free seema) -> text -> wahi hukum (dohri pushti
   wale kaam par pushti wahi rehti hai).
2) Competitor video se APNA version: link -> YouTube API se sirf title/description/tags (video download/copy NAHI) ->
   naya ORIGINAL sawal-reel usi vishay par (copyright/'reused content' niti ke andar).
3) Ek render se 9:16 + 1:1 + 16:9 (dhundhla peeche, video beech mein) - Facebook feed / YouTube / X ke liye."""
import os
import pathlib
import re
import subprocess

import requests

from . import tg, state
from .config import TMP
from .log import log


def transcribe(audio_path):
    from .website import _cf
    tok, acc = _cf()
    if not (tok and acc):
        raise RuntimeError("Cloudflare token/account nahi")
    data = open(audio_path, "rb").read()
    r = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/@cf/openai/whisper", timeout=120,
                      headers={"Authorization": f"Bearer {tok}"}, data=data)
    j = r.json()
    txt = ((j.get("result") or {}).get("text") or "").strip()
    if not txt:
        raise RuntimeError(f"awaaz samajh nahi aayi ({str(j.get('errors') or j)[:120]})")
    return txt


def on_voice(m, handler):
    """Owner ki awaaz -> text -> handler(text) (bot.on_text)."""
    v = m.get("voice") or m.get("audio") or {}
    if not v.get("file_id"):
        return
    if v.get("file_size", 0) > 20 * 1024 * 1024:
        return tg.say("🎙 Awaaz 20 MB se badi hai - chhota note bhejein.")
    p = pathlib.Path(TMP) / f"voice_{v['file_id'][-10:]}.ogg"
    try:
        tg.download(v["file_id"], str(p))
        txt = transcribe(p)
    except Exception as e:
        return tg.say(f"🎙 Awaaz se text nahi bana: {str(e)[:150]}\n(Likh kar bhej dein.)")
    finally:
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass
    tg.say(f"🎙 Aapne kaha: \"{txt[:300]}\"\n(isi ko hukum maan raha hoon)")
    state.update("voice_count", lambda n: (n or 0) + 1, 0)
    return handler(txt)


YT_RX = re.compile(r"(?:youtube\.com/(?:shorts/|watch\?v=)|youtu\.be/)([A-Za-z0-9_\-]{11})")


def competitor_angle(text):
    """Link + 'apna version' -> (brand, topic) ya None. Sirf public jaankari (title/desc/tags) - video copy nahi."""
    m = YT_RX.search(text or "")
    if not m:
        return None
    vid = m.group(1)
    from . import youtube
    from .config import BRANDS
    meta = {}
    for b in BRANDS:
        if youtube.has_login(b):
            try:
                j = requests.get("https://www.googleapis.com/youtube/v3/videos", timeout=30,
                                 params={"part": "snippet", "id": vid},
                                 headers={"Authorization": f"Bearer {youtube._access(b)}"}).json()
                it = (j.get("items") or [{}])[0].get("snippet") or {}
                if it:
                    meta = {"title": it.get("title", ""), "desc": it.get("description", "")[:600], "tags": it.get("tags", [])[:10]}
                    break
            except Exception as e:
                log(f"competitor meta: {e}")
    if not meta:
        try:                                           # bina login: oEmbed (sirf title)
            j = requests.get("https://www.youtube.com/oembed", params={"url": f"https://www.youtube.com/watch?v={vid}", "format": "json"},
                             timeout=20).json()
            meta = {"title": j.get("title", ""), "desc": "", "tags": []}
        except Exception as e:
            log(f"oembed: {e}")
    if not meta.get("title"):
        return None
    low = (meta["title"] + " " + meta["desc"]).lower()
    brand = ("pahadi" if any(w in low for w in ("uttarakhand", "pahad", "garhwal", "kumaon")) else
             "money" if any(w in low for w in ("sip", "loan", "emi", "tax", "invest", "paisa", "money", "bank")) else
             "deals" if any(w in low for w in ("sale", "discount", "offer", "deal", "price")) else "sunonatak")
    topic = (f"Competitor video ka VISHAY (copy nahi, apna naya original sawal aur apni kahani): '{meta['title'][:120]}'"
             + (f" | sandarbh: {', '.join(meta['tags'][:6])}" if meta.get("tags") else ""))
    return brand, topic, meta["title"]


def reframe(video_path):
    """9:16 -> 1:1 (1080x1080) + 16:9 (1920x1080): peeche wahi video dhundhla, beech mein asli. -> (sq, wide)"""
    src = pathlib.Path(video_path)
    out = []
    for name, (w, h) in (("square", (1080, 1080)), ("wide", (1920, 1080))):
        dst = src.with_name(f"{src.stem}_{name}.mp4")
        vf = (f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20:2,eq=brightness=-0.15[bg];"
              f"[0:v]scale=-2:{h}[fg];[bg][fg]overlay=(W-w)/2:0")
        r = subprocess.run(["nice", "-n", "15", "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                            "-filter_complex", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(dst)], capture_output=True, text=True, timeout=1200)
        out.append(str(dst) if r.returncode == 0 and dst.exists() else None)
        if r.returncode != 0:
            log(f"reframe {name}: {r.stderr[-200:]}")
    return tuple(out)


def reframe_latest():
    """Sabse nayi bani video ke 1:1 aur 16:9 aapko (download/doosre platform ke liye)."""
    from . import pipeline
    best = None
    for jid, j in pipeline.jobs().items():
        v = pathlib.Path(j.get("meta") or "-") / "video.mp4"
        if v.exists() and (not best or j.get("created", "") > best[0]):
            best = (j.get("created", ""), v)
    if not best:
        return tg.say("Koi bani video nahi mili.")
    sq, wide = reframe(best[1])
    for p, cap in ((sq, "🟦 1:1 (Facebook/Instagram feed)"), (wide, "🖥 16:9 (YouTube/X/website)")):
        if p and os.path.getsize(p) < 48e6:
            tg.video(p, cap)
    return "ok"
