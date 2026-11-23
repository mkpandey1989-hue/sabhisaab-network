# FEATURES - kya apne aap chalta hai, kya aap chalu karte ho (v2.5.5)
Bot mein 'features' likhein - live haal aata hai. Bot khud nigrani karta hai (watchdog); dikkat par Telegram par STEP-WISE "kya karein" bhejta hai (ek dikkat ka ek sandesh, 24 ghante baad hi dobara; theek hone par "✅ Theek ho gaya").

## Apne aap chalte hain (kuch nahi karna)
| Kya | Kab |
|----|----|
| /jawab live-check + kharab page dobara banna | 1 ghanta (nahi chalta to 20 min) |
| Uptime (/ aur /jawab) | 10 min; lagaataar 2 baar kharab par ek alert |
| Canary (deploy ke baad) | har deploy ke baad |
| Site scan (toote link, patle page) | Ravivaar 22:00 |
| YPP haal | Ravivaar 19:00 baad |
| AdSense haal | Somvaar 10:00 baad |
| Story link-sticker yaad | roz 21:00 (jab aaj ke jawab hon) |
| Jawab-link: UTM, YouTube comment, purani description | har upload par / raat 23:30 |
| Watchdog (dikkat par step-wise sandesh) | har 30 min; network jaanch roz ek baar |
| Audit gate + SEBI phrase scan | har page / money video par |

## Aap ek baar chalu karte ho (dohri pushti - aapka purana niyam)
| Feature | Command |
|----|----|
| Jawab website | `jawab website chalu` (✅✅) / `jawab website band` |
| Telegram digest (roz 20:30, ek message) | `jawab digest chalu` (✅✅) / `jawab digest band` - bot khud ek tap ka prastav bhi bhejta hai (max 2 baar) |
| ads.txt (AdSense approve hone ke BAAD) | `adsense id pub-XXXXXXXXXXXXXXXX` (✅✅) |

## Naye (v2.5.7)
| Kya | Command |
|----|----|
| YouTube par comment/jawab likhna (alag login, har channel ek baar) | `yt comment login` |
| Privacy page ko practice ke saath milana (ek tap pushti) | `privacy ig theek` |
| Telegram quiz poll (roz max 2) | `jawab poll chalu / band` (ya bot ka prastav ✅✅) |
| /jawab ke naye dabbe live hain? | har 6 ghante apne aap (chup, galti par hi sandesh) |

## Haath se jaanch (kabhi bhi)
`features` | `canary` | `site scan` | `adsense haal` | `ypp haal`

## GitHub se kabhi bhi update
1. GitHub par naya ZIP rakho (bot ka code).  2. Wahi ZIP Telegram par bot ko bhejo.  3. "✅ Haan, install karo".  Bot install se pehle khud test chalata hai; fail ho to purana version chalta rahta hai.
(Purani ZIP dobara nahi - hamesha sabse naya version.) Bot ke likhe docs (PENDING/STATUS...) install par nahi badalte.
