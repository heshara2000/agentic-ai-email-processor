"""Central configuration loaded from environment variables."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (override=True so .env wins over stale OS env vars)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# --- Email (IMAP) ---
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
IMAP_FOLDER = os.getenv("IMAP_FOLDER", "INBOX")

# --- Pipeline ---
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

# --- Paths ---
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge_base"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
LOGS_DIR = PROJECT_ROOT / "logs"

for _d in (DATA_DIR,KNOWLEDGE_DIR, OUTPUT_DIR, UPLOADS_DIR, CHROMA_DIR, LOGS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
