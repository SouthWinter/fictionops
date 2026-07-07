from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .markdown import collect_markdown_files, display_path, safe_cell
from .models import TableCheckIssue, TableCheckReport, TableCheckTable


PLACEHOLDER_CELLS = {"", "-", "—", "……", "...", "待定", "未定", "暂无", "无", "TODO", "todo"}


def split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def is_separator_row(line: str) -> bool:
    cells = split_table_row(line)
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def is_table_row(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|") and "|" in line.strip()[1:-1]


def cell_filled(cell: str) -> bool:
    return cell.strip() not in PLACEHOLDER_CELLS


def find_tables(text: str) -> list[tuple[int, list[str], list[list[str]], list[tuple[int, list[str]]]]]:
    lines = text.splitlines()
    tables: list[tuple[int, list[str], list[list[str]], list[tuple[int, list[str]]]]] = []
    index = 0
    while index + 1 < len(lines):
        if not is_table_row(lines[index]) or not is_separator_row(lines[index + 1]):
            index += 1
            continue
        start_line = index + 1
        headers = split_table_row(lines[index])
        rows: list[list[str]] = []
        raw_rows: list[tuple[int, list[str]]] = []
        index += 2
        while index < len(lines) and is_table_row(lines[index]):
            row = split_table_row(lines[index])
            rows.append(row)
            raw_rows.append((index + 1, row))
            index += 1
        tables.append((start_line, headers, rows, raw_rows))
    return tables


def table_issues(
    *,
    path: str,
    line: int,
    headers: list[str],
    rows: list[list[str]],
    raw_rows: list[tuple[int, list[str]]],
    min_filled_cells: int,
) -> list[TableCheckIssue]:
    issues: list[TableCheckIssue] = []
    width = len(headers)
    if width == 0 or any(not header.strip() for header in headers):
        issues.append(TableCheckIssue("P3", "empty_header", path, line, "Table has an empty header cell."))
    normalized_headers = [header.strip().lower() for header in headers if header.strip()]
    duplicates = sorted({header for header in normalized_headers if normalized_headers.count(header) > 1})
    if duplicates:
        issues.append(TableCheckIssue("P3", "duplicate_header", path, line, "Table has duplicate header cells: " + ", ".join(duplicates)))
    if not rows:
        issues.append(TableCheckIssue("P3", "empty_table", path, line, "Table has headers but no body rows."))
    filled_total = 0
    for row_line, row in raw_rows:
        if len(row) != width:
            issues.append(TableCheckIssue("P2", "row_width_mismatch", path, row_line, f"Row has {len(row)} cells but header has {width}."))
        filled = sum(1 for cell in row if cell_filled(cell))
        filled_total += filled
        if filled < min_filled_cells:
            issues.append(TableCheckIssue("P3", "mostly_empty_row", path, row_line, f"Row has fewer than {min_filled_cells} filled cells."))
    if rows and filled_total == 0:
        issues.append(TableCheckIssue("P3", "no_filled_cells", path, line, "Table body has no filled cells."))
    return issues


def build_table_check_report(
    target: Path,
    *,
    all_markdown: bool,
    pattern: str,
    min_filled_cells: int,
) -> TableCheckReport:
    resolved = target.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")
    if min_filled_cells < 1:
        raise ValueError("min_filled_cells must be >= 1")
    files = collect_markdown_files(resolved, all_markdown=all_markdown, pattern=pattern)
    mode = "all-markdown" if all_markdown else "chapters"
    base = resolved if resolved.is_dir() else resolved.parent
    all_issues: list[TableCheckIssue] = []
    table_reports: list[TableCheckTable] = []

    for path in files:
        display = display_path(path, base)
        text = path.read_text(encoding="utf-8")
        tables = find_tables(text)
        for line, headers, rows, raw_rows in tables:
            issues = table_issues(
                path=display,
                line=line,
                headers=headers,
                rows=rows,
                raw_rows=raw_rows,
                min_filled_cells=min_filled_cells,
            )
            filled = sum(1 for row in rows for cell in row if cell_filled(cell))
            empty = sum(1 for row in rows for cell in row if not cell_filled(cell))
            table_reports.append(
                TableCheckTable(
                    path=display,
                    line=line,
                    columns=len(headers),
                    rows=len(rows),
                    filled_cells=filled,
                    empty_cells=empty,
                    headers=headers,
                    issues=issues,
                )
            )
            all_issues.extend(issues)
        if not tables:
            all_issues.append(TableCheckIssue("P4", "no_tables", display, 0, "No Markdown tables found in file."))

    return TableCheckReport(
        target=str(resolved),
        mode=mode,
        file_count=len(files),
        table_count=len(table_reports),
        issue_count=len(all_issues),
        min_filled_cells=min_filled_cells,
        issues=all_issues,
        tables=table_reports,
    )


def render_table_check_report(report: TableCheckReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ != "table":
        raise ValueError(f"Unsupported check-tables format: {format_}")
    lines = [
        "# FictionOps Table Check",
        "",
        f"- Target: `{report.target}`",
        f"- Mode: {report.mode}",
        f"- Files: {report.file_count}",
        f"- Tables: {report.table_count}",
        f"- Issues: {report.issue_count}",
        f"- Min filled cells: {report.min_filled_cells}",
        "",
        "## Tables",
        "",
        "| File | Line | Columns | Rows | Filled | Empty | Issues |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for table in report.tables:
        lines.append(
            f"| `{safe_cell(table.path)}` | {table.line} | {table.columns} | {table.rows} | "
            f"{table.filled_cells} | {table.empty_cells} | {len(table.issues)} |"
        )
    if not report.tables:
        lines.append("| - | 0 | 0 | 0 | 0 | 0 | 0 |")
    lines.extend(["", "## Issues", "", "| Severity | Code | File | Line | Message |", "| --- | --- | --- | ---: | --- |"])
    if report.issues:
        for issue in report.issues:
            lines.append(f"| {issue.severity} | `{issue.code}` | `{safe_cell(issue.path)}` | {issue.line} | {safe_cell(issue.message)} |")
    else:
        lines.append("| - | - | - | 0 | No table issues found. |")
    return "\n".join(lines)
