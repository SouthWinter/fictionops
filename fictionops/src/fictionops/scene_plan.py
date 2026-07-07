from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .echo_audit import blankish, cell_at, header_index, is_markdown_separator, split_markdown_row
from .markdown import safe_cell
from .models import ScenePlanIssue, ScenePlanReport, ScenePlanScene
from .new_chapter import chapter_paths, normalize_chapter_number
from .plan_chapter import (
    CHANGE_HEADERS,
    DESIRE_HEADERS,
    OBSTACLE_HEADERS,
    PRESSURE_HEADERS,
    REMAINDER_HEADERS,
    normalize_book_for_plan,
)


SECTION_RE = re.compile(r"^#{1,6}\s+")

INFO_HEADERS = {
    "info": ["信息", "info", "secret", "event"],
    "knows": ["谁知道", "knows", "character knows"],
    "unknown": ["谁不知道", "unknown", "does not know"],
    "can_say": ["本章能否说出口", "能否说出口", "can say", "can reveal"],
    "forbidden": ["写作禁区", "禁区", "forbidden", "do not reveal"],
}

ECHO_HEADERS = {
    "thread": ["线程", "thread", "伏笔", "foreshadowing"],
    "handling": ["本章处理方式", "处理方式", "handling", "mode"],
    "form": ["形式", "form"],
}

LINE_FIELDS = {
    "title": ["- 标题：", "- 标题:", "- title:", "- Title:"],
    "viewpoint": ["- 视角人物：", "- 视角人物:", "- viewpoint:", "- pov:"],
    "kind": ["- 章节性质：", "- 章节性质:", "- kind:", "- type:"],
    "target_chars": ["- 建议体量：", "- 建议体量:", "- target chars:", "- target:"],
}

CONTINUITY_FIELDS = {
    "上一章留下的压力": ["- 上一章留下的压力：", "- 上一章留下的压力:"],
    "视角人物上次出场时的状态": ["- 视角人物上次出场时的状态：", "- 视角人物上次出场时的状态:"],
    "身体伤病/疲惫": ["- 身体伤病/疲惫：", "- 身体伤病/疲惫:"],
    "关系状态": ["- 关系状态：", "- 关系状态:"],
    "物件位置": ["- 物件位置：", "- 物件位置:"],
    "时间与地点": ["- 时间与地点：", "- 时间与地点:"],
}

BLANK_FIELDS = {
    "哪些动机不解释": ["- 哪些动机不解释：", "- 哪些动机不解释:"],
    "哪些规则只让读者感到": ["- 哪些规则只让读者感到：", "- 哪些规则只让读者感到:"],
    "哪些话不说完": ["- 哪些话不说完：", "- 哪些话不说完:"],
    "哪个场景应在解释完成前结束": ["- 哪个场景应在解释完成前结束：", "- 哪个场景应在解释完成前结束:"],
}

STYLE_FIELDS = {
    "避免的高频词/句式": ["- 避免的高频词/句式：", "- 避免的高频词/句式:"],
    "开头方式": ["- 开头方式：", "- 开头方式:"],
    "结尾方式": ["- 结尾方式：", "- 结尾方式:"],
    "本章语言应更偏": ["- 本章语言应更偏：", "- 本章语言应更偏:"],
}


def line_value(lines: list[str], markers: list[str]) -> str:
    lowered_markers = [marker.lower() for marker in markers]
    for line in lines:
        stripped = line.strip()
        lowered = stripped.lower()
        for marker, lowered_marker in zip(markers, lowered_markers):
            if lowered.startswith(lowered_marker):
                return stripped[len(marker) :].strip()
    return ""


def field_map(lines: list[str], fields: dict[str, list[str]]) -> dict[str, str]:
    return {name: line_value(lines, markers) for name, markers in fields.items()}


def section_lines(lines: list[str], heading_pattern: str) -> list[str]:
    start: int | None = None
    pattern = re.compile(heading_pattern, flags=re.IGNORECASE)
    for index, line in enumerate(lines):
        if SECTION_RE.match(line) and pattern.search(line):
            start = index + 1
            break
    if start is None:
        return []
    end = len(lines)
    for index in range(start, len(lines)):
        if SECTION_RE.match(lines[index]):
            end = index
            break
    return lines[start:end]


def first_table_rows(lines: list[str]) -> tuple[list[str], list[list[str]], int]:
    index = 0
    while index < len(lines) - 1:
        if "|" not in lines[index] or "|" not in lines[index + 1]:
            index += 1
            continue
        headers = split_markdown_row(lines[index])
        separator = split_markdown_row(lines[index + 1])
        if not is_markdown_separator(separator):
            index += 1
            continue
        rows: list[list[str]] = []
        row_index = index + 2
        while row_index < len(lines) and "|" in lines[row_index]:
            row = split_markdown_row(lines[row_index])
            if not is_markdown_separator(row):
                rows.append(row)
            row_index += 1
        return headers, rows, index + 1
    return [], [], 0


def parse_engine_row(lines: list[str]) -> dict[str, str]:
    headers, rows, _row_number = first_table_rows(section_lines(lines, r"五列发动机"))
    if not headers:
        return {"pressure": "", "desire": "", "obstacle": "", "change": "", "remainder": ""}
    row = rows[0] if rows else []

    def value(candidates: list[str]) -> str:
        return cell_at(row, header_index(headers, candidates))

    return {
        "pressure": value(PRESSURE_HEADERS),
        "desire": value(DESIRE_HEADERS),
        "obstacle": value(OBSTACLE_HEADERS),
        "change": value(CHANGE_HEADERS),
        "remainder": value(REMAINDER_HEADERS),
    }


def parse_named_table(lines: list[str], heading_pattern: str, columns: dict[str, list[str]]) -> list[dict[str, str]]:
    headers, rows, _row_number = first_table_rows(section_lines(lines, heading_pattern))
    if not headers:
        return []
    parsed: list[dict[str, str]] = []
    for row in rows:
        item = {name: cell_at(row, header_index(headers, candidates)) for name, candidates in columns.items()}
        if any(not blankish(value) for value in item.values()):
            parsed.append(item)
    return parsed


def parse_scene_order(lines: list[str]) -> list[str]:
    values: list[str] = []
    for line in section_lines(lines, r"场景顺序"):
        match = re.match(r"^\s*\d+[.)、]\s*(.*)$", line)
        if not match:
            continue
        value = match.group(1).strip()
        if not blankish(value):
            values.append(value)
    return values


def short_join(values: list[str], *, field: str) -> list[str]:
    result: list[str] = []
    for value in values:
        if not blankish(value):
            result.append(value)
    return result[:3] if result else [f"保持 {field} 的留白，避免提前解释。"]


def default_scene_titles(*, pressure: str, desire: str, obstacle: str, change: str, remainder: str) -> list[str]:
    return [
        pressure or "让上一章压力进入现场",
        desire or "让视角人物主动追求当下目标",
        obstacle or "让阻碍逼近并制造代价",
        change or "完成不可回退变化",
        remainder or "留下余味和下一章压力",
    ]


def scene_function(index: int, total: int) -> str:
    if index == 1:
        return "opening pressure"
    if index == total:
        return "change and residue"
    if index == 2:
        return "desire meets resistance"
    if index == total - 1:
        return "choice under cost"
    return "escalation"


def build_scenes(
    titles: list[str],
    *,
    viewpoint: str,
    pressure: str,
    desire: str,
    obstacle: str,
    change: str,
    remainder: str,
    info_items: list[dict[str, str]],
    echo_items: list[dict[str, str]],
) -> list[ScenePlanScene]:
    total = len(titles)
    info_boundary = short_join(
        [
            f"{item.get('info', '')}: {item.get('can_say', '') or item.get('forbidden', '')}"
            for item in info_items
        ],
        field="information",
    )
    echoes = short_join(
        [
            f"{item.get('thread', '')}: {item.get('handling', '') or item.get('form', '')}"
            for item in echo_items
        ],
        field="foreshadowing",
    )
    scenes: list[ScenePlanScene] = []
    for index, title in enumerate(titles, start=1):
        function = scene_function(index, total)
        if index == 1:
            focus = f"让{viewpoint or '视角人物'}在具体场景里感到压力，而不是解释压力。"
            exit_check = "读者能感到局势变紧，但不需要立刻知道全部原因。"
        elif index == total:
            focus = "让变化落地，并保留余味、沉默或未说完的话。"
            exit_check = "场景结束时，局势已经改变，仍有东西不能被解释完。"
        else:
            focus = "让人物带着欲望行动，并让阻碍改变其可选项。"
            exit_check = "本场推进了选择成本，而不是只补充信息。"
        scenes.append(
            ScenePlanScene(
                order=index,
                title=title,
                function=function,
                focus=focus,
                pressure=pressure,
                desire=desire,
                obstacle=obstacle,
                change=change if index == total else "",
                remainder=remainder if index == total else "",
                info_boundary=info_boundary,
                foreshadowing=echoes,
                exit_check=exit_check,
            )
        )
    return scenes


def scene_plan_issues(
    *,
    engine_file: Path,
    pressure: str,
    desire: str,
    obstacle: str,
    change: str,
    remainder: str,
    scene_titles: list[str],
) -> list[ScenePlanIssue]:
    issues: list[ScenePlanIssue] = []
    fields = {
        "pressure": pressure,
        "desire": desire,
        "obstacle": obstacle,
        "change": change,
        "remainder": remainder,
    }
    for field_name, value in fields.items():
        if blankish(value):
            issues.append(
                ScenePlanIssue(
                    severity="P2",
                    code="missing_engine_field",
                    field=field_name,
                    message=f"Chapter engine is missing {field_name}; scene skeleton will be generic.",
                )
            )
    if not scene_titles:
        issues.append(
            ScenePlanIssue(
                severity="P3",
                code="generated_scene_order",
                field="scene_order",
                message=f"No filled scene order was found in {engine_file}; FictionOps generated a default skeleton.",
            )
        )
    return issues


def resolve_engine_path(project: Path, *, book: str, chapter: str, engine: str | None) -> Path:
    if engine:
        candidate = Path(engine).expanduser()
        if candidate.is_absolute():
            return candidate.resolve()
        return (project / candidate).resolve()
    return chapter_paths(project, book=book, chapter_number=chapter)["engine"].resolve()


def resolve_scene_plan_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate
    return (project / candidate).resolve()


def write_scene_plan(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_scene_plan(
    project: Path,
    *,
    book: str = "book_01",
    chapter: str,
    engine: str | None = None,
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> ScenePlanReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"scene-plan requires a FictionOps project directory: {project}")

    book_id = normalize_book_for_plan(book)
    chapter_number = normalize_chapter_number(chapter)
    engine_path = resolve_engine_path(project, book=book_id, chapter=chapter_number, engine=engine)
    if not engine_path.exists():
        raise FileNotFoundError(f"chapter engine not found: {engine_path}. Run new-chapter or plan-chapter first.")

    lines = engine_path.read_text(encoding="utf-8").splitlines()
    info = field_map(lines, LINE_FIELDS)
    engine_row = parse_engine_row(lines)
    continuity = field_map(lines, CONTINUITY_FIELDS)
    information_boundaries = parse_named_table(lines, r"信息边界", INFO_HEADERS)
    foreshadowing_threads = parse_named_table(lines, r"伏笔|回声", ECHO_HEADERS)
    blank_requirements = field_map(lines, BLANK_FIELDS)
    style_reminders = field_map(lines, STYLE_FIELDS)
    filled_scene_titles = parse_scene_order(lines)
    scene_titles = filled_scene_titles or default_scene_titles(**engine_row)
    scenes = build_scenes(
        scene_titles,
        viewpoint=info["viewpoint"],
        pressure=engine_row["pressure"],
        desire=engine_row["desire"],
        obstacle=engine_row["obstacle"],
        change=engine_row["change"],
        remainder=engine_row["remainder"],
        info_items=information_boundaries,
        echo_items=foreshadowing_threads,
    )
    issues = scene_plan_issues(
        engine_file=engine_path,
        pressure=engine_row["pressure"],
        desire=engine_row["desire"],
        obstacle=engine_row["obstacle"],
        change=engine_row["change"],
        remainder=engine_row["remainder"],
        scene_titles=filled_scene_titles,
    )

    output_path = resolve_scene_plan_output_path(project, out) if out else None
    report = ScenePlanReport(
        target=str(project.expanduser().resolve()),
        book=book_id,
        chapter=chapter_number,
        engine_file=str(engine_path),
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        title=info["title"],
        viewpoint=info["viewpoint"],
        kind=info["kind"],
        target_chars=info["target_chars"],
        pressure=engine_row["pressure"],
        desire=engine_row["desire"],
        obstacle=engine_row["obstacle"],
        change=engine_row["change"],
        remainder=engine_row["remainder"],
        scene_count=len(scenes),
        scenes=scenes,
        continuity=continuity,
        information_boundaries=information_boundaries,
        foreshadowing_threads=foreshadowing_threads,
        blank_requirements=blank_requirements,
        style_reminders=style_reminders,
        issues=issues,
    )
    if output_path and not dry_run:
        write_scene_plan(output_path, render_scene_plan(report, "markdown"), force=force)
        report.written = True
    return report


def render_scene_plan(report: ScenePlanReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_scene_plan(report)


def format_dict_lines(items: dict[str, str]) -> list[str]:
    return [f"- {key}: {value or '-'}" for key, value in items.items()]


def format_scene_plan(report: ScenePlanReport) -> str:
    lines = [
        "# FictionOps Scene Plan",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter}`",
        f"- Engine: `{report.engine_file}`",
        f"- Title: {report.title or '-'}",
        f"- Viewpoint: {report.viewpoint or '-'}",
        f"- Kind: {report.kind or '-'}",
        f"- Target chars: {report.target_chars or '-'}",
        "",
        "## Engine",
        "",
        f"- Pressure: {report.pressure or '-'}",
        f"- Desire: {report.desire or '-'}",
        f"- Obstacle: {report.obstacle or '-'}",
        f"- Change: {report.change or '-'}",
        f"- Remainder: {report.remainder or '-'}",
        "",
        "## Continuity",
        "",
        *format_dict_lines(report.continuity),
        "",
        "## Scenes",
        "",
        "| # | Function | Title | Focus | Info Boundary | Foreshadowing | Exit Check |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for scene in report.scenes:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(scene.order),
                    safe_cell(scene.function),
                    safe_cell(scene.title),
                    safe_cell(scene.focus),
                    safe_cell("<br>".join(scene.info_boundary)),
                    safe_cell("<br>".join(scene.foreshadowing)),
                    safe_cell(scene.exit_check),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Blank Requirements", "", *format_dict_lines(report.blank_requirements)])
    lines.extend(["", "## Style Reminders", "", *format_dict_lines(report.style_reminders)])
    if report.issues:
        lines.extend(["", "## Issues", "", "| Severity | Code | Field | Message |", "| --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(issue.severity),
                        f"`{safe_cell(issue.code)}`",
                        safe_cell(issue.field),
                        safe_cell(issue.message),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"
