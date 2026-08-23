# 🎬 Demo Video Script — Alpaca AI Trading Agent
**Target durasi: ~2 menit 30 detik · Hackathon: Alpaca AI Trading Agents (lablab.ai)**

Tujuan video: yakinkan juri dalam 3 hal → (1) ini **agent otonom sejati** (Claude yang memutuskan, bukan strategi hardcoded), (2) kami **memakai Alpaca MCP Server resmi** (tema sponsor), (3) kami **jujur & terukur** (backtest dengan metrik nyata).

Tips rekam: pakai OBS / ScreenToGif. Terminal font besar (16–18pt), tema gelap. Bicara pelan & percaya diri. Total 5 scene.

---

## SCENE 1 — Hook & Masalah (0:00 – 0:20)
**Layar:** wajah kamu / slide judul "Autonomous AI Trading Agent · Powered by Claude + Alpaca MCP".

**Narasi:**
> "Kebanyakan trading bot hanya menjalankan aturan yang sudah di-hardcode. Milik kami berbeda — ini agent otonom sungguhan: sebuah LLM, Claude, yang berpikir, menganalisis pasar, dan mengambil keputusan trading-nya sendiri lewat tool-calling. Dan ia berbicara langsung ke **Alpaca MCP Server resmi**. Mari saya tunjukkan."

---

## SCENE 2 — Agent otonom + MCP resmi beraksi (0:20 – 1:15) ⭐ INTI
**Layar:** terminal. Jalankan:
```bash
python agent.py --mcp --symbols NVDA,BTC/USD
```
**Yang harus terlihat & di-highlight (zoom/panah saat editing):**
- Baris `### MCP siap: 74 tool terkatalog ###` → **jeda, tunjuk ini.**
- Log `TOOL get_account_info`, `get_stock_snapshot`, `get_news` → agent MELIHAT dulu.
- Reasoning Claude yang panjang di akhir.

**Narasi (bicara sambil log jalan):**
> "Begitu dijalankan, agent menyalakan Alpaca MCP Server resmi — **74 tool** langsung tersedia: saham, crypto, opsi, portfolio. Perhatikan: Claude tidak asal beli. Ia lebih dulu memanggil tool untuk memeriksa akun, snapshot harga, dan membaca berita…
> …lalu ia memutuskan. Untuk NVDA ia BUY, tapi sengaja hanya 8% ekuitas — di bawah batas 15% — karena ada earnings minggu ini. Untuk Bitcoin, meski sentimen bullish, ia justru **menolak masuk**: RSI 82, parabolik. Dengan kata-katanya sendiri: *disiplin risiko menang, jangan mengejar puncak.* Ini bukan if-else. Ini penilaian."

---

## SCENE 3 — Hybrid signal + guardrail (1:15 – 1:40)
**Layar:** sorot potongan reasoning di `logs/agent.log` (buka file, scroll ke keputusan).

**Narasi:**
> "Setiap keputusan memadukan dua sisi: analisis teknikal — RSI, SMA, momentum — dan sentimen berita yang dinilai Claude sendiri. Dan ada guardrail keras: batas notional per order. Saat order melebihi batas, agent **beradaptasi sendiri**, bukan crash. AI plus pagar pengaman."

---

## SCENE 4 — Bukti terukur: Backtest (1:40 – 2:10)
**Layar:** terminal. Jalankan:
```bash
python backtest.py --symbols SPY,AAPL,NVDA --days 365
```
**Highlight:** baris SPY (return +16%, Sharpe 1.4, drawdown -5%) dan baris ringkasan.

**Narasi (JUJUR — ini justru menguatkan):**
> "Kami tidak sekadar mengklaim. Backtest satu tahun memberi metrik nyata: return, Sharpe ratio, max drawdown, win-rate, dibanding buy-and-hold. Di pasar yang tenang seperti SPY, strategi trend kami memberi Sharpe 1.4 dengan drawdown kecil. Di saham super-volatil, strategi mekanis kalah dari buy-and-hold — dan **justru itu alasan** kami menaruh reasoning LLM dan sentimen di atas sinyal mentah. Kami tahu persis kapan pendekatan ini kuat dan kapan tidak."

---

## SCENE 5 — Arsitektur & penutup (2:10 – 2:30)
**Layar:** diagram arsitektur di README (dua backend: LOCAL vs MCP → Alpaca Paper API).

**Narasi:**
> "Satu otak, dua backend tool: layer lokal yang ringan, atau MCP Server resmi Alpaca. Semuanya paper-trading, aman, dengan reasoning tercatat penuh. Otonom, transparan, dan dibangun tepat di atas ekosistem Alpaca. Terima kasih."

---

## Checklist sebelum submit
- [ ] `.env` terisi & `python smoke_test.py` hijau sebelum rekam
- [ ] Jalankan `agent.py --mcp` sekali sebelum rekam (biar MCP warm, log rapi)
- [ ] Terminal bersih, font besar, tema gelap
- [ ] Audio jelas, tanpa noise
- [ ] Sebut kata kunci juri: **"otonom", "Alpaca MCP Server resmi", "tool-calling", "backtest / Sharpe"**
- [ ] Durasi ≤ 3 menit (aturan lablab biasanya 2–5 menit — cek halaman submission)
- [ ] Upload ke YouTube (unlisted) → tempel link di form lablab
