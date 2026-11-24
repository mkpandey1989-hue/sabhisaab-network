"""/services-list page banata hai: services.html ka head/footer (consent, GA, style) + rate list + demo + custom builder + form."""
import html
import json
import re
import sys

src, rates_f, out = sys.argv[1:4]
S = open(src, encoding="utf-8").read()
R = json.load(open(rates_f, encoding="utf-8"))

head = S[:S.index("<style>")]
style = S[S.index("<style>"):S.index("</style>") + 8]
foot = S[S.index("<footer>"):]
TITLE = "Services Rate List: 1000+ Digital Kaam ₹10 Se | Sab Hisaab"
DESC = ("1000+ digital kaam ki rate list ₹10 se: resume, form madad, website, app, Excel, bot, server, design, SEO. "
        "Likhit quote, 2 badlav shaamil.")
head = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", head, flags=re.S)
head = re.sub(r'(<meta name="description" content=")[^"]*', r"\g<1>" + DESC, head)
head = head.replace('href="https://sabhisaab.com/services"', 'href="https://sabhisaab.com/services-list"')
head = re.sub(r'(name="twitter:title" content=")[^"]*', r"\g<1>" + TITLE, head)

items = [i for i in R["items"] if not i.get("hide")]          # v3.9.2: SEBI order-bot chhupa
cats = {k: v for k, v in R["cats"].items() if any(i["cat"] == k for i in items)}
ORDER = ["micro", "naukri", "yojana", "padhai", "senior", "daftar", "guide", "docs", "excel", "web", "local", "design", "content", "ecom",
         "calc", "soft", "app", "bot", "smart", "domain", "cloud", "devops", "data", "setup", "fix", "care", "trade"]
ORDER += [k for k in cats if k not in ORDER]


def _card(i):
    """v3.9.2: SEO ke liye har kaam HTML mein (pehle JS se banta tha - Google ko list nahi dikhti thi)."""
    mk = (f' <s class="mk">₹{i["market"][0]:,}+</s>' if i["market"][0] > i["price"] and not i.get("nostrike") else "")
    y = '<span class="y">Sharton ke saath</span>' if i["risk"] == "Y" else ""
    return (f'<li class="it" data-i="{i["id"]}" data-c="{i["cat"]}" data-p="{i["price"]}" data-d="{html.escape(i["days"])}">'
            f'<b>{html.escape(i["name"])}</b><span class="pr">₹{i["price"]:,} se</span>{mk}{y}'
            f'<button type="button" data-pick="{i["id"]}">Ye chahiye</button></li>')


SECS = ""
for n_, k in enumerate(ORDER):
    its = sorted((i for i in items if i["cat"] == k), key=lambda x: (x["price"], x["name"]))
    if not its:
        continue
    SECS += (f'<details class="sec" id="c-{k}"{" open" if n_ < 3 else ""}><summary class="sh"><h2>{html.escape(cats[k]["title"])}</h2>'
             f'<span>{len(its)} kaam · ₹{its[0]["price"]:,} se · {html.escape(cats[k]["sub"])}</span></summary>'
             f'<ul class="il">{"".join(_card(i) for i in its)}</ul></details>')
N_ALL = len(items)
DEMOS = [("dukaan-site", "1-page dukaan website", "/", "Aisi tez, mobile par saaf site aapke naam par"),
         ("gst-bill", "GST calculator → billing app", "/gst-calculator", "Isi se aapka GST bill app banta hai"),
         ("emi", "Branded EMI calculator", "/emi-calculator", "Aapke logo aur WhatsApp button ke saath"),
         ("margin", "Dukaan margin tool", "/profit-margin-calculator", "Aapke dhandhe ka apna hisaab"),
         ("bijli", "Bijli bill calculator", "/bijli-bill-calculator", "Solar/bijli dealer ke liye"),
         ("sip", "SIP calculator (chart ke saath)", "/sip-calculator", "MF distributor ke liye branded"),
         ("discount", "Offer / discount tool", "/discount-calculator", "Dukaan ke offer ke liye"),
         ("position", "Trading position-size tool", "/position-size-calculator", "Aapki strategy ka tool"),
         ("bigha", "Zameen converter", "/bigha-converter", "Property dealer ke liye"),
         ("attendance", "Attendance tool", "/attendance-percentage-calculator", "School/coaching ke liye"),
         ("quiz", "Quiz / jawab page", "/jawab", "Lead lene wala quiz"),
         ("uk-guide", "Uttarakhand guide page", "/dehradun-uttarakhand", "Homestay/travel ke liye content")]
demo_html = "".join(
    f'<a class="demo" data-d="{d}" href="{u}" target="_blank" rel="noopener"><b>{html.escape(n)}</b><span>{html.escape(t)}</span>'
    f'<i>Demo kholein →</i></a>' for d, n, u, t in DEMOS)


TOP = ["m-resume","m-form","w-1page","w-5page","w-shop","w-book","w-gmb","c-calc","c-quote","s-bill","s-stock","s-khata","s-pos",
       "b-wa","b-tg","b-faq","t-pine","t-back","t-chart","d-logo","d-reels30","e-store","p-extract","u-vm","f-site","k-care"]
by = {i["id"]: i for i in R["items"]}
rows = "".join(f"<tr><td>{html.escape(by[k]['name'])}</td><td>₹{by[k]['market'][0]:,}–{by[k]['market'][1]:,}</td><td><b>₹{by[k]['price']:,}</b></td><td>{by[k]['days']}</td></tr>" for k in TOP)
TABLE = ("<h2>Market rate vs hamara rate</h2><p>Neeche ke aankde bazaar mein freelancer aur chhoti agency ke aam rate se tulna hai (2026). "
         "Hamara rate kam isliye hai kyunki hamare paas 188 tool aur website ka bana-banaya dhancha hai, aur kaam tez hota hai. "
         "Rate kam hai, par har kaam ka ek nichla rate (floor) tay hai jisse neeche kabhi nahi jaate - taaki kaam ki quality bani rahe.</p>"
         "<table><thead><tr><th>Kaam</th><th>Bazaar mein aam rate</th><th>Hamara rate (se)</th><th>Samay</th></tr></thead><tbody>" + rows + "</tbody></table>")
FAQ = [("Rate 'se' kyun likha hai?", "Har kaam alag hota hai. Likha hua rate shuruaati hai. Aapka kaam dekh kar likhit quote milta hai jisme version number hota hai (jaise SH261123AB-v1). Sirf wahi likhit quote pakka maana jaata hai, baad mein rakam nahi badhti."),
       ("Advance kitna dena hota hai?", "₹10 se ₹199 wale chhote kaam par poora payment pehle. Baaki kaam par lagbhag 30% advance, phir demo dekh kar baaki. Final file, code aur account poora payment hone ke baad milta hai."),
       ("Code aur account kiske naam hoga?", "Aapke naam. Website, domain, hosting, payment gateway, bot - sab aapke apne account par banta hai. Hum aapka password nahi lete; zaroorat ho to aap access dete hain aur kaam ke baad hata dete hain."),
       ("Care plan band karna ho to?", "Care plan har mahine ka hai, kabhi bhi band kar sakte hain. Charge sirf tab tak lagta hai jab tak service chal rahi hai. Hum kabhi service band karein to 30 din pehle batayenge aur saara code aur access aapko de denge."),
       ("Trading bot banate ho?", "Sirf aapki apni strategy ke tool - backtest, indicator, alert, chart, journal, risk calculator aur paper-trading (bina asli paisa). Broker par apne aap order lagane wala bot (algo) hum nahi banate - SEBI ke 2025 niyam mein ye kaam exchange se manzoor algo provider hi kar sakte hain. Hum tip, signal ya profit ka vaada nahi dete aur kisi ka account nahi chalate."),
       ("Offer kab tak hai? 'Seemit samay' to nahi?", "Hum jhootha 'seemit samay' ya 'jaldi karein' nahi likhte. List ke rate 'se shuru' hain aur aage bhi isi tarah chalenge; badlenge to is page par nayi tareekh ke saath. Hafte ki sale ya tyohar offer ho to uski shuru aur khatam ki tareekh saaf likhi hoti hai. Likhit quote 7 din maanya hai."),
       ("Sarkari form, yojana ya bharti mein aap kya karte ho?", "Sirf madad aur guide - form samjhana, documents ki suchi, photo-sign ka sahi size, aapke saamne bharna. Hum sarkari vibhag ya agent nahi hain; naukri, yojana ya praman patra milne ka koi vaada nahi. Nakli document kabhi nahi banate. OTP/password aap daalte hain, sarkari fees portal par aap khud bharte hain."),
       ("Online form bharne mein madad kaise hoti hai?", "Aap apni jaankari aur document khud dete hain; hum form bharne mein madad karte hain (screen-share ya aapke saamne). OTP aur password sirf aap daalte hain - hum kabhi nahi maangte. Portal ki sarkari fees aap seedha portal par bharte hain; hamara charge sirf madad ka hai. Hum sarkari agent nahi hain, aur aapke document apne paas nahi rakhte."),
       ("Kaun sa kaam nahi lete?", "Data scraping, kisi ka phone/email nikalna, bulk ya spam message, nakli review/followers, hacking, kisi ki site ki copy, betting aur loan app. Ye kanoon aur platform niyam ke khilaf hain."),
       ("Referral code kaise chalta hai?", "Form bhejne par aapko ek REF code milta hai. Dost us code se kaam karwaye to dost ko pehle kaam par 10% chhoot milti hai, aur dost ke chukaye bill ka 10% aapko bonus milta hai (₹300 se bade bill par, ek baar mein max ₹500). Bonus dost ka payment hone ke 7 din baad pakka hota hai, agle paid kaam ke bill ka max 10% kaat sakta hai aur 90 din tak chalta hai. Ek hi phone/device se apna hi code nahi chalta, aur bonus nakad nahi milta.")]
FAQ_HTML = '<h2>Aksar pooche jaane wale sawaal</h2><div class="faq">' + "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in FAQ) + "</div>"

EXTRA_CSS = """<style>
.wrapw{max-width:1040px;margin:0 auto;padding:0 20px}
.hero{background:linear-gradient(135deg,#0F766E,#115E59);color:#fff;border-radius:20px;padding:26px 22px;margin-bottom:18px}
.hero h1{color:#fff;margin-bottom:6px}.hero p{color:#d8f3ef;margin:0 0 6px}
.pill{display:inline-block;background:#ffffff22;border:1px solid #ffffff44;border-radius:100px;padding:4px 12px;margin:6px 6px 0 0;font-size:.82rem}
#q{width:100%;padding:14px 16px;border:2px solid var(--brand);border-radius:14px;font-size:16px;margin:8px 0 10px}
.cats{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}.cats button{border:1px solid var(--line);background:#fff;border-radius:100px;padding:6px 12px;font:inherit;font-size:.82rem;cursor:pointer}
.cats button.on{background:var(--brand);color:#fff;border-color:var(--brand)}
.sec{background:#fff;border:1px solid var(--line);border-radius:14px;margin:0 0 10px;padding:0 12px}.sec>summary{cursor:pointer;padding:12px 0;list-style:none}
.sec>summary::-webkit-details-marker{display:none}.sec>summary h2{display:inline;font-size:1.05rem;margin:0}.sec>summary span{display:block;font-size:.8rem;color:var(--muted)}
.sec>summary:after{content:"▾ kholein";float:right;font-size:.75rem;color:var(--brand);margin-top:-30px}.sec[open]>summary:after{content:"▴"}
.il{list-style:none;margin:0 0 10px;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px}
.it{border:1px solid var(--line);border-radius:12px;padding:10px;display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center}
.it b{flex:1 1 100%;font-size:.92rem;line-height:1.35}.it button{margin-left:auto;border:none;background:var(--brand);color:#fff;border-radius:9px;padding:6px 10px;font:inherit;font-size:.82rem;font-weight:600;cursor:pointer}
.it.hid,.sec.hid{display:none}.tnc{font-size:.82rem;color:var(--muted);background:#F8FAFC;border-radius:10px;padding:10px;margin-top:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:13px;display:flex;flex-direction:column;gap:3px}
.card small{color:var(--muted);font-size:.75rem}.card b{font-size:.95rem;line-height:1.35}
.pr{font-weight:800;color:var(--brand);font-size:1.15rem}.mk{font-size:.75rem;color:#8a979c;text-decoration:line-through}
.card button{margin-top:auto;border:none;background:var(--brand);color:#fff;border-radius:10px;padding:8px;font:inherit;font-weight:600;cursor:pointer}
.y{font-size:.72rem;color:#92400E;background:#FEF3C7;border-radius:6px;padding:2px 6px;align-self:flex-start}
.demos{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.demo{background:#fff;border:1px solid var(--line);border-radius:14px;padding:13px;text-decoration:none;color:var(--ink);display:flex;flex-direction:column;gap:3px}
.demo span{font-size:.82rem;color:var(--muted)}.demo i{font-style:normal;color:var(--brand);font-weight:600;font-size:.85rem;margin-top:4px}
.bld{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px}
#bt{width:100%;padding:12px;border:1px solid var(--line);border-radius:12px;font-size:16px;margin-bottom:6px;background:#fff}
.bld label{display:flex;gap:8px;align-items:center;padding:7px 0;border-bottom:1px dashed var(--line);font-size:.92rem}
.bld label span{margin-left:auto;font-weight:700;color:var(--brand)}
.tot{font-size:1.3rem;font-weight:800;margin-top:10px}
#fm input,#fm select,#fm textarea{width:100%;padding:12px 14px;border:1px solid #E3E9EC;border-radius:12px;font-size:16px;font-family:inherit;margin-bottom:8px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:8px}@media(max-width:600px){.two{grid-template-columns:1fr}}
.sum{background:#ECFDF5;border-radius:12px;padding:12px;margin:8px 0;font-size:.92rem}
.okm{display:none;background:#ECFDF5;border:1px solid #A7F3D0;border-radius:12px;padding:14px}
@media(max-width:600px){.hnav{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:2px 12px;max-width:62vw}.hnav a{margin-left:0!important;font-size:.85rem}}#shConsent{max-width:100vw;box-sizing:border-box}#shConsent button{white-space:normal;max-width:100%}footer .wrap{overflow-wrap:anywhere}footer .wrap a{display:inline-block;margin:2px 7px}#shConsent{max-width:100vw;box-sizing:border-box}#shConsent button{white-space:normal;max-width:100%}html,body{max-width:100%;overflow-x:hidden}
.cbar{position:fixed;left:50%;transform:translateX(-50%);bottom:12px;display:flex;gap:8px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:100px;padding:6px 8px 6px 14px;box-shadow:0 6px 20px #0002;z-index:60;font-size:.85rem;max-width:94vw}
.cbar a{color:#fff;border-radius:100px;padding:9px 14px;font-weight:700;text-decoration:none}.cb-wa{background:#25D366}.cb-tg{background:#229ED9}
.findb{background:#fff;border:1px dashed var(--brand);border-radius:14px;padding:12px;margin:10px 0}.findb input{width:100%;box-sizing:border-box;padding:10px;border:1px solid var(--line);border-radius:10px;font-size:16px;margin:0 0 6px}.kit-lab{display:block;font-size:.84rem;font-weight:700;color:#334155;margin:4px 0}.bld label.kit-lab,.bld label.kit-l{display:block;border-bottom:none;padding:0;margin:6px 0 4px}.bld label.kit-lab small,.bld label.kit-l small{margin-left:4px;font-weight:400}.kit-lab small{font-weight:400;color:var(--muted)}#fm ::placeholder,.findb ::placeholder{color:#A3AEB6;opacity:1;font-style:italic}.findb button{border:none;background:var(--brand);color:#fff;border-radius:10px;padding:10px 14px;font:inherit;font-weight:600}
</style>"""

BODY = """<body>
<header><div class="hrow"><a href="/" class="logo">Sab<span>Hisaab</span></a>
<nav class="hnav"><a href="/">Tools</a><a href="/about">About</a><a href="/services">Services</a><a href="/contact">Contact</a></nav></div></header>
<main><div class="wrapw">
<div class="crumb"><a href="/">Home</a> &rsaquo; <a href="/services">Services</a> &rsaquo; Rate list</div>
<div class="hero"><h1>Koi bhi digital kaam — ho jayega</h1>
<p class="upd">Rate list: <time datetime="__TODAY__">__TODAY_H__</time> · shuruaati daam · likhit quote 7 din maanya · <a href="/terms#rate" style="color:#fff">shartein</a></p>
<p><b>Hindi mein likhiye, jaise ghar mein bolte hain</b> — English zaroori nahi, sharm ki koi baat nahi.</p>
<p>Resume ₹10 · Form bharne mein madad ₹49 · Mobile/computer madad ₹49 · Bill · Website — <b>₹10 se shuru</b></p>
<span class="pill">🗂 1000+ kaam ki list</span><span class="pill">📄 Resume sirf ₹10</span><span class="pill">📝 Online form bharne mein madad ₹49</span><span class="pill">✔ Market se kam rate</span><span class="pill">✔ Pehle demo, phir payment</span><span class="pill">✔ 2 badlav shaamil</span><span class="pill">✔ Code aur account aapke naam</span></div>

<div id="offer"></div>
<input id="q" placeholder="Kya kaam hai? jaise: dukaan website, GST bill, bot, logo, excel…" aria-label="Kaam khojein">
<div class="cats" id="cats"></div>
<div class="card" style="border:2px dashed var(--brand);margin-bottom:10px"><small>Kuch bhi</small><b>Koi bhi kaam — list mein nahi? Apne shabdon mein likhiye</b><span class="pr">Baat karke</span><button type="button" onclick="anyKaam()">Apna kaam likho</button></div>
<p id="nf" style="display:none">Is shabd se kaam nahi mila — <a href="#form" onclick="anyKaam()">apne shabdon mein likhiye</a>, hum samajh lenge.</p>
<div id="list">""" + SECS + """</div>
<p class="tnc" id="sharten"><b>* Sharten laagu:</b> list ke rate "se shuru" hain — kaam dekh kar likhit quote milta hai (7 din maanya). Market rate 2026 ke aam freelancer/agency rate ka andaza hai, tulna ke liye. Sarkari kaam mein sirf madad, koi vaada nahi. Poori sharten: <a href="/terms#rate">Terms — rate, chhoot aur offer</a>.</p>
<p style="font-size:.85rem;color:var(--muted);margin-top:8px">List mein nahi? <a href="#custom">Apna custom kaam banaiye</a> ya neeche seedha likhiye. Rate "se" hai — aapka kaam dekh kar likhit quote milta hai.</p>

<h2 id="demo">Live demo — khud chala kar dekhiye</h2>
<p><b><a href="/services-demo">👉 Billing app, khata, stock, dukaan site, booking, menu, bot aur backtest ke 8 chalte demo yahan</a></b> · neeche hamare maujooda tool:</p>
<div class="demos">""" + demo_html + """</div>

<h2 id="custom">Apna custom kaam banaiye</h2>
<div class="bld" id="bld">
<select id="bt" aria-label="Kaam ka type"><option value="2999">1-page website</option><option value="7999">5-page website</option><option value="3999">Billing / stock app</option><option value="2499">Telegram / WhatsApp bot</option><option value="1499">Calculator / tool</option><option value="999">Design (logo/post)</option><option value="0">Sirf add-on chahiye</option></select>
<label><input type="checkbox" value="1499" data-n="Google Business + Maps"> Google Business + Maps <span>+₹1,499</span></label>
<label><input type="checkbox" value="999" data-n="WhatsApp auto-reply"> WhatsApp auto-reply + catalogue <span>+₹999</span></label>
<label><input type="checkbox" value="1499" data-n="Booking form"> Booking / appointment <span>+₹1,499</span></label>
<label><input type="checkbox" value="1499" data-n="Payment gateway"> Payment gateway (aapke account mein) <span>+₹1,499</span></label>
<label><input type="checkbox" value="999" data-n="Logo + brand kit"> Logo + brand kit <span>+₹999</span></label>
<label><input type="checkbox" value="1999" data-n="Hindi+English"> Hindi + English dono <span>+₹1,999</span></label>
<label><input type="checkbox" value="999" data-n="10 post"> 10 social post <span>+₹999</span></label>
<label><input type="checkbox" value="349" data-n="Care plan (mahina)" id="carebox"> Care plan — har mahina, kabhi bhi band <span>₹349/m</span></label>
<div class="tot">Andaza: <span id="tot">₹2,999</span></div>
<button class="cta" style="border:none;width:100%;cursor:pointer" onclick="useCustom()">Isi ka quote maangein</button>
</div>

<h2 id="form">Apna kaam likhiye</h2>
<form class="findb" id="findb"><b>Pehle se kaam diya hai? Apna haal dekhiye</b><br><span id="lastk"></span>
<div class="two"><div><label class="kit-lab" for="fid">Kaam number</label><input id="fid" name="fid" placeholder="jaise: SH261124AB3X" autocomplete="off" autocapitalize="characters" spellcheck="false"></div>
<div><label class="kit-lab" for="fl4">Mobile ke aakhri 4 ank</label><input id="fl4" name="fl4" placeholder="jaise: 3210" inputmode="numeric" maxlength="4"></div></div>
<button type="submit" id="fbtn">Dekhein</button> <small id="fmsg"></small></form>
<div class="bld"><form id="fm">
<div class="two"><div><label class="kit-lab" for="f_name">Aapka naam *</label><input id="f_name" name="name" required maxlength="80" autocomplete="name" placeholder="jaise: Ramesh Kumar"></div>
<div><label class="kit-lab" for="f_ph">Mobile number (WhatsApp) *</label><input id="f_ph" name="phone" type="tel" required inputmode="tel" autocomplete="tel-national" maxlength="16" placeholder="jaise: 98XXXXXXXX — 10 ank"></div></div>
<label class="kit-lab" for="svc">Kaam <small>(upar list se chunein ya khud likhein)</small></label><input name="service" id="svc" placeholder="jaise: Resume / PM Kisan form">
<div id="intake"></div>
<div id="fwrap"></div>
<label class="kit-lab" for="f_msg">Kya chahiye? * <small>Hindi mein likhiye, jaise ghar mein bolte hain</small></label>
<textarea id="f_msg" name="message" required rows="3" maxlength="3000" placeholder="jaise: naukri ke liye resume chahiye / scholarship form bharna hai / phone mein UPI nahi chal raha"></textarea>
<div class="two"><div><label class="kit-lab" for="f_bud">Budget ₹ <small>(zaroori nahi)</small></label><input id="f_bud" name="budget" inputmode="numeric" placeholder="jaise: 500"></div>
<div><label class="kit-lab" for="code">Code <small>(reel ya dost se mila ho)</small></label><input name="code" id="code" placeholder="jaise: MONEY10" style="text-transform:uppercase" autocomplete="off"></div></div>
<label style="font-size:.85rem"><input type="checkbox" name="urgent" style="width:auto"> Jaldi chahiye (urgent +50%)</label><br>
<label style="font-size:.85rem"><input type="checkbox" name="care" style="width:auto"> Har mahine dekhbhal bhi chahiye</label>
<input name="hp_fax" style="position:absolute;left:-5000px;width:1px;height:1px;opacity:0" tabindex="-1" autocomplete="new-password" aria-hidden="true">
<input type="hidden" name="extras" id="extras">
<div class="sum" id="sum">Kaam chunein to andaza yahan dikhega.</div>
<label style="font-size:.8rem;color:var(--muted)"><input type="checkbox" name="consent" required style="width:auto"> Main sahmat hoon ki meri jaankari sirf is kaam ke liye istemaal ho (90 din baad mita di jaati hai). <a href="/privacy">Privacy</a> · <a href="/terms">Terms</a></label>
<button class="cta" type="submit" style="border:none;width:100%;cursor:pointer">Bhejiye ✔</button>
</form><div class="okm" id="ok"></div><div id="help"></div></div>

""" + TABLE + """
<h2>Kaise kaam hota hai</h2>
<ol><li>Aap likhte hain (form, WhatsApp ya comment) — Hindi mein, jaise bolte hain</li><li>Hum call/WhatsApp par kaam samajhte hain, phir <b>aapke apne page</b> par likhit rate aata hai (sirf wahi pakka)</li>
<li>Aap "Haan" dabate hain — wahin UPI QR (rakam bhari hui). Advance (chhote kaam par pura), kaam shuru</li><li><b>Demo</b> dekhiye, 2 badlav shaamil</li>
<li>Baaki payment ke baad <b>final file, code aur account aapke naam</b></li></ol>
<div class="box"><b>Care plan:</b> har mahine ka plan hai — kabhi bhi band kar sakte hain. Charge sirf tab tak jab tak service chal rahi hai. Agar hum kabhi service band karein to 30 din pehle batayenge aur saara code/access aapko de denge.</div>
""" + FAQ_HTML + """
<div class="disc">⚠️ Trading tool sirf aapki apni strategy ka code hai — hum SEBI-registered advisor nahi, koi tip/signal/profit ka vaada nahi. Broker par apne aap order lagane wala bot hum nahi banate (SEBI algo niyam 2025). Ye page aam jaankari hai; tax/kanooni faisle ke liye CA/vakil se salah lein.</div>
</div></main>
<div class="cbar"><span>Seedha baat:</span><a id="waf" class="cb-wa" href="https://wa.me/919917436371?text=Namaste%2C%20mujhe%20ek%20kaam%20karwana%20hai" rel="nofollow noopener" target="_blank">WhatsApp</a><a id="tgf" class="cb-tg" href="#" rel="nofollow noopener" target="_blank" style="display:none">Telegram</a></div>
"""

JS = """<script src="/svc-cfg.js"></script>
<script src="/svc-offer.js"></script>
<script src="/svc-intake.js"></script>
<script src="/svc-kit.js"></script>
<script>
var CATS=__CATS__,cur='all',$=function(i){return document.getElementById(i)};
var IT=[].map.call(document.querySelectorAll('#list .it'),function(e){return {id:e.getAttribute('data-i'),cat:e.getAttribute('data-c'),name:e.querySelector('b').textContent,price:+e.getAttribute('data-p'),days:e.getAttribute('data-d'),el:e}});
var Q=new URLSearchParams(location.search);if(Q.get('code'))$('code').value=Q.get('code').toUpperCase();
function rs(n){return '₹'+Number(n).toLocaleString('en-IN')}
function ev(d,t,n){try{if(window.SVC_API)navigator.sendBeacon?navigator.sendBeacon(window.SVC_API+'/ev',new Blob([JSON.stringify({d:d,t:t,n:n||0})],{type:'text/plain'})):0}catch(e){}}
function draw(){var q=$('q').value.toLowerCase().trim(),ws=q?q.split(/\\s+/):[],seen={},tot=0;IT.forEach(function(i){var t=(i.name+' '+CATS[i.cat].title+' '+i.id).toLowerCase();
var ok=(cur==='all'||i.cat===cur)&&(!q||t.indexOf(q)>=0||ws.every(function(w){return t.indexOf(w)>=0}));i.el.classList.toggle('hid',!ok);if(ok){seen[i.cat]=1;tot++}});
[].forEach.call(document.querySelectorAll('#list .sec'),function(d){var c=d.id.slice(2);d.classList.toggle('hid',!seen[c]);if(q||cur!=='all')d.open=!!seen[c]});$('nf').style.display=tot?'none':''}
function anyKaam(){$('svc').value='Koi bhi kaam (custom)';$('sum').innerHTML='<b>Koi bhi kaam</b><br>Neeche apni zaroorat likhiye — hum padh kar likhit quote bhejenge.';location.hash='form';kit('custom');$('fm').querySelector('textarea').focus();ev('any','c')}
var cb='<button data-c="all" class="on">Sab (__N__)</button>';for(var k in CATS)cb+='<button data-c="'+k+'">'+CATS[k].title+'</button>';$('cats').innerHTML=cb;
$('cats').onclick=function(e){var c=e.target.getAttribute('data-c');if(!c)return;cur=c;[].forEach.call($('cats').children,function(b){b.className=b.getAttribute('data-c')===c?'on':''});draw();if(c!=='all'){var d=$('c-'+c);if(d){d.open=true;d.scrollIntoView({behavior:'smooth',block:'start'})}}};
$('list').addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('[data-pick]');if(b)pick(b.getAttribute('data-pick'))});
$('q').oninput=draw;
function pick(id){var i=IT.filter(function(x){return x.id===id})[0];$('svc').value=i.name;$('sum').innerHTML='<b>'+i.name+'</b><br>Shuruaati rate '+rs(i.price)+' · '+i.days+'<br><small>Final likhit quote kaam dekh kar.</small>';location.hash='form';kit(i.id);ev('pick-'+i.cat,'c')}
function tot(){var t=+$('bt').value,n=[$('bt').selectedOptions[0].text];[].forEach.call(document.querySelectorAll('#bld input:checked'),function(c){t+=+c.value;n.push(c.getAttribute('data-n'))});$('tot').textContent=rs(t);return [t,n]}
$('bld').addEventListener('change',tot);
function useCustom(){var r=tot();$('svc').value='Custom: '+r[1].join(' + ');$('extras').value=r[1].join(', ');$('sum').innerHTML='<b>Custom kaam</b><br>Andaza '+rs(r[0])+'<br><small>Final likhit quote kaam dekh kar.</small>';location.hash='form';kit('w-1page');ev('custom','c')}
function clog(w){try{var u=(window.SVC_API||'/api')+'/clog';navigator.sendBeacon?navigator.sendBeacon(u,new Blob([JSON.stringify({w:String(w).slice(0,150)})],{type:'text/plain'})):0}catch(e){}}
window.addEventListener('error',function(e){clog('js: '+(e.message||'')+' @'+(e.lineno||''))});
function kit(id){if(!window.SVCKIT)return;SVCKIT.fields($('intake'),SVCKIT.kind(id));$('fwrap').innerHTML=SVCKIT.fileInput();var nk=$('intake').querySelector('[data-k=naam]');if(nk){if(!nk.value&&$('f_name').value){nk.value=$('f_name').value;nk.dataset.auto=1}nk.addEventListener('input',function(){delete nk.dataset.auto})}}
document.addEventListener('input',function(e){if(e.target&&e.target.id==='f_name'){var n=$('intake')&&$('intake').querySelector('[data-k=naam]');if(n&&(!n.value||n.dataset.auto)){n.value=e.target.value;n.dataset.auto=1}}});
function api(path,body,ms){var bases=[window.SVC_API||'/api'];if(window.SVC_API2)bases.push(window.SVC_API2);var i=0;
return new Promise(function(ok,no){(function go(){var c=window.AbortController?new AbortController():null,t=setTimeout(function(){c&&c.abort()},ms||10000);
fetch(bases[i]+path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body),signal:c?c.signal:undefined}).then(function(r){clearTimeout(t);return r.json().then(function(j){if(!r.ok){var e=new Error(j.error||'galti');e.hard=r.status>=400&&r.status<500;throw e}return j})}).then(ok).catch(function(e){clearTimeout(t);if(!e.hard&&++i<bases.length)return go();no(e)})})()})}
function qsave(d){try{var a=JSON.parse(localStorage.getItem('svcq')||'[]');a.push(d);localStorage.setItem('svcq',JSON.stringify(a.slice(-5)))}catch(e){}}
function qflush(){try{var a=JSON.parse(localStorage.getItem('svcq')||'[]');if(!a.length)return;localStorage.setItem('svcq','[]');a.forEach(function(d){api('/lead',d,15000).then(function(j){done(j,d)}).catch(function(e){if(!e.hard)qsave(d)})})}catch(e){}}
function done(j,d){var u='/q?id='+j.id+'&k='+j.k;try{localStorage.setItem('svclast',u)}catch(e){}
var sh='https://wa.me/?text='+encodeURIComponent('Koi bhi digital kaam — ho jayega (resume ₹10 se). Mera code '+j.ref+' daalo, pehle kaam par 10% off: https://sabhisaab.com/services-list?code='+j.ref);
$('fm').style.display='none';$('ok').style.display='block';$('ok').innerHTML='<b>✔ Aapka kaam mil gaya! Number: '+j.id+'</b><br>Hum jaldi call/WhatsApp karke kaam samjhenge. Rate aur payment aapke <b>apne page</b> par aayega:<br><a class="cta" style="display:inline-block;margin:8px 0" href="'+u+'">Mera page kholein</a><br><small>Is page ko save/bookmark kar lijiye — sirf aapke liye hai.</small><br><a class="cb-wa" style="display:inline-block;color:#fff;border-radius:100px;padding:8px 14px;text-decoration:none;margin:4px 0" target="_blank" rel="noopener" href="https://wa.me/'+(window.SVC_WA||'919917436371')+'?text='+encodeURIComponent('Namaste, maine kaam bheja hai. Number: '+j.id)+'">WhatsApp par bhi batayein</a> '+(window.SVC_TG?'<a class="cb-tg" style="display:inline-block;color:#fff;border-radius:100px;padding:8px 14px;text-decoration:none" target="_blank" rel="noopener" href="https://t.me/'+window.SVC_TG+'">Telegram par baat</a>':'')+'<br>Dost ko bhejiye: <a href="'+sh+'" target="_blank" rel="noopener">Share karein</a> — code <b>'+j.ref+'</b> se dost ko 10% off, aapko uske bill ka 10% bonus.';ev('form','c')}
$('fm').onsubmit=function(e){e.preventDefault();var b=e.target.querySelector('button[type=submit]'),d=Object.fromEntries(new FormData(e.target));
d.urgent=!!d.urgent;d.care=!!d.care;d.consent=!!d.consent;d.src=Q.get('utm_source')||document.referrer.slice(0,100);d.page='services-list';
d.cid=d.cid||(Date.now().toString(36)+Math.random().toString(36).slice(2,8));if(window.SVCKIT)d.fields=SVCKIT.values($('intake'));var FL=($('fwrap').querySelector('input[type=file]')||{}).files||[];
var wa='https://wa.me/'+(window.SVC_WA||'919917436371')+'?text='+encodeURIComponent('Namaste, kaam: '+(d.service||'')+' | '+d.message+' | '+d.name);
b.disabled=true;b.textContent='Bhej rahe hain…';
api('/lead',d,10000).then(function(j){done(j,d);if(FL.length&&window.SVCKIT){var o=$('ok');o.insertAdjacentHTML('beforeend','<p id="fprog">📎 File bhej rahe hain…</p>');SVCKIT.upload(j.id,j.k,FL,function(i,n,nm){$('fprog').textContent='📎 File '+(i+1)+'/'+n+' bhej rahe hain…'}).then(function(r){$('fprog').innerHTML='📎 '+r.ok+' file pahunch gayi'+(r.bad.length?' · nahi gayi: '+r.bad.join(', ')+' — apne page se ya <a href="https://wa.me/'+(window.SVC_WA||'919917436371')+'?text='+encodeURIComponent('Mera number '+j.id+' - files bhej raha hoon')+'">WhatsApp</a> par bhejiye':'')})}}).catch(function(x){b.disabled=false;b.textContent='Bhejiye ✔';
if(x.hard){clog('hard: '+x.message);$('ok').style.display='block';$('ok').innerHTML='<b>⚠ '+x.message+'</b><br>Theek karke dobara bhejiye, ya <a href="'+wa+'">WhatsApp par bhejiye</a>.';return}
clog('net: '+x.message);
qsave(d);$('ok').style.display='block';$('ok').innerHTML='<b>Network dheema hai.</b> Aapka sandesh is phone mein surakshit hai — net aate hi apne aap chala jayega (page khula rakhein ya dobara kholein). Chahein to abhi <a href="'+wa+'">WhatsApp par bhejein</a>.'})};
window.addEventListener('online',qflush);setTimeout(qflush,1500);
[].forEach.call(document.querySelectorAll('.demo'),function(a){a.addEventListener('click',function(){ev(a.getAttribute('data-d'),'c')})});
var t0=Date.now();ev('list','v');document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden')ev('list','s',Math.round((Date.now()-t0)/1000))});
(function(){var o=window.SVC_OFFER;if(!o||!o.sale)return;var h='',d=new Date(Date.now()+19800000).toISOString().slice(0,10);
if(o.sale.start<=d&&d<=o.sale.end)h+='<div class="sum" style="background:#FEF3C7"><b>🏷 Is hafte ('+o.sale.start.slice(8)+'–'+o.sale.end.slice(8)+'):</b> '+o.sale.name+' — <s>'+rs(o.sale.price)+'</s> <b>'+rs(o.sale.now)+'</b> se ('+o.sale.end+' tak) <button data-i="'+o.sale.item+'" onclick="pick(this.getAttribute(&quot;data-i&quot;))" style="border:none;background:var(--brand);color:#fff;border-radius:8px;padding:4px 10px">Ye chahiye</button></div>';
if(o.fest&&o.fest.start<=d&&d<=o.fest.end)h+='<div class="sum" style="background:#FCE7F3"><b>🎉 '+o.fest.name_hi+' offer:</b> '+o.fest.end+' tak har kaam par '+o.fest.pct+'% tak chhoot (har kaam ki nichli seema ke andar).</div>';
document.getElementById('offer').innerHTML=h})();
if(window.SVCKIT){kit('custom');SVCKIT.help($('help'),'Namaste, services ke baare mein poochna hai')}
if(window.SVC_TG){$('tgf').href='https://t.me/'+window.SVC_TG;$('tgf').style.display=''}
try{var LU=localStorage.getItem('svclast');if(LU)$('lastk').innerHTML='Is phone se bheja kaam: <a href="'+LU+'">Mera page kholein</a><br>'}catch(e){}
if(window.SVCKIT){SVCKIT.enhance($('fm'),{labels:false,f:{name:[0,null,'name'],phone:[0,null,'phone'],message:[0,null,'msg']}});SVCKIT.enhance($('findb'),{labels:false,f:{fid:[0,null,'id'],fl4:[0,null,'l4']}})}
$('findb').onsubmit=function(e){e.preventDefault();var id=$('fid').value.trim().toUpperCase(),l4=$('fl4').value.replace(/\\D/g,'');if(!/^SH[A-Z0-9]{3,}$/.test(id)||l4.length!==4){$('fmsg').textContent='Kaam number (SH...) aur mobile ke aakhri 4 ank likhiye';return}
$('fmsg').textContent='Dhoondh rahe hain…';api('/find',{id:id,last4:l4},10000).then(function(j){location.href='/q?id='+j.id+'&k='+j.k}).catch(function(e){$('fmsg').textContent=e.message})};
$('waf').addEventListener('click',function(){ev('wa','c')});draw();if(Q.get('svc')&&IT.some(function(x){return x.id===Q.get('svc')}))pick(Q.get('svc'));
</script>"""
JS = JS.replace("__CATS__", json.dumps({k: {"title": v["title"]} for k, v in cats.items()}, ensure_ascii=False)).replace("__N__", str(N_ALL))
CATALOG = {"@context": "https://schema.org", "@type": "Service", "name": "Sab Hisaab digital kaam", "areaServed": "IN", "url": "https://sabhisaab.com/services-list",
           "provider": {"@type": "Organization", "name": "Sab Hisaab", "url": "https://sabhisaab.com/"},
           "hasOfferCatalog": {"@type": "OfferCatalog", "name": f"{N_ALL} kaam ki rate list", "itemListElement": [
               {"@type": "OfferCatalog", "name": cats[k]["title"], "url": f"https://sabhisaab.com/services-list#c-{k}",
                "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": i["name"]}, "priceCurrency": "INR",
                                     "price": i["price"]} for i in sorted((i for i in items if i["cat"] == k), key=lambda x: x["price"])[:5]]}
               for k in ORDER if any(i["cat"] == k for i in items)]}}

art = {"@context": "https://schema.org", "@type": "Article", "headline": TITLE, "author": {"@type": "Organization", "name": "Sab Hisaab"},
       "publisher": {"@type": "Organization", "name": "Sab Hisaab"}, "datePublished": "2026-11-23", "dateModified": __import__("datetime").date.today().isoformat(),
       "inLanguage": "hi-Latn", "mainEntityOfPage": "https://sabhisaab.com/services-list"}
faqld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
OG = (f'<meta property="og:title" content="{TITLE}"><meta property="og:description" content="{DESC}">'
      '<meta property="og:url" content="https://sabhisaab.com/services-list"><meta property="og:image" content="https://sabhisaab.com/sab-hisaab-og.png">'
      '<meta property="og:type" content="website">')
ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sabhisaab.com/"},
    {"@type": "ListItem", "position": 2, "name": "Services", "item": "https://sabhisaab.com/services"},
    {"@type": "ListItem", "position": 3, "name": "Rate list", "item": "https://sabhisaab.com/services-list"}]}
head_clean = re.sub(r'<script type="application/ld\+json">.*?</script>\s*', "", head, flags=re.S)
page = (head_clean + style + EXTRA_CSS + f'<script type="application/ld+json">{json.dumps(ld)}</script><script type="application/ld+json">{json.dumps(art, ensure_ascii=False)}</script><script type="application/ld+json">{json.dumps(faqld, ensure_ascii=False)}</script><script type="application/ld+json">{json.dumps(CATALOG, ensure_ascii=False)}</script>' + OG + '\n</head>\n' +
        BODY + foot.replace('<script src="/install-app.js" defer></script>', JS + '\n<script src="/install-app.js" defer></script>'))
page = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{TITLE}">', page)
page = page.replace('content="https://sabhisaab.com/services">', 'content="https://sabhisaab.com/services-list">')
_td = __import__("datetime").date.today()
_MH = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
page = page.replace("__TODAY__", _td.isoformat()).replace("__TODAY_H__", f"{_td.day} {_MH[_td.month - 1]} {_td.year}")   # v3.9.3: mobile par bhi tareekh
open(out, "w", encoding="utf-8").write(page)
print("ok", len(page))
