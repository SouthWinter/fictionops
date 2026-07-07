from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .dogfood_cycle import build_dogfood_cycle_audit
from .markdown import safe_cell
from .models import StableCoreActionItem, StableCoreIssue, StableCoreReport
from .release_evidence import build_release_evidence_audit
from .stability_window import build_stability_window_audit


REQUIRED_LOCAL_FILES = [
    "CHANGELOG.md",
    "docs/cli-contracts.md",
    "docs/compatibility.md",
    "docs/compatibility.zh-CN.md",
    "docs/known-limits.md",
    "docs/known-limits.zh-CN.md",
    "docs/recovery.md",
    "docs/recovery.zh-CN.md",
    "docs/stable-core-audit.md",
    "docs/stable-core-audit.zh-CN.md",
    "docs/milestone-status.md",
    "docs/milestone-status.zh-CN.md",
    "docs/release-trial-evidence.md",
    "docs/dogfood-cycle-evidence.md",
    "docs/stability-window-evidence.md",
    "docs/stability-window-evidence.zh-CN.md",
    ".github/workflows/fictionops-ci.yml",
    ".github/workflows/fictionops-publish.yml",
    "tests/test_cli.py",
]

def issue(severity: str, code: str, field: str, message: str) -> StableCoreIssue:
    return StableCoreIssue(severity=severity, code=code, field=field, message=message)


def blocking_count(issues: list[StableCoreIssue]) -> int:
    return sum(1 for item in issues if item.severity in {"P0", "P1", "P2"})


def stable_core_claim(text: str) -> str:
    lowered = text.lower()
    if "current result:" in lowered and "not complete" in lowered:
        return "not_complete"
    if "current result:" in lowered and "complete" in lowered:
        return "complete"
    return "unknown"


def milestone_claim(text: str) -> str:
    if "1.0.0 Stable Core | Not complete" in text:
        return "not_complete"
    if "1.0.0 Stable Core | Complete" in text:
        return "complete"
    return "unknown"


def next_actions_for_stable_core(report: StableCoreReport) -> list[str]:
    actions: list[str] = []
    if not report.release_evidence_ready:
        actions.append("Fill external release trial evidence and rerun `fictionops audit-release-evidence`.")
    if not report.dogfood_cycle_ready:
        actions.append("Complete a sustained post-migration dogfood cycle and rerun `fictionops audit-dogfood-cycle`.")
    if not report.stability_window_ready:
        actions.append("Fill `docs/stability-window-evidence.md` after a real compatibility window and rerun `fictionops audit-stability-window`.")
    if report.local_foundation_ready and not actions:
        actions.append("Update stable-core audit, milestone status, release notes, and changelog before marking 1.0 complete.")
    elif not report.local_foundation_ready:
        actions.append("Restore missing local governance docs, workflows, or tests before rerunning audit-stable-core.")
    return actions


def display_evidence_path(report: StableCoreReport, value: object, fallback: str) -> str:
    text = str(value or fallback)
    try:
        path = Path(text)
        target = Path(report.target)
        if path.is_absolute():
            return path.relative_to(target).as_posix()
    except (OSError, ValueError):
        pass
    return text.replace("\\", "/")


def action_items_for_stable_core(report: StableCoreReport) -> list[StableCoreActionItem]:
    release_file = display_evidence_path(report, report.evidence.get("release_evidence_file"), "docs/release-trial-evidence.md")
    dogfood_file = display_evidence_path(report, report.evidence.get("dogfood_cycle_file"), "docs/dogfood-cycle-evidence.md")
    stability_file = display_evidence_path(report, report.evidence.get("stability_window_file"), "docs/stability-window-evidence.md")
    local_files = report.evidence.get("missing_local_files", [])
    missing_count = len(local_files) if isinstance(local_files, list) else 0

    items = [
        StableCoreActionItem(
            item_id="local-foundation",
            title="Restore local governance files, workflows, and tests",
            status="complete" if report.local_foundation_ready else "local_required",
            priority="P1" if not report.local_foundation_ready else "P3",
            evidence_file="; ".join(REQUIRED_LOCAL_FILES),
            audit_command="fictionops audit-stable-core . --format json",
            acceptance="local_foundation_ready is true and missing_local_files is empty.",
            notes="All required local stable-core files are present." if report.local_foundation_ready else f"{missing_count} required local evidence file(s) are missing.",
        ),
        StableCoreActionItem(
            item_id="release-trial-evidence",
            title="Record accepted external package release-trial evidence",
            status="complete" if report.release_evidence_ready else "external_required",
            priority="P1" if not report.release_evidence_ready else "P3",
            evidence_file=release_file,
            audit_command=f"fictionops audit-release-evidence . --file {release_file} --format json",
            acceptance="audit-release-evidence returns ready=true with accepted external release evidence.",
            notes="Requires real GitHub Actions, artifact, and install-smoke evidence outside the local checkout.",
        ),
        StableCoreActionItem(
            item_id="sustained-dogfood-cycle",
            title="Record an accepted sustained post-migration dogfood cycle",
            status="complete" if report.dogfood_cycle_ready else "external_required",
            priority="P1" if not report.dogfood_cycle_ready else "P3",
            evidence_file=dogfood_file,
            audit_command=f"fictionops audit-dogfood-cycle . --file {dogfood_file} --format json",
            acceptance="audit-dogfood-cycle returns ready=true for a filled accepted maintenance cycle.",
            notes="Requires elapsed real project work after migration closure; a template or deferred record is not enough.",
        ),
        StableCoreActionItem(
            item_id="stability-window",
            title="Record an accepted compatibility/stability window",
            status="complete" if report.stability_window_ready else "external_required",
            priority="P2" if not report.stability_window_ready else "P3",
            evidence_file=stability_file,
            audit_command=f"fictionops audit-stability-window . --file {stability_file} --format json",
            acceptance="audit-stability-window returns ready=true with Decision: accepted.",
            notes="Requires a real elapsed compatibility window tied to release and dogfood evidence.",
        ),
    ]

    if report.local_foundation_ready and report.release_evidence_ready and report.dogfood_cycle_ready and report.stability_window_ready:
        doc_ready = report.stable_core_doc_claim == "complete" and report.milestone_claim == "complete"
        items.append(
            StableCoreActionItem(
                item_id="stable-core-ledger",
                title="Update stable-core audit and milestone ledger",
                status="complete" if doc_ready else "docs_update_required",
                priority="P3",
                evidence_file="docs/stable-core-audit.md; docs/milestone-status.md",
                audit_command="fictionops audit-stable-core . --format json",
                acceptance="audit-stable-core returns ready=true after docs honestly claim completion.",
                notes="Only update completion claims after release, dogfood, and stability-window evidence are all accepted.",
            )
        )
    return items


def build_stable_core_audit(
    target: Path,
    *,
    release_file: str | None = None,
    dogfood_file: str | None = None,
    stability_file: str | None = None,
) -> StableCoreReport:
    resolved = target.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")
    if not resolved.is_dir():
        raise ValueError(f"audit-stable-core requires a repository/project directory: {resolved}")

    issues: list[StableCoreIssue] = []
    missing_files: list[str] = []
    for item in REQUIRED_LOCAL_FILES:
        candidate = resolved / item
        if item.startswith(".github/") and not candidate.exists():
            candidate = resolved.parent / item
        if not candidate.exists():
            missing_files.append(item)
            issues.append(issue("P1", "missing_local_evidence", item, f"Required stable-core evidence file is missing: {item}"))

    release_report = build_release_evidence_audit(resolved, file_path=release_file)
    dogfood_report = build_dogfood_cycle_audit(resolved, file_path=dogfood_file)
    if not release_report.ready:
        issues.append(
            issue(
                "P1",
                "release_evidence_not_ready",
                "release_evidence",
                f"Release evidence status is {release_report.status}; stable core requires accepted external package evidence.",
            )
        )
    if not dogfood_report.ready:
        issues.append(
            issue(
                "P1",
                "dogfood_cycle_not_ready",
                "dogfood_cycle",
                f"Dogfood cycle status is {dogfood_report.status}; stable core requires an accepted sustained cycle.",
            )
        )

    stability_report = build_stability_window_audit(resolved, file_path=stability_file)
    issues.extend(
        StableCoreIssue(
            severity=item.severity,
            code=item.code,
            field=item.field,
            message=item.message,
        )
        for item in stability_report.issues
    )

    stable_doc_claim = "missing"
    stable_doc = resolved / "docs" / "stable-core-audit.md"
    if stable_doc.exists():
        stable_doc_claim = stable_core_claim(stable_doc.read_text(encoding="utf-8"))
    milestone_doc_claim = "missing"
    milestone_doc = resolved / "docs" / "milestone-status.md"
    if milestone_doc.exists():
        milestone_doc_claim = milestone_claim(milestone_doc.read_text(encoding="utf-8"))

    local_ready = not missing_files
    evidence_ready = release_report.ready and dogfood_report.ready and stability_report.ready
    if evidence_ready and local_ready:
        if stable_doc_claim != "complete":
            issues.append(
                issue(
                    "P3",
                    "stable_core_doc_not_updated",
                    "docs/stable-core-audit.md",
                    "Evidence appears ready, but stable-core-audit.md does not claim completion.",
                )
            )
        if milestone_doc_claim != "complete":
            issues.append(
                issue(
                    "P3",
                    "milestone_status_not_updated",
                    "docs/milestone-status.md",
                    "Evidence appears ready, but milestone-status.md does not mark 1.0 complete.",
                )
            )
    else:
        if stable_doc_claim == "complete":
            issues.append(
                issue(
                    "P1",
                    "stable_core_doc_overclaims",
                    "docs/stable-core-audit.md",
                    "stable-core-audit.md claims completion while required evidence is not ready.",
                )
            )
        if milestone_doc_claim == "complete":
            issues.append(
                issue(
                    "P1",
                    "milestone_status_overclaims",
                    "docs/milestone-status.md",
                    "milestone-status.md claims 1.0 completion while required evidence is not ready.",
                )
            )

    blockers = blocking_count(issues)
    if blockers:
        status = "not_ready"
        ready = False
    elif stable_doc_claim == "complete" and milestone_doc_claim == "complete":
        status = "ready"
        ready = True
    else:
        status = "ready_needs_docs_update"
        ready = False

    report = StableCoreReport(
        target=str(resolved),
        status=status,
        ready=ready,
        local_foundation_ready=local_ready,
        release_evidence_ready=release_report.ready,
        dogfood_cycle_ready=dogfood_report.ready,
        stability_window_ready=stability_report.ready,
        stable_core_doc_claim=stable_doc_claim,
        milestone_claim=milestone_doc_claim,
        issue_count=len(issues),
        blocking_issue_count=blockers,
        issues=issues,
        evidence={
            "missing_local_files": missing_files,
            "release_evidence_status": release_report.status,
            "release_evidence_file": release_report.evidence_file,
            "release_evidence_blocking_issues": release_report.blocking_issue_count,
            "dogfood_cycle_status": dogfood_report.status,
            "dogfood_cycle_file": dogfood_report.evidence_file,
            "dogfood_cycle_blocking_issues": dogfood_report.blocking_issue_count,
            "stability_window_status": stability_report.status,
            "stability_window_file": stability_report.evidence_file,
            "stability_window_blocking_issues": stability_report.blocking_issue_count,
            "stability_window_field_count": stability_report.field_count,
        },
        action_items=[],
        next_actions=[],
    )
    report.action_items = action_items_for_stable_core(report)
    report.next_actions = next_actions_for_stable_core(report)
    return report


def format_stable_core_audit(report: StableCoreReport) -> str:
    lines = [
        "# FictionOps Stable Core Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Status: `{report.status}`",
        f"- Ready: {'yes' if report.ready else 'no'}",
        f"- Local foundation ready: {'yes' if report.local_foundation_ready else 'no'}",
        f"- Release evidence ready: {'yes' if report.release_evidence_ready else 'no'}",
        f"- Dogfood cycle ready: {'yes' if report.dogfood_cycle_ready else 'no'}",
        f"- Stability window ready: {'yes' if report.stability_window_ready else 'no'}",
        f"- Stable-core doc claim: `{report.stable_core_doc_claim}`",
        f"- Milestone claim: `{report.milestone_claim}`",
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
                    [safe_cell(item.severity), f"`{safe_cell(item.code)}`", safe_cell(item.field), safe_cell(item.message)]
                )
                + " |"
            )
    else:
        lines.append("No stable-core issues found.")
    lines.extend(["", "## Evidence", ""])
    for key, value in report.evidence.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Action Plan", ""])
    if report.action_items:
        lines.extend(["| ID | Status | Priority | Evidence | Audit Command | Acceptance |", "| --- | --- | --- | --- | --- | --- |"])
        for item in report.action_items:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{safe_cell(item.item_id)}`",
                        f"`{safe_cell(item.status)}`",
                        safe_cell(item.priority),
                        safe_cell(item.evidence_file),
                        f"`{safe_cell(item.audit_command)}`",
                        safe_cell(item.acceptance),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No stable-core action items.")
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def render_stable_core_audit(report: StableCoreReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_stable_core_audit(report)
