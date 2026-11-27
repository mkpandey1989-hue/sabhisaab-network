#!/usr/bin/env python3
"""paper_reset.py (Claude, 27 Nov 2026) - SIRF PAPER: aaj ka KILL hatao + fund fresh + PAPER TEST ON (dono bot).

Nifty: paper balance Rs 1,00,00,000 | Delta: demo $10,00,000
Aaj ka trade-count / net / kill = 0 (Excel journal ka purana data waisa hi rehta hai).
paper_test.txt = ON -> kill OFF + unlimited trade (sirf paper; LIVE mein apne aap band).

Safety: bot LIVE ho to KUCH NAHI chhedta. Trade/ARMED chal raha ho (ya dashboard padh na paye) to kuch nahi.
Paper day-state ka backup bana ke, bot band -> file -> bot chalu (bot chalte hue file badlo to bot purana likh deta).
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

HOME = "/home/ubuntu"
BOTS = [
    {"name": "Nifty", "dir": HOME, "svc": "nifty-live", "state": "option_day_state_paper.json", "port": 8001,
     "pw": "dashboard_pass.txt", "bal": 10000000.0, "cur": "Rs"},
    {"name": "Delta", "dir": os.path.join(HOME, "deltabot"), "svc": "delta-live", "state": "delta_day_state_paper.json",
     "port": 8002, "pw": "delta_dashboard_pass.txt", "bal": 1000000.0, "cur": "$"},
]


def say(x): print(x, flush=True)


def ist(): return time.gmtime(time.time() + 19800)


def state(b):
    pw = ""
    try: pw = open(os.path.join(b["dir"], b["pw"]), encoding="utf-8").read().strip()
    except Exception: pass
    try:
        rq = urllib.request.Request(f"http://127.0.0.1:{b['port']}/state")
        if pw: rq.add_header("Authorization", "Basic " + base64.b64encode(f"u:{pw}".encode()).decode())
        with urllib.request.urlopen(rq, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"_err": str(e)}


def pid(svc):
    return subprocess.run(["systemctl", "show", svc, "-p", "MainPID", "--value"], capture_output=True, text=True).stdout.strip()


def do(b):
    say(f"\n===== {b['name']} =====")
    d = b["dir"]
    try: live = open(os.path.join(d, "live_mode.txt"), encoding="utf-8").read().strip().upper() == "LIVE"
    except Exception: live = False
    if live:
        say(f"⛔ {b['name']} LIVE mode mein hai - kuch nahi chheda (ye sirf paper ke liye hai)."); return False
    s = state(b)
    if "_err" in s:
        say(f"⏸️ {b['name']}: dashboard nahi padh paya ({s['_err']}) - pakka nahi ki trade nahi, kuch nahi chheda."); return False
    ph = str(s.get("phase", ""))
    if ph != "IDLE":
        say(f"⏸️ {b['name']}: bot abhi {ph} hai (trade/arm) - kuch nahi chheda. Trade band hone ke baad chalao."); return False
    if "LIVE" in str(s.get("mode", "")).upper() and "PAPER" not in str(s.get("mode", "")).upper():
        say(f"⛔ {b['name']}: dashboard LIVE bata raha - kuch nahi chheda."); return False
    sp = os.path.join(d, b["state"])
    bk = os.path.join(d, "deploy_backups"); os.makedirs(bk, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    if os.path.exists(sp): shutil.copy2(sp, os.path.join(bk, f"{b['state']}.{stamp}.bak"))
    new = {"date": time.strftime("%Y-%m-%d", ist()), "trades_today": 0, "trades": 0, "wins": 0, "losses": 0,
           "today_net": 0.0, "today_gross": 0.0, "today_charges": 0.0, "killed": False, "kill_reason": "",
           "balance": b["bal"], "sqoff_done": False, "morning_sent": True}
    subprocess.run(["sudo", "systemctl", "stop", b["svc"]])
    time.sleep(1.5)
    open(sp + ".tmp", "w", encoding="utf-8").write(json.dumps(new, sort_keys=True)); os.replace(sp + ".tmp", sp)
    open(os.path.join(d, "paper_test.txt"), "w").write("ON\n")
    with open(os.path.join(d, "change_log.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": time.strftime("%d-%m-%Y %H:%M:%S", ist()), "what": "PAPER RESET",
                            "detail": f"kill hataya, balance {b['cur']}{int(b['bal']):,}, aaj ka hisaab 0, PAPER TEST ON (SSH se)"},
                           ensure_ascii=False) + "\n")
    json.dump({"what": "PAPER RESET", "detail": f"kill OFF | balance {b['cur']}{int(b['bal']):,} | PAPER TEST ON",
               "time": time.strftime("%H:%M:%S", ist())},
              open(os.path.join(d, ".control_last.json"), "w", encoding="utf-8"), ensure_ascii=False)
    subprocess.run(["sudo", "systemctl", "start", b["svc"]])
    say(f"🔄 {b['name']} chalu... 20 sec check")
    time.sleep(8); p1 = pid(b["svc"]); time.sleep(12); p2 = pid(b["svc"])
    act = subprocess.run(["systemctl", "is-active", b["svc"]], capture_output=True, text=True).stdout.strip()
    if act != "active" or p1 != p2 or p2 in ("", "0"):
        say(f"🛑 {b['name']}: bot theek se chalu nahi hua ({act}) - 'sudo systemctl status {b['svc']}' dekho / Claude ko batao."); return False
    s2 = state(b)
    try: f = json.load(open(sp, encoding="utf-8"))
    except Exception: f = {}
    ok = (not f.get("killed")) and abs(float(f.get("balance", 0)) - b["bal"]) < 1 and int(f.get("trades_today", 9)) == 0
    say(f"{'✅' if ok else '⚠️'} {b['name']}: mode {s2.get('mode', '?')} | balance {b['cur']}{s2.get('balance', '?')} | "
        f"phase {s2.get('phase', '?')} | file: kill {'ON' if f.get('killed') else 'OFF'}, trade {f.get('trades_today')} | "
        f"PAPER TEST {'ON' if os.path.exists(os.path.join(d, 'paper_test.txt')) else 'OFF'}")
    return ok


def main():
    only = [a.lower() for a in sys.argv[1:] if not a.startswith("--")]
    res = [do(b) for b in BOTS if not only or b["name"].lower() in only]
    say("\n" + ("✅ DONO PAPER READY (kill OFF, fund fresh, unlimited test). Telegram pe 🔎 janch dabao."
                if res and all(res) else "⚠️ Upar dekho - jo nahi hua uski wajah likhi hai."))


if __name__ == "__main__":
    main()
