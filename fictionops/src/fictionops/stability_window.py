from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from .dogfood_cycle import build_dogfood_cycle_audit
from .markdown import safe_cell
from .models import StabilityWindowIssue, StabilityWindowReport
from .release_evidence import build_release_evidence_audit


DECISIONS = {"accepted", "deferred", "failed"}
MIN_STABILITY_WINDOW_CALENDAR_DAYS = 7
REQUIRED_FIELDS = [
    "Window ID",
    "Start date",
    "End date",
    "Version range",
    "Release evidence reference",
    "Dogfood cycle reference",
    "Compatibility notes",
    "Breaking changes",
    "Recovery notes",
    "Decision",
    "Reviewer",
]
PLACEHOLDER_VALUES = {"", "-", "TBD", "todo", "accepted / deferred / failed"}


def default_stability_window_path(target: Path) -> Path:
    if target.is_file():
        return target.resolve()
    return (target / "docs" / "stability-window-evidence.md").resolve()


def normalize_field_name(raw: str) -> str:
    key = raw.strip().replace("`", "").strip()
    key = re.sub(r"\s+", " ", key)
    aliases = {
        "Window": "Window ID",
        "Cycle ID": "Window ID",
        "Version": "Version range",
        "Release reference": "Release evidence reference",
        "Dogfood reference": "Dogfood cycle reference",
        "Compatibility": "Compatibility notes",
        "Breaking-change notes": "Breaking changes",
        "Recovery": "Recovery notes",
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
    return value.strip() in PLACEHOLDER_VALUES


def issue(severity: str, code: str, field: str, message: str) -> StabilityWindowIssue:
    return StabilityWindowIssue(severity=severity, code=code, field=field, message=message)


def parse_date(value: str) -> date | None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def looks_like_local_markdown_reference(value: str) -> bool:
    cleaned = value.strip().strip("`")
    lowered = cleaned.lower()
    return lowered.endswith(".md") or cleaned.startswith("docs/") or cleaned.startswith("docs\\")


def looks_like_url_reference(value: str) -> bool:
    cleaned = value.strip().strip("`")
    return bool(re.search(r"(?i)\bhttps?://", cleaned)) or cleaned.lower() in {"http", "https"}


def valid_url_reference(value: str) -> bool:
    cleaned = value.strip().strip("`")
    parsed = urlparse(cleaned)
    return parsed.scheme == "https" and bool(parsed.netloc)


def concrete_url_reference(value: str) -> bool:
    cleaned = value.strip().strip("`").lower()
    return any(
        marker in cleaned
        for marker in (
            "/actions/runs/",
            "artifact",
            "release",
            "dogfood",
            "evidence",
            "stability",
        )
    )


def resolve_local_reference(root: Path, value: str) -> Path:
    cleaned = value.strip().strip("`")
    path = Path(cleaned).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def build_stability_window_audit(target: Path, *, file_path: str | None = None) -> StabilityWindowReport:
    resolved = target.expanduser().resolve()
    evidence_file = Path(file_path).expanduser() if file_path else default_stability_window_path(resolved)
    if file_path and not evidence_file.is_absolute():
        evidence_file = (resolved / evidence_file).resolve()
    issues: list[StabilityWindowIssue] = []

    if not evidence_file.exists():
        issues.append(
            issue(
                "P2",
                "missing_stability_window_evidence",
                "evidence_file",
                f"Stability window evidence file was not found: {evidence_file}",
            )
        )
        return StabilityWindowReport(
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
            next_actions=["Create a filled stability window evidence record after a real compatibility window."],
        )
    if not evidence_file.is_file():
        raise IsADirectoryError(f"stability window evidence path is not a file: {evidence_file}")

    fields = parse_fields(evidence_file.read_text(encoding="utf-8"))
    missing_required: list[str] = []
    for field in REQUIRED_FIELDS:
        value = fields.get(field, "")
        if is_placeholder(value):
            missing_required.append(field)
            issues.append(
                issue(
                    "P2",
                    "missing_stability_window_field",
                    field,
                    f"Stability window evidence field is empty or still a placeholder: {field}",
                )
            )

    decision = fields.get("Decision", "").strip().lower()
    if decision not in DECISIONS:
        issues.append(issue("P1", "invalid_decision", "Decision", "Decision must be one of accepted, deferred, or failed."))
    elif decision != "accepted":
        issues.append(
            issue(
                "P2",
                "stability_window_not_accepted",
                "Decision",
                "Stable core requires an accepted compatibility/stability window record.",
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
                "End date must be the same as or later than Start date for stability-window evidence.",
            )
        )
    elif "Start date" in parsed_dates and "End date" in parsed_dates:
        calendar_days = (parsed_dates["End date"] - parsed_dates["Start date"]).days + 1
        if calendar_days < MIN_STABILITY_WINDOW_CALENDAR_DAYS:
            issues.append(
                issue(
                    "P2",
                    "stability_window_too_short",
                    "End date",
                    f"A stability window must cover at least {MIN_STABILITY_WINDOW_CALENDAR_DAYS} calendar days.",
                )
            )

    reference_root = resolved if resolved.is_dir() else evidence_file.parent
    for field in ("Release evidence reference", "Dogfood cycle reference"):
        value = fields.get(field, "")
        if value and not is_placeholder(value):
            if looks_like_url_reference(value):
                if not valid_url_reference(value):
                    issues.append(
                        issue(
                            "P2",
                            "invalid_evidence_reference_url",
                            field,
                            f"{field} must use a complete https URL when recorded as an external URL reference.",
                        )
                    )
                elif not concrete_url_reference(value):
                    issues.append(
                        issue(
                            "P2",
                            "weak_evidence_reference_url",
                            field,
                            f"{field} URL should point to a concrete run, artifact, release, dogfood, or evidence record.",
                        )
                    )
            elif "evidence" not in value.lower() and "docs/" not in value.lower() and "artifact" not in value.lower():
                issues.append(
                    issue(
                        "P2",
                        "weak_evidence_reference",
                        field,
                        f"{field} must point to a concrete evidence file, run URL, or recorded artifact.",
                    )
                )
            elif looks_like_local_markdown_reference(value):
                reference_file = resolve_local_reference(reference_root, value)
                if not path_is_within(reference_file, reference_root):
                    issues.append(
                        issue(
                            "P2",
                            "evidence_reference_outside_target",
                            field,
                            f"{field} points outside the audited target: {reference_file}",
                        )
                    )
                elif not reference_file.exists():
                    issues.append(
                        issue(
                            "P2",
                            "missing_evidence_reference_file",
                            field,
                            f"{field} points to a local evidence file that does not exist: {reference_file}",
                        )
                    )
                elif field == "Release evidence reference":
                    release_report = build_release_evidence_audit(reference_root, file_path=str(reference_file))
                    if not release_report.ready:
                        issues.append(
                            issue(
                                "P2",
                                "release_reference_not_ready",
                                field,
                                f"Referenced release evidence status is {release_report.status}; stability-window evidence requires an accepted release reference.",
                            )
                        )
                elif field == "Dogfood cycle reference":
                    dogfood_report = build_dogfood_cycle_audit(reference_root, file_path=str(reference_file))
                    if not dogfood_report.ready:
                        issues.append(
                            issue(
                                "P2",
                                "dogfood_reference_not_ready",
                                field,
                                f"Referenced dogfood cycle status is {dogfood_report.status}; stability-window evidence requires an accepted dogfood reference.",
                            )
                        )

    blocking_count = sum(1 for item in issues if item.severity in {"P0", "P1", "P2"})
    if blocking_count:
        status = "incomplete"
        ready = False
        next_actions = ["Fill missing stability-window fields after real elapsed use, then rerun audit-stability-window."]
    elif decision == "accepted":
        status = "accepted"
        ready = True
        next_actions = ["Link this stability window from stable-core-audit, milestone status, and release notes."]
    elif decision == "failed":
        status = "failed"
        ready = False
        next_actions = ["Fix the compatibility or recovery regression, then record a new stability window."]
    elif decision == "deferred":
        status = "deferred"
        ready = False
        next_actions = ["Finish the real compatibility window and update the evidence decision."]
    else:
        status = "incomplete"
        ready = False
        next_actions = ["Fill missing stability-window fields after real elapsed use, then rerun audit-stability-window."]

    return StabilityWindowReport(
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


def format_stability_window_audit(report: StabilityWindowReport) -> str:
    lines = [
        "# FictionOps Stability Window Audit",
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
        lines.append("No stability window issues found.")
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def render_stability_window_audit(report: StabilityWindowReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_stability_window_audit(report)
