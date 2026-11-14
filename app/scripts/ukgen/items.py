"""Docx blocks -> page items (h2/h3/p/ans/ul/table/faq/quiz). Internal hisse alag list mein (kuch gayab nahi)."""
import re
from clean import split_editor, unblueprint, fix_text, is_para_internal, table_kind, heading_internal, TOC_LINE, clean_heading, is_deva, heading_fix, PLACEHOLDER_CELL, INTERNAL_HARD
from model import DISTRICTS

FAQ_CTX = re.compile(r"faq|people also ask|\bpaa\b|sawal|sawaal|सवाल|aksar|questions|q&a|prashn|logon ne", re.I)
QUIZ_CTX = re.compile(r"quiz|mcq|abhyas", re.I)
QPFX = r"(?:Q\s*\d{0,3}\s*[.:)]|प्रश्न\s*\d{0,3}\s*[.:)]?|S\s*\d{1,3}\s*[.:)]|\d{1,3}\s*[.)])"
QA_INLINE = re.compile(r"^(?:%s)?\s*(?P<q>[^?]{6,220}\?)\s*(?:(?:A|Ans|Answer|Jawab|Uttar|उत्तर)\s*[.:)\-]\s*)?(?P<a>.{2,})$" % QPFX)
Q_ONLY = re.compile(r"^(?:%s)?\s*(?P<q>[^?]{6,220}\?)\s*$" % QPFX)
A_PFX = re.compile(r"^(?:A|Ans|Answer|Jawab|Uttar|उत्तर)\s*[.:)\-]\s*", re.I)
MCQ = re.compile(r"\(a\).{1,120}\(b\)|\(A\).{1,120}\(B\)")
MOD_END = re.compile(r"^\[?\s*module\s+\d+\s+(samaapt|samapt|khatam|samaptt)", re.I)
LI_CUE = re.compile(r"template|format|\bform\b|fields|khane|bharein|bharna|keywords?|search (phrases?|shabd|query|sawal)|"
                    r"log (ye|yeh)? ?bhi (search|khoj)|google (me|par)|kya jama|jama karna|sangrah karna", re.I)
LIST_STYLES = ("Compact", "List Paragraph", "List Bullet", "List Number")

def hnum(t):
    m = re.match(r"^(\d{1,3})(?:\.(\d{1,2}))?[.:)]?\s+\S", t)
    return (int(m.group(1)), int(m.group(2)) if m.group(2) else None) if m else (None, None)

class Builder:
    def __init__(self, dname=None, level_map=None):
        self.items, self.internal = [], []
        self.dname = dname
        self.level_map = level_map or {"Heading 2": 2, "Heading 3": 3, "Heading 4": 4, "Heading 5": 4}
        self.skip_level = None       # internal section chal raha ho to us heading level tak
        self.ctx = []                # (level, text)
        self.pending_q = None
        self.list_buf = []
        self.qa_mode = False         # 'Quick Q&A:' ke baad ki lines sawal-jawab hain
        self.nav = None              # zilon ki aapsi suchi wala hissa (level)
        self.nav_done = False
        self.skip_kind = None        # 'fix' / 'soft' / 'hard' - chhoda gaya hissa kis wajah se
        self.drop_li = False         # editor-line (':' par khatam) hati -> neeche ki suchi bhi editor ki
        self.mod_end = False         # '[Module N samaapt]' ke baad agle module ka parichay (page par galat jagah)

    def _flush_list(self):
        if self.list_buf:
            # v3.3.2 audit-3: bullet-suchi jiski har line 'Sawal? Jawab.' ho = sawal-jawab hi hai -> FAQ (pathak aur schema dono ke liye)
            ms = [QA_INLINE.match(x) for x in self.list_buf]
            if len(self.list_buf) >= 2 and all(m and len(m.group("q").split()) >= 3 and "?" not in m.group("a")
                                               and len(m.group("a").strip()) >= 2 for m in ms):
                buf, self.list_buf = self.list_buf, []
                for m in ms:
                    self._qa(m.group("q").strip(), A_PFX.sub("", m.group("a")).strip())
                return
            self.items.append(("ul", self.list_buf))
            self.list_buf = []

    def _flush_q(self):
        # v3.3.2: bina jawab ka akela sawal (PAA keyword-suchi) page par nahi - jawab ke bina pathak ke kaam ka nahi
        if self.pending_q:
            self.internal.append(("paa", self.pending_q))
            self.pending_q = None

    def in_faq(self):
        return any(FAQ_CTX.search(t) for _, t in self.ctx)

    def in_quiz(self):
        return any(QUIZ_CTX.search(t) for _, t in self.ctx)

    def heading(self, level, raw, why_internal=None):
        self._flush_list(); self._flush_q()
        self.qa_mode = False
        self.mod_end = False
        self.drop_li = False
        if self.nav is not None:
            if level <= self.nav:
                self.nav = None
            else:
                self.internal.append(("h", raw)); return
        if self.skip_level is not None:
            if level <= self.skip_level:
                self.skip_level = None
            else:
                self.internal.append(("h", raw)); return
        self.ctx = [(l, t) for l, t in self.ctx if l < level] + [(level, raw)]
        hit, act = heading_fix(raw)
        if hit:
            if act is None:
                self.skip_level = level; self.skip_kind = "fix"; self.internal.append(("h", raw)); return
            if act == "NAV":
                self.nav = level; self.internal.append(("h-nav", raw)); return
            if act == "":
                self.internal.append(("h-hide", raw)); return
            self.items.append(("h%d" % level, fix_text(act.format(D=self.dname or "Uttarakhand")), raw))
            return
        if why_internal or heading_internal(raw):
            self.skip_level = level
            self.skip_kind = "hard" if (why_internal or INTERNAL_HARD.search(raw)) else "soft"
            self.internal.append(("h", raw))
            return
        txt = clean_heading(raw, self.dname)
        if not txt:
            return
        self.items.append(("h%d" % level, txt, raw))

    def _nav_head(self):
        if not self.nav_done:
            self.nav_done = True
            self.items.append(("h2", "%s se Jude Uttarakhand ke Baaki Zile" % (self.dname or "Uttarakhand"), "nav"))

    def nav_table(self, rows):
        """Zilon ki suchi: sirf zila + mandal + 'rishta/pehchan' column, zile ka naam uske page ka link."""
        head = [c.lower() for c in rows[0]]
        zi = next((i for i, c in enumerate(head) if re.match(r"^(zila|jila)\b", c)), None)
        ri = next((i for i, c in enumerate(head) if re.search(r"rishta|sambandh|pehchan|kyun jodein|gateway", c)), None)
        mi = next((i for i, c in enumerate(head) if c.startswith("mandal") or c.startswith("kshetra")), None)
        if zi is None or ri is None:
            self.internal.append(("t:nav", rows)); return
        out = [["Zila"] + (["Mandal"] if mi is not None else []) + ["%s se rishta / pehchan" % (self.dname or "Uttarakhand")]]
        for r in rows[1:]:
            if max(zi, ri) >= len(r):
                continue
            nm, rel = r[zi].strip(), fix_text(re.sub(r"\s*\(Heading[^)]*\)", "", r[ri])).strip(" ✔")
            d = next((x for x in DISTRICTS if nm.lower().startswith(x[2].lower().split()[0]) and
                      (len(x[2].split()) == 1 or x[2].lower().split()[-1] in nm.lower() or nm.lower() == x[2].lower().split()[0])), None)
            if not d or d[2] == self.dname or not rel or re.match(r"^(ye|yeh) page|aap yahan", rel, re.I) or PLACEHOLDER_CELL.match(rel):
                continue
            rel = split_editor(rel)[0]
            if not rel:
                continue
            out.append(["https://sabhisaab.com/uttarakhand/%s" % d[1]] + ([r[mi]] if mi is not None and mi < len(r) else []) + [rel])
        if len(out) >= 4:
            self._nav_head(); self.items.append(("table", out))
        else:
            self.internal.append(("t:nav", rows))

    def para(self, raw, style="", is_li=False, bold=False):
        if self.skip_level is not None:
            # v3.3.2 audit-3: module khatam ka nishan = editor-hissa yahin khatam (pehle agle heading tak sab nigal jata tha,
            # jaise zameen-kanoon ki 'Zaroori suchna')
            if MOD_END.match(raw.strip()):
                self.internal.append(("p", raw)); self.skip_level = None; self.mod_end = True; return
            self.internal.append(("p", raw))
            if self.skip_kind in ("fix", "soft"):
                self._salvage_qa(raw)
            return
        if self.nav is not None and (self.pending_q or re.match(r"^\s*(Q|A|Ans|Jawab|Uttar|प्रश्न|उत्तर)\s*\d{0,3}\s*[.:)]", raw)):
            for line in [l.strip() for l in raw.split("\n") if l.strip()]:
                self._line(line, style, is_li, bold)
            return
        if self.nav is not None:
            # zilon ki suchi wale hisse ka paragraph: sirf zilon ke aapsi rishte wale vaakya (link/URL/13-zile wali line nahi)
            k = split_editor(fix_text(unblueprint(raw)))[0]
            ks = [x for x in re.split(r"(?<=[.!?])\s+", k) if x and not re.search(
                r"\b13 (zile|jile|zila)|neeche|ghoom sak|pages?\b|link|url|website|hub|google|seedha jawab|quick answer|"
                r"jaaniye|jaanein|suchi (di|hai)|garhwal ka zila hai|kumaon (mandal )?ka (ek )?zila hai", x, re.I)]
            if ks and self.dname and re.search(re.escape(self.dname.split()[0]), " ".join(ks), re.I):
                self._nav_head(); self.items.append(("p", " ".join(ks)))
            if " ".join(ks) != raw:
                self.internal.append(("p-nav", raw))
            return
        for line in [l.strip() for l in raw.split("\n") if l.strip()]:
            self._line(line, style, is_li, bold)

    def _line(self, raw, style, is_li, bold):
        # v3.3.2 audit-3: editor ki line ('Kahawat likhne ka format (template):') hati to uske neeche ki suchi bhi usi ki (form ke khane)
        if self.drop_li:
            mq = QA_INLINE.match(raw.strip())
            r0 = raw.strip()
            if ((is_li or style in LIST_STYLES) and not (mq and len(mq.group("a").split()) >= 2 and "?" not in mq.group("a"))
                    and (re.match(r"^[“\"]", r0) or len(r0.split()) <= 8 or re.search(r"\b(likhein|bharein|likhwa|jodein)\b", r0, re.I)
                         or re.match(r"^[^:]{1,40}:\s*\([^)]*\)\.?$", r0))):
                self.internal.append(("li-after-drop", raw)); return
            self.drop_li = False
        if is_para_internal(raw):
            self._flush_q(); self.internal.append(("p", raw))
            if not is_li and raw.rstrip().endswith(":") and LI_CUE.search(raw):
                self._flush_list(); self.drop_li = True
            return
        t = fix_text(unblueprint(raw))
        if not t:
            return
        # v3.3.2: ek paragraph mein '1. Sawal? Jawab. 2. Sawal? Jawab.' - har sawal alag FAQ (pehle poora paragraph ek blob tha)
        if len(re.findall(r"(?:^|\s)\d{1,2}\.\s+[^?]{4,160}\?", t)) >= 2:
            self._flush_list(); self._flush_q()
            for part in re.split(r"\s+(?=\d{1,2}\.\s+[^?]{4,160}\?)", t):
                part = re.sub(r"^\d{1,2}\.\s+", "", part.strip())
                m = QA_INLINE.match(part) if part else None
                if m and len(m.group("q").split()) >= 3 and "?" not in m.group("a"):
                    self._qa(m.group("q"), A_PFX.sub("", m.group("a")))
                elif part and "?" not in part:
                    k = split_editor(part)[0]
                    if k:
                        self.items.append(("p", k))
            return
        mq = re.match(r"^(?:Quick|Chhote|Turant)?\s*(?:Q\s*&\s*A|Q&amp;A|sawal-jawab)\s*:\s*(.*)$", t, re.I)
        if mq:
            self._flush_list(); self._flush_q()
            rest = mq.group(1).strip()
            if not rest:
                self.qa_mode = True; return
            for part in re.split(r"(?:^|\s+)-\s+(?=\S)", rest):
                part = part.strip()
                m = QA_INLINE.match(part) if part else None
                if m and len(m.group("q").split()) >= 3:
                    self._qa(m.group("q"), A_PFX.sub("", m.group("a")))
                elif part:
                    k = split_editor(part)[0]
                    if k:
                        self.items.append(("p", k))
            return
        t, ed = split_editor(t)
        if ed:
            self.internal.append(("p-sent", " ".join(ed)))
        if not t or len(t) < 3:
            if ed and not is_li and style not in LIST_STYLES and raw.rstrip().endswith(":") and LI_CUE.search(raw):
                self._flush_list(); self.drop_li = True
            return
        faq = self.in_faq() or self.qa_mode
        # jawab jo pichhle sawal ka hai
        if self.pending_q:
            q = self.pending_q
            self.pending_q = None
            a = A_PFX.sub("", t)
            if not Q_ONLY.match(t) and len(a) > 1:
                self._flush_list()
                self._qa(q, a)
                return
            self.internal.append(("paa", q))
        strong_q = bool(re.match(r"^(Q\s*\d{0,3}\s*[.:)]|प्रश्न)", t))
        if faq or strong_q or self.in_quiz():
            if MCQ.search(t) or re.search(r"(Uttar|Jawab)\s*:\s*\(?[A-Da-d]\)?\s*$", t):
                self._flush_list(); self.items.append(("quiz", re.sub(r"^(?:%s)\s*" % QPFX, "", t))); return
            m = QA_INLINE.match(t)
            if m and len(m.group("q").split()) >= 3:
                self._flush_list(); self._qa(m.group("q"), A_PFX.sub("", m.group("a"))); return
            m = Q_ONLY.match(t)
            if m and len(m.group("q").split()) >= 3:
                self._flush_list(); self.pending_q = m.group("q"); return
        if re.match(r"^(Seedha Jawab|सीधा जवाब|Quick Answer|Seedha jawab)", t, re.I):
            self._flush_list(); self.items.append(("ans", t)); return
        # v3.3.2 (owner 14 Nov: 'FAQ aur ho sakte hain'): body mein likha khud-mein-poora sawal-jawab ('Block kya karta hai? Vikas Khand ...')
        # bhi sawal-jawab hai. Sirf wahi jo akela padhne par samajh aaye (shuru mein 'ye/is/kyun' jaisa ishara-shabd nahi).
        m = QA_INLINE.match(t)
        if (m and not is_li and style not in LIST_STYLES and 4 <= len(m.group("q").split()) <= 16 and len(m.group("a").split()) >= 8
                and not re.match(r"^(ye|yeh|is|iska|iski|iske|isse|isme|kyun|kyon|kyu|to|aur|par|lekin|magar|kya aap|aap|hum|tab|phir|sach|asli sawal)\b",
                                 m.group("q").strip(), re.I)
                and not re.search(r"\b(aap|aapka|aapke|aapki|hum|hamara)\b", m.group("q"), re.I)):
            self._flush_list(); self._qa(m.group("q"), m.group("a")); return
        if is_li or style in LIST_STYLES:
            self.list_buf.append(t); return
        self._flush_list()
        self.items.append(("pb" if (bold and t.endswith(":") and len(t) < 140) else "p", t))

    def _salvage_qa(self, raw):
        """Editor-hisse ke andar bhi jo pakka sawal-jawab hai (jawab ke saath) wo pathak ka hai -> FAQ.
        Page/heading/site/form wale sawal-jawab nahi."""
        for line in [l.strip() for l in raw.split("\n") if l.strip()]:
            t = fix_text(unblueprint(line))
            m = QA_INLINE.match(t) if t else None
            if not m:
                continue
            q, a = m.group("q").strip(), A_PFX.sub("", m.group("a")).strip()
            if len(q.split()) < 3 or len(a.split()) < 2 or "?" in a:
                continue
            if re.search(r"\b(page|pages|heading|site|website|form|module|blueprint|hum|hamare|humne|main|mera|meri|mujhe|bhej)\b", q + " " + a, re.I):
                continue
            self.internal.append(("salvage", line))
            self._qa(q, a)

    def _qa(self, q, a):
        # PAA ki sawal-suchi ('X? Y? (Dhanaulti hote)') ya sirf '(IMD link)' jaisa jawab = jawab nahi
        if "?" in a or re.match(r"^\s*\([^)]{0,60}\)\s*\.?$", a) or len(re.sub(r"[^A-Za-z0-9\u0900-\u097F]", "", a)) < 1:
            self.internal.append(("paa", q + " " + a)); return
        a, ed = split_editor(fix_text(unblueprint(a)), lenient=True)     # jawab chhota ho sakta hai ('Almora se.')
        if ed:
            self.internal.append(("p-sent", " ".join(ed)))
        if not a:
            self.internal.append(("p", q)); return
        q = re.sub(r"^(?:%s)\s*" % QPFX, "", q).strip()
        q = re.sub(r"\s*\((?:Headings?|Module)\s+[\d.]+[A-Za-z]?(?:\s*(?:,|aur|se)\s*[\d.]+)*\)", "", q)   # sawal mein document ka ishara nahi
        self.items.append(("faq", fix_text(q), fix_text(a)))

    def table(self, rows):
        self._flush_list(); self._flush_q(); self.drop_li = False
        if self.skip_level is not None:
            self.internal.append(("t", rows)); return
        if self.nav is not None:
            self.nav_table(rows); return
        k = table_kind(rows)
        if k == "placeholder":
            rows2 = salvage(rows)
            if rows2:
                self.internal.append(("t:placeholder-part", rows))
                rows, k = rows2, "public"
        if k != "public":
            self.internal.append(("t:" + k, rows)); return
        URLC = r"^(https?://(www\.)?sabhisaab\.com)?/uttarakhand/([a-z-]+)/?$"
        w0 = max(len(r) for r in rows)
        ucols = [j for j in range(w0) if sum(1 for r in rows[1:] if j < len(r) and re.match(URLC, r[j].strip())) >= max(3, (len(rows) - 1) // 2)]
        if ucols:
            # zile ke page wali URL column hatao, naam wale khane ko us page ka link banao (baaki asli jaankari rahe)
            j = ucols[0]
            new = [[c for k, c in enumerate(rows[0]) if k != j]]
            for r in rows[1:]:
                m = re.match(URLC, r[j].strip()) if j < len(r) else None
                rr = [c for k, c in enumerate(r) if k != j]
                if m and rr:
                    rr[0] = "https://sabhisaab.com/uttarakhand/%s" % m.group(3)
                new.append(rr)
            if len(new[0]) < 2 or sum(1 for r in new[1:] for c in r[1:] if c.strip()) < 3:
                self.internal.append(("t:nav", rows)); return
            self.internal.append(("t:nav-col", rows[0]))
            rows = new
        HFIX = [(r"^(blueprint|mool sandarbh-suchi) ka (daava|dawa|vishay)$", r"Aam \2"), (r"^hamara faisla$", "Sahi sandarbh"), (r"^hamari sthiti$", "Sachchai"),
                (r"^arth \((blueprint|mool sandarbh-suchi) ke anusar\)$", "Arth"), (r"^(blueprint|mool sandarbh-suchi) ke anusar lagbhag$", "Lagbhag maap")]
        hdr = []
        for c in rows[0]:
            for a, b in HFIX:
                c = re.sub(a, b, c.strip(), flags=re.I)
            hdr.append(c)
        rows = [hdr] + rows[1:]
        rows = [[("" if re.match(r"^\[[^\]]*\]$", c.strip()) else split_editor(fix_text(unblueprint(c)), lenient=True)[0]) for c in r] for r in rows]
        w = max(len(r) for r in rows)
        rows = [r + [""] * (w - len(r)) for r in rows]
        if w >= 2:                                   # khaali (sirf pehla khana bhara) row page par bekaar
            PH = lambda c: (not c.strip()) or PLACEHOLDER_CELL.match(c.strip()) or re.match(
                r"^(_+|\(?jama karna hai\)?|source nahi|pakki nahi|\(?bharna hai\)?|\(?bharein\)?|\(?khali\)?)$", c.strip(), re.I)
            rows = [rows[0]] + [r for r in rows[1:] if sum(1 for c in r[1:] if not PH(c)) >= max(1, (w - 1 + 1) // 2)]
            rows = [rows[0]] + [[("—" if (k and PH(c)) else c) for k, c in enumerate(r)] for r in rows[1:]]
        if len(rows) < 2:
            self.internal.append(("t:empty", rows)); return
        self.items.append(("table", rows))

    def done(self):
        self._flush_list(); self._flush_q()
        return self.items

def salvage(rows):
    """Aadhi bhari table: khaali column/row hatao; 3+ bhari row aur 2+ column bache to wahi page par (asli aankde na khoyein)."""
    if len(rows) < 3:
        return None
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    filled = lambda c: bool(c.strip()) and not PLACEHOLDER_CELL.match(c.strip()) and not re.match(r"^_+$|^\(.*(bhar|jama|verify|khali).*\)$", c.strip(), re.I)
    cols = [0] + [j for j in range(1, w) if sum(1 for r in rows[1:] if filled(r[j])) >= max(2, (len(rows) - 1) * 0.6)]
    if len(cols) < 2:
        return None
    if any(re.search(r"source|tithi|last verified|last checked|anumati|contact|sampark", rows[0][j], re.I) for j in cols[1:]) and len(cols) == 2:
        return None
    out = [[rows[0][j] for j in cols]] + [[r[j] for j in cols] for r in rows[1:] if all(filled(r[j]) for j in cols)]
    return out if len(out) >= 4 else None

def feed(builder, blocks, intro=False):
    for x in blocks:
        if x["k"] == "t":
            builder.table(x["rows"]); continue
        st = x["s"]
        if st in builder.level_map:
            builder.heading(builder.level_map[st], x["t"]); continue
        if intro and TOC_LINE.match(x["t"].strip()) and len(x["t"]) < 130:
            builder.internal.append(("toc", x["t"])); continue
        if st in ("Source Code",):
            builder.internal.append(("code", x["t"])); continue
        if st in ("Subtitle",) and re.search(r"sabhisaab\.com", x["t"], re.I):
            builder.internal.append(("p", x["t"])); continue
        builder.para(x["t"], st, x.get("li"), x.get("b"))
