"""v2.4.0 (owner 4 Nov + Elite spec D/C/E/F): bina insaan ke surakshit chalne ke 5 kaam -
1) Token expiry watcher (7/3/1 din pehle alert + jo khud naya ho sake wo khud)
2) API 'contract' jaanch (roz har platform par 1 chhota READ-only call) = API badlav watcher
3) Offsite encrypted backup (roz, owner ke Telegram par; password VM par secrets/ mein, owner badal sakta)
4) Restore drill (har Ravivaar: aakhri backup kholkar jaanch)
5) Provenance ledger (har video ka font/awaaz/chitra/sawal ka srot + license)
Koi secret kabhi log/Telegram text/AI mein nahi."""
import datetime
import json
import os
import secrets as _sec
import shutil
import subprocess
import tarfile
import tempfile
import time

import requests

from . import state, tg
from .config import BASE, DATA, SECRETS, BRANDS
from .log import log

PASS_FILE = SECRETS / "backup_pass"
BK_DIR = DATA / "offsite"


# ---------------------------------------------------------------- 1) token expiry
def _days(ts):
    return round((ts - time.time()) / 86400, 1) if ts else None


def token_report():
    """[(naam, din_baaki ya None, note)]"""
    out = []
    try:
        from . import threads as TH
        for b, v in (TH._load() or {}).items():
            out.append((f"Threads {BRANDS.get(b, {}).get('name', b)}", _days(v.get("saved", 0) + 60 * 86400),
                        "20 din par bot khud naya karta hai"))
    except Exception as e:
        out.append(("Threads", None, f"jaanch nahi: {str(e)[:60]}"))
    try:
        from . import pinterest as PI
        o = (PI._cfg() or {}).get("oauth") or {}
        if o:
            out.append(("Pinterest login", _days(o.get("exp", 0)), "5 din pehle bot khud naya karta hai"))
            out.append(("Pinterest refresh (saal ka)", _days(o.get("rexp", 0)), "khatam hone par 'pinterest login' dobara"))
    except Exception as e:
        out.append(("Pinterest", None, f"jaanch nahi: {str(e)[:60]}"))
    try:
        from . import meta as M
        if M.has_token():
            b = M.brand_info(next(iter(BRANDS)))
            if b:
                tok = b["page_token"]
                d = requests.get("https://graph.facebook.com/debug_token", timeout=30,
                                 params={"input_token": tok, "access_token": tok}).json().get("data", {})
                ex = d.get("expires_at") or 0
                dax = d.get("data_access_expires_at") or 0
                out.append(("Meta page token", _days(ex) if ex else 9999, "0 = kabhi khatam nahi"))
                if dax:
                    out.append(("Meta data-access (90 din)", _days(dax), "app khol kar ek baar login karte hi naya"))
    except Exception as e:
        out.append(("Meta", None, f"jaanch nahi: {str(e)[:60]}"))
    try:
        from .website import _cf
        tok, _acc = _cf()
        if tok:
            j = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", timeout=30,
                             headers={"Authorization": f"Bearer {tok}"}).json().get("result") or {}
            exp = j.get("expires_on")
            if exp:
                out.append(("Cloudflare token", _days(datetime.datetime.fromisoformat(exp.replace("Z", "+00:00")).timestamp()), ""))
            else:
                out.append(("Cloudflare token", 9999, "bina expiry" if j.get("status") == "active" else f"haal: {j.get('status')}"))
    except Exception as e:
        out.append(("Cloudflare", None, f"jaanch nahi: {str(e)[:60]}"))
    try:
        from . import updater
        g = updater.github_token_days()
        if g is not None:
            out.append(("GitHub token", g, ""))
    except Exception:
        pass
    return out


def token_watch():
    """Roz: 7/3/1 din (ya kam) bacha ho to alert - ek din mein ek baar."""
    rep = token_report()
    bad = [(n, d, note) for n, d, note in rep if d is not None and d <= 7]
    for n, d, note in bad:
        key = f"tokw:{n}:{int(d)}"
        if int(d) in (7, 3, 1, 0) or d <= 0:
            if state.get(key) != str(datetime.date.today()):
                state.put(key, str(datetime.date.today()))
                tg.alert("red" if d <= 1 else "yellow",
                         f"🔑 {n}: {max(0, d)} din baaki. {note}\nKya karein: '🔑 Token haal' dabayein - steps wahan.")
    return rep


def token_text():
    L = ["🔑 TOKEN / LOGIN HAAL (kitne din baaki):"]
    for n, d, note in token_report():
        L.append(f"• {n}: " + ("jaanch nahi" if d is None else ("kabhi khatam nahi" if d >= 9000 else f"{d} din"))
                 + (f" - {note}" if note else ""))
    L.append("7, 3 aur 1 din pehle bot khud yaad dilata hai; jo khud naya ho sakta hai (Threads, Pinterest) wo khud karta hai.")
    return "\n".join(L)


# ---------------------------------------------------------------- 2) API contract jaanch (badlav watcher)
def contract_tests():
    """Har platform par ek chhota READ-only call. Fail = API/permission/token badla -> saaf alert."""
    res = []

    def t(name, fn):
        try:
            fn()
            res.append((name, True, ""))
        except Exception as e:
            res.append((name, False, str(e)[:120]))
    from . import youtube, meta as M, threads as TH, pinterest as PI
    for b, info in BRANDS.items():
        if youtube.has_login(b):
            t(f"YouTube {info['name']}", lambda b=b: youtube.quota_status())
    if M.has_token():
        t("Meta (FB/IG)", lambda: M.brand_info(next(iter(BRANDS))) or (_ for _ in ()).throw(RuntimeError("page nahi")))
    for b in BRANDS:
        if TH.info(b):
            def _th(b=b):
                ok, msg = TH.alive(b, max_age=0)
                if not ok:
                    raise RuntimeError(msg)
            t(f"Threads {BRANDS[b]['name']}", _th)
    if PI.connected():
        t("Pinterest", lambda: PI._req("GET", "/user_account"))
    t("Telegram", lambda: tg.call("getMe", {}))
    try:
        from .brain import _models
        t("Gemini model list", _models)
    except Exception:
        pass
    state.put("contract_last", {"t": time.strftime("%Y-%m-%d %H:%M"), "res": res})
    bad = [r for r in res if not r[1]]
    if bad:
        tg.alert("yellow", "🧪 ROZ KI API JAANCH - in par dikkat (token/permission/API badla ho sakta hai):\n" +
                 "\n".join(f"• {n}: {e}" for n, _ok, e in bad[:8]) + "\nKya karein: '🔑 Token haal' ya login dobara.")
    return res


# ---------------------------------------------------------------- 3) offsite encrypted backup
def _password():
    if not PASS_FILE.exists():
        PASS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PASS_FILE.write_text(_sec.token_urlsafe(24))
        os.chmod(PASS_FILE, 0o600)
        state.put("bk_pass_new", True)
    return PASS_FILE


def set_password(new):
    new = (new or "").strip()
    if len(new) < 10:
        return "❌ Password kam se kam 10 akshar ka ho."
    _password()
    PASS_FILE.write_text(new)
    os.chmod(PASS_FILE, 0o600)
    state.put("bk_pass_changed", time.strftime("%Y-%m-%d %H:%M"))
    return "✅ Backup password badal gaya. Aage ke backup naye password se banenge (purane purane se khulenge)."


WORDS = ("pahad", "nadi", "suraj", "chanda", "hisaab", "kheti", "barish", "taara", "mitti", "jharna", "basant", "kisan", "deodar",
         "himal", "gangaa", "chidiya", "baadal", "dhoop", "pagdandi", "ghanti")


def new_readable_password():
    """Yaad rakhne layak par mazboot: 4 shabd + 4 ank (jaise pahad-suraj-mitti-taara-4821) - ~40 bit+."""
    return "-".join(_sec.choice(WORDS) for _ in range(4)) + "-" + str(_sec.randbelow(9000) + 1000)


def reset_password():
    """v2.7.1 (owner: 'backup password save nahi hua tha'): naya padhne-layak password + turant naya backup usi se.
    Purane backup purane password se hi khulenge (VM par purana 'backup password' se dekh sakte the - ab ye naya)."""
    pw = new_readable_password()
    msg = set_password(pw)
    state.put("bk_pass_saved", False)
    ok = False
    try:
        ok = bool(make_backup(send=True))
    except Exception as e:
        log(f"reset backup: {e}")
    return pw, msg + ("\n💾 Naye password se taaza backup bana aur aapke Telegram par bheja." if ok else "\n⚠️ Naya backup abhi nahi bana - raat ko apne aap banega.")


def show_password():
    return PASS_FILE.read_text().strip() if PASS_FILE.exists() else ""


BK_ITEMS = ["data/state.json", "data/learn.json", "data/diary.jsonl", "data/qbank.json", "data/keywords.json",
            "data/provenance.jsonl", "secrets", "VERSION"]


def make_backup(send=True):
    """state + seekh + diary + sawal-bank + secrets -> tar.gz -> AES-256 (openssl, pbkdf2) -> owner ke Telegram (offsite)."""
    BK_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M")
    raw = BK_DIR / f"sn_backup_{stamp}.tar.gz"
    with tarfile.open(raw, "w:gz") as tf:
        for it in BK_ITEMS:
            p = BASE / it
            if p.exists():
                tf.add(p, arcname=it)
    enc = BK_DIR / f"sn_backup_{stamp}.tar.gz.enc"
    r = subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt",
                        "-in", str(raw), "-out", str(enc), "-pass", f"file:{_password()}"], capture_output=True, text=True, timeout=300)
    raw.unlink(missing_ok=True)
    if r.returncode != 0 or not enc.exists():
        tg.alert("red", "💾 Offsite backup nahi bana: " + (r.stderr or "")[-150:])
        return None
    os.chmod(enc, 0o600)
    for old in sorted(BK_DIR.glob("sn_backup_*.enc"))[:-7]:          # VM par aakhri 7
        old.unlink(missing_ok=True)
    sent = False
    if send and enc.stat().st_size < 45e6:
        try:
            with open(enc, "rb") as fh:
                tg.call("sendDocument", {"chat_id": tg._chat(), "disable_notification": "true",
                                         "caption": f"💾 Roz ka encrypted backup {stamp} (password VM par; 'backup password' se dekhein/badlein). "
                                                    "Ise rakhe rahein - VM udne par isi se sab wapas."}, {"document": fh})
            sent = True
        except Exception as e:
            log(f"backup send: {e}")
    state.put("bk_last", {"t": stamp, "size_kb": enc.stat().st_size // 1024, "sent": sent})
    if state.get("bk_pass_new"):                   # pehli baar: password ek baar aapko (5 min baad message khud mite)
        state.put("bk_pass_new", False)
        try:
            import threading
            r_ = tg.say(f"🔐 NAYA BACKUP PASSWORD (ek baar - abhi kahin surakshit likh lein): {show_password()}\n"
                        "Badalna ho: 'backup password badlo <naya>'. Ye message 5 min mein khud mitega.")
            mid = (r_ or {}).get("message_id") or ((r_ or {}).get("result") or {}).get("message_id")
            if mid:
                threading.Timer(300, lambda: tg.call("deleteMessage", {"chat_id": tg._chat(), "message_id": mid})).start()
        except Exception as e:
            log(f"pass notify: {e}")
    return enc


def restore_drill():
    """Har Ravivaar: aakhri backup ko kholkar jaancho (state JSON padhta hai? secrets hain?). Kuch badalta nahi."""
    files = sorted(BK_DIR.glob("sn_backup_*.enc"))
    if not files:
        make_backup(send=False)
        files = sorted(BK_DIR.glob("sn_backup_*.enc"))
    if not files:
        return "❌ Koi backup nahi mila"
    f = files[-1]
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "b.tar.gz")
        r = subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-in", str(f), "-out", out,
                            "-pass", f"file:{_password()}"], capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            msg = "❌ Restore drill: backup password se nahi khula (password badla ho to purana backup purane se khulega)"
        else:
            with tarfile.open(out) as tf:
                names = tf.getnames()
                tf.extractall(td, filter="data") if hasattr(tarfile, "data_filter") else tf.extractall(td)
            ok_state = False
            try:
                json.loads(open(os.path.join(td, "data/state.json"), encoding="utf-8").read())
                ok_state = True
            except Exception:
                pass
            nsec = len([n for n in names if n.startswith("secrets/")])
            msg = (f"{'✅' if ok_state and nsec else '⚠'} Restore drill ({f.name}): khula ✅ | state.json {'theek' if ok_state else 'NAHI'}"
                   f" | secrets file {nsec} | kul {len(names)} cheez")
    state.put("bk_drill", {"t": time.strftime("%Y-%m-%d %H:%M"), "msg": msg})
    return msg


def backup_text():
    b, d = state.get("bk_last") or {}, state.get("bk_drill") or {}
    return ("💾 OFFSITE BACKUP:\n"
            f"• Aakhri: {b.get('t', '-')} ({b.get('size_kb', 0)} KB) | Telegram par: {'haan' if b.get('sent') else 'nahi'}\n"
            f"• Restore drill: {d.get('t', '-')} {d.get('msg', '')}\n"
            "• Kya: state, seekh, diary, sawal-bank, secrets (AES-256 encrypted)\n"
            "• Hukum: 'backup abhi' | 'backup password' (dekho) | 'backup password badlo <naya>' | 'restore drill'")


# ---------------------------------------------------------------- 5) provenance ledger
LICENSES = {"font": "Noto Sans / Noto Sans Devanagari (SIL OFL 1.1) + Baloo 2 (SIL OFL 1.1)",
            "tts": "Kokoro-82M (Apache-2.0) - apni VM par",
            "sfx": "apne banaye (numpy) - koi bahari sound nahi",
            "music": "koi bahari gaana nahi (apna banaya halka pad)"}


def provenance(meta, img_source=""):
    """Har video ka srot-record (meta folder mein + data/provenance.jsonl). Copyright sawal par saboot."""
    try:
        src = meta.get("puzzle_kind") or meta.get("source") or "gemini"
        rec = {"t": time.strftime("%Y-%m-%d %H:%M"), "brand": meta.get("brand"), "title": meta.get("title", "")[:90],
               "script": {"source": src, "fact_check": meta.get("audit_notes", ""), "question": meta.get("puzzle_q", "")[:120]},
               "visual": img_source or ("blender3d (apna)" if meta.get("img3d") else "apna design (PIL)"),
               "ai_label": True, **LICENSES}
        d = os.path.dirname(meta.get("video", "")) or str(DATA)
        with open(os.path.join(d, "provenance.json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
        with open(DATA / "provenance.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec
    except Exception as e:
        log(f"provenance: {e}")
        return None


def cleanup_offsite():
    shutil.rmtree(BK_DIR / "tmp", ignore_errors=True)
