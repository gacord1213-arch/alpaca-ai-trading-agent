"""
make_video.py — bikin video demo hackathon FULL otomatis:
  - Voice-over NEURAL (edge-tts, suara en-US-AndrewNeural: warm/confident/human-like)
  - Slide dark-theme di-render PIL (title, bullets, terminal mock)
  - Digabung ffmpeg jadi satu MP4 1920x1080 + subtitle .srt

Output: video/alpaca_demo.mp4  +  video/narration.srt  +  video/narration.txt
Jalankan:  python make_video.py
"""
import asyncio
import os
import subprocess
import textwrap

import edge_tts
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
VOICE = "en-US-AndrewNeural"          # warm, confident, authentic — paling manusiawi
RATE = "+3%"                          # sedikit lebih hidup
OUT = "video"
os.makedirs(OUT, exist_ok=True)

# palet dark
BG = (13, 17, 23)          # github dark
CARD = (22, 27, 34)
ACCENT = (46, 160, 67)     # hijau alpaca
ACCENT2 = (88, 166, 255)   # biru
TXT = (230, 237, 243)
MUT = (139, 148, 158)
TERM_BG = (1, 4, 9)

F = "C:/Windows/Fonts/segoeui.ttf"
FB = "C:/Windows/Fonts/seguibl.ttf"      # black/bold
FM = "C:/Windows/Fonts/consola.ttf"      # monospace


def font(path, size):
    return ImageFont.truetype(path, size)

# ---------- SCENES ----------
# tiap scene: judul, subtitle, bullet/kode, tipe layout, narasi
SCENES = [
    dict(
        kind="title",
        title="Autonomous AI\nTrading Agent",
        sub="Powered by Claude  ·  Official Alpaca MCP Server",
        foot="Alpaca AI Trading Agents Hackathon — lablab.ai",
        narration=(
            "Most trading bots just run hardcoded rules. Ours is different. "
            "This is a true autonomous agent: a large language model, Claude, "
            "that thinks, analyzes the market, and makes its own trading decisions "
            "through tool calling. And it speaks directly to the official Alpaca M C P server. "
            "Let me show you."
        ),
    ),
    dict(
        kind="bullets",
        title="A real agentic loop",
        bullets=[
            ("Claude is the brain", "it chooses which tools to call — not a fixed strategy"),
            ("Official Alpaca MCP Server", "74 live tools: stocks, crypto, options, portfolio"),
            ("Look before it acts", "checks account, price snapshots, and news first"),
            ("Explainable", "every decision comes with written reasoning"),
        ],
        narration=(
            "When it runs, the agent boots the official Alpaca M C P server, and "
            "seventy-four tools become available instantly — stocks, crypto, options, portfolio. "
            "Notice the agent doesn't just buy. It first calls tools to inspect the account, "
            "pull price snapshots, and read the news. Then it decides."
        ),
    ),
    dict(
        kind="term",
        title="Live decision — NVDA & Bitcoin",
        lines=[
            ("$ python agent.py --mcp --symbols NVDA,BTC/USD", ACCENT2),
            ("### MCP ready: 74 tools cataloged ###", ACCENT),
            ("TOOL get_account_info -> equity $100,000", MUT),
            ("TOOL get_stock_snapshot NVDA / get_news", MUT),
            ("", TXT),
            ("CLAUDE:", ACCENT),
            ("  NVDA -> BUY $8k (only 8% of equity —", TXT),
            ("         earnings risk this week, below my 15% cap)", TXT),
            ("  BTC/USD -> HOLD. Sentiment bullish, but RSI 82,", TXT),
            ("         parabolic. Discipline wins — don't chase the top.", TXT),
        ],
        narration=(
            "Here it decides. For N-VIDIA it buys, but deliberately sizes to just eight percent "
            "of equity — below its fifteen percent cap — because earnings are this week. "
            "For Bitcoin, even though sentiment is bullish, it refuses to enter: R-S-I is eighty-two, "
            "parabolic. In its own words: discipline wins, don't chase the top. "
            "This isn't an if-else statement. This is judgment."
        ),
    ),
    dict(
        kind="bullets",
        title="Hybrid signal + hard guardrails",
        bullets=[
            ("Technical analysis", "RSI, SMA 20/50, momentum"),
            ("LLM news sentiment", "Claude scores headlines bullish / bearish"),
            ("Risk guardrail", "hard per-order notional cap"),
            ("Self-correcting", "adapts when an order is rejected — never crashes"),
        ],
        narration=(
            "Every decision blends two sides: technical analysis — R-S-I, moving averages, momentum — "
            "and news sentiment that Claude scores itself. And there's a hard guardrail: a per-order cap. "
            "When an order exceeds it, the agent adapts on its own instead of crashing. "
            "A-I, plus a safety rail."
        ),
    ),
    dict(
        kind="term",
        title="Measured, not just claimed — backtest",
        lines=[
            ("$ python backtest.py --symbols SPY,AAPL,NVDA --days 365", ACCENT2),
            ("", TXT),
            ("SPY   return +15.99%   Sharpe 1.40   maxDD -5.07%", ACCENT),
            ("AAPL  return +23.56%   Sharpe 1.07   win-rate 66.7%", TXT),
            ("NVDA  return  -5.98%   (trend whipsaw on volatility)", MUT),
            ("", TXT),
            ("-> We know exactly when this approach is strong,", TXT),
            ("   and when LLM reasoning must override raw signals.", TXT),
        ],
        narration=(
            "We don't just claim results. A one-year backtest gives real metrics: return, "
            "Sharpe ratio, max drawdown, win-rate, versus buy and hold. On calm markets like the S-P-Y, "
            "our trend strategy delivers a Sharpe of one point four with a small drawdown. "
            "On highly volatile stocks, the mechanical strategy loses to buy and hold — and that is exactly "
            "why we put L-L-M reasoning and sentiment on top of raw signals. "
            "We know precisely when this approach is strong, and when it isn't."
        ),
    ),
    dict(
        kind="title",
        title="One brain,\ntwo tool backends",
        sub="Lightweight local layer  ·  or official Alpaca MCP Server",
        foot="Autonomous · Transparent · Paper-safe · Built on Alpaca",
        narration=(
            "One brain, two tool backends: a lightweight local layer, or the official Alpaca M C P server. "
            "Everything is paper-trading, safe, with full reasoning logged. "
            "Autonomous, transparent, and built right on top of the Alpaca ecosystem. Thank you."
        ),
    ),
]


def rounded(draw, xy, r, fill):
    draw.rounded_rectangle(xy, radius=r, fill=fill)


def render_title(s, path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # accent bar
    d.rectangle([0, 0, 18, H], fill=ACCENT)
    # dekor kanan biar tidak kosong: kartu samar + aksen kotak
    rounded(d, [1330, 300, 1740, 800], 28, CARD)
    d.rectangle([1330, 300, 1356, 800], fill=ACCENT)
    for i in range(3):
        d.rectangle([1392 + i * 64, 356, 1436 + i * 64, 400],
                    fill=[ACCENT, ACCENT2, (255, 189, 46)][i])
    d.text((1392, 450), "▲ BUY  NVDA", font=font(FM, 40), fill=ACCENT)
    d.text((1392, 520), "= HOLD BTC", font=font(FM, 40), fill=(255, 189, 46))
    d.text((1392, 620), "74 MCP tools", font=font(FM, 36), fill=MUT)
    d.text((1392, 690), "Sharpe 1.40", font=font(FM, 36), fill=MUT)
    title = s["title"]
    fbig = font(FB, 120)
    y = 320
    for line in title.split("\n"):
        d.text((160, y), line, font=fbig, fill=TXT)
        y += 138
    d.text((165, y + 26), s["sub"], font=font(F, 42), fill=ACCENT2)
    d.text((165, H - 130), s["foot"], font=font(F, 38), fill=(170, 178, 189))
    img.save(path)


def render_bullets(s, path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 18, H], fill=ACCENT)
    d.text((160, 130), s["title"], font=font(FB, 96), fill=TXT)
    y = 330
    for head, sub in s["bullets"]:
        rounded(d, [160, y, W - 160, y + 140], 24, CARD)
        d.ellipse([200, y + 54, 234, y + 88], fill=ACCENT)
        d.text((280, y + 30), head, font=font(FB, 50), fill=TXT)
        d.text((280, y + 90), sub, font=font(F, 37), fill=MUT)
        y += 172
    img.save(path)


def render_term_state(s, path, cmd_chars=None, out_lines=None, cursor=True):
    """Render terminal; cmd_chars = berapa char command yang sudah 'diketik',
    out_lines = berapa baris output yang sudah tampil, cursor = tampilkan kursor blok."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 18, H], fill=ACCENT)
    d.text((160, 90), s["title"], font=font(FB, 80), fill=TXT)
    tx0, ty0, tx1, ty1 = 160, 250, W - 160, H - 110
    rounded(d, [tx0, ty0, tx1, ty1], 20, TERM_BG)
    rounded(d, [tx0, ty0, tx1, ty0 + 70], 20, (33, 38, 45))
    d.rectangle([tx0, ty0 + 40, tx1, ty0 + 70], fill=(33, 38, 45))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([tx0 + 30 + i * 44, ty0 + 22, tx0 + 56 + i * 44, ty0 + 48], fill=c)
    d.text((tx0 + 200, ty0 + 18), "agent — bash", font=font(F, 34), fill=MUT)

    lines = s["lines"]
    cmd_text, cmd_col = lines[0]
    out = lines[1:]
    if cmd_chars is None:
        cmd_chars = len(cmd_text)
    if out_lines is None:
        out_lines = len(out)

    body_top = ty0 + 70
    region = ty1 - body_top
    lh = min(60, region // (len(lines) + 1))
    fsize = min(40, lh - 12)
    fm = font(FM, fsize)
    block_h = lh * (len(lines) - 1) + fsize
    y0 = body_top + (region - block_h) // 2
    x = tx0 + 44

    # command (sebagian, efek diketik)
    shown = cmd_text[:cmd_chars]
    d.text((x, y0), shown, font=fm, fill=cmd_col)
    if cursor:
        cw = fm.getbbox(shown)[2] if shown else 0
        # kursor blok hanya saat masih mengetik command atau menunggu
        if out_lines == 0:
            d.rectangle([x + cw + 4, y0 + 4, x + cw + 4 + fsize // 2, y0 + fsize],
                        fill=(200, 208, 218))
    # output lines yang sudah tampil
    for j, (text, col) in enumerate(out[:out_lines]):
        d.text((x, y0 + lh * (j + 1)), text, font=fm, fill=col)
    img.save(path)


def render_term(s, path):
    render_term_state(s, path, cursor=False)


RENDER = {"title": render_title, "bullets": render_bullets, "term": render_term}


async def tts(text, path):
    c = edge_tts.Communicate(text, VOICE, rate=RATE)
    await c.save(path)


def dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(out.stdout.strip())


def srt_ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def build_typed_frames(s, prefix):
    """Hasilkan list (png_path, durasi_detik) utk efek: command diketik + output jalan.
    Mengembalikan (frames, action_dur)."""
    cmd = s["lines"][0][0]
    nout = len(s["lines"]) - 1
    frames = []
    fi = [0]

    def emit(cmd_chars, out_lines, cursor, dur):
        png = f"{OUT}/{prefix}_{fi[0]:04d}.png"
        render_term_state(s, png, cmd_chars=cmd_chars, out_lines=out_lines, cursor=cursor)
        frames.append([png, dur])
        fi[0] += 1

    # fase 1: ketik command huruf per huruf (~22 char/detik) + kursor
    for n in range(1, len(cmd) + 1):
        emit(n, 0, True, 0.045)
    emit(len(cmd), 0, True, 0.55)          # jeda "enter"
    # fase 2: output muncul baris demi baris
    for k in range(1, nout + 1):
        emit(len(cmd), k, False, 0.5)
    action = sum(f[1] for f in frames)
    return frames, action


def encode_typed_scene(s, prefix, mp3, out_mp4):
    """Encode 1 scene terminal beranimasi + voice-over + fade."""
    narr = dur(mp3)
    frames, action = build_typed_frames(s, prefix)
    D = max(action + 0.6, narr + 1.0)
    frames[-1][1] += (D - action)          # tahan frame terakhir sampai audio selesai
    listf = f"{OUT}/{prefix}_list.txt"
    with open(listf, "w") as f:
        for p, du in frames:
            f.write(f"file '{os.path.basename(p)}'\nduration {du:.4f}\n")
        f.write(f"file '{os.path.basename(frames[-1][0])}'\n")
    vf = (f"fps=30,format=yuv420p,"
          f"fade=t=in:st=0:d=0.5,fade=t=out:st={D-0.6:.3f}:d=0.6")
    af = f"afade=t=in:st=0:d=0.4,afade=t=out:st={D-0.6:.3f}:d=0.6,apad"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf, "-i", mp3,
        "-vf", vf, "-af", af, "-t", f"{D:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-r", "30", out_mp4,
    ], capture_output=True, cwd=".")
    for p, _ in frames:
        try: os.remove(p)
        except OSError: pass
    try: os.remove(listf)
    except OSError: pass
    return D


def encode_still_scene(s, png, mp3, out_mp4):
    """Encode scene static (title/bullets) + Ken Burns zoom + fade."""
    d = dur(mp3) + 1.0
    nfr = int(d * 30)
    vf = (
        f"scale={W*2}:{H*2},"
        f"zoompan=z='min(zoom+0.0006,1.10)':d={nfr}"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps=30,"
        f"fade=t=in:st=0:d=0.6,fade=t=out:st={d-0.6:.3f}:d=0.6"
    )
    af = f"afade=t=in:st=0:d=0.4,afade=t=out:st={d-0.6:.3f}:d=0.6"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", png, "-i", mp3,
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-t", f"{d:.3f}",
        "-vf", vf, "-af", af, "-r", "30", out_mp4,
    ], capture_output=True)
    return d


def main():
    clips, srt, plain = [], [], []
    t0 = 0.0
    idx = 1
    for i, s in enumerate(SCENES):
        png = f"{OUT}/s{i}.png"
        mp3 = f"{OUT}/s{i}.mp3"
        mp4 = f"{OUT}/s{i}.mp4"
        asyncio.run(tts(s["narration"], mp3))
        if s["kind"] == "term":
            # HYBRID: scene terminal -> efek diketik + output jalan
            d = encode_typed_scene(s, f"typ{i}", mp3, mp4)
        else:
            RENDER[s["kind"]](s, png)
            d = encode_still_scene(s, png, mp3, mp4)
        clips.append(mp4)
        srt.append(f"{idx}\n{srt_ts(t0)} --> {srt_ts(t0 + d - 1.0)}\n"
                   f"{textwrap.fill(s['narration'], 90)}\n")
        plain.append(f"[Scene {i+1}] {s['narration']}\n")
        t0 += d
        idx += 1
        print(f"scene {i+1}/{len(SCENES)} [{s['kind']}] ok ({d:.1f}s)")

    # concat
    listfile = f"{OUT}/list.txt"
    with open(listfile, "w") as f:
        for c in clips:
            f.write(f"file '{os.path.basename(c)}'\n")
    final = f"{OUT}/alpaca_demo.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
        "-c", "copy", final,
    ], capture_output=True, cwd=".")
    # kalau copy gagal (beda param), re-encode
    if not os.path.exists(final) or os.path.getsize(final) < 10000:
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
            "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", final,
        ], capture_output=True, cwd=".")

    with open(f"{OUT}/narration.srt", "w", encoding="utf-8") as f:
        f.write("\n".join(srt))
    with open(f"{OUT}/narration.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(plain))
    print("TOTAL:", round(t0, 1), "s ->", final)


if __name__ == "__main__":
    main()
