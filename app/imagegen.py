"""AI chitra (Gemini image model) - 3D/cinematic background, taaki reel 'asli/premium' lage. Free na chale to chupchap
purana tareeka. Har chitra AI-label ke saath (description + platform flag)."""
import base64
import os
import time
import requests
from . import state
from .log import log

STYLE = ("vertical 9:16, cute 3D Pixar-style illustration, soft cinematic lighting, rich colours, high detail, "
         "Indian setting, family-friendly, NO text, NO letters, NO logos, NO real people or celebrities. Scene: ")


def _models():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return []
    c = state.get("img_models") or {}
    if time.time() - c.get("t", 0) < 86400:
        return c.get("m", [])
    try:
        j = requests.get("https://generativelanguage.googleapis.com/v1beta/models", params={"key": key, "pageSize": 200},
                         timeout=30).json()
        ms = [m["name"].split("/")[-1] for m in j.get("models", [])
              if "image" in m["name"] and "generateContent" in m.get("supportedGenerationMethods", [])]
        ms.sort(reverse=True)
    except Exception:
        ms = []
    state.put("img_models", {"t": time.time(), "m": ms})
    return ms


def make(prompt, out_path):
    if time.time() < state.get("img_block_until", 0):
        return None
    key = os.environ.get("GEMINI_API_KEY")
    import pathlib
    pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    for m in _models():
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                              params={"key": key}, timeout=120,
                              json={"contents": [{"parts": [{"text": STYLE + prompt}]}],
                                    "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}})
            j = r.json()
            if r.status_code != 200:
                log(f"img {m}: {r.status_code} {str(j)[:120]}")
                continue
            for p in j["candidates"][0]["content"]["parts"]:
                if p.get("inlineData"):
                    with open(out_path, "wb") as f:
                        f.write(base64.b64decode(p["inlineData"]["data"]))
                    state.put("img_last_model", m)
                    return out_path
        except Exception as e:
            log(f"img {m}: {e}")
    state.put("img_block_until", time.time() + 6 * 3600)        # free quota nahi: 6 ghante baad phir koshish
    return None
