"""v2.5.2 (5 Nov audit fix): force=False audit gate, re.sub lambda, unique code, marker-based live check, reconcile.
v2.5.0 (owner 5 Nov + Omnichannel Masterplan 'answer free rakho'): SAWAL reel mein, SAHI JAWAB website + Telegram par.
- Video: sawal + vikalp + timer + 'apna jawab comment karo' + 'sahi jawab: sabhisaab.com/jawab (code #N), link description/bio
  mein'. Jawab wala scene video se hatta hai (curiosity-gap; jawab kabhi lock nahi - website par sabke liye free).
- Jawab pehle se jaancha hua (puzzle = ganit/tark se, Gemini sawal = fact-check + do-raay) - wahi jawab video banne se PEHLE
  meta mein pakka; upload hote hi Telegram channel par aur website ke /jawab page par (code anchor #c<code>).
- Har platform par jawab ka link wahan jahan click hota hai: YouTube description ki pehli line, Facebook/Threads post text,
  Pinterest pin ka link, Telegram button; Instagram par 'bio ke link mein' (IG caption link click nahi hota).
- Website page: site ke apne template (about.html) se - wahi header/footer/consent/GA; audit pass ho tabhi live (apply_zip);
  fail ho to sirf Telegram (koi toota page nahi). Owner ki ek baar ki dohri pushti ke baad hi website par apne aap."""
import datetime
import hashlib
import html as H
import json
import re
import zipfile

from . import state, tg
from .config import BRANDS, DATA, SITE
from .log import log

TG_LINK = "https://t.me/sabhisaab"
PAGE = "/jawab"
KEEP = 150            # poore dabbe (naye)
ARCHIVE = 1050        # v2.5.6: uske baad ke purane jawab chhoti list mein (har code ka anchor bana rahe - purani reel ka #cCODE link na tute)
RETAIN = 1200


# v2.5.2 (S1): har jawab ke neeche 2-3 free tool (page patla na ho, visitor ek se zyada page dekhe). Sab slug live homepage se verify kiye.
TOOL_NAMES = {
    "age-calculator": "Age Calculator", "date-difference-calculator": "Date Difference", "din-bache-calculator": "Din Bache",
    "date-add-subtract-calculator": "Date + / − Days", "time-duration-calculator": "Time Duration", "stopwatch-online": "Stopwatch",
    "average-calculator": "Average Calculator", "lcm-hcf-calculator": "LCM & HCF", "number-system-converter": "Number System",
    "sip-calculator": "SIP Calculator", "emi-calculator": "EMI Calculator", "50-30-20-budget-calculator": "50/30/20 Budget",
    "discount-calculator": "Discount Calculator", "percentage-calculator": "Percentage", "price-compare-calculator": "Price Compare",
    "nali-mutthi-converter": "Nali-Mutthi Converter", "bigha-converter": "Bigha Converter",
    "hectare-bigha-acre-converter": "Hectare-Bigha-Acre",
}
RELATED_BY_KIND = {
    "age": ["age-calculator", "date-difference-calculator", "din-bache-calculator"],
    "calendar": ["date-add-subtract-calculator", "date-difference-calculator", "din-bache-calculator"],
    "clock_angle": ["time-duration-calculator", "stopwatch-online"],
    "series": ["average-calculator", "lcm-hcf-calculator", "number-system-converter"],
    "coding": ["number-system-converter", "lcm-hcf-calculator", "average-calculator"],
    "purane_shabd": ["nali-mutthi-converter", "bigha-converter", "percentage-calculator"],
}
RELATED_BY_BRAND = {
    "money": ["sip-calculator", "emi-calculator", "50-30-20-budget-calculator"],
    "deals": ["discount-calculator", "percentage-calculator", "price-compare-calculator"],
    "pahadi": ["nali-mutthi-converter", "bigha-converter", "hectare-bigha-acre-converter"],
    "sunonatak": ["average-calculator", "lcm-hcf-calculator", "number-system-converter"],
}


def related_tools(e):
    slugs = RELATED_BY_KIND.get(e.get("kind") or "") or RELATED_BY_BRAND.get(e.get("brand") or "") or []
    return [(sl, TOOL_NAMES[sl]) for sl in slugs if sl in TOOL_NAMES][:3]


def on():
    return state.get("answer_offsite", True)


def code_for(script):
    c = script.get("reel_code")
    if c:
        return str(c)
    h = int(hashlib.md5((script.get("title", "") + script.get("puzzle_q", "")).encode()).hexdigest()[:6], 16)
    return str(1000 + h % 9000)


def live():
    """Website /jawab sach mein khulta hai? (live hone tak video/description Telegram + home par bhejte hain - 404 kabhi nahi)"""
    return bool(state.get("jawab_live"))


LIVE_MARKER = "आज के सवालों के सही जवाब"


def _live_once():
    """/jawab sach mein jawab-page hai? status 200 + html + marker + 'Page nahi mila' nahi (soft-404 pakadta hai). cache-bust ke saath."""
    import requests
    import time as _t
    try:
        r = requests.get(f"{SITE}{PAGE}?_={int(_t.time())}", timeout=20, allow_redirects=True,
                         headers={"Cache-Control": "no-cache", "User-Agent": "SabhisaabBot-Live/1.0"})
        return live_ok(r.status_code, r.headers.get("content-type", ""), r.text)
    except Exception:
        return False


def live_ok(status, ctype, body):
    """Alag function taaki bina network test ho sake."""
    body = body or ""
    return (status == 200 and "text/html" in (ctype or "").lower() and LIVE_MARKER in body
            and "Page nahi mila" not in body)


def check_live():
    import time as _t
    ok = _live_once()
    if not ok:                                  # ek chhoti galti se link na badle: 20 sec baad ek baar aur
        _t.sleep(20)
        ok = _live_once()
    state.put("jawab_live", ok)
    state.put("jawab_live_at", _t.time())
    return ok


def answer_url(code, platform=None, brand=None):
    """v2.5.2: platform + channel + code ka UTM (GA4 mein 'kaunsi video se traffic aaya'). Instagram par kabhi nahi (niyam)."""
    if not live():
        return TG_LINK
    if platform and platform != "instagram":
        q = f"?utm_source={platform}&utm_medium=answer" + (f"&utm_campaign={brand}" if brand else "") + f"&utm_content=c{code}"
        return f"{SITE}{PAGE}{q}#c{code}"
    return f"{SITE}{PAGE}#c{code}"


def strip_reveal(script):
    """Video se jawab hatao: 'सही जवाब'/✅ wala scene aur uske baad sab -> ek CTA scene. Pehle ke scene mein jawab na bole."""
    if not (on() and script.get("puzzle_options") and script.get("puzzle_answer")):
        return script
    ans = str(script["puzzle_answer"]).strip()
    code = code_for(script)
    script["reel_code"] = code
    sc = list(script.get("scenes") or [])
    cut = None
    for i, s in enumerate(sc):
        t = f"{s.get('show', '')} {s.get('say', '')}"
        from .design import REVEAL_RX
        if i > 0 and (REVEAL_RX.search(s.get("show", "")) or REVEAL_RX.search(s.get("say", "")) or "jawab hai" in t.lower()
                      or "जवाब है" in t or "उत्तर है" in t or "answer is" in t.lower() or
                      (len(ans) >= 3 and ans in t and i >= 2)):
            cut = i
            break
    keep = sc[:cut] if cut else sc[:-1] if len(sc) > 3 else sc
    if not script.get("puzzle_kind"):             # Gemini quiz: QUIZ FORMAT = 1 hook, 2 sawal+vikalp, 3 sochne ka samay, 4+ jawab
        keep = keep[:3]                           # (jawab shabdon mein bhi ho sakta hai - 'चार सौ बीस रुपये') -> 3 ke baad sab hatao
    keep = [s for s in keep if not (len(ans) >= 3 and ans in s.get("say", "") and keep.index(s) >= 2)]
    where = "sabhisaab.com/jawab • टेलीग्राम: t.me/sabhisaab" if live() else "टेलीग्राम t.me/sabhisaab पर"
    keep.append({"show": f"अपना जवाब कमेंट करो! सही जवाब (कोड #{code}): {where}",
                 "say": "अपना जवाब कमेंट में लिखो। सही जवाब हमारी वेबसाइट और टेलीग्राम पर है, लिंक डिस्क्रिप्शन या बायो में है।",
                 "answer_cta": True})
    script["scenes"] = keep
    script["answer_offsite"] = True
    q = script.get("puzzle_q") or script.get("title", "")
    script["description"] = (f"{q}\n\nअपना जवाब कमेंट में लिखें! सही जवाब (कोड #{code}) हमारी वेबसाइट और टेलीग्राम पर - "
                             "लिंक ऊपर/बायो में।")     # description mein jawab nahi (warna website aane ki wajah khatam)
    return script


def desc_line(meta, platform):
    """Har platform ki pehli line: jawab ka link (jahan click hota hai)."""
    if not meta.get("answer_offsite"):
        return ""
    code = meta.get("reel_code") or code_for(meta)
    if platform == "instagram":
        return (f"✅ सही जवाब (कोड #{code}): बायो के लिंक में → sabhisaab.com/jawab | टेलीग्राम: @sabhisaab" if live()
                else f"✅ सही जवाब (कोड #{code}): टेलीग्राम @sabhisaab पर (बायो में लिंक)")
    if not live():
        return f"✅ सही जवाब (कोड #{code}): {TG_LINK}"
    return f"✅ सही जवाब (कोड #{code}): {answer_url(code, platform, meta.get('brand'))} | टेलीग्राम: {TG_LINK}"


def record(meta, links=None):
    """Upload ke baad: jawab register + Telegram + website 'dirty'."""
    if not meta.get("answer_offsite"):
        return None
    code = meta.get("reel_code") or code_for(meta)
    e = {"code": code, "brand": meta.get("brand"), "bname": BRANDS.get(meta.get("brand"), {}).get("name", ""),
         "date": str(datetime.date.today()), "q": meta.get("puzzle_q", "")[:220], "ans": str(meta.get("puzzle_answer", ""))[:120],
         "exp": (meta.get("puzzle_exp") or "")[:300], "page": meta.get("page") or "/",
         "yt": (links or {}).get("youtube", ""), "kind": meta.get("puzzle_kind", ""),
         "opts": [str(o)[:100] for o in (meta.get("puzzle_options") or [])][:4]}
    lst = list(state.get("answer_key") or [])
    # v2.5.2: purani entry kabhi overwrite nahi. Wahi code + wahi sawal = dobara record (badlo); wahi code + ALAG sawal =
    # purani video ka code bhi sahi rahe, isliye dono rakho (page par alag anchor).
    same = [i for i, x in enumerate(lst) if x.get("code") == code and x.get("q") == e["q"]]
    if same:
        e["aid"] = lst[same[0]].get("aid") or code
        lst[same[0]] = e
    else:
        clash = sum(1 for x in lst if x.get("code") == code)
        e["aid"] = code if not clash else f"{code}-{clash + 1}"
        lst.append(e)
    lst = lst[-RETAIN:]
    for x in lst[:-KEEP]:                      # purani entry halki (archive mein sirf code/tarikh/sawal/jawab dikhta hai) - state.json bhari na ho
        x.pop("exp", None)
        x.pop("opts", None)
        x["q"] = str(x.get("q", ""))[:110]
    state.put("answer_key", lst)
    state.put("answer_dirty", True)
    if state.get("answer_digest"):               # v2.5.2: owner ne digest chalu kiya - shaam ko ek message (tick)
        state.update("digest_pending", lambda l: ((l or []) + [e])[-40:], [])
        return e
    try:
        post_telegram(e)
    except Exception as ex:
        log(f"answer tg: {ex}")
    return e


def poll_args(e):
    """Telegram quiz poll ke liye (sawal<=300, option<=100, 2-10 option, explanation<=200) ya None."""
    opts = [str(o)[:100] for o in (e.get("opts") or [])]
    ans = str(e.get("ans", ""))[:100]
    q = str(e.get("q", ""))
    if not (2 <= len(opts) <= 10) or ans not in opts or not q or len(q) > 300 or len(set(opts)) != len(opts):
        return None
    tail = f" {SITE}{PAGE}#c{e.get('aid') or e['code']}"
    exp = (str(e.get("exp") or "")[:200 - len(tail) - 1].rstrip() + tail).strip()[:200]
    return {"question": q, "options": opts, "correct": opts.index(ans), "explanation": exp}


def send_poll(e):
    """Native quiz poll (roz max 2). Fail ho to False (purana text-post chalega)."""
    from .config import TG_CHANNEL
    a = poll_args(e)
    if not a:
        return False
    day = str(datetime.date.today())
    if state.get("poll_day") != day:
        state.put("poll_day", day)
        state.put("poll_n", 0)
    if state.get("poll_n", 0) >= 2:
        return False
    r = tg.call("sendPoll", {"chat_id": TG_CHANNEL, "question": a["question"], "options": json.dumps(a["options"], ensure_ascii=False),
                             "type": "quiz", "correct_option_id": a["correct"], "explanation": a["explanation"], "is_anonymous": "true"})
    if r:
        state.put("poll_n", state.get("poll_n", 0) + 1)
        return True
    return False


def post_telegram(e):
    from .config import TG_CHANNEL
    if state.get("answer_poll"):
        try:
            if send_poll(e):
                return
        except Exception as ex:
            log(f"poll: {ex}")
    rows = ([[{"text": "🌐 Saare jawab (website)", "url": f"{SITE}{PAGE}?utm_source=telegram&utm_medium=answer#c{e.get('aid') or e['code']}"}]]
            if live() else [[{"text": "🌐 Free calculator (website)", "url": f"{SITE}/?utm_source=telegram&utm_medium=answer"}]])
    if e.get("yt"):
        rows.append([{"text": "▶️ Sawal wali video", "url": e["yt"]}])
    txt = (f"✅ JAWAB | {e['bname']} | कोड #{e['code']}\n\n❓ {e['q']}\n\n🎯 सही जवाब: {e['ans']}"
           + (f"\n💡 {e['exp']}" if e.get("exp") else "") + "\n\nरोज़ नए सवाल - चैनल से जुड़े रहें 🙏")
    tg.call("sendMessage", {"chat_id": TG_CHANNEL, "text": txt[:3900], "disable_web_page_preview": "true",
                            "reply_markup": json.dumps({"inline_keyboard": rows})})


# ---------------- website /jawab page (site ka apna template) ----------------
def _esc(s):
    return H.escape(str(s or ""), quote=True)


def share_link(e):
    """WhatsApp par dost ko sawal bhejo (sirf link - koi data collect nahi)."""
    import urllib.parse as _u
    txt = f"{str(e.get('q', ''))[:140]}\nSahi jawab aur wajah: {SITE}{PAGE}#c{e.get('aid') or e.get('code')}"
    return f'<p class="upd"><a href="https://wa.me/?text={_u.quote(txt)}" rel="noopener">WhatsApp par dost ko bhejein</a></p>'


def build_page():
    """site/about.html ke template se /jawab - title<=60, description 95-165, ek H1, canonical, og:url (site audit niyam)."""
    from .website import DIR
    tpl = (DIR / "site" / "about.html").read_text(encoding="utf-8")
    full_list = list(reversed(state.get("answer_key") or []))
    lst = full_list[:KEEP]
    old = full_list[KEEP:KEEP + ARCHIVE]
    today = str(datetime.date.today())
    title = "आज के सवालों के सही जवाब (Answer Key) - Sab Hisaab"
    desc = ("Sab Hisaab ki reels ke roz ke sawalon ke sahi jawab, code ke saath - dimagi paheli, GK, paisa aur pahadi sawal. "
            "Free, bina login.")
    blocks = []
    seen_brand = set()
    for i_, e in enumerate(lst):
        pg = e.get("page") or "/"
        tool = (f'<p class="upd">Isse juda free tool: <a href="{_esc(pg)}">{_esc(SITE + pg)}</a></p>'
                if pg not in ("/", "") else "")
        rt = related_tools(e)
        if rt and pg in ("/", ""):
            tool = ('<p class="upd">Isse juda free tools: ' + " · ".join(f'<a href="/{sl}">{_esc(nm)}</a>' for sl, nm in rt) + "</p>")
        blocks.append(
            (f'<span id="b-{_esc(e.get("brand"))}"></span>' if e.get("brand") and e.get("brand") not in seen_brand and not seen_brand.add(e.get("brand")) else "")
            + f'<section id="c{_esc(e.get("aid") or e["code"])}" style="background:#fff;border:1px solid #E1E7E8;border-radius:14px;padding:16px;'
            f'margin:14px 0"><p class="upd">{_esc(e["date"])} | {_esc(e["bname"])} | कोड #{_esc(e["code"])}</p>'
            f'<h3>{_esc(e["q"])}</h3><p><b>सही जवाब: {_esc(e["ans"])}</b></p>'
            + (f'<p>{_esc(e["exp"])}</p>' if e.get("exp") else "") + tool + share_link(e)
            + (f'<p class="upd"><a href="#c{_esc((lst[i_ + 1].get("aid") or lst[i_ + 1]["code"]))}">Agla jawab ↓</a></p>' if i_ + 1 < len(lst) else "")
            + "</section>")
    from .config import LINKS, WHATSAPP, TELEGRAM, PINTEREST
    chan = ("<h2>Hamare channel</h2><p>" + " · ".join(
        f'<a href="{_esc(LINKS[b]["youtube"])}" rel="noopener">{_esc(BRANDS[b]["name"])} (YouTube)</a>' for b in LINKS if b in BRANDS)
        + f' · <a href="{_esc(TELEGRAM)}" rel="noopener">Telegram</a> · <a href="{_esc(WHATSAPP)}" rel="noopener">WhatsApp channel</a>'
        f' · <a href="{_esc(PINTEREST)}" rel="noopener">Pinterest</a></p>')
    rows = "".join(f"<tr><td>#{_esc(e['code'])}</td><td>{_esc(e['bname'])}</td><td>{_esc(e['ans'])}</td></tr>" for e in lst[:20])
    table = ('<h2>Aaj ke jawab ek nazar mein</h2><div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse">'
             '<thead><tr><th>Code</th><th>Channel</th><th>Sahi jawab</th></tr></thead><tbody>'
             + (rows or "<tr><td>-</td><td>-</td><td>Jaldi aa rahe hain</td></tr>") + "</tbody></table></div>")
    arch = ""
    if old:
        arch = ('<h2>Purane jawab (code se dhoondhein)</h2><p class="upd">Purani reels ka code yahan bhi milega.</p><ul>' + "".join(
            f'<li id="c{_esc(e.get("aid") or e["code"])}"><b>#{_esc(e["code"])}</b> · {_esc(e["date"])} · {_esc(e["bname"])} - '
            f'{_esc(e["q"][:110])} → <b>{_esc(e["ans"])}</b></li>' for e in old) + "</ul>")
    bn = {}
    for e in lst:
        if e.get("brand") and e["brand"] not in bn:
            bn[e["brand"]] = e["bname"]
    nav = ('<p class="upd">Channel ke hisaab se dekhein: ' + " · ".join(f'<a href="#b-{_esc(b)}">{_esc(n)}</a>' for b, n in bn.items()) + "</p>") if len(bn) > 1 else ""
    guide = ('<h2>Ye page kaise kaam karta hai</h2>'
             '<p>Sab Hisaab ke chaar channel hain: Suno Natak (dimagi paheli aur kahani), Sab Hisaab Money (paisa, bachat aur '
             'ganit), Labh Lo Deals (discount aur shopping ka hisaab) aur Pahadi Hisaab (Uttarakhand ki GK, purane pahadi shabd '
             'aur parv). Har channel par roz do naye sawal aate hain. Video mein sawal, chaar vikalp aur paanch second ka samay '
             'hota hai, taaki aap khud sochkar comment mein apna jawab likh sakein. Sahi jawab aur uski chhoti si samajh is page '
             'par aati hai, video ke code ke saath.</p>'
             '<h2>Code se apna sawal kaise dhoondhein</h2>'
             '<p>Har video mein ek code likha hota hai, jaise #4827. Upar ki table mein wahi code dhoondhein, ya neeche us code wale '
             'dabbe tak scroll karein. Har dabbe mein tarikh, channel ka naam, poora sawal, sahi jawab aur jahan ho sake wahan us '
             'vishay ka free calculator ya guide ka link hai, taaki aap sirf jawab hi nahi, poora hisaab bhi samajh sakein.</p>'
             '<h2>Jawab kaise jaanche jaate hain</h2>'
             '<p>Ganit aur tark wale sawal (sudoku, series, ghadi, calendar, umar, disha) ka jawab ganit se nikalta hai, isliye '
             'woh hamesha ek hi sahi hota hai. GK, shabdon ke arth aur pahadi sawal ko hum pakke srot se milane ki poori koshish karte hain. '
             'Phir bhi insaan se galti ho sakti hai, isliye galti dikhe to hamein zaroor batayein. Hum koshish karte hain ki koi sawal kisi bhi channel par '
             'dobara na aaye. Phir bhi koi galti dikhe to contact page se batayein, hum turant theek karte hain.</p>'
             '<h2>Kaun se sawal aate hain</h2>'
             '<p>Dimag hilane wali paheliyan, ulte-pulte shabd aur muhavre, purane zamaane ke naap aur sikke, shuddh Hindi naam, '
             'sudoku, sankhya series, coding-decoding, paise aur discount ke ganit, aur Uttarakhand ki GK. Sawal family ke saath '
             'dekhne layak hote hain aur kisi ko gumraah karne wale aankde nahi hote.</p>'
             '<h2>Paheli jaldi hal karne ke 5 aasaan tareeke</h2>'
             '<p><b>1. Sawal do baar padhein.</b> Zyaadatar galti jaldbaazi mein hoti hai. Sawal mein chhupa shabd jaise "pehle", '
             '"baad mein", "kul" ya "bacha hua" poora matlab badal deta hai.</p>'
             '<p><b>2. Vikalp se ulta chalein.</b> Chaaron vikalp ko sawal mein rakh kar dekhein. Jo vikalp sharton ko poora na kare, '
             'use hata dein. Aksar do vikalp turant hat jaate hain aur faisla aasaan ho jaata hai.</p>'
             '<p><b>3. Chhote number se aazmaayein.</b> Discount, byaj ya percentage ke sawal mein pehle 100 rupaye maan kar hisaab '
             'lagaayein. Pattern samajh aate hi asli number par wahi niyam lagaayein.</p>'
             '<p><b>4. Series mein farak dekhein.</b> Lagataar do sankhyaon ka farak, phir farak ka farak dekhein. Gunaa, varg (square) '
             'aur pichhli do sankhyaon ka jod sabse aam pattern hain.</p>'
             '<p><b>5. Shabd wale sawal mein jad (root) dhoondhein.</b> Shabd ko tod kar dekhein: "anu" matlab baad mein, "agra" '
             'matlab aage, "a" ya "an" matlab nahi. Isse anjaan shabd ka arth bhi andaaze se sahi nikal aata hai.</p>'
             '<h2>Aksar pooche jaane wale sawal</h2>'
             '<p><b>Kya jawab dekhne ke liye login ya follow zaroori hai?</b> Nahi. Ye page sabke liye free hai, bina login, bina '
             'kisi shart ke. Channel follow karna aapki marzi hai; usse bas roz ke naye sawal aap tak pehle pahunchte hain.</p>'
             '<p><b>Jawab video mein kyun nahi hota?</b> Taaki aap pehle khud sochein aur comment mein apna jawab likhein. Sochne '
             'se dimag ki kasrat hoti hai. Uske baad yahan code se sahi jawab aur uski wajah dekh sakte hain.</p>'
             '<p><b>Purane sawal kahan milenge?</b> Naye jawab sabse upar poore dabbon mein aate hain. Usse purane jawab neeche '
             '"Purane jawab" list mein code ke saath kai mahine tak rehte hain, to purani reel ka code bhi yahan mil jaata hai.</p>'
             '<p><b>Mera jawab alag tha, kya main galat hoon?</b> Har jawab ke saath uski chhoti si wajah likhi hai. Use padhein. '
             'Agar phir bhi lagta hai ki hamara jawab galat hai to contact page se batayein. Sahi baat saabit ho to hum jawab '
             'turant badalte hain aur wahi video par comment mein bhi bata dete hain.</p>'
             '<p><b>Kya ye sawal kisi pariksha ki taiyari ke liye kaam aate hain?</b> Ye sawal general knowledge, ganit ki '
             'aadaton aur tark ko majboot karte hain. Kisi pariksha ke liye hamesha uske official syllabus aur srot se padhai karein; '
             'ye page uska vikalp nahi, roz ki halki kasrat hai.</p>'
             '<p><b>Telegram channel par kya milta hai?</b> Wahan har naye video ke saath uska sahi jawab, video ka link aur roz '
             'ke naye sawal milte hain. Channel mein koi spam ya paid promotion nahi bheja jaata.</p>')
    main = (f'<main><div class="wrap"><h1>आज के सवालों के सही जवाब</h1>'
            f'<p class="upd">Aakhri badlaav: {today}</p>'
            '<p>Hamari reels (YouTube, Instagram, Facebook, Threads, Pinterest) mein roz naye sawal aate hain. Video mein jo '
            '<b>code</b> dikhta hai, wahi code yahan dhoondhein. Har jawab pehle ganit, tark ya pakke srot se jaancha jaata hai. '
            f'Roz naye sawal ke liye Telegram se judein: <a href="{TG_LINK}" rel="noopener">{TG_LINK}</a>.</p>'
            + table + nav + ("".join(blocks) or "<p>Aaj ke jawab jaldi aa rahe hain.</p>") + arch + guide +
            chan + '<h2>Sab Hisaab ke kaam ke free tools</h2><p>Paise ka hisaab: <a href="/sip-calculator">SIP</a> · <a href="/emi-calculator">EMI</a> · '
            '<a href="/discount-calculator">Discount</a> · <a href="/percentage-calculator">Percentage</a>. Roz ke kaam: <a href="/age-calculator">Umar</a> · '
            '<a href="/date-difference-calculator">Do tareekh ka farak</a>. Uttarakhand: <a href="/nali-mutthi-converter">Nali-Mutthi</a>. '
            'Saari categories: <a href="/nivesh-calculators">Nivesh</a> · <a href="/loan-tax-calculators">Loan &amp; Tax</a> · '
            '<a href="/rozana-calculators">Rozana</a> · <a href="/guides">Guides</a> · <a href="/articles">Lekh</a>.</p>'
            '<p class="upd">Galti dikhe to <a href="/contact">hamein batayein</a> - hum turant theek karte hain. '
            '<a href="/">Saare free calculator</a>.</p></div></main>')
    s = tpl
    s = re.sub(r"<title>.*?</title>", lambda m: f"<title>{_esc(title)}</title>", s, count=1, flags=re.S)
    s = re.sub(r'<meta name="description" content="[^"]*"', lambda m: f'<meta name="description" content="{_esc(desc)}"', s, count=1)
    s = re.sub(r'(<meta (?:name|property)="(?:twitter:title|og:title)" content=")[^"]*"', lambda m: m.group(1) + _esc(title) + '"', s)
    s = re.sub(r'(<meta (?:name|property)="(?:twitter:description|og:description)" content=")[^"]*"', lambda m: m.group(1) + _esc(desc) + '"', s)
    s = s.replace(f'{SITE}/about"', f'{SITE}{PAGE}"').replace(f"{SITE}/about'", f"{SITE}{PAGE}'")
    s = re.sub(r'"dateModified"\s*:\s*"[^"]*"', lambda m: f'"dateModified": "{today}"', s)
    s = re.sub(r"<main\b.*?</main>", lambda m: main, s, count=1, flags=re.S)
    return s


def _inbound_links():
    """3 maujooda page (links/about/articles...) + homepage mein ek chhoti line '/jawab' ki - sirf jab pehle se na ho."""
    from .website import DIR
    out = {}
    line = ('<p class="upd">Reels ke sawalon ke sahi jawab (code ke saath): '
            '<a href="/jawab">aaj ke jawab dekhein</a>.</p>')
    for fn in ("links.html", "about.html", "articles.html", "contact.html", "index.html"):
        f = DIR / "site" / fn
        if fn != "index.html" and len(out) >= 3:
            continue
        if not f.exists():
            continue
        s = f.read_text(encoding="utf-8")
        if 'href="/jawab"' in s:
            if fn != "index.html":
                out[fn] = None
            continue
        i = s.rfind("</main>")
        if i < 0:
            continue
        out[fn] = s[:i] + line + s[i:]
    return {k: v for k, v in out.items() if v}


def _sitemap_with_jawab():
    """site/sitemap.xml mein /jawab (daily) - sirf jab file ho aur /jawab pehle se na ho. Baaki file jaisi hai waisi."""
    from .website import DIR
    f = DIR / "site" / "sitemap.xml"
    if not f.exists():
        return None
    sm = f.read_text(encoding="utf-8")
    if f"<loc>{SITE}{PAGE}</loc>" in sm or "</urlset>" not in sm:
        return None
    ent = (f"  <url><loc>{SITE}{PAGE}</loc><lastmod>{datetime.date.today()}</lastmod>"
           "<changefreq>daily</changefreq></url>\n")
    return sm.replace("</urlset>", ent + "</urlset>", 1)


def repo_page_ok():
    """VM ke site repo mein jawab.html maujood aur asli jawab-page hai? (None = repo nahi mila)"""
    try:
        from .website import DIR
        f = DIR / "site" / "jawab.html"
        if not f.exists():
            return False
        t = f.read_text(encoding="utf-8", errors="ignore")
        return LIVE_MARKER in t and "Page nahi mila" not in t
    except Exception:
        return None


def reconcile():
    """v2.5.2: kharab/gayab purana page apne aap badle. Repo mein jawab.html na ho ya kharab ho to page dobara banega."""
    if not state.get("jawab_site_on"):
        return "off"
    ok = repo_page_ok()
    if ok is False and (state.get("answer_key") or []):
        state.put("jawab_hash", "")
        state.put("answer_dirty", True)
        state.put("jawab_pub_at", 0)
        return "repo mein page nahi/kharab - dobara banega"
    return "ok"


def tick():
    """Bot ka loop yahi bulata hai. Live-check: nahi chal raha to 20 min, chal raha ho to 1 ghanta. Badlaav par Telegram."""
    import time as _t
    if not state.get("jawab_site_on") and not state.get("answer_digest"):
        return
    if state.get("jawab_site_on") and state.get("jawab_reconciled") != "2.5.2":          # install ke baad ek baar
        state.put("jawab_reconciled", "2.5.2")
        log(f"jawab reconcile: {reconcile()}")
    try:                                              # digest: chalu ho to roz 20:30 IST ke baad ek baar
        from .config import IST
        nw = datetime.datetime.now(IST)
        if state.get("answer_digest") and nw.strftime("%H:%M") >= "20:30" and state.get("digest_day") != str(nw.date()):
            state.put("digest_day", str(nw.date()))
            log(f"digest: {send_digest()} jawab")
    except Exception as ex:
        log(f"digest: {ex}")
    try:                                              # Instagram Story link-sticker yaad (API sticker nahi deta): roz 21:00 IST, ek message
        from .config import IST as _I
        n2 = datetime.datetime.now(_I)
        if n2.strftime("%H:%M") >= "21:00" and state.get("story_rem_day") != str(n2.date()) and live():
            state.put("story_rem_day", str(n2.date()))
            today_ = [e for e in (state.get("answer_key") or []) if e.get("date") == str(n2.date())]
            if today_:
                tg.say("📌 Story link-sticker yaad (Instagram API nahi deta - aap khud lagayein; reel ke baad Story → Link sticker):\n"
                       + "\n".join(f"#{e['code']} ({e.get('bname', '')}): {SITE}{PAGE}#c{e.get('aid') or e['code']}" for e in today_[:10]))
    except Exception as ex:
        log(f"story reminder: {ex}")
    try:                                              # har 6 ghante: live page mein naye jawab ke dabbe sach mein hain? (chup rehta hai agar sab theek)
        if state.get("jawab_live") and _t.time() - state.get("cov_at", 0) > 6 * 3600 and not state.get("answer_dirty"):
            state.put("cov_at", _t.time())
            miss = coverage_check()
            if miss:
                n_ = state.get("cov_miss_n", 0) + 1
                state.put("cov_miss_n", n_)
                state.put("jawab_hash", "")
                state.put("answer_dirty", True)
                if n_ >= 2:
                    tg.alert("yellow", f"/jawab par {len(miss)} naye jawab ke dabbe nahi dikh rahe (codes: {', '.join(map(str, miss[:6]))}). "
                                       "Bot ne page dobara banane ko laga diya; phir bhi na dikhe to 'canary' likhkar screenshot Claude ko.")
            else:
                state.put("cov_miss_n", 0)
    except Exception as ex:
        log(f"coverage: {ex}")
    gap = 3600 if state.get("jawab_live") else 20 * 60
    if _t.time() - state.get("jawab_check_at", 0) <= gap:
        return
    state.put("jawab_check_at", _t.time())
    was = live()
    now_ = check_live()
    if now_ and not was:
        tg.say("🌐 https://sabhisaab.com/jawab ab LIVE hai (page ka asli text mila) - aage ki reel/post mein jawab ka link yahi jayega.")
        state.put("jawab_fail_alerted", False)
    elif was and not now_:
        tg.alert("yellow", "🌐 /jawab page nahi khul raha ya galat page (404/soft-404) - tab tak link Telegram par bhej raha hoon.")
    if not now_:
        log(f"jawab live nahi: {reconcile()}")
        # repo mein page theek hai par live nahi: deploy ruka/cache ho sakta hai - 6 ghante mein sirf ek baar naya deploy
        if repo_page_ok() and not state.get("answer_dirty") and _t.time() - state.get("jawab_redeploy_at", 0) > 6 * 3600:
            state.put("jawab_redeploy_at", _t.time())
            state.put("deploy_due", _t.time() + 120)
            log("jawab: repo mein page hai par live nahi - deploy dobara")


def digest_text(items):
    """Ek message mein sab jawab (Telegram 4096 seema ke andar)."""
    out = ["✅ AAJ KE JAWAB (roz ke sawal - code ke saath)\n"]
    for e in items:
        out.append(f"#{e['code']} | {e.get('bname', '')}\n❓ {e['q'][:120]}\n🎯 {e['ans']}" + (f"\n💡 {e['exp'][:100]}" if e.get("exp") else "") + "\n")
    out.append("रोज़ नए सवाल - चैनल से जुड़े रहें 🙏")
    return "\n".join(out)[:3900]


def send_digest():
    """Roz ek baar: pending jawab ek message mein + website button. Khaali ho to kuch nahi."""
    from .config import TG_CHANNEL
    items = state.get("digest_pending") or []
    if not items:
        return 0
    rows = ([[{"text": "🌐 Saare jawab (website)", "url": f"{SITE}{PAGE}?utm_source=telegram&utm_medium=digest"}]]
            if live() else [[{"text": "🌐 Free calculator (website)", "url": f"{SITE}/?utm_source=telegram&utm_medium=digest"}]])
    for i in range(0, len(items), 6):
        tg.call("sendMessage", {"chat_id": TG_CHANNEL, "text": digest_text(items[i:i + 6]), "disable_web_page_preview": "true",
                                "reply_markup": json.dumps({"inline_keyboard": rows})})
    state.put("digest_pending", [])
    return len(items)


def coverage_check(n=25):
    """Live /jawab mein sabse naye n jawab ke dabbe (id=c<aid>) maujood? -> gayab ki list (network fail par None)."""
    import time as _t
    import requests
    try:
        r = requests.get(f"{SITE}{PAGE}?_={int(_t.time())}", timeout=25, headers={"Cache-Control": "no-cache", "User-Agent": "SabhisaabBot-Coverage/1.0"})
        if r.status_code != 200:
            return None
        body = r.text
    except Exception:
        return None
    lst = list(reversed(state.get("answer_key") or []))[:n]
    return [e.get("aid") or e["code"] for e in lst if f'id="c{e.get("aid") or e["code"]}"' not in body]


def publish_site(force=False):
    """Badla ho to /jawab -> website. v2.5.2: audit asli gate (force=False) - fail ho to page repo mein nahi rehta,
    poora error Telegram par aur state mein (jawab_last_error). Owner ki ek baar ki dohri pushti zaroori."""
    if not state.get("jawab_site_on"):
        return "jawab website: owner ki pushti baaki ('jawab website chalu')"
    if not (state.get("answer_dirty") or force):
        return "jawab website: koi naya jawab nahi"
    from . import website
    try:
        page = build_page()
    except Exception as ex:                      # page ban hi na paye to saaf wajah Telegram par (chup nahi)
        state.put("jawab_last_error", f"build_page: {ex}"[:900])
        tg.alert("yellow", f"Jawab page ban nahi paya: {str(ex)[:300]}")
        return f"jawab website: build fail {str(ex)[:100]}"
    dig = hashlib.md5(page.encode()).hexdigest()
    if state.get("jawab_hash") == dig and not force:
        state.put("answer_dirty", False)
        return "jawab website: koi badlaav nahi"
    links = _inbound_links()
    sm = _sitemap_with_jawab()

    def _zip(with_index):
        z = DATA / "jawab.zip"
        with zipfile.ZipFile(z, "w") as zz:
            zz.writestr("site/jawab.html", page)
            for fn, body in links.items():                # site niyam: har page par kam se kam 3 andar ke link
                if fn == "index.html" and not with_index:
                    continue
                zz.writestr(f"site/{fn}", body)
            if sm:
                zz.writestr("site/sitemap.xml", sm)
        return z
    z = _zip(True)
    r = website.apply_zip(z, force=False)                 # audit asli gate
    z.unlink(missing_ok=True)
    if not str(r).startswith("✅") and "index.html" in links:   # homepage ka badlaav audit mein atka to sirf /jawab + baaki link
        z = _zip(False)
        r2 = website.apply_zip(z, force=False)
        z.unlink(missing_ok=True)
        if str(r2).startswith("✅"):
            r = r2
    if str(r).startswith("✅"):
        state.put("jawab_hash", dig)
        state.put("answer_dirty", False)
        state.put("jawab_check_at", 0)            # deploy ke kuch min baad live jaancha jaayega
        state.put("jawab_last_error", "")
    else:
        state.put("jawab_last_error", str(r)[:900])
        tg.alert("yellow", "✅ Jawab Telegram par gaye; website ka /jawab page audit/ZIP mein ruka (koi toota page live nahi):\n" + str(r)[:900])
    return f"jawab website: {str(r)[:150]}"
