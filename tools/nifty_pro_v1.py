#!/usr/bin/env python3
"""nifty_pro_v1.py  (Claude, 27 Nov 2026) - Nifty LIVE bot ka PRO v1 (Manoj ne chuna: 1,2,3,9,11-19).

TRADE RULE SAME (1 trade/din, SL candle-LOW, risk/lock/kill wahi, 10s button window wahi). Sirf:
  tez SL check (1 Dhan call/tick), Telegram turant (long-poll + background), late-press grace 3s,
  button pe ⏰ close-time + countdown + 20s ping, ✏️ Custom risk, Excel EXIT row sahi,
  band candle timestamp se pakki, VM ghadi check.  +  nifty-live.service: token sirf tab bane jab 6 ghante purana.

Kya karta hai (sab check ke baad, warna KUCH NAHI badalta):
 1) Bazaar ka time (Som-Shukra 09:00-15:30) -> kuch nahi, baad mein chalao.
 2) Naya code PRIVATE repo vm-bots (branch claude/pro-v1) se VM ke apne GitHub token se laata hai.
 3) VM ki abhi wali file wahi honi chahiye jo aaj raat 02:40 GitHub pe gayi thi (secret chhod ke) -
    beech mein Telegram se kuch badla ho to RUKTA hai (aapka badlav nahi mitega).
 4) Asli token/chat id/ntfy topic VM ki file se naye code mein (GitHub pe '***' hi rehta hai).
 5) compile + load test -> backup ~/deploy_backups (⏪ rollback button isi se purana laata hai)
    -> .deploy_pending.json (naya version na chala to ntfy_monitor khud purana laga dega).
 6) nifty-live.service ExecStartPre fix (backup ~/unit_backups) -> restart -> 25s baad check.
Wapas purana: Telegram pe ⏪ rollback  (ya: cp ~/deploy_backups/<backup> ~/nifty_option_LIVE.py && sudo systemctl restart nifty-live)
"""
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
BOT = os.path.join(HOME, "nifty_option_LIVE.py")
REPO = "mkpandey1989-hue/vm-bots"
BRANCH = "claude/pro-v1"
BASE_SHA256 = "2428fcf81e3953bc5072ba17e2e01c07c7838c54f82b70184986b792286f1735"   # 27-Nov 02:40 wali file ('***' ke saath)
MARK = "PRO-1 (27-Nov-2026)"
SECRET_KEYS = ("DHAN_CLIENT_ID", "TG_BOT_TOKEN", "TG_CHAT_ID", "NTFY_TOPIC")
UNIT = "/etc/systemd/system/nifty-live.service"
OLD_PRE = "ExecStartPre=-/usr/bin/python3 /home/ubuntu/refresh_token.py"
NEW_PRE = ("ExecStartPre=-/bin/sh -c 'if [ -n \"$$(find /home/ubuntu/dhan_token.txt -mmin -360 2>/dev/null)\" ]; "
           "then echo \"token taaza (6 ghante se kam) - refresh skip\"; else /usr/bin/python3 /home/ubuntu/refresh_token.py; fi'")


def say(x): print(x, flush=True)


def ist():
    return time.gmtime(time.time() + 19800)


def market_time():
    t = ist(); hm = t.tm_hour * 60 + t.tm_min
    return t.tm_wday < 5 and 9 * 60 <= hm < 15 * 60 + 30


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
    url = f"https://api.github.com/repos/{REPO}/contents/home/nifty_option_LIVE.py?ref={BRANCH}"
    rq = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}",
                                              "Accept": "application/vnd.github.raw",
                                              "User-Agent": "nifty-pro-v1"})
    with urllib.request.urlopen(rq, timeout=60) as r:
        return r.read().decode("utf-8")


def secret_re(k):
    return re.compile(r'^(\s{4}' + k + r'\s*=\s*)"([^"\n]*)"', re.M)


def masked(text):
    for k in SECRET_KEYS:
        text = secret_re(k).sub(lambda m: m.group(1) + '"***"', text)
    return text.replace("\r\n", "\n")


def fix_unit():
    try:
        u = open(UNIT).read()
    except Exception:
        say("⚠️ nifty-live.service nahi mili - token wala fix (16) nahi laga"); return False
    if "refresh skip" in u:
        say("ℹ️ Service pehle se theek (token 6 ghante wala check laga hai)"); return True
    if OLD_PRE not in u:
        say("⚠️ Service mein purani ExecStartPre line nahi mili - fix 16 nahi laga (baaki sab chalega)"); return False
    if not os.path.exists(os.path.join(HOME, "dhan_token.txt")):
        say("⚠️ ~/dhan_token.txt nahi mili - fix 16 nahi laga"); return False
    bk = os.path.join(HOME, "unit_backups"); os.makedirs(bk, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    subprocess.run(["sudo", "cp", "-a", UNIT, f"{bk}/nifty-live.service.{stamp}"], check=False)
    tmp = f"/tmp/nifty-live.service.{stamp}"
    open(tmp, "w").write(u.replace(OLD_PRE, NEW_PRE))
    r = subprocess.run(["sudo", "cp", tmp, UNIT])
    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    ok = r.returncode == 0 and "refresh skip" in open(UNIT).read()
    say("✅ Service fix: restart pe token sirf tab banega jab 6 ghante se purana ho (8:45 cron wala hi chalega). "
        f"Backup: {bk}/nifty-live.service.{stamp}" if ok else "⚠️ Service fix nahi laga - purani line hi hai")
    return ok


def main():
    if market_time():
        sys.exit("⏸️ Abhi bazaar ka time hai (09:00-15:30) - KUCH NAHI badla. 15:30 ke baad ya subah 9 se pehle chalao.")
    if not os.path.exists(BOT):
        sys.exit(f"❌ {BOT} nahi mila - kuch nahi badla")
    cur = open(BOT, encoding="utf-8").read()
    if MARK in cur:
        say("ℹ️ Bot mein PRO v1 pehle se laga hai - file nahi chhedi.")
        fix_unit(); return
    h = hashlib.sha256(masked(cur).encode("utf-8")).hexdigest()
    if h != BASE_SHA256:
        sys.exit("🛑 VM ki nifty_option_LIVE.py aaj raat 02:40 ke baad BADLI hai (ya alag hai) - KUCH NAHI badla, "
                 "taaki aapka naya badlav na mite. Claude ko batao: 'pro script ruki - file badli hai'.")
    tok = gh_token()
    if not tok:
        sys.exit("❌ GitHub token nahi mila (~/sabhisaab-network/secrets/bot.env) - kuch nahi badla")
    try:
        new = fetch_new(tok)
    except Exception as e:
        sys.exit(f"❌ Naya code GitHub se nahi aaya ({e}) - kuch nahi badla")
    if MARK not in new:
        sys.exit("❌ GitHub wali file PRO v1 nahi lagti - kuch nahi badla")
    # asli secret VM file se naye code mein
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
    inc = os.path.join(HOME, "deploy_incoming"); os.makedirs(inc, exist_ok=True)
    stg = os.path.join(inc, "nifty_option_LIVE.py")
    open(stg, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(stg, doraise=True)
    except Exception as e:
        sys.exit(f"❌ Naya code compile nahi hua ({e}) - kuch nahi badla")
    code = ("import importlib.util,sys;s=importlib.util.spec_from_file_location('t',sys.argv[1]);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "print('OK', m.CONFIG.RISK_RUPEES, m.CONFIG.MAX_TRADES_DAY, m.CONFIG.ENTRY_WINDOW_SEC, m.CONFIG.LATE_GRACE_SEC)")
    r = subprocess.run([sys.executable, "-c", code, stg], capture_output=True, text=True, timeout=90, cwd=HOME)
    if r.returncode != 0 or "OK" not in (r.stdout or ""):
        sys.exit("❌ Naya version load nahi hua - kuch nahi badla:\n" + (r.stderr or r.stdout or "")[-500:])
    say("✅ Naya code check PASS: " + r.stdout.strip().splitlines()[-1])
    fix_unit()
    # backup (rollback button isi ko use karta hai) + markers
    bk = os.path.join(HOME, "deploy_backups"); os.makedirs(bk, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    bname = f"nifty_option_LIVE.py.{stamp}.bak"
    shutil.copy2(BOT, os.path.join(bk, bname))
    tmp = BOT + ".new"; shutil.copy2(stg, tmp); shutil.copymode(os.path.join(bk, bname), tmp); os.replace(tmp, BOT)
    now = time.strftime("%d-%m-%Y %H:%M:%S", ist())
    det = "PRO v1: tez SL check, Telegram turant, late-press 3s, ⏰ button time + countdown + ping, Custom risk, candle-time check"
    with open(os.path.join(HOME, "change_log.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": now, "what": "DEPLOY", "detail": det + f" (backup {bname})"}, ensure_ascii=False) + "\n")
    json.dump({"file": "nifty_option_LIVE.py", "backup": os.path.join(bk, bname), "backup_name": bname,
               "applied_at": time.time(), "confirmed": False},
              open(os.path.join(HOME, ".deploy_pending.json"), "w", encoding="utf-8"))
    json.dump({"what": "DEPLOY", "detail": det, "time": time.strftime("%H:%M:%S", ist())},
              open(os.path.join(HOME, ".control_last.json"), "w", encoding="utf-8"), ensure_ascii=False)
    say(f"✅ File badli. Backup: {bk}/{bname}")
    subprocess.run(["sudo", "systemctl", "restart", "nifty-live"])
    say("🔄 nifty-live restart... 25 sec check")
    time.sleep(25)
    st = subprocess.run(["systemctl", "is-active", "nifty-live"], capture_output=True, text=True).stdout.strip()
    if st != "active":
        shutil.copy2(os.path.join(bk, bname), BOT + ".new"); os.replace(BOT + ".new", BOT)
        try: os.remove(os.path.join(HOME, ".deploy_pending.json"))
        except Exception: pass
        subprocess.run(["sudo", "systemctl", "restart", "nifty-live"])
        sys.exit(f"🛑 Naya version chala nahi ({st}) - PURANA wapas laga diya. Claude ko batao: "
                 "journalctl -u nifty-live -n 40")
    say("✅ nifty-live chal raha hai. Telegram pe '✅ BADLAV LAGA' aur 90 sec baad 'DEPLOY PAKKA' aayega.")
    say("   Gadbad lage to Telegram pe ⏪ rollback.")


if __name__ == "__main__":
    main()
