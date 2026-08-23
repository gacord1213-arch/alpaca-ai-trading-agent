"""
tools.py — lapisan eksekusi trading (paper) yang dipanggil Claude sebagai TOOLS.
Semua order PAPER (uang virtual). Ada guard risiko sederhana.
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import config

_trading = TradingClient(config.API_KEY, config.API_SECRET, paper=True)

# --- Guard risiko: batas notional per order (paper, tetap dijaga rapi) ---
MAX_NOTIONAL_PER_ORDER = 10_000.0  # USD


def get_account() -> dict:
    a = _trading.get_account()
    return {
        "cash": float(a.cash),
        "buying_power": float(a.buying_power),
        "equity": float(a.equity),
        "portfolio_value": float(a.portfolio_value),
    }


def get_positions() -> list:
    out = []
    for p in _trading.get_all_positions():
        out.append({
            "symbol": p.symbol,
            "qty": float(p.qty),
            "avg_entry": float(p.avg_entry_price),
            "market_value": float(p.market_value),
            "unrealized_pl": float(p.unrealized_pl),
            "unrealized_pl_pct": round(float(p.unrealized_plpc) * 100, 2),
        })
    return out


def place_order(symbol: str, side: str, notional: float = None, qty: float = None) -> dict:
    """Pasang market order paper. Pakai notional (USD) ATAU qty."""
    if notional is not None and notional > MAX_NOTIONAL_PER_ORDER:
        return {"error": f"notional ${notional} > batas ${MAX_NOTIONAL_PER_ORDER}"}
    side_enum = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
    kwargs = dict(symbol=symbol, side=side_enum, time_in_force=TimeInForce.DAY)
    if notional is not None:
        kwargs["notional"] = round(notional, 2)
    elif qty is not None:
        kwargs["qty"] = qty
    else:
        return {"error": "harus isi notional atau qty"}
    try:
        o = _trading.submit_order(MarketOrderRequest(**kwargs))
        return {"order_id": str(o.id), "symbol": o.symbol, "side": side,
                "status": str(o.status), "submitted_at": str(o.submitted_at)}
    except Exception as e:
        return {"error": str(e)}


def close_position(symbol: str) -> dict:
    try:
        o = _trading.close_position(symbol)
        return {"order_id": str(o.id), "symbol": symbol, "status": str(o.status)}
    except Exception as e:
        return {"error": str(e)}


# --- Skema tool (format OpenAI function-calling) untuk dikirim ke Claude ---
TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_account",
        "description": "Ambil ringkasan akun: cash, buying power, equity, portfolio value.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "get_positions",
        "description": "Ambil daftar posisi terbuka saat ini beserta PnL.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "get_indicators",
        "description": "Ambil indikator teknikal (harga, RSI, SMA20/50, tren, perubahan %) untuk 1 simbol saham.",
        "parameters": {"type": "object", "properties": {
            "symbol": {"type": "string", "description": "Ticker saham, mis. AAPL"}},
            "required": ["symbol"]},
    }},
    {"type": "function", "function": {
        "name": "get_news",
        "description": "Ambil 5 headline berita terbaru untuk 1 simbol. Gunakan untuk MENILAI sentimen (bullish/bearish/netral) sebelum keputusan.",
        "parameters": {"type": "object", "properties": {
            "symbol": {"type": "string", "description": "Ticker saham, mis. NVDA"}},
            "required": ["symbol"]},
    }},
    {"type": "function", "function": {
        "name": "place_order",
        "description": "Pasang market order PAPER. Gunakan 'notional' (USD) untuk beli fractional. side='buy' atau 'sell'.",
        "parameters": {"type": "object", "properties": {
            "symbol": {"type": "string"},
            "side": {"type": "string", "enum": ["buy", "sell"]},
            "notional": {"type": "number", "description": "Nilai order dalam USD (maks 10000)"}},
            "required": ["symbol", "side"]},
    }},
    {"type": "function", "function": {
        "name": "close_position",
        "description": "Tutup seluruh posisi untuk 1 simbol.",
        "parameters": {"type": "object", "properties": {
            "symbol": {"type": "string"}}, "required": ["symbol"]},
    }},
]
