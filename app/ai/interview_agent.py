"""Interview agent: prefab openings + AI follow-up (Ollama, else DeepSeek)."""

from __future__ import annotations

import json
import re
from typing import Any

COMPANY_LABELS = {
    "bigtech": "互联网大厂",
    "multinational": "跨国名企",
    "soe": "国企/事业单位",
    "startup": "成长型创业公司",
}

TECH_LABELS = {
    "frontend": "前端开发",
    "backend": "后端开发",
    "client": "客户端开发",
}

DIFFICULTY_LABELS = {
    "junior": "初级",
    "intermediate": "中级",
    "senior": "高级",
}

COMPANY_PERSONA = {
    "bigtech": "高效直接、关注指标与落地、节奏偏快",
    "multinational": "国际化、职业化、注重沟通清晰与结构化表达",
    "soe": "正式礼貌、稳健务实、强调责任与规范",
    "startup": "务实热情、关注解决问题与成长性",
}

OPENING_BY_COMPANY = {
    "bigtech": (
        "你好，我是本场技术面试官。时间有限，我们直奔主题。"
        "请先做一个简洁的自我介绍，重点说说你的背景、核心能力和最近一段经历。"
    ),
    "multinational": (
        "Hello，欢迎参加今天的面试。我是本场的技术面试官。"
        "请先做一个结构化的自我介绍，简要说明你的教育/工作背景、擅长方向，以及一次你觉得最有代表性的经历。"
    ),
    "soe": (
        "您好，欢迎参加本次面试。我是面试官。"
        "请先做一下自我介绍，介绍您的基本情况、专业方向，以及与本次岗位相关的主要经历。"
    ),
    "startup": (
        "嗨，欢迎来面试！我是今天的技术面试官。"
        "先轻松做个自我介绍吧：你是谁、做过什么、最近最想解决什么问题，都可以聊聊。"
    ),
}

RESUME_MAX_CHARS = 6000


def get_opening(company_type: str) -> dict[str, Any]:
    key = company_type if company_type in OPENING_BY_COMPANY else "bigtech"
    return {
        "ok": True,
        "company_type": key,
        "speech": OPENING_BY_COMPANY[key],
    }


def _truncate_resume(resume_text: str) -> str:
    text = (resume_text or "").strip()
    if not text:
        return "（候选人未提供简历文本）"
    if len(text) <= RESUME_MAX_CHARS:
        return text
    return text[:RESUME_MAX_CHARS] + "\n…（简历已截断）"


def build_system_prompt(
    company_type: str,
    tech_direction: str,
    difficulty: str,
    resume_text: str,
) -> str:
    company = COMPANY_LABELS.get(company_type, company_type or "互联网大厂")
    tech = TECH_LABELS.get(tech_direction, tech_direction or "技术")
    level = DIFFICULTY_LABELS.get(difficulty, difficulty or "中级")
    persona = COMPANY_PERSONA.get(company_type, COMPANY_PERSONA["bigtech"])
    resume = _truncate_resume(resume_text)

    return (
        f"你是{company}的{tech}面试官，本场难度为「{level}」。"
        f"说话风格应符合该类企业画像：{persona}。\n"
        "开场白已由系统发出并请候选人自我介绍；你从候选人的回复开始继续面试。\n"
        "\n"
        "【候选人简历】\n"
        f"{resume}\n"
        "\n"
        "【任务】\n"
        "- 围绕简历与岗位方向追问，一次只聚焦一个问题点。\n"
        "- 根据难度控制深度：初级重基础与表达；中级重项目与取舍；高级重架构、权衡与影响力。\n"
        "- 结合对话历史推进，避免重复已问过的问题。\n"
        "- 正常进行约 5–10 轮有效追问后再结束；若候选人明显无法继续或你已获得充分信息，可提前结束。\n"
        "- 结束时 speech 应礼貌收尾，并可有一句简短总评语气（不必打分）。\n"
        "\n"
        "【输出格式｜强制】\n"
        "只输出一个 JSON 对象，不要 Markdown，不要多余说明。格式严格为：\n"
        '{"speech":"你对候选人说的下一句话","end_interview":false}\n'
        "字段说明：\n"
        "- speech: string，面试官要对候选人说的话\n"
        "- end_interview: boolean，true 表示本场面试到此结束\n"
    )


def _history_for_prompt(messages: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for m in messages:
        role = m.get("role") or "user"
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if role in ("ai", "assistant"):
            label = "面试官"
        else:
            label = "候选人"
        lines.append(f"{label}: {content}")
    return "\n".join(lines) if lines else "（暂无历史）"


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _normalize_reply(parsed: dict[str, Any] | None, raw: str) -> dict[str, Any]:
    if not parsed:
        speech = (raw or "").strip() or "谢谢你的回答。能再具体讲讲你在其中承担的职责和结果吗？"
        return {"ok": True, "speech": speech, "end_interview": False, "fallback": True}

    speech = parsed.get("speech")
    if speech is None:
        speech = parsed.get("content") or parsed.get("message") or ""
    speech = str(speech).strip()
    if not speech:
        speech = "谢谢分享。方便展开讲一下当时的关键实现或决策吗？"

    end_flag = parsed.get("end_interview")
    if end_flag is None:
        end_flag = parsed.get("end") or parsed.get("should_end") or False
    if isinstance(end_flag, str):
        end_flag = end_flag.strip().lower() in ("1", "true", "yes", "y")
    else:
        end_flag = bool(end_flag)

    return {"ok": True, "speech": speech, "end_interview": end_flag, "fallback": False}


def _call_llm(system: str, user_block: str) -> dict[str, Any]:
    """Prefer local Ollama; if unavailable, use DeepSeek cloud."""
    from app.ai.llm_router import chat_prefer_ollama

    return chat_prefer_ollama(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user_block},
        ],
        temperature=0.7,
        format_json=True,
        timeout=180,
    )


def reply(
    messages: list[dict[str, Any]],
    *,
    company_type: str,
    tech_direction: str,
    difficulty: str,
    resume_text: str,
) -> dict[str, Any]:
    """Generate interviewer follow-up from history via DeepSeek or Ollama."""
    system = build_system_prompt(company_type, tech_direction, difficulty, resume_text)
    history = _history_for_prompt(messages)
    user_block = (
        "以下是截至目前的面试对话历史，请基于此继续下一轮提问或结束面试。\n"
        "【对话历史】\n"
        f"{history}\n"
        "\n"
        "请严格按 JSON 格式输出。"
    )

    result = _call_llm(system, user_block)
    if not result.get("ok"):
        return {
            "ok": False,
            "error": result.get("error") or "AI 调用失败",
            "speech": "",
            "end_interview": False,
        }

    raw = result.get("content") or ""
    parsed = _extract_json(raw)
    out = _normalize_reply(parsed, raw)
    out["model"] = result.get("model")
    out["provider"] = result.get("provider") or ""
    return out
