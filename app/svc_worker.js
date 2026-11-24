// sabhisaab-leads v3.8.7 - website form -> KV (JSON) + Telegram + customer ka gupt status page (CRM).
// VM band ho to bhi lead surakshit. Customer ko Telegram/WhatsApp ki zaroorat nahi.
// Rasta: sabhisaab.com/api/* (Pages Function, same-origin) -> yahan. Purana seedha workers.dev bhi chalta hai.
const ORIG = ['https://sabhisaab.com', 'https://www.sabhisaab.com'];
const STAGES = ['new', 'talk', 'rate', 'accepted', 'paid', 'working', 'delivered', 'feedback', 'closed', 'lost'];
function cors(req) {
  const o = req.headers.get('origin') || '';
  return {'access-control-allow-origin': ORIG.includes(o) ? o : ORIG[0], 'access-control-allow-methods': 'GET, POST, OPTIONS',
    'access-control-allow-headers': 'content-type', 'content-type': 'application/json', 'cache-control': 'no-store'};
}
const clean = (v, n) => String(v == null ? '' : v).replace(/[<>]/g, '').trim().slice(0, n);
function j(o, s, h) { return new Response(JSON.stringify(o), {status: s || 200, headers: h || {'content-type': 'application/json'}}); }
function day() { return new Date(Date.now() + 19800000).toISOString().slice(0, 10); }
function rnd(n) { const a = new Uint8Array(n); crypto.getRandomValues(a); return Array.from(a, b => 'abcdefghjkmnpqrstuvwxyz23456789'[b % 31]).join(''); }
function ipOf(req, env) {
  // Pages Function asli IP 'x-sh-ip' mein bhejta hai - sirf tab maano jab gupt proxy key mile
  if (env.PK && req.headers.get('x-sh-pk') === env.PK && req.headers.get('x-sh-ip')) return req.headers.get('x-sh-ip');
  return req.headers.get('cf-connecting-ip') || 'x';
}
async function tg(env, text) {
  try {
    await fetch('https://api.telegram.org/bot' + env.TG_TOKEN + '/sendMessage', {method: 'POST',
      headers: {'content-type': 'application/json'}, body: JSON.stringify({chat_id: env.TG_CHAT, text: text.slice(0, 3900)})});
  } catch (e) {}
}
async function getSt(env, id) { try { return JSON.parse(await env.KV.get('st:' + id) || 'null'); } catch (e) { return null; } }
// v3.8.5: Cloudflare free KV = roz 1000 likhai. Ginti/rate-limit wali likhai fail ho to bhi LEAD kabhi na ruke.
// v3.8.7: mobile - +91/0/space/dash hatao, 10 ank, 6-9 se shuru; nakli (0000000000/1234567890) nahi. Bahar ka number: + se 11-15 ank
function phoneNorm(v) {
  const raw = String(v || '').trim(); let x = raw.replace(/\D/g, '');
  if (raw.startsWith('+') && !x.startsWith('91') && x.length >= 11 && x.length <= 15) return {ok: true, num: x};
  if (x.length === 12 && x.startsWith('91')) x = x.slice(2); else if (x.length === 11 && x.startsWith('0')) x = x.slice(1);
  if (x.length !== 10) return {ok: false, num: '', msg: x.length < 10 ? 'Mobile number adhura hai - 10 ank likhiye' : 'Mobile number 10 ank ka likhiye'};
  if (!/^[6-9]/.test(x) || /^(\d)\1{9}$/.test(x) || x === '1234567890') return {ok: false, num: '', msg: 'Sahi mobile number likhiye (6/7/8/9 se shuru, 10 ank)'};
  return {ok: true, num: '91' + x};
}
function junk(t, min) {
  t = String(t || '').trim(); const L = t.match(/[A-Za-z\u0900-\u097F]/g) || [];
  if (L.length < (min || 3) || new Set(L.map(c => c.toLowerCase())).size < (min === 2 ? 2 : 3)) return true;
  return /^(.)\1+$/.test(t.replace(/\s/g, ''));
}
async function sput(env, k, v, o) { try { await env.KV.put(k, v, o); return true; } catch (e) { return false; } }
async function putSt(env, st) { await env.KV.put('st:' + st.id, JSON.stringify(st), {expirationTtl: 90 * 86400}); }
function pub(st) {
  // customer ko sirf apni cheez - phone/ip/owner note kabhi nahi
  const q = st.quote || null;
  const showPay = q && ['accepted', 'paid', 'working', 'delivered', 'feedback', 'closed'].includes(st.status) && st.status !== 'closed';
  return {id: st.id, ref: st.ref, name: (st.name || '').split(' ')[0], service: st.service, msg: (st.message || '').slice(0, 400),
    status: st.status, stages: STAGES, quote: q ? {name: q.name, final: q.final, advance: q.advance, days: q.days, base: q.base,
      off: q.off, valid: q.valid, note: q.note || ''} : null,
    pay: showPay && st.upi ? {upi: st.upi, pn: 'Sab Hisaab', am: st.pay_amt || q.advance || q.final, tn: st.id} : null,
    paid: st.paid || 0, due: st.due || '', hist: (st.hist || []).slice(-20).map(h => ({t: h.t, s: h.s})),
    rated: !!st.stars, deliver: st.deliver_note || '', files: (st.files || []).map(f => ({name: f.name, size: f.size})),
    details: Object.keys(st.fields || {}).length, item: st.item || ''};
}
function cleanFields(f) {
  const o = {}; if (!f || typeof f !== 'object') return o;
  for (const k of Object.keys(f).slice(0, 20)) { const v = clean(f[k], 1500); if (v) o[clean(k, 20).replace(/[^a-z0-9_]/gi, '')] = v; }
  return o;
}
// v3.8.2: Aadhaar sirf asli jaisa (12 ank, 2-9 se shuru, Verhoeff checksum sahi, aur +91 mobile nahi) - pehle '919917436371'
// jaisa WhatsApp number bhi Aadhaar maan kar form rok deta tha.
const VD = [[0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],[2,3,4,0,1,7,8,9,5,6],[3,4,0,1,2,8,9,5,6,7],[4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],[6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],[8,7,6,5,9,3,2,1,0,4],[9,8,7,6,5,4,3,2,1,0]];
const VP = [[0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],[5,8,0,3,7,9,6,1,4,2],[8,9,1,6,0,4,3,5,2,7],[9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],[2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8]];
function verhoeff(n) { let c = 0; const a = n.split('').reverse().map(Number); for (let i = 0; i < a.length; i++) c = VD[c][VP[i % 8][a[i]]]; return c === 0; }
function secretIn(v) {
  v = String(v || '');
  if (/otp\s*[:=-]?\s*\d{4,8}/i.test(v) || /\b(password|passwd|pin)\s*[:=]/i.test(v) || /\b[A-Z]{5}\d{4}[A-Z]\b/.test(v)) return true;
  const m = v.match(/\d[\d\s-]{10,16}\d/g) || [];
  for (const x of m) { const d = x.replace(/\D/g, ''); if (d.length === 12 && /^[2-9]/.test(d) && !/^91[6-9]\d{9}$/.test(d) && verhoeff(d)) return true; }
  return false;
}
const SECRET = {test: secretIn};
async function lg(env, k, w) { try { await env.KV.put('lg:' + Date.now() + ':' + Math.random().toString(36).slice(2, 5), JSON.stringify({k, w: String(w || '').slice(0, 160), t: new Date().toISOString()}), {expirationTtl: 7 * 86400}); } catch (e) {} }
const FILE_OK = /^(image\/|audio\/|application\/pdf|text\/plain|application\/(msword|vnd\.openxmlformats|vnd\.ms-excel))/;
async function tgFile(env, name, type, buf, caption) {
  try {
    const fd = new FormData(); fd.append('chat_id', env.TG_CHAT); fd.append('caption', caption.slice(0, 1000));
    fd.append('document', new Blob([buf], {type: type || 'application/octet-stream'}), name);
    await fetch('https://api.telegram.org/bot' + env.TG_TOKEN + '/sendDocument', {method: 'POST', body: fd});
  } catch (e) {}
}
const FAQ = [
  [/(kitne|kitna|rate|price|charge|fees|paise|कितने|रेट)/i, 'Rate kaam ke hisaab se - resume ₹10, form madad ₹49, mobile madad ₹49 se shuru. Pehle hum kaam samajhte hain, phir aapke isi page par likhit rate aata hai. Haan dabane ke baad hi payment.'],
  [/(file|photo|document|attach|bhej|upload|pdf|फ़ाइल|फोटो|भेज)/i, 'Isi page par "Details aur files" mein photo/PDF/voice note daal dijiye (10 tak, 8 MB tak). Zyada ho to "WhatsApp par bhejein" dabaiye - number apne aap likha jayega.'],
  [/(pay|payment|upi|qr|paisa|paise de|भुगतान|पेमेंट)/i, 'Rate aane ke baad "Haan" dabaiye - wahin UPI QR aur Pay button khulega, rakam bhari hui. Screenshot zaroori nahi; hum bank mein dekh kar page par "Paisa mila" kar dete hain.'],
  [/(kab|kitne din|time|samay|jaldi|कब|समय)/i, 'Chhote kaam aksar usi din. Bade kaam ka samay rate ke saath likha aata hai. Jaldi ho to form mein "urgent" chunein.'],
  [/(otp|password|aadhaar|aadhar|pan|bank)/i, 'OTP, password, Aadhaar/PAN/bank number hum kabhi nahi maangte. Form mein zaroorat ho to aap khud daalenge, hum screen/call par saath batayenge.'],
  [/(fraud|fake|bharosa|asli|dhokha|फ्रॉड|भरोसा)/i, 'Pehle baat, phir likhit rate, chhote kaam par hi poora advance; bade kaam par demo dekh kar baaki payment. Password/OTP kabhi nahi maangte. Shaq ho to pehle WhatsApp par baat kar lijiye.'],
  [/(refund|wapas|cancel|वापस)/i, 'Kaam shuru hone se pehle cancel = poora advance wapas. Baaki niyam Terms page par saaf likhe hain.'],
  [/(english|hindi|bhasha|likhna nahi|भाषा|हिंदी)/i, 'Bilkul Hindi mein likhiye, jaise ghar mein bolte hain - English zaroori nahi. Voice note bhi bhej sakte hain.']];
async function helpAnswer(env, q) {
  for (const [re, a] of FAQ) if (re.test(q)) return a;
  if (env.AI) {
    try {
      const r = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {max_tokens: 160, messages: [
        {role: 'system', content: 'Tum Sab Hisaab services ke vinamra sahayak ho. Hinglish mein 2-3 chhoti line. Sirf ye sach: kaam - resume ₹10, online form madad ₹49, ITR-1 madad ₹299, mobile/computer madad ₹49, website/app/design; pehle baat phir likhit rate; OTP/password/Aadhaar kabhi nahi maangte. Koi naya rate, guarantee ya vaada mat do. Pata na ho to kaho: WhatsApp par poochiye.'},
        {role: 'user', content: q.slice(0, 400)}]});
      const t = String((r && r.response) || '').replace(/[<>]/g, '').trim();
      if (t && !/guarantee|गारंटी|100%|pakka/i.test(t)) return t.slice(0, 400) + ' (Pakka jawab: WhatsApp par poochiye)';
    } catch (e) {}
  }
  return 'Ye sawal hum khud dekh kar batayenge - neeche "WhatsApp par poochiye" dabaiye, ya apna number aur kaam form mein likh dijiye.';
}
function hist(st, s) { st.hist = st.hist || []; st.hist.push({t: new Date().toISOString(), s}); }

export default {
  async fetch(req, env) {
    const u = new URL(req.url); const H = cors(req);
    let path = u.pathname.replace(/^\/api/, '');
    if (req.method === 'OPTIONS') return new Response('', {headers: H});

    if (path === '/lead' && req.method === 'POST') {
      let d; try { d = await req.json(); } catch (e) { await lg(env, 'bad_json', ''); return j({error: 'data galat'}, 400, H); }
      const isTest = !!(env.KEY && d.test === env.KEY);
      const hp = d.website || d.hp_fax;                                       // honeypot (chhupa dabba)
      if (hp && !(d.consent && String(d.phone || '').replace(/\D/g, '').length >= 10 && String(d.message || '').length >= 3)) {
        await lg(env, 'honeypot', ''); return j({id: 'OK', ref: '', k: ''}, 200, H);
      }
      const ip = ipOf(req, env);
      const rk = 'rl:' + ip; const n = +(await env.KV.get(rk) || 0);
      if (n >= 6 && !isTest) { await lg(env, 'ratelimit', ''); return j({error: 'Ek ghante mein 6 baar ho gaya - thodi der baad koshish karein ya WhatsApp karein'}, 429, H); }
      // dobara bhejna (retry/offline queue): same client id = wahi lead lautao, naya mat banao
      const cid = clean(d.cid, 40).replace(/[^a-z0-9-]/gi, '');
      if (cid) { const old = await env.KV.get('cid:' + cid); if (old) return j(JSON.parse(old), 200, H); }
      await sput(env, rk, String(n + 1), {expirationTtl: 3600});
      const name = clean(d.name, 80), msg = clean(d.message, 3000), pn = isTest ? {ok: true, num: '919999999999'} : phoneNorm(d.phone), phone = pn.num;
      const em = clean(d.email, 120);
      if (!pn.ok && !String(d.phone || '').replace(/\D/g, '') && /^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(em) && name && msg.length >= 3 && d.consent && !isTest) {
        // v3.8.7: /services (purana form) par mobile zaroori nahi - sirf email wala kaam bhi Telegram par (email web3forms se bhi jaata hai)
        await lg(env, 'email_only', ''); await tg(env, '📧 /services form (sirf email, mobile nahi diya)\n' + name + ' · ' + em + '\n\n' + msg.slice(0, 1500));
        return j({id: 'EMAIL', ref: '', k: ''}, 200, H);
      }
      if (!name || !pn.ok || msg.length < 3) { await lg(env, 'missing', (!name ? 'naam ' : '') + (!pn.ok ? 'phone ' : '') + (msg.length < 3 ? 'kaam' : '')); return j({error: !pn.ok && name && msg.length >= 3 ? pn.msg : 'naam, mobile number aur kaam likhiye'}, 400, H); }
      if (junk(msg) || junk(name, 2)) { await lg(env, 'junk', ''); return j({error: 'Thoda saaf likhiye - naam aur kya kaam hai (jaise: "resume banana hai")'}, 400, H); }
      if (!d.consent) { await lg(env, 'consent', ''); return j({error: 'sahmati ka dabba chunein'}, 400, H); }
      if ([msg, ...Object.values(cleanFields(d.fields))].some(v => secretIn(v))) { await lg(env, 'secret', ''); return j({error: 'Aadhaar/PAN/OTP/password jaisa number mat likhiye - hum kabhi nahi maangte. Use hata kar bhejiye.'}, 400, H); }
      if (isTest) { await lg(env, 'selftest', d.via || ''); return j({ok: true, test: true}, 200, H); }
      const t = Date.now(); const id = 'SH' + new Date(t + 19800000).toISOString().slice(2, 10).replace(/-/g, '') +
        Math.random().toString(36).slice(2, 6).toUpperCase();
      const k = rnd(16);
      const lead = {id, k, ref: 'REF-' + id.slice(-4), t: new Date(t).toISOString(), name, phone, message: msg,
        service: clean(d.service, 160), budget: clean(d.budget, 12), code: clean(d.code, 20).toUpperCase(),
        urgent: !!d.urgent, care: !!d.care, extras: clean(d.extras, 600), src: clean(d.src, 120), page: clean(d.page, 80),
        ip: ip.slice(0, 64), via: clean(d.via, 20), fields: cleanFields(d.fields)};
      const saved = await sput(env, 'lead:' + t + ':' + id, JSON.stringify(lead), {expirationTtl: 90 * 86400});
      const st = {...lead, status: 'new', hist: []}; hist(st, 'new'); try { await putSt(env, st); } catch (e) {}
      const out = {id, ref: lead.ref, k};
      if (cid) await sput(env, 'cid:' + cid, JSON.stringify(out), {expirationTtl: 2 * 86400});
      const fl = Object.entries(lead.fields || {}).map(([a, b]) => a + ': ' + b).join('\n');
      await tg(env, '🛎 Naya kaam ' + id + (lead.urgent ? ' ⚡' : '') + '\n' + name + ' · +' + phone.replace(/\D/g, '') + '\n' +
        (lead.service || '') + '\n' + msg.slice(0, saved ? 300 : 2500) + (saved ? '' : '\n' + fl.slice(0, 800) +
        '\n⚠️ SERVER (KV) aaj bhara/fail - ye lead SIRF isi sandesh mein hai, bot card nahi banega. Seedha WhatsApp karein.') +
        (saved ? '\n(poora card + button 5 min mein bot bhejega)' : ''));
      await lg(env, hp ? 'ok_hp' : 'ok', id);
      return j(out, 200, H);
    }
    if (path === '/find' && req.method === 'POST') {                   // link kho gaya: number + mobile ke aakhri 4 ank -> apna page
      let d; try { d = await req.json(); } catch (e) { return j({error: 'data galat'}, 400, H); }
      const ip = ipOf(req, env), rk = 'rf:' + ip, n = +(await env.KV.get(rk) || 0);
      if (n >= 10) return j({error: 'bahut koshish - 1 ghante baad, ya WhatsApp par poochiye'}, 429, H);
      await sput(env, rk, String(n + 1), {expirationTtl: 3600});
      const st = await getSt(env, clean(d.id, 20).toUpperCase());
      const l4 = clean(d.last4, 4).replace(/\D/g, '');
      if (!st || l4.length !== 4 || !String(st.phone || '').replace(/\D/g, '').endsWith(l4)) { await lg(env, 'find_fail', ''); return j({error: 'Number ya mobile ke aakhri 4 ank nahi mile'}, 404, H); }
      await lg(env, 'find_ok', st.id);
      return j({id: st.id, k: st.k}, 200, H);
    }
    if (path === '/clog' && req.method === 'POST') {                   // browser mein galti (bina naam/number) - jaanch ke liye
      let d; try { d = await req.json(); } catch (e) { return j({}, 200, H); }
      const ip = ipOf(req, env), rk = 'rc:' + ip, n = +(await env.KV.get(rk) || 0);
      if (n < 10) { await sput(env, rk, String(n + 1), {expirationTtl: 3600}); await lg(env, 'client', clean(d.w, 160)); }
      return j({}, 200, H);
    }

    if (path === '/q' && req.method === 'GET') {                       // customer ka gupt page
      const st = await getSt(env, clean(u.searchParams.get('id'), 20));
      if (!st || st.k !== u.searchParams.get('k')) return j({error: 'link galat ya purana (90 din)'}, 404, H);
      return j(pub(st), 200, H);
    }
    if (path === '/q/ok' && req.method === 'POST') {                    // customer: "Haan, theek hai"
      let d; try { d = await req.json(); } catch (e) { return j({error: 'data galat'}, 400, H); }
      const st = await getSt(env, clean(d.id, 20));
      if (!st || st.k !== d.k) return j({error: 'link galat'}, 404, H);
      if (st.status !== 'rate') return j(pub(st), 200, H);
      if (st.quote && st.quote.valid && st.quote.valid < day()) return j({error: 'quote ki tarikh nikal gayi - naya quote maangein'}, 400, H);
      st.status = 'accepted'; hist(st, 'accepted'); await putSt(env, st);
      await tg(env, '✅ ' + st.id + ' customer ne rate MAAN liya (₹' + (st.quote || {}).final + '). Ab QR uske page par dikh raha hai. Paisa aaye to bank app dekh kar: paid ' + st.id + ' <rupaye>');
      return j(pub(st), 200, H);
    }
    if (path === '/q/info' && req.method === 'POST') {                  // kaam ki details (sawal-form) baad mein bhi
      let d; try { d = await req.json(); } catch (e) { return j({error: 'data galat'}, 400, H); }
      const st = await getSt(env, clean(d.id, 20));
      if (!st || st.k !== d.k) return j({error: 'link galat'}, 404, H);
      const f = cleanFields(d.fields);
      if (Object.values(f).some(v => secretIn(v))) return j({error: 'Aadhaar/PAN/OTP/password jaisa number mat likhiye - hum kabhi nahi maangte. Use hata kar bhejiye.'}, 400, H);
      st.fields = {...(st.fields || {}), ...f}; await putSt(env, st);
      await tg(env, '📝 ' + st.id + ' ne details bheji:\n' + Object.entries(f).map(([k, v]) => k + ': ' + v).join('\n').slice(0, 3000));
      return j(pub(st), 200, H);
    }
    if (path === '/q/file' && req.method === 'POST') {                  // photo/PDF/voice - seedha owner ke Telegram + 30 din KV
      let fd; try { fd = await req.formData(); } catch (e) { return j({error: 'file nahi mili'}, 400, H); }
      const st = await getSt(env, clean(fd.get('id'), 20));
      if (!st || st.k !== fd.get('k')) return j({error: 'link galat'}, 404, H);
      const file = fd.get('file');
      if (!file || typeof file === 'string') return j({error: 'file nahi mili'}, 400, H);
      st.files = st.files || [];
      if (st.files.length >= 10) return j({error: '10 file ho gayi - baaki WhatsApp par bhejiye'}, 400, H);
      if (file.size > 8 * 1024 * 1024) return j({error: 'file 8 MB se badi - WhatsApp par bhejiye'}, 400, H);
      const type = file.type || '', name = clean(file.name || 'file', 80).replace(/[^\w.\- ]/g, '_');
      if (!FILE_OK.test(type) && !/\.(pdf|docx?|xlsx?|txt|jpe?g|png|webp|heic|m4a|mp3|ogg|opus|aac|wav)$/i.test(name)) return j({error: 'ye file type nahi chalega - photo/PDF/Word/voice bhejiye'}, 400, H);
      const buf = await file.arrayBuffer(); const n = st.files.length + 1;
      await env.KV.put('f:' + st.id + ':' + n, buf, {expirationTtl: 30 * 86400, metadata: {name, type}});
      st.files.push({n, name, size: file.size, type, t: new Date().toISOString()}); await putSt(env, st);
      await tgFile(env, name, type, buf, '📎 ' + st.id + ' (' + (st.name || '') + ') file ' + n + ': ' + name);
      return j(pub(st), 200, H);
    }
    if (path === '/help' && req.method === 'POST') {                    // sahayak: pehle FAQ, phir (ho to) Workers AI
      let d; try { d = await req.json(); } catch (e) { return j({error: 'data galat'}, 400, H); }
      const ip = ipOf(req, env), rk = 'rh:' + ip, n = +(await env.KV.get(rk) || 0);
      if (n >= 20) return j({a: 'Bahut sawal ho gaye - WhatsApp par poochiye 🙏'}, 200, H);
      await sput(env, rk, String(n + 1), {expirationTtl: 3600});
      return j({a: await helpAnswer(env, clean(d.q, 400))}, 200, H);
    }
    if (path === '/q/rate' && req.method === 'POST') {                  // delivery ke baad star
      let d; try { d = await req.json(); } catch (e) { return j({error: 'data galat'}, 400, H); }
      const st = await getSt(env, clean(d.id, 20));
      if (!st || st.k !== d.k) return j({error: 'link galat'}, 404, H);
      if (!['delivered', 'feedback'].includes(st.status) || st.stars) return j(pub(st), 200, H);
      st.stars = Math.max(1, Math.min(5, +d.stars || 0)); st.review = clean(d.text, 500); st.show_ok = !!d.show; st.sample_ok = !!d.sample;
      st.status = 'feedback'; hist(st, 'feedback'); await putSt(env, st);
      await env.KV.put('rv:' + Date.now() + ':' + st.id, JSON.stringify({id: st.id, stars: st.stars, text: st.review, show: st.show_ok,
        sample: st.sample_ok, name: (st.name || '').split(' ')[0], t: day()}), {expirationTtl: 400 * 86400});
      await tg(env, '⭐ ' + st.id + ': ' + st.stars + '/5 ' + st.review.slice(0, 200) + (st.sample_ok ? '\n(namoona dikhane ki ijazat: HAAN)' : ''));
      return j(pub(st), 200, H);
    }
    if (path === '/reviews' && req.method === 'GET') {                  // website par sirf asli, ijazat wale
      const L = await env.KV.list({prefix: 'rv:', limit: 200}); const out = [];
      for (const key of L.keys.reverse()) { const r = JSON.parse(await env.KV.get(key.name) || 'null'); if (r && r.show) out.push({stars: r.stars, text: r.text, name: r.name, t: r.t}); if (out.length >= 12) break; }
      return j({reviews: out}, 200, H);
    }
    if (path === '/ev' && req.method === 'POST') {
      let d; try { d = await req.json(); } catch (e) { return j({}, 200, H); }
      const demo = clean(d.d, 40).replace(/[^a-z0-9-]/gi, ''), ty = ['v', 's', 'c'].includes(d.t) ? d.t : '';
      if (!demo || !ty) return j({}, 200, H);
      if (Math.random() >= 0.25) return j({}, 200, H);              // 4 mein 1 likho (x4) - free KV ki roz ki likhai lead ke liye bache
      const k = 'ev:' + day() + ':' + demo + ':' + ty; const n = +(await env.KV.get(k) || 0);
      await sput(env, k, String(n + 4 * (ty === 's' ? Math.min(+d.n || 0, 600) : 1)), {expirationTtl: 400 * 86400});
      return j({}, 200, H);
    }

    const p = path.split('/');
    if (!env.KEY || p[1] !== env.KEY) return new Response('not found', {status: 404});
    if (p[2] === 'pull') {
      const after = u.searchParams.get('after') || 'lead:0';
      const L = await env.KV.list({prefix: 'lead:', limit: 1000}); const out = [];
      for (const key of L.keys) if (key.name > after) out.push(JSON.parse(await env.KV.get(key.name)));
      return j({leads: out, last: L.keys.length ? L.keys[L.keys.length - 1].name : after});
    }
    if (p[2] === 'st' && req.method === 'GET') {                       // owner/bot: poora haal
      const st = await getSt(env, clean(u.searchParams.get('id'), 20));
      return st ? j(st) : j({error: 'nahi mila'}, 404);
    }
    if (p[2] === 'add' && req.method === 'POST') {                     // v3.8.7: phone/WhatsApp/dukaan wala (manual) kaam - customer ko bhi apna gupt page
      let d; try { d = await req.json(); } catch (e) { return j({error: 'data galat'}, 400); }
      const id = clean(d.id, 20), k = clean(d.k, 32);
      if (!/^SH\w{6,}$/.test(id) || k.length < 12) return j({error: 'id/k galat'}, 400);
      if (await getSt(env, id)) return j({ok: true, dup: true});
      const st = {id, k, ref: 'REF-' + id.slice(-4), t: new Date().toISOString(), name: clean(d.name, 80), phone: clean(d.phone, 16).replace(/\D/g, ''),
        message: clean(d.message, 3000), service: clean(d.service, 160), src: clean(d.src, 40), status: 'new', hist: [], fields: {}};
      hist(st, 'new'); await putSt(env, st);
      return j({ok: true});
    }
    if (p[2] === 'set' && req.method === 'POST') {                     // owner/bot: rate, stage, upi, note (override)
      let d; try { d = await req.json(); } catch (e) { return j({error: 'data galat'}, 400); }
      const st = await getSt(env, clean(d.id, 20));
      if (!st) return j({error: 'nahi mila'}, 404);
      const P = d.patch || {};
      for (const key of ['quote', 'upi', 'pay_amt', 'paid', 'due', 'deliver_note', 'note', 'item']) if (key in P) st[key] = P[key];
      if (P.status && STAGES.includes(P.status) && P.status !== st.status) { st.status = P.status; hist(st, P.status); }
      await putSt(env, st);
      return j({ok: true, status: st.status});
    }
    if (p[2] === 'tgtest') {                                           // worker -> Telegram seedha raasta theek?
      try {
        const r = await fetch('https://api.telegram.org/bot' + env.TG_TOKEN + '/sendMessage', {method: 'POST', headers: {'content-type': 'application/json'},
          body: JSON.stringify({chat_id: env.TG_CHAT, text: '🧪 Website form -> Telegram raasta theek hai (ye jaanch ka sandesh hai).'})});
        const t = await r.json(); return j({ok: !!t.ok, err: t.description || ''});
      } catch (e) { return j({ok: false, err: String(e).slice(0, 120)}); }
    }
    if (p[2] === 'log' && req.method === 'GET') {
      const L = await env.KV.list({prefix: 'lg:', limit: 1000}); const ks = L.keys.slice(-60); const out = [];
      for (const key of ks) out.push(JSON.parse(await env.KV.get(key.name) || '{}'));
      return j({log: out});
    }
    if (p[2] === 'file' && req.method === 'GET') {
      const r = await env.KV.getWithMetadata('f:' + clean(u.searchParams.get('id'), 20) + ':' + (+u.searchParams.get('n') || 0), {type: 'arrayBuffer'});
      if (!r || !r.value) return new Response('nahi', {status: 404});
      return new Response(r.value, {headers: {'content-type': (r.metadata || {}).type || 'application/octet-stream', 'x-name': encodeURIComponent((r.metadata || {}).name || 'file')}});
    }
    if (p[2] === 'fdel' && req.method === 'POST') {                    // kaam ke baad documents mitao (privacy)
      let d; try { d = await req.json(); } catch (e) { return j({error: 'data galat'}, 400); }
      const id = clean(d.id, 20); const L = await env.KV.list({prefix: 'f:' + id + ':'});
      for (const key of L.keys) await env.KV.delete(key.name);
      const st = await getSt(env, id); if (st) { st.files_deleted = (st.files || []).length; st.files = []; await putSt(env, st); }
      return j({ok: true, n: L.keys.length});
    }
    if (p[2] === 'stats') {
      const L = await env.KV.list({prefix: 'ev:' + (u.searchParams.get('day') || day()), limit: 1000}); const o = {};
      for (const key of L.keys) o[key.name] = +(await env.KV.get(key.name) || 0);
      return j(o);
    }
    if (p[2] === 'ping') return new Response('ok');
    return new Response('not found', {status: 404});
  }
};
