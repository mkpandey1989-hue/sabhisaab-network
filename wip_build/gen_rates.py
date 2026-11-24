"""Sab Hisaab Services - rate list generator (v1, 23 Nov 2026).
Niyam: floor = ghante x Rs300 x 1.2 (kabhi isse neeche nahi). price >= floor. Market range sirf tulna ke liye.
risk: G=seedha, Y=sharton ke saath, R=nahi (list mein nahi aata, sirf matcher mana karne ke liye)."""
import hashlib
import json
import sys

HOUR = 300
BUF = 1.2

C = {
 "micro":   ("⚡ Chhote kaam (₹10 se)", "Same din, 100% advance"),
 "web":     ("🌐 Website aur online dukaan", "Aapke naam par, tez, mobile par saaf"),
 "calc":    ("🧮 Calculator aur tools", "188 tool banane ka anubhav"),
 "soft":    ("🧾 Business software (billing, stock, khata)", "Tally/billing app jaisa, aapke hisaab se"),
 "bot":     ("🤖 Bot aur automation", "WhatsApp/Telegram/Sheet - kaam apne aap"),
 "trade":   ("📈 Trading tools (aapki apni strategy)", "Tip/signal nahi - sirf aapke rules ka code"),
 "design":  ("🎬 Video, design aur reels", "Brand jaisa look, bina shoot"),
 "content": ("✍️ Content aur SEO", "Google par dikhne ki taiyari"),
 "ecom":    ("🛒 E-commerce setup", "Order, payment, shipping"),
 "docs":    ("📄 Excel, PDF aur documents", "Ghanton ka kaam minuton mein"),
 "setup":   ("🛠️ Setup aur install", "VM, domain, hosting, broker API - aapke account par"),
 "guide":   ("🎓 Sikhana / guide (screen-share)", "Aap khud karein, hum saath batayein"),
 "fix":     ("🔧 Theek karna (repair)", "Jo toota hai, wo chalu"),
 "care":    ("🔁 Har mahine dekhbhal", "Kabhi bhi band, sirf chalne tak charge"),
}

# (id, cat, naam, price, market_lo, market_hi, ghante, din, risk, keywords)
R = [
 # micro (owner 24 Nov: photo/PDF/QR jaise kaam log khud AI se kar lete - hataye. Sabse chhota = Resume ₹10)
 ("m-resume","micro","Resume (taiyaar format mein, ₹10)",10,100,1500,.03,"Same din","G","resume cv biodata naukri job"),
 ("m-form","micro","Online form bharne mein madad (koi bhi portal)",49,50,200,.12,"Same din","G","form bharna online form apply aavedan registration"),
 ("m-letter","micro","Application / letter / notice / shikayat patra",29,100,500,.08,"Same din","G","application letter notice patra shikayat"),
 ("m-biodata","micro","Shaadi biodata design",49,200,1500,.12,"1 din","G","biodata shaadi"),
 ("m-formula","micro","Excel/Sheet formula theek karna",49,100,500,.12,"Same din","G","excel formula sheet"),
 ("m-maps","micro","Google Maps par dukaan check + sujhav",49,200,1000,.12,"Same din","G","google maps location"),
 ("m-bill","micro","Bill / quotation format (Excel/Word)",99,300,1500,.25,"1 din","G","bill quotation format"),
 ("m-rate","micro","Rate card / price list design",99,300,1500,.25,"1 din","G","rate card price list"),
 ("m-gform","micro","Google Form banana (registration, feedback)",99,300,1500,.25,"1 din","G","google form"),
 ("m-thumb","micro","1 thumbnail",99,300,1500,.25,"1 din","G","thumbnail"),
 ("m-poster","micro","1 poster / banner",99,300,2000,.25,"1 din","G","poster banner"),
 ("m-resume2","micro","Resume pro design + LinkedIn bio",149,500,3000,.4,"1 din","G","resume pro design linkedin"),
 ("m-invite","micro","Digital shaadi / event card",149,500,3000,.4,"1 din","G","invite card shaadi event"),
 # v3.8.0 (owner 24 Nov): madad wale kaam sabse upar - customer saath, OTP/password sirf customer. Sab AI + owner se 100% ho sakne wale.
 ("m-scholar","micro","Scholarship form madad (NSP / rajya portal)",99,150,500,.25,"Same din","G","scholarship nsp chhatravriti vazifa form"),
 ("m-yojana","micro","PM Kisan / ration / pension online apply madad",99,100,500,.25,"Same din","G","pm kisan kisan ration pension yojana vridha vidhwa form apply"),
 ("m-exam","micro","Exam / naukri / admission form madad (photo-sign size ke saath)",49,50,300,.12,"Same din","G","exam naukri bharti admission vacancy recruitment form"),
 ("m-docs","micro","Documents scan, photo-sign size theek (form ke liye)",29,50,200,.08,"Same din","G","photo size signature sign kb resize document"),
 ("m-itr1","micro","ITR-1 madad (salary/pension) - aap login karein, hum saath bhariye",299,899,1500,.6,"Same din","G","itr income tax return form16 salary pension refund"),
 ("m-itr2","micro","ITR-2 / ITR-4 madad (kathin case CA ko)",699,1440,4000,1.5,"1-2 din","G","itr2 itr4 capital gain business presumptive"),
 ("m-mobile","micro","Mobile / computer madad (call ya screen-share par)",49,100,500,.12,"Same din","G","mobile phone laptop computer setting setup upi email printer slow whatsapp app"),
 ("m-study","micro","School / college project, PPT, assignment ka design",99,300,1500,.25,"1 din","G","project ppt presentation assignment school college"),
 ("m-typing","micro","Hindi / English typing (1 page)",19,30,100,.05,"Same din","G","typing type hindi english page"),
 ("m-any","micro","Koi bhi chhota computer / phone ka kaam (likh kar batayein)",49,100,1000,.12,"Baat karke","G","koi bhi kuch bhi chhota kaam help madad computer phone"),
 # web
 ("w-card","web","Digital visiting card / mini site",999,2000,6000,2.5,"1 din","G","visiting card digital card"),
 ("w-1page","web","1-page dukaan / clinic / coaching website + WhatsApp button",2999,10000,25000,7,"2-3 din","G","website site dukaan shop 1 page landing"),
 ("w-land","web","Ad landing page",2499,5000,15000,6,"2 din","G","landing page ad"),
 ("w-5page","web","5-page business website (SEO ready)",7999,30000,80000,18,"5-7 din","G","business website 5 page"),
 ("w-bi","web","Hindi + English website",9999,35000,90000,22,"7 din","G","hindi english bilingual"),
 ("w-shop","web","Online dukaan: product list + WhatsApp/UPI order",4999,15000,50000,12,"4-5 din","G","online dukaan store catalogue order"),
 ("w-book","web","Booking / appointment page (salon, clinic, homestay, taxi)",3999,10000,30000,9,"3-4 din","G","booking appointment homestay taxi"),
 ("w-port","web","Portfolio / resume website",1999,5000,15000,5,"2 din","G","portfolio resume website"),
 ("w-temple","web","Mandir / samiti page + daan raseed",3499,8000,25000,8,"3 din","G","mandir samiti daan"),
 ("w-school","web","School / coaching site + result / admit card",6999,25000,70000,16,"5-7 din","G","school coaching result admit"),
 ("w-wed","web","Shaadi invite website",1499,3000,10000,3.5,"2 din","G","shaadi wedding invite"),
 ("w-menu","web","Restaurant QR menu + order",2999,8000,25000,7,"3 din","G","restaurant menu qr order"),
 ("w-gmb","web","Google Business Profile setup + local SEO",1499,2000,6000,3.5,"1-2 din","G","google business gmb maps"),
 ("w-pwa","web","Website ko Android app (PWA) banana",2499,8000,30000,6,"2 din","G","app android pwa"),
 # calc
 ("c-calc","calc","Branded calculator (EMI/SIP/GST/solar/koi bhi formula)",1499,5000,15000,3.5,"1-2 din","G","calculator emi sip gst solar"),
 ("c-quote","calc","Quotation / estimate PDF app",2999,8000,25000,7,"3 din","G","quotation estimate pdf app"),
 ("c-quiz","calc","Eligibility checker / quiz (lead ke liye)",1999,5000,15000,4.5,"2 din","G","quiz eligibility checker"),
 ("c-widget","calc","Website mein lagne wala widget",999,3000,10000,2.5,"1 din","G","widget embed"),
 ("c-excelweb","calc","Excel sheet ko web tool banana",2499,8000,25000,6,"2-3 din","G","excel web tool"),
 ("c-pack","calc","Package / price builder (customer khud chune)",2499,6000,20000,6,"2-3 din","G","package builder price"),
 ("c-ext","calc","Chrome extension (roz ka kaam 1 click)",3999,10000,40000,9,"3-4 din","G","chrome extension"),
 # soft
 ("s-bill","soft","GST billing / invoice app (phone + PC)",3999,8000,30000,9,"3-4 din","G","billing gst invoice bill app tally"),
 ("s-stock","soft","Stock / inventory + low-stock alert",4999,10000,40000,12,"4-5 din","G","stock inventory maal"),
 ("s-khata","soft","Khata / udhaar ledger app",2999,6000,20000,7,"3 din","G","khata udhaar ledger"),
 ("s-salary","soft","Staff attendance + salary app",3999,8000,30000,9,"3-4 din","G","salary attendance staff"),
 ("s-pos","soft","Dukaan POS (bill + stock + roz ka hisaab)",7999,25000,80000,18,"7 din","G","pos counter billing software"),
 ("s-society","soft","Society / PG maintenance hisaab",3499,8000,30000,8,"3 din","G","society maintenance pg"),
 ("s-fee","soft","School / coaching fee tracker",2999,8000,30000,7,"3 din","G","fee tracker school coaching"),
 ("s-crm","soft","Chhota CRM (lead, follow-up, Sheet)",4999,15000,50000,12,"4-5 din","G","crm lead follow"),
 ("s-tallyx","soft","Tally / Busy data → Excel / dashboard",2999,8000,30000,7,"3 din","G","tally busy export dashboard"),
 ("s-custom","soft","Pura custom software (aapke hisaab se)",14999,50000,300000,40,"10-20 din","G","custom software app erp"),
 ("s-einv","soft","E-invoice / e-way bill jodna (GSP ke through)",9999,25000,80000,24,"7-10 din","Y","e-invoice eway bill gsp"),
 # bot
 ("b-wa","bot","WhatsApp Business auto-reply + catalogue",999,3000,10000,2.5,"1 din","G","whatsapp auto reply catalogue"),
 ("b-faq","bot","24x7 FAQ chatbot (aapki price list par)",3999,10000,30000,9,"3-4 din","G","chatbot faq"),
 ("b-tg","bot","Telegram alert / order bot",2499,8000,25000,6,"2-3 din","G","telegram bot alert"),
 ("b-sheet","bot","Form → Google Sheet → turant alert",1499,3000,10000,3.5,"1-2 din","G","form sheet alert lead"),
 ("b-remind","bot","Fee / renewal reminder (apne customers ko)",2499,5000,15000,6,"2 din","G","reminder fee renewal"),
 ("b-report","bot","Roz ki bikri / lead report bot",2499,6000,20000,6,"2-3 din","G","daily report summary"),
 ("b-igdm","bot","Instagram comment → DM (Meta niyam ke andar)",1999,4000,12000,4.5,"2 din","G","instagram comment dm"),
 ("b-review","bot","Google review link sabko (achha-bura dono)",1499,3000,10000,3.5,"1-2 din","G","review google"),
 ("b-voicein","bot","Inbound call booking bot (sirf aane wali call)",7999,15000,40000,18,"7 din","Y","call voice receptionist"),
 # trade
 ("t-pine","trade","PineScript indicator (aapke rules)",1499,3000,15000,3.5,"2 din","Y","pinescript indicator tradingview"),
 ("t-back","trade","Strategy backtest report",1999,5000,20000,4.5,"2-3 din","Y","backtest strategy"),
 ("t-alert","trade","TradingView alert → Telegram",1999,3000,10000,4.5,"2 din","Y","tradingview alert telegram"),
 ("t-journal","trade","Trade journal + P&L sheet",1499,3000,8000,3.5,"2 din","Y","journal pnl trade"),
 ("t-paper","trade","Paper-trading bot (bina asli paisa)",3999,10000,30000,9,"4-5 din","Y","paper trading"),
 ("t-algo","trade","Aapki strategy ka bot - AAPKE account/static IP par",5999,15000,50000,14,"7 din","Y","algo bot broker api dhan fyers zerodha angel delta strategy"),
 ("t-chart","trade","Personal chart / OI dashboard (aapke broker data se, login ke peeche)",4999,10000,40000,12,"5 din","Y","chart oi pcr dashboard scanner"),
 ("t-crypto","trade","Crypto (Delta/Binance) strategy bot - aapke account par",5999,15000,50000,14,"7 din","Y","crypto delta binance bot"),
 # design
 ("d-logo","design","Logo + brand kit",999,3000,15000,2.5,"1-2 din","G","logo brand kit"),
 ("d-post30","design","30 din ke festival / offer post",1999,5000,15000,5,"3 din","G","festival post social"),
 ("d-thumb10","design","10 thumbnail pack",999,3000,10000,2.5,"2 din","G","thumbnail pack"),
 ("d-promo","design","Product photo se promo video",1499,5000,20000,3.5,"2 din","G","promo video product"),
 ("d-reels30","design","30 reels pack (script + video)",4999,15000,50000,12,"5-7 din","G","reels pack video"),
 ("d-shorts","design","Lambi video → 15 shorts + caption",2999,8000,25000,7,"3 din","G","shorts clip caption"),
 ("d-photo","design","Studio jaisi product photo (10)",999,3000,10000,2.5,"2 din","G","product photo studio"),
 ("d-script","design","30 reel script + hook",999,3000,10000,2.5,"2 din","G","script hook reel"),
 # content
 ("x-blog5","content","5 SEO blog (insaan ka edit)",1999,5000,15000,5,"3 din","G","blog seo article"),
 ("x-audit","content","Website SEO / AdSense readiness audit",999,3000,10000,2.5,"1-2 din","G","seo audit adsense"),
 ("x-gsc","content","Search Console + sitemap + schema setup",999,3000,8000,2.5,"1 din","G","search console sitemap schema"),
 ("x-ebook","content","E-book / guide PDF",1999,5000,15000,5,"3 din","G","ebook guide pdf"),
 # ecom
 ("e-store","ecom","Online store setup (mobile par)",5999,15000,50000,14,"5 din","G","store shopify woocommerce online"),
 ("e-pay","ecom","Razorpay / Cashfree / UPI gateway (aapke account mein)",1499,3000,10000,3.5,"1-2 din","G","payment gateway razorpay cashfree"),
 ("e-ship","ecom","Shiprocket / courier setup",1499,3000,8000,3.5,"1-2 din","G","shiprocket courier shipping"),
 ("e-cod","ecom","Order confirmation bot (COD kam)",2499,5000,15000,6,"2-3 din","G","cod order confirm"),
 ("e-desc","ecom","50 product description",1999,5000,15000,5,"3 din","G","product description listing"),
 ("e-margin","ecom","Marketplace profit / fees sheet",999,2000,6000,2.5,"1 din","G","margin profit amazon flipkart meesho"),
 ("e-pixel","ecom","Meta Pixel + CAPI + GA4",1999,4000,12000,4.5,"2 din","G","pixel capi ga4 tracking"),
 # docs
 ("p-extract","docs","PDF bill / statement → Excel",1499,4000,15000,3.5,"1-2 din","G","pdf excel extract statement"),
 ("p-proposal","docs","Proposal / quotation PDF generator",1999,5000,15000,4.5,"2 din","G","proposal pdf"),
 ("p-deck","docs","Company profile / pitch deck",1999,5000,20000,5,"2-3 din","G","deck profile presentation"),
 ("p-cert","docs","Form → certificate PDF apne aap",1499,3000,10000,3.5,"2 din","G","certificate"),
 ("p-dash","docs","Google Sheet / Excel dashboard",1999,5000,20000,4.5,"2-3 din","G","dashboard sheet excel"),
 ("p-cv","docs","ATS resume + LinkedIn (naukri ke liye poora)",499,1500,5000,1.2,"1 din","G","ats resume linkedin"),
 ("p-sheetapp","docs","Google Sheet se app banana",2499,6000,20000,6,"2-3 din","G","sheet app appsheet"),
 # setup
 ("u-domain","setup","Domain + free hosting setup",299,1000,3000,.7,"1 din","G","domain hosting"),
 ("u-vm","setup","VM / server install (aapke account par)",999,3000,10000,2.5,"1 din","G","vm server install oracle aws vps"),
 ("u-broker","setup","Broker API + static IP setup (aapke account par)",999,3000,8000,2.5,"1 din","Y","broker api static ip"),
 ("u-email","setup","Business email + domain jodna",499,1500,5000,1.2,"1 din","G","business email"),
 ("u-move","setup","Website Cloudflare par shift (hosting kharcha bachao)",1499,3000,8000,3.5,"1-2 din","G","hosting shift migrate cloudflare"),
 # guide
 ("g-hour","guide","1 ghanta screen-share guide (Meet/AnyDesk)",499,800,2500,1,"Tay samay","G","guide sikhana screen share help"),
 ("g-botself","guide","Apna bot khud chalana sikhiye (3 session)",1299,3000,10000,3,"1 hafta","G","bot sikhna training"),
 # fix
 ("f-site","fix","Website / form / page theek karna",499,1000,5000,1.2,"Same/1 din","G","fix repair error website broken"),
 ("f-speed","fix","Website speed + mobile theek",1499,3000,10000,3.5,"1-2 din","G","speed slow mobile"),
 ("f-index","fix","Google index nahi ho raha - jaanch + theek",999,2000,8000,2.5,"1-2 din","G","index google not indexed"),
 ("f-bot","fix","Bot / script error theek",499,1000,5000,1.2,"Same/1 din","G","bot error script fix"),
 # care
 ("k-basic","care","Basic: uptime check + backup (mahina)",149,500,1500,.4,"Har mahina","G","maintenance care basic"),
 ("k-care","care","Care: + 3 chhote badlav (mahina)",349,1000,3000,.9,"Har mahina","G","maintenance care"),
 ("k-pro","care","Pro: + 8 badlav + report (mahina)",749,2000,6000,2,"Har mahina","G","maintenance pro"),
]

RED = [("Google Maps / data scraping, kisi ka phone-email nikalna", "scrap|scraping|scraper|data nikal|number nikal|email nikal|phone list|lead list kharid"),
       ("Cold email / bulk WhatsApp / spam", "bulk whatsapp|bulk sms|bulk message|cold email|mass message|spam"),
       ("Nakli review / followers / likes", "fake review|nakli review|followers badha|followers kharid|likes kharid|fake followers"),
       ("Trading tip / signal / kisi ka account chalana", "signal do|signal bech|tip do|mera account chalao|account chala do|profit guarantee|pakka profit"),
       ("Hacking / copy site / betting / loan app", "hack|hacking|password tod|clone kar|copy kar do site|betting|satta|gambling|loan app|casino"),
       ("Bina consent outbound AI call", "outbound call|robocall|auto call kar|cold call"),
       ("Aadhaar/PAN mein badlav hum khud karein / tatkal ticket bot", "aadhaar badal|aadhar badal|aadhaar update kar do|aadhar update kar do|aadhaar mein naam badal|tatkal bot|tatkal ticket bot"),
       ("Haath/hardware repair ya ghar aakar kaam", "mobile repair|phone repair|screen badal|battery badal|ghar aakar|ghar aa kar|ghar pe aao|hardware repair")]


def build():
    items, bad = [], []
    for (i, c, n, p, lo, hi, h, d, r, kw) in R:
        floor = max(10, round(h * HOUR * BUF / 10) * 10 if h >= .2 else 10)   # <0.2 ghante wale = ₹10 floor (template kaam)
        if p < floor:
            bad.append(f"{i}: price {p} < floor {floor}")
        items.append({"id": i, "cat": c, "name": n, "price": p, "floor": floor, "max": p * 4,
                      "market": [lo, hi], "hours": h, "days": d, "risk": r, "kw": kw.split()})
    if bad:
        sys.exit("FLOOR GALTI:\n" + "\n".join(bad))
    body = {"version": "2026-11-24.1", "hour_rate": HOUR, "buffer": BUF,
            "cats": {k: {"title": v[0], "sub": v[1]} for k, v in C.items()},
            "items": items, "red": [{"name": a, "kw": b.split("|")} for a, b in RED],
            "discount": {"brand": 10, "ref": 10, "care": 5, "max": 25, "small_cap_under": 300, "small_cap": 50, "urgent": 50}}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True)
    body["sha"] = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return body


if __name__ == "__main__":
    b = build()
    out = sys.argv[1] if len(sys.argv) > 1 else "svc_rates.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(b, f, ensure_ascii=False, indent=1)
    print(len(b["items"]), "kaam,", len(b["cats"]), "dabbe, sha", b["sha"])
