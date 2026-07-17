"""Persist interview sessions under data/interviews/."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.utils.paths import INTERVIEWS_DIR, ensure_dirs

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


def _session_path(session_id: str) -> Path:
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_")
    if not safe:
        raise ValueError("无效的面试会话 id")
    return INTERVIEWS_DIR / f"{safe}.json"


def save_interview(session: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    session_id = str(session.get("id") or "").strip()
    if not session_id:
        return {"ok": False, "error": "缺少会话 id"}

    tech = session.get("tech_direction") or session.get("techDirection") or ""
    company = session.get("company_type") or session.get("companyType") or ""
    difficulty = session.get("difficulty") or "intermediate"
    messages = session.get("messages") or []
    resume_text = session.get("resume_text") or session.get("resumeText") or ""
    start_time = session.get("start_time") or session.get("startTime")
    ended_at = datetime.now().isoformat(timespec="seconds")

    title = (
        session.get("title")
        or f"{TECH_LABELS.get(tech, tech or '技术')}-{COMPANY_LABELS.get(company, company or '面试')}"
    )

    record = {
        "id": session_id,
        "title": title,
        "tech_direction": tech,
        "company_type": company,
        "difficulty": difficulty,
        "start_time": start_time,
        "ended_at": ended_at,
        "message_count": len(messages),
        "messages": messages,
        "resume_preview": (resume_text or "")[:500],
        "resume_text": resume_text or "",
        "resume_path": session.get("resume_path") or session.get("resumePath") or "",
    }

    path = _session_path(session_id)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "path": str(path), "id": session_id, "record": record}


def list_interviews(limit: int = 50) -> list[dict[str, Any]]:
    ensure_dirs()
    files = sorted(INTERVIEWS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    items: list[dict[str, Any]] = []
    for f in files[:limit]:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        ended = data.get("ended_at") or ""
        date_label = ended[:10] if ended else ""
        if not date_label and data.get("start_time"):
            try:
                ts = float(data["start_time"])
                date_label = datetime.fromtimestamp(ts / (1000 if ts > 1e12 else 1)).strftime("%m/%d")
            except Exception:
                date_label = ""
        items.append(
            {
                "id": data.get("id") or f.stem,
                "title": data.get("title") or f.stem,
                "techDirection": data.get("tech_direction") or "",
                "companyType": data.get("company_type") or "",
                "difficulty": data.get("difficulty") or "intermediate",
                "date": date_label,
                "messageCount": data.get("message_count") or len(data.get("messages") or []),
                "messages": data.get("messages") or [],
                "resumePath": data.get("resume_path") or "",
                "resumeText": data.get("resume_text") or "",
            }
        )
    return items


def load_interview(session_id: str) -> dict[str, Any]:
    ensure_dirs()
    path = _session_path(session_id)
    if not path.exists():
        return {"ok": False, "error": "记录不存在"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {"ok": True, "record": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}
