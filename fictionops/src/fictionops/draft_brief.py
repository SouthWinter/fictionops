from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .context_pack import build_context_pack
from .markdown import safe_cell
from .models import (
    ContextPackFile,
    DraftBriefIssue,
    DraftBriefReport,
    DraftBriefSceneTask,
)
from .new_chapter import normalize_chapter_number
from .plan_chapter import normalize_book_for_plan
from .scene_plan import build_scene_plan, render_scene_plan


def draft_brief_must_do() -> list[str]:
    return [
        "严格限制在视角人物可知、可误读、可感到的范围内。",
        "先写场景中的身体、动作、物件、对话和沉默，再考虑解释。",
        "每个场景都要推进压力、欲望、阻碍、变化或余味中的至少一项。",
        "保留章节发动机里的留白要求，不用旁白替读者想完。",
        "写完后记录需要同步到复盘、正史、信息表或伏笔表的事项。",
    ]


def draft_brief_must_not() -> list[str]:
    return [
        "不要因为上下文缺失就补造正史或人物动机。",
        "不要让角色知道信息释放表里当前不该知道的作者真相。",
        "不要把场景写成设定说明、计划复述或作者辩解。",
        "不要把所有聪明人写成同一种推理方式。",
        "不要为了凑字数重复解释已经由行动表达过的内容。",
    ]


def make_scene_tasks(scene_plan) -> list[DraftBriefSceneTask]:
    tasks: list[DraftBriefSceneTask] = []
    for scene in scene_plan.scenes:
        guardrails = list(scene.info_boundary)
        if scene.foreshadowing:
            guardrails.extend(f"伏笔轻触：{item}" for item in scene.foreshadowing)
        tasks.append(
            DraftBriefSceneTask(
                order=scene.order,
                title=scene.title,
                function=scene.function,
                writing_goal=scene.focus,
                pressure=scene.pressure,
                desire=scene.desire,
                obstacle=scene.obstacle,
                guardrails=guardrails,
                exit_check=scene.exit_check,
            )
        )
    return tasks


def flatten_issues(scene_plan, context_pack) -> list[DraftBriefIssue]:
    issues: list[DraftBriefIssue] = []
    for issue in scene_plan.issues:
        issues.append(
            DraftBriefIssue(
                severity=issue.severity,
                source="scene-plan",
                code=issue.code,
                field=issue.field,
                message=issue.message,
            )
        )
    for issue in context_pack.issues:
        issues.append(
            DraftBriefIssue(
                severity=issue.severity,
                source="context-pack",
                code=issue.code,
                field=issue.path,
                message=issue.message,
            )
        )
    return issues


def premise_checks(scene_plan, context_pack, issues: list[DraftBriefIssue]) -> list[str]:
    checks = [
        f"场景数：{scene_plan.scene_count}。",
        f"视角人物：{scene_plan.viewpoint or '未填写'}。",
        f"章节性质：{scene_plan.kind or '未填写'}。",
    ]
    missing_engine_fields = [issue.field for issue in issues if issue.source == "scene-plan" and issue.code == "missing_engine_field"]
    if missing_engine_fields:
        checks.append("五列发动机缺字段：" + "、".join(missing_engine_fields) + "。")
    else:
        checks.append("五列发动机已填写，可进入场景执行。")

    missing_context = [issue.field for issue in issues if issue.source == "context-pack" and issue.code == "missing_required_context"]
    if missing_context:
        checks.append(f"缺少必需上下文 {len(missing_context)} 项，写作前应补齐或明确人工豁免。")
    else:
        checks.append("必需上下文齐备或没有阻断项。")

    if scene_plan.blank_requirements:
        checks.append("留白要求已带入 brief，正文不应主动解释完。")
    if scene_plan.information_boundaries:
        checks.append("信息边界已带入 brief，写作时按角色认知处理。")
    if scene_plan.foreshadowing_threads:
        checks.append("伏笔回声已带入 brief，优先轻触而非解释。")
    return checks


def resolve_draft_brief_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate
    return (project / candidate).resolve()


def write_draft_brief(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_draft_brief(
    project: Path,
    *,
    book: str = "book_01",
    chapter: str,
    engine: str | None = None,
    include_context_content: bool = False,
    max_chars_per_file: int = 6000,
    max_total_context_chars: int = 60000,
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> DraftBriefReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"draft-brief requires a FictionOps project directory: {project}")

    book_id = normalize_book_for_plan(book)
    chapter_number = normalize_chapter_number(chapter)
    scene_plan = build_scene_plan(
        project,
        book=book_id,
        chapter=chapter_number,
        engine=engine,
        out=None,
        force=False,
        dry_run=True,
    )
    context_pack = build_context_pack(
        project,
        task="draft",
        book=book_id,
        chapter=chapter_number,
        include_content=include_context_content,
        max_chars_per_file=max_chars_per_file,
        max_total_chars=max_total_context_chars,
        out=None,
        force=False,
        dry_run=True,
    )
    issues = flatten_issues(scene_plan, context_pack)
    missing_required_context_count = sum(1 for item in context_pack.files if item.required and not item.exists)
    output_path = resolve_draft_brief_output_path(project, out) if out else None
    report = DraftBriefReport(
        target=str(project.expanduser().resolve()),
        book=book_id,
        chapter=chapter_number,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        include_context_content=include_context_content,
        max_chars_per_file=max_chars_per_file,
        max_total_context_chars=max_total_context_chars,
        title=scene_plan.title,
        viewpoint=scene_plan.viewpoint,
        kind=scene_plan.kind,
        target_chars=scene_plan.target_chars,
        source_engine=scene_plan.engine_file,
        scene_count=scene_plan.scene_count,
        context_file_count=len(context_pack.files),
        missing_required_context_count=missing_required_context_count,
        issue_count=len(issues),
        premise_checks=premise_checks(scene_plan, context_pack, issues),
        must_do=draft_brief_must_do(),
        must_not=draft_brief_must_not(),
        scene_tasks=make_scene_tasks(scene_plan),
        scene_plan=scene_plan,
        context_pack=context_pack,
        issues=issues,
    )
    if output_path and not dry_run:
        write_draft_brief(output_path, render_draft_brief(report, "markdown"), force=force)
        report.written = True
    return report


def render_draft_brief(report: DraftBriefReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_draft_brief(report)


def format_context_files(files: list[ContextPackFile]) -> list[str]:
    lines = [
        "| Role | Required | Exists | Chars | Included | Truncated | Path |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for item in files:
        lines.append(
            f"| {safe_cell(item.role)} | {'yes' if item.required else 'no'} | "
            f"{'yes' if item.exists else 'no'} | {item.chars} | {item.included_chars} | "
            f"{'yes' if item.truncated else 'no'} | {safe_cell(item.path)} |"
        )
    return lines


def format_draft_brief(report: DraftBriefReport) -> str:
    lines = [
        "# FictionOps Draft Brief",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter}`",
        f"- Engine: `{report.source_engine}`",
        f"- Title: {report.title or '-'}",
        f"- Viewpoint: {report.viewpoint or '-'}",
        f"- Kind: {report.kind or '-'}",
        f"- Target chars: {report.target_chars or '-'}",
        f"- Scenes: {report.scene_count}",
        f"- Context files: {report.context_file_count}",
        f"- Missing required context: {report.missing_required_context_count}",
        f"- Max total context chars: {report.max_total_context_chars}",
        f"- Included context chars: {report.context_pack.included_total_chars}",
        "",
        "## Before Drafting Checks",
        "",
    ]
    for item in report.premise_checks:
        lines.append(f"- {item}")

    lines.extend(["", "## Must Do", ""])
    for item in report.must_do:
        lines.append(f"- {item}")

    lines.extend(["", "## Must Not", ""])
    for item in report.must_not:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Scene Tasks",
            "",
            "| # | Function | Scene | Writing Goal | Guardrails | Exit Check |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for task in report.scene_tasks:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(task.order),
                    safe_cell(task.function),
                    safe_cell(task.title),
                    safe_cell(task.writing_goal),
                    safe_cell("<br>".join(task.guardrails)),
                    safe_cell(task.exit_check),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Context Files", "", *format_context_files(report.context_pack.files)])

    if report.issues:
        lines.extend(["", "## Issues", "", "| Severity | Source | Code | Field | Message |", "| --- | --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(issue.severity),
                        safe_cell(issue.source),
                        f"`{safe_cell(issue.code)}`",
                        safe_cell(issue.field),
                        safe_cell(issue.message),
                    ]
                )
                + " |"
            )

    if report.include_context_content:
        lines.extend(["", "## Context Content", ""])
        for item in report.context_pack.files:
            if not item.exists or not item.content:
                continue
            lines.extend(
                [
                    f"### {item.role}: `{item.path}`",
                    "",
                    "```markdown",
                    item.content.rstrip(),
                    "```",
                    "",
                ]
            )

    lines.extend(["", "## Source Scene Plan", "", render_scene_plan(report.scene_plan, "markdown").rstrip()])
    return "\n".join(lines).rstrip() + "\n"
