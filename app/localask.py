"""v3.4.40 (owner 23 Nov 2026: "jis hisab se bola tha wo nahi kar raha" + 30 din ki chat ka audit).

Owner ke ROZ ke sawal (video kitni gayi, schedule, indexing baaki, link se traffic TABLE, Instagram/FB views, /jawab live hua ya
nahi, Gemini kaun sa, bot zinda hai?) ab BINA Gemini ke, seedha asli data se. Kyun:
  1) 21-23 Nov: Gemini ki free seema roz khatam -> in sawalon par "🧠 Dono dimaag abhi busy ... 398 min" aata tha.
  2) Gemini kabhi galat button chalata tha ('Indexing bakance' -> Website doctor; 'libk se traffic' -> indexing report).
  3) Owner ka niyam: GINTI kabhi andaaze se nahi - sirf asli data.
Sirf CHHOTE sawal (max 16 shabd) aur bina 'banao/karo/band/chalu/hatao' wale - lamba hukum pehle jaisa Gemini samjhega.
Pakke command (button / 'tl in (...)' wale) yahan kabhi nahi pakde jaate - unka apna raasta waisa hi.
"""
import ast
import datetime
import pathlib
import re
import time

from . import state, tg
from .config import BRANDS, IST
from .log import log

SITE = "https://sabhisaab.com"
ACTION_RX = re.compile(r"\b(banao|bana do|banado|bnao|karo|kar do|kardo|krdo|kr do|band|chalu|hatao|hata do|delete|mitao|badlo|"
                       r"badal do|set|daalo|dalo|bhej do|bhejo|upload karo|post karo|install|restart|reset|login|token|secret|key|"
                       r"rakhna|rakho|yaad rakh\w*|dhyan rakh\w*|hamesha|aage se|mat karna|mat karo|niyam)\b")   # niyam/yaad = Gemini (rule)
ASK_RX = re.compile(r"\b(kitn\w*|kya|kab|kon|kaun|kaise|batao|btao|bta|dikhao|do|de do|dedo|haal|hal|status|report|list|suchi|"
                    r"latest|abhi|aaj|kal|total|table|tabel|format|pending|baaki|baki|bache|balance|nahi|nhi|ya nhi|ya nahi|hai)\b")

_EXACT = None


def _exact_cmds():
    """bot.py aur baaki module ke pakke hukum ('tl in (...)', 't == "..."') - ye kabhi yahan nahi pakde jaate."""
    global _EXACT
    if _EXACT is not None:
        return _EXACT
    out = set()
    for f in pathlib.Path(__file__).parent.glob("*.py"):
        if f.name == "localask.py":
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for n in ast.walk(tree):
            if not isinstance(n, ast.Compare) or not isinstance(n.left, ast.Name) or n.left.id not in ("tl", "t", "tl0", "_tl0"):
                continue
            for op, cmp_ in zip(n.ops, n.comparators):
                vals = []
                if isinstance(op, (ast.In, ast.NotIn)) and isinstance(cmp_, (ast.Tuple, ast.List, ast.Set)):
                    vals = [e.value for e in cmp_.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                elif isinstance(op, ast.Eq) and isinstance(cmp_, ast.Constant) and isinstance(cmp_.value, str):
                    vals = [cmp_.value]
                out.update(v.strip().lower() for v in vals)
    _EXACT = out
    return out


def norm(tl):
    """Owner ki tez typing ki aam galtiyan (chat se): bakance, linkk, libk, ink, indixing, vedio, shedule, gye/gyi..."""
    t = " " + re.sub(r"[.!?।]+$", "", (tl or "").lower().strip()) + " "
    t = t.replace("’", "'")
    for a, b in ((r"\bbakance\b|\bbalence\b|\bbalanc\b", "balance"), (r"\blinkk+\b|\blibk\b|\blnk\b|\blik\b", "link"),
                 (r"^ ink ", " link "), (r"\bindixing\b|\bindexng\b|\bindeksing\b|\bindexig\b", "indexing"),
                 (r"\bvedio\b|\bvidio\b|\bvdo\b|\bvidoe\b|\bvideos\b", "video"), (r"\breels\b", "reel"),
                 (r"\bshedule\b|\bsedule\b|\bschedual\b|\bshedul\b", "schedule"), (r"\btrafic\b|\btrafik\b|\btraffik\b", "traffic"),
                 (r"\bjabab\b|\bjwab\b|\bjavab\b", "jawab"), (r"\bdayari\b|\bdaiyari\b|\bdairy\b|\bdiyari\b", "diary"),
                 (r"\binsta\b|\binstgram\b|\bintagram\b|\binstagarm\b|\bisntagram\b|\binstagram\w*\b|\binsata\b", "instagram"), (r"\bfb\b|\bfacebok\b|\bfecebook\b|\bfesbuk\b|\bfacbook\b", "facebook"), (r"\byoutub\b|\butube\b|\byou tube\b", "youtube"), (r"\bplateform\w*\b|\bpletform\w*\b|\bplatforms\b", "platform"), (r"\bview\b|\bviwes\b|\bviewz\b|\bvivs\b", "views"), (r"\bpintrest\b|\bpintrst\b", "pinterest"),
                 (r"\bclaudflare\b|\bcloudfare\b", "cloudflare")):
        t = re.sub(a, b, t)
    return re.sub(r"\s+", " ", t).strip()


# ------------------------------------------------------------------ jawab (data se)
def today_videos_text():
    """Aaj kitni video gayi, kab, kahan - jobs + history se (Gemini nahi)."""
    from . import pipeline
    now = datetime.datetime.now(IST)
    today = str(now.date())
    rows = []
    for jid, j in (pipeline.jobs() or {}).items():
        if j.get("status") in ("sample", "rejected"):
            continue
        slot = str(j.get("slot") or "")
        if slot[:10] != today and str(j.get("created", ""))[:10] != today:
            continue
        rows.append((slot[11:16] or "--:--", jid, j))
    rows.sort(key=lambda r: r[0])
    posted = [r for r in rows if r[2].get("status") == "posted"]
    wait = [r for r in rows if r[2].get("status") in ("waiting", "approved", "making", "need_login", "uploading", "scheduled")]
    L = [f"🎬 AAJ ({now.strftime('%d %b')}, abhi {now.strftime('%H:%M')}): {len(posted)} video ja chuki, {len(wait)} line mein "
         f"(upload ginti {pipeline.uploads_today()})"]
    for hm, jid, j in rows:
        st = j.get("status")
        icon = {"posted": "✅", "waiting": "⏳ manzoori", "approved": "🕒 tay", "making": "🛠 ban rahi", "need_login": "🔑 login",
                "failed": "❌"}.get(st, st)
        done = list((j.get("done") or {}).keys())
        pl = [p for p in ("youtube", "facebook", "instagram", "threads", "pinterest", "telegram", "dailymotion") if p in done]
        yt = (j.get("done") or {}).get("youtube") or (f"https://youtu.be/{j['vid']}" if j.get("vid") else "")
        L.append(f"• {hm} {BRANDS.get(j.get('brand'), {}).get('name', j.get('brand'))} {icon}: {str(j.get('title', ''))[:60]}"
                 + (f"\n   {yt}" if yt else "") + (f"\n   Platform: {', '.join(pl)}" if pl and st == "posted" else ""))
    if not rows:
        L.append("• Aaj abhi koi video nahi bani/gayi.")
    nxt = []
    for b, slots in pipeline.schedule().items():
        for hm in [x.strip() for x in str(slots).split(",") if x.strip()]:
            if hm > now.strftime("%H:%M"):
                nxt.append((hm, BRANDS[b]["name"]))
    if nxt:
        L.append("⏰ Aage aaj: " + ", ".join(f"{h} {n}" for h, n in sorted(nxt)))
    if state.get("paused"):
        L.append("⏸ Bot ROKA hua hai - '▶️ Resume' dabayein.")
    return "\n".join(L)


def gemini_text():
    """Kaun sa Gemini model chal raha, kaun seema par (kab tak), doosra dimaag (Cloudflare) - sach."""
    from . import brain
    now = time.time()
    cool = state.get("gemini_cool") or {}
    st = state.get("gemini_status") or {}
    try:
        order = brain.discover() or brain.MODELS
    except Exception:
        order = brain.MODELS
    last = state.get("gemini_last_model") or "-"
    L = [f"🧠 DIMAAG (AI) KA HAAL - aakhri jawab diya: {last}"]
    free = []
    for m in order[:8]:
        c = cool.get(m)
        if isinstance(c, (int, float)) and c > now:
            till = datetime.datetime.fromtimestamp(c, IST).strftime("%H:%M")
            L.append(f"• {m}: ⏳ free seema khatam - {till} IST tak")
        elif st.get(m) and st.get(m) != "ok":
            L.append(f"• {m}: ⚠️ {str(st[m])[:70]}")
        else:
            free.append(m)
            L.append(f"• {m}: ✅ " + ("aaj chala" if st.get(m) == "ok" else "taiyaar"))
    L.append("☁️ Doosra dimaag (Cloudflare AI): " + ("🔑 token mein 'Workers AI' ijaazat nahi" if state.get("cfai_noperm") else "juda"))
    if not free:
        L.append("⚠️ Abhi saare Gemini model seema par. Roz ke sawal (video, schedule, indexing, traffic, jawab) phir bhi chalte hain - "
                 "wo bina AI ke asli data se aate hain.")
    err = state.get("gemini_last_error") or ""
    if err:
        L.append(f"Aakhri galti: {err[:160]}")
    try:                                               # v3.4.43: kahan kharch ho raha
        L.append("")
        L.append(brain.use_text())
        L.append("Bachat chalu: halka kaam lite model par + 6 ghante cache; tareef/A-B-C-D comment bina AI.")
    except Exception as e:
        log(f"gemini use: {e}")
    if not free or err:
        L.append("Pakka ilaaj (aapka faisla, Pending list mein): Google AI Studio → Billing chalu + mahine ki seema.")
    return "\n".join(L)


def quick_status():
    """'Bot bhai kya haal / zinda ho / sab thik' - chhota sach (poora: 🩺 Sab theek?)."""
    from . import pipeline, diary
    from .bot import STARTED, VER
    up = int((time.time() - STARTED) / 60)
    today = str(datetime.datetime.now(IST).date())
    jobs = pipeline.jobs() or {}
    posted = sum(1 for j in jobs.values() if j.get("status") == "posted" and str(j.get("slot", ""))[:10] == today)
    wait = sum(1 for j in jobs.values() if j.get("status") == "waiting")
    errs = [r for r in diary.recent(300, ["galti"]) if r.get("t", "")[:10] == today]
    now = time.time()
    cool = state.get("gemini_cool") or {}
    try:
        from . import brain
        allc = all(isinstance(cool.get(m), (int, float)) and cool[m] > now for m in (brain.discover() or brain.MODELS)[:4])
    except Exception:
        allc = False
    L = [f"🤖 Haan Manoj bhai, chalu hoon ✅ (v{VER}, {up // 60} ghante {up % 60} min se)",
         f"🎬 Aaj {posted} video ja chuki | {wait} aapki manzoori mein",
         f"⚙️ Abhi: {state.get('working_on') or 'koi bhaari kaam nahi'}",
         f"🧠 Dimaag: {'⏳ Gemini free seema par (roz ke sawal phir bhi chalte hain)' if allc else '✅ chal raha'}",
         f"{'⚠️' if errs else '✅'} Aaj galti: {len(errs)}" + (f" (aakhri: {errs[-1]['text'][:80]})" if errs else "")]
    if state.get("paused"):
        L.append("⏸ Roz ka kaam ROKA hai - '▶️ Resume' dabayein.")
    L.append("Poora haal: '🩺 Sab theek?' | aaj ki video: 'aaj kitni video'")
    return "\n".join(L)


def jawab_text(run=None):
    """/jawab par naye jawab live hain ya nahi - code-wise + atka ho to khud dobara."""
    from . import answers
    lst = list(reversed(state.get("answer_key") or []))[:8]
    if not state.get("jawab_site_on"):
        return "🌐 /jawab website par band hai (owner ki pushti baaki: 'jawab website chalu')."
    miss = answers.coverage_check(8)
    L = [f"🌐 JAWAB WEBSITE ({SITE}/jawab) - aakhri {len(lst)} jawab:"]
    for e in lst:
        aid = str(e.get("aid") or e.get("code"))
        mark = "❔ (jaanch nahi ho payi)" if miss is None else ("⏳ abhi live nahi" if aid in (miss or []) else "✅ live")
        if aid in set(state.get("jawab_skip") or []):
            mark = "⚠️ likhai-galti se roka"
        L.append(f"• #{e.get('code')} {e.get('bname') or e.get('brand')} ({str(e.get('date', ''))[5:]}): {mark}\n   {SITE}/jawab#c{aid}")
    due = float(state.get("deploy_due") or 0)
    if state.get("site_undeployed") or due:
        L.append("🚀 Website deploy line mein" + (f" ({max(0, int((due - time.time()) / 60))} min mein)" if due else "")
                 + " - bot khud live karega.")
    err = state.get("jawab_last_error") or ""
    if err:
        L.append(f"⚠️ Aakhri rukawat: {err[:250]}")
    if miss and run and not (state.get("site_undeployed") or due):
        L.append("🔧 Jo live nahi, unhe abhi dobara chadha raha hoon (audit ke saath) - 10-20 min mein live.")
        state.put("answer_dirty", True)
        run(lambda: log(answers.publish_site(force=True)))
    elif miss == []:
        L.append("✅ Sab naye jawab website par live hain.")
    return "\n".join(L)


def bing_why_text():
    """'Bing par indexing kyun nahi' - asli aankde (bot ki state) + saaf wajah + bot kya kar raha. Sirf padhta hai."""
    info = state.get("bing_urlinfo") or {}
    sent = state.get("bing_api_sent") or {}
    chk = [v for v in info.values() if v.get("chk")]
    crawled = sum(1 for v in chk if v.get("crawl"))
    never = len(chk) - crawled
    wk = str(datetime.date.today() - datetime.timedelta(days=7))
    sent7 = sum(1 for d in sent.values() if str(d) >= wk)
    last = state.get("bing_last_resp") or {}
    L = ["🅱️ BING - INDEXING KYUN DHEEMI HAI (sach)",
         f"• Bot ne {len(chk)} page ka Bing haal dekha: Bing aaya {crawled} par, kabhi nahi aaya {never} par.",
         f"• Pichhle 7 din bot ne Bing ko {sent7} URL bheje (aakhri din: {last.get('n', '?')}, Bing ka jawab: {last.get('code', '?')}).",
         "• Wajah 1: Bing naye domain par bahut dheere aata hai - wo pehle site ka bharosa (bahar ke link, purani umar) dekhta hai.",
         "• Wajah 2: Oct mein purane bot ne ek hi URL baar-baar bheje the; uske baad Bing ne site kam dikhayi. Isliye bot ab "
         "sirf wahi bhejta hai jo Bing ne nahi dekha / naya-badla hai, roz quota ka aadha, ek URL 14-30 din mein ek baar.",
         "• Wajah 3: Bing 'crawl' karke bhi turant index nahi karta - Bing ki ginti aur 'search mein dikha' alag-alag hoti hai.",
         "• Technical: crawl error 0, sitemap Bing tak pahuncha - site mein koi rok nahi.",
         "Bot kya kar raha: roz priority se URL (Google-index-nahi > Bing-kabhi-nahi-aaya > naya page), IndexNow sirf badle page, "
         "roz 08:00 Bing report. Zyada bhejna = dobara spam ka khatra, isliye nahi.",
         "Aap kya kar sakte (marzi): Pinterest/Quora/FB group mein page ke link - bahar ke link se Bing jaldi aata hai."]
    return "\n".join(L)


def new_pages_text():
    today = datetime.date.today()
    d = state.get("pq_new_pages") or {}
    rows = sorted(((u, x) for u, x in d.items() if x >= str(today - datetime.timedelta(days=3))), key=lambda r: r[1], reverse=True)
    L = [f"🆕 NAYE PAGE (pichhle 3 din) - {len(rows)}:"]
    L += [f"• {x[5:]} {u if u.startswith('http') else SITE + '/' + u.lstrip('/')}" for u, x in rows[:20]]
    if not rows:
        L.append("• Pichhle 3 din mein koi naya page live nahi hua.")
    try:
        from . import pagequeue
        L.append("\n" + pagequeue.status_text().split("\n")[0])
    except Exception:
        pass
    return "\n".join(L)


# ------------------------------------------------------------------ GA4: link se traffic TABLE
def _ga(dims, metrics, start, end, limit=200):
    import requests
    from . import website as W
    tok = W._gcreds("https://www.googleapis.com/auth/analytics.readonly")
    j = requests.post(f"https://analyticsdata.googleapis.com/v1beta/properties/{W.GA4_PROPERTY}:runReport",
                      headers={"Authorization": f"Bearer {tok}"}, timeout=60,
                      json={"dateRanges": [{"startDate": start, "endDate": end}], "dimensions": [{"name": d} for d in dims],
                            "metrics": [{"name": m} for m in metrics], "limit": limit}).json()
    if "error" in j:
        raise RuntimeError(j["error"].get("message", "")[:200])
    return [([d["value"] for d in r["dimensionValues"]], [float(m["value"] or 0) for m in r["metricValues"]])
            for r in j.get("rows") or []]


BCOL = [("pahadi", "Pah"), ("money", "Mon"), ("deals", "Deal"), ("sunonatak", "Suno")]


def _bcol(camp):
    c = (camp or "").lower()
    for k, s in BCOL:
        if k in c:
            return s
    return "Baaki"


def link_table(focus=None):
    """Platform (rows) x Aaj/Kal/7 din + 7 din brand-wise. GA4 sessionSource + utm_campaign. Returns HTML (<pre>)."""
    import html as _h
    from .scoreboard import group_source
    from . import website as W
    if not W.SA.exists():
        return "🔑 Website ki Google service account file bot ke paas nahi - traffic nahi padh sakta (🧾 Mere kaam)."
    ranges = {"Aaj": ("today", "today"), "Kal": ("yesterday", "yesterday"), "7din": ("6daysAgo", "today")}
    plat, brand = {}, {}
    for col, (s_, e_) in ranges.items():
        for (src, camp), (u,) in _ga(["sessionSource", "sessionCampaignName"], ["activeUsers"], s_, e_):
            g = group_source(src)
            plat.setdefault(g, {}).setdefault(col, 0)
            plat[g][col] += int(u)
            if col == "7din":
                brand.setdefault(g, {}).setdefault(_bcol(camp), 0)
                brand[g][_bcol(camp)] += int(u)
    tot = {}
    for col, (s_, e_) in ranges.items():
        try:
            t_ = W._ga_total(s_, e_)
            tot[col] = t_[0] if t_ else 0
        except Exception:
            tot[col] = sum(v.get(col, 0) for v in plat.values())
    order = sorted(plat, key=lambda g: -plat[g].get("7din", 0))
    w = max([10] + [len(g) for g in order])
    rows = [f"{'Kahan se':<{w}} {'Aaj':>4} {'Kal':>4} {'7din':>5}", "-" * (w + 16)]
    for g in order:
        p = plat[g]
        rows.append(f"{g:<{w}} {p.get('Aaj', 0):>4} {p.get('Kal', 0):>4} {p.get('7din', 0):>5}")
    rows += ["-" * (w + 16), f"{'KUL (asli)':<{w}} {tot.get('Aaj', 0):>4} {tot.get('Kal', 0):>4} {tot.get('7din', 0):>5}"]
    cols = [s for _, s in BCOL] + ["Baaki"]
    rows2 = [f"{'7 din':<{w}} " + " ".join(f"{c:>4}" for c in cols), "-" * (w + 26)]
    for g in order:
        b = brand.get(g, {})
        if sum(b.values()):
            rows2.append(f"{g:<{w}} " + " ".join(f"{b.get(c, 0):>4}" for c in cols))
    head = "🌐 WEBSITE PAR LOG - KAHAN SE (GA4 asli, log = activeUsers)"
    if focus:
        f = plat.get(focus, {})
        head += f"\n👉 {focus}: aaj {f.get('Aaj', 0)} | kal {f.get('Kal', 0)} | 7 din {f.get('7din', 0)}"
    note = ("Brand = hamare link ka utm (Pah=Pahadi, Mon=Money, Deal=Labh Lo Deals, Suno=Suno Natak; Baaki = bina brand wala "
            "link - Uttarakhand/tool page ka link, Google search, seedha). Ek aadmi do raaste se aaye to dono mein ginta hai, "
            "isliye KUL (asli) alag hai. GA4 1-2 ghante der se ginta hai - 'Kal' pakka.")
    e_ = lambda x: _h.escape(x, quote=False)
    return (f"<b>{e_(head)}</b>\n<pre>{e_(chr(10).join(rows))}</pre>\n<b>Brand-wise (7 din)</b>\n"
            f"<pre>{e_(chr(10).join(rows2))}</pre>\n{e_(note)}")


def traffic_reply(run, focus=None, chart=True):
    """'link se traffic' / 'traffic' / button: pehle TABLE (owner 17 Nov: traffic ke saath table hamesha), phir 30 din ka graph."""
    from . import idxlink
    tg.say("🔎 Google Analytics se asli ginti (aaj, kal, 7 din) la raha hoon...")

    def _go():
        try:
            idxlink.send_html(link_table(focus))
        except Exception as e:
            tg.say(f"🌐 Traffic table nahi bani: {str(e)[:200]}")
        if chart:
            try:
                from . import scoreboard
                scoreboard.send_traffic(30)
            except Exception as e:
                log(f"traffic chart: {e}")
    return run(_go) or True


COMMENT_NOTE = ("💬 COMMENT BOT KA TAREEKA (v3.4.41):\n"
                "• Quiz reel par 'C', 'सी', 'D🔥', 'Thand' = us sawal ka JAWAB - bot ab video ka sawal pehchaanta hai.\n"
                "• Jawab: 'C (छोलिया) chuna 👍 Sahi jawab aur tareeka sabhisaab.com/jawab par - code #6024' (7 alag roop).\n"
                "• Sahi/galat comment mein nahi batata (warna website par koi nahi aata); 'comment/like/share/tag karo' kabhi nahi "
                "(Meta ise engagement-bait maan kar reach ghatata hai).\n"
                "• Spam na lage: har video max 15 jawab, har account roz max 40, ek insaan ko ek video par ek hi; 7-45 min ruk kar.\n"
                "• Sawal/tareef/lamba comment: AI (video ka sawal jaankar) - 'samajh nahi aaya' kabhi nahi. Gaali/link-spam: chhupata hai.")


GA_ZERO_NOTE = ("⏱ GA4 mein 'engagement time 0-1 sec' kyun :\n"
                "• Tracking theek hai: Google search / video se aaye logon ka samay dikhta hai - yani GA chal raha hai.\n"
                "• Zyadatar log Facebook/Instagram app ke andar ke browser se aate hain, seedha jawab wale dabbe (#code) par utarte hain, "
                "jawab dekh kar app band - app ka browser band hote hi GA4 ko samay nahi pahunchta, isliye 0 sec.\n"
                "• Ilaaj (v3.4.41, /jawab par): 'jawab dekha' tap par aur 15/45 sec par chhota naap-event - asli samay ab gina jayega "
                "(page_view dobara nahi, koi nakli ginti nahi). 'Agla sawal' + 'isi tarah ke sawal' pehle se lage hain.\n"
                "• Asli ruk-na badhane ke liye: jawab ke baad agla sawal turant dikhe - ye chal raha hai; naya data 2-3 din mein dikhega.")


def dwell_text():
    """Log kitni der ruke - 7 din, raaste ke hisaab se (GA4 averageSessionDuration, engagementRate)."""
    from .scoreboard import group_source
    from . import website as W
    if not W.SA.exists():
        return "🔑 Website ki Google service account file bot ke paas nahi."
    tot = _ga([], ["averageSessionDuration", "engagementRate", "sessions", "screenPageViewsPerSession"], "6daysAgo", "today")
    by = {}
    for (src,), (dur, er, ses) in _ga(["sessionSource"], ["averageSessionDuration", "engagementRate", "sessions"], "6daysAgo", "today"):
        g = group_source(src)
        a = by.setdefault(g, [0.0, 0.0, 0.0])
        a[0] += dur * ses
        a[1] += er * ses
        a[2] += ses
    L = ["⏱ WEBSITE PAR KITNI DER RUKE (pichhle 7 din, GA4 asli)"]
    if tot:
        dur, er, ses, pps = tot[0][1]
        L.append(f"• Ausat: {int(dur // 60)} min {int(dur % 60)} sec | ruke (engaged): {er * 100:.0f}% | {int(ses)} session | "
                 f"ek visit mein {pps:.1f} page")
    for g, (d_, e_, s_) in sorted(by.items(), key=lambda x: -x[1][2])[:8]:
        if s_:
            L.append(f"• {g}: {int(d_ / s_ // 60)}m {int(d_ / s_ % 60)}s | ruke {e_ / s_ * 100:.0f}% | {int(s_)} session")
    L.append("Lambi der = 'Agla sawal' + 'isi tarah ke sawal' + andar ke link (sab /jawab par lage hain).")
    return "\n".join(L)


PLAT_WORDS = {"Instagram": ("instagram", " ig "), "Facebook": ("facebook",), "Threads": ("threads",), "YouTube": ("youtube", " yt "),
              "LinkedIn": ("linkedin", "linkdin"), "Pinterest": ("pinterest",), "Telegram": ("telegram",), "WhatsApp": ("whatsapp",),
              "Bing": ("bing",), "Google": ("google",), "FB Group": ("group",), "Quora": ("quora",)}


def _plat(t):
    t = f" {t} "
    for k, ws in PLAT_WORDS.items():
        if any(w in t for w in ws):
            return k
    return None


# ------------------------------------------------------------------ router
def on_text(tl, run=None, raw=""):
    """True = jawab de diya. None = ye sawal yahan ka nahi (purana raasta)."""
    run = run or (lambda f: f())
    t0 = (tl or "").strip().lower()
    if not t0 or t0.startswith("/") and t0 not in ("/jawab", "/health"):
        return None
    if t0 in _exact_cmds() and t0 not in ("/jawab", "/health"):
        return None
    t = norm(t0)
    if t in _exact_cmds():
        if t != t0:                                   # spelling theek karke pakka hukum mila ('indexing linkk' -> 'indexing link')
            from .bot import on_text as B
            return bool(B("__fz__" + t) or True)
        return None
    m_ = re.match(r"^(ho gya|ho gyi|hogaya|hogya|o gaya|ho gye|ho gaye)\s+(.+)$", t)
    if m_:                                            # 'ho gya pin secret' -> 'ho gaya pin secret' (kaam-suchi ka pakka hukum)
        from .bot import on_text as B
        return bool(B("__fz__ho gaya " + m_.group(2)) or True)
    words = t.split()
    if len(words) > 16:
        return None
    act = bool(ACTION_RX.search(re.sub(r"\b(table|tabel) (banao|bana do|banado|bnao)\b", "table", t)))
    vid = re.search(r"\b(video|reel|short)\b", t)
    if re.search(r"\bgra+ff?\b|\bgraph\b|\bgrafh\b|\bgrph\b|\bchart\b|\bchaart\b", t):
        return None                                   # 'growth graff' / 'graph' = graph wala purana hukum (intents)
    if (re.search(r"\bho ?gaya\b|\bho ?gya\b|\bkar (di|diya|dia)\b|\bkr (di|diya)\b|\bdone\b", t)
            and not re.search(r"\b(kya|kyu|kyon|kitn\w*|kab|kaun|kon)\b", t)):
        return None                                   # 'indexing ho gaya' / 'kar diya' = pakka-karne wale hukum, unka apna raasta
    # 1) dosti / chhoti baat (Gemini ki zaroorat nahi)
    if re.fullmatch(r"(bot bhai |bhai )?(kaise ho( aap)?|love you.*|miss you.*|happy diwali.*|good (morning|night).*|gm|gn|"
                    r"thank(s| you)?.*|dhanyavad.*|shukriya.*)( bot bhai)?", t):
        return bool(tg.say("🙏 Shukriya Manoj bhai! Main chalu hoon aur kaam par hoon. Kuch chahiye to likhiye - "
                           "'aaj kitni video', 'link se traffic', 'indexing baaki', '/jawab haal'."))
    # 2) Gemini / dimaag
    if re.search(r"\bgemini\b|\bdimaag\b|\bai model\b", t) and not act:
        return bool(tg.say(gemini_text()))
    # 3) /jawab website par hai ya nahi (+ 'theek karo' = jo atka wo dobara chadhao - jawab_text khud karta hai)
    if ((t in ("/jawab", "jawab", "jawab haal", "jawab page", "answer sheet") or t.rstrip("/").endswith("sabhisaab.com/jawab")
            or (re.search(r"\b(jawab|answer)\b", t) and re.search(r"website|site|page|publish|chadh|lag|atk|live|sheet|dikh", t)))
            and (not act or re.search(r"\b(thik|theek|fix|sudhaar|sudhar)\b", t))
            and not re.search(r"\b(band|chalu|digest|poll)\b", t)):
        tg.say("🔎 /jawab live page jaanch raha hoon...")
        return bool(run(lambda: tg.say(jawab_text(run))))
    if act:
        return None
    if re.search(r"\b(url|page|link|pages)\b", t) and re.search(r"\b(bheje|bheja|bhej diye|bhej diya|submit)\b", t) \
            and not re.search(r"\bbhej do\b", t):
        from . import website
        tg.say("📮 Aaj/kal search engine ko bheje page (Bing API + IndexNow) - taaza haal la raha hoon...")
        return bool(run(lambda: tg.say(website.bing_report())))
    # 4a) ek khaas page index kyun nahi ('almora wala page kyu index nhi') -> us page ka doctor
    if re.search(r"\bindex\w*", t) and re.search(r"\bkyu|\bkyon|\bkyun|\bwajah|\bkaran\b", t) and "bing" not in t:
        try:
            from . import siteknow
            pend = siteknow.not_indexed() or []
            ws = [w for w in t.split() if len(w) > 3 and w not in ("index", "indexing", "kyun", "kyon", "page", "wala", "wale", "hai", "nhi", "nahi", "raha")]
            hit = [k for k in pend if any(w in k for w in ws)][:3]
            if hit:
                for k in hit:
                    run(lambda k=k: tg.say(siteknow.doctor(k)))
                return True
        except Exception as e:
            log(f"localask page doctor: {e}")
    # 4) indexing (Google) - baaki / balance / suchi -> ek hi sandesh
    if (re.search(r"\bindex\w*|\bgsc\b|\bpending url", t) or (re.search(r"\bgoogle\b", t) and re.search(r"pending|baaki|baki|bache", t)
                                                                and re.search(r"\burl|\bpage|\blink", t))) and "bing" not in t:
        from . import idxlink
        if re.search(r"\blink\b", t) and not re.search(r"kitn|baaki|baki|balance|pending|bache|nahi|nhi", t):
            return bool(idxlink.on_text("indexing link", run))
        if re.search(r"\bnaye?\b|\bnew\b", t) and re.search(r"\bpage\b", t):
            return bool(tg.say(new_pages_text()))
        return bool(run(lambda: idxlink.send_html(idxlink.not_indexed_text())))
    if re.search(r"\b(aaj|aj|new|naye?)\b.*\bpage\b", t) and re.search(r"batao|dikhao|kaun|kon|kitne|list|live", t):
        return bool(tg.say(new_pages_text()))
    # 5) traffic (website par log) - TABLE
    if (re.search(r"\btraffic\b|\blog (aaye|aye|aa rhe|aa rahe)\b|kitne log|\bvisitor|\bviewer aaye|\blink se\b|\bgrowth\b|"
                  r"\baudiance\b|\baudience\b", t)
            and not re.search(r"\b(video|reel) (ke )?views?\b|\bsubscriber|\bfollower", t)):
        if re.search(r"\bder\b|\bruk|\btime spend|\bkitni der\b|dwell", t):
            return bool(run(lambda: tg.say(dwell_text())))
        foc = _plat(t)
        return bool(traffic_reply(run, foc, chart=not re.search(r"\btable\b|\btabel\b|\bformat\b", t)))
    if re.search(r"\bder\b.*\bruk|\bruk\w* .*\bder\b", t) or (re.search(r"analytics|\bga4?\b|engagement", t)
                                                                  and re.search(r"\b0\b|zero|\btime\b|samay|kam|kyu", t)):
        tg.say(GA_ZERO_NOTE)
        return bool(run(lambda: tg.say(dwell_text())))
    if ((re.search(r"\b(table|tabel|format)\b", t) and re.search(r"\blink\b|\blog\b|audience|audiance|traffic|website", t)
         and not re.search(r"\breport table\b|\bscoreboard\b|\bdin\b", t))
            or (re.search(r"\b(koi|log|kitne|kon se|kaun se)\b", t) and re.search(r"\b(aa rhe|aa rahe|aaye|aaya|aye|aate)\b", t)
                and re.search(r"website|site|\blink\b|video se|reel se|channel se|facebook se|instagram se|threads se|"
                              r"pinterest se|linkedin se|google se|bing se", t))
            or (re.search(r"\bviews?\b", t) and re.search(r"\bwebsite\b|\bsite\b", t))):
        return bool(traffic_reply(run, _plat(t), chart=not re.search(r"\btable\b|\btabel\b|\bformat\b", t)))
    if re.search(r"\bbing\b", t) and re.search(r"\bkyu|\bkyon|\bkyun|\bwhy\b|system|nahi ho|nhi ho|dheem|kam ", t):
        from . import website
        tg.say(bing_why_text())
        return bool(run(lambda: tg.say(website.bing_report())))
    # 5b) Bing (index / url bheje / haal) - IndexNow/Bing hi bot khud bhejta hai
    if ((re.search(r"\bbing\b", t) and re.search(r"index|url|link|bheje|bheja|kitn|haal|hal\b|report|record|kaun|kon", t))
            or (re.search(r"\b(url|page|link)\b", t) and re.search(r"\b(bheje|bheja|bhej diye|bhej diya)\b", t))):
        from . import website
        tg.say("🅱️ Bing ka taaza haal la raha hoon...")
        return bool(run(lambda: tg.say(website.bing_report())))
    # 6) views
    if re.search(r"\bviews?\b|\bvyu\b|\bfollowers?\b|\bsubscribers?\b", t):
        if vid and re.search(r"gyi|gayi|gye|gaye|dali|upload|kitn", t):      # 'kitni video gayi aur views kitne' = dono
            tg.say(today_videos_text())
        from .bot import on_text as B
        if re.search(r"follower|subscriber", t):
            return bool(B("📈 Poora haal") or True)
        pf = _plat(t)
        if not pf or re.search(r"\b(total|kul|sab|sabhi|saare|sare|all)\b", t):      # v3.6.1: 'total views sab platform' = YT+FB+IG ek table
            from . import growth
            tg.say("📊 YouTube + Facebook + Instagram ke aakhri 12 video ke views la raha hoon...")
            from . import idxlink as _IXL
            return bool(run(lambda: _IXL.send_html(growth.all_views_text(12))))
        if pf in ("Facebook", "Instagram", "YouTube"):
            from . import growth
            tg.say(f"📈 {pf} ke aakhri video ke views la raha hoon...")
            return bool(run(lambda: tg.say(growth.video_detail(8, None, pf.lower()))))
        if pf == "Pinterest":
            return bool(B("pinterest haal") or True)
        if not re.search(r"website|site", t):
            return bool(B("👀 Views") or True)
    # 7) aaj ki video / schedule
    vid = re.search(r"\b(video|reel|short)\b", t)
    if (re.search(r"\bschedule\b|time table|kab kab|jayegi|jaegi|jaengi|jayengi|kab (aayenge|aayegi|jayenge|banenge)", t)
            and (vid or "schedule" in t or re.search(r"swal|sawal|reel", t))):
        from .bot import schedule_text
        return bool(tg.say(schedule_text()))
    if vid and re.search(r"gyi|gayi|gai\b|gye|gaye|chali|chale|dali|daali|upload|post hu|kitn|ban gyi|ban gayi|bani", t) \
            and not re.search(r"\bbana|\bbnao|banao", t):
        return bool(tg.say(today_videos_text()))
    # 8) comment
    if re.search(r"\bcomment", t) and re.search(r"jawab|reply|koi|haal|kar rhe|kar rahe|kar raha|kar rha|diya|system|kaise|ulta", t):
        from .bot import on_text as B
        tg.say(COMMENT_NOTE)
        return bool(B("💬 Comment haal") or True)
    # 9) Telegram ka raasta
    if (re.search(r"\btelegram\b", t) and re.search(r"kya ho|route|roote|raasta|rasta|badla|change|dikkat|band", t)) or \
            ("cloudflare" in t and "telegram" in t):
        from . import relay
        return bool(tg.say(relay.status_text()))
    # 10) diary
    if re.search(r"\bdiary\b", t):
        from . import growth
        return bool(tg.say(growth.day_report()))
    # 11) VM
    if re.search(r"\bvm\b|\bdisk\b|\bram\b|\bcpu\b|nifty chart|\bcache\b|\bcetch\b", t) and not re.search(r"audit", t):
        from .bot import vm_text
        return bool(tg.say(vm_text()))
    # 11b) manzoori wali video / galti wale platform / backup password / audit
    if re.search(r"\bwaiting\b|manzoori (mein|me|wali)|approval (mein|me)", t):
        from .bot import on_text as B
        return bool(B("⏳ Pending") or True)
    if re.search(r"channel status|sab platform|\berror\b|\bgalti\b", t) and re.search(r"kya|hai|batao|active|kahi|kahin", t):
        from .bot import health_text
        tg.say("🩺 Har platform jaanch raha hoon...")
        return bool(run(lambda: tg.say(health_text())))
    if re.search(r"\bbackup password\b", t):
        from .bot import on_text as B
        return bool(B("backup password") or True)
    if re.fullmatch(r"(vm )?(audit (deep|chalao|karo|full)|deep audit|full audit|poora audit karo)", t):
        from .bot import on_text as B
        return bool(B("audit") or True)
    # 12) bot zinda? / sab thik? / kya chal raha
    if (t in ("/health", "health", "sab theek hai", "sab thik hai", "bot", "bot bhai", "batao bot bhai")
            or (re.match(r"^(bot bhai|bot|bhai)\b", t) and re.search(
                r"haal|hal\b|thik|theek|dikkat|pressani|pareshani|jinda|zinda|mast|mar gye|kya ho gya|kya chal|chl rha|kaise|task|"
                r"kar rhe|kar rahe|khabar", t))
            or re.search(r"kya (task|kaam) kar (rhe|rahe)", t)
            or re.search(r"(koi )?dikkat (pressani|pareshani)|sab thik (chal|hai)|channel status", t)):
        return bool(tg.say(quick_status()))
    return None


def down_fallback(text, run=None):
    """Gemini + Cloudflare dono band: pehle data wale raaste se koshish, warna chhota sach (bina lambi menu suchi)."""
    try:
        if on_text(text, run, text):
            return True
    except Exception as e:
        log(f"localask fallback: {e}")
    t = norm(text)
    try:                                              # AI band ho tab bhi seedhe kaam (keyword se) - brand/topic baad mein
        from .bot import on_text as B
        if re.search(r"\b(video|reel|short)\b", t) and re.search(r"banao|bana do|banado|bnao|dalo|daalo", t):
            tg.say("🎬 AI abhi seema par hai, isliye topic/style nahi samajh sakta - brand chuniye, bot roz wale saanche se video "
                   "banayega (manzoori ke baad hi jayegi). Lambi/3D/khaas topic: AI wapas aane par likhein.")
            return bool(B("🎬 Abhi video") or True)
        if re.search(r"\bfile\b", t) and re.search(r"website|sab ?hisab|sabhisab|site", t):
            return bool(B("website file site") or True)
    except Exception as e:
        log(f"localask down kw: {e}")
    import time as _t
    cool = [v for v in (state.get("gemini_cool") or {}).values() if isinstance(v, (int, float)) and v > _t.time()]
    till = datetime.datetime.fromtimestamp(min(cool), IST).strftime("%H:%M") if cool else ""
    return bool(tg.say("🧠 Ye baat samajhne ke liye AI (Gemini) chahiye - abhi uski free seema khatam" + (f" ({till} IST tak)" if till else "")
                       + ".\nYe sab abhi bhi turant chalte hain: 'aaj kitni video' | 'schedule' | 'indexing baaki' | 'link se traffic' | "
                         "'instagram views' | 'jawab haal' | 'gemini haal' | '🩺 Sab theek?' | '📖 Poora menu'"))
