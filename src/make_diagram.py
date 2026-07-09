"""Render docs/architecture.mmd to a PNG using the mermaid.ink service.

    e:/heshara/Test_task/env4/Scripts/python.exe src/make_diagram.py

graph: docs/architecture.png
"""
from __future__ import annotations

import base64
import json
import urllib.request
import zlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MMD_FILE = PROJECT_ROOT / "docs" / "architecture.mmd"
PNG_FILE = PROJECT_ROOT / "docs" / "architecture.png"
import config
from logger import get_logger


log = get_logger()

INBOX_DIR = config.DATA_DIR / "inbox"
INBOX_DIR.mkdir(parents=True, exist_ok=True)

def _encode(graph: str) -> str:
    """Encode the graph in the pako format mermaid.ink expects."""
    state = {"code": graph, "mermaid": {"theme": "default"}}
    raw = json.dumps(state).encode("utf-8")
    compressed = zlib.compress(raw, 9)
    return "pako:" + base64.urlsafe_b64encode(compressed).decode("ascii")


def main() -> int:
    if not MMD_FILE.exists():
        log.error(" Diagram source not found: %s", MMD_FILE)
        return 1
   ## draw the graph
   
    graph = MMD_FILE.read_text(encoding="utf-8")
    url = f"https://mermaid.ink/img/{_encode(graph)}?type=png"

    log.info("Rendering diagram via mermaid.ink ...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as exc:  # noqa: BLE001
        log.error(" Could not render online: %s: %s", type(exc).__name__, exc)
        log.error(" Export -> PNG and save it as docs/architecture.png")
        return 1

    PNG_FILE.write_bytes(data)
    log.info(" Saved diagram to %s  (%d bytes)", PNG_FILE, len(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
