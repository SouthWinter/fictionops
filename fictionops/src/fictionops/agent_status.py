from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .agent_issue_ledger import load_issue_ledger


STATUS_SCHEMA = "fictionops.agent_project_status.v1"


def _object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def build_agent_project_status(path: Path, *, latest: int = 12) -> dict[str, Any]:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"agent status requires a project directory: {root}")
    sessions: list[dict[str, Any]] = []
    usage: Counter[str] = Counter()
    costs: Counter[str] = Counter()
    for session_file in root.rglob("session.json"):
        if "agent_runs" not in session_file.parts:
            continue
        session = _object(session_file)
        if not session.get("session_id"):
            continue
        run_dir = session_file.parent
        checkpoint = _object(run_dir / "checkpoint.json")
        budget = _object(run_dir / "model_budget.json")
        cumulative_usage = budget.get("cumulative_usage") if isinstance(budget.get("cumulative_usage"), dict) else {}
        cumulative_cost = budget.get("cumulative_cost_by_currency") if isinstance(budget.get("cumulative_cost_by_currency"), dict) else {}
        for key, value in cumulative_usage.items():
            if isinstance(value, int) and not isinstance(value, bool):
                usage[str(key)] += value
        for key, value in cumulative_cost.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                costs[str(key)] += float(value)
        state = str(session.get("state") or checkpoint.get("phase") or "unknown")
        sessions.append(
            {
                "session_id": session.get("session_id"),
                "workflow": session.get("workflow"),
                "state": state,
                "run_dir": str(run_dir),
                "source_file": session.get("source_file"),
                "updated_at": session.get("updated_at") or checkpoint.get("updated_at"),
                "resumable": bool(checkpoint.get("resumable")) and state not in {"applied", "cancelled", "ready_for_approval"},
                "ready_for_approval": bool(session.get("ready_for_approval")) or state == "ready_for_approval",
                "model_calls": int(budget.get("cumulative_used_calls") or budget.get("used_calls") or 0),
            }
        )
    sessions.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    issue_payload = load_issue_ledger(root)
    issues = [item for item in issue_payload.get("issues") or [] if isinstance(item, dict)]
    state_counts = Counter(str(item["state"]) for item in sessions)
    issue_counts = Counter(str(item.get("status") or "unknown") for item in issues)
    return {
        "schema": STATUS_SCHEMA,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "project": str(root),
        "session_count": len(sessions),
        "state_counts": dict(sorted(state_counts.items())),
        "author_actions": {
            "ready_for_approval": sum(bool(item["ready_for_approval"]) for item in sessions),
            "needs_revision_attention": state_counts.get("needs_revision_attention", 0),
            "resumable": sum(bool(item["resumable"]) for item in sessions),
        },
        "issue_count": len(issues),
        "issue_status_counts": dict(sorted(issue_counts.items())),
        "cumulative_usage": dict(sorted(usage.items())),
        "cumulative_cost_by_currency": {key: round(value, 12) for key, value in sorted(costs.items())},
        "latest_sessions": sessions[: max(0, latest)],
    }


def render_agent_project_status(payload: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if output_format != "markdown":
        raise ValueError(f"unsupported agent status format: {output_format}")
    actions = payload["author_actions"]
    lines = [
        "# FictionOps Agent Project Status",
        "",
        f"- Sessions: {payload['session_count']}",
        f"- Ready for approval: {actions['ready_for_approval']}",
        f"- Needs revision attention: {actions['needs_revision_attention']}",
        f"- Resumable: {actions['resumable']}",
        f"- Persistent issues: {payload['issue_count']}",
        f"- Usage: `{json.dumps(payload['cumulative_usage'], ensure_ascii=False)}`",
        f"- Cost: `{json.dumps(payload['cumulative_cost_by_currency'], ensure_ascii=False)}`",
        "",
        "| State | Workflow | Calls | Run |",
        "| --- | --- | ---: | --- |",
    ]
    for item in payload["latest_sessions"]:
        lines.append(f"| `{item['state']}` | `{item.get('workflow') or '-'}` | {item['model_calls']} | `{item['run_dir']}` |")
    return "\n".join(lines).rstrip() + "\n"
