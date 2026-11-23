#!/bin/bash
# autostart_fix.sh  (Claude, 17 Nov 2026)
# Kaam: VM chalu hote hi aur kisi bhi crash ke baad SAB bot apne aap chalu rahein - hamesha (lifetime).
# Sirf systemd ki 2 setting badalti hai. Kisi bot ka CODE, token, trade, config - kuch NAHI chhedta.
# Koi service RESTART nahi karta (chalti trade par asar nahi) - nayi setting agli baar start hone par lagti hai.
# Purani unit file ka backup: /home/ubuntu/unit_backups/<naam>.service.<samay>
set -u
TS=$(date +%Y%m%d_%H%M%S)
BK=/home/ubuntu/unit_backups
mkdir -p "$BK"
U=/etc/systemd/system

echo "== 1) nifty-live: token refresh fail ho to bhi bot chalu ho =="
# Wajah (17 Nov 10:51 reboot): ExecStartPre refresh_token.py ne Dhan se naya token maanga, Dhan ne kaha
# 'Token can be generated once every 2 minutes' -> refresh fail -> poora bot START HI NAHI hua (auto-restart loop).
# Purana token (dhan_token.txt) agle din tak valid tha. '-' lagane se refresh fail = chetavni, bot phir bhi chalu.
# Roz ka 08:45 refresh + 08:50 restart (cron) waisa hi rahega.
F=$U/nifty-live.service
if [ -f "$F" ]; then
  cp -a "$F" "$BK/nifty-live.service.$TS"
  if grep -q '^ExecStartPre=/usr/bin/python3 /home/ubuntu/refresh_token.py' "$F"; then
    sudo sed -i 's|^ExecStartPre=/usr/bin/python3 /home/ubuntu/refresh_token.py|ExecStartPre=-/usr/bin/python3 /home/ubuntu/refresh_token.py|' "$F"
    echo "   ✅ badla: ExecStartPre=-/usr/bin/python3 /home/ubuntu/refresh_token.py"
  else
    echo "   ℹ️ pehle se theek (ya line alag hai) - kuch nahi badla"
  fi
fi

echo "== 2) delta-live: 10 crash / 5 min ke baad HAMESHA ke liye band na ho =="
# Wajah: StartLimitIntervalSec=300 + StartLimitBurst=10 -> 5 min mein 10 baar gira to systemd use 'failed' karke
# chhod deta hai (phir kabhi khud chalu nahi). StartLimitIntervalSec=0 = kabhi haar na maane. RestartSec 5 -> 10.
F=$U/delta-live.service
if [ -f "$F" ]; then
  cp -a "$F" "$BK/delta-live.service.$TS"
  sudo sed -i 's|^StartLimitIntervalSec=300$|StartLimitIntervalSec=0|; s|^StartLimitBurst=10$|# StartLimitBurst=10 (17 Nov: band - IntervalSec=0)|; s|^RestartSec=5$|RestartSec=10|' "$F"
  grep -E '^StartLimitIntervalSec|^RestartSec' "$F" | sed 's/^/   /'
fi

echo "== 3) chowkidar + sabhinet + nifty-chart: haar na maanne wali setting (agar nahi hai) =="
for S in chowkidar sabhinet nifty-chart; do
  F=$U/$S.service
  [ -f "$F" ] || continue
  if ! grep -q '^StartLimitIntervalSec=' "$F"; then
    cp -a "$F" "$BK/$S.service.$TS"
    sudo sed -i '0,/^\[Unit\]$/s//[Unit]\nStartLimitIntervalSec=0/' "$F"
    echo "   ✅ $S: StartLimitIntervalSec=0 joda"
  else
    echo "   ℹ️ $S: pehle se ($(grep '^StartLimitIntervalSec=' "$F"))"
  fi
done

sudo systemctl daemon-reload

echo "== 4) VM chalu hote hi chalu (enable) - jo band ho use enable =="
for S in sabhinet nifty-live delta-live chowkidar nifty-chart; do
  E=$(systemctl is-enabled "$S" 2>/dev/null)
  if [ "$E" != "enabled" ]; then sudo systemctl enable "$S" && echo "   ✅ $S: enable kiya"; else echo "   ✅ $S: enabled"; fi
done
systemctl is-enabled nifty-chart-watchdog.timer >/dev/null 2>&1 || true

echo "== 5) Abhi ka haal (koi restart nahi kiya) =="
for S in sabhinet nifty-live delta-live chowkidar nifty-chart; do
  printf "   %-12s %s | restart: %s\n" "$S" "$(systemctl is-active $S)" "$(systemctl show $S -p Restart --value)"
done
echo
echo "Backup: $BK  (wapas: sudo cp $BK/<naam>.service.$TS /etc/systemd/system/<naam>.service && sudo systemctl daemon-reload)"
echo "Pakka jaanch (bazaar band hone par, marzi): sudo reboot  -> 2 min baad upar wala 5) dobara: bash autostart_fix.sh"
