"""Chhota JSON store (thread-safe)."""
import json
import threading
from .config import STATE

_lock = threading.RLock()


def _load():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def get(key, default=None):
    with _lock:
        return _load().get(key, default)


def put(key, value):
    with _lock:
        d = _load()
        d[key] = value
        tmp = STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1))
        tmp.replace(STATE)


def update(key, fn, default=None):
    with _lock:
        d = _load()
        d[key] = fn(d.get(key, default))
        tmp = STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1))
        tmp.replace(STATE)
        return d[key]
