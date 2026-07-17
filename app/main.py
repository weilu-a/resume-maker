"""Desktop entry: pywebview window for 简历工坊."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python app/main.py` from project root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import webview

from app.ai.ollama_runtime import ensure_ollama_ready, shutdown_ollama
from app.api import ApiBridge
from app.utils.paths import FRONTEND_DIR, ensure_dirs


def main() -> None:
    ensure_dirs()
    # Start bundled AI if present (no-op when using system Ollama)
    try:
        ensure_ollama_ready()
    except Exception:
        pass

    index = FRONTEND_DIR / "index.html"
    if not index.exists():
        raise FileNotFoundError(f"前端入口不存在: {index}")

    api = ApiBridge()
    window = webview.create_window(
        title="简历工坊 · Resume Studio",
        url=index.as_uri(),
        js_api=api,
        width=1280,
        height=800,
        min_size=(1024, 680),
    )
    api.set_window(window)
    try:
        webview.start(debug=False)
    finally:
        shutdown_ollama()


if __name__ == "__main__":
    main()
