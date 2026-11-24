"""v2.9.1 (plan A6): COMMENT SE IDEA - hafte ke comment (sirf text, kabhi naam nahi) se Gemini 3 naye sawal-vishay + log kya
puchh rahe hain. Sirf owner ko report (kuch apne aap post nahi). Comment text pehle se 30 din ki privacy niti mein hai."""
import re

from . import diary
from .log import log

ASK = """Ye ek Hindi quiz/calculator network ke viewers ke comment hain (naam hata diye gaye). Inse batao:
1) log kis cheez mein sabse zyada ruchi le rahe hain, 2) 3 naye quiz-sawal ke VISHAY (paheli/ganit/GK - SIP/FD/loan salah nahi),
3) ek cheez jo log baar-baar puchh rahe/galat samajh rahe. Comment:
{c}
Return ONLY JSON: {{"ruchi": "...", "vishay": ["...", "...", "..."], "sawal": "..."}}"""


def texts(entries):
    """diary ki 'comment' line se sirf comment ka text (platform/brand/naam hata kar)."""
    out = []
    for e in entries:
        t = str(e.get("text") or e.get("t") or e.get("msg") or "")
        m = re.search(r"\):\s*(.+)$", t)
        if m:
            out.append(m.group(1)[:120])
    return out


def weekly():
    from .brain import ask_gemini
    try:
        ents = diary.recent(400, kinds=["comment"])
    except Exception as e:
        log(f"ideas diary: {e}")
        return ""
    cs = texts(ents)
    if len(cs) < 5:
        return ""
    try:
        r = ask_gemini(ASK.format(c="\n".join("- " + c for c in cs[-120:])), temperature=0.4)
    except Exception as e:
        log(f"ideas ai: {e}")
        return ""
    if not isinstance(r, dict):
        return ""
    return ("💡 Is hafte comment se seekh (naam kabhi nahi):\n• Ruchi: " + str(r.get("ruchi", ""))[:200]
            + "\n• Naye vishay: " + "; ".join(map(str, r.get("vishay") or []))[:300]
            + "\n• Log puchh/galat samajh rahe: " + str(r.get("sawal", ""))[:200])
