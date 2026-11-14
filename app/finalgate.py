"""v3.1.0 (11 Nov 2026 audit) - FINAL AUTHORITY (pakka darwaza): video post hone se theek pehle ki aakhri jaanch.

Owner: "jaise hi video final hoti hai to final authority check kare tab post ho... roz ki nautanki nahi chalegi".
v2.9.2 ke 7 jaanch (audit.final_authority) waise hi hain. Ye unke UPAR 5 nayi PAKKI jaanch jodta hai - har ek kisi asli galti se nikli:
  1) LIKHAI   - Hindi mein doosri lipi/toota akshar/Hindi+English chipka shabd (live galti: 'परछਾਈ' #3977, 10 Nov).
  2) VISHAY   - 3 aam channel par SIP/FD/RD/loan/nivesh-salah (owner niyam 9). Tyohaar wale slot mein ye jaanch chhoot rahi thi
                (live galti: Money #4592 'Bhai Dooj ... SIP aur tax', 10 Nov). YouTube ki July 2026 niti: AI awaaz + paise ki salah = monetization nahi.
  3) DHAANCHA - sawal hai, 2-4 vikalp, koi khaali/bahut lamba nahi.
  4) PADHNE KA SAMAY - lamba likha scene 1 second se kam na dikhe (koi padh hi na paaye).
  5) RAFTAAR  - bolne ki raftaar (shabd/second) aur kul lambai ka ASLI naap - owner ko manzoori sandesh mein dikhe (rokta nahi, batata hai).
Sab jaanch bina network, 1 second se kam. Koi jaanch khud crash ho to video nahi rukti (log mein jaati hai) - schedule kabhi na toote.
"""
import re

from .log import log

OPT_MAX = 80                 # ek vikalp itne akshar se lamba = card par nahi samata
SLOW_WPS, FAST_WPS = 1.9, 3.6     # Hindi bolne ki aaraamdeh raftaar (shabd/second) - isse bahar ho to owner ko ⚠ dikhe


def _texts(meta):
    """Public + bolne wala text (description nahi - usme brand ki line/tag hote hain)."""
    out = [str(meta.get("title") or ""), str(meta.get("puzzle_q") or "")]
    out += [str(o) for o in (meta.get("puzzle_options") or [])]
    for sc in meta.get("scenes") or []:
        if isinstance(sc, dict):
            out += [str(sc.get("show") or ""), str(sc.get("say") or "")]
    return out


def pace(meta):
    """Asli naap: kul second, bole gaye shabd, shabd/second, har scene (second, shabd). Naap na ho sake to {}."""
    try:
        scenes = [s for s in (meta.get("scenes") or []) if isinstance(s, dict)]
        starts = list(meta.get("scene_starts") or [])
        total = float(meta.get("duration") or 0)
        if not scenes or len(starts) != len(scenes) or total <= 0:
            return {}
        per = []
        for i, sc in enumerate(scenes):
            end = starts[i + 1] if i + 1 < len(starts) else total
            d = max(0.0, float(end) - float(starts[i]))
            say = re.sub(r"https?://\S+", "", str(sc.get("say") or sc.get("show") or ""))
            w = len([x for x in say.split() if x.strip(".,!?।:;-–—")])
            per.append((round(d, 2), w, len(str(sc.get("show") or ""))))
        words = sum(p[1] for p in per)
        spoken = sum(p[0] for p in per) or total
        return {"sec": round(total, 1), "words": words, "wps": round(words / spoken, 2) if spoken else 0.0, "scenes": per}
    except Exception as e:
        log(f"finalgate pace: {e}")
        return {}


def pace_line(meta):
    p = pace(meta)
    if not p:
        return ""
    flag = "🐢 dheemi" if p["wps"] < SLOW_WPS else "🐇 tez" if p["wps"] > FAST_WPS else "✅ theek"
    return f"Raftaar {p['wps']} shabd/sec ({flag}), kul {p['sec']}s, {len(p['scenes'])} scene"


def check(meta):
    """-> [(bool, sandesh)] - audit.run ke checks mein judta hai. False = video aage nahi jayegi (doosri script banegi)."""
    out = []
    try:
        from . import hindifix
        probs = hindifix.script_problems(meta)
        out.append((not probs, "Final+: Hindi likhai saaf (doosri lipi/toota/chipka akshar nahi)"
                    + ("" if not probs else " - " + "; ".join(probs)[:160])))
    except Exception as e:
        log(f"finalgate likhai: {e}")
    try:
        from . import qplan
        brand = meta.get("brand")
        hit = (brand != "pahadi" and meta.get("format") != "long" and not meta.get("owner_topic")
               and bool(qplan.BLOCK_RX.search(" ".join(_texts(meta)))))
        out.append((not hit, "Final+: vishay niyam ke andar (aam channel par SIP/FD/RD/loan/nivesh-salah nahi)"))
    except Exception as e:
        log(f"finalgate vishay: {e}")
    try:
        opts = [str(o).strip() for o in (meta.get("puzzle_options") or [])]
        if opts:
            q = str(meta.get("puzzle_q") or "").strip()
            okk = (len(q) >= 6 and 2 <= len(opts) <= 4 and all(o and len(o) <= OPT_MAX for o in opts))
            out.append((okk, "Final+: sawal ka dhaancha (sawal + 2-4 vikalp, koi khaali/bahut lamba nahi)"))
    except Exception as e:
        log(f"finalgate dhaancha: {e}")
    try:
        p = pace(meta)
        if p:
            flash = [i + 1 for i, (d, _w, n) in enumerate(p["scenes"]) if n >= 40 and d < 1.0]
            out.append((not flash, "Final+: har lamba scene padhne layak der dikhta hai"
                        + ("" if not flash else f" - scene {flash} 1 sec se kam")))
            out.append((True, "Final+: " + pace_line(meta)))          # sirf jaankari (rokta nahi)
    except Exception as e:
        log(f"finalgate raftaar: {e}")
    try:
        if meta.get("answer_offsite") and meta.get("puzzle_options") and not str(meta.get("puzzle_exp") or "").strip():
            out.append((True, "Final+: ⚠ is sawal ki 'wajah' khaali hai - website par sirf jawab dikhega (rokta nahi)"))
    except Exception as e:
        log(f"finalgate wajah: {e}")
    return out


def blocked_script(brand, script):
    """Render se PEHLE (minute bachane ko): 3 aam channel par mana vishay? -> bool"""
    try:
        from . import qplan
        return (brand != "pahadi" and not script.get("owner_topic")
                and bool(qplan.BLOCK_RX.search(" ".join(_texts(script)))))
    except Exception:
        return False


def remember(meta, checks):
    """Aakhri jaanch ka nateeja yaad rakho ('final jaanch' command ke liye)."""
    try:
        from . import state
        import datetime
        rows = [(c, m) for c, m in checks if str(m).startswith("Final")]
        state.put("final_gate_last", {"t": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "title": str(meta.get("title", ""))[:80],
                                      "brand": meta.get("brand"), "rows": rows[:20], "pass": all(c == "✅" for c, _ in checks)})
    except Exception as e:
        log(f"finalgate remember: {e}")


def report():
    """Owner ke liye: aakhri video ki final authority jaanch (kuch badalta nahi)."""
    from . import state
    d = state.get("final_gate_last") or {}
    if not d:
        return "🛂 Final authority: abhi tak koi video is jaanch se nahi guzri (agli video ke baad dikhega)."
    L = [f"🛂 FINAL AUTHORITY - aakhri video ({d.get('t', '')}, {d.get('brand', '')})", f"📝 {d.get('title', '')}",
         "Nateeja: " + ("✅ PAAS - post ke layak" if d.get("pass") else "❌ ROKI gayi - doosri script bani")]
    L += [f"{c} {m}" for c, m in d.get("rows") or []]
    L.append("\nAwaaz ki raftaar badalni ho: 'awaaz raftaar 1.1' (0.9 se 1.25, dohri pushti).")
    return "\n".join(L)[:3800]


# ---- awaaz ki raftaar: owner ki pakki setting (dohri pushti se hi badalti hai) ----
SPEED_MIN, SPEED_MAX = 0.9, 1.25


def voice_speed(default=1.0):
    try:
        from . import state
        v = state.get("voice_speed")
        return float(v) if v and SPEED_MIN <= float(v) <= SPEED_MAX else float(default)
    except Exception:
        return float(default)


def parse_speed(text):
    m = re.search(r"(\d(?:[.,]\d{1,2})?)", str(text or ""))
    if not m:
        return None
    v = float(m.group(1).replace(",", "."))
    return v if SPEED_MIN <= v <= SPEED_MAX else None
