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
- **Bot update:** ZIP (root mein install.sh, VERSION, README.md, app/, docs/ - docs/ POORA, kyunki install purana docs/ badal deta hai).
  VERSION badhao. Owner ZIP bot ko bhejta hai → "✅ Haan, install karo" → backup + selfcheck + rollback apne aap.
- **Website badlaav:** ZIP mein repo-raaste (site/x.html, scripts/x.py). Owner bot ko → "🌐 Haan". Deploy bot khud (15 min baad).
- Kaam khatam karke `docs/ROADMAP.md` ke NEECHE naya section jodo (purana mat badlo/mitao; sirf sach mein dohra
  ya ab-laagu-nahi hatao aur us section mein likho kya hataya). Naye owner-kaam `app/tasks.py` ke SEED mein jodo
  taaki PENDING.md mein apne aap aayein; jo API se jaancha ja sake use `auto` checker do.

## 3. Pakke niyam (short - poora ROADMAP section 10)
- Trading services (nifty-live, delta-live, nifty-chart) aur Chowkidar kabhi nahi chhedna.
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

## 4. GitHub ka use
Sirf padhne ki copy. Public repo free hai; GitHub Actions cron band; bot din mein ek baar copy bhejta hai. Push fail ho
to bhi bot ka kaam nahi rukta. Koi kharcha/limit ka khatra nahi.
