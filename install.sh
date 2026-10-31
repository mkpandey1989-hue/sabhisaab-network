#!/bin/bash
# Sabhisaab Network - install / update. Sirf ~/sabhisaab-network + apni service (sabhinet) ko chhedta hai.
# Chowkidar, trading services, system settings: kuch nahi chhedta.
set -euo pipefail
B=/home/ubuntu/sabhisaab-network
SRC="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
VER="$(cat "$SRC/VERSION")"
echo "== Sabhisaab Network v$VER install =="

echo "-- 1/7 System libraries (Hindi akshar, emoji)"
sudo apt-get install -y -q libraqm0 fonts-noto-color-emoji libarchive-tools >/dev/null
# v1.8.1: website audit (JS jaanch) ke liye node
command -v node >/dev/null 2>&1 || sudo apt-get install -y -q nodejs >/dev/null || echo "   (nodejs install nahi hua - audit sirf WARNING dega)"
# v2.0: npm (calculator test ke liye jsdom + seedha Cloudflare deploy ke liye wrangler - bot pehli zaroorat par khud laata hai)
command -v npm >/dev/null 2>&1 || sudo apt-get install -y -q npm >/dev/null || echo "   (npm nahi - seedha deploy GitHub Actions se hoga)"

echo "-- 2/7 Code copy (purana app backup)"
mkdir -p "$B/data/backup" "$B/secrets" && chmod 700 "$B/secrets"
if [ -d "$B/app" ] && [ -n "$(ls -A "$B/app" 2>/dev/null)" ]; then
  tar czf "$B/data/backup/app-$(date +%Y%m%d-%H%M%S).tgz" -C "$B" app VERSION install.sh 2>/dev/null || \
  tar czf "$B/data/backup/app-$(date +%Y%m%d-%H%M%S).tgz" -C "$B" app VERSION
  ls -1t "$B"/data/backup/app-*.tgz | tail -n +2 | xargs -r rm -f
fi
rm -rf "$B/app.new"; cp -r "$SRC/app" "$B/app.new"
# v1.7: GitHub copy mein badi/png file nahi hoti - VM par pehle se rakhi asset/bank file kabhi na mitein
for sub in assets scripts/bank; do
  if [ -d "$B/app/$sub" ]; then mkdir -p "$B/app.new/$sub"; cp -rn "$B/app/$sub/." "$B/app.new/$sub/" 2>/dev/null || true; fi
done
rm -rf "$B/app"; mv "$B/app.new" "$B/app"
cp "$SRC/VERSION" "$B/VERSION"; cp "$SRC/install.sh" "$B/install.sh"; cp "$SRC/README.md" "$B/README.md" 2>/dev/null || true; rm -rf "$B/docs"; cp -r "$SRC/docs" "$B/docs" 2>/dev/null || true
find "$B/app" -name "__pycache__" -prune -exec rm -rf {} +

echo "-- 3/7 Python packages"
nice -n 19 uv pip install -q --python "$B/venv/bin/python" requests pillow soundfile numpy matplotlib google-auth google-auth-httplib2 google-api-python-client

echo "-- 4/7 Secrets (sirf pehli baar, purane bot ki settings se)"
if [ ! -f "$B/secrets/bot.env" ]; then
  grep -E '^(LISTENER_BOT_TOKEN|OWNER_CHAT_ID|GEMINI_API_KEY|GEMINI_MODEL|GITHUB_TOKEN)=' /home/ubuntu/yt-listener/listener.env > "$B/secrets/bot.env"
  echo "   bot.env bana"
fi
chmod 600 "$B"/secrets/* 2>/dev/null || true

echo "-- 5/7 Jaanch"
"$B/venv/bin/python" -c "from PIL import features; assert features.check('raqm'), 'raqm nahi mila'; print('   Hindi text: OK')"
cd "$B" && "$B/venv/bin/python" -c "import app.bot, app.pipeline, app.youtube, app.website, app.siteknow, app.upgrader, app.kb, app.seodiary, app.tasks, app.relay, app.backup; print('   Code: OK')"

echo "-- 6/7 Commands (sn-test, sn-selfcheck, sn-switch, sn-tgapi-setup)"
# v2.0 (VIKALP): local Telegram Bot API server - bot 2 GB tak file le sake (cloud API ki 20 MB seema khatam).
# my.telegram.org se api_id/api_hash chahiye. Chalana: ~/sabhisaab-network/sn-tgapi-setup <api_id> <api_hash>
cat > "$B/sn-tgapi-setup" <<'EOT'
#!/bin/bash
set -euo pipefail
[ $# -eq 2 ] || { echo "Usage: sn-tgapi-setup <api_id> <api_hash>"; exit 1; }
B=/home/ubuntu/sabhisaab-network
printf 'TELEGRAM_API_ID=%s\nTELEGRAM_API_HASH=%s\n' "$1" "$2" > "$B/secrets/tgapi.env"; chmod 600 "$B/secrets/tgapi.env"
sudo apt-get install -y -q make git zlib1g-dev libssl-dev gperf cmake g++ >/dev/null
cd /home/ubuntu && [ -d telegram-bot-api ] || git clone -q --recursive https://github.com/tdlib/telegram-bot-api.git
cd telegram-bot-api && mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release .. >/dev/null && nice -n 19 cmake --build . --target telegram-bot-api -j1
sudo install -m 755 telegram-bot-api /usr/local/bin/telegram-bot-api
mkdir -p /home/ubuntu/tgapi-data
sudo tee /etc/systemd/system/tgapi.service >/dev/null <<EOS
[Unit]
Description=Local Telegram Bot API (sabhinet 2 GB files)
After=network-online.target
[Service]
User=ubuntu
EnvironmentFile=$B/secrets/tgapi.env
ExecStart=/usr/local/bin/telegram-bot-api --local --http-ip-address=127.0.0.1 --http-port=8081 --dir=/home/ubuntu/tgapi-data --api-id=\${TELEGRAM_API_ID} --api-hash=\${TELEGRAM_API_HASH}
Restart=always
Nice=10
[Install]
WantedBy=multi-user.target
EOS
sudo systemctl daemon-reload && sudo systemctl enable --now tgapi && sleep 5
TOK=$(grep '^LISTENER_BOT_TOKEN=' $B/secrets/bot.env | cut -d= -f2)
curl -fsS "http://127.0.0.1:8081/bot$TOK/getMe" >/dev/null || { echo "Local server nahi chala - kuch nahi badla"; exit 1; }
curl -fsS "https://api.telegram.org/bot$TOK/logOut" >/dev/null || true
grep -q '^SN_TG_API=' $B/secrets/bot.env || printf 'SN_TG_API=http://127.0.0.1:8081\nSN_TG_MAX_MB=2000\n' >> $B/secrets/bot.env
sudo systemctl restart sabhinet && echo "OK: bot ab 2 GB tak file le sakta hai (10 min baad pehla message)"
EOT
cat > "$B/sn-test" <<EOT
#!/bin/bash
exec sudo systemd-run --quiet --wait --pipe --collect --slice=reels.slice --uid=ubuntu --gid=ubuntu \\
  --working-directory=$B -E HOME=/home/ubuntu -E PYTHONPATH=$B -E HF_HUB_DISABLE_TELEMETRY=1 \\
  -p Nice=10 -p OOMScoreAdjust=500 -p EnvironmentFile=$B/secrets/bot.env \\
  $B/venv/bin/python -m app.make_test "\$@"
EOT
cat > "$B/sn-selfcheck" <<EOT
#!/bin/bash
# Service chalu hone se pehle: naya code theek na ho to pichhla backup wapas
cd $B
if ! $B/venv/bin/python -c "import app.bot" 2>/dev/null; then
  L=\$(ls -1t $B/data/backup/app-*.tgz 2>/dev/null | head -1)
  if [ -n "\$L" ]; then rm -rf $B/app && tar xzf "\$L" -C $B && echo "ROLLBACK: \$L"; fi
fi
exit 0
EOT
cat > "$B/sn-switch" <<EOT
#!/bin/bash
# sn-switch on  = naya bot chalu, purana ytlistener band
# sn-switch off = wapas purana ytlistener
if [ "\$1" = "on" ]; then
  sudo systemctl disable --now ytlistener 2>/dev/null || true
  sudo systemctl enable --now sabhinet && echo "Naya bot chalu (sabhinet). Telegram dekhein."
elif [ "\$1" = "off" ]; then
  sudo systemctl disable --now sabhinet 2>/dev/null || true
  sudo systemctl enable --now ytlistener && echo "Purana ytlistener wapas chalu."
else
  systemctl is-active sabhinet ytlistener
fi
EOT
chmod 755 "$B/sn-test" "$B/sn-selfcheck" "$B/sn-switch" "$B/sn-tgapi-setup"

echo "-- 7/7 Service sabhinet (24x7, reels ki seema mein, trading ko pehla haq)"
sudo tee /etc/systemd/system/sabhinet.service >/dev/null <<EOT
[Unit]
Description=Sabhisaab Network bot (Telegram + video + YouTube)
After=network-online.target
Wants=network-online.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=$B
EnvironmentFile=$B/secrets/bot.env
Environment=PYTHONPATH=$B HOME=/home/ubuntu HF_HUB_DISABLE_TELEMETRY=1 PYTHONUNBUFFERED=1
ExecStartPre=$B/sn-selfcheck
ExecStart=$B/venv/bin/python -m app.bot
Slice=reels.slice
Nice=10
OOMScoreAdjust=500
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
EOT
sudo systemctl daemon-reload
if [ -z "${SN_FROM_BOT:-}" ] && systemctl is-active --quiet sabhinet; then
  sudo systemctl restart sabhinet && echo "   sabhinet restart (naya code)"
fi
echo "== INSTALL OK v$VER =="
if ! systemctl is-active --quiet sabhinet; then
  echo "Naya bot chalu karne ke liye:  ~/sabhisaab-network/sn-switch on"
fi
