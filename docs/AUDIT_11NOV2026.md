# AUDIT 11 Nov 2026 - [FABLE 5.2] Claude Fable 5.2 (bot v3.0.2 + website + VM + policy) -> bot v3.1.0 + website W11 (ZIP 12 Nov ko diye)

> **Kisne kiya:** ye poora audit aur is chat ki saari ZIP (bot v3.1.0, v3.1.1, v3.1.2 + website W11, W12) Claude Fable 5.2 ne banayi -
> owner ne 12 Nov ko pakka kiya (model owner ne chuna tha). v3.1.3 (sirf ye naam ka tag) Claude Opus 5.5 ne joda.
> AGLA AI: neeche ke sudhar Fable 5.2 ke audit ke hain - jo baaki hain wo docs/PENDING.md + docs/TRAFFIC_PLAN.md hissa 5 mein hain.

Owner ka hukum: "100% padhna... website, bot, VM, policy, indexing, audience, video - sab ki audit; final ZIP".
Ye file SACH likhti hai - jo theek hai wo theek, jo kamzor hai wo kamzor. Tag: [CRITICAL] [HIGH] [MEDIUM] [LOW].

## 0. Kya padha / jaancha, aur kya NAHI jaanch saka
PADHA: GitHub bot repo (v3.0.2 = live, VM audit se milaya) ka poora app/ (84 Python file, ~28,700 line mein se audit/pipeline/answers/render/
tts/karaoke/text/guardtext/qplan/puzzles/website(Bing)/votes/updater/tasks/privacy_patch/config poore; baaki ka dhaancha), docs ke sab
panne (AI_START, PENDING, OWNER_RULES, WORKPLAN, STATUS, HEALTH, ESCALATE, QUERIES, INDEXING, SITESCAN, KEYWORDS, PLAYBOOK, IDEAS_AUDIT,
ADSENSE_REVENUE_PLAN, AUDIT_9NOV, ROADMAP ke aakhri 40 hisse), CHAT.md (owner ke saare 488 sandesh + traffic/haal wale jawab),
VM audit report (11 Nov 07:47), website repo ke saare 273 HTML (script se: title/description/canonical/H1/robots/sitemap/shabd/
dohraav), live https://sabhisaab.com/, /jawab, privacy/terms/disclaimer/contact ka poora text, robots/_headers/sw.js/manifest/llms.txt,
owner ke 2 attachment (10-pillar "Master Audit Prompt" + "Pro-Level Master Audit Blueprint" PDF).
CHALAYA (sandbox): website ka apna audit gate scripts/audit.py (272 page, ERROR 0), bot ke module import, 1,440 + 228 built-in sawal
naye darwaze se, naya tests/smoke.py (27 jaanch PASS).
AAJ WEB SE MILAYA: YouTube monetization niti (July 2026 safai), Google spam niti (scaled content; May + Aug 2026), Meta original-content
niti (Mar 2026).
NAHI JAANCH SAKA (sach): (1) owner ne likha "attachment video dekho" - VIDEO FILE chat mein NAHI aayi (sirf VM audit .txt + PDF).
Isliye video ki raftaar/quality aankh se nahi dekhi; code se timing ka tareeka padha aur naap ka auzaar banaya. (2) VM par seedha
haath nahi - sirf report. (3) GSC/AdSense/YouTube Studio ke andar ke panne (192 "not indexed" ki 6 wajah ka screenshot is chat mein
nahi). (4) Video render sandbox mein nahi chalaya (awaaz ka model VM par hai) - isliye render.py ko chheda hi nahi.

## A. SABSE BADA SACH (pehle ye padhein)
Aankde (bot ki apni report se, 11 Nov): YouTube 4 channel, 28 din = 3,151 views; pichhle 7 din mein 62 upload -> ek video par ausatan
lagbhag 13 views. Website: 7 din mein 10 log. Google Search: 28 din mein ~45 baar dikhi, 0 click. Pinterest: 28 din 3 website-click.
10 din mein bot ke ~40 version bane (v2.3 -> v3.0.2), sabhinet service 25 baar restart.
Matlab: MACHINE theek chal rahi hai (HEALTH mein sab ✅), par AUDIENCE nahi aa rahi. Aur feature jodne se ye nahi badlega. Teen asli wajah:

### A1. [CRITICAL] "100% bina insaan" + "YouTube/Facebook monetization" - aaj ki niti mein dono saath nahi chalte
- YouTube ne July 2026 mein apni monetization niti saaf ki: "generic ya repetitive" (saanche se bani, AI/computer se bani, video-dar-video
  bahut kam farak), "unsatisfying" aur "AI persona jo sehat/paise par bole" - in par kamai nahi. Channel ko poore taur par dekha jaata hai.
- Hamara model = 4 channel x roz 2 = 8 saanche wali AI-awaaz quiz reel. Rang/card/hook rotate karna achha hai, par niti "asli insaani
  yogdaan/alag mulya" dekhti hai, rang nahi. YPP ke liye apply karte waqt reviewer yahi dekhega.
- Meta (Mar 2026): original content ko reach + kamai, dohraav/kam-mehnat ko kam reach. Wahi disha.
- Ye BAN ka khatra nahi hai (hum niyam nahi tod rahe, label laga rahe hain) - ye "kamai manzoor nahi + kam reach" ka khatra hai.
- ILAAJ (sabse sasta, 95% automatic rahega): har channel par hafte mein 1-2 video mein OWNER KI APNI AWAAZ (phone par 30-60 sec bol kar
  bot ko bhejna - sawal samjhana, pahadi shabd bolna, apna anubhav). Bot baaki sab kare (edit, card, post, jawab). Pahadi Hisaab par ye
  sabse asardaar hoga (asli pahadi awaaz = koi AI nakal nahi kar sakta). Owner list mein kaam joda gaya.
- Saath mein: channel kam karna sochein. 4 naye channel par 0 se shuru karne se behtar 1-2 par dhyan (YPP: 1,000 subscriber + 10M Shorts
  views/90 din ya 4,000 ghante). Abhi 3,151 views/28 din 4 mein bante hain.

### A2. [CRITICAL] Website par log isliye nahi aa rahe - technical galti NAHI, mukabla + nayi domain
- Technical SEO saaf hai (script se jaancha): 270 page, har ek ka alag title/description, canonical sahi, 1 H1, sitemap = file, noindex
  sirf 404/links, sabse chhota page 1,001 shabd, page-dar-page dohraav sirf ~9% (median). 263 page index hain.
- Phir bhi 28 din mein ~45 impression. Wajah: (1) domain 21 Jul 2026 ki - 3.5 mahine, koi bahari link nahi; (2) "SIP/EMI/GST
  calculator" jaise shabd par Groww, ClearTax, bank ki site baithi hain - nayi site page 5+ par; (3) 3 mahine mein 270 page ek saath =
  Google ko "ye sab ek hi saanche se" lagta hai (Aug 2026 ke spam update ke baad Google is par aur sakht hai); (4) Roman Hinglish mein log kam khojte hain -
  ya English ("emi calculator") ya Devanagari.
- Jahan hum JEET rahe hain wo dekhiye (KEYWORDS.md): "1 mutthi in square feet", "ek nali kitna hota hai", "ukfr login", "chakravriddhi
  byaj" = position 1-10. Yani PAHADI/desi/Uttarakhand wale sawal jahan bade khiladi nahi hain. Website ki asli taaqat yahi hai.
- ILAAJ: naye calculator banana BAND. Uttarakhand/zameen/kisan/pahadi vishay par 15-20 gehre panne (ek-ek, owner ke anubhav ke saath),
  wahi Pahadi Hisaab channel ka vishay - channel aur site ek doosre ko uthayenge. Hissa H mein poora plan.

### A3. [HIGH] Reel -> website ka pul kamzor hai (banawat se)
Shorts/Reels ke description ka link click nahi hota. "Code yaad rakho, site par jao" = 3 kadam; 13 views wali video se koi nahi aata.
Jo kaam karta hai: lambi video ke link, pinned comment, channel ka profile link, Telegram. Hub video (hafte ki) sahi disha hai.
/jawab achha bana hai - par pehle video par audience chahiye.

## B. Mili galtiyan (asli, saboot ke saath) aur ilaaj
| # | Tag | Galti (kahan) | Khatra | Ilaaj |
|---|---|---|---|---|
| 1 | CRITICAL | Hindi mein Punjabi (Gurmukhi) akshar: live /jawab code #3977 "परछਾਈ" (video + website + register). text.fix sirf chhupe akshar hatata tha | Galat Hindi video par; Google ko kharab content; owner ki roz ki shikayat | ✅ v3.1.0 app/hindifix.py: doosri lipi -> Devanagari (Unicode naam se), dohri matra; har bahar jaate text par (guardtext); purani entry padhte waqt theek. Sahi text byte-dar-byte waisa hi (2,216 Hindi line + 1,440 sawal par jaancha) |
| 2 | CRITICAL | "Final authority" kamzor tha: 7 jaanch, likhai/vishay/padhne ka samay nahi | Galat video post | ✅ app/finalgate.py: +5 pakki jaanch (likhai, mana vishay, dhaancha, padhne ka samay, raftaar ka naap). 'final jaanch' command |
| 3 | HIGH | Tyohaar wale slot mein vishay-rok chhoot gayi: 10 Nov Money par "Bhai Dooj Nivesh: SIP aur tax" (#4592) - owner niyam 9 + YouTube "AI persona + paisa" | Monetization + niyam | ✅ render se pehle pakad kar jaancha hua puzzle; darwaze par bhi; BLOCK_RX mein nivesh/demat joda |
| 4 | HIGH | /jawab ka structured data GALAT: AboutPage "About Sab Hisaab", breadcrumb "About Us", tareekh 21 Jul (about.html ke saanche se) | Google structured-data niti (markup page se mile) | ✅ answers.fix_ld: CollectionPage + sahi breadcrumb; install ke baad page khud dobara banega |
| 5 | HIGH | Bing ko roz 10-30 BINA BADLE purane page baari-baari dobara (INDEXING.md: 4-11 Nov "bing-api roz") | Wahi aadat jisse Bing ne site hatayi thi | ✅ bing_plan: sirf Google-index-nahi / Bing-ne-crawl-nahi / naya-badla. Purane dobara nahi |
| 6 | HIGH | Homepage: "100% Data aapke paas", "data kahin nahi jaata" - jabki GA4, cookie, OneSignal, vote counter hai | Privacy policy se takraav (AdSense/DPDP) | ✅ W11: sach wali line + Privacy link |
| 7 | HIGH | Gemini free quota roz khatam (VM audit: SAARE model 'cool'; tathya-jaanch, tyohaar-jaanch, photo fail) | Bot ka "dimaag" aadhe din band; jaanch bina sawal | Owner faisla: billing + seema (list mein). Code pehle se Cloudflare AI par girta hai |
| 8 | MEDIUM | Public GitHub docs mein VM ka poora IP (trading wali VM); chat copy mein bhi IP aa sakta tha | Hamla karne wale ko pata | ✅ docs mein IP dhaka; updater._mask ab IP chhupata hai |
| 9 | MEDIUM | VM: 14 suraksha update baaki | Purani kamzori | Owner: apt upgrade (list mein) |
| 10 | MEDIUM | Bank ka tathya: Nanda Devi "poori tarah Bharat mein doosri sabse oonchi" (galat - Bharat ki doosri; poori tarah Bharat mein SABSE oonchi) | Galat GK | ✅ puzzles.py |
| 11 | MEDIUM | /jawab ke FAQ mein "table mein saare 1,200 jawab" (ab sirf 8) + ek line do baar | Purani baat | ✅ answers.py |
| 12 | MEDIUM | Vote counter (asli %): Origin header nakli bana kar koi bhi vote bhar sakta hai; KV read-modify-write | "Asli %" bigaad sakte hain | Agla: Cloudflare Turnstile ya din-bhar ka namak-wala hash (privacy page pehle). Abhi 30-vote seema hi bachav |
| 13 | MEDIUM | ZIP se page badle to sitemap lastmod haath se bhejna padta tha | lastmod aur page ki tareekh alag | ✅ website.sync_lastmod (page ki dateModified se) |
| 14 | MEDIUM | Website par cookie sahmati sab desh ke liye 'denied' se shuru | GA4 ginti kam dikhti hai (10 log/hafta asal se kam ho sakta hai) | Faisla: Bharat ke liye DPDP ke hisaab se abhi yahi surakshit; badalna ho to vakeel se |
| 15 | LOW | Privacy: "Ye teeno cheezein" (4 hain); Disclaimer mein quiz-jawab ka zikr nahi | Chhoti | ✅ W11 |
| 16 | LOW | venv 6 GB (CUDA wala torch, CPU VM par bekaar); ~/carve, ~/keep, ~/sandbox purane | Jagah (abhi 11% bhari) | Chhodo (jokhim > fayda) - pehle bhi yahi faisla |
| 17 | LOW | SSH port 22 duniya ke liye khula (key-only + fail2ban hai, 2,544 koshish roki) | Kam | Marzi: Oracle Security List mein seemit; ed25519 key |
| 18 | LOW | GitHub copy mein tests/ nahi tha (AI_START kehta hai ZIP mein zaroor) | Agla AI bina test ke ZIP banata | ✅ naya tests/smoke.py (27 jaanch); updater ko tests/ bhi GitHub par bhejna chahiye (agla) |

## C. Owner ka 10-pillar "Master Audit Prompt" - har point ka sach
Wo prompt ek aise product ke liye likha hai jisme BAHAR ke user login karte hain (unke /analytics, password vault, webhook, database).
Hamara system waisa NAHI hai: site static hai (koi database/login nahi), bot sirf owner ke apne channel par chalta hai. Isliye:
| Pillar | Haal |
|---|---|
| 1 Speed/Core Web Vitals | Static + Cloudflare; font non-blocking; image cache 1 saal; SW network-first (naya jawab turant). /jawab 46 KB. PageSpeed bot hafta-war naapta hai. Baaki: Google Fonts self-host (pehle se list mein). ✅ theek |
| 2 SEO/OG | sitemap/robots/canonical ✅. /jawab ka JSON-LD galat tha -> ✅ theek kiya. WhatsApp share: /jawab#cCODE ka preview hamesha ek hi photo (static site par har code ka alag OG mumkin nahi bina naye page ke - aur naye page = scaled content; mat karo) |
| 3 Bot engine | Post-lock (dobara post nahi) ✅, retry + 24h rok ✅, token watcher ✅, systemd restart ✅, watchdog ✅, kill = 'pause' ✅. DLQ/Redis/SQLite NAHI chahiye (ek process, ek owner) |
| 4 Media/A-B | tmp safai ✅, render alag thread + nice ✅, A/B thumbnail (lambi video) ✅ - par 13 views par A/B ka koi matlab nahi (data hi nahi). "Human jitter" = NAHI (neeche D) |
| 5 Security | Secrets 600 folder ✅, koi webhook nahi (polling) ✅, public repo mein koi token nahi (scan kiya) ✅, CSP/HSTS ✅. AES vault ki zaroorat nahi (koi bahari user ka data nahi) |
| 6 Database | Nahi hai. state.json atomic + lock ✅; encrypted backup Telegram par ✅ |
| 7 Logs/health | Ek-line log, token masked ✅; HEALTH.md ✅. /health endpoint NAHI (VM par khula web port nahi - sahi faisla) |
| 8 Legal | Privacy/Terms/Disclaimer/About/Contact poore padhe: YouTube API, Google, Meta, Pinterest, OneSignal, Gemini, DPDP haq, data deletion - sab likha hai. Chhoti 3 galti -> W11 |
| 9 Liability/IP | Terms 10 (as-is), 5 (copyright) ✅. "User ka content license" laagu nahi (user kuch upload nahi karta) |
| 10 Monetization | ads.txt taiyaar, CMP ka kaam owner list mein. Refund/Pricing page tabhi jab payment gateway aaye. ASLI rukavat = traffic (hissa A) |

## D. "Pro-Level Master Audit Blueprint" PDF - har sujhaav ka faisla
⛔ = mat karo (niti todta hai ya jhooth hai) | ✅ = pehle se hai | 🟢 = achha, kab
| Sujhaav | Faisla | Kyun |
|---|---|---|
| "Bot-detection obfuscation", "human-like jitter taaki platform na pakde" | ⛔ | Hum official API se, apne naam se post karte hain - chhupane ki koi zaroorat nahi, aur chhupana hi "deceptive" hai |
| Spintax comment reply (har comment par ghuma-phira kar site ka link) | ⛔ | Yahi spam ki paribhasha hai (YouTube/Meta). Abhi: comment ka asli jawab, link sirf jahan sawal usi ka ho |
| "90% reel + 10% raaz website par": jhoothi kahani ("court ki forensic report"), "hidden bank offer jo app par nahi dikhta" | ⛔ | Misleading/clickbait (YouTube "unsatisfying", AdSense deceptive). Hamara "sawal reel mein, jawab site par" sach hai - wahi rakho |
| "Written by Verified Financial Editor / Reviewed by SME" card | ⛔ | Aisa koi vyakti hai hi nahi = nakli E-E-A-T. Sach: "Manoj Kumar Pandey ne likha/jaancha" (author page hai) |
| Citation box "RBI circular/MCLR par aadharit" har tool par | ⛔ jaise likha | Jhootha daava (calculator formula par chalta hai). Sach wala "Official source" box 172 page par pehle se ✅ |
| Money channel: "5,000 SIP 15% return = 75 lakh / 1.4 crore" hook | ⛔ | Return ka daava (SEBI) + AI persona + paisa (YouTube July 2026) + owner ne khud band kiya |
| Roz ka poll "OPS wapas aana chahiye?" | ⛔ | Rajneetik vishay - AdSense/brand ke liye jokhim, site ke kaam ka nahi |
| "Secret number unlock", step-by-step reveal se rokna | ⛔ | Zabardasti rokna (pehle bhi IDEAS_AUDIT mein mana). 'Tap karke socho' sach wala tareeka ✅ hai |
| "Agla rahasya" trending code carousel | 🟢 chhota | /jawab par "Agla jawab" + naye 8 pehle se. Views aane par "sabse zyada dekhe gaye" jodna theek |
| Tool chaining (SIP ka nateeja -> tax tool mein pehle se bhara) | 🟢 baad | Asli kaam ka; URL parameter se. Par pehle traffic chahiye - abhi 10 log/hafta |
| WhatsApp share card (canvas) | ✅ | /jawab score card pehle se. Calculator nateeje par bhi - list mein (W11/embed) |
| Calculation history localStorage | 🟢 baad | Privacy page mein pehle likhna hoga |
| systemd Restart=always, log/disk safai, token refresh, weekly feedback (jo chale wo zyada) | ✅ | sabhinet.service, guard.cleanup, ops token watcher, learn.choose + qplan.weekly_adapt |
| SQLite pending queue, UptimeRobot webhook | ⛔ zaroorat nahi | Post-lock + reopen_jobs + ntfy/relay pehle se; khula port nahi kholna |
| 4-tier tool page (tool + 300-500 shabd + FAQ schema) | ✅ | Har page 1,000+ shabd, FAQPage/BreadcrumbList schema |
| "10 topic cluster" | ✅ | 8 category hub page. Naye "programmatic" page ⛔ (scaled content) |
| Low-competition Hinglish query ("bigha to nali converter") | 🟢 YAHI | Hissa A2/H - yahi asli mauka |
PDF mein channel ka jo varnan hai (Suno Natak = audio drama, Money = SIP/tax hacks) wo PURANA hai - owner ne 10 Nov ko sab channel
sawal/paheli par kar diye. Us PDF ke "master prompt" ko kisi AI ko dena = purani disha mein wapas jaana.

## E. Platform niti - aaj (11 Nov 2026) hum kahan khade hain
| Platform | Hum niyam ke andar? | Dhyan |
|---|---|---|
| YouTube (aaj jaancha) | Upload/label/API: haan. Monetization: A1 dekhein (saanche wali AI video) | Apni awaaz; channel kam; Money par paise ki salah zero (ab darwaze par) |
| Google Search (aaj jaancha) | Spam niti: koi cloaking/link-kharid/doorway nahi ✅. Scaled content: 270 page 3.5 mahine - seema par | Naye calculator page band; purane gehre karo; ek-ek page (owner ka niyam sahi hai) |
| AdSense | Zaroori panne, ads.txt, CMP taiyari ✅. Apply kar sakte hain; "low value content" se mana ho sakta hai (nayi site + calculator) | Mana ho to ghabrana nahi; traffic ke bina kamai waise bhi ~0 |
| Bing | Purani galti (zyada submit) ka asar baaki; v3.0.2 phir baari-baari purane bhej raha tha | ✅ band kiya. Ticket ka intezaar; sirf naya/badla |
| Facebook/Instagram/Threads (Meta aaj jaancha) | API se, label ke saath ✅. DM/link-comment band ✅. @sunonatak DM rok 27 Nov tak | Wahi reel 4 platform par = theek; par "original" ko reach milta hai (A1) |
| Pinterest | 2 pin/din/link seema ✅, sahi link ✅ | Theek |
| Telegram / WhatsApp | Ek-tarfa channel, opt-in bot ✅. WhatsApp ka API nahi - haath se forward | Theek |
| OneSignal push | Opt-in, roz max 1 ✅ | Theek |
Bot ka policywatch 18 niti-panne har 3 din dekhta hai - ye chalta rahe. Par niti padhna aur niti ke hisaab se CONTENT badalna alag hai;
A1 jaisa badlaav bot khud nahi kar sakta (insaan ki awaaz chahiye).

## F. Indexing - "bahut page index nahi" ka sach
- Site ke 270 asli page mein se Google par sirf 7 index nahi (STATUS.md): 5 "Discovered", 1 "Crawled - not indexed", 1 title takraav
  (fire-number vs retirement). Ye sab AAM tool hain (stopwatch, random number, number system) jinke liye Google khud widget dikhata hai -
  inhe index karne ki Google ko koi jaldi nahi. Koi technical rok nahi (pehle bhi jaancha, aaj dobara).
- GSC ka "192 not indexed, 6 wajah": ye asli page nahi hain - zyadatar purane .html pate (clean URL par redirect), purane ?t= link
  (canonical homepage), 404, aur wahi 7. (Screenshot is chat mein nahi tha - owner GSC mein har wajah khol kar ginti dekh le; agar
  "Crawled - currently not indexed" 7 se bahut zyada ho to Claude ko wo list bhejein.)
- ASLI samasya index nahi, RANK hai: 263 page index hokar bhi 28 din mein ~45 baar dikhe. Ilaaj hissa H.
- Request Indexing baar-baar karne se kuch nahi hoga; bahar se asli link (Pinterest pin, YouTube description, kisi pahadi group/site
  ka zikr) + behtar page hi raasta hai.

## G. VM audit (11 Nov 07:47 report) - nateeja
Theek: RAM 10.7 GB khaali, disk 11%, OOM 0, ghadi sync, koi failed service nahi, trading services chal rahi (chheda nahi), port 8001-3
bahar se band, SSH key-only + root band + fail2ban, secrets 600, koi secret git mein nahi, Telegram takraav (409) nahi.
Dhyan: (1) 14 suraksha update [MEDIUM, owner]. (2) Gemini quota - saare model 'cool' [HIGH, owner faisla]. (3) quizbot poll 43
"connection reset" 3 din mein - relay se chal raha hai, chalta hai; agla: backoff badhana. (4) IG "ProcessingFailedError" 5 baar -
v2.9.8 ka re-encode laga hai, 3 din aur dekho. (5) GA4 Data API 4 fail - owner ne 10 Nov ko chalu kiya, ab theek hona chahiye.
(6) ~/chert_pwd.txt, ~/dashboard_pass.txt, ~/dhan_auth.txt, ~/dhan_token.txt saade text mein (trading ke; permission theek) - chhedna
nahi, par VM ka backup kisi ko mat dena. (7) ubuntu user ke paas bina password sudo - Oracle ka default; SSH key hi asli taala hai,
use sambhal kar rakhein. (8) sabhinet 25 restart = 10 din mein 40 update install; ab update kam karo (neeche J).

## H. Audience + kamai ka plan (niti ke andar; jitna ho sake automatic)
Lakshya ka sahi kram: PEHLE audience (3-6 mahine), PHIR monetization. Abhi monetization ke button dabane se kuch nahi milega.
1. FOCUS (owner faisla): 4 mein se 1-2 channel ko "mukhya" maano - sujhav: Pahadi Hisaab (alag pehchaan, kam mukabla, site ke pahadi
   panne isi par rank kar rahe) + ek paheli channel. Baaki chalte rahein par ummeed in do se.
2. APNI AWAAZ: hafte mein 1-2 video (A1). Phone ki video/awaaz bot ko bhejne ka raasta pehle se hai (Telegram se 20 MB tak; badi file ka raasta WORKPLAN #16 mein baaki).
3. WEBSITE: 30 din tak koi naya calculator nahi. Har hafte 2 pahadi/desi panne gehre karo ya naye likho (ek-ek, owner ka niyam):
   nali-mutthi ke zila-wise udaharan, bisi/mana/patha jaise purane naap, khasra-khatauni padhna, UKFR ke asli sawal, dakhil-kharij,
   pahadi mahino/tyohaar ki tithi. Ye wo sawal hain jinka jawab bade site nahi dete. KEYWORDS.md ke "position 1-12" wale shabd pehle.
4. PUL: har lambi (hub) video ke description + pinned comment mein /jawab; channel profile link = sabhisaab.com/jawab; Pahadi reel ka
   sawal usi pahadi panne se joda (jawab ke neeche wahi panna) - bot ka related_tools pehle se karta hai.
5. ROKNA (dwell): /jawab par tap-karke-socho, streak, agla jawab, related tool - ho chuka. Aur kuch jodne se pehle 4 hafte ka GA4 dekho
   (engaged 60%, ausat 9 min pehle se achha hai - samasya rokna nahi, LAANA hai).
6. KAMAI ka kram: (a) Services lead (custom calculator) - traffic ke bina bhi; (b) AdSense - 16 Nov ko apply theek, ummeed kam;
   (c) Facebook Stars/affiliate (Labh Lo Deals ka Facebook page sabse bada asset hai - bot ki meeting report mein 8,500+ follower likha hai, Studio mein pakka kar lein - wahan sach wale deal + #ad);
   (d) YPP - A1 ke baad hi.
7. NAAPNA: har Ravivaar ek hi sawal - "is hafte kaunsi 3 video sabse zyada dekhi gayi aur kyun?" (company meeting pehle se). 4 hafte
   tak wahi format rakho; roz format badalne se seekh nahi banti.

## I. Is delivery mein kya hai
BOT v3.1.0 (ZIP): app/hindifix.py (naya), app/finalgate.py (naya), audit/guardtext/pipeline/answers/qplan/puzzles/tts/updater/website/
tasks/bot.py mein chhote judaav, tests/smoke.py (naya, 27 jaanch), docs. Naye command: 'final jaanch', 'awaaz raftaar 1.1' (dohri pushti).
Koi purana function band nahi (niyam 20); sirf Bing ka "purane page baari se" band (galti thi).
WEBSITE W11 (ZIP): site/index.html (sach wali 3 line), site/privacy.html ("saari"), site/disclaimer.html (quiz-jawab hissa). audit.py
ERROR 0 / WARNING 0 (bot v3.1.0 ke lastmod-sync ke saath). PEHLE bot ZIP, PHIR website ZIP.
Test: tests/smoke 27/27 PASS; 1,440 built-in sawal naye darwaze se bina galat alarm; /jawab naye JSON-LD ke saath site audit PASS.

## J. Aage ke khatre (jo bot ko abhi nahi pata) + salah
- Har roz 3-4 update lagana band karein. Ab se: hafte mein 1 ZIP, sirf asli shikayat/data par. Har naya feature = nayi galti ki jagah.
- YouTube/Meta niti aur sakht hogi (disha saaf hai) - jitni jaldi asli awaaz/chehra/anubhav judega utna surakshit.
- Gemini ke model naam/quota badalte rehte hain - brain.discover khud dhoondhta hai ✅; free tier kabhi bhi kam ho sakta hai -> billing.
- Meta Graph version (abhi v23) - upgrader khud jaanchta hai ✅. Threads token 60 din - watcher ✅.
- Budget 1 Feb 2027: tax ke 13 panne - factwatch + owner ki ek nazar.
- DPDP niyam 2027 mein poore laagu: sahmati banner aur data-deletion pehle se hai ✅.
- "Zindagi bhar bina insaan" - sach ye hai ki koi bhi system 6-12 mahine mein kisi platform ke badlaav se tootta hai. Bot use PAKAD kar
  bata sakta hai (ESCALATE/PENDING ✅), par theek karne ko insaan/AI chahiye hoga. Isliye docs + tests ko taaza rakhna hi asli bima hai.

## K. JOD (12 Nov, v3.1.1) - video ki jaanch (owner ne file bhej di)
Reel: Labh Lo Deals, code #5034, 'अगर BANK = AZMJ, तो MILK = ?', 24.0s, 1080x1920, 30fps, awaaz -14.3 LUFS (theek).
Sahi tha: Hindi ki spelling, jawab (LHKJ) aur 50-50 (sahi kabhi nahi kata), awaaz ka star, quality (dhundhla nahi).
Kami (sab v3.1.1 mein theek, poora byora ROADMAP v3.1.1):
| # | Tag | Kami | Ilaaj |
|---|---|---|---|
| 1 | HIGH | Awaaz ne sawal bola hi nahi - sirf card ka naam 'कोडिंग-डिकोडिंग Code' | hook ke baad sawal bola jaata hai |
| 2 | HIGH | "Dheemi" isliye lagi: 'सोचिए / कमेंट में लिखिए' 3 baar, 24s mein ~12s bharti | bharti hatayi |
| 3 | HIGH | "5 second sochiye" ke dauran awaaz lagataar - sochne ka samay zero; har sawal ko ek sa samay | sawal ke hisaab se 1 / 2.5 / 3 sec ki chuppi |
| 4 | MEDIUM | Subtitle vaakya beech se toot-ta: 'लिखिए। दो' / 'गलत विकल्प हटा दिए अब' / 'बताओ!' | patti vaakya ke ant par |
| 5 | MEDIUM | Lehja mila-jula (सोचिए + बताओ/लिखो); hook mein 'पंडित जी कहता है', 'दादी कहता है' | sab 'aap'; ling/aadar-mukt vaakya |
| 6 | MEDIUM | Vikalp B, D laal (galat jaisa ishara); parde ka beech ka 45% khaali | ek rang; block beech mein |
Sach: awaaz main sun nahi sakta - shabdon ka uchcharan (jaise 'MILK', 'कोड') kaan se owner hi jaanch sakta hai.

