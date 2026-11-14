"""v3.3.2 audit-5 (14 Nov shaam, owner: "sarkari srot + jo pending hai sab clear, kuch miss mat karna").

Do kaam:
1) CENSUS: Census 2011 (Primary Census Abstract, antim aankde) se mile tathya. Jaanch: 13 zilon ka kshetrafal jodne par
   53,483 varg km = rajya ka kul kshetrafal (sab sahi); aabadi/ling-anupat/saksharta censusindia ke PCA aankde.
   Page par jahan purana/aarambhik (provisional) ya galat aankda tha, ya 'lagbhag 75% se 76%' jaisa gol-mol likha tha,
   wahan antim aankda. (Tehri ka '3,796 varg km (Census 2011)' galat tha - Census 2011 mein 3,642; 4,085 = Census 2001.)
2) EDITOR/SEO LINE: Word file mein lekhak ke liye likhi baatein jo ab bhi page par dikh rahi thin ('snippet ke liye',
   'Passage ranking ke liye', 'Aakhri jaanch: ____', 'low-competition', 'backlink', 'mere dwara banaye', 'quiz.html file',
   'Kya likhein' wali khaali dhancha-table, 'aap survey karke bharein') - pathak ke kaam ki nahi; Google ise 'banaya hua
   / adhoora' maanta hai. Hatayi ya pathak ki bhasha mein badli. Asli jaankari (tathya, salah) kahin nahi hati.
"""
import re

# (slug-shuruaat ya '*', regex, badal) - har string par (para, suchi, table ke khane, FAQ, heading)
SUBS = [
    # ---- 1) Census 2011 ----
    ("tehri-garhwal", r"Lagbhag 3,796 sq km \(Census figure\)\. Kuch sources 4,080 sq km batate hain",
     "3,642 sq km (Census 2011; 2001 ki Census mein 4,085 sq km)"),
    ("tehri-garhwal", r"Iska kshetrafal lagbhag 3,796 varg km \(Census\) maana jata hai, jabki kuch sources 4,080 varg km bhi likhte hain\.",
     "Census 2011 ke anusar iska kshetrafal 3,642 varg km hai (2001 ki Census mein 4,085 varg km tha, isliye purane sroton mein bada aankda milta hai)."),
    ("tehri-garhwal", r"Kshetrafal: 3,796 varg km \(Census 2011 ke anusar\)\. 4,080 varg km wala aankda bhi online milta hai\.",
     "Kshetrafal: 3,642 varg km (Census 2011). 4,085 varg km wala aankda 2001 ki Census ka hai."),
    ("tehri-garhwal", r"Census 2011 ke anusar lagbhag 3,796 varg km; kuch sources 4,080 varg km bhi likhte hain \(purane-naye maap ka farak\)",
     "Census 2011 ke anusar 3,642 varg km (2001 ki Census mein 4,085 varg km tha)"),
    ("tehri-garhwal", r"\b3,796\b", "3,642"),
    ("tehri-garhwal", r"[Ll]agbhag 3,640 sq km", "3,642 sq km"),
    ("tehri-garhwal", r"\b3,640\b", "3,642"),
    ("tehri-garhwal", r"1,078( mahilayen / 1,000 purush)? \(kuch sources 1,077\)", r"1,077\1"),
    ("tehri-garhwal", r"Lagbhag 75% se 76% \(source ke hisab se(?: alag-alag)?\)", "76.36%"),
    ("tehri-garhwal", r"\b1,078(?= mahila)", "1,077"),
    ("almora", r"Zile ki saksharta dar lagbhag 81% hai \(aankde me thoda antar ho sakta hai; pushti karein\)\.",
     "Census 2011 ke anusar zile ki saksharta dar 80.47% thi."),
    ("almora", r"Zile ka kshetrafal lagbhag 3,082 vargkm hai \(Wikipedia\)\.", "Census 2011 ke anusar zile ka kshetrafal 3,144 varg km hai."),
    ("almora", r"purush tha \(Wikipedia\)", "purush tha (Census 2011)"),
    ("almora", r"Kshetrafal lagbhag 3,082 vargkm", "Kshetrafal 3,144 vargkm (Census 2011)"),
    ("almora", r"^lagbhag 3,082 vargkm$", "3,144 vargkm (Census 2011)"),
    ("pithoragarh", r"Saksharta dar Lagbhag 83% \(kuch sources me 82\.93%\)",
     "Saksharta dar 82.25% (Census 2011 ka antim aankda; 82.93% shuruaati aankda tha)"),
    ("pithoragarh", r"Saksharta dar lagbhag 83% thi\.", "Saksharta dar 82.25% thi (Census 2011)."),
    ("pithoragarh", r"^Lagbhag 83% \(kuch sources me 82\.93%\)$", "82.25% (Census 2011 ka antim aankda; 82.93% shuruaati aankda tha)"),
    ("dehradun", r"\(Census 2011 data portal\); kuch sources me 85\.24%", "(Census 2011 ka antim aankda; 85.24% shuruaati aankda tha)"),
    ("dehradun", r"Saksharta Lagbhag 84-85% \(alag sources me thoda farak\)", "Saksharta 84.25% (Census 2011)"),
    ("dehradun", r"^Lagbhag 84-85% \(alag sources me thoda farak\)$", "84.25% (Census 2011)"),
    ("dehradun", r"[Ll]agbhag 84-85%", "84.25%"),
    ("rudraprayag", r"Literacy lagbhag 81% ke aas-paas hai", "Census 2011 ke anusar saksharta 81.30% thi"),
    ("pauri-garhwal", r"lagbhag 5,230 se 5,329 varg kilometre \(alag-alag sarkari strot me thoda fark\)", "5,329 varg kilometre (Census 2011)"),
    # ---- Cantonment: Lok Sabha uttar (eparlib AU234) ki desh-bhar ki chhavni suchi mein Uttarakhand ki 9: Almora, Chakrata, Clement
    #      Town, Dehradun, Landour, Lansdowne, Nainital, Ranikhet, Roorkee. Page 'Nainital mein koi cantonment nahi' likh raha tha - galat.
    ("nainital", r"Nainital zile me koi Cantonment Board \(Chhavni Parishad\) nahi hai; najdeeki cantonment Ranikhet \(Almora zila\) me hai\.",
     "Nainital shahar mein Nainital Cantonment Board (Chhavni Parishad) hai, jo Raksha Mantralaya ke adheen hai; Kumaon Regiment ka Regimental Centre Ranikhet (Almora zila) mein hai."),
    ("nainital", r"Nainital zile me koi Cantonment nahi hai \(([^)]*)\)\. Par yahan", r"Nainital shahar mein Nainital Cantonment Board hai (\1). Yahan"),
    ("nainital", r"^Nahi\. Par angrezi kaal ki kai imaratein hain", "Haan, Nainital shahar mein Nainital Cantonment Board hai. Saath hi angrezi kaal ki kai imaratein hain"),
    ("almora", r"aur Ranikhet Cantonment Board se prashasit hota hai\.", "aur Ranikhet aur Almora shahar ke chhavni kshetra apne-apne Cantonment Board se prashasit hote hain."),
    # Pithoragarh Nagar Nigam: 23 Jan 2025 ko pehla chunav (40 ward), mayor Kalpana Deolal (BJP) - page 'pushti karein' likh raha tha
    ("pithoragarh-zila-prashasan", r"Pithoragarh shehar zile ka sabse bada nagar nikay hai aur yahan Nagar Palika Parishad \(Nagar Palika\) vyavastha rahi hai\. \(Kya Pithoragarh ko Nagar Nigam ka darja mil gaya hai, ye abhi Shahri Vikas Vibhag ki taza notification se pushti karein\.\)",
     "Pithoragarh shehar zile ka sabse bada nagar nikay hai. Pehle yahan Nagar Palika Parishad thi; ab Pithoragarh Nagar Nigam (Municipal Corporation) hai, jiska pehla chunav 23 January 2025 ko hua (40 ward). Pehli mayor Kalpana Deolal (BJP) chuni gayin."),
    # Rajya mein ab 11 Nagar Nigam (2024-25 ke naye: Rishikesh, Kotdwar, Srinagar, Almora, Pithoragarh) - purana '6' hata
    ("*", r"Uttarakhand me 6 Nagar Nigam hain \(Dehradun, Haridwar, Haldwani-Kathgodam, Kashipur, Rudrapur aur Roorkee\), jisme Haridwar aur Roorkee dono isi jile me hain\.",
     "Uttarakhand mein ab 11 Nagar Nigam hain (Dehradun, Rishikesh, Haridwar, Roorkee, Haldwani-Kathgodam, Kashipur, Rudrapur, Kotdwar, Srinagar, Almora aur Pithoragarh); inmein Haridwar aur Roorkee dono isi zile mein hain."),
    ("*", r"Uttarakhand me 2016-17 ke aas-paas 6 Nagar Nigam the \(Dehradun, Haridwar, Haldwani, Kashipur, Rudrapur, Roorkee\), aur sabhi zile ke pahadi hisse me chhote nagar nikay hi hain\.",
     "Uttarakhand mein ab 11 Nagar Nigam hain (Dehradun, Rishikesh, Haridwar, Roorkee, Haldwani, Kashipur, Rudrapur, Kotdwar, Srinagar, Almora aur Pithoragarh); Uttarkashi zile mein koi Nagar Nigam nahi, yahan chhote nagar nikay hi hain."),
    # Hub ki zila-table: Census 2011 kshetrafal (13 ka jod = 53,483)
    ("uttarakhand", r"^1,781 sq km$", "1,766 sq km"),
    ("uttarakhand", r"^3,422 sq km$", "4,251 sq km"),
    ("uttarakhand", r"^3,796 sq km$", "3,642 sq km"),
    ("*", r"har jawab chhota aur seedha, taaki voice assistant aur \"People Also Ask\" me uth sake\.", "har jawab chhota aur seedha."),
    # Badrinath kapat 16 Nov 2026 raat - page 32 din mein live honge; 'band honge' 2 din mein purana ho jata. Tithi-neutral roop.
    ("*", r"23 April 2026 ko khule; 16 November 2026 ko raat 9:37 baje band honge\.?", "2026 mein kapat 23 April ko khule aur band hone ki tithi 16 November 2026, raat 9:37 baje tay thi."),
    ("*", r"Badrinath ke kapat kab band honge \(2026\)\?", "2026 mein Badrinath ke kapat kab band hue?"),
    ("*", r"^Kapat band honge: 16 November 2026", "Kapat band hone ki tithi: 16 November 2026"),
    ("*", r"Kapat band honge: 16 November 2026", "Kapat band hone ki tithi: 16 November 2026"),
    ("*", r"Badrinath ke kapat 16 November 2026 ko raat lagbhag 9:37 baje band hone ki ghoshna hai", "Badrinath ke kapat band hone ki tithi 16 November 2026, raat lagbhag 9:37 baje tay thi"),
    ("*", r"Badrinath ke kapat kab khule aur kab band honge \(2026\)\?", "2026 mein Badrinath ke kapat kab khule aur kab band hue?"),
    # ---- 2) editor / SEO line ----
    ("*", r"\s*Aakhri jaanch: _{2,}(?: \(tithi bharein\))?", ""),
    ("*", r"\s*\((?:snippet|Passage ranking) ke liye\)", ""),
    ("*", r"Is table ke upar kya likhein:?\s*\"([^\"]+)\"", r"\1"),
    ("*", r"\s*\(People Also Ask\)", ""),
    ("*", r"\bPeople Also Ask:\s*", "Log ye bhi poochhte hain: "),
    ("*", r"Neeche kuch aur “People Also Ask” aur low-competition phrases jo is module se jude hain\.", "Neeche kuch aur aksar poochhe jaane wale sawal hain."),
    ("*", r"\s*Har jawab chhota rakha gaya hai taaki \"People Also Ask\" aur AI-answers me aa sake\.", ""),
    ("*", r"Long-Tail FAQ", "Aur Sawal-Jawab"),
    ("*", r"Part B: Tourism Long-Tail \(Ghumne aur Yatra\)", "Ghumne aur Yatra ke Sawal"),
    ("*", r"Sample Table ([A-C]): ", ""),
    ("*", r"\s*\(Zero-Competition Vocabulary\)", ""),
    ("*", r"Master Cheat-Sheet", "Ek Nazar Wali Table"),
    ("*", r"\s*\(Cheat-Sheet\)", ""),
    ("*", r"Page par ise interactive quiz ke roop me lagane ke liye har sawal ke vikalp aur sahi uttar neeche diye gaye hain\. Quiz fir bhi reader ko rokne me madad karta hai\.",
     "Har sawal ke vikalp aur sahi uttar neeche diye gaye hain."),
    ("*", r"\s*Ise PDF/Word ke roop me download ke liye bhi diya ja sakta hai\.", ""),
    ("*", r"\s*Download kaise banayein: Is poori table ko ek PDF/Excel “[^”]+” ke roop me dein\. Log ise download karenge aur share karenge; ye apne aap me backlink aur brand-recall ka strot banta hai\.", ""),
    ("*", r"taaki dono tarah ke search ka traffic aapko mile", "taaki dono ki jaankari ek jagah mile"),
    ("*", r"Ye aise searches hain jinme log seedha kaam ki jaankari dhoondhte hain, isliye ye traffic aur bharosa dono deta hai\.",
     "Ye wo kaam hain jinke liye log seedhi, kaam ki jaankari dhoondhte hain."),
    ("*", r"\s*Ye bahut kam competition wala local-search traffic hai \([^)]*\)\. Data bharne se pehle Census/LGD se milaan zaroor karein\.", ""),
    ("*", r"\s*Isse bahut zyada traffic aata hai\.", ""),
    ("*", r"\(original, mere dwara banaye gaye; PYQ nahi\)", "(abhyas ke liye; ye pichhle saal ke prashn nahi)"),
    ("*", r"isliye taza jaankari ke baad hi likhein\.", "isliye jaane se pehle official site ya sthaniya daftar se taza jaankari le lein."),
    ("*", r"Chamoli kshetra me Gorkha shasan se jude kisi vishesh kile ya yuddh-sthal ka naam main pakka nahi kar paya\. Isliye is hisse me wahi sthaniya jaankari jodein jo aapko gaon ke buzurgon ya sthaniya itihaskaron se mile\. Pehle se hi galat naam likhne se behtar hai ki jagah khali chhodein aur baad me bharein\.",
     "Chamoli kshetra mein Gorkha shasan se jude kisi khaas kile ya yuddh-sthal ka pakka naam kisi prakashit srot mein nahi milta, isliye yahan koi naam anumaan se nahi likha gaya."),
    ("*", r"Seedha Jawab: Almora me mahine ka kharch shahar aur gaon me alag hota hai\. Neeche ek khud bharne wali budget table hai\.",
     "Seedha Jawab: Almora me mahine ka kharch shahar aur gaon me alag hota hai. Neeche kharch ki khaas baatein hain - apne parivar ke hisaab se jod kar andaza lagayein."),
    ("*", r"Neeche ek khud bharne wali accessibility table aur checklist hai\.", "Neeche buzurg aur wheelchair yatriyon ke liye zaroori salah hai."),
    ("*", r"\s*- Unki jagah har heading me “khud survey karke bharne wali table”, checklist aur sahi sawal diye hain\.", ""),
    ("*", r"Ise bina sahi jaankari ke bharna ya paid reviews par chhodna galat hoga\.",
     "Champawat-Lohaghat ke purane halwai aur chai ki dukanon ki koi jaanchi hui suchi abhi uplabdh nahi hai; kisi dukaan ko '50 saal purani' kehne se pehle sthaniya logon se pushti zaroori hai."),
    ("*", r"Yeh vivaran verify hona baaki hai\.", "Is vivaran ki sarkari pushti abhi nahi mili hai."),
    ("*", r"aur iski sthan-wise verify ki hui suchi nahi hai", "aur iski sthan-wise jaanchi hui suchi nahi hai"),
]

# poora item hatao: (slug, regex jo item ke text mein ho)
DROP = [
    ("bageshwar-pariyojana-aapda-itihas", r"interactive quiz padhne wale ko page par rukne"),
    ("almora-basna-workation", r"^Budget table \(aap Almora me survey karke bharein\):$"),
    ("almora-basna-workation", r"^Table \(aap jaakar bharein\):$"),
    ("almora-basna-workation", r"^Success story likhne ka sahi tareeka"),
    ("almora-basna-workation", r"^Story ka dhancha:$"),
    ("almora-basna-workation", r"^Apni asli rasidein aur bills rakhein aur unhe reference ke roop me daalein\.$"),
    ("champawat-patti-gaon-bazaar", r"^- Verification: Dukaan ke naam ke saath"),
    ("haridwar-patti-gaon-bazaar", r"^Ek reliable \"Local Food Guide\" ka dhancha:$"),
    ("haridwar-patti-gaon-bazaar", r"^Bharne ke liye table \(sthaniya satyapan se\):$"),
    ("chamoli-purana-pahadi-jeevan", r"^121\.7 Ab Aap Bharein"),
    ("chamoli-purana-pahadi-jeevan", r"^Neeche ek khali table ka dhancha rakhein jise gaon ke buzurg bhar sakein:$"),
    ("chamoli-purana-pahadi-jeevan", r"^Har shabd ke saath ek vakya ka udaharan lein, jisme wo shabd istemal hota hai\."),
]
# heading badlo (jahan neeche ki 'kaise likhein' table hati)
HEAD = {
    ("champawat-pahadi-shabd-boli", "121.3 Aapke Gaon Ka Shabd: Word-Bank Ka Tareeka"): "121.3 Boliyon ko Bachane ki Nayi Pahal",
}


def _s(x, subs):
    if isinstance(x, str):
        for rx, rep in subs:
            x = rx.sub(rep, x)
        return x
    if isinstance(x, (list, tuple)):
        y = [_s(z, subs) for z in x]
        return type(x)(y) if isinstance(x, tuple) else y
    return x


_C = [(pre, re.compile(rx), rep) for pre, rx, rep in SUBS]
_D = [(sl, re.compile(rx)) for sl, rx in DROP]


def _txt(it):
    return it[1] if isinstance(it[1], str) else ""


def apply(p, log=None):
    slug = p.get("slug", "")
    subs = [(rx, rep) for pre, rx, rep in _C if pre == "*" or slug.startswith(pre)]
    out = []
    n = 0
    for it in p["items"]:
        if it[0] == "table" and it[1] and len(it[1][0]) > 1 and re.search(r"kya likhein", str(it[1][0][1]), re.I):
            n += 1                                   # 'Khana | Kya likhein' = lekhak ka dhancha, pathak ki jaankari nahi
            continue
        if any(sl == slug and rx.search(_txt(it)) for sl, rx in _D):
            n += 1
            continue
        if it[0] in ("h2", "h3", "h4") and (slug, it[1]) in HEAD:
            it = (it[0], HEAD[(slug, it[1])]) + tuple(it[2:])
        new = (it[0],) + tuple(_s(z, subs) for z in it[1:])
        if new != it:
            n += 1
        if new[0] in ("p", "pb", "ans") and isinstance(new[1], str) and not new[1].strip():
            continue
        out.append(new)
    p["items"] = out
    if log is not None and n:
        log.append({"page": slug, "action": "fix5", "n": n})
    return n
