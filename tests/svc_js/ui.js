const { JSDOM, VirtualConsole } = require("jsdom");
const fs = require("fs");
let fails = 0; const ok = (c, m) => { if (!c) { fails++; console.log("FAIL", m); } else console.log("ok  ", m); };
const strip = h => h.replace(/<script[^>]*src="(?!\/svc-cfg)[^"]*"[^>]*><\/script>/g, "");
function page(file, url, fetchImpl, pre) {
  const vc = new VirtualConsole(); const errs = [];
  vc.on("jsdomError", e => errs.push(String(e.message || e)));
  const src = file === "q.html" ? fs.readFileSync("/tmp/qpage.html", "utf8") : fs.readFileSync("/tmp/w/site/" + file, "utf8");
  let html = strip(src.replace('<script src="/svc-intake.js"></script>', "<script>" + fs.readFileSync("/tmp/w/site/svc-intake.js", "utf8") + "</script>")
    .replace('<script src="/svc-kit.js"></script>', "<script>" + fs.readFileSync("/tmp/w/site/svc-kit.js", "utf8") + "</script>")).replace('<script src="/svc-cfg.js"></script>', "<script>" + (pre || "") + "</script>");
  const dom = new JSDOM(html, { url, runScripts: "dangerously", virtualConsole: vc, beforeParse(w) {
    w.fetch = fetchImpl; w.alert = m => { w.__alerts = (w.__alerts || []).concat(m); }; w.QRCode = function (el, o) { el.innerHTML = "<canvas data-t='" + o.text + "'></canvas>"; };
    w.navigator.sendBeacon = () => true; w.matchMedia = () => ({ matches: false, addListener() {} });
  } });
  return { dom, errs };
}
const res = (st, body) => Promise.resolve({ ok: st < 400, status: st, json: () => Promise.resolve(body) });
const wait = ms => new Promise(r => setTimeout(r, ms));
function fill(w) {
  const f = w.document.getElementById("fm");
  f.querySelector("[name=name]").value = "Ramesh"; f.querySelector("[name=phone]").value = "9876543210";
  f.querySelector("[name=message]").value = "resume banana hai"; f.querySelector("[name=consent]").checked = true;
  return f;
}
(async () => {
  // 1) same-origin /api chalta hai
  let calls = [];
  let { dom, errs } = page("services-list.html", "https://sabhisaab.com/services-list?code=ref-ab12", (u, o) => { calls.push(u); return res(200, { id: "SH261124ABCD", ref: "REF-ABCD", k: "kkk" }); },
    "window.SVC_API='/api';window.SVC_API2='https://w.example';");
  await wait(50); let w = dom.window; let f = fill(w);
  f.dispatchEvent(new w.Event("submit", { cancelable: true })); await wait(50);
  ok(calls[calls.length - 1] === "/api/lead", "form pehle same-origin /api/lead par");
  ok(w.document.getElementById("ok").innerHTML.includes("/q?id=SH261124ABCD&amp;k=kkk") || w.document.getElementById("ok").innerHTML.includes("/q?id=SH261124ABCD&k=kkk"), "safal: gupt page ka link dikha");
  ok(w.document.getElementById("code").value === "REF-AB12", "reel/dost code URL se bhara");
  ok(errs.length === 0, "list page JS error nahi: " + errs.join("|"));
  // 2) /api atka (network) -> workers.dev se
  calls = [];
  ({ dom, errs } = page("services-list.html", "https://sabhisaab.com/services-list", (u) => { calls.push(u); return u.startsWith("/api") ? Promise.reject(new Error("net")) : res(200, { id: "SH1", ref: "REF-1", k: "k1" }); },
    "window.SVC_API='/api';window.SVC_API2='https://w.example';"));
  await wait(50); w = dom.window; f = fill(w); f.dispatchEvent(new w.Event("submit", { cancelable: true })); await wait(80);
  ok(calls.join(",") === "/api/lead,https://w.example/lead", "/api fail -> doosra raasta");
  ok(w.document.getElementById("ok").innerHTML.includes("SH1"), "doosre raaste se bhi safal");
  // 3) dono fail -> phone mein save, WhatsApp vikalp, baad mein khud bhejna
  let online = false; calls = [];
  ({ dom, errs } = page("services-list.html", "https://sabhisaab.com/services-list", (u, o) => { calls.push([u, JSON.parse(o.body).cid]); return online ? res(200, { id: "SH2", ref: "REF-2", k: "k2" }) : Promise.reject(new Error("net")); },
    "window.SVC_API='/api';window.SVC_API2='https://w.example';"));
  await wait(50); w = dom.window; f = fill(w); f.dispatchEvent(new w.Event("submit", { cancelable: true })); await wait(80);
  ok(JSON.parse(w.localStorage.getItem("svcq")).length === 1, "network nahi: sandesh phone mein surakshit");
  ok(w.document.getElementById("ok").innerHTML.includes("wa.me"), "WhatsApp vikalp dikha");
  const cid = calls[0][1]; online = true; w.dispatchEvent(new w.Event("online")); await wait(80);
  ok(calls[calls.length - 1][1] === cid, "net aate hi wahi sandesh (same cid) dobara gaya - dohra lead nahi");
  ok(JSON.parse(w.localStorage.getItem("svcq")).length === 0, "queue khaali");
  // 4) galat data (400) -> alert, queue mein nahi
  ({ dom, errs } = page("services-list.html", "https://sabhisaab.com/services-list", () => res(400, { error: "naam, mobile number aur kaam likhiye" }), "window.SVC_API='/api';"));
  await wait(50); w = dom.window; f = fill(w); f.dispatchEvent(new w.Event("submit", { cancelable: true })); await wait(50);
  ok(w.document.getElementById("ok").textContent.includes("naam, mobile number aur kaam likhiye"), "400 par saaf galti page par dikhi (alert nahi)");
  ok(!w.localStorage.getItem("svcq") || JSON.parse(w.localStorage.getItem("svcq")).length === 0, "400 wala queue mein nahi");
  // 4b) hafte ki sale banner (asli date + asli rakam)
  { const d = new Date(Date.now() + 19800000).toISOString().slice(0, 10);
    const r = page("services-list.html", "https://sabhisaab.com/services-list", () => res(200, {}), "window.SVC_OFFER={sale:{item:'s-bill',name:'GST billing',pct:15,price:3999,now:3399,start:'" + d + "',end:'" + d + "'},fest:{name:'Diwali',name_hi:'दीपावली',pct:5,start:'" + d + "',end:'" + d + "'}};");
    await wait(50); const h = r.dom.window.document.getElementById("offer").innerHTML;
    ok(h.includes("3,399") && h.includes("3,999") && h.includes("दीपावली"), "sale/tyohar banner asli rakam ke saath");
    r.dom.window.document.querySelector("#offer button").click(); ok(r.dom.window.document.getElementById("svc").value.includes("GST"), "sale button se kaam chuna");
    ok(r.errs.length === 0, "offer JS error nahi " + r.errs.join("|"));
    const r2 = page("services-list.html", "https://sabhisaab.com/services-list", () => res(200, {}), "window.SVC_OFFER={sale:{item:'s-bill',name:'x',pct:15,price:1,now:1,start:'2000-01-01',end:'2000-01-07'}};");
    await wait(50); ok(r2.dom.window.document.getElementById("offer").innerHTML === "", "purani sale (date nikal gayi) nahi dikhti"); }
  // 4c) v3.8.1: kaam ke sawal + file + sahayak
  { let posts = [];
    const r = page("services-list.html", "https://sabhisaab.com/services-list", (u, o) => { posts.push([u, o]); if (u.endsWith("/help")) return res(200, { a: "Rate kaam ke hisaab se" });
      return u.endsWith("/q/file") ? res(200, { files: [1] }) : res(200, { id: "SH5", ref: "REF-5", k: "k5" }); }, "window.SVC_API='/api';");
    await wait(60); const w = r.dom.window, d = w.document;
    ok(d.querySelector("#help .kit-h"), "sahayak dikha");
    w.pick("m-resume"); await wait(10);
    ok(d.querySelector('#intake [data-k="padhai"]') && d.querySelector("#fwrap input[type=file]"), "resume chuna -> resume ke sawal + file button");
    ok(d.querySelector("#intake").textContent.includes("Aadhaar"), "Aadhaar/OTP mat likhiye chetavni");
    w.pick("m-itr1"); await wait(10); ok(d.querySelector('#intake [data-k="aay"]'), "ITR chuna -> ITR ke sawal");
    w.pick("m-resume"); d.querySelector('#intake [data-k="padhai"]').value = "12th 2022";
    const f = fill(w); const fi = d.querySelector("#fwrap input[type=file]");
    Object.defineProperty(fi, "files", { value: [new w.File(["abc"], "old.pdf", { type: "application/pdf" })] });
    f.dispatchEvent(new w.Event("submit", { cancelable: true })); await wait(120);
    const lead = posts.find(p => p[0] === "/api/lead"); ok(lead && JSON.parse(lead[1].body).fields.padhai === "12th 2022", "sawal ke jawab lead ke saath gaye");
    ok(posts.some(p => p[0] === "/api/q/file"), "file lead ke baad upload hui");
    ok(d.getElementById("ok").textContent.includes("1 file pahunch"), "file pahunchne ka sandesh");
    d.querySelector(".kit-chips button").click(); await wait(40);
    ok(d.querySelector(".kit-hl").textContent.includes("Rate kaam"), "sahayak ne jawab diya");
    ok(r.errs.length === 0, "list page JS error nahi " + r.errs.join("|")); }
  { let posts = []; const st0 = { id: "SH9", ref: "REF-9", name: "Ramesh", service: "Resume", msg: "", stages: ["new","talk","rate","accepted","paid","working","delivered","feedback","closed","lost"], status: "talk", item: "m-resume", files: [], hist: [] };
    const r = page("q.html", "https://sabhisaab.com/q?id=SH9&k=abc", (u, o) => { posts.push([u, o]); if (u.endsWith("/q/info")) return res(200, { ...st0, details: 1 });
      if (u.endsWith("/q/file")) return res(200, { ...st0, files: [{ name: "a.jpg" }] }); if (u.endsWith("/help")) return res(200, { a: "Isi page par file" }); return res(200, st0); }, "window.SVC_API='/api';");
    await wait(80); const d = r.dom.window.document;
    ok(d.querySelector('#qi [data-k="padhai"]'), "gupt page: kaam ke hisaab se sawal (resume)");
    d.querySelector('#qi [data-k="naam"]').value = "Ramesh"; d.getElementById("qsave").click(); await wait(40);
    ok(posts.some(p => p[0] === "/api/q/info" && JSON.parse(p[1].body).fields.naam === "Ramesh"), "details gupt page se gayi");
    const fi = d.querySelector("#qf input[type=file]"); Object.defineProperty(fi, "files", { value: [new r.dom.window.File(["x"], "a.jpg", { type: "image/jpeg" })] });
    d.getElementById("qup").click(); await wait(80);
    ok(posts.some(p => p[0] === "/api/q/file"), "gupt page se file gayi");
    ok(d.querySelector("#qhelp .kit-h") && d.getElementById("app").innerHTML.includes("WhatsApp par bhejiye"), "sahayak + WhatsApp vikalp");
    ok(r.errs.length === 0, "gupt page JS error nahi " + r.errs.join("|")); }
  // 5) q page har stage
  const base = { id: "SH9", ref: "REF-9", name: "Ramesh", service: "Resume", msg: "", stages: ["new","talk","rate","accepted","paid","working","delivered","feedback","closed","lost"], paid: 0, hist: [] };
  const Q = { name: "Resume (taiyaar format)", final: 10, advance: 10, days: "Same din", base: 10, off: 0, valid: "2099-01-01" };
  const stages = {
    new: [{ ...base, status: "new" }, "Kaam mil gaya"],
    rate: [{ ...base, status: "rate", quote: Q }, "Haan, theek hai"],
    accepted: [{ ...base, status: "accepted", quote: Q, pay: { upi: "test@upi", pn: "Sab Hisaab", am: 10, tn: "SH9" } }, "upi://pay?pa=test%40upi&pn=Sab%20Hisaab&am=10&cu=INR&tn=SH9"],
    working: [{ ...base, status: "working", quote: Q, due: "2026-11-30" }, "Kaam chalu"],
    delivered: [{ ...base, status: "delivered", quote: Q }, "Star dijiye"],
    lost: [{ ...base, status: "lost" }, "band hai"] };
  for (const [k, [st, want]] of Object.entries(stages)) {
    const r = page("q.html", "https://sabhisaab.com/q?id=SH9&k=abc", () => res(200, st), "window.SVC_API='/api';");
    await wait(60); const h = r.dom.window.document.getElementById("app").innerHTML.replace(/&amp;/g, "&");
    ok(h.includes(want), "q page " + k + ": '" + want.slice(0, 30) + "'"); ok(r.errs.length === 0, "q " + k + " JS error nahi " + r.errs.join("|"));
    if (k === "accepted") ok(h.includes("<canvas"), "QR bana (rakam bhari)");
    ok(!h.includes("9876543210"), "phone page par nahi");
  }
  // 6) Haan dabana
  let st = { ...base, status: "rate", quote: Q }; let posted = null;
  let r = page("q.html", "https://sabhisaab.com/q?id=SH9&k=abc", (u, o) => { if (o && o.method === "POST") { posted = [u, JSON.parse(o.body)]; return res(200, { ...st, status: "accepted", pay: { upi: "a@b", pn: "Sab Hisaab", am: 10, tn: "SH9" } }); } return res(200, st); }, "window.SVC_API='/api';");
  await wait(60); r.dom.window.document.getElementById("yes").click(); await wait(60);
  ok(posted && posted[0] === "/api/q/ok" && posted[1].k === "abc", "Haan -> /api/q/ok (gupt key ke saath)");
  ok(r.dom.window.document.getElementById("app").innerHTML.includes("upi://pay"), "Haan ke baad turant QR/pay");
  // 7) bina key
  r = page("q.html", "https://sabhisaab.com/q", () => res(200, {}), "");
  await wait(40); ok(r.dom.window.document.getElementById("app").innerHTML.includes("adhoora"), "bina key: saaf sandesh");
  // 8) rating
  st = { ...base, status: "delivered", quote: Q }; posted = null;
  r = page("q.html", "https://sabhisaab.com/q?id=SH9&k=abc", (u, o) => { if (o && o.method === "POST") { posted = JSON.parse(o.body); return res(200, { ...st, status: "feedback", rated: true }); } return res(200, st); }, "");
  await wait(60); const d = r.dom.window.document; d.querySelector('#st button[data-n="5"]').click(); d.getElementById("smp").checked = true; d.getElementById("send").click(); await wait(60);
  ok(posted && posted.stars === 5 && posted.sample === true && posted.show === false, "rating + ijazat sahi gayi");
  console.log(fails ? "\nFAILED " + fails : "\nSAB UI TEST PASS"); process.exit(fails ? 1 : 0);
})();
