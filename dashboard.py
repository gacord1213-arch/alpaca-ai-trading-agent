"""
dashboard.py — laporan portofolio paper Alpaca yang enak dibaca (buat demo/CLI).
  python dashboard.py            # cetak ringkasan ke terminal
  python dashboard.py --html     # tulis logs/dashboard.html juga
"""
import argparse
from datetime import datetime
import tools


def _fmt_usd(x: float) -> str:
    return f"${x:,.2f}"


def build_report() -> dict:
    acct = tools.get_account()
    positions = tools.get_positions()
    total_upl = sum(p["unrealized_pl"] for p in positions)
    return {"acct": acct, "positions": positions, "total_upl": total_upl,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M")}


def print_report(r: dict):
    a = r["acct"]
    print("=" * 60)
    print(f"  PORTFOLIO PAPER ALPACA  |  {r['ts']}")
    print("=" * 60)
    print(f"  Equity        : {_fmt_usd(a['equity'])}")
    print(f"  Portfolio val : {_fmt_usd(a['portfolio_value'])}")
    print(f"  Cash          : {_fmt_usd(a['cash'])}")
    print(f"  Buying power  : {_fmt_usd(a['buying_power'])}")
    print("-" * 60)
    if not r["positions"]:
        print("  (belum ada posisi terbuka)")
    else:
        print(f"  {'SYMBOL':<8}{'QTY':>8}{'ENTRY':>12}{'MKT VAL':>14}{'PnL':>12}{'PnL%':>9}")
        for p in r["positions"]:
            print(f"  {p['symbol']:<8}{p['qty']:>8.2f}{_fmt_usd(p['avg_entry']):>12}"
                  f"{_fmt_usd(p['market_value']):>14}{_fmt_usd(p['unrealized_pl']):>12}"
                  f"{p['unrealized_pl_pct']:>8.2f}%")
        print("-" * 60)
        print(f"  Total unrealized PnL: {_fmt_usd(r['total_upl'])}")
    print("=" * 60)


def write_html(r: dict, path="logs/dashboard.html"):
    a = r["acct"]
    rows = "".join(
        f"<tr><td>{p['symbol']}</td><td>{p['qty']:.2f}</td>"
        f"<td>${p['avg_entry']:,.2f}</td><td>${p['market_value']:,.2f}</td>"
        f"<td style='color:{'#16a34a' if p['unrealized_pl']>=0 else '#dc2626'}'>"
        f"${p['unrealized_pl']:,.2f} ({p['unrealized_pl_pct']:.2f}%)</td></tr>"
        for p in r["positions"]) or "<tr><td colspan=5>Belum ada posisi</td></tr>"
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Alpaca AI Agent — Portfolio</title>
<style>body{{font-family:system-ui,Segoe UI,sans-serif;background:#0f172a;color:#e2e8f0;padding:32px}}
h1{{color:#38bdf8}} .cards{{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0}}
.card{{background:#1e293b;border-radius:12px;padding:18px 24px;min-width:160px}}
.card b{{display:block;color:#94a3b8;font-size:13px;font-weight:500}}
.card span{{font-size:22px;font-weight:700}}
table{{width:100%;border-collapse:collapse;margin-top:12px}}
th,td{{padding:10px 12px;text-align:right;border-bottom:1px solid #334155}}
th:first-child,td:first-child{{text-align:left}} th{{color:#94a3b8}}</style></head>
<body><h1>🤖 Alpaca AI Trading Agent — Portfolio</h1>
<p style="color:#64748b">Diperbarui {r['ts']} · Paper trading (uang virtual)</p>
<div class="cards">
<div class="card"><b>Equity</b><span>${a['equity']:,.0f}</span></div>
<div class="card"><b>Portfolio Value</b><span>${a['portfolio_value']:,.0f}</span></div>
<div class="card"><b>Cash</b><span>${a['cash']:,.0f}</span></div>
<div class="card"><b>Unrealized PnL</b><span style="color:{'#16a34a' if r['total_upl']>=0 else '#dc2626'}">${r['total_upl']:,.2f}</span></div>
</div>
<table><tr><th>Symbol</th><th>Qty</th><th>Entry</th><th>Market Value</th><th>Unrealized PnL</th></tr>
{rows}</table></body></html>"""
    import os
    os.makedirs("logs", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[HTML] ditulis ke {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", action="store_true")
    args = ap.parse_args()
    r = build_report()
    print_report(r)
    if args.html:
        write_html(r)
