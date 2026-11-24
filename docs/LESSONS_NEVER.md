# LESSONS - jo galtiyan ho chuki hain, aage KABHI nahi (har AI/developer kaam se PEHLE padhe)

Owner (Manoj bhai) ka hukum, 23 Nov 2026: "audit mein jo kamiyan mili, jo aage nahi karni - GitHub par rakho taaki koi bhi AI
samjhe". Har ZIP se pehle is suchi ki har line par ✅ jaancho. Naya sabak mile to NEECHE jodo (purana mat mitao).
Saboot aur poora haal: docs/AUDIT_23NOV2026.md, docs/ROADMAP.md (v3.4.40-v3.4.43), docs/COMMANDS.md.

## A. Bot ki baat-cheet (owner ki chat)
1. **Ek sawal = ek jawab.** Handler `return run(...)` / `return tg.say(...)` ke baad aage ka code ya Gemini kabhi na chale.
   (Galti: run() None deta tha -> 'indexing link' par 3 alag jawab.) bot.run aur tg.say/alert kabhi None nahi lautate - is niyam
   ko mat todo.
2. **Ginti/haal kabhi AI se nahi.** Video kitni gayi, schedule, indexing, traffic, views, /jawab live, Gemini model - sab
   `app/localask.py` mein asli data se. Naya roz ka sawal aaye to localask + tests/smoke.py + docs/COMMANDS.md mein jodo.
3. **Gemini band = bot gunga nahi.** "Dono dimaag busy 398 min" kabhi nahi; data wale sawal bina AI chalein; baaki par chhota sach.
4. **Owner ki spelling samjho** (bakance, libk, ink, linkk, indixing, vedio, shedule, jabab, dayari, "ho gya", "What's post").
   Fuzzy button se pehle localask chalta hai ('website traffic' ko 'Website draft' bana diya tha).
5. **Lambi menu suchi har jawab ke neeche nahi** - sirf jab bot sach mein na samjhe.
6. **"Poora haal button dabao" jaisa taalna nahi** - jo maanga wahi report do (FB views = FB views).
7. **Har owner sandesh ka test:** CHAT.md ke asli sandesh bot par chala kar dekho (koi 'busy', dohra ya khaali jawab nahi).

## B. Link aur report
8. **Link kabhi aadha nahi.** Report ko `[:3900]` / `[:4000]` se mat kaato - tg.say khud line par todta hai. Chhota ansh chahiye
   to `tg.cut()` (link ke beech kabhi nahi kaat'ta). '/slug' nahi, poora https://sabhisaab.com/slug.
9. **Indexing ki EK ginti** = live sitemap: Index ✅ + Index nahi (wajah) + Naye (jaanch baaki). "Sab index" aur "baaki 18" ek
   saath kabhi nahi. '📑 Indexing' / 'pending indexing' = yahi suchi.
10. **Website doctor jhoothi wajah nahi:** title ka saancha milna = dohra page NAHI (Almora: content 3-5% milta, wahi saanche ke
    12 page index). Asli content milao + page ki umar batao.
11. **"Owner ka kaam" sirf wahi jo owner kar sake.** /jawab audit-fail jaisa bot ka kaam "AAPKA KAAM" mein nahi.
12. **Upload report sach:** YouTube 3 ghante pehle schedule (yt_pre) = pehli koshish, "♻️ dobara koshish" nahi.

## C. Niti (spam / platform policy)
13. **Engagement bait kabhi nahi** (Meta demote karta hai): caption/post/comment-reply mein "comment karo, comment mein likhiye,
    like/share/tag/follow karo, dost ko bhejo". Sawal sawal ki tarah ("Aapka jawab kya hai?"). guardtext.no_bait() aakhri filter.
    Video ke andar ka text/awaaz owner ka format hai - bina owner ki pushti mat badlo.
14. **Nakli aankda kabhi nahi** ("99% log galat", "88% votes", rank). sawalpost opener mein tha - hataya.
15. **Gemini ka banaya sawal post mein nahi** - sirf reel ka asli sawal jiska jawab website par live hai.
16. **Comment bot:** quiz reel par "C", "सी", "D🔥", "Thand" = JAWAB ("samajh nahi aaya" kabhi nahi). Sahi/galat public mein nahi
    (website par aane ki wajah khatam). Har video max 15, account roz 40, ek insaan ek jawab, 7-45 min der, 7 alag roop.
    Instagram par sirf saada 'sabhisaab.com/jawab' (https/UTM nahi).
17. **Bing ko URL ki baarish nahi** (Oct mein site dikhna band hua tha): sirf naye / Bing-ne-na-dekhe, quota ka aadha, ek URL
    14-30 din mein ek baar. IndexNow sirf badle page.
18. **GA4 mein nakli ginti nahi:** page_view dobara kabhi nahi; samay-naap ke chhote event (key event nahi) theek hain.

## D. Website / deploy
19. **Deploy video render ke peeche nahi** - alag SITE line. Git ka har kaam (ZIP, deploy, GitHub copy) ek hi `ZIP_LOCK` (RLock)
    mein - warna git index.lock takraav. (v3.4.36 ne deploy wapas WORK line mein daala tha = /jawab 15-25 min late.)
20. **/jawab: har jawab live** - "nahi dikha" alert sirf tab jab deploy line mein / chal na raha ho.
21. **Hinglish + AdSense:** suchi mein Hindi/English hain, Roman-Hindi alag nahi - guarantee kabhi mat bolo; mana ho to Devanagari roop.

## E. Gemini (free tier - dono key "Free tier", 23 Nov)
22. **Halka kaam lite model par** (comment, plan, news, bank, seo, idea, meeting), owner ki baat + script + audit bade model par.
    Wahi halka prompt 6 ghante mein dobara = cache. Hisaab: 'gemini haal'.
23. **Tareef/emoji/A-B-C-D comment par Gemini nahi** (template, seema ke andar).
24. Model ka naam / kram kabhi andaze se nahi - brain ki state se.

## F. Kaam karne ka tareeka
25. **Jo theek hai wo mat chhedo**; har ZIP mein likho kya NAHI chheda.
26. **Bahari audit (Gemini/koi AI) ki har baat pehle repo se milao** - 3.4.35-39 ke sudhaar sahi the, sirf deploy-line galat thi.
27. **ROADMAP mein literal "\n" nahi**, purana content mat mitao, naya section neeche.
28. Samajh na aaye / content-format badalna ho -> **owner se pehle poochho** (23 Nov: "ulta sidha mat karna").
