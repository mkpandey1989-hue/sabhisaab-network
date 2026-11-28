# MASTER - Sab Hisaab ka POORA haal ek jagah (koi bhi AI / developer SABSE PEHLE ye padhe)

> 🔖 **AAKHRI AUDIT: 25 Nov 2026 (v3.9.5, Claude)** — SABSE PEHLE `docs/LAST_AUDIT.md` padho (kya kami mili, kya theek kiya, kya baaki, kya KABHI NAHI). Poora saboot: `docs/AUDIT_25NOV2026.md`. Naya audit karo to isi stamp ki tareekh + LAST_AUDIT.md badlo.

Aakhri update: 22 Nov 2026 (Claude, bot v3.4.39). Kuch badle to isi file ko update karo, purana sach mitao mat - "pehle/ab" likho.
Iske baad: `docs/PENDING.md` (bot roz likhta hai) → `docs/AI_START.md` → `docs/ROADMAP.md` (neeche se naye section).

## 0. Teen line mein
- Owner: **Manoj Kumar Pandey** ("Manoj bhai"), Hinglish, phone/Telegram se kaam. Har step poore link + bhare hue text ke saath.
  "Faltu mat chhedna" - jo chal raha hai use bina wajah mat badlo. Sach batao; nakli aankda/% kabhi nahi.
- Lakshya: sabhisaab.com par traffic + log ruke (dwell) → AdSense kamai. 4 video brand + bot traffic laate hain.
- Bot: Oracle VM `nifty-a1`, systemd `sabhinet` (repo `sabhisaab-network`). Website: Cloudflare Pages (repo `sabhisaab`).

## 1. Saare account (kahan, kis naam se, kaun chalata hai)
| Jagah | Pata / ID | Kaun post karta hai | Haal (17 Nov) |
|---|---|---|---|
| Website | https://sabhisaab.com (Cloudflare Pages + DNS) | bot deploy (VM se seedha) | ~305 URL sitemap mein |
| Email | contact@sabhisaab.com (profiles par) ; owner Gmail alag | - | - |
| GitHub | mkpandey1989-hue/sabhisaab-network (public, bot) ; mkpandey1989-hue/sabhisaab (public, website copy) ; **mkpandey1989-hue/vm-bots (PRIVATE - trading bot, chart, chowkidar, systemd, cron)** ; yt-auto (private, purana) | sabhinet/website: bot khud push ; vm-bots: VM roz 02:40 (`~/vm_backup.py`) | koi secret repo mein NAHI (code mein `***`) |
| Google Search Console | sc-domain:sabhisaab.com (service account bot ke paas) | bot sitemap bhejta, index jaanchta | Google 288/297 index (16 Nov) |
| Google Analytics 4 | G-QX5MWV42TR | - | owner-mode + India mein analytics default ON (consent region) |
| Google AdSense | pub-1074878035420336 | - | 16 Nov apply, **review chal raha** - ad code site par NAHI |
| Bing Webmaster + IndexNow | key bot ke paas | bot roz max 50 URL, sitemap auto-resubmit | Bing index ~26 (dheere) |
| YouTube (4) | @sunonatak, @sabhisaabmoney, @labhlodeals, @pahadihisaab (Google Cloud project yt-auto-512210, OAuth In production) | bot | roz 2-2 Shorts |
| Facebook Page (4) + Instagram (4) | facebook.com/<handle>, instagram.com/<handle> (wahi 4 handle) ; Meta app 1818304339486733 (Live), system user token | bot | IG caption mein click-link nahi, sirf sabhisaab.com/jawab ki saadi line |
| Threads (4) | threads.net/@<handle> | bot (token 60 din, auto-refresh) | chal raha |
| Pinterest | pinterest.com/sabhisaabcom (app 1630338, Standard access) | bot | /jawab par roz max 2 pin (spam-suraksha) - '⏸' galti nahi |
| Telegram | t.me/sabhisaab (channel) ; bot sabhinet owner chat | bot | chal raha |
| WhatsApp channel | https://whatsapp.com/channel/0029Vb8rHA5EFeXmREHFHk3n | **owner forward** (API nahi) | bot taiyaar text deta hai |
| LinkedIn Page | https://www.linkedin.com/company/144149065/ ("Sab Hisaab") | bot → Make.com webhook (eu1, scenario "Integration Webhooks, LinkedIn") → Page | roz 09:15 1 post; Make scenario galti par khud BAND hota hai (16 Nov hua tha) - band dikhe to Make mein ON |
| Dailymotion | https://www.dailymotion.com/sabhisaab (Partner, 17 Nov) | bot (Private API key) | 17 Nov 09:51 nayi key se **juda** (@sabhisaab), roz max 2 video |
| Quora | profile "Manoj Kumar Pandey" (bio: Founder sabhisaab.com · 2010 se hisaab-kitaab) + Space "Sab Hisaab - Paisa, Pahad aur Paheli" | **owner haath se** (API nahi) | 17 Nov se: 4 jawab + 1 sawal; 20 Nov se link wale jawab |
| UptimeRobot | owner Gmail par hafte ki report | - | site up |
| Doosra "VM" Telegram bot | Gemini se bana alag bot (TradingBot/VM sahayak) - code is repo mein NAHI | - | uska "24-ghante channel tracker" Posts=0 dikhata hai - **galat hai**, sabhinet ka '📊 Aaj ka haal' / 'report table' maano |

Brand: Suno Natak (sunonatak), Sab Hisaab Money (money), Labh Lo Deals (deals), Pahadi Hisaab (pahadi). Handle sab jagah same.

## 2. Roz kya, kab, kahan jaata hai (IST)
- Video (har brand roz 2, manzoori ke baad / jawab na mile to Thumb 1 se): pahadi 09:30, 18:00 | money 12:30, 20:30 | deals 16:00, 21:30 |
  sunonatak 13:30, 19:30. Har video → YouTube + FB + IG + Threads + Pinterest (seema ke andar) + Telegram + story + /jawab par jawab +
  **Dailymotion (roz max 2, key judne ke baad)**. WhatsApp: owner forward.
- 05:40 auto-doctor (khud jaanch + surakshit sudhaar) | 06:40 Uttarakhand queue (max 10 naye page/din, audit ke baad) |
  08:00 website report | 09:15 LinkedIn | 11:30 Google index jaanch | **11:40 GOOGLE INDEXING suchi (poore URL, tap = copy)** |
  18:45 UK page social | 19:15 share kit (WhatsApp status / FB group / Quora ka taiyaar text) | 21:50 brand x platform table |
  Ravivaar: site scan, link-chowkidar, hafte ki report.
  **v3.4.24:** 10:30 mauka calendar (juda calculator Telegram + FB) | sawal wali reel ke 3 ghante baad FB page link-card (brand max 2/din) |
  Ravivaar 20:40 funnel (platform-wise kitne ruke) | 20 Dec saal jaanch. Quiz bot inline share (BotFather /setinline ke baad). Haal: 'naye kaam haal'.
  Faisla (18 Nov, owner): har sawal ka alag website page NAHI banega (Google ka khatra) - sirf bahar se log + purane page behtar.
- Har link par UTM: utm_source = youtube/facebook/threads/pinterest/telegram/whatsapp/whatsapp_status/facebook_group/linkedin/
  quora/dailymotion/push (+ medium linkpost/mauka/inline v3.4.24). Report (`report table 7 din`) inhi naam se alag line deta hai. Instagram par UTM/click-link nahi (niyam).

## 3. Owner ke haath ke kaam (sach - bot ye nahi kar sakta)
1. ~~Dailymotion nayi key~~ - 17 Nov ho gaya (juda).
1b. **VM backup ek baar chalao** (2 min): `curl -sL https://raw.githubusercontent.com/mkpandey1989-hue/sabhisaab-network/claude/v348/tools/vm_backup.py -o vm_backup.py && python3 vm_backup.py --install`
   → "✅ GitHub par gaya" aaye to bas. Uske baad roz raat 02:40 apne aap.
2. **Google indexing** (roz 5 min): 11:40 ki EK hi suchi (queue ke naye page bhi isi mein; subah ka queue sandesh link nahi deta; kaam na ho to 'aaj koi kaam nahi' aata hai) → link tap (copy) → search.google.com/search-console → "Inspect any URL" → REQUEST
   INDEXING → bot mein `indexing ho gaya`. Google ka Indexing API sirf job/live-video ke liye hai - bot khud nahi kar sakta.
3. **Quora** (roz 15 min): 2-3 jawab; screenshot Claude ko. 20 Nov se purane 4 jawab mein link (PENDING mein poore link).
   Quora Space ka link Claude ko (website par jodna baaki).
4. **WhatsApp channel**: bot ka taiyaar text forward.
5. **AdSense**: approval mail ka intezaar (2-4 hafte). Mail aate hi Claude ko - privacy ki line + ad jagah (quiz vikalp ke paas kabhi
   nahi, apne ad par kabhi click nahi).
6. Marzi: Reddit r/Uttarakhand hafte mein 1-2 (haath se), Telegram directory (tgstat), FB group "Pahadi Hisaab Parivar".
Poori list + tareekh: `docs/PENDING.md` (bot roz likhta hai; v3.4.9 ne purane ho-chuke AdSense/owner-mode/Pinterest kaam hata diye).

## 4. Itihaas (kya kab hua - short)
- Oct 2026: 4 brand ke YouTube/FB/IG/Threads/Pinterest/Telegram/WhatsApp bane; bot v1-v2.
- 1-13 Nov: website 280+ tool page, /jawab, Bing/IndexNow, Uttarakhand project (13 zile + hub, 264 page queue), Fable audit (v3.1).
- 14-16 Nov: UK queue live hona shuru (roz 8-10), LinkedIn (Make), AdSense apply, tracking fix (consent region), owner link,
  auto-doctor, scoreboard, share kit, Quora/WhatsApp/FB group kit (v3.3.x - v3.4.6).
- 17 Nov: v3.4.7 indexing suchi + ek jaisi ginti + site sudhaar; v3.4.8 Dailymotion + LinkedIn/Dailymotion website/privacy par;
  v3.4.9 Dailymotion secret pehchaan + chat mein secret chhupa + ek hi indexing suchi (website ki 09:05 'PENDING KAAM' band).
- 17 Nov VM (owner ne chalaye, sab OK): tools/autostart_fix.sh (5 service boot par chalu + kabhi haar na maane), tools/chowkidar_social_fix.py
  (chowkidar post ginti sabhinet se + Dhan token fallback), tools/chart_alert_fix.py (nifty-chart MemoryMax 500M, memory message 475+ MB
  din mein 1 baar, raat 03:00 300+ MB par chart khud restart, subah 8 baje report sirf gadbad par), journal 200M + apt clean.
- 18 Nov: v3.4.24 reach.py (FB link-card, mauka calendar, funnel, saal jaanch) + quiz bot inline share. 11 kaam pehle se bane mile.
- 18 Nov: v3.4.25 'sawal wali post' / 'ek post do' = turant copy-layak reel ka sawal (kabhi dohra nahi), 'restart' asli, chat ki 5 galti theek.
  Quiz bot = @Sabhisaab_bot (Telegram getMe) - inline BotFather mein isi par.
- 18 Nov shaam: v3.4.26 '<brand> <platform> post' / 'sab platform post' (Insta story photo bhi), 'pin kit', Google index jaanch
  restart-proof (16 Nov se atki thi), traffic table par din. AdSense: review 16 Nov 16:49 se ('Getting ready'), 18 Nov mail.
- 19 Nov: v3.4.27 FB group post 3 line (See more se pehle link) + pehla-comment text, platform-wise 'diya hua' sawal,
  'facebook post' = group, traffic report mein reel ke poore link.
- 19 Nov: v3.4.28-29 index-check retry, toote job 'kharab', 'sab features' (39 feature ka asli haal).
- 19 Nov 10:15: v3.4.30 BUG: bot asli quiz-jawab comment ('Khet ❤️') ko AI ke 'spam' andaze par Instagram mein chhupa raha tha + seen-list
  beqram kat'ti thi. Ab quiz-jawab kabhi nahi chhupta, spam sirf link/promo par, Unhide kiya to dobara nahi, har chhupane par owner ko sandesh.
- 19 Nov 10:30: v3.4.31 chhupe quiz-jawab har 3 ghante apne aap WAPAS ('comment wapas'), FB/Threads/khabar ke POORE link,
  indexing suchi par '✅ Maine Request Indexing kar di' button (pehle owner ka likha 'ho gaya' bot samajhta nahi tha -> roz wahi page).
- 19 Nov 10:45: v3.4.32 owner ne 'mendhak ne kudne ka faisla kiya' sawal par naraazgi -> bachkani/internet trick-paheli band
  (Gemini prompt adult + regex + Gemini critic + video audit). Unhide jaanch ka nateeja ab hamesha sandesh mein.
- 19 Nov 10:55: v3.4.33 'Mat daalo' -> bot poochhta 'doosri banau?'; 10 min jawab nahi to usi slot ki nayi video khud.
- 22 Nov: v3.4.39 /jawab par Suno Natak ka channel-button gayab: table mein sirf aakhri KEEP=8 jawab hote hain aur buttons unhi 8 se bante the (jis channel ka jawab 8 mein na ho uska button nahi). Ab jawab_table mein BRANDS ke chaaron channel ke button hamesha; jis channel ka jawab table mein nahi uska button window.jwLookB se purane register (jawab-archive-*.json, b = channel ka naam) se jawab dikhata hai (na mile to 'jaldi aayenge'). Install ke baad bot.py ek baar (state jawab_btn3439) /jawab dobara banata hai. Table/KEEP/anchor/audit niyam waise hi.
- 22 Nov: v3.4.38 v3.4.37 ne #5139 (Suno Natak, 'FIRE = GJSF') ko page se BAHAR kar diya tha -> Suno Natak ka channel-button aur uske jawab /jawab se gayab. Audit ka 'mixed script' niyam [Devanagari][A-Za-z]|[A-Za-z][Devanagari] hai aur danda '।' bhi Devanagari mein gina jata hai: 'XBUFS।' = error. Ab: Latin ke turant baad danda -> '.', danda ke turant baad Latin -> khaali jagah (jawab bahar nahi). Sirf asli tuta shabd ('पहाadi', doosri lipi) bahar. Safe roop mein baaki chipke bhi khaali jagah se alag.\n- 22 Nov: v3.4.37 /jawab ka ASLI karan: audit 'jawab.html' par 2 error deta tha - (1) 'paragraph dobara likha': 'Isi tarah ke N aur' block mein sawal 55 akshar par kat'te the, to do jawab ka paragraph ek jaisa ban jata tha; (2) 'mixed script': kisi jawab ke text mein Hindi+English chipka / doosri lipi. Ek jawab ki galti se poora page rukta tha. Ab: har block mein apna code (paragraph alag); kharab text wala jawab SIRF page se bahar (Telegram/record mein rehta hai, state jawab_skip, coverage_check use gayab nahi ginta); audit fir bhi fail ho to ek baar safe roop (strict jaanch, 'isi tarah ke' block nahi).\n- 22 Nov: v3.4.36 v3.4.35 ke baad '_jw: index.lock File exists' aaya: (1) deploy ko alag thread mein chalana git ko jawab-publish se takra raha tha -> wapas usi WORK line mein; (2) website._git ab purana (90 s+) index.lock, jab koi git chal nahi raha, khud hata deta hai aur chalte lock par 4 s ruk kar 5 baar dobara koshish karta hai.\n- 22 Nov: v3.4.35 /jawab ATKA tha: jawab file VM par lagti thi par Cloudflare deploy chhut/fail hota to koi dobara deploy nahi lagata tha ('ZIP pehle se lagi hui' ko success maan ke deploy_due set hi nahi hota tha). Ab: site_undeployed flag + tick_auto dobara deploy (10/20..60 min), deploy_due sirf jaldi hota hai (15 min wala ZIP 1-min deploy ko aage nahi dhakelta), deploy alag thread + ek-waqt-ek-lock, coverage miss par force-publish deploy bhi lagata hai, install ke baad atke saare jawab ek baar dobara publish.
- 19 Nov 19:30: v3.4.34 CHAT.md GitHub par wapas (1 MB seema), indexing PARTIAL=index + kul/ho gaye/baaki + poore link,
  GA4 traffic chart + FB Group alag, button galat spelling/awaaz, ghumaudar sawal, views se sawal-type band (pushti/24h),
  sirf jawab-live sawal post, MASTER AUDIT (owner ke niyam roz 21:55). Hukum: 'master audit', 'niyam', 'traffic',
  '<shabd> wale sawal band karo', 'band vishay', 'sawal jaanch abhi'.
- 19 Nov audit: Google 305/315 page index par impression ~60/hafta (ranking nahi); Bing ~40 index, 217 kabhi crawl nahi; GSC shabd
  sirf 'keywords' likhne par aate (apne aap kabhi nahi). Sujhaav (owner ki haan baaki): UK queue 8/din -> 2/hafta, Somvaar keyword
  sandesh, EMI/MB table. Bing ticket REQ00378387 (29 Oct band) par follow-up draft Gmail mein - feedback link se bhejna.
- Aage: ~mid Dec UK queue poori → Jan 2027 Search Console data dekh kar Himachal ke 20-30 page (sirf jo UK mein chala) ya UK sudhaar.

## 5. Privacy policy (https://sabhisaab.com/privacy, aakhri update 17 Nov 2026) - code wahi kare jo ye kehti hai
- Website: GA4 (India + baaki desh mein ginti default ON, EEA/UK/Swiss mein sahmati ke baad), ad cookie band; AdSense ad abhi nahi.
- Platform: YouTube/Meta/Threads/Pinterest official API; LinkedIn (Make.com, sirf post); Dailymotion (sirf upload, site par koi player/
  cookie nahi); Telegram/WhatsApp ek-tarfa channel. Commenter data max 30 din. AI awaaz ka label har video par.
- Naya platform/cookie/embed jodo to **pehle privacy page** (webfix jaisa, audit gate se, tareekh + sitemap lastmod).

## 6. KABHI MAT KARNA (in sab par owner pehle naraz ho chuka ya niyam ke khilaaf)
- Indexing API / nakli lastmod / ek din mein 10 se zyada naye page / ek-ek number ke alag page (scaled content).
- Bot khud content likhe (Google spam) - sudhaar Claude karta hai, bot sirf audit gate se lagata hai.
- Token/secret chat, GitHub ya docs mein. (17 Nov galti: Dailymotion secret pehchana nahi gaya → CHAT.md mein chhapa. Ab
  `updater._mask` nishaan-wale secret bhi chhupata hai; naya secret-intake banao to pehle `clean_secret`/`_mask` test karo.)
- Instagram par "@sabhisaab" ya click/UTM link; quiz vikalp ke paas ad; apne ad par click.
- Trading services (nifty-live, delta-live, nifty-chart) chhedna; `data/` ya `secrets/` commit karna.
- Bulk cold WhatsApp/DM, Reddit/Quora/Facebook group par bot se auto-post, personal profile scraping.
- Local audit: `config.json` ka `site_dir` **patch wali copy** par karo (17 Nov galti: asli copy jaanchi, lamba title VM par ruka).

## 7. Kaam dene ka tareeka (AI ke liye)
- **NIYAM (17 Nov, owner): sab kuch ki TAAZA copy hamesha GitHub par** - owner ko kisi AI ko file bhejni na pade:
  | Kya | Kahan | Kaun update karta |
  |---|---|---|
  | sabhinet bot code + docs (MASTER, PENDING, ROADMAP, STATUS, CHAT...) | sabhisaab-network (public) | bot khud (badlav ke 10 min mein) + AI apni branch push |
  | website | sabhisaab (public) | bot deploy ke saath |
  | trading bot, Nifty chart, chowkidar, master_guard/vm_health/ntfy_monitor, systemd unit, crontab, roadmap docx (text) | **vm-bots (PRIVATE)** | VM roz 02:40 (`vm_backup.py`, secrets `***`) |
  Har AI: kaam ke baad MASTER.md + ROADMAP + (owner-kaam ho to) tasks.py SEED update karke **push** kare. VM par badlav sirf
  `tools/` ki script (backup + py_compile + idempotent) se; agli raat vm-bots khud taaza. Secret (token/key/password/topic/chat id)
  kabhi kisi repo mein nahi - na public, na private.
- Bot ZIP: `git ls-files` (photos/*.webp, data/, secrets/, pycache, .gitignore bina) → VERSION badhao → ROADMAP mein `## vX.Y.Z`
  → `tests/smoke.py` PASS → owner bot ko ZIP bhejta hai. Naye owner-kaam `app/tasks.py` SEED mein (auto checker ho to do).
- Website badlaav: `app/webfix.py` jaisa idempotent patch + `website._apply_zip` (audit gate) ya site ZIP.
- Har report mein ek hi ginti: `website.ga_range(N)` + GA4 asli total; source naam `scoreboard.group_source`.

## 8. Teen bot - kaun kya bataye (takraav nahi)
| Bot | Kaam (sirf ye) | Na kare |
|---|---|---|
| **sabhinet** (@Sabhisaab_bot, @Manoj_yt_sahayak_bot - repo sabhisaab-network) | video, saare channel, website, indexing, GA4/GSC/Bing, Quora/LinkedIn/Dailymotion, 'vm audit' (maangne par) | trading chhedna |
| **chowkidar** (@manoj_vm_chowkidar_bot, ~/chowkidar, cron: 09:05 subah, 21:00 report, 03:15 daily, Sat weekly, 1 tareekh monthly, 09:00 bill) | VM (RAM/disk/CPU/kernel/update), suraksha (SSH/fail2ban), trading services up/down, bill, **sabhinet service sirf chal raha/ruka** | channel ki post ginti / website / token - ye sabhinet ka hai (iska "6-channel tracker" Posts=0 galat dikhata tha) |
| **master_guard / vm_health / ntfy_monitor** (cron) | chupchap jaanch + sirf galti par alert | roz ka "sab theek" sandesh (dohra shor) |
| **nifty-chart** (~/nifty_chart, ntfy) | chart + shaam 20:00 health report, chart band ho to watchdog restart | memory ka har ghante sandesh (17 Nov band) - trading logic kabhi na chhedo |
