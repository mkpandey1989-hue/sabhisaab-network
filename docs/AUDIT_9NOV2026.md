# AUDIT 9 Nov 2026 - Claude (bot v2.5.7 + website + policy) -> v2.6.0 + W7

Source: GitHub copy (bot 37a4d21 = live v2.5.7, website 4a18b1d), docs/CHAT.md, PENDING, STATUS, HEALTH, ESCALATE, QUERIES,
SITESCAN, INDEXING, KEYWORDS, ROADMAP (sec. 10), owner ka 9 Nov ka sandesh + /jawab screenshot.
Har sudhaar sandbox mein test kiya: tests/smoke.py, tests/test_answers.py, website scripts/audit.py (0 ERROR) aur
scripts/calc_test.py (183 page + 168 card PASS).

## A. Policy (sabse zaroori)
| Mila | Khatra | Ilaaj (v2.6.0) |
|---|---|---|
| Instagram comment mein 'link/info/website' par bot UTM link wala DM bhejta tha (Money, Pahadi par chalu) | Privacy sec. 8 ke ulta; @sunonatak ki rok isi pattern se | DM default BAND (`ig_private_reply_on` sirf owner ki dohri pushti se; 28 Nov se pehle nahi) |
| Commenter ka naam Gemini prompt mein | Privacy "bina profile"; Gemini free tier data Google sudhaar mein le sakta hai | Prompt mein sirf comment text; privacy mein free-tier ki baat likhi (W7) |
| Gemini band ho to comment Cloudflare Workers AI ko; Telegram band ho to ntfy.sh | Privacy mein zikr nahi tha | Privacy mein Workers AI + relay likha (W7); ntfy par comment text kabhi nahi (code) |
| Privacy: app-button "14 din"; code mein 3 din | Policy aur code alag | Privacy 3 din (W7) |
| Privacy/Terms: "har video par platform ka AI label" | Meta API par label field nahi - poora sach nahi | Sach wali line: description mein har jagah, label jahan platform deta hai (W7) |
| Facebook Pahadi: Meta (#10) - bot har 45 min koshish (240 fail) | API par baar-baar galat call = spam jaisa | Brand-wise 24 ghante rok, 3 din mein ek alert (mobile steps), naya token aate hi chalu |

## B. Website
- 105 "toote link" mein asli galat sirf 10 + 3 khud-link (baaki galat alarm: scanner sirf H1 milata tha; 47 'yahan' jaise naam galti nahi).
  W7 mein theek; bot ab Ravivaar scan ke baad khud theek karta hai ('link theek' command), audit gate ke saath, max 15 page.
- 7 index-nahi page: 1,268-1,735 shabd, 90%+ alag content, sitemap mein, 5-15 andar ke link, robots/canonical sahi. Koi technical rok nahi.
  Wajah: nayi site + Google ki crawl priority. Ilaaj: Bing priority (neeche), GSC Request indexing 16 Nov se (PENDING), lastmod sach.
- GSC ke 48 shabd: kabhi lage nahi the. W7: personal loan 1-40 lakh EMI table + 2 FAQ (ganit Python se jaancha; 18% wali purani line
  Rs 1 galat thi - theek), TB/GB/MB/KB jhatpat table + 2 FAQ, mutthi->sq ft table + FAQ. Dates sirf inhi page par (asli badlaav).
- Do calculator ek kaam ke (tax-regime-compare vs old-vs-new-tax-regime): PENDING mein (20 Nov).
- /jawab: table ab seedhi (left align, sticky header), SAARE 1,200 jawab table mein, code/shabd khoj, channel button, purani reel ka
  #cCODE seedha us line par (highlight). Pehle sirf 20 line ki tedhi table thi. 5 Nov 2026 se pehle ki reels mein jawab video mein hi tha.

## C. Bot
- Telegram 413: 45 MB se badi video ka apne aap preview (ffmpeg, aspect sahi); asli upload quality par asar nahi.
- Bing: Bing ka niyam site-wise quota (is site ka 100/din; Bing 10,000/din tak deta hai). Ab roz max 30 (quota ka 1/3):
  Google-index-nahi > Bing-crawl-nahi (GetUrlInfo) > naya/badla > baaki; ek URL 14/30 din mein ek baar; links.html kabhi nahi.
  IndexNow ka niyam (sirf badle, 10/din) waisa hi.
- "Video se kitne log aaye": report ab kal (pakka) + 7 din, platform/brand/reel-code wise, aur sach: Shorts description ke link
  YouTube par click nahi hote (2023 se), Instagram caption mein bhi nahi.
- Pinterest roz ki seema ab "⏸ intezaar" (galti nahi). ESCALATE `_qb 'list'` bug theek.
- PENDING: W2 privacy (live par pehle se sahi) itihaas mein; naye kaam SEED_V260 (W7, FB Pahadi token, Private DNS, GSC dobara,
  tax-regime do page, Phase 2).

## D. Jo jaan-boojh kar NAHI kiya (policy/suraksha)
- VM par WARP/VPN ya khula web port (trading ka raasta + suraksha). Telegram ka doosra raasta (Cloudflare relay + ntfy) pehle se hai.
- Pinterest par /jawab ki jagah doosre page ka link (bhramak link = Pinterest spam niti).
- Sab 180 page par ek saath "Aakhri update" (poori site ek saath badalna = KABHI MAT KARNA). Phase 2: 10-15 page roz, sirf asli tareekh.
- Sarkari dar bina jaanch apne aap badalna (paise ke aankde). Phase 2: official source + do baar milan + audit/calc test.

## E. Phase 2 (agla)
Sarkari-dar watcher (config.SCHEME_RATES_2026 se shuru), policy-change watcher, keyword auto-sudhaar (roz max 2 page),
staged "Aakhri jaanch", Pinterest analytics ('kitne logo ne dekha'), tax-regime do page.

## F. Phase 2 (v2.6.1, usi din) - bana
- Sarkari dar watcher (factwatch): do jaanch + 6 ghante baad dobara + audit; lekh ke udaharan nahi chhedta (ganit galat na ho).
- Policy/API watcher (policywatch): 18 page, har 3 din; asar wala badlaav alert, naya API feature PENDING mein.
- Keyword auto-FAQ (kwfix): sirf ganit se pakka jawab; W7 ki tables ke baad abhi zyadatar shabd pehle se cover hain - naye shabd aate hi jodega.
- Pinterest 'kitne logo ne dekha': brain tool 'pinterest'.
- Seema (sach): JS se banne wale Meta page kabhi-kabhi bina browser padhe nahi jaate - wahan purana news-watch. Sarkari site band/badli
  ho to dar nahi badlegi (shak alert) - galat number lagane se behtar.

## G. v2.6.2 + W8 (usi din, owner: "apna kaam shuru karo")
- Jaancha: robots.txt khula + Sitemap line ✅, 404.html noindex ✅, ads.txt khaali (sahi) ✅, koi asli page 300 shabd se kam nahi ✅,
  har page par tareekh pehle se ✅ (scanner galat gin raha tha).
- Bana: homepage + har tool page par 'Aaj ka sawal' (website -> /jawab -> Telegram/WhatsApp loop), AdSense meta-tag site jodna.
- Baaki (agla): tax-regime ke 3 page ka takraav (salary-wise table chahiye - is saal ke slab pakke srot se jaanch kar), Google Fonts
  self-host (270 page ka head - dheere-dheere), schema/editorial-policy/share-card, /jawab tap-to-guess + streak, video V1-V10.
- Badi galti mili + theek (W8): naye regime mein 12 lakh se thoda upar aay par 87A marginal relief nahi lagta tha - 4 calculator galat tax
  dikhate the (13 lakh: Rs 66,300 vs sahi Rs 26,000). Node se jaancha: 12.75L=0, 13L=26,000, 14L=81,900, 15L=97,500.
- Tax-regime ke 3 page: compare wala ab salary-wise table page (alag irada); guide aur calculator waise hi.
- Baaki (sach): Google Fonts self-host (270 page ka head - fayda chhota, risk bada; alag ZIP mein dheere), result share-card/embed,
  video V1-V10 (render test VM par chahiye - yahan video render ki jaanch nahi ho sakti).

## H. 10 Nov (v2.6.3 + W9)
- Asli galti: TDS calculator mein commission 5% (sahi 2%, 1 Oct 2024 se). Mahila Samman page kehta tha 'confirm karein khul raha hai ya nahi'
  jabki 31 Mar 2025 se band hai. 13 tax page par naye Income-tax Act 2025 ka zikr nahi tha.
- Jhoothe alarm: fonts 404 (preconnect tag), RBI 'dar badli' (homepage ke roz badalte %), 90 din (page update ho chuka tha par gina nahi).
- Khatra: token aate hi 30 purani post ek saath. Theek: 20 min ka farak + 3 din seema.
- Section ke naye number (80C, 87A waghairah) srot aapas mein alag bata rahe the - isliye page par number nahi likhe, sirf sach ki baat.
