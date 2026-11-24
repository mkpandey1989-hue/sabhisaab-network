import {onRequest} from './fn.mjs';
let seen; globalThis.fetch=async(u,o)=>{seen=[u,o];return new Response('{"id":"A"}',{status:200})};
const r=await onRequest({request:new Request('https://sabhisaab.com/api/lead?x=1',{method:'POST',body:'{"a":1}',headers:{'content-type':'application/json','cf-connecting-ip':'5.5.5.5'}})});
const ok=seen[0]==='https://w.example/api/lead?x=1'&&seen[1].headers.get('x-sh-pk')==='pk1'&&seen[1].headers.get('x-sh-ip')==='5.5.5.5'&&seen[1].body==='{"a":1}'&&r.status===200;
globalThis.fetch=async()=>{throw new Error('x')}; const r2=await onRequest({request:new Request('https://sabhisaab.com/api/q?id=1')});
console.log(ok&&r2.status===502?'PROXY TEST PASS':'PROXY FAIL '+JSON.stringify(seen[0]));
