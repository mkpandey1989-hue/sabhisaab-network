"""v2.7.0 (owner 10 Nov: 'video link se website par traffic'): HAFTE KI HUB VIDEO = 'is hafte ke 10 sawal'.

Kyun: YouTube Shorts ki description ke link click nahi hote; LAMBI video ki description ke link click hote hain aur Shorts ka
'Related video' bhi lambi video par jaata hai. Isliye har hafte ek brand ki lambi video:
  - is hafte usi channel ki reels ke 8-12 sawal (answers.answer_key se - ye jawab pehle hi jaanche ja chuke, Gemini andaza nahi)
  - har sawal: sawal -> 5 sec sochiye -> sahi jawab + wajah  (asli value, 'templated' nahi)
  - description mein ASLI chapters (render ke baad har scene ka asli samay) + har sawal ka clickable link /jawab#cCODE + tool page
Sawal kam hon (6 se kam) to purana tareeka (writer/bank) - schedule kabhi nahi tootta.
"""
import datetime
import re

from . import state
from .config import BRANDS, SITE

MIN_Q, MAX_Q, DAYS = 6, 12, 14

# v2.7.4 (owner: 'topic thumbnail aisa jo searchable ho'): log YouTube/Google par jo SACH MEIN khojte hain - 'paheliyan with
# answer', 'GK quiz in Hindi', 'maths tricks', 'Uttarakhand GK' (UKSSSC/UKPSC ki taiyari wale). Har hafte alag shabd-kram
# (ek hi title baar-baar nahi). Nakli aankda/jhootha exam-daava nahi: 'abhyaas ke liye' sach hai.
SEO = {
    "pahadi": (["Uttarakhand GK Quiz in Hindi | {n} सवाल जवाब सहित | UKSSSC UKPSC अभ्यास",
                "उत्तराखंड GK {n} सवाल (जवाब के साथ) | Pahadi Quiz | Garhwali Kumaoni",
                "Uttarakhand Samanya Gyan | {n} GK Questions Answers Hindi | पहाड़ी क्विज़"],
               ["उत्तराखंड GK", "*{n} सवाल*", "जवाब सहित"],
               "uttarakhand gk, uttarakhand gk quiz, uttarakhand gk in hindi, uksssc gk, ukpsc, pahadi quiz, garhwali, kumaoni, उत्तराखंड सामान्य ज्ञान"),
    "money": (["Maths Tricks Quiz in Hindi | {n} दिमागी सवाल जवाब सहित | SSC Railway अभ्यास",
               "{n} Maths Puzzles with Answer | गणित के दिमागी सवाल | Reasoning Quiz Hindi",
               "Speed Maths Quiz Hindi | {n} सवाल 5 सेकंड वाले | जवाब और ट्रिक"],
              ["{n} गणित सवाल", "*ट्रिक के साथ*", "कितने सही?"],
              "maths tricks, maths quiz in hindi, reasoning quiz, ssc maths, railway maths, गणित पहेली, dimagi sawal, speed maths"),
    "deals": (["Discount Percentage Tricks | {n} सवाल जवाब सहित | Maths Quiz in Hindi",
               "Sale का असली हिसाब | {n} Discount Maths Puzzles with Answer | Hindi",
               "Percentage Maths Quiz | {n} दिमागी सवाल | Shopping Discount Tricks Hindi"],
              ["{n} डिस्काउंट सवाल", "*असली हिसाब*", "कितने सही?"],
              "discount tricks, percentage tricks, maths quiz hindi, successive discount, sale maths, प्रतिशत, छूट का हिसाब"),
    "sunonatak": (["Hindi Paheliyan with Answer | {n} दिमाग वाली पहेलियाँ | Reasoning Quiz",
                   "{n} Tricky Paheliyan (जवाब के साथ) | Dimagi Sawal | Hindi Riddles",
                   "Dimag Wali Paheli | {n} Hindi Riddles with Answer | Logic Quiz"],
                  ["{n} पहेलियाँ", "*जवाब के साथ*", "कितनी सुलझीं?"],
                  "paheliyan, hindi paheliyan with answer, dimagi paheli, hindi riddles, reasoning quiz, tricky questions, पहेलियाँ"),
}


def seo(brand, n, today=None):
    titles, thumb, tags = SEO.get(brand, SEO["sunonatak"])
    wk = (today or datetime.date.today()).isocalendar()[1]
    return (titles[wk % len(titles)].format(n=n)[:100], [x.format(n=n) for x in thumb],
            [t.strip() for t in tags.split(",") if t.strip()])


def week_items(brand, today=None, key=None):
    """Is brand ke pichhle 14 din ke jawab (naye pehle), har sawal ek baar."""
    today = today or datetime.date.today()
    cut = str(today - datetime.timedelta(days=DAYS))
    seen, out = set(), []
    for e in reversed(key if key is not None else (state.get("answer_key") or [])):
        if e.get("brand") != brand or str(e.get("date", "")) < cut:
            continue
        q = re.sub(r"\s+", " ", str(e.get("q", ""))).strip()
        if not q or not e.get("ans") or q.lower() in seen:
            continue
        seen.add(q.lower())
        out.append(e)
        if len(out) >= MAX_Q:
            break
    return out


def _clean_q(q):
    q = re.sub(r"#\S+", "", q)
    return re.sub(r"\s+", " ", q).strip(" -|:")


def script(brand, today=None, key=None):
    """-> lambi video ki script (format long) ya None (sawal kam)."""
    items = week_items(brand, today, key)
    if len(items) < MIN_Q:
        return None
    b = BRANDS[brand]["name"]
    n = len(items)
    scenes = [{"show": f"{b}: is hafte ke {n} sawal - aapne kitne sahi kiye?",
               "say": f"Namaste! Is video mein {b} ke is hafte ke {n} sawal hain. Har sawal ke baad paanch second sochiye, phir sahi jawab "
                      f"aur uski wajah dekhiye. Apna score comment mein likhiye.",
               "chapter": "Shuruaat"}]
    for i, e in enumerate(items, 1):
        q = _clean_q(str(e["q"]))
        qs = q if len(q) <= 120 else q[:117].rstrip() + "…"          # v2.9.6: audit niyam - har scene ka text 140 akshar tak
        scenes.append({"show": f"Sawal {i}: {qs}", "say": f"Sawal number {i}. {q} Paanch second sochiye.",
                       "chapter": f"Sawal {i}: {q[:60]}"})
        exp = re.sub(r"\s+", " ", str(e.get("exp") or "")).strip()
        head = f"Sahi jawab: {str(e['ans'])[:60]}"
        room = 136 - len(head)
        ex_s = (exp if len(exp) <= room else exp[:max(0, room - 1)].rstrip() + "…") if exp and room > 20 else ""
        scenes.append({"show": head + (f"\n{ex_s}" if ex_s else ""),
                       "say": f"Sahi jawab hai {e['ans']}. " + (exp[:220] if exp else "")})
    scenes.append({"show": f"Har sawal ka jawab aur wajah: {SITE}/jawab", "say": "Har sawal ka jawab, wajah aur free calculator "
                   "sab hisaab dot com par hai. Roz naye sawal ke liye channel subscribe kariye aur Telegram par judiye.",
                   "chapter": "Aage kya"})
    links = "\n".join(f"Sawal {i}: {SITE}/jawab#c{e.get('aid') or e.get('code')}" for i, e in enumerate(items, 1))
    return {"brand": brand, "format": "long", "page": "/", "source": "hub_week", "hub_items": [e.get("aid") or e.get("code") for e in items],
            "title": seo(brand, n, today)[0],
            "tags": seo(brand, n, today)[2] + [BRANDS[brand]["name"], "sabhisaab"],
            "description": f"{seo(brand, n, today)[0]}\n\nIs hafte {b} ki reels ke {n} sawal - har sawal ka sahi jawab aur wajah. "
                           f"Apna score comment mein likhiye!\n\nHar sawal ka jawab website par (link par tap karein):\n{links}",
            "thumb": {"lines": seo(brand, n, today)[1], "emoji": "🧠"},
            "scenes": scenes}


def chapters(meta):
    """Render ke baad asli samay se YouTube chapters (pehla 0:00, kam se kam 3, har ek 10+ sec). -> text ya ''."""
    starts = meta.get("scene_starts") or []
    sc = meta.get("scenes") or []
    rows, last = [], -99.0
    for i, s in enumerate(sc):
        if i >= len(starts) or not s.get("chapter"):
            continue
        t = 0.0 if not rows else float(starts[i])
        if rows and t - last < 10:
            continue
        rows.append((t, s["chapter"]))
        last = t
    if len(rows) < 3:
        return ""

    def fmt(t):
        t = int(t)
        return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"
    return "Chapters:\n" + "\n".join(f"{fmt(t)} {c}" for t, c in rows)
