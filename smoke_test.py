"""
smoke_test.py — verifikasi pipeline end-to-end di PAPER trading:
  1. Cek koneksi & saldo akun
  2. Ambil harga terbaru (quote) sebuah saham
  3. Pasang 1 order beli kecil (paper), lalu tampilkan posisi
Semua di akun paper (uang virtual). Aman.
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
import config

def main():
    trading = TradingClient(config.API_KEY, config.API_SECRET, paper=True)
    data = StockHistoricalDataClient(config.API_KEY, config.API_SECRET)

    # 1. Akun
    acct = trading.get_account()
    print("=== AKUN (PAPER) ===")
    print(f"  status       : {acct.status}")
    print(f"  cash         : ${float(acct.cash):,.2f}")
    print(f"  buying_power : ${float(acct.buying_power):,.2f}")
    print(f"  equity       : ${float(acct.equity):,.2f}")
    print(f"  portfolio    : ${float(acct.portfolio_value):,.2f}")

    # 2. Quote terbaru
    symbol = "AAPL"
    q = data.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=symbol))
    quote = q[symbol]
    print(f"\n=== QUOTE {symbol} ===")
    print(f"  bid ${quote.bid_price}  /  ask ${quote.ask_price}  @ {quote.timestamp}")

    # 3. Pasang 1 order beli paper (qty kecil). Fractional biar pasti kebeli.
    print(f"\n=== PASANG ORDER PAPER: beli 1 {symbol} (market) ===")
    order = trading.submit_order(MarketOrderRequest(
        symbol=symbol, qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
    ))
    print(f"  order id     : {order.id}")
    print(f"  status       : {order.status}")
    print(f"  submitted_at : {order.submitted_at}")

    # 4. Posisi saat ini
    print("\n=== POSISI ===")
    positions = trading.get_all_positions()
    if not positions:
        print("  (belum ada posisi terisi — order mungkin masih 'accepted' saat market tutup)")
    for p in positions:
        print(f"  {p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f}  (PnL ${float(p.unrealized_pl):.2f})")

    print("\nSMOKE TEST SELESAI — pipeline paper trading jalan end-to-end. ✅")

if __name__ == "__main__":
    main()
