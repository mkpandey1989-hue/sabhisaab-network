# COMMANDS - aap kya likhein → bot kaun si report dega (v3.4.42, 23 Nov 2026)

Ye naksha aapki 30 din ki asli chat (461 alag sandesh) ko bot par chala kar banaya. Spelling galat ho to bhi chalega
(bakance, libk, ink, linkk, indixing, vedio, shedule, jabab, dayari, "ho gya", "What's post").
Neeche wale sawal AI (Gemini) ke bina, asli data se aate hain - Gemini ki free seema khatam ho tab bhi.

| Aap likhte hain (jaise) | Bot deta hai |
|---|---|
| aaj kitni video gayi / abhi tak kitni video gyi / 9.30 wali ban gayi? | Aaj ki har video: samay, channel, haal (✅/⏳), YouTube link, platform + aage ke samay |
| video schedule / aaj kon kon se video jayegi / math ke sawal kab aayenge | Aaj ka pakka schedule (har channel 2 sawal-reel, ban chuki / banegi) |
| indexing / 📑 Indexing / indexing balance / pending indexing / kitne page index nahi / google pending url | EK suchi: Live sitemap = Index ✅ + Index nahi (wajah) + Naye (Google jaanch baaki), har page ka POORA link |
| indexing link | Aaj ke Google 'Request indexing' link; naya link na ho to wahi latest pending suchi |
| almora wala page kyu index nahi | Sirf us page ka doctor: asli wajah (content milaan, umar, andar ke link) |
| aaj ke naye page | Pichhle 3 din ke naye live page (poore link) |
| bing kyu nahi / bing ka system | Bing ki asli ginti + wajah + bot kya bhej raha + Bing report |
| aaj kaun se page bheje / bing ko kitne link bheje | Bing API + IndexNow ka aaj/kal ka haal |
| link se traffic / traffic / website traffic / 🌐 Link se traffic | TABLE: kahan se (FB, IG, LinkedIn...) × Aaj/Kal/7 din + brand-wise + 30 din graph |
| link se traffic table format | Sirf table (graph nahi) |
| instagram se kitna traffic / facebook se koi aaye? | Wahi table, upar us platform ki line |
| log kitni der ruke / analytics mein 0 time kyu | GA4 ausat samay + raaste ke hisaab se + 0 sec ki wajah |
| facebook views / instagram views | Us platform ki aakhri video ke views |
| views / total views | Saari video ke views + 7 din scoreboard |
| followers / subscribers / 📈 Poora haal | Har brand × platform followers, views, likes |
| kitni video gayi aur views kitne | Dono (aaj ki video + views) |
| /jawab / jawab website par lagi? / jawab page thik karo | Aakhri 8 jawab: ✅ live / ⏳ nahi; atka ho to bot khud dobara chadhata hai |
| comment ka jawab diya? / comment bot kya kar raha | Comment bot ka tareeka + aaj ka comment haal |
| gemini / gemini ka kaun sa model | Har Gemini model: chal raha / seema kab tak / Cloudflare dimaag |
| bot bhai / kya haal / zinda ho / koi dikkat | Chhota sach: chalu kab se, aaj video, manzoori, abhi kya chal raha, galti |
| 🩺 Sab theek? / health | Poori jaanch (har login, platform, website, Gemini) |
| channel status / threads par error kya | Har platform ki jaanch (Sab theek?) |
| telegram ko kya hua / raasta kyu badla | Telegram raaste ka haal (seedha / Cloudflare / ntfy) |
| vm / disk kitna bhara | RAM, disk, load, trading service |
| audit / vm audit / audit deep | Poore VM ka audit |
| website audit | Website ka audit (page, link, schema) |
| auto doctor | Abhi poori khud-jaanch + khud-sudhaar (roz 05:40 + har 2 ghante chupchaap) |
| master audit / niyam | Aapke saare pakke niyam ki jaanch |
| diary / din bhar kya kiya | Aaj ka poora hisaab |
| mera kaam / ⏳ Pending | Aapke haath ke kaam / manzoori wali video |
| whatsapp post / pahadi fb group post / instagram post / new swal de do | Reel ka ASLI sawal (jawab website par live) - copy-layak |
| ho gaya <shabd> / ho gya <shabd> | Kaam-suchi se hata |
| backup password | Password (1 min mein khud mitega) |

AI (Gemini) chahiye: naya topic par video ("pahadi ki video X par banao"), naya niyam ("aage se aisa karna"),
lamba sawal/salah. Gemini band ho to bot saaf batata hai aur upar wale hukum sujhata hai; "video banao" par brand chunne ka
button deta hai.

## Services desk (v3.5.0)
| Aap likhte hain | Bot deta hai |
|---|---|
| services chalu | Lead worker banata/naya karta hai + website ko pata deta hai (deploy) |
| services band | Desk rokta hai (worker mein lead phir bhi surakshit) |
| services report / services report 7 | Lead, paid ₹, kahan se (code/source), demo ginti |
| quote SH261123AB 4999 dukaan site | Naya version quote (guard ke saath) - phir ✅ button |
| paid SH261123AB 2999 | Payment ledger mein (bank app mein dekh kar likhein) + referral jaanch |
| lead SH261123AB | Us lead ka poora JSON + haal |
| rate gst billing | Rate list se: hamara rate, floor, market |
| refund SH261123AB 999 | Refund ledger mein + referral credit radd |
| services video chalu / band | Roz raat 4 brand ke alag services ad video (manzoori/slot purane jaisa) |
| services video namoona | Abhi ek namoona (Pahadi) - button dabaye bina post nahi |
| services video report | Bani video ka record (dohrav 0) |
| (apne aap) Instagram account band mila | Us brand ka IG upload + comment ruk jaata, khulte hi apne aap chalu |

## Services v3.8.0 (24 Nov 2026) - CRM, gupt page, naya video
| Aap likhte hain | Bot deta hai |
|---|---|
| services upi aapki-id@bank | UPI ek baar set (sirf .env/svc.json mein). Customer ke "Haan" dabate hi uske gupt page par isi ka QR, rakam bhari |
| (naye lead ka card) 💬 WhatsApp · 📞 Uthaya · 📵 Nahi · ⏰ Baad | Bhara hua WhatsApp + call log (nahi uthi = 3 ghante baad yaad, baad = agle din) |
| ✅ ₹X customer ke page par bhejo (button) | EK click: rate customer ke page par + bhara WhatsApp message aapko |
| quote SH.. 499 naam | Rate badal kar naya quote (guard + floor) - phir ✅ button |
| pay SH.. | Haan ka intezaar kiye bina QR khol do (special case) |
| crm / services crm | Khule kaam stage ke hisaab se |
| SH.. working (ya talk/rate/accepted/paid/delivered/closed/lost) | Owner override - stage badlo (log + page par) |
| crm SH.. amount 149 · crm SH.. note ... · crm SH.. due 2026-11-30 | Rakam / note / delivery date badlo (log mein) |
| paid SH.. 2999 | Paisa (bank app dekh kar) - stage working, referral bonus 10% (₹300+ bill, max ₹500) |
| deliver SH.. note | Delivered + customer ko rating ka bhara WhatsApp |
| aur kaam SH.. | 30 din baad "aur kaam?" - SIRF aap bhejte hain (bot apne aap nahi) |
| season add 2026-12-31 \| NSP last date \| m-scholar \| https://scholarships.gov.in/ | Season date (sirf .gov.in/.nic.in) - 7 din pehle us kaam ki video |
| season list | Season dates |
| services chhutti 3 / services chhutti 0 | Chhutti: services video ruki |
| services seema 8 · services seema hatao | (Zaroorat ho tabhi) itne kaam chal rahe hon to us din services video nahi. Default: koi seema nahi - video roz |
| services report 7 | Funnel (aaye → baat → rate → haan → paid → delivered), brand code/source, comment, video audit, CRM |
| services video namoona | Ek namoona (Pahadi, 6 kaam, 5 round audit) |
| (apne aap) 5 min / 24 ghante / 48 ghante | Yaad: baat nahi hui / rate nahi gaya / customer ne haan nahi kaha (har ek ek hi baar) |
| manual call Ramesh 9876543210 PM Kisan form bharna hai (call/wa/dukaan) | Phone/WhatsApp/dukaan wala kaam CRM mein - customer ko bhi gupt page, bahi mein hamesha |
| baat SH.. kal 5 baje call | Baat ka record (bahi mein "baat hui" hamesha; note 90 din) |
| bahi · bahi SH.. · bahi 3210 | Zindagi bhar ka kaam/paise ka hisaab (number ya mobile ke aakhri 4 ank se) |
| paid SH.. 99 | Ab saath mein rasid ka bhara WhatsApp (tap = bhejo) |
| 🧾 Services (main menu) | Sirf services ke button: aaj ka hisaab, khule kaam, bahi, manual kaam, 7 din, doctor, namoona, video chalu/band, form jaanch, comment, awaaz, season, chhutti, madad |
| aaj kitne customer aaye · aaj ki sale · kal ki sale · is mahine ki sale | Seedha hisaab (roz 23:58 apne aap bhi) |
| SH261124APJ1 (sirf number likho) | Us kaam ka haal: stage, rate, mila, page |
| services doctor | Doctor ka haal (awaaz, aaj ki video, form) - har 5 min apne aap ilaaj |
| services instagram sunonatak chalu / band | Services video us brand ke Instagram par (Suno Natak default band) |
| 🗓 Master schedule (button) / 'master schedule' | v3.9.3: har brand ki sawal reel, services reel (aaj/kal), page-post, story - sab samay ek jagah |
| services post band / chalu | v3.9.3: FB par roz 1 services photo-post (har brand) band/chalu |
| post samay pahadi 19:30 | v3.9.3: services post ka pakka samay badlo (✅ -> ✅✅ dohri pushti) |
| 🖼 Services post namoona | v3.9.3: aaj ki post ka chitra + caption dekho (post nahi hota) |
| services video band / services video chalu | Roz ki services video (v3.9.0 se default chalu) |

