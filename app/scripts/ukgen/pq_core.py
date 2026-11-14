"""Page queue ka shuddh (pure) hissa: kaunse page aaj, link-gating, sitemap. Bot (app/pagequeue.py) yahi code chalata hai."""
import re, datetime

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def gate(html, live, pubdate, tools_count=None):
    """Jo page abhi live nahi, uska link hatao (text rehta hai), khaali suchi chhupao, tareekh bharo."""
    def li(m):
        return m.group(0) if m.group(1) in live else ""
    html = re.sub(r'<li data-ukli="([a-z0-9-]+)">.*?</li>', li, html, flags=re.S)
    html = re.sub(r'<div class="ukrel" data-ukblk="1"><b>[^<]*</b><ul class="ukdir"></ul></div>\n?', "", html)
    def a(m):
        return m.group(0) if m.group(2) in live else m.group(3)
    html = re.sub(r'<a href="/([a-z0-9-]+(?:#[a-z0-9-]+)?)" data-uk="([a-z0-9-]+)">(.*?)</a>', a, html, flags=re.S)
    d = datetime.date.fromisoformat(pubdate)
    html = html.replace("@@PUB@@", pubdate).replace("@@PUBH@@", "%d %s %d" % (d.day, MONTHS[d.month - 1], d.year))
    if tools_count:
        html = re.sub(r"Saare \d{2,4} Tools", "Saare %d Tools" % tools_count, html)
    return html

def inbound(slug, live_after, links, inj):
    return sum(1 for q in live_after if q != slug and slug in links.get(q, ())) + inj.get(slug, 0)

def select(manifest, live, per_day, inj=None):
    """Priority kram mein aaj ke page; har chune page par kam se kam 3 andar ke link (audit niyam) aur 'requires' pehle live."""
    inj = inj or {}
    links = {m["slug"]: set(m["links_to"]) for m in manifest}
    req = {m["slug"]: m.get("requires", []) for m in manifest}
    cand = [m["slug"] for m in sorted(manifest, key=lambda x: x["rank"]) if m["slug"] not in live]
    banned, chosen = set(), []
    for _ in range(40):
        for s in cand:
            if len(chosen) >= per_day:
                break
            if s in chosen or s in banned:
                continue
            if all(r in live or r in chosen for r in req[s]):
                chosen.append(s)
        after = set(live) | set(chosen)
        bad = [s for s in chosen if inbound(s, after, links, inj) < 3 or not all(r in after for r in req[s])]
        if not bad:
            return chosen
        for s in bad:
            chosen.remove(s); banned.add(s)
    return chosen

def sitemap_add(sm, entries, base="https://sabhisaab.com"):
    """entries: [(slug, lastmod, image)] - alphabetical kram mein jodo, pehle se ho to sirf lastmod."""
    for slug, lastmod, img in entries:
        loc = "%s/%s" % (base, slug)
        if "<loc>%s</loc>" % loc in sm:
            sm = re.sub(r"(<loc>%s</loc>\s*<lastmod>)[\d-]+" % re.escape(loc), lambda m: m.group(1) + lastmod, sm)
            continue
        block = ("<url>\n<loc>%s</loc>\n<lastmod>%s</lastmod>\n<changefreq>monthly</changefreq>\n<priority>0.7</priority>\n"
                 "<image:image><image:loc>%s/%s</image:loc></image:image>\n</url>\n") % (loc, lastmod, base, img)
        locs = [(m.start(), m.group(1)) for m in re.finditer(r"<url>\s*<loc>%s/([^<]*)</loc>" % re.escape(base), sm)]
        pos = None
        for st, sl in locs:
            if sl and sl > slug:
                pos = st; break
        if pos is None:
            pos = sm.rfind("</urlset>")
        sm = sm[:pos] + block + sm[pos:]
    return sm

INJ_MARK = "<!--uk-hub-link-->"
def inject(html, snippet):
    if INJ_MARK in html or "</main>" not in html:
        return html
    i = html.find('<div class="artread">')
    pos = i if i != -1 else html.find("</main>")
    return html[:pos] + INJ_MARK + snippet + "\n" + html[pos:]
