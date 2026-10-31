"""Bot ki diary (JSON lines): aapke hukum, confirmation, upload, galti. Restart ke baad bhi yaad."""
import datetime
import json
from .config import DATA, IST

FILE = DATA / "diary.jsonl"


def add(kind, text, **data):
    row = {"t": datetime.datetime.now(IST).isoformat(timespec="seconds"), "kind": kind, "text": text[:500], **data}
    with open(FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    _trim()


def recent(n=20, kinds=None):
    try:
        rows = [json.loads(x) for x in FILE.read_text(encoding="utf-8").splitlines() if x.strip()]
    except Exception:
        return []
    if kinds:
        rows = [r for r in rows if r["kind"] in kinds]
    return rows[-n:]


def _trim(keep=5000):
    try:
        lines = FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) > keep + 500:
            FILE.write_text("\n".join(lines[-keep:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def text_view(n=15):
    rows = recent(n)
    if not rows:
        return "📓 Diary khaali hai."
    icon = {"hukum": "🗣", "pakka": "✅", "upload": "📤", "galti": "🔴", "file": "📁", "setting": "⚙️"}
    return "📓 Diary (aakhri {}):\n".format(len(rows)) + "\n".join(
        f"{icon.get(r['kind'], '•')} {r['t'][5:16].replace('T', ' ')} {r['text'][:120]}" for r in rows)
