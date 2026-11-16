"""v2.9.2 (owner: BotFather token): TELEGRAM QUIZ BOT (@SabHisaabQuizBot) - log khud aate hain, aaj ka sawal A/B/C/D tap,
sahi/galat + wajah ka link, code bhejo to purana jawab (zindagi bhar ke register se).
Niti: koi phone/naam save nahi. '/roz' sirf jo khud chune: unka chat-id (sirf roz 08:00 ek sawal bhejne ke liye), '/stop' se turant
mitta. Privacy page mein likha (W11). Main bot se alag token, alag thread - main bot par asar nahi.
"""
import json
import re
import threading
import time

import requests

from . import state
from .config import SECRETS, SITE
from .log import log

CFG = SECRETS / "quizbot.json"


def token():
    try:
        return json.loads(CFG.read_text()).get("token", "")
    except Exception:
        return ""


def save(tok):
    CFG.write_text(json.dumps({"token": tok.strip(), "t": time.time()}))
    CFG.chmod(0o600)


def parse(text):
    m = re.search(r"\b(\d{6,12}:[A-Za-z0-9_\-]{30,})\b", text or "")
    return m.group(1) if m else None


def api(method, data=None, tok=None, timeout=40):
    """v2.9.5: main bot wale SAB raaste (seedha + Cloudflare relay) - VM par seedha Telegram atakta tha, isliye /start nahi pahuncha."""
    from . import tg
    tok = tok or token()
    r, _b = tg._http("POST", f"/bot{tok}/{method}", timeout, data=data or {})
    j = r.json()
    if not j.get("ok"):
        state.put("quizbot_err", {"t": time.strftime("%Y-%m-%d %H:%M"), "e": f"{method}: {str(j.get('description'))[:150]}"})
    return j


def today_q():
    """Aaj ka sabse naya 4-vikalp wala jawab."""
    for e in reversed(state.get("answer_key") or []):
        if len(e.get("opts") or []) == 4 and e.get("ans") in e.get("opts"):
            return e
    return None


def kb(e):
    aid = str(e.get("aid") or e.get("code"))
    return json.dumps({"inline_keyboard": [[{"text": f"{'ABCD'[i]}) {str(o)[:28]}", "callback_data": f"q:{aid}:{i}"}]
                                           for i, o in enumerate(e["opts"][:4])]}, ensure_ascii=False)


def answer_for(aid):
    for e in reversed(state.get("answer_key") or []):
        if str(e.get("aid") or e.get("code")) == str(aid):
            return e
    return None


def lookup_code(code):
    from . import answers
    rows = [r for r in answers.archive_rows() if r.get("c") == code]
    if not rows:
        return f"Code #{code} nahi mila. Reel mein # ke baad wala number dobara dekhein: {SITE}/jawab"
    r = rows[-1]
    return f"#{r['c']} ({r['d']}, {r['b']}): {r['q']}\n✅ सही जवाब: {r['ans']}" + (f"\n{r['e']}" if r.get("e") else "") + f"\n{SITE}/jawab#c{r['a']}"


def handle(u):
    if "callback_query" in u:
        cq = u["callback_query"]
        try:
            _, aid, i = cq["data"].split(":")
            e = answer_for(aid)
            if not e:
                return api("answerCallbackQuery", {"callback_query_id": cq["id"], "text": "Ye sawal purana ho gaya"})
            ok = e["opts"][int(i)] == e["ans"]
            api("answerCallbackQuery", {"callback_query_id": cq["id"], "text": "🎉 Sahi!" if ok else "❌ Galat"})
            api("sendMessage", {"chat_id": cq["message"]["chat"]["id"], "text": ("🎉 Sahi jawab!" if ok else "❌ Galat.")
                                + f" सही जवाब: {e['ans']}\nPoori wajah: {SITE}/jawab#c{aid}\nAur sawal: /aaj"})
        except Exception as ex:
            log(f"quizbot cb: {ex}")
        return
    m = u.get("message") or {}
    chat = (m.get("chat") or {}).get("id")
    if not chat or (m.get("chat") or {}).get("type") != "private":
        return
    t = (m.get("text") or "").strip()
    subs = set(state.get("quiz_subs") or [])
    if t.startswith("/start"):
        return api("sendMessage", {"chat_id": chat, "text": "🙏 Sab Hisaab Quiz mein swagat!\n/aaj - aaj ka sawal\nReel ka code (jaise 1270) bhejein - "
                                   "uska jawab\n/roz - roz subah 8 baje ek sawal (band: /stop)\nHum aapka naam/number save nahi karte."})
    if t.startswith("/roz"):
        subs.add(chat)
        state.put("quiz_subs", sorted(subs))
        return api("sendMessage", {"chat_id": chat, "text": "✅ Roz subah 8 baje ek sawal aayega. Band: /stop"})
    if t.startswith("/stop"):
        subs.discard(chat)
        state.put("quiz_subs", sorted(subs))
        return api("sendMessage", {"chat_id": chat, "text": "✅ Band. Aapka chat-id mita diya."})
    mc = re.fullmatch(r"#?(\d{3,6})", t)
    if mc:
        return api("sendMessage", {"chat_id": chat, "text": lookup_code(mc.group(1))})
    e = today_q()
    if not e:
        return api("sendMessage", {"chat_id": chat, "text": f"Aaj ka sawal jaldi aa raha hai. Tab tak: {SITE}/jawab"})
    return api("sendMessage", {"chat_id": chat, "text": f"🧩 {e['q']}\nSoch kar tap karein:", "reply_markup": kb(e)})


def daily():
    e = today_q()
    if not (e and token()):
        return 0
    n = 0
    for chat in list(state.get("quiz_subs") or [])[:2000]:
        try:
            api("sendMessage", {"chat_id": chat, "text": f"🌅 Aaj ka sawal: {e['q']}", "reply_markup": kb(e)})
            n += 1
            time.sleep(0.05)                      # Telegram seema (30/sec) se kaafi neeche
        except Exception:
            pass
    return n


def _loop():
    off = 0
    hooked = False
    while True:
        if not token():
            time.sleep(60)
            continue
        try:
            if not hooked:                         # purana webhook ho to getUpdates kabhi kuch nahi deta
                api("deleteWebhook", {"drop_pending_updates": "false"})
                hooked = True
            r = api("getUpdates", {"offset": off, "timeout": 50}, timeout=65)
            state.put("quizbot_poll", time.strftime("%Y-%m-%d %H:%M:%S"))
            for u in r.get("result", []):
                off = u["update_id"] + 1
                try:
                    handle(u)
                except Exception as ex:
                    log(f"quizbot: {ex}")
        except Exception as ex:
            log(f"quizbot poll: {str(ex)[:80]}")
            state.put("quizbot_err", {"t": time.strftime("%Y-%m-%d %H:%M"), "e": f"poll: {str(ex)[:150]}"})
            time.sleep(15)


_TH = {"t": None}


def start():
    th = threading.Thread(target=_loop, daemon=True, name="quizbot")
    th.start()
    _TH["t"] = th
    return th


def ensure():
    """Thread mar gaya ho to dobara (watchdog har kuch minute)."""
    if token() and not (_TH["t"] and _TH["t"].is_alive()):
        start()
        return True
    return False


def status_text():
    if not token():
        return "🤖 Quiz bot: token nahi. Bhejein: quiz bot token <token>"
    e = state.get("quizbot_err") or {}
    return (f"🤖 Quiz bot: {'chal raha ✅' if (_TH['t'] and _TH['t'].is_alive()) else 'band ❌ (dobara chalu kar raha)'}\n"
            f"• Aakhri jaanch (getUpdates): {state.get('quizbot_poll') or 'abhi nahi'}\n"
            f"• /roz wale: {len(state.get('quiz_subs') or [])}\n"
            + (f"• Aakhri galti: {e.get('t')} - {e.get('e')}" if e else "• Koi galti nahi"))
