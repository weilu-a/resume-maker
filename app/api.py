"""pywebview JS API bridge."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import webview

from app.ai import deepseek_client
from app.ai.interview_agent import get_opening, reply as interview_agent_reply, generate_summary as interview_summary_gen
from app.ai.ollama_client import check_health
from app.ai.ollama_runtime import ensure_ollama_ready
from app.interview.store import list_interviews as list_saved_interviews
from app.interview.store import save_interview as persist_interview
from app.resume.generator import default_template_id, generate_resume, list_templates
from app.resume.optimizer import (
    export_optimized,
    extract_pdf_text as read_pdf_text,
    optimize_resume,
    render_optimized_html,
)
from app.resume.pdf_export import payload_to_context, render_template_html
from app.resume.pdf_preview import render_pdf_preview
from app.utils.config import load_env
from app.utils.paths import DATA_DIR, OUTPUT_DIR, TEMPLATES_DIR, ensure_dirs


class ApiBridge:
    def __init__(self) -> None:
        load_env()
        ensure_dirs()
        self._window: webview.Window | None = None
        self._last_optimize_result: dict[str, Any] | None = None
        self._last_optimized_pdf: str | None = None

    def set_window(self, window: webview.Window) -> None:
        self._window = window

    def ping(self) -> dict[str, Any]:
        return {"ok": True, "app": "简历工坊"}

    def check_ollama(self) -> dict[str, Any]:
        runtime = ensure_ollama_ready()
        health = check_health()
        health["runtime"] = runtime
        if runtime.get("bundled") and health.get("online"):
            health["message"] = health.get("message") or "内置 AI 就绪"
        return health

    def check_deepseek(self) -> dict[str, Any]:
        return deepseek_client.check_health()

    def list_templates(self) -> list[dict[str, Any]]:
        return list_templates()

    def pick_photo(self) -> dict[str, Any]:
        if not self._window:
            return {"ok": False, "error": "窗口未就绪"}
        try:
            files = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=("图片文件 (*.png;*.jpg;*.jpeg;*.webp)",),
            )
        except Exception as e:
            return {"ok": False, "error": f"打开文件对话框失败: {str(e)}"}
        if not files:
            return {"ok": False, "cancelled": True}
        src = Path(files[0])
        dest = DATA_DIR / "photos" / f"{uuid.uuid4().hex}{src.suffix.lower()}"
        shutil.copy2(src, dest)
        return {"ok": True, "path": str(dest), "uri": dest.resolve().as_uri()}

    def pick_pdf(self) -> dict[str, Any]:
        if not self._window:
            return {"ok": False, "error": "窗口未就绪"}
        try:
            files = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=("PDF 文件 (*.pdf)",),
            )
        except Exception as e:
            return {"ok": False, "error": f"打开文件对话框失败: {str(e)}"}
        if not files:
            return {"ok": False, "cancelled": True}
        src = Path(files[0])
        dest = DATA_DIR / "uploads" / f"{uuid.uuid4().hex}.pdf"
        shutil.copy2(src, dest)
        return {"ok": True, "path": str(dest), "name": src.name}

    def extract_pdf_text(self, pdf_path: str) -> dict[str, Any]:
        """Extract plain text from an uploaded resume PDF (pdfplumber)."""
        try:
            path = Path(pdf_path)
            if not path.exists():
                return {"ok": False, "error": f"文件不存在: {pdf_path}"}
            if not path.is_file():
                return {"ok": False, "error": f"不是文件: {pdf_path}"}
            
            file_size = path.stat().st_size
            if file_size == 0:
                return {"ok": False, "error": "文件为空"}
            
            text = read_pdf_text(pdf_path)
            if not text or not text.strip():
                return {"ok": False, "error": "未能从 PDF 提取到文字（可能是扫描件或加密文件）"}
            
            return {
                "ok": True,
                "text": text,
                "chars": len(text),
                "preview": (text or "")[:500],
            }
        except FileNotFoundError as e:
            return {"ok": False, "error": f"文件未找到: {e}"}
        except PermissionError as e:
            return {"ok": False, "error": f"权限错误: {e}"}
        except Exception as e:
            import traceback
            return {"ok": False, "error": f"解析失败: {str(e)}\n\n{traceback.format_exc()[:500]}"}

    def get_interview_opening(self, company_type: str = "bigtech") -> dict[str, Any]:
        try:
            return get_opening(company_type or "bigtech")
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def interview_reply(self, payload_json: str) -> dict[str, Any]:
        try:
            payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
            messages = payload.get("messages") or []
            return interview_agent_reply(
                messages,
                company_type=payload.get("company_type") or payload.get("companyType") or "bigtech",
                tech_direction=payload.get("tech_direction")
                or payload.get("techDirection")
                or "frontend",
                difficulty=payload.get("difficulty") or "intermediate",
                resume_text=payload.get("resume_text") or payload.get("resumeText") or "",
            )
        except Exception as e:
            return {"ok": False, "error": str(e), "speech": "", "end_interview": False}

    def interview_summary(self, payload_json: str) -> dict[str, Any]:
        try:
            payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
            messages = payload.get("messages") or []
            return interview_summary_gen(
                messages,
                company_type=payload.get("company_type") or payload.get("companyType") or "bigtech",
                tech_direction=payload.get("tech_direction")
                or payload.get("techDirection")
                or "frontend",
                difficulty=payload.get("difficulty") or "intermediate",
                resume_text=payload.get("resume_text") or payload.get("resumeText") or "",
            )
        except Exception as e:
            return {"ok": False, "error": str(e), "summary": ""}

    def save_interview(self, payload_json: str) -> dict[str, Any]:
        try:
            payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
            return persist_interview(payload or {})
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def list_interviews(self) -> list[dict[str, Any]]:
        try:
            return list_saved_interviews()
        except Exception:
            return []

    def generate_resume(self, payload_json: str) -> dict[str, Any]:
        try:
            payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
            result = generate_resume(payload)
            return result
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def preview_form(self, payload_json: str) -> dict[str, Any]:
        """Render selected template HTML for live preview (no AI polish)."""
        try:
            payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
            template_id = (payload or {}).get("template_id") or default_template_id()
            html_path = TEMPLATES_DIR / template_id / "template.html"
            if not html_path.exists():
                return {"ok": False, "error": f"模板不存在: {template_id}"}
            context = payload_to_context(payload or {})
            html = render_template_html(template_id, context)
            return {"ok": True, "html": html, "template_id": template_id}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def optimize_resume(self, pdf_path: str, template_id: str = "") -> dict[str, Any]:
        try:
            result = optimize_resume(pdf_path)
            self._last_optimize_result = result
            tid = template_id or default_template_id()
            # 只渲染预览，不在切换模板时落盘；首次优化也不批量写 PDF
            html_preview = render_optimized_html(result, tid)
            slim = {k: v for k, v in result.items() if k != "raw_text"}
            slim["raw_preview"] = (result.get("raw_text") or "")[:500]
            slim["preview_html"] = html_preview.get("html", "")
            slim["preview_url"] = ""
            slim["pdf_path"] = ""
            slim["template_id"] = html_preview.get("template_id", tid)
            slim["resume_name"] = html_preview.get("name", "")
            return slim
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def preview_optimized(self, template_id: str = "") -> dict[str, Any]:
        """Re-render optimized resume HTML only (no PDF write on template switch)."""
        try:
            if not self._last_optimize_result:
                return {"ok": False, "error": "请先完成简历优化"}
            tid = template_id or default_template_id()
            return render_optimized_html(self._last_optimize_result, tid)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def export_optimized(self, template_id: str = "") -> dict[str, Any]:
        try:
            if not self._last_optimize_result:
                return {"ok": False, "error": "请先完成简历优化"}
            tid = template_id or default_template_id()
            exported = export_optimized(self._last_optimize_result, tid)
            self._last_optimized_pdf = exported.get("pdf_path")
            return exported
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def render_pdf_preview(self, pdf_path: str) -> dict[str, Any]:
        try:
            preview = render_pdf_preview(pdf_path)
            return {"ok": True, **preview}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def open_output_folder(self) -> dict[str, Any]:
        import os
        import subprocess
        import sys

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = str(OUTPUT_DIR)
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
            return {"ok": True, "path": path}
        except Exception as e:
            return {"ok": False, "error": str(e), "path": path}

    def list_recent_outputs(self) -> list[dict[str, Any]]:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(OUTPUT_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
        items = []
        for f in files[:10]:
            items.append(
                {
                    "name": f.name,
                    "path": str(f),
                    "mtime": f.stat().st_mtime,
                }
            )
        return items
