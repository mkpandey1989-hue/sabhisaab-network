"""v2.0: Bot ka gyaan-bhandaar - har sawaal par Gemini ko pakki jaankari (pehle sirf 4,000 akshar jaata tha).
Static: app/kb.md (niyam, policy, seema). Dynamic: website ke page, pending index, khule kaam, niyam, plan, upgrade.
Tools (sirf PADHNA): Gemini 'need' maange to bot ye chala kar dobara sochta hai - jaise Chowkidar."""
import datetime
import json
import pathlib
from . import state

STATIC = pathlib.Path(__file__).with_name("kb.md")


def static():
    try:
        return STATIC.read_text(encoding="utf-8")
    except Exception:
        return ""


def dynamic():
    out = []
    try:
        from . import siteknow
        pg = siteknow.pages()
        if pg:
            ni = siteknow.not_indexed()
            out.append(f"WEBSITE ABHI: {len(pg)} HTML page, sitemap mein {sum(1 for v in pg.values() if v.get('in_sitemap'))}; "
                       f"Google index nahi: {len(ni)} -> " + ", ".join("/" + x for x in ni[:12]))
    except Exception:
        pass
    td = [x.get("x", "")[:90] for x in (state.get("todo") or [])][:12]
    if td:
        out.append("KHULE KAAM: " + " | ".join(td))
    rl = [r.get("rule", "")[:100] for r in (state.get("rules") or [])][-12:]
    if rl:
        out.append("OWNER KE PAKKE NIYAM: " + " | ".join(rl))
    si = state.get("seo_ideas") or {}
    if si:                                       # v2.0.3: SEO diary ke topic sujhaav (plan banate waqt)
        out.append("SEO DIARY SUJHAAV (doosre channel se seekh): " + " | ".join(f"{b}: {', '.join(v[:3])}" for b, v in si.items()))
    up = state.get("upgrade_last") or {}
    if up:
        out.append(f"AAKHRI KHUD-UPGRADE: {up.get('t', '')} {up.get('summary', '')[:200]}")
    au = state.get("audit") or {}
    if au.get("probs"):
        out.append("SUBAH KI JAANCH KI DIKKAT: " + "; ".join(au["probs"])[:400])
    return "\n".join(out)


def text():
    return (static() + "\n" + dynamic())[:9000]


# ---------- padhne wale tools (Gemini 'need' se) ----------
def run_tool(name, arg=""):
    arg = (arg or "").strip()
    try:
        if name == "site_page":
            from . import siteknow
            hits = siteknow.find(arg)
            return "\n".join(f"/{k}: {v['title']} | {v['words']} shabd | lastmod {v['lastmod']} | "
                             f"index={'haan' if v.get('indexed') else ('nahi: ' + v.get('why', '') if v.get('indexed') is False else '?')}"
                             for k, v in hits) or "page nahi mila"
        if name == "plan":
            d = arg or str(datetime.date.today() + datetime.timedelta(days=1))
            return json.dumps((state.get("plan") or {}).get(d) or (state.get("plan_pending") or {}).get(d) or {}, ensure_ascii=False)
        if name == "diary":
            from . import diary
            day = arg or str(datetime.date.today())
            return "\n".join(f"{r['t'][11:16]} {r['kind']}: {r['text'][:120]}" for r in diary.recent(600) if r["t"][:10] == day)[-3000:]
        if name == "todo":
            from . import tasks
            return tasks.report()[:3000]
        if name == "traffic":
            from . import website
            return website.traffic(int(arg or 1))
        if name == "doctor":
            from . import siteknow
            return siteknow.doctor(arg.strip("/") or None)
        if name == "videos":
            from . import growth
            return growth.video_detail(5)
        if name == "upgrade":
            from . import upgrader
            return upgrader.report()
        if name == "seo":
            from . import marketing
            return marketing.gsc_ideas()
        if name == "web":
            from .brain import ask_grounded
            a, src = ask_grounded("Short Hinglish answer, exact dates in IST: " + arg)
            return a[:1500] + "\nSource: " + "; ".join(src[:3])
    except Exception as e:
        return f"{name} nahi chala: {str(e)[:150]}"
    return "aisa tool nahi"


TOOLS = ("site_page <keyword>, plan <YYYY-MM-DD>, diary <YYYY-MM-DD>, todo, traffic <days>, doctor <slug optional>, "
         "videos, upgrade, seo, web <question>")
