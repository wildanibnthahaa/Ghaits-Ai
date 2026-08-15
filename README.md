<div align="center">

# ⚡ Ghaits x Hermes Agent

### Autonomous AI Trading Infrastructure for MetaTrader 5

**MetaTrader 5 · Ghaits Bridge · MCP · Hermes Agent · Telegram**

<br>

[![MetaTrader 5](https://img.shields.io/badge/MetaTrader%205-Bridge-00a86b?style=for-the-badge&logo=metatrader5&logoColor=white)](https://www.metatrader5.com/)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-7c3aed?style=for-the-badge)](https://github.com/NousResearch/hermes-agent)
[![MCP](https://img.shields.io/badge/MCP-Integrated-2563eb?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Telegram](https://img.shields.io/badge/Telegram-Gateway-229ED9?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org/)

</div>

---

## 🧠 What is Ghaits AI?

**Ghaits AI** is a self-hosted AI trading infrastructure that connects **MetaTrader 5** with **Hermes Agent** through a controlled bridge and MCP layer.

Instead of allowing the AI layer to communicate directly with MetaTrader, Ghaits introduces an isolated bridge between the trading terminal and the agent.

This creates a modular architecture where:

- MetaTrader handles market and execution connectivity.
- Ghaits Bridge handles the MT5 connection.
- MCP exposes controlled MT5 capabilities to Hermes.
- Hermes provides the AI agent layer.
- Telegram provides the human ↔ AI interface.

> **Give an AI agent controlled access to a real trading environment without turning the trading terminal itself into the AI runtime.**

---

## 🏗️ Architecture


                         ┌──────────────────────┐
                         │      TELEGRAM        │
                         │   Human ↔ AI Control │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    HERMES AGENT      │
                         │    AI Agent Layer    │
                         └──────────┬───────────┘
                                    │
                                    │ MCP
                                    ▼
                         ┌──────────────────────┐
                         │      MCP SERVER      │
                         │   MT5 Tool Gateway   │
                         └──────────┬───────────┘
                                    │
                                    │ Local Query
                                    ▼
                         ┌──────────────────────┐
                         │   GHAITS MT5 BRIDGE  │
                         │                      │
                         │  Bridge: 18788       │
                         │  Query : 18789       │
                         └──────────┬───────────┘
                                    │
                                    │ Pairing
                                    ▼
                         ┌──────────────────────┐
                         │     META TRADER 5    │
                         │        + EA          │
                         └──────────────────────┘


---

✨ Core Features

Component	Purpose
```
🤖 Hermes Agent	AI agent runtime
📡 Ghaits Bridge	MT5 ↔ VPS communication layer
🔌 MCP Server	Exposes MT5 capabilities to Hermes
💬 Telegram	Human ↔ AI communication
🔐 Linux Isolation	Dedicated user per profile
⚙️ systemd	Persistent bridge service
🔗 Pairing Code	Controlled EA ↔ Bridge authentication
📊 MT5 Data	Account, positions, orders and related data
🧩 Profiles	Multiple isolated Ghaits environments
```


---

### 🚀 One-Command Installation

> Ubuntu/Debian VPS with sudo access required.

```

No manual download.

No chmod.

No separate bash install.sh.

Just run:

curl -fsSL https://raw.githubusercontent.com/wildanibnthahaa/Ghaits-Ai/main/install.sh | bash

The installer automatically:

1. Checks basic dependencies.

2. Creates the isolated Linux user ghaits-trading.

3. Clones or updates the Ghaits repository.

4. Creates and starts the MT5 Bridge systemd service.

5. Installs Hermes Agent.

6. Applies the Telegram dependency fix.

7. Installs MCP support.

8. Configures the MT5 MCP server.

9. Installs the trading SOUL.md template.

10. Generates and displays the initial EA pairing code.



Default Linux user:
ghaits-trading

Default bridge service:
ghaits-mt5-bridge-trading.service

Default ports:
Bridge : 127.0.0.1:18788
Query  : 127.0.0.1:18789

```
---

### 🛠️ Finish Hermes Configuration

The infrastructure is installed automatically.

Your AI-provider and Telegram credentials remain under your control.

Enter the trading environment:
```
sudo -iu ghaits-trading

Configure Hermes:

hermes setup

Configure Telegram:

hermes gateway setup
hermes gateway install

Enable lingering so user services can continue after logout:

exit
sudo loginctl enable-linger ghaits-trading
```
> 🔐 Keep API keys and Telegram bot tokens private. Never commit credentials into this repository.




---

### 📡 MetaTrader 5 Setup

Ghaits communicates with MetaTrader 5 through an Expert Advisor.
```
1. Install the EA

Place the .mq5 Expert Advisor inside:

MQL5/Experts/

Then compile it using MetaEditor.

2. Attach the EA

Open MetaTrader 5 and attach the Ghaits EA to the intended chart.

Configure the required inputs.

3. Pair the EA

The installer generates a temporary pairing code.

Enter the code into:

InpPairingCode

Then detach and re-attach the EA so it reconnects to the bridge.

Pairing Code Expired?

Generate a fresh pairing code:

sudo systemctl restart ghaits-mt5-bridge-trading.service

Then:

sudo journalctl \
  -u ghaits-mt5-bridge-trading.service \
  -n 5 \
  --no-pager

```
---

### ⚙️ Profiles
```
Ghaits supports isolated installation profiles through GHAITS_PROFILE.

The default profile is:

GHAITS_PROFILE=trading

Which creates:

Linux user
└── ghaits-trading

systemd
└── ghaits-mt5-bridge-trading.service

You can create another isolated profile:

GHAITS_PROFILE=demo \
curl -fsSL https://raw.githubusercontent.com/wildanibnthahaa/Ghaits-Ai/main/install.sh | bash

This produces:

ghaits-demo
ghaits-mt5-bridge-demo.service

Bridge ports can also be customized:

GHAITS_BRIDGE_PORT=18788
GHAITS_QUERY_PORT=18789

```
---

### 🔍 Useful Commands
```
Check bridge status

sudo systemctl status ghaits-mt5-bridge-trading.service

Restart bridge

sudo systemctl restart ghaits-mt5-bridge-trading.service

Stop bridge

sudo systemctl stop ghaits-mt5-bridge-trading.service

Start bridge

sudo systemctl start ghaits-mt5-bridge-trading.service

Live logs

sudo journalctl \
  -u ghaits-mt5-bridge-trading.service \
  -f

Recent logs

sudo journalctl \
  -u ghaits-mt5-bridge-trading.service \
  -n 50 \
  --no-pager

Enter Ghaits environment

sudo -iu ghaits-trading

```
---

## 📁 Repository Structure
```
Ghaits-Ai/
│
├── integrations/
│   └── mt5/
│       │
│       ├── bridge/
│       │   └── server.py
│       │       └── MT5 bridge server
│       │
│       ├── mcp_server.py
│       │   └── Hermes ↔ MT5 MCP gateway
│       │
│       ├── ea/
│       │   └── MetaTrader 5 Expert Advisors
│       │
│       └── report/
│           └── Reporting components
│
├── templates/
│   └── SOUL_trading.md
│       └── Trading agent behavior template
│
├── install.sh
│   └── One-command VPS installer
│
└── README.md
```

---

## 🔄 Agent Workflow

Ghaits is designed around an agent workflow:
```
┌──────────────┐
│    MARKET    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    ANALYZE   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    DECIDE    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    EXECUTE   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    MONITOR   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│     LEARN    │
└──────┬───────┘
       │
       └──────────────────┐
                          │
                          ▼
                       ANALYZE
```
The architecture separates:

Trading Terminal
       ≠
AI Runtime
       ≠
Human Interface

Each layer has a specific responsibility.


---

### 🔐 Security Model
```
Ghaits is designed around isolation.

Each profile can have its own:

Linux user
    ↓
Ghaits installation
    ↓
Hermes environment
    ↓
MT5 Bridge service
    ↓
MCP configuration

The bridge listens locally by default:

127.0.0.1

This helps avoid exposing the MT5 query interface directly to the public internet.

> Always review your firewall, credentials, Telegram bot permissions, AI-provider permissions, and execution controls before connecting a live account.

```


---

⚠️ Risk Disclaimer

Ghaits AI is software infrastructure for automated trading workflows.

It:
```
does not guarantee profits;

is not financial advice;

can make incorrect decisions;

can encounter software, network, broker, or model failures.


Before using a live account:

Test on demo/paper first.

Verify the complete EA ↔ Bridge connection.

Verify pairing.

Verify AI model configuration.

Verify execution behavior.

Verify independent risk controls.

Start with minimal exposure.

```
Never assume an AI agent is inherently safe simply because the infrastructure is automated.


---

🗺️ Roadmap

Infrastructure

[x] MT5 Bridge

[x] Hermes Agent integration

[x] MCP integration

[x] Telegram gateway integration

[x] One-command installer

[x] Linux profile isolation

[x] Pairing-code workflow


Coming Next

[ ] Improved installation diagnostics

[ ] Automated EA distribution

[ ] EA version management

[ ] Multi-profile management

[ ] Health monitoring

[ ] Monitoring dashboard

[ ] Better deployment tooling

[ ] Production deployment documentation



---

📌 Project Status

Ghaits AI is actively evolving.

The current focus is the core infrastructure:
```
MetaTrader 5
      ↕
Ghaits Bridge
      ↕
MCP
      ↕
Hermes Agent
      ↕
Telegram
```
The repository is intended to evolve into a modular trading-agent infrastructure that can be deployed repeatedly across isolated environments.


---

<div align="center">⚡ Ghaits AI

Build the infrastructure.
Connect the agent.
Control the execution.

<br>MetaTrader 5 · Ghaits Bridge · MCP · Hermes Agent · Telegram

</div>
```
