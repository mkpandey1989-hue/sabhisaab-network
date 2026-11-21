# TRAFFIC_PLAN - impression aur click kaise badhenge (12 Nov 2026, [FABLE 5.2] Claude Fable 5.2) - NAYA AI: AI_START ke turant baad YE padho

Owner ka lakshya: roz 10-20 hazaar impression, 2-3 hazaar click. Owner ki maang: "ZIP lagate hi result".
SACH (chhupana nahi): koi ZIP ye nahi kar sakti. Google naya/badla page dobara padhne mein 2-14 din leta hai aur nayi site ko
bharosa dene mein mahine. Is file mein wahi likha hai jo sach mein kaam karta hai, kis kram mein, aur kya KABHI nahi karna.

## 1. Aaj ki asli haalat (bot ki KEYWORDS.md + STATUS.md, 12 Nov)
- Google par 263 page index. 28 din mein kul ~45 impression, 0 click, 49 alag shabd. Website par ~10 log/hafta.
- Jahan Google hamein dikha raha hai (position): "10 mutthi in square feet" 1, "ek nali kitna hota hai" 1, "chakravriddhi byaj" 1,
  "today weather report in hindi" 6, "gb vs mb" 6, "24 lakh personal loan emi calculator" 7, "1 tb is how many mb" 8,
  "500 me 238 kitna percent" 11, "N lakh personal loan emi" 11-22, "tb to gb / mb to gb" 12-17, "49 roman number" 27.
- Sabse zyada impression wala shabd "ukfr login" (26) hai - log sarkari portal dhoondh rahe the, hamein nahi (isliye "chhodo").
- Nateeja: Google hamein pehchaanta hai par bahut kam mauka deta hai. Page ke andar ki cheezein (table, FAQ, schema, 1000+ shabd)
  PEHLE SE hain - bot ka kwfix roz naye shabd ka FAQ bhi jodta hai. Yani "page ke andar aur likho" se ab bada farak nahi aayega.

## 2. Impression kam kyun hain (asli wajah, bade se chhota)
1. BHAROSA/AUTHORITY: domain 21 Jul 2026 ki, bahar se koi asli link/zikr nahi. Calculator wale shabdon par Groww, ClearTax, bank,
   Housing/MagicBricks baithe hain. Bina bahari sanket ke Google nayi site ko page 2-5 par rakhta hai.
2. FOCUS: 270 page 6 alag vishay par (nivesh, loan, sehat, trading, converter, rozana). Google ke liye site "kis cheez ki" hai ye
   saaf nahi. Jeet sirf pahadi/zameen/desi sawalon par mil rahi hai.
3. BHASHA: poori site Roman Hinglish mein. Log ya English mein khojte hain ("1 nali in square feet") ya Devanagari mein
   ("1 नाली में कितने वर्ग फुट"). Devanagari text site par tha hi nahi (sirf /jawab par) - wo saare sawal hamare haath se bahar.
4. TITLE: kai title sirf tool ka naam the ("Personal Loan EMI Calculator | Sab Hisaab") - jis shabd par rank hai wo title mein nahi.
5. Bing: purane over-submit ke baad site hati hui; v3.1.0 se dobara-bhejna band, ticket ka intezaar (19 Nov jaanch).

## 3. Owner ke "Zero se Advance Pro" blueprint ka faisla (har point)
| Point | Faisla | Wajah / haal |
|---|---|---|
| No bots, no self-click, ad button se door | ✅ sahi | pehle se niyam. AdSense abhi laga nahi |
| GSC impression ≠ paisa | ✅ sahi | paisa tab jab log site par aayein |
| 3-in-1 title (English + Hinglish + हिंदी) | 🟢 SEEMIT | Title 60 akshar ka (audit niyam). Teeno thoosna = keyword stuffing. Sahi tareeka: title mein 1 Devanagari vaakyansh + page par asli Hindi hissa. W12 mein nali page par TEST shuru |
| Hinglish + हिंदी heading/FAQ | 🟢 haan | asli vaakya, keyword ki list nahi (audit "Hindi me:" block ko stuffing maan kar rokta hai - sahi hai) |
| Title mein saal, bracket, "1 second mein" | ⚠️ sambhal kar | saal sirf wahan jahan cheez saal se badalti ho (tax, 8th CPC). Jhootha "2026-27" = fake taazgi (hamara niyam) |
| hreflang / alag /hi/ page | ⏸ abhi nahi | nayi site par ek hi URL mein dono lipi behtar (taaqat nahi bant-ti). T1 ke nateeje ke baad dobara socho |
| Regional zameen tool (bigha/kanal/biswa state-wise) | 🟢 YAHI ASLI MAUKA | Panne PEHLE SE hain (/bigha-kitna-hota-hai 'har rajya', /bigha-converter, /hectare-bigha-acre-converter, /nali-mutthi-converter). Kaam = inhe gehra + Hindi + srot (T1/T2), naye page nahi |
| State-wise bijli bill (UPCL/UPPCL), solar | 🟢 baad | /bijli-bill-calculator, /appliance-bijli-kharch-calculator, /pm-surya-ghar-solar-subsidy-calculator, /inverter-battery-backup-calculator pehle se hain. UPCL ki asli slab usi page par jodo (tariff har saal badalta hai -> factwatch) |
| 8th Pay Commission page | ✅ hai | /8th-pay-commission-calculator + /da-arrear-calculator. Fitment factor sarkar ne tay nahi kiya - "anumaan" likha rahe; har sarkari ghoshna par usi din update (T7) |
| "₹5000 SIP 10 saal" jaise ALAG page | ⛔ | ek-ek number ka alag page = scaled content/doorway (Google spam niti; Aug 2026 update). Usi page par TABLE - ho chuka |
| Programmatic SEO: 1 tool = 50 URL (/1-nali-in-gaj, /5-nali-in-sqft) | ⛔ KABHI NAHI | yahi doorway page hai. 263 index page par pehle hi seema par hain. Table + FAQ usi page par |
| Pre-calculated HTML table | ✅ ho chuka | loan, data, mutthi, percentage, roman par hai; W12: nali ki table. "Position 0 pakka" jhooth hai - mauka badhta hai bas |
| WebApplication + FAQPage schema | ✅ ho chuka | har tool page par. FAQ ka rich result Google ab aam site ko kam dikhata hai - schema nuksaan nahi karta |
| GSC regex filter | ✅ bot karta hai | KEYWORDS.md roz banta hai, kwfix ganit wale shabd ka FAQ khud jodta hai |
| Google Indexing API se 188 page | ⛔ KABHI NAHI | Google ke apne panne par likha hai: ye API sirf JobPosting aur live-video page ke liye; galat istemal par access band. (aaj jaancha) |
| Bing IndexNow | ✅ hai | sirf naya/badla URL (v3.1.0) |
| WhatsApp share ?nali=5 | 🟢 T6 | canonical base page par rahe, sitemap mein na jaye |
| Shorts mein "Google par Sab Hisaab search karo" | 🟢 TEST | pehle owner phone par dekhe ki "sab hisaab jawab" khojne par hum #1 aate hain ya nahi (owner list). Aayen to CTA mein jodenge. "10x authority" jhooth hai |
| Pahadi Hisaab par asli awaaz | ✅ P0 | AUDIT_11NOV hissa A1 - yahi YPP ka bhi raasta |
| Pinned comment + Related video | 🟢 owner | API se nahi hota; owner list mein |
| "7-15 din mein bada uchaal" | ⛔ jhootha vaada | ummeed neeche hissa 6 |

## 4. W12 (12 Nov) mein kya kiya - ye ek TEST hai, 26 Nov ko naapna
- /nali-mutthi-square-feet (hamara #1 page): title ab "Nali, Mutthi to Square Feet — 1 नाली कितने वर्ग फुट, गज" (55 akshar),
  description mein seedha jawab, NAYI nali table (1-50 nali -> sq ft, gaz, sq m, acre), asli Hindi hissa (3 paragraph, lang="hi"),
  3 Devanagari FAQ (schema ke saath), diagram ki galti theek (sq ft ke aage ₹ laga tha).
- /personal-loan-emi-calculator, /data-storage-converter, /mausam-weather: title + description mein wahi shabd jin par Google
  dikha raha hai (bot ki apni salah "title/description mein ye shabd saaf" - KEYWORDS.md).
- NAAPNA: 26 Nov ko KEYWORDS.md mein dekho - (a) nali page par Devanagari shabd aaye? (b) in 4 page ke impression/click badhe?
  Badhe to T1 chalao. Na badhe to title wapas mat badlo (2 hafte kam hain) - 10 Dec tak ruko.

## 5. AGLA AI: is kram mein kaam (har kaam chhota, ek-ek; niyam: hafte mein max 2 page badlo, naya page max 2/hafta)
T1 [26 Nov] W12 ka nateeja naapo (upar). Kaam kare to WAHI saancha (Devanagari title-tukda + asli Hindi hissa + 3 Hindi FAQ + number
   table) in page par, ek-ek: /bigha-kitna-hota-hai, /bigha-converter, /hectare-bigha-acre-converter, /nali-mutthi-converter, /area-guide,
   /zameen-kharidne-se-pehle-kagaz. Hindi text haath se likho (machine anuvaad nahi), number usi page ke.
T2 Zameen cluster gehra (naya page nahi): /bigha-kitna-hota-hai (har rajya wala panna pehle se hai) ka HAR number us rajya ke
   rajasv/bhulekh srot se dobara milao aur srot ka link page par do; jo pakka na mile use "alag-alag" likho. Phir usi par W12 wala
   Hindi saancha ("1 बीघा में कितने गज" jaise sawal). Ye sabse bada search-pool hai (bigha ke sawal poore Hindi belt mein).
T3 Pahadi cluster ke naye gehre panne (max 2/hafta, owner ke anubhav ke saath): khasra-khatauni padhna (bhulekh UK), dakhil-kharij
   ka kharcha/samay, bisi-mana-patha-naali purane naap, nali ka zila-wise farak, pahad mein circle rate kaise dekhein,
   Uttarakhand stamp duty (mahila chhoot), ghar ka naksha paas, Harela/Phooldei/Ghee Sankranti ki tithi har saal.
   Har page: asli sawal -> seedha jawab pehli line mein -> table -> sarkari srot -> Hindi hissa.
T4 [25 Nov, pehle se list mein W7] Top 5 tool ka English + Devanagari - T1 ke nateeje se tay karo: ek URL mein dono lipi, alag /hi/ nahi.
T5 Bahari sanket (bina iske T1-T4 adhoore): (a) har pahadi/zameen panne ka Pinterest pin + FB page post (bot: usi din), (b) YouTube
   lambi video ke description mein us vishay ka panna, (c) calculator embed widget (list mein W11, 30 Nov) - doosri site lagaye to link,
   (d) owner: Quora/Reddit par hafte mein 2 ASLI jawab jahan hamara panna sach mein kaam ka ho (link 1, copy-paste nahi).
   KABHI NAHI: link khareedna, comment mein link chipkana, PBN, directory spam.
T6 Share: calculator nateeje ka "WhatsApp par bhejo" link ?value= ke saath (canonical base, robots mein kuch nahi badalna).
T7 Mausam ke hisaab se pehle se taiyaari (bot ke calendar mein): 1 Feb Budget (tax panne 7 din mein), Mar-Jun result
   (percentage/CGPA), 8th CPC ki har sarkari ghoshna, Char Dham kapat tithi, rabi/kharif MSP. Jo pehle sahi panna deta hai wo dikhta hai.
T8 Chhantai: 16 Nov ke Request-indexing ke baad bhi jo aam tool index na ho (stopwatch, random number, number system) - owner se pooch
   kar noindex. Kam par achhe page = site ka star behtar.
T9 Brand-search CTA: owner ki jaanch ke baad (hissa 3).
Har kaam ke baad: scripts/audit.py ERROR 0, WORKPLAN mein 1 line, yahan "ho gaya" likho.

## 6. Kitna, kab (imaandaar andaaza - vaada nahi)
| Kab | Roz impression | Roz click | Shart |
|---|---|---|---|
| Aaj | ~2 | 0 | - |
| 30 din | 30-150 | 1-10 | W12 + T1 + T5(a,b) |
| 90 din | 300-1,500 | 15-100 | T2 + T3 (15-20 gehre panne) + asli awaaz wali video se log |
| 6 mahine | 2,000-8,000 | 100-600 | upar sab lagataar + 5-10 asli bahari link + Bing wapas |
| 9-12 mahine | 10,000-20,000 | 800-2,500 | ek vishay (zameen/pahadi/sarkari hisaab) ki "wahi site" ban jayein |
Ye tabhi jab har hafte kaam ho. Koi hafta chhoota to tareekh aage. Jaldi ka koi jaayaz raasta nahi; jo "7 din mein" bole wo ya
jhooth hai ya niti todna (aur phir AdSense/Search dono se bahar).

## 7. KABHI NAHI (ye list badalni nahi)
Ek-ek number ke alag page | Indexing API | bot/VPN/khud ke click | chhupa text ya keyword ki list | title mein 3 bhasha thoosna |
link khareedna/adal-badal | comment mein link ki baarish | jhoothi tareekh/"2026-27" | nakli reviewer/expert ka naam | doosri site ka text.
