"""v3.4.21 (17 Nov 2026) - Telegram channel ke DISCUSSION GROUP mein quiz: log channel post ke neeche A/B/C/D likhein,
bot turant sahi/galat bataye + score/leaderboard (Ravivaar 20:00). Log roz wapas aate hain.

Setup (owner, ek baar): Telegram channel → Edit → Discussion → naya group banao/jodo → us group mein bot ko ADMIN banao
(sirf 'Delete messages' kaafi) → group mein likho: /quizgroup
Privacy: leaderboard ke liye sirf Telegram first name + Telegram number-id + score (phone number kabhi nahi). Group mein
'score hatao' = turant mitao. Privacy policy mein ye line (webfix.apply_privacy_gq) lagne ke BAAD hi naam/score rakha jaata hai -
tab tak sirf sahi/galat (kuch save nahi).
"""
import datetime
import re

from . import state, tg
from .config import IST
from .log import log

LETTERS = "ABCD"


def _send(chat, text, reply_to=None):
    d = {"chat_id": chat, "text": text[:3500], "disable_web_page_preview": "true"}
    if reply_to:
        d["reply_to_message_id"] = reply_to
        d["allow_sending_without_reply"] = "true"
    try:
        return tg.call("sendMessage", d)
    except Exception as e:
        log(f"gq send: {e}")


def _code(txt):
    m = re.search(r"#(\d{4})\b", txt or "")
    return m.group(1) if m else None


def _entry(code):
    for e in reversed(state.get("answer_key") or []):
        if str(e.get("code")) == str(code) or str(e.get("aid")) == str(code):
            return e
    return None


def _letter(text, opts):
    t = (text or "").strip()
    m = re.match(r"^\(?([A-Da-d])\)?(?:[\s).:-]|$)", t)
    if m:
        return m.group(1).upper()
    for i, o in enumerate(opts or []):
        if t.lower() == str(o).strip().lower():
            return LETTERS[i]
    return None


def store_ok():
    return bool(state.get("sitepatch_3421"))         # privacy policy mein line lagi -> tabhi naam/score


def on_group(m, owner):
    chat = m.get("chat") or {}
    cid = chat.get("id")
    txt = (m.get("text") or m.get("caption") or "").strip()
    who = (m.get("from") or {})
    if txt.lower().startswith("/quizgroup") and who.get("id") == owner:
        state.put("gq_chat", cid)
        return _send(cid, "✅ Quiz group juda. Channel ki har sawal-post ke neeche A/B/C/D likhiye - bot turant batayega sahi ya galat. "
                          "Har Ravivaar raat 8 baje hafte ke top 5. Apna score mitana ho to likhiye: score hatao")
    if cid != state.get("gq_chat"):
        return None
    if m.get("is_automatic_forward"):                # channel ki post group mein aayi -> code yaad
        c = _code(txt)
        if c:
            p = state.get("gq_posts") or {}
            p[str(m["message_id"])] = c
            state.put("gq_posts", dict(list(p.items())[-300:]))
        return None
    uid = str(who.get("id") or "")
    if txt.lower() in ("score hatao", "mera score hatao", "/scorehatao"):
        sc = state.get("gq_scores") or {}
        sc.pop(uid, None)
        state.put("gq_scores", sc)
        return _send(cid, "🗑 Aapka naam aur score mita diya.", m.get("message_id"))
    if txt.lower() in ("mera score", "/score"):
        s = (state.get("gq_scores") or {}).get(uid)
        return _send(cid, f"📊 Aapka score: {s['ok']}/{s['n']} sahi" if s else "Abhi koi score nahi - kisi sawal par A/B/C/D likhiye.",
                     m.get("message_id"))
    rp = m.get("reply_to_message") or {}
    if not rp or who.get("is_bot"):
        return None
    code = (state.get("gq_posts") or {}).get(str(rp.get("message_id"))) or _code(rp.get("text") or rp.get("caption"))
    if not code:
        return None
    e = _entry(code)
    if not e or not e.get("opts"):
        return None
    opts = [str(x) for x in e["opts"]]
    if str(e.get("ans")) not in opts:
        return None
    pick = _letter(txt, opts)
    if not pick:
        return None
    right = LETTERS[opts.index(str(e["ans"]))]
    done = state.get("gq_done") or {}
    first = uid not in (done.get(code) or [])
    if first:
        done.setdefault(code, []).append(uid)
        state.put("gq_done", dict(list(done.items())[-200:]))
    try:
        from .answers import answer_url
        link = answer_url(e.get("aid") or code, "telegram", e.get("brand"))
    except Exception:
        link = "https://sabhisaab.com/jawab"
    ok = pick == right
    line = ""
    if first and store_ok():
        sc = state.get("gq_scores") or {}
        s = sc.get(uid) or {"n": 0, "ok": 0, "wk": {}}
        wk = datetime.date.today().strftime("%G-%V")
        s["n"] += 1
        s["ok"] += int(ok)
        s["wk"] = {wk: (s.get("wk") or {}).get(wk, 0) + int(ok)}
        s["nm"] = (who.get("first_name") or "Dost")[:20]
        sc[uid] = s
        state.put("gq_scores", sc)
        line = f" | score {s['ok']}/{s['n']}"
    if ok:
        msg = f"✅ Sahi! 🎉{line}" + ("" if first else " (pehla jawab hi gina jaata hai)")
    else:
        msg = f"❌ Is baar nahi{line}. Sahi jawab + tareeka: {link}"
    return _send(cid, msg, m.get("message_id"))


def weekly_due(now=None):
    now = now or datetime.datetime.now(IST)
    return (now.weekday() == 6 and now.strftime("%H:%M") >= "20:00" and state.get("gq_wk_day") != str(now.date())
            and state.get("gq_chat") and store_ok())


def weekly():
    state.put("gq_wk_day", str(datetime.date.today()))
    wk = datetime.date.today().strftime("%G-%V")
    rows = sorted(((s.get("wk") or {}).get(wk, 0), s.get("nm", "Dost")) for s in (state.get("gq_scores") or {}).values())
    rows = [r for r in reversed(rows) if r[0] > 0][:5]
    if not rows:
        return None
    med = ["🥇", "🥈", "🥉", "4.", "5."]
    txt = "🏆 Is hafte ke TOP sahi jawab:\n" + "\n".join(f"{med[i]} {nm} - {n}" for i, (n, nm) in enumerate(rows)) + \
          "\n\nAgle hafte aap? Har sawal-post ke neeche A/B/C/D likhiye. Roz ke sawal: https://sabhisaab.com/jawab"
    _send(state.get("gq_chat"), txt)
    return None
