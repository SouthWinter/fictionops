from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .constants import DEFAULT_WATCH_TERMS
from .markdown import clean_preview, collect_markdown_files, display_path, split_sentences, substantive_blocks
from .models import CountItem, StyleAuditFile, StyleAuditReport

def classify_block(text: str) -> str:
    sample = text.strip()
    if not sample:
        return "empty"
    head = sample[:80]
    if head.startswith(("“", "\"", "‘", "'")):
        return "dialogue"
    if re.search(r"[雪雨风雾霜海河山城门天夜晨暮灯火影水潮云]", head):
        return "setting"
    if re.search(r"[手眼脚肩背血汗冷疼痛脸喉心口呼吸发指骨]", head):
        return "body"
    if re.search(r"(已经|从来|后来|那时|此时|这一日|这一天|过去|现在|原本|自从|许多年)", head):
        return "summary"
    if re.search(r"[走站坐拿放推拉看听问说笑跪抬转伸握挑]", head):
        return "action"
    return "other"


def sentence_opening(sentence: str, size: int = 4) -> str:
    opening = re.sub(r"^[\s“”‘’\"'（）()《》【】\[\]，,。！？!?；;：:、.-]+", "", sentence.strip())
    opening = re.sub(r"\s+", "", opening)
    if len(opening) < 2:
        return ""
    return opening[:size]


def count_watch_terms(text: str, watch_terms: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for term in watch_terms:
        if term:
            counts[term] = text.count(term)
    return counts


def top_items(counter: Counter[str], *, limit: int, min_count: int = 1) -> list[CountItem]:
    items = [
        CountItem(item=item, count=count)
        for item, count in counter.most_common()
        if count >= min_count and item
    ]
    return items[:limit]


def parse_watch_terms(raw: str | None) -> list[str]:
    if raw is None:
        return DEFAULT_WATCH_TERMS
    terms = [term.strip() for term in raw.split(",") if term.strip()]
    return terms or DEFAULT_WATCH_TERMS


def build_style_audit_report(
    target: Path,
    *,
    all_markdown: bool,
    pattern: str,
    watch_terms: list[str],
    top: int,
    min_repeat: int,
) -> StyleAuditReport:
    resolved = target.expanduser().resolve()
    base = resolved if resolved.is_dir() else resolved.parent
    files = collect_markdown_files(resolved, all_markdown=all_markdown, pattern=pattern)
    mode = "all-markdown" if all_markdown else "chapters"

    aggregate_terms: Counter[str] = Counter()
    aggregate_openings: Counter[str] = Counter()
    opening_types: Counter[str] = Counter()
    ending_types: Counter[str] = Counter()
    file_reports: list[StyleAuditFile] = []

    for path in files:
        text = path.read_text(encoding="utf-8")
        blocks = substantive_blocks(text)
        opening = blocks[0] if blocks else ""
        ending = blocks[-1] if blocks else ""
        opening_type = classify_block(opening)
        ending_type = classify_block(ending)
        opening_types[opening_type] += 1
        ending_types[ending_type] += 1

        watch_counts = count_watch_terms(text, watch_terms)
        aggregate_terms.update(watch_counts)
        watch_total = sum(watch_counts.values())

        sentence_counts: Counter[str] = Counter()
        for sentence in split_sentences(text):
            opening_key = sentence_opening(sentence)
            if opening_key:
                sentence_counts[opening_key] += 1
                aggregate_openings[opening_key] += 1

        file_reports.append(
            StyleAuditFile(
                path=display_path(path, base),
                opening_type=opening_type,
                opening_preview=clean_preview(opening),
                ending_type=ending_type,
                ending_preview=clean_preview(ending),
                watch_total=watch_total,
                top_terms=top_items(watch_counts, limit=5),
                repeated_openings=top_items(sentence_counts, limit=5, min_count=min_repeat),
            )
        )

    return StyleAuditReport(
        target=str(resolved),
        mode=mode,
        file_count=len(file_reports),
        watch_terms=watch_terms,
        watch_total=sum(aggregate_terms.values()),
        opening_types=dict(opening_types.most_common()),
        ending_types=dict(ending_types.most_common()),
        aggregate_terms=top_items(aggregate_terms, limit=top),
        repeated_openings=top_items(aggregate_openings, limit=top, min_count=min_repeat),
        files=file_reports,
    )


def format_count_items(items: list[CountItem]) -> str:
    if not items:
        return "-"
    return ", ".join(f"{item.item}:{item.count}" for item in items)


def format_counter_dict(counts: dict[str, int]) -> str:
    if not counts:
        return "-"
    return ", ".join(f"{key}:{value}" for key, value in counts.items())


def format_style_audit_table(report: StyleAuditReport) -> str:
    lines = [
        "# FictionOps Style Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Mode: `{report.mode}`",
        f"- Files: {report.file_count}",
        f"- Watch hits: {report.watch_total}",
        f"- Opening types: {format_counter_dict(report.opening_types)}",
        f"- Ending types: {format_counter_dict(report.ending_types)}",
        "",
        "## Watched Terms",
        "",
    ]
    if report.aggregate_terms:
        lines.extend(["| Term | Count |", "| --- | ---: |"])
        for item in report.aggregate_terms:
            lines.append(f"| {item.item} | {item.count} |")
    else:
        lines.append("No watched terms found.")

    lines.extend(["", "## Repeated Sentence Openings", ""])
    if report.repeated_openings:
        lines.extend(["| Opening | Count |", "| --- | ---: |"])
        for item in report.repeated_openings:
            lines.append(f"| {item.item} | {item.count} |")
    else:
        lines.append("No repeated sentence openings above threshold.")

    lines.extend(
        [
            "",
            "## Files",
            "",
            "| # | File | Open | End | Watch | Top Terms | Repeated Openings |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for index, file_report in enumerate(report.files, start=1):
        open_cell = f"{file_report.opening_type}: {file_report.opening_preview}"
        end_cell = f"{file_report.ending_type}: {file_report.ending_preview}"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    f"`{file_report.path}`",
                    open_cell,
                    end_cell,
                    str(file_report.watch_total),
                    format_count_items(file_report.top_terms),
                    format_count_items(file_report.repeated_openings),
                ]
            )
            + " |"
        )
    return "\n".join(lines)
