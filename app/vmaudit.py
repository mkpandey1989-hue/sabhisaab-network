"""v2.1.1: POORE VM ka audit (postmortem) - SIRF PADHTA HAI, kuch nahi badalta/mitata/restart karta.

Kyun: 30 Oct ko VM ka data mit gaya, owner ne purane backup se (Gemini ki madad se) chalu kiya. Kya-kya laut aaya,
kya toota, kaun se login gaye, kaun se bot takra rahe, kahan kachra pada hai, suraksha mein kami - sab ek report mein.
Report sirf owner ke Telegram par (file). GitHub par NAHI (repo public hai; suraksha ki jaankari wahan nahi jaani chahiye).
Har token/secret chhupa: sirf 'fingerprint' (sha256 ke 8 akshar) - taaki dikhe ki do jagah EK hi token hai ya nahi.
Command: 'vm audit' (ya /audit).
"""
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import time
import requests

HOME = pathlib.Path("/home/ubuntu")
SKIP = ("/venv", "env/", "/.cache", "site-packages", "node_modules", "/.git/", "/tgapi", "/telegram-bot-api", "/.npm",
        "/.local/lib", "/__pycache__")
TRADING = ["nifty-live", "delta-live", "nifty-chart", "nifty-chart-watchdog"]
RX_TG = re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b")
RX_GEM = re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")
RX_ANY = re.compile(r"\d{8,10}:[A-Za-z0-9_-]{30,}|EAA[A-Za-z0-9]{30,}|TH[A-Za-z0-9]{40,}|AIza[0-9A-Za-z_-]{30,}|"
                    r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_\w{30,}|GOCSPX-[\w-]{20,}|pina_[A-Za-z0-9]{20,}|"
                    r"\bcf[a-z]{2,3}_[A-Za-z0-9._\-]{20,}|\b[0-9a-f]{40}\b|sk-[A-Za-z0-9_-]{20,}")


def sh(cmd, t=40):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return (r.stdout + (r.stderr if r.returncode else "")).strip()
    except Exception as e:
        return f"(nahi chala: {e})"


def fp(tok):
    return hashlib.sha256(tok.encode()).hexdigest()[:8]


def mask(t):
    t = RX_ANY.sub(lambda m: f"<chhupa:{fp(m.group())}>", t or "")
    t = re.sub(r"(https?://)[^/\s:@]+:[^/\s@]+@", r"\1<chhupa>@", t)
    t = re.sub(r"(?i)((?:token|secret|password|passwd|api_?key)\w*\s*[=:]\s*['\"]?)([^'\"\s,]{8,})", r"\1<chhupa>", t)
    return t


def _ok(p):
    return not any(s in str(p) for s in SKIP)


def _proj(path):
    parts = pathlib.Path(path).parts
    return parts[3] if path.startswith("/home/ubuntu/") and len(parts) > 3 else path


class Report:
    def __init__(self):
        self.F = []
        self.S = []

    def find(self, lvl, txt, fix=""):
        self.F.append((lvl, txt, fix))

    def sec(self, title, body):
        self.S.append(f"\n{'=' * 70}\n## {title}\n{'=' * 70}\n{mask(body)}")


def _units(all_=True):
    flag = "--all " if all_ else ""
    return sh(f"systemctl list-units --type=service {flag}--no-legend --no-pager --plain | awk '{{print $1}}'").split()


def _env_files():
    files = set()
    for u in _units():
        for part in sh(f"systemctl show {u} -p EnvironmentFiles --value").split():
            if part.startswith("/"):
                files.add(part)
    for pat in (".env", "*.env", "*.json", "*.cfg", "*.ini", "*.py", "*.txt"):
        for f in HOME.rglob(pat):
            try:
                low = str(f).lower()
                if (_ok(f) and f.is_file() and f.stat().st_size < 300_000 and
                        (pat in (".env", "*.env") or "secret" in low or "config" in f.name.lower() or "token" in f.name.lower())):
                    files.add(str(f))
            except Exception:
                pass
    return sorted(files)


def sec_system(R):
    b = []
    b.append("Samay: " + sh("date '+%Y-%m-%d %H:%M:%S %Z (%z)'") + " | UTC: " + sh("date -u '+%H:%M'"))
    tz = sh("timedatectl show -p Timezone --value")
    ntp = sh("timedatectl show -p NTPSynchronized --value")
    b.append(f"Timezone: {tz} | Ghadi sync (NTP): {ntp}")
    if ntp.strip() != "yes":
        R.find("🟡", "VM ki ghadi internet se sync nahi (NTP) - samay galat ho sakta hai", "sudo timedatectl set-ntp true")
    try:
        from .config import IST
        b.append("Bot ka IST samay: " + datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M"))
    except Exception:
        pass
    b.append("OS: " + sh("grep PRETTY_NAME /etc/os-release | cut -d= -f2") + " | Kernel: " + sh("uname -r"))
    b.append("Uptime: " + sh("uptime -p") + " | Load: " + sh("cat /proc/loadavg") + " | CPU: " + sh("nproc"))
    b.append(sh("free -m"))
    b.append(sh("df -h / 2>/dev/null"))
    b.append("Inodes: " + sh("df -i / | tail -1"))
    pct = sh("df --output=pcent / | tail -1").strip().rstrip("%")
    if pct.isdigit() and int(pct) >= 80:
        R.find("🔴", f"Disk {pct}% bhari", "Section 6 (kachra) dekhein")
    elif pct.isdigit() and int(pct) >= 65:
        R.find("🟡", f"Disk {pct}% bhari", "Section 6 (kachra) dekhein")
    avail = sh("free -m | awk '/Mem:/{print $7}'")
    if avail.isdigit() and int(avail) < 1200:
        R.find("🟡", f"RAM sirf {avail} MB khaali", "Section 1 ke bhaari process dekhein")
    sw = sh("free -m | awk '/Swap:/{print $2}'")
    if sw == "0":
        R.find("🟡", "Swap nahi hai - render ke waqt RAM bhari to Linux bot ko maar dega (OOM)", "4 GB swapfile (Claude se steps)")
    oom = sh("journalctl -k --since '-7 days' --no-pager 2>/dev/null | grep -ci 'out of memory\\|killed process'")
    b.append(f"OOM (RAM khatam, 7 din): {oom}")
    if oom.isdigit() and int(oom) > 0:
        R.find("🟡", f"7 din mein {oom} baar RAM khatam (OOM kill)", "journalctl -k | grep -i killed")
    if os.path.exists("/var/run/reboot-required"):
        R.find("🟡", "VM restart maang raha hai (kernel update)", "Bazaar band ke samay Oracle console se Reboot")
    up = sh("apt list --upgradable 2>/dev/null | grep -c upgradable")
    secu = sh("apt list --upgradable 2>/dev/null | grep -ci security")
    b.append(f"Update baaki: {up} (suraksha: {secu})")
    if secu.isdigit() and int(secu) > 0:
        R.find("🟡", f"{secu} suraksha update baaki", "sudo apt update && sudo apt upgrade -y (bazaar band ke samay)")
    b.append("Bhaari process (CPU):\n" + sh("ps -eo pid,user,pcpu,pmem,etime,cmd --sort=-pcpu | head -12 | cut -c1-170"))
    b.append("Bhaari process (RAM):\n" + sh("ps -eo pid,user,pcpu,pmem,etime,cmd --sort=-pmem | head -10 | cut -c1-170"))
    R.sec("1. SYSTEM (ghadi, RAM, disk, update)", "\n".join(b))


def sec_services(R):
    b = []
    failed = sh("systemctl list-units --type=service --state=failed --no-legend --no-pager --plain")
    b.append("FAILED service:\n" + (failed or "(koi nahi)"))
    for ln in failed.splitlines():
        name = (ln.split() or [""])[0]
        if not name.endswith(".service"):
            continue
        if name.startswith("run-"):
            R.find("🟡", f"Purana adhoora kaam '{name}' failed pada hai (kachra)", f"sudo systemctl reset-failed {name}")
        elif name:
            R.find("🔴", f"Service '{name}' FAILED", f"journalctl -u {name} -n 50")
    rows = []
    for u in _units():
        info = sh(f"systemctl show {u} -p ExecStart -p WorkingDirectory -p FragmentPath --value")
        if "/home/ubuntu" not in info:
            continue
        p = {k: sh(f"systemctl show {u} -p {k} --value") for k in
             ("ActiveState", "SubState", "NRestarts", "MemoryCurrent", "ActiveEnterTimestamp", "User", "UnitFileState")}
        ex = re.search(r"argv\[\]=([^;]+)", info)
        mem = int(p["MemoryCurrent"]) // 1048576 if p["MemoryCurrent"].isdigit() else "-"
        rows.append(f"- {u}: {p['ActiveState']}/{p['SubState']} | restarts {p['NRestarts']} | RAM {mem} MB | user "
                    f"{p['User'] or 'root'} | boot par: {p['UnitFileState']} | chalu se: {p['ActiveEnterTimestamp']}\n"
                    f"    {(ex.group(1).strip() if ex else info.splitlines()[0] if info else '')[:160]}")
        base = u.split(".")[0]
        if p["NRestarts"].isdigit() and int(p["NRestarts"]) >= 5:
            R.find("🟡", f"'{u}' {p['NRestarts']} baar khud restart hua (girta-uthta)", f"journalctl -u {u} -n 80")
        if p["ActiveState"] == "active" and p["UnitFileState"] not in ("enabled", "static", "enabled-runtime", "transient"):
            R.find("🟡", f"'{u}' chal raha hai par VM reboot par khud chalu NAHI hoga ({p['UnitFileState']})", f"sudo systemctl enable {u}")
        if p["ActiveState"] == "active" and not p["User"] and base not in TRADING and not u.startswith("run-"):
            R.find("🟡", f"'{u}' root ke roop mein chal raha (zaroorat se zyada taakat)", "User=ubuntu (Claude se)")
    b.append("\n/home/ubuntu wali saari service:\n" + "\n".join(rows))
    b.append("\nTimers:\n" + sh("systemctl list-timers --all --no-pager | head -25"))
    b.append("\nCron (ubuntu):\n" + sh("crontab -l 2>&1"))
    b.append("\nCron (root):\n" + sh("sudo -n crontab -l 2>&1"))
    b.append("\n/etc/cron.d:\n" + sh("ls -la /etc/cron.d"))
    R.sec("2. SERVICE, TIMER, CRON (kaun chal raha, kaun gira)", "\n".join(b))


def sec_bots(R):
    b = []
    where, gem = {}, {}
    for f in _env_files():
        try:
            txt = pathlib.Path(f).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in RX_TG.finditer(txt):
            where.setdefault(m.group(), set()).add(f)
        for m in RX_GEM.finditer(txt):
            gem.setdefault(m.group(), set()).add(f)
    for u in _units():
        env = sh(f"systemctl show {u} -p Environment --value")
        for m in RX_TG.finditer(env):
            where.setdefault(m.group(), set()).add(f"service:{u}")
        for m in RX_GEM.finditer(env):
            gem.setdefault(m.group(), set()).add(f"service:{u}")
    for tok, files in where.items():
        name, hook = "?", ""
        try:
            me = requests.get(f"https://api.telegram.org/bot{tok}/getMe", timeout=15).json()
            name = "@" + me["result"]["username"] if me.get("ok") else f"(token band: {me.get('description', '')[:40]})"
            if me.get("ok"):
                wh = requests.get(f"https://api.telegram.org/bot{tok}/getWebhookInfo", timeout=15).json().get("result", {})
                hook = (f" | webhook: {'HAAN' if wh.get('url') else 'nahi'} | atke sandesh: {wh.get('pending_update_count', 0)}")
                if wh.get("url"):
                    R.find("🔴", f"Bot {name} par webhook laga hai - polling wala program sandesh nahi paayega", "Claude se deleteWebhook")
                if (wh.get("pending_update_count") or 0) > 20:
                    R.find("🟡", f"Bot {name}: {wh['pending_update_count']} sandesh atke (koi nahi padh raha)", "us bot ki service dekhein")
        except Exception as e:
            name = f"(jaanch nahi: {str(e)[:50]})"
        projs = sorted({_proj(x) for x in files})
        b.append(f"- Telegram {name} [fp {fp(tok)}] → {', '.join(projs)}{hook}")
        if name.startswith("(token band"):
            R.find("🟡", f"Purana/band Telegram token pada hai [fp {fp(tok)}] in: {', '.join(projs)[:120]}",
                   "Wo project bekaar ho to hatayein (Claude se pooch kar)")
    b.append("\nGemini keys (kaun sa project kaun si key):")
    for k, files in gem.items():
        projs = sorted({_proj(x) for x in files})
        b.append(f"- Gemini key [fp {fp(k)}] → {', '.join(projs)}")
        if len(projs) > 1:
            R.find("🟡", f"EK hi Gemini key {len(projs)} jagah ({', '.join(projs)[:80]}) - free seema baant rahe (isliye 'Gemini busy')",
                   "Har bot ki alag key: aistudio.google.com/apikey (free)")
    c409 = {}
    for u in _units(False):
        n = sh(f"journalctl -u {u} --since '-3 days' --no-pager 2>/dev/null | grep -ci 'terminated by other getupdates\\|error_code.: 409\\| 409 '")
        if n.isdigit() and int(n) > 0:
            c409[u] = int(n)
    b.append("\n409 takraav (3 din, do program ek bot par): " + (json.dumps(c409) if c409 else "koi nahi"))
    for u, n in c409.items():
        R.find("🔴", f"'{u}' ke log mein {n} baar 409 - doosra program bhi isi bot token se sandesh le raha", "Upar list: kaun sa token 2 jagah")
    b.append("VM → Telegram seedha raasta: " + sh("curl -s -m 10 -o /dev/null -w '%{http_code}' https://api.telegram.org") + " (302/200 = theek)")
    R.sec("3. BOT (Telegram token, takraav, Gemini key)", "\n".join(b))


def sec_security(R):
    b = []
    lis = sh("ss -tlnpH 2>/dev/null")
    b.append("Khule port:\n" + lis)
    for ln in lis.splitlines():
        parts = ln.split()
        if len(parts) < 4:
            continue
        addr = parts[3]
        port = addr.rsplit(":", 1)[-1]
        dch = sh("sudo -n iptables -S CHOW_DASH 2>/dev/null")             # v2.1.9: Chowkidar ka dashboard firewall
        if port in ("8001", "8002", "8003") and "-j DROP" in dch and f"--dport {port}" not in dch:
            b.append(f"Port {port}: bahar se band (Chowkidar tunnel + firewall) ✅")
            continue
        if port in ("8001", "8002", "8003") and "hashlimit" in dch:
            R.find("🟢", f"Port {port} khula par Chowkidar shield (har IP par seema) laga - tunnel judte hi band", "Cloudflare token permission (PENDING)")
            continue
        if addr.split(":")[0] in ("0.0.0.0", "*", "[::]") and port != "22":
            proc = re.search(r'users:\(\("([^"]+)"', ln)
            R.find("🟡", f"Port {port} poori duniya ke liye khula ({proc.group(1) if proc else '?'})",
                   "Zaroori na ho to 127.0.0.1 par + Oracle Security List mein band")
    b.append("\nFirewall (ufw):\n" + sh("sudo -n ufw status verbose 2>&1 | head -30"))
    b.append("\nfail2ban:\n" + sh("sudo -n fail2ban-client status sshd 2>&1 | head -12"))
    sshd = sh("sudo -n sshd -T 2>/dev/null | grep -Ei '^(passwordauthentication|permitrootlogin|pubkeyauthentication|port|maxauthtries) '")
    b.append("\nSSH setting:\n" + sshd)
    if re.search(r"passwordauthentication yes", sshd):
        R.find("🔴", "SSH password se login khula (hacker password aazma sakte)", "PasswordAuthentication no (Claude se steps)")
    if re.search(r"permitrootlogin yes", sshd):
        R.find("🔴", "root seedha SSH se login kar sakta", "PermitRootLogin no")
    b.append("\nSSH keys:\n" + sh("for f in /home/*/.ssh/authorized_keys; do [ -f $f ] && echo \"$f: $(grep -c . $f) key\" && "
                                 "ssh-keygen -lf $f 2>/dev/null; done"))
    b.append("\nAakhri login:\n" + re.sub(r"(\d+\.\d+\.\d+)\.\d+", r"\1.x", sh("last -n 12 -a 2>/dev/null")))
    users = sh("awk -F: '$7 ~ /(bash|sh|zsh)$/ {print $1\" uid=\"$3}' /etc/passwd")
    b.append("\nShell wale user:\n" + users)
    for ln in users.splitlines():
        u = ln.split()[0]
        if u not in ("root", "ubuntu", "opc"):
            R.find("🔴", f"Anjaan user '{u}' jo login kar sakta", "Pehchaan na ho to turant Claude ko")
    b.append("\nsudo bina password:\n" + sh("sudo -n grep -rh NOPASSWD /etc/sudoers /etc/sudoers.d 2>/dev/null | grep -v '^#'"))
    tmpx = sh("find /tmp /dev/shm /var/tmp -maxdepth 3 -type f -perm -u+x 2>/dev/null | head -20")
    b.append("\n/tmp mein chalne wali file:\n" + (tmpx or "(koi nahi)"))
    if tmpx:
        R.find("🟡", "/tmp mein chalne layak file (aksar install ka kachra; kabhi malware)", "List Claude ko")
    for ln in sh("ps -eo pcpu,user,cmd --sort=-pcpu --no-headers | awk '$1>60' | head -5").splitlines():
        if not any(w in ln for w in ("ffmpeg", "python", "chrome", "node", "piper", "apt", "dpkg", "unattended")):
            R.find("🔴", f"Anjaan process zyada CPU: {ln[:120]}", "Pehchaan na ho to Claude ko (miner jaanch)")
    est = sh("ss -tnpH state established 2>/dev/null | awk '{print $4, $5}' | "
             "sed -E 's/users:\\(\\(\"([^\"]+)\".*/\\1/' | awk '{n=split($1,a,\":\"); ip=a[1]; for(i=2;i<n;i++) ip=ip\":\"a[i]; "
             "print $2\" -> \"ip}' | sort | uniq -c | sort -rn | head -25")
    b.append("\nAbhi kaun kahan juda (process -> IP):\n" + est)
    perm = []
    for f in _env_files():
        try:
            st = os.stat(f)
            if st.st_mode & 0o004 and RX_ANY.search(pathlib.Path(f).read_text(encoding="utf-8", errors="ignore")):
                perm.append(f"{oct(st.st_mode)[-3:]} {f}")
        except Exception:
            pass
    b.append("\nSecret wali file jo SAB padh sakte (o+r):\n" + ("\n".join(perm) or "(koi nahi)"))
    if perm:
        R.find("🟡", f"{len(perm)} secret wali file sabke liye padhne layak", "chmod 600 <file> (list section 4)")
    b.append("\nGit repo:")
    for g in sorted(set(HOME.glob("*/.git")) | set(HOME.glob("*/*/.git")) | set(HOME.glob("*/*/*/.git"))):   # v2.1.9: site_repo bhi
        repo = g.parent
        if not _ok(repo):
            continue
        rem = sh(f"git -C '{repo}' remote -v 2>/dev/null | head -1")
        if re.search(r"https://[^/\s]+@github", rem):
            R.find("🔴", f"{repo.name}: GitHub token git remote URL mein likha", "git remote set-url (Claude se)")
        leak = sh(f"git -C '{repo}' grep -lE '[0-9]{{8,10}}:[A-Za-z0-9_-]{{35}}|AIza[0-9A-Za-z_-]{{35}}|ghp_[A-Za-z0-9]{{30}}|"
                  f"EAA[A-Za-z0-9]{{40}}' 2>/dev/null | head -5")
        dirty = sh(f"git -C '{repo}' status --porcelain 2>/dev/null | wc -l")
        b.append(f"- {repo}: {mask(rem) or 'remote nahi'} | badle file: {dirty} | secret wali tracked file: {leak or 'koi nahi'}")
        if leak and "github.com" in rem:
            R.find("🔴", f"{repo.name}: git mein secret wali file ({leak.splitlines()[0]}) - push hui to duniya dekhegi",
                   "Token badlein + file .gitignore mein (Claude se)")
    R.sec("4. SURAKSHA (port, SSH, user, process, secret file, git)", "\n".join(b))


def sec_sabhinet(R):
    from . import state
    from .config import BASE, BRANDS, SECRETS, DATA
    b = ["Version: " + (BASE / "VERSION").read_text().strip(),
         "Service: " + sh("systemctl is-active sabhinet") + " | chalu se: " + sh("systemctl show sabhinet -p ActiveEnterTimestamp --value")]
    try:
        from . import youtube, meta as M, threads as TH, pinterest as PI, analytics as AN
        for bk, v in BRANDS.items():
            yt = youtube.has_login(bk)
            ok_, ch = youtube.channel_ok(bk) if yt else (False, "")
            th = TH.info(bk)
            tok, why = TH.alive(bk, max_age=0) if th else (False, "")
            mi = M.brand_info(bk) if M.has_token() else None
            b.append(f"- {v['name']}: YouTube {('✅ ' + str(ch)) if ok_ else (('⛔ ' + str(ch)) if yt else '🔑 login nahi')} | "
                     f"FB {'✅' if mi else '❌'} IG {('✅ @' + mi['ig_user']) if mi and mi.get('ig_user') else '❌'} | "
                     f"Threads {'✅' if th and tok else (('🔴 ' + why[:60]) if th else '🔑')} | GA {'✅' if AN.has(bk) else '🔑'}")
            if th and not tok:
                R.find("🔴", f"{v['name']} Threads token khatam ({why[:50]})", "Meta developer → naya Threads token → bot chat mein paste")
            if not yt:
                R.find("🔴", f"{v['name']} YouTube login nahi", "bot: /login")
            elif not ok_:
                R.find("🔴", f"{v['name']} YouTube login toota ({ch})", "bot: /login")
            if M.has_token() and not mi:
                R.find("🔴", f"{v['name']} Facebook/Instagram nahi jud raha", "bot: /meta")
        if M.has_token() and M._cfg().get("secret_bad"):
            R.find("🔴", "Meta App Secret galat", "bot: 'meta secret <secret>'")
        ps = PI.status()
        b.append(f"Pinterest: app_id {PI.app_id()} | env {ps['env']} | login {ps['oauth']} | live {ps['live']} | secret {ps['secret']}")
        if not ps["oauth"]:
            R.find("🔴", "Pinterest login (OAuth) nahi - manzoori ke baad bhi pins public nahi", "bot: /pinterest → Allow → address bot ko")
    except Exception as e:
        b.append(f"Connection jaanch galti: {e}")
    try:
        from .website import _cf
        tok, acc = _cf()
        b.append(f"Cloudflare: token {'haan' if tok else 'NAHI'} | account ID {len(acc or '')} akshar")
        if acc and not re.fullmatch(r"[0-9a-f]{32}", acc):
            R.find("🔴", f"Cloudflare Account ID galat ({len(acc)} akshar, 32 chahiye) - relay/deploy/AI nahi chalega",
                   "bot: 'cf account <sahi 32 akshar>'")
        if tok:
            v = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", timeout=20,
                             headers={"Authorization": f"Bearer {tok}"}).json()
            st = (v.get("result") or {}).get("status")
            b.append(f"Cloudflare token: {st or str(v.get('errors'))[:100]}")
            if st != "active":
                R.find("🔴", f"Cloudflare token kaam nahi kar raha ({st})", "Roll → bot: 'cf token <naya>'")
            if acc:
                a = requests.get(f"https://api.cloudflare.com/client/v4/accounts/{acc}", timeout=20,
                                 headers={"Authorization": f"Bearer {tok}"}).json()
                b.append("Cloudflare account pahunch: " + ("✅" if a.get("success") else str(a.get("errors"))[:120]))
    except Exception as e:
        b.append(f"Cloudflare jaanch: {e}")
    try:
        from . import relay, tg
        c = relay.cfg()
        b.append(f"Relay: url {'haan' if c.get('url') else 'NAHI'} | live {c.get('live')} | abhi raasta: {tg.route_name()}")
        if not c.get("live"):
            R.find("🟡", "Telegram ka doosra raasta (Cloudflare relay) chalu nahi", "bot: 'relay banao' (CF sahi hone ke baad)")
    except Exception as e:
        b.append(f"Relay: {e}")
    b.append("Backup ntfy: " + ("judi" if state.get("ntfy_ok") else "setup baaki ('backup setup')"))
    b.append("Gemini: aakhri model " + str(state.get("gemini_last_model")) + " | aakhri galti: " + str(state.get("gemini_last_error"))[:160])
    b.append("Gemini band (cool): " + json.dumps(state.get("gemini_cool") or {})[:300])
    if state.get("cfai_noperm"):
        R.find("🟡", "Cloudflare token mein 'Workers AI: Read' nahi - Gemini busy ho to bot chup", "Token Edit → Workers AI Read")
    hist = state.get("history", [])
    days = [(datetime.date.today() - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    b.append("\nPichhle 7 din upload (brand x din " + " ".join(d[5:] for d in days) + "):")
    for bk, v in BRANDS.items():
        row = [sum(1 for h in hist if h.get("brand") == bk and h.get("date") == d) for d in days]
        b.append(f"- {v['name']:<18} " + " ".join(str(x) for x in row) + f"  (kul {sum(row)})")
        miss = sum(1 for x in row[-4:-1] if x == 0)          # v2.1.2: sirf pichhle 3 poore din (purana outage nahi)
        if miss >= 1:
            R.find("🟡", f"{v['name']}: pichhle 3 din mein {miss} din koi video nahi", "Section 5 ki galtiyan dekhein")
    ph = state.get("platform_health") or {}
    bad = [f"{k}: {v.get('err', '')[:90]}" for k, v in ph.items() if not v.get("ok")]
    b.append("\nPlatform jo ruke hain:\n" + ("\n".join(bad) or "(koi nahi)"))
    b.append("\nGaltiyan (3 din, ginti):\n" + sh(
        "journalctl -u sabhinet --since '-3 days' --no-pager 2>/dev/null | grep -iE 'error|traceback|galti|fail|nahi chala' | "
        "sed -E 's/^.{0,40}python3?\\[[0-9]+\\]: //; s/[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9:]{8} //; s/[0-9]+/N/g' | "
        "cut -c1-150 | sort | uniq -c | sort -rn | head -30"))
    ga = sh("journalctl -u sabhinet --since '-7 days' --no-pager 2>/dev/null | "
            "grep -oE 'https://console\\.(developers|cloud)\\.google\\.com/apis/[^ \"]*' | sort -u | head -3")
    if ga:
        b.append("Google API jo band hain (link):\n" + ga)
        R.find("🟡", "Google ki koi API project mein chalu nahi (traffic/analytics adhoora)", "Section 5 ka link kholkar 'Enable'")
    b.append("\nsabhinet data size:\n" + sh(f"du -sh '{DATA}' '{DATA}'/* '{BASE}/logs' 2>/dev/null | sort -rh | head -15"))
    sec = sh(f"ls -la '{SECRETS}' 2>/dev/null")
    b.append("\nsecrets folder (sirf naam/permission):\n" + sec)
    if re.search(r"^-rw-r--r--", sec, re.M):
        R.find("🟡", "secrets folder mein koi file sabke liye padhne layak", f"chmod 600 {SECRETS}/*")
    b.append(f"\nPending list: {len(state.get('todo') or [])} kaam")
    R.sec("5. SABHISAAB BOT (login, Cloudflare, relay, Gemini, upload, galti)", "\n".join(b))


def sec_files(R):
    b = []
    units_txt = sh("for u in $(systemctl list-units --type=service --all --no-legend --no-pager --plain | awk '{print $1}'); do "
                   "systemctl show $u -p ExecStart -p WorkingDirectory --value; done 2>/dev/null")
    cron_txt = sh("crontab -l 2>/dev/null; sudo -n crontab -l 2>/dev/null; cat /etc/cron.d/* 2>/dev/null")
    b.append("/home/ubuntu (size | aakhri badlaav | kisi service/cron mein?):")
    now = time.time()
    for d in sorted(HOME.iterdir()):
        if d.name.startswith(".") and d.name not in (".cache", ".local", ".npm", ".config"):
            continue
        size = sh(f"du -sh '{d}' 2>/dev/null | cut -f1")
        try:
            newest = float(sh(f"find '{d}' -xdev -type f -printf '%T@\\n' 2>/dev/null | sort -n | tail -1") or 0)
        except ValueError:
            newest = 0
        age = int((now - newest) / 86400) if newest else -1
        used = str(d) in units_txt or str(d) in cron_txt
        keepn = {".cache": " | andar huggingface = sabhinet ka awaaz/model, MAT mitao", ".local": " | python/pip ka saaman, mat mitao"}
        b.append(f"- {d.name:<28} {size:>6} | {age} din pehle | {'✅ chal raha' if used else '— kisi service mein nahi'}"
                 f"{' | git' if (d / '.git').exists() else ''}{keepn.get(d.name, '')}")
        if d.is_dir() and not used and age > 30 and not d.name.startswith("."):
            R.find("🟡", f"'{d.name}' ({size}) {age} din se nahi chhua, kisi service/cron mein nahi - shayad bekaar",
                   "Claude se pakka karke hatayein (bot kuch nahi mitata)")
    b.append("\nBade file (>150 MB):\n" + sh("find /home/ubuntu -xdev -type f -size +150M -printf '%s %p\\n' 2>/dev/null | "
                                            "sort -rn | head -20 | awk '{printf \"%.0f MB %s\\n\", $1/1048576, $2}'"))
    b.append("\nBackup/purani copy:\n" + sh("find /home/ubuntu -maxdepth 3 \\( -iname '*backup*' -o -iname '*.bak*' -o -iname '*_old*' "
                                           "-o -iname '*.zip' -o -iname '*.tar*' \\) -not -path '*/node_modules/*' -not -path '*/venv/*' "
                                           "-printf '%TY-%Tm-%Td %s %p\\n' 2>/dev/null | sort | tail -30 | "
                                           "awk '{printf \"%s %.1f MB %s\\n\", $1, $2/1048576, $3}'"))
    b.append("\nCache/kachra: pip/.cache " + sh("du -sh /home/ubuntu/.cache 2>/dev/null | cut -f1") +
             " | journal " + sh("journalctl --disk-usage 2>/dev/null | grep -oE '[0-9.]+[KMGT]'") +
             " | apt " + sh("du -sh /var/cache/apt 2>/dev/null | cut -f1") + " | /tmp " + sh("du -sh /tmp 2>/dev/null | cut -f1"))
    jr = sh("journalctl --disk-usage 2>/dev/null | grep -oE '[0-9.]+G'")
    if jr:
        R.find("🟡", f"System log {jr} ka (bekaar jagah)", "sudo journalctl --vacuum-size=300M")
    b.append("\nPython venv:\n" + sh("find /home/ubuntu -maxdepth 3 -name pyvenv.cfg -printf '%h\\n' 2>/dev/null | "
                                    "xargs -r -I{} du -sh {} 2>/dev/null"))
    R.sec("6. FILE/FOLDER (kya kahan, kya bekaar, kachra)", "\n".join(b))


def sec_guard(R):
    b = ["Chowkidar: " + sh("systemctl is-active chowkidar") + " | restarts " + sh("systemctl show chowkidar -p NRestarts --value")]
    try:
        from . import updater
        files = updater._cw_files()
        b.append("Chowkidar mein 'ytlistener' wali file: " + (", ".join(str(f) for f in files) or "koi nahi ✅"))
        if files:
            R.find("🟡", "Chowkidar abhi bhi ytlistener dekhta hai (sabhinet nahi)", "bot: 'chowkidar fix' (15:35 ke baad)")
    except Exception as e:
        b.append(str(e))
    b.append("\nTrading (SIRF PADHA - kabhi chheda nahi):")
    for s in TRADING:
        st = sh(f"systemctl is-active {s}")
        if st != "active" and s == "nifty-chart-watchdog":
            b.append(f"- {s}: {st} (watchdog; band hona theek ho sakta hai)")
            continue
        rs = sh(f"systemctl show {s} -p NRestarts --value")
        er = sh(f"journalctl -u {s} --since '-1 day' --no-pager 2>/dev/null | grep -ci 'error\\|traceback'")
        b.append(f"- {s}: {st} | restarts {rs} | 1 din mein error-line {er}")
        if st != "active":
            R.find("🔴", f"Trading service '{s}' {st}", "Khud dekhein (bot nahi chhedta)")
    R.sec("7. CHOWKIDAR + TRADING (sirf padha)", "\n".join(b))


def run_all():
    R = Report()
    t0 = time.time()
    for fn in (sec_system, sec_services, sec_bots, sec_security, sec_sabhinet, sec_files, sec_guard):
        try:
            fn(R)
        except Exception as e:
            import traceback
            R.sec(f"{fn.__name__} (adhoora)", f"galti: {e}\n{traceback.format_exc()[-600:]}")
    order = {"🔴": 0, "🟡": 1}
    R.F.sort(key=lambda x: order.get(x[0], 2))
    head = [f"# VM AUDIT / POSTMORTEM - {datetime.datetime.now():%Y-%m-%d %H:%M} ({int(time.time() - t0)} sec)",
            "SIRF PADHA GAYA - kuch badla/mitaya/restart nahi. Har secret chhupa (fp = pehchaan ke 8 akshar).", "",
            f"## NATEEJA: 🔴 {sum(1 for f in R.F if f[0] == '🔴')} zaroori | 🟡 {sum(1 for f in R.F if f[0] == '🟡')} dhyan", ""]
    head += [f"{l} {t}" + (f"\n     → {x}" if x else "") for l, t, x in R.F] or ["🟢 Koi kami nahi mili."]
    return mask("\n".join(head)) + "\n" + "\n".join(R.S) + "\n", R.F


def run_and_send():
    from . import tg
    from .config import DATA
    text, F = run_all()
    out = DATA / f"vm-audit-{datetime.datetime.now():%Y%m%d-%H%M}.txt"
    out.write_text(text, encoding="utf-8")
    out.chmod(0o600)
    red = sum(1 for f in F if f[0] == "🔴")
    yel = sum(1 for f in F if f[0] == "🟡")
    with open(out, "rb") as fh:
        tg.call("sendDocument", {"chat_id": tg._chat(), "caption": f"🔎 VM audit: 🔴 {red} | 🟡 {yel}. Ye file Claude ko bhejein "
                                                                    "(secret chhupe hain)."}, {"document": fh})
    top = "\n".join(f"{l} {t[:110]}" for l, t, _ in F[:12])
    return f"🔎 VM audit poora. 🔴 {red} zaroori, 🟡 {yel} dhyan.\n{top}"
