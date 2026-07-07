from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .adopt import ADOPT_EXTENSIONS
from .book_gate import build_book_gate
from .character_audit import build_character_audit_report
from .constants import DEFAULT_WATCH_TERMS
from .doctor import build_doctor_report
from .information_audit import build_info_report
from .markdown import display_path, safe_cell
from .models import AdoptReviewCheck, AdoptReviewIssue, AdoptReviewReport, AdoptReviewWaiver


BLOCKING_SEVERITIES = {"P1", "P2"}
MIGRATION_MARKER_DIRS = {"adopt_review", "adopted_handoff", "import_queue", "imported"}
DEFAULT_WAIVER_FILE = Path("07_audits/adopt_review/waivers.json")
WAIVER_MATCH_FIELDS = ("source", "code", "subject", "path")


def issue_blocks(issue: AdoptReviewIssue) -> bool:
    return issue.severity.upper() in BLOCKING_SEVERITIES


def resolve_waiver_path(project: Path, waivers: str | None) -> Path | None:
    if waivers:
        candidate = Path(waivers).expanduser()
        if candidate.is_absolute():
            return candidate.resolve()
        return (project / candidate).resolve()
    default = project / DEFAULT_WAIVER_FILE
    return default.resolve() if default.exists() else None


def parse_waiver_entry(raw: object, index: int) -> AdoptReviewWaiver:
    if not isinstance(raw, dict):
        raise ValueError(f"waiver #{index} must be an object")
    reason = str(raw.get("reason", "") or "").strip()
    if not reason:
        raise ValueError(f"waiver #{index} requires a non-empty reason")
    fields = {
        "source": str(raw.get("source", "") or "").strip(),
        "code": str(raw.get("code", "") or "").strip(),
        "subject": str(raw.get("subject", "") or "").strip(),
        "path": str(raw.get("path", "") or "").strip(),
    }
    if not any(fields.values()):
        raise ValueError(f"waiver #{index} must match at least one of source, code, subject, or path")
    return AdoptReviewWaiver(
        source=fields["source"],
        code=fields["code"],
        subject=fields["subject"],
        path=fields["path"],
        reason=reason,
        owner=str(raw.get("owner", "") or "").strip(),
        until=str(raw.get("until", "") or "").strip(),
    )


def load_review_waivers(project: Path, waivers: str | None) -> tuple[Path | None, list[AdoptReviewWaiver]]:
    waiver_path = resolve_waiver_path(project, waivers)
    if waiver_path is None:
        return None, []
    if not waiver_path.exists():
        raise FileNotFoundError(f"adopt-review waiver file does not exist: {waiver_path}")
    try:
        data = json.loads(waiver_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid adopt-review waiver JSON: {waiver_path}: {exc}") from exc
    raw_waivers = data.get("waivers") if isinstance(data, dict) else data
    if not isinstance(raw_waivers, list):
        raise ValueError("adopt-review waivers must be a list or an object with a waivers list")
    return waiver_path, [parse_waiver_entry(raw, index) for index, raw in enumerate(raw_waivers, start=1)]


def waiver_matches_issue(waiver: AdoptReviewWaiver, issue: AdoptReviewIssue) -> bool:
    criteria = [
        (field, getattr(waiver, field))
        for field in WAIVER_MATCH_FIELDS
        if getattr(waiver, field)
    ]
    return bool(criteria) and all(str(getattr(issue, field)) == value for field, value in criteria)


def split_waived_issues(
    issues: list[AdoptReviewIssue],
    waivers: list[AdoptReviewWaiver],
) -> tuple[list[AdoptReviewIssue], list[AdoptReviewIssue]]:
    active: list[AdoptReviewIssue] = []
    waived: list[AdoptReviewIssue] = []
    for issue in issues:
        if any(waiver_matches_issue(waiver, issue) for waiver in waivers):
            waived.append(issue)
        else:
            active.append(issue)
    return active, waived


def collect_migration_files(project: Path) -> list[Path]:
    if not project.is_dir():
        return []
    files: list[Path] = []
    for path in project.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in ADOPT_EXTENSIONS:
            continue
        rel = path.relative_to(project)
        parts = {part.lower() for part in rel.parts}
        if parts & MIGRATION_MARKER_DIRS or ".imported." in path.name.lower():
            files.append(path)
    return sorted(files, key=lambda item: display_path(item, project))


def import_queue_files(project: Path) -> list[Path]:
    return [path for path in collect_migration_files(project) if "import_queue" in {part.lower() for part in path.relative_to(project).parts}]


def review_issue(
    *,
    severity: str,
    source: str,
    code: str,
    subject: str,
    path: str,
    message: str,
) -> AdoptReviewIssue:
    return AdoptReviewIssue(
        severity=severity or "P4",
        source=source,
        code=code or "issue",
        subject=subject or "-",
        path=path or "-",
        message=message or "",
    )


def issue_from_object(source: str, issue: object, *, default_subject: str = "-") -> AdoptReviewIssue:
    subject = (
        getattr(issue, "subject", "")
        or getattr(issue, "chapter", "")
        or getattr(issue, "character", "")
        or getattr(issue, "item", "")
        or getattr(issue, "thread", "")
        or default_subject
    )
    return review_issue(
        severity=str(getattr(issue, "severity", "P4") or "P4"),
        source=source,
        code=str(getattr(issue, "code", "issue") or "issue"),
        subject=str(subject or "-"),
        path=str(getattr(issue, "path", "") or "-"),
        message=str(getattr(issue, "message", "")),
    )


def check_status(blocking: int, issue_count: int) -> str:
    if blocking:
        return "blocked"
    if issue_count:
        return "notes"
    return "pass"


def make_check(name: str, source_command: str, issues: list[AdoptReviewIssue], summary: str) -> AdoptReviewCheck:
    blocking = sum(1 for issue in issues if issue_blocks(issue))
    return AdoptReviewCheck(
        name=name,
        source_command=source_command,
        status=check_status(blocking, len(issues)),
        issue_count=len(issues),
        blocking_issue_count=blocking,
        summary=summary,
    )


def migration_status(*, standard_project: bool, import_queue_count: int, blocking_count: int, issue_count: int) -> tuple[str, bool]:
    if not standard_project:
        return "not_fictionops_project", False
    if import_queue_count:
        return "needs_import_sorting", False
    if blocking_count:
        return "needs_migration_fixes", False
    if issue_count:
        return "migration_notes", True
    return "ready_for_project_work", True


def next_actions(
    *,
    standard_project: bool,
    import_queue_count: int,
    info_blockers: int,
    character_blockers: int,
    book_gate_blockers: int,
    waived_issue_count: int,
    book: str,
) -> list[str]:
    actions: list[str] = []
    if not standard_project:
        actions.append("Run `fictionops init <new-project>` and copy legacy files into that project before reviewing migration.")
    if import_queue_count:
        actions.append(
            f"Sort {import_queue_count} imported draft file(s) from `06_drafts/import_queue/` into book chapter folders, then create or sync chapter engines."
        )
    if info_blockers:
        actions.append("Convert imported canon notes into `05_canon/information_release_table.md` before drafting or reviewing new chapters.")
    if character_blockers:
        actions.append("Split imported character notes into character index, arc files, intelligence profiles, and voice profiles.")
    if book_gate_blockers:
        actions.append(f"Resolve book-gate blockers, then rerun `fictionops book-gate . --book {book}`.")
    if waived_issue_count:
        actions.append(
            "Review `07_audits/adopt_review/waivers.json` before normal drafting; waivers defer migration blockers but do not erase the decision record."
        )
    if not actions:
        actions.append(f"Run `fictionops doctor . --book {book}` and continue normal FictionOps review or drafting.")
    actions.append(f"After fixes, rerun `fictionops adopt-review . --book {book}` to confirm the migration sandbox is stable.")
    return actions


def resolve_adopt_review_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (project / candidate).resolve()


def write_adopt_review(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")


def build_adopt_review(
    project: Path,
    *,
    book: str = "book_01",
    pattern: str = "**/*.md",
    min_chapter_chars: int = 200,
    watch_terms: list[str] | None = None,
    top: int = 12,
    min_repeat: int = 3,
    scan_text: bool = True,
    stale_after: int = 8,
    max_issues: int = 80,
    waivers: str | None = None,
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> AdoptReviewReport:
    resolved = project.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")
    if not resolved.is_dir():
        raise ValueError(f"adopt-review requires a FictionOps project directory: {resolved}")
    if max_issues < 0:
        raise ValueError("adopt-review --max-issues must be >= 0")

    watch_terms = watch_terms or DEFAULT_WATCH_TERMS
    standard_project = (resolved / "project.yml").exists()
    migration_files = collect_migration_files(resolved)
    queued_files = import_queue_files(resolved)

    doctor = build_doctor_report(
        resolved,
        all_markdown=False,
        pattern=pattern,
        metric="nonspace",
        skip_standard=False,
        strict_standard=True,
        min_chapter_chars=min_chapter_chars,
        watch_terms=watch_terms,
        top=top,
        min_repeat=min_repeat,
        scan_text=scan_text,
        stale_after=stale_after,
        book=book,
        outline=None,
    )
    info = build_info_report(resolved, pattern=pattern, table_path=None, scan_text=scan_text)
    characters = build_character_audit_report(resolved, pattern=pattern)
    book_gate = build_book_gate(
        resolved,
        book=book,
        outline=None,
        min_chapter_chars=min_chapter_chars,
        pattern=pattern,
        out=None,
        force=False,
        dry_run=True,
    )

    project_issues: list[AdoptReviewIssue] = []
    if not standard_project:
        project_issues.append(
            review_issue(
                severity="P1",
                source="project-shape",
                code="missing_project_yml",
                subject="-",
                path="project.yml",
                message="Migration review requires an initialized FictionOps project.",
            )
        )
    if doctor.continuity.get("missing_standard_files", 0):
        project_issues.append(
            review_issue(
                severity="P2",
                source="doctor",
                code="missing_standard_project_files",
                subject="-",
                path="-",
                message=f"{doctor.continuity['missing_standard_files']} standard project-memory file(s) are missing.",
            )
        )
    if doctor.continuity.get("placeholder_standard_files", 0):
        project_issues.append(
            review_issue(
                severity="P3",
                source="doctor",
                code="placeholder_standard_project_files",
                subject="-",
                path="-",
                message=f"{doctor.continuity['placeholder_standard_files']} standard project-memory file(s) still look like templates.",
            )
        )

    import_issues: list[AdoptReviewIssue] = []
    if not migration_files:
        import_issues.append(
            review_issue(
                severity="P4",
                source="adopt-review",
                code="no_migration_imports",
                subject="-",
                path="-",
                message="No adopted/imported files were detected; this may be a fresh project or a migration that was already manually normalized.",
            )
        )
    if queued_files:
        import_issues.append(
            review_issue(
                severity="P2",
                source="adopt-review",
                code="import_queue_unsorted",
                subject="drafts",
                path="06_drafts/import_queue",
                message=f"{len(queued_files)} imported draft-like file(s) are still waiting to be assigned to book/chapter folders.",
            )
        )

    info_issues = [issue_from_object("audit-info", issue) for issue in info.issues]
    character_issues = [issue_from_object("audit-characters", issue) for issue in characters.issues]
    book_gate_issues = [issue_from_object("book-gate", issue) for issue in book_gate.issues]
    waiver_path, loaded_waivers = load_review_waivers(resolved, waivers)
    issues = project_issues + import_issues + info_issues + character_issues + book_gate_issues
    active_issues, waived_issues = split_waived_issues(issues, loaded_waivers)
    active_project_issues, _ = split_waived_issues(project_issues, loaded_waivers)
    active_import_issues, _ = split_waived_issues(import_issues, loaded_waivers)
    active_info_issues, _ = split_waived_issues(info_issues, loaded_waivers)
    active_character_issues, _ = split_waived_issues(character_issues, loaded_waivers)
    active_book_gate_issues, _ = split_waived_issues(book_gate_issues, loaded_waivers)
    blocking_count = sum(1 for issue in active_issues if issue_blocks(issue))
    status, ready = migration_status(
        standard_project=standard_project,
        import_queue_count=len(queued_files),
        blocking_count=blocking_count,
        issue_count=len(active_issues),
    )

    checks = [
        make_check(
            "Project shape",
            "init",
            active_project_issues,
            f"standard_project={standard_project}, missing_standard={doctor.continuity.get('missing_standard_files', 0)}, placeholders={doctor.continuity.get('placeholder_standard_files', 0)}",
        ),
        make_check(
            "Adopted imports",
            "adopt --copy-to",
            active_import_issues,
            f"migration_files={len(migration_files)}, import_queue={len(queued_files)}",
        ),
        make_check(
            "Doctor",
            "doctor",
            [
                review_issue(
                    severity=severity,
                    source="doctor",
                    code=f"{severity.lower()}_issues",
                    subject="-",
                    path="-",
                    message=f"Doctor reported {count} {severity} issue(s).",
                )
                for severity, count in doctor.issue_counts.items()
                if count and severity in BLOCKING_SEVERITIES
            ],
            f"status={doctor.status}, P1={doctor.issue_counts.get('P1', 0)}, P2={doctor.issue_counts.get('P2', 0)}, P3={doctor.issue_counts.get('P3', 0)}",
        ),
        make_check(
            "Information boundary",
            "audit-info",
            active_info_issues,
            f"tables={len(info.table_files)}, items={info.item_count}, issues={len(info.issues)}",
        ),
        make_check(
            "Characters",
            "audit-characters",
            active_character_issues,
            f"characters={characters.character_count}, arcs={characters.arc_count}, issues={len(characters.issues)}",
        ),
        make_check(
            "Book gate",
            "book-gate",
            active_book_gate_issues,
            f"status={book_gate.status}, ready={book_gate.ready}, blocking={book_gate.blocking_issue_count}, issues={book_gate.issue_count}",
        ),
    ]

    output_path = resolve_adopt_review_output_path(resolved, out) if out else None
    displayed_issues = active_issues[:max_issues] if max_issues else []
    report = AdoptReviewReport(
        target=str(resolved),
        book=book,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        status=status,
        ready=ready,
        standard_project=standard_project,
        migration_files=len(migration_files),
        import_queue_files=len(queued_files),
        total_issue_count=len(issues),
        issue_count=len(active_issues),
        blocking_issue_count=blocking_count,
        waived_issue_count=len(waived_issues),
        waiver_file=str(waiver_path) if waiver_path else None,
        waivers=loaded_waivers,
        max_issues=max_issues,
        omitted_issues=max(0, len(active_issues) - len(displayed_issues)),
        checks=checks,
        issues=displayed_issues,
        next_actions=next_actions(
            standard_project=standard_project,
            import_queue_count=len(queued_files),
            info_blockers=sum(1 for issue in active_info_issues if issue_blocks(issue)),
            character_blockers=sum(1 for issue in active_character_issues if issue_blocks(issue)),
            book_gate_blockers=sum(1 for issue in active_book_gate_issues if issue_blocks(issue)),
            waived_issue_count=len(waived_issues),
            book=book,
        ),
        doctor=doctor,
        info=info,
        characters=characters,
        book_gate=book_gate,
    )
    if output_path and not dry_run:
        write_adopt_review(output_path, render_adopt_review(report, "markdown"), force=force)
        report.written = True
    return report


def format_adopt_review(report: AdoptReviewReport) -> str:
    lines = [
        "# FictionOps Adopt Review",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Status: `{report.status}`",
        f"- Ready: {'yes' if report.ready else 'no'}",
        f"- Standard project: {'yes' if report.standard_project else 'no'}",
        f"- Migration files: {report.migration_files}",
        f"- Import queue files: {report.import_queue_files}",
        f"- Total issues: {report.total_issue_count}",
        f"- Active issues: {report.issue_count}",
        f"- Blocking issues: {report.blocking_issue_count}",
        f"- Waived issues: {report.waived_issue_count}",
        f"- Waiver file: `{report.waiver_file}`" if report.waiver_file else "- Waiver file: -",
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
    if report.waived_issue_count:
        lines.append("Issues shown here are active issues after applying migration waivers.")
        lines.append("")
    if report.issues:
        lines.extend(["| Severity | Source | Code | Subject | Path | Message |", "| --- | --- | --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(issue.severity),
                        safe_cell(issue.source),
                        f"`{safe_cell(issue.code)}`",
                        safe_cell(issue.subject),
                        f"`{safe_cell(issue.path)}`",
                        safe_cell(issue.message),
                    ]
                )
                + " |"
            )
        if report.omitted_issues:
            lines.append(f"| P4 | adopt-review | `omitted_issues` | - | - | {report.omitted_issues} issue(s) omitted by --max-issues. |")
    else:
        lines.append("No migration review issues found.")

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def render_adopt_review(report: AdoptReviewReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_adopt_review(report)
