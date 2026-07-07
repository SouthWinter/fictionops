from __future__ import annotations

from pathlib import Path

from .echo_audit import blankish, cell_at, header_index, is_markdown_separator, split_markdown_row
from .models import ChapterPlan, PlanChapterResult
from .new_book import normalize_book_id
from .new_chapter import chapter_paths, normalize_chapter_number


CHAPTER_HEADERS = ["章", "章节", "chapter", "ch"]
TITLE_HEADERS = ["标题", "title"]
VIEWPOINT_HEADERS = ["视角", "视角人物", "viewpoint", "pov", "view"]
KIND_HEADERS = ["性质", "章节性质", "kind", "type"]
PRESSURE_HEADERS = ["pressure", "压力"]
DESIRE_HEADERS = ["desire", "欲望"]
OBSTACLE_HEADERS = ["obstacle", "阻碍"]
CHANGE_HEADERS = ["change", "变化"]
REMAINDER_HEADERS = ["remainder", "余味", "残留"]
TARGET_HEADERS = ["体量", "字数", "建议体量", "target", "target chars", "target_chars"]


def normalize_book_for_plan(book: str) -> str:
    try:
        return normalize_book_id(book)
    except ValueError:
        return book.strip()


def default_outline_path(project: Path, *, book: str) -> Path:
    return project / "04_structure" / "book_outlines" / f"{book}_outline.md"


def resolve_outline_path(project: Path, *, book: str, outline: str | None) -> Path:
    if outline:
        candidate = Path(outline).expanduser()
        if candidate.is_absolute():
            return candidate.resolve()
        return (project / candidate).resolve()
    return default_outline_path(project, book=book).resolve()


def table_is_chapter_plan(headers: list[str]) -> bool:
    if header_index(headers, CHAPTER_HEADERS) is None:
        return False
    engine_fields = [
        TITLE_HEADERS,
        VIEWPOINT_HEADERS,
        PRESSURE_HEADERS,
        DESIRE_HEADERS,
        OBSTACLE_HEADERS,
        CHANGE_HEADERS,
        REMAINDER_HEADERS,
        TARGET_HEADERS,
    ]
    return sum(1 for candidates in engine_fields if header_index(headers, candidates) is not None) >= 3


def plan_from_row(path: Path, row_number: int, headers: list[str], row: list[str]) -> ChapterPlan:
    def value(candidates: list[str]) -> str:
        return cell_at(row, header_index(headers, candidates))

    return ChapterPlan(
        source=str(path),
        row=row_number,
        chapter=value(CHAPTER_HEADERS),
        title=value(TITLE_HEADERS),
        viewpoint=value(VIEWPOINT_HEADERS),
        kind=value(KIND_HEADERS),
        pressure=value(PRESSURE_HEADERS),
        desire=value(DESIRE_HEADERS),
        obstacle=value(OBSTACLE_HEADERS),
        change=value(CHANGE_HEADERS),
        remainder=value(REMAINDER_HEADERS),
        target_chars=value(TARGET_HEADERS),
    )


def load_chapter_plans(path: Path) -> list[ChapterPlan]:
    lines = path.read_text(encoding="utf-8").splitlines()
    plans: list[ChapterPlan] = []
    index = 0
    while index < len(lines) - 1:
        if "|" not in lines[index] or "|" not in lines[index + 1]:
            index += 1
            continue
        headers = split_markdown_row(lines[index])
        separator = split_markdown_row(lines[index + 1])
        if not is_markdown_separator(separator) or not table_is_chapter_plan(headers):
            index += 1
            continue

        row_index = index + 2
        while row_index < len(lines) and "|" in lines[row_index]:
            row = split_markdown_row(lines[row_index])
            if is_markdown_separator(row):
                row_index += 1
                continue
            chapter_value = cell_at(row, header_index(headers, CHAPTER_HEADERS))
            if not blankish(chapter_value):
                try:
                    normalize_chapter_number(chapter_value)
                except ValueError:
                    row_index += 1
                    continue
                plans.append(plan_from_row(path, row_index + 1, headers, row))
            row_index += 1
        index = row_index
    return plans


def load_chapter_plan(path: Path, *, chapter_number: str) -> ChapterPlan:
    for plan in load_chapter_plans(path):
        if normalize_chapter_number(plan.chapter) == chapter_number:
            return plan
    raise ValueError(f"chapter {chapter_number} was not found in outline table: {path}")


def set_line_value(
    lines: list[str],
    marker: str,
    value: str,
    *,
    field_name: str,
    force: bool,
    result: PlanChapterResult,
) -> None:
    if blankish(value):
        return
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith(marker):
            continue
        prefix = line[: len(line) - len(line.lstrip())]
        existing = stripped[len(marker) :].strip()
        if blankish(existing) or force:
            new_line = f"{prefix}{marker}{value.strip()}"
            if line != new_line:
                lines[index] = new_line
                result.updated_fields.append(field_name)
        elif existing != value.strip():
            result.skipped_fields.append(field_name)
        return


def set_chapter_engine_table(
    lines: list[str],
    plan: ChapterPlan,
    *,
    force: bool,
    result: PlanChapterResult,
) -> None:
    desired = {
        "pressure": plan.pressure,
        "desire": plan.desire,
        "obstacle": plan.obstacle,
        "change": plan.change,
        "remainder": plan.remainder,
    }
    header_candidates = {
        "pressure": PRESSURE_HEADERS,
        "desire": DESIRE_HEADERS,
        "obstacle": OBSTACLE_HEADERS,
        "change": CHANGE_HEADERS,
        "remainder": REMAINDER_HEADERS,
    }
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
        if sum(1 for candidates in header_candidates.values() if header_index(headers, candidates) is not None) < 5:
            index += 1
            continue

        row_index = index + 2
        while row_index < len(lines) and "|" in lines[row_index]:
            row = split_markdown_row(lines[row_index])
            if is_markdown_separator(row):
                row_index += 1
                continue
            changed = False
            for field_name, value in desired.items():
                if blankish(value):
                    continue
                cell_index = header_index(headers, header_candidates[field_name])
                if cell_index is None:
                    continue
                while len(row) <= cell_index:
                    row.append("")
                existing = row[cell_index].strip()
                clean_value = value.strip()
                if blankish(existing) or force:
                    if existing != clean_value:
                        row[cell_index] = clean_value
                        result.updated_fields.append(field_name)
                        changed = True
                elif existing != clean_value:
                    result.skipped_fields.append(field_name)
            if changed:
                lines[row_index] = "| " + " | ".join(row) + " |"
            return
        return


def apply_plan_to_engine(text: str, plan: ChapterPlan, *, force: bool, result: PlanChapterResult) -> str:
    lines = text.splitlines()
    set_line_value(lines, "- 标题：", plan.title, field_name="title", force=force, result=result)
    set_line_value(lines, "- 视角人物：", plan.viewpoint, field_name="viewpoint", force=force, result=result)
    set_line_value(lines, "- 建议体量：", plan.target_chars, field_name="target_chars", force=force, result=result)
    if not blankish(plan.kind):
        set_line_value(lines, "- 章节性质：", plan.kind, field_name="kind", force=force, result=result)
    set_chapter_engine_table(lines, plan, force=force, result=result)
    return "\n".join(lines) + "\n"


def plan_chapter(
    project: Path,
    *,
    book: str,
    chapter: str,
    outline: str | None,
    force: bool,
    dry_run: bool,
) -> PlanChapterResult:
    book_id = normalize_book_for_plan(book)
    chapter_number = normalize_chapter_number(chapter)
    outline_path = resolve_outline_path(project, book=book_id, outline=outline)
    if not outline_path.exists():
        raise FileNotFoundError(f"book outline not found: {outline_path}")

    paths = chapter_paths(project, book=book_id, chapter_number=chapter_number)
    engine_path = paths["engine"]
    if not engine_path.exists():
        raise FileNotFoundError(f"chapter engine not found: {engine_path}. Run new-chapter first.")

    plan = load_chapter_plan(outline_path, chapter_number=chapter_number)
    result = PlanChapterResult(
        outline_file=str(outline_path),
        engine_file=str(engine_path),
        plan_row=plan.row,
        dry_run=dry_run,
    )
    updated_text = apply_plan_to_engine(engine_path.read_text(encoding="utf-8"), plan, force=force, result=result)
    if not dry_run and result.updated_fields:
        engine_path.write_text(updated_text, encoding="utf-8", newline="\n")
    return result
