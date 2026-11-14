# -*- coding: utf-8 -*-
"""v3.3.4 (audit-6): source file mein bache 'lekhak/website banane wale ke liye' nirdesh, keyword-list (stuffing) aur
'module/heading number' wali bhasha saaf. Har niyam haath se dekh kar likha (14 Nov 2026) - koi auto-likhai nahi.
Sirf hatata ya saaf shabd badalta hai; naya tathya nahi jodta."""
import re

# ---- poore vaakya jo pathak ke liye nahi, page banane wale ke liye the (kisi bhi page par mile to hatao)
SENT = [
    r"Website par inka istemal karte samay hamesha “pyaar bhari bolchaal ka hissa”[^.]*\.",
    r"Ek “Almora ke prachin lekh” ka page tabhi banayein[^.]*\.",
    r"Aap kya kar sakte hain \(original content\):[^.]*\.",
    r"- Page ke upar aap “Last updated: \[date\]” zaroor likhein aur har 3-6 mahine me check karein\.",
    r"Page ki shuruaat me steps rakhein, aur screenshot ya chhoti video guide jodein\.",
    r"Page par madad ke sahi raaste \(112, 181, Gaura Shakti\) aur zimmedar yatra ke tareeke likhein\.",
    r"Har tathya ke saath uska heading number \([^)]*\) jodein\.",
    r"Jin tathyon me tithi hai \(kapat, project ki sthiti\), unhe saal ke saath update karte rahein\.",
    r"Isliye apne Chamoli page par ise “Kumaon ka mahatvapurn andolan[^.]*\.",
    r"Inhe Chamoli ke page par “Uttarakhand ki prasiddh gathayein” ke roop me ek chhote note me hi likhein\.",
    r"Page par is tarah ki table me “upyog” ke saath “paramparik” shabd zaroor rakhein,[^.]*\.",
    r"Page par is vishay ko darane ke bajay sachchi jaankari aur suraksha salah ke roop me likhein\.",
    r"Is par page ko local-product ke roop me dikhane ke liye[^.]*\.",
    r"Apne gaon ki paramparik rasoi, chulha aur bartan ki tasveerein \(apni khinchi hui\) page par jodein\.",
    r"Page par “Ek paheli aur uska jawab \(neeche click karein\)”[^.]*\.",
    r"Ek chhota widget banayein jisme paheli dikhe[^.]*\.",
    r"Isse bachche page par zyada der rukte hain\.",
    r"Page par ise sirf “pehle ye hota tha, aur ab doctor se ilaaj ki salah dete hain” ke roop me likhein\.",
    r"Website par ise “Answer dikhayein” button \(HTML details/summary\) ke saath lagayein, taaki padhne wala pehle khud soche\.",
    r"Isse log page par zyada der rukte hain\.",
    r"Neeche score ke saath “Is quiz ko share karein” ka button dein\.",
    r"Ye table page ke upar ya neeche rakhein\.",
    r"Har pankti ke saath uska heading number likha hai, taaki padhne wala detail tak pahunch sake\.",
    r"\[?Aage Part C: [^\]]*\]",
    r"Page ke ant me “Sandarbh” naam ka ek section rakhein\.",
    r"Is kala ke jankar apne kshetra me khojkar unki tasveer aur jaankari page me jodein\.",
    r"Page par ek chhota “Karigar se kharidein” section jodein,[^.]*\.",
    r"Page ke upar “Last updated” tithi zaroor likhein\.",
    r"Page par ise “paramparik aahaar ki parampara” ke roop me sammanpoorvak likhein,[^.]*\.",
    r"Source aur “Last updated” tithi dein\.",
    r"Is bank ko page par “Chamoli ke 50 sabse zyada puchhe jaane wale sawal” ke roop me rakhein\.",
    r"Jin jawabon me tithi hai \(kapat, permit, niyam\), unke saath “Last updated” tithi zaroor dein[^.]*\.",
    r"Page par iska zikra karte samay kisi bhi swasthya laabh ka dava na karein;[^.]*\.",
    r"Is parampara par ek alag section me samudaya ki kahaniyan jodein\.",
    r"In naamon ko page me jodein, kyunki local log inhi naamon se jagah ko jaante hain\.",
    r"Chunav ka natija aur naye pratinidhiyon ki jaankari page par “Last updated” ke saath daalein\.",
    r"Ye fark samjhana aapke page ko “kaun sa chunav kaun karwata hai” jaisi search ke liye upyogi banata hai\.",
    r"Page par apne zile ke DLSA ka pata aur sampark nambar official site se lekar jodein\.",
    r"Page par ek chhoti table me aas-paas ke zilon ke code dena upyogi hoga,[^.]*\.",
    r"Page par ise \"kai itihaskar maante hain\" ya \"mana jata hai\" ke roop me hi likhein\.",
    r"Is section me unhe sirf \"sanskritik context\" me likhein,[^.]*\.",
    r"Quiz banane ka tareeka: [^.]*\.",
    r"Cheat-sheet banane ka sujhav: [^;]*;[^.]*\.",
    r"Ye ek bahut hi alag aur sourced content hoga\.",
    r"Gaon-wise data kaise banayein \(original content\):.*$",
    r"Ye original aur anubhav-aadharit content hoga\.",
    r"Isliye is section me \"Garhwali surnames ka origin\" jaise[^.]*\.",
    r"Ye heading aapke Uttarakhand Hub page se judne wala \"bridge\" hai; vistar wahan likhein\.",
    r"Ye “Pauri me workation” jaise search ke liye ek bahut upyogi aur sharing-layak content hai\.",
    r"\*\*Har tathya ke saamne “\(strot: ___, dekha gaya: November 2026\)“\*\* likhein\.",
    r"Official site ke link rel=\"noopener\" ke saath, aur Wikipedia ko sirf sandarbh ke roop me\.",
    r"Page ke upar “Last updated” tarikh dikhayein\.",
    r"Search Console me dekhein ki logon ne asli me kaun se shabd se aapko khoja,[^.]*\.",
    r"Seasonal shabd \(jaise “kailash yatra 2026”\) har saal update karein\.",
    r"Ye bahut kam log likhte hain, isliye bahut upyogi aur alag content hoga\.",
    r"Page par \"rate badal sakte hain, booking se pehle confirm karein\" zaroor likhein\.",
    r"Ye \"Garhwali shabd ka sahi ucharan\" jaisi search ke liye bahut kaam aata hai\.",
    r"Bachon ke liye Garhwali kahani aur paheliyan ka alag section banayein\.",
    r"Aap archive.org se wo page dekhkar table me bharein\.",
    r"Ye bahut hi alag aur zindagi se juda content hoga\.",
    r"Tehri ke page par in shaharon ko \"paas ke sthal\" ke roop me ek line me jodein,[^.]*\.",
    r"Agli Census ke naye aankde aane par page update karein\.",
    r"Dhyan dein: kisi bhi purani tasveer ko page par lagane se pehle uske copyright/anumati ki jaanch karein\.",
    r"Word me khulne par neeche ki suchi khali dikhe to[^.]*\.",
    r"Isse log aapke aankde par bharosa karenge\.",
    r"Voice search: [^\n]*$",
    r"Search phrases: [^\n]*$",
    r"Original research ka mauka: “Almora ke 25 ‘pehle’” ek achha long-form page ban sakta hai\.",
    r"Khud jaakar photo lene se aapka content unique banega\.",
    r"Agar aapke paas Census village directory ka data ho to use jodkar yeh section bahut majboot ban sakta hai\.",
    r"Ise “protein se bharpoor” jaisi saral bhasha me likha ja sakta hai, par bimari ke ilaj ke dave na karein\.",
    r"Is hastshilp ko badhawa dene ke liye “Chamoli se oon ke utpad kharidne ka sahi tareeka” ek alag section me likha ja sakta hai[^.]*\.",
    r"Ise aap Chamoli ke “naye rozgar” ke avsar ke roop me likh sakte hain\.",
    r"Is par gaon ke buzurgon se baat karke ek sanskritik jaankari ke roop me likha ja sakta hai[^.]*\.",
    r"Is par aap Chamoli ke Forest division \(.*?\) se sampark ka tareeka likh sakte hain; sabhi division ki sahi suchi Forest Department se lein\.",
    r"Vyanjan ki recipe aap apne gaon ya parivar ki parampara se jodkar likh sakte hain,[^.]*\.",
    r"Page par “Mansoon me yatra kaise karein” ka ek alag section yatriyon ke liye bahut upyogi rahega\.",
    r"Isse “Almora ke gaon se jama ki gayi kahawatein” jaisa unique content banega\.",
    r"Sthaniya verification ke baad hi isko .*? ki suchi me jodein\.",
    r"Kisi sthan ko “Chamoli ka rock climbing hub” likhne se pehle uski jaankari pushti karein\.",
    r"Inki suchi un jilon ke pages me likhein\.",
    r"Inhe un jilon ke pages me hi rakhein\.",
    r"Chamoli ke andolankariyon ke naam, jinhe aap shahid ke roop me likhna chahte hain,[^.]*\.",
    r"3\. 4\. Yeh jaankari ek “gaon-devta-sthal” table me rakhein\.",
    r"Sawal ko H3 ya bold me rakhein\.",
    r"Pahadi surnames \([^)]*\) ke bare me aap Garhwal ke jilon ke pages par vistar se likh sakte hain; wahan ye search bahut hota hai\.",
    r"Haridwar page me High-Intent Data Pack \(201-214\), Devanagari pack \(212\) aur emergency directory \(208\) pehle se hain\.",
    r"Ise \"Palayan\" ke roop me .*? me alag se likha ja sakta hai\.",
    r"Aap yahan par \"samasya aur samadhan\" santulit roop me likh sakte hain\.",
    r"Aapke page ke liye mauka: [^.]*\.(?: Iske liye Palayan Aayog ki report aur jile ke gram panchayat ke aankde jodein\.)?",
    r"Is par ek bhavuk H3 likha ja sakta hai: \"Old Tehri ke doobne ki kahani\"\.",
    r"Un modules me bhi sudhar kar diya gaya hai\.",
    r"Share ke liye WhatsApp aur Facebook ka link rakhein\.",
]
SENT_RX = [re.compile(r"(?:^|(?<=\s))" + s + r"\s*") for s in SENT]

# ---- shabd/vaakya-ansh jo badalne hain (pathak ki bhasha mein; matlab wahi)
SUBS = [
    # ---- samay ke saath galat hone wali bhasha (tareekh beetne par bhi sahi rahe; tathya wahi)
    (r"Abhi \(8 November 2026\) ke baad Haridwar ke sabse nazdiki snan hain: Somvati Amavasya \(9 November 2026\) aur Kartik Purnima \(24 November 2026\)\. Uske baad",
     "November 2026 se November 2027 tak Haridwar ke bade snan: Somvati Amavasya (9 November 2026), Kartik Purnima (24 November 2026), phir"),
    (r"Aane Wale 12 Mahino ke Snan aur Pramukh Parv", "November 2026 se November 2027 ke Snan aur Pramukh Parv"),
    (r"Somvati Amavasya 9 November 2026 ko hai kya\? Haan, Kartik Amavasya Somvar ko \(9 Nov 2026\)\.",
     "Somvati Amavasya (Kartik) 2026 me kis din padi? 9 November 2026, Somvar."),
    (r"Kumbh-tithi \(14 Jan-20 Apr 2027\) aur Kartik Purnima \(24 Nov 2026\) par jaa rahe hon to jaldi booking\.",
     "Kumbh-tithi (14 Jan-20 Apr 2027) aur Kartik Purnima jaise bade snan par jaa rahe hon to jaldi booking."),
    (r"Badrinath 16 November 2026 se band hai aur agle saal April-May me khulega \(2026 me 23 April ko khula tha\)\.",
     "Badrinath ke kapat 2026 me 23 April ko khule aur 16 November 2026 ko band hone tay the; har saal sardi me band rehkar April-May me phir khulte hain."),
    (r"बद्रीनाथ धाम के कपाट 2026 में कब बंद होंगे\?", "बद्रीनाथ धाम के कपाट 2026 में किस दिन बंद होने तय थे?"),
    (r"Banbasa me agla Agniveer rally 23 se 29 November 2026 ko tay hai, aur lagbhag 4,492 CEE-qualified yuva isme shamil honge\.",
     "Banbasa me Agniveer rally ki tithi 23 se 29 November 2026 batayi gayi, jisme lagbhag 4,492 CEE-qualified yuvaon ke shamil hone ki baat thi."),
    (r"Banbasa me agla Agniveer rally kab hai\? Ek local khabar-portal ke anusar 23 se 29 November 2026\.",
     "Banbasa Agniveer rally 2026 ki tithi kya batayi gayi? Ek local khabar-portal ke anusar 23 se 29 November 2026."),
    (r"Banbasa me agla Agniveer rally kab hai\?", "Banbasa Agniveer rally 2026 ki tithi kya batayi gayi?"),
    (r"^Agla rally \(taaza\)$", "Rally (November 2026)"),
    (r"^Taaza; Verify baaki$", "Local portal; official notice se pushti karein"),
    (r"lagbhag 18,300 Agniveer 31 December 2026 tak pehle chakra me seva poori karenge\.",
     "pehle chakra ke lagbhag 18,300 Agniveer ki seva 31 December 2026 tak poori hone ka anumaan tha."),
    (r"\b(upar|pichhle|pehle|aage|agle|baaki|baki|Baaki|Pehle|Pichhle|Upar)( ke) [Mm]odules\b", r"\1\2 hisson"),
    (r"\b[Pp]ichhle modules\b", "pichhle hisson"),
    (r"\bpichhle module\b", "pichhle hisse"),
    (r"\b(poore|is poore) module\b", r"\1 hisse"),
    (r"\bYe poora module\b", "Ye poora hissa"),
    (r"\bPehle module me\b", "Pehle hisse me"),
    (r"\bantim module hai\b", "aakhri hissa hai"),
    (r"\bsabse mahatvapurn module hai\b", "sabse mahatvapurn hissa hai"),
    (r"\bse aage ka module\b", "se aage ka hissa"),
    (r"\bke khane ke modules me hain\b", "wale khane ke hisse me hain"),
    (r"\baur aage ke modules me aayega\b", "me di gayi hai"),
    (r"\bus module ka reference diya gaya hai\b", "us hisse ka link diya gaya hai"),
    (r"\bHar module ke “Quick Q&A”", "Har hisse ke “Quick Q&A”"),
    (r"\bBaaki modules me\b", "Baaki hisson me"),
    (r"\bPage ke modules padhkar\b", "Page ke hisse padhkar"),
    (r"\bzameen ke niyam wale module\b", "zameen ke niyam wale hisse"),
    (r"\(module me upar\)", "(upar)"),
    (r"\bModules 6 se 11 me\b", "upar ke hisson me"),
    (r"\bjo upar ke modules me\b", "jo upar ke hisson me"),
    (r"\bUpar Ke Modules Me\b", "Upar Ke Hisson Me"),
    (r" 18 modules me 200 headings ke saath ", " "),
    (r"\bhar heading me kis vishay par kya hota tha, matlab,", "har vishay par kya hota tha, uska matlab"),
    (r"\b[Hh]ar heading me\b", "har hisse me"),
    (r"\bHar heading me\b", "Har hisse me"),
    (r"\b[Aa]gle heading me\b", "agle hisse me"),
    (r"\bPichhle Heading me\b", "Pichhle hisse me"),
    (r"\bHar medical heading me\b", "Har medical vishay me"),
    (r"\bhar heading par lagu\b", "har vishay par lagu"),
    (r"\bHar heading ke aakhir me\b", "Har vishay ke aakhir me"),
    (r"\bkharche ke heading diye hain\b", "kharche ke vishay diye hain"),
    (r"\bisliye ye heading Pauri ke liye\b", "isliye ye vishay Pauri ke liye"),
    (r"\bwahi heading dekhein\b", "wahi hissa dekhein"),
    (r"\bsambandhit heading dekhein\b", "sambandhit hissa dekhein"),
    (r"\bYe heading poore page ke\b", "Ye hissa poore page ke"),
    (r"\bus heading ka sandarbh\b", "us hisse ka sandarbh"),
    (r"\bVistaar ke liye heading number dekhein\.", "Vistaar ke liye page ke baaki hisse dekhein."),
    (r"\bVistaar ke liye har pankti ke saath us vishay ka heading number diya gaya hai\.", "Vistaar ke liye baaki hisse dekhein."),
    (r"\b(kuch|kai|Is hisse ke kuch|is hisse ke) headings\b", r"\1 vishay"),
    (r"\bun headings par\b", "un vishayon par"),
    (r"\bjaise headings ka\b", "jaise vishayon ka"),
    (r"\byeh headings\b", "ye vishay"),
    (r"\bIs hisse ke headings\b", "Is hisse ke vishay"),
    (r"\bPehle saat headings \(136 se 142\)", "Pehle saat hisse"),
    (r"\bIs par agle heading me baat karte hain\.", "Is par aage baat karte hain."),
    (r"\bIs baare me agle heading me\b", "Is baare me aage"),
    (r"\bIs section me sirf wahi naam likhe jayenge\b", "Is hisse me sirf wahi naam likhe gaye hain"),
    (r", isliye inka alag ullekh search ke liye zaroori hai\.", "."),
    (r", jo nostalgia, shiksha aur \"purane zamane me kaise hota tha\" jaise search ke liye bahut lokpriya hai\.", "."),
    (r"; page par sirf wahi daalein jo official site par ho\.", "; official site par diya number hi istemal karein."),
    (r", isliye unhe sthaniya mahilaon se likhit sangrah kar ke page par jodein\.", "."),
    (r"\s*\[local survey needed\]", " (sthaniya pushti baaki)"),
    (r"\s*\[(?:verified|verified naam|safety|general observation|interpretation)\]", ""),
    (r"\[recipe varies by village\]", "(vidhi gaon-gaon me alag)"),
    (r"\[sthaniya naam badal sakta hai\]", "(sthaniya naam badal sakta hai)"),
    (r"\[Mountain Voices glossary\]", "(srot: Mountain Voices glossary)"),
    (r"\[([^\[\]]*(?:parampara|verified|Lok-vishwas|sandarbh|jaankari)[^\[\]]*)\]", r"(\1)"),
    (r"^Part [A-K]: ", ""),
    (r"\bVoice Search ke 30 Seedhe Sawal-Jawab \(Mobile par Bole Jane Wale\)", "30 Seedhe Sawal-Jawab"),
    (r"\bVoice Search ke 30 Seedhe Sawal-Jawab\b", "30 Seedhe Sawal-Jawab"),
    (r"\bVoice Search Ke 30 Seedhe Sawal-Jawab\b", "30 Seedhe Sawal-Jawab"),
    (r"\bVoice Search ke Sawal \(30 Sawal-Jawab\)", "30 Seedhe Sawal-Jawab"),
    (r"\bVoice Search Aur Hinglish Sawal Bank\b", "Log Kya Puchhte Hain: Sawal-Jawab"),
    (r"\bVoice Search aur Hinglish Query Bank: 30 Sawaal-Jawab\b", "30 Seedhe Sawal-Jawab"),
    (r"\bVoice Search aur Hinglish Query Bank \(30 Sawal-Jawab\)", "30 Seedhe Sawal-Jawab"),
    (r"\bVoice Search aur Hinglish Query Bank\b", "Log Kya Puchhte Hain: Sawal-Jawab"),
    (r"\bVoice Search aur Hinglish Sawal \(Log Kya Puchhte Hain\)", "Log Kya Puchhte Hain: Sawal-Jawab"),
    (r"^Quick Q&A \(Voice Search\):$", "Chhote sawal-jawab:"),
    (r", voice-search ke sawaal,", ", seedhe sawal-jawab,"),
    (r", voice search ke sawal,", ", seedhe sawal-jawab,"),
    (r"\bvoice search ke sawal\b", "seedhe sawal-jawab"),
    (r"Heading Bonus \(", "("),
    (r" \| 200 Heading Master Page$", ""),
    (r"Isliye is hisse me “prashikshan sansthan ka naam” tabhi jodein jab aap use IMF ya Uttarakhand Adventure Sports ki suchi se pushti karein\.",
     "Kisi sansthan me daakhila lene se pehle uska naam IMF ya Uttarakhand Adventure Sports ki suchi se pakka karein."),
    (r"Is suchi ko aap Uttarakhand Land Records \(Bhulekh\) ya zila Rajasv vibhag se milakar bharein\.",
     "Pakki suchi ke liye Uttarakhand Land Records (Bhulekh) ya zila Rajasv vibhag dekhein."),
    (r"Poori table ke liye India Post ki official PIN directory se data nikalkar yaha jodein\.",
     "Apne dak ghar ka PIN India Post ki official PIN directory se pakka karein."),
    (r"; unki suchi un jilon ke pages me daalein\.", "; unki suchi un jilon ke pages par hai."),
    (r"^Pauri ki suchi me na jodein jab tak pramanik strot na mile$", "Pramanik strot nahi mila"),
    (r"^Original research ka tareeka: ", "Apne gaon ki jaankari jutane ka tareeka: "),
    (r"^Heading upar$", "Upar dekhein"),
    (r"\bMaster FAQ Addendum \((40 aur Sawal-Jawab)\)", r"\1"),
    (r"Ye asli PYQ nahi hain, isliye inhe \"practice questions\" ke roop me hi dikhayein\.", "Ye asli PYQ nahi, sirf abhyas (practice) ke sawal hain."),
    (r"ke karyalay se list lein aur ek photo-essay banayein\.", "ke karyalay se poori suchi lein."),
    (r", jise aap sthaniya shabdon ke saath likh sakte hain\.", "."),
    (r"\bseedha jawab alag H3 me diya gaya hai\b", "seedha jawab alag hisse me diya gaya hai"),
    (r"^\"Tab aur ab\" \(Then vs Now\) ke content ke vichar:$", "\"Tab aur ab\" (Then vs Now):"),
    (r"\bwale headings \(138 se 142\) me\b", "wale hisson me"),
    (r"\bpage ke modules dobara dekhein\b", "page dobara padhein"),
    (r"\bpage ke headings dekhein\b", "page dobara padhein"),
]
SUBS_RX = [(re.compile(a), b) for a, b in SUBS]

# ---- poora paragraph hatao (pathak ke kaam ka nahi)
PDROP = [
    r"^Draft: \d{1,2} November 2026 \|",
    r"^\(2\) 40 aur sawal-jawab \(50 FAQ ke upar\)\.$",
    r"^“Champawat” ki spelling kaise likhein \(search ke liye\):",
    r"^Gaon ka page kaise banayein \(Micro-spoke idea\):$",
    r"^Voice search ke liye likhne ke niyam:$",
    r"^Original aur sahi story banane ka tareeka:$",
    r"^Gazetteer kholkar in sawalon ke jawab dhoondhein aur apne shabdon me likhein",
    r"^Module suchi: M1 ",
    r"^Heritage content ke vichar:$",
    r"^PYQ kaise ikattha karein \(original content ke liye\):$",
    r"^Lekhak: Manoj Kumar Pandey, Sab Hisaab \| Aakhri update: \[DD Month YYYY\]",
]
PDROP_RX = [re.compile(s) for s in PDROP]
# in paragraph ke turant baad wali list bhi lekhak-nirdesh thi
PDROP_WITH_LIST = {s for s in PDROP if re.search(r"Micro-spoke|likhne ke niyam|story banane|Gazetteer kholkar|Heritage content|PYQ kaise", s)}

# ---- poora hissa (heading se agli barabar/upar ki heading tak) hatao
HDROP = [
    r"Har Dish Ka Blo(?:c)?k Banane Ka Tareeka$",
    r"Is Section Ko Banane Ka Tareeka$",
    r"Log Yeh Bhi Search Karte Hain$",
    r"Seasonal aur Time-Based Search$",
    r"Local Town aur Tehsil Intent$",
]
HDROP_RX = [re.compile(s) for s in HDROP]


def is_kw_list(lis):
    """Search-query ki chhoti-chhoti lowercase suchi (keyword stuffing) - Google spam niti ke khilaf."""
    lis = [x for x in lis if isinstance(x, str)]
    if len(lis) < 4:
        return False
    q = sum(1 for x in lis if re.fullmatch(r"[a-z0-9 '\-?/]+", x.strip()))
    return q >= len(lis) * 0.6


def _clean_str(t):
    for rx in SENT_RX:
        t = rx.sub("", t)
    for rx, rep in SUBS_RX:
        t = rx.sub(rep, t)
    return re.sub(r"[ \t]{2,}", " ", t).strip() if t != t.strip() or "  " in t else t


def _cl(x):
    if isinstance(x, str):
        return _clean_str(x)
    if isinstance(x, list):
        return [_cl(z) for z in x]
    if isinstance(x, tuple):
        return tuple(_cl(z) for z in x)
    return x


def apply(p, log=None):
    items = p["items"]
    out = []
    n = 0
    i = 0
    while i < len(items):
        it = items[i]
        k = it[0]
        if k in ("h2", "h3", "h4") and any(rx.search(it[1]) for rx in HDROP_RX):
            L = int(k[1])
            j = i + 1
            while j < len(items) and not (items[j][0] in ("h2", "h3", "h4") and int(items[j][0][1]) <= L):
                j += 1
            n += j - i
            i = j
            continue
        if k == "ul" and is_kw_list(it[1]):
            n += 1
            i += 1
            continue
        if k in ("p", "pb", "ans") and isinstance(it[1], str):
            hit = [s for s, rx in zip(PDROP, PDROP_RX) if rx.search(it[1].strip())]
            if hit:
                n += 1
                i += 1
                if hit[0] in PDROP_WITH_LIST and i < len(items) and items[i][0] == "ul":
                    i += 1
                continue
        new = (k,) + tuple(_cl(z) for z in it[1:])
        if new != it:
            n += 1
        if k in ("p", "pb", "ans") and isinstance(new[1], str) and not new[1].strip():
            i += 1
            continue
        if k == "ul":
            lis = [x for x in new[1] if not (isinstance(x, str) and not x.strip())]
            if not lis:
                i += 1
                continue
            new = (k, lis) + tuple(new[2:])
        out.append(new)
        i += 1
    p["items"] = out
    if log is not None and n:
        log.append({"page": p.get("slug", ""), "action": "clean6", "n": n})
    return n
