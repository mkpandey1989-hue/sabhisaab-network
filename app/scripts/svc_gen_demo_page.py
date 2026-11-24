"""/services-demo: ek hi page par 8 chalne wale demo (bill, khata, stock, dukaan site, booking, menu, bot, trading backtest)."""
import json
import re
import sys

src, out = sys.argv[1:3]
S = open(src, encoding="utf-8").read()
head = S[:S.index("<style>")]
style = S[S.index("<style>"):S.index("</style>") + 8]
foot = S[S.index("<footer>"):]
TITLE = "Live Demo: Billing App, Khata, Dukaan Site, Bot | Sab Hisaab"
DESC = "Resume ₹10, GST bill app, khata, stock, dukaan website, booking, QR menu, bot aur backtest - khud chala kar dekhiye, phir apne naam se banwaiye."
head = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", head, flags=re.S)
head = re.sub(r'(<meta name="description" content=")[^"]*', r"\g<1>" + DESC, head)
head = head.replace('href="https://sabhisaab.com/services"', 'href="https://sabhisaab.com/services-demo"')
head = re.sub(r'(name="twitter:title" content=")[^"]*', r"\g<1>" + TITLE, head)

CSS = """<style>
.wrapw{max-width:980px;margin:0 auto;padding:0 20px}
.hero{background:linear-gradient(135deg,#0F766E,#134E4A);color:#fff;border-radius:20px;padding:24px 22px;margin-bottom:16px}
.hero h1{color:#fff}.hero p{color:#d8f3ef;margin:0}
.tabs{display:flex;gap:6px;overflow-x:auto;padding:4px 0 10px}
.tabs button{flex:0 0 auto;border:1px solid var(--line);background:#fff;border-radius:100px;padding:8px 14px;font:inherit;font-size:.85rem;cursor:pointer}
.tabs button.on{background:var(--brand);color:#fff;border-color:var(--brand)}
.pane{display:none;background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px;margin-bottom:14px}.pane.on{display:block}
.pane h2{margin-top:0}.pane input,.pane select{padding:10px 12px;border:1px solid var(--line);border-radius:10px;font-size:16px;font-family:inherit;max-width:100%}
.row{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}.row>*{flex:1 1 120px}
.btn{border:none;background:var(--brand);color:#fff;border-radius:10px;padding:10px 14px;font:inherit;font-weight:600;cursor:pointer}
.btn.alt{background:#fff;color:var(--brand);border:1px solid var(--brand)}
.own{display:block;text-align:center;margin-top:12px;background:#0F1720;color:#fff;border-radius:12px;padding:12px;text-decoration:none;font-weight:700}
.inv{border:1px dashed #94a3b8;border-radius:12px;padding:12px;margin-top:10px;font-size:.9rem}
.inv table{width:100%;display:table}.inv td,.inv th{padding:4px;border-bottom:1px solid #eee;text-align:left}
.low{color:#B91C1C;font-weight:700}.ok{color:#047857;font-weight:700}
.site{border-radius:16px;overflow:hidden;border:1px solid var(--line);margin-top:10px}
.site .top{padding:22px;color:#fff}.site .bd{padding:14px}.site .wa{display:inline-block;background:#25D366;color:#fff;border-radius:100px;padding:8px 14px;text-decoration:none;font-weight:700}
.slots{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}.slots button{padding:10px;border:1px solid var(--line);border-radius:10px;background:#fff;cursor:pointer;font:inherit}
.slots button.bk{background:#fee2e2;color:#991b1b;text-decoration:line-through}.slots button.me{background:#d1fae5}
.chat{background:#E7F0EE;border-radius:14px;padding:10px;height:260px;overflow:auto;font-size:.9rem}
.m{max-width:80%;padding:8px 10px;border-radius:12px;margin:6px 0;white-space:pre-line}.m.u{background:#fff;margin-left:auto}.m.b{background:#D9FDD3}
canvas{width:100%;height:220px;border:1px solid var(--line);border-radius:12px;margin-top:8px}
</style>"""

BODY = """<body>
<header><div class="hrow"><a href="/" class="logo">Sab<span>Hisaab</span></a>
<nav class="hnav"><a href="/">Tools</a><a href="/services">Services</a><a href="/contact">Contact</a></nav></div></header>
<main><div class="wrapw">
<div class="crumb"><a href="/">Home</a> &rsaquo; <a href="/services">Services</a> &rsaquo; Live demo</div>
<div class="hero"><h1>Pehle chala kar dekhiye, phir banwaiye</h1>
<p>Neeche 9 demo asli chalte hain. Apna naam, rate, saman daal kar dekhiye. Pasand aaye to "Apne naam se banwao" dabaiye — aapke dhandhe ke hisaab se badal kar, aapke account par banega.</p></div>
<div class="tabs" id="tabs"></div>

<section class="pane" id="p-resume" data-n="Resume ₹10"><h2>0. Resume — sirf ₹10</h2>
<p>Apni jaankari bhariye, resume turant ban jaata hai. Hum ise saaf format mein, galti theek karke, ₹10 mein PDF bana dete hain.</p>
<div class="row"><input id="rName" value="Rahul Negi" oninput="cv()"><input id="rJob" value="Sales Executive" oninput="cv()"></div>
<div class="row"><input id="rEdu" value="B.Com, Kumaun University (2024)" oninput="cv()"><input id="rSk" value="MS Excel, Hindi-English, Customer baat-cheet" oninput="cv()"></div>
<div class="row"><input id="rExp" value="1 saal - Negi Traders, Haldwani (billing aur stock)" oninput="cv()"></div>
<div class="inv" id="rOut" style="background:#fff"></div>
<div class="row"><button class="btn alt" onclick="window.print()">🖨 Print / PDF</button></div>
<a class="own" href="/services-list?svc=m-resume#form" data-d="demo-resume">Mera resume banwao — ₹10</a></section>

<section class="pane" id="p-bill" data-n="GST bill app"><h2>1. GST bill / invoice app</h2>
<p>Dukaan ka naam, saman, rate aur GST daaliye — bill turant banega. Print ya PDF bhi.</p>
<div class="row"><input id="bShop" value="Pandey General Store"><input id="bCust" placeholder="Customer ka naam"></div>
<div class="row"><input id="bItem" placeholder="Saman (jaise Chawal 5kg)"><input id="bQty" type="number" inputmode="numeric" value="1" min="1"><input id="bRate" type="number" inputmode="numeric" placeholder="Rate ₹"><select id="bGst"><option>0</option><option>5</option><option selected>12</option><option>18</option><option>28</option></select><button class="btn" onclick="billAdd()">+ Jodo</button></div>
<div class="inv" id="bOut"></div>
<div class="row"><button class="btn alt" onclick="window.print()">🖨 Print / PDF</button></div>
<a class="own" href="/services-list?svc=s-bill#form" data-d="demo-bill">Apne naam se banwao — ₹3,999 se</a></section>

<section class="pane" id="p-khata" data-n="Udhaar khata"><h2>2. Udhaar khata (ledger)</h2>
<p>Kisne kitna liya, kitna diya — har customer ka baaki apne aap.</p>
<div class="row"><input id="kName" placeholder="Customer"><input id="kAmt" type="number" inputmode="numeric" placeholder="₹"><select id="kTy"><option value="1">Udhaar diya</option><option value="-1">Paisa mila</option></select><button class="btn" onclick="khAdd()">Likho</button></div>
<div class="inv" id="kOut">Abhi koi entry nahi.</div>
<a class="own" href="/services-list?svc=s-khata#form" data-d="demo-khata">Apne naam se banwao — ₹2,999 se</a></section>

<section class="pane" id="p-stock" data-n="Stock alert"><h2>3. Stock + low-stock alert</h2>
<p>Maal ghatte hi laal nishaan. Asli app mein ye WhatsApp/Telegram par alert bhejta hai.</p>
<div class="row"><input id="sItem" placeholder="Saman"><input id="sQty" type="number" inputmode="numeric" placeholder="Kitna"><input id="sMin" type="number" inputmode="numeric" placeholder="Kam se kam"><button class="btn" onclick="stAdd()">Jodo</button></div>
<div class="inv" id="sOut"></div>
<a class="own" href="/services-list?svc=s-stock#form" data-d="demo-stock">Apne naam se banwao — ₹4,999 se</a></section>

<section class="pane" id="p-site" data-n="Dukaan website"><h2>4. Dukaan / clinic / coaching website</h2>
<p>Naam, kaam aur rang chuniye — aapki site kaisi dikhegi, abhi dekhiye.</p>
<div class="row"><input id="wName" value="Negi Homestay, Almora" oninput="siteDraw()"><input id="wLine" value="Pahadon ke beech ghar jaisa khana aur kamra" oninput="siteDraw()"><select id="wCol" onchange="siteDraw()"><option value="#0F766E">Hara</option><option value="#1D4ED8">Neela</option><option value="#B45309">Bhura</option><option value="#9D174D">Gulabi</option></select></div>
<div class="site" id="wOut"></div>
<a class="own" href="/services-list?svc=w-1page#form" data-d="demo-site">Apne naam se banwao — ₹2,999 se</a></section>

<section class="pane" id="p-book" data-n="Booking"><h2>5. Booking / appointment</h2>
<p>Customer khud khaali slot chune. Bhara slot apne aap band.</p>
<div class="slots" id="bkOut"></div><p id="bkMsg" style="margin-top:8px"></p>
<a class="own" href="/services-list?svc=w-book#form" data-d="demo-book">Apne naam se banwao — ₹3,999 se</a></section>

<section class="pane" id="p-menu" data-n="QR menu"><h2>6. Restaurant menu + order</h2>
<p>Table par QR scan → menu → order seedha WhatsApp par.</p>
<div class="inv" id="mOut"></div><p id="mTot" style="font-weight:700"></p>
<a class="own" href="/services-list?svc=w-menu#form" data-d="demo-menu">Apne naam se banwao — ₹2,999 se</a></section>

<section class="pane" id="p-bot" data-n="Bot"><h2>7. WhatsApp / Telegram bot</h2>
<p>Raat 2 baje bhi customer ko jawab. Neeche likh kar dekhiye: <i>rate, timing, address, order</i>.</p>
<div class="chat" id="cOut"><div class="m b">Namaste! 🙏 Main dukaan ka bot hoon. Rate, timing, address ya order likhiye.</div></div>
<div class="row"><input id="cIn" placeholder="Yahan likhiye…" onkeydown="if(event.key==='Enter')botSay()"><button class="btn" onclick="botSay()">Bhejo</button></div>
<a class="own" href="/services-list?svc=b-tg#form" data-d="demo-bot">Apne naam se banwao — ₹2,499 se</a></section>

<section class="pane" id="p-trade" data-n="Strategy backtest"><h2>8. Strategy backtest (sirf seekhne ke liye)</h2>
<p>Do moving average ka crossover — <b>namoona (banawati) data</b> par. Asli kaam mein aapki strategy, aapke data par. Ye nivesh salah nahi.</p>
<div class="row"><input id="tF" type="number" inputmode="numeric" value="9" min="2"><input id="tS" type="number" inputmode="numeric" value="21" min="3"><button class="btn" onclick="bt()">Chalao</button></div>
<canvas id="tC" width="900" height="300"></canvas><p id="tOut"></p>
<a class="own" href="/services-list?svc=t-back#form" data-d="demo-trade">Apni strategy ka backtest — ₹1,999 se</a></section>

<h2>Ye demo kyun?</h2>
<p>Bahut log puchhte hain ki banne ke baad cheez kaisi dikhegi. Isliye har aam kaam ka ek chhota, chalta hua namoona yahan hai. Aapka asli app isi tarah ka hoga, par aapke dhandhe ke hisaab se: aapka naam, logo, rang, aapke saman ki list, aapke tax ke rate, aapke customer ka data aur aapki zaroorat ke button. Demo mein jo aap bharte hain wo sirf aapke phone/browser mein rehta hai — hum use kahin save nahi karte.</p>
<p>Asli app mein aur kya jud sakta hai: kai log (staff) ka login, roz ki report WhatsApp ya Telegram par, Google Sheet mein backup, PDF bill customer ko seedha bhejna, barcode, aur mahine ka hisaab. Jo aapko chahiye wahi banta hai — zaroorat se zyada kuch nahi, taaki kharcha kam rahe aur chalana aasaan ho.</p>
<p>Rate "se" likha hai. Aapka kaam dekh kar likhit quote milta hai jisme version number hota hai — sirf wahi pakka hai. Advance ke baad kaam shuru hota hai, pehle demo dikhaya jaata hai, 2 badlav shaamil hain, aur final code, file aur account aapke naam par milta hai. Poori shartein <a href="/terms">Terms</a> ke section 8 mein hain, aur saare kaam ki suchi <a href="/services-list">rate list</a> par.</p>
<h2>Demo aur asli app mein farak</h2>
<table><thead><tr><th>Cheez</th><th>Is demo mein</th><th>Aapke asli app mein</th></tr></thead><tbody>
<tr><td>Naam, logo, rang</td><td>Namoona</td><td>Aapka apna brand</td></tr>
<tr><td>Data kahan rehta hai</td><td>Sirf aapke browser mein, page band = khatam</td><td>Aapke apne Google Sheet / server par, roz backup</td></tr>
<tr><td>Staff login</td><td>Nahi</td><td>Zaroorat ho to har staff ka alag login</td></tr>
<tr><td>Alert / report</td><td>Screen par</td><td>WhatsApp / Telegram par apne aap</td></tr>
<tr><td>Bill / receipt</td><td>Print / PDF</td><td>PDF seedha customer ko, GST ke hisaab se</td></tr>
<tr><td>Phone par</td><td>Browser mein</td><td>Home screen par app ki tarah (PWA)</td></tr>
</tbody></table>
<h2>Resume ₹10 aur form bharne mein madad</h2>
<p>Naukri dhoondh rahe log ke liye sabse pehla kaam resume hai. Bahut log ek purana format copy karke bhej dete hain jisme spelling galat hoti hai, number ya email chhoot jaata hai, ya padhai aur anubhav ulte kram mein hote hain. Hum aapki di hui jaankari ko ek saaf, ek page ke format mein lagate hain, chhoti galtiyaan theek karte hain aur PDF bhej dete hain - sirf ₹10 mein. Zyada design, LinkedIn bio ya naukri ke hisaab se alag-alag resume chahiye to uska alag rate list par likha hai.</p>
<p>Online form (naukri, admission, scholarship, sarkari yojana) bharne mein bhi madad karte hain. Jaankari aur document aapke hote hain, OTP aur password aap khud daalte hain - hum kabhi nahi maangte. Portal ki fees aap seedha portal par bharte hain; hamara charge sirf madad ka hai. Hum kisi sarkari vibhag ke agent nahi hain aur kaam ke baad aapke document apne paas nahi rakhte.</p>
<h2>Kaise shuru karein</h2>
<p>Jo demo aapke kaam ke paas ho, uska "Apne naam se banwao" button dabaiye. Form mein bas apna naam, WhatsApp number aur do-teen line mein apni zaroorat likhiye - jaise "meri kapde ki dukaan hai, 3 staff hain, roz 40 bill bante hain, udhaar wale customer bhi hain". Hum padh kar likhit quote bhejte hain. Pasand aaye to advance dijiye, hum pehle ek demo aapke naam se banakar dikhate hain, phir aapke kehne par badlav karte hain. Sab theek lage tab baaki payment, aur poora app aapke account par chalu. Koi chhoti cheez baad mein badalni ho to care plan le sakte hain, jo kabhi bhi band ho sakta hai.</p>
<div class="disc">⚠️ Trading demo banawati data par sirf samjhane ke liye hai. Hum SEBI-registered advisor nahi; koi tip, signal ya munafe ka vaada nahi. Asli bot aapke apne account aur server par aap chalate hain.</div>
</div></main>
"""

JS = r"""<script src="/svc-cfg.js"></script>
<script>
var $=function(i){return document.getElementById(i)},rs=function(n){return '₹'+(Math.round(n*100)/100).toLocaleString('en-IN')};
function ev(d,t,n){try{if(window.SVC_API&&navigator.sendBeacon)navigator.sendBeacon(window.SVC_API+'/ev',new Blob([JSON.stringify({d:d,t:t,n:n||0})],{type:'text/plain'}))}catch(e){}}
var panes=[].slice.call(document.querySelectorAll('.pane')),tb='';
panes.forEach(function(p,i){tb+='<button data-i="'+i+'">'+p.getAttribute('data-n')+'</button>'});$('tabs').innerHTML=tb;
var shown={};function show(i){panes.forEach(function(p,j){p.className='pane'+(i===j?' on':'')});[].forEach.call($('tabs').children,function(b,j){b.className=i===j?'on':''});
var id=panes[i].id.replace('p-','demo-');if(!shown[id]){shown[id]=1;ev(id,'v');if(id==='demo-trade')bt()}}
$('tabs').onclick=function(e){var i=e.target.getAttribute('data-i');if(i!==null)show(+i)};
var h=location.hash.replace('#','');show(Math.max(0,panes.findIndex(function(p){return p.id==='p-'+h})));
[].forEach.call(document.querySelectorAll('.own'),function(a){a.addEventListener('click',function(){ev(a.getAttribute('data-d'),'c')})});
var t0=Date.now();document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden')ev('demo-page','s',Math.round((Date.now()-t0)/1000))});
// 0 resume
function cv(){var g=function(i){return ($(i).value||'').replace(/</g,'')};$('rOut').innerHTML='<div style="border-left:6px solid #0F766E;padding-left:12px"><div style="font-size:1.4rem;font-weight:800">'+g('rName')+'</div><div style="color:#0F766E;font-weight:700">'+g('rJob')+'</div><small>📞 98xxxxxx10 · ✉ naam@gmail.com · Haldwani</small></div><p><b>Padhai</b><br>'+g('rEdu')+'</p><p><b>Anubhav</b><br>'+g('rExp')+'</p><p><b>Hunar</b><br>'+g('rSk').split(',').map(function(x){return '• '+x.trim()}).join('<br>')+'</p>'}cv();
// 1 bill
var BI=[{n:'Chawal 5kg',q:2,r:320,g:5},{n:'Sabun',q:3,r:40,g:18}];
function billAdd(){var n=$('bItem').value.trim(),r=+$('bRate').value;if(!n||!r)return alert('Saman aur rate daaliye');BI.push({n:n,q:+$('bQty').value||1,r:r,g:+$('bGst').value});$('bItem').value='';$('bRate').value='';bill()}
function bill(){var s=0,g=0,h='<b>'+($('bShop').value||'Dukaan')+'</b><br><small>Bill no: SH-'+(1000+BI.length)+' · '+new Date().toLocaleDateString('en-IN')+' · '+($('bCust').value||'Customer')+'</small><table><tr><th>Saman</th><th>Qty</th><th>Rate</th><th>GST</th><th>Kul</th></tr>';
BI.forEach(function(x,i){var a=x.q*x.r,t=a*x.g/100;s+=a;g+=t;h+='<tr><td>'+x.n+'</td><td>'+x.q+'</td><td>'+rs(x.r)+'</td><td>'+x.g+'%</td><td>'+rs(a+t)+'</td></tr>'});
h+='</table><p>Taxable: '+rs(s)+' · CGST: '+rs(g/2)+' · SGST: '+rs(g/2)+'<br><b>Kul: '+rs(s+g)+'</b></p>';$('bOut').innerHTML=h}
['bShop','bCust'].forEach(function(i){$(i).oninput=bill});bill();
// 2 khata
var KH={};function khAdd(){var n=$('kName').value.trim(),a=+$('kAmt').value;if(!n||!a)return;KH[n]=(KH[n]||0)+a*(+$('kTy').value);$('kAmt').value='';
var h='<table><tr><th>Customer</th><th>Baaki</th></tr>',t=0;Object.keys(KH).forEach(function(k){t+=KH[k];h+='<tr><td>'+k+'</td><td class="'+(KH[k]>0?'low':'ok')+'">'+rs(KH[k])+'</td></tr>'});$('kOut').innerHTML=h+'</table><p><b>Kul baaki: '+rs(t)+'</b></p>'}
// 3 stock
var ST=[{n:'Doodh',q:4,m:10},{n:'Bread',q:25,m:8}];function stAdd(){var n=$('sItem').value.trim();if(!n)return;ST.push({n:n,q:+$('sQty').value||0,m:+$('sMin').value||0});stock()}
function stock(){var h='<table><tr><th>Saman</th><th>Bacha</th><th>Haal</th><th></th></tr>';ST.forEach(function(x,i){h+='<tr><td>'+x.n+'</td><td>'+x.q+'</td><td class="'+(x.q<x.m?'low':'ok')+'">'+(x.q<x.m?'⚠️ Mangao':'Theek')+'</td><td><button class="btn alt" onclick="ST['+i+'].q--;stock()">−1 bika</button></td></tr>'});$('sOut').innerHTML=h+'</table>'}stock();
// 4 site
function siteDraw(){var c=$('wCol').value;$('wOut').innerHTML='<div class="top" style="background:'+c+'"><div style="font-size:1.3rem;font-weight:800">'+$('wName').value+'</div><div>'+$('wLine').value+'</div></div><div class="bd">⭐ Kamra · Khana · Ghoomna<br>📍 Map · ⏰ Timing · 📷 Photo<br><br><a class="wa" href="#" onclick="return false">WhatsApp par booking</a></div>'}siteDraw();
// 5 booking
var SL=['9:00','9:30','10:00','10:30','11:00','11:30','12:00','4:00','4:30','5:00','5:30','6:00'],BK={1:1,4:1,9:1},h5='';
SL.forEach(function(s,i){h5+='<button class="'+(BK[i]?'bk':'')+'" data-i="'+i+'">'+s+'</button>'});$('bkOut').innerHTML=h5;
$('bkOut').onclick=function(e){var i=e.target.getAttribute('data-i');if(i===null||BK[i])return;[].forEach.call($('bkOut').children,function(b){if(b.className==='me')b.className=''});e.target.className='me';$('bkMsg').textContent='✅ '+SL[i]+' ka slot chuna. Asli app mein confirmation WhatsApp par jaata hai.'};
// 6 menu
var MN=[['Aloo ke gutke',80],['Bhatt ki churkani',120],['Mandua roti (2)',40],['Chai',20]],MQ={};
function menu(){var h='<table>',t=0;MN.forEach(function(m,i){var q=MQ[i]||0;t+=q*m[1];h+='<tr><td>'+m[0]+'</td><td>'+rs(m[1])+'</td><td><button class="btn alt" onclick="MQ['+i+']=Math.max(0,(MQ['+i+']||0)-1);menu()">−</button> '+q+' <button class="btn" onclick="MQ['+i+']=(MQ['+i+']||0)+1;menu()">+</button></td></tr>'});$('mOut').innerHTML=h+'</table>';$('mTot').textContent=t?'Order: '+rs(t)+' → WhatsApp par seedha jaata':'Kuch chuniye'}menu();
// 7 bot
function botSay(){var v=$('cIn').value.trim();if(!v)return;$('cIn').value='';var c=$('cOut'),l=v.toLowerCase(),a='Samajh gaya 🙂 Dukaan wale ko bata diya, 5 min mein jawab aayega. Aap "rate", "timing" ya "order" bhi likh sakte hain.';
if(/rate|price|kitne|daam/.test(l))a='📋 Aaj ka rate:\nChawal ₹64/kg\nAata ₹38/kg\nDoodh ₹56/L';else if(/time|timing|khula|kab/.test(l))a='⏰ Subah 8 se raat 9 tak, Ravivaar 1 baje tak.';
else if(/address|kahan|pata|location/.test(l))a='📍 Mall Road, Almora (map link asli bot bhejta hai).';else if(/order|chahiye|bhejo/.test(l))a='🛒 Order ke liye saman ki list likhiye. Total + UPI link aapko bhej denge.';
c.innerHTML+='<div class="m u">'+v.replace(/</g,'')+'</div><div class="m b">'+a+'</div>';c.scrollTop=1e6}
// 8 backtest (banawati data)
function rnd(s){return function(){s=(s*9301+49297)%233280;return s/233280}}
function bt(){var f=+$('tF').value,s=+$('tS').value;if(f>=s)return alert('Pehla number chhota rakhiye');var r=rnd(7),p=[100];for(var i=1;i<300;i++)p.push(p[i-1]*(1+(r()-.48)*.03));
function ma(n,i){if(i<n)return null;var t=0;for(var k=i-n+1;k<=i;k++)t+=p[k];return t/n}
var pos=0,ent=0,pnl=0,tr=0,win=0,eq=[];for(i=1;i<p.length;i++){var a=ma(f,i),b=ma(s,i),a0=ma(f,i-1),b0=ma(s,i-1);if(a&&b&&a0&&b0){if(!pos&&a0<=b0&&a>b){pos=1;ent=p[i]}else if(pos&&a0>=b0&&a<b){var g=(p[i]-ent)/ent*100;pnl+=g;tr++;if(g>0)win++;pos=0}}eq.push(pnl)}
var cv=$('tC'),x=null;try{x=cv.getContext&&cv.getContext('2d')}catch(e){}if(!x){$('tOut').textContent='Trade: '+tr+' · Kul: '+pnl.toFixed(1)+'%';return}var W=cv.width,H=cv.height,mn=Math.min.apply(0,p),mx=Math.max.apply(0,p);x.clearRect(0,0,W,H);
function line(arr,col){x.strokeStyle=col;x.lineWidth=2;x.beginPath();arr.forEach(function(v,i){if(v===null)return;var X=i/(arr.length-1)*W,Y=H-(v-mn)/(mx-mn)*H;i&&arr[i-1]!==null?x.lineTo(X,Y):x.moveTo(X,Y)});x.stroke()}
line(p,'#94a3b8');line(p.map(function(_,i){return ma(f,i)}),'#0F766E');line(p.map(function(_,i){return ma(s,i)}),'#B45309');
$('tOut').innerHTML='Trade: '+tr+' · Jeet: '+(tr?Math.round(win/tr*100):0)+'% · Kul: '+pnl.toFixed(1)+'% <small>(banawati data, sirf samajhne ke liye)</small>';ev('demo-trade-run','c')}
</script>"""

art = {"@context": "https://schema.org", "@type": "Article", "headline": TITLE, "author": {"@type": "Organization", "name": "Sab Hisaab"},
       "publisher": {"@type": "Organization", "name": "Sab Hisaab"}, "datePublished": "2026-11-23", "dateModified": "2026-11-23",
       "inLanguage": "hi-Latn", "mainEntityOfPage": "https://sabhisaab.com/services-demo"}
bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sabhisaab.com/"},
    {"@type": "ListItem", "position": 2, "name": "Services", "item": "https://sabhisaab.com/services"},
    {"@type": "ListItem", "position": 3, "name": "Live demo", "item": "https://sabhisaab.com/services-demo"}]}
OG = (f'<meta property="og:title" content="{TITLE}"><meta property="og:description" content="{DESC}">'
      '<meta property="og:url" content="https://sabhisaab.com/services-demo"><meta property="og:image" content="https://sabhisaab.com/sab-hisaab-og.png">'
      '<meta property="og:type" content="website">')
page = (head + style + CSS + f'<script type="application/ld+json">{json.dumps(art)}</script><script type="application/ld+json">{json.dumps(bc)}</script>'
        + OG + "\n</head>\n" + BODY + foot.replace('<script src="/install-app.js" defer></script>', JS + '\n<script src="/install-app.js" defer></script>'))
open(out, "w", encoding="utf-8").write(page)
print("ok", len(page))
