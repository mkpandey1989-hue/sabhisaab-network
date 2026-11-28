# LAST AUDIT - koi bhi AI / developer kaam se PEHLE ye padhe (26 Nov 2026 dopahar, v3.9.7, Claude)

## v3.9.7 - "index jaanch purani / daily.py crash" ki ASLI jad (owner: "bot ki chat ka error + kuch page index nahi - permanent")
| # | Kami | Theek | Kahan |
|---|---|---|---|
| 1 | 24 Nov 08:19 owner ne website alert par "✅ Dekh liya, band karo" dabaya. `ack_all` alerts.json ki HAR dict mein `"ack": True` daalta tha -> `seen_news` aur `open` mein bool | ack_all ab sirf `open` khaali karta hai, `alerts_clean` se dhancha pakka | `bot.py` ack_all, `website.alerts_clean` |
| 2 | Is bool se `daily.py` roz crash (pehle `news()`, v3.9.6 ke baad agli line `old_open v["text"]`). v3.9.6 ka ilaaj ADHURA tha - simulation mein v3.9.6 wali daily.py bhi gir gayi | daily.py load par hi alerts saaf + `old_open` surakshit + khabar hissa try mein | `website.daily_fix397` (site397_apply, audit gate se) |
| 3 | daily.py SAB KUCH aakhir mein save karti thi -> 24-26 Nov roz 3-4 baar Google URL Inspection chali, nateeja ek baar bhi save nahi -> index suchi 24 Nov par atki, already-index page bhi "baaki" mein | index scan ke TURANT baad `save(S_MAIN)` + `day` | daily.py (patch) |
| 4 | Auto-doctor har 2 ghante "dobara shuru → KHUD THEEK KIYA" likhta raha (jhootha) | pehle se chal rahi ho to "chal rahi"; pichhli galti ho to pehle `heal()` | `autodoctor.gidx` |
| 5 | Sandesh mein `(rc {rc})` (f-string galti) | `f"... (rc {rc})"` | `website._daily` |
| 6 | Index jaanch roz sirf 150 URL (385 mein se) -> kuch page 3 din purane status par | `GSC_BUDGET = 400` (Google seema 2000/din) | `website.GSC_BUDGET` |
| 7 | Do thread ek saath daily chala sakte the | `_DAILY_LOCK` | `website.daily` |

Simulation (asli daily.py + 24 Nov jaisi kharab alerts.json): purani = `TypeError: 'bool' object is not subscriptable`; nayi = chali, index 26 Nov save;
GA4/aage ka hissa jaan-boojh kar giraya to bhi index save. Smoke 735 ✅.

### Index ka sach (26 Nov)
- Naye 35 page: koi technical rok nahi (index,follow + canonical + sitemap + hub link 9-19 page se). 8 page 26 Nov 07:11 ko live hue - Google 2-14 din leta hai.
- 7 purane tool page (delivery-date, fire-number, number-system, random-number, stopwatch, notice-period, buy-vs-rent) Aug se "Discovered/Crawled -
  currently not indexed" = Google ka quality/demand faisla, technical nahi. Ilaaj = ek-ek page asli Hindi misaal/FAQ (owner ka niyam: ek page ek baar,
  AdSense review ke dauraan dhyan se). Request Indexing baar-baar dabane se kuch nahi hota.

### NAHI chheda
Video/thumbnail/schedule, site ka koi page, Bing/IndexNow niyam, trading, chowkidar.

### KABHI NAHI
Kisi state JSON mein "har dict par" andha key daalna · roz ki report ka saara data sirf aakhir mein save karna · auto-doctor ka bina jaanche "theek kiya".

---
(neeche purana 26 Nov subah ka audit, waisa hi)

# LAST AUDIT - koi bhi AI / developer kaam se PEHLE ye padhe (26 Nov 2026, v3.9.6, Claude)

Purana: `docs/AUDIT_25NOV2026.md`. Galtiyan jo kabhi nahi: `docs/LESSONS_NEVER.md` (38-40 is audit ke). Poora: ROADMAP "v3.9.6".

## 1. Kami -> theek (smoke 724 ✅)
| # | Kami | Theek | Kahan |
|---|---|---|---|
| 1 | GSC "Web Story is invalid" (AMP) - mobile CSS `<style amp-boilerplate>` mein ghusa (11 story) | CSS hata, AMP par patch kabhi nahi | `website.amp_clean`, `_is_amp`, `site396_apply` |
| 2 | /uttarakhand hub ki 13 zile table mein 0 link, Haridwar gayab, editor note chhapa | 13 x 7 linked table | `website.uk_hub_table` |
| 3 | services form: `SVCKIT.enhance is not a function` (purani cache), services-list par JS dohra load | guard + dohra hata | `website.svckit_guard` |
| 4 | website roz-report crash `daily.py news()` bool >= str (roz 2-3 DHYAN) | sirf string tareekh | `website.daily_fix` |
| 5 | `raqm_layout() failed` - video prepare gira | saaf text → BASIC engine | `app/raqmsafe.py` |
| 6 | Auto-doctor sirf 05:40 + har 2 ghante; "jaanch fail" owner ko | galti aate hi 3 min mein khud + heal(); fail = bot-kaam | `autodoctor.kick/heal/kick_run` |
| 7 | Video raat 00:20 se; owner: 23:30-04:30 | 23:30 se KAL ke slot | `pipeline.NIGHT_START` |

## 2. Jaancha - theek (mat chhedo)
pauri-garhwal-sanskriti-tyohar / services-demo / services-list: index,follow + canonical + sitemap theek, noindex nahi, content alag
(UK sibling se 5-shabd milan 5-7%). 23 Nov wale sanskriti page index ho chuke, 24 Nov wale nahi = sirf umar. "Sitemaps: Temporary
processing error" Google ki taraf. Spam niyam (LAST_AUDIT 25 Nov) sab laagu.

## 3. Isi ZIP mein aur (owner ki haan, 26 Nov 08:29)
- Sawal reel/post ki "अपना जवाब कमेंट में लिखिए" har jagah hati -> "जवाब सोचिए / पहले खुद हल कीजिए" (answers, puzzles, design, sawalpost, sharekit, hooks).
  Smoke test: sawal text mein "कमेंट में ... लिखिए" aaya to FAIL.
- AMP: bot install ke 2 min baad khud theek karta hai; `idxlink.amp_pass` (URL Inspection API ampResult) roz jaanchta hai, PASS par
  PENDING se khud hatata hai. Validate Fix sirf marzi.
- 25 Nov privacy + services-demo pehle hi live (GitHub commit 25 Nov) - PENDING se hataya (`_mig_396`).

## 3b. Baaki (owner)
- Pinterest secret reset (PENDING). YouTube services reel repetitive jokhim (25 Nov sujhav).

## 4. KABHI NAHI
AMP page par sab-page patch · hub par bina link suchi/editor note · auto-doctor ki fail jaanch owner par daalna.
