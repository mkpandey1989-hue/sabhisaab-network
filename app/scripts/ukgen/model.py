"""Docx -> module model. Har source block ka hisaab rakhta hai (kuch bhi chupchap gayab nahi)."""
import json, re, collections

DISTRICTS = [  # file, slug, Naam, mandal, boli
    ("Dehradun_Page_merged.docx", "dehradun", "Dehradun", "Garhwal", "Garhwali"),
    ("Nainital Page_merged.docx", "nainital", "Nainital", "Kumaon", "Kumaoni"),
    ("Haridwar Page_merged.docx", "haridwar", "Haridwar", "Garhwal", "Garhwali"),
    ("rudraprayag page_merged.docx", "rudraprayag", "Rudraprayag", "Garhwal", "Garhwali"),
    ("Chamoli page_merged.docx", "chamoli", "Chamoli", "Garhwal", "Garhwali"),
    ("Uttarkashi_merged.docx", "uttarkashi", "Uttarkashi", "Garhwal", "Garhwali"),
    ("Almora page_merged.docx", "almora", "Almora", "Kumaon", "Kumaoni"),
    ("tehri garhwal page_merged.docx", "tehri-garhwal", "Tehri Garhwal", "Garhwal", "Garhwali"),
    ("Pauri Garhwal page_merged.docx", "pauri-garhwal", "Pauri Garhwal", "Garhwal", "Garhwali"),
    ("pithoragarh page_merged.docx", "pithoragarh", "Pithoragarh", "Kumaon", "Kumaoni"),
    ("Udham Singh Nagar page_merged.docx", "udham-singh-nagar", "Udham Singh Nagar", "Kumaon", "Kumaoni"),
    ("Bageshwar_Page_merged.docx", "bageshwar", "Bageshwar", "Kumaon", "Kumaoni"),
    ("champawat_page.docx", "champawat", "Champawat", "Kumaon", "Kumaoni"),
]
HUB_FILE = "Uttarakhand_Mega_Hub_Page_Complete_merged.docx"

# module title -> theme (kram zaroori hai)
THEME_RX = [
    ("internal", r"kaise padhein|publish|pahle ye padhein|padhne se pehle|page setup|is file|vishay-suchi|table of contents|"
                 r"front matter|editor|ready-to-paste|technical seo|implementation pack|on-page seo|verify aur bharne|"
                 r"pre-publish|schema \(json|long-tail keyword list|sudhar-log|publish se pehle"),
    ("sources", r"sources aur sandarbh"),
    ("main", r"search booster|high-intent|himachal connect|serp pack|book end"),
    ("addon", r"people also ask|\(vistaar\)|^bonus:|part 3: ready|addendum|extra module|appendix a: on-page"),
    ("bhavishya", r"bhavishya|future"),
    ("transport", r"transport|yatayat|pahunch|hawai, rail"),
    ("aadhunik", r"aadhunik|adhunik|modern lifestyle"),
    ("career", r"career|competitive|gk, pariksha"),
    ("sarkari", r"portal|sarkari sew|nagrik sev"),
    ("vaidya", r"vaidya|prasav"),
    ("hyperlocal", r"hyper-local|garh, smarak"),
    ("shabd", r"vocabulary|shabd|kahawat|kahavat"),
    ("buzurg", r"buzurg|paramparik gyan"),
    ("prasiddh", r"sarkari yojana, khel"),
    ("economy", r"economy|arthvyavastha|network, bijli"),
    ("tourism", r"tourism|paryatan|ghumne"),
    ("food", r"gastronomy|\bkhana|khaana|rasoi|swad|\bfood"),
    ("land", r"\bland\b|zameen"),
    ("history", r"spirituality|itihas|adhyatm|dharm|aastha"),
    ("culture", r"\bculture|sanskriti|aabadi, samaj"),
    ("climate", r"climate|mausam"),
    ("geo", r"geography|bhugol"),
    ("identity", r"identity|pehchan|pehchaan"),
]

def theme_of(title):
    t = title.lower()
    for k, rx in THEME_RX:
        if re.search(rx, t):
            return k
    return None

def load_blocks(path="blocks.json"):
    return json.load(open(path))

def split_modules(blocks):
    """H1 (aur Title) se module. Pehle H1 se pehle ka content 'intro'."""
    mods = [{"title": "__intro__", "blocks": []}]
    for x in blocks:
        if x["k"] == "p" and x["s"] in ("Heading 1", "Title"):
            mods.append({"title": x["t"].strip(), "blocks": []})
        else:
            mods[-1]["blocks"].append(x)
    return [m for m in mods if m["blocks"] or m["title"] != "__intro__"]

def assign_themes(mods):
    """Har module ko theme. addon -> pichhle module ki theme. Pehle 'MODULE' se pehle = intro (internal chhod kar)."""
    prev = "identity"
    out = []
    seen_module = False
    for i, m in enumerate(mods):
        t = m["title"]
        if re.search(r"\bmodule\b", t, re.I):
            seen_module = True
        th = theme_of(t) if t != "__intro__" else "intro"
        if not seen_module and th != "internal":
            th = "intro"
        if th is None:
            # zile ka naam wala title (pehla H1) = intro
            th = "intro" if not re.search(r"module", t, re.I) else prev
        if th == "addon":
            tl = t.lower()
            if "addendum" in tl or "extra module" in tl:
                th = "main"
            elif "part 3" in tl:
                th = "land"
            else:
                th = prev
        if th not in ("internal", "intro", "sources", "main"):
            prev = th
        out.append((th, m))
    return out
