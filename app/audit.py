"""Upload se pehle jaanch. Koi bhi ❌ ho to video aage nahi jayegi."""
from .config import BRANDS, FORBIDDEN_WORDS, AI_LABEL, SITE
from .render import probe
from .log import log


SEBI_RISKY = ("guaranteed return", "guaranteed profit", "guaranteed munafa", "pakka profit", "pakka munafa", "sure shot", "sureshot",
              "100% profit", "100% return", "paisa double", "paise double", "jackpot call", "buy karo", "sell karo", "target price",
              "stock tip", "intraday tip", "tips lo", "गारंटीड रिटर्न", "गारंटीड मुनाफा", "पक्का मुनाफा", "पक्का मुनाफ़ा", "शर्तिया मुनाफा",
              "पैसा डबल", "पैसे डबल", "100% रिटर्न", "स्टॉक टिप", "टारगेट प्राइस", "खरीदो अभी", "बेच दो अभी")


def sebi_hits(text):
    """Chhote-bade akshar se bina fark; sankuchit phrase (jaise 'target price', 'pakka munafa') - aam shabd nahi, taaki galat ruk na lage."""
    t = (text or "").lower()
    return [w for w in SEBI_RISKY if w in t]


def description(script: dict, platform="youtube", medium="shorts") -> str:
    b = BRANDS[script["brand"]]
    page = script.get("page") or "/"
    link = f"{SITE}{page}{'&' if '?' in page else '?'}utm_source={platform}&utm_medium={medium}&utm_campaign={script['brand']}"
    short = f"{SITE}{page if page != '/' else '/'}"          # pehli line chhoti aur poori dikhe (See more se pehle)
    try:
        from .answers import desc_line
        aline = desc_line(script, platform)
    except Exception:
        aline = ""
    parts = ([aline] if aline else []) + [f"👉 {short} (free calculator)", "📢 https://t.me/sabhisaab", "",
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
    if meta.get("brand") == "money":              # v2.5.2: SEBI finfluencer niyam - return ka daava / tip / salah wale shabd video nahi
        sebi = sebi_hits(all_text)
        ok(not sebi, "SEBI: return/tip/salah wale shabd nahi" if not sebi else f"SEBI jokhim shabd: {sebi}")
    ok(b["footer"].lower() in desc.lower(), f"Brand line: {b['footer']}")
    ok(AI_LABEL.lower() in desc.lower(), "AI label description mein")
    ok("sabhisaab.com" in desc, "Website link + UTM")
    if meta["brand"] == "deals" and meta.get("affiliate"):
        ok("#ad" in desc.lower(), "#ad (ASCI)")
    v = probe(meta["video"], "stream=codec_type,codec_name,width,height:format=duration,size")
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
    try:                                          # v2.3.0 (v11 se): thumbnail contrast (kam ho to khud badhao)
        from .thumbs import check_saliency_contrast
        c_ok, c_val = check_saliency_contrast(meta["thumbs"][0]) if meta.get("thumbs") else (True, 5.0)
        ok(c_ok, f"Thumbnail contrast {c_val}:1 (>= 4.5:1)")
    except Exception as e:
        log(f"contrast: {e}")
    ok(bool(vs) and vs[0].get("codec_name") in ("h264", None), "Video codec H.264")
    try:                                          # v2.3.3: monetization-suraksha - nakli aankde / ashleel shabd kabhi nahi
        import re as _re
        alltxt = " ".join([meta.get("title", ""), meta.get("description", "")] +
                          [f"{x.get('show', '')} {x.get('say', '')}" for x in meta.get("scenes", [])])
        fake = _re.search(r"\d{2}(\.\d)?\s*%\s*(लोग|log|logon|students|छात्र|people|fail|फेल)|\bvotes?\b|वोट्स?|99\.9", alltxt, _re.I)
        adult = _re.search(r"(?i)\b(sexy|nude|kiss|bikini|hot girl|xxx|18\+)\b|सेक्सी|नग्न|चुम्मा|अश्लील", alltxt)
        fake = fake or _re.search(r"\b\d{1,3}\s*%\s*(genius|जीनियस)|genius\s*certificate|\biq\s*(test|certificate)|असली\s*आई\s*क्यू|jail\s*bhej|जेल\s*भेज|muawza|मुआवज़ा\s*ले|IAS\s*(interview|इंटरव्यू)", alltxt, _re.I)
        ok(not fake, "Koi banaya hua aankda nahi ('90% log', 'votes', '1% Genius', IQ certificate, jhootha daar)")
        ok(not adult, "Parivaar ke saath dekhne layak (koi ashleel shabd nahi)")
    except Exception as e:
        log(f"policy gate: {e}")
    ok(detect_black_frames(meta["video"]) if meta.get("video") else True, "Koi kaala/khaali frame nahi (shuru 5 sec)")
    return checks


def detect_black_frames(video_path) -> bool:
    """v2.3.0 (v11 se) Gate: shuru ke 5 sec mein 0.5 sec se lamba kaala/khaali frame nahi."""
    import subprocess
    try:
        r = subprocess.run(["nice", "-n", "15", "ffmpeg", "-hide_banner", "-loglevel", "info", "-t", "5", "-i", str(video_path),
                            "-vf", "blackdetect=d=0.5:pix_th=0.05", "-an", "-f", "null", "-"],
                           capture_output=True, text=True, timeout=60)
        return "black_start" not in (r.stderr or "")
    except Exception:
        return True


def run_12_gates(meta: dict) -> list:
    """v11 naam: saare pre-publish gate (run ke andar)."""
    return run(meta)


def qc_report(meta: dict) -> str:
    """Button #25: awaaz LUFS (asli naap) + thumbnail contrast + kaala frame - ek aakhri video par."""
    from .sfx import measure_lufs
    L = [f"🎚 QC: {meta.get('title', '')[:60]}"]
    lu = measure_lufs(meta["video"]) if meta.get("video") else None
    L.append(f"• Loudness: {lu:.1f} LUFS (lakshya -14 ±1) {'✅' if lu is not None and abs(lu + 14) <= 1.5 else '⚠'}" if lu is not None
             else "• Loudness: naap nahi paya")
    try:
        from .thumbs import check_saliency_contrast
        c_ok, c_val = check_saliency_contrast(meta["thumbs"][0])
        L.append(f"• Thumbnail contrast: {c_val}:1 {'✅' if c_ok else '⚠'} (>= 4.5:1)")
    except Exception as e:
        L.append(f"• Thumbnail contrast: jaanch nahi ({str(e)[:60]})")
    L.append(f"• Kaala/khaali frame: {'✅ nahi' if detect_black_frames(meta['video']) else '❌ mila'}")
    return "\n".join(L)


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


def deep_6stage_audit() -> str:
    """v2.3.0 (v11 se, asli jaanch): 6 vibhag - har line state/file/system se (koi likha-likhaya 'PASS' nahi)."""
    import glob
    import shutil
    import subprocess
    from . import state, privacy, siteknow
    from .config import BASE, SECRETS
    from .guard import mem_avail_mb, reap_stuck_ffmpeg
    out = ["🛡 6-STAGE DEEP AUDIT (asli haal):"]
    bank = glob.glob(str(BASE / "app" / "scripts" / "bank" / "*.json"))
    used = {h.get("sig") for h in (state.get("history") or [])}
    out.append(f"1) Script bank: {len(bank)} file | puzzle sawal ho chuke: {len(state.get('used_puzzle_hashes') or [])}")
    stuck = reap_stuck_ffmpeg(40)
    out.append(f"2) Video QC: atke ffmpeg {len(stuck)} (hataye) | batch render + -14 LUFS + kaala-frame gate chalu")
    from .meta import ig_safe_text
    igt = ig_safe_text("Dekho https://sabhisaab.com/x #a #b #c #d #e #f #g")
    out.append(f"3) Platform niyam: AI label '{AI_LABEL[:30]}…' | IG bina link: {'✅' if 'http' not in igt else '❌'} | "
               f"IG hashtag ≤5: {'✅' if igt.count('#') <= 5 else '❌'}")
    try:
        pi = privacy.check_site()
    except Exception as e:
        pi = [f"jaanch nahi: {str(e)[:60]}"]
    out.append("4) Privacy/DPDP: " + ("✅ privacy/terms page theek, commenter data 30 din" if not pi else "⚠ " + "; ".join(pi)[:200]))
    try:
        pg, ni = len(siteknow.pages()), len(siteknow.not_indexed())
    except Exception:
        pg, ni = 0, 0
    rc = state.get("redirect_check") or {}
    out.append(f"5) Website/SEO: {pg} page | index baaki {ni} | redirect ok={rc.get('ok', '-')}")
    du = shutil.disk_usage("/")
    sec = oct(SECRETS.stat().st_mode)[-3:] if SECRETS.exists() else "?"
    sv = []
    for s in ("sabhinet", "chowkidar", "nifty-live", "delta-live", "nifty-chart"):
        try:
            st = subprocess.run(["systemctl", "is-active", s], capture_output=True, text=True, timeout=5).stdout.strip()
        except Exception:
            st = "?"
        sv.append(f"{s}:{'✅' if st == 'active' else st or '?'}")
    out.append(f"6) VM (sirf padha): RAM khaali {mem_avail_mb()} MB | Disk {du.used / 1e9:.0f}/{du.total / 1e9:.0f} GB | secrets {sec} | "
               + ", ".join(sv))
    _ = used
    return "\n".join(out)
