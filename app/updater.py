"""Telegram se update (zip/tgz bhejo) + GitHub par code ki copy (sirf padhne ke liye)."""
import os
import pathlib
import shutil
import subprocess
import tarfile
import time
import zipfile
from . import tg, state
from .config import BASE, DATA, GITHUB_MIRROR, TG_MAX_MB
from .log import log

UPD = DATA / "update"


def receive(doc):
    """Koi bhi archive: install.sh ho to update, warna inbox mein khol kar list."""
    from . import files, diary
    name = doc.get("file_name", "file")
    if not name.lower().endswith(files.ARCHIVE):
        return None
    if doc.get("file_size", 0) > TG_MAX_MB * 1024 * 1024:
        tg.alert("yellow", f"Telegram bot {TG_MAX_MB} MB se badi file nahi utaar sakta. Chhota zip bhejein ya hisso mein.")
        return "big"
    ts = time.strftime("%Y%m%d-%H%M%S")
    d = UPD / ts
    d.mkdir(parents=True, exist_ok=True)
    f = d / name
    tg.download(doc["file_id"], f)
    if not files.extract(f, d / "x"):
        tg.alert("yellow", f"'{name}' khul nahi rahi (kharab ya password wali?).")
        return "bad"
    inst = next((p for p in (d / "x").rglob("install.sh")), None)
    # v2.1.9: sirf sabhinet ka layout (install.sh + VERSION + app/bot.py) hi update. Chowkidar ZIP (chowkidar.py) yahan kabhi install nahi.
    if any((d / "x").rglob("chowkidar.py")):
        shutil.rmtree(d, ignore_errors=True)
        tg.alert("yellow", f"👮 '{name}' Chowkidar ki ZIP hai - main ise nahi lagata (do updater = takraav). Ise "
                           "@manoj_vm_chowkidar_bot ko bhejein → '👮 Chowkidar Upgrade' → 1️⃣ → 2️⃣ (15:35 ke baad).")
        return "chowkidar"
    if inst and not ((inst.parent / "VERSION").exists() and (inst.parent / "app" / "bot.py").exists()):
        inst = None                                    # kisi aur program ka install.sh - sirf inbox mein
    if not inst and name.lower().endswith(".zip"):
        from . import website
        with zipfile.ZipFile(f) as z:
            names = z.namelist()
        from . import pagequeue as _PQ                # v3.3.0: page-queue ZIP (site ZIP se PEHLE pehchano - warna sab ek din mein chadh jaate)
        if _PQ.is_queue_zip(names):
            _PQ.offer_zip(ts, f, name, names)
            return ts
        if website.is_site_zip(names):
            # v2.0: har ZIP ki apni jagah (pehle doosri ZIP pehli ko mita deti thi); auto mode mein bina pooche (audit gate phir bhi)
            z = {"ts": ts, "path": str(f), "force": "-force" in name}
            if state.get("site_zip_auto"):
                import threading
                tg.say(f"🌐 Website ZIP '{name}' - audit ke baad apne aap chadhegi...")

                def _go():
                    tg.say(website.apply_zip(z["path"], z["force"]))
                threading.Thread(target=_go, daemon=True).start()
                return ts
            state.update("site_zips", lambda d: {**dict(list((d or {}).items())[-20:]), ts: z}, {})
            tg.say(f"🌐 Ye website ki ZIP lagti hai ({len([n for n in names if not n.endswith('/')])} file). "
                   "Pehle audit, phir GitHub par chadhaun?",
                   tg.inline([[("🌐 Haan, website par", f"ws:{ts}"), ("📁 Nahi, inbox mein", f"wi:{ts}")]]))
            return ts
    if not inst:
        dest = files.save(name.rsplit(".", 1)[0])
        shutil.move(str(d / "x"), dest)
        shutil.rmtree(d, ignore_errors=True)
        _, lst = files.listing(dest)
        diary.add("file", f"archive inbox mein: {name}")
        tg.say(f"📁 '{name}' khol kar surakshit rakh di (VM inbox).\n{lst}\n\nIska kya karna hai, normal baat mein bata dein.")
        return "inbox"
    ver = (inst.parent / "VERSION").read_text().strip() if (inst.parent / "VERSION").exists() else "?"
    cur = (BASE / "VERSION").read_text().strip() if (BASE / "VERSION").exists() else "?"
    try:                     # v2.2.0: nayi ZIP ABHI wale version ke upar bani ho (warna purane sudhaar gayab = regression)
        rm_ = (inst.parent / "docs" / "ROADMAP.md")
        rmt = rm_.read_text(encoding="utf-8", errors="ignore") if rm_.exists() else ""
        if cur not in ("?", "") and f"## v{cur}" not in rmt and f"## v{cur} " not in rmt:
            shutil.rmtree(d, ignore_errors=True)
            tg.alert("red", f"⛔ '{name}' (v{ver}) NAHI lagaunga: ye abhi chal rahe v{cur} ke upar nahi bani (iske ROADMAP mein "
                            f"v{cur} ka hissa nahi). Lagane par pichhle sudhaar gayab ho jaate. Ye ZIP Claude ko bhejein - "
                            "wo isme se kaam ki cheez jaanch kar sahi version mein jodega.")
            return "old_base"
    except Exception as e:
        log(f"base check: {e}")
    cur = (BASE / "VERSION").read_text().strip()
    tg.say(f"📦 Update mila: v{cur} ➜ v{ver}\nInstall karein? (purana backup rahega, gadbad hui to apne aap wapas)",
           tg.inline([[("✅ Haan, install karo", f"up:{ts}"), ("❌ Nahi", f"upno:{ts}")]]))
    return ts


def install(ts):
    inst = next((p for p in (UPD / ts / "x").rglob("install.sh")), None)
    if not inst:
        return tg.say("❌ Update file nahi mili.")
    tg.say("⏳ Install ho raha hai...")
    r = subprocess.run(["bash", str(inst)], capture_output=True, text=True, timeout=900,
                       env={**os.environ, "SN_FROM_BOT": "1"})
    out = (r.stdout + r.stderr)[-1500:]
    if r.returncode != 0 or "INSTALL OK" not in r.stdout:
        return tg.say(f"❌ Install fail, purana version hi chal raha hai.\n{out}")
    ver = (BASE / "VERSION").read_text().strip()
    state.put("pending_update", ver)
    shutil.rmtree(UPD, ignore_errors=True)
    tg.say(f"✅ v{ver} install. Bot 10 second mein naye code se chalu hoga...")
    log(f"update v{ver}, restart")
    time.sleep(2)
    os._exit(0)   # systemd naye code se chalu karega (selfcheck fail ho to backup wapas)


def status_md():
    """Aage koi bhi AI/insaan GitHub se padh kar samajh le ki kya bana hai aur kahan tak (koi secret/ID nahi)."""
    import datetime
    from . import state, pipeline
    from .config import BRANDS
    ver = (BASE / "VERSION").read_text().strip()
    hist = state.get("history", [])
    since = str(datetime.date.today() - datetime.timedelta(days=7))
    per = {b: sum(1 for h in hist if h["brand"] == b and h["date"] >= since) for b in BRANDS}
    try:
        from . import youtube, threads as TH, meta as M, pinterest as PI
        conn = {v["name"]: {"youtube": youtube.has_login(b), "meta": bool(M.brand_info(b)) if M.has_token() else False,
                            "threads": bool(TH.info(b)) and TH.alive(b)[0]} for b, v in BRANDS.items()}
        pin = PI.status()
    except Exception:
        conn, pin = {}, {}
    lines = [f"# Sabhisaab Network - STATUS (apne aap, roz)", f"Version: v{ver} | Updated: {datetime.datetime.now():%Y-%m-%d %H:%M} IST", "",
             "## Connections (sirf haan/na, koi token nahi)"]
    lines += [f"- {n}: " + ", ".join(f"{k} {'OK' if v else 'NO'}" for k, v in c.items()) for n, c in conn.items()]
    lines += [f"- Pinterest: env={pin.get('env')} live={pin.get('live')} oauth={pin.get('oauth')}", "",
              "## Schedule (IST)"] + [f"- {BRANDS[b]['name']}: {s}" for b, s in pipeline.schedule().items()]
    lines += ["", "## Pichhle 7 din YouTube uploads"] + [f"- {BRANDS[b]['name']}: {n}" for b, n in per.items()]
    lines += ["", "## Owner ke pakke niyam (bot ke liye)"] + [f"- {r['rule']}" for r in (state.get("rules") or [])[-20:]]
    try:                                      # v2.0: website ka haal bhi (koi secret nahi)
        from . import siteknow
        pg = siteknow.pages()
        ni = siteknow.not_indexed()
        lines += ["", "## Website", f"- HTML page: {len(pg)}, Google index nahi: {len(ni)}"] + [f"  - /{x}" for x in ni[:15]]
    except Exception:
        pass
    lines += ["", "## Khule kaam (owner)"] + [f"- {x.get('x', '')[:140]}" for x in (state.get("todo") or [])[:15]]
    u = state.get("upgrade_last") or {}
    lines += ["", "## Khud-upgrade", f"- {u.get('t', '-')}: {u.get('summary', '-')[:300]}",
              "", "## Baaki kaam", "- docs/AI_START.md (koi bhi AI pehle ye), docs/ROADMAP.md, docs/PENDING.md (saare khule kaam),",
              "  docs/HANDOVER.md (architecture), docs/ESCALATE.md (jo bot khud theek nahi kar paya)"]
    return "\n".join(lines) + "\n"


def mirror(daily=False, force=False):
    """Code + docs (STATUS.md, HANDOVER.md) GitHub par. Secrets/data/video kabhi nahi. 3 koshish; badlaav na ho to skip."""
    import hashlib
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok or not GITHUB_MIRROR:
        return "GitHub token nahi, mirror skip"
    m = DATA / "mirror"
    shutil.rmtree(m, ignore_errors=True)
    m.mkdir(parents=True)
    for item in ("app", "install.sh", "README.md", "VERSION", "docs", "tests"):   # v3.2.0: tests bhi GitHub par (agla AI kho na de)
        src = BASE / "src" / item if (BASE / "src" / item).exists() else BASE / item
        if src.is_dir():
            shutil.copytree(src, m / item, ignore=shutil.ignore_patterns("__pycache__", "*.mp4", "*.png", "*.wav"))
        elif src.exists():
            shutil.copy2(src, m / item)
    (m / "docs").mkdir(exist_ok=True)
    try:
        (m / "docs" / "STATUS.md").write_text(status_md())
        from . import upgrader
        (m / "docs" / "ESCALATE.md").write_text(upgrader.escalate_md())
        from . import tasks                     # v2.0.3: saare khule kaam ek file mein (koi bhi AI yahin se shuru kare)
        pm = tasks.pending_md()
        (m / "docs" / "PENDING.md").write_text(pm)
        (BASE / "docs").mkdir(exist_ok=True)
        (BASE / "docs" / "PENDING.md").write_text(pm)
        (m / "docs" / "QUERIES.md").write_text(queries_md())
        if (BASE / "docs" / "KEYWORDS.md").exists():
            shutil.copy2(BASE / "docs" / "KEYWORDS.md", m / "docs" / "KEYWORDS.md")
        (m / "docs" / "HEALTH.md").write_text(health_md())
        (m / "docs" / "CHAT.md").write_text(chat_md())
        try:
            from . import website as _w
            (m / "docs" / "INDEXING.md").write_text(_w.indexing_md())
        except Exception as e:
            log(f"indexing md: {e}")
        for nm in ("STATUS.md", "ESCALATE.md", "PENDING.md", "QUERIES.md", "HEALTH.md", "CHAT.md", "KEYWORDS.md", "INDEXING.md"):
            fp = m / "docs" / nm                # v2.0.8: aakhri jaal - bot ki likhi file mein koi token GitHub na jaye
            if fp.exists():
                fp.write_text(_mask_tokens(fp.read_text(encoding="utf-8")), encoding="utf-8")
    except Exception as e:
        log(f"status md: {e}")
    for f in m.rglob("*"):                      # GitHub seema: 1 MB se badi file kabhi nahi
        if f.is_file() and f.stat().st_size > 1_000_000:
            f.unlink()
    h = hashlib.md5()
    for f in sorted(m.rglob("*")):
        if f.is_file() and f.name not in ("STATUS.md", "ESCALATE.md", "PENDING.md", "QUERIES.md", "KEYWORDS.md", "HEALTH.md", "CHAT.md", "INDEXING.md"):
            h.update(f.read_bytes())
    digest = h.hexdigest() + (str(__import__("datetime").date.today()) if daily else "")
    from . import state
    if state.get("mirror_hash") == digest and not force:
        shutil.rmtree(m, ignore_errors=True)
        return "GitHub: koi badlaav nahi"
    ver = (BASE / "VERSION").read_text().strip()
    url = f"https://x-access-token:{tok}@github.com/{GITHUB_MIRROR}.git"
    cmds = [["git", "init", "-q", "-b", "main"], ["git", "add", "-A"],
            ["git", "-c", "user.name=sabhisaab-bot", "-c", "user.email=contact@sabhisaab.com", "commit", "-q", "-m",
             f"v{ver} (VM se apne aap)"], ["git", "push", "-q", "-f", url, "main"]]
    err = ""
    for attempt in range(3):
        ok = True
        for c in cmds if attempt == 0 else cmds[-1:]:
            r = subprocess.run(c, cwd=m, capture_output=True, text=True, timeout=180)
            if r.returncode != 0:
                err = r.stderr.replace(tok, "***")[-200:]
                ok = False
                break
        if ok:
            break
        log(f"mirror koshish {attempt + 1} fail: {err}")
        time.sleep(20 * (attempt + 1))
    shutil.rmtree(m, ignore_errors=True)
    if err and not ok:
        return f"GitHub copy nahi gayi ({err.strip()[:120]})"
    state.put("mirror_hash", digest)
    return f"GitHub copy: v{ver} ✅"


def github_token_days():
    """GitHub token kitne din aur chalega (expiry se 15 din pehle yaad dilane ke liye)."""
    import datetime
    import requests
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return None
    r = requests.get("https://api.github.com/user", headers={"Authorization": f"Bearer {tok}"}, timeout=20)
    if r.status_code == 401:
        return -1
    exp = r.headers.get("github-authentication-token-expiration")
    if not exp:
        return 9999
    d = datetime.datetime.strptime(exp[:19], "%Y-%m-%d %H:%M:%S")
    return (d - datetime.datetime.utcnow()).days



DOC_FILES = {"ai": "AI_START.md", "roadmap": "ROADMAP.md", "handover": "HANDOVER_OWNER.md", "pending": "PENDING.md",
             "status": "STATUS.md", "escalate": "ESCALATE.md", "arch": "HANDOVER.md"}


def send_docs(text=""):
    """v2.0.3: 'roadmap do' / 'handover file' / 'pending list do' / 'docs do' -> taaza docs Telegram par (VM se, GitHub nahi)."""
    from . import tasks, tg, upgrader
    d = BASE / "docs"
    d.mkdir(exist_ok=True)
    try:                                       # hamesha taaza: pending + status + escalate abhi likho
        (d / "PENDING.md").write_text(tasks.pending_md())
        (d / "STATUS.md").write_text(status_md())
        (d / "ESCALATE.md").write_text(upgrader.escalate_md())
    except Exception as e:
        log(f"send_docs refresh: {e}")
    t = (text or "").lower()
    keys = [k for k, w in (("roadmap", "road"), ("handover", "hand"), ("pending", "pending"), ("status", "status"),
                           ("escalate", "escalat"), ("ai", "ai start")) if w in t]
    if not keys or "docs" in t or "sab" in t or "saare" in t:
        keys = ["ai", "roadmap", "handover", "pending", "status", "escalate"]
    sent = []
    for k in keys:
        f = d / DOC_FILES[k]
        if f.exists():
            with open(f, "rb") as fh:
                tg.call("sendDocument", {"chat_id": tg._chat(), "caption": f"📄 {f.name} (taaza, VM se)"}, {"document": fh})
            sent.append(f.name)
    if not sent:
        return "Docs abhi VM par nahi mile - agla update docs ke saath aayega."
    return ("📄 Bheje: " + ", ".join(sent) + "\nYahi file GitHub par bhi roz 04:00 taaza hoti hain: "
            "https://github.com/mkpandey1989-hue/sabhisaab-network/tree/main/docs")



# ---------------- v2.0.4: owner ki har baat ka record (koi bhi AI wahin se shuru kare) ----------------
QFILE = DATA / "queries.jsonl"
UNSURE = ("samajh nahi", "samjha nahi", "nahi kar sakta", "nahi kar sakti", "taakat nahi", "mere paas", "abhi nahi",
          "pata nahi", "jaankari nahi", "nahi mila", "support nahi", "possible nahi", "sambhav nahi")


def mark_dirty():
    from . import state
    state.put("docs_dirty", True)


def log_query(text, action, reply):
    """Har free-text hukum jo think() tak gaya. Jo bot ne poora nahi kiya (chat/samajh nahi) -> 'AI ke liye' khula."""
    import datetime
    import json
    low = (reply or "").lower()
    unsure = action in ("chat", "", None) and any(w in low for w in UNSURE)
    rec = {"t": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "q": _mask(text or "")[:500], "action": action,
           "reply": _mask(reply or "")[:300], "open": bool(unsure)}
    QFILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QFILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if unsure:
        mark_dirty()


def queries_md():
    import json
    try:
        rows = [json.loads(x) for x in QFILE.read_text(encoding="utf-8").splitlines() if x.strip()]
    except Exception:
        rows = []
    open_ = [r for r in rows if r.get("open")][-40:]
    lines = ["# QUERIES - owner ne jo kaha aur bot poora nahi kar paya (AI/developer: inhe pakka karke kaam shuru karo)",
             "Bot har free-text hukum yahan likhta hai. 'Khule' = bot ne 'samajh nahi / nahi kar sakta' kaha. Fix ZIP mein",
             "us kaam ka command/feature jodo, phir yahan likhe sawaal owner se ek baar pakka karo.", "",
             f"## Khule ({len(open_)})"]
    lines += [f"- {r['t']} | \"{r['q'][:200]}\" → bot: {r['reply'][:160]}" for r in reversed(open_)] or ["- (koi nahi)"]
    lines += ["", "## Aakhri 25 hukum (sab)"]
    lines += [f"- {r['t']} [{r.get('action')}] {r['q'][:160]}" for r in reversed(rows[-25:])]
    return "\n".join(lines) + "\n"


def send_chowkidar_file():
    """Chowkidar (TradingBot) ki wo file jismein 'ytlistener' likha hai - sirf PADH kar owner ko (secret chhupa kar).
    sabhinet Chowkidar ko kabhi BADALTA nahi; owner ye file Claude ko deta hai, fix VM bot ke '🛠 Update' se lagta hai."""
    import re
    from . import tg
    hits = []
    for root in (pathlib.Path("/home/ubuntu"),):
        for f in root.rglob("*.py"):
            sp = str(f)
            if "sabhisaab-network" in sp or "/venv" in sp or "/.cache" in sp or "site-packages" in sp or "/tgapi" in sp:
                continue
            try:
                if f.stat().st_size < 400_000 and "ytlistener" in f.read_text(encoding="utf-8", errors="ignore"):
                    hits.append(f)
            except Exception:
                pass
            if len(hits) >= 3:
                break
    if not hits:
        return "Chowkidar ki koi file nahi mili jismein 'ytlistener' ho."
    pat = re.compile(r"\d{8,10}:[A-Za-z0-9_-]{30,}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_\w{30,}|"
                     r"EAA[A-Za-z0-9]{40,}|sk-[A-Za-z0-9_-]{20,}")
    kv = re.compile(r"((?:token|secret|password|passwd|api_?key|chat_?id)\w*[\"']?\s*[=:]\s*[\"']?)([^\"'\s,)]{6,})", re.I)
    out = []
    for f in hits:
        txt = kv.sub(r"\1***CHHUPAYA***", pat.sub("***CHHUPAYA***", f.read_text(encoding="utf-8", errors="ignore")))
        safe = DATA / f"chowkidar-{f.parent.name}-{f.name}.txt"
        safe.write_text(f"# asli raasta: {f}\n" + txt, encoding="utf-8")
        with open(safe, "rb") as fh:
            tg.call("sendDocument", {"chat_id": tg._chat(), "caption": f"🛡 Chowkidar file (secret chhupa kar): {f}"},
                    {"document": fh})
        safe.unlink(missing_ok=True)
        out.append(str(f))
    return ("📎 Bheji: " + ", ".join(out) + "\nYe file Claude ko bhejein. Claude fix ZIP dega, use VM bot (Chowkidar) mein "
            "'🛠 Update' se lagayein. sabhinet khud Chowkidar nahi badalta (niyam).")



def health_md():
    """v2.0.5: docs/HEALTH.md - har brand x platform: chal raha / ruka (kab se, kyun, kya karna). Koi bhi AI yahin dekhe."""
    import datetime
    from . import state
    from .config import BRANDS
    h = state.get("platform_health") or {}
    lines = ["# HEALTH - kaun sa channel/page chal raha hai, kaun ruka (bot roz + har galti par likhta hai)",
             f"Updated: {datetime.datetime.now():%Y-%m-%d %H:%M} IST", "",
             "| Brand | Platform | Haal | Aakhri | Galti / kya karein |", "|---|---|---|---|---|"]
    fix = {"App Secret": "Meta App Secret: bot ko 'meta secret <secret>' (developers.facebook.com → app → Basic)",
           "login": "us platform ka login dobara (bot: /login ya token)", "token": "naya token bot ko",
           "ProcessingFailed": "IG ne file mana ki - bot IG-safe dobara banata hai; baar-baar ho to AI dekhe",
           "rok": "Meta ki rok (Account Status) - review"}
    for k in sorted(h):
        b, pf = k.split(":", 1)
        v = h[k]
        tip = next((t for w, t in fix.items() if w.lower() in (v.get("err") or "").lower()), "")
        lines.append(f"| {BRANDS.get(b, {}).get('name', b)} | {pf} | {('⏸ intezaar' if v.get('wait') else '✅ chal raha') if v.get('ok') else '❌ ruka'} | {v.get('t', '')} | "
                     f"{v.get('wait', '') if v.get('ok') else (v.get('err', '')[:110] + ' → ' + tip)} |")
    rc = state.get("redirect_check") or {}
    if rc:
        lines += ["", f"## Redirect jaanch ({rc.get('t')}): {rc.get('ok')} theek, {len(rc.get('bad') or [])} galat"]
        lines += [f"- {b}" for b in (rc.get("bad") or [])[:30]]
    try:
        from . import meta as M
        if M.has_token() and M._cfg().get("secret_bad"):
            lines += ["", "🔴 Meta App Secret galat - Instagram + story ruke. Owner: bot ko 'meta secret <secret>'."]
    except Exception:
        pass
    return "\n".join(lines) + "\n"



# ---------------- v2.0.6: owner ki baatcheet ka record (GitHub docs/CHAT.md) ----------------
CFILE = DATA / "chat.jsonl"


def _mask_tokens(t):
    """Sirf token jaise shabd (docs ke liye - 'key'/'token' shabd ke baad ka saada text nahi chhupata)."""
    import re
    t = re.sub(r"\bsn-[0-9a-f]{20,}\b", "sn-***", t)       # v2.1.4: ntfy topic (iske bina koi bhi hukum bhej sakta)
    t = re.sub(r"\d{8,10}:[A-Za-z0-9_-]{30,}|EAA[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|"
               r"github_pat_\w{30,}|GOCSPX-[\w-]{20,}|pina_[A-Za-z0-9]{20,}|\bcf[a-z]{2,3}_[A-Za-z0-9._\-]{20,}|"
               r"\b[0-9a-f]{40}\b", "***", t)
    return re.sub(r"(?<![/\w.-])(?=[A-Za-z0-9._\-]*\d)(?=[A-Za-z0-9._\-]*[A-Za-z])[A-Za-z0-9._\-]{36,}", "***", t)


def _mask(t):
    import re
    t = re.sub(r"\b(?:[a-z]{3,10}-){3,}[a-z]{3,10}-\d{3,6}\b", "***", t)      # v2.8.0: backup password (shabd-shabd-...-1234)
    t = re.sub(r"(?i)(password|passwd|parol|पासवर्ड)(\s*[:=-]?\s*\n?\s*)(\S{6,})", r"\1\2***", t)
    t = re.sub(r"\bsn-[0-9a-f]{20,}\b", "sn-***", t)       # v2.1.4: ntfy topic
    t = re.sub(r"\d{8,10}:[A-Za-z0-9_-]{30,}|EAA[A-Za-z0-9]{30,}|TH[A-Za-z0-9]{40,}|AIza[0-9A-Za-z_-]{30,}|"
               r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_\w{30,}|GOCSPX-[\w-]{20,}|\b[0-9a-f]{32}\b|pina_[A-Za-z0-9]{20,}", "***", t)
    # v2.0.8: Cloudflare naya format (cfut_/cfat_...), 40-hex (Pinterest secret), koi bhi lamba token jaisa shabd
    t = re.sub(r"\bcf[a-z]{2,3}_[A-Za-z0-9._\-]{20,}|\b[0-9a-f]{40}\b", "***", t)
    t = re.sub(r"(?<![/\w.-])(?=[A-Za-z0-9._\-]*\d)(?=[A-Za-z0-9._\-]*[A-Za-z])[A-Za-z0-9._\-]{32,}", "***", t)
    t = re.sub(r"(?i)\b(key|secret|token|password)\s+\S{6,}", r"\1 ***", t)
    t = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", "***@***", t)          # email
    t = re.sub(r"(?<!\d)(\+?91[\s-]?)?[6-9]\d{9}(?!\d)", "***", t)      # phone
    t = re.sub(r"(?<![\w.])(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?![\w.])", "***.***", t)   # v3.1.0: IP (VM ka pata public copy mein nahi)
    return t


def log_chat(text):
    import datetime
    import json
    CFILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CFILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "q": _mask(text)[:600]},
                           ensure_ascii=False) + "\n")
    mark_dirty()


BFILE = DATA / "botsaid.jsonl"


def log_bot(text):
    """v2.1.0: bot ne OWNER ko kya kaha (CHAT.md mein owner ki baat ke saath - poori analysis ke liye).
    Commenter ke comment wale alert kabhi nahi; @handle, secret, phone, email chhupe."""
    import datetime
    import json
    import re
    t = (text or "").strip()
    if not t or t.startswith("💬") or "par comment (" in t:
        return
    t = re.sub(r"@[A-Za-z0-9_.]{3,}", "@***", _mask(t))
    BFILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BFILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "b": t[:2000]},   # v2.8.0: poori report
                           ensure_ascii=False) + "\n")
    mark_dirty()


def _rows(fp, cut):
    import json
    try:
        rows = [json.loads(x) for x in fp.read_text(encoding="utf-8").splitlines() if x.strip()]
    except Exception:
        return []
    rows = [r for r in rows if r.get("t", "")[:10] >= cut]
    fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return rows


def chat_md(days=30):                             # v2.8.0 (owner): poori 30 din ki baat-cheet, secret chhupa
    """v2.1.0: owner ki baat (👤) + bot ka jawab (🤖), samay ke kram mein. 30 din. Secret/phone/email/@handle chhupe;
    commenter ke comment wale alert nahi (privacy policy)."""
    import datetime
    cut = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    rows = [(r["t"], 0, "👤 " + _mask(r["q"])[:1000]) for r in _rows(CFILE, cut)]
    rows += [(r["t"], 1, "🤖 " + _mask(r["b"])[:1500].replace("\n", " / ")) for r in _rows(BFILE, cut)]
    rows.sort()
    lines = ["# CHAT - owner (👤) aur bot (🤖) ki baat, 30 din, naya upar. Token/password/secret/phone/email/@handle chhupe.",
             "Commenter ke comment yahan kabhi nahi (privacy policy). AI: galat/adhoore jawab yahin se pakdo, fix ZIP do.", ""]
    lines += [f"- {t} {x}" for t, _, x in reversed(rows[-4000:])]
    return "\n".join(lines) + "\n"


def scrub_logs():
    """v2.0.8: purane chat/query log mein reh gaye token mitao (29 Oct: Cloudflare token CHAT/QUERIES mein gaya,
    GitHub ne push rok diya). Har start par - sasta aur surakshit."""
    import json
    n = 0
    for fp in (QFILE, CFILE, BFILE):
        try:
            rows = [json.loads(x) for x in fp.read_text(encoding="utf-8").splitlines() if x.strip()]
        except Exception:
            continue
        out = []
        for r in rows:
            r2 = {k: (_mask(v) if isinstance(v, str) and k in ("q", "reply", "b") else v) for k, v in r.items()}
            n += r2 != r
            out.append(r2)
        fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
    if n:
        mark_dirty()
    return n


# ---------------- v2.1.0: Chowkidar ki status list mein ytlistener -> sabhinet (owner ki DOHRI pushti se hi) ----------------
CW_DIR = pathlib.Path("/home/ubuntu/chowkidar")


def _cw_transform(txt):
    """v2.1.4: status/list mein ytlistener -> sabhinet, LEKIN 'X not in' wale filter ytlistener par hi rahein.
    v2.1.0 ne andha badla tha: `if "ytlistener" not in s` (purana hatao) -> `if "sabhinet" not in s` = sabhinet hi
    list se gayab. Ye usko bhi wapas theek karta hai."""
    import re
    txt = re.sub(r'(["\'])sabhinet\1(\s+not\s+in\b)', r'\1ytlistener\1\2', txt)       # ulta filter wapas
    txt = re.sub(r'(["\'])ytlistener\1(\s+not\s+in\b)', r'\1@@YTL@@\1\2', txt)        # filter bachao
    txt = re.sub(r"\bytlistener\b", "sabhinet", txt)
    return txt.replace("@@YTL@@", "ytlistener")


def _cw_files():
    """v2.1.9: sirf chowkidar.py / chowkidar_pro.py (jo service chalati hai). data/inbox ki purani upload ya *_new.py nahi."""
    hits = []
    for f in (CW_DIR / "chowkidar.py", CW_DIR / "chowkidar_pro.py"):
        try:
            if f.exists() and f.stat().st_size < 400_000:
                t = f.read_text(encoding="utf-8", errors="ignore")
                if ("ytlistener" in t or "sabhinet" in t) and _cw_transform(t) != t:
                    hits.append(f)
        except Exception:
            pass
    return hits


def _cw_files_old():
    roots = [CW_DIR] if CW_DIR.exists() else [pathlib.Path("/home/ubuntu")]
    hits = []
    for root in roots:
        for f in root.rglob("*.py"):
            sp = str(f)
            if ("sabhisaab-network" in sp or "/venv" in sp or "env/" in sp or "/.cache" in sp or "site-packages" in sp
                    or "/tgapi" in sp or "/telegram-bot-api" in sp):
                continue
            try:
                if f.stat().st_size < 400_000:
                    t = f.read_text(encoding="utf-8", errors="ignore")
                    if ("ytlistener" in t or "sabhinet" in t) and _cw_transform(t) != t:
                        hits.append(f)
            except Exception:
                pass
    return hits[:8]


def chowkidar_preview():
    import re
    files = _cw_files()
    if not files:
        return None, "✅ Chowkidar theek hai - kuch badalna nahi (status mein sabhinet, purana ytlistener sirf hatane wale filter mein)."
    lines = []
    for f in files:
        for n, ln in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if _cw_transform(ln) != ln:
                lines.append(f"{f.name}:{n}: {_mask(ln.strip())[:90]}  →  {_mask(_cw_transform(ln).strip())[:90]}")
    return files, ("🛡 Chowkidar mein ye badlaav honge (" + str(len(lines)) + "):\n" + "\n".join(lines[:12]) +
                   "\n\nBadlaav: status mein 'ytlistener' → 'sabhinet' (purana hatane wala filter wahi rahega). Pehle backup, phir Python jaanch, phir Chowkidar "
                   "restart. Chowkidar na chale to backup wapas (apne aap). Trading service ko koi chhoota nahi.")


def chowkidar_apply():
    import datetime
    import re
    import subprocess
    nowi = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
    if nowi.weekday() < 5 and datetime.time(9, 0) <= nowi.time() <= datetime.time(15, 35):
        return "⏸ Bazaar khula hai (9:00-15:35). Chowkidar ko 15:35 ke baad hi chhedenge - tab dobara 'chowkidar fix' likhein."
    files = _cw_files()
    if not files:
        return "✅ Kuch badalna nahi (Chowkidar pehle se theek)."
    stamp = nowi.strftime("%Y%m%d-%H%M%S")
    backups = []
    try:
        for f in files:
            b = f.with_name(f.name + f".bak-sabhinet-{stamp}")
            shutil.copy2(f, b)
            backups.append((f, b))
            f.write_text(_cw_transform(f.read_text(encoding="utf-8")), encoding="utf-8")
            r = subprocess.run(["python3", "-m", "py_compile", str(f)], capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                raise RuntimeError(f"Python jaanch fail: {f.name}: {r.stderr[-150:]}")
        r = subprocess.run(["sudo", "-n", "systemctl", "restart", "chowkidar"], capture_output=True, text=True, timeout=90)
        if r.returncode != 0:
            raise RuntimeError(f"restart nahi hua: {(r.stderr or r.stdout)[-150:]}")
        import time as _t
        _t.sleep(12)
        st = subprocess.run(["systemctl", "is-active", "chowkidar"], capture_output=True, text=True).stdout.strip()
        if st != "active":
            raise RuntimeError(f"restart ke baad Chowkidar '{st}'")
        return (f"✅ Chowkidar theek: {len(files)} file sudhari (status mein sabhinet), Chowkidar chalu (active). "
                f"Backup: *.bak-sabhinet-{stamp}. VM bot mein 'Status' dabakar dekhein.")
    except Exception as e:
        for f, b in backups:
            try:
                shutil.copy2(b, f)
            except Exception:
                pass
        subprocess.run(["sudo", "-n", "systemctl", "restart", "chowkidar"], capture_output=True, timeout=90)
        return f"↩️ Chowkidar ka badlaav WAPAS (backup se), Chowkidar purani file par chalu. Kaaran: {str(e)[:200]}"
