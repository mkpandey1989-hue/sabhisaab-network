# AUDIT 25 Nov 2026 (v3.9.5) - poora project, senior manager ki nazar se

Owner ka hukum (25 Nov 05:14): "Total project ki sr manager ki tarah audit - privacy policy sab brand aur platform, spam to nahi lag
raha, 3 naye link index nahi ho rahe, bot ki 1 mahine ki chatting padh kar dikkat theek karo, final zip, faltu function mat chhedna."

Kya dekha: repo v3.9.4 (GitHub main), website repo copy (25 Nov 04:10), docs/CHAT.md (30 din, 971 owner sandesh), STATUS, INDEXING,
QUERIES, ESCALATE, privacy.html (live copy), services-list / services-demo / naye UK page, 563 alag owner sandesh bot ke router par chalaye.

## 1. Privacy - policy jo kehti hai vs code jo karta hai
| # | Mila | Khatra | Kiya |
|---|---|---|---|
| P1 | `data/services/comments.jsonl` + `dm.jsonl` mein commenter/DM ka naam + text kabhi nahi mitta; saal-bhar backup mein 400 din | Policy "max 30 din" ka ulta (DPDP + Meta/YouTube app review) | ✅ `svc.wipe_social_pii` roz, backup mein naam/text nahi |
| P2 | GitHub (public) CHAT.md mein lead ka number `📞 +88811473651` khula (mask sirf 91/6-9 wale number pakadta tha) | Kisi ka number public | ✅ `_mask` naya niyam + test |
| P3 | CHAT.md (30 Oct) mein "Account ID" ke baad 31-akshar hex khula (32/40 hi chhupte the) | Agar Pinterest secret tha to koi bhi app chala sakta | ✅ chhupaya; owner: secret reset (PENDING) |
| P4 | Privacy page: "website purely static, koi database nahi" + "koi database nahi" (sec 7, 18) - par Services form, vote, gupt page Cloudflare Worker storage mein | Galat bayan | ✅ website ZIP |
| P5 | Sec 14 "Do apwaad" mein sirf naam/email/WhatsApp - asli form mobile, sandesh, file, IP leta hai; Telegram quiz bhi | Adhoora | ✅ website ZIP |
| P6 | DM ka apne-aap jawab + DM se lead (v3.9.4) privacy page mein nahi tha | Meta app review mein policy=practice zaroori | ✅ website ZIP (DM line) |
| P7 | Sec 17 retention mein Services (90 din) aur Telegram quiz nahi | Adhoora | ✅ website ZIP |

Theek mila (nahi chheda): calculator data browser mein, GA4 Consent Mode (EEA denied), owner-mode, Gemini ko naam nahi, Instagram par
link nahi, AI label, #ad, SEBI line, data deletion section, YouTube API section, OneSignal sirf opt-in.
Brand/platform: chaaron brand + YouTube/FB/IG/Threads/Pinterest/LinkedIn/Dailymotion/Telegram/WhatsApp ek hi page
(sabhisaab.com/privacy) par - har app/channel mein yahi URL hona chahiye (alag page ki zaroorat nahi).

## 2. Spam / platform niti
| # | Mila | Kiya |
|---|---|---|
| S1 | 24 Nov Pahadi: services reel 19:56 (namoona) + 20:02 + 20:12 - 20:02 aur 20:12 ek hi kaam ("मोबाइल / कंप्यूटर मदद ₹49") do alag YouTube video | ✅ upload se pehle aakhri taala `svc_twin_today` (namoona wala hissa v3.9.3 mein theek ho chuka tha) |
| S2 | Services CTA "कमेंट में अपना काम लिखिए" (awaaz + caption) - LESSONS 13 "comment mein likhiye" ko bait kehta hai | ✅ (owner 25 Nov 05:44) - ab "sabhisaab.com पर फ़ॉर्म में अपना काम लिखिए"; audit comment/like/share/follow maangna rokta hai |
| S3 | Har brand par roz services reel - Suno Natak (kahani/quiz) aur Pahadi (sanskriti) par vigyapan jaisi reel; YouTube "repetitious content" / YPP jokhim (ek hi saancha + AI awaaz) | ⏳ OWNER FAISLA - 2 hafte `services 7 din` ka nateeja dekh kar jis brand par lead 0 ho wahan services reel hafte mein 2-3 karein |
| S4 | UK page (13 zila x kai prakar) - scaled content? | ✅ Jaancha: 5-shabd milan 1.2-3.6% (alag content), 2600-5900 shabd - spam nahi |
| S5 | services-list 1030 kaam, 360 KB, OfferCatalog schema; koi nakli rating nahi | ✅ theek; "Article" schema services page par thoda galat (chhota, nahi chheda) |

## 3. Teen naye link jo index nahi (25 Nov 04:26 ki suchi)
1. **/pauri-garhwal-sanskriti-tyohar** - 24 Nov ko bana (1 din). 5900 shabd, alag content, 18 page se link, sitemap mein. Bas naya hai.
2. **/services-list** - 23 Nov bana, 24 Nov 19:01 bada patch. "URL is unknown to Google" = Google abhi aaya hi nahi. 361 page ke
   footer se link + sitemap - 2-7 din mein aata hai.
3. **/services-demo** - "Discovered/Crawled, index nahi". Sirf 5 page se link, 940 shabd, demo zyada JS. Kamzor page - Google der
   karta hai. Sujhav (owner pushti ke baad): har demo ke neeche 2-3 line asli istemaal (kaun, kab) + services page aur 3-4 tool page
   se link. Abhi nahi chheda.
Spam ki wajah se NAHI ruke - teeno 1-3 din purane hain. Kaam: ek baar Request indexing (PENDING), dobara-dobara nahi.
Note: GitHub par `state/daily.json` 21 Nov ka hai, par VM ki roz ki jaanch chal rahi hai (auto-doctor 25 Nov: "Google index jaanch
2026-11-24 ✅") - sirf GitHub copy purani.

## 4. Chat (30 din) se mile mudde
- "(3 page)" + "baaki ⏳ 18" ek sandesh mein = do number (LESSONS 9) -> ✅ "Baaki 15 page: Request ho chuke / Google ne taaza index
  bataya" line.
- 23-24 Nov ka `🏷 Code: {L.get('code')...}` (f-string bina f) - v3.9.4 mein theek ho chuka (code jaancha).
- 24 Nov 19:45 "/jawab jaanch fail [Errno 2] data/jawab." - v3.9.3 mein lock + alag file se theek.
- 563 alag owner sandesh router par chalaye (bina Gemini): koi crash/atka nahi; "Facebook post" = FB GROUP aur bina platform = WhatsApp
  (v3.4.27 owner ka niyam) - jaan-boojh kar, nahi chheda.

## 5. Kya NAHI chheda
Schedule/taala, services video ka design/awaaz/CTA, rate list, /services (AdSense), comment bot, trading/chowkidar, Gemini kram,
UK queue, Bing/IndexNow niyam. Sirf: `updater._mask`, `svc` (30-din safai + backup), `pipeline` (ek naya taala), `idxlink.message`
(ek line), `tasks` (3 owner kaam), tests (+8), docs.

## 6. Agle kadam (kram se)
1. Owner: bot ZIP v3.9.5 -> website privacy ZIP -> Pinterest secret reset -> 3 page Request indexing (sab PENDING mein).
2. 2 hafte baad S2/S3 ka faisla `services 7 din` + YouTube Studio (Shorts views/brand) dekh kar.
3. services-demo ko mazboot karna (sec 3.3) - owner pushti ke baad.

## 7. Doosra hissa (owner 05:44) - saar
IG ProcessingFailedError ka pakka ilaaj + IG kabhi galti se band nahi, slot doctor (har 5 min), comment-bait hata, bonus/referral ek srot
+ record + gupt page par bonus, services-demo mazboot, Pinterest services pin alag URL, audit stamp har doc par. Poori suchi + kya baaki:
`docs/LAST_AUDIT.md`. Platform niti (Nov 2026 jaanchi): Meta engagement-bait (like/share/comment maangna demote), YouTube "Generic or
Repetitive Content" (July 2026 saaf kiya - saanche wali AI video par YPP nahi), Pinterest (ek URL/ek jaisa pin baar-baar = spam;
5-15 pin/din surakshit), Google spam (scaled content, site reputation - Aug/Sep 2026 spam update), Bing (IndexNow sirf badle URL).
