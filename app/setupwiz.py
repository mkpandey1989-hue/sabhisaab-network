"""v2.7.2 (owner 10 Nov: 'question, look etc sab setting ke liye easy line-wise pichhle sample; channel-wise final ka option'):
CHANNEL SETUP - ek message mein ek channel ki saari setting line-wise, har line par namoona aur badlo; aakhir mein 'FINAL'.

1) 🎨 Look        - Sample Studio ka namoona (video + 3 thumbnail; '➡️ Agla' se agla look; '✅ Pakka' se pakka) - pehle se tha
2) 🎣 Sawal ka tareeka - is channel ke ASLI sawal par saare 8 andaaz ek saath padhne ko (line-wise), ek chunein ya 'Rotate'
3) 🖼 Thumbnail rang/layout - jo rang/layout pass ho chuke (rotate) dikhte hain; naya namoona Studio se
4) ⏰ Samay        - roz ke 2 slot; 'Best time' se asli data ke hisaab se sujhaav
5) ✅ FINAL        - is channel ki setting pakki (diary + list); kabhi bhi badal sakte hain
Kuch bhi bina owner ke button ke nahi badalta. Namoona kabhi post nahi hota.
"""
import datetime

from . import state, tg
from .config import BRANDS, SCHEDULE


def brand_menu():
    fin = state.get("setup_final") or {}
    return tg.inline([[(("✅ " if b in fin else "⚙️ ") + v["name"], f"cs:b:{b}")] for b, v in BRANDS.items()])


def hook_of(brand):
    hb = state.get("hook_mode_brand") or {}
    return hb.get(brand) or state.get("hook_mode") or "rotate"


def card(brand):
    """Ek channel ki setting - line-wise."""
    from . import hooks
    look = (state.get("brand_look") or {}).get(brand) or {}
    pal = [p for p in (state.get("palettes_ok") or []) if p]
    lay = [x for x in (state.get("layouts_ok") or []) if x]
    hk = hook_of(brand)
    fin = (state.get("setup_final") or {}).get(brand)
    L = [f"⚙️ {BRANDS[brand]['name']} - CHANNEL SETUP" + (f" (FINAL {fin})" if fin else ""), "",
         f"1) 🎨 Look: {look.get('look') or 'Premium Neon (default)'}",
         f"2) 🎣 Sawal ka tareeka: {'baari-baari (8 andaaz)' if hk == 'rotate' else hk + ' - ' + hooks.STYLES[hk][0]}",
         f"3) 🖼 Thumbnail: rang {', '.join(pal) or 'default'} | layout {', '.join(lay) or 'list'} (baari-baari)",
         f"4) ⏰ Samay: roz {SCHEDULE.get(brand, '-')}", "",
         "Har line ka button dabaiye - namoona dekh kar badlein. Sab theek lage to '✅ FINAL'."]
    kb = tg.inline([[("🎬 Look namoona", f"cs:look:{brand}"), ("🎣 8 tareeke dekho", f"cs:hk:{brand}")],
                    [("🎨 Rang/Layout", f"cs:pal:{brand}"), ("⏰ Best time", "cs:bt:x")],
                    [("✅ FINAL (is channel ki setting pakki)", f"cs:fin:{brand}")]])
    return "\n".join(L), kb


def hook_samples(brand):
    """Is channel ke ek asli (bank) sawal par saare andaaz - owner padh kar chune."""
    from . import puzzles, hooks
    p = None
    for _ in range(6):
        try:
            p = puzzles.generate_puzzle("auto", brand)
        except Exception:
            p = None
        if p and p.get("puzzle_options") and p.get("puzzle_answer"):
            break
    if not p:
        return "Abhi namoona sawal nahi mila - thodi der baad.", None
    q = p.get("puzzle_q") or (p.get("scenes") or [{}])[1].get("show", "")
    L = [f"🎣 {BRANDS[brand]['name']}: ek hi sawal, {len(hooks.STYLES)} tareeke", f"❓ {q}", f"Vikalp: {' | '.join(p['puzzle_options'])}", ""]
    for k in hooks.STYLES:
        r = hooks.apply(dict(p), brand, mode=k)
        L.append(f"• {k}: {r['scenes'][0]['show']}")
    L += ["", "(Sahi jawab yahan nahi likha - video mein bhi leak nahi hota.) Ek chuniye ya baari-baari:"]
    names = list(hooks.STYLES)
    rows = [[(n, f"cs:hs:{brand}:{n}") for n in names[i:i + 4]] for i in range(0, len(names), 4)]
    rows.append([("🔄 Baari-baari (rotate)", f"cs:hs:{brand}:rotate")])
    return "\n".join(L), tg.inline(rows)


def set_hook(brand, mode):
    from . import hooks
    if mode != "rotate" and mode not in hooks.STYLES:
        return "❌ Aisa andaaz nahi."
    state.update("hook_mode_brand", lambda d: {**(d or {}), brand: mode}, {})
    return f"✅ {BRANDS[brand]['name']}: sawal ka tareeka '{mode}'. Agli reel se."


def finalize(brand):
    fin = dict(state.get("setup_final") or {})
    fin[brand] = str(datetime.date.today())
    state.put("setup_final", fin)
    try:
        from . import diary
        diary.add("niyam", f"{BRANDS[brand]['name']}: channel setup FINAL ({hook_of(brand)})")
    except Exception:
        pass
    left = [BRANDS[b]["name"] for b in BRANDS if b not in fin]
    return (f"✅ {BRANDS[brand]['name']} ki setting FINAL. Roz ki reel isi se banegi (badalna ho to kabhi bhi '⚙️ Channel setup').\n"
            + (f"Baaki channel: {', '.join(left)}" if left else "🎉 Chaaron channel FINAL!"))
