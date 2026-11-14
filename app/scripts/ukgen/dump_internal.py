"""v3.3 (owner 14 Nov: 'faltu delete, kaam ka rakho'): site par na jaane wale hisse mein se sirf kaam ki baatein
(kya pakka karna hai, kaunsa data jama karna hai, kya sudhara) ek file mein; keyword-suchi, SEO/Pinterest pack, TOC,
JSON-LD dhanche, purane URL ki table jaisa faltu hissa hamesha ke liye chhoda (ginti neeche)."""
import os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen import build_pages
from model import DISTRICTS
NAME = {d[1]: d[2] for d in DISTRICTS}; NAME["uttarakhand"] = "Uttarakhand Hub"
KEEP_MOD = re.compile(r"verify|checklist|sudhar|bharne|jaan-boojh|corrections|farak", re.I)
MISSING = re.compile(r"mere paas|nahi likh|pushti nahi|verify nahi|nahi mila|source nahi|pakka (naam|record)|abhi tayyar nahi|jama kar", re.I)

def words(x):
    return len(str(x).split())

def main(out):
    pages, internal, _ = build_pages()
    keep, gone = collections.Counter(), collections.Counter()
    md = ["# Uttarakhand pages: kaam ki baatein (jo site par nahi gaya)", "",
          "Ye sirf aapke/aage ke kaam ke liye hai - site par nahi jaata. Isme: (1) kya pakka karna hai (verify list),",
          "(2) kaunsa data abhi nahi hai aur jama karna hai, (3) khaali table jinhe bharna hai, (4) jo galti sudhari gayi,",
          "(5) wo sawal jo logon ne poochhe par jinka jawab file mein nahi tha (naye FAQ ke idea).",
          "Keyword-suchi, SEO/Pinterest pack, Word ka TOC, JSON-LD dhancha, purane URL ki table aur publish-niyam faltu the - hata diye.", ""]
    have = collections.defaultdict(set)              # jo sawal pehle se kisi page par FAQ hai, wo 'idea' mein dobara nahi
    for pg in pages:
        for it in pg["items"]:
            if it[0] == "faq":
                have[pg.get("district") or "uttarakhand"].add(re.sub(r"[^a-z0-9]", "", it[1].lower()))
    for k, lst in internal.items():
        sec = []
        ideas = []
        for e in lst:
            if "blocks" in e:
                if KEEP_MOD.search(e["module"]):
                    sec.append("### " + e["module"])
                    for x in e["blocks"]:
                        t = x["t"] if x["k"] == "p" else " | ".join(" / ".join(r) for r in [x["rows"][0]]) + " ..."
                        sec.append("- " + t); keep["verify list"] += words(t)
                else:
                    gone["editor/SEO section"] += sum(words(x["t"]) if x["k"] == "p" else sum(words(c) for r in x["rows"] for c in r)
                                                      for x in e["blocks"])
                continue
            kind, val = e["item"][0], e["item"][1]
            n = sum(words(c) for r in val for c in r) if isinstance(val, list) else words(val)
            if kind == "t:placeholder":
                sec.append("- [%s] Bharni hai: %s" % (e.get("page"), " | ".join(val[0])))
                keep["khaali table"] += n
            elif kind == "area-fix":
                sec.append("- Sudhara: " + val); keep["sudhaar"] += n
            elif kind in ("p-sent", "p") and MISSING.search(str(val)):
                sec.append("- [%s] Data nahi tha: %s" % (e.get("page"), str(val)[:300])); keep["missing data"] += n
            elif kind == "paa" or (kind == "p" and str(val).strip().endswith("?") and words(val) <= 20):
                # v3.3.2 audit-3: bina jawab ke sawal page par nahi (patla content), par owner/Claude ke liye FAQ ke idea - rakho
                q = re.sub(r"^\s*(\d+[.)]|[-•*]|Q\d*[.:])\s*", "", str(val)).strip()
                nq = re.sub(r"[^a-z0-9]", "", q.lower())
                if nq and nq not in have[k] and q not in ideas:
                    ideas.append(q); keep["FAQ ke idea (jawab likhna baaki)"] += n
                else:
                    gone["bina jawab ke sawal (pehle se FAQ / dohraav)"] += n
            elif kind in ("p-nav", "h-nav", "h-hide", "t:nav-col", "t:placeholder-part", "t:empty"):
                gone[{"p-nav": "zilon ki suchi ke link-niyam", "h-nav": "navigation heading", "h-hide": "lekhak-wali heading",
                      "t:nav-col": "URL column", "t:placeholder-part": "aadhi-bhari table ke khaali khane", "t:empty": "khaali table"}[kind]] += n
            else:
                gone[{"p": "editor/SEO line", "p-sent": "editor/meta vaakya", "h": "editor heading", "toc": "Word TOC",
                      "t:nav": "purane URL table", "t:internal": "SEO table", "t": "editor table", "code": "JSON-LD",
                      "t:placeholder": "khaali table"}.get(kind, kind)] += n
        if ideas:
            sec += ["", "### Sawal jinka jawab abhi page par nahi (FAQ ke idea - jawab pakke srot se likh kar hi jodein)"] + ["- " + q for q in ideas]
        if sec:
            md += ["", "## " + NAME.get(k, k), ""] + sec
    md[5:5] = ["Rakha: " + ", ".join("%s %d shabd" % kv for kv in keep.most_common()),
               "Hamesha ke liye hataya (faltu): " + ", ".join("%s %d" % kv for kv in gone.most_common()) +
               " | kul %d shabd" % sum(gone.values()), ""]
    open(out, "w", encoding="utf-8").write("\n".join(md))
    return keep, gone

if __name__ == "__main__":
    k, g = main(sys.argv[1]); print(dict(k), sum(k.values())); print(dict(g), sum(g.values()))
