from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .adopt_review import build_adopt_review
from .markdown import safe_cell
from .models import AdoptPlanReport, AdoptReviewIssue, AdoptTaskGroup, RevisionTask
from .revision_plan import sort_tasks


ACTION_BY_CODE = {
    "missing_project_yml": "Initialize a clean FictionOps sandbox with `fictionops init`, then rerun `adopt --copy-to` into that sandbox.",
    "missing_standard_project_files": "Restore the standard FictionOps project-memory files before sorting imported material.",
    "placeholder_standard_project_files": "Fill or deliberately archive placeholder project-memory files so later audits do not rely on templates.",
    "no_migration_imports": "Confirm whether this is already normalized material or a fresh project rather than an adopted migration sandbox.",
    "import_queue_unsorted": "Move each imported draft-like file from `06_drafts/import_queue/` into the correct book/chapter folder, then create or sync chapter engines.",
    "missing_information_table": "Create and fill `05_canon/information_release_table.md` before drafting or reviewing secret-heavy chapters.",
    "no_information_items": "Add real information/secret rows to the information release table.",
    "missing_author_truth": "Record the author truth for this item before using it as canon.",
    "missing_reader_state": "Record what the reader knows at this manuscript point.",
    "missing_in_world_versions": "Record who knows, guesses, repeats, or officially denies this information.",
    "missing_next_release": "Plan the next release point, or mark the item intentionally dormant.",
    "missing_forbidden_note": "Record what must not be revealed early.",
    "forbidden_text_hit": "Review the text hit and mask it as rumor, partial evidence, action, or silence if needed.",
    "early_text_hit_before_release": "Move, mask, or reclassify this information so release order remains intentional.",
    "missing_character_index": "Create or restore the character index and list the active cast.",
    "no_character_index_rows": "Fill the character index with active characters and arc-file references.",
    "missing_character_arcs": "Create filled character arc files for the major active characters.",
    "placeholder_character_arc": "Replace the placeholder character arc with actual wound, desire, voice, growth, and failure-path material.",
    "missing_character_identity": "Fill identity fields so later migration work does not infer the wrong character.",
    "missing_character_start": "Record the character's starting wound, desire, fear, misunderstanding, or self-protection.",
    "missing_character_intelligence": "Record what this character sees quickly, misses, solves by, and fails by.",
    "missing_character_voice": "Record this character's voice and behavior markers before dialogue-heavy revision.",
    "missing_character_growth": "Fill the growth path with pressure, irreversible choices, and costs.",
    "missing_failure_path": "Add the tempting failure path so later growth has a visible counterforce.",
    "missing_relationship_anchors": "Add relationship anchors where this character's choices depend on them.",
    "indexed_character_missing_arc": "Create or link this character's arc file from the character index.",
    "arc_not_listed_in_index": "Add this arc file's character to the character index.",
    "missing_intelligence_profiles": "Create the intelligence profile table or ensure each arc carries its own intelligence mode.",
    "no_intelligence_profiles": "Fill the intelligence profile table or confirm intelligence modes live in individual arcs.",
    "missing_voice_profiles": "Create the voice profile table or ensure each arc carries its own voice markers.",
    "no_voice_profiles": "Fill the voice profile table or confirm voice modes live in individual arcs.",
    "character_missing_intelligence_profile": "Add this character to intelligence profiles or fill intelligence in the arc file.",
    "character_missing_voice_profile": "Add this character to voice profiles or fill voice in the arc file.",
}


AREA_BY_SOURCE = {
    "project-shape": "migration",
    "adopt-review": "migration",
    "doctor": "migration",
    "audit-info": "information",
    "audit-characters": "character_or_plan",
    "book-gate": "book_closure",
}


SOURCE_COMMAND_BY_SOURCE = {
    "project-shape": "init",
    "adopt-review": "adopt-review",
    "doctor": "doctor",
    "audit-info": "audit-info",
    "audit-characters": "audit-characters",
    "book-gate": "book-gate",
}


DEFAULT_ACTION_BY_AREA = {
    "migration": "Normalize imported files into FictionOps folders, then rerun the migration review.",
    "information": "Update information-release tables before continuing draft or review work.",
    "character_or_plan": "Update character memory before relying on migrated scenes or dialogue.",
    "book_closure": "Resolve book-level blockers before treating the migrated book as maintainable.",
}


PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4, "P5": 5}
BLOCKING_PRIORITIES = {"P0", "P1", "P2"}


MIGRATION_CODES = {
    "missing_project_yml",
    "missing_standard_project_files",
    "placeholder_standard_project_files",
    "no_migration_imports",
    "import_queue_unsorted",
}

CANON_CODES = {
    "missing_information_table",
    "no_information_items",
    "missing_author_truth",
    "missing_reader_state",
    "missing_in_world_versions",
    "missing_next_release",
    "missing_forbidden_note",
    "forbidden_text_hit",
    "early_text_hit_before_release",
    "missing_echo_table",
    "no_echo_threads",
    "missing_first_plant",
    "missing_last_echo",
    "missing_next_echo",
    "missing_payoff_direction",
    "missing_forbidden_reveal",
    "stale_last_echo",
    "no_text_hit",
}

CHARACTER_CODES = {
    "missing_character_index",
    "no_character_index_rows",
    "missing_character_arcs",
    "placeholder_character_arc",
    "missing_character_identity",
    "missing_character_start",
    "missing_character_intelligence",
    "missing_character_voice",
    "missing_character_growth",
    "missing_failure_path",
    "missing_relationship_anchors",
    "indexed_character_missing_arc",
    "arc_not_listed_in_index",
    "missing_intelligence_profiles",
    "no_intelligence_profiles",
    "missing_voice_profiles",
    "no_voice_profiles",
    "character_missing_intelligence_profile",
    "character_missing_voice_profile",
}

BOOK_STRUCTURE_CODES = {
    "missing_book_outline",
    "no_chapter_plan_rows",
    "missing_chapter_file",
    "unplanned_chapter_file",
    "missing_chapter_engine",
    "placeholder_chapter_engine",
    "engine_not_synced",
    "missing_chapter_retrospective",
    "placeholder_retrospective",
    "placeholder_chapter_retrospective",
    "placeholder_chapter",
    "missing_book_retrospective",
    "placeholder_book_retrospective",
    "open_sync_item",
    "no_chapter_files",
}

TABLE_CODES = {
    "empty_header",
    "duplicate_header",
    "empty_table",
    "row_width_mismatch",
    "mostly_empty_row",
    "no_filled_cells",
}

PACING_STYLE_CODES = {
    "too_uniform_wave",
    "flat_chapter_run",
    "same_band_run",
    "short_chapter_run",
    "heavy_chapter_run",
    "abrupt_length_jump",
    "high_frequency_word_scan",
    "high_density_style_marker",
    "repeated_sentence_opening",
}

PHASE_ORDER = {
    "01_migration_shape": 1,
    "02_canon_boundaries": 2,
    "03_character_memory": 3,
    "04_book_structure": 4,
    "05_table_hygiene": 5,
    "06_pacing_and_style": 6,
    "07_other_notes": 7,
}


def task_from_review_issue(issue: AdoptReviewIssue) -> RevisionTask:
    area = AREA_BY_SOURCE.get(issue.source, "migration")
    source_command = SOURCE_COMMAND_BY_SOURCE.get(issue.source, issue.source or "adopt-review")
    return RevisionTask(
        priority=issue.severity or "P4",
        area=area,
        source_command=source_command,
        code=issue.code or "migration_issue",
        chapter=issue.subject or "-",
        path=issue.path or "-",
        message=issue.message or "",
        suggested_action=ACTION_BY_CODE.get(issue.code, DEFAULT_ACTION_BY_AREA.get(area, "Review and decide the next migration fix.")),
    )


def priority_counts(tasks: list[RevisionTask]) -> dict[str, int]:
    counts = Counter(task.priority for task in tasks)
    return {key: counts.get(key, 0) for key in ["P1", "P2", "P3", "P4", "P5"]}


def priority_rank(priority: str) -> int:
    return PRIORITY_ORDER.get(priority, 9)


def task_blocks(task: RevisionTask) -> bool:
    return (task.priority or "P4").upper() in BLOCKING_PRIORITIES


def phase_for_task(task: RevisionTask) -> str:
    code = task.code or ""
    if code in MIGRATION_CODES or task.area == "migration":
        return "01_migration_shape"
    if code in CANON_CODES or task.area in {"information", "foreshadowing"}:
        return "02_canon_boundaries"
    if code in CHARACTER_CODES or task.area == "character_or_plan":
        return "03_character_memory"
    if code in BOOK_STRUCTURE_CODES:
        return "04_book_structure"
    if code in TABLE_CODES or task.area == "table":
        return "05_table_hygiene"
    if code in PACING_STYLE_CODES or task.area in {"pacing", "style"}:
        return "06_pacing_and_style"
    if task.area == "book_closure":
        return "04_book_structure"
    return "07_other_notes"


def unique_samples(values: list[str], *, limit: int = 3) -> list[str]:
    samples: list[str] = []
    for value in values:
        clean = value or "-"
        if clean == "-" or clean in samples:
            continue
        samples.append(clean)
        if len(samples) >= limit:
            break
    return samples


def build_task_groups(tasks: list[RevisionTask]) -> list[AdoptTaskGroup]:
    grouped: dict[tuple[str, str, str], list[RevisionTask]] = {}
    for task in tasks:
        phase = phase_for_task(task)
        key = (phase, task.code or "migration_issue", task.suggested_action or "")
        grouped.setdefault(key, []).append(task)

    groups: list[AdoptTaskGroup] = []
    for (phase, code, suggested_action), group_tasks in grouped.items():
        priorities = sorted({task.priority or "P4" for task in group_tasks}, key=priority_rank)
        groups.append(
            AdoptTaskGroup(
                phase=phase,
                priority=priorities[0] if priorities else "P4",
                code=code,
                count=len(group_tasks),
                blocking_count=sum(1 for task in group_tasks if task_blocks(task)),
                areas=sorted({task.area for task in group_tasks if task.area}),
                source_commands=sorted({task.source_command for task in group_tasks if task.source_command}),
                sample_subjects=unique_samples([task.chapter for task in group_tasks]),
                sample_paths=unique_samples([task.path for task in group_tasks]),
                suggested_action=suggested_action,
            )
        )
    return sorted(
        groups,
        key=lambda group: (
            PHASE_ORDER.get(group.phase, 99),
            priority_rank(group.priority),
            -group.blocking_count,
            -group.count,
            group.code,
        ),
    )


def resolve_adopt_plan_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (project / candidate).resolve()


def resolve_group_output_dir(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (project / candidate).resolve()


def slugify(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip().lower())
    clean = re.sub(r"_+", "_", clean).strip("_")
    return clean or "group"


def group_file_name(index: int, group: AdoptTaskGroup) -> str:
    return f"{index:02d}_{slugify(group.phase)}_{slugify(group.code)}.md"


def tasks_for_group(tasks: list[RevisionTask], group: AdoptTaskGroup) -> list[RevisionTask]:
    return [
        task
        for task in tasks
        if phase_for_task(task) == group.phase
        and (task.code or "migration_issue") == group.code
        and (task.suggested_action or "") == group.suggested_action
    ]


def write_adopt_plan(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")


def format_group_index(report: AdoptPlanReport, group_files: list[tuple[AdoptTaskGroup, Path]]) -> str:
    lines = [
        "# FictionOps Adopt Repair Groups",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Review status: `{report.review_status}`",
        f"- Groups: {len(group_files)}",
        f"- Tasks: {report.task_count}",
        "",
        "## Groups",
        "",
    ]
    if not group_files:
        lines.append("No grouped migration repair work above current thresholds.")
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "| # | Phase | Priority | Code | Count | Blocking | Workfile | Suggested Action |",
            "| ---: | --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for index, (group, path) in enumerate(group_files, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    f"`{safe_cell(group.phase)}`",
                    safe_cell(group.priority),
                    f"`{safe_cell(group.code)}`",
                    str(group.count),
                    str(group.blocking_count),
                    f"[`{safe_cell(path.name)}`]({safe_cell(path.name)})",
                    safe_cell(group.suggested_action),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def format_group_workfile(report: AdoptPlanReport, group: AdoptTaskGroup, tasks: list[RevisionTask], index: int) -> str:
    title = f"{index:02d} {group.phase} / {group.code}"
    sources = ", ".join(f"`{source}`" for source in group.source_commands) or "-"
    lines = [
        f"# {title}",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Priority: `{group.priority}`",
        f"- Count: {group.count}",
        f"- Blocking: {group.blocking_count}",
        f"- Sources: {sources}",
        "",
        "## Suggested Action",
        "",
        group.suggested_action or "Review and decide the next migration fix.",
        "",
        "## Samples",
        "",
    ]
    if group.sample_subjects:
        lines.append("- Subjects: " + ", ".join(f"`{subject}`" for subject in group.sample_subjects))
    if group.sample_paths:
        lines.append("- Paths: " + ", ".join(f"`{path}`" for path in group.sample_paths))
    if not group.sample_subjects and not group.sample_paths:
        lines.append("- No samples available.")

    lines.extend(["", "## Tasks", ""])
    if not tasks:
        lines.append("No tasks matched this repair group.")
    else:
        lines.extend(
            [
                "| Done | Priority | Area | Source | Subject | Path |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for task in tasks:
            lines.append(
                "| "
                + " | ".join(
                    [
                        "[ ]",
                        safe_cell(task.priority),
                        safe_cell(task.area),
                        f"`{safe_cell(task.source_command)}`",
                        safe_cell(task.chapter),
                        f"`{safe_cell(task.path)}`",
                    ]
                )
                + " |"
            )

    if tasks:
        lines.extend(["", "## Evidence", ""])
        for task_index, task in enumerate(tasks, start=1):
            lines.append(f"{task_index}. **{task.priority} {task.area}** `{task.code}`: {task.message}")
    return "\n".join(lines).rstrip() + "\n"


def planned_group_files(report: AdoptPlanReport, group_dir: Path) -> list[Path]:
    files = [group_dir / "index.md"]
    files.extend(group_dir / group_file_name(index, group) for index, group in enumerate(report.task_groups, start=1))
    return files


def write_group_workfiles(report: AdoptPlanReport, group_dir: Path, *, force: bool) -> list[str]:
    group_files = [(group, group_dir / group_file_name(index, group)) for index, group in enumerate(report.task_groups, start=1)]
    files = [group_dir / "index.md"] + [path for _, path in group_files]
    if not force:
        existing = [path for path in files if path.exists()]
        if existing:
            raise FileExistsError(existing[0])

    group_dir.mkdir(parents=True, exist_ok=True)
    (group_dir / "index.md").write_text(format_group_index(report, group_files), encoding="utf-8", newline="\n")
    for index, (group, path) in enumerate(group_files, start=1):
        path.write_text(format_group_workfile(report, group, tasks_for_group(report.tasks, group), index), encoding="utf-8", newline="\n")
    return [str(path) for path in files]


def build_adopt_plan(
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
    max_issues: int = 200,
    waivers: str | None = None,
    out: str | None = None,
    group_out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> AdoptPlanReport:
    resolved = project.expanduser().resolve()
    review = build_adopt_review(
        resolved,
        book=book,
        pattern=pattern,
        min_chapter_chars=min_chapter_chars,
        watch_terms=watch_terms,
        top=top,
        min_repeat=min_repeat,
        scan_text=scan_text,
        stale_after=stale_after,
        max_issues=max_issues,
        waivers=waivers,
        out=None,
        force=False,
        dry_run=True,
    )
    tasks = sort_tasks([task_from_review_issue(issue) for issue in review.issues])
    task_groups = build_task_groups(tasks)
    output_path = resolve_adopt_plan_output_path(resolved, out) if out else None
    group_output_dir = resolve_group_output_dir(resolved, group_out) if group_out else None
    report = AdoptPlanReport(
        target=str(resolved),
        book=book,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        review_status=review.status,
        review_ready=review.ready,
        task_count=len(tasks),
        priority_counts=priority_counts(tasks),
        task_groups=task_groups,
        group_output_dir=str(group_output_dir) if group_output_dir else None,
        group_files_written=0,
        group_files=[],
        tasks=tasks,
        next_actions=review.next_actions,
        adopt_review=review,
    )
    if group_output_dir:
        report.group_files = [str(path) for path in planned_group_files(report, group_output_dir)]
    if not dry_run and not force:
        if output_path and output_path.exists():
            raise FileExistsError(output_path)
        if group_output_dir:
            existing_group_files = [path for path in planned_group_files(report, group_output_dir) if path.exists()]
            if existing_group_files:
                raise FileExistsError(existing_group_files[0])
    if output_path and not dry_run:
        write_adopt_plan(output_path, render_adopt_plan(report, "markdown"), force=force)
        report.written = True
    if group_output_dir and not dry_run:
        report.group_files = write_group_workfiles(report, group_output_dir, force=force)
        report.group_files_written = len(report.group_files)
    return report


def format_adopt_plan(report: AdoptPlanReport) -> str:
    lines = [
        "# FictionOps Adopt Plan",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Review status: `{report.review_status}`",
        f"- Review ready: {'yes' if report.review_ready else 'no'}",
        f"- Tasks: {report.task_count}",
        f"- Priority counts: P1={report.priority_counts.get('P1', 0)}, P2={report.priority_counts.get('P2', 0)}, P3={report.priority_counts.get('P3', 0)}, P4={report.priority_counts.get('P4', 0)}, P5={report.priority_counts.get('P5', 0)}",
        f"- Group output dir: `{report.group_output_dir}`" if report.group_output_dir else "- Group output dir: -",
        f"- Group files written: {report.group_files_written}",
        "",
        "## Rule",
        "",
        "Fix migration-shape and import-queue tasks before normal book revision; otherwise later audits will be reading unsorted material.",
        "",
        "## Repair Groups",
        "",
    ]
    if not report.task_groups:
        lines.append("No grouped migration repair work above current thresholds.")
    else:
        lines.extend(
            [
                "| # | Phase | Priority | Code | Count | Blocking | Sources | Sample Paths | Suggested Action |",
                "| ---: | --- | --- | --- | ---: | ---: | --- | --- | --- |",
            ]
        )
        for index, group in enumerate(report.task_groups, start=1):
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        f"`{safe_cell(group.phase)}`",
                        safe_cell(group.priority),
                        f"`{safe_cell(group.code)}`",
                        str(group.count),
                        str(group.blocking_count),
                        ", ".join(f"`{safe_cell(source)}`" for source in group.source_commands) or "-",
                        "<br>".join(f"`{safe_cell(path)}`" for path in group.sample_paths) or "-",
                        safe_cell(group.suggested_action),
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Tasks",
            "",
        ]
    )
    if not report.tasks:
        lines.append("No migration tasks above current thresholds.")
    else:
        lines.extend(
            [
                "| # | Priority | Area | Source | Code | Subject | Path | Suggested Action |",
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

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")

    if report.tasks:
        lines.extend(["", "## Evidence", ""])
        for index, task in enumerate(report.tasks, start=1):
            lines.append(f"{index}. **{task.priority} {task.area}** `{task.code}`: {task.message}")

    return "\n".join(lines).rstrip() + "\n"


def render_adopt_plan(report: AdoptPlanReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_adopt_plan(report)
