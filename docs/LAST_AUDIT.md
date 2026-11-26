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
