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
KEEP = 8              # v2.9.4 (owner 10 baar kaha): page par sirf aakhri 8 video ke jawab; baaki SAB khoj (register) se - page hamesha halka
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


import re as _re_
REVEAL_RX_SAFE = _re_.compile(r"सही जवाब है|जवाब है")


_FILLER = set("पाँच पांच 5 सेकंड सेकेंड सोचिए सोचो सोचें और अपना जवाब उत्तर कमेंट में लिखिए लिखो लिखें बताइए बताओ क्या आपको इसका सही पता है "
              "कीजिए करो करें समय शुरू अब चलिए तो ज़रा जरा ध्यान से बस आपके पास हैं".split())


def _is_filler(say):
    """Sirf 'sochiye / 5 second / comment mein likhiye' jaisi baat? (koi sanket ya nayi jaankari nahi) -> bool"""
    ws = [w.strip(".,!?।:;-–—…'\"()") for w in str(say or "").split()]
    left = [w for w in ws if w and w not in _FILLER]
    return bool(ws) and len(left) <= 1


def think_hold(script):
    """Sochne ki chuppi (second) SAWAL ke hisaab se: yaad wala GK/shabd 1.0 | ganit/code/tark 2.5 | chitra wali paheli 3.0;
    lamba sawal +0.5. Seema 1.0-3.5. Video ki awaaz is dauran chup - dekhne wala sach mein soch sake."""
    q = str(script.get("puzzle_q") or "")
    if script.get("diagram"):
        h = 3.0
    elif re.search(r"[0-9=+×÷%₹]|[A-Z]{3,}", q):
        h = 2.5
    else:
        h = 1.0
    if len(q) > 90:
        h += 0.5
    return max(1.0, min(3.5, h))


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
    for s in keep:                                # v2.7.3: '(संकेत: ...)' jawab ki taraf ishara - hatao
        for k_ in ("show", "say"):
            if s.get(k_):
                s[k_] = re.sub(r"\s*[(（]\s*(?:संकेत|हिंट|hint|इशारा)[^)）]*[)）]", "", s[k_], flags=re.I).strip()
    opts_ = [str(o) for o in script.get("puzzle_options") or []]
    if len(opts_) == 4 and len(keep) >= 3:          # v3.2.0 (owner 13 Nov): har video alag 'jawab-tareeka' (50-50 / poora / ...)
        try:
            apply_mech(script, keep, opts_, ans)
        except Exception as e:
            log(f"vmech: {e}")
    where = "sabhisaab.com/jawab • टेलीग्राम: t.me/sabhisaab" if live() else "टेलीग्राम t.me/sabhisaab पर"
    try:                                          # v3.1.1 (owner: 'timing sawal ke hisaab se'): aakhri sawal-scene par ASLI sochne ki chuppi
        if state.get("think_hold_on", True) and keep and not keep[-1].get("answer_cta"):
            keep[-1] = dict(keep[-1], hold=think_hold(script))
    except Exception as e:
        log(f"think hold: {e}")
    keep.append({"show": f"अपना जवाब कमेंट कीजिए! सही जवाब (कोड #{code}): {where}",      # v3.1.1: poori video mein ek hi lehja (aap)
                 "say": "अपना जवाब कमेंट में लिखिए। सही जवाब बायो के लिंक पर।",      # v2.7.3: chhota (pehle ~10 sec khaali end)
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
    try:
        archive_add(e)                             # v2.8.0: zindagi bhar ka jawab-register (kabhi nahi mitta)
    except Exception as ex:
        log(f"jawab archive: {ex}")
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


JW_CSS = ("<style>.jw-tools{position:sticky;top:0;z-index:5;background:var(--bg,#F6F8F9);padding:8px 0}"
          ".jw-tools input{width:100%;max-width:520px;font-size:16px;padding:10px 12px;border:1px solid #C9D3D5;border-radius:10px}"
          ".jw-chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 0}.jw-chips button{border:1px solid #C9D3D5;background:#fff;"
          "border-radius:999px;padding:6px 12px;font-size:14px;cursor:pointer}.jw-chips button.on{background:#0F766E;color:#fff;"
          "border-color:#0F766E}.jw-tap button{display:block;width:100%;text-align:left;margin:6px 0;padding:10px 12px;font-size:15px;"
          "border:1px solid #C9D3D5;border-radius:10px;background:#fff;cursor:pointer}.jw-tap button.ok{background:#DCFCE7;"
          "border-color:#16A34A;font-weight:700}.jw-tap button.bad{background:#FEE2E2;border-color:#DC2626}.jw-sharebtn{border:1px solid "
          "#0F766E;color:#0F766E;background:#fff;border-radius:999px;padding:6px 14px;cursor:pointer}.jw-me button{border:1px solid #C9D3D5;background:#fff;border-radius:999px;padding:4px 10px;"
          "font-size:13px;cursor:pointer;margin:2px}.jw-wrap{overflow-x:auto;max-height:70vh;overflow-y:auto;border:1px solid #E1E7E8;border-radius:12px;"
          "background:#fff}table.jw{display:table!important;table-layout:auto;width:100%;border-collapse:collapse;font-size:14px;white-space:normal}"
          "table.jw thead{display:table-header-group}table.jw tbody{display:table-row-group}table.jw tr{display:table-row}"
          "table.jw th,table.jw td{display:table-cell}table.jw td.n{color:#8A979C;font-weight:400;width:1%}table.jw th,table.jw td{text-align:left;"
          "vertical-align:top;padding:8px 10px;border-bottom:1px solid #EDF1F2}table.jw th{position:sticky;top:0;background:#EDF1F2;"
          "white-space:nowrap}table.jw td:nth-child(2){white-space:nowrap;font-weight:600}table.jw td:nth-child(3){white-space:nowrap;"
          "color:#4F5D64}table.jw tr:target,section:target{background:#FFF7D6!important}@media(max-width:600px){table.jw "
          "td:nth-child(3),table.jw th:nth-child(3){display:none!important}}</style>")

JW_JS = ("<script>(function(){var q=document.getElementById('jq'),n=document.getElementById('jn'),z=document.getElementById('j0'),"
         "rows=[].slice.call(document.querySelectorAll('table.jw tbody tr')),b='';function f(){var t=(q.value||'').toLowerCase()"
         ".replace(/^#/,'').trim(),c=0;rows.forEach(function(r){var ok=(!b||r.getAttribute('data-b')===b)&&(!t||r.getAttribute('data-k')"
         ".indexOf(t)>=0);r.style.display=ok?'':'none';if(ok)c++});n.textContent=c+' jawab dikh rahe hain';z.hidden=c>0}"
         "q.addEventListener('input',f);[].slice.call(document.querySelectorAll('.jw-chips button')).forEach(function(x){x.addEventListener("
         "'click',function(){b=x.getAttribute('data-b');[].slice.call(document.querySelectorAll('.jw-chips button')).forEach(function(y)"
         "{y.className=y===x?'on':''});f()})});f()})();</script>")


JW_STREAK = ("<script>document.addEventListener('DOMContentLoaded',function(){var K='sh_jawab_streak',d;try{d=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){d={}}"
             "d.ok=d.ok||0;d.n=d.n||0;d.days=d.days||0;d.last=d.last||'';d.ids=d.ids||[];var b=document.getElementById('jwStreak');"
             "function show(){if(b)b.textContent=d.n?('🔥 Aapka hisaab: '+d.ok+'/'+d.n+' sahi · '+d.days+' din lagatar'):"
             "'🔥 Har jawab ke neeche bataiye aapka jawab sahi tha ya nahi - aapki streak isi phone par banegi'}"
             "function today(){var t=new Date();return t.getFullYear()+'-'+(t.getMonth()+1)+'-'+t.getDate()}"
             "[].slice.call(document.querySelectorAll('.jw-me')).forEach(function(p){var id=p.getAttribute('data-id');"
             "if(d.ids.indexOf(id)>=0){p.textContent='✔ Aapne is sawal ka hisaab de diya';return}"
             "[].slice.call(p.querySelectorAll('button')).forEach(function(x){x.addEventListener('click',function(){var t=today();"
             "try{d=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){d={}}d.ok=d.ok||0;d.n=d.n||0;d.days=d.days||0;d.last=d.last||'';d.ids=d.ids||[];"
             "if(d.last!==t){var y=new Date();y.setDate(y.getDate()-1);var ys=y.getFullYear()+'-'+(y.getMonth()+1)+'-'+y.getDate();"
             "d.days=(d.last===ys)?d.days+1:1;d.last=t}d.n++;if(x.getAttribute('data-r')==='1')d.ok++;d.ids=d.ids.concat([id]).slice(-300);"
             "try{localStorage.setItem(K,JSON.stringify(d))}catch(e){}p.textContent=x.getAttribute('data-r')==='1'?'🎉 Shabaash! Streak badhi':"
             "'👍 Koi baat nahi - agla sawal try karein';show()})})});show()});</script>")



def tap_ok(e):
    """v2.8.0: is jawab par 'tap karke socho' ban sakta hai? (4 vikalp + sahi unme ek hi baar)"""
    o = [str(x) for x in (e.get("opts") or [])]
    return len(o) == 4 and o.count(str(e.get("ans", ""))) == 1


def tap_block(e):
    """Sawal ke neeche A/B/C/D - pehle tap, phir neeche jawab (jawab kabhi lock nahi). Vote sirf ginti (votes.py)."""
    if not tap_ok(e):
        return ""
    o = [str(x) for x in e["opts"]]
    aid = _esc(e.get("aid") or e.get("code"))
    btns = "".join(f'<button type="button" data-o="{i}">{"ABCD"[i]}) {_esc(x)}</button>' for i, x in enumerate(o))
    return (f'<div class="jw-tap" data-id="{aid}" data-c="{_esc(e.get("code"))}" data-a="{o.index(str(e["ans"]))}">'
            f'<p class="upd">🤔 Pehle socho, phir tap karo (sahi jawab neeche likha hai):</p>{btns}<p class="upd jw-pct"></p><p class="upd jw-pcts"></p></div>')


def tap_js():
    """Tap + streak + asli % (30+ vote) + score card share. Sab browser mein; vote mein sirf code+vikalp jaata hai."""
    vu = ""
    try:
        from . import votes
        vu = votes.url() if state.get("votes_on") else ""
    except Exception:
        vu = ""
    return ("<script>document.addEventListener('DOMContentLoaded',function(){var VU=" + json.dumps(vu) + ",K='sh_jawab_streak',d;"
            "try{d=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){d={}}d.ok=d.ok||0;d.n=d.n||0;d.days=d.days||0;d.last=d.last||'';"
            "d.ids=d.ids||[];d.pick=d.pick||{};function sv(){try{localStorage.setItem(K,JSON.stringify(d))}catch(e){}}"
            "function td(x){return x.getFullYear()+'-'+(x.getMonth()+1)+'-'+x.getDate()}"
            "function mark(b,o){var a=+b.getAttribute('data-a');[].slice.call(b.querySelectorAll('button')).forEach(function(x){"
            "var i=+x.getAttribute('data-o');x.disabled=true;if(i===a)x.className='ok';else if(i===o)x.className='bad'})}"
            "var blocks=[].slice.call(document.querySelectorAll('.jw-tap'));blocks.forEach(function(b){var id=b.getAttribute('data-id');"
            "if(d.pick[id]!==undefined){mark(b,d.pick[id]);return}[].slice.call(b.querySelectorAll('button')).forEach(function(x){"
            "x.addEventListener('click',function(){var o=+x.getAttribute('data-o'),a=+b.getAttribute('data-a'),t=td(new Date());"
            "try{d=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){d={}}d.ok=d.ok||0;d.n=d.n||0;d.days=d.days||0;d.last=d.last||'';"
            "d.ids=d.ids||[];d.pick=d.pick||{};"
            "if(d.last!==t){var y=new Date();y.setDate(y.getDate()-1);d.days=(d.last===td(y))?d.days+1:1;d.last=t}d.n++;if(o===a)d.ok++;"
            "d.pick[id]=o;d.ids=d.ids.concat([id]).slice(-300);var ks=Object.keys(d.pick);if(ks.length>300)delete d.pick[ks[0]];sv();mark(b,o);"
            "var p=b.querySelector('.jw-pct');if(p)p.textContent=o===a?'🎉 Sahi! Streak badhi.':'👍 Koi baat nahi - sahi jawab hara dikh raha hai.';"
            "var s=document.getElementById('jwStreak');if(s)s.textContent='🔥 Aapka hisaab: '+d.ok+'/'+d.n+' sahi · '+d.days+' din lagatar';"
            "if(VU&&window.fetch){fetch(VU+'/v?c='+encodeURIComponent(b.getAttribute('data-c'))+'&o='+o,{method:'POST',mode:'cors'}).catch(function(){})}"
            "})})});"
            "if(VU&&window.fetch&&blocks.length){var cs=blocks.slice(0,60).map(function(b){return b.getAttribute('data-c')}).join(',');"
            "fetch(VU+'/p?c='+cs).then(function(r){return r.json()}).then(function(m){blocks.forEach(function(b){var a=m[b.getAttribute('data-c')];"
            "if(!a)return;var n=a.reduce(function(s,x){return s+x},0);var p=b.querySelector('.jw-pcts');if(p)"
            "p.textContent='📊 Ab tak '+n+' logon ne chuna: '+a.map(function(x,i){return 'ABCD'[i]+' '+Math.round(100*x/n)+'%'}).join(' · ')})"
            "}).catch(function(){})}"
            "var sb=document.getElementById('jwShare');if(sb)sb.addEventListener('click',function(){var c=document.createElement('canvas');"
            "c.width=1080;c.height=1080;var g=c.getContext('2d');var gr=g.createLinearGradient(0,0,1080,1080);gr.addColorStop(0,'#0F766E');"
            "gr.addColorStop(1,'#1E3A8A');g.fillStyle=gr;g.fillRect(0,0,1080,1080);g.fillStyle='#fff';g.textAlign='center';"
            "g.font='bold 64px sans-serif';g.fillText('Mera Sab Hisaab Score',540,300);g.font='bold 200px sans-serif';"
            "g.fillText(d.ok+'/'+d.n,540,560);g.font='bold 56px sans-serif';g.fillText(d.days+' din lagatar 🔥',540,690);"
            "g.font='44px sans-serif';g.fillText('Aap kitne sahi karoge? sabhisaab.com/jawab',540,900);"
            "c.toBlob(function(bl){var f=new File([bl],'sabhisaab-score.png',{type:'image/png'});"
            "if(navigator.canShare&&navigator.canShare({files:[f]})){navigator.share({files:[f],text:'Mera score '+d.ok+'/'+d.n+' - aap? https://sabhisaab.com/jawab'}).catch(function(){})}"
            "else{var a=document.createElement('a');a.href=URL.createObjectURL(bl);a.download='sabhisaab-score.png';a.click()}})})"
            "});</script>")



# ---------------- v2.8.0 (owner: '10-20 saal baad bhi reel dekhe to jawab mile'): ZINDAGI BHAR KA JAWAB-REGISTER ----------------
ARCH = DATA / "jawab_archive.jsonl"


def _arch_row(e):
    return {"c": str(e.get("code", "")), "a": str(e.get("aid") or e.get("code", "")), "d": str(e.get("date", "")),
            "b": str(e.get("bname", "")), "q": str(e.get("q", ""))[:220], "ans": str(e.get("ans", ""))[:120],
            "e": str(e.get("exp", ""))[:200]}


def _hfix(x):
    """v3.1.0: purani entry mein reh gayi likhai-galti (jaise 'परछਾਈ') padhte waqt hi theek - website/khoj par hamesha saaf Hindi."""
    try:
        from .hindifix import repair
        return repair(x) if isinstance(x, str) else x
    except Exception:
        return x


def archive_rows():
    try:
        rows = [json.loads(x) for x in ARCH.read_text(encoding="utf-8").splitlines() if x.strip()]
    except Exception:
        return []
    for r in rows:
        for k in ("q", "ans", "e"):
            if isinstance(r.get(k), str):
                r[k] = _hfix(r[k])
    return rows


def archive_add(e):
    """Har naya jawab ek baar (aid+sawal). Pehli baar: ab tak ke saare /jawab wale bhi."""
    rows = archive_rows()
    have = {(r["a"], r["q"]) for r in rows}
    new = []
    if not rows:
        for x in state.get("answer_key") or []:
            r = _arch_row(x)
            if r["q"] and (r["a"], r["q"]) not in have:
                have.add((r["a"], r["q"]))
                new.append(r)
    r = _arch_row(e)
    if r["q"] and (r["a"], r["q"]) not in have:
        new.append(r)
    if new:
        ARCH.parent.mkdir(parents=True, exist_ok=True)
        with open(ARCH, "a", encoding="utf-8") as f:
            for x in new:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")


def archive_import_codes():
    """v2.9.5 (pending: purani 3-ank code wali reels): puzzles.reel_codes (aakhri 800, jawab ke saath) -> zindagi bhar ka register,
    jo code register mein nahi. Sirf woh jinka jawab jaancha hua code mein hai. -> kitne jode"""
    rows = archive_rows()
    have = {r.get("c") for r in rows}
    new = []
    for code, v in (state.get("reel_codes") or {}).items():
        if not isinstance(v, dict) or str(code) in have or not v.get("q") or not v.get("ans"):
            continue
        b = v.get("brand", "")
        new.append({"c": str(code), "a": str(code), "d": str(v.get("t", "")), "b": BRANDS.get(b, {}).get("name", b),
                    "q": str(v["q"])[:220], "ans": str(v["ans"])[:120], "e": ""})
    if new:
        ARCH.parent.mkdir(parents=True, exist_ok=True)
        with open(ARCH, "a", encoding="utf-8") as f:
            for x in new:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
        state.put("answer_dirty", True)
    return len(new)


def archive_files():
    """site/jawab-archive.json (saal ki list) + har saal ki file. /jawab ki khoj inhe tab padhti hai jab code table mein na mile."""
    rows = archive_rows()
    by = {}
    for r in rows:
        by.setdefault((r.get("d") or "0000")[:4], []).append(r)
    out = {f"site/jawab-archive-{y}.json": json.dumps(v, ensure_ascii=False, separators=(",", ":")) for y, v in by.items() if y.isdigit()}
    out["site/jawab-archive.json"] = json.dumps({"u": str(datetime.date.today()), "years": sorted((y for y in by if y.isdigit()), reverse=True),
                                                 "n": len(rows)})
    return out


JW_ARCH = ("<script>document.addEventListener('DOMContentLoaded',function(){var q=document.getElementById('jq'),z=document.getElementById('j0'),"
           "box=document.createElement('div');box.id='jArch';if(z)z.parentNode.insertBefore(box,z.nextSibling);var tm=null,idx=null;"
           "function show(list,t){box.innerHTML='';if(!list.length)return;var h=document.createElement('p');h.className='upd';"
           "h.textContent='📚 Purane jawab (zindagi bhar ka register): '+list.length;box.appendChild(h);list.slice(0,30).forEach(function(r){"
           "var p=document.createElement('p');p.style.cssText='background:#fff;border:1px solid #E1E7E8;border-radius:10px;padding:8px 10px';"
           "p.textContent='#'+r.c+' ('+r.d+', '+r.b+'): '+r.q+' → सही जवाब: '+r.ans+(r.e?' ('+r.e+')':'');box.appendChild(p)})}"
           "function look(t){t=(t||'').toLowerCase().replace(/^#/,'').trim();if(t.length<3||!z||z.hidden){box.innerHTML='';return}"
           "(idx?Promise.resolve(idx):fetch('/jawab-archive.json').then(function(r){return r.json()}).then(function(j){idx=j;return j}))"
           ".then(function(j){return Promise.all((j.years||[]).map(function(y){return fetch('/jawab-archive-'+y+'.json').then(function(r)"
           "{return r.json()}).catch(function(){return []})}))}).then(function(arrs){var all=[].concat.apply([],arrs);"
           "show(all.filter(function(r){return (r.c===t)||((r.q+' '+r.ans).toLowerCase().indexOf(t)>=0)}),t)}).catch(function(){})}"
           "if(q)q.addEventListener('input',function(){clearTimeout(tm);tm=setTimeout(function(){look(q.value)},400)});"
           "var h=(location.hash||'').match(/^#c(\\d{3,6})$/);if(h&&!document.getElementById('c'+h[1])&&q){q.value=h[1];"
           "if(z)z.hidden=false;look(h[1]);setTimeout(function(){box.scrollIntoView({block:'start'})},900)}});</script>")

def jawab_table(lst, old):
    """v2.6.0 (owner 9 Nov screenshot): saare jawab ek seedhi table mein (Code | Tarikh | Channel | Sawal | Jawab), upar khoj
    (code ya shabd) + channel button. Sab browser mein - koi data server par nahi. Purane jawab ki row par hi anchor (#cCODE)
    taaki purani reel ka link seedha us line par khule. Naye 150 ke poore dabbe neeche waise hi."""
    allx = list(lst) + list(old)
    full_ids = {str(e.get("aid") or e.get("code")) for e in lst}
    seen_b, chips = [], ['<button type="button" data-b="" class="on">Sab</button>']
    rows = []
    for e in allx:
        aid = str(e.get("aid") or e.get("code"))
        bk = str(e.get("brand") or "")
        if bk and bk not in seen_b:
            seen_b.append(bk)
            chips.append(f'<button type="button" data-b="{_esc(bk)}">{_esc(e.get("bname") or bk)}</button>')
        key = " ".join([str(e.get("code", "")), str(e.get("q", "")), str(e.get("ans", "")), str(e.get("bname", ""))]).lower()
        code_cell = (f'<a href="#c{_esc(aid)}">#{_esc(e.get("code"))}</a>' if aid in full_ids else f'#{_esc(e.get("code"))}')
        rid = "" if aid in full_ids else f' id="c{_esc(aid)}"'
        rows.append(f'<tr{rid} data-b="{_esc(bk)}" data-k="{_esc(key)}"><td class="n">{len(rows) + 1}</td><td>{code_cell}</td><td>{_esc(e.get("date"))}</td>'
                    f'<td>{_esc(e.get("bname"))}</td><td>{_esc(str(e.get("q", ""))[:140])}</td><td><b>{_esc(e.get("ans"))}</b></td></tr>')
    if not rows:
        rows = ['<tr><td class="n">1</td><td>-</td><td>-</td><td>-</td><td>Aaj ke jawab jaldi aa rahe hain</td><td>-</td></tr>']
    return ('<p id="jwStreak" class="upd"></p><p class="upd"><button type="button" id="jwShare" class="jw-sharebtn">📤 Apna score card '
            'share karo</button></p>' + JW_STREAK + tap_js() + JW_ARCH + "<h2>Saare jawab: code ya shabd se khojein</h2>"
            '<div class="jw-tools"><label for="jq" class="upd">Video ka code (jaise 1270) ya koi shabd likhein:</label>'
            '<input id="jq" type="search" inputmode="search" autocomplete="off" placeholder="Code ya shabd...">'
            '<div class="jw-chips">' + "".join(chips) + '</div><p id="jn" class="upd"></p></div>'
            '<div class="jw-wrap"><table class="jw"><thead><tr><th>Kram</th><th>Code</th><th>Tarikh</th><th>Channel</th><th>Sawal</th>'
            '<th>Sahi jawab</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>"
            '<p id="j0" class="upd" hidden>Ye code/shabd nahi mila. Code dobara dekhein (video mein # ke baad wala number). 5 Nov 2026 '
            'se pehle ki reels mein jawab video ke andar hi bata diya jaata tha. Neeche zindagi bhar ke register mein bhi khoja ja raha hai. '
            f'Telegram channel mein bhi khoj sakte hain: <a href="{TG_LINK}" rel="noopener">{TG_LINK}</a></p>'
            f'<p class="upd">Yahan sabse naye {len(allx)} jawab. Purana code/sawal upar khoj dabbe mein likhein - zindagi bhar ke register se '
            f'mil jayega. Code par tap karein to poori wajah khulegi.</p>' + JW_JS)



def build_page():
    """site/about.html ke template se /jawab - title<=60, description 95-165, ek H1, canonical, og:url (site audit niyam)."""
    from .website import DIR
    tpl = (DIR / "site" / "about.html").read_text(encoding="utf-8")
    full_list = list(reversed(state.get("answer_key") or []))
    for e_ in full_list:                             # v3.1.0: purani entry ki likhai-galti page banate waqt theek
        for k_ in ("q", "ans", "exp"):
            if isinstance(e_.get(k_), str):
                e_[k_] = _hfix(e_[k_])
        if isinstance(e_.get("opts"), list):
            e_["opts"] = [_hfix(o) for o in e_["opts"]]
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
            f'<h3>{_esc(e["q"])}</h3>' + tap_block(e) + f'<p><b>सही जवाब: {_esc(e["ans"])}</b></p>'
            + (f'<p>{_esc(e["exp"])}</p>' if e.get("exp") else "") + tool + share_link(e)
            + ("" if tap_ok(e) else
               f'<p class="upd jw-me" data-id="{_esc(e.get("aid") or e["code"])}">Aapne pehle socha tha? '
               f'<button type="button" data-r="1">✅ Mera jawab sahi tha</button> <button type="button" data-r="0">❌ Galat tha</button></p>')
            + (f'<p class="upd"><a href="#c{_esc((lst[i_ + 1].get("aid") or lst[i_ + 1]["code"]))}">Agla jawab ↓</a></p>' if i_ + 1 < len(lst) else "")
            + "</section>")
    from .config import LINKS, WHATSAPP, TELEGRAM, PINTEREST
    chan = ("<h2>Hamare channel</h2><p>" + " · ".join(
        f'<a href="{_esc(LINKS[b]["youtube"])}" rel="noopener">{_esc(BRANDS[b]["name"])} (YouTube)</a>' for b in LINKS if b in BRANDS)
        + f' · <a href="{_esc(TELEGRAM)}" rel="noopener">Telegram</a> · <a href="{_esc(WHATSAPP)}" rel="noopener">WhatsApp channel</a>'
        f' · <a href="{_esc(PINTEREST)}" rel="noopener">Pinterest</a></p>')
    table = jawab_table(lst, [])                     # v2.9.2: table mein sirf naye (tez); purane khoj par register se
    arch = ""
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
             '<p>Har video mein ek code likha hota hai, jaise #4827. Upar ke khoj dabbe mein wahi code likhein, ya neeche us code wale '
             'dabbe tak scroll karein. Har dabbe mein tarikh, channel ka naam, poora sawal, sahi jawab aur jahan ho sake wahan us '
             'vishay ka free calculator ya guide ka link hai, taaki aap sirf jawab hi nahi, poora hisaab bhi samajh sakein.</p>'
             '<h2>Jawab kaise jaanche jaate hain</h2>'
             '<p>Ganit aur tark wale sawal (sudoku, series, ghadi, calendar, umar, disha) ka jawab ganit se nikalta hai, isliye '
             'woh hamesha ek hi sahi hota hai. GK, shabdon ke arth aur pahadi sawal ko hum pakke srot se milane ki poori koshish karte hain. '
             'Hum koshish karte hain ki koi sawal kisi bhi channel par dobara na aaye. Phir bhi galti ho sakti hai - koi galti dikhe to '
             'contact page se batayein, hum turant theek karte hain.</p>'
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
             '<p><b>Purane sawal kahan milenge?</b> Upar ki table mein sabse naye jawab dikhte hain. Usse purana koi bhi jawab khoj dabbe mein '
             'video ka code ya koi shabd likhne par hamare poore register se mil jaata hai - hum koi jawab kabhi hatate nahi.</p>'
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
            + table + nav + ("".join(blocks) or "<p>Aaj ke jawab jaldi aa rahe hain.</p>") + guide +
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
    if "</head>" in s and "table.jw" not in s.split("</head>")[0]:      # v2.6.0: table ki style <head> mein (audit niyam)
        s = s.replace("</head>", JW_CSS + "</head>", 1)
    return fix_ld(s, title, desc, today)


LD_RX = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
JAWAB_BORN = "2026-11-05"             # /jawab pehli baar live (docs/INDEXING.md) - kabhi backdate nahi


def fix_ld(html, title, desc, today):
    """v3.1.0 (11 Nov audit): /jawab about.html ke saanche se banta hai - uska JSON-LD (AboutPage 'About Sab Hisaab', breadcrumb
    'About Us', 21 Jul ki tareekh) /jawab par GALAT structured data tha (Google structured-data niti: markup page se mile).
    Ab: BreadcrumbList = Home > Sawal ke Jawab; AboutPage -> CollectionPage (sahi naam/description/tareekh). Baaki block waise hi."""
    def _one(m):
        try:
            d = json.loads(m.group(2))
        except Exception:
            return m.group(0)
        if not isinstance(d, dict):
            return m.group(0)
        t = d.get("@type")
        if t == "BreadcrumbList":
            d["itemListElement"] = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                                    {"@type": "ListItem", "position": 2, "name": "Sawal ke Jawab", "item": SITE + PAGE}]
        elif t in ("AboutPage", "WebPage", "CollectionPage"):
            d["@type"] = "CollectionPage"
            d["name"] = title
            d["url"] = SITE + PAGE
            d["description"] = desc
            d["datePublished"] = JAWAB_BORN
            d["dateModified"] = today
        else:
            return m.group(0)
        return m.group(1) + json.dumps(d, ensure_ascii=False) + m.group(3)
    try:
        return LD_RX.sub(_one, html)
    except Exception as e:
        log(f"jawab ld: {e}")
        return html


def jawab_json(n=5):
    """v2.6.2: website ke har page par 'Aaj ka sawal' dabba (install-app.js) ke liye sabse naye n SAWAL (jawab nahi - jigyasa
    bani rahe, click /jawab par). Sirf sawal/code/channel - koi niji data nahi."""
    lst = list(reversed(state.get("answer_key") or []))[:n]
    items = [{"c": str(e.get("code", "")), "a": str(e.get("aid") or e.get("code", "")), "b": str(e.get("bname", "")),
              "q": _hfix(re.sub(r"\s+", " ", str(e.get("q", ""))).strip()[:140]), "d": str(e.get("date", ""))} for e in lst if e.get("q")]
    return json.dumps({"u": str(datetime.date.today()), "items": items}, ensure_ascii=False)


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
        if i < 0 and fn == "index.html":                # v2.6.2: homepage mein <main> nahi - 'Naye lekh' se pehle
            i = s.find('<section class="artstrip">')
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
    today = str(datetime.date.today())
    if f"<loc>{SITE}{PAGE}</loc>" in sm:              # v2.6.0: page roz badalta hai - lastmod bhi sach (dateModified se mile)
        rx = re.compile(r"(<loc>" + re.escape(SITE + PAGE) + r"</loc>\s*<lastmod>)([\d-]+)(</lastmod>)")
        if rx.search(sm) and rx.search(sm).group(2) != today:
            return rx.sub(lambda m: m.group(1) + today + m.group(3), sm, count=1)
        return None
    if "</urlset>" not in sm:
        return None
    ent = (f"  <url><loc>{SITE}{PAGE}</loc><lastmod>{datetime.date.today()}</lastmod>"
           "<changefreq>daily</changefreq></url>\n")
    # v2.6.2: alphabetical jagah par (audit niyam: homepage pehle, baaki A-Z)
    from .webstory import sitemap_insert            # v2.9.1: kai-line format bhi
    return sitemap_insert(sm, ent, PAGE.strip("/"))


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
    if state.get("jawab_site_on") and state.get("jawab_fix_v310") != 1:                  # v3.1.0 install ke baad ek baar:
        state.put("jawab_fix_v310", 1)                                                   # sahi JSON-LD + saaf Hindi ke saath page dobara bane
        state.put("answer_dirty", True)
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
    lst = list(reversed(state.get("answer_key") or []))[:min(n, KEEP)]     # v2.9.4: page par jitne rehte hain utne hi
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
            try:
                for fn_, body_ in archive_files().items():         # v2.8.0: zindagi bhar ka jawab-register (saal-war)
                    zz.writestr(fn_, body_)
            except Exception as ex:
                log(f"jawab archive files: {ex}")
            try:
                zz.writestr("site/jawab.json", jawab_json())      # v2.6.2: har page ka 'Aaj ka sawal' dabba
            except Exception as ex:
                log(f"jawab.json: {ex}")
            for fn, body in links.items():                # site niyam: har page par kam se kam 3 andar ke link
                if fn == "index.html" and not with_index:
                    continue
                zz.writestr(f"site/{fn}", body)
            if sm:
                zz.writestr("site/sitemap.xml", sm)
        return z
    z = _zip(True)
    r = website.apply_zip(z, force=False, deploy_in=1)    # audit asli gate; v2.9.2: 1 min mein live (pehle 15)
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


# ---------------- v3.2.0 (owner 13 Nov 2026): jawab-tareeka har video alag ----------------
# Pehle har quiz video mein 50-50 hi lagta tha. Ab 5 tareeke, views ke hisaab se (learn.choose 'vmech': har naya
# pehle 3 video, phir jeetne wala zyada, 25% khoj), usi channel par pichhla tareeka lagatar dobara nahi.
# Pakke niyam: SAHI vikalp kabhi nahi katta; 'jaal' (sahi ke sabse paas wala galat) bhi nahi katta (hook 'ulta' use dikhata hai);
# koi nakli %/vote/'log yahin phanste' jaisa daava nahi; jawab ka sanket nahi.
VMECH = {
    "fifty": "50-50 (aakhir mein 2 galat kate)",
    "full": "Poora muqabla (charon vikalp aakhir tak)",
    "ek_kata": "Ek galat kata (3 mein se chuno)",
    "dhire": "Dheere-dheere kaatna (pehle 1, phir 2)",
    "savdhaan": "Jaal ki chetavni (koi kata nahi)",
}
_MECH_SAY = {
    "fifty": "दो गलत विकल्प हटा दिए। अब बताइए!",
    "ek_kata": "एक गलत विकल्प हटा दिया। अब तीन में से चुनिए!",
    "dhire": "एक और गलत विकल्प गया। अब सिर्फ़ दो बचे!",
    "dhire_1": "एक गलत विकल्प हटा दिया।",
    "savdhaan": "ध्यान से! इनमें एक विकल्प जाल है, जल्दबाज़ी मत कीजिए।",
    "full": "चारों विकल्प सामने हैं, सोचिए!",
}


def mech_options(n_scenes):
    """Is video mein kaunse tareeke chal sakte hain. dhire ko kam se kam 4 scene chahiye (sawal dikhte hi kaatna nahi)."""
    if state.get("fifty_on", True) is False:          # purana switch: band ho to sirf bina-kaate tareeke
        return ["full", "savdhaan"]
    mode = state.get("vmech_mode") or "rotate"
    if mode in VMECH and (mode != "dhire" or n_scenes >= 4):
        return [mode]
    return [k for k in VMECH if k != "dhire" or n_scenes >= 4]


def _say_add(sc, txt):
    say = sc.get("say", "")
    if REVEAL_RX_SAFE.search(say):
        return sc
    return dict(sc, say=txt if _is_filler(say) else (say + " " + txt).strip())


def apply_mech(script, keep, opts_, ans, mech=None):
    """keep (scene list) ko jagah par badalta hai; script['vmech'] + script['fifty_out'] (sab kate vikalp, audit ke liye)."""
    from .hooks import traps as _tr
    brand = script.get("brand", "")
    if mech is None:
        opts = mech_options(len(keep))
        try:
            from . import learn
            mech = learn.choose("vmech", opts, f"{brand}:{script.get('reel_code', '')}:{script.get('puzzle_q', '')[:40]}",
                                avoid=(state.get("last_vmech") or {}).get(brand))
        except Exception:
            mech = opts[int(hashlib.md5(str(script.get("puzzle_q", "")).encode()).hexdigest(), 16) % len(opts)]
    wrong = [o for o in _tr(opts_, ans) if str(o).strip() != str(ans).strip()]
    safe = wrong[1:]                                   # jaal (wrong[0]) kabhi nahi katta
    far = list(reversed(safe))                         # sabse door wala galat pehle katta
    script.pop("fifty_out", None)
    for i, sc in enumerate(keep):
        if sc.get("fifty") or sc.get("elim"):
            keep[i] = {k: v for k, v in sc.items() if k not in ("fifty", "elim")}
    if mech == "dhire" and (len(keep) < 4 or len(far) < 2):
        mech = "fifty"
    if mech in ("fifty", "ek_kata", "dhire") and len(far) < (1 if mech == "ek_kata" else 2):
        mech = "full"
    if mech == "fifty":
        out = far[:2]
        keep[-1] = _say_add(dict(keep[-1], fifty=True, elim=out), _MECH_SAY["fifty"])
    elif mech == "ek_kata":
        out = far[:1]
        keep[-1] = _say_add(dict(keep[-1], fifty=True, elim=out), _MECH_SAY["ek_kata"])
    elif mech == "dhire":
        out = far[:2]
        keep[-2] = _say_add(dict(keep[-2], fifty=True, elim=out[:1]), _MECH_SAY["dhire_1"])
        keep[-1] = _say_add(dict(keep[-1], fifty=True, elim=out), _MECH_SAY["dhire"])
    else:
        out = []
        if mech == "savdhaan" or _is_filler(keep[-1].get("say", "")):
            keep[-1] = _say_add(keep[-1], _MECH_SAY.get(mech, _MECH_SAY["full"]))
    out = [str(o) for o in out if str(o).strip() != str(ans).strip()]
    if out:
        script["fifty_out"] = out
    script["vmech"] = mech
    state.update("last_vmech", lambda d, v=mech: {**(d or {}), brand: v}, {})
    return mech
