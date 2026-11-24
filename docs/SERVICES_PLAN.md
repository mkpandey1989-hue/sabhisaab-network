# SERVICES PLAN — A se Z (aaj se future tak)

> Status: **PLAN** (24 Nov 2026). Coding owner ke "shuru karo" ke baad hi.
> Yeh file services ka akela sach (single source) hai. Naya AI/developer pehle isse padhe.
> Purani file: project doc `SERVICES_PLAN_FINAL_DRAFT.md` (sections 0–12) — uski sab baatein yahan shaamil hain.
> Niyam: purana content kabhi delete/reformat nahi, sirf naye section jodo (sabse neeche "Badlav log" mein date ke saath).

---
## 0. Ek line mein
Reel dekhne wala koi bhi aadmi — chahe ₹10 ka resume ho, ₹49 ki form madad ho, mobile/computer ki dikkat ho ya ₹5,000 ki website — **turant comment/message kare, bot use pakde, aap kaam samajh kar rate dein, wo pay kare, kaam deliver ho, aur wo dost ko bheje.** Sab Telegram se aap control karein.

**Tagline (owner chunega, ek):**
1. "Koi bhi digital kaam — ho jayega"
2. "Aapka kaam, hamari zimmedari"
3. "Mobile ho ya computer — kaam bataiye, hum karenge"

---
## 1. Pakke niyam (kabhi nahi tootenge)
1. Owner ka naam/awaaz kisi video/post/ad mein nahi — sirf brand. Awaaz = brand TTS.
2. Ads/video par "AI se bana" nahi. Website par sachcha AI label rahega (about page).
3. UPI QR (owner ka naam dikhta hai) sirf customer ke **private quote page** par, kahin public nahi.
4. Customer ka password/OTP kabhi nahi lenge. OTP customer khud daalega, screen share mein control customer ke paas.
5. Koi cold DM, bulk message, bina ijazat call nahi.
6. Data sirf kaam ke liye, **90 din** baad apne aap delete. Form par DPDP consent checkbox.
7. Secrets sirf VM `.env` mein, GitHub par kabhi nahi.
8. `/services` page minimal badlav (AdSense). Bade badlav `services-list`, `services-demo`, quote page par. Quote page `noindex`.
9. Nakli timer, "2 slot bache", nakli review, nakli number — kabhi nahi.
10. Rate **kaam samajhne ke baad** hi final; floor price se neeche kabhi nahi (nuksan nahi).
11. Har video publish se pehle **5 round audit** (section 9) — ek bhi fail = publish nahi.
12. Faltu cheez nahi chhedni; jo maanga wahi badlo.

---
## 2. Kaam ki list (kya karenge)

### 2A. SABSE ZAROORI — Madad wale kaam (yahi asli kaam layega)
Har aadmi ke liye. Customer saath rahega (call/screen share), OTP wahi daalega.
| Kaam | Rate (se) | Note |
|---|---|---|
| Resume basic | ₹10 | sabse chhota kaam |
| Resume design / 2 page | ₹149 | |
| Sarkari/online form bharne mein madad (simple: exam, naukri, admission) | ₹49 | 1 form, documents customer ke |
| Scholarship form madad (NSP / rajya portal) | ₹99 | lamba form |
| PM Kisan / ration / pension online apply madad | ₹99 | sirf apply ki madad, faisla sarkar ka |
| Documents scan, size/format theek karke upload layak banana | ₹29 | |
| Application/letter/notice | ₹29 | |
| Biodata | ₹49 | |
| ITR madad — ITR-1 (salary/pension) | ₹299 | customer khud login, hum screen par samjhayein; galat daava nahi |
| ITR madad — ITR-2/4 | ₹699 se | case dekh kar; kathin case CA ko refer |
| Koi bhi madad ("XYZ") | ₹49 se | kaam samajh kar rate |

**ITR par saaf rule:** ₹49 wala rate ITR par kabhi nahi dikhega. ITR video mein sirf "ITR-1 madad ₹299 se". "Refund pakka", "tax bachao guarantee" jaisi line kabhi nahi.

### 2B. Mobile / laptop / computer ki madad
Phone setting, UPI app setup, email banana, WhatsApp Business setup, laptop slow, printer/scanner, Google account recovery ki madad (customer khud kare), photo/backup — ₹49 se. Remote: customer ki marzi se screen share (Google Meet / AnyDesk jahan customer control de sake), password nahi.

### 2C. Padhai
School/college project, PPT, Hindi/English typing, photo se text, chart/graph — ₹49 se.

### 2D. Dhanda (business)
GST bill app, khata, stock, booking, menu/rate card, 1-page website, Google Maps listing, Instagram/YouTube page setup, poster/thumbnail, WhatsApp bot, trading tools (sirf user ki strategy, signal nahi). Bundle "Dukaan Online Pack" ₹4,999 (alag ₹9,000+). Purani list (103 item, `app/svc_rates.json`) sab rahegi.

### 2E. Maintenance (care plan)
₹199 / ₹499 / ₹999 mahina. Mahine-mahine, kabhi bhi band. "Jab tak service, tab tak charge."

### 2F. NAHI karenge
Aadhaar/PAN mein khud badlav, ITR "hum file karenge" ka daava, tatkal ticket bot, nakli review/followers, betting/loan app, kisi ka trading account chalana, signal bechna, cold calling, bulk messaging, chhote kaam jo log khud AI se kar lete hain (photo compress jaise).

---
## 3. Price, chhoot, sale

- **Bazaar se 70–90% sasta:** har card, video, quote page par `Bazaar ₹X (kata hua) → Hamara ₹Y`. Bazaar rate ka source/likha hua aadhaar `svc_rates.json` mein.
- **Floor price:** `max(10, ghante×300×1.2)` — isse neeche koi discount nahi le ja sakta (code guard).
- **Discount seema:** brand code 10% · referral 10% · care +5% · **total max 25%** · ₹300 se chhote kaam par max ₹50 · urgent +50%.
- **Hafte ki sachchi sale:** har hafte 1 kaam par 20% off, asli shuru/khatam date. Date ke baad rate apne aap wapas. Sale ka log audit mein.
- **Tyohar offer:** Diwali, Holi, Raksha Bandhan, shaadi season, naya session (Apr–Jul), result/admission season — calendar se apne aap.
- **Bundle** aur **care plan** discount upar ki seema ke andar.

---
## 4. Referral (nuksan nahi, dono ko fayda)
- Dost jitna pay kare, uska **10%** bonus referrer ko.
- Bonus sirf ₹300+ ke paid kaam par banega; ek bonus max ₹500.
- Bonus agle **paid** kaam ke bill ka max 10% tak hi lagega — kaam kabhi free nahi.
- Dost (naya customer) ko pehle kaam par 10% off.
- Bonus tab pakka jab dost ne pay kiya aur 7 din refund nahi liya. Refund hua = bonus cancel.
- Same phone / same device / same IP se khud ko refer = block. Mahine mein max 5 bonus.
- **Expiry 90 din** (data delete ke niyam ke saath mel).
- Video/page line: **"Dost ko bhejo — uske bill ka 10% aapka"**.

---
## 5. Customer ka safar (form se delivery tak)

1. **Pehla sampark:** reel comment "KAAM" / DM / website form / WhatsApp button / QR poster.
2. **Form:** naam, phone, kaam (koi bhi likh sake), optional: code, urgent, care. Consent checkbox.
3. **Bhejna (kabhi fail nahi):** form → Cloudflare Worker → owner ke Telegram. 8 sec mein jawab nahi to retry; fir bhi fail to phone mein save, agli baar khud bheje. WhatsApp sirf extra option. Customer ko Telegram/WhatsApp ki zaroorat nahi.
4. **Customer ko turant:** tracking number + apna gupt page `sabhisaab.com/q?id=…&k=…` ("Kaam mila, hum samajh kar rate batayenge"). Page bookmark/share ka button.
5. **Owner (Telegram):** lead card — "Call karo" (tel: link), "WhatsApp karo" (tayyar message), "Rate daalo". Call ke baad ek tap: uthaya / nahi uthaya / baad mein.
6. **Rate:** owner rate daale → bot floor/max guard check → customer page par rate + kya milega + din + 2 revision niyam.
7. **Haan:** customer "Haan, theek hai" dabaye → Pay button + QR (amount bhara hua) khule.
8. **Payment:** UPI deep link. Owner bank app mein dekh kar "paid" (nakli screenshot se bachav).
9. **Kaam chalu → Delivered:** page par status. Final file poora payment ke baad; pehle watermark demo.
10. **Feedback:** star rating (sirf asli customer), ijazat ho to namoona portfolio.
11. **Band / Lost** + 30 din baad "aur kaam?" — sirf owner ke ek tap se.

**Bina login ke pehchaan:** phone + tracking ID + secret key wala link. Password nahi.

---
## 6. CRM (bot)
- Stage: Naya → Baat hui → Rate bheja → Haan → Paid → Kaam chalu → Delivered → Feedback → Band/Lost.
- Har step samay ke saath history (hash-chain audit, badla na ja sake).
- Follow-up yaad: 24 ghante jawab nahi, rate ke 48 ghante baad, delivery date se 1 din pehle.
- Kaam ki line: zyada order ho to bot sachchi "abhi X din ki line" bataye.
- Commands: `services report`, `lead <id>`, `paid <id>`, `refund <id>`, `rate <id> <₹>`, aur naye `call <id> uthaya|nahi|baad`, `deliver <id>`.

---
## 7. Video system (roz, bot)

### 7A. Har video kaisi
- **Pehle 1–2 second:** ek aam dikkat badi Hindi mein ("Form bharna nahi aata?", "Resume chahiye kal tak?"). Attractive, saaf, jhooth nahi.
- **Beech:** 6–8 kaam ek ke baad ek, har kaam ka chhota asli demo/screenshot. Teeno group: banana · madad/form · mobile-computer.
- **Price + bazaar rate kata hua**, sale ho to sachchi date.
- **Referral line** + **"Comment KAAM"** + link.
- Zarurat ho to video 5–10 sec lambi — par poori baat aaye.
- Har video ka rang/look/hook/layout alag; (kaam-set, look, hook, layout) combination lifetime dobara nahi.
- Kaali screen, galat caption, text overlap = audit fail.

### 7B. Season wali video (calendar)
Scholarship, exam form, admission, naukri form, ITR — **official last date se 7 din pehle**.
- Date sirf **sarkari site** se (link record mein). Date pakki na ho to video nahi.
- Rate kaam ke hisab se: simple form ₹49, scholarship ₹99, ITR-1 ₹299. ₹49 ITR par kabhi nahi.

### 7C. Dhanda / Pahadi video
Roz ek dhanda (dukaan, clinic, coaching, homestay, taxi…). Pahadi: "Uttarakhand ki dukaan/homestay online karo".

### 7D. Asli kaam ka namoona
Sirf jab kaam ho chuka ho **aur** customer ne ijazat di ho; naam/number chhupa. Tab tak "Namoona" likha demo.

### 7E. Kab banegi, kahan jayegi
Raat 01:30–05:00 jab VM khali. Har platform alag version: IG, FB, YT, Threads, Pinterest. Purana approval/auto flow.

---
## 8. Audience kaise aayegi (privacy ke andar)
1. Season video (section 7B) — sabse bada.
2. Comment "KAAM" → bot public reply + private reply (Meta niyam: comment ke 7 din ke andar, 1 baar).
3. YouTube: pinned comment + description link (DM nahi hota).
4. Link: bot khud — caption, YT description, pinned comment, FB comment, Telegram channel, Pinterest. Owner ek baar khud — 4 IG bio, FB button, YT links, WhatsApp status, Google Business Profile.
5. **Google Business Profile** (free, address chhupa "service area") → asli Google review.
6. Share button har page/reel link par, referral code ke saath.
7. Offline QR poster dukaan ke liye (lagane wale ko referral 10%).
8. Website: services-list par ghoomta slider (resume, GST bill, chart, form…), bada "Koi bhi kaam likho" box.
9. Ads (baad mein, ₹100–200/din test): sirf Hindi belt/Uttarakhand, "Messages" objective, sabse acchi organic reel. "Guarantee" shabd nahi.
10. Spam nahi: cold DM, bulk, bina ijazat call — kabhi nahi.

---
## 9. VIDEO AUDIT — 5 round (publish se pehle, zero galti)
Ek bhi round fail = video **rukegi**, owner ko Telegram par wajah.
1. **Tathya (facts):** har date/rate/shabd source se milao — date sarkari link se, rate `svc_rates.json` (sha lock) se, bazaar rate record se. Season video bina link = fail.
2. **Niyam/policy:** mana shabd — guarantee, pakka refund, "AI se bana", owner naam, nakli jaldi, sarkari logo/naam aisa ki lage hum sarkar hain. Platform policy (YT inauthentic, IG 50/24h, Meta).
3. **Dikhawat (visual):** frame-by-frame — kaali/khali frame, toota glyph (tofu), text overlap, caption-demo mel, safe area, padhne layak size.
4. **Awaaz/sync:** TTS bol sahi, text ke saath, loudness theek, chup jagah nahi.
5. **Owner ✅:** Telegram par namoona + audit report; owner haan kare tabhi publish (owner chahe to baad mein "auto" mode, par round 1–4 hamesha).
Audit report `data/services/video_audit.jsonl` mein hamesha.

---
## 10. Report
- **Roz (21:45):** funnel — kitne aaye → baat hui → rate → paid → delivered; kaun si reel/platform/code laaya; aaj ka paisa; pending follow-up.
- **Mangne par:** `services report N` (N din).
- **Hafta:** sabse accha kaam, sabse achhi video (IG+FB+YT views sab jodkar), kya band karein.

---
## 11. Privacy / legal
- DPDP: consent, sirf kaam ke liye, 90 din delete, "data hatao" command.
- Customer ke documents (form madad) kaam ke baad 7 din mein delete; hamare paas copy nahi.
- GST: abhi registered nahi; services threshold ₹20L. Paar hone se pehle registration.
- Refund: terms section 8 ke hisab se. Refund = referral bonus cancel.
- Personal UPI: shuru ke liye theek; volume badhe to business UPI/current account.
- Trading tools: sirf user ki strategy, SEBI retail algo niyam ka dhyan, signal nahi.

---
## 12. Aur advance features (future, owner chune)
1. **Kaam pehchan chat (bina AI kharch):** "Koi bhi kaam likho" box keyword se kaam + andaza rate + "kya documents chahiye" list.
2. **Documents checklist:** har form madad ke liye "kya kya taiyar rakhein" (photo size, signature, certificate).
3. **Last date alarm:** customer ne form madad li → agle saal/agli date par owner ke ek tap se yaad.
4. **Auto receipt PDF:** payment ke baad rasid (GST nahi, saaf likha).
5. **Hook A/B:** jo hook zyada leads laaye, bot usko zyada chalaye (views + leads data).
6. **Capacity guard:** din mein max X kaam; zyada par line ki sachchi date.
7. **Brand routing:** Pahadi lead → Pahadi brand reply; Money → Money.
8. **Kaam ki quality checklist:** har kaam type ki test list, deliver se pehle tick.
9. **Namoona library:** ijazat wale kaam (naam chhupa) — video aur website dono mein.
10. **Owner chhutti mode:** "services chhutti 3" → naye lead ko sachcha jawab "3 din baad", video ruk jaye.

---
## 13. Kram (kya pehle)
1. Form → Telegram pakka (retry + offline save) + tracking page. **Test karke hi aage.**
2. Rate-baad-samajh flow + Pay button/QR private page + CRM stage + call log.
3. Referral naya system (10%, seema, expiry).
4. Video naya (multi-kaam, season calendar, 5 round audit).
5. Comment KAAM → reply (IG/FB), YT pinned.
6. Report funnel. 7. Google Business Profile guide (mobile). 8. Advance features owner ki pasand se.

---
## Badlav log
- 24 Nov 2026: pehla version. Owner ki baatein: madad wale kaam sabse upar, ITR ₹49 nahi, 5 round video audit, referral % wala, sachchi sale/tyohar, GBP review, video sirf asli kaam ke baad, aur sab future plan.

---
## 14. Owner ki nayi baatein (24 Nov 2026, 06:24) — sab karna hai
1. Section 12 ke **saare advance feature** check karke live karne hain.
2. ITR rate pakka: ITR-1 madad ₹299, ITR-2/4 ₹699 se (build ke waqt bazaar rate dobara check).
3. **Comment/DM samajh (sirf services video par):** purane/baaki video ke comment ko bot haath nahi lagayega. Customer kuch bhi, kaisi bhi bhasha/spelling mein likhe — bot AI ki tarah samjhe (kaam, jaldi, budget, gussa, spam). Pakka na samjhe = **koi reply nahi, owner ko Telegram**. Galat comment/DM kabhi nahi. Public comment mein rate/QR nahi, sirf link/DM.
4. Bot customer ki apni bhasha/andaaz (ghar jaisi Hinglish/Hindi) mein jawab de — izzat se, bina gaali/slang ke, jhooth vaada nahi.
5. **One-click:** owner final amount daale → ek click mein customer page par QR + Pay (final amount) chala jaye; payment list update.
6. **Owner override:** CRM mein koi bhi stage/amount/note owner seedha badal sake (special case); har badlav log mein.
7. Privacy policy dobara check karke jo naya data/feature hai uski line jodna.
8. Website ke 4 brand × jitne platform (IG, FB, YT, Threads, Pinterest, Telegram channel; WhatsApp channel owner manual) — policy ke hisab se sabme.
9. Services video time: **05:00, 07:00, 18:00, 20:00** (owner se pakka: 4 video roz ya 1 video 4 jagah). Purana brand schedule **nahi chhedna**.
10. Story/post/community — jo bhi API se policy ke andar ho (IG/FB story) wo bhi.
11. Sab note karte rehna, phir ek saath build.

---
## 15. Final confirm list (24 Nov 2026, 06:31)
- Purane/baaki video ke comment ka system **jaisa hai waisa** — naya samajh wala system sirf naye services video par.
- Video/page par saaf likhna-bolna: "Hindi mein likhiye, jaise ghar mein bolte hain — English zaroori nahi, sharm ki baat nahi. Voice note bhi chalega." (Voice note: DM/WhatsApp par; bot likhit mein samjhe, nahi to owner ko.)
- Platform (website se check): 4 brand × Instagram, Facebook, YouTube, Threads + Pinterest (sabhisaabcom), Telegram channel (t.me/sabhisaab), WhatsApp channel (manual), LinkedIn company page, Dailymotion (sabhisaab). Har jagah policy ke hisab se, alag text.
- Services video: **roz 4 alag video**, IST 05:00 · 07:00 · 18:00 · 20:00. Bot views/comment/lead data se report de; time owner badlega. Purana brand schedule nahi chhedna.
- Easy + advance sab features lene hain (sec 12 + 14 + chat wale: story sticker, highlights, 5-min yaad, line-guard slowdown, mahine ka top kaam video).
- Owner ke haath wale kaam `docs/PENDING.md` mein bhi.

---
## 16. Instagram suraksha — PLAN BADLA (24 Nov 2026, email + purane docs check)
- Email: @sunonatak **2 baar band** hua — 26 Oct reinstated; 24 Nov 04:13 IST "Verify you're human" (profile chhupa), 05:17 IST reinstated.
- Purani wajah (ROADMAP 342, AUDIT_9NOV): "comment LINK, DM milega" + caption mein link/UTM = Meta ne "prohibited commercial practices / scam" shak kiya. @labhlodeals par bhi 30 din DM rok (28 Nov tak).
- Isliye **Instagram par:** "Comment KAAM → DM" **NAHI** (kisi brand par). Caption/comment mein link nahi. Sirf "Link bio mein" + services bio link. Comment ka jawab public, chhota, bina link, sirf services video par, samajh na aaye to owner ko.
- IG DM automation tab tak band jab tak: (a) 30 din bina kisi lock/warning, (b) Meta App Review (instagram_manage_messages) pass, (c) owner ki dohri pushti. @sunonatak par kam se kam 2 lock ke baad 60 din.
- Lead ka raasta: **Facebook** (comment → private reply, Meta niyam 7 din/1 baar, owner pushti ke baad), **YouTube** pinned comment + description link, **Telegram/WhatsApp channel**, **website form**.
- Services video Instagram par jayega (bina link/DM bulawa ke); text: "Kaam ho to bio ka link dabaiye".

---
## 17. Tagline + kaam ka niyam (FINAL, 24 Nov 2026 06:43)
- **Tagline:** "Koi bhi digital kaam — ho jayega"
- **Neeche line:** "Hindi mein likhiye, jaise ghar mein bolte hain"
- **Saath mein kaam dikhein + ₹10 se shuru:** `Resume ₹10 · Form madad ₹49 · Mobile/computer madad ₹49 · Bill/website… — ₹10 se shuru` (video end card, services-list hero, poster).
- **Kaam ka niyam:** list mein sirf wahi kaam jo owner **AI ki madad se** kar sake (likhna, design, form/online madad screen share par, sheet/app/website code, guide). NAHI: haath/hardware repair, ghar aakar kaam, license wala kaam (CA ka ITR file daava, vakil), aisa kaam jo AI se na ho. Mobile/computer madad = sirf screen share/call par guide, hardware nahi.
- Har naya kaam list mein daalne se pehle check: "kya AI + owner ise 100% kar sakte hain?" — nahi to RED list.

---
## 18. Build status (24 Nov 2026) - v3.8.0 bana
Sec 5-10, 12 (1,2,5,6,7,9 bot mein; 3,4,8 aage), 14, 15 (time/brand/comment/bhasha), 16, 17 - code mein. Test: bot 80, page 39, worker 22, proxy 1.
Aage (owner/API ki seema): IG story question sticker + Highlights (API nahi - owner khud), Google Business Profile (owner), FB private reply
(owner ki dohri pushti ke baad), auto receipt PDF, documents checklist, hook A/B (views data ke baad), mahine ka "top kaam" video.

## 19. v3.8.1 (24 Nov 2026)
Documents/attachment (sawal-form + files + WhatsApp vikalp), sahayak (FAQ + seemit AI), gupt page function (deploy fix), video audit 6 round. Sec 12 #1 (kaam pehchan + documents list) aur #2 (checklist) ab live.
