"""Render Jinja templates and export PDF with Chinese font support."""

from __future__ import annotations

import html as html_lib
import io
import os
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from xhtml2pdf import pisa
from xhtml2pdf.default import DEFAULT_FONT

from app.utils.paths import FONTS_DIR, TEMPLATES_DIR


def _find_chinese_font() -> str | None:
    candidates = [
        FONTS_DIR / "NotoSansSC-Regular.otf",
        FONTS_DIR / "NotoSansSC-Regular.ttf",
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttf"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


def _register_font() -> str:
    font_path = _find_chinese_font()
    font_name = "ResumeCN"
    if font_path:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        try:
            if font_path.lower().endswith(".ttc"):
                pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=0))
            else:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
            DEFAULT_FONT["helvetica"] = font_name
            DEFAULT_FONT["times"] = font_name
            DEFAULT_FONT["courier"] = font_name
            return font_name
        except Exception:
            pass
    return "Helvetica"


def soft_break(text: Any, width: int = 14) -> Markup:
    """Force line breaks for PDF (xhtml2pdf ignores CSS word-break on CJK)."""
    if text is None:
        return Markup("")
    s = str(text)
    if not s:
        return Markup("")
    break_after = set("，。；：、？！,.;:!?（）()【】[]")
    parts: list[str] = []
    for line in s.replace("\r\n", "\n").split("\n"):
        buf: list[str] = []
        count = 0
        for ch in line:
            buf.append(ch)
            if ch.isspace() or ch in break_after:
                count = 0
                continue
            count += 1
            if count >= max(4, int(width)):
                buf.append("\n")
                count = 0
        parts.append("".join(buf))
    escaped = html_lib.escape("\n".join(parts))
    return Markup(escaped.replace("\n", "<br/>"))


def fmt(text: Any, width: int = 22) -> Markup:
    """Escape + forced breaks for resume body fields."""
    return soft_break(text, width)


def _jinja_env(template_id: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR / template_id)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["soft_break"] = soft_break
    env.filters["fmt"] = fmt
    return env


def payload_to_context(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize form / polished payload into template context."""
    photo = payload.get("photo_path") or payload.get("photo_uri") or ""
    if photo and not str(photo).startswith("file:"):
        p = Path(str(photo))
        photo_uri = p.resolve().as_uri() if p.exists() else ""
    else:
        photo_uri = str(photo) if photo else ""

    return {
        "name": payload.get("name", "") or "",
        "phone": payload.get("phone", "") or "",
        "email": payload.get("email", "") or "",
        "summary": payload.get("summary", "") or "",
        "intent": payload.get("intent", "") or "",
        "photo_uri": photo_uri,
        "experiences": payload.get("experiences") or [],
        "education": payload.get("education") or [],
        "projects": payload.get("projects") or [],
        "skills": payload.get("skills", "") or "",
    }


def render_template_html(template_id: str, context: dict[str, Any]) -> str:
    env = _jinja_env(template_id)
    font_name = _register_font()
    context = {**context, "font_name": font_name}
    tmpl = env.get_template("template.html")
    return tmpl.render(**context)


def html_to_pdf(html: str, output_path: Path) -> Path:
    _register_font()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as out:
        result = pisa.CreatePDF(
            io.BytesIO(html.encode("utf-8")),
            dest=out,
            encoding="utf-8",
            link_callback=_link_callback,
        )
    if result.err:
        raise RuntimeError("PDF 生成失败，请检查模板 HTML 与字体配置")
    return output_path


def _link_callback(uri: str, rel: str) -> str:
    """Resolve local file paths for images in HTML."""
    if uri.startswith("file:///"):
        path = uri[8:]
        if re.match(r"^/[A-Za-z]:", path):
            path = path[1:]
        return path
    if uri.startswith("file://"):
        return uri[7:]
    if os.path.isfile(uri):
        return uri
    candidate = TEMPLATES_DIR.parent / uri
    if candidate.exists():
        return str(candidate)
    return uri


def export_resume_pdf(template_id: str, context: dict[str, Any], output_path: Path) -> Path:
    html = render_template_html(template_id, context)
    return html_to_pdf(html, output_path)
