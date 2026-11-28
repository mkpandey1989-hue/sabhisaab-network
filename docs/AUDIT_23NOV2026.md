# AUDIT 23 Nov 2026 - bot ki 30 din ki chat ka poora audit (v3.4.40)

Owner ka sawal (23 Nov 15:40): "4.34 aur jo chal rahi hai milao, Gemini ne gadbad ki; website par jawab publish ho; 30 din ki
chat bariki se dekho; jis hisab se bola tha wo nahi kar raha; roadmap + pending + mera kaam check karke final ZIP do."

## 1. 3.4.34 (owner ki ZIP) vs 3.4.39 (VM par chal rahi) - kya mila
- Sirf 3 code file badli thi: `answers.py`, `website.py`, `bot.py` (+ tests). Baaki 190+ file bilkul same.
- 3.4.35-3.4.39 ke badlaav line-by-line padhe: sab /jawab publish aur deploy atakne ke ilaaj the (deploy dobara, git lock,
  likhai-galti wala jawab page se bahar, Suno Natak button). Inme koi feature toota nahi; smoke 466 ✅ dono par pass.
- Asli gadbad: (a) ROADMAP mein v3.4.36-38 ek line mein "\n" chipka hua tha (theek kiya), (b) v3.4.36 ne deploy wapas
  video-render wali WORK line mein daal diya - isliye naya jawab 15-25 min baad live hota tha aur "15 min mein nahi dikha"
  wala alert roz aata tha.
- Faisla: 3.4.39 ko aadhaar rakha (3.4.34 par wapas jaane se /jawab ke 5 sudhaar kho jaate) + upar v3.4.40.

## 2. Chat ka audit kaise kiya (andaza nahi, asli jaanch)
- CHAT.md ke 30 din: owner ke 889 sandesh, 461 alag-alag. Bot ke jawab sirf 21 Nov se log mein the (pehle ka log mit gaya tha).
- Har ek alag sandesh (461) ko naye/purane code par chala kar dekha (Telegram nakli, network band, Gemini "seema khatam"
  - wahi haal jo 21-23 Nov ko VM par tha). Nateeja:

| Jaanch | v3.4.39 (abhi chal rahi) | v3.4.40 |
|---|---|---|
| Gemini band hone par "🧠 Dono dimaag busy ... 398 min" | 140 sandesh | 0 |
| Ek sawal par 2-3 alag jawab (asli + Gemini) | 7 (indexing link, auto doctor, report table...) | 0 |
| Koi jawab nahi | 0 | 0 |
| Gemini band par saaf "AI chahiye" (secret/aage ka hukum jaisi baat) | - | 45 (sach) |

## 3. Kamiyan jo mili (asli, chat se) aur sudhaar
1. **Ek sawal = 2-3 jawab.** `bot.run()` None lautata tha; `return run(...)` wale hukum (indexing link, auto doctor,
   'kitne page index nahi') ke baad bot aage ke handler + Gemini bhi chala deta tha. → `run()` ab True; `tg.say/alert`
   dohra-roka ya fail par bhi None nahi.
2. **Gemini ki free seema = bot gunga.** "aaj kitni video gayi", "video schedule", "indexing baaki", "link se traffic",
   "instagram views", "gemini kaun sa model", "bot zinda ho?" par "Dono dimaag busy". → naya `app/localask.py`: ye sab
   ab asli data se, Gemini ke bina (owner ka niyam: ginti kabhi andaze se nahi).
3. **Galat button:** 'Indexing bakance' → Website doctor; 'libk se traffic' → indexing report; 'Indexing balance latest'
   → lambi Bing report. → spelling sudhaar (bakance, linkk, libk, ink, indixing, vedio, shedule, jabab, dayari...) +
   'indexing baaki/balance/pending' = EK sandesh (kitne baaki + poore link).
4. **Ulta-pulta indexing sandesh:** "sab live page Google index mein hain" + "baaki 18" ek saath. → saaf: "naya link nahi -
   aapka kaam nahi; baaki 18 par aap request kar chuke, Google 2-14 din".
5. **"Link se traffic TABLE format"** (7+ baar maanga) - table nahi aati thi, sirf list. → asli table: Kahan se × Aaj/Kal/7 din
   + brand-wise (Pahadi/Money/Deals/Suno). Button '🌐 Link se traffic' bhi ab table + graph.
6. **"Kitni der ruk rahe"** ka jawab nahi. → GA4 se ausat samay, engaged %, raaste ke hisaab se.
7. **"Facebook views / Instagram views"** → "Poora haal button dabayein" (khud nahi kiya). → seedha us platform ke views.
8. **Har jawab ke neeche 15 line ki menu suchi** ("📋 Main ye sab kar sakta hoon"). → sirf jab bot sach mein na samjhe.
9. **/jawab der se live:** deploy video render ke peeche. → alag SITE line + `ZIP_LOCK` (RLock) mein deploy aur GitHub copy
   bhi (git index.lock takraav ki asli jad); "nahi dikha" jaanch deploy chal raha ho to 8 min ruk kar (jhootha alert nahi),
   aur wo alert ab hara (bot khud karta hai). Auto-doctor mein /jawab ruka = "🤖 BOT KHUD KAR RAHA" (pehle "AAPKA KAAM"
   jabki owner kuch kar hi nahi sakta). 3 baar fail = ESCALATE (Claude).
10. **Har upload "♻️ dobara koshish" + YouTube line gayab** - YouTube 3 ghante pehle schedule hoti hai, use "pichhli koshish"
    gin liya jaata tha. → pehli baar = poori "📤" report (YouTube link + ruke platform bhi).
11. **Nakli aankda:** sawal-post opener "🔥 99% लोग पहली बार में गलत" (owner + YouTube/Meta niti ke khilaf). → hataya.
12. **'Wo wala swal se do'** par Gemini ne apna sawal (Polyhouse subsidy 80%) bina website jawab ke bana diya (owner niyam:
    sirf website-live jawab wale sawal). → ye sab ab asli reel-sawal se; Gemini prompt mein mana.
13. **"What's post"** (owner ki spelling) samajh nahi aata tha. → WhatsApp.
14. **"Gemini ka kaun sa model"** - Sab theek? mein "Model kram:" khaali, "galti: None". → 'gemini haal' = har model ka
    haal (kab tak seema), Cloudflare dimaag, sach.
15. **"ho gya pin secret"** (ho gaya ki spelling) kaam-suchi mein nahi jaata tha. → theek.
16. **Lamba sandesh "(1/2) / (1/2)"** dohra sirlekh. → chunk 3800.
17. **CHAT.md mein ek minute ke sandesh ABC kram mein** (AI ko lagta tha jawab sawal se pehle aaya). → asli kram.

## 4. Kya NAHI chheda (owner ka niyam: jo theek hai wo mat chhedo)
Video banana/render/thumbnail/look/hook, upload ke platform, schedule ke samay, website ke page, privacy, LinkedIn, Dailymotion,
trading/Chowkidar - kuch nahi badla. Sirf: baat samajhna (localask), dohra jawab, /jawab deploy ki line, 4 sandesh ke shabd.

## 5. Gemini wali "300+ kamiyan"
Wo list is chat mein nahi aayi (sirf ZIP aayi). Upar wali jaanch bot ki ASLI chat se hai. Gemini ki list mile to har baat
pehle repo se milao (AI_START niyam: "Bahari audit ki har baat pehle repo se verify karo").

## 6. Owner ke haath ke kaam (PENDING) - jaancha
- Zaroori, jo bot ke liye sabse bada farq laayega: **Gemini billing** (P1). Iske bina din mein kai ghante AI band rehta hai -
  v3.4.40 roz ke sawal bina AI ke chala deta hai, par "video ka naya topic", "naya niyam" jaisi baat AI hi samajhta hai.
- Purane / shayad ho chuke (owner 'ho gaya <shabd>' likh de to list chhoti): nali index (12 Nov), brand search (12 Nov),
  sandbox mount photo (12 Nov), private DNS (marzi), related video (12 Nov).
- Baaki suchi waisi hi (bot roz 04:00 khud likhta hai).

## 7. Agla AI kya kare
- Gemini ki list aaye to section 5 ke niyam se.
- 'Bing par 10 url bhej do' jaisa seedha hukum abhi Gemini se jaata hai - chaho to localask mein jodo (Bing niti: sirf
  index-nahi page, roz seema).
- tools/replay jaisa test: owner ke naye sandesh `docs/CHAT.md` se nikaal kar `localask.on_text` par chalao - koi "busy"
  ya dohra jawab na ho.

## 8. Shaam ki jaanch (v3.4.41) - owner ke 6 sawal
1. **Bing:** crawl error 0, sitemap pahuncha - site mein rok nahi. Bing naye domain par dheere aata hai; Oct ke over-submit ke baad
   bot jaan-boojh kar sirf naye/na-dekhe URL, quota ka aadha bhejta hai. 'bing kyu nahi' ab asli aankde batata hai.
2. **Google pending:** live sitemap 358 = index 324 + index nahi 8 + naye (1-5 din, Google ki jaanch baaki) 26. (GitHub copy, 21 Nov ki
   Google jaanch.) Bot ab yahi ek ginti deta hai.
3. **Almora (almora-kaise-pahunche):** 18 Nov live, 20 Nov Google aaya, 'Crawled - not indexed'. Content baaki 12 'kaise-pahunche'
   page se sirf 3-5% milta, 18 page se link - technical sab theek. Doctor ki "title same" wali baat galat thi (12 wahi saanche wale
   index hain) - theek ki. Asli wajah: naya page (5 din); Google 2-4 hafte mein dobara tay karta hai.
4. **Hinglish + AdSense:** AdSense ki suchi mein Hindi aur English hain, 'Hinglish/Roman Hindi' alag se nahi. Site lang="hi-Latn",
   99% Roman. Google ka niyam: mukhya bhasha suchi wali ho. Roman Hindi par kuch logon ko 'unsupported language'/kam gunvatta
   ka mana hua (forum), kai Hinglish site chalti bhi hain - pakki guarantee kisi ki nahi. Approval aaye to theek; mana ho to pehle
   top page ka Devanagari roop (PENDING W7 pehle se).
5. **Comment bot:** upar v3.4.41.
6. **GA4 0 sec:** consent theek (India = analytics granted); Google search se aaye logon ka samay dikhta hai. Zyadatar log FB/IG
   app-browser se #code par utar kar band karte hain - samay GA tak nahi pahunchta. v3.4.41 mein naap-event.
