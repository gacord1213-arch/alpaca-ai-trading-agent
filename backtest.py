"""
backtest.py — mesin BACKTEST untuk memvalidasi strategi agent di data historis.

Kenapa penting: juri ingin bukti strategi "beneran works", bukan tebak-tebakan.
Modul ini menjalankan strategi berbasis indikator YANG SAMA dengan yang dipakai
agent (SMA20/SMA50 trend + RSI) di harga historis Alpaca, lalu menghitung metrik
kuantitatif: total return, CAGR, win-rate, max drawdown, Sharpe ratio, jumlah trade,
dan membandingkannya dengan buy & hold.

Strategi yang diuji (long-only, sinyal harian):
  ENTRY  : SMA20 > SMA50 (uptrend) DAN RSI14 < 70 (belum overbought)
  EXIT   : SMA20 < SMA50 (trend patah) ATAU RSI14 > 78 (overbought ekstrem)
Ini versi mekanis dari logika reasoning agent, biar bisa diukur objektif.

Jalankan:
  python backtest.py --symbols AAPL,NVDA,MSFT --days 365
  python backtest.py --symbols SPY --days 730 --capital 100000
"""
import argparse
import math
from datetime import datetime, timedelta

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

import config

_data = StockHistoricalDataClient(config.API_KEY, config.API_SECRET)

TRADING_DAYS = 252


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


def _load_bars(symbol: str, days: int) -> pd.DataFrame:
    req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=datetime.now() - timedelta(days=days + 90),  # buffer utk warm-up SMA50
    )
    bars = _data.get_stock_bars(req).df
    if bars.empty:
        return bars
    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.xs(symbol, level=0)
    return bars


def _metrics_from_equity(equity: pd.Series, daily_ret: pd.Series,
                         trade_returns: list, n_days: int) -> dict:
    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    years = max(n_days / TRADING_DAYS, 1e-9)
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1
    # max drawdown
    roll_max = equity.cummax()
    drawdown = equity / roll_max - 1
    max_dd = drawdown.min()
    # Sharpe (rf=0), disetahunkan dari return harian strategi
    mu = daily_ret.mean()
    sigma = daily_ret.std()
    sharpe = (mu / sigma * math.sqrt(TRADING_DAYS)) if sigma and sigma > 0 else 0.0
    wins = [r for r in trade_returns if r > 0]
    win_rate = (len(wins) / len(trade_returns)) if trade_returns else 0.0
    avg_win = (sum(wins) / len(wins)) if wins else 0.0
    losses = [r for r in trade_returns if r <= 0]
    avg_loss = (sum(losses) / len(losses)) if losses else 0.0
    return {
        "total_return_pct": round(total_return * 100, 2),
        "cagr_pct": round(cagr * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "sharpe": round(sharpe, 2),
        "num_trades": len(trade_returns),
        "win_rate_pct": round(win_rate * 100, 1),
        "avg_win_pct": round(avg_win * 100, 2),
        "avg_loss_pct": round(avg_loss * 100, 2),
    }


def backtest_symbol(symbol: str, days: int = 365, capital: float = 100000.0) -> dict:
    bars = _load_bars(symbol, days)
    if bars.empty or len(bars) < 60:
        return {"symbol": symbol, "error": "data tidak cukup untuk backtest"}

    df = pd.DataFrame(index=bars.index)
    df["close"] = bars["close"]
    df["sma20"] = df["close"].rolling(20).mean()
    df["sma50"] = df["close"].rolling(50).mean()
    df["rsi"] = _rsi(df["close"])
    df = df.dropna()
    # batasi ke jendela yang diminta (setelah warm-up indikator)
    df = df.iloc[-min(len(df), days):]
    if len(df) < 30:
        return {"symbol": symbol, "error": "jendela terlalu pendek setelah warm-up"}

    close = df["close"].values
    sma20 = df["sma20"].values
    sma50 = df["sma50"].values
    rsi = df["rsi"].values
    n = len(df)

    position = 0          # 0 = cash, 1 = long
    entry_price = 0.0
    trade_returns = []
    strat_daily = []      # return harian strategi (untuk Sharpe/equity)

    for i in range(1, n):
        # return harian: kalau kemarin long, kena perubahan harga hari ini
        r = (close[i] / close[i - 1] - 1) if position == 1 else 0.0
        strat_daily.append(r)

        uptrend = sma20[i] > sma50[i]
        # sinyal pakai data SAMPAI hari i (dieksekusi harga close i)
        if position == 0 and uptrend and rsi[i] < 70:
            position = 1
            entry_price = close[i]
        elif position == 1 and ((not uptrend) or rsi[i] > 78):
            trade_returns.append(close[i] / entry_price - 1)
            position = 0
    # tutup posisi terbuka di akhir periode (mark-to-market)
    if position == 1:
        trade_returns.append(close[-1] / entry_price - 1)

    strat_daily = pd.Series(strat_daily)
    equity = (1 + strat_daily).cumprod() * capital
    m = _metrics_from_equity(equity, strat_daily, trade_returns, n)

    # baseline buy & hold di simbol yang sama
    bh_return = close[-1] / close[0] - 1
    m["buy_hold_return_pct"] = round(bh_return * 100, 2)
    m["vs_buy_hold_pct"] = round((m["total_return_pct"] - m["buy_hold_return_pct"]), 2)
    m["symbol"] = symbol
    m["days_tested"] = n
    m["final_equity"] = round(float(equity.iloc[-1]), 2)
    m["start"] = str(df.index[0].date())
    m["end"] = str(df.index[-1].date())
    return m


def _fmt(m: dict) -> str:
    if "error" in m:
        return f"  {m['symbol']}: ⚠️  {m['error']}"
    beat = "✅ MENGALAHKAN" if m["vs_buy_hold_pct"] > 0 else "❌ kalah dari"
    return (
        f"  {m['symbol']}  ({m['start']} → {m['end']}, {m['days_tested']} hari bursa)\n"
        f"    Strategi return   : {m['total_return_pct']:+.2f}%   (CAGR {m['cagr_pct']:+.2f}%)\n"
        f"    Buy & Hold        : {m['buy_hold_return_pct']:+.2f}%   → strategi {beat} B&H ({m['vs_buy_hold_pct']:+.2f} pp)\n"
        f"    Max Drawdown      : {m['max_drawdown_pct']:.2f}%\n"
        f"    Sharpe (annual)   : {m['sharpe']}\n"
        f"    Trades            : {m['num_trades']}  |  Win-rate {m['win_rate_pct']}%  "
        f"(avg win {m['avg_win_pct']:+.2f}% / avg loss {m['avg_loss_pct']:+.2f}%)\n"
        f"    Final equity      : ${m['final_equity']:,.2f}"
    )


def run(symbols, days=365, capital=100000.0):
    print("=" * 70)
    print(f" BACKTEST STRATEGI AGENT  |  {days} hari kalender  |  modal ${capital:,.0f}")
    print(" Strategi: long SMA20>SMA50 & RSI<70  |  exit trend patah / RSI>78")
    print("=" * 70)
    results = []
    for s in symbols:
        m = backtest_symbol(s, days=days, capital=capital)
        results.append(m)
        print(_fmt(m))
        print("-" * 70)
    ok = [r for r in results if "error" not in r]
    if ok:
        avg_ret = sum(r["total_return_pct"] for r in ok) / len(ok)
        beat = sum(1 for r in ok if r["vs_buy_hold_pct"] > 0)
        print(f" RINGKASAN: {len(ok)} simbol | rata2 return strategi {avg_ret:+.2f}% | "
              f"{beat}/{len(ok)} mengalahkan buy & hold")
    print("=" * 70)
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="AAPL,NVDA,MSFT")
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--capital", type=float, default=100000.0)
    args = ap.parse_args()
    syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    run(syms, days=args.days, capital=args.capital)
