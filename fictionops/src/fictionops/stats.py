from __future__ import annotations

from pathlib import Path

from .markdown import collect_markdown_files, count_latin_words, display_path, is_cjk
from .models import FileStats, StatsReport

def metric_value(stats: FileStats, metric: str) -> int:
    if metric == "chars":
        return stats.chars
    if metric == "cjk":
        return stats.cjk_chars
    return stats.nonspace_chars


def band_for(value: int) -> str:
    if value < 6000:
        return "short"
    if value < 8000:
        return "lean"
    if value < 10000:
        return "standard"
    if value < 12000:
        return "heavy"
    return "very_heavy"


def build_stats_report(target: Path, *, all_markdown: bool, pattern: str, metric: str) -> StatsReport:
    resolved = target.expanduser().resolve()
    base = resolved if resolved.is_dir() else resolved.parent
    files = collect_markdown_files(resolved, all_markdown=all_markdown, pattern=pattern)
    file_stats: list[FileStats] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        chars = len(text)
        nonspace_chars = sum(1 for char in text if not char.isspace())
        cjk_chars = sum(1 for char in text if is_cjk(char))
        latin_words = count_latin_words(text)
        lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        preliminary = FileStats(
            path=display_path(path, base),
            chars=chars,
            nonspace_chars=nonspace_chars,
            cjk_chars=cjk_chars,
            latin_words=latin_words,
            lines=lines,
            band="",
        )
        value = metric_value(preliminary, metric)
        preliminary.band = band_for(value)
        file_stats.append(preliminary)

    values = [metric_value(stats, metric) for stats in file_stats]
    total = sum(values)
    file_count = len(file_stats)
    average = round(total / file_count) if file_count else 0
    minimum = min(values) if values else 0
    maximum = max(values) if values else 0
    mode = "all-markdown" if all_markdown else "chapters"
    return StatsReport(
        target=str(resolved),
        mode=mode,
        metric=metric,
        file_count=file_count,
        total=total,
        average=average,
        minimum=minimum,
        maximum=maximum,
        files=file_stats,
    )


def format_table(report: StatsReport) -> str:
    lines = [
        "# FictionOps Stats",
        "",
        f"- Target: `{report.target}`",
        f"- Mode: `{report.mode}`",
        f"- Metric: `{report.metric}`",
        f"- Files: {report.file_count}",
        f"- Total: {report.total}",
        f"- Average: {report.average}",
        f"- Min / Max: {report.minimum} / {report.maximum}",
        "",
    ]
    if not report.files:
        lines.append("No matching Markdown files found.")
        if report.mode == "chapters":
            lines.append("Tip: use `--all` to include all Markdown files.")
        return "\n".join(lines)

    lines.extend(
        [
            "| # | File | Nonspace | CJK | Lines | Band |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for index, stats in enumerate(report.files, start=1):
        lines.append(
            f"| {index} | `{stats.path}` | {stats.nonspace_chars} | {stats.cjk_chars} | {stats.lines} | {stats.band} |"
        )
    return "\n".join(lines)
