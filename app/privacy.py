"""v1.7: Privacy - website ki Privacy Policy (sabhisaab.com/privacy) jo vaada karti hai, bot wahi kare.

Vaade (policy section 8, 9, 12, 17):
- Commenter ka naam, comment ka text, jawab ka record: zyada se zyada 30 din, phir apne aap mitao.
  (YouTube API Developer Policy: doosre logon ka API data 30 din se zyada nahi rakhna.)
- Koi "Data Deletion" maange to owner 'data hatao <naam>' likhe -> sab jagah se turant mitao.
- Roz policy page live jaancho: zaroori baatein (YouTube ToS, Google privacy, revoke link, data deletion,
  30 din) page par hon. Na mile to laal alert - kyunki Meta/Google/Pinterest app isi URL par tike hain.
"""
import datetime
import json
import time
from . import state
from .config import DATA, SITE
from .log import log

RETAIN_DAYS = 30
DIARY = DATA / "diary.jsonl"
# diary ki wo lines jinme kisi bahari vyakti (commenter) ka naam/comment hota hai
PII_KINDS = ("comment",)
PII_PREFIX = ("jawab diya", "IG DM link", "comment jawab")
PII_SETTING = ("spam comment hataya", "abuse comment hataya")

MUST = {
    "/privacy": ["youtube.com/t/terms", "policies.google.com/privacy", "security.google.com/settings/security/permissions",
                 'id="data-deletion"', "30 din", "Gemini", "contact@sabhisaab.com"],
    "/terms": ["youtube.com/t/terms", "#ad", "AI"],
}


def _is_pii(row):
    k, tx = row.get("kind", ""), row.get("text", "")
    return k in PII_KINDS or (k == "upload" and tx.startswith(PII_PREFIX)) or (k == "setting" and tx.startswith(PII_SETTING))


def retain():
    """v2.0: website ki privacy mein jo din likhe hain wahi (siteknow roz padhta hai). Kabhi 30 se zyada nahi."""
    try:
        d = int(state.get("privacy_retain_days") or RETAIN_DAYS)
    except Exception:
        d = RETAIN_DAYS
    return max(1, min(d, RETAIN_DAYS))


def migrate():
    """v2.0: purana audience record sirf naam se tha (YouTube + Instagram ke ek naam wale log jud jaate the) -
    policy kehti hai platform jodkar track nahi karte. Ab key = 'platform:naam'. Purane (bina platform) record hatao."""
    if state.get("aud_v2"):
        return 0
    aud = state.get("audience") or {}
    keep = {k: v for k, v in aud.items() if ":" in k}
    state.put("audience", keep)
    state.put("aud_v2", True)
    return len(aud) - len(keep)


def purge(days=None):
    """Roz raat: seema (30 din) se purana commenter data mitao (audience, diary, drafts, queue, backup). Hisaab lautaata hai."""
    days = days or retain()
    migrate()
    cut_d = str(datetime.date.today() - datetime.timedelta(days=days))
    cut_ts = time.time() - days * 86400
    out = {}
    aud = state.get("audience") or {}
    keep = {k: v for k, v in aud.items() if isinstance(v, dict) and (v.get("last") or "") >= cut_d}
    out["audience"] = len(aud) - len(keep)
    if out["audience"]:
        state.put("audience", keep)
    try:
        lines = DIARY.read_text(encoding="utf-8").splitlines()
        new = []
        for x in lines:
            try:
                r = json.loads(x)
            except Exception:
                continue
            if _is_pii(r) and r.get("t", "")[:10] < cut_d:
                continue
            new.append(x)
        out["diary"] = len(lines) - len(new)
        if out["diary"]:
            DIARY.write_text("\n".join(new) + ("\n" if new else ""), encoding="utf-8")
    except FileNotFoundError:
        out["diary"] = 0
    except Exception as e:
        log(f"privacy diary: {e}")
    dr = state.get("reply_drafts") or {}
    dr2 = {k: v for k, v in dr.items() if (v.get("at") or 0) > cut_ts}      # v2.0: din ke hisaab se (ginti se nahi)
    if len(dr2) != len(dr):
        state.put("reply_drafts", dr2)
        out["drafts"] = len(dr) - len(dr2)
    for f in sorted((DATA / "backup").glob("*")) if (DATA / "backup").exists() else []:   # backup bhi seema ke andar
        if f.is_file() and f.name.startswith(("state-", "diary-")) and f.stat().st_mtime < cut_ts:
            f.unlink(missing_ok=True)
    q = state.get("reply_queue") or []
    q2 = [x for x in q if x.get("at", 0) > cut_ts]
    if len(q2) != len(q):
        state.put("reply_queue", q2)
        out["queue"] = len(q) - len(q2)
    it = state.get("intents") or {}
    if len(it) > 200:
        state.put("intents", dict(list(it.items())[-200:]))
    state.put("privacy_purge", {"t": time.time(), "removed": out})
    log(f"privacy purge: {out}")
    return out


def forget(name):
    """'data hatao <naam>' - ek vyakti ka saara record (audience, diary, queue, drafts) turant mitao."""
    n = (name or "").strip().lstrip("@").lower()
    if len(n) < 2:
        return "Naam/username likhein, jaise: data hatao @rahul_123"
    cnt = 0
    aud = state.get("audience") or {}
    keep = {k: v for k, v in aud.items() if k.split(":", 1)[-1].lstrip("@").lower() != n}
    cnt += len(aud) - len(keep)
    state.put("audience", keep)
    q = state.get("reply_queue") or []
    q2 = [x for x in q if (x.get("who") or "").lstrip("@").lower() != n]
    cnt += len(q) - len(q2)
    state.put("reply_queue", q2)
    try:
        lines = DIARY.read_text(encoding="utf-8").splitlines()
        new = []
        for x in lines:
            try:
                r = json.loads(x)
            except Exception:
                continue
            if _is_pii(r) and n in r.get("text", "").lower():
                continue
            new.append(x)
        cnt += len(lines) - len(new)
        DIARY.write_text("\n".join(new) + ("\n" if new else ""), encoding="utf-8")
    except FileNotFoundError:
        pass
    # backup mein bhi purani copy na rahe
    for f in (DATA / "backup").glob("diary-*.jsonl") if (DATA / "backup").exists() else []:
        try:
            rows = [x for x in f.read_text(encoding="utf-8").splitlines()
                    if not (n in x.lower() and any(k in x for k in ('"comment"', "jawab diya", "IG DM link", "comment jawab")))]
            f.write_text("\n".join(rows) + "\n", encoding="utf-8")
        except Exception:
            pass
    from . import diary
    diary.add("setting", f"data deletion poora (1 vyakti, {cnt} record)")
    return (f"🧹 '{name}' ka data mita diya: {cnt} record (audience, diary, queue, backup).\n"
            "Platform par uska comment hai to wo comment platform se hi hatega - hamare paas ab koi record nahi.\n"
            "Jisne maanga tha use email par likh dein: 'Aapka data hata diya gaya hai.'")


def check_site():
    """Live privacy/terms page mein zaroori baatein hain? (Meta/Google/Pinterest app review isi par tika hai)."""
    import requests
    probs = []
    for path, need in MUST.items():
        try:
            r = requests.get(SITE + path, timeout=25, headers={"User-Agent": "SabhisaabBot-PolicyCheck/1.7"})
            if r.status_code != 200:
                probs.append(f"{path} khul nahi raha (HTTP {r.status_code})")
                continue
            miss = [x for x in need if x not in r.text]
            if miss:
                probs.append(f"{path} mein ye nahi mila: {', '.join(miss)} (nayi policy ZIP deploy hui?)")
        except Exception as e:
            probs.append(f"{path} jaanch nahi hui: {str(e)[:60]}")
    return probs


def report():
    p = state.get("privacy_purge") or {}
    aud = state.get("audience") or {}
    probs = check_site()
    when = datetime.datetime.fromtimestamp(p["t"]).strftime("%d %b %H:%M") if p.get("t") else "abhi tak nahi"
    return ("🔐 Privacy haal\n"
            f"• Commenter record: {len(aud)} (sirf pichhle {retain()} din, har platform alag - jodkar track nahi)\n"
            f"• Aakhri auto-safai: {when} | hataya: {p.get('removed', {})}\n"
            f"• Website policy page: " + ("✅ sab zaroori baatein maujood" if not probs else "❌ " + "; ".join(probs)) +
            "\n• Kisi ne data hatane ko kaha? Likhein: data hatao <naam ya @username>")
