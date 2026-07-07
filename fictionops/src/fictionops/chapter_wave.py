from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .markdown import extract_chapter_key, safe_cell
from .models import ChapterWaveIssue, ChapterWaveItem, ChapterWaveReport
from .stats import build_stats_report, metric_value


def longest_adjacent_flat_run(values: list[int], *, tolerance: int) -> int:
    if not values:
        return 0
    longest = 1
    current = 1
    for previous, value in zip(values, values[1:]):
        if abs(value - previous) <= tolerance:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest


def longest_equal_run(values: list[str]) -> int:
    if not values:
        return 0
    longest = 1
    current = 1
    for previous, value in zip(values, values[1:]):
        if value == previous:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest


def longest_predicate_run(values: list[str], allowed: set[str]) -> int:
    longest = 0
    current = 0
    for value in values:
        if value in allowed:
            current += 1
        else:
            current = 0
        longest = max(longest, current)
    return longest


def build_chapter_wave_issues(
    *,
    file_count: int,
    spread_ratio_percent: int,
    longest_flat_run: int,
    longest_same_band_run: int,
    short_run: int,
    heavy_run: int,
    chapters: list[ChapterWaveItem],
    min_spread_ratio: int,
    max_flat_run: int,
    max_same_band_run: int,
) -> list[ChapterWaveIssue]:
    issues: list[ChapterWaveIssue] = []
    if file_count == 0:
        return [
            ChapterWaveIssue(
                severity="P2",
                code="no_chapter_files",
                chapter="-",
                message="No chapter files were detected for chapter-wave audit.",
            )
        ]

    if file_count >= 4 and spread_ratio_percent < min_spread_ratio:
        issues.append(
            ChapterWaveIssue(
                severity="P3",
                code="too_uniform_wave",
                chapter="-",
                message=(
                    f"Chapter lengths are very uniform: spread is {spread_ratio_percent}% of the average "
                    f"(threshold {min_spread_ratio}%)."
                ),
            )
        )

    if file_count >= max_flat_run and longest_flat_run >= max_flat_run:
        issues.append(
            ChapterWaveIssue(
                severity="P3",
                code="flat_chapter_run",
                chapter="-",
                message=(
                    f"{longest_flat_run} adjacent chapters stay within the flat-length tolerance. "
                    "Check whether the book is being filled to a mechanical target."
                ),
            )
        )

    if file_count >= max_same_band_run and longest_same_band_run >= max_same_band_run:
        issues.append(
            ChapterWaveIssue(
                severity="P4",
                code="same_band_run",
                chapter="-",
                message=f"{longest_same_band_run} adjacent chapters share the same length band.",
            )
        )

    if short_run >= 3:
        issues.append(
            ChapterWaveIssue(
                severity="P3",
                code="short_chapter_run",
                chapter="-",
                message=f"{short_run} adjacent chapters are in the short band.",
            )
        )

    if heavy_run >= 3:
        issues.append(
            ChapterWaveIssue(
                severity="P4",
                code="heavy_chapter_run",
                chapter="-",
                message=f"{heavy_run} adjacent chapters are in heavy or very_heavy bands.",
            )
        )

    for chapter in chapters:
        if chapter.delta_from_previous is None:
            continue
        previous = chapters[chapter.index - 2]
        jump_threshold = max(3000, round(previous.metric_value * 0.5))
        if chapter.delta_from_previous > jump_threshold:
            issues.append(
                ChapterWaveIssue(
                    severity="P4",
                    code="abrupt_length_jump",
                    chapter=chapter.chapter,
                    message=(
                        f"Length changes by {chapter.delta_from_previous} from the previous chapter "
                        f"(threshold {jump_threshold})."
                    ),
                )
            )

    return issues


def build_chapter_wave_report(
    target: Path,
    *,
    all_markdown: bool,
    pattern: str,
    metric: str,
    flat_tolerance: int = 200,
    min_spread_ratio: int = 15,
    max_flat_run: int = 4,
    max_same_band_run: int = 5,
) -> ChapterWaveReport:
    stats_report = build_stats_report(target, all_markdown=all_markdown, pattern=pattern, metric=metric)
    values = [metric_value(stats, metric) for stats in stats_report.files]
    deltas: list[int | None] = [None]
    for previous, value in zip(values, values[1:]):
        deltas.append(abs(value - previous))

    chapters = [
        ChapterWaveItem(
            index=index,
            chapter=extract_chapter_key(Path(stats.path)),
            path=stats.path,
            chars=stats.chars,
            nonspace_chars=stats.nonspace_chars,
            cjk_chars=stats.cjk_chars,
            lines=stats.lines,
            metric_value=value,
            band=stats.band,
            delta_from_previous=delta,
        )
        for index, (stats, value, delta) in enumerate(zip(stats_report.files, values, deltas), start=1)
    ]
    spread = stats_report.maximum - stats_report.minimum if values else 0
    spread_ratio_percent = round((spread * 100) / stats_report.average) if stats_report.average else 0
    average_delta = round(sum(delta for delta in deltas[1:] if delta is not None) / (len(values) - 1)) if len(values) > 1 else 0
    bands = [chapter.band for chapter in chapters]
    longest_flat_run = longest_adjacent_flat_run(values, tolerance=flat_tolerance)
    longest_same_band_run = longest_equal_run(bands)
    short_run = longest_predicate_run(bands, {"short"})
    heavy_run = longest_predicate_run(bands, {"heavy", "very_heavy"})
    issues = build_chapter_wave_issues(
        file_count=stats_report.file_count,
        spread_ratio_percent=spread_ratio_percent,
        longest_flat_run=longest_flat_run,
        longest_same_band_run=longest_same_band_run,
        short_run=short_run,
        heavy_run=heavy_run,
        chapters=chapters,
        min_spread_ratio=min_spread_ratio,
        max_flat_run=max_flat_run,
        max_same_band_run=max_same_band_run,
    )

    return ChapterWaveReport(
        target=stats_report.target,
        mode=stats_report.mode,
        metric=stats_report.metric,
        file_count=stats_report.file_count,
        total=stats_report.total,
        average=stats_report.average,
        minimum=stats_report.minimum,
        maximum=stats_report.maximum,
        spread=spread,
        spread_ratio_percent=spread_ratio_percent,
        average_delta=average_delta,
        longest_flat_run=longest_flat_run,
        longest_same_band_run=longest_same_band_run,
        band_counts=dict(Counter(bands).most_common()),
        issues=issues,
        chapters=chapters,
    )


def format_band_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "-"
    return ", ".join(f"{key}:{value}" for key, value in counts.items())


def format_delta(delta: int | None) -> str:
    if delta is None:
        return "-"
    return str(delta)


def format_chapter_wave_table(report: ChapterWaveReport) -> str:
    lines = [
        "# FictionOps Chapter Wave Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Mode: `{report.mode}`",
        f"- Metric: `{report.metric}`",
        f"- Files: {report.file_count}",
        f"- Average: {report.average}",
        f"- Min / Max: {report.minimum} / {report.maximum}",
        f"- Spread: {report.spread} ({report.spread_ratio_percent}% of average)",
        f"- Average adjacent delta: {report.average_delta}",
        f"- Longest flat run: {report.longest_flat_run}",
        f"- Longest same-band run: {report.longest_same_band_run}",
        f"- Bands: {format_band_counts(report.band_counts)}",
        "",
        "## Issues",
        "",
    ]
    if report.issues:
        lines.extend(["| Severity | Code | Chapter | Message |", "| --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                f"| {issue.severity} | `{issue.code}` | {safe_cell(issue.chapter)} | {safe_cell(issue.message)} |"
            )
    else:
        lines.append("No chapter wave issues above thresholds.")

    if not report.chapters:
        lines.append("")
        lines.append("Tip: use `--all` to include all Markdown files.")
        return "\n".join(lines)

    lines.extend(
        [
            "",
            "## Chapters",
            "",
            "| # | Chapter | File | Value | Delta | Band | Lines |",
            "| --- | --- | --- | ---: | ---: | --- | ---: |",
        ]
    )
    for chapter in report.chapters:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(chapter.index),
                    safe_cell(chapter.chapter),
                    f"`{chapter.path}`",
                    str(chapter.metric_value),
                    format_delta(chapter.delta_from_previous),
                    chapter.band,
                    str(chapter.lines),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def render_chapter_wave_report(report: ChapterWaveReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ == "table":
        return format_chapter_wave_table(report)
    raise ValueError(f"Unsupported chapter wave format: {format_}")
