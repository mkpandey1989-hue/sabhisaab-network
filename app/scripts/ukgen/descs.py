"""v3.3.2 audit-3: har zila-page ka description (meta + page ka pehla para) ALAG.

Pehle 264 mein se 247 page ka description ek hi saancha tha, sirf zile ka naam badalta tha (Google ise 'boilerplate' maanta hai
aur khud badal deta hai; pathak ko bhi page ka asli maal nahi dikhta). Ab har page ke description mein us zile ki 2-3 asli,
mashhoor jagah/cheez ke naam - wahi jo us page ke text mein sach mein baar-baar aate hain (kam se kam 2 baar). Naam neeche ki
suchi se (sab sarvajanik, mashhoor naam); page mein na mile to purana description hi rehta hai (kuch gadha nahi jaata).
Audit seema: 95-165 akshar.
"""
import json
import re

ENT = {
    "almora": ["Jageshwar", "Kasar Devi", "Binsar", "Ranikhet", "Chitai", "Katarmal", "Dwarahat", "Chaukhutia", "Kosi",
               "Bal Mithai", "Lakhudiyar", "Syalde Bikhauti", "Someshwar"],
    "bageshwar": ["Bagnath", "Baijnath", "Kausani", "Pindari", "Kafni", "Sunderdhunga", "Saryu", "Gomti", "Kanda",
                  "Uttarayani", "Kapkot", "Garur"],
    "chamoli": ["Badrinath", "Hemkund Sahib", "Valley of Flowers", "Auli", "Joshimath", "Gopeshwar", "Roopkund", "Mana",
                "Nanda Devi", "Kuari Pass", "Alaknanda", "Chipko", "Gairsain", "Karnaprayag", "Nandprayag", "Ramman"],
    "champawat": ["Lohaghat", "Abbott Mount", "Purnagiri", "Devidhura", "Bagwal", "Tanakpur", "Mayawati", "Baleshwar",
                  "Pancheshwar", "Banbasa", "Pati"],
    "dehradun": ["Mussoorie", "Rishikesh", "Sahastradhara", "Chakrata", "Robber's Cave", "Forest Research Institute",
                 "Tapkeshwar", "Kempty", "Vikasnagar", "Rajaji", "Jaunsar", "Doiwala"],
    "haridwar": ["Har Ki Pauri", "Kumbh", "Roorkee", "Mansa Devi", "Chandi Devi", "Rajaji", "Piran Kaliyar", "Kankhal",
                 "Ganga Aarti", "Laksar", "Bhagwanpur"],
    "nainital": ["Naini Jheel", "Bhimtal", "Haldwani", "Ramnagar", "Corbett", "Mukteshwar", "Kainchi Dham", "Sattal",
                 "Naukuchiatal", "Kathgodam", "Kosi"],
    "pauri-garhwal": ["Lansdowne", "Kotdwar", "Srinagar", "Khirsu", "Tarkeshwar", "Dhari Devi", "Kandoliya",
                      "Binsar Mahadev", "Satpuli", "Kanvashram", "Thalisain"],
    "pithoragarh": ["Munsiyari", "Dharchula", "Patal Bhuvaneshwar", "Gangolihat", "Chaukori", "Om Parvat", "Kailash",
                    "Askot", "Milam", "Narayan Ashram", "Johar", "Berinag", "Didihat"],
    "rudraprayag": ["Kedarnath", "Tungnath", "Chopta", "Madhyamaheshwar", "Guptkashi", "Ukhimath", "Deoria Tal",
                    "Gaurikund", "Sonprayag", "Triyuginarayan", "Mandakini", "Agastyamuni"],
    "tehri-garhwal": ["Tehri Dam", "New Tehri", "Dhanaulti", "Surkanda Devi", "Kunjapuri", "Chamba", "Devprayag",
                      "Khatling", "Kanatal", "Ghansali", "Bhilangana", "Narendranagar"],
    "udham-singh-nagar": ["Rudrapur", "Kashipur", "Khatima", "Sitarganj", "Nanakmatta", "Jaspur", "Pantnagar", "Atariya",
                          "Bajpur", "Tharu", "Gadarpur"],
    "uttarkashi": ["Gangotri", "Yamunotri", "Harsil", "Dodital", "Dayara", "Gaumukh", "Har Ki Dun", "Barkot", "Purola",
                   "Kedarkantha", "Nelong", "Bhagirathi"],
}

# Khane ke page: vyanjan ke naam (poore Uttarakhand ke mashhoor) - jo is page mein sabse zyada aur doosre zilon se alag
DISH = ["Kafuli", "Phaanu", "Chainsoo", "Bhatt ki Churkani", "Aloo ke Gutke", "Jhangore ki Kheer", "Arsa", "Singori",
        "Bal Mithai", "Kandali", "Dubuk", "Baadi", "Thechwani", "Gahat", "Rus", "Sisunak", "Bhang ki Chutney", "Rot",
        "Swale", "Gulgula", "Jholi", "Kapa", "Bhatt", "Mandua", "Jhangora", "Pisyun Loon", "Lingude", "Timla", "Khatai"]

SHORT = {   # {E} = 2-3 naam; baaki hissa us vishay ka saar
    "main": "{D} zile ki poori jaankari: {E} — mukhya jagah, doori-samay, unchai, emergency number aur seedhe jawab.",
    "identity": "{D} zila prashasan: {E} — tehsil, block, vidhan sabha, police, RTO, PIN aur STD code ek page par.",
    "geo": "{D} ka bhugol: {E} — chotiyan, ghatiyan, nadiyan, sangam, taal, jharne aur bhukamp zone.",
    "climate": "{D} ka mausam aur jungle: {E} — har mahine ka mausam, barf, ped-paudhe, jadi-booti aur jeev-jantu.",
    "land": "{D} mein zameen aur kheti: {E} — nali-mutthi naap, khasra-khatauni, bhoo-kanoon aur pahadi kheti.",
    "food": "{D} ka pahadi khana: {E} — mandua-jhangora, chutney, jungli saag, mithai aur ghar ke tareeke.",
    "culture": "{D} ki sanskriti: {E} — lok-nritya, lok-geet, aipan, tyohar, mele aur samaj ki paramparayein.",
    "history": "{D} ka itihas aur mandir: {E} — raajvansh, angrezi daur, andolan, devta aur lok-kathayein.",
    "tourism": "{D} mein ghumne ki jagah: {E} — chhupe sthal, trek, adventure, kab jayein aur taiyar itinerary.",
    "transport": "{D} kaise pahunchein: {E} — railway station, airport, bus-taxi, doori aur rukne ki jagah.",
    "economy": "{D} ki arthvyavastha: {E} — kheti-bagwani, hastshilp, GI-ODOP utpad, udyog, shiksha aur sehat.",
    "buzurg": "{D} ka purana pahadi jeevan: {E} — buzurgon ki dincharya, purana khana, naap-tol, gharat aur naula.",
    "shabd": "{D} ki boli aur {B} shabd: {E} — rishton ke naam, kahawatein, paheliyan, lok-geet aur lok-sahitya.",
    "vaidya": "{D} ki vaidya parampara aur aastha: {E} — gharelu nuskhe (doctor ki salah ke saath), devta aur lok-vishwas.",
    "hyperlocal": "{D} ke gaon aur bazaar: {E} — patti-pargana, block, kasbe, purane pul-kile aur raaste ki doori.",
    "sarkari": "{D} mein sarkari seva: {E} — Bhulekh khatauni, praman patra, Apuni Sarkar, UCC aur helpline.",
    "career": "{D} GK aur career: {E} — UKPSC-UKSSSC taiyari, school-college, ITI, fauj bharti aur abhyas prashn.",
    "aadhunik": "{D} mein basna: {E} — workation, retirement, ghar banana, kharch, suvidhayein aur suraksha.",
    "bhavishya": "{D} ki pariyojanayein aur aapda itihas: {E} — sadak-rail-ropeway, purani aapdayein aur GK quiz.",
    "prasiddh": "{D} ki yojanayein, khel aur prasiddh log: {E} — sarkari yojana, khiladi, media aur desi gyan.",
}


def _text(items):
    return json.dumps(items, ensure_ascii=False)


def _join(es):
    return es[0] if len(es) == 1 else ", ".join(es[:-1]) + " aur " + es[-1]


def _count(names, t, need):
    cnt = [(len(re.findall(r"(?<![A-Za-z])%s(?![a-z])" % re.escape(n), t, re.I if n in DISH else 0)), i, n)
           for i, n in enumerate(names)]
    return [n for _, _, n in sorted([c for c in cnt if c[0] >= need], key=lambda c: (-c[0], c[1]))]


def pick(page, k=3, df=None):
    t = _text(page["items"])
    if page.get("theme") == "food":
        es = _count(DISH, t, 2)
        if df:                                   # doosre zilon ke khane-page se alag naam pehle
            es = sorted(es, key=lambda n: df.get(n, 0))
        if es:
            return es[:k]
    names = ENT.get(page.get("district") or "", [])
    return (_count(names, t, 2) or _count(names, t, 1))[:k]


def unique_desc(pages, log=None):
    """Theme/main zila pages: description mein page ke apne mashhoor naam. -> kitne badle"""
    n = 0
    df = {}
    for p in pages:
        if p.get("district") and p.get("theme") == "food":
            for d in set(_count(DISH, _text(p["items"]), 2)):
                df[d] = df.get(d, 0) + 1
    for p in pages:
        tpl = SHORT.get(p.get("theme")) if p.get("district") else None
        if not tpl:
            continue
        es = pick(p, df=df)
        while es:
            d = tpl.format(D=p["D"], B=p.get("boli") or "", E=_join(es))
            if len(d) <= 165:
                break
            es = es[:-1]
        if not es or len(d) < 95:
            continue
        if log is not None:
            log.append((p["slug"], p["desc"], d))
        p["desc"] = d
        n += 1
    return n
