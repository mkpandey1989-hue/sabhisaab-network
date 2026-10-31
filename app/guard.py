"""VM guard: trading/backtest ko kabhi takleef nahi. Sirf padhta hai, kuch nahi chhedta."""
import os
import shutil
import time
from .config import (MEM_MIN_MB, WAIT_SEC, TMP, STOCK, LOGS,
                     TMP_HOURS, STOCK_DAYS, LOG_DAYS)
from .log import log


def mem_avail_mb() -> int:
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    return 99999


def backtest_running() -> bool:
    me = os.getpid()
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == me:
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode(errors="ignore").lower()
        except OSError:
            continue
        if "backtest" in cmd and "sabhisaab-network" not in cmd:
            return True
    return False


CLK = os.sysconf("SC_CLK_TCK")
REELS_CG = "/sys/fs/cgroup/reels.slice/cpu.stat"
OTHERS_PAUSE = 1.2    # baaki programs (trading/backtest) itne core se zyada lein to ruko
OTHERS_RESUME = 0.8   # itne se kam ho jaye tab phir chalao
OTHERS_FULL = 0.5     # itne se kam ho to 2 core


def _busy_sec() -> float:
    with open("/proc/stat") as f:
        v = [int(x) for x in f.readline().split()[1:9]]
    user, nice, system, idle, iowait, irq, softirq, steal = v
    return (user + nice + system + irq + softirq + steal) / CLK


def _reels_sec() -> float:
    try:
        with open(REELS_CG) as f:
            for line in f:
                if line.startswith("usage_usec"):
                    return int(line.split()[1]) / 1e6
    except OSError:
        pass
    return 0.0


def others_cpu(interval=3.0) -> float:
    """Reels bot ko chhod kar baaki programs kitne core le rahe hain (apna load nahi ginta)."""
    b1, r1 = _busy_sec(), _reels_sec()
    time.sleep(interval)
    b2, r2 = _busy_sec(), _reels_sec()
    return max(0.0, ((b2 - b1) - (r2 - r1)) / interval)


import threading as _th
_DL = _th.local()


def set_deadline(ts):
    """v2.0.2: is samay ke baad intezaar nahi - 1 core par (Nice=10, trading ko pehla haq phir bhi) bana do."""
    _DL.ts = ts


def wait_until_ok(notify=None, max_wait_min=180) -> int:
    """Jab tak VM khaali na ho, ruko. Kitne thread use karne hain wo lautao."""
    paused = False
    start = time.time()
    while True:
        dl = getattr(_DL, "ts", None)
        if dl and time.time() >= dl and mem_avail_mb() > 700:
            if paused and notify:
                notify("⏰ Slot paas hai - 1 core par rendering jaari (trading ko phir bhi pehla haq).")
            return 1
        cpu = others_cpu()
        mem = mem_avail_mb()
        bt = backtest_running()
        limit = OTHERS_RESUME if paused else OTHERS_PAUSE
        if cpu < limit and mem > MEM_MIN_MB and not bt:
            if paused and notify:
                notify("▶️ VM khaali ho gaya, rendering phir shuru.")
            return 2 if cpu < OTHERS_FULL else 1
        if not paused:
            why = ("backtest chal raha hai" if bt else
                   f"trading/baaki programs {cpu:.1f} core le rahe hain" if cpu >= limit else
                   f"RAM sirf {mem} MB khaali")
            log(f"PAUSE: {why}")
            if notify:
                notify(f"⏸ Rendering ruki: {why}. Trading ko pehla haq. Khaali hote hi apne aap shuru hogi.")
            paused = True
        if time.time() - start > max_wait_min * 60:
            raise TimeoutError("VM bahut der se busy hai")
        time.sleep(WAIT_SEC)


def _older_than(path, seconds):
    try:
        return time.time() - path.stat().st_mtime > seconds
    except OSError:
        return False


def cleanup() -> str:
    freed = 0
    for p in TMP.iterdir():
        if _older_than(p, TMP_HOURS * 3600):
            freed += _size(p)
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    for p in STOCK.iterdir():
        if _older_than(p, STOCK_DAYS * 86400):
            freed += _size(p)
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    eng = LOGS / "engine.log"            # v2.0: engine.log kabhi rotate nahi hota tha
    try:
        if eng.exists() and eng.stat().st_size > 50 * 2**20:
            eng.rename(LOGS / f"engine.log.{time.strftime('%Y%m%d%H%M')}")
    except OSError:
        pass
    for p in LOGS.glob("*.log.*"):
        if _older_than(p, LOG_DAYS * 86400):
            freed += _size(p)
            p.unlink(missing_ok=True)
    msg = f"🧹 Safai: {freed / 1e6:.1f} MB khaali"
    log(msg)
    return msg


def _size(p) -> int:
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
