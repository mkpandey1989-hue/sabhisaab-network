"""v3.9.2 (24 Nov 2026): 1000+ naye kaam (owner ki list + 18-26 hisse) -> rate list mein.
Daam ka niyam (svc_gen_rates.py jaisa): floor = AI ke saath ghante x Rs300 x 1.2 (Rs360/ghanta) - kabhi isse neeche nahi (paise bachein).
Bazaar (market) = aam freelancer ka kam se kam daam: bina AI ke ~3 guna samay x Rs500/ghanta, ya hisse ka jaancha hua kam se kam daam
(sources: docs/MARKET_RATES.md). Hamara daam = max(floor, bazaar x factor) -> 'se shuru'. Jahan bazaar hi sasta (CSC/cyber cafe) wahan
'sasta' ka dawa nahi hota (video/site sirf jahan bazaar > hamara).
Policy: (1) broker par apne aap order lagane wala algo/script NAHI (SEBI 4 Feb 2025: algo provider exchange-empanelled hona chahiye);
(2) jo kaam log khud 1 click mein kar lete (PDF merge/split/compress, background hatana) owner ne 24 Nov hataye the - wo nahi;
(3) naam mein 'AI' nahi (owner niyam) - 'smart'/'chatbot'; (4) sarkari kaam = sirf madad/guide, OTP/password customer khud."""
import difflib
import json
import pathlib
import re

HOUR, BUF = 300, 1.2

# cat: (title, sub, ghante, bazaar_lo, bazaar_hi, factor, din, risk, video_group, shot, q1, q2, fayda, bolne_ka_naam)
CATS = {
 "cloud":  ("☁️ VM aur cloud server (aapke account par)", "Oracle/AWS/GCP/VPS - setup, secure, 24x7 chalana", 1.5, 1500, 8000, .3, "1-2 din", "Y",
            "बनाना", "phone", "सर्वर का काम", "खुद मुश्किल लगता है?", "आपके खाते पर", "सर्वर और क्लाउड सेटअप"),
 "devops": ("🔐 DevOps aur server security", "Auto-deploy, backup, alert, Cloudflare", 2, 2500, 15000, .3, "1-3 din", "Y",
            "बनाना", "phone", "सर्वर सुरक्षित", "है या नहीं?", "अलर्ट + बैकअप", "सर्वर सुरक्षा और ऑटो डिप्लॉय"),
 "data":   ("🗄️ Database, backup aur API", "MySQL, Postgres, Sheet, backup, API", 2, 2000, 12000, .3, "1-3 din", "G",
            "बनाना", "stock", "डेटा का", "बैकअप है?", "रोज़ बैकअप", "डेटाबेस, बैकअप और ए पी आई"),
 "domain": ("📧 Domain, email aur hosting", "Domain, DNS, business email, free hosting", .8, 800, 5000, .3, "Same din", "Y",
            "मदद", "site", "अपने नाम का", "डोमेन और ईमेल?", "आपके नाम पर", "डोमेन, ईमेल और होस्टिंग"),
 "smart":  ("🧠 Smart automation (chatbot, OCR, awaaz se likhna)", "Chatbot, PDF se data, Hindi awaaz-text", 3, 3000, 20000, .3, "2-4 din", "G",
            "बनाना", "bot", "रोज़ का काम", "अपने आप हो?", "समय की बचत", "स्मार्ट ऑटोमेशन"),
 "bot":    ("🤖 Bot aur automation", "WhatsApp/Telegram/Sheet - kaam apne aap", 2.5, 3000, 20000, .3, "2-3 din", "G",
            "बनाना", "bot", "ग्राहक के मैसेज", "छूट जाते हैं?", "अपने आप जवाब", "बॉट और ऑटोमेशन"),
 "web":    ("🌐 Website aur online dukaan", "Aapke naam par, tez, mobile par saaf", 7, 10000, 50000, .25, "2-4 din", "G",
            "बनाना", "site", "आपके काम की", "वेबसाइट नहीं?", "आपके नाम पर", "वेबसाइट"),
 "calc":   ("🧮 Calculator aur tools", "Apni website par apna tool", 3.5, 5000, 15000, .25, "2 din", "G",
            "बनाना", "calc", "वेबसाइट पर", "अपना कैलकुलेटर?", "आपका लोगो", "कैलकुलेटर टूल"),
 "soft":   ("🧾 Business software (billing, stock, khata)", "Aapke dhande ke hisaab se", 9, 8000, 50000, .3, "4-7 din", "G",
            "बनाना", "bill", "हिसाब अभी भी", "कॉपी में?", "सब एक जगह", "बिज़नेस सॉफ़्टवेयर"),
 "app":    ("📱 Mobile aur web app", "Android/PWA - aapke naam par", 12, 20000, 100000, .2, "5-10 din", "G",
            "बनाना", "site", "अपना ऐप", "बनवाना है?", "फ़ोन पर आइकन", "मोबाइल ऐप"),
 "excel":  ("📊 Excel aur Google Sheet", "Formula, dashboard, register, automation", .8, 500, 5000, .3, "1 din", "G",
            "बनाना", "stock", "Excel में", "उलझे हैं?", "साफ़ शीट", "एक्सेल और गूगल शीट"),
 "docs":   ("📄 Excel, PDF aur documents", "Ghanton ka kaam minuton mein", .6, 300, 3000, .3, "1 din", "G",
            "बनाना", "letter", "डॉक्यूमेंट", "बनाना है?", "साफ़ फ़ॉर्मेट", "डॉक्यूमेंट और पी डी एफ"),
 "design": ("🎬 Video, design aur reels", "Brand jaisa look, bina shoot", 1, 500, 5000, .3, "1-2 din", "G",
            "बनाना", "list", "दुकान का", "डिज़ाइन चाहिए?", "छपाई लायक", "डिज़ाइन और वीडियो"),
 "content": ("✍️ Content aur SEO", "Google par dikhne ki taiyari", 1.5, 1500, 10000, .3, "1-3 din", "G",
            "बनाना", "letter", "गूगल पर", "दिखना है?", "गूगल के हिसाब से", "कंटेंट और एस ई ओ"),
 "ecom":   ("🛒 E-commerce setup", "Order, payment, shipping", 2, 2000, 15000, .3, "1-3 din", "G",
            "बनाना", "site", "सामान ऑनलाइन", "बेचना है?", "ऑर्डर अपने आप", "ऑनलाइन बिक्री सेटअप"),
 "trade":  ("📈 Trading tools (aapki apni strategy)", "Tip/signal nahi - sirf aapke rules ka tool, order apne aap NAHI", 3, 3000, 15000, .3, "2-4 din", "Y",
            "बनाना", "trade", "अपनी स्ट्रेटेजी", "जाँचनी है?", "टिप/सिग्नल नहीं", "ट्रेडिंग टूल, आपके अपने नियम"),
 "micro":  ("⚡ Chhote kaam (₹10 se)", "Same din, 100% advance", .08, 100, 500, .15, "Same din", "G",
            "बनाना", "letter", "छोटा सा काम", "अटका है?", "उसी दिन", "छोटा डिजिटल काम"),
 "guide":  ("🎓 Sikhana / guide (screen-share)", "Aap khud karein, hum saath batayein", .5, 400, 1250, .45, "Same din", "G",
            "मोबाइल-कंप्यूटर", "phone", "खुद सीखना है?", "साथ बैठ कर", "स्क्रीन-शेयर", "सीखिए, स्क्रीन शेयर पर"),
 "fix":    ("🔧 Theek karna (repair)", "Jo toota hai, wo chalu", 1, 1000, 8000, .3, "Same din", "Y",
            "मदद", "site", "कुछ चल नहीं रहा?", "ठीक कराइए", "जल्दी ठीक", "ठीक करने का काम"),
 "care":   ("🔁 Har mahine dekhbhal", "Kabhi bhi band, sirf chalne tak charge", .3, 500, 6000, .2, "Har mahina", "G",
            "मदद", "site", "हर महीने", "देखभाल?", "कभी भी बंद", "हर महीने की देखभाल"),
 "local":  ("🏔️ Local aur Pahadi kaam", "Homestay, gaon ki dukaan, yatra, mela", 1.2, 500, 10000, .3, "1-2 din", "G",
            "बनाना", "book", "पहाड़ का काम", "ऑनलाइन?", "आपके इलाके के लिए", "लोकल और पहाड़ी काम"),
 "naukri": ("🏛️ Sarkari naukri / bharti form madad", "Form, documents, admit card - OTP/fees aap khud", .12, 100, 300, .45, "Same din", "Y",
            "मदद", "form", "भर्ती का फ़ॉर्म", "गलती का डर?", "OTP आप ही डालें", "सरकारी भर्ती फ़ॉर्म में मदद"),
 "yojana": ("🪪 Yojana aur praman patra madad", "Sirf madad/guide - sarkari fees portal par aap khud", .12, 100, 300, .45, "Same din", "Y",
            "मदद", "form", "योजना का आवेदन", "कैसे करें?", "आप सामने, हम साथ", "योजना और प्रमाण पत्र में मदद"),
 "padhai": ("🎒 School / college form madad", "Admission, exam form, counselling guide", .12, 100, 300, .45, "Same din", "G",
            "मदद", "form", "एडमिशन का फ़ॉर्म", "समझ नहीं आता?", "सही कागज़, सही समय", "स्कूल कॉलेज फ़ॉर्म में मदद"),
 "daftar": ("🗂️ Rozmarra daftar-kaam (RTI, shikayat, claim)", "Draft aur guide - vakeel ki salah nahi", .25, 200, 1000, .4, "Same din", "Y",
            "मदद", "letter", "शिकायत या क्लेम", "कैसे लिखें?", "सही फ़ॉर्मेट", "शिकायत और क्लेम का ड्राफ्ट"),
 "senior": ("👴 Buzurg aur gaon ke liye madad", "UPI, smartphone, Jeevan Pramaan, scam se bachav", .2, 100, 500, .5, "Same din", "G",
            "मोबाइल-कंप्यूटर", "phone", "फ़ोन चलाना", "मुश्किल लगता है?", "आराम से, साथ में", "बुज़ुर्गों के लिए फ़ोन मदद"),
}

SRC_CAT = {1: "cloud", 2: "devops", 3: "data", 4: "domain", 5: "smart", 6: "bot", 7: "web", 8: "calc", 9: "soft", 10: "app",
           11: "excel", 12: "docs", 13: "design", 14: "content", 15: "ecom", 16: "trade", 17: "micro"}

# owner ki list ke baad ke kaam (17.41-50 aur 18-26) - list adhuri aayi thi (17.40 par kati)
ADD = {
 "micro": ["Website quick review", "Google Form se WhatsApp alert", "Visiting card design", "Ek page notice / suchna",
           "Hindi-English ek page typing", "Photo ka size form ke liye (KB)", "Signature scan theek", "Chhota poster text",
           "Bill ka format theek", "Chhoti Excel sheet theek"],
 "guide": ["Excel sikhiye (30 min)", "Google Sheet sikhiye (30 min)", "Canva sikhiye (30 min)", "Smartphone chalana sikhiye (30 min)",
           "UPI safe tareeke se sikhiye (30 min)", "Email aur Google Drive sikhiye (30 min)", "Website khud update karna sikhiye",
           "WordPress chalana sikhiye", "Telegram bot chalana sikhiye", "VM / server chalana sikhiye", "Google Business Profile chalana sikhiye",
           "YouTube channel setup sikhiye", "Reels banana sikhiye (phone se)", "Online form bharna khud sikhiye", "TradingView chart chalana (sirf tool)",
           "Python basic sikhiye (1 ghanta)", "Hindi typing sikhiye", "Zoom / Meet chalana sikhiye", "Cyber fraud se bachna sikhiye",
           "Apni dukaan ka hisaab Sheet mein sikhiye"],
 "fix":   ["WordPress error theek", "Website hack ke baad saaf karna", "Contact form ka email nahi aata - theek", "Email spam mein jata hai - theek",
           "Google Analytics / tag theek", "Search Console error theek", "Payment gateway error theek", "WhatsApp button kaam nahi karta - theek",
           "Mobile par website tooti - theek", "Excel macro error theek", "Google Sheet script error theek", "Telegram bot band - theek",
           "Server down - wapas chalu", "SSL / https error theek", "Domain / DNS galat - theek", "App crash theek (aapka code)",
           "Pinterest / FB page connect error theek", "Printer / scanner setup madad (screen-share)", "Phone storage / slow theek (screen-share)",
           "Laptop software install madad (screen-share)"],
 "care":  ["Website care basic (mahina)", "Website care + 3 badlav (mahina)", "Social post care - 8 post (mahina)", "Google Business posts - 4 (mahina)",
           "Bot care (mahina)", "Server / VM care (mahina)", "Backup care (mahina)", "SEO care + report (mahina)", "Excel / Sheet report care (mahina)",
           "Online store care (mahina)", "Telegram channel post care (mahina)", "Trading tool care (sirf aapka tool, mahina)"],
 "local": ["Homestay ki Google listing + photo", "Homestay booking page", "Pahadi product online (WhatsApp catalogue)", "Gaon ki dukaan ka WhatsApp catalogue",
           "Char Dham yatra registration guide", "Taxi / cab service ka page", "Mela / utsav ka poster", "Shaadi / pooja ka digital nyota",
           "Pahadi product label", "Mandi bhav sheet (aapke liye)", "Bigha-nali-biswa converter widget", "Gaon ki samiti ka hisaab sheet",
           "Local coaching ka admission poster", "Trekking / tour package page", "Local dukaan ka Google Maps sudhar"],
 "naukri": ["SSC form madad", "Railway (RRB) form madad", "Police bharti form madad", "Agniveer form madad", "TET / CTET form madad", "Bank (IBPS/SBI) form madad",
            "Anganwadi bharti form madad", "UKSSSC / UKPSC form madad", "Rajya bharti form madad (kisi bhi rajya)", "Eligibility aur umar-chhoot jaanch",
            "Documents checklist (bharti ke hisaab se)", "Fee payment guide", "Admit card download madad", "Result dekhne mein madad",
            "Correction window guide", "Roz ki Hindi bharti summary (aapke liye)", "Aapke liye kaun si bharti - suchi", "Answer-key objection draft",
            "DV (document verification) checklist", "Interview taiyari (30 min)", "Typing test taiyari guide", "Photo-signature size (bharti ke hisaab se)"],
 "yojana": ["PM Kisan registration / status madad", "Ayushman card guide", "Ration card apply guide", "Aay praman patra apply guide",
            "Jati praman patra apply guide", "Niwas praman patra apply guide", "Vridha / vidhwa / divyang pension apply guide", "e-Shram card guide",
            "Labour card guide", "Scholarship (NSP / rajya) apply madad", "KCC (Kisan credit card) documents guide", "PAN card apply guide",
            "Voter ID apply / sudhar guide", "Passport apply guide", "Driving licence online apply guide", "Janm / mrityu praman patra guide",
            "Khatauni / dakhil-kharij guide", "Udyam registration madad", "FSSAI registration madad", "GST registration documents guide",
            "Mudra / PMEGP project report", "Bijli / paani connection online apply guide"],
 "padhai": ["School admission form madad", "RTE admission form madad", "Board private candidate form madad", "University exam form madad",
            "Re-evaluation form madad", "Marksheet sudhar ki application", "Migration certificate application", "DigiLocker + APAAR ID madad",
            "CUET form madad", "JEE / NEET form madad", "Counselling choice-filling guide", "Hostel form madad", "Education loan documents guide",
            "Fees chhoot ka patra", "Scholarship renewal madad", "Online class / exam setup madad"],
 "daftar": ["RTI application draft", "Consumer shikayat draft (e-Daakhil guide)", "Bank / RBI shikayat draft", "Cyber fraud shikayat guide (1930)",
            "Insurance claim documents guide", "EPF claim guide", "ITR guide (aap khud bharein)", "Police shikayat format", "Kiraynama format (vakeel se jaanch karwayein)",
            "Duplicate document guide", "Bijli bill shikayat draft", "Gas / LPG shikayat draft", "Nagar nigam shikayat draft", "Railway refund / TDR guide"],
 "senior": ["UPI safe setup", "Naya smartphone setup", "Jeevan Pramaan (pension life certificate) madad", "Bank KYC guide", "WhatsApp video call sikhana",
            "Hindi awaaz se likhna (voice typing)", "Scam / fraud call se bachav guide", "Bade akshar + aasan phone setting", "Pension status dekhna",
            "Online bill bharna sikhana", "Dawai / doctor appointment online guide", "Photo-video bachchon ko bhejna sikhana"],
}

# naam badlo (owner niyam: 'AI' shabd nahi; video audit chatgpt/gemini bhi rokta)
RENAME = {
 "ChatGPT / Claude / Gemini API setup": "Chatbot API setup (OpenAI / Claude / Gemini)",
 "Website par AI chatbot": "Website par smart chatbot", "WhatsApp par AI chatbot (official API)": "WhatsApp par smart chatbot (official API)",
 "PDF se AI FAQ bot": "PDF se sawal-jawab bot", "AI se customer reply draft": "Customer reply draft helper", "AI content writing workflow": "Content writing workflow",
 "AI image workflow": "Image banane ka workflow", "AI voice-over workflow": "Voice-over workflow", "AI video script maker": "Video script maker",
 "AI resume improver": "Resume sudhar tool", "AI email reply assistant": "Email reply helper", "AI meeting notes summary": "Meeting notes summary",
 "AI data cleaning": "Data cleaning automation", "Custom GPT / Claude Project setup": "Custom chatbot project setup", "n8n mein AI workflow": "n8n workflow",
 "Zapier / Make mein AI workflow": "Zapier / Make workflow", "Roz ke kaam ka AI agent": "Roz ke kaam ka smart agent", "Telegram AI bot": "Telegram smart bot",
 "Discord AI bot": "Discord smart bot", "Slack AI bot": "Slack smart bot", "Apne documents par AI search": "Apne documents mein smart search",
 "AI kharcha (API cost) monitor": "API kharcha monitor", "Shayari / quote (original)": "Shayari / quote (apni, original)",
 # video audit 'profit' shabd rokta hai (trading vaada) - dukaan ke hisaab ke liye 'nafa-nuksaan'
 "Profit margin": "Dukaan margin", "Profit / loss sheet": "Nafa-nuksaan (P&L) sheet", "Profit tracker": "Nafa-nuksaan tracker",
}
# nahi lena (wajah)
SKIP = {
 # SEBI 4 Feb 2025: broker API se apne aap order = empanelled algo provider ka kaam
 "Order script (aapke rules)", "Stop-loss auto script", "Target / trailing script", "Square-off script", "Token auto-refresh", "Static IP setup",
 "Zerodha Kite API setup", "Angel One SmartAPI setup", "Dhan API setup", "Upstox API setup", "Fyers API setup", "Delta Exchange API setup",
 "Trading VM + 24x7 service", "Crypto bot (aapke rules, aapka exchange API)", "Apne bot se Telegram trade alert",
 # log khud 1 click mein (owner 24 Nov)
 "PDF merge", "PDF split", "PDF compress", "PDF se Word", "Word se PDF", "Watermark", "Password lagana", "Page order badalna", "Image se PDF",
 "Excel se PDF", "Background removal", "Photo background saaf",
 # pehle se 112 mein (dohra nahi)
 "Logo", "GST billing", "E-invoice", "POS", "Khata", "Inventory", "CRM", "Quotation", "Custom software (aapki zaroorat ka)", "Resume banana",
 "Biodata design", "Online form bharne mein madad", "Application / patra", "Google Form banana", "Rate card", "Thumbnail", "Invitation card",
 "Bill / quotation format", "Hindi typing", "PineScript indicator", "TradingView alerts", "Strategy backtest", "Trade journal sheet", "Paper trading",
 "Chart dashboard", "Chrome extension", "PWA (install hone wala web app)", "WhatsApp Business auto-reply", "Telegram order bot", "Roz ki report bot",
 "Fees reminder bot", "Google Business Profile setup", "Search Console setup", "Meta Pixel setup", "Shiprocket setup", "COD order confirm",
 "Bulk product descriptions", "Resume", "PDF se Excel", "Excel formula theek", "Dashboard", "Company profile", "Proposal",
 "Personal portfolio", "Payroll", "Attendance", "Society maintenance", "Fees", "EMI", "SIP", "Due date",
}

# bhaari kaam (AI ke saath bhi zyada ghante) - (pattern, ghante)
HEAVY = [
 (r"kubernetes|grafana|terraform|disaster|migration plan|ansible", 5), (r"wordpress vm|nextcloud|ghost blog|n8n self|appwrite|supabase|firebase setup", 2.5),
 (r"erp|hospital|hotel booking|recruitment|help desk|document management", 22),
 (r"news / magazine|directory|job board|kirana online|jewellery|furniture|electronics|^hotel|property / real|^college|^school$", 12),
 (r"link-in-bio|personal blog|app download|startup landing|event / seminar|florist|bakery|^cafe", 4),
 (r"flutter|react native|course app|chat feature|community|video course|delivery boy|field staff", 30), (r"icon \+ splash|privacy policy|play store", 1.2),
 (r"explainer|animated logo|brand kit|channel intro|promo video|product video", 3),
 (r"\be-book\b|course outline|90 din|podcast", 4), (r"project report|business plan", 2),
 (r"monte carlo|walk-forward|optimiser|kai saal", 5), (r"newsletter tool|news digest", 3), (r"newsletter writing", 1.5),
 # madad/sikhana/care (bazaar fixed nahi, ghante se)
 (r"1 ghanta|python basic", 1), (r"interview taiyari \(30|sikhiye \(30|\(30 min\)", .5),
 (r"registration madad|cuet|\bjee\b|neet|counselling|education loan", .25),
 (r"website care \+ 3|social post care|seo care|online store care", 2), (r"care|posts - 4", 1),
 (r"screen-share", .3),
]
LIGHT = [(r"checklist|guide$|download|dekhne|size|status|link \+ qr|ideas|text$|bio$|headline", .05),
         (r"letter$|application$|format$|draft$|minutes format|patra$", .25)]
MADAD = {"naukri", "yojana", "padhai", "daftar", "senior", "guide", "micro", "care"}
# video nahi (sirf site/bot): sarkari pehchaan-patra, kanooni draft, jaati - organic bhi sambhal kar; ads mein bilkul nahi
NOVIDEO = r"pan card|passport|voter id|driving licence|jati|ayushman|affidavit|legal notice|police|kiraynama|duplicate document|bank kyc|insurance claim"
# bazaar ka 'kam se kam' chhota (CSC ₹25+GST) - 'sasta' wali kati hui keemat video/site par NAHI
NOSTRIKE = {"naukri", "yojana", "padhai"}
PFX = {"cloud": "cl", "devops": "dv", "data": "db", "domain": "dm", "smart": "sm", "bot": "bo", "web": "we", "calc": "ca", "soft": "so",
       "app": "ap", "excel": "ex", "docs": "dc", "design": "de", "content": "co", "ecom": "ec", "trade": "tr", "micro": "mi", "guide": "gu",
       "fix": "fx", "care": "cr", "local": "lo", "naukri": "na", "yojana": "yo", "padhai": "pa", "daftar": "df", "senior": "se"}
SUFFIX = {"web": " website", "calc": " calculator", "soft": " software"}


def _nice(p):
    steps = [10, 15, 19, 29, 39, 49, 59, 69, 79, 99, 129, 149, 199, 249, 299, 349, 399, 449, 499, 599, 699, 799, 899, 999, 1199, 1299, 1499,
             1799, 1999, 2499, 2999, 3499, 3999, 4499, 4999, 5999, 6999, 7999, 8999, 9999, 12999, 14999, 19999, 24999, 29999]
    for s in steps:
        if s >= p:
            return s
    return int(round(p, -3)) - 1


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:28]


def items(existing):
    """existing = purane 112 (name list) -> naye item dict (svc_gen_rates.build jaisa)."""
    src = json.loads((pathlib.Path(__file__).parent / "svc_more_src.json").read_text(encoding="utf-8"))
    old = [re.sub(r"\s*\(.*?\)", "", n).lower() for n in existing]
    out, seen = [], set()
    rows = [(SRC_CAT[c["n"]], n) for c in src for n in c["items"]] + [(k, n) for k, v in ADD.items() for n in v]
    for cat, name in rows:
        name = name.strip()
        if name in SKIP or not name or name.endswith(" r"):
            continue
        name = RENAME.get(name, name)
        if cat in SUFFIX and SUFFIX[cat].strip() not in name.lower():
            name += SUFFIX[cat]
        base = re.sub(r"\s*\(.*?\)", "", name).lower()
        if any(difflib.SequenceMatcher(None, base, o).ratio() > .86 for o in old):
            continue
        T = CATS[cat]
        low = name.lower()
        h, heavy = T[2], False
        for pat, hh in HEAVY:
            if re.search(pat, low):
                h, heavy = hh, True
                break
        else:
            if cat in MADAD or cat == "docs":
                for pat, hh in LIGHT:
                    if re.search(pat, low):
                        h = min(h, hh) if cat != "docs" else hh
                        break
        floor = max(10, round(h * HOUR * BUF / 10) * 10 if h >= .2 else 10)
        if cat in MADAD and not heavy:
            lo, f = T[3], T[5]
        else:
            lo, f = max(T[3], int(round(h * 3 * 500, -2))), (T[5] if cat not in MADAD else .3)
        hi = max(T[4], lo * 4)
        price = _nice(max(floor, h * HOUR * BUF, lo * f))
        iid = f"{PFX[cat]}-{_slug(base)}"
        while iid in seen:
            iid += "x"
        seen.add(iid)
        kw = sorted(set(w for w in re.findall(r"[a-z0-9]{3,}", low) if w not in ("aur", "par", "the", "and", "madad", "setup", "sikhiye", "theek")))
        it = {"id": iid, "cat": cat, "name": name, "price": price, "floor": floor, "max": price * 4, "market": [lo, hi], "hours": h,
              "days": T[6], "risk": T[7], "kw": kw, "new": 1}
        if re.search(NOVIDEO, low):
            it["novideo"] = 1
        if cat in NOSTRIKE:
            it["nostrike"] = 1
        if price < floor:
            raise SystemExit(f"FLOOR GALTI {iid}")
        out.append(it)
    # v3.9.2: owner ki list mein ek hi naam do dabbon mein (Cover letter, RTI draft, Product photo edit...) - ek hi rakho, sasta wala
    best = {}
    for it in out:
        k = re.sub(r"\s*\(.*?\)", "", it["name"]).lower().strip()
        if k not in best or it["price"] < best[k]["price"]:
            best[k] = it
    keep = {id(v) for v in best.values()}
    return [it for it in out if id(it) in keep]


def cats():
    """naye dabbe + video ke liye shabd (group, shot, q1, q2, fayda, bolne_ka)."""
    return {k: {"title": v[0], "sub": v[1], "v": [v[8], v[9], v[10], v[11], v[12], v[13]]} for k, v in CATS.items()}
