#!/usr/bin/env python3
"""delta_multi_v4.py  (Claude, 27 Nov 2026) - Delta bot: KAI SYMBOL + LIQUIDITY + $10 lakh demo.

TRADE RULE SAME (SL candle LOW/HIGH, qty = R se, lock/trail/add-on, exchange stop). EK WAQT 1 HI TRADE.
 * Telegram: 'eth' / 'symbol sol' / 'long xrp 5' / 'short gold 15' -> wahi coin active (patla coin activate nahi).
   'symbols' = saari list. Coin yaad rehta hai (restart ke baad bhi).
 * Entry se pehle LIQUIDITY: spread > 0.15% ya SL-doori ka 25% -> skip; orderbook mein qty kam -> qty kam.
 * Har coin ka apna lot/tick/fees/max-leverage Delta se; chhote coin ke price ke decimal sahi.
 * Paper (demo) fund $10,00,000 (paper day-state ka balance bhi $10 lakh kar deta hai; LIVE file nahi chhedta).
 * Excel mein naya 'symbol' column (purana Excel apne aap alag naam se rakh diya jaata hai).
Pehle v2/v3/v3.1/v3.2 koi bhi laga ho - chalega. Trade/ARMED chal raha ho to ruk jaata hai.
Wapas purana: Delta Telegram pe ⏪ rollback
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
BRANCH = "claude/delta-multi-v4"
BASE_SHA256 = ("40a4688479d4ad55b22dfb941d9d4ba1093dc894abd7e6b68b9651a0e3eabc5f", "90688e508d542de192ce5217beb175526e95b6210f1a44c6328d1971eb21e0b7", "1b0aa2c1d7e1cdc3eafe123af09e919ea69561b444ee417cd9eceaf240e96c20", "fd4bf5307911b220283fe5bad0baca3ca77e47dc67f45f712ef672ad9380679d")   # v3.2 / v3.1 / v3 / v2
MARK = "MULTI v4 (27-Nov-2026): kai symbol + LIQUIDITY check"
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
                                              "User-Agent": "delta-multi-v4"})
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
        say("ℹ️ Delta bot mein MULTI v4 pehle se laga hai - file nahi chhedi.")
        fix_unit(); return
    busy, why = bot_busy()
    if busy and not force:
        sys.exit(f"⏸️ {why} - KUCH NAHI badla. Trade band hone ke baad chalao.")
    if busy is None and not force:
        sys.exit(f"⏸️ {why} - pakka nahi ki trade nahi chal raha, isliye KUCH NAHI badla. "
                 f"Delta Telegram pe 'status' dekho; trade na ho to:  python3 /tmp/delta_pro_v2.py --force")
    h = hashlib.sha256(masked(cur).encode("utf-8")).hexdigest()
    if h not in BASE_SHA256:
        sys.exit("🛑 VM ki delta_btc_LIVE.py aaj wali (v2/v3/v3.1/v3.2) nahi hai - KUCH NAHI badla. "
                 "Claude ko batao: 'delta multi script ruki - file badli hai'.")
    tok = gh_token()
    if not tok:
        sys.exit("❌ GitHub token nahi mila (~/sabhisaab-network/secrets/bot.env) - kuch nahi badla")
    try:
        new = fetch_new(tok)
    except Exception as e:
        sys.exit(f"❌ Naya code GitHub se nahi aaya ({e}) - kuch nahi badla")
    if MARK not in new:
        sys.exit("❌ GitHub wali file MULTI v4 nahi lagti - kuch nahi badla")
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
            "print('OK', m.CONFIG.RISK_RUPEES, m.CONFIG.VIRTUAL_CAPITAL, m.CONFIG.ENTRY_TFS, m.CONFIG.MAX_SPREAD_PCT)")
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
    det = ("MULTI v4: kai symbol (eth/sol/...) ek waqt 1 trade, LIQUIDITY check (spread + orderbook), "
           "har coin ka lot/tick/lev, demo $10 lakh, Excel symbol column")
    # demo (paper) balance $10 lakh - sirf paper day-state (LIVE wali file nahi)
    try:
        sp = os.path.join(DIR, "delta_day_state_paper.json")
        d = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
        d["balance"] = 1000000.0
        open(sp + ".tmp", "w", encoding="utf-8").write(json.dumps(d, sort_keys=True)); os.replace(sp + ".tmp", sp)
        say("✅ Paper (demo) balance -> $1,000,000")
    except Exception as e:
        say(f"⚠️ Paper balance set nahi hua ({e}) - bot naye din se $10 lakh lega")
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
    say("✅ delta-live chal raha hai. Delta Telegram pe '✅ BADLAV LAGA'. Ab likho: eth  /  symbol sol  /  long xrp 5  /  symbols")
    say("   Gadbad lage to Delta Telegram bot pe ⏪ rollback.")


if __name__ == "__main__":
    main()
