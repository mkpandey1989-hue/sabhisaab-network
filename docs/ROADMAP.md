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
| IP | 140.245.x.x — RESERVED (Meta app allowlist, Google API key, Dhan, Delta isi par) |
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

- Meta: Business portfolio "Sabhisaab Network"; app "Sabhisaab Publisher" (Live, IP allowlist 140.245.x.x, Require App Secret ON); system user sabhisaab-bot; Threads API use case.

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

## v2.0.9 (29 Oct 2026, 17:15) - Pinterest OAuth "redirect URI does not match"
Redirect URI 'https://sabhisaab.com/' Pinterest app mein pehle se juda tha, phir bhi galti. Owner ke screenshot ka URL
developers.pinterest.com/apps/1630338/ - code mein APP_ID "1630538" tha (galat app = galat redirect). Ab App ID
pinterest.json mein ('pinterest app id <id>' command); code ka purana number sirf fallback.

## v2.0.10 (29 Oct 2026, 17:40) - Pinterest secret kisi bhi tarah bhejo
Owner ne 'pinterest secret naya <secret>' EK message mein bheja → command sirf akela text pehchanta tha → text Gemini tak
gaya (Gemini us waqt band) aur secret chat mein khula raha. Ab koi bhi message jismein 40-hex ho = Pinterest App secret:
turant mitao, rakho, login link do. (Owner ke paas aur koi 40-hex key nahi; GitHub token ghp_/github_pat_ hote hain.)

## v2.1.0 (29 Oct 2026, raat) - bot ka dimaag poore din band nahi hoga + poori chat + Chowkidar fix
1. Gemini "jawab nahi de raha" (asli kaaran): har 429 par model POORE DIN ke liye band ho jaata tha. Google free tier ka
   429 aksar MINUTE ki seema hota hai. 2-3 jaldi sandesh = saare model din bhar band. Chowkidar (alag code) isliye chalta raha.
   Ab: din ki seema = Google ke agle din tak; minute ki seema = retryDelay/65 sec. Khaali/block jawab (KeyError 'candidates')
   ab agla model. Sab Gemini band → Cloudflare Workers AI (llama, owner ka CF account, free) = doosra dimaag.
   Token mein 'Workers AI: Read' chahiye (Pending list). Sab band ho to saaf sandesh: kitne min mein wapas.
2. CHAT.md: ab owner (👤) + bot (🤖) dono, samay ke kram mein, 30 din. Comment alert (commenter data) kabhi nahi; @handle,
   secret, phone, email chhupe. Docs ke liye alag _mask_tokens (pehle 'PageSpeed key (website...' galti se chhup gaya tha).
3. Chowkidar 'ytlistener' → 'sabhinet': owner ke kehne par (29 Oct, kai baar). Command 'chowkidar fix' → preview → ✅ → ✅✅
   (dohri pushti) → backup *.bak-sabhinet-<samay> → sirf shabd badla → py_compile → sudo systemctl restart chowkidar →
   active na ho to backup wapas. Bazaar khule (Som-Shukra 9:00-15:35) mein mana. NIYAM BADLA: Chowkidar ko sirf isi
   command se, owner ke dohre button se. Trading service abhi bhi kabhi nahi.
4. Pinterest: Standard form 29 Oct 18:47 bhara (email aaya). state pin_form; 'pinterest kya hua' = haal. 26 Nov ko
   community post ki yaad (Pending), 19 Nov ko Bing 'site:' jaanch ki yaad.
Baaki (agle kaam): Chowkidar ke apne Telegram ko doosra raasta (uska code chahiye - 'chowkidar file do'); trading alert ka
doosra raasta sirf owner ki dohri pushti par.

## v2.1.1 (2 Nov 2026) - POSTMORTEM: 30 Oct VM restore + poora audit tool
Kya hua: 30 Oct ko VM ka data mit gaya. Owner ne purane backup se (Gemini ki madad se) chalu kiya. GitHub par VERSION 2.0.8
mila (code hubahu 2.0.8, Gemini ne code nahi badla). 2.0.9 / 2.0.10 / 2.1.0 ke saare sudhaar kho gaye. chat.jsonl 30 Oct
19:10 se shuru = restore ka samay. secrets/ purane backup ke = kai token purane.
Jo toota (GitHub STATUS/HEALTH/CHAT se pakka):
- Pinterest: App ID phir galat (1630538) → login link galat app ka → 'Authentication failed'. env=production, live=False,
  oauth=False → har upload par Pinterest 401 "insufficient permissions" (❌ HEALTH mein). Owner ke mutabiq 2 Nov ko Standard
  manzoori mil chuki. Fix: APP_ID default 1630338; Standard live na ho aur env production = pin chhodo, HEALTH mein
  '⏸ intezaar' (❌ nahi). Login ke baad check_standard roz 11 baje khud LIVE karega.
- Threads: Money/Deals/Pahadi ke token 30 Oct ko khatam (backup purana tha, 20-din refresh chhoot gaya). STATUS 'threads OK'
  GALAT dikhata tha (sirf file dekhta tha) = "report galat". Fix: threads.alive() - /me se asli jaanch (6 ghante cache),
  'Sab theek?' aur STATUS dono mein.
- Cloudflare Account ID 30 Oct ko 31 akshar ('1' chhoota) → relay/deploy/AI nahi chal sakte. Fix: 'cf account' sirf 32-hex
  maanta hai.
- Gemini 'busy' (2.1.0 ka fix kho gaya) → 2.1.0 phir se andar.
- ESCALATE: "Google Analytics Data API has not been used in project 46284..." → traffic/video-click report adhoori (owner
  31 Oct ko 3 baar poochha). API enable karni hai (audit mein poora link).
Naya: app/vmaudit.py - 'vm audit' command. SIRF PADHTA HAI. 7 hisse: system (ghadi/NTP, RAM, disk, swap, OOM, update),
service/timer/cron (failed, restart, boot-enable, root), bot (har Telegram token ka fingerprint + kahan-kahan, getMe,
webhook, atke sandesh, 409 takraav, ek Gemini key kai jagah), suraksha (port, ufw, fail2ban, sshd, keys, login, user,
NOPASSWD, /tmp executable, anjaan CPU process, open connection, secret file permission, git remote/secret), sabhinet
(har brand x platform asli login, Pinterest, Cloudflare verify, relay, ntfy, Gemini, 7 din upload grid, galti ginti, band
Google API link, size, secrets permission), file/folder (har folder size/umr/kis service mein, bade file, backup, cache,
journal, venv), Chowkidar + trading (sirf padha). Report file sirf owner ke Telegram par (GitHub par nahi - public repo).
Pending (auto-jaanch ke saath): vm audit, Threads token x3, Pinterest login, CF account ID, Chowkidar fix.

## v2.1.2 (2 Nov 2026) - pehle VM audit (15:56) ke nateeje
Audit: system swasth (RAM 10.8 GB khaali, disk 18%, swap 4 GB, OOM 0, update 0, NTP sync, IST sahi). SSH sirf key,
password/root band, fail2ban 42 ban. Do Telegram bot alag token, webhook nahi, 409 nahi. Relay LIVE, Cloudflare token
active, account ID 32. Trading 3 service active (sirf padha).
Postmortem: 27-30 Oct VM band/restore = video nahi (outage). Restore ke dauran sabhinet 98 baar "Failed to load environment
files" (bot.env nahi tha) - ab theek. 31 Oct se roz video; Suno Natak 31 Oct chhoota (IG ProcessingFailed + audit rok).
Sudhaar:
- ask_grounded (Google-search Gemini): 3 din mein ~50 bekaar 429 → model-wise cool ('grounded_cool') + sab fail = 1 ghanta band.
- imagegen: free account par image model seema 0 → '7 din' rok ('limit: 0'), sab 429 = 24 ghante (pehle har 6 ghante 8 koshish).
- site_repo/config.json (isme bot token + Bing key) ab chmod 600 (644 tha). Public repo mein nahi hai (.gitignore) - pakka kiya.
- vmaudit: 'video nahi' sirf pichhle 3 poore din (purana outage galat chetavni deta tha).
Owner ke liye (bot nahi karta): ~45 GB kachra (.sandbox.img 30G - restore/carve ka, vm-backup.tar.gz 7.4G aur
backups/cfg-20261102.tgz 7.7G dohre, ~/.cache 6.3G). Port 111 (rpcbind) band karna. 8001 (nifty_option_LIVE), 8002 (delta),
8003 (chart) = trading ke dashboard - Oracle Security List mein sirf zaroori IP. Chowkidar: 5 file mein ytlistener
(chowkidar.py chalu, baaki copy/inbox) → 'chowkidar fix'.

## v2.1.3 (2 Nov 2026, 17:00) - 'Install' button nahi chal raha tha (MERI galti v2.1.0 se)
Kaaran: on_callback ke andar ek shakha mein `from . import updater` likha (Chowkidar fix) → Python ne poore function mein
`updater` ko local maan liya → 'up:' (Install) button par UnboundLocalError (audit: 10x LOOP ERROR). Isliye v2.1.2 ka
Install dabane par kuch nahi hua. Sudhaar: bot.py ki saari 5 local `from . import updater` hataayi (upar global import hai).
Poore app/ par AST jaanch: kisi function mein local import se pehle global naam ka use nahi (koi aur aisi galti nahi).
Is baar install SSH se (button tootta hua tha): data/update ka sabse naya install.sh chalao.
Pinterest LIVE ke baad 'Cannot add non-sandbox pins on sandbox boards' (code 15): go_live ne sandbox wale '<Brand> board'
chun liye the (money, pahadi). Ab: go_live asli board pehle chunta hai; code 15 aaye to production mein naya PUBLIC board
('<Brand>', na mile to '<Brand> | Sab Hisaab') banakar wahi pin dobara. HEALTH ka baar-baar DHYAN isi se tha.
2.1.2 ke sudhaar bhi isi mein (grounded/image Gemini rok, config.json 600, audit 3-din).

## v2.1.4 (2 Nov 2026, shaam) - traffic, Gemini kram, Chowkidar ka sahi sudhaar, ntfy suraksha
- Website traffic: owner ke sawaal ("video link se kitne aaye") Gemini ke paas jaate the → "GA access nahi". Ab koi bhi
  sawaal jismein website/site/link/traffic + aaye/click/kitne log ho → seedha GA4 (din: aaj/kal/hafta/mahina). Report mein
  ab HAR link: source / medium / campaign(brand) → log, aur utm wale landing page. GA4 galti ho to owner ka kaam link ke
  saath (API Enable / service account ko Viewer) + Pending list mein ('ga_need'). ESCALATE: "Analytics Data API has not
  been used in project 46284..." = API enable karni hai.
- Gemini: kram ab 'aaj chala' → 'anjaan' → 'galti wale' (roz naya mauka). Pehle sabse naya (4-argon, 3.8/3.7/3.6 jo free
  mein ⚠️) hamesha pehle = har sawaal par 3-4 fail. 'Sab theek?' ab asli kram dikhata hai.
- Chowkidar (MERI GALTI v2.1.0): andha badlaav `"ytlistener" not in` (purana hatane ka filter) ko `"sabhinet" not in`
  bana diya = sabhinet hi status list se gayab. Ab _cw_transform: filter ytlistener par, baaki sabhinet; pehle ka ulta
  filter bhi wapas. Owner 'chowkidar fix' ek baar aur (Pending, auto-jaanch).
- ntfy topic GitHub CHAT.md mein khul gaya tha (bot ka setup sandesh). Ab sn-... chhupta hai; bot ne ek baar apne aap
  naya topic banaya (relay ka NTFY_TOPIC bhi naya) + owner ko naya setup bheja. Command: 'backup reset'.
- Dobara-koshish (reopen) par poora upload report baar-baar aata tha (2 Nov 16:30-16:41 Pahadi 4 baar). Ab sirf naya
  ✅/❌; kuch naya na ho to sandesh nahi; WhatsApp copy sandesh sirf pehli baar.

## v2.1.5 (2 Nov 2026, raat) - comment ka sach, poora haal, indexing ka pakka record
- Comment jawab: Gemini fail = `classify` par return = koi jawab nahi (owner: "pehle reply deta tha, ab nahi"). Ab Gemini
  na chale to chhota vinamra jawab ("🙏 Dhanyavaad...") - link/spam/promo jaisa comment ho to nahi. Har kadam ki ginti
  (state cstats): naye YT/IG, line, gaye, atke, AI fail, aakhri galti. Command 'comment haal'.
  YouTube: TV/device login Google se 'youtube.force-ssl' nahi deta → comment likhna (reply/top comment) 403. Pehli 403 par
  'yt_reply_noscope' → YT ke jawab line mein nahi (bekaar koshish nahi). YT comment padhe jaate hain; IG ke jawab jaate hain.
- 'poora haal' / koi bhi sawaal jismein follower/like/view/comment/subscriber mein se 2 ho: YT subscriber + kul views,
  FB followers, IG followers + post, aakhri videos ke views/likes, comment haal - ek sandesh.
- IndexNow: data/indexnow_log.jsonl (hamesha, append-only: samay, URL, Bing ka code, kyun) + GitHub docs/INDEXING.md
  (aakhri 300) + 'bing haal' (Bing crawl/index + IndexNow ginti). 14-din/10-roz niyam wahi.
- site_repo/config.json har start par chmod 600 (2.1.2 ka fix sirf dobara likhne par lagta tha).

## v2.1.6 (2 Nov 2026, raat) - Google ka asli kaaran, roz indexing, pending number se, IG lambi video
ASLI KAARAN (traffic report + sitemap band): 30 Oct restore mein secrets/gsc_sa.json NAYI service account ki aayi
('ais-gemini-key-...', doosra project, Gemini se banwayi). GA4 aur Search Console mein ijaazat purani
'gsc-bot@sabhisaab.iam.gserviceaccount.com' ko hai (owner ke GA4 screen par Viewer), aur Analytics Data API purane project
'sabhisaab' mein chalu hai. Isliye: "API not used in project 46284..." + koi GSC data/sitemap nahi.
Ilaaj: purane gsc-bot ki NAYI JSON key → bot ko file. Command 'google jaanch' (GSC + GA4 asli test + sahi link/steps);
JSON aate hi bot khud jaanchta hai. Traffic galti par bhi yahi jaanch.
- Roz 11:20: Google ko sitemap (GSC API) + IndexNow ko naye/badle page (sitemap lastmod 10 din + GSC not-indexed),
  sirf jo pehle nahi bheje (indexnow_log se), 10/din. Galti ho to owner ko alert. Command 'index bhejo'.
- Pending: '🧾 Mere kaam' ab numbered; 🤖 = bot khud API se pakka karke hatata hai; baaki 'ho gaya <number>' → ✅ button
  (pakki pushti) → sirf wahi ek kaam hatta hai. CHAT.md ab 15 din.
- IG 'ProcessingFailedError' (Suno Natak 8x, Money 3x): pehli fail par IG-safe re-encode (pehle se), doosri par video
  90 sec se lambi ho to 89 sec ka reel + "Poori video YouTube par". Galti mein video ki lambai bhi likhi jaati hai.
- Gemini kram (owner): sabse uncha model pehle; seema (429) wala thodi der cool; 'limit: 0' = poora din; sirf asli galti
  wale aakhir mein.
- Link ka page brand se mel khaye (Pahadi shabd → bike-loan-emi nahi): BRAND_PAGE_WORDS, na mile to homepage.
- Har Ravivaar 10:30: khud safai (guard.cleanup) + self-audit; 🔴 ho tabhi file bhejta hai. Stock (reels) 5 din (pehle 10).
- Duplicate: upload se pehle 3 jaanch pehle se (state history, signature, channel ke recent title >0.8) - wahi rakhi.

## v2.1.7 (2 Nov 2026, raat) - roz ke khaas din bina Gemini ke bhi
- app/indiacal.py: apna pakka calendar - har saal ke rashtriya/antarrashtriya din (26 Jan, 15 Aug, 9 Nov Uttarakhand
  sthapna, 14 Nov bal diwas, 31 Mar FY end, 31 Oct bachat diwas...) + Diwali-Chhath 2026 (Dhanteras 6, Diwali 8,
  Govardhan 9, Bhai Dooj 10 (aage-peeche ka note), Chhath 15 Nov; kai panchang + Business Standard 27 Oct 2026).
  Google-search Gemini fail ho (free seema) to yahi; chale to uski list + is calendar ke chhoote din.
  Bade din par us brand ki video ka vishay roz ke plan mein (pehle se plan ho to nahi chhedta).
  NAYE SAAL (2027) ke chandra tyohaar (Holi, Eid, Diwali...) Claude DATED mein jode - pakke srot se.
- Bade din: story (FB+IG) + Telegram ke saath ab FB page post + Threads post LINK ke saath (dono mein link clickable).
- Tyohaar story ab subah 07:00 (pehle raat 00:10 - koi dekhta nahi tha).
- AI_START 3c: har AI pehle CHAT.md padhe (15 din), galat/adhoore jawab fix kare.

## v2.1.8 (2 Nov 2026, raat) - CHAT.md se mili 3 galtiyan
(CHAT 20:52-20:59) 1) 'ho gaya pin secret' → "koi kaam nahi mila": item ka text "Pinterest App secret..." mein "pin secret"
ek saath nahi. Ab har shabd alag-alag dhoondha jaata hai; kai mile to sirf sabse milta ek hatta hai. 2) Owner ne PageSpeed
key bina 'psi key' ke bheji → Gemini tak gayi → "maine note kar li" (jhooth, kahin nahi rakhi). Ab AIza... key pakad kar
mitao + button 'PageSpeed' → rakh kar asli jaanch (sabhisaab.com mobile speed). Brain prompt: key/token par kabhi
'note kar liya' nahi. 3) Pro buttons (Poora menu ke upar 4 line): Poora haal, Link se traffic, Hafte ka traffic, Google
jaanch, Bing + index, Aaj index bhejo, Comment haal, Raasta haal, VM audit, Chowkidar fix, Backup setup, Kaam (number).
Pushti: GA4 + GSC 20:33 se ✅ (purane gsc-bot ki nayi key) - traffic report chal rahi (aaj: pinterest, threads se log).

## v2.1.9 (3 Nov 2026) - Claude: poore VM + Chowkidar v5.1 ka 3 baar audit, dono bot ka takraav khatam
Aadhaar: owner ki bheji vm-audit-20261103-0133.txt + chowkidar_v5_1_mega_legend_final.zip (3,636 line, poori padhi).
Saath mein alag ZIP: **chowkidar_v5_2_safe.zip** (sirf @manoj_vm_chowkidar_bot ko; ise sabhinet NAHI lagata).

Mile hue takraav/khatre aur sudhaar (sabhinet taraf, is ZIP mein):
- ZIP galat pehchan: sabhinet har install.sh wali ZIP ko apna update samajhta tha (Chowkidar v5.1 ZIP mein bhi install.sh tha ->
  Chowkidar bina uski dohri pushti ke lag jaata). Ab: chowkidar.py wali ZIP kabhi install nahi, owner ko Chowkidar bot ka raasta;
  update tabhi jab install.sh + VERSION + app/bot.py saath hon. (app/updater.py receive)
- 'chowkidar fix' sirf chowkidar.py / chowkidar_pro.py dekhta hai (pehle data/inbox ki purani upload bhi -> VM audit ka jhootha 🟡).
  v5.2 is regex ke saath surakshit jaancha gaya (transform se koi line nahi badalti).
- GitHub token: site_repo token-wale URL se clone hota tha -> token .git/config mein (Chowkidar backup/export se Telegram tak ja sakta
  tha). Ab har sync par origin bina token (repo public; push pehle jaisa URL mein token). VM audit ab 3 level gehra git bhi dekhta hai.
- render._ff/probe: samay-seema (60 min / 2 min). 4 ghante wala atka ffmpeg isi se tha.
- guard.backtest_running: Chowkidar ke backtest (/sandbox/runs/) par bhi render rukta hai.
- vm audit: .cache (huggingface = sabhinet ka model) aur .local ko 'mat mitao' likhta hai.
- tasks SEED_V219: owner-kaam (Chowkidar v5.2 install [auto cw52], Cloudflare token mein Tunnel/Zone/DNS permission [auto cw_dash],
  (marzi) /kachra se KACHRA-2nov, purane script ki file Claude ko). vm audit Chowkidar ka dashboard firewall pehchanta hai.

Chowkidar v5.2 mein (alag ZIP) - saar: roz ka backup KACHRA/img/tar/video/secret/.git ke bina (7.7 GB -> MB); git token pakad + button;
sabhinet ke folder mein kabhi likhna/kholna nahi; Gemini par koi alag seema NAHI (owner 3 Nov: Chowkidar se baat zaroori) -
sirf jo model sabhinet ke liye quota par ho wo aakhir mein; install ke baad apne aap: git token hatana, khula secrets.tgz encrypt,
phoola 7.7 GB backup hatana, purani copy saaf, dashboard SHIELD (har IP par seema) + Cloudflare TUNNEL (https://<chhupa>.sabhisaab.com,
private IP par, pakki jaanch ke baad hi seedha port 8001-8003 band; webhook wala port kabhi band nahi; tunnel gire to shield ke saath khula);
sabhinet ki galti par dohra alert nahi (sirf baar-baar girna); sabhinet busy ho to restart/reboot dohri pushti; delta-live trade ho to
port-hang restart nahi; backtest bina sandbox image (25 GB shart); shaam ki EK report 21:00; Telegram band -> relay -> ntfy;
naye /takraav aur /kachra.

Abhi khule (agle AI ke liye): IG ProcessingFailedError (Suno Natak 9, Money 3 baar) ka kaaran pakka nahi; purane script
master_guard.py / vm_health.py / ntfy_monitor.py / maintenance.sh ka code nahi dekha (owner /get se bhejega); port 8001-8003;
ubuntu ka NOPASSWD:ALL sudo seemit karna (dhyan se, saare bot isi par); venv mein ~3 GB CUDA torch (ARM VM par bekaar) - CPU torch.
Hataya: kuch nahi (purana content wahi).

## v2.2.0 (3 Nov 2026) - Sample Studio + din-plan + koi sawal dohraav nahi (sab purana waise hi)
Owner ka hukum: purane saare feature/report waise hi; naya sirf jodna. Har channel ka namoona dekh kar look pakka,
pasand na aaye to agla, mitao bolo to turant mite; setting badle to dohri pushti; ek baar pakka = roz apne aap, slot kabhi na chhoote.
- app/studio.py: NAMOONA (status "sample" - tick/upload/pending/report kabhi nahi chhoote). Video + 3 thumbnail + "kahan kya jayega"
  (YouTube/FB/Threads/Telegram page link, Instagram bina link, Pinterest link, video par sabhisaab.com, AI label, Money SEBI).
  Buttons: 👍 Thumb 1/2/3 (pasand note), 🎨 Naye thumbnail, ➡️ Agla namoona (pichhla turant mitta; 5 look ghoomte hain:
  Seedha / Kahani / Quiz / Myth vs Fact / Top-3 tips), 🗑 Mitao (VM file + Telegram ke saare message), ✅ Ye look pakka
  (DOHRI pushti -> state brand_look[brand] = look style + pasand thumbnail layout/rang), 📤 Isi ko daalo (normal manzoori;
  reason owner ka, autopilot kabhi nahi). Bhoola namoona 1 din mein apne aap saaf.
- Pakka look: pipeline.prepare roz ki short video mein look style; thumbs.make mein pakka layout+rang = Thumb 1 (autopilot isi se).
- app/weekplan.py: DIN-PLAN - har channel ka har din andaaz (sawal/kahani/myth/tips/galtiyan/10-sec challenge/Ravivaar recap);
  Pahadi: Somvaar Uttarakhand GK, Budhvaar purane naam, Shukravaar pahadi shabd (180 din dohraav nahi, tathya audit_ai Google jaanch).
  Badlaav "somvaar money: kahani" / "din plan band|chalu" - dohri pushti (dp:y). Custom topic/lambi video par laagu nahi.
- writer: us channel ke pichhle 60 title + 40 hook "mat dohraao" ke saath; har nayi script ka hook state.hooks mein.
- thumbs: 4 naye modern rang (neon, sunset, royal, mint) - learn.pick inhe bhi aazmata hai; Studio se pakke.
- topics: Pahadi ke 4 naye idea. Menu: 🧪 Sample studio, 📅 Din-plan, 📘 Studio manual. docs/SAMPLE_STUDIO.md.
- tasks SEED_V220: "chaaron channel ka look pakka" (auto looks4).
- Bahari ZIP "sabhinet-v11_2_0-final-guaranteed" (3 Nov) NAHI lagaya: wo v2.1.0 (29 Oct) par bana tha - v2.1.1 se v2.1.9 tak ke
  sudhaar gayab (vm audit, Pinterest App ID 1630338 [usme galat 1630538], IG 89-sec, ntfy rotate, IndexNow log, Chowkidar-fix
  ka surakshit regex [usme andha 'ytlistener->sabhinet' jo Chowkidar v5.2 ki filter line ulat kar sabhinet ko nigrani se hata deta],
  ZIP pehchan, git token, ffmpeg seema). "Claude-Audit Verified" likha tha - Claude ne use kabhi jaancha nahi tha.
  Usme se laayak cheez (puzzles, sfx, 9 visual style, offline panchang, gallery commands, GA4 dwell) ek-ek karke, Sample Studio
  ke namoone se jaanch kar hi aage aayengi. vault_web (8099) nahi: relay + ntfy pehle se; ek aur khula darwaza zaroori nahi.
- updater: nayi ZIP tabhi lagti hai jab uske ROADMAP mein abhi wale version ka '## vX' hissa ho (purane base par bani ZIP
  jaise v11.2.0 -> laal alert, kuch nahi badla).
- Meta Graph API: abhi v23.0 (aaj tak chalu; v25.0 Feb 2026 latest). Badlaav namoona-jaanch ke baad hi (data/graph_ver.txt).
Hataya: kuch nahi.

## v2.3.0 (3 Nov 2026) - v11.2.0 ke saare feature (jaanch + sudhaar ke saath) + Premium Neon design. Purana sab waisa hi.
Aadhaar: GitHub v2.2.0 (acc19bb). Bahari 'sabhinet-v11_2_0-final-guaranteed.zip' ke har feature ko ek-ek karke milaya;
sirf 'billguard restart-loop fixer' nahi (system ka kaam; Chowkidar v5.2 karta hai; sabhinet system/trading nahi chhedta).
Step 0: trend/keyword kachra filter (seo.relevant/BAD/BRAND_EXTRA, keywords_for(topic, brand)) - "Sambalpuri song", "ssc gd" titles band.
Step 1 suraksha: guard.scrub_for_ai (Gemini Blindfold: ask_cf/ask_gemini/ask_grounded/imagegen) + blindfold_status;
  reap_stuck_ffmpeg (SIRF sabhinet/reels.slice ka; v11 har ffmpeg maarta tha); clean_uv_cache (huggingface kabhi nahi);
  do-charan post-taala _locked_post/acquire_post_lock (FB/IG/Threads/Pinterest/YouTube; beech mein ruka -> dobara nahi + alert;
  fail -> taala khulta - v11 din bhar band kar deta tha); youtube.quota_status; meta.check_ig_publishing_limit,
  dm_already_sent/record_dm_sent; threads.check_threads_quota/post_riddle_thread; pinterest.can_pin_now (15/din, URL par 2);
  SPARE_REELS_DIR spare_reel_refill (02:30) + _take_spare (slot kabhi na chhoote); build_offline_long_script (Ravivaar,
  Gemini band ho tab); vault_web 127.0.0.1:8099 (DEFAULT BAND, dohri pushti, sirf jaankari wale hukum).
Step 2 video: imagegen.procedural_scene (9 style) + make_infographic_pin (Pinterest 1000x1500); render: neon border,
  progress bar, power-word rang, timer+rewatch SIRF challenge/puzzle par, batched overlays (>8 scene), nice 15; HUD setting.
Step 3 awaaz: sfx.py (uchcharan [7.5 = dashamlav; Hinglish 'po/pan/ac' nahi badalte], scene raftaar, sting/whoosh/tick/riser,
  dheema pad, setting 'awaaz'), measure_lufs (ASLI; v11 hamesha pass likhta tha), contrast/H.264/kaala-frame gate, carousel.
Step 4 puzzle: puzzles.py 11 mode (hash bina reel-code = asli dohraav rok; rang-milaan tark se; galat matchstick hata;
  mazaak-shabd 'मज़ेदार' label; nakli % hata; exam 6 topic dual-verify; asli _distractors (pehle 'विकल्प B'); jawab ki jagah
  barabar; mode khatam -> baari-baari dusra), prepare(script_in) + challenge-din puzzle, Threads paheli, WhatsApp card (bina nakli rank).
Step 5: calendar_in asli offline panchang (Meeus/Lahiri/purnimant; v11 ka angrezi-mahina wala galat) + badge; sirf pakki tarikh
  ke tyohaar offline; learn hook bandit (bina jhoothe %) + views se jeet, score_script, retention/fatigue salaah; growth vip/
  comment-topic/story jaanch; company revenue/10-vibhag/milestone ASLI (v11 haath se 'READY'); gallery commands; DPDP ledger;
  scheme rates + dhara 123 (80C, 1 Apr 2026 - web se pakka); GA4 dwell; calc smoke; scroll forensics.
  BUG (LIVE v2.2.0 mein bhi): prepare ka bank-fallback clean_script UnboundLocalError -> theek (import function ke shuru mein).
Step 6 website: web_widgets (nakli rank/percentile/'68%' hata; sudhaar = mailto; reel-code asli reel-codes.json) - SIRF EK page
  DRAFT -> Claude -> website ZIP (bot khud live nahi karta); widget live ho to reel-codes.json apne aap.
Step 6b (owner ke screenshot): app/design.py PREMIUM NEON QUIZ - neon frame, category pill, mode-wise neon chitra, kaanch card,
  A-D vikalp, jawab hara + nishaan, timer ring, bada CTA, 3 neon thumbnail; SAARI short video ka naya default (state neon_default;
  Studio 'Purana classic'). Gemini image mile to peeche 3D AI chitra. Nakli 'votes %' kabhi nahi (niti).
Step 7: 50-button Pro Deck (PRO_DECK_PANELS pe:1..50, sab asli kaam; 27/28/33 dohri pushti), elite_audit.run_6pass_audit ASLI
  (puzzle sawal kharch nahi karta), audit.deep_6stage_audit asli, news.exam_alerts, Reel Code Khoj, Doubt Shield, Panchang Badge;
  updater: purane base ki ZIP (ROADMAP mein abhi wala '## vX' nahi) kabhi install nahi.
Jaanch: 54 file compile, pyflakes, UnboundLocal scanner, 50/50 deck, 150-300 puzzle (0 dohraav), asli ffmpeg render (short +
  12-scene lambi), -13.8 LUFS, 16 gate, 6-pass 6/6. Hataya: kuch nahi.

## v2.3.1 (3 Nov 2026 shaam) - har channel roz 2 SAWAL wali reel, safe-zone design, Pahadi GK + purane shabd, Bing API, PENDING saaf
Owner (screenshot 4:43 PM): naya neon design aaya par video purane andaaz (kahani) ki thi; neeche 'sabhisaab.com' platform
ke caption ke neeche dab raha tha; Bing par 1 bhi URL submission nahi; PENDING mein dohre/purane kaam.
- config.SCHEDULE: har channel 2 slot (pahadi 09:30,18:00 | money 12:30,20:30 | deals 16:00,21:30 | sunonatak 19:30,13:30).
  QUIZ_SLOT (doosra) = jaancha hua puzzle/GK (puzzles.generate_puzzle); owner ne pehle ek samay badla ho to bhi schedule()
  doosra jodta hai (state quiz_slot_on). Pehla slot = Gemini QUIZ FORMAT (writer.QUIZ_STYLE + JSON 'quiz' -> 4 vikalp,
  jawab vikalp mein na ho to quiz chhod kar aam card). state quiz_all (default chalu).
- YouTube upload ab ~100 unit (4 Dec 2025 se; pehle 1600) - MAX_UPLOADS_DAY 10, quota_status 250/upload maan kar.
- puzzles: MCQ_BANKS pahadi_gk (27 pakke Uttarakhand tathya) + pahadi_shabd (20 Garhwali/Kumaoni shabd); BRAND_KINDS pahadi
  = in dono par; doosre channel par pahadi sawal kabhi nahi; pahadi bank khatam -> Gemini pahadi GK (Google tathya-jaanch).
- design: SAFE ZONE - sab zaroori cheez y<=1470 (neeche ~450px YouTube/IG ka caption/button), vikalp daayein 940 tak
  (like/comment icon), CTA 1290, site ka naam 1400 par kaali patti mein; chitra chhote; pahadi = parvat, boli = bubble.
- website.bing_submit_daily: Bing Webmaster URL Submission API - roz 06:40, quota tak max 10, home + sabse zyada impression
  wale page, ek URL 30 din mein ek baar; INDEXING.md mein 'bing-api roz'. Hukum: 'bing bhejo'. IndexNow pehle jaisa.
- tasks.fix_list_v231 (ek baar): PENDING ke 3 dohre kaam + 2 ho chuke (vm audit file, Workers AI: Read) itihaas mein;
  '<shabd>' wale kaam ko saaf 'ho gaya <shabd>'; @sunonatak warning-review vs monetization-review ka fark likha.
Hataya: kuch nahi.

## v2.3.2 (3 Nov 2026, 5 PM screenshot ke baad) - PRO thumbnail, pura website pata, bank bhi sawal-wala, taazi Gemini seema par bank
- design.full_url: video + thumbnail par PURA pata https://sabhisaab.com/<page> (owner niyam 28 Oct; pehle sirf 'sabhisaab.com').
  46 akshar se lamba ho to https://sabhisaab.com/. Neeche halki brand patti ('<brand> • roz 2 naye sawal') - khaali na lage.
- design.thumbnail v2 (PRO, reference jaisa): neon frame, ek taraf bada chamakta chitra + 5s ring, doosri taraf bada sawal
  (pehli line peeli chamak), 2 vikalp A/B (jawab chhupa), CTA, neeche-kone mein pura pata. 3 variant: rang badle + chitra baayein/daayein.
  Pahad ka chitra ab anupaat mein (barf ki lakeer, suraj baayein - timer se takraav nahi).
- Bank: BANK_MIN 6 (pehle 4), max_new 3; bank ki script bhi QUIZ_STYLE (4 vikalp); pahadi bank = Uttarakhand GK/purane shabd
  vishay (trend nahi). Gemini free seema ~13:30 IST par taazi -> 14:05 par bhi bank bharna (01:00 wala bhi). Spare reel 02:30.
- Studio: 'purana default' ki jagah 'Premium Neon (naya default)'; namoona card mein asli pura pata.
- BUG: '🎨 Naye thumbnail' (pipeline.new_thumbs + studio.new_thumbs) purane thumbs.make se purana design deta tha -> ab neon.
- Thumbnail 3 ALAG layout: 0) chitra + bada sawal + A/B  1) sirf bada sawal + badi chamak '?'  2) bada 5s timer + A/B/C.
  Jawab kabhi thumbnail par nahi; timer ring bada ho to ank bhi bada.
- Sandesh mein '__puzzle__' ki jagah 'sawal-slot: jaancha hua puzzle/GK'.
Raat/taazi-seema par bank: 01:00 + 14:05 (Gemini seema ~13:30 IST taazi) bank scripts sawal-wali + 02:30 spare reel -> slot nahi tootta.
Hataya: kuch nahi.

## v2.3.3 (3 Nov 2026 raat) - sirf SAWAL reel, apna 3D (Blender), owner ke 24 PRO-ELITE look, dimag+pyaar combo, comment jawab
Owner: purani website-wali kahani reel ab bhi aa rahi thi; pata home ka chahiye; screenshot jaisa 3D/attractive; 24 look; dimag +
romantic combo (market trend); namoona button; look chunne ki setting (dohri pushti); comment ka jawab; best samay.
Market (web, Mar 2026): quiz reels (jawab ke liye ant tak dekhte hain = completion) + Bharat mein couple 'micro-drama' tez badh rahe.
- Sirf sawal: prepare - QUIZ FORMAT wali script mein 4 vikalp nahi -> dobara; 3 koshish ke baad jaancha puzzle (purani kahani kabhi nahi).
  writer bank-fallback bhi sirf 'quiz' wali bank script; writer.quiz_fields (Gemini + bank dono). Namoona bhi QUIZ_STYLE.
- topics: QUIZ_TOPICS (har channel 15-17 sawal-vishay, 60 din dohraav nahi) - purane website-page vishay band (state quiz_topics_only).
- design.full_url = hamesha https://sabhisaab.com/ (home).
- 3 TOP FORMAT (weekplan): Dil vs Dimag (couple micro-drama + dimagi sawal), Pyaar ka Hisaab (couple + paisa/bachat sawal),
  Sach ya Jhooth (guess the lie); parivaar ke saath dekhne layak. 4 haath se likhi pakki combo bank script (har channel 1).
- APNA 3D: app/blender3d.py + blender3d_scene.py - Blender (Ubuntu apt, free) Cycles CPU, nice 15, ~1-2 min/chitra; 28 scene
  (couple, dil-dimag tarazu, sikke, pahad, '?', + 24 look: ghadi, tarazu, tijori, shatranj, katore, mahal-oont, matrix, do darwaze,
  laser, parivaar, lift, rubik, surang-train, compass, kuan-mendhak, pul, nadi-naav, sheeshiyan, black hole, mombatti, trikon, crime,
  number grid). Hindi text 3D mein nahi. Raat 03:10 apne aap install (sudo apt, DPkg lock 10 min). Ubuntu build mein OIDN nahi ->
  median filter. design: 3D upar khidki (_panel3d) + peeche dhundhla (blend_3d_bg) + thumbnail. state use_3d (dohri pushti).
- 24 PRO-ELITE look (owner screenshot): puzzles.ELITE24 (har look ki klasik paheli, jawab tark se jaancha) + LOOK24 + looks_for;
  kind 'elite24' (Suno Natak/Money/Deals par zyada; Pahadi par sirf pahadi). Menu '🎨 24 Look' -> channel -> ✅/⬜ chuno ->
  '✅ Pakka karo' (dohri) -> state looks24[brand]; '🎬 Kisi look ka namoona' (asli sawal kharch nahi) -> Agla = agla look.
- Doosra (aakhri) slot = puzzle/24-look slot (owner ne samay badla ho to bhi aakhri slot).
- Main keyboard: 🧪 Namoona, 🎨 24 Look, 💬 Comment haal, ⏰ Best time, 👑 Pro 50 Deck.
- ⏰ Best time: asli views (learn views_hour) + Bharat peak -> har channel 2 samay ka sujhav -> dohri pushti -> state schedule.
- Comment: Facebook page comment padhna + jawab (meta.fb_comments/fb_reply, growth.check_fb_comments); jaanch 2 ghante -> 45 min.
  YouTube: TV login Google se comment-likhne ki ijaazat nahi deta (padhta hai, aapko dikhata hai) - 'comment haal' mein saaf.
- audit: nakli aankda ('90% log', 'votes', 99.9) aur ashleel shabd -> ❌ (monetization suraksha).
Hataya: kuch nahi.

## v2.3.4 (4 Nov 2026 subah) - 3D ki jaanch/marammat, roz alag 3D (channel aapas mein kabhi same nahi), naye default sawal
Owner (4:27 AM): Blender lag gaya par 'Ab tak bane 3D chitra: 0' - namoona bina 3D. Aur: har video ka 3D/thumbnail sawal ke
hisaab se alag; aaj ek channel par jo look gaya wo doosre par nahi; ulte-pulte/ghumaavdaar shabd, purane zamaane ke anokhe
shabd, pahad ke purane naam, shuddh Hindi, sudoku waghera - koi sawal kabhi kisi channel par dobara nahi.
- blender3d: Blender ab saaf mahaul mein (bot ka PYTHONPATH hata kar - Blender ke apne Python se takraav ka shak), 2 tareeke
  (full -> simple: bina compositor/Filmic), har galti state b3d_last_err + '🧊 Apna 3D' mein; '3d jaanch' (chhota render + asli
  galti ki lines), '3d repair karo' (Mesa/EGL library ke saath dobara install); raat 03:10 agar ek bhi 3D nahi bana to khud
  jaanch + repair + aapko khabar.
- 3D scene ab sawal ke hisaab se (sudoku->grid, series->matrix, coding->tijori, calendar/ghadi->ghadi, disha->compass,
  umar->parivaar, purane shabd->sikke, pahad->pahad...); _unique_today: ek din mein do channel par same scene nahi;
  24-look: _looks_today - aaj doosre channel par gaya look is channel par nahi.
- Naye default sawal (puzzles): utpate_shabd (16 ghumaavdaar shabd/muhavre), purane_shabd (12: aana, pai, chavanni, ser, man,
  tola, kos, pahar, ghadi, taar, lalten, athanni), pahadi_purana (10: gharat, bakhli, tibari, hudka, damau, mashakbeen, pichhaura,
  gulobandh, Tehri ki nath, dhara) + ganit se (hamesha sahi jawab): sudoku4 (asli 4x4 jaal video/thumbnail par), series, coding,
  calendar, clock_angle, direction, age. BRAND_KINDS naye default (Pahadi: GK + purane shabd + purane naam).
- Sab channel ka ek sawal-register (q_registry/q_recent): Gemini ka sawal kisi bhi channel par pehle aaya ho to dobara likhwao;
  writer ko pichhle 30 sawal 'mat dohraao' ke saath. Puzzle/bank sawal pehle se global (used_puzzle_hashes).
- QUIZ_TOPICS mein ulte-pulte shabd, purane shabd, shuddh Hindi naam, muhavre, pahad ke purane naam jode.
Hataya: kuch nahi.

## v2.3.5 (4 Nov 2026) - Blender 5 theek, ANANT sawal-bank (bina dohraav), khud seekhne wala chunav
Owner (4:55 AM screenshot): VM par Blender 5.0.1 - '3d jaanch' mein full ❌ (rc 0), simple ✅. Aur: ulte-pulte/purane shabd/pahad ke
purane naam jaise sawal ANANT (kabhi dohraav nahi, kisi channel par nahi), trend dekh kar bank bharta rahe, naye dimag hilane wale
aur 'ego/confusion' wale sawal, sab rotate, khud upgrade.
- 3D: Blender 5 mein scene.node_tree hat gaya tha (wahi 'full' ki galti; Python galti par Blender rc 0 deta hai). Ab compositor
  sirf jahan ho; chamak (bloom) PIL mein - Blender 4/5 dono par ek jaisa; view transform AgX > Filmic > Standard; 'simple' pehle.
- app/qbank.py ANANT BANK: 11 category (ulte-pulte shabd, purane shabd, shuddh Hindi, pahad ke purane naam, pahadi boli, pahadi GK,
  Ego test, Dimag hilao trending, Trending GK [seo trends ke shabd -> pakka purana tathya], paise ka sawal, deal ka ganit).
  Gemini 8 naye likhta -> niyam jaanch (4 alag vikalp, jawab vikalp mein, nakli % nahi) -> dohraav jaanch (used_puzzle_hashes +
  q_registry, sab channel) -> ask_grounded Google se har jawab sahi + ek hi -> tabhi bank (data/qbank.json). Jaanch na ho to kuch
  nahi judta. Roz 01:20 + 14:20 (sabse khaali 6 category). '🏦 Sawal bank' / 'sawal bank bharo'.
- puzzles: static bank khatam -> anant bank; naye kind ego_sawal, dimag_trend, trend_gk, money_quiz, deals_quiz (BRAND_KINDS mein).
- Khud seekhna: learn mein 'pkind' (sawal-category) + 'theme3d'; generate_puzzle category ko asli views ke wazan se chunta hai
  (zyada dekhi gayi = zyada baar, nayi bhi aazmati rehti hai).
- q_registry mein ab har sawal (Gemini + bank + puzzle) - Gemini kabhi puzzle wala sawal bhi nahi dohraata.
Hataya: kuch nahi.

## v2.3.6 (4 Nov 2026) - VM audit (05:32) + screenshot ki galtiyan, sawal-bank bina Google bhi, pahad ke parv, naye rang khud
Owner: 'sawal bank bharo' ke baad 0; 07:20 'daily.py timed out 4200 sec'; event roz nahi; Bing; website traffic 0 dikhta;
FB Business Dashboard (photo post, story, reel); naye 24 look screenshot; bot khud naye design aazmaye (24 ghante auto).
VM audit: Gemini ke saare model cool (free seema) + Google-search wala bhi -> qbank jaanch fail -> 0; calendar find 9 baar fail;
IG ProcessingFailedError 14; sabhinet 13 restart (update ke); UnboundLocalError 'updater' (purane version ka - abhi koi local import
pehle-use nahi, scanner saaf).
- website.daily: report 8 baje tak rukti hai (TG_HOLD_UNTIL) - 06:10 + 70 min par beech mein marta tha; ab timeout = 70 min + ruka samay.
- website.traffic_smart: 'aaj' 0 ho to pichhle 7 din bhi (GA4 24-48 ghante der se ginta hai).
- qbank: Google band ho to 'do-dimaag andha hal' - Cloudflare Workers AI + Gemini (jo chale) bina jawab dekhe hal karein; GK tathya
  par dono ka milna zaroori, baaki par ek; har 3 ghante khaali category khud; galti status mein. Owner ko kuch likhna nahi.
- calendar: offline bana din yaad (cal_offline_days) - har 6 ghante Google mile to dobara pakka; pahadi_small_events: Surya ka rashi
  badalna (Uttarayani, Phooldei, Bikhauti, Harela, Ghee Sankranti, Khatarua), Igas Bagwal (Kartik Shukla Ekadashi), Purnima,
  Amavasya, Ekadashi (offline ganit, 'aage-peeche' note) -> Pahadi par roz chhote-bade parv.
- IG: pehli koshish se hi IG-safe format (H.264 high, 30fps, AAC 48k stereo, faststart).
- FB: roz har page par 1 photo-post (sawal wala thumbnail + 'jawab reel mein' + https://sabhisaab.com/); story card ab neon sawal-design.
- WhatsApp channel ka API nahi -> roz 1 taiyaar post owner ko (forward); FB group API band (2024) -> PENDING mein 'marzi' kaam.
- 7 naye look (owner ka doosra screenshot): shakuni ke paase (7), origami net (11), 2027 ka 1 Jan (shukravaar), parallel 2 ohm (1),
  uttolak (5 kg), jail ki surang (bhookhe sher), A=1 code (HI) - 3D scene jode.
- Rang/design apne aap: design.PALETTES (8) + use_palette; har Ravivaar 11:00 naya rang namoona -> '✅ Default mein jodo' / 24 ghante
  baad apne aap; pakke rang roz baari-baari (channel + din). 'rang list', 'naya rang', 'rang hatao <naam>'.
Bing: INDEXING.md mein 4 Nov 06:40 ko 10 page 'bing-api roz' 200 OK - chal raha hai.
Hataya: kuch nahi.

## v2.3.7 (4 Nov 2026 dopahar) - button audit, sach-bolta bot, roz khud-jaanch, Pinterest traffic, routines
Owner: 10 baar bheja Chowkidar 'Export bada hai ya fail hua' (alag ZIP: Chowkidar v5.2.4); analytics/kuch button; 'kachra saaf'
par AI ne bina kuch kiye 'saaf kar diya' bola; 'total impression/click jod kar' par purana YouTube report; Pinterest ka haal;
fact-checker ne 365 x 50 = 18,250 ko galat kaha; 'reel kab' par AI ka andaaza; spec doc (Elite Pro Upgrade) ke zaroori hisse.
VM audit 11:11: 'updater' UnboundLocal / node_tree / IG ProcessingFailed ki ginti 05:32 jitni hi - yaani naye version mein dobara
nahi hui (purane version ki thi).
- Button audit (nakli VM): 93 button chala kar dekhe - '🧩 Puzzle' KeyError (naye mode ke naam nahi the) theek; baaki sab jawab dete.
- Sach-bolta bot: AI ka jawab 'kar diya/saaf kar/bhej diya' bole par koi kaam na chala ho -> saaf note 'maine kaam chalaya nahi'.
  'kachra/safai' -> ASLI safai (guard + purane 3D); 'total/kul impression/click' -> analytics.totals_text (YouTube views +
  impression + click + Pinterest + website); 'pinterest ... kitne/dekha' -> pinterest.analytics_summary (API).
- Reel kab: schedule_text() (asli schedule + aaj bani/gayi) - AI ke facts mein bhi 'SCHEDULE_TRUTH'.
- 'schedule <channel> HH:MM,HH:MM' (dohri pushti). 'roz HH:MM <koi bhi hukum>' -> routine (dohri pushti), 'routine list/hatao N'.
- audit_ai: tathya-jaanch galat-alarm - ganit khud jaanch (jaanchne wale ka apna gunaa sahi) + doosri raay (Gemini/Cloudflare).
- elite_audit.daily_heal: roz 05:45 khud 6-pass audit -> 3D/sawal-bank/safai khud theek -> sirf zaroori baat alert mein.
- tg.alert: wahi peela/laal alert 3 ghante mein ek baar (ginti saath) - alert spam kam.
- Pinterest drip: 08-22 har 90 min ek website page/tool ka 1000x1500 pin (UTM, ek page 30 din mein ek baar, 15/din seema ke andar).
- brain MODELS fallback: purane 2.5 ki jagah VM par chalne wale 3.5/3.1 (2.5 aakhir mein).
- Comment reply: comment ko 'untrusted data' maana (prompt-injection guard), quiz-jawab par insaan jaisa jawab.
- Naye menu button: 📈 Kul hisaab, 📌 Pinterest haal, 🧹 Kachra saaf, 🗓 Schedule.
Hataya: kuch nahi. Nahi kiya (jaan-boojh kar): Web 2.0 / tier backlink automation (Google link-spam niti - site ko nuksaan),
auto-follow/DM (platform spam niti), Facebook group post (API band).

## v2.4.0 (4 Nov 2026) - jo adhoora/nahi bana tha wo sab (owner: 'kyu chhode, ho sakte the')
- AI-ART bina Gemini: imagegen.cf_image (Cloudflare Workers AI Flux/SDXL, owner ke CF account ki free seema) - Gemini image
  seema khatam -> pehle Cloudflare, phir apna. blender3d.ai_art: har reel ka chitra pehle AI-art (28 scene + 31 look ke prompt,
  'no text/no logo'), na mile to Blender 3D. state use_ai_art. Seema par 3 ghante aaram.
- 12 naye look (doosre screenshot ke baaki): ramayan (Lanka), aladdin (Alif Laila), pahadi_rasta (Gaurikund), titanic (1912),
  mirror_clock (8:45), blackbox (narangi), spinner (360°), lava (Death Valley 56.7°C), swamp (A C F J O U), kitchen (sendha =
  rock salt), balloon (helium), anime (odd prime 9). Kul 43 look.
- Layout bhi khud: design.LAYOUTS list / grid (2x2 vikalp) / big3d (bada chitra); har Budhvaar naya layout namoona ->
  '✅ Default mein jodo' ya 24 ghante baad apne aap; roz baari-baari; 'layout list', 'naya layout', 'layout hatao <naam>'.
- Pinterest: board ke SECTIONS apne aap (Calculators/Quiz/Pahadi) + drip pin A/B title (A=page title, B=hook) -> har Somvaar
  asli pin analytics (impression, website-click) se seekh, jeeta wala 70%.
- app/ops.py: token watcher (Threads 60 din, Pinterest login/refresh, Meta page + data-access, Cloudflare, GitHub) - 7/3/1 din
  alert; roz 06:20 API contract jaanch (YouTube/Meta/Threads/Pinterest/Telegram/Gemini READ-only) = API badlav watcher;
  offsite encrypted backup roz 02:15 (state, learn, diary, qbank, keywords, provenance, secrets -> AES-256 openssl pbkdf2
  200k -> owner ke Telegram, VM par aakhri 7), password secrets/backup_pass (600) - pehli baar ek baar aapko (5 min mein message
  mitta), 'backup password' (1 min), 'backup password badlo <naya>' (dohri pushti); har Ravivaar restore drill;
  provenance ledger (har video: script srot, fact-check, chitra srot, font/TTS/sfx license, AI label) - '📜 Provenance'.
- app/media_tools.py: awaaz se hukum (Telegram voice -> Cloudflare Whisper -> on_text; pushti wale kaam par pushti wahi);
  competitor link + 'apna version' -> sirf title/desc/tags (YouTube API/oEmbed) -> APNA original sawal-reel (copy nahi);
  'har size' -> aakhri video 1:1 + 16:9 (dhundhla peeche).
- Surakshit khud-ilaaj (elite_audit.self_fix): log mein jaani galti -> pakka ilaaj (Gemini model list naya, Pinterest/Threads
  token naya, safai, atke ffmpeg, 3D jaanch). Code khud nahi badalta (galat patch = bot gir sakta) - anjaani galti par khabar.
- Test suite: tests/smoke.py (puzzle jawab+dohraav, har layout + thumbnail, saare menu button, 50 deck, schedule, ganit-jaanch,
  quiz_fields, pahadi parv, provenance). install.sh 1b: naye code ki jaanch INSTALL SE PEHLE - fail = install ruka, purana chalta.
  Isi test ne pakda: har sudoku ka sawal-text aur title ek jaisa tha -> ab pehli pankti + reel code (alag).
- Naye button: 🔑 Token haal, 💾 Backup, 📜 Provenance. Second admin: owner ne mana kiya -> PENDING mein 'marzi'.
Hataya: kuch nahi.

## v2.4.1 (4 Nov 2026 raat) - owner screenshot: galat page link, Threads 'Fatal', shuru mein '5', AI chitra mein likha
- siteknow: google/bing/yandex verification file, 404, bina title/noindex ab 'page' nahi (build + is_content); find() ab ank/chhote
  shabd se milaan nahi karta (pehle '15' googleb9a1fd91a1579ee6 se mil jaata tha -> reel/Pinterest/YouTube par galat link).
  Paheli-reel ka page hamesha home. Pinterest drip + Bing API bhi sirf asli page.
- Threads: container FINISHED hone tak ruko + 3 baar publish; phir bhi 'Fatal' to bina link-card dobara.
- design: pehle (sawal) scene par timer/'5 सेकंड' nahi - timer sirf vikalp aane par.
- AI-art: ank/akshar banane wale prompt hataye (number tiles, sudoku board, percent sign); 'absolutely no text...'; peeche ka AI
  chitra zyada dhundhla (24) + andhera, taaki uske andar ka koi likha (jaise '15. Sha') na padha jaaye.
- Dohraav 365 din, sab channel: duplicate() 90 -> 365 din; q_registry 6000; used_puzzle_hashes kram wali list 6000 (pehle set ka
  aadha kaat-ne se kuch purane sawal 'bhool' jaata tha).
- PENDING: 'Sample Studio look pakka' wala kaam itihaas mein (Premium Neon + AI-art default chal raha).
Hataya: kuch nahi.

## v2.4.2 (5 Nov 2026) - AI chitra mein '5000' jaise ank
Owner namoona (Suno Natak, mobile loan 5000): peeche ke AI chitra mein bada '5000' likha aa gaya - chitra ka prompt sawal ke
shabdon se banta tha (ank + ₹). imagegen.clean_prompt: ank, ₹, %, #, Devanagari ank, lakh/crore hata kar hi prompt (Gemini +
Cloudflare dono); neon design mein scene ke peeche AI chitra dhundhla (22) + andhera, taaki sawal saaf aur chitra ka koi likha na padhe.
Hataya: kuch nahi.

## v2.5.0 (5 Nov 2026) - JAWAB website + Telegram par (reel mein sirf sawal), pehle second mein jawab-leak band
Owner + 'Omnichannel Growth & Compliance Masterplan' (answer free rakho, lock mat karo; curiosity-gap se website/Telegram):
- app/answers.py: strip_reveal - video se jawab wala scene + uske baad sab hata kar aakhri CTA scene 'apna jawab comment karo;
  sahi jawab (kod #N): sabhisaab.com/jawab • t.me/sabhisaab' ('लिंक: डिस्क्रिप्शन / बायो में'). Gemini quiz: pehle 3 scene hi
  (jawab shabdon mein bhi ho sakta tha). Description mein jawab nahi. Video ka pura link: https://sabhisaab.com/jawab.
- Har platform ki pehli line: '✅ सही जवाब (कोड #N): https://sabhisaab.com/jawab#cN | Telegram' (YouTube desc, FB, Threads);
  Instagram: 'बायो के लिंक में'; Pinterest pin ka link seedha jawab#code.
- Upload hote hi (YT/FB/IG mein se koi ek safal): jawab Telegram channel par (sawal, sahi jawab, wajah, video link) + website
  /jawab page 'dirty' -> har 30 min mein publish_site: site ke apne about.html template se (consent, GA, header/footer wahi),
  table + har jawab ka dabba (#c<code>) + 'kaise kaam karta hai' + FAQ (800+ shabd), 3 page (links/about/articles) par ek line
  link (site niyam: 3 inbound) -> site audit pass hone par hi live (local site audit: PASS, 0 error). Owner ki ek baar dohri
  pushti ('jawab website chalu'); Telegram turant. 'jawab haal', 'jawab video mein' / 'jawab website par' (dohri pushti).
- BUG (owner ki video, Labh Lo Deals): pehle scene 'चुनौती: ... सही जवाब बताइए!' ko 'reveal' maan kar PEHLE second mein ₹420 hara
  dikh jaata tha. design.REVEAL_RX: ab sirf 'सही जवाब:'/'सही जवाब है'/'✅' wala hi reveal.
- writer QUIZ_STYLE: quiz JSON mein 'why' (website ke liye wajah); scene 1-3 mein jawab mana.
- 'sab channel ek samay HH:MM,HH:MM' (dohri pushti, fayda/nuksaan saath). Disk GB ab Chowkidar jaise (1000 wale GB: 208).
- PENDING: FB comment permission (pages_read_user_content + pages_manage_engagement), GSC 'Request indexing' 4 page.
- tests/smoke: 'jawab video mein nahi, link har jagah' jaanch.
Hataya: video ka jawab-scene (setting se wapas la sakte hain).

## v2.5.1 (5 Nov 2026) - '/jawab link nahi khul raha'
Wajah: 0 jawab wala /jawab page site audit mein 775 shabd (800 zaroori) par ruk jaata tha -> live hi nahi hua -> reel/description
ka link 404. Ab: page mein 'paheli jaldi hal karne ke 5 tareeke' (khaali page bhi 941 shabd, local site audit PASS);
answers.live() - page sach mein 200 deta hai tabhi video/description/Pinterest/Telegram button mein /jawab link, warna Telegram
(t.me/sabhisaab) + home; bot har 20 min jaanchta hai, live hote hi khabar ('ab LIVE hai'); baad mein band hua to wapas Telegram.
Hataya: kuch nahi.


## v2.5.2 (5 Nov 2026) - /jawab audit fix + AdSense taiyari
Source: Sabhisaab_Pro_Audit_Developer_Handover.docx (5 Nov). Har baat pehle ZIP ke code se verify ki; jo verify nahi hui wo neeche "baaki".

### Kiya (verify karke)
- B-01 answers.publish_site: apply_zip(force=False) - audit asli gate. Fail par page repo mein nahi, `jawab_last_error` + Telegram par poora error. Success sirf "✅" par.
- B-02 website.deploy_direct: audit fail ho aur ERROR sirf bot ke page (site/jawab.html) ki ho to wo file data/quarantine mein, repo se commit karke hatayi, page dobara banne ko answer_dirty; baaki site deploy hoti hai. Doosre page ki galti ho to kuch nahi hatata.
- B-03 answers.build_page: saare re.sub ke replacement lambda mein (original par "bad escape" reproduce hua). tests/test_answers.py mein 9 kharab-text case.
- B-04 Reel code takraav: puzzles._unique_reel_code (4 ank, pehle se use hue code kabhi nahi); answers.record overwrite band (wahi code alag sawal = dono rakhe, anchor c<code>-2); _strip_code aur design.py ke regex 3 se 6 ank. Audit ka "YYMMDD+brand" format NAHI liya: screen par bahut lamba aur 5 jagah code regex badalna padta; 4 ank + "koi code dohra nahi" wahi maqsad poora karta hai.
- B-05 answers.reconcile(): repo mein jawab.html na ho/kharab ho to jawab_hash saaf + answer_dirty. Install ke baad ek baar + live-check mein.
- B-06 answers.check_live: status + html + asli marker + "Page nahi mila" nahi, cache-bust, 1 baar dobara koshish; chalte hue 1 ghanta, nahi chalte 20 min; live se not-live par Telegram alert; repo mein page theek par live nahi to 6 ghante mein ek baar deploy dobara.
- B-07 install.sh: bot ke roz likhe docs ZIP ki purani copy se nahi badalte; test_answers install se pehle chalta hai. (Audit ne likha tests/ ZIP mein nahi - ZIP mein tests/smoke.py maujood tha; ab test_answers.py bhi.)
- B-09 /jawab sitemap.xml mein (daily, sirf ek baar), homepage + 3 page mein link (homepage ka badlaav audit mein atka to sirf baaki).
- B-11 /jawab par "shak ho to sawal hata diya jaata hai / do alag jaanch" wala daava narm kiya (code mein aisa har sawal ka verified_by record nahi tha).
- S1 Answer Hub: har jawab ke neeche 2-3 free tool (slug live homepage se verify), neeche popular tools/category block.
- S12 canary.py: deploy ke baad /, /jawab, /privacy, /terms, /contact, galat URL par 404, sitemap mein /jawab, h1=1, zaroori pages par adsbygoogle nahi. Command 'canary'.
- S5/W-01..W-05 adsense.py: 'adsense haal' (live jaanch), 'adsense id pub-...' (dohri pushti -> site/ads.txt, audit gate).
- R-07 audit.py: money brand par SEBI jokhim phrase (guaranteed return, pakka munafa, buy karo, target price...) milne par video ruke.
- Naye owner kaam tasks.SEED_V252.

### Baaki (jaan-boojh kar nahi kiya)
- Telegram roz ka digest, per-platform alag creative, quality-governor (n-gram), policy-diff watcher, UTM/GA4 events, platform auto-pause, uptime ping: alag release (owner ki dohri pushti + asli data chahiye).
- privacy.html / sw.js / 404.html / audit.py / sitemap generator ZIP mein nahi - unhe nahi chhua. Privacy ki 2 line (IG "LINK", "abhi koi vigyapan nahi") owner-kaam hain.
- Pinned comment bot, link_for freeze: jaan-boojh kar nahi - description mein link ka haal upload ke waqt ka live() hi sahi hai (live se not-live par video ka purana link 404 nahi deta).


## v2.5.3 (5 Nov 2026) - FINAL Pro Plan ka bot-wala hissa (privacy/policy ke andar)
Source: SabHisaab_FINAL_Pro_Plan.docx. GitHub repo (mkpandey1989-hue/sabhisaab-network) sirf v2.0.6 par hai (1 commit) - base ye ZIP (v2.5.2 + ye).
### Kiya
- T1/T6/B10 Telegram digest: 'jawab digest chalu' (dohri pushti), roz 20:30 IST ek message + website button. Default BAND (purana raasta).
- T3/UTM: har jawab-link par utm_source=<platform>&utm_medium=answer&utm_campaign=<brand>&utm_content=c<code>. Instagram par kabhi nahi. Pinterest link par bhi utm_content.
- T4: YouTube top-comment mein jawab-link (website live ho to; warna Telegram). Description ki purani "sahi jawab" line website live hone par raat 23:30 par badalti hai (roz max 8 video, sirf wahi line).
- W4/T1: /jawab par 'Hamare channel' (YouTube x4, Telegram, WhatsApp, Pinterest) + har jawab ke neeche WhatsApp-share (sirf link, koi data nahi).
- B1/B2/B8/W1/W5: sitescan.py - 'site scan' + Ravivaar 22:00: toote related-link, patle page, 'Aakhri update' nahi, zaroori page par ad. SIRF padhta hai; docs/SITESCAN.md.
- B19: canary.uptime_tick - 10 min, lagaataar 2 baar kharab par ek alert, theek par ek sandesh.
- B5: 'ypp haal' - subs + 1 Feb 2027 deadline countdown (watch hours Studio mein hi; TV-login se analytics nahi).
- B21: roz 21:00 Instagram Story link-sticker reminder (sirf owner ko, aaj ke jawab ke link).
- 22 naye pending kaam (tasks.SEED_V253) - developer P0/P1/P2 + owner.
### Jaan-boojh kar nahi (policy / data ke bina)
- Platform policy-hash watcher, quality governor, Telegram opt-in bot, weekly quiz, schema/share-card generator, Hindi/English draft, web push, hub video pipeline: har ek mein owner ki pushti/naya data/privacy-page badlav chahiye - PENDING mein.
- Site files (privacy.html, templates, sitemap generator) ZIP mein nahi - bot unhe nahi chhuta; docs/PRIVACY_PATCH.md developer ke liye.
- B18 invalid-click shield: AdSense chalne ke baad.

## v2.5.4 (5 Nov 2026) - namoona video par Download button
- Sample/namoona video (studio.send) ke neeche SIRF ek button: "⬇️ Download (original file)". Dabane par wahi video original file (document) ki tarah aati hai (compress nahi, 49 MB tak). Baaki buttons/messages jaise the waise.
- Sirf isi namoone ki mp4, bot ke folder ke andar se; kuch post/upload nahi. 'Namoona mita do' par ye copy bhi mit jaati hai.
- Asli video approval message (pipeline._send_for_approval) ko nahi chhua.

## v2.5.5 (5 Nov 2026) - full automatic nigrani (watchdog)
- watchdog.py: har 30 min state padhta hai; dikkat par STEP-WISE sandesh (jawab page 2 ghante se band, publish 12 ghante se atka, website down, toote related-link). Ek dikkat = ek sandesh/24 ghante; theek hone par "✅ Theek ho gaya".
- Roz ek baar network jaanch: ad code approval se pehle, AdSense chalu par privacy mein 'koi vigyapan nahi', privacy mein Instagram 'LINK' wali line.
- Ravivaar 19:00 'ypp haal', Somvaar 10:00 'adsense haal' apne aap.
- Telegram digest ka ek-tap prastav (max 2 baar, 7 din ke gap par). Chalu karna phir bhi owner ke tap se (purana niyam).
- 'features' command + docs/FEATURES.md. 9 naye pending (agli release ke kaam).
- Watchdog sirf padhta aur batata hai - website/channel/settings kuch nahi badalta.

## v2.5.6 (5 Nov 2026) - purani reels ka jawab website par bana rahe
Live export (export_sabhisaab-network_20261105_2120) padhkar: live = v2.5.5 (sirf bot ke likhe docs aur runtime bank alag). Isliye ye ZIP live code ke upar sirf answers.py + tasks.py + docs.
- Pehle: /jawab par sirf 150 jawab (~19 din) - uske baad purani reel ka #cCODE link page ke upar utarta, jawab nahi milta. Ab: 150 poore dabbe + 1,050 purane "Purane jawab" list mein (har code ka anchor), kul 1,200 tak (state.json mein ~360 KB).
- Har poore dabbe mein "Agla jawab ↓", upar "Channel ke hisaab se dekhein" (in-page, naye page nahi) - page par rukne ka samay badhane ke liye.
- FAQ text sach ke hisaab se badla. 4 naye pending kaam (SEED_V256).
- Jaan-boojh kar nahi: purane 3-ank reel_codes ka import (code takraav se galat jawab ka khatra), channel/mahina-wise alag page (duplicate content ka khatra).

## v2.5.7 (5 Nov 2026) - comment, privacy, policy
Source: live export (v2.5.5 = installed), SabHisaab_Jawab_Video_Final_Plan.docx.
- COMMENT KYUN NAHI HO RAHA THA: YouTube ka upload (TV/device) login Google se youtube.force-ssl nahi deta -> reply/pehla comment 403 (state yt_reply_noscope/yt_comment_noscope); Facebook comment padhne ki ijaazat (pages_read_user_content) Meta app mein baaki (owner kaam); Instagram ke jawab chalte hain.
  Fix: ytcomment.py - alag comment-login (yc_<brand>.json, wahi Desktop client jo /analytics mein hai). 'yt comment login' -> har channel ka link -> address paste. Upload token KABHI nahi badalta; flag ab brand-wise (jis brand ka comment-login hai wo khulta hai). Watchdog har hafte step-wise yaad dilata hai.
- privacy_patch.py + 'privacy ig theek': VM repo ki privacy.html se SIRF Instagram 'LINK' private-reply wali line + ek chhota UTM/share vaada, purani/nayi line dikhakar ✅✅ ke baad, audit gate ke saath. Baaki page nahi chhua. Line na mile to kuch nahi.
- Telegram native quiz poll (flag answer_poll, 'jawab poll chalu', ek-tap prastav, roz max 2; sawal<=300, option<=100, explanation<=200; fail par text post).
- /jawab coverage check (har 6 ghante, live page mein naye 25 jawab ke dabbe; gayab to page dobara + 2 baar par alert).
- ypp haal: /analytics login wale brand ka asli watch hours (365 din) + Shorts views (90 din) (pehle kaha tha analytics nahi - galat tha; analytics.py maujood hai).
- Policy: puzzle naam '1% Genius' hataya; audit mein nakli daava ('1% Genius', IQ certificate, jail/muawza hook, IAS interview) video roke. Plan ki 'NAHI KARNA' list AI_START mein.
- 13 naye pending kaam (SEED_V257): owner (comment login, privacy, poll, analytics), developer (/jawab UI, privacy browser line, hub), bot agli (video V1-V10, asli % engine, Web Stories, retention learner, IG private reply 28 Nov ke baad).

## v2.6.0 (9 Nov 2026) - Claude ka poora audit: policy, website, Bing, Telegram, /jawab (W7 ke saath)
Kuch hataya nahi. Poora haal: docs/AUDIT_9NOV2026.md.
- Instagram DM default band (privacy sec. 8); AI ko commenter ka naam nahi; ntfy par comment nahi.
- FB comment ijaazat (#10): brand-wise 24 ghante rok + ek alert; naye token par khud chalu.
- tg.video: 45 MB se badi video ka preview; aakaar asli video se.
- Bing Webmaster API: priority kram, roz max 30 (quota/3), GetUrlInfo se crawl-nahi page pehle. IndexNow niyam waisa hi.
- sitescan.link_kind (asli galat link) + autofix ('link theek', Ravivaar apne aap, audit gate). Watchdog ka sandesh badla.
- website.traffic_smart: hamare link se (kal pakka + 7 din, platform/brand/code) + Shorts link ki sachai. kb tool bhi yahi.
- /jawab: answers.jawab_table (saare 1,200, khoj, channel button, CSS head mein); sitemap /jawab lastmod roz sach.
- Pinterest roz-seema = ⏸; qbank._items (list bug). tasks: SEED_V260 + fix_list_v260, checker w7 + fb_perm.
- tests/smoke.py + tests/test_answers.py naye (install se pehle chalte hain).
- Website W7 (alag ZIP): 10 galat + 3 khud-link, privacy/terms sach, EMI/GB-TB/mutthi tables, 4 page ki sitemap lastmod.

## v2.6.1 (9 Nov 2026) - Phase 2: sarkari-dar watcher, policy/API watcher, keyword auto-FAQ (v2.6.0 sab shamil)
Kuch hataya nahi. v2.6.0 ki ZIP lagi ho ya nahi - sirf v2.6.1 lagao (purani ZIP kabhi nahi).
- factwatch.py: PPF/NSC/SSY/SCSS/KVP/POMIS/EPF. Google-search Gemini (sirf gov.in/nic.in/rbi srot) + sarkari page khud khol kar
  pakka + 6+ ghante baad dobara wahi number = tabhi badlaav. Sirf calculator default (tools.js + page input + label) aur scheme page par
  bot ka 'Taaza dar' dabba. Lekh ke udaharan/table nahi (unka ganit purani dar par) - PENDING mein Claude ke liye. 1.5% se bada jhatka =
  shak, owner alert. Teen-mahine ke din (25 Mar-7 Apr, 25 Jun-7 Jul, 25 Sep-7 Oct, 25 Dec-7 Jan) roz, baaki Somvaar, 10:20.
  Commands: 'sarkari dar', 'dar jaancho'. Pehle se jaana hua: EPF default 8.15 aur VPF 8.25 alag - watcher pakke srot se theek karega.
- policywatch.py: 18 asli page (policy + API changelog), har 3 din 03:30, vaakya-hash diff (tareekh/mahine ka shor hata), naye vaakya ->
  Gemini asar (none/low/high). Alert + PENDING ('[API naya]' / '[Policy]'). Pehli baar sirf aadhaar. Commands: 'policy haal', 'policy jaancho'.
  Purana growth.policy_watch (news headline) bhi chalta rahega.
- kwfix.py: GSC shabd (position <=30) par SIRF pakka-ganit FAQ (personal loan EMI, KB/MB/GB/TB, mutthi/nali, roman) usi page par, roz max
  2 page, milta-julta sawal ho to nahi (audit 0.85, hum 0.75), FAQPage schema ke saath, audit gate. 07:40. Command: 'keyword sudhaar'.
- kb tools: pinterest <days>, rates, policy. kb.md mein naye kaam + Instagram DM band ki sachai.
- tasks.add() (module khud kaam jode, dohraav nahi), fix_list_v261 (bane hue 'Bot agli' kaam itihaas mein).
- tests/smoke.py: 13 naye test (dar, policy diff, keyword FAQ). Sab mock/offline; sabhi PASS.

## v2.6.2 (9 Nov 2026) - website-channel loop, AdSense site-jodna, list safai (W8 ke saath)
- answers.jawab_json(): /jawab.json (sabse naye 5 SAWAL + code + channel; jawab nahi). W8 ka install-app.js v5 isse homepage
  ('🧩 Aaj ke sawal', 3 sawal) aur har tool/guide page ke neeche 'Aaj ka sawal' dabba + Telegram/WhatsApp dikhata hai.
  Niyam/parichay page (privacy, terms, about, contact, author, links, jawab) par nahi.
- _inbound_links: homepage mein <main> nahi tha - isliye homepage par /jawab ka link kabhi nahi juda. Ab 'Naye lekh' se pehle.
- _sitemap_with_jawab: /jawab A-Z jagah par (audit warning khatam). W8 sitemap A-Z.
- adsense: 'adsense id pub-...' ab ads.txt + homepage <meta name="google-adsense-account"> (Google ke 'Meta tag'/'Ads.txt'
  site-connect tareeke; koi ad nahi dikhta). Isliye apply ke samay hi chalega, approval ka intezaar nahi.
- sitescan: 'Update: <time>' bhi tareekh gini jaati hai - pehle 176 page galat 'tareekh nahi' gine jaate the; asal mein sirf
  homepage bina tareekh (zaroori nahi). add_review_line/review_daily bane (page ki apni dateModified hi dikhate; abhi zaroorat nahi).
- tasks.fix_list_v262: ho chuke/dohre kaam itihaas mein (W4, W6, canary, adsense haal, GA API, D15, D6, W5, D5, dohra FB comment,
  dohra GSC 4 page); W4-dev par checker w8; naye kaam W8 ZIP + AdSense site jodna (16 Nov). QUERIES ke 4 purane 'khule' band.
- website.traffic: ga_data_ok flag (pending 'ga4' khud band).
- (v2.6.2 aage) /jawab: har dabbe mein '✅ Mera jawab sahi tha / ❌ Galat tha' + upar streak (localStorage sh_jawab_streak, sirf browser;
  privacy W8 mein likha). Jawab kabhi lock nahi.
- W8 mein: income tax ke 4 jagah (tools.js 2, income-tax, tax-regime-compare, old-vs-new) Section 87A MARGINAL RELIEF ki galti theek
  (13 lakh salary par pehle ~Rs 66,300 dikhta tha, sahi Rs 26,000). FY 2026-27 slab Budget 2026 mein nahi badle - pakka kiya.
  tax-regime-compare ab 'Salary-wise Tax Table' (6-30 lakh, New/Old + kitni deduction par Old sasta) - teen page ka takraav khatam.
  about#editorial-niti (sarkari dar, AI ka sach, sudhaar/tareekh niti).

## v2.6.3 + W9 (10 Nov 2026) - jhoothe alarm, tax ka naya Act, ruki video dheere, /jawab table pakki
- bot.reopen_jobs: naya token aate hi pehle ~30 ruki post 2 minute mein FB/IG/Threads par chali gayi thi (9 Nov 16:58) - spam jaisa.
  Ab har ek 20 min ke farak par, aur 3 din se purani dobara nahi (old_skip). Saari 'need_login/partial' wapsi isi ek function se.
- /jawab table: site ke global CSS 'table{display:block}' se column tedhe ho sakte the - table.jw ab hamesha asli table
  (Chromium mein naapa: header aur har line ke column ek hi x par, mobile 390px aur desktop dono). 'Kram' (serial) column joda.
- factwatch.mark_reviewed: sarkari srot se dar wahi mili = us scheme ke page 'jaanche gaye' (website repo state/review_ok.json);
  install ke baad pehli jaanch turant (fact_ran_once).
- W9: scripts/watch.py v11 - (1) sirf <a> link jaanche (preconnect fonts.googleapis.com ka khaali root 404 = jhootha alarm tha),
  (2) RBI par sirf neeti dar (repo/SDF/MSF/bank rate/CRR/SLR) - homepage ke roz badalte % se jhootha alarm tha, (3) 90-din review =
  page ki dateModified ya bot ki pakki jaanch (jo naya). 13 tax page par 'naya Income-tax Act 2025' (1 Apr 2026 se; dar/slab nahi badle,
  section number badle) - har page ki apni line. TDS calculator: 194H commission 5% -> 2% (1 Oct 2024 se; tools.js + page).
  Mahila Samman: naya khaata 31 Mar 2025 se band (DoP SB Order 03/2025) - page par saaf, FAQ/description theek.

## v2.6.4 (10 Nov 2026) - pending list saaf: sirf owner ke asli kaam number ke saath
- tasks.is_claude(): '[Bot agli]/[Developer]/[Claude]/[P2]/[API naya]' wale kaam Telegram 'Pending' aur docs/PENDING.md mein alag
  section 'Claude/developer ke kaam' (owner ko kuch nahi karna). Number ('ho gaya 3') sirf owner ke kaam par.
- fix_list_v264: 9 jaankari/dohre kaam itihaas mein (GitHub update, GA4 UTM, YPP seema, purani reel, prastav, dohra hub video,
  second admin, schema injector, /jawab khoj). 'yt comment login' par checker ytc (sab channel ka comment-login = khud band).

## v2.7.0 (10 Nov 2026) - hub video = website traffic ka asli raasta (docs/WORKPLAN.md mein poori list)
- hubvideo.py: 'hafte ki lambi video' ab 'is hafte ke 8-12 sawal' - usi brand ke pichhle 14 din ke JAANCHE HUE jawab (answer_key),
  har sawal: sawal -> 5 sec sochiye -> jawab + wajah. 6 se kam sawal = purana tareeka (writer/bank).
- render.py: meta.scene_starts (har scene ka asli shuru samay). audit.description: lambi video mein ASLI chapters (0:00 se,
  3+, har 10s+) aur utm_medium=long. Description mein har sawal ka clickable link /jawab#cCODE (lambi video ke link click hote hain).
- bot: har brand ki har hafte apni hub (Som Pahadi, Budh Money, Shukra Deals, Ravi Suno Natak, 01:30) - pehle 4 hafte mein ek baar.
  Upload ke baad hub_videos apne aap set (Shorts ka 'Related video' owner Studio mein ek baar chune - API nahi deta).

## v2.7.1 (10 Nov 2026) - sawal puchhne ka tareeka + backup password reset
- hooks.py: owner ke Level 1-5 / 6-andaaz blueprint se 8 andaaz (seedha, samay, ulta 'jawab X nahi', bahas Rahul vs Amit, team A vs B,
  pehchaan topper/jaldbaaz, shart pehli baar, jasoos). X hamesha galat vikalp (sahi ke sabse paas wala = jaldbazi ka jaal). Nakli
  aankda ('99% fail') KABHI nahi - policy. Har reel par ek, ek brand par lagataar wahi nahi. 'hook haal', 'hook rotate', 'hook <naam>'.
  pipeline: strip_reveal se pehle lagta hai; thumbnail tag = andaaz ka naam.
- ops.reset_password: 'backup password reset' -> ✅✅ -> padhne-layak password (4 shabd + 4 ank) + turant naya backup; message 15 min
  mein mitega; '✅ Maine save kar liya' tak roz 10:05 par yaad; PENDING checker bkpass.

## v2.7.2 (10 Nov 2026) - spelling galti + Channel setup (line-wise, channel-wise FINAL)
- hooks.match: 'bahes'->'bahas', 'roteta'->'rotate', alias (debate/timer/story...). bot.fuzzy_command: 38 chhote command ki 2-3
  akshar ki galti ('comment hal' -> 'comment haal') - bot batata hai 'maine X samjha'. brain prompt: owner ki Hinglish spelling
  galtiyon se matlab samjho, kabhi 'samajh nahi aaya' sirf spelling par nahi.
- setupwiz.py + '⚙️ Channel setup' button: channel chuno -> 1) Look (Studio namoona/agla/pakka) 2) Sawal ka tareeka (usi channel ke
  asli sawal par 8 andaaz line-wise; ek chuno ya rotate - hook_mode_brand) 3) Rang/layout 4) Samay/best time -> '✅ FINAL'
  (setup_final). 'hook <naam>' ab sab channel par (channel-wise wizard se).

## v2.7.3 (10 Nov 2026) - hafte-war sawal schedule (default) + video sudhaar (owner ki 34.8s reel dekh kar)
- qplan.py: PLAN[brand][din] = (pehla slot, doosra slot) sawal-type. Pahadi = GK/boli/purane naam; baaki 3 = ego, dimag, ganit, series,
  coding, ghadi, disha, umar, discount-ganit, trend GK. SIP/FD/RD/loan-app/PPF/bima/share BLOCK (BLOCK_RX) 3 aam channel par.
  pattern(): ank hata kar saancha - 4 din tak kisi channel par wahi saancha nahi. Dono slot ab jaancha-hua sawal (Gemini topic-reel
  nahi). Plan ka type na mile -> wahi type dobara -> 'auto' x3 -> purana; schedule kabhi nahi tootta. 'sawal schedule', 'sawal plan
  band/chalu', 'bank safai' (roz 03:10 apne aap).
- Video (owner ki reel: 8 sec tak sirf sawal, 'sochiye' scene par vikalp gayab, aakhri ~10 sec khaali, 'रोज़ की कहानी' label, beech
  mein do text ek saath dhundhle): design.body_frame - sawal + 4 vikalp PEHLE second se poori reel; pehle scene par hook line
  (Rahul vs Amit...), timer doosre scene se; 'सवाल-जवाब' label; lambi line chhoti font. strip_reveal: CTA bolna ~3 sec;
  '(संकेत: ...)' hataya. render: neon mein crossfade 0.15s. Sandbox mein frame bana kar dekha (Noto font ke saath).

## v2.7.4 (10 Nov 2026) - lambi video ki galti, searchable hub, sawal zindagi bhar ek baar, PLAYBOOK
- Lambi video: 7 Nov ko Pahadi lambi video 'ffmpeg:' (khaali galti) par ruki; Money wali SEBI disclaimer par rooki (sahi). Ab
  render fail -> photo/3D/clip ke bina saada render dobara (pipeline). ffmpeg galti khaali ho to exit code/OOM ka ishara.
  Hub video ab jaanche hue quiz sawal se hai - SEBI wala jokhim nahi.
- hubvideo.SEO: har brand ke 3 searchable title (har hafte alag), thumbnail lines (bada number + 'जवाब सहित'), tags.
- pipeline.q_lifetime.json: har sawal ka hash ZINDAGI BHAR (pehli baar ab tak ke register + /jawab se bhara); q_seen pehle yahi
  dekhta hai; qplan loop bhi. used_puzzle_hashes 20,000.
- docs/PLAYBOOK.md: content/hook/look/hub/traffic/kabhi-nahi - doosra AI isi se kaam kare.

## v2.7.5 (10 Nov 2026) - jo look/andaaz zyada dekha jaaye wo apne aap zyada chale + 2 naye card layout
- learn.choose(feature, options, seed, avoid): har naya vikalp pehle 3 video mein aazmaya (MIN_TRIES), phir asli views ke ausat se
  wazan (0.3x-3x), 25% khoj (trend badle to naya jeet sake), pichhla dobara nahi. Video ka rang (vpal), layout (vlay), sawal ka
  andaaz (hstyle) isi se. upload par learn mein vpal/vlay/hstyle/look24 bhi darj. 'look haal' / 'kya chal raha' = jeet ki report.
- design: owner ki 24 card-model photo se 2 naye layout - 'neon4' (har vikalp ka apna neon rang 2x2 + seedhi timer patti) aur
  'bar' (rangin line vikalp + timer patti). studio.propose_layout inhe apne aap namoona banakar deta hai -> haan ya 24 ghante baad
  default list mein -> phir views ke hisaab se rotate. Frame sandbox mein bana kar dekhe.

## v2.7.6 (10 Nov 2026) - light/comic card, 50-50, purana layout-bug, namoona = asli maal
- BUG (purana): render pehle scene-frame banata tha, layout/rang baad mein lagata tha -> har video PICHHLI video ka layout/rang
  leti thi (restart ke baad 'list'). Ab design.body_frame khud script ka layout + rang lagata hai.
- 2 naye card (owner ki photo): 'light3' (safed '5 SEC TEST' card, gehre akshar, rangin vikalp) aur 'versus' (neela-narangi comic,
  peeli bijli, 'TEAM A vs TEAM B' jab hook team/bahas). Background bhi alag (_bg_light/_bg_versus); 3D andhera inpar nahi.
- V3 50-50: aakhri 'sochiye' scene par 2 GALAT vikalp kat-te hain (jaldbazi wala jaal dikhta rehta hai); sahi KABHI nahi - code aur
  design dono jaanchte hain; test 40 sawal par. 'fifty_on' state (default chalu).
- Namoona (Channel setup / Studio): ab aaj ke plan ka asli jaancha sawal + hook (sawal-yaad kharch nahi hoti).

## v2.7.7 (10 Nov 2026) - doosre AI ke sujhaav ka audit + har video ka apna pehla comment
- docs/IDEAS_AUDIT.md: Gemini ke 4 doc ke ~45 idea - ⛔ stealth/hash-badlo/hydra/key-pool/search-hijack/high-CPC inject/DM/exit-popup/
  unlock/fake coupon; ✅ jo pehle se hai; 🟢 jo lena hai (A/B thumbnail, retention-drop sfx, score card, web push...).
- pipeline.comment_opener: pehla YouTube comment ab video ke sawal se juda ('Aapka jawab A, B, C ya D?', bahas/team par 'kiske saath',
  hub par 'kitne sahi') + jawab link - har video ka alag, jawab kabhi nahi.

## v2.8.0 (10 Nov 2026) - asli % engine, tap-karke-socho, zindagi bhar jawab, viral paheli, 30 din chat
- votes.py: Cloudflare Worker 'sabhisaab-votes' + KV (relay jaisa, owner ke maujooda token se). POST /v?c=CODE&o=0-3 sirf sabhisaab.com
  Origin se; GET /p sirf 30+ vote wale code. Koi IP/naam/cookie nahi. setup(): worker -> site _headers CSP connect-src (audit gate)
  -> votes_on. Apne aap roz 11:30 (jab tak ban na jaaye); 'vote chalu' / 'vote band'. Node mein worker test (evil origin, galat code).
- /jawab: 150 naye sawal par A/B/C/D tap (pehle socho; jawab neeche - kabhi lock nahi), sahi hara/galat laal, streak, vote ginti,
  '📊 Ab tak N logon ne chuna: A x% ...' (30+), '📤 Score card' (browser mein 1080x1080, Web Share ya download).
- Zindagi bhar ka jawab-register: data/jawab_archive.jsonl (kabhi nahi mitta; pehli baar /jawab ke 1200 se bhara) -> site/
  jawab-archive.json + jawab-archive-<saal>.json; /jawab ki khoj table mein na mile to register mein dhoondhti hai.
- puzzles: owner ki FB photo wale 3 naye compute-paheli - missing_digit ('9 ? 5 - 682 = 293'), magic_square (3x3 jod 15/18/21,
  jaal dikhta hai), pick_sum (1-9 mein se 4 ank = N; ek hi sahi vikalp); series mein 'inc' (2,6,12,20,30). 360 bana kar jaancha.
  Grid jaal 3x3 bhi. qplan mein jode; money se money_quiz (SIP/FD) hataya.
- updater.chat_md: 30 din (pehle 15 aur 15 se purana mit jaata tha), bot ki report 1500 akshar tak; backup password + 'password:' ke
  baad ka shabd bhi chhupta hai (token pehle se).
- Website W10: privacy - vote ginti (koi data nahi), score card, jawab-register.

## v2.8.1 (10 Nov 2026) - sawal-type views ke hisaab se, tyohaar spam band, purani 105 ginti
- qplan.weekly_adapt (Ravivaar 23:10): learn ke asli views (views_pkind, 3+ video) se har brand ka sabse kamzor type (median ka
  60% se kam) -> sabse tagda bahar wala (120%+) ya ek naya aazmane ko. Hafte mein max 1 per brand, sirf DEFAULT plan par
  (owner ka 'qplan_custom' kabhi nahi), money_quiz kabhi nahi, pahadi par sirf pahadi type. 'sawal plan reset' = wapas.
- calendar_in.post_today: 10 Nov ko 3 tyohaar x 4 channel = 12 story 4 min mein gayi (kal ki Kartik Amavasya bhi). Ab din mein EK
  (bada pehle); kal ka 'bhed' wala sirf tab jab aaj ka apna din na ho.
- Watchdog '105 galat link' purane (v2.6.0 se pehle) scanner ki ginti thi; ab sitescan_last.v=260 ke bina alert nahi, aur bot
  04:30 par naye scanner se taaza scan + autofix khud chalata hai.

## v2.8.2 (10 Nov 2026) - tyohaar 2+ website se pakka + tithi ka samay, chat audit ke sudhaar
- calendar_in.VERIFY: Gemini (Google search) ko 3+ ALAG panchang/calendar site (drikpanchang, prokerala, astrosage, mpanchang,
  timeanddate, sarkari suchi) ka har ek ka din + tithi ka shuru/khatam samay. agreement(): kam se kam 2 alag domain isi din ko
  maanein tabhi post; kuch doosre din ko maanein to text mein saaf 'kuch panchang ke anusaar aaj, kuch ke anusaar kal' + ilaaka.
  timing_line(): 'अमावस्या: 8 नवंबर सुबह 11:20 से 9 नवंबर सुबह 10:03 तक' story/post aur subah ki report mein; 'Pakka kiya:' site.
- Chat audit: 'ho gaya fb starts / labhlodeals riview / GSC wakah' nahi mile the -> tasks.suggest (kaam + uske 'how' mein
  fuzzy milan) -> button se pushti. 'sabka lagakar kitna traffic' par sirf 'aaj 1 log' aaya tha -> traffic report mein hamesha
  '7 din ka kul' upar; link_traffic ka GA4 dimension na chale to uske bina (khaali jawab nahi).

## v2.9.0 (10 Nov 2026) - karaoke subtitle (V4), tyohaar ke din sawal bhi usi vishay par
- karaoke.py: bola ja raha shabd peela (baaki safed), 5-5 shabd ki patti, kaali paardarshi pill, y=1462 (site-patti aur brand-naam
  ke beech, YouTube ke neeche wale buttons se upar). Samay = us scene ki ASLI awaaz ki lambai, akshar ke hisaab se baanta. Link/
  hashtag nahi. 10 fps PNG sequence -> joined par ek overlay (render). Fail = bina subtitle (video kabhi nahi rukti).
  state karaoke_on (default chalu). Sandbox mein asli ffmpeg overlay chala kar frame dekhe.
- V5 moving background pehle se (neon parat par dheema zoompan 4-6%) - alag kaam nahi.
- pipeline scheduler: jis din calendar ne (2+ website se) tyohaar pakka karke 'plan' mein vishay rakha, us din brand ka PEHLA slot
  usi vishay ka quiz (block vishay nahi); doosra slot hafte-war plan se. Pehle qplan ke baad ye plan chhoot raha tha.

## v2.9.1 (10 Nov 2026) - FINAL batch: Web Stories, A/B thumbnail, roz tool-pin, comment se idea, sitemap kai-line
- webstory.py: har brand hafte mein 1 Google Web Story (Mangal Pahadi, Guru Money, Shani Deals, Ravi Suno Natak 12:15) - is hafte ke
  5 jaanche sawal: cover, sawal+vikalp -> jawab+wajah (outlink /jawab#cCODE), aakhri page. AMP boilerplate, poster 640x853 (apna),
  logo icon-192. /stories/* ka alag CSP (! Content-Security-Policy + cdn.ampproject.org) bot khud _headers mein. Sitemap mein.
  'story banao <brand>'. Site audit (stories subfolder) 0 error.
- abtest.py: sirf LAMBI video (Shorts feed mein custom thumbnail nahi dikhta). Upload par baaki thumbnail DATA/ab mein; 3-10 din baad
  (Reporting API 1-2 din der) agar 300+ impression aur CTR < brand median ka 70% -> doosra thumbnail (thumbnails.set), ek hi baar.
  '/analytics' login ke bina chupchap kuch nahi. Roz 14:00.
- toolpin.py: roz 17:10 EK Pinterest pin website ke tool page ka (brand din ke hisaab se; vishay keyword se page; SIP/FD/loan 3 aam
  brand par nahi; ek page 60 din mein ek baar; can_pin_now seema; chitra apna 1000x1500; title page ka asli naam).
- ideas.py: Shanivaar 20:00 hafte ke comment (sirf text - 'platform brand naam (mood):' hata kar) se ruchi/naye vishay/galatfahmi -
  sirf owner ko report.
- sitemap_insert: answers (/jawab) aur story dono ab kai-line <url>\n<loc> format mein bhi sahi A-Z jagah (pehle ant mein judta tha).

## v2.9.2 (10 Nov 2026) - owner ki reel/screenshot audit: rang, Hindi, comment, /jawab tez, final adhikari, push, quiz bot
- text.fix: AI text ke chhupe ZWJ/ZWNJ (matra se pehle)/ZWSP/BOM hata kar NFC - reel mein 'परछ◌ाई' jaisa dotted gola nahi.
- pipeline: pakke rang/layout 3 se kam -> SAARE design.PALETTES / LAYOUTS (big3d sirf 3D ho to) apne aap; learn.choose views se.
  (Asli wajah 'har reel ek rang': palettes_ok khaali tha.)
- hooks: pehle scene ki awaaz chhoti (sawal aage bola jaata ho to sirf hook; warna hook + pehla vaakya); bahas ki line chhoti.
- youtube.new_comments: hamare top comment par aaye REPLIES bhi (comments.list parentId) - jawab usi thread mein (growth parent).
  Gande comment: YouTube setModerationStatus=rejected, FB hide - pehle se, jaancha.
- /jawab: KEEP 150->40, table sirf naye; 419 KB -> ~76 KB. Purana code/sawal: register (jawab-archive) se khoj; #cCODE page par
  na ho to JS khud register se dhoondh kar dikhata.
- audit.final_authority (audit.run ke ant mein): vikalp mein sahi ek baar, reel code, video mein jawab leak nahi, 'jawab X nahi'
  mein X sahi nahi, 50-50 mein sahi nahi kata, chhupe akshar nahi, title <=100.
- Jawab turant: upload ke turant publish_site (apply_zip deploy_in=1 min); 15 min baad coverage_check, na mile to dobara + alert.
- push.py (OneSignal): 'onesignal <App ID> <key>' (chat se mitta) -> site par OneSignalSDKWorker.js + CSP + install-app.js mein
  '🔔 Roz ka naya sawal' button (sirf dabane par SDK load + permission; popup nahi); roz 19:05 max 1 notification.
- quizbot.py: 'quiz bot token <token>' -> alag thread; /start, /aaj (A/B/C/D tap), code bhejo = register se jawab, /roz (opt-in,
  sirf chat-id, /stop se mitta), roz 08:00 sirf /roz walon ko.
- config.OFFICIAL + 'welcome pin': Telegram channel mein saare asli link + nakli-chetavni post aur PIN.
- app/sitepatch (privacy/terms/about): 'Hamare official channel (sirf yahi asli)', notification + quiz bot ki privacy, About ki AI
  label line sach. website.sitepatch_apply bot khud ek baar (audit gate) - owner ko alag site ZIP nahi.
- tasks: INFO_V292 (8 ho chuke kaam itihaas mein), naye owner kaam (onesignal, quiz token, galat pin hatao) checker ke saath.

## v2.9.3 (10 Nov 2026) - 'hata diya bolta hai, phir dikhta hai' ki asli wajah + audit
- WAJAH: 'Mere kaam' list mein do tarah ke kaam - (a) owner ki todo list, (b) bot-jaanch wale (check() har baar dobara banata:
  hub video, Meta DM App Review, YouTube Advanced, IG/FB/Threads link, Pinterest Standard, purane W2/W3...). 'ho gaya' sirf (a) se
  hatata tha; (b) agle 'Mere kaam' mein phir aa jaate. Ab: owner_ok (pushti button 'ho:<key>') se (b) bhi pakka band - sirf
  STRICT (login/token jinke bina bot chal hi nahi sakta) asli jaanch se. 'ho gaya <shabd>' ab (b) mein bhi dhoondhta (find_computed).
- Hataye: meta_dm (DM niti se band), hub (bot khud), web_v18/w2/w3, old_crons/old_bot (purane ek-baar). fix_list_v293: YouTube links
  + bio (owner ne screenshot se dikhaya) band. welcome_pin dono purane 'welcome' kaam band karta. GA flag 7-din report par bhi.
- Audit (static): 69 inline button prefix - sab ka handler hai; 86 menu button - sab ka handler. Website: 269 page, har page par
  3+ andar ke link (median 7) - sirf terms 2 (footer se juda); koi anaath page nahi.

## v2.9.4 (10 Nov 2026) - owner ki 3 reel + 'Ranker' photo + lambi shikayat
- Wajah 'har reel Rahul vs Amit': owner ne 10 Nov 04:08 'hook bahas' PAKKA kiya tha -> fix_list_v294 phir rotate. bahas mein 18 naam-jodi
  (10 reel tak dohraav nahi, state hook_pairs). 4 naye challenge andaaz: dobara ('pehli nazar mein X... ruko'), chunauti, tez, dost.
- 'exam' card (design._body_exam/_bg_exam): owner ki Ranker photo jaisa - safed + rangin glow, navy category pill, laal/kaale bold ank,
  laal gol A/B/C/D, laal site pill. 6 diagram paheli (puzzles._gen_diagram): ratio (x²+2, x³-x...), Y-branch, dibba (3 box ek niyam),
  gola (3 ank + k), cross (chaar ÷ 2), BODMAS - har ek ka q alag (dohraav-jaanch na atke), q_show chhota title. diagram -> layout exam.
  qplan mein 6 slot. 1200 bana kar jaanche; frame dekhe.
- render: light/versus/exam par AI photo/clip parat nahi (versus kaala dikh raha tha).
- /jawab KEEP=8 (owner 10 baar); coverage_check KEEP tak.
- Namoona 'Agla': har baar naya sawal-type + naya rang/layout (pehle seed same -> same namoona).
- YouTube comment: padhna/replies/moderation ab comment-login (force-ssl) token se - upload-login mein commentThreads ki ijaazat nahi
  thi (asli wajah 'comment ka jawab nahi').
- Seekhna: bina-command baaton ka record (free_text_log 50) -> har Somvaar Gemini sujhav -> owner '✅' -> learned_alias (hamesha).
- docs/OWNER_RULES.md: owner ke 20 pakke niyam - har AI pehle yahi padhe.
- 'Mere kaam': FB Pahadi token ke steps (system user -> Generate new token -> permissions -> bot mein paste).

## v2.9.5 (11 Nov 2026) - quiz bot asli wajah, Pahadi comment-login, platform caption, purane code, PageSpeed
- quizbot: seedha api.telegram.org VM par atakta tha (main bot relay se chalta hai) -> ab tg._http (seedha + Cloudflare relay),
  shuru par deleteWebhook, getUpdates/galti state mein, ensure() har 10 min (thread mara to dobara), 'quiz bot haal'.
- YouTube comment: Pahadi ka comment-login file thi par scope nahi (403 insufficient scopes) -> growth 403 dekhte hi token hatata +
  owner list mein '[P0] yt comment login pahadi'; bina comment-login wale brand ko padhne ki koshish nahi (shor nahi);
  'yt comment login <brand>' = sirf us channel ka naya link (purana hata kar).
- audit.platform_head: FB/IG/Threads/Pinterest par quiz ki apni pehli line (3 rup, har reel rotate) - quality governor ka bacha hissa.
- answers.archive_import_codes: puzzles.reel_codes (aakhri 800, purane 3-ank bhi) -> zindagi bhar ka register (ek baar, fix_v295).
- bot.psi_weekly: Ravivaar 09:30 - 5 page ki mobile speed + LCP/CLS (PSI_KEY 'psi key ...'; Google Cloud 'sabhinet-pagespeed').
- fix_list_v295: quality governor / PageSpeed / purane code ho gaye; channel-wise /jawab page NAHI (owner niyam).

## v2.9.6 (11 Nov 2026) - hub video audit fail theek
- 11 Nov 02:00 Budh ki Money hub video 'Audit fail: Har scene ka text chhota aur padhne layak' (audit: scene show <= 140) - sawal +
  'Sahi jawab + wajah(160)' lamba tha. hubvideo: sawal 120 tak, jawab+wajah 136 tak (bolne mein poora). Fallback purana tareeka chala tha.

## v2.9.7 (11 Nov 2026) - 11 Nov ki asli chat se
- 03:06 '🔴 ZAROORI prepare: thumb_1.jpg nahi mila': lambi video ka preview banne tak video khud post ho kar 'posted' mein chali gayi
  thi (video sahi post hui). _send_for_approval: posted/file nahi to chupchap; thumbs sirf jo maujood.
- VM audit '🔴 @Sabhisaab_bot par webhook': ye sirf sandesh bhejne wala bot ho sakta hai - ab 🔴 sirf MAIN bot par; baaki 🟡 + kahan mila.
- 10 Nov 16:08/16:13 owner ne 'Maine save kar liya' likha - bot nahi samjha (Gemini ne ulta sawal kiya) -> backup password save.
  'Like kon kar raha' -> sach: naam kisi API se nahi milte + hum rakhte nahi; ginti kahan dekhein.
- fix_list_v296: line mein purani SIP/loan wali video ('Honeymoon Budget: loan ya SIP') cancel (owner niyam).
- (v2.9.6 bhi andar: hub video har scene 140 akshar tak)

## v2.9.8 (11 Nov 2026) - VM audit (03:06) + Gemini audit PDF + chat
- brain.SKIP + transcribe/imagen/veo/gemma (VM log: 400 'JSON mode not enabled' gemini-3.5-transcribe par).
- meta._ig_safe_video: -g 60 -keyint_min 60 -sc_threshold 0, 4M/4.5M/9M (IG ProcessingFailedError 5x / 3 din).
- tg.say: 3900 se lambe sandesh line par todkar (1/n)... - pehle 4000 par KAAT diya jaata tha (owner: 'aadhi report, link adhoora').
- vmaudit: NRestarts mein update-install wale exit bhi gine jaate hain -> ab sirf journal ke asli crash/kill (3+) par 🟡.
- log: har galti ek line (345 multi-line JSON lines ki jagah).
- audit.qc_report: post hone ke baad file POSTED mein - wahan bhi dhoondhe (QC 'Errno 2').
- bot: 'comment login ... jud gaye kya' -> seedha har channel ka haal (pehle sirf 'button dabao').
- website traffic: 7 din vs pichhla hafta (📈/📉) + roz ka ausat.
- NAHI kiya (Gemini PDF): SQLite state / bot.py 4 hisse (jokhim > fayda, abhi atomic write + lock theek); CUDA venv hatana (disk 11% -
  174 GB khaali, torch toot sakta); purane chowkidar cron (trading system ke - owner ki marzi); NIGHT_LOCK (render pehle se nice 15,
  OOM 0, trading services theek).

## v2.9.9 (11 Nov 2026) - 'Comment haal' ka asli bug + 15 din traffic tulna
- BUG: cstats din badalne par reset hota tha sirf jab naya comment/galti aaye; comment_text din nahi jaanchta tha -> 11 Nov subah bhi KAL
  (10 Nov 20:49) ki ginti aur KAL ki Pahadi 403 'aaj' ke naam se dikhti rahi (Pahadi 04:57 par jud chuka tha). Ab: sirf aaj ka; kal ek
  line; har jaanch par 'runs' stamp; har YouTube channel ka aakhri haal (yc_status: ✅ theek / ❌ 403 / comment-login nahi); galti ek line.
- Comment jaanch ab alag thread mein (WORK queue mein lambi video 30-60 min ke peeche atakti thi).
- website.traffic_trend: pichhle 15 din ka roz ausat vs kal (📈/📉 %) + aaj abhi tak; roz 21:05 khud; 'traffic trend'; traffic report mein upar.

## v3.0.0 (11 Nov 2026) - Pinterest khane + Web Story Bing ko turant
- pinterest.SECTIONS + math/gk; section_for(brand, puzzle_kind): Ganit Tricks / GK Quiz / Sawal-Paheli / Pahadi GK; reel pin isi se,
  tool pin 'Free Calculators & Tools' khane mein (Pinterest par log 'maths quiz', 'gk quiz' khojte hain).
- webstory.publish: live hote hi IndexNow (Bing/Yandex); Google sitemap se.
- (Comment haal v2.9.9 live par jaancha: 'aakhri jaanch 06:02', aaj ka hi hisaab, koi purani 403 nahi.)

## v3.0.1 (11 Nov 2026) - Web Story 'invalid' ki asli wajah
- GSC crawled HTML: <head> mein Cloudflare ZARAZ ki inline <script data-cfasync nonce> (khaali config) - AMP mein custom script mana
  ('mandatory attribute missing'). Code mein galti nahi - Cloudflare edge par judti hai. Ilaaj: owner Zaraz band kare (khaali hai).
- webstory.live_check: live story padh kar AMP ke bahar ki script pakde; publish ke baad khud; 'story jaanch'. Owner list mein steps.

## v3.0.2 (11 Nov 2026) - 'story jaanch' takraav + list safai + haal-patra
- 'story jaanch' pehle se FB/IG Story API jaanch thi (bot.py ~1386) - v3.0.1 ka AMP jaanch wahan tak pahunchta hi nahi tha. Ab AMP:
  'amp jaanch' / 'web story jaanch'.
- fix_list_v302: Zaraz (GSC 07:32 'Web Story is valid') + FB Pahadi ijaazat (Full access + comment haal saaf) list se band.
- WORKPLAN ke upar 'ABHI KA HAAL' - kisi bhi AI ke liye shuruaat.

## v3.1.0 (12 Nov 2026) - [FABLE 5.2] POORA AUDIT (bot + website + VM + policy) -> pakka darwaza + saaf Hindi + sach
Poori report: docs/AUDIT_11NOV2026.md (pehle wahi padho - khaaskar hissa A: audience kyun nahi aa rahi).
- app/hindifix.py (naya): Hindi shabd ke andar ghusa doosri lipi ka akshar (live galti #3977 'परछਾਈ' - Gurmukhi matra) -> Devanagari
  (Unicode naam se milan), dohri matra/nukta/halant ek. problems(): poora paraya shabd, Hindi+English chipka ('पहाadi'), akeli matra,
  toota akshar. guardtext.clean + clean_script se HAR bahar jaate text par; answers padhte waqt purani entry bhi theek.
- app/finalgate.py (naya): final authority ki +5 jaanch (likhai, mana vishay, dhaancha, lamba scene 1 sec se kam nahi, raftaar ka
  naap). audit.run ke andar; nateeja state final_gate_last. Command: 'final jaanch'. 'awaaz raftaar 1.1' (0.9-1.25, dohri pushti,
  state voice_speed; tts isi ko padhta hai, na ho to purana VOICE_SPEED).
- pipeline.prepare: tyohaar/Gemini slot ki script mein SIP/FD/loan/nivesh ho (3 aam channel) to render se PEHLE jaancha hua puzzle
  (10 Nov Money #4592 'Bhai Dooj SIP' nikal gaya tha - blocked_topic sirf plan ka naam dekhta tha, script nahi). Owner ka apna maanga
  vishay (topic_text) aur lambi video par ye rok nahi. qplan.BLOCK_RX: nivesh/demat/invest ke roop jode.
- answers.fix_ld: /jawab ka JSON-LD about.html ke saanche se AboutPage/'About Us' aa raha tha -> CollectionPage + 'Sawal ke Jawab'
  breadcrumb, datePublished 2026-11-05. FAQ ki purani line ('table mein 1,200 jawab') aur dohri line theek. Install ke baad page ek
  baar khud dobara banta hai (state jawab_fix_v310).
- website.bing_plan: 'baaki (baari se)' = bina badle purane page roz dobara bhejna BAND (rotate=False). Sirf Google-index-nahi /
  Bing-ne-crawl-nahi / naya-badla. Wajah: yahi aadat purane bot ke baad Bing ban ki thi.
- website.sync_lastmod: website ZIP ke page ki JSON-LD dateModified -> sitemap lastmod (sitemap ZIP mein bhejna zaroori nahi).
- updater._mask: public chat copy mein IP chhupa. Docs mein VM ka poora IP hataya (140.245.x.x) - public repo + trading VM.
- puzzles: Nanda Devi ki wajah sahi. tasks.SEED_V310: 4 owner-kaam (apni awaaz/YPP, Gemini billing, apt upgrade, video file).
- tests/smoke.py NAYA likha (27 jaanch) - GitHub copy mein purane tests/ nahi the. AGLA AI: updater ko tests/ bhi GitHub par
  bhejna sikhao, warna har baar yahi hoga.
- NAHI kiya (sach): render.py/design.py ko nahi chheda (video file nahi mili, sandbox mein awaaz-model nahi - bina dekhe timing badalna
  galat). Vote counter ka dhokha-bachav (Turnstile) agla. Naye feature koi nahi - audit ka nateeja hi ye hai ki feature kam, focus zyada.
- Website W11 (alag ZIP): index.html ki 3 privacy-galat line, privacy 'saari', disclaimer mein quiz-jawab hissa.

## v3.1.1 (12 Nov 2026) - [FABLE 5.2] owner ki bheji reel (#5034 'अगर BANK = AZMJ, तो MILK = ?', 24s) frame-dar-frame dekhi -> 6 kami theek
Kaise dekhi: ffmpeg se har second ka frame + subtitle patti 4/sec + awaaz ki chuppi ka naap (awaaz SUNI nahi ja sakti - sirf naap).
Phir sandbox mein SN_TTS=silent se POORI video render karke naya roop dekha (fonts-noto apt se). Hindi ki spelling us reel mein sahi thi.
1. AWAAZ NE SAWAL BOLA HI NAHI: hooks.apply pehle scene ka "pehla vaakya" leta tha - bank ke sawal mein wo card ka NAAM hota hai
   ('कोडिंग-डिकोडिंग Code।'). Ab hooks.spoken_q: hook ke baad sawal (code paheli: 'स्क्रीन पर कोड देखिए। MILK का कोड क्या होगा?';
   chitra paheli: 'चित्र ध्यान से देखिए...'; agle scene mein sawal poochha ja raha ho to dohraav nahi).
2. "DHEEMI" KI ASLI WAJAH raftaar nahi, BHARTI thi: 'सोचिए / कमेंट में लिखिए' 3 baar (24s mein ~12s). answers._is_filler: 50-50 wale
   scene ki bharti line hata kar 'दो गलत विकल्प हटा दिए। अब बताइए!'. Sanket/trick wali line nahi kat-ti.
3. SOCHNE KA SAMAY SAWAL KE HISAAB SE (owner ki maang): answers.think_hold -> scene["hold"] (GK/shabd 1.0s, ganit/code 2.5s, chitra 3.0s,
   lamba sawal +0.5; seema 3.5). tts.synth(hold=) utni chuppi jodta hai; render pass karta hai; karaoke us chuppi mein shabd nahi
   phailata. Pehle "5 second sochiye" bolte hue awaaz lagataar chalti thi - sochne ka ek second nahi tha. Band: state think_hold_on=False.
4. SUBTITLE VAAKYA BEECH SE TOOT-TA THA ('लिखिए। दो' | 'गलत विकल्प हटा दिए अब' | 'बताओ!'): karaoke._groups - patti vaakya ke ant par
   badalti hai, lamba vaakya barabar hisson mein.
5. HINDI KA LEHJA + VYAKARAN: ek hi video mein 'सोचिए/लिखिए' (aap) aur 'बताओ/लिखो/करो' (tum) mile the -> sab 'aap'. Hook 'bahas':
   '{a} कहता है' = प्रिया/दादी/मम्मी ke saath galat ling, 'पंडित जी कहता है' galat aadar -> '{a} का जवाब है ..., {b} का कहना है - नहीं!'
   + kaarak roop (बेटे/पोते/भतीजे का). Hook, card aur thumbnail ke parde wale text bhi "aap" mein (दो!→दीजिए!, बताओ→बताइए).
6. EXAM CARD: (a) vikalp B aur D LAAL the (i % 2) - 'galat' jaisa ishara; ab sab ek rang. (b) sab kuch upar chipka tha, parde ka beech ka
   ~45% khaali; ab sawal+vikalp ka block beech ki taraf (chitra wale card waise hi).
Nateeja (wahi tarah ka sawal, sandbox): 24s -> ~21s, sawal bola jaata hai, 2.5s asli sochne ka samay.
List: 'video file bhejein' + 'apt upgrade' band (owner ne 12 Nov ko dono kiye; VM reboot 02:28, kernel 1016).
JAANCH BAAKI (VM par hi ho sakti hai): asli Kokoro awaaz ke saath pehli video - 'final jaanch' mein raftaar dekhein; kaan se sunein.
NAHI chheda: speed_math/number_connect ke 'trick' scene (jawab ka tareeka video mein hi bata dete hain - dekhne wale ko mulya milta hai,
YouTube ki 'unsatisfying' niti ke liye achha; par website aane ki wajah kam karta hai - owner chahe to agla faisla).
tests/smoke.py: 37 jaanch.



## v3.1.2 (12 Nov 2026) - [FABLE 5.2] traffic plan + website W12 + chhote sudhaar
- docs/TRAFFIC_PLAN.md (NAYA): impression kam kyun (authority, focus, bhasha, title), owner ke "Zero se Pro" blueprint ke har point ka
  faisla (programmatic 50-URL aur Indexing API = KABHI NAHI), agle kaam T1-T9 kram se, imaandaar samay-andaaza.
- website._apply_zip: wahi website ZIP dobara aaye (12 Nov: W11 do baar) to 'nothing to commit' ka laal ZAROORI alert nahi -
  "pehle se lagi hui hai". (W11 12 Nov 02:13 par lag chuki thi - commit 8eca341.)
- app/ownermode.py (NAYA, owner: "meri apni visit Analytics mein na gini jaaye, IP badalta hai"): har page ke Analytics-code se PEHLE ek
  line - owner apne browser mein ek baar https://sabhisaab.com/#owner-on khole to localStorage 'sh_owner'=1 aur us browser se GA poori tarah
  band (Google ka official window['ga-disable-ID']); '#owner-off' se wapas; kone mein 'Owner mode' patti. Bot install ke ~5 min baad VM ki
  ABHI ki 271 file par khud lagata hai (website._apply_zip ke audit gate se, ZIP_LOCK ke andar, idempotent; state ownermode_v312), phir owner
  ko link bhejta hai. Command: 'owner mode'. about.html saanche mein bhi - isliye /jawab mein apne aap. AMP story mein nahi (wahan JS mana).
  GSC par asar nahi (wo visit ginta hi nahi). Privacy page mein 'sh_owner' ki line (W12).
- tasks.SEED_V312: 5 owner-kaam (owner mode link, nali page index request, brand-search jaanch, Related video + channel link, sandbox
  mount ki photo) + 2 developer-kaam tareekh ke saath (T2 19 Nov, T1 26 Nov).
- Website W12 (alag ZIP, bot ke apne gate se sandbox mein laga kar dekha - audit ERROR 0, sitemap lastmod apne aap):
  /nali-mutthi-square-feet = Devanagari title-tukda + nali table (1-50) + asli Hindi hissa + 3 Hindi FAQ + diagram se galat ₹ hataya;
  /personal-loan-emi-calculator, /data-storage-converter, /mausam-weather = title/description mein wahi shabd jin par rank hai.
- VM (owner ke screenshot): reboot theek - kernel 7.0.0-1016, sabhinet + nifty-live + delta-live + nifty-chart + chowkidar chalu.
  Ek fail: home-ubuntu-sandbox.mount (purana bacha hua mount; asar nahi) - owner se fstab/unit ki photo maangi.
- Namoona thumbnail (owner ka screenshot): 'बताइए' wala naya lehja dikh raha hai; Hindi sahi.
tests/smoke.py: 43 jaanch.
\n

## v3.1.3 (12 Nov 2026) - [OPUS 5.5] sirf naam ka tag (code mein koi badlaav nahi)
- Owner ne pakka kiya: 11-12 Nov ka audit (AUDIT_11NOV2026.md), TRAFFIC_PLAN.md aur v3.1.0, v3.1.1, v3.1.2 + website W11, W12 ki ZIP
  Claude Fable 5.2 ne banayi. In sab par [FABLE 5.2] tag laga; AI_START, WORKPLAN, tasks.py ki tippani mein bhi.
- Ye tag Claude Opus 5.5 ne joda. Pehle ke audit: AUDIT_5NOV2026 = bahar ka docx (lekhak ka naam file mein nahi), AUDIT_9NOV2026 =
  'Claude' (model ka naam nahi likha tha) - inhe nahi badla.


## v3.2.0 (13 Nov 2026) - [OPUS 5.5] Bing: sirf index-nahi page + roz ki Bing report; video: har reel alag jawab-tareeka
Owner (13 Nov): "Bing ko daily wahi URL jaayein jo index nahi huye, report GSC jaisi usi samay; video mein kabhi 50-50 kabhi full kabhi kuch
naya; baaki kuch mat chhedo."
- Policy jaanchi: Bing URL Submission quota site-wise (is site ka roz 70-100; Bing 10,000 tak deta hai, site ki umar/impression se),
  naye/badle content ke liye. Hamari seema WAISI HI: quota ka 1/3, upar se 30/din (purane over-submit ke baad bharosa). 30/din x 14 din
  = 420 > ~270 page, yaani har index-nahi page har 14-30 din mein ek baar pahunchta hai - seema badhane ki zaroorat nahi.
- website.bing_page_stats (NAYA): GetPageStats (padhne wali call, quota nahi khaati) -> jo page Bing search mein kabhi dikha
  (impression > 0) = Bing index ka pakka saboot -> state bing_shown (kabhi ghatta nahi).
- website.bing_plan: (1) Bing-index (bing_shown) + bina badla page ab KABHI nahi jaata (pehle Google-pending hone par bhi ja sakta tha).
  (2) Naya kram 3: "crawl hua, Bing index ka saboot nahi" - 30 din mein ek baar (OWNER_RULES 6: sirf jo index nahi hue). Pehle ye page
  kabhi nahi jaate the. Kram: Google-index-nahi > Bing-crawl-nahi > naya/badla > crawl-hua-par-index-nahi. Bina jaanch wale purane
  page rotate se ab bhi NAHI (v3.1.0 niyam waisa hi). 14/30 din ka niyam waisa hi.
- website.bing_report (NAYA): Bing index ginti (+kal se badlaav, state bing_inindex), crawl, pakka-index page, crawl-nahi, aaj kitne
  bheje + kyun, kul bheje, 14 din Bing impression/click, kitne baaki. website.daily() ke baad USI samay (08:00, GSC report ke saath)
  Telegram par. '🔎 Bing' / 'bing haal' ab yahi report.
- website.indexnow_text: IndexNow ginti mein ab Bing API ke URL nahi jude (pehle "IndexNow aaj 25" dikhta tha, asli 1 tha).
- answers.apply_mech (NAYA, strip_reveal ka 50-50 block iski jagah): 5 jawab-tareeke - fifty (aakhir mein 2 galat kate), full (charon
  aakhir tak), ek_kata (1 galat kata), dhire (pehle 1 phir 2; kam se kam 4 scene, warna fifty), savdhaan ("ek vikalp jaal hai",
  koi nahi katta). Chunav learn.choose('vmech') - har naya pehle 3 video, phir views wala zyada, 25% khoj; usi channel par pichhla
  lagatar nahi. Niyam: sahi kabhi nahi katta, jaal (sahi ke sabse paas wala galat, hook 'ulta' use dikhata hai) kabhi nahi katta,
  koi nakli %/'log yahin phanste' nahi. state fifty_on=False ho to sirf full/savdhaan. state vmech_mode = ek naam ho to wahi (abhi
  koi command nahi - default 'rotate').
- design.body_frame: scene ka apna 'elim' (dheere kaatne ke liye); purana 'fifty' + script fifty_out raasta waisa hi chalta hai.
- audit.final_authority: naya jaanch - kisi bhi scene ki 'elim' mein sahi vikalp nahi. learn: feature 'vmech' ('jeet' mein
  "🎯 Jawab-tareeka"), pipeline record_upload mein vmech.
- tests/smoke.py: GitHub copy mein tests/ nahi thi (VM wali 43 jaanch yahan nahi pahunchi) - naye sire se: 52 module import +
  Bing kram 12 jaanch + jawab-tareeka (har tareeka x 3/4/5 scene) + strip_reveal + audit. Agla AI: VM ki purani tests/ mil jaye to
  dono jod do.
- Kuch aur nahi chheda (owner ka niyam). Website repo (daily.py) nahi badla.
- (v3.2.0, owner ke export 13 Nov 19:44 se pakka) VM ka live code = GitHub v3.1.3 (sirf 7 file badli, upar likhi). Export mein bhi
  tests/ nahi mili - purani 43 jaanch sirf v3.1.x ZIP ke andar thi. Ab install.sh tests/ ko VM par rakhta hai aur updater use GitHub
  par bhejta hai, taaki aage koi AI jaanch na khoye.


## v3.3.0 (14 Nov 2026) - [OPUS 5.5] Page Queue: Uttarakhand ke 264 page roz thoda-thoda, khud live
Owner (13-14 Nov): "Uttarakhand ka total data website par, Google/Bing/Pinterest policy ke hisaab se; kuch delete nahi, duplicate nahi;
ZIP bot ko, bot priority se roz khud live kare bina yaad dilaye; GSC ke liye mujhe link aaye; Bing par bhi jaaye; traffic ruke."
Poora vivran + owner ke 6 attachment ke har sujhaav ka faisla: docs/UTTARAKHAND_QUEUE.md.
- app/pagequeue.py (NAYA): queue ZIP (ukqueue/manifest.json) pehchaan + dohri pushti; roz 06:40 IST ke baad rank kram se 8 page
  (max 10, us din ke doosre naye page gin kar); 3+ andar-link aur requires ki shart; live-nahi page ka link nahi (gate); pehle ke page
  mein naye link (tareekh wahi); hub live hote hi 6 purane page + homepage footer mein /uttarakhand link (ek baar, pq_inj_done);
  sitemap mein naye URL (alphabetical, asli tareekh); website._apply_zip ke audit gate se; fail = kuch nahi + laal alert;
  site_changed sirf naye page (IndexNow purane page par nahi); deploy ke 25 min baad live jaanch -> owner ko URL + GSC kram.
- bot.py: loop hook (pagequeue.due/run_day/tick), command 'queue haal/roko/chalu/roz N/abhi', callback 'pq:' (dohri pushti).
- updater.receive: queue ZIP ko site ZIP se PEHLE pehchanta hai (warna saare page ek din mein chadh jaate).
- tasks.SEED_V330: owner-kaam (ZIP bhejna, auto 'pq') + 2 developer-kaam (chaupal/poll sirf moderation+privacy ke baad;
  GSC dekh kar title sudhaar, auto nahi).
- app/scripts/ukgen/: page banane ka code (bot nahi chalata) - aage koi AI dobara bana sake.
- tests/smoke.py: +11 jaanch (queue kram, 3-link shart, gate, sitemap kram/dohraav, inject ek baar, homepage, ZIP pehchaan).
- Jaancha: VM jaisa sandbox (asli site repo copy + asli audit.py) mein queue ZIP load + roz chalaya - har din audit paas.
- Kuch aur nahi chheda: video, thumbnail, schedule, Bing kram, IndexNow niyam waise hi.
- (v3.3.0, 14 Nov subah, doosra daur) verify-tag + lekhak/AI ki personal line hatayi, zile ka naam heading mein, Devanagari H1,
  faltu 80,330 shabd owner ki ijaazat se hataye (kaam ka 24,312 UK_kaam_ki_baatein.md mein), Bing 50/din (quota/2) + naye UK page
  sabse pehle + Bing report mein 'Bing ne kya bola' aur UK ka alag hisaab. Policy 14 Nov ki: docs/UTTARAKHAND_QUEUE.md hissa 5.


## v3.3.1 (14 Nov 2026) - [OPUS 5.5] Queue ab website ke doosre sudhaar ko kabhi wapas nahi palatti
Owner (14 Nov, queue 8/264 live dekh kar): "bot ZIP badlenge, naya page banayenge ya website par sudhaar karenge to schedule
tutega to nahi?"
- Kami mili: v3.3.0 roz pehle se live Uttarakhand page ko queue ki SOURCE se dobara likhti thi (naye link jodne ke liye) - agar beech
  mein kisi aur ZIP/bot-sudhaar ne us page ko badla ho (footer, privacy, owner mode, link-fix) to wo badlaav agle din palat jaata.
- Ab: gate() live-nahi link ko '<span data-ukg data-h>' aur list item ko 'hidden' banata hai (Google ko koi link nahi; text rehta
  hai) + '<!--ukg2-->' nishaan. Agle din activate() sirf LIVE file mein ye soye link jagata hai - page ka baaki kuch nahi chhuta.
  14 Nov ke pehle 8 page (purana markup, kisi ne badla nahi) ek baar source se naye markup mein aate hain, phir hamesha activate.
- Jaancha: v3.3.0 se din 1 + v3.3.1 se din 2-4, beech mein live page par 'website sudhaar' daala - bacha rahaa; links sahi jage.
- 3 tool page (kapat countdown, shabdkosh, GK quiz) par ek-ek naya section - ab 1000+ shabd (audit WARNING khatam). Inke liye
  nayi queue ZIP (bina live page ko chhede, sirf source badalta hai).
- tests/smoke.py: +2 (activate sirf link jagata hai aur website ka doosra badlaav bachata hai; khaali dabba chhupa/dikha).
- Schedule kabhi nahi tootta: queue data/pagequeue/ + state mein hai (install.sh sirf app/ badalta hai); bot ZIP install, doosri
  website ZIP, naye page - sab ke baad queue wahi se chalti hai. Doosri ZIP ne us din naye page daale ho to queue utne kam leti hai
  (din ki seema 10).

## v3.3.2 (14 Nov 2026) - [OPUS 5.5] Teesra daur: Gemini/ChatGPT ki suchi ki poori jaanch + Google-index se nikle page ka ilaaj
Owner: "pura pado 100%, ek baar total privacy policy ke hisaab se final check karke verify karke do" + (dopahar) "bot ne jo bheje
the wo index ho gaye, purane jo Google ne index se hataye unko bhi theek karo, galti ho to bot ki chatting dekhna".
- Uttarakhand content (app/scripts/ukgen): chhode gaye har hisse ko padha - 17 heading ke neeche asli baatein wapas (SHG, rehne ka
  kharch, bazaar band din...), editor-hisse ke pakke sawal-jawab FAQ mein, '[Module N samaapt]' par editor-hissa khatam; bachi
  'verify' tippani saaf Hindi mein; 'Module/Heading/Section N' ke toote ishare hate ya sahi heading ke link bane; form-template ki
  suchi hati; galat FAQ-jod (pargana != vyapar marg) band; har zila-page ka description alag (descs.py, pehle 247 ek saancha).
  FAQ 5,154 (v2) -> 6,480, 4 se kam FAQ wala page 0. Audit: din-1 aur poore 536 page dono ERROR 0 / WARNING 0.
- Bot: owner ne 14 Nov 10:34 'indixing report do latest' likha - bot ne jawab hi nahi diya. Ab 'index/indexing/indixing/indeks' +
  'report/haal/status/batao/do/kitne' = Google + Bing + Uttarakhand ka poora haal.
- Bot: Google index ka haal ab website repo ki daily.py (roz URL Inspection, 150/din) ke nateeje se (siteknow ke raaste) - pichhla
  v3.3.2-draft jo khud dobara URL Inspection karta tha HATAYA (quota dohra, do report). Index se NIKLE page roz pakde jaate hain:
  'website doctor' (siteknow) ki wajah ke saath alert + owner ki GSC 'Request indexing' suchi mein naye page ke baad sabse upar.
  siteknow.doctor mein naya: sitemap mein hote hue 'noindex', canonical doosre URL par.
- Website (sitefix ZIP, 18 page): electricity-bill-guide (Crawled-not-indexed; wajah /bijli-bill-kaise-banta-hai se ek hi vishay)
  ab sirf 'bill ghatana' - appliance-wise bachat ka hisaab, naya title/description; scientific-calculator-guide par 11 hal kiye
  sawal (code se jaanche); 12 page par dohra-escape '&amp;times;' (screen par '&times;' dikhta tha); 6 page par bhatka Devanagari.
- Kabhi nahi (waise hi): Indexing API, bulk IndexNow, nakli lastmod, bot se apne aap content likhwana.
- tests/smoke.py: index haal/suchi (naye + nikle + index-nahi, max 10), website doctor (noindex/canonical/chhota, theek page par
  galat aarop nahi). SMOKE PASS.
- Chautha daur (14 Nov shaam-raat, owner: "photo jahan risk na ho maximum lagao, bhasha/dhancha theek karo, 100% ek baar mein"):
  * Photo: owner ki 58 photo + 34 video dekhe; 35 saaf photo/frame (chehra, aawaz, watermark/poster wale frame, number plate,
    gaadi ka dashboard, hotel/restaurant, raat ke dhundhle frame BAHAR). EXIF/GPS hata kar naya webp (<=1200px, <160KB). 264 mein se
    260 page par 1 photo (4 tool page par nahi); vishay + ilake se chuni, sabse zyada ek photo 13 page par. Alt text Hinglish, width/
    height/lazy. Pakki jagah ka naam alt mein nahi (owner: 'fix location mat dalna').
  * Bot: photo sirf usi din site par jaati hai jis din uska page (pagequeue.page_images) - pehle se photo daalna 'faltu file'
    aur 404 ka khatra. load_zip ukqueue/img/*.webp rakhta hai; aaj ki ZIP mein sirf aaj ke page ki, jo site par nahi.
  * Bhasha: 828 English heading-saanche haath se Hinglish (headings_tpl.py). Bachi English heading sirf naam (Kedarnath Wildlife
    Sanctuary, USDMA, Uttarakhand High Court, UCC). 'FAQ: X' -> 'Sawal-Jawab: X'. Ek page mein dohri heading: 0.
  * Dhancha: 32 hisson ki heading 'Kya <Zila> mein <Cheez> Hai?' (jawab pehle se 'nahi + kahan milega'); pehla para 264/264 alag.
    13 zilon ka ek hi kram (1-214) waisa hi - poori kitaab ka dhancha badalna = sab link/anchor todna; isliye nahi kiya.
  * Audit: din-1 aur 536 page dono ERROR 0 / WARNING 0; anchor 3,228 - toota 0; E2E (asli load_zip + _run_day + photo): 0 photo
    gayab; SMOKE 273 PASS.


## v3.3.3 (14 Nov 2026 shaam) - [OPUS 5.5] Paanchva daur: sarkari srot milan, Drive ki photo, taazgi-chowkidari, Pinterest asli photo
Owner: "sarkari srot aur jo pending hai sab clear, Google Discover par naam aaye, bot sab page par nazar rakhe taaki purane data se
index se na hate, Drive ke 'Claudi Ai' folder ki photo (duplicate bhi hain) dekh lena".
- Tathya (ukgen/fix5.py + faq_extra): Census 2011 PCA se 13 zile milaye (13 kshetrafal ka jod = 53,483 = rajya). Sahi kiya: Tehri
  kshetrafal 3,796->3,642 (4,085 = 2001), sex ratio 1,077, saksharta 76.36%; Almora 3,144 / 80.47%; Pithoragarh 82.25%; Dehradun
  84.25%; Rudraprayag 81.30%; Pauri 5,329; hub table (Champawat 1,766, Nainital 4,251). Nainital mein Cantonment HAI (Lok Sabha
  uttar AU234: Uttarakhand ki 9 chhavni) - page 'nahi' likh raha tha. Pithoragarh ab Nagar Nigam (pehla chunav 23 Jan 2025).
  Rajya mein 11 Nagar Nigam (purana '6' hata). Vidhan sabha 70, RTO UK-01..20, zila-gathan tithi - mile, sahi the.
- Bachi lekhak/SEO line hati: 'snippet ke liye', 'Passage ranking', 'Aakhri jaanch: ____', 'People Also Ask', 'low-competition',
  'backlink', 'quiz.html file', 'mere dwara banaye', 'Kya likhein' wali khaali dhancha-table, 'aap survey karke bharein'.
  Badrinath 16 Nov 2026 'band honge' -> tithi-neutral (page 32 din mein live honge).
- 4 tool page par ek-ek naya kaam ka hissa (kharcha ki misaal, kapat band hone ki parampara, 10 roz ke shabd, 13 zile + seat).
- Photo: Drive 'Claudi Ai' 138 file = 74 alag (64 dohri). Har ek dekhi; 45 + chat ki 7 chuni, phir 6 kamzor hatayi = 46 nayi
  (photos2.py). Kul 81. Lambe page (2,500+ shabd) par doosri alag photo - 211 page par 2. og:image apni 1200px chaudi photo: 148 page.
- Bot: pagequeue.fresh_scan/fresh_run - har Somvaar 12:15 (aur 'taazgi' likhne par) live UK page mein beeti tareekh ke saath
  bhavishya-vaakya, title mein pichhla saal, 150 din se purana samay-badalne wala page -> owner ko suchi (Claude sudhaar ZIP deta).
  Bot khud content NAHI badalta, nakli lastmod NAHI (Google niyam).
- Bot: 'aaj index ke liye kon kon se page bheje' jaise sawal ab naam ke saath jawab (website.sent_today_text) - 2-3 Nov ko bot ne
  'record nahi hai' kaha tha.
- Pinterest drip: pichhle 30 din ke naye UK page pehle; pin page ki apni asli photo se (imagegen.make_photo_pin), infographic sirf
  jab photo na ho. Roz 15 / ek URL 2 ki seema waisi.
- Audit: din-1 + 536 page ERROR 0 / WARNING 0; anchor 3,227 toota 0; dohri heading 0; E2E photo gayab 0; SMOKE 276 PASS.
