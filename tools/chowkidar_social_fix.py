#!/usr/bin/env python3
"""chowkidar_social_fix.py (Claude, 17 Nov 2026) - chowkidar ka '6-Social Track' button sach dikhaye.

Pehle: sabhinet ke log mein shabd dhoondh kar andaaza (Posts=0, Pinterest Errors=2 - dono galat; Pinterest ka '⏸' roz 2 pin
ki spam-seema hai, galti nahi). Ab: sabhinet ki apni pakki ginti padhta hai (data/state.json: platform_health + posted_log
+ uploads) - wahi jo sabhinet ke 'report table' / HEALTH.md mein hai. Sirf PADHTA hai.

Kya karta hai: ~/chowkidar/chowkidar.py (+ chowkidar_pro.py agar same ho) mein SIRF function sabhisaab_omnichannel_audit
badalta hai. Backup: ~/chowkidar/<file>.<samay>.bak. py_compile pass hone par hi likhta hai, phir chowkidar restart
(chowkidar sirf nigrani bot hai - trading/sabhinet par koi asar nahi). Dobara chalane par kuch nahi badalta.
"""
import os, sys, time, shutil, py_compile, subprocess

NEW = r'''def sabhisaab_omnichannel_audit():
    """v2 (17 Nov 2026, Claude): sabhinet ki apni pakki ginti (data/state.json) - log se andaaza nahi."""
    import json as _j
    base_d = HOME + "/sabhisaab-network"
    L = ["🌐 SABHISAAB CHANNEL HAAL (sabhinet ki apni ginti se)"]
    L.append("• Service: %s" % ("✅ ACTIVE" if active("sabhinet") else "❌ " + svc_state("sabhinet")))
    try:
        st = _j.load(open(base_d + "/data/state.json", encoding="utf-8"))
    except Exception as e:
        L.append("⚠ state.json nahi padh paya (%s) - sabhinet mein '🩺 Sab theek?' dekhein" % str(e)[:60])
        return "\n".join(L)
    today = datetime.date.today().isoformat()
    since = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    up = st.get("uploads") or {}
    L.append("\n🎬 YouTube video: aaj %s | kal %s" % (up.get(today, 0), up.get(since, 0)))
    posted = [p for p in (st.get("posted_log") or []) if str(p.get("date", "")) >= since]
    cnt = {}
    for p in posted:
        for pf in (p.get("ids") or {}):
            cnt[pf] = cnt.get(pf, 0) + 1
    L.append("📤 Pichhle 24-48 ghante mein post (platform: video): " +
             (", ".join("%s %d" % (k, v) for k, v in sorted(cnt.items(), key=lambda x: -x[1])) or "abhi koi nahi"))
    ph = st.get("platform_health") or {}
    bad, wait = [], []
    for k, v in sorted(ph.items()):
        if not isinstance(v, dict):
            continue
        if not v.get("ok", True):
            bad.append("❌ %s (%s): %s" % (k, v.get("t", ""), str(v.get("err", ""))[:90]))
        elif v.get("wait"):
            wait.append(k)
    L.append("\n📡 Platform haal:")
    L += bad or ["✅ Koi platform ruka nahi"]
    if wait:
        L.append("⏸ Jaanboojh kar ruka (spam-seema / manzoori, galti NAHI): " + ", ".join(sorted(set(w.split(":")[-1] for w in wait))))
    repo = base_d + "/data/site_repo"
    if os.path.isdir(repo):
        rc, last_c = sh("cd %s && git log -1 --format='%%cr' 2>/dev/null" % q(repo))
        L.append("\n🌍 Website: aakhri badlaav %s" % (last_c.strip() or "N/A"))
    L.append("\nPoori report: sabhinet mein 'report table 7 din' | '🩺 Sab theek?' (token/login wahi jaanchta hai)")
    return "\n".join(L)
'''

def patch(fp):
    src = open(fp, encoding="utf-8").read()
    a = src.find("def sabhisaab_omnichannel_audit():")
    b = src.find("def sabhisaab_replies_audit():")
    if a < 0 or b < 0 or b < a:
        return "❌ %s: function nahi mila - kuch nahi badla" % fp
    if "sabhinet ki apni pakki ginti (data/state.json)" in src[a:b]:
        return "ℹ️ %s: pehle se naya - kuch nahi badla" % fp
    new = src[:a] + NEW + src[b:]
    tmp = fp + ".new"
    open(tmp, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(tmp, doraise=True)
    except Exception as e:
        os.remove(tmp)
        return "❌ %s: compile fail (%s) - kuch nahi badla" % (fp, str(e)[:120])
    bak = "%s.%s.bak" % (fp, time.strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(fp, bak)
    os.replace(tmp, fp)
    return "✅ %s badla (backup: %s)" % (fp, bak)

d = os.path.expanduser("~/chowkidar")
main = os.path.join(d, "chowkidar.py")
pro = os.path.join(d, "chowkidar_pro.py")
same = os.path.exists(pro) and open(pro, "rb").read() == open(main, "rb").read()
out = [patch(main)]
if same:
    out.append(patch(pro))
print("\n".join(out))
if any(x.startswith("✅") for x in out):
    r = subprocess.run(["sudo", "systemctl", "restart", "chowkidar"], capture_output=True, text=True)
    time.sleep(3)
    st = subprocess.run(["systemctl", "is-active", "chowkidar"], capture_output=True, text=True).stdout.strip()
    print("chowkidar restart: %s" % st)
    if st != "active":
        print("⚠ chowkidar chalu nahi hua - backup wapas lagao: cp <backup> ~/chowkidar/chowkidar.py && sudo systemctl restart chowkidar")
