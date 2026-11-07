# Sabhisaab Network bot - HANDOVER (kisi bhi naye AI/developer ke liye)

Repo sirf CODE ki copy hai. Asli bot Oracle VM `nifty-a1` par `~/sabhisaab-network` mein chalta hai (systemd `sabhinet`).
Secrets (tokens) sirf VM par `secrets/` (700/600). GitHub par kabhi nahi. Roz ka haal: `docs/STATUS.md` (bot khud likhta hai).

## Website (v1.2 se isi bot mein)
Purana website bot (Cloudflare Worker @Sabhiisaab_bot + GitHub Actions cron) ki jagah: VM bot website repo
(mkpandey1989-hue/sabhisaab) ki apni scripts (daily.py, watch.py, gsc.py, audit.py) VM par chalata hai (app/website.py).
Purane cron (daily/watch/pending/health/notify/bot) bot khud band karta hai jab token mein Actions:write ho.
deploy.yml (workflow_dispatch) rehta hai; bot use indexnow=koi-nahi se chalata hai aur khud sirf badle URL
IndexNow ko bhejta hai (din mein max 10, ek URL 14 din mein ek baar) - Bing spam (12,800 submission) dobara nahi.
Owner ke haath ke kaam: app/tasks.py roz jaanchta hai, hote hi LIVE.

## Brands
sunonatak = Suno Natak (paise ki kahaniyan) | money = Sab Hisaab Money | deals = Labh Lo Deals | pahadi = Pahadi Hisaab.
Website: https://sabhisaab.com (free calculators). Telegram channel @sabhisaab.

## Modules (app/)
bot.py (Telegram, menu, scheduler, 2 queue: kaam + upload) | pipeline.py (topic->script->3 audit->video->manzoori->upload)
writer.py (Gemini script) | brain.py (Gemini model auto-chunav, grounded Google search, baat samajhna)
render.py/thumbs.py (video, thumbnail, Shorts cover frame) | audit.py (10 technical) | audit_ai.py (policy + fact check)
calendar_in.py (tyohaar: Google search se pakki tarikh/tithi/muhurat, 3 jaanch, auto story)
company.py (vibhaag meeting, owner ke niyam) | growth.py (comments, report, graph, khabar, policy watch, duplicate scan, delete)
youtube.py meta.py threads.py pinterest.py (platform API) | relay.py (Telegram ka Cloudflare raasta + VM dhadkan) | backup.py (ntfy: Telegram ke bina khabar) | learn.py (views se seekh) | updater.py (Telegram se update, GitHub copy)

## Pakke niyam
- Owner ka naam video/social par kabhi nahi. AI label har description mein + YouTube altered-content flag.
- Koi asli insaan/celebrity naam nahi, rajneeti nahi, dharm-tulna nahi, sab samuday ka samman.
- Finance: SEBI disclaimer, koi guaranteed return/stock tip nahi. Affiliate par #ad. Suno Natak: kahaniyan kalpanik.
- Trading services (nifty-live, delta-live, nifty-chart) ko kabhi nahi chhedna.
- Duplicate: topic 45 din, title 90 din, content fingerprint, aur upload se pehle channel ki asli list.

## Jo jaan-boojh kar NAHI kiya (policy/kanoon)
Proxy rotation, fingerprint chhupana, video hash badal kar platform ko dhokha, doosron ka watermark hatana,
cold DM / auto follow / auto collab invite, competitor scraping (ToS), bina ijaazat logon ka data (naam/phone) lena,
"controversy slider", subliminal frames. Ye sab account ban / kanooni khatra hain.

## Pending (kyun baaki)
- Pinterest Standard: Pinterest ki manzoori ka intezaar (bot roz khud jaanchta hai, milte hi LIVE).
- YouTube Analytics: v1.1 mein 'Desktop app' client se /analytics (retention: Analytics API, CTR: Reporting API channel_reach_basic_a1).
- Instagram story link sticker / Shorts mein clickable link: API deta hi nahi; link description, pehla comment,
  Telegram button, Pinterest pin, Threads aur on-screen sabhisaab.com se.
- Website par newsletter/consent, link-in-bio page, "ye bhi dekhein": website repo mein (AdSense apply ke baad).
- WhatsApp channel: koi API nahi, bot message taiyaar deta hai.

## v1.3 (research ke baad)
- Video: 3x super-sampled zoompan (kaanpna khatam) + xfade 0.45s (slide ka jhatka khatam). Owner photos = background.
- Traffic: Threads link_attachment card, IG comment 'LINK' -> 1 private-reply DM (App Review ke baad), Telegram buttons,
  Pinterest link, YouTube top comment, Shorts 'Related video' -> hub video (Studio, haftawar list bot deta hai).
- Policy: format rotation (7 format) - YouTube 'inauthentic content' (Jul 2025) se bachav; FB is_ai_generated=true;
  YouTube containsSyntheticMedia=true; India IT Rules SGI (20 Feb 2026).
- Stats: FB fb_reels_total_plays/likes/comments, IG 'views' metric (impressions/plays hat chuke).
- Purane Telegram message (15 min se purane) restart par nahi chalte; news/policy dobara nahi bhejta.

## v2.0.0 (29 Oct 2026) - naye module
- siteknow.py: website repo (VM par) padh kar data/site_index.json; naya/hata page, legal page badlaav, privacy ke "N din",
  website vs config.LINKS farak; doctor() - index na hone ki wajah. Roz 06:20 + har deploy ke baad.
- upgrader.py: roz 05:30 auto-heal; Ravivaar 02:30 packages (rollback), Meta Graph version (test pass ho tabhi
  data/graph_ver.txt), Gemini list; jo khud na ho -> docs/ESCALATE.md (GitHub).
- kb.py + kb.md: Gemini ko pakka gyaan; Gemini "need" maange to padhne wale tools chala kar dobara poochta hai (max 2 baar).
- website.py: MAX_FILES 3000, repo-style raaste (site/, scripts/, .github/workflows/, worker/, README.md), ZIP_LOCK,
  ginti_sync apne aap, 10 naye page/din, deploy_direct (audit -> calc_test -> wrangler -> GSC sitemap API -> IndexNow),
  remove_obsolete(), squash_history() (dono double confirm).
- Naye shabd: "cf token <t>", "cf account <id>", "website doctor", "upgrade haal", "website zip auto chalu/band",
  buttons 🩺 Website doctor, 🔄 Upgrade haal, 🧹 GitHub safai, 🧠 Website gyaan taaza.

## v2.0.2 (29 Oct 2026)
- guardtext.py: clean() = tool ginti (website tools.js) + poora https://sabhisaab.com/ link + owner naam hatao. install() bot
  chalu hote hi meta/threads/pinterest/youtube ke text wale function par laagu; tg.py public channel post par bhi; audit.description.
- marketing.py: recount() roz 23:30 (max 15 YouTube description); gsc_ideas() Ravivaar 19:30 (query -> extra_topics + topic_pages).
- website.py: push_github() fail ho to gh_pending + har ghante dobara; tick_auto() auto deploy (deploy_due, 15 min); sync()
  gh_pending par reset nahi karta; Ravivaar 03:30 squash_history (gh_squash_auto).
- pipeline.py: clean_script, off-site topic -> siteknow.find page, guard.set_deadline (slot-40 min), bank fallback.
