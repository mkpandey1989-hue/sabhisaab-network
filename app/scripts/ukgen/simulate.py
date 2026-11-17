import sys, json, os, shutil, subprocess, re
sys.path.insert(0, "/home/claude/ukgen")
sys.path.insert(0, "/home/claude/sabhisaab-network")
from app.pagequeue import gate, select, sitemap_add, inject, inject_home, page_images
OUT = "/home/claude/ukout"
SNIP = ('<div class="artread"><b>Uttarakhand guide</b><a href="/uttarakhand">Uttarakhand ki poori jaankari: 13 zile, '
        'Char Dham, pahadi khana, nali-mutthi aur bhoo-kanoon</a></div>')
INJ = ["uttarakhand-farmer-id-ukfr", "nali-mutthi-square-feet", "nali-mutthi-converter", "bigha-kitna-hota-hai", "agristack-guide", "guides"]

def run(days, tag):
    man = json.load(open(OUT + "/manifest.json"))
    live, plan = [], []
    for d in range(days):
        ch = select(man, set(live), 8, {"uttarakhand": len(INJ)})
        if not ch: break
        live += ch; plan.append(ch)
    site = "/home/claude/sim_" + tag
    shutil.rmtree(site, ignore_errors=True)
    shutil.copytree("/home/claude/sabhisaab_site", site, ignore=shutil.ignore_patterns(".git"))
    cfg = json.load(open(site + "/config.json")); cfg["site_dir"] = site + "/site"; json.dump(cfg, open(site + "/config.json", "w"))
    L = set(live)
    ent = []
    for i, ch in enumerate(plan):
        date = "2026-11-%02d" % (15 + i) if i < 16 else "2026-12-%02d" % (i - 15)
        for s in ch:
            html = gate(open(OUT + "/pages/%s.html" % s, encoding="utf-8").read(), L, date, 188)
            open(site + "/site/%s.html" % s, "w", encoding="utf-8").write(html)
            img = re.search(r'og:image" content="https://sabhisaab.com/([^"]+)"', html).group(1)
            ent.append((s, date, img))
    sm = open(site + "/site/sitemap.xml").read()
    open(site + "/site/sitemap.xml", "w").write(sitemap_add(sm, ent))
    htmls = [open(site + "/site/%s.html" % s_).read() for s_ in L]
    for nm in page_images(htmls, set(os.listdir(site + "/site")), set(os.listdir(OUT + "/img"))):   # bot jaisa: photo page ke saath
        shutil.copy2(OUT + "/img/" + nm, site + "/site/" + nm)
    for f in INJ:
        fp = site + "/site/%s.html" % f
        src = open(fp).read()
        open(fp, "w").write(inject(src, SNIP))
    r = subprocess.run([sys.executable, "scripts/audit.py"], cwd=site, capture_output=True, text=True)
    print(tag, "days", len(plan), "live", len(live))
    print(r.stdout[-6000:])
if __name__ == "__main__":
    run(int(sys.argv[1]), sys.argv[2])
