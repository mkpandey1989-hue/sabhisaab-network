SAB HISAAB — HANDOVER v5.1 (naye AI / developer ke liye — sabse pehle ye)

Tareekh: 29 October 2026 · Saath mein: SabHisaab_Roadmap_v14.docx (poori detail). Ye file v1–v4.1 ki jagah hai; purani VM, Cloudflare Worker bot, GitHub cron aur 22-file ZIP wali baatein hata di gayi hain kyunki ab laagu nahi.

# 1. Pehle 5 minute

- Owner: Manoj Kumar Pandey ("Manoj bhai"). Bhasha: Hinglish, chhote vaakya. Wo Telegram se kaam karte hain, laptop bahut kam. Har step poore link aur bhare hue text ke saath. Kuch bhi miss nahi.

- Ek hi bot: **sabhinet** (Telegram "Youtube Bot"), Oracle VM **nifty-a1** (2 OCPU / 12 GB / 200 GB, reserved IP 140.245.8.212) par 24x7. Website sabhisaab.com aur 4 brand channel dono yahi chalata hai.

- Code padhne ke liye (public, sirf copy): https://github.com/mkpandey1989-hue/sabhisaab-network (bot) · https://github.com/mkpandey1989-hue/sabhisaab (website). Roz ka haal: docs/STATUS.md; jo bot khud na sudhaar paya: docs/ESCALATE.md.

- Owner se kabhi token chat mein mat maango. Token owner seedha bot ko bhejta hai; bot message mita kar VM ke secrets/ mein rakhta hai.

# 2. Kaam dene ka tareeka

| **Kya** | **Kaise** |
| --- | --- |
| Bot ka naya version | ZIP: root mein install.sh, VERSION, README.md, app/, docs/ → owner bot ko bhejta hai → "✅ Haan, install karo" → backup + selfcheck + rollback apne aap |
| Website badlaav | ZIP mein repo-raaste (site/x.html, scripts/x.py, README.md) ya sirf file naam (site/ mein jaati hai) → "🌐 Haan". File ginti ki seema nahi (Telegram 20 MB). _redirects mana |
| Deploy | "🚀 Website deploy" — Cloudflare token ho to VM se seedha, warna GitHub deploy.yml |
| Naya page | Roadmap v14 section 3.2 ka spec; ek din mein max 10 naye page; audit ERROR 0; calculator chala kar |
| Jaanch se pehle | Bahari audit ki har baat repo se verify karo; live site ke liye web fetch |

# 3. Abhi ka haal (29 Oct 2026)

- Website: 271 page, sitemap 268, 188 tool, audit 0/0, calculator test pass. Privacy/terms ka naya version live (28 Oct).

- Google pending 7: buy-vs-rent-guide, fire-number-calculator, delivery-date-calculator, random-number-generator, number-system-converter, stopwatch-online, notice-period-buyout-calculator. Wajah aur ilaaj: Roadmap section 8.

- Bot: v2.0.1 chal raha; **v2.0.2 taiyaar** (sabhinet-v2.0.2-update.zip). Website fix W3 LIVE (29 Oct, confirm kiya).

- Connections: 4 brand ka YouTube, Meta (FB+IG), Threads OK; Pinterest Trial (Standard baaki); website service account aur GitHub token bot ke paas.

# 4. Owner ke liye abhi ka kram

- sabhinet-v2.0.2-update.zip bot ko → "✅ Haan, install karo" → "Update safal: v2.0.2" ka intezaar. (W3 aur deploy ho chuke.)

- (Ek baar) Cloudflare: dash.cloudflare.com/profile/api-tokens → Create Token → Custom: Account → Cloudflare Pages → Edit → token bot ko "cf token <token>"; dashboard se Account ID → "cf account <id>". Iske baad deploy VM se seedha.

- (Ek baar) 🧹 GitHub safai → 1️⃣ Purani file hatao (Worker code + band cron). Chahein to 2️⃣ History saaf.

- Roz 1-2 GSC Request Indexing (bot ki subah ki list se), buy-vs-rent-guide pehle.

- Bing support ka jawab aaye to uska text bhejna.

# 5. Bot ke module (app/)

| **File** | **Kaam** |
| --- | --- |
| bot.py | Telegram, menu, scheduler (15 sec), 2 queue, file/photo/video/token intake, Gemini "need" loop |
| brain.py + kb.py + kb.md | Gemini (sabse naya model pehle, quota par neeche), gyaan-bhandaar, padhne wale tools |
| pipeline.py, writer.py, render.py, thumbs.py, tts.py, imagegen.py | Video ka safar |
| audit.py, audit_ai.py | 10 technical + kanoon/samaj + tathya jaanch |
| youtube.py, meta.py, threads.py, pinterest.py, analytics.py | Platform API |
| website.py | Website repo VM par, ZIP → audit → GitHub, deploy (seedha/Actions), IndexNow (Bing-safe), GSC sitemap, traffic, file bhejna, GitHub safai |
| siteknow.py | Website gyaan, badlaav pakadna, link milan, doctor |
| upgrader.py | Auto-heal (roz), khud-upgrade (Ravivaar, rollback), ESCALATE.md |
| privacy.py | 30 din safai, data hatao, policy page jaanch, platform-wise record |
| growth.py, calendar_in.py, company.py, tasks.py, learn.py, seo.py, topics.py, news.py | Comment, report, tyohaar, meeting, owner ke kaam, seekh, topic |
| updater.py, guard.py, state.py, diary.py, tg.py, files.py | Update/mirror, VM suraksha + safai, yaaddasht, Telegram |

# 6. Pakke niyam (sabse zaroori — poori list Roadmap section 10)

- Trading services (nifty-live, delta-live, nifty-chart) aur Chowkidar kabhi nahi chhedna.

- Privacy mein jo likha hai wahi code kare — pehle code, phir policy, dono saath. Commenter data max 30 din, platform jodkar nahi.

- AI label har video par; owner ka naam video/social par kabhi nahi; finance mein SEBI disclaimer; affiliate par hi #ad.

- Website: .html URL nahi, _redirects nahi, din mein 10 se zyada naye page nahi, IndexNow sirf badle URL (max 10/din), sitemap delete nahi, Indexing API calculator par nahi, backlink kharidna nahi.

- Purani ZIP kabhi dobara nahi — hamesha sabse naya version.

# 7. Jo bot nahi kar sakta (platform ka niyam — sirf owner)

GSC Request Indexing; YouTube channel Links; IG/FB/Threads bio link; Telegram/WhatsApp pin; WhatsApp channel post (forward); Meta App Review; Pinterest Standard form; AdSense apply; Meta Data Deletion URL; Instagram account review; Bing support email. Bot har ek ko "🧾 Mere kaam" mein rakhta hai aur jaise hi ho jaye khud pakad kar LIVE karta hai.

# 8. Agla version

Bot v2.1+ ke liye: docs/ESCALATE.md padho, phir Roadmap section 9 aur 11. Docs update karte waqt naya section jodo, purana mat badlo — sirf sach mein dohra ya ab-laagu-nahi wala hatao aur v-section mein likho kya hataya.

# 9. v2.0.2 ke pakke niyam (code mein)

- Har public text guardtext.clean() se: asli tool ginti + poora https://sabhisaab.com/ link + owner naam nahi. Naya platform jodo to guardtext._WRAP mein uska text wala function jodo.

- Schedule kabhi nahi chhootna: auto-manzoori (slot - 20 min), render deadline (slot - 40 min, 1 core), bank script fallback.

- GitHub sirf copy: push fail = gh_pending (kaam nahi rukta); Ravivaar squash; deploy Cloudflare token se VM se.

Sab Hisaab Handover v5.1 · page

# 10. v5.2 (29 Oct 2026, shaam) — kya joda

- Ab owner ko roadmap/handover attach nahi karna. Claude Project instructions mein ek line: "Sabse pehle: git clone https://github.com/mkpandey1989-hue/sabhisaab-network aur docs/AI_START.md, docs/PENDING.md padho, wahin se kaam shuru karo."
- Saare khule kaam: `docs/PENDING.md` (bot roz likhta hai; bot se "pending list do").
- Owner ke abhi ke kaam: sabhinet-v2.0.3-update.zip install; W4-site-fix-29oct.zip "🌐 Haan"; "ho gaya bing"; Chowkidar ko ytlistener wala message; 30 Oct @sunonatak Request review; @labhlodeals "Features you can't use" ka screenshot.
- Naye command: "website report 8 baje" (dohri pushti), "report time", "seo diary", "seo diary abhi", "roadmap do", "docs do".
- Section 4 ka "Bing support ka jawab aaye to text bhejna" - ho gaya (29 Oct, mudda hal).


# 11. v5.3 (29 Oct 2026, raat)
- Install: sabhinet-v2.0.4-update.zip (bot) + W4-site-fix-v2-29oct.zip (website; pehli W4 ki jagah - dono mein se sirf ye).
- Naye command: bot ke message par reply + 'delete'; 'chowkidar file do'; 'report time'.
- Saare khule kaam: bot se 'pending list do' ya GitHub docs/PENDING.md. Owner ki unsamjhi baatein: docs/QUERIES.md.
