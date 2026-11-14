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
    (DIR / "config.json").chmod(0o600)          # v2.1.2: isme bot token hai (audit: 644 tha)


def _detoken():
    """v2.1.9: .git/config mein GitHub token na rahe (backup/export/Chowkidar ke raaste leak ho sakta tha). Repo public hai -
    fetch bina token chalta hai; push ke waqt token URL mein alag se jaata hai (jaise pehle)."""
    try:
        clean = f"https://github.com/{REPO}.git"
        cur = subprocess.run(["git", "remote", "get-url", "origin"], cwd=DIR, capture_output=True, text=True, timeout=30).stdout.strip()
        if cur != clean:
            subprocess.run(["git", "remote", "set-url", "origin", clean], cwd=DIR, capture_output=True, timeout=30)
    except Exception as e:
        log(f"detoken: {str(e)[:80]}")


def sync():
    """Repo ki taaza copy (code), par bot ki yaaddasht (state/) surakshit."""
    if not (DIR / ".git").exists():
        DIR.parent.mkdir(parents=True, exist_ok=True)
        tok = os.environ.get("GITHUB_TOKEN")
        url = f"https://x-access-token:{tok}@github.com/{REPO}.git" if tok else f"https://github.com/{REPO}.git"
        r = subprocess.run(["git", "clone", "-q", "--depth", "20", url, str(DIR)], capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError("Website repo clone nahi hua: " + r.stderr[-200:].replace(tok or "#", "***"))
        _detoken()
    else:
        _detoken()
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
    wait = max(0, int((hold_until or 0) - time.time()))          # v2.3.6: report 8 baje tak rukti hai - wo samay bhi jodo
    rc, out = run_script("scripts/daily.py", timeout=4200 + wait,   # (pehle 06:10 + 70 min = 07:20 par beech mein maar deta tha)
                         extra_env={"TG_HOLD_UNTIL": str(int(hold_until))} if hold_until else None)
    if rc != 0:
        tg.alert("yellow", f"Website ki roz ki report mein dikkat:\n{out[-400:]}")
    try:                                          # v3.2.0 (owner): Bing ki report bhi GSC ke saath, usi samay
        if hold_until and time.time() < hold_until:
            time.sleep(max(0, hold_until - time.time()))
        tg.say(bing_report())
    except Exception as e:
        log(f"bing report: {e}")


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
ILOG = DATA / "indexnow_log.jsonl"          # v2.1.5: HAMESHA ka record (kab, kaunsa URL, Bing ka jawab) - kabhi na bhoole


def _ilog(urls, code, reason):
    try:
        with open(ILOG, "a", encoding="utf-8") as f:
            for u in urls:
                f.write(json.dumps({"t": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "url": u, "code": code,
                                    "why": reason[:60]}, ensure_ascii=False) + "\n")
        from . import updater
        updater.mark_dirty()
    except Exception as e:
        log(f"indexnow log: {e}")


def indexnow_rows():
    try:
        return [json.loads(x) for x in ILOG.read_text(encoding="utf-8").splitlines() if x.strip()]
    except Exception:
        return []


def indexnow_text():
    rows = [r for r in indexnow_rows() if not str(r.get("why", "")).startswith("bing-api")]   # v3.2.0: Bing API alag ginti
    ok = [r for r in rows if r.get("code") in (200, 202)]
    today = str(datetime.date.today())
    week = str(datetime.date.today() - datetime.timedelta(days=7))
    last = rows[-1] if rows else {}
    return (f"📮 IndexNow (Bing/Yandex ko naye page ki khabar): kul {len(ok)} URL bheje | aaj "
            f"{sum(1 for r in ok if r['t'][:10] == today)} | 7 din {sum(1 for r in ok if r['t'][:10] >= week)} | "
            f"aakhri: {last.get('t', '-')} {last.get('url', '')[len(SITE):][:50]} ({last.get('code', '-')})\n"
            "Niyam: IndexNow sirf badle/naye page, din mein max 10, ek URL 14 din mein ek baar. Bing Webmaster API alag: roz max 30 (quota ka 1/3), pehle index-nahi page (v2.6.0).")


def sent_today_text(day=None):
    """v3.3.2 audit-5 (owner 3 Nov: 'kal kitne bheje, kaun kaun se page' - bot ne kaha record nahi): aaj/kal bheje URL ke naam.
    Record indexnow_log.jsonl se (IndexNow + Bing API dono, 'why' se alag)."""
    rows = [r for r in indexnow_rows() if r.get("code") in (200, 202)]
    days = [day] if day else [str(datetime.date.today()), str(datetime.date.today() - datetime.timedelta(days=1))]
    out = []
    for d in days:
        rr = [r for r in rows if r.get("t", "")[:10] == d]
        if not rr:
            out.append(f"{d}: koi URL nahi bheja")
            continue
        api = [r for r in rr if str(r.get("why", "")).startswith("bing-api")]
        inx = [r for r in rr if r not in api]
        out.append(f"{d}: IndexNow {len(inx)} + Bing API {len(api)} = {len(rr)}")
        out += [f"  • {r['url'][len(SITE):] or '/'}" + (" (Bing API)" if r in api else "") for r in rr[:30]]
    return "🗂 Bheje gaye page (record: indexnow_log):\n" + "\n".join(out)


def indexing_md():
    """docs/INDEXING.md - GitHub par hamesha: kab kaunsa page Bing/Google ko bheja (koi secret nahi)."""
    rows = indexnow_rows()
    lines = ["# INDEXING - kaunsa page kab search engine ko bheja (bot khud likhta hai, purana kabhi nahi mitta)",
             f"Updated: {datetime.datetime.now():%Y-%m-%d %H:%M} IST | kul {len(rows)} entry", "",
             "Niyam: IndexNow sirf badle/naye URL, din mein max 10, ek URL 14 din mein ek baar. Bulk kabhi nahi. "
             "Bing Webmaster API (v2.6.0): roz max 30 (quota ka 1/3), kram: Google-index-nahi > Bing-crawl-nahi > naya/badla > crawl-hua-par-Bing-index-nahi (30 din mein 1 baar, v3.2.0); Bing-index wale bina badle dobara NAHI; ek URL 14/30 din mein ek baar.", "",
             "| Samay | Page | Jawab | Kyun |", "|---|---|---|---|"]
    lines += [f"| {r['t']} | {r['url'][len(SITE):] or '/'} | {r['code']} | {r.get('why', '')} |" for r in reversed(rows[-300:])]
    gsc = state.get("gsc_requested") or {}
    if gsc:
        lines += ["", "## Google (GSC Request Indexing, owner ke haath)"] + [f"- {k}: {v}" for k, v in list(gsc.items())[-50:]]
    return "\n".join(lines) + "\n"
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
    _ilog(fresh, r.status_code, reason)
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


def apply_zip(path, force=False, deploy_in=15):
    with ZIP_LOCK:                       # ek waqt mein ek ZIP (git takraav nahi)
        return _apply_zip(path, force, deploy_in)


def _apply_zip(path, force=False, deploy_in=15):
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
    try:                                 # v3.1.2 (12 Nov: owner ne W11 ZIP do baar bheji -> 'nothing to commit' ka laal ZAROORI alert aaya):
        chg = subprocess.run(["git", "status", "--porcelain", "--", *moved], cwd=DIR, capture_output=True, text=True, timeout=60)
        if chg.returncode == 0 and not chg.stdout.strip():
            return ("ℹ️ Ye ZIP pehle se lagi hui hai - iski koi file website ki abhi ki file se alag nahi. Kuch nahi badla, "
                    "dobara bhejne ki zaroorat nahi.")
    except Exception as e:
        log(f"zip already-applied check: {e}")
    try:                                 # v3.1.0: page ki apni 'dateModified' = sitemap lastmod (ZIP mein sitemap bhejne ki zaroorat nahi)
        if sync_lastmod(moved):
            moved = sorted(set(moved + ["site/sitemap.xml"]))
    except Exception as e:
        log(f"lastmod sync: {e}")
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
        state.put("deploy_due", time.time() + deploy_in * 60)  # aakhri ZIP ke baad khud deploy (v2.9.2: /jawab ke liye 1 min)
        nxt = f" {deploy_in} minute mein bot khud deploy karega (aur ZIP aayi to uske baad)."
    else:
        nxt = " Saari ZIP ho jayein to '🚀 Website deploy' dabayein."
    return f"✅ {len(moved)} file VM par chadh gayi (audit paas){warn}. {gh_note}{nxt}"


def sync_lastmod(moved, root=None):
    """v3.1.0: ZIP se badle har site/<page>.html ki JSON-LD 'dateModified' ko sitemap ke usi URL ke <lastmod> mein likho (sirf jab alag ho
    aur sitemap khud ZIP mein na ho). Tareekh page se hi aati hai - bot khud koi nayi tareekh nahi gadhta (fake taazgi nahi). -> badle URL ki ginti"""
    root = root or DIR
    if "site/sitemap.xml" in moved:
        return 0
    smf = root / "site" / "sitemap.xml"
    if not smf.exists():
        return 0
    sm = smf.read_text(encoding="utf-8")
    n = 0
    for p in moved:
        if not (p.startswith("site/") and p.endswith(".html")) or "/" in p[5:]:
            continue
        f = root / p
        if not f.exists():
            continue
        m = re.search(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})', f.read_text(encoding="utf-8", errors="ignore"))
        if not m:
            continue
        slug = p[5:-5]
        loc = SITE + "/" + ("" if slug == "index" else slug)
        rx = re.compile(r"(<loc>" + re.escape(loc) + r"</loc>\s*<lastmod>)(\d{4}-\d{2}-\d{2})")
        mm = rx.search(sm)
        if mm and mm.group(2) != m.group(1):
            sm = rx.sub(lambda x: x.group(1) + m.group(1), sm, count=1)
            n += 1
    if n:
        smf.write_text(sm, encoding="utf-8")
    return n


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


BOT_PAGES = ("site/jawab.html",)       # jo page bot khud banata hai (baaki site owner/dev ka - bot unhe kabhi nahi hatata)


def bot_page_errors(audit_out, pages=BOT_PAGES):
    """audit ke ERROR lines jin mein SIRF bot ke page ka naam hai -> unki list. Koi ERROR line kisi aur file ki ho to [] (kuch nahi hatega)."""
    errs = [l for l in (audit_out or "").splitlines() if "ERROR" in l.upper()]
    if not errs:
        return []
    names = [p for p in pages if any(os.path.basename(p) in l or p in l or os.path.basename(p)[:-5] in l for l in errs)]
    others = [l for l in errs if not any(os.path.basename(p) in l or p in l or os.path.basename(p)[:-5] in l for p in pages)]
    return names if names and not others else []


def _quarantine_bot_pages(audit_out):
    """Sirf bot ke page par audit ERROR ho to wo file data/quarantine mein, repo se commit karke hatao (taaki sync() wapas na laye),
    aur page dobara banne ke liye answer_dirty. Baaki website deploy ho jaati hai. Telegram par poora error."""
    bad = bot_page_errors(audit_out)
    if not bad:
        return []
    qd = DATA / "quarantine"
    qd.mkdir(parents=True, exist_ok=True)
    for f in bad:
        src = DIR / f
        if src.exists():
            shutil.copy2(src, qd / (os.path.basename(f) + "." + str(int(time.time()))))
            _git("rm", "-q", "-f", f)
    _git("-c", "user.name=Sab Hisaab bot", "-c", "user.email=contact@sabhisaab.com", "commit", "-q", "-m",
         "bot: quarantine " + ", ".join(bad))
    push_github()
    state.put("jawab_hash", "")
    state.put("answer_dirty", True)
    state.put("jawab_pub_at", 0)
    tg.alert("yellow", "Bot ka page quarantine hua (baaki website deploy hogi):\n" + ", ".join(bad) + "\n" + (audit_out or "")[-700:])
    return bad


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
        q = _quarantine_bot_pages(r.stdout or "")       # v2.5.2: bot ka bana page poore deploy ko na roke
        if q:
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
    try:
        from . import canary
        msg.append(canary.after_deploy())          # v2.5.2: soft-404 / asli text / sitemap jaanch (deploy ko nahi rokta)
    except Exception as e:
        log(f"canary: {e}")
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


def _ga_help(err):
    """GA4 ki galti ko owner ke kaam mein badlo (link ke saath). Secret nahi - sirf project number / service account email."""
    import re as _re
    try:
        email = json.loads(SA.read_text()).get("client_email", "")
    except Exception:
        email = ""
    if email and email != OLD_SA:
        state.put("ga_need", {"kind": "sa", "email": email})
        return google_check()
    m = _re.search(r"project (\d{6,})", err)
    if m or "has not been used" in err or "disabled" in err.lower():
        link = f"https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com?project={m.group(1)}" if m else \
            "https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com"
        state.put("ga_need", {"kind": "api", "link": link})
        return ("🔑 Website traffic abhi nahi padh pa raha: Google Analytics Data API band hai.\n"
                f"1) Ye link kholein (wahi Google account): {link}\n2) 'Enable' dabayein\n"
                "3) 5 minute baad bot mein likhein: 'website traffic'")
    if email != OLD_SA:          # v2.1.6: asli kaaran restore mein nayi service account - seedha sahi ilaaj do
        state.put("ga_need", {"kind": "sa", "email": email})
        return google_check()
    if "permission" in err.lower() or "403" in err:
        state.put("ga_need", {"kind": "access", "email": email})
        return ("🔑 Website traffic: bot ke service account ko GA4 dekhne ki ijaazat nahi.\n"
                "1) analytics.google.com → neeche ⚙️ Admin → Property access management → ➕ → Add users\n"
                f"2) Email: {email}\n3) Role: Viewer → Add\n4) 5 minute baad: 'website traffic'")
    return f"❌ Website traffic nahi aaya: {err[:200]}"


OUR_SOURCES = ("youtube", "facebook", "instagram", "threads", "pinterest", "telegram", "whatsapp", "t.me", "l.facebook.com",
               "m.facebook.com", "lm.facebook.com", "youtube.com", "m.youtube.com", "l.instagram.com", "pinterest.com", "threads.net")
OUR_CAMPAIGNS = ("sunonatak", "money", "deals", "pahadi", "demo", "jawab", "hub")


def _plat(src):
    s = (src or "").lower()
    for k, v in (("youtube", "YouTube"), ("youtu", "YouTube"), ("facebook", "Facebook"), ("instagram", "Instagram"),
                 ("threads", "Threads"), ("pinterest", "Pinterest"), ("pin.it", "Pinterest"), ("telegram", "Telegram"),
                 ("t.me", "Telegram"), ("whatsapp", "WhatsApp"), ("wa.me", "WhatsApp")):
        if k in s:
            return v
    return ""


def link_rows_split(rows):
    """rows: [(source, medium, campaign, content, users)] -> (platform->users, brand->users, code->users). Bina network (test)."""
    plat, brand, code = {}, {}, {}
    for src, med, camp, cont, u in rows:
        p = _plat(src)
        ours = bool(p) or (camp or "").lower() in OUR_CAMPAIGNS
        if not ours or (med or "").lower() == "organic":
            continue
        p = p or "Doosra (hamara link)"
        plat[p] = plat.get(p, 0) + u
        if (camp or "").lower() in OUR_CAMPAIGNS:
            brand[camp.lower()] = brand.get(camp.lower(), 0) + u
        m = re.match(r"c(\d{3,6})$", (cont or "").strip())
        if m:
            code["#" + m.group(1)] = code.get("#" + m.group(1), 0) + u
    return plat, brand, code


def link_traffic(start="yesterday", end="yesterday", label="kal (pakka)"):
    """v2.6.0 (owner: 'video se kitne log aaye nahi dikhta'): sirf HAMARE link (video/post/Telegram/WhatsApp/Pinterest) se
    aaye log - platform-wise, brand-wise, reel-code-wise. GA4 'aaj' ka data adhoora hota hai, isliye kal ka pakka bhi."""
    if not SA.exists():
        return ""
    tok = _gcreds("https://www.googleapis.com/auth/analytics.readonly")
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY}:runReport"
    dims = [{"name": "sessionSource"}, {"name": "sessionMedium"}, {"name": "sessionCampaignName"}, {"name": "sessionManualAdContent"}]
    j = requests.post(url, headers={"Authorization": f"Bearer {tok}"}, timeout=60, json={
        "dateRanges": [{"startDate": start, "endDate": end}], "dimensions": dims,
        "metrics": [{"name": "activeUsers"}], "limit": 200}).json()
    if "error" in j:                               # v2.8.2: utm_content wala dimension na chale to uske bina (khaali jawab nahi)
        log(f"link_traffic: {j['error'].get('message', '')[:200]}")
        j = requests.post(url, headers={"Authorization": f"Bearer {tok}"}, timeout=60, json={
            "dateRanges": [{"startDate": start, "endDate": end}], "dimensions": dims[:3],
            "metrics": [{"name": "activeUsers"}], "limit": 200}).json()
        if "error" in j:
            raise RuntimeError(j["error"].get("message", "")[:300])
        for r in j.get("rows", []):
            r["dimensionValues"].append({"value": ""})
    state.put("ga_data_ok", time.time())                  # v2.6.2: GA Data API chalu hai (pending ka 'ga4' kaam khud band)
    rows = [(r["dimensionValues"][0]["value"], r["dimensionValues"][1]["value"], r["dimensionValues"][2]["value"],
             r["dimensionValues"][3]["value"], int(r["metricValues"][0]["value"])) for r in j.get("rows", [])]
    plat, brand, code = link_rows_split(rows)
    tot = sum(plat.values())
    L = [f"🔗 Hamare video/post ke link se ({label}): {tot} log"]
    if plat:
        L.append("   Platform: " + ", ".join(f"{k} {v}" for k, v in sorted(plat.items(), key=lambda x: -x[1])))
    if brand:
        L.append("   Brand: " + ", ".join(f"{k} {v}" for k, v in sorted(brand.items(), key=lambda x: -x[1])))
    if code:
        L.append("   Reel code: " + ", ".join(f"{k} {v}" for k, v in sorted(code.items(), key=lambda x: -x[1])[:8]))
    return "\n".join(L)


LINK_TRUTH = ("ℹ️ Sach: YouTube Shorts ki description/comment ke link click nahi hote (YouTube ka niyam, 2023 se), Instagram "
              "caption mein bhi nahi. Isliye Shorts se seedha traffic bahut kam aata hai. Click hone wale raaste: lambi video ki "
              "description, Shorts ka 'Related video', channel ke Links, Telegram/WhatsApp/Facebook/Threads/Pinterest post. "
              "Telegram/WhatsApp ke andar khule link kabhi-kabhi GA4 mein '(direct)' gine jaate hain.")


def traffic_smart():
    """v2.3.6 + v2.6.0: aaj (adhoora) + kal (pakka) + 7 din - aur alag se 'hamare link se kitne aaye' + sachai."""
    t1 = traffic(1)
    if "(aaj): 0 log" in t1 or "aaj): 0 log" in t1:
        try:
            t1 += "\n\n📅 Pichhle 7 din (pakka gina hua):\n" + traffic(7)
        except Exception:
            pass
    extra = []
    for st, en, lb in (("yesterday", "yesterday", "kal, pakka"), ("7daysAgo", "yesterday", "7 din")):
        try:
            x = link_traffic(st, en, lb)
            if x:
                extra.append(x)
        except Exception as e:
            log(f"link_traffic: {e}")
    try:
        extra.insert(0, traffic_trend())          # v2.9.9: 15-din ausat se tulna sabse upar
    except Exception as e:
        log(f"traffic trend: {e}")
    try:                          # v2.8.2 ('sabka lagakar kitna?' par sirf 'aaj 1 log' aaya tha): 7 din ka kul hamesha upar
        tot = _ga_total("7daysAgo", "today")
        if tot is not None:
            prev = _ga_total("14daysAgo", "8daysAgo")      # v2.9.8 (owner: 'badh raha ya ghat raha, din ka ausat'): pichhle hafte se tulna
            trend = ""
            if prev is not None:
                d_ = tot[0] - prev[0]
                trend = (f" | pichhla hafta {prev[0]} log → {'📈 badha' if d_ > 0 else '📉 ghata' if d_ < 0 else '➖ barabar'}"
                         f" ({'+' if d_ >= 0 else ''}{d_})")
            extra.insert(0, f"📅 Pichhle 7 din ka kul: {tot[0]} log, {tot[1]} page dekhe (roz ausat {tot[0] / 7:.1f} log, "
                            f"{tot[1] / 7:.0f} page){trend}")
    except Exception as e:
        log(f"traffic total: {e}")
    if extra:                     # upar rakho - Telegram 4000 akshar par kaat deta hai
        t1 = "\n".join(extra) + "\n" + LINK_TRUTH + "\n\n" + t1
    return t1


def traffic_trend():
    """v2.9.9 (owner: 'pichhle 15 din ke ausat se aaj badh raha ya ghat raha'): GA4 sab raaste milakar.
    Aaj adhoora din hota hai - isliye 'kal' ko 15-din ausat se milate hain, aaj ka abhi tak alag."""
    t = _ga_total("today", "today")
    y = _ga_total("yesterday", "yesterday")
    f = _ga_total("15daysAgo", "yesterday")
    if f is None:
        return "📊 Traffic trend: Google Analytics se data nahi mila"
    au, ap = f[0] / 15, f[1] / 15

    def cmp(v, avg):
        if avg <= 0:
            return "➖"
        r = (v - avg) / avg * 100
        return f"{'📈' if r > 10 else '📉' if r < -10 else '➖'} {'+' if r >= 0 else ''}{r:.0f}%"
    L = ["📊 WEBSITE TRAFFIC (sab raaste: Google, Bing, Pinterest, video link, seedha)",
         f"• Pichhle 15 din ka roz ausat: {au:.1f} log, {ap:.0f} page",
         f"• Kal: {y[0] if y else '?'} log, {y[1] if y else '?'} page → ausat se {cmp(y[0], au) if y else '?'}",
         f"• Aaj (abhi tak): {t[0] if t else '?'} log, {t[1] if t else '?'} page"]
    state.put("traffic_trend", {"t": str(datetime.date.today()), "avg": round(au, 2), "kal": y[0] if y else None})
    return "\n".join(L)


def _ga_total(start, end):
    """(kul log, kul page views) - ek chhoti GA4 report."""
    if not SA.exists():
        return None
    tok = _gcreds("https://www.googleapis.com/auth/analytics.readonly")
    j = requests.post(f"https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY}:runReport",
                      headers={"Authorization": f"Bearer {tok}"}, timeout=60,
                      json={"dateRanges": [{"startDate": start, "endDate": end}],
                            "metrics": [{"name": "activeUsers"}, {"name": "screenPageViews"}]}).json()
    rows = j.get("rows") or []
    if "error" in j:
        raise RuntimeError(j["error"].get("message", "")[:200])
    state.put("ga_data_ok", time.time())              # v2.9.3: GA Data API chal raha (list ka 'ga4' kaam khud band)
    if not rows:
        return (0, 0)
    mv = rows[0]["metricValues"]
    return int(mv[0]["value"]), int(mv[1]["value"])


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
            raise RuntimeError(j["error"].get("message", "")[:400])
        return [(r["dimensionValues"][0]["value"], int(r["metricValues"][0]["value"]), int(r["metricValues"][1]["value"]))
                for r in j.get("rows", [])]
    try:
        src = rep("sessionSource")
    except Exception as e:
        return _ga_help(str(e))
    camp = [x for x in rep("sessionCampaignName") if x[0] not in ("(not set)", "(direct)", "(organic)", "(referral)")]
    pages = rep("pagePath", 6)
    try:                     # v2.1.4: HAR link ka hisaab - kaunsa platform / medium / brand (utm) se kitne aaye
        j = requests.post(url, headers=h, timeout=60, json={
            "dateRanges": rng, "dimensions": [{"name": "sessionSource"}, {"name": "sessionMedium"},
                                              {"name": "sessionCampaignName"}],
            "metrics": [{"name": "activeUsers"}, {"name": "screenPageViews"}],
            "orderBys": [{"metric": {"metricName": "activeUsers"}, "desc": True}], "limit": 25}).json()
        links = [(r["dimensionValues"][0]["value"], r["dimensionValues"][1]["value"], r["dimensionValues"][2]["value"],
                  int(r["metricValues"][0]["value"])) for r in j.get("rows", [])]
    except Exception:
        links = []
    try:
        j = requests.post(url, headers=h, timeout=60, json={
            "dateRanges": rng, "dimensions": [{"name": "landingPagePlusQueryString"}],
            "metrics": [{"name": "activeUsers"}],
            "dimensionFilter": {"filter": {"fieldName": "landingPagePlusQueryString",
                                           "stringFilter": {"matchType": "CONTAINS", "value": "utm_"}}},
            "orderBys": [{"metric": {"metricName": "activeUsers"}, "desc": True}], "limit": 10}).json()
        lands = [(r["dimensionValues"][0]["value"], int(r["metricValues"][0]["value"])) for r in j.get("rows", [])]
    except Exception:
        lands = []
    users = sum(x[1] for x in src)
    dwell_str = ""
    try:                     # v2.3.0 (v11 se): log kitni der ruke (GA4 averageSessionDuration + engagement)
        j_dur = requests.post(url, headers=h, timeout=45, json={
            "dateRanges": rng, "metrics": [{"name": "averageSessionDuration"}, {"name": "engagedSessions"}, {"name": "engagementRate"}]}).json()
        mv = (j_dur.get("rows") or [{}])[0].get("metricValues") or []
        if len(mv) >= 3:
            a_s = float(mv[0].get("value", 0) or 0)
            dwell_str = (f"\n⏱ Kitni der ruke (ausat): {int(a_s // 60)}m {int(a_s % 60)}s | Ruke (engaged): "
                         f"{float(mv[2].get('value', 0) or 0) * 100:.1f}% ({int(float(mv[1].get('value', 0) or 0))} session)")
    except Exception as _e:
        log(f"ga4 dwell: {_e}")
    lines = [f"🌐 sabhisaab.com ({'aaj' if days == 1 else f'pichhle {days} din'}): {users} log, "
             f"{sum(x[2] for x in src)} page dekhe" + dwell_str,
             "📍 Kahan se aaye: " + ", ".join(f"{s} {u}" for s, u, _ in src[:8])]
    if camp:
        lines.append("🔗 Hamare link se (brand): " + ", ".join(f"{c} {u}" for c, u, _ in camp[:6]))
    lines.append("📄 Sabse zyada dekhe page: " + ", ".join(f"{p} ({v})" for p, _, v in pages))
    ours = [x for x in links if x[1] not in ("organic", "(none)") or x[2] not in ("(not set)", "(direct)", "(organic)")]
    if ours:
        lines.append("\n🔗 Har link (kahan se / kaise / kis brand ka → log):")
        lines += [f"• {s_} / {m_} / {c_} → {u_}" for s_, m_, c_, u_ in ours[:15]]
    if lands:
        lines.append("🎯 Hamare link jinse log aaye (page + link):")
        lines += [f"• {p_[:90]} → {u_}" for p_, u_ in lands[:8]]
    if not ours and not lands:
        lines.append("🔗 Hamare video/post ke link se is samay koi nahi (ya Google ne abhi gina nahi - 24-48 ghante der hoti hai).")
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
    state.put("ga_need", None)
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
    if state.get("videos_json_hash") == dig and not (DIR / "site" / "sh-elite-widget.js").exists():
        return "videos.json: koi badlaav nahi"
    z = DATA / "videos-json.zip"
    extra = {}
    try:                     # v2.3.0: widget website par live ho tabhi reel-codes.json (sawal + jawab; koi niji data nahi)
        if (DIR / "site" / "sh-elite-widget.js").exists():
            codes = {k: {"q": v.get("q", ""), "ans": v.get("ans", ""), "t": v.get("t", "")}
                     for k, v in list((state.get("reel_codes") or {}).items())[-400:]}
            extra["site/reel-codes.json"] = json.dumps(codes, ensure_ascii=False, sort_keys=True)
            dig = hashlib.md5((body + extra["site/reel-codes.json"]).encode()).hexdigest()
            if state.get("videos_json_hash") == dig:
                return "videos.json + reel-codes.json: koi badlaav nahi"
    except Exception as e:
        log(f"reel-codes: {e}")
    with zipfile.ZipFile(z, "w") as zz:
        zz.writestr("site/videos.json", body)
        for k_, v_ in extra.items():
            zz.writestr(k_, v_)
    r = apply_zip(z, force=True)
    z.unlink(missing_ok=True)
    if "❌" not in str(r):
        state.put("videos_json_hash", dig)
    return f"videos.json ({len(m)} page): {str(r)[:120]}"



OLD_SA = "gsc-bot@sabhisaab.iam.gserviceaccount.com"     # 30 Oct se pehle yahi tha (GA4 + GSC mein ijaazat isi ko)


def google_check():
    """v2.1.6: Google (GSC + GA4) ka asli haal + agar toota to SAHI ilaaj link ke saath.
    30 Oct restore mein gsc_sa.json NAYI service account (doosre project) ki aayi - usko na GA4 ki ijaazat, na GSC ki,
    na us project mein Analytics API chalu. Isliye traffic report + sitemap dono band."""
    if not SA.exists():
        state.put("google_ok", False)
        return "🔑 Google service account file VM par nahi. Neeche wale steps se JSON key banakar bot ko bhejein."
    try:
        info = json.loads(SA.read_text())
    except Exception:
        return "❌ gsc_sa.json padhi nahi ja rahi - nayi key bhejein."
    email, proj = info.get("client_email", "?"), info.get("project_id", "?")
    out = [f"🔎 Google jaanch | service account: {email} (project {proj})"]
    ok_gsc = ok_ga = False
    try:
        tk = _gcreds("https://www.googleapis.com/auth/webmasters.readonly")
        sites = requests.get("https://www.googleapis.com/webmasters/v3/sites", headers={"Authorization": f"Bearer {tk}"},
                             timeout=30).json()
        names = [x.get("siteUrl") for x in sites.get("siteEntry", [])]
        ok_gsc = any("sabhisaab.com" in (n or "") for n in names)
        out.append("• Search Console (sitemap, index): " + ("✅" if ok_gsc else
                   f"❌ is account ko sabhisaab.com ki ijaazat nahi ({sites.get('error', {}).get('message', 'list khaali')[:80]})"))
    except Exception as e:
        out.append(f"• Search Console: ❌ {str(e)[:120]}")
    try:
        tk = _gcreds("https://www.googleapis.com/auth/analytics.readonly")
        j = requests.post(f"https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY}:runReport",
                          headers={"Authorization": f"Bearer {tk}"}, timeout=30,
                          json={"dateRanges": [{"startDate": "1daysAgo", "endDate": "today"}],
                                "metrics": [{"name": "activeUsers"}]}).json()
        ok_ga = "error" not in j
        out.append("• Analytics (website par kaun aaya): " + ("✅" if ok_ga else f"❌ {j['error'].get('message', '')[:140]}"))
    except Exception as e:
        out.append(f"• Analytics: ❌ {str(e)[:120]}")
    state.put("google_ok", ok_gsc and ok_ga)
    if ok_gsc and ok_ga:
        state.put("ga_need", None)
        return "\n".join(out + ["✅ Google poora juda - traffic, sitemap, index report sab chalenge."])
    if email != OLD_SA:
        out += ["", "🛠 SABSE AASAAN ILAAJ (5 min): purane service account ki NAYI key bot ko dein - us par GA4 + Search "
                    "Console ki ijaazat aur API pehle se chalu hain (aapke Analytics screen par 'gsc-bot' Viewer dikh raha hai).",
                "1) https://console.cloud.google.com/iam-admin/serviceaccounts?project=sabhisaab kholein (mkpandey1989 wala account)",
                f"2) {OLD_SA} par click → upar 'Keys' tab → 'Add key' → 'Create new key' → JSON → Create (file download hogi)",
                "3) Wo .json file is bot ko Telegram par bhejein (bot surakshit rakh kar chat se mita dega, phir khud jaanchega)",
                "Project 'sabhisaab' na dikhe to upar project chunne wale dabbe mein 'sabhisaab' search karein."]
    else:
        if not ok_gsc:
            out += ["", "🛠 Search Console: https://search.google.com/search-console/users?resource_id=sc-domain%3Asabhisaab.com",
                    f"→ Add user → {email} → Permission: Full → Add"]
        if not ok_ga:
            out += ["", f"🛠 Analytics API: https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com?project={proj} → Enable",
                    f"   aur analytics.google.com → Admin → Property access management → ➕ → {email} → Viewer"]
    return "\n".join(out)


def daily_index():
    """v2.1.6: ROZ (owner: 'pehle roz jaata tha'): Google ko sitemap + Bing/IndexNow ko naye/badle page jo abhi tak
    nahi bheje (14-din/10-roz niyam wahi). Pehle sirf website deploy par hota tha."""
    msg = []
    if SA.exists():
        msg.append(submit_sitemap() or "")
    urls = []
    try:
        sm = requests.get(SITE + "/sitemap.xml", timeout=30).text
        cut = str(datetime.date.today() - datetime.timedelta(days=10))
        for loc, mod in re.findall(r"<loc>([^<]+)</loc>\s*(?:<lastmod>([^<]+)</lastmod>)?", sm):
            if (mod or "")[:10] >= cut:
                urls.append(loc.strip())
    except Exception as e:
        log(f"daily_index sitemap: {e}")
    try:
        from . import siteknow
        urls += [p if p.startswith("http") else f"{SITE}/{p.lstrip('/')}" for p in (siteknow.not_indexed() or [])][:20]
    except Exception:
        pass
    done = {r["url"] for r in indexnow_rows() if r.get("code") in (200, 202)}
    fresh = [u for u in dict.fromkeys(urls) if u not in done]
    msg.append(indexnow(fresh, "roz: naya/badla") if fresh else "IndexNow: aaj koi naya page nahi")
    state.put("index_day", str(datetime.date.today()))
    return " | ".join(m for m in msg if m)



def verify_calculators_smoke():
    """v2.3.0 (v11 se): site_repo ka calc_test.py chalao - koi calculator toota to pakdo (kuch deploy nahi karta)."""
    sync()
    ct = DIR / "scripts" / "calc_test.py"
    if not ct.exists():
        return "ℹ️ calc_test.py website repo mein nahi (audit.py hi jaanch karta hai)."
    try:
        t = _npm_tools()
        env = {**_env(), "NODE_PATH": str(t / "node_modules")}
        r = subprocess.run(["nice", "-n", "15", PY, "scripts/calc_test.py", "site"], cwd=DIR, env=env,
                           capture_output=True, text=True, timeout=1200)
        return ("✅ Calculator smoke test PASS: " if r.returncode == 0 else "❌ Calculator smoke test FAIL: ") + (r.stdout + r.stderr)[-400:]
    except Exception as e:
        return f"ℹ️ Calculator test nahi chala ({str(e)[:100]})"


# ---------------- v2.6.0 (owner 9 Nov): Bing - priority wala roz ka kram (policy ke andar) ----------------
# Bing ka niyam: URL Submission quota site ke hisaab se (is site ka ~100/din; Bing domain par 10,000/din tak deta hai).
# Spam se bachav: (1) quota ka max ek-tihaai, upar se 30/din, (2) sirf asli zaroorat wale URL - pehle jo Google/Bing ne
# index/crawl NAHI kiye, phir naye-badle page, phir baaki, (3) ek URL 14 din (pending) / 30 din (baaki) mein ek hi baar,
# (4) IndexNow alag - sirf badle page (purana niyam). Har din ALAG URL jaate hain.
BING_MAX_DAY = 50              # v3.3.0 (owner 14 Nov: 'jyada ho sakte hain to'): 30 -> 50, quota ka 1/2 (pehle 1/3). Bina badle,
                               # pehle se index page ab bhi KABHI nahi; 14/30 din ka niyam waisa hi (purana over-submit dobara nahi)
BING_QUOTA_PART = 2


def bing_cap(quota):
    return max(0, min(BING_MAX_DAY, int(quota or 0) // BING_QUOTA_PART))

BING_INFO_CHECKS = 40          # roz itne URL ka Bing haal (GetUrlInfo - padhne wali call, submission quota nahi khaati)
BING_RESEND_PENDING = 14
BING_RESEND_OTHER = 30


def _bing_date(v):
    """'/Date(1730000000000)/' ya ISO -> 'YYYY-MM-DD' ya ''."""
    m = re.search(r"Date\((-?\d+)", str(v or ""))
    if m:
        ms = int(m.group(1))
        if ms <= 0:
            return ""
        d = datetime.datetime.utcfromtimestamp(ms / 1000).date()
        return "" if d.year < 2001 else str(d)
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(v or ""))
    return m.group(1) if m and not m.group(1).startswith(("0001", "1970")) else ""


def bing_url_info(n=BING_INFO_CHECKS):
    """Roz kuch URL ka Bing haal: kabhi crawl hua ya nahi (state bing_urlinfo). Sirf padhna."""
    key = _env().get("BING_API_KEY")
    if not key:
        return 0
    from . import siteknow
    pg = siteknow.pages() or {}
    info = dict(state.get("bing_urlinfo") or {})
    cut = str(datetime.date.today() - datetime.timedelta(days=14))
    urls = [SITE + ("/" + k.strip("/") if k.strip("/") else "/") for k, v in pg.items() if siteknow.is_content(k, v)]
    todo = sorted([u for u in urls if (info.get(u) or {}).get("chk", "") < cut], key=lambda u: (info.get(u) or {}).get("chk", ""))[:n]
    base = "https://ssl.bing.com/webmaster/api.svc/json"
    done = 0
    for u in todo:
        try:
            j = requests.get(f"{base}/GetUrlInfo", params={"apikey": key, "siteUrl": SITE + "/", "url": u}, timeout=20).json()
            d = j.get("d") or {}
            info[u] = {"chk": str(datetime.date.today()), "crawl": _bing_date(d.get("LastCrawledDate")),
                       "disc": _bing_date(d.get("DiscoveryDate")), "http": d.get("HttpStatus")}
            done += 1
        except Exception as e:
            log(f"bing urlinfo {u}: {str(e)[:80]}")
            break
        time.sleep(0.3)
    state.put("bing_urlinfo", info)
    return done


def bing_plan(quota, today=None, pages=None, google_pending=None, urlinfo=None, sent=None, imp=None, rotate=False, shown=None,
              new_uk=None):
    """Kaunse URL aaj Bing ko (bina network - test ho sake). -> (list, {url: kyun})."""
    today = today or str(datetime.date.today())
    t = datetime.date.fromisoformat(today)
    cap = bing_cap(quota)
    new_uk = {("/" + str(x).strip("/")) for x in (new_uk or [])}   # v3.3.0: page queue ke naye page (14 din) - sabse pehle, alag
    if cap == 0:
        return [], {}
    from . import siteknow
    pages = pages or {}
    urlinfo, sent, imp = urlinfo or {}, sent or {}, imp or {}
    shown = {("/" + str(x).strip("/")) if str(x).strip("/") else "/" for x in (shown or [])}   # v3.2.0: Bing search mein dikhe = index ka saboot
    gp = {("/" + str(x).strip("/")) for x in (google_pending or [])}
    recent = str(t - datetime.timedelta(days=14))
    rows = []
    for k, v in pages.items():
        if not siteknow.is_content(k, v) or str(k).strip("/") in ("links", "jawab") or (str(k).strip("/") and v.get("in_sitemap") is False):
            continue                      # links.html kabhi nahi (niyam); /jawab roz badalta hai - uska IndexNow alag
        path = "/" + str(k).strip("/") if str(k).strip("/") else "/"
        u = SITE + path
        ui = urlinfo.get(u) or {}
        fresh_pg = (v.get("lastmod") or "") >= recent
        if path in shown and not fresh_pg:
            continue                      # v3.2.0: Bing mein index (search mein dikh chuka) + bina badla = kabhi dobara nahi
        if path in new_uk:
            pr, why = -1, "naya Uttarakhand page (queue)"
        elif path in gp:
            pr, why = 0, "Google index nahi"
        elif ui.get("chk") and not ui.get("crawl"):
            pr, why = 1, "Bing ne kabhi crawl nahi kiya"
        elif fresh_pg:
            pr, why = 2, "naya/badla page"
        elif ui.get("crawl"):             # v3.2.0 (owner 13 Nov: 'jo index nahi huye wo jaayein'): crawl hua par Bing search
            pr, why = 3, "crawl hua, Bing index ka saboot nahi"   # mein kabhi nahi dikha -> 30 din mein ek baar (OWNER_RULES 6)
        else:
            if not rotate:                # v3.1.0 (11 Nov audit): BINA BADLE, pehle se crawl hue page baari-baari dobara bhejna BAND.
                continue                  # Bing URL Submission sirf naye/badle URL ke liye hai; 4-11 Nov roz 10-30 purane page ja rahe the
            pr, why = 4, "baaki (baari se)"   # (wahi aadat jisse purane bot ke baad Bing ne site dikhana band kiya tha). Sitemap unhe khud dikhata hai.
        gap = BING_RESEND_PENDING if pr <= 1 else BING_RESEND_OTHER
        last = sent.get(u, "")
        if last and last > str(t - datetime.timedelta(days=gap)):
            continue
        rows.append((pr, last or "0000", -int(imp.get(path, 0)), path, u, why))
    rows.sort()
    pick = rows[:cap]
    return [r[4] for r in pick], {r[4]: r[5] for r in pick}


def bing_submit_daily(force=False):
    key = _env().get("BING_API_KEY")
    if not key:
        return "🔑 Bing API key nahi (bot ko 'bing key <key>')"
    today = str(datetime.date.today())
    if not force and state.get("bing_api_day") == today:
        return "Bing API: aaj pehle hi bheja ja chuka"
    base = "https://ssl.bing.com/webmaster/api.svc/json"
    try:
        q = requests.get(f"{base}/GetUrlSubmissionQuota", params={"apikey": key, "siteUrl": SITE + "/"}, timeout=30).json()
        quota = int(((q.get("d") or {}).get("DailyQuota")) or 0)
    except Exception as e:
        return f"Bing quota jaanch nahi hui: {str(e)[:100]}"
    if quota <= 0:
        state.put("bing_api_day", today)
        return "Bing API: aaj ka quota 0 (Bing ne roka/khatam)"
    try:
        bing_url_info()
    except Exception as e:
        log(f"bing urlinfo: {e}")
    try:
        bing_page_stats()
    except Exception as e:
        log(f"bing pagestats: {e}")
    from . import siteknow
    sent = state.get("bing_api_sent") or {}
    sent = {u: d for u, d in sent.items() if d >= str(datetime.date.today() - datetime.timedelta(days=60))}
    state.put("bing_last_plan", {"day": today, "quota": quota, "why": {}, "sent": 0})
    imp = {}
    try:
        for qv in json.loads((DATA / "keywords.json").read_text()).values():
            pth = "/" + str(qv.get("page", "/")).strip("/")
            imp[pth] = imp.get(pth, 0) + int(qv.get("imp", 0))
    except Exception:
        pass
    _cut = str(datetime.date.today() - datetime.timedelta(days=14))
    _uk = [s_ for s_, d_ in (state.get("pq_pub") or {}).items() if d_ >= _cut]
    fresh, why = bing_plan(quota, today, siteknow.pages() or {}, siteknow.not_indexed() or [],
                           state.get("bing_urlinfo") or {}, sent, imp, shown=list(state.get("bing_shown") or {}), new_uk=_uk)
    if not fresh:
        state.put("bing_api_day", today)
        return "Bing API: aaj koi zaroori URL nahi (sab haal hi mein bheje ja chuke)"
    try:
        r = requests.post(f"{base}/SubmitUrlBatch", params={"apikey": key}, timeout=30,
                          json={"siteUrl": SITE + "/", "urlList": fresh})
        code = r.status_code
    except Exception as e:
        return f"Bing API: bhej nahi paya ({str(e)[:100]})"
    _ilog(fresh, code, "bing-api roz (priority)")
    state.put("bing_last_resp", {"day": today, "code": code, "text": (r.text or "")[:300], "n": len(fresh)})   # v3.3.0: Bing ne kya bola
    state.put("bing_api_day", today)
    if code == 200:
        for u in fresh:
            sent[u] = today
        state.put("bing_api_sent", sent)
        state.put("bing_last_plan", {"day": today, "quota": quota, "why": why, "sent": len(fresh)})
        diary.add("upload", f"Bing URL submission {len(fresh)} page (quota {quota})")
        from collections import Counter as _C
        c = _C(why.values())
        return (f"🔎 Bing Webmaster API: {len(fresh)} page bheje ✅ (aaj ka quota {quota}, seema {bing_cap(quota)}) | "
                + ", ".join(f"{k}: {v}" for k, v in c.items()))
    return f"Bing API: HTTP {code} {r.text[:120]}"


def bing_page_stats():
    """v3.2.0: Bing Search Performance (GetPageStats, ek padhne wali call, quota nahi khaati) -> jo page Bing search mein
    kabhi bhi dikhe (impression > 0) = Bing index ka pakka saboot. state bing_shown {path: aakhri tareekh}. Kabhi ghatta nahi."""
    key = _env().get("BING_API_KEY")
    if not key:
        return 0
    j = requests.get("https://ssl.bing.com/webmaster/api.svc/json/GetPageStats",
                     params={"apikey": key, "siteUrl": SITE + "/"}, timeout=30).json()
    shown = dict(state.get("bing_shown") or {})
    for r in (j.get("d") or []):
        u = str(r.get("Query") or "")
        if not u or int(r.get("Impressions") or 0) <= 0:
            continue
        pth = "/" + re.sub(r"^https?://[^/]+", "", u).split("?")[0].split("#")[0].strip("/")
        d = _bing_date(r.get("Date")) or str(datetime.date.today())
        if d > shown.get(pth, ""):
            shown[pth] = d
    state.put("bing_shown", shown)
    return len(shown)


def _bing_traffic(key, days=7):
    """GetRankAndTrafficStats -> (impression, click) pichhle N din."""
    j = requests.get("https://ssl.bing.com/webmaster/api.svc/json/GetRankAndTrafficStats",
                     params={"apikey": key, "siteUrl": SITE + "/"}, timeout=30).json()
    cut = str(datetime.date.today() - datetime.timedelta(days=days))
    im = cl = 0
    for r in (j.get("d") or []):
        if _bing_date(r.get("Date")) >= cut:
            im += int(r.get("Impressions") or 0)
            cl += int(r.get("Clicks") or 0)
    return im, cl


def bing_report():
    """v3.2.0 (owner 13 Nov): Bing ki roz ki report - GSC report ke saath, usi samay (08:00). Sirf padhta hai."""
    key = _env().get("BING_API_KEY")
    if not key:
        return "🅱️ BING: API key nahi (bot ko 'bing key <key>')"
    from . import siteknow
    base = "https://ssl.bing.com/webmaster/api.svc/json"
    today = str(datetime.date.today())
    L = ["🅱️ BING - roz ki report (Google report ke saath)"]
    try:
        c = requests.get(f"{base}/GetCrawlStats", params={"apikey": key, "siteUrl": SITE + "/"}, timeout=30).json()
        st = (c.get("d") or [{}])[-1] or {}
        ii = st.get("InIndex")
        hist = dict(state.get("bing_inindex") or {})
        prev = [v for k, v in sorted(hist.items()) if k < today]
        if ii is not None:
            hist[today] = int(ii)
            state.put("bing_inindex", dict(sorted(hist.items())[-60:]))
            ch = (f" ({'+' if int(ii) - prev[-1] >= 0 else ''}{int(ii) - prev[-1]} pichhli baar se)" if prev else "")
            L.append(f"• Bing index mein (Bing ki ginti): {ii}{ch}")
        L.append(f"• Kal Bing ne crawl kiye: {st.get('CrawledPages', '-')} | crawl error: {st.get('CrawlErrors', '-')}")
    except Exception as e:
        L.append(f"• Crawl/index ginti nahi mili ({str(e)[:60]})")
    try:
        bing_page_stats()
    except Exception as e:
        log(f"bing report pagestats: {e}")
    pg = siteknow.pages() or {}
    content = ["/" + str(k).strip("/") if str(k).strip("/") else "/" for k, v in pg.items()
               if siteknow.is_content(k, v) and v.get("in_sitemap") is not False]
    shown = state.get("bing_shown") or {}
    info = state.get("bing_urlinfo") or {}
    seen = sum(1 for p in content if p in shown)
    crawled = sum(1 for p in content if (info.get(SITE + p) or {}).get("crawl"))
    never = sum(1 for p in content if (info.get(SITE + p) or {}).get("chk") and not (info.get(SITE + p) or {}).get("crawl"))
    unchk = sum(1 for p in content if not (info.get(SITE + p) or {}).get("chk"))
    L.append(f"• Site ke page: {len(content)} | Bing search mein dikh chuke (pakka index): {seen}")
    L.append(f"• Bing ne crawl kiye: {crawled} | kabhi crawl nahi: {never} | jaanch baaki: {unchk}")
    try:
        im, cl = _bing_traffic(key, 14)
        L.append(f"• Bing search (14 din, Bing hafte-wari deta hai): {im} baar dikha, {cl} click")
    except Exception as e:
        log(f"bing traffic: {e}")
    lp = state.get("bing_last_plan") or {}
    rows = [r for r in indexnow_rows() if str(r.get("why", "")).startswith("bing-api") and r.get("code") == 200]
    if lp.get("day") == today:
        from collections import Counter as _C
        cc = _C((lp.get("why") or {}).values())
        L.append(f"• Aaj 06:40 Bing ko bheje: {lp.get('sent', len(lp.get('why') or {}))} (quota {lp.get('quota')}, "
                 f"hamari seema {bing_cap(lp.get('quota'))})"
                 + ("" if not cc else " - " + ", ".join(f"{k}: {v}" for k, v in cc.items())))
    else:
        L.append("• Aaj Bing ko abhi kuch nahi gaya (06:40 ka kaam nahi chala?) - 'bing bhejo' se haath se")
    L.append(f"• Kul Bing API se bheje: {len({r['url'] for r in rows})} alag page (ek page 14/30 din mein ek baar)")
    lr = state.get("bing_last_resp") or {}
    if lr:
        ok_ = lr.get("code") == 200
        L.append(f"• Bing ne kya bola ({lr.get('day')}): {'✅ manzoor (HTTP 200)' if ok_ else '❌ HTTP ' + str(lr.get('code'))} "
                 f"- {lr.get('n')} URL" + ("" if ok_ else f" | {lr.get('text', '')[:160]}"))
    try:                                             # v3.3.0: Uttarakhand pages ka alag hisaab
        from . import pagequeue as _PQ
        man = _PQ.manifest()
        if man:
            pub = state.get("pq_pub") or {}
            uk = ["/" + m["slug"] for m in man]
            live_uk = [p for p in uk if p.strip("/") in pub]
            sent_all = state.get("bing_api_sent") or {}
            sent_uk = [p for p in live_uk if (SITE + p) in sent_all or any(r["url"] == SITE + p for r in rows)]
            shown_uk = [p for p in live_uk if p in shown]
            L.append(f"• 🏔️ Uttarakhand: kul {len(uk)} | live {len(live_uk)} | Bing ko bheje {len(sent_uk)} | Bing search mein dikhe "
                     f"{len(shown_uk)} | live par index ka saboot nahi {len(live_uk) - len(shown_uk)} | queue mein baaki {len(uk) - len(live_uk)}")
            gs = _PQ.gidx_summary()                  # v3.3.2: Google ka haal bhi (roz ki daily.py URL Inspection ka nateeja)
            if gs:
                L.append(gs)
    except Exception as e:
        log(f"bing report uk: {e}")
    left = [p for p in content if p not in shown]
    L.append(f"• Abhi Bing index ka saboot nahi: {len(left)} page - bot roz quota ka aadha (max {BING_MAX_DAY}) baari se bhejta hai "
             "(pehle naye Uttarakhand page, phir Google-index-nahi, Bing-crawl-nahi, naye/badle, crawl-hue-par-index-nahi).")
    L.append("ℹ️ 'Pakka index' = jo page Bing search mein kam se kam ek baar dikha. Bing ka data 2-7 din der se aata hai.")
    return "\n".join(L)


# ---------------- v2.9.2: bot ZIP ke saath aaya website-sudhaar (owner ko alag site ZIP nahi) ----------------
def sitepatch_apply():
    """app/sitepatch/*.html -> site/ (audit gate) + unhi page ki sitemap lastmod aaj. Ek baar (state sitepatch_v292)."""
    import pathlib as _pl
    src = _pl.Path(__file__).parent / "sitepatch"
    if state.get("sitepatch_v292") or not src.exists():
        return ""
    files = {f"site/{f.name}": f.read_text(encoding="utf-8") for f in sorted(src.glob("*.html"))}
    if not files:
        return ""
    try:
        sync()
    except Exception as e:
        log(f"sitepatch sync: {e}")
    smf = DIR / "site" / "sitemap.xml"
    if smf.exists():
        sm = smf.read_text(encoding="utf-8")
        day = str(datetime.date.today())
        for p in files:
            slug = p[5:-5]
            sm = re.sub(r"(<loc>" + re.escape(SITE + "/" + slug) + r"</loc>\s*<lastmod>)[\d-]+", lambda m: m.group(1) + day, sm, count=1)
        files["site/sitemap.xml"] = sm
    z = DATA / "sitepatch.zip"
    with zipfile.ZipFile(z, "w") as zz:
        for p, b in files.items():
            zz.writestr(p, b)
    r = apply_zip(z, force=False, deploy_in=1)
    z.unlink(missing_ok=True)
    if str(r).startswith("✅"):
        state.put("sitepatch_v292", True)
        return "🌐 Website: privacy/terms/about mein 'Hamare official channel' + notification/quiz bot ki baat live (audit pass)."
    return f"🌐 Website sudhaar audit mein ruka (kuch live nahi): {str(r)[:200]}"
