"""Aapke haath ke kaam (jo API se nahi ho sakte) - bot roz khud jaanchta hai. Ho gaya to apne aap LIVE karta hai
aur batata hai. Bas jo sach mein baaki hai wahi list mein dikhta hai."""
import os
import requests
from . import state, tg, youtube
from .config import BRANDS
from .log import log

SITE_UTM = "https://sabhisaab.com/?utm_source={src}&utm_campaign={b}"


def _ig_fb_links():
    from . import meta as M
    out = {}
    if not M.has_token():
        return out
    for b in BRANDS:
        i = M.brand_info(b)
        if not i:
            continue
        try:
            if i.get("ig_id"):
                w = M._get(f"/{i['ig_id']}", i["page_token"], fields="website").get("website") or ""
                out[f"ig_{b}"] = "sabhisaab.com" in w
            w = M._get(f"/{i['page_id']}", i["page_token"], fields="website").get("website") or ""
            out[f"fb_{b}"] = "sabhisaab.com" in w
        except Exception as e:
            log(f"link check {b}: {e}")
    return out


def _threads_links():
    from . import threads as TH
    out = {}
    for b in BRANDS:
        i = TH.info(b)
        if not i:
            continue
        try:
            j = requests.get("https://graph.threads.net/v1.0/me", timeout=20,
                             params={"fields": "threads_biography", "access_token": i["token"]}).json()
            out[f"th_{b}"] = "sabhisaab" in (j.get("threads_biography") or "").lower()
        except Exception:
            pass
    return out


def _yt_advanced():
    out = {}
    for b in BRANDS:
        if youtube.has_login(b):
            try:
                st = youtube._api(b, "GET", "/youtube/v3/channels", params={"part": "status", "mine": "true"})["items"][0]["status"]
                out[b] = st.get("longUploadsStatus") == "allowed"
            except Exception:
                pass
    return out


def _gh():
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return False, False
    try:
        r = requests.get("https://api.github.com/repos/mkpandey1989-hue/sabhisaab", timeout=20,
                         headers={"Authorization": f"Bearer {tok}"}).json()
        return True, bool(r.get("permissions", {}).get("push"))
    except Exception:
        return True, False


def _meta_insights():
    from . import meta as M
    if not M.has_token():
        return False
    for b in BRANDS:
        i = M.brand_info(b)
        if i and i.get("ig_id"):
            try:
                M._get(f"/{i['ig_id']}/insights", i["page_token"], metric="reach", period="day")
                return True
            except Exception as e:
                log(f"insights perm: {e}")
                return False
    return False


def check():
    """Returns list of (key, done, title, how)."""
    from . import analytics as AN, website, pinterest as PI
    items = []
    for b, v in BRANDS.items():
        items.append((f"yt_{b}", youtube.has_login(b), f"YouTube login: {v['name']}", "/login"))
    items.append(("an_client", AN.CLIENT.exists(), "Analytics client JSON (yt-auto-desktop)",
                  "Google Cloud → Clients → yt-auto-desktop → Download JSON → /analytics → file bhejein"))
    for b, v in BRANDS.items():
        items.append((f"an_{b}", AN.has(b), f"Analytics login: {v['name']}", "/analytics → button"))
    items.append(("site_sa", website.SA.exists(), "Website Google service account (gsc-bot) JSON",
                  "Cloud project 'sabhisaab' → IAM → Service accounts → gsc-bot → Keys → Add key → JSON → bot ko file"))
    has_tok, push = _gh()
    items.append(("gh_push", push, "GitHub token: website repo par likhne + Actions ki ijaazat",
                  "github.com/settings/personal-access-tokens → token edit → repos: sabhisaab + sabhisaab-network → "
                  "Contents: Read/write, Actions: Read/write → naya token bot ko"))
    if push and not state.get("old_crons_off"):
        tg.say(website.disable_old_crons())
    items.append(("old_crons", bool(state.get("old_crons_off")), "Purane GitHub cron band (double report nahi)", "bot khud karega (token ke baad)"))
    items.append(("old_bot", bool(state.get("old_bot_off")), "Purana website Telegram bot (@Sabhiisaab_bot) band",
                  "Cloudflare → Workers → sabhisaab-bot → Settings → Delete/Disable; phir yahan likhein 'purana bot band'"))
    items.append(("bing_key", bool(website._env().get("BING_API_KEY")), "Bing API key (bot quota/crawl khud dekhega)",
                  "bing.com/webmasters → Settings (⚙️) → API access → API Key → Generate → bot ko: 'bing key <key>' "
                  "(message bot khud mitata hai)"))
    for k, ok in _ig_fb_links().items():
        p, b = k.split("_", 1)
        items.append((k, ok, f"{'Instagram' if p == 'ig' else 'Facebook'} profile link: {BRANDS[b]['name']}",
                      SITE_UTM.format(src="instagram" if p == "ig" else "facebook", b=b)))
    if not state.get("threads_links_ok"):      # Threads API profile 'Links' nahi dikhata - bio text ya aapki pushti
        for k, ok in _threads_links().items():
            b = k.split("_", 1)[1]
            items.append((k, ok, f"Threads bio link: {BRANDS[b]['name']}",
                          SITE_UTM.format(src="threads", b=b) + "  (Links mein laga diya ho to bot ko likhein: 'threads link laga diya')"))
    for b, ok in _yt_advanced().items():
        items.append((f"ytadv_{b}", ok, f"YouTube Advanced features: {BRANDS[b]['name']}",
                      "studio.youtube.com → Settings → Channel → Feature eligibility → Advanced features → Get access"))
    items.append(("meta_ins", _meta_insights(), "Meta insights ijaazat (reel reach/plays)",
                  "Business Settings → System users → sabhisaab-bot → Generate token → instagram_manage_insights + read_insights tick → token bot ko"))
    # v2.9.3: 'Meta App Review auto-DM' hataya - DM niti (privacy sec. 8) se band hai, owner ka kaam nahi
    # v2.9.3: 'hub video' hataya - v2.7.0 se bot har brand ki har hafte khud banata aur jodta hai
    if state.get("pin_form"):             # v2.1.0: form bhar diya - ab sirf intezaar (bot roz 11 baje khud jaanchta hai)
        items.append(("pin_std", PI.status().get("live", False),
                      f"Pinterest Standard: form bhara {state.get('pin_form')} - manzoori ka intezaar 🤖 bot khud jaanchta hai",
                      "Kuch nahi karna. Mana ho to email ka screenshot Claude ko; 26 Nov tak jawab na aaye to community post (list mein aayega)"))
    else:
        items.append(("pin_std", PI.status().get("live", False), "Pinterest Standard (public pins)", "recording + Upgrade form (alag steps)"))
    # v1.8: website ki nayi privacy + social ZIP live hui? (Meta/Google/Pinterest app isi page par tike hain)
    try:
        from . import privacy as PV
        items.append(("web_v18", not PV.check_site(), "Website privacy + social link page LIVE",
                      "ho chuka (28-29 Oct) - agar laal ho to privacy page dekhein"))
    except Exception as e:
        log(f"web_v18: {e}")
    try:
        from .config import DATA
        y = (DATA / "site_repo" / ".github" / "workflows" / "deploy.yml")
        items.append(("web_w2", y.exists() and "sabhinet bot hamesha" in y.read_text(encoding="utf-8"),
                      "Website ZIP W2 (Google sitemap har deploy par)", "W2 ZIP bot ko bhejo → 🌐 Haan"))
    except Exception as e:
        log(f"web_w2: {e}")
    # v2.0: seedha Cloudflare deploy (GitHub Actions par nirbharta khatam)
    from . import website as _w
    items.append(("cf_token", all(_w._cf()), "Cloudflare API token + Account ID VM par (website deploy + Telegram ka doosra raasta)",
                  "dash.cloudflare.com/profile/api-tokens → Create Token → Create Custom Token → naam 'sabhinet' → "
                  "Permissions (Account): Workers Scripts=Edit, Workers KV Storage=Edit, Cloudflare Pages=Edit, "
                  "Account Settings=Read → Continue → Create → token bot ko: 'cf token <token>'; Account ID "
                  "(dash.cloudflare.com → Workers & Pages, daayin taraf) → 'cf account <id>'. Message bot khud mita dega."))
    gn = state.get("ga_need")                # v2.1.4: website traffic (GA4) ke liye owner ka kaam, link ke saath
    if gn:
        items.append(("ga4", False, "Google (traffic report + roz sitemap/index) dobara jodna - restore mein nayi service account aa gayi",
                      "Bot mein 'google jaanch' likhein → wo 3 step aur link dega (purane gsc-bot ki nayi JSON key bot ko). "
                      "Ho jaate hi list se khud hatega" if gn.get("kind") == "sa" else
                      ((f"{gn.get('link')} → Enable" if gn.get("kind") == "api" else
                        f"analytics.google.com → Admin → Property access management → Add users → {gn.get('email')} → Viewer")
                       + " → phir bot mein 'google jaanch'")))
    try:                       # v2.0.7: Telegram toote to bhi baat (Cloudflare relay + ntfy)
        from . import relay as _rl
        items.append(("relay", _rl.ok(), "Telegram ka doosra raasta (Cloudflare relay) + VM chowkidaar",
                      "cf token + cf account dete hi bot khud banata hai. Haal: 'raasta haal'"))
        items.append(("ntfy", bool(state.get("ntfy_ok")), "Backup khabar app ntfy (Telegram poora band ho tab bhi)",
                      "Bot ko likhein 'backup setup' → 3 step → test link kholte hi bot khud pakad lega"))
    except Exception as e:
        log(f"relay item: {e}")
    try:                      # v2.0: website fix W3 live hua? (stopwatch page par disclaimer ab ek hi baar)
        r = requests.get("https://sabhisaab.com/stopwatch-online", timeout=20)
        items.append(("web_w3", r.ok and r.text.count("natija ek anuman hai.") <= 1,
                      "Website ZIP W3 (30 galat link + 21 dohra vaakya + buy-vs-rent title) LIVE",
                      "W3-site-fix-29oct.zip bot ko bhejo → 🌐 Haan → 🚀 Website deploy"))
    except Exception as e:
        log(f"web_w3: {e}")
    # v2.9.3 (owner: 'hata diya bolta hai, fir dubara dikhta hai'): bot-jaanch wale kaam par owner ki pushti ab pakki maani jaati hai
    # (sirf woh jinke bina bot ka kaam hi na chale - login/token - unhe bot ki asli jaanch hi band karti hai)
    ok_ = state.get("owner_ok") or {}
    gone_keys = {"web_v18", "web_w2", "web_w3", "old_crons", "old_bot"}      # purane ek-baar ke kaam / bot ke apne
    items = [(k, (d or (k in ok_ and not str(k).startswith(STRICT))), t, h) for k, d, t, h in items if k not in gone_keys]
    seed_todo()
    auto_close()                                   # v2.0.3: jo API se pakka ho sake, bot khud band karta hai
    import datetime as _d
    today = str(_d.date.today())
    for it_ in (state.get("todo") or []):          # aapke/bot ke khule kaam: jab tak aap 'ho gaya' na bolein
        if it_.get("after") and it_["after"] > today:
            continue                               # v2.0.3: tareekh se pehle list mein nahi (yaad us din aayegi)
        how = it_.get("how") or "ho jaye to likhein: 'ho gaya <shabd>'"
        tag = " 🤖 bot khud jaanchta hai" if it_.get("auto") else ""
        items.append(("todo_" + it_["x"][:20], False, f"📌 {it_['x']} ({it_['t']}){tag}", how))
    return items


# ---------------- v2.0.3: khule kaam ki apne-aap jaanch ----------------
def _tg_pinned():
    try:
        from .config import TG_CHANNEL
        r = tg.call("getChat", {"chat_id": TG_CHANNEL}, tries=1) or {}
        return bool(r.get("pinned_message"))
    except Exception:
        return False


def _gsc_all_indexed():
    try:
        from . import siteknow
        pg = siteknow.pages()
        return bool(pg) and not siteknow.not_indexed()
    except Exception:
        return False


def _psi_key():
    try:
        from . import website
        return bool(website._env().get("PSI_KEY"))
    except Exception:
        return False


def _cf_ok():
    try:
        from . import website
        return all(website._cf())
    except Exception:
        return False


def _dm_over():
    import datetime
    return str(datetime.date.today()) > "2026-11-27"


def _meta_secret_ok():
    from . import meta as M
    return M.has_token() and not M._cfg().get("secret_bad")


def _threads_all_ok():
    from . import threads as TH
    return all(TH.alive(b)[0] for b in BRANDS if TH.info(b))


def _pin_oauth():
    from . import pinterest as PI
    return PI.status()["oauth"]


def _cf_acc_ok():
    import re as _r
    from .website import _cf
    return bool(_r.fullmatch(r"[0-9a-f]{32}", _cf()[1] or ""))


def _cw_done():
    from . import updater
    return not updater._cw_files()


def _cw52():
    """v2.1.9: Chowkidar v5.2 chal raha hai? (sirf version line padhta hai)"""
    try:
        import pathlib as _p
        t = _p.Path("/home/ubuntu/chowkidar/chowkidar.py").read_text(encoding="utf-8", errors="ignore")[:3000]
        return 'VERSION = "5.2' in t or 'VERSION = "5.3' in t or 'VERSION = "6.' in t
    except Exception:
        return False


def _looks4():
    """v2.2.0: chaaron channel ka look Sample Studio mein pakka?"""
    from .config import BRANDS
    lk = state.get("brand_look") or {}
    return all(b in lk for b in BRANDS)


def _cw_dash():
    """v2.1.9: Chowkidar ne dashboard tunnel jod kar seedha port band kar diya? (sirf haan/na padhta hai)"""
    try:
        import json as _j
        import pathlib as _p
        return bool(_j.loads(_p.Path("/home/ubuntu/chowkidar/pro_config.json").read_text()).get("dash_done"))
    except Exception:
        return False



def _w7_live():
    """v2.6.0: Website W7 VM ke site repo mein lag gaya? (galat link theek + privacy mein Workers AI)"""
    try:
        from .website import DIR
        a = (DIR / "site" / "sip-calculator.html").read_text(encoding="utf-8", errors="ignore")
        b = (DIR / "site" / "privacy.html").read_text(encoding="utf-8", errors="ignore")
        return 'href="/exit-load-calculator">Exit Load Calculator' in a and "Workers AI" in b
    except Exception:
        return False


def _fb_perm_fixed():
    """v2.6.0: Facebook comment padhne ki rok (Meta #10) khatam - koi brand ruka nahi aur pichhle 2 din mein padhna chala."""
    import time as _t
    act = [b for b, v in (state.get("fb_comment_perm") or {}).items() if _t.time() < float(v.get("until", 0) or 0)]
    ok = state.get("fb_read_ok") or {}
    return bool(state.get("fb_perm_ever")) and not act and bool(ok) and all(_t.time() - float(x) < 2 * 86400 for x in ok.values())



def _site_has(fn, *needles):
    try:
        from .website import DIR
        t = (DIR / "site" / fn).read_text(encoding="utf-8", errors="ignore")
        return all(n in t for n in needles)
    except Exception:
        return False


def _w8_live():
    """v2.6.2: W8 (har page 'Aaj ka sawal' + homepage section) live?"""
    return _site_has("install-app.js", "shJawab") and _site_has("index.html", 'id="aaj-ke-sawal"')


def _w9_live():
    """v2.6.3: W9 (tax pages naya Act note, 194H 2%, MSSC band, watch.py v11) live?"""
    try:
        from .website import DIR
        return (_site_has("income-tax-calculator.html", 'id="naya-act"') and _site_has("mahila-samman-calculator.html", 'id="yojana-band"')
                and "v11" in (DIR / "scripts" / "watch.py").read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return False


def _ytc_ok():
    """v2.6.4: har YouTube login wale channel ka comment-login ho chuka."""
    try:
        from . import ytcomment, youtube
        return any(youtube.has_login(b) for b in BRANDS) and not ytcomment.missing()
    except Exception:
        return False


def _bk_saved():
    return state.get("bk_pass_saved") is True


def _analytics_all():
    try:
        from . import analytics as _AN
        return all(_AN.has(b) for b in BRANDS)
    except Exception:
        return False


def _push_ok():
    return bool(state.get("push_on"))


def _quiz_ok():
    try:
        from . import quizbot as _QB
        return bool(_QB.token())
    except Exception:
        return False


def _ga_ok():
    import time as _t
    return _t.time() - float(state.get("ga_data_ok", 0) or 0) < 7 * 86400


def _pq_loaded():
    return bool(state.get("pq_loaded"))


AUTO = {"pq": _pq_loaded, "looks4": _looks4, "cw52": _cw52, "cw_dash": _cw_dash,
        "threads_ok": _threads_all_ok, "pin_oauth": _pin_oauth, "cf_acc": _cf_acc_ok, "cw_done": _cw_done,
        "meta_secret": _meta_secret_ok, "tg_pin": _tg_pinned, "gsc_all": _gsc_all_indexed, "psi": _psi_key, "cf": _cf_ok, "dm_over": _dm_over,
        "w7": _w7_live, "fb_perm": _fb_perm_fixed, "w8": _w8_live, "ga4": _ga_ok, "w9": _w9_live, "ytc": _ytc_ok, "bkpass": _bk_saved, "anall": _analytics_all, "push": _push_ok, "quizb": _quiz_ok}


def add(text, how="", after=None, auto=None):
    """v2.6.1: bot khud naya kaam list mein (dohraav nahi). factwatch/policywatch jaise module isi se."""
    import datetime as _d
    text = str(text).strip()[:400]
    if not text:
        return False
    if any(o.get("x") == text for o in (state.get("todo") or [])):
        return False
    it = {"x": text, "t": str(_d.date.today())}
    if how:
        it["how"] = how
    if after:
        it["after"] = after
    if auto:
        it["auto"] = auto
    state.update("todo", lambda l: (l or []) + [it], [])
    _dirty()
    return True


def auto_close():
    """'auto' wale kaam API se jaancho; ho gaye to list se hatao aur owner ko batao (ek baar)."""
    lst = state.get("todo") or []
    done, left = [], []
    for x in lst:
        fn = AUTO.get(x.get("auto") or "")
        ok = False
        if fn:
            try:
                ok = bool(fn())
            except Exception as e:
                log(f"auto_close {x.get('auto')}: {e}")
        (done if ok else left).append(x)
    if done:
        state.put("todo", left)
        state.update("todo_done", lambda l: ((l or []) + [{**d, "done": str(__import__('datetime').date.today()), "by": "bot"}
                                                        for d in done])[-200:], [])
        try:
            from . import diary
            for d in done:
                diary.add("pakka", "kaam pura (bot ne pakka kiya): " + d["x"][:120])
        except Exception:
            pass
        _dirty()
        tg.alert("green", "✅ Ye kaam ho gaya (bot ne khud API se pakka kiya), list se hata diya:\n" +
                 "\n".join("• " + d["x"][:120] for d in done))
    return done


def mark_done(word, prefix=False):
    """'ho gaya <shabd>' - list se hatao + itihaas mein rakho (PENDING.md mein 'ho chuke' dikhte hain)."""
    import datetime
    w = word.strip().lower()
    before = state.get("todo") or []
    words = [x for x in w.split() if len(x) > 1]

    def hit(x):        # v2.1.8: 'ho gaya pin secret' -> har shabd kahin bhi (pehle poora jumla ek saath chahiye tha)
        tx = x["x"].lower()
        if prefix:
            return tx.startswith(w)
        return w in tx or (words and all(k in tx for k in words))
    gone = [x for x in before if w and hit(x)][:1 if prefix else None]
    if not prefix and len(gone) > 1:            # kai mile to sirf sabse milta-julta ek (galti se sab na hatein)
        gone = sorted(gone, key=lambda x: -sum(k in x["x"].lower() for k in words))[:1]
    state.put("todo", [x for x in before if x not in gone])
    if gone:
        state.update("todo_done", lambda l: ((l or []) + [{**g, "done": str(datetime.date.today()), "by": "owner"}
                                                        for g in gone])[-200:], [])
        _dirty()
    return gone


def suggest(word, n=3):
    """v2.8.2 ('ho gaya fb starts', 'labhlodeals riview', 'GSC wakah' nahi mile the): spelling galat ho to bhi milte-julte kaam.
    Kaam ke text + uske 'how' (jisme 'ho gaya xyz' likha hota hai) dono mein, har shabd ka fuzzy milan. -> [(score, todo)]"""
    import difflib
    import re as _re
    ws = [x for x in _re.findall(r"[a-z0-9\u0900-\u097f]+", word.lower()) if len(x) > 1]
    if not ws:
        return []
    out = []
    for o in state.get("todo") or []:
        toks = _re.findall(r"[a-z0-9\u0900-\u097f]+", (o.get("x", "") + " " + o.get("how", "")).lower())
        if not toks:
            continue
        sc = 0.0
        for w in ws:
            best = max((difflib.SequenceMatcher(None, w, t).ratio() for t in toks), default=0)
            sc += best if best >= 0.72 else 0
        sc /= len(ws)
        if sc >= 0.5:
            out.append((round(sc, 3), o))
    out.sort(key=lambda x: -x[0])
    return out[:n]


def already_done(word):
    w = word.strip().lower()
    return [d for d in (state.get("todo_done") or []) if w and w in d.get("x", "").lower()][-1:]


def _dirty():
    try:
        from . import updater
        updater.mark_dirty()                     # v2.0.4: kaam ho gaya -> docs/PENDING.md GitHub par turant (10 min mein)
    except Exception:
        pass


CLAUDE_TAGS = ("[Bot agli", "[P0 Bot agli", "[P1 Bot agli", "[P2 Bot agli", "[Developer", "[P0 Developer", "[P1 Developer",
               "[P2 Developer", "[Claude]", "[P2]", "[API naya]")


def is_claude(text):
    """v2.6.4: ye kaam Claude/developer ka hai (owner ke haath ka nahi) - list mein alag dikhe."""
    t = str(text or "").lstrip("📌 ").strip()
    return t.startswith(CLAUDE_TAGS)


def report(auto=False):
    items = check()
    prev = state.get("tasks_done") or {}
    newly = [t for k, d, t, _ in items if d and not prev.get(k)]
    state.put("tasks_done", {k: d for k, d, _, _ in items})
    if auto and newly and prev:
        tg.alert("green", "✅ Aapka kaam ho gaya, bot ne LIVE kar diya:\n" + "\n".join(f"• {t}" for t in newly))
    pend_all = [(k, t, h) for k, d, t, h in items if not d]
    pend = [x for x in pend_all if not is_claude(x[1])]          # v2.6.4: sirf owner ke haath ke number wale
    dev = [x for x in pend_all if is_claude(x[1])]
    if auto:
        return None
    state.put("pend_order", [[k, t] for k, t, _ in pend])     # v2.1.6: 'ho gaya 3' ke liye number
    done_n = sum(1 for _, d, _, _ in items if d)
    lines = [f"🧾 Aapke haath ke kaam: {done_n}/{len(items)} ho gaye"]
    if pend:
        lines.append("\n⬜ Baaki (🤖 = bot khud jaanch kar hatayega; baaki ho jaye to 'ho gaya <number>'):")
        lines += [f"{n}. {'🤖 ' if not str(k).startswith('todo') else ''}{t}\n   👉 {h}" for n, (k, t, h) in enumerate(pend, 1)]
    else:
        lines.append("🎉 Aapke haath ka sab kaam ho gaya!")
    if dev:
        lines.append(f"\n🛠 Claude/developer ke kaam: {len(dev)} (aapko kuch nahi karna - Claude chat mein 'continue' bolein): "
                     + "; ".join(t.split("]", 1)[-1].strip()[:40] for _, t, _ in dev[:6]) + (" ..." if len(dev) > 6 else ""))
    return "\n".join(lines)[:4000]


# v1.8: owner ke haath ke baaki kaam (28 Oct 2026 tak) - ek baar list mein, 'ho gaya <shabd>' se hatte hain
SEED = [
    "Meta app Data Deletion URL: developers.facebook.com → Sabhisaab Publisher → App settings → Basic → "
    "Data deletion instructions URL = https://sabhisaab.com/privacy#data-deletion → Save",
    "YouTube channel links (4 channel): Studio → Customization → Basic info → Links → https://sabhisaab.com/ + WhatsApp channel "
    "(Shorts description mein link clickable nahi, channel link hota hai)",
    "Instagram/Facebook/Threads bio mein WhatsApp channel link bhi (link-in-bio: https://sabhisaab.com/links)",
    "Telegram + WhatsApp channel par welcome post (sab channel ke link) Pin karein",
    "Instagram @sunonatak warning: Account Status → Request review",
    "Labh Lo Deals FB: Content Monetization 'Policy issues' ka kaaran padh kar bot ko bhejein",
    "Chowkidar mein ytlistener ki jagah sabhinet status (TradingBot repo - developer)",
    "AdSense apply (mid-Nov 2026 ke baad)",
]


SEED_V20 = [
    "GSC Request Indexing (roz 1-2, isi kram mein): buy-vs-rent-guide (W3 deploy ke baad), random-number-generator, "
    "number-system-converter, stopwatch-online, fire-number-calculator, delivery-date-calculator, notice-period-buyout-calculator. "
    "Ek-tap link roz subah ki Pending report mein",
    "Bing: support ka jawab aaye to text bot ko ya Claude ko bhejein (bulk submit kabhi nahi; bot sirf badle URL bhejta hai)",
]


SEED_V203 = [
    # (text, after-date or "", auto-key or "", how)
    ("Instagram @sunonatak: Account Status → 'You can't send messages' → Request review (rok 28 Oct se 27 Nov 2026; "
     "review 29 din ke andar; English text Claude chat mein). Bio + caption pehle saaf ho chuke", "", "",
     "ho jaye to likhein: 'ho gaya sunonatak review'"),
    ("Instagram @sunonatak: 27 Nov tak koi DM nahi (bot ka DM bhi band). 'Established presence' (monetization) wala review "
     "abhi MAT dabana - 90 din mein ek hi baar milta hai", "", "dm_over",
     "27 Nov ke baad apne aap list se hatega: 'ho gaya dm rok'"),
    ("Instagram @sunonatak: monetization 'Established presence' ka Request review ab bhej sakte hain (agar followers badhe "
     "hon aur koi nayi rok na ho)", "2027-01-27", "", "ho jaye to likhein: 'ho gaya established'"),
    ("Instagram @labhlodeals: Account Status → 'Features you can't use' kholo → screenshot Claude/bot ko bhejo "
     "(wahan narangi nishaan hai)", "", "", "ho jaye to likhein: 'ho gaya labhlodeals features'"),
    ("4 Facebook page: Professional dashboard → Page status / Monetization dekho - koi narangi/laal nishaan ho to screenshot "
     "(Instagram ki rok sirf Instagram par hai, FB ka alag hota hai)", "", "", "ho jaye to likhein: 'ho gaya fb status'"),
    ("Telegram channel @sabhisaab par welcome post Pin karein (sab channel ke link)", "", "tg_pin",
     "Telegram → channel → welcome post par long-press → Pin. Bot khud pakad lega"),
    ("WhatsApp channel 'Sab Hisaab' par welcome post Pin karein", "", "",
     "ho jaye to likhein: 'ho gaya whatsapp pin'"),
    ("PageSpeed key (website ki speed report ke liye): console.cloud.google.com/apis/library/pagespeedonline.googleapis.com"
     "?project=yt-auto-512210 → Enable → console.cloud.google.com/apis/credentials?project=yt-auto-512210 → Create "
     "credentials → API key → Edit → API restrictions: PageSpeed Insights API → Save → key bot ko: 'psi key <key>'",
     "", "psi", "Bot khud pakad lega (message bhi khud mitata hai)"),
    ("Chowkidar (@manoj_vm_chowkidar_bot) ko ye message bhejein: 'status list mein ytlistener hata do, uski jagah "
     "sabhinet service dikhao (systemctl is-active sabhinet). ytlistener service band hai, use dobara mat chalana.'",
     "", "", "ho jaye to likhein: 'ho gaya chowkidar'"),
    ("AdSense apply: adsense.google.com → site sabhisaab.com → Privacy & messaging mein Google-certified CMP chalu "
     "(Europe/UK) → approval ke baad ads.txt bot ko", "2026-11-16", "", "ho jaye to likhein: 'ho gaya adsense'"),
]


SEED_V204 = [
    ("Chowkidar abhi bhi 'ytlistener' dikhata hai (wo sirf padhta hai, apni file khud nahi badal sakta). Theek karna: "
     "1) sabhinet bot ko likhein 'chowkidar file do' 2) aayi file Claude ko bhejein 3) Claude fix ZIP dega 4) VM (Chowkidar) "
     "bot mein '🛠 Update' dabakar ZIP bhejein", "", "", "ho jaye to likhein: 'ho gaya chowkidar fix'"),
    ("Instagram @labhlodeals: 'You can't use direct messaging for 30 days' par tap → Request review / Disagree (wahi English "
     "text). DM bot ki taraf se bhi band (28 Nov tak)", "", "", "ho jaye to likhein: 'ho gaya labhlodeals review'"),
    ("Facebook (charon page): Professional dashboard → Monetization → 'Stars' → Set up (payout + PAN/tax details). "
     "Content monetization 'invite only' hai - wahan sirf 'Notify me' dabayein", "", "", "ho jaye to likhein: 'ho gaya fb stars'"),
    ("Facebook Labh Lo Deals: Monetization → 'Affiliate partnerships' → Set up (sirf deals page; har affiliate post par #ad)",
     "", "", "ho jaye to likhein: 'ho gaya fb affiliate'"),
    ("Bing Webmaster (bing.com/webmasters → sabhisaab.com): 1) Sitemaps → https://sabhisaab.com/sitemap.xml dikh raha ho "
     "to bas 'Resubmit' EK baar; na ho to Submit sitemap 2) URL Inspection → https://sabhisaab.com/ → Request indexing (sirf "
     "home, ek baar) 3) IndexNow tab mein bot ke bheje URL dikhte hain - dekh lein. Saare URL ek saath kabhi submit nahi",
     "", "", "ho jaye to likhein: 'ho gaya bing sitemap'"),
    ("Google Search Console → Indexing → Pages → neeche 'Why pages aren't indexed' (6 wajah, 192 page) ka screenshot Claude "
     "ko. Ghabrana nahi: inmein zyada purane .html/redirect/utm wale URL hote hain. Kuch delete/remove mat karna",
     "", "", "ho jaye to likhein: 'ho gaya gsc wajah'"),
    ("Website W4 ZIP (W4-site-fix-29oct.zip) bot ko → '🌐 Haan' (report 8 baje, Users sahi, Home screen button, nav jaanch)",
     "", "", "ho jaye to likhein: 'ho gaya w4'"),
]


SEED_V205 = [
    ("🔴 Meta App Secret dobara (Instagram + story isi se ruke hain): developers.facebook.com → My Apps → Sabhisaab "
     "Publisher → App settings → Basic → 'App secret' → Show → copy → bot ko likhein: meta secret <secret>", "", "meta_secret",
     "Bot jaanch kar khud hata dega"),
    ("GSC → Indexing → Pages → 'Redirect error' (26) par tap → neeche Examples ki list ka screenshot Claude ko "
     "(baaki wajah theek hain: redirect/canonical/?t= wale apne aap)", "", "", "ho jaye to likhein: 'ho gaya redirect'"),
    ("AdSense agar 'site 6 mahine purani nahi' bol kar mana kare to dobara apply (site 21 Jul 2026 se)", "2027-01-22", "",
     "ho jaye to likhein: 'ho gaya adsense dobara'"),
]


SEED_V206 = [
    ("GSC 'Redirect error' (26 purane .html link): bot ko likhein 'redirect jaanch'. Jawab 'sab sahi' aaye to GSC → Indexing → "
     "Pages → Redirect error → 'Validate fix' (ya 'Start new validation') dabayein. (Ye Jul-Aug ki purani galti hai, "
     "saare page ab maujood hain)", "", "", "ho jaye to likhein: 'ho gaya validate'"),
    ("Website W6 ZIP (W6-video-link-29oct.zip) bot ko → '🌐 Haan' (har page par usi vishay ki YouTube video ka link)",
     "", "", "ho jaye to likhein: 'ho gaya w6'"),
]


SEED_V207 = [
    ("Pinterest App secret badlein (29 Oct ko Telegram chat aur screenshot mein khula reh gaya tha)", None, None,
     "developers.pinterest.com/apps → Sabhisaab Publisher → Manage → App secret key → Reset/Regenerate → bot ko "
     "'/pinterest' → naya secret bhejein (bot mita dega). 'ho gaya pin secret'"),
]


SEED_V2111 = [            # v2.1.1: 30 Oct VM restore (purana backup) ke baad jo toota
    ("Bot mein 'vm audit' likhein → aayi file Claude ko bhejein (poore VM ka postmortem, sirf padhta hai)", None, None,
     "'ho gaya vm audit'"),
    ("Threads token naya (restore ke baad purane token 30 Oct ko khatam): Sab Hisaab Money, Labh Lo Deals, Pahadi Hisaab",
     None, "threads_ok", "developers.facebook.com → app → Threads → har brand ka naya token → bot chat mein paste → brand chunein. "
                         "Bot khud pakdega"),
    ("Pinterest login dobara (App ID ab sahi 1630338): bot mein /pinterest → link Chrome mein → Allow → address bot ko",
     None, "pin_oauth", "Bot khud pakdega; manzoori mil chuki ho to agle din 11 baje khud LIVE"),
    ("Cloudflare Account ID sahi bhejein (30 Oct ko 31 akshar gaya - pehla '1' chhoot gaya): 'cf account <32 akshar>'",
     None, "cf_acc", "dash.cloudflare.com → Workers & Pages → daayin Account ID → copy nishaan"),
]


SEED_V211 = [
    ("Cloudflare token mein 'Workers AI: Read' jodein (Gemini band ho to bot ka doosra dimaag)", None, None,
     "dash.cloudflare.com/profile/api-tokens → 'sabhinet' ke aage ⋯ → Edit → Add more → Account | Workers AI | Read → "
     "Continue to summary → Update token. Token wahi rehta hai, bot ko dobara bhejna NAHI. 'ho gaya workers ai'"),
    ("Chowkidar status mein ytlistener ki jagah sabhinet: bot ko likhein 'chowkidar fix' → ✅ Haan → ✅✅ Haan pakka "
     "(bazaar band ke samay, 15:35 ke baad)", None, "cw_done", "Bot khud backup, jaanch, restart karta hai; ho jaate hi list se hatega"),
    ("Pinterest: 29 Oct ko Standard form bhara tha - ab tak jawab nahi aaya to community.pinterest.biz par post "
     "(English text Claude chat mein, 29 Oct)", "2026-11-26", None, "Post ke baad: 'ho gaya pinterest post'"),
    ("Bing jaanch (19 Nov): bing.com par 'site:sabhisaab.com' search karein. 10 se kam page dikhein to Bing Webmaster → Support → "
     "purane ticket par reply (Claude se English text lein)", "2026-11-19", None, "'ho gaya bing jaanch'"),
]


SEED_V219 = [            # v2.1.9 (3 Nov 2026): Claude ka poora VM + Chowkidar audit
    ("Chowkidar v5.2 ZIP (chowkidar_v5_2_safe.zip) @manoj_vm_chowkidar_bot ko bhejein → '👮 Chowkidar Upgrade' → 1️⃣ → 2️⃣ "
     "(15:35 ke baad). Ye ZIP is bot (sabhinet) ko NAHI", None, "cw52",
     "Install ke baad Chowkidar mein: /takraav → '🔐 Git se token hatao' (agar dikhe). Bot khud pakdega aur list se hatayega"),
    ("Cloudflare token mein 3 permission jodein (trading dashboard ka HTTPS raasta, phir Chowkidar khud seedha port band karega): "
     "Account | Cloudflare Tunnel | Edit; Zone | Zone | Read; Zone | DNS | Edit (Specific zone: sabhisaab.com)", None, "cw_dash",
     "dash.cloudflare.com/profile/api-tokens → 'sabhinet' ke aage ⋯ → Edit → '+ Add more' (3 baar) → Continue to summary → "
     "Update token. Token wahi, kahin bhejna NAHI. Chowkidar 6 ghante mein khud jod kar naye https link bhejega"),
    ("(Marzi) Chowkidar mein '/kachra' → KACHRA-2nov (~38 GB, purana VM backup) chahiye na ho to '1) mitao'. Baaki safai v5.2 khud "
     "kar chuka. .cache/huggingface KABHI nahi", None, None, "ho jaye to: 'ho gaya kachra'"),
    ("Chowkidar mein '/get master_guard.py', '/get vm_health.py', '/get ntfy_monitor.py', '/get maintenance.sh' → aayi 4 file "
     "Claude ko (purane script - dohri restart/alert ka shak)", None, None, "ho jaye to: 'ho gaya purane script'"),
]


SEED_V220 = [
    ("Sample Studio se chaaron channel ka look pakka karein: Menu → 🧪 Sample studio → channel → video+thumbnail dekhein → "
     "pasand na aaye to '➡️ Agla namoona' → pasand aaye to '✅ Ye look pakka' (dohri pushti)", None, "looks4",
     "Manual: Menu → 📘 Studio manual. Jab tak pakka nahi, purana look chalta rahega (kuch nahi rukta). Bot khud pakdega"),
]


SEED_V230 = [
    ("(Marzi) Google Cloud mein 'Google Analytics Data API' chalu karein - website par log kitni der ruke (GA4 dwell) ke liye",
     None, None, "console.cloud.google.com → APIs → 'Google Analytics Data API' → Enable. Ho jaye to: 'ho gaya ga4'"),
]


def fix_list_v231():
    """v2.3.1 (owner: 'correction pending list'): dohre kaam hatao, ho chuke kaam itihaas mein, har kaam ka saaf 'ho gaya <shabd>'."""
    import datetime as _d
    day = str(_d.date.today())
    lst = state.get("todo") or []
    gone_why = []
    drop = {   # dohre (doosra wala zyada poora hai) / pehle se tareekh wala
        "Facebook/Threads bio mein WhatsApp channel link": "dohra (Instagram/Facebook/Threads bio wala kaam rakha)",
        "WhatsApp channel 'Sab Hisaab' par welcome post Pin karein": "dohra (Telegram + WhatsApp welcome wala kaam rakha)",
        "AdSense apply (mid-Nov 2026 ke baad)": "dohra (16 Nov wala tareekh-kaam rakha)",
    }
    done_now = {
        "Bot mein 'vm audit' likhein": "owner ne 3 Nov ko VM audit file bhej di",
        "Cloudflare token mein 'Workers AI: Read' jodein": "owner ke 3 Nov screenshot mein 'Workers AI: Read' laga hai",
    }
    how = {
        "Meta app Data Deletion URL": "ho jaye to: 'ho gaya data deletion'",
        "YouTube channel links (4 channel)": "ho jaye to: 'ho gaya yt links'",
        "Instagram/Facebook/Threads bio mein WhatsApp channel link": "ho jaye to: 'ho gaya bio'",
        "Telegram + WhatsApp channel par welcome post": "ho jaye to: 'ho gaya welcome pin'",
        "Instagram @sunonatak warning: Account Status": "Ye WARNING wala review hai (monetization 'Established presence' wala nahi). Ho jaye to: 'ho gaya sunonatak warning'",
        "Labh Lo Deals FB: Content Monetization 'Policy issues'": "ho jaye to: 'ho gaya deals policy'",
        "Bing: support ka jawab aaye": "ho jaye to: 'ho gaya bing support'",
    }
    keep, moved = [], []
    for o in lst:
        x = o.get("x", "")
        d_ = next((v for k, v in drop.items() if x.startswith(k)), None)
        dn = next((v for k, v in done_now.items() if x.startswith(k)), None)
        if d_ or dn:
            moved.append({**o, "done": day, "by": "bot-safai", "note": d_ or dn})
            gone_why.append(f"{x[:50]} → {d_ or dn}")
            continue
        h = next((v for k, v in how.items() if x.startswith(k)), None)
        keep.append({**o, "how": h} if h else o)
    state.put("todo", keep)
    if moved:
        state.update("todo_done", lambda l: ((l or []) + moved)[-200:], [])
    _dirty()
    return gone_why


SEED_V236 = [
    ("(Marzi) WhatsApp channel: Meta ne iska API nahi diya - bot roz 1 taiyaar post (photo + sawal + link) bhejta hai, bas forward karein",
     None, None, "Jab WhatsApp channel ka API aayega, bot khud post shuru karega. Ho jaye to: 'ho gaya whatsapp'"),
    ("(Marzi) Facebook GROUP post: Meta ne 2024 se group API band kar di - group mein reel khud share karein (Business Dashboard ka 'group post' kaam)",
     None, None, "Page ke photo-post, reel, story bot khud karta hai. Ho jaye to: 'ho gaya fb group'"),
]


SEED_V257 = [            # v2.5.7: comment + privacy + Jawab/Video plan (SabHisaab_Jawab_Video_Final_Plan.docx) ke baaki kaam - policy ke andar
    ("[P0 Owner] YouTube par bot ke comment/jawab ke liye: bot mein 'yt comment login' likhein -> har channel ka link -> us channel ka account -> Allow -> address bot ko. "
     "(Pehle Google Cloud -> OAuth consent screen -> 'In production'; '/analytics' wala Desktop client wahi chalta hai). Upload wala login nahi badlega", None, None,
     "ho jaye to likhein: 'ho gaya yt comment login'"),
    ("[P0 Owner] Bot mein 'privacy ig theek' likhein -> purani/nayi line dekhkar ✅✅ (bot privacy.html mein SIRF Instagram 'LINK' wali line + ek chhota UTM vaada badlega; audit paas hone par). "
     "Phir 'Aakhri update' tareekh developer se", None, None, "ho jaye to likhein: 'ho gaya privacy assist'"),
    ("[Owner] Bot ne Telegram quiz poll ka prastav bheja ho (roz max 2) to ✅✅; 'jawab poll chalu/band' bhi chalta hai", None, None, "ho jaye to likhein: 'ho gaya poll'"),
    ("[Owner] Har brand ka '/analytics' login (agar nahi kiya): 'ypp haal' mein asli watch hours/Shorts views tabhi aate hain", None, None, "ho jaye to likhein: 'ho gaya analytics login'"),
    ("[P0 Developer B1/P0-1] /jawab ka naya UI: har sawal ka ek dabba (code+channel+tarikh beech mein), tap-to-guess + 'Seedha jawab dekhein' (jawab kabhi lock nahi), aaj ka score/streak (browser mein), "
     "code/shabd khoj, channel chips, WhatsApp challenge, Telegram patti 60% scroll par, GA4 events (pick/peek/search/share/engaged 30-90-180s). Bot ne har jawab ka anchor (#cCODE) aur 1,200 tak archive rakha hai", "2026-11-25", None,
     "ho jaye to likhein: 'ho gaya jawab ui'"),
    ("[P0 Developer P0-2] Privacy page: 'Jawab page par score/streak sirf aapke browser mein' + (A1 chalu hone par) anonymous vote counter ka zikr + Telegram opt-in/poll ka zikr", "2026-11-25", None,
     "ho jaye to likhein: 'ho gaya privacy browser'"),
    ("[P0 Bot agli - video] V1 option ek-ek karke+pop, V2 neon timer bar+tick, V3 50-50 (sahi option kabhi nahi katta - unit test), V6 micro-motion, V7 honest level tag, V8 blur-reveal CTA, V10 ant ka CTA. "
     "Render VM par test chahiye + A7 flash-safety scan (1 sec mein 3 se zyada flash nahi)", None, None, "Claude ko bolein: 'video V1-V10 banao' (VM par render time naap kar)"),
    ("[P1 Bot agli] A1 asli % engine (Cloudflare Worker anonymous counter, 30+ vote ke baad hi %), A2 difficulty label, V4 karaoke subtitles, V5 moving background, V9 hook variety + Expert Fact, A9 anti-templated guard", None, None,
     "Claude ko bolein: 'asli percent engine banao'"),
    ("[P1 Bot agli] Web Stories + Pinterest pins har sawal ke slides se (A8 quality score; pehle hafte owner approve), A10 exam/tyohaar calendar queue, A12 weekly Telegram report", None, None,
     "Claude ko bolein: 'web stories aur weekly report banao'"),
    ("[P2 Bot agli] A3 retention learner (YouTube Analytics se hook A/B), A5 purani reel revival, A6 comment->FAQ/idea (naam kabhi nahi, 30 din)", "2026-12-15", None, "Claude ko bolein: 'retention learner banao'"),
    ("[P2 Bot agli] A11 Instagram private reply (ek comment par ek DM, 7 din ke andar, app review ke baad) - SIRF 28 Nov 2026 ke baad, pehle hafte owner approve; DM-band account par nahi", "2026-11-28", None,
     "Claude ko bolein: 'instagram private reply banao' (Meta App Review pehle)"),
    ("[Developer B3] Jawab ke neeche mini-tool embed (Discount/EMI/Percentage), finance/kanoon jawab par 'Source' link (RBI/SEBI/India Code) + 'Reviewed on', topic hub pages (50 sawal), weekly mock test", "2026-12-10", None,
     "ho jaye to likhein: 'ho gaya b3 hub'"),
    ("[Owner] YouTube pinned comment: (agar chahein) apne video ka pehla comment khud ek click se pin karein - API se pin nahi hota. Text: 'Aap kya chunenge? Sahi jawab code #N par.'", None, None,
     "ho jaye to likhein: 'ho gaya pin'"),
]


SEED_V256 = [            # v2.5.6: purani reels ke jawab + zyada der rokne ke agle kadam (har ek alag release)
    ("[Bot agli] Purani 3-ank code wali reels (v2.5.0 se pehle) ke jawab website par: bot ke reel_codes se import. DHYAN: purane code takraav (B-04) se kuch code galat sawal par ho sakte hain - "
     "pehle owner ek-do namoone dekhe, galat wale na jayein", None, None, "Claude ko bolein: 'purane jawab import karo' (pehle pakka karenge)"),
    ("[Bot agli] /jawab ke channel-wise aur mahine-wise alag page (zyada page = zyada der). DHYAN: wahi jawab do page par duplicate na ho (AdSense 'low value' / SEO takraav) - "
     "har page par alag samagri (jawab + wajah + related tool) ho tabhi", None, None, "Claude ko bolein: 'jawab channel pages banao' (site repo ZIP chahiye)"),
    ("[Developer D15] /jawab par code search box (7-8 ank tak sahi code mil jaye; galat code par 'aaj ke top 5 jawab') - bot ne har purane jawab ka anchor (#cCODE) rakh diya hai, sirf search chahiye", "2026-11-25", None,
     "ho jaye to likhein: 'ho gaya jawab search'"),
    ("[Owner] Purani reels: bot 'jawab haal' / 'code <ank>' se jaanch (last 800 code); naye (v2.5.6 ke baad) jawab website par 1,200 tak anchor ke saath rehte hain", None, None,
     "ho jaye to likhein: 'ho gaya purani reel jaanch'"),
]


SEED_V255 = [            # v2.5.5: bot ke agle (abhi na bane) kaam - har ek alag release mein, GitHub se ZIP nikal kar Claude ko 'v2.5.6 mein <naam> banao' bol kar
    ("[Bot agli] Platform policy-change watcher: YouTube/Meta/AdSense/Pinterest policy page ka hash roz; badle to Telegram par 'kya badla + kya karna' (diff chhota)", None, None,
     "Claude ko bolein: 'policy watcher banao'"),
    ("[Bot agli] Quality governor: reel/post ka hook, caption, thumbnail rang platform ke hisaab se alag; ek hi video 5 platform par bina badlav nahi (script-similarity jaanch)", None, None,
     "Claude ko bolein: 'governor banao'"),
    ("[Bot agli] Telegram opt-in bot ('roz ka sawal', score/reminder, 'data hatao'; phone number nahi) - privacy page ka text pehle", None, None,
     "Claude ko bolein: 'telegram optin banao'"),
    ("[Bot agli] Weekly quiz generator (apne qbank se naye sawal, dohraav nahi) + hub video script/chapters/description links (owner approve)", None, None,
     "Claude ko bolein: 'hub video aur quiz banao'"),
    ("[Bot agli] Schema injector (BreadcrumbList/Article/WebApplication; QAPage kabhi nahi), share-card + embed generator, Hindi/English page draft (owner review ke bina publish nahi)", None, None,
     "Claude ko bolein: 'schema aur share card banao' (site repo ZIP mein chahiye)"),
    ("[Bot agli] PageSpeed/Core Web Vitals watcher (PageSpeed API key chahiye) + GA4 hafta-wari earnings/traffic report", None, None,
     "pehle PageSpeed API key (Google Cloud) banayein, phir Claude ko bolein"),
    ("[Bot agli] YPP watch-hours/Shorts-views ka asli ginti: YouTube Analytics ki ijaazat (OAuth scope) chahiye - abhi TV-login se nahi milta", None, None,
     "owner: YouTube login dobara 'analytics' ijaazat ke saath; phir Claude ko bolein"),
    ("[Owner] Bot ne 'chalu karein?' prastav bheja ho (Telegram digest) to ✅✅ dabayein; 'features' likhkar dekhein kya chalu/band hai", None, None,
     "ho jaye to likhein: 'ho gaya features'"),
    ("[Owner] GitHub se kabhi bhi update: GitHub par naya ZIP (code) rakhein -> Telegram par wahi ZIP bot ko bhejein -> ✅ install. Naya feature chalu karne ke command: docs/FEATURES.md", None, None,
     "ho jaye to likhein: 'ho gaya github update'"),
]


SEED_V253 = [            # v2.5.3 (5 Nov 2026): FINAL Pro Plan ke jo kaam bot/zip se nahi ho sakte (site repo / developer / owner) - privacy policy ke andar
    ("[P0 Developer W1] SIP page 'Aage ye padhein': link ka naam aur link alag (Gold vs SIP -> sovereign-gold-bond, Expense Ratio -> real-return, Exit Load -> swp). "
     "Template bug poori site par: slug se naam banao. Bot 'site scan' list dega (docs/SITESCAN.md)", None, None, "ho jaye to likhein: 'ho gaya w1 links'"),
    ("[P0 Developer W5] Patle tool page (<300 shabd): 'site scan' ki list se 30 sabse accha pakke karo (formula + 3 misaal + FAQ + 'Reviewed on'); baaki par content ya noindex", "2026-11-10", None,
     "ho jaye to likhein: 'ho gaya w5 thin'"),
    ("[P0 Developer W2] Privacy sec. 8: Instagram 'LINK likhne par private reply' wali line hatao/narm karo (bot DM/'comment LINK' nahi karta; @sunonatak/@labhlodeals DM 27/28 Nov tak band). "
     "'Aakhri update' tareekh badlo. Text docs/PRIVACY_PATCH.md mein", None, None, "ho jaye to likhein: 'ho gaya w2 privacy'"),
    ("[P0 Developer W4] Homepage + har tool/guide ke neeche 'Aaj ke sawal' (/jawab) block + 'Hamare channel' strip (Telegram/WhatsApp pehle). Bot sirf /jawab, links, about, articles mein line jodta hai",
     "2026-11-10", None, "ho jaye to likhein: 'ho gaya w4 home'"),
    ("[P0 Developer D5] Certified CMP + ad-slot code (flag ke peeche, default OFF): 3 slot, min-height, 'Advertisement' label, button se 200px door, ek screen par 2 se zyada nahi, "
     "zaroori pages par nahi, Auto Ads nahi. Bot 'canary' check karega", "2026-11-12", None, "ho jaye to likhein: 'ho gaya d5 slot'"),
    ("[P0 Developer D6] Verify aur screenshot/HTTP status bhejein: robots.txt, sitemap.xml (/jawab shamil), ads.txt jagah, /jawab live, galat URL par 404 status", "2026-11-10", None,
     "ho jaye to likhein: 'ho gaya d6 verify'"),
    ("[P1 Developer W6] Google Fonts self-host (Baloo2 file bot assets mein hai); homepage ki line 'Calculation aapke browser mein hoti hai' (GA4 + Fonts ka mismatch hatao)", "2026-11-20", None,
     "ho jaye to likhein: 'ho gaya w6 fonts'"),
    ("[P1 Developer W8/B8] Har finance page par 'Reviewed on' + official source. Budget 1 Feb 2027 ke 7 din ke andar income tax/TDS/NPS/PPF pages; 1 Apr FY badlav", "2027-01-25", None,
     "ho jaye to likhein: 'ho gaya w8 review'"),
    ("[P1 Developer W7/D8] Top 5 tools ka reviewed English + Devanagari (hreflang), phir GSC dekh kar badhao. Machine-translate nahi", "2026-11-25", None, "ho jaye to likhein: 'ho gaya w7 lang'"),
    ("[P1 Developer W10/D9] Schema: BreadcrumbList, Article, WebApplication, Organization/Person. QAPage kabhi nahi; Rich Results Test ka jawab", "2026-11-25", None, "ho jaye to likhein: 'ho gaya w10 schema'"),
    ("[P1 Developer W11/D10] /editorial-policy (data kahan se, kab update, galti kaise batayein; asli qualification) + result share-card + embed widget", "2026-11-30", None,
     "ho jaye to likhein: 'ho gaya w11 editorial'"),
    ("[P1 Developer D15/T2] /jawab par code search + auto-suggest + thumbnail grid + smart 404 (galat code par 'aaj ke top 5 jawab'). JSON index; koi data server par nahi", "2026-11-25", None,
     "ho jaye to likhein: 'ho gaya d15 search'"),
    ("[P1 Developer D14/T12-T15] Honest 'Tap to guess' (vote % sirf asli count se), accordion, 'Suno' audio, Surprise-me, related slider (4), category tags. Nakli % kabhi nahi", "2026-12-05", None,
     "ho jaye to likhein: 'ho gaya d14 retention'"),
    ("[P1 Developer D11/B9] Telegram opt-in bot ('roz ka sawal', score/reminder, 'data hatao'; phone number nahi; 30 din). Digest ke baad ka agla kadam", "2026-12-05", None,
     "ho jaye to likhein: 'ho gaya d11 optin'"),
    ("[P1 Developer D12/T18-T19] Web push (OneSignal, sirf opt-in, roz 1 se zyada nahi) + weekly digest + privacy page mein likhna", "2026-12-15", None, "ho jaye to likhein: 'ho gaya d12 push'"),
    ("[P1 Developer D13/W12] /services page: 3-4 asli namoone, WhatsApp button, form (budget + kaam ka type); test submit email par aaye", "2026-11-25", None, "ho jaye to likhein: 'ho gaya d13 services'"),
    ("[Owner T4] Har hafte 1 lambi hub video (8-12 min, 'is hafte ke 10 sawal'): description mein links + chapters; Shorts mein 'Related video' se jodo. YouTube Channel Links mein site + Telegram", None, None,
     "ho jaye to likhein: 'ho gaya t4 hub'"),
    ("[Owner T7/B21] Roz 21:00 par bot Story link-sticker yaad dilata hai - Instagram Story mein sticker aap lagayein (API nahi deta)", None, None, "ho jaye to likhein: 'ho gaya t7 story'"),
    ("[Owner] Bot mein 'jawab digest chalu' (dohri pushti) - roz 20:30 par ek digest; 'site scan' (Ravivaar apne aap); 'ypp haal'", None, None, "ho jaye to likhein: 'ho gaya digest'"),
    ("[Owner YPP] 31 Jan 2027 tak purani seema (1,000 subs + 4,000 hours / 10M Shorts) mein jo channel pahunche wo apply kare; 1 Feb se 8,000 hours / 20M. YouTube Studio -> Earn dekhein. "
     "Sabse paas wale 1-2 channel par dhyan (bot 'ypp haal')", None, None, "ho jaye to likhein: 'ho gaya ypp plan'"),
    ("[Owner] Google Search Console + GA4: UTM (utm_content=c<code>) se 'kaunsi video se traffic' hafte mein dekhein; GSC query -> page sudhaar (bot Ravivaar idea deta hai)", None, None,
     "ho jaye to likhein: 'ho gaya ga4 utm'"),
    ("[P2] Backup ad network (traffic kuch hazaar daily hone par), calculator embed outreach, Tier-1 English channel, B18 invalid-click shield (AdSense chalne ke baad), "
     "PageSpeed API key (B7), hafte mein 2-3 naye lekh (10/din ke andar)", "2027-01-15", None, "ho jaye to likhein: 'ho gaya p2'"),
    ("[Bot agli release] Policy-change watcher (YouTube/Meta/AdSense/Pinterest policy hash), quality governor (templated content), weekly quiz, schema/share-card generator, Hindi/English draft - pehle owner ki pushti", None, None,
     "ye Claude/developer ka kaam hai; ho jaye to likhein: 'ho gaya bot agli'"),
]


SEED_V252 = [            # v2.5.2 (5 Nov 2026): audit ke baad naye kaam
    ("Bot mein 'canary' likhein - website ka haal (/, /jawab, privacy, soft-404, sitemap). Koi ❌ ho to screenshot Claude ko", None, None,
     "ho jaye to likhein: 'ho gaya canary'"),
    ("Bot mein 'adsense haal' likhein - AdSense taiyari ki live jaanch. Jawab ka screenshot Claude ko", None, None,
     "ho jaye to likhein: 'ho gaya adsense haal'"),
    ("AdSense: 20-30 sabse accha page chun kar padhein (har tool page par misaal + FAQ + 'aakhri jaanch' tareekh). 10 kamzor tool page "
     "par text badhwayein ya noindex karwayein (apply se pehle)", "2026-11-12", None, "ho jaye to likhein: 'ho gaya adsense content'"),
    ("AdSense → Privacy & messaging → Certified CMP chalu karein (EU/UK visitors). Phir adsense.google.com par sabhisaab.com apply", "2026-11-16", None,
     "ho jaye to likhein: 'ho gaya adsense apply'"),
    ("AdSense approve hone par: bot ko 'adsense id pub-XXXXXXXXXXXXXXXX' (ads.txt) → ✅✅. Phir privacy page ka 'abhi koi vigyapan nahi' "
     "hatwayein (Claude/developer ko batayein)", "2026-11-17", None, "ho jaye to likhein: 'ho gaya adsense id'"),
    ("Privacy page: Instagram 'LINK likhne par private reply' wali line asli niyam se milwayein (bot 'comment LINK / DM' kabhi nahi karta). "
     "Developer ko batayein - site repo ka privacy.html", None, None, "ho jaye to likhein: 'ho gaya privacy ig'"),
]


SEED_V250 = [
    ("Facebook comment padhne ki ijaazat: Meta app mein 'pages_read_user_content' + 'pages_manage_engagement' jodein, phir page token dobara",
     None, None, "developers.facebook.com → aapki app → Use cases / Permissions → dono jodein → Graph API Explorer se naya page token "
                 "(chaaron page chunkar) → bot ko waise hi bhejein jaise pehle bheja tha. Ho jaye to: 'ho gaya fb comment'"),
    ("Google Search Console: 4 'URL is unknown to Google' page ke liye 'Request indexing' (ye sirf aap kar sakte hain)",
     None, None, "search.google.com/search-console → upar 'Inspect any URL' mein page daalein → 'Request indexing'. Page: "
                 "delivery-date-calculator, fire-number-calculator, random-number-generator, notice-period-buyout-calculator. "
                 "Roz 10 tak. Ho jaye to: 'ho gaya gsc request'"),
]

SEED_V240 = [
    ("(Marzi) Second admin: abhi koi nahi - kabhi chahiye ho to us vyakti ka Telegram ID bot ko dein (sirf dekhne/manzoori ke haq)",
     None, None, "Owner ne 4 Nov ko kaha: abhi nahi. Ho jaye to: 'ho gaya admin'"),
]


SEED_V260 = [            # v2.6.0 (9 Nov 2026): Claude ka poora audit (bot + website + policy) - docs/AUDIT_9NOV2026.md
    ("[P0 Owner] Website W7 ZIP (W7-site-fix-9nov.zip) bot ko → '🌐 Haan' (10 galat link + 3 khud-link theek; privacy/terms sach ke hisaab se: "
     "Gemini free-tier, Cloudflare Workers AI, 3 din app-button, AI label; EMI 1-40 lakh table, TB/GB/MB, mutthi table)", None, "w7",
     "Bot khud jaanchta hai - lagte hi list se hatega. Ya likhein: 'ho gaya w7'"),
    ("[P0 Owner] Facebook Pahadi Hisaab: comment padhne ki ijaazat (Meta #10). developers.facebook.com/tools/explorer → App: Sabhisaab Publisher → "
     "'Get Page Access Token' → Pahadi page → pages_read_user_content + pages_manage_engagement + pages_read_engagement ✅ → Generate → token bot ko", None, "fb_perm",
     "Bot 2 din tak padhna chalta dekh kar khud hatayega. Ya: 'ho gaya fb pahadi token'"),
    ("[Owner, marzi] Phone par Private DNS (VPN ki zaroorat nahi, banking/UPI par asar nahi): Settings → Connections → More connection settings → "
     "Private DNS → 'Private DNS provider hostname' → dns.google → Save", None, None, "ho jaye to: 'ho gaya private dns'"),
    ("[Owner] GSC Request indexing dobara (pichhli 2 Nov - 14 din baad, roz 1-2): fire-number-calculator, notice-period-buyout-calculator, "
     "delivery-date-calculator, number-system-converter, random-number-generator, stopwatch-online, buy-vs-rent-guide", "2026-11-16", None,
     "search.google.com/search-console → Inspect any URL → Request indexing. Ho jaye to: 'ho gaya gsc dobara'"),
    ("[Developer] Do calculator ek hi kaam ke: /tax-regime-compare-calculator aur /old-vs-new-tax-regime-calculator (Google mein aapas mein takraav). "
     "Ek ko mazboot karo, doosre ka content alag (jaise salary-wise table) ya canonical - bina URL hataye", "2026-11-20", None,
     "Claude ko bolein: 'tax regime do page theek karo'. Ho jaye to: 'ho gaya tax regime'"),
]


# v2.6.2 (9 Nov, Claude ne GitHub + live site se jaancha): jo kaam ho chuke ya dohre hain
DONE_V262 = [
    ("Website W6 ZIP (W6-video-link-29oct.zip)", lambda: _site_has("install-app.js", "videos.json"), "site par videos.json + 'Is hisaab ki video' live"),
    ("Website W4 ZIP (W4-site-fix-29oct.zip)", lambda: _site_has("install-app.js", "sh_a2hs_dismissed"), "Home-screen button + nav live (W4)"),
    ("Bot mein 'canary' likhein", lambda: True, "bot har deploy ke baad khud canary chalata hai - owner ko likhne ki zaroorat nahi"),
    ("Bot mein 'adsense haal' likhein", lambda: True, "bot ne 9 Nov ko khud chalaya; 'adsense haal' kabhi bhi"),
    ("(Marzi) Google Cloud mein 'Google Analytics Data API'", _ga_ok, "GA Data API chal raha (website report mein 'kitni der ruke' aa raha)"),
    ("Facebook comment padhne ki ijaazat: Meta app mein", lambda: any("[P0 Owner] Facebook Pahadi" in (o.get("x") or "") for o in state.get("todo") or []),
     "dohra: sirf Pahadi page ruka hai - '[P0 Owner] Facebook Pahadi' wala kaam dekhein"),
    ("Google Search Console: 4 'URL is unknown to Google'", lambda: True, "dohra: 16 Nov wale 'GSC Request indexing dobara' (7 page) mein shamil"),
    ("[Developer D15] /jawab par code search box", lambda: True, "v2.6.0: /jawab par code/shabd khoj + channel button bana"),
    ("[P0 Developer D6] Verify aur screenshot", lambda: True, "Claude ne jaancha (9 Nov): robots khula + Sitemap line, sitemap A-Z (/jawab shamil), ads.txt jagah, 404.html noindex"),
    ("[P0 Developer W5] Patle tool page", lambda: True, "Claude scan (9 Nov): koi asli page 300 shabd se kam nahi (sabse chhota tool page ~880)"),
    ("[P1 Developer W10/D9] Schema", lambda: True, "Claude ne jaancha: har page par WebApplication/Article + FAQPage + BreadcrumbList; homepage/about/author par Organization + Person pehle se"),
    ("[P0 Developer B1/P0-1] /jawab ka naya UI", lambda: True,
     "v2.6.2: har sawal ka dabba (code+channel+tarikh), khoj + channel button, '✅ sahi tha / ❌ galat' + streak (sirf browser); jawab kabhi lock nahi. 4-option wala tap-to-guess nahi (sawal ke vikalp data mein nahi)"),
    ("[P0 Developer D5] Certified CMP + ad-slot code", lambda: True,
     "CMP AdSense ke andar chalu hota hai (owner ka 16 Nov kaam); ad slot sirf approval ke baad. Site jodna: 'adsense id pub-...' (ads.txt + meta)"),
]


def fix_list_v262():
    import datetime as _d
    lst, moved, keep = state.get("todo") or [], [], []
    for o in lst:
        x = o.get("x", "")
        hit = next(((c, n) for k, c, n in DONE_V262 if x.startswith(k) or k in x), None)
        if hit:
            try:
                ok = hit[0]()
            except Exception:
                ok = False
            if ok:
                moved.append({**o, "done": str(_d.date.today()), "by": "bot-safai", "note": hit[1]})
                continue
        if (x.startswith("[P0 Developer W4] Homepage") or x.startswith("[Developer] Do calculator ek hi kaam")
                or x.startswith("[P0 Developer P0-2] Privacy page")) and not o.get("auto"):
            o = {**o, "auto": "w8"}
        if x.startswith("[P1 Developer W11/D10] /editorial-policy"):
            o = {**o, "x": "[P1 Developer W11] Result share-card + embed widget (editorial niti W8 mein about#editorial-niti par ban gayi)"}
        if x.startswith("(Marzi) Google Cloud mein 'Google Analytics Data API'") and not o.get("auto"):
            o = {**o, "auto": "ga4"}
        keep.append(o)
    state.put("todo", keep)
    if moved:
        state.update("todo_done", lambda l: ((l or []) + moved)[-200:], [])
    add("[P0 Owner] Website W8 ZIP (W8-site-9nov.zip) bot ko → '🌐 Haan' (homepage par 'Aaj ke sawal', har tool page ke neeche "
        "'Aaj ka sawal' dabba + Telegram/WhatsApp, sitemap A-Z)", how="Bot khud jaanchta hai - lagte hi hatega. Ya: 'ho gaya w8'", auto="w8")
    add("[Owner] AdSense mein site jodte samay: AdSense → Sites → sabhisaab.com → 'Meta tag' chunein → apna pub-ID copy → bot mein "
        "'adsense id pub-XXXXXXXXXXXXXXXX' → ✅✅ (ads.txt + homepage meta, koi ad nahi dikhta) → 15 min baad AdSense mein Verify → Request review",
        how="Ho jaye to: 'ho gaya adsense jodna'", after="2026-11-16")
    _dirty()
    _close_old_queries()


def _close_old_queries():
    """QUERIES 'khule' jo ab ban chuke: Pinterest views (tool 'pinterest'), video-link traffic (website traffic), trading (niyam: bot nahi chhedta)."""
    import json as _j
    try:
        from .updater import QFILE
        rows = [_j.loads(x) for x in QFILE.read_text(encoding="utf-8").splitlines() if x.strip()]
    except Exception:
        return
    ch = False
    for r in rows:
        q = (r.get("q") or "").lower()
        if r.get("open") and (("pinterest" in q and ("dekha" in q or "kitne" in q)) or ("link" in q and "website" in q)
                              or "nifty" in q or "chart" in q):
            r["open"] = False
            r["closed"] = "v2.6.2: ab chalta hai (pinterest / website traffic 'hamare link se') ya niyam (trading bot nahi chhedta)"
            ch = True
    if ch:
        QFILE.write_text("".join(_j.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


INFO_V264 = [   # (shuru ka text, note) - kaam nahi, jaankari thi; list se hatao taaki sirf asli kaam dikhe
    ("[Owner] GitHub se kabhi bhi update", "jaankari: ZIP bot ko bhejna hi update hai (docs/FEATURES.md)"),
    ("[Owner] Google Search Console + GA4: UTM", "bot khud batata hai: 'website traffic' mein 'hamare link se' (v2.6.0)"),
    ("[Owner YPP] 31 Jan 2027 tak purani seema", "jaankari: 'ypp haal' mein roz dikhta hai"),
    ("[Owner] Purani reels: bot 'jawab haal'", "jaankari: /jawab par 1,200 jawab code-khoj ke saath (v2.6.0)"),
    ("[Owner] Bot ne 'chalu karein?' prastav", "jaankari: prastav aane par hi ✅✅ - alag kaam nahi"),
    ("[Owner T4] Har hafte 1 lambi hub video", "dohra: 'Har brand ki 1 hub lambi video' wala kaam hi rakha"),
    ("(Marzi) Second admin", "owner ne 4 Nov ko mana kiya - zaroorat ho to 'list mein daalo second admin'"),
    ("[Bot agli] Schema injector", "schema har page par pehle se (Claude 10 Nov); share-card wala kaam alag (W11) list mein"),
    ("[P1 Developer D15/T2] /jawab par code search", "v2.6.0-2.6.3: khoj, channel button, Kram, purane code ka anchor bane"),
]


INFO_V292 = [
    ("Har brand ki 1 'hub' lambi video", "v2.7.0 se bot har brand ki har hafte khud banata hai (hubvideo) - owner ko kuch nahi"),
    ("[Owner] Har brand ka '/analytics' login", "10 Nov: chaaron channel jude (bot ne pakka kiya)"),
    ("[Bot agli] Weekly quiz generator", "v2.7.0 hubvideo + v2.7.3 qplan + v2.8.0 paheli generator"),
    ("[Bot agli] YPP watch-hours/Shorts-views ka asli ginti", "10 Nov '/analytics' login - 'ypp haal' mein asli"),
    ("[P0 Bot agli - video] V1 option", "v2.7.x: hook line, vikalp pehle second se, 50-50 (V3), karaoke (V4), naye card (neon4/bar/light3/versus)"),
    ("[P1 Bot agli] A1 asli % engine", "v2.8.0 votes.py (30+ vote) + v2.9.0 karaoke + moving bg pehle se"),
    ("[P1 Bot agli] Web Stories + Pinterest pins", "v2.9.1 webstory.py + toolpin.py + tyohaar calendar (v2.8.2)"),
    ("[Bot agli] Telegram opt-in bot", "v2.9.2 quizbot.py (owner ka token aate hi)"),
]


INFO_V293 = [
    ("YouTube channel links (4 channel)", "owner ne 10 Nov ko lagaye (screenshot: Pahadi par sabhisaab.com + Telegram)"),
    ("Instagram/Facebook/Threads bio mein", "owner ne 10 Nov ko lagaye (screenshot: IG Money, Threads Deals, FB Labh Lo)"),
    ("Har brand ki 1 'hub' lambi video", "bot khud har hafte banata hai (v2.7.0)"),
]


DONE_V295 = [
    ("[Bot agli] Quality governor", "v2.7.x-2.9.5: andaaz/naam/rang/card rotate + har platform ki alag pehli line (audit.platform_head)"),
    ("[Bot agli] PageSpeed/Core Web Vitals watcher", "v2.9.5: har Ravivaar 5 page ki mobile speed (key 'psi key ...' se)"),
    ("[Bot agli] Purani 3-ank code wali reels", "v2.9.5: reel_codes -> zindagi bhar ka register (/jawab khoj mein)"),
    ("[Bot agli] /jawab ke channel-wise aur mahine-wise alag page", "NAHI karna - owner ka niyam: /jawab par sirf 8, baaki khoj"),
]


DONE_V302 = [
    ("Cloudflare ZARAZ band karein", "11 Nov 07:22 owner ne Configuration Rule (stories par Zaraz band) lagaya; 07:32 GSC: 'Web Story is valid' ✅"),
    ("Facebook Pahadi Hisaab: comment padhne ki ijaazat", "System user 'sabhisaab-bot' ke paas Pahadi page Full access (10 Nov screenshot); "
                                                          "11 Nov Comment haal mein FB ijaazat ki koi galti nahi. Galti aayi to bot khud dobara likhega."),
]


def fix_list_v302():
    import datetime as _d
    lst, moved, keep = state.get("todo") or [], [], []
    for o in lst:
        hit = next((n for k, n in DONE_V302 if k in o.get("x", "")), None)
        if hit:
            moved.append({**o, "done": str(_d.date.today()), "by": "owner (screenshot se pakka)", "note": hit})
        else:
            keep.append(o)
    state.put("todo", keep)
    if moved:
        state.update("todo_done", lambda l: ((l or []) + moved)[-200:], [])
    _dirty()


def fix_list_v301():
    add("[P0 Owner] Cloudflare ZARAZ band karein (Web Story 'invalid' ki asli wajah - Zaraz har page mein apni script daalta hai, "
        "AMP mein mana): dash.cloudflare.com → sabhisaab.com chunein → baayein menu 'Zaraz' (na dikhe to upar search mein 'Zaraz') → "
        "Zaraz ki setting mein 'Disable Zaraz' / toggle OFF → confirm. (Zaraz khaali hai - GA website mein alag se laga hai, kuch nahi tootega.) "
        "Phir GSC: https://sabhisaab.com/stories/pahadi-quiz-2026-w46 → 'Request indexing'",
        how="Bot mein 'amp jaanch' likhein - ✅ aaye to: 'ho gaya zaraz'")
    _dirty()


def fix_list_v296():
    """11 Nov: line mein purani 'SIP/loan' wali video (Honeymoon Budget: loan ya SIP) - owner ka niyam (3 aam channel par SIP nahi)."""
    try:
        from . import pipeline as _P, qplan as _Q
        for jid, j in list(_P.jobs().items()):
            if j.get("status") not in ("waiting", "approved", "need_login", "partial"):
                continue
            title = ""
            try:
                title = _P._meta(j).get("title", "")
            except Exception:
                title = j.get("title", "")
            if _Q.blocked(j.get("brand", ""), title):
                j["status"], j["note"] = "cancelled", "owner niyam: SIP/FD/loan vishay nahi (v2.9.6)"
                _P.save_job(jid, j)
    except Exception as e:
        from .log import log as _lg
        _lg(f"fix_v296: {e}")


def fix_list_v295():
    import datetime as _d
    lst, moved, keep = state.get("todo") or [], [], []
    for o in lst:
        hit = next((n for k, n in DONE_V295 if k in o.get("x", "")), None)
        if hit:
            moved.append({**o, "done": str(_d.date.today()), "by": "Claude v2.9.5", "note": hit})
        else:
            keep.append(o)
    state.put("todo", keep)
    if moved:
        state.update("todo_done", lambda l: ((l or []) + moved)[-200:], [])
    try:
        from . import answers as _A
        _A.archive_import_codes()
    except Exception:
        pass
    _dirty()


def fix_list_v294():
    """Owner ne bahas pakka kiya tha (4:08) - ab owner ne variety maangi: andaaz phir baari-baari + har channel ka bhi."""
    state.put("hook_mode", "rotate")
    state.put("hook_mode_brand", {})
    import datetime as _d
    lst, moved, keep = state.get("todo") or [], [], []
    for o in lst:
        x = o.get("x", "")
        if "Facebook Pahadi Hisaab: comment padhne" in x:
            o = {**o, "how": ("business.facebook.com/settings/system-users → sabhisaab-bot → 'Generate new token' → App: Sabhisaab "
                              "Publisher → Expiry: Never → permissions tick (pages_read_engagement, pages_read_user_content, "
                              "pages_manage_engagement, pages_manage_posts, pages_show_list, instagram_basic, instagram_content_publish, "
                              "instagram_manage_comments, business_management) → Generate → token copy → bot chat mein paste. "
                              "Phir: 'ho gaya fb pahadi'")}
        keep.append(o)
    state.put("todo", keep)
    _dirty()


def fix_list_v293():
    import datetime as _d
    lst, moved, keep = state.get("todo") or [], [], []
    for o in lst:
        hit = next((n for k, n in INFO_V293 if k in o.get("x", "")), None)
        if hit:
            moved.append({**o, "done": str(_d.date.today()), "by": "owner (screenshot)", "note": hit})
        else:
            keep.append(o)
    state.put("todo", keep)
    if moved:
        state.update("todo_done", lambda l: ((l or []) + moved)[-200:], [])
    _dirty()


def fix_list_v292():
    import datetime as _d
    lst, moved, keep = state.get("todo") or [], [], []
    for o in lst:
        x = o.get("x", "")
        hit = next((n for k, n in INFO_V292 if k in x), None)
        if hit:
            moved.append({**o, "done": str(_d.date.today()), "by": "bot-safai", "note": hit})
            continue
        keep.append(o)
    state.put("todo", keep)
    if moved:
        state.update("todo_done", lambda l: ((l or []) + moved)[-200:], [])
    add("[Owner] OneSignal: bot mein bhejein -> onesignal <App ID> <API key> (ek hi message; bot turant chat se mitata hai)",
        how="Bot khud website par button laga dega; ho jaye to apne aap list se hatega", auto="push")
    add("[Owner] Quiz bot: bot mein bhejein -> quiz bot token <BotFather wala token> (ek hi message; bot turant mitata hai)",
        how="Bot khud quiz bot chalu karega; ho jaye to apne aap hatega", auto="quizb")
    add("[Owner] Telegram channel @sabhisaab mein galti se PIN hua 'ho gaya welcome pin' message delete karein, phir bot mein likhein: welcome pin",
        how="Bot asli welcome post (saare official link) daal kar pin kar dega; ho jaye to: 'ho gaya welcome pin'")
    _dirty()


def fix_list_v271():
    add("[Owner] Backup password naya banwayein (pichhla save nahi hua tha): bot mein 'backup password reset' → ✅✅ → jo password aaye use "
        "Google Keep / Notes / kaagaz par likhein (Telegram par backup ke saath nahi) → '✅ Maine save kar liya'",
        how="'Maine save kar liya' dabate hi list se hatega", auto="bkpass")
    _dirty()


def fix_list_v264():
    import datetime as _d
    lst, moved, keep = state.get("todo") or [], [], []
    for o in lst:
        x = o.get("x", "")
        hit = next((n for k, n in INFO_V264 if k in x), None)
        if hit:
            moved.append({**o, "done": str(_d.date.today()), "by": "bot-safai", "note": hit})
            continue
        if "yt comment login" in x and not o.get("auto"):
            o = {**o, "auto": "ytc"}
        keep.append(o)
    state.put("todo", keep)
    if moved:
        state.update("todo_done", lambda l: ((l or []) + moved)[-200:], [])
    add("[Owner] GSC 'Request indexing' (roz max 3, badle hue zaroori page): 10 Nov: https://sabhisaab.com/income-tax-calculator , "
        "https://sabhisaab.com/tax-regime-compare-calculator , https://sabhisaab.com/mahila-samman-calculator | 11 Nov: https://sabhisaab.com/ , "
        "https://sabhisaab.com/tds-calculator , https://sabhisaab.com/jawab",
        how="search.google.com/search-console → upar search dabbe mein URL paste → 'Request indexing'. Sab ho jaye to: 'ho gaya gsc 10nov'")
    _dirty()


def fix_list_v263():
    add("[P0 Owner] Website W9 ZIP (W9-site-10nov.zip) bot ko → '🌐 Haan' (13 tax page par naye Income-tax Act 2025 ka sach, TDS 194H 5%→2% "
        "galti theek, Mahila Samman band hone ki saaf jaankari, chaukidaar ke jhoothe alarm - fonts 404 / RBI / 90 din - theek)",
        how="Bot khud jaanchta hai - lagte hi hatega. Ya: 'ho gaya w9'", auto="w9")
    _dirty()


def fix_list_v261():
    """v2.6.1: policy-watcher, sarkari-dar watcher, keyword auto-sudhaar ban gaye - purane 'Bot agli' kaam itihaas mein."""
    import datetime as _d
    lst, moved, keep = state.get("todo") or [], [], []
    starts = ("[Bot agli] Platform policy-change watcher", "[Bot agli - Phase 2] Sarkari-dar watcher",
              "[Bot agli - Phase 2] Keyword auto-sudhaar")
    for o in lst:
        x = o.get("x", "")
        if x.startswith(starts):
            moved.append({**o, "done": str(_d.date.today()), "by": "bot", "note": "v2.6.1 mein bana (policywatch / factwatch / kwfix)"})
        elif x.startswith("[Bot agli release] Policy-change watcher"):
            moved.append({**o, "done": str(_d.date.today()), "by": "bot",
                          "note": "v2.6.1: policy watcher bana; quality governor/weekly quiz/schema alag kaam ke roop mein list mein hain"})
        else:
            keep.append(o)
    state.put("todo", keep)
    if moved:
        state.update("todo_done", lambda l: ((l or []) + moved)[-200:], [])
    _dirty()


def fix_list_v260():
    """v2.6.0: jo kaam live site par pehle hi ho chuka (privacy sec.8 IG line) - itihaas mein; W1 link ka kaam W7 checker se jode."""
    import datetime as _d
    lst, moved, keep = state.get("todo") or [], [], []
    for o in lst:
        x = o.get("x", "")
        if ("Privacy page: Instagram 'LINK likhne par private reply'" in x or x.startswith("[P0 Developer W2]")
                or x.startswith("[P0 Owner] Bot mein 'privacy ig theek'")):
            moved.append({**o, "done": str(_d.date.today()), "by": "bot-safai",
                          "note": "live privacy.html sec. 8 mein sahi line pehle se hai (Claude audit 9 Nov 2026)"})
            continue
        if x.startswith("[P0 Developer W1]") and not o.get("auto"):
            o = {**o, "auto": "w7"}
        keep.append(o)
    state.put("todo", keep)
    if moved:
        state.update("todo_done", lambda l: ((l or []) + moved)[-200:], [])
    _dirty()


def fix_list_v241():
    """v2.4.1: purana ho chuka kaam itihaas mein (Premium Neon default se look apne aap chal raha)."""
    import datetime as _d
    lst, moved, keep = state.get("todo") or [], [], []
    for o in lst:
        if o.get("x", "").startswith("Sample Studio se chaaron channel ka look pakka"):
            moved.append({**o, "done": str(_d.date.today()), "by": "bot-safai",
                          "note": "ab zaroori nahi - Premium Neon + AI-art default chal raha; badalna ho to '🎨 24 Look'"})
        else:
            keep.append(o)
    state.put("todo", keep)
    if moved:
        state.update("todo_done", lambda l: ((l or []) + moved)[-200:], [])
    _dirty()


SEED_V310 = [            # v3.1.0 (11 Nov 2026): Claude Fable 5.2 ka poora audit (bot + website + VM + policy) - docs/AUDIT_11NOV2026.md
    ("[P0 Owner - faisla] YouTube kamai (YPP): July 2026 ki niti mein 'ek hi saanche ki AI awaaz wali video' par monetization nahi milta. "
     "Har channel par hafte mein 1-2 video APNI awaaz mein (phone se 30-60 sec bol kar bot ko bhejein - sawal samjhana / pahadi shabd bolna); "
     "baaki sab bot karega. Bina iske views aa sakte hain par YPP approval ka khatra", None, None,
     "Poori wajah: GitHub docs/AUDIT_11NOV2026.md hissa A. Shuru kar dein to: 'ho gaya apni awaaz'"),
    ("[P1 Owner - faisla] Gemini ka free quota roz khatam ho raha (VM audit: saare model 'cool', tathya-jaanch/tyohaar-jaanch fail). "
     "Google AI Studio → Billing chalu + mahine ki seema (jaise ₹500) lagayein - tab bot ka dimaag din bhar chalega aur comment text Google ki "
     "training mein nahi jayega", None, None,
     "aistudio.google.com → Settings → Billing. Chalu ho jaye to Claude ko batayein (privacy page ki 'free tier' line badlegi). 'ho gaya gemini billing'"),
    ("[P1 Owner] VM par 14 suraksha update baaki: bazaar band ke samay (raat/Ravivaar) Chowkidar se ya SSH se: "
     "sudo apt update && sudo apt upgrade -y", None, None, "ho jaye to: 'ho gaya vm update'"),
]


def seed_v310():
    import datetime as _d
    day = str(_d.date.today())
    lst = state.get("todo") or []
    have = {o.get("x") for o in lst}
    lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
            for t, a, k, h in SEED_V310 if t not in have]
    state.put("todo", lst)
    _dirty()


DONE_V311 = [            # v3.1.1 (12 Nov): owner ne ye dono kaam kar diye (chat mein video file + VM ke screenshot)
    ("FILE Claude chat mein bhejein", "12 Nov: video mil gayi - 6 kami v3.1.1 mein theek (ROADMAP v3.1.1)"),
    ("14 suraksha update baaki", "12 Nov 02:28 IST: apt upgrade + reboot ho gaya (kernel 7.0.0-1016), sabhinet + trading services chalu"),
]


def fix_list_v311():
    import datetime as _d
    lst, moved, keep = state.get("todo") or [], [], []
    for o in lst:
        hit = next((n for k, n in DONE_V311 if k in o.get("x", "")), None)
        if hit:
            moved.append({**o, "done": str(_d.date.today()), "by": "owner (chat mein pakka)", "note": hit})
        else:
            keep.append(o)
    state.put("todo", keep)
    if moved:
        state.update("todo_done", lambda l: ((l or []) + moved)[-200:], [])
    _dirty()


SEED_V312 = [            # v3.1.2 (12 Nov 2026): traffic plan (docs/TRAFFIC_PLAN.md) + VM screenshot se nikle kaam
    ("[Owner, 1 min] OWNER MODE (aapki apni visit Analytics mein na gini jaaye; IP badle to bhi): bot ka '👤 OWNER MODE taiyaar' sandesh aane "
     "ke baad apne HAR browser mein EK BAAR kholein - phone ka Chrome aur laptop ka Chrome dono: https://sabhisaab.com/#owner-on  "
     "(neeche kone mein kaali patti 'Owner mode' dikhe = chalu). Incognito ya data saaf karne par dobara", None, None,
     "Haal/jaankari: bot mein 'owner mode'. Ho jaye to: 'ho gaya owner mode'"),
    ("[Owner, 2 min] Website ZIP W12 lagne ke 20 minute baad: Google Search Console → upar URL inspection mein "
     "https://sabhisaab.com/nali-mutthi-square-feet daalein → 'Request indexing' (sirf ye 1 page - isi par Hindi wala test hai)", None, None,
     "ho jaye to: 'ho gaya nali index'"),
    ("[Owner, 2 min] Phone ke Chrome ke Incognito tab mein Google par likhein: sab hisaab jawab - pehla nateeja sabhisaab.com/jawab aata hai? "
     "Haan ya nahi Claude ko batayein (haan hua to reel ke ant mein 'Google par khojiye - Sab Hisaab jawab' jodenge)", None, None,
     "ho jaye to: 'ho gaya brand search'"),
    ("[Owner] YouTube Studio (phone app): har nayi Short → Edit → 'Related video' mein us channel ki hafte wali lambi video chunein; "
     "aur channel → Customise → Links mein sabse upar https://sabhisaab.com/jawab rakhein (Shorts ke description ka link click nahi hota - "
     "yahi do jagah se log site par aate hain)", None, None, "ho jaye to: 'ho gaya related video'"),
    ("[Owner, 1 min] VM par purana 'sandbox' mount fail dikh raha hai (reboot ke baad; bot aur trading par koi asar nahi). SSH mein ye do "
     "command chala kar photo Claude ko bhejein: grep -n sandbox /etc/fstab   aur   systemctl cat home-ubuntu-sandbox.mount", None, None,
     "Photo ke baad Claude hatane ki sahi command dega. 'ho gaya sandbox mount'"),
    ("[P0 Developer T1] W12 ka nateeja naapo (docs/TRAFFIC_PLAN.md hissa 4-5): nali page par Devanagari shabd/impression aaye? Aaye to wahi "
     "saancha /bigha-converter se shuru karke ek-ek page par; na aaye to 10 Dec tak ruko, title wapas mat badlo", "2026-11-26", None,
     "docs/TRAFFIC_PLAN.md"),
    ("[P0 Developer T2] /bigha-kitna-hota-hai (har rajya) ka har number us rajya ke rajasv/bhulekh srot se milao + srot ka link + W12 wala "
     "Hindi saancha (naya page nahi). Phir T3: pahadi/zameen ke gehre panne, hafte mein max 2", "2026-11-19", None, "docs/TRAFFIC_PLAN.md hissa 5"),
]


SEED_V330 = [            # v3.3.0 (14 Nov 2026): Uttarakhand page queue
    ("[Owner, 2 min] Pehle bot ZIP v3.3.0 bot ko bhejein -> '✅ Haan, install karo'. Install ho jaye to Uttarakhand queue ZIP "
     "(uk_pages_queue_*.zip) bot ko bhejein -> '✅ Haan, queue mein' -> '✅✅ Haan, pakka'. Roz subah bot khud page live karega aur "
     "GSC ke URL bhejega", None, "pq", "Queue mil gayi to apne aap hatega. Haal: 'queue haal'"),
    ("[Developer] Uttarakhand pages: 'Gaon ki chaupal' (logon ki yaadein) aur 1-click poll - sirf moderation + asli ginti (sabhisaab-votes, "
     "30+ vote ke baad hi %) + privacy page mein pehle likhne ke baad. Nakli % kabhi nahi", "2026-12-15", None, "docs/ROADMAP.md v3.3.0"),
    ("[Developer] Uttarakhand pages ke GSC nateeje (impression/query) dekh kar title/description sudhaar - sirf jahan 1000+ impression aur "
     "CTR kam ho; har badlaav ek baar, 28 din ruk kar naapo (auto-rewrite nahi)", "2027-01-05", None, "docs/ROADMAP.md v3.3.0"),
]


def seed_v330():
    import datetime as _d
    day = str(_d.date.today())
    lst = state.get("todo") or []
    have = {o.get("x") for o in lst}
    lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
            for t, a, k, h in SEED_V330 if t not in have]
    state.put("todo", lst)
    _dirty()


def seed_v312():
    import datetime as _d
    day = str(_d.date.today())
    lst = state.get("todo") or []
    have = {o.get("x") for o in lst}
    lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
            for t, a, k, h in SEED_V312 if t not in have]
    state.put("todo", lst)
    _dirty()


def seed_todo():
    if not state.get("seed_v330"):
        state.put("seed_v330", True)
        try:
            seed_v330()
        except Exception as e:
            from .log import log as _lg
            _lg(f"seed_v330: {e}")
    if not state.get("seed_v312"):
        state.put("seed_v312", True)
        try:
            seed_v312()
        except Exception as e:
            from .log import log as _lg
            _lg(f"seed_v312: {e}")
    if not state.get("seed_v310"):
        state.put("seed_v310", True)
        try:
            seed_v310()
        except Exception as e:
            from .log import log as _lg
            _lg(f"seed_v310: {e}")
    if not state.get("fix_v311"):
        state.put("fix_v311", True)
        try:
            fix_list_v311()
        except Exception as e:
            from .log import log as _lg
            _lg(f"fix_v311: {e}")
    if not state.get("fix_v302"):
        state.put("fix_v302", True)
        fix_list_v302()
    if not state.get("fix_v301"):
        state.put("fix_v301", True)
        fix_list_v301()
    if not state.get("fix_v296"):
        state.put("fix_v296", True)
        fix_list_v296()
    if not state.get("fix_v295"):
        state.put("fix_v295", True)
        try:
            fix_list_v295()
        except Exception as e:
            from .log import log as _lg
            _lg(f"fix_list_v295: {e}")
    if not state.get("fix_v294"):
        state.put("fix_v294", True)
        try:
            fix_list_v294()
        except Exception as e:
            from .log import log as _lg
            _lg(f"fix_list_v294: {e}")
    if not state.get("fix_v293"):
        state.put("fix_v293", True)
        try:
            fix_list_v293()
        except Exception as e:
            from .log import log as _lg
            _lg(f"fix_list_v293: {e}")
    if not state.get("fix_v292"):
        state.put("fix_v292", True)
        try:
            fix_list_v292()
        except Exception as e:
            from .log import log as _lg
            _lg(f"fix_list_v292: {e}")
    if not state.get("fix_v271"):
        state.put("fix_v271", True)
        try:
            fix_list_v271()
        except Exception as e:
            from .log import log as _lg
            _lg(f"fix_list_v271: {e}")
    if not state.get("fix_v264"):
        state.put("fix_v264", True)
        try:
            fix_list_v264()
        except Exception as e:
            from .log import log as _lg
            _lg(f"fix_list_v264: {e}")
    if not state.get("fix_v263"):
        state.put("fix_v263", True)
        try:
            fix_list_v263()
        except Exception as e:
            from .log import log as _lg
            _lg(f"fix_list_v263: {e}")
    if not state.get("fix_v262"):
        state.put("fix_v262", True)
        try:
            fix_list_v262()
        except Exception as e:
            from .log import log as _lg
            _lg(f"fix_list_v262: {e}")
    if not state.get("fix_v261"):
        state.put("fix_v261", True)
        fix_list_v261()
    if not state.get("seed_v260"):
        import datetime as _d
        day = str(_d.date.today())
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V260 if t not in have]
        state.put("todo", lst)
        state.put("seed_v260", True)
        fix_list_v260()
        _dirty()
    if not state.get("seed_v257"):
        import datetime as _d
        day = str(_d.date.today())
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V257 if t not in have]
        state.put("todo", lst)
        state.put("seed_v257", True)
        _dirty()
    if not state.get("seed_v256"):
        import datetime as _d
        day = str(_d.date.today())
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V256 if t not in have]
        state.put("todo", lst)
        state.put("seed_v256", True)
        _dirty()
    if not state.get("seed_v255"):
        import datetime as _d
        day = str(_d.date.today())
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V255 if t not in have]
        state.put("todo", lst)
        state.put("seed_v255", True)
        _dirty()
    if not state.get("seed_v253"):
        import datetime as _d
        day = str(_d.date.today())
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V253 if t not in have]
        state.put("todo", lst)
        state.put("seed_v253", True)
        _dirty()
    if not state.get("seed_v252"):
        import datetime as _d
        day = str(_d.date.today())
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V252 if t not in have]
        state.put("todo", lst)
        state.put("seed_v252", True)
        _dirty()
    if not state.get("seed_v250"):
        import datetime as _d
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": str(_d.date.today()), "how": h} for t, a, k, h in SEED_V250 if t not in have]
        state.put("todo", lst)
        state.put("seed_v250", True)
        _dirty()
    if not state.get("seed_v241"):
        try:
            fix_list_v241()
        except Exception:
            pass
        state.put("seed_v241", True)
    if not state.get("seed_v240"):
        import datetime as _d
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": str(_d.date.today()), "how": h} for t, a, k, h in SEED_V240 if t not in have]
        state.put("todo", lst)
        state.put("seed_v240", True)
        _dirty()
    if not state.get("seed_v236"):
        import datetime as _d
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": str(_d.date.today()), "how": h} for t, a, k, h in SEED_V236 if t not in have]
        state.put("todo", lst)
        state.put("seed_v236", True)
        _dirty()
    if not state.get("seed_v231"):
        try:
            r_ = fix_list_v231()
            from . import diary
            diary.add("setting", "PENDING list saaf (v2.3.1): " + "; ".join(r_)[:400])
        except Exception as e:
            from .log import log
            log(f"fix_list_v231: {e}")
        state.put("seed_v231", True)
    if not state.get("seed_v230"):
        import datetime as _d
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": str(_d.date.today()), **({"auto": k} if k else {}), "how": h} for t, a, k, h in SEED_V230 if t not in have]
        state.put("todo", lst)
        state.put("seed_v230", True)
        _dirty()
    if not state.get("seed_v220"):
        import datetime as _d
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": str(_d.date.today()), **({"auto": k} if k else {}), "how": h} for t, a, k, h in SEED_V220 if t not in have]
        state.put("todo", lst)
        state.put("seed_v220", True)
        _dirty()
    if not state.get("seed_v219"):
        import datetime as _d
        day = str(_d.date.today())
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V219 if t not in have]
        state.put("todo", lst)
        state.put("seed_v219", True)
        _dirty()
    if not state.get("seed_v214"):
        import datetime as _d
        lst = state.get("todo") or []
        t = ("Chowkidar: 'chowkidar fix' EK BAAR AUR (2 Nov wale badlaav ne sabhinet ko hi list se hata diya tha - "
             "ab sahi sudhaar) → ✅ → ✅✅ (15:35 ke baad)")
        if t not in {o.get("x") for o in lst}:
            lst.append({"x": t, "t": str(_d.date.today()), "auto": "cw_done",
                        "how": "Phir VM bot mein 'Status' - sabhinet dikhe. Bot khud list se hatayega"})
        state.put("todo", lst)
        state.put("seed_v214", True)
        _dirty()
    if not state.get("seed_v2111"):
        import datetime as _d
        day = str(_d.date.today())
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V2111 if t not in have]
        state.put("todo", lst)
        state.put("seed_v2111", True)
        _dirty()
    if not state.get("seed_v211"):
        import datetime as _d
        day = str(_d.date.today())
        lst = [x for x in (state.get("todo") or []) if not x.get("x", "").startswith("Chowkidar abhi bhi 'ytlistener'")]
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V211 if t not in have]
        state.put("todo", lst)
        if not state.get("pin_form"):
            state.put("pin_form", "2026-10-29")          # owner ne 29 Oct 18:47 form bhara (Pinterest ka email aaya)
        state.put("seed_v211", True)
        _dirty()
    if not state.get("seed_v207"):
        import datetime as _d
        day = str(_d.date.today())
        lst = state.get("todo") or []
        have = {o.get("x") for o in lst}
        lst += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V207 if t not in have]
        state.put("todo", lst)
        state.put("seed_v207", True)
        _dirty()
    if not state.get("seed_v206"):
        import datetime as _d
        day = str(_d.date.today())
        lst = state.get("todo") or []
        gone = [x for x in lst if x.get("x", "").startswith("GSC → Indexing → Pages → 'Redirect error' (26) par tap")]
        left = [x for x in lst if x not in gone]
        for x in left:                         # FB Stars kaam: poore steps
            if x.get("x", "").startswith("Facebook (charon page): Professional dashboard → Monetization → 'Stars'"):
                x["how"] = ("facebook.com/professional_dashboard/monetization → Stars → Set up → Terms accept → Payout: "
                            "bank + PAN + tax form → Submit. Har page alag (upar page badal kar). 'ho gaya fb stars'")
        have = {o.get("x") for o in left}
        left += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                 for t, a, k, h in SEED_V206 if t not in have]
        state.put("todo", left)
        state.update("todo_done", lambda l: (l or []) + [{**g, "done": day, "by": "owner"} for g in gone], [])
        state.put("seed_v206", True)
        _dirty()
    if not state.get("seed_v205"):          # v2.0.5: Meta secret mix-up, GSC redirect, Bing sitemap ho gaya, W4 ho gaya
        import datetime as _d
        day = str(_d.date.today())
        done_words = ("Bing Webmaster (bing.com/webmasters", "Google Search Console → Indexing → Pages → neeche",
                      "Website W4 ZIP")
        lst = state.get("todo") or []
        gone = [x for x in lst if x.get("x", "").startswith(done_words)]
        left = [x for x in lst if x not in gone]
        have = {o.get("x") for o in left}
        left += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                 for t, a, k, h in SEED_V205 if t not in have]
        state.put("todo", left)
        state.update("todo_done", lambda l: (l or []) + [{**g, "done": day, "by": "owner"} for g in gone], [])
        state.put("seed_v205", True)
        _dirty()
    if not state.get("seed_v204"):          # v2.0.4 (29 Oct shaam): Chowkidar sahi tareeka, labhlodeals DM, FB, Bing, GSC
        import datetime as _d
        day = str(_d.date.today())
        drop = ("Instagram @labhlodeals: Account Status", "4 Facebook page: Professional dashboard")
        old = [x for x in (state.get("todo") or []) if not x.get("x", "").startswith(drop)]
        have = {o.get("x") for o in old}
        old += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V204 if t not in have]
        state.put("todo", old)
        state.update("todo_done", lambda l: (l or []) + [
            {"x": "Instagram @labhlodeals 'Features you can't use' dekha: DM 30 din band (screenshot mila)", "t": day, "done": day, "by": "owner"},
            {"x": "4 Facebook page monetization dekha: Content monetization invite-only, Stars + Affiliate 'Available'", "t": day, "done": day, "by": "owner"}], [])
        state.put("seed_v204", True)
        _dirty()
    if not state.get("seed_v203"):          # v2.0.3 (29 Oct): Bing hal, Instagram rok, naye kaam, purane sudhaare
        import datetime as _d
        day = str(_d.date.today())
        drop = ("Bing:", "Instagram @sunonatak warning", "Chowkidar mein ytlistener", "AdSense apply (mid-Nov",
                "Telegram + WhatsApp channel par welcome", "Instagram/Facebook/Threads bio mein WhatsApp")
        old = [x for x in (state.get("todo") or []) if not x.get("x", "").startswith(drop)]
        for x in old:                           # GSC wala kaam: saare page index hote hi bot khud band karega
            if x.get("x", "").startswith("GSC Request Indexing"):
                x["auto"] = "gsc_all"
        have = {o.get("x") for o in old}
        old += [{"x": t, "t": day, **({"after": a} if a else {}), **({"auto": k} if k else {}), "how": h}
                for t, a, k, h in SEED_V203 if t not in have]
        old.append({"x": "Facebook/Threads bio mein WhatsApp channel link (Instagram bio mein sirf https://sabhisaab.com - "
                         "naye finance account par extra link Meta shak karta hai)", "t": day,
                    "how": "ho jaye to likhein: 'ho gaya bio'"})
        state.put("todo", old)
        state.update("todo_done", lambda l: (l or []) + [{"x": "Bing support: sabhisaab.com ka mudda hal (29 Oct 2026). "
                                                             "2-3 hafte mein wapas dikhega; sirf badle URL IndexNow se",
                                                        "t": day, "done": day, "by": "owner"}], [])
        state.put("bing_resolved", day)
        state.put("seed_v203", True)
    if not state.get("seed_v20"):           # v2.0: purani GSC list (salary-structure-guide wali) hatao, nayi daalo
        old = [x for x in (state.get("todo") or []) if not x.get("x", "").startswith("GSC Request Indexing")]
        import datetime as _d
        old += [{"x": t, "t": str(_d.date.today())} for t in SEED_V20 if t not in {o.get("x") for o in old}]
        state.put("todo", old)
        state.put("seed_v20", True)
    if state.get("seed_v18"):
        return
    have = {x.get("x") for x in (state.get("todo") or [])}
    import datetime
    day = str(datetime.date.today())
    new = [{"x": s, "t": day} for s in SEED if s not in have]
    if new:
        state.update("todo", lambda l: (l or []) + new, [])
    state.put("seed_v18", True)


def pending_md():
    """v2.0.3: docs/PENDING.md - ek hi jagah SAARE khule kaam (owner + bot/AI), aage ki tareekh wale, aur ho chuke.
    Bot roz 04:00 GitHub copy ke saath likhta hai; koi bhi AI repo padh kar wahin se kaam shuru kare."""
    import datetime
    today = str(datetime.date.today())
    try:
        items = check()
    except Exception as e:
        log(f"pending_md check: {e}")
        items = []
    open_all = [(t, h) for k, d, t, h in items if not d]
    open_ = [x for x in open_all if not is_claude(x[0])]
    dev_ = [x for x in open_all if is_claude(x[0])]
    later = [x for x in (state.get("todo") or []) if x.get("after") and x["after"] > today]
    done = (state.get("todo_done") or [])[-30:]
    lines = ["# PENDING - saare khule kaam (bot roz khud likhta hai)", f"Updated: {datetime.datetime.now():%Y-%m-%d %H:%M} IST", "",
             "Niyam: 🤖 wale kaam bot API se khud jaanchta hai aur ho jaate hi yahan se hata deta hai. Baaki owner",
             "'ho gaya <shabd>' likhta hai. Naya kaam: 'list mein daalo <kaam>'. AI/developer: pehle docs/AI_START.md.", "",
             f"## Abhi khule (owner ke haath ke) - {len(open_)}"]
    lines += [f"- {t}\n  - Kaise: {h}" for t, h in open_] or ["- (koi nahi)"]
    lines += ["", f"## Claude/developer ke kaam - {len(dev_)} (owner ko kuch nahi karna; Claude ko 'continue')"]
    lines += [f"- {t}" for t, h in dev_] or ["- (koi nahi)"]
    lines += ["", "## Aage ki tareekh wale (us din apne aap list mein aayenge)"]
    lines += [f"- {x['after']}: {x['x']}" for x in later] or ["- (koi nahi)"]
    try:
        from . import upgrader
        esc = upgrader.escalate_md().split("## Khule mudde", 1)[-1].split("##", 1)[0].strip()
    except Exception:
        esc = "-"
    lines += ["", "## Bot/AI ke kaam (jo bot khud theek nahi kar paya - docs/ESCALATE.md)", esc or "- (koi nahi)"]
    lines += ["", "## Ho chuke (aakhri 30)"] + [f"- {d.get('done', '')} ({d.get('by', '')}): {d.get('x', '')[:140]}" for d in reversed(done)]
    return "\n".join(lines) + "\n"



STRICT = ("yt_", "an_", "site_sa", "gh_push", "cf_token", "bing_key", "relay")   # inke bina bot kaam nahi kar sakta - asli jaanch hi


def owner_confirm(key):
    """Owner ne kaha 'kar diya' (bot-jaanch wala kaam) -> pakka maano. -> True agar maana"""
    import datetime as _d
    if str(key).startswith(STRICT):
        return False
    state.update("owner_ok", lambda d: {**(d or {}), key: str(_d.date.today())}, {})
    _dirty()
    return True


def find_computed(word):
    """'ho gaya <shabd>' bot-jaanch wale kaam (todo nahi) mein bhi dhoondo. -> [(key, title)]"""
    import difflib
    import re as _re
    ws = [x for x in _re.findall(r"[a-z0-9\u0900-\u097f]+", word.lower()) if len(x) > 1]
    out = []
    for k, t in state.get("pend_order") or []:
        if str(k).startswith("todo_"):
            continue
        toks = _re.findall(r"[a-z0-9\u0900-\u097f]+", str(t).lower())
        sc = sum(max((difflib.SequenceMatcher(None, w, x).ratio() for x in toks), default=0) >= 0.75 for w in ws) / max(1, len(ws))
        if sc >= 0.5:
            out.append((sc, k, t))
    out.sort(key=lambda x: -x[0])
    return [(k, t) for _, k, t in out[:3]]


def by_number(n):
    """v2.1.6: '🧾 Mere kaam' ki list ka n-va kaam -> (key, text)."""
    order = state.get("pend_order") or []
    if 1 <= n <= len(order):
        return order[n - 1]
    return None
