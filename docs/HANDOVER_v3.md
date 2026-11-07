
# HANDOVER v3 — Sabhisaab Network bot + Website (28 October 2026)

*Upar ke dono purane handover (website + network) jaise ke taise hain. Ye naya hissa unke baad hai; kuch delete nahi kiya.*

## A. Naye AI/Developer ke liye pehle 5 minute

1. Ye file + "SabHisaab_Roadmap_v12.docx" padhein (roadmap mein schedule, system, pending, khatre).
2. Code: https://github.com/mkpandey1989-hue/sabhisaab-network (bot) aur https://github.com/mkpandey1989-hue/sabhisaab (website). Dono public mirror; asli chalne wala bot VM par. Roz ka live haal: `docs/STATUS.md`, design: `docs/HANDOVER.md`.
3. Owner se kabhi token chat mein na maangein; naya token owner seedha Telegram bot ko bhejta hai (bot message mita kar `secrets/` mein rakhta hai).
4. Naya version: zip banao (root mein `install.sh`, `VERSION`, `app/`, `docs/`, `README.md`) → owner bot ko bhejta hai → "✅ Haan".
5. Kabhi na chhedein: trading services, Cloudflare Pages project "sabhisaab", `_redirects` file, website sitemap delete/resubmit.

## B. Code ka naksha (app/)

| File | Kaam |
|---|---|
| bot.py | Telegram polling, menu/buttons, chat samajhna, scheduler (15 sec), 2 queue: kaam + upload, file/photo/video intake, token intake |
| brain.py | Gemini model auto-chunav (upar wala pehle), Google-search grounded jawab, intent (action) samajhna |
| pipeline.py | topic → script → audit_ai → render → audit → manzoori/autopilot → upload (har platform alag, retry), duplicate 4 jaanch, platform on/off |
| writer.py | Gemini script (7 format rotation, LINK CTA, owner niyam, hafte ki seekh) + bank fallback |
| render.py / thumbs.py | Layered video (bg + sthir chrome + fading text), photo/clip/AI-image bg, 3 thumbnail, Shorts cover |
| imagegen.py | Gemini image model se 3D background (best-effort) |
| audit.py / audit_ai.py | 10 technical jaanch, caption/description + cross_links; kanoon/samaj + tathya jaanch |
| youtube.py, meta.py, threads.py, pinterest.py | Platform API (upload, stats, delete, comments, DM private-reply, OAuth) |
| analytics.py | YouTube Analytics (retention) + Reporting API (CTR) |
| website.py | Website repo scripts VM par, GA4/GSC traffic, audit, ZIP deploy, IndexNow (Bing-safe), file bhejna |
| calendar_in.py | Tyohaar 7 din aage (Google search, 3 jaanch), tithi, story, muhurat story |
| growth.py | Comments (auto vinamra jawab, moderation, audience), reports, graph, khabar, policy watch, duplicate scan, delete, backup |
| company.py / tasks.py | Vibhaag meeting, owner niyam; owner ke haath ke kaam + khule kaam ki list |
| learn.py, seo.py, topics.py, news.py, updater.py, guard.py, state.py, diary.py, tg.py | Seekh, trend, topic, khabar, update/mirror, CPU/RAM guard, yaaddasht, diary, Telegram |

## C. Owner ke Telegram commands (normal Hindi bhi chalta hai)

- Buttons: 🎬 Abhi video, ⏳ Pending, 📊 Aaj ka haal, 🩺 Sab theek?, ⏸ Pause, ▶️ Resume, 📖 Poora menu (Aaj ka poora hisaab, Kal ka plan, Khabar, Growth graph, Aakhri 5 video, Post hatao, Duplicate jaanch, Aaj ke tyohaar, Company meeting, Analytics, Mere kaam, Website haal, Indexing, Website deploy, Bing, Website audit, Badlaav ka record, Website par aaj kitne log, Website ki file).
- Likh kar: `money ka facebook band karo`, `roz 8 video tak daalo`, `money roz 9 baje aur 7 baje`, `pahadi par Uttarakhand GK bhi banao`, `agle hafte ka plan banao`, `website file advance-tax-calculator`, `hub video money <link>`, `threads link laga diya`, `purana bot band`, `bing key <key>`, `auto jawab band/chalu`, `list mein daalo <kaam>`, `ho gaya <shabd>`, `aage se ... mat karna` (pakka niyam), `/login`, `/analytics`, `/pinterest`, `/version`, `/logs`, `/safai`.
- Photo/mobile video bhejo → brand gallery (caption mein brand naam) → "🎬 Abhi in photo/video se reel".

## D. Data kahan (sab VM par, restart ke baad bhi)

state.json (jobs, schedule, plan, calendar, rules, todo, audience, posted_log, history...), diary.jsonl (har ghatna), learn.json (views/CTR seekh), growth.json (roz followers/views), photos/ & clips/ (owner media), site_repo/ (website code + uski state), backup/ (sirf aakhri).

## E. Pending (roadmap v12 section 6 jaisa)

Meta App Review, Pinterest Standard, website service account key, purana website bot delete, Instagram @sunonatak review, website footer social links + app (PWA) button + link-in-bio, Chowkidar status mein sabhinet, AdSense, YouTube advanced features, hub video + Related video.

## F. v1.7.0 (28 Oct 2026) — Privacy milan + audit fix

*Upar ka sab jaisa ka taisa. Ye naya hissa.*

**Website (sabhisaab repo, ZIP W1 + W2):**
- privacy.html poori nayi: website + 4 brand channel + automation app; GA4 (Consent Mode v2, bina cookie ping), browser storage (sh_consent, sh_a2hs_dismissed, offline cache), weather tool sirf sheher ka naam (GPS nahi), social comment data (Gemini ko text, 30 din seema), YouTube API Services (YouTube ToS, Google Privacy, revoke link), Meta/Pinterest/Telegram/WhatsApp, AI video + affiliate #ad, `#data-deletion` section (Meta app ke liye: https://sabhisaab.com/privacy#data-deletion).
- terms.html: naye section 12-15 (social comment niyam, AI video, affiliate, YouTube/Meta/Pinterest shartein). disclaimer.html: social/AI/affiliate. about + contact: "Hamare social channel" section.
- /links (link-in-bio) naya page: noindex, sitemap mein NAHI (jaan-boojh kar; AdSense se pehle naya content page nahi). audit.py LEGAL mein "links".
- install-app.js v2: har page ke footer mein social link (JS se, ek jagah se). index.html Organization schema mein sameAs.
- salary-structure-guide (4→6) aur notice-period-buyout (4→5) inbound link.
- llms.txt ginti theek (51/53/29/26/39) + social.
- deploy.yml: "Google ko sitemap" step ab har deploy par (pehle 'koi-nahi' par skip hota tha, aur bot hamesha 'koi-nahi' bhejta hai).
- Facebook Sab Hisaab Money aur WhatsApp channel ka seedha link abhi nahi (owner se link milna baaki). WhatsApp ke liye "Updates tab me Sab Hisaab search" likha hai.

**Bot (app/):**
- privacy.py (naya): roz 02:45 commenter data 30 din se purana mitao (audience, diary, queue, drafts, intents cap); `data hatao <naam>`; `/privacy` report; self-audit mein live privacy/terms jaanch.
- bot.py: "pinterest test" NameError (SITE) theek; menu mein 🔐 Privacy; intents 200 tak.
- website.py: deploy race (purana run dekh kar galat LIVE) theek; pull --autostash; IndexNow sirf sitemap wale URL; .yml wali ZIP bhi website ZIP maani jaati hai.
- install.sh: VM par pehle se rakhi app/assets aur scripts/bank file kabhi nahi mitti (GitHub copy mein badi/png file nahi hoti).

## G. v1.8.0 (28 Oct 2026 raat) — saare link, video par poora pata, comment mein sahi link

*v1.7 ka sab isme shaamil hai. Website ZIP W1-v2 ne W1 ki jagah li (W1 kabhi chadhi hi nahi thi).*

- Owner ke diye link: Facebook ab facebook.com/<handle> (sunonatak, sabhisaabmoney, labhlodeals, pahadihisaab), Threads threads.net/@<handle>, WhatsApp channel https://whatsapp.com/channel/0029Vb8rHA5EFeXmREHFHk3n. Website (/links, about, contact, footer JS, sameAs, llms.txt, privacy) aur bot (config.LINKS/WHATSAPP) dono mein ek jaise.
- config.py: LINKS/HANDLES/WHATSAPP/TELEGRAM/SITE_URL ek jagah. Naya brand/channel = sirf yahan badlo, caption aur cross-link apne aap.
- Video (render.py): neeche "https://sabhisaab.com/" poora pata, Shorts/Reels safe zone ke andar (neeche 28% aur daayin button wale hisse se bahar); mukhya text box bhi upar khiska.
- Labh Lo Deals ka screen/description footer ab "Bachat aur deals ki aasaan jaankari"; "#ad" sirf affiliate wali post par (meta["affiliate"]) - ASCI ka sahi tareeka.
- audit.py: post se pehle page link khol kar jaanch (toota ho to homepage); website ki tool ginti roz website se (tools.js) - caption mein "N free calculator" apne aap.
- Comment jawab: jis video par comment, usi ka page link (UTM medium=comment) + WhatsApp; IG "LINK" DM bhi usi page ka. history/posted_log mein ab "page" save hota hai.
- Telegram channel post: WhatsApp button + website link.
- Platform ki seema (imaandaari): YouTube Shorts description/comment mein link clickable nahi (YouTube ka niyam, 2023 se) - wahan Related video + channel ke links; Instagram caption/comment mein link clickable nahi - DM aur bio; Facebook, Threads, Pinterest, Telegram, YouTube lambi video mein link clickable.

## H. v1.8.0 — pending kaam bot ke paas + har Somvaar link jaanch

- tasks.py: "🧾 Mere kaam" mein naye auto-check: W1v2 live (privacy page mein zaroori baatein) aur W2 live (deploy.yml). Owner ke 9 haath ke kaam ek baar list mein (seed_v18): Meta Data Deletion URL, GSC Request Indexing, YouTube channel links, bio mein WhatsApp, welcome post pin, @sunonatak review, Labh Lo Deals monetization kaaran, Chowkidar sabhinet status, AdSense. Hatane ke liye: "ho gaya deletion", "ho gaya request indexing", "ho gaya channel links", "ho gaya bio", "ho gaya welcome", "ho gaya review", "ho gaya policy issues", "ho gaya chowkidar", "ho gaya adsense".
- Self-audit har Somvaar: saare channel link + WhatsApp + Telegram + Pinterest + /links khulte hain? Sirf 404/410 = laal (login-wall ko toota nahi maanta).

## I. v1.8.1 (29 Oct 2026) — "Audit fail - kuch nahi chadhaya:" (khali) ka ilaaj

- Kaaran (pakka, dobara karke dekha): website ki scripts/audit.py JS jaanch ke liye `node` chalati hai. VM par node nahi tha → audit.py crash (FileNotFoundError), stdout khali → bot sirf "Audit fail:" dikhata tha.
- Website: scripts/audit.py ab node na mile to crash nahi, sirf 1 WARNING (JS jaanch GitHub deploy par hoti hi hai). ZIP W1v3 + W2v2 dono mein naya audit.py.
- Bot: apply_zip ab stdout + stderr dono dikhata hai; audit se pehle ensure_node() (sudo -n apt-get install nodejs, din mein ek koshish); install.sh bhi nodejs daalta hai.
