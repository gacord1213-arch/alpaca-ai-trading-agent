"""
mcp_bridge.py — jembatan ke Alpaca MCP Server RESMI (alpacahq/alpaca-mcp-server).

Kenapa ada: tema hackathon = "Alpaca MCP server". Modul ini menyalakan MCP server
resmi lewat stdio, meng-katalog SEMUA tool resmi (60+: stocks, options, crypto,
watchlist, portfolio history, market movers, dsb), lalu mengekspornya sebagai
tool OpenAI-compatible supaya Claude (via gorouter) bisa memanggilnya.

Dipakai oleh agent.py saat mode --mcp.

Catatan teknis penting (hasil debugging):
- Server dijalankan via console-script `alpaca-mcp-server(.exe)`, BUKAN `python -m`
  (repo tidak punya __main__.py -> "python -m" exit diam-diam / Connection closed).
- PYTHONPATH host Hermes bisa "mencemari" versi mcp; kita bersihkan env sebelum spawn.
- Semua sinkron di luar; async MCP dijalankan lewat satu event loop privat.
"""
import os
import sys
import json
import shutil
import asyncio
import threading
from pathlib import Path

import config  # memuat kredensial + guard paper-only

# ---- lokasi console-script server ----
def _server_command() -> str:
    # 1) coba di venv aktif (.venv/Scripts atau .venv/bin)
    here = Path(sys.executable).parent
    for name in ("alpaca-mcp-server.exe", "alpaca-mcp-server"):
        cand = here / name
        if cand.exists():
            return str(cand)
    # 2) coba PATH
    found = shutil.which("alpaca-mcp-server")
    if found:
        return found
    raise RuntimeError(
        "console-script 'alpaca-mcp-server' tidak ditemukan. "
        "Jalankan: uv pip install -e mcp_server"
    )


def _server_env() -> dict:
    env = os.environ.copy()
    # bersihkan PYTHONPATH host agar versi mcp server tidak bentrok
    env.pop("PYTHONPATH", None)
    # suntik kredensial paper dari config (nama env sesuai README MCP resmi)
    env["ALPACA_API_KEY"] = config.API_KEY
    env["ALPACA_SECRET_KEY"] = config.API_SECRET
    env["ALPACA_PAPER_TRADE"] = "true"  # SELALU paper — sejalan guard config.py
    return env


class MCPClient:
    """Klien MCP sinkron: jalan di thread + event-loop privat sendiri."""

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._session = None
        self._ctx = None
        self._sess_ctx = None
        self.tools = []  # list schema OpenAI-compatible

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    async def _aopen(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=_server_command(),
            args=["--transport", "stdio"],
            env=_server_env(),
        )
        self._ctx = stdio_client(params)
        r, w = await self._ctx.__aenter__()
        self._sess_ctx = ClientSession(r, w)
        self._session = await self._sess_ctx.__aenter__()
        await self._session.initialize()
        listed = await self._session.list_tools()
        tools = []
        for t in listed.tools:
            schema = t.inputSchema or {"type": "object", "properties": {}}
            desc = (t.description or t.name)[:1024]
            tools.append({
                "type": "function",
                "function": {"name": t.name, "description": desc, "parameters": schema},
            })
        self.tools = tools
        return tools

    async def _acall(self, name, arguments):
        res = await self._session.call_tool(name, arguments or {})
        # gabungkan bagian teks dari hasil MCP
        out = []
        for c in (res.content or []):
            txt = getattr(c, "text", None)
            if txt is not None:
                out.append(txt)
            else:
                out.append(str(c))
        text = "\n".join(out) if out else "(no content)"
        if getattr(res, "isError", False):
            return {"error": text}
        return text

    async def _aclose(self):
        try:
            if self._sess_ctx:
                await self._sess_ctx.__aexit__(None, None, None)
        finally:
            if self._ctx:
                await self._ctx.__aexit__(None, None, None)

    # ---- API sinkron ----
    def open(self):
        return self._run(self._aopen())

    def call(self, name, arguments):
        return self._run(self._acall(name, arguments))

    def close(self):
        try:
            self._run(self._aclose())
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)


if __name__ == "__main__":
    # smoke test: buka server MCP resmi, cetak jumlah + contoh tool, panggil get_clock
    c = MCPClient()
    tools = c.open()
    print(f"MCP tools terkatalog: {len(tools)}")
    names = [t["function"]["name"] for t in tools]
    print("Contoh:", ", ".join(names[:12]))
    for probe in ("get_clock", "get_account_info"):
        if probe in names:
            print(f"\n[call] {probe} ->")
            print(str(c.call(probe, {}))[:400])
    c.close()
