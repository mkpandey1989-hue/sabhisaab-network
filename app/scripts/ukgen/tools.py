"""4 bane-banaye Uttarakhand tool ko site ke template mein (audit ke niyam ke saath). Asli calculator/JS waisa hi."""
import re, os, sys, json, html as H
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools_content import TOOLS
from clean import esc

SRC = "/home/claude/uk/UK_work/tools"
DIST = {"almora", "bageshwar", "chamoli", "champawat", "dehradun", "haridwar", "nainital", "pauri-garhwal", "pithoragarh",
        "rudraprayag", "tehri-garhwal", "udham-singh-nagar", "uttarkashi"}
TOOL_CSS = """<style>
.uktool{--geru:#8F2D1F;--geru-d:#6E2015;--deodar:#0F766E;--ghaam:#D99A1E;--ink:#24282C;--muted:#5C6268;--line:#E3DDD6;--bg:#FFFFFF;--panel:#FBF6F2;--chip:#F3E7E0;--ok:#2F7D4F;--bad:#B3261E;margin:14px 0 6px}
.uktool .aipan{height:14px;border-radius:6px;margin:0 0 14px;background-color:#8F2D1F;background-image:radial-gradient(circle at 11px 11px,#fff 2.2px,transparent 2.6px),linear-gradient(90deg,transparent 0 10px,rgba(255,255,255,.85) 10px 12px,transparent 12px 22px);background-size:22px 22px,22px 22px}
.uktool .panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}
.uktool label{display:block;font-weight:600;margin:12px 0 6px}
.uktool input,.uktool select,.uktool button{font:inherit}
.uktool input[type=number],.uktool input[type=text],.uktool input[type=search],.uktool input[type=date],.uktool select{width:100%;padding:11px 12px;border:1.5px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink)}
.uktool .btn{background:var(--deodar);color:#fff;border:0;border-radius:10px;padding:11px 18px;font-weight:700;cursor:pointer}
.uktool .btn.alt{background:transparent;color:var(--deodar);border:1.5px solid var(--deodar)}
.uktool .grid2{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}
@media (max-width:620px){.uktool .grid2{grid-template-columns:1fr}}
.uktool .chips{display:flex;flex-wrap:wrap;gap:8px}
.uktool .chip{display:inline-flex;align-items:center;gap:6px;padding:8px 12px;border-radius:999px;background:var(--chip);border:1.5px solid transparent;cursor:pointer;font-weight:600;user-select:none}
.uktool .chip input{accent-color:var(--geru);width:auto}
.uktool .chip:has(input:checked){border-color:var(--geru);background:var(--bg)}
.uktool .note{font-size:.9rem;color:var(--muted)}
.uktool table{width:100%;border-collapse:collapse;font-size:.95rem}
.uktool th,.uktool td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
.uktool th{color:var(--muted);font-weight:600}
.uktool .tablewrap{overflow-x:auto}
.uktool #res,.uktool #out,.uktool #qbox,.uktool #next{min-height:60px}
</style>
"""

def fix_urls(s):
    s = re.sub(r"https://sabhisaab\.com/uttarakhand/([a-z-]+)", lambda m: "/%s-uttarakhand" % m.group(1) if m.group(1) in DIST else "/uttarakhand", s)
    return s

def port(slug, uk_slugs):
    s = open(os.path.join(SRC, slug + ".html"), encoding="utf-8").read()
    main = s[s.find("<main>") + 6:s.find("</main>")]
    # aakhri 'aur tool / aur taiyari' link-section (navigation) hatao - uski jagah site ka gated jaal
    main = re.sub(r"<section>\s*<h2>(Aur kaam ke tool|Aur taiyari|Aur tool)</h2>.*?</section>", "", main, flags=re.S)
    scripts = [x for x in re.findall(r"<script(?![^>]*application/ld\+json)[^>]*>(.*?)</script>", s, re.S)]
    main = fix_urls(main)
    main = re.sub(r"(<details\b[^>]*>)\s*<summary>", r"\1\n<summary>", main)   # settings ka khulne wala dabba FAQ nahi
    def a(m):
        href = m.group(1)
        sl = href.replace("https://sabhisaab.com", "").strip("/")
        if sl in uk_slugs:
            return '<a href="/%s" data-uk="%s"' % (sl, sl)
        return '<a href="/%s"' % sl
    main = re.sub(r'<a href="(https://sabhisaab\.com/[a-z0-9-]*)"', a, main)
    main = re.sub(r'(<input\b(?=[^>]*type="number")(?![^>]*inputmode)[^>]*?)(/?>)', r'\1 inputmode="decimal"\2', main)
    js = [fix_urls(x).replace('Blueprint ne', 'purani suchi ne').replace('Blueprint ke shabd', 'purani suchi ke shabd')
          .replace('Blueprint me aaya', 'purani suchi me aaya').replace('Blueprint', 'purani suchi')
          .replace('alag, verify', 'alag, pushti karein') for x in scripts]
    intro = re.search(r'<header class="top">.*?<p>(.*?)</p>', s, re.S)
    return main.strip(), js, (H.unescape(re.sub(r"<[^>]+>", "", intro.group(1))) if intro else "")

def tool_parts(slug, uk_slugs):
    t = TOOLS[slug]
    main, js, intro = port(slug, uk_slugs)
    parts = ['<p class="lead">%s</p>\n' % esc(intro or t["desc"]),
             '<div class="uktool"><div class="aipan" aria-hidden="true"></div>\n%s\n</div>\n' % main]
    for sec in t["sections"]:
        h, ps = sec[0], sec[1]
        hid = re.sub(r"[^a-z0-9]+", "-", h.lower()).strip("-")
        parts.append('<h2 id="%s">%s</h2>\n' % (hid, esc(h)) + "".join("<p>%s</p>\n" % esc(p) for p in ps))
        if len(sec) > 2:
            rows = sec[2]
            parts.append('<div class="tw"><table class="tb"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>\n' % (
                "".join("<th>%s</th>" % esc(c) for c in rows[0]),
                "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % esc(c) for c in r) for r in rows[1:])))
    parts.append('<h2 id="sawal">Aksar poochhe jaane wale sawal</h2>\n')
    for q, a in t["faqs"]:
        parts.append('<details class="faq"><summary>%s</summary><div class="fa">%s</div></details>\n' % (esc(q), esc(a)))
    jsblk = "".join("<script>%s</script>\n" % x for x in js)
    return parts, t["faqs"], jsblk
