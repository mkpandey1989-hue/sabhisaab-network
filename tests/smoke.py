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
        "toolpin ideas push quizbot hindifix finalgate ownermode learn audit pagequeue linkedin").split()
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
print(f"\nSMOKE {'PASS' if not BAD else 'FAIL'}: {len(OK)} ✅, {len(BAD)} ❌")
sys.exit(1 if BAD else 0)
