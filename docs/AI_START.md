# AI_START - koi bhi AI / developer SABSE PEHLE ye padhe

Owner: Manoj Kumar Pandey ("Manoj bhai"). Bhasha: Hinglish, chhote vaakya. Wo mobile/Telegram se kaam karte hain.
Har step poore link aur bhare hue text ke saath. Owner se roadmap/handover attach karwane ki zaroorat NAHI - sab yahin hai.

## 1. Padhne ka kram (5 minute)
1. `docs/PENDING.md` - saare khule kaam (owner + bot/AI), aage ki tareekh wale, aur jo ho chuke. Bot roz 04:00 IST likhta hai.
2. `docs/STATUS.md` - bot ka aaj ka haal (connections, schedule, uploads, website index).
3. `docs/ESCALATE.md` - jo bot khud theek nahi kar paya. Yahi tumhara pehla kaam hai.
3b. `docs/QUERIES.md` - owner ne bot ko jo kaha aur bot poora nahi kar paya ("Khule"). Inhe owner se ek baar pakka
    karke feature/command jodo. (Bot ye file kaam hote hi 10 min mein GitHub par bhejta hai.)
3c. `docs/HEALTH.md` - har brand x platform: chal raha / ruka, kyun, kya karna.
3d. `docs/KEYWORDS.md` - Google par log kya khoj kar aa rahe (roz). Page/title/naya page se PEHLE padho; 'naya' wale par
    owner se pakka karo. Ek-ek number ke alag page (5 lakh, 6 lakh...) kabhi nahi (Google scaled-content niti).
3e. `docs/CHAT.md` - owner ne bot ko jo bhi likha (30 din, secret/phone/email chhupe). Bot ki training/naye command yahin se.
4. `docs/ROADMAP.md` - poori yojana + pakke niyam (section 10 = KABHI MAT KARNA). Naya section sabse neeche.
5. `docs/HANDOVER_OWNER.md` - owner ke liye handover (kaam dene ka tareeka). `docs/HANDOVER.md` - code architecture.

Repo: https://github.com/mkpandey1989-hue/sabhisaab-network (bot, public copy, koi secret nahi)
Website repo: https://github.com/mkpandey1989-hue/sabhisaab (copy; asli source VM par ~/sabhisaab-network/data/site_repo)
Live: https://sabhisaab.com/ · Asli bot: Oracle VM nifty-a1 (140.245.8.212), systemd `sabhinet`.

## 2. Kaam kaise dena hai
- **Bot update:** ZIP (root mein install.sh, VERSION, README.md, app/, tests/, docs/). v2.5.2 se install sirf code-docs naye karta hai; bot ke roz likhe docs (PENDING, STATUS, ESCALATE, QUERIES, HEALTH, KEYWORDS, CHAT, INDEXING) install par NAHI badalte - ZIP mein unki copy purani ho to bhi chalega. tests/ ZIP mein zaroor rakho (install se pehle smoke + test_answers chalte hain).
  VERSION badhao. Owner ZIP bot ko bhejta hai → "✅ Haan, install karo" → backup + selfcheck + rollback apne aap.
- **Website badlaav:** ZIP mein repo-raaste (site/x.html, scripts/x.py). Owner bot ko → "🌐 Haan". Deploy bot khud (15 min baad).
- Kaam khatam karke `docs/ROADMAP.md` ke NEECHE naya section jodo (purana mat badlo/mitao; sirf sach mein dohra
  ya ab-laagu-nahi hatao aur us section mein likho kya hataya). Naye owner-kaam `app/tasks.py` ke SEED mein jodo
  taaki PENDING.md mein apne aap aayein; jo API se jaancha ja sake use `auto` checker do.

## 3. Pakke niyam (short - poora ROADMAP section 10)
- Trading services (nifty-live, delta-live, nifty-chart) kabhi nahi chhedna. Chowkidar sirf 'chowkidar fix' command se (owner ka dohra button, v2.1.0).
- Token kabhi chat/GitHub par nahi. Owner seedha bot ko bhejta hai; bot message mita kar VM ke secrets/ mein rakhta hai.
- Privacy policy jo kahe wahi code kare. Commenter data max 30 din, platform jodkar nahi.
- AI label har video; owner ka naam video/social par kabhi nahi; finance mein SEBI disclaimer; #ad sirf affiliate.
- Instagram par koi link/UTM nahi ("link bio mein"); "comment LINK / DM" wala bulawa kabhi nahi (29 Oct 2026 ki rok).
- Website: .html URL nahi, _redirects nahi, din mein 10 se zyada naye page nahi, IndexNow sirf badle URL (max 10/din),
  sitemap delete nahi, Indexing API calculator par nahi, backlink kharidna nahi.
- Pakki setting (samay, topic, platform, niyam, report) bina owner ki DOHRI pushti ke kabhi nahi.
- Purani ZIP kabhi dobara nahi. Bahari audit ki har baat pehle repo se verify karo.

## 3b. Telegram ke raaste (v2.0.7)
Bot pehle seedha api.telegram.org, na chale to Cloudflare Worker 'sabhinet-relay' (app/relay.py), sab band ho to ntfy
(app/backup.py). Worker hi VM ki dhadkan dekhta hai (VM ke bina khabar). Poora haal: ROADMAP 'v2.0.7' section.

## 3c. Har baar pehle CHAT.md (owner ka niyam, 2 Nov 2026)
docs/CHAT.md = owner (👤) + bot (🤖) ki 15 din ki baat. Har AI kaam shuru karne se pehle padhe: jahan 👤 ne kuch maanga
aur 🤖 ka jawab galat/adhoora/"nahi kar sakta" tha, wo fix karo (ZIP). Kaam pura ho to docs/PENDING.md mein bot khud
hatata hai (🤖 auto) ya owner 'ho gaya <number>' se; AI apne ZIP mein naya kaam tasks.py ke SEED mein daale.

## 4. GitHub ka use
Sirf padhne ki copy. Public repo free hai; GitHub Actions cron band; bot din mein ek baar copy bhejta hai. Push fail ho
to bhi bot ka kaam nahi rukta. Koi kharcha/limit ka khatra nahi.

## 3d. Do bot, do updater (v2.1.9, 3 Nov 2026)
- sabhinet ZIP (install.sh + VERSION + app/ + docs/) -> sirf @Manoj_yt_sahayak_bot. Chowkidar ZIP (chowkidar.py + install_chowkidar.sh,
  kabhi install.sh nahi) -> sirf @manoj_vm_chowkidar_bot. Dono bot doosre ki ZIP pehchaan kar mana karte hain.
- Chowkidar sabhinet ke folder mein kabhi nahi likhta; sabhinet Chowkidar/trading ko sirf padhta hai ('chowkidar fix' hi apvaad).
- Chowkidar ka code TradingBot taraf hai; uski aakhri jaanchi copy: v5.2-SAFE-FINAL (ROADMAP 'v2.1.9').

## 3e. Sample Studio + din-plan (v2.2.0, 3 Nov 2026)
- Namoona (status "sample") kabhi upload/pending/report mein nahi. Owner ka pakka look: state brand_look; din-plan: app/weekplan.py.
- Har setting badlaav dohri pushti se. Manual: docs/SAMPLE_STUDIO.md. Bahari "v11.2.0" ZIP v2.1.0 par bani thi - kabhi mat lagao.

## 3f. v2.3.0 (3 Nov 2026)
- Naye module: design (Premium Neon - default), puzzles, sfx, vault_web (band), web_widgets (sirf draft), elite_audit (asli).
- Kabhi nakli aankde ('88% votes', '99% fail', rank) mat jodo - owner ka niyam + platform niti. Sab badlaav dohri pushti se.
- Function ke andar import ho to UnboundLocalError ka khatra: naya code likhte waqt branch-aware scan (ROADMAP v2.3.0).

## 3g. v2.5.2 (5 Nov 2026): /jawab audit fix
- /jawab page ab audit gate (force=False) se hi chadhta hai; fail par page repo mein nahi rehta, poora error Telegram + state `jawab_last_error`.
- Reel code ab 4 ank (1000-9999, bharne par 5); purane 3 ank wale code jaise the. Koi bhi code kabhi overwrite nahi (answers.record, puzzles._unique_reel_code).
- Live-check marker se (soft-404 pakadta hai), chalte hue 1 ghanta; deploy ke baad canary.py. Naye command: 'canary', 'adsense haal', 'adsense id pub-...'.
- Kabhi nahi: khud ad click, 'ad par click karo', auto-refresh, nakli traffic/views, platform ke niyam todna, kharidi hui engagement.

## 3h. v2.5.3 (5 Nov 2026)
- Naye command: 'site scan' (sirf padhta), 'ypp haal', 'jawab digest chalu/band' (dohri pushti), 'canary', 'adsense haal', 'adsense id pub-...'.
- Jawab link UTM: answers.answer_url(code, platform, brand). Instagram par kabhi link/UTM nahi. Code regex 3-6 ank (puzzles._strip_code, design.py).
- Digest chalu ho to answers.record Telegram par alag post nahi karta (digest_pending). Band ho to purana raasta.
- Site scan/uptime/YPP: kuch badalte nahi. Platform policy page dekhe bina naya feature nahi.
- v2.5.4: namoona video par callback `dl:<jid>` (studio.download) - sirf namoona; tg.video(markup=...) optional, baaki callers par asar nahi.
- v2.5.5: watchdog.py (nigrani + step-wise sandesh, sirf padhta), 'features' command, docs/FEATURES.md. Naya monitor jodo to evaluate()/net_checks() mein (key + title + steps) - dedupe/recovery apne aap.
- v2.5.6: answers.KEEP=150 (poore) + ARCHIVE=1050 (chhoti list, har code ka anchor) ; RETAIN=1200; record() purani entry se exp hatata hai. Export (5 Nov 21:20) = v2.5.5 live.

## 3i. v2.5.7 - Jawab/Video plan ki NAHI KARNA list (policy, bot kabhi nahi)
Nakli vote/%/'88% log'/'98% fail'/'1% genius'; nakli pinned comment; 'asli IQ'/genius certificate/IAS jaisa jhootha jod; daravna hook ('jail bhej sakta hai', 'muawza'); video CTA mein jawab leak;
kisi named loan app ko fake/asli batana; auto-next countdown/auto-redirect; poore-screen laal flash (1 sec mein 3 se zyada jhapak); 'million views/RPM' jaise vaade par plan; bina verify practice sawal;
Auto Ads/ad refresh/khud click/ad ke paas answer button; kisi aur ki photo se puzzle; DM/auto-comment (Instagram DM 27/28 Nov tak band). Comment likhne ke liye YouTube mein ytcomment.py ka alag login - upload token mat chhedo.
