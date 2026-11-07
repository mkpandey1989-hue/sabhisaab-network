"""v2.2.0 (3 Nov 2026): SAMPLE STUDIO - har channel ka NAMOONA dekh kar look pakka karna.

Owner ka hukum: video + thumbnail ka namoona bane, dekh kar 'mitao' bolun to turant mite, 'agla' bolun to alag look ka
naya namoona (pichhla turant mitta), sab theek lage tabhi 'pakka' (dohri pushti). Har channel ka alag.
Niyam (ROADMAP 10): namoona KABHI post nahi hota. 'Isi ko daalo' dabane par hi normal manzoori line mein jaata hai,
aur wahan bhi aapke button ke bina upload nahi (reason aapka hai, autopilot ka nahi).
"""
import datetime
import json
import pathlib
import shutil

from . import state, tg
from .config import BRANDS, SITE
from .log import log

LOOKS = [
    {"name": "Premium Neon + Seedha", "style": ""},
    {"name": "Kahani andaaz", "style": "chhoti kahani ke andaaz mein, ek aam kirdaar ke saath; end mein tool se hisaab"},
    {"name": "Quiz / sawal-jawab", "style": "shuru mein ek sawal jis par dekhne wala ruk kar soche, phir jawab step by step"},
    {"name": "Myth vs Fact", "style": "ek aam galatfehmi vs sach, 3 saaf point mein"},
    {"name": "Top-3 tez tips", "style": "tez raftaar, 3 numbered tips, har scene chhota aur punchy"},
]
# v2.3.0 Step 2 (v11 ke 9 visual style) - har ek Studio ka look; pakka karne par roz ki video isi rang-roop mein
from .config import VISUAL_STYLES, VISUAL_NAMES
LOOKS += [{"name": f"Visual: {VISUAL_NAMES.get(v, v)}", "style": "", "visual": v} for v in VISUAL_STYLES if v != "auto"]
LOOKS += [{"name": "Purana classic (bina neon)", "style": "", "visual": "classic"}]


def brand_buttons():
    return tg.inline([[(v["name"], f"sm:b:{k}:0")] for k, v in BRANDS.items()])


def approved(brand):
    """Owner ka pakka kiya hua look (ya None)."""
    return (state.get("brand_look") or {}).get(brand)


def buttons(jid):
    return tg.inline([[("👍 Thumb 1", f"sm:t:{jid}:1"), ("👍 Thumb 2", f"sm:t:{jid}:2"), ("👍 Thumb 3", f"sm:t:{jid}:3")],
                      [("🎨 Naye thumbnail", f"sm:n:{jid}"), ("➡️ Agla namoona", f"sm:x:{jid}")],
                      [("🗑 Mitao", f"sm:d:{jid}"), ("✅ Ye look pakka", f"sm:f:{jid}")],
                      [("📤 Isi ko daalo (manzoori line)", f"sm:p:{jid}")]])


def _mids(res):
    out = []
    for r in (res if isinstance(res, list) else [res]):
        if isinstance(r, dict) and r.get("message_id"):
            out.append(r["message_id"])
    return out


def _remember(jid, mids):
    from . import pipeline
    j = pipeline.jobs().get(jid)
    if j is not None:
        j["mids"] = (j.get("mids") or []) + list(mids)
        pipeline.save_job(jid, j)


def make(brand, n=0):
    """Naya namoona (n = kaun sa look). Kabhi post nahi."""
    from . import pipeline
    look = LOOKS[n % len(LOOKS)]
    st = state.get("studio") or {}
    st[brand] = {"n": n, "t": datetime.datetime.now().isoformat()[:16]}
    state.put("studio", st)
    from .writer import QUIZ_STYLE                # v2.3.3: namoona bhi SAWAL wala (purani kahani-reel kabhi nahi)
    return pipeline.prepare(brand, None, "namoona", style=QUIZ_STYLE + ("; " + look["style"] if look["style"] else ""),
                            sample={"n": n, "look": look["name"], "visual": look.get("visual", "")})


def preview_text(meta, look_name, n, checks):
    """Kahan kya jayega - har platform ka asli niyam (koi link galat jagah nahi)."""
    from . import audit
    from .meta import ig_safe_text
    b = BRANDS[meta["brand"]]
    page = meta.get("page") or "/"
    yt = audit.description(meta).splitlines()
    cap = meta.get("description") or meta.get("title", "")
    try:
        ig = ig_safe_text(cap).splitlines()[0][:110]
    except Exception:
        ig = "(link nahi) 🔗 link bio mein"
    fin = " | 📜 SEBI disclaimer" if meta["brand"] == "money" else ""
    return (f"🧪 NAMOONA #{n + 1} — {b['name']} — look: {look_name}\n"
            f"🔒 Ye kahin POST NAHI hoga.\n\n"
            f"📝 {meta['title']}\n⏱ {meta.get('duration', 0):.0f} sec | ✅ audit {sum(1 for c, _ in checks if c == '✅')}/{len(checks)}\n\n"
            f"📍 Video + thumbnail par likha: {_full(meta)} (safe jagah mein)\n"
            f"🔗 Page: {SITE}{page}\n"
            f"▶️ YouTube: title + description (link clickable) — pehli line: {yt[0][:90] if yt else '-'}\n"
            f"📘 Facebook / 🧵 Threads / ✈️ Telegram: page link ke saath\n"
            f"📸 Instagram: koi link nahi → \"{ig}\"\n"
            f"📌 Pinterest: pin ka link → {SITE}{page}\n"
            f"🤖 AI label: haan{fin} | owner ka naam: kahin nahi\n\n"
            f"Dekh kar chunein 👇 (👍 = pasand note, pakka nahi; ✅ = dohri pushti ke baad pakka)")


def _full(meta):
    try:
        from .design import full_url
        return full_url(meta)
    except Exception:
        return SITE + "/"


def send(jid, meta, checks, sample):
    """prepare() ke aakhir mein (namoona): video + 3 thumbnail + 'kahan kya jayega' + studio buttons."""
    mids = []
    try:
        mids += _mids(tg.video(meta["video"], f"🧪 NAMOONA (post nahi hoga) | {meta['title'][:80]}", meta["thumbs"][0],
                               tg.inline([[("⬇️ Download (original file)", f"dl:{jid}")]])))      # v2.5.4: video par sirf ek button
    except Exception as e:
        tg.say(f"⚠️ Video preview nahi gaya (network): {str(e)[:120]}")
    try:
        mids += _mids(tg.photos(meta["thumbs"], "🖼 Thumb 1 / 2 / 3 (namoona)"))
    except Exception as e:
        log(f"studio photos: {e}")
    mids += _mids(tg.say(preview_text(meta, sample.get("look", ""), int(sample.get("n", 0)), checks), buttons(jid)))
    _remember(jid, mids)


def wipe(jid, say=True):
    """Namoona turant mitao: VM ki file + Telegram ke message (video, thumbnail, card). Wapas nahi aata."""
    from . import pipeline
    j = pipeline.jobs().get(jid)
    if not j or j.get("status") != "sample":
        return "Ye namoona ab nahi hai (pehle hi mit gaya ya manzoori line mein chala gaya)."
    for mid in j.get("mids") or []:
        tg.delete(tg._chat(), mid)
    try:
        from .config import BASE
        d = pathlib.Path(j.get("meta") or "")
        if j.get("meta") and d.is_dir() and str(d.resolve()).startswith(str(BASE.resolve()) + "/") and len(d.resolve().parts) > 4:
            shutil.rmtree(d, ignore_errors=True)          # sirf isi namoone ka folder (bot ke andar)
    except Exception as e:
        log(f"studio wipe: {e}")
    state.update("jobs", lambda dd: {k: v for k, v in (dd or {}).items() if k != jid}, {})
    from . import diary
    try:
        diary.add("namoona", f"{BRANDS[j['brand']]['name']}: namoona mitaya ({j.get('title', '')[:60]})")
    except Exception:
        pass
    return "🗑 Namoona mita diya (video, thumbnail, message aur VM ki file)." if say else ""


def like(jid, k):
    from . import pipeline
    j = pipeline.jobs().get(jid)
    if not j or j.get("status") != "sample":
        return "Ye namoona ab nahi hai."
    try:
        variants = json.loads((pathlib.Path(j["meta"]) / "thumbs.json").read_text())
        v = variants[int(k) - 1]
    except Exception:
        return "Thumbnail ki jaankari nahi mili."
    j["liked"] = int(k)
    pipeline.save_job(jid, j)
    return (f"👍 Thumb {k} pasand note kiya ({v.get('layout', '').replace('L_', '')}, rang {v.get('palette', '')}). "
            "Abhi pakka nahi — '✅ Ye look pakka' dabane par hi.")


def new_thumbs(jid):
    from . import pipeline
    from .thumbs import make as mk
    import time
    j = pipeline.jobs().get(jid)
    if not j or j.get("status") != "sample":
        return tg.say("Ye namoona ab nahi hai.")
    meta = json.loads((pathlib.Path(j["meta"]) / "meta.json").read_text())
    t = dict(meta.get("thumb") or {"lines": [meta["title"]]}, emoji="")
    if meta.get("design") == "neon_quiz":           # v2.3.2: namoone ke naye thumbnail bhi neon
        from . import design as _DS
        k0 = int(time.time()) % 97
        meta["thumbs"] = [str(_DS.thumbnail(meta, pathlib.Path(j["meta"]) / f"thumb_n{k0}_{k}.jpg", k0 + k)) for k in range(3)]
    else:
        meta["thumbs"] = [str(p) for p in mk(meta["brand"], t, j["meta"], meta["title"] + str(time.time()))]
    (pathlib.Path(j["meta"]) / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    mids = _mids(tg.photos(meta["thumbs"], "🎨 Naye thumbnail (namoona)"))
    mids += _mids(tg.say("Kaun sa pasand? 👇", buttons(jid)))
    _remember(jid, mids)


def nxt(jid):
    """Agla namoona: pichhla turant mitta, phir agla look."""
    from . import pipeline
    j = pipeline.jobs().get(jid) or {}
    brand = j.get("brand") or ((state.get("studio") or {}).get("_last") or "sunonatak")
    n = int((j.get("sample") or {}).get("n", (state.get("studio") or {}).get(brand, {}).get("n", 0))) + 1
    lk24 = (j.get("sample") or {}).get("look24")
    if lk24:                                      # v2.3.3: 24-look namoona -> agla 24-look
        from .puzzles import LOOK24
        ks = list(LOOK24)
        nx = ks[(ks.index(lk24) + 1) % len(ks)] if lk24 in ks else ks[0]
        wipe(jid, say=False)
        tg.say(f"➡️ Pichhla mita diya. Agla look: {LOOK24[nx]} (3D ke saath 3-8 min)...")
        return make_look(brand, nx)
    wipe(jid, say=False)
    tg.say(f"➡️ Pichhla namoona mita diya. Agla look: {LOOKS[n % len(LOOKS)]['name']} (2-6 min)...")
    return make(brand, n)


def finalize_ask(jid):
    from . import pipeline
    j = pipeline.jobs().get(jid)
    if not j or j.get("status") != "sample":
        return tg.say("Ye namoona ab nahi hai.")
    look = (j.get("sample") or {}).get("look", "")
    k = j.get("liked") or 1
    return tg.say(f"⚠️ Dobara pakka? {BRANDS[j['brand']]['name']} ki aage ki SAARI roz wali video '{look}' look mein, "
                  f"aur thumbnail ka pehla design Thumb {k} jaisa. (Badalna ho to kabhi bhi naya namoona.)",
                  tg.inline([[("✅✅ Haan, pakka", f"sm:F:{jid}"), ("❌ Nahi", "sm:z:x")]]))


def finalize(jid):
    from . import pipeline
    j = pipeline.jobs().get(jid)
    if not j or j.get("status") != "sample":
        return "Ye namoona ab nahi hai."
    smp = j.get("sample") or {}
    look = LOOKS[int(smp.get("n", 0)) % len(LOOKS)]
    v = {}
    try:
        v = json.loads((pathlib.Path(j["meta"]) / "thumbs.json").read_text())[int(j.get("liked") or 1) - 1]
    except Exception:
        pass
    rec = {"look": look["name"], "style": look["style"], "visual": look.get("visual", ""), "layout": v.get("layout", ""),
           "palette": v.get("palette", ""), "t": datetime.date.today().isoformat()}
    state.update("brand_look", lambda d: {**(d or {}), j["brand"]: rec}, {})
    try:
        from . import diary
        diary.add("niyam", f"{BRANDS[j['brand']]['name']}: look pakka '{look['name']}' + thumbnail {rec['layout']}/{rec['palette']}")
    except Exception:
        pass
    wipe(jid, say=False)
    return (f"✅ PAKKA: {BRANDS[j['brand']]['name']} — look '{look['name']}', thumbnail design pehle "
            f"({rec['layout'].replace('L_', '')}, {rec['palette']}). Agli roz wali video se laagu. Namoona mita diya.")


def promote(jid):
    """Namoona -> normal manzoori line (aapke button ke bina upload nahi)."""
    from . import pipeline
    j = pipeline.jobs().get(jid)
    if not j or j.get("status") != "sample":
        return "Ye namoona ab nahi hai."
    j["status"] = "waiting"
    j["reason"] = "aapne maanga (namoona se)"
    j["slot"] = (pipeline.now() + datetime.timedelta(minutes=30)).isoformat()
    pipeline.save_job(jid, j)
    tg.say(f"📤 {jid} ab manzoori line mein. Thumb chunein (ya 🚀 Abhi daalo). Aapke button ke bina kahin nahi jayegi.",
           pipeline.job_buttons(jid))
    return ""


def cleanup(days=1):
    """Bhoole hue namoone 1 din baad apne aap mitao (disk saaf)."""
    from . import pipeline
    cut = (pipeline.now() - datetime.timedelta(days=days)).isoformat()
    n = 0
    for jid, j in list(pipeline.jobs().items()):
        if j.get("status") == "sample" and j.get("created", "") < cut:
            wipe(jid, say=False)
            n += 1
    return n


def status_text():
    lines = ["🧪 SAMPLE STUDIO — har channel ka pakka look"]
    for k, v in BRANDS.items():
        a = approved(k)
        lines.append(f"• {v['name']}: " + (f"'{a['look']}' + thumbnail {a.get('layout', '').replace('L_', '')} ({a['t']})"
                                            if a else "Premium Neon (naya default) chal raha - chaho to badlo"))
    lines.append("\nNaya namoona: brand chunein 👇 (kahin post nahi hoga)")
    return "\n".join(lines)


MANUAL = """📘 SAMPLE STUDIO + DIN-PLAN — MANUAL (v2.3.3)

0) NAYA DEFAULT (v2.3.0): PREMIUM NEON
• Har short video ab neon frame + kaanch card + A/B/C/D vikalp + timer + bada CTA mein (aapke bheje namoone jaisa).
• Gemini image ki seema bachi ho to peeche 3D AI chitra; warna apne neon chitra. Koi nakli '88% votes' nahi.
• Purana look chahiye: Studio mein 'Purana classic (bina neon)' → ✅ pakka.

0a) NAYA (v2.3.3) — main keyboard par: 🧪 Namoona | 🎨 24 Look | 💬 Comment haal | ⏰ Best time | 👑 Pro 50 Deck
• 🎨 24 Look → channel → ✅/⬜ chuno → '✅ Pakka karo' (dohri pushti). '🎬 Kisi look ka namoona' = us look ki reel (post nahi).
• Har reel mein apna 3D chitra (Blender, raat ko khud install). '🧊 Apna 3D' se haal; '3d band/chalu' (dohri pushti).
• 3 format baari-baari: Dil vs Dimag | Pyaar ka Hisaab | Sach ya Jhooth - sab sawal wale, parivaar ke saath dekhne layak.
• ⏰ Best time → sujhav → '✅ Ye samay lagao' → dohri pushti.

0b) ROZ 2 SAWAL-WALI REEL (v2.3.1)
• Har channel: pehli reel = Gemini ka naya sawal (4 vikalp), doosri = jaancha hua puzzle/GK (Pahadi par pahadi GK + purane shabd).
• Dono aapko Thumb 1/2/3 ke saath aati hain; aap chunein, warna slot par Thumb 1 se apne aap.

1) NAMOONA BANAO
• Menu → 🧪 Sample studio → channel chunein (ya likhein: "sample money", "namoona pahadi").
• 2-6 min mein aayega: video + 3 thumbnail + "kahan kya jayega" (har platform ka link/niyam).
• 🔒 Namoona KABHI post nahi hota.

2) DEKH KAR CHUNEIN (har button ka kaam)
• 👍 Thumb 1/2/3 — pasand note (abhi pakka nahi)
• 🎨 Naye thumbnail — usi video ke 3 naye design (naye rang/layout)
• ➡️ Agla namoona — ye wala TURANT mitta, agla alag look (14 look: Seedha, Kahani, Quiz, Myth vs Fact, Top-3 tips + 9 visual style: 3D mascot, worker chart, stick-figure mic, liquid match, mystery box, dhol, chooza, jeevit fasal, puzzle board → phir se)
• 🗑 Mitao — video, thumbnail, message aur VM ki file turant mitti
• ✅ Ye look pakka — DOHRI pushti ke baad us channel ki roz ki video isi look + pasand wale thumbnail design se
• 📤 Isi ko daalo — normal manzoori line mein (wahan bhi aapke button ke bina upload nahi)
Bhoola hua namoona 1 din baad apne aap mit jaata hai.

3) EK BAAR PAKKA = HAMESHA APNE AAP
• Pakka look + din-plan ke hisaab se bot roz slot se 3 ghante pehle video banata hai, aapko bhejta hai; jawab na mile to
  slot par Thumb 1 se khud daalta hai (autopilot). Fail ho to bank script — slot kabhi nahi chhootta.
• Look badalna ho: naya namoona → pasand → ✅ pakka (dohri pushti). Purana look tab tak chalta rahta hai.

3b) VISUAL STYLE + HUD
• Menu → 🎨 9 Visual Style → channel → style: seedha us style ka namoona.
• Menu → 🎛 HUD: neon border, progress bar, power-word rang, panchang badge - har ek band/chalu (dohri pushti).
• Timer + 'code yaad rakhein' sirf challenge/puzzle video par.

4) DIN-PLAN (kis din kya)
• Menu → 📅 Din-plan. Har channel ka har din alag andaaz (sawal / kahani / myth / tips / galtiyan / 10-sec challenge / Ravivaar recap).
• Pahadi: Somvaar GK, Budhvaar purane naam, Shukravaar pahadi shabd (180 din tak koi vishay dohraaya nahi).
• Badlo: "somvaar money: kahani" → dohri pushti. Band/chalu: "din plan band" / "din plan chalu" (dohri pushti).

5) KOI SAWAL DOHRAAYA NAHI
• Har nayi script ko us channel ke pichhle 60 title + 40 sawal dikhaye jaate hain: "inhe mat dohraao".
• 90 din mein milta-julta title + channel par asli title bhi jaancha jaata hai. Bank ki script ek baar hi.

6) KAHAN KYA JAATA HAI (niyam)
• Roz 4 channel x (YouTube, Facebook, Instagram, Threads, Pinterest, Telegram). YouTube par din mein max 6 upload (API seema).
• Instagram par koi link nahi ("link bio mein"); baaki jagah page ka link. Video par https://sabhisaab.com/ safe jagah.
• AI label har jagah; Money par SEBI disclaimer; aapka naam/pata kahin nahi; commenter ka data 30 din mein saaf.
"""


# ---------------- v2.3.0 Step 2: 9 visual style ki list + HUD setting (dohri pushti) ----------------
HUD_PARTS = {"neon": "Neon border", "progress": "Upar progress bar", "power_words": "Power-word rang", "panchang": "Panchang badge"}


def styles_text():
    L = ["🎨 9 VISUAL STYLE (v11 se) — har ek ka namoona Studio mein (post nahi hota):"]
    for i, v in enumerate([x for x in VISUAL_STYLES if x != "auto"], 1):
        L.append(f"{i}) {VISUAL_NAMES.get(v, v)}")
    L.append("\nNiche channel + style chunein → namoona aayega → pasand aaye to '✅ Ye look pakka'.")
    return "\n".join(L)


def style_buttons(brand):
    vis = [x for x in VISUAL_STYLES if x != "auto"]
    idx = {lk.get("visual"): i for i, lk in enumerate(LOOKS) if lk.get("visual")}
    rows, row = [], []
    for v in vis:
        row.append((VISUAL_NAMES.get(v, v)[:20], f"sm:b:{brand}:{idx[v]}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return tg.inline(rows)


def hud_text():
    h = state.get("hud") or {}
    L = ["🎛 VIDEO HUD (v11 se) — har video par:"]
    for k, nm in HUD_PARTS.items():
        L.append(f"• {nm}: {'CHALU' if h.get(k, True) else 'BAND'}")
    L.append("• Timer + chhupa code: sirf challenge/puzzle video par (sach rehne ke liye)")
    L.append("Badlo: 'hud neon band' / 'hud progress chalu' / 'hud power band' / 'hud panchang band' (dohri pushti)")
    return "\n".join(L)


def hud_parse(tl):
    import re
    m = re.match(r"^hud\s+(neon|progress|power|panchang)\s+(band|chalu)$", tl.strip())
    if not m:
        return None
    k = {"power": "power_words"}.get(m.group(1), m.group(1))
    return k, m.group(2) == "chalu"


def hud_apply(k, on):
    state.update("hud", lambda d: {**(d or {}), k: bool(on)}, {})
    return f"✅ {HUD_PARTS[k]}: {'CHALU' if on else 'BAND'} (agli video se)."



# ---------------- v2.3.3: owner ke 24 PRO-ELITE look - har channel par chunna (dohri pushti) + har look ka namoona ----------------
def make_look(brand, look):
    """Ek 24-look ka namoona (asli sawal kharch nahi hota). Kabhi post nahi."""
    from . import pipeline, puzzles
    keep = {k: state.get(k) for k in ("used_puzzle_hashes", "reel_codes", "last_puzzle_kind", "looks24", "look_day")}
    try:
        state.put("looks24", {**(state.get("looks24") or {}), brand: [look]})
        state.put("used_puzzle_hashes", [])
        sc = puzzles.generate_puzzle("elite24", brand)
    finally:
        for k, v in keep.items():
            state.put(k, v)
    nm = puzzles.LOOK24.get(look, look)
    return pipeline.prepare(brand, None, "namoona", None, "short", "", {"n": 0, "look": nm, "visual": "", "look24": look}, sc)


def looks_menu(brand):
    from .puzzles import LOOK24, looks_for
    draft = (state.get("looks24_draft") or {}).get(brand)
    on = set(draft if draft is not None else looks_for(brand))
    rows, row = [], []
    for k, nm in LOOK24.items():
        row.append((("✅ " if k in on else "⬜ ") + nm.split(" (")[0][:16], f"s24:t:{brand}:{k}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([("🎬 Kisi look ka namoona", f"s24:sm:{brand}"), ("✅ Pakka karo", f"s24:f:{brand}")])
    rows.append([("☑️ Sab chuno", f"s24:all:{brand}"), ("⬜ Sab hatao", f"s24:none:{brand}")])
    return tg.inline(rows)


def looks_text(brand):
    from .puzzles import looks_for
    return (f"🎨 24 PRO-ELITE LOOK — {BRANDS[brand]['name']}\nAbhi chalu: {len(looks_for(brand))}/24. ✅ = roz ki paheli-reel mein aayega.\n"
            "Tap karke chuno/hatao → '✅ Pakka karo' (dohri pushti). Har look ka 3D chitra + pakka sawal.")


def sample_look_buttons(brand):
    from .puzzles import LOOK24
    return tg.inline([[(nm.split(" (")[0][:20], f"s24:s:{brand}:{k}")] for k, nm in LOOK24.items()])


def best_hours(brand):
    """Asli views (har ghante ka ausat) + Bharat ke aam peak (12:30-14:00, 19:00-22:00) -> 2 samay."""
    from . import learn
    d = learn.load().get("views_hour") or {}
    score = {}
    for h in range(7, 23):
        base = 1.0 + (0.6 if 19 <= h <= 21 else 0) + (0.35 if 12 <= h <= 13 else 0) + (0.2 if h in (9, 18, 22) else 0)
        v = d.get(f"{h:02d}") or d.get(str(h)) or {}
        n = len(v.get("videos") or []) if isinstance(v, dict) else 0
        avg = (v.get("views", 0) / n) if n else 0
        score[h] = base + (min(2.0, avg / 100.0) if n >= 2 else 0)
    eve = max((h for h in range(18, 23)), key=lambda h: score[h])
    day = max((h for h in range(11, 16)), key=lambda h: score[h])
    return [f"{day:02d}:30", f"{eve:02d}:00"], score


def best_time_text():
    from .pipeline import schedule
    lines = ["⏰ BEST SAMAY (asli views + Bharat ka aam peak: dopahar 12-2, shaam 7-10)"]
    prop = {}
    sch = schedule()
    for i, b in enumerate(BRANDS):
        t2, _ = best_hours(b)
        h_day, h_eve = t2
        hd = int(h_day[:2]) + (i % 2)           # channel aapas mein na takrayein
        he = int(h_eve[:2]) + (i % 3 == 2)
        prop[b] = f"{min(hd, 15):02d}:{['30', '00', '45', '15'][i]},{min(he, 22):02d}:{['00', '30', '15', '45'][i]}"
        lines.append(f"• {BRANDS[b]['name']}: abhi {sch.get(b)} → sujhav {prop[b]} (doosra = paheli/3D reel)")
    state.put("best_time_pending", prop)
    lines.append("\n'✅ Ye samay lagao' dabane par dohri pushti; phir bot roz isi par (aap kabhi bhi badal sakte ho).")
    return "\n".join(lines)



# ---------------- v2.3.6: bot khud naye rang/design aazmata hai -> namoona -> aapki haan (ya 24 ghante baad apne aap) ----------------
def propose_palette():
    """Hafte mein ek baar: abhi tak na aazmaya rang -> namoona (post nahi) + '✅ default mein jodo' button."""
    from . import design, pipeline, puzzles
    ok, no = set(state.get("palettes_ok") or []), set(state.get("palettes_no") or [])
    pend = state.get("palette_pending") or {}
    if pend.get("name"):
        return None
    left = [p for p in design.PALETTES if p not in ok and p not in no]
    if not left:
        return None
    name = left[0]
    b = list(BRANDS)[len(ok) % len(BRANDS)]
    keep = {k: state.get(k) for k in ("used_puzzle_hashes", "reel_codes", "last_puzzle_kind", "look_day")}
    try:
        state.put("used_puzzle_hashes", [])
        sc = puzzles.generate_puzzle("auto", b)
    finally:
        for k, v in keep.items():
            state.put(k, v)
    state.put("palette_pending", {"name": name, "t": __import__("time").time()})
    jid = pipeline.prepare(b, None, "namoona", None, "short", "", {"n": 0, "look": f"Naya rang: {name}", "visual": "", "palette": name}, sc)
    tg.say(f"🎨 Bot ka NAYA RANG/DESIGN namoona: '{name}' (upar). Pasand ho to default list mein jodein - "
           "24 ghante mein jawab na mila to bot khud jod dega (aap baad mein hata sakte hain).",
           tg.inline([[("✅ Default mein jodo", f"s36:pa:{name}"), ("❌ Ye rang nahi", f"s36:pr:{name}")]]))
    return jid


def palette_auto_check():
    """24 ghante tak jawab nahi -> apne aap default mein (owner ka niyam)."""
    import time as _t
    pend = state.get("palette_pending") or {}
    if pend.get("name") and _t.time() - pend.get("t", 0) > 24 * 3600:
        palette_decide(pend["name"], True, auto=True)


def palette_decide(name, yes, auto=False):
    state.put("palette_pending", None)
    key = "palettes_ok" if yes else "palettes_no"
    state.update(key, lambda L: sorted(set((L or []) + [name])), [])
    msg = (f"✅ Rang '{name}' default list mein jud gaya" + (" (24 ghante jawab nahi aaya, isliye apne aap)" if auto else "")
           + " - ab roz ki reel mein baari-baari aayega." if yes else f"👍 Rang '{name}' nahi lagega.")
    tg.say(msg)
    return msg


def palettes_text():
    from . import design
    ok = state.get("palettes_ok") or []
    return ("🎨 RANG/DESIGN LIST: channel ka apna rang + " + (", ".join(ok) if ok else "abhi koi naya nahi") +
            f"\nBaaki aazmane ko: {len([p for p in design.PALETTES if p not in ok and p not in (state.get('palettes_no') or [])])}"
            "\nBot har Ravivaar ek naya rang namoona bhejta hai. Hatana: 'rang hatao <naam>' (dohri pushti)")



def propose_layout():
    """v2.4.0: hafte mein ek baar naya LAYOUT namoona (vikalp 2x2 / bada chitra) -> haan ya 24 ghante baad apne aap."""
    from . import design, pipeline, puzzles
    ok, no = set(state.get("layouts_ok") or []), set(state.get("layouts_no") or [])
    pend = state.get("layout_pending") or {}
    if pend.get("name"):
        return None
    left = [p for p in design.LAYOUTS if p != "list" and p not in ok and p not in no]
    if not left:
        return None
    name = left[0]
    b = list(BRANDS)[(len(ok) + 1) % len(BRANDS)]
    keep = {k: state.get(k) for k in ("used_puzzle_hashes", "reel_codes", "last_puzzle_kind", "look_day")}
    try:
        state.put("used_puzzle_hashes", [])
        sc = puzzles.generate_puzzle("auto", b)
    finally:
        for k, v in keep.items():
            state.put(k, v)
    state.put("layout_pending", {"name": name, "t": __import__("time").time()})
    jid = pipeline.prepare(b, None, "namoona", None, "short", "",
                           {"n": 0, "look": f"Naya layout: {design.LAYOUTS[name]}", "visual": "", "layout": name}, sc)
    tg.say(f"🧩 Bot ka NAYA LAYOUT namoona: '{design.LAYOUTS[name]}'. Pasand ho to default mein jodein - 24 ghante mein jawab "
           "na mila to bot khud jod dega (baad mein 'layout hatao <naam>').",
           tg.inline([[("✅ Default mein jodo", f"s39:la:{name}"), ("❌ Ye layout nahi", f"s39:lr:{name}")]]))
    return jid


def layout_decide(name, yes, auto=False):
    state.put("layout_pending", None)
    state.update("layouts_ok" if yes else "layouts_no", lambda L: sorted(set((L or []) + [name])), [])
    msg = (f"✅ Layout '{name}' default list mein" + (" (24 ghante jawab nahi aaya, apne aap)" if auto else "") + " - roz baari-baari."
           if yes else f"👍 Layout '{name}' nahi lagega.")
    tg.say(msg)
    return msg


def layout_auto_check():
    import time as _t
    pend = state.get("layout_pending") or {}
    if pend.get("name") and _t.time() - pend.get("t", 0) > 24 * 3600:
        layout_decide(pend["name"], True, auto=True)


DL_MAX_MB = 49          # Telegram bot ke sendDocument ki seema (cloud API 50 MB)


def download(jid):
    """'⬇️ Download' button: wahi namoona video ORIGINAL file (document) ki tarah - compress nahi. Sirf isi namoone ki file, bot ke andar se.
    Kuch post/upload nahi hota. File Telegram par hi rehti hai; namoona 'mita do' par ye copy bhi mit jaati hai."""
    import json as _json
    from . import pipeline
    from .config import BASE
    j = pipeline.jobs().get(jid)
    if not j or not j.get("meta"):
        return tg.say("Ye namoona ab nahi hai (mit gaya ya purana ho gaya).")
    try:
        meta = _json.loads((pathlib.Path(j["meta"]) / "meta.json").read_text())
        f = pathlib.Path(meta["video"]).resolve()
    except Exception:
        return tg.say("Video file nahi mili.")
    base = str(BASE.resolve()) + "/"
    if not str(f).startswith(base) or not f.is_file() or f.suffix.lower() != ".mp4":
        return tg.say("Video file nahi mili.")
    mb = f.stat().st_size / 1048576
    if mb > DL_MAX_MB:
        return tg.say(f"Video {mb:.0f} MB hai - Telegram bot {DL_MAX_MB} MB se badi file nahi bhej sakta. VM par: {f}")
    with open(f, "rb") as fh:
        res = tg.call("sendDocument", {"chat_id": tg._chat(), "caption": f"⬇️ Original file ({mb:.1f} MB) - namoona, post nahi hoga"},
                      {"document": fh}, timeout=600)
    _remember(jid, _mids(res))
    return res
