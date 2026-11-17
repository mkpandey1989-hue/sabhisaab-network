"""v3.4.21 (17 Nov 2026) - owner: "Quora ke sawal ka jawab bot taiyaar kare". Bot Quora par KHUD kuch post nahi karta
(Quora ka niyam - automated posting = ban). Owner sawal bhejta hai -> bot paste-layak jawab deta hai.

Hukum:  quora: <sawal>      (ya 'quora jawab <sawal>')  - Quora app mein sawal copy karke yahan bhejo.
Niyam (owner ke): pehli line ASLI anubhav (sirf neeche ki pakki baaton se, banawati nahi), 150-260 shabd, sawal ki bhasha
(Hindi sawal = Hindi, English = English), owner ka naam kabhi nahi, banawati aankde nahi, 20 Nov 2026 se har 3rd jawab
mein ek seedha juda calculator link (jab sach mein juda ho), usse pehle koi link nahi.
"""
import datetime
import re

from . import state, tg
from .log import log

SITE = "https://sabhisaab.com"
LINK_FROM = datetime.date(2026, 11, 20)
FACTS = ("I run a free Hindi calculator website (sabhisaab.com) with 180+ money and daily-life calculators",
         "I trade Nifty options myself and run a small automated setup for it",
         "I make daily Hindi quiz and puzzle videos",
         "I write detailed Uttarakhand district guides")


def _tool_for(q):
    try:
        from .answers import TOOL_NAMES
    except Exception:
        return None
    ql = q.lower()
    best = None
    for sl, nm in TOOL_NAMES.items():
        words = [w for w in re.split(r"[^a-z0-9]+", (sl + " " + nm).lower()) if len(w) > 2 and w not in ("calculator", "the", "aur")]
        hit = sum(1 for w in words if w in ql)
        if hit and (not best or hit > best[0]):
            best = (hit, sl, nm)
    return best[1:] if best else None


def draft(q):
    from . import brain
    hindi = bool(re.search(r"[ऀ-ॿ]", q))
    n = (state.get("qd_n") or 0) + 1
    tool = _tool_for(q) if datetime.date.today() >= LINK_FROM and n % 3 == 0 else None
    p = ("Write a Quora answer.\nQUESTION: " + q + "\n\nRULES:\n"
         f"- Language: {'simple Hindi (Devanagari)' if hindi else 'simple English'}.\n"
         "- FIRST line = one honest personal-experience line using ONLY one of these true facts (rephrase, do not add new "
         "claims): " + " | ".join(FACTS) + ". Pick the most relevant one.\n"
         "- 150-260 words, short paragraphs or a short numbered list, practical, specific, no hype.\n"
         "- Never invent statistics, returns, prices or laws you are not sure of; say 'check the latest' where it changes.\n"
         "- No person's name, no 'DM me', no promotion words.\n"
         + (f"- End with exactly one line: 'You can check your own numbers here: {SITE}/{tool[0]}' (in the answer language).\n" if tool
            else "- Do NOT include any link.\n")
         + "Return only the answer text.")
    txt = ""
    for fn in (getattr(brain, "ask_gemini", None), getattr(brain, "ask_cf", None)):
        if not fn:
            continue
        try:
            r = fn(p, json_mode=False, temperature=0.5)
            txt = (r if isinstance(r, str) else str(r)).strip()
            if len(txt) > 200:
                break
        except Exception as e:
            log(f"quora draft: {e}")
    if not txt:
        return "⚠️ Jawab nahi bana (AI abhi nahi chala - Gemini quota?). Thodi der baad phir bhejein."
    state.put("qd_n", n)
    return txt


def on_text(t, tl):
    m = re.match(r"^\s*quora(?:\s*jawab)?\s*[:\-]\s*(.{10,})$", t, re.S | re.I) or re.match(r"^\s*quora jawab\s+(.{10,})$", t, re.S | re.I)
    if not m:
        return None
    q = m.group(1).strip()
    tg.say("✍️ Quora jawab taiyaar kar raha hoon (30-60 sec)... Bot Quora par khud kuch nahi daalta - aap copy-paste karenge.")
    import threading

    def _go():
        a = draft(q)
        tg.say("👇 COPY karke Quora par paste karein. Pehli line (anubhav) ek baar padh lein - sach ho tabhi rakhein:")
        tg.say(a)
    threading.Thread(target=_go, daemon=True).start()
    return True
