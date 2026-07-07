from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .audit_plan import build_plan_audit_report
from .chapter_wave import build_chapter_wave_report
from .constants import DEFAULT_WATCH_TERMS
from .markdown import display_path, safe_cell
from .models import BookGateCheck, BookGateIssue, BookGateReport
from .plan_chapter import normalize_book_for_plan, resolve_outline_path
from .retrospective import build_retrospective_report
from .revision_plan import build_revision_plan
from .table_check import build_table_check_report
from .word_scan import build_word_scan_report


BLOCKING_SEVERITIES = {"P0", "P1", "P2"}

BOOK_BLOCKING_CODES = {
    "missing_book_outline",
    "no_chapter_plan_rows",
    "missing_chapter_file",
    "missing_chapter_engine",
    "engine_not_synced",
    "missing_book_retrospective",
    "placeholder_book_retrospective",
    "missing_chapter_retrospective",
    "placeholder_chapter_retrospective",
    "open_sync_item",
    "no_chapter_files",
}

MATERIAL_CODES = {"missing_book_outline", "no_chapter_plan_rows", "no_chapter_files"}


def resolve_book_gate_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate
    return (project / candidate).resolve()


def write_book_gate(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def severity_blocks(severity: str) -> bool:
    return (severity or "P4").upper() in BLOCKING_SEVERITIES


def book_issue_blocks(issue: BookGateIssue) -> bool:
    return severity_blocks(issue.severity) or issue.code in BOOK_BLOCKING_CODES


def gate_issue(
    *,
    source: str,
    issue: object,
    default_subject: str = "-",
    default_path: str = "-",
) -> BookGateIssue:
    return BookGateIssue(
        severity=str(getattr(issue, "severity", "P4") or "P4"),
        source=source,
        code=str(getattr(issue, "code", "issue") or "issue"),
        subject=str(
            getattr(issue, "chapter", "")
            or getattr(issue, "character", "")
            or getattr(issue, "thread", "")
            or getattr(issue, "item", "")
            or (f"line {getattr(issue, 'line', '')}" if getattr(issue, "line", 0) else "")
            or default_subject
        ),
        path=str(getattr(issue, "path", "") or default_path),
        message=str(getattr(issue, "message", "")),
    )


def revision_issue(task: object) -> BookGateIssue:
    suggested = str(getattr(task, "suggested_action", ""))
    message = str(getattr(task, "message", ""))
    if suggested:
        message = (message + " " if message else "") + f"Suggested action: {suggested}"
    return BookGateIssue(
        severity=str(getattr(task, "priority", "P4") or "P4"),
        source="revision-plan",
        code=str(getattr(task, "code", "issue") or "issue"),
        subject=str(getattr(task, "chapter", "") or "-"),
        path=str(getattr(task, "path", "") or "-"),
        message=message,
    )


def selected_revision_issues(
    tasks: list[object],
    *,
    max_notes: int = 8,
    skip_sources: set[str] | None = None,
) -> list[BookGateIssue]:
    skip_sources = skip_sources or set()
    filtered = [task for task in tasks if str(getattr(task, "source_command", "")) not in skip_sources]
    blocking = [revision_issue(task) for task in filtered if severity_blocks(str(getattr(task, "priority", "P4")))]
    notes: list[BookGateIssue] = []
    for task in filtered:
        if severity_blocks(str(getattr(task, "priority", "P4"))):
            continue
        notes.append(revision_issue(task))
        if len(notes) >= max_notes:
            break
    return blocking + notes


def check_from_issues(name: str, command: str, issues: list[BookGateIssue], summary: str) -> BookGateCheck:
    blocking = sum(1 for item in issues if book_issue_blocks(item))
    status = "pass" if not issues else ("blocked" if blocking else "notes")
    return BookGateCheck(
        name=name,
        source_command=command,
        status=status,
        issue_count=len(issues),
        blocking_issue_count=blocking,
        summary=summary,
    )


def next_actions(status: str, issues: list[BookGateIssue], *, book: str) -> list[str]:
    if status == "needs_book_material":
        return [
            f"Fill `04_structure/book_outlines/{book}_outline.md` and create/sync the planned chapter drafts.",
            f"Run `fictionops audit-plan . --book {book}` before closing the book.",
        ]
    blocking = [item for item in issues if book_issue_blocks(item)]
    if blocking:
        sources = sorted({item.source for item in blocking})
        return [
            "Resolve book-closing blockers from: " + ", ".join(sources) + ".",
            f"Run `fictionops revision-plan . --book {book}` after fixes, then rerun `fictionops book-gate . --book {book}`.",
        ]
    if issues:
        return [
            "Review non-blocking book notes before clean export.",
            f"If notes become real work, run `fictionops revision-plan . --book {book}` and track them there.",
        ]
    return [
        f"Proceed to clean export: `fictionops export-clean . --book {book}`.",
        f"After export, run `fictionops audit-publish . --book {book}`.",
    ]


def build_book_gate(
    project: Path,
    *,
    book: str = "book_01",
    outline: str | None = None,
    min_chapter_chars: int = 200,
    pattern: str = "**/*.md",
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> BookGateReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"book-gate requires a FictionOps project directory: {project}")

    resolved = project.expanduser().resolve()
    book_id = normalize_book_for_plan(book)
    issues: list[BookGateIssue] = []

    plan = None
    outline_path = resolve_outline_path(resolved, book=book_id, outline=outline)
    if not outline_path.exists():
        issues.append(
            BookGateIssue(
                severity="P2",
                source="audit-plan",
                code="missing_book_outline",
                subject="-",
                path=display_path(outline_path, resolved),
                message="Book outline file is missing.",
            )
        )
        plan_issues = [item for item in issues if item.source == "audit-plan"]
        plan_summary = "Book outline missing."
    else:
        plan = build_plan_audit_report(resolved, book=book_id, outline=outline)
        plan_issues = [gate_issue(source="audit-plan", issue=item) for item in plan.issues]
        issues.extend(plan_issues)
        plan_summary = (
            f"{plan.planned_chapters} planned, {plan.chapter_files} drafts, "
            f"{plan.engine_files} engines, {plan.synced_engines} synced."
        )

    retrospective = build_retrospective_report(resolved, book=book_id)
    retrospective_issues = [gate_issue(source="retrospective", issue=item) for item in retrospective.issues]
    issues.extend(retrospective_issues)

    revision_plan = build_revision_plan(
        resolved,
        book=book_id,
        outline=outline if outline_path.exists() else None,
        all_markdown=False,
        pattern=pattern,
        metric="nonspace",
        skip_standard=False,
        strict_standard=False,
        min_chapter_chars=min_chapter_chars,
        out=None,
        force=False,
        dry_run=True,
    )
    revision_issues = selected_revision_issues(
        revision_plan.tasks,
        skip_sources={"check-tables", "scan-words"},
    )
    issues.extend(revision_issues)

    book_root = resolved / "06_drafts" / book_id
    wave_target = book_root if book_root.exists() else resolved
    wave = build_chapter_wave_report(
        wave_target,
        all_markdown=False,
        pattern=pattern,
        metric="nonspace",
    )
    wave_issues = [gate_issue(source="audit-wave", issue=item) for item in wave.issues]
    issues.extend(wave_issues)

    word_scan = build_word_scan_report(
        wave_target,
        all_markdown=False,
        pattern=pattern,
        watch=",".join(DEFAULT_WATCH_TERMS),
        min_count=3,
        top=12,
    )
    table_check = build_table_check_report(
        resolved,
        all_markdown=True,
        pattern=pattern,
        min_filled_cells=1,
    )
    table_issues = [
        gate_issue(source="check-tables", issue=item)
        for item in table_check.issues
        if item.code != "no_tables"
    ]
    issues.extend(table_issues)

    checks = [
        check_from_issues("Plan coverage", "audit-plan", plan_issues, plan_summary),
        check_from_issues(
            "Retrospective closure",
            "retrospective",
            retrospective_issues,
            (
                f"{retrospective.chapter_count} chapters, {retrospective.retrospective_count} retrospectives, "
                f"{retrospective.sync_item_count} open sync item(s)."
            ),
        ),
        check_from_issues(
            "Revision blockers",
            "revision-plan",
            revision_issues,
            (
                f"{revision_plan.task_count} tasks; "
                + ", ".join(f"{key}={value}" for key, value in revision_plan.priority_counts.items())
            ),
        ),
        check_from_issues(
            "Project tables",
            "check-tables",
            table_issues,
            f"{table_check.table_count} tables across {table_check.file_count} files.",
        ),
        check_from_issues(
            "Word scan",
            "scan-words",
            [],
            f"{word_scan.file_count} chapters, {len(word_scan.aggregate_terms)} high-frequency term(s), {len(word_scan.watch_hits)} watched term(s).",
        ),
        check_from_issues(
            "Chapter wave",
            "audit-wave",
            wave_issues,
            f"{wave.file_count} chapters, average {wave.average}, spread {wave.spread_ratio_percent}%.",
        ),
    ]

    blocking_count = sum(1 for item in issues if book_issue_blocks(item))
    blocking_codes = {item.code for item in issues if book_issue_blocks(item)}
    if blocking_codes & MATERIAL_CODES:
        status = "needs_book_material"
        ready = False
    elif blocking_count:
        status = "needs_book_closure"
        ready = False
    elif issues:
        status = "book_notes"
        ready = True
    else:
        status = "ready_for_clean_export"
        ready = True

    output_path = resolve_book_gate_output_path(resolved, out) if out else None
    report = BookGateReport(
        target=str(resolved),
        book=book_id,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        status=status,
        ready=ready,
        issue_count=len(issues),
        blocking_issue_count=blocking_count,
        checks=checks,
        issues=issues,
        next_actions=next_actions(status, issues, book=book_id),
        plan=plan,
        retrospective=retrospective,
        revision_plan=revision_plan,
        word_scan=word_scan,
        tables=table_check,
    )
    if output_path and not dry_run:
        write_book_gate(output_path, render_book_gate(report, "markdown"), force=force)
        report.written = True
    return report


def render_book_gate(report: BookGateReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_book_gate(report)


def format_book_gate(report: BookGateReport) -> str:
    lines = [
        "# FictionOps Book Gate",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Status: `{report.status}`",
        f"- Ready: {'yes' if report.ready else 'no'}",
        f"- Issues: {report.issue_count}",
        f"- Blocking issues: {report.blocking_issue_count}",
        "",
        "## Checks",
        "",
        "| Check | Status | Issues | Blocking | Source | Summary |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for check in report.checks:
        lines.append(
            "| "
            + " | ".join(
                [
                    safe_cell(check.name),
                    safe_cell(check.status),
                    str(check.issue_count),
                    str(check.blocking_issue_count),
                    f"`{safe_cell(check.source_command)}`",
                    safe_cell(check.summary),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Source | Code | Subject | Path | Message |", "| --- | --- | --- | --- | --- | --- |"])
        for item in report.issues:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(item.severity),
                        safe_cell(item.source),
                        f"`{safe_cell(item.code)}`",
                        safe_cell(item.subject),
                        f"`{safe_cell(item.path)}`",
                        safe_cell(item.message),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No book-gate issues found.")

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
