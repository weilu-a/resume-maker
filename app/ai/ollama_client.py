"""Ollama client with rule-based fallback for demos."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")


def _ollama_base() -> str:
    host = (os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").strip().rstrip("/")
    if not host.startswith("http"):
        host = "http://" + host
    return host

# Prefer smaller instruction-tuned Chinese models when auto-picking
_PREFERRED_PREFIXES = (
    "qwen2.5",
    "qwen2",
    "qwen",
    "deepseek",
    "llama3.2",
    "llama3.1",
    "llama3",
    "phi3",
    "gemma2",
    "mistral",
)


def _list_models() -> list[str]:
    r = requests.get(f"{_ollama_base()}/api/tags", timeout=5)
    r.raise_for_status()
    return [m.get("name", "") for m in r.json().get("models", []) if m.get("name")]


def _pick_model(requested: str, available: list[str]) -> str | None:
    if not available:
        return None
    # Exact / prefix match for requested
    for n in available:
        if n == requested or n.startswith(requested) or requested in n:
            return n
    req_base = requested.split(":")[0]
    for n in available:
        if n.startswith(req_base) or req_base in n:
            return n
    # Preferred family
    for prefix in _PREFERRED_PREFIXES:
        for n in available:
            if n.startswith(prefix):
                return n
    return available[0]


def check_health(model: str = DEFAULT_MODEL) -> dict[str, Any]:
    try:
        names = _list_models()
        picked = _pick_model(model, names)
        has_model = picked is not None
        return {
            "online": True,
            "has_model": has_model,
            "models": names,
            "model": picked or model,
            "requested_model": model,
            "message": (
                f"Ollama 就绪（{picked}）"
                if has_model
                else f"Ollama 在线，但没有可用模型。请执行: ollama pull {model}"
            ),
        }
    except Exception:
        return {
            "online": False,
            "has_model": False,
            "models": [],
            "model": model,
            "requested_model": model,
            "message": "Ollama 未启动。请安装并运行 Ollama，然后执行: ollama pull qwen2.5:3b",
        }


def _resolve_model(model: str = DEFAULT_MODEL) -> str | None:
    health = check_health(model)
    if not health["online"] or not health["has_model"]:
        return None
    return health.get("model") or model


def chat_messages(
    messages: list[dict[str, str]],
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    format_json: bool = False,
    timeout: int = 180,
) -> dict[str, Any]:
    """Low-level Ollama chat. Returns {ok, content, model} or {ok:False, error}."""
    resolved = _resolve_model(model)
    if not resolved:
        return {"ok": False, "error": "Ollama 未就绪或没有可用模型"}
    payload: dict[str, Any] = {
        "model": resolved,
        "stream": False,
        "messages": messages,
        "options": {"temperature": temperature},
    }
    if format_json:
        payload["format"] = "json"
    try:
        r = requests.post(f"{_ollama_base()}/api/chat", json=payload, timeout=timeout)
        r.raise_for_status()
        content = (r.json().get("message") or {}).get("content") or ""
        return {"ok": True, "content": content, "model": resolved}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _chat(prompt: str, system: str, model: str = DEFAULT_MODEL) -> tuple[str | None, str]:
    """Return (content, provider). provider: ollama | deepseek | none."""
    from app.ai.llm_router import chat_text_prefer_ollama

    result = chat_text_prefer_ollama(
        prompt,
        system=system,
        temperature=0.3,
        format_json=True,
        timeout=180,
    )
    if not result.get("ok"):
        return None, "none"
    return (result.get("content") or None), (result.get("provider") or "none")


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _polish_text_rule(text: str) -> str:
    if not text or not text.strip():
        return text
    t = text.strip()
    replacements = [
        ("负责开发", "主导开发"),
        ("负责", "主导"),
        ("参与了", "深度参与"),
        ("修复了很多", "系统性修复多项"),
        ("很多 Bug", "关键缺陷"),
        ("性格开朗，工作负责", "具备良好的协作沟通与主人翁意识"),
        ("学习能力强", "具备快速学习与独立攻坚能力"),
        ("能吃苦耐劳", "抗压能力强，注重交付质量"),
    ]
    for a, b in replacements:
        t = t.replace(a, b)
    if "提升" not in t and "降低" not in t and len(t) > 20:
        t = t.rstrip("。") + "，持续关注质量与交付效率。"
    return t


def polish_resume_data(data: dict[str, Any], model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Polish experience descriptions in resume form data."""
    system = (
        "你是资深中文简历润色助手。保持事实不变，强化动词与结果导向表述。"
        "只输出 JSON，格式："
        '{"summary":"...","experiences":[{"description":"..."}],"projects":[{"description":"..."}]}'
    )
    prompt = json.dumps(
        {
            "name": data.get("name"),
            "summary": data.get("summary", ""),
            "experiences": [
                {"company": e.get("company"), "title": e.get("title"), "description": e.get("description", "")}
                for e in data.get("experiences", [])
            ],
            "projects": [
                {"name": p.get("name"), "description": p.get("description", "")}
                for p in data.get("projects", [])
            ],
        },
        ensure_ascii=False,
    )
    raw, provider = _chat(prompt, system, model)
    parsed = _extract_json(raw) if raw else None
    result = dict(data)
    result["ai_source"] = provider if parsed else "fallback"

    if parsed:
        if parsed.get("summary"):
            result["summary"] = parsed["summary"]
        exps = parsed.get("experiences") or []
        for i, exp in enumerate(result.get("experiences", [])):
            if i < len(exps) and exps[i].get("description"):
                exp["description"] = exps[i]["description"]
        projs = parsed.get("projects") or []
        for i, proj in enumerate(result.get("projects", [])):
            if i < len(projs) and projs[i].get("description"):
                proj["description"] = projs[i]["description"]
        return result

    result["summary"] = _polish_text_rule(result.get("summary", "") or "具备扎实专业能力，追求高质量交付。")
    for exp in result.get("experiences", []):
        exp["description"] = _polish_text_rule(exp.get("description", ""))
    for proj in result.get("projects", []):
        proj["description"] = _polish_text_rule(proj.get("description", ""))
    return result


def optimize_resume_text(raw_text: str, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Optimize extracted PDF resume text into structured comparison result."""
    system = (
        "你是中文简历优化专家。根据原文输出 JSON，字段必须齐全："
        "{"
        '"score":90,"skill_match":90,"experience_density":85,"keywords":90,"score_up":12,'
        '"original_sections":[{"title":"教育背景","content":"..."}],'
        '"optimized_sections":[{"title":"教育背景","content":"..."}],'
        '"suggestions":[{"type":"动词强化","icon":"check","text":"..."}]'
        "}"
        "optimized_sections 的 title 必须使用这些标准标题之一："
        "基本信息、教育背景、工作经历、实习经历、项目经历、校园经历、专业技能、自我评价、求职意向。"
        "content 用换行分段，不要把整份简历塞进某一个 content。"
        "不要在 content 里写英文栏目标题（如 Personal information / Educational background / Work experience / Skills）。"
        "不要把 Skills、Resume 等英文词当作姓名。"
        "保留事实，强化动词、量化成果与行业关键词。"
    )
    prompt = f"请优化以下简历文本：\n\n{raw_text[:6000]}"
    raw, provider = _chat(prompt, system, model)
    parsed = _extract_json(raw) if raw else None
    if parsed and parsed.get("optimized_sections"):
        parsed["ai_source"] = provider
        return parsed
    return _fallback_optimize(raw_text)


def _fallback_optimize(raw_text: str) -> dict[str, Any]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", raw_text) if p.strip()]
    if not paragraphs:
        paragraphs = [raw_text.strip() or "（未能从 PDF 提取到有效文字）"]

    skip_heads = {
        "personal resume",
        "resume",
        "个人简历",
        "简历",
        "curriculum vitae",
        "cv",
    }
    section_keys = (
        ("教育", "教育背景"),
        ("实习", "实习经历"),
        ("工作", "工作经历"),
        ("项目", "项目经历"),
        ("校园", "校园经历"),
        ("技能", "专业技能"),
        ("证书", "持有证书"),
        ("评价", "自我评价"),
        ("概述", "个人概述"),
        ("荣誉", "所获荣誉"),
        ("基本信息", "基本信息"),
    )

    original_sections = []
    optimized_sections = []
    for i, p in enumerate(paragraphs[:8]):
        lines = [ln.strip() for ln in p.splitlines() if ln.strip()]
        title = lines[0][:40] if lines else f"段落 {i + 1}"
        if title.strip().lower() in skip_heads:
            title = lines[1][:40] if len(lines) > 1 else title
            content = "\n".join(lines[2:] if len(lines) > 2 else lines[1:]).strip() or p
        else:
            content = "\n".join(lines[1:]).strip() if len(lines) > 1 else p

        for key, label in section_keys:
            if key in title or key in (lines[0] if lines else ""):
                title = label
                break

        original_sections.append({"title": title, "content": content})
        optimized_sections.append({"title": title, "content": _polish_text_rule(content)})

    return {
        "ai_source": "fallback",
        "score": 88,
        "skill_match": 90,
        "experience_density": 84,
        "keywords": 86,
        "score_up": 10,
        "original_sections": original_sections,
        "optimized_sections": optimized_sections,
        "suggestions": [
            {
                "type": "动词强化",
                "icon": "check",
                "text": "建议将笼统的「负责/参与」改为「主导/推动」，突出主动性。",
            },
            {
                "type": "数据量化",
                "icon": "info",
                "text": "尽量补充可量化结果，如性能提升、覆盖率、用户量等。",
            },
            {
                "type": "专业词汇",
                "icon": "star",
                "text": "补充行业关键词，便于通过 ATS 与招聘关键词筛选。",
            },
        ],
    }
