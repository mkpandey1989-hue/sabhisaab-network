#!/usr/bin/env python3
"""delta_pro_v2.py  (Claude, 27 Nov 2026) - Delta BTC bot ka PRO v2 (Nifty PRO v2 jaisa, Delta policy ke hisaab se).

TRADE RULE SAME (1 trade/din, SL candle LOW/HIGH, risk/lock/kill, exchange stop, 10s button window). Sirf:
  SL check har 0.5s (Delta quota 20000/5min ke andar), 429 pe Delta ka X-RATE-LIMIT-RESET jitna wait,
  Telegram turant (long-poll + background), late-press grace 3s, button pe ⏰ close-time + countdown +
  20s ping (raat 23:00-07:00 IST ping chup), ✏️ Custom risk, Excel EXIT row sahi, band candle time se pakki,
  VM ghadi + Delta clock drift check, 4 TF (1/5/15/30).  +  delta-live.service: RestartSec -> 2s.

Kya karta hai (sab check ke baad, warna KUCH NAHI badalta):
 1) Bot ka trade / ARMED chal raha ho (dashboard :8002 /state se) -> ruk jaata hai, baad mein chalao.
 2) Naya code PRIVATE repo vm-bots (branch claude/delta-pro-v2) se VM ke apne GitHub token se.
 3) VM ki abhi wali delta_btc_LIVE.py wahi honi chahiye jo aaj raat 02:40 GitHub pe gayi (chat id/topic chhod ke).
 4) Asli Telegram chat id + ntfy topic VM file se naye code mein (token pehle ki tarah delta_tg.txt mein).
 5) compile + load test -> backup ~/deltabot/deploy_backups (⏪ rollback button isi se) -> restart -> 20s check,
    bot baar-baar gire to purana khud wapas.
Wapas purana: Delta Telegram bot pe ⏪ rollback
"""
import base64
import hashlib
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import time
import urllib.request

HOME = "/home/ubuntu"
DIR = os.path.join(HOME, "deltabot")
BOT = os.path.join(DIR, "delta_btc_LIVE.py")
REPO = "mkpandey1989-hue/vm-bots"
BRANCH = "claude/delta-pro-v2"
BASE_SHA256 = ("0b871104d47c99255a6f180f9b8fe851f7796be5a63fe33eb00a53ab15b73c99",)   # 27-Nov 02:40 wali ('***' ke saath)
MARK = "PRO v2 (27-Nov-2026, Nifty PRO v2 jaisa"
SECRET_KEYS = ("TG_CHAT_ID", "NTFY_TOPIC")
UNIT = "/etc/systemd/system/delta-live.service"


def say(x): print(x, flush=True)


def ist():
    return time.gmtime(time.time() + 19800)


def gh_token():
    envf = os.path.join(HOME, "sabhisaab-network/secrets/bot.env")
    try:
        for ln in open(envf, encoding="utf-8"):
            if ln.startswith("GITHUB_TOKEN="):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return os.environ.get("GITHUB_TOKEN", "")


def fetch_new(tok):
    url = f"https://api.github.com/repos/{REPO}/contents/home/deltabot/delta_btc_LIVE.py?ref={BRANCH}"
    rq = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}",
                                              "Accept": "application/vnd.github.raw",
                                              "User-Agent": "delta-pro-v2"})
    with urllib.request.urlopen(rq, timeout=60) as r:
        return r.read().decode("utf-8")


def secret_re(k):
    return re.compile(r'^(\s{4}' + k + r'\s*=\s*)"([^"\n]*)"', re.M)


def masked(text):
    for k in SECRET_KEYS:
        text = secret_re(k).sub(lambda m: m.group(1) + '"***"', text)
    return text.replace("\r\n", "\n")


def bot_busy():
    """Dashboard se phase padho. (busy?, wajah)"""
    pw = ""
    try: pw = open(os.path.join(DIR, "delta_dashboard_pass.txt"), encoding="utf-8").read().strip()
    except Exception: pass
    try:
        rq = urllib.request.Request("http://127.0.0.1:8002/state")
        if pw: rq.add_header("Authorization", "Basic " + base64.b64encode(f"u:{pw}".encode()).decode())
        with urllib.request.urlopen(rq, timeout=5) as r:
            d = json.loads(r.read().decode("utf-8"))
        ph = str(d.get("phase", ""))
        if ph in ("ACTIVE", "PENDING_FILL", "ARMED"):
            return True, f"bot abhi {ph} hai (trade/arm chal raha)"
        return False, ph or "?"
    except Exception as e:
        return None, f"dashboard nahi padh paya ({e})"


def fix_unit():
    try:
        u = open(UNIT).read()
    except Exception:
        say("⚠️ delta-live.service nahi mili - restart-time fix nahi laga (bot ka baaki sab chalega)"); return False
    m = re.search(r"^RestartSec=(\d+)$", u, flags=re.M)
    if not m or int(m.group(1)) <= 2:
        say("ℹ️ Service restart-time pehle se theek"); return True
    new_u = re.sub(r"^RestartSec=\d+$", "RestartSec=2", u, flags=re.M)
    bk = os.path.join(HOME, "unit_backups"); os.makedirs(bk, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    subprocess.run(["sudo", "cp", "-a", UNIT, f"{bk}/delta-live.service.{stamp}"], check=False)
    tmp = f"/tmp/delta-live.service.{stamp}"
    open(tmp, "w").write(new_u)
    r = subprocess.run(["sudo", "cp", tmp, UNIT])
    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    ok = r.returncode == 0 and "RestartSec=2" in open(UNIT).read()
    say(f"✅ delta-live restart wait {m.group(1)}s -> 2s. Backup: {bk}/delta-live.service.{stamp}" if ok
        else "⚠️ Service fix nahi laga (bot ka baaki sab chalega)")
    return ok


def main():
    force = "--force" in sys.argv
    if not os.path.exists(BOT):
        sys.exit(f"❌ {BOT} nahi mila - kuch nahi badla")
    cur = open(BOT, encoding="utf-8").read()
    if MARK in cur:
        say("ℹ️ Delta bot mein PRO v2 pehle se laga hai - file nahi chhedi.")
        fix_unit(); return
    busy, why = bot_busy()
    if busy and not force:
        sys.exit(f"⏸️ {why} - KUCH NAHI badla. Trade band hone ke baad chalao.")
    if busy is None and not force:
        sys.exit(f"⏸️ {why} - pakka nahi ki trade nahi chal raha, isliye KUCH NAHI badla. "
                 f"Delta Telegram pe 'status' dekho; trade na ho to:  python3 /tmp/delta_pro_v2.py --force")
    h = hashlib.sha256(masked(cur).encode("utf-8")).hexdigest()
    if h not in BASE_SHA256:
        sys.exit("🛑 VM ki delta_btc_LIVE.py aaj raat 02:40 ke baad BADLI hai (ya alag hai) - KUCH NAHI badla. "
                 "Claude ko batao: 'delta pro script ruki - file badli hai'.")
    tok = gh_token()
    if not tok:
        sys.exit("❌ GitHub token nahi mila (~/sabhisaab-network/secrets/bot.env) - kuch nahi badla")
    try:
        new = fetch_new(tok)
    except Exception as e:
        sys.exit(f"❌ Naya code GitHub se nahi aaya ({e}) - kuch nahi badla")
    if MARK not in new:
        sys.exit("❌ GitHub wali file PRO v2 nahi lagti - kuch nahi badla")
    for k in SECRET_KEYS:
        m = secret_re(k).search(cur)
        if not m:
            sys.exit(f"❌ VM file mein {k} nahi mila - kuch nahi badla")
        val = m.group(2)
        new, n = secret_re(k).subn(lambda mm, v=val: mm.group(1) + '"' + v + '"', new, count=1)
        if n != 1:
            sys.exit(f"❌ Naye code mein {k} ki line nahi mili - kuch nahi badla")
    for k in SECRET_KEYS:
        if secret_re(k).search(new).group(2) == "***":
            sys.exit(f"❌ {k} abhi bhi '***' hai - kuch nahi badla")
    inc = os.path.join(DIR, "deploy_incoming"); os.makedirs(inc, exist_ok=True)
    stg = os.path.join(inc, "delta_btc_LIVE.py")
    open(stg, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(stg, doraise=True)
    except Exception as e:
        sys.exit(f"❌ Naya code compile nahi hua ({e}) - kuch nahi badla")
    code = ("import importlib.util,sys;s=importlib.util.spec_from_file_location('t',sys.argv[1]);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "print('OK', m.CONFIG.RISK_RUPEES, m.CONFIG.MAX_TRADES_DAY, m.CONFIG.ENTRY_TFS, m.CONFIG.POLL_SECONDS)")
    r = subprocess.run([sys.executable, "-c", code, stg], capture_output=True, text=True, timeout=90, cwd=DIR)
    if r.returncode != 0 or "OK" not in (r.stdout or ""):
        sys.exit("❌ Naya version load nahi hua - kuch nahi badla:\n" + (r.stderr or r.stdout or "")[-500:])
    say("✅ Naya code check PASS: " + r.stdout.strip().splitlines()[-1])
    fix_unit()
    bk = os.path.join(DIR, "deploy_backups"); os.makedirs(bk, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    bname = f"delta_btc_LIVE.py.{stamp}.bak"
    shutil.copy2(BOT, os.path.join(bk, bname))
    tmp = BOT + ".new"; shutil.copy2(stg, tmp); shutil.copymode(os.path.join(bk, bname), tmp); os.replace(tmp, BOT)
    det = ("PRO v2: SL har 0.5s, 1/5/15/30 min, Telegram turant, late-press 3s, ⏰ button time + countdown + ping, "
           "Custom risk, candle-time check")
    with open(os.path.join(DIR, "change_log.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": time.strftime("%d-%m-%Y %H:%M:%S", ist()), "what": "DEPLOY",
                            "detail": det + f" (backup {bname})"}, ensure_ascii=False) + "\n")
    json.dump({"file": "delta_btc_LIVE.py", "backup_name": bname, "applied_at": time.time(), "confirmed": False},
              open(os.path.join(DIR, ".deploy_pending.json"), "w", encoding="utf-8"))
    json.dump({"what": "DEPLOY", "detail": det, "time": time.strftime("%H:%M:%S", ist())},
              open(os.path.join(DIR, ".control_last.json"), "w", encoding="utf-8"), ensure_ascii=False)
    say(f"✅ File badli. Backup: {bk}/{bname}")
    subprocess.run(["sudo", "systemctl", "restart", "delta-live"])
    say("🔄 delta-live restart... 20 sec check (bot baar baar gir to nahi raha)")
    def _pid():
        return subprocess.run(["systemctl", "show", "delta-live", "-p", "MainPID", "--value"],
                              capture_output=True, text=True).stdout.strip()
    time.sleep(8); p1 = _pid(); time.sleep(12); p2 = _pid()
    st = subprocess.run(["systemctl", "is-active", "delta-live"], capture_output=True, text=True).stdout.strip()
    if st == "active" and (p1 != p2 or p2 in ("", "0")):
        st = "baar-baar restart"
    if st != "active":
        shutil.copy2(os.path.join(bk, bname), BOT + ".new"); os.replace(BOT + ".new", BOT)
        try: os.remove(os.path.join(DIR, ".deploy_pending.json"))
        except Exception: pass
        subprocess.run(["sudo", "systemctl", "restart", "delta-live"])
        sys.exit(f"🛑 Naya version chala nahi ({st}) - PURANA wapas laga diya. Claude ko batao "
                 f"(bot khud ka log: ~/deltabot/delta_bot.log)")
    say("✅ delta-live chal raha hai. Delta Telegram bot pe '✅ BADLAV LAGA' aur naye 1/5/15/30 button aayenge.")
    say("   Gadbad lage to Delta Telegram bot pe ⏪ rollback.")


if __name__ == "__main__":
    main()
