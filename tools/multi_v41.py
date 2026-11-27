#!/usr/bin/env python3
"""multi_v41.py (Claude, 27 Nov 2026)

NIFTY BOT -> MULTI v4: Dhan pe jo naam chart pe dikhe wahi likho:
  airtel -> [Cash][Option][Future] | hcl option | dlf future | airtel cash | sensex | banknifty | crude | gold | nifty
  Option = buy call/put. Cash/Future/MCX = long + SHORT. Logic + risk same, ek waqt 1 trade.
  Liquidity (spread/depth), circuit, F&O ban check. '🔎 janch' = LIVE/PAPER + instrument (Telegram/dashboard/ntfy).
DELTA BOT -> v4.1: 🔎 janch button, 'gold' jaisa coin na ho to saaf jawab, dashboard pe coin.
DONO: ntfy notification pe [🔎 Janch] [❌ EXIT (2-step)] [📱 Dashboard] - Telegram band ho tab bhi.

Nifty: bazaar ke time (Som-Shukra 09:00-15:30) NAHI chhedta + trade/ARMED chal raha ho to bhi nahi.
Delta: trade/ARMED chal raha ho to nahi chhedta. Check, backup, compile, restart, 20s check, gire to purana wapas.
Wapas purana: Telegram pe ⏪ rollback.
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
REPO = "mkpandey1989-hue/vm-bots"
BRANCH = "claude/multi-v41"
MARKS = {"Nifty": "MULTI v4 (27-Nov-2026, Manoj): Dhan pe KOI BHI instrument", "Delta": "v4.1 (27-Nov-2026): NTFY CONTROL"}
BOTS = [
    {"name": "Nifty", "dir": HOME, "file": "nifty_option_LIVE.py", "repo_path": "home/nifty_option_LIVE.py",
     "svc": "nifty-live", "keys": ("DHAN_CLIENT_ID", "TG_BOT_TOKEN", "TG_CHAT_ID", "NTFY_TOPIC"),
     "base": ("300ed510da28af196769b8a01b2456c5f178c6fabc547bf28eecb39826e027c3", "6eb9f3eec08cbcfde2b9ff0ca894e98fca19d344369a569c2a7272b2c8f96446", "d209fe0a7ae94fd65134553d197fc6317e0bd927f75895f6ed1e1261e8ad7ded", "cbaee762be6216eb47c9aa44cecc8ad5271be0ca7fa6d01eb0be59c01d416a65"), "market": True,
     "port": 8001, "pw": "dashboard_pass.txt"},
    {"name": "Delta", "dir": os.path.join(HOME, "deltabot"), "file": "delta_btc_LIVE.py",
     "repo_path": "home/deltabot/delta_btc_LIVE.py", "svc": "delta-live", "keys": ("TG_CHAT_ID", "NTFY_TOPIC"),
     "base": ("b2126719c757689216e852f5e31a8ab59ecd5bd68eae6bd9d3d73e56693a09a0", "40a4688479d4ad55b22dfb941d9d4ba1093dc894abd7e6b68b9651a0e3eabc5f", "fd4bf5307911b220283fe5bad0baca3ca77e47dc67f45f712ef672ad9380679d", "90688e508d542de192ce5217beb175526e95b6210f1a44c6328d1971eb21e0b7", "1b0aa2c1d7e1cdc3eafe123af09e919ea69561b444ee417cd9eceaf240e96c20"), "market": False,
     "port": 8002, "pw": "delta_dashboard_pass.txt"},
]


def say(x): print(x, flush=True)


def ist(): return time.gmtime(time.time() + 19800)


def market_time():
    t = ist(); hm = t.tm_hour * 60 + t.tm_min
    return t.tm_wday < 5 and 9 * 60 <= hm < 15 * 60 + 30


def gh_token():
    try:
        for ln in open(os.path.join(HOME, "sabhisaab-network/secrets/bot.env"), encoding="utf-8"):
            if ln.startswith("GITHUB_TOKEN="):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return os.environ.get("GITHUB_TOKEN", "")


def fetch(tok, path):
    rq = urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}?ref={BRANCH}",
                                headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github.raw",
                                         "User-Agent": "multi-v41"})
    with urllib.request.urlopen(rq, timeout=60) as r:
        return r.read().decode("utf-8")


def secret_re(k):
    return re.compile(r'^(\s{4}' + k + r'\s*=\s*)"([^"\n]*)"', re.M)


def masked(text, keys):
    for k in keys:
        text = secret_re(k).sub(lambda m: m.group(1) + '"***"', text)
    return text.replace("\r\n", "\n")


def bot_busy(b):
    pw = ""
    try: pw = open(os.path.join(b["dir"], b["pw"]), encoding="utf-8").read().strip()
    except Exception: pass
    try:
        rq = urllib.request.Request(f"http://127.0.0.1:{b['port']}/state")
        if pw: rq.add_header("Authorization", "Basic " + base64.b64encode(f"u:{pw}".encode()).decode())
        with urllib.request.urlopen(rq, timeout=5) as r:
            ph = str(json.loads(r.read().decode("utf-8")).get("phase", ""))
        return (ph in ("ACTIVE", "PENDING_FILL", "ARMED", "EXIT_PENDING")), ph
    except Exception as e:
        return None, f"dashboard nahi padh paya ({e})"


def do_bot(b, tok, force):
    path = os.path.join(b["dir"], b["file"])
    say(f"\n===== {b['name']} =====")
    if not os.path.exists(path):
        say(f"❌ {path} nahi mila - {b['name']} nahi chheda"); return False
    cur = open(path, encoding="utf-8").read()
    MARK = MARKS[b["name"]]
    if MARK in cur:
        say(f"ℹ️ {b['name']}: naya version pehle se laga hai - nahi chheda"); return True
    if b["market"] and market_time():
        say(f"⏸️ {b['name']}: bazaar ka time (09:00-15:30) - nahi chheda. 15:30 ke baad dobara chalao."); return False
    if True:
        busy, why = bot_busy(b)
        if busy or (busy is None and not force):
            say(f"⏸️ {b['name']}: {why if busy is None else 'bot abhi ' + why + ' hai'} - nahi chheda. "
                f"Trade/arm na ho to dobara chalao (dashboard na padhe to aakhir mein --force)."); return False
    if hashlib.sha256(masked(cur, b["keys"]).encode("utf-8")).hexdigest() not in b["base"]:
        say(f"🛑 {b['name']}: file aaj wali (v3.2 / v4) nahi hai ya baad mein badli - nahi chheda. Claude ko batao."); return False
    try:
        new = fetch(tok, b["repo_path"])
    except Exception as e:
        say(f"❌ {b['name']}: GitHub se nahi aaya ({e}) - nahi chheda"); return False
    if MARK not in new:
        say(f"❌ {b['name']}: GitHub file naya version nahi - nahi chheda"); return False
    for k in b["keys"]:
        m = secret_re(k).search(cur)
        if not m: say(f"❌ {b['name']}: {k} nahi mila - nahi chheda"); return False
        new, n = secret_re(k).subn(lambda mm, v=m.group(2): mm.group(1) + '"' + v + '"', new, count=1)
        if n != 1 or secret_re(k).search(new).group(2) == "***":
            say(f"❌ {b['name']}: {k} naye code mein nahi laga - nahi chheda"); return False
    inc = os.path.join(b["dir"], "deploy_incoming"); os.makedirs(inc, exist_ok=True)
    stg = os.path.join(inc, b["file"]); open(stg, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(stg, doraise=True)
    except Exception as e:
        say(f"❌ {b['name']}: compile fail ({e}) - nahi chheda"); return False
    code = ("import importlib.util,sys;s=importlib.util.spec_from_file_location('t',sys.argv[1]);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print('OK', m.CONFIG.MAX_TRADES_DAY, m.CONFIG.ENTRY_TFS)")
    r = subprocess.run([sys.executable, "-c", code, stg], capture_output=True, text=True, timeout=90, cwd=b["dir"])
    if r.returncode != 0 or "OK" not in (r.stdout or ""):
        say(f"❌ {b['name']}: load fail - nahi chheda:\n" + (r.stderr or r.stdout or "")[-400:]); return False
    say(f"✅ {b['name']}: naya code check PASS")
    bk = os.path.join(b["dir"], "deploy_backups"); os.makedirs(bk, exist_ok=True)
    bname = f"{b['file']}.{time.strftime('%Y%m%d_%H%M%S')}.bak"
    shutil.copy2(path, os.path.join(bk, bname))
    shutil.copy2(stg, path + ".new"); shutil.copymode(os.path.join(bk, bname), path + ".new"); os.replace(path + ".new", path)
    det = ("MULTI v4: koi bhi instrument (naam likho) + long/short + liquidity/ban/circuit + janch + ntfy button"
           if b["name"] == "Nifty" else "v4.1: janch button + saaf 'coin nahi mila' + ntfy button (Janch/EXIT/Dashboard)")
    with open(os.path.join(b["dir"], "change_log.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": time.strftime("%d-%m-%Y %H:%M:%S", ist()), "what": "DEPLOY",
                            "detail": det + f" (backup {bname})"}, ensure_ascii=False) + "\n")
    json.dump({"file": b["file"], "backup": os.path.join(bk, bname), "backup_name": bname, "applied_at": time.time(),
               "confirmed": False}, open(os.path.join(b["dir"], ".deploy_pending.json"), "w", encoding="utf-8"))
    json.dump({"what": "DEPLOY", "detail": det, "time": time.strftime("%H:%M:%S", ist())},
              open(os.path.join(b["dir"], ".control_last.json"), "w", encoding="utf-8"), ensure_ascii=False)
    say(f"✅ {b['name']}: file badli. Backup: {bk}/{bname}")
    subprocess.run(["sudo", "systemctl", "restart", b["svc"]])
    def _pid():
        return subprocess.run(["systemctl", "show", b["svc"], "-p", "MainPID", "--value"],
                              capture_output=True, text=True).stdout.strip()
    time.sleep(8); p1 = _pid(); time.sleep(12); p2 = _pid()
    st = subprocess.run(["systemctl", "is-active", b["svc"]], capture_output=True, text=True).stdout.strip()
    if st == "active" and (p1 != p2 or p2 in ("", "0")): st = "baar-baar restart"
    if st != "active":
        shutil.copy2(os.path.join(bk, bname), path + ".new"); os.replace(path + ".new", path)
        try: os.remove(os.path.join(b["dir"], ".deploy_pending.json"))
        except Exception: pass
        subprocess.run(["sudo", "systemctl", "restart", b["svc"]])
        say(f"🛑 {b['name']}: naya version chala nahi ({st}) - PURANA wapas laga diya. Claude ko batao."); return False
    say(f"✅ {b['name']}: chal raha hai. Telegram pe '🔎 janch' dabao." + ("  Phir likho: airtel / hcl option / dlf future / sensex / crude / nifty" if b["name"] == "Nifty" else ""))
    return True


def main():
    force = "--force" in sys.argv
    tok = gh_token()
    if not tok: sys.exit("❌ GitHub token nahi mila (~/sabhisaab-network/secrets/bot.env) - kuch nahi badla")
    only = [a.lower() for a in sys.argv[1:] if not a.startswith("--")]
    res = [do_bot(b, tok, force) for b in BOTS if not only or b["name"].lower() in only]
    if not res: sys.exit("❌ 'nifty' ya 'delta' likho (ya kuch nahi = dono) - kuch nahi badla")
    say("\n" + ("✅ DONO HO GAYE." if all(res) else "⚠️ Upar dekho - jo nahi hua uski wajah likhi hai."))


if __name__ == "__main__":
    main()
