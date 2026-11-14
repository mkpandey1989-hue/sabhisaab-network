# WORKPLAN - SABSE PEHLE YE PADHO (koi bhi AI / developer)

## AGLA AI SABSE PEHLE: docs/TRAFFIC_PLAN.md ka hissa 5 (T1 -> T9) - Fable 5.2 ke audit ke baaki sudhar. Owner ka #1 lakshya = impression/click.
- 12 Nov, v3.1.2 + website W12: nali page par Hindi (Devanagari) ka TEST + 3 page ke title/description. 26 Nov ko naapna (T1).
- Naye feature/naye calculator page NAHI. Ek-ek number ke alag page, Indexing API, link khareedna - KABHI NAHI (TRAFFIC_PLAN hissa 7).

## 12 Nov 2026 - v3.1.1 [FABLE 5.2]: owner ki reel dekh kar video ki 6 kami theek (ROADMAP v3.1.1)
- Sawal ab bola jaata hai; bharti line hati; sochne ki chuppi sawal ke hisaab se (scene["hold"]); subtitle vaakya-war; lehja 'aap';
  exam card beech mein + vikalp ek rang. VM par asli awaaz ke saath pehli video owner kaan se sune - yahi ek jaanch baaki.

## 12 Nov 2026 - v3.1.0 [FABLE 5.2]: Claude Fable 5.2 ka POORA AUDIT HUA -> docs/AUDIT_11NOV2026.md (naya AI: pehle wahi padhe)
- Nateeja ek line mein: machine theek, AUDIENCE nahi (28 din: YouTube 3,151 views, site 10 log/hafta, Google ~45 impression). Wajah
  feature ki kami NAHI - (1) saanche wali AI video par YouTube/Meta kamai nahi dete (July/Mar 2026 niti), (2) nayi domain + calculator
  ka mukabla, (3) reel se site ka pul kamzor. ISLIYE: naye feature/naye calculator page MAT banao; hissa H ka plan chalao.
- v3.1.0 mein theek: Hindi mein doosri lipi (hindifix), final authority +5 (finalgate, 'final jaanch'), tyohaar slot ki vishay-rok,
  /jawab JSON-LD, Bing ko purane page dobara nahi, IP public nahi, sitemap lastmod sync, tests/smoke.py naya.
- Owner ke 4 naye faisle PENDING mein (apni awaaz, Gemini billing, apt upgrade, video file). Update ab hafte mein 1 se zyada nahi.
- Agla (chhota, jab data aaye): vote counter par Turnstile; updater tests/ bhi GitHub par bheje; quizbot poll backoff.

## ABHI KA HAAL (11 Nov 2026, 07:35 IST) - v3.0.2
Pehle docs/OWNER_RULES.md (owner ke 20 pakke niyam), phir ye hissa. Jo ✅ hai use DOBARA mat banao.

### ✅ HO CHUKA (live par pakka)
- Video: 4 channel roz, rang/card/andaaz/naam-jodi rotate, exam card + 6 diagram paheli, 50-50, karaoke, final authority jaanch.
- /jawab: sirf aakhri 8, baaki zindagi bhar ka register (khoj), video ke 1 min mein live + 15 min baad jaanch.
- Comment: YouTube (4 channel comment-login, Pahadi 11 Nov 04:57 juda), IG, FB auto-jawab; gande comment hide/reject;
  'Comment haal' sirf aaj ka + channel-wise; alag thread.
- Quiz bot (@SabHisaabQuizBot) relay se chal raha (11 Nov 04:22 'chal raha ✅'); OneSignal button website par; quiz poll chalu.
- Web Story: Cloudflare Zaraz /stories par band (Configuration Rule) -> 11 Nov 07:32 GSC 'Web Story is valid' ✅; 'amp jaanch'.
- Analytics login 4/4; PageSpeed hafta-war; traffic 15-din ausat roz 21:05; Pinterest khane; Bing IndexNow; official channel page.
- VM audit + Gemini PDF ke sahi point theek (v2.9.8); baaki kyun nahi - ROADMAP v2.9.8.

### ⏳ OWNER ke haath (bot ki '⏳ Pending' list mein bhi)
- 16 Nov: AdSense apply -> bot mein 'adsense id pub-...'.
- Backup password: 'backup password reset' -> save -> 'maine save kar liya'.
- Marzi: WhatsApp forward, IG story sticker, YT comment pin, jawab digest, Private DNS.

### ⏳ CLAUDE/DEVELOPER - khula kaam: KOI NAHI (11 Nov). Naya kaam sirf owner ke naye screenshot/shikayat se.
### Galti aaye to: pehle GitHub docs/CHAT.md (bot chat) + screenshot -> asli wajah -> test -> ZIP. Andaze se badlaav nahi.

---
# WORKPLAN - owner ki poori 'advance pro' list (Claude, 10 Nov 2026 se). Har ZIP ke baad yahan haal badalta hai.
Niyam: ek-ek feature, har ek ka test, policy pehle (spam nahi, nakli % nahi, bina jaanch number nahi). Owner 'continue' likhta hai.

| # | Kaam | Haal | Kahan |
|---|---|---|---|
| 1 | Hafte ki hub video 'is hafte ke 8-12 sawal' (har brand har hafte, asli chapters, har sawal ka clickable /jawab link) | ✅ v2.7.0 | app/hubvideo.py, render scene_starts, audit.description |
| 2 | Web Stories (Google Discover/Search) - har hafte har brand ki 1 story jaanche hue sawal se | ⏳ agla | site /stories/ + bot |
| 3 | Asli % engine (Cloudflare Worker anonymous vote, 30+ vote ke baad hi %) | ⏳ | worker + /jawab |
| 4 | Video V1-V10 naya look (option ek-ek karke, timer, blur-reveal, micro-motion) | ⏳ (VM par render test chahiye) | design.py |
| 5 | Quality governor (har platform ka alag hook/caption, templated jaanch) | ⏳ | pipeline captions |
| 6 | Tyohaar/exam calendar se sawal (Diwali sale, ITR date, board exam) | ⏳ | topics/weekplan |
| 7 | Telegram opt-in quiz bot (roz ka sawal, score) | ⏳ owner: BotFather se naya bot token | naya module |
| 8 | Retention learner (YouTube Analytics se hook A/B) | ⏳ owner: '/analytics' login | learn.py |
| 9 | Result share-card + embed widget | ⏳ | site |
| 10 | Top 5 tools English (reviewed, hreflang) | ⏳ | site |
| 11 | Google Fonts self-host | ⏳ (270 page - dheere) | site |
| 12 | Pinterest: har tool page ki pin (alag din, spam seema ke andar) | ⏳ | pinterest.py |
| 13 | Sawal puchhne ka tareeka (owner ka Level 1-5 blueprint: seedha, 5-sec, 'jawab X nahi', Rahul vs Amit, Team A vs B, topper ya jaldbaaz, pehli baar mein, jasoos) - bina nakli % | ✅ v2.7.1 | app/hooks.py, 'hook haal' |
| 14 | Backup password reset (padhne-layak) + turant naya backup + save hone tak roz yaad | ✅ v2.7.1 | ops.reset_password, 'backup password reset' |
| 18 | Spelling galti samajhna (hook 8 naam + 38 chhote command + Gemini ko niyam) | ✅ v2.7.2 | hooks.match, bot.fuzzy_command, brain |
| 19 | ⚙️ Channel setup: har channel ki setting line-wise (look, sawal ka tareeka 8 namoone ek hi asli sawal par, rang/layout, samay) + channel-wise FINAL | ✅ v2.7.2 | setupwiz.py |
| 20 | Hafte-war sawal schedule (din-war type, block SIP/FD/RD/loan, dohraav-saancha, bank safai) | ✅ v2.7.3 | qplan.py |
| 21 | Owner ki reel ke hisaab se video sudhaar (vikalp pehle second se, hook line, chhota end, label) | ✅ v2.7.3 | design/answers/render |
| 22 | Lambi video galti (saada render dobara) + searchable hub title/thumbnail/tags | ✅ v2.7.4 | pipeline, hubvideo.SEO |
| 23 | Sawal zindagi bhar ek hi baar (sab channel) | ✅ v2.7.4 | pipeline.q_lifetime |
| 24 | docs/PLAYBOOK.md (doosre AI ke liye ranneeti) | ✅ v2.7.4 | docs |
| 25 | Views ke hisaab se look/rang/layout/andaaz ka apne aap chunav (naya bhi aazmaya jaaye) | ✅ v2.7.5 | learn.choose |
| 26 | 2 naye card layout (neon4, bar) owner ki photo se; namoona -> rotate | ✅ v2.7.5 | design.LAYOUTS |
| 27 | Light (5 SEC TEST) + comic (TEAM A vs B) card; layout purana bug theek | ✅ v2.7.6 | design |
| 28 | V3 50-50 (sahi kabhi nahi) | ✅ v2.7.6 | answers/design |
| 29 | Asli % engine (anonymous ginti, 30+) + tap-karke-socho + score card | ✅ v2.8.0 + W10 | votes.py, answers |
| 30 | Jawab zindagi bhar (register + /jawab khoj) | ✅ v2.8.0 | answers.archive |
| 31 | Viral photo jaisi paheli (khaali ank, jaadui vargh, 4 ank = N, +4+6+8 series) | ✅ v2.8.0 | puzzles |
| 32 | 30 din poori chat GitHub par (password/token chhupa) | ✅ v2.8.0 | updater |
| 33 | Sawal-type views ke hisaab se hafte-war (sirf default plan) | ✅ v2.8.1 | qplan.weekly_adapt |
| 34 | Tyohaar post din mein ek; purani scan ginti | ✅ v2.8.1 | calendar_in, watchdog |
| 35 | Karaoke subtitle (V4) | ✅ v2.9.0 | karaoke.py |
| 36 | Tyohaar ke din reel ka sawal usi vishay par | ✅ v2.9.0 | pipeline scheduler |
| 37 | Tyohaar 2+ website se pakka + tithi samay | ✅ v2.8.2 | calendar_in |
| 38 | Web Stories (har brand hafte mein 1) | ✅ v2.9.1 | webstory.py |
| 39 | A/B thumbnail (lambi video, analytics login ke baad khud) | ✅ v2.9.1 | abtest.py |
| 40 | Roz 1 website-tool pin (Pinterest) | ✅ v2.9.1 | toolpin.py |
| 41 | Comment se hafte ka idea (A6) | ✅ v2.9.1 | ideas.py |
| 15 | 24 card-model look (owner ki photo: 99% Fail neon -> bina nakli %, 3 SEC TEST light, Team A vs B comic, VS, grid, timer bar) + 'Look gallery' next-next preview + default/rotate + naye look khud banana | ⏳ agla | design.py, studio |
| 16 | Owner ki badi video (20 MB se badi) bot tak: link (YouTube unlisted/Drive) se ya local Bot API (2 GB) | ⏳ | tg.py / naya |
| 17 | 'Ek baar login, phir kabhi nahi': har token ki umr + khud-naya (Threads 60 din, Pinterest refresh) - ops token watcher ki jaanch | ⏳ | ops.py |

## Owner ki 5 Nov wali Word file (SabHisaab_Jawab_Video_Final_Plan) - har point ka haal
| Point | Haal |
|---|---|
| B1 /jawab: dabba (code+channel+tarikh), khoj, channel button, #cCODE, streak, WhatsApp share | ✅ v2.6.0-2.6.3 |
| B1 tap-to-guess (vikalp ke saath) + 'Seedha jawab dekhein' | ⏳ (vikalp answer_key mein jodne honge) |
| B1 Telegram patti 60% scroll par + GA4 events (pick/peek/search/share/engaged) | ⏳ |
| B1 har 6 ghante coverage check | ✅ pehle se (coverage_check) |
| P0-2 privacy: streak browser mein | ✅ W8 |
| B2/P0-3 video V1 V2 V3 V6 V7 V8 V10 | ⏳ (VM render test) |
| P1-1 Telegram quiz poll (limit ke andar) | ✅ pehle se ('jawab poll chalu' - owner ki pushti) |
| P1-2 A1 asli % engine + A2 label | ⏳ |
| P1-3 V4 karaoke, V5 background, V9 hook variety | V9 ✅ (hooks.py) / V4 V5 ⏳ |
| P1-4 Web Stories + Pinterest pins | ⏳ |
| B3 mini-tool link jawab ke neeche | ✅ ('Isse juda free tools') |
| B3 finance/kanoon jawab par Source + Reviewed on | ⏳ |
| B3 topic hub pages, weekly mock test, verified variants | ⏳ (AdSense ke baad, quality score ke saath) |
| A3 retention learner | ⏳ owner: '/analytics' login |
| A4 jawab accuracy gate | ✅ pehle se (qbank do-dimaag jaanch) |
| A5 purani reel revival | ⏳ |
| A6 comment -> FAQ/idea (naam nahi) | ⏳ |
| A7 flash-safety | ✅ design mein flash nahi (V-items ke saath test) |
| A9 anti-templated | ✅ hooks rotate / ⏳ captions per platform |
| A10 exam/tyohaar calendar | ⏳ |
| A11 Instagram private reply | ⏳ 28 Nov ke baad + privacy pehle (abhi band) |
| A12 weekly Telegram report | ✅ pehle se (Ravivaar 21:00) |
| PART C 'nahi karna' list | ✅ code mein palan (nakli %, jhootha daava, auto-next nahi) |

## v2.9.1 ke baad - SAACH: jo baaki hai aur kyun
| Kaam | Kyun nahi kiya / kya chahiye |
|---|---|
| Retention-drop par zoom/awaaz, har platform ka best samay | owner ka '/analytics' login + 2-3 hafte ka data; learn.choose ghanta pehle se seekhta hai |
| Telegram opt-in quiz bot | owner BotFather se naya bot token de (ek baar) |
| Web push notification | owner OneSignal (free) account banaye; privacy page pehle |
| Top 5 tools English | har page insaan/Claude se likhwa kar (scaled AI content nahi) - alag kaam |
| Google Fonts self-host | 270 page ka head; fayda chhota, khatra bada - baad mein ek-ek |
| Purani reel 'revival' | YouTube par dobara daalna = reused content khatra; sirf Telegram throwback (baad mein) |
| 24 card-model ke baaki (detective, impostor, memory...) | 6 card ban chuke (list/grid/big3d/neon4/bar/light3/versus); baaki naye sawal-type maangte hain |

## AGLI FINAL ZIP ke liye NOTE (owner 10 Nov - abhi likha, final ZIP mein ek saath banana)
| # | Kaam | Note |
|---|---|---|
| N1 | Video publish hote hi /jawab par jawab STRICTLY (kuch minute mein) | upload ke turant baad publish_site + 15 min mein coverage_check; na mile to dobara + alert; YouTube scheduled (publish_at) ho to usi samay |
| N2 | Privacy / Terms / About par 'Hamare official channel' | YouTube x4, Facebook, Instagram, Threads, Pinterest, Telegram, WhatsApp - naam + link; 'sirf yahi asli, baaki nakli'; video ke jawab site par kyun |
| N3 | OneSignal web push (owner App ID + REST key dega) | opt-in button (shaant, popup nahi), roz max 1 (naya sawal), privacy page mein ullekh, service worker site par |
| N4 | Telegram quiz bot (owner BotFather token dega) | /start par roz ka sawal, A/B/C/D button, score; koi phone/naam save nahi |
| N5 | '/analytics' login ke baad: retention-drop par zoom/sfx + best samay | learn mein retention data; owner ne login kar diya to khud |
| N6 | PENDING safai: '/analytics login' (4 juda 10 Nov) par checker; 'hub lambi video' (ab hubvideo khud) hatao; Claude ke ho chuke (V3, % engine, karaoke, Web Stories, weekly quiz, YPP analytics) itihaas mein | final ZIP |

## PROGRESS v2.9.2 (sandbox, 10 Nov 10:30) - final ZIP ke liye kaam chal raha
- ✅ text.fix: Hindi mein ZWJ/ZWNJ/ZWSP (matra se pehle) hata kar NFC - 'परछ◌ाई' jaisa dotted gola nahi
- ✅ rang/layout: pakke 3 se kam hon to SAARE palette/layout apne aap rotate (pehle palettes_ok khaali = har reel ek rang)
- ✅ YouTube: hamare top comment par aaye REPLIES bhi padhe + jawab (pehle sirf naye thread); reply parent = thread
- ✅ /jawab tez: 419KB -> 76KB (naye 40 dabbe+table, baaki register se; #cCODE na mile to register se khud)
- ✅ 'welcome pin': bot channel mein saare official link post + PIN
- ✅ N1 audit.final_authority (7 jaanch) + upload ke turant publish_site (deploy 1 min) + 15 min baad coverage + dobara
- ✅ N2 official channel (bot ZIP ke andar sitepatch); N3 OneSignal (push.py); N4 quiz bot (quizbot.py); N6 list safai; tests; docs
- ✅ v2.9.2 FINAL ZIP

## PROGRESS v2.9.4 (sandbox, owner ka 10 Nov 16:xx sandesh - lambi list)
- ✅ hooks: naam-jodi 18 (10 reel tak dohraav nahi), 4 naye challenge andaaz (dobara/chunauti/tez/dost), hook_mode phir rotate (owner ne 4:08 par bahas pakka kiya tha - ab variety)
- ✅ light/comic card par AI photo nahi (versus kaala dikh raha tha)
- ✅ /jawab KEEP=8 (owner 10 baar); coverage_check KEEP tak
- ✅ namoona 'Agla': har baar naya sawal-type + naya rang/layout (pehle seed same tha)
- ✅ docs/OWNER_RULES.md (20 pakke niyam)
- ✅ 'exam' card (Ranker jaisa safed/rangin glow, bold, laal gol vikalp) + 6 diagram paheli (ratio, Y, dibba, gola, cross, BODMAS) - 1200 bana kar jaanche, frame dekhe; qplan mein; diagram = exam layout
- ✅ comment padhna comment-login se (asli wajah); bot seekhe (Somvaar, pushti); FB Pahadi steps; Bing (sirf na-index pehle) + Google URL Inspection pehle se (website daily.py, '📑 Indexing')
- ✅ v2.9.4 ZIP

## v2.9.5 (11 Nov) - ✅ quiz bot relay+haal, ✅ Pahadi comment-login recovery, ✅ platform caption, ✅ purane code register, ✅ PageSpeed hafta-war,
   ✅ pending safai. Owner: 'yt comment login pahadi'; quiz bot /start; (agar PageSpeed key bot mein nahi) 'psi key <key>'.

## PROGRESS v2.9.8 (sandbox, 11 Nov - VM audit + Gemini PDF + chat)
- ✅ brain SKIP + transcribe/imagen/veo/gemma; ✅ IG re-encode GOP 60 + 4.5M; ✅ tg.say lamba sandesh kai hisson mein (kaata nahi)
- ✅ vmaudit: restart sirf ASLI crash par 🟡; ✅ log ek line; ✅ QC/preview POSTED mein bhi file dhoondhe
- ✅ 'comment login per jud gaye kya' seedha jawab; ✅ traffic: pichhla hafta tulna + roz ausat
- ⏳ Web Story 'invalid' (owner se GSC AMP detail screenshot), SQLite/bot split NAHI (jokhim > fayda), CUDA venv: owner pushti wala command
