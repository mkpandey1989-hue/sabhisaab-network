# PLAYBOOK - audience + traffic ki ranneeti (koi bhi AI/developer pehle ye padhe, phir AI_START.md)
Owner: Manoj. Lakshya: zyada audience + website traffic + monetization, BINA spam, poori tarah automatic. Ye file 'kyun' batati hai;
code kahan hai wo bhi. Badlav karo to yahan bhi likho.

## 1. Sawal (content) - kya chalta hai
| Channel | Kya | Kyun |
|---|---|---|
| Pahadi Hisaab | Uttarakhand GK, Garhwali/Kumaoni boli, pahad ke purane naam | 'Uttarakhand GK' UKSSSC/UKPSC wale khojte hain; pahadi log pehchaan saabit karne aate hain |
| Sab Hisaab Money | Ego test, exam ganit trick, speed math, umar/calendar/sudoku | 'maths tricks', 'SSC railway maths' khoje jaate hain |
| Labh Lo Deals | Discount/percentage ganit (50%+40% jaise jaal), rang-milan, alag kaun | ego-jaal + website ka Discount calculator |
| Suno Natak | Paheliyan, coding (BOOK=ANNJ), series, ghadi, disha, ulte-pulte shabd | 'paheliyan with answer', 'dimag wali paheli' sabse khoje jaate hain |
- BAND (3 aam channel): SIP/FD/RD/loan-app/PPF/bima/share - salah wale, trend gaya, SEBI jokhim (qplan.BLOCK_RX).
- Sabse achha sawal = 'aasaan dikhe, log jaldi mein galat bolein' (17 bhed, 9 bachi; 2nd ko overtake = 2nd; 50%+50% != free).
- Hafte-war din-war type: app/qplan.py PLAN. Ek sawal ZINDAGI BHAR dobara nahi, kisi bhi channel par (pipeline.q_lifetime.json);
  ek jaisa saancha 4 din nahi (qplan.pattern). Jawab hamesha jaancha hua (qbank do-dimaag / compute).

## 2. Sawal puchhne ka tareeka (hook) - app/hooks.py
8 andaaz rotate: seedha, samay, ulta ('jawab X nahi'), bahas (Rahul vs Amit), team A/B, pehchaan, shart, jasoos.
X hamesha GALAT vikalp (sahi ke sabse paas). NAKLI AANKDA KABHI NAHI ('99% fail', '95% galat') - YouTube/Meta/AdSense misleading.
Channel-wise pakka: '⚙️ Channel setup'.

## 3. Video (Shorts) - app/design.py, render.py, answers.py
- Pehle second se sawal + 4 vikalp + hook line; vikalp poori reel; timer 2nd scene se; jawab video mein NAHI (code #N -> /jawab).
- Aakhri bolna ~3 sec. 'संकेत' hint nahi. Flash nahi (1 sec mein 3+ nahi). AI awaaz ka label description mein.
- Rang/layout/andaaz: learn.choose - naya 3 baar aazmao, phir jo zyada dekha gaya uska zyada (25% khoj). 'look haal'.
- Rang (palette) + layout + 24-look roz baari-baari (state palettes_ok/layouts_ok, puzzles.LOOK24). Naye rang/layout bot khud
  namoona banata hai -> owner haan ya 24 ghante baad apne aap list mein.

## 4. Lambi 'hub' video (website traffic ka asli pul) - app/hubvideo.py
- Shorts ki description ke link click NAHI hote; lambi video ke hote hain. Isliye har brand har hafte: Som Pahadi, Budh Money,
  Shukra Deals, Ravi Suno Natak (01:30) - is hafte ke 8-12 jaanche sawal, asli chapters, har sawal ka /jawab#cCODE link.
- Title/thumbnail SEARCH wale shabd se (hubvideo.SEO): 'Uttarakhand GK Quiz in Hindi', 'Hindi Paheliyan with Answer',
  'Maths Tricks Quiz', 'Discount Percentage Tricks' - 3 rup, har hafte alag. Render fail -> saada tareeka (photo/3D bina).
- Owner ek baar: Studio mein Shorts ka 'Related video' = brand ki hub (API nahi deta).

## 5. Website par laane ke raaste
/jawab (code se khoj, streak), har tool page par 'Aaj ka sawal' (install-app.js + jawab.json), hub video ke links, Pinterest pin,
Telegram/WhatsApp, YouTube channel Links (owner). GSC shabd par sirf pakka-ganit FAQ (kwfix). Bing priority (website.bing_plan).

## 5b. v2.8-2.9 ke raaste
Web Story (Google Discover), roz 1 tool pin (Pinterest), /jawab par tap-vote + asli % (30+), score card share, zindagi bhar ka
jawab-register, karaoke subtitle, tyohaar 2+ website se pakka + tithi ka samay, sawal-type views se hafte-war.

## 5c. v2.9.2
/jawab halka (naye 40 + register khoj), video publish hote hi 1 min mein jawab live, final_authority jaanch, OneSignal opt-in
(roz max 1), Telegram quiz bot (opt-in), Telegram welcome pin, official channel suchi (nakli account se bachav).

## 6. KABHI NAHI (policy)
Nakli % / nakli vote / 'Genius certificate' / 'IAS sawal'; daravna jhootha hook; jawab CTA mein leak; auto-next/auto-redirect;
ek saath dher post (token aate hi 20 min farak - bot.reopen_jobs); Instagram DM/link (28 Nov tak band, privacy sec. 8);
commenter ka naam AI ko; bina jaanch paise ke aankde; poori site ek saath badalna; links.html sitemap/IndexNow mein.
