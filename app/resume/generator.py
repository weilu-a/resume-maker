"""Resume generation: polish with AI and export PDF."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.ai.ollama_client import polish_resume_data
from app.resume.pdf_export import export_resume_pdf, payload_to_context, render_template_html
from app.resume.pdf_preview import render_pdf_preview
from app.utils.paths import MODELS_RESUME_DIR, OUTPUT_DIR, TEMPLATES_DIR

DEFAULT_TEMPLATE_ID = "blue-minimal"


def list_templates() -> list[dict[str, Any]]:
    """Load templates from models/resume (PDF designs + previews)."""
    index_path = MODELS_RESUME_DIR / "index.json"
    if not index_path.exists():
        # Fallback to legacy HTML template index
        index_path = TEMPLATES_DIR / "index.json"
        with open(index_path, encoding="utf-8") as f:
            data = json.load(f)
        templates = data.get("templates", [])
        for t in templates:
            preview = TEMPLATES_DIR / t["id"] / "preview.svg"
            if not preview.exists():
                preview = TEMPLATES_DIR / t["id"] / "preview.png"
            t["preview_url"] = preview.resolve().as_uri() if preview.exists() else ""
        return templates

    with open(index_path, encoding="utf-8") as f:
        data = json.load(f)
    templates = data.get("templates", [])
    for t in templates:
        preview_rel = t.get("preview") or f"previews/{t['id']}.png"
        preview = MODELS_RESUME_DIR / preview_rel
        t["preview_url"] = preview.resolve().as_uri() if preview.exists() else ""
        pdf_file = t.get("file") or f"{t['id']}.pdf"
        pdf_path = MODELS_RESUME_DIR / pdf_file
        t["pdf_url"] = pdf_path.resolve().as_uri() if pdf_path.exists() else ""
        t["has_html"] = (TEMPLATES_DIR / t["id"] / "template.html").exists()
    return templates


def default_template_id() -> str:
    templates = list_templates()
    if templates:
        return templates[0]["id"]
    return DEFAULT_TEMPLATE_ID


def generate_resume(payload: dict[str, Any]) -> dict[str, Any]:
    template_id = payload.get("template_id") or default_template_id()
    html_path = TEMPLATES_DIR / template_id / "template.html"
    if not html_path.exists():
        raise FileNotFoundError(f"模板不存在: {template_id}")

    polished = polish_resume_data(payload)
    name = polished.get("name") or "未命名"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_", " "))[:20].strip() or "resume"
    out_path = OUTPUT_DIR / f"{safe_name}_{stamp}.pdf"

    context = payload_to_context(polished)

    export_resume_pdf(template_id, context, out_path)
    preview_html = render_template_html(template_id, context)
    page_preview = render_pdf_preview(out_path)

    return {
        "ok": True,
        "pdf_path": str(out_path),
        "preview_url": page_preview["preview_url"],
        "ai_source": polished.get("ai_source", "fallback"),
        "preview_html": preview_html,
        "polished": {
            "name": context["name"],
            "phone": context["phone"],
            "email": context["email"],
            "summary": context["summary"],
            "experiences": context["experiences"],
            "education": context["education"],
            "projects": context["projects"],
        },
    }
