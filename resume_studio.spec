# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for 简历工坊 desktop app (onedir)."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None
root = Path(SPECPATH)

datas = [
    (str(root / "frontend"), "frontend"),
    (str(root / "templates"), "templates"),
    (str(root / "fonts"), "fonts"),
    (str(root / ".env"), "."),
]
# PDF 简历模板元数据（若存在）
models_resume = root / "models" / "resume"
if models_resume.is_dir():
    datas.append((str(models_resume), "models/resume"))

binaries = []
hidden = [
    "webview",
    "jinja2",
    "pdfplumber",
    "xhtml2pdf",
    "reportlab",
    "reportlab.graphics.barcode.code128",
    "PIL",
    "requests",
    "dotenv",
    "clr_loader",
    "pythonnet",
    "app",
    "app.api",
    "app.main",
    "app.ai.ollama_client",
    "app.ai.deepseek_client",
    "app.ai.interview_agent",
    "app.interview.store",
    "app.resume.generator",
    "app.resume.optimizer",
    "app.resume.pdf_export",
    "app.resume.pdf_preview",
    "app.utils.paths",
    "app.utils.config",
]

for pkg in ("reportlab", "xhtml2pdf", "pdfplumber", "PIL", "pythonnet", "clr_loader"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hidden += pkg_hidden

hidden += collect_submodules("reportlab")
hidden += collect_submodules("reportlab.graphics.barcode")
hidden += collect_submodules("xhtml2pdf")
hidden += collect_submodules("app")
hidden += collect_submodules("pythonnet")
hidden += collect_submodules("clr_loader")
hidden = sorted(set(hidden))

a = Analysis(
    [str(root / "app" / "main.py")],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ResumeStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ResumeStudio",
)
