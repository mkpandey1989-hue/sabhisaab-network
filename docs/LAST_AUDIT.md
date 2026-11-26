# LAST AUDIT - koi bhi AI / developer kaam se PEHLE ye padhe (25 Nov 2026, v3.9.5, Claude)

Owner (Manoj bhai) ka hukum: "last audit ki stamp lagao taki koi bhi AI sabse pahle yahi dekhe ki audit mein ye kami thik kiya".
Naya audit karo to: is file ko naye sire se likho (purana `docs/AUDIT_<din>.md` mein rehta hai) + sab docs ke upar ki 🔖 stamp ki
tareekh badlo. Poora saboot: `docs/AUDIT_25NOV2026.md`. Galtiyan jo kabhi nahi: `docs/LESSONS_NEVER.md` (29-37 is audit ke).

## 1. Kya kami mili -> kya theek kiya (sab v3.9.5 ZIP mein, smoke 713 ✅)
| # | Kami | Theek | Kahan |
|---|---|---|---|
| 1 | Services comment/DM ka naam+text kabhi nahi mitta (policy 30 din), saal-bhar backup mein 400 din | roz 30-din safai, backup mein naam/text nahi | `svc.wipe_social_pii` |
| 2 | Public GitHub CHAT.md mein galat/videshi phone + 31-hex likhawat | mask naya | `updater._mask` |
| 3 | Privacy page: "koi database nahi" galat, DM/Services/Telegram quiz/referral adhoora | website ZIP (privacy) | `site/privacy.html` |
| 4 | Ek services kaam Pahadi par 2 baar (20:02 + 20:12) | upload se pehle aakhri taala | `pipeline.svc_twin_today` |
| 5 | Indexing sandesh: "3 page" + "baaki 18" do number | "Baaki N" ka matlab saath | `idxlink.message` |
| 6 | Services CTA "कमेंट में अपना काम लिखिए" = Meta comment-bait | ab "sabhisaab.com पर फ़ॉर्म में अपना काम लिखिए"; audit mein comment/like/share/follow maangna mana | `svcvideo.CTA_*`, `BAN`, `svcpost` |
| 7 | IG `ProcessingFailedError` (services reel 3/5 fail; sawal 0/15) | Meta ka diya upload `uri`, poori file ek request, usi container par 20/40s dobara, 3rd koshish 720p saadi file, pipeline 10 min x 6, report ⏳ (laal nahi) | `meta._ig_container`, `_ig_compact`, `pipeline.IG_RETRY_*` |
| 8 | 3 ProcessingFailed = brand ka POORA Instagram apne aap band (galat) | kuch-der wali galti gini hi nahi jaati | `igguard.transient` |
| 9 | Slot ki video bani nahi / fail / upload line mein atki = slot khaali; auto-doctor owner ko "aapka kaam" bolta | har 5 min slot doctor khud dobara banata/bhejta (max 2), auto-doctor khud upload kick | `pipeline.slot_doctor`, `autodoctor.stuck` |
| 10 | Referral bonus: advance par hi 10% (poore bill ka nahi); aadha istemaal = poora bonus khatam; 90 din safai mein code-wale ka number mitne se bonus kho jaata | poore chukaye bill par update, aadha istemaal = baaki bachta, bonus baaki tak naam/number surakshit, gupt page par bonus dikhta | `svc._ref_pending`, `paid`, `night_audit`, `bonus.py` |
| 11 | Bonus ke niyam 6 jagah alag-alag likhe (svc, gupt page, terms, rate list FAQ + schema, video awaaz) | EK srot `app/bonus.py`; 'bonus set' (dohri pushti) -> sab jagah apne aap | `bonus.sync_site`, `svc._site_files` |
| 12 | services-demo kamzor (940 shabd, har demo 17-37 shabd) - "Crawled, index nahi" | har demo par "Kiske kaam ka" + 5 FAQ + FAQ schema (1627 shabd) | website ZIP `site/services-demo.html` |
| 13 | Services pin har baar ek hi URL (Pinterest repetitive) | pin us video ke kaam ke dabbe `#c-<cat>` par | `pinterest.pick_link` |

## 2. Jaancha - theek mila (mat chhedo)
Schedule ka taala (`sched_lock`/`sched_guard`), raat 00:20-04:30 aaj ki saari sawal reel + 01:30 ke baad services, UK page (5-shabd milan
1-4% = alag content), IG hashtag ≤5, YouTube tags ≤15, AI label, Pinterest roz 10-12, Dailymotion 3, IndexNow/Bing seema, GA4 consent.

## 3. Baaki (owner ka faisla / haath ka kaam)
- **YouTube YPP jokhim:** har channel par roz ek jaisi services reel (saancha + AI awaaz). YouTube July 2026 "Generic or Repetitive Content".
  Sujhav: 2 hafte `services 7 din` dekh kar jis brand par lead 0 ho wahan YouTube par services reel band (`services` setting) - owner pakka kare.
- **Sawal reel ke andar "अपना जवाब कमेंट में लिखिए"** (owner ka format - bina pushti nahi badla). Meta ise bhi comment-bait gin sakta hai.
- PENDING: Pinterest secret reset, website ZIP (privacy + services-demo), 3 page Request indexing.

## 4. Is audit ke baad KABHI NAHI
Comment/like/share/follow MAANGNA (video, caption, post) · bonus ka koi ank haath se kahin likhna (sirf `bonus.py`) · naya data file bina
mitne ki tareekh · Meta ki kuch-der wali galti par account band · slot ki video fail par owner ko kaam dena jab bot khud bana sakta hai.
