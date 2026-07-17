from __future__ import annotations

import sys
from pathlib import Path


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _app_root() -> Path:
    """Writable root: next to .exe when packaged, else project root."""
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _resource_root() -> Path:
    """Read-only bundled assets (frontend / templates / fonts / models)."""
    if _is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent / "_internal"
    return Path(__file__).resolve().parents[2]


# Writable (user data, exports, .env)
ROOT_DIR = _app_root()
# Bundled resources
RESOURCE_DIR = _resource_root()

APP_DIR = RESOURCE_DIR / "app"
FRONTEND_DIR = RESOURCE_DIR / "frontend"
TEMPLATES_DIR = RESOURCE_DIR / "templates"
MODELS_RESUME_DIR = RESOURCE_DIR / "models" / "resume"
FONTS_DIR = RESOURCE_DIR / "fonts"

DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
CACHE_DIR = DATA_DIR / "cache"
INTERVIEWS_DIR = DATA_DIR / "interviews"

__all__ = [
    "ROOT_DIR",
    "RESOURCE_DIR",
    "APP_DIR",
    "FRONTEND_DIR",
    "TEMPLATES_DIR",
    "MODELS_RESUME_DIR",
    "DATA_DIR",
    "OUTPUT_DIR",
    "FONTS_DIR",
    "CACHE_DIR",
    "INTERVIEWS_DIR",
    "ensure_dirs",
]


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    INTERVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "photos").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "uploads").mkdir(parents=True, exist_ok=True)
