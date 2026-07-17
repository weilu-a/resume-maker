"""Load local .env configuration (DeepSeek etc.)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from app.utils.paths import ROOT_DIR

_ENV_LOADED = False


def load_env(force: bool = False) -> Path:
    """Load project-root .env into process env. Safe to call multiple times."""
    global _ENV_LOADED
    env_path = ROOT_DIR / ".env"
    if force or not _ENV_LOADED:
        load_dotenv(env_path, override=False)
        _ENV_LOADED = True
    return env_path


def deepseek_settings() -> dict[str, str]:
    load_env()
    return {
        "api_key": (os.getenv("DEEPSEEK_API_KEY") or "").strip(),
        "base_url": (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").rstrip("/"),
        "model": (os.getenv("DEEPSEEK_MODEL") or "deepseek-v4-flash").strip(),
    }
