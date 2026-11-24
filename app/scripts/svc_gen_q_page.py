"""/q page: customer ka gupt page (noindex). services.html ka head/style/footer + status, rate, Haan, UPI QR, rating, share.
python3 gen_q_page.py site/services.html site/q.html"""
import re
import sys

src, out = sys.argv[1:3]
S = open(src, encoding="utf-8").read()
head = S[:S.index("<style>")]
style = S[S.index("<style>"):S.index("</style>") + 8]
foot = S[S.index("<footer>"):]
TITLE = "Aapka kaam - Sab Hisaab"
head = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", head, flags=re.S)
head = re.sub(r'<meta name="description" content="[^"]*"\s*/?>', '<meta name="description" content="Aapke kaam ka haal, rate aur payment - sirf aapke liye.">', head)
head = re.sub(r'<link rel="canonical"[^>]*>', '<link rel="canonical" href="https://sabhisaab.com/q">', head)
head = re.sub(r'<meta name="robots"[^>]*>', '', head)
head = head.replace("<head>", '<head>\n<meta name="robots" content="noindex,nofollow">', 1)
head = re.sub(r'<script type="application/ld\+json">.*?</script>', '', head, flags=re.S)   # gupt page - schema nahi
head = re.sub(r'<meta property="og:[^>]*>\s*', '', head)
head = re.sub(r'<meta name="twitter:[^>]*>\s*', '', head)
# gupt link (k) analytics/ad tool tak na jaye: is page par GA/ads script nahi, sirf khaali gtag
head = re.sub(r'<script[^>]*googletagmanager[^>]*>\s*</script>', '', head)
head = re.sub(r'<script[^>]*pagead2[^>]*>\s*</script>', '', head)
head = re.sub(r'<script>(?:(?!</script>).)*gtag\((?:(?!</script>).)*</script>', '', head, flags=re.S)
head = head.replace('<meta name="robots" content="noindex,nofollow">', '<meta name="robots" content="noindex,nofollow"><meta name="referrer" content="no-referrer"><script>window.dataLayer=[];function gtag(){}</script>', 1)

CSS = """<style>
footer .wrap{overflow-wrap:anywhere}footer .wrap a{display:inline-block;margin:2px 7px}#shConsent{max-width:100vw;box-sizing:border-box}#shConsent button{white-space:normal;max-width:100%}html,body{max-width:100%;overflow-x:hidden}
.qw{max-width:640px;margin:0 auto;padding:0 18px 30px}
.box{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px;margin:12px 0}
.steps{display:flex;gap:4px;flex-wrap:wrap;margin:8px 0}.steps span{font-size:.74rem;border-radius:100px;padding:3px 9px;background:#EEF2F3;color:#64748B}
.steps span.d{background:#CCFBF1;color:#115E59}.steps span.c{background:var(--brand);color:#fff;font-weight:700}
.amt{font-size:2rem;font-weight:800;color:var(--brand)}.mk{color:#8a979c;text-decoration:line-through;font-size:.9rem}
.big{display:block;width:100%;border:none;border-radius:12px;padding:14px;font:inherit;font-weight:700;font-size:1.05rem;cursor:pointer;
 background:var(--brand);color:#fff;text-align:center;text-decoration:none;margin-top:10px}
.big.alt{background:#fff;color:var(--brand);border:2px solid var(--brand)}
#qr{display:flex;justify-content:center;margin:12px 0}#qr img,#qr canvas{width:220px!important;height:220px!important}
.stars button{font-size:2rem;background:none;border:none;cursor:pointer;color:#CBD5E1}.stars button.on{color:#F59E0B}
.muted{color:var(--muted);font-size:.85rem}.err{background:#FEF2F2;border:1px solid #FECACA;border-radius:12px;padding:12px}
</style>"""

BODY = """<body>
<header><div class="hrow"><a href="/" class="logo">Sab<span>Hisaab</span></a>
<nav class="hnav"><a href="/services-list">Services</a><a href="/contact">Contact</a></nav></div></header>
<main><div class="qw">
<h1 style="margin-top:14px">Aapka kaam</h1>
<p class="muted">Ye page sirf aapke liye hai — link kisi ko na dein. Koi bhi digital kaam — ho jayega.</p>
<div id="app"><div class="box">Load ho raha hai…</div></div>
<div id="qhelp"></div>
</div></main>
<script src="/svc-cfg.js"></script>
<script src="/svc-intake.js"></script>
<script src="/svc-kit.js"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js" integrity="sha512-CNgIRecGo7nphbeZ04Sc13ka07paqdeTu0WR1IM4kNcpmBAUSHSQX0FslNhTDadL4O5SAGapGt4FodqL8My0mA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
<script>
(function(){
var P=new URLSearchParams(location.search),ID=P.get('id')||'',K=P.get('k')||'',A=document.getElementById('app'),S=null;
var NAMES={new:'Mila',talk:'Baat hui',rate:'Rate aaya',accepted:'Haan',paid:'Paisa mila',working:'Kaam chalu',delivered:'Taiyaar',feedback:'Rating',closed:'Band',lost:'Band'};
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function rs(n){return '₹'+Number(n||0).toLocaleString('en-IN')}
function bases(){var b=[window.SVC_API||'/api'];if(window.SVC_API2)b.push(window.SVC_API2);return b}
function call(path,opt){var b=bases(),i=0;return new Promise(function(ok,no){(function go(){var c=window.AbortController?new AbortController():null,t=setTimeout(function(){c&&c.abort()},10000);
fetch(b[i]+path,Object.assign({signal:c?c.signal:undefined},opt||{})).then(function(r){clearTimeout(t);return r.json().then(function(j){if(!r.ok){var e=new Error(j.error||'galti');e.hard=r.status<500;throw e}return j})}).then(ok)
.catch(function(e){clearTimeout(t);if(!e.hard&&++i<b.length)return go();no(e)})})()})}
function post(path,body){return call(path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)})}
function wa(t){return 'https://wa.me/'+(window.SVC_WA||'919917436371')+'?text='+encodeURIComponent(t)}
function upi(p){return 'upi://pay?pa='+encodeURIComponent(p.upi)+'&pn='+encodeURIComponent(p.pn)+'&am='+encodeURIComponent(p.am)+'&cu=INR&tn='+encodeURIComponent(p.tn)}
function draw(s){S=s;var i=s.stages.indexOf(s.status),h='';
h+='<div class="box"><b>Number: '+esc(s.id)+'</b> · '+esc(s.name)+' ji<div class="steps">';
['new','talk','rate','accepted','working','delivered'].forEach(function(k){var j=s.stages.indexOf(k);h+='<span class="'+(k===s.status?'c':(j<i?'d':''))+'">'+NAMES[k]+'</span>'});
h+='</div><div class="muted">Aapka kaam: '+esc(s.service||s.msg)+'</div></div>';
if(s.status==='new'||s.status==='talk'){h+='<div class="box"><b>Kaam mil gaya ✔</b><p>Hum call/WhatsApp karke kaam samjhenge, phir rate isi page par aayega. Jaldi ho to:</p><a class="big alt" href="'+wa('Namaste, mera number '+s.id+' hai')+'">WhatsApp par likhein</a>'+(window.SVC_TG?'<a class="big alt" target="_blank" rel="noopener" href="https://t.me/'+window.SVC_TG+'">Telegram par likhein</a>':'')+'</div>'}
var q=s.quote;
if(q&&['rate','accepted','paid','working','delivered','feedback'].indexOf(s.status)>=0){
h+='<div class="box"><b>'+esc(q.name)+'</b><div class="amt">'+rs(q.final)+'</div>'+(q.off?'<span class="mk">'+rs(q.base)+'</span> ':'')+
'<div class="muted">Pehle: '+rs(q.advance)+' · Samay: '+esc(q.days)+' · 2 badlav shaamil · final file poore payment ke baad'+(q.valid?' · '+esc(q.valid)+' tak valid':'')+'</div>'+(q.note?'<p>'+esc(q.note)+'</p>':'');
if(s.status==='rate')h+='<button class="big" id="yes">Haan, theek hai — aage badhein</button><a class="big alt" href="'+wa('Mera number '+s.id+' - rate par baat karni hai')+'">Kuch poochna hai</a>';
h+='</div>'}
if(s.pay&&['accepted','paid','working'].indexOf(s.status)>=0&&+s.pay.am>0){
h+='<div class="box"><b>Payment — '+rs(s.pay.am)+'</b><p class="muted">Kisi bhi UPI app (PhonePe, GPay, Paytm, BHIM) se. Rakam pehle se bhari hai.</p><div id="qr"></div>'+
'<a class="big" href="'+upi(s.pay)+'">UPI app se pay karein</a><p class="muted">Pay karne ke baad hum bank mein dekh kar yahan "Paisa mila" kar denge (thoda samay lag sakta hai). Screenshot zaroori nahi.</p></div>'}
if(s.status==='working')h+='<div class="box"><b>Kaam chalu hai 🛠</b>'+(s.due?'<p>Taiyaar hone ki tarikh: '+esc(s.due)+'</p>':'')+'</div>';
if(['new','talk','rate','accepted','paid','working'].indexOf(s.status)>=0&&window.SVCKIT){h+='<div class="box"><b>📝 Kaam ki details aur files</b>'+(s.details?' <span class="muted">✔ '+s.details+' jaankari mil chuki</span>':'')+
'<p class="muted">Jitna pata ho likhiye/bhejiye — photo, PDF, Word, voice note sab chalega. Baaki hum baat karke pooch lenge.</p><div id="qi"></div><button class="big alt" id="qsave" type="button">Details bhejein</button>'+
'<div id="qf">'+SVCKIT.fileInput()+'</div><button class="big" id="qup" type="button">File bhejein</button><p class="muted" id="qmsg"></p>'+
((s.files&&s.files.length)?'<p class="muted">Pahunchi: '+s.files.map(function(f){return esc(f.name)}).join(', ')+'</p>':'')+
'<a class="big alt" target="_blank" rel="noopener" href="'+wa('Mera number '+s.id+' - files/jaankari bhej raha hoon')+'">Bahut files hain? WhatsApp par bhejiye</a></div>'}
if(s.status==='delivered'&&!s.rated){h+='<div class="box"><b>Kaam taiyaar ✔</b>'+(s.deliver?'<p>'+esc(s.deliver)+'</p>':'')+'<p>Kaisa laga? Star dijiye:</p><div class="stars" id="st">'+[1,2,3,4,5].map(function(n){return '<button data-n="'+n+'" aria-label="'+n+' star">★</button>'}).join('')+'</div>'+
'<textarea id="rv" rows="3" maxlength="500" style="width:100%;border:1px solid var(--line);border-radius:12px;padding:10px;font:inherit" placeholder="Do shabd (Hindi mein chalega)"></textarea>'+
'<label class="muted"><input type="checkbox" id="show"> Mera pehla naam aur ye baat website par dikha sakte hain</label><br>'+
'<label class="muted"><input type="checkbox" id="smp"> Mera kaam (naam/number chhupa kar) namoone ki tarah dikha sakte hain</label>'+
'<button class="big" id="send">Bhejein</button></div>'}
if(s.rated||s.status==='feedback')h+='<div class="box"><b>Dhanyavaad 🙏</b> Aapki rating mil gayi.</div>';
if(s.status==='lost'||s.status==='closed')h+='<div class="box">Ye kaam band hai. Naya kaam? <a href="/services-list">Yahan likhiye</a></div>';
var sh='https://wa.me/?text='+encodeURIComponent('Koi bhi digital kaam — ho jayega (resume ₹10 se, Hindi mein likho). Mera code '+s.ref+' daalo, pehle kaam par 10% off: https://sabhisaab.com/services-list?code='+s.ref);
h+='<div class="box"><b>Dost ko bhejiye</b><p class="muted">Code <b>'+esc(s.ref)+'</b> se dost ko pehle kaam par 10% off — aapko uske chukaye bill ka 10% bonus (₹300+ bill par, max ₹500, agle kaam mein, 90 din tak).</p><a class="big alt" target="_blank" rel="noopener" href="'+sh+'">WhatsApp par share karein</a></div>';
A.innerHTML=h;
if(window.SVCKIT&&document.getElementById('qi')){SVCKIT.fields(document.getElementById('qi'),SVCKIT.kind(s.item||'custom'));
var qm=document.getElementById('qmsg');document.getElementById('qsave').onclick=function(){var v=SVCKIT.values(document.getElementById('qi'));if(!Object.keys(v).length){qm.textContent='Pehle kuch likhiye';return}
qm.textContent='Bhej rahe hain…';post('/q/info',{id:ID,k:K,fields:v}).then(function(x){S=x;qm.textContent='✔ Details pahunch gayi'}).catch(function(e){qm.textContent=e.message})};
document.getElementById('qup').onclick=function(){var fl=document.querySelector('#qf input[type=file]').files;if(!fl.length){qm.textContent='Pehle file chunein';return}
SVCKIT.upload(ID,K,fl,function(i,n){qm.textContent='File '+(i+1)+'/'+n+' bhej rahe hain…'}).then(function(r){qm.textContent='✔ '+r.ok+' file pahunchi'+(r.bad.length?' · nahi gayi: '+r.bad.join(', '):'');load()})}}
var y=document.getElementById('yes');if(y)y.onclick=function(){y.disabled=true;y.textContent='…';post('/q/ok',{id:ID,k:K}).then(draw).catch(function(e){alert(e.message);y.disabled=false})};
if(s.pay&&document.getElementById('qr')){(function mk(n){if(window.QRCode){new QRCode(document.getElementById('qr'),{text:upi(s.pay),width:220,height:220})}else if(n<40)setTimeout(function(){mk(n+1)},150)})(0)}
var st=document.getElementById('st'),N=0;if(st)st.onclick=function(e){var n=+e.target.getAttribute('data-n');if(!n)return;N=n;[].forEach.call(st.children,function(b){b.className=+b.getAttribute('data-n')<=n?'on':''})};
var sd=document.getElementById('send');if(sd)sd.onclick=function(){if(!N){alert('Star chunein');return}sd.disabled=true;post('/q/rate',{id:ID,k:K,stars:N,text:document.getElementById('rv').value,show:document.getElementById('show').checked,sample:document.getElementById('smp').checked}).then(draw).catch(function(e){alert(e.message);sd.disabled=false})};
}
function load(){if(!ID||!K){A.innerHTML='<div class="err">Link adhoora hai. Form bhejne ke baad mila poora link kholein, ya <a href="/services-list">naya kaam likhein</a>.</div>';return}
call('/q?id='+encodeURIComponent(ID)+'&k='+encodeURIComponent(K)).then(draw).catch(function(e){A.innerHTML='<div class="err">'+esc(e.hard?e.message:'Network dheema hai - thodi der baad page dobara kholein.')+'</div>'})}
load();if(window.SVCKIT)SVCKIT.help(document.getElementById('qhelp'),'Mera number '+ID+' - madad chahiye');setInterval(function(){if(document.visibilityState==='visible'&&S&&['new','talk','rate','accepted','paid','working'].indexOf(S.status)>=0)call('/q?id='+encodeURIComponent(ID)+'&k='+encodeURIComponent(K)).then(function(s){if(s.status!==S.status||(s.pay&&!S.pay))draw(s)}).catch(function(){})},30000);
})();
</script>
"""
open(out, "w", encoding="utf-8").write(head + style + CSS + "\n</head>\n" + BODY + foot)
print("ok", out)
