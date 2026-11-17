#!/usr/bin/env python3
"""Uttarakhand project: 14 Word file -> sabhisaab.com ke page (queue ke liye). Kuch bhi delete nahi:
public na hone wala hissa internal/ mein, duplicate ka pehla roop site par aur baaki jagah uska link."""
import json, re, os, sys, difflib, collections, html as H, hashlib, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import DISTRICTS, HUB_FILE, load_blocks, split_modules, assign_themes
from themes import THEMES, ORDER, NIC, IMAGES
from items import Builder, feed, hnum
from clean import fix_text, esc, clean_heading, is_deva

SITE = "https://sabhisaab.com"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/ukout"
LIVE_SITE = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/sabhisaab_site/site"

# ------------------------------------------------------------------ hub ka bantwara
HUB_PAGES = [
    ("uttarakhand", "hub", None, [1, 2, 3, 16, 26, 27, 29, 30, 25, "explore", "quick", "intro"],
     "Uttarakhand Guide 2026: 13 Zile, Char Dham, GK",
     "Uttarakhand ki Poori Jaankari: 13 Zile, Char Dham, Sanskriti aur Itihas",
     "Uttarakhand ki poori jaankari ek jagah: 13 zile, Garhwal-Kumaon farak, Char Dham, zameen ke niyam, Himachal se tulna, galatfehmiyan aur har zile ki guide.",
     "Uttarakhand guide (sab zile)"),
    ("uttarakhand-char-dham-panch-kedar", "hubtopic", None, [5, 17],
     "Char Dham, Panch Kedar aur Panch Prayag",
     "Uttarakhand ke Teerth: Char Dham, Panch Kedar, Panch Badri aur Shakti Peeth",
     "Uttarakhand ke dharmik circuit: Char Dham, Panch Kedar, Panch Badri, Panch Prayag, shakti peeth aur prasiddh mandiron ki zila-wise directory.",
     "Char Dham aur teerth"),
    ("uttarakhand-bhugol-nadiyan-glacier", "hubtopic", None, [4, 18],
     "Uttarakhand ka Bhugol: Nadiyan, Glacier, Taal",
     "Uttarakhand ka Bhugol: Himalaya, Nadiyan, Glacier, Taal aur Sanrakshit Kshetra",
     "Uttarakhand ka bhugol: Himalaya ki shrinkhalayein, nadiyan aur unke udgam, glacier, taal, jharne, darre, mausam aur national park-sanctuary.",
     "Bhugol, nadiyan aur glacier"),
    ("uttarakhand-zameen-kanoon-nali-mutthi", "hubtopic", None, [6],
     "Uttarakhand Bhoo Kanoon 2025 aur Nali Naap",
     "Uttarakhand mein Zameen: Nali-Mutthi ka Naap aur Bhoo Kanoon 2025",
     "Uttarakhand mein zameen ke naap (nali, mutthi, bisi), khasra-khatauni aur bhoo-kanoon 2025 ke niyam: bahari log kya kharid sakte hain aur kya nahi.",
     "Zameen ke niyam aur naap"),
    ("uttarakhand-pahadi-virasat-tyohar", "hubtopic", None, [7, 8, 21],
     "Pahadi Virasat: Tyohar, Lok-Kala aur Khana",
     "Uttarakhand ki Pahadi Virasat: Tyohar, Lok-Kala, Khana aur Pahadi Calendar",
     "Uttarakhand ki pahadi virasat: buzurgon ki duniya, tyohar, lok-kala, pahadi khana aur anaaj, saath mein saal bhar ka pahadi calendar aur kheti ka chakra.",
     "Pahadi virasat aur tyohar"),
    ("uttarakhand-itihas-prasiddh-hastiyan", "hubtopic", None, [9, 19],
     "Uttarakhand ka Itihas aur Prasiddh Hastiyan",
     "Uttarakhand ka Itihas: Katyuri se Rajya Andolan Tak aur Prasiddh Hastiyan",
     "Uttarakhand ka itihas Katyuri aur Chand raajvansh se Gorkha raj, angrezi daur, swatantrata sangram aur rajya andolan tak, saath mein prasiddh hastiyan.",
     "Itihas aur hastiyan"),
    ("uttarakhand-yatra-planner", "hubtopic", None, [10, 11, 13],
     "Uttarakhand Yatra Planner: Kab aur Kaise",
     "Uttarakhand Yatra Planner: Kab Jayein, Kaise Pahunchein aur Suraksha",
     "Uttarakhand yatra ki taiyari: kis mausam mein kahan jayein, rail-hawai-sadak raaste, permit, mausam, aapda se suraksha aur zaroori niyam.",
     "Yatra planner"),
    ("uttarakhand-prashasan-arthvyavastha", "hubtopic", None, [12, 20],
     "Uttarakhand Prashasan aur Arthvyavastha",
     "Uttarakhand ka Prashasan, Rajneeti, Arthvyavastha aur Sarkari Seva",
     "Uttarakhand rajya ka prashasan, vidhan sabha, rajneeti, arthvyavastha, shiksha, swasthya aur sarkari sevaon ki saaf jaankari ek jagah.",
     "Prashasan aur arthvyavastha"),
    ("uttarakhand-gk-ukpsc", "hubtopic", None, [14, 24],
     "Uttarakhand GK: UKPSC/UKSSSC ke 200+ Sawal",
     "Uttarakhand GK: UKPSC/UKSSSC Taiyari aur 200 Sawal-Jawab",
     "Uttarakhand GK ki taiyari: UKPSC aur UKSSSC ke liye zaroori tathya aur Uttarakhand se jude 200 sawal-jawab, chhote aur seedhe uttar ke saath.",
     "Uttarakhand GK aur UKPSC"),
    ("uttarakhand-shahar-paryatan-sthal", "hubtopic", None, [15],
     "Uttarakhand ke Shahar, Ghati aur Paryatan Sthal",
     "Uttarakhand ke Shahar, Qasbe, Ghatiyan aur Paryatan Sthal: Zila-Wise",
     "Uttarakhand ke shahar, qasbe, ghatiyan aur paryatan sthal zila-wise: kaun si jagah kis zile mein hai aur wahan kya khaas hai, ek hi directory mein.",
     "Shahar aur paryatan sthal"),
    ("uttarakhand-pahadi-shabdkosh", "hubtopic", None, [22, 28],
     "Pahadi Shabdkosh: Kumaoni-Garhwali 120+ Shabd",
     "Pahadi Shabdkosh: 120+ Lupt Hote Kumaoni aur Garhwali Shabd",
     "Uttarakhand ke 120 se zyada purane pahadi shabd unke arth ke saath, aur Kumaoni-Garhwali mein ek hi arth ke alag shabdon ki tulna table.",
     "Pahadi shabdkosh"),
    ("uttarakhand-hindi-jankari", "hubtopic", None, [23],
     "उत्तराखंड की पूरी जानकारी हिंदी में",
     "उत्तराखंड: पूरी जानकारी हिंदी में",
     "उत्तराखंड की पूरी जानकारी हिंदी में: राज्य की पहचान, जिले, चार धाम, भूगोल, इतिहास, संस्कृति और ज़रूरी सवालों के सीधे जवाब, एक ही पेज पर आसान भाषा में।",
     "Hindi mein jaankari"),
]

def norm_p(html_inner):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html_inner)).strip().lower()

def text_of(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


# v3.3.2 (owner 14 Nov: 'FAQ zyada aur sahi page par'): zile ki badi FAQ-bank (50-sawal, voice-search, PAA) ke sawal
# us vishay wale page par le jao jahan sawal ka jawab sabse zyada kaam ka hai (copy nahi - MOVE; kuch nahi khota).
THEME_KW = {
 "tourism": r"ghum|ghoom|trek|best time|kab jayein|kab jaayein|dekhne|hill station|darshan|paryatan|jheel|\btal\b|camping|rafting|paragliding|ski|sunrise|itinerary|kitne din",
 "transport": r"kaise pahunch|railway|station|airport|\bbus\b|taxi|helicopter|heli|sadak|road|doori|kitni door|\bkm\b|rukne|hotel|homestay|network|petrol|parking",
 "food": r"khana|khaane|dish|mithai|recipe|roti|\bdal\b|daal|saag|kafal|bhatt|chutney|swad|bhojan|thali",
 "history": r"itihas|history|mandir|temple|raja|katyuri|\bchand\b|gorkha|british|andolan|katha|\bdham\b|sthapna|kisne banaya",
 "culture": r"tyohar|mela|festival|nritya|dance|\bgeet\b|shaadi|vivah|pehnawa|gehna|aipan|holi|sanskriti",
 "identity": r"tehsil|\bblock\b|zila kab|zile kab|kab bana|mukhyalaya|headquarter|\bdm\b|collector|vidhan sabha|lok sabha|pin code|\bstd\b|aabadi|population|sex ratio|saaksharta|literacy|kshetrafal|\barea\b|nagar nikay",
 "career": r"ukpsc|uksssc|\bexam\b|\bgk\b|career|naukri|\bjob|coaching|college|university|school|bharti|army|agniveer|pariksha",
 "land": r"zameen|nali|mutthi|bigha|khasra|khatauni|bhulekh|registry|stamp|circle rate|land law|bhu kanoon|bhoo kanoon|\bkheti\b|fasal|krishi",
 "climate": r"mausam|weather|barf|snow|barish|tapman|temperature|jungle|forest|wildlife|tiger|leopard|guldar|panchhi|pakshi|bird|sanctuary|national park",
 "geo": r"\bnadi|river|glacier|parvat|\bpeak|choti|unchai|altitude|ghati|valley|bhukamp|earthquake|seismic|latitude|seema|sangam|prayag",
 "sarkari": r"portal|certificate|praman patra|ration|aadhaar|online|apply|aavedan|helpline|csc|e-district|passport|licence|license|\brto\b|shikayat",
 "aadhunik": r"workation|retire|basna|kiraya|rent|internet|work from home|ghar banana|property|\bpet\b|kutte",
 "buzurg": r"purane zamane|buzurg|gharat|naula|chulha|kothar|bartan|purani parampara",
 "shabd": r"shabd|boli|kumaoni|garhwali|jaunsari|kahawat|paheli|matlab|meaning|kehte hain|bhasha",
 "economy": r"economy|arthvyavastha|\bgdp\b|per capita|udyog|industry|odop|shilp|hastshilp|bazaar|hydro|bijli|mining|khanan",
 "vaidya": r"vaidya|jadi|booti|nuskha|ilaj|ilaaj|aastha|jagar|aspatal|hospital|dawai",
 "hyperlocal": r"\bgaon\b|patti|village|\bhaat\b|dukaan|halwai|pargana",
 "bhavishya": r"pariyojana|project|ropeway|aapda|disaster|landslide|bhuskhalan|cloudburst|badal phat|baadh",
 "prasiddh": r"yojana|scheme|\bkhel\b|sports|khiladi|player|prasiddh log|famous people|janm|born|puraskar",
}
THEME_KW = {k: re.compile(v, re.I) for k, v in THEME_KW.items()}
BANK_HEAD = re.compile(r"\bfaqs?\b|\bsawaa?l\b|faq bank|\d+[- ]question|sawal-jawab|sawaal-jawab|voice|mic par|people also ask|log ye bhi|log yeh bhi|"
                       r"aksar poochhe|master faq|search pack|सवाल|query bank|aur aksar", re.I)

HUB_KW = {
 "uttarakhand": r"kitne zile|kitne mandal|rajdhani|kab bana|kab alag|devbhoomi|sthapna diwas|rajya (pashu|pakshi|phool|pushp|vriksh|ped|geet|khel)|kul kshetrafal|kul aabadi|rajyabhasha|doosri rajbhasha",
 "uttarakhand-char-dham-panch-kedar": r"\bdham\b|kedar|badri|gangotri|yamunotri|kapat|panch kedar|prayag|hemkund|mandir|temple|jyotirling",
 "uttarakhand-bhugol-nadiyan-glacier": r"\bnadi|river|glacier|parvat|\bpeak|choti|ghati|valley|jheel|\btal\b|unchai|bhukamp|kshetrafal|seema|latitude|bugyal",
 "uttarakhand-zameen-kanoon-nali-mutthi": r"zameen|nali|mutthi|bhu kanoon|bhoo kanoon|land|khatauni|khasra|registry|stamp|ucc",
 "uttarakhand-pahadi-virasat-tyohar": r"tyohar|mela|nritya|dance|\bgeet\b|khana|mithai|harela|phooldei|ghughutiya|aipan|pehnawa|lok",
 "uttarakhand-itihas-prasiddh-hastiyan": r"itihas|raja|andolan|katyuri|\bchand\b|gorkha|british|janm|prasiddh vyakti|swatantrata|rajya kab|alag rajya|9 november|chipko",
 "uttarakhand-yatra-planner": r"yatra|trek|ghum|ghoom|best time|itinerary|kaise pahunch|railway|airport|helicopter|permit|ilp",
 "uttarakhand-prashasan-arthvyavastha": r"\bzile\b|\bzila\b|mandal|tehsil|vidhan sabha|lok sabha|rajya sabha|rajdhani|gairsain|high court|economy|gdp|yojana|mukhyamantri|rajyapal|governor",
 "uttarakhand-shahar-paryatan-sthal": r"hill station|nainital|mussoorie|rishikesh|haridwar|auli|kausani|munsiyari|chopta|lansdowne|corbett",
 "uttarakhand-pahadi-shabdkosh": r"shabd|boli|kumaoni|garhwali|jaunsari|matlab|kahawat|bhasha",
}
HUB_KW = {k: re.compile(v, re.I) for k, v in HUB_KW.items()}

def _pick(q, hint, kw, avail):
    sc = sorted(((len(rx.findall(q)), k) for k, rx in kw.items() if k in avail), reverse=True)
    if sc and sc[0][0] >= 1 and (len(sc) < 2 or sc[0][0] > sc[1][0]):
        return sc[0][1]
    if hint and hint in avail:
        if not sc or sc[0][0] == 0 or any(k == hint and n == sc[0][0] for n, k in sc):
            return hint
    return None

def redistribute_faqs(pages, log=None):
    groups = collections.defaultdict(dict)
    for p in pages:
        if p["district"]:
            groups[p["district"]][p["theme"]] = p
        elif p["slug"] != "uttarakhand-hindi-jankari":
            groups["__hub__"][p["slug"]] = p
    moved = 0
    for d, tp in groups.items():
        kw = HUB_KW if d == "__hub__" else THEME_KW
        nfaq = {k: sum(1 for it in p["items"] if it[0] == "faq") for k, p in tp.items()}
        for src_key, p in list(tp.items()):
            keep, head_bank, hint = [], False, None
            for it in p["items"]:
                if it[0] in ("h2", "h3", "h4"):
                    head_bank = bool(BANK_HEAD.search(it[1]))
                    hint = _pick(it[1], None, kw, tp) if head_bank else None
                if it[0] == "faq" and head_bank and not is_deva(it[1]):
                    tgt = _pick(it[1], hint, kw, tp)
                    if tgt and tgt != src_key and nfaq.get(tgt, 0) < 15:
                        tp[tgt].setdefault("_moved", []).append(it)
                        nfaq[tgt] = nfaq.get(tgt, 0) + 1; nfaq[src_key] -= 1; moved += 1
                        if log is not None:
                            log.append({"page": p["slug"], "action": "faq_move", "to": tp[tgt]["slug"], "q": it[1]})
                        continue
                keep.append(it)
            p["items"] = keep
        for k, p in tp.items():
            mv = p.pop("_moved", [])
            if mv:
                idx = next((i for i, it in enumerate(p["items"]) if it[0] == "h2" and re.search(r"srot|sandarbh|source", it[1], re.I)), len(p["items"]))
                lab = p["label"].split(":")[-1].strip() if p["district"] else p["h1"].split(":")[0]
                p["items"][idx:idx] = [("h2", "%s: Aksar Poochhe Jaane Wale Sawal" % lab, "faq-moved")] + mv
    return moved

def add_extra_faqs(pages):
    from faq_extra import FAQ_EXTRA
    for p in pages:
        extra = FAQ_EXTRA.get(p["slug"])
        if not extra:
            continue
        have = [it[1].lower() for it in p["items"] if it[0] == "faq"]
        new = [("faq", q, a) for q, a in extra
               if not any(difflib.SequenceMatcher(None, q.lower(), h).ratio() >= 0.8 for h in have)]
        if not new:
            continue
        idx = next((i for i, it in enumerate(p["items"]) if len(it) > 2 and it[2] == "faq-moved"), None)
        if idx is not None:
            j = idx + 1
            while j < len(p["items"]) and p["items"][j][0] == "faq":
                j += 1
            p["items"][j:j] = new
        else:
            at = next((i for i, it in enumerate(p["items"]) if it[0] == "h2" and re.search(r"srot|sandarbh|source", it[1], re.I)), len(p["items"]))
            lab = p["label"].split(":")[-1].strip() if p["district"] else "Uttarakhand"
            p["items"][at:at] = [("h2", "%s: Aksar Poochhe Jaane Wale Sawal" % lab, "faq-moved")] + new

# ------------------------------------------------------------------ pages banana
def build_pages():
    B = load_blocks(os.environ.get("UK_BLOCKS", "/home/claude/blocks.json"))
    pages, internal = [], collections.defaultdict(list)
    modmap = {}            # district -> {module number: theme}
    for fn, ds, D, mandal, boli in DISTRICTS:
        groups = collections.OrderedDict()
        modmap[ds] = {}
        for th, m in assign_themes(split_modules(B[fn])):
            mm = re.match(r"^MODULE\s+(\d+)", m["title"], re.I)
            if mm and th not in ("internal", "main", "intro", "sources") and "(" not in m["title"][:12]:
                modmap[ds].setdefault(int(mm.group(1)), th)
            if th == "internal":
                internal[ds].append({"module": m["title"], "why": "editor/SEO/publish ke liye likha gaya (page par nahi)",
                                     "blocks": m["blocks"]})
                continue
            key = "main" if th in ("intro", "main", "sources") else th
            groups.setdefault(key, []).append((th, m))
        for key, mods in groups.items():
            suf, tops, h1, desc, label, tools = THEMES[key]
            slug = ds + "-" + suf
            b = Builder(dname=D)
            first = True
            for th, m in mods:
                t = m["title"]
                if key == "main":
                    if th == "intro":
                        feed(b, m["blocks"], intro=True)
                    elif th == "sources":
                        b.heading(2, "Srot aur Sandarbh"); feed(b, m["blocks"])
                    elif re.search(r"book end", t, re.I):
                        b.heading(2, "Saransh: %s ek nazar mein" % D); feed(b, m["blocks"])
                    elif re.search(r"extra module|lambi poonch", t, re.I):
                        b.heading(2, "%s: aur aksar poochhe jaane wale sawal" % D); feed(b, m["blocks"])
                    elif re.search(r"addendum", t, re.I):
                        b.heading(2, "%s: master FAQ aur srot" % D)
                        b.level_map = {"Heading 2": 3, "Heading 3": 4, "Heading 4": 4}
                        feed(b, m["blocks"]); b.level_map = {"Heading 2": 2, "Heading 3": 3, "Heading 4": 4}
                    else:
                        feed(b, m["blocks"])
                    continue
                if first:
                    feed(b, m["blocks"]); first = False; continue
                tl = t.lower()
                if "people also ask" in tl:
                    disp = "Log ye bhi poochhte hain"
                elif "vistaar" in tl:
                    disp = "Vistaar se: " + clean_heading(re.sub(r"^MODULE\s+\d+\s*\(VISTAAR\)\s*:?", "", t, flags=re.I), D)
                elif "part 3" in tl:
                    disp = "Taiyar reference table: naap-tol aur theth shabd"
                else:
                    disp = clean_heading(re.sub(r"^BONUS\s*:\s*", "", t, flags=re.I), D)
                b.heading(2, t if "people also ask" in tl else disp)
                if b.items and b.items[-1][0] == "h2":
                    b.items[-1] = ("h2", disp, t)
                b.level_map = {"Heading 2": 3, "Heading 3": 4, "Heading 4": 4}
                feed(b, m["blocks"])
                b.level_map = {"Heading 2": 2, "Heading 3": 3, "Heading 4": 4}
            items = b.done()
            internal[ds] += [{"page": slug, "item": x} for x in b.internal]
            title = next((x.format(D=D, B=boli) for x in tops if len(x.format(D=D, B=boli)) <= 47), D)
            pages.append(dict(slug=slug, kind="main" if key == "main" else "theme", district=ds, D=D, mandal=mandal,
                              boli=boli, theme=key, title=title, h1=h1.format(D=D, B=boli), desc=desc.format(D=D, B=boli),
                              label=label.format(D=D), tools=tools, items=items, lang="hi-Latn"))
    # ---- hub
    hb = B[HUB_FILE]
    secs = collections.OrderedDict()
    cur = "intro"
    for x in hb:
        if x["k"] == "p" and x["s"] == "Heading 1" and "implementation pack" in x["t"].lower():
            cur = "internal"; secs.setdefault(cur, []); continue
        if x["k"] == "p" and x["s"] == "Heading 2" and cur != "internal":
            m = re.match(r"^Module\s+(\d+)\s*:", x["t"])
            if m:
                cur = int(m.group(1))
            elif "explore" in x["t"].lower():
                cur = "explore"
            elif "quick facts" in x["t"].lower():
                cur = "quick"
            elif "kya milega" in x["t"].lower():
                cur = "toc"
        secs.setdefault(cur, []).append(x)
    internal["uttarakhand"].append({"module": "Hub IMPLEMENTATION PACK + Appendix A-F", "why": "sirf editor ke liye",
                                    "blocks": secs.pop("internal", [])})
    internal["uttarakhand"].append({"module": "Hub TOC", "why": "page ka apna TOC ban jaata hai", "blocks": secs.pop("toc", [])})
    # v3.3 (14 Nov): hub ki zila-table ke kshetrafal ko zile ke apne page (Census 2011) se milaya - galat ank site par na jaaye
    AREA_FIX = {"Almora": "3,144 sq km", "Bageshwar": "2,241 sq km", "Chamoli": "8,030 sq km", "Pauri Garhwal": "5,329 sq km",
                "Udham Singh Nagar": "2,542 sq km"}
    for blk in secs.get(3, []):
        if blk["k"] == "t" and blk["rows"] and blk["rows"][0][:2] == ["Zila", "Mukhyalay"]:
            for r in blk["rows"][1:]:
                if r[0] in AREA_FIX and r[3] != AREA_FIX[r[0]]:
                    internal["uttarakhand"].append({"page": "uttarakhand", "item": ("area-fix", "%s: %s -> %s" % (r[0], r[3], AREA_FIX[r[0]]))})
                    r[3] = AREA_FIX[r[0]]
            blk["rows"] = [r[:6] for r in blk["rows"]]          # aakhri 'Poora guide' (purana URL) column: neeche asli link-suchi hai
    for slug, kind, _, parts, title, h1, desc, label in HUB_PAGES:
        b = Builder(dname="Uttarakhand", level_map={"Heading 1": 2, "Heading 2": 2, "Heading 3": 3, "Heading 4": 4})
        order = parts if kind == "hubtopic" else ["intro", "quick", 1, 2, 3, 16, 26, 27, 29, 30, "explore", 25]
        for p in order:
            blk = secs.get(p, [])
            if p == "intro":
                blk = [y for y in blk if not (y["k"] == "p" and y["s"] == "Heading 1")]
            feed(b, blk, intro=(p == "intro"))
        items = b.done()
        internal["uttarakhand"] += [{"page": slug, "item": x} for x in b.internal]
        pages.append(dict(slug=slug, kind=kind, district=None, D="Uttarakhand", mandal=None, boli=None, theme=slug,
                          title=title, h1=h1, desc=desc, label=label, tools=["nali-mutthi-converter"] if "zameen" in slug else [],
                          items=items, lang="hi" if slug.endswith("hindi-jankari") else "hi-Latn"))
    redistribute_faqs(pages)
    add_extra_faqs(pages)
    from descs import unique_desc                  # v3.3.2 audit-3: 247 page ka ek-saancha description -> har page ka apna
    unique_desc(pages)
    # v3.3.2: GK page par ek bhi table nahi tha (audit warning) - hub ke apne tathyon se ek nazar wali GK table
    for p in pages:
        if p["slug"] == "uttarakhand-gk-ukpsc":
            at = next((i for i, it in enumerate(p["items"]) if it[0] == "h2"), 0)
            p["items"][at:at] = [("h2", "Uttarakhand GK: Ek Nazar Mein (Pariksha ke Liye Table)", "gk-table"), ("table", [
                ["Prashn", "Uttar"],
                ["Rajya kab bana", "9 November 2000 (Bharat ka 27va rajya)"],
                ["Naam Uttaranchal se Uttarakhand kab hua", "1 January 2007"],
                ["Rajdhani", "Dehradun (antarim); Gairsain (Bhararisain, Chamoli) grishmakalin"],
                ["High Court", "Nainital"],
                ["Mandal aur zile", "2 mandal (Garhwal, Kumaon), 13 zile"],
                ["Rajya pashu / pakshi", "Kasturi mrig / Himalayan Monal"],
                ["Rajya phool / vriksh", "Brahma Kamal / Buransh"],
                ["Kshetrafal mein sabse bada zila", "Uttarkashi"],
                ["Kshetrafal mein sabse chhota zila", "Champawat"],
                ["Puranon mein naam", "Garhwal: Kedarkhand; Kumaon: Manaskhand"],
            ])]
    return pages, internal, modmap

if __name__ == "__main__":
    pages, internal, modmap = build_pages()
    c = collections.Counter(p["kind"] for p in pages)
    print(len(pages), dict(c))
    for p in pages[:3] + pages[-12:]:
        w = sum(len(" ".join(str(z) for z in it[1:]).split()) for it in p["items"])
        print(p["slug"], len(p["items"]), w, collections.Counter(i[0] for i in p["items"]).most_common(8))
