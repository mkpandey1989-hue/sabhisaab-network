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


AUTO = {"meta_secret": _meta_secret_ok, "tg_pin": _tg_pinned, "gsc_all": _gsc_all_indexed, "psi": _psi_key, "cf": _cf_ok, "dm_over": _dm_over}


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


def mark_done(word):
    """'ho gaya <shabd>' - list se hatao + itihaas mein rakho (PENDING.md mein 'ho chuke' dikhte hain)."""
    import datetime
    w = word.strip().lower()
    before = state.get("todo") or []
    gone = [x for x in before if w and w in x["x"].lower()]
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
    pend = [(t, h) for k, d, t, h in items if not d]
    if auto:
        return None
    done_n = sum(1 for _, d, _, _ in items if d)
    lines = [f"🧾 Aapke haath ke kaam: {done_n}/{len(items)} ho gaye"]
    if pend:
        lines.append("\n⬜ Baaki (bot roz khud jaanchta hai, hote hi LIVE):")
        lines += [f"• {t}\n   👉 {h}" for t, h in pend]
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


def seed_todo():
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
