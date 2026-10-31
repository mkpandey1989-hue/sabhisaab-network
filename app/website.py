"""Website (sabhisaab.com) ka poora kaam ab isi bot mein - purane Cloudflare/GitHub-Actions bot ki jagah.
Website repo ki apni jaanchi hui scripts (daily.py, watch.py, gsc.py, audit.py) VM par chalti hain; report isi bot se aati hai.
Bing suraksha: IndexNow sirf BADLE hue URL, din mein max 10, ek URL 14 din mein ek baar. '--all' kabhi nahi."""
import datetime
import json
import os
import shutil
import subprocess
import time
import re
import zipfile
import requests
from . import state, tg, diary
from .config import BASE, DATA, SECRETS, IST, SITE_ZIP_MAX_FILES, NEW_PAGES_PER_DAY
from .log import log

REPO = "mkpandey1989-hue/sabhisaab"
DIR = DATA / "site_repo"
KEEP = DATA / "site_state"
SA = SECRETS / "gsc_sa.json"
ENVF = SECRETS / "site.env"
INDEXNOW_KEY = "f25e6bb327394937bd14591cb8dc2800"      # site par public file hai, secret nahi
SITE = "https://sabhisaab.com"
GA4_PROPERTY = "543920755"
MAX_FILES = SITE_ZIP_MAX_FILES     # v2.0: 22 ki purani seema hatayi
OLD_CRONS = ["daily.yml", "watch.yml", "pending.yml", "health.yml", "notify.yml", "bot.yml"]
PY = str(BASE / "venv" / "bin" / "python")
import threading as _th
ZIP_LOCK = _th.Lock()


def _env():
    e = dict(os.environ)
    if ENVF.exists():
        for line in ENVF.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                e[k.strip()] = v.strip()
    e.update(TG_TOKEN=os.environ.get("LISTENER_BOT_TOKEN", ""), TG_CHAT=os.environ.get("OWNER_CHAT_ID", ""),
             GA4_PROPERTY_ID=GA4_PROPERTY, GSC_PROPERTY="sc-domain:sabhisaab.com", GH_REPO=REPO)
    if SA.exists():
        e["GOOGLE_SA_JSON"] = SA.read_text()
    if os.environ.get("GITHUB_TOKEN"):
        e["BOT_GH_TOKEN"] = os.environ["GITHUB_TOKEN"]
    if os.environ.get("GEMINI_API_KEY"):
        e["GEMINI_KEY"] = os.environ["GEMINI_API_KEY"]
    return e


def set_env(key, val):
    lines = [l for l in ENVF.read_text().splitlines() if not l.startswith(key + "=")] if ENVF.exists() else []
    ENVF.write_text("\n".join(lines + [f"{key}={val}"]) + "\n")
    ENVF.chmod(0o600)


def _git(*args, timeout=180):
    r = subprocess.run(["git", *args], cwd=DIR, capture_output=True, text=True, timeout=timeout)
    tok = os.environ.get("GITHUB_TOKEN", "")
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).replace(tok, "***")[-300:] if tok else (r.stderr or r.stdout)[-300:])
    return r.stdout


def _config():
    has_sa = SA.exists()
    e = _env()
    cfg = {"site_url": SITE, "site_dir": "site", "incoming_dir": str(DATA / "site_incoming"),
           "gsc_property": "sc-domain:sabhisaab.com", "ga4_id": "G-QX5MWV42TR", "adsense_approved": bool(state.get("adsense_ok")),
           "git_branch": "main", "indexnow_key": INDEXNOW_KEY, "bing_api_key": e.get("BING_API_KEY", "x"),
           "bing_enabled": bool(e.get("BING_API_KEY")), "google_sa_json": str(SA) if has_sa else "/tmp/x.json",
           "gsc_enabled": has_sa, "gsc_daily_budget": 150, "telegram_token": e["TG_TOKEN"],
           "telegram_chat_id": e["TG_CHAT"], "telegram_enabled": True}
    (DIR / "config.json").write_text(json.dumps(cfg))


def sync():
    """Repo ki taaza copy (code), par bot ki yaaddasht (state/) surakshit."""
    if not (DIR / ".git").exists():
        DIR.parent.mkdir(parents=True, exist_ok=True)
        tok = os.environ.get("GITHUB_TOKEN")
        url = f"https://x-access-token:{tok}@github.com/{REPO}.git" if tok else f"https://github.com/{REPO}.git"
        r = subprocess.run(["git", "clone", "-q", "--depth", "20", url, str(DIR)], capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError("Website repo clone nahi hua: " + r.stderr[-200:].replace(tok or "#", "***"))
    else:
        KEEP.mkdir(parents=True, exist_ok=True)
        for f in list((DIR / "state").glob("*.json")) + [DIR / "state.json"]:
            if f.exists():
                shutil.copy2(f, KEEP / f.name)
        if state.get("gh_pending"):                   # v2.0.2: VM ki nayi commit GitHub par nahi gayi - mitao mat
            pass
        else:
            _git("fetch", "-q", "--depth", "20", "origin", "main", timeout=600)
            _git("reset", "-q", "--hard", "origin/main")
        for f in KEEP.glob("*.json"):
            dest = DIR / ("state.json" if f.name == "state.json" else f"state/{f.name}")
            dest.parent.mkdir(exist_ok=True)
            shutil.copy2(f, dest)
    _config()


def ensure_node():
    """v1.8.1: website audit JS jaanch ke liye node chahiye. Na ho to ek baar apne aap install (sudo -n, bina password)."""
    if shutil.which("node"):
        return True
    if state.get("node_try") == str(datetime.date.today()):
        return False
    state.put("node_try", str(datetime.date.today()))
    try:
        r = subprocess.run(["sudo", "-n", "apt-get", "install", "-y", "-q", "nodejs"], capture_output=True, text=True,
                           timeout=900, env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"})
        log(f"nodejs install rc={r.returncode} {r.stderr[-200:]}")
    except Exception as e:
        log(f"nodejs install: {e}")
    return bool(shutil.which("node"))


def run_script(*args, timeout=3600, extra_env=None):
    """Website repo ki script chalao (neechi priority - trading/video ko takleef nahi)."""
    sync()
    env = _env()
    env.update(extra_env or {})
    r = subprocess.run(["nice", "-n", "15", PY, *args], cwd=DIR, env=env, capture_output=True, text=True,
                       timeout=timeout)
    out = (r.stdout + r.stderr)[-1500:]
    log(f"website {args}: rc={r.returncode} {out[-300:]}")
    return r.returncode, out


def daily(hold_until=None):
    """Roz ki website report. v2.0.3: hold_until (epoch) = report pehle taiyaar, Telegram par theek tay samay par
    (website repo ki daily.py TG_HOLD_UNTIL maanti hai - W4 ke baad)."""
    rc, out = run_script("scripts/daily.py", timeout=4200,
                         extra_env={"TG_HOLD_UNTIL": str(int(hold_until))} if hold_until else None)
    if rc != 0:
        tg.alert("yellow", f"Website ki roz ki report mein dikkat:\n{out[-400:]}")


def watch():
    rc, out = run_script("scripts/watch.py", "watch", timeout=900)
    if rc != 0:
        log(f"site watch rc {rc}")


def pending():
    run_script("scripts/watch.py", "pending", timeout=900)


def audit_text():
    rc, out = run_script("scripts/audit.py", timeout=600)
    return ("✅" if rc == 0 else "❌") + " Website audit:\n" + out[-1200:]


def index_report():
    if not SA.exists():
        return "🔑 Google service account file baaki (steps chat mein) - tab tak indexing report nahi."
    rc, out = run_script("scripts/gsc.py", "report", timeout=1800)
    return None if rc == 0 else f"Indexing report nahi bani:\n{out[-300:]}"


# ---------------- Bing-safe IndexNow ----------------
def indexnow(urls, reason=""):
    """Sirf badle URL. Din mein max 10. Ek URL 14 din mein ek hi baar. (12,800 wali galti dobara kabhi nahi.)"""
    sent = state.get("indexnow_sent") or {}
    today = str(datetime.date.today())
    cut = str(datetime.date.today() - datetime.timedelta(days=14))
    sent = {u: d for u, d in sent.items() if d >= cut}
    today_n = sum(1 for d in sent.values() if d == today)
    fresh = [u for u in dict.fromkeys(urls) if u.startswith(SITE) and u not in sent][:max(0, 10 - today_n)]
    if not fresh:
        return "IndexNow: kuch nahi bheja (seema/pehle bheja ja chuka)"
    r = requests.post("https://api.indexnow.org/IndexNow", timeout=30, json={
        "host": "sabhisaab.com", "key": INDEXNOW_KEY, "keyLocation": f"{SITE}/{INDEXNOW_KEY}.txt", "urlList": fresh})
    if r.status_code in (200, 202):
        for u in fresh:
            sent[u] = today
        state.put("indexnow_sent", sent)
        diary.add("upload", f"IndexNow {len(fresh)} URL ({reason})")
        return f"IndexNow: {len(fresh)} badle URL bheje ✅"
    return f"IndexNow: HTTP {r.status_code} {r.text[:80]}"


def bing_status():
    key = _env().get("BING_API_KEY")
    if not key:
        return "🔑 Bing API key baaki (Bing Webmaster → Settings → API access → API Key) - bot ko bhejein: 'bing key <key>'"
    base = "https://ssl.bing.com/webmaster/api.svc/json"
    try:
        q = requests.get(f"{base}/GetUrlSubmissionQuota", params={"apikey": key, "siteUrl": SITE + "/"}, timeout=30).json()
        c = requests.get(f"{base}/GetCrawlStats", params={"apikey": key, "siteUrl": SITE + "/"}, timeout=30).json()
        if not c.get("d") and (c.get("Message") or c.get("ErrorCode") is not None):
            return f"🔎 Bing ne data nahi diya: {c.get('Message') or c.get('ErrorCode')} (key/site jaanchein)"
        if not c.get("d"):
            return ("🔎 Bing: key sahi hai, par crawl ka data abhi khaali hai (block/ticket ke dauraan aisa hota hai). "
                    f"URL quota: {q.get('d', {}).get('DailyQuota', '-')}")
        st = (c.get("d") or [])[-1] if c.get("d") else {}
        return (f"🔎 Bing: crawl kiye {st.get('CrawledPages', '-')}, index mein {st.get('InIndex', '-')}, "
                f"crawl error {st.get('CrawlErrors', '-')} | aaj ka quota {q.get('d', {}).get('DailyQuota', '-')}")
    except Exception as e:
        return f"Bing jaanch nahi hui: {str(e)[:100]}"


# ---------------- Website ZIP -> audit -> GitHub -> deploy (v2.0) ----------------
REPO_DIRS = ("site/", "scripts/", "worker/", ".github/workflows/")
ROOT_OK = ("README.md", "requirements.txt", ".gitignore")
SITE_EXT = (".html", ".xml", ".txt", ".js", ".json", ".css", ".py", ".yml", "_headers", "_routes", ".md",
            ".webp", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".webmanifest", ".woff2")


def _clean(n):
    n = n.replace("\\", "/").lstrip("./")
    for pre in ("sabhisaab-main/", "sabhisaab/"):          # GitHub se utari ZIP ka bahari folder
        if n.startswith(pre):
            n = n[len(pre):]
    return n


def is_site_zip(names):
    names = [_clean(n) for n in names if not n.endswith("/")]
    return bool(names) and all(n.endswith(SITE_EXT) for n in names) and any(
        n.endswith((".html", "tools.js", ".py", ".yml")) for n in names)


def _dest(name):
    n = _clean(name)
    b = os.path.basename(n)
    if b == "_redirects":
        return None
    if n.startswith(REPO_DIRS):        # v2.0: repo jaisa raasta ho to wahi (sub-folder bhi)
        return n
    if n in ROOT_OK:
        return n
    if b in ("index.js", "google.js", "wrangler.toml", "package.json"):
        return f"worker/{b}"
    if b.endswith(".py"):
        return f"scripts/{b}"
    if b.endswith(".yml"):
        return f".github/workflows/{b}"
    if b.endswith(".md"):
        return b if b == "README.md" else f"docs/{b}"
    return f"site/{b}"


def _new_pages_today(extra):
    d = str(datetime.date.today())
    c = state.get("site_new_pages") or {}
    return (c.get(d, 0) if isinstance(c, dict) else 0) + extra


def apply_zip(path, force=False):
    with ZIP_LOCK:                       # ek waqt mein ek ZIP (git takraav nahi)
        return _apply_zip(path, force)


def _apply_zip(path, force=False):
    """v2.0: file ki koi seema nahi (Telegram ki 20 MB seema ke andar), repo ke raaste surakshit, _redirects mana,
    tools.js badla to ginti sync khud, PEHLE audit - ERROR ho to kuch nahi chadhega. Ek din mein 10 se zyada NAYE page nahi."""
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return "❌ GitHub token nahi (website repo par likhne ki ijaazat wala token bhejein)"
    with zipfile.ZipFile(path) as z:
        files = [n for n in z.namelist() if not n.endswith("/")]
        if len(files) > MAX_FILES:
            return f"❌ ZIP mein {len(files)} file - seema {MAX_FILES}."
        sync()
        moved, new_pages = [], 0
        for n in files:
            d = _dest(n)
            if not d:
                return "❌ _redirects file mana hai (homepage tod deti hai)."
            if ".." in d.split("/"):
                return f"❌ Galat raasta: {n}"
            tgt = DIR / d
            if d.startswith("site/") and d.endswith(".html") and not tgt.exists():
                new_pages += 1
            tgt.parent.mkdir(parents=True, exist_ok=True)
            tgt.write_bytes(z.read(n))
            moved.append(d)
    if new_pages and _new_pages_today(new_pages) > NEW_PAGES_PER_DAY and not force:
        _git("checkout", "-q", "--", ".")
        _git("clean", "-qfd", "site", "scripts", "worker", ".github", "docs")
        return (f"⛔ Aaj {_new_pages_today(new_pages)} NAYE page ho jaate - Google scaled-content niyam (din mein max "
                f"{NEW_PAGES_PER_DAY}). Kal bhejein, ya sach mein zaroori ho to ZIP ke naam mein -force jodein.")
    if "site/tools.js" in moved and (DIR / "scripts" / "ginti_sync.py").exists():
        r = subprocess.run(["nice", "-n", "15", PY, "scripts/ginti_sync.py"], cwd=DIR, capture_output=True, text=True, timeout=600)
        changed = [l.split()[-1] for l in r.stdout.splitlines() if l.strip().endswith(".html")]
        out = subprocess.run(["git", "status", "--porcelain", "site"], cwd=DIR, capture_output=True, text=True).stdout
        moved = sorted(set(moved + [l[3:] for l in out.splitlines() if l[3:].startswith("site/")]))
        log(f"ginti sync: rc={r.returncode} {len(changed)}")
    ensure_node()
    r = subprocess.run(["nice", "-n", "15", PY, "scripts/audit.py"], cwd=DIR, env=_env(), capture_output=True,
                       text=True, timeout=900)
    rc = r.returncode
    if rc != 0 and not force:
        out = (r.stdout or "") + (("\n⚠️ " + r.stderr.strip()[-600:]) if r.stderr.strip() else "")
        if not out.strip():
            out = "audit.py ne kuch nahi likha (rc %d)" % rc
        _git("checkout", "-q", "--", ".")
        _git("clean", "-qfd", "site", "scripts", "worker", ".github", "docs")
        return "❌ Audit fail - kuch nahi chadhaya:\n" + out[-1200:]
    _git("add", *moved)
    _git("-c", "user.name=Sab Hisaab bot", "-c", "user.email=contact@sabhisaab.com", "commit", "-q", "-m",
         f"bot: {len(moved)} file ({datetime.date.today()})")
    gh_note = push_github()          # v2.0.2: GitHub band ho to bhi kaam nahi rukta - copy baad mein apne aap
    if new_pages:
        d = str(datetime.date.today())
        state.update("site_new_pages", lambda c: {d: (c or {}).get(d, 0) + new_pages}, {})
    diary.add("upload", f"website: {len(moved)} file chadhayi ({new_pages} naye page)")
    state.put("site_changed", sorted(set((state.get("site_changed") or []) + [m for m in moved if m.startswith("site/")])))
    warn = ""
    m = re.search(r"WARNING:\s*(\d+)", r.stdout or "")
    if m and int(m.group(1)):
        warn = f" (audit WARNING {m.group(1)} - '🛠 Website audit' mein dekhein)"
    if state.get("auto_deploy", True):
        state.put("deploy_due", time.time() + 15 * 60)       # aakhri ZIP ke 15 min baad khud deploy (beech mein aur ZIP aayi to aage)
        nxt = " 15 minute mein bot khud deploy karega (aur ZIP aayi to uske baad)."
    else:
        nxt = " Saari ZIP ho jayein to '🚀 Website deploy' dabayein."
    return f"✅ {len(moved)} file VM par chadh gayi (audit paas){warn}. {gh_note}{nxt}"


def push_github():
    """Website ki copy GitHub par. Fail ho to 'gh_pending' - har ghante bot khud dobara (deploy VM se chalta rehta hai)."""
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        state.put("gh_pending", True)
        return "(GitHub token nahi - copy baad mein)"
    url = f"https://x-access-token:{tok}@github.com/{REPO}.git"
    for i in range(3):
        try:
            _git("push", "-q", url, "HEAD:main", timeout=300)
            state.put("gh_pending", False)
            return "GitHub copy ✅."
        except Exception as e:
            if i == 2:
                state.put("gh_pending", True)
                log(f"github push: {e}")
                return "(GitHub abhi nahi mila - copy bot khud baad mein bhejega)"
            try:
                _git("pull", "-q", "--rebase", "--autostash", url, "main", timeout=300)
            except Exception:
                pass


def _cf():
    e = _env()
    return e.get("CLOUDFLARE_API_TOKEN"), e.get("CLOUDFLARE_ACCOUNT_ID")


def _npm_tools():
    """VM par jsdom (calculator test) + wrangler (seedha Cloudflare deploy) - ek baar, data/node_tools mein."""
    t = DATA / "node_tools"
    if (t / "node_modules" / "jsdom").exists() and (t / "node_modules" / "wrangler").exists():
        return t
    t.mkdir(parents=True, exist_ok=True)
    if not (t / "package.json").exists():
        (t / "package.json").write_text('{"name":"sn-tools","private":true}')
    r = subprocess.run(["nice", "-n", "15", "npm", "install", "--no-audit", "--no-fund", "-q", "jsdom@24.1.3", "wrangler@3"],
                       cwd=t, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise RuntimeError("npm install nahi hua: " + (r.stderr or r.stdout)[-300:])
    return t


def deploy_direct():
    """v2.0: VM se seedha Cloudflare Pages (GitHub Actions ki zaroorat nahi). audit -> calculator test -> wrangler ->
    Google sitemap (API) -> sirf badle URL IndexNow. GitHub sirf code ki copy rehta hai."""
    tokc, acc = _cf()
    sync()
    if not ensure_node():
        return "❌ node nahi mila - seedha deploy nahi ho sakta (GitHub Actions wala raasta chalega)"
    t = _npm_tools()
    env = {**_env(), "NODE_PATH": str(t / "node_modules"), "CLOUDFLARE_API_TOKEN": tokc, "CLOUDFLARE_ACCOUNT_ID": acc}
    r = subprocess.run(["nice", "-n", "15", PY, "scripts/audit.py"], cwd=DIR, env=env, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        return "❌ Audit fail - deploy roka:\n" + (r.stdout or r.stderr)[-1000:]
    if (DIR / "scripts" / "calc_test.py").exists():
        r = subprocess.run(["nice", "-n", "15", PY, "scripts/calc_test.py", "site"], cwd=DIR, env=env, capture_output=True,
                           text=True, timeout=1800)
        if r.returncode != 0:
            return "❌ Calculator test fail - deploy roka:\n" + (r.stdout + r.stderr)[-1000:]
    r = subprocess.run(["nice", "-n", "15", str(t / "node_modules" / ".bin" / "wrangler"), "pages", "deploy", "site",
                        "--project-name=sabhisaab", "--branch=main", "--commit-dirty=true"],
                       cwd=DIR, env=env, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        return "❌ Cloudflare deploy fail:\n" + (r.stdout + r.stderr).replace(tokc or "#", "***")[-800:]
    msg = ["✅ Website LIVE (VM se seedha Cloudflare)."]
    msg.append(submit_sitemap())
    msg.append(_after_live())
    return " ".join(x for x in msg if x)


def submit_sitemap():
    """Google Search Console ko sitemap (API, Google ka jaayaz tareeka)."""
    if not SA.exists():
        return ""
    try:
        tk = _gcreds("https://www.googleapis.com/auth/webmasters")
        u = "https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Asabhisaab.com/sitemaps/" + \
            requests.utils.quote(SITE + "/sitemap.xml", safe="")
        r = requests.put(u, headers={"Authorization": f"Bearer {tk}"}, timeout=30)
        return "Google sitemap ✅" if r.status_code in (200, 204) else f"Google sitemap HTTP {r.status_code}"
    except Exception as e:
        return f"Google sitemap: {str(e)[:80]}"


def _after_live():
    ch = state.get("site_changed") or []
    urls = [f"{SITE}/{os.path.basename(p)[:-5]}" for p in ch if p.endswith(".html")]
    urls = [SITE + "/" if u.endswith("/index") else u for u in urls]
    try:
        sm = (DIR / "site" / "sitemap.xml").read_text(encoding="utf-8")
        urls = [u for u in urls if f"<loc>{u}</loc>" in sm or u == SITE + "/"]
    except Exception:
        pass
    state.put("site_changed", [])
    try:
        from . import siteknow
        siteknow.refresh(notify=True)
    except Exception as e:
        log(f"siteknow after deploy: {e}")
    return indexnow(urls, "deploy")


def deploy():
    """v2.0.1: Cloudflare token VM par ho to seedha VM se; warna GitHub Actions deploy.yml (IndexNow 'koi-nahi')."""
    if all(_cf()):
        try:
            return deploy_direct()
        except Exception as e:
            log(f"direct deploy: {e}")
            tg.say(f"⚠️ Seedha deploy nahi hua ({str(e)[:120]}), GitHub Actions se koshish...")
    if state.get("gh_pending"):
        push_github()
        if state.get("gh_pending"):          # GitHub par purani copy hai - usse deploy galat hoga; 30 min baad dobara
            state.put("deploy_due", time.time() + 1800)
            return "⏳ GitHub abhi nahi mil raha, isliye deploy 30 min baad khud. (Cloudflare token bhej dein to GitHub ki zaroorat hi nahi)"
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return "❌ GitHub token nahi - deploy shuru nahi ho sakta"
    h = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}
    started = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=20)
    r = requests.post(f"https://api.github.com/repos/{REPO}/actions/workflows/deploy.yml/dispatches", headers=h,
                      timeout=30, json={"ref": "main", "inputs": {"indexnow": "koi-nahi"}})
    if r.status_code != 204:
        return f"❌ Deploy shuru nahi hua ({r.status_code}): {r.text[:150]}"
    tg.say("🚀 Deploy shuru (audit → calculator test → Cloudflare → Google sitemap). 3-6 minute...")
    for _ in range(40):
        time.sleep(20)
        runs = requests.get(f"https://api.github.com/repos/{REPO}/actions/workflows/deploy.yml/runs", headers=h,
                            params={"per_page": 5, "event": "workflow_dispatch"}, timeout=30).json().get("workflow_runs", [])
        runs = [x for x in runs if datetime.datetime.fromisoformat(x.get("created_at", "1970-01-01T00:00:00Z")
                                                                  .replace("Z", "+00:00")) >= started]
        runs.sort(key=lambda x: x.get("created_at", ""))
        if runs and runs[0].get("status") == "completed":
            if runs[0].get("conclusion") == "success":
                return "✅ Website LIVE. " + _after_live()
            return f"❌ Deploy fail: {runs[0].get('html_url')}"
    return "⏳ Deploy abhi chal raha hai, GitHub Actions mein dekhein."


def disable_old_crons():
    """Purane GitHub-Actions cron (report/chowkidar) band - ab ye kaam VM bot karta hai (double report nahi)."""
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return "GitHub token nahi"
    h = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}
    res = []
    for wf in OLD_CRONS:
        r = requests.put(f"https://api.github.com/repos/{REPO}/actions/workflows/{wf}/disable", headers=h, timeout=30)
        res.append(f"{wf}:{'band' if r.status_code in (204, 404) else r.status_code}")
    ok = all(":band" in x for x in res)
    state.put("old_crons_off", ok)
    return ("✅ Purane GitHub cron band: " if ok else "⚠️ Kuch cron band nahi hue (token ko 'Actions: write' chahiye): ") + ", ".join(res)


# ---------------- v1.5: asli traffic (GA4 + GSC) aur website ki file ----------------
def _gcreds(scope):
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    c = service_account.Credentials.from_service_account_file(str(SA), scopes=[scope])
    c.refresh(Request())
    return c.token


def traffic(days=1):
    """Website par kitne log aaye, kahan se (YouTube/Instagram/Facebook/Threads/Pinterest/Google...), kaunse page."""
    if not SA.exists():
        return "🔑 Website ki Google service account file abhi bot ke paas nahi (🧾 Mere kaam dekhein)."
    tok = _gcreds("https://www.googleapis.com/auth/analytics.readonly")
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY}:runReport"
    h = {"Authorization": f"Bearer {tok}"}
    rng = [{"startDate": "today" if days == 1 else f"{days}daysAgo", "endDate": "today"}]

    def rep(dim, n=8):
        j = requests.post(url, headers=h, timeout=60, json={
            "dateRanges": rng, "dimensions": [{"name": dim}],
            "metrics": [{"name": "activeUsers"}, {"name": "screenPageViews"}],
            "orderBys": [{"metric": {"metricName": "activeUsers"}, "desc": True}], "limit": n}).json()
        if "error" in j:
            raise RuntimeError(j["error"].get("message", "")[:150])
        return [(r["dimensionValues"][0]["value"], int(r["metricValues"][0]["value"]), int(r["metricValues"][1]["value"]))
                for r in j.get("rows", [])]
    src = rep("sessionSource")
    camp = [x for x in rep("sessionCampaignName") if x[0] not in ("(not set)", "(direct)", "(organic)", "(referral)")]
    pages = rep("pagePath", 6)
    users = sum(x[1] for x in src)
    lines = [f"🌐 sabhisaab.com ({'aaj' if days == 1 else f'pichhle {days} din'}): {users} log, "
             f"{sum(x[2] for x in src)} page dekhe",
             "📍 Kahan se aaye: " + ", ".join(f"{s} {u}" for s, u, _ in src[:8])]
    if camp:
        lines.append("🔗 Hamare link se (brand): " + ", ".join(f"{c} {u}" for c, u, _ in camp[:6]))
    lines.append("📄 Sabse zyada dekhe page: " + ", ".join(f"{p} ({v})" for p, _, v in pages))
    try:
        gt = _gcreds("https://www.googleapis.com/auth/webmasters.readonly")
        import datetime as _d
        e = _d.date.today() - _d.timedelta(days=2)
        j = requests.post("https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Asabhisaab.com/searchAnalytics/query",
                          headers={"Authorization": f"Bearer {gt}"}, timeout=60,
                          json={"startDate": str(e - _d.timedelta(days=6)), "endDate": str(e), "rowLimit": 1}).json()
        tot = requests.post("https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Asabhisaab.com/searchAnalytics/query",
                            headers={"Authorization": f"Bearer {gt}"}, timeout=60,
                            json={"startDate": str(e - _d.timedelta(days=6)), "endDate": str(e)}).json()
        r = (tot.get("rows") or [{}])[0]
        lines.append(f"🔎 Google search (7 din): {int(r.get('clicks', 0))} click, {int(r.get('impressions', 0))} baar dikha")
    except Exception as ex:
        log(f"gsc traffic: {ex}")
    return "\n".join(lines)


def find_files(name):
    """Website repo + is bot ka code + aapki photo/video gallery - sab jagah naam se khojo."""
    sync()
    name = name.lower().strip().replace(" ", "-")
    roots = [DIR, BASE / "app", DATA / "photos", DATA / "clips", DATA / "inbox"]
    hits = []
    for r in roots:
        if r.exists():
            hits += [p for p in r.rglob("*") if p.is_file() and ".git" not in p.parts and name in p.name.lower()]
    return hits[:30]


def send_files(name):
    """Website ki koi bhi file (ya poori site ZIP) Telegram par."""
    hits = [DIR / "site"] if name.lower() in ("site", "website", "poori site", "sab") else find_files(name)
    if not hits:
        return "Ye file website mein nahi mili. Naam ka hissa likhein, jaise 'emi' ya 'tools.js'."
    out = DATA / "site_send.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for h_ in hits:
            for f in ([h_] if h_.is_file() else [x for x in h_.rglob("*") if x.is_file()]):
                try:
                    z.write(f, f.relative_to(DIR))
                except ValueError:
                    z.write(f, f.name)
    nice = DATA / f"sabhisaab-{''.join(c for c in name if c.isalnum() or c in '-_')[:30] or 'files'}.zip"
    out.replace(nice)
    with open(nice, "rb") as f:          # (pehle tuple bhejne se 'seek' galti aati thi)
        tg.call("sendDocument", {"chat_id": tg._chat(), "caption": f"📁 {len(hits)} file/folder: {name}"[:200]},
                {"document": f})
    nice.unlink(missing_ok=True)
    return None


# ---------------- v2.0: GitHub par sirf zaroori/taaza ----------------
OBSOLETE = ["worker", ".github/workflows/bot.yml", ".github/workflows/daily.yml", ".github/workflows/watch.yml",
            ".github/workflows/pending.yml", ".github/workflows/health.yml", ".github/workflows/notify.yml",
            ".github/workflows/ping.yml", "setup.sh", "config.example.json"]


def remove_obsolete():
    """Purane Cloudflare-Worker bot ka code + band cron workflow repo se hatao (deploy.yml, audit.yml, ginti.yml rehte hain)."""
    tok = os.environ.get("GITHUB_TOKEN")
    sync()
    gone = [p for p in OBSOLETE if (DIR / p).exists()]
    if not gone:
        return "✅ Purani file pehle hi hat chuki hain."
    _git("rm", "-r", "-q", *gone)
    _git("-c", "user.name=Sab Hisaab bot", "-c", "user.email=contact@sabhisaab.com", "commit", "-q", "-m",
         "bot: purane Worker bot aur band cron hataye (kaam ab VM bot karta hai)")
    _git("push", "-q", f"https://x-access-token:{tok}@github.com/{REPO}.git", "HEAD:main", timeout=300)
    diary.add("setting", f"website repo se purani file hatayi: {', '.join(gone)}")
    return "🧹 Hataya: " + ", ".join(gone)


def squash_history():
    """GitHub par website repo ki puraani history hata kar sirf aaj ki taaza copy (1 commit). Site par koi asar nahi."""
    tok = os.environ.get("GITHUB_TOKEN")
    sync()
    _git("checkout", "-q", "--orphan", "sn-latest")
    _git("add", "-A")
    _git("rm", "--cached", "-q", "--ignore-unmatch", "config.json", "state.json")   # secret kabhi GitHub par nahi
    _git("-c", "user.name=Sab Hisaab bot", "-c", "user.email=contact@sabhisaab.com", "commit", "-q", "-m",
         f"Sab Hisaab - taaza copy ({datetime.date.today()})")
    _git("push", "-q", "-f", f"https://x-access-token:{tok}@github.com/{REPO}.git", "sn-latest:main", timeout=600)
    shutil.rmtree(DIR, ignore_errors=True)
    sync()
    diary.add("setting", "website GitHub history saaf (sirf taaza copy)")
    return "✅ GitHub par ab sirf taaza copy (1 commit). Site/deploy par koi asar nahi."


def tick_auto():
    """Scheduler se har minute: (1) pending GitHub copy dobara (har ghante) (2) ZIP ke 15 min baad auto deploy."""
    out = []
    if state.get("gh_pending") and time.time() - (state.get("gh_try_at") or 0) > 3600:
        state.put("gh_try_at", time.time())
        out.append(("gh", push_github))
    due = state.get("deploy_due")
    if due and time.time() >= due:
        state.put("deploy_due", 0)
        out.append(("deploy", deploy))
    return out


# ---------------- v2.0.6: redirect jaanch (GSC 'Redirect error' dobara kabhi na aaye) ----------------
def redirect_check(limit=400):
    """Har page ke purane roop (.html, aakhir mein /) ko jaancho: ek hi hop mein saaf URL par 200 aana chahiye.
    Loop / 2+ hop / galat jagah / 4xx-5xx = galti. Nateeja state.redirect_check (HEALTH.md + doctor)."""
    from . import siteknow
    pg = list(siteknow.pages().keys())[:limit]
    bad, ok = [], 0
    s = requests.Session()
    for slug in pg:
        if slug in ("index", "404") or slug.startswith("google"):
            continue
        for old in (f"{SITE}/{slug}.html", f"{SITE}/{slug}/"):
            url, hops, seen = old, 0, set()
            try:
                while hops < 5:
                    r = s.get(url, allow_redirects=False, timeout=20)
                    if r.status_code in (301, 302, 307, 308):
                        nxt = requests.compat.urljoin(url, r.headers.get("Location", ""))
                        if nxt in seen:
                            raise RuntimeError("loop")
                        seen.add(nxt)
                        url, hops = nxt, hops + 1
                        continue
                    break
                want = f"{SITE}/{slug}"
                if r.status_code != 200 or url.rstrip("/") != want or hops > 1:
                    bad.append(f"{old} → {url} ({r.status_code}, {hops} hop)")
                else:
                    ok += 1
            except Exception as e:
                bad.append(f"{old}: {str(e)[:60]}")
            time.sleep(0.3)
    state.put("redirect_check", {"t": str(datetime.date.today()), "ok": ok, "bad": bad[:50]})
    return ok, bad


# ---------------- v2.0.6: website page par usi vishay ki video (channel <-> website jod) ----------------
def publish_videos():
    """history (page -> sabse nayi YouTube video) se site/videos.json. Badla ho tabhi ZIP -> audit -> GitHub -> auto deploy.
    Page par install-app.js 'Is hisaab ki video' dikhata hai (sirf link, embed nahi - speed par asar nahi)."""
    import hashlib
    from .config import BRANDS
    hist = state.get("history") or []
    m = {}
    for h in hist:
        pg = (h.get("page") or "/").split("?")[0]
        if not pg or pg == "/" or not h.get("vid"):
            continue
        m[pg] = {"v": h["vid"], "t": (h.get("title") or "")[:90], "c": BRANDS.get(h.get("brand"), {}).get("name", ""),
                 "h": h.get("brand", ""), "d": h.get("date", "")}
    if not m:
        return "videos.json: abhi koi page-wali video nahi"
    body = json.dumps(m, ensure_ascii=False, sort_keys=True)
    dig = hashlib.md5(body.encode()).hexdigest()
    if state.get("videos_json_hash") == dig:
        return "videos.json: koi badlaav nahi"
    z = DATA / "videos-json.zip"
    with zipfile.ZipFile(z, "w") as zz:
        zz.writestr("site/videos.json", body)
    r = apply_zip(z, force=True)
    z.unlink(missing_ok=True)
    if "❌" not in str(r):
        state.put("videos_json_hash", dig)
    return f"videos.json ({len(m)} page): {str(r)[:120]}"
