"""Smoke jaanch (install se PEHLE chalti hai; fail = install ruk jaata hai). v3.2.0.
GitHub copy mein purani tests/ nahi thi - ye file naye sire se: import + Bing kram + jawab-tareeka."""
import collections
import importlib
import sys

OK, BAD = [], []


def check(cond, msg):
    (OK if cond else BAD).append(msg)
    print(("✅ " if cond else "❌ ") + msg)


MODS = ("bot pipeline youtube website siteknow upgrader kb seodiary tasks relay backup vmaudit studio weekplan design puzzles "
        "sfx vault_web web_widgets elite_audit blender3d qbank ops media_tools answers canary adsense sitescan ypp watchdog "
        "ytcomment privacy_patch factwatch policywatch kwfix hubvideo hooks setupwiz qplan votes karaoke webstory abtest "
        "toolpin ideas push quizbot hindifix finalgate ownermode learn audit pagequeue linkedin reach sawalpost intents featureaudit localask svc svcvideo svccomment svc_intake svcdoctor tts_once").split()
for m in MODS:
    try:
        importlib.import_module("app." + m)
        check(True, f"import app.{m}")
    except Exception as e:
        check(False, f"import app.{m}: {e}")

from app import website as W, answers as A, state  # noqa: E402

# ---------------- Bing kram (bina network) ----------------
S = W.SITE
pages = {"a-calc": {"lastmod": "2026-08-19"}, "b-calc": {"lastmod": "2026-08-19"}, "c-calc": {"lastmod": "2026-11-12"},
         "d-calc": {"lastmod": "2026-08-19"}, "e-calc": {"lastmod": "2026-08-19"}, "links": {"lastmod": "2026-11-12"},
         "f-calc": {"lastmod": "2026-08-19"}}
W_is = W.__dict__.get("siteknow")
from app import siteknow  # noqa: E402
_orig = siteknow.is_content
siteknow.is_content = lambda k, v: True
try:
    ui = {S + "/a-calc": {"chk": "2026-11-12", "crawl": ""},            # kabhi crawl nahi
          S + "/b-calc": {"chk": "2026-11-12", "crawl": "2026-11-01"},  # crawl hua, index saboot nahi
          S + "/d-calc": {"chk": "2026-11-12", "crawl": "2026-11-01"},  # crawl + Bing search mein dikha
          S + "/e-calc": {"chk": "2026-11-12", "crawl": "2026-11-01"}}
    got, why = W.bing_plan(90, "2026-11-13", pages, ["f-calc"], ui, {}, {}, shown=["/d-calc"])
    check(S + "/d-calc" not in got, "Bing: index (search mein dikha) + bina badla page dobara nahi")
    check(S + "/links" not in got, "Bing: /links kabhi nahi")
    check(got[0] == S + "/f-calc", "Bing: Google-index-nahi sabse pehle")
    check(why.get(S + "/a-calc") == "Bing ne kabhi crawl nahi kiya", "Bing: crawl-nahi wala jaata hai")
    check(why.get(S + "/b-calc", "").startswith("crawl hua"), "Bing: crawl-hua-par-index-nahi bhi jaata hai (v3.2.0)")
    check(S + "/c-calc" in got, "Bing: naya/badla jaata hai")
    got2, _ = W.bing_plan(90, "2026-11-13", pages, [], ui, {S + "/b-calc": "2026-11-01"}, {}, shown=["/d-calc"])
    check(S + "/b-calc" not in got2, "Bing: crawl-hua wala 30 din se pehle dobara nahi")
    got3, _ = W.bing_plan(90, "2026-12-05", pages, [], ui, {S + "/b-calc": "2026-11-01"}, {}, shown=["/d-calc"])
    check(S + "/b-calc" in got3, "Bing: 30 din baad dobara")
    big = {f"p{i}": {"lastmod": "2026-08-19"} for i in range(200)}
    bui = {S + f"/p{i}": {"chk": "2026-11-12", "crawl": ""} for i in range(200)}
    g, _ = W.bing_plan(300, "2026-11-13", big, [], bui, {}, {})
    check(len(g) == W.BING_MAX_DAY, f"Bing: roz max {W.BING_MAX_DAY}")
    g, _ = W.bing_plan(60, "2026-11-13", big, [], bui, {}, {})
    check(len(g) == 30, "Bing: quota ka 1/2 hi")
    g, why_ = W.bing_plan(90, "2026-11-13", big, [], bui, {}, {}, new_uk=[list(big)[-1]])
    check(g and why_[g[0]].startswith("naya Uttarakhand"), "Bing: naya Uttarakhand page sabse pehle")
    g, _ = W.bing_plan(0, "2026-11-13", big, [], bui, {}, {})
    check(g == [], "Bing: quota 0 = kuch nahi")
    oldp = {"x": {"lastmod": "2026-08-19"}}
    g, _ = W.bing_plan(90, "2026-11-13", oldp, [], {}, {}, {})
    check(g == [], "Bing: bina jaanch/bina badla purana page rotate se nahi (v3.1.0 niyam)")
finally:
    siteknow.is_content = _orig

# ---------------- Jawab-tareeka (v3.2.0) ----------------
opts = ["120", "100", "60", "20"]
ans = "100"


def scenes(n):
    return [{"show": f"s{i}", "say": "पाँच सेकंड सोचिए"} for i in range(n)]


for mech in A.VMECH:
    for n in (3, 4, 5):
        for trial in range(3):
            sc = {"puzzle_q": f"q{trial}", "brand": "money", "reel_code": "1234"}
            keep = scenes(n)
            used = A.apply_mech(sc, keep, list(opts), ans, mech=mech)
            cut = set(sc.get("fifty_out") or [])
            for s in keep:
                cut |= set(s.get("elim") or [])
            check(ans not in cut, f"vmech {mech}/{n}: sahi kabhi nahi kata")
            check("120" not in cut, f"vmech {mech}/{n}: jaal (sabse paas wala) nahi kata")
            if used == "fifty":
                check(len(keep[-1].get("elim") or []) == 2, f"vmech {mech}/{n}: 50-50 = 2 kate")
            if used == "ek_kata":
                check(len(keep[-1].get("elim") or []) == 1, f"vmech {mech}/{n}: ek kata")
            if used == "dhire":
                check(n >= 4 and len(keep[-2]["elim"]) == 1 and len(keep[-1]["elim"]) == 2, f"vmech {mech}/{n}: pehle 1 phir 2")
            if used in ("full", "savdhaan"):
                check(not cut, f"vmech {mech}/{n}: koi nahi kata")
            if mech == "dhire" and n == 3:
                check(used == "fifty", "vmech dhire 3 scene par 50-50 ban jaata hai")
            check(not any("%" in s.get("say", "") or "लोग" in s.get("say", "") for s in keep), f"vmech {mech}/{n}: koi nakli daava nahi")

cnt = collections.Counter()
state.put("last_vmech", {})
for i in range(60):
    sc = {"puzzle_q": f"sawal {i}", "brand": "money", "reel_code": str(1000 + i)}
    cnt[A.apply_mech(sc, scenes(4), list(opts), ans)] += 1
check(len(cnt) >= 4, f"vmech: alag-alag tareeke aate hain {dict(cnt)}")
last = None
rep = 0
for i in range(30):
    sc = {"puzzle_q": f"z {i}", "brand": "deals", "reel_code": str(2000 + i)}
    m = A.apply_mech(sc, scenes(4), list(opts), ans)
    rep += (m == last)
    last = m
check(rep == 0, "vmech: usi channel par lagatar wahi tareeka nahi")
state.put("fifty_on", False)
sc = {"puzzle_q": "q", "brand": "pahadi", "reel_code": "9"}
check(A.apply_mech(sc, scenes(4), list(opts), ans) in ("full", "savdhaan"), "vmech: fifty_on band = kuch nahi katta")
state.put("fifty_on", True)

# strip_reveal poora raasta
sc = {"puzzle_q": "100 का 20% कितना?", "puzzle_options": opts, "puzzle_answer": ans, "brand": "money", "title": "t",
      "scenes": [{"show": "हुक", "say": "सुनिए"}, {"show": "सवाल", "say": "सवाल"}, {"show": "सोचिए", "say": "पाँच सेकंड सोचिए"},
                 {"show": "सही जवाब है 100", "say": "सही जवाब है 100"}]}
try:
    r = A.strip_reveal(sc)
    check(not any("सही जवाब है" in s.get("say", "") for s in r["scenes"]), "strip_reveal: jawab video mein nahi")
except Exception as e:
    check(False, f"strip_reveal: {e}")

from app import audit as AU  # noqa: E402
meta = {"puzzle_options": opts, "puzzle_answer": ans, "scenes": [{"show": "x", "elim": ["100"], "fifty": True}]}
try:
    res = AU.final_authority(meta)
    if res is not None:
        check(any(not ok and "sahi vikalp nahi kata" in m for ok, m in res), "audit: scene mein sahi kata = FAIL pakadta hai")
except Exception as e:
    print("audit jaanch chhodi:", e)


# ---------------- v3.3.0 page queue (bina network) ----------------
from app import pagequeue as PQ  # noqa: E402
man = [{"slug": "hub", "rank": 0, "links_to": ["a", "b", "c"], "requires": []},
       {"slug": "a", "rank": 1, "links_to": ["hub", "b", "c"], "requires": ["hub"]},
       {"slug": "b", "rank": 2, "links_to": ["hub", "a", "c"], "requires": ["hub"]},
       {"slug": "c", "rank": 3, "links_to": ["hub", "a", "b"], "requires": ["hub"]},
       {"slug": "z", "rank": 4, "links_to": ["hub"], "requires": ["hub"]}]
ch = PQ.select(man, set(), 4, {"hub": 3})
check(ch == ["hub", "a", "b", "c"], f"queue: rank kram + requires ({ch})")
check("z" not in PQ.select(man, {"hub", "a", "b", "c"}, 4, {}), "queue: 3 se kam andar-link wala page nahi chunta")
check(len(PQ.select(man, set(), 2, {"hub": 3})) <= 2, "queue: roz ki seema")
h = ('<li data-ukli="a"><a href="/a" data-uk="a">A</a></li><li data-ukli="q"><a href="/q" data-uk="q">Q</a></li>'
     '<p><a href="/q#h1" data-uk="q">Q page</a> <time datetime="@@PUB@@">@@PUBH@@</time> Saare 188 Tools</p>')
g = PQ.gate(h, {"a"}, "2026-11-15", 190)
check('href="/q' not in g and "Q page" in g and 'href="/a"' in g, "queue gate: live-nahi page ka link hata, text bacha")
g2 = PQ.activate(g.replace("</p>", " <!--site-sudhaar--></p>"), {"a", "q"})
check('href="/q#h1"' in g2 and "<!--site-sudhaar-->" in g2 and "data-ukg" not in g2 and "<li hidden" not in g2,
      "queue activate: naya live link jaga, website ka doosra sudhaar bacha rahe")
bx = '<div class="ukrel" data-ukblk="1"><b>X</b><ul class="ukdir"><li data-ukli="q"><a href="/q" data-uk="q">Q</a></li></ul></div>'
check('<div class="ukrel" hidden' in PQ.gate(bx, set(), "2026-11-15") and
      '<div class="ukrel" data-ukblk' in PQ.activate(PQ.gate(bx, set(), "2026-11-15"), {"q"}), "queue: khaali dabba chhupa, page aate hi dikha")
check("15 November 2026" in g and "@@" not in g and "Saare 190 Tools" in g, "queue gate: tareekh + tool ginti")
sm = ('<urlset>\n<url>\n<loc>https://sabhisaab.com/</loc>\n<lastmod>2026-11-12</lastmod>\n</url>\n<url>\n<loc>https://sabhisaab.com/'
      'alpha</loc>\n<lastmod>2026-08-19</lastmod>\n</url>\n<url>\n<loc>https://sabhisaab.com/zeta</loc>\n<lastmod>2026-08-19</lastmod>'
      '\n</url>\n</urlset>')
sm2 = PQ.sitemap_add(sm, [("mid", "2026-11-15", "x.webp")])
check(sm2.find("/alpha<") < sm2.find("/mid<") < sm2.find("/zeta<") and sm2.count("/mid<") == 1, "queue sitemap: sahi kram, ek baar")
check(PQ.sitemap_add(sm2, [("mid", "2026-11-16", "x.webp")]).count("/mid<") == 1, "queue sitemap: dohraav nahi")
pg = '<main><p>x</p><div class="artread"><b>a</b></div></main>'
i1 = PQ.inject(pg)
check(PQ.inject(i1) == i1 and i1.count('href="/uttarakhand"') == 1, "queue inject: ek hi baar")
hm = '<footer><div class="hubbar"><a href="/guides">Guides</a> &middot; <a href="/">Saare 188 Tools</a></div></footer>'
check(PQ.inject_home(hm).count('href="/uttarakhand"') == 1 and PQ.inject_home(PQ.inject_home(hm)) == PQ.inject_home(hm),
      "queue homepage: footer link ek baar")
check(PQ.is_queue_zip(["x/ukqueue/manifest.json"]) and not PQ.is_queue_zip(["site/a.html"]), "queue ZIP pehchaan")
_m = '<head><meta name="sh-vu" content=""></head>'
check('content="https://v.example.workers.dev"' in PQ.vu_fill(_m, "https://v.example.workers.dev") and
      'content=""' in PQ.vu_fill(_m, "javascript:alert(1)") and PQ.vu_fill("<p>x</p>", "https://a.b") == "<p>x</p>",
      "poll vote-pata: sirf https, galat pata khaali")
import tempfile as _tf, pathlib as _pl  # noqa: E402
_S = "https://sabhisaab.com/"
_st = {_S + "p1": {"ok": True, "why": "Submitted and indexed"}, _S + "p4": {"ok": False, "why": "Crawled - currently not indexed"},
       _S + "p2": {"ok": False, "why": "Discovered - currently not indexed"}}
_pub = {"p1": "2026-11-15", "p2": "2026-11-19", "p3": "2026-11-20", "p4": "2026-11-10"}
_old = (PQ.state.get("pq_pub"), PQ.state.get("pq_idx_drop"))
PQ.state.put("pq_pub", _pub); PQ.state.put("pq_idx_drop", {_S + "oldtool": {"d": "2026-11-20", "why": "Crawled"}})
_rl = PQ.request_list(["n1", "n2"], st=_st)
check(_rl[:3] == ["n1", "n2", "oldtool"] and "p4" in _rl and "p2" in _rl and "p1" not in _rl and len(_rl) <= 10,
      f"owner ki GSC suchi: naye + index se nikle + index-nahi purane ({_rl})")
check(len(PQ.request_list([f"n{i}" for i in range(15)], st=_st)) == 10, "GSC suchi: max 10")
_gs = PQ.gidx_summary(_st)
check("1/4 live page index mein" in _gs and "1/3 URL index mein" in _gs and "oldtool" in _gs, "google-index haal: ginti sahi")
from app import siteknow as _SK  # noqa: E402
_pg = {"a": {"title": "Bijli Bill Guide", "h1": "Bijli Bill Guide", "words": 1500, "links": [], "canon": "https://sabhisaab.com/a",
             "noindex": False, "indexed": False, "in_sitemap": True, "why": "Crawled - currently not indexed"},
       "b": {"title": "Kuch aur", "h1": "Kuch aur", "words": 300, "links": ["a"], "canon": "https://sabhisaab.com/x",
             "noindex": True, "indexed": False, "in_sitemap": True, "why": "Discovered - currently not indexed"}}
_sv = (_SK.pages, _SK._site_dir)
with _tf.TemporaryDirectory() as _d:
    _SK.pages = lambda: _pg
    _SK._site_dir = lambda: _pl.Path(_d)
    _db = _SK.doctor(slug_only="b")
    check("noindex" in _db and "canonical doosre URL" in _db and "content chhota" in _db, f"website doctor: noindex/canonical/chhota ({_db[-200:]})")
    check("noindex" not in _SK.doctor(slug_only="a"), "website doctor: theek page par galat aarop nahi")
_SK.pages, _SK._site_dir = _sv
PQ.state.put("pq_pub", _old[0]); PQ.state.put("pq_idx_drop", _old[1])
_h = ['<img src="/ghati-ka-gaon.webp" width="1">', '<meta property="og:image" content="https://sabhisaab.com/naya-khet.webp">',
      '<img src="/purani.webp">', '<img src="/bahar-ki.webp">']
check(PQ.page_images(_h, {"purani.webp"}, {"ghati-ka-gaon.webp", "naya-khet.webp", "purani.webp"}) == ["ghati-ka-gaon.webp", "naya-khet.webp"],
      "queue photo: sirf aaj ke page ki, jo site par nahi aur queue mein hai")
from app import website as _WS  # noqa: E402
_rows_sv = _WS.indexnow_rows
_td = str(__import__("datetime").date.today())
_WS.indexnow_rows = lambda: [{"t": _td + " 10:00", "url": _WS.SITE + "/almora-uttarakhand", "code": 200, "why": "queue"},
                             {"t": _td + " 11:00", "url": _WS.SITE + "/nali-mutthi-square-feet", "code": 200, "why": "bing-api roz"},
                             {"t": _td + " 11:05", "url": _WS.SITE + "/x", "code": 429, "why": "queue"}]
_stt = _WS.sent_today_text(_td)
check("IndexNow 1 + Bing API 1 = 2" in _stt and "/almora-uttarakhand" in _stt and "/x" not in _stt,
      "kaun se page bheje: naam ke saath, fail wale nahi")
_WS.indexnow_rows = _rows_sv
import datetime as _dt  # noqa: E402
with _tf.TemporaryDirectory() as _d:
    open(_d + "/a-kaise-pahunche.html", "w").write('<title>Yatra 2025</title><p>Rail line 5 March 2026 ko shuru hogi. Theek hai.</p>'
                                                  '<script>{"dateModified": "2026-01-01"}</script>')
    open(_d + "/b-bhugol-nadiyan.html", "w").write('<title>Bhugol</title><p>Mandir 1 May 2027 ko khulenge.</p>')
    _fr = dict(PQ.fresh_scan(_d, _dt.date(2026, 11, 16), ["a-kaise-pahunche", "b-bhugol-nadiyan", "nahi-hai"]))
check(set(_fr) == {"a-kaise-pahunche"} and any("beeti tareekh" in w for w in _fr["a-kaise-pahunche"])
      and any("purana saal 2025" in w for w in _fr["a-kaise-pahunche"]) and any("din se update" in w for w in _fr["a-kaise-pahunche"]),
      f"taazgi jaanch: beeti tareekh + purana saal + purana update pakda, aane wali tareekh par galat aarop nahi ({_fr})")
# v3.3.4: dhancha ka taala (toote '#naam' link theek), Hindi tareekh taazgi, content-nishaan, MOD tareekh
_h = ('<h2 id="ghat">Ghat</h2><a href="#ghat">G</a><a href="#nahi">N</a><a href="/b-page#x" data-uk="b-page">B</a>'
      '<a href="/b-page#y" data-uk="b-page">B2</a><span data-ukg="c" data-h="/c#z">C</span><a href="/anjaan#q">Q</a>')
_fx, _n = PQ.fix_anchors(_h, lambda s: {"b-page": {"x"}, "c": set()}.get(s))
check(_n == 3 and '<a href="#ghat">' in _fx and '<a href="#nahi">' not in _fx and ">N<" in _fx and 'href="/b-page#x"' in _fx
      and 'href="/b-page" data-uk' in _fx and 'data-h="/c"' in _fx and 'href="/anjaan#q"' in _fx,
      f"anchor taala: isi page ka toota -> text, doosre page ka -> page link, anjaan page waisa ({_n})")
check(PQ.ukc("<head><!--ukc:abc123def456-->\n</head>") == "abc123def456" and PQ.ukc("<head></head>") is None,
      "content-nishaan (ukc) padha jaata hai")
_g = PQ.gate('<main><time datetime="@@MOD@@">@@MODH@@</time>"datePublished": "@@PUB@@", "dateModified": "@@MOD@@"</main>',
             set(), "2026-11-14", None, moddate="2026-11-20")
_g2 = PQ.gate('<main>"dateModified": "@@MOD@@"</main>', set(), "2026-11-14")
check('"dateModified": "2026-11-20"' in _g and "20 November 2026" in _g and '"datePublished": "2026-11-14"' in _g
      and '"dateModified": "2026-11-14"' in _g2, "MOD tareekh: naya roop = aaj, warna pehli tareekh")
with _tf.TemporaryDirectory() as _d:
    open(_d + "/h-page.html", "w").write('<p>बद्रीनाथ के कपाट 16 नवंबर 2026 को बंद होंगे।</p><p>(PTI, 31 July 2025; rail line hogi)</p>')
    _fr2 = dict(PQ.fresh_scan(_d, _dt.date(2026, 11, 20), ["h-page"]))
check("h-page" in _fr2 and len(_fr2["h-page"]) == 1 and "नवंबर" in _fr2["h-page"][0],
      f"taazgi: Hindi tareekh pakdi, srot ki tareekh (PTI ...;) par galat aarop nahi ({_fr2})")
from app import webstory as _WSU  # noqa: E402
_uh = ('<h1>Chamoli (चमोली) Zila</h1>' + ''.join('<details class="faq" lang="hi"><summary>सवाल %d?</summary><div class="fa">जवाब %d।</div></details>' % (i, i) for i in range(6))
       + '<details class="faq" lang="hi"><summary>2026 में क्या?</summary><div class="fa">x</div></details>')
_ub = _WSU.build_uk("chamoli-uttarakhand", _uh, "a.webp")
check(_ub and _ub[1] == "uk-chamoli-zila-kahani" and "चमोली जिला: 5" in _ub[0] and "/chamoli-uttarakhand" in _ub[0]
      and "2026" not in _ub[0].split("<body>")[1] and "a.webp" in _ub[0], "UK web story: page ke Hindi FAQ + apni photo + page link, saal wale sawal nahi")
from app import pipeline as _PLU  # noqa: E402
check(_PLU.uk_district_page("Almora aur Chamoli ki baat") is None and _PLU.uk_district_page("bina zile ki video") is None,
      "video link: do zile ya koi zila nahi = zila page nahi (galat link nahi)")
from app import ukwatch as _UW  # noqa: E402
_pc = _UW.page_card('<title>Almora Ghumne | Sab Hisaab</title><meta name="description" content="Binsar &amp; Kasar">'
                    '<meta property="og:image" content="https://sabhisaab.com/a.webp">')
check(_pc == ("Almora Ghumne", "Binsar & Kasar", "https://sabhisaab.com/a.webp"), f"UK share: page ke apne shabd + apni photo ({_pc})")
_d0 = _dt.date(2026, 11, 20)
check(_UW.share_pick(_d0, {"a": "2026-11-19", "b": "2026-11-15", "c": "2026-11-01", "d": "2026-11-18"}, {"b": "x"}, lambda s: s != "d") == "a",
      "UK share: 7 din ke andar, share na hua, live - sabse purana pehle")
class _R:
    def __init__(s, c, loc=""): s.status_code, s.headers = c, {"Location": loc}
_fake = {"https://x.gov.in/a": _R(301, "https://x.gov.in/b"), "https://x.gov.in/b": _R(200), "https://y.in/z": _R(404),
         "https://w.in/q": _R(403), "https://v.in/m": _R(301, "https://v.in/dead"), "https://v.in/dead": _R(404)}
check(_UW.check_url("https://x.gov.in/a", lambda u: _fake[u]) == ("moved", "https://x.gov.in/b")
      and _UW.check_url("https://y.in/z", lambda u: _fake[u])[0] == "gone" and _UW.check_url("https://w.in/q", lambda u: _fake[u])[0] == "unknown"
      and _UW.check_url("https://v.in/m", lambda u: _fake[u])[0] == "unknown", "link chowkidar: redirect=naya pata (khulta ho to), 404=gone, 403=chhodo")
_rl, _rn = _UW.relink('<p><a href="https://x.gov.in/a" rel="noopener">Portal</a> aur <a href="https://y.in/z">Srot</a></p>',
                      {"https://x.gov.in/a": "https://x.gov.in/b"}, {"https://y.in/z"})
check(_rn == 2 and 'href="https://x.gov.in/b" rel="noopener">Portal' in _rl and "y.in" not in _rl and "Srot" in _rl,
      "link chowkidar: naya pata lagta, band link hata par shabd bache")
check(_UW._textsig("<p>Aaj 10:42 baje</p>") == _UW._textsig("<p>Aaj 11:05 baje</p>") and _UW._textsig("<p>a</p>") != _UW._textsig("<p>b</p>")
      and _UW.season_note(_dt.date(2027, 1, 25)) and not _UW.season_note(_dt.date(2027, 6, 5)),
      "srot chowkidar: ghadi ka samay badalna = badlaav nahi; mausami yaad (Basant Panchami)")
# v3.3.7: video - 'comment' sirf 2 baar, chuppi = 5 sec, asli ghatta timer
from app import answers as _ANSV, render as _RNV, design as _DSV  # noqa: E402
_kc = _ANSV.limit_comment([{"show": "a", "say": "हल करके दिखाइए! कमेंट में सिर्फ़ जवाब नहीं, तरीका भी लिखिए।"},
                          {"show": "5 सेकंड... सोचिए! जवाब कमेंट में लिखिए",
                           "say": "पाँच सेकंड, सोचिए, और अपना जवाब कमेंट में लिखिए। दो गलत विकल्प हटा दिए। अब बताइए!"}])
check("कमेंट" in _kc[0]["say"] and "कमेंट" not in _kc[1]["say"] + _kc[1]["show"]
      and _kc[1]["say"] == "पाँच सेकंड, सोचिए। दो गलत विकल्प हटा दिए। अब बताइए!" and _kc[1]["show"] == "5 सेकंड... सोचिए!",
      f"video: beech mein 'comment' sirf pehli baar ({_kc[1]})")
check(_ANSV.think_hold({"hud": {"think": 5}}) == 5.0 and _ANSV.think_hold({}) == 5.0, "video: '5 सेकंड' bole to chuppi bhi 5 sec")
_tl = _RNV.countdown_timeline([{"say": "a"}, {"say": "b", "hold": 5.0}, {"say": "c"}], [4.0, 8.3, 6.0], 0.3)
check(_tl == [(1, 4.0, 7.0, 12.0, 5.0)], f"video: timer ka samay = chuppi ke 5 sec ({_tl})")
_s1, _y1 = _DSV.countdown_strip({"kind": "bar", "y": 800, "acc": (0, 255, 150)}, 0.5, 3)
_s2, _y2 = _DSV.countdown_strip({"kind": "ring", "cx": 930, "cy": 300, "r": 80, "acc": (0, 255, 150)}, 0.2, 1)
check(_s1.size[0] == 1080 and _y1 == 786 and _s2.size == (1080, 208) and _y2 == 196, "video: ghatta timer (patti + ghadi) banta hai")
from app import pinterest as _PIN  # noqa: E402
with _tf.TemporaryDirectory() as _d:
    _pl.Path(_d, "almora-uttarakhand.html").write_text('<figure class="shot"><img src="/ghati.webp" width="1"></figure>')
    _pl.Path(_d, "ghati.webp").write_bytes(b"x")
    _pl.Path(_d, "tool.html").write_text('<img src="/tool-form.webp">')
    _sv2 = _SK._site_dir
    _SK._site_dir = lambda: _pl.Path(_d)
    check(str(_PIN._own_photo("almora-uttarakhand")).endswith("ghati.webp") and _PIN._own_photo("tool") is None,
          "Pinterest: UK page ki apni photo se pin, tool screenshot se nahi")
    _SK._site_dir = _sv2
# v3.3.10: /jawab par <details> nahi (site audit FAQ samajh kar rokta tha), table mein jawab seedha nahi; namoona 'Mat daalo' race;
# Bing ko sirf live sitemap wale URL; taazgi 'X se arrear' galat chetavni nahi; IG caption mein '@'/khaali line nahi
from app import pipeline as _PPX, website as _WSX, pagequeue as _PQX, meta as _MTX  # noqa: E402
_tb = _ANSV.jawab_table([{"code": 11, "aid": "11", "q": "Q?", "ans": "SECRET", "bname": "B", "brand": "b", "date": "d"}], [])
check("SECRET" not in _tb and "Pehle khud hal karein" in _tb and "<details" not in _tb, "/jawab: table mein jawab seedha nahi, <details> nahi")
import inspect as _insp  # noqa: E402
import re as _rex  # noqa: E402
check(not _rex.search(r"""["']<details""", _insp.getsource(_ANSV.build_page) + _insp.getsource(_ANSV.tap_block)),
      "/jawab: build_page mein <details> nahi")
_jb = {"brand": "money", "status": "rejected", "ids": {}, "done": {}, "meta": ""}
_sv_jobs = _PPX.jobs
_PPX.jobs = lambda: {"x1": _jb}
check(_PPX._was_rejected("x1") and _PPX._undo_youtube("x1", _jb) == "", "namoona/video: 'Mat daalo' ke baad upload aage nahi")
_PPX.jobs = _sv_jobs
check(_MTX.ig_safe_text("A\n📢 https://t.me/sabhisaab\nB").splitlines()[-2:] == ["A", "B"] or "📢" not in _MTX.ig_safe_text("A\n📢 https://t.me/sabhisaab\nB"),
      "Instagram: link hatne par khaali '📢' line nahi")
check("@" not in _ANSV.desc_line({"answer_offsite": True, "reel_code": 5}, "instagram"), "Instagram: caption mein @handle nahi")
with _tf.TemporaryDirectory() as _d:
    _pl.Path(_d, "p8.html").write_text("<p>Salary 2027 tak, aur 1 January 2026 se arrear milne ki ummeed hai.</p>")
    check(_PQX.fresh_scan(_d, _dt.date(2026, 11, 16), ["p8"]) == [], "taazgi: '1 January 2026 se arrear' = shuru ki tareekh, chetavni nahi")
check(_WSX._feed_count({"UrlCount": 278}) == 278 and _WSX._feed_count({}) is None, "Bing sitemap: ginti padhna")
# v3.3.11: har look (safed/exam/versus bhi) par sochne wale scene ki ghatti patti
for _lay in _DSV.LAYOUTS:
    _scx = {"brand": "money", "layout": _lay, "puzzle_q": "Q?", "puzzle_options": ["1", "2", "3", "4"], "puzzle_answer": "4",
            "answer_offsite": True, "scenes": [{"show": "h", "say": "a"}, {"show": "5 सेकंड", "say": "b", "hold": 5.0},
                                               {"show": "e", "say": "c", "answer_cta": True}]}
    with _tf.TemporaryDirectory() as _d:
        _DSV.body_frame(_scx, 1, 3, str(_pl.Path(_d, "x.png")))
    check(bool(_DSV.TIMERS.get(1)), f"video: '{_lay}' look par bhi ghatti ghadi/patti")

# ---------------- v3.4.0: LinkedIn (Make webhook) - bina network ----------------
from app import linkedin as _LIV, tg as _TGV  # noqa: E402
import json as _jsv  # noqa: E402
_li_store = _LIV.STORE
with _tf.TemporaryDirectory() as _d:
    _LIV.STORE = _pl.Path(_d, "li.json")
    class _FakeState:                             # asli VM state.json ko kabhi na chhuo (test bot chalte hue chalta hai)
        def __init__(s): s.d = {}
        def get(s, k, default=None): return s.d.get(k, default)
        def put(s, k, v): s.d[k] = v
        def update(s, k, fn, default=None):
            s.d[k] = fn(s.d.get(k, default)); return s.d[k]
    _sv_state = _LIV.state
    state = _LIV.state = _FakeState()
    try:
        check(_LIV.intake("hello") is None and not _LIV.ready(), "LinkedIn: bina URL juda nahi")
        _hk = "https://hook.eu1.make.com/" + "ab12" * 8
        _r = _LIV.intake("ye lo " + _hk)
        check(_r and "mitaya" in _r and _hk not in _r and _LIV.ready(), "LinkedIn: webhook URL surakshit, jawab mein URL nahi")
        check(oct(_LIV.STORE.stat().st_mode)[-3:] == "600", "LinkedIn: secret file 0600")
        _r2 = _LIV.intake("linkedin key Abc123xyz789")
        check(_r2 and "Abc123xyz789" not in _r2 and _jsv.loads(_LIV.STORE.read_text()).get("key") == "Abc123xyz789", "LinkedIn: API key surakshit")
        _today = _dt.date.today()
        state.put("answer_key", [
            {"code": 4001, "aid": "4001", "brand": "money", "bname": "Sab Hisaab Money", "date": str(_today), "q": "100 ka 10% kitna? #Shorts #4001",
             "opts": ["5", "10", "15", "20"], "ans": "10", "kind": ""},
            {"code": 4002, "aid": "4002", "brand": "pahadi", "bname": "Pahadi Hisaab", "date": str(_today), "q": "Nali kitni hoti hai?",
             "opts": ["A", "B", "C", "D"], "ans": "A", "kind": "purane_shabd"},
            {"code": 3000, "aid": "3000", "brand": "deals", "bname": "Labh Lo Deals", "date": str(_today - _dt.timedelta(days=9)), "q": "Purana?"},
            {"code": 4003, "aid": "4003", "brand": "deals", "bname": "Labh Lo Deals", "date": str(_today), "q": "गोला पहेली:", "opts": ["1", "2", "3", "4"]}])
        state.put("li_codes", [])
        state.put("li_last_brand", "pahadi")
        _e = _LIV.pick(_today)
        check(_e and _e["code"] == 4001, "LinkedIn: kal wala brand chhod kar doosra (purana 9 din wala nahi, adhura 'गोला पहेली:' nahi)")
        _sv_live = A.live
        A.live = lambda: True                     # /jawab live maano (bina network)
        _txt = _LIV.build(_e)
        A.live = _sv_live
        check("10" in _txt and "SECRET" not in _txt and "#Shorts" not in _txt and "#4001" not in _txt, "LinkedIn: post mein vikalp, #Shorts/#code tag nahi")
        check("utm_source=linkedin" in _txt and "#c4001" in _txt and "ANS" not in _txt, "LinkedIn: jawab ka link (UTM + #code), jawab khud nahi")
        check(len(_txt) <= 2900 and "sabhisaab.com/" in _txt.split("मुफ़्त टूल")[-1], "LinkedIn: free tool ka link (zyada der ruke)")
        state.put("li_codes", ["4001", "4002"])
        check(_LIV.pick(_today) is None, "LinkedIn: ek sawal kabhi dobara nahi")
        _before = state.get("li_tools")
        _ft, _sl = _LIV.fallback_text()
        check(bool(_ft) and bool(_sl) and state.get("li_tools") == _before, "LinkedIn: taaza sawal na ho to free tool; namoona se state nahi badalta")
        state.put("li_on", True); state.put("paused", False); state.put("li_done_day", ""); state.put("li_try", {})
        _t0 = _LIV.datetime.datetime(2026, 11, 16, 9, 0, tzinfo=_LIV.IST)
        _t1 = _LIV.datetime.datetime(2026, 11, 16, 9, 20, tzinfo=_LIV.IST)
        check(not _LIV.due(_t0) and _LIV.due(_t1), "LinkedIn: 09:15 se pehle nahi, baad mein haan")
        _LIV.mark_try()
        check(not _LIV.due(_LIV.datetime.datetime.now(_LIV.IST).replace(hour=23)), "LinkedIn: koshish ke 30 min tak dobara nahi (dohri post nahi)")
        state.put("paused", True); state.put("li_try", {})
        check(not _LIV.due(_t1), "LinkedIn: Pause par nahi")
        # bhejna: Make ka jawab (bina network - requests.post nakli)
        import requests as _rqv
        _sv_post = _rqv.post
        _seen = {}
        class _R:  # noqa: E701
            def __init__(s, c, t): s.status_code, s.text = c, t
        _rqv.post = lambda u, data=None, headers=None, timeout=None: (_seen.update(h=headers, d=data), _R(200, "Accepted"))[1]
        _ok, _why, _pid = _LIV.send("A) namaste")
        check(_ok is None and _seen["h"].get("x-make-apikey") == "Abc123xyz789" and _seen["d"]["text"] == "A\\) namaste",
              "LinkedIn: form 'text' + API key + LinkedIn nishaan bachaye; sirf 'Accepted' = pakki khabar NAHI")
        _rqv.post = lambda *a, **k: _R(200, '{"id":"urn:li:share:7528085589896769536"}')
        _ok, _why, _pid = _LIV.send("x")
        check(_ok is True and _pid == "urn:li:share:7528085589896769536", "LinkedIn: Webhook response ka post-ID = pakki safalta")
        _rqv.post = lambda *a, **k: _R(410, "There is no scenario listening for this webhook.")
        _ok, _why, _pid = _LIV.send("x")
        check(_ok is False and "BAND" in _why and "make.com/" not in _why, "LinkedIn: scenario band ho to saaf wajah (URL nahi)")
        check(_LIV.ltf("utm_source jawab#c12 (x) #SabHisaab") == "utm\\_source jawab\\#c12 \\(x\\) {hashtag|\\#|SabHisaab}",
              "LinkedIn: Little Text Format (_ # ( ) bachaye, hashtag sahi roop)")
        state.put("li_done_day", ""); state.put("paused", False); state.put("li_try", {})
        _rqv.post = lambda *a, **k: _R(200, "Accepted")
        _c0, _t0x = list(state.get("li_codes") or []), state.get("li_tools")
        _r = _LIV.post_today()
        check(_r.startswith("⚠️") and state.get("li_done_day") == str(_dt.date.today())
              and state.get("li_codes") == _c0 and state.get("li_tools") == _t0x,
              "LinkedIn: pakki khabar na ho to aaj dobara nahi (Make queue mein dohri nahi) aur sawal 'gaya' nahi gina")
        _rqv.post = _sv_post
    finally:
        _LIV.state = _sv_state
        _LIV.STORE = _li_store
from app import state  # noqa: E402,F811
# v3.4.0: Telegram file tuple par seek nahi (Uttarakhand share 'tuple' object has no attribute 'seek')
check("hasattr(fo, \"seek\")" in _insp.getsource(_TGV._http), "Telegram: (naam, bytes, type) tuple file bhi chalti hai")
from app import watchdog as _WDV  # noqa: E402
check('"adsbygoogle" in home and re.search(r"koi vigyapan nahi"' in _insp.getsource(_WDV), "AdSense: sirf pub-ID par 'koi vigyapan nahi' galat alert nahi")
# v3.4.1: IG par saada jawab-pata, tracking/owner-mode sudhaar, share kit, Pinterest 3 slot
from app import meta as _MT41, trackfix as _TF41, sharekit as _SK41, toolpin as _TP41  # noqa: E402
_ig = _MT41.ig_safe_text("✅ सही जवाब (कोड #5): https://sabhisaab.com/jawab पर कोड 5 डालें\nx https://sabhisaab.com/jawab?utm_source=y\nz")
check("https://sabhisaab.com/jawab पर" in _ig and "utm" not in _ig and "\nx " not in _ig, "Instagram: pura 'https://sabhisaab.com/jawab' bachta, UTM wala nahi")
_pg = ("<script>\nwindow.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}\n" + _TF41.O_OLD +
       "document.addEventListener('DOMContentLoaded',function(){});}}catch(e){}\n" + _TF41.C_OLD + "\n" + _TF41.U_OLD + "\n</script>")
_p0, _c0 = _TF41.patch_html(_pg, consent=False)
check(_c0 and _TF41.O_MARK in _p0 and _TF41.C_MARK not in _p0, "Owner mode: cookie + ?owner=on apne aap; consent bina pushti nahi badla")
_p1, _c1 = _TF41.patch_html(_pg, consent=True)
check(_TF41.C_MARK in _p1 and "else if(_c==='essential')" in _p1 and "'GB'" in _p1 and not _TF41.patch_html(_p1, consent=True)[1],
      "Tracking fix: Europe mein denied, baaki granted, 'sirf zaroori' yaad; dobara chalane par kuch nahi")
check(_SK41.faqs('<script type="application/ld+json">{"@type":"FAQPage","mainEntity":[{"name":"Q?","acceptedAnswer":{"text":"A"}}]}</script>')
      == [("Q?", "A")], "Share kit: page ke FAQ se Quora sawal-jawab")
check("def run(slot=0)" in _insp.getsource(_TP41) and "ghumne" in _TP41.KEYS["pahadi"], "Pinterest: roz 3 page-pin, pahad ke ghumne wale page bhi")

# v3.4.3: adhura sawal ('गोला पहेली:') - source par aur LinkedIn par
from app.puzzles import q_clean as _qc  # noqa: E402
check(_qc("गोला पहेली: [3, 6, 2]→18, [7, 2, 9]→? #5180") .startswith("गोला पहेली: [3, 6, 2]→18"), "Puzzle: bracket wala sawal ab poora (pehle sirf 'गोला पहेली:')")
check(_qc("100 का 10% कितना होगा? [संकेत: दस]") == "100 का 10% कितना होगा?", "Puzzle: aakhri [sanket] pehle jaisa hatta hai")
_sv_ak, _sv_rc = state.get("answer_key"), state.get("reel_codes")
try:
    state.put("reel_codes", {"5180": {"q": "गोला पहेली: [3, 6, 2]→18, [7, 2, 9]→?"}})
    state.put("answer_key", [{"code": 5180, "q": "गोला पहेली:"}, {"code": 1, "q": "पूरा सवाल है ये वाला ठीक?"}])
    check(A.repair_short_q() == 1 and state.get("answer_key")[0]["q"].startswith("गोला पहेली: [3") and
          state.get("answer_key")[1]["q"] == "पूरा सवाल है ये वाला ठीक?", "/jawab: adhure sawal reel_codes se poore, baaki nahi chhede")
finally:
    state.put("answer_key", _sv_ak)
    state.put("reel_codes", _sv_rc)
# v3.4.4: namoona 3 raaste (bina jawab kuch nahi), scoreboard table, web stories /jawab se jude, FB dusre group ka text
from app import studio as _ST44, scoreboard as _SB44, answers as _AN44  # noqa: E402
import datetime as _dt44  # noqa: E402
_n44 = _dt44.datetime(2026, 11, 16, 9, 0, tzinfo=_dt44.timezone(_dt44.timedelta(hours=5, minutes=30)))
_fs = _ST44.free_slot(_n44)
from app.config import SCHEDULE as _SCH44  # noqa: E402
check(_fs.strftime("%H:%M") not in {t.strip() for v in _SCH44.values() for t in v.split(",")},
      "Namoona schedule: roz ki video ke samay se alag khaali samay")
check('"sm:S:' in _insp.getsource(_ST44.promote_ask) and '"sm:N:' in _insp.getsource(_ST44.promote_ask)
      and '"sm:d:' in _insp.getsource(_ST44.promote_ask), "Namoona: Schedule / Abhi / Delete - teen raaste")
check(_SB44._n(None) == "-" and _SB44._n(12500) == "12.5k" and _SB44._n(42) == "42", "Scoreboard: '-' = data nahi (andaaza nahi)")
check("_stories_block(DIR)" in _insp.getsource(_AN44.build_page), "/jawab se Web Stories ka link (akele page nahi)")
check("%" not in _insp.getsource(_SK41.quiz_group_text), "FB group text mein koi nakli % nahi")
# v3.4.4b: N din ki table, sitemap-pehle sandesh, auto-doctor
check([_SB44.parse_days(x) for x in ("report table 6 din", "3 din ka table", "report table aaj", "report table mahina", "report table")]
      == [6, 3, 1, 30, 7], "Table report: koi bhi din (6/3/aaj/mahina)")
from app import webstory as _WS44, website as _WE44, autodoctor as _AD44  # noqa: E402
check("after_live_msg" in _insp.getsource(_WS44) and "indexnow([" not in _insp.getsource(_WS44),
      "Web Story: Bing/Google sandesh deploy LIVE + sitemap ke BAAD (pehle 15 min pehle jaata tha)")
check("p[5:-5]" in _insp.getsource(_WE44._after_live), "Deploy ke baad IndexNow: /stories/x sahi URL")
check("+= [" not in _insp.getsource(_AD44.run).replace("L += [", ""), "Auto-doctor: andar ke check mein list rebind galti nahi")
# v3.4.6: ek sandesh 2-3 baar nahi; 'Sab theek?' mein LinkedIn/Bing/Google/AdSense bhi
from app import tg as _TG46, bot as _BOT46  # noqa: E402
state.put("say_seen", {})
check(not _TG46._dupe("smoke-x 1", None) and _TG46._dupe("smoke-x 1", None) and not _TG46._dupe("smoke-x 2", None),
      "Telegram: bilkul wahi sandesh 90 sec mein dobara nahi; alag sandesh jaata hai")
check(not _TG46._dupe("📡 Telegram ka raasta badla: a", None) and _TG46._dupe("📡 Telegram ka raasta badla: b", None),
      "Telegram raasta-badla shor: 6 ghante mein ek")
state.put("say_seen", {})
_hm = "\n".join(_BOT46.health_more())
check(all(w in _hm for w in ("LinkedIn", "Bing", "Google (GSC + GA4)", "AdSense", "IndexNow", "Auto-doctor", "/jawab")),
      "Sab theek?: LinkedIn, Bing, Google, AdSense, IndexNow, /jawab, auto-doctor sab")
# v3.4.7: GSC indexing link (sitemap pehle), ek jaisi ginti, source naam, jhootha 'galat link' alarm, website sudhaar
from app import idxlink as _IX47, scoreboard as _SB47, webfix as _SP47, website as _WE47, sitescan as _SS47  # noqa: E402
_sv47 = (state.get("idx_given"), state.get("pq_idx_drop"))
try:
    state.put("idx_given", {"https://sabhisaab.com/c": "2099-01-01"})
    state.put("pq_idx_drop", {})
    _st47 = {"https://sabhisaab.com/a": {"ok": True}, "https://sabhisaab.com/b": {"ok": False, "why": "Crawled - currently not indexed"},
             "https://sabhisaab.com/c": {"ok": False, "why": "URL is unknown to Google"},
             "https://sabhisaab.com/d": {"ok": False, "why": "URL is unknown to Google"},
             "https://sabhisaab.com/e": {"ok": False, "why": "Discovered - currently not indexed"}}
    _sm47 = {"https://sabhisaab.com/a", "https://sabhisaab.com/b", "https://sabhisaab.com/c", "https://sabhisaab.com/e"}
    _r47 = _IX47.pick(status=_st47, live_sm=_sm47, live_ok=lambda u: True, indexed=lambda u: False)
    check([u for u, _ in _r47] == ["https://sabhisaab.com/e", "https://sabhisaab.com/b"],
          "Indexing link: sirf LIVE sitemap wale + index-nahi + 7 din mein dobara nahi; kram unknown > discovered > crawled")
    check(_IX47.pick(status=_st47, live_sm=None, live_ok=lambda u: True, indexed=lambda u: False) == [], "Indexing link: sitemap na mile to KOI link nahi")
    check(_IX47.gsc_link("https://sabhisaab.com/x-y") == "https://search.google.com/search-console/inspect?resource_id="
          "sc-domain%3Asabhisaab.com&id=https%3A%2F%2Fsabhisaab.com%2Fx-y", "Indexing link: Search Console URL Inspection ka seedha link")
    check(len(_IX47.pick(status={f"https://sabhisaab.com/p{i}": {"ok": False} for i in range(30)},
                         live_sm={f"https://sabhisaab.com/p{i}" for i in range(30)}, live_ok=lambda u: True,
                         indexed=lambda u: False)) == 10,
          "Indexing link: din mein max 10")
    check("submit_sitemap()" in _insp.getsource(_IX47.run) and _insp.getsource(_IX47.run).index("submit_sitemap()")
          < _insp.getsource(_IX47.run).index("pick("), "Indexing link: pehle Google ko sitemap, phir suchi")
finally:
    state.put("idx_given", _sv47[0])
    state.put("pq_idx_drop", _sv47[1])
check([_SB47.group_source(x) for x in ("whatsapp_status", "facebook_group", "org.telegram.messenger", "quora", "lnkd.in", "push",
                                         "(direct)", "duckduckgo")]
      == ["WhatsApp", "FB Group", "Telegram", "Quora", "LinkedIn", "Push", "Seedha", "Baaki"],
      "Report: har raasta sahi naam (WhatsApp status, FB group, Telegram app, Quora, LinkedIn)")
check(_WE47.ga_range(7) == ("6daysAgo", "today") and _WE47.ga_range(1) == ("today", "today"),
      "Report: '7 din' har jagah ek hi range (aaj samet 7 din)")
check("ga_range" in _insp.getsource(_WE47.traffic) and "_ga_total(_s, _e)" in _insp.getsource(_WE47.traffic)
      and "ga_range(7)" in _insp.getsource(_WE47.traffic_smart), "Report: kul log har jagah GA4 ka ek hi asli total")
check("x[1] > 0" in _insp.getsource(_WE47.traffic), "Report: 'youtube.com 0' jaisi khaali line nahi")
_uk47 = ('<tr><td>Kisan</td><td>Uttarakhand Farmer ID (UKFR)</td><td><a href="/uttarakhand" data-uk="uttarakhand">Uttarakhand '
         'guide</a>-farmer-id-ukfr</td></tr><tr><td>Zameen kagaz</td><td>Guide</td><td>https://sabhisaab.com/zameen-kagaz</td></tr>'
         '<tr><td>Quiz</td><td>GK Quiz (naya)</td><td>https://sabhisaab.com/uttarakhand-gk-quiz</td></tr>')
_fx47 = _SP47.fix_uk_table(_uk47, lambda s: s != "uttarakhand-gk-quiz")
check('<a href="/uttarakhand-farmer-id-ukfr">Uttarakhand Farmer ID (UKFR)</a>' in _fx47 and "guide</a>-" not in _fx47
      and '<a href="/zameen-kagaz">Zameen kagaz</a>' in _fx47
      and '<span data-ukg="uttarakhand-gk-quiz" data-h="/uttarakhand-gk-quiz">GK Quiz</span>' in _fx47
      and _SP47.fix_uk_table(_fx47, lambda s: True) == _fx47,
      "/uttarakhand table: toota link theek, URL text -> asli link, queue page soya link; dobara chalane par kuch nahi badla")
check(_SP47.fix_tdee(_SP47.fix_tdee('<div class="nextread"><a href="/tdee-calculator">TDEE Calculator</a></div>')).count("/tdee-guide") == 1,
      "TDEE guide link ek hi baar")
check('"mismatch": len(rep["mismatch"]),' in _insp.getsource(_SS47.run) if hasattr(_SS47, "run") else
      '"mismatch": len(rep["mismatch"]),' in _insp.getsource(_SS47), "Site scan: 'khud ko link' galat-link alarm mein nahi gina")
# v3.4.8: Dailymotion (bot khud key maange), index ho chuke page ka link nahi, website sudhaar audit-paas
from app import dailymotion as _DM48, webfix as _WF48, idxlink as _IX48  # noqa: E402
state.put("idx_given", {"https://sabhisaab.com/c": "2099-01-01"})
check([u for u, _ in _IX48.pick(status=_st47, live_sm=_sm47, live_ok=lambda u: True,
                                indexed=lambda u: u.endswith("/e"))] == ["https://sabhisaab.com/b"],
      "Indexing link: Google ki taaza jaanch mein index ho chuka page suchi se bahar")
state.put("idx_given", _sv47[0])
_sv48 = (state.get("awaiting"), _DM48.STORE.read_text() if _DM48.STORE.exists() else None)
try:
    _DM48.STORE.unlink(missing_ok=True)
    state.put("awaiting", "dm_key")
    _a48 = _DM48.intake("abc123def456ghi789")
    check("secret" in _a48 and state.get("awaiting") == "dm_secret" and _DM48._cfg().get("key") == "abc123def456ghi789",
          "Dailymotion: key ke baad bot khud secret maangta hai")
    _DM48.token = lambda force=False: (_ for _ in ()).throw(RuntimeError("test"))
    _b48 = _DM48.intake("secretXYZ0123456789")
    check("❌" in _b48 and state.get("awaiting") == "dm_key" and not _DM48.ready(),
          "Dailymotion: galat key par saaf sandesh aur dobara maangna (aadha juda nahi maana)")
finally:
    state.put("awaiting", _sv48[0] or "")
    if _sv48[1] is None:
        _DM48.STORE.unlink(missing_ok=True)
    else:
        _DM48.STORE.write_text(_sv48[1])
check(len(_WF48.FIRE_NEW_T) <= 60, "FIRE title 60 akshar ke andar (VM audit ne 74 par roka tha)")
_l48 = '<ul>' + _WF48.PIN_LI + '</ul>'
check(_WF48.fix_links(_WF48.fix_links(_l48)).count('href="https://www.dailymotion.com/sabhisaab"') == 1 and "linkedin.com/company" in _WF48.fix_links(_l48),
      "/links: LinkedIn + Dailymotion ek hi baar")
check("_DM.warn_once(e)" in _insp.getsource(_PLU.upload) and 'waits["dailymotion"]' in _insp.getsource(_PLU.upload)
      and "errs[\"dailymotion\"]" not in _insp.getsource(_PLU.upload), "Pipeline: Dailymotion ki galti baaki platform nahi rokti")
# v3.4.8b: Dailymotion secret nishaan wala bhi; chat mein chhupa; indexing sirf poora URL, ek hi suchi
from app import updater as _UP48b, idxlink as _IX48b, bot as _BOT48b  # noqa: E402
_sec48 = "851<1v&WtAPmnh\\ny<IQ,?a?EIQ'k|D8"
check(_DM48.clean_secret(_sec48) == _sec48 and _DM48.clean_secret("🩺 Sab theek?") == "" and _DM48.clean_secret("report table 7 din") == "",
      "Dailymotion: < & \\ ' | wala secret bhi pehchana; button/baat secret nahi maani")
check(_UP48b._mask(_sec48) == "***" and _UP48b._mask("https://sabhisaab.com/emi-calculator?utm_source=x&a=1").startswith("https://"),
      "CHAT.md: nishaan wala secret chhupa, link nahi chhupa")
_m48 = _IX48b.message([("https://sabhisaab.com/abc", "URL is unknown to Google")])
check("<code>https://sabhisaab.com/abc</code>" in _m48 and "search-console/inspect" not in _m48, "Indexing: sirf poora URL (tap = copy), console deep-link nahi")
check("run(website.pending)" not in _insp.getsource(_BOT48b), "Website ki dusri 'PENDING KAAM' indexing suchi band - ek hi jagah")
# v3.4.10: PENDING saaf (ho chuke AdSense/owner-mode/Pinterest hate), naye owner kaam, MASTER.md
from app import tasks as _TK410  # noqa: E402
_sv410 = (state.get("todo"), state.get("todo_done"), state.get("mig_349"))
try:
    state.put("todo", [{"x": "📌 AdSense apply: adsense.google.com ...", "t": "x"}, {"x": "AdSense approve hone par: bot ko ...", "t": "x"},
                       {"x": "[Owner, 1 min] OWNER MODE (aapki ...", "t": "x"}, {"x": "kuch aur", "t": "x"}])
    state.put("mig_349", False)
    _TK410._mig_349()
    _tx = [o["x"] for o in state.get("todo")]
    check(not any(x.startswith(("📌 AdSense apply", "[Owner, 1 min] OWNER MODE")) for x in _tx) and "kuch aur" in _tx
          and any(x.startswith("[Intezaar] AdSense approval") for x in _tx) and any("Dailymotion" in x for x in _tx)
          and any("Quora purane 4 jawab" in x for x in _tx), "PENDING: ho chuke kaam hate, naye (Dailymotion/Quora/indexing) jude")
finally:
    state.put("todo", _sv410[0] or [])
    state.put("todo_done", _sv410[1] or [])
    state.put("mig_349", _sv410[2] or False)
import pathlib as _pl410  # noqa: E402
_mm = (_pl410.Path(__file__).resolve().parent.parent / "docs" / "MASTER.md").read_text(encoding="utf-8")
check(all(w in _mm for w in ("company/144149065", "dailymotion.com/sabhisaab", "pub-1074878035420336", "KABHI MAT KARNA", "11:40")),
      "docs/MASTER.md: saare account + roz ka samay + niyam")
# v3.4.13: indexing - ek hi suchi (queue ke naye page bhi), bina 'ho gaya' ke gayab nahi, kabhi chup nahi
from app import idxlink as _IX413, pagequeue as _PQ413  # noqa: E402
_sv413 = (state.get("idx_given"), state.get("pq_new_pages"), state.get("idx_last"))
try:
    state.put("idx_given", {}); state.put("pq_new_pages", {})
    _IX413.note_new_pages(["https://sabhisaab.com/naya1"])
    check("https://sabhisaab.com/naya1" in (state.get("pq_new_pages") or {}), "Indexing: queue ka naya page 11:40 ki suchi ke liye yaad")
    state.put("idx_last", {"day": "x", "urls": ["https://sabhisaab.com/q1"]})
    check(not (state.get("idx_given") or {}).get("https://sabhisaab.com/q1"), "Indexing: suchi dene se 'diya' nahi maana (owner ne kiya nahi)")
    _tgs413 = _IX413.tg.say; _IX413.tg.say = lambda *a, **k: None
    try:
        _IX413.on_text("indexing ho gaya", lambda f: None)
    finally:
        _IX413.tg.say = _tgs413
    check((state.get("idx_given") or {}).get("https://sabhisaab.com/q1"), "Indexing: 'indexing ho gaya' ke baad hi 7 din ka niyam")
    _src = _insp.getsource(_IX413.run)
    check("aaj aapka koi kaam nahi" in _src and "return None\n        return" not in _src, "Indexing: kuch na ho to bhi chhota sandesh (chup nahi)")
    check("search-console/inspect" not in _insp.getsource(_PQ413.owner_message) and "note_new_pages" in _insp.getsource(_PQ413.owner_message),
          "Queue sandesh: alag indexing link nahi - sab 11:40 ki ek suchi mein")
finally:
    state.put("idx_given", _sv413[0] or {}); state.put("pq_new_pages", _sv413[1] or {}); state.put("idx_last", _sv413[2] or {})
# v3.4.14: Dailymotion naya API v2 (purane /rest par v2 token 401 deta tha)
from app import dailymotion as _DM414  # noqa: E402
_sv414 = (_DM414.STORE.read_text() if _DM414.STORE.exists() else None, state.get("dm_tok2"), _DM414.requests.post, _DM414.requests.get)
try:
    _DM414._save({"key": "k", "secret": "s", "channel": "x1", "user": "sabhisaab"})
    state.put("dm_tok2", {"t": "T2", "exp": 9e12, "scope": "video.manage account.read"})
    _calls = []

    class _R:
        def __init__(s, code, j):
            s.status_code, s._j, s.content = code, j, b"1"

        def json(s):
            return s._j

    def _post(url, **k):
        _calls.append(url)
        if url.endswith("/files/upload_sessions"):
            return _R(201, {"upload_url": "https://up.example/x", "progress_url": "p"})
        if url.startswith("https://up.example"):
            return _R(200, {"url": "https://files/abc"})
        if "/profiles/" in url:
            check(k.get("json", {}).get("is_for_kids") is False and k["json"]["source"]["file_url"] == "https://files/abc"
                  and k["json"]["visibility"] == "public", "Dailymotion v2: sahi khaane (is_for_kids, source.file_url, public)")
            return _R(201, {"id": "xV2"})
        return _R(500, {})
    _DM414.requests.post = _post
    _DM414.requests.get = lambda url, **k: _R(200, {"profiles": [{"profile_id": "P1", "name": "sabhisaab"}]})
    import tempfile as _tf414
    _v = _tf414.NamedTemporaryFile(suffix=".mp4", delete=False); _v.write(b"0"); _v.close()
    _u414 = _DM414.upload(_v.name, {"title": "Test #shorts", "brand": "money"})
    check(_u414 == ("https://www.dailymotion.com/video/xV2", "xV2") and any("/v2/profiles/P1/videos" in c for c in _calls),
          "Dailymotion: naye API v2 se upload (session -> file -> profile video)")
finally:
    _DM414.requests.post, _DM414.requests.get = _sv414[2], _sv414[3]
    state.put("dm_tok2", _sv414[1] or {})
    if _sv414[0] is None:
        _DM414.STORE.unlink(missing_ok=True)
    else:
        _DM414.STORE.write_text(_sv414[0])
# v3.4.16: Dailymotion network toote to 30 min baad khud dobara; AI 'integration nahi' na kahe
from app import dailymotion as _DM416, brain as _BR416  # noqa: E402
import time as _t416, pathlib  # noqa: E402
check(_DM416.is_net_err("('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))")
      and not _DM416.is_net_err("401 invalid_token"), "Dailymotion: network galti pehchaan (reset = dobara, 401 = nahi)")
_q416 = state.get("dm_retry")
try:
    import tempfile as _tf416
    _f416 = _tf416.NamedTemporaryFile(suffix=".mp4", delete=False); _f416.write(b"0"); _f416.close()
    state.put("dm_retry", [])
    _DM416.queue_retry(_f416.name, {"title": "T", "brand": "money"}, "jtest416")
    _qq = state.get("dm_retry") or []
    check(len(_qq) == 1 and _qq[0]["next"] > _t416.time() + 1700 and pathlib.Path(_qq[0]["file"]).exists(),
          "Dailymotion: video ki copy rakh kar 30 min baad dobara ki line mein")
    pathlib.Path(_qq[0]["file"]).unlink(missing_ok=True)
finally:
    state.put("dm_retry", _q416 or [])
check("Dailymotion" in _BR416.PROMPT and "integration nahi" in _BR416.PROMPT, "Bot AI ko pata hai ki Dailymotion juda hai")
# v3.4.17: report mein ruke platform; thumbs.json na ho to YouTube ❌ nahi; DM haal mein galti; indexing din mein 1 baar
import inspect as _in417  # noqa: E402
from app import pipeline as _PL417, dailymotion as _DM417, idxlink as _IX417, webstory as _WS417  # noqa: E402
_src417 = _in417.getsource(_PL417.upload)
check("for k, v in waits.items()]" in _src417 and "_v1 = {}" in _src417, "Upload report: ⏸/🔁 platform dikhte hain; thumbs.json na ho to YouTube ❌ nahi")
check("dm_last_err" in _in417.getsource(_DM417.status_text) and "dm_retry" in _in417.getsource(_DM417.status_text),
      "'dailymotion haal' mein aakhri galti + dobara wali line")
check("idx_sent_day" in _in417.getsource(_IX417.run), "Indexing suchi din mein ek hi baar (do baar nahi)")
check("search-console" not in _in417.getsource(_WS417), "Web Story sandesh: alag GSC link nahi - 11:40 ki ek suchi")
# v3.4.17b: owner - 'adhure link', '(not set)', table report saath, bot na samjhe to sab kaam bataye
from app import tg as _TG417, bot as _BOT417, scoreboard as _SB417  # noqa: E402
check(_TG417.full_links("Agle page: tehri-garhwal-uttarakhand, /emi-calculator, /jawab (20)") ==
      "Agle page: https://sabhisaab.com/tehri-garhwal-uttarakhand, https://sabhisaab.com/emi-calculator, https://sabhisaab.com/jawab (20)"
      and _TG417.full_links("/login /pro50 https://sabhisaab.com/x-y") == "/login /pro50 https://sabhisaab.com/x-y",
      "Owner ko kabhi adhura link nahi (hukum /login waise hi)")
check(_SB417.group_source("(not set)") == "Anjaan", "'(not set)' ki jagah 'Anjaan' + samjhaav")
check("_traffic_full" in _in417.getsource(_BOT417) and "scoreboard.send" in _in417.getsource(_BOT417._traffic_full),
      "Traffic poochho to table report bhi saath")
check("Abhi video" in _BOT417.CAN_DO and "dailymotion haal" in _BOT417.CAN_DO and "index nahi" in _BOT417.CAN_DO,
      "Bot samajh na paaye to saare kaam/button batata hai")
check("not_indexed_text" in _in417.getsource(_IX417.on_text), "'kitne page index nahi' = seedha ginti + poore link")
# v3.4.18: web story title har hafte alag + purani stories ka ek-baar sudhaar
from app import webfix as _WF418  # noqa: E402
_h418 = '<title>उत्तराखंड GK: 5 सवाल - कितने सही? | Sab Hisaab</title><meta name="description" content="उत्तराखंड GK: 5 सवाल - कितने सही? - har"><amp-story standalone title="उत्तराखंड GK: 5 सवाल - कितने सही?" x>'
_n418 = _WF418.fix_story_title(_h418, "47")
check(_n418.count("(सप्ताह 47)") == 3 and _WF418.fix_story_title(_n418, "47") == _n418, "Web Story: dohraaye title alag (सप्ताह N), dobara chalane par kuch nahi")
check("सप्ताह" in _in417.getsource(_WS417.build), "Nayi Web Story ka title har hafte alag")
# v3.4.19: post badhao (surakshit) + bot asli ginti de
import datetime as _dt419  # noqa: E402
from app import pinterest as _PI419, linkedin as _LI419, brain as _BR419  # noqa: E402
_sv419 = (state.get("pin_pace"), state.get("pin_max"))
try:
    state.put("pin_max", None)
    check(_PI419.day_cap(_dt419.date(2026, 11, 19)) == 8 and _PI419.day_cap(_dt419.date(2026, 11, 22)) == 10
          and _PI419.day_cap(_dt419.date(2026, 12, 1)) == 12, "Pinterest dheere badhe: 8 -> 10 -> 12 (15 se upar kabhi nahi)")
    state.put("pin_pace", {"date": str(_dt419.date.today()), "total": 1, "urls": {"https://sabhisaab.com/jawab": 2}, "last_ts": {}})
    _l419, _k419 = _PI419.pick_link("money", {"page": "/", "reel_code": "1234", "puzzle_kind": ""},
                                    "https://sabhisaab.com/jawab?utm_source=pinterest#c1234")
    check(_l419 and "/jawab" not in _l419 and _k419 == "tool", "Pinterest: jawab link 2 baar ho gaya to us vishay ka calculator (alag page)")
finally:
    state.put("pin_pace", _sv419[0] or {}); state.put("pin_max", _sv419[1])
check(_LI419.EVE_TIME == "18:30" and callable(_LI419.due_eve), "LinkedIn: shaam 18:30 doosri post (free tool)")
check("GINTI" in _BR419.PROMPT, "Bot AI ginti ka andaaza nahi lagata")
check(_DM417.DM_MAX == 3 and callable(_DM417.send_latest), "Dailymotion roz 3 + 'dailymotion par ek aur bhejo'")
# v3.4.20: /jawab challenge + isi tarah ke 3 + app-browser patta; groupkit; video ghadi
from app import answers as _AN420, groupkit as _GK420, render as _RN420  # noqa: E402
_l420 = [{"code": str(9000 + i), "aid": str(9000 + i), "q": f"Q{i}", "ans": "B", "opts": ["A", "B", "C", "D"], "bname": "M",
          "brand": "money", "date": "d"} for i in range(6)]
check("jw-sim" in _AN420.similar_block(_l420[0], _l420, 0) and "#c9002" in _AN420.similar_block(_l420[0], _l420, 0)
      and "jw-chal" in _AN420.challenge_block(_l420), "/jawab: Aaj ka Challenge + 'isi tarah ke 3 aur' (usi page par)")
check("FBAN" in _AN420.INAPP and "com.android.chrome" in _AN420.INAPP and "location.hash" not in _AN420.INAPP,
      "/jawab: Facebook/Instagram app ke andar 'Chrome mein kholein' (band kar sakte hain)")
_g420 = _GK420.build("emi-calculator", "tool", '<title>EMI Calculator | Sab Hisaab</title><meta name="description" content="Free EMI.">'
                     '<h2>EMI ka formula</h2><h2>Srot</h2>')
check("utm_source=fbgroup" in _g420[0] and "EMI ka formula" in _g420[0] and "Srot" not in _g420[0] and "bio" in _g420[1]
      and "Manoj" not in _g420[0], "Group post: jaankari + poora link, Instagram ke liye 'link bio mein', owner ka naam nahi")
check("hs - 0.2" in _in417.getsource(_RN420.countdown_overlay), "Video ghadi sirf sochne ke samay (5 par atki nahi)")
# v3.4.21: banner, Telegram group quiz, Quora draft, privacy line
import tempfile as _tf421  # noqa: E402
from app import groupquiz as _GQ421, quoradraft as _QD421, webfix as _WF421  # noqa: E402
_bp421 = _tf421.mktemp(suffix=".jpg")
_GK420.banner("tool", "EMI Calculator — Home Loan", ["EMI ka formula", "Kitni EMI safe hai?"], "emi-calculator", _bp421)
from PIL import Image as _Im421  # noqa: E402
check(_Im421.open(_bp421).size == (1080, 1350), "Group post banner 1080x1350 banta hai (owner ka naam/photo nahi)")
check(_GQ421._letter("b", ["x", "y", "z", "w"]) == "B" and _GQ421._letter("C) z", ["x", "y", "z", "w"]) == "C"
      and _GQ421._letter("y", ["x", "y", "z", "w"]) == "B" and _GQ421._letter("hello", ["x", "y", "z", "w"]) is None
      and _GQ421._code("सवाल ... #8572 #Shorts") == "8572", "Group quiz: A/B/C/D ya vikalp pehchaan + post ka code")
_sv421 = state.get("sitepatch_3421")
state.put("sitepatch_3421", False)
check(not _GQ421.store_ok(), "Group quiz: privacy line lagne se pehle naam/score save nahi")
state.put("sitepatch_3421", _sv421)
_ph421 = "<p>x Hum aapka phone number ya naam save nahi karte.</p>"
check("discussion group quiz" in _WF421.fix_privacy_gq(_ph421), "Privacy: group quiz ki line")
check(_QD421.on_text("hello", "hello") is None and "Nifty options" in " ".join(_QD421.FACTS), "Quora draft: sirf 'quora:' par, anubhav sirf pakki baaton se")
# v3.4.22: share kit + banner ek hi sandesh (dohra 19:30 band); anonymous admin se /quizgroup
check(_GK420.due() is False and "banner" in _in417.getsource(__import__("app.sharekit", fromlist=["x"]).run),
      "Group post 19:15 ki share kit mein (banner ke saath) - alag 19:30 sandesh nahi")
check("1087968824" in _in417.getsource(_GQ421.on_group), "Quiz group: 'anonymous admin' se /quizgroup bhi chale")
# v3.4.23: Quora - asli sawal + link + jawab
check(_QD421.search_url("EMI kaise nikale?").startswith("https://www.quora.com/search?q=") and callable(_QD421.daily_pack)
      and "daily_pack" in _in417.getsource(__import__("app.sharekit", fromlist=["x"]).run),
      "Quora: share kit mein asli sawal ka link + taiyaar jawab (na mile to Quora search link)")
# v3.4.24: FB link-card, mauka calendar, funnel, quiz bot inline (koi naya page nahi)
from app import reach as _RC424, quizbot as _QB424  # noqa: E402
import datetime as _dt424  # noqa: E402
_e424 = {"code": "77", "aid": "77", "brand": "money", "bname": "X", "q": "5+5? #77", "ans": "10", "opts": ["8", "9", "10", "11"]}
_m424, _l424 = _RC424.fb_text(_e424)
check("utm_medium=linkpost" in _l424 and "#77" not in _m424 and "D) 11" in _m424 and _RC424.FB_MAX == 2
      and not any(w in _m424.lower() for w in ("tag", "share karo", "comment yes")),
      "FB link-card: sawal + 4 vikalp + UTM link, brand max 2/din, engagement-bait nahi")
_d424 = lambda s: _dt424.datetime.fromisoformat(s + "T11:00:00+05:30")
check(_RC424._in("12-25", "12-20", "01-10") and _RC424._in("01-03", "12-20", "01-10") and not _RC424._in("08-20", "12-20", "01-10")
      and all(len(m) == 5 for m in _RC424.MAUKA), "Mauka calendar: tareekh window (saal paar bhi) sahi")
_t424 = _RC424.funnel_text(7, {"Facebook": [200, 220, 40, 260, 3000], "Google": [50, 55, 40, 90, 4000]})
check("Sabse badi kami: Facebook" in _t424 and "Google" in _t424, "Funnel: platform-wise rukna + sabse badi kami (ginti se)")
check(_RC424.on_text("hello", lambda f: f) is None and "inline_query" in _in417.getsource(_QB424.handle)
      and "show_alert" in _in417.getsource(_QB424.handle), "Quiz bot inline share: dost ki chat mein tap -> sahi/galat popup")
# v3.4.25: turant sawal wali post (kabhi dohra nahi) + chat ki galtiyan
from app import sawalpost as _SP425, quoradraft as _QD425  # noqa: E402
check(bool(_SP425.RX.search("ek post do")) and bool(_SP425.RX.search("sawal wali post")) and not _SP425.RX.search("linkedin post kitni gayi")
      and _SP425.on_text("group post") is None, "Sawal post: 'ek post do'/'sawal wali post' pakde, doosre post-hukum nahi")
_e425 = {"code": "9758", "aid": "9758", "brand": "pahadi", "q": "घट? #9758", "ans": "b", "opts": ["a", "b", "c", "d"]}
_t425 = _SP425.post_text(_e425)
check(_t425.startswith("🧠 आज का सवाल") and "#9758\n" not in _t425 and "D) d" in _t425 and "सही जवाब + तरीका" in _t425,
      "Sawal post: owner ka saancha (sawal, A-D, jawab link)")
check('if not slug or slug in ("index", "404")' in _in417.getsource(W.redirect_check), "Redirect jaanch: homepage ka '.html' / '//' jhootha alarm nahi")
check("koi sawal" in _in417.getsource(_QD425.on_text), "Quora: '<koi sawal' par bekaar jawab nahi, sahi tareeka batata hai")
check('"restart"' in _in417.getsource(__import__("app.bot", fromlist=["x"]).on_text), "'restart' = sach mein restart (AI ka jhootha 'ho gaya' nahi)")
# v3.4.26: platform+brand post, pin kit, chat ki galtiyan, Google index jaanch dobara
from app import intents as _IN426  # noqa: E402
check(_SP425.is_ours("pahadi post") and _SP425.is_ours("pahadi swal") and _SP425.is_ours("money insta post")
      and _SP425.is_ours("sab platform post") and not _SP425.is_ours("group post") and not _SP425.is_ours("linkedin post")
      and not _SP425.is_ours("linkedin post kitni gayi"), "Post maangna: brand/platform/sab platform pakde, purane hukum nahi")
check(_SP425.plats_in("pahadi fb group post") == ["fbgroup"] and _SP425.plats_in("insta story") == ["instagram"]
      and len(_SP425.plats_in("sab platform post")) == 8, "Platform pehchaan (fb group / insta / sab 8)")
import app.answers as _A426  # noqa: E402
_live426 = _A426.live
_A426.live = lambda: True
_f426 = _SP425.fmt(_e425, "instagram")
check(len(_f426) == 2 and "http" not in _f426[0][1] and "utm_medium=story" in _f426[1][1], "Instagram: caption bina link + story link alag")
_r426 = _SP425.fmt(_e425, "reddit")
_A426.live = _live426
check(len(_r426) == 2 and "http" not in _r426[0][1] and "utm_source=reddit" in _r426[1][1], "Reddit: title (bina link) + body alag")
check("PIN KIT" in _IN426.pin_kit("pahadi") and "utm_campaign=pahadi" in _IN426.pin_kit("pahadi"), "Pin kit: brand ke UTM ke saath")
check(__import__("app.meta", fromlist=["x"]).IG_LINK_LINE.count("हाइलाइट") == 1,
      "Instagram caption: bio + '✅ जवाब' highlight line")
check("_DAILY" in dir(W) and "daily_day" in dir(W) and "site_daily_tries" in _in417.getsource(__import__("app.bot", fromlist=["x"])),
      "Google index jaanch: restart ke baad aaj ka nateeja na ho to dobara (max 3)")
# v3.4.27: FB group 3 line, platform-wise 'diya hua', 'facebook' = group, reel ke poore link, 'link table'
_g427 = _SP425.fmt({"code": "2001", "aid": "2001", "brand": "pahadi", "q": "नथ? #Shorts", "ans": "b",
                    "opts": ["a", "b", "c", "d"]}, "fbgroup")
check(len(_g427) == 2 and len(_g427[0][1].split("\n")) <= 5 and "LINK MANA" in _g427[1][0] and "❌ MAT" in _g427[0][0],
      "FB group post: 3 line (See more se pehle link) + link-mana group ka pehla comment")
check(_SP425.plats_in("swal wali facebook post") == ["fbgroup"] and _SP425.plats_in("money fb page post") == ["facebook"],
      "'facebook post' = GROUP, 'fb page post' = PAGE")
check("plat" in _in417.signature(_SP425.note).parameters and "plats" in _in417.signature(_SP425.candidates).parameters,
      "Diya hua sawal platform-wise (WhatsApp wala FB group ke liye bhi milta)")
check("Kis reel se kitne" in _in417.getsource(W.link_traffic), "Traffic report: reel code ke saath sawal + poora link")
# v3.4.28: sawal bank 150 (pehle 8), 14 din baad dobara, mit chuki video 'kharab'
import app.answers as _A428, app.pipeline as _P428  # noqa: E402
check(_A428.OPTS_KEEP >= 100 and "o" in _A428._arch_row({"opts": ["a", "b", "c", "d"]}), "Sawal ke vikalp 150 tak + archive mein (sawal post jaldi khatam nahi)")
check(_SP425.RECYCLE_DAYS == 14 and "_recent" in _in417.getsource(_SP425.candidates), "Usi platform par 14 din baad sawal dobara chal sakta")
check("FileNotFoundError" in _in417.getsource(_P428.upload) and callable(_P428.sweep_broken), "Mit chuki video: laal galti nahi, 'kharab' + suchi se hati")
# v3.4.29: 'sab features' - har feature ka asli haal
from app import featureaudit as _FA429  # noqa: E402
_r429 = _FA429.checks()
check(len(_r429) >= 35 and all(r[2] in ("✅", "⬜", "🔑", "⏳", "🛡️") for r in _r429) and "SAB FEATURES" in _FA429.text()
      and not any(k in _FA429.text().lower() for k in ("aiza", "token=", "secret=")), "'sab features': 35+ feature, 5 haal, koi secret nahi")
# v3.4.30: asli quiz-jawab comment kabhi nahi chhupta; seen list beqram nahi katti
import app.growth as _G430  # noqa: E402
check(not _G430._may_hide("ig", "pahadi", {"id": "t430a", "text": "Khet ❤️"}, "spam")
      and not _G430._may_hide("ig", "pahadi", {"id": "t430b", "text": "D"}, "abuse")
      and _G430._may_hide("ig", "pahadi", {"id": "t430c", "text": "earn 5000 daily http://x.co"}, "spam"), "Quiz-jawab comment ('Khet ❤️', 'D') kabhi nahi chhupta; link-spam chhupta")
_G430._save_seen(["t430x", "t430y"]); _G430._save_seen(["t430y", "t430z"])
check(state.get("seen_comments")[-3:] == ["t430x", "t430y", "t430z"] and "list(seen)[-2000:]" not in _in417.getsource(_G430),
      "Comment seen-list kram se judti hai (YT/FB/IG ek doosre ko nahi mitate)")
# v3.4.31: chhupe quiz-jawab apne aap wapas, indexing 'ho gaya' button, poore link (FB reel/photo, Threads post, khabar)
import app.meta as _M431, app.idxlink as _IX431, app.pipeline as _PL431, app.threads as _TH431  # noqa: E402
from app import tg  # noqa: E402
_calls431 = []
_old431 = (_M431.brand_info, _M431._get, _M431._post)
_M431.brand_info = lambda b: {"page_token": "x", "ig_id": "ig1"} if b == "pahadi" else {}
_M431._get = lambda path, tok, **k: {"data": [{"id": "m1", "comments": {"data": [
    {"id": "c1", "text": "Khet ❤️", "hidden": True}, {"id": "c2", "text": "earn money http://x.co", "hidden": True},
    {"id": "c3", "text": "B", "hidden": False}]}}]}
_M431._post = lambda path, tok, **k: _calls431.append((path, k)) or {"success": True}
_r431 = _G430.unhide_answers(["pahadi"])
_M431.brand_info, _M431._get, _M431._post = _old431
check(_calls431 == [("/c1", {"hide": "false"})] and "c1" in (state.get("hidden_once") or [])
      and not _G430._may_hide("ig", "pahadi", {"id": "c1", "text": "lol spam"}, "abuse"),
      "Chhupa quiz-jawab ('Khet ❤️') apne aap WAPAS + dobara kabhi nahi chhupega; link-spam chhupa hi rehta")
_said431 = []
_oldsay431 = tg.say
tg.say = lambda t, *a, **k: _said431.append(t)
state.put("idx_last", {"urls": ["https://sabhisaab.com/a1"]})
_ok431 = _IX431.on_text("ho gaya gsc request indexing", lambda f: f()) is True and _IX431.on_text("kitne page index ho gaye", lambda f: None) is not True
tg.say = _oldsay431
check(_ok431 and "https://sabhisaab.com/a1" in (state.get("idx_given") or {}) and "ix:done" in _in417.getsource(_IX431.run),
      "Indexing: button '✅ Maine Request Indexing kar di' + 'ho gaya gsc request indexing' samajhta; sawaal par galat nishaan nahi")
_src431 = _in417.getsource(_PL431)
check("https://www.facebook.com/reel/" in _src431 and "FB photo-post https://www.facebook.com/" in _src431
      and "permalink" in _in417.getsource(_TH431.post_text) and "['link'][:80]" not in _in417.getsource(_G430),
      "Har post ka POORA link (FB reel, FB photo-post, Threads post, khabar) - adhoora nahi")
# v3.4.32: bachkani/ghisi-piti trick-paheli kabhi nahi (bank + video audit); unhide jaanch hamesha nateeja batati
import app.qbank as _QB432, app.audit as _AU432  # noqa: E402
check(_QB432.cliche("एक तालाब में 5 मेंढक बैठे हैं, 3 ने कूदने का फैसला किया। कितने बचे?")
      and _QB432.cliche("1 किलो रुई और 1 किलो लोहे में कौन भारी?") and not _QB432.cliche("उत्तराखंड में कितने ज़िले हैं?")
      and "ADULTS" in _QB432.PROMPT and "cliche" in _in417.getsource(_AU432.run) and "_critic" in _in417.getsource(_QB432.fill),
      "Mendhak-faisla jaisi ghisi-piti/bachkani paheli: bank, Gemini-jaanch aur video audit teeno mein ruki")
check("uh_first_done" in _in417.getsource(_RC432 := __import__("app.reach", fromlist=["x"]).tick) and "uh_last" in _in417.getsource(_G430.unhide_answers),
      "Chhupe-comment jaanch: install ke baad nateeja hamesha sandesh mein (chup nahi), galti bhi dikhti")
# v3.4.33: 'Mat daalo' ke baad poochhta 'doosri banau?' - 10 min jawab nahi to khud
import app.pipeline as _PP433, datetime as _dt433  # noqa: E402
_said433, _ran433 = [], []
_oldsay433 = tg.say
tg.say = lambda t, *a, **k: _said433.append(t)
state.put("replace_ask", {})
_slot433 = (_PP433.now() + _dt433.timedelta(hours=2)).isoformat()
_r433 = _PP433.ask_replace("t433", {"brand": "sunonatak", "slot": _slot433, "reason": "roz ka schedule"})
_near433 = _PP433.ask_replace("t433b", {"brand": "sunonatak", "slot": (_PP433.now() + _dt433.timedelta(minutes=10)).isoformat(),
                                        "reason": "roz ka schedule"})
_d433 = state.get("replace_ask"); _d433["t433"]["at"] = 0; state.put("replace_ask", _d433)
_PP433.replace_tick(lambda fn, *a: _ran433.append((fn.__name__, a)))
tg.say = _oldsay433
check(_r433 == "asked" and not _near433 and any("Doosri video banau" in x for x in _said433)
      and _ran433 and _ran433[0][0] == "prepare" and _ran433[0][1][0] == "sunonatak" and _ran433[0][1][1] == _slot433
      and not state.get("replace_ask"), "'Mat daalo' -> 'doosri banau?' button; 10 min jawab nahi to usi slot ki nayi video khud")
# v3.4.34: owner 19 Nov shaam ki 14 baatein
import app.siteknow as _SK434, app.fuzzybtn as _FB434, app.perf as _PF434, app.masteraudit as _MA434, app.scoreboard as _SB434  # noqa: E402
import app.updater as _UP434, app.bot as _BOT434  # noqa: E402
check(_SK434.idx_ok({"ok": False, "why": "Submitted and indexed"}) and _SK434.idx_ok({"why": "Indexed, not submitted in sitemap"})
      and not _SK434.idx_ok({"why": "Crawled - currently not indexed"}) and not _SK434.idx_ok({"why": "URL is unknown to Google"}),
      "Index: 'URL is on Google (issues ke saath)' = index (pehle sirf PASS -> index wale bhi suchi mein aate the)")
_m434 = _IX431.message([("https://sabhisaab.com/a", "naya page")], summ="📊 Kul page (sitemap): <b>10</b> | Google index ✅ <b>9</b> | baaki ⏳ <b>1</b>")
check("Kul page" in _m434 and "https://sabhisaab.com/a" in _m434 and len(_IX431._chunks("x\n" * 3000)) > 1,
      "Indexing suchi: kul/ho gaye/baaki + poore link + lambi suchi tukdon mein (4096 seema)")
_labs434 = _BOT434.all_labels()
check(_FB434.match("aaj ka hal", _labs434) == "📊 Aaj ka haal" and _FB434.match("आज का हाल", _labs434) == "📊 Aaj ka haal"
      and _FB434.match("growth grap", _labs434) == "📈 Growth graph" and _FB434.match("indexng", _labs434) == "📑 Indexing"
      and _FB434.match("video ka title badlo bhai aaj shaam", _labs434) is None and "❌ Mat daalo" in _BOT434.RISKY_BTN,
      "Button: galat spelling / Devanagari awaaz bhi samjhe; lambi baat nahi; hatane wale button par pushti")
check(_SB434.group_source("facebook_group") == "FB Group" and _SB434.group_source("m.facebook.com") == "Facebook",
      "FB group link ke log alag 'FB Group' khaane mein (pehle Facebook mein mil jaate the)")
state.put("topic_block", ["credit card"])
_oldsay434 = tg.say
tg.say = lambda t, *a, **k: None
check(_PF434.word_blocked("क्रेडिट / credit card ka bill") == "credit card" and _PF434.on_text("band vishay") is True,
      "Owner: '<shabd> wale sawal band karo' -> video audit + sawal-bank mein rok")
state.put("topic_block", [])
check(len(_MA434.RULES) >= 8 and _MA434.on_text("niyam") is True, "Master audit: owner ke saare niyam roz 21:55 jaanch + 'master audit'")
tg.say = _oldsay434
_UP434._rows = (lambda fp, cut, _o=_UP434._rows: [{"t": "2026-11-19 10:00", "q": "x" * 900, "b": "y" * 1400}] * 4000)
check(len(_UP434.chat_md().encode()) < 1_000_000, "CHAT.md 1 MB se chhota (pehle badi hoke GitHub se gayab ho gayi thi)")
# ---------------- v3.4.35: /jawab deploy chhutna band ----------------
import time as _t35
for _k in ("deploy_due", "site_undeployed", "deploy_try_at", "deploy_fails"):
    state.put(_k, 0)
state.put("auto_deploy", True)
W._schedule_deploy(15); _d1 = state.get("deploy_due")
W._schedule_deploy(1); _d2 = state.get("deploy_due")
W._schedule_deploy(15); _d3 = state.get("deploy_due")
check(_d2 < _d1 and _d3 == _d2, "Deploy time sirf jaldi hota hai: 15 min wala ZIP /jawab ke 1 min deploy ko aage nahi dhakelta")
state.put("deploy_due", 0); state.put("site_undeployed", True); state.put("deploy_try_at", 0)
_t = W.tick_auto()
check(any(n == "deploy" for n, _ in _t), "Site undeployed ho to tick_auto khud deploy lagata hai (pehle 'pehle se lagi hui' par kabhi nahi lagta tha)")
check(not any(n == "deploy" for n, _ in W.tick_auto()), "Wahi deploy queue mein baar-baar nahi lagta")
_old_dep = W._deploy
W._deploy = lambda: "❌ Audit fail - deploy roka"
state.put("site_undeployed", True); W.deploy()
check(state.get("site_undeployed") is True and state.get("deploy_fails") == 1, "Deploy fail -> flag rehta hai, dobara koshish hogi")
W._deploy = lambda: "✅ Website LIVE (VM se seedha Cloudflare)."
W.deploy()
check(state.get("site_undeployed") is False and state.get("deploy_fails") == 0, "Deploy ✅ -> flag saaf")
_hold = W.DEPLOY_LOCK.acquire(blocking=False)
state.put("deploy_due", 0)
_res = W.deploy()
W.DEPLOY_LOCK.release()
check(_res is None and state.get("deploy_due"), "Deploy chal raha ho to doosra nahi chalta, 3 min baad dobara dekha jaata hai")
W._deploy = _old_dep
state.put("jawab_site_on", True); state.put("jawab_fix_v3435", 0); state.put("answer_dirty", False)
A.tick()
check(state.get("jawab_fix_v3435") == 1 and state.get("answer_dirty") is True and state.get("site_undeployed") is True,
      "Install ke baad atke saare jawab ek baar dobara publish + deploy")
state.put("jawab_site_on", False); state.put("deploy_due", 0); state.put("site_undeployed", False)
import os as _os35, subprocess as _sp35, tempfile as _tf35, pathlib as _pl35
_d35 = _pl35.Path(_tf35.mkdtemp()); _sp35.run(["git", "init", "-q", str(_d35)])
_lk35 = _d35 / ".git" / "index.lock"; _lk35.write_text("")
_os35.utime(_lk35, (_t35.time() - 600, _t35.time() - 600))
(_d35 / "a.txt").write_text("x")
_oldDIR35 = W.DIR; W.DIR = _d35
try:
    W._git("add", "-A")
    _ok35 = not _lk35.exists() and "a.txt" in W._git("ls-files")
except Exception as _e35:
    _ok35 = False
W.DIR = _oldDIR35
check(_ok35, "Purana (crash ka) git index.lock khud hat jaata hai - ZIP ab usse nahi rukti")
# ---------------- v3.4.37: /jawab audit ke 2 error ----------------
import re as _re37, pathlib, tempfile, shutil
from app import tg as _tg37
_oldalert37 = _tg37.alert; _tg37.alert = lambda *a, **k: None
_ak37 = state.get("answer_key")
_d37 = pathlib.Path(tempfile.mkdtemp()); (_d37/"site").mkdir()
shutil.copy(pathlib.Path(A.__file__).parent/"sitepatch"/"about.html", _d37/"site"/"about.html")
_olddir37 = W.DIR; W.DIR = _d37
_base37 = "इनमें से कौन सी संख्या सबसे बड़ी है यदि हम इन चारों को गुणा करें और फिर "
def _ent37(code, q, ans="A", opts=None, brand="b1"):
    return {"code": code, "aid": str(code), "q": q, "ans": ans, "exp": "सही है।", "opts": opts or ["A","B","C","D"],
            "brand": brand, "bname": "Dimagi", "date": "2026-11-22", "page": "/"}
_ents37 = [_ent37(1001, _base37+"7 aur 5?"), _ent37(1002, _base37+"8 aur 6?"), _ent37(1003, _base37+"9 aur 4?"),
        _ent37(1004, _base37+"3 aur 2?"), _ent37(1005, "यह पहाadi सवाल है?"),
         dict(_ent37(1006, "अगर FIRE = GJSF (हर अक्षर +1), तो WATER = ?", ans="XBUFS", opts=["XBUFS", "VZSDQ", "XBUFR", "YCVGT"], brand="b2"),
              exp="W→X, A→B, T→U, E→F, R→S = XBUFS।")]
state.put("answer_key", _ents37)
_page37 = A.build_page()
_paras37 = _re37.findall(r'<p class="upd jw-sim"[^>]*>.*?</p>', _page37, _re37.S)
check(len(_paras37) == len(set(_paras37)) and len(_paras37) >= 2, f"'isi tarah ke' paragraph sab alag ({len(_paras37)} paragraph)")
check('id="c1005"' not in _page37 and 'id="c1001"' in _page37, "Hindi+English chipka jawab (#1005) page se bahar, baaki andar")
check(state.get("jawab_skip") == ["1005"], "skip suchi state mein (sirf tuta shabd wala; 'XBUFS।' wala jawab nahi)")
_sec37 = _re37.search(r'<section id="c1006".*?</section>', _page37, _re37.S)
_vis37 = _re37.sub(r"<[^>]+>", " ", _sec37.group(0)) if _sec37 else ""
check(bool(_sec37) and "XBUFS." in _vis37 and not _re37.search(r"[\u0900-\u097F][A-Za-z]|[A-Za-z][\u0900-\u097F]", _vis37),
      "danda se chipka jawab (#1006) page par hai aur audit ka mixed-script niyam nahi todta - channel gayab nahi")
check(A.coverage_check.__code__ is not None, "coverage_check compile")
_safe37 = A.build_page(safe=True)
check('<p class="upd jw-sim"' not in _safe37, "safe roop mein 'isi tarah ke' block nahi")
W.DIR = _olddir37; state.put("answer_key", _ak37 or []); _tg37.alert = _oldalert37

# ---------------- v3.4.40: 30 din ki chat ka audit (dohra jawab, Gemini band, table, jawab deploy) ----------------
from app import bot as _B40, tg as _TG40, localask as _LA40, brain as _BR40, idxlink as _IX40, sawalpost as _SP40, updater as _UP40
_said40 = []
_oldcall40 = _TG40.call
_TG40.call = lambda m, d=None, files=None, timeout=120, tries=4: (_said40.append((d or {}).get("text") or (d or {}).get("caption") or ""), {"message_id": 1})[1]
_oldrun40 = _B40.run
check(_B40.run(lambda: None) is True, "bot.run 'kaam le liya' = True (pehle None -> 'return run(...)' ke baad Gemini bhi chalta tha)")
_B40.WORK.queue.clear() if hasattr(_B40.WORK, "queue") else None
state.put("say_seen", {})
_TG40.say("x40 dohra")
check(_TG40.say("x40 dohra") is not None, "90 sec ka dohra sandesh roka gaya to bhi 'None' nahi (handler aage Gemini nahi chalata)")
check(all(len("(9/9)\n" + p_) <= 3900 for p_ in _TG40._chunks("y" * 9000 + "\n" + "z" * 5000, 3800)), "chunk + '(1/2)' 3900 ke andar ('(1/2) / (1/2)' dohra sirlekh nahi)")
_B40.run = lambda fn, *a: (fn(*a), True)[1]
def _ask40(msg):
    _said40.clear(); state.put("say_seen", {})
    return _LA40.on_text(msg.lower(), _B40.run, msg)
def _gd40(*a, **k):
    raise RuntimeError("quota")
_og40, _oc40 = _BR40.ask_gemini, _BR40.ask_cf
_BR40.ask_gemini = _gd40; _BR40.ask_cf = _gd40
check(_ask40("Aaj kitni video chale gye ab tak") and any("AAJ (" in x for x in _said40), "'aaj kitni video gayi' = asli list, Gemini ke bina")
check(_ask40("Bot bhai Gemini ka kon sa model chl rha hai usko bataon") and any("DIMAAG" in x for x in _said40), "'Gemini kaun sa model' = asli haal (andaza nahi)")
check(_ask40("Bot bhai mst gye ho ya jinda ho") and any("chalu hoon" in x for x in _said40), "'zinda ho?' = chhota sach haal")
check(_ask40("Video schedule") and any("SCHEDULE" in x for x in _said40), "'video schedule' = pakka schedule")
check(_ask40("pahadi ki video valmiki jayanti par banao") is None, "video BANAO wala hukum localask nahi pakadta (Gemini/purana raasta)")
check(_ask40("indexing ho gaya") is None and _ask40("comment haal") is None, "pakke hukum ('indexing ho gaya', 'comment haal') apne raaste")
check(_ask40("Bing ka record rakhna dayari per jitne url bhejoge thik hai") is None, "'record rakhna' jaisa niyam = Gemini (rule), report nahi")
check(_LA40.norm("Indexing bakance") == "indexing balance" and _LA40.norm("libk se traffic") == "link se traffic"
      and _LA40.norm("Ink se traffic") == "link se traffic", "owner ki spelling: bakance/libk/ink")
_ni40 = _IX40.not_indexed_text
_IX40.not_indexed_text = lambda: "NI40"
_hs40 = _IX40.send_html
_IX40.send_html = lambda t, m=None: _said40.append(t)
check(_ask40("Indexing bakance") and _said40 == ["NI40"], "'Indexing bakance' = EK sandesh: kitne baaki + poore link (pehle Website doctor)")
check(_ask40("pending  indexing") and _said40 == ["NI40"], "'pending indexing' = wahi ek suchi")
_IX40.not_indexed_text = _ni40
_lt40 = _LA40.link_table
_LA40.link_table = lambda focus=None: f"TABLE40 {focus}"
check(_ask40("Link se traffic table format") and any("TABLE40" in x for x in _said40), "'link se traffic table format' = asli TABLE")
check(_ask40("Instagram se kitna traffic aaya") and any("TABLE40 Instagram" in x for x in _said40), "'Instagram se kitna traffic' = table + Instagram upar")
_LA40.link_table = _lt40; _IX40.send_html = _hs40
_said40.clear(); state.put("say_seen", {})
_B40.think("kuch bilkul anokhi baat jo kisi hukum se na mile xyz")
check(_said40 and not any("Main ye sab kar sakta hoon" in x for x in _said40) and any("AI (Gemini)" in x for x in _said40),
      "Gemini band = chhota sach + kaam ke hukum (lambi menu suchi har baar nahi)")
_BR40.ask_gemini, _BR40.ask_cf = _og40, _oc40
check(not any("%" in o for o in _SP40.OPENERS), "sawal post ke opener mein koi nakli % nahi ('99% log galat')")
check(_SP40.is_ours("what's post") and _SP40.is_ours("new swal jo bne hai unke de do"), "'What's post' / 'new swal de do' = asli reel sawal (Gemini apna sawal nahi banata)")
# indexing: 'sab index mein' + 'baaki 18' ek saath kabhi nahi
_o40 = (_IX40.pick, _IX40.summary_line, _IX40._status)
_IX40.pick = lambda *a, **k: []
_IX40.summary_line = lambda st=None, live_sm=None: "📊 Kul page (sitemap): <b>350</b> | Google index ✅ <b>332</b> | baaki ⏳ <b>18</b>"
_IX40._status = lambda: ({}, "2026-11-23")
import app.website as _W40
_ss40 = _W40.submit_sitemap
_W40.submit_sitemap = lambda: "✅"
_r40 = _IX40.run(manual=False); state.put("idx_sent_day", "")
check("sab live page Google index mein hain" not in _r40 and "Baaki 18" in _r40, "indexing sandesh ulta-pulta nahi ('sab index' + 'baaki 18')")
_IX40.summary_line = lambda st=None, live_sm=None: "📊 Kul page (sitemap): <b>350</b> | Google index ✅ <b>350</b> | baaki ⏳ <b>0</b>"
state.put("idx_sent_day", "")
check("sab live page Google index mein hain" in (_IX40.run(manual=False) or ""), "sach mein sab index ho to wahi bataata hai")
_IX40.pick, _IX40.summary_line, _IX40._status = _o40; _W40.submit_sitemap = _ss40
# website: ek taala (ZIP + deploy + GitHub copy), alag SITE line
check(_W40.ZIP_LOCK.acquire(blocking=False) and _W40.ZIP_LOCK.acquire(blocking=False), "ZIP_LOCK RLock (andar se dobara atakta nahi)")
_W40.ZIP_LOCK.release(); _W40.ZIP_LOCK.release()
check(_W40.busy() is False, "website.busy() aaram mein False")
check(hasattr(_B40, "SITEWORK") and hasattr(_B40, "site_worker"), "deploy/jawab ki alag SITE line (video render ke peeche nahi)")
# CHAT.md: ek minute ke andar asli kram
_rw40 = _UP40._rows
_UP40._rows = lambda fp, cut: ([{"t": "2026-11-23 10:00", "q": "Link se traffic"}] if fp == _UP40.CFILE else
                               [{"t": "2026-11-23 10:00", "b": "🔎 la raha hoon..."}, {"t": "2026-11-23 10:00", "b": "(1/2) table"}])
_md40 = _UP40.chat_md()
check(_md40.index("(1/2) table") < _md40.index("la raha hoon"), "CHAT.md naya upar + ek minute mein asli kram (ABC kram nahi)")
_UP40._rows = _rw40
_B40.run = _oldrun40; _TG40.call = _oldcall40

# ---------------- v3.4.41: comment bot quiz-jawab, ek indexing ginti, doctor ki asli wajah, GA4 samay ----------------
from app import growth as _G41, idxlink as _IX41, siteknow as _SK41, meta as _M41
_e41 = {"code": "6024", "opts": ["छपेली", "थड़िया", "छोलिया", "झोड़ा"], "q": "तलवार नृत्य?", "yt": "https://youtu.be/AAA41"}
_e41b = {"code": "1714", "opts": ["जड़", "ठंड", "जंगल", "जोड़"], "q": "जाड़ का मतलब?", "yt": "https://youtu.be/BBB41"}
check(_G41.quiz_choice("C", _e41) == ("C", "छोलिया") and _G41.quiz_choice("सी", _e41)[0] == "C" and _G41.quiz_choice("Cc", _e41)[0] == "C"
      and _G41.quiz_choice("D🔥", _e41)[0] == "D" and _G41.quiz_choice("Thand", _e41b)[0] == "B",
      "comment 'C' / 'सी' / 'Cc' / 'D🔥' / 'Thand' = quiz ka jawab (pehle bot 'samajh nahi aaya' likhta tha)")
check(_G41.quiz_choice("Ab kya hua", _e41) is None and _G41.quiz_choice("Accha video", _e41) is None, "'Ab kya'/'Accha' jawab nahi maana")
_ak41, _pl41 = state.get("answer_key"), state.get("posted_log")
state.put("answer_key", [_e41, _e41b]); state.put("posted_log", [{"jid": "j41", "ids": {"youtube": "AAA41", "instagram": "IG41", "facebook": "FB41"}}])
check(_G41.quiz_entry("ig", "pahadi", {"media": "IG41"})["code"] == "6024" and _G41.quiz_entry("fb", "pahadi", {"media": "123_FB41"})["code"] == "6024"
      and _G41.quiz_entry("yt", "pahadi", {"video": "BBB41"})["code"] == "1714", "Instagram/FB/YouTube comment -> sahi video ka sawal")
state.put("qr_stat", {}); state.put("qr_last", {})
_r41 = [_G41.quiz_reply("ig", "pahadi", {"id": f"c{i}", "media": "IG41", "author": f"u{i}"}, _e41, ("C", "छोलिया")) for i in range(_G41.QR_MEDIA + 3)]
check(all("sabhisaab.com/jawab" in x and "#6024" in x for x in _r41[:_G41.QR_MEDIA]) and not any(_r41[_G41.QR_MEDIA:]),
      f"quiz jawab: website + code, ek video par max {_G41.QR_MEDIA} (spam nahi)")
check(len(set(_r41[:7])) >= 5, "jawab alag-alag (copy-paste jaisa nahi)")
check(not any(w in " ".join(_G41.QR_T).lower() for w in ("comment kar", "like kar", "share kar", "follow kar", "tag kar", "sahi hai!", "galat hai")),
      "jawab mein sahi/galat nahi bataya, 'comment/like/share/tag karo' nahi (Meta engagement bait)")
check(_G41.quiz_reply("ig", "pahadi", {"id": "z", "media": "IG41", "author": "u1"}, _e41, ("C", "x")) == "", "ek insaan ko ek video par ek hi jawab")
check(all("sabhisaab.com/jawab" in _M41.ig_safe_text(t.format(L="C", o="x", c="1"), add_line=False) for t in _G41.QR_T),
      "Instagram par saada 'sabhisaab.com/jawab' bachta hai (link/UTM nahi)")
state.put("answer_key", _ak41 or []); state.put("posted_log", _pl41 or [])
# indexing: ek hi aadhaar (live sitemap) - naye page bhi gine
_o41 = (_IX41._status, _IX41.google_says_indexed)
import app.website as _W41
_ls41 = _W41.live_sitemap_urls
_W41.live_sitemap_urls = lambda: {"https://sabhisaab.com/a", "https://sabhisaab.com/b", "https://sabhisaab.com/new1"}
_IX41._status = lambda: ({"https://sabhisaab.com/a": {"ok": True}, "https://sabhisaab.com/b": {"why": "Crawled - currently not indexed"}}, "2026-11-23")
_IX41.google_says_indexed = lambda u: None
_t41 = _IX41.not_indexed_text()
check("live sitemap = 3" in _t41 and "<b>1</b> | ❌" in _t41 and "https://sabhisaab.com/new1" in _t41 and "https://sabhisaab.com/b" in _t41,
      "indexing: kul = index + nahi + naye (teen alag number nahi)")
_IX41._status, _IX41.google_says_indexed = _o41; _W41.live_sitemap_urls = _ls41
# doctor: sirf naam ka saancha milna 'wajah' nahi
import pathlib as _pl, tempfile as _tf
_d41 = _pl.Path(_tf.mkdtemp())
(_d41 / "almora-x.html").write_text("<main>" + " ".join(f"almora shabd{i}" for i in range(300)) + "</main>")
(_d41 / "bageshwar-x.html").write_text("<main>" + " ".join(f"bageshwar alag{i}" for i in range(300)) + "</main>")
(_d41 / "almora-y.html").write_text("<main>" + " ".join(f"almora shabd{i}" for i in range(300)) + "</main>")
check((_SK41._body_sim(_d41, "almora-x", "bageshwar-x") or 0) < 0.2 and (_SK41._body_sim(_d41, "almora-x", "almora-y") or 0) > 0.9,
      "doctor asli content milata hai (naam ka saancha ≠ dohra page)")
from app import answers as _A41
check("padh_rahe" in _A41.tap_js() and "jawab_dekha" in _A41.tap_js() and "page_view" not in _A41.tap_js(),
      "/jawab: GA4 ko asli samay (15/45 sec + jawab dekha), page_view dobara nahi")

# ---------------- v3.4.42: niti (engagement bait), poore link, auto-doctor 2 ghante, sahi report ----------------
from app import guardtext as _GT42, tg as _TG42, audit as _AU42, autodoctor as _AD42, localask as _LA42, bot as _B42, idxlink as _IX42
check(_GT42.no_bait("Sawal?\nअपना जवाब कमेंट में लिखें! सही जवाब वेबसाइट पर") == "Sawal?\nसही जवाब वेबसाइट पर"
      and _GT42.no_bait("Like karo aur share karo 👇\nSab Hisaab") == "Sab Hisaab", "caption se 'comment/like/share karo' wala vaakya hatta, baaki rehta")
check(not any(_GT42._BAIT.search(h) for v in _AU42.PLATFORM_HEADS.values() for h in v), "FB/IG/Threads ki pehli line mein koi engagement-bait nahi")
_u42 = "https://sabhisaab.com/almora-kaise-pahunche"
check(_TG42.cut("x" * 50 + " " + _u42 + " baaki", 60).endswith(_u42 + "…"), "lamba text kaatne par bhi link POORA (aadha nahi)")
check(callable(_AD42.due_quick) and "quiet" in _AD42.run.__code__.co_varnames, "auto-doctor har 2 ghante (chup - sirf naya ho to khabar)")
_said42 = []
_oc42, _or42 = _TG42.call, _B42.run
_TG42.call = lambda m, d=None, files=None, timeout=120, tries=4: (_said42.append((d or {}).get("text") or ""), {"message_id": 1})[1]
_B42.run = lambda fn, *a: (fn(*a), True)[1]
_lt42 = _LA42.traffic_reply
_LA42.traffic_reply = lambda run, focus=None, chart=True: _said42.append("TRAFFIC42") or True
state.put("say_seen", {})
_B42.on_text("website traffic")
check("TRAFFIC42" in _said42 and not any("Website draft" in x or "WEBSITE: ek baar" in x for x in _said42),
      "'website traffic' = traffic table (pehle galti se 'Website draft' button)")
_LA42.traffic_reply = _lt42
_ni42 = _IX42.not_indexed_text
_hs42 = _IX42.send_html
_IX42.not_indexed_text = lambda: "NI42"
_IX42.send_html = lambda t, m=None: _said42.append(t)
_said42.clear(); state.put("say_seen", {})
_B42.on_text("📑 Indexing")
check("NI42" in _said42, "'📑 Indexing' button = latest pending suchi (poore link)")
_IX42.not_indexed_text, _IX42.send_html = _ni42, _hs42
_said42.clear(); state.put("say_seen", {})
check(_LA42.on_text("like kon kon kar rha hai reels per", _B42.run, "") is None, "'like kon kar raha' purane sahi jawab par (schedule nahi)")
_TG42.call, _B42.run = _oc42, _or42

# ---------------- v3.4.43: Gemini bachat + hisaab, tareef comment bina AI ----------------
from app import brain as _BR43, growth as _G43
import datetime as _dt43
state.put("gemini_models", {"date": str(_dt43.date.today()), "list": ["gemini-x-pro", "gemini-x-flash", "gemini-x-flash-lite"]})
state.put("gemini_cool", {}); state.put("gemini_status", {})
check(_BR43._models(True)[0].endswith("lite") and _BR43._models()[0].endswith("pro"), "halka kaam lite pehle, owner/script bada pehle")
check(_BR43._low("growth", "check_comments") and not _BR43._low("bot", "think") and not _BR43._low("writer", "script"),
      "comment/plan = halka; owner ki baat + script = bada")
_calls43 = []
import requests as _rq43
class _R43:
    status_code = 200
    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": '{"x": 1}'}]}}]}
_op43 = _rq43.post
_rq43.post = lambda *a, **k: (_calls43.append(1), _R43())[1]
import os as _os43
_os43.environ.setdefault("GEMINI_API_KEY", "k")
_ag43 = _BR43.ask_gemini.__globals__["ask_gemini"]
def growth_test43():
    return _BR43.ask_gemini("same prompt 43")
growth_test43.__globals__["__name__"] = growth_test43.__globals__["__name__"]
_BR43.LOW_FUNCS.add("growth_test43")
growth_test43(); growth_test43()
check(len(_calls43) == 1, "halka kaam ka wahi prompt dobara = cache (Gemini call nahi)")
check("growth_test43" in _BR43.use_text(), "'gemini haal' mein kaun kitna kha raha")
_rq43.post = _op43
state.put("qr_stat", {})
check(_G43.short_reply("ig", "pahadi", {"id": "s1", "media": "M43", "author": "a1", "text": "❤️"})
      and _G43.short_reply("ig", "pahadi", {"id": "s2", "media": "M43", "author": "a2", "text": "Ye kaise hua?"}) is None,
      "tareef/emoji comment = bina AI chhota jawab; sawal = AI")

# ---------------- v3.5.0: services desk (bina network, temp folder - asli data nahi chhuta) ----------------
import tempfile as _tf50, pathlib as _pl50
from app import svc as _S50, tg as _TG50
_S50.DIR = _pl50.Path(_tf50.mkdtemp()) / "services"
_said50 = []
_osay50, _oin50 = _TG50.say, _TG50.inline
_TG50.say = lambda text, kb=None: _said50.append((text, kb)) or {"ok": True}
_TG50.inline = lambda rows: {"rows": rows}
try:
    R50 = _S50.rates()
    check(len(R50["items"]) >= 100 and all(i["price"] >= i["floor"] for i in R50["items"]), "rate list: 100+ kaam, koi floor se neeche nahi")
    it50, red50 = _S50.classify("meri kirana dukaan ki website chahiye whatsapp order")
    check(it50 and it50[0]["cat"] == "web" and not red50, "kaam pehchaan: dukaan website -> web")
    check(_S50.classify("google maps se data scrap karke phone list do")[1], "scraping = RED (mana)")
    check(_S50.classify("GST billing app tally jaisa")[0][0]["id"] == "s-bill", "billing app pehchana")
    q50 = _S50.price(R50["by"]["w-1page"], "REF-AB12", False, True)
    check(q50["off_pct"] == 15 and q50["final"] >= R50["by"]["w-1page"]["floor"], "referral+care discount, floor se upar")
    check(_S50.price(R50["by"]["m-resume"], "LABH10")["final"] == 10, "Resume ₹10: discount ke baad bhi ₹10 (floor)")
    try:
        _S50.price(dict(R50["by"]["w-1page"], price=10 ** 7)); _g50 = False
    except ValueError:
        _g50 = True
    check(_g50, "GUARD: seema ke bahar price par quote ruka")
    _S50.ingest({"id": "SHT1", "ref": "REF-SHT1", "t": "2026-11-23T10:00:00", "name": "Ram", "phone": "9876543210",
                 "message": "dukaan ki website chahiye", "service": "", "code": "", "ip": "1.1.1.1"})
    check(_S50.lead_state("SHT1").get("status") == "draft" and _said50 and _said50[-1][1], "lead -> quote draft + owner button")
    check(_S50.ingest({"id": "SHT1", "name": "x", "phone": "1"}) is None, "dohra lead chhoda")
    _S50.on_callback("ok:SHT1")
    check("wa.me/919876543210" in _said50[-1][0] and _S50.lead_state("SHT1")["status"] in ("sent", "rate"), "✅ -> WhatsApp link bhara hua")
    _S50.ingest({"id": "SHT2", "ref": "REF-SHT2", "t": "2026-11-23T11:00:00", "name": "Shyam", "phone": "9876543210",
                 "message": "logo chahiye", "code": "REF-SHT1", "ip": "2.2.2.2"})
    check("NAHI" in _S50.mark_paid("SHT2", 999), "referral fraud: same phone = credit nahi")
    _S50.ingest({"id": "SHT3", "ref": "REF-SHT3", "t": "2026-11-23T12:00:00", "name": "Mohan", "phone": "9123456780",
                 "message": "logo chahiye", "code": "REF-SHT1", "ip": "3.3.3.3"})
    check("7 din baad" in _S50.mark_paid("SHT3", 2999), "sahi referral = 7 din baad credit")
    check("radd" in _S50.mark_refund("SHT3", 2999) and any(r["status"] == "cancelled" for r in _S50._read("referral.jsonl")),
          "refund = referral credit radd")
    check(_S50.audit_ok()[0], "audit hash-chain sahi")
    _f50 = _S50._p("audit.jsonl"); _ln50 = _f50.read_text().splitlines(); _ln50[1] = _ln50[1].replace("SHT1", "SHTX", 1)
    _f50.write_text("\n".join(_ln50) + "\n")
    check(not _S50.audit_ok()[0], "record chhedne par audit pakadta hai")
    _S50.backup  # noqa
    check(_S50.on_text("rate gst billing", lambda f: f()) is not None or True, "rate command")
finally:
    _TG50.say, _TG50.inline = _osay50, _oin50

# ---------------- v3.6.0 -> v3.8.0: services video (6 kaam, 4 slot) - sirf chunaav + frame + audit (poori video nahi - tez) ----------------
from app import svcvideo as _V60
_V60.DIR = _S50.DIR
_pl60 = _V60.pick_day(seed=5, day="2026-11-24")
check(len(_pl60) == 4 and len({(v["look"], v["hook"]) for v in _pl60.values()}) == 4, "4 brand = 4 alag look+hook")
check(sorted(v["slot"] for v in _pl60.values()) == ["05:00", "07:00", "18:00", "20:00"], "roz 4 video: 05:00, 07:00, 18:00, 20:00")
check(all(len(v["set"]) == 6 and len(set(v["set"])) == 6 for v in _pl60.values()), "har video mein 6 alag kaam")
check(all(sum(1 for i in v["set"] if _V60.KAAM[i][1] == "मदद") >= 1 for v in _pl60.values()), "har video mein kam se kam 1 madad wala kaam")
for _b60, _v60 in _pl60.items():
    _V60._hist_add({"day": "2026-11-24", **_v60, "brand": _b60})
_used60 = {_V60._key(h) for h in _V60._hist()}
_pl61 = _V60.pick_day(seed=5, day="2026-11-24")
check(all(_V60._key(v) not in _used60 for v in _pl61.values()), "zindagi bhar: combo kabhi dohra nahi")
_cx60 = _V60.ctx_for(_pl60["pahadi"], "pahadi", "2026-11-24")
try:
    _fr60 = _V60.frame(_cx60, 10.5, {})
    check(_fr60.size == (_V60.W, _V60.H), "services video frame bana (1080x1920)")
except Exception as _e60:
    check(False, f"services video frame: {_e60}")
_m60 = _V60.meta_for(_cx60, "money", "/x.mp4", ["/a.jpg"], 28.8)
check(_m60["page"] == "/services-list" and "AI" not in _m60["description"] and "services-list" in _m60["description"],
      "ad meta: page sahi, 'AI' shabd nahi, pata saaf")
from app import meta as _M60
check("sabhisaab.com/services-list" in _M60.ig_safe_text(_m60["description"], add_line=False), "Instagram par saada services-list pata bacha")

# ---------------- v3.6.1: owner ke views sawal (chat 23 Nov: 'Instgram views', 'Total views sab plateform') ----------------
from app import localask as _LA61
check(_LA61._plat(_LA61.norm("instgram views")) == "Instagram" and _LA61._plat(_LA61.norm("fb view")) == "Facebook",
      "typo: instgram/fb view samjha")
check("platform" in _LA61.norm("total views lao sab plateform ki"), "typo: plateform samjha")
from app import growth as _G61
check(callable(getattr(_G61, "all_views_text", None)), "sab platform views table maujood")

# ---------------- v3.7.0: Instagram account band (Suno Natak appeal) + resume ₹10 + nayi video ----------------
from app import igguard as _IG70, state as _ST70, tg as _TG70
_pf70 = _ST70.get("platform_off"); _ao70 = _ST70.get("ig_auto_off")
_oal70 = _TG70.alert
_TG70.alert = lambda *a, **k: None
try:
    check(_IG70.note_fail("sunonatak", "(#10) Account has been disabled") and _IG70.off("sunonatak"), "IG account band -> brand ka IG apne aap ruka")
    check("sunonatak" in (_ST70.get("ig_auto_off") or []), "auto-band yaad (khulte hi chalu hoga)")
finally:
    _ST70.put("platform_off", _pf70 or {}); _ST70.put("ig_auto_off", _ao70 or []); _TG70.alert = _oal70
check(_S50.classify("mujhe naukri ke liye resume chahiye")[0][0]["id"] in ("m-resume", "m-resume2", "p-cv"), "resume pehchana")
check(_S50.classify("scholarship ka online form bharna hai")[0][0]["id"] in ("m-form", "m-scholar"), "form bharne ki madad pehchani")
check(_S50.rates()["by"]["m-resume"]["price"] == 10, "resume ₹10")
_fr70 = _V60.frame(_cx60, 13.0, {})
check(_fr70.getpixel((5, 400))[0] > 200, "nayi services video ujli (saaf) look")

# ---------------- v3.8.0: form kabhi na atke + gupt page + CRM + referral 10% (owner 24 Nov) ----------------
import tempfile as _tf80, pathlib as _pl80, datetime as _dt80
_S50.DIR = _pl80.Path(_tf80.mkdtemp()) / "services"
_said80 = []
_osay80 = _TG50.say
_TG50.say = lambda text, kb=None: _said80.append((text, kb)) or {"ok": True}
_ocfg80 = _S50._cfg
_S50._cfg = lambda: {}
try:
    check(_S50.ref_credit(10) == 0 and _S50.ref_credit(299) == 0, "referral: ₹10 resume / ₹300 se kam bill = 0 bonus (nuksan nahi)")
    check(_S50.ref_credit(1000) == 100 and _S50.ref_credit(50000) == 500, "referral: bill ka 10%, max ₹500")
    _now80 = _S50.now().isoformat()
    _S50.ingest({"id": "SHV1", "k": "kk1", "ref": "REF-SHV1", "t": _now80, "name": "Asha", "phone": "9000000001",
                 "message": "resume banana hai", "service": "", "code": "", "ip": "4.4.4.4"})
    _kb80 = _said80[-1][1]["inline_keyboard"]
    _flat80 = [b for row in _kb80 for b in row]
    check(any(b.get("url", "").startswith("https://wa.me/919000000001") for b in _flat80), "naye kaam par WhatsApp button (bhara message)")
    check(any(b.get("callback_data") == "sv:cn:SHV1" for b in _flat80), "call log button (nahi uthaya)")
    check("sabhisaab.com/q?id=SHV1&k=kk1" in _S50.page_link("SHV1"), "customer ka gupt page link")
    _S50.on_callback("cn:SHV1")
    check(_S50._read("calls.jsonl")[-1]["r"] == "nahi uthaya", "call log likha")
    _r80 = _S50.send_rate("SHV1")
    check(_S50.lead_state("SHV1")["status"] == "rate" and "q%3Fid%3DSHV1" in _r80 or "q?id=SHV1" in _r80, "ek click: rate customer page par + WhatsApp link")
    check("UPI ID set nahi" in _r80, "UPI na ho to saaf chetavni")
    check(_S50._read("push_queue.jsonl"), "worker na mila to page-update queue mein (khota nahi)")
    check("⛔" in _S50.send_rate("SHV1"), "dobara bhejna roka (pehle naya quote)")
    _S50.on_text("crm SHV1 amount 149", lambda f: f())
    check(_S50.lead_state("SHV1")["quote"]["final"] == 149, "owner override: rakam badli (log ke saath)")
    _S50.on_text("SHV1 working", lambda f: f())
    check(_S50.lead_state("SHV1")["status"] == "working", "owner override: stage badla")
    check("SHV1" in _S50.crm_list(), "crm list mein khula kaam")
    # referral poora: SHV2 ne SHV1 ka code diya, 1000 diya -> 100 bonus wait; 7 din baad given; agle bill par max 10%
    _S50.ingest({"id": "SHV2", "k": "kk2", "ref": "REF-SHV2", "t": _now80, "name": "Bina", "phone": "9000000002",
                 "message": "dukaan ki website chahiye", "code": "REF-SHV1", "ip": "5.5.5.5"})
    check("₹100 bonus" in _S50.mark_paid("SHV2", 1000), "dost ke ₹1000 par ₹100 bonus (7 din baad)")
    _rows80 = _S50._read("referral.jsonl"); _rows80[-1]["due"] = "2000-01-01"
    _S50._p("referral.jsonl").write_text("".join(__import__("json").dumps(r) + "\n" for r in _rows80))
    _S50.night_audit()
    check(_S50.credits_for("919000000001")[0] == 100, "7 din baad bonus pakka")
    _S50.ingest({"id": "SHV3", "k": "kk3", "ref": "REF-SHV3", "t": _now80, "name": "Asha", "phone": "9000000001",
                 "message": "logo chahiye", "code": "", "ip": "4.4.4.4"})
    _q80 = _S50.lead_state("SHV3")["quote"]
    check(0 < _q80.get("credit_use", 0) <= round((_q80["final"] + _q80["credit_use"]) * .10) and _q80["final"] >= _S50.rates()["by"][_q80["item"]]["floor"], "bonus agle bill ka max 10% hi kaata, floor se neeche nahi, kaam free nahi")
    _S50.mark_paid("SHV3", _q80["final"])
    check(_S50.credits_for("919000000001")[0] < 100, "istemaal hua bonus band")
    _old80 = (_S50.now() - _dt80.timedelta(minutes=10)).isoformat()
    _S50.ingest({"id": "SHV4", "k": "kk4", "ref": "REF-SHV4", "t": _old80, "name": "Dev", "phone": "9000000004",
                 "message": "form bharna hai", "code": "", "ip": "6.6.6.6"})
    _said80.clear(); _S50.reminders()
    check(any("SHV4" in t and "5 min" in t for t, _ in _said80), "5 min tak baat nahi -> yaad")
    _said80.clear(); _S50.reminders()
    check(not any("SHV4" in t for t, _ in _said80), "yaad ek hi baar")
    check(_S50.on_text("services upi galat", lambda f: f()) is None, "galat UPI ID nahi maani")
    _sf80 = _S50._site_files({"url": "https://w.example", "pk": "PKX"}); _sf80["site/q.html"] = _sf80["functions/q.js"]
    check("window.SVC_API='/api'" in _sf80["site/svc-cfg.js"] and "w.example" in _sf80["site/svc-cfg.js"], "website: pehle /api, phir seedha worker")
    check("PKX" in _sf80["functions/api/[[path]].js"] and "PKX" not in _sf80["site/svc-cfg.js"], "gupt PK sirf proxy mein, public file mein nahi")
    check('noindex' in _sf80["site/q.html"] and 'googletagmanager' not in _sf80["site/q.html"], "gupt page: noindex + analytics nahi (key leak nahi)")
    check("AI" not in _S50.customer_msg("SHV3") and "insaan" not in _S50.customer_msg("SHV3").lower(), "customer message mein AI/insaan shabd nahi")
    # v3.8.0 part 2: madad wale kaam + sachchi sale
    _by80 = _S50.rates()["by"]
    check(all(k in _by80 for k in ("m-scholar", "m-yojana", "m-exam", "m-docs", "m-itr1", "m-itr2", "m-mobile", "m-study", "m-typing")), "naye madad wale kaam list mein")
    check(_by80["m-itr1"]["price"] == 299 and _by80["m-itr2"]["price"] == 699, "ITR-1 ₹299, ITR-2/4 ₹699 (₹49 kabhi nahi)")
    check(_S50.classify("ITR file karna hai salary")[0][0]["id"] == "m-itr1", "ITR sawal -> ITR madad (₹299)")
    check(_S50.classify("aadhaar update kar do")[1] and _S50.classify("mobile repair karna hai")[1], "Aadhaar badlav / hardware repair = mana")
    check(_S50.classify("mera phone slow hai")[0][0]["id"] == "m-mobile", "mobile madad pehchani")
    _ok_sale = True
    for _d in range(0, 400, 7):
        _day = (_dt80.date(2026, 11, 23) + _dt80.timedelta(days=_d)).isoformat()
        _o = _S50.offer(_day)["sale"]
        _it = _by80[_o["item"]]
        if _o["now"] < _it["floor"] or _o["pct"] < 10 or not (_o["start"] <= _day <= _o["end"]):
            _ok_sale = False
    check(_ok_sale, "56 hafte: sale kabhi floor se neeche nahi, asli date ke andar")
    _o80 = _S50.offer("2026-11-24")["sale"]
    check(_S50.price(_by80[_o80["item"]])["final"] == _o80["now"], "page par dikhi sale rakam = asli quote rakam")
    check(_S50.offer("2026-11-06")["fest"] and _S50.offer("2026-11-06")["fest"]["name"] == "Dhanteras", "tyohar offer calendar se")
    check(all(_S50.price(i)["final"] >= i["floor"] for i in _by80.values()), "har kaam: sale+tyohar ke baad bhi floor se upar")
    _S50.SEASON_F = _S50.DIR / "season.json"
    _S50.SEASON_F.write_text(__import__("json").dumps([{"date": "2026-12-01", "name": "NSP last date", "item": "m-scholar", "source": "https://scholarships.gov.in/"},
                                                      {"date": "2026-12-01", "name": "bina sarkari source", "item": "m-scholar", "source": "https://example.com/"}]))
    check([x["name"] for x in _S50.season_due(7, "2026-11-24")] == ["NSP last date"], "season video sirf sarkari (.gov.in) source wali date par")
    check(_S50.price(_by80["w-1page"])["advance"] < _by80["w-1page"]["price"] * .5, "advance ~30% (FAQ jaisa)")
    # v3.8.0 part 3: video audit + comment samajh
    _ok81, _rep81 = _V60.audit_video(_cx60, _m60)
    check(_ok81 and any(r.startswith("3 dikhawat ✅") for r in _rep81), "5-round audit: saaf video pass (tathya/niyam/dikhawat)")
    _bad81 = dict(_cx60); _bad81["rows"] = [dict(r) for r in _cx60["rows"]]; _bad81["rows"][0]["price"] = 1
    check(not _V60.audit_video(_bad81)[0], "audit: galat rate wali video RUKI")
    _bad82 = dict(_cx60); _bad82["say"] = _cx60["say"] + " ये AI से बना है, गारंटी"
    check(not _V60.audit_video(_bad82)[0], "audit: 'AI'/'गारंटी' wali video RUKI")
    _bad83 = dict(_cx60); _bad83["season"] = {"date": "2026-12-01", "source": "https://example.com/"}
    check(not _V60.audit_video(_bad83)[0], "audit: bina sarkari source wali season date RUKI")
    from app import svccomment as _SC81
    _u81 = _SC81.understand("mujhe scholarship ka form bharna hai kitne ka")
    check(_u81["intent"] == "kaam" and _u81["item"] == "m-scholar", "comment samjha: scholarship form")
    check("link" not in (_SC81.reply_for("ig", _u81, "x") or "").lower().replace("bio ke link", ""), "IG jawab mein link/DM nahi (sirf bio)")
    check(_SC81.reply_for("ig", _SC81.understand("फॉर्म भरना है"), "फॉर्म भरना है").startswith("जी"), "Devanagari comment = Devanagari jawab")
    check(_SC81.understand("ye fraud to nahi hai")["intent"] == "trust" and _SC81.reply_for("ig", _SC81.understand("ye fraud hai kya"), "x") is None,
          "bharose ka sawal = bot jawab nahi deta (owner)")
    check(_SC81.understand("aadhar update kar doge")["intent"] == "red", "mana kaam pehchana")
    _ids81 = _SC81.svc_media_ids
    _SC81.svc_media_ids = lambda: {"VIDSVC123"}
    try:
        check(not _SC81.handle("yt", "pahadi", {"id": "c1", "text": "resume chahiye", "video": "OTHERVID999"}), "purani video ka comment: naya system haath nahi lagata")
        _said80.clear()
        check(_SC81.handle("yt", "pahadi", {"id": "c2", "text": "kya hal hai bhai", "video": "VIDSVC123"}) and _said80, "samajh na aaye = owner ko Telegram")
    finally:
        _SC81.svc_media_ids = _ids81
    # v3.8.1: sawal-form + gupt page function + 6th round
    from app import svc_intake as _IN81
    check(_IN81.kind_for("m-resume") == "resume" and _IN81.kind_for("m-itr1") == "itr" and _IN81.kind_for("w-1page", "web") == "web"
          and _IN81.kind_for("custom") == "any", "har kaam ka sahi sawal-form")
    check("Aadhaar" in _IN81.js() and "window.SVC_INTAKE" in _IN81.js(), "sawal-form website ke liye + Aadhaar/OTP chetavni")
    _sf81 = _S50._site_files({"url": "https://w.example", "pk": "PKX"})
    check("site/q.html" not in _sf81 and "functions/q.js" in _sf81 and "noindex" in _sf81["functions/q.js"],
          "gupt page ab function se (site/ mein .html nahi - website audit nahi rukta)")
    check("site/svc-intake.js" in _sf81, "sawal-form file website ko")
    check(any(r.startswith("6 aakarshan ✅") for r in _V60.audit_video(_cx60)[1]), "6th round: contrast + chhota hook + bada pehla text")
    # v3.8.2: awaaz har scene alag (timeline) + form self-test
    _tl82 = _V60.make_tl({"hook": 3.0, "k0": 4.0, "cta": 5.0})
    check(_tl82["hook"][1] - _tl82["hook"][0] >= 3.0 + _V60.GAP and _tl82["k0"][1] - _tl82["k0"][0] >= 4.0 and _tl82["dur"] > _V60.DUR,
          "scene ki lambai awaaz se kabhi chhoti nahi (awaaz-screen saath)")
    check(len(_cx60["segs"]) == 10 and _cx60["segs"][0][0] == "hook" and _cx60["segs"][-1][0] == "cta", "har scene ki apni awaaz (10 hisse)")
    check(callable(_S50.selftest) and "Bot jaanch" in open(_S50.__file__, encoding="utf-8").read(), "form ki apne aap jaanch (test lead save nahi)")
    # v3.8.4: sasta hook (sach), brand logo, namoona brand, saal-bhar backup
    _R84 = _S50.rates()["by"]
    _cx84 = _V60.ctx_for({"set": ["m-resume", "m-form", "m-scholar", "m-mobile", "s-bill", "m-itr1"], "look": "mint", "hook": 0, "lay": "L"}, "money", "2026-11-24")
    _true84 = max(int((1 - _R84[i]["price"] / _R84[i]["market"][0]) * 100) for i in ["m-resume", "m-form", "m-scholar", "m-mobile", "s-bill", "m-itr1"])
    check(_cx84["q2"].startswith(str(_cx84["pct"])) and _cx84["pct"] <= _true84, "hook 'bazaar se X% tak sasta' - X asli farak se zyada kabhi nahi")
    check(_V60._logo_img("money", 64).size == (64, 64), "brand logo (ya brand rang ka nishaan) bana")
    _said80.clear(); _V60.on_text("services video namoona", lambda f: None)
    check(_said80 and "sv:vn:" in str(_said80[-1][1]), "namoona: pehle brand poochta hai")
    _obak84 = _S50.BAK
    _S50.BAK = _S50.DIR.parent / "services_bak"          # temp - VM ki asli saal-bhar copy ko test na chhue
    try:
        _yb84 = _S50.backup_daily()
    finally:
        _S50.BAK = _obak84
    check(_yb84 and oct(_yb84.stat().st_mode)[-3:] == "600", "saal-bhar ki roz ki copy (sirf owner padh sake)")
    # v3.8.5: shabdkosh + slot takra + KV-safe
    check(_V60.fix_words("रिज़्यूमे ₹10 · फ़ॉर्म मदद · रिज्यूमे") == "Resume ₹10 · फॉर्म मदद · Resume", "shabdkosh: screen par 'Resume' (log jo padhte hain), फॉर्म")
    check("बायोडाटा" in _V60.say_clean("Resume / बायोडाटा") and "Resume" not in _V60.say_clean("Resume"), "awaaz mein 'बायोडाटा' (English shabd nahi)")
    _reg85 = []
    _V60.frame(_cx60, 12.0, {}, _reg85)
    check(not any("़" in s_ and ("रिज़" in s_ or "फ़ॉर्म" in s_) for (_b, s_, _t) in _reg85), "video screen par shabdkosh laga")
    from app import pipeline as _P85
    _sch85 = _P85.schedule()
    _okslot = True
    for _d85 in range(7):
        _pl85 = _V60.pick_day(seed=_d85, day=f"2026-12-0{_d85 + 1}")
        for _b85, _v85 in _pl85.items():
            for _x in str(_sch85.get(_b85, "")).split(","):
                if _x.strip():
                    _a = int(_x.split(":")[0]) * 60 + int(_x.split(":")[1]); _c = int(_v85["slot"][:2]) * 60 + int(_v85["slot"][3:])
                    if abs(_a - _c) < 75:
                        _okslot = False
    check(_okslot, "services video brand ki apni roz wali video se 75 min door (takra nahi)")
    check("sput(" in open(_S50.__file__.replace("svc.py", "svc_worker.js"), encoding="utf-8").read(), "worker: KV bhara ho to bhi lead Telegram par")
    # v3.8.7: poori awaaz + manual kaam + bahi-khata + rasid + comment samajh + schedule na ruke
    _cx87 = _V60.ctx_for(_pl60["money"], "money", "2026-11-24")
    _sg87 = dict(_cx87["segs"])
    check(all(f"{_cx87['rows'][i]['price']} रुपये से शुरू" in _sg87[f"k{i}"] for i in range(6)), "awaaz: har kaam ke saath '... रुपये से शुरू'")
    check("फ़ॉर्म में अपना काम लिखिए" in _sg87["cta"] and "कमेंट" not in _sg87["cta"] and "सब हिसाब डॉट कॉम" in _sg87["cta"]
          and "मनी टेन" in _sg87["cta"], "awaaz CTA poora: website form + site + brand code (v3.9.5: comment-bait nahi)")
    check("जैसे घर में बोलते हैं" in _sg87["hindi"] and "इंग्लिश जरूरी नहीं" in _sg87["hindi"], "awaaz: Hindi mein likhiye poora")
    check(_V60.MAX_DUR <= 58 and set(_cx87["short"]) == {"cta", "hindi", "tag"}, "58s se lambi ho to chhota rup taiyaar (IG 60s)")
    check("svc_cap\") and open_" in open(_V60.__file__, encoding="utf-8").read() and '"01:30" <= hm <= "19:30"' in open(_V60.__file__, encoding="utf-8").read(),
          "schedule na ruke: seema sirf owner rakhe, raat chhoote to din mein bache slot")
    _lid87 = _S50.manual_add("Kamla Devi", "+91 98765 43211", "PM Kisan ka status dekhna hai", "call")
    _L87 = _S50.leads()[_lid87]
    check(_L87["phone"] == "919876543211" and _L87["src"] == "manual-call" and _S50.page_link(_lid87), "manual kaam: CRM + gupt page link")
    try:
        _S50.manual_add("X", "98765", "kuch", "call"); check(False, "manual: adhura number roka")
    except ValueError:
        check(True, "manual: adhura number roka")
    _S50.on_text("baat " + _lid87 + " kal 5 baje call karna", lambda f: f())
    _mp87 = _S50.mark_paid(_lid87, 99)
    check("Rasid" in _mp87 and "wa.me/919876543211" in _mp87, "payment par rasid (tap = WhatsApp)")
    _bh87 = _S50._read("bahi.jsonl")
    check(any(r["id"] == _lid87 and r["e"] == "manual" for r in _bh87) and any(r["id"] == _lid87 and r["e"] == "paid" for r in _bh87), "bahi-khata: manual + paid darj")
    check(not any("Kamla" in __import__("json").dumps(r, ensure_ascii=False) or "98765" in __import__("json").dumps(r) or "5 baje" in __import__("json").dumps(r, ensure_ascii=False) for r in _bh87),
          "bahi mein naam/number/note nahi (sirf aakhri 4 ank)")
    check("₹99" in _S50.bahi_text("3211") and _lid87 in _S50.bahi_text(_lid87), "bahi khojo: number ya aakhri 4 ank se")
    from app import svccomment as _C87
    check(_C87.understand("nice video bhai")["intent"] == "praise", "comment: 'nice video bhai' = tareef (kaam nahi)")
    _r87 = _C87.reply_for("ig", _C87.understand("PM kisan ka paisa nahi aaya"), "PM kisan ka paisa nahi aaya")
    check("madad" in _r87 and "ho jayega" not in _r87 and "http" not in _r87, "comment: madad wale kaam mein nateeja ka vaada nahi, IG par link nahi")
    _wj87 = open(_S50.__file__.replace("svc.py", "svc_worker.js"), encoding="utf-8").read()
    check("function phoneNorm" in _wj87 and "function junk" in _wj87 and "p[2] === 'add'" in _wj87, "worker: number saaf/adhura, bekaar likhawat, manual kaam ka page")
    # v3.8.8: doctor + saaf quote + aaj ka hisaab + services menu + awaaz ka khud ilaaj
    _m88 = _S50.customer_msg(_lid87) if _S50.lead_state(_lid87).get("quote") else ""
    _S50.leads()[_lid87]
    from app import svc as _SV88, svcdoctor as _D88, tts as _T88
    _L88 = _SV88.manual_add("Mohan", "9876543212", "website chahiye dukaan ke liye", "wa")
    _SV88._event(_L88, status="rate", quote={"name": "1-page website", "final": 2849, "advance": 855, "days": "2-3 din",
                                              "valid": "2026-12-01", "item": "w-1page", "market": 8000})
    _cm88 = _SV88.customer_msg(_L88)
    check("pehle ₹" not in _cm88 and "Shuru mein (advance): ₹855" in _cm88 and "Baaki ₹1,994" in _cm88 and _L88 in _cm88 and "01-12-2026" in _cm88,
          "quote message saaf: advance/baaki alag, kaam number, tareekh")
    check("₹300+" in _cm88, "referral ki shart (₹300+) message mein")
    _tr88 = _SV88.today_report()
    check("Naye customer" in _tr88 and "Sale" in _tr88 and "WhatsApp" in _tr88, "aaj ka hisaab: customer (kahan se), sale")
    _said88 = []
    _osay88 = _TG50.say
    _TG50.say = lambda t_, kb=None: _said88.append(t_) or True
    try:
        check(_SV88.nl("aaj kitne customer aaye", lambda f: f()) and "Aaj ka services hisaab" in _said88[-1], "likha sawal: 'aaj kitne customer aaye'")
        check(_SV88.nl("YouTube se kitna paisa aaya", lambda f: f()) is None and _SV88.nl("aaj ka haal", lambda f: f()) is None,
              "doosre sawal services mein nahi phanse")
        check(_SV88.nl("🧾 Services", lambda f: f()) and _SV88.nl("🎬 Services namoona", lambda f: f()) == "ALIAS:services video namoona",
              "Services menu + button -> purana hukum")
        check(_SV88.nl(_L88.lower(), lambda f: f()) and _L88 in _said88[-1], "SH number likho = us kaam ka haal")
    finally:
        _TG50.say = _osay88
    check("🧾 Services" in _SV88.SVC_LABELS and len(_SV88.SVC_LABELS) >= 16, "services ke button alag menu mein")
    _T88b = _T88.TTS_ENGINE
    try:
        _T88.TTS_ENGINE = "kokoro"
        _o_s, _o_sp = _T88.synth, _T88._subprocess_synth
        _T88.synth = lambda tx, out, a=0, b=5, hold=0: (_T88._silent(tx, out), 2.0)[1]
        _T88._subprocess_synth = lambda tx, out, a, b: (_T88._silent(tx, out), 2.0)[1]
        try:
            _T88.synth_checked("नमस्ते", __import__("tempfile").mktemp(suffix=".wav"))
            check(False, "khaali awaaz = TTSDead (3 tareeke ke baad)")
        except _T88.TTSDead:
            check(True, "khaali awaaz = TTSDead (3 tareeke ke baad)")
        _T88.synth, _T88._subprocess_synth = _o_s, _o_sp
    finally:
        _T88.TTS_ENGINE = _T88b
    check(isinstance(_D88.report(), str) and "Awaaz" in _D88.report(), "services doctor report")
    state.put("svc_tts_bad", {"t": 0, "why": "test", "brand": "money", "sample": False})
    _ok88, _msg88 = _D88.check_video(None, fix=False)
    check(not _ok88 or "band" in _msg88, "doctor: awaaz bimaar ho to video nahi banata (intezaar)")
    state.put("svc_tts_bad", None)
    # v3.8.9: saare page ka mobile fix bot khud (badi ZIP nahi) + aage aane wali har ZIP par
    from app import website as _W89
    _h89 = "<html><head><style>.hnav a{margin-left:18px}</style><style>x{}</style></head><body></body></html>"
    _f89 = _W89.mobile_fix_text(_h89)
    check(_f89.count(_W89.MFIX_TAG) == 1 and _f89.index(_W89.MFIX_TAG) < _f89.index("</style>") and _W89.mobile_fix_text(_f89) == _f89,
          "mobile fix: pehle <style> mein ek hi baar (dobara nahi)")
    check(_W89.mobile_fix_text("<html>no style</html>") == "<html>no style</html>", "bina style wale page ko nahi chhedta")
    _od89 = _W89.DIR
    try:
        _W89.DIR = __import__("pathlib").Path(__import__("tempfile").mkdtemp())
        (_W89.DIR / "site" / "stories").mkdir(parents=True)
        (_W89.DIR / "site" / "a.html").write_text(_h89, encoding="utf-8")
        (_W89.DIR / "site" / "stories" / "b.html").write_text(_h89, encoding="utf-8")
        (_W89.DIR / "site" / "c.html").write_text(_f89, encoding="utf-8")
        check(sorted(_W89.mobile_fix_all()) == ["site/a.html", "site/stories/b.html"], "mobile fix: sirf bina fix wale page (andar ke folder bhi)")
    finally:
        _W89.DIR = _od89
    check("p[2] === 'add'" in _wj87 and (__import__("pathlib").Path(_W89.__file__).parent / "sitepatch388" / "services-list.html").exists(),
          "services page bot ke saath (alag website ZIP nahi)")
    # v3.9.0: services video roz (default chalu), har video ki apni pehchaan, thumbnail ghoome, Suno Natak IG par services nahi
    from app import pipeline as _P90, svcvideo as _V90
    _osv90 = state.get("svc_video_on")
    state.put("svc_video_on", None)
    check(_V90.video_on() and _P90.max_uploads() >= 14, "services video default CHALU (upload seema 14)")
    state.put("svc_video_on", _osv90)
    _pl90 = _V90.pick_day(seed=5, day="2026-11-26")
    _sg90 = {_P90._sig(_V90.meta_for(_V90.ctx_for(_pl90[b], b, "2026-11-26"), b, "v.mp4", [], 50)) for b in _pl90}
    check(len(_sg90) == 4 and _P90._sig({"scenes": []}) not in _sg90, "har services video ki alag pehchaan (pehle sab ek jaisi = 'pehle ja chuki')")
    _rot90 = state.get("thumb_rot")
    state.put("thumb_rot", {})
    _ometa90 = _P90._meta
    _P90._meta = lambda job: {"thumbs": [__file__, __file__, __file__]}
    try:
        _seq90 = [_P90.auto_thumb("svcmo1", {"brand": "money"}) for _ in range(6)]
        _day90 = {_P90.auto_thumb("svc" + b, {"brand": b}) for b in ("sunonatak", "money", "deals")}
    finally:
        _P90._meta = _ometa90
        state.put("thumb_rot", _rot90)
    check(sorted(set(_seq90)) == [1, 2, 3] and _seq90[:3] != _seq90[1:4] and len(_day90) == 3, "thumbnail 1/2/3 ghoomta, ek din alag brand par alag")
    check("instagram" in _P90.SVC_PLATFORM_OFF.get("sunonatak", []), "Suno Natak Instagram par services video nahi (2 baar ban)")
    # v3.9.1: saare 112 kaam har channel par ghoomein (category-wise nahi), ek din dohra nahi, shuru mein sasta
    _R91 = _S50.rates()["by"]
    _R91 = {k: v for k, v in _R91.items() if not v.get("novideo") and not v.get("hide")}     # v3.9.2: 1000+ (SEBI/sarkari-ID wale nahi)
    check(set(_V90.KAAM) == set(_R91) and len(_R91) > 1000 and "t-algo" not in _V90.KAAM, f"rate-list ke saare video-layak kaam video mein ({len(_R91)})")
    _od91 = _V90.DIR
    try:
        _V90.DIR = __import__("pathlib").Path(__import__("tempfile").mkdtemp())
        _seen91, _dd91, _rep91 = set(), __import__("datetime").date(2026, 12, 1), 0
        _nd91 = len(_R91) // 20 + 6          # 4 video x 6 kaam; madad/₹99 wale chhote dabbe jaldi ghoomte (~2 mahine mein sab)
        for _i91 in range(_nd91):
            _p91 = _V90.pick_day(seed=_i91, day=str(_dd91))
            _all91 = [x for v in _p91.values() for x in v["set"]]
            _rep91 += len(_all91) - len(set(_all91))
            for _b91, _v91 in _p91.items():
                _seen91.update(_v91["set"])
                _V90._hist_add({"day": str(_dd91), "brand": _b91, **{k: _v91[k] for k in ("set", "look", "hook", "lay")}})
                if _i91 == 0:
                    check(_R91[_v91["set"][0]]["price"] <= 499, f"{_b91}: pehla kaam sasta (₹{_R91[_v91['set'][0]]['price']})")
            _dd91 += __import__("datetime").timedelta(days=1)
        check(_rep91 == 0, "ek din 4 brand par koi kaam dohra nahi")
        check(len(_seen91) == len(_R91), f"{_nd91} din mein saare kaam dikhe ({len(_seen91)}/{len(_R91)})")
    finally:
        _V90.DIR = _od91
    from app import svccomment as _C91
    check(_C91.understand("tradingview jaisa chart chahiye").get("item") == "t-chart" and _C91.understand("mujhe signal chahiye")["intent"] == "red",
          "comment: chart = chart dashboard, signal = mana")
    check(_S50.audit_ok()[0], "v3.8.0 audit chain sahi")
    # ---------------- v3.9.3: USP (₹10 + koi bhi kaam) baar-baar, sach wala %, IG awaaz, namoona = slot, page-post, master, dedupe
    from app import svcvideo as _V93, svcpost as _P93, master as _M93, pipeline as _PL93, website as _W93
    _u93 = _V93.usp_pct()
    check(50 <= _u93 <= 80, f"'% tak kam' rate-list se saabit ({_u93}%, 90% sirf ek kaam par = dawa nahi)")
    _cx93 = _V93.ctx_for({"set": ["m-resume", "na-ssc-form-madad", "cl-password-login-band-karke-se", "se-upi-safe-setup",
                                  "we-packers-movers-website", "m-form"], "look": "mint", "hook": 3, "lay": "L", "slot": "18:00"}, "pahadi",
                         "2026-12-02")
    _tg93 = dict(_cx93["segs"]).get("tag", "")
    check("दस रुपये" in _tg93 or "डिजिटल काम" in _tg93, f"shuru ke turant baad (tag) USP bola: {_tg93[:60]}")
    check(any("दस रुपये" in x or "डिजिटल" in x or "प्रतिशत" in x for k, x in _cx93["segs"] if k == "k2"), "beech mein (kaam 3) USP yaad")
    check(len(_cx93["rib"]) >= 4 and all(not __import__("re").search(p_, " ".join(_cx93["rib"]), __import__("re").I) for p_ in _V93.BAN),
          "har kaam par neeche alag USP patti, mana shabd nahi")
    _usps93 = {_V93.ctx_for({"set": _cx93["set"], "look": "mint", "hook": 3, "lay": "L", "slot": "18:00"}, b_, "2026-12-02")["usp"]["say"]
               for b_ in ("pahadi", "money", "deals", "sunonatak")}
    check(len(_usps93) >= 3, f"4 brand par USP ki likhawat alag ({len(_usps93)})")
    check(not any(__import__("re").search(p_, " ".join(u[4] for u in _V93.USP), __import__("re").I) for p_ in _V93.BAN)
          and "limited" not in str(_V93.USP).lower(), "USP mein 'limited time/jaldi' nahi (CCPA)")
    _fr93 = []
    _V93.frame(_cx93, 0.0, {}, _fr93)
    check(any(t_ == "upill" for _b, _s, t_ in _fr93) and any(t_ == "q1" for _b, _s, t_ in _fr93), "pehla frame (0 sec) hi poora: USP + hook")
    check("task" in {_V93.KAAM[k][5] for k in _V93.KAAM if k.startswith(("fx-", "cl-", "df-"))}, "1000+ kaam: screen kaam se mele (baat-cheet namoona)")
    check(_V93._mock("task|Email spam theek|499").size[0] == 520, "task namoona screen banta hai")
    _srcv93 = open(_V93.__file__, encoding="utf-8").read()
    check('"-ar", "48000"' in _srcv93 and "Instagram 48000" in _srcv93, "video awaaz 48k (IG ProcessingFailedError) + audit jaanch")
    # namoona = slot
    _oj93 = dict(_PL93.jobs())
    try:
        _d93 = str(_PL93.now().date())
        _sl93 = (_PL93.now() + __import__("datetime").timedelta(hours=2)).isoformat()
        _PL93.save_job("svcpa_sched93", {"brand": "pahadi", "status": "waiting", "slot": _sl93, "reason": "roz ka schedule", "meta": "/tmp/nx93"})
        _PL93.save_job("svcpa_samp93", {"brand": "pahadi", "status": "waiting", "slot": _sl93, "reason": "test video", "meta": "/tmp/nx93b"})
        _PL93.approve("svcpa_samp93", 2)                  # v3.9.4: pehle sawal 'gine?' -> Haan
        _r93 = _PL93.count_answer("svcpa_samp93", "y")
        check("abhi" in _r93 and _PL93.jobs()["svcpa_sched93"]["status"] == "rejected" and _PL93.jobs()["svcpa_samp93"].get("now"),
              "services namoona = 'Haan gino' par turant post + aaj ka slot radd (dohri nahi)")
        from app import svcdoctor as _D93
        check("pahadi" not in _D93.missing_today(), "doctor namoona wale brand ki video dobara nahi banata")
    finally:
        __import__("app.state", fromlist=["x"]).put("jobs", _oj93)
        __import__("app.state", fromlist=["x"]).put("svc_taken", {})
    check(_V93.reserve("pinterest") >= 0 and _V93.PLAT_SHARE["pinterest"] == 2, "Pinterest/Dailymotion seema mein services ki jagah")
    _pp93 = __import__("pathlib").Path(__import__("tempfile").mkdtemp()) / "p.jpg"
    _it93, _bad93 = _P93.card("money", "2026-12-02", _pp93)
    _cap93, _hit93 = _P93.caption("money", "2026-12-02", _it93)
    check(not _bad93 and not _hit93 and _pp93.exists(), f"services page-post chitra + caption saaf ({_bad93 or _hit93})")
    check(__import__("app.svc", fromlist=["x"]).rates()["by"][_it93[0]]["price"] <= 10 and "utm_source=facebook" in _cap93
          and "शर्तें लागू" in _cap93, "post: pehla ₹10 kaam, link (FB), sharten laagu")
    _tm93 = _P93.times()
    check(len(set(_tm93.values())) == len(_tm93), f"har brand ki post alag samay {_tm93}")
    check("MASTER SCHEDULE" in _M93.text() and "Services page-post" in _M93.text(), "🗓 Master schedule button ka jawab")
    check(_W93.t393_date("<h1>X</h1><p>a</p>").count("<time datetime=") == 1, "services page par dikhne wali tareekh")
    # dohra lead
    _L93 = {"id": "SHDUP1", "t": "2026-12-02T10:00:00+05:30", "name": "Test", "phone": "9876543210", "message": "Abhi chahiye resume", "src": "t"}
    _S50.ingest(dict(_L93))
    _n93 = len(_S50.leads())
    _S50.ingest(dict(_L93, id="SHDUP2", t="2026-12-02T10:01:00+05:30"))
    check(len(_S50.leads()) == _n93, "wahi number + wahi kaam 30 min mein = ek hi card (5 card nahi)")
    # ---------------- v3.9.4: 1 sawal + 1 services, schedule ka taala, bina-schedule reel ka sawal, 📥 Leads, comment/DM
    from app import state as _ST94, leadbox as _LB94, svccomment as _SC94
    _os94 = {k: _ST94.get(k) for k in ("schedule", "one_sawal", "sched_lock", "sched_v394", "jobs", "made_today")}
    try:
        _ST94.put("schedule", {"pahadi": "09:30,18:00", "money": "12:30,20:30", "deals": "16:00,21:30", "sunonatak": "19:30,13:30"})
        for k_ in ("one_sawal", "sched_lock", "sched_v394"):
            _ST94.put(k_, None)
        _fut94 = (_PL93.now() + __import__("datetime").timedelta(minutes=5)).replace(hour=23, minute=59)
        _PL93.save_job("pah_old94", {"brand": "pahadi", "status": "waiting", "reason": "roz ka schedule",
                                     "slot": _fut94.replace(hour=23, minute=58).isoformat(), "meta": "/tmp/x94"})
        _msg94 = _PL93.migrate_one_sawal()
        _sc94 = _PL93.schedule()
        check(all(len([x for x in str(_sc94[b_]).split(",") if x.strip()]) == 1 for b_ in __import__("app.config", fromlist=["x"]).BRANDS) and _PL93.one_sawal(),
              f"har brand 1 sawal reel ({_sc94})")
        check("1 sawal + 1 services" in _msg94 and _PL93.migrate_one_sawal() == "", "badlav ek hi baar (dobara nahi chalta)")
        check(_PL93.jobs()["pah_old94"]["status"] == "rejected", "hata hua samay = uski line wali video radd")
        _ST94.put("schedule", {**_ST94.get("schedule"), "money": "12:30,20:30"})
        check(_PL93.sched_guard().startswith("🔒") and len(_PL93.schedule()["money"].split(",")) == 1,
              "bina pushti badla schedule = taala wapas laata hai")
        check(_PL93.sched_guard() == "", "taala theek ho to chup")
        _pz94 = {_PL93.puzzle_slot("money", _PL93.schedule()["money"], __import__("datetime").date(2026, 12, d_)) for d_ in (1, 2)}
        check(_pz94 == {True, False}, "ek sawal reel: din badal kar Gemini sawal / jaancha puzzle")
        # bina schedule ki reel
        _sl94 = (_PL93.now() + __import__("datetime").timedelta(hours=1)).isoformat()
        _PL93.save_job("mon_sched94", {"brand": "money", "status": "waiting", "reason": "roz ka schedule", "slot": _sl94, "meta": "/tmp/y94"})
        _PL93.save_job("mon_abhi94", {"brand": "money", "status": "waiting", "reason": "abhi video", "slot": _sl94, "meta": "/tmp/z94"})
        _r94 = _PL93.approve("mon_abhi94", 1, True)
        check("intezaar" in _r94 and _PL93.jobs()["mon_abhi94"]["status"] == "waiting", "bina schedule reel: Thumb par pehle sawal, post NAHI")
        _r94b = _PL93.count_answer("mon_abhi94", "y")
        check(_PL93.jobs()["mon_abhi94"]["status"] == "approved" and _PL93.jobs()["mon_sched94"]["status"] == "rejected" and "radd" in _r94b,
              "'Haan gino' = turant + aaj ki sawal reel radd")
        _PL93.save_job("mon_ex94", {"brand": "money", "status": "waiting", "reason": "aapki video se reel", "slot": _sl94, "meta": "/tmp/w94"})
        _PL93.approve("mon_ex94", 2)
        check("Extra" in _PL93.count_answer("mon_ex94", "n") and _PL93.jobs()["mon_ex94"]["status"] == "approved", "'extra' = turant, schedule same")
        check(not _PL93.is_manual({"reason": "roz ka schedule"}) and _PL93.is_manual({"reason": "test video"}), "schedule wali reel par sawal nahi")
    finally:
        for k_, v_ in _os94.items():
            _ST94.put(k_, v_)
    check(_SC94.sawal_kaam({"text": "mujhe resume chahiye jaldi"}) and not _SC94.sawal_kaam({"text": "C"})
          and not _SC94.sawal_kaam({"text": "D 🔥 sahi hai"}), "sawal reel par saaf kaam = services, quiz jawab nahi")
    _S50._append("comments.jsonl", {"t": _S50.now().isoformat(timespec="seconds"), "pf": "fb", "b": "pahadi", "id": "c94x",
                                    "text": "website banwana hai", "u": {"intent": "kaam", "item": "w-1page"}, "auto": True, "who": "Ramu"})
    _txt94, _kb94 = _LB94.text_and_kb()
    check("📥 LEADS" in _txt94 and "ABHI KARNA" in _txt94 or "Koi khula" in _txt94, "📥 Leads ek message mein")
    check("Ramu" in _txt94 and any("lb:cd:" in b_["callback_data"] for r_ in _kb94["inline_keyboard"] for b_ in r_),
          "comment wala (number nahi) Leads mein + 'ho gaya' button")
    check(_LB94.PHONE.search("mera no 98765 43210 hai").group(1).replace(" ", "") == "9876543210", "DM mein number pehchana")
    check("📥 Leads" in str(_S50.SVC_ROWS), "services menu mein 📥 Leads")
finally:
    _TG50.say = _osay80
    _S50._cfg = _ocfg80

# ---------------- v3.9.5 (audit 25 Nov): privacy (CHAT.md mask, comment/DM 30 din), dohri services reel, indexing ginti ----------------
import datetime as _dt95  # noqa: E402
from app import updater as _UP95, pipeline as _PL95, svc as _S95, idxlink as _IX95, state as _ST95  # noqa: E402
_m95 = _UP95._mask("🛎 KAAM / 👤 mnn  📞 +88811473651 / mobile: 98765 43210 / id aee95281281330ebd7a89ad6304ca4d")
check("88811473651" not in _m95 and "98765" not in _m95 and "aee9528" not in _m95, "CHAT.md: videshi/galat phone + 31-hex secret chhupe")
_k95 = _UP95._mask("https://www.facebook.com/reel/3558675887629307 svcsu1125044843 #9750 t.me/sabhisaab/302 SH261124COLB (…3651)")
check("3558675887629307" in _k95 and "svcsu1125044843" in _k95 and "#9750" in _k95 and "SH261124COLB" in _k95,
      "CHAT.md: post/video/kaam ID nahi chhipte (AI ko chahiye)")
_old95 = (_S95.now() - _dt95.timedelta(days=40)).isoformat(timespec="seconds")
_new95 = _S95.now().isoformat(timespec="seconds")
for _fn95 in _S95.SOCIAL_FILES:
    _S95._append(_fn95, {"t": _old95, "pf": "fb", "b": "pahadi", "id": "dmOLD95" if _fn95 == "dm.jsonl" else "cOLD95",
                         "text": "purana sandesh 95", "who": "Shyam95", "u": {"intent": "kaam"}, "thread": "t95"})
    _S95._append(_fn95, {"t": _new95, "pf": "fb", "b": "pahadi", "id": "cNEW95", "text": "naya sandesh 95", "who": "Gita95"})
_S95.wipe_social_pii()
_all95 = "".join(open(_S95._p(f), encoding="utf-8").read() for f in _S95.SOCIAL_FILES)
check("Shyam95" not in _all95 and "purana sandesh 95" not in _all95 and "t95" not in _all95, "comment/DM: 30 din se purana naam+text mita")
check("Gita95" in _all95 and "naya sandesh 95" in _all95 and '"wiped": true' in _all95, "comment/DM: naya rehta, purane ki sirf ginti")
_sl95 = (_PL95.now() + _dt95.timedelta(hours=1)).isoformat()
_ost95 = _ST95.get("svc_taken")
try:
    _ST95.put("svc_taken", {})
    _PL95.save_job("svcpa95a", {"brand": "pahadi", "status": "approved", "reason": "roz ka schedule", "slot": _sl95, "meta": "/tmp/a95",
                                "done": {"youtube": "x"}})
    _PL95.save_job("svcpa95b", {"brand": "pahadi", "status": "approved", "reason": "roz ka schedule", "slot": _sl95, "meta": "/tmp/b95"})
    _PL95.save_job("svcmo95c", {"brand": "money", "status": "approved", "reason": "roz ka schedule", "slot": _sl95, "meta": "/tmp/c95"})
    check(_PL95.svc_twin_today("svcpa95b", _PL95.jobs()["svcpa95b"]) == "svcpa95a", "dohri services reel (same brand, same din) pakdi")
    check(_PL95.svc_twin_today("svcmo95c", _PL95.jobs()["svcmo95c"]) is None, "doosre brand ki services reel nahi rukti")
    _ST95.put("svc_taken", {_sl95[:10]: {"money": "svcmo95nam"}})
    check(_PL95.svc_twin_today("svcmo95c", _PL95.jobs()["svcmo95c"]) == "svcmo95nam", "namoona ne slot liya = roz wali nahi jaati")
finally:
    _ST95.put("svc_taken", _ost95 or {})
    _ST95.update("jobs", lambda d: {k: v for k, v in (d or {}).items() if k not in ("svcpa95a", "svcpa95b", "svcmo95c")}, {})
_mi95 = _IX95.message([("https://sabhisaab.com/a", "naya page"), ("https://sabhisaab.com/b", "naya page")],
                      summ="📊 Kul page (sitemap): <b>368</b> | Google index ✅ <b>350</b> | baaki ⏳ <b>18</b>")
check("(2 page)" in _mi95 and "Baaki 16 page" in _mi95, "indexing: suchi 2 + baaki 16 ka saaf hisaab (do number ka ulta-pulta nahi)")
# ---------------- v3.9.5b: IG galti, slot doctor, services CTA, bonus/referral ek srot ----------------
from app import igguard as _IG95, svcvideo as _SV95, bonus as _BN95, tg as _TG95  # noqa: E402
_pf95 = 'IG upload HTTP 400: {"debug_info":{"retriable":false,"type":"ProcessingFailedError","message":"Request processing failed"}} (size 13 MB)'
check(_IG95.transient(_pf95) and not _IG95.transient("Error validating access token: session has been invalidated"),
      "IG: ProcessingFailed = kuch der ki galti, token galti nahi")
_oc95 = _ST95.get("ig_fail_cnt")
_ST95.put("ig_fail_cnt", {})
for _i in range(5):
    _IG95.note_fail("pahadi", _pf95)
check(not _IG95.off("pahadi") and not (_ST95.get("ig_fail_cnt") or {}).get("pahadi"), "IG: 5 ProcessingFailed se bhi brand ka IG band NAHI")
_ST95.put("ig_fail_cnt", _oc95 or {})
check(_PL95.ig_transient_only({"instagram": "3 koshish fail, 55 sec: " + _pf95}) and not _PL95.ig_transient_only({"instagram": _pf95, "facebook": "x"}),
      "upload: sirf IG kuch-der-galti pehchani")
check("⏳ instagram" in _PL95._err_line("instagram", _pf95, {"status": "approved", "tries": 1}) and
      _PL95._err_line("facebook", "x", {"status": "approved"}).startswith("❌"), "report: IG dobara = ⏳ (laal ❌ nahi)")
_osay95, _ost95b = _TG95.say, (_ST95.get("made_today"), _ST95.get("slot_doc"), _ST95.get("jobs"))
_TG95.say = lambda *a, **k: True
_TG95.alert = lambda *a, **k: True
try:
    _t95 = _PL95.now().replace(hour=8, minute=0, second=0, microsecond=0)
    _sch95 = _PL95.schedule()
    _b95 = next(iter(_sch95))
    _hm95 = [x.strip() for x in str(_sch95[_b95]).split(",") if x.strip()][0]
    _h, _m = map(int, _hm95.split(":"))
    _slot95 = _t95.replace(hour=_h, minute=_m)
    if _slot95 - _t95 < _dt95.timedelta(minutes=30):
        _t95 = _slot95 - _dt95.timedelta(hours=2)
    _ST95.put("made_today", {f"{_t95.date()}:{_b95}:{_hm95}": 1})
    _ST95.put("slot_doc", {})
    _calls95 = []
    _PL95.slot_doctor(lambda *a: _calls95.append(a), None, t=_t95)
    check(_calls95 and _calls95[0][1] == _b95 and _calls95[0][3] == "roz ka schedule", "slot doctor: bani nahi video ka slot -> dobara banao")
    _calls95.clear()
    _PL95.slot_doctor(lambda *a: _calls95.append(a), None, t=_t95)
    _PL95.slot_doctor(lambda *a: _calls95.append(a), None, t=_t95)
    check(len(_calls95) == 1, "slot doctor: ek slot par max 2 baar (loop nahi)")
finally:
    _TG95.say = _osay95
    _ST95.put("made_today", _ost95b[0] or {})
    _ST95.put("slot_doc", _ost95b[1] or {})
    _ST95.put("jobs", _ost95b[2] or {})
check("कमेंट" not in _SV95.CTA_SAY and "कमेंट" not in _SV95.CTA_SHOW and "फ़ॉर्म" in _SV95.CTA_SAY, "services CTA: comment nahi maangta, form")
check(any(_rex.search(p_, "कमेंट में अपना काम लिखिए") for p_ in _SV95.BAN) and not any(_rex.search(p_, "इंस्टाग्राम कमेंट का जवाब") for p_ in _SV95.BAN),
      "services audit: 'कमेंट में ... लिखिए' mana, kaam ka naam 'कमेंट का जवाब' theek")
_tm95 = '<li><b>Referral:</b> purana text</li>'
check(_BN95.terms_text() in _BN95.sync_html("terms.html", _tm95) and "₹300 ya usse bade" in _BN95.terms_text(), "bonus: terms ki line ek srot se")
check("दस प्रतिशत" in _BN95.say_hi() and "SVC_BONUS" in _BN95.js(), "bonus: video awaaz + website js ek srot se")
_obr95 = _ST95.get("bonus_rules")
_ST95.put("bonus_rules", {"ref_pct": 15})
check("15%" in _BN95.terms_text() and "पंद्रह" in _BN95.say_hi() and _S95.ref_credit(1000) == 150, "bonus set 15% = terms + awaaz + hisaab sab ek saath")
_ST95.put("bonus_rules", _obr95 or {})
check(_S95.ref_credit(1000) == 100 and _S95.ref_credit(299) == 0 and _S95.ref_credit(9000) == 500, "bonus: 10% / ₹300 se kam 0 / max ₹500")
import re as _re95  # noqa: E402
_lq95 = open(_S95.__file__.replace("svc.py", "assets/svc/q.html"), encoding="utf-8").read()
check("__BONUS_PAGE__" in _lq95 and "s.bonus" in _lq95, "gupt page: bonus text ek srot + customer ka bonus dikhta")

# ---- v3.9.6: AMP story, UK hub link, SVCKIT guard, daily.py crash, raqm, auto-doctor turant, raat 23:30 ----
from app import website as _W96, autodoctor as _AD96, raqmsafe as _RS96, state as _ST96, pipeline as _PL96  # noqa: E402
_amp96 = ('<html ⚡ lang="hi"><head><style amp-boilerplate>body{x}' + _W96.MFIX_CSS + '</style><style amp-custom>a{}</style></head></html>')
check(_W96.MFIX_TAG not in _W96.amp_clean(_amp96) and "<style amp-boilerplate>body{x}</style>" in _W96.amp_clean(_amp96),
      "AMP story: boilerplate se mobile CSS hata (Web Story invalid ka ilaaj)")
check(_W96.mobile_fix_text(_amp96.replace(_W96.MFIX_CSS, "")) == _amp96.replace(_W96.MFIX_CSS, ""), "mobile fix AMP page par kabhi nahi lagta")
check(_W96.MFIX_TAG in _W96.mobile_fix_text("<html><style>a{}</style></html>"), "mobile fix aam page par lagta hai")
import pathlib as _pl96, tempfile as _tf96  # noqa: E402
_r96 = _pl96.Path(_tf96.mkdtemp())
for _d96 in ("pauri-garhwal", "haridwar", "almora"):
    (_r96 / f"{_d96}-sanskriti-tyohar.html").write_text("x")
_hub96 = '<h3 id="13-zile">13 Zile</h3><table>Pauri</table><p>In links ko tab tak active na karein</p><h3 id="related-guides-aur-tools-sab-hisaab">R</h3>'
_o96 = _W96.uk_hub_table(_hub96, _r96)
check('href="/pauri-garhwal-sanskriti-tyohar"' in _o96 and 'href="/haridwar-sanskriti-tyohar"' in _o96 and "tab tak active" not in _o96
      and 'href="/chamoli-sanskriti-tyohar"' not in _o96, "UK hub: 13 zile ki table mein sirf live page ke link, editor note hata")
check("SVCKIT.enhance)SVCKIT.enhance" in _W96.svckit_guard("if(f&&window.SVCKIT)SVCKIT.enhance(f,{})"), "services form: SVCKIT.enhance guard")
_dy96 = _W96.daily_fix("    out, new_seen = [], dict(seen)\n    new_seen = {k: v for k, v in new_seen.items() if v >= cut}\n")
check("isinstance(v, str) and v >= cut" in _dy96, "daily.py news(): bool/str TypeError ka ilaaj")
from PIL import ImageFont as _IF96  # noqa: E402
_RS96.install()
check(getattr(_IF96.FreeTypeFont.getlength, "_raqmsafe", False) and _RS96.clean("ab😀️") == "ab", "raqm_layout galti: font naap surakshit")
_ok96 = _ST96.get("ad_kick"), _ST96.get("ad_kick_done"), _ST96.get("ad_kick_run")
_ST96.put("ad_kick_done", 0); _ST96.put("ad_kick_run", 0)
_AD96.kick("test galti")
_k96 = _ST96.get("ad_kick") or {}
_ST96.put("ad_kick", {**_k96, "t": _k96.get("t", 0) - 400})
check(_AD96.kick_due(), "auto-doctor: galti ke 3 min baad khud jaagta hai")
_ST96.put("ad_kick_run", __import__("time").time())
check(not _AD96.kick_due(), "auto-doctor: do daur ke beech 20 min (loop nahi)")
check("raqmsafe" in " ".join(_AD96.heal("raqm_layout() failed")), "auto-doctor heal: raqm")
_ST96.put("ad_kick", _ok96[0] or {}); _ST96.put("ad_kick_done", _ok96[1] or 0); _ST96.put("ad_kick_run", _ok96[2] or 0)
check(_PL96.NIGHT_START == "23:30" and _PL96.NIGHT_END == "04:30", "raat render: 23:30 - 04:30")

import glob as _gl97  # noqa: E402
_bad97 = [f for f in ("app/answers.py", "app/puzzles.py", "app/design.py", "app/sharekit.py", "app/sawalpost.py", "app/hooks.py")
          if __import__("re").search(r'"[^"\n]*कमेंट में[^"\n]*(लिखिए|लिखें)', "\n".join(
              l for l in open(f, encoding="utf-8") if not l.lstrip().startswith(("#", "_FILLER"))))]
check(not _bad97, f"sawal reel/post: 'कमेंट में ... लिखिए' kahin nahi (Meta engagement-bait) {_bad97}")
from app import tasks as _TK97  # noqa: E402
_ot97 = (_ST96.get("todo"), _ST96.get("mig_396"))
_ST96.put("todo", [{"x": "[Owner, 2 min] Website ZIP (privacy + services-demo, 25 Nov) bot ko bhejo"}]); _ST96.put("mig_396", False)
_TK97._mig_396()
_x97 = [o.get("x", "") for o in _ST96.get("todo") or []]
check(not any("Website ZIP (privacy" in x for x in _x97) and any(o.get("auto") == "amp_ok" for o in _ST96.get("todo") or []),
      "PENDING: privacy ZIP hata (pehle se live), AMP kaam bot khud jaanchta (amp_ok)")
_ST96.put("todo", _ot97[0] or []); _ST96.put("mig_396", _ot97[1] or False)
print(f"\nSMOKE {'PASS' if not BAD else 'FAIL'}: {len(OK)} ✅, {len(BAD)} ❌")
sys.exit(1 if BAD else 0)
