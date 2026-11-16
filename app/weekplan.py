"""v2.2.0 (3 Nov 2026): HAFTE KA DIN-PLAN - har channel ka har din ek alag andaaz (log roz kuch naya dekhein, ruk kar dekhein).

Topic waise hi aate hain (aapka plan > aapke topic > website page > idea > trend). Din-plan sirf ANDAAZ (hook/format) batata hai,
aur Pahadi ke liye kuch din ka VISHAY (GK / purane naam / pahadi shabd). Aapka Sample Studio wala pakka look upar se laagu.
Badlaav sirf dohri pushti se ("somvaar money: kahani andaaz"). Kuch bhi badle bina bot roz khud isi se chalta hai.
"""
import datetime

from . import state
from .config import BRANDS

SHORT = {"sunonatak": "Suno Natak", "money": "Money", "deals": "Deals", "pahadi": "Pahadi"}
DAYS = ["Somvaar", "Mangalvaar", "Budhvaar", "Guruvaar", "Shukravaar", "Shanivaar", "Ravivaar"]
DAY_KEYS = ["somvaar", "mangalvaar", "budhvaar", "guruvaar", "shukravaar", "shanivaar", "ravivaar"]

# har din: (andaaz ka naam, writer ko hidayat)
ANDAAZ = {
    "sawal": ("Sawal se shuru", "pehli 2 second mein ek seedha sawal jis par dekhne wala ruk jaye; jawab beech mein, poora hisaab end mein"),
    "kahani": ("Chhoti kahani", "ek aam ghar ki chhoti kahani (naam aam, jaise Ramesh/Sunita); galti -> sabak -> tool se hisaab"),
    "myth": ("Myth vs Fact", "ek aam galatfehmi pehle, phir sach 3 saaf point mein, number ke saath"),
    "tips": ("Top-3 tez tips", "3 numbered tips, har scene chhota aur punchy, aakhri tip sabse kaam ki"),
    "galti": ("5 galtiyan", "log jo galti karte hain (3-5), har galti ka nuksaan rupaye mein"),
    "challenge": ("10 second challenge", "screen par sawal + '10 second mein jawab do' + timer jaisa ehsaas; comment mein jawab maango"),
    "recap": ("Hafte ka sabse kaam ka", "is hafte ka sabse kaam ka hisaab/tathya, saaf udaharan ke saath, save karne layak"),
}
# v2.3.3 (owner 3 Nov + market trend: quiz reels + couple micro-drama): 3 TOP FORMAT - 'dimag + pyaar' combo, sab SAWAL wale
ANDAAZ.update({
    "dil_dimag": ("Dil vs Dimag", "COUPLE MICRO-DRAMA: ek pyaara couple (naam aam: Aarav-Riya / pahad par Mohan-Kamla), ladki pyaar se "
                  "ek dimagi sawal poochti hai ('agar sach mein pyaar hai to 5 second mein batao'); ladka atakta hai; dekhne wale se "
                  "4 vikalp; jawab + kyun; aakhir mein meetha twist (ek line). Saaf-suthra, parivaar ke saath dekhne layak"),
    "pyaar_hisaab": ("Pyaar ka Hisaab", "COUPLE + PAISA/BACHAT SAWAL: shaadi/gift/date/EMI/gold jaisi asli life situation mein couple ki "
                     "pyaari bahas, beech mein asli number wala sawal (4 vikalp), sahi jawab ka 2 line hisaab, aakhir mein "
                     "'ek dusre ka hisaab rakho' jaisa meetha sabak"),
    "sach_jhooth": ("Sach ya Jhooth", "GUESS THE LIE (2026 ka trend): couple/dost ek-dusre ko 3 baatein kehte hain, ek jhooth hai; "
                    "dekhne wala pakde (4 vikalp: pehli/doosri/teesri/teeno sach); jawab + asli tathya; tathya pakke hon"),
})
# brand -> 7 din (Somvaar se) - teeno format baari-baari, Ravivaar recap bhi sawal wala
DEFAULT = {
    "sunonatak": ["dil_dimag", "sach_jhooth", "dil_dimag", "pyaar_hisaab", "dil_dimag", "sach_jhooth", "challenge"],
    "money": ["pyaar_hisaab", "sach_jhooth", "pyaar_hisaab", "dil_dimag", "pyaar_hisaab", "challenge", "sach_jhooth"],
    "deals": ["pyaar_hisaab", "dil_dimag", "sach_jhooth", "pyaar_hisaab", "challenge", "pyaar_hisaab", "dil_dimag"],
    "pahadi": ["dil_dimag", "sach_jhooth", "dil_dimag", "pyaar_hisaab", "dil_dimag", "sach_jhooth", "challenge"],
}
# Pahadi: kuch din ka vishay (topic) bhi - kabhi dohraav nahi (180 din), tathya Google search se jaanch (audit_ai)
PAHADI_DAY_TOPICS = {
    0: [  # Somvaar: Uttarakhand GK
        "Uttarakhand GK: rajya kab bana aur kitne zile", "Uttarakhand GK: sabse ooncha shikhar", "Uttarakhand GK: rajya pashu, pakshi, phool, vriksh",
        "Uttarakhand GK: char dham kaun se", "Uttarakhand GK: panch prayag kaun se aur kahan", "Uttarakhand GK: prasiddh taal (jheel)",
        "Uttarakhand GK: rashtriya udyan aur abhayaranya", "Uttarakhand GK: Garhwal aur Kumaon mandal ke zile",
        "Uttarakhand GK: badi nadiyan aur unka udgam", "Uttarakhand GK: prasiddh lok nritya", "Uttarakhand GK: prasiddh mele",
        "Uttarakhand GK: Chipko andolan", "Uttarakhand GK: rajya ke pratham", "Uttarakhand GK: prasiddh mandir aur unki kahani",
    ],
    2: [  # Budhvaar: purane naam / itihaas
        "Uttarakhand ke shaharon ke purane naam aur unka matlab", "Garhwal ke 52 garh - kya hai kahani", "Kumaon ka purana naam kya tha",
        "Dehradun naam kaise pada", "Almora aur Nainital ke naam ki kahani", "pahad ke purane naap: nali, mutthi, bigha, mana",
        "pahad ke purane bartan aur unke naam", "pahadi gaon ke purane ghar (bakhli, tibari) ka matlab", "pahad ke purane khel",
    ],
    4: [  # Shukravaar: pahadi shabd / boli
        "Garhwali ke 10 shabd jo shahar mein bhool gaye", "Kumaoni ke 10 anokhe shabd aur matlab", "pahadi rishton ke naam (Garhwali/Kumaoni)",
        "pahadi khane ke naam aur kaise bante", "pahadi kehawatein aur unka matlab", "ginti aur din ke naam pahadi boli mein",
        "pahadi kapdon aur gehno ke purane naam", "kheti ke pahadi shabd (hal, jol, kudal...)",
    ],
}


def _over():
    return state.get("day_plan_over") or {}


def on():
    return state.get("day_plan_on", True)


def today_andaaz(brand, d=None):
    d = d or datetime.date.today()
    wd = d.weekday()
    o = (_over().get(brand) or {}).get(str(wd))
    if o:
        return o, o
    k = DEFAULT.get(brand, DEFAULT["money"])[wd]
    return ANDAAZ[k]


def style_for(brand, d=None):
    """Roz ki video ke liye writer hidayat (din ka andaaz). Plan band ho to ''."""
    if not on():
        return ""
    name, how = today_andaaz(brand, d)
    return f"Aaj ka andaaz ({name}): {how}"


def day_topic(brand, used, d=None):
    """Pahadi ke GK/purane naam/shabd wale din: is din ka ek naya vishay (180 din mein dohraav nahi)."""
    if brand != "pahadi" or not on():
        return None
    d = d or datetime.date.today()
    pool = PAHADI_DAY_TOPICS.get(d.weekday())
    if not pool:
        return None
    cut = str(d - datetime.timedelta(days=180))
    fresh = [t for t in pool if used.get(t, "0") < cut]
    return fresh[0] if fresh else None


def text():
    L = [f"📅 HAFTE KA DIN-PLAN ({'CHALU' if on() else 'BAND'}) — har channel ka har din ka andaaz", ""]
    for i, dn in enumerate(DAYS):
        parts = []
        for b in BRANDS:
            name, _ = today_andaaz(b, datetime.date.today() + datetime.timedelta(days=(i - datetime.date.today().weekday()) % 7))
            extra = {0: " + GK", 2: " + purane naam", 4: " + pahadi shabd"}.get(i, "") if b == "pahadi" else ""
            parts.append(f"{SHORT.get(b, b)}: {name}{extra}")
        L.append(f"• {dn}: " + " | ".join(parts))
    L.append("\nRavivaar raat: har channel ki LAMBI video (pehle jaisa). Sab channel par roz (YouTube, Facebook, Instagram, Threads, "
             "Pinterest, Telegram) — YouTube par din mein max 6 upload (API seema), isliye 4 roz + 1 lambi theek hai.")
    L.append("Badalna: likhein jaise 'somvaar money: kahani' ya 'budhvaar pahadi: sawal' → dohri pushti. "
             "Poora band/chalu: 'din plan band' / 'din plan chalu' (dohri pushti).")
    return "\n".join(L)


def parse_change(t):
    """'somvaar money: kahani' -> (brand, weekday, (name, how)) ya None."""
    import re
    m = re.match(r"^\s*(\w+)\s+(\w+)\s*[:=\-]\s*(.+)$", t.strip().lower())
    if not m or m.group(1) not in DAY_KEYS:
        return None
    wd = DAY_KEYS.index(m.group(1))
    bk = next((k for k, v in BRANDS.items() if m.group(2) in (k, v["name"].lower().split()[0])), None)
    if not bk:
        return None
    want = m.group(3).strip()
    hit = next((v for k, v in ANDAAZ.items() if k in want or v[0].lower() in want), None)
    return bk, wd, (hit or (want[:40], want[:200]))


def apply_change(bk, wd, val):
    o = _over()
    o.setdefault(bk, {})[str(wd)] = list(val)
    state.put("day_plan_over", o)
    return f"✅ Pakka: {BRANDS[bk]['name']} — {DAYS[wd]} ka andaaz ab '{val[0]}'."
