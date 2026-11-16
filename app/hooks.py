"""v2.7.1 (owner 10 Nov: 'ek hi sawal ko Zero se Pro level tak puchhne ke tareeke'): SAWAL PUCHHNE KA TAREEKA (hook engine).

Owner ke blueprint (Level 1-5 + 6 andaaz) ko POLICY ke saath:
  - Nakli aankda KABHI nahi ('99% fail', '95% log galat' = misleading; YouTube/Meta/AdSense) -> 'jaldbazi mat karna' jaisa sach.
  - 'Jawab X nahi hai' / 'Rahul kehta hai X' mein X hamesha ek GALAT vikalp (code se pakka) - jawab kabhi leak nahi.
  - Daravna/jhootha daava, IQ/IAS jaisa jhootha jod nahi. Behas sirf 'kiske saath ho' tak - ladai bhadkana nahi.
Har reel par ek andaaz; ek brand par lagataar do baar wahi nahi (templated se bachav). Owner: 'hook rotate' (default) ya
'hook <naam>' se ek pakka; 'hook haal' se list.
"""
import hashlib
import re

from . import state

STYLES = {
    # naam: (label, show, say)  {trap} = ek galat vikalp, {alt} = doosra galat vikalp
    "seedha":   ("Dimag lagao", "🧠 दिमाग लगाइए और बताइए!", "दिमाग लगाइए और बताइए!"),
    "samay":    ("5 sec challenge", "⏱️ सिर्फ 5 सेकंड! जल्दबाज़ी मत कीजिए", "सिर्फ पाँच सेकंड! जल्दबाज़ी मत कीजिए।"),
    "ulta":     ("Jawab {trap} nahi", "❌ जवाब {trap} नहीं है! ध्यान से पढ़िए", "जवाब {trap} नहीं है! ध्यान से पढ़िए।"),
    "bahas":    ("{a} vs {b}", "{a}: {trap} | {b}: नहीं! आप किसके साथ?", "{ao} का जवाब है {trap}, {bo} का कहना है - नहीं! आप किसके साथ हैं?"),
    "team":     ("Team A vs Team B", "टीम A: {trap} vs टीम B: {alt} — आप किस टीम में?", "टीम ए कहती है {trap}, टीम बी कहती है {alt}। आप किस टीम में हैं?"),
    "pehchaan": ("Topper ya jaldbaaz?", "🎓 देखते हैं आप टॉपर की तरह सोचते हैं या जल्दबाज़ की तरह!", "देखते हैं आप टॉपर की तरह सोचते हैं या जल्दबाज़ की तरह!"),
    "shart":    ("Pehli baar mein?", "🏆 पहली बार में सही बताया तो आपकी रीज़निंग कमाल!", "पहली बार में सही बताया, तो आपकी रीज़निंग कमाल की है!"),
    "jasoos":   ("Jasoos bano", "🕵️ जासूस बनिए — सुराग सवाल में ही है!", "जासूस बनिए, सुराग सवाल में ही छिपा है!"),
}
STYLES.update({   # v2.9.4 (owner: 'challenge jaisa lage, log utawale hon') - sab sach, nakli aankda nahi
    "dobara":   ("Pehli nazar ka dhokha", "👀 पहली नज़र में {trap} लगता है... पर रुकिए!", "पहली नज़र में {trap} लगता है, पर रुकिए! दोबारा सोचिए।"),
    "chunauti": ("Challenge accepted?", "🔥 हल करके दिखाइए - सिर्फ़ जवाब नहीं, तरीका भी!", "हल करके दिखाइए! कमेंट में सिर्फ़ जवाब नहीं, तरीका भी लिखिए।"),
    "tez":      ("Sirf tez dimaag", "⚡ तेज़ दिमाग वालों के लिए - घड़ी चालू!", "सिर्फ़ तेज़ दिमाग वालों के लिए! घड़ी चालू।"),
    "dost":     ("Dost ko tag karo", "🤝 जिस दोस्त को ये आता हो, उसे भेजिए!", "जिस दोस्त को लगता है वो सब जानता है, उसे ये सवाल भेजिए!"),
})
NEEDS_TRAP = {"ulta", "bahas", "team", "dobara"}
# v2.9.4 (owner: 'Rahul-Amit har sawal par - log pareshan'): har baar alag jodi (ek hi jodi 10 reel tak dobara nahi)
NAME_PAIRS = [("राहुल", "अमित"), ("प्रिया", "नेहा"), ("सोनू", "मोनू"), ("दादी", "पोता"), ("टीचर", "स्टूडेंट"), ("भैया", "दीदी"),
              ("पापा", "बेटी"), ("रीना", "मीना"), ("चाचा", "भतीजा"), ("बॉस", "इंटर्न"), ("मम्मी", "बेटा"), ("दुकानदार", "ग्राहक"),
              ("कप्तान", "खिलाड़ी"), ("नानी", "नाती"), ("रवि", "सलमा"), ("गुरप्रीत", "अनु"), ("पंडित जी", "मुंशी जी"), ("दोस्त A", "दोस्त B")]


# v3.1.1: 'का/की/को' se pehle badalne wale naam. Pehle saancha '{a} कहता है' tha - प्रिया/दादी/दीदी/मम्मी ke saath galat ling aur
# 'पंडित जी कहता है' galat aadar. Ab '... का जवाब है' (ling/aadar se mukt) + ye kaarak roop.
_OBL = {"पोता": "पोते", "भतीजा": "भतीजे", "बेटा": "बेटे"}


def _num(s):
    m = re.search(r"-?\d+(?:\.\d+)?", str(s).replace(",", ""))
    return float(m.group()) if m else None


def traps(options, answer):
    """Galat vikalp - jo sahi ke sabse paas (jaldbazi wala) pehle. Sahi kabhi nahi."""
    wrong = [o for o in (options or []) if str(o).strip() and str(o).strip() != str(answer).strip()]
    a = _num(answer)
    if a is not None and all(_num(o) is not None for o in wrong):
        wrong.sort(key=lambda o: abs(_num(o) - a))
    return wrong


def pick(brand, key, last=None, mode=None):
    """Kaunsa andaaz: owner ka pakka (mode) ya rotate (brand+sawal se, pichhle se alag)."""
    if mode is None:                               # v2.7.2: channel-wise pehle, phir sab ka
        mode = (state.get("hook_mode_brand") or {}).get(brand) or state.get("hook_mode") or "rotate"
    if mode in STYLES:
        return mode
    names = list(STYLES)
    try:                                           # v2.7.5: views ke hisaab se andaaz (naya pehle 3 baar, 25% khoj)
        from . import learn
        return learn.choose("hstyle", names, f"{brand}:{key}", avoid=last)
    except Exception:
        h = int(hashlib.md5(f"{brand}:{key}".encode()).hexdigest(), 16)
        s = names[h % len(names)]
        return names[(h + 1) % len(names)] if s == last else s


def spoken_q(script):
    """Sawal ko BOLNE layak banao (parde par jo likha hai wahi rehta hai). Code wali paheli ('अगर BANK = AZMJ, तो MILK = ?') mein
    akshar-dar-akshar bolna lamba aur ajeeb hai -> 'स्क्रीन पर कोड देखिए। MILK का कोड क्या होगा?'. Baaki sawal jaisa hai waisa
    ('= ?' -> 'कितना होगा?'), 150 akshar tak. Chitra wali paheli: sawal + 'चित्र ध्यान से देखिए।'"""
    q = re.sub(r"\s*\[[^\]]*\]", "", str(script.get("puzzle_q") or "")).strip()
    q = re.sub(r"\s*\((?:Code|कोड)\s*#\d+\)", "", q).strip()
    if not q:
        return ""
    m = re.search(r"\b([A-Z]{2,10})\s*=\s*\?", q)
    if m and len(re.findall(r"\b[A-Z]{2,10}\b", q)) >= 2:
        return f"स्क्रीन पर कोड देखिए। {m.group(1)} का कोड क्या होगा?"
    q = re.sub(r"\s*=\s*\?\s*$", " कितना होगा?", q)
    q = re.sub(r"\s*=\s*\?", " कितना", q)
    if script.get("diagram"):                    # chitra wali paheli: ank/teer bolna bekaar - seedha kaam ki baat
        return "चित्र ध्यान से देखिए। सवाल के निशान की जगह क्या आएगा?" if "?" in q else "चित्र ध्यान से देखिए और सही जवाब चुनिए।"
    if len(q) > 150:
        q = q[:150].rsplit(" ", 1)[0] + "..."
    return q


def apply(script, brand=None, mode=None):
    """Quiz script (puzzle_options + puzzle_answer) ke pehle scene ka hook + thumbnail tag badlo. Kuch na bane to waisa hi."""
    opts, ans = script.get("puzzle_options"), script.get("puzzle_answer")
    sc = script.get("scenes") or []
    if not opts or not ans or not sc:
        return script
    brand = brand or script.get("brand", "")
    lasts = dict(state.get("hook_last") or {})
    style = pick(brand, script.get("puzzle_hash") or script.get("title", ""), lasts.get(brand), mode)
    tr = traps(opts, ans)
    if style in NEEDS_TRAP and len(tr) < (2 if style == "team" else 1):
        style = "samay"
    label, show, say = STYLES[style]
    fill = {"trap": tr[0] if tr else "", "alt": tr[1] if len(tr) > 1 else ""}
    used_pairs = list(state.get("hook_pairs") or [])
    free = [p for p in NAME_PAIRS if "|".join(p) not in used_pairs[-10:]] or NAME_PAIRS
    h_ = int(hashlib.md5(str(script.get("puzzle_hash") or script.get("title", "")).encode()).hexdigest(), 16)
    pa, pb = free[h_ % len(free)]
    fill.update(a=pa, b=pb, ao=_OBL.get(pa, pa), bo=_OBL.get(pb, pb))     # v3.1.1: 'बेटा का' nahi, 'बेटे का' (kaarak roop)
    if style == "bahas":
        state.put("hook_pairs", (used_pairs + ["|".join((pa, pb))])[-30:])
    show, say, label = show.format(**fill), say.format(**fill), label.format(**fill)
    assert str(ans).strip() not in (fill["trap"], fill["alt"]) or not fill["trap"]     # jawab kabhi leak nahi
    s0 = dict(sc[0])
    code = script.get("reel_code")
    s0["show"] = show + (f" (Code #{code})" if code else "")
    q_ = re.sub(r"\W+", "", str(script.get("puzzle_q") or ""))[:40]
    later = " ".join(re.sub(r"\W+", "", str(x.get("say") or "")) for x in sc[1:])
    if q_ and q_ in later:                     # v2.9.3 (owner ki reel: pehla scene ~15 sec): sawal aage bola jaata hai to yahan sirf hook
        s0["say"] = say
    else:
        first = re.split(r"(?<=[।!?.])\s+", str(sc[0].get("say") or "").strip())[0][:110]
        fn = re.sub(r"\W+", "", first)
        asked_later = any("?" in str(x.get("say") or "") or str(x.get("say") or "").lstrip().startswith("सवाल") for x in sc[1:3])
        is_label = bool(fn) and (fn[:12] not in re.sub(r"\W+", "", str(script.get("puzzle_q") or "")) or len(fn) < 14)
        if q_ and is_label and not asked_later:  # v3.1.1 (owner ki reel 12 Nov): pehla vaakya sirf card ka NAAM tha ('कोडिंग-डिकोडिंग Code।')
            first = spoken_q(script) or first    # -> awaaz ne sawal kabhi bola hi nahi. Ab hook ke baad SAWAL bola jaata hai
        s0["say"] = (say + " " + first).strip()  # (agar agle scene mein sawal poochha ja raha ho to dohraate nahi).
    script = dict(script, scenes=[s0] + sc[1:], hook_style=style)
    th = dict(script.get("thumb") or {})
    th["tag"] = label[:24]
    script["thumb"] = th
    lasts[brand] = style
    state.put("hook_last", lasts)
    return script


def match(name):
    """v2.7.2: spelling galat ho to bhi samjho ('bahes' -> 'bahas', 'roteta' -> 'rotate')."""
    import difflib
    n = (name or "").strip().lower()
    alias = {"debate": "bahas", "behas": "bahas", "timer": "samay", "time": "samay", "reverse": "ulta", "story": "jasoos",
             "detective": "jasoos", "ego": "pehchaan", "bet": "shart", "basic": "seedha", "random": "rotate", "baari": "rotate"}
    if n in STYLES or n == "rotate":
        return n
    if n in alias:
        return alias[n]
    m = difflib.get_close_matches(n, list(STYLES) + ["rotate"] + list(alias), n=1, cutoff=0.6)
    return alias.get(m[0], m[0]) if m else None


def status_text():
    mode = state.get("hook_mode") or "rotate"
    rows = [f"{'✅' if mode == k else '•'} {k}: {v[1].format(trap='X', alt='Y')}" for k, v in STYLES.items()]
    return ("🎣 SAWAL PUCHHNE KA TAREEKA (hook)\nAbhi: " + ("har reel par baari-baari (rotate)" if mode == "rotate" else mode) + "\n\n"
            + "\n".join(rows) + "\n\nBadalna: 'hook rotate' ya 'hook <naam>' (jaise 'hook bahas').\n"
            "Niyam: nakli % kabhi nahi; 'jawab X nahi' mein X hamesha galat vikalp; jawab video mein leak nahi.")
