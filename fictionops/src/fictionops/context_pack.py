from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .markdown import display_path, safe_cell
from .models import ContextPackFile, ContextPackIssue, ContextPackReport
from .new_chapter import chapter_paths, normalize_chapter_number
from .plan_chapter import normalize_book_for_plan


CONTEXT_TASKS = ["draft", "review", "handoff", "canon-sync"]


@dataclass
class ContextSpec:
    role: str
    path: Path
    required: bool


def previous_chapter_number(chapter: str) -> str | None:
    number = int(chapter)
    if number <= 1:
        return None
    return f"{number - 1:03d}"


def next_chapter_number(chapter: str) -> str:
    return f"{int(chapter) + 1:03d}"


def add_file(specs: list[ContextSpec], project: Path, role: str, relative: str, *, required: bool) -> None:
    specs.append(ContextSpec(role=role, path=project / relative, required=required))


def add_glob(
    specs: list[ContextSpec],
    project: Path,
    role: str,
    relative_dir: str,
    pattern: str = "*.md",
    *,
    required: bool,
) -> None:
    directory = project / relative_dir
    matches = sorted(directory.glob(pattern)) if directory.exists() else []
    if matches:
        for path in matches:
            if path.is_file():
                specs.append(ContextSpec(role=role, path=path, required=required))
        return
    if required:
        specs.append(ContextSpec(role=role, path=directory / pattern, required=True))


def chapter_file_specs(project: Path, *, book: str, chapter: str, role: str, required: bool) -> list[ContextSpec]:
    paths = chapter_paths(project, book=book, chapter_number=chapter)
    return [ContextSpec(role=role, path=paths["chapter"], required=required)]


def chapter_engine_spec(project: Path, *, book: str, chapter: str, required: bool = True) -> ContextSpec:
    paths = chapter_paths(project, book=book, chapter_number=chapter)
    return ContextSpec(role="chapter engine", path=paths["engine"], required=required)


def chapter_retrospective_spec(project: Path, *, book: str, chapter: str, required: bool) -> ContextSpec:
    paths = chapter_paths(project, book=book, chapter_number=chapter)
    return ContextSpec(role="chapter retrospective", path=paths["retrospective"], required=required)


def common_project_specs(project: Path, specs: list[ContextSpec]) -> None:
    add_file(specs, project, "project config", "project.yml", required=False)
    add_file(specs, project, "current context", "00_management/current_context.md", required=False)
    add_file(specs, project, "story seed", "01_story_seed/story_seed.md", required=False)


def build_context_specs(project: Path, *, task: str, book: str, chapter: str | None) -> list[ContextSpec]:
    specs: list[ContextSpec] = []
    common_project_specs(project, specs)

    book_outline = f"04_structure/book_outlines/{book}_outline.md"
    info_table = "05_canon/information_release_table.md"
    echo_table = "05_canon/foreshadowing_echo_table.md"

    if task == "draft":
        assert chapter is not None
        add_file(specs, project, "book outline", book_outline, required=True)
        specs.append(chapter_engine_spec(project, book=book, chapter=chapter))
        add_file(specs, project, "information boundary", info_table, required=True)
        add_file(specs, project, "foreshadowing echoes", echo_table, required=False)
        add_file(specs, project, "regional voices", "02_world/regional_voices.md", required=False)
        add_file(specs, project, "voice profiles", "03_characters/voice_profiles.md", required=False)
        add_file(specs, project, "intelligence profiles", "03_characters/intelligence_profiles.md", required=False)
        add_glob(specs, project, "character arc", "03_characters/character_arcs", required=False)
        previous = previous_chapter_number(chapter)
        if previous:
            specs.extend(chapter_file_specs(project, book=book, chapter=previous, role="previous chapter", required=True))
            specs.append(chapter_retrospective_spec(project, book=book, chapter=previous, required=False))

    elif task == "review":
        assert chapter is not None
        specs.extend(chapter_file_specs(project, book=book, chapter=chapter, role="chapter under review", required=True))
        specs.append(chapter_engine_spec(project, book=book, chapter=chapter))
        previous = previous_chapter_number(chapter)
        if previous:
            specs.extend(chapter_file_specs(project, book=book, chapter=previous, role="previous chapter", required=False))
        specs.extend(chapter_file_specs(project, book=book, chapter=next_chapter_number(chapter), role="next chapter", required=False))
        add_file(specs, project, "information boundary", info_table, required=True)
        add_file(specs, project, "foreshadowing echoes", echo_table, required=False)
        add_file(specs, project, "voice profiles", "03_characters/voice_profiles.md", required=False)
        add_file(specs, project, "intelligence profiles", "03_characters/intelligence_profiles.md", required=False)
        add_glob(specs, project, "character arc", "03_characters/character_arcs", required=False)

    elif task == "handoff":
        add_file(specs, project, "handoff log", "00_management/handoff_log.md", required=True)
        add_file(specs, project, "decision log", "00_management/decision_log.md", required=True)
        add_file(specs, project, "model config", "00_management/model_config.json", required=False)
        add_file(specs, project, "workflow", "00_management/workflow.md", required=False)
        add_file(specs, project, "series outline", "04_structure/series_outline.md", required=False)
        add_file(specs, project, "book outline", book_outline, required=True)
        add_file(specs, project, "information boundary", info_table, required=True)
        add_file(specs, project, "foreshadowing echoes", echo_table, required=True)
        add_file(specs, project, "character index", "03_characters/character_index.md", required=False)
        add_file(specs, project, "intelligence profiles", "03_characters/intelligence_profiles.md", required=False)
        add_file(specs, project, "voice profiles", "03_characters/voice_profiles.md", required=False)
        add_file(specs, project, "object locations", "05_canon/object_locations.md", required=False)
        add_file(specs, project, "open questions", "05_canon/open_questions.md", required=False)
        add_file(specs, project, "latest doctor report", "07_audits/doctor_report.md", required=False)
        add_file(specs, project, "revision plan", "07_audits/revision_plan.md", required=False)
        add_file(specs, project, "book gate report", f"07_audits/book_gate/{book}_gate.md", required=False)
        add_file(specs, project, "release gate report", f"07_audits/release_gate/{book}_release_gate.md", required=False)
        add_glob(specs, project, "book retrospective", "07_audits/book_retrospectives", required=False)

    elif task == "canon-sync":
        add_file(specs, project, "decision log", "00_management/decision_log.md", required=True)
        add_file(specs, project, "timeline", "04_structure/timeline.md", required=False)
        add_file(specs, project, "information boundary", info_table, required=True)
        add_file(specs, project, "foreshadowing echoes", echo_table, required=True)
        add_file(specs, project, "object locations", "05_canon/object_locations.md", required=False)
        add_file(specs, project, "open questions", "05_canon/open_questions.md", required=False)
        add_file(specs, project, "resolved questions", "05_canon/resolved_questions.md", required=False)
        if chapter is not None:
            specs.extend(chapter_file_specs(project, book=book, chapter=chapter, role="source chapter", required=True))
            specs.append(chapter_retrospective_spec(project, book=book, chapter=chapter, required=False))

    return merge_context_specs(specs)


def merge_context_specs(specs: list[ContextSpec]) -> list[ContextSpec]:
    merged: dict[Path, ContextSpec] = {}
    for spec in specs:
        key = spec.path
        existing = merged.get(key)
        if existing is None:
            merged[key] = spec
            continue
        roles = existing.role.split(" / ")
        if spec.role not in roles:
            roles.append(spec.role)
        existing.role = " / ".join(roles)
        existing.required = existing.required or spec.required
    return list(merged.values())


def checklist_for_task(task: str) -> list[str]:
    if task == "draft":
        return [
            "本章视角人物现在想要什么？",
            "本章压力从哪里来？",
            "本章有什么不能说？",
            "本章结尾改变什么？",
            "本章应留下什么余味？",
        ]
    if task == "review":
        return [
            "先查正史，再查信息边界。",
            "再查人物弧线和章节发动机是否兑现。",
            "最后看风格、解释密度和读者体验。",
        ]
    if task == "canon-sync":
        return [
            "这是正文改出了新正史，还是正文误写？",
            "哪些文件需要同步？",
            "哪些旧设定需要归档？",
            "这次改动会影响后续哪些章节？",
        ]
    return [
        "当前状态是什么？",
        "已经完成什么？",
        "下一步是什么？",
        "风险在哪里？",
        "新接手者必须先读哪些文件？",
    ]


def read_context_file(path: Path, *, base: Path, spec: ContextSpec, include_content: bool, max_chars: int) -> ContextPackFile:
    exists = path.exists() and path.is_file()
    text = path.read_text(encoding="utf-8") if exists else ""
    nonspace = sum(1 for char in text if not char.isspace())
    content = ""
    truncated = False
    included_chars = 0
    if include_content and exists:
        limit = max(0, max_chars)
        source_content = text[:limit]
        included_chars = len(source_content)
        truncated = len(text) > limit
        if limit > 0:
            content = source_content
            if truncated:
                content = content.rstrip() + "\n\n...[truncated]"
    return ContextPackFile(
        role=spec.role,
        path=display_path(path, base),
        required=spec.required,
        exists=exists,
        chars=len(text),
        nonspace_chars=nonspace,
        included_chars=included_chars,
        truncated=truncated,
        content=content,
    )


def build_context_pack(
    project: Path,
    *,
    task: str,
    book: str = "book_01",
    chapter: str | None = None,
    include_content: bool = True,
    max_chars_per_file: int = 6000,
    max_total_chars: int = 60000,
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> ContextPackReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"context-pack requires a FictionOps project directory: {project}")
    if task not in CONTEXT_TASKS:
        raise ValueError(f"unsupported context-pack task: {task}")
    if max_chars_per_file < 0:
        raise ValueError("context-pack --max-chars-per-file must be >= 0")
    if max_total_chars < 0:
        raise ValueError("context-pack --max-total-chars must be >= 0")

    book_id = normalize_book_for_plan(book)
    chapter_number = normalize_chapter_number(chapter) if chapter else None
    if task in {"draft", "review"} and chapter_number is None:
        raise ValueError(f"context-pack --task {task} requires --chapter")

    specs = build_context_specs(project, task=task, book=book_id, chapter=chapter_number)
    files: list[ContextPackFile] = []
    remaining_chars = max_total_chars if include_content else 0
    for spec in specs:
        file_limit = min(max_chars_per_file, remaining_chars) if include_content else max_chars_per_file
        item = read_context_file(
            spec.path,
            base=project,
            spec=spec,
            include_content=include_content,
            max_chars=file_limit,
        )
        files.append(item)
        if include_content:
            remaining_chars = max(0, remaining_chars - item.included_chars)
    included_total_chars = sum(item.included_chars for item in files)
    issues = [
        ContextPackIssue(
            severity="P2",
            code="missing_required_context",
            path=item.path,
            message=f"Required context file is missing for {task}: {item.role}.",
        )
        for item in files
        if item.required and not item.exists
    ]

    output_path = resolve_context_pack_output_path(project, out) if out else None
    report = ContextPackReport(
        target=str(project),
        task=task,
        book=book_id,
        chapter=chapter_number,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        include_content=include_content,
        max_chars_per_file=max_chars_per_file,
        max_total_chars=max_total_chars,
        included_total_chars=included_total_chars,
        files=files,
        issues=issues,
        checklist=checklist_for_task(task),
    )
    if output_path and not dry_run:
        write_context_pack(output_path, render_context_pack(report, "markdown"), force=force)
        report.written = True
    return report


def resolve_context_pack_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate
    return (project / candidate).resolve()


def write_context_pack(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def render_context_pack(report: ContextPackReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_context_pack(report)


def format_context_pack(report: ContextPackReport) -> str:
    lines = [
        "# FictionOps Context Pack",
        "",
        f"- Task: {report.task}",
        f"- Book: {report.book}",
        f"- Chapter: {report.chapter or '-'}",
        f"- Include content: {str(report.include_content).lower()}",
        f"- Max chars per file: {report.max_chars_per_file}",
        f"- Max total chars: {report.max_total_chars}",
        f"- Included total chars: {report.included_total_chars}",
        "",
        "## Checklist",
        "",
    ]
    for item in report.checklist:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Files",
            "",
            "| Role | Required | Exists | Chars | Included | Truncated | Path |",
            "| --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for item in report.files:
        lines.append(
            f"| {safe_cell(item.role)} | {'yes' if item.required else 'no'} | "
            f"{'yes' if item.exists else 'no'} | {item.chars} | {item.included_chars} | "
            f"{'yes' if item.truncated else 'no'} | {safe_cell(item.path)} |"
        )

    if report.issues:
        lines.extend(["", "## Issues", ""])
        for issue in report.issues:
            lines.append(f"- {issue.severity} `{issue.code}` {issue.path}: {issue.message}")

    if report.include_content:
        lines.extend(["", "## Content", ""])
        for item in report.files:
            if not item.exists:
                continue
            lines.extend(
                [
                    f"### {item.role}: {item.path}",
                    "",
                    "```markdown",
                    item.content.rstrip(),
                    "```",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"
