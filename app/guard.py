"""VM guard: trading/backtest ko kabhi takleef nahi. Sirf padhta hai, kuch nahi chhedta."""
import os
import shutil
import time
from .config import (MEM_MIN_MB, WAIT_SEC, TMP, STOCK, LOGS,
                     TMP_HOURS, STOCK_DAYS, LOG_DAYS)
from .log import log


def mem_avail_mb() -> int:
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    return 99999


def backtest_running() -> bool:
    me = os.getpid()
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == me:
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode(errors="ignore").lower()
        except OSError:
            continue
        if ("backtest" in cmd or "/sandbox/runs/" in cmd) and "sabhisaab-network" not in cmd:
            return True                                # v2.1.9: Chowkidar ka backtest (bt-* unit) bhi
    return False


CLK = os.sysconf("SC_CLK_TCK")
REELS_CG = "/sys/fs/cgroup/reels.slice/cpu.stat"
OTHERS_PAUSE = 1.2    # baaki programs (trading/backtest) itne core se zyada lein to ruko
OTHERS_RESUME = 0.8   # itne se kam ho jaye tab phir chalao
OTHERS_FULL = 0.5     # itne se kam ho to 2 core


def _busy_sec() -> float:
    with open("/proc/stat") as f:
        v = [int(x) for x in f.readline().split()[1:9]]
    user, nice, system, idle, iowait, irq, softirq, steal = v
    return (user + nice + system + irq + softirq + steal) / CLK


def _reels_sec() -> float:
    try:
        with open(REELS_CG) as f:
            for line in f:
                if line.startswith("usage_usec"):
                    return int(line.split()[1]) / 1e6
    except OSError:
        pass
    return 0.0


def others_cpu(interval=3.0) -> float:
    """Reels bot ko chhod kar baaki programs kitne core le rahe hain (apna load nahi ginta)."""
    b1, r1 = _busy_sec(), _reels_sec()
    time.sleep(interval)
    b2, r2 = _busy_sec(), _reels_sec()
    return max(0.0, ((b2 - b1) - (r2 - r1)) / interval)


import threading as _th
_DL = _th.local()


def set_deadline(ts):
    """v2.0.2: is samay ke baad intezaar nahi - 1 core par (Nice=10, trading ko pehla haq phir bhi) bana do."""
    _DL.ts = ts


def wait_until_ok(notify=None, max_wait_min=180) -> int:
    """Jab tak VM khaali na ho, ruko. Kitne thread use karne hain wo lautao."""
    paused = False
    start = time.time()
    while True:
        dl = getattr(_DL, "ts", None)
        if dl and time.time() >= dl and mem_avail_mb() > 700:
            if paused and notify:
                notify("⏰ Slot paas hai - 1 core par rendering jaari (trading ko phir bhi pehla haq).")
            return 1
        cpu = others_cpu()
        mem = mem_avail_mb()
        bt = backtest_running()
        limit = OTHERS_RESUME if paused else OTHERS_PAUSE
        if cpu < limit and mem > MEM_MIN_MB and not bt:
            if paused and notify:
                notify("▶️ VM khaali ho gaya, rendering phir shuru.")
            return 2 if cpu < OTHERS_FULL else 1
        if not paused:
            why = ("backtest chal raha hai" if bt else
                   f"trading/baaki programs {cpu:.1f} core le rahe hain" if cpu >= limit else
                   f"RAM sirf {mem} MB khaali")
            log(f"PAUSE: {why}")
            if notify:
                notify(f"⏸ Rendering ruki: {why}. Trading ko pehla haq. Khaali hote hi apne aap shuru hogi.")
            paused = True
        if time.time() - start > max_wait_min * 60:
            raise TimeoutError("VM bahut der se busy hai")
        time.sleep(WAIT_SEC)


def _older_than(path, seconds):
    try:
        return time.time() - path.stat().st_mtime > seconds
    except OSError:
        return False


def cleanup() -> str:
    freed = 0
    for p in TMP.iterdir():
        if _older_than(p, TMP_HOURS * 3600):
            freed += _size(p)
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    for p in STOCK.iterdir():
        if _older_than(p, STOCK_DAYS * 86400):
            freed += _size(p)
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    eng = LOGS / "engine.log"            # v2.0: engine.log kabhi rotate nahi hota tha
    try:
        if eng.exists() and eng.stat().st_size > 50 * 2**20:
            eng.rename(LOGS / f"engine.log.{time.strftime('%Y%m%d%H%M')}")
    except OSError:
        pass
    for p in LOGS.glob("*.log.*"):
        if _older_than(p, LOG_DAYS * 86400):
            freed += _size(p)
            p.unlink(missing_ok=True)
    msg = f"🧹 Safai: {freed / 1e6:.1f} MB khaali"
    log(msg)
    return msg


def _size(p) -> int:
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


# ---------------- v2.3.0 Step 1 (v11 se milan): Gemini Blindfold DLP + stuck ffmpeg reaper + deep safai ----------------
import re as _re
import pathlib as _pl
import subprocess as _sp

_SECRET_PATTERNS = [
    _re.compile(r"\d{8,12}:[A-Za-z0-9_-]{30,}"),                 # Telegram bot token
    _re.compile(r"EAA[A-Za-z0-9]{30,}"),                         # Meta token
    _re.compile(r"\bTH[A-Za-z0-9_\-]{35,}"),                     # Threads token
    _re.compile(r"AIza[0-9A-Za-z_-]{30,}"),                      # Google API key
    _re.compile(r"GOCSPX-[A-Za-z0-9_\-]{18,}"),                  # Google OAuth secret
    _re.compile(r"\bya29\.[A-Za-z0-9_\-]{20,}"),                 # Google access token
    _re.compile(r"\b1//0[A-Za-z0-9_\-]{30,}"),                   # Google refresh token
    _re.compile(r"gh[pousr]_[A-Za-z0-9]{25,}"),                  # GitHub
    _re.compile(r"github_pat_\w{25,}"),
    _re.compile(r"x-access-token:[^@\s]+@"),
    _re.compile(r"pina_[A-Za-z0-9_\-]{18,}"),                    # Pinterest
    _re.compile(r"\bcf[a-z]{2,3}_[A-Za-z0-9._\-]{20,}"),         # Cloudflare
    _re.compile(r"\b[0-9a-f]{32}\b"),                            # 32-hex secret (Meta app secret, Bing key)
    _re.compile(r"\b[0-9a-f]{40}\b"),
    _re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    _re.compile(r"(?i)(?:api_?key|secret|token|password|passwd|authorization)\s*[:=]\s*['\"]?[^'\"\s,}{]{6,}"),
    _re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),                  # email
    _re.compile(r"(?<![\d₹,.])(\+?91[\s-]?)?[6-9]\d{9}(?![\d,])"),  # Indian mobile (rupaye ki rakam nahi)
]


def scrub_for_ai(text):
    """Gemini Blindfold: AI (Gemini / Cloudflare AI) ko jaane wale har text se token, secret, email, phone, secrets path hatao."""
    if not isinstance(text, str) or not text:
        return text
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[VAULT_CHHUPA]", out)
    for p in ("/home/ubuntu/sabhisaab-network/secrets", "/home/ubuntu/.ssh", "/home/ubuntu/.oci"):
        out = out.replace(p, "[SECRETS_LOCKED]")
    try:
        from . import state
        state.update("blindfold_hits", lambda n, d=(out != text): (n or 0) + (1 if d else 0), 0)
    except Exception:
        pass
    return out


def blindfold_status():
    from . import state
    probe = ("token EAAabcdef1234567890abcdefghijklmnopqrstuvwxyz and AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz123456 "
             "mail test@gmail.com phone 9876543210 /home/ubuntu/sabhisaab-network/secrets/bot.env")
    s = scrub_for_ai(probe)
    ok = all(x not in s for x in ("EAAabcdef", "AIzaSy", "test@gmail.com", "9876543210", "/secrets/bot.env"))
    keep = scrub_for_ai("SIP ₹5000 x 12% = ₹6000000000 nahi") == "SIP ₹5000 x 12% = ₹6000000000 nahi"
    return (f"🙈 GEMINI BLINDFOLD (DLP): {'✅ CHALU' if ok else '❌ GADBAD'}\n"
            f"• Gemini, Google-search Gemini, Cloudflare AI aur image AI - sabke prompt pehle saaf\n"
            f"• Token/secret/email/phone/secrets path → [VAULT_CHHUPA]\n"
            f"• Rupaye ki rakam nahi chhedi: {'✅' if keep else '⚠'}\n"
            f"• Ab tak chhupaya: {state.get('blindfold_hits') or 0} baar")


def _own_ffmpeg(pid):
    """Sirf sabhinet (reels.slice / sabhinet.service / sn-test) ka ffmpeg - trading/system ka kabhi nahi."""
    try:
        cg = open(f"/proc/{pid}/cgroup").read()
        return "sabhinet" in cg or "reels.slice" in cg
    except Exception:
        return False


def reap_stuck_ffmpeg(max_minutes=40):
    """v11 se: atka ffmpeg (max_minutes se zyada) band - SIRF sabhinet ka apna. Returns list."""
    killed = []
    try:
        r = _sp.run(["ps", "-eo", "pid,etimes,comm,args"], capture_output=True, text=True, timeout=10)
        for line in r.stdout.splitlines()[1:]:
            parts = line.strip().split(None, 3)
            if len(parts) < 4:
                continue
            pid_s, etimes_s, comm, args = parts
            if "ffmpeg" in comm.lower() and int(etimes_s) > max_minutes * 60 and _own_ffmpeg(pid_s):
                try:
                    os.kill(int(pid_s), 15)
                    time.sleep(1)
                    try:
                        os.kill(int(pid_s), 9)
                    except OSError:
                        pass
                    killed.append(f"PID {pid_s} ({int(etimes_s) // 60}m): {args[:80]}")
                    log(f"REAPED STUCK FFMPEG: PID {pid_s} {int(etimes_s) // 60} min")
                except Exception as e:
                    log(f"reap fail {pid_s}: {e}")
    except Exception as e:
        log(f"reap_stuck_ffmpeg: {e}")
    return killed


def clean_uv_cache(execute=False):
    """Deep Safai: atka ffmpeg + bot ka kachra; ~/.cache/uv (dobara ban jaata) sirf execute par.
    ~/.cache/huggingface (sabhinet ki awaaz/model) KABHI nahi."""
    uv_cache = _pl.Path("/home/ubuntu/.cache/uv")
    hf_cache = _pl.Path("/home/ubuntu/.cache/huggingface")
    reaped = reap_stuck_ffmpeg(35)
    base_clean = cleanup()
    uv_mb = _size(uv_cache) / 1e6 if uv_cache.exists() else 0.0
    hf_mb = _size(hf_cache) / 1e6 if hf_cache.exists() else 0.0
    freed = 0.0
    if execute and uv_cache.exists():
        try:
            shutil.rmtree(uv_cache, ignore_errors=True)
            freed = uv_mb
        except Exception as e:
            log(f"uv clean: {e}")
    return (f"🧹 DEEP SAFAI {'(kiya)' if execute else '(sirf jaanch)'}\n"
            f"• Atke ffmpeg band: {len(reaped)}" + ("".join(f"\n   - {k}" for k in reaped[:5])) + "\n"
            f"• Bot ka kachra: {base_clean}\n"
            f"• ~/.cache/uv: {uv_mb:.0f} MB" + (f" → {freed:.0f} MB khali" if execute else " (likhein 'deep safai karo' → dohri pushti)") + "\n"
            f"• ~/.cache/huggingface: {hf_mb:.0f} MB — 🔒 KABHI nahi (awaaz/model)")
