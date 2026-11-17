"""v3.4.0 (16 Nov 2026): LinkedIn Company Page 'Sab Hisaab' par roz 1 post - Make.com ke raaste.

Kyun Make: LinkedIn ki apni Page-API (Community Management API) sirf registered company ko milti hai (review). Make.com
LinkedIn ka approved partner hai, isliye owner ne 16 Nov ko Make par scenario banaya:
    Webhooks (Custom webhook 'sabhisaab-linkedin')  ->  LinkedIn 'Create a Company Text Post' (Company: Sab Hisaab, Content = text)
Bot sirf webhook par {"text": "..."} bhejta hai; Make use Page par daal deta hai. Post par sirf 'Sab Hisaab' ka naam (owner ka nahi).

Niyam (owner, 16 Nov): roz 1 post, subah 09:15 IST; us din ka ek quiz sawal + sahi jawab ka link (/jawab#cCODE, UTM linkedin)
+ ek related free tool (zyada der ruke, zyada page). Samay/band/chalu badlna = dohri pushti. Webhook URL / API key = secret:
chat se turant mitao, secrets/linkedin.json (0600), GitHub/log/alert mein kabhi nahi.
Image post abhi nahi: sabhisaab.com ki image Make tak nahi pahunchi (Cloudflare) - text post Page par dikhti hai (16 Nov test).
"""
import datetime
import json
import re
import time

from . import state, tg
from .config import IST, SECRETS, SITE
from .log import log

STORE = SECRETS / "linkedin.json"
HOOK_RX = re.compile(r"https://hook\.(?:eu|us)\d\.make\.com/[A-Za-z0-9]{20,64}")
DEFAULT_TIME = "09:15"
CONN_DAYS = 60            # LinkedIn ka access token ~60 din; Make khud naya karta hai par 50/57 din par yaad dilao
MAX_TRY = 3
TAGS = {"sunonatak": "#Maths #Puzzle #DimaghiSawal", "money": "#Finance #PaisaGyaan #Maths",
        "deals": "#Shopping #Discount #Maths", "pahadi": "#Uttarakhand #PahadiGK #GK"}


# ---------------------------------------------------------------- secret
def _cfg():
    try:
        return json.loads(STORE.read_text())
    except Exception:
        return {}


def _save(c):
    STORE.parent.mkdir(mode=0o700, exist_ok=True)
    STORE.write_text(json.dumps(c))
    STORE.chmod(0o600)


def ready():
    return bool(_cfg().get("hook"))


def on():
    return ready() and state.get("li_on") is not False


def intake(text):
    """secret_intake se: Make webhook URL ya 'linkedin key <k>' -> (jawab) ya None. Message bot.py mitata hai."""
    m = HOOK_RX.search(text or "")
    if m:
        c = _cfg()
        new = c.get("hook") != m.group()
        c["hook"] = m.group()
        c.setdefault("conn_date", str(datetime.date.today()))
        _save(c)
        if new and datetime.datetime.now(IST).strftime("%H:%M") >= when():
            state.put("li_done_day", str(datetime.date.today()))   # v3.4.2: jodte hi raat ko post nahi - kal se samay par
        state.put("li_fail", 0)
        return ("🔐 LinkedIn (Make) webhook mila - chat se mitaya, VM par surakshit.\n"
                + ("✅ Roz " + when() + " par Sab Hisaab Page par 1 post jayegi (pehli: agla " + when() + ") (us din ka sawal + jawab link + 1 free tool).\n"
                   if new else "Wahi purana URL tha - kuch nahi badla.\n")
                + "Pehle dekhna ho: 'linkedin namoona' | Abhi bhejna: 'linkedin abhi' | Haal: 'linkedin haal'")
    k = re.match(r"(?i)^\s*linkedin\s+key\s+(\S{8,200})\s*$", text or "")
    if k:
        c = _cfg()
        c["key"] = k.group(1)
        _save(c)
        return ("🔐 LinkedIn webhook ki API key mili (chat se mitayi). Bot ab har post ke saath 'x-make-apikey' bhejega.\n"
                "Dhyan: Make mein bhi wahi key lagi ho (Webhooks → sabhisaab-linkedin → Edit → API Key authentication) - "
                "warna post rukegi aur bot 🔴 batayega.")
    return None


# ---------------------------------------------------------------- content
def when():
    return state.get("li_time") or DEFAULT_TIME


def _clean(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def pick(today=None):
    """Aaj ka sawal: 3 din ke andar, LinkedIn par kabhi na gaya, kal wala brand na ho to behtar, vikalp wala pehle."""
    today = today or datetime.date.today()
    done = set(state.get("li_codes") or [])
    last_b = state.get("li_last_brand")
    lst = [e for e in reversed(state.get("answer_key") or []) if e.get("q") and e.get("code")]
    fresh = []
    for e in lst:
        try:
            age = (today - datetime.date.fromisoformat(str(e.get("date"))[:10])).days
        except Exception:
            continue
        q = re.sub(r"\s*#\S+", "", _clean(e.get("q"))).strip()
        if len(q) < 14 or q.endswith(":"):          # v3.4.3: sirf 'गोला पहेली:' jaisa adhura sawal nahi
            continue
        if 0 <= age <= 3 and str(e.get("aid") or e.get("code")) not in done:
            fresh.append(e)
    if not fresh:
        return None
    fresh.sort(key=lambda e: (e.get("brand") == last_b, not e.get("opts")))
    return fresh[0]


def _tool(e):
    try:
        from .answers import related_tools
        t = related_tools(e)
    except Exception:
        t = []
    if not t:
        return None
    i = len(state.get("li_codes") or []) % len(t)       # roz alag tool (ek hi tool baar-baar nahi)
    sl, nm = t[i]
    return nm, f"{SITE}/{sl}?utm_source=linkedin&utm_medium=social&utm_campaign=li_tool"


def _ans_link(e):
    try:
        from .answers import answer_url
        return answer_url(e.get("aid") or e.get("code"), "linkedin", e.get("brand"))
    except Exception:
        return f"{SITE}/jawab?utm_source=linkedin&utm_medium=social#c{e.get('code')}"


def build(e):
    q = _clean(e.get("q"))
    q = re.sub(r"\s*#\S+", "", q).strip()                  # '#Shorts' / '#4545' jaise tag post mein nahi
    lines = [f"🧠 आज का सवाल | {e.get('bname') or 'Sab Hisaab'}", "", q]
    ops = [o for o in (e.get("opts") or []) if _clean(o)]
    if len(ops) >= 2:
        lines += [""] + [f"{'ABCD'[i]}) {_clean(o)}" for i, o in enumerate(ops[:4])]
    lines += ["", "👇 अपना जवाब कमेंट में लिखिए - फिर मिलाइए:", f"✅ सही जवाब + पूरा तरीका: {_ans_link(e)}"]
    t = _tool(e)
    if t:
        lines += [f"🧮 मुफ़्त टूल - {t[0]}: {t[1]}"]
    lines += ["", "रोज़ एक नया सवाल - Page को Follow करें 🙏",
              "#SabHisaab #Hindi #Quiz " + TAGS.get(e.get("brand") or "", "#GK")]
    return "\n".join(lines)[:2900]


def fallback_text():
    """Taaza sawal na ho to (bahut kam): ek free tool ka parichay - har din alag (list poori hone tak dohraav nahi).
    -> (text, slug) ya (None, None). State yahan nahi badalta (namoona bhi isi se) - post safal hone par hi."""
    try:
        from .answers import TOOL_NAMES
    except Exception:
        return None, None
    used = state.get("li_tools") or []
    left = [k for k in TOOL_NAMES if k not in used] or list(TOOL_NAMES)
    sl = left[0]
    return (f"🧮 आज का मुफ़्त टूल: {TOOL_NAMES[sl]}\n\nहिंदी में, बिना लॉगिन, मोबाइल पर तुरंत हिसाब।\n"
            f"👉 {SITE}/{sl}?utm_source=linkedin&utm_medium=social&utm_campaign=li_tool\n\n"
            f"रोज़ के सवाल-जवाब: {SITE}/jawab?utm_source=linkedin&utm_medium=social\n\n#SabHisaab #Hindi #Calculator"), sl


def compose():
    """-> (text, entry ya None, tool-slug ya None)"""
    e = pick()
    if e:
        return build(e), e, None
    txt, sl = fallback_text()
    return txt, None, sl


# ---------------------------------------------------------------- bhejna
RESERVED = set("\\|{}@[]()<>#*_~")


def ltf(text):
    """v3.4.2: LinkedIn 'Little Text Format' - in nishaanon \\ | { } @ [ ] ( ) < > # * _ ~ ko '\\' se bachana zaroori,
    warna LinkedIn post kaat deta/rok deta hai (16 Nov: 'A)' aur utm_source ke '_' wali post nahi dikhi). '#Tag' hashtag ka
    sahi roop {hashtag|\\#|Tag}. Link ke andar ke '_' '#' bhi bachaye jaate hain (LinkedIn dikhate waqt '\\' hata deta hai)."""
    out, i, n = [], 0, len(text)
    while i < n:
        m = re.match(r"#([A-Za-z\u0900-\u097F][\w\u0900-\u097F]{1,40})", text[i:])
        if m and (i == 0 or text[i - 1] in " \n"):
            out.append("{hashtag|\\#|" + m.group(1) + "}")
            i += len(m.group(0))
            continue
        ch = text[i]
        out.append("\\" + ch if ch in RESERVED else ch)
        i += 1
    return "".join(out)


def send(text):
    """-> (ok, sandesh, post_id). Webhook URL kabhi sandesh/log mein nahi.
    v3.4.2: text 'form' ki tarah (Make ne dhancha ?text= se seekha tha - JSON wala 16 Nov ko khaali pahuncha: 5 B,
    'Validation failed'). Pakki khabar SIRF jab Make ka 'Webhook response' LinkedIn ka post-ID (urn:li:...) lautaye.
    Sirf 'Accepted' = Make ne liya par post bani ya nahi pata nahi (scenario band ho to Make queue mein rakh kar bhi
    'Accepted' bolta hai) - ise safalta NAHI maante."""
    import requests
    c = _cfg()
    if not c.get("hook"):
        return False, "webhook URL nahi (bot chat mein Make ka hook.eu1.make.com/... URL paste karein)", None
    h = {}
    if c.get("key"):
        h["x-make-apikey"] = c["key"]
    try:
        r = requests.post(c["hook"], data={"text": ltf(text)}, headers=h, timeout=60)
    except Exception as ex:
        return False, f"network: {type(ex).__name__}", None
    body = (r.text or "").strip()[:300]
    urn = re.search(r"urn:li:(?:share|ugcPost|activity):\d+", body)
    if r.status_code == 200 and urn:
        return True, "LinkedIn ne post bana di", urn.group()
    if r.status_code == 200 and body.lower() == "accepted":
        return None, ("Make ne liya par LinkedIn ki pakki khabar nahi - Make scenario mein aakhir mein 'Webhook response' "
                      "(Body = Post ID) nahi hai, ya scenario BAND hai aur message queue mein ruka hai"), None
    if r.status_code in (404, 410) or "no scenario listening" in body.lower():
        return False, "Make scenario BAND hai (Make → Scenarios → 'Integration Webhooks, LinkedIn' → toggle ON)", None
    if r.status_code in (401, 403):
        return False, "API key galat/nahi (Make webhook mein key lagi hai to bot ko 'linkedin key <key>' bhejein)", None
    if r.status_code == 429:
        return False, "Make ki seema (bahut zyada request) - baad mein dobara", None
    clean = re.sub(r"https?://\S+", "<link>", body)[:150]
    return False, f"HTTP {r.status_code}: {clean}", None


def post_today():
    """Roz ka kaam (ya 'linkedin abhi'). -> sandesh"""
    if not ready():
        return "LinkedIn juda nahi (webhook URL nahi)."
    text, e, sl = compose()
    if not text:
        return "Aaj bhejne layak kuch nahi mila."
    ok, why, pid = send(text)
    day = str(datetime.date.today())
    if ok is None:                                    # pakki khabar nahi: dobara NAHI (Make queue mein dohri post banegi)
        state.put("li_done_day", day)
        state.put("li_last_err", f"{day} {time.strftime('%H:%M')} {why}")
        state.update("li_log", lambda l: ((l or []) + [{"d": day, "t": time.strftime("%H:%M"), "c": "?"}])[-60:], [])
        return "⚠️ " + why + ". Aaj dobara nahi bhejunga (dohri post se bachne ke liye)."
    if ok:
        if e:
            state.update("li_codes", lambda l: ((l or []) + [str(e.get("aid") or e.get("code"))])[-500:], [])
            state.put("li_last_brand", e.get("brand"))
        if sl:
            from .answers import TOOL_NAMES
            used = state.get("li_tools") or []
            used = [] if all(k in used for k in TOOL_NAMES) else used
            state.put("li_tools", (used + [sl])[-60:])
        state.put("li_done_day", day)
        state.put("li_fail", 0)
        state.update("li_log", lambda l: ((l or []) + [{"d": day, "t": time.strftime("%H:%M"),
                                                         "c": str(e.get("code")) if e else "tool", "id": pid}])[-60:], [])
        link = f"https://www.linkedin.com/feed/update/{pid}/" if pid else ""
        return (f"✅ LinkedIn (Sab Hisaab Page) par post bani" + (f" - sawal #{e.get('code')} ({e.get('bname')})" if e else
                " - aaj ka free tool") + (f"\n{link}" if link else ""))
    n = (state.get("li_fail") or 0) + 1
    state.put("li_fail", n)
    state.put("li_last_err", f"{day} {time.strftime('%H:%M')} {why}")
    log(f"linkedin fail {n}: {why}")
    return f"❌ LinkedIn post nahi gayi ({why})"


def _mig343():
    if state.get("li_mig343"):
        return
    state.put("li_mig343", True)
    try:
        from .answers import repair_short_q
        n = repair_short_q()
        if n:
            log(f"jawab: {n} adhure sawal poore kiye (v3.4.3)")
    except Exception as ex:
        log(f"repair_short_q: {ex}")


def _mig342():
    """16 Nov ki 'post gayi' (sawal #1723) asal mein Make par atki thi - wo record mitao taaki sawal dobara ja sake."""
    if state.get("li_mig342"):
        return
    state.put("li_mig342", True)
    if not any((x or {}).get("id") for x in (state.get("li_log") or [])):
        state.put("li_codes", [])
        state.put("li_log", [])


def due(now=None):
    _mig342()
    _mig343()
    now = now or datetime.datetime.now(IST)
    if not on() or state.get("paused") or state.get("li_done_day") == str(now.date()):
        return False
    if now.strftime("%H:%M") < when():
        return False
    tries = state.get("li_try") or {}
    if tries.get("d") == str(now.date()):
        if tries.get("n", 0) >= MAX_TRY or time.time() - tries.get("at", 0) < 30 * 60:   # 30 min ruk kar dobara, din mein max 3
            return False
    return True


def mark_try():
    day = str(datetime.date.today())
    tr = state.get("li_try") or {}
    n = tr.get("n", 0) + 1 if tr.get("d") == day else 1
    state.put("li_try", {"d": day, "n": n, "at": time.time()})
    return n


def run_due():
    n = (state.get("li_try") or {}).get("n", 1)
    r = post_today()
    if r.startswith("✅"):
        tg.alert("green", "💼 " + r)
    elif r.startswith("⚠️"):
        tg.alert("yellow", "💼 " + r + "\nTheek karna: Make → scenario → Edit → LinkedIn gole ke baad + → Webhooks → "
                 "'Webhook response' (Status 200, Body = LinkedIn ka Post ID) → Save → toggle ON.")
    elif n >= MAX_TRY:
        tg.alert("red", "💼 " + r + f"\n{MAX_TRY} baar koshish hui. Kya karein:\n1) Make.com kholein → Scenarios → 'Integration Webhooks, "
                 "LinkedIn' → upar toggle Active ho\n2) Wahan History mein laal ❌ ho to us par tap → error ka screenshot Claude ko\n"
                 "3) Theek karke bot mein 'linkedin abhi'")
    return r


def remind_due(now=None):
    """Make ka LinkedIn connection ~60 din: 50 aur 57 din par ek-ek yaad (dohraav nahi)."""
    c = _cfg()
    if not c.get("conn_date"):
        return None
    now = now or datetime.datetime.now(IST)
    try:
        age = (now.date() - datetime.date.fromisoformat(c["conn_date"])).days
    except Exception:
        return None
    for mark in (50, 57):
        k = f"{c['conn_date']}:{mark}"
        if age >= mark and k not in (state.get("li_remind") or []):
            state.update("li_remind", lambda l, k=k: ((l or []) + [k])[-10:], [])
            return (f"💼 LinkedIn connection {age} din purana (LinkedIn ~{CONN_DAYS} din par dobara login maangta hai).\n"
                    "Phone/laptop: make.com → left 'Credentials' (ya Connections) → 'Sab Hisaab LinkedIn' → Reauthorize → "
                    "LinkedIn par Allow.\nHo jaye to bot mein: 'ho gaya linkedin reconnect' (30 sec ka kaam).")
    return None


def status_text():
    c = _cfg()
    lg = state.get("li_log") or []
    week = [x for x in lg if x.get("d", "") >= str(datetime.date.today() - datetime.timedelta(days=7))]
    age = ""
    if c.get("conn_date"):
        try:
            age = f"{(datetime.date.today() - datetime.date.fromisoformat(c['conn_date'])).days} din"
        except Exception:
            pass
    return ("💼 LINKEDIN (Sab Hisaab Page, Make.com se)\n"
            f"• Juda: {'✅' if c.get('hook') else '❌ webhook URL nahi'} | API key: {'✅' if c.get('key') else '— (marzi)'}\n"
            f"• Roz: {'CHALU' if state.get('li_on') is not False else 'BAND'} | samay {when()} | aaj: "
            f"{'✅ gayi' if state.get('li_done_day') == str(datetime.date.today()) else 'abhi nahi'}\n"
            f"• 7 din mein post: {len(week)} | kul: {len(lg)}\n"
            f"• Connection umr: {age or '-'} (50 din par bot yaad dilayega)\n"
            + (f"• Aakhri dikkat: {state.get('li_last_err')}\n" if state.get("li_fail") else "")
            + "Hukum: 'linkedin namoona' | 'linkedin abhi' | 'linkedin samay 9:15' | 'linkedin band/chalu' (dohri pushti) | "
              "'linkedin seekh' (Make ko khaana sikhana)")


# ---------------------------------------------------------------- chat
def on_text(t, tl):
    """bot.on_text se. Apna hukum ho to tg.say(...) ka nateeja, warna None."""
    if tl.startswith("ho gaya") and tl not in ("ho gaya linkedin reconnect", "ho gaya linkedin"):
        return None                                # baaki 'ho gaya ...' pending-list wala handler sambhale
    if not tl.startswith(("linkedin", "linked in", "ho gaya linkedin")):
        return None
    tl = tl.replace("linked in", "linkedin")
    if tl in ("linkedin", "linkedin haal", "linkedin status", "linkedin kya haal"):
        return tg.say(status_text())
    if tl in ("linkedin namoona", "linkedin sample", "linkedin preview"):
        txt = compose()[0]
        return tg.say("🧪 NAMOONA (kahin post NAHI hua) - kal/aaj aisa jayega:\n\n" + (txt or "abhi koi taaza sawal nahi"))
    if tl in ("linkedin abhi", "linkedin post", "linkedin bhejo", "linkedin post karo"):
        if not ready():
            return tg.say("❌ Pehle Make ka webhook URL (hook.eu1.make.com/...) yahan paste karein - bot use mita kar rakh lega.")
        txt = compose()[0]
        return tg.say("⚠️ Ye abhi Sab Hisaab LinkedIn Page par jayega (aaj ki roz wali post yahi maani jayegi):\n\n" + (txt or "")[:1500],
                      tg.inline([[("✅✅ Haan, abhi bhejo", "li:now"), ("❌ Nahi", "li:x")]]))
    if tl in ("linkedin seekh", "linkedin learn", "linkedin dhancha"):
        if not ready():
            return tg.say("❌ Pehle Make ka webhook URL paste karein.")
        return tg.say("⚠️ Ye sirf tab dabayein jab Make mein Webhook gole par 'Redetermine data structure' chalu ho (Listening). "
                      "Bot ek chhota namoona bhejega taaki Make 'text' khaana pehchaane. Scenario ON ho to ye namoona Page par "
                      "post ban sakta hai - isliye pehle scenario OFF rakhein.",
                      tg.inline([[("✅✅ Haan, namoona bhejo", "li:learn"), ("❌ Nahi", "li:x")]]))
    if tl in ("linkedin band", "linkedin chalu"):
        v = "on" if tl.endswith("chalu") else "off"
        return tg.say(f"⚠️ Pakka? LinkedIn roz ki post {'CHALU' if v == 'on' else 'BAND'}.",
                      tg.inline([[("✅✅ Haan", f"li:{v}"), ("❌ Nahi", "li:x")]]))
    m = re.match(r"linkedin\s+(?:samay|time|ka samay)\s+(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm|baje|subah|shaam)?", tl)
    if m:
        h, mi = int(m.group(1)), int(m.group(2) or 0)
        if m.group(3) in ("pm", "shaam") and h < 12:
            h += 12
        if not (0 <= h <= 23 and 0 <= mi <= 59):
            return tg.say("❌ Samay samajh nahi aaya. Jaise: 'linkedin samay 9:15' ya 'linkedin samay 6 shaam'.")
        hm = f"{h:02d}:{mi:02d}"
        return tg.say(f"⚠️ Pakka? LinkedIn ki roz ki post {when()} ki jagah {hm} par.",
                      tg.inline([[("✅✅ Haan", f"li:t{hm.replace(':', '')}"), ("❌ Nahi", "li:x")]]))
    if tl in ("ho gaya linkedin reconnect", "ho gaya linkedin"):
        c = _cfg()
        if c:
            c["conn_date"] = str(datetime.date.today())
            _save(c)
        return tg.say("✅ Theek - LinkedIn connection ki ginti aaj se dobara (agli yaad 50 din baad).")
    return tg.say(status_text())


def on_callback(rest, run):
    if rest == "x":
        return tg.say("👍 Kuch nahi badla.")
    if rest == "learn":
        def _l():
            ok, why, pid = send("Sab Hisaab - Make dhancha jaanch (ye post dikhe to mita dein)")
            return tg.say("📨 Namoona bheja. Make mein 'Successfully determined' dikhe to OK dabayein, phir LinkedIn gole mein "
                          "Content = 'text' dobara chunein. (Make ka jawab: " + ("post bani!" if ok else why) + ")")
        return run(_l)
    if rest == "now":
        return run(lambda: tg.say(post_today()))
    if rest in ("on", "off"):
        state.put("li_on", rest == "on")
        return tg.say("💼 LinkedIn roz ki post: " + ("CHALU (" + when() + ")" if rest == "on" else "BAND"))
    if rest.startswith("t") and re.fullmatch(r"t\d{4}", rest):
        hm = f"{rest[1:3]}:{rest[3:5]}"
        state.put("li_time", hm)
        return tg.say(f"⏰ LinkedIn roz ki post ab {hm} par (pakka, yaad rahega).")
    return tg.say("Ye purana button hai.")
