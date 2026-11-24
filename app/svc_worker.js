// sabhisaab-leads v3.8.0 - website form -> KV (JSON) + Telegram + customer ka gupt status page (CRM).
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
    rated: !!st.stars, deliver: st.deliver_note || ''};
}
function hist(st, s) { st.hist = st.hist || []; st.hist.push({t: new Date().toISOString(), s}); }

export default {
  async fetch(req, env) {
    const u = new URL(req.url); const H = cors(req);
    let path = u.pathname.replace(/^\/api/, '');
    if (req.method === 'OPTIONS') return new Response('', {headers: H});

    if (path === '/lead' && req.method === 'POST') {
      let d; try { d = await req.json(); } catch (e) { return j({error: 'data galat'}, 400, H); }
      if (d.website) return j({id: 'OK', ref: '', k: ''}, 200, H);            // honeypot
      const ip = ipOf(req, env);
      const rk = 'rl:' + ip; const n = +(await env.KV.get(rk) || 0);
      if (n >= 6) return j({error: 'thodi der baad koshish karein'}, 429, H);
      // dobara bhejna (retry/offline queue): same client id = wahi lead lautao, naya mat banao
      const cid = clean(d.cid, 40).replace(/[^a-z0-9-]/gi, '');
      if (cid) { const old = await env.KV.get('cid:' + cid); if (old) return j(JSON.parse(old), 200, H); }
      await env.KV.put(rk, String(n + 1), {expirationTtl: 3600});
      const name = clean(d.name, 80), phone = clean(d.phone, 16).replace(/[^0-9+]/g, ''), msg = clean(d.message, 3000);
      if (!name || phone.replace(/\D/g, '').length < 10 || msg.length < 3) return j({error: 'naam, mobile number aur kaam likhiye'}, 400, H);
      if (!d.consent) return j({error: 'sahmati ka dabba chunein'}, 400, H);
      const t = Date.now(); const id = 'SH' + new Date(t + 19800000).toISOString().slice(2, 10).replace(/-/g, '') +
        Math.random().toString(36).slice(2, 6).toUpperCase();
      const k = rnd(16);
      const lead = {id, k, ref: 'REF-' + id.slice(-4), t: new Date(t).toISOString(), name, phone, message: msg,
        service: clean(d.service, 160), budget: clean(d.budget, 12), code: clean(d.code, 20).toUpperCase(),
        urgent: !!d.urgent, care: !!d.care, extras: clean(d.extras, 600), src: clean(d.src, 120), page: clean(d.page, 80),
        ip: ip.slice(0, 64), via: clean(d.via, 20)};
      await env.KV.put('lead:' + t + ':' + id, JSON.stringify(lead), {expirationTtl: 90 * 86400});
      const st = {...lead, status: 'new', hist: []}; hist(st, 'new'); await putSt(env, st);
      const out = {id, ref: lead.ref, k};
      if (cid) await env.KV.put('cid:' + cid, JSON.stringify(out), {expirationTtl: 2 * 86400});
      await tg(env, '🛎 Naya kaam ' + id + (lead.urgent ? ' ⚡' : '') + '\n' + name + ' · +' + phone.replace(/\D/g, '') + '\n' +
        (lead.service || '') + '\n' + msg.slice(0, 300) + '\n(poora card + button 5 min mein bot bhejega)');
      return j(out, 200, H);
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
      const k = 'ev:' + day() + ':' + demo + ':' + ty; const n = +(await env.KV.get(k) || 0);
      await env.KV.put(k, String(n + (ty === 's' ? Math.min(+d.n || 0, 600) : 1)), {expirationTtl: 400 * 86400});
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
    if (p[2] === 'set' && req.method === 'POST') {                     // owner/bot: rate, stage, upi, note (override)
      let d; try { d = await req.json(); } catch (e) { return j({error: 'data galat'}, 400); }
      const st = await getSt(env, clean(d.id, 20));
      if (!st) return j({error: 'nahi mila'}, 404);
      const P = d.patch || {};
      for (const key of ['quote', 'upi', 'pay_amt', 'paid', 'due', 'deliver_note', 'note']) if (key in P) st[key] = P[key];
      if (P.status && STAGES.includes(P.status) && P.status !== st.status) { st.status = P.status; hist(st, P.status); }
      await putSt(env, st);
      return j({ok: true, status: st.status});
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
