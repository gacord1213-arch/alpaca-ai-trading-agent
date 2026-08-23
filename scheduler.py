"""
scheduler.py — jalankan agent secara OTONOM terjadwal (bukti "autonomous").
  python scheduler.py --symbols AAPL,NVDA,MSFT --interval 3600   # tiap 1 jam
  python scheduler.py --once                                     # sekali jalan
Menghormati jam bursa: skip eksekusi saat market tutup (kecuali --force).
"""
import argparse
import time
from datetime import datetime

from alpaca.trading.client import TradingClient
import config
import agent

_trading = TradingClient(config.API_KEY, config.API_SECRET, paper=True)


def market_is_open() -> bool:
    try:
        return bool(_trading.get_clock().is_open)
    except Exception:
        return False


def run_loop(symbols, interval, once, force):
    agent.log.info("### SCHEDULER START | interval=%ss | symbols=%s ###", interval, symbols)
    while True:
        if force or market_is_open():
            agent.log.info(">>> siklus agent @ %s", datetime.now().strftime("%H:%M:%S"))
            try:
                agent.run_session(symbols)
            except Exception as e:
                agent.log.error("siklus gagal: %s", e)
        else:
            agent.log.info("market TUTUP — skip siklus (%s)", datetime.now().strftime("%H:%M:%S"))
        if once:
            break
        time.sleep(interval)
    agent.log.info("### SCHEDULER STOP ###")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="AAPL,NVDA,MSFT")
    ap.add_argument("--interval", type=int, default=3600, help="detik antar siklus")
    ap.add_argument("--once", action="store_true", help="jalan sekali lalu berhenti")
    ap.add_argument("--force", action="store_true", help="abaikan jam bursa")
    a = ap.parse_args()
    syms = [s.strip().upper() for s in a.symbols.split(",") if s.strip()]
    run_loop(syms, a.interval, a.once, a.force)
