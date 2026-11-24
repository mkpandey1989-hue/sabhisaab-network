# ukgen - Uttarakhand Word files -> sabhisaab.com pages (v3.3.2, 14 Nov 2026, Claude Opus 5.5)
Bot isse nahi chalata; ye sirf aage koi AI/developer dobara page banaye to kaam aaye.
Kram: extract.py (14 merged docx -> blocks.json) -> render.py (264 page + manifest.json + dedupe_log.json)
-> dump_internal.py (jo site par nahi gaya, poora) -> simulate.py N (N din ki site par asli audit.py).
Paths file ke upar likhe hain (/home/claude/...); chalane se pehle badlein. Niyam: docs/UTTARAKHAND_QUEUE.md.
v3.3.2 naye: headings_hi.py (98 English template heading -> Hinglish), faq_extra.py (page ke apne tathyon se FAQ, sirf jahan 4 se
kam the), descs.py (har zila-page ka alag description). clean.HEADING_FIX: lekhak-wali heading ka naam badlo / chhupao / chhodo -
naya niyam jodne se pehle us heading ke neeche ka content padho (asli baatein wahan bhi hoti hain). render.tidy_page: milta-julta
sawal jodne se pehle shabd-farak dekho (matlab alag ho to doosra saadha para).

v3.3.2 audit-4 (14 Nov raat): headings_tpl.py - 828 English heading-saanche ka HAATH se likha Hinglish ({D} = zile ka naam;
headings_hi.hinglish(t, D) pehle yahi dekhta hai, phir purana HEAD_HI/PREFIX, aur us nateeje par bhi saancha). Niyam-aadharit
shabd-badal (auto_hinglish) aazmaya tha - vaakya ulte bante the ('likhe gaye par is Zila') - isliye HATAYA; nayi English heading
aaye to TPL mein haath se jodo. dhancha.py - jis hisse ka jawab khud kehta hai 'is zile mein ye nahi hai', uski heading saachi
sawal-roop mein ('Kya Nainital mein Glacier Hai?'), SIRF haath se jaanchi suchi (OK) par - kyunki kai heading mein doosre vishay
bhi hote hain. render.tidy_page 3c: ek page mein do baar wahi heading ho to doosri ke saath uske h2 ka vishay.
photos/ - owner ki apni photo/video-frame (photos.py se saaf kiye: chehra, aawaz, watermark/poster, number plate, pakki jagah ka
naam nahi; EXIF/GPS hata kar naya webp, 1200px tak, 160KB se kam). photos.json = file, chaudai, alt, ilaka, vishay.
render.photo_for: page ke vishay + ilake (pahad/terai) se photo, ek photo kam baar dohrao; hero sirf chaudi (900px+) photo.
Bot ZIP mein photos/*.webp nahi jaate (queue ZIP ke ukqueue/img/ mein jaate hain, page ke saath hi site par).
