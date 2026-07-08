"""Central configuration loaded from environment variables."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

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
SAMPLES_DIR = DATA_DIR / "samples"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
OUTPUT_DIR = DATA_DIR / "output"
CHROMA_DIR = DATA_DIR / "chroma"

for _d in (DATA_DIR, SAMPLES_DIR, KNOWLEDGE_DIR, OUTPUT_DIR, CHROMA_DIR):
    _d.mkdir(parents=True, exist_ok=True)
