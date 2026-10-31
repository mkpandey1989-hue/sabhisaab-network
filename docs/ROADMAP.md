SAB HISAAB — MASTER ROADMAP v14.1 (saaf version)

Tareekh: 29 October 2026 · Pichhla: Roadmap v13 / v13.1 · Owner: Manoj Kumar Pandey

v14 ek saaf, ek-jagah version hai. v1 se v13 ka jo hissa ab laagu nahi (purani chhoti VM, Cloudflare Worker bot, GitHub cron, 22-file ZIP, purana IP, laptop/cron wala tareeka) aur jo line baar-baar dohrayi gayi thi, wo hata di gayi. Har zaroori niyam, seekh aur galti ka sabak ek hi baar, sahi section mein rakha gaya hai.

# 0. v14 mein kya hataya, kya joda

| **Hataya (ab laagu nahi)** | **Kyun** |
| --- | --- |
| Purani VM ki baatein (Ubuntu 22.04 / Python 3.10 / 100 GB, ephemeral IP, "VM par site ka kuch nahi chalta") | Ab nifty-a1 2 OCPU / 12 GB / 200 GB, reserved IP; website ka saara kaam VM bot karta hai |
| Cloudflare Worker bot (@Sabhiisaab_bot), uske 27 command, worker/ folder | Band; saara kaam sabhinet bot mein |
| GitHub Actions cron (daily, watch, pending, health, notify, bot, ping) aur unke manual link | Bot ne band kiye; kaam VM par |
| "ZIP mein 22 se zyada file nahi", "do ZIP ek saath nahi", ginti ke liye GitHub par login | v2.0.0 mein seema khatam, ZIP line, ginti sync apne aap |
| Laptop setup, purana README ka "incoming folder + cron" tareeka | Sab Telegram + VM se |
| 130/153/183/185 jaisi purani ginti, purane batch ke ZIP naam (A1-A3, B1-B2, C1, W1, W1v2, W2, v1.7, v1.8) | Itihaas; abhi ki ginti section 3 mein |
| Dohrayi lines (KABHI MAT KARNA 6 baar, page spec 4 baar, audit list 4 baar, pending list 5 baar) | Ek baar, ek jagah |

| **Joda (v14)** | **Section** |
| --- | --- |
| 29 Oct poora audit: 7 pending URL ki asli wajah + fix | 8 |
| Bot v2.0.0 (seema khatam, seedha deploy, website gyaan/doctor, khud-upgrade, gyaan-bhandaar) | 5 |
| Privacy milan ki 2 nayi kami aur ilaaj | 6 |
| Traffic + monetization ka aage ka plan | 11 |

# 1. Ek panne mein system

- **Website** sabhisaab.com — Hinglish free calculators, Cloudflare Pages par static (project "sabhisaab"). Code ki copy: github.com/mkpandey1989-hue/sabhisaab.

- **4 brand channel** — Suno Natak, Sab Hisaab Money, Labh Lo Deals, Pahadi Hisaab: YouTube, Facebook, Instagram, Threads (+ Pinterest board). Saanjha: Telegram t.me/sabhisaab, WhatsApp channel "Sab Hisaab", Pinterest sabhisaabcom.

- **Ek hi bot (sabhinet, Telegram ****"****Youtube Bot****"****)** Oracle VM nifty-a1 par 24x7: video/reel banana, post, comment, tyohaar, report, aur website ka audit, deploy, indexing, traffic. Code ki copy: github.com/mkpandey1989-hue/sabhisaab-network (GitHub sirf padhne ke liye; roz docs/STATUS.md + docs/ESCALATE.md).

- **Lakshya:** zyada traffic website aur channel par, monetization (AdSense, YouTube YPP, FB), zero manual, poori tarah policy ke andar.

- **Kharcha:** Rs 0/mahina (sab free tier).

# 2. VM — nifty-a1 (sirf yahi VM)

| **Cheez** | **Vivaran** |
| --- | --- |
| Shape | Oracle VM.Standard.A1.Flex (ARM aarch64), Mumbai, Always Free |
| Size | 2 OCPU / 12 GB RAM / 200 GB boot (free seema poori; isse upar bill). Budget alert laga hai |
| OS | Ubuntu 26.04, timezone Asia/Kolkata, user ubuntu |
| IP | 140.245.8.212 — RESERVED (Meta app allowlist, Google API key, Dhan, Delta isi par) |
| Trading services | nifty-live (8001), delta-live (8002), nifty-chart (8003) — bot inhe kabhi nahi chhedta, trading ko pehla haq |
| Bot service | sabhinet (systemd, reels.slice max 6 GB, Nice=10, OOMScoreAdjust=500, Restart=always, selfcheck + rollback) |
| Bot folder | ~/sabhisaab-network: app/, data/ (state.json, diary.jsonl, learn.json, growth.json, site_index.json, photos/, clips/, stock/, site_repo/, backup/), secrets/ (700, file 600), venv/ (uv Python), logs/ |
| Bade VM ka faayda (v2.0) | 7 din ke backup, 30 din log, 10 din video stock, website ZIP par file-ginti ki seema nahi, VM par node/npm (calculator test + seedha Cloudflare deploy), vikalp: local Telegram Bot API server (2 GB tak file) |
| VM ke niyam | do-release-upgrade nahi; reserved IP hi rakhna; automatic backup policy nahi (manual boot volume backup, max 5); laptop ki purani file VM par upload nahi; naya package ARM support dekh kar |
| Oracle idle reclaim | Lambe samay kam CPU par Oracle instance wapas le sakta hai — trading + video se CPU chalta rehta hai; Oracle email dekhte rahein |

# 3. Website — abhi ki haalat (29 Oct 2026)

| **Hissa** | **Ginti** |
| --- | --- |
| Kul HTML page | 271 |
| Sitemap URL | 268 (links, 404, Google verification file sitemap mein nahi) |
| Tools (tools.js) | 188 — Nivesh 51, Loan/Tax 53, Rozana 29, Utility 23 (+3 Live = hub par 26), Sehat 11, Trading 9, Converter 9 |
| Guides / Lekh / Hub | 39 / 24 / 9 |
| Audit | ERROR 0 / WARNING 0; calculator test 183 page + 168 card pass |
| Google index | ~261 / 268; pending 7 (section 8) |
| Bing | Site Explorer mein ~8 indexed; bulk IndexNow (Aug–Oct, ~12,800 submission) ki wajah se bharosa ghata; support ko email kiya (28 Oct) |
| Backlink | Lagbhag zero — sabse badi kamzori |
| AdSense | Apply nahi; mid-Nov 2026 ke baad (3-4 hafte koi naya page nahi) |

## 3.1 URL aur file ke pakke niyam

- File nsc-calculator.html, par har jagah link /nsc-calculator (bina .html). Canonical/sitemap/link mein .html kabhi nahi (isi galti se pehle 2 hafte ka traffic gaya tha).

- _redirects file kabhi nahi (homepage toot gaya tha). Clean URL Cloudflare khud karta hai.

- Social link sirf do jagah: website mein install-app.js (har page ka footer) + links/about/contact, aur bot mein config.LINKS. Bot roz dono ka milan jaanchta hai.

## 3.2 Naya page — spec (ek hi baar)

- Template: nsc-calculator.html. Head: GA4 + consent → title (60 akshar tak, "| Sab Hisaab" milakar) → description 95-165 → robots (max-image-preview:large) → canonical → og(8) + twitter(4) → font (1 preload + 1 media=print + 1 noscript) → poora CSS inline → 3 JSON-LD (WebApplication/Article + FAQPage + BreadcrumbList).

- Body: header → crumb → H1 (sirf 1) → lekhak/update → share → intro → calculator → TOC → 5-6 unique H2 (har H2 ki id TOC mein) → kam se kam 1 table → 4-6 FAQ (schema hu-ba-hu) → "ye bhi dekhein" → disclaimer (finance: SEBI wala; sehat: medical; baaki: aam) → YMYL par sarkari source box → footer.

- Tool jodna: tools.js mein object + PAGES map; index.html ke cards dobara generate; hub mein card; 3-4 milte page se inbound link (3+); sitemap block (homepage pehle, baaki alphabetical); dateModified = sitemap lastmod. Ginti sync ab bot khud chalata hai (tools.js badle to).

- Content: 1000+ shabd, chhote vaakya, asli number ("lagbhag" agar anuman), har page par ek baat jo kahin aur na mile (Information Gain). Do page ka title/H1 ek jaisa kabhi nahi (cannibalization — section 8).

- Saal-par-saal badalne wale number (kist, dar, subsidy) page ki script mein ek constant mein. Calculator badle to chala kar dekhna (audit kaafi nahi — 13 calculator ek baar isi wajah se toote the).

## 3.3 Audit (scripts/audit.py) — kya pakadta hai

- HTML: html/body ek baar, tag balance, duplicate id, bina &amp; ka &. SEO: title/description lambai, H1, canonical = og:url, .html/?t= link nahi, 3+ inbound, dead link, duplicate title/description. Schema: FAQ = page, dates, author, aggregateRating kabhi nahi. Content: 1000+ shabd, mixed script nahi, misleading dava nahi. Perf/mobile: font, inputmode, img attributes. Policy: consent + GA4, YMYL disclaimer + source, rel=noopener, approval se pehle adsbygoogle nahi. Ginti, PAGES sync, sitemap kram/lastmod, JS syntax (node ho to).

- **29 Oct ko naye 2 check:** tool-naam wala link homepage (/) par; ek vaakya lagataar do baar.

- Audit pehredaar hai, sampadak nahi: galat formula, galat number, bekaar content nahi pakadta.

## 3.4 ZIP → live (bot v2.0.0)

- ZIP Telegram bot ko → "🌐 Haan, website par" (ya "website zip auto chalu" ke baad bina pooche).

- Bot: repo-raaste ke hisaab se file rakhta hai (site/, scripts/, .github/workflows/, README.md); tools.js badla to ginti sync; audit; ERROR ho to kuch nahi chadhta; ek din mein 10 se zyada NAYE page par rok.

- Saari ZIP ke baad "🚀 Website deploy": Cloudflare token ho to VM se seedha (audit → calculator test → wrangler → Google sitemap API → sirf badle URL IndexNow); warna GitHub deploy.yml.

- Deploy ke baad bot website gyaan taaza karta hai (naye/hate page, legal badlaav).

## 3.5 Indexing aur search engine ke niyam

- Google: sitemap har deploy par API se. Index status roz URL Inspection API se. Request Indexing ka API nahi — owner haath se, roz 1-2 (bot ek-tap link deta hai). Indexing API calculator par mana. Ek URL par 14 din se pehle dobara request nahi.

- Bing/IndexNow: sirf badle URL, din mein max 10, ek URL 14 din mein ek baar. "Sabhi URL ping", rotate mode, cron — kabhi nahi. Sitemap delete/resubmit nahi. Bharosa samay (3-6 hafte) aur bahar ke link se aata hai.

- Backlink: kharidna/auto banana mana (link scheme). Jaayaz raaste: apne channel/profile mein link, Pinterest pin, Threads link card, FB post, GitHub repo About, Quora/Reddit par asli sawaal ka jawab (hafte mein 3-4), local/agri portal ko email.

## 3.6 Jo number badalte rehte hain

| **Cheez** | **Abhi** | **Kahan / kab** |
| --- | --- | --- |
| PM Kisan aakhri kist | 23vi, 20 June 2026 | pm-kisan-calculator (LATEST) + tools.js; 24vi aate hi teeno jagah |
| PM Surya Ghar subsidy | Rs 30,000/kW (2 tak), Rs 18,000 (3rd), max Rs 78,000; vishesh rajya max Rs 85,800 | solar page; chowkidar 90 din |
| Small savings | PPF 7.1, NSC 7.7, SSY/SCSS 8.2 (Oct–Dec 2026) | Jan–Mar 2027 ki ghoshna end-Dec |
| Income-tax Act 2025 | 1 April 2026 se; purana 80C ab Section 123 | tax pages par 5-6 ke batch mein note (baaki) |
| Gahne par GST | 3% poore bill par; 5% sirf banwai | gold calc + guide |

# 4. Brand aur channel

| **Brand (code)** | **YouTube** | **Facebook** | **Instagram** | **Threads** | **Post** |
| --- | --- | --- | --- | --- | --- |
| Suno Natak (sunonatak) | youtube.com/@sunonatak | facebook.com/sunonatak | instagram.com/sunonatak | threads.net/@sunonatak | 19:30 |
| Sab Hisaab Money (money) | youtube.com/@sabhisaabmoney | facebook.com/sabhisaabmoney | instagram.com/sabhisaabmoney | threads.net/@sabhisaabmoney | 12:30 |
| Labh Lo Deals (deals) | youtube.com/@labhlodeals | facebook.com/labhlodeals | instagram.com/labhlodeals | threads.net/@labhlodeals | 16:00 |
| Pahadi Hisaab (pahadi) | youtube.com/@pahadihisaab | facebook.com/pahadihisaab | instagram.com/pahadihisaab | threads.net/@pahadihisaab | 09:30 |

| **Saanjha** | **Link** |
| --- | --- |
| Website / link-in-bio | https://sabhisaab.com/ · https://sabhisaab.com/links |
| WhatsApp channel | https://whatsapp.com/channel/0029Vb8rHA5EFeXmREHFHk3n (API nahi — bot post taiyaar, owner forward) |
| Telegram channel | https://t.me/sabhisaab (bot admin) |
| Pinterest | https://www.pinterest.com/sabhisaabcom/ (5 board; Trial → Standard baaki) |
| Policy | /privacy (#data-deletion), /terms, /disclaimer — Meta app, Google OAuth app, Pinterest app inhi par |
| Email | contact@sabhisaab.com |

- Meta: Business portfolio "Sabhisaab Network"; app "Sabhisaab Publisher" (Live, IP allowlist 140.245.8.212, Require App Secret ON); system user sabhisaab-bot; Threads API use case.

- Google: ek project yt-auto-512210 (In production), YouTube Data + Analytics API, API key VM IP par seemit; TV OAuth client; website service account gsc-bot (GSC Owner, GA4 543920755, G-QX5MWV42TR).

- Owner ka naam website ke author line par; video/reel/social par kabhi nahi.

# 5. Bot sabhinet v2.0.0

## 5.1 Kaam ka safar (video)

Topic (manzoor plan → owner ke topic → website page, pending-index page pehle → trend) → Gemini script (7 format rotation) → Kokoro hf_alpha awaaz → layered FFmpeg 1080x1920 (bina jhatke) → 3 thumbnail → 3-star audit (technical + kanoon/samaj + Google-search tathya) → manzoori ya autopilot (sirf roz ke schedule par) → YouTube (publishAt theek minute), Facebook, Instagram, Threads, Pinterest, Telegram + story → comment (gaali/spam hide, 7-45 min baad vinamra jawab, usi video ka page link) → seekh (views/retention/CTR).

## 5.2 Roz/hafte ka schedule (IST)

| **Samay** | **Kaam** |
| --- | --- |
| 00:02 / 00:10 | Tyohaar 7 din aage (Google search, 3 jaanch) / aaj ki story; muhurat par aur ek |
| 02:45 / 03:00 | Commenter data 30 din se purana saaf / backup (7 din) + Pinterest refresh |
| 04:00 | GitHub: code + docs/STATUS.md + docs/ESCALATE.md |
| 05:30 | Auto-heal (v2.0): node, site repo, Gemini, disk, baar-baar galti |
| 06:00 / 06:10 / 06:20 | Self-audit / website roz ki report / website gyaan + badlaav (v2.0) |
| har 30 min | Website chowkidar |
| 08:30 / 09:05 / 10:30 / 11:00 | Khabar / indexing ke 10 link / owner ke kaam ki jaanch / Pinterest Standard jaanch |
| Slot se 3 ghante pehle | Video taiyari; post 09:30, 12:30, 16:00, 19:30 |
| har 2 ghante | Comments |
| 21:30 / 22:00 / 23:00 | Din ki report / seekh / growth snapshot |
| Ravivaar | 01:30 lambi (hub) video; 02:30 khud-upgrade (v2.0); 18:30 related-video list; 19:00 company meeting; 20:00 hafte ki seekh + plan; 21:00 hafte ka hisaab |
| Somvaar 09:00 | Policy khabar + saare channel link ki jaanch |

## 5.3 v2.0.0 mein naya (29 Oct 2026)

- **Website ZIP ki seema khatam:** 22 file ki jagah 3000 (asli seema sirf Telegram ki 20 MB). Repo-raaste (site/, scripts/, .github/workflows/, README.md) surakshit. Har ZIP ki apni jagah (pehle doosri ZIP pehli ko mita deti thi). tools.js badle to ginti sync khud. Ek din mein 10 naye page ki suraksha.

- **Seedha VM se deploy:** "cf token" + "cf account" ke baad audit → calculator test → wrangler → Google sitemap → IndexNow, sab VM se. GitHub sirf copy.

- **GitHub safai:** "🧹 GitHub safai" → purana Worker code + band cron hatao; ya website repo ki history hata kar sirf taaza copy (double confirm). Bot repo pehle se sirf taaza copy rakhta hai.

- **Website gyaan + doctor (siteknow):** har page ka title/H1/shabd/lastmod/index status; naya/hata page → video topic mein apne aap; privacy/terms badle → alert, privacy ke "N din" ke hisaab se bot ki safai; website aur bot ke channel link ka farak; "website doctor" = pending page ki sambhavit wajah.

- **Khud-upgrade (upgrader):** Ravivaar packages (rollback ke saath), Meta Graph naya version (test pass ho tabhi), Gemini list; roz auto-heal; jo khud na ho → GitHub docs/ESCALATE.md (koi bhi AI padh kar fix ZIP de).

- **Dimaag (kb):** Gemini ko pakka gyaan (kb.md + live data); jawab ke liye data chahiye to bot khud dhoondhta hai (page, plan, diary, kaam, traffic, doctor, video, web) aur dobara sochta hai; 30 baat ki yaad.

- **Privacy:** commenter record platform-wise (jodkar track nahi), draft 30 din, backup bhi 30 din ke andar.

- **VM:** 7 backup, 30 din log, engine.log rotate, 10 din stock; vikalp sn-tgapi-setup (local Telegram API, 2 GB file).

## 5.4 Owner ke command (normal Hindi bhi)

- Buttons: 🎬 Abhi video, ⏳ Pending, 📊 Aaj ka haal, 🩺 Sab theek?, ⏸ Pause, ▶️ Resume, 📖 Poora menu (kal ka plan, khabar, duplicate jaanch, tyohaar, company meeting, analytics, mere kaam, website haal/indexing/deploy/audit/Bing/traffic/file, growth graph, aakhri 5 video, post hatao, privacy, 🩺 Website doctor, 🔄 Upgrade haal, 🧹 GitHub safai, 🧠 Website gyaan taaza).

- Likh kar: "money ka facebook band karo", "money roz 9 baje aur 7 baje", "pahadi par Uttarakhand GK bhi banao", "agle hafte ka plan banao", "kal ka plan", "aaj kya kiya", "website file <naam>", "data hatao <naam>", "ho gaya <shabd>", "aage se ... mat karna", "cf token <t>", "cf account <id>", "website zip auto chalu/band", "hub video <brand> <link>", /login, /analytics, /pinterest, /privacy, /logs, /safai, /panic, /version.

- Photo/mobile video bhejo (caption mein brand) → gallery → "🎬 Abhi in photo/video se reel". Test/owner video bina hukum kabhi post nahi.

## 5.5 Secrets (sirf VM par, naam)

bot.env (Telegram, Gemini, GitHub token), meta.json, threads.json, pinterest.json, yt_*.json, yt_analytics_client.json + ya_*.json, gsc_sa.json, site.env (Bing key, PSI key, Cloudflare token + account), tgapi.env (vikalp). Token kabhi chat/GitHub par nahi — owner seedha bot ko bhejta hai, bot message mita kar rakhta hai.

## 5.6 Bot kahan ruk sakta hai

- Token: YouTube login revoke → /login; Meta token/secret badla → naya bhejo; Threads 60 din (bot 20 din par refresh); Pinterest 30 din (refresh); GitHub token expiry se 15 din pehle yaad.

- Seema: YouTube 10,000 unit/din (~6 upload); Gemini free quota (model khud neeche); Instagram 100 post/24h.

- Owner ka haath wala kaam na hua to wahi feature ruka (🧾 Mere kaam mein dikhta hai).

# 6. Privacy policy aur asli kaam ka milan

| **Policy kehti hai** | **Bot/site asal mein** | **Jaanch** |
| --- | --- | --- |
| Calculator data browser se bahar nahi | Saare calculator browser mein; 3 Live tool sirf likha naam/code bhejte hain | audit |
| GA4 Consent Mode v2 | Default denied; "Sab cookies theek" par granted | har page |
| Commenter data max 30 din | Roz 02:45 safai (audience, diary, queue, draft, backup) | bot |
| Platform jodkar track nahi | v2.0: record "platform:naam" — pehle sirf naam se tha (kami theek) | bot |
| Data deletion 7 din | "data hatao <naam>" turant sab jagah se; owner email se pushti | owner + bot |
| IG "LINK" par ek DM | Meta App Review ke baad | bot |
| AI label | YouTube synthetic flag + FB is_ai_generated + description | audit |
| #ad sirf affiliate wali post | audit | bot |
| Policy page mein zaroori baatein | Roz subah live jaanch; badle to alert | bot |

- Aage: AdSense approval par Europe/UK ke liye Google-certified CMP (AdSense "Privacy & messaging") chalu karna zaroori — apna banner kaafi nahi. ads.txt approval ke baad. DPDP Rules 2025 ke charan dhyan mein.

# 7. Link kahan clickable hai

| **Jagah** | **Clickable?** | **Bot kya karta hai** |
| --- | --- | --- |
| YouTube Shorts description/comment | Nahi | Poora link likhta hai + Related video → hub video; channel Links (owner) |
| YouTube lambi video | Haan | Page link + UTM |
| Facebook post/reel | Haan | Pehli line page link |
| Instagram caption/comment | Nahi | Bio /links + "LINK" par DM (App Review ke baad) |
| Story | API se sticker nahi | Story par poora pata |
| Threads / Pinterest / Telegram | Haan | Link card / pin link / button |
| WhatsApp channel | Haan | Bot post taiyaar, owner forward |
| Video ke andar | Kabhi nahi | https://sabhisaab.com/ safe zone mein |

# 8. 29 Oct 2026 audit — 7 pending URL aur ilaaj

| **URL** | **GSC** | **Mili wajah** | **Ilaaj** |
| --- | --- | --- | --- |
| buy-vs-rent-guide | Crawled – not indexed | Calculator page jaisa hi H1/title ("Ghar Kharidein Ya Kiraye Par Rahein") — Google ek hi rakhta hai | Naya title/H1 "Kiraya vs Apna Ghar — Checklist", dateModified + lastmod 29 Oct, anchor badle (W3) |
| fire-number-calculator | Discovered | fire-guide ke dono "FIRE Calculator" link homepage par jaate the | Link theek (W3) |
| stopwatch-online, random-number-generator, number-system-converter | Discovered / Unknown | Disclaimer ka vaakya do baar; aam tool (Google ka apna widget); stopwatch ka "timer" link homepage | Vaakya theek, link hataya (W3); bot ab inhe Pinterest/Threads/FB par pehle le jaata hai |
| delivery-date-calculator | Discovered | Sehat (YMYL) — Google sakht | Samay + bahar ke link; source box pehle se |
| notice-period-buyout-calculator | Discovered | Kam inbound link (5) | Bot topic boost; agle content batch mein 2-3 link |

- Kul W3 sudhaar: 30 galat link (guides ke CTA homepage par jaate the — 17 guide), 21 page par dohra vaakya, 1 cannibalization; audit.py mein 2 naye check. 44 site file + audit.py + README. Audit 0/0, calculator test pass.

- 234/268 page ki lastmod ek hi din (19 Aug) — galat nahi; aage sirf asli badlaav par tareekh.

# 9. Abhi baaki (pending)

| **#** | **Kaam** | **Kaun** | **Band karne ka shabd** |
| --- | --- | --- | --- |
| 1 | sabhinet-v2.0.0-update.zip, phir W3-site-fix-29oct.zip, phir 🚀 Website deploy | Owner | auto-check |
| 2 | Cloudflare API token + Account ID bot ko (seedha deploy) | Owner | auto-check |
| 3 | GSC Request Indexing roz 1-2: buy-vs-rent-guide, random-number-generator, number-system-converter, stopwatch-online, fire-number-calculator, delivery-date-calculator, notice-period-buyout-calculator | Owner | ho gaya request indexing |
| 4 | Meta app Data Deletion URL = https://sabhisaab.com/privacy#data-deletion | Owner | ho gaya deletion |
| 5 | YouTube 4 channel Links: sabhisaab.com + WhatsApp | Owner | ho gaya channel links |
| 6 | IG/FB/Threads bio mein /links | Owner | ho gaya bio |
| 7 | Telegram + WhatsApp welcome post pin | Owner | ho gaya welcome |
| 8 | Instagram @sunonatak Request review | Owner | ho gaya review |
| 9 | Labh Lo Deals FB "Policy issues" ka kaaran bot ko | Owner | ho gaya policy issues |
| 10 | Meta App Review (instagram_manage_messages + pages_messaging) | Owner | auto |
| 11 | Pinterest Standard | Owner | auto |
| 12 | Bing support ka jawab aaye to text bhejna | Owner | ho gaya bing |
| 13 | Chowkidar status mein sabhinet (TradingBot repo) | Developer | ho gaya chowkidar |
| 14 | AdSense apply (mid-Nov 2026 ke baad) + certified CMP | Owner | ho gaya adsense |
| 15 | Hub video har brand + Shorts Related video | Bot + Owner | hub video <brand> <link> |
| 16 | Income-tax Act 2025 (Section 123) tax pages | AI/Developer | — |
| 17 | (Vikalp) local Telegram API: sn-tgapi-setup <api_id> <api_hash> | Owner (ek command) | — |

# 10. KABHI MAT KARNA (ek hi master list)

**Website/technical:** .html wala URL; _redirects; ek din mein 10 se zyada naye page; publish date backdate; poori site ek saath badalna; do page ka ek jaisa title/H1; tool-naam wala link homepage par; calculator ko bina chalaye sahi maanna; page script mein tools.js ke variable (DISC, NUM) bina define; meta mein straight quote; VM par na ho aisa program bina "na mile to" bachav.

**Google/Bing:** Indexing API calculator par; GSC Removals; ek URL par baar-baar request; sabhi URL ping / IndexNow --all / rotate / cron; sitemap delete-resubmit; backlink kharidna ya auto banana; Bing site: operator par bharosa.

**Content/AdSense:** aggregateRating, fake review, "12,345 log" counter; doorway (sirf number badal kar state page); card ka naam aur page ka kaam alag; Auto Ads; Calculate button ke 200px mein ad; khud ke ad par click; approval se pehle adsbygoogle.

**Channel/policy:** owner ka naam video/social par; asli insaan/celebrity, rajneeti, dharm-tulna; guaranteed return/stock tip; har Deals post par #ad (sirf affiliate wali); AI label hatana; gaana/film music; ek jaisi AI video baar-baar; proxy, fingerprint, bot-detection bypass, cold DM, auto follow, scraping; commenter data 30 din se zyada ya platform jodkar; links.html ko sitemap/IndexNow; video text Shorts ke neeche 28%/daayin button hisse mein.

**Bot/VM:** trading services ya Chowkidar ko chhedna; token chat ya GitHub par; privacy mein kuch aur aur code mein kuch aur; purani ZIP dobara (hamesha sabse naya version); do-release-upgrade; bot ke audit band karna.

# 11. Aage ka plan — traffic aur kamaai

| **Kab** | **Kaam** | **Faayda** |
| --- | --- | --- |
| Is hafte | v2.0.0 + W3 + deploy; Cloudflare token; GSC 7 URL | Indexing ki rukawat hatna |
| Roz (bot) | 4 brand × 4-5 platform; pending page pehle; har post mein page link + UTM | Bahar ke link → Google/Bing jaldi; traffic ka source GA4 mein |
| Har Ravivaar (bot) | Lambi (hub) video brand-wise rotation | YPP watch hours (1000 subs + 8000 ghante) |
| Nov 2026 | Bing ka jawab + URL Inspection; koi naya page nahi | Bharosa wapas |
| Mid-Nov ke baad | AdSense apply + certified CMP + ads.txt; phir hafte mein 2-3 naya page (GSC query data se) | Website kamaai |
| Lagataar | Jaayaz backlink (section 3.5); Quora/Reddit hafte mein 3-4 asli jawab | #1 kamzori ka ilaaj |
| FB/IG | 3-4 hafte original reels ke baad Labh Lo Deals monetization (Policy issues ka kaaran pehle) | FB kamaai |
| Baad mein | Naye platform (traffic ke hisaab se), affiliate (sirf #ad ke saath), services page ke lead | Doosri kamaai |

# 12. Seekh — galtiyan jo dobara nahi honi (sankshep)

- URL ka do pata (.html + clean) → 2 hafte traffic gaya. _redirects ne homepage toda.

- Bulk IndexNow (cron chalu reh gaya) → ~12,800 submission → Bing ka bharosa gaya.

- 13 calculator live par toote the (DISC/NUM page mein nahi) — audit pass tha; ab calculator test har deploy par.

- Bahari audit aksar purani cached site dekhta hai — pehle repo se verify.

- VM par node na hone se audit khali error deta tha — ab bachav.

- 29 Oct: CTA link homepage par, dohra vaakya, cannibalization — ab audit + bot doctor pakadte hain.

- Ek saath bahut kuch mat badlo; naye keyword/command ka kram dhyan se.

# 13. v14.1 — Bot v2.0.2 (29 Oct 2026): poori tarah automatic, mobile se

| **Kya** | **Ab kaise (apne aap)** |
| --- | --- |
| Tool ki ginti | Har caption, description, title, video ka text, thumbnail, story, comment, DM, Telegram post mein website ki ASLI ginti (188 se 190 hue to har jagah 190). Purani YouTube description bhi roz raat 23:30 theek (din mein 15). Instagram/Threads purani caption API se badal nahi sakti - nayi post sahi |
| Website link | Har jagah poora https://sabhisaab.com/... - adhoora ya bina https kabhi nahi (sab platform par ek hi jagah jaanch) |
| Schedule | Jawab na mile to slot se 20 min pehle khud manzoori; VM busy ho to slot se 40 min pehle 1 core par video; 3 script fail ho to taiyaar bank script se aakhri koshish |
| Website ZIP | Aakhri ZIP ke 15 min baad bot khud deploy ("auto deploy band" se band) |
| GitHub | Band ho to bhi ZIP + deploy VM par; copy har ghante dobara. Har Ravivaar 03:30 GitHub par sirf taaza copy (history saaf). Cloudflare token ke baad GitHub sirf padhne ki copy |
| Nigrani | Website ke page, privacy/terms har 3 ghante (repo) aur 6 ghante (live); badlaav par alert; privacy ke din badle to bot ki safai bhi |
| SEO / traffic | Har Ravivaar 19:30 Google Search Console: jo query dikh rahi par click kam - wahi video topic (usi page ke link ke saath) + page sudhaar ki salah ("seo seekh") |
| Bahar ka topic | Website se alag topic ho to bot sabse milta tool/guide page dhoondh kar wahi link lagata hai |
| Comment jawab | Video ke context ke saath, commenter ki baat ka seedha jawab, wahi line dohrayi nahi jaati; gaali/spam hide; 7-45 min baad |

Laptop kab chahiye: ab kabhi nahi. Sirf ek baar ke kaam (Cloudflare token, Data Deletion URL, GSC Request Indexing, channel Links) phone ke browser se ho jaate hain - steps Handover v5 section 4 mein.

Jo platform ka niyam hone se kabhi automatic nahi hoga: GSC Request Indexing, YouTube channel Links, bio link, WhatsApp channel post, Meta App Review, Pinterest Standard, AdSense apply, YouTube/Instagram par comment ko "like" (API nahi deti).

Sab Hisaab Roadmap v14.1 · page

# 14. v14.2 — Bot v2.0.3 + Website W4 (29 Oct 2026, shaam)

Kuch hataya nahi. Section 9 ki pending list ab bot khud `docs/PENDING.md` mein roz likhta hai (wahi asli list).

## 14.1 Kya hua (29 Oct)

| **Mudda** | **Wajah** | **Ilaaj** |
| --- | --- | --- |
| Instagram @sunonatak: DM band 28 Oct se 27 Nov 2026 ("prohibited commercial practices" / scam shak) | Naya finance account + bio mein loan/EMI + Telegram link + caption mein lamba UTM link + video mein "comment LINK, DM milega" | Bio badla (owner), Telegram link hataya, caption saaf; v2.0.3: Instagram par koi link/UTM nahi, "LINK" bulawa band, @sunonatak DM code se band. Review: owner 30 Oct |
| Teeno baaki Instagram: "Established presence" | Account naya, followers kam - saza nahi | Samay + roz original reel. Monetization review 90 din mein ek baar - Jan 2027 se pehle nahi |
| @labhlodeals Instagram: "Features you can't use" | Abhi pata nahi | Owner screenshot bheje (PENDING) |
| Sab Hisaab Money ki reel Instagram par fail (ProcessingFailedError) | IG ne file mana ki | v2.0.3: pehli fail par IG ke pakke format (H.264/AAC/30fps/yuv420p) mein dobara bana kar upload |
| Pahadi script audit ne roki (title gaane ka, video calculator ka prachaar) | Writer har topic ko calculator par mod deta tha | v2.0.3: topic-match niyam; GK/itihaas/tyohaar par calculator prachaar nahi |
| Bing | Support ne 29 Oct ko mudda hal kiya | 2-3 hafte; sirf badle URL IndexNow. Bulk kabhi nahi |
| Roz ki report "Users : 0" | GA4 bina metricAggregations ke "totals" nahi deta | W4: daily.py pehli row/rows ka jod padhta hai |
| Report der se aati thi | Report video ke kaam ki line mein phansti thi | v2.0.3: alag thread, theek samay par |
| Chowkidar mein purana ytlistener | Chowkidar TradingBot ka hai (sabhinet nahi chhedta) | Owner Chowkidar ko message bhejta hai (PENDING) |

## 14.2 Bot v2.0.3 mein naya

- **Instagram suraksha:** caption/comment se har link/UTM hatana (`meta.ig_safe_text`), sirf "🔗 Free calculator ka link bio mein 👆". Brand-wise DM rok (`state.ig_dm_block`, default sunonatak 2026-11-27). Kisi bhi script (bank samet) se "comment LINK / DM" scene hat kar saada website line (`guardtext.clean_script`).
- **Report theek samay par:** Website roz ki report 08:00 (110 min pehle taiyari, daily.py `TG_HOLD_UNTIL` tak rukti hai), tyohaar 07:30, din ki report 21:30. Badalna: "website report 8 baje" → dohri pushti. "report time" = abhi ka samay.
- **Dohri pushti:** set_schedule, set_auto, set_count, platform, add_topic, rule, set_report - sab do baar "Haan" ke baad hi.
- **Khule kaam apne aap:** todo item mein `after` (us tareekh se dikhe), `auto` (API checker: tg_pin, gsc_all, psi, cf, dm_over), `how`. Ho jaaye to bot khud hata kar batata hai; `todo_done` mein itihaas. `docs/PENDING.md` roz GitHub par + VM par.
- **Docs bot se:** "roadmap do", "handover do", "pending list do", "docs do" → taaza file Telegram par.
- **SEO diary:** har Shanivaar 21:00 (ya "seo diary abhi"): har brand ke vishay par doosre channel ki tez chalti Shorts (YouTube Data API, ~404 unit/hafta) vs hamari videos → Gemini se "unki jeet / hum peeche kyun / ab karein / naye topic / website idea". Seekh `state.insights` mein (writer maanta hai); topic sujhaav sirf hafte ke plan mein (owner manzoori). File: data/seo_diary.jsonl. "seo diary" = aakhri entries.
- **Script bank:** raat 01:00 har brand mein kam se kam 4 taaza, 3-jaanch-paas script (`pipeline.bank_refill`) - Gemini band ho ya video fail ho to slot nahi chhootta.
- **PENDING naye kaam:** sunonatak review (30 Oct), DM rok 27 Nov tak, Established presence review 27 Jan 2027 ke baad, labhlodeals features, 4 FB page status, Telegram pin (auto), WhatsApp pin, PageSpeed key (auto), Chowkidar message, AdSense 16 Nov se, FB/Threads bio mein WhatsApp.

## 14.3 Website W4 (scripts/daily.py)
GA4 users sahi; `TG_HOLD_UNTIL` (report theek samay par); "Aaj sirf ye 2 dabaayein" (roz 1-2 Request Indexing ka niyam); Bing line ab GitHub deploy par nirbhar nahi.

## 14.4 Naye KABHI MAT KARNA (section 10 mein jodein)
- Instagram caption/comment/bio mein UTM ya ek se zyada link; finance account ke bio mein Telegram link.
- Video/caption mein "comment LINK likho, DM milega" - jab tak Meta App Review na ho aur account purana na ho.
- Monetization "Established presence" ka review jaldi dabana (90 din mein ek mauka).
- Report/settings bina dohri pushti badalna.

## 14.5 Aage (bot ke liye agla, v2.1)
- Instagram review ka nateeja 27 Nov ke baad dekh kar DM feature (App Review ke baad) sirf purane accounts par.
- Ready (render ki hui) spare reel bank - abhi script bank hai.
- Chowkidar ka status sabhinet par (owner ke message ke baad pushti).


# 15. v14.3 — Bot v2.0.4 + Website W4 (v2) (29 Oct 2026, raat)

Kuch hataya nahi. Is section ke saath owner ne bheje screenshot (FB monetization, GSC, Chowkidar, bot chat) padhe gaye.

| **Mila** | **Wajah** | **Ilaaj** |
| --- | --- | --- |
| Website par "Home screen / app" button gayab | Chrome ka install button sirf tab aata hai jab browser khud prompt de; ek baar ✕ dabane par 14 din chhupta tha / app pehle se install ho to nahi aata | W4 v2: har page ke footer mein HAMESHA "📲 Sab Hisaab ko Home screen par lagayein"; ✕ ke baad 3 din. Audit ab har page par Home (logo) link + menu + install-app.js jaanchta hai - koi bhi badlaav inhe hataye to deploy ruk jaata hai |
| Chowkidar ne kuch nahi badla, par list se kaam hat gaya | Chowkidar sirf padhta hai (khud file nahi badal sakta); owner ne 'ho gaya' likha | Kaam wapas list mein, sahi tareeke se: 'chowkidar file do' → file Claude ko → fix ZIP → VM bot '🛠 Update'. sabhinet Chowkidar ko badalta nahi, sirf file padh kar (secret chhupa kar) bhejta hai |
| 'ho gaya bing' → "koi kaam nahi mila" | Bing kaam v2.0.3 install par khud 'ho chuka' mein gaya tha | Ab bot batata hai "pehle hi ho chuka (tareekh)" |
| Bot ne kaha "file delete kar di" (jhooth) | Gemini chat ne bina action ke daava kiya | Brain mein HONESTY niyam; asli delete: bot ke message par REPLY karke 'delete' likhein |
| "report time batao" par video schedule bataya | Report-samay sawaal pehchana nahi | Ab report + video dono samay batata hai |
| "seo diary abh" par khaali diary dikhi | Shabd ka milan sakht tha | 'abh/naya/aaj/chalao' ya diary khaali ho to turant banti hai |
| Pending report: "roz 10 link - har ek par Request Indexing" | watch.py ka purana text | W4 v2: "roz sirf 1-2" |
| @labhlodeals Instagram: DM 30 din band | Wahi Meta pattern | Bot DM band 28 Nov tak (state.ig_dm_block deals); owner review |
| Facebook: Content monetization invite-only; Stars + Affiliate available | Naye page | PENDING: Stars set up (charon), Affiliate (sirf Labh Lo Deals, #ad), Content monetization 'Notify me' |
| GSC: 261 indexed, 192 not indexed (6 wajah) | "All known pages" mein purane .html/redirect/utm URL bhi gine jaate hain | PENDING: wajah table ka screenshot; kuch delete/remove nahi |

## 15.1 Naya v2.0.4
- **Reply se delete:** bot ke kisi message par reply → "delete/hatao/mita do" → wo message sach mein mitta hai (48 ghante tak - Telegram ki seema). Baaki likha hukum bhi chalta hai.
- **Har baat ka record:** har free-text hukum `data/queries.jsonl`; jo bot poora nahi kar paya wo `docs/QUERIES.md` ("Khule").
- **GitHub turant:** koi kaam 'ho gaya' / bot ne khud pakka kiya / unsamjhi query → 10 min ke andar `docs/PENDING.md` + `docs/QUERIES.md` GitHub par (din bhar mein kuch hi push; roz 04:00 wala poora copy bhi).
- **Chowkidar file:** 'chowkidar file do' → TradingBot ki wo .py jismein ytlistener hai, token/secret chhupa kar Telegram par.

## 15.2 Bing - sahi tareeka (policy ke hisaab se)
- IndexNow: sirf badle URL, din mein max 10, ek URL 14 din mein ek baar (bot karta hai). Bing ka anonymous sitemap ping 2022 se band hai, par Bing Webmaster Tools mein sitemap submit karna aaj bhi sahi tareeka hai.
- Owner ek baar: Sitemaps mein sitemap.xml Resubmit; URL Inspection se sirf homepage Request indexing; API key bot ko. Bulk URL submission kabhi nahi (pichhli baar 12,800 se dikkat hui thi).
- Bing support ne 29 Oct ko mudda hal kiya; 2-3 hafte mein site wapas dikhegi.

## 15.3 Kamai ka raasta (kab kya)
- Website: AdSense 16 Nov ke baad (PENDING mein tareekh se apne aap aata hai).
- Facebook: Stars ab; Content monetization invite par; Affiliate (Labh Lo Deals).
- YouTube: YPP shartein poori hone par (lambi video hafte mein ek). Instagram/Threads India mein ad revenue nahi - traffic ke liye.


# 16. v14.4 — Bot v2.0.5 + Website W5 (29 Oct 2026, raat)

| **Mila (screenshot)** | **Wajah** | **Ilaaj** |
| --- | --- | --- |
| Instagram + FB/IG story fail: "App Secret galat/purana" | Owner ne Bing key bheji (32 akshar); bot ne use Meta App Secret samajh kar badal diya | v2.0.5: 32-akshar key par bot POOCHHTA hai (🅱️ Bing / 📘 Meta); jaanch fail to purana wapas. Install par ek baar: wahi value Bing par jaanch kar Bing key bana deta hai. Owner: 'meta secret <secret>' (PENDING, bot khud jaanchta hai) |
| 'bing key' nahi le raha | Upar wali galti | Ab 'bing key <key>' jaanch ke saath; galat ho to batata hai |
| Audit WARNING 1 | Naya nav-check 404 page par menu maang raha tha | W5: 404 chhoda |
| Bing Sitemaps: 1 sitemap, 268 URL, Success, 29 Oct crawl | Theek | Kaam 'ho chuka' |
| GSC 192 not indexed | Page with redirect 135 (.html → saaf URL, theek), Alternate canonical 13 (/?t=, theek), Crawled-not-indexed 11 (purane .html), Robots 1 (/?t=fd), Discovered 6 (naye) | Sirf "Redirect error 26" dekhna - PENDING: examples ka screenshot |
| GSC queries: '5/6/7/2 lakh loan emi', '500 mb to gb', '1 tb kitne mb', 'chakravriddhi byaj', 'ukfr login' | Log calculator ke seedhe sawaal khoj rahe | KEYWORDS bank (neeche) |
| FB page: purana naam 'Debu Typer' (2022) badla, 4 video | Naam badalna Meta allow karta hai; Page transparency mein dikhta hai | Naam ab mat badlo; roz post, About/category/website poora; followers kharidna kabhi nahi |

## 16.1 Naya v2.0.5
- **KEYWORDS bank:** roz 07:00 GSC (28 din, query+page) → data/keywords.json + docs/KEYWORDS.md (GitHub). Har shabd par "kya karein" (title/description, page mazboot, milta page, chhodo) aur haal (naya/manzoor/nahi). Bot: 'keywords', 'keywords taaza', 'keyword haan 3', 'keyword nahi 3'. Ek-ek number ke alag page kabhi nahi - ek achha page + table/FAQ.
- **HEALTH:** har brand x platform ka aakhri haal (state.platform_health) → docs/HEALTH.md; galti par turant GitHub.
- **32-akshar key:** poochh kar rakhna + jaanch + rollback. 'meta secret <secret>' command.
- Docs har push par poore naye (purana copy hat kar naya) - koi dohri file nahi.

## 16.2 Kamai (tathya, 29 Oct 2026)
- AdSense: Google ki eligibility mein traffic ki koi seema nahi (original content, policy, 18+, site ka maalik). India ke liye 6 mahine wali shart kuch jagah likhi milti hai - isliye 16 Nov ko apply; mana ho to 22 Jan 2027 ke baad dobara (PENDING mein tareekh se).
- Facebook: Stars (set up), Content monetization invite-only, Affiliate partnerships jis page par dikhe (Labh Lo Deals) - baaki page par jab Meta khud dikhaye.


# 17. v14.5 — Bot v2.0.6 + Website W6 (29 Oct 2026, subah 10 baje ke baad)

| **Mila** | **Wajah** | **Ilaaj** |
| --- | --- | --- |
| Meta secret + Bing key bot ne le liye (owner) | v2.0.5 ka sudhaar chala | Kaam list se apne aap hata |
| GSC Redirect error 26 - sab purane .html (Jul 23 - Aug 10 crawl) | Us samay ki purani galti (tab redirect loop tha); saare 26 page ab site par maujood | v2.0.6 'redirect jaanch' (har Budh 02:00 + command): har page ka .html aur / roop - ek hop mein 200. Sab sahi to owner GSC mein 'Validate fix' |
| Sab Hisaab Money Instagram: ProcessingFailedError (IG-safe video ke baad bhi) | File nahi, caption/limit ka shak: Instagram Help Center ab ek post par max 5 hashtag kehta hai | v2.0.6: IG caption mein max 5 hashtag; teesri koshish chhote saade caption se; poori galti log mein (HEALTH.md) |
| FB Stars "Available to set up" | Page eligible | Owner: Set up + payout (PAN/bank/tax). Niyam: Stars ke liye bheekh/dhoka nahi, engagement-bait nahi |

## 17.1 Naya v2.0.6
- **CHAT.md:** owner ka har message (bot ke jawab ya commenter data kabhi nahi), token/key/phone/email chhupa kar, 30 din, GitHub par 10 min mein.
- **Redirect jaanch:** website.redirect_check (HEALTH.md mein nateeja).
- **Website par video link (channel ↔ website):** bot roz 23:40 history se site/videos.json (page → sabse nayi video) banata hai, badla ho tabhi ZIP → audit → GitHub → deploy. W6 ka install-app.js us page par "📺 Is hisaab ki video" link dikhata hai (embed nahi, speed theek).
- **Instagram:** max 5 hashtag; 3 koshish (normal → IG-safe video → chhota caption).

## 17.2 Traffic ka plan (sab policy ke andar, bot apne aap)
1. Video → website: har description/Threads/Pinterest/Telegram/FB par us vishay ka page (pehle se). Instagram par sirf bio.
2. Website → channel: har page par usi vishay ki video (W6) + footer mein saare channel (W3).
3. Search: KEYWORDS bank roz; jo shabd dikhe unke liye title/FAQ (owner manzoori); IndexNow sirf badle URL; GSC Request Indexing roz 1-2.
4. YouTube: Shorts ka Related video = brand ki hub lambi video; channel Links (owner); playlist apne aap.
5. Pinterest Standard milte hi har video ka pin (abhi sandbox).
6. Kabhi nahi: view/follower kharidna, spam comment, auto-follow, cold DM, ek-ek number ke dohre page, clickbait jhooth.

## v2.0.7 (29 Oct 2026 shaam) - Telegram ka doosra raasta + Telegram ke bina khabar
Ghatna: 29 Oct ~15:45 se VM se api.telegram.org band (curl 000, ping 100% loss, telegram.org bhi). Google/GitHub chal rahe the.
tracepath: raasta 195.219.69.104 / 195.219.68.127 (beech ka bada network) ke baad "no reply". VM, RAM (9 GB khaali),
firewall (iptables/ipset/nft khaali), fail2ban (sirf sshd), Chowkidar - sab nirdosh. ~16:40 raasta khud khula.
Asar: sabhinet aur Chowkidar dono chup (Chowkidar bhi isi VM par, isi Telegram par).

Kya joda:
- tg.py: kai raaste. Kram: local Bot API (agar SN_TG_API) → seedha api.telegram.org → Cloudflare relay. Connect 8 sec mein
  na ho to agla raasta; jo chala 10 min usi par, phir seedha dobara. Raasta badle to owner ko ek sandesh. Galti ke text
  mein token/relay key kabhi nahi (_hide).
- relay.py (naya): owner ke Cloudflare account par Worker 'sabhinet-relay' (free). Sirf sahi key + sirf api.telegram.org
  tak (bot/<token>/method aur file/bot... raaste). 'cf token' + 'cf account' aate hi bot khud banata hai (har 6 ghante
  dobara koshish jab tak na bane). Command: 'raasta haal', 'relay banao'.
  Token mein chahiye: Workers Scripts Edit, Workers KV Storage Edit, Account Settings Read (+ Cloudflare Pages Edit website ke liye).
- VM ke bina chowkidaar: wahi Worker har 10 min (cron) KV mein VM ki dhadkan dekhta hai (bot har 10 min 'beat' bhejta hai).
  30 min se dhadkan nahi → Cloudflare se seedha owner ko Telegram + ntfy (Oracle console ke steps ke saath). Wapas aaye to
  ek "wapas" sandesh. Bot token Worker ke 'secret' binding mein (owner ka apna CF account; chat/GitHub par kabhi nahi).
- backup.py (naya): ntfy.sh (free app, bina account). Telegram par bheja na jaye to wahi text ntfy par. Har ntfy khabar par
  button (Haal / Sab theek? / Resume). Hukum sirf surakshit: haal, status, pending, pause, resume, vm, raasta, menu.
  ntfy se hukum aaye to 3 min tak har jawab ntfy par bhi. Topic 24-akshar random (secrets/backup.json). Din mein max 80.
  Command: 'backup setup' (owner ke 3 step), 'backup test'. Pehla hukum aate hi 'ntfy_ok' (Pending list se khud hatta).
- Service jaanch: chowkidar, nifty-live, delta-live, nifty-chart ko har 10 min SIRF padhta hai (systemctl is-active).
  2 baar lagataar band = ek laal khabar (relay/ntfy se bhi pahunchti hai). Kabhi restart/stop nahi.
- YouTube top comment: TV/device login mein comment ki ijaazat (youtube.force-ssl) milti hi nahi → har upload par 403.
  Ab pehli 403 par band (state yt_comment_noscope). Shorts mein comment link waise bhi clickable nahi.
- writer.py: Suno Natak ka aakhri vaakya ab "isi topic ka free tool" (calculator sirf hisaab wale topic par) - 29 Oct ko
  AI audit ne dictionary topic par "free calculator" CTA ko bhramak bata kar roka tha.
- Pending list: Pinterest App secret badlna (29 Oct chat/screenshot mein khula), relay, ntfy, CF token ki sahi ijaazat.

Jo NAHI kiya (aur kyun):
- Chowkidar ka code: file VM par hai, repo mein nahi. Sahi tareeka (PENDING): 'chowkidar file do' → file Claude ko → fix ZIP
  (relay + ntfy + status mein ytlistener ki jagah sabhinet) → Chowkidar '🛠 Update'. Tab tak sabhinet hi Chowkidar ki
  service ko padh kar khabar deta hai.
- Trading services (nifty-live, delta-live, nifty-chart): niyam - kabhi nahi chhedna. Unke Telegram alert ka doosra raasta
  sirf owner ki DOHRI pushti, bazaar band ke samay, alag ZIP se.
- GitHub ko hukum ka raasta nahi banaya: repo public hai, hukum/khabar sabko dikhegi. GitHub sirf roz ki status copy.
- VM poora band ho to kaam (video/upload/website) nahi chal sakta - ye sab VM par hi hai. Cloudflare sirf khabar deta hai.

## v2.0.8 (29 Oct 2026, 17:10) - token kabhi log/GitHub/Gemini mein nahi
Ghatna: owner ne Cloudflare token bina 'cf token' ke bheja → secret_intake ne naya format (cfut_...) nahi pehchana → text
Gemini tak gaya, bot ke jawab mein token dikha, queries.jsonl/chat.jsonl mein likha gaya → GitHub ki push protection ne
mirror push rok diya (repo public hai, achha hua). Relay phir bhi CHALU hua (17:06).
Kya joda:
- updater._mask: Cloudflare (cf??_...), 40-hex (Pinterest secret), aur koi bhi 32+ akshar ka akshar+ank wala shabd chhupa.
  log_query (q + reply) ab mask hota hai (pehle nahi hota tha).
- updater.scrub_logs(): har start par purane chat/query log saaf. Mirror ke waqt bot ki likhi har docs file par aakhri mask.
- secret_intake: cfut_/cfat_ token bina prefix ke bhi pakad kar mitata/rakhta hai (Gemini tak kabhi nahi); akela 40-hex
  mitata hai aur 'pinterest secret naya' batata hai.
- Command 'pinterest secret naya': secret reset ke baad naya secret lena (pehle /pinterest purana secret hone par nahi poochta tha).
Owner ke kaam: Cloudflare token dobara Roll + 'cf token <naya>'; Telegram mein token wale purane message mitana;
Pinterest app mein Redirect URI 'https://sabhisaab.com/' jodna (OAuth "redirect URI does not match" isi se).
