"""Render PDF first page to PNG for in-app A4 preview."""

from __future__ import annotations

import uuid
from pathlib import Path

from app.utils.paths import CACHE_DIR, ensure_dirs


def render_pdf_preview(pdf_path: str | Path, scale: float = 2.0) -> dict[str, str]:
    """Render the first page of a PDF to a PNG cache file.

    Returns ``path`` and ``preview_url`` (file URI for webview <img>).
    """
    ensure_dirs()
    src = Path(pdf_path)
    if not src.exists():
        raise FileNotFoundError(f"PDF 不存在: {pdf_path}")

    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(src))
    try:
        if len(pdf) < 1:
            raise RuntimeError("PDF 没有页面")
        page = pdf[0]
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil()
    finally:
        pdf.close()

    out = CACHE_DIR / f"preview_{uuid.uuid4().hex}.png"
    image.save(out, format="PNG")
    return {"path": str(out), "preview_url": out.resolve().as_uri()}
