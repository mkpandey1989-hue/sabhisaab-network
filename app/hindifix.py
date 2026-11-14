"""v3.1.0 (11 Nov 2026 audit): HINDI LIKHAI KI PAKKI JAANCH + MARAMMAT.

Asli galti (live /jawab, code #3977, 10 Nov): 'परछਾਈ' - Devanagari shabd ke beech GURMUKHI (Punjabi) ki matra. AI (Gemini) kabhi-kabhi
ek jaisi dikhne wali doosri lipi ka akshar de deta hai; font mein wo tooti/alag dikhti hai aur Google/insaan dono ko galat lagti hai.
v2.9.2 ka text.fix sirf chhupe (zero-width) akshar hatata tha - doosri lipi nahi pakadta tha.

repair(text)   -> surakshit marammat (sirf wahi jo 100% pakka hai):
                  1) chhupe (zero-width) akshar (text.fix jaisa)
                  2) Devanagari shabd ke ANDAR ghusa doosri Bharatiya lipi ka akshar -> wahi Devanagari akshar (Unicode naam se milan)
                  3) dohri matra / dohra nukta / dohra halant / dohra anusvar -> ek
problems(text) -> jo marammat ke baad bhi galat hai (video/website par NAHI jaana chahiye): poora shabd doosri lipi mein,
                  Hindi+English ek hi shabd mein chipke ('पहाadi'), shabd ke shuru mein akeli matra, toota akshar (U+FFFD), dotted gola.
Sahi Hindi par koi asar nahi (tests/smoke.py mein 40+ shabd jaanche). English, ank, emoji, URL ko nahi chhedta.
"""
import re
import unicodedata

# Bharat ki doosri lipiyan jinke akshar Devanagari jaise dikhte hain (block shuru, naam)
_BLOCKS = [(0x0980, "BENGALI"), (0x0A00, "GURMUKHI"), (0x0A80, "GUJARATI"), (0x0B00, "ORIYA"), (0x0B80, "TAMIL"),
           (0x0C00, "TELUGU"), (0x0C80, "KANNADA"), (0x0D00, "MALAYALAM")]
_FOREIGN_RX = re.compile(r"[\u0980-\u0D7F]")
_DEV = r"\u0900-\u097F"
_DEV_RX = re.compile(f"[{_DEV}]")
_WORD_RX = re.compile(r"[^\s]+")
_ZW_BAD = re.compile(r"[\u200b\u2060\ufeff\u25cc]|[\u200c\u200d](?=[\u0900-\u0903\u093a-\u094c\u094e\u094f\u0955-\u0957\u0962\u0963])")
_MATRA = "\u093a\u093b\u093e-\u094c\u094e\u094f\u0955-\u0957\u0962\u0963"       # swar ki matrayein
_SIGNS = "\u0900-\u0903\u093c\u094d"                                              # chandrabindu/anusvar/visarg/nukta/halant
# khaas Gurmukhi chinh jinka seedha naam-milan nahi hota
_SPECIAL = {0x0A70: "\u0902", 0x0A71: "", 0x0A51: "", 0x0A75: "\u094d\u092f"}     # tippi->anusvar, addak->hatao, yakash->्य


def _map_char(ch):
    """Doosri lipi ka akshar -> wahi Devanagari akshar (Unicode naam ek jaisa ho tabhi). Na mile to None."""
    cp = ord(ch)
    if cp in _SPECIAL:
        return _SPECIAL[cp]
    for start, name in _BLOCKS:
        if start <= cp < start + 0x80:
            try:
                nm = unicodedata.name(ch)
            except ValueError:
                return None
            if not nm.startswith(name + " "):
                return None
            try:
                return unicodedata.lookup("DEVANAGARI " + nm[len(name) + 1:])
            except KeyError:
                return None
    return None


def _fix_word(w):
    if not _FOREIGN_RX.search(w) or not _DEV_RX.search(w):
        return w                       # sirf MILE-JULE shabd (Hindi ke andar ghusa paraya akshar); poora paraya shabd problems() pakdega
    out = []
    for ch in w:
        if _FOREIGN_RX.match(ch):
            m = _map_char(ch)
            out.append(ch if m is None else m)
        else:
            out.append(ch)
    return "".join(out)


def repair(text):
    """Surakshit marammat. str ke alawa kuch aaye to waisa hi lauta do."""
    if not isinstance(text, str) or not text:
        return text
    # NFC jaan-boojh kar NAHI: wo nukta wale akshar (ज़ ड़ फ़) ka roop badal deta hai aur 'sawal kabhi dobara nahi' wala
    # zindagi-bhar ka register (pipeline._qnorm ka hash) purane sawal ko naya samajh sakta tha. Sahi text byte-dar-byte waisa hi rahe.
    t = _ZW_BAD.sub("", text)
    if _FOREIGN_RX.search(t):
        t = _WORD_RX.sub(lambda m: _fix_word(m.group(0)), t)
    t = re.sub(f"([{_MATRA}])\\1+", r"\1", t)                 # ाा -> ा
    t = re.sub(r"([\u0901\u0902\u0903\u093c\u094d])\1+", r"\1", t)   # ंं / ़़ / ्् -> ek
    return t


def problems(text):
    """Marammat ke BAAD bhi jo galat hai. -> [chhota sandesh] (khaali = sab theek)"""
    if not isinstance(text, str) or not text:
        return []
    t = repair(text)
    out = []
    if "\ufffd" in t:
        out.append("toota akshar (\ufffd)")
    if "\u25cc" in t:
        out.append("dotted gola (akeli matra)")
    t_nolink = re.sub(r"https?://\S+|[#@]\S+", " ", t)
    for w in _WORD_RX.findall(t_nolink):
        core = w.strip(".,!?।:;\"'“”‘’()[]{}<>|*_~`-–—/\\₹%+=")
        if not core:
            continue
        if _FOREIGN_RX.search(core):
            out.append(f"doosri lipi ka akshar: {core[:24]}")
            continue
        if _DEV_RX.search(core) and re.search(r"[A-Za-z]", core):
            # 'A)टिहरी', 'BOOK=किताब', 'Q.सवाल' jaise jod theek hain; galti sirf jab ek hi shabd mein dono lipi BINA chinh ke chipki hon
            if re.search(f"[{_DEV}][A-Za-z]|[A-Za-z][{_DEV}]", core):
                out.append(f"Hindi+English chipke: {core[:24]}")
                continue
        if re.match(f"[{_MATRA}\u094d\u093c]", core):
            out.append(f"shabd ke shuru mein akeli matra: {core[:24]}")
        if re.search(f"[{_MATRA}][\u094d]", core):
            out.append(f"matra ke baad halant: {core[:24]}")
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq[:6]


TEXT_KEYS = ("title", "description", "thumb_title", "puzzle_q", "puzzle_answer", "puzzle_exp", "hook_line")


def repair_script(s):
    """Script ke HAR text par marammat (title, scene show+say, sawal, vikalp, jawab, wajah, thumbnail). Wahi niyam sab par,
    isliye 'sahi jawab vikalpon mein ek baar' wali jaanch kabhi nahi tootti. -> wahi dict"""
    if not isinstance(s, dict):
        return s
    for k in TEXT_KEYS:
        if isinstance(s.get(k), str):
            s[k] = repair(s[k])
    for k in ("puzzle_options", "fifty_out", "tags"):
        if isinstance(s.get(k), list):
            s[k] = [repair(x) if isinstance(x, str) else x for x in s[k]]
    for sc in s.get("scenes") or []:
        if isinstance(sc, dict):
            for k in ("show", "say"):
                if isinstance(sc.get(k), str):
                    sc[k] = repair(sc[k])
    th = s.get("thumb")
    if isinstance(th, dict) and isinstance(th.get("lines"), list):
        th["lines"] = [repair(x) if isinstance(x, str) else x for x in th["lines"]]
    return s


def script_problems(s):
    """Poori script ki likhai-galtiyan (public text + bolne wala text). -> [sandesh]"""
    out = []
    if not isinstance(s, dict):
        return out
    texts = [s.get(k) for k in TEXT_KEYS if k != "description"] + list(s.get("puzzle_options") or [])
    for sc in s.get("scenes") or []:
        if isinstance(sc, dict):
            texts += [sc.get("show"), sc.get("say")]
    for t in texts:
        for p in problems(t if isinstance(t, str) else ""):
            if p not in out:
                out.append(p)
    return out[:6]
