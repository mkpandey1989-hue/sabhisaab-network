# Sabhisaab Network bot v1.0 (sirf VM par, 24x7)

Platforms: YouTube (4) · Facebook (4) · Instagram (4) · Threads (4) · Telegram channel · Pinterest (sandbox->standard)
Dimaag: Gemini (model khud dhoondhta hai, sabse naya pehle, seema par neeche), normal Hindi/Hinglish baat, confirmation.
Roz: subah 06:00 self-audit, 07:30 khaas din idea, slot se 3 ghante pehle video, 10:00 login yaad, 12:00 auto tyohaar
story, har 2 ghante comment, 21:30 report, 22:00 views se seekh. Ravivaar: 01:30 lambi video, 20:00 hafte ki seekh +
agle 7 din ka plan, 21:00 hafte ka hisaab.
Settings chat se (code badle bina): samay (ek se zyada slot), roz ki seema, auto-upload, naye topic, plan.
Data: data/state.json, data/diary.jsonl, data/learn.json (restart ke baad bhi yaad).
Niyam: chowkidar/trading/system ko kabhi nahi chhedna. Secrets sirf secrets/ (700/600).

v1.0: 3-star audit (technical + policy/samaj + Google-search fact check), tyohaar Google search se pakke (tithi/muhurat,
aaj/kal bhed par dono din), YouTube par theek samay ka schedule (publishAt) + alag upload line, autopilot, duplicate
jaanch (asli channel), company meeting (vibhaag), owner ke niyam (self-correction), Pinterest Standard khud pehchanna,
GitHub par docs/STATUS.md + docs/HANDOVER.md (koi secret nahi). Dekhein docs/HANDOVER.md.

v1.7.0 (28 Oct 2026): privacy milan - commenter data 30 din me apne aap saaf, "data hatao <naam>", /privacy, roz website policy jaanch; deploy race + Pinterest test fix; install mein asset suraksha. Dekhein docs/HANDOVER_v3.md section F.
v1.8.0 (28 Oct 2026): saare channel link ek jagah (config.LINKS) + WhatsApp, video par https://sabhisaab.com/ safe zone mein, comment jawab mein usi video ka page link, post se pehle link jaanch, tool ginti website se apne aap. docs/HANDOVER_v3.md section G.
v2.9.8 (29 Oct 2026): deploy() wapas (v2.0.0 mein galti se hat gaya tha). v2.0.0 (29 Oct 2026): bade VM ke hisaab se upgrade - website ZIP ki 22-file seema khatam (repo raaste, ZIP line, auto ginti
sync, din mein 10 naye page ki suraksha), seedha VM se Cloudflare deploy (cf token), website gyaan + doctor (siteknow.py),
khud-upgrade + auto-heal + docs/ESCALATE.md (upgrader.py), gyaan-bhandaar + data dhoondh kar sochna (kb.py, kb.md),
privacy: commenter record platform-wise + drafts 30 din, 7 backup, 30 din log, engine.log rotate, local Telegram API vikalp.
v2.0.2 (29 Oct 2026): guardtext.py - har public text mein website ki asli tool ginti + poora https://sabhisaab.com/ link
(sab platform API par ek jagah); purani YouTube description roz raat theek (marketing.recount); GSC query -> video topic +
page sudhaar salah (marketing.gsc_ideas, Ravivaar); ZIP ke 15 min baad auto deploy; GitHub band ho to bhi kaam VM par
(copy baad mein); Ravivaar GitHub par sirf taaza copy; site/policy nigrani 3/6 ghante; slot paas ho to 1 core par render
+ bank script se aakhri koshish (post kabhi na chhoote); bahar ke topic par sabse milta tool page; comment jawab video ke
context ke saath, dohraav nahi.

v2.0.3 (29 Oct 2026): Instagram par koi link/UTM nahi + "comment LINK/DM" bulawa band + @sunonatak DM rok (27 Nov tak);
IG upload fail par IG-safe dobara encode; report theek samay par (website 08:00, tyohaar 07:30, din 21:30; badlav dohri
pushti se); topic/niyam/platform/report setting dohri pushti; khule kaam apne aap jaanch + docs/PENDING.md roz; "roadmap do"
/ "docs do"; SEO diary (Shanivaar 21:00); script bank raat 01:00 bhara rehta hai. Koi bhi AI: pehle docs/AI_START.md.

v2.0.4 (29 Oct 2026 raat): reply karke 'delete' = asli delete; bot jhootha daava nahi karta; har hukum ka record +
docs/QUERIES.md; kaam/query par docs 10 min mein GitHub; 'chowkidar file do' (secret chhupa kar); 'ho gaya' par "pehle hi
ho chuka"; @labhlodeals DM rok; naye khule kaam (Chowkidar sahi tareeka, FB Stars/Affiliate, Bing sitemap, GSC wajah, W4).

v2.0.5 (29 Oct raat): Bing key / Meta secret mix-up theek (32-akshar key par poochhta hai, jaanch + rollback,
install par apne aap sudhaar); 'meta secret <x>'; KEYWORDS bank roz (docs/KEYWORDS.md, 'keyword haan <no>');
HEALTH.md (har brand x platform); naye khule kaam.

v2.3.2 (3 Nov 2026): PRO neon thumbnail, video par pura website pata, bank bhi sawal-wala + 14:05 taazi-seema bank.

v2.5.7 (5 Nov 2026): YouTube comment ka alag login ('yt comment login'), privacy assistant ('privacy ig theek'), Telegram quiz poll, /jawab coverage check, ypp haal asli watch hours, policy fix ('1% Genius' hata). 13 naye pending kaam.
v2.5.6 (5 Nov 2026): /jawab par purani reels ke jawab 1,200 tak (anchor ke saath), Agla jawab / channel nav. v2.5.5 neeche.
v2.5.5 (5 Nov 2026): watchdog - bot khud nigrani karta hai, dikkat par step-wise 'kya karein' Telegram par; ypp/adsense haal hafte mein apne aap; 'features' command; docs/FEATURES.md.
v2.5.4 (5 Nov 2026): namoona video par sirf ek '⬇️ Download (original file)' button (baaki sab waisa). v2.5.3 neeche.
v2.5.3 (5 Nov 2026): jawab-link UTM (platform+channel+code), YouTube comment/purani description mein jawab-link, /jawab par channel links + WhatsApp share, Telegram digest (dohri pushti, default band), 'site scan' (toote link/patle page), uptime alert, 'ypp haal', Story link-sticker reminder, 22 naye pending kaam. docs/ROADMAP.md v2.5.3.
v2.5.2 (5 Nov 2026): /jawab audit fix - audit gate (force=False), regex crash, 4 ank unique reel code (overwrite band), marker live-check, reconcile, deploy canary, AdSense taiyari (adsense haal / adsense id), SEBI phrase scan, install.sh docs/test fix. Dekho docs/AUDIT_5NOV2026.md.
v2.5.1 (5 Nov 2026): /jawab page live hone tak link Telegram par (404 kabhi nahi); khaali page bhi site audit pass.

v2.5.0 (5 Nov 2026): reel mein sirf sawal, jawab website /jawab + Telegram par; pehle second ka jawab-leak band; har platform par jawab-link.

v2.4.2 (5 Nov 2026): AI chitra mein ank/likha nahi (prompt saaf + peeche dhundhla).

v2.4.1 (4 Nov 2026): galat page link (googleXXXX) band, Threads Fatal ka ilaaj, pehle scene par timer nahi, AI chitra mein likha nahi, 365 din dohraav-rok.

v2.4.0 (4 Nov 2026): AI-art (Cloudflare), 43 look, layout khud, Pinterest sections + A/B, token/API watcher, encrypted offsite backup + drill, provenance, awaaz se hukum, competitor vishay, 1:1/16:9, test-gate install.

v2.3.7 (4 Nov 2026): button audit, sach-bolta bot, roz khud-jaanch, Pinterest drip pin, routines, kul hisaab.

v2.3.6 (4 Nov 2026): daily report timeout theek, sawal-bank bina Google bhi, pahad ke parv offline, FB photo-post, naye 7 look, rang khud aazmaye (24 ghante auto).

v2.3.5 (4 Nov 2026): Blender 5 theek, anant sawal-bank (Google jaanch, bina dohraav), khud seekhne wala sawal-chunav.

v2.3.4 (4 Nov 2026): 3D jaanch/repair, roz alag 3D, naye default sawal (ulte-pulte shabd, purane shabd, pahad ke purane naam, sudoku, series, coding, ghadi, disha, umar), sab channel mila kar koi sawal dohraav nahi.

v2.3.3 (3 Nov 2026): sirf sawal-reel, apna 3D (Blender, 28 scene), 24 PRO-ELITE look (chunna + namoona), dimag+pyaar combo format, FB comment jawab, best time.

v2.3.1 (3 Nov 2026): har channel roz 2 sawal-wali reel (Gemini quiz + jaancha puzzle/Pahadi GK), safe-zone design, Bing URL API, PENDING saaf.

v2.3.0 (3 Nov 2026): Premium Neon design (default), 11 puzzle mode, awaaz SFX, 50-button Pro Deck, spare reel, post-taala, Gemini Blindfold, asli panchang, DPDP ledger - v11 ke saare feature jaanch ke saath. Manual: docs/SAMPLE_STUDIO.md.

v2.2.0 (3 Nov 2026): Sample Studio (namoona dekh kar look pakka, agla/mitao/pakka dohri pushti), din-plan (kis din kya), koi sawal dohraav nahi, naye thumbnail rang. Manual: docs/SAMPLE_STUDIO.md.

v2.0.6 (29 Oct): CHAT.md (owner ke hukum, secret chhupa kar), redirect jaanch, website page par video link (videos.json),
Instagram max 5 hashtag + chhota caption wali koshish, naye khule kaam (Validate fix, W6, FB Stars steps).
