"""v2.0.2: Har bahar jaane wale text ki aakhri jaanch (caption, description, title, scene text, thumbnail, story,
Threads, Pinterest, Telegram, WhatsApp, comment jawab, DM) - post se theek pehle, apne aap:
1) Tool ki ginti hamesha website ki ASLI ginti (188 -> 190 hue to har jagah 190). Kabhi purana number nahi.
2) Website ka link hamesha poora: https://sabhisaab.com/... (bina https wala ya adhoora kabhi nahi).
3) Owner ka naam kabhi nahi (FORBIDDEN_WORDS hata deta hai).
Bolne wale text ('say') ko nahi chhedta - wahan "सब हिसाब डॉट कॉम" sahi hai."""
import re

COUNT_RX = re.compile(r"(?<![\d₹.,/-])([1-9]\d{2})(\+?)(\s*(?:free\s+|फ्री\s+|मुफ्त\s+)?(?:hindi\s+)?"
                      r"(?:calculators?|tools?|कैलकुलेटर|टूल्स?|टूल))", re.I)
LINK_RX = re.compile(r"(?<![\w@/.])(?:https?://)?(?:www\.)?sabhisaab\.com(?![\w-])(/[^\s)\]}>\"'|,]*)?", re.I)


def count():
    try:
        from .audit import tool_count
        return tool_count()
    except Exception:
        return None


def fix_count(text, n=None):
    n = n or count()
    if not text or not n:
        return text
    return COUNT_RX.sub(lambda m: f"{n}{m.group(2)}{m.group(3)}" if int(m.group(1)) != n and 100 <= int(m.group(1)) <= 999
                        else m.group(0), text)


def fix_links(text):
    if not text:
        return text

    def _r(m):
        path = m.group(1) or "/"
        if path.startswith("/?") or path == "/":
            return "https://sabhisaab.com" + path
        return "https://sabhisaab.com" + path
    out = LINK_RX.sub(_r, text)
    return out.replace("https://sabhisaab.com?", "https://sabhisaab.com/?")


def fix_name(text):
    try:
        from .config import FORBIDDEN_WORDS
        for w in FORBIDDEN_WORDS:
            text = re.sub(re.escape(w), "", text, flags=re.I)
    except Exception:
        pass
    return text


def clean(text, n=None):
    """Public text ki aakhri safai."""
    if not isinstance(text, str):
        return text
    return fix_name(fix_links(fix_count(text, n)))


def clean_script(s):
    """Script (title, description, scene 'show', thumbnail lines, tags) - 'say' ko chhod kar."""
    n = count()
    for sc in s.get("scenes", []) or []:          # v2.0.3: "comment LINK / DM" wala bulawa kabhi nahi (Meta scam-pattern)
        blob = f"{sc.get('show', '')} {sc.get('say', '')}"
        if re.search(r"LINK|लिंक चाहिए|कमेंट में लिंक|dm\b|डीएम", blob, re.I):
            sc["show"] = "पूरा हिसाब, फ्री कैलकुलेटर: https://sabhisaab.com/"
            sc["say"] = "पूरा हिसाब, फ्री कैलकुलेटर सब हिसाब डॉट कॉम पर।"
    for k in ("title", "description"):
        if isinstance(s.get(k), str):
            s[k] = clean(s[k], n)
    for sc in s.get("scenes", []) or []:
        if isinstance(sc.get("show"), str):
            sc["show"] = clean(sc["show"], n)
    th = s.get("thumb") or {}
    if isinstance(th.get("lines"), list):
        th["lines"] = [clean(x, n) if isinstance(x, str) else x for x in th["lines"]]
    if isinstance(s.get("tags"), list):
        s["tags"] = [fix_count(t, n) if isinstance(t, str) else t for t in s["tags"]]
    return s


def stale_count(text):
    """Text mein purani ginti hai? (YouTube/FB purani post ki description sudhaarne ke liye)"""
    n = count()
    return bool(n and text and any(int(m.group(1)) != n for m in COUNT_RX.finditer(text)))


# ---------- har platform ke API par ek hi jagah laagu (koi bhi raasta chhoot na jaye) ----------
_WRAP = {
    "meta": {"post_facebook": [2], "post_instagram": [2], "ig_reply": [2], "private_reply_ig": [2], "private_reply_fb": [2]},
    "threads": {"post_text": [1]},
    "pinterest": {"post_pin": [2, 3]},
    "youtube": {"upload": [2, 3], "reply_comment": [2], "top_comment": [2]},
}
_done = False


def install():
    """Bot chalu hote hi: in sab function ke text argument par clean() apne aap (caption/comment/DM/description)."""
    global _done
    if _done:
        return
    import functools
    import importlib
    for mod, fns in _WRAP.items():
        try:
            m = importlib.import_module(f"app.{mod}")
        except Exception:
            continue
        for fn, idx in fns.items():
            f = getattr(m, fn, None)
            if not f or getattr(f, "_guarded", False):
                continue

            def make(f=f, idx=idx):
                @functools.wraps(f)
                def w(*a, **k):
                    a = list(a)
                    for i in idx:
                        if i < len(a) and isinstance(a[i], str):
                            a[i] = clean(a[i])
                    for kk in ("caption", "text", "title", "description"):
                        if isinstance(k.get(kk), str):
                            k[kk] = clean(k[kk])
                    return f(*a, **k)
                w._guarded = True
                return w
            setattr(m, fn, make())
    _done = True


def tg_clean(data):
    """Telegram channel/owner ke public post (text/caption) bhi."""
    for k in ("text", "caption"):
        if isinstance(data.get(k), str) and str(data.get("chat_id", "")).startswith("@"):
            data[k] = clean(data[k])
    return data
