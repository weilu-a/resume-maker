"""Bootstrap bundled Ollama (exe + model) so classmates need no separate install."""

from __future__ import annotations

import atexit
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

import requests

from app.utils.paths import ROOT_DIR

# Prefer a dedicated port so we don't fight a system-wide Ollama on 11434
DEFAULT_BUNDLE_HOST = "127.0.0.1:11435"

_proc: subprocess.Popen | None = None
_started_by_us = False


def runtime_dir() -> Path:
    return ROOT_DIR / "runtime"


def bundled_ollama_exe() -> Path:
    return runtime_dir() / "ollama" / "ollama.exe"


def bundled_models_dir() -> Path:
    return runtime_dir() / "models"


def is_bundled() -> bool:
    return bundled_ollama_exe().is_file() and (bundled_models_dir() / "manifests").exists()


def _port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _api_ok(base: str, timeout: float = 1.5) -> bool:
    try:
        r = requests.get(f"{base.rstrip('/')}/api/tags", timeout=timeout)
        return r.ok
    except Exception:
        return False


def _parse_host(hostport: str) -> tuple[str, int]:
    hostport = hostport.replace("http://", "").replace("https://", "").rstrip("/")
    if ":" in hostport:
        h, p = hostport.rsplit(":", 1)
        return h, int(p)
    return hostport, 11434


def ensure_ollama_ready(preferred_model: str = "qwen2.5:3b") -> dict[str, Any]:
    """
    Make sure an Ollama HTTP API is reachable.
    Priority:
      1) Already-running Ollama that has models (system or previous)
      2) Bundled runtime/ollama + runtime/models (auto-start)
    """
    existing = (os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
    if not existing.startswith("http"):
        existing = "http://" + existing

    # 1) Reuse healthy existing server
    if _api_ok(existing):
        os.environ["OLLAMA_HOST"] = existing
        return {"ok": True, "host": existing, "source": "existing", "bundled": False}

    # Also probe common default if env pointed elsewhere
    for probe in ("http://127.0.0.1:11434", f"http://{DEFAULT_BUNDLE_HOST}"):
        if probe != existing and _api_ok(probe):
            os.environ["OLLAMA_HOST"] = probe
            return {"ok": True, "host": probe, "source": "existing", "bundled": False}

    if not is_bundled():
        return {
            "ok": False,
            "host": existing,
            "source": "none",
            "bundled": False,
            "message": "未检测到内置 AI 运行时，且系统 Ollama 未启动",
        }

    return _start_bundled(preferred_model)


def _start_bundled(preferred_model: str) -> dict[str, Any]:
    global _proc, _started_by_us

    hostport = os.environ.get("OLLAMA_BUNDLE_HOST") or DEFAULT_BUNDLE_HOST
    host, port = _parse_host(hostport)
    base = f"http://{host}:{port}"

    exe = bundled_ollama_exe()
    models = bundled_models_dir()
    home = runtime_dir() / "ollama_home"
    home.mkdir(parents=True, exist_ok=True)
    log_path = runtime_dir() / "ollama_serve.log"

    env = os.environ.copy()
    env["OLLAMA_HOST"] = f"{host}:{port}"
    env["OLLAMA_MODELS"] = str(models.resolve())
    # Keep writable state next to the app, not in the user's profile
    env["OLLAMA_HOME"] = str(home.resolve())
    # Avoid pulling / writing into unexpected places
    env.setdefault("OLLAMA_KEEP_ALIVE", "10m")

    # If something already answers on bundle port, just use it
    if _api_ok(base):
        os.environ["OLLAMA_HOST"] = base
        return {"ok": True, "host": base, "source": "bundled-already", "bundled": True}

    creationflags = 0
    if os.name == "nt":
        # Hide console window; keep a handle so we can stop it on exit
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    try:
        log_f = open(log_path, "a", encoding="utf-8", errors="replace")
        _proc = subprocess.Popen(
            [str(exe), "serve"],
            cwd=str(exe.parent),
            env=env,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
        _started_by_us = True
        atexit.register(shutdown_ollama)
    except Exception as e:
        return {
            "ok": False,
            "host": base,
            "source": "bundled",
            "bundled": True,
            "message": f"启动内置 Ollama 失败: {e}",
        }

    # Wait until API is up (model load happens on first request)
    deadline = time.time() + 45
    while time.time() < deadline:
        if _api_ok(base, timeout=1.0):
            os.environ["OLLAMA_HOST"] = base
            return {
                "ok": True,
                "host": base,
                "source": "bundled",
                "bundled": True,
                "model": preferred_model,
                "message": f"内置 AI 已启动（{preferred_model}）",
            }
        if _proc.poll() is not None:
            return {
                "ok": False,
                "host": base,
                "source": "bundled",
                "bundled": True,
                "message": f"内置 Ollama 异常退出，详见 {log_path}",
            }
        time.sleep(0.4)

    return {
        "ok": False,
        "host": base,
        "source": "bundled",
        "bundled": True,
        "message": f"内置 Ollama 启动超时，详见 {log_path}",
    }


def shutdown_ollama() -> None:
    """Stop the process we started (leave system Ollama alone)."""
    global _proc, _started_by_us
    if not _started_by_us or _proc is None:
        return
    try:
        _proc.terminate()
        try:
            _proc.wait(timeout=5)
        except Exception:
            _proc.kill()
    except Exception:
        pass
    _proc = None
    _started_by_us = False
