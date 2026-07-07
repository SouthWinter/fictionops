from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .constants import INFO_TABLE_NAME_MARKERS
from .continuity_audit import format_bool
from .echo_audit import (
    blankish,
    cell_at,
    extract_explicit_chapter_number,
    header_index,
    is_markdown_separator,
    split_markdown_row,
)
from .markdown import clean_preview, collect_markdown_files, display_path, extract_chapter_key, natural_key, safe_cell
from .models import InfoBoundaryIssue, InfoBoundaryItem, InfoBoundaryReport


def table_is_information_table(headers: list[str]) -> bool:
    has_item = header_index(headers, ["info", "information", "secret", "信息", "秘密", "信息/秘密"]) is not None
    has_truth = header_index(headers, ["author truth", "truth", "作者真相", "真相"]) is not None
    has_boundary = (
        header_index(headers, ["reader", "reader current", "读者", "读者目前知道"]) is not None
        or header_index(headers, ["public version", "public", "公共版本", "公开版本"]) is not None
        or header_index(headers, ["do not reveal", "forbidden", "禁止事项", "禁止提前"]) is not None
    )
    return has_item and (has_truth or has_boundary)


def find_info_table_files(target: Path, *, pattern: str, table_path: str | None) -> list[Path]:
    resolved = target.expanduser().resolve()
    if table_path:
        table = Path(table_path).expanduser()
        if not table.is_absolute():
            table = resolved / table if resolved.is_dir() else resolved.parent / table
        return [table] if table.exists() and table.suffix.lower() == ".md" else []
    if resolved.is_file():
        return [resolved] if resolved.suffix.lower() == ".md" else []
    all_files = collect_markdown_files(resolved, all_markdown=True, pattern=pattern)
    candidates: list[Path] = []
    for path in all_files:
        lowered = str(path).lower()
        if any(marker in lowered for marker in INFO_TABLE_NAME_MARKERS):
            candidates.append(path)
    return candidates


def parse_info_items_from_file(path: Path, *, base: Path) -> list[InfoBoundaryItem]:
    lines = path.read_text(encoding="utf-8").splitlines()
    items: list[InfoBoundaryItem] = []
    index = 0
    while index < len(lines) - 1:
        line = lines[index]
        next_line = lines[index + 1]
        if "|" not in line or "|" not in next_line:
            index += 1
            continue
        headers = split_markdown_row(line)
        separator = split_markdown_row(next_line)
        if not is_markdown_separator(separator) or not table_is_information_table(headers):
            index += 1
            continue

        item_i = header_index(headers, ["info", "information", "secret", "信息", "秘密", "信息/秘密"])
        truth_i = header_index(headers, ["author truth", "truth", "作者真相", "真相"])
        reader_i = header_index(headers, ["reader", "reader current", "读者", "读者目前知道"])
        char_a_i = header_index(headers, ["character a", "group a", "角色/群体 A", "角色 A", "角色A"])
        char_b_i = header_index(headers, ["character b", "group b", "角色/群体 B", "角色 B", "角色B"])
        public_i = header_index(headers, ["public version", "public", "公共版本", "公开版本"])
        official_i = header_index(headers, ["official version", "official", "官方版本"])
        next_i = header_index(headers, ["next release", "next", "下一次释放", "下次释放"])
        forbid_i = header_index(headers, ["do not reveal", "forbidden", "禁止事项", "禁止提前"])

        row_index = index + 2
        while row_index < len(lines) and "|" in lines[row_index]:
            row = split_markdown_row(lines[row_index])
            if is_markdown_separator(row):
                row_index += 1
                continue
            item_name = cell_at(row, item_i)
            if not blankish(item_name):
                items.append(
                    InfoBoundaryItem(
                        source=display_path(path, base),
                        row=row_index + 1,
                        item=item_name,
                        author_truth=cell_at(row, truth_i),
                        reader_state=cell_at(row, reader_i),
                        character_a=cell_at(row, char_a_i),
                        character_b=cell_at(row, char_b_i),
                        public_version=cell_at(row, public_i),
                        official_version=cell_at(row, official_i),
                        next_release=cell_at(row, next_i),
                        forbidden=cell_at(row, forbid_i),
                        text_hits=0,
                        first_text_hit=None,
                        last_text_hit=None,
                    )
                )
            row_index += 1
        index = row_index
    return items


def extract_terms(*values: str) -> list[str]:
    ignored = {
        "do",
        "does",
        "not",
        "no",
        "the",
        "a",
        "an",
        "and",
        "or",
        "to",
        "of",
        "in",
        "with",
        "without",
        "only",
        "before",
        "after",
        "explain",
        "reveal",
        "reveals",
        "revealed",
        "secret",
        "info",
        "information",
        "forbidden",
        "禁止",
        "提前",
        "透露",
        "揭露",
        "秘密",
        "信息",
    }
    terms: list[str] = []
    for value in values:
        cleaned = re.sub(r"[`*_#>\[\]{}()（）《》“”‘’\"']", " ", value or "")
        for part in re.split(r"[,，、;；/：:\s]+", cleaned):
            term = part.strip()
            if len(term) < 2:
                continue
            if term.lower() in ignored:
                continue
            if term not in terms:
                terms.append(term)
    return terms[:8]


def scan_info_item_in_chapters(
    item: InfoBoundaryItem,
    chapter_files: list[Path],
    *,
    base: Path,
) -> tuple[int, str | None, str | None, int | None]:
    terms = extract_terms(item.item, item.forbidden)
    if not terms:
        return 0, None, None, None
    total = 0
    first_hit: str | None = None
    last_hit: str | None = None
    first_hit_number: int | None = None
    for path in sorted(chapter_files, key=natural_key):
        text = path.read_text(encoding="utf-8")
        hits = sum(text.count(term) for term in terms)
        if not hits:
            continue
        total += hits
        displayed = display_path(path, base)
        if first_hit is None:
            first_hit = displayed
            key = extract_chapter_key(path)
            first_hit_number = int(key) if key.isdigit() else None
        last_hit = displayed
    return total, first_hit, last_hit, first_hit_number


def build_info_report(
    target: Path,
    *,
    pattern: str,
    table_path: str | None,
    scan_text: bool,
) -> InfoBoundaryReport:
    resolved = target.expanduser().resolve()
    base = resolved if resolved.is_dir() else resolved.parent
    table_files = find_info_table_files(resolved, pattern=pattern, table_path=table_path)
    chapter_files = collect_markdown_files(resolved, all_markdown=False, pattern=pattern)
    items: list[InfoBoundaryItem] = []
    issues: list[InfoBoundaryIssue] = []

    if not table_files:
        issues.append(
            InfoBoundaryIssue(
                severity="P1",
                code="missing_information_table",
                item="-",
                path=str(resolved),
                message="No information release table file was found.",
            )
        )

    for table in table_files:
        items.extend(parse_info_items_from_file(table, base=base))

    if table_files and not items:
        for table in table_files:
            issues.append(
                InfoBoundaryIssue(
                    severity="P2",
                    code="no_information_items",
                    item="-",
                    path=display_path(table, base),
                    message="Information table file was found but no recognizable information rows were parsed.",
                )
            )

    for item in items:
        path = f"{item.source}:{item.row}"
        if blankish(item.author_truth):
            issues.append(
                InfoBoundaryIssue("P2", "missing_author_truth", item.item, path, "Information item has no author truth.")
            )
        if blankish(item.reader_state):
            issues.append(
                InfoBoundaryIssue("P3", "missing_reader_state", item.item, path, "Information item has no reader-current state.")
            )
        known_versions = [item.character_a, item.character_b, item.public_version, item.official_version]
        if all(blankish(value) for value in known_versions):
            issues.append(
                InfoBoundaryIssue("P3", "missing_in_world_versions", item.item, path, "No character, public, or official knowledge version is recorded.")
            )
        if blankish(item.next_release):
            issues.append(
                InfoBoundaryIssue("P3", "missing_next_release", item.item, path, "Information item has no next release plan.")
            )
        if blankish(item.forbidden):
            issues.append(
                InfoBoundaryIssue("P4", "missing_forbidden_note", item.item, path, "Information item has no forbidden early reveal note.")
            )

        if scan_text and chapter_files:
            hits, first_hit, last_hit, first_hit_number = scan_info_item_in_chapters(item, chapter_files, base=base)
            item.text_hits = hits
            item.first_text_hit = first_hit
            item.last_text_hit = last_hit
            next_release_number = extract_explicit_chapter_number(item.next_release)
            if hits and not blankish(item.forbidden):
                issues.append(
                    InfoBoundaryIssue(
                        "P2",
                        "forbidden_text_hit",
                        item.item,
                        path,
                        f"Information/forbidden terms appear in chapter text; first hit: {first_hit}. Review for possible early reveal.",
                    )
                )
            if (
                first_hit_number is not None
                and next_release_number is not None
                and first_hit_number < next_release_number
            ):
                issues.append(
                    InfoBoundaryIssue(
                        "P2",
                        "early_text_hit_before_release",
                        item.item,
                        path,
                        f"First text hit is chapter {first_hit_number}, before planned release chapter {next_release_number}.",
                    )
                )

    return InfoBoundaryReport(
        target=str(resolved),
        table_files=[display_path(path, base) for path in table_files],
        chapter_count=len(chapter_files),
        item_count=len(items),
        text_scan=scan_text,
        issues=issues,
        items=items,
    )


def format_info_report(report: InfoBoundaryReport) -> str:
    lines = [
        "# FictionOps Information Boundary Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Information table files: {len(report.table_files)}",
        f"- Chapters scanned: {report.chapter_count}",
        f"- Items: {report.item_count}",
        f"- Text scan: {format_bool(report.text_scan)}",
        f"- Issues: {len(report.issues)}",
        "",
    ]
    if report.table_files:
        lines.extend(["## Information Tables", ""])
        for path in report.table_files:
            lines.append(f"- `{path}`")
        lines.append("")

    lines.extend(
        [
            "## Items",
            "",
            "| # | Item | Source | Reader | Public | Official | Next Release | Forbidden | Hits | First Hit |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |",
        ]
    )
    if report.items:
        for index, item in enumerate(report.items, start=1):
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        safe_cell(item.item),
                        f"`{safe_cell(item.source)}:{item.row}`",
                        safe_cell(clean_preview(item.reader_state, 28)),
                        safe_cell(clean_preview(item.public_version, 28)),
                        safe_cell(clean_preview(item.official_version, 28)),
                        safe_cell(clean_preview(item.next_release, 28)),
                        safe_cell(clean_preview(item.forbidden, 28)),
                        str(item.text_hits),
                        f"`{safe_cell(item.first_text_hit)}`" if item.first_text_hit else "-",
                    ]
                )
                + " |"
            )
    else:
        lines.append("| - | - | - | - | - | - | - | - | 0 | - |")

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Item | Path | Message |", "| --- | --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                "| "
                + " | ".join(
                    [
                        issue.severity,
                        f"`{issue.code}`",
                        safe_cell(issue.item),
                        f"`{safe_cell(issue.path)}`",
                        safe_cell(issue.message),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No information boundary issues found.")
    return "\n".join(lines)


def render_info_report(report: InfoBoundaryReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ == "table":
        return format_info_report(report)
    raise ValueError(f"Unsupported information audit format: {format_}")
