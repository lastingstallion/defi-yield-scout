# DeFi Yield Scout — CROO Agent

A callable AI agent that scans DeFi protocols for yield farming opportunities, alpha leaks, and risk analysis. Built on the [CROO Agent Protocol (CAP)](https://croo.network).

## What It Does

DeFi Yield Scout monitors **500+ DeFi pools** across 20+ chains in real-time:

- 🔍 **Yield Discovery** — Find the highest APY pools with acceptable risk
- 📊 **TVL Analysis** — Track Total Value Locked trends and capital flows  
- ⚠️ **Risk Scoring** — Protocol risk assessment based on TVL, age, audits
- 🏗️ **New Pool Alerts** — Detect newly launched pools before they trend
- 📈 **Trending Protocols** — Identify momentum shifts across DeFi

## Architecture

```
┌─────────────────────────────────────────────┐
│           DeFi Yield Scout Agent            │
├─────────────────────────────────────────────┤
│  CROO CAP SDK (AgentClient)                │
│  ├── WebSocket event stream                 │
│  ├── Order negotiation + delivery           │
│  └── USDC payment settlement (on-chain)     │
├─────────────────────────────────────────────┤
│  DeFi Intelligence Engine                   │
│  ├── DeFiLlama API (yields, TVL, protocols) │
│  ├── Multi-chain aggregation                │
│  ├── Risk scoring algorithm                 │
│  └── Trend detection                        │
├─────────────────────────────────────────────┤
│  Delivery                                   │
│  ├── Structured JSON analysis               │
│  ├── Human-readable reports                 │
│  └── File attachments (CSV exports)         │
└─────────────────────────────────────────────┘
```

## Quick Start

```bash
# Install dependencies
pip install croo-sdk httpx

# Set environment variables
export CROO_API_URL="https://api.croo.network"
export CROO_WS_URL="wss://api.croo.network/ws"
export CROO_SDK_KEY="croo_sk_your_key_here"

# Run the agent
python src/agent.py
```

## Service Offerings

| Service | Description | Price |
|---------|-------------|-------|
| `yield-scan` | Top yield opportunities across chains | $0.50 USDC |
| `risk-analysis` | Deep risk assessment of a protocol | $1.00 USDC |
| `new-pools` | Newly launched pools (< 7 days) | $0.75 USDC |
| `trending` | Trending protocols by TVL change | $0.50 USDC |
| `full-report` | Comprehensive DeFi intelligence report | $2.00 USDC |

## SDK Integration

Uses [CROO Python SDK](https://github.com/CROO-Network/python-sdk):

- `AgentClient` — authenticated via SDK-Key
- WebSocket event streaming for real-time order handling
- On-chain payment settlement via CAP
- File upload for detailed reports

## Tech Stack

- **Python 3.10+** — async agent runtime
- **croo-sdk** — CROO Agent Protocol integration
- **httpx** — async HTTP client for DeFiLlama API
- **Base Chain** — payment settlement (USDC)

## License

MIT
