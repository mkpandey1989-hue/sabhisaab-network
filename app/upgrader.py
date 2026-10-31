"""v2.0: Khud-sudhaar (self-upgrade) engine - policy ke andar, bina owner ke, hamesha wapsi (rollback) ke saath.

Roz 05:30 (auto-heal): node/site repo/Gemini/disk/purani galti -> jo khud theek ho sake, theek; baaki ESCALATE.md mein.
Ravivaar 02:30 (upgrade):
 1. Python packages: freeze -> upgrade -> import + self-test -> fail ho to purana wapas (bot kabhi nahi rukta)
 2. Meta Graph API version: Google search se naya version, test call pass ho tabhi data/graph_ver.txt (restart par laagu)
 3. Gemini model list taaza (sabse naya free model pehle)
 4. Platform policy ki khabar -> 'sudhaar prastaav' list (code badalna ho to ESCALATE.md - Claude ke liye)
Jo bot khud nahi kar sakta (code badlaav) wo GitHub docs/ESCALATE.md mein likhta hai - koi bhi AI padh kar ZIP de sake.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import time
import requests
from . import state, tg, diary
from .config import BASE, DATA, GRAPH_VER
from .log import log

PY = str(BASE / "venv" / "bin" / "python")
PKGS = ["requests", "pillow", "soundfile", "numpy", "matplotlib", "google-auth", "google-auth-httplib2",
        "google-api-python-client"]


def _sh(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=BASE)
    return r.returncode, (r.stdout + r.stderr)[-800:]


def _selftest():
    rc, out = _sh([PY, "-c", "import app.bot, app.pipeline, app.youtube, app.website, app.siteknow, app.render; print('OK')"], 300)
    return rc == 0 and "OK" in out, out


def upgrade_packages():
    uv = shutil.which("uv") or os.path.expanduser("~/.local/bin/uv")
    if not os.path.exists(uv):
        return "packages: uv nahi mila (skip)"
    rc, frozen = _sh([uv, "pip", "freeze", "--python", PY], 300)
    if rc != 0:
        return "packages: freeze nahi hua (skip)"
    fz = DATA / "pip-freeze-before.txt"
    fz.write_text(frozen if "==" in frozen else "")
    rc, out = _sh(["nice", "-n", "19", uv, "pip", "install", "-q", "--upgrade", "--python", PY, *PKGS])
    ok, why = _selftest()
    if rc == 0 and ok:
        rc2, after = _sh([uv, "pip", "freeze", "--python", PY], 300)
        ch = sorted(set(after.splitlines()) - set(frozen.splitlines()))
        return "packages: " + (f"{len(ch)} naye version ✅ ({', '.join(ch[:5])})" if ch else "sab taaza ✅")
    _sh([uv, "pip", "install", "-q", "--python", PY, "-r", str(fz)])
    return f"packages: upgrade se gadbad, purane version wapas ✅ ({why[-120:]})"


def check_graph():
    """Naya Meta Graph version mile aur test pass ho to apnao (purana deprecation se pehle)."""
    try:
        from .brain import ask_grounded
        ans, _ = ask_grounded("What is the latest stable Meta Graph API version number (like v24.0)? "
                              "Reply only the version, e.g. v24.0")
        m = re.search(r"v(\d{2})\.0", ans)
        if not m:
            return "Graph: naya version pata nahi chala"
        new = f"v{m.group(1)}.0"
        if float(new[1:]) <= float(GRAPH_VER[1:]):
            return f"Graph: {GRAPH_VER} hi taaza ✅"
        from . import meta as M
        if not M.has_token():
            return f"Graph: {new} mila, token nahi (skip)"
        r = requests.get(f"https://graph.facebook.com/{new}/me", params={"access_token": M._cfg()["token"], "fields": "id"},
                         timeout=30)
        if r.status_code == 200 and "id" in r.json():
            (DATA / "graph_ver.txt").write_text(new)
            state.put("restart_needed", True)
            return f"Graph: {GRAPH_VER} -> {new} test pass ✅ (agle restart par laagu)"
        return f"Graph: {new} test fail ({r.status_code}) - purana {GRAPH_VER} hi chalega"
    except Exception as e:
        return f"Graph jaanch: {str(e)[:100]}"


def escalate(items):
    """Jo bot khud nahi sudhaar sakta - GitHub docs/ESCALATE.md (koi secret nahi). Claude/AI isse padh kar ZIP de."""
    state.put("escalate", [{"t": str(datetime.date.today()), "x": x[:300]} for x in items][-40:])


def escalate_md():
    rows = state.get("escalate") or []
    errs = sorted((state.get("err_count") or {}).items(), key=lambda kv: -kv[1])[:15]
    au = (state.get("audit") or {}).get("probs") or []
    lines = ["# ESCALATE - jo bot khud theek nahi kar paya (AI/developer ke liye)",
             f"Updated: {datetime.datetime.now():%Y-%m-%d %H:%M} IST. Koi secret nahi. Ise padh kar fix ZIP banayein "
             "(root mein install.sh, VERSION, app/, docs/).", "", "## Khule mudde"]
    lines += [f"- {r['t']}: {r['x']}" for r in rows] or ["- (koi nahi)"]
    lines += ["", "## Baar-baar wali galtiyan (ginti)"] + ([f"- {n}x {k}" for k, n in errs] or ["- (koi nahi)"])
    lines += ["", "## Subah ki jaanch"] + ([f"- {p}" for p in au] or ["- sab theek"])
    return "\n".join(lines) + "\n"


def heal():
    """Roz 05:30: jo khud theek ho sake wo theek; baaki escalate."""
    done, open_ = [], []
    try:
        from . import website
        if not website.ensure_node():
            open_.append("node install nahi hua (website JS jaanch sirf GitHub par)")
        try:
            website.sync()
        except Exception as e:
            shutil.rmtree(website.DIR, ignore_errors=True)
            try:
                website.sync()
                done.append("website repo dobara clone")
            except Exception as e2:
                open_.append(f"website repo sync: {str(e2)[:100]}")
    except Exception as e:
        open_.append(f"website: {str(e)[:100]}")
    try:
        from . import brain
        if not brain.discover(force=True):
            open_.append("Gemini model list nahi mili (key/quota)")
    except Exception as e:
        open_.append(f"gemini: {str(e)[:80]}")
    du = shutil.disk_usage("/")
    if du.used / du.total > 0.8:
        from .guard import cleanup
        done.append(cleanup())
        if shutil.disk_usage("/").used / du.total > 0.8:
            open_.append("Disk 80% se upar - Oracle boot volume 200 GB tak hai (free); stock/video safai dekhein")
    for k, n in (state.get("err_count") or {}).items():
        if n >= 3:
            open_.append(f"baar-baar galti ({n}x): {k}")
    escalate(open_)
    state.put("heal_last", {"t": str(datetime.datetime.now())[:16], "done": done, "open": open_[:20]})
    if done:
        diary.add("setting", "auto-heal: " + "; ".join(done)[:300])
    return done, open_


def weekly():
    res = [upgrade_packages(), check_graph()]
    try:
        from . import brain
        lst = brain.discover(force=True)
        res.append("Gemini: " + (" > ".join(lst[:3]) if lst else "list nahi mili"))
    except Exception as e:
        res.append(f"Gemini: {e}")
    try:
        from . import siteknow
        ch = siteknow.refresh(notify=False)
        res.append("Website gyaan taaza" + (f" ({len(ch)} badlaav)" if ch else " ✅"))
    except Exception as e:
        res.append(f"website gyaan: {str(e)[:80]}")
    heal()
    summ = " | ".join(res)
    state.put("upgrade_last", {"t": str(datetime.datetime.now())[:16], "summary": summ})
    diary.add("setting", "hafte ka khud-upgrade: " + summ[:400])
    tg.alert("green", "🔄 Hafte ka khud-upgrade (wapsi ke saath):\n• " + "\n• ".join(res))
    if state.get("restart_needed"):
        state.put("restart_needed", False)
        log("upgrader: restart naye Graph version ke liye")
        time.sleep(3)
        os._exit(0)          # systemd naye setting se chalu karega


def report():
    u = state.get("upgrade_last") or {}
    h = state.get("heal_last") or {}
    return ("🔄 Khud-sudhaar haal\n"
            f"• Aakhri hafte ka upgrade: {u.get('t', 'abhi nahi')} - {u.get('summary', '-')[:500]}\n"
            f"• Aaj ka auto-heal: {h.get('t', '-')} | theek kiya: {', '.join(h.get('done') or []) or '-'}\n"
            f"• Khule mudde (GitHub docs/ESCALATE.md mein, AI ke liye): {len(h.get('open') or [])}"
            + ("".join(f"\n   - {x[:120]}" for x in (h.get('open') or [])[:8])))
