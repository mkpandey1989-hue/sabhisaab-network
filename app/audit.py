"""Upload se pehle jaanch. Koi bhi ❌ ho to video aage nahi jayegi."""
from .config import BRANDS, FORBIDDEN_WORDS, AI_LABEL, SITE
from .render import probe


def description(script: dict, platform="youtube", medium="shorts") -> str:
    b = BRANDS[script["brand"]]
    page = script.get("page") or "/"
    link = f"{SITE}{page}{'&' if '?' in page else '?'}utm_source={platform}&utm_medium={medium}&utm_campaign={script['brand']}"
    short = f"{SITE}{page if page != '/' else '/'}"          # pehli line chhoti aur poori dikhe (See more se pehle)
    parts = [f"👉 {short} (free calculator)", "📢 https://t.me/sabhisaab", "",
             script["title"], "", script.get("description", "").strip(), "",
             f"🔗 Poora hisaab: {link}", cross_links(script["brand"], platform), "",
             ("#ad — is post mein affiliate link hai (khareed par hamein commission mil sakta hai)"
              if script.get("affiliate") else None),
             b["footer"], AI_LABEL, "", b["tags"]]
    from .guardtext import clean                 # v2.0.2: ginti + poora link + naam - aakhri jaanch
    return clean("\n".join(p for p in parts if p is not None).replace("\n\n\n", "\n\n").strip())


def run(meta: dict) -> list:
    checks = []
    ok = lambda c, m: checks.append(("✅" if c else "❌", m))
    b = BRANDS[meta["brand"]]
    page = meta.get("page") or "/"
    if page != "/":                       # v1.8: page ka link khulta hai? nahi to homepage (toota link kabhi nahi)
        lk = link_ok(f"{SITE}{page}")
        if lk is False:
            meta["page_broken"] = page
            meta["page"] = "/"
    ok(meta.get("page", "/") == "/" or not meta.get("page_broken"),
       "Website link khulta hai" + (f" (toota {meta['page_broken']} -> homepage)" if meta.get("page_broken") else ""))
    desc = description(meta)
    all_text = " ".join([meta["title"], desc] + [s["show"] + " " + (s.get("say") or "") for s in meta["scenes"]]).lower()
    bad = [w for w in FORBIDDEN_WORDS if w in all_text]
    ok(not bad, "Owner ka naam kahin nahi" if not bad else f"Naam mila: {bad}")
    ok(b["footer"].lower() in desc.lower(), f"Brand line: {b['footer']}")
    ok(AI_LABEL.lower() in desc.lower(), "AI label description mein")
    ok("sabhisaab.com" in desc, "Website link + UTM")
    if meta["brand"] == "deals" and meta.get("affiliate"):
        ok("#ad" in desc.lower(), "#ad (ASCI)")
    v = probe(meta["video"], "stream=codec_type,width,height:format=duration,size")
    vs = [s for s in v.get("streams", []) if s.get("codec_type") == "video"]
    au = [s for s in v.get("streams", []) if s.get("codec_type") == "audio"]
    long_v = meta.get("format") == "long"
    want = (1920, 1080) if long_v else (1080, 1920)
    ok(bool(vs) and (vs[0].get("width"), vs[0].get("height")) == want, f"{want[0]}x{want[1]} HD")
    ok(bool(au), "Awaaz maujood")
    dur = meta.get("duration", 0)
    ok((90 <= dur <= 1500) if long_v else (10 <= dur <= 180),
       f"Lambai {dur:.0f}s ({'lambi video 1.5-25 min' if long_v else 'Shorts 10-180s'})")
    size_mb = int(v.get("format", {}).get("size", 0)) / 1e6
    ok(size_mb < 200, f"Size {size_mb:.1f} MB")
    long_lines = [s["show"] for s in meta["scenes"] if len(s["show"]) > 140]
    if long_v:
        meta.setdefault("tags", [])
    ok(not long_lines, "Har scene ka text chhota aur padhne layak")
    ok(len(meta.get("thumbs", [])) == 3, "3 thumbnail bane")
    from .guardtext import stale_count, LINK_RX          # v2.0.2: purani ginti / adhoora link kabhi nahi
    pub = " ".join([meta["title"], desc] + [s["show"] for s in meta["scenes"]])
    ok(not stale_count(pub), "Tool ginti website jaisi (" + str(tool_count() or "?") + ")")
    ok(all(m.group(0).startswith("https://sabhisaab.com/") for m in LINK_RX.finditer(desc)), "Har link poora https://sabhisaab.com/")
    return checks


def passed(checks) -> bool:
    return all(c[0] == "✅" for c in checks)



def cross_links(brand, platform):
    """Har post/caption: 1) poora website link (tool ginti website se, apne aap) 2) Telegram + WhatsApp
    3) baaki brands ke channel - jis platform par dekh rahe usi ke (wahan link khulta hai), us brand ka nahi."""
    from .config import BRANDS, LINKS, HANDLES, TELEGRAM, WHATSAPP
    others = [k for k in BRANDS if k != brand and k in LINKS]
    if platform == "instagram":
        o = " ".join(f"@{HANDLES[k]}" for k in others)
    else:
        pf = platform if platform in ("youtube", "facebook", "threads") else "youtube"
        o = " | ".join(LINKS[k][pf] for k in others)
    n = tool_count()
    return (f"🧮 {str(n) + ' ' if n else ''}free calculator: https://sabhisaab.com/?utm_source={platform}&utm_campaign={brand}\n"
            f"📢 Telegram: {TELEGRAM}\n💬 WhatsApp: {WHATSAPP}\n🤝 Hamare aur channel: {o}")


def tool_count():
    """Website par abhi kitne tool hain - website se roz ek baar ginti (page badhe/ghate to bot apne aap wahi likhe)."""
    import datetime
    import re
    import requests
    from . import state
    c = state.get("site_tools") or {}
    today = str(datetime.date.today())
    if c.get("day") == today:
        return c.get("n")
    n = None
    try:
        from .config import DATA
        f = DATA / "site_repo" / "site" / "tools.js"
        txt = f.read_text(encoding="utf-8") if f.exists() else requests.get(SITE + "/tools.js", timeout=20).text
        n = len(re.findall(r"\{id:'[A-Za-z0-9_-]+',cat:", txt)) or None
    except Exception:
        n = c.get("n")
    state.put("site_tools", {"day": today, "n": n})
    return n


def link_ok(url):
    """Link sach mein khulta hai? (404 wala link kabhi post nahi)."""
    import requests
    try:
        r = requests.get(url, timeout=20, allow_redirects=True, headers={"User-Agent": "SabhisaabBot-LinkCheck/1.8"})
        return r.status_code not in (404, 410)     # sirf "page hai hi nahi" = toota; login-wall/bot-block (4xx/5xx) toota nahi
    except Exception:
        return None          # network ki dikkat: rokna nahi, sirf note
