# MARKET RATES + kya ads kar sakte hain (v3.9.2, 24 Nov 2026)

Ye file isliye hai ki video/site par "बाज़ार ₹X+" aur "X% तक सस्ता" ka **aadhar likha rahe** (CCPA 2022: dawa saabit karne layak ho).
Rate badalne se pehle ye file + `app/scripts/svc_more_items.py` (CATS) + `svc_gen_rates.py` padho. `svc_rates.json` haath se KABHI nahi (sha).

## 1. Daam ka niyam (sab 1030 kaam par)
- **Floor** = AI ke saath lagne wale ghante x ₹300 x 1.2 = **₹360/ghanta**. Hamara rate isse neeche kabhi nahi (paise bachein).
- **Bazaar (market) kam se kam** = (a) neeche ki research ka kam se kam rate, ya (b) bina AI ~3 guna samay x ₹500/ghanta (aam freelancer) - jo bada.
- **Hamara rate** = max(floor, bazaar x hisse ka factor) -> "…9" wala saaf rate (19, 29, 49, 99, 129, 199, 249, 299, 399, 499, 699, 999, 1499…).
  Factor: website .25, app .2, madad/sarkari form .45, buzurg .5, guide .45, care .2, baaki .3 (yani bazaar ke kam se kam rate ka ~20-45%).
- Purane 112 kaam ke rate **nahi badle**.
- **Kati keemat (strike) sirf jab bazaar > hamara rate** aur hissa `nostrike` na ho. Sarkari naukri/yojana/school form (CSC ₹25+GST, cyber cafe
  ₹100-150) par "sasta" ka dawa NAHI - sirf "₹49 se".

## 2. Research (24 Nov 2026, web search - har 6 mahine dobara dekho)
| Kaam | Bazaar mein mila | Hamara (se) |
|---|---|---|
| Chhoti business website | ₹5k-50k (Hostinger blog), freelancer ₹3k-15k (dev.to), basic static ₹10k-25k (upGrowth) | ₹2,999 |
| Online form (CSC / cyber cafe) | CSC ₹25+GST sarkari tay; cyber cafe ~₹100-150 | ₹49 (sasta ka dawa nahi) |
| ITR | CA ₹1,000-2,500 (ITR-1); online ₹500-1,000; ClearTax ₹299 se | ₹299 madad |
| Telegram/WhatsApp bot | Fiverr India $20-400; WhatsApp chatbot agency ₹25k-75k | ₹1,199 se |
| Logo | beginner ₹500-2,000 / ₹1,000-10,000 | purana rate |
| VPS / server setup | Fiverr $50-200; IndiaMART ₹500-599 | ₹699 |
| Resume | ₹500-2,000 budget; Topmate median ~₹704 | ₹10 / ₹149 |
| Reel editing | ₹170-800 / reel | ₹499 |
| Excel dashboard | freelancer bid ₹750-1,050; Fiverr $50-400 | ₹399 |
| Mobile app | freelancer ₹500-2,000/ghanta; simple MVP ₹1.5L+ | ₹4,499 se (WebView/PWA) |
| SEO blog | ₹2,000-5,000 / 1000 shabd | ₹699 |
| PineScript | Fiverr $50-200 | ₹1,499 |

## 3. Kya NAHI liya / chhupaya (wajah)
- **Broker par apne aap order lagane wale bot** (t-algo, t-crypto + owner list ke order/stop-loss/square-off/token/static-IP/broker-API/24x7 trading VM):
  SEBI circular 4 Feb 2025 - retail algo dene wala exchange-empanelled hona chahiye. `hide` = site/video/quote mein nahi (rate list mein record).
  Bacha: indicator, alert, chart, backtest, journal, calculator, paper-trading, scanner (aapke niyam), option payoff.
- **PDF merge/split/compress/convert, background hatana** - log khud 1 click mein (owner 24 Nov).
- **"AI" naam wale kaam** -> "smart / chatbot" naam (owner niyam; video audit AI/ChatGPT/Gemini rokta).
- Owner ki list kati thi (17.40 "Website quick r" par) - 17.41-50 aur 18-26 hum ne likhe (dekho svc_more_items.ADD). Owner ki asli list aaye to ADD badlo.

## 4. Kya ads / promote kar sakte hain (platform niyam)
| Hissa | Apni video (organic, roz wali) | Paid ads (Google/Meta) |
|---|---|---|
| Website, app, Excel, design, content, bot, cloud, devops, data, domain, ecom, local, care | ✅ | ✅ (sach, likhit quote) |
| Sarkari naukri / yojana / school form madad | ✅ + "sarkari vibhag nahi" line (description mein) | ❌ Google: government documents/services ads ke liye certification; Meta bhi sakht - mat chalao |
| PAN/passport/voter/DL/jati/Ayushman guide, kanooni draft, bank KYC, insurance claim, police shikayat | ❌ video nahi (`novideo`), sirf site/bot | ❌ |
| Printer/phone/laptop screen-share madad | ✅ | ❌ Google: third-party consumer tech support ads mana |
| Trading tools (order bot ke bina) | ✅ + "tip/signal nahi, jokhim" line | ❌ Google financial services verification ke bina nahi |
| Crypto | ❌ (ASCI VDA niyam - bhaari disclaimer) | ❌ |
- YouTube "paid promotion" dabba: apne brand ki apni video par zaroori nahi.

## 5a. '90% discount' kyun nahi (24 Nov jaanch)
- Rate list mein bazaar se 90%+ kam sirf 1 kaam (₹10 Resume) hai; 80%+ = 12, 70%+ = 198 (20%), 60%+ = 884. ASCI ke 'up to' niyam mein sabse bada % kaafi kaamon par lagu hona chahiye - isliye video/post par **`usp_pct()`** = sabse bada 10 ka kadam jahan kam se kam 10% kaam utne saste (aaj **70%**). Rate badlenge to apne aap badlega.
- 'Discount' shabd nahi - hamara pehle ka koi ooncha rate nahi tha (jhootha 'pehle/ab' mana). 'बाज़ार से X% तक कम' + 'शुरुआती दाम' (sach: kaam badhne par rate badal sakte hain, terms#rate).

## 5. Shabd (future-proof, galat vaada nahi)
- ✅ "₹49 se शुरू", "* शर्तें लागू · पूरी शर्तें: sabhisaab.com/terms" (har frame par neeche, wahi bhasha, padhne layak - ASCI/CCPA).
- ✅ Sale: sirf asli tareekh ke saath ("इस हफ़्ते · 30/11 तक").
- ❌ "Limited time / सीमित समय / जल्दी करें / only today / offer khatam / बस कुछ ही" - offer lambe chalenge, ye jhoothi jaldbaazi hogi
  (CCPA Dark Patterns 2023). Video audit (BAN) inhe rokta hai.
- ❌ "Guarantee", "selection pakka", "profit", "100% approve".
- Terms par `#rate` hissa (8A) = "sharten laagu" ka poora matlab.
