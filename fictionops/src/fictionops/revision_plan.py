from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .audit_plan import build_plan_audit_report
from .chapter_wave import build_chapter_wave_report
from .character_audit import build_character_audit_report
from .constants import DEFAULT_WATCH_TERMS
from .continuity_audit import build_continuity_report
from .doctor import (
    build_epub_doctor_section,
    build_manifest_doctor_section,
    build_metadata_doctor_section,
    build_publish_doctor_section,
    build_retrospective_doctor_section,
    doctor_status,
    looks_like_standard_project,
)
from .echo_audit import build_echo_report
from .information_audit import build_info_report
from .markdown import safe_cell
from .models import RevisionPlanReport, RevisionTask, TableCheckReport, WordScanReport
from .plan_chapter import normalize_book_for_plan, resolve_outline_path
from .stats import build_stats_report
from .style_audit import build_style_audit_report
from .table_check import build_table_check_report
from .word_scan import build_word_scan_report


PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4, "P5": 5}
AREA_ORDER = {
    "continuity": 0,
    "information": 1,
    "character_or_plan": 2,
    "chapter_engine": 3,
    "table": 4,
    "foreshadowing": 5,
    "retrospective": 6,
    "pacing": 7,
    "style": 8,
    "publish": 9,
}


ACTION_BY_CODE = {
    "missing_standard_file": "Create or restore this project-memory file before continuing structural work.",
    "placeholder_standard_file": "Fill this project-memory file or archive it if the project no longer uses it.",
    "missing_chapter_engine": "Create the missing chapter engine, then sync it from the book outline if possible.",
    "placeholder_chapter_engine": "Fill the chapter engine pressure, desire, obstacle, change, and remainder fields.",
    "missing_chapter_retrospective": "Add a chapter retrospective so post-draft decisions are not lost.",
    "placeholder_retrospective": "Replace the placeholder retrospective with actual revision notes.",
    "placeholder_chapter": "Draft or expand the chapter before treating it as part of the maintained manuscript.",
    "missing_character_index": "Create a character index so the maintained cast can be scanned at handoff.",
    "no_character_index_rows": "Fill the character index with at least the active cast and arc file references.",
    "missing_character_arcs": "Create filled character arc files for the major active characters.",
    "placeholder_character_arc": "Replace the placeholder character arc with actual wound, desire, voice, growth, and failure-path material.",
    "missing_character_identity": "Fill the character identity fields so later tools do not infer the wrong person.",
    "missing_character_start": "Record the character's starting wound, desire, fear, misunderstanding, or self-protection.",
    "missing_character_intelligence": "Record what this character sees quickly, misses, and how they fail.",
    "missing_character_voice": "Record the character's voice and behavior markers before dialogue-heavy drafting.",
    "missing_character_growth": "Fill the growth path with pressure, irreversible choices, and costs.",
    "missing_failure_path": "Add the tempting failure path so growth has a visible counterforce.",
    "missing_relationship_anchors": "Add relationship anchors where they matter for this character's choices.",
    "indexed_character_missing_arc": "Create or link the character's arc file from the character index.",
    "arc_not_listed_in_index": "Add this arc file's character to the character index.",
    "missing_intelligence_profiles": "Create the global intelligence profile table or rely on filled per-character arcs.",
    "no_intelligence_profiles": "Fill the global intelligence profile table or confirm each arc carries its own intelligence mode.",
    "missing_voice_profiles": "Create the global voice profile table or rely on filled per-character arcs.",
    "no_voice_profiles": "Fill the global voice profile table or confirm each arc carries its own voice mode.",
    "character_missing_intelligence_profile": "Add this character to the intelligence profile table or fill the intelligence section in their arc.",
    "character_missing_voice_profile": "Add this character to the voice profile table or fill the voice section in their arc.",
    "no_chapter_plan_rows": "Add a recognizable chapter-planning table to the book outline.",
    "missing_chapter_file": "Create the planned chapter draft or remove the stale outline row.",
    "engine_not_synced": "Run plan-chapter or manually align the chapter engine with the book outline.",
    "unplanned_chapter_file": "Add this chapter to the book outline or archive the stray draft.",
    "missing_information_table": "Create and fill an information release table before drafting secret-heavy scenes.",
    "no_information_items": "Add at least one recognizable information/secret row to the table.",
    "missing_author_truth": "Record the author truth so later revisions do not guess at this secret.",
    "missing_reader_state": "Record what the reader currently knows at this point in the manuscript.",
    "missing_in_world_versions": "Record at least one character, public, or official version of this information.",
    "missing_next_release": "Plan the next release point or explicitly mark this item as intentionally dormant.",
    "missing_forbidden_note": "Record what must not be revealed early.",
    "forbidden_text_hit": "Review the first text hit and rewrite it as rumor, partial evidence, silence, or safe action if needed.",
    "early_text_hit_before_release": "Move, mask, or reclassify this information so release order stays intentional.",
    "missing_echo_table": "Create a foreshadowing echo table before relying on long-range callbacks.",
    "no_echo_threads": "Add recognizable foreshadowing rows to the echo table.",
    "missing_first_plant": "Record where this thread first enters the reader's memory.",
    "missing_last_echo": "Record the latest echo or add a light reminder if the thread is still active.",
    "missing_next_echo": "Plan a light next echo so the thread does not vanish.",
    "missing_payoff_direction": "Write the intended payoff or transformation direction.",
    "missing_forbidden_reveal": "Record what must not be explained yet.",
    "stale_last_echo": "Add a light echo, close the thread, or mark it dormant.",
    "no_text_hit": "Confirm whether this is an abstract thread; otherwise add a textual anchor.",
    "too_uniform_wave": "Review whether chapters are being filled to a mechanical target instead of pressure needs.",
    "flat_chapter_run": "Vary chapter pressure and scene count; do not fix this by padding alone.",
    "same_band_run": "Check whether the repeated length band is intentional.",
    "short_chapter_run": "Confirm these short chapters have enough pressure, change, and residue.",
    "heavy_chapter_run": "Split, sharpen, or justify the sustained heavy chapters.",
    "abrupt_length_jump": "Check whether the sudden length jump matches a real structural escalation.",
    "open_sync_item": "Sync this retrospective item into the relevant canon, outline, or character file.",
    "missing_book_retrospective": "Create the book retrospective before treating the book as closed.",
    "placeholder_book_retrospective": "Fill the book retrospective with actual book-level residue and follow-up.",
    "draft_marker_present": "Remove draft markers from clean Markdown before release.",
    "missing_metadata_field": "Fill the required publish metadata field.",
    "manifest_not_exported": "Export the publish manifest after clean Markdown and metadata are ready.",
    "stale_manifest": "Regenerate the manifest so hashes match current publish inputs.",
    "empty_header": "Fill or rename the empty Markdown table header cell.",
    "duplicate_header": "Rename duplicate Markdown table headers so later scans can distinguish fields.",
    "empty_table": "Add body rows or remove the unused Markdown table.",
    "row_width_mismatch": "Fix this Markdown table row so it has the same number of cells as the header.",
    "mostly_empty_row": "Fill the row with real material or remove it if it is only a placeholder.",
    "no_filled_cells": "Replace placeholder table cells with usable project memory.",
    "high_frequency_word_scan": "Read the repeated term in context and vary it only if it weakens freshness or voice.",
}

AREA_DEFAULT_ACTION = {
    "continuity": "Resolve this continuity maintenance issue before deeper prose polish.",
    "information": "Update the information release table and revise the affected text if needed.",
    "character_or_plan": "Align the plan, chapter engine, and character logic before drafting onward.",
    "chapter_engine": "Strengthen the chapter engine so pressure and change are explicit.",
    "foreshadowing": "Update the echo table and add, move, or close the relevant thread.",
    "retrospective": "Close this post-draft follow-up so the next task does not rely on memory.",
    "pacing": "Review chapter length as a pressure signal, not only as a word-count target.",
    "style": "Reduce density only where the pattern harms reader trust or freshness.",
    "table": "Repair table structure before using it as project memory.",
    "publish": "Fix this publish pipeline issue before release packaging.",
}


def task_from_issue(
    issue: object,
    *,
    area: str,
    source_command: str,
    default_path: str = "-",
) -> RevisionTask:
    code = str(getattr(issue, "code", "issue"))
    message = str(getattr(issue, "message", ""))
    priority = str(getattr(issue, "severity", "P4") or "P4")
    chapter = str(
        getattr(issue, "chapter", "")
        or getattr(issue, "character", "")
        or getattr(issue, "thread", "")
        or getattr(issue, "item", "")
        or "-"
    )
    path = str(getattr(issue, "path", "") or default_path or "-")
    return RevisionTask(
        priority=priority,
        area=area,
        source_command=source_command,
        code=code,
        chapter=chapter,
        path=path,
        message=message,
        suggested_action=ACTION_BY_CODE.get(code, AREA_DEFAULT_ACTION.get(area, "Review and decide whether to revise.")),
    )


def style_tasks(style_report: object, *, top: int) -> list[RevisionTask]:
    tasks: list[RevisionTask] = []
    for item in getattr(style_report, "aggregate_terms", [])[:top]:
        tasks.append(
            RevisionTask(
                priority="P4",
                area="style",
                source_command="audit-style",
                code="high_density_style_marker",
                chapter="-",
                path="-",
                message=f"Watched style marker `{item.item}` appears {item.count} time(s).",
                suggested_action=AREA_DEFAULT_ACTION["style"],
            )
        )
    for item in getattr(style_report, "repeated_openings", [])[:top]:
        tasks.append(
            RevisionTask(
                priority="P4",
                area="style",
                source_command="audit-style",
                code="repeated_sentence_opening",
                chapter="-",
                path="-",
                message=f"Sentence opening `{item.item}` repeats {item.count} time(s).",
                suggested_action="Vary syntax only where the repetition is not carrying deliberate rhythm.",
            )
        )
    return tasks


def word_scan_tasks(word_scan: WordScanReport, *, top: int) -> list[RevisionTask]:
    tasks: list[RevisionTask] = []
    for item in word_scan.aggregate_terms[:top]:
        tasks.append(
            RevisionTask(
                priority="P5",
                area="style",
                source_command="scan-words",
                code="high_frequency_word_scan",
                chapter="-",
                path="-",
                message=f"High-frequency term `{item.item}` appears {item.count} time(s) in the scanned manuscript.",
                suggested_action=ACTION_BY_CODE["high_frequency_word_scan"],
            )
        )
    return tasks


def table_tasks(table_report: TableCheckReport) -> list[RevisionTask]:
    tasks: list[RevisionTask] = []
    for issue in table_report.issues:
        if issue.code == "no_tables":
            continue
        tasks.append(
            RevisionTask(
                priority=issue.severity,
                area="table",
                source_command="check-tables",
                code=issue.code,
                chapter=f"line {issue.line}" if issue.line else "-",
                path=issue.path,
                message=issue.message,
                suggested_action=ACTION_BY_CODE.get(issue.code, AREA_DEFAULT_ACTION["table"]),
            )
        )
    return tasks


def sort_tasks(tasks: list[RevisionTask]) -> list[RevisionTask]:
    return sorted(
        tasks,
        key=lambda task: (
            PRIORITY_ORDER.get(task.priority, 9),
            AREA_ORDER.get(task.area, 99),
            task.source_command,
            task.chapter,
            task.path,
            task.code,
        ),
    )


def build_revision_plan(
    target: Path,
    *,
    book: str = "book_01",
    outline: str | None = None,
    all_markdown: bool = False,
    pattern: str = "**/*.md",
    metric: str = "nonspace",
    skip_standard: bool = False,
    strict_standard: bool = False,
    min_chapter_chars: int = 200,
    flat_tolerance: int = 200,
    min_spread_ratio: int = 15,
    max_flat_run: int = 4,
    max_same_band_run: int = 5,
    watch_terms: list[str] | None = None,
    top: int = 12,
    min_repeat: int = 3,
    scan_text: bool = True,
    stale_after: int = 8,
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> RevisionPlanReport:
    if not target.exists():
        raise FileNotFoundError(f"path does not exist: {target}")

    resolved = target.expanduser().resolve()
    book_id = normalize_book_for_plan(book)
    standard_enabled = strict_standard or (not skip_standard and looks_like_standard_project(resolved))
    tasks: list[RevisionTask] = []

    stats = build_stats_report(resolved, all_markdown=all_markdown, pattern=pattern, metric=metric)
    if stats.file_count == 0:
        tasks.append(
            RevisionTask(
                priority="P2",
                area="continuity",
                source_command="stats",
                code="no_chapter_files",
                chapter="-",
                path=str(resolved),
                message="No chapter files were detected.",
                suggested_action="Check the path, create chapter drafts, or use --all only for nonstandard layouts.",
            )
        )

    continuity = build_continuity_report(
        resolved,
        pattern=pattern,
        skip_standard=not standard_enabled,
        min_chapter_chars=min_chapter_chars,
    )
    tasks.extend(
        task_from_issue(issue, area="continuity", source_command="audit-continuity")
        for issue in continuity.issues
    )

    characters = build_character_audit_report(resolved, pattern=pattern)
    tasks.extend(
        task_from_issue(issue, area="character_or_plan", source_command="audit-characters")
        for issue in characters.issues
    )

    wave = build_chapter_wave_report(
        resolved,
        all_markdown=all_markdown,
        pattern=pattern,
        metric=metric,
        flat_tolerance=flat_tolerance,
        min_spread_ratio=min_spread_ratio,
        max_flat_run=max_flat_run,
        max_same_band_run=max_same_band_run,
    )
    tasks.extend(task_from_issue(issue, area="pacing", source_command="audit-wave") for issue in wave.issues)

    style = build_style_audit_report(
        resolved,
        all_markdown=all_markdown,
        pattern=pattern,
        watch_terms=watch_terms or DEFAULT_WATCH_TERMS,
        top=top,
        min_repeat=min_repeat,
    )
    tasks.extend(style_tasks(style, top=min(top, 5)))
    word_scan = build_word_scan_report(
        resolved,
        all_markdown=all_markdown,
        pattern=pattern,
        watch=",".join(watch_terms or DEFAULT_WATCH_TERMS),
        min_count=max(2, min_repeat),
        top=top,
    )
    tasks.extend(word_scan_tasks(word_scan, top=min(top, 3)))

    tables = build_table_check_report(
        resolved,
        all_markdown=True,
        pattern=pattern,
        min_filled_cells=1,
    )
    tasks.extend(table_tasks(tables))

    echoes = build_echo_report(
        resolved,
        pattern=pattern,
        table_path=None,
        scan_text=scan_text,
        stale_after=stale_after,
    )
    tasks.extend(task_from_issue(issue, area="foreshadowing", source_command="audit-echoes") for issue in echoes.issues)

    info = build_info_report(
        resolved,
        pattern=pattern,
        table_path=None,
        scan_text=scan_text,
    )
    tasks.extend(task_from_issue(issue, area="information", source_command="audit-info") for issue in info.issues)

    if resolved.is_dir():
        outline_path = resolve_outline_path(resolved, book=book_id, outline=outline)
        if outline_path.exists() or outline is not None:
            plan = build_plan_audit_report(resolved, book=book_id, outline=outline)
            tasks.extend(
                task_from_issue(issue, area="character_or_plan", source_command="audit-plan")
                for issue in plan.issues
            )

        retrospective, _section = build_retrospective_doctor_section(resolved, book=book_id)
        if retrospective is not None:
            tasks.extend(
                task_from_issue(issue, area="retrospective", source_command="retrospective")
                for issue in retrospective.issues
            )

        publish, _publish_section = build_publish_doctor_section(
            resolved,
            book=book_id,
            min_chapter_chars=min_chapter_chars,
        )
        if publish is not None:
            tasks.extend(task_from_issue(issue, area="publish", source_command="audit-publish") for issue in publish.issues)

        metadata, _metadata_section = build_metadata_doctor_section(resolved, book=book_id)
        if metadata is not None:
            tasks.extend(
                task_from_issue(issue, area="publish", source_command="export-metadata")
                for issue in metadata.issues
            )

        manifest, _manifest_section = build_manifest_doctor_section(resolved, book=book_id)
        if manifest is not None:
            tasks.extend(
                task_from_issue(issue, area="publish", source_command="export-manifest")
                for issue in manifest.issues
            )

        epub, _epub_section = build_epub_doctor_section(resolved, book=book_id)
        if epub is not None:
            tasks.extend(task_from_issue(issue, area="publish", source_command="audit-epub") for issue in epub.issues)

    tasks = sort_tasks(tasks)
    counts = Counter(task.priority for task in tasks)
    priority_counts = {key: counts.get(key, 0) for key in ["P1", "P2", "P3", "P4", "P5"]}
    status = doctor_status(priority_counts)
    output_path = resolve_revision_plan_output_path(resolved, out) if out else None
    report = RevisionPlanReport(
        target=str(resolved),
        book=book_id,
        status=status,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        task_count=len(tasks),
        priority_counts=priority_counts,
        tasks=tasks,
    )
    if output_path and not dry_run:
        write_revision_plan(output_path, render_revision_plan(report, "markdown"), force=force)
        report.written = True
    return report


def resolve_revision_plan_output_path(target: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate
    base = target if target.is_dir() else target.parent
    return (base / candidate).resolve()


def write_revision_plan(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def render_revision_plan(report: RevisionPlanReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_revision_plan(report)


def format_revision_plan(report: RevisionPlanReport) -> str:
    lines = [
        "# FictionOps Revision Plan",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Status: `{report.status}`",
        f"- Tasks: {report.task_count}",
        f"- Priority counts: P1={report.priority_counts.get('P1', 0)}, P2={report.priority_counts.get('P2', 0)}, P3={report.priority_counts.get('P3', 0)}, P4={report.priority_counts.get('P4', 0)}, P5={report.priority_counts.get('P5', 0)}",
        "",
        "## Priority Rule",
        "",
        "Fix P1/P2 structural and information-boundary issues before pacing, style, and polish.",
        "",
        "## Tasks",
        "",
    ]
    if not report.tasks:
        lines.append("No revision tasks above current thresholds.")
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "| # | Priority | Area | Source | Code | Chapter/Item | Path | Suggested Action |",
            "| ---: | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for index, task in enumerate(report.tasks, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    safe_cell(task.priority),
                    safe_cell(task.area),
                    f"`{safe_cell(task.source_command)}`",
                    f"`{safe_cell(task.code)}`",
                    safe_cell(task.chapter),
                    f"`{safe_cell(task.path)}`",
                    safe_cell(task.suggested_action),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Evidence", ""])
    for index, task in enumerate(report.tasks, start=1):
        lines.append(f"{index}. **{task.priority} {task.area}** `{task.code}`: {task.message}")
    return "\n".join(lines) + "\n"
