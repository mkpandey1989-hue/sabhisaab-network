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
