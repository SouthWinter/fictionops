from __future__ import annotations

import re
from pathlib import Path

from .constants import ECHO_TABLE_NAME_MARKERS
from .continuity_audit import format_bool
from .markdown import chinese_numeral_to_int, clean_preview, collect_markdown_files, display_path, extract_chapter_key, natural_key, safe_cell
from .models import EchoIssue, EchoReport, EchoThread

def split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in stripped:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    cells.append("".join(current).strip())
    return cells


def is_markdown_separator(cells: list[str]) -> bool:
    nonblank = [cell.strip() for cell in cells if cell.strip()]
    return bool(nonblank) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in nonblank)


def normalize_header(header: str) -> str:
    return re.sub(r"[\s_/\-（）()：:|]+", "", header.strip().lower())


def header_index(headers: list[str], candidates: list[str]) -> int | None:
    normalized = [normalize_header(header) for header in headers]
    normalized_candidates = [normalize_header(candidate) for candidate in candidates]
    for candidate in normalized_candidates:
        for index, header in enumerate(normalized):
            if candidate == header or candidate in header:
                return index
    return None


def table_is_echo_table(headers: list[str]) -> bool:
    return header_index(headers, ["thread", "线程", "伏笔", "线索"]) is not None and (
        header_index(headers, ["first plant", "初次埋下", "初种", "首次埋下"]) is not None
        or header_index(headers, ["last echo", "上次回声", "最后回声", "最近回声"]) is not None
        or header_index(headers, ["next light echo", "下一次轻回声", "下次回声"]) is not None
        or header_index(headers, ["payoff direction", "兑现方向", "兑现/转化方向", "转化方向"]) is not None
    )


def blankish(value: str) -> bool:
    stripped = re.sub(r"\s+", "", value or "")
    return stripped in {"", "-", "—", "……", "...", "待定", "todo", "TODO", "暂无", "无", "未定"}


def cell_at(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return row[index].strip()


def find_echo_table_files(target: Path, *, pattern: str, table_path: str | None) -> list[Path]:
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
        if any(marker in lowered for marker in ECHO_TABLE_NAME_MARKERS):
            candidates.append(path)
    return candidates


def parse_echo_threads_from_file(path: Path, *, base: Path) -> list[EchoThread]:
    lines = path.read_text(encoding="utf-8").splitlines()
    threads: list[EchoThread] = []
    index = 0
    while index < len(lines) - 1:
        line = lines[index]
        next_line = lines[index + 1]
        if "|" not in line or "|" not in next_line:
            index += 1
            continue
        headers = split_markdown_row(line)
        separator = split_markdown_row(next_line)
        if not is_markdown_separator(separator) or not table_is_echo_table(headers):
            index += 1
            continue

        thread_i = header_index(headers, ["thread", "线程", "伏笔", "线索"])
        first_i = header_index(headers, ["first plant", "初次埋下", "初种", "首次埋下"])
        last_i = header_index(headers, ["last echo", "上次回声", "最后回声", "最近回声"])
        state_i = header_index(headers, ["current state", "当前状态", "当前读者记忆", "读者记忆"])
        next_i = header_index(headers, ["next light echo", "下一次轻回声", "下次回声", "下一次"])
        forbid_i = header_index(headers, ["do not reveal yet", "禁止提前解释", "禁提前解释", "禁止事项"])
        payoff_i = header_index(headers, ["payoff direction", "兑现方向", "兑现/转化方向", "转化方向"])

        row_index = index + 2
        while row_index < len(lines) and "|" in lines[row_index]:
            row = split_markdown_row(lines[row_index])
            if is_markdown_separator(row):
                row_index += 1
                continue
            thread_name = cell_at(row, thread_i)
            if not blankish(thread_name):
                threads.append(
                    EchoThread(
                        source=display_path(path, base),
                        row=row_index + 1,
                        thread=thread_name,
                        first_plant=cell_at(row, first_i),
                        last_echo=cell_at(row, last_i),
                        current_state=cell_at(row, state_i),
                        next_light_echo=cell_at(row, next_i),
                        do_not_reveal=cell_at(row, forbid_i),
                        payoff_direction=cell_at(row, payoff_i),
                        text_hits=0,
                        last_text_hit=None,
                    )
                )
            row_index += 1
        index = row_index
    return threads


def extract_thread_terms(thread: str) -> list[str]:
    cleaned = re.sub(r"[`*_#>\[\]（）()《》\"“”‘’]", "", thread)
    parts = re.split(r"[,，、/;；|]+", cleaned)
    terms: list[str] = []
    for part in parts:
        term = part.strip()
        if len(term) >= 2 and term not in {"伏笔", "线索", "回声"}:
            terms.append(term)
    if not terms and len(cleaned.strip()) >= 2:
        terms.append(cleaned.strip())
    return terms[:6]


def extract_explicit_chapter_number(text: str) -> int | None:
    patterns = [
        r"第(\d+)章",
        r"ch[_-]?(\d+)",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            return max(int(match) for match in matches)
    chinese_matches = re.findall(r"第([零〇一二三四五六七八九十百两]+)章", text)
    numbers = [chinese_numeral_to_int(match) for match in chinese_matches]
    numbers = [number for number in numbers if number is not None]
    return max(numbers) if numbers else None


def scan_thread_in_chapters(thread: EchoThread, chapter_files: list[Path], *, base: Path) -> tuple[int, str | None]:
    terms = extract_thread_terms(thread.thread)
    if not terms:
        return 0, None
    total = 0
    last_hit: str | None = None
    for path in sorted(chapter_files, key=natural_key):
        text = path.read_text(encoding="utf-8")
        hits = sum(text.count(term) for term in terms)
        if hits:
            total += hits
            last_hit = display_path(path, base)
    return total, last_hit


def build_echo_report(
    target: Path,
    *,
    pattern: str,
    table_path: str | None,
    scan_text: bool,
    stale_after: int,
) -> EchoReport:
    resolved = target.expanduser().resolve()
    base = resolved if resolved.is_dir() else resolved.parent
    table_files = find_echo_table_files(resolved, pattern=pattern, table_path=table_path)
    chapter_files = collect_markdown_files(resolved, all_markdown=False, pattern=pattern)
    threads: list[EchoThread] = []
    issues: list[EchoIssue] = []

    if not table_files:
        issues.append(
            EchoIssue(
                severity="P1",
                code="missing_echo_table",
                thread="-",
                path=str(resolved),
                message="No foreshadowing/echo table file was found.",
            )
        )

    for table in table_files:
        threads.extend(parse_echo_threads_from_file(table, base=base))

    if table_files and not threads:
        for table in table_files:
            issues.append(
                EchoIssue(
                    severity="P2",
                    code="no_echo_threads",
                    thread="-",
                    path=display_path(table, base),
                    message="Echo table file was found but no recognizable echo rows were parsed.",
                )
            )

    max_chapter = 0
    for chapter in chapter_files:
        key = extract_chapter_key(chapter)
        if key.isdigit():
            max_chapter = max(max_chapter, int(key))

    for thread in threads:
        if scan_text and chapter_files:
            hits, last_hit = scan_thread_in_chapters(thread, chapter_files, base=base)
            thread.text_hits = hits
            thread.last_text_hit = last_hit

        path = f"{thread.source}:{thread.row}"
        if blankish(thread.first_plant):
            issues.append(
                EchoIssue("P2", "missing_first_plant", thread.thread, path, "Thread has no first planting location.")
            )
        if blankish(thread.last_echo):
            issues.append(
                EchoIssue("P3", "missing_last_echo", thread.thread, path, "Thread has no last echo recorded.")
            )
        if blankish(thread.next_light_echo):
            issues.append(
                EchoIssue("P3", "missing_next_echo", thread.thread, path, "Thread has no planned next light echo.")
            )
        if blankish(thread.payoff_direction):
            issues.append(
                EchoIssue("P3", "missing_payoff_direction", thread.thread, path, "Thread has no payoff/transformation direction.")
            )
        if blankish(thread.do_not_reveal):
            issues.append(
                EchoIssue("P4", "missing_forbidden_reveal", thread.thread, path, "Thread has no forbidden early reveal note.")
            )
        last_chapter = extract_explicit_chapter_number(thread.last_echo)
        if last_chapter is not None and max_chapter and max_chapter - last_chapter >= stale_after:
            issues.append(
                EchoIssue(
                    "P3",
                    "stale_last_echo",
                    thread.thread,
                    path,
                    f"Last recorded echo is chapter {last_chapter}; latest detected chapter is {max_chapter}.",
                )
            )
        if scan_text and chapter_files and thread.text_hits == 0:
            issues.append(
                EchoIssue(
                    "P4",
                    "no_text_hit",
                    thread.thread,
                    path,
                    "Thread label was not found in detected chapter text. This may be fine for abstract threads.",
                )
            )

    return EchoReport(
        target=str(resolved),
        table_files=[display_path(path, base) for path in table_files],
        chapter_count=len(chapter_files),
        thread_count=len(threads),
        text_scan=scan_text,
        issues=issues,
        threads=threads,
    )


def format_echo_report(report: EchoReport) -> str:
    lines = [
        "# FictionOps Echo Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Echo table files: {len(report.table_files)}",
        f"- Chapters scanned: {report.chapter_count}",
        f"- Threads: {report.thread_count}",
        f"- Text scan: {format_bool(report.text_scan)}",
        f"- Issues: {len(report.issues)}",
        "",
    ]
    if report.table_files:
        lines.extend(["## Echo Tables", ""])
        for path in report.table_files:
            lines.append(f"- `{path}`")
        lines.append("")

    lines.extend(
        [
            "## Threads",
            "",
            "| # | Thread | Source | First Plant | Last Echo | Next Echo | Payoff | Text Hits | Last Text Hit |",
            "| --- | --- | --- | --- | --- | --- | --- | ---: | --- |",
        ]
    )
    if report.threads:
        for index, thread in enumerate(report.threads, start=1):
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        safe_cell(thread.thread),
                        f"`{safe_cell(thread.source)}:{thread.row}`",
                        safe_cell(clean_preview(thread.first_plant, 28)),
                        safe_cell(clean_preview(thread.last_echo, 28)),
                        safe_cell(clean_preview(thread.next_light_echo, 28)),
                        safe_cell(clean_preview(thread.payoff_direction, 28)),
                        str(thread.text_hits),
                        f"`{safe_cell(thread.last_text_hit)}`" if thread.last_text_hit else "-",
                    ]
                )
                + " |"
            )
    else:
        lines.append("| - | No echo threads parsed. | - | - | - | - | - | 0 | - |")

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Thread | Path | Message |", "| --- | --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                f"| {issue.severity} | {issue.code} | {safe_cell(issue.thread)} | `{safe_cell(issue.path)}` | {safe_cell(issue.message)} |"
            )
    else:
        lines.append("No echo maintenance gaps found.")
    return "\n".join(lines)
