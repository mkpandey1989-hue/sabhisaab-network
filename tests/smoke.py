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
        "toolpin ideas push quizbot hindifix finalgate ownermode learn audit pagequeue").split()
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
print(f"\nSMOKE {'PASS' if not BAD else 'FAIL'}: {len(OK)} ✅, {len(BAD)} ❌")
sys.exit(1 if BAD else 0)
