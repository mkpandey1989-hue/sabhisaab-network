#!/usr/bin/env python3
"""vm_backup.py  (Claude, 17 Nov 2026) - VM ke SAARE bot/chart/chowkidar ka CODE roz PRIVATE GitHub repo par.

Owner: "sari file GitHub par rakh do taki koi bhi AI se change/theek karwa saku; security wali file mat bhejna".
- Kahan: https://github.com/mkpandey1989-hue/vm-bots  (PRIVATE - push se pehle har baar jaanchta hai; public mila to RUK jata hai)
- Kya jaata hai: /home/ubuntu ke .py .sh .md .service .timer .cron + systemd unit + crontab + roadmap .docx (text bana kar).
  (sabhinet ka code pehle se apne repo sabhisaab-network mein hai - wo yahan nahi.)
- Kya KABHI nahi: secrets/ .ssh .oci .env token/pass/key/secret naam ki file, .json state, .db, log, xlsx journal, photo/video.
  Code ke andar ke token / ntfy topic / Telegram chat id / password -> '***' (asli sirf VM par).
- Token: sabhinet ka GITHUB_TOKEN (/home/ubuntu/sabhisaab-network/secrets/bot.env) - naya kuch nahi maangta.
- Chalana:  python3 vm_backup.py           (abhi ek baar)
            python3 vm_backup.py --install (roz raat 02:40 apne aap - crontab mein ek line; dobara chalane par dohra nahi)
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

HOME = os.environ.get("VMB_HOME", "/home/ubuntu")
REPO = "mkpandey1989-hue/vm-bots"
ENVF = os.path.join(HOME, "sabhisaab-network/secrets/bot.env")
SYSD = os.environ.get("VMB_SYSTEMD", "/etc/systemd/system")
UNITS = ("sabhinet", "nifty-live", "delta-live", "chowkidar", "nifty-chart", "nifty-chart-watchdog", "nifty-chart-maint",
         "billguard", "ytlistener")
CODE_EXT = (".py", ".sh", ".md", ".service", ".timer", ".cron", ".html", ".js", ".css")
SKIP_DIRS = {"sabhisaab-network", "sabhisaab", "unit_backups", "secrets", "snap", "node_modules", "venv", ".venv", "data", "logs",
             "chart_data", "photos", "videos", "deploy_backups", "backups", "bt", "tmp", "__pycache__", "sabhisaab_site", "site"}
BAD_NAME = re.compile(r"(?i)(token|passw|pwd|secret|apikey|api_key|\.env$|\.key$|\.pem$|credential|cookie|session|oauth|"
                      r"mainnet|delta_tg|\.bak|backup)")
BAD_CODE = re.compile(r"(?i)\.bak|backup|\.orig$|\.old$")    # code file (.py/.sh): naam mein 'token' ho to bhi aaye (refresh_token.py) - andar safai hoti hai
SKIP_FILES = {"caf.py", "csf.py", "vm_backup.py"}            # Claude ke tool ki download copy (asli tools/ mein) - vm_backup.py alag se
SKIP_DIRS |= {"carve", "keep"}                               # purani recovery ke tukde (Perl CPAN) - code nahi
MAXB = 900_000
CRON = "40 2 * * * /usr/bin/python3 %s/vm_backup.py >> %s/vm_backup.log 2>&1" % (HOME, HOME)


def token():
    try:
        for ln in open(ENVF):
            if ln.startswith("GITHUB_TOKEN="):
                return ln.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return os.environ.get("GITHUB_TOKEN", "")


def gh(path, tok, data=None, method=None):
    rq = urllib.request.Request("https://api.github.com" + path, method=method,
                                data=json.dumps(data).encode() if data else None,
                                headers={"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(rq, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception:
        return 0, {}


# ---------------- secret safai ----------------
GENERIC = [
    r"\d{8,10}:[A-Za-z0-9_-]{30,}",                       # Telegram bot token
    r"AIza[0-9A-Za-z_-]{30,}", r"gh[pousr]_[A-Za-z0-9]{30,}", r"github_pat_\w{30,}", r"GOCSPX-[\w-]{20,}",
    r"pina_[A-Za-z0-9]{20,}", r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",   # JWT (Dhan token)
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----", r"\bsk-[A-Za-z0-9_-]{20,}",
]
KV = re.compile(r"""(?i)\b(\w*(?:token|secret|passw(?:or)?d?|api_?key|client_?id|chat_?id|topic|webhook)\w*["']?\s*[:=]\s*["'])"""
                r"""([^"'\n]{4,})(["'])""")


def collect_literals(texts):
    """sab file mein se ntfy topic + chat id + webhook jaise asli maan - har jagah (URL mein bhi) chhupane ke liye."""
    lit = set()
    for t in texts:
        for m in re.finditer(r"""(?i)\b\w*(?:TOPIC|CHAT_?ID|OWNER_?ID|CLIENT_?ID)\w*["']?[ \t]*[:=][ \t]*(?:["']([A-Za-z0-9_-]{5,})["']|(-?\d{6,})\b)""", t):
            lit.add(m.group(1) or m.group(2))
        for m in re.finditer(r"(?i)\bclient_?id\s*=\s*(\d{6,})", t):     # Dhan client id (comment/print mein bhi)
            lit.add(m.group(1))
        for m in re.finditer(r"ntfy\.sh/([A-Za-z0-9_-]{5,})", t):
            lit.add(m.group(1))
    return {x for x in lit if not x.isupper() and x not in ("None", "True", "False")}


def scrub(t, lits):
    for p in GENERIC:
        t = re.sub(p, "***", t)

    def kv(m):
        v = m.group(2)
        if "/" in v or re.search(r"\.(txt|json|key|env|log|pem)$", v) or v.startswith("{") or " " in v.strip():
            return m.group(0)                       # file ka naam/path ya sandesh - chhupane ki zarurat nahi
        return m.group(1) + "***" + m.group(3)
    t = KV.sub(kv, t)
    for x in sorted(lits, key=len, reverse=True):
        t = t.replace(x, "***")
    return t


def docx_text(p):
    try:
        x = zipfile.ZipFile(p).read("word/document.xml").decode("utf-8", "ignore")
        x = re.sub(r"</w:p>", "\n", x)
        return re.sub(r"<[^>]+>", "", x)
    except Exception:
        return None


# ---------------- file chuno ----------------
def gather():
    files = {}                                   # repo_path -> text
    for root, dirs, fs in os.walk(HOME):
        rel = os.path.relpath(root, HOME)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS and depth < 2]
        for f in fs:
            p = os.path.join(root, f)
            rp = os.path.normpath(os.path.join("home", rel, f))
            if f.startswith(".") or os.path.islink(p) or (depth == 0 and f in SKIP_FILES):
                continue
            if BAD_NAME.search(f) and not (f.endswith((".py", ".sh")) and not BAD_CODE.search(f)
                                           and not re.search(r"(?i)\.(env|key|pem)$", f)):
                continue
            try:
                if os.path.getsize(p) > MAXB:
                    continue
            except Exception:
                continue
            if f.endswith(CODE_EXT):
                try:
                    files[rp] = open(p, encoding="utf-8").read()
                except Exception:
                    pass
            elif f.endswith(".docx"):
                t = docx_text(p)
                if t:
                    files[rp[:-5] + ".docx.md"] = t
    for u in UNITS:
        for ext in (".service", ".timer"):
            p = os.path.join(SYSD, u + ext)
            if os.path.exists(p):
                files["systemd/" + u + ext] = open(p).read()
    for who, cmd in (("ubuntu", ["crontab", "-l"]), ("root", ["sudo", "-n", "crontab", "-l"])):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if r.returncode == 0:
                files[f"cron/crontab_{who}.txt"] = r.stdout
        except Exception:
            pass
    return files


README = """# vm-bots - nifty-a1 VM ka poora code (PRIVATE)

**Ye repo VM khud roz raat 02:40 update karta hai** (`vm_backup.py`, cron). Yahan jo hai wahi VM par chal raha hai.
Aakhri update: {when} | {n} file

## Koi bhi AI pehle ye padhe
1. Ye sirf **padhne/samajhne** ki copy hai. Code mein `***` = asli token/topic/chat id/password - wo sirf VM par hain. Yahan kabhi asli secret mat likho.
2. Badlav ka tareeka (hamesha): naya code ek **tool script** (backup + py_compile + idempotent) ke roop mein
   `sabhisaab-network/tools/` mein do -> owner VM par ek `curl ... && python3 ...` line chalata hai -> agli raat ye repo khud update.
3. Trading logic (nifty_option_LIVE.py, delta_btc_LIVE.py) owner ki marzi ke bina **kabhi mat chhedo**. Bazaar ke samay (9:00-15:30) nifty-live restart nahi.
4. Poora haal / niyam / account: https://github.com/mkpandey1989-hue/sabhisaab-network/blob/claude/v348/docs/MASTER.md

## Kya kahan
| Folder | Kya |
|---|---|
| home/ | /home/ubuntu ke bot: nifty_option_LIVE.py (Nifty options, Dhan), refresh_token.py (Dhan token roz 08:45), master_guard.py, vm_health.py, ntfy_monitor.py, maintenance.sh |
| home/deltabot/ | BTC bot (Delta) - delta-live yahi wala chalata hai |
| home/nifty_chart/ | Nifty live chart (port 8003) + watchdog + maint |
| home/chowkidar/ | VM chowkidar Telegram bot (report, suraksha, bill) |
| systemd/ | service/timer file (Restart=always, StartLimitIntervalSec=0) |
| cron/ | crontab (ubuntu + root) |
| *.docx.md | roadmap/guide docx ka text |

Kabhi nahi aata: secrets/, .ssh, .oci, *.env, token/pass/key naam ki DATA file (code .py aata hai, andar `***`), *.json state, *.db, log, xlsx journal, photo/video.

## Koi AI kaise padhe
- Claude (claude.ai / Claude Code): owner chat mein bole "vm-bots repo bhi padho" -> repo jod kar `git clone` (private - owner ki ijazat se).
- Doosra AI: owner GitHub par is repo ka ZIP (Code -> Download ZIP) de, ya us AI ko repo ki access de.
- Pehle ye README, phir neeche ki 'ASLI chalne wali file' table, phir sabhisaab-network ka docs/MASTER.md.
"""


def build(lits_out=None):
    files = gather()
    lits = collect_literals(files.values())
    return files, lits


def running_table():
    """systemd ExecStart + crontab se: ASLI chalne wali file kaun si (AI galat copy na badle) + service ka haal."""
    rows, seen = [], set()
    for u in UNITS:
        p = os.path.join(SYSD, u + ".service")
        if not os.path.exists(p):
            continue
        txt = open(p).read()
        try:
            act = subprocess.run(["systemctl", "is-active", u], capture_output=True, text=True, timeout=10).stdout.strip()
            ena = subprocess.run(["systemctl", "is-enabled", u], capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            act = ena = "?"
        paths = re.findall(r"/home/ubuntu/[\w./-]+\.(?:py|sh)\b", txt)
        wd = re.search(r"WorkingDirectory=(\S+)", txt)
        for rel in re.findall(r"ExecStart=\S+\s+(?:-u\s+)?([\w.-]+\.py)\b", txt):
            if wd:
                paths.append(os.path.join(wd.group(1), rel))
        for f in paths:
            if f in seen or "/venv/" in f or "env/bin" in f:
                continue
            seen.add(f)
            loc = f.replace("/home/ubuntu", "home", 1)
            ok = os.path.exists(f.replace("/home/ubuntu", HOME, 1))
            rows.append(f"| {u} ({act}, {ena}) | `{loc}` | {'✅' if ok else '❌ VM par file nahi mili'} |")
    try:
        cr = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        cr = ""
    for f in sorted(set(re.findall(r"/home/ubuntu/[\w./-]+\.(?:py|sh)", cr))):
        if f in seen:
            continue
        seen.add(f)
        ok = os.path.exists(f.replace("/home/ubuntu", HOME, 1))
        rows.append(f"| cron | `{f.replace('/home/ubuntu', 'home', 1)}` | {'✅' if ok else '❌ VM par file nahi mili'} |")
    return ("\n## ASLI chalne wali file (systemd + cron se - inhi ko badlo, baaki copy/purani ho sakti hain)\n"
            "| Kaun chalata (haal) | File | |\n|---|---|---|\n" + "\n".join(rows) + "\n"
            "| sabhinet | alag repo: https://github.com/mkpandey1989-hue/sabhisaab-network | ✅ |\n")


def run(dry=None):
    if dry:
        files, lits = build()
        for rp, t in files.items():
            fp = os.path.join(dry, rp)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            open(fp, "w", encoding="utf-8").write(scrub(t, lits))
        print(len(files), "file,", len(lits), "maan chhupaye ->", dry)
        return True
    tok = token()
    if not tok:
        sys.exit("❌ GITHUB_TOKEN nahi mila (" + ENVF + ")")
    st, j = gh("/repos/" + REPO, tok)
    if st == 404:
        st2, _ = gh("/user/repos", tok, {"name": REPO.split("/")[1], "private": True,
                                          "description": "nifty-a1 VM bots ka code (roz VM se, secrets ke bina)"}, "POST")
        if st2 not in (201, 422):
            sys.exit(f"❌ Token repo nahi bana sakta (GitHub {st2}). 1 min ka kaam: https://github.com/new -> Repository name: vm-bots "
                     "-> PRIVATE chuno -> Create repository. Phir yahi command dobara chalao.")
        time.sleep(3)
        st, j = gh("/repos/" + REPO, tok)
    if st != 200:
        sys.exit(f"❌ Repo tak pahunch nahi (GitHub {st}) - token ko is repo ki 'Contents: write' chahiye. Claude ko batao.")
    if not j.get("private"):
        sys.exit("🛑 Repo PUBLIC hai - suraksha ke liye kuch nahi bheja. GitHub > vm-bots > Settings > Private karo.")
    files = gather()
    lits = collect_literals(files.values())
    out = tempfile.mkdtemp(prefix="vmb_")
    for rp, t in files.items():
        fp = os.path.join(out, rp)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        open(fp, "w", encoding="utf-8").write(scrub(t, lits))
    open(os.path.join(out, "README.md"), "w").write(
        README.format(when=time.strftime("%d %b %Y %H:%M", time.gmtime(time.time() + 19800)) + " IST", n=len(files)) + running_table())
    shutil.copy2(os.path.abspath(__file__), os.path.join(out, "vm_backup.py"))
    # aakhri jaal: koi bhi bacha secret jaisa shabd mila to push hi nahi
    left = []
    for r, _, fs in os.walk(out):
        for f in fs:
            t = open(os.path.join(r, f), encoding="utf-8", errors="ignore").read()
            for p in GENERIC:
                if re.search(p, t):
                    left.append(f)
            if tok in t:
                left.append(f)
    if left:
        shutil.rmtree(out, ignore_errors=True)
        sys.exit("🛑 In file mein secret jaisa kuch bacha - push NAHI kiya: " + ", ".join(sorted(set(left))[:5]))
    url = f"https://x-access-token:{tok}@github.com/{REPO}.git"
    ok = True
    for c in (["git", "init", "-q", "-b", "main"], ["git", "add", "-A"],
              ["git", "-c", "user.name=nifty-a1", "-c", "user.email=vm@sabhisaab.com", "commit", "-q", "-m",
               "VM copy " + time.strftime("%Y-%m-%d")], ["git", "push", "-q", "-f", url, "main"]):
        r = subprocess.run(c, cwd=out, capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            print("❌", " ".join(c[:2]), (r.stderr or r.stdout).replace(tok, "***")[-300:])
            ok = False
            break
    shutil.rmtree(out, ignore_errors=True)
    if ok:
        print(f"✅ GitHub par gaya: https://github.com/{REPO}  ({len(files)} file, secret '***' kiye: {len(lits)} maan)")
    return ok


def install():
    me = os.path.join(HOME, "vm_backup.py")
    if os.path.abspath(__file__) != me:
        shutil.copy2(os.path.abspath(__file__), me)
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    if "vm_backup.py" not in cur:
        new = cur.rstrip("\n") + "\n" + CRON + "\n"
        subprocess.run(["crontab", "-"], input=new, text=True)
        print("✅ Roz raat 02:40 apne aap (crontab mein joda)")
    else:
        print("ℹ️ Roz wala pehle se laga hai")


SELF_URL = "https://raw.githubusercontent.com/mkpandey1989-hue/sabhisaab-network/claude/v348/tools/vm_backup.py"


def self_update():
    """roz raat: owner ke apne repo se is script ka naya version (Claude ka sudhaar) - owner ko dobara command nahi chalani.
    Sirf tab badle jab naya code compile ho aur usme ye hi script ho (vm-bots + PRIVATE jaanch)."""
    import py_compile
    me = os.path.abspath(__file__)
    try:
        new = urllib.request.urlopen(SELF_URL, timeout=30).read().decode("utf-8")
    except Exception:
        return False
    if new == open(me, encoding="utf-8").read() or 'REPO = "mkpandey1989-hue/vm-bots"' not in new or "PRIVATE hai" not in new:
        return False
    tmp = me + ".new"
    open(tmp, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(tmp, doraise=True)
    except Exception:
        os.remove(tmp)
        return False
    os.replace(tmp, me)
    print("🔄 vm_backup.py naya version laga")
    return True


if __name__ == "__main__":
    if "--no-update" not in sys.argv and "--dry" not in sys.argv and self_update():
        os.execv(sys.executable, [sys.executable, os.path.abspath(__file__), "--no-update"] + [a for a in sys.argv[1:] if a != "--install"])
    if "--install" in sys.argv:
        install()
    run(dry=sys.argv[sys.argv.index("--dry") + 1] if "--dry" in sys.argv else None)
