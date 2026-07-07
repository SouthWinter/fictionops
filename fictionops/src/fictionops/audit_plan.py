from __future__ import annotations

from pathlib import Path

from .echo_audit import blankish
from .markdown import display_path, extract_chapter_key, natural_key, safe_cell
from .models import PlanAuditChapter, PlanAuditIssue, PlanAuditReport
from .new_chapter import chapter_paths, normalize_chapter_number
from .plan_chapter import load_chapter_plans, normalize_book_for_plan, resolve_outline_path


def collect_book_files(project: Path, *, book: str, kind: str) -> dict[str, Path]:
    directory = project / "06_drafts" / book / kind
    if not directory.exists():
        return {}
    files = sorted([path for path in directory.glob("*.md") if path.is_file()], key=natural_key)
    indexed: dict[str, Path] = {}
    for path in files:
        key = extract_chapter_key(path)
        indexed.setdefault(key, path)
    return indexed


def missing_engine_fields(engine_text: str, plan_values: dict[str, str]) -> list[str]:
    missing: list[str] = []
    for field, value in plan_values.items():
        if blankish(value):
            continue
        if value.strip() not in engine_text:
            missing.append(field)
    return missing


def plan_values(plan: object) -> dict[str, str]:
    return {
        "title": getattr(plan, "title", ""),
        "viewpoint": getattr(plan, "viewpoint", ""),
        "kind": getattr(plan, "kind", ""),
        "pressure": getattr(plan, "pressure", ""),
        "desire": getattr(plan, "desire", ""),
        "obstacle": getattr(plan, "obstacle", ""),
        "change": getattr(plan, "change", ""),
        "remainder": getattr(plan, "remainder", ""),
        "target_chars": getattr(plan, "target_chars", ""),
    }


def build_plan_audit_report(project: Path, *, book: str, outline: str | None) -> PlanAuditReport:
    resolved = project.expanduser().resolve()
    book_id = normalize_book_for_plan(book)
    outline_path = resolve_outline_path(resolved, book=book_id, outline=outline)
    if not outline_path.exists():
        raise FileNotFoundError(f"book outline not found: {outline_path}")

    plans = load_chapter_plans(outline_path)
    chapter_files = collect_book_files(resolved, book=book_id, kind="chapters")
    engine_files = collect_book_files(resolved, book=book_id, kind="chapter_engines")

    chapters: list[PlanAuditChapter] = []
    issues: list[PlanAuditIssue] = []
    planned_keys: set[str] = set()
    synced_count = 0

    if not plans:
        issues.append(
            PlanAuditIssue(
                severity="P2",
                code="no_chapter_plan_rows",
                chapter="-",
                path=display_path(outline_path, resolved),
                message="No recognizable chapter-planning rows were found in the book outline.",
            )
        )

    for plan in plans:
        chapter_key = normalize_chapter_number(plan.chapter)
        planned_keys.add(chapter_key)
        expected_paths = chapter_paths(resolved, book=book_id, chapter_number=chapter_key)
        chapter_file = chapter_files.get(chapter_key)
        engine_file = engine_files.get(chapter_key)
        missing_fields: list[str] = []
        engine_synced = False

        if engine_file:
            missing_fields = missing_engine_fields(engine_file.read_text(encoding="utf-8"), plan_values(plan))
            engine_synced = not missing_fields
            if engine_synced:
                synced_count += 1
        chapters.append(
            PlanAuditChapter(
                chapter=chapter_key,
                title=plan.title,
                row=plan.row,
                chapter_file=display_path(chapter_file, resolved) if chapter_file else None,
                engine_file=display_path(engine_file, resolved) if engine_file else None,
                engine_synced=engine_synced,
                missing_engine_fields=missing_fields,
            )
        )

        if not chapter_file:
            issues.append(
                PlanAuditIssue(
                    severity="P3",
                    code="missing_chapter_file",
                    chapter=chapter_key,
                    path=display_path(expected_paths["chapter"], resolved),
                    message="Chapter is planned in the book outline but no draft file exists.",
                )
            )
        if not engine_file:
            issues.append(
                PlanAuditIssue(
                    severity="P2",
                    code="missing_chapter_engine",
                    chapter=chapter_key,
                    path=display_path(expected_paths["engine"], resolved),
                    message="Chapter is planned in the book outline but no chapter engine exists.",
                )
            )
        elif missing_fields:
            issues.append(
                PlanAuditIssue(
                    severity="P3",
                    code="engine_not_synced",
                    chapter=chapter_key,
                    path=display_path(engine_file, resolved),
                    message="Chapter engine is missing planned fields: " + ", ".join(missing_fields),
                )
            )

    for chapter_key, path in chapter_files.items():
        if chapter_key not in planned_keys:
            issues.append(
                PlanAuditIssue(
                    severity="P4",
                    code="unplanned_chapter_file",
                    chapter=chapter_key,
                    path=display_path(path, resolved),
                    message="Draft chapter exists but no matching row was found in the book outline.",
                )
            )

    return PlanAuditReport(
        target=str(resolved),
        book=book_id,
        outline_file=str(outline_path),
        planned_chapters=len(plans),
        chapter_files=len(chapter_files),
        engine_files=len(engine_files),
        synced_engines=synced_count,
        chapters=chapters,
        issues=issues,
    )


def format_plan_audit_report(report: PlanAuditReport) -> str:
    lines = [
        "# FictionOps Plan Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Outline: `{report.outline_file}`",
        f"- Planned chapters: {report.planned_chapters}",
        f"- Chapter files: {report.chapter_files}",
        f"- Engine files: {report.engine_files}",
        f"- Synced engines: {report.synced_engines}",
        f"- Issues: {len(report.issues)}",
        "",
        "## Chapter Plan Coverage",
        "",
        "| Chapter | Title | Outline Row | Draft | Engine | Synced | Missing Engine Fields |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    if report.chapters:
        for chapter in report.chapters:
            lines.append(
                "| "
                + " | ".join(
                    [
                        chapter.chapter,
                        safe_cell(chapter.title),
                        str(chapter.row),
                        f"`{safe_cell(chapter.chapter_file)}`" if chapter.chapter_file else "-",
                        f"`{safe_cell(chapter.engine_file)}`" if chapter.engine_file else "-",
                        "yes" if chapter.engine_synced else "no",
                        ", ".join(chapter.missing_engine_fields) if chapter.missing_engine_fields else "-",
                    ]
                )
                + " |"
            )
    else:
        lines.append("| - | No planned chapters found. | - | - | - | no | - |")

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Chapter | Path | Message |", "| --- | --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                f"| {issue.severity} | {issue.code} | {issue.chapter} | `{safe_cell(issue.path)}` | {safe_cell(issue.message)} |"
            )
    else:
        lines.append("No plan coverage gaps found.")
    return "\n".join(lines)
