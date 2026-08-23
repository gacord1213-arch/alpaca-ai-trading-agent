"""
config.py — memuat kredensial dari .env secara aman.
PAPER TRADING ONLY. .env tidak pernah di-commit (lihat .gitignore).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Alpaca (paper) ---
API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
IS_PAPER = "paper-api" in BASE_URL

# --- LLM (gorouter / OpenAI-compatible) ---
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://gorouter.app/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-opus-4-8-thinking")

if not API_KEY or not API_SECRET:
    raise RuntimeError("Kredensial Alpaca tidak ditemukan. Isi .env dulu.")
if not IS_PAPER:
    raise RuntimeError("SAFETY STOP: BASE_URL bukan paper-api. Agent ini paper-only.")
if not LLM_API_KEY:
    raise RuntimeError("LLM_API_KEY tidak ditemukan. Isi .env dulu.")
