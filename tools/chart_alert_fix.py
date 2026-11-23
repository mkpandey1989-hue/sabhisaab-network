#!/usr/bin/env python3
"""chart_alert_fix.py  (Claude, 17 Nov 2026; v2: memory seema 500 MB) - Nifty chart ke faltu phone message band.

Sirf ~/nifty_chart/chart_server.py ke MESSAGE wale hisse badalta hai. Chart ka data/feed/trade/bot - kuch NAHI chhedta.
1) Memory message: pehle 260 MB par HAR GHANTE aata tha (chart ka normal 260-290 MB hai). Ab sirf 285+ MB par, din mein 1 baar.
2) Raat 03:00 (bazaar band, koi browser khula nahi, memory 200+ MB) chart khud chupchap restart -> din bhar memory kam rahe.
   (systemd Restart=always 5 sec mein wapas chalu karta hai - bot nifty-live ko koi asar nahi.)
3) Subah 08:00 health report: sirf tab jab koi gadbad ho (sab theek = message nahi). Shaam 20:00 report waisa hi (trend ke saath).
4) 'pehle se khabar' (Oracle maintenance waghera): ek hi baat din mein 1 baar, baar baar nahi.
v2 (owner: '500 MB kar do, auto-safai bhi rakho'): nifty-chart.service MemoryMax 300M -> 500M (VM mein 1.5 GB+ khali ho tabhi),
   message 475+ MB par, raat 03:00 safai 300+ MB par. Pehle v1 chala chuke ho to bhi ye dobara chala sakte ho.
Backup: chart_server.py.bak_alertfix_<samay>. Wapas: cp <backup> chart_server.py && sudo systemctl restart nifty-chart
"""
import os
import py_compile
import shutil
import subprocess
import sys
import time

F = os.path.expanduser("~/nifty_chart/chart_server.py")
MARK = "# alertfix v1 (17 Nov 2026)"

R = [
    # 1) memory alert
    ('            if d.get("chart_mb", 0) >= 260 and can("mem", 60):\n'
     '                await ALERTS._ntfy(f"Chart service {d[\'chart_mb\']} MB memory le rahi hai (limit 300). Zarurat padi to khud restart hogi.")\n',
     '            ' + MARK + ': 285+ MB par hi, din mein 1 baar (260-290 normal hai)\n'
     '            if d.get("chart_mb", 0) >= 285 and can("mem", 1440):\n'
     '                await ALERTS._ntfy(f"Chart service {d[\'chart_mb\']} MB memory le rahi hai (limit 300). Zarurat padi to khud restart hogi.")\n'
     '            # raat 03:00: bazaar band + koi browser nahi + 200+ MB -> chupchap restart (systemd 5 sec mein wapas)\n'
     '            if (hm_to_sec("03:00") <= tod < hm_to_sec("03:05") and d.get("chart_mb", 0) >= 200 and not APP.clients\n'
     '                    and time.time() - START_TS > 3600):\n'
     '                log(f"raat ki safai restart (memory {d.get(\'chart_mb\')} MB)")\n'
     '                os._exit(0)\n'),
    # 3) subah report sirf gadbad par
    ('    await ALERTS._ntfy("\\n".join(lines), title=f"Nifty VM health {when}", prio="default")\n'
     '    for a in alerts:\n'
     '        await ALERTS._ntfy(a, title="Nifty: pehle se khabar", prio="high")\n',
     '    ' + MARK + ': Subah report sirf gadbad par; ek khabar din mein 1 baar\n'
     '    if when != "Subah" or warn or alerts:\n'
     '        await ALERTS._ntfy("\\n".join(lines), title=f"Nifty VM health {when}", prio="default")\n'
     '    for a in alerts:\n'
     '        if _deep_once(a):\n'
     '            await ALERTS._ntfy(a, title="Nifty: pehle se khabar", prio="high")\n'),
    # 4) startup deep alert bhi din mein 1 baar
    ('                for a in al:\n'
     '                    if can("deep:" + a[:40], 360):\n',
     '                for a in al:\n'
     '                    if can("deep:" + a[:40], 360) and _deep_once(a):\n'),
    # helper
    ('async def health_report(when):\n',
     '_DEEP_SENT = {}\n\n\n'
     'def _deep_once(a):\n'
     '    ' + MARK + '\n'
     '    k, day = a[:60], date_txt(ct_now())\n'
     '    if _DEEP_SENT.get(k) == day:\n'
     '        return False\n'
     '    _DEEP_SENT[k] = day\n'
     '    return True\n\n\n'
     'async def health_report(when):\n'),
]


V2 = [
    ('if d.get("chart_mb", 0) >= 285 and can("mem", 1440):', 'if d.get("chart_mb", 0) >= 475 and can("mem", 1440):'),
    ("285+ MB par hi, din mein 1 baar (260-290 normal hai)", "475+ MB par hi, din mein 1 baar (seema 500 MB - v2)"),
    ('d.get("chart_mb", 0) >= 200 and not APP.clients', 'd.get("chart_mb", 0) >= 300 and not APP.clients'),
    ("MB memory le rahi hai (limit 300)", "MB memory le rahi hai (limit 500)"),
    ("MB (limit 300) | chal raha", "MB (limit 500) | chal raha"),
]
UNIT = "/etc/systemd/system/nifty-chart.service"


def set_unit_500():
    """MemoryMax 300M -> 500M (sirf jab VM mein 1500 MB+ khali). -> ab ki seema (MB) ya None"""
    try:
        u = open(UNIT).read()
    except Exception:
        print("⚠️ nifty-chart.service nahi mili - seema nahi badli")
        return None
    if "MemoryMax=500M" in u:
        print("ℹ️ Seema pehle se 500 MB")
        return 500
    if "MemoryMax=300M" not in u:
        print("⚠️ Unit mein MemoryMax=300M nahi mila - seema nahi badli")
        return None
    av = 0
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable:"):
            av = int(line.split()[1]) // 1024
    if av < 1500:
        print(f"⚠️ VM mein sirf {av} MB khali - bot ki hifazat ke liye seema 300 MB hi rakhi")
        return 300
    bk = "/home/ubuntu/unit_backups"
    os.makedirs(bk, exist_ok=True)
    subprocess.run(["sudo", "cp", "-a", UNIT, f"{bk}/nifty-chart.service.{time.strftime('%Y%m%d_%H%M%S')}"])
    r = subprocess.run(["sudo", "sed", "-i", "s/^MemoryMax=300M$/MemoryMax=500M/", UNIT])
    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    if r.returncode == 0 and "MemoryMax=500M" in open(UNIT).read():
        print(f"✅ Chart memory seema 300 -> 500 MB (VM mein {av} MB khali tha). Backup: {bk}")
        return 500
    print("⚠️ Seema badal nahi payi - 300 MB hi hai")
    return 300


def main():
    if not os.path.exists(F):
        sys.exit(f"❌ {F} nahi mila - kuch nahi badla")
    src = open(F, encoding="utf-8").read()
    new = src
    if MARK not in src:
        for old, rep in R:
            if new.count(old) != 1:
                sys.exit("❌ Code wahi nahi mila jo socha tha (shayad file badli hai) - KUCH NAHI badla. Claude ko batao.")
            new = new.replace(old, rep)
    lim = set_unit_500()
    if lim == 500:
        for a, b in V2:
            new = new.replace(a, b)
    if new == src:
        print("ℹ️ chart_server.py pehle se theek - kuch nahi badla.")
        restart_maybe()
        return
    bk = F + ".bak_alertfix_" + time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(F, bk)
    tmp = F + ".new"
    open(tmp, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(tmp, doraise=True)
    except Exception as e:
        os.remove(tmp)
        sys.exit(f"❌ Naya code compile nahi hua ({e}) - KUCH NAHI badla.")
    os.replace(tmp, F)
    shutil.copymode(bk, F)
    print("✅ chart_server.py badla. Backup:", bk)
    restart_maybe()
    print("Wapas purana: cp", bk, F, "&& sudo systemctl restart nifty-chart")


def restart_maybe():
    ist = time.gmtime(time.time() + 19800)
    hm = ist.tm_hour * 60 + ist.tm_min
    market = ist.tm_wday < 5 and 9 * 60 <= hm < 15 * 60 + 45
    if market:
        print("⏸️ Abhi bazaar khula hai - chart restart NAHI kiya. Badlav raat ko lagega; ya 3:45 ke baad chalao:")
        print("   sudo systemctl restart nifty-chart")
    else:
        subprocess.run(["sudo", "systemctl", "restart", "nifty-chart"])
        time.sleep(8)
        st = subprocess.run(["systemctl", "is-active", "nifty-chart"], capture_output=True, text=True).stdout.strip()
        print("🔄 chart restart:", st, "(bot nifty-live ko chhua nahi)")
    out = subprocess.run(["systemctl", "show", "nifty-chart", "-p", "MemoryMax", "--value"], capture_output=True, text=True).stdout.strip()
    if out.isdigit():
        print("   Chart memory seema ab:", int(out) // 1048576, "MB")


if __name__ == "__main__":
    main()
