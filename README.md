# 🤖 Alpaca AI Trading Agent

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white">
  <img alt="Alpaca" src="https://img.shields.io/badge/Alpaca-Trading%20API-FFD200?logo=alpaca">
  <img alt="MCP" src="https://img.shields.io/badge/MCP-74%20official%20tools-6E56CF">
  <img alt="Claude" src="https://img.shields.io/badge/brain-Claude%20(tool--calling)-D97757">
  <img alt="Paper trading" src="https://img.shields.io/badge/mode-paper%20trading%20only-2ea043">
</p>

Autonomous AI trading agent for the **[Alpaca AI Trading Agents Hackathon](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon)** (lablab.ai).

An LLM (**Claude**) acts as the *brain* of a trading agent: it inspects the account, reads technical indicators **and** news sentiment, then decides and executes trades autonomously on an **Alpaca paper account** — explaining its reasoning for every decision. It can drive the **official Alpaca MCP Server (74 tools)** for stocks, 24/7 crypto, and options.

> ⚠️ **Paper trading only** (virtual money). No live funds. Not financial advice.

---

## 🎬 Demo video

▶️ **[`video/alpaca_demo.mp4`](video/alpaca_demo.mp4)** — 2-minute walkthrough with English voice-over: the agentic loop, a live NVDA/BTC decision, and the backtest results. Narration transcript in [`video/narration.txt`](video/narration.txt).

---

## ✨ Highlights

- **True agentic loop** — Claude drives via **tool-calling** (OpenAI-compatible function calling), not a hardcoded strategy. It *chooses* which tools to call and when.
- **🔌 Official Alpaca MCP Server** — `--mcp` mode connects Claude to the **official [alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server)** (**74 tools**: stocks, **crypto 24/7**, **options chains**, watchlists, portfolio history, market movers). *This is the hackathon's core theme.*
- **Hybrid signal** — combines **technical analysis** (RSI, SMA20/50, momentum) with **LLM news-sentiment** scoring.
- **📈 Backtesting engine** — validates the strategy on historical data with real metrics: total return, CAGR, win-rate, max drawdown, **Sharpe ratio**, and a buy & hold baseline.
- **Explainable** — every decision comes with written reasoning (logged) — great for demo & judging.
- **Risk guardrails** — hard per-order notional cap; the agent adapts when an order is rejected instead of crashing.
- **Autonomous scheduler** — runs on a schedule, respects market hours.
- **Live dashboard** — CLI + dark-themed HTML portfolio report.

---

## 🏆 How this maps to the judging criteria

| Criterion | How this project delivers |
|-----------|---------------------------|
| **Application of Technology** | Genuine agentic tool-calling loop over **both** a local tool layer and the **official Alpaca MCP Server (74 tools)** — stocks, crypto, options — the exact ecosystem the hackathon is built around. |
| **Presentation** | 2-min voice-over [demo video](video/alpaca_demo.mp4), clean README with architecture diagram, and fully explainable per-decision reasoning. |
| **Business Value** | A disciplined, risk-capped agent that blends technicals + news sentiment and is **backtested** — not a black box; you can see *when* it wins and *when* it holds. |
| **Originality** | LLM reasoning is the strategy engine (not just a wrapper): it sizes positions under risk limits and can override raw signals, e.g. **HOLD** an overbought parabolic asset. |

---

## ⚡ Quick start

```bash
# 1. enter project & create venv
cd alpaca-agent
uv venv .venv
source .venv/Scripts/activate    # Windows (git-bash) | Linux/mac: source .venv/bin/activate
uv pip install -r requirements.txt

# 2. configure credentials
cp .env.example .env             # then edit .env with your Alpaca PAPER keys

# 3. run one autonomous decision cycle
python agent.py --symbols AAPL,NVDA,MSFT --force
```

`.env` fields:

```
APCA_API_KEY_ID=...              # Alpaca PAPER key
APCA_API_SECRET_KEY=...
APCA_API_BASE_URL=https://paper-api.alpaca.markets

LLM_BASE_URL=https://gorouter.app/v1   # OpenAI-compatible endpoint
LLM_API_KEY=...
LLM_MODEL=claude-opus-4-8-thinking
```

---

## 🏗️ Architecture

```
                         ┌───────────────────────────┐
                         │   Claude (via gorouter)    │
                         │   OpenAI-compatible API    │
                         │   "the brain" — reasoning  │
                         └────────────┬──────────────┘
                                      │ tool-calls (function calling)
            ┌─────────────────────────┴─────────────────────────┐
            ▼                                                     ▼
  ┌────────────────────┐                          ┌──────────────────────────┐
  │   LOCAL tool layer  │                          │   MCP tool layer (--mcp)  │
  │  market_data (RSI)  │                          │  Official Alpaca MCP      │
  │  news_data (sent.)  │                          │  Server — 74 tools:       │
  │  tools (buy/sell)   │                          │  stocks·crypto·options·   │
  │                     │                          │  watchlist·portfolio·news │
  └─────────┬──────────┘                          └────────────┬─────────────┘
            │                                                    │ stdio (JSON-RPC)
            └────────────────────────┬───────────────────────────┘
                                     ▼
                          ┌──────────────────────┐
                          │   Alpaca Paper API    │
                          │  (virtual $100k acct) │
                          └──────────┬───────────┘
                                     │
        ┌────────────────┬──────────┴──────────┬──────────────────┐
        ▼                ▼                     ▼                  ▼
 ┌─────────────┐ ┌──────────────┐    ┌────────────────┐  ┌──────────────┐
 │ scheduler.py │ │ dashboard.py │    │  backtest.py    │  │ agent.py     │
 │ autonomous   │ │ CLI + HTML   │    │  strategy stats │  │ brain / loop │
 └─────────────┘ └──────────────┘    └────────────────┘  └──────────────┘
```

**Two tool backends, same brain:** by default the agent uses the lightweight local tool layer (fast, token-cheap). Pass `--mcp` and the exact same reasoning loop instead speaks to the **official Alpaca MCP Server** over stdio — proving ecosystem fluency while unlocking crypto, options, and portfolio-history tools.

**Decision flow per cycle:**
1. Inspect account + positions → know current state
2. For each watchlist symbol → indicators (technicals) + news (sentiment)
3. Claude reasons over technical + sentiment, sizes positions under risk limits
4. Places / closes orders → executed on paper account
5. Everything logged to `logs/agent.log`

---

## ▶️ Usage

```bash
# run one agent decision cycle (local tool layer)
python agent.py --symbols AAPL,NVDA,MSFT

# 🔌 run with the OFFICIAL Alpaca MCP Server (74 tools: stocks, crypto, options...)
python agent.py --mcp --symbols NVDA,BTC/USD

# 📈 backtest the strategy on historical data (metrics + buy&hold baseline)
python backtest.py --symbols AAPL,NVDA,MSFT,SPY --days 365

# autonomous scheduler (every hour, market hours only)
python scheduler.py --symbols AAPL,NVDA,MSFT --interval 3600
python scheduler.py --once --force        # single cycle, ignore market hours (demo)

# portfolio dashboard
python dashboard.py                       # CLI table
python dashboard.py --html                # also writes logs/dashboard.html

# connectivity smoke test
python smoke_test.py
```

The MCP server is vendored under `mcp_server/` and installed editable:

```bash
uv pip install -e mcp_server        # exposes the `alpaca-mcp-server` console script
python mcp_bridge.py                # smoke test: lists 74 tools, calls get_clock
```

### Example: an explainable live decision

```text
$ python agent.py --mcp --symbols NVDA,BTC/USD
### MCP ready: 74 tools cataloged ###
TOOL get_account_info -> equity $100,000
TOOL get_stock_snapshot NVDA / get_news

CLAUDE:
  NVDA -> BUY $8k (only 8% of equity — earnings risk this week, below my 15% cap)
  BTC/USD -> HOLD. Sentiment bullish, but RSI 82, parabolic. Discipline wins — don't chase the top.
```

*(Illustrative of the agent's logged reasoning. Actual numbers depend on live market data at run time.)*

---

## 🗂️ Project layout

| File | Role |
|------|------|
| `config.py` | Loads `.env`, enforces **paper-only** guard |
| `market_data.py` | Bars + technical indicators (RSI, SMA, momentum) |
| `news_data.py` | Alpaca News API headlines (sentiment context) |
| `tools.py` | Trading tools + JSON schemas + risk guardrail |
| `agent.py` | The agent loop — Claude tool-calling brain (`--mcp` optional) |
| `mcp_bridge.py` | Bridge to the **official Alpaca MCP Server** (74 tools over stdio) |
| `mcp_server/` | Vendored `alpacahq/alpaca-mcp-server` (installed editable) |
| `backtest.py` | Historical strategy backtest — return, Sharpe, drawdown, win-rate |
| `scheduler.py` | Autonomous scheduled runner (market-aware) |
| `dashboard.py` | CLI + HTML portfolio report |
| `smoke_test.py` | End-to-end connectivity check |
| `make_video.py` | Generates the narrated demo video (`video/alpaca_demo.mp4`) |

---

## 🔒 Safety

- **Paper account only** — `config.py` refuses to run against a non-paper base URL.
- Per-order notional cap (`MAX_NOTIONAL_PER_ORDER` in `tools.py`).
- Secrets live only in `.env` (git-ignored) — never hardcoded, never committed.

---

## 🧠 Model

Uses **Claude** through an OpenAI-compatible gateway (gorouter). Swappable — point `LLM_BASE_URL` / `LLM_MODEL` at any OpenAI-compatible provider.

---

*Built for the Alpaca AI Trading Agents Hackathon · Aug 28 – Sep 4, 2026*
