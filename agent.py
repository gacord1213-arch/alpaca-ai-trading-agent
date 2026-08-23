"""
agent.py — OTAK agent: Claude (via gorouter) memutuskan trading dgn memanggil tools.
Loop: kumpulkan konteks -> Claude reasoning + tool_calls -> eksekusi paper -> log.

Jalankan:  python agent.py --symbols AAPL,NVDA,MSFT
"""
import argparse
import json
import logging
import os
from datetime import datetime

from openai import OpenAI

import config
import tools
import market_data
import news_data

# ---------- logging ----------
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("logs/agent.log", encoding="utf-8"),
              logging.StreamHandler()],
)
log = logging.getLogger("agent")

client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)

SYSTEM_PROMPT = """Kamu adalah AI trading agent otonom yang beroperasi di akun PAPER Alpaca (uang virtual).
Tujuan: mengelola portofolio kecil secara disiplin memakai data teknikal + penilaianmu.

Aturan main:
- Gunakan tools untuk MELIHAT dulu (get_account, get_positions, get_indicators, get_news) sebelum bertindak.
- Padukan DUA sisi analisis:
  (a) Teknikal: tren (SMA20 vs SMA50), RSI (overbought >70 / oversold <30), momentum 1d/5d.
  (b) Sentimen: baca get_news tiap kandidat dan nilai bullish/bearish/netral dari headline.
- Keputusan trading harus mempertimbangkan KEDUANYA. Sebutkan skor sentimen (mis. "bullish 4/5") dalam alasanmu.
- Kelola risiko: jangan alokasikan lebih dari ~15% equity ke satu posisi. Order pakai 'notional' USD (maks $10.000/order).
- Boleh memutuskan TIDAK trading jika sinyal tidak meyakinkan (HOLD).
- Untuk SETIAP keputusan, jelaskan alasannya singkat & jelas (ini akan ditampilkan ke juri hackathon).
- Setelah selesai bertindak, tutup dengan ringkasan: apa yang kamu lakukan dan kenapa.
"""

# ---------- dispatcher tool ----------
def run_tool(name: str, args: dict):
    if name == "get_account":
        return tools.get_account()
    if name == "get_positions":
        return tools.get_positions()
    if name == "get_indicators":
        return market_data.get_indicators(args["symbol"])
    if name == "get_news":
        return news_data.get_news(args["symbol"])
    if name == "place_order":
        return tools.place_order(**args)
    if name == "close_position":
        return tools.close_position(**args)
    return {"error": f"unknown tool {name}"}


def run_session(symbols, max_steps=12, mcp_client=None):
    """Kalau mcp_client diberikan -> pakai tool MCP resmi (74 tool).
    Kalau None -> pakai tool lokal (tools.py + market_data + news)."""
    watchlist = ", ".join(symbols)

    if mcp_client is not None:
        tool_schemas = mcp_client.tools
        dispatch = lambda fn, a: mcp_client.call(fn, a)
        mode_note = ("Kamu terhubung ke ALPACA MCP SERVER RESMI (74 tool: stocks, crypto, options, "
                     "watchlist, portfolio history, market movers, dsb). Nama tool memakai skema resmi, "
                     "mis. get_account_info, get_stock_snapshot, place_stock_order, place_crypto_order, "
                     "get_option_chain, get_portfolio_history. Beberapa order butuh field seperti "
                     "symbol/side/type/time_in_force/qty atau notional. Selalu LIHAT dulu sebelum order.")
    else:
        tool_schemas = tools.TOOL_SCHEMAS
        dispatch = run_tool
        mode_note = ("Tool lokal: get_account, get_positions, get_indicators, get_news, place_order, close_position.")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + mode_note},
        {"role": "user", "content":
            f"Waktu: {datetime.now():%Y-%m-%d %H:%M}. "
            f"Watchlist hari ini: {watchlist}. "
            f"Analisis akun & watchlist, lalu ambil keputusan trading yang disiplin. "
            f"Cek posisi yang sudah ada juga (kelola exit bila perlu)."},
    ]

    for step in range(max_steps):
        resp = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            tools=tool_schemas,
            tool_choice="auto",
            max_tokens=1500,
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if msg.content:
            log.info("CLAUDE: %s", msg.content.strip())

        if not msg.tool_calls:
            log.info("=== sesi selesai (tidak ada tool call lagi) ===")
            break

        for tc in msg.tool_calls:
            fn = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = dispatch(fn, args)
            log.info("TOOL %s(%s) -> %s", fn, args, json.dumps(result, default=str)[:400])
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str),
            })
    else:
        log.info("=== mencapai max_steps ===")

    return messages


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="AAPL,NVDA,MSFT",
                    help="daftar ticker dipisah koma")
    ap.add_argument("--mcp", action="store_true",
                    help="pakai Alpaca MCP Server RESMI (74 tool) sebagai lapisan tool")
    args = ap.parse_args()
    syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    mcp_client = None
    if args.mcp:
        import mcp_bridge
        log.info("### Menyalakan Alpaca MCP Server resmi... ###")
        mcp_client = mcp_bridge.MCPClient()
        n = len(mcp_client.open())
        log.info("### MCP siap: %d tool terkatalog ###", n)

    log.info("### START agent | watchlist=%s | model=%s | mcp=%s ###",
             syms, config.LLM_MODEL, bool(mcp_client))
    try:
        run_session(syms, mcp_client=mcp_client)
    finally:
        if mcp_client:
            mcp_client.close()
    log.info("### END agent ###")
