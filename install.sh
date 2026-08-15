#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/wildanibnthahaa/Ghaits-Ai.git"
PROFILE="${GHAITS_PROFILE:-trading}"
USERNAME="ghaits-${PROFILE}"
INSTALL_DIR="/home/${USERNAME}/Ghaits-Ai"
BRIDGE_PORT="${GHAITS_BRIDGE_PORT:-18788}"
QUERY_PORT="${GHAITS_QUERY_PORT:-18789}"

echo "======================================================="
echo " Ghaits Trading Bridge + Hermes Agent - Installer"
echo " Profil: ${PROFILE} (user Linux: ${USERNAME})"
echo "======================================================="
echo ""

echo "==> [1/9] Mengecek dependency dasar (python3, git)"
if ! command -v python3 >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
  echo "    Menginstall python3 dan git..."
  sudo apt-get update -y
  sudo apt-get install -y python3 python3-venv git curl
fi

echo "==> [2/9] Membuat user Linux terisolasi: ${USERNAME}"
if id "$USERNAME" &>/dev/null; then
  echo "    User $USERNAME sudah ada, skip."
else
  sudo useradd -m -s /bin/bash "$USERNAME"
fi

echo "==> [3/9] Mengambil kode bridge dari repo (sebagai $USERNAME)"
sudo -iu "$USERNAME" bash -c "
  if [ -d '$INSTALL_DIR' ]; then
    echo '    Folder sudah ada, menarik update...'
    git -C '$INSTALL_DIR' pull
  else
    git clone '$REPO_URL' '$INSTALL_DIR'
  fi
"

echo "==> [4/9] Menyiapkan MT5 bridge sebagai systemd service"
sudo tee /etc/systemd/system/ghaits-mt5-bridge-${PROFILE}.service > /dev/null <<UNIT_EOF
[Unit]
Description=Ghaits MT5 Bridge - profil ${PROFILE}
After=network.target

[Service]
Type=simple
User=${USERNAME}
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/python3 -m integrations.mt5.bridge.server --host 127.0.0.1 --port ${BRIDGE_PORT} --query-port ${QUERY_PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT_EOF

sudo systemctl daemon-reload
sudo systemctl enable "ghaits-mt5-bridge-${PROFILE}.service"
sudo systemctl restart "ghaits-mt5-bridge-${PROFILE}.service"
sleep 2
sudo systemctl status "ghaits-mt5-bridge-${PROFILE}.service" --no-pager || true

echo "==> [5/9] Menginstall Hermes Agent (headless, sebagai $USERNAME)"
sudo -iu "$USERNAME" bash -c \
  "curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --skip-browser"

echo "==> [6/9] Menerapkan fix Telegram (pin python-telegram-bot 22.6)"
sudo -iu "$USERNAME" bash -c '
  UV_BIN="$HOME/.hermes/bin/uv"
  if [ ! -x "$UV_BIN" ]; then
    UV_BIN="$HOME/.local/bin/uv"
  fi
  cd "$HOME/.hermes/hermes-agent"
  "$UV_BIN" pip install --python venv/bin/python "python-telegram-bot[webhooks]==22.6"
' || echo "    (lewati, jalankan manual nanti kalau perlu)"

echo "==> [7/9] Menginstall MCP support di venv Hermes"
sudo -iu "$USERNAME" bash -c '
  UV_BIN="$HOME/.hermes/bin/uv"
  if [ ! -x "$UV_BIN" ]; then
    UV_BIN="$HOME/.local/bin/uv"
  fi
  cd "$HOME/.hermes/hermes-agent"
  "$UV_BIN" pip install --python venv/bin/python mcp
' || echo "    (lewati, jalankan manual nanti kalau perlu)"

echo "==> [8/9] Menyiapkan MCP server jembatan ke MT5 bridge"
sudo mkdir -p "/home/${USERNAME}/mt5-mcp"
sudo cp "${INSTALL_DIR}/integrations/mt5/mcp_server.py" "/home/${USERNAME}/mt5-mcp/mcp_server.py"
sudo chown -R "${USERNAME}:${USERNAME}" "/home/${USERNAME}/mt5-mcp"

sudo python3 - "$USERNAME" "$QUERY_PORT" <<'PYEOF'
import sys
from pathlib import Path

username = sys.argv[1]
query_port = sys.argv[2]

config_path = Path(f"/home/{username}/.hermes/config.yaml")
content = config_path.read_text(encoding="utf-8")

if "mcp_servers:" in content:
    print("    mcp_servers sudah ada di config, skip.")
else:
    addition = (
        "\nmcp_servers:\n"
        "  mt5_bridge:\n"
        f'    command: "/home/{username}/.hermes/hermes-agent/venv/bin/python"\n'
        f'    args: ["/home/{username}/mt5-mcp/mcp_server.py"]\n'
        "    env:\n"
        '      MT5_QUERY_HOST: "127.0.0.1"\n'
        f'      MT5_QUERY_PORT: "{query_port}"\n'
    )
    config_path.write_text(content + addition, encoding="utf-8")
    print("    mcp_servers berhasil ditambahkan ke config Hermes.")
PYEOF
sudo chown "${USERNAME}:${USERNAME}" "/home/${USERNAME}/.hermes/config.yaml"

echo "==> [9/9] Mengambil pairing code awal untuk EA"
PAIRING_LINE="$(sudo journalctl -u "ghaits-mt5-bridge-${PROFILE}.service" -n 20 --no-pager | grep 'pairing code' | tail -1 || true)"

echo ""
echo "======================================================="
echo " Setup otomatis selesai!"
echo "======================================================="
echo ""
echo "$PAIRING_LINE"
echo ""
echo "Sisa langkah manual:"
echo ""
echo "1. sudo -iu $USERNAME"
echo "2. hermes setup             # pilih model AI + masukin API key kamu sendiri"
echo "3. hermes gateway setup     # masukin bot token Telegram kamu (dari @BotFather)"
echo "4. hermes gateway install"
echo "5. exit"
echo "6. sudo loginctl enable-linger $USERNAME"
echo ""
echo "7. Masukkan pairing code di atas ke InpPairingCode di EA MetaTrader kamu,"
echo "   lalu detach-attach EA supaya connect."
echo ""
echo "Kalau pairing code sudah kadaluarsa (lebih dari 10 menit), minta baru dengan:"
echo "   sudo systemctl restart ghaits-mt5-bridge-${PROFILE}.service"
echo "   sudo journalctl -u ghaits-mt5-bridge-${PROFILE}.service -n 5 --no-pager"
