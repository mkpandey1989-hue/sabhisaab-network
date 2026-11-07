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
    items.append(("meta_dm", not state.get("dm_perm_missing"), "Meta App Review: comment 'LINK' par auto-DM",
                  "developers.facebook.com → app 'Sabhisaab Publisher' → App Review → Permissions: instagram_manage_messages "
                  "(+ pages_messaging) → Request → screencast: comment LINK → DM aata hai. Manzoori ke baad bot khud chalu."))
    hub = state.get("hub_videos") or {}
    items.append(("hub", len(hub) >= 4, "Har brand ki 1 'hub' lambi video (clickable website links wali)",
                  "Lambi video banne ke baad bot ko: 'hub video <brand> <youtube link>' (Shorts ka Related video isi par)"))
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


AUTO = {"looks4": _looks4, "cw52": _cw52, "cw_dash": _cw_dash,
        "threads_ok": _threads_all_ok, "pin_oauth": _pin_oauth, "cf_acc": _cf_acc_ok, "cw_done": _cw_done,
        "meta_secret": _meta_secret_ok, "tg_pin": _tg_pinned, "gsc_all": _gsc_all_indexed, "psi": _psi_key, "cf": _cf_ok, "dm_over": _dm_over}


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


def already_done(word):
    w = word.strip().lower()
    return [d for d in (state.get("todo_done") or []) if w and w in d.get("x", "").lower()][-1:]


def _dirty():
    try:
        from . import updater
        updater.mark_dirty()                     # v2.0.4: kaam ho gaya -> docs/PENDING.md GitHub par turant (10 min mein)
    except Exception:
        pass


def report(auto=False):
    items = check()
    prev = state.get("tasks_done") or {}
    newly = [t for k, d, t, _ in items if d and not prev.get(k)]
    state.put("tasks_done", {k: d for k, d, _, _ in items})
    if auto and newly and prev:
        tg.alert("green", "✅ Aapka kaam ho gaya, bot ne LIVE kar diya:\n" + "\n".join(f"• {t}" for t in newly))
    pend = [(k, t, h) for k, d, t, h in items if not d]
    if auto:
        return None
    state.put("pend_order", [[k, t] for k, t, _ in pend])     # v2.1.6: 'ho gaya 3' ke liye number
    done_n = sum(1 for _, d, _, _ in items if d)
    lines = [f"🧾 Aapke haath ke kaam: {done_n}/{len(items)} ho gaye"]
    if pend:
        lines.append("\n⬜ Baaki (🤖 = bot khud jaanch kar hatayega; baaki ho jaye to 'ho gaya <number>'):")
        lines += [f"{n}. {'🤖 ' if not str(k).startswith('todo') else ''}{t}\n   👉 {h}" for n, (k, t, h) in enumerate(pend, 1)]
    else:
        lines.append("🎉 Sab ho gaya!")
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


def seed_todo():
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
    open_ = [(t, h) for k, d, t, h in items if not d]
    later = [x for x in (state.get("todo") or []) if x.get("after") and x["after"] > today]
    done = (state.get("todo_done") or [])[-30:]
    lines = ["# PENDING - saare khule kaam (bot roz khud likhta hai)", f"Updated: {datetime.datetime.now():%Y-%m-%d %H:%M} IST", "",
             "Niyam: 🤖 wale kaam bot API se khud jaanchta hai aur ho jaate hi yahan se hata deta hai. Baaki owner",
             "'ho gaya <shabd>' likhta hai. Naya kaam: 'list mein daalo <kaam>'. AI/developer: pehle docs/AI_START.md.", "",
             f"## Abhi khule (owner ke haath ke) - {len(open_)}"]
    lines += [f"- {t}\n  - Kaise: {h}" for t, h in open_] or ["- (koi nahi)"]
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



def by_number(n):
    """v2.1.6: '🧾 Mere kaam' ki list ka n-va kaam -> (key, text)."""
    order = state.get("pend_order") or []
    if 1 <= n <= len(order):
        return order[n - 1]
    return None
