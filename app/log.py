import datetime
from .config import LOGS

def log(msg: str) -> None:
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    with open(LOGS / "engine.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")
