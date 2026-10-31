"""Sabhisaab Network - saari settings ek jagah."""
import os
import pathlib

BASE = pathlib.Path(os.environ.get("SN_BASE", "/home/ubuntu/sabhisaab-network"))
DATA = BASE / "data"
TMP = DATA / "tmp"
STOCK = DATA / "stock"
POSTED = DATA / "posted"
LOGS = BASE / "logs"
for _d in (TMP, STOCK, POSTED, LOGS):
    _d.mkdir(parents=True, exist_ok=True)

# Awaaz: Kokoro hf_alpha (final). Badalna ho to sirf ye line.
TTS_ENGINE = os.environ.get("SN_TTS", "kokoro")   # kokoro | silent (sirf test)
VOICE = os.environ.get("SN_VOICE", "hf_alpha")
VOICE_SPEED = float(os.environ.get("SN_VOICE_SPEED", "1.0"))

# Video
W, H, FPS = 1080, 1920, 30
CRF, PRESET = 19, "medium"
AUDIO_BITRATE = "192k"
LOUDNESS = "loudnorm=I=-14:TP=-1.5:LRA=11"

# VM ki suraksha: trading ko pehla haq
LOAD_PAUSE = 1.7       # isse upar load ho to rendering ruk jaye
LOAD_FULL = 0.8        # isse neeche ho to 2 core
MEM_MIN_MB = 1500      # system mein isse kam khaali RAM ho to ruk jaye
WAIT_SEC = 30

# Safai
TMP_HOURS = 6
STOCK_DAYS = 10          # v2.0: VM 2 OCPU/12 GB/200 GB - zyada stock
LOG_DAYS = 30            # v2.0: 30 din log
BACKUP_KEEP = 7          # v2.0: 7 din ke backup (pehle 1 - chhoti VM ki seema). 30 din privacy seema ke andar

SITE = "https://sabhisaab.com"
FORBIDDEN_WORDS = ["manoj", "pandey", "मनोज", "पाण्डेय", "पांडेय"]   # owner ka naam kabhi video mein nahi
AI_LABEL = "Is video ki awaaz AI se bani hai."

BRANDS = {
    "sunonatak": dict(name="Suno Natak", bg=("#160b2e", "#4b1d6e"), accent="#ffcc33",
                      footer="Kahaniyan kalpanik, sabak asli", tags="#SunoNatak #PaiseKiKahani"),
    "money": dict(name="Sab Hisaab Money", bg=("#04221d", "#0b5d4b"), accent="#7cffb2",
                  footer="SEBI registered adviser nahi, sirf jaankari", tags="#SabHisaabMoney #Bachat"),
    "deals": dict(name="Labh Lo Deals", bg=("#2e0a0a", "#8a1c1c"), accent="#ffd166",
                  footer="Bachat aur deals ki aasaan jaankari", tags="#LabhLoDeals #Bachat"),
    # v1.8: "#ad" ab sirf usi post par jisme sach mein affiliate link ho (meta["affiliate"]) - ASCI ka sahi tareeka
    "pahadi": dict(name="Pahadi Hisaab", bg=("#08222f", "#1d5a6b"), accent="#9be7ff",
                   footer="Pahadi zameen aur yojana ki jaankari", tags="#PahadiHisaab #Uttarakhand"),
}

# ---------------- v0.2: 24x7 bot ----------------
import datetime as _dt
IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))
SECRETS = BASE / "secrets"
SECRETS.mkdir(mode=0o700, exist_ok=True)
STATE = DATA / "state.json"

# Roz kis brand ki video kab public ho (IST). Video 3 ghante pehle banti hai.
SCHEDULE = {
    "pahadi": "09:30",
    "money": "12:30",
    "deals": "16:00",
    "sunonatak": "19:30",
}
PREPARE_HOURS = 3            # slot se itne ghante pehle video bane aur Telegram par manzoori ke liye aaye
AUTO_APPROVE = True          # jawab na mile to slot par apne aap (Thumb 1 = ab tak sabse achha) upload
MAX_UPLOADS_DAY = 6          # YouTube API ki roz ki seema ke andar (4 channel ek hi project)
YT_CATEGORY = "27"           # Education
GITHUB_MIRROR = "mkpandey1989-hue/sabhisaab-network"   # sirf code ki copy, audit ke liye
GEMINI_FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]

# ---------------- v0.3: Facebook / Instagram / Telegram channel ----------------
# v2.0: Graph version ek jagah; upgrader naya version test karke data/graph_ver.txt mein likhta hai (restart par laagu)
_GV = DATA / "graph_ver.txt"
GRAPH_VER = (_GV.read_text().strip() if _GV.exists() else "") or "v23.0"
GRAPH = f"https://graph.facebook.com/{GRAPH_VER}"
RUPLOAD = "https://rupload.facebook.com"
TG_CHANNEL = "@sabhisaab"          # hub channel; bot ko wahan admin banana zaroori
PLATFORMS = ["youtube", "facebook", "instagram", "threads", "telegram"]


# ---------------- v1.8: saare channel ke link (ek jagah; naya channel/brand aaye to sirf yahan badlein) ----------------
SITE_URL = SITE + "/"                       # video par aur har jagah poora pata: https://sabhisaab.com/
TELEGRAM = "https://t.me/sabhisaab"
WHATSAPP = "https://whatsapp.com/channel/0029Vb8rHA5EFeXmREHFHk3n"
PINTEREST = "https://www.pinterest.com/sabhisaabcom/"
HANDLES = {"sunonatak": "sunonatak", "money": "sabhisaabmoney", "deals": "labhlodeals", "pahadi": "pahadihisaab"}
LINKS = {k: {"youtube": f"https://www.youtube.com/@{h}", "facebook": f"https://www.facebook.com/{h}",
             "instagram": f"https://www.instagram.com/{h}", "threads": f"https://www.threads.net/@{h}"}
         for k, h in HANDLES.items()}


# ---------------- v2.0: bade VM ke hisaab se seemaayein ----------------
SITE_ZIP_MAX_FILES = 3000     # pehle 22 (purane Cloudflare Worker bot ki seema thi) - VM par git se koi seema nahi
NEW_PAGES_PER_DAY = 10        # Google scaled-content niyam: ek din mein 10 se zyada NAYE page nahi (fix ki ginti nahi)
TG_MAX_MB = int(os.environ.get("SN_TG_MAX_MB", "20"))   # Telegram cloud API 20 MB; local Bot API server par 2000
