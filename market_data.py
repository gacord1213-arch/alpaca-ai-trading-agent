"""
market_data.py — ambil data pasar dari Alpaca + hitung indikator teknikal.
Dipakai sebagai KONTEKS yang disuapkan ke Claude (bukan pengganti keputusan).
"""
from datetime import datetime, timedelta
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
import config

_data = StockHistoricalDataClient(config.API_KEY, config.API_SECRET)


def _rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])


def get_latest_price(symbol: str) -> dict:
    q = _data.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=symbol))
    quote = q[symbol]
    return {
        "symbol": symbol,
        "bid": float(quote.bid_price),
        "ask": float(quote.ask_price),
        "mid": round((float(quote.bid_price) + float(quote.ask_price)) / 2, 2),
    }


def get_indicators(symbol: str, days: int = 100) -> dict:
    """Ambil bar harian dan hitung indikator ringkas untuk konteks LLM."""
    # butuh ~50 hari BURSA untuk SMA50 -> ambil kalender lebih lebar (akhir pekan/libur)
    req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=datetime.now() - timedelta(days=days + 60),
    )
    bars = _data.get_stock_bars(req).df
    if bars.empty:
        return {"symbol": symbol, "error": "no data"}
    # bars.df multiindex (symbol, timestamp) -> ambil level symbol
    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.xs(symbol, level=0)
    close = bars["close"]
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    last = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else last
    week_ago = float(close.iloc[-6]) if len(close) > 6 else last
    return {
        "symbol": symbol,
        "last_close": round(last, 2),
        "change_1d_pct": round((last / prev - 1) * 100, 2),
        "change_5d_pct": round((last / week_ago - 1) * 100, 2),
        "sma20": round(float(sma20), 2) if pd.notna(sma20) else None,
        "sma50": round(float(sma50), 2) if pd.notna(sma50) else None,
        "rsi14": round(_rsi(close), 1),
        "trend": "up" if pd.notna(sma20) and pd.notna(sma50) and sma20 > sma50 else "down",
    }


if __name__ == "__main__":
    for s in ["AAPL", "NVDA", "TSLA"]:
        print(get_indicators(s))
