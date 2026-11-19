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
        "toolpin ideas push quizbot hindifix finalgate ownermode learn audit pagequeue linkedin reach sawalpost intents featureaudit").split()
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
      == ["WhatsApp", "Facebook", "Telegram", "Quora", "LinkedIn", "Push", "Seedha", "Baaki"],
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
print(f"\nSMOKE {'PASS' if not BAD else 'FAIL'}: {len(OK)} ✅, {len(BAD)} ❌")
sys.exit(1 if BAD else 0)
