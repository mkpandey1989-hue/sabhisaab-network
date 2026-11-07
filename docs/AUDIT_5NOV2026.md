# Audit 5 Nov 2026 - verify + fix (v2.5.2)
Screenshot (5 Nov 11:21): https://sabhisaab.com/jawab ab khul raha hai (title "आज के सवालों के सही जवाब", "Aakhri badlaav: 2026-11-05"); jawab ki table abhi "Jaldi aa rahe hain" - answer_key khaali hai ya page naya bana. 404 khatam.

| ID | Audit ka daava | ZIP se verify | Nateeja |
|----|----|----|----|
| F-02/B-01 | publish_site force=True | answers.py:264 sach | FIX |
| F-03/B-02 | ek kharab bot-page poora deploy rokta | website.deploy_direct audit bina force | FIX (quarantine) |
| F-04/B-03 | re.sub backslash crash | original par reproduce: "bad escape \d" | FIX |
| F-05/B-04 | code 101-998, overwrite | puzzles.py:564 + record() + reel_codes dono overwrite | FIX |
| F-06/B-05 | kharab page regenerate nahi | sach (answer_dirty hi trigger) | FIX reconcile |
| F-07/B-06 | check_live sirf status, 24h | sach | FIX marker + 1h |
| F-08/B-07 | ZIP mein tests/ nahi | GALAT: tests/smoke.py maujood; docs overwrite sach | install.sh FIX |
| F-09/B-08 | GitHub repo purani | VM/GitHub dekha nahi | VERIFY NAHI HUA - VM par check |
| F-10/B-09 | /jawab sitemap/homepage | sitemap generator ZIP mein nahi; homepage par link nahi (live dekha) | sitemap + link jodne ka code |
| F-11 | templated reels ka platform risk | policy-level, code se sahi nahi/galat nahi | Baaki - governor alag release |
| F-12/B-11 | page par verification ka daava | code mein har sawal ka verified_by nahi | text narm kiya |
| F-13 | privacy IG "LINK" vs practice | privacy.html ZIP mein nahi | owner/dev kaam (SEED) |
| F-14 | AdSense apply nahi | live privacy "abhi koi vigyapan nahi" | adsense.py + SEED |
| F-15 | Shorts link click nahi | platform ki seema | owner kaam (channel Links) |
| Naya | puzzles._strip_code / design.py regex `#\d{3}` | 4 ank code par adhoora katta (dedupe toot'ta) | FIX (isi release mein) |

Verify NAHI hua (ZIP mein nahi): site repo ki audit.py/sw.js/404.html/sitemap generator, Cloudflare dashboard, VM state/logs, live /jawab ka HTTP header.

## FINAL Pro Plan (SabHisaab_FINAL_Pro_Plan.docx) se - bot ke hisaab se
| Plan | Bot mein | Nateeja |
|----|----|----|
| W1/B1 toote related-link (SIP page) | site template ZIP mein nahi | sitescan.py pakadta hai; fix developer (PENDING) |
| W2 privacy sec 8 / W3 sec 4 | privacy.html ZIP mein nahi | docs/PRIVACY_PATCH.md + PENDING |
| W4 homepage/channel block | bot sirf /jawab + 4 page mein line | /jawab par channel block joda; baaki developer |
| W5/B2 patle page | - | sitescan (padhta) + PENDING |
| T6/B10 digest | - | kiya (default band) |
| T4 hub/comment/description | top comment + purani description | kiya |
| B5 YPP | analytics scope nahi | 'ypp haal' (subs + deadline); hours Studio mein |
| B19 uptime | - | kiya |
| B21 story reminder | - | kiya |
| YPP 1 Feb 2027 (8,000 hrs / 20M) | - | web par verify kiya: sach (1,000 subs same; fan-funding 500 subs same; existing partners affected nahi) |
