"""v3.4.34 (owner 19 Nov: "jitne bhi button hai agar mein likh kar ya audio se bolu bot samjhe, thori spelling mistake bhi").

Har button (neeche wala keyboard + 📖 Poora menu + pro buttons) ka naam - bina emoji, chhote-bade akshar, Hinglish spelling
(aa/a, ee/i, oo/u, th/t, w/v, z/j, ph/f, dohre akshar) aur awaaz se aaye shabd (Devanagari -> roman) - sab ek jaisa.
Sirf CHHOTA sandesh (max 6 shabd) button maana jaata hai; lambi baat AI samjhega (galat button kabhi na dabe).
"""
import difflib
import re

DEV = {"अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ा": "aa",
       "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ं": "n", "ँ": "n", "ः": "h",
       "क": "ka", "ख": "kha", "ग": "ga", "घ": "gha", "च": "cha", "छ": "chha", "ज": "ja", "झ": "jha", "ट": "ta", "ठ": "tha",
       "ड": "da", "ढ": "dha", "ण": "na", "त": "ta", "थ": "tha", "द": "da", "ध": "dha", "न": "na", "प": "pa", "फ": "pha",
       "ब": "ba", "भ": "bha", "म": "ma", "य": "ya", "र": "ra", "ल": "la", "व": "va", "श": "sha", "ष": "sha", "स": "sa",
       "ह": "ha", "़": "", "्": "_", "ड़": "da", "ढ़": "dha", "क़": "ka", "ज़": "ja", "फ़": "fa"}


def roman(s):
    out = []
    for ch in s:
        r = DEV.get(ch)
        if r is None:
            out.append(ch)
        elif r == "_":                      # halant: pichhla 'a' hatao
            if out and out[-1].endswith("a"):
                out[-1] = out[-1][:-1]
        else:
            if r in ("aa", "i", "ee", "u", "oo", "e", "ai", "o", "au") and out and out[-1].endswith("a") and len(out[-1]) > 1:
                out[-1] = out[-1][:-1]      # matra: vyanjan ka 'a' hatao
            out.append(r)
    return "".join(out)


def key(s):
    """Hinglish phonetic chaabi."""
    s = roman((s or "").lower())
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    for a, b in (("ph", "f"), ("th", "t"), ("dh", "d"), ("kh", "k"), ("gh", "g"), ("bh", "b"), ("chh", "ch"), ("sh", "s"),
                 ("w", "v"), ("z", "j"), ("q", "k"), ("ck", "k"), ("ee", "i"), ("oo", "u"), ("y", "i")):
        s = s.replace(a, b)
    s = re.sub(r"(.)\1+", r"\1", s)              # dohre akshar: 'aaj'='aj', 'haal'='hal'
    s = re.sub(r"a\b", "", s)                    # aakhri 'a' (video/videoa, hisaab/hisab)
    s = re.sub(r"\s+", " ", s).strip()
    return s


STOP = {"karo", "kro", "kar", "do", "de", "dena", "dikhao", "dikha", "bhejo", "batao", "bta", "btao", "please", "plz", "bot",
        "ka", "ki", "ke", "ko", "zara", "jara", "abhi"}


def _core(s):
    return " ".join(w for w in key(s).split() if w not in {key(x) for x in STOP})


def match(text, labels, cutoff=0.8):
    """text -> sabse milta button naam ya None."""
    t = (text or "").strip()
    if not t or t.startswith("/") or len(t.split()) > 6 or len(t) > 60:
        return None
    if t in labels:
        return t
    kt = _core(t)
    if len(kt) < 3:
        return None
    table = {}
    for lb in labels:
        k = _core(lb)
        if len(k) >= 3:
            table.setdefault(k, lb)
    if kt in table:
        return table[kt]
    m = difflib.get_close_matches(kt, list(table), n=2, cutoff=cutoff)
    if not m:
        return None
    if len(m) == 2 and difflib.SequenceMatcher(None, kt, m[0]).ratio() - difflib.SequenceMatcher(None, kt, m[1]).ratio() < 0.04:
        return None                              # do button barabar mile - andaza nahi, AI se poochho
    return table[m[0]]
