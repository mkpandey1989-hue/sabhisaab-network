import datetime
from .config import LOGS

def log(msg: str) -> None:
    msg = " ".join(str(msg).split())               # v2.9.8: multi-line JSON galti ek line mein (log saaf, ginti sahi)
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg[:2000]}"
    print(line, flush=True)
    with open(LOGS / "engine.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")
