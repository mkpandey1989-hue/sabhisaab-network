"""Text safai + public/internal faisla. Har hataya/khiska hissa 'internal' log mein jaata hai (delete nahi)."""
import re, html as H

INTERNAL_HARD = re.compile(
    # v3.3.2 (owner 14 Nov, Gemini audit): 'kyu nahi / blueprint / publish / editor' akele shabd se poora hissa nahi hatta -
    # unke liye HEADING_FIX (neeche) har heading ka faisla alag se karta hai. Yahan sirf pakke editor/SEO hisse.
    r"sirf editor|editor ke liye|editor.s verify|publish na kar|publish se pehle|publish karne se pehle|publish ke din|pre-publish|"
    r"owner note|owner ki|community contribution|community box|contribution form|form ke fields|dropdown suchi|samiksha ki prakriya|"
    r"aapki madad chahiye|namoona sandesh|apni kahani|aapki kahani|apna gaon, apni baat|apne gaon ki kahani|aap apni kahani|"
    r"internal linking|internal links? ke liye|circular internal|andar ke link|spoke-page|spoke page|\bspoke\b|\bserp\b|json-ld|schema \(|master schemas?\b|"
    r"schema plan|seo checklist|indexing checklist|sampadak|front matter|page setup|implementation|technical seo|on-page|"
    r"meta title|seo pack|pinterest pack|likhne ke niyam|keyword bank|low-competition|sirf aapke liye", re.I)
INTERNAL_SOFT = re.compile(
    r"keyword|kaise padhein|how to use|module index|table of contents|vishay[- ]?suchi|jump links|image alt|alt text|"
    r"indexing|search console|verify list|sudhar-log|bharne ki|is file|owner note", re.I)
FAQ_LIKE = re.compile(r"faq|people also ask|\bpaa\b|sawal|sawaal|सवाल|q&a|questions", re.I)

# v3.3.2 (owner 14 Nov: 'bina padhe data hata diya'): har sandehjanak heading ka alag faisla, padh kar.
#   None = poora hissa editor ka (page par nahi) | "" = heading chhupao, content pichhle hisse mein rahe
#   "NAV" = zilon ki aapsi suchi: sirf 'rishta' wali table page par (link ke saath), baaki niyam/URL editor ka
#   text = nayi pathak-wali heading ({D} = zile ka naam)
HEADING_FIX = [
    (r"faq me jodne ke liye", "Aur Chhote Sawal-Jawab"),
    (r"quiz kaise khelein", "{D} GK Quiz: Apni Jaankari Parkhein"),
    (r"^148\.1 kya likhein aur kya nahi", "Ye Jagahein Kis Zile Mein Hain: Aam Bhram"),
    (r"zimmedar tarike se kaise likhein", "Andhvishwas aur Bhedbhav: Zimmedar Soch"),
    (r"naam kyun nahi diye", "Sthaniya Khana aur Dukaan Kaise Dhoondhein"),
    (r"structural valley", "“Dun” Ghati Kya Hai aur {D} Mein Kyon Nahi"),
    (r"sudhaar aur yogdan|sidha jura zila link|is file me jo sudhaar", None),
    # sirf heading lekhak-wali ('maine kyu nahi likha'); neeche pathak ke kaam ki baatein ho sakti hain -> heading chhupao, vaakya-filter chalne do
    (r"50 muhavare.*kyu nahi|maine kahawat|maine paheli|kyu maine|geet ke bol kyu nahi|kahaniyan kyu nahi|hum dukaan ke naam kyun nahi|"
     r"hamari imandari ki baat$|kahawat ka sahi format|is heading par abhi", ""),
    (r"sahi aur galat dava", "Ye Jagahein aur Paramparayein {D} ki Nahi"),
    # v3.3.2 audit-3 (har chhode gaye hisse ko padha): heading lekhak-wali, par andar pathak ke kaam ki baatein/sawal-jawab.
    # Heading badlo; andar ke lekhak-niyam vaakya-filter (split_editor) hata deta hai, khali table 'salvage' se.
    (r"^181\.? .*rehne ka kharcha: mahine ka budget", "{D} Mein Rehne ka Kharcha"),
    (r"^181\.1 mahine ka budget kaise banayein", "Mahine ka Budget: Kiraya, Rasoi, LPG, Internet aur Yatra"),
    (r"^181\.2 budget kaise banayein", "Ghar ka Mahine ka Budget: Aasan Tareeka"),
    (r"shg kaise banayein aur judein", "SHG (Swayam Sahayata Samuh) Kaise Banayein aur Judein"),
    (r"bazaar: kab khule/band", "{D} ke Bazaar: Kab Khule, Kab Band"),
    (r"sabse purani dukan.*ke daave", "“Sabse Purani Dukan” ke Daave aur Sthaniya Khana"),
    (r"poori patti list kaise banayein", "Poori Patti List Kahan Milegi"),
    (r"data-sangrah table: block-wise gram panchayat", "Gram Panchayat ki Poori Suchi Kahan Milegi"),
    (r"garh/kot ki list kaise banayein", "Garh aur Kot ki Jaankari Kahan Milegi"),
    (r"^150\.2 data-sangrah table", "Bugyal, Van Panchayat aur Zimmedar Yatra"),
    (r"^151\.1 kya khoj kar likhna hai", "{D} ka Khana: Kya Khayein, Kahan Milega"),
    (r"bazaar ke band hone ka din: data-sangrah", "Bazaar Band Hone ka Din, Mandi aur Mele"),
    (r"^153\.2 data-sangrah table", "Bus-Taxi Yatra: Kaam ki Baatein aur Helpline"),
    (r"^171\.2 data-sangrah table", "{D} ke ‘Pehle’ aur Gaurav: Sawal-Jawab"),
    (r"mahilaon ki safety par page kaise likhein", "Mahilaon ki Yatra Suraksha"),
    (r"apni pyq suchi kaise banayein", "Students ke liye: Apni PYQ Suchi Kaise Banayein"),
    (r"is heading par|page structure|tasveerein page par|(?<!baatein )kaise likhein|kaise jama karein|surakshit lekhan|page par kaise|"
     r"naksha banane ka sujhav|template \(aap bharein\)|quiz ko page par|saral code|last verified ka niyam|aap bhejein|"
     r"jump-link index|kaise banayein|data-sangrah|aapko bharna|kya khoj kar likhna", None),
    (r"purane exam ke sawal \(pyq\): hamari imandari", "Purane Exam ke Sawal (PYQ) aur Abhyas ka Tareeka"),
    (r"^143\.5 blueprint ki galti", "Aam Galatfehmi: Ye Pattiyan {D} ki Nahi"),
    (r"block-wise poori suchi kyu nahi", "Block-wise Gaon aur Gram Panchayat ki Poori Suchi Kahan Milegi"),
    (r"bus adda aur taxi union ke naam kyu nahi", "Bus aur Taxi: Yatra se Pehle Zaroori Baatein"),
    (r"ye aankde kyu nahi likhe", "Rehne ka Kharch Kin Baaton Par Nirbhar Karta Hai"),
    (r"dar kyu nahi likhi", "Ghar Banane ki Laagat Kin Baaton Par Nirbhar Hai"),
    (r"blueprint se sudhaar", "Doosre Zile ki Ghatnayein: Sahi Jaankari"),
    (r"parivar ke rishte \(samanya garhwal-kumaon", "Parivar ke Rishte: Garhwali-Kumaoni Shabd"),
    (r"blueprint me diye gaye maap", "Lok-smriti ke Paramparik Maap (Mutthi, Pao, Mana)"),
    (r"blueprint ki suchi me doosre zilon", "Ye Pattiyan {D} ki Nahi: Doosre Zilon ke Naam"),
    (r"^198\. official links aur sandarbh", "Official Links aur Sandarbh Suchi"),
    (r"^198\.1 sarkari portal", "Sarkari Portal"),
    (r"^198\.2 sab hisaab ke tools", None),
    (r"nuskhe.*kyon nahi likh", "Gharelu Nuskhon Par Saavdhani: Kyon Zaroori Hai"),
    (r"hum daam kyon nahi", "Rehne ka Kharch: Sahi Andaza Kaise Lagayein"),
    (r"per sq ft rate kyon nahi", "Pahad Mein Ghar Banana Mehnga Kyon Padta Hai"),
    (r"patti-list yahan kyon nahi", "Pahadi Patti-Vyavastha Terai Mein Kyon Nahi"),
    (r"hum code kyun nahi likh", "Bank aur IFSC Code: Surakshit Tareeka"),
    (r"golu devta wala hissa", "Golu Devta ki Paramparayein: Kumaon ki ya Tehri ki?"),
    (r"^200\.? |navigation matrix|inter-district navigation|13 zilon (ka|ki) navigation|13 jilon ka navigation|"
     r"zilon ka aapsi jod|baaki 12 (zilon|jilon)|13 zilon ka (master matrix|safar)|doosre zilon ki taraf|zilon me aage badhein", "NAV"),
]
HEADING_FIX = [(re.compile(a, re.I), b) for a, b in HEADING_FIX]

def heading_fix(t):
    """-> (matched, action)"""
    for rx, act in HEADING_FIX:
        if rx.search(t):
            return True, act
    return False, None

def heading_internal(t):
    if INTERNAL_HARD.search(t):
        return True
    if INTERNAL_SOFT.search(t) and not FAQ_LIKE.search(t):
        return True
    return False

PARA_INTERNAL = re.compile(
    r"^(#+\s*module\b|search phrases?\s*:|primary keyword|secondary keywords?|search jo|search keywords?|seo keywords?|seo fayda|seo ke liye|moderation ke tips|niyam jo page par|page par form|search query|keyword|keywords|lsi\b|focus keyword|secondary keyword|target keyword|meta title|"
    r"meta description|title tag|url slug|url \(|h1 \(|og:|open graph|image alt|alt text|schema|internal link|"
    r"anchor text|sabhisaab\.com\s*[|/]|\[?module \d+ (samaapt|samapt|khatam)|module \d+ \(headings? \d|module \d+[^.]{0,160}\bpoora hua|agla module|agla:|\[agla|"
    r"yeh sawal google ke|inhe page ke faq schema|is document|yeh document|ye document|pinterest pin|pin title|"
    r"canonical|breadcrumb:|indexnow|gsc |google search console)", re.I)
PARA_INTERNAL_ANY = re.compile(r"publish na karein|sirf editor|sirf aapke liye|publish se pehle hata|page par publish nahi|"
                               r"publish karte samay hata|editor ke liye|faqpage_all\.json|schema me bhi jodenge", re.I)
TOC_LINE = re.compile(r"^(module\s+\d+[^.]{0,120}|\d{1,3}\.\s.{0,90})$", re.I)

PLACEHOLDER_CELL = re.compile(r"^(|—|-|–|\?|\.{2,}|_+|jama karna hai|bharna hai|khaali|khali|verify|tbd|n/?a|"
                              r"\(bharein\)|bharein|owner bharega|\[.*bhar.*\])$", re.I)
TABLE_INTERNAL_HEAD = re.compile(r"keyword|spoke page|meta|schema|title tag|pin title|taiyar copy|anchor|site structure|page ka url|asli url|\burl\b|link \(aap", re.I)

TYPOS = {"ki liye": "ke liye", "ka liye": "ke liye", "se pahle": "se pehle", "chahiaye": "chahiye",
         "chaiye": "chahiye", "aapko ko": "aapko", "kholha": "khola", "hotaa": "hota", "kartaa": "karta",
         "jaataa": "jaata", "miltea": "milte",
         # v3.3.2 (owner 14 Nov: 'spelling mistake'): poore 264 page ke shabd-ginti se mili galtiyan (kam baar aaye, mashhoor shabd se 1 akshar door)
         "vebsite": "website", "vpkas": "vikas", "suraksit": "surakshit", "sarakshit": "surakshit", "bannne": "banane",
         "bananey": "banane", "nrityaa": "nritya", "bhaarosemand": "bharosemand", "ooonchi": "oonchi", "pooori": "poori",
         "prtha": "pratha", "prtibandhit": "pratibandhit", "prathibandhit": "pratibandhit", "prbhavit": "prabhavit",
         "mashoor": "mashhoor", "lokation": "location", "sapply": "supply", "ingineer": "engineer", "uttpad": "utpad",
         "udpad": "utpad", "mashroom": "mushroom", "pasport": "passport", "stroat": "strot", "ilaaake": "ilaake",
         "cheerein": "cheezein", "sistem": "system", "vidheshi": "videshi", "paryavarn": "paryavaran", "prayavaran": "paryavaran",
         "dristi": "drishti", "uddgam": "udgam", "nawjat": "navjat", "sankritik": "sanskritik", "pucchhyari": "puchhyari",
         "haldka": "halka", "pairmane": "paimane", "pashikshan": "prashikshan", "kamjor": "kamzor", "judey": "jude",
         "sheru": "shuru", "bhaut": "bahut", "sekta": "sakta", "sekti": "sakti", "janakari": "jaankari", "sharkari": "sarkari",
         "chamoawat": "Champawat", "bagheshwar": "Bageshwar", "champwat": "Champawat", "kumaor": "Kumaon", "kemaon": "Kumaon",
         "pramparik": "paramparik", "paarmparik": "paramparik", "paaramparik": "paramparik", "mitli": "milti",
         "mussourie": "Mussoorie", "turism": "tourism", "turist": "tourist", "kedarnaath": "Kedarnath", "badrinaath": "Badrinath",
         "karnprayag": "Karnaprayag", "lokal": "local", "patthal": "patthar", "sthaaniya": "sthaniya", "salaah": "salah",
         "unchaai": "unchai", "oonchaai": "oonchai", "gurudware": "gurudwara", "aakele": "akele", "madhumakhi": "madhumakkhi",
         "sawdhan": "savdhan", "sangrakshan": "sanrakshan", "garwal": "Garhwal", "gadhwal": "Garhwal", "almor": "Almora",
         "jaroori": "zaroori", "ucchai": "unchai", "manasarovar": "Mansarovar", "madmaheshwar": "Madhmaheshwar",
         "bhilangna": "Bhilangana", "nanakmata": "Nanakmatta", "darchula": "Dharchula", "hemkunt": "Hemkund", "deovan": "Deoban",
         "sarkanda": "Surkanda", "kharsoli": "Kharsali", "kharshali": "Kharsali", "ahipan": "Aipan", "chauchari": "Chanchari",
         "ukssc": "UKSSSC", "escholarship": "e-scholarship", "digitale": "digital", "vidhesh": "videsh", "panjabi": "Punjabi",
         "aasapaas": "aaspaas", "laakh": "lakh", "bachhon": "bachchon", "dastavej": "dastavez", "kaaryalay": "karyalay",
         "maarg": "marg", "dhaam": "dham", "praachin": "prachin", "vartamaan": "vartaman", "adhaarit": "adharit",
         "vyavhaarik": "vyavharik", "saamudayik": "samudayik", "prastaavit": "prastavit", "raajasv": "rajasv", "sthaanon": "sthanon"}

_TAGW = re.compile(r"\b(verify|pushti)\b(\s+(baaki|karein|karna|zaroori))?", re.I)
_INSTR = re.compile(r"\bse\s+(verify|pushti)", re.I)


def _paren_tag(m):
    """( ... verify ... ) - sirf tag ho to hatao; vaakya ho ('... yatra se pehle zaroor verify karein') to 'pushti karein' banao."""
    inner = m.group(1)
    if not re.search(r"\b(verify|pushti)\b", inner, re.I):
        return m.group(0)
    rest = _TAGW.sub("", inner)
    rest = re.sub(r"^[\s;,:\-]+|[\s;,:\-.]+$", "", rest)
    if len(rest.split()) >= 4:
        # v3.3.2: poora vaakya hai -> salah bani rahe ('verify' akela/verb -> 'pushti karein')
        t = re.sub(r"\bverify\s+(karein|kar lein|karna|karna zaroori hai|kar len)\b", r"pushti \1", inner, flags=re.I)
        t = re.sub(r"\bverify\s+baaki\b", "pushti karein", t, flags=re.I)
        t = re.sub(r"\b(zaroor|pehle|se)\s+verify\b(?!\s+\w)", r"\1 pushti karein", t, flags=re.I)
        t = re.sub(r"\bverify\b", "pushti karein", t, flags=re.I)
        t = re.sub(r"pushti karein\s+(karein|kar lein)", "pushti karein", t)
        t = re.sub(r"\bpushti\s+(baaki|zaroori)\b", "pushti karein", t, flags=re.I)
        return "(" + t.strip() + ")"
    rest = re.sub(r"\s*[;,]\s*[;,]\s*", "; ", rest)
    if not rest or rest.lower() in ("naam", "din", "sthiti", "taaza sthiti", "sanket"):
        return ""
    return "(" + rest + ")"


def _sq_tag(m):
    """[VERIFY ...] editor-nishan: 3+ shabd ki asli note bache to (note), warna kuch nahi."""
    rest = re.sub(r"\b(verify|pushti|confirm)\b(\s+(baaki|karein|karna|zaroori|with|from|se))?", "", m.group(1), flags=re.I)
    rest = re.sub(r"^[\s;,:\-]+|[\s;,:\-]+$", "", rest)
    if len(rest.split()) >= 3 and not re.search(r"url|structure|source|official|portal|site|whether|with|check|exact|latest|current|taaza", rest, re.I):
        return " (" + rest + ")"
    return ""

def fix_text(t):
    t = t.replace("Master Schemas", "Master Reference").replace("MASTER SCHEMAS", "MASTER REFERENCE")
    t = t.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    # v3.3 (owner 14 Nov: 'tag hata dena'): editor ke verify-nishan hatao; asli salah ('official site se pushti karein') rahe
    t = re.sub(r"\s*✔\s*", " ", t)
    t = re.sub(r"\s*\[\s*VERIFY\s*\]\s*", " ", t, flags=re.I)
    t = re.sub(r"\s*\[\s*([^\]]{0,80}\b(?:verify|pushti|confirm)\b[^\]]{0,80})\]", _sq_tag, t, flags=re.I)
    t = re.sub(r"\(([^()]*)\)", _paren_tag, t)
    t = re.sub(r"\b(verify|pushti)\s+baaki\b\.?", "", t, flags=re.I)
    t = re.sub(r"\bverify karein\b", "pushti karein", t, flags=re.I)
    t = re.sub(r"\bverify kitaab se\b", "kitaab se milayein", t, flags=re.I)
    t = re.sub(r"\s*\bverify\.?\s*$", "", t, flags=re.I)              # vaakya ke ant mein akela tag
    t = re.sub(r"\(\s*([^()]*?)[\s,;:]+\)", r"(\1)", t)
    t = re.sub(r"\(\s*\)", "", t)
    t = re.sub(r"\s+([.,;:])", r"\1", t)
    for w, r in TYPOS.items():
        t = re.sub(r"\b%s\b" % re.escape(w), lambda m, r=r: (r[:1].upper() + r[1:]) if m.group(0)[:1].isupper() else r, t, flags=re.I)
    # ek hi shabd lagataar (alag alag -> alag-alag), audit ka niyam
    for _ in range(3):
        t = re.sub(r"\b([A-Za-z]{3,})(\s+)\1\b", r"\1-\1", t)
    # Devanagari aur Roman akshar chipke na hon
    t = re.sub(r"([A-Za-z])([\u0900-\u097F])", r"\1 \2", t)
    t = re.sub(r"([\u0900-\u097F])([A-Za-z])", r"\1 \2", t)
    t = re.sub(r"[ \t]{2,}", " ", t).strip()
    t = re.sub(r"([;,])\s*verify\s*\.?\s*\)", r"\1 pushti karein.)", t, flags=re.I)
    # v3.3.2: tag hatne ke baad bacha kachra (',.)', '..', '( ', ' ,')
    t = re.sub(r"[,;]\s*([.)])", r"\1", t)
    t = re.sub(r"(?<!\.)\.\.(?!\.)", ".", t)
    t = re.sub(r"\(\s+", "(", t); t = re.sub(r"\s+\)", ")", t)
    t = re.sub(r"\(\s*[,;.]\s*", "(", t)
    t = re.sub(r"\(\s*\)", "", t)
    t = re.sub(r"\s+([,;:.])", r"\1", t)
    # v3.3.2 audit-3: bacha hua 'verify' (Gemini: 'verify remark chhod diye') -> saaf Hindi; 'abhi pakka nahi' wali imandari rahe
    for a, b in VERIFY_RW:
        t = a.sub(b, t)
    return t

VERIFY_RW = [(re.compile(a, re.I), b) for a, b in [
    (r";?\s*(tithi|unki|iski|inki) ki pushti verify_list me rakhi gayi hai", r"; \1 par sroton mein matbhed ho sakta hai"),
    (r",?\s*par unki pushti pehle verify_list me rakhi gayi hai", ", par unki pushti abhi baaki hai"),
    (r"\bverify kiye bina\b", "jaanche bina"), (r"\bbina verify kiye\b", "bina jaanche"), (r"\bbina verify\b", "bina jaanche"),
    (r"\bverify (karna|karni) (zaroori|behtar) (hai|hoga)\b", r"jaanchna \2 \3"),
    (r"\bverify karna (hoga|chahiye)\b", r"jaanchna \1"), (r"\bverify karni hongi\b", "jaanchni hongi"),
    (r"\bverify karna kathin\b", "pakka karna kathin"), (r"\bverify karna\b", "jaanchna"),
    (r"\bverify karwayein\b", "jaanch karwayein"), (r"\bverify hona chahiye\b", "jaanchna chahiye"),
    (r"\bModule \d+ ke kai headings\b", "is vishay ki kai baatein"),
    (r"Har zile ke page ki Heading 121\.A aur 122\.A me", "Har zile ke page ke boli-shabd wale hisse mein"), (r"\bverify (na )?kar lein\b", r"\1jaanch lein"),
    (r"\bverify kar sakte hain\b", "jaanch sakte hain"), (r"\bverify ki jaani chahiye\b", "jaanchi jaani chahiye"),
    (r"\bverify (hone|honi) chahiyen?\b", "jaanche jaane chahiye"), (r"\bverify ho (gaye|gayi|gaya|chuke|chuki) (hain|hai)\b", r"pakke ho \1 \2"),
    (r"\bse verify\b(?=\s*[(.;,]|\s*$)", "se jaanchein"),
    (r"\b(data|naam|roop|praman|vidhi|sthiti)( aur (naam|roop|vidhi))? verify nahi\b", r"\1\2 ki pushti nahi"),
    (r"\bverify nahi\b", "pushti nahi"),
    (r"\bVerify kahan karein\b", "Pushti kahan karein"), (r"“Verify kahan karein”", "“Pushti kahan karein”"),
    (r"^⚠\s*Verify\s*:", "⚠ Dhyan dein:"),
    (r"\bhumne (verified roop me |abhi )?nahi paya\b", "nahi mila"), (r"\bhumne (kisi bharosemand suchi me )?nahi dekha\b", r"\1nahi mila"),
    (r"\bhumne abhi pakka nahi kiya\b", "abhi pakka nahi hai"),
    (r",?\s*\(hum pakka nahi kar paye\)", ""), (r"\s*\(khali template\)", ""),
    (r"\bPariksha ya publish ke liye\b", "Pariksha ke liye"),
    (r"\bpichhle modules me\b", "pichhle hisson mein"),
    (r"^Module \d+ ka maksad\s*:", "Is hisse ka maksad:"),
    (r"^Pehle yeh samajh lein: Module \d+ ke kai headings\b", "Pehle yeh samajh lein: is vishay ki kai baatein"),
    (r",?\s*aur (Module|Heading) 199 me uski kahani likhna", ""),
]]

def esc(t):
    return H.escape(t, quote=True)

def is_para_internal(t):
    tl = t.strip()
    return bool(PARA_INTERNAL.match(tl) or PARA_INTERNAL_ANY.search(tl))

def table_kind(rows):
    """public / internal(meta) / placeholder"""
    if not rows:
        return "placeholder"
    head = " ".join(rows[0])
    if TABLE_INTERNAL_HEAD.search(head):
        return "internal"
    body = [c for r in rows[1:] for c in r[1:]] or [c for r in rows for c in r]
    if not body:
        return "placeholder"
    empty = sum(1 for c in body if PLACEHOLDER_CELL.match(c.strip()))
    if empty / len(body) >= 0.5:
        return "placeholder"
    return "public"

DEVA = re.compile(r"[\u0900-\u097F]")
def is_deva(t):
    letters = re.findall(r"[A-Za-z\u0900-\u097F]", t)
    return bool(letters) and sum(1 for c in letters if DEVA.match(c)) / len(letters) > 0.5

def titlecase(s):
    if s.upper() != s:
        return s
    small = {"aur", "ka", "ki", "ke", "se", "me", "mein", "of", "and", "the", "&", "ya", "par"}
    out = []
    for i, w in enumerate(s.lower().split()):
        if i and w in small:
            out.append(w)
        elif w.upper() in ("UKPSC", "UKSSSC", "GK", "FAQ", "PAA", "SEO", "UCC", "RTO", "STD", "PIN", "SDM", "ILP", "GMVN",
                           "KMVN", "GI", "ODOP", "UK", "NH", "DM", "IAS", "IIT", "AIIMS", "NIM"):
            out.append(w.upper())
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)

def clean_heading(t, dname=None):
    # v3.3.2: document-dhanche wale shabd heading se hatao (Module 6 ke..., PAGE INTRO:, '(E-E-A-T ke liye)', '(... Page Par Likhein)')
    t = re.sub(r"^\s*PAGE INTRO\s*:\s*", "", t, flags=re.I)
    t = re.sub(r":?\s*\bModule \d+ Se Aage Ke\s+", ": ", t, flags=re.I)
    t = re.sub(r"\bKya Hamare Paas Hai\b", "Jo Pakka Pata Hai", t, flags=re.I)
    t = re.sub(r"^\s*(Bonus\s*:\s*)?Is Module ke\s+", "", t, flags=re.I)
    t = re.sub(r"^\s*Module\s+\d+\s+FAQ\s*:\s*", "", t, flags=re.I)
    t = re.sub(r"^\s*Module\s+\d+\s+(Ke|Ka|Ki)\s+", "", t, flags=re.I)
    t = re.sub(r"Sabse Zyada Search Kiye Jane Wale", "Sabse Zyada Poochhe Jaane Wale", t, flags=re.I)
    t = re.sub(r"^\s*Low-Competition Search Sawaal\s*\(People Also Ask\)", "Log Ye Bhi Poochhte Hain", t, flags=re.I)
    t = re.sub(r"\s*\(Quick FAQ\)", "", t, flags=re.I)
    t = re.sub(r"\s*aur keyword cluster\b", "", t, flags=re.I)
    t = re.sub(r"\bsearch pack\s*:\s*", "Mein ", t, flags=re.I)
    t = t.replace("हिंदी सर्च पैक:", "हिंदी में")
    t = re.sub(r"\s*\((?=[^)]*(\bpage\b|e-e-a-t|eeat|aap bhej|aap bhar|module|pushti|verify|ke liye sandarbh))[^)]*\)", "", t, flags=re.I)
    t = re.sub(r"\bkaise pushti karein\b", "Kaise Pata Karein", t, flags=re.I)
    t = re.sub(r"\s*\((jo|jahan) (pakki|pakka|source) [^)]*\)", "", t, flags=re.I)
    t = re.sub(r"^((?:\d+\.)+\d*\s+)?Jo pakka mila\s*:\s*", r"\1", t, flags=re.I)
    t = re.sub(r"^((?:\d+\.)+\d*\s+)?Jo pakka hai\s*$", r"\1Pramukh Aitihasik Sthal", t, flags=re.I)
    t = re.sub(r"\s*\((jo )?hamare paas[^)]*\)", "", t, flags=re.I)
    t = re.sub(r"\s+(aur|aur hamare)?\s*hamare paas kya hai\s*$", "", t, flags=re.I)
    t = re.sub(r"\bjo hamare paas verified (hai|hain)\b", "", t, flags=re.I).strip()
    t = re.sub(r"^(\d+\.\d+)\s*$", "", t)
    t = re.sub(r"\bIs page ke liye istemal kiye gaye aur sujhaye gaye\b", "Istemal kiye gaye", t, flags=re.I)
    t = unblueprint(t).replace("Master Schemas", "Master Reference").replace("MASTER SCHEMAS", "MASTER REFERENCE")
    t = re.sub(r",\s*Schema[- ]Ready\s*\)", ")", t, flags=re.I)
    t = re.sub(r"\s*\(\s*Schema[- ]Ready\s*\)", "", t, flags=re.I)
    m = re.match(r"^\s*MODULE\s+\d+\s+FAQ\s+POOL\s*(?:\((.*)\))?", t, re.I)
    if m:
        return "Aksar poochhe jaane wale sawal" + (": " + fix_text(m.group(1)) if m.group(1) else "")
    t = re.sub(r"^\s*MODULE\s+\d+\s+(?=[A-Z])(?!.*:)", "", t)
    t = re.sub(r"\s*\((?:Headings?|Heading)\s*\d+[^)]*\)", "", t, flags=re.I)
    t = re.sub(r"^MODULE\s+\d+\s*(\([^)]*\))?\s*:\s*", "", t, flags=re.I)
    if dname:
        t = re.sub(r"^%s\s*[—–-]\s*" % re.escape(dname.upper()), "", t)
        t = re.sub(r"^%s\s*[—–-]\s*" % re.escape(dname), "", t)
    t = titlecase(t.strip(" :—–-"))
    return fix_text(t)


# v3.3 (14 Nov): lekhak/editor ko likhi line (pathak ke liye nahi) - vaakya ke star par alag (baaki vaakya page par rehte hain)
EDITOR_SENT = re.compile(
    r"publish (se pehle|karne se pehle|karte samay|karein|karna)|chhapne se pehle|aapki website|apni site|site ke asli url|pro tip|"
    r"original content ka mauka|placeholder|\.docx|agla kadam|aage ka kaam|page yahin samaapt|module \d+ samaapt|\bschema\b|"
    r"e-e-a-t|google ko (pasand|\W?original)|google ke \W?(people|logon)|seo\b|featured snippet|long-tail|internal linking|ranking|"
    r"sirf editor|editorial check|ye table bharein|kaun bharein|aap bharein|personal review banayein|jaisa guide banayein|"
    r"content (banayein|likhein)|community (contribution )?box|community contribution|section 199|heading 199|comment me likhein|appendix [a-f]\b|is file\b|ye document|yeh document|"
    # v3.3 (owner 14 Nov: 'mere liye likhi personal line hatao'): lekhak ki apni kahani / 'mere paas data nahi' / baad ka vaada
    r"\bmere paas\b|\bhamare paas (pakka|verified|abhi)|\bmaine\b(?! nahi chakh)|\bmain ne\b|nahi likh(a|e|i)\b|nahi likh rahe|"
    r"\b(likhenge|jodenge|banayenge|daalenge|bharenge)\b|mool sandarbh-suchi|blueprint|verify nahi hu|pushti nahi hu|abhi tayyar nahi|"
    r"check karwa lein|website par lagane|site par (jodein|daalein)|aapne bataya|website owner|sabhisaab\.com team|namaste doston|"
    r"\bis module (me|ke|ka)\b|\bthis module\b|\bhum\b[^.]{0,70}\b(karenge|kar paaye|nahi paaye)\b|aapki site|"
    r"jab aap [^.]{0,30}(verify|pushti) kar|verify karne ka tareeka|“verify”|\"verify\"",
    re.I)

ABBR = re.compile(r"(?:\b(?:Dr|Mr|Mrs|Ms|St|No|Rs|Sri|Shri|Pt|Lt|Col|Gen|Capt|Prof|vs|etc|Smt|Km|km|ft|sq|Sq|approx|Govt|Ltd|Co|Jr|Sr|"
                  r"cm|kg|gm|mm|ml|hr|hrs|min|sec|Nos?|Ft|Mt|Mts|Jan|Feb|Mar|Apr|Aug|Sept?|Oct|Nov|Dec|ca|c|ii|iii|iv|viz|ie|eg|Ex)|\b[A-Z])\.$")
# lekhak/document ke baare mein - pathak ke kaam ka nahi (poora vaakya-tukda hatega)
META = re.compile(
    r"publish (se pehle|karne se pehle|karte samay|karein|karna)|chhapne se pehle|aapki website|apni site|aapki site|site ke asli url|"
    r"original content ka mauka|placeholder|\.docx|word file|aage ka kaam|agla kadam hai|agla kadam:|page yahin samaapt|module \d+ samaapt|"
    r"\bschema\b|json-ld|e-e-a-t|google ko (pasand|\W?original)|google ke \W?(people|logon)|\bseo\b|featured snippet|long-tail|"
    r"internal link|anchor text|link (karein|dein|lagayein|jodein)|links? ko .{0,30}(jodna|badal)|googlebot|\bctr\b|dwell time|index ho|"
    r"sirf editor|editorial check|sampadkiya|ye table bharein|kaun bharein|aap bharein|apna andaza bharein|personal review banayein|jaisa guide banayein|"
    r"content (banayein|likhein)|community (contribution )?box|community contribution|community prompt|section 199|heading 199|"
    r"comment me likhein|neeche ke form|form me bhejein|appendix [a-f]\b|\bis file\b|ye document|yeh document|is document|"
    r"\bmere paas\b|\bmujhe\b[^.“”\"]{0,140}\b(nahi|web|source|pata)\b|\bmaine\b(?! nahi chakh)|\bmain ne\b|\bmain koi\b|\bmain (yahan )?(nahi|kisi)\b|"
    r"\bhamare paas\b|\bhume\b [^.]{0,40}nahi mil|nahi likh|na(hi)? (di|diya|diye|likhi|likha|likhe) (gayi|gaya|gaye)|likha nahi gaya|"
    r"nahi de rahe|nahi daal rahe|nahi bata rahe|nahi kar rahe|koi daava nahi kar rahe|"
    r"(?<![(“\"])\b(hum|ham|main)\b[^.“”\"]{0,90}\b(likhenge|jodenge|banayenge|daalenge|bharenge|chhapenge|sudharenge|denge|batayenge|"
    r"bana sakte hain|intezaar kar rahe|jodna chahenge|baad me)\b|\bye hum aage\b|joden ge\b|jod denge\b|\bse module \d+ me\b|^[^“”\"(]*\b(jodenge|chhapenge|bharenge)\b|jodi jayegi|joda jayega|verify (nahi )?hu(i|a|e)|pushti nahi hu|"
    r"verify (karenge|karke)|abhi tayyar nahi|check karwa lein|cross-check karwa|website par lagane|site par (jodein|daalein)|aapne bataya|"
    r"aapne .{0,40}likhwaye|website owner|sabhisaab\.com team|namaste doston|\bthis module\b|"
    r"\bhum\b[^.]{0,70}\b(karenge|kar paaye|nahi paaye|sudhar rahe)\b|jab aap [^.]{0,30}(verify|pushti) kar|verify karne ka tareeka|"
    r"“verify”|\"verify\"|source-tag|\[s\]|\[b\]|\[m\]|is page ke source|is page ke liye verify|pro tip|search phrases|"
    r"^(hum|humne|main|mujhe|hame|hamein|hume)\b.{0,200}\b(nahi|na)\b|hamare dekhe|hamare sources me|\bmere dwara\b|"
    r"(?<![“\"(])\bmujhe\b[^.“”\"]{0,80}\b(mil|pakk|source)|\bis heading\b|bina verify ke|flag ka matlab|page ke liye salah|sampa?dakiya|"
    r"\b(na likhein|man se na likhein|karke likhein|ke saath (hi )?likhein|pages? par (vistar se )?likhein|jodkar likhein|aisa likhein|"
    r"shabdon se likhein|tathya na likhein|bhasha me hi likhein|chhapein|samman ke saath likhein)\b|[\"“][^\"”]{2,80}[\"”] likhein|\bhum\b[^.]{0,80}\b(gadh|nahi keh|nahi bol)|"
    r"\bkeywords?\b|verify nahi hai|likhe ja chuke hain|\bmodule\b[^.]{0,40}\b(samapt|samaapt)\b|jawab likhne se pehle|agla module|\bab tak headings\b|nahi de raha|nahi likh raha|nahi bata raha|\bmere search\b|aage badhein:|alag se banega|search-friendly|\d+-heading|^isliye humne yeh page|laga sakte hain|interactive banane|pehle ke module dekhein|"
    r"aapka page|table bhar|aapko bharna|alag page|page bana|page se jodein|page par [^.]{0,40}\blikh|likhne ka niyam|bina verify kiye|"
    r"copy na karein|bhavarth likhein|\bhum\b[^.]{0,60}\blikhte hain\b|jaan-?boojh ?kar khali|"
    r"itna hi verified|verified data (abhi )?nahi|verified (suchi|list|record) (abhi )?nahi|vishay-suchi hai|apne page par|page par [^.]{0,60}\b(likhein|dein|rakhein|lagayein|na likhein)\b|"
    r"\bis page (par|me|mein|ke|ko)\b|likhte samay|likhne ke liye:|\bhum\b[^.]{0,80}\b(jodenge|karenge|denge)\b|"
    r"(?<![(“\"])\bhum\b[^.“”\"]{0,100}\bnahi\b|mere dekhe|\bmere\b[^.“”\"]{0,30}\b(sroton|source|paas)\b|tabhi likhein|likhein jab|\blikhein\b[^.]{0,30}\bjab tak\b|aap(ne)? (use )?khud (verify|jaakar|jaanch)|khud verify kiya|verify karke chhap|"
    r"chhap sakte|hamari team|apni team|aap.{0,20}(page|site) par|verify nahi kar|verify nahi ki|confirm nahi kar|jo hum verify|"
    r"avoid karein jab tak|\bgoogle\b(?!\s*maps)|search karte|search hote|search hoti|search me log|"
    r"#\s*module\b|aapke traffic|page ka aakhri hissa|likhna (galat|sahi nahi) hoga|sirf wahi jo verify|agli heading \d+|likhne ka format|format \(template\)|"
    r"sirf wahi likhein|verify_list|verify nishan|verify\W? likh rahe|publish karte (waqt|hain)|page publish|template\W? (me|mein) jodein|"
    r"template de sakte|khaali template diya|template \(jise bhar|^template:|aakhri module|module \d+ part [a-z]|^agla:|"
    r"apni website par (ek|banayein|bana)|bharkar apni website|tabhi (likhenge|dalenge|daalenge|jodenge)|\bme likhenge\b|"
    r"wo baat galat thi aur yahan sahi|kehna zyada imandar|likhna galat hoga, isliye abhi nahi|data-sangrah|sampadak ka sujhav|"
    r"search jo is|pichhle \d+ headings|audit me|logon ne yeh bhi|hamari policy|dukandar ka haq|paid listing|mool sandarbh-suchi|blueprint", re.I)
# 'mool sandarbh-suchi' wale vaakya: document ke baare mein (hatao) - warna sirf shabd hatao, tathya rakho
MSS_DOC = re.compile(r"\b(likha|likhe|likhi|likhkar|diya|diye|di gayi|di gai|manga|mange|maange|maangi|mangi|ginaya|ginayi|ginaye|"
                     r"zikr|zikra|aaya|aaye|aayi|bataya|batayi|daava|dawa|claim|galti|galat|sudhar|sudhaar|chahiye tha|par ek dhyan|se alag|"
                     r"ke anusar|ke hisaab|ke aadhar|wala|wali|wale|tha|the|thi|hai ki|maangta|deta hai|karta hai)\b", re.I)
REWRITE = [
    (r"^\s*Is module (me|mein) (kya kya hai|kya milega|kya hai)\s*:\s*", "Is hisse mein: "),
    (r"^\s*Is module (ke|ka) (\d+ )?(saaf |zaroori |mukhya )*niyam( \(zaroor padhein\))?\s*:\s*", ""),
    (r"\b(I|i)s module (me|mein)\b", r"\1s hisse mein"), (r"\b(I|i)s [Mm]odule (ke|ka|ki|ko)\b", lambda m: m.group(1) + "s hisse " + m.group(2).lower()),
    (r"^(mool sandarbh-suchi|blueprint) (ke|ki|ka) (shabd|naam)\s*\(([^)]*)\)\s*:\s*", r"\3 (\4): "),
    (r"^(mool sandarbh-suchi|blueprint) (ke|ki|ka) aur upay\s*\(([^)]*)\)\s*:\s*", r"Kuch aur lok-upay (\3): "),
    (r"\s*\((mool sandarbh-suchi|purane sandarbh|blueprint) ke (anusar|hisaab se)\)", ""),
    (r",?\s*isliye page par [^:.;]{0,60} na likhein", ""),
    (r"^(verify|pushti) karein\s*:\s*", "Dhyan dein: "), (r"^(verify|pushti) note\s*:\s*", "Dhyan dein: "),
    (r"\b(Y|y)eh? module\b", r"\1eh hissa"), (r"\b(I|i)s module ko\b", r"\1s hisse ko"),
    (r"^\(?(Imandari ki baat|Imaandari ka note|Sach ye hai|Ek spashtikaran|Sabhisaab Verification Note|Sampadkiya (niyam|salah|savdhani|sujhav))\s*:\s*", ""),
]
REWRITE = [(re.compile(a, re.I), b) for a, b in REWRITE]
CLAUSE = re.compile(r"\s*;\s*|,\s*(?=(?:isliye|kyunki|kyonki|kyuki|lekin|par|balki|jabki|hum|main|yahan|aur hum)\b)")
TOPIC = re.compile(r"^(?:(?:dhyan dein|note)\s*:\s*)?(?P<x>.+?)\s+(?:(?:hum|main)\s+(?:yahan\s+|is page par\s+)?(?:koi\s+|kisi\s+)?[^,;]{0,25}?(?:nahi|na)\s+(?:de|likh|bata|daal))", re.I)
VERB_END = re.compile(r"\b(hai|hain|tha|the|thi|hota|hoti|hote|hoga|hogi|honge|karein|karen|kijiye|dekhein|lein|len|poochhein|puchhein|"
                      r"milta|milti|milte|milega|milegi|jata|jati|jate|jaata|jaati|jaate|gaya|gayi|gaye|sakte|sakti|sakta|chahiye|rehta|rehti|rehte|"
                      r"karta|karti|karte|padta|padti|padte|lagta|lagti|lagte|banta|banti|bante|aata|aati|aate|rakhein|bachein|jaayein|jayein|"
                      r"jaanchein|milayein|upyog karein|sampark karein|dein|batayein|hua|hui|hue)\s*[.!?।)\]]*\s*$", re.I)
POINTER = re.compile(r"(dekhein|dekh lein|lein|karein|poochhein|puchhein|poochein|pooch lein|milayein|jaanchein|jaanch lein|sampark karein|upyog karein)\s*[.!]?$", re.I)
NUMMARK = re.compile(r"^\(?\d{1,2}[.)]\s*$")

def _sentences(t):
    parts = [y for z in re.split(r"(?<=[.!?।])\s+", t) for y in re.split(r"\s+(?=-\s+[A-Z0-9“\"(])", z)]
    out = []
    for x in parts:
        prev_q = len(out) >= 2 and out[-2].rstrip().endswith("?")
        if out and (ABBR.search(out[-1]) or (NUMMARK.match(out[-1]) and not prev_q)):
            out[-1] = out[-1] + " " + x
        else:
            if out:
                m = re.search(r":\s*(\d{1,2}\.)$", out[-1])       # 'niyam: 1.' -> '1.' agle vaakya ke saath
                if m:
                    out[-1] = out[-1][:m.start() + 1].rstrip()
                    x = m.group(1) + " " + x
            out.append(x)
    return out

def _cap(x):
    x = x.strip(" ,;")
    return x[:1].upper() + x[1:] if x else x

def _voice(sent, lenient=False):
    """-> (pathak ka roop ya '', hataya hissa ya '')"""
    m = re.match(r"^(\d{1,2}\.\s*|-\s+)", sent)
    if m and sent[m.end():].strip():
        k, d = _voice(sent[m.end():], lenient)
        return (m.group(1) + k if k else ""), (sent if d else "")
    s = sent
    if s.startswith("(") and s.rstrip(".").endswith(")") and META.search(s[1:]):
        return "", sent
    for rx, rep in REWRITE:
        s = rx.sub(rep, s)
    s = s.strip()
    if not s or (NUMMARK.match(s) and not NUMMARK.match(sent.strip())):
        return "", sent
    if re.search(r"mool sandarbh-suchi|blueprint", s, re.I):
        if MSS_DOC.search(s):
            return "", sent
        s2 = re.sub(r"\s*\((?:[^()]{0,30}\s)?(?:mool sandarbh-suchi|blueprint)[^()]{0,40}\)", "", s, flags=re.I)
        s2 = re.sub(r"(?:(?<=^)|(?<=\s)|(?<=:))\s*(mool sandarbh-suchi|blueprint)\s+(ke|ki|ka|me|mein)?\s*", " ", s2, flags=re.I)
        s2 = re.sub(r"\s*(mool sandarbh-suchi|blueprint)\s*", " ", s2, flags=re.I)
        s2 = re.sub(r"\s{2,}", " ", s2).strip()
        if len(s2.split()) >= 5 and not META.search(s2):
            return _cap(s2), ""
        return "", sent
    if not META.search(s):
        return s, ""
    # tukdon mein: pathak ke kaam wala tukda bachao (jaise 'mandir par pehle se poochhein; hum dar nahi likh rahe')
    cl = [c for c in CLAUSE.split(s) if c and c.strip()]
    keep = []
    for c in cl:
        c2 = re.sub(r"^\s*(isliye|to|aur)\s+", "", c, flags=re.I)
        if META.search(c2) or len(c2.split()) < (2 if lenient else 5) or (not lenient and not VERB_END.search(c2)) or re.match(r"^\s*(kyunki|kyonki|kyuki|balki|jabki|lekin|par)\b", c2, re.I):
            continue
        if c2 is not c and c2 != c and not POINTER.search(c2):
            continue                                    # 'isliye ...' sirf tab jab salah ho ('isliye 112 ka upyog karein')
        keep.append(c2)
    if keep and len(cl) > 1:
        m = TOPIC.match(cl[0].strip())
        if len(keep) == 1 and POINTER.search(keep[0]) and m and 3 <= len(m.group("x").split()) <= 14 and not META.search(m.group("x")):
            p = keep[0].strip()
            return _cap(m.group("x").strip(" ,")) + " ke liye " + p + ("" if p.endswith((".", "!")) else "."), sent
        out = "; ".join(_cap(c) for c in keep)
        out = out if out.endswith((".", "?", "!", "।")) else out + "."
        return out, sent
    return "", sent

def _balance(k):
    if k.count("(") > k.count(")") and k.lstrip().startswith("("):
        k = k.lstrip()[1:]
    elif k.count(")") > k.count("(") and re.search(r"\)\s*[.!?]?$", k):
        k = re.sub(r"\)(\s*[.!?]?)$", r"\1", k)
    return k

def split_editor(t, lenient=False):
    """-> (pathak ke vaakya, editor ke vaakya). v3.3.2: poora vaakya tabhi hatega jab usme pathak ke kaam ka kuch na bache."""
    keep, drop = [], []
    sents = _sentences(t)
    numbered = sum(1 for x in sents if re.match(r"^\d{1,2}\.\s", x))
    for x in sents:
        k, d = _voice(x, lenient)
        if k:
            keep.append(k)
        if d and not k:
            drop.append(d)
        elif d and k != x:
            drop.append("[tukda] " + d)
    if numbered and any(re.match(r"^\d{1,2}\.\s", d) for d in drop):
        keep = [re.sub(r"^\d{1,2}\.\s*", "", k) for k in keep]       # kram toota to number hatao
    keep = [_balance(k) for k in keep if k.strip() not in ("-", "")]
    while keep and NUMMARK.match(keep[0]) and len(keep) > 1 and not keep[0].endswith(")"):
        break
    return " ".join(keep).strip(), drop

def unblueprint(t):
    t = re.sub(r"\s*\((?:blueprint|mool sandarbh-suchi) ke (?:anusar|hisaab se)\)", "", t, flags=re.I)
    t = re.sub(r"\s*\(blueprint\)", "", t, flags=re.I)
    t = re.sub(r"\bBlueprint (ke anusar|ke hisaab se)", r"purane sandarbh \1", t, flags=re.I)
    t = re.sub(r"\bBlueprint\b", "mool sandarbh-suchi", t, flags=re.I)
    return t
