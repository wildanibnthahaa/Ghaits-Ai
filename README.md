# Ghaits AI Trading Bridge

Bridge penghubung antara MetaTrader 5 (EA) dan Hermes Agent (AI assistant) lewat Telegram.

## Isi repo
- integrations/mt5/bridge/ - server bridge, menerima koneksi dari EA MetaTrader
- integrations/mt5/mcp_server.py - jembatan Hermes ke data MT5 (saldo, posisi, order, pairing code)
- integrations/mt5/ea/ - tempat file .mq5 (diupload manual admin)
- install.sh - installer sekali-jalan
- templates/SOUL_trading.md - kepribadian dan alur kerja asisten trading Hermes

## Cara Install
1. Siapkan VPS Ubuntu/Debian kosong, akses sudo.
2. Jalankan:
   curl -fsSL https://raw.githubusercontent.com/wildanibnthahaa/Ghaits-Ai/main/install.sh -o install.sh
   bash install.sh
3. Ikuti instruksi terakhir untuk isi API key model AI dan bot Telegram sendiri.

## Upload File EA
Minta file .mq5 dari admin, taruh di folder MQL5/Experts/ MetaTrader. Minta pairing code lewat chat Telegram ke bot kamu (ketik "connect").
