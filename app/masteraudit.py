"""v3.4.34 (owner 19 Nov: "ek master audit ka system rakho taaki sab maintain kare jaise jaise humne bola").

OWNER KE NIYAM -> roz ki pakki jaanch (21:55) + 'master audit' hukum. Har niyam: jaancho -> jo khud theek ho sake wo turant
theek (auto) -> baaki saaf sandesh (kya toota, kahan, kya karna). Sab theek ho to roz sirf ek line.
Naya niyam judta hai to yahan RULES mein ek line + ek jaanch.
"""
import datetime
import re
import time

from . import state, tg
from .config import BRANDS, SITE
from .log import log

RULES = [
    ("sawal", "Bachkana/ghisa-pita internet trick-sawal kabhi nahi (19 Nov)"),
    ("band", "Owner/bot ne jo vishay ya sawal-type band kiya wo kabhi nahi"),
    ("index", "Indexing suchi mein sirf wahi page jo SACH MEIN index nahi; poore link; kul/ho gaye/baaki"),
    ("link", "Bot ke har sandesh mein POORA link (https://...), adhoora '/slug' ya kata hua nahi"),
    ("comment", "Asli quiz-jawab comment kabhi chhupa na rahe"),
    ("github", "CHAT/PENDING/HEALTH taaza GitHub par (har ghante)"),
    ("post", "Roz ke schedule ki har reel samay par gayi (ya 'Mat daalo' ke baad nayi bani)"),
    ("jawab", "Har 'sawal wali post' ka jawab website par LIVE"),
    ("galti", "Baar-baar wali galti 24 ghante mein khud theek - na ho to saaf sandesh"),
]


def _bot_msgs(hours=24):
    try:
        from . import updater
        cut = (datetime.datetime.now() - datetime.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
        return [r.get("b", "") for r in updater._rows(updater.BFILE, cut[:10]) if str(r.get("t", "")) >= cut]
    except Exception:
        return []


def check_sawal():
    from .qbank import cliche
    from .perf import word_blocked
    cut = str(datetime.date.today() - datetime.timedelta(days=2))
    bad, blk = [], []
    for e in state.get("answer_key") or []:
        if str(e.get("date", "")) < cut:
            continue
        q = str(e.get("q", ""))
        if cliche(q, e.get("opts")):
            bad.append(f"#{e.get('code')} {q[:60]}")
        w = word_blocked(q)
        if w:
            blk.append(f"#{e.get('code')} ('{w}') {q[:50]}")
    out = []
    if bad:
        out.append(("sawal", "Bachkana sawal post hua: " + "; ".join(bad[:4]), "video hatana ho to '🗑 Post hatao'"))
    if blk:
        out.append(("band", "Band vishay wala sawal gaya: " + "; ".join(blk[:4]), "'band vishay' dekhein"))
    return out


def check_index():
    from . import idxlink
    last = state.get("idx_last") or {}
    if last.get("day") != str(datetime.date.today()):
        return []
    st, _d = idxlink._status()
    wrong = [u for u in last.get("urls") or [] if (st.get(u) or {}).get("ok")]
    if wrong:
        return [("index", f"Aaj ki indexing suchi mein {len(wrong)} page index ho chuke the: " + ", ".join(wrong[:3]),
                 "bot agli suchi mein khud hata dega")]
    return []


SLUG_RX = re.compile(r"(?:^|[\s(•:])/(?!jawab\b)[a-z0-9][a-z0-9-]{3,}(?=[\s),.]|$)")
CUT_RX = re.compile(r"https?://\S{10,}(?:\.\.\.|…)")


def check_links():
    short, cut = 0, 0
    ex = ""
    for m in _bot_msgs(24):
        if "sabhisaab" in m.lower() or "index" in m.lower():
            s_ = SLUG_RX.findall(m)
            if s_ and "sabhisaab.com" not in m:
                short += 1
                ex = ex or s_[0].strip()
        if CUT_RX.search(m):
            cut += 1
    out = []
    if short:
        out.append(("link", f"{short} sandesh mein adhoora page link (jaise '{ex}')", "Claude ko ye sandesh bhejein - code mein poora link"))
    if cut:
        out.append(("link", f"{cut} sandesh mein kata hua link ('...')", "Claude ko bhejein"))
    return out


def check_comment():
    u = state.get("uh_last") or {}
    out = []
    if u.get("errs"):
        out.append(("comment", "Chhupe comment ki jaanch mein galti: " + "; ".join(u["errs"][:2]), "Meta token/permission dekhein"))
    try:
        from . import growth
        r = growth.unhide_answers()                 # auto-theek
        if r:
            out.append(("comment", f"{len(r)} asli jawab chhupe mile - WAPAS dikha diye (auto-theek) ✅", ""))
    except Exception as e:
        log(f"master comment: {e}")
    return out


def check_github():
    at = float(state.get("docs_push_at") or 0)
    if time.time() - at > 3 * 3600:
        state.put("docs_dirty", True)               # auto: agle loop mein push
        return [("github", f"GitHub copy {int((time.time() - at) / 3600)} ghante purani - abhi dobara bhej raha hoon (auto)", "")]
    return []


def check_posts():
    from . import pipeline
    now = pipeline.now()
    today = str(now.date())
    hist = [h for h in (state.get("history") or []) if h.get("date") == today]
    jobs = pipeline.jobs()
    miss = []
    for b, slots in pipeline.schedule().items():
        for hh in [x.strip() for x in str(slots).split(",") if x.strip()]:
            h, m = map(int, hh.split(":"))
            slot = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if now < slot + datetime.timedelta(minutes=40):
                continue
            got = [j for j in jobs.values() if j.get("brand") == b and str(j.get("slot", ""))[:16] == slot.isoformat()[:16]]
            if any(j.get("status") == "posted" for j in got):
                continue
            if any(j.get("status") == "rejected" for j in got) and not any(j.get("status") not in ("rejected", "failed") for j in got):
                miss.append(f"{BRANDS[b]['name']} {hh} (aapne hatayi, nayi nahi bani)")
            elif not got and sum(1 for x in hist if x.get("brand") == b) >= len(str(slots).split(",")):
                continue
            elif not any(j.get("status") == "posted" for j in got):
                st_ = ", ".join(sorted({j.get("status", "?") for j in got})) or "bani hi nahi"
                miss.append(f"{BRANDS[b]['name']} {hh} ({st_})")
    if miss:
        return [("post", "Aaj ye slot khaali: " + "; ".join(miss[:6]), "'⏳ Pending' / '🎬 Abhi video'")]
    return []


def check_jawab():
    try:
        from . import sawalpost
        live = sawalpost.live_ids()
        if live is None:
            return [("jawab", "Website ka /jawab nahi khula (jaanch nahi ho payi)", "site haal dekhein")]
        recent = [str(e.get("aid") or e.get("code")) for e in (state.get("answer_key") or [])[-12:]
                  if str(e.get("date", "")) < str(datetime.date.today())]
        gone = [a for a in recent if a not in live]
        if gone:
            state.put("answer_dirty", True)          # auto: /jawab dobara banega
            return [("jawab", f"{len(gone)} purane sawal ka jawab website par nahi (#{', #'.join(gone[:4])}) - /jawab dobara bana raha (auto)", "")]
    except Exception as e:
        log(f"master jawab: {e}")
    return []


def check_errors():
    ec = state.get("err_count") or {}
    prev = state.get("ma_err_prev") or {}
    grew = [(k, n) for k, n in ec.items() if n - prev.get(k, 0) >= 3]
    state.put("ma_err_prev", dict(ec))
    if grew:
        return [("galti", "Baar-baar galti (24 ghante): " + "; ".join(f"{n - prev.get(k, 0)}x {k[:60]}" for k, n in grew[:4]),
                 "ye sandesh Claude ko bhejein")]
    return []


CHECKS = [check_sawal, check_index, check_links, check_comment, check_github, check_posts, check_jawab, check_errors]


def run():
    found = []
    for fn in CHECKS:
        try:
            found += fn()
        except Exception as e:
            log(f"master {fn.__name__}: {e}")
    state.put("ma_last", {"t": time.strftime("%Y-%m-%d %H:%M"), "n": len(found)})
    return found


def text(found=None):
    found = run() if found is None else found
    names = dict(RULES)
    if not found:
        return f"🛡 MASTER AUDIT ({time.strftime('%d %b %H:%M')}): aapke {len(RULES)} niyam - sab ✅ theek."
    L = [f"🛡 MASTER AUDIT ({time.strftime('%d %b %H:%M')}): {len(found)} baat ({len(RULES)} niyam jaanche)"]
    for k, what, do in found:
        L.append(f"• [{names.get(k, k)}]\n   {what}" + (f"\n   → {do}" if do else ""))
    return "\n".join(L)


def due(now):
    return now.strftime("%H:%M") >= "21:55" and state.get("ma_day") != str(now.date())


def on_text(tl):
    if tl in ("master audit", "masteraudit", "master jaanch", "niyam jaanch", "sab niyam", "audit karo", "master audit karo"):
        import threading
        tg.say("🛡 Saare niyam jaanch raha hoon...")
        threading.Thread(target=lambda: tg.say(text()), daemon=True).start()
        return True
    if tl in ("niyam", "mere niyam", "owner niyam"):
        tg.say("📜 AAPKE NIYAM (master audit roz 21:55 jaanchta hai):\n" + "\n".join(f"{i}. {r}" for i, (_k, r) in enumerate(RULES, 1)))
        return True
    return None
