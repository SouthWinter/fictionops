from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .markdown import safe_cell
from .models import DogfoodCycleIssue, DogfoodCycleReport


DECISIONS = {"accepted", "deferred", "failed"}
READY_STATUSES = {"ready", "ready_for_project_work", "complete", "completed"}
MIN_DOGFOOD_CALENDAR_DAYS = 7
RECOGNIZED_FICTIONOPS_COMMANDS = {
    "adopt",
    "adopt-review",
    "adopt-plan",
    "import-plan",
    "init",
    "new-book",
    "new-chapter",
    "plan-chapter",
    "scene-plan",
    "draft-brief",
    "post-draft",
    "review-gate",
    "book-gate",
    "audit-plan",
    "retrospective",
    "stats",
    "scan-words",
    "check-tables",
    "audit-wave",
    "audit-style",
    "audit-continuity",
    "audit-echoes",
    "audit-info",
    "audit-characters",
    "agent-prompt",
    "agent-connect",
    "eval-agent",
    "agent-smoke",
    "agent-run",
    "agent-exec",
    "agent-inbox",
    "write-chapter",
    "revise-chapter",
    "audit-chapter",
    "agent-session",
    "agent-next",
    "audit-agent-workflow",
    "setup-ai",
    "model-config",
    "context-pack",
    "workflow-plan",
    "revision-plan",
    "doctor",
    "report",
    "export-clean",
    "audit-publish",
    "publish-copy",
    "export-metadata",
    "export-manifest",
    "export-epub",
    "audit-epub",
    "release-gate",
    "audit-release-evidence",
    "audit-dogfood-cycle",
    "audit-stability-window",
    "audit-stable-core",
}
REQUIRED_FIELDS = [
    "Cycle ID",
    "Project / sandbox",
    "Start date",
    "End date",
    "Version / commit range",
    "Scope",
    "Book / chapter scope",
    "Focused tasks",
    "Commands exercised",
    "AI workflow evidence",
    "Human review boundary",
    "Day-by-day ledger",
    "Initial adopt-review status",
    "Final adopt-review status",
    "import_queue_files",
    "blocking_issue_count",
    "Waiver count",
    "Compatibility notes",
    "Recovery notes",
    "Decision",
    "Reviewer",
]
PLACEHOLDER_VALUES = {"", "accepted / deferred / failed", "yes / no", "TBD", "todo", "-"}


def default_dogfood_cycle_path(target: Path) -> Path:
    if target.is_file():
        return target.resolve()
    return (target / "docs" / "dogfood-cycle-evidence.md").resolve()


def normalize_field_name(raw: str) -> str:
    key = raw.strip().replace("`", "").strip()
    key = re.sub(r"\s+", " ", key)
    aliases = {
        "Project": "Project / sandbox",
        "Sandbox": "Project / sandbox",
        "Version": "Version / commit range",
        "Commit range": "Version / commit range",
        "Initial status": "Initial adopt-review status",
        "Final status": "Final adopt-review status",
        "Waivers": "Waiver count",
    }
    return aliases.get(key, key)


def parse_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^\s*[-*]\s+(.+?):\s*(.*)\s*$", line)
        if not match:
            continue
        fields[normalize_field_name(match.group(1))] = match.group(2).strip()
    return fields


def is_placeholder(value: str) -> bool:
    cleaned = value.strip()
    return cleaned in PLACEHOLDER_VALUES


def issue(severity: str, code: str, field: str, message: str) -> DogfoodCycleIssue:
    return DogfoodCycleIssue(severity=severity, code=code, field=field, message=message)


def parse_int(value: str) -> int | None:
    try:
        return int(value.strip())
    except ValueError:
        return None


def parse_date(value: str) -> date | None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def command_count(value: str) -> int:
    normalized = value.replace("\uff0c", ",").replace("\u3001", ",").replace("\uff1b", ";")
    parts = [part.strip() for part in re.split(r"[,;]", normalized) if part.strip()]
    return len(parts)


def command_names(value: str) -> list[str]:
    normalized = value.replace("\uff0c", ",").replace("\u3001", ",").replace("\uff1b", ";")
    names: list[str] = []
    for part in (part.strip().strip("`") for part in re.split(r"[,;]", normalized)):
        if not part:
            continue
        tokens = [token.strip("`$") for token in part.split()]
        if not tokens:
            continue
        if len(tokens) >= 3 and tokens[0] == "python" and tokens[1] == "-m" and tokens[2] == "fictionops":
            tokens = tokens[3:]
        elif tokens[0] == "fictionops":
            tokens = tokens[1:]
        if tokens:
            names.append(tokens[0])
    return names


def recognized_command_count(value: str) -> int:
    return len({name for name in command_names(value) if name in RECOGNIZED_FICTIONOPS_COMMANDS})


def has_book_or_project_scope(value: str) -> bool:
    lowered = value.lower()
    return bool(
        re.search(r"\bbook[_ -]?\d+\b", lowered)
        or re.search(r"\bbook\s+\d+\b", lowered)
        or any(token in value for token in ("第一本", "第二本", "第三本", "全书", "卷", "本"))
    )


def has_chapter_scope(value: str) -> bool:
    lowered = value.lower()
    return bool(
        re.search(r"\bch[_ -]?\d+", lowered)
        or "chapter" in lowered
        or any(token in value for token in ("章节", "章", "全章", "全部"))
    )


def has_ai_workflow_evidence(value: str) -> bool:
    lowered = value.lower()
    if any(token in lowered for token in ("none", "no ai", "without ai", "not used")):
        return False
    return any(
        token in lowered
        for token in (
            "agent",
            "runner",
            "controller",
            "eval-agent",
            "agent-run",
            "agent-exec",
            "agent-inbox",
            "model",
            "api",
            "ai",
        )
    )


def has_human_review_boundary(value: str) -> bool:
    lowered = value.lower()
    return any(
        token in lowered
        for token in (
            "review",
            "human",
            "staged",
            "inbox",
            "gate",
            "no source overwrite",
            "manual",
            "复核",
            "人工",
            "暂存",
            "收件箱",
            "门禁",
            "不覆盖",
        )
    )


def ledger_entry_count(value: str) -> int:
    iso_dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", value)
    day_labels = re.findall(r"\bday\s*\d+\b", value, flags=re.IGNORECASE)
    chinese_days = re.findall(r"第\s*[一二三四五六七八九十\d]+\s*天", value)
    return max(len(iso_dates), len(day_labels) + len(chinese_days))


def build_dogfood_cycle_audit(target: Path, *, file_path: str | None = None) -> DogfoodCycleReport:
    resolved = target.expanduser().resolve()
    evidence_file = Path(file_path).expanduser() if file_path else default_dogfood_cycle_path(resolved)
    if file_path and not evidence_file.is_absolute():
        evidence_file = (resolved / evidence_file).resolve()
    issues: list[DogfoodCycleIssue] = []

    if not evidence_file.exists():
        issues.append(
            issue(
                "P1",
                "missing_dogfood_cycle_evidence",
                "evidence_file",
                f"Dogfood cycle evidence file was not found: {evidence_file}",
            )
        )
        return DogfoodCycleReport(
            target=str(resolved),
            evidence_file=str(evidence_file),
            evidence_file_exists=False,
            status="missing",
            ready=False,
            decision="",
            field_count=0,
            missing_required_fields=REQUIRED_FIELDS.copy(),
            issue_count=len(issues),
            blocking_issue_count=len(issues),
            issues=issues,
            next_actions=["Create a filled dogfood cycle evidence record, then rerun audit-dogfood-cycle."],
        )
    if not evidence_file.is_file():
        raise IsADirectoryError(f"dogfood cycle evidence path is not a file: {evidence_file}")

    fields = parse_fields(evidence_file.read_text(encoding="utf-8"))
    missing_required: list[str] = []
    for field in REQUIRED_FIELDS:
        value = fields.get(field, "")
        if is_placeholder(value):
            missing_required.append(field)
            issues.append(
                issue(
                    "P2",
                    "missing_required_evidence",
                    field,
                    f"Required dogfood cycle field is empty or still a placeholder: {field}",
                )
            )

    decision = fields.get("Decision", "").strip().lower()
    if decision not in DECISIONS:
        issues.append(
            issue("P1", "invalid_decision", "Decision", "Decision must be one of accepted, deferred, or failed.")
        )
    elif decision != "accepted":
        issues.append(
            issue(
                "P2",
                f"decision_{decision}",
                "Decision",
                f"Dogfood cycle decision is {decision}, so it does not close the sustained-cycle requirement.",
            )
        )

    final_status = fields.get("Final adopt-review status", "").strip().lower()
    if final_status and final_status not in READY_STATUSES:
        issues.append(
            issue(
                "P2",
                "final_status_not_ready",
                "Final adopt-review status",
                "Final adopt-review status must show ready/ready_for_project_work/complete for 1.0 dogfood proof.",
            )
        )

    parsed_dates: dict[str, date] = {}
    for field in ("Start date", "End date"):
        value = fields.get(field, "")
        if value and not is_placeholder(value):
            parsed = parse_date(value)
            if parsed is None:
                issues.append(issue("P2", "invalid_date", field, f"{field} should use YYYY-MM-DD."))
            else:
                parsed_dates[field] = parsed
    if "Start date" in parsed_dates and "End date" in parsed_dates and parsed_dates["End date"] < parsed_dates["Start date"]:
        issues.append(
            issue(
                "P2",
                "date_range_reversed",
                "End date",
                "End date must be the same as or later than Start date for dogfood cycle evidence.",
            )
        )
    elif "Start date" in parsed_dates and "End date" in parsed_dates:
        calendar_days = (parsed_dates["End date"] - parsed_dates["Start date"]).days + 1
        if calendar_days < MIN_DOGFOOD_CALENDAR_DAYS:
            issues.append(
                issue(
                    "P2",
                    "dogfood_cycle_too_short",
                    "End date",
                    f"A sustained dogfood cycle must cover at least {MIN_DOGFOOD_CALENDAR_DAYS} calendar days.",
                )
            )

    for field in ("import_queue_files", "blocking_issue_count", "Waiver count"):
        value = fields.get(field, "")
        if value and not is_placeholder(value):
            number = parse_int(value)
            if number is None or number < 0:
                issues.append(issue("P1", "invalid_integer", field, f"{field} must be a non-negative integer."))
            elif field in {"import_queue_files", "blocking_issue_count"} and number != 0:
                issues.append(issue("P2", f"{field}_not_zero", field, f"{field} must be 0 for accepted 1.0 dogfood proof."))

    commands = fields.get("Commands exercised", "")
    if commands and not is_placeholder(commands) and command_count(commands) < 3:
        issues.append(
            issue(
                "P2",
                "thin_command_coverage",
                "Commands exercised",
                "A sustained dogfood cycle must exercise at least three command paths before it can be accepted.",
            )
        )
    elif commands and not is_placeholder(commands) and recognized_command_count(commands) < 3:
        issues.append(
            issue(
                "P2",
                "unrecognized_command_coverage",
                "Commands exercised",
                "Commands exercised must include at least three recognized FictionOps CLI command paths.",
            )
        )

    book_scope = fields.get("Book / chapter scope", "")
    if book_scope and not is_placeholder(book_scope):
        if not has_book_or_project_scope(book_scope) or not has_chapter_scope(book_scope):
            issues.append(
                issue(
                    "P2",
                    "missing_book_chapter_scope",
                    "Book / chapter scope",
                    "Accepted dogfood evidence must name the real book/project slice and chapter range or target chapters.",
                )
            )

    focused_tasks = fields.get("Focused tasks", "")
    if focused_tasks and not is_placeholder(focused_tasks) and len(focused_tasks.strip()) < 20:
        issues.append(
            issue(
                "P2",
                "thin_focused_tasks",
                "Focused tasks",
                "Focused tasks should summarize the real maintenance or writing work, not just say smoke/test.",
            )
        )

    ai_evidence = fields.get("AI workflow evidence", "")
    if ai_evidence and not is_placeholder(ai_evidence) and decision == "accepted" and not has_ai_workflow_evidence(ai_evidence):
        issues.append(
            issue(
                "P2",
                "missing_ai_workflow_evidence",
                "AI workflow evidence",
                "Accepted dogfood evidence must describe the agent/API runner, controller, or eval-agent path used.",
            )
        )

    review_boundary = fields.get("Human review boundary", "")
    if review_boundary and not is_placeholder(review_boundary) and decision == "accepted" and not has_human_review_boundary(review_boundary):
        issues.append(
            issue(
                "P2",
                "missing_human_review_boundary",
                "Human review boundary",
                "Accepted dogfood evidence must state how staged model or tool output stopped for human review.",
            )
        )

    ledger = fields.get("Day-by-day ledger", "")
    if ledger and not is_placeholder(ledger) and decision == "accepted" and ledger_entry_count(ledger) < 2:
        issues.append(
            issue(
                "P2",
                "thin_day_by_day_ledger",
                "Day-by-day ledger",
                "Accepted sustained evidence needs at least a start and close ledger entry, not only a date range.",
            )
        )

    blocking_count = sum(1 for item in issues if item.severity in {"P0", "P1", "P2"})
    if blocking_count:
        status = "incomplete"
        ready = False
        next_actions = ["Fill missing dogfood cycle fields and rerun audit-dogfood-cycle."]
    elif decision == "accepted":
        status = "accepted"
        ready = True
        next_actions = ["Link this dogfood cycle from stable-core-audit, milestone status, and release notes."]
    elif decision == "failed":
        status = "failed"
        ready = False
        next_actions = ["Fix the dogfood regression, add tests or docs, and record a new cycle."]
    elif decision == "deferred":
        status = "deferred"
        ready = False
        next_actions = ["Finish the sustained dogfood cycle and update the evidence decision."]
    else:
        status = "incomplete"
        ready = False
        next_actions = ["Fill missing dogfood cycle fields and rerun audit-dogfood-cycle."]

    return DogfoodCycleReport(
        target=str(resolved),
        evidence_file=str(evidence_file),
        evidence_file_exists=True,
        status=status,
        ready=ready,
        decision=decision,
        field_count=len(fields),
        missing_required_fields=missing_required,
        issue_count=len(issues),
        blocking_issue_count=blocking_count,
        issues=issues,
        next_actions=next_actions,
    )


def format_dogfood_cycle_audit(report: DogfoodCycleReport) -> str:
    lines = [
        "# FictionOps Dogfood Cycle Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Evidence file: `{report.evidence_file}`",
        f"- Status: `{report.status}`",
        f"- Ready: {'yes' if report.ready else 'no'}",
        f"- Decision: `{report.decision or '-'}`",
        f"- Parsed fields: {report.field_count}",
        f"- Missing required fields: {len(report.missing_required_fields)}",
        f"- Issues: {report.issue_count}",
        f"- Blocking issues: {report.blocking_issue_count}",
        "",
        "## Issues",
        "",
    ]
    if report.issues:
        lines.extend(["| Severity | Code | Field | Message |", "| --- | --- | --- | --- |"])
        for item in report.issues:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(item.severity),
                        f"`{safe_cell(item.code)}`",
                        safe_cell(item.field),
                        safe_cell(item.message),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No dogfood cycle issues found.")
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def render_dogfood_cycle_audit(report: DogfoodCycleReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_dogfood_cycle_audit(report)
