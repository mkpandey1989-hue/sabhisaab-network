"""Koi bhi file samjho: zip / tgz / tar / 7z / rar (bsdtar se), photo, video, PDF, text. Phone ya laptop, dono se.
Update package (install.sh wala) ho to update; YouTube client JSON ho to surakshit; baaki inbox mein + list."""
import shutil
import subprocess
import tarfile
import time
import zipfile
from .config import DATA

INBOX = DATA / "inbox"
ARCHIVE = (".zip", ".tgz", ".tar.gz", ".tar", ".7z", ".rar", ".tar.xz", ".gz")


def extract(path, dest):
    dest.mkdir(parents=True, exist_ok=True)
    n = path.name.lower()
    try:
        if n.endswith(".zip"):
            zipfile.ZipFile(path).extractall(dest)
            return True
        if n.endswith((".tgz", ".tar.gz", ".tar", ".tar.xz")):
            with tarfile.open(path) as t:
                t.extractall(dest, filter="data")
            return True
    except Exception:
        pass
    if shutil.which("bsdtar"):      # 7z, rar, aur baaki sab
        r = subprocess.run(["bsdtar", "-xf", str(path), "-C", str(dest)], capture_output=True, text=True, timeout=300)
        return r.returncode == 0
    return False


def save(src_name):
    d = INBOX / time.strftime("%Y-%m-%d")
    d.mkdir(parents=True, exist_ok=True)
    base = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in src_name)[-80:] or "file"
    p = d / f"{time.strftime('%H%M%S')}_{base}"
    return p


def listing(folder, limit=15):
    files = [p for p in folder.rglob("*") if p.is_file()]
    lines = [f"• {p.relative_to(folder)} ({p.stat().st_size // 1024} KB)" for p in files[:limit]]
    if len(files) > limit:
        lines.append(f"... aur {len(files) - limit}")
    return files, "\n".join(lines)


# ---------------- v2.3.0 Step 5 (v11 se): photo gallery manager + ek file bhejna ----------------
def gallery_photos(brand=None, limit=10):
    """data/photos/<brand>/ ki sabse nayi photo (pehle nayi)."""
    from .config import BRANDS
    root = DATA / "photos"
    if not root.exists():
        return []
    if brand and brand in BRANDS:
        pts = list((root / brand).glob("*.jpg")) + list((root / brand).glob("*.png"))
    else:
        pts = list(root.rglob("*.jpg")) + list(root.rglob("*.png"))
    pts = [p for p in pts if p.is_file()]
    pts.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return pts[:limit]


def send_recent_photos(n=3, brand=None):
    """'last 3 photos wapas do' -> aakhri photo Telegram par wapas."""
    from . import tg
    pts = gallery_photos(brand, limit=max(1, min(n, 10)))
    if not pts:
        return "📸 Gallery mein abhi koi photo nahi."
    for p in pts:
        try:
            with open(p, "rb") as fh:
                tg.call("sendPhoto", {"chat_id": tg._chat(), "caption": f"📸 {p.parent.name}/{p.name}"}, {"photo": fh})
        except Exception:
            with open(p, "rb") as fh:
                tg.call("sendDocument", {"chat_id": tg._chat(), "caption": f"📸 {p.parent.name}/{p.name}"}, {"document": fh})
    return f"✅ Aakhri {len(pts)} photo wapas bhej di."


def delete_recent_photos(n=3, brand=None):
    """'photos delete kar do gallery se' -> aakhri N photo VM se hatao (dohri pushti ke baad bulaya jaata hai)."""
    from . import diary
    pts = gallery_photos(brand, limit=max(1, min(n, 20)))
    if not pts:
        return "📸 Gallery pehle se khaali."
    removed = []
    for p in pts:
        removed.append(f"{p.parent.name}/{p.name}")
        p.unlink(missing_ok=True)
    diary.add("setting", f"gallery se {len(removed)} photo hatayi: {', '.join(removed[:5])}")
    return f"🗑 Gallery se aakhri {len(removed)} photo mita di: {', '.join(removed[:5])}"


def send_single_file(query_name):
    """Sirf EK mangi gayi file (secret kabhi nahi; text file mein token chhupa kar)."""
    from . import tg, updater
    from .config import BASE
    q = (query_name or "").strip().lower()
    if not q:
        return "File ka naam likhein, jaise: 'single file AI_START.md'."
    if any(w in q for w in ("secret", ".env", "token", "gsc_sa", "meta.json", "threads.json", "pinterest.json", "relay.json",
                            "backup.json", "vault_key", "state.json")):
        return "🔒 Suraksha niyam: secret/token wali file kisi ko nahi bheji jaati."
    match = None
    for r in (BASE / "docs", DATA / "inbox", DATA / "site_repo" / "site", BASE / "app"):
        if not r.exists():
            continue
        for f in r.rglob("*"):
            if f.is_file() and "secrets" not in f.parts and ".git" not in f.parts and q in f.name.lower():
                match = f
                break
        if match:
            break
    if not match:
        return f"📁 '{query_name}' naam ki koi (non-secret) file nahi mili."
    if match.suffix.lower() in (".py", ".md", ".txt", ".json", ".html", ".js", ".css", ".sh"):
        safe_p = DATA / f"safe_{match.name}"
        safe_p.write_text(updater._mask(match.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
        with open(safe_p, "rb") as fh:
            tg.call("sendDocument", {"chat_id": tg._chat(), "caption": f"📄 {match.name} (token chhupa kar)"}, {"document": fh})
        safe_p.unlink(missing_ok=True)
    else:
        with open(match, "rb") as fh:
            tg.call("sendDocument", {"chat_id": tg._chat(), "caption": f"📁 {match.name}"}, {"document": fh})
    return f"✅ Sirf 1 file bheji: {match.name}"
