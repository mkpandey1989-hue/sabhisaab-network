"""v3.3.2 audit-4 (owner: 'ek jaisa dhancha theek karo'): jis hisse ka jawab khud kehta hai 'is zile mein ye NAHI hai'
(glacier, bugyal, ILP, rail, cantonment...), uski heading ab saachi sawal-roop mein: 'Kya Nainital mein Glacier Hai?'.
Pehle heading 13 zilon mein ek jaisi thi ('Snout Locations, Length in Km...') aur page wo vaada karta tha jo zile mein hai
hi nahi (pathak aur Google dono ke liye galat sanket). Jawab (nahi + kahan milega) waisa hi rehta hai - kuch nahi hatta.
Sirf tab badalta hai jab: (1) heading ke turant baad wale para ki pehli line mein zile ka naam + 'nahi' ho, aur
(2) us line aur heading - dono mein ek hi vishay-shabd mile (neeche TOPIC). Warna heading waisi hi."""
import re

NEG = re.compile(r"\b(koi|kisi)\b[^.]{0,70}\bnahi\b|\bnahi (hai|hain|hota|hote|girti|lagta|lagti|milta|mila)\b", re.I)
# (pehli line mein shabd, heading mein shabd, sawal ka vishay)
TOPIC = [
    (r"glacier", r"glacier|snout|bamak", "Glacier"),
    (r"bugyal", r"bugyal", "Bugyal"),
    (r"antarrashtriya seema|international seema|\bILP\b|inner line", r"border|seema|\bILP\b|permit", "Antarrashtriya Seema ya ILP"),
    (r"railway station|rail station|rail line|railway line", r"rail", "Railway Station"),
    (r"airport", r"airport", "Airport"),
    (r"cantonment|chhavni", r"cantonment|chhavni|colonial|angrezi|dharohar|yeh hain", "Cantonment"),
    (r"tea estate|chai", r"tea|chai", "Chai Bagaan"),
    (r"ski", r"ski|winter sport", "Ski Slope"),
    (r"IMF|barf (se dhaki|wale|choti)|baraf wale|barf-chhoti|parvatarohan|mountaineering", r"peak|choti|mountaineering|parvatarohan", "Barf Wali Badi Chotiyan", 1),
    (r"trans-himalayan|darre|pass\b", r"pass|darr", "Oonche Himalayi Darre", 1),
    (r"hydropower|\bdam\b|baandh", r"hydro|dam|baandh|jal-vidyut", "Bada Baandh ya Hydropower"),
    (r"nagar nigam", r"nagar nigam|urban|nagar nikay|shahri", "Nagar Nigam"),
    (r"regimental centre", r"regiment", "Regimental Centre"),
    (r"university", r"education|university|shiksha", "University"),
    (r"sainik school", r"sainik", "Sainik School"),
    (r"glacial|boating lake|bada prasiddh boating|tal \(lakes\)|bade tal", r"lake|tal|kund", "Bada Tal (Jheel)"),
]


# haath se jaancha: in hisson ki POORI heading usi cheez par hai jo zile mein nahi (baaki hisson mein aur vishay bhi hain)
OK = {
    ("dehradun-bhugol-nadiyan", "15.1"), ("dehradun-bhugol-nadiyan", "16"), ("dehradun-bhugol-nadiyan", "20"),
    ("nainital-bhugol-nadiyan", "15.1"), ("nainital-bhugol-nadiyan", "16.1"), ("nainital-bhugol-nadiyan", "20.1"),
    ("nainital-mausam-jungle", "26.1"), ("nainital-ghumne-ki-jagah", "76.1"), ("nainital-ghumne-ki-jagah", "77.1"),
    ("nainital-arthvyavastha", "96.1"), ("nainital-patti-gaon-bazaar", "150.1"),
    ("rudraprayag-zila-prashasan", "4.2"), ("rudraprayag-kaise-pahunche", "84.1"),
    ("chamoli-kaise-pahunche", "83.1"), ("chamoli-kaise-pahunche", "84.1"), ("chamoli-gk-exam-career", "176.4"),
    ("uttarkashi-zila-prashasan", "4.1"), ("pithoragarh-kaise-pahunche", "84.1"),
    ("bageshwar-bhugol-nadiyan", "21.1"), ("bageshwar-ghumne-ki-jagah", "77"),
    ("haridwar-bhugol-nadiyan", "15.1"), ("haridwar-bhugol-nadiyan", "16.1"), ("haridwar-bhugol-nadiyan", "20.1"),
    ("haridwar-mausam-jungle", "26.1"),
    ("almora-bhugol-nadiyan", "20.1"), ("almora-mausam-jungle", "26.1"), ("almora-ghumne-ki-jagah", "76.1"),
    ("almora-ghumne-ki-jagah", "77.1"),
    ("pauri-garhwal-bhugol-nadiyan", "16"), ("pauri-garhwal-bhugol-nadiyan", "20"), ("pauri-garhwal-mausam-jungle", "26"),
    ("udham-singh-nagar-bhugol-nadiyan", "20.1"),
}


def neg_headings(p, log=None):
    D = p.get("D")
    if not p.get("district") or not D:
        return 0
    nm = D.split()[0].lower()
    items = p["items"]
    n = 0
    used = set()
    for i, it in enumerate(items[:-1]):
        if it[0] not in ("h2", "h3", "h4") or items[i + 1][0] not in ("p", "ans"):
            continue
        t = re.sub(r"^Seedha Jawab:\s*", "", str(items[i + 1][1]))
        first = re.split(r"(?<=[.?!;])\s", t)[0]
        if nm not in first.lower() or not NEG.search(first):
            continue
        h = it[1]
        mnum = re.match(r"^((?:[A-Z]\.)?\d{1,3}(?:\.\d{1,2})?\.?\s+)?(.*)$", h)
        num, body = mnum.group(1) or "", mnum.group(2)
        lvl = int(it[0][1])
        words = 0
        for x in items[i + 1:]:
            if x[0] in ("h2", "h3", "h4") and int(x[0][1]) <= lvl:
                break
            words += len(" ".join(str(z) for z in x[1:]).split())
        if (p["slug"], num.strip().rstrip(".")) not in OK:
            continue                         # sirf haath se jaanche hisse (jahan poori heading usi gair-maujood cheez par hai)
        if words > 260:                      # bada hissa - usmein aur bhi baatein hain, heading ka daayra mat ghatao
            continue
        for tp in TOPIC:
            fr, hr, topic = tp[:3]
            if topic in used:
                continue
            if re.search(fr, first, re.I) and re.search(hr, body, re.I):
                used.add(topic)
                new = "%sKya %s mein %s %s?" % (num, D, topic, "Hain" if len(tp) > 3 else "Hai")
                if log is not None:
                    log.append((p["slug"], h, new))
                items[i] = (it[0], new) + tuple(it[2:])
                n += 1
                break
    return n
