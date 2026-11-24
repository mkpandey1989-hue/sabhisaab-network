"""v3.4.29 (19 Nov 2026, owner: "kaun se feature band hain, kaun approval ke bina ruke, kisme permission/set nahi - sab check karo").

'sab features' / 'feature audit' -> VM par ASLI haal (state + secrets dekh kar, andaza nahi). Har feature:
  ✅ chal raha | ⬜ band (aapka ek hukum) | 🔑 key/login/ijaazat nahi | ⏳ kisi ke intezaar/manzoori mein | 🛡️ jaanboojh kar band (suraksha)
Koi token/secret ka text kabhi nahi dikhata - sirf haan/na.
"""
import os

from . import state
from .config import BRANDS, SECRETS


def _sec(name):
    try:
        p = SECRETS / name
        return p.exists() and p.stat().st_size > 2
    except Exception:
        return False


def _env(k):
    if os.environ.get(k):
        return True
    try:
        from . import website
        return bool(website._env().get(k))
    except Exception:
        return False


def _on(key, default=False):
    v = state.get(key)
    return default if v is None else bool(v)


def _yt_comment():
    try:
        from . import ytcomment
        n = sum(1 for b in BRANDS if ytcomment.has(b))
        return n, len(BRANDS)
    except Exception:
        return 0, len(BRANDS)


def checks():
    """-> [(group, naam, status, kyun/kya karna)]"""
    R = []

    def add(g, name, st, why=""):
        R.append((g, name, st, why))

    T = "Traffic laane wale"
    add(T, "Jawab website (/jawab)", "✅" if _on("jawab_site_on") else "⬜", "" if _on("jawab_site_on") else "likho: jawab website chalu")
    add(T, "Telegram quiz poll (roz 2)", "✅" if _on("answer_poll") else "⬜", "" if _on("answer_poll") else "likho: jawab poll chalu")
    add(T, "Telegram digest (roz 20:30, sab jawab ek sandesh)", "✅" if _on("answer_digest") else "⬜",
        "" if _on("answer_digest") else "likho: jawab digest chalu")
    add(T, "FB page link-card (reel ke 3 ghante baad)", "⬜" if _on("rc_fb_off") else "✅", "likho: fb link post chalu" if _on("rc_fb_off") else "")
    add(T, "Mauka calendar (10:30 juda calculator)", "⬜" if _on("rc_mk_off") else "✅", "likho: mauka chalu" if _on("rc_mk_off") else "")
    add(T, "Share kit (19:15 WhatsApp/FB group/Quora text)", "✅" if _on("sk_on", True) else "⬜", "" if _on("sk_on", True) else "likho: share kit chalu")
    add(T, "Uttarakhand page share (18:45)", "✅" if _on("uk_share_on", True) else "⬜", "" if _on("uk_share_on", True) else "likho: uk share chalu")
    add(T, "Group post kit (FB group banner)", "✅" if _on("grp_on", True) else "⬜", "" if _on("grp_on", True) else "likho: group post chalu")
    if not _sec("onesignal.json"):
        add(T, "Website notification (OneSignal push)", "🔑", "OneSignal app id/key nahi - 'onesignal <app_id> <key>'")
    else:
        add(T, "Website notification (OneSignal push)", "✅" if _on("push_on") else "⬜", "" if _on("push_on") else "push band - 'push chalu'")
    if not _sec("pinterest.json"):
        add(T, "Pinterest pin", "🔑", "Pinterest login nahi")
    else:
        add(T, "Pinterest pin (roz seema ke andar)", "✅" if _on("pin_drip_on", True) else "⬜", "")
    add(T, "Calculator pin (tool pages)", "✅" if _on("toolpin_on", True) else "⬜", "")
    if not _sec("linkedin.json"):
        add(T, "LinkedIn (Make.com)", "🔑", "Make webhook nahi - Claude se setup")
    else:
        add(T, "LinkedIn subah 09:15", "✅" if _on("li_on", True) else "⬜", "" if _on("li_on", True) else "likho: linkedin chalu")
        add(T, "LinkedIn shaam 18:30", "✅" if _on("li_eve_on", True) else "⬜", "")
    if not _sec("dailymotion.json"):
        add(T, "Dailymotion", "🔑", "Dailymotion key nahi")
    else:
        add(T, "Dailymotion (roz max 3)", "✅" if _on("dm_on", True) else "⬜", "" if _on("dm_on", True) else "likho: dailymotion chalu")
    add(T, "Threads post", "✅" if _sec("threads.json") else "🔑", "" if _sec("threads.json") else "Threads login nahi")
    add(T, "Instagram/FB story (reel ke saath)", "✅" if _on("stories_on", True) else "⬜", "")
    add(T, "Hafte ki lambi YouTube video (description ka link click hota)", "✅" if _on("hub_week_on", True) else "⬜", "")
    if not _sec("quizbot.json"):
        add(T, "Quiz bot (@...)", "🔑", "quiz bot token nahi")
    else:
        add(T, "Quiz bot (roz sawal, /jawab)", "✅", "")
        inl = state.get("quizbot_inline")
        add(T, f"Quiz bot inline share (@{state.get('quizbot_user') or 'bot'} kisi bhi chat mein)", "✅" if inl else "⏳",
            "" if inl else "BotFather → /setinline → @" + (state.get("quizbot_user") or "quiz bot") + " → 'sawal ya code likhein'")
    gq = state.get("gq_chat")
    add(T, "Telegram group quiz (A/B/C/D reply + score)", "✅" if gq else "⏳", "" if gq else "Discussion group mein /quizgroup bhejo")
    pq = _on("pq_on")
    add(T, "Uttarakhand page queue (roz naye page)", "✅" if pq else "⬜", "" if pq else "likho: queue chalu")

    C = "Comment / jawab"
    n, tot = _yt_comment()
    add(C, f"YouTube comment par jawab-link ({n}/{tot} channel)", "✅" if n == tot else ("🔑" if n == 0 else "⏳"),
        "" if n == tot else "likho: yt comment login")
    add(C, "FB/IG comment ka apne aap jawab", "✅" if _on("auto_reply", True) else "⬜", "" if _on("auto_reply", True) else "likho: auto jawab chalu")
    add(C, "Instagram private reply (DM mein link)", "🛡️" if not _on("ig_private_reply_on") else "✅",
        "Jaanboojh kar band - privacy policy sec.8; chahiye to Claude se (privacy line + niyam)" if not _on("ig_private_reply_on") else "")
    add(C, "Vote % counter (/jawab par asli %)", "✅" if _on("votes_on") else ("⬜" if _sec("votes.json") else "🔑"),
        "" if _on("votes_on") else ("likho: vote chalu" if _sec("votes.json") else "Cloudflare Worker banana hai - likho: vote chalu (bot banata hai)"))

    G = "Google / naap-tol"
    add(G, "Google Search Console + Analytics", "✅" if _sec("gsc_sa.json") else "🔑", "" if _sec("gsc_sa.json") else "service account nahi")
    add(G, "Indexing suchi (11:40)", "✅" if _on("idx_on", True) else "⬜", "")
    add(G, "GSC sawal → FAQ (kwfix)", "✅" if _on("kwfix_auto", True) else "⬜", "")
    add(G, "Toote link khud theek (linkfix)", "✅" if _on("linkfix_auto", True) else "⬜", "")
    add(G, "Website speed (PageSpeed)", "✅" if _env("PSI_KEY") else "🔑", "" if _env("PSI_KEY") else "likho: psi key <Google API key>")
    add(G, "Bing API report", "✅" if _env("BING_API_KEY") else "🔑", "" if _env("BING_API_KEY") else "Bing Webmaster API key nahi (marzi)")
    add(G, "YouTube Analytics (har video ke views/watch time)", "✅" if _sec("yt_analytics_client.json") else "🔑",
        "" if _sec("yt_analytics_client.json") else "likho: /analytics - Desktop client jodna (steps bot deta)")
    add(G, "Scoreboard (21:50 brand x platform)", "✅" if _on("sb_on", True) else "⬜", "")
    add(G, "Gemini AI (Quora/jawab draft, samajh)", "✅" if _env("GEMINI_API_KEY") else "🔑", "" if _env("GEMINI_API_KEY") else "Gemini key nahi")

    S = "Khud-dekhbhaal"
    add(S, "Auto-doctor (05:40)", "✅" if _on("ad_on", True) else "⬜", "")
    add(S, "Auto deploy (website)", "✅" if _on("auto_deploy", True) else "⬜", "")
    add(S, "GitHub copy (taaza)", "✅" if _env("GITHUB_TOKEN") else "🔑", "" if _env("GITHUB_TOKEN") else "GitHub token nahi")
    add(S, "Phone alert (ntfy)", "✅" if _on("ntfy_ok") else "⏳", "" if _on("ntfy_ok") else "ntfy app mein topic subscribe (bot steps deta)")
    add(S, "Website ZIP bina pooche chadhna", "🛡️" if not _on("site_zip_auto") else "✅",
        "Jaanboojh kar band - galat zip seedha live na ho (aap ✅ dabate ho)" if not _on("site_zip_auto") else "")
    add(S, "Emergency web panel (vault, VM ke andar)", "🛡️" if not _on("vault_on") else "✅",
        "Jaanboojh kar band - sirf tab jab Telegram band ho; SSH se hi khulta" if not _on("vault_on") else "")

    M = "Kamai"
    pub = state.get("adsense_pub")
    add(M, "AdSense ad", "✅" if _on("adsense_ok") else "⏳", "" if _on("adsense_ok") else
        ("Google review chal raha (16 Nov se) - mail aate hi Claude ko" if pub else "AdSense id nahi"))
    return R


ORDER = {"🔑": 0, "⏳": 1, "⬜": 2, "🛡️": 3, "✅": 4}


def text():
    R = checks()
    cnt = {}
    for _g, _n, st, _w in R:
        cnt[st] = cnt.get(st, 0) + 1
    L = [f"🧩 SAB FEATURES - VM ka asli haal ({len(R)})",
         f"✅ {cnt.get('✅', 0)} chal rahe | ⬜ {cnt.get('⬜', 0)} band | 🔑 {cnt.get('🔑', 0)} key/login nahi | "
         f"⏳ {cnt.get('⏳', 0)} intezaar | 🛡️ {cnt.get('🛡️', 0)} jaanboojh kar band"]
    bad = sorted([r for r in R if r[2] != "✅"], key=lambda r: ORDER.get(r[2], 9))
    if bad:
        L.append("\n👉 JO NAHI CHAL RAHE (kyun + kya karna):")
        for g, n, st, w in bad:
            L.append(f"{st} {n}" + (f"\n    → {w}" if w else ""))
    L.append("\n✅ CHAL RAHE:")
    cur = None
    for g, n, st, w in R:
        if st != "✅":
            continue
        if g != cur:
            L.append(f"[{g}]")
            cur = g
        L.append(f"  ✅ {n}")
    L.append("\nℹ️ Facebook group / WhatsApp / Quora / Reddit post aur Instagram story-sticker: unki API hi nahi - "
             "bot taiyaar text deta hai, daalna aapka.")
    return "\n".join(L)


def on_text(tl):
    tl = (tl or "").strip().lower().rstrip(".!?")
    if tl in ("sab features", "sab feature", "feature audit", "features audit", "features sab", "kya band hai",
              "kaun se feature band hai", "band features"):
        from . import tg
        tg.say(text())
        return True
    return None
