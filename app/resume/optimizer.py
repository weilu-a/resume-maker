"""Resume optimization: extract PDF text, AI rewrite, re-export."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import pdfplumber

from app.ai.ollama_client import optimize_resume_text
from app.resume.generator import DEFAULT_TEMPLATE_ID, default_template_id
from app.resume.pdf_export import export_resume_pdf, render_template_html
from app.resume.pdf_preview import render_pdf_preview
from app.utils.paths import OUTPUT_DIR, TEMPLATES_DIR

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(?:1[3-9]\d[\s-]?\d{4}[\s-]?\d{4}|\d{3,4}[\s-]?\d{7,8})(?!\d)")
_PERIOD_RE = re.compile(
    r"((?:19|20)\d{2}\s*[./年-]?\s*\d{0,2}\s*(?:月)?\s*[-–—至到~～]+\s*(?:至今|今|(?:19|20)\d{2}\s*[./年-]?\s*\d{0,2}\s*(?:月)?))"
)

# (match_keywords, kind, display_label)
_SECTION_DEFS: list[tuple[tuple[str, ...], str, str]] = [
    (("基本信息", "个人信息", "联系方式"), "basic", "基本信息"),
    (("求职意向", "应聘岗位"), "intent", "求职意向"),
    (("自我评价", "自我概述", "个人评价", "个人概述", "自我介绍"), "summary", "自我评价"),
    (("专业技能", "掌握技能", "技能证书", "持有证书", "擅长技能"), "skills", "专业技能"),
    (("教育背景", "教育经历", "学历背景", "学业背景"), "education", "教育背景"),
    (("工作经历", "工作经验", "任职经历"), "experience", "工作经历"),
    (("实习经历", "实习经验"), "experience", "实习经历"),
    (("项目经历", "项目经验", "项目案例"), "projects", "项目经历"),
    (("校园经历", "在校经历", "社团经历"), "projects", "校园经历"),
    (("所获荣誉", "获奖情况", "荣誉奖项"), "honors", "所获荣誉"),
]

_SKIP_TITLES = {
    "personal resume",
    "resume",
    "个人简历",
    "简历",
    "curriculum vitae",
    "cv",
    # 模板里的英文副标题（PDF 抽取后会混进正文）
    "personal information",
    "educational background",
    "education background",
    "work experience",
    "project experience",
    "project experiences",
    "self-evaluation",
    "self evaluation",
    "skills",
    "skill",
    "professional skills",
}

_EN_SECTION_MAP: dict[str, tuple[str, str]] = {
    "personal information": ("basic", "基本信息"),
    "educational background": ("education", "教育背景"),
    "education background": ("education", "教育背景"),
    "work experience": ("experience", "工作经历"),
    "internship experience": ("experience", "实习经历"),
    "project experience": ("projects", "项目经历"),
    "project experiences": ("projects", "项目经历"),
    "professional skills": ("skills", "专业技能"),
    "skills": ("skills", "专业技能"),
    "self-evaluation": ("summary", "自我评价"),
    "self evaluation": ("summary", "自我评价"),
}

_BAD_NAME_WORDS = {
    "skills",
    "skill",
    "resume",
    "education",
    "educational",
    "experience",
    "experiences",
    "information",
    "background",
    "personal",
    "project",
    "projects",
    "evaluation",
    "professional",
    "internship",
    "summary",
    "profile",
    "contact",
    "objective",
}


def extract_pdf_text(pdf_path: str) -> str:
    from pathlib import Path

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {pdf_path}")
    
    file_size = path.stat().st_size
    if file_size > 10 * 1024 * 1024:
        raise ValueError(f"文件过大（{file_size / 1024 / 1024:.1f}MB），请使用小于 10MB 的 PDF")
    
    chunks: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        if len(pdf.pages) > 20:
            raise ValueError(f"PDF 页数过多（{len(pdf.pages)}页），请使用少于 20 页的 PDF")
        
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                chunks.append(text.strip())
                
            if len(chunks) > 50:
                break
    
    result = "\n\n".join(chunks)
    if len(result) > 50000:
        result = result[:50000] + "\n\n...（内容过长，已截断）"
    
    return result


def optimize_resume(pdf_path: str) -> dict[str, Any]:
    raw_text = extract_pdf_text(pdf_path)
    result = optimize_resume_text(raw_text)
    result["ok"] = True
    result["source_path"] = pdf_path
    result["raw_text"] = raw_text
    try:
        original_preview = render_pdf_preview(pdf_path)
        result["original_preview_url"] = original_preview["preview_url"]
    except Exception:
        result["original_preview_url"] = ""
    return result


def _looks_like_person_name(text: str) -> bool:
    t = (text or "").strip()
    if not t or not (2 <= len(t) <= 8):
        return False
    low = t.lower()
    if low in _SKIP_TITLES or low in _BAD_NAME_WORDS:
        return False
    skip = (
        "简历",
        "自我",
        "工作",
        "项目",
        "教育",
        "技能",
        "经历",
        "概述",
        "评价",
        "总结",
        "联系",
        "基本",
        "信息",
        "意向",
        "姓名",
        "电话",
        "邮箱",
        "院校",
    )
    if any(k in t for k in skip):
        return False
    # 纯英文单词（如 Skills）不当作姓名
    if re.fullmatch(r"[A-Za-z][A-Za-z .·'-]{0,20}", t):
        if low in _BAD_NAME_WORDS or " " not in t and len(t) <= 12:
            # 单个英文词基本都不是中文简历姓名
            return False
    if re.fullmatch(r"[\u4e00-\u9fff]{2,4}", t):
        return True
    return bool(re.fullmatch(r"[A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?", t))


def _is_chrome_line(line: str) -> bool:
    s = (line or "").strip()
    if not s:
        return True
    low = s.lower()
    if low in _SKIP_TITLES or low in _EN_SECTION_MAP:
        return True
    if s in ("个人简历", "简历", "RESUME", "PERSONAL RESUME"):
        return True
    # 纯英文副标题行
    if re.fullmatch(r"[A-Za-z][A-Za-z /&-]{2,40}", s) and low in _BAD_NAME_WORDS.union(
        {k.split()[0] for k in _EN_SECTION_MAP}
    ):
        return True
    return False


def _normalize_body(text: str) -> str:
    """Make long PDF-extracted blobs readable with line breaks."""
    if isinstance(text, (tuple, list)):
        text = "\n".join(str(x) for x in text)
    t = (text or "").replace("\r\n", "\n").strip()
    if not t:
        return ""
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    if t.count("\n") < 2 and len(t) > 60:
        t = re.sub(r"([。！？；;])\s*", r"\1\n", t)
        t = re.sub(r"\s*[•●◆▪]\s*", "\n• ", t)
        t = re.sub(r"(?:^|[\n])\s*(\d+[\.、）)])\s*", r"\n\1 ", t)

    junk = ("PERSONAL RESUME", "个人简历", "RESUME")
    lines = []
    for ln in t.splitlines():
        s = ln.strip()
        if not s:
            continue
        if _is_chrome_line(s):
            continue
        if s.upper() in {j.upper() for j in junk} or s in junk:
            continue
        if s in ("简历内容",):
            continue
        # 去掉行首粘连的英文副标题：如 "Educational background某某大学"
        for en in sorted(_EN_SECTION_MAP.keys(), key=len, reverse=True):
            if s.lower().startswith(en):
                s = s[len(en) :].lstrip(" ·:-—")
                break
        if not s or _is_chrome_line(s):
            continue
        lines.append(s)
    return "\n".join(lines).strip()


def _split_period(text: str) -> tuple[str, str]:
    m = _PERIOD_RE.search(text or "")
    if not m:
        return "", text
    period = re.sub(r"\s+", "", m.group(1))
    rest = (text[: m.start()] + text[m.end() :]).strip(" \n，,、|-/")
    return period, rest


def _match_section_header(line: str) -> tuple[str, str] | None:
    s = (line or "").strip()
    if not s or len(s) > 40:
        return None
    low = s.lower()
    if low in _EN_SECTION_MAP:
        return _EN_SECTION_MAP[low]
    for keys, kind, label in _SECTION_DEFS:
        for k in keys:
            if s == k or s.startswith(k) or (k in s and len(s) <= len(k) + 4):
                return kind, label
    return None


def parse_resume_text(text: str) -> dict[str, Any]:
    """Split raw resume text into structured fields by Chinese section headers."""
    raw = (text or "").replace("\r\n", "\n")
    # Insert newlines before known headers if stuck mid-line
    for keys, _kind, _label in _SECTION_DEFS:
        for k in keys:
            raw = re.sub(rf"(?<![=\n])({re.escape(k)})", r"\n\1", raw)

    lines = [ln.strip() for ln in raw.splitlines()]
    lines = [ln for ln in lines if ln]

    name = ""
    phone = ""
    email = ""
    blocks: dict[str, list[str]] = {}
    current: str | None = None

    email_m = _EMAIL_RE.search(raw)
    if email_m:
        email = email_m.group(0)
    phone_m = _PHONE_RE.search(raw.replace(" ", ""))
    if phone_m:
        phone = phone_m.group(0)

    for ln in lines:
        if ln.lower() in _SKIP_TITLES or ln in ("PERSONAL RESUME", "RESUME", "个人简历"):
            continue
        if _looks_like_person_name(ln) and not name:
            name = ln
            continue
        hit = _match_section_header(ln)
        if hit:
            current = hit[0]
            blocks.setdefault(current, [])
            continue
        if current:
            blocks.setdefault(current, []).append(ln)
        elif not name and _looks_like_person_name(ln):
            name = ln

    def join(kind: str) -> str:
        return _normalize_body("\n".join(blocks.get(kind, [])))

    education: list[dict[str, str]] = []
    edu_body = join("education")
    if edu_body:
        period, body = _split_period(edu_body)
        first = body.splitlines()[0] if body else "教育背景"
        rest = "\n".join(body.splitlines()[1:]).strip() if body.count("\n") else ""
        education.append(
            {
                "school": first[:48],
                "period": period,
                "degree": "",
                "major": rest[:160] if rest else "",
            }
        )

    experiences: list[dict[str, str]] = []
    for kind in ("experience",):
        body = join(kind)
        if not body:
            continue
        # Split multiple jobs by period markers
        chunks = re.split(r"\n(?=(?:19|20)\d{2})", body)
        parts = [c.strip() for c in chunks if c.strip()] or [body]
        for part in parts[:4]:
            period, rest = _split_period(part)
            lines_p = [x for x in rest.splitlines() if x.strip()]
            company = lines_p[0][:40] if lines_p else "工作经历"
            title = lines_p[1][:40] if len(lines_p) > 1 and len(lines_p[1]) < 30 else ""
            desc_lines = lines_p[2:] if title else lines_p[1:]
            desc = _normalize_body("\n".join(desc_lines) if desc_lines else (rest if rest != company else ""))
            if not desc and rest and rest != company:
                desc = _normalize_body("\n".join(lines_p[1:]) if len(lines_p) > 1 else rest)
            experiences.append(
                {
                    "company": company,
                    "period": period,
                    "title": title,
                    "description": desc or rest,
                }
            )

    projects: list[dict[str, str]] = []
    proj_body = join("projects")
    if proj_body:
        period, rest = _split_period(proj_body)
        lines_p = [x for x in rest.splitlines() if x.strip()]
        pname = lines_p[0][:40] if lines_p else "项目经历"
        desc = _normalize_body("\n".join(lines_p[1:]) if len(lines_p) > 1 else rest)
        projects.append({"name": pname, "period": period, "description": desc})

    summary = join("summary")
    skills = join("skills")
    intent = join("intent")[:40]
    basic = join("basic")
    if basic:
        em = _EMAIL_RE.search(basic)
        if em:
            email = em.group(0)
        ph = _PHONE_RE.search(basic.replace(" ", ""))
        if ph:
            phone = ph.group(0)

    return {
        "name": name or "优化简历",
        "phone": phone,
        "email": email,
        "summary": summary,
        "intent": intent,
        "skills": skills,
        "education": education,
        "experiences": experiences,
        "projects": projects,
        "photo_uri": "",
    }


def _apply_optimized_sections(base: dict[str, Any], sections: list[dict[str, Any]]) -> dict[str, Any]:
    """Overlay AI-optimized section contents onto parsed structure."""
    ctx = dict(base)
    for sec in sections or []:
        title = (sec.get("title") or "").strip()
        content = _normalize_body(sec.get("content") or "")
        if not content and not title:
            continue
        if title.lower() in _SKIP_TITLES or title in ("简历内容",):
            continue
        if _looks_like_person_name(title):
            ctx["name"] = title
            # contact-only body
            em = _EMAIL_RE.search(content)
            if em:
                ctx["email"] = em.group(0)
            ph = _PHONE_RE.search(content.replace(" ", ""))
            if ph:
                ctx["phone"] = ph.group(0)
            continue

        hit = _match_section_header(title)
        kind = hit[0] if hit else None
        if not kind:
            # fuzzy
            for keys, k, _lab in _SECTION_DEFS:
                if any(key in title for key in keys):
                    kind = k
                    break
        if kind == "summary" and content:
            ctx["summary"] = content
        elif kind == "skills" and content:
            ctx["skills"] = content
        elif kind == "intent" and content:
            ctx["intent"] = content[:40]
        elif kind == "education" and content:
            period, body = _split_period(content)
            first = body.splitlines()[0][:48] if body else "教育背景"
            rest = "\n".join(body.splitlines()[1:]).strip()
            ctx["education"] = [
                {"school": first, "period": period, "degree": "", "major": rest[:160]}
            ]
        elif kind == "projects" and content:
            period, body = _split_period(content)
            lines_p = body.splitlines()
            pname = title if not _match_section_header(title) else (lines_p[0][:40] if lines_p else "项目经历")
            if _match_section_header(title):
                pname = lines_p[0][:40] if lines_p else "项目经历"
                desc = _normalize_body("\n".join(lines_p[1:]))
            else:
                desc = body
            # replace / append
            existing = [p for p in ctx.get("projects") or [] if p.get("name") != pname]
            existing.append({"name": pname, "period": period, "description": desc or body})
            ctx["projects"] = existing
        elif kind == "experience" and content:
            period, body = _split_period(content)
            lines_p = [x for x in body.splitlines() if x.strip()]
            if _match_section_header(title):
                company = lines_p[0][:40] if lines_p else "工作经历"
                title_role = lines_p[1][:40] if len(lines_p) > 1 and len(lines_p[1]) < 28 else ""
                desc = _normalize_body("\n".join(lines_p[2 if title_role else 1 :]))
            else:
                company = title[:40]
                title_role = ""
                desc = body
            existing = [e for e in ctx.get("experiences") or [] if e.get("company") != company]
            existing.append(
                {
                    "company": company,
                    "period": period,
                    "title": title_role,
                    "description": desc or body,
                }
            )
            ctx["experiences"] = existing
        elif content and len(content) < 400 and not kind:
            # short unclassified — prefer not polluting experiences
            if not ctx.get("summary"):
                ctx["summary"] = content[:220]
    return ctx


def sections_to_context(result: dict[str, Any]) -> dict[str, Any]:
    """Build template context from raw text + optimized sections (never dump raw wall)."""
    raw = result.get("raw_text") or ""
    sections = result.get("optimized_sections") or []

    base = parse_resume_text(raw)
    ctx = _apply_optimized_sections(base, sections)

    # Ensure minimum viable structure without wall-of-text fallback
    if not ctx.get("experiences") and not ctx.get("projects") and not ctx.get("education"):
        # Build from optimized sections individually instead of whole raw
        for sec in sections:
            title = (sec.get("title") or "").strip()
            content = _normalize_body(sec.get("content") or "")
            if not content or title.lower() in _SKIP_TITLES or title == "简历内容":
                continue
            if _looks_like_person_name(title) or _match_section_header(title):
                continue
            ctx.setdefault("experiences", []).append(
                {
                    "company": title[:40] or "经历",
                    "period": "",
                    "title": "",
                    "description": content[:500],
                }
            )
            if len(ctx["experiences"]) >= 3:
                break

    if not ctx.get("experiences") and not ctx.get("projects") and not ctx.get("education"):
        # Last resort: take first meaningful paragraph only, not whole resume
        paras = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
        paras = [p for p in paras if p.lower() not in _SKIP_TITLES and p not in ("个人简历", "RESUME")]
        snippet = _normalize_body(paras[1] if len(paras) > 1 else (paras[0] if paras else ""))[:400]
        ctx["experiences"] = [
            {
                "company": "相关经历",
                "period": "",
                "title": "",
                "description": snippet or "（请完善工作/项目经历）",
            }
        ]

    if not ctx.get("name"):
        ctx["name"] = "优化简历"
    ctx.setdefault("phone", "")
    ctx.setdefault("email", "")
    ctx.setdefault("summary", "")
    ctx.setdefault("intent", "")
    ctx.setdefault("skills", "")
    ctx.setdefault("photo_uri", "")
    ctx.setdefault("education", [])
    ctx.setdefault("experiences", [])
    ctx.setdefault("projects", [])
    return ctx


def render_optimized_html(result: dict[str, Any], template_id: str | None = None) -> dict[str, Any]:
    template_id = template_id or default_template_id() or DEFAULT_TEMPLATE_ID
    html_path = TEMPLATES_DIR / template_id / "template.html"
    if not html_path.exists():
        raise FileNotFoundError(f"模板不存在: {template_id}")
    context = sections_to_context(result)
    html = render_template_html(template_id, context)
    return {
        "ok": True,
        "html": html,
        "template_id": template_id,
        "name": context.get("name", ""),
        "context": context,
    }


def export_optimized(result: dict[str, Any], template_id: str | None = None) -> dict[str, Any]:
    template_id = template_id or default_template_id() or DEFAULT_TEMPLATE_ID
    html_path = TEMPLATES_DIR / template_id / "template.html"
    if not html_path.exists():
        raise FileNotFoundError(f"模板不存在: {template_id}")

    context = sections_to_context(result)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"optimized_{stamp}.pdf"
    export_resume_pdf(template_id, context, out_path)
    preview = render_pdf_preview(out_path)
    return {
        "ok": True,
        "pdf_path": str(out_path),
        "preview_url": preview["preview_url"],
        "template_id": template_id,
        "name": context.get("name", ""),
        "html": render_template_html(template_id, context),
    }
