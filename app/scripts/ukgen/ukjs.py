# v3.3 (14 Nov): pathak ke liye 2 chhoti suvidha - koi data save/bheja nahi jaata (privacy policy ke andar)
UK_JS = r"""<script>
(function(){var m=document.querySelector('main');if(!m)return;
var g=document.getElementById('gShare');
if(g&&('speechSynthesis' in window)&&('SpeechSynthesisUtterance' in window)){
 var b=document.createElement('button');b.type='button';b.className='ukbtn';var T0='🎧 Ye page suniye';b.textContent=T0;g.appendChild(b);
 var on=false;
 function stop(){try{window.speechSynthesis.cancel();}catch(e){}on=false;b.textContent=T0;}
 b.addEventListener('click',function(){
  if(on){stop();return;}
  var els=[].slice.call(m.querySelectorAll('h1,h2,h3,p,li,summary,.fa'));
  els=els.filter(function(el){return !el.closest('.ukrel,.srcbox,.gshare,.crumb,.meta,.toc,.uktool,.dupref,.artread,.box,.uknext,.ukpoll,script');});
  var s=window.speechSynthesis;s.cancel();on=true;b.textContent='⏹ Rokiye';
  els.forEach(function(el,i){var t=(el.innerText||'').trim();if(!t)return;
   var u=new SpeechSynthesisUtterance(t);u.lang=/[ऀ-ॿ]/.test(t)?'hi-IN':'en-IN';u.rate=0.95;
   if(i===els.length-1)u.onend=stop;s.speak(u);});
 });
 window.addEventListener('pagehide',stop);
}
var a=null,cur=location.pathname.replace(/\/$/,'');
[].slice.call(document.querySelectorAll('.ukrel a')).some(function(x){var h=x.getAttribute('href');if(h&&h!==cur&&h.indexOf('#')<0){a=x;return true;}return false;});
if(!a)return;var shown=false;
window.addEventListener('scroll',function(){
 if(shown)return;var d=document.documentElement;if((window.scrollY+window.innerHeight)/d.scrollHeight<0.7)return;
 var c=document.getElementById('shConsent');if(c&&c.style.display==='block')return;
 shown=true;var n=document.createElement('div');n.className='uknext';
 n.innerHTML='<b>Agla padhiye</b> <a></a> <button type="button" aria-label="Band karein">×</button>';
 var l=n.querySelector('a');l.href=a.getAttribute('href');l.textContent=a.textContent;
 n.querySelector('button').addEventListener('click',function(){n.remove();});document.body.appendChild(n);
},{passive:true});
})();
(function(){var mv=document.querySelector('meta[name="sh-vu"]');var VU=mv?(mv.getAttribute('content')||''):'';
var ps=[].slice.call(document.querySelectorAll('.ukpoll'));if(!ps.length||!/^https:\/\//.test(VU)||!window.fetch)return;
var K='sh_ukpoll',d;try{d=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){d={}}
function sv(){try{localStorage.setItem(K,JSON.stringify(d))}catch(e){}}
ps.forEach(function(p){p.hidden=false;var c=p.getAttribute('data-c'),r=p.querySelector('.pr');
 function done(o){[].slice.call(p.querySelectorAll('button')).forEach(function(x){x.disabled=true;if(+x.getAttribute('data-o')===o)x.className='on';});
  r.textContent='Dhanyavaad! 30 vote ke baad yahan sabka asli nateeja dikhega.';}
 if(d[c]!==undefined)done(d[c]);
 [].slice.call(p.querySelectorAll('button')).forEach(function(x){x.addEventListener('click',function(){if(d[c]!==undefined)return;
  var o=+x.getAttribute('data-o');d[c]=o;sv();done(o);fetch(VU+'/v?c='+c+'&o='+o,{method:'POST',mode:'cors'}).catch(function(){});});});});
fetch(VU+'/p?c='+ps.map(function(p){return p.getAttribute('data-c')}).join(',')).then(function(r){return r.json()}).then(function(m){
 ps.forEach(function(p){var a=m[p.getAttribute('data-c')];if(!a)return;var n=a.reduce(function(s,x){return s+x},0);
  var bs=[].slice.call(p.querySelectorAll('button'));p.querySelector('.pr').textContent='📊 Ab tak '+n+' logon ki raay: '+
  bs.map(function(b,i){return b.textContent+' '+Math.round(100*(a[i]||0)/n)+'%'}).join(' · ');});}).catch(function(){});
})();
</script>
"""
UK_CSS = """
.shot.tall img{width:auto;max-width:100%;max-height:460px;margin:0 auto}
.ukbtn{background:#fff;border:1px solid var(--line);border-radius:99px;padding:7px 13px;font:inherit;font-size:.85rem;cursor:pointer}
.uknext{position:fixed;left:12px;right:12px;bottom:12px;max-width:560px;margin:0 auto;z-index:9000;background:#fff;border:1px solid var(--line);border-left:4px solid var(--brand);border-radius:12px;padding:11px 40px 11px 14px;box-shadow:0 8px 28px rgba(15,23,32,.16);font-size:.9rem}
.uknext a{color:var(--brand);font-weight:700;text-decoration:none}.uknext button{position:absolute;right:8px;top:6px;border:0;background:none;font-size:1.3rem;cursor:pointer;color:var(--muted)}
.ukpoll{border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:18px 0;background:#fff}
.ukpoll p{margin:6px 0}.ukpoll button{display:inline-block;margin:4px 6px 4px 0;padding:8px 12px;border:1px solid var(--line);border-radius:99px;background:#fff;font:inherit;cursor:pointer}
.ukpoll button.on{border-color:var(--brand);background:var(--brand);color:#fff}.ukpoll button:disabled{cursor:default}
@media print{.uknext,.ukbtn,.ukpoll{display:none!important}}
"""
