# SERVICES HANDOVER — koi bhi AI / developer services par kaam se PEHLE ye padhe (v3.9.3, 24 Nov 2026)

Owner: Manoj bhai (Hinglish, mobile + Telegram). Ek-ek baat poochne ke bajaye poora kaam ek saath, test karke, ek ZIP.
Ye file = services ka shuru se ab tak + aage ka plan + KYA KARNA / KYA KABHI NAHI. Saath mein: `docs/SERVICES_PLAN.md` (sections 0-21),
`docs/AUDIENCE_SERVICES.md` (audience ki likhawat), `docs/COMMANDS.md`, `docs/PENDING.md` (owner + AI ke khule kaam), `docs/LESSONS_NEVER.md`.

---

## 1. Ye kya hai (ek line)
sabhisaab.com par "Koi bhi digital kaam — ho jayega" (₹10 se shuru) — form madad, resume, mobile madad, ITR madad, website, app, bot,
trading TOOLS (signal nahi), sarkari form/bharti/yojana madad, server/cloud, Excel, design ... **1030 kaam** (2 chhupe: SEBI order-bot). Customer Hindi mein likhta hai → bot Telegram par owner ko → owner baat karke rate →
customer ke gupt page par 'Haan' + UPI QR → kaam → rasid → bahi-khata. Roz 4 services video sab platform par.

## 2. Kaun sa hissa kahan (architecture)
| Hissa | File | Kaam |
|---|---|---|
| Rate list (asli) | `app/svc_rates.json` (generator `app/scripts/svc_gen_rates.py`) | 1030 kaam (112 purane + `svc_more_items.py` se 918 naye, 27 dabbe): price, floor, max, market, kw, `hide`/`novideo`/`nostrike`/`new`; RED (mana) list; discount niyam. Daam ka aadhar: `docs/MARKET_RATES.md`. **sha jaanch** - haath se mat badlo, generator chalao |
| Cloudflare worker | `app/svc_worker.js` (`sabhisaab-leads vX`) | /lead (jaanch: honeypot, 6/ghanta, phone 10 ank, bekaar likhawat, Aadhaar/OTP chhupa), /q gupt page data, /q/ok, /q/info, /q/file, /q/rate, /help (FAQ + Workers AI), /find (tracker), /ev, /clog; admin /{KEY}/pull,set,add,log,file,fdel,stats,ping. KV free 1000 likhna/din -> `sput` |
| Website se worker | Pages Functions `functions/api/[[path]].js` (proxy, PK secret), `functions/q.js` (gupt page, noindex) | bot likhta hai, `.gitignore` - GitHub par NAHI |
| Website files (bot likhta) | `site/svc-cfg.js`, `svc-offer.js`, `svc-intake.js`, `svc-kit.js` | kit = form jaanch/label/upload/help; `svc_kit_v` badle to usi din likhe |
| Services page | `site/services-list.html` (generator `app/scripts/svc_gen_list_page.py`; v3.9.2 se har kaam HTML mein - 27 `<details>` dabbe, Google ko dikhta; bot ek baar `website.svc392_apply` se lagata hai: list + terms#rate + har page footer 'Rate List' link + sitemap), `/services` (AdSense wala - kam chhedo) | form + tracker + intake |
| Gupt page | `app/assets/svc/q.html` (generator `svc_gen_q_page.py`) | rate, Haan, QR, details/file, rating, status |
| Bot - CRM/lead | `app/svc.py` | ingest, card, rate, paid (rasid), deliver, refund, referral, offer/sale, reminders, report, today_report (23:58), manual, bahi, backup, night_audit (90 din), nl (likha sawal), Services menu |
| Bot - video | `app/svcvideo.py` | pick_day (rotation), ctx_for (likha/bola), render (frame + Kokoro + ffmpeg), audit_video (6 round), make_day, tick |
| Awaaz | `app/tts.py` (+ `tts_once.py`) | Kokoro Hindi; `synth_checked` = jaanch + model dobara + alag process; TTSDead |
| Doctor | `app/svcdoctor.py` | har 5 min: awaaz, aaj ki video bharo, worker ping, atka nishan; sirf badlaav par sandesh |
| Comment | `app/svccomment.py` | sirf services video par; samajh (kaam/daam/bharosa/gaali/spam/mana) -> jawab 7-45 min baad ya owner ko sujhav |
| Kaam ke sawal | `app/svc_intake.py` | har kism ke sawal + ek zaroori (REQ) |
| Upload | `app/pipeline.py` | services job = `design: services_ad`; YT/FB/IG/Threads/Pinterest/Dailymotion/Telegram + story; `auto_thumb` 1/2/3 ghoomta |
| Mobile fix | `app/website.py` `mobile_fix_*` | saare page par /*m412*/ CSS (bot khud, har aane wali ZIP par bhi) |
| Data (VM) | `data/services/*.jsonl` | leads, events, calls, payments, bahi (zindagi bhar), video_history, video_audit, comments, push_queue; saal-bhar backup `data/services_year/` |

## 3. Ek customer ka safar
1. Form (services-list / services / comment / phone par `manual ...`) -> browser mein jaanch (naam, 10 ank mobile, bekaar likhawat, kaam ka 1 zaroori sawal) -> /api/lead (same-origin) -> worker -> KV + Telegram turant.
2. Bot har kuch minute `pull` -> CRM card (WhatsApp / call log / rate bhejo / mana).
3. Owner baat karta hai (call log), `quote SH.. 499 naam` -> customer ko message (kul, shuru mein advance, baaki, samay, page link).
4. Customer gupt page: Haan -> QR (sirf yahin owner ka UPI naam) -> `paid SH.. 499` -> rasid WhatsApp -> kaam -> `deliver SH..` -> files mitti.
5. Bahi-khata mein har ghatna (naam/number/sandesh nahi). 90 din baad sandesh/PII mitta (privacy page jaisa).

## 4. Roz ki services video (kaise chalti hai)
- Default CHALU (`services video band` se band). Raat 01:30 ke baad `make_day`: 4 brand, slot 05:00 · 07:00 · 18:00 · 20:00 IST (har din brand ghoomte, brand ki apni roz wali video se 75 min door). Raat chhooti to din mein 19:30 tak bache slot.
- **Kaam ka chunav (v3.9.2):** saare 1017 video-layak kaam har channel par (category-wise nahi, audience mix hai; naye kaam `_auto_kaam` se - screen par kaam ka naam, awaaz mein dabbe ka Hindi naam). Sabse kam dikha kaam hamesha pehle, ek din 4 brand mein koi kaam dohra nahi, ek video mein ek kism ke max 2, madad + ₹99 tak wala na aaye to aakhri ko badlo, pehla kaam sabse sasta/bada bazaar-farak (hook). ~2 mahine mein poori list (test: 56 din mein 1017/1017).
- **v3.9.3 sabse badi baat baar-baar:** 0 sec se hi patti "₹10 से शुरू · कोई भी डिजिटल काम"; hook ke turant baad USP scene (6 tarah: ₹10 से शुरू / शुरुआती दाम / 1000+ काम / बाज़ार से X% तक कम - brand+din ke hisaab se alag); har kaam par neeche alag USP patti (`RIBBON`); kaam 3 par awaaz mein yaad (`REMIND`); CTA par phir. X = `usp_pct()` (rate list ka SACH: jahan 10%+ kaam utne saste - aaj 70). **"Limited time" aur "90% discount" NAHI** - 90% sirf ₹10 Resume par sach, aur offer lambe chalenge (CCPA dark pattern); "शुरुआती दाम" sach hai (terms#rate).
- Naye 1000 kaam ka screen: `task` namoona (grahak ne kaam likha -> 'हो जाएगा, ₹X से') - jahan dabbe ka screen mel nahi khata (fix/care/cloud/daftar...).
- Awaaz 48 kHz stereo (loudnorm 96k bana deta tha -> IG ProcessingFailedError). Audit round 4 jaanchta hai.
- Owner ka **namoona** + koi Thumb = TURANT post + us brand ka AAJ ka services slot (baaki roz wali radd, YouTube se bhi; doctor dobara nahi banata). Kuch na dabaya = kuch nahi.
- Pinterest (roz ~10-12) / Dailymotion (roz 3) ki seema mein services ki 2-2 jagah pehle rakhi (`svcvideo.reserve`) - normal video kam.
- Har frame par neeche: **"* शर्तें लागू · पूरी शर्तें: sabhisaab.com/terms"** (ASCI/CCPA). Kati keemat sirf jab bazaar sach mein mehenga (sarkari form par nahi). Description mein 'Sharten laagu' line (bina link - IG safe).
- Har video: 6 kaam, alag rang (12 LOOKS), hook (12), layout L/R; (set, rang, hook, layout) zindagi bhar dohra nahi. Season (sirf .gov.in/.nic.in tareekh) aur hafte ki sale asli.
- Awaaz: har scene alag (Kokoro), screen ka bada likha sab bola: "... रुपये से शुरू", site, comment, brand code. 58s se lambi = chhota rup.
- Audit 6 round (tathya/rate, mana shabd, frame, awaaz, aakarshan, owner). Fail = naya set (3 baar); sirf awaaz ki galti = "awaaz bimaar" -> doctor.
- Pass -> Telegram par preview + thumbnail; jawab na mile to slot se 20 min pehle autopilot (thumbnail 1/2/3 ghoom kar).
- Platform: YT Short, FB Reel + story, IG Reel + story (Suno Natak IG par NAHI - 2 baar ban), Threads, Pinterest, Dailymotion, Telegram. Alag FB photo-post nahi.
- Trading tool wale kaam: "टिप/सिग्नल नहीं", description mein jokhim line; "profit/मुनाफ़ा/पक्की कमाई" audit rokta hai.

## 4b. Services PAGE-POST + MASTER SCHEDULE (v3.9.3)
- `app/svcpost.py`: har brand ke FB page par roz 1 photo-post (1080x1350: ₹10 se shuru + 6 kaam + link services-list utm + sharten laagu), us brand ke shaam ke best ghante par (asli views), reel se 40 min door. Samay ek baar tay = PAKKA (`svc_post_times`), badlav 'post samay pahadi 19:30' + dohri pushti. IG par nahi (link mana). Purani 'sawal photo-post' ek din chhod kar (feed bhari nahi).
- `app/master.py`: '🗓 Master schedule' button (main + services menu) - har brand: sawal reel, services reel (aaj/kal), page-post, story/channel, roz ke baaki kaam. 'video kab hai' wale sawal par bhi.
- Raat 00:20-04:30 aaj ki saari sawal reel ban kar line mein (pehle 3 ghante pehle banti thi) - `state night_make` False = purana tareeka.
- Roz safai (`guard._old_media`): post ho chuki video ki mp4 10 din baad, IG-safe copy 1 din, services ki radd video 3 din (meta/thumbnail rehte).

## 5. KABHI NAHI (services)
- "Limited time / सीमित समय / जल्दी करें / only today / offer khatam" - offer lambe chalenge (CCPA dark patterns). Audit rokta hai.
- Broker par apne aap order lagane wala bot (SEBI 2025) - t-algo/t-crypto `hide`. Sarkari kaam mein naukri/yojana/praman patra ka vaada ya nakli document.
- Owner ka naam/awaaz/chehra kisi video/post mein. UPI QR (owner ka naam) sirf customer ke gupt page par.
- "AI se bana" / "insaan" wording ads/services mein. "Guarantee", "100% pakka", "sirf aaj", nakli jaldi.
- Cold DM, bulk/WhatsApp spam, comment->DM (koi brand), IG caption/comment mein link.
- Customer se password/OTP/Aadhaar/PAN/bank number. OTP customer khud daale.
- Trading tip/signal, kisi ka account chalana, kamai ka vaada. RED list ke kaam (scraping, nakli review, hacking, betting, Aadhaar badalna, ghar aakar repair).
- `svc_rates.json` haath se badalna (sha). Rate badle -> generator + website rate list + AUDIENCE doc.
- `/services` (AdSense) par bada badlav; faltu cheez chhedna.
- Secret GitHub par (`functions/` gitignored; VM .env / svc.json).
- main branch par push (VM khud main sync karta hai) - sirf `wip-v3.8.0` branch, owner ZIP Telegram se lagata hai.
- Pakki setting (fixed) owner ki do baar haan ke bina badalna. Naya bada plan = pehle plan, owner "final" bole tab code.

## 6. Kaam karne ka tareeka (AI ke liye)
1. `git clone`, `docs/AI_START.md` -> `docs/PENDING.md` -> ye file. VM ka haal: main branch ki `docs/CHAT.md`, `STATUS.md`, `HEALTH.md` (VM bhejta hai).
2. Badlaav `wip-v3.8.0` par; VERSION badhao; `docs/ROADMAP.md` mein naya section; COMMANDS/PENDING update.
3. Test: `tests/smoke.py` (VM par install gate - poora chalta hai). Services hissa alag: smoke ka "# ---------------- v3.5.0" se aage. JS: `tests/svc_js/ui.js` (jsdom), `wt.mjs` (worker), `ft.mjs` (proxy). Video: nakli awaaz se render + audit (Kokoro yahan nahi chalta - asli awaaz owner ke namoona se).
4. Website: VM ka audit (`scripts/audit.py`) + calc_test gate. 360/412px par overflow jaanch (Playwright).
5. ZIP: `git archive` -> owner Telegram par bhejta hai -> bot install + smoke + restart + "GitHub copy". Badi website ZIP ki jagah bot se lagao (Telegram 20 MB).
6. Owner ko jawab: chhota, Hinglish, kya hua + uska kya kaam.

## 7. Owner ke Telegram command (sabse zaroori)
🧾 Services (menu) · aaj kitne customer aaye · aaj/kal/is mahine ki sale · khule kaam · SH.. (haal) · manual call <naam> <mobile> <kaam> ·
baat SH.. <note> · bahi [SH..|3210] · quote SH.. <rakam> <naam> · paid SH.. <rakam> · deliver SH.. · SH.. <stage> ·
services video namoona/chalu/band · services instagram <brand> chalu/band · services chhutti N · services seema N/hatao ·
services shabd X = Y · services awaaz sudhar X = Y · services doctor · services form jaanch · season add/list. (Poora: COMMANDS.md)

## 8. Aage ka plan (kram se)
1. (Owner) Bio/pin/GBP - AUDIENCE_SERVICES.md. Pehle 2 hafte services video + comment ka nateeja `services 7 din` se.
2. Asli Kokoro awaaz par 'vakyon ke beech ruk' ki ginti dekhna (v3.9.0 se awaaz-track se) - audit fail ho to `services doctor` + audit sandesh ka screenshot.
3. Hook A/B: kaunse hook/kaam se lead aaye (brand code + video_history) -> report mein; kamzor hook kam.
4. Mahine ka "sabse zyada maange gaye kaam" video (asli lead ginti se).
5. Customer review (sirf asli, kaam ke baad) -> /reviews page par; Google Business Profile.
6. AdSense review ke baad hi /services par badlav.
7. Har naya kaam: `svc_more_items.py` (ADD/CATS) -> `python3 app/scripts/svc_gen_rates.py app/svc_rates.json` -> `svc_gen_list_page.py` (sitepatch) -> test. Video KAAM apne aap (dabbe ki `v`), intake dabbe se (`svc_intake.kind_for`).
8. (Owner) Search Console: /services-list aur /services-demo 'Request indexing' (site patch lagne ke baad). Owner ki poori list (18-21 dabbe) aaye to ADD badlo.
9. 2 hafte baad: kaun se naye dabbe se lead aaye (svc report) -> kamzor dabbe ka video hissa kam.
