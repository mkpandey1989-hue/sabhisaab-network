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
v2.0.1 (29 Oct 2026): deploy() wapas (v2.0.0 mein galti se hat gaya tha). v2.0.0 (29 Oct 2026): bade VM ke hisaab se upgrade - website ZIP ki 22-file seema khatam (repo raaste, ZIP line, auto ginti
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

v2.0.6 (29 Oct): CHAT.md (owner ke hukum, secret chhupa kar), redirect jaanch, website page par video link (videos.json),
Instagram max 5 hashtag + chhota caption wali koshish, naye khule kaam (Validate fix, W6, FB Stars steps).
