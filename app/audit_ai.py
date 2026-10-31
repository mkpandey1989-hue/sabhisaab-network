"""Teen-star audit ka 2 aur 3 star (1 star = audit.py ki 10 technical jaanch):
 2) Kanoon / policy / samaj (sab dharm-samuday ka samman, rajneeti nahi, bhramak dawa nahi, asli naam nahi)
 3) Tathya jaanch Google Search se (niyam, dar, tarikh, yojana) - galat ho to video nahi banegi."""
import json
import re
from .brain import ask_gemini, ask_grounded, _json
from .log import log

POLICY = """You are the Legal + Policy + Social-harmony auditor of a Hindi media company (YouTube, Meta, Pinterest,
Threads policies; Indian law; SEBI rules for finance; ASCI ad rules). Script JSON:
{script}
Reject if ANY: hate or mockery of any religion/caste/region/community/gender; politics or politicians; religious
comparison; real person/celebrity names; misleading or clickbait title not supported by content; guaranteed returns,
stock/crypto tips, medical/legal claims; copyrighted lyrics/quotes; violence, adult, gambling; content about minors;
fear-mongering; anything likely to hurt sentiments or invite legal complaints. Stories must be clearly fictional.
Return ONLY JSON: {{"ok": true/false, "issues": ["..."]}}"""

FACTS = """Fact-check this Hindi script for an Indian audience using Google Search (official/government/RBI/SEBI/
reputed sources). Check every number, rate, rule, date, scheme name, limit. Script:
{text}
Return ONLY JSON: {{"ok": true/false, "wrong": ["claim -> correct fact (source)"]}}. ok=false only if something is
factually wrong or outdated (not for style)."""

NEEDS_FACTS = re.compile(r"\d|%|₹|rule|niyam|नियम|योजना|yojana|tax|टैक्स|ब्याज|byaj|limit|सीमा|RBI|SEBI|EPFO|GST", re.I)


def check(brand, script):
    """Returns (ok, notes)."""
    if script.get("source") == "bank":       # haath se likhi, pehle se jaanchi script (Gemini band ho tab bhi kaam chale)
        return True, ["Bank script (pehle se jaanchi)"]
    lite = {k: script.get(k) for k in ("title", "description", "scenes")}
    try:
        p = ask_gemini(POLICY.format(script=json.dumps(lite, ensure_ascii=False)[:6000]), temperature=0.1)
    except Exception as e:
        log(f"policy audit: {e}")
        return False, ["policy audit nahi chala (Gemini) - surakshit rehne ke liye roka"]
    if not p.get("ok", False):
        return False, ["Policy: " + "; ".join(p.get("issues", [])[:3])]
    text = script.get("title", "") + "\n" + "\n".join(s.get("say", s.get("show", "")) for s in script.get("scenes", []))
    if brand == "sunonatak" and not NEEDS_FACTS.search(text):
        return True, ["Policy ✅", "Tathya: kahani (zaroorat nahi)"]
    if not NEEDS_FACTS.search(text):
        return True, ["Policy ✅", "Tathya: koi number/niyam nahi"]
    try:
        txt, src = ask_grounded(FACTS.format(text=text[:4000]))
        f = _json(txt)
        tag = "Google search"
    except Exception as e:
        log(f"fact grounded fail: {e}")
        try:
            f = ask_gemini(FACTS.replace("using Google Search ", "").format(text=text[:4000]), temperature=0.1)
            tag = "bina search (search nahi chala)"
        except Exception as e2:
            return False, [f"Tathya jaanch nahi chali: {e2}"]
    if not f.get("ok", False):
        return False, ["Tathya galat: " + "; ".join(f.get("wrong", [])[:3])]
    return True, ["Policy ✅", f"Tathya ✅ ({tag})"]
