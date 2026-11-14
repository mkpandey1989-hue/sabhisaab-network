# Uttarakhand project -> website (v3.3.0, 14 Nov 2026, Claude Opus 5.5)

Owner: "Uttarakhand ka total data website par, policy ke hisaab se; kuch delete nahi, duplicate nahi; ZIP bot ko bhejunga, bot roz
priority se khud live kare; mujhe message aaye kaunse URL GSC/Bing par index karne hain; traffic aaye aur ruke."

## 1. Kya bana
- Sroat: UK_Hub.docx = 14 merged docx (Hub + 13 zile), ~10.87 lakh shabd. Generator: app/scripts/ukgen/.
- 264 page: 1 hub (/uttarakhand), 11 hub-vishay, 13 zila guide (/almora-uttarakhand ...), 235 zila-vishay
  (/almora-pahadi-khana, /almora-ghumne-ki-jagah ... 18 vishay x 13 zile, Chamoli +1), 4 tool (Char Dham kharcha, Kapat countdown,
  Kumaoni-Garhwali shabdkosh, GK quiz - owner ke banaye, site ke saanche mein; JS waisa hi).
- Site par ~10.25 lakh shabd (template ke saath). Site par NAHI gaya hissa: 24,312 shabd kaam ka (owner ke paas UK_kaam_ki_baatein.md -
  verify list, kaunsa data nahi hai, khaali table, sudhaar) + 80,330 shabd faltu jo owner ki ijaazat (14 Nov) se hamesha ke liye hataya:
  'Search jo is section se match...' / 'Search Keywords:' suchi (keyword stuffing), keyword bank, spoke/SERP/Pinterest pack,
  editor checklist, JSON-LD dhanche, Word ka TOC, khaali placeholder table, purane /uttarakhand/x/ URL wali navigation table,
  'Publish se pehle...', 'aapki website...', 'Community Box' (site par aisa box nahi) jaise editor ke vaakya.
  Baaki ~14k token sirf nishaan the (Q1., A:, ✔, [verify], '(Headings 41 to 47)').
- 'Blueprint' (andar ka dastavez) -> 'mool sandarbh-suchi'; '(verify)' -> '(pushti karein)'.
- Duplicate: ek page par milte FAQ jode (272), doosre page par wahi FAQ/paragraph = pehle page ka link (146), 1 dohra paragraph
  hata (log mein). Site ke purane 272 page se bhi milaan.
- Hub ki zila-table ke 5 galat kshetrafal zile ke apne page (Census 2011) se sudhaare: Almora 3,144, Bageshwar 2,241,
  Chamoli 8,030, Pauri 5,329, Udham Singh Nagar 2,542 sq km.
- Har page: Article + BreadcrumbList (+FAQPage jahan 4+ FAQ) schema, canonical (bina www), lekhak, tareekh (live hone ka din),
  zila NIC site + uk.gov.in srot, 'Dhyan dein' (vaidya = ilaaj ki salah nahi, zameen = kanooni salah nahi, career = asli PYQ nahi).
- Pathak ke liye (koi data save/bheja nahi): '🎧 Ye page suniye' (phone ki apni awaaz, speechSynthesis) aur 70% padhne par
  chhota 'Agla padhiye' card (× se band). Link-jaal: zile ke saare vishay, doosre zile ka wahi vishay, 13 zile, hub-vishay, tool.
- Audit: pehle din ki site aur 33 din baad ki poori site (536 page) par asli scripts/audit.py: ERROR 0. (4 WARNING: 3 tool page
  1000 shabd se thode kam, GK page par table nahi.)

## 2. Bot (app/pagequeue.py)
- Queue ZIP (ukqueue/manifest.json + ukqueue/pages/*.html) -> dohri pushti -> data/pagequeue/. Site ZIP se pehle pehchaan.
- Roz 06:40 IST ke baad: rank kram, default 8 (max 10, us din ke doosre naye page gin kar). Har naye page par 3+ andar-link aur
  hub/zila page pehle. Live-nahi page ka link nahi (text rehta hai) - jaise page aate hain purane page mein link judte hain
  (tareekh wahi). Hub live hote hi 6 purane page (UKFR, nali-mutthi x2, bigha, agristack, guides) + homepage footer mein link.
- website._apply_zip ke audit gate se. Fail = kuch nahi, laal alert, kal dobara. IndexNow sirf aaj ke naye page.
- Deploy ke 25 min baad URL live jaanch -> owner ko list + GSC 'Request indexing' kram. Bing API apne aap (bing_plan 'naya page').
- Command: 'queue haal', 'queue roko/chalu', 'queue roz N', 'queue abhi' (sab dohri pushti).
- Kram: Din 1 hub + 7 bade zile, Din 2 baaki 6 zile, phir Ghumne ki jagah (13), Kaise pahunchein, Khana, Itihas... ~33 din.

## 3. Owner ke bheje 6 attachment (14 Nov) - har baat ka faisla
| Sujhaav | Faisla | Kyun |
|---|---|---|
| Hub-spoke link-jaal, 3-click gehrai, anchor mein asli naam | ✅ kiya | Home footer -> hub -> zila -> vishay |
| Upar 40-55 shabd seedha jawab + table | ✅ (content mein 'Seedha jawab' + table pehle se) | |
| Har page par asli tareekh, srot, disclaimer, privacy/terms link | ✅ | footer + srcbox |
| 'Listen' button (Web Speech) | ✅ | browser ki awaaz, kuch save nahi |
| 70% scroll par Next-read card | ✅ chhota, band hone wala | popup/interstitial nahi |
| Roz thoda live, sitemap mein asli lastmod | ✅ 8/din | NEW_PAGES_PER_DAY 10 |
| PII jaanch | ✅ kiya: sirf sarkari/sansthan ke number/email mile (112, 1077, Police WhatsApp, KMVN, @nic.in) | |
| SoftwareApplication + aggregateRating | ❌ kabhi nahi | bina asli review rating = structured-data spam (audit bhi rokta hai) |
| Title mein har mahine [Month] badalna, emoji | ❌ | content badle bina tareekh badalna = nakli taazgi |
| Live % poll ("84% ne chuna") | ⏳ sirf asli ginti, 30+ vote ke baad, privacy page pehle | nakli % owner niyam se mana |
| Bina login comment wall (naam + gaon) | ⏳ moderation + privacy ke baad (PENDING) | UGC spam, niji data |
| IndexNow par pehle din 260 URL | ❌ | page abhi live nahi = 404; purane over-submit se Bing ne site giraayi thi; IndexNow max 10/din |
| Bing 95/din bulk | ❌ wahi bing_plan (quota/3, max 30) | naye page apne aap priority mein |
| GSC '10 URL roz API se' | ❌ API se request-indexing nahi hota; Indexing API sirf job/live-video ke liye | owner haath se, bot list deta hai |
| WebSub/RSS 'Google limit bypass' | ❌ | Google Search ke liye koi bypass nahi; sitemap kaafi |
| lastmod mein random jitter | ❌ | nakli samay |
| Homepage par roz index-nahi pages ka 'Trending' dabba | ❌ abhi | homepage roz badalna + nakli 'trending'; footer link kaafi |
| Index na ho to bot khud 2 FAQ + table jode | ❌ | apne aap bana content = scaled-content khatra; owner ko suchna |
| 625 page / 10.5 lakh, Tehsil pages | ❌ abhi | tehsil ka asli alag content nahi hai; patle page = thin content |
| 28-30 page/din | ❌ | 10/din niyam |
| Glossary auto-linker har shabd par | ❌ | zyada link = spam; shabdkosh tool + page link kaafi |
| Sitemap sharding | ⏳ | 536 URL ek sitemap mein theek (seema 50,000); bot ki lastmod logic ek file par |
| PostgreSQL + Claude Haiku rate-bot, www.sabhisaab.com | ❌ abhi | site static hai, factwatch pehle se; 'www' galat (canonical bina www) |
| Cloudflare cache, CLS ad box | ✅ pehle se / AdSense ke baad | |
| CTR healer (title auto-rewrite) | ⏳ sirf sujhaav, owner ki haan se | T1 niyam: title baar-baar mat badlo |


## 4. Doosra daur (14 Nov subah, owner: "tag hatao, meri personal line hatao, faltu delete, heading/FAQ strong, Bing zyada")
- Verify-tag hataye: '(verify)', '[VERIFY]', '✔', '(Verify ✔: ...)' -> sirf tag gaya, andar ki baat rahi ('(Verify ✔: raaste ke hisab se
  badal sakti hai)' -> '(raaste ke hisab se badal sakti hai)'). Jahan asli salah thi ('UPCL se verify karein') wo 'pushti karein' bani.
  DHYAN: har tathya ek-ek karke sarkari srot se nahi milaya gaya (1,300+ jagah) - isliye har page par 'Dhyan dein' note hai ki aankde
  srot ke hisaab se alag ho sakte hain. Jo tathya pakke nahi the unki suchi UK_kaam_ki_baatein.md mein.
- Lekhak/AI ki apni baatein (127 'mere paas pakka naam nahi, isliye maine nahi likha', 121 'baad mein jodenge', 83 'Blueprint',
  'Namaste doston, main Sabhisaab.com ka owner hu', 'Website Owner ki taraf se') vaakya ke star par hataye; jo heading khaali bachi
  (6) wo bhi. Pathak ko 'humare paas data nahi' padhna patla content lagta hai.
- 13 zilon mein ek jaisi English template heading ('93. District Economy...') mein zile ka naam ('93. Almora: District Economy...');
  'the District' -> zile ka naam. H1 mein Devanagari naam ek baar: 'Almora (अल्मोड़ा) ka Pahadi Khana...' (Hindi search).
- Page-se-page milaan (6 shabd ke tukde, nav-box hata kar): koi do page 15% se zyada ek jaise nahi. Sabse chhota page 829 shabd (tool).
- Bing: BING_MAX_DAY 30 -> 50, quota ka 1/2 (pehle 1/3). Naye Uttarakhand page (14 din) sabse pehle ('naya Uttarakhand page'),
  phir purane index-nahi page waise hi. Index/bina badla page dobara KABHI nahi, 14/30 din ka niyam waisa hi.
  Roz 08:00 Bing report mein naya: 'Bing ne kya bola' (HTTP 200 / error) + Uttarakhand ka alag hisaab (kul/live/bheje/Bing mein dikhe/baaki).

## 5. Policy jo 14 Nov 2026 ko dekhi
- Google: 2026 mein teen spam update (June, 18 Aug, Sep) - scaled content abuse (bahut saare kam-kaam ke page, keyword-bhare page,
  AI se thok mein page) par. 15 May 2026 se spam niyam AI Overviews/AI Mode par bhi. Isliye: roz 8 page, har page asli lamba
  content, keyword suchi hataayi, page-se-page duplicate nahi.
- Google ne 7 May 2026 se FAQ rich result (search mein FAQ ka dabba) sabke liye band kiya. FAQPage schema nuksaan nahi karta (rakha),
  par FAQ se 'extra jagah' wala faayda ab nahi - FAQ ab sirf pathak aur AI-jawab ke liye. Isliye FAQ jawab chhote, seedhe rakhe.
- Bing: sitemap + IndexNow saath; lastmod sirf jab content badle (hum asli publish tareekh dete hain, jitter nahi). SOAP/POX API
  31 Aug 2026 se band - bot pehle se JSON API (ssl.bing.com/webmaster/api.svc/json) use karta hai.

## 6. KYA KARNA (owner) - v3.3.2 se
1. Bot ko kram se 3 ZIP (har ek ke baad bot ka jawab aane dein):
   a) sabhinet_v3.3.2.zip -> '✅ Haan, install karo'.  (v3.3.1 aur uk_pages_queue_v2 mat lagayein - dono isi mein aa gaye.)
   b) uk_pages_queue_v3.zip -> '✅ Haan, queue mein'. Pehle se live 8 page isi se agle din saaf content mein aa jaate hain
      (URL, title, publish tareekh wahi; koi naya din nahi ginta).
   c) sitefix_2026-11-14.zip (website ZIP) -> bot ki pushti. Isme 18 purane page ka sudhaar (neeche 9.4).
2. Roz bot ka 'Aaj N naya page LIVE' sandesh -> GSC -> URL inspection -> suchi mein upar se jitne ho sakein 'Request indexing'
   (Google ~10/din). v3.3.2 se suchi mein naye page ke baad wo purane page bhi aate hain jo Google ne index se nikaale/nahi liye.
3. 'indexing report' (ya galat spelling 'indixing report do') likhein -> Google + Bing ka poora taaza haal.
4. Bot 'Google index se NIKLE page' ka sandesh bheje to wo sandesh Claude ko - content sudhaar Claude karega.
5. 2-3 hafte baad GSC -> Performance -> Pages mein '-uttarakhand' filter: kaunse page par impression aaye - Claude ko batayein.
6. (Marzi) Aur photo bhejni ho to Claude ko (bot ko nahi) - wahi niyam: chehra/aawaaz/number plate/pakki jagah nahi.

## 7. KYA NAHI KARNA (koi bhi AI/insaan)
- Ek din mein 10 se zyada naya page; bulk IndexNow; Indexing API; nakli lastmod/jitter; har mahine title mein mahina badalna.
- aggregateRating / nakli star; nakli % ('84% ne chuna'); bina moderation comment wall; doosri site ka text copy.
- Index na ho to bot se apne aap FAQ/table bharwana; tehsil ke patle page; keyword suchi page par.
- Queue ke page haath se site par daalna (link toot jaayenge) - hamesha queue ZIP se. (Live UK page par chhota sudhaar website ZIP
  se kar sakte hain - v3.3.1 se queue use wapas nahi palatti.)

## 8. Aage ke kaam (developer, PENDING mein bhi)
- Gaon ki chaupal / poll: moderation + privacy page + asli ginti (sabhisaab-votes, 30+ vote) ke baad hi (15 Dec).
- GSC data (impression/query) aane par sirf un page ka title/description sudhaar jahan 1000+ impression aur CTR kam (5 Jan).
- UK_kaam_ki_baatein.md ki verify list se top 50 tathya sarkari srot se milana (district NIC site, Census 2011).
- (v3.3.2 mein 35 photo lag gayi.) Jin zilon ki photo kam hai (Champawat, Udham Singh Nagar, Haridwar ke liye terai/ghaat) - owner nayi bheje to photos.py se.
- 3 tool page ko 1000+ shabd, GK page par table (audit WARNING).

## 9. Teesra daur (14 Nov dopahar) - Gemini/ChatGPT ki suchi par poori jaanch, v3.3.2
Owner: "pura pado 100%, ek baar total privacy policy ke hisaab se final check karke verify karke do". Har daave ka nateeja:
| Daava | Jaanch mein kya mila | Kya kiya |
|---|---|---|
| Policy ke andar aur FAQ ho sakte the | 29 page par 4 se kam FAQ the; kai jagah sawal-jawab numbered para/bullet mein chhupe the | Numbered/bullet/inline 'Sawal? Jawab.' -> FAQ; 33 page par hath se likhe page-aadharit FAQ (faq_extra.py). Page par dikhne wale FAQ: 5,154 (pichhli ZIP) -> 6,480; 4 se kam FAQ wala page: 0 |
| Bina padhe non-duplicate data hataya | Haan - 'kaise banayein', 'data-sangrah', 'kya khoj kar likhna' wali heading ke neeche asli baatein bhi chali gayi thi (SHG kaise banayein, rehne ka kharch, bazaar band din, Tehri ke sawal-jawab) | Har chhoda hissa padha (skipsec suchi): 17 heading ka naam badla aur content wapas; editor-hisse ke andar ke pakke sawal-jawab FAQ mein; '[Module N samaapt]' par editor-hissa khatam (zameen-kanoon ki 'Zaroori suchna' wapas) |
| Spelling / mixed bhasha | 1,036 English template heading; ~100 typo | 98 template heading Hinglish (headings_hi.py), ~100 typo sahi; bachi English heading sirf naam/ek-baar wali |
| Verify remark chhod diye | 50+ 'verify karna zaroori hai', 'Data verify nahi', 'verify_list me rakhi' bache the | Saaf Hindi: 'jaanchna zaroori', 'pushti nahi', 'sroton mein matbhed'; 'verify_list/verify nishan' wale vaakya hate. Rendered HTML mein 'verify' ab sirf 'Pushti kahan karein' jaisi pathak-salah |
| Lekhak/owner ki line bachi | 'Module 12 (...) poora hua', '# MODULE 10 (Part B)', 'Sampadak ka sujhav', 'apni website par banayein', 'Haridwar aapke traffic ka sabse bada hissa', '(Heading 99)' jaise toote ishare, form-template ki suchi | Sab hata diye (META/PARA_INTERNAL), isi page ke 'Module N' ishare hate, na mile 'Heading N' ishare hate, template ke neeche ki khaali suchi hati |
| Description ek jaise | 264 mein se 247 page ka description ek hi saancha (sirf zile ka naam) - ye wahi text page ka pehla para bhi hai | descs.py: har page mein us zile ke 2-3 asli naam jo us page mein sach mein aate hain (Almora ghumne: Jageshwar, Binsar...). Ab 264/264 alag |
| Advanced/automatic | Bot ka Google-index haal (siteknow) pehle se tha; bot ne owner ka 'indixing report do latest' (14 Nov 10:34) ka JAWAB HI NAHI diya | 'indexing report' ab galat spelling mein bhi samjhta hai; Google index se NIKLE page roz pakad kar website-doctor ki wajah ke saath alert; GSC suchi mein upar. Google se dobara URL Inspection NAHI (daily.py pehle se 150/din karta hai - quota dohra nahi) |
| Polls / comment | - | Gumnaam poll (52 page) sirf sabhisaab-votes worker ki asli ginti (30+ vote ke baad %); privacy page mein pehle se. Comment wall abhi nahi (moderation) |
Shabd (264 UK page): ~10.25 lakh -> ~9.96 lakh. Kam hue ~70k mein ~46k lekhak/AI-vaakya; ~10k 'asli gaye' ki jaanch ki - bache hue zyadatar
bina jawab ke keyword-sawal ki suchi (page par sawal bina jawab = patla content) jo UK_kaam_ki_baatein.md mein poori hai.

### 9.4 Purane page jo Google ne index nahi kiye / nikaale (state/daily.json, 7 Nov tak ka GitHub copy)
260/269 URL index mein. Baaki 9: 3 'Crawled - not indexed' (buy-vs-rent-guide, electricity-bill-guide, scientific-calculator-guide),
6 'Discovered - not indexed' (delivery-date, fire-number, number-system-converter, random-number, stopwatch, notice-period-buyout).
- electricity-bill-guide: wajah = /bijli-bill-kaise-banta-hai se ek hi vishay (description bhi 'Bijli bill kaise banta hai' se shuru).
  Ab page sirf 'bill ghatana' par: appliance-wise bachat ka hisaab (formula + table), naya title/description, dono page aapas mein saaf link.
- scientific-calculator-guide: 11 hal kiye sawal (kya likhein, kya jawab), har jawab code se jaancha; 3 naye FAQ.
- buy-vs-rent-guide: 29 Oct ko sudhra tha, Google aakhri baar 18 Jul aaya - sirf 'Request indexing' chahiye.
- 6 'Discovered' tool: technical sab theek (canonical, robots, sitemap, 1,268-1,606 shabd, 5-8 andar ke link). Stopwatch/random
  number jaise aam tool par Google khud widget dikhata hai - index hona pakka nahi; Request indexing + bahar ke link.
- Poori site: 12 page par '&amp;times;' jaisa dohra-escape (screen par '&times;' dikhta tha) aur 6 page par Hinglish ke beech bhatka
  Devanagari shabd ('ka औसत') - sahi. dateModified sirf un 2 page ka badla jinka content sach mein badla.


## 10. Chautha daur (14 Nov raat) - photo, bhasha, dhancha
### 10.1 Photo ke niyam (owner: "chehra aawaaz na aaye, fix location mat dalna, kewal pahad/ghar dikhe")
- Sirf owner ke parivar ki khud ki khichi photo/video. Chehra, insaan ki pehchan, aawaaz (video ka audio kabhi nahi), number
  plate, watermark (naam/phone model wala), poster/text wale frame, hotel kamra, restaurant, gaadi ka dashboard - BAHAR.
- Alt text mein sirf dikhne wali cheez ('ghati mein basa pahadi kasba'), kisi gaon/ghar ka pakka naam nahi.
- EXIF/GPS nahi (naya webp banta hai), 1200px tak, 160KB se kam, width/height/loading=lazy (pehli photo eager).
- Photo page ke saath hi site par jaati hai; queue mein pehle se rakhi rehti hai.
### 10.2 Bhasha
- Heading: headings_tpl.py (828 saanche). Naya English heading aaye to wahin haath se Hinglish - niyam-aadharit anuvaad MAT (galat vaakya).
### 10.3 Dhancha
- 'Kya X mein Y Hai?' sirf haath se jaanchi suchi (dhancha.OK). Kram 1-214 sab zilon mein ek - jaan-boojh kar (anchor/link).

## 11. Paanchva daur (14 Nov shaam) - v3.3.3
- ZIP kram: sabhinet_v3.3.3.zip -> uk_pages_queue_v4.zip (queue v3 ki jagah; pehle se live page agle din naye content mein). sitefix
  dobara nahi (pehle hi lag chuki).
- Taazgi: bot har Somvaar 'Taazgi jaanch' bhejega - wo sandesh Claude ko. 'taazgi' likh kar kabhi bhi.
- Sarkari srot: fix5.py mein har sudhaar ke saath srot likha hai. Naya aankda jodna ho to pehle Census/NIC/Lok Sabha uttar se.
- Photo niyam waise hi (section 10.1). Drive par nayi photo daalein to Claude ko batayein - photos2.py jaisa naya daur.
