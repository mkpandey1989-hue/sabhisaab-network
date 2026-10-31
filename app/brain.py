"""Bot ka dimaag: aapki normal Hindi/Hinglish baat samajhna (Gemini). Model: sabse upar wala pehle,
seema/credit khatam ho to apne aap neeche wala. Gemini na chale to keyword se samjhe."""
import datetime
import json
import os
import re
import requests
from . import state, diary
from .config import BRANDS, IST
from .log import log

MODELS = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"]   # sirf tab jab list na mile
SKIP = ("tts", "image", "embedding", "audio", "live", "robotics", "computer-use", "vision", "aqa", "learnlm")
ACTIONS = ["status", "today", "week", "vm", "views", "make_video", "make_long", "comments", "report", "add_topic",
           "set_count", "plan", "show_plan", "insights", "day_report", "news", "growth_graph", "video_detail", "delete", "dup_scan", "festivals", "meeting", "rule", "web", "website", "tasks", "platform", "pending", "approve", "reject", "new_thumbs",
           "pause", "resume", "set_schedule", "set_auto", "logs", "safety", "help", "diary", "doctor", "upgrade", "chat"]
CHANGES = {"make_video", "make_long", "set_count", "platform", "approve", "reject", "pause", "resume", "set_schedule", "set_auto",
           "new_thumbs", "add_topic", "rule", "set_report"}
# v2.0.3: owner ka hukum - koi bhi pakki setting (samay, topic, platform, niyam, report) bina DOHRI pushti ke kabhi nahi
DOUBLE = {"set_schedule", "set_auto", "set_count", "platform", "add_topic", "rule", "set_report"}

PROMPT = """You are "Sabhisaab bot", the smart, friendly, honest manager of the owner's 4 Hindi brands
(YouTube, Facebook, Instagram, Threads, Telegram, Pinterest). Talk like a capable assistant/partner in simple Hinglish
(Roman script), warm, to the point. Address him as "Manoj bhai". Plain text only (no markdown, no ** or #).
HONESTY (sabse zaroori): kabhi mat kaho ki tumne koi kaam kar diya (delete, badla, bheja, set kiya) jab tak wo kaam
action/tool se sach mein na hua ho. Chat ka jawab sirf jaankari hai. Kuch nahi kar sakte to saaf bolo aur batao owner
kya likhe (jaise: delete ke liye us message par reply karke 'delete' likhein). Samajh na aaye to pooch lo.
Brands (key: name): {brands}
KNOWLEDGE (pakki jaankari - system, niyam, policy, seema, website, khule kaam):
{kb}
LIVE FACTS (the only truth; never invent numbers/links; if something is not here, say you don't know yet and how to check):
{facts}
Recent conversation:
{chat}
Recent diary: {diary}
Owner's new message: "{msg}"

Decide the action. Return ONLY JSON:
{{"action": one of {actions}, "brand": brand key | "all" | "", "topic": "", "time": "HH:MM" or "HH:MM,HH:MM" | "",
 "count": number | 0, "thumb": 0-3,
 "auto": true | false | null, "reply": "your answer to the owner",
 "need": [{{"tool": name, "arg": "..."}}] (optional, max 3)}}
Rules:
- THINK like a smart manager who knows the whole system (KNOWLEDGE). If answering needs data you do not have
  (a website page detail, a plan of some date, what happened on a day, pending tasks, traffic, why a page is not
  indexed, video stats, upgrade status, a current real-world fact), set action "chat" and ask for it in "need" using
  tools: {tools}. The bot will run them and ask you again with results (TOOL RESULTS). Do not guess.
- "website doctor / page index kyun nahi / indexing ki dikkat" -> doctor (topic = page slug if given).
  "upgrade / khud sudhaar / bot update haal" -> upgrade.
- Make/post a reel/video -> make_video. Every video ALWAYS goes to all platforms of that brand, so phrases like
  "sab page par / sab jagah / har platform par" do NOT mean all brands. Use brand "all" ONLY if he clearly says all
  brands / charon brand / har channel ki alag-alag. If he names one brand, use that brand.
- topic = only the real subject he wants the video about (e.g. "Valmiki Jayanti", "SIP"). Style words like
  "attractive, badiya, mast, modern thumbnail, check karke" are NOT topics -> topic "".
- Long/lambi/8-10 minute video -> make_long. Mood/style words (mazedaar, emotional, motivation) go in topic only if
  he gives a subject; otherwise topic "".
- Comments check/reply -> comments. Weekly/full A-Z report -> report.
- "is topic par bhi video banao / ye bhi yaad rakho" (future topics, not now) -> add_topic with brand + topic.
- Daily upload limit change -> set_count with count. Weekly content/marketing plan -> plan.
  "kya seekha / kya chal raha hai views mein / kyun nahi dekh rahe" -> insights.
- ANSWER EXACTLY WHAT IS ASKED. "kal/aaj/parso ka plan kya hai" -> show_plan (put date YYYY-MM-DD in "time" field),
  NOT plan. Only "plan banao / naya plan" -> plan.
- "aaj kya kiya / din bhar ka hisaab / diary" -> day_report. "khabar / news" -> news.
- "graph / growth / channel kitna badha" -> growth_graph. Any question about views/likes/comments of videos on any
  platform ("facebook par kitne like", "labh lo deals instagram views") -> video_detail with brand and put platform
  name (facebook/instagram/youtube) in "topic". NEVER say data is not available - use video_detail.
- "video/post delete karo / hatao / galti se gayi" -> delete (bot will list and ask double confirmation).
- "duplicate kitne gaye / dobara video check karo" -> dup_scan (bot scans real channels). Never say you cannot check.
- "tyohaar / event / aaj kya hai / panchang / muhurat" -> festivals. "meeting / company report / departments" -> meeting.
- Owner gives a permanent instruction or correction ("aage se aisa mat karna", "hamesha ...", "ye galat hai, sahi ye hai")
  -> rule, put the rule text in "topic".
- "X brand ka facebook/instagram/threads/pinterest/telegram/youtube band karo / mat dalo / chalu karo" -> platform with
  brand, platform name in "topic", auto=false for band, true for chalu.
- Website visitors/traffic/kitne log aaye/link se kitne aaye -> website topic "traffic" (count = days, default 1).
  ANY file request (website page, calculator, .py code, photo, video, folder, "poori website") -> website topic
  "file:<best keyword e.g. advance-tax-calculator, photo, site>". Never claim you saved/remember files yourself.
- Website (sabhisaab.com) full check report/GSC -> website topic "report"; index/indexing -> "index";
  audit -> "audit"; deploy -> "deploy"; bing -> "bing". "mere kaam / kya baaki hai / pending steps" -> tasks.
- Any current/real-world fact question not in facts (dates, muhurat, rules, rates, news, "kab hai", "kitna hai")
  -> web, put the exact question in "topic". Never guess dates.
- If facts already contain the answer, use action chat and answer directly with numbers/links from facts.
- Changing a brand's daily time -> set_schedule (24h HH:MM). Auto upload on/off -> set_auto.
- Questions (kya haal, kitni video, kya chal raha, kaun sa platform fail, kyun) -> action "chat" and answer fully
  from LIVE FACTS in "reply" (mention failures and what to do). Views/likes report request -> views.
- Never claim you did something; actions happen only after his confirmation."""


def _rank(name):
    m = re.search(r"gemini-(\d+(?:\.\d+)?)", name)
    ver = float(m.group(1)) if m else 0
    tier = 1 if "lite" in name else (3 if "pro" in name else 2)
    preview = 1 if ("preview" in name or "exp" in name) else 0
    return (-ver, -tier, preview, name)


def discover(force=False):
    """Google se poochho abhi kaun se model chalu hain; sabse naya + sabse taakatwar pehle. Roz ek baar."""
    today = str(datetime.date.today())
    c = state.get("gemini_models") or {}
    if c.get("date") == today and c.get("list") and not force:
        return c["list"]
    key = os.environ.get("GEMINI_API_KEY")
    names = []
    try:
        r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                         params={"key": key, "pageSize": 200}, timeout=30).json()
        for mdl in r.get("models", []):
            n = mdl.get("name", "").replace("models/", "")
            if (n.startswith("gemini-") and "generateContent" in mdl.get("supportedGenerationMethods", [])
                    and not any(x in n for x in SKIP)):
                names.append(n)
    except Exception as e:
        log(f"brain: model list nahi mili ({e})")
    names = sorted(set(names), key=_rank)[:8]
    if names:
        state.put("gemini_models", {"date": today, "list": names})
    return names


def _models():
    cool = state.get("gemini_cool", {})
    today = str(datetime.date.today())
    env = os.environ.get("GEMINI_MODEL")
    order = discover() or MODELS
    if env and env not in order:
        order = order + [env]
    return [m for m in order if cool.get(m) != today]


def _json(txt):
    """Sochne wale (naye) model JSON ke aas-paas extra text bhi dete hain: pehla poora {...} nikaalo."""
    t = re.sub(r"^```(json)?|```$", "", txt.strip()).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    start = t.find("{")
    depth = 0
    for i in range(start, len(t)) if start >= 0 else []:
        depth += t[i] == "{"
        depth -= t[i] == "}"
        if depth == 0:
            return json.loads(t[start:i + 1])
    raise ValueError("JSON nahi mila")


def ask_gemini(prompt, json_mode=True, temperature=0.3):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Gemini key nahi")
    last = None
    for m in _models():
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                              params={"key": key}, timeout=90,
                              json={"contents": [{"parts": [{"text": prompt}]}],
                                    "generationConfig": {"temperature": temperature, **(
                                        {"responseMimeType": "application/json"} if json_mode else {})}})
            j = r.json()
            if r.status_code in (429, 403) or "quota" in json.dumps(j).lower():
                state.update("gemini_cool", lambda d, m=m: {**(d or {}), m: str(datetime.date.today())}, {})
                log(f"brain: {m} ki seema khatam, agla model")
                last = f"{m} quota"
                continue
            if r.status_code == 404:          # model band ho gaya -> aaj ke liye hatao
                state.update("gemini_cool", lambda d, m=m: {**(d or {}), m: str(datetime.date.today())}, {})
                last = f"{m}: model nahi mila"
                continue
            if r.status_code != 200:
                last = f"{m}: {r.status_code} {j.get('error', {}).get('message', '')[:120]}"
                state.update("gemini_status", lambda d, m=m, x=last: {**(d or {}), m: x[:80]}, {})
                continue
            txt = j["candidates"][0]["content"]["parts"][0]["text"]
            state.update("gemini_status", lambda d, m=m: {**(d or {}), m: "ok"}, {})
            state.put("gemini_last_model", m)
            state.put("gemini_last_error", "")
            if not json_mode:
                return txt
            return _json(txt)
        except Exception as e:
            last = f"{m}: {e}"
            state.update("gemini_status", lambda d, m=m, x=str(e): {**(d or {}), m: x[:80]}, {})
    state.put("gemini_last_error", str(last)[:300])
    raise RuntimeError(f"Gemini nahi chala ({last})")


def remember(who, text):
    state.update("chat_log", lambda l: ((l or []) + [f"{who}: {text[:600]}"])[-30:], [])


def understand(msg, facts, tool_results=""):
    from . import kb
    brands = ", ".join(f"{k}: {v['name']}" for k, v in BRANDS.items())
    dia = "; ".join(f"{r['kind']}:{r['text'][:80]}" for r in diary.recent(15))
    chat = "\n".join(state.get("chat_log", [])[-20:])
    if tool_results:
        facts = facts + "\nTOOL RESULTS (abhi nikale, inhi se jawab do, need dobara mat maango jab tak zaroori na ho):\n" + tool_results
    try:
        out = ask_gemini(PROMPT.format(brands=brands, kb=kb.text(), facts=facts[:16000], diary=dia[:2000], msg=msg[:1500],
                                       chat=chat[:5000], actions=ACTIONS, tools=kb.TOOLS), temperature=0.4)
        if not (out.get("need") and not tool_results):
            remember("Manoj", msg)
            remember("Bot", out.get("reply", ""))
        if out.get("action") not in ACTIONS:
            out["action"] = "chat"
        if out.get("brand") not in BRANDS and out.get("brand") != "all":
            out["brand"] = guess_brand(msg)
        return out
    except Exception as e:
        log(f"brain fallback: {e}")
        return {"action": "chat", "brand": guess_brand(msg), "topic": "", "time": "", "thumb": 0, "auto": None,
                "reply": "Abhi Gemini (samajhne wala dimaag) jawab nahi de raha - seema ya network. "
                         "Tab tak button/menu se karein; agla sandesh aate hi bot phir Gemini aazmayega."}


def guess_brand(msg):
    m = msg.lower().replace(" ", "")
    if any(w in m for w in ("sabbrand", "charon", "harchannel", "allbrand", "charobrand")):
        return "all"
    for k, v in {"sunonatak": ["suno", "natak", "kahani"], "money": ["money", "sip", "nivesh"],
                 "deals": ["deal", "labh", "offer"], "pahadi": ["pahad", "pahadi", "zameen", "jameen"]}.items():
        if any(w in m for w in v):
            return k
    return ""


def summary(intent):
    a = intent["action"]
    b = "Charon brand" if intent.get("brand") == "all" else BRANDS.get(intent.get("brand") or "", {}).get("name", "")
    return {"make_video": f"🎬 {b or '(brand?)'} ki video banana" + (f" — topic: {intent['topic']}" if intent.get("topic") else ""),
            "make_long": f"📺 {b or '(brand?)'} ki LAMBI video (8-12 min) banana" + (f" — topic: {intent['topic']}" if intent.get("topic") else ""),
            "set_schedule": f"⏰ {b or '(brand?)'} ka roz ka samay {intent.get('time') or '(samay?)'} karna",
            "set_auto": f"🤖 Auto-upload {'ON' if intent.get('auto') else 'OFF'} karna",
            "set_count": f"⬆️ Roz ki upload seema {intent.get('count') or '?'} karna",
            "platform": f"🔀 {intent.get('brand')} ka {intent.get('topic')} {'chalu' if intent.get('auto') else 'band'} karna",
            "pause": "⏸ Roz ka kaam rokna", "resume": "▶️ Roz ka kaam chalu karna",
            "approve": f"✅ Pending video Thumb {intent.get('thumb') or 1} se daalna",
            "reject": "❌ Pending video hatana", "new_thumbs": "🎨 Naye thumbnail banana",
            "add_topic": f"🧩 {b or '(brand?)'} ke liye aage ka topic yaad rakhna: {intent.get('topic') or '?'}",
            "rule": f"📌 Pakka niyam (hamesha laagu): {intent.get('topic') or '?'}",
            "set_report": f"🕗 " + {"site": "Website ki roz ki report", "day": "Din ki report", "events": "Tyohaar/events report"}
            .get(intent.get("topic"), str(intent.get("topic"))) + f" roz theek {intent.get('time')} baje (IST) bhejna"}.get(a, a)



def ask_grounded(prompt, temperature=0.1):
    """Google Search ke saath Gemini (asli, aaj ki jaankari + source links). Returns (text, [urls])."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Gemini key nahi")
    last = None
    for m in _models():
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                              params={"key": key}, timeout=120,
                              json={"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}],
                                    "generationConfig": {"temperature": temperature}})
            j = r.json()
            if r.status_code != 200:
                last = f"{m}: {r.status_code} {j.get('error', {}).get('message', '')[:100]}"
                continue
            c = j["candidates"][0]
            txt = "".join(p.get("text", "") for p in c["content"]["parts"])
            gm = c.get("groundingMetadata", {})
            urls = [ch.get("web", {}).get("uri", "") for ch in gm.get("groundingChunks", [])]
            titles = [ch.get("web", {}).get("title", "") for ch in gm.get("groundingChunks", [])]
            state.put("grounded_last_model", m)
            return txt, [f"{t} {u}"[:160] for t, u in zip(titles, urls) if u]
        except Exception as e:
            last = f"{m}: {e}"
    raise RuntimeError(f"Google-search wala Gemini nahi chala ({last})")
